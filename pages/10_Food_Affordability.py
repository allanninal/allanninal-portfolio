"""
Food Affordability Dashboard
Analyzing global food affordability using World Bank/FAO data (2017-2020)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.food_affordability.database import FoodAffordabilityDatabase
from src.shared import apply_theme, render_sidebar_nav, render_tech_tags, render_page_footer
from components import render_technical_section
from components.dashboard import render_site_header, render_site_footer

# Page config
st.set_page_config(
    page_title="Food Affordability | Allan Ninal",
    page_icon="🍎",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load food affordability data from database."""
    with FoodAffordabilityDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        income_summary = db.get_income_summary()
        stats = db.get_stats()
        most_affordable = db.get_most_affordable(15)
        least_affordable = db.get_least_affordable(15)
        highest_unaffordability = db.get_highest_unaffordability(15)
    return (full_data, country_summary, region_summary, income_summary,
            stats, most_affordable, least_affordable, highest_unaffordability)


# Load data
(full_data, country_summary, region_summary, income_summary,
 stats, most_affordable, least_affordable, highest_unaffordability) = load_data()

# Apply shared theme
apply_theme()

# Additional page-specific styles
st.markdown("""
<style>
    .food-card {
        background: var(--accent-gradient);
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        height: 100%;
    }
    .food-card h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    .food-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    .affordable-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    }
    .unaffordable-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    .crisis-banner {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        padding: 1.5rem 2rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        margin: 1rem 0 2rem 0;
    }
    .diet-info {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    render_sidebar_nav()
    st.divider()
    render_tech_tags(["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

render_site_header()

# Header
st.markdown('<h1 class="page-title">Food Affordability Around the World</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="data-badge">Data: 2017-2020 | 184 Countries | World Bank & FAO</div>
""", unsafe_allow_html=True)

st.markdown("""
Can people afford a healthy diet? This dashboard explores the cost of nutritious food across
184 countries, revealing stark disparities between regions and income groups.
""")

st.divider()

# Diet definitions
st.markdown("""
<div class="diet-info">
<strong>What is a "Healthy Diet"?</strong> The lowest-cost combination of locally available foods that meets
dietary guidelines for energy, nutrients, and food group diversity. A diet is considered
<strong>unaffordable</strong> if it costs more than 52% of household income.
</div>
""", unsafe_allow_html=True)

# Calculate key stats
total_unaffordable = country_summary['healthy_unaffordable_number'].sum()
avg_cost = country_summary['cost_healthy_diet'].dropna().mean()
# Use the filtered data (excludes nulls) for most/least affordable
cheapest = most_affordable.iloc[0] if len(most_affordable) > 0 else None
most_expensive = least_affordable.iloc[0] if len(least_affordable) > 0 else None

# Hero Stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="food-card unaffordable-card">
        <h1>{total_unaffordable/1000:.1f}B</h1>
        <p><strong>People</strong><br>Cannot afford healthy diet</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="food-card">
        <h1>${avg_cost:.2f}</h1>
        <p><strong>Global Average</strong><br>Cost per day</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    if cheapest is not None:
        st.markdown(f"""
        <div class="food-card affordable-card">
            <h1>${cheapest['cost_healthy_diet']:.2f}</h1>
            <p><strong>{cheapest['country']}</strong><br>Most affordable</p>
        </div>
        """, unsafe_allow_html=True)

with col4:
    if most_expensive is not None:
        st.markdown(f"""
        <div class="food-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
            <h1>${most_expensive['cost_healthy_diet']:.2f}</h1>
            <p><strong>{most_expensive['country']}</strong><br>Most expensive</p>
        </div>
        """, unsafe_allow_html=True)

