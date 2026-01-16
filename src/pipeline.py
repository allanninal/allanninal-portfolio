"""
Main ETL Pipeline: Extract, Transform, Load

This module orchestrates the full data pipeline:
1. Extract: Load raw CSV data
2. Transform: Clean, validate, and enrich
3. Load: Store in DuckDB database

Usage:
    python -m src.pipeline
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

from src.extract.loader import load_raw_data, get_data_info
from src.transform.cleaner import clean_data, validate_data
from src.transform.enricher import calculate_coverage_gap, add_derived_metrics, create_summary_stats
from src.load.database import DatabaseManager


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan> - {message}",
    level="INFO"
)
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)


def run_pipeline(save_intermediate: bool = True) -> dict:
    """
    Run the complete ETL pipeline.

    Args:
        save_intermediate: If True, save intermediate CSV files

    Returns:
        Dictionary with pipeline execution statistics
    """
    start_time = datetime.now()
    stats = {"started_at": start_time.isoformat()}

    logger.info("=" * 60)
    logger.info("Starting ETL Pipeline: Media Perception vs Reality")
    logger.info("=" * 60)

    # =========================================
    # EXTRACT
    # =========================================
    logger.info("\n[1/4] EXTRACT: Loading raw data...")

    raw_df = load_raw_data()
    data_info = get_data_info(raw_df)

    stats["extract"] = {
        "rows": data_info["row_count"],
        "columns": data_info["column_count"],
        "year_range": data_info["year_range"],
        "entities": data_info["entity_count"],
    }

    # =========================================
    # TRANSFORM: Clean
    # =========================================
    logger.info("\n[2/4] TRANSFORM: Cleaning data...")

    clean_df = clean_data(raw_df)
    validation_result = validate_data(clean_df)

    if not validation_result.is_valid:
        logger.error("Data validation failed! Errors:")
        for error in validation_result.errors:
            logger.error(f"  - {error}")
        raise ValueError("Data validation failed")

    stats["validation"] = {
        "is_valid": validation_result.is_valid,
        "warnings": len(validation_result.warnings),
        "stats": validation_result.stats,
    }

    # =========================================
    # TRANSFORM: Enrich
    # =========================================
    logger.info("\n[3/4] TRANSFORM: Enriching data...")

    enriched_df = calculate_coverage_gap(clean_df)
    enriched_df = add_derived_metrics(enriched_df)
    summary_df = create_summary_stats(enriched_df)

    stats["transform"] = {
        "output_rows": len(enriched_df),
        "output_columns": len(enriched_df.columns),
        "summary_rows": len(summary_df),
    }

    # Save intermediate files
    if save_intermediate:
        processed_path = Path("data/processed")
        processed_path.mkdir(exist_ok=True)

        clean_df.to_csv(processed_path / "cleaned_data.csv", index=False)
        enriched_df.to_csv(processed_path / "enriched_data.csv", index=False)
        summary_df.to_csv(processed_path / "summary_stats.csv", index=False)
        logger.info(f"Saved intermediate files to {processed_path}")

    # =========================================
    # LOAD
    # =========================================
    logger.info("\n[4/4] LOAD: Loading into DuckDB...")

    with DatabaseManager() as db:
        db.create_schema()
        db.load_data(enriched_df)
        table_stats = db.get_table_stats()

    stats["load"] = {
        "database": str(DatabaseManager.DEFAULT_DB_PATH),
        "tables": table_stats,
    }

    # =========================================
    # SUMMARY
    # =========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    stats["completed_at"] = end_time.isoformat()
    stats["duration_seconds"] = round(duration, 2)

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Rows processed: {len(enriched_df):,}")
    logger.info(f"Database: {DatabaseManager.DEFAULT_DB_PATH}")

    # Print key insights
    logger.info("\n" + "-" * 40)
    logger.info("KEY INSIGHTS:")
    logger.info("-" * 40)

    most_overcovered = summary_df.nlargest(3, "gap_media_avg_mean")
    most_undercovered = summary_df.nsmallest(3, "gap_media_avg_mean")

    logger.info("Most OVER-covered causes (more media than deaths):")
    for _, row in most_overcovered.iterrows():
        logger.info(f"  {row['cause']}: +{row['gap_media_avg_mean']:.1f}% gap")

    logger.info("Most UNDER-covered causes (less media than deaths):")
    for _, row in most_undercovered.iterrows():
        logger.info(f"  {row['cause']}: {row['gap_media_avg_mean']:.1f}% gap")

    return stats


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    try:
        stats = run_pipeline()
        print("\n\nPipeline Statistics:")
        import json
        print(json.dumps(stats, indent=2, default=str))
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)
