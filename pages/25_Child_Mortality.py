"""
Child Mortality Rates Dashboard
Tracking 216 years of progress saving children's lives (Gapminder v10, 2017)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.child_mortality.database import ChildMortalityDatabase
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
    page_title="Child Mortality Rates | Allan Ninal",
    page_icon="👶",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load child mortality data from database."""
    with ChildMortalityDatabase() as db:
        full_data = db.get_full_data()
        latest_data = db.get_latest_data()
        region_summary = db.get_region_summary()
        year_summary = db.get_year_summary()
        tier_summary = db.get_tier_summary()
        lowest_mortality = db.get_lowest_mortality(limit=20)
        highest_mortality = db.get_highest_mortality(limit=20)
        most_improved = db.get_most_improved(limit=20)
        global_trend = db.get_global_trend()
        historical_trend = db.get_historical_trend()
        era_comparison = db.get_era_comparison()
        stats = db.get_stats()
    return (full_data, latest_data, region_summary, year_summary, tier_summary,
            lowest_mortality, highest_mortality, most_improved, global_trend,
            historical_trend, era_comparison, stats)


# Load data
(full_data, latest_data, region_summary, year_summary, tier_summary,
 lowest_mortality, highest_mortality, most_improved, global_trend,
 historical_trend, era_comparison, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Child Mortality", icon="👶", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Child Mortality Rates (1800-2016)",
    subtitle="One of humanity's greatest achievements: how we reduced child deaths from 1-in-2 to 1-in-25 over 200 years.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | {stats['years_covered']} | Gapminder v10"
)

