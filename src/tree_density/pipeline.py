"""
Tree Density ETL Pipeline

Processes global tree density data from Crowther et al. (2015).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "tree_density.csv"

# Region mapping for countries
REGION_MAPPING = {
    # East Asia & Pacific
    "Australia": "East Asia & Pacific", "Brunei": "East Asia & Pacific",
    "Cambodia": "East Asia & Pacific", "China": "East Asia & Pacific",
    "Fiji": "East Asia & Pacific", "Hong Kong": "East Asia & Pacific",
    "Indonesia": "East Asia & Pacific", "Japan": "East Asia & Pacific",
    "Kiribati": "East Asia & Pacific", "Laos": "East Asia & Pacific",
    "Macao": "East Asia & Pacific", "Malaysia": "East Asia & Pacific",
    "Marshall Islands": "East Asia & Pacific", "Micronesia (country)": "East Asia & Pacific",
    "Mongolia": "East Asia & Pacific", "Myanmar": "East Asia & Pacific",
    "Nauru": "East Asia & Pacific", "New Caledonia": "East Asia & Pacific",
    "New Zealand": "East Asia & Pacific", "North Korea": "East Asia & Pacific",
    "Palau": "East Asia & Pacific", "Papua New Guinea": "East Asia & Pacific",
    "Philippines": "East Asia & Pacific", "Samoa": "East Asia & Pacific",
    "Singapore": "East Asia & Pacific", "Solomon Islands": "East Asia & Pacific",
    "South Korea": "East Asia & Pacific", "Taiwan": "East Asia & Pacific",
    "Thailand": "East Asia & Pacific", "Timor": "East Asia & Pacific",
    "Tonga": "East Asia & Pacific", "Tuvalu": "East Asia & Pacific",
    "Vanuatu": "East Asia & Pacific", "Vietnam": "East Asia & Pacific",

    # Europe & Central Asia
    "Albania": "Europe & Central Asia", "Andorra": "Europe & Central Asia",
    "Armenia": "Europe & Central Asia", "Austria": "Europe & Central Asia",
    "Azerbaijan": "Europe & Central Asia", "Belarus": "Europe & Central Asia",
    "Belgium": "Europe & Central Asia", "Bosnia and Herzegovina": "Europe & Central Asia",
    "Bulgaria": "Europe & Central Asia", "Croatia": "Europe & Central Asia",
    "Cyprus": "Europe & Central Asia", "Czech Republic": "Europe & Central Asia",
    "Denmark": "Europe & Central Asia", "Estonia": "Europe & Central Asia",
    "Faeroe Islands": "Europe & Central Asia", "Finland": "Europe & Central Asia",
    "France": "Europe & Central Asia", "Georgia": "Europe & Central Asia",
    "Germany": "Europe & Central Asia", "Gibraltar": "Europe & Central Asia",
    "Greece": "Europe & Central Asia", "Greenland": "Europe & Central Asia",
    "Guernsey": "Europe & Central Asia", "Hungary": "Europe & Central Asia",
    "Iceland": "Europe & Central Asia", "Ireland": "Europe & Central Asia",
    "Isle of Man": "Europe & Central Asia", "Italy": "Europe & Central Asia",
    "Jersey": "Europe & Central Asia", "Kazakhstan": "Europe & Central Asia",
    "Kosovo": "Europe & Central Asia", "Kyrgyzstan": "Europe & Central Asia",
    "Latvia": "Europe & Central Asia", "Liechtenstein": "Europe & Central Asia",
    "Lithuania": "Europe & Central Asia", "Luxembourg": "Europe & Central Asia",
    "Macedonia": "Europe & Central Asia", "Malta": "Europe & Central Asia",
    "Moldova": "Europe & Central Asia", "Monaco": "Europe & Central Asia",
    "Montenegro": "Europe & Central Asia", "Netherlands": "Europe & Central Asia",
    "Northern Cyprus": "Europe & Central Asia", "Norway": "Europe & Central Asia",
    "Poland": "Europe & Central Asia", "Portugal": "Europe & Central Asia",
    "Romania": "Europe & Central Asia", "Russia": "Europe & Central Asia",
    "San Marino": "Europe & Central Asia", "Serbia": "Europe & Central Asia",
    "Slovakia": "Europe & Central Asia", "Slovenia": "Europe & Central Asia",
    "Spain": "Europe & Central Asia", "Sweden": "Europe & Central Asia",
    "Switzerland": "Europe & Central Asia", "Tajikistan": "Europe & Central Asia",
    "Turkey": "Europe & Central Asia", "Turkmenistan": "Europe & Central Asia",
    "Ukraine": "Europe & Central Asia", "United Kingdom": "Europe & Central Asia",
    "Uzbekistan": "Europe & Central Asia",

    # Latin America & Caribbean
    "Argentina": "Latin America & Caribbean", "Aruba": "Latin America & Caribbean",
    "Bahamas": "Latin America & Caribbean", "Barbados": "Latin America & Caribbean",
    "Belize": "Latin America & Caribbean", "Bolivia": "Latin America & Caribbean",
    "Bonaire Sint Eustatius and Saba": "Latin America & Caribbean",
    "Brazil": "Latin America & Caribbean", "British Virgin Islands": "Latin America & Caribbean",
    "Cayman Islands": "Latin America & Caribbean", "Chile": "Latin America & Caribbean",
    "Colombia": "Latin America & Caribbean", "Costa Rica": "Latin America & Caribbean",
    "Cuba": "Latin America & Caribbean", "Curacao": "Latin America & Caribbean",
    "Dominica": "Latin America & Caribbean", "Dominican Republic": "Latin America & Caribbean",
    "Ecuador": "Latin America & Caribbean", "El Salvador": "Latin America & Caribbean",
    "Falkland Islands": "Latin America & Caribbean", "French Guiana": "Latin America & Caribbean",
    "Grenada": "Latin America & Caribbean", "Guadeloupe": "Latin America & Caribbean",
    "Guatemala": "Latin America & Caribbean", "Guyana": "Latin America & Caribbean",
    "Haiti": "Latin America & Caribbean", "Honduras": "Latin America & Caribbean",
    "Jamaica": "Latin America & Caribbean", "Martinique": "Latin America & Caribbean",
    "Mexico": "Latin America & Caribbean", "Montserrat": "Latin America & Caribbean",
    "Nicaragua": "Latin America & Caribbean", "Panama": "Latin America & Caribbean",
    "Paraguay": "Latin America & Caribbean", "Peru": "Latin America & Caribbean",
    "Puerto Rico": "Latin America & Caribbean", "Saint Barthlemy": "Latin America & Caribbean",
    "Saint Kitts and Nevis": "Latin America & Caribbean", "Saint Lucia": "Latin America & Caribbean",
    "Saint Pierre and Miquelon": "Latin America & Caribbean",
    "Saint Vincent and the Grenadines": "Latin America & Caribbean",
    "Sint Maarten (Dutch part)": "Latin America & Caribbean",
    "Suriname": "Latin America & Caribbean", "Trinidad and Tobago": "Latin America & Caribbean",
    "Turks and Caicos Islands": "Latin America & Caribbean",
    "United States Virgin Islands": "Latin America & Caribbean",
    "Uruguay": "Latin America & Caribbean", "Venezuela": "Latin America & Caribbean",

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
    "Western Sahara": "Middle East & North Africa", "Yemen": "Middle East & North Africa",

    # North America
    "American Samoa": "North America", "Canada": "North America",
    "Guam": "North America", "Northern Mariana Islands": "North America",
    "United States": "North America",

    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia",
    "Bhutan": "South Asia", "India": "South Asia",
    "Maldives": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",

    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa",
    "Botswana": "Sub-Saharan Africa", "Burkina Faso": "Sub-Saharan Africa",
    "Burundi": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa",
    "Cape Verde": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Comoros": "Sub-Saharan Africa",
    "Congo": "Sub-Saharan Africa", "Cote d'Ivoire": "Sub-Saharan Africa",
    "Democratic Republic of Congo": "Sub-Saharan Africa", "Djibouti": "Sub-Saharan Africa",
    "Equatorial Guinea": "Sub-Saharan Africa", "Eritrea": "Sub-Saharan Africa",
    "Ethiopia": "Sub-Saharan Africa", "Gabon": "Sub-Saharan Africa",
    "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa",
    "Guinea": "Sub-Saharan Africa", "Guinea-Bissau": "Sub-Saharan Africa",
    "Kenya": "Sub-Saharan Africa", "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa", "Mali": "Sub-Saharan Africa",
    "Mauritania": "Sub-Saharan Africa", "Mauritius": "Sub-Saharan Africa",
    "Mayotte": "Sub-Saharan Africa", "Mozambique": "Sub-Saharan Africa",
    "Namibia": "Sub-Saharan Africa", "Niger": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Reunion": "Sub-Saharan Africa",
    "Rwanda": "Sub-Saharan Africa", "Saint Helena": "Sub-Saharan Africa",
    "Sao Tome and Principe": "Sub-Saharan Africa", "Senegal": "Sub-Saharan Africa",
    "Seychelles": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "Somalia": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa",
    "South Sudan": "Sub-Saharan Africa", "Sudan": "Sub-Saharan Africa",
    "Swaziland": "Sub-Saharan Africa", "Tanzania": "Sub-Saharan Africa",
    "Togo": "Sub-Saharan Africa", "Uganda": "Sub-Saharan Africa",
    "Zambia": "Sub-Saharan Africa", "Zimbabwe": "Sub-Saharan Africa",
}


def get_density_tier(trees_per_km2: float) -> str:
    """Classify tree density into tiers."""
    if pd.isna(trees_per_km2):
        return "Unknown"
    if trees_per_km2 >= 50000:
        return "Very High (50k+/km²)"
    elif trees_per_km2 >= 30000:
        return "High (30-50k/km²)"
    elif trees_per_km2 >= 15000:
        return "Moderate (15-30k/km²)"
    elif trees_per_km2 >= 5000:
        return "Low (5-15k/km²)"
    else:
        return "Very Low (<5k/km²)"


def get_per_capita_tier(trees_per_capita: float) -> str:
    """Classify trees per capita into tiers."""
    if pd.isna(trees_per_capita):
        return "Unknown"
    if trees_per_capita >= 1000:
        return "Very High (1000+)"
    elif trees_per_capita >= 200:
        return "High (200-1000)"
    elif trees_per_capita >= 50:
        return "Moderate (50-200)"
    elif trees_per_capita >= 10:
        return "Low (10-50)"
    else:
        return "Very Low (<10)"


def load_raw_data() -> pd.DataFrame:
    """Load raw tree density data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading tree density data from: {file_path}")
    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows, {df['Entity'].nunique()} entities")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived fields."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Rename columns
    df = df.rename(columns={
        'Entity': 'entity',
        'Year': 'year',
        'Number of trees': 'num_trees',
        'Tree density (trees per km2)': 'trees_per_km2',
        'Tree density (trees per capita)': 'trees_per_capita',
    })

    # Filter out aggregate rows (World, etc.)
    aggregates = ['World', 'World (mean)', 'World (median)']
    world_data = df[df['entity'].isin(aggregates)].copy()
    df = df[~df['entity'].isin(aggregates)].copy()

    # Add region
    df['region'] = df['entity'].map(REGION_MAPPING).fillna("Other")

    # Add density tier
    df['density_tier'] = df['trees_per_km2'].apply(get_density_tier)

    # Add per capita tier
    df['per_capita_tier'] = df['trees_per_capita'].apply(get_per_capita_tier)

    # Calculate percentage of world total (3.04 trillion trees)
    world_trees = 3.04e12
    df['pct_world_trees'] = (df['num_trees'] / world_trees * 100).round(4)

    # Convert large numbers to billions for readability
    df['trees_billions'] = (df['num_trees'] / 1e9).round(2)

    # Reorder columns
    df = df[['entity', 'year', 'region', 'num_trees', 'trees_billions', 'pct_world_trees',
             'trees_per_km2', 'trees_per_capita', 'density_tier', 'per_capita_tier']]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions, {len(df)} countries")

    return df


