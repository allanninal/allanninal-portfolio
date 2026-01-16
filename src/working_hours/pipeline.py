"""
Working Hours ETL Pipeline

Processes Huberman & Minns (2007) working hours data (1870-2000).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "working_hours.csv"

# Region mapping for 14 countries
REGION_MAPPING = {
    # Europe - Western
    "Belgium": "Western Europe",
    "France": "Western Europe",
    "Germany": "Western Europe",
    "Ireland": "Western Europe",
    "Netherlands": "Western Europe",
    "Switzerland": "Western Europe",
    "United Kingdom": "Western Europe",

    # Europe - Southern
    "Italy": "Southern Europe",
    "Spain": "Southern Europe",

    # Europe - Nordic
    "Denmark": "Nordic",
    "Sweden": "Nordic",

    # North America
    "Canada": "North America",
    "United States": "North America",

    # Oceania
    "Australia": "Oceania",
}


def get_hours_category(weekly_hours: float) -> str:
    """Classify weekly working hours into categories."""
    if pd.isna(weekly_hours):
        return "Unknown"
    if weekly_hours < 40:
        return "Short (<40h)"
    elif weekly_hours < 45:
        return "Standard (40-45h)"
    elif weekly_hours < 50:
        return "Long (45-50h)"
    elif weekly_hours < 60:
        return "Very Long (50-60h)"
    else:
        return "Extreme (60+h)"


def load_raw_data() -> pd.DataFrame:
    """Load raw working hours data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading working hours data from: {file_path}")
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
        'Full-time production workers (male and female) in non-agricultural activities (Weekly Work Hours) (Huberman & Minns (2007)) ': 'weekly_hours',
        'Full-time production workers (male and female) in non-agricultural activities (Annual Work Hours) (Huberman & Minns (2007))': 'annual_hours',
        'Weeks Worked': 'weeks_worked',
        'Days of Vacation and Holidays': 'vacation_days'
    })

    # Add region
    df['region'] = df['country'].map(REGION_MAPPING).fillna("Other")

    # Add era classification
    def get_era(year):
        if year < 1900:
            return "Pre-1900"
        elif year < 1914:
            return "Pre-WWI"
        elif year < 1939:
            return "Interwar"
        elif year < 1950:
            return "WWII Era"
        elif year < 1980:
            return "Post-War"
        else:
            return "Modern"

    df['era'] = df['year'].apply(get_era)

    # Add hours category
    df['hours_category'] = df['weekly_hours'].apply(get_hours_category)

    # Calculate daily hours (assuming 6-day work week for historical, 5-day for modern)
    df['daily_hours'] = df.apply(
        lambda row: row['weekly_hours'] / 5 if row['year'] >= 1980 else row['weekly_hours'] / 6
        if pd.notna(row['weekly_hours']) else None,
        axis=1
    )

    # Reorder columns
    df = df[['country', 'year', 'region', 'era', 'weekly_hours', 'annual_hours',
             'weeks_worked', 'vacation_days', 'hours_category', 'daily_hours']]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions, {df['era'].nunique()} eras")

    return df


def create_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create country-level summary."""
    logger.info("Creating country summary...")

    summaries = []

    for country in df['country'].unique():
        country_data = df[df['country'] == country].sort_values('year')

        if len(country_data) == 0:
            continue

        latest = country_data.dropna(subset=['weekly_hours']).iloc[-1] if len(country_data.dropna(subset=['weekly_hours'])) > 0 else country_data.iloc[-1]
        earliest = country_data.dropna(subset=['weekly_hours']).iloc[0] if len(country_data.dropna(subset=['weekly_hours'])) > 0 else country_data.iloc[0]

        weekly_change = None
        if pd.notna(latest['weekly_hours']) and pd.notna(earliest['weekly_hours']):
            weekly_change = latest['weekly_hours'] - earliest['weekly_hours']

        annual_change = None
        if pd.notna(latest['annual_hours']) and pd.notna(earliest['annual_hours']):
            annual_change = latest['annual_hours'] - earliest['annual_hours']

        # Get latest vacation days
        vacation_data = country_data.dropna(subset=['vacation_days'])
        latest_vacation = vacation_data.iloc[-1]['vacation_days'] if len(vacation_data) > 0 else None
        earliest_vacation = vacation_data.iloc[0]['vacation_days'] if len(vacation_data) > 0 else None

        summaries.append({
            'country': country,
            'region': latest['region'],
            'latest_year': int(latest['year']),
            'latest_weekly_hours': round(latest['weekly_hours'], 1) if pd.notna(latest['weekly_hours']) else None,
            'latest_annual_hours': int(latest['annual_hours']) if pd.notna(latest['annual_hours']) else None,
            'earliest_year': int(earliest['year']),
            'earliest_weekly_hours': round(earliest['weekly_hours'], 1) if pd.notna(earliest['weekly_hours']) else None,
            'weekly_change': round(weekly_change, 1) if weekly_change is not None else None,
            'annual_change': int(annual_change) if annual_change is not None else None,
            'latest_vacation_days': int(latest_vacation) if pd.notna(latest_vacation) else None,
            'vacation_change': int(latest_vacation - earliest_vacation) if pd.notna(latest_vacation) and pd.notna(earliest_vacation) else None,
            'data_points': len(country_data),
            'hours_category': get_hours_category(latest['weekly_hours']) if pd.notna(latest['weekly_hours']) else "Unknown",
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
        'weekly_hours': ['mean', 'min', 'max'],
        'annual_hours': 'mean',
        'vacation_days': 'mean',
    }).round(1)

    region_stats.columns = ['countries', 'avg_weekly', 'min_weekly', 'max_weekly', 'avg_annual', 'avg_vacation']
    region_stats = region_stats.reset_index()
    region_stats = region_stats.sort_values('avg_weekly', ascending=True)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_era_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create era-level trends."""
    logger.info("Creating era summary...")

    era_stats = df.groupby('era').agg({
        'weekly_hours': ['mean', 'min', 'max'],
        'annual_hours': 'mean',
        'vacation_days': 'mean',
        'country': 'nunique',
    }).round(1)

    era_stats.columns = ['avg_weekly', 'min_weekly', 'max_weekly', 'avg_annual', 'avg_vacation', 'countries_with_data']
    era_stats = era_stats.reset_index()

    # Sort by era order
    era_order = ['Pre-1900', 'Pre-WWI', 'Interwar', 'WWII Era', 'Post-War', 'Modern']
    era_stats['era_order'] = era_stats['era'].map({e: i for i, e in enumerate(era_order)})
    era_stats = era_stats.sort_values('era_order').drop('era_order', axis=1)

    logger.info(f"Created summary for {len(era_stats)} eras")

    return era_stats


def run_working_hours_pipeline(save_files: bool = True) -> dict:
    """Run the complete working hours pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Working Hours Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    country_summary = create_country_summary(enriched_df)
    region_summary = create_region_summary(enriched_df)
    era_summary = create_era_summary(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "working_hours_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "working_hours_countries.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "working_hours_regions.csv", index=False)
        era_summary.to_csv(PROCESSED_PATH / "working_hours_eras.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import WorkingHoursDatabase

    with WorkingHoursDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, era_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Year range: {stats['years'][0]}-{stats['years'][1]}")
    logger.info(f"  Average weekly hours (2000): {stats['latest_avg_weekly']}h")
    logger.info(f"  Shortest work week: {stats['shortest_week_country']} ({stats['shortest_week_hours']}h)")

    return stats


if __name__ == "__main__":
    stats = run_working_hours_pipeline()
    print(json.dumps(stats, indent=2, default=str))
