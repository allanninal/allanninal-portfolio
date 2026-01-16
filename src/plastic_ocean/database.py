"""
DuckDB database for Plastic Ocean Pollution data (Meijer et al. 2021).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class PlasticOceanDatabase(BaseDatabase):
    """Database manager for plastic ocean pollution data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "plastic_ocean.duckdb"
    PROJECT_NAME = "Plastic Ocean Pollution"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating plastic ocean database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS plastic_ocean (
                entity VARCHAR,
                year INTEGER,
                probability DOUBLE,
                mismanaged_waste DOUBLE,
                ocean_emissions DOUBLE,
                share_emitted DOUBLE,
                share_global_waste DOUBLE,
                share_global_ocean DOUBLE,
                waste_per_capita DOUBLE,
                ocean_per_capita DOUBLE,
                region VARCHAR,
                ocean_tier VARCHAR,
                per_capita_tier VARCHAR,
                mismanaged_kt DOUBLE,
                ocean_kt DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                total_mismanaged DOUBLE,
                total_ocean_emissions DOUBLE,
                share_global_ocean DOUBLE,
                avg_waste_per_capita DOUBLE,
                avg_ocean_per_capita DOUBLE,
                mismanaged_kt DOUBLE,
                ocean_kt DOUBLE
            )
        """)

        # Ocean tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ocean_tier_summary (
                ocean_tier VARCHAR,
                countries INTEGER,
                total_share DOUBLE,
                avg_share DOUBLE,
                min_share DOUBLE,
                max_share DOUBLE,
                total_emissions DOUBLE
            )
        """)

        # Per capita tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS per_capita_summary (
                per_capita_tier VARCHAR,
                countries INTEGER,
                avg_per_capita DOUBLE,
                min_per_capita DOUBLE,
                max_per_capita DOUBLE,
                total_emissions DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  ocean_tier_df: pd.DataFrame, per_capita_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["plastic_ocean", "region_summary", "ocean_tier_summary", "per_capita_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO plastic_ocean SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into plastic_ocean")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO ocean_tier_summary SELECT * FROM ocean_tier_df")
        logger.info(f"Loaded {len(ocean_tier_df)} rows into ocean_tier_summary")

        self.conn.execute("INSERT INTO per_capita_summary SELECT * FROM per_capita_df")
        logger.info(f"Loaded {len(per_capita_df)} rows into per_capita_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all plastic ocean data."""
        return self.query("SELECT * FROM plastic_ocean ORDER BY ocean_emissions DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY total_ocean_emissions DESC")

    def get_ocean_tier_summary(self) -> pd.DataFrame:
        """Get ocean tier summary."""
        return self.query("""
            SELECT * FROM ocean_tier_summary
            ORDER BY CASE ocean_tier
                WHEN 'Very High (5%+)' THEN 1
                WHEN 'High (1-5%)' THEN 2
                WHEN 'Moderate (0.1-1%)' THEN 3
                WHEN 'Low (0.01-0.1%)' THEN 4
                WHEN 'Very Low (<0.01%)' THEN 5
                ELSE 6
            END
        """)

    def get_per_capita_summary(self) -> pd.DataFrame:
        """Get per capita tier summary."""
        return self.query("""
            SELECT * FROM per_capita_summary
            ORDER BY CASE per_capita_tier
                WHEN 'Very High (1+ kg)' THEN 1
                WHEN 'High (0.1-1 kg)' THEN 2
                WHEN 'Moderate (0.01-0.1 kg)' THEN 3
                WHEN 'Low (<0.01 kg)' THEN 4
                WHEN 'Zero' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT entity FROM plastic_ocean ORDER BY entity")
        return result['entity'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM plastic_ocean
            WHERE entity = '{country}'
        """)

    def get_top_ocean_emitters(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest ocean plastic emissions."""
        return self.query(f"""
            SELECT entity, region, ocean_kt, share_global_ocean,
                   ocean_per_capita, ocean_tier
            FROM plastic_ocean
            WHERE ocean_emissions > 0
            ORDER BY ocean_emissions DESC
            LIMIT {limit}
        """)

    def get_top_mismanaged(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most mismanaged plastic waste."""
        return self.query(f"""
            SELECT entity, region, mismanaged_kt, share_global_waste,
                   waste_per_capita, ocean_tier
            FROM plastic_ocean
            ORDER BY mismanaged_waste DESC
            LIMIT {limit}
        """)

    def get_top_per_capita_ocean(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest per capita ocean emissions."""
        return self.query(f"""
            SELECT entity, region, ocean_per_capita, ocean_kt,
                   share_global_ocean, per_capita_tier
            FROM plastic_ocean
            WHERE ocean_per_capita > 0
            ORDER BY ocean_per_capita DESC
            LIMIT {limit}
        """)

    def get_top_per_capita_waste(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest per capita mismanaged waste."""
        return self.query(f"""
            SELECT entity, region, waste_per_capita, mismanaged_kt,
                   share_global_waste
            FROM plastic_ocean
            ORDER BY waste_per_capita DESC
            LIMIT {limit}
        """)

    def get_highest_probability(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest probability of ocean emission."""
        return self.query(f"""
            SELECT entity, region, probability, ocean_kt, share_global_ocean
            FROM plastic_ocean
            WHERE probability > 0
            ORDER BY probability DESC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT entity, ocean_kt, mismanaged_kt, share_global_ocean,
                   ocean_per_capita, ocean_tier
            FROM plastic_ocean
            WHERE region = '{region}'
            ORDER BY ocean_emissions DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        total_ocean = self.query("SELECT SUM(ocean_emissions) as total FROM plastic_ocean")['total'].iloc[0]
        total_mismanaged = self.query("SELECT SUM(mismanaged_waste) as total FROM plastic_ocean")['total'].iloc[0]

        top_emitter = self.query("""
            SELECT entity, share_global_ocean FROM plastic_ocean
            ORDER BY ocean_emissions DESC LIMIT 1
        """).iloc[0]

        top_mismanaged = self.query("""
            SELECT entity, share_global_waste FROM plastic_ocean
            ORDER BY mismanaged_waste DESC LIMIT 1
        """).iloc[0]

        top_per_capita = self.query("""
            SELECT entity, ocean_per_capita FROM plastic_ocean
            WHERE ocean_per_capita > 0
            ORDER BY ocean_per_capita DESC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM plastic_ocean").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM plastic_ocean").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "total_ocean_kt": total_ocean / 1000 if total_ocean else 0,
            "total_mismanaged_kt": total_mismanaged / 1000 if total_mismanaged else 0,
            "top_emitter": top_emitter['entity'],
            "top_emitter_share": top_emitter['share_global_ocean'],
            "top_mismanaged_country": top_mismanaged['entity'],
            "top_mismanaged_share": top_mismanaged['share_global_waste'],
            "top_per_capita_country": top_per_capita['entity'],
            "top_per_capita": top_per_capita['ocean_per_capita'],
        }


if __name__ == "__main__":
    with PlasticOceanDatabase() as db:
        print("Stats:", db.get_stats())
