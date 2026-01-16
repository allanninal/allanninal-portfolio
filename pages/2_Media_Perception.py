"""
Media Perception vs Reality - Project Page

A data engineering and analysis project exploring the disconnect between
causes of death and their representation in media coverage.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database import DatabaseManager
from src.analysis import (
    get_perception_gap_ranking,
    get_terrorism_911_impact,
    get_heart_disease_paradox,
    get_violence_vs_disease_comparison,
    get_key_statistics,
)
from components import (
    setup_page,
    render_hero_header,
    render_hero_stats,
    render_shocking_fact,
    render_research_studies,
    render_quiz_section,
    render_technical_section,
    render_data_footer,
    render_compare_cards,
    render_correlation_insight,
    render_site_header,
    render_site_footer,
    HeroStat,
    ResearchStudy,
    load_data_with_error_handling,
)

# Page configuration
st.set_page_config(
    page_title="Media Perception vs Reality | Allan Niñal",
    page_icon="📊",
    layout="wide",
)

# Setup page with theme and sidebar
setup_page("Media Perception vs Reality", icon="📊", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()


@st.cache_data(ttl=3600)
def load_data():
    """Load data from database with caching."""
    db_path = Path(__file__).parent.parent / "data" / "media_perception.duckdb"
    return load_data_with_error_handling(
        db_class=DatabaseManager,
        db_path=db_path,
        get_methods=["get_full_data", "get_cause_summary"],
        pipeline_command="python -m src.pipeline"
    )


# =============================================================================
# VISUALIZATIONS
# =============================================================================

def create_animated_bar_chart(summary: pd.DataFrame) -> go.Figure:
    """Create an enhanced perception gap chart."""
    df = summary.copy()
    df = df.sort_values("avg_gap", ascending=True)

    colors = []
    for x in df["avg_gap"]:
        if x > 20:
            colors.append("#dc2626")
        elif x > 5:
            colors.append("#ef4444")
        elif x < -20:
            colors.append("#16a34a")
        elif x < -5:
            colors.append("#22c55e")
        else:
            colors.append("#94a3b8")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["cause_name"],
        x=df["avg_gap"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=[f"{x:+.1f}%" for x in df["avg_gap"]],
        textposition="outside",
        textfont=dict(size=12, color="#374151"),
        hovertemplate="<b>%{y}</b><br>Gap: <b>%{x:+.1f}%</b><br><extra></extra>",
    ))

    fig.add_vline(x=0, line_dash="solid", line_color="#374151", line_width=2)
    fig.add_vrect(x0=5, x1=50, fillcolor="#fee2e2", opacity=0.3, layer="below", line_width=0)
    fig.add_vrect(x0=-50, x1=-5, fillcolor="#dcfce7", opacity=0.3, layer="below", line_width=0)

    fig.update_layout(
        title=dict(text="<b>The Perception Gap</b><br><sup>Media Coverage % minus Death Share %</sup>", font=dict(size=18)),
        xaxis=dict(title="← Under-covered | Over-covered →", gridcolor="#e5e7eb", range=[-35, 45], zeroline=False),
        yaxis=dict(title=""),
        height=550,
        margin=dict(l=20, r=80, t=80, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def create_treemap(summary: pd.DataFrame) -> go.Figure:
    """Create a treemap showing relative proportions."""
    fig = go.Figure(go.Treemap(
        labels=summary["cause_name"],
        parents=[""] * len(summary),
        values=summary["avg_share_deaths"],
        textinfo="label+percent root",
        marker=dict(colors=summary["avg_gap"], colorscale="RdYlGn_r", showscale=True, colorbar=dict(title="Gap %")),
        hovertemplate="<b>%{label}</b><br>Deaths: %{value:.1f}%<br>Media Gap: %{color:+.1f}%<br><extra></extra>",
    ))
    fig.update_layout(title="What Actually Kills Us (sized by death share, colored by media gap)", height=450, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def create_heatmap(data: pd.DataFrame) -> go.Figure:
    """Create a year vs cause heatmap."""
    pivot = data.pivot(index="cause_name", columns="year", values="gap_media_avg")
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale="RdYlGn_r", zmid=0,
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Gap: %{z:+.1f}%<extra></extra>",
    ))
    fig.update_layout(title="Coverage Gap Over Time (red = over-covered, green = under-covered)", xaxis_title="Year", yaxis_title="", height=500)
    fig.add_vline(x=2001, line_dash="dash", line_color="black", annotation_text="9/11")
    return fig


def create_comparison_chart(data: pd.DataFrame, cause1: str, cause2: str) -> go.Figure:
    """Create a side-by-side comparison of two causes."""
    df1 = data[data["cause_name"] == cause1]
    df2 = data[data["cause_name"] == cause2]

    fig = make_subplots(rows=2, cols=2, subplot_titles=(f"{cause1} - Coverage", f"{cause2} - Coverage", f"{cause1} - Gap", f"{cause2} - Gap"), vertical_spacing=0.15)

    for df, col, name in [(df1, 1, cause1), (df2, 2, cause2)]:
        fig.add_trace(go.Scatter(x=df["year"], y=df["share_deaths"], name="Deaths", line=dict(color="#22c55e", width=2), showlegend=(col==1)), row=1, col=col)
        fig.add_trace(go.Scatter(x=df["year"], y=df["share_media_avg"], name="Media", line=dict(color="#ef4444", width=2), showlegend=(col==1)), row=1, col=col)

    for df, col in [(df1, 1), (df2, 2)]:
        colors = ["#ef4444" if x > 0 else "#22c55e" for x in df["gap_media_avg"]]
        fig.add_trace(go.Bar(x=df["year"], y=df["gap_media_avg"], marker_color=colors, showlegend=False), row=2, col=col)

    fig.update_layout(height=600, plot_bgcolor="white")
    return fig


# =============================================================================
# MAIN CONTENT
# =============================================================================

# Load data
full_data, summary = load_data()

# Hero Section
render_hero_header(
    title="Media Perception vs Reality",
    subtitle="What if the news we consume doesn't reflect reality?",
    data_badge="📅 Data: 1999 - 2016 | 18 years | 13 causes | 234 data points"
)

# Shocking fact banner
terrorism_deaths = summary[summary["cause_name"] == "Terrorism"]["avg_share_deaths"].values[0]
terrorism_media = summary[summary["cause_name"] == "Terrorism"]["avg_share_media"].values[0]
terrorism_ratio = terrorism_media / terrorism_deaths if terrorism_deaths > 0 else 4000

render_shocking_fact(
    value=f"{terrorism_ratio:,.0f}x",
    description=f"Terrorism receives <b>{terrorism_ratio:,.0f} times more</b> media coverage than its actual death toll warrants.<br>Meanwhile, heart disease (the #1 killer) gets only 10% of fair coverage.",
    style="danger"
)

st.markdown("---")

# The Problem section
st.markdown("## The Problem")

render_hero_stats([
    HeroStat("28%", "of deaths from Heart Disease<br>(#1 killer)"),
    HeroStat("3%", "media coverage for<br>Heart Disease", gradient="danger"),
    HeroStat("-25%", "coverage gap<br>(massively under-reported)", gradient="warning"),
])

st.markdown("""
This project analyzes **18 years of data** (1999-2016) comparing:
- **CDC mortality data** - What actually kills Americans
- **NYT & Guardian articles** - What media covers
- **Google Trends** - What people search for

