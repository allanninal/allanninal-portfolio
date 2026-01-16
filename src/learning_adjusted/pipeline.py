"""
Learning-Adjusted Years of Schooling ETL Pipeline

Processes World Bank Human Capital Index education data (2018).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "learning_adjusted.csv"

# Region mapping for countries
REGION_MAPPING = {
    # East Asia & Pacific
    "Australia": "East Asia & Pacific", "Cambodia": "East Asia & Pacific",
    "China": "East Asia & Pacific", "Hong Kong": "East Asia & Pacific",
    "Indonesia": "East Asia & Pacific", "Japan": "East Asia & Pacific",
    "Kiribati": "East Asia & Pacific", "Laos": "East Asia & Pacific",
    "Macao": "East Asia & Pacific", "Malaysia": "East Asia & Pacific",
    "Mongolia": "East Asia & Pacific", "Myanmar": "East Asia & Pacific",
    "New Zealand": "East Asia & Pacific", "Papua New Guinea": "East Asia & Pacific",
    "Philippines": "East Asia & Pacific", "Singapore": "East Asia & Pacific",
    "Solomon Islands": "East Asia & Pacific", "South Korea": "East Asia & Pacific",
    "Thailand": "East Asia & Pacific", "Timor": "East Asia & Pacific",
    "Tonga": "East Asia & Pacific", "Tuvalu": "East Asia & Pacific",
    "Vanuatu": "East Asia & Pacific", "Vietnam": "East Asia & Pacific",

    # Europe & Central Asia
    "Albania": "Europe & Central Asia", "Armenia": "Europe & Central Asia",
    "Austria": "Europe & Central Asia", "Azerbaijan": "Europe & Central Asia",
    "Belgium": "Europe & Central Asia", "Bosnia and Herzegovina": "Europe & Central Asia",
    "Bulgaria": "Europe & Central Asia", "Croatia": "Europe & Central Asia",
    "Cyprus": "Europe & Central Asia", "Czech Republic": "Europe & Central Asia",
    "Denmark": "Europe & Central Asia", "Estonia": "Europe & Central Asia",
    "Finland": "Europe & Central Asia", "France": "Europe & Central Asia",
    "Georgia": "Europe & Central Asia", "Germany": "Europe & Central Asia",
    "Greece": "Europe & Central Asia", "Hungary": "Europe & Central Asia",
    "Iceland": "Europe & Central Asia", "Ireland": "Europe & Central Asia",
    "Italy": "Europe & Central Asia", "Kazakhstan": "Europe & Central Asia",
    "Kosovo": "Europe & Central Asia", "Kyrgyzstan": "Europe & Central Asia",
    "Latvia": "Europe & Central Asia", "Lithuania": "Europe & Central Asia",
    "Luxembourg": "Europe & Central Asia", "Macedonia": "Europe & Central Asia",
    "Malta": "Europe & Central Asia", "Moldova": "Europe & Central Asia",
    "Montenegro": "Europe & Central Asia", "Netherlands": "Europe & Central Asia",
    "Norway": "Europe & Central Asia", "Poland": "Europe & Central Asia",
    "Portugal": "Europe & Central Asia", "Romania": "Europe & Central Asia",
    "Russia": "Europe & Central Asia", "Serbia": "Europe & Central Asia",
    "Slovakia": "Europe & Central Asia", "Slovenia": "Europe & Central Asia",
    "Spain": "Europe & Central Asia", "Sweden": "Europe & Central Asia",
    "Switzerland": "Europe & Central Asia", "Tajikistan": "Europe & Central Asia",
    "Turkey": "Europe & Central Asia", "Ukraine": "Europe & Central Asia",
    "United Kingdom": "Europe & Central Asia",

    # Latin America & Caribbean
    "Argentina": "Latin America & Caribbean", "Brazil": "Latin America & Caribbean",
    "Chile": "Latin America & Caribbean", "Colombia": "Latin America & Caribbean",
    "Costa Rica": "Latin America & Caribbean", "Dominican Republic": "Latin America & Caribbean",
    "Ecuador": "Latin America & Caribbean", "El Salvador": "Latin America & Caribbean",
    "Guatemala": "Latin America & Caribbean", "Guyana": "Latin America & Caribbean",
    "Haiti": "Latin America & Caribbean", "Honduras": "Latin America & Caribbean",
    "Jamaica": "Latin America & Caribbean", "Mexico": "Latin America & Caribbean",
    "Nicaragua": "Latin America & Caribbean", "Panama": "Latin America & Caribbean",
    "Paraguay": "Latin America & Caribbean", "Peru": "Latin America & Caribbean",
    "Trinidad and Tobago": "Latin America & Caribbean", "Uruguay": "Latin America & Caribbean",

    # Middle East & North Africa
    "Algeria": "Middle East & North Africa", "Bahrain": "Middle East & North Africa",
    "Egypt": "Middle East & North Africa", "Iran": "Middle East & North Africa",
    "Iraq": "Middle East & North Africa", "Israel": "Middle East & North Africa",
    "Jordan": "Middle East & North Africa", "Kuwait": "Middle East & North Africa",
    "Lebanon": "Middle East & North Africa", "Morocco": "Middle East & North Africa",
    "Oman": "Middle East & North Africa", "Palestine": "Middle East & North Africa",
    "Qatar": "Middle East & North Africa", "Saudi Arabia": "Middle East & North Africa",
    "Tunisia": "Middle East & North Africa", "United Arab Emirates": "Middle East & North Africa",
    "Yemen": "Middle East & North Africa",

    # North America
    "Canada": "North America", "United States": "North America",

    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia",
    "India": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",

    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa",
    "Botswana": "Sub-Saharan Africa", "Burkina Faso": "Sub-Saharan Africa",
    "Burundi": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Comoros": "Sub-Saharan Africa",
    "Congo": "Sub-Saharan Africa", "Cote d'Ivoire": "Sub-Saharan Africa",
    "Democratic Republic of Congo": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Gabon": "Sub-Saharan Africa", "Gambia": "Sub-Saharan Africa",
    "Ghana": "Sub-Saharan Africa", "Guinea": "Sub-Saharan Africa",
    "Kenya": "Sub-Saharan Africa", "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa", "Mali": "Sub-Saharan Africa",
    "Mauritania": "Sub-Saharan Africa", "Mauritius": "Sub-Saharan Africa",
    "Mozambique": "Sub-Saharan Africa", "Namibia": "Sub-Saharan Africa",
    "Niger": "Sub-Saharan Africa", "Nigeria": "Sub-Saharan Africa",
    "Rwanda": "Sub-Saharan Africa", "Senegal": "Sub-Saharan Africa",
    "Seychelles": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "South Africa": "Sub-Saharan Africa", "South Sudan": "Sub-Saharan Africa",
    "Sudan": "Sub-Saharan Africa", "Swaziland": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa",
    "Uganda": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa",
}

# Income group mapping (approximate based on World Bank classifications)
INCOME_MAPPING = {
    # High income
    "Australia": "High income", "Austria": "High income", "Bahrain": "High income",
    "Belgium": "High income", "Canada": "High income", "Chile": "High income",
    "Croatia": "High income", "Cyprus": "High income", "Czech Republic": "High income",
    "Denmark": "High income", "Estonia": "High income", "Finland": "High income",
    "France": "High income", "Germany": "High income", "Greece": "High income",
    "Hong Kong": "High income", "Hungary": "High income", "Iceland": "High income",
    "Ireland": "High income", "Israel": "High income", "Italy": "High income",
    "Japan": "High income", "Kuwait": "High income", "Latvia": "High income",
    "Lithuania": "High income", "Luxembourg": "High income", "Macao": "High income",
    "Malta": "High income", "Netherlands": "High income", "New Zealand": "High income",
    "Norway": "High income", "Oman": "High income", "Poland": "High income",
    "Portugal": "High income", "Qatar": "High income", "Saudi Arabia": "High income",
    "Seychelles": "High income", "Singapore": "High income", "Slovakia": "High income",
    "Slovenia": "High income", "South Korea": "High income", "Spain": "High income",
    "Sweden": "High income", "Switzerland": "High income", "Trinidad and Tobago": "High income",
    "United Arab Emirates": "High income", "United Kingdom": "High income",
    "United States": "High income", "Uruguay": "High income",

    # Upper middle income
    "Albania": "Upper middle income", "Argentina": "Upper middle income",
    "Armenia": "Upper middle income", "Azerbaijan": "Upper middle income",
    "Bosnia and Herzegovina": "Upper middle income", "Botswana": "Upper middle income",
    "Brazil": "Upper middle income", "Bulgaria": "Upper middle income",
    "China": "Upper middle income", "Colombia": "Upper middle income",
    "Costa Rica": "Upper middle income", "Dominican Republic": "Upper middle income",
    "Ecuador": "Upper middle income", "Gabon": "Upper middle income",
    "Georgia": "Upper middle income", "Guatemala": "Upper middle income",
    "Guyana": "Upper middle income", "Iran": "Upper middle income",
    "Iraq": "Upper middle income", "Jamaica": "Upper middle income",
    "Jordan": "Upper middle income", "Kazakhstan": "Upper middle income",
    "Kosovo": "Upper middle income", "Lebanon": "Upper middle income",
    "Macedonia": "Upper middle income", "Malaysia": "Upper middle income",
    "Mauritius": "Upper middle income", "Mexico": "Upper middle income",
    "Montenegro": "Upper middle income", "Namibia": "Upper middle income",
    "Paraguay": "Upper middle income", "Peru": "Upper middle income",
    "Romania": "Upper middle income", "Russia": "Upper middle income",
    "Serbia": "Upper middle income", "South Africa": "Upper middle income",
    "Sri Lanka": "Upper middle income", "Thailand": "Upper middle income",
    "Turkey": "Upper middle income",

    # Lower middle income
    "Algeria": "Lower middle income", "Angola": "Lower middle income",
    "Bangladesh": "Lower middle income", "Benin": "Lower middle income",
    "Bolivia": "Lower middle income", "Cambodia": "Lower middle income",
    "Cameroon": "Lower middle income", "Comoros": "Lower middle income",
    "Congo": "Lower middle income", "Cote d'Ivoire": "Lower middle income",
    "Egypt": "Lower middle income", "El Salvador": "Lower middle income",
    "Ghana": "Lower middle income", "Haiti": "Lower middle income",
    "Honduras": "Lower middle income", "India": "Lower middle income",
    "Indonesia": "Lower middle income", "Kenya": "Lower middle income",
    "Kiribati": "Lower middle income", "Kyrgyzstan": "Lower middle income",
    "Laos": "Lower middle income", "Lesotho": "Lower middle income",
    "Mauritania": "Lower middle income", "Moldova": "Lower middle income",
    "Mongolia": "Lower middle income", "Morocco": "Lower middle income",
    "Myanmar": "Lower middle income", "Nepal": "Lower middle income",
    "Nicaragua": "Lower middle income", "Nigeria": "Lower middle income",
    "Pakistan": "Lower middle income", "Palestine": "Lower middle income",
    "Papua New Guinea": "Lower middle income", "Philippines": "Lower middle income",
    "Senegal": "Lower middle income", "Solomon Islands": "Lower middle income",
    "Swaziland": "Lower middle income", "Tajikistan": "Lower middle income",
    "Tanzania": "Lower middle income", "Timor": "Lower middle income",
    "Tonga": "Lower middle income", "Tunisia": "Lower middle income",
    "Tuvalu": "Lower middle income", "Ukraine": "Lower middle income",
    "Vanuatu": "Lower middle income", "Vietnam": "Lower middle income",
    "Zambia": "Lower middle income", "Zimbabwe": "Lower middle income",

    # Low income
    "Afghanistan": "Low income", "Burkina Faso": "Low income",
    "Burundi": "Low income", "Chad": "Low income",
    "Democratic Republic of Congo": "Low income", "Ethiopia": "Low income",
    "Gambia": "Low income", "Guinea": "Low income",
    "Liberia": "Low income", "Madagascar": "Low income",
    "Malawi": "Low income", "Mali": "Low income",
    "Mozambique": "Low income", "Niger": "Low income",
    "Rwanda": "Low income", "Sierra Leone": "Low income",
    "South Sudan": "Low income", "Sudan": "Low income",
    "Togo": "Low income", "Uganda": "Low income",
    "Yemen": "Low income",
}


def get_education_tier(years: float) -> str:
    """Classify learning-adjusted years into tiers."""
    if pd.isna(years):
        return "Unknown"
    if years >= 11:
        return "Excellent (11+ years)"
    elif years >= 9:
        return "Good (9-11 years)"
    elif years >= 7:
        return "Moderate (7-9 years)"
    elif years >= 5:
        return "Low (5-7 years)"
    else:
        return "Very Low (<5 years)"


def load_raw_data() -> pd.DataFrame:
    """Load raw learning-adjusted years data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading learning-adjusted years data from: {file_path}")
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
        'Learning-Adjusted Years of School': 'lays'
    })

    # Add region
    df['region'] = df['country'].map(REGION_MAPPING).fillna("Other")

    # Add income group
    df['income_group'] = df['country'].map(INCOME_MAPPING).fillna("Other")

    # Add education tier
    df['education_tier'] = df['lays'].apply(get_education_tier)

    # Calculate gap from maximum (Singapore = 12.9)
    max_lays = df['lays'].max()
    df['gap_from_best'] = max_lays - df['lays']

    # Reorder columns
    df = df[['country', 'year', 'region', 'income_group', 'lays', 'education_tier', 'gap_from_best']]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions, {df['income_group'].nunique()} income groups")

    return df


