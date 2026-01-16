"""DuckDB database management for the deaths vs media coverage data."""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class DatabaseManager(BaseDatabase):
    """
    Manages DuckDB database operations for the media perception project.

    Implements a simple star schema:
    - dim_cause: Cause of death dimension
    - dim_year: Year dimension with period classification
    - fact_metrics: Main fact table with all measurements
    """

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "media_perception.duckdb"
    PROJECT_NAME = "Media Perception"

    def create_schema(self):
        """Create the database schema (star schema)."""
        logger.info("Creating database schema...")

        # Dimension: Causes of death
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_cause (
                cause_id INTEGER PRIMARY KEY,
                cause_name VARCHAR NOT NULL,
                category VARCHAR,
                is_chronic_disease BOOLEAN,
                is_violence_related BOOLEAN
            )
        """)

        # Dimension: Years
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_year (
                year INTEGER PRIMARY KEY,
                period VARCHAR,
                is_post_911 BOOLEAN,
                decade INTEGER
            )
        """)

        # Fact table: All metrics
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fact_metrics (
                id INTEGER PRIMARY KEY,
                cause_id INTEGER REFERENCES dim_cause(cause_id),
                year INTEGER REFERENCES dim_year(year),
                share_deaths DOUBLE,
                share_google DOUBLE,
                share_nyt DOUBLE,
                share_guardian DOUBLE,
                share_media_avg DOUBLE,
                gap_nyt DOUBLE,
                gap_guardian DOUBLE,
                gap_media_avg DOUBLE,
                gap_google DOUBLE,
                ratio_nyt DOUBLE,
                ratio_guardian DOUBLE,
                attention_score DOUBLE
            )
        """)

        # Summary view for easy querying
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_metrics_full AS
            SELECT
                f.*,
                c.cause_name,
                c.category,
                y.period,
                y.is_post_911
            FROM fact_metrics f
            JOIN dim_cause c ON f.cause_id = c.cause_id
            JOIN dim_year y ON f.year = y.year
        """)

        # Aggregated summary view
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_cause_summary AS
            SELECT
                c.cause_name,
                c.category,
                AVG(f.share_deaths) as avg_share_deaths,
                AVG(f.share_nyt) as avg_share_nyt,
                AVG(f.share_guardian) as avg_share_guardian,
                AVG(f.share_media_avg) as avg_share_media,
                AVG(f.gap_media_avg) as avg_gap,
                MIN(f.gap_media_avg) as min_gap,
                MAX(f.gap_media_avg) as max_gap
            FROM fact_metrics f
            JOIN dim_cause c ON f.cause_id = c.cause_id
            GROUP BY c.cause_name, c.category
            ORDER BY avg_gap DESC
        """)

        logger.info("Schema created successfully")

    def load_data(self, df: pd.DataFrame):
        """
        Load enriched DataFrame into the database.

        Args:
            df: Enriched DataFrame with all calculated metrics
        """
        logger.info(f"Loading {len(df):,} rows into database...")

        # Clear existing data
        self.conn.execute("DELETE FROM fact_metrics")
        self.conn.execute("DELETE FROM dim_cause")
        self.conn.execute("DELETE FROM dim_year")

        # Load dim_cause
        causes = df[["cause", "category"]].drop_duplicates()
        causes["cause_id"] = range(1, len(causes) + 1)
        causes["is_chronic_disease"] = causes["category"] == "chronic_disease"
        causes["is_violence_related"] = causes["category"].isin(["violence", "behavioral"])

        self.conn.execute("""
            INSERT INTO dim_cause (cause_id, cause_name, category, is_chronic_disease, is_violence_related)
            SELECT cause_id, cause, category, is_chronic_disease, is_violence_related
            FROM causes
        """)
        logger.info(f"Loaded {len(causes)} causes into dim_cause")

        # Load dim_year
        years = df[["year", "period"]].drop_duplicates()
        years["is_post_911"] = years["year"] >= 2002
        years["decade"] = (years["year"] // 10) * 10

        self.conn.execute("""
            INSERT INTO dim_year (year, period, is_post_911, decade)
            SELECT year, period, is_post_911, decade
            FROM years
        """)
        logger.info(f"Loaded {len(years)} years into dim_year")

        # Create cause_id mapping
        cause_id_map = causes.set_index("cause")["cause_id"].to_dict()
        df["cause_id"] = df["cause"].map(cause_id_map)

        # Load fact_metrics
        fact_cols = [
            "cause_id", "year", "share_deaths", "share_google", "share_nyt",
            "share_guardian", "share_media_avg", "gap_nyt", "gap_guardian",
            "gap_media_avg", "gap_google", "ratio_nyt", "ratio_guardian",
            "attention_score"
        ]
        facts = df[fact_cols].copy()
        facts["id"] = range(1, len(facts) + 1)

        self.conn.execute("""
            INSERT INTO fact_metrics
            SELECT id, cause_id, year, share_deaths, share_google, share_nyt,
                   share_guardian, share_media_avg, gap_nyt, gap_guardian,
                   gap_media_avg, gap_google, ratio_nyt, ratio_guardian,
                   attention_score
            FROM facts
        """)
        logger.info(f"Loaded {len(facts)} rows into fact_metrics")

    def get_full_data(self) -> pd.DataFrame:
        """Get all data from the full metrics view."""
        return self.query("SELECT * FROM v_metrics_full ORDER BY cause_name, year")

    def get_cause_summary(self) -> pd.DataFrame:
        """Get aggregated summary by cause."""
        return self.query("SELECT * FROM v_cause_summary")

    def get_yearly_totals(self) -> pd.DataFrame:
        """Get yearly aggregated totals."""
        return self.query("""
            SELECT
                year,
                SUM(share_deaths) as total_deaths,
                SUM(share_nyt) as total_nyt,
                SUM(share_guardian) as total_guardian
            FROM v_metrics_full
            GROUP BY year
            ORDER BY year
        """)

    def get_table_stats(self) -> dict:
        """Get row counts for all tables."""
        stats = {"project": self.PROJECT_NAME}
        for table in ["dim_cause", "dim_year", "fact_metrics"]:
            result = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            stats[table] = result[0]
        return stats

    def get_stats(self) -> dict:
        """Get database statistics (alias for get_table_stats)."""
        return self.get_table_stats()


if __name__ == "__main__":
    from src.extract.loader import load_raw_data
    from src.transform.cleaner import clean_data
    from src.transform.enricher import calculate_coverage_gap, add_derived_metrics

    # Full ETL pipeline
    print("Running full ETL pipeline...")

    raw_df = load_raw_data()
    clean_df = clean_data(raw_df)
    enriched_df = calculate_coverage_gap(clean_df)
    enriched_df = add_derived_metrics(enriched_df)

    with DatabaseManager() as db:
        db.create_schema()
        db.load_data(enriched_df)

        print("\nTable statistics:")
        for table, count in db.get_table_stats().items():
            print(f"  {table}: {count:,} rows")

        print("\nTop 5 over-covered causes:")
        summary = db.get_cause_summary()
        print(summary.head().to_string())
