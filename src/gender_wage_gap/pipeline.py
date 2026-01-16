"""
Gender Wage Gap ETL Pipeline

Processes OECD gender wage gap data (2017).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "gender_wage_gap.csv"

# Region mapping
REGION_MAPPING = {
    # Europe - Nordic
    "Denmark": "Nordic", "Finland": "Nordic", "Iceland": "Nordic",
    "Norway": "Nordic", "Sweden": "Nordic",

    # Europe - Western
    "Austria": "Western Europe", "Belgium": "Western Europe", "France": "Western Europe",
    "Germany": "Western Europe", "Ireland": "Western Europe", "Luxembourg": "Western Europe",
    "Netherlands": "Western Europe", "Switzerland": "Western Europe", "United Kingdom": "Western Europe",

    # Europe - Southern
    "Greece": "Southern Europe", "Italy": "Southern Europe", "Portugal": "Southern Europe",
    "Spain": "Southern Europe", "Turkey": "Southern Europe",

    # Europe - Eastern/Central
    "Czech Republic": "Central/Eastern Europe", "Estonia": "Central/Eastern Europe",
    "Hungary": "Central/Eastern Europe", "Latvia": "Central/Eastern Europe",
    "Lithuania": "Central/Eastern Europe", "Poland": "Central/Eastern Europe",
    "Slovakia": "Central/Eastern Europe", "Slovenia": "Central/Eastern Europe",

    # North America
    "Canada": "North America", "United States": "North America", "Mexico": "North America",

    # Asia-Pacific
    "Australia": "Asia-Pacific", "Japan": "Asia-Pacific", "South Korea": "Asia-Pacific",
    "New Zealand": "Asia-Pacific",

    # Latin America
    "Chile": "Latin America", "Colombia": "Latin America", "Costa Rica": "Latin America",

    # Middle East
    "Israel": "Middle East",
}


def get_gap_tier(gap: float) -> str:
    """Classify wage gap into tiers."""
    if pd.isna(gap):
        return "Unknown"
    if gap < 10:
        return "Low (<10%)"
    elif gap < 15:
        return "Moderate (10-15%)"
    elif gap < 20:
        return "High (15-20%)"
    else:
        return "Very High (>20%)"


def load_raw_data() -> pd.DataFrame:
    """Load raw gender wage gap data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading gender wage gap data from: {file_path}")
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
        'Gender wage gap (OECD 2017)': 'wage_gap'
    })

    # Add region
    df['region'] = df['country'].map(REGION_MAPPING).fillna("Other")

    # Add decade
    df['decade'] = (df['year'] // 10 * 10).astype(str) + 's'

    # Add gap tier
    df['gap_tier'] = df['wage_gap'].apply(get_gap_tier)

    # Reorder columns
    df = df[['country', 'year', 'region', 'wage_gap', 'decade', 'gap_tier']]

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

        gap_change = latest['wage_gap'] - earliest['wage_gap'] if len(country_data) > 1 else None

        summaries.append({
            'country': country,
            'region': latest['region'],
            'latest_year': int(latest['year']),
            'latest_gap': round(latest['wage_gap'], 2),
            'earliest_year': int(earliest['year']),
            'earliest_gap': round(earliest['wage_gap'], 2),
            'gap_change': round(gap_change, 2) if gap_change is not None else None,
            'data_points': len(country_data),
            'avg_gap': round(country_data['wage_gap'].mean(), 2),
            'min_gap': round(country_data['wage_gap'].min(), 2),
            'max_gap': round(country_data['wage_gap'].max(), 2),
            'gap_tier': get_gap_tier(latest['wage_gap']),
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
        'wage_gap': ['mean', 'min', 'max'],
    }).round(2)

    region_stats.columns = ['countries', 'avg_gap', 'min_gap', 'max_gap']
    region_stats = region_stats.reset_index()
    region_stats = region_stats.sort_values('avg_gap', ascending=True)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_decade_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create decade-level trends."""
    logger.info("Creating decade summary...")

    decade_stats = df.groupby('decade').agg({
        'wage_gap': ['mean', 'min', 'max'],
        'country': 'nunique',
    }).round(2)

    decade_stats.columns = ['avg_gap', 'min_gap', 'max_gap', 'countries_with_data']
    decade_stats = decade_stats.reset_index()
    decade_stats = decade_stats.sort_values('decade')

    logger.info(f"Created summary for {len(decade_stats)} decades")

    return decade_stats


def run_gender_wage_gap_pipeline(save_files: bool = True) -> dict:
    """Run the complete gender wage gap pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Gender Wage Gap Pipeline")
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
        enriched_df.to_csv(PROCESSED_PATH / "gender_wage_gap_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "gender_wage_gap_countries.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "gender_wage_gap_regions.csv", index=False)
        decade_summary.to_csv(PROCESSED_PATH / "gender_wage_gap_decades.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import GenderWageGapDatabase

    with GenderWageGapDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, decade_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Year range: {stats['years'][0]}-{stats['years'][1]}")
    logger.info(f"  Average wage gap: {stats['latest_avg_gap']}%")
    logger.info(f"  Most equal: {stats['most_equal_country']} ({stats['most_equal_gap']}%)")

    return stats


if __name__ == "__main__":
    stats = run_gender_wage_gap_pipeline()
    print(json.dumps(stats, indent=2, default=str))
