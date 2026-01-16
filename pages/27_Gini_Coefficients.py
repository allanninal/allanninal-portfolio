"""
Gini Coefficients Dashboard
Income inequality across OECD countries (OECD 2016)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.gini_coefficients.database import GiniCoefficientsDatabase
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
    page_title="Gini Coefficients | Allan Ninal",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load Gini coefficients data from database."""
    with GiniCoefficientsDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        tier_summary = db.get_tier_summary()
        most_equal = db.get_most_equal(limit=18)
        most_unequal = db.get_most_unequal(limit=18)
        best_redistribution = db.get_best_redistribution(limit=18)
        redistribution_comparison = db.get_redistribution_comparison()
        stats = db.get_stats()
    return (full_data, country_summary, tier_summary, most_equal, most_unequal,
            best_redistribution, redistribution_comparison, stats)


# Load data
(full_data, country_summary, tier_summary, most_equal, most_unequal,
 best_redistribution, redistribution_comparison, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Gini Coefficients", icon="📊", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Gini Coefficients: Income Inequality",
    subtitle="How wealth is distributed across OECD countries - and how much taxes and transfers reduce inequality.",
    data_badge=f"🌍 Data: {stats['countries']} OECD Countries | {stats['years_covered']} | OECD Income Distribution Database"
)

