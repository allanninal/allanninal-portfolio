"""
Mobile Data Pricing ETL Pipeline

Processes the Alliance for Affordable Internet mobile data pricing data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Tuple
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
MOBILE_DATA_FILE = "Price of mobile data - Alliance for Affordable Internet (2019).csv"

# African region mapping
REGION_MAPPING = {
    # North Africa
    "Algeria": "North Africa", "Egypt": "North Africa", "Morocco": "North Africa",
    "Tunisia": "North Africa", "Sudan": "North Africa",

    # West Africa
    "Benin": "West Africa", "Burkina Faso": "West Africa", "Cape Verde": "West Africa",
    "Cote d'Ivoire": "West Africa", "Gambia": "West Africa", "Ghana": "West Africa",
    "Guinea": "West Africa", "Guinea-Bissau": "West Africa", "Liberia": "West Africa",
    "Mali": "West Africa", "Mauritania": "West Africa", "Niger": "West Africa",
    "Nigeria": "West Africa", "Senegal": "West Africa", "Sierra Leone": "West Africa",
    "Togo": "West Africa",

    # Central Africa
    "Cameroon": "Central Africa", "Central African Republic": "Central Africa",
    "Chad": "Central Africa", "Congo": "Central Africa",
    "Democratic Republic of Congo": "Central Africa", "Gabon": "Central Africa",

    # East Africa
    "Burundi": "East Africa", "Comoros": "East Africa", "Ethiopia": "East Africa",
    "Kenya": "East Africa", "Madagascar": "East Africa", "Mauritius": "East Africa",
    "Mozambique": "East Africa", "Rwanda": "East Africa", "Tanzania": "East Africa",
    "Uganda": "East Africa",

    # Southern Africa
    "Angola": "Southern Africa", "Botswana": "Southern Africa", "Lesotho": "Southern Africa",
    "Malawi": "Southern Africa", "Namibia": "Southern Africa", "South Africa": "Southern Africa",
    "Zambia": "Southern Africa", "Zimbabwe": "Southern Africa",
}

# UN affordability target
UN_AFFORDABILITY_TARGET = 2.0  # 2% of GNI is the UN target for affordable broadband


def load_raw_data() -> pd.DataFrame:
    """Load raw mobile data pricing from CSV."""
    file_path = RAW_DATA_PATH / MOBILE_DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading mobile data pricing from: {file_path}")
    df = pd.read_csv(file_path)

    # Rename columns
    df.columns = ["country", "year", "cost_pct_gni"]

    logger.info(f"Loaded {len(df):,} rows, {df['country'].nunique()} countries")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived metrics."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Add region
    df["region"] = df["country"].map(REGION_MAPPING).fillna("Other")

    # Round cost percentage
    df["cost_pct_gni"] = df["cost_pct_gni"].round(2)

    # Add affordability tier based on UN target (2% of GNI)
    def get_affordability_tier(cost):
        if cost <= UN_AFFORDABILITY_TARGET:
            return "Affordable"
        elif cost <= 5:
            return "Moderately Affordable"
        elif cost <= 10:
            return "Expensive"
        else:
            return "Unaffordable"

    df["affordability_tier"] = df["cost_pct_gni"].apply(get_affordability_tier)

    # Calculate ratio to UN target
    df["ratio_to_un_target"] = (df["cost_pct_gni"] / UN_AFFORDABILITY_TARGET).round(2)

    # Add rank (1 = most affordable)
    df["rank"] = df["cost_pct_gni"].rank(ascending=True).astype(int)

    # Calculate how many days of income for 1GB
    # (cost_pct_gni / 100) * 365 days = days of income
    df["days_of_income_per_gb"] = ((df["cost_pct_gni"] / 100) * 365).round(1)

    logger.info(f"Enrichment complete. Added region, tier, rank, and derived metrics")

    return df


def create_summary_stats(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create summary statistics."""
    logger.info("Creating summary statistics...")

    # Region summary
    region_summary = df.groupby("region").agg({
        "cost_pct_gni": ["mean", "median", "min", "max", "std", "count"],
        "country": "nunique"
    }).round(2)
    region_summary.columns = ["avg_cost", "median_cost", "min_cost", "max_cost", "std_cost", "observations", "countries"]
    region_summary = region_summary.reset_index().sort_values("avg_cost")

    # Affordability tier summary
    tier_summary = df.groupby("affordability_tier").agg({
        "country": "count",
        "cost_pct_gni": ["mean", "min", "max"]
    }).round(2)
    tier_summary.columns = ["countries", "avg_cost", "min_cost", "max_cost"]
    tier_summary = tier_summary.reset_index()

    # Define order
    tier_order = ["Affordable", "Moderately Affordable", "Expensive", "Unaffordable"]
    tier_summary["affordability_tier"] = pd.Categorical(
        tier_summary["affordability_tier"],
        categories=tier_order,
        ordered=True
    )
    tier_summary = tier_summary.sort_values("affordability_tier")

    logger.info(f"Created summaries: {len(region_summary)} regions, {len(tier_summary)} tiers")

    return region_summary, tier_summary


def run_mobile_data_pipeline(save_files: bool = True) -> dict:
    """Run the complete mobile data pricing pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Mobile Data Pricing Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    region_summary, tier_summary = create_summary_stats(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "mobile_data_enriched.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "mobile_data_region_summary.csv", index=False)
        tier_summary.to_csv(PROCESSED_PATH / "mobile_data_tier_summary.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import MobileDataDatabase

    with MobileDataDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, region_summary, tier_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    most_affordable = enriched_df.nsmallest(3, 'cost_pct_gni')
    logger.info("\nMost Affordable Countries:")
    for _, row in most_affordable.iterrows():
        logger.info(f"  {row['rank']}. {row['country']}: {row['cost_pct_gni']}% of GNI")

    least_affordable = enriched_df.nlargest(3, 'cost_pct_gni')
    logger.info("\nLeast Affordable Countries:")
    for _, row in least_affordable.iterrows():
        logger.info(f"  {row['rank']}. {row['country']}: {row['cost_pct_gni']}% of GNI")

    # Calculate key stats
    affordable_count = len(enriched_df[enriched_df['cost_pct_gni'] <= UN_AFFORDABILITY_TARGET])
    unaffordable_count = len(enriched_df[enriched_df['cost_pct_gni'] > 10])

    return {
        "rows": len(enriched_df),
        "countries": enriched_df["country"].nunique(),
        "regions": enriched_df["region"].nunique(),
        "year": int(enriched_df["year"].iloc[0]),
        "affordable_countries": affordable_count,
        "unaffordable_countries": unaffordable_count,
        "database": stats,
    }


if __name__ == "__main__":
    stats = run_mobile_data_pipeline()
    print(json.dumps(stats, indent=2, default=str))
