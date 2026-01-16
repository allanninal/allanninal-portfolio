"""
ETL pipeline for National Poverty Lines (Jolliffe et al., 2022).

Harmonized national poverty lines in 2017 international-$ per person per day.
Shows how different countries define poverty, from <$1 to >$37/day.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import PovertyLinesDatabase

# Region mapping for countries
REGION_MAP = {
    # Europe
    "Albania": "Europe", "Austria": "Europe", "Belarus": "Europe",
    "Belgium": "Europe", "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Cyprus": "Europe", "Czechia": "Europe", "Denmark": "Europe",
    "Estonia": "Europe", "Finland": "Europe", "France": "Europe", "Germany": "Europe",
    "Greece": "Europe", "Hungary": "Europe", "Iceland": "Europe", "Ireland": "Europe",
    "Italy": "Europe", "Kosovo": "Europe", "Latvia": "Europe", "Lithuania": "Europe",
    "Luxembourg": "Europe", "Malta": "Europe", "Moldova": "Europe", "Montenegro": "Europe",
    "Netherlands": "Europe", "North Macedonia": "Europe", "Norway": "Europe", "Poland": "Europe",
    "Portugal": "Europe", "Romania": "Europe", "Russia": "Europe", "Serbia": "Europe",
    "Slovakia": "Europe", "Slovenia": "Europe", "Spain": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "Ukraine": "Europe", "United Kingdom": "Europe",
    # North America
    "Canada": "North America", "United States": "North America", "Mexico": "North America",
    # Central America & Caribbean
    "Belize": "Central America & Caribbean", "Costa Rica": "Central America & Caribbean",
    "El Salvador": "Central America & Caribbean", "Guatemala": "Central America & Caribbean",
    "Honduras": "Central America & Caribbean", "Nicaragua": "Central America & Caribbean",
    "Panama": "Central America & Caribbean", "Dominican Republic": "Central America & Caribbean",
    "Haiti": "Central America & Caribbean", "Jamaica": "Central America & Caribbean",
    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",
    # East Asia
    "China": "East Asia", "Japan": "East Asia", "South Korea": "East Asia",
    "Mongolia": "East Asia", "Taiwan": "East Asia",
    # Southeast Asia
    "Cambodia": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Laos": "Southeast Asia", "Malaysia": "Southeast Asia", "Myanmar": "Southeast Asia",
    "Philippines": "Southeast Asia", "Thailand": "Southeast Asia",
    "Timor": "Southeast Asia", "Vietnam": "Southeast Asia",
    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia", "Bhutan": "South Asia",
    "India": "South Asia", "Maldives": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",
    # Central Asia
    "Kazakhstan": "Central Asia", "Kyrgyzstan": "Central Asia", "Tajikistan": "Central Asia",
    "Turkmenistan": "Central Asia", "Uzbekistan": "Central Asia",
    "Armenia": "Central Asia", "Azerbaijan": "Central Asia", "Georgia": "Central Asia",
    # Middle East
    "Iran": "Middle East", "Iraq": "Middle East", "Israel": "Middle East",
    "Jordan": "Middle East", "Lebanon": "Middle East", "Palestine": "Middle East",
    "Turkey": "Middle East", "Yemen": "Middle East",
    # North Africa
    "Algeria": "North Africa", "Egypt": "North Africa", "Libya": "North Africa",
    "Morocco": "North Africa", "Sudan": "North Africa", "Tunisia": "North Africa",
    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa",
    "Cape Verde": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Comoros": "Sub-Saharan Africa", "Congo": "Sub-Saharan Africa",
    "Cote d'Ivoire": "Sub-Saharan Africa", "Democratic Republic of Congo": "Sub-Saharan Africa",
    "Djibouti": "Sub-Saharan Africa", "Equatorial Guinea": "Sub-Saharan Africa",
    "Eritrea": "Sub-Saharan Africa", "Eswatini": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Gabon": "Sub-Saharan Africa", "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa",
    "Guinea": "Sub-Saharan Africa", "Guinea-Bissau": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa", "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa", "Mali": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa",
    "Mauritius": "Sub-Saharan Africa", "Mozambique": "Sub-Saharan Africa", "Namibia": "Sub-Saharan Africa",
    "Niger": "Sub-Saharan Africa", "Nigeria": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa",
    "Sao Tome and Principe": "Sub-Saharan Africa", "Senegal": "Sub-Saharan Africa",
    "Seychelles": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "Somalia": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa", "South Sudan": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa",
    "Uganda": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa", "Zimbabwe": "Sub-Saharan Africa",
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
    "Papua New Guinea": "Oceania", "Solomon Islands": "Oceania", "Vanuatu": "Oceania",
    "Samoa": "Oceania", "Tonga": "Oceania", "Kiribati": "Oceania",
    "Micronesia": "Oceania", "Nauru": "Oceania", "Tuvalu": "Oceania",
}


def classify_poverty_line_tier(poverty_line: float) -> str:
    """Classify poverty line into tiers ($ per day)."""
    if poverty_line < 2.15:
        return "Extreme (<$2.15)"
    elif poverty_line < 3.65:
        return "Low ($2.15-$3.65)"
    elif poverty_line < 6.85:
        return "Lower-Middle ($3.65-$6.85)"
    elif poverty_line < 15:
        return "Upper-Middle ($6.85-$15)"
    else:
        return "High Income (>$15)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV."""
    logger.info(f"Extracting data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform data into analysis-ready format."""
    logger.info("Transforming data...")

    # Rename columns
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "World Bank income group": "income_group",
        "Harmonized national poverty line": "poverty_line"
    })

    # Add region
    df["region"] = df["country"].map(REGION_MAP).fillna("Other")

    # Add poverty line tier
    df["poverty_tier"] = df["poverty_line"].apply(classify_poverty_line_tier)

    # Round poverty line for display
    df["poverty_line_rounded"] = df["poverty_line"].round(2)

    logger.info(f"Countries: {df['country'].nunique()}")
    logger.info(f"Income groups: {df['income_group'].nunique()}")

    # Income group summary
    income_summary = df.groupby("income_group").agg(
        countries=("country", "count"),
        avg_poverty_line=("poverty_line", "mean"),
        min_poverty_line=("poverty_line", "min"),
        max_poverty_line=("poverty_line", "max"),
        median_poverty_line=("poverty_line", "median")
    ).reset_index()
    income_summary = income_summary.round(2)

    # Region summary
    region_summary = df.groupby("region").agg(
        countries=("country", "count"),
        avg_poverty_line=("poverty_line", "mean"),
        min_poverty_line=("poverty_line", "min"),
        max_poverty_line=("poverty_line", "max")
    ).reset_index()
    region_summary = region_summary.round(2)

    return df, income_summary, region_summary


def load(main_df: pd.DataFrame, income_df: pd.DataFrame, region_df: pd.DataFrame,
         db_path: Path = None):
    """Load data into database."""
    logger.info("Loading data into database...")

    with PovertyLinesDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, income_df, region_df)

        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")

    return stats


def run_poverty_lines_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the full ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "poverty_lines.csv"

    logger.info("Starting National Poverty Lines pipeline...")

    # ETL
    raw_df = extract(data_path)
    main_df, income_df, region_df = transform(raw_df)
    stats = load(main_df, income_df, region_df, db_path)

    logger.info("Pipeline completed successfully!")
    return stats


if __name__ == "__main__":
    stats = run_poverty_lines_pipeline()
    print("\nPipeline Results:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
