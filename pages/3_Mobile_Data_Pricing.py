"""
Mobile Data Pricing Dashboard
Analyzing the cost of mobile data across African nations (2018)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mobile_data.database import MobileDataDatabase
from src.shared import apply_theme, render_sidebar_nav, render_tech_tags, render_page_footer
from components import render_technical_section
from components.dashboard import render_site_header, render_site_footer

# Page config
st.set_page_config(
    page_title="Mobile Data Pricing | Allan Niñal",
    page_icon="📱",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load mobile data from database."""
    with MobileDataDatabase() as db:
        full_data = db.get_full_data()
        region_summary = db.get_region_summary()
        tier_summary = db.get_tier_summary()
        stats = db.get_stats()
    return full_data, region_summary, tier_summary, stats


# Load data
full_data, region_summary, tier_summary, stats = load_data()

# Apply shared theme
apply_theme()

# Additional page-specific styles
st.markdown("""
<style>
    .hero-stat {
        background: var(--accent-gradient);
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        height: 100%;
    }
    .hero-stat h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    .hero-stat p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    .affordable {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    }
    .unaffordable {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    .shocking-banner {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        padding: 1.5rem 2rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        margin: 1rem 0 2rem 0;
    }
    .un-target {
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

# Site Header
render_site_header()

# Header
st.markdown('<h1 class="page-title">📱 Mobile Data Pricing in Africa</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="data-badge">📅 Data: 2018 | 45 African Countries | Alliance for Affordable Internet</div>
""", unsafe_allow_html=True)

st.markdown("""
How much does 1GB of mobile data cost relative to income? This analysis reveals the stark digital divide
across Africa, where the cost of staying connected ranges from less than half a day's income to over 4 months.
""")

st.divider()

# UN Target Explanation
st.markdown("""
<div class="un-target">
<strong>📋 UN Affordability Target:</strong> The United Nations considers broadband affordable when 1GB of data costs
<strong>≤2% of monthly GNI per capita</strong>. Only 7 of 45 African countries meet this target.
</div>
""", unsafe_allow_html=True)

# Hero Stats
col1, col2, col3, col4 = st.columns(4)

most_affordable = full_data.iloc[0]
least_affordable = full_data.iloc[-1]
affordable_count = len(full_data[full_data['cost_pct_gni'] <= 2])
unaffordable_count = len(full_data[full_data['cost_pct_gni'] > 10])

with col1:
    st.markdown(f"""
    <div class="hero-stat affordable">
        <h1>{most_affordable['cost_pct_gni']}%</h1>
        <p><strong>{most_affordable['country']}</strong><br>Most Affordable</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="hero-stat unaffordable">
        <h1>{least_affordable['cost_pct_gni']}%</h1>
        <p><strong>{least_affordable['country']}</strong><br>Least Affordable</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="hero-stat">
        <h1>{affordable_count}</h1>
        <p><strong>Countries</strong><br>Meet UN Target (≤2%)</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    ratio = least_affordable['cost_pct_gni'] / most_affordable['cost_pct_gni']
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
        <h1>{ratio:.0f}x</h1>
        <p><strong>Price Gap</strong><br>Most vs Least Affordable</p>
    </div>
    """, unsafe_allow_html=True)

