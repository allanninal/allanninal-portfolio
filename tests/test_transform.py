"""Tests for data transformation module."""

import pytest
import pandas as pd
import numpy as np

from src.extract.loader import load_raw_data
from src.transform.cleaner import clean_data, validate_data, EXPECTED_CAUSES
from src.transform.enricher import calculate_coverage_gap, add_derived_metrics, create_summary_stats


@pytest.fixture
def raw_data():
    """Load raw data for tests."""
    return load_raw_data()


@pytest.fixture
def clean_data_fixture(raw_data):
    """Clean data for tests."""
    return clean_data(raw_data)


@pytest.fixture
def enriched_data(clean_data_fixture):
    """Enriched data for tests."""
    df = calculate_coverage_gap(clean_data_fixture)
    return add_derived_metrics(df)


class TestCleanData:
    """Tests for the clean_data function."""

    def test_returns_dataframe(self, raw_data):
        """Should return a pandas DataFrame."""
        df = clean_data(raw_data)
        assert isinstance(df, pd.DataFrame)

    def test_columns_renamed(self, raw_data):
        """Columns should be renamed to snake_case."""
        df = clean_data(raw_data)
        expected_cols = ["cause", "year", "share_deaths", "share_google", "share_nyt", "share_guardian"]
        for col in expected_cols:
            assert col in df.columns, f"Missing renamed column: {col}"

    def test_year_is_integer(self, raw_data):
        """Year column should be integer type."""
        df = clean_data(raw_data)
        assert df["year"].dtype == int

    def test_preserves_row_count(self, raw_data):
        """Should preserve the number of rows."""
        df = clean_data(raw_data)
        assert len(df) == len(raw_data)

    def test_data_is_sorted(self, raw_data):
        """Data should be sorted by cause and year."""
        df = clean_data(raw_data)
        is_sorted = (df["cause"] + df["year"].astype(str)).is_monotonic_increasing
        # Note: this is cause-wise monotonic
        for cause in df["cause"].unique():
            cause_years = df[df["cause"] == cause]["year"]
            assert cause_years.is_monotonic_increasing


class TestValidateData:
    """Tests for the validate_data function."""

    def test_validation_passes(self, clean_data_fixture):
        """Validation should pass for clean data."""
        result = validate_data(clean_data_fixture)
        assert result.is_valid is True

    def test_returns_validation_result(self, clean_data_fixture):
        """Should return a ValidationResult object."""
        result = validate_data(clean_data_fixture)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "stats")

    def test_all_causes_present(self, clean_data_fixture):
        """All expected causes should be present."""
        actual_causes = set(clean_data_fixture["cause"].unique())
        expected_causes = set(EXPECTED_CAUSES)
        assert actual_causes == expected_causes

    def test_share_values_in_range(self, clean_data_fixture):
        """Share values should be between 0 and 100."""
        share_cols = ["share_deaths", "share_nyt", "share_guardian"]
        for col in share_cols:
            values = clean_data_fixture[col].dropna()
            assert (values >= 0).all(), f"{col} has negative values"
            assert (values <= 100).all(), f"{col} has values > 100"


class TestCoverageGap:
    """Tests for the calculate_coverage_gap function."""

    def test_adds_gap_columns(self, clean_data_fixture):
        """Should add gap calculation columns."""
        df = calculate_coverage_gap(clean_data_fixture)
        expected_cols = ["gap_nyt", "gap_guardian", "gap_media_avg", "gap_google"]
        for col in expected_cols:
            assert col in df.columns, f"Missing gap column: {col}"

    def test_gap_calculation_correct(self, clean_data_fixture):
        """Gap should equal coverage minus deaths."""
        df = calculate_coverage_gap(clean_data_fixture)
        # Check a few random rows
        sample = df.dropna(subset=["gap_nyt"]).sample(min(10, len(df)))
        for _, row in sample.iterrows():
            expected_gap = row["share_nyt"] - row["share_deaths"]
            assert abs(row["gap_nyt"] - expected_gap) < 0.001

    def test_adds_ratio_columns(self, clean_data_fixture):
        """Should add coverage ratio columns."""
        df = calculate_coverage_gap(clean_data_fixture)
        assert "ratio_nyt" in df.columns
        assert "ratio_guardian" in df.columns


class TestDerivedMetrics:
    """Tests for the add_derived_metrics function."""

    def test_adds_category(self, enriched_data):
        """Should add category classification."""
        assert "category" in enriched_data.columns
        assert enriched_data["category"].notna().all()

    def test_valid_categories(self, enriched_data):
        """Categories should be from expected set."""
        valid_categories = {"chronic_disease", "infectious_disease", "behavioral", "accidents", "violence"}
        actual_categories = set(enriched_data["category"].unique())
        assert actual_categories.issubset(valid_categories)

    def test_adds_coverage_flags(self, enriched_data):
        """Should add over/under coverage flags."""
        assert "is_over_covered" in enriched_data.columns
        assert "is_under_covered" in enriched_data.columns
        assert enriched_data["is_over_covered"].dtype == bool
        assert enriched_data["is_under_covered"].dtype == bool

    def test_adds_attention_score(self, enriched_data):
        """Should add attention score (absolute gap)."""
        assert "attention_score" in enriched_data.columns
        assert (enriched_data["attention_score"] >= 0).all()


class TestCreateSummary:
    """Tests for the create_summary_stats function."""

    def test_returns_one_row_per_cause(self, enriched_data):
        """Summary should have one row per cause."""
        summary = create_summary_stats(enriched_data)
        assert len(summary) == 13

    def test_contains_aggregated_stats(self, enriched_data):
        """Summary should contain aggregated statistics."""
        summary = create_summary_stats(enriched_data)
        expected_cols = ["share_deaths_mean", "gap_media_avg_mean", "category_first"]
        for col in expected_cols:
            assert col in summary.columns, f"Missing summary column: {col}"

    def test_adds_rankings(self, enriched_data):
        """Summary should include ranking columns."""
        summary = create_summary_stats(enriched_data)
        assert "death_rank" in summary.columns
        assert "coverage_rank" in summary.columns
