"""Data cleaning and validation functions."""

import pandas as pd
from loguru import logger
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of data validation checks."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: dict


# Expected column names (standardized)
COLUMN_MAPPING = {
    "Entity": "cause",
    "Year": "year",
    "Share of deaths": "share_deaths",
    "Share of Google searches": "share_google",
    "Share of NYT media coverage": "share_nyt",
    "Share of Guardian media coverage": "share_guardian",
}

EXPECTED_CAUSES = [
    "Alzheimer's Disease",
    "Cancer",
    "Diabetes",
    "Drug overdose",
    "Heart disease",
    "Homicide",
    "Kidney disease",
    "Lower respiratory disease",
    "Pneumonia & influenza",
    "Road incidents",
    "Stroke",
    "Suicide",
    "Terrorism",
]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the raw data.

    Operations:
    - Rename columns to snake_case
    - Convert data types
    - Handle missing values appropriately
    - Sort by cause and year

    Args:
        df: Raw DataFrame

    Returns:
        Cleaned DataFrame
    """
    logger.info("Starting data cleaning...")

    # Create a copy to avoid modifying original
    df_clean = df.copy()

    # Rename columns
    df_clean = df_clean.rename(columns=COLUMN_MAPPING)
    logger.info(f"Renamed columns: {list(df_clean.columns)}")

    # Convert year to integer
    df_clean["year"] = df_clean["year"].astype(int)

    # Ensure numeric columns are float (they may have NaN)
    numeric_cols = ["share_deaths", "share_google", "share_nyt", "share_guardian"]
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

    # Sort by cause and year
    df_clean = df_clean.sort_values(["cause", "year"]).reset_index(drop=True)

    # Log missing value stats
    missing = df_clean[numeric_cols].isnull().sum()
    logger.info(f"Missing values per column: {missing.to_dict()}")

    logger.info(f"Cleaning complete. Output shape: {df_clean.shape}")

    return df_clean


def validate_data(df: pd.DataFrame) -> ValidationResult:
    """
    Validate the cleaned data for quality issues.

    Checks:
    - All expected causes are present
    - Year range is reasonable (1999-2016)
    - Share values are between 0 and 100
    - Shares sum to ~100 per year (within tolerance)

    Args:
        df: Cleaned DataFrame

    Returns:
        ValidationResult with validation status and details.
    """
    errors = []
    warnings = []
    stats = {}

    # Check 1: Expected causes
    actual_causes = set(df["cause"].unique())
    expected_causes = set(EXPECTED_CAUSES)

    missing_causes = expected_causes - actual_causes
    extra_causes = actual_causes - expected_causes

    if missing_causes:
        errors.append(f"Missing causes: {missing_causes}")
    if extra_causes:
        warnings.append(f"Unexpected causes found: {extra_causes}")

    stats["cause_count"] = len(actual_causes)

    # Check 2: Year range
    min_year, max_year = df["year"].min(), df["year"].max()
    if min_year < 1990 or max_year > 2025:
        warnings.append(f"Unusual year range: {min_year}-{max_year}")

    stats["year_range"] = (min_year, max_year)

    # Check 3: Share values in valid range [0, 100]
    share_cols = ["share_deaths", "share_google", "share_nyt", "share_guardian"]
    for col in share_cols:
        col_data = df[col].dropna()
        if (col_data < 0).any():
            errors.append(f"{col} contains negative values")
        if (col_data > 100).any():
            errors.append(f"{col} contains values > 100")

    # Check 4: Shares sum to ~100 per year (for deaths, which is complete)
    yearly_sums = df.groupby("year")["share_deaths"].sum()
    stats["death_share_sums"] = {
        "min": round(yearly_sums.min(), 2),
        "max": round(yearly_sums.max(), 2),
        "mean": round(yearly_sums.mean(), 2),
    }

    if (yearly_sums < 95).any() or (yearly_sums > 105).any():
        warnings.append(
            f"Death shares don't sum to ~100: range [{yearly_sums.min():.1f}, {yearly_sums.max():.1f}]"
        )

    # Check 5: Missing data patterns
    missing_pct = (df[share_cols].isnull().sum() / len(df) * 100).round(1)
    stats["missing_percentage"] = missing_pct.to_dict()

    # Google searches only available from 2004
    google_before_2004 = df[df["year"] < 2004]["share_google"].notna().sum()
    if google_before_2004 > 0:
        warnings.append(f"Found {google_before_2004} Google search values before 2004")

    is_valid = len(errors) == 0

    if is_valid:
        logger.info("Data validation PASSED")
    else:
        logger.error(f"Data validation FAILED with {len(errors)} errors")

    for warning in warnings:
        logger.warning(warning)

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        stats=stats,
    )


if __name__ == "__main__":
    from src.extract.loader import load_raw_data

    raw_df = load_raw_data()
    clean_df = clean_data(raw_df)
    result = validate_data(clean_df)

    print(f"\nValidation: {'PASSED' if result.is_valid else 'FAILED'}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Stats: {result.stats}")