# Shocking fact banner
st.markdown(f"""
<div class="shocking-banner">
    <h2 style="margin: 0; font-size: 1.8rem;">💸 In {least_affordable['country']}, 1GB of mobile data costs {least_affordable['days_of_income_per_gb']:.0f} days of average income</h2>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">That's over 4 months of work just to afford 1 gigabyte of data. In Egypt, it costs less than 2 days.</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Rankings", "🌍 Regional Analysis", "📊 Affordability Tiers", "🔬 Research Findings", "📋 Raw Data"
])

# Tab 1: Rankings
with tab1:
    st.markdown("### Affordability Rankings (2018)")
    st.markdown("*Cost of 1GB as % of monthly GNI per capita. Lower = more affordable.*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Most Affordable (Top 15)")
        top_15 = full_data.head(15).copy()

        fig_top = px.bar(
            top_15,
            x='cost_pct_gni',
            y='country',
            orientation='h',
            color='cost_pct_gni',
            color_continuous_scale='Greens_r',
            labels={'cost_pct_gni': 'Cost (% of GNI)', 'country': ''}
        )
        fig_top.add_vline(x=2, line_dash="dash", line_color="blue",
                          annotation_text="UN Target (2%)")
        fig_top.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.markdown("#### ❌ Least Affordable (Bottom 15)")
        bottom_15 = full_data.tail(15).copy()

        fig_bottom = px.bar(
            bottom_15,
            x='cost_pct_gni',
            y='country',
            orientation='h',
            color='cost_pct_gni',
            color_continuous_scale='Reds',
            labels={'cost_pct_gni': 'Cost (% of GNI)', 'country': ''}
        )
        fig_bottom.add_vline(x=10, line_dash="dash", line_color="red",
                             annotation_text="Unaffordable (>10%)")
        fig_bottom.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_bottom, use_container_width=True)

    # Days of income visualization
    st.markdown("### 📅 Days of Income Required for 1GB")
    st.markdown("*How many days must the average person work to afford 1GB of data?*")

    fig_days = px.bar(
        full_data.sort_values('days_of_income_per_gb', ascending=True),
        x='country',
        y='days_of_income_per_gb',
        color='affordability_tier',
        color_discrete_map={
            'Affordable': '#10b981',
            'Moderately Affordable': '#f59e0b',
            'Expensive': '#ef4444',
            'Unaffordable': '#7f1d1d'
        },
        labels={'days_of_income_per_gb': 'Days of Income', 'country': '', 'affordability_tier': 'Tier'}
    )
    fig_days.update_layout(
        xaxis_tickangle=-45,
        height=500,
    )
    st.plotly_chart(fig_days, use_container_width=True)

# Tab 2: Regional Analysis
with tab2:
    st.markdown("### Regional Comparison")

    # Regional bar chart
    fig_regions = px.bar(
        region_summary,
        x='region',
        y='avg_cost',
        color='avg_cost',
        color_continuous_scale='RdYlGn_r',
        labels={'avg_cost': 'Average Cost (% of GNI)', 'region': 'Region'},
        text='avg_cost'
    )
    fig_regions.add_hline(y=2, line_dash="dash", line_color="blue",
                          annotation_text="UN Target (2%)")
    fig_regions.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_regions.update_layout(
        height=450,
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_regions, use_container_width=True)

    # Regional details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Regional Statistics")
        region_display = region_summary[['region', 'avg_cost', 'median_cost', 'countries', 'min_cost', 'max_cost']].copy()
        region_display.columns = ['Region', 'Avg Cost', 'Median Cost', 'Countries', 'Min', 'Max']
        st.dataframe(region_display, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("### Cost Distribution by Region")
        fig_box = px.box(
            full_data,
            x='region',
            y='cost_pct_gni',
            color='region',
            labels={'cost_pct_gni': 'Cost (% of GNI)', 'region': ''}
        )
        fig_box.add_hline(y=2, line_dash="dash", line_color="blue")
        fig_box.update_layout(
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # Regional insights
    st.markdown("### Key Regional Insights")

    best_region = region_summary.iloc[0]
    worst_region = region_summary.iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="insight-card">
            <h4>🏆 Most Affordable Region</h4>
            <p><strong>{best_region['region']}</strong> has the lowest average cost
            at <strong>{best_region['avg_cost']:.1f}%</strong> of GNI.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="insight-card">
            <h4>📈 Highest Variation</h4>
            <p><strong>{region_summary.loc[region_summary['std_cost'].idxmax(), 'region']}</strong>
            shows the widest range of prices within the region.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="insight-card">
            <h4>❌ Least Affordable Region</h4>
            <p><strong>{worst_region['region']}</strong> has the highest average cost
            at <strong>{worst_region['avg_cost']:.1f}%</strong> of GNI.</p>
        </div>
        """, unsafe_allow_html=True)

