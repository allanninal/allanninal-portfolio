"""
Technology Adoption Dashboard
Analyzing 160 years of US household technology adoption (1860-2019)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.technology_adoption.database import TechnologyAdoptionDatabase
from src.shared import apply_theme, render_sidebar_nav, render_tech_tags, render_page_footer
from components import render_technical_section
from components.dashboard import render_site_header, render_site_footer

# Page config
st.set_page_config(
    page_title="Technology Adoption | Allan Ninal",
    page_icon="📱",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load technology adoption data from database."""
    with TechnologyAdoptionDatabase() as db:
        full_data = db.get_full_data()
        tech_summary = db.get_technology_summary()
        category_summary = db.get_category_summary()
        decade_summary = db.get_decade_summary()
        stats = db.get_stats()
        fastest = db.get_fastest_adopters(10)
    return full_data, tech_summary, category_summary, decade_summary, stats, fastest


# Load data
full_data, tech_summary, category_summary, decade_summary, stats, fastest_adopters = load_data()

# Apply shared theme
apply_theme()

# Additional page-specific styles
st.markdown("""
<style>
    .tech-card {
        background: var(--accent-gradient);
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        height: 100%;
    }
    .tech-card h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    .tech-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    .fast-adopter {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    }
    .slow-adopter {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    }
    .timeline-banner {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        padding: 1.5rem 2rem;
        border-radius: var(--radius-lg);
        color: white;
        text-align: center;
        margin: 1rem 0 2rem 0;
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
st.markdown('<h1 class="page-title">Technology Adoption in US Households</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="data-badge">Data: 1860-2019 | 45 Technologies | 7 Categories | Our World in Data</div>
""", unsafe_allow_html=True)

st.markdown("""
How quickly do American households adopt new technologies? From the flush toilet in 1860 to smartphones
in 2019, this dashboard explores 160 years of technological change in US households.
""")

st.divider()

# Timeline banner
year_range = stats["year_range"]
st.markdown(f"""
<div class="timeline-banner">
    <h2 style="margin: 0; font-size: 1.8rem;">160 Years of Innovation: {year_range[0]} - {year_range[1]}</h2>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">From running water to smartphones - tracking how technology transforms daily life</p>
</div>
""", unsafe_allow_html=True)

