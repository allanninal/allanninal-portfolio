"""
Data pipeline for Self-reported Loneliness in Older Adults.

Extracts data from Our World in Data CSV and loads into DuckDB.
"""

from pathlib import Path
from loguru import logger

from src.loneliness_older_adults.database import LonelinessOlderAdultsDatabase


def run_pipeline():
    """Run the complete ETL pipeline for loneliness data."""
    logger.info("Starting Loneliness in Older Adults pipeline...")

    with LonelinessOlderAdultsDatabase() as db:
        # Create schema
        db.create_schema()

        # Load data from CSV
        db.load_from_csv()

        # Verify
        stats = db.get_stats()
        logger.info(f"Pipeline complete. Stats: {stats}")

    return stats


if __name__ == "__main__":
    run_pipeline()