# Tab 3: Affordability Tiers
with tab3:
    st.markdown("### Affordability Tier Distribution")

    # Pie chart
    fig_pie = px.pie(
        tier_summary,
        values='countries',
        names='affordability_tier',
        color='affordability_tier',
        color_discrete_map={
            'Affordable': '#10b981',
            'Moderately Affordable': '#f59e0b',
            'Expensive': '#ef4444',
            'Unaffordable': '#7f1d1d'
        }
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Tier breakdown
    st.markdown("### Tier Definitions")

    col1, col2, col3, col4 = st.columns(4)

    tiers_info = [
        ("Affordable", "≤2%", "#10b981", "Meets UN target"),
        ("Moderately Affordable", "2-5%", "#f59e0b", "Slightly above target"),
        ("Expensive", "5-10%", "#ef4444", "Significantly above target"),
        ("Unaffordable", ">10%", "#7f1d1d", "Far beyond reach for many"),
    ]

    for col, (tier, threshold, color, desc) in zip([col1, col2, col3, col4], tiers_info):
        tier_data = tier_summary[tier_summary['affordability_tier'] == tier]
        count = tier_data['countries'].values[0] if len(tier_data) > 0 else 0

        with col:
            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <h3 style="margin: 0;">{count}</h3>
                <p style="margin: 0.3rem 0 0 0; font-weight: 600;">{tier}</p>
                <small>{threshold}</small><br>
                <small>{desc}</small>
            </div>
            """, unsafe_allow_html=True)

    # Countries by tier
    st.markdown("### Countries by Tier")

    for tier in ['Affordable', 'Moderately Affordable', 'Expensive', 'Unaffordable']:
        with st.expander(f"{tier}"):
            tier_countries = full_data[full_data['affordability_tier'] == tier][['country', 'cost_pct_gni', 'region', 'days_of_income_per_gb']]
            tier_countries.columns = ['Country', 'Cost (% GNI)', 'Region', 'Days of Income']
            st.dataframe(tier_countries, use_container_width=True, hide_index=True)

# Tab 4: Research Findings
with tab4:
    st.markdown("### Research Study Results")
    st.markdown("Based on the data analysis, here are the key research findings:")

    # Study 1
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">📱 Study 1: The Digital Divide</h4>
        <p><b>Finding:</b> Mobile data in the least affordable country ({least_affordable['country']}) costs
        <b>{ratio:.0f} times more</b> (relative to income) than in the most affordable ({most_affordable['country']}).</p>
        <p><b>Implication:</b> Digital connectivity remains a luxury for many African nations,
        limiting access to online education, healthcare, and economic opportunities.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 2
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🎯 Study 2: UN Target Achievement</h4>
        <p><b>Finding:</b> Only <b>{affordable_count} out of 45 countries (15.6%)</b> meet the UN's
        affordability target of ≤2% of GNI for 1GB of data.</p>
        <p><b>Implication:</b> The vast majority of African nations fail to provide affordable
        internet access, creating barriers to digital inclusion and economic development.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 3
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🌍 Study 3: Regional Disparities</h4>
        <p><b>Finding:</b> {best_region['region']} has the most affordable data (avg {best_region['avg_cost']:.1f}%),
        while {worst_region['region']} is the most expensive (avg {worst_region['avg_cost']:.1f}%).</p>
        <p><b>Implication:</b> Geographic location within Africa significantly impacts digital accessibility,
        with Central Africa facing the greatest challenges.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 4
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">💰 Study 4: The Income Barrier</h4>
        <p><b>Finding:</b> In {unaffordable_count} countries, 1GB costs more than <b>10% of monthly income</b>.
        In {least_affordable['country']}, it requires <b>{least_affordable['days_of_income_per_gb']:.0f} days</b> of average earnings.</p>
        <p><b>Implication:</b> For a third of African nations, mobile data is effectively a luxury item,
        deepening inequality between those who can and cannot afford to connect.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 5
    conflict_countries = ['Central African Republic', 'Democratic Republic of Congo', 'Chad', 'South Sudan', 'Mali']
    conflict_data = full_data[full_data['country'].isin(conflict_countries)]
    conflict_avg = conflict_data['cost_pct_gni'].mean()

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">⚠️ Study 5: Conflict Zones & Connectivity</h4>
        <p><b>Finding:</b> Countries experiencing conflict or instability have significantly higher
        data costs. The average cost in conflict-affected nations is <b>{conflict_avg:.1f}%</b> vs
        the overall average of {full_data['cost_pct_gni'].mean():.1f}%.</p>
        <p><b>Implication:</b> Instability not only affects physical infrastructure but also
        digital connectivity, further isolating vulnerable populations.</p>
    </div>
    """, unsafe_allow_html=True)

    # Key correlations
    st.markdown("### Key Insights")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #fee2e2; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>GDP & Data Costs: Inverse Relationship</strong><br>
            <small>Wealthier nations tend to have more affordable data relative to income.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #fef3c7; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>Competition Matters</strong><br>
            <small>Countries with more telecom providers generally have lower prices.</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #dcfce7; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>North Africa Leads</strong><br>
            <small>Better infrastructure and higher GDP contribute to affordability.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #fee2e2; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>Central Africa Lags</strong><br>
            <small>Limited infrastructure and economic challenges drive high costs.</small>
        </div>
        """, unsafe_allow_html=True)

# Tab 5: Raw Data
with tab5:
    st.markdown("### Explore the Raw Data")

    col1, col2 = st.columns(2)

    with col1:
        filter_region = st.multiselect(
            "Filter by Region",
            options=sorted(full_data['region'].unique()),
            default=[]
        )

    with col2:
        filter_tier = st.multiselect(
            "Filter by Affordability Tier",
            options=['Affordable', 'Moderately Affordable', 'Expensive', 'Unaffordable'],
            default=[]
        )

    # Apply filters
    filtered_data = full_data.copy()

    if filter_region:
        filtered_data = filtered_data[filtered_data['region'].isin(filter_region)]

    if filter_tier:
        filtered_data = filtered_data[filtered_data['affordability_tier'].isin(filter_tier)]

    st.write(f"Showing {len(filtered_data):,} countries")

    display_cols = ['rank', 'country', 'region', 'cost_pct_gni', 'affordability_tier', 'days_of_income_per_gb', 'ratio_to_un_target']
    st.dataframe(filtered_data[display_cols], use_container_width=True, height=400)

    # Download button
    csv = filtered_data.to_csv(index=False)
    st.download_button(
        label="📥 Download data as CSV",
        data=csv,
        file_name="mobile_data_pricing.csv",
        mime="text/csv"
    )

# Quiz Section
st.markdown("## Quiz: Test Your Knowledge")

st.markdown("""
<div style="background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border: 2px solid #a855f7; border-radius: 16px; padding: 2rem; margin: 1rem 0;">
    <h3 style="margin: 0;">🎯 Can you guess which country has more affordable mobile data?</h3>