# Key insight banner
render_shocking_fact(
    value=f"{stats['global_improvement_pct']:.0f}% Reduction",
    description=f"Global child mortality dropped from <b>{stats['avg_mortality_1950']:.0f}</b> to <b>{stats['avg_mortality_2016']:.0f}</b> per 1,000 births since 1950. <b>{stats['lowest_mortality_country']}</b> now has the world's lowest rate at <b>{stats['lowest_mortality']:.1f}</b>, while <b>{stats['highest_mortality_country']}</b> has the highest at <b>{stats['highest_mortality']:.1f}</b>.",
    style="success"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['lowest_mortality']:.1f}", f"{stats['lowest_mortality_country']}<br>Lowest Rate", "success"),
    HeroStat(f"{stats['avg_mortality_2016']:.0f}", "Global Average<br>2016 (per 1,000)"),
    HeroStat(f"{stats['most_improved_pct']:.0f}%", f"{stats['most_improved_country']}<br>Most Improved", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Tracked", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Rankings", "216 Years of Progress", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Rankings
with tab1:
    st.subheader("Child Mortality Rankings (2016)")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Lowest Mortality (Safest for Children)")

        fig = px.bar(
            lowest_mortality,
            x='mortality_rate',
            y='country',
            orientation='h',
            color='mortality_tier',
            color_discrete_map={
                'Very Low': '#22c55e',
                'Low': '#3b82f6',
                'Moderate': '#f97316',
                'High': '#ef4444',
                'Very High': '#7f1d1d'
            },
            labels={'mortality_rate': 'Deaths per 1,000', 'country': '', 'mortality_tier': 'Tier'}
        )

        fig.update_layout(
            height=550,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Highest Mortality (Most Vulnerable)")

        fig = px.bar(
            highest_mortality,
            x='mortality_rate',
            y='country',
            orientation='h',
            color='mortality_tier',
            color_discrete_map={
                'Very Low': '#22c55e',
                'Low': '#3b82f6',
                'Moderate': '#f97316',
                'High': '#ef4444',
                'Very High': '#7f1d1d'
            },
            labels={'mortality_rate': 'Deaths per 1,000', 'country': '', 'mortality_tier': 'Tier'}
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
    st.subheader("Global Child Mortality Distribution (2016)")

    fig = px.choropleth(
        latest_data,
        locations='country',
        locationmode='country names',
        color='mortality_rate',
        color_continuous_scale='RdYlGn_r',
        range_color=[0, 130],
        labels={'mortality_rate': 'Deaths per 1,000'},
        hover_data={'country': True, 'mortality_rate': ':.1f', 'region': True}
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
    st.subheader("Countries by Mortality Tier (2016)")

    tier_colors = {
        'Very Low': '#22c55e',
        'Low': '#3b82f6',
        'Moderate': '#f97316',
        'High': '#ef4444',
        'Very High': '#7f1d1d'
    }

    fig = px.pie(
        tier_summary,
        values='countries',
        names='mortality_tier',
        color='mortality_tier',
        color_discrete_map=tier_colors
    )

    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Tiers**: Very Low (<10), Low (10-25), Moderate (25-50), High (50-100), Very High (100+) per 1,000 live births")

# Tab 2: 216 Years of Progress
with tab2:
    st.subheader("Two Centuries of Saving Children's Lives")

    st.markdown("""
    In 1800, nearly **half of all children** died before their 5th birthday. Today, it's about **1 in 25**.
    This is one of humanity's greatest achievements.
    """)

    # Historical trend
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=historical_trend['year'],
        y=historical_trend['avg_rate'],
        mode='lines',
        name='Global Average',
        line=dict(color='#3b82f6', width=2),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))

    fig.update_layout(
        title='Global Child Mortality Rate (1800-2016)',
        height=450,
        xaxis_title='Year',
        yaxis_title='Deaths per 1,000 Live Births',
        yaxis_range=[0, 500],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Era comparison
    st.subheader("Progress by Era")

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            era_comparison,
            x='era',
            y='avg_rate',
            color='avg_rate',
            color_continuous_scale='RdYlGn_r',
            labels={'avg_rate': 'Avg Deaths per 1,000', 'era': 'Era'}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Key Milestones")
        st.markdown("""
        - **1800-1900**: Pre-modern medicine, ~400/1,000
        - **1901-1950**: Vaccines emerge, ~200/1,000
        - **1951-1980**: Antibiotics widespread, ~120/1,000
        - **1981-2000**: ORT saves millions, ~70/1,000
        - **2001-2016**: Modern healthcare, ~30/1,000
        """)

    # Most improved countries
    st.subheader("Most Improved Countries (1950-2016)")

    fig = px.bar(
        most_improved,
        x='improvement_pct',
        y='country',
        orientation='h',
        color='improvement_tier',
        color_discrete_map={
            'Near Elimination': '#22c55e',
            'Dramatic': '#3b82f6',
            'Strong': '#f97316',
            'Moderate': '#fbbf24',
            'Limited': '#94a3b8'
        },
        labels={'improvement_pct': '% Reduction', 'country': '', 'improvement_tier': 'Improvement'}
    )

    fig.update_layout(
        height=550,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**{stats['most_improved_country']}** reduced child mortality by **{stats['most_improved_pct']:.0f}%** since 1950 - from over 130 deaths per 1,000 to just 3.")

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Child Mortality by Region (2016)")

    # Regional bar chart
    fig = px.bar(
        region_summary.sort_values('avg_rate', ascending=False),
        x='avg_rate',
        y='region',
        orientation='h',
        color='avg_rate',
        color_continuous_scale='RdYlGn_r',
        labels={'avg_rate': 'Avg Deaths per 1,000', 'region': ''}
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
    display_summary.columns = ['Region', 'Countries', 'Avg Rate', 'Min Rate', 'Max Rate', 'Avg Improvement %']

    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # Regional trends
    st.subheader("Regional Trends Over Time")

    selected_regions = st.multiselect(
        "Select regions to compare:",
        options=region_summary['region'].tolist(),
        default=['Europe', 'North America', 'Sub-Saharan Africa', 'South Asia'][:4]
    )

    if selected_regions:
        # Get data for selected regions from 1950 onwards
        regional_data = full_data[(full_data['region'].isin(selected_regions)) & (full_data['year'] >= 1950)]
        regional_trends = regional_data.groupby(['region', 'year']).agg(
            avg_rate=('mortality_rate', 'mean')
        ).reset_index()

        fig = px.line(
            regional_trends,
            x='year',
            y='avg_rate',
            color='region',
            markers=False,
            labels={'avg_rate': 'Avg Deaths per 1,000', 'year': 'Year', 'region': 'Region'}
        )

        fig.update_layout(
            height=450,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Regional disparity
    st.subheader("Within-Region Disparity (2016)")

    fig = go.Figure()

    for _, row in region_summary.iterrows():
        fig.add_trace(go.Box(
            y=latest_data[latest_data['region'] == row['region']]['mortality_rate'],
            name=row['region'],
            boxpoints='all',
            jitter=0.3,
        ))

    fig.update_layout(
        height=500,
        yaxis_title='Deaths per 1,000',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Box plots show the distribution within each region.** Sub-Saharan Africa has both the highest average and widest variation.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📉", "Study 1: The Great Decline",
            f"Global child mortality fell <b>{stats['global_improvement_pct']:.0f}%</b> since 1950 - from 208 to 29 deaths per 1,000.",
            "Vaccines, antibiotics, oral rehydration therapy, and improved nutrition transformed child survival."),
        ResearchStudy("🇮🇸", "Study 2: Iceland Leads the World",
            f"<b>Iceland</b> has the world's lowest child mortality at <b>{stats['lowest_mortality']:.1f}</b> per 1,000 in 2016.",
            "Universal healthcare, high living standards, and excellent prenatal care contribute to exceptional outcomes."),
        ResearchStudy("🌍", "Study 3: Sub-Saharan Africa's Challenge",
            "Sub-Saharan Africa has the highest regional average at <b>74 per 1,000</b> - still comparable to global rates in 1950.",
            "Infectious diseases, malnutrition, and limited healthcare access drive persistent high mortality."),
        ResearchStudy("🇰🇷", "Study 4: South Korea's Transformation",
            f"<b>South Korea</b> achieved the most dramatic improvement: <b>{stats['most_improved_pct']:.0f}%</b> reduction since 1950.",
            "From 130+ deaths per 1,000 to just 3 - demonstrating what rapid development can achieve."),
        ResearchStudy("⚠️", "Study 5: The 63x Gap",
            f"A child in <b>Somalia</b> (132.5/1,000) is <b>63x more likely</b> to die before age 5 than one in <b>Iceland</b> (2.1/1,000).",
            "Where you are born still largely determines a child's chance of survival."),
    ])

    st.markdown("### What is Child Mortality?")
    st.markdown("""
    **Child mortality rate** (under-5 mortality) measures the probability of dying between birth and age 5,
    expressed per 1,000 live births. It's a key indicator of population health and development.

    **Key causes of child death:**
    - Pneumonia and respiratory infections
    - Diarrheal diseases
    - Malaria (in endemic regions)
    - Malnutrition (underlying factor in ~45% of deaths)
    - Neonatal conditions (first 28 days)
    """)

    st.markdown("### Data Sources")
    sources = [
        "**1800-1950**: Gapminder historical estimates from mortality.org and International Historical Statistics",
        "**1950-2016**: UN Inter-agency Group for Child Mortality Estimation (UNIGME)",
        "**Methodology**: Standardized estimates combining national statistics, surveys, and modeling"
    ]
    for source in sources:
        st.markdown(f"- {source}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    with ChildMortalityDatabase() as db:
        countries_list = db.get_countries_list()

    selected_country = st.selectbox(
        "Select a country:",
        options=countries_list,
        index=countries_list.index('United States') if 'United States' in countries_list else 0
    )

    with ChildMortalityDatabase() as db:
        country_data = db.get_country_data(selected_country)
        country_trend = db.get_country_trend(selected_country)

    if len(country_data) > 0:
        latest_info = country_data[country_data['year'] == 2016]
        if len(latest_info) > 0:
            latest_info = latest_info.iloc[0]
        else:
            latest_info = country_data.iloc[-1]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("2016 Rate", f"{latest_info['mortality_rate']:.1f}/1,000")

        with col2:
            st.metric("Tier", latest_info['mortality_tier'])

        with col3:
            st.metric("Region", latest_info['region'])

        with col4:
            if pd.notna(latest_info.get('improvement_pct')):
                st.metric("1950-2016 Change", f"-{latest_info['improvement_pct']:.0f}%")
            else:
                st.metric("1950-2016 Change", "N/A")

        # Country trend
        st.subheader(f"{selected_country} Child Mortality Over Time")

        # Show full historical trend
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_trend['year'],
            y=country_trend['mortality_rate'],
            mode='lines',
            name=selected_country,
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))

        fig.update_layout(
            height=400,
            xaxis_title='Year',
            yaxis_title='Deaths per 1,000 Live Births',
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
            with ChildMortalityDatabase() as db:
                compare_data = db.compare_countries([selected_country] + compare_countries)

            # Filter to 1950+ for clearer comparison
            compare_data = compare_data[compare_data['year'] >= 1950]

            fig = px.line(
                compare_data,
                x='year',
                y='mortality_rate',
                color='country',
                markers=False,
                labels={'mortality_rate': 'Deaths per 1,000', 'year': 'Year', 'country': 'Country'}
            )

            fig.update_layout(
                height=450,
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if latest_info['mortality_rate'] < 10:
            st.success(f"**{selected_country}** has achieved very low child mortality, among the world's best outcomes.")
        elif latest_info['mortality_rate'] < 25:
            st.info(f"**{selected_country}** has low child mortality, better than the global average.")
        elif latest_info['mortality_rate'] < 50:
            st.warning(f"**{selected_country}** has moderate child mortality with room for improvement.")
        else:
            st.error(f"**{selected_country}** faces significant child mortality challenges requiring urgent attention.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Latest Data (2016)", "All Years", "Region Summary", "Year Summary", "Tier Summary"],
        horizontal=True
    )

    if data_view == "Latest Data (2016)":
        display_data = latest_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "child_mortality_2016.csv", "text/csv")

    elif data_view == "All Years":
        st.warning("Full dataset has 41,000+ rows. Showing sample years.")
        sample_years = [1800, 1850, 1900, 1950, 1980, 2000, 2016]
        display_data = full_data[full_data['year'].isin(sample_years)].copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download Full CSV", csv, "child_mortality_all.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "child_mortality_regions.csv", "text/csv")

    elif data_view == "Year Summary":
        st.dataframe(year_summary, use_container_width=True, hide_index=True)
        csv = year_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "child_mortality_years.csv", "text/csv")

    else:
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "child_mortality_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Iceland", "Japan"),
        ("South Korea", "China"),
        ("Nigeria", "India"),
    ],
    data=latest_data,
    name_column="country",
    value_column="mortality_rate",
    title="Test Your Knowledge",
    prompt="Can you guess which country has the LOWER child mortality rate?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """child_mortality ────────────┐
