"""
Suicide Rates by Sex and Age Dashboard
Analyzing global suicide mortality patterns across 198 countries (IHME, 2019)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.suicide_rates.database import SuicideRatesDatabase
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
    page_title="Suicide Rates by Sex and Age | Allan Ninal",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load suicide rates data from database."""
    with SuicideRatesDatabase() as db:
        full_data = db.get_full_data()
        latest_data = db.get_latest_data()
        region_summary = db.get_region_summary()
        age_summary = db.get_age_summary()
        tier_summary = db.get_tier_summary()
        top_male = db.get_highest_male_rates(20)
        top_female = db.get_highest_female_rates(20)
        top_ratio = db.get_highest_gender_ratio(20)
        lowest_ratio = db.get_lowest_gender_ratio(20)
        global_trend = db.get_global_trend()
        stats = db.get_stats()
    return (full_data, latest_data, region_summary, age_summary, tier_summary,
            top_male, top_female, top_ratio, lowest_ratio, global_trend, stats)


# Load data
(full_data, latest_data, region_summary, age_summary, tier_summary,
 top_male, top_female, top_ratio, lowest_ratio, global_trend, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Suicide Rates", icon="📊", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Suicide Rates by Sex and Age",
    subtitle="Exploring global patterns in suicide mortality across 198 countries, revealing stark gender disparities and age-related vulnerabilities.",
    data_badge=f"🌍 Data: {stats['countries']} Countries • 1990-2017 | IHME Global Burden of Disease"
)

