"""
ETL pipeline for Healthcare Access and Quality Index (IHME 2017).

Data source: Institute for Health Metrics and Evaluation
HAQ Index measures healthcare access and quality on a 0-100 scale.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import HealthcareQualityDatabase

# Regional aggregates to exclude (keep only countries)
AGGREGATE_ENTITIES = {
    "Andean Latin America",
    "Australasia",
    "Caribbean",
    "Central Asia",
    "Central Europe",
    "Central Latin America",
    "Central Sub-Saharan Africa",
    "East Asia",
    "Eastern Europe",
    "Eastern Sub-Saharan Africa",
    "High-income",
    "High-income Asia Pacific",
    "High-income North America",
    "Latin America and Caribbean",
    "North Africa and Middle East",
    "Oceania",
    "South Asia",
    "Southeast Asia",
    "Southern Latin America",
    "Southern Sub-Saharan Africa",
    "Sub-Saharan Africa",
    "Tropical Latin America",
    "Western Europe",
    "Western Sub-Saharan Africa",
    "World",
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
    "Macedonia": "Europe", "Malta": "Europe", "Moldova": "Europe", "Montenegro": "Europe",
    "Netherlands": "Europe", "Norway": "Europe", "Poland": "Europe", "Portugal": "Europe",
    "Romania": "Europe", "Russia": "Europe", "Serbia": "Europe", "Slovakia": "Europe",
    "Slovenia": "Europe", "Spain": "Europe", "Sweden": "Europe", "Switzerland": "Europe",
    "Ukraine": "Europe", "United Kingdom": "Europe",
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
    "Trinidad and Tobago": "Central America & Caribbean", "The Bahamas": "Central America & Caribbean",
    "Barbados": "Central America & Caribbean", "Antigua and Barbuda": "Central America & Caribbean",
    "Dominica": "Central America & Caribbean", "Grenada": "Central America & Caribbean",
    "Saint Lucia": "Central America & Caribbean", "Saint Vincent and the Grenadines": "Central America & Caribbean",
    "United States Virgin Islands": "Central America & Caribbean",
    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",
    # East Asia
    "China": "East Asia", "Japan": "East Asia", "South Korea": "East Asia",
    "North Korea": "East Asia", "Mongolia": "East Asia", "Taiwan": "East Asia",
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
    "Micronesia (country)": "Oceania", "Marshall Islands": "Oceania",
    "American Samoa": "Oceania", "Guam": "Oceania", "Northern Mariana Islands": "Oceania",
    # Other
    "Armenia": "Central Asia", "Azerbaijan": "Central Asia", "Georgia": "Central Asia",
}


def classify_haq_tier(haq_index: float) -> str:
    """Classify HAQ index into tiers."""
    if haq_index >= 90:
        return "Very High"
    elif haq_index >= 70:
        return "High"
    elif haq_index >= 50:
        return "Moderate"
    elif haq_index >= 30:
        return "Low"
    else:
        return "Very Low"


def classify_improvement(change: float) -> str:
    """Classify improvement over 25 years (1990-2015)."""
    if change >= 25:
        return "Dramatic"
    elif change >= 15:
        return "Strong"
    elif change >= 10:
        return "Moderate"
    elif change >= 5:
        return "Modest"
    else:
        return "Minimal"


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
        "HAQ Index (IHME (2017))": "haq_index"
    })

    # Filter out aggregates
    df = df[~df["country"].isin(AGGREGATE_ENTITIES)].copy()
    logger.info(f"After filtering aggregates: {len(df)} rows")

    # Add region
    df["region"] = df["country"].map(REGION_MAP).fillna("Other")

    # Add HAQ tier
    df["haq_tier"] = df["haq_index"].apply(classify_haq_tier)

    # Calculate improvement for each country (2015 vs 1990)
    df_1990 = df[df["year"] == 1990][["country", "haq_index"]].rename(columns={"haq_index": "haq_1990"})
    df_2015 = df[df["year"] == 2015][["country", "haq_index"]].rename(columns={"haq_index": "haq_2015"})

    improvement_df = df_1990.merge(df_2015, on="country")
    improvement_df["improvement"] = improvement_df["haq_2015"] - improvement_df["haq_1990"]
    improvement_df["improvement_pct"] = (improvement_df["improvement"] / improvement_df["haq_1990"] * 100).round(1)
    improvement_df["improvement_tier"] = improvement_df["improvement"].apply(classify_improvement)

    # Add improvement to main df
    df = df.merge(improvement_df[["country", "improvement", "improvement_pct", "improvement_tier"]], on="country", how="left")

    logger.info(f"Countries: {df['country'].nunique()}")
    logger.info(f"Years: {sorted(df['year'].unique())}")

    # Region summary (using 2015 data)
    df_2015_full = df[df["year"] == 2015].copy()
    region_summary = df_2015_full.groupby("region").agg(
        countries=("country", "count"),
        avg_haq=("haq_index", "mean"),
        min_haq=("haq_index", "min"),
        max_haq=("haq_index", "max"),
        avg_improvement=("improvement", "mean")
    ).reset_index()
    region_summary = region_summary.round(1)

    # Year summary (global averages by year)
    year_summary = df.groupby("year").agg(
        countries=("country", "nunique"),
        avg_haq=("haq_index", "mean"),
        min_haq=("haq_index", "min"),
        max_haq=("haq_index", "max")
    ).reset_index()
    year_summary = year_summary.round(1)

    # Tier summary (2015 data)
    tier_summary = df_2015_full.groupby("haq_tier").agg(
        countries=("country", "count"),
        avg_haq=("haq_index", "mean"),
        avg_improvement=("improvement", "mean")
    ).reset_index()
    tier_summary = tier_summary.round(1)

    return df, region_summary, year_summary, tier_summary


def load(main_df: pd.DataFrame, region_df: pd.DataFrame, year_df: pd.DataFrame,
         tier_df: pd.DataFrame, db_path: Path = None):
    """Load data into database."""
    logger.info("Loading data into database...")

    with HealthcareQualityDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, region_df, year_df, tier_df)

        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")

    return stats


def run_healthcare_quality_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the full ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "healthcare_quality.csv"

    logger.info("Starting Healthcare Access and Quality Index pipeline...")

    # ETL
    raw_df = extract(data_path)
    main_df, region_df, year_df, tier_df = transform(raw_df)
    stats = load(main_df, region_df, year_df, tier_df, db_path)

    logger.info("Pipeline completed successfully!")
    return stats


if __name__ == "__main__":
    stats = run_healthcare_quality_pipeline()
    print("\nPipeline Results:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
