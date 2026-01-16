"""
CO2 Emissions by Sector Dashboard
Analyzing carbon dioxide emissions across 193 countries (CAIT, 1990-2016)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.co2_emissions.database import CO2EmissionsDatabase
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
    page_title="CO2 Emissions | Allan Ninal",
    page_icon="🏭",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load CO2 emissions data from database."""
    with CO2EmissionsDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        sector_summary = db.get_sector_summary()
        tier_summary = db.get_tier_summary()
        top_emitters = db.get_top_emitters(20)
        top_per_capita = db.get_top_per_capita(20)
        lowest_per_capita = db.get_lowest_per_capita(20)
        global_trend = db.get_global_trend()
        stats = db.get_stats()
    return (full_data, country_summary, region_summary, sector_summary, tier_summary,
            top_emitters, top_per_capita, lowest_per_capita, global_trend, stats)


# Load data
(full_data, country_summary, region_summary, sector_summary, tier_summary,
 top_emitters, top_per_capita, lowest_per_capita, global_trend, stats) = load_data()

# Setup page with theme and sidebar
setup_page("CO2 Emissions", icon="🏭", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="CO2 Emissions by Sector",
    subtitle="Tracking carbon dioxide emissions from energy, industry, transport, and land use across 193 countries from 1990-2016.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | CAIT Climate Data Explorer"
)

