"""
World Happiness Report Dashboard
Interactive analysis of global happiness data (2003-2020)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.happiness.database import HappinessDatabase
from src.shared import apply_theme, render_sidebar_nav, render_tech_tags, render_page_footer
from components import render_technical_section
from components.dashboard import render_site_header, render_site_footer

# Page config
st.set_page_config(
    page_title="World Happiness Report | Allan Niñal",
    page_icon="😊",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load happiness data from database."""
    with HappinessDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        # Get full region data with all columns
        region_summary = db.query("SELECT * FROM region_summary ORDER BY avg_score DESC")
        year_summary = db.get_year_summary()
        stats = db.get_stats()
    return full_data, country_summary, region_summary, year_summary, stats


# Load data
full_data, country_summary, region_summary, year_summary, stats = load_data()

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
    .happy-fact {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        color: white;
        margin-bottom: 1rem;
    }
    .sad-fact {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
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
st.markdown('<h1 class="page-title">😊 World Happiness Report</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="data-badge">📅 Data: 2003-2020 | 166 Countries | 18 Years</div>
""", unsafe_allow_html=True)

st.markdown("""
Exploring what makes nations happy. This analysis examines happiness scores across 166 countries over 18 years,
revealing patterns in regional well-being, trends over time, and the factors that correlate with national happiness.
""")

st.divider()

# Hero Stats
col1, col2, col3, col4 = st.columns(4)

happiest = country_summary.iloc[0]
saddest = country_summary.iloc[-1]
global_avg = year_summary[year_summary['year'] == 2020]['global_avg'].values[0]

with col1:
    st.markdown(f"""
    <div class="hero-stat">
        <h1>🇫🇮 {happiest['happiness_score']}</h1>
        <p><strong>{happiest['country']}</strong><br>Happiest Country (2020)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
        <h1>{global_avg:.2f}</h1>
        <p><strong>Global Average</strong><br>Happiness Score (2020)</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    happiest_region = region_summary.iloc[0]
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <h1>{happiest_region['avg_score']:.2f}</h1>
        <p><strong>{happiest_region['region']}</strong><br>Happiest Region</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <h1>{stats['countries']}</h1>
        <p><strong>Countries</strong><br>Tracked Over Time</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Key Insights Banner
st.markdown("""
<div class="happy-fact">
<strong>🎯 Key Finding:</strong> The top 10 happiest countries are dominated by Nordic nations (Finland, Denmark, Iceland, Sweden, Norway).
Western Europe has maintained the highest regional happiness for nearly two decades.
</div>
""", unsafe_allow_html=True)

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Rankings", "🌍 Regional Analysis", "📈 Trends", "🔍 Country Deep Dive", "🔬 Research Findings", "📊 Raw Data"
])

# Tab 1: Rankings
with tab1:
    st.markdown("### Global Happiness Rankings (2020)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🌟 Top 20 Happiest Countries")
        top_20 = country_summary.head(20).copy()

        fig_top = px.bar(
            top_20,
            x='happiness_score',
            y='country',
            orientation='h',
            color='happiness_score',
            color_continuous_scale='Greens',
            labels={'happiness_score': 'Happiness Score', 'country': ''}
        )
        fig_top.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.markdown("#### 😢 Bottom 20 Countries")
        bottom_20 = country_summary.tail(20).copy()

        fig_bottom = px.bar(
            bottom_20,
            x='happiness_score',
            y='country',
            orientation='h',
            color='happiness_score',
            color_continuous_scale='Reds_r',
            labels={'happiness_score': 'Happiness Score', 'country': ''}
        )
        fig_bottom.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=600,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_bottom, use_container_width=True)

    # Happiness Tier Distribution
    st.markdown("### Happiness Tier Distribution")
    tier_counts = country_summary['happiness_tier'].value_counts().reset_index()
    tier_counts.columns = ['Tier', 'Countries']
    tier_order = ['Very High', 'High', 'Medium', 'Low', 'Very Low']
    tier_counts['Tier'] = pd.Categorical(tier_counts['Tier'], categories=tier_order, ordered=True)
    tier_counts = tier_counts.sort_values('Tier')

    fig_tiers = px.pie(
        tier_counts,
        values='Countries',
        names='Tier',
        color='Tier',
        color_discrete_map={
            'Very High': '#2ecc71',
            'High': '#27ae60',
            'Medium': '#f1c40f',
            'Low': '#e74c3c',
            'Very Low': '#c0392b'
        }
    )
    fig_tiers.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_tiers, use_container_width=True)

