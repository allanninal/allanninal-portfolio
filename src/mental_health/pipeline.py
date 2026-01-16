"""
ETL Pipeline for Mental Health Services across Incomes (Wang et al. 2007).

Based on WHO World Mental Health Surveys in 17 countries (2001-2004).
Examines treatment rates by severity and service type across income levels.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import MentalHealthDatabase


# Income group classification based on GDP healthcare spending
def classify_income_group(gdp_health: float) -> str:
    """Classify country by healthcare spending as income proxy."""
    if pd.isna(gdp_health):
        return "No Data"
    if gdp_health >= 10:
        return "High Income"
    elif gdp_health >= 7:
        return "Upper-Middle"
    elif gdp_health >= 5:
        return "Lower-Middle"
    else:
        return "Low Income"


def classify_treatment_gap(severe_rate: float) -> str:
    """Classify treatment gap for severe mental illness."""
    if pd.isna(severe_rate):
        return "No Data"
    if severe_rate >= 50:
        return "Low Gap (<50% untreated)"
    elif severe_rate >= 30:
        return "Moderate Gap (50-70% untreated)"
    elif severe_rate >= 20:
        return "High Gap (70-80% untreated)"
    else:
        return "Very High Gap (80%+ untreated)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the mental health services data."""
    logger.info("Transforming mental health services data...")

    # Rename columns
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "Share of GDP spent on healthcare": "gdp_healthcare",
        "Share receiving any treatment for mental health": "any_treatment",
        "Mental health specialty (%)": "specialty_pct",
        "General medical (%)": "general_medical_pct",
        "Human services (%)": "human_services_pct",
        "Complementary & alternative medicine (%)": "alternative_pct",
        "Severe mental health who received treatment in last year (%)": "severe_treated",
        "Moderate mental health who received treatment in last year (%)": "moderate_treated",
        "Mild mental health who received treatment in last year (%)": "mild_treated",
    })

    # Add income group classification
    df["income_group"] = df["gdp_healthcare"].apply(classify_income_group)

    # Add treatment gap classification
    df["treatment_gap"] = df["severe_treated"].apply(classify_treatment_gap)

    # Calculate treatment gaps (100 - treatment rate)
    df["severe_untreated"] = 100 - df["severe_treated"]
    df["moderate_untreated"] = 100 - df["moderate_treated"]
    df["mild_untreated"] = 100 - df["mild_treated"]

    # Calculate primary service preference (which sector dominates)
    service_cols = ["specialty_pct", "general_medical_pct", "human_services_pct", "alternative_pct"]
    df["primary_service"] = df[service_cols].idxmax(axis=1).map({
        "specialty_pct": "Mental Health Specialty",
        "general_medical_pct": "General Medical",
        "human_services_pct": "Human Services",
        "alternative_pct": "Alternative Medicine"
    })

    # Sort by treatment rate
    df = df.sort_values("any_treatment", ascending=False).reset_index(drop=True)

    logger.info(f"Processed {len(df)} countries")

    # Create income group summary
    income_summary = df.groupby("income_group").agg({
        "country": "count",
        "gdp_healthcare": "mean",
        "any_treatment": "mean",
        "severe_treated": "mean",
        "moderate_treated": "mean",
        "mild_treated": "mean",
    }).reset_index()
    income_summary.columns = [
        "income_group", "countries", "avg_gdp_health", "avg_any_treatment",
        "avg_severe_treated", "avg_moderate_treated", "avg_mild_treated"
    ]
    logger.info(f"Created summary for {len(income_summary)} income groups")

    # Create service sector summary (global averages)
    service_summary = pd.DataFrame({
        "service_type": ["Mental Health Specialty", "General Medical", "Human Services", "Alternative Medicine"],
        "avg_usage": [
            df["specialty_pct"].mean(),
            df["general_medical_pct"].mean(),
            df["human_services_pct"].mean(),
            df["alternative_pct"].mean()
        ],
        "min_usage": [
            df["specialty_pct"].min(),
            df["general_medical_pct"].min(),
            df["human_services_pct"].min(),
            df["alternative_pct"].min()
        ],
        "max_usage": [
            df["specialty_pct"].max(),
            df["general_medical_pct"].max(),
            df["human_services_pct"].max(),
            df["alternative_pct"].max()
        ]
    })
    logger.info(f"Created summary for {len(service_summary)} service types")

    return df, income_summary, service_summary


def load(main_df: pd.DataFrame, income_df: pd.DataFrame,
         service_df: pd.DataFrame, db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with MentalHealthDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, income_df, service_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_mental_health_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "mental_health_services.csv"

    logger.info("=" * 50)
    logger.info("Starting Mental Health Services ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    main_df, income_df, service_df = transform(raw_df)
    stats = load(main_df, income_df, service_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Countries: {stats['countries']}")
    logger.info(f"Highest treatment: {stats['highest_treatment_country']} ({stats['highest_treatment']:.1f}%)")
    logger.info(f"Lowest treatment: {stats['lowest_treatment_country']} ({stats['lowest_treatment']:.1f}%)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_mental_health_pipeline()
