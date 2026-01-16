"""Gender Wage Gap analysis module."""

from .pipeline import run_gender_wage_gap_pipeline
from .database import GenderWageGapDatabase

__all__ = ["run_gender_wage_gap_pipeline", "GenderWageGapDatabase"]