# Hero Stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="tech-card">
        <h1>{stats['technologies']}</h1>
        <p><strong>Technologies</strong><br>Tracked</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="tech-card fast-adopter">
        <h1>{stats['years_covered']}</h1>
        <p><strong>Years</strong><br>of Data</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="tech-card slow-adopter">
        <h1>{stats['categories']}</h1>
        <p><strong>Categories</strong><br>of Technology</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    universal_count = len(tech_summary[tech_summary['max_adoption'] >= 90])
    st.markdown(f"""
    <div class="tech-card" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
        <h1>{universal_count}</h1>
        <p><strong>Technologies</strong><br>Reached 90%+</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "S-Curves", "Speed of Adoption", "Categories", "Research Findings", "Explorer", "Raw Data"
])

# Tab 1: S-Curves (Classic adoption visualization)
with tab1:
    st.markdown("### Technology Adoption S-Curves")
    st.markdown("*The classic 'S-curve' pattern shows how technologies spread through society*")

    col1, col2 = st.columns([1, 3])

    with col1:
        # Category filter
        categories = sorted(full_data['category'].unique())
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)

        # Filter technologies based on category
        if selected_category == "All":
            available_techs = sorted(full_data['technology'].unique())
        else:
            available_techs = sorted(full_data[full_data['category'] == selected_category]['technology'].unique())

        # Multi-select for technologies
        default_techs = ["Automobile", "Television", "Internet", "Smartphone usage"]
        default_selection = [t for t in default_techs if t in available_techs][:4]

        selected_techs = st.multiselect(
            "Select Technologies",
            available_techs,
            default=default_selection if default_selection else available_techs[:4]
        )

    with col2:
        if selected_techs:
            filtered_data = full_data[full_data['technology'].isin(selected_techs)]

            fig_scurve = px.line(
                filtered_data,
                x='year',
                y='adoption_pct',
                color='technology',
                title="Technology Adoption Over Time",
                labels={'year': 'Year', 'adoption_pct': 'Household Adoption (%)', 'technology': 'Technology'}
            )
            fig_scurve.update_layout(
                height=500,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_scurve.update_traces(line=dict(width=3))

            # Add 50% threshold line
            fig_scurve.add_hline(y=50, line_dash="dash", line_color="gray",
                                  annotation_text="50% (Mainstream)")

            st.plotly_chart(fig_scurve, use_container_width=True)
        else:
            st.info("Select at least one technology to view the S-curves")

    # Era comparison
    st.markdown("### Adoption by Era")
    st.markdown("*Compare how quickly technologies spread across different time periods*")

    # Group technologies by introduction era
    era_data = tech_summary.copy()
    era_data['era'] = pd.cut(
        era_data['first_year'],
        bins=[1850, 1920, 1950, 1980, 2000, 2020],
        labels=['Pre-1920', '1920-1950', '1950-1980', '1980-2000', '2000+']
    )

    era_avg = era_data.groupby('era').agg({
        'years_to_50_pct': 'mean',
        'technology': 'count',
        'max_adoption': 'mean'
    }).round(1).reset_index()
    era_avg.columns = ['Era', 'Avg Years to 50%', 'Technologies', 'Avg Max Adoption']

    col1, col2 = st.columns(2)

    with col1:
        fig_era = px.bar(
            era_avg,
            x='Era',
            y='Avg Years to 50%',
            color='Avg Years to 50%',
            color_continuous_scale='RdYlGn_r',
            title="Average Years to 50% Adoption by Era",
            text='Avg Years to 50%'
        )
        fig_era.update_traces(textposition='outside')
        fig_era.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_era, use_container_width=True)

    with col2:
        fig_era_count = px.bar(
            era_avg,
            x='Era',
            y='Technologies',
            color='Technologies',
            color_continuous_scale='Blues',
            title="Number of New Technologies by Era",
            text='Technologies'
        )
        fig_era_count.update_traces(textposition='outside')
        fig_era_count.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_era_count, use_container_width=True)

# Tab 2: Speed of Adoption
with tab2:
    st.markdown("### Speed of Technology Adoption")
    st.markdown("*How long did it take each technology to reach 50% household adoption?*")

    # Filter to technologies that reached 50%
    reached_50 = tech_summary[tech_summary['years_to_50_pct'].notna()].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Fastest Adopters")
        fastest_10 = reached_50.nsmallest(15, 'years_to_50_pct')

        fig_fast = px.bar(
            fastest_10.sort_values('years_to_50_pct'),
            x='years_to_50_pct',
            y='technology',
            orientation='h',
            color='years_to_50_pct',
            color_continuous_scale='Greens_r',
            title="Technologies with Fastest Adoption",
            labels={'years_to_50_pct': 'Years to 50%', 'technology': ''}
        )
        fig_fast.update_layout(
            yaxis={'categoryorder': 'total descending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_fast, use_container_width=True)

    with col2:
        st.markdown("#### Slowest Adopters")
        slowest_10 = reached_50.nlargest(15, 'years_to_50_pct')

        fig_slow = px.bar(
            slowest_10.sort_values('years_to_50_pct', ascending=False),
            x='years_to_50_pct',
            y='technology',
            orientation='h',
            color='years_to_50_pct',
            color_continuous_scale='Reds',
            title="Technologies with Slowest Adoption",
            labels={'years_to_50_pct': 'Years to 50%', 'technology': ''}
        )
        fig_slow.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_slow, use_container_width=True)

    # Timeline scatter
    st.markdown("### Introduction Year vs Adoption Speed")
    st.markdown("*Are newer technologies adopted faster?*")

    fig_scatter = px.scatter(
        reached_50,
        x='first_year',
        y='years_to_50_pct',
        color='category',
        size='max_adoption',
        hover_name='technology',
        title="Technology Introduction Year vs Years to 50% Adoption",
        labels={
            'first_year': 'Year Introduced',
            'years_to_50_pct': 'Years to 50% Adoption',
            'category': 'Category',
            'max_adoption': 'Max Adoption'
        }
    )
    fig_scatter.update_layout(height=500)
    # Add trend line
    fig_scatter.add_trace(go.Scatter(
        x=reached_50['first_year'],
        y=reached_50['years_to_50_pct'].rolling(5, center=True).mean(),
        mode='lines',
        name='Trend (5-tech avg)',
        line=dict(color='red', dash='dash', width=2)
    ))
    st.plotly_chart(fig_scatter, use_container_width=True)

# Tab 3: Categories
with tab3:
    st.markdown("### Technology Categories")

    col1, col2 = st.columns(2)

    with col1:
        # Category pie chart
        fig_pie = px.pie(
            category_summary,
            values='technologies',
            names='category',
            title="Technologies by Category",
            hole=0.4
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Category adoption speed
        fig_cat_speed = px.bar(
            category_summary.sort_values('avg_years_to_peak'),
            x='category',
            y='avg_years_to_peak',
            color='avg_years_to_peak',
            color_continuous_scale='RdYlGn_r',
            title="Average Years to 50% by Category",
            labels={'avg_years_to_peak': 'Avg Years', 'category': 'Category'}
        )
        fig_cat_speed.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_cat_speed, use_container_width=True)

    # Category timeline
    st.markdown("### Category Timeline")

    for category in sorted(category_summary['category'].unique()):
        with st.expander(f"{category}"):
            cat_techs = full_data[full_data['category'] == category]

            fig_cat = px.line(
                cat_techs,
                x='year',
                y='adoption_pct',
                color='technology',
                title=f"{category} Technologies Over Time",
                labels={'year': 'Year', 'adoption_pct': 'Adoption (%)', 'technology': 'Technology'}
            )
            fig_cat.update_layout(height=400)
            st.plotly_chart(fig_cat, use_container_width=True)

            # Category summary table
            cat_summary = tech_summary[tech_summary['category'] == category][
                ['technology', 'first_year', 'max_adoption', 'years_to_50_pct', 'current_adoption']
            ].copy()
            cat_summary.columns = ['Technology', 'Introduced', 'Peak %', 'Years to 50%', 'Current %']
            st.dataframe(cat_summary, use_container_width=True, hide_index=True)

# Tab 4: Research Findings
with tab4:
    st.markdown("### Research Findings")
    st.markdown("*Key insights from 160 years of technology adoption data*")

    # Calculate key stats for findings
    avg_time_old = tech_summary[tech_summary['first_year'] < 1950]['years_to_50_pct'].mean()
    avg_time_new = tech_summary[tech_summary['first_year'] >= 2000]['years_to_50_pct'].mean()
    speed_increase = avg_time_old / avg_time_new if avg_time_new > 0 else 0

    # Finding 1
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">Accelerating Adoption</h4>
        <p><b>Finding:</b> Technologies introduced after 2000 reach 50% adoption <b>{speed_increase:.1f}x faster</b>
        than those introduced before 1950.</p>
        <p><b>Implication:</b> Network effects, digital distribution, and pre-existing infrastructure
        enable rapid scaling of modern technologies.</p>
    </div>
    """, unsafe_allow_html=True)

    # Finding 2
    universal_techs = tech_summary[tech_summary['max_adoption'] >= 95]['technology'].tolist()
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">Universal Technologies</h4>
        <p><b>Finding:</b> <b>{len(universal_techs)}</b> technologies have achieved near-universal adoption (95%+):
        {', '.join(universal_techs[:5])}...</p>
        <p><b>Implication:</b> Certain technologies become so essential they're considered necessities rather than luxuries.</p>
    </div>
    """, unsafe_allow_html=True)

    # Finding 3
    landline_data = tech_summary[tech_summary['technology'] == 'Landline']
    mobile_data = tech_summary[tech_summary['technology'] == 'Cellular phone']

    if len(landline_data) > 0 and len(mobile_data) > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
            <h4 style="color: #1e40af; margin-top: 0;">Technology Displacement</h4>
            <p><b>Finding:</b> The landline took <b>{int(landline_data['years_to_50_pct'].iloc[0])}</b> years to reach 50%,
            while cellular phones took only <b>{int(mobile_data['years_to_50_pct'].iloc[0])}</b> years.</p>
            <p><b>Implication:</b> Newer technologies can leapfrog older ones, and replacement cycles are accelerating.</p>
        </div>
        """, unsafe_allow_html=True)

    # Finding 4
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
        <h4 style="color: #1e40af; margin-top: 0;">The S-Curve Pattern</h4>
        <p><b>Finding:</b> Most technologies follow a consistent S-curve: slow early adoption, rapid growth,
        then plateau at saturation.</p>
        <p><b>Implication:</b> Understanding where a technology is on its S-curve helps predict future growth
        and market saturation timing.</p>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    st.markdown("### Key Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Fastest to 50%",
            "2 years",
            "Smartphone usage (2011-2013)"
        )

    with col2:
        st.metric(
            "Slowest to 50%",
            "76 years",
            "Dishwasher (1922-1998)"
        )

    with col3:
        st.metric(
            "Avg Time to 50%",
            f"{tech_summary['years_to_50_pct'].mean():.0f} years",
            "Across all technologies"
        )

