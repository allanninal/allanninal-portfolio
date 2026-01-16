"""
DuckDB database for Energy Deaths per TWh data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class EnergyDeathsDatabase(BaseDatabase):
    """Database manager for energy deaths data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "energy_deaths.duckdb"
    PROJECT_NAME = "Deaths per TWh Energy Production"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating energy deaths database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS energy_deaths (
                energy_source VARCHAR,
                year INTEGER,
                deaths_per_twh DOUBLE,
                category VARCHAR,
                safety_tier VARCHAR,
                relative_danger DOUBLE,
                safety_rank INTEGER
            )
        """)

        # Category summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS category_summary (
                category VARCHAR,
                sources INTEGER,
                avg_deaths DOUBLE,
                min_deaths DOUBLE,
                max_deaths DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, category_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["energy_deaths", "category_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO energy_deaths SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into energy_deaths")

        self.conn.execute("INSERT INTO category_summary SELECT * FROM category_df")
        logger.info(f"Loaded {len(category_df)} rows into category_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all energy deaths data."""
        return self.query("SELECT * FROM energy_deaths ORDER BY deaths_per_twh DESC")

    def get_by_safety(self) -> pd.DataFrame:
        """Get data sorted by safety (safest first)."""
        return self.query("SELECT * FROM energy_deaths ORDER BY deaths_per_twh ASC")

    def get_category_summary(self) -> pd.DataFrame:
        """Get category summary."""
        return self.query("SELECT * FROM category_summary ORDER BY avg_deaths DESC")

    def get_fossil_fuels(self) -> pd.DataFrame:
        """Get fossil fuel sources."""
        return self.query("""
            SELECT * FROM energy_deaths
            WHERE category = 'Fossil Fuels'
            ORDER BY deaths_per_twh DESC
        """)

    def get_renewables(self) -> pd.DataFrame:
        """Get renewable sources."""
        return self.query("""
            SELECT * FROM energy_deaths
            WHERE category = 'Renewables'
            ORDER BY deaths_per_twh DESC
        """)

    def get_clean_energy(self) -> pd.DataFrame:
        """Get clean energy sources (renewables + nuclear)."""
        return self.query("""
            SELECT * FROM energy_deaths
            WHERE category IN ('Renewables', 'Nuclear')
            ORDER BY deaths_per_twh DESC
        """)

    def get_by_tier(self, tier: str) -> pd.DataFrame:
        """Get sources by safety tier."""
        return self.query(f"""
            SELECT * FROM energy_deaths
            WHERE safety_tier = '{tier}'
            ORDER BY deaths_per_twh DESC
        """)

    def get_comparison(self, source1: str, source2: str) -> dict:
        """Compare two energy sources."""
        data1 = self.query(f"SELECT * FROM energy_deaths WHERE energy_source = '{source1}'")
        data2 = self.query(f"SELECT * FROM energy_deaths WHERE energy_source = '{source2}'")

        if len(data1) == 0 or len(data2) == 0:
            return None

        rate1 = data1.iloc[0]['deaths_per_twh']
        rate2 = data2.iloc[0]['deaths_per_twh']

        return {
            "source1": source1,
            "source2": source2,
            "rate1": rate1,
            "rate2": rate2,
            "ratio": rate1 / rate2 if rate2 > 0 else float('inf'),
            "difference": rate1 - rate2,
            "safer": source1 if rate1 < rate2 else source2,
        }

    def get_stats(self) -> dict:
        """Get database statistics."""
        data = self.get_full_data()

        most_dangerous = data.iloc[0]
        safest = data.iloc[-1]

        fossil = data[data['category'] == 'Fossil Fuels']['deaths_per_twh'].mean()
        renewable = data[data['category'] == 'Renewables']['deaths_per_twh'].mean()

        return {
            "project": self.PROJECT_NAME,
            "sources": len(data),
            "categories": self.conn.execute("SELECT COUNT(DISTINCT category) FROM energy_deaths").fetchone()[0],
            "most_dangerous": most_dangerous['energy_source'],
            "highest_deaths": most_dangerous['deaths_per_twh'],
            "safest": safest['energy_source'],
            "lowest_deaths": safest['deaths_per_twh'],
            "danger_ratio": most_dangerous['deaths_per_twh'] / safest['deaths_per_twh'],
            "fossil_avg": fossil,
            "renewable_avg": renewable,
            "fossil_vs_renewable": fossil / renewable if renewable > 0 else float('inf'),
        }


if __name__ == "__main__":
    with EnergyDeathsDatabase() as db:
        print("Stats:", db.get_stats())