</div>
""", unsafe_allow_html=True)

quiz_pairs = [
    ("Egypt", "Nigeria"),
    ("South Africa", "Kenya"),
    ("Morocco", "Democratic Republic of Congo"),
]

for country_a, country_b in quiz_pairs:
    data_a = full_data[full_data["country"] == country_a]
    data_b = full_data[full_data["country"] == country_b]

    if len(data_a) > 0 and len(data_b) > 0:
        cost_a = data_a.iloc[0]["cost_pct_gni"]
        cost_b = data_b.iloc[0]["cost_pct_gni"]

        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            if st.button(f"🅰️ {country_a}", key=f"quiz_{country_a}", use_container_width=True):
                if cost_a < cost_b:  # Lower cost = more affordable
                    st.success(f"✓ Correct! {country_a} costs {cost_a:.1f}% vs {country_b}'s {cost_b:.1f}%")
                else:
                    st.error(f"✗ Actually, {country_b} is cheaper! ({cost_b:.1f}% vs {cost_a:.1f}%)")

        with col2:
            st.markdown("<div style='text-align: center; font-size: 1.5rem; padding-top: 0.5rem;'>vs</div>", unsafe_allow_html=True)

        with col3:
            if st.button(f"🅱️ {country_b}", key=f"quiz_{country_b}", use_container_width=True):
                if cost_b < cost_a:  # Lower cost = more affordable
                    st.success(f"✓ Correct! {country_b} costs {cost_b:.1f}% vs {country_a}'s {cost_a:.1f}%")
                else:
                    st.error(f"✗ Actually, {country_a} is cheaper! ({cost_a:.1f}% vs {cost_b:.1f}%)")

st.markdown("---")

# Technical Deep Dive
SCHEMA_DIAGRAM = """mobile_data ────────────┐
• country               │
• year                  │
• cost_pct_gni          │    region_summary ─────────┐
• region                │    • region                │
• affordability_tier    │    • avg/median/min/max    │
• ratio_to_un_target    │    • countries count       │
• days_of_income_per_gb │    └───────────────────────┘
• rank                  │
└───────────────────────┘    tier_summary ───────────┐
                             • affordability_tier    │
                             • countries count       │
                             • avg/min/max cost      │
                             └───────────────────────┘"""

SAMPLE_QUERIES = """-- Most affordable countries (UN target compliant)
SELECT country, region, cost_pct_gni, affordability_tier
FROM mobile_data
WHERE cost_pct_gni <= 2
ORDER BY cost_pct_gni;

-- Regional cost comparison
SELECT region,
       ROUND(avg_cost, 2) as avg_cost_pct,
       countries
FROM region_summary
ORDER BY avg_cost;

-- Countries by affordability tier
SELECT affordability_tier,
       countries,
       ROUND(avg_cost, 2) as avg_cost
FROM tier_summary
ORDER BY avg_cost;

-- Days of income required by region
SELECT region,
       ROUND(AVG(days_of_income_per_gb), 1) as avg_days
FROM mobile_data
GROUP BY region
ORDER BY avg_days;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["African region mapping", "UN affordability tier classification", "Days-of-income calculations", "Region and tier summaries"]
)

st.markdown("---")

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Data Source:**
    - Alliance for Affordable Internet
    - UN Broadband Commission
    """)

with col2:
    st.markdown("""
    **Coverage:**
    - 2018 (single year)
    - 45 African countries
    - 6 regions
    """)

with col3:
    st.markdown("""
    **Credits:**
    - Dataset: [A4AI / OWID](https://github.com/owid/owid-datasets/tree/master/datasets/Price%20of%20mobile%20data%20-%20Alliance%20for%20Affordable%20Internet%20(2019))
    """)

render_page_footer("https://github.com/owid/owid-datasets/tree/master/datasets/Price%20of%20mobile%20data%20-%20Alliance%20for%20Affordable%20Internet%20(2019)")

# Site Footer
render_site_footer()
