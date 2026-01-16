"""
World Bank Poverty and Inequality Platform Dashboard
Global poverty and inequality data for 177 countries (1967-2021)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.poverty_inequality.database import PovertyInequalityDatabase
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
    page_title="Poverty & Inequality | Allan Ninal",
    page_icon="💰",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load poverty and inequality data from database."""
    with PovertyInequalityDatabase() as db:
        full_data = db.get_full_data()
        country_latest = db.get_country_latest()
        region_summary = db.get_region_summary()
        tier_summary = db.get_poverty_tier_summary()
        highest_poverty = db.get_highest_poverty(limit=20)
        lowest_poverty = db.get_lowest_poverty(limit=20)
        most_unequal = db.get_most_unequal(limit=20)
        most_equal = db.get_most_equal(limit=20)
        poverty_vs_inequality = db.get_poverty_vs_inequality()
        global_trend = db.get_global_trend()
        stats = db.get_stats()
    return (full_data, country_latest, region_summary, tier_summary,
            highest_poverty, lowest_poverty, most_unequal, most_equal,
            poverty_vs_inequality, global_trend, stats)


# Load data
(full_data, country_latest, region_summary, tier_summary,
 highest_poverty, lowest_poverty, most_unequal, most_equal,
 poverty_vs_inequality, global_trend, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Poverty & Inequality", icon="💰", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="World Bank Poverty and Inequality Platform",
    subtitle="Comprehensive global poverty rates and inequality measures across 177 countries spanning 54 years.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | {stats['years_covered']} | World Bank PIP"
)

