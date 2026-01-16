"""
ETL Pipeline for CO2 Emissions by Sector data (CAIT, 2020).

Data source: CAIT Climate Data Explorer via Climate Watch Portal.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import CO2EmissionsDatabase


# Region mapping for countries
REGION_MAPPING = {
    # Europe
    "Albania": "Europe", "Andorra": "Europe", "Austria": "Europe", "Belarus": "Europe",
    "Belgium": "Europe", "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Cyprus": "Europe", "Czech Republic": "Europe", "Czechia": "Europe",
    "Denmark": "Europe", "Estonia": "Europe", "Finland": "Europe", "France": "Europe",
    "Germany": "Europe", "Greece": "Europe", "Hungary": "Europe", "Iceland": "Europe",
    "Ireland": "Europe", "Italy": "Europe", "Kosovo": "Europe", "Latvia": "Europe",
    "Liechtenstein": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe",
    "Malta": "Europe", "Moldova": "Europe", "Monaco": "Europe", "Montenegro": "Europe",
    "Netherlands": "Europe", "North Macedonia": "Europe", "Norway": "Europe",
    "Poland": "Europe", "Portugal": "Europe", "Romania": "Europe", "Russia": "Europe",
    "San Marino": "Europe", "Serbia": "Europe", "Slovakia": "Europe", "Slovenia": "Europe",
    "Spain": "Europe", "Sweden": "Europe", "Switzerland": "Europe", "Ukraine": "Europe",
    "United Kingdom": "Europe",

    # Asia
    "Afghanistan": "Asia", "Armenia": "Asia", "Azerbaijan": "Asia", "Bahrain": "Asia",
    "Bangladesh": "Asia", "Bhutan": "Asia", "Brunei": "Asia", "Cambodia": "Asia",
    "China": "Asia", "Georgia": "Asia", "Hong Kong": "Asia", "India": "Asia",
    "Indonesia": "Asia", "Iran": "Asia", "Iraq": "Asia", "Israel": "Asia", "Japan": "Asia",
    "Jordan": "Asia", "Kazakhstan": "Asia", "Kuwait": "Asia", "Kyrgyzstan": "Asia",
    "Laos": "Asia", "Lebanon": "Asia", "Macao": "Asia", "Malaysia": "Asia",
    "Maldives": "Asia", "Mongolia": "Asia", "Myanmar": "Asia", "Nepal": "Asia",
    "North Korea": "Asia", "Oman": "Asia", "Pakistan": "Asia", "Palestine": "Asia",
    "Philippines": "Asia", "Qatar": "Asia", "Saudi Arabia": "Asia", "Singapore": "Asia",
    "South Korea": "Asia", "Sri Lanka": "Asia", "Syria": "Asia", "Taiwan": "Asia",
    "Tajikistan": "Asia", "Thailand": "Asia", "Timor": "Asia", "Turkey": "Asia",
    "Turkmenistan": "Asia", "United Arab Emirates": "Asia", "Uzbekistan": "Asia",
    "Vietnam": "Asia", "Yemen": "Asia",

    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Botswana": "Africa",
    "Burkina Faso": "Africa", "Burundi": "Africa", "Cameroon": "Africa",
    "Cape Verde": "Africa", "Central African Republic": "Africa", "Chad": "Africa",
    "Comoros": "Africa", "Congo": "Africa", "Cote d'Ivoire": "Africa",
    "Democratic Republic of Congo": "Africa", "Djibouti": "Africa", "Egypt": "Africa",
    "Equatorial Guinea": "Africa", "Eritrea": "Africa", "Eswatini": "Africa",
    "Ethiopia": "Africa", "Gabon": "Africa", "Gambia": "Africa", "Ghana": "Africa",
    "Guinea": "Africa", "Guinea-Bissau": "Africa", "Kenya": "Africa", "Lesotho": "Africa",
    "Liberia": "Africa", "Libya": "Africa", "Madagascar": "Africa", "Malawi": "Africa",
    "Mali": "Africa", "Mauritania": "Africa", "Mauritius": "Africa", "Morocco": "Africa",
    "Mozambique": "Africa", "Namibia": "Africa", "Niger": "Africa", "Nigeria": "Africa",
    "Rwanda": "Africa", "Sao Tome and Principe": "Africa", "Senegal": "Africa",
    "Seychelles": "Africa", "Sierra Leone": "Africa", "Somalia": "Africa",
    "South Africa": "Africa", "South Sudan": "Africa", "Sudan": "Africa",
    "Swaziland": "Africa", "Tanzania": "Africa", "Togo": "Africa", "Tunisia": "Africa",
    "Uganda": "Africa", "Zambia": "Africa", "Zimbabwe": "Africa",

    # North America
    "Antigua and Barbuda": "North America", "Bahamas": "North America",
    "Barbados": "North America", "Belize": "North America", "Canada": "North America",
    "Costa Rica": "North America", "Cuba": "North America", "Dominica": "North America",
    "Dominican Republic": "North America", "El Salvador": "North America",
    "Grenada": "North America", "Guatemala": "North America", "Haiti": "North America",
    "Honduras": "North America", "Jamaica": "North America", "Mexico": "North America",
    "Nicaragua": "North America", "Panama": "North America",
    "Saint Kitts and Nevis": "North America", "Saint Lucia": "North America",
    "Saint Vincent and the Grenadines": "North America",
    "Trinidad and Tobago": "North America", "United States": "North America",

    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",

    # Oceania
    "Australia": "Oceania", "Fiji": "Oceania", "Kiribati": "Oceania",
    "Marshall Islands": "Oceania", "Micronesia": "Oceania", "Nauru": "Oceania",
    "New Zealand": "Oceania", "Palau": "Oceania", "Papua New Guinea": "Oceania",
    "Samoa": "Oceania", "Solomon Islands": "Oceania", "Tonga": "Oceania",
    "Tuvalu": "Oceania", "Vanuatu": "Oceania",
}


def classify_per_capita(value: float) -> str:
    """Classify per capita emissions into tiers."""
    if pd.isna(value):
        return "No Data"
    if value >= 15:
        return "Very High (15+)"
    elif value >= 8:
        return "High (8-15)"
    elif value >= 4:
        return "Moderate (4-8)"
    elif value >= 1:
        return "Low (1-4)"
    else:
        return "Very Low (<1)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the CO2 emissions data."""
    logger.info("Transforming CO2 emissions data...")

    # Rename columns for easier access
    df = df.rename(columns={
        "Entity": "entity",
        "Year": "year",
        "Building (CAIT)": "building",
        "Int'l aviation & shipping (CAIT)": "aviation_shipping",
        "Electricity & Heat (CAIT)": "electricity_heat",
        "Energy (CAIT)": "energy",
        "Fugitive Emissions (CAIT)": "fugitive",
        "Industry (CAIT)": "industry",
        "Land-Use Change and Forestry (CAIT)": "land_use",
        "Manufacturing & Construction (CAIT)": "manufacturing",
        "Other Fuel Combustion (CAIT)": "other_fuel",
        "Total excluding LUCF (CAIT)": "total_excl_lucf",
        "Total including LUCF (CAIT)": "total_incl_lucf",
        "Transport (CAIT)": "transport",
        "Buildings (per capita) (CAIT)": "building_pc",
        "Electricity & Heat (per capita) (CAIT)": "electricity_heat_pc",
        "Fugitive Emissions (per capita) (CAIT)": "fugitive_pc",
        "Industry (per capita) (CAIT)": "industry_pc",
        "International aviation & shipping (per capita) (CAIT)": "aviation_shipping_pc",
        "Land-Use Change and Forestry (per capita) (CAIT)": "land_use_pc",
        "Manufacturing & Construction (per capita) (CAIT)": "manufacturing_pc",
        "Total excluding LUCF (per capita) (CAIT)": "total_excl_lucf_pc",
        "Total including LUCF (per capita) (CAIT)": "total_incl_lucf_pc",
        "Transport (per capita) (CAIT)": "transport_pc",
    })

    # Exclude aggregate entities
    aggregate_entities = ["World", "European Union (27)"]
    df = df[~df["entity"].isin(aggregate_entities)].copy()

    # Add region mapping
    df["region"] = df["entity"].map(REGION_MAPPING)
    df["region"] = df["region"].fillna("Other")

    # Add per capita tier classification
    df["per_capita_tier"] = df["total_excl_lucf_pc"].apply(classify_per_capita)

    # Get latest year data for main analysis
    latest_year = df["year"].max()
    latest_df = df[df["year"] == latest_year].copy()

    logger.info(f"Latest year: {latest_year}")
    logger.info(f"Processed {len(latest_df)} countries for latest year")

    # Create country summary (latest year only for simpler analysis)
    country_summary = latest_df[[
        "entity", "year", "region", "total_excl_lucf", "total_incl_lucf",
        "electricity_heat", "transport", "industry", "building", "manufacturing",
        "land_use", "total_excl_lucf_pc", "per_capita_tier"
    ]].copy()

    # Calculate sector shares
    country_summary["electricity_share"] = (country_summary["electricity_heat"] / country_summary["total_excl_lucf"] * 100).fillna(0)
    country_summary["transport_share"] = (country_summary["transport"] / country_summary["total_excl_lucf"] * 100).fillna(0)
    country_summary["industry_share"] = (country_summary["industry"] / country_summary["total_excl_lucf"] * 100).fillna(0)
    country_summary["manufacturing_share"] = (country_summary["manufacturing"] / country_summary["total_excl_lucf"] * 100).fillna(0)

    logger.info(f"Created country summary with {len(country_summary)} countries")

    # Create region summary
    region_summary = latest_df.groupby("region").agg({
        "entity": "count",
        "total_excl_lucf": "sum",
        "total_incl_lucf": "sum",
        "electricity_heat": "sum",
        "transport": "sum",
        "industry": "sum",
        "manufacturing": "sum",
        "land_use": "sum",
        "total_excl_lucf_pc": "mean",
    }).reset_index()
    region_summary.columns = [
        "region", "countries", "total_emissions", "total_incl_lucf",
        "electricity_heat", "transport", "industry", "manufacturing",
        "land_use", "avg_per_capita"
    ]
    logger.info(f"Created summary for {len(region_summary)} regions")

    # Create sector summary (global totals by sector for latest year)
    global_latest = latest_df[latest_df["total_excl_lucf"].notna()]
    sector_totals = {
        "Electricity & Heat": global_latest["electricity_heat"].sum(),
        "Transport": global_latest["transport"].sum(),
        "Manufacturing": global_latest["manufacturing"].sum(),
        "Industry": global_latest["industry"].sum(),
        "Building": global_latest["building"].sum(),
        "Fugitive Emissions": global_latest["fugitive"].sum(),
        "Other Fuel Combustion": global_latest["other_fuel"].sum(),
    }
    sector_summary = pd.DataFrame([
        {"sector": k, "emissions": v, "share": v / sum(sector_totals.values()) * 100 if sum(sector_totals.values()) > 0 else 0}
        for k, v in sector_totals.items()
    ])
    sector_summary = sector_summary.sort_values("emissions", ascending=False)
    logger.info(f"Created sector summary with {len(sector_summary)} sectors")

    # Create per capita tier summary
    tier_summary = latest_df.groupby("per_capita_tier").agg({
        "entity": "count",
        "total_excl_lucf_pc": ["mean", "min", "max"],
        "total_excl_lucf": "sum",
    }).reset_index()
    tier_summary.columns = [
        "per_capita_tier", "countries", "avg_per_capita",
        "min_per_capita", "max_per_capita", "total_emissions"
    ]
    logger.info(f"Created summary for {len(tier_summary)} per capita tiers")

    return df, country_summary, region_summary, sector_summary, tier_summary


def load(full_df: pd.DataFrame, country_df: pd.DataFrame, region_df: pd.DataFrame,
         sector_df: pd.DataFrame, tier_df: pd.DataFrame, db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with CO2EmissionsDatabase(db_path) as db:
        db.create_schema()
        db.load_data(full_df, country_df, region_df, sector_df, tier_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_co2_emissions_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "co2_emissions_by_sector.csv"

    logger.info("=" * 50)
    logger.info("Starting CO2 Emissions by Sector ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    full_df, country_df, region_df, sector_df, tier_df = transform(raw_df)
    stats = load(full_df, country_df, region_df, sector_df, tier_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Countries: {stats['countries']}")
    logger.info(f"Year range: {stats['year_min']} - {stats['year_max']}")
    logger.info(f"Global emissions ({stats['year_max']}): {stats['global_emissions_gt']:.1f} Gt CO2")
    logger.info(f"Top emitter: {stats['top_emitter']} ({stats['top_emitter_gt']:.1f} Gt)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_co2_emissions_pipeline()
