"""
ETL pipeline for Child Mortality Rates (Gapminder v10, 2017).

Data spans 1800-2100 (with projections after 2016).
Child mortality = deaths per 1,000 live births before age 5.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import ChildMortalityDatabase

# Territories/entities to exclude (no meaningful data or not countries)
EXCLUDE_ENTITIES = {
    "French Southern Territories",
    "Heard Island and McDonald Islands",
    "South Georgia and the South Sandwich Islands",
    "Channel Islands",
}

# Region mapping for countries
REGION_MAP = {
    # Europe
    "Albania": "Europe", "Andorra": "Europe", "Austria": "Europe", "Belarus": "Europe",
    "Belgium": "Europe", "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Cyprus": "Europe", "Czech Republic": "Europe", "Denmark": "Europe",
    "Estonia": "Europe", "Finland": "Europe", "France": "Europe", "Germany": "Europe",
    "Greece": "Europe", "Hungary": "Europe", "Iceland": "Europe", "Ireland": "Europe",
    "Italy": "Europe", "Latvia": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe",
    "Macedonia": "Europe", "Malta": "Europe", "Moldova": "Europe", "Monaco": "Europe",
    "Montenegro": "Europe", "Netherlands": "Europe", "Norway": "Europe", "Poland": "Europe",
    "Portugal": "Europe", "Romania": "Europe", "Russia": "Europe", "San Marino": "Europe",
    "Serbia": "Europe", "Slovakia": "Europe", "Slovenia": "Europe", "Spain": "Europe",
    "Sweden": "Europe", "Switzerland": "Europe", "Ukraine": "Europe", "United Kingdom": "Europe",
    # North America
    "Canada": "North America", "United States": "North America", "Mexico": "North America",
    "Greenland": "North America", "Bermuda": "North America",
    # Central America & Caribbean
    "Belize": "Central America & Caribbean", "Costa Rica": "Central America & Caribbean",
    "El Salvador": "Central America & Caribbean", "Guatemala": "Central America & Caribbean",
    "Honduras": "Central America & Caribbean", "Nicaragua": "Central America & Caribbean",
    "Panama": "Central America & Caribbean", "Cuba": "Central America & Caribbean",
    "Dominican Republic": "Central America & Caribbean", "Haiti": "Central America & Caribbean",
    "Jamaica": "Central America & Caribbean", "Puerto Rico": "Central America & Caribbean",
    "Trinidad and Tobago": "Central America & Caribbean", "Bahamas": "Central America & Caribbean",
    "Barbados": "Central America & Caribbean", "Antigua and Barbuda": "Central America & Caribbean",
    "Aruba": "Central America & Caribbean", "Curacao": "Central America & Caribbean",
    "Grenada": "Central America & Caribbean", "Saint Lucia": "Central America & Caribbean",
    "Saint Vincent and the Grenadines": "Central America & Caribbean",
    "United States Virgin Islands": "Central America & Caribbean",
    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",
    # East Asia
    "China": "East Asia", "Japan": "East Asia", "South Korea": "East Asia",
    "North Korea": "East Asia", "Mongolia": "East Asia", "Taiwan": "East Asia",
    "Hong Kong": "East Asia", "Macao": "East Asia",
    # Southeast Asia
    "Brunei": "Southeast Asia", "Cambodia": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Laos": "Southeast Asia", "Malaysia": "Southeast Asia", "Myanmar": "Southeast Asia",
    "Philippines": "Southeast Asia", "Singapore": "Southeast Asia", "Thailand": "Southeast Asia",
    "Timor": "Southeast Asia", "Vietnam": "Southeast Asia",
    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia", "Bhutan": "South Asia",
    "India": "South Asia", "Maldives": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",
    # Central Asia
    "Kazakhstan": "Central Asia", "Kyrgyzstan": "Central Asia", "Tajikistan": "Central Asia",
    "Turkmenistan": "Central Asia", "Uzbekistan": "Central Asia",
    # Middle East
    "Bahrain": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
    "Israel": "Middle East", "Jordan": "Middle East", "Kuwait": "Middle East",
    "Lebanon": "Middle East", "Oman": "Middle East", "Palestine": "Middle East",
    "Qatar": "Middle East", "Saudi Arabia": "Middle East", "Syria": "Middle East",
    "Turkey": "Middle East", "United Arab Emirates": "Middle East", "Yemen": "Middle East",
    # North Africa
    "Algeria": "North Africa", "Egypt": "North Africa", "Libya": "North Africa",
    "Morocco": "North Africa", "Sudan": "North Africa", "Tunisia": "North Africa",
    "Western Sahara": "North Africa",
    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa",
    "Cape Verde": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa", "Comoros": "Sub-Saharan Africa", "Congo": "Sub-Saharan Africa",
    "Cote d'Ivoire": "Sub-Saharan Africa", "Democratic Republic of Congo": "Sub-Saharan Africa",
    "Djibouti": "Sub-Saharan Africa", "Equatorial Guinea": "Sub-Saharan Africa",
    "Eritrea": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa", "Gabon": "Sub-Saharan Africa",
    "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa", "Guinea": "Sub-Saharan Africa",
    "Guinea-Bissau": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa", "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa", "Malawi": "Sub-Saharan Africa",
    "Mali": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa", "Mauritius": "Sub-Saharan Africa",
    "Mozambique": "Sub-Saharan Africa", "Namibia": "Sub-Saharan Africa", "Niger": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa", "Sao Tome and Principe": "Sub-Saharan Africa",
    "Senegal": "Sub-Saharan Africa", "Seychelles": "Sub-Saharan Africa", "Sierra Leone": "Sub-Saharan Africa",
    "Somalia": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa", "South Sudan": "Sub-Saharan Africa",
    "Swaziland": "Sub-Saharan Africa", "Tanzania": "Sub-Saharan Africa", "Togo": "Sub-Saharan Africa",
    "Uganda": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa", "Zimbabwe": "Sub-Saharan Africa",
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
    "Papua New Guinea": "Oceania", "Solomon Islands": "Oceania", "Vanuatu": "Oceania",
    "Samoa": "Oceania", "Tonga": "Oceania", "Kiribati": "Oceania",
    "Micronesia": "Oceania", "Marshall Islands": "Oceania", "Palau": "Oceania",
    "Nauru": "Oceania", "Tuvalu": "Oceania", "Cook Islands": "Oceania",
    "Niue": "Oceania", "Tokelau": "Oceania", "Northern Mariana Islands": "Oceania",
    "Guam": "Oceania",
    # Caucasus
    "Armenia": "Central Asia", "Azerbaijan": "Central Asia", "Georgia": "Central Asia",
}


def classify_mortality_tier(rate: float) -> str:
    """Classify child mortality rate into tiers (per 1,000 live births)."""
    if rate < 10:
        return "Very Low"
    elif rate < 25:
        return "Low"
    elif rate < 50:
        return "Moderate"
    elif rate < 100:
        return "High"
    else:
        return "Very High"


def classify_improvement(pct_change: float) -> str:
    """Classify improvement percentage (1950-2016)."""
    if pct_change >= 95:
        return "Near Elimination"
    elif pct_change >= 80:
        return "Dramatic"
    elif pct_change >= 60:
        return "Strong"
    elif pct_change >= 40:
        return "Moderate"
    else:
        return "Limited"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV."""
    logger.info(f"Extracting data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform data into analysis-ready format."""
    logger.info("Transforming data...")

    # Rename columns
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "Child mortality": "mortality_rate"
    })

    # Filter out excluded entities and future projections
    df = df[~df["country"].isin(EXCLUDE_ENTITIES)].copy()
    df = df[df["year"] <= 2016].copy()  # Keep only historical data
    df = df[df["mortality_rate"] > 0].copy()  # Remove zero values

    logger.info(f"After filtering: {len(df)} rows")

    # Add region
    df["region"] = df["country"].map(REGION_MAP).fillna("Other")

    # Add mortality tier (for each year)
    df["mortality_tier"] = df["mortality_rate"].apply(classify_mortality_tier)

    # Calculate improvement for each country (1950-2016)
    df_1950 = df[df["year"] == 1950][["country", "mortality_rate"]].rename(columns={"mortality_rate": "rate_1950"})
    df_2016 = df[df["year"] == 2016][["country", "mortality_rate"]].rename(columns={"mortality_rate": "rate_2016"})

    improvement_df = df_1950.merge(df_2016, on="country", how="inner")
    improvement_df["improvement_pts"] = improvement_df["rate_1950"] - improvement_df["rate_2016"]
    improvement_df["improvement_pct"] = ((improvement_df["rate_1950"] - improvement_df["rate_2016"]) / improvement_df["rate_1950"] * 100).round(1)
    improvement_df["improvement_tier"] = improvement_df["improvement_pct"].apply(classify_improvement)

    # Merge improvement back to main df for 2016 data
    df = df.merge(
        improvement_df[["country", "improvement_pts", "improvement_pct", "improvement_tier"]],
        on="country",
        how="left"
    )

    logger.info(f"Countries: {df['country'].nunique()}")
    logger.info(f"Years: {df['year'].min()} to {df['year'].max()}")

    # Region summary (using 2016 data)
    df_2016_full = df[df["year"] == 2016].copy()
    region_summary = df_2016_full.groupby("region").agg(
        countries=("country", "count"),
        avg_rate=("mortality_rate", "mean"),
        min_rate=("mortality_rate", "min"),
        max_rate=("mortality_rate", "max"),
        avg_improvement_pct=("improvement_pct", "mean")
    ).reset_index()
    region_summary = region_summary.round(1)

    # Year summary (global averages by year) - key milestone years
    milestone_years = [1800, 1850, 1900, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2016]
    year_data = df[df["year"].isin(milestone_years)]
    year_summary = year_data.groupby("year").agg(
        countries=("country", "nunique"),
        avg_rate=("mortality_rate", "mean"),
        min_rate=("mortality_rate", "min"),
        max_rate=("mortality_rate", "max")
    ).reset_index()
    year_summary = year_summary.round(1)

    # Tier summary (2016 data)
    tier_summary = df_2016_full.groupby("mortality_tier").agg(
        countries=("country", "count"),
        avg_rate=("mortality_rate", "mean"),
        avg_improvement_pct=("improvement_pct", "mean")
    ).reset_index()
    tier_summary = tier_summary.round(1)

    return df, region_summary, year_summary, tier_summary


def load(main_df: pd.DataFrame, region_df: pd.DataFrame, year_df: pd.DataFrame,
         tier_df: pd.DataFrame, db_path: Path = None):
    """Load data into database."""
    logger.info("Loading data into database...")

    with ChildMortalityDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, region_df, year_df, tier_df)

        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")

    return stats


def run_child_mortality_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the full ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "child_mortality.csv"

    logger.info("Starting Child Mortality Rates pipeline...")

    # ETL
    raw_df = extract(data_path)
    main_df, region_df, year_df, tier_df = transform(raw_df)
    stats = load(main_df, region_df, year_df, tier_df, db_path)

    logger.info("Pipeline completed successfully!")
    return stats


if __name__ == "__main__":
    stats = run_child_mortality_pipeline()
    print("\nPipeline Results:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
