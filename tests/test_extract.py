"""Tests for data extraction module."""

import pytest
import pandas as pd
from pathlib import Path

from src.extract.loader import load_raw_data, get_data_info


class TestLoadRawData:
    """Tests for the load_raw_data function."""

    def test_load_returns_dataframe(self):
        """Should return a pandas DataFrame."""
        df = load_raw_data()
        assert isinstance(df, pd.DataFrame)

    def test_load_has_expected_columns(self):
        """Should have all expected columns."""
        df = load_raw_data()
        expected_cols = [
            "Entity",
            "Year",
            "Share of deaths",
            "Share of Google searches",
            "Share of NYT media coverage",
            "Share of Guardian media coverage",
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_load_has_expected_row_count(self):
        """Should have expected number of rows (13 causes * 18 years = 234)."""
        df = load_raw_data()
        assert len(df) == 234, f"Expected 234 rows, got {len(df)}"

    def test_load_has_expected_entities(self):
        """Should have exactly 13 causes of death."""
        df = load_raw_data()
        assert df["Entity"].nunique() == 13

    def test_load_year_range(self):
        """Should cover years 1999-2016."""
        df = load_raw_data()
        assert df["Year"].min() == 1999
        assert df["Year"].max() == 2016

    def test_load_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_raw_data(tmp_path / "nonexistent.csv")


class TestGetDataInfo:
    """Tests for the get_data_info function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        df = load_raw_data()
        info = get_data_info(df)
        assert isinstance(info, dict)

    def test_contains_expected_keys(self):
        """Should contain all expected keys."""
        df = load_raw_data()
        info = get_data_info(df)

        expected_keys = [
            "row_count",
            "column_count",
            "columns",
            "year_range",
            "entities",
            "entity_count",
            "missing_values",
            "dtypes",
        ]
        for key in expected_keys:
            assert key in info, f"Missing key: {key}"

    def test_row_count_matches(self):
        """Row count should match DataFrame length."""
        df = load_raw_data()
        info = get_data_info(df)
        assert info["row_count"] == len(df)

    def test_year_range_tuple(self):
        """Year range should be a tuple of two integers."""
        df = load_raw_data()
        info = get_data_info(df)
        assert isinstance(info["year_range"], tuple)
        assert len(info["year_range"]) == 2
        assert all(isinstance(y, int) for y in info["year_range"])