# Tab 5: Explorer
with tab5:
    st.markdown("### Technology Explorer")

    col1, col2 = st.columns([1, 3])

    with col1:
        all_techs = sorted(full_data['technology'].unique())
        selected_tech = st.selectbox("Select Technology", all_techs)

    # Get technology details
    tech_info = tech_summary[tech_summary['technology'] == selected_tech]
    tech_data = full_data[full_data['technology'] == selected_tech].sort_values('year')

    if len(tech_info) > 0:
        info = tech_info.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Introduced", int(info['first_year']))
        with col2:
            st.metric("Peak Adoption", f"{info['max_adoption']:.1f}%")
        with col3:
            yrs = info['years_to_50_pct']
            st.metric("Years to 50%", f"{int(yrs)}" if pd.notna(yrs) else "N/A")
        with col4:
            st.metric("Category", info['category'])

        # Technology timeline
        fig_tech = go.Figure()

        fig_tech.add_trace(go.Scatter(
            x=tech_data['year'],
            y=tech_data['adoption_pct'],
            mode='lines+markers',
            name=selected_tech,
            line=dict(width=3, color='#3b82f6'),
            marker=dict(size=8)
        ))

        fig_tech.add_hline(y=50, line_dash="dash", line_color="gray",
                           annotation_text="50% (Mainstream)")
        fig_tech.add_hline(y=90, line_dash="dash", line_color="green",
                           annotation_text="90% (Universal)")

        fig_tech.update_layout(
            title=f"{selected_tech} Adoption Over Time",
            xaxis_title="Year",
            yaxis_title="Household Adoption (%)",
            height=450,
            yaxis=dict(range=[0, 105])
        )

        st.plotly_chart(fig_tech, use_container_width=True)

        # Detailed data table
        st.markdown("### Detailed Data")
        display_data = tech_data[['year', 'adoption_pct', 'adoption_tier']].copy()
        display_data.columns = ['Year', 'Adoption %', 'Tier']
        st.dataframe(display_data, use_container_width=True, hide_index=True)

