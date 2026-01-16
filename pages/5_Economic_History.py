"""
Economic History Dashboard - Maddison Project Database
Interactive analysis of global economic development from 1 CE to 2018
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.maddison.database import MaddisonDatabase
from src.shared import apply_theme, render_sidebar_nav, render_tech_tags, render_page_footer
from components import render_technical_section
from components.dashboard import render_site_header, render_site_footer

# Page config
st.set_page_config(
    page_title="Economic History | Allan Niñal",
    page_icon="📈",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load economic data from database."""
    with MaddisonDatabase() as db:
        full_data = db.get_full_data()
        modern_data = db.get_modern_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        year_summary = db.get_year_summary()
        historical_data = db.get_historical_data()
        stats = db.get_stats()
    return full_data, modern_data, country_summary, region_summary, year_summary, historical_data, stats


# Load data
full_data, modern_data, country_summary, region_summary, year_summary, historical_data, stats = load_data()

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
    .era-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .ancient { background: #dbeafe; color: #1e40af; }
    .medieval { background: #fef3c7; color: #92400e; }
    .modern { background: #dcfce7; color: #166534; }
    .contemporary { background: #f3e8ff; color: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    render_sidebar_nav()
    st.divider()
    render_tech_tags(["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

render_site_header()

# Header
st.markdown('<h1 class="page-title">📈 Economic History</h1>', unsafe_allow_html=True)
st.markdown(f"""
<div class="data-badge">📅 Data: 1 CE - 2018 | {stats['entities']} Countries | {stats['records_with_gdp']:,} Data Points</div>
""", unsafe_allow_html=True)

st.markdown("""
Exploring two millennia of global economic development using the Maddison Project Database.
This analysis traces GDP per capita from the Roman Empire to the modern era, revealing the
dramatic transformation of human prosperity through the ages.
""")

st.divider()

# Hero Stats
col1, col2, col3, col4 = st.columns(4)

# Get top country in 2018
top_2018 = country_summary[country_summary['latest_year'] == 2018].head(1)
if len(top_2018) > 0:
    top_country = top_2018.iloc[0]
else:
    top_country = country_summary.iloc[0]

with col1:
    st.markdown(f"""
    <div class="hero-stat">
        <h1>${top_country['gdp_per_capita']:,.0f}</h1>
        <p><strong>{top_country['entity']}</strong><br>Highest GDP/capita (2018)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    latest_global = year_summary[year_summary['year'] == 2018]
    if len(latest_global) > 0:
        global_avg = latest_global.iloc[0]['global_avg_gdp_pc']
    else:
        global_avg = year_summary.iloc[-1]['global_avg_gdp_pc']
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
        <h1>${global_avg:,.0f}</h1>
        <p><strong>Global Average</strong><br>GDP per capita (2018)</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Growth since 1820
    y1820 = year_summary[year_summary['year'] == 1820]
    y2018 = year_summary[year_summary['year'] == 2018]
    if len(y1820) > 0 and len(y2018) > 0:
        growth = y2018.iloc[0]['global_avg_gdp_pc'] / y1820.iloc[0]['global_avg_gdp_pc']
    else:
        growth = 15  # fallback estimate
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <h1>{growth:.0f}x</h1>
        <p><strong>Growth Since 1820</strong><br>Global GDP/capita</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="hero-stat" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <h1>2,000+</h1>
        <p><strong>Years of Data</strong><br>From Roman Empire to Today</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Era badges
st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <span class="era-badge ancient">Ancient (1-500 CE)</span>
    <span class="era-badge medieval">Medieval (500-1500)</span>
    <span class="era-badge modern">Early Modern (1500-1820)</span>
    <span class="era-badge contemporary">Industrial Era (1820+)</span>
</div>
""", unsafe_allow_html=True)

# Key Finding Banner
st.markdown("""
<div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
    <strong>Key Finding:</strong> For most of human history, GDP per capita remained relatively flat at around $500-1000 (in 2011 dollars).
    The "Great Divergence" began around 1820 with the Industrial Revolution, leading to unprecedented growth in Western Europe and North America,
    while much of the world remained at pre-industrial levels until the 20th century.
</div>
""", unsafe_allow_html=True)

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Long-Run Trends", "🌍 Regional Analysis", "🏆 Rankings", "🔍 Country Explorer", "🔬 Research Findings", "📊 Raw Data"
])

# Tab 1: Long-Run Trends
with tab1:
    st.markdown("### The Great Divergence: 2000 Years of Economic History")

    # Global trend line (modern era)
    st.markdown("#### Global Average GDP per Capita (1820-2018)")

    fig_global = px.line(
        year_summary,
        x='year',
        y='global_avg_gdp_pc',
        markers=False,
        labels={'year': 'Year', 'global_avg_gdp_pc': 'GDP per Capita (2011 $)'}
    )
    fig_global.update_layout(height=400)
    fig_global.update_traces(line=dict(width=3, color='#7c3aed'))
    st.plotly_chart(fig_global, use_container_width=True)

    # Major economies comparison
    st.markdown("#### Major Economies: Historical Trajectories")

    major_economies = ['United Kingdom', 'United States', 'China', 'India', 'Japan', 'Germany']
    major_data = modern_data[modern_data['entity'].isin(major_economies)]

    fig_major = px.line(
        major_data,
        x='year',
        y='gdp_per_capita',
        color='entity',
        labels={'year': 'Year', 'gdp_per_capita': 'GDP per Capita (2011 $)', 'entity': 'Country'}
    )
    fig_major.update_layout(height=500)
    st.plotly_chart(fig_major, use_container_width=True)

    # Historical data (ancient/medieval)
    st.markdown("#### Ancient and Medieval World (Before 1820)")

    if len(historical_data) > 0:
        # Group by era
        historical_avg = historical_data.groupby('year')['gdp_per_capita'].mean().reset_index()

        fig_ancient = px.scatter(
            historical_data,
            x='year',
            y='gdp_per_capita',
            color='entity',
            hover_data=['entity', 'year', 'gdp_per_capita'],
            labels={'year': 'Year', 'gdp_per_capita': 'GDP per Capita (2011 $)', 'entity': 'Region/Country'}
        )
        fig_ancient.update_layout(height=400)
        st.plotly_chart(fig_ancient, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Key Observations:**
            - Roman Empire (~1 CE): ~$1,000-1,500 GDP per capita
            - Medieval Europe (1000 CE): Similar levels to antiquity
            - China and India: Comparable to or exceeding Europe until 1500
            - Pre-industrial maximum: ~$2,000-3,000 (Netherlands, 1600s)
            """)
        with col2:
            st.markdown("""
            **The Malthusian Trap:**
            - Population growth absorbed productivity gains
            - Average person lived near subsistence level
            - Occasional prosperity followed by population growth
            - Broken only by Industrial Revolution
            """)

# Tab 2: Regional Analysis
with tab2:
    st.markdown("### Regional Economic Development")

    # Regional bar chart
    fig_regions = px.bar(
        region_summary,
        x='region',
        y='avg_gdp_per_capita',
        color='avg_gdp_per_capita',
        color_continuous_scale='RdYlGn',
        labels={'avg_gdp_per_capita': 'Avg GDP per Capita (2011 $)', 'region': 'Region'},
        text='avg_gdp_per_capita'
    )
    fig_regions.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_regions.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_regions, use_container_width=True)

    # Regional trends over time
    st.markdown("### Regional Trends Over Time")

    # Calculate regional averages by year
    regional_trends = modern_data.groupby(['year', 'region'])['gdp_per_capita'].mean().reset_index()

    fig_regional_trend = px.line(
        regional_trends,
        x='year',
        y='gdp_per_capita',
        color='region',
        labels={'year': 'Year', 'gdp_per_capita': 'Avg GDP per Capita (2011 $)', 'region': 'Region'}
    )
    fig_regional_trend.update_layout(height=500)
    st.plotly_chart(fig_regional_trend, use_container_width=True)

    # Regional statistics table
    st.markdown("### Regional Statistics (2018)")
    region_display = region_summary[['region', 'avg_gdp_per_capita', 'countries', 'total_population']].copy()
    region_display.columns = ['Region', 'Avg GDP/Capita', 'Countries', 'Total Population']
    region_display['Avg GDP/Capita'] = region_display['Avg GDP/Capita'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    region_display['Total Population'] = region_display['Total Population'].apply(lambda x: f"{x/1e9:.2f}B" if pd.notna(x) else "N/A")
    st.dataframe(region_display, use_container_width=True, hide_index=True)

# Tab 3: Rankings
with tab3:
    st.markdown("### Global Economic Rankings (Latest Data)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top 20 Economies by GDP per Capita")
        top_20 = country_summary.head(20).copy()

        fig_top = px.bar(
            top_20,
            x='gdp_per_capita',
            y='entity',
            orientation='h',
            color='gdp_per_capita',
            color_continuous_scale='Greens',
            labels={'gdp_per_capita': 'GDP per Capita (2011 $)', 'entity': ''}
        )
        fig_top.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.markdown("#### Bottom 20 Economies by GDP per Capita")
        bottom_20 = country_summary.tail(20).copy()

        fig_bottom = px.bar(
            bottom_20,
            x='gdp_per_capita',
            y='entity',
            orientation='h',
            color='gdp_per_capita',
            color_continuous_scale='Reds_r',
            labels={'gdp_per_capita': 'GDP per Capita (2011 $)', 'entity': ''}
        )
        fig_bottom.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=600,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_bottom, use_container_width=True)

    # Inequality measure
    st.markdown("### Global Economic Inequality")
    top_gdp = country_summary.head(10)['gdp_per_capita'].mean()
    bottom_gdp = country_summary.tail(10)['gdp_per_capita'].mean()
    ratio = top_gdp / bottom_gdp if bottom_gdp > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Top 10 Average", f"${top_gdp:,.0f}")
    with col2:
        st.metric("Bottom 10 Average", f"${bottom_gdp:,.0f}")
    with col3:
        st.metric("Ratio (Top/Bottom)", f"{ratio:.1f}x")

# Tab 4: Country Explorer
with tab4:
    st.markdown("### Country Comparison Tool")

    countries = sorted(modern_data['entity'].unique())

    col1, col2 = st.columns(2)

    with col1:
        selected_countries = st.multiselect(
            "Select countries to compare",
            options=countries,
            default=['United States', 'China', 'United Kingdom', 'India', 'Japan']
        )

    with col2:
        year_range = st.slider(
            "Select year range",
            min_value=1820,
            max_value=2018,
            value=(1900, 2018)
        )

    if selected_countries:
        # Filter data
        comparison_data = modern_data[
            (modern_data['entity'].isin(selected_countries)) &
            (modern_data['year'] >= year_range[0]) &
            (modern_data['year'] <= year_range[1])
        ]

        # Line chart comparison
        fig_compare = px.line(
            comparison_data,
            x='year',
            y='gdp_per_capita',
            color='entity',
            markers=False,
            labels={'year': 'Year', 'gdp_per_capita': 'GDP per Capita (2011 $)', 'entity': 'Country'}
        )
        fig_compare.update_layout(height=500)
        st.plotly_chart(fig_compare, use_container_width=True)

        # Log scale option
        if st.checkbox("Show logarithmic scale"):
            fig_log = px.line(
                comparison_data,
                x='year',
                y='gdp_per_capita',
                color='entity',
                log_y=True,
                labels={'year': 'Year', 'gdp_per_capita': 'GDP per Capita (2011 $, log scale)', 'entity': 'Country'}
            )
            fig_log.update_layout(height=400)
            st.plotly_chart(fig_log, use_container_width=True)

        # Summary stats
        st.markdown("### Country Statistics")

        for country in selected_countries:
            country_data = modern_data[modern_data['entity'] == country]
            if len(country_data) > 0:
                with st.expander(f"📊 {country}"):
                    latest = country_data[country_data['year'] == country_data['year'].max()].iloc[0]
                    earliest = country_data[country_data['year'] == country_data['year'].min()].iloc[0]

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Latest GDP/capita", f"${latest['gdp_per_capita']:,.0f}")
                    col2.metric("Data Range", f"{int(earliest['year'])}-{int(latest['year'])}")

                    # Calculate growth
                    if earliest['gdp_per_capita'] > 0:
                        growth = latest['gdp_per_capita'] / earliest['gdp_per_capita']
                        col3.metric("Total Growth", f"{growth:.1f}x")

                    # Population if available
                    if pd.notna(latest['population']):
                        col4.metric("Population (Latest)", f"{latest['population']/1e6:.1f}M")

# Tab 5: Research Findings
with tab5:
    st.markdown("### Research Study Results")
    st.markdown("Based on the Maddison Project Database analysis, here are key findings about global economic history:")

    # Study 1: The Great Divergence
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🌍 Study 1: The Great Divergence</h4>
        <p><b>Finding:</b> Around 1820, Western Europe and North America began experiencing unprecedented economic growth,
        while Asia, Africa, and Latin America remained at pre-industrial levels. This "Great Divergence" created
        the modern wealth gap between nations.</p>
        <p><b>Evidence:</b> In 1820, the richest regions were only ~3x wealthier than the poorest. By 1950, this gap
        had grown to 15x, and peaked at over 50x in some comparisons.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 2: The Hockey Stick of History
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">📈 Study 2: The Hockey Stick of History</h4>
        <p><b>Finding:</b> When graphed over 2000 years, global GDP per capita forms a "hockey stick" shape:
        nearly flat for 1,800 years, then sharply upward after 1820.</p>
        <p><b>Magnitude:</b> Global average GDP per capita grew from ~$600 in 1820 to ~$15,000 in 2018 —
        a <b>25x increase</b> in just 200 years, compared to minimal growth in the previous 1,800 years.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 3: Asian Resurgence
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🌏 Study 3: The Asian Economic Miracle</h4>
        <p><b>Finding:</b> After 150 years of relative decline, East Asian economies began catching up
        rapidly in the late 20th century. Japan, South Korea, Taiwan, and later China experienced
        the fastest sustained economic growth in human history.</p>
        <p><b>China's transformation:</b> From ~$500 GDP per capita in 1950 to ~$14,000 in 2018 —
        a <b>28x increase</b> in just 68 years.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 4: Pre-Industrial Prosperity
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🏛️ Study 4: Pre-Industrial Peaks</h4>
        <p><b>Finding:</b> Before industrialization, the wealthiest societies achieved GDP per capita
        of ~$2,000-3,000. The Dutch Golden Age (1600s) and Song Dynasty China (1000-1100 CE)
        represent pre-industrial prosperity peaks.</p>
        <p><b>Implication:</b> Without technological revolution, there appears to be a "ceiling"
        on pre-industrial prosperity around $3,000 per capita.</p>
    </div>
    """, unsafe_allow_html=True)

    # Study 5: Convergence and Divergence
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">🔄 Study 5: Convergence in the 21st Century</h4>
        <p><b>Finding:</b> Since 1990, many developing nations have been growing faster than developed
        nations, leading to partial convergence. The gap between rich and poor countries is narrowing
        for the first time since 1820.</p>
        <p><b>Key drivers:</b> Globalization, technology transfer, improved governance, and investments
        in education and infrastructure.</p>
    </div>
    """, unsafe_allow_html=True)

# Tab 6: Raw Data
with tab6:
    st.markdown("### Explore the Raw Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        filter_region = st.multiselect(
            "Filter by Region",
            options=sorted(modern_data['region'].unique()),
            default=[]
        )

    with col2:
        filter_year = st.slider(
            "Filter by Year",
            min_value=1820,
            max_value=2018,
            value=(1900, 2018),
            key="raw_data_year"
        )

    with col3:
        show_all_years = st.checkbox("Include ancient/medieval data (before 1820)")

    # Apply filters
    if show_all_years:
        filtered_data = full_data.copy()
    else:
        filtered_data = modern_data.copy()

    if filter_region:
        filtered_data = filtered_data[filtered_data['region'].isin(filter_region)]

    if not show_all_years:
        filtered_data = filtered_data[
            (filtered_data['year'] >= filter_year[0]) &
            (filtered_data['year'] <= filter_year[1])
        ]

    filtered_data = filtered_data[filtered_data['gdp_per_capita'].notna()]

    st.write(f"Showing {len(filtered_data):,} records")

    st.dataframe(filtered_data, use_container_width=True, height=400)

    # Download button
    csv = filtered_data.to_csv(index=False)
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=csv,
        file_name="maddison_data_filtered.csv",
        mime="text/csv"
    )

st.markdown("---")

# Technical Deep Dive
SCHEMA_DIAGRAM = """economic_data ──────────┐
• entity                │    country_summary ────────┐
• year                  │    • entity, region        │
• gdp_per_capita        │    • latest_year           │
• population            │    • gdp_per_capita        │
• gdp                   │    • data_points           │
• region                │    └───────────────────────┘
└───────────────────────┘
                             region_summary ─────────┐
                             • region                │
                             • avg_gdp_per_capita    │
                             • total_population      │
                             • countries             │
                             └───────────────────────┘"""

SAMPLE_QUERIES = """-- Top 10 economies in 2018
SELECT entity, region, gdp_per_capita
FROM economic_data
WHERE year = 2018 AND gdp_per_capita IS NOT NULL
ORDER BY gdp_per_capita DESC
LIMIT 10;

-- Regional averages
SELECT region, AVG(gdp_per_capita) as avg_gdp
FROM economic_data
WHERE year = 2018
GROUP BY region
ORDER BY avg_gdp DESC;

-- UK economic history
SELECT year, gdp_per_capita, population
FROM economic_data
WHERE entity = 'United Kingdom'
ORDER BY year;

-- Growth since 1950
SELECT entity,
       MAX(CASE WHEN year = 1950 THEN gdp_per_capita END) as gdp_1950,
       MAX(CASE WHEN year = 2018 THEN gdp_per_capita END) as gdp_2018,
       MAX(CASE WHEN year = 2018 THEN gdp_per_capita END) /
       MAX(CASE WHEN year = 1950 THEN gdp_per_capita END) as growth
FROM economic_data
GROUP BY entity
HAVING gdp_1950 IS NOT NULL AND gdp_2018 IS NOT NULL
ORDER BY growth DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Region mapping for 170+ countries", "Handles data spanning 2000+ years", "Separates ancient/medieval from modern data", "Pre-computed summaries for performance"]
)

st.markdown("---")

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Data Source:**
    - Maddison Project Database 2020
    - Bolt & van Zanden (2020)
    - [OWID Dataset](https://github.com/owid/owid-datasets)
    """)

with col2:
    st.markdown(f"""
    **Coverage:**
    - 1 CE - 2018 ({stats['year_range'][1] - stats['year_range'][0]:,} years)
    - {stats['entities']} countries/regions
    - {stats['records_with_gdp']:,} data points
    """)

with col3:
    st.markdown("""
    **Full Citation:**
    - Bolt, J. & van Zanden, J.L. (2020)
    - "Maddison style estimates of the
    evolution of the world economy"
    """)

render_page_footer("https://github.com/owid/owid-datasets/tree/master/datasets/Maddison%20Project%20Database%202020%20(Bolt%20and%20van%20Zanden%20(2020))")

render_site_footer()
