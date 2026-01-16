"""
DuckDB database for Plastic Waste data from Jambeck et al. (2015).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase
from src.shared.mappings import REGION_MAPPING_FULL

# Use centralized region mapping
REGION_MAPPING = REGION_MAPPING_FULL


class PlasticWasteDatabase(BaseDatabase):
    """Database manager for Plastic Waste data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "plastic_waste.duckdb"
    CSV_PATH = Path(__file__).parent.parent.parent / "Plastic Waste - Jambeck et al. (2015).csv"
    PROJECT_NAME = "Plastic Waste"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating Plastic Waste database schema...")

        # Main fact table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS plastic_waste_data (
                entity VARCHAR,
                year INTEGER,
                coastal_population BIGINT,
                waste_per_capita DOUBLE,
                plastic_share_pct DOUBLE,
                inadequate_mgmt_pct DOUBLE,
                municipal_waste BIGINT,
                plastic_waste BIGINT,
                inadequate_plastic_waste BIGINT,
                littered_plastic BIGINT,
                mismanaged_per_capita DOUBLE,
                mismanaged_2010 BIGINT,
                mismanaged_2025 BIGINT,
                plastic_per_capita_daily DOUBLE,
                region VARCHAR
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                region VARCHAR,
                coastal_population BIGINT,
                plastic_waste BIGINT,
                mismanaged_2010 BIGINT,
                mismanaged_2025 BIGINT,
                inadequate_mgmt_pct DOUBLE,
                plastic_per_capita_daily DOUBLE,
                projected_growth_pct DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                total_coastal_pop BIGINT,
                total_plastic_waste BIGINT,
                total_mismanaged_2010 BIGINT,
                total_mismanaged_2025 BIGINT,
                avg_inadequate_pct DOUBLE,
                countries INTEGER
            )
        """)

        logger.info("Schema created successfully")

    def load_from_csv(self):
        """Load data from CSV file and populate database."""
        logger.info(f"Loading data from {self.CSV_PATH}")

        # Read CSV
        df = pd.read_csv(self.CSV_PATH)
        df.columns = [
            'entity', 'year', 'coastal_population', 'waste_per_capita',
            'plastic_share_pct', 'inadequate_mgmt_pct', 'municipal_waste',
            'plastic_waste', 'inadequate_plastic_waste', 'littered_plastic',
            'mismanaged_per_capita', 'mismanaged_2010', 'mismanaged_2025',
            'plastic_per_capita_daily'
        ]

        # Remove World aggregate row
        df = df[df['entity'] != 'World']

        # Add region mapping
        df['region'] = df['entity'].map(REGION_MAPPING).fillna('Other')

        # Clear and load main table
        self.conn.execute("DELETE FROM plastic_waste_data")
        self.conn.execute("INSERT INTO plastic_waste_data SELECT * FROM df")
        logger.info(f"Loaded {len(df)} rows into plastic_waste_data")

        # Create country summary
        self.conn.execute("DELETE FROM country_summary")
        self.conn.execute("""
            INSERT INTO country_summary
            SELECT
                entity,
                region,
                coastal_population,
                plastic_waste,
                mismanaged_2010,
                mismanaged_2025,
                inadequate_mgmt_pct,
                plastic_per_capita_daily,
                CASE WHEN mismanaged_2010 > 0
                    THEN ((mismanaged_2025 - mismanaged_2010) * 100.0 / mismanaged_2010)
                    ELSE 0
                END as projected_growth_pct
            FROM plastic_waste_data
            WHERE coastal_population IS NOT NULL
        """)

        # Create region summary
        self.conn.execute("DELETE FROM region_summary")
        self.conn.execute("""
            INSERT INTO region_summary
            SELECT
                region,
                SUM(coastal_population) as total_coastal_pop,
                SUM(plastic_waste) as total_plastic_waste,
                SUM(mismanaged_2010) as total_mismanaged_2010,
                SUM(mismanaged_2025) as total_mismanaged_2025,
                AVG(inadequate_mgmt_pct) as avg_inadequate_pct,
                COUNT(DISTINCT entity) as countries
            FROM plastic_waste_data
            WHERE coastal_population IS NOT NULL
            GROUP BY region
            ORDER BY total_mismanaged_2010 DESC
        """)

        logger.info("All summary tables populated")

    def get_full_data(self) -> pd.DataFrame:
        """Get all plastic waste data."""
        return self.query("SELECT * FROM plastic_waste_data ORDER BY mismanaged_2010 DESC")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("""
            SELECT * FROM country_summary
            WHERE coastal_population IS NOT NULL
            ORDER BY mismanaged_2010 DESC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY total_mismanaged_2010 DESC")

    def get_top_polluters(self, limit: int = 20) -> pd.DataFrame:
        """Get top countries by mismanaged plastic waste."""
        return self.query(f"""
            SELECT entity, region, coastal_population, plastic_waste,
                   mismanaged_2010, mismanaged_2025, inadequate_mgmt_pct,
                   plastic_per_capita_daily
            FROM plastic_waste_data
            WHERE mismanaged_2010 IS NOT NULL
            ORDER BY mismanaged_2010 DESC
            LIMIT {limit}
        """)

    def get_top_per_capita(self, limit: int = 20) -> pd.DataFrame:
        """Get top countries by per capita mismanaged plastic."""
        return self.query(f"""
            SELECT entity, region, mismanaged_per_capita,
                   plastic_per_capita_daily, inadequate_mgmt_pct
            FROM plastic_waste_data
            WHERE mismanaged_per_capita IS NOT NULL
            ORDER BY mismanaged_per_capita DESC
            LIMIT {limit}
        """)

    def get_waste_management_analysis(self) -> pd.DataFrame:
        """Get waste management efficiency analysis."""
        return self.query("""
            SELECT entity, region, inadequate_mgmt_pct,
                   plastic_waste, mismanaged_2010,
                   CASE
                       WHEN inadequate_mgmt_pct = 0 THEN 'Excellent'
                       WHEN inadequate_mgmt_pct < 20 THEN 'Good'
                       WHEN inadequate_mgmt_pct < 50 THEN 'Moderate'
                       WHEN inadequate_mgmt_pct < 80 THEN 'Poor'
                       ELSE 'Critical'
                   END as management_rating
            FROM plastic_waste_data
            WHERE inadequate_mgmt_pct IS NOT NULL
            ORDER BY inadequate_mgmt_pct DESC
        """)

    def get_projection_analysis(self) -> pd.DataFrame:
        """Get 2010 vs 2025 projection analysis."""
        return self.query("""
            SELECT entity, region, mismanaged_2010, mismanaged_2025,
                   (mismanaged_2025 - mismanaged_2010) as absolute_change,
                   CASE WHEN mismanaged_2010 > 0
                       THEN ((mismanaged_2025 - mismanaged_2010) * 100.0 / mismanaged_2010)
                       ELSE 0
                   END as growth_pct
            FROM plastic_waste_data
            WHERE mismanaged_2010 IS NOT NULL AND mismanaged_2025 IS NOT NULL
            ORDER BY (mismanaged_2025 - mismanaged_2010) DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {"project": self.PROJECT_NAME}
        stats["total_countries"] = self.conn.execute("SELECT COUNT(*) FROM plastic_waste_data WHERE coastal_population IS NOT NULL").fetchone()[0]
        stats["total_mismanaged_2010"] = self.conn.execute("SELECT SUM(mismanaged_2010) FROM plastic_waste_data").fetchone()[0]
        stats["total_mismanaged_2025"] = self.conn.execute("SELECT SUM(mismanaged_2025) FROM plastic_waste_data").fetchone()[0]
        stats["total_coastal_pop"] = self.conn.execute("SELECT SUM(coastal_population) FROM plastic_waste_data").fetchone()[0]
        return stats


def init_database():
    """Initialize the database with data from CSV."""
    with PlasticWasteDatabase() as db:
        db.create_schema()
        db.load_from_csv()
        print("Stats:", db.get_stats())


if __name__ == "__main__":
    init_database()
