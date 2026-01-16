"""
Loneliness in Older Adults Dashboard
Exploring self-reported loneliness rates among older adults across 15 countries
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.loneliness_older_adults.database import LonelinessOlderAdultsDatabase
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
    page_title="Loneliness in Older Adults | Allan Ninal",
    page_icon="",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load loneliness data from database."""
    with LonelinessOlderAdultsDatabase() as db:
        by_country = db.get_by_country()
        regional = db.get_regional_summary()
        stats = db.get_stats()
    return by_country, regional, stats


# Load data
by_country, regional, stats = load_data()

# Setup page with theme and sidebar
setup_page("Loneliness in Older Adults", icon="", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Loneliness in Older Adults",
    subtitle="How common is loneliness among older adults across different countries?",
    data_badge="Data: 2002-2018 | 15 Countries | Ages 65+ | Our World in Data"
)

# Key insight banner
gap = stats['highest_rate'] - stats['lowest_rate']
render_shocking_fact(
    value=f"{gap:.0f} percentage points",
    description=f"The gap between <b>{stats['highest_country']}</b> ({stats['highest_rate']:.0f}%) and <b>{stats['lowest_country']}</b> ({stats['lowest_rate']:.0f}%) reveals stark differences in how older adults experience loneliness across cultures.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['highest_rate']:.0f}%", f"Highest Rate<br>{stats['highest_country']}", "danger"),
    HeroStat(f"{stats['lowest_rate']:.0f}%", f"Lowest Rate<br>{stats['lowest_country']}", "success"),
    HeroStat(f"{stats['avg_loneliness']:.0f}%", "Average Across<br>All Countries", "secondary"),
    HeroStat(f"{stats['total_countries']}", "Countries<br>Surveyed", "warning"),
])

# Definition box
st.markdown("""
<div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 1rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem;">
<strong>How is loneliness measured?</strong> Survey respondents were asked how often they feel lonely.
This data aggregates those who report feeling lonely <b>"some of the time"</b>, <b>"most of the time"</b>,
or <b>"almost all the time"</b>. Different surveys used slightly different age thresholds (65+, 72+, or 75+).
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Country Ranking", "Regional Analysis", "Research Findings", "Explorer", "Raw Data"
])

# Tab 1: Country Ranking
with tab1:
    st.subheader("Loneliness Rates by Country")

    # Horizontal bar chart - most impactful visualization
    fig = px.bar(
        by_country.sort_values('loneliness_rate', ascending=True),
        x='loneliness_rate',
        y='country',
        orientation='h',
        color='loneliness_rate',
        color_continuous_scale='RdYlGn_r',
        labels={'loneliness_rate': 'Loneliness Rate (%)', 'country': 'Country'},
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0, 70], dtick=10),
    )

    # Add average line
    fig.add_vline(
        x=stats['avg_loneliness'],
        line_dash="dash",
        line_color="#6366f1",
        annotation_text=f"Average: {stats['avg_loneliness']:.0f}%",
        annotation_position="top"
    )

    st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Loneliness Rate Map")

    # Map country names for choropleth (England -> United Kingdom for map)
    map_data = by_country.copy()
    map_data['map_country'] = map_data['country'].replace({'England': 'United Kingdom'})

    fig_map = px.choropleth(
        map_data,
        locations='map_country',
        locationmode='country names',
        color='loneliness_rate',
        color_continuous_scale='RdYlGn_r',
        labels={'loneliness_rate': 'Loneliness Rate (%)'},
        title='Self-Reported Loneliness Among Older Adults (65+)',
        range_color=[20, 65]
    )

    fig_map.update_layout(
        height=450,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth',
            center=dict(lat=50, lon=10),
            scope='world',
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Focus on Europe/relevant regions
    fig_map.update_geos(
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor="lightgray"
    )

    st.plotly_chart(fig_map, use_container_width=True)

    st.caption("Note: Data coverage limited to 15 countries. Most data from European surveys.")

    # Narrative insights
    st.markdown("### Key Observations")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Southern Europe Struggles**
        - Greece leads with 62% of older adults feeling lonely
        - Italy (47%) and Spain (40%) also above average
        - Mediterranean cultures despite strong family ties
        """)

        st.markdown("""
        **Nordic Success**
        - Denmark has lowest rate at just 25%
        - Sweden and Switzerland follow at 26-30%
        - Strong social safety nets may contribute
        """)

    with col2:
        st.markdown("""
        **Central Europe Mixed**
        - Austria (46%) significantly higher than Germany (37%)
        - Switzerland outperforms neighbors at 26%
        - Economic factors may not fully explain differences
        """)

        st.markdown("""
        **English-Speaking Countries**
        - US (30%) and England (33%) similar rates
        - Below average but not in top performers
        - Data from more recent surveys (2018)
        """)

