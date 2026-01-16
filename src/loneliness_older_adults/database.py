"""
DuckDB database for Self-reported Loneliness in Older Adults data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Dict, Any

from src.shared.base_database import BaseDatabase


class LonelinessOlderAdultsDatabase(BaseDatabase):
    """Database manager for loneliness in older adults data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "loneliness_older_adults.duckdb"
    CSV_PATH = Path(__file__).parent.parent.parent / "Self-reported loneliness in older adults - OWID (2018).csv"
    PROJECT_NAME = "Loneliness in Older Adults"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating loneliness older adults database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS loneliness_by_country (
                country VARCHAR PRIMARY KEY,
                year INTEGER,
                loneliness_rate DOUBLE,
                region VARCHAR
            )
        """)

        # Regional summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS regional_summary (
                region VARCHAR PRIMARY KEY,
                avg_loneliness DOUBLE,
                min_loneliness DOUBLE,
                max_loneliness DOUBLE,
                country_count INTEGER
            )
        """)

        logger.info("Schema created successfully")

    def load_from_csv(self, csv_path: Path = None):
        """Load data from CSV file."""
        csv_path = csv_path or self.CSV_PATH
        logger.info(f"Loading data from {csv_path}")

        # Read CSV
        df = pd.read_csv(csv_path)
        df.columns = ['country', 'year', 'loneliness_rate']

        # Add region classification
        region_map = {
            'Austria': 'Central Europe',
            'Belgium': 'Western Europe',
            'Denmark': 'Nordic',
            'England': 'Western Europe',
            'Finland': 'Nordic',
            'France': 'Western Europe',
            'Germany': 'Central Europe',
            'Greece': 'Southern Europe',
            'Israel': 'Middle East',
            'Italy': 'Southern Europe',
            'Netherlands': 'Western Europe',
            'Spain': 'Southern Europe',
            'Sweden': 'Nordic',
            'Switzerland': 'Central Europe',
            'United States': 'North America',
        }
        df['region'] = df['country'].map(region_map)

        # Clear existing data
        self.conn.execute("DELETE FROM loneliness_by_country")
        self.conn.execute("DELETE FROM regional_summary")

        # Load main data
        self.conn.execute("INSERT INTO loneliness_by_country SELECT * FROM df")
        logger.info(f"Loaded {len(df)} rows into loneliness_by_country")

        # Calculate and load regional summary
        regional = df.groupby('region').agg({
            'loneliness_rate': ['mean', 'min', 'max', 'count']
        }).reset_index()
        regional.columns = ['region', 'avg_loneliness', 'min_loneliness', 'max_loneliness', 'country_count']

        self.conn.execute("INSERT INTO regional_summary SELECT * FROM regional")
        logger.info(f"Loaded {len(regional)} rows into regional_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all loneliness data (required by base class)."""
        return self.query("SELECT * FROM loneliness_by_country ORDER BY loneliness_rate DESC")

    def get_by_country(self) -> pd.DataFrame:
        """Get loneliness data by country sorted by rate."""
        return self.query("""
            SELECT country, year, loneliness_rate, region
            FROM loneliness_by_country
            ORDER BY loneliness_rate DESC
        """)

    def get_regional_summary(self) -> pd.DataFrame:
        """Get regional summary statistics."""
        return self.query("""
            SELECT * FROM regional_summary
            ORDER BY avg_loneliness DESC
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries in a specific region."""
        return self.query(f"""
            SELECT country, loneliness_rate, year
            FROM loneliness_by_country
            WHERE region = '{region}'
            ORDER BY loneliness_rate DESC
        """)

    def get_extremes(self) -> Dict[str, Any]:
        """Get countries with highest and lowest loneliness."""
        highest = self.query("""
            SELECT country, loneliness_rate
            FROM loneliness_by_country
            ORDER BY loneliness_rate DESC
            LIMIT 1
        """).iloc[0]

        lowest = self.query("""
            SELECT country, loneliness_rate
            FROM loneliness_by_country
            ORDER BY loneliness_rate ASC
            LIMIT 1
        """).iloc[0]

        return {
            "highest_country": highest['country'],
            "highest_rate": highest['loneliness_rate'],
            "lowest_country": lowest['country'],
            "lowest_rate": lowest['loneliness_rate'],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        df = self.get_full_data()
        extremes = self.get_extremes()

        return {
            "project": self.PROJECT_NAME,
            "total_countries": len(df),
            "avg_loneliness": round(df['loneliness_rate'].mean(), 1),
            "highest_country": extremes['highest_country'],
            "highest_rate": extremes['highest_rate'],
            "lowest_country": extremes['lowest_country'],
            "lowest_rate": extremes['lowest_rate'],
            "regions": self.conn.execute("SELECT COUNT(DISTINCT region) FROM loneliness_by_country").fetchone()[0],
        }


if __name__ == "__main__":
    with LonelinessOlderAdultsDatabase() as db:
        db.create_schema()
        db.load_from_csv()
        print("Stats:", db.get_stats())