# Key insight banner
render_shocking_fact(
    value=f"32.4 Gt CO2",
    description=f"In 2016, global CO2 emissions reached <b>32.4 billion tonnes</b>. <b>{stats['top_emitter']}</b> leads with <b>{stats['top_emitter_gt']:.1f} Gt</b> (30% of global), while <b>{stats['top_per_capita_country']}</b> has the highest per capita emissions at <b>{stats['top_per_capita']:.1f} tonnes/person</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"32.4 Gt", "Global CO2<br>(2016)"),
    HeroStat(f"{stats['top_emitter_gt']:.1f} Gt", f"{stats['top_emitter']}<br>Largest Emitter", "success"),
    HeroStat(f"27", "Years of<br>Data (1990-2016)", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Top Emitters", "Per Capita", "Sectors & Trends",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Top Emitters
with tab1:
    st.subheader("Largest CO2 Emitters (2016)")

    fig = px.bar(
        top_emitters,
        x='total_excl_lucf',
        y='entity',
        orientation='h',
        color='total_excl_lucf',
        color_continuous_scale='Reds',
        labels={'total_excl_lucf': 'CO2 Emissions (Mt)', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional breakdown
    st.subheader("Emissions by Region")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            region_summary,
            values='total_emissions',
            names='region',
            color='region',
            title='Share of Global CO2 Emissions'
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            region_summary.sort_values('total_emissions', ascending=True),
            x='total_emissions',
            y='region',
            orientation='h',
            color='total_emissions',
            color_continuous_scale='Reds',
            labels={'total_emissions': 'CO2 (Mt)', 'region': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Emissions Map")

    fig = px.choropleth(
        country_summary,
        locations='entity',
        locationmode='country names',
        color='total_excl_lucf',
        color_continuous_scale='Reds',
        labels={'total_excl_lucf': 'CO2 (Mt)'},
        title='CO2 Emissions by Country (2016, Mt)'
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

# Tab 2: Per Capita
with tab2:
    st.subheader("Highest Per Capita Emissions (tonnes/person)")

    fig = px.bar(
        top_per_capita,
        x='total_excl_lucf_pc',
        y='entity',
        orientation='h',
        color='total_excl_lucf_pc',
        color_continuous_scale='Blues',
        labels={'total_excl_lucf_pc': 'Tonnes CO2/Person', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Lowest Per Capita Emissions")

    fig = px.bar(
        lowest_per_capita.head(20),
        x='total_excl_lucf_pc',
        y='entity',
        orientation='h',
        color='total_excl_lucf_pc',
        color_continuous_scale='Greens',
        labels={'total_excl_lucf_pc': 'Tonnes CO2/Person', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Per capita tiers
    st.subheader("Countries by Per Capita Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        tier_data = tier_summary[tier_summary['per_capita_tier'] != 'No Data']
        fig = px.pie(
            tier_data,
            values='countries',
            names='per_capita_tier',
            color='per_capita_tier',
            color_discrete_map={
                'Very High (15+)': '#991b1b',
                'High (8-15)': '#ef4444',
                'Moderate (4-8)': '#f97316',
                'Low (1-4)': '#eab308',
                'Very Low (<1)': '#22c55e'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tier_display = tier_summary.copy()
        tier_display.columns = ['Tier', 'Countries', 'Avg Per Capita', 'Min', 'Max', 'Total Emissions']

        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Per Capita Tiers (tonnes CO2/person):**
        - **Very High**: 15+ (oil states, developed nations)
        - **High**: 8-15
        - **Moderate**: 4-8
        - **Low**: 1-4
        - **Very Low**: <1 (least developed nations)
        """)

    # World map - per capita
    st.subheader("Per Capita Emissions - Global View")

    fig = px.choropleth(
        country_summary,
        locations='entity',
        locationmode='country names',
        color='total_excl_lucf_pc',
        color_continuous_scale='Blues',
        labels={'total_excl_lucf_pc': 't/person'},
        title='Per Capita CO2 Emissions (2016)'
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

# Tab 3: Sectors & Trends
with tab3:
    st.subheader("Emissions by Sector (2016)")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            sector_summary,
            values='emissions',
            names='sector',
            color='sector',
            title='Global CO2 by Sector'
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            sector_summary.sort_values('emissions', ascending=True),
            x='emissions',
            y='sector',
            orientation='h',
            color='emissions',
            color_continuous_scale='Reds',
            labels={'emissions': 'CO2 (Mt)', 'sector': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Global trend over time
    st.subheader("Global Emissions Trend (1990-2016)")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=global_trend['year'],
        y=global_trend['total_emissions'],
        mode='lines+markers',
        name='Total CO2',
        line=dict(color='#ef4444', width=3)
    ))

    fig.update_layout(
        height=400,
        xaxis_title='Year',
        yaxis_title='CO2 Emissions (Mt)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Sector trends
    st.subheader("Emissions by Sector Over Time")

    fig = go.Figure()

    colors = {'electricity_heat': '#ef4444', 'transport': '#3b82f6',
              'manufacturing': '#22c55e', 'industry': '#f97316'}

    for col, color in colors.items():
        fig.add_trace(go.Scatter(
            x=global_trend['year'],
            y=global_trend[col],
            mode='lines',
            name=col.replace('_', ' ').title(),
            line=dict(color=color, width=2)
        ))

    fig.update_layout(
        height=400,
        xaxis_title='Year',
        yaxis_title='CO2 Emissions (Mt)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🇨🇳", "Study 1: China's Rapid Rise",
            "<b>China</b> became the world's largest CO2 emitter in 2005, surpassing the US. By 2016, China emitted <b>9.8 Gt</b> - nearly twice US levels.",
            "China's emissions grew 4x from 1990 to 2016, driven by rapid industrialization and coal-powered growth."),
        ResearchStudy("⚡", "Study 2: Electricity & Heat Dominates",
            "<b>Electricity and heat production</b> accounts for the largest share of emissions at approximately <b>40%</b> globally.",
            "The power sector is the primary target for decarbonization, with potential through renewables, nuclear, and efficiency gains."),
        ResearchStudy("🛢️", "Study 3: The Per Capita Gap",
            "<b>Qatar</b> has the highest per capita emissions at <b>31 tonnes/person</b> - over 300x higher than the lowest countries.",
            "Oil-rich Gulf states and developed nations have per capita emissions many times higher than developing countries."),
        ResearchStudy("🚗", "Study 4: Transport Growth",
            "<b>Transport emissions</b> grew by 65% from 1990-2016, driven by increased global mobility and car ownership.",
            "Aviation and shipping emissions are particularly hard to decarbonize, creating long-term challenges."),
        ResearchStudy("📈", "Study 5: Emissions Continue Rising",
            "Despite climate agreements, global CO2 emissions <b>increased 60%</b> from 1990 to 2016 - from 21 Gt to 34 Gt.",
            "The Paris Agreement aims to reverse this trend, but current trajectories remain off-track for limiting warming to 1.5°C."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Data from CAIT Climate Data Explorer (Climate Watch Portal)",
        "Emissions measured in million tonnes (Mt) of CO2",
        "Excludes LUCF (Land Use Change and Forestry) unless specified",
        "Per capita calculated using World Bank population data"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Sector Definitions")
    sectors = [
        "**Electricity & Heat**: Power plants and centralized heating",
        "**Transport**: Road, rail, domestic aviation and shipping",
        "**Manufacturing**: Production of goods and materials",
        "**Industry**: Industrial processes (cement, chemicals, etc.)",
        "**Building**: Residential and commercial buildings",
        "**Fugitive**: Leaks from fuel extraction and processing"
    ]
    for sector in sectors:
        st.markdown(f"- {sector}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(country_summary['entity'].unique()),
        index=sorted(country_summary['entity'].unique()).index('United States') if 'United States' in country_summary['entity'].unique() else 0
    )

    country_info = country_summary[country_summary['entity'] == selected_country]

    if len(country_info) > 0:
        info = country_info.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total CO2 (2016)", f"{info['total_excl_lucf']:.1f} Mt")

        with col2:
            st.metric("Per Capita", f"{info['total_excl_lucf_pc']:.1f} t/person")

        with col3:
            st.metric("Electricity Share", f"{info['electricity_share']:.1f}%")

        with col4:
            st.metric("Transport Share", f"{info['transport_share']:.1f}%")

        # Country trend over time
        with CO2EmissionsDatabase() as db:
            country_trend = db.get_country_trend(selected_country)

        if len(country_trend) > 0:
            st.subheader(f"{selected_country} - Emissions Trend (1990-2016)")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=country_trend['year'],
                y=country_trend['total_excl_lucf'],
                mode='lines+markers',
                name='Total CO2',
                line=dict(color='#ef4444', width=3)
            ))

            fig.update_layout(
                height=400,
                xaxis_title='Year',
                yaxis_title='CO2 Emissions (Mt)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

            # Per capita trend
            st.subheader(f"{selected_country} - Per Capita Trend")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=country_trend['year'],
                y=country_trend['total_excl_lucf_pc'],
                mode='lines+markers',
                name='Per Capita',
                line=dict(color='#3b82f6', width=3)
            ))

            fig.update_layout(
                height=300,
                xaxis_title='Year',
                yaxis_title='Tonnes CO2/Person',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Regional comparison
        st.subheader(f"How {selected_country} Compares in {info['region']}")

        with CO2EmissionsDatabase() as db:
            region_countries = db.get_by_region(info['region'])

        colors = ['#ef4444' if c != selected_country else '#3b82f6' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='total_excl_lucf',
            y='entity',
            orientation='h',
            labels={'total_excl_lucf': 'CO2 (Mt)', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"CO2 Emissions in {info['region']}",
            height=max(400, len(region_countries) * 20),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        global_avg_pc = 4.5  # Approximate global average
        if info['total_excl_lucf_pc'] >= 15:
            st.error(f"**{selected_country}** has very high per capita emissions - among the world's highest.")
        elif info['total_excl_lucf_pc'] >= 8:
            st.warning(f"**{selected_country}** has high per capita emissions, above most developed countries.")
        elif info['total_excl_lucf_pc'] >= global_avg_pc:
            st.info(f"**{selected_country}** has moderate emissions, around the global average.")
        else:
            st.success(f"**{selected_country}** has relatively low per capita emissions.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Country Summary (2016)", "Region Summary", "Sector Summary", "Per Capita Tiers", "Full Time Series"],
        horizontal=True
    )

    if data_view == "Country Summary (2016)":
        st.dataframe(country_summary, use_container_width=True, hide_index=True)
        csv = country_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "co2_emissions_countries.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "co2_emissions_regions.csv", "text/csv")

    elif data_view == "Sector Summary":
        st.dataframe(sector_summary, use_container_width=True, hide_index=True)
        csv = sector_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "co2_emissions_sectors.csv", "text/csv")

    elif data_view == "Per Capita Tiers":
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "co2_emissions_tiers.csv", "text/csv")

    else:
        st.info("Full time series has 5,000+ rows. Showing first 500.")
        st.dataframe(full_data.head(500), use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download Full CSV", csv, "co2_emissions_full.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("China", "United States"),
        ("Qatar", "United Arab Emirates"),
        ("Germany", "Japan"),
    ],
    data=country_summary,
    name_column="entity",
    value_column="total_excl_lucf",
    title="Test Your CO2 Emissions Knowledge",
    prompt="Can you guess which country emits MORE CO2?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """co2_emissions ────────┐
* entity (PK)         │    country_summary
* year                ├──▶ * entity (PK)
* electricity_heat    │    * total_excl_lucf
* transport           │    * per_capita
* industry            │    * sector_shares
* manufacturing       │
* total_excl_lucf     │    sector_summary
* per_capita_tier     └──▶ * sector (PK)
                           * emissions"""

SAMPLE_QUERIES = """-- Top 10 emitters in 2016
SELECT entity, region, total_excl_lucf
FROM country_summary
ORDER BY total_excl_lucf DESC
LIMIT 10;

-- Regional totals
SELECT region, total_emissions, avg_per_capita
FROM region_summary
ORDER BY total_emissions DESC;

-- Country emissions over time
SELECT year, total_excl_lucf
FROM co2_emissions
WHERE entity = 'China'
ORDER BY year;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["27 years of data (1990-2016)", "193 countries", "7 emission sectors", "Per capita calculations"]
)

# Footer
render_data_footer(
    data_sources=["CAIT Climate Data Explorer", "Climate Watch Portal"],
    time_period="1990-2016\n193 countries",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "World Resources Institute", "Compilation": "Our World in Data"},
    dataset_url="https://www.climatewatchdata.org/data-explorer/historical-emissions"
)

# Site Footer
render_site_footer()
