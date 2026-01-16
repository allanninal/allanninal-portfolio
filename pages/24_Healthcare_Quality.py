"""
Healthcare Access and Quality Index Dashboard
Tracking global healthcare improvements from 1990 to 2015 (IHME 2017)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.healthcare_quality.database import HealthcareQualityDatabase
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
    page_title="Healthcare Quality Index | Allan Ninal",
    page_icon="🏥",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load healthcare quality data from database."""
    with HealthcareQualityDatabase() as db:
        full_data = db.get_full_data()
        latest_data = db.get_latest_data()
        region_summary = db.get_region_summary()
        year_summary = db.get_year_summary()
        tier_summary = db.get_tier_summary()
        top_countries = db.get_top_countries(limit=20)
        bottom_countries = db.get_bottom_countries(limit=20)
        most_improved = db.get_most_improved(limit=20)
        global_trend = db.get_global_trend()
        stats = db.get_stats()
    return (full_data, latest_data, region_summary, year_summary, tier_summary,
            top_countries, bottom_countries, most_improved, global_trend, stats)


# Load data
(full_data, latest_data, region_summary, year_summary, tier_summary,
 top_countries, bottom_countries, most_improved, global_trend, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Healthcare Quality", icon="🏥", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Healthcare Access and Quality Index",
    subtitle="Measuring how well healthcare systems prevent deaths from treatable conditions across 197 countries from 1990 to 2015.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | {stats['years_covered']} | IHME Global Burden of Disease Study"
)

