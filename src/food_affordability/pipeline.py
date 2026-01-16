"""
Food Affordability ETL Pipeline

Processes World Bank/FAO food affordability data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_PATH = Path(__file__).parent.parent.parent / "data" / "processed"
DATA_FILE = "food_affordability.csv"

# Region mapping based on World Bank classifications
REGION_MAPPING = {
    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa", "Cabo Verde": "Sub-Saharan Africa",
    "Cameroon": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Comoros": "Sub-Saharan Africa", "Congo": "Sub-Saharan Africa",
    "Cote d'Ivoire": "Sub-Saharan Africa", "Democratic Republic of Congo": "Sub-Saharan Africa",
    "Djibouti": "Sub-Saharan Africa", "Equatorial Guinea": "Sub-Saharan Africa", "Eritrea": "Sub-Saharan Africa",
    "Eswatini": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa", "Gabon": "Sub-Saharan Africa",
    "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa", "Guinea": "Sub-Saharan Africa",
    "Guinea-Bissau": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa", "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa", "Malawi": "Sub-Saharan Africa",
    "Mali": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa", "Mauritius": "Sub-Saharan Africa",
    "Mozambique": "Sub-Saharan Africa", "Namibia": "Sub-Saharan Africa", "Niger": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa", "Sao Tome and Principe": "Sub-Saharan Africa",
    "Senegal": "Sub-Saharan Africa", "Seychelles": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "South Africa": "Sub-Saharan Africa", "South Sudan": "Sub-Saharan Africa", "Sudan": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa", "Uganda": "Sub-Saharan Africa",
    "Zambia": "Sub-Saharan Africa", "Zimbabwe": "Sub-Saharan Africa",

    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia", "Bhutan": "South Asia",
    "India": "South Asia", "Maldives": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",

    # East Asia & Pacific
    "Australia": "East Asia & Pacific", "Brunei": "East Asia & Pacific", "Cambodia": "East Asia & Pacific",
    "China": "East Asia & Pacific", "Fiji": "East Asia & Pacific", "Hong Kong": "East Asia & Pacific",
    "Indonesia": "East Asia & Pacific", "Japan": "East Asia & Pacific", "Kiribati": "East Asia & Pacific",
    "Laos": "East Asia & Pacific", "Macau": "East Asia & Pacific", "Malaysia": "East Asia & Pacific",
    "Mongolia": "East Asia & Pacific", "Myanmar": "East Asia & Pacific", "New Zealand": "East Asia & Pacific",
    "Papua New Guinea": "East Asia & Pacific", "Philippines": "East Asia & Pacific",
    "Singapore": "East Asia & Pacific", "Solomon Islands": "East Asia & Pacific",
    "South Korea": "East Asia & Pacific", "Taiwan": "East Asia & Pacific", "Thailand": "East Asia & Pacific",
    "Timor": "East Asia & Pacific", "Tonga": "East Asia & Pacific", "Vanuatu": "East Asia & Pacific",
    "Vietnam": "East Asia & Pacific",

    # Europe & Central Asia
    "Albania": "Europe & Central Asia", "Armenia": "Europe & Central Asia", "Austria": "Europe & Central Asia",
    "Azerbaijan": "Europe & Central Asia", "Belarus": "Europe & Central Asia", "Belgium": "Europe & Central Asia",
    "Bosnia and Herzegovina": "Europe & Central Asia", "Bulgaria": "Europe & Central Asia",
    "Croatia": "Europe & Central Asia", "Cyprus": "Europe & Central Asia", "Czechia": "Europe & Central Asia",
    "Denmark": "Europe & Central Asia", "Estonia": "Europe & Central Asia", "Finland": "Europe & Central Asia",
    "France": "Europe & Central Asia", "Georgia": "Europe & Central Asia", "Germany": "Europe & Central Asia",
    "Greece": "Europe & Central Asia", "Hungary": "Europe & Central Asia", "Iceland": "Europe & Central Asia",
    "Ireland": "Europe & Central Asia", "Italy": "Europe & Central Asia", "Kazakhstan": "Europe & Central Asia",
    "Kosovo": "Europe & Central Asia", "Kyrgyzstan": "Europe & Central Asia", "Latvia": "Europe & Central Asia",
    "Lithuania": "Europe & Central Asia", "Luxembourg": "Europe & Central Asia",
    "Moldova": "Europe & Central Asia", "Montenegro": "Europe & Central Asia",
    "Netherlands": "Europe & Central Asia", "North Macedonia": "Europe & Central Asia",
    "Norway": "Europe & Central Asia", "Poland": "Europe & Central Asia", "Portugal": "Europe & Central Asia",
    "Romania": "Europe & Central Asia", "Russia": "Europe & Central Asia", "Serbia": "Europe & Central Asia",
    "Slovakia": "Europe & Central Asia", "Slovenia": "Europe & Central Asia", "Spain": "Europe & Central Asia",
    "Sweden": "Europe & Central Asia", "Switzerland": "Europe & Central Asia",
    "Tajikistan": "Europe & Central Asia", "Turkey": "Europe & Central Asia",
    "Turkmenistan": "Europe & Central Asia", "Ukraine": "Europe & Central Asia",
    "United Kingdom": "Europe & Central Asia", "Uzbekistan": "Europe & Central Asia",

    # Latin America & Caribbean
    "Antigua and Barbuda": "Latin America & Caribbean", "Argentina": "Latin America & Caribbean",
    "Aruba": "Latin America & Caribbean", "Bahamas": "Latin America & Caribbean",
    "Barbados": "Latin America & Caribbean", "Belize": "Latin America & Caribbean",
    "Bolivia": "Latin America & Caribbean", "Brazil": "Latin America & Caribbean",
    "Chile": "Latin America & Caribbean", "Colombia": "Latin America & Caribbean",
    "Costa Rica": "Latin America & Caribbean", "Cuba": "Latin America & Caribbean",
    "Curacao": "Latin America & Caribbean", "Dominica": "Latin America & Caribbean",
    "Dominican Republic": "Latin America & Caribbean", "Ecuador": "Latin America & Caribbean",
    "El Salvador": "Latin America & Caribbean", "Grenada": "Latin America & Caribbean",
    "Guatemala": "Latin America & Caribbean", "Guyana": "Latin America & Caribbean",
    "Haiti": "Latin America & Caribbean", "Honduras": "Latin America & Caribbean",
    "Jamaica": "Latin America & Caribbean", "Mexico": "Latin America & Caribbean",
    "Nicaragua": "Latin America & Caribbean", "Panama": "Latin America & Caribbean",
    "Paraguay": "Latin America & Caribbean", "Peru": "Latin America & Caribbean",
    "Puerto Rico": "Latin America & Caribbean", "Saint Kitts and Nevis": "Latin America & Caribbean",
    "Saint Lucia": "Latin America & Caribbean", "Saint Vincent and the Grenadines": "Latin America & Caribbean",
    "Suriname": "Latin America & Caribbean", "Trinidad and Tobago": "Latin America & Caribbean",
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
    "Yemen": "Middle East & North Africa",

    # North America
    "Canada": "North America", "United States": "North America",
}

# Income group mapping (simplified - based on World Bank 2020 classifications)
INCOME_MAPPING = {
    # High income
    "Australia": "High income", "Austria": "High income", "Bahrain": "High income",
    "Belgium": "High income", "Canada": "High income", "Chile": "High income",
    "Croatia": "High income", "Cyprus": "High income", "Czechia": "High income",
    "Denmark": "High income", "Estonia": "High income", "Finland": "High income",
    "France": "High income", "Germany": "High income", "Greece": "High income",
    "Hong Kong": "High income", "Hungary": "High income", "Iceland": "High income",
    "Ireland": "High income", "Israel": "High income", "Italy": "High income",
    "Japan": "High income", "Kuwait": "High income", "Latvia": "High income",
    "Lithuania": "High income", "Luxembourg": "High income", "Macau": "High income",
    "Malta": "High income", "Netherlands": "High income", "New Zealand": "High income",
    "Norway": "High income", "Oman": "High income", "Poland": "High income",
    "Portugal": "High income", "Qatar": "High income", "Saudi Arabia": "High income",
    "Singapore": "High income", "Slovakia": "High income", "Slovenia": "High income",
    "South Korea": "High income", "Spain": "High income", "Sweden": "High income",
    "Switzerland": "High income", "United Arab Emirates": "High income",
    "United Kingdom": "High income", "United States": "High income", "Uruguay": "High income",
    "Seychelles": "High income", "Trinidad and Tobago": "High income", "Barbados": "High income",
    "Bahamas": "High income", "Antigua and Barbuda": "High income", "Saint Kitts and Nevis": "High income",
    "Brunei": "High income", "Aruba": "High income", "Puerto Rico": "High income",

    # Upper middle income
    "Albania": "Upper middle income", "Argentina": "Upper middle income", "Armenia": "Upper middle income",
    "Azerbaijan": "Upper middle income", "Belarus": "Upper middle income", "Bosnia and Herzegovina": "Upper middle income",
    "Botswana": "Upper middle income", "Brazil": "Upper middle income", "Bulgaria": "Upper middle income",
    "China": "Upper middle income", "Colombia": "Upper middle income", "Costa Rica": "Upper middle income",
    "Cuba": "Upper middle income", "Dominican Republic": "Upper middle income", "Ecuador": "Upper middle income",
    "Equatorial Guinea": "Upper middle income", "Fiji": "Upper middle income", "Gabon": "Upper middle income",
    "Georgia": "Upper middle income", "Guatemala": "Upper middle income", "Guyana": "Upper middle income",
    "Indonesia": "Upper middle income", "Iran": "Upper middle income", "Iraq": "Upper middle income",
    "Jamaica": "Upper middle income", "Jordan": "Upper middle income", "Kazakhstan": "Upper middle income",
    "Lebanon": "Upper middle income", "Libya": "Upper middle income", "Malaysia": "Upper middle income",
    "Maldives": "Upper middle income", "Mauritius": "Upper middle income", "Mexico": "Upper middle income",
    "Montenegro": "Upper middle income", "Namibia": "Upper middle income", "North Macedonia": "Upper middle income",
    "Panama": "Upper middle income", "Paraguay": "Upper middle income", "Peru": "Upper middle income",
    "Romania": "Upper middle income", "Russia": "Upper middle income", "Serbia": "Upper middle income",
    "South Africa": "Upper middle income", "Suriname": "Upper middle income", "Thailand": "Upper middle income",
    "Tonga": "Upper middle income", "Turkey": "Upper middle income", "Turkmenistan": "Upper middle income",
    "Venezuela": "Upper middle income", "Grenada": "Upper middle income", "Saint Lucia": "Upper middle income",
    "Dominica": "Upper middle income", "Saint Vincent and the Grenadines": "Upper middle income",

    # Lower middle income
    "Angola": "Lower middle income", "Bangladesh": "Lower middle income", "Belize": "Lower middle income",
    "Benin": "Lower middle income", "Bhutan": "Lower middle income", "Bolivia": "Lower middle income",
    "Cabo Verde": "Lower middle income", "Cambodia": "Lower middle income", "Cameroon": "Lower middle income",
    "Comoros": "Lower middle income", "Congo": "Lower middle income", "Cote d'Ivoire": "Lower middle income",
    "Djibouti": "Lower middle income", "Egypt": "Lower middle income", "El Salvador": "Lower middle income",
    "Eswatini": "Lower middle income", "Ghana": "Lower middle income", "Honduras": "Lower middle income",
    "India": "Lower middle income", "Kenya": "Lower middle income", "Kiribati": "Lower middle income",
    "Kyrgyzstan": "Lower middle income", "Laos": "Lower middle income", "Lesotho": "Lower middle income",
    "Mauritania": "Lower middle income", "Moldova": "Lower middle income", "Mongolia": "Lower middle income",
    "Morocco": "Lower middle income", "Myanmar": "Lower middle income", "Nepal": "Lower middle income",
    "Nicaragua": "Lower middle income", "Nigeria": "Lower middle income", "Pakistan": "Lower middle income",
    "Papua New Guinea": "Lower middle income", "Philippines": "Lower middle income",
    "Sao Tome and Principe": "Lower middle income", "Senegal": "Lower middle income",
    "Solomon Islands": "Lower middle income", "Sri Lanka": "Lower middle income",
    "Tajikistan": "Lower middle income", "Tanzania": "Lower middle income", "Timor": "Lower middle income",
    "Tunisia": "Lower middle income", "Ukraine": "Lower middle income", "Uzbekistan": "Lower middle income",
    "Vanuatu": "Lower middle income", "Vietnam": "Lower middle income", "Zambia": "Lower middle income",
    "Zimbabwe": "Lower middle income", "Algeria": "Lower middle income",

    # Low income
    "Afghanistan": "Low income", "Burkina Faso": "Low income", "Burundi": "Low income",
    "Central African Republic": "Low income", "Chad": "Low income",
    "Democratic Republic of Congo": "Low income", "Eritrea": "Low income",
    "Ethiopia": "Low income", "Gambia": "Low income", "Guinea": "Low income",
    "Guinea-Bissau": "Low income", "Haiti": "Low income", "Liberia": "Low income",
    "Madagascar": "Low income", "Malawi": "Low income", "Mali": "Low income",
    "Mozambique": "Low income", "Niger": "Low income", "Rwanda": "Low income",
    "Sierra Leone": "Low income", "Somalia": "Low income", "South Sudan": "Low income",
    "Sudan": "Low income", "Syria": "Low income", "Togo": "Low income", "Uganda": "Low income",
    "Yemen": "Low income",
}


def load_raw_data() -> pd.DataFrame:
    """Load raw food affordability data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading food affordability data from: {file_path}")
    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows, {df['Entity'].nunique()} countries")

    return df


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and add derived metrics."""
    logger.info("Cleaning and enriching data...")

    df = df.copy()

    # Rename columns
    df = df.rename(columns={
        'Entity': 'country',
        'Year': 'year',
        'cost_healthy_diet': 'cost_healthy_diet',
        'cost_nutrient_sufficient_diet': 'cost_nutrient_diet',
        'cost_energy_sufficient_diet': 'cost_energy_diet',
        'healthy_unaffordable_share': 'healthy_unaffordable_share',
        'healthy_unaffordable_number': 'healthy_unaffordable_number',
        'nutrition_sufficient_unaffordable_share': 'nutrient_unaffordable_share',
        'nutrition_sufficient_unaffordable_number': 'nutrient_unaffordable_number',
        'energy_sufficient_unaffordable_share': 'energy_unaffordable_share',
        'energy_sufficient_unaffordable_number': 'energy_unaffordable_number',
        'cost_staples': 'cost_staples',
        'cost_veg': 'cost_vegetables',
        'cost_fruits': 'cost_fruits',
        'cost_legumes': 'cost_legumes',
        'cost_animal_food': 'cost_animal',
        'cost_oils': 'cost_oils',
    })

    # Add region
    df["region"] = df["country"].map(REGION_MAPPING).fillna("Other")

    # Add income group
    df["income_group"] = df["country"].map(INCOME_MAPPING).fillna("Unknown")

    # Add affordability tier based on share unable to afford healthy diet
    def get_affordability_tier(share):
        if pd.isna(share):
            return "Unknown"
        if share <= 10:
            return "Affordable"
        elif share <= 30:
            return "Moderately Unaffordable"
        elif share <= 50:
            return "Unaffordable"
        else:
            return "Highly Unaffordable"

    df["affordability_tier"] = df["healthy_unaffordable_share"].apply(get_affordability_tier)

    # Select and order columns
    cols = ['country', 'year', 'region', 'income_group',
            'cost_healthy_diet', 'cost_nutrient_diet', 'cost_energy_diet',
            'healthy_unaffordable_share', 'healthy_unaffordable_number',
            'nutrient_unaffordable_share', 'nutrient_unaffordable_number',
            'energy_unaffordable_share', 'energy_unaffordable_number',
            'cost_staples', 'cost_vegetables', 'cost_fruits',
            'cost_legumes', 'cost_animal', 'cost_oils', 'affordability_tier']

    # Only keep columns that exist
    cols = [c for c in cols if c in df.columns]
    df = df[cols]

    logger.info(f"Enrichment complete. {df['region'].nunique()} regions, {df['income_group'].nunique()} income groups")

    return df


def create_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create country-level summary using latest year data."""
    logger.info("Creating country summary...")

    # Get latest year for each country
    latest = df.loc[df.groupby('country')['year'].idxmax()]

    summary = latest[['country', 'region', 'income_group', 'cost_healthy_diet',
                      'healthy_unaffordable_share', 'healthy_unaffordable_number',
                      'affordability_tier']].copy()

    # Add rankings
    summary['rank_by_cost'] = summary['cost_healthy_diet'].rank(ascending=True, na_option='bottom').astype(int)
    summary['rank_by_unaffordability'] = summary['healthy_unaffordable_share'].rank(ascending=False, na_option='bottom').astype(int)

    summary = summary.sort_values('rank_by_cost')

    logger.info(f"Created summary for {len(summary)} countries")

    return summary