# Key insight banner
render_shocking_fact(
    value=f"0.221 Gap",
    description=f"<b>{stats['most_equal_country']}</b> is the most equal country (Gini: <b>{stats['most_equal_gini']:.3f}</b>), while <b>{stats['most_unequal_country']}</b> is the most unequal (<b>{stats['most_unequal_gini']:.3f}</b>). On average, taxes and transfers reduce inequality by <b>{stats['avg_reduction_pct']:.0f}%</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['most_equal_gini']:.3f}", f"{stats['most_equal_country']}<br>Most Equal", "success"),
    HeroStat(f"{stats['avg_gini_post']:.3f}", "OECD Average<br>Post-Tax Gini"),
    HeroStat(f"{stats['avg_reduction_pct']:.0f}%", "Avg Inequality<br>Reduction", "secondary"),
    HeroStat(f"{stats['countries']}", "OECD<br>Countries", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Inequality Rankings", "Redistribution Effect", "Trends Over Time",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Inequality Rankings
with tab1:
    st.subheader("Income Inequality Rankings (Post-Tax & Transfers)")

    st.markdown("""
    The **Gini coefficient** measures income inequality from 0 (perfect equality) to 1 (perfect inequality).
    Lower values mean more equal income distribution.
    """)

    # Full ranking
    fig = px.bar(
        country_summary.sort_values('gini_post_tax'),
        x='gini_post_tax',
        y='country',
        orientation='h',
        color='inequality_tier',
        color_discrete_map={
            'Very Low': '#22c55e',
            'Low': '#3b82f6',
            'Moderate': '#f97316',
            'High': '#ef4444',
            'Very High': '#7f1d1d'
        },
        labels={'gini_post_tax': 'Gini Coefficient (Post-Tax)', 'country': '', 'inequality_tier': 'Inequality Level'}
    )

    fig.update_layout(
        height=900,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tier breakdown
    st.subheader("Countries by Inequality Level")

    tier_colors = {
        'Very Low': '#22c55e',
        'Low': '#3b82f6',
        'Moderate': '#f97316',
        'High': '#ef4444',
        'Very High': '#7f1d1d'
    }

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            tier_summary,
            values='countries',
            names='inequality_tier',
            color='inequality_tier',
            color_discrete_map=tier_colors
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Inequality Tiers")
        st.markdown("""
        - **Very Low** (< 0.25): Highly equal societies
        - **Low** (0.25 - 0.30): Below-average inequality
        - **Moderate** (0.30 - 0.35): Average OECD inequality
        - **High** (0.35 - 0.40): Above-average inequality
        - **Very High** (> 0.40): Significant inequality
        """)

        st.markdown("### Quick Facts")
        st.markdown(f"""
        - Most equal: **{stats['most_equal_country']}** ({stats['most_equal_gini']:.3f})
        - Most unequal: **{stats['most_unequal_country']}** ({stats['most_unequal_gini']:.3f})
        - OECD average: **{stats['avg_gini_post']:.3f}**
        """)

# Tab 2: Redistribution Effect
with tab2:
    st.subheader("How Taxes and Transfers Reduce Inequality")

    st.markdown("""
    The **pre-tax** Gini measures market income inequality (wages, capital income).
    The **post-tax** Gini measures inequality after taxes and government transfers (welfare, pensions).
    The difference shows the **redistribution effect**.
    """)

    # Pre vs Post comparison
    fig = go.Figure()

    sorted_data = redistribution_comparison.sort_values('reduction_pct', ascending=True)

    fig.add_trace(go.Bar(
        y=sorted_data['country'],
        x=sorted_data['gini_pre_tax'],
        name='Pre-Tax (Market Income)',
        orientation='h',
        marker_color='#ef4444'
    ))

    fig.add_trace(go.Bar(
        y=sorted_data['country'],
        x=sorted_data['gini_post_tax'],
        name='Post-Tax (After Redistribution)',
        orientation='h',
        marker_color='#22c55e'
    ))

    fig.update_layout(
        title='Pre-Tax vs Post-Tax Gini Coefficients',
        height=900,
        barmode='overlay',
        xaxis_title='Gini Coefficient',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Reduction percentage ranking
    st.subheader("Redistribution Effectiveness (% Reduction)")

    fig = px.bar(
        best_redistribution,
        x='reduction_pct',
        y='country',
        orientation='h',
        color='redistribution_tier',
        color_discrete_map={
            'Very Strong': '#22c55e',
            'Strong': '#3b82f6',
            'Moderate': '#f97316',
            'Weak': '#ef4444',
            'Very Weak': '#7f1d1d'
        },
        labels={'reduction_pct': '% Reduction', 'country': '', 'redistribution_tier': 'Redistribution Level'}
    )

    fig.update_layout(
        height=550,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**{stats['best_redistribution_country']}** has the strongest redistribution, reducing inequality by **{stats['best_redistribution_pct']:.1f}%** through taxes and transfers.")

    # Scatter: Pre-tax inequality vs reduction
    st.subheader("Does More Inequality Lead to More Redistribution?")

    fig = px.scatter(
        redistribution_comparison,
        x='gini_pre_tax',
        y='reduction_pct',
        color='redistribution_tier',
        size='gini_reduction',
        hover_name='country',
        color_discrete_map={
            'Very Strong': '#22c55e',
            'Strong': '#3b82f6',
            'Moderate': '#f97316',
            'Weak': '#ef4444',
            'Very Weak': '#7f1d1d'
        },
        labels={
            'gini_pre_tax': 'Pre-Tax Gini (Market Inequality)',
            'reduction_pct': 'Redistribution (%)',
            'redistribution_tier': 'Redistribution Level'
        }
    )

    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("**Observation**: Countries with similar pre-tax inequality (like Chile and South Korea) can have vastly different post-tax inequality based on their redistribution policies.")

# Tab 3: Trends Over Time
with tab3:
    st.subheader("Income Inequality Trends")

    # Country selector for trends
    selected_countries = st.multiselect(
        "Select countries to compare:",
        options=country_summary['country'].tolist(),
        default=['United States', 'Germany', 'Sweden', 'Chile', 'Japan'][:5]
    )

    if selected_countries:
        with GiniCoefficientsDatabase() as db:
            trend_data = db.compare_countries(selected_countries)

        # Post-tax trends
        st.markdown("### Post-Tax Gini Over Time")

        fig = px.line(
            trend_data,
            x='year',
            y='gini_post_tax',
            color='country',
            markers=True,
            labels={'gini_post_tax': 'Gini Coefficient', 'year': 'Year', 'country': 'Country'}
        )

        fig.update_layout(
            height=450,
            yaxis_range=[0.2, 0.5],
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Pre-tax trends
        st.markdown("### Pre-Tax Gini Over Time")

        fig = px.line(
            trend_data,
            x='year',
            y='gini_pre_tax',
            color='country',
            markers=True,
            labels={'gini_pre_tax': 'Gini Coefficient', 'year': 'Year', 'country': 'Country'}
        )

        fig.update_layout(
            height=450,
            yaxis_range=[0.35, 0.55],
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Please select at least one country to view trends.")

    st.info("**Note**: Data availability varies by country. Most countries have data from 2004-2013, but some extend back to 1987.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🇮🇸", "Study 1: Iceland Most Equal",
            f"<b>Iceland</b> has the lowest post-tax Gini coefficient (<b>{stats['most_equal_gini']:.3f}</b>) among OECD countries.",
            "Nordic countries consistently rank among the most equal due to progressive taxation and generous welfare states."),
        ResearchStudy("🇨🇱", "Study 2: Chile Most Unequal",
            f"<b>Chile</b> has the highest Gini (<b>{stats['most_unequal_gini']:.3f}</b>) - nearly double Iceland's inequality level.",
            "Despite economic growth, Latin American countries often have persistent inequality due to historical factors."),
        ResearchStudy("🇫🇮", "Study 3: Finland's Redistribution Champion",
            f"<b>Finland</b> reduces inequality by <b>{stats['best_redistribution_pct']:.1f}%</b> through taxes and transfers - the most in the OECD.",
            "Strong welfare systems with progressive taxation can halve market inequality."),
        ResearchStudy("🇺🇸", "Study 4: US High Inequality, Weak Redistribution",
            "The <b>United States</b> has both high market inequality AND below-average redistribution.",
            "The US post-tax Gini (0.396) is among the highest in OECD, reflecting limited social transfers."),
        ResearchStudy("📊", "Study 5: Redistribution Cuts Inequality by a Third",
            f"On average, OECD countries reduce inequality by <b>{stats['avg_reduction_pct']:.0f}%</b> through fiscal policy.",
            "Pre-tax Gini averages 0.476, but post-tax averages 0.318 - showing the power of redistribution."),
    ])

    st.markdown("### What is the Gini Coefficient?")
    st.markdown("""
    The **Gini coefficient** is the most commonly used measure of income inequality:
    - **0** = Perfect equality (everyone has the same income)
    - **1** = Perfect inequality (one person has all income)
    - **0.25-0.35** = Typical for developed countries
    - **0.40+** = High inequality

    **Two measures:**
    - **Pre-tax**: Market income (wages, capital gains) before government intervention
    - **Post-tax**: Disposable income after taxes and transfers (welfare, pensions, benefits)
    """)

    st.markdown("### OECD Methodology")
    st.markdown("""
    This data uses the OECD's 2012 methodology which includes:
    - More detailed breakdown of household transfers
    - Value of goods produced for own consumption
    - Revised household income definitions
    """)

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    with GiniCoefficientsDatabase() as db:
        countries_list = db.get_countries_list()

    selected_country = st.selectbox(
        "Select a country:",
        options=countries_list,
        index=countries_list.index('United States') if 'United States' in countries_list else 0
    )

    with GiniCoefficientsDatabase() as db:
        country_data = db.get_country_data(selected_country)
        country_trend = db.get_country_trend(selected_country)

    if len(country_data) > 0:
        latest_info = country_data.iloc[-1]  # Most recent year

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Post-Tax Gini", f"{latest_info['gini_post_tax']:.3f}")

        with col2:
            st.metric("Pre-Tax Gini", f"{latest_info['gini_pre_tax']:.3f}")

        with col3:
            st.metric("Redistribution", f"-{latest_info['reduction_pct']:.1f}%")

        with col4:
            st.metric("Data Year", int(latest_info['year']))

        # Country trend
        st.subheader(f"{selected_country} Gini Trend Over Time")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_trend['year'],
            y=country_trend['gini_pre_tax'],
            mode='lines+markers',
            name='Pre-Tax',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=8)
        ))

        fig.add_trace(go.Scatter(
            x=country_trend['year'],
            y=country_trend['gini_post_tax'],
            mode='lines+markers',
            name='Post-Tax',
            line=dict(color='#22c55e', width=2),
            marker=dict(size=8)
        ))

        # Add OECD average lines
        fig.add_hline(y=stats['avg_gini_pre'], line_dash="dash", line_color="#ef4444",
                      annotation_text="OECD Avg Pre-Tax", annotation_position="right")
        fig.add_hline(y=stats['avg_gini_post'], line_dash="dash", line_color="#22c55e",
                      annotation_text="OECD Avg Post-Tax", annotation_position="right")

        fig.update_layout(
            height=450,
            yaxis_title='Gini Coefficient',
            xaxis_title='Year',
            yaxis_range=[0.2, 0.55],
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Comparison to OECD
        st.subheader(f"How {selected_country} Compares to OECD Average")

        compare_data = pd.DataFrame({
            'Metric': ['Post-Tax Gini', 'Pre-Tax Gini', 'Redistribution (%)'],
            selected_country: [latest_info['gini_post_tax'], latest_info['gini_pre_tax'], latest_info['reduction_pct']],
            'OECD Average': [stats['avg_gini_post'], stats['avg_gini_pre'], stats['avg_reduction_pct']]
        })

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=compare_data['Metric'],
            y=compare_data[selected_country],
            name=selected_country,
            marker_color='#3b82f6'
        ))

        fig.add_trace(go.Bar(
            x=compare_data['Metric'],
            y=compare_data['OECD Average'],
            name='OECD Average',
            marker_color='#94a3b8'
        ))

        fig.update_layout(
            height=400,
            barmode='group',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if latest_info['gini_post_tax'] < 0.28:
            st.success(f"**{selected_country}** has very low inequality, among the most equal OECD countries.")
        elif latest_info['gini_post_tax'] < 0.32:
            st.info(f"**{selected_country}** has below-average inequality for the OECD.")
        elif latest_info['gini_post_tax'] < 0.36:
            st.warning(f"**{selected_country}** has above-average inequality for the OECD.")
        else:
            st.error(f"**{selected_country}** has high inequality compared to other OECD countries.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Country Summary (Latest)", "Full Time Series", "Tier Summary", "Redistribution Comparison"],
        horizontal=True
    )

    if data_view == "Country Summary (Latest)":
        display_data = country_summary.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "gini_country_summary.csv", "text/csv")

    elif data_view == "Full Time Series":
        display_data = full_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "gini_full_data.csv", "text/csv")

    elif data_view == "Tier Summary":
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "gini_tier_summary.csv", "text/csv")

    else:
        st.dataframe(redistribution_comparison, use_container_width=True, hide_index=True)
        csv = redistribution_comparison.to_csv(index=False)
        st.download_button("Download CSV", csv, "gini_redistribution.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Sweden", "Germany"),
        ("United States", "Japan"),
        ("Chile", "Mexico"),
    ],
    data=country_summary,
    name_column="country",
    value_column="gini_post_tax",
    title="Test Your Knowledge",
    prompt="Can you guess which country has MORE income inequality (higher Gini)?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """gini_coefficients ──────────┐
