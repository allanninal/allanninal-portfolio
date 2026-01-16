"""
ETL pipeline for Gini Coefficients (OECD 2016).

Measures income inequality across OECD countries.
Gini ranges 0 (perfect equality) to 1 (perfect inequality).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import GiniCoefficientsDatabase


def classify_inequality_tier(gini: float) -> str:
    """Classify Gini coefficient into inequality tiers."""
    if gini < 0.25:
        return "Very Low"
    elif gini < 0.30:
        return "Low"
    elif gini < 0.35:
        return "Moderate"
    elif gini < 0.40:
        return "High"
    else:
        return "Very High"


def classify_redistribution(reduction_pct: float) -> str:
    """Classify redistribution effectiveness."""
    if reduction_pct >= 40:
        return "Very Strong"
    elif reduction_pct >= 30:
        return "Strong"
    elif reduction_pct >= 20:
        return "Moderate"
    elif reduction_pct >= 10:
        return "Weak"
    else:
        return "Very Weak"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV."""
    logger.info(f"Extracting data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform data into analysis-ready format."""
    logger.info("Transforming data...")

    # Rename columns
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "Gini coefficient (income after taxes and transfers) (OECD Income Distribution Database (2016))": "gini_post_tax",
        "Gini  coefficient (before taxes and transfers) (OECD Income Distribution Database (2016))": "gini_pre_tax"
    })

    # Calculate redistribution effect
    df["gini_reduction"] = df["gini_pre_tax"] - df["gini_post_tax"]
    df["reduction_pct"] = ((df["gini_pre_tax"] - df["gini_post_tax"]) / df["gini_pre_tax"] * 100).round(1)

    # Add inequality tier (based on post-tax)
    df["inequality_tier"] = df["gini_post_tax"].apply(classify_inequality_tier)

    # Add redistribution tier
    df["redistribution_tier"] = df["reduction_pct"].apply(classify_redistribution)

    logger.info(f"Countries: {df['country'].nunique()}")
    logger.info(f"Years: {df['year'].min()} to {df['year'].max()}")

    # Get latest year data for each country (for summary)
    latest_data = df.loc[df.groupby('country')['year'].idxmax()].copy()

    # Country summary (using latest year for each country)
    country_summary = latest_data[['country', 'year', 'gini_post_tax', 'gini_pre_tax',
                                    'gini_reduction', 'reduction_pct', 'inequality_tier',
                                    'redistribution_tier']].copy()
    country_summary = country_summary.round(3)

    # Tier summary (using latest data)
    tier_summary = latest_data.groupby('inequality_tier').agg(
        countries=('country', 'count'),
        avg_gini_post=('gini_post_tax', 'mean'),
        avg_gini_pre=('gini_pre_tax', 'mean'),
        avg_reduction_pct=('reduction_pct', 'mean')
    ).reset_index()
    tier_summary = tier_summary.round(3)

    return df, country_summary, tier_summary


def load(main_df: pd.DataFrame, country_df: pd.DataFrame, tier_df: pd.DataFrame,
         db_path: Path = None):
    """Load data into database."""
    logger.info("Loading data into database...")

    with GiniCoefficientsDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, country_df, tier_df)

        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")

    return stats


def run_gini_coefficients_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the full ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "gini_coefficients.csv"

    logger.info("Starting Gini Coefficients pipeline...")

    # ETL
    raw_df = extract(data_path)
    main_df, country_df, tier_df = transform(raw_df)
    stats = load(main_df, country_df, tier_df, db_path)

    logger.info("Pipeline completed successfully!")
    return stats


if __name__ == "__main__":
    stats = run_gini_coefficients_pipeline()
    print("\nPipeline Results:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