def create_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create regional summary statistics."""
    logger.info("Creating region summary...")

    # Use latest year data
    latest = df.loc[df.groupby('country')['year'].idxmax()]

    region_stats = latest.groupby('region').agg({
        'country': 'count',
        'cost_healthy_diet': ['mean', 'min', 'max'],
        'healthy_unaffordable_share': 'mean',
        'healthy_unaffordable_number': 'sum',
    }).round(2)

    region_stats.columns = ['countries', 'avg_cost_healthy', 'min_cost', 'max_cost',
                            'avg_unaffordable_share', 'total_unaffordable_millions']

    region_stats = region_stats.reset_index()
    region_stats = region_stats.sort_values('avg_unaffordable_share', ascending=False)

    logger.info(f"Created summary for {len(region_stats)} regions")

    return region_stats


def create_income_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create income group summary statistics."""
    logger.info("Creating income group summary...")

    # Use latest year data
    latest = df.loc[df.groupby('country')['year'].idxmax()]

    income_stats = latest.groupby('income_group').agg({
        'country': 'count',
        'cost_healthy_diet': 'mean',
        'healthy_unaffordable_share': 'mean',
        'healthy_unaffordable_number': 'sum',
    }).round(2)

    income_stats.columns = ['countries', 'avg_cost_healthy', 'avg_unaffordable_share',
                            'total_unaffordable_millions']

    income_stats = income_stats.reset_index()

    logger.info(f"Created summary for {len(income_stats)} income groups")

    return income_stats


