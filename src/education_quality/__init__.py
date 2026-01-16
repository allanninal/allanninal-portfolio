"""Education Quality analysis module."""

from .pipeline import run_education_quality_pipeline
from .database import EducationQualityDatabase

__all__ = ["run_education_quality_pipeline", "EducationQualityDatabase"]