def create_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create regional summary statistics."""
    logger.info("Creating region summary...")

    region_stats = df.groupby('region').agg({
        'entity': 'count',
        'num_trees': 'sum',
        'trees_per_km2': ['mean', 'min', 'max'],
        'trees_per_capita': ['mean', 'min', 'max'],
    }).round(2)

    region_stats.columns = ['countries', 'total_trees', 'avg_density', 'min_density',
                            'max_density', 'avg_per_capita', 'min_per_capita', 'max_per_capita']
    region_stats = region_stats.reset_index()

    # Add trees in billions
    region_stats['trees_billions'] = (region_stats['total_trees'] / 1e9).round(1)

    region_stats = region_stats.sort_values('total_trees', ascending=False)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_density_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create density tier summary."""
    logger.info("Creating density tier summary...")

    tier_stats = df.groupby('density_tier').agg({
        'entity': 'count',
        'trees_per_km2': ['mean', 'min', 'max'],
        'trees_per_capita': 'mean',
    }).round(2)

    tier_stats.columns = ['countries', 'avg_density', 'min_density', 'max_density', 'avg_per_capita']
    tier_stats = tier_stats.reset_index()

    # Sort by tier
    tier_order = ['Very High (50k+/km²)', 'High (30-50k/km²)', 'Moderate (15-30k/km²)',
                  'Low (5-15k/km²)', 'Very Low (<5k/km²)', 'Unknown']
    tier_stats['order'] = tier_stats['density_tier'].map({t: i for i, t in enumerate(tier_order)})
    tier_stats = tier_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(tier_stats)} density tiers")

    return tier_stats


