"""
World Happiness Report ETL Pipeline

Processes the World Happiness Report data and loads it into DuckDB.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Tuple
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
HAPPINESS_FILE = "World Happiness Report (2022).csv"

# Region mapping for countries
REGION_MAPPING = {
    # Western Europe
    "Finland": "Western Europe", "Denmark": "Western Europe", "Iceland": "Western Europe",
    "Switzerland": "Western Europe", "Netherlands": "Western Europe", "Norway": "Western Europe",
    "Sweden": "Western Europe", "Luxembourg": "Western Europe", "Austria": "Western Europe",
    "Germany": "Western Europe", "Belgium": "Western Europe", "Ireland": "Western Europe",
    "United Kingdom": "Western Europe", "France": "Western Europe", "Spain": "Western Europe",
    "Portugal": "Western Europe", "Italy": "Western Europe", "Malta": "Western Europe",

    # North America
    "Canada": "North America", "United States": "North America",

    # Latin America
    "Costa Rica": "Latin America", "Mexico": "Latin America", "Brazil": "Latin America",
    "Chile": "Latin America", "Panama": "Latin America", "Uruguay": "Latin America",
    "Guatemala": "Latin America", "Argentina": "Latin America", "Colombia": "Latin America",
    "El Salvador": "Latin America", "Nicaragua": "Latin America", "Honduras": "Latin America",
    "Paraguay": "Latin America", "Peru": "Latin America", "Ecuador": "Latin America",
    "Bolivia": "Latin America", "Venezuela": "Latin America", "Dominican Republic": "Latin America",
    "Jamaica": "Latin America", "Trinidad and Tobago": "Latin America", "Haiti": "Latin America",

    # East Asia
    "Japan": "East Asia", "South Korea": "East Asia", "Taiwan": "East Asia",
    "China": "East Asia", "Hong Kong": "East Asia", "Mongolia": "East Asia",

    # Southeast Asia
    "Singapore": "Southeast Asia", "Thailand": "Southeast Asia", "Malaysia": "Southeast Asia",
    "Vietnam": "Southeast Asia", "Philippines": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Cambodia": "Southeast Asia", "Myanmar": "Southeast Asia", "Laos": "Southeast Asia",

    # South Asia
    "India": "South Asia", "Pakistan": "South Asia", "Bangladesh": "South Asia",
    "Sri Lanka": "South Asia", "Nepal": "South Asia", "Bhutan": "South Asia",

    # Middle East
    "Israel": "Middle East", "United Arab Emirates": "Middle East", "Saudi Arabia": "Middle East",
    "Bahrain": "Middle East", "Kuwait": "Middle East", "Qatar": "Middle East",
    "Jordan": "Middle East", "Lebanon": "Middle East", "Turkey": "Middle East",
    "Iran": "Middle East", "Iraq": "Middle East", "Yemen": "Middle East", "Syria": "Middle East",

    # Central & Eastern Europe
    "Czechia": "Central & Eastern Europe", "Slovenia": "Central & Eastern Europe",
    "Poland": "Central & Eastern Europe", "Slovakia": "Central & Eastern Europe",
    "Lithuania": "Central & Eastern Europe", "Estonia": "Central & Eastern Europe",
    "Latvia": "Central & Eastern Europe", "Hungary": "Central & Eastern Europe",
    "Romania": "Central & Eastern Europe", "Croatia": "Central & Eastern Europe",
    "Bulgaria": "Central & Eastern Europe", "Serbia": "Central & Eastern Europe",
    "Bosnia and Herzegovina": "Central & Eastern Europe", "Montenegro": "Central & Eastern Europe",
    "North Macedonia": "Central & Eastern Europe", "Albania": "Central & Eastern Europe",
    "Kosovo": "Central & Eastern Europe", "Moldova": "Central & Eastern Europe",

    # Commonwealth of Independent States
    "Russia": "CIS", "Ukraine": "CIS", "Belarus": "CIS", "Kazakhstan": "CIS",
    "Uzbekistan": "CIS", "Kyrgyzstan": "CIS", "Tajikistan": "CIS", "Turkmenistan": "CIS",
    "Azerbaijan": "CIS", "Armenia": "CIS", "Georgia": "CIS",

    # Sub-Saharan Africa
    "Mauritius": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa",
    "Senegal": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa", "Uganda": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa", "Malawi": "Sub-Saharan Africa",
    "Mali": "Sub-Saharan Africa", "Niger": "Sub-Saharan Africa", "Burkina Faso": "Sub-Saharan Africa",
    "Benin": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa", "Guinea": "Sub-Saharan Africa", "Ivory Coast": "Sub-Saharan Africa",
    "Madagascar": "Sub-Saharan Africa", "Mozambique": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Namibia": "Sub-Saharan Africa", "Congo": "Sub-Saharan Africa", "Gabon": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa",
    "Democratic Republic of Congo": "Sub-Saharan Africa", "Angola": "Sub-Saharan Africa",
    "Comoros": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa", "Eswatini": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa", "Gambia": "Sub-Saharan Africa", "Somalia": "Sub-Saharan Africa",
    "South Sudan": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa",

    # North Africa
    "Egypt": "North Africa", "Morocco": "North Africa", "Algeria": "North Africa",
    "Tunisia": "North Africa", "Libya": "North Africa",

    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania",
}


def load_raw_data() -> pd.DataFrame:
    """Load raw happiness data from CSV."""
    file_path = RAW_DATA_PATH / HAPPINESS_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading happiness data from: {file_path}")
    df = pd.read_csv(file_path)

    # Rename columns for easier handling
    df.columns = ["country", "year", "happiness_score"]

    logger.info(f"Loaded {len(df):,} rows, {df['country'].nunique()} countries, years {df['year'].min()}-{df['year'].max()}")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived metrics."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Add region
    df["region"] = df["country"].map(REGION_MAPPING).fillna("Other")

    # Round happiness score
    df["happiness_score"] = df["happiness_score"].round(2)

    # Add happiness tier
    df["happiness_tier"] = pd.cut(
        df["happiness_score"],
        bins=[0, 4, 5, 6, 7, 10],
        labels=["Very Low", "Low", "Medium", "High", "Very High"]
    )

    # Calculate year-over-year change
    df = df.sort_values(["country", "year"])
    df["yoy_change"] = df.groupby("country")["happiness_score"].diff().round(3)

    # Calculate country average and rank
    country_avg = df.groupby("country")["happiness_score"].mean()
    df["country_avg"] = df["country"].map(country_avg).round(2)

    # Latest year rank
    latest_year = df["year"].max()
    latest = df[df["year"] == latest_year].copy()
    latest["rank"] = latest["happiness_score"].rank(ascending=False).astype(int)
    df = df.merge(latest[["country", "rank"]], on="country", how="left", suffixes=("", "_latest"))
    df["rank"] = df["rank"].fillna(0).astype(int)

    logger.info(f"Enrichment complete. Added region, tier, YoY change, and rankings")

    return df


def create_summary_stats(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create summary statistics."""
    logger.info("Creating summary statistics...")

    latest_year = df["year"].max()
    latest = df[df["year"] == latest_year].copy()

    # Country summary (latest year)
    country_summary = latest[["country", "region", "happiness_score", "happiness_tier", "rank"]].copy()
    country_summary = country_summary.sort_values("rank")

    # Region summary
    region_summary = df.groupby("region").agg({
        "happiness_score": ["mean", "std", "min", "max", "count"],
        "country": "nunique"
    }).round(2)
    region_summary.columns = ["avg_score", "std_score", "min_score", "max_score", "observations", "countries"]
    region_summary = region_summary.reset_index().sort_values("avg_score", ascending=False)

    # Year summary (global averages)
    year_summary = df.groupby("year").agg({
        "happiness_score": ["mean", "std", "min", "max"],
        "country": "nunique"
    }).round(2)
    year_summary.columns = ["global_avg", "std", "min", "max", "countries"]
    year_summary = year_summary.reset_index()

    logger.info(f"Created summaries: {len(country_summary)} countries, {len(region_summary)} regions, {len(year_summary)} years")

    return country_summary, region_summary, year_summary


def run_happiness_pipeline(save_files: bool = True) -> dict:
    """Run the complete happiness data pipeline."""
    logger.info("=" * 60)
    logger.info("Starting World Happiness Report Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    country_summary, region_summary, year_summary = create_summary_stats(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "happiness_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "happiness_country_summary.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "happiness_region_summary.csv", index=False)
        year_summary.to_csv(PROCESSED_PATH / "happiness_year_summary.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import HappinessDatabase

    with HappinessDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, year_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    happiest = country_summary.head(5)
    logger.info("\nTop 5 Happiest Countries:")
    for _, row in happiest.iterrows():
        logger.info(f"  {row['rank']}. {row['country']}: {row['happiness_score']}")

    return {
        "rows": len(enriched_df),
        "countries": enriched_df["country"].nunique(),
        "regions": enriched_df["region"].nunique(),
        "year_range": (int(enriched_df["year"].min()), int(enriched_df["year"].max())),
        "database": stats,
    }


if __name__ == "__main__":
    stats = run_happiness_pipeline()
    print(json.dumps(stats, indent=2, default=str))
