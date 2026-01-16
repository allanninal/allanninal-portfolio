"""
DuckDB database for OECD Life Expectancy historical data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase
from src.shared.mappings import REGION_MAPPING_OECD

# Use centralized OECD region mapping
REGION_MAPPING = REGION_MAPPING_OECD


class LifeExpectancyDatabase(BaseDatabase):
    """Database manager for OECD Life Expectancy data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "life_expectancy.duckdb"
    CSV_PATH = Path(__file__).parent.parent.parent / "Life expectancy - OECD.csv"
    PROJECT_NAME = "Life Expectancy"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating Life Expectancy database schema...")

        # Main fact table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS life_expectancy_data (
                entity VARCHAR,
                year INTEGER,
                life_expectancy DOUBLE,
                region VARCHAR
            )
        """)

        # Country summary (latest data)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                region VARCHAR,
                latest_year INTEGER,
                life_expectancy DOUBLE,
                first_year INTEGER,
                data_points INTEGER,
                change_since_1960 DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                avg_life_expectancy DOUBLE,
                max_life_expectancy DOUBLE,
                min_life_expectancy DOUBLE,
                countries INTEGER
            )
        """)

        # Year summary (for trends)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                global_avg_life_expectancy DOUBLE,
                max_life_expectancy DOUBLE,
                min_life_expectancy DOUBLE,
                countries_with_data INTEGER
            )
        """)

        logger.info("Schema created successfully")

    def load_from_csv(self):
        """Load data from CSV file and populate database."""
        logger.info(f"Loading data from {self.CSV_PATH}")

        # Read CSV
        df = pd.read_csv(self.CSV_PATH)
        df.columns = ['entity', 'year', 'life_expectancy']

        # Add region mapping
        df['region'] = df['entity'].map(REGION_MAPPING).fillna('Other')

        # Clear and load main table
        self.conn.execute("DELETE FROM life_expectancy_data")
        self.conn.execute("INSERT INTO life_expectancy_data SELECT * FROM df")
        logger.info(f"Loaded {len(df)} rows into life_expectancy_data")

        # Create country summary
        self.conn.execute("DELETE FROM country_summary")
        self.conn.execute("""
            INSERT INTO country_summary
            WITH latest AS (
                SELECT entity, MAX(year) as latest_year
                FROM life_expectancy_data
                WHERE life_expectancy IS NOT NULL
                GROUP BY entity
            ),
            first_data AS (
                SELECT entity, MIN(year) as first_year,
                       FIRST(life_expectancy ORDER BY year) as first_le
                FROM life_expectancy_data
                WHERE life_expectancy IS NOT NULL
                GROUP BY entity
            )
            SELECT
                l.entity,
                l.region,
                lt.latest_year,
                l.life_expectancy,
                f.first_year,
                COUNT(*) as data_points,
                l.life_expectancy - f.first_le as change_since_1960
            FROM life_expectancy_data l
            JOIN latest lt ON l.entity = lt.entity AND l.year = lt.latest_year
            JOIN first_data f ON l.entity = f.entity
            GROUP BY l.entity, l.region, lt.latest_year, l.life_expectancy, f.first_year, f.first_le
        """)

        # Create region summary (using 2015 data where available)
        self.conn.execute("DELETE FROM region_summary")
        self.conn.execute("""
            INSERT INTO region_summary
            SELECT
                region,
                AVG(life_expectancy) as avg_life_expectancy,
                MAX(life_expectancy) as max_life_expectancy,
                MIN(life_expectancy) as min_life_expectancy,
                COUNT(DISTINCT entity) as countries
            FROM life_expectancy_data
            WHERE year = 2015 AND life_expectancy IS NOT NULL
            GROUP BY region
            ORDER BY avg_life_expectancy DESC
        """)

        # Create year summary
        self.conn.execute("DELETE FROM year_summary")
        self.conn.execute("""
            INSERT INTO year_summary
            SELECT
                year,
                AVG(life_expectancy) as global_avg_life_expectancy,
                MAX(life_expectancy) as max_life_expectancy,
                MIN(life_expectancy) as min_life_expectancy,
                COUNT(DISTINCT entity) as countries_with_data
            FROM life_expectancy_data
            WHERE life_expectancy IS NOT NULL
            GROUP BY year
            ORDER BY year
        """)

        logger.info("All summary tables populated")

    def get_full_data(self) -> pd.DataFrame:
        """Get all life expectancy data."""
        return self.query("SELECT * FROM life_expectancy_data ORDER BY entity, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("""
            SELECT * FROM country_summary
            WHERE life_expectancy IS NOT NULL
            ORDER BY life_expectancy DESC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_life_expectancy DESC")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year summary."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_country_history(self, entity: str) -> pd.DataFrame:
        """Get historical data for a country."""
        return self.query(f"""
            SELECT year, life_expectancy
            FROM life_expectancy_data
            WHERE entity = '{entity}' AND life_expectancy IS NOT NULL
            ORDER BY year
        """)

    def get_top_countries(self, year: int, limit: int = 20) -> pd.DataFrame:
        """Get top countries by life expectancy for a given year."""
        return self.query(f"""
            SELECT entity, region, life_expectancy
            FROM life_expectancy_data
            WHERE year = {year} AND life_expectancy IS NOT NULL
            ORDER BY life_expectancy DESC
            LIMIT {limit}
        """)

    def get_improvement_rates(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Calculate improvement rates between two years."""
        return self.query(f"""
            WITH start_data AS (
                SELECT entity, life_expectancy as start_le
                FROM life_expectancy_data
                WHERE year = {start_year} AND life_expectancy IS NOT NULL
            ),
            end_data AS (
                SELECT entity, life_expectancy as end_le
                FROM life_expectancy_data
                WHERE year = {end_year} AND life_expectancy IS NOT NULL
            )
            SELECT
                e.entity,
                e.region,
                s.start_le,
                ed.end_le,
                (ed.end_le - s.start_le) as years_gained,
                ((ed.end_le - s.start_le) / s.start_le * 100) as improvement_pct
            FROM life_expectancy_data e
            JOIN start_data s ON e.entity = s.entity
            JOIN end_data ed ON e.entity = ed.entity
            WHERE e.year = {end_year}
            ORDER BY years_gained DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {"project": self.PROJECT_NAME}
        stats["total_records"] = self.conn.execute("SELECT COUNT(*) FROM life_expectancy_data").fetchone()[0]
        stats["entities"] = self.conn.execute("SELECT COUNT(DISTINCT entity) FROM life_expectancy_data").fetchone()[0]
        stats["year_range"] = self.conn.execute("SELECT MIN(year), MAX(year) FROM life_expectancy_data").fetchone()
        stats["records_with_data"] = self.conn.execute("SELECT COUNT(*) FROM life_expectancy_data WHERE life_expectancy IS NOT NULL").fetchone()[0]
        return stats


def init_database():
    """Initialize the database with data from CSV."""
    with LifeExpectancyDatabase() as db:
        db.create_schema()
        db.load_from_csv()
        print("Stats:", db.get_stats())


if __name__ == "__main__":
    init_database()