# Crisis banner
if highest_unaffordability is not None and len(highest_unaffordability) > 0:
    worst = highest_unaffordability.iloc[0]
    st.markdown(f"""
    <div class="crisis-banner">
        <h2 style="margin: 0; font-size: 1.8rem;">In {worst['country']}, {worst['healthy_unaffordable_share']:.1f}% of the population cannot afford a healthy diet</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Food affordability remains a critical global challenge, especially in low-income countries</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Rankings", "Regional Analysis", "Income Groups", "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Rankings
with tab1:
    st.markdown("### Cost of a Healthy Diet by Country")
    st.markdown("*Daily cost in 2017 USD PPP to meet dietary guidelines*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Most Affordable")
        fig_cheap = px.bar(
            most_affordable.sort_values('cost_healthy_diet'),
            x='cost_healthy_diet',
            y='country',
            orientation='h',
            color='cost_healthy_diet',
            color_continuous_scale='Greens_r',
            title="Countries with Lowest Cost Healthy Diet",
            labels={'cost_healthy_diet': 'Cost ($/day)', 'country': ''}
        )
        fig_cheap.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_cheap, use_container_width=True)

    with col2:
        st.markdown("#### Most Expensive")
        fig_expensive = px.bar(
            least_affordable.sort_values('cost_healthy_diet', ascending=False),
            x='cost_healthy_diet',
            y='country',
            orientation='h',
            color='cost_healthy_diet',
            color_continuous_scale='Reds',
            title="Countries with Highest Cost Healthy Diet",
            labels={'cost_healthy_diet': 'Cost ($/day)', 'country': ''}
        )
        fig_expensive.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_expensive, use_container_width=True)

    # Unaffordability rankings
    st.markdown("### Population Unable to Afford a Healthy Diet")

    fig_unafford = px.bar(
        highest_unaffordability.sort_values('healthy_unaffordable_share'),
        x='healthy_unaffordable_share',
        y='country',
        orientation='h',
        color='healthy_unaffordable_share',
        color_continuous_scale='Reds',
        title="Countries with Highest Share of Population Unable to Afford Healthy Diet",
        labels={'healthy_unaffordable_share': 'Population Share (%)', 'country': ''}
    )
    fig_unafford.update_layout(
        yaxis={'categoryorder': 'total descending'},
        height=500,
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_unafford, use_container_width=True)

# Tab 2: Regional Analysis
with tab2:
    st.markdown("### Regional Comparison")

    col1, col2 = st.columns(2)

    with col1:
        # Average cost by region
        fig_region_cost = px.bar(
            region_summary.sort_values('avg_cost_healthy'),
            x='region',
            y='avg_cost_healthy',
            color='avg_cost_healthy',
            color_continuous_scale='RdYlGn_r',
            title="Average Cost of Healthy Diet by Region",
            labels={'avg_cost_healthy': 'Avg Cost ($/day)', 'region': 'Region'},
            text='avg_cost_healthy'
        )
        fig_region_cost.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig_region_cost.update_layout(
            height=450,
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_region_cost, use_container_width=True)

    with col2:
        # Unaffordability by region
        fig_region_unafford = px.bar(
            region_summary.sort_values('avg_unaffordable_share', ascending=False),
            x='region',
            y='avg_unaffordable_share',
            color='avg_unaffordable_share',
            color_continuous_scale='Reds',
            title="Average % Unable to Afford Healthy Diet by Region",
            labels={'avg_unaffordable_share': 'Avg Unaffordable (%)', 'region': 'Region'},
            text='avg_unaffordable_share'
        )
        fig_region_unafford.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_region_unafford.update_layout(
            height=450,
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_region_unafford, use_container_width=True)

    # Regional summary table
    st.markdown("### Regional Summary")
    region_display = region_summary.copy()
    region_display['avg_cost_healthy'] = region_display['avg_cost_healthy'].apply(lambda x: f"${x:.2f}")
    region_display['avg_unaffordable_share'] = region_display['avg_unaffordable_share'].apply(lambda x: f"{x:.1f}%")
    region_display['total_unaffordable_millions'] = region_display['total_unaffordable_millions'].apply(lambda x: f"{x:.1f}M")
    region_display.columns = ['Region', 'Countries', 'Avg Cost', 'Min Cost', 'Max Cost', 'Avg Unaffordable %', 'Total Unaffordable']
    st.dataframe(region_display, use_container_width=True, hide_index=True)

# Tab 3: Income Groups
with tab3:
    st.markdown("### Analysis by Income Group")
    st.markdown("*World Bank income classifications*")

    col1, col2 = st.columns(2)

    with col1:
        # Cost by income group
        fig_income_cost = px.bar(
            income_summary,
            x='income_group',
            y='avg_cost_healthy',
            color='avg_cost_healthy',
            color_continuous_scale='Blues',
            title="Average Cost of Healthy Diet by Income Group",
            labels={'avg_cost_healthy': 'Avg Cost ($/day)', 'income_group': 'Income Group'},
            text='avg_cost_healthy'
        )
        fig_income_cost.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig_income_cost.update_layout(
            height=400,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_income_cost, use_container_width=True)

    with col2:
        # Unaffordability by income group
        fig_income_unafford = px.bar(
            income_summary,
            x='income_group',
            y='avg_unaffordable_share',
            color='avg_unaffordable_share',
            color_continuous_scale='Reds',
            title="Average % Unable to Afford Healthy Diet by Income Group",
            labels={'avg_unaffordable_share': 'Avg Unaffordable (%)', 'income_group': 'Income Group'},
            text='avg_unaffordable_share'
        )
        fig_income_unafford.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_income_unafford.update_layout(
            height=400,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_income_unafford, use_container_width=True)

    # Income group details
    st.markdown("### Income Group Summary")
    income_display = income_summary.copy()
    income_display['avg_cost_healthy'] = income_display['avg_cost_healthy'].apply(lambda x: f"${x:.2f}")
    income_display['avg_unaffordable_share'] = income_display['avg_unaffordable_share'].apply(lambda x: f"{x:.1f}%")
    income_display['total_unaffordable_millions'] = income_display['total_unaffordable_millions'].apply(lambda x: f"{x:.1f}M")
    income_display.columns = ['Income Group', 'Countries', 'Avg Cost/Day', 'Avg Unaffordable %', 'Total Unaffordable']
    st.dataframe(income_display, use_container_width=True, hide_index=True)

    # Key insight
    if len(income_summary) > 0:
        low_income = income_summary[income_summary['income_group'] == 'Low income']
        high_income = income_summary[income_summary['income_group'] == 'High income']

        if len(low_income) > 0 and len(high_income) > 0:
            low_pct = low_income['avg_unaffordable_share'].iloc[0]
            high_pct = high_income['avg_unaffordable_share'].iloc[0]

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
                <h4 style="color: #1e40af; margin-top: 0;">Income Disparity</h4>
                <p>In <b>low-income countries</b>, an average of <b>{low_pct:.1f}%</b> of the population cannot afford a healthy diet,
                compared to just <b>{high_pct:.1f}%</b> in high-income countries.</p>
            </div>
            """, unsafe_allow_html=True)