# Key insight banner
render_shocking_fact(
    value=f"{stats['avg_gender_ratio']:.1f}x Higher for Men",
    description=f"Globally, men die by suicide at <b>{stats['avg_gender_ratio']:.1f} times</b> the rate of women. <b>{stats['highest_rate_country']}</b> has the highest male rate at <b>{stats['highest_rate']:.1f}/100k</b>, while <b>{stats['highest_ratio_country']}</b> shows the largest gender gap at <b>{stats['highest_ratio']:.1f}x</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['avg_male_rate']:.1f}", "Avg Male Rate<br>(per 100k)"),
    HeroStat(f"{stats['avg_female_rate']:.1f}", "Avg Female Rate<br>(per 100k)", "success"),
    HeroStat(f"{stats['highest_ratio']:.1f}x", f"Highest Gender Gap<br>({stats['highest_ratio_country']})", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Male Rates", "Female Rates", "Gender Gap",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Male Rates
with tab1:
    st.subheader("Countries with Highest Male Suicide Rates")

    fig = px.bar(
        top_male,
        x='male_rate',
        y='entity',
        orientation='h',
        color='male_rate',
        color_continuous_scale='Reds',
        labels={'male_rate': 'Deaths per 100,000 males', 'entity': ''}
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
    st.subheader("Male Suicide Rates by Region")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.bar(
            region_summary.sort_values('avg_male_rate', ascending=True),
            x='avg_male_rate',
            y='region',
            orientation='h',
            color='avg_male_rate',
            color_continuous_scale='Reds',
            labels={'avg_male_rate': 'Avg per 100k', 'region': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Global trend
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=global_trend['year'],
            y=global_trend['avg_male_rate'],
            name='Male Rate',
            line=dict(color='#ef4444', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=global_trend['year'],
            y=global_trend['avg_female_rate'],
            name='Female Rate',
            line=dict(color='#3b82f6', width=3)
        ))

        fig.update_layout(
            title='Global Average Rates Over Time',
            height=400,
            xaxis_title='Year',
            yaxis_title='Deaths per 100,000',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # World map
    st.subheader("Global Male Suicide Rate Map")

    fig = px.choropleth(
        latest_data,
        locations='entity',
        locationmode='country names',
        color='male_rate',
        color_continuous_scale='Reds',
        labels={'male_rate': 'per 100k'},
        title='Male Suicide Rate by Country (per 100,000)'
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

    # Rate tiers
    st.subheader("Countries by Risk Tier (Male Rates)")

    col1, col2 = st.columns([1, 1])

    with col1:
        tier_data = tier_summary[tier_summary['countries'] > 0]
        fig = px.pie(
            tier_data,
            values='countries',
            names='rate_tier',
            color='rate_tier',
            color_discrete_map={
                'Very High (20+)': '#7f1d1d',
                'High (15-20)': '#dc2626',
                'Moderate (10-15)': '#f97316',
                'Low (5-10)': '#fbbf24',
                'Very Low (<5)': '#a3e635'
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
        tier_display.columns = ['Tier', 'Countries', 'Avg Rate', 'Min Rate', 'Max Rate', 'Avg M:F Ratio']

        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Risk Tiers (per 100,000 males):**
        - **Very High**: 20+ deaths
        - **High**: 15-20 deaths
        - **Moderate**: 10-15 deaths
        - **Low**: 5-10 deaths
        - **Very Low**: <5 deaths
        """)

# Tab 2: Female Rates
with tab2:
    st.subheader("Countries with Highest Female Suicide Rates")

    fig = px.bar(
        top_female,
        x='female_rate',
        y='entity',
        orientation='h',
        color='female_rate',
        color_continuous_scale='Blues',
        labels={'female_rate': 'Deaths per 100,000 females', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional comparison
    st.subheader("Female Suicide Rates by Region")

    fig = px.bar(
        region_summary.sort_values('avg_female_rate', ascending=True),
        x='avg_female_rate',
        y='region',
        orientation='h',
        color='avg_female_rate',
        color_continuous_scale='Blues',
        labels={'avg_female_rate': 'Avg per 100k', 'region': ''}
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # World map - female
    st.subheader("Global Female Suicide Rate Map")

    fig = px.choropleth(
        latest_data,
        locations='entity',
        locationmode='country names',
        color='female_rate',
        color_continuous_scale='Blues',
        labels={'female_rate': 'per 100k'},
        title='Female Suicide Rate by Country (per 100,000)'
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

    # Male vs Female comparison
    st.subheader("Male vs Female Rates by Region")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=region_summary['region'],
        x=region_summary['avg_male_rate'],
        name='Male',
        orientation='h',
        marker_color='#ef4444'
    ))

    fig.add_trace(go.Bar(
        y=region_summary['region'],
        x=region_summary['avg_female_rate'],
        name='Female',
        orientation='h',
        marker_color='#3b82f6'
    ))

    fig.update_layout(
        height=400,
        barmode='group',
        xaxis_title='Deaths per 100,000',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Gender Gap
with tab3:
    st.subheader("Countries with Largest Male:Female Suicide Ratio")

    st.markdown("The gender gap in suicide is one of the most consistent patterns globally - men die by suicide at much higher rates than women.")

    fig = px.bar(
        top_ratio,
        x='gender_ratio',
        y='entity',
        orientation='h',
        color='gender_ratio',
        color_continuous_scale='Purples',
        labels={'gender_ratio': 'Male:Female Ratio', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Lowest ratios
    st.subheader("Countries with Smallest Gender Gap")

    fig = px.bar(
        lowest_ratio.head(15),
        x='gender_ratio',
        y='entity',
        orientation='h',
        color='gender_ratio',
        color_continuous_scale='Greens',
        labels={'gender_ratio': 'Male:Female Ratio', 'entity': ''}
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        yaxis={'categoryorder': 'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # World map - gender ratio
    st.subheader("Gender Gap in Suicide Globally")

    fig = px.choropleth(
        latest_data[latest_data['gender_ratio'].notna()],
        locations='entity',
        locationmode='country names',
        color='gender_ratio',
        color_continuous_scale='Purples',
        labels={'gender_ratio': 'M:F Ratio'},
        title='Male:Female Suicide Ratio by Country'
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

    # Age-based analysis
    st.subheader("Gender Gap by Age Group")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=age_summary['age_group'],
        y=age_summary['male_rate'],
        name='Male',
        marker_color='#ef4444'
    ))

    fig.add_trace(go.Bar(
        x=age_summary['age_group'],
        y=age_summary['female_rate'],
        name='Female',
        marker_color='#3b82f6'
    ))

    fig.update_layout(
        title='Suicide Rates by Age Group and Sex (Global Average)',
        height=400,
        barmode='group',
        xaxis_title='Age Group',
        yaxis_title='Deaths per 100,000',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Age group table
    col1, col2 = st.columns([2, 1])

    with col1:
        age_display = age_summary.copy()
        age_display['gender_ratio'] = age_display['gender_ratio'].round(2)
        age_display.columns = ['Age Group', 'Male Rate', 'Female Rate', 'Both Sexes', 'M:F Ratio']

        st.dataframe(age_display, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("""
        **Key Pattern:**

        The gender gap widens dramatically with age:
        - Youth (15-19): ~2-3x
        - Middle age: ~3-4x
        - Elderly (70+): ~4-5x

        Older men are particularly vulnerable.
        """)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🚹", "Study 1: The Male Paradox",
            "Men die by suicide at <b>3-4x the rate</b> of women globally, yet women have higher rates of <b>suicidal ideation and attempts</b>.",
            "Men tend to use more lethal methods and are less likely to seek help, contributing to higher completion rates."),
        ResearchStudy("🌍", "Study 2: Geographic Extremes",
            "<b>Greenland</b> has the highest male suicide rate at <b>75/100k</b>, while many Middle Eastern countries report rates below <b>5/100k</b>.",
            "Cultural, religious, and reporting factors contribute to extreme variations across countries."),
        ResearchStudy("👴", "Study 3: Age Vulnerability",
            "Suicide rates increase with age, with <b>70+ year-olds</b> showing the highest rates - particularly among men.",
            "Social isolation, chronic illness, and loss of independence are key risk factors in elderly populations."),
        ResearchStudy("📉", "Study 4: Global Decline",
            "Global suicide rates have <b>declined by ~30%</b> since 1990, though progress is uneven across regions.",
            "Improved mental health services, reduced access to means, and crisis interventions have contributed to this decline."),
        ResearchStudy("🇬🇭", "Study 5: The Ghana Anomaly",
            "<b>Ghana</b> shows a remarkable <b>10.5x</b> male:female ratio - the highest globally.",
            "Cultural factors around masculinity, economic pressures, and underreporting of female suicide may contribute."),
    ])

    st.markdown("### Risk Factors")
    risk_factors = [
        "Mental health disorders (depression, substance abuse)",
        "Previous suicide attempts",
        "Access to lethal means",
        "Social isolation and relationship problems",
        "Economic hardship and unemployment",
        "Chronic pain and terminal illness"
    ]
    for factor in risk_factors:
        st.markdown(f"- {factor}")

    st.markdown("### Protective Factors")
    protective = [
        "Strong social connections and support networks",
        "Access to mental health care",
        "Restricted access to lethal means",
        "Cultural and religious beliefs",
        "Problem-solving and coping skills"
    ]
    for factor in protective:
        st.markdown(f"- {factor}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(latest_data['entity'].unique()),
        index=sorted(latest_data['entity'].unique()).index('United States') if 'United States' in latest_data['entity'].unique() else 0
    )

    with SuicideRatesDatabase() as db:
        country_data = db.get_country_data(selected_country)
        age_profile = db.get_age_profile_by_country(selected_country)

    if len(country_data) > 0:
        latest = country_data[country_data['year'] == country_data['year'].max()].iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Male Rate", f"{latest['male_rate']:.1f}/100k")

        with col2:
            st.metric("Female Rate", f"{latest['female_rate']:.1f}/100k")

        with col3:
            st.metric("Gender Ratio", f"{latest['gender_ratio']:.1f}x")

        with col4:
            st.metric("Latest Year", int(latest['year']))

        # Trend over time
        st.subheader(f"Suicide Rate Trend in {selected_country}")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data['male_rate'],
            name='Male',
            line=dict(color='#ef4444', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data['female_rate'],
            name='Female',
            line=dict(color='#3b82f6', width=3)
        ))

        fig.update_layout(
            height=400,
            xaxis_title='Year',
            yaxis_title='Deaths per 100,000',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Age profile
        if len(age_profile) > 0:
            st.subheader(f"Age Profile for {selected_country}")

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=age_profile['age_group'],
                y=age_profile['male_rate'],
                name='Male',
                marker_color='#ef4444'
            ))

            fig.add_trace(go.Bar(
                x=age_profile['age_group'],
                y=age_profile['female_rate'],
                name='Female',
                marker_color='#3b82f6'
            ))

            fig.update_layout(
                height=400,
                barmode='group',
                xaxis_title='Age Group',
                yaxis_title='Deaths per 100,000',
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Regional comparison
        st.subheader(f"How {selected_country} Compares in {latest['region']}")

        with SuicideRatesDatabase() as db:
            region_countries = db.get_by_region(latest['region'])

        colors = ['#3b82f6' if c != selected_country else '#ef4444' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='male_rate',
            y='entity',
            orientation='h',
            labels={'male_rate': 'Male Rate (per 100k)', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            title=f"Male Suicide Rates in {latest['region']}",
            height=max(400, len(region_countries) * 20),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if latest['male_rate'] >= 20:
            st.error(f"**{selected_country}** has a very high male suicide rate - among the highest globally.")
        elif latest['male_rate'] >= 15:
            st.warning(f"**{selected_country}** has a high male suicide rate compared to the global average.")
        elif latest['male_rate'] >= 10:
            st.info(f"**{selected_country}** has a moderate male suicide rate.")
        else:
            st.success(f"**{selected_country}** has a relatively low male suicide rate.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Latest Data", "Full Time Series", "Region Summary", "Age Group Summary", "Rate Tiers"],
        horizontal=True
    )

    if data_view == "Latest Data":
        st.dataframe(latest_data, use_container_width=True, hide_index=True)
        csv = latest_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "suicide_rates_latest.csv", "text/csv")

    elif data_view == "Full Time Series":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "suicide_rates_full.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "suicide_rates_regions.csv", "text/csv")

    elif data_view == "Age Group Summary":
        st.dataframe(age_summary, use_container_width=True, hide_index=True)
        csv = age_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "suicide_rates_age.csv", "text/csv")

    else:
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "suicide_rates_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Greenland", "Russia"),
        ("United States", "Japan"),
        ("South Korea", "India"),
    ],
    data=latest_data,
    name_column="entity",
    value_column="male_rate",
    title="Test Your Knowledge",
    prompt="Can you guess which country has the HIGHER male suicide rate?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """suicide_rates ────────┐
* entity (PK)         │    region_summary
* year                ├──▶ * region (PK)
* male_rate           │    * avg_male_rate
* female_rate         │    * avg_female_rate
* gender_ratio        │
* rate_tier           │    age_summary
* male_15_19...       └──▶ * age_group (PK)
* female_15_19...          * male_rate
                           * female_rate"""

SAMPLE_QUERIES = """-- Highest male suicide rates
SELECT entity, region, male_rate, gender_ratio
FROM suicide_rates
WHERE year = (SELECT MAX(year) FROM suicide_rates)
ORDER BY male_rate DESC
LIMIT 10;

-- Gender ratio by region
SELECT region, avg_male_rate, avg_female_rate, avg_gender_ratio
FROM region_summary
ORDER BY avg_gender_ratio DESC;

-- Country trend
SELECT year, male_rate, female_rate
FROM suicide_rates
WHERE entity = 'United States'
ORDER BY year;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["28 years of data (1990-2017)", "198 countries", "9 age groups", "Gender-disaggregated rates"]
)

# Footer
render_data_footer(
    data_sources=["IHME Global Burden of Disease Study 2019", "Our World in Data"],
    time_period="1990-2017",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "IHME", "Compilation": "Our World in Data"},
    dataset_url="https://ourworldindata.org/suicide"
)

# Crisis resources
st.markdown("---")
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 1.5rem; border-radius: 12px; text-align: center;">
    <h4 style="color: white; margin: 0 0 0.5rem 0;">If you or someone you know needs help</h4>
    <p style="color: rgba(255,255,255,0.9); margin: 0;">
        <b>International Association for Suicide Prevention:</b>
        <a href="https://www.iasp.info/resources/Crisis_Centres/" target="_blank" style="color: #fbbf24;">Find a Crisis Center</a>
        <br>
        <b>US National Suicide Prevention Lifeline:</b> 988 (call or text)
    </p>
</div>
""", unsafe_allow_html=True)

# Site Footer
render_site_footer()