* country, year (PK)        │    country_summary
* gini_post_tax             ├──▶ * country (PK)
* gini_pre_tax              │    * gini_post_tax
* gini_reduction            │    * reduction_pct
* reduction_pct             │
* inequality_tier           │    tier_summary
* redistribution_tier       └──▶ * inequality_tier (PK)
                                 * avg_gini_post"""

SAMPLE_QUERIES = """-- Most equal countries
SELECT country, gini_post_tax, inequality_tier
FROM country_summary
ORDER BY gini_post_tax ASC
LIMIT 10;

-- Best redistribution
SELECT country, gini_pre_tax, gini_post_tax, reduction_pct
FROM country_summary
ORDER BY reduction_pct DESC;

-- Country trend
SELECT year, gini_post_tax, gini_pre_tax
FROM gini_coefficients
WHERE country = 'United States'
ORDER BY year;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["36 OECD countries", "Pre and post-tax measures", "Redistribution analysis", "Time series data"]
)

# Footer
render_data_footer(
    data_sources=["OECD Income Distribution Database (2016)", "OECD Social Expenditure Database"],
    time_period="1987-2014",
    data_points=f"{stats['countries']} countries, 257 observations",
    credits={"Data": "OECD", "Methodology": "OECD Terms of Reference (2012)"},
    dataset_url="https://stats.oecd.org/Index.aspx?DataSetCode=IDD"
)

# Site Footer
render_site_footer()
