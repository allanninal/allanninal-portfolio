"""
ETL Pipeline for Plastic Ocean Pollution data (Meijer et al. 2021).

Data source: More than 1000 rivers account for 80% of global riverine plastic emissions.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import PlasticOceanDatabase


# Region mapping for countries
REGION_MAPPING = {
    # Europe
    "Albania": "Europe", "Belgium": "Europe", "Bosnia and Herzegovina": "Europe",
    "Bulgaria": "Europe", "Croatia": "Europe", "Cyprus": "Europe", "Denmark": "Europe",
    "Estonia": "Europe", "Finland": "Europe", "France": "Europe", "Germany": "Europe",
    "Greece": "Europe", "Ireland": "Europe", "Italy": "Europe", "Latvia": "Europe",
    "Lithuania": "Europe", "Malta": "Europe", "Montenegro": "Europe", "Netherlands": "Europe",
    "Norway": "Europe", "Poland": "Europe", "Portugal": "Europe", "Romania": "Europe",
    "Russia": "Europe", "Serbia": "Europe", "Slovenia": "Europe", "Spain": "Europe",
    "Sweden": "Europe", "Ukraine": "Europe", "United Kingdom": "Europe",

    # Asia
    "Afghanistan": "Asia", "Bahrain": "Asia", "Bangladesh": "Asia", "Brunei": "Asia",
    "Cambodia": "Asia", "China": "Asia", "Georgia": "Asia", "Hong Kong": "Asia",
    "India": "Asia", "Indonesia": "Asia", "Iran": "Asia", "Iraq": "Asia",
    "Israel": "Asia", "Japan": "Asia", "Jordan": "Asia", "Kuwait": "Asia",
    "Lebanon": "Asia", "Malaysia": "Asia", "Maldives": "Asia", "Myanmar": "Asia",
    "Nepal": "Asia", "North Korea": "Asia", "Oman": "Asia", "Pakistan": "Asia",
    "Philippines": "Asia", "Qatar": "Asia", "Saudi Arabia": "Asia", "Singapore": "Asia",
    "South Korea": "Asia", "Sri Lanka": "Asia", "Syria": "Asia", "Taiwan": "Asia",
    "Thailand": "Asia", "Timor": "Asia", "Turkey": "Asia", "United Arab Emirates": "Asia",
    "Vietnam": "Asia", "Yemen": "Asia",

    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Burkina Faso": "Africa",
    "Cameroon": "Africa", "Cape Verde": "Africa", "Comoros": "Africa", "Congo": "Africa",
    "Cote d'Ivoire": "Africa", "Democratic Republic of Congo": "Africa", "Djibouti": "Africa",
    "Egypt": "Africa", "Equatorial Guinea": "Africa", "Eritrea": "Africa", "Gabon": "Africa",
    "Gambia": "Africa", "Ghana": "Africa", "Guinea": "Africa", "Guinea-Bissau": "Africa",
    "Kenya": "Africa", "Liberia": "Africa", "Libya": "Africa", "Madagascar": "Africa",
    "Mauritania": "Africa", "Mauritius": "Africa", "Morocco": "Africa", "Mozambique": "Africa",
    "Namibia": "Africa", "Nigeria": "Africa", "Sao Tome and Principe": "Africa",
    "Senegal": "Africa", "Sierra Leone": "Africa", "Somalia": "Africa", "South Africa": "Africa",
    "Sudan": "Africa", "Tanzania": "Africa", "Togo": "Africa", "Tunisia": "Africa",

    # North America
    "Antigua and Barbuda": "North America", "Bahamas": "North America",
    "Barbados": "North America", "Belize": "North America", "Canada": "North America",
    "Costa Rica": "North America", "Cuba": "North America", "Dominica": "North America",
    "Dominican Republic": "North America", "El Salvador": "North America",
    "Grenada": "North America", "Guatemala": "North America", "Haiti": "North America",
    "Honduras": "North America", "Jamaica": "North America", "Mexico": "North America",
    "Nicaragua": "North America", "Panama": "North America", "Puerto Rico": "North America",
    "Saint Kitts and Nevis": "North America", "Saint Lucia": "North America",
    "Saint Vincent and the Grenadines": "North America",
    "Trinidad and Tobago": "North America", "United States": "North America",

    # South America
    "Argentina": "South America", "Brazil": "South America", "Chile": "South America",
    "Colombia": "South America", "Ecuador": "South America", "French Guiana": "South America",
    "Guyana": "South America", "Peru": "South America", "Suriname": "South America",
    "Uruguay": "South America", "Venezuela": "South America",

    # Oceania
    "Australia": "Oceania", "Fiji": "Oceania", "Micronesia": "Oceania",
    "New Caledonia": "Oceania", "New Zealand": "Oceania", "Papua New Guinea": "Oceania",
    "Samoa": "Oceania", "Solomon Islands": "Oceania", "Tonga": "Oceania", "Vanuatu": "Oceania",
}


def classify_ocean_emission(share: float) -> str:
    """Classify share of global ocean plastic emissions into tiers."""
    if pd.isna(share):
        return "No Data"
    if share >= 5:
        return "Very High (5%+)"
    elif share >= 1:
        return "High (1-5%)"
    elif share >= 0.1:
        return "Moderate (0.1-1%)"
    elif share >= 0.01:
        return "Low (0.01-0.1%)"
    else:
        return "Very Low (<0.01%)"


def classify_per_capita(value: float) -> str:
    """Classify per capita ocean emissions into tiers."""
    if pd.isna(value):
        return "No Data"
    if value >= 1:
        return "Very High (1+ kg)"
    elif value >= 0.1:
        return "High (0.1-1 kg)"
    elif value >= 0.01:
        return "Moderate (0.01-0.1 kg)"
    elif value > 0:
        return "Low (<0.01 kg)"
    else:
        return "Zero"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the plastic ocean data."""
    logger.info("Transforming plastic ocean pollution data...")

    # Rename columns for easier access
    df = df.rename(columns={
        "Entity": "entity",
        "Year": "year",
        "Probability of plastic being emitted to ocean": "probability",
        "Mismanaged plastic waste (metric tons year-1)": "mismanaged_waste",
        "Mismanaged waste emitted to the ocean (metric tons year-1)": "ocean_emissions",
        "Share of mismanaged plastic waste emitted to ocean": "share_emitted",
        "Share of global mismanaged plastic waste": "share_global_waste",
        "Share of global plastics emitted to ocean": "share_global_ocean",
        "Mismanaged plastic waste per capita (kg per year)": "waste_per_capita",
        "Mismanaged plastic waste to ocean per capita (kg per year)": "ocean_per_capita",
    })

    # Identify aggregate regions in the data
    aggregate_regions = ["Africa", "Asia", "Europe", "EU-27", "North America", "Oceania", "South America", "World"]

    # Filter to countries only (exclude aggregate regions)
    countries_df = df[~df["entity"].isin(aggregate_regions)].copy()

    # Add region mapping
    countries_df["region"] = countries_df["entity"].map(REGION_MAPPING)
    countries_df["region"] = countries_df["region"].fillna("Other")

    # Add tier classifications
    countries_df["ocean_tier"] = countries_df["share_global_ocean"].apply(classify_ocean_emission)
    countries_df["per_capita_tier"] = countries_df["ocean_per_capita"].apply(classify_per_capita)

    # Convert to thousands of tonnes for readability
    countries_df["mismanaged_kt"] = countries_df["mismanaged_waste"] / 1000
    countries_df["ocean_kt"] = countries_df["ocean_emissions"] / 1000

    logger.info(f"Processed {len(countries_df)} countries")

    # Create region summary
    region_summary = countries_df.groupby("region").agg({
        "entity": "count",
        "mismanaged_waste": "sum",
        "ocean_emissions": "sum",
        "share_global_ocean": "sum",
        "waste_per_capita": "mean",
        "ocean_per_capita": "mean",
    }).reset_index()
    region_summary.columns = [
        "region", "countries", "total_mismanaged", "total_ocean_emissions",
        "share_global_ocean", "avg_waste_per_capita", "avg_ocean_per_capita"
    ]
    region_summary["mismanaged_kt"] = region_summary["total_mismanaged"] / 1000
    region_summary["ocean_kt"] = region_summary["total_ocean_emissions"] / 1000
    logger.info(f"Created summary for {len(region_summary)} regions")

    # Create ocean tier summary
    ocean_tier_summary = countries_df.groupby("ocean_tier").agg({
        "entity": "count",
        "share_global_ocean": ["sum", "mean", "min", "max"],
        "ocean_emissions": "sum",
    }).reset_index()
    ocean_tier_summary.columns = [
        "ocean_tier", "countries", "total_share", "avg_share",
        "min_share", "max_share", "total_emissions"
    ]
    logger.info(f"Created summary for {len(ocean_tier_summary)} ocean emission tiers")

    # Create per capita tier summary
    per_capita_summary = countries_df.groupby("per_capita_tier").agg({
        "entity": "count",
        "ocean_per_capita": ["mean", "min", "max"],
        "ocean_emissions": "sum",
    }).reset_index()
    per_capita_summary.columns = [
        "per_capita_tier", "countries", "avg_per_capita",
        "min_per_capita", "max_per_capita", "total_emissions"
    ]
    logger.info(f"Created summary for {len(per_capita_summary)} per capita tiers")

    return countries_df, region_summary, ocean_tier_summary, per_capita_summary


def load(main_df: pd.DataFrame, region_df: pd.DataFrame,
         ocean_tier_df: pd.DataFrame, per_capita_df: pd.DataFrame,
         db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with PlasticOceanDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, region_df, ocean_tier_df, per_capita_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_plastic_ocean_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "plastic_ocean_pollution.csv"

    logger.info("=" * 50)
    logger.info("Starting Plastic Ocean Pollution ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    main_df, region_df, ocean_tier_df, per_capita_df = transform(raw_df)
    stats = load(main_df, region_df, ocean_tier_df, per_capita_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Countries: {stats['countries']}")
    logger.info(f"Global ocean emissions: {stats['total_ocean_kt']:.0f} kt")
    logger.info(f"Top emitter: {stats['top_emitter']} ({stats['top_emitter_share']:.1f}%)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_plastic_ocean_pipeline()