def create_diet_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Create diet type cost comparison."""
    logger.info("Creating diet comparison...")

    # Use latest year data with all three diet costs available
    latest = df.loc[df.groupby('country')['year'].idxmax()]

    comparison = latest[['country', 'region', 'cost_healthy_diet',
                         'cost_nutrient_diet', 'cost_energy_diet']].copy()

    comparison.columns = ['country', 'region', 'cost_healthy', 'cost_nutrient', 'cost_energy']

    # Calculate ratio of healthy diet cost to energy diet cost
    comparison['healthy_vs_energy_ratio'] = (
        comparison['cost_healthy'] / comparison['cost_energy']
    ).round(2)

    # Filter to rows with valid ratios
    comparison = comparison.dropna(subset=['healthy_vs_energy_ratio'])
    comparison = comparison.sort_values('healthy_vs_energy_ratio', ascending=False)

    logger.info(f"Created comparison for {len(comparison)} countries")

    return comparison


def run_food_affordability_pipeline(save_files: bool = True) -> dict:
    """Run the complete food affordability pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Food Affordability Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    enriched_df = clean_and_enrich(raw_df)
    country_summary = create_country_summary(enriched_df)
    region_summary = create_region_summary(enriched_df)
    income_summary = create_income_summary(enriched_df)
    diet_comparison = create_diet_comparison(enriched_df)

    # Save processed files
    if save_files:
        PROCESSED_PATH.mkdir(exist_ok=True)
        enriched_df.to_csv(PROCESSED_PATH / "food_affordability_enriched.csv", index=False)
        country_summary.to_csv(PROCESSED_PATH / "food_affordability_countries.csv", index=False)
        region_summary.to_csv(PROCESSED_PATH / "food_affordability_regions.csv", index=False)
        income_summary.to_csv(PROCESSED_PATH / "food_affordability_income.csv", index=False)
        diet_comparison.to_csv(PROCESSED_PATH / "food_affordability_diets.csv", index=False)
        logger.info(f"Saved processed files to {PROCESSED_PATH}")

    # Load to database
    from .database import FoodAffordabilityDatabase

    with FoodAffordabilityDatabase() as db:
        db.create_schema()
        db.load_data(enriched_df, country_summary, region_summary, income_summary, diet_comparison)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    logger.info("\nKey Insights:")
    logger.info(f"  Countries analyzed: {stats['countries']}")
    logger.info(f"  Total unable to afford healthy diet: {stats['total_unaffordable_billions']}B people")

    return stats


if __name__ == "__main__":
    stats = run_food_affordability_pipeline()
    print(json.dumps(stats, indent=2, default=str))
