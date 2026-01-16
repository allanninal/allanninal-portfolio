"""
Education Quality ETL Pipeline

Processes Global Data Set on Education Quality (1965-2015) from Altinok, Angrist, and Patrinos (2018).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "education_quality.csv"

# Region mapping for countries
REGION_MAPPING = {
    # East Asia & Pacific
    "Australia": "East Asia & Pacific", "China": "East Asia & Pacific",
    "Hong Kong": "East Asia & Pacific", "Indonesia": "East Asia & Pacific",
    "Japan": "East Asia & Pacific", "South Korea": "East Asia & Pacific",
    "Malaysia": "East Asia & Pacific", "New Zealand": "East Asia & Pacific",
    "Philippines": "East Asia & Pacific", "Singapore": "East Asia & Pacific",
    "Taiwan": "East Asia & Pacific", "Thailand": "East Asia & Pacific",
    "Vietnam": "East Asia & Pacific", "Cambodia": "East Asia & Pacific",
    "Macau": "East Asia & Pacific", "Myanmar": "East Asia & Pacific",

    # Europe & Central Asia
    "Albania": "Europe & Central Asia", "Armenia": "Europe & Central Asia",
    "Austria": "Europe & Central Asia", "Azerbaijan": "Europe & Central Asia",
    "Belgium": "Europe & Central Asia", "Belgium Flemish": "Europe & Central Asia",
    "Belgium French": "Europe & Central Asia", "Bosnia and Herzegovina": "Europe & Central Asia",
    "Bulgaria": "Europe & Central Asia", "Croatia": "Europe & Central Asia",
    "Cyprus": "Europe & Central Asia", "Czech Republic": "Europe & Central Asia",
    "Czechia": "Europe & Central Asia", "Denmark": "Europe & Central Asia",
    "Estonia": "Europe & Central Asia", "Finland": "Europe & Central Asia",
    "France": "Europe & Central Asia", "Georgia": "Europe & Central Asia",
    "Germany": "Europe & Central Asia", "Greece": "Europe & Central Asia",
    "Hungary": "Europe & Central Asia", "Iceland": "Europe & Central Asia",
    "Ireland": "Europe & Central Asia", "Italy": "Europe & Central Asia",
    "Kazakhstan": "Europe & Central Asia", "Kosovo": "Europe & Central Asia",
    "Kyrgyzstan": "Europe & Central Asia", "Latvia": "Europe & Central Asia",
    "Lithuania": "Europe & Central Asia", "Luxembourg": "Europe & Central Asia",
    "Malta": "Europe & Central Asia", "Moldova": "Europe & Central Asia",
    "Montenegro": "Europe & Central Asia", "Netherlands": "Europe & Central Asia",
    "North Macedonia": "Europe & Central Asia", "Macedonia": "Europe & Central Asia",
    "Norway": "Europe & Central Asia", "Poland": "Europe & Central Asia",
    "Portugal": "Europe & Central Asia", "Romania": "Europe & Central Asia",
    "Russia": "Europe & Central Asia", "Serbia": "Europe & Central Asia",
    "Slovakia": "Europe & Central Asia", "Slovenia": "Europe & Central Asia",
    "Spain": "Europe & Central Asia", "Sweden": "Europe & Central Asia",
    "Switzerland": "Europe & Central Asia", "Turkey": "Europe & Central Asia",
    "Ukraine": "Europe & Central Asia", "United Kingdom": "Europe & Central Asia",
    "England": "Europe & Central Asia", "Scotland": "Europe & Central Asia",
    "Northern Ireland": "Europe & Central Asia", "Tajikistan": "Europe & Central Asia",
    "Uzbekistan": "Europe & Central Asia",

    # Latin America & Caribbean
    "Argentina": "Latin America & Caribbean", "Brazil": "Latin America & Caribbean",
    "Chile": "Latin America & Caribbean", "Colombia": "Latin America & Caribbean",
    "Costa Rica": "Latin America & Caribbean", "Cuba": "Latin America & Caribbean",
    "Dominican Republic": "Latin America & Caribbean", "Ecuador": "Latin America & Caribbean",
    "El Salvador": "Latin America & Caribbean", "Guatemala": "Latin America & Caribbean",
    "Honduras": "Latin America & Caribbean", "Jamaica": "Latin America & Caribbean",
    "Mexico": "Latin America & Caribbean", "Nicaragua": "Latin America & Caribbean",
    "Panama": "Latin America & Caribbean", "Paraguay": "Latin America & Caribbean",
    "Peru": "Latin America & Caribbean", "Trinidad and Tobago": "Latin America & Caribbean",
    "Uruguay": "Latin America & Caribbean", "Venezuela": "Latin America & Caribbean",
    "Bolivia": "Latin America & Caribbean",

    # Middle East & North Africa
    "Algeria": "Middle East & North Africa", "Bahrain": "Middle East & North Africa",
    "Egypt": "Middle East & North Africa", "Iran": "Middle East & North Africa",
    "Iraq": "Middle East & North Africa", "Israel": "Middle East & North Africa",
    "Jordan": "Middle East & North Africa", "Kuwait": "Middle East & North Africa",
    "Lebanon": "Middle East & North Africa", "Libya": "Middle East & North Africa",
    "Morocco": "Middle East & North Africa", "Oman": "Middle East & North Africa",
    "Palestine": "Middle East & North Africa", "Qatar": "Middle East & North Africa",
    "Saudi Arabia": "Middle East & North Africa", "Syria": "Middle East & North Africa",
    "Tunisia": "Middle East & North Africa", "United Arab Emirates": "Middle East & North Africa",
    "Yemen": "Middle East & North Africa",

    # North America
    "Canada": "North America", "United States": "North America",

    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia",
    "India": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",

    # Sub-Saharan Africa
    "Benin": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa",
    "Cameroon": "Sub-Saharan Africa", "Chad": "Sub-Saharan Africa",
    "Congo": "Sub-Saharan Africa", "Cote d'Ivoire": "Sub-Saharan Africa",
    "Ethiopia": "Sub-Saharan Africa", "Gabon": "Sub-Saharan Africa",
    "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa",
    "Guinea": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa", "Liberia": "Sub-Saharan Africa",
    "Madagascar": "Sub-Saharan Africa", "Malawi": "Sub-Saharan Africa",
    "Mali": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa",
    "Mauritius": "Sub-Saharan Africa", "Mozambique": "Sub-Saharan Africa",
    "Namibia": "Sub-Saharan Africa", "Niger": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa",
    "Senegal": "Sub-Saharan Africa", "Seychelles": "Sub-Saharan Africa",
    "Sierra Leone": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa",
    "Swaziland": "Sub-Saharan Africa", "Eswatini": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa",
    "Uganda": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa",
}

# Era classification
def get_era(year: int) -> str:
    """Classify year into historical era."""
    if year < 1980:
        return "1965-1979"
    elif year < 1990:
        return "1980-1989"
    elif year < 2000:
        return "1990-1999"
    elif year < 2010:
        return "2000-2009"
    else:
        return "2010-2015"


def get_performance_tier(score: float) -> str:
    """Classify harmonized score into performance tiers."""
    if pd.isna(score):
        return "Unknown"
    if score >= 525:
        return "High (525+)"
    elif score >= 475:
        return "Upper-Middle (475-525)"
    elif score >= 425:
        return "Middle (425-475)"
    elif score >= 375:
        return "Lower-Middle (375-425)"
    else:
        return "Low (<375)"


def load_raw_data() -> pd.DataFrame:
    """Load raw education quality data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading education quality data from: {file_path}")
    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows, {df['Entity'].nunique()} entities")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived fields."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Rename columns (strip trailing spaces from column names)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'Entity': 'entity',
        'Year': 'year',
        'Average harmonised learning outcome score (Altinok, Angrist, and Patrinos (2018))': 'avg_score',
        'Share of students achieving the minimum threshold (Altinok, Angrist, and Patrinos (2018))': 'pct_minimum',
        'Share of students achieving the intermediate threshold (Altinok, Angrist, and Patrinos (2018))': 'pct_intermediate',
        'Share of students achieving the advanced threshold (Altinok, Angrist, and Patrinos (2018))': 'pct_advanced',
    })

    # Extract base country name (remove regional qualifiers for mapping)
    def get_base_country(entity):
        # Handle entities like "Canada (Ontario)" -> "Canada"
        if '(' in entity:
            return entity.split('(')[0].strip()
        return entity

    df['country_base'] = df['entity'].apply(get_base_country)

    # Add region
    df['region'] = df['country_base'].map(REGION_MAPPING).fillna("Other")

    # Add era
    df['era'] = df['year'].apply(get_era)

    # Add performance tier
    df['performance_tier'] = df['avg_score'].apply(get_performance_tier)

    # Calculate gap from maximum (Singapore 2015 = ~560)
    max_score = df['avg_score'].max()
    df['gap_from_best'] = max_score - df['avg_score']

    # Flag if entity is a country (not a sub-national region)
    df['is_country'] = ~df['entity'].str.contains(r'\(', regex=True)

    # Reorder columns
    df = df[['entity', 'country_base', 'year', 'era', 'region', 'avg_score',
             'pct_minimum', 'pct_intermediate', 'pct_advanced',
             'performance_tier', 'gap_from_best', 'is_country']]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions, {df['era'].nunique()} eras")

    return df


