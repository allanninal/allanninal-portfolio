"""
Technology Adoption ETL Pipeline

Processes US household technology adoption data from Our World in Data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Tuple
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "technology_adoption.csv"

# Technology category mapping
CATEGORY_MAPPING = {
    # Transportation
    "Automobile": "Transportation",
    "Automatic transmission": "Transportation",
    "Disk brakes": "Transportation",
    "Electronic ignition": "Transportation",
    "Power steering": "Transportation",
    "Radial tires": "Transportation",
    "Shipping container port infrastructure": "Transportation",

    # Home Appliances
    "Dishwasher": "Home Appliances",
    "Dryer": "Home Appliances",
    "Electric Range": "Home Appliances",
    "Freezer": "Home Appliances",
    "Household refrigerator": "Home Appliances",
    "Refrigerator": "Home Appliances",
    "Iron": "Home Appliances",
    "Microwave": "Home Appliances",
    "Stove": "Home Appliances",
    "Vacuum": "Home Appliances",
    "Washer": "Home Appliances",
    "Washing machine": "Home Appliances",
    "Water Heater": "Home Appliances",

    # Utilities & Infrastructure
    "Central heating": "Utilities",
    "Electric power": "Utilities",
    "Electricity access": "Utilities",
    "Flush toilet": "Utilities",
    "Home air conditioning": "Utilities",
    "Running water": "Utilities",
    "Nox pollution controls (boilers)": "Utilities",

    # Communication
    "Cellular phone": "Communication",
    "Landline": "Communication",
    "Radio": "Communication",
    "Telephone": "Communication",
    "Households with only mobile phones (no landlines)": "Communication",

    # Entertainment
    "Cable TV": "Entertainment",
    "Colour TV": "Entertainment",
    "Television": "Entertainment",
    "Videocassette recorder": "Entertainment",

    # Computing & Internet
    "Computer": "Computing",
    "Internet": "Computing",
    "Microcomputer": "Computing",
    "Smartphone usage": "Computing",
    "Tablet": "Computing",
    "Ebook reader": "Computing",

    # Digital Services
    "Amazon Prime users": "Digital Services",
    "Podcasting": "Digital Services",
    "Social media usage": "Digital Services",
    "RTGS adoption": "Digital Services",
}


def load_raw_data() -> pd.DataFrame:
    """Load raw technology adoption data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading technology adoption data from: {file_path}")
    df = pd.read_csv(file_path)

    # Rename columns
    df.columns = ["technology", "code", "year", "adoption_pct"]

    # Drop code column (always empty)
    df = df.drop(columns=["code"])

    logger.info(f"Loaded {len(df):,} rows, {df['technology'].nunique()} technologies")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived metrics."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Add category
    df["category"] = df["technology"].map(CATEGORY_MAPPING).fillna("Other")

    # Round adoption percentage
    df["adoption_pct"] = df["adoption_pct"].round(2)

    # Add decade
    df["decade"] = (df["year"] // 10 * 10).astype(str) + "s"

    # Add adoption tier
    def get_adoption_tier(pct):
        if pct >= 90:
            return "Universal"
        elif pct >= 50:
            return "Mainstream"
        elif pct >= 10:
            return "Early Majority"
        else:
            return "Early Adopters"

    df["adoption_tier"] = df["adoption_pct"].apply(get_adoption_tier)

    logger.info(f"Enrichment complete. {df['category'].nunique()} categories assigned")

    return df


def create_technology_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create technology-level summary statistics."""
    logger.info("Creating technology summary...")

    summaries = []

    for tech in df["technology"].unique():
        tech_data = df[df["technology"] == tech].sort_values("year")

        # Basic stats
        first_year = tech_data["year"].min()
        last_year = tech_data["year"].max()
        max_adoption = tech_data["adoption_pct"].max()
        current_adoption = tech_data[tech_data["year"] == last_year]["adoption_pct"].iloc[0]
        years_tracked = last_year - first_year + 1
        category = tech_data["category"].iloc[0]

        # Find year of peak adoption
        peak_year = tech_data.loc[tech_data["adoption_pct"].idxmax(), "year"]

        # Calculate years to 50% adoption
        above_50 = tech_data[tech_data["adoption_pct"] >= 50]
        if len(above_50) > 0:
            year_50 = above_50["year"].min()
            years_to_50_pct = year_50 - first_year
        else:
            years_to_50_pct = None

        summaries.append({
            "technology": tech,
            "category": category,
            "first_year": first_year,
            "last_year": last_year,
            "max_adoption": max_adoption,
            "current_adoption": current_adoption,
            "years_tracked": years_tracked,
            "years_to_50_pct": years_to_50_pct,
            "peak_year": peak_year,
        })

    summary_df = pd.DataFrame(summaries)
    logger.info(f"Created summary for {len(summary_df)} technologies")

    return summary_df


def create_category_summary(df: pd.DataFrame, tech_summary: pd.DataFrame) -> pd.DataFrame:
    """Create category-level summary statistics."""
    logger.info("Creating category summary...")

    category_stats = tech_summary.groupby("category").agg({
        "technology": "count",
        "max_adoption": "mean",
        "years_to_50_pct": "mean",
        "first_year": "min",
    }).round(2)

    category_stats.columns = ["technologies", "avg_max_adoption", "avg_years_to_peak", "oldest_tech_year"]

    # Add newest tech year
    newest_year = tech_summary.groupby("category")["first_year"].max()
    category_stats["newest_tech_year"] = newest_year

    category_stats = category_stats.reset_index()

    logger.info(f"Created summary for {len(category_stats)} categories")

    return category_stats


def create_decade_summary(df: pd.DataFrame, tech_summary: pd.DataFrame) -> pd.DataFrame:
    """Create decade-level summary statistics."""
    logger.info("Creating decade summary...")

    # Average adoption by decade
    decade_adoption = df.groupby("decade").agg({
        "adoption_pct": "mean",
        "technology": "nunique",
    }).round(2)

    decade_adoption.columns = ["avg_adoption", "technologies_tracked"]

    # Count new technologies introduced per decade (using a copy to avoid modifying tech_summary)
    intro_decades = (tech_summary["first_year"] // 10 * 10).astype(str) + "s"
    new_tech_count = intro_decades.value_counts()

    decade_adoption["new_technologies"] = decade_adoption.index.map(
        lambda x: new_tech_count.get(x, 0)
    )

    decade_summary = decade_adoption.reset_index()
    decade_summary = decade_summary.sort_values("decade")

    logger.info(f"Created summary for {len(decade_summary)} decades")

    return decade_summary


def run_technology_adoption_pipeline(save_files: bool = True) -> dict:
    """Run the complete technology adoption pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Technology Adoption Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    tech_summary = create_technology_summary(enriched_df)
    category_summary = create_category_summary(enriched_df, tech_summary)
    decade_summary = create_decade_summary(enriched_df, tech_summary)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "technology_adoption_enriched.csv", index=False)
        tech_summary.to_csv(PROCESSED_PATH / "technology_summary.csv", index=False)
        category_summary.to_csv(PROCESSED_PATH / "technology_category_summary.csv", index=False)
        decade_summary.to_csv(PROCESSED_PATH / "technology_decade_summary.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import TechnologyAdoptionDatabase

    with TechnologyAdoptionDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, tech_summary, category_summary, decade_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    fastest = tech_summary.dropna(subset=["years_to_50_pct"]).nsmallest(5, "years_to_50_pct")
    logger.info("\nFastest Technologies to 50% Adoption:")
    for _, row in fastest.iterrows():
        logger.info(f"  {row['technology']}: {int(row['years_to_50_pct'])} years (introduced {int(row['first_year'])})")

    return {
        "rows": len(enriched_df),
        "technologies": enriched_df["technology"].nunique(),
        "categories": enriched_df["category"].nunique(),
        "year_range": (int(enriched_df["year"].min()), int(enriched_df["year"].max())),
        "database": stats,
    }


if __name__ == "__main__":
    stats = run_technology_adoption_pipeline()
    print(json.dumps(stats, indent=2, default=str))