# Key insight banner
render_shocking_fact(
    value=f"~2 Billion",
    description=f"people live in <b>extreme poverty</b> (below $2.15/day). <b>{stats['highest_poverty_country']}</b> has the highest rate (<b>{stats['highest_poverty_rate']}%</b>), while <b>{stats['most_unequal_country']}</b> is the most unequal (Gini: <b>{stats['highest_gini']}</b>).",
    style="danger"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['avg_extreme_poverty']}%", "Global Avg<br>Extreme Poverty", "danger"),
    HeroStat(f"{stats['avg_gini']:.2f}", "Global Avg<br>Gini Coefficient"),
    HeroStat(f"{stats['countries']}", "Countries<br>Covered", "secondary"),
    HeroStat("54", "Years of<br>Data", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Poverty Rankings", "Inequality Analysis", "Regional View",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Poverty Rankings
with tab1:
    st.subheader("Extreme Poverty by Country")

    st.markdown("""
    **Extreme poverty** is defined as living on less than **$2.15 per day** (2017 PPP).
    This is the World Bank's international poverty line.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Highest Extreme Poverty Rates")

        fig = px.bar(
            highest_poverty,
            x='extreme_poverty_rate',
            y='country',
            orientation='h',
            color='poverty_tier',
            color_discrete_map={
                'Extreme (40%+)': '#7f1d1d',
                'High (20-40%)': '#ef4444',
                'Moderate (5-20%)': '#f97316',
                'Low (1-5%)': '#3b82f6',
                'Very Low (<1%)': '#22c55e'
            },
            labels={'extreme_poverty_rate': '% Below $2.15/day', 'country': '', 'poverty_tier': 'Poverty Level'}
        )

        fig.update_layout(
            height=600,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Lowest Extreme Poverty Rates")

        # Filter to show countries with some poverty for meaningful comparison
        lowest_display = lowest_poverty[lowest_poverty['extreme_poverty_rate'] < 5].head(20)

        fig = px.bar(
            lowest_display,
            x='extreme_poverty_rate',
            y='country',
            orientation='h',
            color='poverty_tier',
            color_discrete_map={
                'Extreme (40%+)': '#7f1d1d',
                'High (20-40%)': '#ef4444',
                'Moderate (5-20%)': '#f97316',
                'Low (1-5%)': '#3b82f6',
                'Very Low (<1%)': '#22c55e'
            },
            labels={'extreme_poverty_rate': '% Below $2.15/day', 'country': '', 'poverty_tier': 'Poverty Level'}
        )

        fig.update_layout(
            height=600,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Multi-tier poverty comparison
    st.subheader("Poverty at Different Thresholds")

    st.markdown("""
    The World Bank uses multiple poverty lines:
    - **$2.15/day** - International Poverty Line (extreme poverty)
    - **$3.65/day** - Lower-middle income poverty line
    - **$6.85/day** - Upper-middle income poverty line
    """)

    # Top 15 highest poverty countries with all thresholds
    top_countries = highest_poverty['country'].head(15).tolist()
    multi_threshold = country_latest[country_latest['country'].isin(top_countries)].copy()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['country'],
        x=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['extreme_poverty_rate'],
        name='$2.15/day (Extreme)',
        orientation='h',
        marker_color='#7f1d1d'
    ))

    fig.add_trace(go.Bar(
        y=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['country'],
        x=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['lower_mid_poverty_rate'],
        name='$3.65/day (Lower-Mid)',
        orientation='h',
        marker_color='#ef4444'
    ))

    fig.add_trace(go.Bar(
        y=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['country'],
        x=multi_threshold.sort_values('extreme_poverty_rate', ascending=True)['upper_mid_poverty_rate'],
        name='$6.85/day (Upper-Mid)',
        orientation='h',
        marker_color='#f97316'
    ))

    fig.update_layout(
        title='Poverty Rates at Multiple Thresholds',
        height=550,
        barmode='group',
        xaxis_title='% of Population',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Inequality Analysis
with tab2:
    st.subheader("Income Inequality (Gini Coefficient)")

    st.markdown("""
    The **Gini coefficient** measures income inequality:
    - **0** = Perfect equality (everyone has the same income)
    - **1** = Perfect inequality (one person has all income)
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Most Unequal Countries")

        fig = px.bar(
            most_unequal,
            x='gini',
            y='country',
            orientation='h',
            color='inequality_tier',
            color_discrete_map={
                'Extreme (0.50+)': '#7f1d1d',
                'Very High (0.40-0.50)': '#ef4444',
                'High (0.35-0.40)': '#f97316',
                'Moderate (0.30-0.35)': '#3b82f6',
                'Low (<0.30)': '#22c55e'
            },
            labels={'gini': 'Gini Coefficient', 'country': '', 'inequality_tier': 'Inequality Level'}
        )

        fig.update_layout(
            height=600,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Most Equal Countries")

        fig = px.bar(
            most_equal,
            x='gini',
            y='country',
            orientation='h',
            color='inequality_tier',
            color_discrete_map={
                'Extreme (0.50+)': '#7f1d1d',
                'Very High (0.40-0.50)': '#ef4444',
                'High (0.35-0.40)': '#f97316',
                'Moderate (0.30-0.35)': '#3b82f6',
                'Low (<0.30)': '#22c55e'
            },
            labels={'gini': 'Gini Coefficient', 'country': '', 'inequality_tier': 'Inequality Level'}
        )

        fig.update_layout(
            height=600,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Poverty vs Inequality Scatter
    st.subheader("Does Poverty Correlate with Inequality?")

    fig = px.scatter(
        poverty_vs_inequality,
        x='gini',
        y='extreme_poverty_rate',
        color='region',
        size='mean',
        hover_name='country',
        labels={
            'gini': 'Gini Coefficient (Inequality)',
            'extreme_poverty_rate': 'Extreme Poverty Rate (%)',
            'region': 'Region',
            'mean': 'Mean Income'
        }
    )

    fig.update_layout(
        height=550,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Insight**: High inequality doesn't always mean high poverty. Some countries (like South Africa) are highly unequal but middle-income, while others are poor but relatively equal.")

# Tab 3: Regional View
with tab3:
    st.subheader("Poverty and Inequality by Region")

    # Regional summary bar chart
    fig = px.bar(
        region_summary.sort_values('avg_extreme_poverty', ascending=True),
        x='avg_extreme_poverty',
        y='region',
        orientation='h',
        color='avg_extreme_poverty',
        color_continuous_scale='Reds',
        labels={'avg_extreme_poverty': 'Avg Extreme Poverty (%)', 'region': ''}
    )

    fig.update_layout(
        title='Average Extreme Poverty Rate by Region',
        height=400,
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional stats table
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Regional Poverty Statistics")

        region_display = region_summary[['region', 'countries', 'avg_extreme_poverty', 'avg_lower_mid_poverty']].copy()
        region_display.columns = ['Region', 'Countries', 'Extreme Poverty (%)', 'Lower-Mid Poverty (%)']
        region_display = region_display.sort_values('Extreme Poverty (%)', ascending=False)

        st.dataframe(region_display, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("### Regional Inequality Statistics")

        inequality_display = region_summary[['region', 'countries', 'avg_gini', 'avg_mean_income']].copy()
        inequality_display.columns = ['Region', 'Countries', 'Avg Gini', 'Avg Income ($/day)']
        inequality_display = inequality_display.sort_values('Avg Gini', ascending=False)

        st.dataframe(inequality_display.round(2), use_container_width=True, hide_index=True)

    # World Map
    st.subheader("Global Map: Extreme Poverty")

    fig = px.choropleth(
        country_latest,
        locations='country',
        locationmode='country names',
        color='extreme_poverty_rate',
        color_continuous_scale='Reds',
        labels={'extreme_poverty_rate': '% Below $2.15/day'},
        hover_name='country',
        hover_data=['gini', 'mean']
    )

    fig.update_layout(
        height=500,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Global trend over time
    st.subheader("Global Poverty Trend Over Time")

    fig = px.line(
        global_trend,
        x='year',
        y='avg_extreme_poverty',
        markers=True,
        labels={'year': 'Year', 'avg_extreme_poverty': 'Avg Extreme Poverty (%)'}
    )

    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success("**Progress**: Global extreme poverty has declined significantly since 1990, though progress has slowed in recent years.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🇲🇬", "Study 1: Madagascar's Extreme Poverty",
            f"<b>Madagascar</b> has the highest extreme poverty rate at <b>{stats['highest_poverty_rate']}%</b> - nearly 4 in 5 people live below $2.15/day.",
            "Political instability, weak infrastructure, and climate vulnerability have trapped millions in poverty."),
        ResearchStudy("🇿🇦", "Study 2: South Africa's Inequality Crisis",
            f"<b>South Africa</b> has the world's highest Gini coefficient (<b>{stats['highest_gini']}</b>) - a legacy of apartheid.",
            "Despite being a middle-income country, wealth is extremely concentrated among a small elite."),
        ResearchStudy("🇸🇰", "Study 3: Slovakia's Equality Model",
            f"<b>Slovakia</b> has the lowest inequality (Gini: <b>{stats['lowest_gini']}</b>) among countries measured.",
            "Post-communist European countries often have low inequality due to historical redistribution policies."),
        ResearchStudy("🌍", "Study 4: Sub-Saharan Africa Bears the Burden",
            "Sub-Saharan Africa has the highest regional poverty rate - over <b>40%</b> live in extreme poverty.",
            "Despite rapid economic growth in some countries, population growth has outpaced poverty reduction."),
        ResearchStudy("📉", "Study 5: Poverty Has Declined, But Not Enough",
            "Global extreme poverty fell from <b>36%</b> (1990) to under <b>10%</b> (2019) - a historic achievement.",
            "COVID-19 reversed years of progress, pushing an estimated 100 million back into extreme poverty."),
    ])

    st.markdown("### Understanding Poverty Measures")
    st.markdown("""
    **Poverty Lines:**
    - **$2.15/day** (2017 PPP): International extreme poverty line
    - **$3.65/day**: Lower-middle income poverty line
    - **$6.85/day**: Upper-middle income poverty line

    **Key Metrics:**
    - **Headcount Ratio**: % of population below the poverty line
    - **Poverty Gap Index**: Measures depth of poverty (how far below the line)
    - **Gini Coefficient**: Inequality measure (0 = perfect equality, 1 = perfect inequality)

    **Data Quality:**
    - Based on household surveys
    - Uses Purchasing Power Parity (PPP) to compare across countries
    - Some countries have limited data coverage
    """)

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    with PovertyInequalityDatabase() as db:
        countries_list = db.get_countries_list()

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_country = st.selectbox(
            "Select a country:",
            options=countries_list,
            index=countries_list.index('India') if 'India' in countries_list else 0
        )

    with col2:
        # Get region for selected country
        country_info = country_latest[country_latest['country'] == selected_country]
        if len(country_info) > 0:
            st.metric("Region", country_info.iloc[0]['region'])

    with PovertyInequalityDatabase() as db:
        country_data = db.get_country_data(selected_country)
        country_trend = db.get_country_trend(selected_country)

    if len(country_data) > 0:
        latest_info = country_data.iloc[-1]  # Most recent year

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Extreme Poverty",
                      f"{latest_info['extreme_poverty_rate']:.1f}%" if pd.notna(latest_info['extreme_poverty_rate']) else "N/A")

        with col2:
            st.metric("Gini Coefficient",
                      f"{latest_info['gini']:.3f}" if pd.notna(latest_info['gini']) else "N/A")

        with col3:
            st.metric("Mean Income",
                      f"${latest_info['mean']:.1f}/day" if pd.notna(latest_info['mean']) else "N/A")

        with col4:
            st.metric("Data Year", int(latest_info['year']))

        # Country trend
        if len(country_trend) > 1:
            st.subheader(f"{selected_country} Poverty Trend Over Time")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=country_trend['year'],
                y=country_trend['extreme_poverty_rate'],
                mode='lines+markers',
                name='Extreme ($2.15/day)',
                line=dict(color='#7f1d1d', width=2),
                marker=dict(size=8)
            ))

            if 'lower_mid_poverty_rate' in country_trend.columns:
                fig.add_trace(go.Scatter(
                    x=country_trend['year'],
                    y=country_trend['lower_mid_poverty_rate'],
                    mode='lines+markers',
                    name='Lower-Mid ($3.65/day)',
                    line=dict(color='#ef4444', width=2),
                    marker=dict(size=8)
                ))

            fig.update_layout(
                height=400,
                yaxis_title='% of Population',
                xaxis_title='Year',
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

            # Gini trend
            st.subheader(f"{selected_country} Inequality Trend")

            fig = px.line(
                country_trend,
                x='year',
                y='gini',
                markers=True,
                labels={'year': 'Year', 'gini': 'Gini Coefficient'}
            )

            fig.add_hline(y=stats['avg_gini'], line_dash="dash", line_color="#94a3b8",
                          annotation_text="Global Avg", annotation_position="right")

            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Compare with region
        st.subheader(f"Compare with Region")

        country_region = latest_info['region']
        with PovertyInequalityDatabase() as db:
            region_countries = db.get_by_region(country_region)

        if len(region_countries) > 1:
            # Only include countries that have both metrics
            region_with_both = region_countries[
                (region_countries['extreme_poverty_rate'].notna()) &
                (region_countries['gini'].notna())
            ].head(15)

            if len(region_with_both) > 0:
                fig = px.scatter(
                    region_with_both,
                    x='gini',
                    y='extreme_poverty_rate',
                    text='country',
                    color='poverty_tier',
                    color_discrete_map={
                        'Extreme (40%+)': '#7f1d1d',
                        'High (20-40%)': '#ef4444',
                        'Moderate (5-20%)': '#f97316',
                        'Low (1-5%)': '#3b82f6',
                        'Very Low (<1%)': '#22c55e'
                    },
                    labels={
                        'gini': 'Gini Coefficient',
                        'extreme_poverty_rate': 'Extreme Poverty (%)',
                        'poverty_tier': 'Poverty Level'
                    }
                )

                fig.update_traces(textposition='top center')

                fig.update_layout(
                    title=f'{country_region} Countries: Poverty vs Inequality',
                    height=450,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )

                st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if pd.notna(latest_info['extreme_poverty_rate']):
            if latest_info['extreme_poverty_rate'] < 1:
                st.success(f"**{selected_country}** has virtually eliminated extreme poverty (<1%).")
            elif latest_info['extreme_poverty_rate'] < 5:
                st.info(f"**{selected_country}** has low extreme poverty - most have escaped the $2.15/day threshold.")
            elif latest_info['extreme_poverty_rate'] < 20:
                st.warning(f"**{selected_country}** has moderate poverty - significant progress still needed.")
            else:
                st.error(f"**{selected_country}** has high poverty - major challenges remain for development.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Country Latest", "Regional Summary", "Poverty Tier Summary", "Full Time Series"],
        horizontal=True
    )

    if data_view == "Country Latest":
        display_cols = ['country', 'year', 'region', 'extreme_poverty_rate',
                        'lower_mid_poverty_rate', 'gini', 'mean', 'poverty_tier']
        display_data = country_latest[display_cols].copy()
        display_data.columns = ['Country', 'Year', 'Region', 'Extreme Poverty (%)',
                                'Lower-Mid Poverty (%)', 'Gini', 'Mean Income', 'Poverty Tier']
        st.dataframe(display_data.round(2), use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "pip_country_latest.csv", "text/csv")

    elif data_view == "Regional Summary":
        st.dataframe(region_summary.round(2), use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "pip_region_summary.csv", "text/csv")

    elif data_view == "Poverty Tier Summary":
        st.dataframe(tier_summary.round(2), use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "pip_tier_summary.csv", "text/csv")

    else:
        # Full time series - show sample
        st.warning("Full dataset has 4,877 rows. Showing first 500 rows.")
        display_cols = ['country', 'year', 'region', 'extreme_poverty_rate', 'gini', 'mean']
        display_data = full_data[display_cols].head(500)
        st.dataframe(display_data.round(3), use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download Full CSV", csv, "pip_full_data.csv", "text/csv")

st.markdown("---")

# Quiz Section
quiz_data = country_latest[country_latest['extreme_poverty_rate'].notna()].copy()
render_quiz_section(
    questions=[
        ("India", "China"),
        ("Nigeria", "Indonesia"),
        ("Brazil", "South Africa"),
    ],
    data=quiz_data,
    name_column="country",
    value_column="extreme_poverty_rate",
    title="Test Your Knowledge",
    prompt="Can you guess which country has a HIGHER extreme poverty rate?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """poverty_inequality ─────────┐
* country, year (PK)        │    country_latest
* extreme_poverty_rate      ├──▶ * country (PK)
* lower_mid_poverty_rate    │    * extreme_poverty_rate
* gini, mean, median        │    * gini, poverty_tier
* poverty_tier              │
* inequality_tier           │    region_summary
                            └──▶ * region (PK)
                                 * avg_extreme_poverty"""

SAMPLE_QUERIES = """-- Highest poverty countries
SELECT country, extreme_poverty_rate, gini
FROM country_latest
ORDER BY extreme_poverty_rate DESC
LIMIT 10;

-- Regional comparison
SELECT region, AVG(extreme_poverty_rate) as avg_poverty
FROM country_latest
GROUP BY region
ORDER BY avg_poverty DESC;

-- Country trend
SELECT year, extreme_poverty_rate, gini
FROM poverty_inequality
WHERE country = 'India'
ORDER BY year;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["177 countries", "54 years of data", "Multiple poverty thresholds", "Gini inequality measures"]
)

# Footer
render_data_footer(
    data_sources=["World Bank Poverty and Inequality Platform (PIP)", "Household survey data"],
    time_period="1967-2021",
    data_points=f"{stats['countries']} countries, 4,877 observations",
    credits={"Data": "World Bank", "Methodology": "PPP-adjusted 2017 international dollars"},
    dataset_url="https://pip.worldbank.org/"
)

# Site Footer
render_site_footer()
