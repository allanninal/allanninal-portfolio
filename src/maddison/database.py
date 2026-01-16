"""
DuckDB database for Maddison Project historical economic data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase
from src.shared.mappings import REGION_MAPPING_FULL

# Use centralized region mapping
REGION_MAPPING = REGION_MAPPING_FULL


class MaddisonDatabase(BaseDatabase):
    """Database manager for Maddison Project economic history data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "maddison.duckdb"
    CSV_PATH = Path(__file__).parent.parent.parent / "Maddison Project Database 2020 (Bolt and van Zanden (2020)).csv"
    PROJECT_NAME = "Maddison Project"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating Maddison database schema...")

        # Main fact table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS economic_data (
                entity VARCHAR,
                year INTEGER,
                gdp_per_capita DOUBLE,
                population BIGINT,
                gdp DOUBLE,
                region VARCHAR
            )
        """)

        # Country summary (latest data)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                region VARCHAR,
                latest_year INTEGER,
                gdp_per_capita DOUBLE,
                population BIGINT,
                gdp DOUBLE,
                data_points INTEGER,
                first_year INTEGER
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                avg_gdp_per_capita DOUBLE,
                total_population BIGINT,
                total_gdp DOUBLE,
                countries INTEGER
            )
        """)

        # Year summary (for trends)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                global_avg_gdp_pc DOUBLE,
                total_population BIGINT,
                total_gdp DOUBLE,
                countries_with_data INTEGER
            )
        """)

        logger.info("Schema created successfully")

    def load_from_csv(self):
        """Load data from CSV file and populate database."""
        logger.info(f"Loading data from {self.CSV_PATH}")

        # Read CSV
        df = pd.read_csv(self.CSV_PATH)
        df.columns = ['entity', 'year', 'gdp_per_capita', 'population', 'gdp']

        # Add region mapping
        df['region'] = df['entity'].map(REGION_MAPPING).fillna('Other')

        # Filter out aggregates and keep only valid data
        aggregates = ['World', 'Western Europe', 'Eastern Europe', 'Western Offshoots',
                      'Latin America', 'East Asia', 'South and South-East Asia',
                      'Middle East and North Africa', 'Sub-Saharan Africa']
        df = df[~df['entity'].isin(aggregates)]

        # Clear and load main table
        self.conn.execute("DELETE FROM economic_data")
        self.conn.execute("INSERT INTO economic_data SELECT * FROM df")
        logger.info(f"Loaded {len(df)} rows into economic_data")

        # Create country summary
        self.conn.execute("DELETE FROM country_summary")
        self.conn.execute("""
            INSERT INTO country_summary
            SELECT
                entity,
                region,
                MAX(year) as latest_year,
                FIRST(gdp_per_capita) FILTER (WHERE year = (SELECT MAX(year) FROM economic_data e2 WHERE e2.entity = economic_data.entity AND e2.gdp_per_capita IS NOT NULL)) as gdp_per_capita,
                FIRST(population) FILTER (WHERE year = (SELECT MAX(year) FROM economic_data e2 WHERE e2.entity = economic_data.entity AND e2.population IS NOT NULL)) as population,
                FIRST(gdp) FILTER (WHERE year = (SELECT MAX(year) FROM economic_data e2 WHERE e2.entity = economic_data.entity AND e2.gdp IS NOT NULL)) as gdp,
                COUNT(*) as data_points,
                MIN(year) as first_year
            FROM economic_data
            GROUP BY entity, region
        """)

        # Create region summary (using 2018 data where available)
        self.conn.execute("DELETE FROM region_summary")
        self.conn.execute("""
            INSERT INTO region_summary
            SELECT
                region,
                AVG(gdp_per_capita) as avg_gdp_per_capita,
                SUM(population) as total_population,
                SUM(gdp) as total_gdp,
                COUNT(DISTINCT entity) as countries
            FROM economic_data
            WHERE year = 2018 AND gdp_per_capita IS NOT NULL
            GROUP BY region
            ORDER BY avg_gdp_per_capita DESC
        """)

        # Create year summary (modern era: 1820+)
        self.conn.execute("DELETE FROM year_summary")
        self.conn.execute("""
            INSERT INTO year_summary
            SELECT
                year,
                AVG(gdp_per_capita) as global_avg_gdp_pc,
                SUM(population) as total_population,
                SUM(gdp) as total_gdp,
                COUNT(DISTINCT entity) as countries_with_data
            FROM economic_data
            WHERE year >= 1820 AND gdp_per_capita IS NOT NULL
            GROUP BY year
            ORDER BY year
        """)

        logger.info("All summary tables populated")

    def get_full_data(self) -> pd.DataFrame:
        """Get all economic data."""
        return self.query("SELECT * FROM economic_data ORDER BY entity, year")

    def get_modern_data(self) -> pd.DataFrame:
        """Get modern era data (1820+)."""
        return self.query("""
            SELECT * FROM economic_data
            WHERE year >= 1820 AND gdp_per_capita IS NOT NULL
            ORDER BY entity, year
        """)

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("""
            SELECT * FROM country_summary
            WHERE gdp_per_capita IS NOT NULL
            ORDER BY gdp_per_capita DESC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_gdp_per_capita DESC")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year summary."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_country_history(self, entity: str) -> pd.DataFrame:
        """Get historical data for a country."""
        return self.query(f"""
            SELECT year, gdp_per_capita, population, gdp
            FROM economic_data
            WHERE entity = '{entity}' AND gdp_per_capita IS NOT NULL
            ORDER BY year
        """)

    def get_historical_data(self) -> pd.DataFrame:
        """Get ancient/medieval data (before 1820)."""
        return self.query("""
            SELECT * FROM economic_data
            WHERE year < 1820 AND gdp_per_capita IS NOT NULL
            ORDER BY year, entity
        """)

    def get_top_economies(self, year: int, limit: int = 20) -> pd.DataFrame:
        """Get top economies by GDP per capita for a given year."""
        return self.query(f"""
            SELECT entity, region, gdp_per_capita, population, gdp
            FROM economic_data
            WHERE year = {year} AND gdp_per_capita IS NOT NULL
            ORDER BY gdp_per_capita DESC
            LIMIT {limit}
        """)

    def get_growth_rates(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Calculate growth rates between two years."""
        return self.query(f"""
            WITH start_data AS (
                SELECT entity, gdp_per_capita as start_gdp
                FROM economic_data
                WHERE year = {start_year} AND gdp_per_capita IS NOT NULL
            ),
            end_data AS (
                SELECT entity, gdp_per_capita as end_gdp
                FROM economic_data
                WHERE year = {end_year} AND gdp_per_capita IS NOT NULL
            )
            SELECT
                e.entity,
                e.region,
                s.start_gdp,
                ed.end_gdp,
                ((ed.end_gdp - s.start_gdp) / s.start_gdp * 100) as growth_pct,
                (ed.end_gdp / s.start_gdp) as growth_multiple
            FROM economic_data e
            JOIN start_data s ON e.entity = s.entity
            JOIN end_data ed ON e.entity = ed.entity
            WHERE e.year = {end_year}
            ORDER BY growth_pct DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {"project": self.PROJECT_NAME}
        stats["total_records"] = self.conn.execute("SELECT COUNT(*) FROM economic_data").fetchone()[0]
        stats["entities"] = self.conn.execute("SELECT COUNT(DISTINCT entity) FROM economic_data").fetchone()[0]
        stats["year_range"] = self.conn.execute("SELECT MIN(year), MAX(year) FROM economic_data").fetchone()
        stats["records_with_gdp"] = self.conn.execute("SELECT COUNT(*) FROM economic_data WHERE gdp_per_capita IS NOT NULL").fetchone()[0]
        return stats


def init_database():
    """Initialize the database with data from CSV."""
    with MaddisonDatabase() as db:
        db.create_schema()
        db.load_from_csv()
        print("Stats:", db.get_stats())


if __name__ == "__main__":
    init_database()