# Tab 6: Raw Data
with tab6:
    st.markdown("### Explore the Raw Data")

    data_view = st.radio(
        "Select data view",
        ["Full Data", "Technology Summary", "Category Summary", "Decade Summary"],
        horizontal=True
    )

    if data_view == "Full Data":
        st.dataframe(full_data, use_container_width=True, height=400)
    elif data_view == "Technology Summary":
        st.dataframe(tech_summary, use_container_width=True, height=400)
    elif data_view == "Category Summary":
        st.dataframe(category_summary, use_container_width=True)
    else:
        st.dataframe(decade_summary, use_container_width=True)

    # Download button
    csv = full_data.to_csv(index=False)
    st.download_button(
        label="Download Full Data (CSV)",
        data=csv,
        file_name="technology_adoption.csv",
        mime="text/csv"
    )

# Technical Deep Dive
SCHEMA_DIAGRAM = """technology_adoption ────────────┐
* technology                     │
* year                           │    technology_summary ──────────┐
* adoption_pct                   │    * technology                 │
* category                       │    * category                   │
* decade                         │    * first_year / last_year     │
* adoption_tier                  │    * max_adoption               │
└────────────────────────────────┘    * years_to_50_pct           │
                                      * peak_year                  │
category_summary ────────────────┐    └──────────────────────────────┘
* category                       │
* technologies                   │    decade_summary ───────────────┐
* avg_max_adoption               │    * decade                      │
* avg_years_to_peak              │    * avg_adoption                │
* oldest_tech_year               │    * technologies_tracked        │
* newest_tech_year               │    * new_technologies            │
└────────────────────────────────┘    └──────────────────────────────┘"""

SAMPLE_QUERIES = """-- Technologies with fastest adoption
SELECT technology, first_year, years_to_50_pct, max_adoption
FROM technology_summary
WHERE years_to_50_pct IS NOT NULL
ORDER BY years_to_50_pct ASC
LIMIT 10;

-- Category comparison
SELECT category,
       technologies,
       ROUND(avg_max_adoption, 1) as avg_max_pct,
       ROUND(avg_years_to_peak, 1) as avg_years
FROM category_summary
ORDER BY avg_years_to_peak;

-- Adoption by decade
SELECT decade,
       ROUND(avg_adoption, 1) as avg_pct,
       technologies_tracked,
       new_technologies
FROM decade_summary
ORDER BY decade;

-- Technologies that reached universal adoption (90%+)
SELECT technology, category, first_year, max_adoption, years_to_50_pct
FROM technology_summary
WHERE max_adoption >= 90
ORDER BY years_to_50_pct ASC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["S-curve adoption analysis", "Technology categorization", "Speed of adoption metrics", "Era comparison", "Interactive technology explorer"]
)

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Data Source:**
    - Our World in Data
    - Comin and Hobijn (2004)
    - US Census Bureau
    """)

with col2:
    st.markdown(f"""
    **Coverage:**
    - {year_range[0]}-{year_range[1]} ({stats['years_covered']} years)
    - {stats['technologies']} technologies
    - {stats['categories']} categories
    """)

with col3:
    st.markdown("""
    **Credits:**
    - Dataset: [OWID Technology Adoption](https://ourworldindata.org/grapher/technology-adoption-by-households-in-the-united-states)
    """)

render_page_footer("https://ourworldindata.org/grapher/technology-adoption-by-households-in-the-united-states")

render_site_footer()