def create_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create regional summary statistics."""
    logger.info("Creating region summary...")

    region_stats = df.groupby('region').agg({
        'country': 'count',
        'lays': ['mean', 'min', 'max', 'std'],
    }).round(2)

    region_stats.columns = ['countries', 'avg_lays', 'min_lays', 'max_lays', 'std_lays']
    region_stats = region_stats.reset_index()
    region_stats = region_stats.sort_values('avg_lays', ascending=False)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_income_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create income group summary statistics."""
    logger.info("Creating income group summary...")

    income_stats = df.groupby('income_group').agg({
        'country': 'count',
        'lays': ['mean', 'min', 'max', 'std'],
    }).round(2)

    income_stats.columns = ['countries', 'avg_lays', 'min_lays', 'max_lays', 'std_lays']
    income_stats = income_stats.reset_index()

    # Sort by income level
    income_order = ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Other']
    income_stats['order'] = income_stats['income_group'].map({g: i for i, g in enumerate(income_order)})
    income_stats = income_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(income_stats)} income groups")

    return income_stats


def create_tier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create education tier summary."""
    logger.info("Creating tier summary...")

    tier_stats = df.groupby('education_tier').agg({
        'country': 'count',
        'lays': ['mean', 'min', 'max'],
    }).round(2)

    tier_stats.columns = ['countries', 'avg_lays', 'min_lays', 'max_lays']
    tier_stats = tier_stats.reset_index()

    # Sort by tier
    tier_order = ['Excellent (11+ years)', 'Good (9-11 years)', 'Moderate (7-9 years)', 'Low (5-7 years)', 'Very Low (<5 years)', 'Unknown']
    tier_stats['order'] = tier_stats['education_tier'].map({t: i for i, t in enumerate(tier_order)})
    tier_stats = tier_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(tier_stats)} tiers")

    return tier_stats


def run_learning_adjusted_pipeline(save_files: bool = True) -> dict:
    """Run the complete learning-adjusted years pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Learning-Adjusted Years Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    region_summary = create_region_summary(enriched_df)
    income_summary = create_income_summary(enriched_df)
    tier_summary = create_tier_summary(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "learning_adjusted_enriched.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "learning_adjusted_regions.csv", index=False)
        income_summary.to_csv(PROCESSED_PATH / "learning_adjusted_income.csv", index=False)
        tier_summary.to_csv(PROCESSED_PATH / "learning_adjusted_tiers.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import LearningAdjustedDatabase

    with LearningAdjustedDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, region_summary, income_summary, tier_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Global average LAYS: {stats['global_avg']} years")
    logger.info(f"  Best: {stats['best_country']} ({stats['best_lays']} years)")
    logger.info(f"  Lowest: {stats['lowest_country']} ({stats['lowest_lays']} years)")

    return stats


if __name__ == "__main__":
    stats = run_learning_adjusted_pipeline()
    print(json.dumps(stats, indent=2, default=str))