# Tab 4: Research Findings
with tab4:
    st.markdown("### Research Findings")
    st.markdown("*Key insights from the World Bank/FAO food affordability analysis*")

    # Finding 1: Scale of the problem
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">The Scale of Food Insecurity</h4>
        <p><b>Finding:</b> Over <b>3 billion people</b> worldwide cannot afford a healthy diet as defined by
        international dietary guidelines.</p>
        <p><b>Implication:</b> This represents roughly 40% of the global population facing barriers to adequate nutrition,
        with profound implications for health, productivity, and development.</p>
    </div>
    """, unsafe_allow_html=True)

    # Finding 2: Regional disparities
    if len(region_summary) > 0:
        worst_region = region_summary.iloc[0]
        best_region = region_summary.iloc[-1]

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
            <h4 style="color: #1e40af; margin-top: 0;">Regional Disparities</h4>
            <p><b>Finding:</b> <b>{worst_region['region']}</b> has the highest average unaffordability rate at
            <b>{worst_region['avg_unaffordable_share']:.1f}%</b>, while <b>{best_region['region']}</b> has the lowest.</p>
            <p><b>Implication:</b> Geographic location significantly determines food security, with Sub-Saharan Africa
            and South Asia facing the greatest challenges.</p>
        </div>
        """, unsafe_allow_html=True)

    # Finding 3: Cost vs Affordability
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">Cost vs. Affordability Paradox</h4>
        <p><b>Finding:</b> Some countries with low absolute food costs still have high unaffordability rates due to
        extremely low incomes.</p>
        <p><b>Implication:</b> Addressing food security requires both reducing food prices AND increasing incomes.
        Food costs must be considered relative to purchasing power, not just absolute prices.</p>
    </div>
    """, unsafe_allow_html=True)

    # Finding 4: The healthy diet gap
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">The Healthy Diet Gap</h4>
        <p><b>Finding:</b> A healthy diet typically costs <b>5x more</b> than a diet that just meets caloric needs.
        The most expensive components are often fruits, vegetables, and animal-source foods.</p>
        <p><b>Implication:</b> Many people can afford enough calories but not the dietary diversity needed for health,
        leading to "hidden hunger" and micronutrient deficiencies.</p>
    </div>
    """, unsafe_allow_html=True)

    # Key statistics
    st.markdown("### Key Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Countries Analyzed",
            f"{stats['countries']}",
            "Global coverage"
        )

    with col2:
        st.metric(
            "Time Period",
            f"{stats['years'][0]}-{stats['years'][1]}",
            "4 years of data"
        )

    with col3:
        affordable_count = len(country_summary[country_summary['healthy_unaffordable_share'] <= 10])
        st.metric(
            "Countries Meeting Target",
            f"{affordable_count}",
            "Less than 10% unaffordable"
        )

