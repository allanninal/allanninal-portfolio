"""
ETL Pipeline for Air Pollution Deaths data (Lelieveld et al. 2019).

Data source: Deaths attributed to air pollution from different sources.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import AirPollutionDatabase


# Region mapping for countries
REGION_MAPPING = {
    # Europe
    "Albania": "Europe", "Austria": "Europe", "Belarus": "Europe", "Belgium": "Europe",
    "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe", "Croatia": "Europe",
    "Cyprus": "Europe", "Czech Republic": "Europe", "Denmark": "Europe", "Estonia": "Europe",
    "Finland": "Europe", "France": "Europe", "Germany": "Europe", "Greece": "Europe",
    "Hungary": "Europe", "Iceland": "Europe", "Ireland": "Europe", "Italy": "Europe",
    "Latvia": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe", "Macedonia": "Europe",
    "Moldova": "Europe", "Netherlands": "Europe", "Norway": "Europe", "Poland": "Europe",
    "Portugal": "Europe", "Romania": "Europe", "Russia": "Europe", "Serbia and Montenegro": "Europe",
    "Slovakia": "Europe", "Slovenia": "Europe", "Spain": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "Ukraine": "Europe", "United Kingdom": "Europe",

    # Asia
    "Afghanistan": "Asia", "Armenia": "Asia", "Azerbaijan": "Asia", "Bahrain": "Asia",
    "Bangladesh": "Asia", "Bhutan": "Asia", "Brunei": "Asia", "Cambodia": "Asia",
    "China": "Asia", "Georgia": "Asia", "India": "Asia", "Indonesia": "Asia",
    "Iran": "Asia", "Iraq": "Asia", "Israel": "Asia", "Japan": "Asia", "Jordan": "Asia",
    "Kazakhstan": "Asia", "Kuwait": "Asia", "Kyrgyzstan": "Asia", "Laos": "Asia",
    "Lebanon": "Asia", "Malaysia": "Asia", "Maldives": "Asia", "Mongolia": "Asia",
    "Myanmar": "Asia", "Nepal": "Asia", "North Korea": "Asia", "Oman": "Asia",
    "Pakistan": "Asia", "Philippines": "Asia", "Qatar": "Asia", "Saudi Arabia": "Asia",
    "Singapore": "Asia", "South Korea": "Asia", "Sri Lanka": "Asia", "Syria": "Asia",
    "Tajikistan": "Asia", "Thailand": "Asia", "Timor": "Asia", "Turkey": "Asia",
    "Turkmenistan": "Asia", "United Arab Emirates": "Asia", "Uzbekistan": "Asia",
    "Vietnam": "Asia", "Yemen": "Asia",

    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Botswana": "Africa",
    "Burkina Faso": "Africa", "Burundi": "Africa", "Cameroon": "Africa",
    "Cape Verde": "Africa", "Central African Republic": "Africa", "Chad": "Africa",
    "Comoros": "Africa", "Congo": "Africa", "Cote d'Ivoire": "Africa",
    "Democratic Republic of Congo": "Africa", "Djibouti": "Africa", "Egypt": "Africa",
    "Equatorial Guinea": "Africa", "Eritrea": "Africa", "Ethiopia": "Africa",
    "Gabon": "Africa", "Gambia": "Africa", "Ghana": "Africa", "Guinea": "Africa",
    "Guinea-Bissau": "Africa", "Kenya": "Africa", "Lesotho": "Africa", "Liberia": "Africa",
    "Libya": "Africa", "Madagascar": "Africa", "Malawi": "Africa", "Mali": "Africa",
    "Mauritania": "Africa", "Mauritius": "Africa", "Morocco": "Africa",
    "Mozambique": "Africa", "Namibia": "Africa", "Niger": "Africa", "Nigeria": "Africa",
    "Rwanda": "Africa", "Sao Tome and Principe": "Africa", "Senegal": "Africa",
    "Seychelles": "Africa", "Sierra Leone": "Africa", "Somalia": "Africa",
    "South Africa": "Africa", "Sudan and South Sudan": "Africa", "Swaziland": "Africa",
    "Tanzania": "Africa", "Togo": "Africa", "Tunisia": "Africa", "Uganda": "Africa",
    "Zambia": "Africa", "Zimbabwe": "Africa",

    # North America
    "Canada": "North America", "United States": "North America", "Mexico": "North America",
    "Bahamas": "North America", "Barbados": "North America", "Belize": "North America",
    "Costa Rica": "North America", "Cuba": "North America", "Dominican Republic": "North America",
    "El Salvador": "North America", "Guatemala": "North America", "Haiti": "North America",
    "Honduras": "North America", "Jamaica": "North America", "Nicaragua": "North America",
    "Panama": "North America", "Trinidad and Tobago": "North America",
    "Antigua and Barbuda": "North America", "Grenada": "North America",
    "Saint Lucia": "North America", "Saint Vincent and the Grenadines": "North America",

    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",

    # Oceania
    "Australia": "Oceania", "Fiji": "Oceania", "Kiribati": "Oceania",
    "Micronesia": "Oceania", "New Zealand": "Oceania", "Papua New Guinea": "Oceania",
    "Samoa": "Oceania", "Solomon Islands": "Oceania", "Tonga": "Oceania",
    "Vanuatu": "Oceania",
}


def classify_death_rate(rate: float) -> str:
    """Classify death rate per 100,000 into tiers."""
    if rate >= 150:
        return "Very High (150+)"
    elif rate >= 100:
        return "High (100-150)"
    elif rate >= 50:
        return "Moderate (50-100)"
    elif rate >= 25:
        return "Low (25-50)"
    else:
        return "Very Low (<25)"


def classify_fossil_share(share: float) -> str:
    """Classify fossil fuel share of deaths into tiers."""
    if share >= 50:
        return "Very High (50%+)"
    elif share >= 30:
        return "High (30-50%)"
    elif share >= 15:
        return "Moderate (15-30%)"
    elif share >= 5:
        return "Low (5-15%)"
    else:
        return "Very Low (<5%)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the air pollution data."""
    logger.info("Transforming air pollution data...")

    # Rename columns for easier access
    df = df.rename(columns={
        "Entity": "entity",
        "Year": "year",
        "Excess mortality from air pollution (all sources)": "deaths_all_sources",
        "Excess mortality from fossil fuels": "deaths_fossil_fuels",
        "Excess mortality from all anthropogenic pollution": "deaths_anthropogenic",
        "Total Years Life Lost from air pollution (all sources)": "yll_all_sources",
        "Total Years Life Lost from fossil fuels": "yll_fossil_fuels",
        "Total Years Life Lost from all anthropogenic pollution": "yll_anthropogenic",
        "Death rates from all air pollution (per 100,000)": "death_rate_all",
        "Death rates from air pollution from fossil fuels (per 100,000)": "death_rate_fossil",
        "Death rates from all anthropogenic air pollution (per 100,000)": "death_rate_anthropogenic",
        "YLL rates from all air pollution (per 100,000)": "yll_rate_all",
        "YLL rates from air pollution from fossil fuels (per 100,000)": "yll_rate_fossil",
        "YLL rates from anthropogenic air pollution (per 100,000)": "yll_rate_anthropogenic",
        "Deaths from fossil pollution as a share of total air pollution deaths": "share_fossil_total",
        "Deaths from fossil pollution as a share of total anthropogenic air pollution deaths": "share_fossil_anthropogenic",
        "Deaths from anthropogenic pollution as a share of total air pollution deaths": "share_anthropogenic_total",
    })

    # Identify aggregate regions in the data
    aggregate_regions = [
        "Africa", "East Asia", "Europe", "North America", "Oceania",
        "South America", "South and Southeast Asia", "West Asia", "World"
    ]

    # Filter to countries only (exclude aggregate regions)
    countries_df = df[~df["entity"].isin(aggregate_regions)].copy()

    # Add region mapping
    countries_df["region"] = countries_df["entity"].map(REGION_MAPPING)
    countries_df["region"] = countries_df["region"].fillna("Other")

    # Add tier classifications
    countries_df["death_rate_tier"] = countries_df["death_rate_all"].apply(classify_death_rate)
    countries_df["fossil_share_tier"] = countries_df["share_fossil_total"].apply(classify_fossil_share)

    # Convert deaths to thousands for readability
    countries_df["deaths_all_thousands"] = countries_df["deaths_all_sources"] / 1000
    countries_df["deaths_fossil_thousands"] = countries_df["deaths_fossil_fuels"] / 1000
    countries_df["deaths_anthropogenic_thousands"] = countries_df["deaths_anthropogenic"] / 1000

    # Convert YLL to millions
    countries_df["yll_all_millions"] = countries_df["yll_all_sources"] / 1e6
    countries_df["yll_fossil_millions"] = countries_df["yll_fossil_fuels"] / 1e6

    logger.info(f"Processed {len(countries_df)} countries")

    # Create region summary
    region_summary = countries_df.groupby("region").agg({
        "entity": "count",
        "deaths_all_sources": "sum",
        "deaths_fossil_fuels": "sum",
        "deaths_anthropogenic": "sum",
        "yll_all_sources": "sum",
        "death_rate_all": "mean",
        "death_rate_fossil": "mean",
        "share_fossil_total": "mean",
    }).reset_index()
    region_summary.columns = [
        "region", "countries", "total_deaths_all", "total_deaths_fossil",
        "total_deaths_anthropogenic", "total_yll", "avg_death_rate",
        "avg_death_rate_fossil", "avg_fossil_share"
    ]
    region_summary["deaths_millions"] = region_summary["total_deaths_all"] / 1e6
    region_summary["yll_millions"] = region_summary["total_yll"] / 1e6
    logger.info(f"Created summary for {len(region_summary)} regions")

    # Create death rate tier summary
    death_rate_summary = countries_df.groupby("death_rate_tier").agg({
        "entity": "count",
        "death_rate_all": ["mean", "min", "max"],
        "share_fossil_total": "mean",
        "deaths_all_sources": "sum",
    }).reset_index()
    death_rate_summary.columns = [
        "death_rate_tier", "countries", "avg_death_rate", "min_death_rate",
        "max_death_rate", "avg_fossil_share", "total_deaths"
    ]
    logger.info(f"Created summary for {len(death_rate_summary)} death rate tiers")

    # Create fossil share tier summary
    fossil_share_summary = countries_df.groupby("fossil_share_tier").agg({
        "entity": "count",
        "share_fossil_total": ["mean", "min", "max"],
        "death_rate_all": "mean",
        "deaths_fossil_fuels": "sum",
    }).reset_index()
    fossil_share_summary.columns = [
        "fossil_share_tier", "countries", "avg_fossil_share", "min_fossil_share",
        "max_fossil_share", "avg_death_rate", "total_fossil_deaths"
    ]
    logger.info(f"Created summary for {len(fossil_share_summary)} fossil share tiers")

    return countries_df, region_summary, death_rate_summary, fossil_share_summary


def load(main_df: pd.DataFrame, region_df: pd.DataFrame,
         death_rate_df: pd.DataFrame, fossil_share_df: pd.DataFrame,
         db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with AirPollutionDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, region_df, death_rate_df, fossil_share_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_air_pollution_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "air_pollution_deaths.csv"

    logger.info("=" * 50)
    logger.info("Starting Air Pollution Deaths ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    main_df, region_df, death_rate_df, fossil_share_df = transform(raw_df)
    stats = load(main_df, region_df, death_rate_df, fossil_share_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Total countries: {stats['countries']}")
    logger.info(f"Total deaths: {stats['total_deaths_millions']:.2f} million")
    logger.info(f"Highest death rate: {stats['highest_death_rate_country']} ({stats['highest_death_rate']:.1f}/100k)")
    logger.info(f"Most deaths: {stats['most_deaths_country']} ({stats['most_deaths_thousands']:.0f}k)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_air_pollution_pipeline()
