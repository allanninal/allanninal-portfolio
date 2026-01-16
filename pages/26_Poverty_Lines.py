"""
National Poverty Lines Dashboard
How different countries define poverty (Jolliffe et al., 2022)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.poverty_lines.database import PovertyLinesDatabase
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
    page_title="National Poverty Lines | Allan Ninal",
    page_icon="💵",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load poverty lines data from database."""
    with PovertyLinesDatabase() as db:
        full_data = db.get_full_data()
        income_summary = db.get_income_summary()
        region_summary = db.get_region_summary()
        lowest_lines = db.get_lowest_poverty_lines(limit=20)
        highest_lines = db.get_highest_poverty_lines(limit=20)
        ipl_comparison = db.get_comparison_to_ipl()
        stats = db.get_stats()
    return (full_data, income_summary, region_summary, lowest_lines,
            highest_lines, ipl_comparison, stats)


# Load data
(full_data, income_summary, region_summary, lowest_lines,
 highest_lines, ipl_comparison, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Poverty Lines", icon="💵", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="National Poverty Lines",
    subtitle="How different countries define poverty - from $0.91 to $37.80 per day. What's considered poor in one country may be comfortable in another.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | Jolliffe et al. (2022) | World Bank"
)

# Key insight banner
render_shocking_fact(
    value=f"{stats['ratio_highest_lowest']:.0f}x Difference",
    description=f"<b>{stats['highest_line_country']}</b> defines poverty as living on less than <b>${stats['highest_line']:.2f}/day</b>, while <b>{stats['lowest_line_country']}</b> sets it at <b>${stats['lowest_line']:.2f}/day</b>. The World Bank's International Poverty Line is <b>${stats['international_poverty_line']}/day</b>.",
    style="warning"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"${stats['lowest_line']:.2f}", f"{stats['lowest_line_country']}<br>Lowest Line", "success"),
    HeroStat(f"${stats['median_poverty_line']:.2f}", "Median<br>Poverty Line"),
    HeroStat(f"${stats['highest_line']:.2f}", f"{stats['highest_line_country']}<br>Highest Line", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Compared", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Comparison", "Income Groups", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Comparison
with tab1:
    st.subheader("National Poverty Lines by Country")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Lowest Poverty Lines")
        st.caption("Countries with the lowest national poverty thresholds")

        fig = px.bar(
            lowest_lines,
            x='poverty_line_rounded',
            y='country',
            orientation='h',
            color='income_group',
            color_discrete_map={
                'Low income': '#ef4444',
                'Lower middle income': '#f97316',
                'Upper middle income': '#3b82f6',
                'High income': '#22c55e'
            },
            labels={'poverty_line_rounded': '$/day', 'country': '', 'income_group': 'Income Group'}
        )

        # Add IPL reference line
        fig.add_vline(x=2.15, line_dash="dash", line_color="red",
                      annotation_text="IPL $2.15", annotation_position="top right")

        fig.update_layout(
            height=550,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Highest Poverty Lines")
        st.caption("Countries with the highest national poverty thresholds")

        fig = px.bar(
            highest_lines,
            x='poverty_line_rounded',
            y='country',
            orientation='h',
            color='income_group',
            color_discrete_map={
                'Low income': '#ef4444',
                'Lower middle income': '#f97316',
                'Upper middle income': '#3b82f6',
                'High income': '#22c55e'
            },
            labels={'poverty_line_rounded': '$/day', 'country': '', 'income_group': 'Income Group'}
        )

        fig.update_layout(
            height=550,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Distribution of Poverty Lines")

    fig = px.choropleth(
        full_data,
        locations='country',
        locationmode='country names',
        color='poverty_line',
        color_continuous_scale='RdYlGn',
        range_color=[0, 40],
        labels={'poverty_line': '$/day'},
        hover_data={'country': True, 'poverty_line_rounded': True, 'income_group': True}
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

    # Distribution histogram
    st.subheader("Distribution of Poverty Lines")

    fig = px.histogram(
        full_data,
        x='poverty_line',
        nbins=30,
        color='income_group',
        color_discrete_map={
            'Low income': '#ef4444',
            'Lower middle income': '#f97316',
            'Upper middle income': '#3b82f6',
            'High income': '#22c55e'
        },
        labels={'poverty_line': 'Poverty Line ($/day)', 'count': 'Countries'}
    )

    # Add IPL reference line
    fig.add_vline(x=2.15, line_dash="dash", line_color="red",
                  annotation_text="IPL $2.15", annotation_position="top right")

    fig.update_layout(
        height=400,
        barmode='stack',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**International Poverty Line (IPL)**: The World Bank's extreme poverty threshold is $2.15/day (2017 PPP). Many countries set their national lines above or below this.")

# Tab 2: Income Groups
with tab2:
    st.subheader("Poverty Lines by World Bank Income Classification")

    st.markdown("""
    The World Bank classifies countries into four income groups. Higher-income countries naturally set higher poverty thresholds
    to reflect their higher cost of living and expectations for minimum living standards.
    """)

    # Income group comparison
    fig = px.bar(
        income_summary,
        x='income_group',
        y='avg_poverty_line',
        color='income_group',
        color_discrete_map={
            'Low income': '#ef4444',
            'Lower middle income': '#f97316',
            'Upper middle income': '#3b82f6',
            'High income': '#22c55e'
        },
        labels={'avg_poverty_line': 'Average Poverty Line ($/day)', 'income_group': ''},
        text='avg_poverty_line'
    )

    fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')

    fig.update_layout(
        title='Average National Poverty Line by Income Group',
        height=450,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Income summary table
    st.subheader("Income Group Summary")

    display_summary = income_summary.copy()
    display_summary.columns = ['Income Group', 'Countries', 'Avg Line', 'Min Line', 'Max Line', 'Median Line']

    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # Box plot by income group
    st.subheader("Poverty Line Distribution by Income Group")

    fig = go.Figure()

    income_order = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
    colors = ['#ef4444', '#f97316', '#3b82f6', '#22c55e']

    for income, color in zip(income_order, colors):
        group_data = full_data[full_data['income_group'] == income]
        fig.add_trace(go.Box(
            y=group_data['poverty_line'],
            name=income,
            marker_color=color,
            boxpoints='all',
            jitter=0.3,
        ))

    fig.update_layout(
        height=500,
        yaxis_title='Poverty Line ($/day)',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Countries by income group
    st.subheader("Browse by Income Group")

    selected_income = st.selectbox(
        "Select an income group:",
        options=income_order,
        index=0
    )

    with PovertyLinesDatabase() as db:
        income_countries = db.get_by_income_group(selected_income)

    st.dataframe(income_countries, use_container_width=True, hide_index=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Poverty Lines by Region")

    # Regional bar chart
    fig = px.bar(
        region_summary.sort_values('avg_poverty_line', ascending=True),
        x='avg_poverty_line',
        y='region',
        orientation='h',
        color='avg_poverty_line',
        color_continuous_scale='RdYlGn',
        labels={'avg_poverty_line': 'Average Poverty Line ($/day)', 'region': ''}
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional summary table
    st.subheader("Regional Summary")

    display_region = region_summary.copy()
    display_region.columns = ['Region', 'Countries', 'Avg Line', 'Min Line', 'Max Line']

    st.dataframe(display_region, use_container_width=True, hide_index=True)

    # Regional disparity
    st.subheader("Within-Region Disparity")

    fig = go.Figure()

    for _, row in region_summary.iterrows():
        fig.add_trace(go.Box(
            y=full_data[full_data['region'] == row['region']]['poverty_line'],
            name=row['region'],
            boxpoints='all',
            jitter=0.3,
        ))

    fig.update_layout(
        height=500,
        yaxis_title='Poverty Line ($/day)',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Regional variation**: Europe has the highest average poverty lines, while Sub-Saharan Africa and South Asia have the lowest.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("💵", "Study 1: The 42x Gap",
            f"National poverty lines range from <b>${stats['lowest_line']:.2f}</b> ({stats['lowest_line_country']}) to <b>${stats['highest_line']:.2f}</b> ({stats['highest_line_country']}).",
            "What counts as poverty in Norway would be comfortable middle-class income in many developing countries."),
        ResearchStudy("🌍", "Study 2: Below the IPL",
            f"Several countries set their national poverty lines <b>below the $2.15 International Poverty Line</b>.",
            "Uzbekistan ($0.91), Uganda ($1.49), and Mozambique ($1.49) define poverty more restrictively than the World Bank."),
        ResearchStudy("💰", "Study 3: Income Group Patterns",
            "High-income countries average <b>$25.48/day</b>, while low-income countries average just <b>$2.08/day</b>.",
            "A 12x difference reflects both cost of living and societal expectations for minimum living standards."),
        ResearchStudy("🇪🇺", "Study 4: European Standards",
            "European countries have the highest poverty lines, with most setting thresholds <b>above $20/day</b>.",
            "These relative poverty measures aim to ensure social inclusion, not just survival."),
        ResearchStudy("📊", "Study 5: Harmonization Challenge",
            "Different countries measure poverty differently - by income vs. consumption, household size adjustments, etc.",
            "Jolliffe et al. harmonized these definitions to enable cross-country comparisons for the first time."),
    ])

    st.markdown("### About Poverty Lines")
    st.markdown("""
    **National poverty lines** are the thresholds countries use to measure poverty domestically. They reflect:
    - Cost of basic necessities (food, housing, clothing)
    - Cultural expectations for minimum living standards
    - Political and economic considerations

    **Why they differ:**
    - **Absolute vs. Relative**: Some measure absolute deprivation; others use relative thresholds (e.g., 60% of median income)
    - **Cost of Living**: Prices vary dramatically between countries
    - **Social Norms**: What's considered essential differs by culture
    """)

    st.markdown("### International Poverty Lines")
    st.markdown("""
    The World Bank uses three international thresholds:
    - **$2.15/day**: Extreme poverty (typical for low-income countries)
    - **$3.65/day**: Poverty line for lower-middle-income countries
    - **$6.85/day**: Poverty line for upper-middle-income countries
    """)

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    with PovertyLinesDatabase() as db:
        countries_list = db.get_countries_list()

    selected_country = st.selectbox(
        "Select a country:",
        options=countries_list,
        index=countries_list.index('United States') if 'United States' in countries_list else 0
    )

    with PovertyLinesDatabase() as db:
        country_data = db.get_country_data(selected_country)

    if len(country_data) > 0:
        info = country_data.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Poverty Line", f"${info['poverty_line_rounded']:.2f}/day")

        with col2:
            st.metric("Income Group", info['income_group'])

        with col3:
            st.metric("Region", info['region'])

        with col4:
            multiple = info['poverty_line'] / 2.15
            st.metric("vs. IPL ($2.15)", f"{multiple:.1f}x")

        # Context
        st.subheader("How Does This Compare?")

        col1, col2 = st.columns([1, 1])

        with col1:
            # Compare to same income group
            income_avg = income_summary[income_summary['income_group'] == info['income_group']]['avg_poverty_line'].values[0]

            st.markdown(f"""
            **Within {info['income_group']} Countries:**
            - {selected_country}: ${info['poverty_line_rounded']:.2f}/day
            - Group Average: ${income_avg:.2f}/day
            - Difference: {"+" if info['poverty_line'] > income_avg else ""}{((info['poverty_line'] - income_avg) / income_avg * 100):.0f}%
            """)

        with col2:
            # Compare to global
            st.markdown(f"""
            **Global Comparison:**
            - {selected_country}: ${info['poverty_line_rounded']:.2f}/day
            - Global Median: ${stats['median_poverty_line']:.2f}/day
            - Global Average: ${stats['avg_poverty_line']:.2f}/day
            """)

        # Visual comparison
        st.subheader("Visual Comparison")

        # Get countries in same income group for comparison
        with PovertyLinesDatabase() as db:
            same_group = db.get_by_income_group(info['income_group'])

        # Highlight selected country
        same_group['is_selected'] = same_group['country'] == selected_country

        fig = px.bar(
            same_group.sort_values('poverty_line_rounded'),
            x='poverty_line_rounded',
            y='country',
            orientation='h',
            color='is_selected',
            color_discrete_map={True: '#3b82f6', False: '#94a3b8'},
            labels={'poverty_line_rounded': '$/day', 'country': ''}
        )

        fig.update_layout(
            title=f'{info["income_group"]} Countries - Poverty Lines',
            height=max(400, len(same_group) * 25),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if info['poverty_line'] < 2.15:
            st.error(f"**{selected_country}** sets its poverty line below the International Poverty Line ($2.15), using a more restrictive definition of poverty.")
        elif info['poverty_line'] < 6.85:
            st.warning(f"**{selected_country}** has a poverty line typical of low to lower-middle income countries.")
        elif info['poverty_line'] < 15:
            st.info(f"**{selected_country}** has a moderate poverty line, reflecting upper-middle income status.")
        else:
            st.success(f"**{selected_country}** has a high poverty line (${info['poverty_line_rounded']:.2f}/day), reflecting high-income country standards focused on relative poverty and social inclusion.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Income Group Summary", "Region Summary", "IPL Comparison"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        display_data = full_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "poverty_lines_full.csv", "text/csv")

    elif data_view == "Income Group Summary":
        st.dataframe(income_summary, use_container_width=True, hide_index=True)
        csv = income_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "poverty_lines_income.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "poverty_lines_regions.csv", "text/csv")

    else:
        st.dataframe(ipl_comparison, use_container_width=True, hide_index=True)
        csv = ipl_comparison.to_csv(index=False)
        st.download_button("Download CSV", csv, "poverty_lines_ipl_comparison.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Norway", "Switzerland"),
        ("United States", "Germany"),
        ("India", "Bangladesh"),
    ],
    data=full_data,
    name_column="country",
    value_column="poverty_line",
    title="Test Your Knowledge",
    prompt="Can you guess which country has the HIGHER national poverty line?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """poverty_lines ──────────────┐
* country (PK)              │    income_summary
* year                      ├──▶ * income_group (PK)
* income_group              │    * avg_poverty_line
* poverty_line              │    * median_poverty_line
* region                    │
* poverty_tier              │    region_summary
                            └──▶ * region (PK)
                                 * avg_poverty_line"""

SAMPLE_QUERIES = """-- Lowest poverty lines
SELECT country, income_group, poverty_line_rounded
FROM poverty_lines
ORDER BY poverty_line ASC
LIMIT 10;

-- By income group
SELECT income_group, avg_poverty_line, median_poverty_line
FROM income_summary
ORDER BY avg_poverty_line;

-- Countries below IPL
SELECT country, poverty_line_rounded
FROM poverty_lines
WHERE poverty_line < 2.15;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["157 countries", "4 income groups", "Harmonized measures", "IPL comparison"]
)

# Footer
render_data_footer(
    data_sources=["Jolliffe et al. (2022)", "World Bank Poverty and Inequality Platform"],
    time_period="Various years (2001-2018)",
    data_points=f"{stats['countries']} countries",
    credits={"Research": "World Bank", "Publication": "World Bank Policy Research Working Paper"},
    dataset_url="https://openknowledge.worldbank.org/handle/10986/37061"
)

# Site Footer
render_site_footer()
