"""
ETL Pipeline for Deaths per TWh Energy Production.

Data sources: Markandya & Wilkinson (2007), Sovacool et al. (2016), Our World in Data.
Compares death rates from different energy sources per terawatt-hour of electricity.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import EnergyDeathsDatabase


# Energy source categories
ENERGY_CATEGORIES = {
    "Brown coal": "Fossil Fuels",
    "Coal": "Fossil Fuels",
    "Oil": "Fossil Fuels",
    "Gas": "Fossil Fuels",
    "Biomass": "Biomass",
    "Hydropower": "Renewables",
    "Nuclear": "Nuclear",
    "Solar": "Renewables",
    "Wind": "Renewables",
}

# Safety tier based on deaths per TWh
def classify_safety(deaths_per_twh: float) -> str:
    """Classify energy source by safety tier."""
    if pd.isna(deaths_per_twh):
        return "No Data"
    if deaths_per_twh < 0.1:
        return "Extremely Safe (<0.1)"
    elif deaths_per_twh < 1:
        return "Very Safe (0.1-1)"
    elif deaths_per_twh < 5:
        return "Safe (1-5)"
    elif deaths_per_twh < 20:
        return "Moderate (5-20)"
    else:
        return "High Risk (20+)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the energy deaths data."""
    logger.info("Transforming energy deaths data...")

    # Rename columns
    df = df.rename(columns={
        "Entity": "energy_source",
        "Year": "year",
        "Deaths per TWh of electricity production": "deaths_per_twh",
    })

    # Add category
    df["category"] = df["energy_source"].map(ENERGY_CATEGORIES)
    df["category"] = df["category"].fillna("Other")

    # Add safety tier
    df["safety_tier"] = df["deaths_per_twh"].apply(classify_safety)

    # Calculate relative danger (compared to safest - solar)
    safest_rate = df["deaths_per_twh"].min()
    df["relative_danger"] = df["deaths_per_twh"] / safest_rate

    # Add rank
    df["safety_rank"] = df["deaths_per_twh"].rank(method="min").astype(int)

    # Sort by deaths (most dangerous first)
    df = df.sort_values("deaths_per_twh", ascending=False).reset_index(drop=True)

    logger.info(f"Processed {len(df)} energy sources")

    # Create category summary
    category_summary = df.groupby("category").agg({
        "energy_source": "count",
        "deaths_per_twh": ["mean", "min", "max"],
    }).reset_index()
    category_summary.columns = ["category", "sources", "avg_deaths", "min_deaths", "max_deaths"]
    category_summary = category_summary.sort_values("avg_deaths", ascending=False)

    logger.info(f"Created summary for {len(category_summary)} categories")

    return df, category_summary


def load(main_df: pd.DataFrame, category_df: pd.DataFrame, db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with EnergyDeathsDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, category_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_energy_deaths_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "energy_deaths.csv"

    logger.info("=" * 50)
    logger.info("Starting Energy Deaths ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    main_df, category_df = transform(raw_df)
    stats = load(main_df, category_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Energy sources: {stats['sources']}")
    logger.info(f"Most dangerous: {stats['most_dangerous']} ({stats['highest_deaths']:.1f} deaths/TWh)")
    logger.info(f"Safest: {stats['safest']} ({stats['lowest_deaths']:.3f} deaths/TWh)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_energy_deaths_pipeline()
