"""
Air Pollution Deaths Dashboard
Analyzing mortality from air pollution across 181 countries (Lelieveld et al. 2019)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.air_pollution.database import AirPollutionDatabase
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
    page_title="Air Pollution Deaths | Allan Ninal",
    page_icon="💨",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load air pollution data from database."""
    with AirPollutionDatabase() as db:
        full_data = db.get_full_data()
        region_summary = db.get_region_summary()
        death_rate_summary = db.get_death_rate_summary()
        fossil_share_summary = db.get_fossil_share_summary()
        highest_death_rate = db.get_highest_death_rate(20)
        lowest_death_rate = db.get_lowest_death_rate(20)
        most_deaths = db.get_most_deaths(20)
        highest_fossil_share = db.get_highest_fossil_share(20)
        most_yll = db.get_most_yll(20)
        stats = db.get_stats()
    return (full_data, region_summary, death_rate_summary, fossil_share_summary,
            highest_death_rate, lowest_death_rate, most_deaths, highest_fossil_share,
            most_yll, stats)


# Load data
(full_data, region_summary, death_rate_summary, fossil_share_summary,
 highest_death_rate, lowest_death_rate, most_deaths, highest_fossil_share,
 most_yll, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Air Pollution Deaths", icon="💨", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Deaths from Air Pollution",
    subtitle="Analyzing mortality from outdoor air pollution across 181 countries, separating fossil fuel from other anthropogenic sources.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | Lelieveld et al. (2019)"
)

