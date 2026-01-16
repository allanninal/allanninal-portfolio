"""Gini Coefficients analysis module."""

from .pipeline import run_gini_coefficients_pipeline
from .database import GiniCoefficientsDatabase

__all__ = ["run_gini_coefficients_pipeline", "GiniCoefficientsDatabase"]
