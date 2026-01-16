"""
Plastic Ocean Pollution Dashboard
Analyzing riverine plastic emissions to oceans across 163 countries (Meijer et al. 2021)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.plastic_ocean.database import PlasticOceanDatabase
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
    page_title="Plastic Ocean Pollution | Allan Ninal",
    page_icon="🌊",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load plastic ocean data from database."""
    with PlasticOceanDatabase() as db:
        full_data = db.get_full_data()
        region_summary = db.get_region_summary()
        ocean_tier_summary = db.get_ocean_tier_summary()
        per_capita_summary = db.get_per_capita_summary()
        top_ocean = db.get_top_ocean_emitters(20)
        top_mismanaged = db.get_top_mismanaged(20)
        top_per_capita = db.get_top_per_capita_ocean(20)
        top_probability = db.get_highest_probability(20)
        stats = db.get_stats()
    return (full_data, region_summary, ocean_tier_summary, per_capita_summary,
            top_ocean, top_mismanaged, top_per_capita, top_probability, stats)


# Load data
(full_data, region_summary, ocean_tier_summary, per_capita_summary,
 top_ocean, top_mismanaged, top_per_capita, top_probability, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Plastic Ocean", icon="🌊", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Plastic Ocean Pollution",
    subtitle="Tracking how mismanaged plastic waste reaches the ocean through rivers across 163 countries.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | Meijer et al. (2021) Science Advances"
)