# Tab 2: Regional Analysis
with tab2:
    st.subheader("Loneliness by Region")

    # Regional bar chart
    fig = px.bar(
        regional.sort_values('avg_loneliness', ascending=False),
        x='region',
        y='avg_loneliness',
        color='avg_loneliness',
        color_continuous_scale='RdYlGn_r',
        labels={'avg_loneliness': 'Average Loneliness Rate (%)', 'region': 'Region'},
        error_y=regional['max_loneliness'] - regional['avg_loneliness'],
        error_y_minus=regional['avg_loneliness'] - regional['min_loneliness'],
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional summary table
    st.subheader("Regional Summary Table")

    region_display = regional.copy()
    region_display['avg_loneliness'] = region_display['avg_loneliness'].apply(lambda x: f"{x:.1f}%")
    region_display['min_loneliness'] = region_display['min_loneliness'].apply(lambda x: f"{x:.0f}%")
    region_display['max_loneliness'] = region_display['max_loneliness'].apply(lambda x: f"{x:.0f}%")
    region_display.columns = ['Region', 'Average', 'Minimum', 'Maximum', 'Countries']

    st.dataframe(region_display, use_container_width=True, hide_index=True)

    # Regional details
    st.subheader("Regional Breakdown")

    for _, row in regional.sort_values('avg_loneliness', ascending=False).iterrows():
        region = row['region']
        countries_in_region = by_country[by_country['region'] == region]

        with st.expander(f"{region} - Average: {row['avg_loneliness']:.1f}%"):
            # Show countries in this region
            for _, c in countries_in_region.iterrows():
                diff_from_avg = c['loneliness_rate'] - stats['avg_loneliness']
                emoji = "" if diff_from_avg > 5 else "" if diff_from_avg < -5 else ""
                st.markdown(f"- **{c['country']}**: {c['loneliness_rate']:.0f}% ({diff_from_avg:+.0f}% from average) {emoji}")

# Tab 3: Research Findings
with tab3:
    render_research_studies([
        ResearchStudy("", "Study 1: The Southern Europe Paradox",
            "Despite strong family cultures, Southern European countries (Greece 62%, Italy 47%, Spain 40%) have the <b>highest loneliness rates</b>.",
            "Cultural expectations of family support may increase loneliness when unmet. Economic crises may have eroded traditional support systems."),
        ResearchStudy("", "Study 2: Nordic Success Story",
            "Nordic countries (Denmark 25%, Sweden 30%) have the <b>lowest loneliness rates</b> despite stereotypes of cold, distant cultures.",
            "Strong social safety nets, community programs, and housing designed for social interaction may compensate for less family-centric culture."),
        ResearchStudy("", "Study 3: The 37 Percentage Point Gap",
            "Between Denmark (25%) and Greece (62%), there's a <b>2.5x difference</b> in loneliness prevalence among older adults.",
            "This massive gap suggests loneliness is not inevitable with aging - policy and cultural factors play crucial roles."),
        ResearchStudy("", "Study 4: Economic Development Not Enough",
            "Wealthy countries like Austria (46%) can have higher loneliness than their economic peers (Germany 37%, Switzerland 26%).",
            "GDP alone doesn't explain loneliness - social policies, housing, and community design matter more."),
        ResearchStudy("", "Study 5: Measurement Challenges",
            "Different survey years (2002-2018) and age groups (65-74 vs 72+ vs 75+) make <b>direct comparisons imperfect</b>.",
            "Longitudinal studies with consistent methodology needed to track true trends and effectiveness of interventions."),
    ])

    st.markdown("### Methodology Notes")
    methods = [
        "Data aggregates people who report feeling lonely 'some of the time', 'most of the time', or 'almost all the time'",
        "Most European data from 2005 (Sundstrm et al. 2009), population 65+",
        "US data from 2018 CIGNA survey, population 72+",
        "England data from 2018 Community Life Survey, ages 65-74",
        "Finland data from 2002 (Savikko et al. 2005), ages 75+",
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Different survey methodologies across countries",
        "Different years of data collection (2002-2018)",
        "Different age thresholds (65+, 72+, 75+)",
        "Cultural differences in interpreting and reporting loneliness",
        "Self-reported data subject to social desirability bias",
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 4: Explorer
with tab4:
    st.subheader("Explore the Data")

    # Country selector
    selected_country = st.selectbox(
        "Select a country:",
        options=by_country['country'].tolist(),
        index=0
    )

    country_data = by_country[by_country['country'] == selected_country].iloc[0]

    col1, col2 = st.columns([1, 1])

    with col1:
        # Gauge chart for selected country
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=country_data['loneliness_rate'],
            delta={'reference': stats['avg_loneliness'], 'relative': False, 'suffix': '%'},
            title={'text': f"Loneliness Rate in {selected_country}"},
            gauge={
                'axis': {'range': [0, 70], 'ticksuffix': '%'},
                'bar': {'color': "#6366f1"},
                'steps': [
                    {'range': [0, 30], 'color': "#dcfce7"},
                    {'range': [30, 45], 'color': "#fef3c7"},
                    {'range': [45, 70], 'color': "#fee2e2"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': stats['avg_loneliness']
                }
            }
        ))

        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"### {selected_country}")
        st.markdown(f"**Loneliness Rate:** {country_data['loneliness_rate']:.0f}%")
        st.markdown(f"**Survey Year:** {country_data['year']}")
        st.markdown(f"**Region:** {country_data['region']}")

        diff = country_data['loneliness_rate'] - stats['avg_loneliness']
        if diff > 0:
            st.error(f" {diff:.0f} percentage points **above** average")
        elif diff < 0:
            st.success(f" {abs(diff):.0f} percentage points **below** average")
        else:
            st.info(" At the average")

        # Rank
        rank = by_country[by_country['loneliness_rate'] >= country_data['loneliness_rate']].shape[0]
        st.markdown(f"**Rank:** {rank} of {stats['total_countries']} (1 = highest loneliness)")

    # Compare two countries
    st.markdown("---")
    st.subheader("Compare Two Countries")

    col1, col2 = st.columns(2)
    with col1:
        country1 = st.selectbox("First country:", options=by_country['country'].tolist(), index=0, key="compare1")
    with col2:
        country2 = st.selectbox("Second country:", options=by_country['country'].tolist(), index=len(by_country)-1, key="compare2")

    if country1 != country2:
        data1 = by_country[by_country['country'] == country1].iloc[0]
        data2 = by_country[by_country['country'] == country2].iloc[0]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=country1,
            x=[country1],
            y=[data1['loneliness_rate']],
            marker_color='#ef4444' if data1['loneliness_rate'] > data2['loneliness_rate'] else '#22c55e',
            text=[f"{data1['loneliness_rate']:.0f}%"],
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            name=country2,
            x=[country2],
            y=[data2['loneliness_rate']],
            marker_color='#ef4444' if data2['loneliness_rate'] > data1['loneliness_rate'] else '#22c55e',
            text=[f"{data2['loneliness_rate']:.0f}%"],
            textposition='outside'
        ))

        fig.update_layout(
            height=350,
            yaxis=dict(range=[0, 70], title='Loneliness Rate (%)'),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        diff = abs(data1['loneliness_rate'] - data2['loneliness_rate'])
        higher = country1 if data1['loneliness_rate'] > data2['loneliness_rate'] else country2
        st.info(f"**{higher}** has a {diff:.0f} percentage point higher loneliness rate")

# Tab 5: Raw Data
with tab5:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["By Country", "Regional Summary"],
        horizontal=True
    )

    if data_view == "By Country":
        display_df = by_country.copy()
        display_df.columns = ['Country', 'Year', 'Loneliness Rate (%)', 'Region']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        csv = by_country.to_csv(index=False)
        st.download_button("Download CSV", csv, "loneliness_by_country.csv", "text/csv")
    else:
        display_df = regional.copy()
        display_df.columns = ['Region', 'Average (%)', 'Minimum (%)', 'Maximum (%)', 'Countries']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        csv = regional.to_csv(index=False)
        st.download_button("Download CSV", csv, "loneliness_regional.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Greece", "Denmark"),  # Which has higher loneliness?
        ("Italy", "Sweden"),
        ("United States", "Germany"),
    ],
    data=by_country,
    name_column="country",
    value_column="loneliness_rate",
    title="Test Your Perception",
    prompt=" Can you guess which country has higher loneliness rates among older adults?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """loneliness_by_country ────┐
 country (PK)            │    regional_summary
 year                    ├───▶  region (PK)
 loneliness_rate         │      avg_loneliness
 region (FK)             │      min_loneliness
                         │      max_loneliness
                         │      country_count"""

SAMPLE_QUERIES = """-- Countries ranked by loneliness
SELECT country, loneliness_rate, region
FROM loneliness_by_country
ORDER BY loneliness_rate DESC;

-- Regional averages
SELECT region,
       ROUND(avg_loneliness, 1) as avg_rate,
       country_count
FROM regional_summary
ORDER BY avg_loneliness DESC;

-- Countries above average
SELECT country, loneliness_rate,
       loneliness_rate - 39 as diff_from_avg
FROM loneliness_by_country
WHERE loneliness_rate > 39
ORDER BY loneliness_rate DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Regional classification", "Survey year tracking", "Statistical aggregation", "Cross-country comparison"]
)

# Footer
render_data_footer(
    data_sources=["Our World in Data", "Sundstrm et al. (2009)", "Savikko et al. (2005)", "ONS (2019)", "CIGNA (2018)"],
    time_period="2002 - 2018\nAges 65+",
    data_points=f"{stats['total_countries']} countries across {stats['regions']} regions",
    credits={"Original research": "Multiple academic sources", "Data compilation": "Our World in Data"},
    dataset_url="https://ourworldindata.org/loneliness-and-social-connections"
)

# Site Footer
render_site_footer()