# Tab 5: Country Explorer
with tab5:
    st.markdown("### Country Explorer")

    col1, col2 = st.columns([1, 3])

    with col1:
        countries = sorted(country_summary['country'].unique())
        selected_country = st.selectbox("Select Country", countries)

    # Get country data
    country_info = country_summary[country_summary['country'] == selected_country]
    country_history = full_data[full_data['country'] == selected_country].sort_values('year')

    if len(country_info) > 0:
        info = country_info.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Cost/Day", f"${info['cost_healthy_diet']:.2f}" if pd.notna(info['cost_healthy_diet']) else "N/A")
        with col2:
            unafford = info['healthy_unaffordable_share']
            st.metric("Unaffordable %", f"{unafford:.1f}%" if pd.notna(unafford) else "N/A")
        with col3:
            st.metric("Region", info['region'])
        with col4:
            st.metric("Income Group", info['income_group'])

        # Country trend over time
        if len(country_history) > 1:
            fig_trend = go.Figure()

            fig_trend.add_trace(go.Scatter(
                x=country_history['year'],
                y=country_history['cost_healthy_diet'],
                mode='lines+markers',
                name='Cost of Healthy Diet',
                line=dict(width=3, color='#3b82f6'),
                marker=dict(size=10)
            ))

            fig_trend.update_layout(
                title=f"Cost of Healthy Diet in {selected_country} Over Time",
                xaxis_title="Year",
                yaxis_title="Cost ($/day)",
                height=400
            )

            st.plotly_chart(fig_trend, use_container_width=True)

        # Country data table
        st.markdown("### Historical Data")
        if len(country_history) > 0:
            display_cols = ['year', 'cost_healthy_diet', 'healthy_unaffordable_share',
                           'cost_nutrient_diet', 'cost_energy_diet']
            display_cols = [c for c in display_cols if c in country_history.columns]
            display_data = country_history[display_cols].copy()
            display_data.columns = ['Year', 'Healthy Diet Cost', 'Unaffordable %', 'Nutrient Diet Cost', 'Energy Diet Cost'][:len(display_cols)]
            st.dataframe(display_data, use_container_width=True, hide_index=True)