# Key insight banner
render_shocking_fact(
    value=f"8.8 Million",
    description=f"In 2015, <b>8.8 million people died</b> from outdoor air pollution - equivalent to <b>120 deaths per 100,000</b> globally. <b>{stats['highest_death_rate_country']}</b> had the highest rate ({stats['highest_death_rate']:.0f}/100k), and <b>fossil fuels</b> caused <b>41%</b> of all air pollution deaths.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['total_deaths_millions']:.1f}M", "Deaths from<br>Air Pollution"),
    HeroStat(f"{stats['total_fossil_deaths_millions']:.1f}M", "Deaths from<br>Fossil Fuels", "success"),
    HeroStat(f"41%", "Fossil Fuel<br>Share", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Death Rates", "Total Deaths", "Fossil Fuel Share",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Death Rates
with tab1:
    st.subheader("Countries with Highest Death Rates (per 100,000)")

    fig = px.bar(
        highest_death_rate,
        x='death_rate_all',
        y='entity',
        orientation='h',
        color='death_rate_all',
        color_continuous_scale='Reds',
        labels={'death_rate_all': 'Deaths per 100,000', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Countries with Lowest Death Rates")

    fig = px.bar(
        lowest_death_rate.head(20),
        x='death_rate_all',
        y='entity',
        orientation='h',
        color='death_rate_all',
        color_continuous_scale='Greens',
        labels={'death_rate_all': 'Deaths per 100,000', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Death rate tiers
    st.subheader("Countries by Death Rate Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            death_rate_summary,
            values='countries',
            names='death_rate_tier',
            color='death_rate_tier',
            color_discrete_map={
                'Very High (150+)': '#991b1b',
                'High (100-150)': '#ef4444',
                'Moderate (50-100)': '#f97316',
                'Low (25-50)': '#eab308',
                'Very Low (<25)': '#22c55e'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        death_rate_display = death_rate_summary.copy()
        death_rate_display.columns = ['Tier', 'Countries', 'Avg Rate', 'Min', 'Max', 'Avg Fossil %', 'Total Deaths']

        st.dataframe(death_rate_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Death Rate Tiers (per 100,000):**
        - **Very High**: 150+ (severe air quality crisis)
        - **High**: 100-150
        - **Moderate**: 50-100
        - **Low**: 25-50
        - **Very Low**: <25 (cleanest air)
        """)

    # World map
    st.subheader("Global Death Rates Map")

    fig = px.choropleth(
        full_data,
        locations='entity',
        locationmode='country names',
        color='death_rate_all',
        color_continuous_scale='Reds',
        labels={'death_rate_all': 'Deaths/100k'},
        title='Air Pollution Death Rate by Country (per 100,000)'
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

# Tab 2: Total Deaths
with tab2:
    st.subheader("Countries with Most Deaths from Air Pollution")

    fig = px.bar(
        most_deaths,
        x='deaths_all_thousands',
        y='entity',
        orientation='h',
        color='deaths_all_thousands',
        color_continuous_scale='Reds',
        labels={'deaths_all_thousands': 'Deaths (Thousands)', 'entity': ''}
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
    st.subheader("Deaths by Region")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            region_summary,
            values='deaths_millions',
            names='region',
            color='region',
            title='Share of Global Air Pollution Deaths'
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            region_summary.sort_values('deaths_millions', ascending=True),
            x='deaths_millions',
            y='region',
            orientation='h',
            color='deaths_millions',
            color_continuous_scale='Reds',
            labels={'deaths_millions': 'Deaths (Millions)', 'region': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Years of Life Lost
    st.subheader("Years of Life Lost (YLL)")

    st.markdown("YLL measures the total potential years of life lost due to premature deaths from air pollution.")

    fig = px.bar(
        most_yll,
        x='yll_all_millions',
        y='entity',
        orientation='h',
        color='yll_all_millions',
        color_continuous_scale='Purples',
        labels={'yll_all_millions': 'Years Lost (Millions)', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Fossil Fuel Share
with tab3:
    st.subheader("Countries with Highest Fossil Fuel Share of Deaths")

    st.markdown("These countries have the highest proportion of air pollution deaths attributable to fossil fuel combustion (coal, oil, gas).")

    fig = px.bar(
        highest_fossil_share,
        x='share_fossil_total',
        y='entity',
        orientation='h',
        color='share_fossil_total',
        color_continuous_scale='Blues',
        labels={'share_fossil_total': 'Fossil Fuel Share (%)', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Fossil share tiers
    st.subheader("Countries by Fossil Fuel Share Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            fossil_share_summary,
            values='countries',
            names='fossil_share_tier',
            color='fossil_share_tier',
            color_discrete_map={
                'Very High (50%+)': '#1e40af',
                'High (30-50%)': '#3b82f6',
                'Moderate (15-30%)': '#60a5fa',
                'Low (5-15%)': '#93c5fd',
                'Very Low (<5%)': '#dbeafe'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fossil_share_display = fossil_share_summary.copy()
        fossil_share_display.columns = ['Tier', 'Countries', 'Avg %', 'Min %', 'Max %', 'Avg Death Rate', 'Fossil Deaths']

        st.dataframe(fossil_share_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Fossil Fuel Share Tiers:**
        - **Very High**: 50%+ (mostly industrialized nations)
        - **High**: 30-50%
        - **Moderate**: 15-30%
        - **Low**: 5-15%
        - **Very Low**: <5% (mostly biomass/dust sources)
        """)

    # Regional comparison
    st.subheader("Average Fossil Fuel Share by Region")

    fig = px.bar(
        region_summary.sort_values('avg_fossil_share', ascending=False),
        x='region',
        y='avg_fossil_share',
        color='avg_fossil_share',
        color_continuous_scale='Blues',
        labels={'region': 'Region', 'avg_fossil_share': 'Avg Fossil Share (%)'},
        text='avg_fossil_share'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # World map - fossil share
    st.subheader("Fossil Fuel Share - Global View")

    fig = px.choropleth(
        full_data,
        locations='entity',
        locationmode='country names',
        color='share_fossil_total',
        color_continuous_scale='Blues',
        labels={'share_fossil_total': 'Fossil %'},
        title='Fossil Fuel Share of Air Pollution Deaths by Country'
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

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("💀", "Study 1: The Hidden Pandemic",
            "Air pollution causes <b>8.8 million deaths annually</b> - more than tobacco smoking, HIV/AIDS, and malaria combined.",
            "This makes air pollution the world's largest single environmental health risk, responsible for 1 in 8 deaths globally."),
        ResearchStudy("⛽", "Study 2: Fossil Fuel Impact",
            "<b>Fossil fuel combustion</b> (coal, oil, natural gas) accounts for <b>41% of all air pollution deaths</b> - about 3.6 million lives annually.",
            "Transitioning away from fossil fuels could prevent millions of deaths while also addressing climate change."),
        ResearchStudy("🇧🇬", "Study 3: Eastern Europe Crisis",
            "<b>Bulgaria</b> has the highest death rate at <b>211 per 100,000</b>, followed by other Eastern European nations relying heavily on coal.",
            "The legacy of Soviet-era industrialization and continued coal dependence creates severe health impacts."),
        ResearchStudy("🇨🇳", "Study 4: China's Burden",
            "<b>China</b> has the most total deaths at <b>2.8 million</b>, with <b>56% attributable to fossil fuels</b>.",
            "Rapid industrialization and coal-powered growth created massive public health costs despite economic gains."),
        ResearchStudy("🇨🇦", "Study 5: Developed World Paradox",
            "<b>Canada</b> and other wealthy nations have <b>87%+</b> of deaths from fossil fuels - highest fossil share despite lower total rates.",
            "In clean-air countries with minimal biomass burning, fossil fuels dominate as the primary remaining pollution source."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Chemical transport model simulation of atmospheric pollution",
        "Exposure-response functions from epidemiological studies",
        "Separate accounting for fossil fuels vs other anthropogenic vs natural sources",
        "Years of Life Lost (YLL) calculated based on life expectancy"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Data from 2015 - air quality changes annually",
        "Models may under/overestimate exposures in some regions",
        "Indoor air pollution not included (major factor in developing nations)",
        "Some country groupings (Serbia and Montenegro, Sudan and South Sudan)"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(full_data['entity'].unique()),
        index=sorted(full_data['entity'].unique()).index('United States') if 'United States' in full_data['entity'].unique() else 0
    )

    country_data = full_data[full_data['entity'] == selected_country]

    if len(country_data) > 0:
        info = country_data.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Deaths (2015)", f"{info['deaths_all_thousands']:.1f}k")

        with col2:
            st.metric("Death Rate", f"{info['death_rate_all']:.1f}/100k")

        with col3:
            st.metric("Fossil Fuel Share", f"{info['share_fossil_total']:.1f}%")

        with col4:
            st.metric("YLL", f"{info['yll_all_millions']:.2f}M years")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Fossil Fuel Deaths", f"{info['deaths_fossil_thousands']:.1f}k")

        with col2:
            st.metric("Fossil Death Rate", f"{info['death_rate_fossil']:.1f}/100k")

        with col3:
            st.metric("Death Rate Tier", info['death_rate_tier'].split('(')[0].strip())

        # Source breakdown
        st.subheader("Deaths by Pollution Source")

        source_data = pd.DataFrame({
            'Source': ['Fossil Fuels', 'Other Anthropogenic', 'Natural Sources'],
            'Deaths': [
                info['deaths_fossil_fuels'],
                info['deaths_anthropogenic'] - info['deaths_fossil_fuels'] if info['deaths_anthropogenic'] > info['deaths_fossil_fuels'] else 0,
                info['deaths_all_sources'] - info['deaths_anthropogenic'] if info['deaths_all_sources'] > info['deaths_anthropogenic'] else 0
            ]
        })

        fig = px.pie(
            source_data,
            values='Deaths',
            names='Source',
            color='Source',
            color_discrete_map={
                'Fossil Fuels': '#3b82f6',
                'Other Anthropogenic': '#f97316',
                'Natural Sources': '#22c55e'
            }
        )

        fig.update_layout(
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Regional comparison
        st.subheader(f"How {selected_country} Compares in {info['region']}")

        region_countries = full_data[full_data['region'] == info['region']].sort_values('death_rate_all', ascending=False)

        colors = ['#ef4444' if c != selected_country else '#3b82f6' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='death_rate_all',
            y='entity',
            orientation='h',
            labels={'death_rate_all': 'Deaths per 100,000', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"Death Rates in {info['region']}",
            height=max(400, len(region_countries) * 20),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        global_avg_rate = 120
        if info['death_rate_all'] >= 150:
            st.error(f"**{selected_country}** has a very high air pollution death rate - among the worst in the world.")
        elif info['death_rate_all'] >= global_avg_rate:
            st.warning(f"**{selected_country}** has an above-average death rate compared to the global average of 120/100k.")
        elif info['death_rate_all'] >= 50:
            st.info(f"**{selected_country}** has a moderate death rate, below the global average of 120/100k.")
        else:
            st.success(f"**{selected_country}** has relatively clean air with low air pollution mortality.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Region Summary", "Death Rate Tiers", "Fossil Share Tiers"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "air_pollution_full.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "air_pollution_regions.csv", "text/csv")

    elif data_view == "Death Rate Tiers":
        st.dataframe(death_rate_summary, use_container_width=True, hide_index=True)
        csv = death_rate_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "air_pollution_death_rate_tiers.csv", "text/csv")

    else:
        st.dataframe(fossil_share_summary, use_container_width=True, hide_index=True)
        csv = fossil_share_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "air_pollution_fossil_share_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Bulgaria", "Germany"),
        ("China", "India"),
        ("Canada", "United States"),
    ],
    data=full_data,
    name_column="entity",
    value_column="death_rate_all",
    title="Test Your Air Pollution Knowledge",
    prompt="Can you guess which country has a HIGHER air pollution death rate?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """air_pollution ────────┐
* entity (PK)         │    region_summary
* year                ├──▶ * region (PK)
* deaths_all_sources  │    * total_deaths
* deaths_fossil_fuels │    * avg_death_rate
* death_rate_all      │    * avg_fossil_share
* death_rate_fossil   │
* share_fossil_total  │    death_rate_summary
* death_rate_tier     └──▶ * tier (PK)
* fossil_share_tier        * countries"""

SAMPLE_QUERIES = """-- Countries with highest death rates
SELECT entity, region, death_rate_all, share_fossil_total
FROM air_pollution
ORDER BY death_rate_all DESC
LIMIT 10;

-- Regional death totals
SELECT region, SUM(deaths_all_sources)/1e6 as deaths_millions
FROM air_pollution
GROUP BY region
ORDER BY deaths_millions DESC;

-- Highest fossil fuel share
SELECT entity, share_fossil_total, death_rate_fossil
FROM air_pollution
ORDER BY share_fossil_total DESC
LIMIT 10;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Chemical transport modeling", "181 countries", "Fossil vs anthropogenic sources", "Years of Life Lost metrics"]
)

# Footer
render_data_footer(
    data_sources=["Lelieveld et al. (2019) PNAS", "Max Roser, Our World in Data"],
    time_period="2015\n181 countries",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "Lelieveld et al.", "Compilation": "Our World in Data"},
    dataset_url="https://doi.org/10.1073/pnas.1819989116"
)

# Site Footer
render_site_footer()