* country, year (PK)        │    region_summary
* mortality_rate            ├──▶ * region (PK)
* region                    │    * avg_rate
* mortality_tier            │    * avg_improvement_pct
* improvement_pct           │
* improvement_tier          │    year_summary
                            └──▶ * year (PK)
                                 * avg_rate
                                 * min_rate, max_rate"""

SAMPLE_QUERIES = """-- Countries with lowest mortality (2016)
SELECT country, region, mortality_rate, mortality_tier
FROM child_mortality
WHERE year = 2016
ORDER BY mortality_rate ASC
LIMIT 20;

-- Most improved since 1950
SELECT country, region, improvement_pct, improvement_tier
FROM child_mortality
WHERE year = 2016 AND improvement_pct IS NOT NULL
ORDER BY improvement_pct DESC;

-- Regional averages
SELECT region, avg_rate, avg_improvement_pct
FROM region_summary
ORDER BY avg_rate;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["210 countries tracked", "216 years of data (1800-2016)", "Regional analysis", "Improvement metrics"]
)

# Footer
render_data_footer(
    data_sources=["Gapminder v10 (2017)", "UNIGME", "UN World Population Prospects"],
    time_period="1800-2016",
    data_points=f"{stats['countries']} countries, 216 years",
    credits={"Data": "Gapminder Foundation", "Estimates": "UN Inter-agency Group for Child Mortality Estimation"},
    dataset_url="https://www.gapminder.org/data/documentation/gd005/"
)

# Site Footer
render_site_footer()