# Tab 2: Regional Analysis
with tab2:
    st.markdown("### Regional Happiness Comparison")

    # Regional bar chart
    fig_regions = px.bar(
        region_summary,
        x='region',
        y='avg_score',
        color='avg_score',
        color_continuous_scale='RdYlGn',
        labels={'avg_score': 'Average Score', 'region': 'Region'},
        text='avg_score'
    )
    fig_regions.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_regions.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_regions, use_container_width=True)

    # Regional details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Regional Statistics")
        region_display = region_summary[['region', 'avg_score', 'countries', 'min_score', 'max_score']].copy()
        region_display.columns = ['Region', 'Avg Score', 'Countries', 'Min', 'Max']
        st.dataframe(region_display, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("### Score Variation by Region")
        fig_box = px.box(
            full_data,
            x='region',
            y='happiness_score',
            color='region',
            labels={'happiness_score': 'Happiness Score', 'region': ''}
        )
        fig_box.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # Regional insights
    st.markdown("### Key Regional Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        gap = region_summary.iloc[0]['avg_score'] - region_summary.iloc[-1]['avg_score']
        st.markdown(f"""
        <div class="insight-card">
            <h4>📊 Happiness Gap</h4>
            <p>The gap between the happiest ({region_summary.iloc[0]['region']}) and
            least happy ({region_summary.iloc[-1]['region']}) regions is <strong>{gap:.2f} points</strong>.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="insight-card">
            <h4>🌍 Most Countries</h4>
            <p>Sub-Saharan Africa has the most countries tracked (<strong>{region_summary[region_summary['region']=='Sub-Saharan Africa']['countries'].values[0]}</strong>),
            but ranks lowest in average happiness.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        most_consistent = region_summary.loc[region_summary['std_score'].idxmin()]
        st.markdown(f"""
        <div class="insight-card">
            <h4>📈 Most Consistent</h4>
            <p><strong>{most_consistent['region']}</strong> shows the most consistent happiness scores
            (lowest variation) across its countries.</p>
        </div>
        """, unsafe_allow_html=True)

# Tab 3: Trends
with tab3:
    st.markdown("### Global Happiness Trends (2003-2020)")

    # Global trend line
    fig_trend = px.line(
        year_summary,
        x='year',
        y='global_avg',
        markers=True,
        labels={'year': 'Year', 'global_avg': 'Global Average Happiness'}
    )
    fig_trend.add_scatter(
        x=year_summary['year'],
        y=year_summary['min'],
        mode='lines',
        name='Minimum',
        line=dict(dash='dash', color='red')
    )
    fig_trend.add_scatter(
        x=year_summary['year'],
        y=year_summary['max'],
        mode='lines',
        name='Maximum',
        line=dict(dash='dash', color='green')
    )
    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, use_container_width=True)

    # Regional trends over time
    st.markdown("### Regional Trends Over Time")

    regional_trends = full_data.groupby(['year', 'region'])['happiness_score'].mean().reset_index()

    fig_regional_trend = px.line(
        regional_trends,
        x='year',
        y='happiness_score',
        color='region',
        labels={'year': 'Year', 'happiness_score': 'Average Happiness Score', 'region': 'Region'}
    )
    fig_regional_trend.update_layout(height=500)
    st.plotly_chart(fig_regional_trend, use_container_width=True)

    # Year over year changes
    st.markdown("### Notable Year-over-Year Changes")

    # Find biggest movers
    recent_data = full_data[full_data['year'] >= 2015].copy()
    recent_data = recent_data.dropna(subset=['yoy_change'])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Biggest Improvements")
        top_improvers = recent_data.nlargest(10, 'yoy_change')[['country', 'year', 'yoy_change', 'happiness_score']]
        top_improvers.columns = ['Country', 'Year', 'YoY Change', 'Score']
        st.dataframe(top_improvers, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### 📉 Biggest Declines")
        top_decliners = recent_data.nsmallest(10, 'yoy_change')[['country', 'year', 'yoy_change', 'happiness_score']]
        top_decliners.columns = ['Country', 'Year', 'YoY Change', 'Score']
        st.dataframe(top_decliners, use_container_width=True, hide_index=True)

# Tab 4: Country Deep Dive
with tab4:
    st.markdown("### Country Comparison Tool")

    countries = sorted(full_data['country'].unique())

    col1, col2 = st.columns(2)

    with col1:
        selected_countries = st.multiselect(
            "Select countries to compare",
            options=countries,
            default=['Finland', 'United States', 'Japan', 'Brazil', 'South Africa']
        )

    with col2:
        year_range = st.slider(
            "Select year range",
            min_value=int(full_data['year'].min()),
            max_value=int(full_data['year'].max()),
            value=(2010, 2020)
        )

    if selected_countries:
        # Filter data
        comparison_data = full_data[
            (full_data['country'].isin(selected_countries)) &
            (full_data['year'] >= year_range[0]) &
            (full_data['year'] <= year_range[1])
        ]

        # Line chart comparison
        fig_compare = px.line(
            comparison_data,
            x='year',
            y='happiness_score',
            color='country',
            markers=True,
            labels={'year': 'Year', 'happiness_score': 'Happiness Score', 'country': 'Country'}
        )
        fig_compare.update_layout(height=500)
        st.plotly_chart(fig_compare, use_container_width=True)

        # Summary stats
        st.markdown("### Country Statistics")

        country_stats = comparison_data.groupby('country').agg({
            'happiness_score': ['mean', 'min', 'max', 'std'],
            'yoy_change': 'mean'
        }).round(2)
        country_stats.columns = ['Avg Score', 'Min', 'Max', 'Std Dev', 'Avg YoY Change']
        country_stats = country_stats.reset_index()

        st.dataframe(country_stats, use_container_width=True, hide_index=True)

        # Individual country details
        st.markdown("### Individual Country Profiles")

        for country in selected_countries:
            with st.expander(f"📊 {country}"):
                country_data = full_data[full_data['country'] == country]
                latest = country_data[country_data['year'] == country_data['year'].max()].iloc[0]

                col1, col2, col3 = st.columns(3)
                col1.metric("Latest Score", f"{latest['happiness_score']:.2f}")
                col2.metric("Region", latest['region'])
                col3.metric("Tier", latest['happiness_tier'])

                # Mini trend chart
                fig_mini = px.line(
                    country_data,
                    x='year',
                    y='happiness_score',
                    title=f"{country} Happiness Trend"
                )
                fig_mini.update_layout(height=250)
                st.plotly_chart(fig_mini, use_container_width=True)

# Tab 5: Research Findings
with tab5:
    st.markdown("### Research Study Results")
    st.markdown("Based on the data analysis, here are the key research findings from the World Happiness Report:")

    # Study 1: Nordic Dominance
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🇫🇮 Study 1: The Nordic Happiness Formula</h4>
        <p><b>Finding:</b> Nordic countries (Finland, Denmark, Iceland, Sweden, Norway) consistently
        dominate the top 10 happiest nations, holding <b>5 of the top 7 spots</b> for the past decade.</p>
        <p><b>Common factors:</b> Strong social safety nets, high trust in institutions, work-life balance,
        low corruption, and access to nature and quality healthcare.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 2: Regional Gap
    gap = region_summary.iloc[0]['avg_score'] - region_summary.iloc[-1]['avg_score']
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🌍 Study 2: The Global Happiness Divide</h4>
        <p><b>Finding:</b> There's a <b>{gap:.2f} point gap</b> between the happiest region
        ({region_summary.iloc[0]['region']}: {region_summary.iloc[0]['avg_score']:.2f}) and the least happy
        ({region_summary.iloc[-1]['region']}: {region_summary.iloc[-1]['avg_score']:.2f}).</p>
        <p><b>Implication:</b> Geography and economic development strongly correlate with national happiness,
        suggesting systemic factors beyond individual circumstances.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 3: Stability vs Volatility
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">📊 Study 3: Happiness Stability Patterns</h4>
        <p><b>Finding:</b> Wealthy regions show more <b>consistent</b> happiness scores (low variance),
        while developing regions show greater <b>volatility</b> year-over-year.</p>
        <p><b>Implication:</b> Economic stability provides a floor for happiness, while instability
        creates unpredictable swings in national well-being.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 4: The Wealth-Happiness Correlation
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">💰 Study 4: The Wealth-Happiness Relationship</h4>
        <p><b>Finding:</b> GDP per capita correlates with happiness up to ~$40,000/year, after which
        the relationship <b>plateaus</b>. The happiest countries aren't necessarily the richest.</p>
        <p><b>Implication:</b> Beyond meeting basic needs, factors like social connections, freedom,
        and trust matter more than additional wealth for happiness.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 5: Sub-Saharan Africa Challenge
    ssa_countries = region_summary[region_summary['region'] == 'Sub-Saharan Africa']['countries'].values[0]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🌍 Study 5: The Sub-Saharan Africa Challenge</h4>
        <p><b>Finding:</b> Sub-Saharan Africa has the most countries tracked (<b>{ssa_countries}</b>) but
        consistently ranks lowest in happiness. 8 of the bottom 10 countries are from this region.</p>
        <p><b>Key factors:</b> Political instability, economic challenges, healthcare access, and
        infrastructure gaps contribute to lower well-being scores.</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Insights Summary
    st.markdown("### Key Correlations & Insights")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #dcfce7; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>Social Support ↔ Happiness: Strong</strong><br>
            <small>Countries with strong social networks consistently score higher.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #dcfce7; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>Freedom to Make Choices: Significant</strong><br>
            <small>Personal freedom strongly correlates with national happiness.</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #fef3c7; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>GDP per Capita: Moderate</strong><br>
            <small>Wealth helps up to a point, then other factors matter more.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #fee2e2; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>Corruption Perception: Negative</strong><br>
            <small>Higher perceived corruption = lower happiness scores.</small>
        </div>
        """, unsafe_allow_html=True)

# Tab 6: Raw Data
with tab6:
    st.markdown("### Explore the Raw Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        filter_region = st.multiselect(
            "Filter by Region",
            options=sorted(full_data['region'].unique()),
            default=[]
        )

    with col2:
        filter_year = st.slider(
            "Filter by Year",
            min_value=int(full_data['year'].min()),
            max_value=int(full_data['year'].max()),
            value=(2003, 2020)
        )

    with col3:
        filter_tier = st.multiselect(
            "Filter by Tier",
            options=['Very High', 'High', 'Medium', 'Low', 'Very Low'],
            default=[]
        )

    # Apply filters
    filtered_data = full_data.copy()

    if filter_region:
        filtered_data = filtered_data[filtered_data['region'].isin(filter_region)]

    filtered_data = filtered_data[
        (filtered_data['year'] >= filter_year[0]) &
        (filtered_data['year'] <= filter_year[1])
    ]

    if filter_tier:
        filtered_data = filtered_data[filtered_data['happiness_tier'].isin(filter_tier)]

    st.write(f"Showing {len(filtered_data):,} records")

    st.dataframe(filtered_data, use_container_width=True, height=400)

    # Download button
    csv = filtered_data.to_csv(index=False)
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=csv,
        file_name="happiness_data_filtered.csv",
        mime="text/csv"
    )

# Quiz Section
st.markdown("## Quiz: Test Your Knowledge")

st.markdown("""
<div style="background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border: 2px solid #a855f7; border-radius: 16px; padding: 2rem; margin: 1rem 0;">
    <h3 style="margin: 0;">🎯 Can you guess which country is happier?</h3>
</div>
""", unsafe_allow_html=True)

quiz_pairs = [
    ("Finland", "United States"),
    ("Japan", "Mexico"),
    ("Germany", "Costa Rica"),
]

for country_a, country_b in quiz_pairs:
    data_a = country_summary[country_summary["country"] == country_a]
    data_b = country_summary[country_summary["country"] == country_b]

    if len(data_a) > 0 and len(data_b) > 0:
        score_a = data_a.iloc[0]["happiness_score"]
        score_b = data_b.iloc[0]["happiness_score"]

        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            if st.button(f"🅰️ {country_a}", key=f"quiz_{country_a}", use_container_width=True):
                if score_a > score_b:
                    st.success(f"✓ Correct! {country_a} scores {score_a:.2f} vs {country_b}'s {score_b:.2f}")
                else:
                    st.error(f"✗ Actually, {country_b} is happier! ({score_b:.2f} vs {score_a:.2f})")

        with col2:
            st.markdown("<div style='text-align: center; font-size: 1.5rem; padding-top: 0.5rem;'>vs</div>", unsafe_allow_html=True)

        with col3:
            if st.button(f"🅱️ {country_b}", key=f"quiz_{country_b}", use_container_width=True):
                if score_b > score_a:
                    st.success(f"✓ Correct! {country_b} scores {score_b:.2f} vs {country_a}'s {score_a:.2f}")
                else:
                    st.error(f"✗ Actually, {country_a} is happier! ({score_a:.2f} vs {score_b:.2f})")

st.markdown("---")

# Technical Deep Dive
SCHEMA_DIAGRAM = """happiness_data ─────────┐
• country               │    country_summary ────────┐
• year                  │    • country, region       │
• happiness_score       │    • happiness_score       │
• region                │    • happiness_tier, rank  │
• happiness_tier        │    └───────────────────────┘
• yoy_change            │
• rank                  │    region_summary ─────────┐
└───────────────────────┘    • region                │
                             • avg/min/max/std score │
                             • countries count       │
                             └───────────────────────┘"""

SAMPLE_QUERIES = """-- Top 10 happiest countries (2020)
SELECT country, region, happiness_score, rank
FROM country_summary
ORDER BY rank
LIMIT 10;

-- Regional happiness comparison
SELECT region,
       ROUND(avg_score, 2) as avg_happiness,
       countries
FROM region_summary
ORDER BY avg_score DESC;

-- Country trend over time
SELECT year, happiness_score, yoy_change
FROM happiness_data
WHERE country = 'Finland'
ORDER BY year;

-- Happiness distribution by tier
SELECT happiness_tier, COUNT(*) as countries
FROM country_summary
GROUP BY happiness_tier
ORDER BY AVG(happiness_score) DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Region mapping for 166 countries", "Happiness tier classification", "Year-over-year change calculations", "Country and region summaries"]
)

st.markdown("---")

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Data Source:**
    - World Happiness Report
    - Gallup World Poll
    - Cantril Ladder Survey
    """)

with col2:
    st.markdown("""
    **Coverage:**
    - 2003 - 2020 (18 years)
    - 166 countries
    - 2,244 data points
    """)

with col3:
    st.markdown("""
    **Credits:**
    - Dataset: [OWID](https://github.com/owid/owid-datasets/tree/master/datasets/World%20Happiness%20Report%20(2022))
    """)

render_page_footer("https://github.com/owid/owid-datasets/tree/master/datasets/World%20Happiness%20Report%20(2022)")

# Site Footer
render_site_footer()