def create_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create country-level summary with trend analysis."""
    logger.info("Creating country summary...")

    # Filter to country-level data only
    country_df = df[df['is_country']].copy()

    summaries = []
    for entity in country_df['entity'].unique():
        entity_data = country_df[country_df['entity'] == entity].sort_values('year')

        if len(entity_data) == 0:
            continue

        latest = entity_data.iloc[-1]
        earliest = entity_data.iloc[0]

        score_change = latest['avg_score'] - earliest['avg_score'] if pd.notna(latest['avg_score']) and pd.notna(earliest['avg_score']) else None

        summaries.append({
            'entity': entity,
            'region': latest['region'],
            'earliest_year': earliest['year'],
            'latest_year': latest['year'],
            'earliest_score': earliest['avg_score'],
            'latest_score': latest['avg_score'],
            'score_change': score_change,
            'latest_pct_minimum': latest['pct_minimum'],
            'latest_pct_advanced': latest['pct_advanced'],
            'data_points': len(entity_data),
            'performance_tier': latest['performance_tier'],
        })

    summary_df = pd.DataFrame(summaries)
    summary_df = summary_df.sort_values('latest_score', ascending=False)

    logger.info(f"Created summary for {len(summary_df)} countries")

    return summary_df


def create_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create regional summary statistics."""
    logger.info("Creating region summary...")

    # Filter to country-level data only for latest year per country
    country_df = df[df['is_country']].copy()
    latest_df = country_df.loc[country_df.groupby('entity')['year'].idxmax()]

    region_stats = latest_df.groupby('region').agg({
        'entity': 'count',
        'avg_score': ['mean', 'min', 'max', 'std'],
        'pct_minimum': 'mean',
        'pct_advanced': 'mean',
    }).round(2)

    region_stats.columns = ['countries', 'avg_score', 'min_score', 'max_score', 'std_score', 'avg_pct_minimum', 'avg_pct_advanced']
    region_stats = region_stats.reset_index()
    region_stats = region_stats.sort_values('avg_score', ascending=False)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_era_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create era-based summary statistics."""
    logger.info("Creating era summary...")

    # Filter to country-level data
    country_df = df[df['is_country']].copy()

    era_stats = country_df.groupby('era').agg({
        'entity': 'nunique',
        'avg_score': ['mean', 'min', 'max'],
        'pct_minimum': 'mean',
        'pct_advanced': 'mean',
    }).round(2)

    era_stats.columns = ['countries_tested', 'avg_score', 'min_score', 'max_score', 'avg_pct_minimum', 'avg_pct_advanced']
    era_stats = era_stats.reset_index()

    # Sort by era chronologically
    era_order = ['1965-1979', '1980-1989', '1990-1999', '2000-2009', '2010-2015']
    era_stats['order'] = era_stats['era'].map({e: i for i, e in enumerate(era_order)})
    era_stats = era_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(era_stats)} eras")

    return era_stats


def create_tier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create performance tier summary."""
    logger.info("Creating tier summary...")

    # Filter to latest country-level data
    country_df = df[df['is_country']].copy()
    latest_df = country_df.loc[country_df.groupby('entity')['year'].idxmax()]

    tier_stats = latest_df.groupby('performance_tier').agg({
        'entity': 'count',
        'avg_score': ['mean', 'min', 'max'],
        'pct_minimum': 'mean',
        'pct_advanced': 'mean',
    }).round(2)

    tier_stats.columns = ['countries', 'avg_score', 'min_score', 'max_score', 'avg_pct_minimum', 'avg_pct_advanced']
    tier_stats = tier_stats.reset_index()

    # Sort by tier
    tier_order = ['High (525+)', 'Upper-Middle (475-525)', 'Middle (425-475)', 'Lower-Middle (375-425)', 'Low (<375)', 'Unknown']
    tier_stats['order'] = tier_stats['performance_tier'].map({t: i for i, t in enumerate(tier_order)})
    tier_stats = tier_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(tier_stats)} tiers")

    return tier_stats


def run_education_quality_pipeline(save_files: bool = True) -> dict:
    """Run the complete education quality pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Education Quality Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    country_summary = create_country_summary(enriched_df)
    region_summary = create_region_summary(enriched_df)
    era_summary = create_era_summary(enriched_df)
    tier_summary = create_tier_summary(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "education_quality_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "education_quality_countries.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "education_quality_regions.csv", index=False)
        era_summary.to_csv(PROCESSED_PATH / "education_quality_eras.csv", index=False)
        tier_summary.to_csv(PROCESSED_PATH / "education_quality_tiers.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import EducationQualityDatabase

    with EducationQualityDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, era_summary, tier_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    logger.info("\nKey Insights:")
    logger.info(f"  Total records: {stats['total_records']}")
    logger.info(f"  Countries/entities: {stats['entities']}")
    logger.info(f"  Year range: {stats['years'][0]} - {stats['years'][1]}")
    logger.info(f"  Global average score: {stats['global_avg']}")
    logger.info(f"  Best: {stats['best_entity']} ({stats['best_score']})")

    return stats


if __name__ == "__main__":
    stats = run_education_quality_pipeline()
    print(json.dumps(stats, indent=2, default=str))
