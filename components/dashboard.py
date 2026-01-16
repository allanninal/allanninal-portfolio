"""
Reusable dashboard components for Streamlit pages.

This module provides common UI patterns used across all dashboard pages,
reducing code duplication and ensuring consistent styling.

Usage:
    from components.dashboard import (
        setup_page, render_hero_stats, render_research_studies,
        render_quiz_section, render_technical_section, render_data_footer,
        render_site_header, render_site_footer
    )
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class HeroStat:
    """Configuration for a hero stat card."""
    value: str
    label: str
    gradient: str = "var(--gradient-primary)"  # or "danger", "warning", "success"


@dataclass
class ResearchStudy:
    """Configuration for a research study card."""
    icon: str
    title: str
    finding: str
    implication: str


@dataclass
class QuizQuestion:
    """Configuration for a quiz question."""
    option_a: str
    option_b: str
    data_column: str = "avg_share_media"  # Column to compare


# =============================================================================
# PAGE CSS - Common styles for dashboard pages
# =============================================================================

def get_page_css() -> str:
    """Return common CSS for dashboard pages."""
    return """
<style>
    /* Hero stat cards */
    .hero-stat {
        background: var(--gradient-primary);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        text-align: center;
        color: white;
        margin-bottom: 1rem;
    }
    .hero-stat.danger {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .hero-stat.warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    .hero-stat.success {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }
    .hero-stat.secondary {
        background: var(--gradient-secondary);
    }
    .hero-stat-number {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        color: #ffffff !important;
    }
    .hero-stat-label {
        font-size: 0.9rem;
        margin-top: 0.5rem;
        color: rgba(255, 255, 255, 0.95) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }

    /* Shocking fact callout */
    .shocking-fact {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: var(--radius-lg);
        padding: 2rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    .shocking-fact h2 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 800;
    }
    .shocking-fact p {
        font-size: 1.1rem;
        margin: 1rem 0 0 0;
        opacity: 0.95;
    }
    .shocking-fact.primary {
        background: var(--gradient-primary);
    }
    .shocking-fact.warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }

    /* Comparison cards */
    .compare-card {
        background: var(--card);
        border: 2px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .compare-card:hover {
        border-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    .compare-card.over {
        border-color: var(--danger);
        background: var(--danger-light);
    }
    .compare-card.under {
        border-color: var(--success);
        background: var(--success-light);
    }

    /* Research study cards */
    .research-study {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 2px solid #3b82f6;
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .research-study h4 {
        color: #1e40af;
        margin-top: 0;
    }
    .research-study p {
        margin-bottom: 0.5rem;
    }

    /* Quiz styling */
    .quiz-container {
        background: var(--primary-10);
        border: 2px solid var(--primary);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin: 1rem 0;
    }

    /* Correlation insight boxes */
    .correlation-box {
        padding: 1rem;
        border-radius: var(--radius-md);
        margin: 0.5rem 0;
    }
    .correlation-box.danger {
        background: #fee2e2;
    }
    .correlation-box.success {
        background: #dcfce7;
    }
    .correlation-box.warning {
        background: #fef3c7;
    }

    /* Insight boxes */
    .insight-box {
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .insight-box h4 {
        margin-top: 0;
    }
</style>
"""


# =============================================================================
# PAGE SETUP
# =============================================================================

def setup_page(
    title: str,
    icon: str = "📊",
    tech_tags: List[str] = None
) -> None:
    """
    Set up a dashboard page with common configuration.

    Args:
        title: Page title for browser tab.
        icon: Page icon emoji.
        tech_tags: List of technology tags for sidebar.
    """
    from src.shared.theme import apply_theme, render_sidebar_nav, render_tech_tags

    # Apply theme
    apply_theme()

    # Add page-specific CSS
    st.markdown(get_page_css(), unsafe_allow_html=True)

    # Setup sidebar
    with st.sidebar:
        render_sidebar_nav()
        st.divider()
        if tech_tags:
            render_tech_tags(tech_tags)


# =============================================================================
# DATA LOADING WITH ERROR HANDLING
# =============================================================================

def load_data_with_error_handling(
    db_class: Type,
    db_path: Path,
    get_methods: List[str],
    pipeline_command: str = "python -m src.pipeline"
) -> Tuple:
    """
    Load data from database with proper error handling.

    Args:
        db_class: Database class to instantiate.
        db_path: Path to the DuckDB file.
        get_methods: List of method names to call on db instance.
        pipeline_command: Command to show if database not found.

    Returns:
        Tuple of DataFrames from get_methods.

    Raises:
        st.stop(): If database not found or error occurs.
    """
    if not db_path.exists():
        st.error(f"Database not found at `{db_path}`")
        st.info(f"Run the pipeline first: `{pipeline_command}`")
        st.stop()

    try:
        with db_class(db_path) as db:
            results = []
            for method_name in get_methods:
                method = getattr(db, method_name)
                results.append(method())
            return tuple(results) if len(results) > 1 else results[0]
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info(f"Try running: `{pipeline_command}`")
        st.stop()


# =============================================================================
# HERO SECTIONS
# =============================================================================

def render_hero_header(
    title: str,
    subtitle: str,
    data_badge: str = None
) -> None:
    """
    Render the hero header section.

    Args:
        title: Main page title.
        subtitle: Subtitle/tagline.
        data_badge: Optional data period badge text.
    """
    st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)

    if data_badge:
        st.markdown(f"""
        <div class="data-badge">{data_badge}</div>
        """, unsafe_allow_html=True)


def render_hero_stats(stats: List[HeroStat]) -> None:
    """
    Render hero stat cards in columns.

    Args:
        stats: List of HeroStat configurations.
    """
    cols = st.columns(len(stats))

    for col, stat in zip(cols, stats):
        # Determine CSS class based on gradient
        css_class = ""
        if stat.gradient == "danger":
            css_class = "danger"
        elif stat.gradient == "warning":
            css_class = "warning"
        elif stat.gradient == "success":
            css_class = "success"
        elif stat.gradient == "secondary":
            css_class = "secondary"

        with col:
            st.markdown(f"""
            <div class="hero-stat {css_class}">
                <div class="hero-stat-number">{stat.value}</div>
                <div class="hero-stat-label">{stat.label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_shocking_fact(
    value: str,
    description: str,
    style: str = "danger"
) -> None:
    """
    Render a shocking fact callout banner.

    Args:
        value: The main statistic/value to display.
        description: Description text.
        style: "danger" (red), "primary" (blue), or "warning" (orange).
    """
    st.markdown(f"""
    <div class="shocking-fact {style}">
        <h2>{value}</h2>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# RESEARCH SECTIONS
# =============================================================================

def render_research_study(study: ResearchStudy) -> None:
    """
    Render a single research study card.

    Args:
        study: ResearchStudy configuration.
    """
    st.markdown(f"""
    <div class="research-study">
        <h4>{study.icon} {study.title}</h4>
        <p><b>Finding:</b> {study.finding}</p>
        <p><b>Implication:</b> {study.implication}</p>
    </div>
    """, unsafe_allow_html=True)


def render_research_studies(studies: List[ResearchStudy]) -> None:
    """
    Render multiple research study cards.

    Args:
        studies: List of ResearchStudy configurations.
    """
    st.markdown("### Research Study Results")
    for study in studies:
        render_research_study(study)


def render_correlation_insight(
    title: str,
    description: str,
    style: str = "danger"
) -> None:
    """
    Render a correlation insight box.

    Args:
        title: Correlation title (e.g., "Deaths ↔ NYT Coverage: 0.04").
        description: Description of what it means.
        style: "danger", "success", or "warning".
    """
    st.markdown(f"""
    <div class="correlation-box {style}">
        <strong>{title}</strong><br>
        <small>{description}</small>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# QUIZ SECTION
# =============================================================================

def render_quiz_section(
    questions: List[Tuple[str, str]],
    data: pd.DataFrame,
    name_column: str = "cause_name",
    value_column: str = "avg_share_media",
    title: str = "Test Your Perception",
    prompt: str = "Can you guess which gets more coverage?"
) -> None:
    """
    Render an interactive quiz section.

    Args:
        questions: List of (option_a, option_b) tuples.
        data: DataFrame containing the comparison data.
        name_column: Column name for entity names.
        value_column: Column name for values to compare.
        title: Quiz section title.
        prompt: Quiz prompt text.
    """
    st.markdown(f"## Quiz: {title}")

    st.markdown(f"""
    <div class="quiz-container">
        <h3>{prompt}</h3>
    </div>
    """, unsafe_allow_html=True)

    for option_a, option_b in questions:
        try:
            value_a = data[data[name_column] == option_a][value_column].iloc[0]
            value_b = data[data[name_column] == option_b][value_column].iloc[0]
        except (IndexError, KeyError):
            continue

        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            if st.button(f"A: {option_a}", key=f"quiz_{option_a}_{option_b}_a", use_container_width=True):
                if value_a > value_b:
                    st.success(f"Correct! {option_a}: {value_a:.1f}%")
                else:
                    st.error(f"Actually, {option_b} is higher ({value_b:.1f}% vs {value_a:.1f}%)")

        with col2:
            st.markdown("<div style='text-align: center; font-size: 1.5rem; padding-top: 0.5rem;'>vs</div>", unsafe_allow_html=True)

        with col3:
            if st.button(f"B: {option_b}", key=f"quiz_{option_a}_{option_b}_b", use_container_width=True):
                if value_b > value_a:
                    st.success(f"Correct! {option_b}: {value_b:.1f}%")
                else:
                    st.error(f"Actually, {option_a} is higher ({value_a:.1f}% vs {value_b:.1f}%)")


# =============================================================================
# COMPARISON CARDS
# =============================================================================

def render_compare_cards(
    items: List[Dict[str, Any]],
    threshold_over: float = 5,
    threshold_under: float = -5
) -> None:
    """
    Render comparison cards for two items.

    Args:
        items: List of dicts with 'name', 'deaths', 'media', 'gap' keys.
        threshold_over: Gap threshold for "over" styling.
        threshold_under: Gap threshold for "under" styling.
    """
    cols = st.columns(len(items))

    for col, item in zip(cols, items):
        gap = item.get('gap', 0)
        css_class = ""
        if gap > threshold_over:
            css_class = "over"
        elif gap < threshold_under:
            css_class = "under"

        with col:
            st.markdown(f"""
            <div class="compare-card {css_class}">
                <h3>{item['name']}</h3>
                <p><strong>Deaths:</strong> {item['deaths']:.1f}%</p>
                <p><strong>Media:</strong> {item['media']:.1f}%</p>
                <p><strong>Gap:</strong> {item['gap']:+.1f}%</p>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# TECHNICAL SECTIONS
# =============================================================================

def render_pipeline_architecture(
    stages: List[Tuple[str, List[str]]] = None,
    features: List[str] = None
) -> None:
    """
    Render the data pipeline architecture expander.

    Args:
        stages: List of (stage_name, [bullet_points]) tuples.
        features: List of key features.
    """
    if stages is None:
        stages = [
            ("EXTRACT", ["CSV Load", "Validate", "Schema"]),
            ("TRANSFORM", ["Clean", "Enrich", "Calculate"]),
            ("LOAD", ["DuckDB", "Star Schema", "Views"]),
        ]

    if features is None:
        features = [
            "Modular, testable components",
            "Data validation at each stage",
            "Comprehensive logging",
        ]

    with st.expander("🔧 Data Pipeline Architecture", expanded=False):
        # Visual pipeline stages
        st.markdown("""
        <div style="display: flex; justify-content: space-between; gap: 1rem; margin: 1rem 0;">
            <div style="flex: 1; background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); border-radius: 12px; padding: 1rem; color: white; text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📥</div>
                <div style="font-weight: 700; font-size: 0.9rem;">EXTRACT</div>
                <div style="font-size: 0.75rem; opacity: 0.9; margin-top: 0.5rem;">CSV Load • Validate • Schema</div>
            </div>
            <div style="flex: 1; background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); border-radius: 12px; padding: 1rem; color: white; text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚙️</div>
                <div style="font-weight: 700; font-size: 0.9rem;">TRANSFORM</div>
                <div style="font-size: 0.75rem; opacity: 0.9; margin-top: 0.5rem;">Clean • Enrich • Calculate</div>
            </div>
            <div style="flex: 1; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); border-radius: 12px; padding: 1rem; color: white; text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💾</div>
                <div style="font-weight: 700; font-size: 0.9rem;">LOAD</div>
                <div style="font-size: 0.75rem; opacity: 0.9; margin-top: 0.5rem;">DuckDB • Star Schema • Views</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Features list
        st.markdown("**Key Features:**")
        for feature in features:
            st.markdown(f"✅ {feature}")

        st.markdown("""
        ```
                              │
                              ▼
        ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
        │   EXTRACT   │─▶│  TRANSFORM  │─▶│    LOAD     │
        └─────────────┘  └─────────────┘  └─────────────┘
        ```

        **Key Features:**
        """ + "\n".join([f"- {f}" for f in features]))


def render_database_schema(
    schema_diagram: str,
    why_text: str = None
) -> None:
    """
    Render the database schema expander.

    Args:
        schema_diagram: ASCII diagram of schema.
        why_text: Explanation of why this schema was chosen.
    """
    with st.expander("🗄️ Database Schema", expanded=False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #cbd5e1; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;">⭐ Star Schema Design</div>
            <div style="font-size: 0.85rem; color: #64748b;">Optimized for analytical queries with dimension and fact tables</div>
        </div>
        """, unsafe_allow_html=True)

        st.code(schema_diagram, language="text")

        if why_text:
            st.markdown(f"""
            **Why This Design?**
            {why_text}
            """)


def render_sample_queries(queries: str) -> None:
    """
    Render sample SQL queries expander.

    Args:
        queries: SQL code to display.
    """
    with st.expander("📝 Sample SQL Queries", expanded=False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-weight: 600; color: #92400e; margin-bottom: 0.5rem;">💡 Try These Queries</div>
            <div style="font-size: 0.85rem; color: #a16207;">Copy and run in DuckDB to explore the data yourself</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(queries, language="sql")


def render_technical_section(
    schema_diagram: str = None,
    sample_queries: str = None,
    features: List[str] = None
) -> None:
    """
    Render the complete technical section with pipeline, schema, and queries.

    Args:
        schema_diagram: ASCII diagram for schema.
        sample_queries: SQL queries to show.
        features: List of key features.
    """
    st.markdown("## Technical Deep Dive")

    col1, col2 = st.columns(2)

    with col1:
        render_pipeline_architecture(features=features)

    with col2:
        if schema_diagram:
            render_database_schema(schema_diagram)

    if sample_queries:
        render_sample_queries(sample_queries)


# =============================================================================
# FOOTER
# =============================================================================

def render_data_footer(
    data_sources: List[str],
    time_period: str,
    data_points: str,
    credits: Dict[str, str] = None,
    dataset_url: str = None
) -> None:
    """
    Render the data footer section.

    Args:
        data_sources: List of data source names.
        time_period: Time period description.
        data_points: Data points description.
        credits: Dict of credit_name: credit_url.
        dataset_url: URL for page footer link.
    """
    from src.shared.theme import render_page_footer

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Data Sources:**")
        for source in data_sources:
            st.markdown(f"- {source}")

    with col2:
        st.markdown(f"""
        **Time Period:**
        {time_period}

        **Data Points:**
        {data_points}
        """)

    with col3:
        if credits:
            st.markdown("**Credits:**")
            for name, url in credits.items():
                if url:
                    st.markdown(f"- [{name}]({url})")
                else:
                    st.markdown(f"- {name}")

    if dataset_url:
        render_page_footer(dataset_url)


# =============================================================================
# SITE HEADER AND FOOTER
# =============================================================================

def render_site_header() -> None:
    """
    Render a consistent site header for project pages.
    Shows navigation back to home and portfolio branding.
    """
    header_cols = st.columns([1, 4, 1])

    with header_cols[0]:
        st.page_link("Home.py", label="← Home", icon="🏠")

    with header_cols[2]:
        st.markdown(
            "[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/allanninal)"
        )


def render_site_footer() -> None:
    """
    Render a consistent site footer for project pages.
    Clean white design using native Streamlit components.
    """
    st.markdown("---")

    footer_cols = st.columns([2, 1, 1, 1.5])

    with footer_cols[0]:
        st.markdown("### Allan Ninal")
        st.markdown("""
        AI Engineer passionate about data analytics and uncovering insights from global datasets.
        """)
        st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/allanninal) [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/allanninal)")

    with footer_cols[1]:
        st.markdown("**Data Projects**")
        st.page_link("pages/2_Media_Perception.py", label="Media Perception")
        st.page_link("pages/4_World_Happiness.py", label="World Happiness")
        st.page_link("pages/21_Suicide_Rates.py", label="Suicide Rates")

    with footer_cols[2]:
        st.markdown("**More Projects**")
        st.page_link("pages/6_Life_Expectancy.py", label="Life Expectancy")
        st.page_link("pages/10_Food_Affordability.py", label="Food Affordability")
        st.page_link("pages/19_CO2_Emissions.py", label="CO2 Emissions")

    with footer_cols[3]:
        st.markdown("**Get in Touch**")
        st.link_button("Connect on LinkedIn", "https://linkedin.com/in/allanninal", type="primary")
        st.link_button("View GitHub", "https://github.com/allanninal")

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.875rem;'>Built with Streamlit &bull; 2025 Allan Ninal</p>", unsafe_allow_html=True)
