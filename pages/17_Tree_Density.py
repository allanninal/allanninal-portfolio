"""
Tree Density Dashboard
Analyzing global tree distribution across 237 countries (Crowther et al. 2015)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.tree_density.database import TreeDensityDatabase
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
    page_title="Tree Density | Allan Ninal",
    page_icon="🌲",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load tree density data from database."""
    with TreeDensityDatabase() as db:
        full_data = db.get_full_data()
        region_summary = db.get_region_summary()
        density_summary = db.get_density_summary()
        per_capita_summary = db.get_per_capita_summary()
        most_trees = db.get_most_trees(20)
        highest_density = db.get_highest_density(20)
        most_per_capita = db.get_most_per_capita(20)
        least_per_capita = db.get_least_per_capita(20)
        stats = db.get_stats()
    return (full_data, region_summary, density_summary, per_capita_summary,
            most_trees, highest_density, most_per_capita, least_per_capita, stats)


# Load data
(full_data, region_summary, density_summary, per_capita_summary,
 most_trees, highest_density, most_per_capita, least_per_capita, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Tree Density", icon="🌲", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Global Tree Density",
    subtitle="Mapping 3 trillion trees across every continent using 429,775 ground-sourced measurements.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | Crowther et al. (2015) Nature"
)

# Key insight banner
render_shocking_fact(
    value=f"3.04 Trillion",
    description=f"Earth has approximately <b>3.04 trillion trees</b> - about <b>422 trees per person</b> globally. <b>{stats['most_trees_country']}</b> has the most with <b>{stats['most_trees_billions']:.0f} billion</b>, while <b>{stats['most_per_capita_country']}</b> has the most per capita at <b>{stats['most_per_capita']:,.0f} trees/person</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['total_trees_trillion']:.1f}T", "Total Trees<br>On Earth"),
    HeroStat(f"{stats['most_trees_billions']:.0f}B", f"{stats['most_trees_country']}<br>Most Trees", "success"),
    HeroStat(f"422", "Trees Per Person<br>Global Average", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Total Trees", "Tree Density", "Trees Per Capita",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Total Trees
with tab1:
    st.subheader("Countries with Most Trees")

    fig = px.bar(
        most_trees,
        x='trees_billions',
        y='entity',
        orientation='h',
        color='trees_billions',
        color_continuous_scale='Greens',
        labels={'trees_billions': 'Trees (Billions)', 'entity': ''}
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
    st.subheader("Trees by Region")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            region_summary,
            values='trees_billions',
            names='region',
            color='region',
            title='Share of World\'s Trees'
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            region_summary.sort_values('trees_billions', ascending=True),
            x='trees_billions',
            y='region',
            orientation='h',
            color='trees_billions',
            color_continuous_scale='Greens',
            labels={'trees_billions': 'Trees (Billions)', 'region': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Distribution")

    fig = px.choropleth(
        full_data,
        locations='entity',
        locationmode='country names',
        color='trees_billions',
        color_continuous_scale='Greens',
        labels={'trees_billions': 'Trees (B)'},
        title='Trees by Country (Billions)'
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

# Tab 2: Tree Density
with tab2:
    st.subheader("Countries with Highest Tree Density (Trees/km²)")

    fig = px.bar(
        highest_density,
        x='trees_per_km2',
        y='entity',
        orientation='h',
        color='trees_per_km2',
        color_continuous_scale='Greens',
        labels={'trees_per_km2': 'Trees per km²', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Density tiers
    st.subheader("Countries by Density Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            density_summary,
            values='countries',
            names='density_tier',
            color='density_tier',
            color_discrete_map={
                'Very High (50k+/km²)': '#166534',
                'High (30-50k/km²)': '#22c55e',
                'Moderate (15-30k/km²)': '#84cc16',
                'Low (5-15k/km²)': '#eab308',
                'Very Low (<5k/km²)': '#f97316'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        density_display = density_summary.copy()
        density_display.columns = ['Tier', 'Countries', 'Avg Density', 'Min', 'Max', 'Avg Per Capita']

        st.dataframe(density_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Density Tiers:**
        - **Very High**: 50,000+ trees/km² (dense forests)
        - **High**: 30,000-50,000/km²
        - **Moderate**: 15,000-30,000/km²
        - **Low**: 5,000-15,000/km²
        - **Very Low**: <5,000/km² (arid/desert regions)
        """)

    # Regional density comparison
    st.subheader("Average Density by Region")

    fig = px.bar(
        region_summary.sort_values('avg_density', ascending=False),
        x='region',
        y='avg_density',
        color='avg_density',
        color_continuous_scale='Greens',
        labels={'region': 'Region', 'avg_density': 'Avg Trees/km²'},
        text='avg_density'
    )

    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Trees Per Capita
with tab3:
    st.subheader("Countries with Most Trees Per Person")

    fig = px.bar(
        most_per_capita,
        x='trees_per_capita',
        y='entity',
        orientation='h',
        color='trees_per_capita',
        color_continuous_scale='Blues',
        labels={'trees_per_capita': 'Trees Per Person', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Countries with Fewest Trees Per Person")

    fig = px.bar(
        least_per_capita.head(20),
        x='trees_per_capita',
        y='entity',
        orientation='h',
        color='trees_per_capita',
        color_continuous_scale='Reds_r',
        labels={'trees_per_capita': 'Trees Per Person', 'entity': ''}
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
        fig = px.pie(
            per_capita_summary,
            values='countries',
            names='per_capita_tier',
            color='per_capita_tier',
            color_discrete_map={
                'Very High (1000+)': '#1e40af',
                'High (200-1000)': '#3b82f6',
                'Moderate (50-200)': '#60a5fa',
                'Low (10-50)': '#93c5fd',
                'Very Low (<10)': '#dbeafe'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        per_capita_display = per_capita_summary.copy()
        per_capita_display.columns = ['Tier', 'Countries', 'Avg Per Capita', 'Min', 'Max', 'Avg Density']

        st.dataframe(per_capita_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Per Capita Tiers:**
        - **Very High**: 1,000+ trees/person (sparsely populated forest nations)
        - **High**: 200-1,000 trees/person
        - **Moderate**: 50-200 trees/person
        - **Low**: 10-50 trees/person
        - **Very Low**: <10 trees/person (dense populations or deserts)
        """)

    # World map - per capita
    st.subheader("Trees Per Person - Global View")

    fig = px.choropleth(
        full_data,
        locations='entity',
        locationmode='country names',
        color='trees_per_capita',
        color_continuous_scale='Blues',
        labels={'trees_per_capita': 'Trees/Person'},
        title='Trees Per Capita by Country'
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
        ResearchStudy("🌍", "Study 1: Three Trillion Trees",
            "Earth has approximately <b>3.04 trillion trees</b> - about <b>8 times more</b> than previous satellite-based estimates suggested.",
            "This groundbreaking Nature study combined 429,775 ground measurements with satellite data to create the most accurate global tree count ever."),
        ResearchStudy("🇷🇺", "Study 2: Russia's Forest Dominance",
            "<b>Russia</b> has more trees than any other country with <b>642 billion trees</b> (21% of global total), followed by <b>Canada</b> with 318 billion.",
            "The boreal forests of Russia and Canada together account for over 30% of all trees on Earth."),
        ResearchStudy("🏝️", "Study 3: The Per Capita Paradox",
            "<b>French Guiana</b> has over <b>20,000 trees per person</b>, while <b>Qatar</b> has less than <b>0.006 trees per person</b>.",
            "Population density and climate create extreme variations - densely populated nations and desert countries have the fewest trees per person."),
        ResearchStudy("🌳", "Study 4: Tropical vs Boreal",
            "<b>Tropical forests</b> have the highest tree density at <b>800+ trees/hectare</b>, while <b>boreal forests</b> cover the most area.",
            "Despite lower density, boreal regions contain more trees due to their vast extent across Russia, Canada, and Scandinavia."),
        ResearchStudy("📉", "Study 5: Human Impact",
            "An estimated <b>15 billion trees are cut</b> each year, with only <b>5 billion planted</b> - a net loss of <b>10 billion annually</b>.",
            "Since human civilization began, tree numbers have fallen by approximately 46%, from 6 trillion to 3 trillion."),
    ])

    st.markdown("### Methodology")
    methods = [
        "429,775 ground-sourced measurements from every continent except Antarctica",
        "Trees defined as woody stems >10 cm diameter at breast height (DBH)",
        "Machine learning models to extrapolate measurements to global scale",
        "Per capita and per km² calculations using World Bank 2014 data"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Snapshot from 2014 - tree cover changes annually",
        "Definition excludes shrubs and small trees (<10 cm DBH)",
        "Some regions have fewer ground measurements than others",
        "Urban trees may be undercounted in some areas"
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
            st.metric("Total Trees", f"{info['trees_billions']:.1f}B")

        with col2:
            st.metric("World Share", f"{info['pct_world_trees']:.2f}%")

        with col3:
            st.metric("Trees/km²", f"{info['trees_per_km2']:,.0f}")

        with col4:
            st.metric("Trees/Person", f"{info['trees_per_capita']:,.0f}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Density Tier", info['density_tier'].split('(')[0].strip())

        with col2:
            st.metric("Per Capita Tier", info['per_capita_tier'].split('(')[0].strip())

        # Regional comparison
        st.subheader(f"How {selected_country} Compares in {info['region']}")

        region_countries = full_data[full_data['region'] == info['region']].sort_values('num_trees', ascending=False)

        colors = ['#22c55e' if c != selected_country else '#ef4444' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='trees_billions',
            y='entity',
            orientation='h',
            labels={'trees_billions': 'Trees (Billions)', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"Trees in {info['region']}",
            height=max(400, len(region_countries) * 20),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        global_avg_per_capita = 422
        if info['trees_per_capita'] >= global_avg_per_capita * 5:
            st.success(f"**{selected_country}** has exceptionally high trees per capita - well above the global average of 422.")
        elif info['trees_per_capita'] >= global_avg_per_capita:
            st.info(f"**{selected_country}** has above-average trees per capita compared to the global average of 422.")
        elif info['trees_per_capita'] >= 50:
            st.warning(f"**{selected_country}** has moderate tree coverage per capita, below the global average of 422.")
        else:
            st.error(f"**{selected_country}** has very low trees per capita - significantly below the global average of 422.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Region Summary", "Density Tiers", "Per Capita Tiers"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "tree_density_full.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "tree_density_regions.csv", "text/csv")

    elif data_view == "Density Tiers":
        st.dataframe(density_summary, use_container_width=True, hide_index=True)
        csv = density_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "tree_density_tiers.csv", "text/csv")

    else:
        st.dataframe(per_capita_summary, use_container_width=True, hide_index=True)
        csv = per_capita_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "tree_density_per_capita.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Russia", "Brazil"),
        ("Canada", "United States"),
        ("Finland", "Sweden"),
    ],
    data=full_data,
    name_column="entity",
    value_column="trees_billions",
    title="Test Your Tree Knowledge",
    prompt="Can you guess which country has MORE trees?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """tree_density ─────────┐
* entity (PK)         │    region_summary
* year                ├──▶ * region (PK)
* region              │    * total_trees
* num_trees           │    * avg_density
* trees_per_km2       │    * avg_per_capita
* trees_per_capita    │
* density_tier        │    density_summary
* per_capita_tier     └──▶ * density_tier (PK)
                           * countries"""

SAMPLE_QUERIES = """-- Countries with most trees
SELECT entity, region, trees_billions, pct_world_trees
FROM tree_density
ORDER BY num_trees DESC
LIMIT 10;

-- Regional tree totals
SELECT region, SUM(num_trees)/1e9 as trees_billions
FROM tree_density
GROUP BY region
ORDER BY trees_billions DESC;

-- Highest density countries
SELECT entity, trees_per_km2, trees_per_capita
FROM tree_density
ORDER BY trees_per_km2 DESC
LIMIT 10;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["429,775 ground measurements", "237 countries/territories", "Trees >10cm DBH", "Per capita and density metrics"]
)

# Footer
render_data_footer(
    data_sources=["Crowther et al. (2015) Nature", "World Bank Population Data"],
    time_period="2014\n237 countries/territories",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "Crowther et al.", "Compilation": "Our World in Data"},
    dataset_url="https://www.nature.com/articles/nature14967"
)

# Site Footer
render_site_footer()