# Tab 6: Raw Data
with tab6:
    st.markdown("### Explore the Raw Data")

    data_view = st.radio(
        "Select data view",
        ["Country Summary", "Full Data", "Regional Summary", "Income Group Summary"],
        horizontal=True
    )

    if data_view == "Country Summary":
        st.dataframe(country_summary, use_container_width=True, height=400)
    elif data_view == "Full Data":
        st.dataframe(full_data, use_container_width=True, height=400)
    elif data_view == "Regional Summary":
        st.dataframe(region_summary, use_container_width=True)
    else:
        st.dataframe(income_summary, use_container_width=True)

    # Download button
    csv = country_summary.to_csv(index=False)
    st.download_button(
        label="Download Country Summary (CSV)",
        data=csv,
        file_name="food_affordability_summary.csv",
        mime="text/csv"
    )

# Technical Deep Dive
SCHEMA_DIAGRAM = """food_affordability ─────────────────┐
* country                            │
* year                               │
* region                             │    country_summary ────────────────┐
* income_group                       │    * country                       │
* cost_healthy_diet                  │    * region / income_group         │
* cost_nutrient_diet                 │    * cost_healthy_diet             │
* cost_energy_diet                   │    * healthy_unaffordable_share    │
* healthy_unaffordable_share         │    * rank_by_cost                  │
* healthy_unaffordable_number        │    * rank_by_unaffordability       │
* affordability_tier                 │    └────────────────────────────────┘
└────────────────────────────────────┘
                                         region_summary ────────────────────┐
income_summary ──────────────────────┐   * region                          │
* income_group                       │   * countries                       │
* countries                          │   * avg_cost_healthy                │
* avg_cost_healthy                   │   * avg_unaffordable_share          │
* avg_unaffordable_share             │   * total_unaffordable_millions     │
* total_unaffordable_millions        │   └────────────────────────────────┘
└────────────────────────────────────┘"""

SAMPLE_QUERIES = """-- Most affordable countries for healthy diet
SELECT country, region, cost_healthy_diet, healthy_unaffordable_share
FROM country_summary
ORDER BY cost_healthy_diet ASC
LIMIT 10;

-- Countries with highest food insecurity
SELECT country, region, healthy_unaffordable_share
FROM country_summary
WHERE healthy_unaffordable_share IS NOT NULL
ORDER BY healthy_unaffordable_share DESC
LIMIT 10;

-- Regional comparison
SELECT region,
       ROUND(avg_cost_healthy, 2) as avg_cost,
       ROUND(avg_unaffordable_share, 1) as unaffordable_pct,
       countries
FROM region_summary
ORDER BY avg_unaffordable_share DESC;

-- Income group analysis
SELECT income_group,
       countries,
       ROUND(avg_cost_healthy, 2) as avg_cost,
       ROUND(avg_unaffordable_share, 1) as unaffordable_pct
FROM income_summary
ORDER BY avg_unaffordable_share DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["World Bank region classification", "Income group analysis", "Multi-year trends", "Diet cost comparison", "Affordability tier classification"]
)

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Data Source:**
    - World Bank Food Prices for Nutrition
    - FAO State of Food Security Report
    - Herforth et al. (2022)
    """)

with col2:
    st.markdown(f"""
    **Coverage:**
    - {stats['years'][0]}-{stats['years'][1]}
    - {stats['countries']} countries
    - {stats['regions']} regions
    """)

with col3:
    st.markdown("""
    **Credits:**
    - [World Bank DataBank](https://databank.worldbank.org/source/food-prices-for-nutrition)
    - [Our World in Data](https://ourworldindata.org)
    """)

render_page_footer("https://databank.worldbank.org/source/food-prices-for-nutrition")

render_site_footer()
