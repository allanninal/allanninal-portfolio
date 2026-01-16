"""Data extraction and loading from raw sources."""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Optional


RAW_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"
MAIN_DATASET = "Causes of death vs. media coverage - Shen.csv"


def load_raw_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw CSV data from the specified path.

    Args:
        file_path: Path to CSV file. Defaults to main dataset.

    Returns:
        Raw DataFrame with original data.

    Raises:
        FileNotFoundError: If the data file doesn't exist.
    """
    if file_path is None:
        file_path = RAW_DATA_PATH / MAIN_DATASET

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading raw data from: {file_path}")

    df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Date range: {df['Year'].min()} - {df['Year'].max()}")
    logger.info(f"Entities: {df['Entity'].nunique()} unique causes of death")

    return df


def get_data_info(df: pd.DataFrame) -> dict:
    """
    Get summary information about the dataset.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with data summary statistics.
    """
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "year_range": (int(df["Year"].min()), int(df["Year"].max())),
        "entities": sorted(df["Entity"].unique().tolist()),
        "entity_count": df["Entity"].nunique(),
        "missing_values": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


if __name__ == "__main__":
    # Quick test
    df = load_raw_data()
    info = get_data_info(df)
    print(f"\nDataset Summary:")
    print(f"  Rows: {info['row_count']:,}")
    print(f"  Years: {info['year_range'][0]} - {info['year_range'][1]}")
    print(f"  Causes: {info['entity_count']}")
    print(f"\nCauses of death tracked:")
    for entity in info["entities"]:
        print(f"    - {entity}")
