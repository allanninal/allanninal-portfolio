"""
Reusable dashboard components for Streamlit pages.

This module provides common UI patterns used across dashboard pages,
reducing code duplication and ensuring consistent styling.

Example usage:
    from components import (
        setup_page, render_hero_stats, HeroStat,
        render_research_studies, ResearchStudy,
        render_quiz_section, render_data_footer
    )

    # Setup page with theme
    setup_page("My Dashboard", tech_tags=["Python", "DuckDB"])

    # Render hero stats
    render_hero_stats([
        HeroStat("1M", "Total Records"),
        HeroStat("50", "Countries", gradient="success"),
    ])
"""

from .dashboard import (
    # Data classes
    HeroStat,
    ResearchStudy,
    QuizQuestion,
    # Page setup
    setup_page,
    get_page_css,
    # Hero sections
    render_hero_header,
    render_hero_stats,
    render_shocking_fact,
    # Content sections
    render_research_study,
    render_research_studies,
    render_correlation_insight,
    render_quiz_section,
    render_compare_cards,
    # Technical sections
    render_pipeline_architecture,
    render_database_schema,
    render_sample_queries,
    render_technical_section,
    # Footer
    render_data_footer,
    # Data loading
    load_data_with_error_handling,
)

# Legacy styles module
from .styles import COMMON_CSS, inject_css

__all__ = [
    # Data classes
    "HeroStat",
    "ResearchStudy",
    "QuizQuestion",
    # Page setup
    "setup_page",
    "get_page_css",
    # Hero sections
    "render_hero_header",
    "render_hero_stats",
    "render_shocking_fact",
    # Content sections
    "render_research_study",
    "render_research_studies",
    "render_correlation_insight",
    "render_quiz_section",
    "render_compare_cards",
    # Technical sections
    "render_pipeline_architecture",
    "render_database_schema",
    "render_sample_queries",
    "render_technical_section",
    # Footer
    "render_data_footer",
    # Data loading
    "load_data_with_error_handling",
    # Legacy
    "COMMON_CSS",
    "inject_css",
]
