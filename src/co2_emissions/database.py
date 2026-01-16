"""
DuckDB database for CO2 Emissions by Sector data (CAIT, 2020).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class CO2EmissionsDatabase(BaseDatabase):
    """Database manager for CO2 emissions data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "co2_emissions.duckdb"
    PROJECT_NAME = "CO2 Emissions by Sector"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating CO2 emissions database schema...")

        # Full time series data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS co2_emissions (
                entity VARCHAR,
                year INTEGER,
                building DOUBLE,
                aviation_shipping DOUBLE,
                electricity_heat DOUBLE,
                energy DOUBLE,
                fugitive DOUBLE,
                industry DOUBLE,
                land_use DOUBLE,
                manufacturing DOUBLE,
                other_fuel DOUBLE,
                total_excl_lucf DOUBLE,
                total_incl_lucf DOUBLE,
                transport DOUBLE,
                building_pc DOUBLE,
                electricity_heat_pc DOUBLE,
                fugitive_pc DOUBLE,
                industry_pc DOUBLE,
                aviation_shipping_pc DOUBLE,
                land_use_pc DOUBLE,
                manufacturing_pc DOUBLE,
                total_excl_lucf_pc DOUBLE,
                total_incl_lucf_pc DOUBLE,
                transport_pc DOUBLE,
                region VARCHAR,
                per_capita_tier VARCHAR
            )
        """)

        # Country summary (latest year)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                year INTEGER,
                region VARCHAR,
                total_excl_lucf DOUBLE,
                total_incl_lucf DOUBLE,
                electricity_heat DOUBLE,
                transport DOUBLE,
                industry DOUBLE,
                building DOUBLE,
                manufacturing DOUBLE,
                land_use DOUBLE,
                total_excl_lucf_pc DOUBLE,
                per_capita_tier VARCHAR,
                electricity_share DOUBLE,
                transport_share DOUBLE,
                industry_share DOUBLE,
                manufacturing_share DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                total_emissions DOUBLE,
                total_incl_lucf DOUBLE,
                electricity_heat DOUBLE,
                transport DOUBLE,
                industry DOUBLE,
                manufacturing DOUBLE,
                land_use DOUBLE,
                avg_per_capita DOUBLE
            )
        """)

        # Sector summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sector_summary (
                sector VARCHAR,
                emissions DOUBLE,
                share DOUBLE
            )
        """)

        # Per capita tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                per_capita_tier VARCHAR,
                countries INTEGER,
                avg_per_capita DOUBLE,
                min_per_capita DOUBLE,
                max_per_capita DOUBLE,
                total_emissions DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, full_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, sector_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["co2_emissions", "country_summary", "region_summary", "sector_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO co2_emissions SELECT * FROM full_df")
        logger.info(f"Loaded {len(full_df)} rows into co2_emissions")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO sector_summary SELECT * FROM sector_df")
        logger.info(f"Loaded {len(sector_df)} rows into sector_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all CO2 emissions data."""
        return self.query("SELECT * FROM co2_emissions ORDER BY year DESC, total_excl_lucf DESC")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary for latest year."""
        return self.query("SELECT * FROM country_summary ORDER BY total_excl_lucf DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY total_emissions DESC")

    def get_sector_summary(self) -> pd.DataFrame:
        """Get sector summary."""
        return self.query("SELECT * FROM sector_summary ORDER BY emissions DESC")

    def get_tier_summary(self) -> pd.DataFrame:
        """Get per capita tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE per_capita_tier
                WHEN 'Very High (15+)' THEN 1
                WHEN 'High (8-15)' THEN 2
                WHEN 'Moderate (4-8)' THEN 3
                WHEN 'Low (1-4)' THEN 4
                WHEN 'Very Low (<1)' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT entity FROM co2_emissions ORDER BY entity")
        return result['entity'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get full time series data for a specific country."""
        return self.query(f"""
            SELECT * FROM co2_emissions
            WHERE entity = '{country}'
            ORDER BY year
        """)

    def get_top_emitters(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest total emissions."""
        return self.query(f"""
            SELECT entity, region, total_excl_lucf, total_excl_lucf_pc,
                   electricity_share, transport_share, per_capita_tier
            FROM country_summary
            WHERE total_excl_lucf IS NOT NULL
            ORDER BY total_excl_lucf DESC
            LIMIT {limit}
        """)

    def get_top_per_capita(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest per capita emissions."""
        return self.query(f"""
            SELECT entity, region, total_excl_lucf_pc, total_excl_lucf, per_capita_tier
            FROM country_summary
            WHERE total_excl_lucf_pc IS NOT NULL
            ORDER BY total_excl_lucf_pc DESC
            LIMIT {limit}
        """)

    def get_lowest_per_capita(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest per capita emissions."""
        return self.query(f"""
            SELECT entity, region, total_excl_lucf_pc, total_excl_lucf, per_capita_tier
            FROM country_summary
            WHERE total_excl_lucf_pc IS NOT NULL AND total_excl_lucf_pc > 0
            ORDER BY total_excl_lucf_pc ASC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT entity, total_excl_lucf, total_excl_lucf_pc, per_capita_tier
            FROM country_summary
            WHERE region = '{region}'
            ORDER BY total_excl_lucf DESC
        """)

    def get_global_trend(self) -> pd.DataFrame:
        """Get global emissions trend over time."""
        return self.query("""
            SELECT year, SUM(total_excl_lucf) as total_emissions,
                   SUM(total_incl_lucf) as total_incl_lucf,
                   SUM(electricity_heat) as electricity_heat,
                   SUM(transport) as transport,
                   SUM(industry) as industry,
                   SUM(manufacturing) as manufacturing
            FROM co2_emissions
            WHERE total_excl_lucf IS NOT NULL
            GROUP BY year
            ORDER BY year
        """)

    def get_country_trend(self, country: str) -> pd.DataFrame:
        """Get emissions trend for a specific country."""
        return self.query(f"""
            SELECT year, total_excl_lucf, total_excl_lucf_pc,
                   electricity_heat, transport, industry, manufacturing
            FROM co2_emissions
            WHERE entity = '{country}'
            ORDER BY year
        """)

    def get_years(self) -> List[int]:
        """Get list of all years in data."""
        result = self.query("SELECT DISTINCT year FROM co2_emissions ORDER BY year")
        return result['year'].tolist()

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest_year = self.conn.execute("SELECT MAX(year) FROM co2_emissions").fetchone()[0]
        global_emissions = self.query(f"""
            SELECT SUM(total_excl_lucf) as total FROM co2_emissions
            WHERE year = {latest_year} AND total_excl_lucf IS NOT NULL
        """)['total'].iloc[0]

        top_emitter = self.query(f"""
            SELECT entity, total_excl_lucf FROM country_summary
            ORDER BY total_excl_lucf DESC LIMIT 1
        """).iloc[0]

        top_per_capita = self.query(f"""
            SELECT entity, total_excl_lucf_pc FROM country_summary
            WHERE total_excl_lucf_pc IS NOT NULL
            ORDER BY total_excl_lucf_pc DESC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM co2_emissions").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM co2_emissions").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "year_min": self.conn.execute("SELECT MIN(year) FROM co2_emissions").fetchone()[0],
            "year_max": latest_year,
            "global_emissions_gt": global_emissions / 1000 if global_emissions else 0,  # Convert Mt to Gt
            "top_emitter": top_emitter['entity'],
            "top_emitter_gt": top_emitter['total_excl_lucf'] / 1000 if top_emitter['total_excl_lucf'] else 0,
            "top_per_capita_country": top_per_capita['entity'],
            "top_per_capita": top_per_capita['total_excl_lucf_pc'],
        }


if __name__ == "__main__":
    with CO2EmissionsDatabase() as db:
        print("Stats:", db.get_stats())