The results reveal a shocking disconnect between reality and perception.
""")

st.markdown("---")

# Interactive Explorer
st.markdown("## Interactive Explorer")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gap Analysis", "🗺️ Treemap", "🔥 Heatmap", "⚖️ Compare", "🔬 Research Findings"])

with tab1:
    st.plotly_chart(create_animated_bar_chart(summary), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔴 Over-covered (red bars)**\n- These causes get MORE media attention than deaths warrant\n- Terrorism: ~0% of deaths, ~30% of coverage\n- Creates irrational fear")
    with col2:
        st.markdown("**🟢 Under-covered (green bars)**\n- These causes get LESS media attention than deaths warrant\n- Heart disease: ~28% of deaths, ~3% of coverage\n- Hidden killers")

with tab2:
    st.plotly_chart(create_treemap(summary), use_container_width=True)
    st.caption("Box size = share of deaths. Color = media gap (red = over-covered, green = under-covered)")

with tab3:
    st.plotly_chart(create_heatmap(full_data), use_container_width=True)
    st.markdown("**Notable patterns:**\n- Terrorism coverage spikes after 9/11 (2001) and stays elevated\n- Heart disease consistently under-covered across all years\n- Homicide coverage remains high despite low death rates")

with tab4:
    st.markdown("### Compare Two Causes Side-by-Side")
    col1, col2 = st.columns(2)
    with col1:
        cause1 = st.selectbox("First cause:", sorted(full_data["cause_name"].unique()), index=4)
    with col2:
        cause2 = st.selectbox("Second cause:", sorted(full_data["cause_name"].unique()), index=12)

    if cause1 != cause2:
        st.plotly_chart(create_comparison_chart(full_data, cause1, cause2), use_container_width=True)
        stats1 = summary[summary["cause_name"] == cause1].iloc[0]
        stats2 = summary[summary["cause_name"] == cause2].iloc[0]
        render_compare_cards([
            {"name": cause1, "deaths": stats1['avg_share_deaths'], "media": stats1['avg_share_media'], "gap": stats1['avg_gap']},
            {"name": cause2, "deaths": stats2['avg_share_deaths'], "media": stats2['avg_share_media'], "gap": stats2['avg_gap']},
        ])
    else:
        st.warning("Select two different causes to compare")

with tab5:
    render_research_studies([
        ResearchStudy("📊", "Study 1: The Violence Amplification Effect",
            "Violence-related deaths (terrorism + homicide) account for only <b>0.8%</b> of total deaths but receive <b>52.6%</b> of media coverage - a <b>66x amplification factor</b>.",
            "Media systematically over-represents violent deaths, potentially contributing to public fear and misallocation of resources toward rare threats."),
        ResearchStudy("💔", "Study 2: The Hidden Killer Phenomenon",
            "Heart disease kills <b>27x more people</b> than terrorism annually, yet terrorism receives <b>10x more</b> media coverage. This creates a perception gap of <b>-26 percentage points</b> for heart disease.",
            "The leading cause of death in America receives less than 10% of proportional media attention, potentially reducing public awareness of prevention strategies."),
        ResearchStudy("📅", "Study 3: The 9/11 Media Shock & Displacement Effect",
            "In 2001, terrorism coverage jumped from 15.9% to 47.9% (+32 points) - the largest single-year change in the dataset. This <b>displaced coverage</b> of cancer (-12 points) and homicide (-10 points).",
            "Major events create lasting shifts in media attention that persist long after the event itself, affecting coverage of other important health issues."),
        ResearchStudy("🔍", "Study 4: Media-Search Synchronization",
            "Google search patterns correlate <b>0.42</b> with media coverage but only <b>0.04</b> with actual death rates.",
            "Media coverage shapes public health concerns more than reality. People search for what they see in the news, not what actually poses the greatest risk."),
        ResearchStudy("🏥", "Study 5: The Chronic Disease Blindspot",
            "Chronic diseases (heart disease, cancer, diabetes, stroke, etc.) cause <b>75%</b> of deaths but receive only <b>30%</b> of media coverage - a systematic <b>45-point under-representation</b>.",
            "Preventable chronic conditions that kill millions annually receive less than half their proportional coverage, potentially reducing public engagement with prevention and lifestyle changes."),
    ])

    st.markdown("### Key Correlations")
    col1, col2 = st.columns(2)
    with col1:
        render_correlation_insight("Deaths ↔ NYT Coverage: 0.04", "Almost NO relationship between what kills people and what gets covered!", "danger")
        render_correlation_insight("NYT ↔ Guardian: 0.96", "Media outlets cover nearly identical topics - echo chamber effect.", "success")
    with col2:
        render_correlation_insight("Google ↔ NYT: 0.42", "People search for what media covers, not what actually kills them.", "warning")
        render_correlation_insight("Deaths ↔ Guardian: -0.12", "Slight inverse relationship - more deaths = less coverage!", "danger")

    st.markdown("### Download Data")
    st.download_button(label="📥 Download Full Dataset (CSV)", data=full_data.to_csv(index=False), file_name="media_perception_data.csv", mime="text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[("Heart disease", "Terrorism"), ("Cancer", "Homicide"), ("Diabetes", "Drug overdose")],
    data=summary,
    name_column="cause_name",
    value_column="avg_share_media",
    title="Test Your Perception",
    prompt="🎯 Can you guess which cause gets more media coverage?"
)

st.markdown("---")

# Key Insights
st.markdown("## Key Insights")

try:
    insights = [
        (get_terrorism_911_impact, "🔴", "#fef2f2"),
        (get_heart_disease_paradox, "💔", "#f0fdf4"),
        (get_violence_vs_disease_comparison, "⚔️", "#faf5ff"),
    ]
    for insight_fn, icon, bg_color in insights:
        insight = insight_fn()
        st.markdown(f"""
        <div class="insight-box" style="background: {bg_color};">
            <h4>{icon} {insight.title}</h4>
            <p>{insight.description}</p>
            <p style="margin-top: 1rem;"><strong>📊 Key Stat:</strong> {insight.key_stat}</p>
        </div>
        """, unsafe_allow_html=True)
except Exception:
    st.info("Run the pipeline to generate insights: `python -m src.pipeline`")

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """dim_cause ──────┐
• cause_id (PK) │
• cause_name    │    fact_metrics
• category      ├───▶ • cause_id (FK)
                │    • year (FK)