# Key insight banner
render_shocking_fact(
    value=f"980,000 tonnes",
    description=f"Nearly <b>1 million tonnes</b> of plastic reach the ocean via rivers each year. <b>{stats['top_emitter']}</b> alone accounts for <b>{stats['top_emitter_share']:.1f}%</b> of global river plastic emissions, with <b>{stats['top_per_capita']:.2f} kg/person</b> reaching the ocean.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"979 kt", "Plastic to Ocean<br>Per Year"),
    HeroStat(f"36%", f"{stats['top_emitter']}<br>Largest Source", "success"),
    HeroStat(f"1000+", "Rivers Account for<br>80% of Emissions", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Ocean Emissions", "Mismanaged Waste", "Per Capita",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Ocean Emissions
with tab1:
    st.subheader("Countries with Most Plastic Reaching Ocean")

    fig = px.bar(
        top_ocean,
        x='ocean_kt',
        y='entity',
        orientation='h',
        color='ocean_kt',
        color_continuous_scale='Blues',
        labels={'ocean_kt': 'Plastic to Ocean (kt)', 'entity': ''}
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
    st.subheader("Ocean Emissions by Region")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            region_summary,
            values='ocean_kt',
            names='region',
            color='region',
            title='Share of Global Riverine Plastic to Ocean'
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            region_summary.sort_values('ocean_kt', ascending=True),
            x='ocean_kt',
            y='region',
            orientation='h',
            color='ocean_kt',
            color_continuous_scale='Blues',
            labels={'ocean_kt': 'Plastic (kt)', 'region': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Ocean Plastic Emissions Map")

    fig = px.choropleth(
        full_data,
        locations='entity',
        locationmode='country names',
        color='ocean_kt',
        color_continuous_scale='Blues',
        labels={'ocean_kt': 'Plastic (kt)'},
        title='Riverine Plastic Emissions to Ocean by Country (kt/year)'
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

    # Ocean emission tiers
    st.subheader("Countries by Ocean Emission Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        tier_data = ocean_tier_summary[ocean_tier_summary['countries'] > 0]
        fig = px.pie(
            tier_data,
            values='countries',
            names='ocean_tier',
            color='ocean_tier',
            color_discrete_map={
                'Very High (5%+)': '#1e3a8a',
                'High (1-5%)': '#3b82f6',
                'Moderate (0.1-1%)': '#60a5fa',
                'Low (0.01-0.1%)': '#93c5fd',
                'Very Low (<0.01%)': '#dbeafe'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tier_display = ocean_tier_summary.copy()
        tier_display.columns = ['Tier', 'Countries', 'Total %', 'Avg %', 'Min %', 'Max %', 'Total Emissions']

        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Ocean Emission Tiers (% of global):**
        - **Very High**: 5%+ of global ocean plastics
        - **High**: 1-5%
        - **Moderate**: 0.1-1%
        - **Low**: 0.01-0.1%
        - **Very Low**: <0.01%
        """)

# Tab 2: Mismanaged Waste
with tab2:
    st.subheader("Countries with Most Mismanaged Plastic Waste")

    st.markdown("Mismanaged waste is plastic that is littered or inadequately disposed, making it susceptible to entering waterways.")

    fig = px.bar(
        top_mismanaged,
        x='mismanaged_kt',
        y='entity',
        orientation='h',
        color='mismanaged_kt',
        color_continuous_scale='Reds',
        labels={'mismanaged_kt': 'Mismanaged Waste (kt)', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Comparison: Mismanaged vs Ocean Emissions
    st.subheader("Mismanaged Waste vs Ocean Emissions")

    st.markdown("Not all mismanaged plastic reaches the ocean. The emission probability depends on proximity to rivers and coastlines.")

    # Get top countries by mismanaged waste
    top_compare = top_mismanaged.head(15).copy()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=top_compare['entity'],
        x=top_compare['mismanaged_kt'],
        name='Mismanaged Waste',
        orientation='h',
        marker_color='#ef4444'
    ))

    # Get ocean data for same countries
    ocean_data = full_data[full_data['entity'].isin(top_compare['entity'])][['entity', 'ocean_kt']]
    ocean_dict = dict(zip(ocean_data['entity'], ocean_data['ocean_kt']))
    top_compare['ocean_kt_val'] = top_compare['entity'].map(ocean_dict)

    fig.add_trace(go.Bar(
        y=top_compare['entity'],
        x=top_compare['ocean_kt_val'],
        name='Reaches Ocean',
        orientation='h',
        marker_color='#3b82f6'
    ))

    fig.update_layout(
        height=500,
        barmode='group',
        xaxis_title='Plastic (kt)',
        yaxis={'categoryorder': 'total ascending'},
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Highest probability countries
    st.subheader("Countries with Highest Emission Probability")

    st.markdown("These countries have the highest probability of mismanaged plastic reaching the ocean (due to river/coastal proximity).")

    fig = px.bar(
        top_probability,
        x='probability',
        y='entity',
        orientation='h',
        color='probability',
        color_continuous_scale='Oranges',
        labels={'probability': 'Probability (%)', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Per Capita
with tab3:
    st.subheader("Highest Per Capita Ocean Plastic Emissions (kg/person/year)")

    fig = px.bar(
        top_per_capita,
        x='ocean_per_capita',
        y='entity',
        orientation='h',
        color='ocean_per_capita',
        color_continuous_scale='Purples',
        labels={'ocean_per_capita': 'kg/person/year', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Per capita tiers
    st.subheader("Countries by Per Capita Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        pc_data = per_capita_summary[per_capita_summary['countries'] > 0]
        fig = px.pie(
            pc_data,
            values='countries',
            names='per_capita_tier',
            color='per_capita_tier',
            color_discrete_map={
                'Very High (1+ kg)': '#7c3aed',
                'High (0.1-1 kg)': '#a78bfa',
                'Moderate (0.01-0.1 kg)': '#c4b5fd',
                'Low (<0.01 kg)': '#ddd6fe',
                'Zero': '#f3f4f6'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        pc_display = per_capita_summary.copy()
        pc_display.columns = ['Tier', 'Countries', 'Avg kg', 'Min kg', 'Max kg', 'Total Emissions']

        st.dataframe(pc_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Per Capita Tiers (kg/person/year):**
        - **Very High**: 1+ kg reaching ocean
        - **High**: 0.1-1 kg
        - **Moderate**: 0.01-0.1 kg
        - **Low**: <0.01 kg
        - **Zero**: No ocean emissions
        """)

    # World map - per capita
    st.subheader("Per Capita Ocean Emissions - Global View")

    fig = px.choropleth(
        full_data[full_data['ocean_per_capita'] > 0],
        locations='entity',
        locationmode='country names',
        color='ocean_per_capita',
        color_continuous_scale='Purples',
        labels={'ocean_per_capita': 'kg/person'},
        title='Per Capita Plastic to Ocean (kg/person/year)'
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
        ResearchStudy("🇵🇭", "Study 1: Philippines Dominates",
            "The <b>Philippines</b> alone accounts for <b>36% of all river plastic</b> entering the ocean, despite having just 1.4% of world population.",
            "A combination of high population density, extensive coastline, poor waste management, and monsoon flooding creates this outsized impact."),
        ResearchStudy("🌏", "Study 2: Asia's 80% Share",
            "<b>Asia</b> contributes over <b>80% of all riverine plastic</b> reaching the ocean, with Philippines, India, and Malaysia leading.",
            "Rapid economic growth outpaced waste management infrastructure in many Asian nations."),
        ResearchStudy("🏞️", "Study 3: Rivers Matter More",
            "<b>Over 1,000 rivers</b> account for <b>80% of ocean plastic emissions</b> - previously only 20 rivers were thought to be major sources.",
            "This finding shifted focus from a few large rivers to many smaller ones, especially in Southeast Asia and Africa."),
        ResearchStudy("📊", "Study 4: The Conversion Gap",
            "Only <b>1.6%</b> of mismanaged plastic globally reaches the ocean - the rest stays on land or in rivers.",
            "Emission probability varies from 0% (landlocked/well-managed) to 35%+ (island nations with poor waste management)."),
        ResearchStudy("🇮🇳", "Study 5: India's Paradox",
            "<b>India</b> has the most mismanaged plastic waste (21% of global) but ranks 3rd in ocean emissions due to lower emission probability.",
            "Geography matters - distance from coast and river systems affects how much waste actually reaches the ocean."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Modeled plastic transport through 50,000+ river catchments worldwide",
        "Combined mismanaged waste data with hydrological models",
        "Calculated emission probability based on distance to rivers/coast",
        "Validated against field measurements in multiple rivers"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Single year snapshot (2015) - may not reflect current situation",
        "Waste management data varies in quality by country",
        "Does not include direct coastal littering (only riverine)",
        "Marine microplastics from other sources not included"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(full_data['entity'].unique()),
        index=sorted(full_data['entity'].unique()).index('Philippines') if 'Philippines' in full_data['entity'].unique() else 0
    )

    country_data = full_data[full_data['entity'] == selected_country]

    if len(country_data) > 0:
        info = country_data.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Ocean Emissions", f"{info['ocean_kt']:.1f} kt")

        with col2:
            st.metric("Global Share", f"{info['share_global_ocean']:.2f}%")

        with col3:
            st.metric("Per Capita", f"{info['ocean_per_capita']:.3f} kg")

        with col4:
            st.metric("Mismanaged Waste", f"{info['mismanaged_kt']:.0f} kt")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Emission Probability", f"{info['probability']:.1f}%")

        with col2:
            st.metric("Waste Per Capita", f"{info['waste_per_capita']:.1f} kg")

        with col3:
            st.metric("Ocean Tier", info['ocean_tier'].split('(')[0].strip() if pd.notna(info['ocean_tier']) else "N/A")

        # Breakdown
        st.subheader("Waste Flow Breakdown")

        if info['mismanaged_waste'] > 0:
            flow_data = pd.DataFrame({
                'Stage': ['Mismanaged\nWaste', 'Reaches\nOcean'],
                'Tonnes': [info['mismanaged_waste'], info['ocean_emissions']]
            })

            fig = px.funnel(
                flow_data,
                x='Tonnes',
                y='Stage',
                color='Stage',
                color_discrete_sequence=['#ef4444', '#3b82f6']
            )

            fig.update_layout(
                height=300,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

            conversion = (info['ocean_emissions'] / info['mismanaged_waste'] * 100) if info['mismanaged_waste'] > 0 else 0
            st.info(f"**{conversion:.2f}%** of {selected_country}'s mismanaged plastic waste reaches the ocean via rivers.")

        # Regional comparison
        st.subheader(f"How {selected_country} Compares in {info['region']}")

        with PlasticOceanDatabase() as db:
            region_countries = db.get_by_region(info['region'])

        colors = ['#3b82f6' if c != selected_country else '#ef4444' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='ocean_kt',
            y='entity',
            orientation='h',
            labels={'ocean_kt': 'Plastic to Ocean (kt)', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"Ocean Plastic Emissions in {info['region']}",
            height=max(400, len(region_countries) * 20),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if info['share_global_ocean'] >= 5:
            st.error(f"**{selected_country}** is among the largest sources of ocean plastic globally - urgent intervention needed.")
        elif info['share_global_ocean'] >= 1:
            st.warning(f"**{selected_country}** is a significant contributor to ocean plastic pollution.")
        elif info['share_global_ocean'] >= 0.1:
            st.info(f"**{selected_country}** has moderate ocean plastic emissions.")
        else:
            st.success(f"**{selected_country}** has relatively low ocean plastic emissions.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Region Summary", "Ocean Emission Tiers", "Per Capita Tiers"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "plastic_ocean_full.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "plastic_ocean_regions.csv", "text/csv")

    elif data_view == "Ocean Emission Tiers":
        st.dataframe(ocean_tier_summary, use_container_width=True, hide_index=True)
        csv = ocean_tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "plastic_ocean_tiers.csv", "text/csv")

    else:
        st.dataframe(per_capita_summary, use_container_width=True, hide_index=True)
        csv = per_capita_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "plastic_ocean_per_capita.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Philippines", "Indonesia"),
        ("India", "China"),
        ("Malaysia", "Thailand"),
    ],
    data=full_data,
    name_column="entity",
    value_column="ocean_kt",
    title="Test Your Plastic Pollution Knowledge",
    prompt="Can you guess which country sends MORE plastic to the ocean?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """plastic_ocean ────────┐
* entity (PK)         │    region_summary
* year                ├──▶ * region (PK)
* mismanaged_waste    │    * total_ocean_emissions
* ocean_emissions     │    * avg_per_capita
* probability         │
* share_global_ocean  │    ocean_tier_summary
* ocean_per_capita    └──▶ * tier (PK)
* ocean_tier               * countries"""

SAMPLE_QUERIES = """-- Top ocean plastic emitters
SELECT entity, region, ocean_kt, share_global_ocean
FROM plastic_ocean
ORDER BY ocean_emissions DESC
LIMIT 10;

-- Regional ocean emissions
SELECT region, ocean_kt, avg_ocean_per_capita
FROM region_summary
ORDER BY ocean_kt DESC;

-- Highest emission probability
SELECT entity, probability, ocean_kt
FROM plastic_ocean
WHERE probability > 0
ORDER BY probability DESC
LIMIT 10;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["50,000+ river catchments modeled", "163 countries", "Emission probability analysis", "Per capita metrics"]
)

# Footer
render_data_footer(
    data_sources=["Meijer et al. (2021) Science Advances", "Our World in Data"],
    time_period="2015\n163 countries",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "Meijer et al.", "Compilation": "Our World in Data"},
    dataset_url="https://advances.sciencemag.org/content/7/18/eaaz5803"
)

# Site Footer
render_site_footer()
