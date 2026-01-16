"""
Female Labor Force Participation ETL Pipeline

Processes OECD/OWID female labor participation data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "female_labor_participation.csv"

# Region mapping
REGION_MAPPING = {
    # Europe
    "Austria": "Europe", "Belgium": "Europe", "Czech Republic": "Europe",
    "Denmark": "Europe", "Estonia": "Europe", "Finland": "Europe",
    "France": "Europe", "Germany": "Europe", "Greece": "Europe",
    "Hungary": "Europe", "Iceland": "Europe", "Ireland": "Europe",
    "Italy": "Europe", "Latvia": "Europe", "Luxembourg": "Europe",
    "Netherlands": "Europe", "Norway": "Europe", "Poland": "Europe",
    "Portugal": "Europe", "Slovak Republic": "Europe", "Slovenia": "Europe",
    "Spain": "Europe", "Sweden": "Europe", "Switzerland": "Europe",
    "United Kingdom": "Europe",

    # North America
    "Canada": "North America", "United States": "North America", "Mexico": "North America",

    # Asia-Pacific
    "Australia": "Asia-Pacific", "Japan": "Asia-Pacific", "South Korea": "Asia-Pacific",
    "New Zealand": "Asia-Pacific", "China": "Asia-Pacific", "India": "Asia-Pacific",
    "Indonesia": "Asia-Pacific",

    # Latin America
    "Brazil": "Latin America", "Chile": "Latin America", "Colombia": "Latin America",

    # Middle East
    "Israel": "Middle East", "Turkey": "Middle East",

    # Aggregate
    "OECD countries": "OECD Aggregate",
}


def load_raw_data() -> pd.DataFrame:
    """Load raw female labor participation data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading female labor data from: {file_path}")
    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows, {df['Entity'].nunique()} countries")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived fields."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Rename columns
    df = df.rename(columns={
        'Entity': 'country',
        'Year': 'year',
        'Female labor force participation rate (OWID based on OECD 2017 and others)': 'participation_rate'
    })

    # Add region
    df['region'] = df['country'].map(REGION_MAPPING).fillna("Other")

    # Add decade
    df['decade'] = (df['year'] // 10 * 10).astype(str) + 's'

    # Reorder columns
    df = df[['country', 'year', 'region', 'participation_rate', 'decade']]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions")

    return df


def create_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create country-level summary."""
    logger.info("Creating country summary...")

    summaries = []

    for country in df['country'].unique():
        country_data = df[df['country'] == country].sort_values('year')

        if len(country_data) == 0:
            continue

        latest = country_data.iloc[-1]
        earliest = country_data.iloc[0]

        rate_change = latest['participation_rate'] - earliest['participation_rate'] if len(country_data) > 1 else None

        summaries.append({
            'country': country,
            'region': latest['region'],
            'latest_year': int(latest['year']),
            'latest_rate': round(latest['participation_rate'], 2),
            'earliest_year': int(earliest['year']),
            'earliest_rate': round(earliest['participation_rate'], 2),
            'rate_change': round(rate_change, 2) if rate_change else None,
            'data_points': len(country_data),
            'avg_rate': round(country_data['participation_rate'].mean(), 2),
            'max_rate': round(country_data['participation_rate'].max(), 2),
            'min_rate': round(country_data['participation_rate'].min(), 2),
        })

    summary_df = pd.DataFrame(summaries)
    logger.info(f"Created summary for {len(summary_df)} countries")

    return summary_df


def create_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create regional summary statistics."""
    logger.info("Creating region summary...")

    # Use latest year for each country
    latest_per_country = df.loc[df.groupby('country')['year'].idxmax()]

    region_stats = latest_per_country.groupby('region').agg({
        'country': 'count',
        'participation_rate': ['mean', 'min', 'max'],
    }).round(2)

    region_stats.columns = ['countries', 'avg_rate', 'min_rate', 'max_rate']
    region_stats = region_stats.reset_index()

    # Add total data points per region
    data_points = df.groupby('region').size().reset_index(name='total_data_points')
    region_stats = region_stats.merge(data_points, on='region')

    region_stats = region_stats.sort_values('avg_rate', ascending=False)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_decade_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create decade-level trends."""
    logger.info("Creating decade summary...")

    decade_stats = df.groupby('decade').agg({
        'participation_rate': ['mean', 'min', 'max'],
        'country': 'nunique',
    }).round(2)

    decade_stats.columns = ['avg_rate', 'min_rate', 'max_rate', 'countries_with_data']
    decade_stats = decade_stats.reset_index()
    decade_stats = decade_stats.sort_values('decade')

    logger.info(f"Created summary for {len(decade_stats)} decades")

    return decade_stats


def run_female_labor_pipeline(save_files: bool = True) -> dict:
    """Run the complete female labor pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Female Labor Force Participation Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    country_summary = create_country_summary(enriched_df)
    region_summary = create_region_summary(enriched_df)
    decade_summary = create_decade_summary(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "female_labor_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "female_labor_countries.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "female_labor_regions.csv", index=False)
        decade_summary.to_csv(PROCESSED_PATH / "female_labor_decades.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import FemaleLaborDatabase

    with FemaleLaborDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, decade_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Year range: {stats['years'][0]}-{stats['years'][1]}")
    logger.info(f"  Latest average rate: {stats['latest_avg_rate']}%")

    return stats


if __name__ == "__main__":
    stats = run_female_labor_pipeline()
    print(json.dumps(stats, indent=2, default=str))
