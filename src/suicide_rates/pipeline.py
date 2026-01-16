"""
ETL Pipeline for Suicide Rates by Sex and Age (IHME, 2019).

Death rates from suicide measured per 100,000 individuals.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import SuicideRatesDatabase


# Region mapping for countries
REGION_MAPPING = {
    # Europe
    "Albania": "Europe", "Andorra": "Europe", "Austria": "Europe", "Belarus": "Europe",
    "Belgium": "Europe", "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Cyprus": "Europe", "Czechia": "Europe", "Denmark": "Europe",
    "Estonia": "Europe", "Finland": "Europe", "France": "Europe", "Germany": "Europe",
    "Greece": "Europe", "Hungary": "Europe", "Iceland": "Europe", "Ireland": "Europe",
    "Italy": "Europe", "Latvia": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe",
    "Malta": "Europe", "Moldova": "Europe", "Monaco": "Europe", "Montenegro": "Europe",
    "Netherlands": "Europe", "North Macedonia": "Europe", "Norway": "Europe",
    "Poland": "Europe", "Portugal": "Europe", "Romania": "Europe", "Russia": "Europe",
    "San Marino": "Europe", "Serbia": "Europe", "Slovakia": "Europe", "Slovenia": "Europe",
    "Spain": "Europe", "Sweden": "Europe", "Switzerland": "Europe", "Ukraine": "Europe",
    "United Kingdom": "Europe",

    # Asia
    "Afghanistan": "Asia", "Armenia": "Asia", "Azerbaijan": "Asia", "Bahrain": "Asia",
    "Bangladesh": "Asia", "Bhutan": "Asia", "Brunei": "Asia", "Cambodia": "Asia",
    "China": "Asia", "Georgia": "Asia", "India": "Asia", "Indonesia": "Asia",
    "Iran": "Asia", "Iraq": "Asia", "Israel": "Asia", "Japan": "Asia", "Jordan": "Asia",
    "Kazakhstan": "Asia", "Kuwait": "Asia", "Kyrgyzstan": "Asia", "Laos": "Asia",
    "Lebanon": "Asia", "Malaysia": "Asia", "Maldives": "Asia", "Mongolia": "Asia",
    "Myanmar": "Asia", "Nepal": "Asia", "North Korea": "Asia", "Oman": "Asia",
    "Pakistan": "Asia", "Palestine": "Asia", "Philippines": "Asia", "Qatar": "Asia",
    "Saudi Arabia": "Asia", "Singapore": "Asia", "South Korea": "Asia", "Sri Lanka": "Asia",
    "Syria": "Asia", "Taiwan": "Asia", "Tajikistan": "Asia", "Thailand": "Asia",
    "Timor": "Asia", "Turkey": "Asia", "Turkmenistan": "Asia", "United Arab Emirates": "Asia",
    "Uzbekistan": "Asia", "Vietnam": "Asia", "Yemen": "Asia",

    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Botswana": "Africa",
    "Burkina Faso": "Africa", "Burundi": "Africa", "Cameroon": "Africa", "Cape Verde": "Africa",
    "Central African Republic": "Africa", "Chad": "Africa", "Comoros": "Africa",
    "Congo": "Africa", "Cote d'Ivoire": "Africa", "Democratic Republic of Congo": "Africa",
    "Djibouti": "Africa", "Egypt": "Africa", "Equatorial Guinea": "Africa", "Eritrea": "Africa",
    "Eswatini": "Africa", "Ethiopia": "Africa", "Gabon": "Africa", "Gambia": "Africa",
    "Ghana": "Africa", "Guinea": "Africa", "Guinea-Bissau": "Africa", "Kenya": "Africa",
    "Lesotho": "Africa", "Liberia": "Africa", "Libya": "Africa", "Madagascar": "Africa",
    "Malawi": "Africa", "Mali": "Africa", "Mauritania": "Africa", "Mauritius": "Africa",
    "Morocco": "Africa", "Mozambique": "Africa", "Namibia": "Africa", "Niger": "Africa",
    "Nigeria": "Africa", "Rwanda": "Africa", "Sao Tome and Principe": "Africa",
    "Senegal": "Africa", "Seychelles": "Africa", "Sierra Leone": "Africa", "Somalia": "Africa",
    "South Africa": "Africa", "South Sudan": "Africa", "Sudan": "Africa", "Tanzania": "Africa",
    "Togo": "Africa", "Tunisia": "Africa", "Uganda": "Africa", "Zambia": "Africa",
    "Zimbabwe": "Africa",

    # North America
    "Antigua and Barbuda": "North America", "Bahamas": "North America",
    "Barbados": "North America", "Belize": "North America", "Canada": "North America",
    "Costa Rica": "North America", "Cuba": "North America", "Dominica": "North America",
    "Dominican Republic": "North America", "El Salvador": "North America",
    "Grenada": "North America", "Guatemala": "North America", "Haiti": "North America",
    "Honduras": "North America", "Jamaica": "North America", "Mexico": "North America",
    "Nicaragua": "North America", "Panama": "North America", "Puerto Rico": "North America",
    "Saint Kitts and Nevis": "North America", "Saint Lucia": "North America",
    "Saint Vincent and the Grenadines": "North America", "Trinidad and Tobago": "North America",
    "United States": "North America", "United States Virgin Islands": "North America",

    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",

    # Oceania
    "Australia": "Oceania", "Fiji": "Oceania", "Kiribati": "Oceania",
    "Marshall Islands": "Oceania", "Micronesia (country)": "Oceania",
    "Nauru": "Oceania", "New Zealand": "Oceania", "Palau": "Oceania",
    "Papua New Guinea": "Oceania", "Samoa": "Oceania", "Solomon Islands": "Oceania",
    "Tonga": "Oceania", "Tuvalu": "Oceania", "Vanuatu": "Oceania",
}

# Aggregate entities to exclude
AGGREGATE_ENTITIES = [
    "World", "Africa", "Asia", "Europe", "Oceania", "Australasia",
    "Central Asia", "Central Europe", "Eastern Europe", "Western Europe",
    "East Asia", "South Asia", "Southeast Asia",
    "Central Sub-Saharan Africa", "Eastern Sub-Saharan Africa",
    "Southern Sub-Saharan Africa", "Western Sub-Saharan Africa", "Sub-Saharan Africa",
    "North America", "Latin America & Caribbean", "Caribbean",
    "Middle East & North Africa", "North Africa and Middle East",
    "East Asia & Pacific", "Europe & Central Asia", "South Asia",
    "High income", "Low income", "Lower-middle income", "Upper-middle income",
    "High-income", "Low-income", "Lower-middle-income", "Upper-middle-income",
    "G20", "OECD", "European Union", "Commonwealth",
    "Andean Latin America", "Central Latin America", "Southern Latin America", "Tropical Latin America",
    "High-income Asia Pacific", "High-income North America",
]


def classify_suicide_rate(rate: float) -> str:
    """Classify suicide rate into risk tiers (per 100,000)."""
    if pd.isna(rate):
        return "No Data"
    if rate >= 20:
        return "Very High (20+)"
    elif rate >= 15:
        return "High (15-20)"
    elif rate >= 10:
        return "Moderate (10-15)"
    elif rate >= 5:
        return "Low (5-10)"
    else:
        return "Very Low (<5)"


def classify_gender_ratio(ratio: float) -> str:
    """Classify male:female suicide ratio."""
    if pd.isna(ratio):
        return "No Data"
    if ratio >= 4:
        return "Extreme (4x+)"
    elif ratio >= 3:
        return "Very High (3-4x)"
    elif ratio >= 2:
        return "High (2-3x)"
    elif ratio >= 1.5:
        return "Moderate (1.5-2x)"
    else:
        return "Low (<1.5x)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger.info(f"Reading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform and enrich the suicide rates data."""
    logger.info("Transforming suicide rates data...")

    # Rename columns for easier access
    df = df.rename(columns={
        "Entity": "entity",
        "Year": "year",
        "Male suicide rate (age-standardized)": "male_rate",
        "Female suicide rate (age-standardized)": "female_rate",
        "Male:female suicide ratio": "gender_ratio",
        "Suicide rate - 15-19 years (Male)": "male_15_19",
        "Suicide rate - 15-19 years (Female)": "female_15_19",
        "Suicide rate - 15-19 years (Both sexes)": "both_15_19",
        "Suicide rate - 20-24 years (Male)": "male_20_24",
        "Suicide rate - 20-24 years (Female)": "female_20_24",
        "Suicide rate - 20-24 years (Both sexes)": "both_20_24",
        "Suicide rate - 25-29 years (Male)": "male_25_29",
        "Suicide rate - 25-29 years (Female)": "female_25_29",
        "Suicide rate - 25-29 years (Both sexes)": "both_25_29",
        "Suicide rate - 30-34 years (Male)": "male_30_34",
        "Suicide rate - 30-34 years (Female)": "female_30_34",
        "Suicide rate - 30-34 years (Both sexes)": "both_30_34",
        "Suicide rate - 35-39 years (Male)": "male_35_39",
        "Suicide rate - 35-39 years (Female)": "female_35_39",
        "Suicide rate - 35-39 years (Both sexes)": "both_35_39",
        "Suicide rate - 40-44 years (Male)": "male_40_44",
        "Suicide rate - 40-44 years (Female)": "female_40_44",
        "Suicide rate - 40-44 years (Both sexes)": "both_40_44",
        "Suicide rate - 45-49 years (Male)": "male_45_49",
        "Suicide rate - 45-49 years (Female)": "female_45_49",
        "Suicide rate - 45-49 years (Both sexes)": "both_45_49",
        "Suicide rate - 50-69 years (Male)": "male_50_69",
        "Suicide rate - 50-69 years (Female)": "female_50_69",
        "Suicide rate - 50-69 years (Both sexes)": "both_50_69",
        "Suicide rate - 70+ years (Male)": "male_70_plus",
        "Suicide rate - 70+ years (Female)": "female_70_plus",
        "Suicide rate - 70+ years (Both sexes)": "both_70_plus",
    })

    # Filter to countries only (exclude aggregates)
    countries_df = df[~df["entity"].isin(AGGREGATE_ENTITIES)].copy()

    # Add region mapping
    countries_df["region"] = countries_df["entity"].map(REGION_MAPPING)
    countries_df["region"] = countries_df["region"].fillna("Other")

    # Add tier classifications
    countries_df["rate_tier"] = countries_df["male_rate"].apply(classify_suicide_rate)
    countries_df["ratio_tier"] = countries_df["gender_ratio"].apply(classify_gender_ratio)

    # Calculate overall rate (average of male and female)
    countries_df["overall_rate"] = (countries_df["male_rate"] + countries_df["female_rate"]) / 2

    logger.info(f"Processed {len(countries_df)} country-year records")

    # Get latest year for each country for summaries
    latest_year = countries_df.groupby("entity")["year"].max().reset_index()
    latest_data = countries_df.merge(latest_year, on=["entity", "year"])

    # Create region summary (using latest data)
    region_summary = latest_data.groupby("region").agg({
        "entity": "count",
        "male_rate": "mean",
        "female_rate": "mean",
        "gender_ratio": "mean",
        "overall_rate": "mean",
    }).reset_index()
    region_summary.columns = [
        "region", "countries", "avg_male_rate", "avg_female_rate",
        "avg_gender_ratio", "avg_overall_rate"
    ]
    logger.info(f"Created summary for {len(region_summary)} regions")

    # Create age group summary (global averages from latest data)
    age_groups = []
    for age_group in ["15_19", "20_24", "25_29", "30_34", "35_39", "40_44", "45_49", "50_69", "70_plus"]:
        male_col = f"male_{age_group}"
        female_col = f"female_{age_group}"
        both_col = f"both_{age_group}"

        age_label = age_group.replace("_", "-").replace("plus", "+")

        age_groups.append({
            "age_group": age_label,
            "male_rate": latest_data[male_col].mean(),
            "female_rate": latest_data[female_col].mean(),
            "both_rate": latest_data[both_col].mean(),
            "gender_ratio": latest_data[male_col].mean() / latest_data[female_col].mean() if latest_data[female_col].mean() > 0 else None,
        })

    age_summary = pd.DataFrame(age_groups)
    logger.info(f"Created summary for {len(age_summary)} age groups")

    # Create rate tier summary
    tier_summary = latest_data.groupby("rate_tier").agg({
        "entity": "count",
        "male_rate": ["mean", "min", "max"],
        "gender_ratio": "mean",
    }).reset_index()
    tier_summary.columns = [
        "rate_tier", "countries", "avg_rate", "min_rate", "max_rate", "avg_ratio"
    ]
    logger.info(f"Created summary for {len(tier_summary)} rate tiers")

    return countries_df, region_summary, age_summary, tier_summary


def load(main_df: pd.DataFrame, region_df: pd.DataFrame,
         age_df: pd.DataFrame, tier_df: pd.DataFrame,
         db_path: Path = None):
    """Load transformed data into DuckDB database."""
    logger.info("Loading data into database...")

    with SuicideRatesDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, region_df, age_df, tier_df)
        stats = db.get_stats()

    logger.info("Data loaded successfully!")
    return stats


def run_suicide_rates_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the complete ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "suicide_rates.csv"

    logger.info("=" * 50)
    logger.info("Starting Suicide Rates ETL Pipeline")
    logger.info("=" * 50)

    # ETL
    raw_df = extract(data_path)
    main_df, region_df, age_df, tier_df = transform(raw_df)
    stats = load(main_df, region_df, age_df, tier_df, db_path)

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Countries: {stats['countries']}")
    logger.info(f"Year range: {stats['year_min']}-{stats['year_max']}")
    logger.info(f"Highest rate: {stats['highest_rate_country']} ({stats['highest_rate']:.1f}/100k)")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    run_suicide_rates_pipeline()