def create_per_capita_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create per capita tier summary."""
    logger.info("Creating per capita tier summary...")

    tier_stats = df.groupby('per_capita_tier').agg({
        'entity': 'count',
        'trees_per_capita': ['mean', 'min', 'max'],
        'trees_per_km2': 'mean',
    }).round(2)

    tier_stats.columns = ['countries', 'avg_per_capita', 'min_per_capita', 'max_per_capita', 'avg_density']
    tier_stats = tier_stats.reset_index()

    # Sort by tier
    tier_order = ['Very High (1000+)', 'High (200-1000)', 'Moderate (50-200)',
                  'Low (10-50)', 'Very Low (<10)', 'Unknown']
    tier_stats['order'] = tier_stats['per_capita_tier'].map({t: i for i, t in enumerate(tier_order)})
    tier_stats = tier_stats.sort_values('order').drop('order', axis=1)

    logger.info(f"Created summary for {len(tier_stats)} per capita tiers")

    return tier_stats


def run_tree_density_pipeline(save_files: bool = True) -> dict:
    """Run the complete tree density pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Tree Density Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    region_summary = create_region_summary(enriched_df)
    density_summary = create_density_summary(enriched_df)
    per_capita_summary = create_per_capita_summary(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "tree_density_enriched.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "tree_density_regions.csv", index=False)
        density_summary.to_csv(PROCESSED_PATH / "tree_density_tiers.csv", index=False)
        per_capita_summary.to_csv(PROCESSED_PATH / "tree_density_per_capita.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import TreeDensityDatabase

    with TreeDensityDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, region_summary, density_summary, per_capita_summary)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Total trees: {stats['total_trees_trillion']:.2f} trillion")
    logger.info(f"  Most trees: {stats['most_trees_country']} ({stats['most_trees_billions']:.0f}B)")
    logger.info(f"  Highest density: {stats['highest_density_country']} ({stats['highest_density']:.0f}/km²)")
    logger.info(f"  Most per capita: {stats['most_per_capita_country']} ({stats['most_per_capita']:.0f})")

    return stats


if __name__ == "__main__":
    stats = run_tree_density_pipeline()
    print(json.dumps(stats, indent=2, default=str))
