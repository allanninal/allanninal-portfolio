"""
ETL pipeline for World Bank Poverty and Inequality Platform (PIP).

Comprehensive poverty and inequality data for 177 countries (1967-2021).
Includes poverty headcounts at multiple thresholds, Gini coefficients,
and income distribution metrics.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from .database import PovertyInequalityDatabase

# Region mapping
REGION_MAP = {
    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa", "Benin": "Sub-Saharan Africa", "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa", "Burundi": "Sub-Saharan Africa", "Cabo Verde": "Sub-Saharan Africa",
    "Cameroon": "Sub-Saharan Africa", "Central African Republic": "Sub-Saharan Africa", "Chad": "Sub-Saharan Africa",
    "Comoros": "Sub-Saharan Africa", "Congo, Dem. Rep.": "Sub-Saharan Africa", "Congo, Rep.": "Sub-Saharan Africa",
    "Cote d'Ivoire": "Sub-Saharan Africa", "Djibouti": "Sub-Saharan Africa", "Equatorial Guinea": "Sub-Saharan Africa",
    "Eritrea": "Sub-Saharan Africa", "Eswatini": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Gabon": "Sub-Saharan Africa", "Gambia": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa",
    "Guinea": "Sub-Saharan Africa", "Guinea-Bissau": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa", "Liberia": "Sub-Saharan Africa", "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa", "Mali": "Sub-Saharan Africa", "Mauritania": "Sub-Saharan Africa",
    "Mauritius": "Sub-Saharan Africa", "Mozambique": "Sub-Saharan Africa", "Namibia": "Sub-Saharan Africa",
    "Niger": "Sub-Saharan Africa", "Nigeria": "Sub-Saharan Africa", "Rwanda": "Sub-Saharan Africa",
    "Sao Tome and Principe": "Sub-Saharan Africa", "Senegal": "Sub-Saharan Africa", "Seychelles": "Sub-Saharan Africa",
    "Sierra Leone": "Sub-Saharan Africa", "Somalia": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa",
    "South Sudan": "Sub-Saharan Africa", "Sudan": "Sub-Saharan Africa", "Tanzania": "Sub-Saharan Africa",
    "Togo": "Sub-Saharan Africa", "Uganda": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa",
    # South Asia
    "Afghanistan": "South Asia", "Bangladesh": "South Asia", "Bhutan": "South Asia",
    "India": "South Asia", "Maldives": "South Asia", "Nepal": "South Asia",
    "Pakistan": "South Asia", "Sri Lanka": "South Asia",
    # East Asia & Pacific
    "Cambodia": "East Asia & Pacific", "China": "East Asia & Pacific", "Fiji": "East Asia & Pacific",
    "Indonesia": "East Asia & Pacific", "Kiribati": "East Asia & Pacific", "Lao PDR": "East Asia & Pacific",
    "Malaysia": "East Asia & Pacific", "Marshall Islands": "East Asia & Pacific", "Micronesia, Fed. Sts.": "East Asia & Pacific",
    "Mongolia": "East Asia & Pacific", "Myanmar": "East Asia & Pacific", "Nauru": "East Asia & Pacific",
    "Palau": "East Asia & Pacific", "Papua New Guinea": "East Asia & Pacific", "Philippines": "East Asia & Pacific",
    "Samoa": "East Asia & Pacific", "Solomon Islands": "East Asia & Pacific", "Thailand": "East Asia & Pacific",
    "Timor-Leste": "East Asia & Pacific", "Tonga": "East Asia & Pacific", "Tuvalu": "East Asia & Pacific",
    "Vanuatu": "East Asia & Pacific", "Vietnam": "East Asia & Pacific",
    # Europe & Central Asia
    "Albania": "Europe & Central Asia", "Armenia": "Europe & Central Asia", "Azerbaijan": "Europe & Central Asia",
    "Belarus": "Europe & Central Asia", "Bosnia and Herzegovina": "Europe & Central Asia", "Bulgaria": "Europe & Central Asia",
    "Croatia": "Europe & Central Asia", "Czech Republic": "Europe & Central Asia", "Estonia": "Europe & Central Asia",
    "Georgia": "Europe & Central Asia", "Hungary": "Europe & Central Asia", "Kazakhstan": "Europe & Central Asia",
    "Kosovo": "Europe & Central Asia", "Kyrgyz Republic": "Europe & Central Asia", "Latvia": "Europe & Central Asia",
    "Lithuania": "Europe & Central Asia", "Moldova": "Europe & Central Asia", "Montenegro": "Europe & Central Asia",
    "North Macedonia": "Europe & Central Asia", "Poland": "Europe & Central Asia", "Romania": "Europe & Central Asia",
    "Russian Federation": "Europe & Central Asia", "Serbia": "Europe & Central Asia", "Slovak Republic": "Europe & Central Asia",
    "Slovenia": "Europe & Central Asia", "Tajikistan": "Europe & Central Asia", "Turkey": "Europe & Central Asia",
    "Turkmenistan": "Europe & Central Asia", "Ukraine": "Europe & Central Asia", "Uzbekistan": "Europe & Central Asia",
    # Latin America & Caribbean
    "Argentina": "Latin America & Caribbean", "Belize": "Latin America & Caribbean", "Bolivia": "Latin America & Caribbean",
    "Brazil": "Latin America & Caribbean", "Chile": "Latin America & Caribbean", "Colombia": "Latin America & Caribbean",
    "Costa Rica": "Latin America & Caribbean", "Dominican Republic": "Latin America & Caribbean", "Ecuador": "Latin America & Caribbean",
    "El Salvador": "Latin America & Caribbean", "Guatemala": "Latin America & Caribbean", "Guyana": "Latin America & Caribbean",
    "Haiti": "Latin America & Caribbean", "Honduras": "Latin America & Caribbean", "Jamaica": "Latin America & Caribbean",
    "Mexico": "Latin America & Caribbean", "Nicaragua": "Latin America & Caribbean", "Panama": "Latin America & Caribbean",
    "Paraguay": "Latin America & Caribbean", "Peru": "Latin America & Caribbean", "St. Lucia": "Latin America & Caribbean",
    "Suriname": "Latin America & Caribbean", "Trinidad and Tobago": "Latin America & Caribbean", "Uruguay": "Latin America & Caribbean",
    "Venezuela": "Latin America & Caribbean",
    # Middle East & North Africa
    "Algeria": "Middle East & North Africa", "Egypt": "Middle East & North Africa", "Iran": "Middle East & North Africa",
    "Iraq": "Middle East & North Africa", "Jordan": "Middle East & North Africa", "Lebanon": "Middle East & North Africa",
    "Libya": "Middle East & North Africa", "Morocco": "Middle East & North Africa", "Syria": "Middle East & North Africa",
    "Tunisia": "Middle East & North Africa", "West Bank and Gaza": "Middle East & North Africa", "Yemen": "Middle East & North Africa",
    # High Income
    "Australia": "High Income", "Austria": "High Income", "Belgium": "High Income",
    "Canada": "High Income", "Cyprus": "High Income", "Denmark": "High Income",
    "Finland": "High Income", "France": "High Income", "Germany": "High Income",
    "Greece": "High Income", "Iceland": "High Income", "Ireland": "High Income",
    "Israel": "High Income", "Italy": "High Income", "Japan": "High Income",
    "Korea, Rep.": "High Income", "Luxembourg": "High Income", "Malta": "High Income",
    "Netherlands": "High Income", "New Zealand": "High Income", "Norway": "High Income",
    "Portugal": "High Income", "Singapore": "High Income", "Spain": "High Income",
    "Sweden": "High Income", "Switzerland": "High Income", "Taiwan": "High Income",
    "United Kingdom": "High Income", "United States": "High Income",
}


def classify_poverty_tier(extreme_poverty_rate: float) -> str:
    """Classify country by extreme poverty rate ($2.15/day)."""
    if pd.isna(extreme_poverty_rate):
        return "Unknown"
    if extreme_poverty_rate < 1:
        return "Very Low (<1%)"
    elif extreme_poverty_rate < 5:
        return "Low (1-5%)"
    elif extreme_poverty_rate < 20:
        return "Moderate (5-20%)"
    elif extreme_poverty_rate < 40:
        return "High (20-40%)"
    else:
        return "Extreme (40%+)"


def classify_inequality_tier(gini: float) -> str:
    """Classify country by Gini coefficient."""
    if pd.isna(gini):
        return "Unknown"
    if gini < 0.30:
        return "Low (<0.30)"
    elif gini < 0.35:
        return "Moderate (0.30-0.35)"
    elif gini < 0.40:
        return "High (0.35-0.40)"
    elif gini < 0.50:
        return "Very High (0.40-0.50)"
    else:
        return "Extreme (0.50+)"


def extract(data_path: Path) -> pd.DataFrame:
    """Extract data from CSV."""
    logger.info(f"Extracting data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Extracted {len(df)} rows, {df['country'].nunique()} countries")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Transform data into analysis-ready format."""
    logger.info("Transforming data...")

    # Select and rename key columns
    df = df.rename(columns={
        "headcount_ratio_international_povline": "extreme_poverty_rate",  # $2.15/day
        "headcount_ratio_lower_mid_income_povline": "lower_mid_poverty_rate",  # $3.65/day
        "headcount_ratio_upper_mid_income_povline": "upper_mid_poverty_rate",  # $6.85/day
        "poverty_gap_index_international_povline": "poverty_gap_index",
        "headcount_international_povline": "extreme_poverty_count",
        "headcount_lower_mid_income_povline": "lower_mid_poverty_count",
        "headcount_upper_mid_income_povline": "upper_mid_poverty_count",
    })

    # Add region
    df["region"] = df["country"].map(REGION_MAP).fillna("Other")

    # Add tiers
    df["poverty_tier"] = df["extreme_poverty_rate"].apply(classify_poverty_tier)
    df["inequality_tier"] = df["gini"].apply(classify_inequality_tier)

    # Calculate income ratio (P90/P10) if not present
    if "p90_p10_ratio" not in df.columns:
        df["p90_p10_ratio"] = None

    # Select key columns for main table
    key_cols = [
        "country", "year", "region", "reporting_level", "welfare_type",
        "extreme_poverty_rate", "lower_mid_poverty_rate", "upper_mid_poverty_rate",
        "poverty_gap_index", "gini", "mean", "median",
        "extreme_poverty_count", "lower_mid_poverty_count", "upper_mid_poverty_count",
        "poverty_tier", "inequality_tier",
        "decile1_share", "decile10_share", "palma_ratio", "p90_p10_ratio"
    ]

    # Only include columns that exist
    available_cols = [c for c in key_cols if c in df.columns]
    main_df = df[available_cols].copy()

    logger.info(f"Years: {main_df['year'].min()} to {main_df['year'].max()}")
    logger.info(f"Countries: {main_df['country'].nunique()}")

    # Get latest year data for each country
    latest_df = main_df.loc[main_df.groupby('country')['year'].idxmax()].copy()
    latest_df = latest_df.sort_values('extreme_poverty_rate', ascending=False)

    # Region summary (using latest data)
    region_summary = latest_df.groupby('region').agg(
        countries=('country', 'count'),
        avg_extreme_poverty=('extreme_poverty_rate', 'mean'),
        avg_lower_mid_poverty=('lower_mid_poverty_rate', 'mean'),
        avg_gini=('gini', 'mean'),
        avg_mean_income=('mean', 'mean'),
        total_extreme_poor=('extreme_poverty_count', 'sum')
    ).reset_index()
    region_summary = region_summary.round(3)

    # Poverty tier summary
    poverty_tier_summary = latest_df.groupby('poverty_tier').agg(
        countries=('country', 'count'),
        avg_extreme_poverty=('extreme_poverty_rate', 'mean'),
        avg_gini=('gini', 'mean')
    ).reset_index()
    poverty_tier_summary = poverty_tier_summary.round(3)

    return main_df, latest_df, region_summary, poverty_tier_summary


def load(main_df: pd.DataFrame, latest_df: pd.DataFrame,
         region_df: pd.DataFrame, tier_df: pd.DataFrame,
         db_path: Path = None):
    """Load data into database."""
    logger.info("Loading data into database...")

    with PovertyInequalityDatabase(db_path) as db:
        db.create_schema()
        db.load_data(main_df, latest_df, region_df, tier_df)

        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")

    return stats


def run_poverty_inequality_pipeline(
    data_path: Path = None,
    db_path: Path = None
) -> dict:
    """Run the full ETL pipeline."""
    if data_path is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "poverty_inequality_pip.csv"

    logger.info("Starting Poverty and Inequality Platform pipeline...")

    # ETL
    raw_df = extract(data_path)
    main_df, latest_df, region_df, tier_df = transform(raw_df)
    stats = load(main_df, latest_df, region_df, tier_df, db_path)

    logger.info("Pipeline completed successfully!")
    return stats


if __name__ == "__main__":
    stats = run_poverty_inequality_pipeline()
    print("\nPipeline Results:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
