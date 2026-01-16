"""
DuckDB database for Natural Disasters data from EM-DAT.

Uses the BaseDatabase class for common functionality.
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any

from src.shared.base_database import BaseDatabase
from src.shared.mappings import REGION_MAPPING_FULL


# Disaster types in the dataset
DISASTER_TYPES = [
    "drought", "earthquake", "flood", "volcanic", "storm",
    "landslide", "fog", "wildfire", "temperature", "glacial_lake", "mass_movement"
]

# Use centralized region mapping
REGION_MAPPING = REGION_MAPPING_FULL


class NaturalDisastersDatabase(BaseDatabase):
    """Database manager for Natural Disasters data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "natural_disasters.duckdb"
    CSV_PATH = Path(__file__).parent.parent.parent / "Natural disasters (EMDAT).csv"
    PROJECT_NAME = "Natural Disasters"

    # Inherited from BaseDatabase: __init__, connect, close, __enter__, __exit__, query

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating Natural Disasters database schema...")

        # Main raw data table (wide format)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS disasters_raw (
                entity VARCHAR,
                year INTEGER,
                region VARCHAR,
                -- All disasters aggregate
                deaths_all BIGINT,
                injured_all BIGINT,
                affected_all BIGINT,
                homeless_all BIGINT,
                total_affected_all BIGINT,
                total_damages_all DOUBLE,
                -- Drought
                deaths_drought BIGINT,
                total_affected_drought BIGINT,
                total_damages_drought DOUBLE,
                -- Earthquake
                deaths_earthquake BIGINT,
                total_affected_earthquake BIGINT,
                total_damages_earthquake DOUBLE,
                -- Flood
                deaths_flood BIGINT,
                total_affected_flood BIGINT,
                total_damages_flood DOUBLE,
                -- Storm
                deaths_storm BIGINT,
                total_affected_storm BIGINT,
                total_damages_storm DOUBLE,
                -- Temperature (extreme heat/cold)
                deaths_temperature BIGINT,
                total_affected_temperature BIGINT,
                total_damages_temperature DOUBLE,
                -- Volcanic
                deaths_volcanic BIGINT,
                total_affected_volcanic BIGINT,
                total_damages_volcanic DOUBLE,
                -- Landslide
                deaths_landslide BIGINT,
                total_affected_landslide BIGINT,
                total_damages_landslide DOUBLE,
                -- Wildfire
                deaths_wildfire BIGINT,
                total_affected_wildfire BIGINT,
                total_damages_wildfire DOUBLE,
                -- Mass movement (dry)
                deaths_mass_movement BIGINT,
                total_affected_mass_movement BIGINT,
                total_damages_mass_movement DOUBLE,
                -- Per 100k rates
                deaths_rate_per_100k_all DOUBLE,
                total_affected_rate_per_100k_all DOUBLE,
                -- GDP percentages
                total_damages_pct_gdp_all DOUBLE
            )
        """)

        # Year summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                total_deaths BIGINT,
                total_affected BIGINT,
                total_damages_billion DOUBLE,
                deaths_drought BIGINT,
                deaths_earthquake BIGINT,
                deaths_flood BIGINT,
                deaths_storm BIGINT,
                deaths_temperature BIGINT,
                deaths_volcanic BIGINT,
                deaths_landslide BIGINT,
                deaths_wildfire BIGINT,
                disaster_events INTEGER
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                region VARCHAR,
                total_deaths BIGINT,
                total_affected BIGINT,
                total_damages_billion DOUBLE,
                years_with_data INTEGER,
                deadliest_year INTEGER,
                deadliest_year_deaths BIGINT,
                primary_disaster_type VARCHAR
            )
        """)

        # Disaster type summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS disaster_type_summary (
                disaster_type VARCHAR,
                total_deaths BIGINT,
                total_affected BIGINT,
                total_damages_billion DOUBLE,
                death_pct DOUBLE,
                countries_affected INTEGER
            )
        """)

        # Decade summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decade_summary (
                decade INTEGER,
                total_deaths BIGINT,
                total_affected BIGINT,
                total_damages_billion DOUBLE,
                deaths_drought BIGINT,
                deaths_earthquake BIGINT,
                deaths_flood BIGINT,
                deaths_storm BIGINT,
                avg_deaths_per_year DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_from_csv(self):
        """Load data from CSV file and populate database."""
        logger.info(f"Loading data from {self.CSV_PATH}")

        # Read CSV
        df = pd.read_csv(self.CSV_PATH)

        # Add region mapping
        df['region'] = df['Entity'].map(REGION_MAPPING).fillna('Other')

        # Clean column names and select key columns
        clean_df = pd.DataFrame({
            'entity': df['Entity'],
            'year': df['Year'],
            'region': df['region'],
            'deaths_all': pd.to_numeric(df['deaths_all_disasters'], errors='coerce').fillna(0).astype(int),
            'injured_all': pd.to_numeric(df['injured_all_disasters'], errors='coerce').fillna(0).astype(int),
            'affected_all': pd.to_numeric(df['affected_all_disasters'], errors='coerce').fillna(0).astype(int),
            'homeless_all': pd.to_numeric(df['homeless_all_disasters'], errors='coerce').fillna(0).astype(int),
            'total_affected_all': pd.to_numeric(df['total_affected_all_disasters'], errors='coerce').fillna(0).astype(int),
            'total_damages_all': pd.to_numeric(df['total_damages_all_disasters'], errors='coerce').fillna(0),
            'deaths_drought': pd.to_numeric(df['deaths_drought'], errors='coerce').fillna(0).astype(int),
            'total_affected_drought': pd.to_numeric(df['total_affected_drought'], errors='coerce').fillna(0).astype(int),
            'total_damages_drought': pd.to_numeric(df['total_damages_drought'], errors='coerce').fillna(0),
            'deaths_earthquake': pd.to_numeric(df['deaths_earthquake'], errors='coerce').fillna(0).astype(int),
            'total_affected_earthquake': pd.to_numeric(df['total_affected_earthquake'], errors='coerce').fillna(0).astype(int),
            'total_damages_earthquake': pd.to_numeric(df['total_damages_earthquake'], errors='coerce').fillna(0),
            'deaths_flood': pd.to_numeric(df['deaths_flood'], errors='coerce').fillna(0).astype(int),
            'total_affected_flood': pd.to_numeric(df['total_affected_flood'], errors='coerce').fillna(0).astype(int),
            'total_damages_flood': pd.to_numeric(df['total_damages_flood'], errors='coerce').fillna(0),
            'deaths_storm': pd.to_numeric(df['deaths_storm'], errors='coerce').fillna(0).astype(int),
            'total_affected_storm': pd.to_numeric(df['total_affected_storm'], errors='coerce').fillna(0).astype(int),
            'total_damages_storm': pd.to_numeric(df['total_damages_storm'], errors='coerce').fillna(0),
            'deaths_temperature': pd.to_numeric(df['deaths_temperature'], errors='coerce').fillna(0).astype(int),
            'total_affected_temperature': pd.to_numeric(df['total_affected_temperature'], errors='coerce').fillna(0).astype(int),
            'total_damages_temperature': pd.to_numeric(df['total_damages_temperature'], errors='coerce').fillna(0),
            'deaths_volcanic': pd.to_numeric(df['deaths_volcanic'], errors='coerce').fillna(0).astype(int),
            'total_affected_volcanic': pd.to_numeric(df['total_affected_volcanic'], errors='coerce').fillna(0).astype(int),
            'total_damages_volcanic': pd.to_numeric(df['total_damages_volcanic'], errors='coerce').fillna(0),
            'deaths_landslide': pd.to_numeric(df['deaths_landslide'], errors='coerce').fillna(0).astype(int),
            'total_affected_landslide': pd.to_numeric(df['total_affected_landslide'], errors='coerce').fillna(0).astype(int),
            'total_damages_landslide': pd.to_numeric(df['total_damages_landslide'], errors='coerce').fillna(0),
            'deaths_wildfire': pd.to_numeric(df['deaths_wildfire'], errors='coerce').fillna(0).astype(int),
            'total_affected_wildfire': pd.to_numeric(df['total_affected_wildfire'], errors='coerce').fillna(0).astype(int),
            'total_damages_wildfire': pd.to_numeric(df['total_damages_wildfire'], errors='coerce').fillna(0),
            'deaths_mass_movement': pd.to_numeric(df['deaths_mass_movement'], errors='coerce').fillna(0).astype(int),
            'total_affected_mass_movement': pd.to_numeric(df['total_affected_mass_movement'], errors='coerce').fillna(0).astype(int),
            'total_damages_mass_movement': pd.to_numeric(df['total_damages_mass_movement'], errors='coerce').fillna(0),
            'deaths_rate_per_100k_all': pd.to_numeric(df['deaths_rate_per_100k_all_disasters'], errors='coerce'),
            'total_affected_rate_per_100k_all': pd.to_numeric(df['total_affected_rate_per_100k_all_disasters'], errors='coerce'),
            'total_damages_pct_gdp_all': pd.to_numeric(df['total_damages_pct_gdp_all_disasters'], errors='coerce'),
        })

        # Filter out aggregate entities like "World"
        clean_df = clean_df[~clean_df['entity'].isin(['World', 'High income', 'Low income', 'Middle income',
                                                       'Upper middle income', 'Lower middle income'])]

        # Load main table
        self.conn.execute("DELETE FROM disasters_raw")
        self.conn.execute("INSERT INTO disasters_raw SELECT * FROM clean_df")
        logger.info(f"Loaded {len(clean_df)} rows into disasters_raw")

        # Create year summary
        self.conn.execute("DELETE FROM year_summary")
        self.conn.execute("""
            INSERT INTO year_summary
            SELECT
                year,
                SUM(deaths_all) as total_deaths,
                SUM(total_affected_all) as total_affected,
                SUM(total_damages_all) / 1000000000.0 as total_damages_billion,
                SUM(deaths_drought) as deaths_drought,
                SUM(deaths_earthquake) as deaths_earthquake,
                SUM(deaths_flood) as deaths_flood,
                SUM(deaths_storm) as deaths_storm,
                SUM(deaths_temperature) as deaths_temperature,
                SUM(deaths_volcanic) as deaths_volcanic,
                SUM(deaths_landslide) as deaths_landslide,
                SUM(deaths_wildfire) as deaths_wildfire,
                COUNT(DISTINCT entity) as disaster_events
            FROM disasters_raw
            WHERE deaths_all > 0 OR total_affected_all > 0
            GROUP BY year
            ORDER BY year
        """)

        # Create country summary with primary disaster type
        self.conn.execute("DELETE FROM country_summary")
        self.conn.execute("""
            INSERT INTO country_summary
            WITH country_totals AS (
                SELECT
                    entity,
                    region,
                    SUM(deaths_all) as total_deaths,
                    SUM(total_affected_all) as total_affected,
                    SUM(total_damages_all) / 1000000000.0 as total_damages_billion,
                    COUNT(DISTINCT year) as years_with_data,
                    SUM(deaths_drought) as d_drought,
                    SUM(deaths_earthquake) as d_earthquake,
                    SUM(deaths_flood) as d_flood,
                    SUM(deaths_storm) as d_storm,
                    SUM(deaths_temperature) as d_temperature,
                    SUM(deaths_volcanic) as d_volcanic
                FROM disasters_raw
                GROUP BY entity, region
            ),
            deadliest AS (
                SELECT
                    entity,
                    year as deadliest_year,
                    deaths_all as deadliest_year_deaths,
                    ROW_NUMBER() OVER (PARTITION BY entity ORDER BY deaths_all DESC) as rn
                FROM disasters_raw
            )
            SELECT
                ct.entity,
                ct.region,
                ct.total_deaths,
                ct.total_affected,
                ct.total_damages_billion,
                ct.years_with_data,
                d.deadliest_year,
                d.deadliest_year_deaths,
                CASE
                    WHEN ct.d_drought >= GREATEST(ct.d_earthquake, ct.d_flood, ct.d_storm, ct.d_temperature, ct.d_volcanic) THEN 'Drought'
                    WHEN ct.d_earthquake >= GREATEST(ct.d_drought, ct.d_flood, ct.d_storm, ct.d_temperature, ct.d_volcanic) THEN 'Earthquake'
                    WHEN ct.d_flood >= GREATEST(ct.d_drought, ct.d_earthquake, ct.d_storm, ct.d_temperature, ct.d_volcanic) THEN 'Flood'
                    WHEN ct.d_storm >= GREATEST(ct.d_drought, ct.d_earthquake, ct.d_flood, ct.d_temperature, ct.d_volcanic) THEN 'Storm'
                    WHEN ct.d_temperature >= GREATEST(ct.d_drought, ct.d_earthquake, ct.d_flood, ct.d_storm, ct.d_volcanic) THEN 'Temperature'
                    ELSE 'Volcanic'
                END as primary_disaster_type
            FROM country_totals ct
            LEFT JOIN deadliest d ON ct.entity = d.entity AND d.rn = 1
            WHERE ct.total_deaths > 0 OR ct.total_affected > 0
            ORDER BY ct.total_deaths DESC
        """)

        # Create disaster type summary
        self.conn.execute("DELETE FROM disaster_type_summary")
        total_deaths = self.conn.execute("SELECT SUM(deaths_all) FROM disasters_raw").fetchone()[0]

        disaster_types_data = [
            ("Drought", "deaths_drought", "total_affected_drought", "total_damages_drought"),
            ("Earthquake", "deaths_earthquake", "total_affected_earthquake", "total_damages_earthquake"),
            ("Flood", "deaths_flood", "total_affected_flood", "total_damages_flood"),
            ("Storm", "deaths_storm", "total_affected_storm", "total_damages_storm"),
            ("Temperature", "deaths_temperature", "total_affected_temperature", "total_damages_temperature"),
            ("Volcanic", "deaths_volcanic", "total_affected_volcanic", "total_damages_volcanic"),
            ("Landslide", "deaths_landslide", "total_affected_landslide", "total_damages_landslide"),
            ("Wildfire", "deaths_wildfire", "total_affected_wildfire", "total_damages_wildfire"),
            ("Mass Movement", "deaths_mass_movement", "total_affected_mass_movement", "total_damages_mass_movement"),
        ]

        for dtype, deaths_col, affected_col, damages_col in disaster_types_data:
            self.conn.execute(f"""
                INSERT INTO disaster_type_summary
                SELECT
                    '{dtype}' as disaster_type,
                    SUM({deaths_col}) as total_deaths,
                    SUM({affected_col}) as total_affected,
                    SUM({damages_col}) / 1000000000.0 as total_damages_billion,
                    CASE WHEN {total_deaths} > 0 THEN SUM({deaths_col}) * 100.0 / {total_deaths} ELSE 0 END as death_pct,
                    COUNT(DISTINCT CASE WHEN {deaths_col} > 0 OR {affected_col} > 0 THEN entity END) as countries_affected
                FROM disasters_raw
            """)

        # Create decade summary
        self.conn.execute("DELETE FROM decade_summary")
        self.conn.execute("""
            INSERT INTO decade_summary
            SELECT
                (year / 10) * 10 as decade,
                SUM(deaths_all) as total_deaths,
                SUM(total_affected_all) as total_affected,
                SUM(total_damages_all) / 1000000000.0 as total_damages_billion,
                SUM(deaths_drought) as deaths_drought,
                SUM(deaths_earthquake) as deaths_earthquake,
                SUM(deaths_flood) as deaths_flood,
                SUM(deaths_storm) as deaths_storm,
                SUM(deaths_all) / 10.0 as avg_deaths_per_year
            FROM disasters_raw
            GROUP BY (year / 10) * 10
            ORDER BY decade
        """)

        logger.info("All summary tables populated")

    # query() is inherited from BaseDatabase

    def get_full_data(self) -> pd.DataFrame:
        """Get all disaster data (required by BaseDatabase)."""
        return self.query("SELECT * FROM disasters_raw ORDER BY entity, year")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year-by-year summary."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM country_summary ORDER BY total_deaths DESC")

    def get_disaster_type_summary(self) -> pd.DataFrame:
        """Get summary by disaster type."""
        return self.query("SELECT * FROM disaster_type_summary ORDER BY total_deaths DESC")

    def get_decade_summary(self) -> pd.DataFrame:
        """Get decade summary."""
        return self.query("SELECT * FROM decade_summary ORDER BY decade")

    def get_top_deadliest_years(self, limit: int = 20) -> pd.DataFrame:
        """Get deadliest years."""
        return self.query(f"""
            SELECT * FROM year_summary
            WHERE total_deaths > 0
            ORDER BY total_deaths DESC
            LIMIT {limit}
        """)

    def get_top_affected_countries(self, limit: int = 30) -> pd.DataFrame:
        """Get most affected countries."""
        return self.query(f"""
            SELECT entity, region, total_deaths, total_affected, total_damages_billion,
                   primary_disaster_type, deadliest_year, deadliest_year_deaths
            FROM country_summary
            ORDER BY total_deaths DESC
            LIMIT {limit}
        """)

    def get_country_history(self, country: str) -> pd.DataFrame:
        """Get disaster history for a specific country."""
        return self.query(f"""
            SELECT year, deaths_all, total_affected_all, total_damages_all / 1000000.0 as damages_million,
                   deaths_drought, deaths_earthquake, deaths_flood, deaths_storm,
                   deaths_temperature, deaths_volcanic, deaths_landslide, deaths_wildfire
            FROM disasters_raw
            WHERE entity = '{country}'
            AND (deaths_all > 0 OR total_affected_all > 0)
            ORDER BY year
        """)

    def get_regional_summary(self) -> pd.DataFrame:
        """Get regional aggregation."""
        return self.query("""
            SELECT
                region,
                SUM(deaths_all) as total_deaths,
                SUM(total_affected_all) as total_affected,
                SUM(total_damages_all) / 1000000000.0 as total_damages_billion,
                COUNT(DISTINCT entity) as countries,
                SUM(deaths_drought) as deaths_drought,
                SUM(deaths_earthquake) as deaths_earthquake,
                SUM(deaths_flood) as deaths_flood,
                SUM(deaths_storm) as deaths_storm
            FROM disasters_raw
            GROUP BY region
            ORDER BY total_deaths DESC
        """)

    def get_disaster_trends(self, disaster_type: str = 'all') -> pd.DataFrame:
        """Get trends for specific disaster type or all disasters."""
        if disaster_type == 'all':
            return self.query("""
                SELECT year,
                       SUM(deaths_all) as deaths,
                       SUM(total_affected_all) as affected
                FROM disasters_raw
                GROUP BY year
                ORDER BY year
            """)
        else:
            deaths_col = f"deaths_{disaster_type}"
            affected_col = f"total_affected_{disaster_type}"
            return self.query(f"""
                SELECT year,
                       SUM({deaths_col}) as deaths,
                       SUM({affected_col}) as affected
                FROM disasters_raw
                GROUP BY year
                ORDER BY year
            """)

    def get_major_disasters(self, min_deaths: int = 10000) -> pd.DataFrame:
        """Get major disaster events with high death tolls."""
        return self.query(f"""
            SELECT entity, year, deaths_all, total_affected_all, region,
                   deaths_drought, deaths_earthquake, deaths_flood, deaths_storm,
                   deaths_temperature, deaths_volcanic
            FROM disasters_raw
            WHERE deaths_all >= {min_deaths}
            ORDER BY deaths_all DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {}
        stats["total_records"] = self.conn.execute("SELECT COUNT(*) FROM disasters_raw").fetchone()[0]
        stats["total_countries"] = self.conn.execute("SELECT COUNT(DISTINCT entity) FROM disasters_raw").fetchone()[0]
        year_range = self.conn.execute("SELECT MIN(year), MAX(year) FROM disasters_raw").fetchone()
        stats["year_range"] = (year_range[0], year_range[1])
        stats["total_deaths"] = self.conn.execute("SELECT SUM(deaths_all) FROM disasters_raw").fetchone()[0]
        stats["total_affected"] = self.conn.execute("SELECT SUM(total_affected_all) FROM disasters_raw").fetchone()[0]
        return stats


def init_database():
    """Initialize the database with data from CSV."""
    with NaturalDisastersDatabase() as db:
        db.create_schema()
        db.load_from_csv()
        print("Stats:", db.get_stats())


if __name__ == "__main__":
    init_database()