# Key insight banner
render_shocking_fact(
    value=f"{stats['haq_range']:.0f}-Point Gap",
    description=f"In 2015, <b>{stats['highest_haq_country']}</b> achieved a HAQ Index of <b>{stats['highest_haq']:.1f}</b>, while <b>{stats['lowest_haq_country']}</b> scored just <b>{stats['lowest_haq']:.1f}</b>. <b>{stats['most_improved_country']}</b> improved most over 25 years, gaining <b>{stats['most_improved_points']:.1f}</b> points.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['highest_haq']:.0f}", f"{stats['highest_haq_country']}<br>Highest HAQ", "success"),
    HeroStat(f"{stats['avg_haq_2015']:.0f}", "Global Average<br>HAQ Index 2015"),
    HeroStat(f"+{stats['avg_improvement']:.0f}", "Avg Improvement<br>1990-2015", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Tracked", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Rankings", "25-Year Progress", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Rankings
with tab1:
    st.subheader("Healthcare Access and Quality Index Rankings (2015)")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Top 20 Countries")

        fig = px.bar(
            top_countries,
            x='haq_index',
            y='country',
            orientation='h',
            color='haq_tier',
            color_discrete_map={
                'Very High': '#22c55e',
                'High': '#3b82f6',
                'Moderate': '#f97316',
                'Low': '#ef4444',
                'Very Low': '#7f1d1d'
            },
            labels={'haq_index': 'HAQ Index', 'country': '', 'haq_tier': 'HAQ Tier'}
        )

        fig.update_layout(
            height=550,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Bottom 20 Countries")

        fig = px.bar(
            bottom_countries,
            x='haq_index',
            y='country',
            orientation='h',
            color='haq_tier',
            color_discrete_map={
                'Very High': '#22c55e',
                'High': '#3b82f6',
                'Moderate': '#f97316',
                'Low': '#ef4444',
                'Very Low': '#7f1d1d'
            },
            labels={'haq_index': 'HAQ Index', 'country': '', 'haq_tier': 'HAQ Tier'}
        )

        fig.update_layout(
            height=550,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global HAQ Index Distribution (2015)")

    fig = px.choropleth(
        latest_data,
        locations='country',
        locationmode='country names',
        color='haq_index',
        color_continuous_scale='RdYlGn',
        range_color=[20, 95],
        labels={'haq_index': 'HAQ Index'},
        hover_data={'country': True, 'haq_index': ':.1f', 'region': True}
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

    # Tier breakdown
    st.subheader("Countries by HAQ Tier (2015)")

    tier_colors = {
        'Very High': '#22c55e',
        'High': '#3b82f6',
        'Moderate': '#f97316',
        'Low': '#ef4444',
        'Very Low': '#7f1d1d'
    }

    fig = px.pie(
        tier_summary,
        values='countries',
        names='haq_tier',
        color='haq_tier',
        color_discrete_map=tier_colors
    )

    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**HAQ Tiers**: Very High (90+), High (70-90), Moderate (50-70), Low (30-50), Very Low (<30)")

# Tab 2: 25-Year Progress
with tab2:
    st.subheader("Global Healthcare Progress 1990-2015")

    st.markdown("The HAQ Index tracks how healthcare systems have improved over 25 years in preventing deaths from treatable conditions.")

    # Global trend
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=global_trend['year'],
        y=global_trend['avg_haq'],
        mode='lines+markers',
        name='Global Average',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10)
    ))

    fig.add_trace(go.Scatter(
        x=global_trend['year'],
        y=global_trend['max_haq'],
        mode='lines',
        name='Maximum',
        line=dict(color='#22c55e', width=2, dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=global_trend['year'],
        y=global_trend['min_haq'],
        mode='lines',
        name='Minimum',
        line=dict(color='#ef4444', width=2, dash='dash')
    ))

    fig.update_layout(
        title='Global HAQ Index Trend (1990-2015)',
        height=450,
        xaxis_title='Year',
        yaxis_title='HAQ Index',
        yaxis_range=[0, 100],
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "1990 Average",
            f"{global_trend[global_trend['year'] == 1990]['avg_haq'].values[0]:.1f}",
        )

    with col2:
        improvement = global_trend[global_trend['year'] == 2015]['avg_haq'].values[0] - global_trend[global_trend['year'] == 1990]['avg_haq'].values[0]
        st.metric(
            "25-Year Improvement",
            f"+{improvement:.1f} points",
        )

    with col3:
        st.metric(
            "2015 Average",
            f"{global_trend[global_trend['year'] == 2015]['avg_haq'].values[0]:.1f}",
        )

    # Most improved countries
    st.subheader("Most Improved Countries (1990-2015)")

    fig = px.bar(
        most_improved,
        x='improvement',
        y='country',
        orientation='h',
        color='improvement_tier',
        color_discrete_map={
            'Dramatic': '#22c55e',
            'Strong': '#3b82f6',
            'Moderate': '#f97316',
            'Modest': '#fbbf24',
            'Minimal': '#94a3b8'
        },
        labels={'improvement': 'Points Gained', 'country': '', 'improvement_tier': 'Improvement Level'}
    )

    fig.update_layout(
        height=550,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**{stats['most_improved_country']}** improved the most, gaining **{stats['most_improved_points']:.1f}** points on the HAQ Index from 1990 to 2015.")

    # Year-over-year comparison
    st.subheader("Progress Summary")

    progress_data = []
    years = [1990, 1995, 2000, 2005, 2010, 2015]
    for year in years:
        year_data = full_data[full_data['year'] == year]
        progress_data.append({
            'Year': year,
            'Avg HAQ': year_data['haq_index'].mean(),
            'Very High Tier': len(year_data[year_data['haq_tier'] == 'Very High']),
            'Very Low Tier': len(year_data[year_data['haq_tier'] == 'Very Low'])
        })

    progress_df = pd.DataFrame(progress_data)

    st.dataframe(progress_df, use_container_width=True, hide_index=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Healthcare Quality by Region (2015)")

    # Regional bar chart
    fig = px.bar(
        region_summary.sort_values('avg_haq', ascending=True),
        x='avg_haq',
        y='region',
        orientation='h',
        color='avg_haq',
        color_continuous_scale='RdYlGn',
        labels={'avg_haq': 'Average HAQ Index', 'region': ''}
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

    display_summary = region_summary.copy()
    display_summary.columns = ['Region', 'Countries', 'Avg HAQ', 'Min HAQ', 'Max HAQ', 'Avg Improvement']

    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # Regional trends
    st.subheader("Regional Trends Over Time")

    selected_regions = st.multiselect(
        "Select regions to compare:",
        options=region_summary['region'].tolist(),
        default=['Europe', 'North America', 'Sub-Saharan Africa', 'South Asia']
    )

    if selected_regions:
        regional_trends = full_data[full_data['region'].isin(selected_regions)].groupby(['region', 'year']).agg(
            avg_haq=('haq_index', 'mean')
        ).reset_index()

        fig = px.line(
            regional_trends,
            x='year',
            y='avg_haq',
            color='region',
            markers=True,
            labels={'avg_haq': 'Average HAQ Index', 'year': 'Year', 'region': 'Region'}
        )

        fig.update_layout(
            height=450,
            yaxis_range=[0, 100],
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Regional disparity
    st.subheader("Within-Region Disparity (2015)")

    fig = go.Figure()

    for _, row in region_summary.iterrows():
        fig.add_trace(go.Box(
            y=latest_data[latest_data['region'] == row['region']]['haq_index'],
            name=row['region'],
            boxpoints='all',
            jitter=0.3,
        ))

    fig.update_layout(
        height=500,
        yaxis_title='HAQ Index',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Box plots show the distribution within each region.** Some regions like Sub-Saharan Africa have wide variation, while Europe is more uniform.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🏥", "Study 1: Global Improvement",
            f"The global average HAQ Index increased from <b>{global_trend[global_trend['year'] == 1990]['avg_haq'].values[0]:.1f}</b> in 1990 to <b>{global_trend[global_trend['year'] == 2015]['avg_haq'].values[0]:.1f}</b> in 2015.",
            "Healthcare access and quality improved everywhere, but the gap between best and worst performers persists."),
        ResearchStudy("🇦🇩", "Study 2: Andorra Leads the World",
            f"<b>Andorra</b> achieved the highest HAQ Index of <b>{stats['highest_haq']:.1f}</b> in 2015, followed by Iceland, Switzerland, and Norway.",
            "Small wealthy nations with universal healthcare consistently rank highest."),
        ResearchStudy("🌍", "Study 3: Sub-Saharan Africa Lags",
            "Sub-Saharan Africa has the lowest regional average, with many countries scoring below 50 on the HAQ Index.",
            "Limited healthcare infrastructure, workforce shortages, and disease burden contribute to lower scores."),
        ResearchStudy("🚀", "Study 4: Rapid Improvers",
            f"<b>{stats['most_improved_country']}</b> improved most dramatically, gaining <b>{stats['most_improved_points']:.1f}</b> points over 25 years.",
            "Targeted investments in healthcare infrastructure can drive significant improvements."),
        ResearchStudy("📊", "Study 5: The 66-Point Gap",
            f"In 2015, a <b>{stats['haq_range']:.0f}-point gap</b> separates the highest and lowest performers.",
            "Where you are born largely determines your access to quality healthcare that can save your life."),
    ])

    st.markdown("### About the HAQ Index")
    st.markdown("""
    The Healthcare Access and Quality (HAQ) Index measures how well healthcare systems prevent deaths from **32 causes** that should not be fatal with effective medical care.

    **What it measures:**
    - Deaths from vaccine-preventable diseases
    - Maternal and neonatal mortality
    - Deaths from treatable cancers
    - Cardiovascular disease mortality
    - Deaths from appendicitis, hernias, and other surgical conditions
    """)

    st.markdown("### Methodology")
    methods = [
        "Based on Global Burden of Disease Study mortality data",
        "Uses age-standardized mortality rates for 32 causes amenable to healthcare",
        "Scaled 0-100 where 100 represents no mortality from amenable causes",
        "Accounts for population structure and competing risks"
    ]
    for method in methods:
        st.markdown(f"- {method}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    with HealthcareQualityDatabase() as db:
        countries_list = db.get_countries_list()

    selected_country = st.selectbox(
        "Select a country:",
        options=countries_list,
        index=countries_list.index('United States') if 'United States' in countries_list else 0
    )

    with HealthcareQualityDatabase() as db:
        country_data = db.get_country_data(selected_country)
        country_trend = db.get_country_trend(selected_country)

    if len(country_data) > 0:
        latest_info = country_data[country_data['year'] == 2015].iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("2015 HAQ Index", f"{latest_info['haq_index']:.1f}")

        with col2:
            st.metric("HAQ Tier", latest_info['haq_tier'])

        with col3:
            st.metric("Region", latest_info['region'])

        with col4:
            if pd.notna(latest_info['improvement']):
                st.metric("25-Year Change", f"+{latest_info['improvement']:.1f}")
            else:
                st.metric("25-Year Change", "N/A")

        # Country trend
        st.subheader(f"{selected_country} HAQ Index Over Time")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_trend['year'],
            y=country_trend['haq_index'],
            mode='lines+markers',
            name=selected_country,
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=10)
        ))

        # Add global average for comparison
        global_avg = full_data.groupby('year')['haq_index'].mean().reset_index()

        fig.add_trace(go.Scatter(
            x=global_avg['year'],
            y=global_avg['haq_index'],
            mode='lines',
            name='Global Average',
            line=dict(color='#94a3b8', width=2, dash='dash')
        ))

        fig.update_layout(
            height=400,
            xaxis_title='Year',
            yaxis_title='HAQ Index',
            yaxis_range=[0, 100],
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Compare with similar countries
        st.subheader("Compare with Other Countries")

        # Get countries in same region (excluding selected country)
        region_countries = [c for c in latest_data[latest_data['region'] == latest_info['region']]['country'].tolist() if c != selected_country]
        available_options = [c for c in countries_list if c != selected_country]

        # Only use region countries as default if they exist in available options
        default_selection = [c for c in region_countries[:3] if c in available_options]

        compare_countries = st.multiselect(
            "Select countries to compare:",
            options=available_options,
            default=default_selection,
            max_selections=5
        )

        if compare_countries:
            with HealthcareQualityDatabase() as db:
                compare_data = db.compare_countries([selected_country] + compare_countries)

            fig = px.line(
                compare_data,
                x='year',
                y='haq_index',
                color='country',
                markers=True,
                labels={'haq_index': 'HAQ Index', 'year': 'Year', 'country': 'Country'}
            )

            fig.update_layout(
                height=450,
                yaxis_range=[0, 100],
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if latest_info['haq_index'] >= 90:
            st.success(f"**{selected_country}** has world-leading healthcare access and quality.")
        elif latest_info['haq_index'] >= 70:
            st.info(f"**{selected_country}** has strong healthcare outcomes, above the global average.")
        elif latest_info['haq_index'] >= 50:
            st.warning(f"**{selected_country}** has moderate healthcare quality with room for improvement.")
        else:
            st.error(f"**{selected_country}** faces significant healthcare access and quality challenges.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset (2015)", "All Years", "Region Summary", "Year Summary", "Tier Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset (2015)":
        display_data = latest_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "healthcare_quality_2015.csv", "text/csv")

    elif data_view == "All Years":
        display_data = full_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "healthcare_quality_all.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "healthcare_quality_regions.csv", "text/csv")

    elif data_view == "Year Summary":
        st.dataframe(year_summary, use_container_width=True, hide_index=True)
        csv = year_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "healthcare_quality_years.csv", "text/csv")

    else:
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "healthcare_quality_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Andorra", "United States"),
        ("South Korea", "Japan"),
        ("Ethiopia", "India"),
    ],
    data=latest_data,
    name_column="country",
    value_column="haq_index",
    title="Test Your Knowledge",
    prompt="Can you guess which country has the HIGHER Healthcare Access and Quality Index?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """healthcare_quality ────────┐
* country, year (PK)       │    region_summary
* haq_index                ├──▶ * region (PK)
* region                   │    * avg_haq
* haq_tier                 │    * avg_improvement
* improvement              │
* improvement_tier         │    year_summary
                           └──▶ * year (PK)
                                * avg_haq
                                * min_haq, max_haq"""

SAMPLE_QUERIES = """-- Top countries by HAQ Index (2015)
SELECT country, region, haq_index, haq_tier
FROM healthcare_quality
WHERE year = 2015
ORDER BY haq_index DESC;

-- Most improved countries
SELECT country, region, improvement, improvement_pct
FROM healthcare_quality
WHERE year = 2015
ORDER BY improvement DESC;

-- Regional comparison
SELECT region, avg_haq, avg_improvement
FROM region_summary
ORDER BY avg_haq DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["197 countries tracked", "25-year time series (1990-2015)", "Regional analysis", "Improvement metrics"]
)

# Footer
render_data_footer(
    data_sources=["Institute for Health Metrics and Evaluation (IHME)", "Global Burden of Disease Study 2015"],
    time_period="1990-2015",
    data_points=f"{stats['countries']} countries, 6 time points",
    credits={"Research": "IHME / University of Washington", "Publication": "The Lancet 2017"},
    dataset_url="https://ourworldindata.org/grapher/healthcare-access-and-quality-index"
)

# Site Footer
render_site_footer()
