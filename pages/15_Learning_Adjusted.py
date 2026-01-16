"""
Learning-Adjusted Years of Schooling Dashboard
Analyzing education quality across 157 countries (World Bank 2018)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.learning_adjusted.database import LearningAdjustedDatabase
from components.dashboard import (
    setup_page,
    render_hero_header,
    render_hero_stats,
    render_shocking_fact,
    render_research_studies,
    render_quiz_section,
    render_technical_section,
    render_data_footer,
    render_site_header,
    render_site_footer,
    HeroStat,
    ResearchStudy,
)

# Page config
st.set_page_config(
    page_title="Learning-Adjusted Years | Allan Ninal",
    page_icon="📚",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load learning-adjusted years data from database."""
    with LearningAdjustedDatabase() as db:
        full_data = db.get_full_data()
        region_summary = db.get_region_summary()
        income_summary = db.get_income_summary()
        tier_summary = db.get_tier_summary()
        top_countries = db.get_top_countries(20)
        bottom_countries = db.get_bottom_countries(20)
        stats = db.get_stats()
    return (full_data, region_summary, income_summary, tier_summary,
            top_countries, bottom_countries, stats)


# Load data
(full_data, region_summary, income_summary, tier_summary,
 top_countries, bottom_countries, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Learning-Adjusted Years", icon="📚", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Hero Header
render_hero_header(
    title="Learning-Adjusted Years of Schooling",
    subtitle="Measuring not just how long children stay in school, but how much they actually learn.",
    data_badge=f"📊 Data: {stats['countries']} Countries | World Bank Human Capital Index (2018)"
)

# Key insight banner
gap = round(stats['best_lays'] - stats['lowest_lays'], 1)
render_shocking_fact(
    value=f"{gap} years",
    description=f"The gap between the best and worst education systems spans <b>{gap} years</b> of learning-adjusted schooling. <b>{stats['best_country']}</b> leads with <b>{stats['best_lays']} years</b>, while <b>{stats['lowest_country']}</b> has only <b>{stats['lowest_lays']} years</b> of effective education.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['global_avg']}", "Global Average<br>Learning Years"),
    HeroStat(f"{stats['best_lays']}", f"{stats['best_country']}<br>World Leader", "success"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "secondary"),
    HeroStat(f"{stats['regions']}", "World Regions<br>Compared", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Rankings", "Regional Analysis", "Income Groups",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Rankings
with tab1:
    st.subheader("Top 20 Countries by Learning-Adjusted Years")

    fig = px.bar(
        top_countries,
        x='lays',
        y='country',
        orientation='h',
        color='lays',
        color_continuous_scale='Greens',
        labels={'lays': 'Learning-Adjusted Years', 'country': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Bottom 20 Countries")

    fig = px.bar(
        bottom_countries,
        x='lays',
        y='country',
        orientation='h',
        color='lays',
        color_continuous_scale='Reds_r',
        labels={'lays': 'Learning-Adjusted Years', 'country': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Education tiers
    st.subheader("Countries by Education Tier")

    tier_display = tier_summary.copy()
    tier_display.columns = ['Tier', 'Countries', 'Avg Years', 'Min', 'Max']

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            tier_summary,
            values='countries',
            names='education_tier',
            color='education_tier',
            color_discrete_map={
                'Excellent (11+ years)': '#22c55e',
                'Good (9-11 years)': '#84cc16',
                'Moderate (7-9 years)': '#eab308',
                'Low (5-7 years)': '#f97316',
                'Very Low (<5 years)': '#ef4444'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Tier Definitions:**
        - **Excellent**: 11+ years of quality-adjusted education
        - **Good**: 9-11 years
        - **Moderate**: 7-9 years
        - **Low**: 5-7 years
        - **Very Low**: Less than 5 years
        """)

# Tab 2: Regional Analysis
with tab2:
    st.subheader("Regional Comparison")

    # Bar chart of regional averages
    fig = px.bar(
        region_summary,
        x='region',
        y='avg_lays',
        color='avg_lays',
        color_continuous_scale='RdYlGn',
        labels={'region': 'Region', 'avg_lays': 'Average Learning-Adjusted Years'},
        text='avg_lays'
    )

    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Distribution by Region")

        fig = px.box(
            full_data,
            x='region',
            y='lays',
            color='region',
            labels={'region': 'Region', 'lays': 'Learning-Adjusted Years'},
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Regional Summary Table")

        display_region = region_summary.copy()
        display_region.columns = ['Region', 'Countries', 'Avg LAYS', 'Min', 'Max', 'Std Dev']

        st.dataframe(display_region, use_container_width=True, hide_index=True)

        st.markdown("""
        **Key Patterns:**
        - North America & Europe lead globally
        - East Asia shows strong performance
        - Sub-Saharan Africa faces biggest challenges
        - South Asia has high variability
        """)

    # World map
    st.subheader("Global Distribution")

    fig = px.choropleth(
        full_data,
        locations='country',
        locationmode='country names',
        color='lays',
        color_continuous_scale='RdYlGn',
        labels={'lays': 'LAYS'},
        title='Learning-Adjusted Years by Country'
    )

    fig.update_layout(
        height=500,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Income Groups
with tab3:
    st.subheader("Education by Income Level")

    fig = px.bar(
        income_summary,
        x='income_group',
        y='avg_lays',
        color='avg_lays',
        color_continuous_scale='Blues',
        labels={'income_group': 'Income Group', 'avg_lays': 'Average Learning-Adjusted Years'},
        text='avg_lays'
    )

    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Distribution by Income Group")

        fig = px.box(
            full_data,
            x='income_group',
            y='lays',
            color='income_group',
            labels={'income_group': 'Income Group', 'lays': 'Learning-Adjusted Years'},
            category_orders={'income_group': ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Other']}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-30,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Income Group Summary")

        display_income = income_summary.copy()
        display_income.columns = ['Income Group', 'Countries', 'Avg LAYS', 'Min', 'Max', 'Std Dev']

        st.dataframe(display_income, use_container_width=True, hide_index=True)

        # Calculate income gap
        high_income_avg = income_summary[income_summary['income_group'] == 'High income']['avg_lays'].values[0]
        low_income_avg = income_summary[income_summary['income_group'] == 'Low income']['avg_lays'].values[0]
        income_gap = high_income_avg - low_income_avg

        st.warning(f"**Income Gap:** High-income countries average **{income_gap:.1f} more years** of quality education than low-income countries.")

    # Scatter plot: Income vs LAYS
    st.subheader("Gap from Best by Income Group")

    fig = px.scatter(
        full_data,
        x='lays',
        y='gap_from_best',
        color='income_group',
        hover_name='country',
        labels={
            'lays': 'Learning-Adjusted Years',
            'gap_from_best': 'Gap from Singapore (best)',
            'income_group': 'Income Group'
        },
        category_orders={'income_group': ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Other']}
    )

    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📊", "Study 1: The Learning Crisis",
            "A child in a low-income country receives only <b>4.1 years</b> of quality-adjusted education, compared to <b>11+ years</b> in high-income countries.",
            "The World Bank's Human Capital Index reveals that simply counting years in school dramatically overstates actual learning outcomes in many developing nations."),
        ResearchStudy("🇸🇬", "Study 2: Singapore's Success",
            "Singapore leads the world with <b>12.9 learning-adjusted years</b>, meaning students achieve nearly <b>13 years of effective learning</b> during their schooling.",
            "Singapore's education system combines high enrollment with exceptional teaching quality, demonstrating that both access and quality matter."),
        ResearchStudy("🌍", "Study 3: Regional Disparities",
            "Sub-Saharan Africa averages only <b>5.0 years</b> of learning-adjusted schooling, while Europe & Central Asia averages <b>10.0 years</b>.",
            "These disparities translate to massive differences in human capital, economic productivity, and long-term development outcomes."),
        ResearchStudy("💰", "Study 4: Income Correlation",
            "High-income countries average <b>10.7 years</b> vs <b>4.1 years</b> for low-income countries - a gap of <b>6.6 years</b> of effective education.",
            "The correlation between national income and education quality creates reinforcing cycles that are difficult to break."),
        ResearchStudy("📈", "Study 5: Quality vs Quantity",
            "Some countries show <b>30-40% learning gaps</b> - meaning students learn only 60-70% of what their years in school would suggest.",
            "This finding has transformed education policy, shifting focus from enrollment targets to learning outcomes."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Learning-Adjusted Years of Schooling (LAYS) combines quantity and quality of education",
        "Formula: LAYS = Expected years of school × Harmonized learning outcomes",
        "Harmonized test scores from international assessments (PISA, TIMSS, PIRLS)",
        "Scores converted to common scale (300-625) where 625 = full learning"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Single year snapshot (2018) - no trend analysis possible",
        "Test participation varies across countries",
        "Not all countries have recent assessment data",
        "Quality measures focus on math and reading only"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(full_data['country'].unique()),
        index=sorted(full_data['country'].unique()).index('United States') if 'United States' in full_data['country'].unique() else 0
    )

    country_data = full_data[full_data['country'] == selected_country]

    if len(country_data) > 0:
        info = country_data.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Learning-Adjusted Years", f"{info['lays']:.1f}")

        with col2:
            st.metric("Education Tier", info['education_tier'].split('(')[0].strip())

        with col3:
            st.metric("Region", info['region'])

        with col4:
            st.metric("Gap from Best", f"-{info['gap_from_best']:.1f} years")

        # Regional comparison
        st.subheader(f"How {selected_country} Compares")

        region_countries = full_data[full_data['region'] == info['region']].sort_values('lays', ascending=False)

        colors = ['#3b82f6' if c != selected_country else '#ef4444' for c in region_countries['country']]

        fig = px.bar(
            region_countries,
            x='lays',
            y='country',
            orientation='h',
            labels={'lays': 'Learning-Adjusted Years', 'country': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"Countries in {info['region']}",
            height=max(400, len(region_countries) * 25),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Income group comparison
        income_countries = full_data[full_data['income_group'] == info['income_group']].sort_values('lays', ascending=False)

        colors = ['#22c55e' if c != selected_country else '#ef4444' for c in income_countries['country']]

        fig2 = px.bar(
            income_countries,
            x='lays',
            y='country',
            orientation='h',
            labels={'lays': 'Learning-Adjusted Years', 'country': ''}
        )

        fig2.update_traces(marker_color=colors)

        fig2.update_layout(
            title=f"Countries in {info['income_group']}",
            height=max(400, len(income_countries) * 25),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Interpretation
        if info['lays'] >= 11:
            st.success(f"**{selected_country}** is among the world's top performers in education quality, with learning outcomes that approach full potential.")
        elif info['lays'] >= 9:
            st.info(f"**{selected_country}** has good education outcomes, but there's room for improvement to reach top-tier performance.")
        elif info['lays'] >= 7:
            st.warning(f"**{selected_country}** has moderate education outcomes. Significant improvements in quality could boost human capital substantially.")
        else:
            st.error(f"**{selected_country}** faces major challenges in education quality. Students are losing years of potential learning.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Region Summary", "Income Summary", "Tier Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "learning_adjusted_full.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "learning_adjusted_regions.csv", "text/csv")

    elif data_view == "Income Summary":
        st.dataframe(income_summary, use_container_width=True, hide_index=True)
        csv = income_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "learning_adjusted_income.csv", "text/csv")

    else:
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "learning_adjusted_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Singapore", "United States"),
        ("Japan", "China"),
        ("Finland", "United Kingdom"),
    ],
    data=full_data,
    name_column="country",
    value_column="lays",
    title="Test Your Education Knowledge",
    prompt="Can you guess which country has MORE learning-adjusted years?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """learning_adjusted ────┐
* country (PK)        │    region_summary
* year                ├──▶ * region (PK)
* region              │    * countries
* income_group        │    * avg_lays
* lays                │    * min_lays, max_lays
* education_tier      │
* gap_from_best       │    income_summary
                      ├──▶ * income_group (PK)
tier_summary ─────────┤    * countries
* education_tier (PK) │    * avg_lays
* countries           │
* avg_lays            │"""

SAMPLE_QUERIES = """-- Top countries by learning-adjusted years
SELECT country, region, lays, education_tier
FROM learning_adjusted
ORDER BY lays DESC
LIMIT 10;

-- Regional averages
SELECT region, ROUND(AVG(lays), 1) as avg_lays
FROM learning_adjusted
GROUP BY region
ORDER BY avg_lays DESC;

-- Income group analysis
SELECT income_group, COUNT(*) as countries, ROUND(AVG(lays), 1) as avg_lays
FROM learning_adjusted
GROUP BY income_group
ORDER BY avg_lays DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["157-country global analysis", "World Bank income classification", "Regional breakdown by 7 regions", "Education quality tiers"]
)

# Footer
render_data_footer(
    data_sources=["World Bank Human Capital Index", "World Bank EdStats", "Harmonized Learning Outcomes"],
    time_period=f"2018\n{stats['countries']} countries analyzed",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "World Bank", "Compilation": "Our World in Data"},
    dataset_url="https://www.worldbank.org/en/publication/human-capital"
)

# Site footer
render_site_footer()