dim_year ───────┤    • share_deaths
• year (PK)     │    • share_media
• period        │    • gap_media_avg
• is_post_911   ┘    • attention_score"""

SAMPLE_QUERIES = """-- Top over-covered causes
SELECT cause_name,
       ROUND(avg_share_deaths, 1) as deaths,
       ROUND(avg_share_media, 1) as media,
       ROUND(avg_gap, 1) as gap
FROM v_cause_summary
ORDER BY avg_gap DESC
LIMIT 5;

-- 9/11 impact on terrorism coverage
SELECT year,
       ROUND(share_deaths, 4) as deaths_pct,
       ROUND(share_media_avg, 1) as media_pct,
       ROUND(share_media_avg / NULLIF(share_deaths, 0), 0) as multiplier
FROM v_metrics_full
WHERE cause_name = 'Terrorism'
  AND year BETWEEN 2000 AND 2003;

-- Correlation between Google searches and media
SELECT cause_name,
       ROUND(CORR(share_google, share_nyt), 2) as google_nyt_corr
FROM v_metrics_full
WHERE share_google IS NOT NULL
GROUP BY cause_name;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Modular, testable components", "Data validation at each stage", "Comprehensive logging", "39 automated tests"]
)

# Footer
render_data_footer(
    data_sources=["CDC WONDER Database", "Google Trends", "NYT Article API", "The Guardian API"],
    time_period="1999 - 2016\n13 causes of death",
    data_points="234 data points",
    credits={"Research by Owen Shen": None, "Dataset: OWID": "https://github.com/owid/owid-datasets/tree/master/datasets/Causes%20of%20death%20vs.%20media%20coverage%20-%20Shen"},
    dataset_url="https://github.com/owid/owid-datasets/tree/master/datasets/Causes%20of%20death%20vs.%20media%20coverage%20-%20Shen"
)

# Site Footer
render_site_footer()
