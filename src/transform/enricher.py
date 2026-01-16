"""Data enrichment and derived metrics calculation."""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Optional


def calculate_coverage_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the gap between actual deaths and media coverage.

    A positive gap means over-coverage (more media than deaths warrant).
    A negative gap means under-coverage (less media than deaths warrant).

    Args:
        df: Cleaned DataFrame with share columns

    Returns:
        DataFrame with coverage gap columns added.
    """
    logger.info("Calculating coverage gaps...")

    df = df.copy()

    # NYT coverage gap
    df["gap_nyt"] = df["share_nyt"] - df["share_deaths"]

    # Guardian coverage gap
    df["gap_guardian"] = df["share_guardian"] - df["share_deaths"]

    # Average media coverage (NYT + Guardian) / 2
    df["share_media_avg"] = (df["share_nyt"] + df["share_guardian"]) / 2
    df["gap_media_avg"] = df["share_media_avg"] - df["share_deaths"]

    # Google search gap (where available)
    df["gap_google"] = df["share_google"] - df["share_deaths"]

    # Coverage ratio (how many times more/less coverage than deaths)
    # Avoid division by zero for terrorism
    df["ratio_nyt"] = np.where(
        df["share_deaths"] > 0.0001,
        df["share_nyt"] / df["share_deaths"],
        np.nan
    )
    df["ratio_guardian"] = np.where(
        df["share_deaths"] > 0.0001,
        df["share_guardian"] / df["share_deaths"],
        np.nan
    )

    logger.info("Coverage gaps calculated successfully")

    return df


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add additional derived metrics for analysis.

    Metrics added:
    - Category classification (medical, external, violence)
    - Trend indicators (YoY change in coverage)
    - Attention score (combined measure of over/under coverage)

    Args:
        df: DataFrame with coverage gaps

    Returns:
        DataFrame with derived metrics added.
    """
    logger.info("Adding derived metrics...")

    df = df.copy()

    # Categorize causes of death
    category_map = {
        "Alzheimer's Disease": "chronic_disease",
        "Cancer": "chronic_disease",
        "Diabetes": "chronic_disease",
        "Heart disease": "chronic_disease",
        "Kidney disease": "chronic_disease",
        "Lower respiratory disease": "chronic_disease",
        "Stroke": "chronic_disease",
        "Pneumonia & influenza": "infectious_disease",
        "Drug overdose": "behavioral",
        "Suicide": "behavioral",
        "Road incidents": "accidents",
        "Homicide": "violence",
        "Terrorism": "violence",
    }
    df["category"] = df["cause"].map(category_map)

    # Is this cause over-represented in media? (>5% gap)
    df["is_over_covered"] = df["gap_media_avg"] > 5
    df["is_under_covered"] = df["gap_media_avg"] < -5

    # Calculate year-over-year changes in coverage
    df = df.sort_values(["cause", "year"])
    df["deaths_yoy_change"] = df.groupby("cause")["share_deaths"].diff()
    df["nyt_yoy_change"] = df.groupby("cause")["share_nyt"].diff()
    df["guardian_yoy_change"] = df.groupby("cause")["share_guardian"].diff()

    # Attention score: absolute deviation from fair coverage
    df["attention_score"] = abs(df["gap_media_avg"])

    # Period classification
    df["period"] = pd.cut(
        df["year"],
        bins=[1998, 2001, 2008, 2012, 2017],
        labels=["pre_9/11", "post_9/11", "financial_crisis", "recent"]
    )

    logger.info(f"Added {len(category_map)} categories and derived metrics")

    return df


def create_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary statistics aggregated by cause.

    Args:
        df: Enriched DataFrame

    Returns:
        Summary DataFrame with one row per cause.
    """
    logger.info("Creating summary statistics...")

    summary = df.groupby("cause").agg({
        "share_deaths": ["mean", "min", "max", "std"],
        "share_nyt": ["mean", "min", "max"],
        "share_guardian": ["mean", "min", "max"],
        "share_google": ["mean", "min", "max"],
        "gap_media_avg": ["mean", "min", "max"],
        "category": "first",
    })

    # Flatten column names
    summary.columns = ["_".join(col).strip("_") for col in summary.columns]
    summary = summary.reset_index()

    # Add ranking
    summary["death_rank"] = summary["share_deaths_mean"].rank(ascending=False).astype(int)
    summary["coverage_rank"] = summary["share_nyt_mean"].rank(ascending=False).astype(int)
    summary["gap_rank"] = summary["gap_media_avg_mean"].abs().rank(ascending=False).astype(int)

    logger.info(f"Created summary for {len(summary)} causes")

    return summary


if __name__ == "__main__":
    from src.extract.loader import load_raw_data
    from src.transform.cleaner import clean_data

    raw_df = load_raw_data()
    clean_df = clean_data(raw_df)
    enriched_df = calculate_coverage_gap(clean_df)
    enriched_df = add_derived_metrics(enriched_df)
    summary_df = create_summary_stats(enriched_df)

    print("\nTop 5 over-covered causes (avg media gap):")
    top_over = summary_df.nlargest(5, "gap_media_avg_mean")[["cause", "gap_media_avg_mean", "share_deaths_mean"]]
    print(top_over.to_string(index=False))

    print("\nTop 5 under-covered causes (avg media gap):")
    top_under = summary_df.nsmallest(5, "gap_media_avg_mean")[["cause", "gap_media_avg_mean", "share_deaths_mean"]]
    print(top_under.to_string(index=False))
