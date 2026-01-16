"""
Time With People ETL Pipeline

Processes American Time Use Survey (ATUS) data (2009-2019).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import json

RAW_DATA_PATH = Path(__file__).parent.parent.parent
DATA_FILE = "Who Americans spend time with - American Time Use Survey (2009-2019).csv"

# Age group definitions
AGE_GROUPS = {
    (15, 19): "Teen (15-19)",
    (20, 29): "Young Adult (20-29)",
    (30, 39): "Adult (30-39)",
    (40, 49): "Middle Age (40-49)",
    (50, 59): "Mature Adult (50-59)",
    (60, 69): "Senior (60-69)",
    (70, 100): "Elderly (70+)",
}


def get_age_group(age: int) -> str:
    """Map age to age group."""
    for (min_age, max_age), group in AGE_GROUPS.items():
        if min_age <= age <= max_age:
            return group
    return "Unknown"


def load_raw_data() -> pd.DataFrame:
    """Load raw ATUS data from CSV."""
    file_path = RAW_DATA_PATH / DATA_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading ATUS data from: {file_path}")
    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows (ages)")

    return df


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and standardize column names."""
    logger.info("Cleaning and transforming data...")

    df = df.copy()

    # Rename columns to simpler names
    column_mapping = {
        'Entity': 'entity',
        'Year': 'age',  # Year column is actually age!
        'Time spent alone, by age of respondent (United States)': 'alone',
        'Time spent with children, by age of respondent (United States)': 'children',
        'Time spent with coworkers, by age of respondent (United States)': 'coworkers',
        'Time spent with family, by age of respondent (United States)': 'family',
        'Time spent with friends, by age of respondent (United States)': 'friends',
        'Time spent with other people, by age of respondent (United States)': 'other',
        'Time spent with partner, by age of respondent (United States)': 'partner',
        'Time spent with other unclassified people, by age of respondent (United States)': 'unclassified',
    }

    df = df.rename(columns=column_mapping)

    # Drop entity column (all US)
    df = df.drop(columns=['entity'])

    # Add age group
    df['age_group'] = df['age'].apply(get_age_group)

    # Calculate total accounted time (for verification)
    companion_cols = ['alone', 'children', 'coworkers', 'family', 'friends', 'other', 'partner', 'unclassified']
    df['total_accounted'] = df[companion_cols].sum(axis=1)

    # Reorder columns
    cols = ['age', 'alone', 'children', 'coworkers', 'family', 'friends', 'other', 'partner', 'unclassified', 'age_group', 'total_accounted']
    df = df[cols]

    logger.info(f"Transformation complete. Age range: {df['age'].min()}-{df['age'].max()}")

    return df


def create_companion_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary statistics for each companion type."""
    logger.info("Creating companion summary...")

    companion_cols = ['alone', 'children', 'coworkers', 'family', 'friends', 'other', 'partner']
    summaries = []

    for col in companion_cols:
        avg_minutes = df[col].mean()
        min_minutes = df[col].min()
        max_minutes = df[col].max()

        # Find peak age
        peak_idx = df[col].idxmax()
        peak_age = df.loc[peak_idx, 'age']

        # Find decline age (after peak, where it drops below 80% of peak)
        peak_val = df[col].max()
        threshold = peak_val * 0.8
        post_peak = df[df['age'] > peak_age]
        decline_rows = post_peak[post_peak[col] < threshold]
        decline_age = decline_rows['age'].min() if len(decline_rows) > 0 else None

        summaries.append({
            'companion': col.title(),
            'avg_minutes': round(avg_minutes, 1),
            'min_minutes': round(min_minutes, 1),
            'max_minutes': round(max_minutes, 1),
            'peak_age': int(peak_age),
            'decline_age': int(decline_age) if decline_age else None,
        })

    summary_df = pd.DataFrame(summaries)
    logger.info(f"Created summary for {len(summaries)} companion types")

    return summary_df


def create_age_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary by age group."""
    logger.info("Creating age group summary...")

    companion_cols = ['alone', 'children', 'coworkers', 'family', 'friends', 'partner']

    grouped = df.groupby('age_group').agg({
        'age': ['min', 'max'],
        **{col: 'mean' for col in companion_cols}
    }).round(1)

    # Flatten column names
    grouped.columns = ['age_min', 'age_max'] + companion_cols
    grouped = grouped.reset_index()

    # Add age range string
    grouped['age_range'] = grouped['age_min'].astype(str) + '-' + grouped['age_max'].astype(str)

    # Calculate total social time (excluding alone)
    social_cols = ['children', 'coworkers', 'family', 'friends', 'partner']
    grouped['total_social'] = grouped[social_cols].sum(axis=1).round(1)

    # Select final columns
    grouped = grouped[['age_group', 'age_range', 'alone', 'children', 'coworkers', 'family', 'friends', 'partner', 'total_social']]

    logger.info(f"Created summary for {len(grouped)} age groups")

    return grouped


def create_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """Convert to long format for easier visualization."""
    logger.info("Creating long format data...")

    companion_cols = ['alone', 'children', 'coworkers', 'family', 'friends', 'other', 'partner']

    long_df = df.melt(
        id_vars=['age', 'age_group'],
        value_vars=companion_cols,
        var_name='companion',
        value_name='minutes'
    )

    # Capitalize companion names
    long_df['companion'] = long_df['companion'].str.title()

    # Reorder columns to match database schema
    long_df = long_df[['age', 'companion', 'minutes', 'age_group']]

    logger.info(f"Created {len(long_df)} rows in long format")

    return long_df


def run_time_with_people_pipeline(save_files: bool = True) -> dict:
    """Run the complete time use pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Time With People Pipeline")
    logger.info("=" * 60)

    # Extract
    raw_df = load_raw_data()

    # Transform
    main_df = clean_and_transform(raw_df)
    companion_summary = create_companion_summary(main_df)
    age_group_summary = create_age_group_summary(main_df)
    long_df = create_long_format(main_df)

    # Save processed files
    if save_files:
        processed_path = RAW_DATA_PATH / "data" / "processed"
        processed_path.mkdir(exist_ok=True)
        main_df.to_csv(processed_path / "time_with_people.csv", index=False)
        companion_summary.to_csv(processed_path / "time_companion_summary.csv", index=False)
        age_group_summary.to_csv(processed_path / "time_age_groups.csv", index=False)
        long_df.to_csv(processed_path / "time_long_format.csv", index=False)
        logger.info(f"Saved processed files to {processed_path}")

    # Load to database
    from .database import TimeWithPeopleDatabase

    with TimeWithPeopleDatabase() as db:
        db.create_schema()
        db.load_data(main_df, companion_summary, age_group_summary, long_df)
        stats = db.get_stats()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)

    # Print key insights
    logger.info("\nKey Insights:")
    logger.info(f"  Age range: {stats['age_range'][0]}-{stats['age_range'][1]}")
    logger.info(f"  Peak alone time: {stats['peak_alone_minutes']} minutes/day at age {stats['peak_alone_age']}")

    return stats


if __name__ == "__main__":
    stats = run_time_with_people_pipeline()
    print(json.dumps(stats, indent=2, default=str))
