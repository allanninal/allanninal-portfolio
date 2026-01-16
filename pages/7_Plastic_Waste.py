"""Plastic Waste Analysis Dashboard using Jambeck et al. (2015) data."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.plastic_waste import PlasticWasteDatabase
from components.dashboard import render_site_header, render_site_footer


st.set_page_config(
    page_title="Plastic Waste & Ocean Pollution",
    page_icon="🌊",
    layout="wide"
)


@st.cache_resource
def get_database():
    """Get database connection."""
    db = PlasticWasteDatabase().connect()
    return db


@st.cache_data
def load_data():
    """Load all data from database."""
    db = get_database()
    return {
        "full": db.get_full_data(),
        "country_summary": db.get_country_summary(),
        "region_summary": db.get_region_summary(),
        "top_polluters": db.get_top_polluters(20),
        "top_per_capita": db.get_top_per_capita(20),
        "waste_management": db.get_waste_management_analysis(),
        "projections": db.get_projection_analysis(),
        "stats": db.get_stats()
    }


# Load data
data = load_data()
db = get_database()

render_site_header()

# Header
st.title("🌊 Plastic Waste & Ocean Pollution")
st.markdown("*Analyzing coastal plastic waste streams and their potential contribution to ocean debris*")

# Hero stats
col1, col2, col3, col4 = st.columns(4)

stats = data["stats"]

with col1:
    mismanaged_2010_mt = stats["total_mismanaged_2010"] / 1000000 if stats["total_mismanaged_2010"] else 0
    st.metric(
        "Mismanaged Plastic (2010)",
        f"{mismanaged_2010_mt:.1f}M tonnes",
        None
    )

with col2:
    mismanaged_2025_mt = stats["total_mismanaged_2025"] / 1000000 if stats["total_mismanaged_2025"] else 0
    growth = ((mismanaged_2025_mt - mismanaged_2010_mt) / mismanaged_2010_mt * 100) if mismanaged_2010_mt > 0 else 0
    st.metric(
        "Projected 2025",
        f"{mismanaged_2025_mt:.1f}M tonnes",
        f"+{growth:.0f}% growth"
    )

with col3:
    coastal_pop_b = stats["total_coastal_pop"] / 1000000000 if stats["total_coastal_pop"] else 0
    st.metric(
        "Coastal Population",
        f"{coastal_pop_b:.2f}B people",
        None
    )

with col4:
    st.metric(
        "Countries Analyzed",
        stats["total_countries"],
        "coastal nations"
    )

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Top Polluters", "🌍 Regional Analysis", "📊 Waste Management",
    "📈 2025 Projections", "📚 Research Findings", "📋 Raw Data"
])

# Tab 1: Top Polluters
with tab1:
    st.header("Top Contributors to Ocean Plastic Pollution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("By Total Mismanaged Waste (2010)")
        top_polluters = data["top_polluters"].head(15)
        top_polluters['mismanaged_mt'] = top_polluters['mismanaged_2010'] / 1000000
        
        fig_total = px.bar(
            top_polluters.sort_values('mismanaged_mt'),
            x='mismanaged_mt',
            y='entity',
            color='region',
            orientation='h',
            title="Top 15 Countries by Total Mismanaged Plastic (Million Tonnes)",
            labels={'entity': 'Country', 'mismanaged_mt': 'Mismanaged Plastic (Million Tonnes)', 'region': 'Region'}
        )
        fig_total.update_layout(height=500)
        st.plotly_chart(fig_total, use_container_width=True)
    
    with col2:
        st.subheader("By Per Capita Mismanaged Waste")
        top_per_capita = data["top_per_capita"].head(15)
        
        fig_per_capita = px.bar(
            top_per_capita.sort_values('mismanaged_per_capita'),
            x='mismanaged_per_capita',
            y='entity',
            color='region',
            orientation='h',
            title="Top 15 Countries by Per Capita Mismanaged Plastic (kg/person/day)",
            labels={'entity': 'Country', 'mismanaged_per_capita': 'Per Capita (kg/person/day)', 'region': 'Region'}
        )
        fig_per_capita.update_layout(height=500)
        st.plotly_chart(fig_per_capita, use_container_width=True)
    
    # Key insight
    st.info("""
    **Key Finding:** While China and Indonesia top the list in total mismanaged plastic, 
    small island nations like Sri Lanka, Maldives, and Guyana have the highest per capita rates.
    This highlights the different nature of the problem: large populations vs. limited waste infrastructure.
    """)

# Tab 2: Regional Analysis
with tab2:
    st.header("Regional Analysis")
    
    region_summary = data["region_summary"]
    region_summary['total_mismanaged_mt'] = region_summary['total_mismanaged_2010'] / 1000000
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_region = px.pie(
            region_summary,
            values='total_mismanaged_2010',
            names='region',
            title="Share of Global Mismanaged Plastic by Region (2010)",
            hole=0.4
        )
        fig_region.update_layout(height=450)
        st.plotly_chart(fig_region, use_container_width=True)
    
    with col2:
        fig_region_bar = px.bar(
            region_summary.sort_values('total_mismanaged_mt', ascending=True),
            x='total_mismanaged_mt',
            y='region',
            color='avg_inadequate_pct',
            color_continuous_scale='Reds',
            orientation='h',
            title="Mismanaged Plastic by Region (Million Tonnes)",
            labels={'region': 'Region', 'total_mismanaged_mt': 'Mismanaged Plastic (MT)', 
                   'avg_inadequate_pct': 'Avg Inadequate %'}
        )
        fig_region_bar.update_layout(height=450)
        st.plotly_chart(fig_region_bar, use_container_width=True)
    
    # Regional data table
    st.subheader("Regional Summary")
    display_cols = ['region', 'countries', 'total_coastal_pop', 'total_plastic_waste', 
                   'total_mismanaged_2010', 'total_mismanaged_2025', 'avg_inadequate_pct']
    st.dataframe(
        region_summary[display_cols].round(2),
        use_container_width=True,
        hide_index=True,
        column_config={
            'region': 'Region',
            'countries': 'Countries',
            'total_coastal_pop': st.column_config.NumberColumn('Coastal Population', format="%d"),
            'total_plastic_waste': st.column_config.NumberColumn('Plastic Waste (tonnes)', format="%d"),
            'total_mismanaged_2010': st.column_config.NumberColumn('Mismanaged 2010', format="%d"),
            'total_mismanaged_2025': st.column_config.NumberColumn('Mismanaged 2025', format="%d"),
            'avg_inadequate_pct': st.column_config.NumberColumn('Avg Inadequate %', format="%.1f%%")
        }
    )

# Tab 3: Waste Management
with tab3:
    st.header("Waste Management Efficiency Analysis")
    
    waste_mgmt = data["waste_management"]
    
    # Rating distribution
    col1, col2 = st.columns(2)
    
    with col1:
        rating_counts = waste_mgmt['management_rating'].value_counts()
        fig_ratings = px.pie(
            values=rating_counts.values,
            names=rating_counts.index,
            title="Distribution of Waste Management Ratings",
            color=rating_counts.index,
            color_discrete_map={
                'Excellent': '#10b981',
                'Good': '#3b82f6',
                'Moderate': '#f59e0b',
                'Poor': '#ef4444',
                'Critical': '#7f1d1d'
            }
        )
        fig_ratings.update_layout(height=400)
        st.plotly_chart(fig_ratings, use_container_width=True)
    
    with col2:
        # Scatter plot: inadequate % vs total plastic waste
        fig_scatter = px.scatter(
            waste_mgmt,
            x='inadequate_mgmt_pct',
            y='mismanaged_2010',
            color='region',
            size='plastic_waste',
            hover_name='entity',
            title="Inadequate Management % vs Total Mismanaged Plastic",
            labels={
                'inadequate_mgmt_pct': 'Inadequate Management (%)',
                'mismanaged_2010': 'Mismanaged Plastic (tonnes)',
                'region': 'Region'
            },
            log_y=True
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Countries with best and worst management
    st.subheader("Waste Management by Country")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Best Managed (0% Inadequate)**")
        excellent = waste_mgmt[waste_mgmt['inadequate_mgmt_pct'] == 0][['entity', 'region', 'plastic_waste']].head(15)
        st.dataframe(excellent, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Worst Managed (80%+ Inadequate)**")
        critical = waste_mgmt[waste_mgmt['inadequate_mgmt_pct'] >= 80][['entity', 'region', 'inadequate_mgmt_pct', 'mismanaged_2010']].head(15)
        st.dataframe(critical, use_container_width=True, hide_index=True)

# Tab 4: 2025 Projections
with tab4:
    st.header("2010 to 2025 Projections")
    
    projections = data["projections"]
    projections['absolute_change_mt'] = projections['absolute_change'] / 1000000
    
    # Top countries by projected increase
    top_increase = projections.nlargest(15, 'absolute_change')
    
    fig_proj = px.bar(
        top_increase.sort_values('absolute_change'),
        x='absolute_change',
        y='entity',
        color='growth_pct',
        color_continuous_scale='Reds',
        orientation='h',
        title="Countries with Largest Projected Increase in Mismanaged Plastic (2010-2025)",
        labels={'entity': 'Country', 'absolute_change': 'Increase (tonnes)', 'growth_pct': 'Growth %'}
    )
    fig_proj.update_layout(height=500)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # Comparison chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_compare = go.Figure()
        top_countries = projections.nlargest(10, 'mismanaged_2010')
        fig_compare.add_trace(go.Bar(
            name='2010',
            x=top_countries['entity'],
            y=top_countries['mismanaged_2010'] / 1000000,
            marker_color='#3b82f6'
        ))
        fig_compare.add_trace(go.Bar(
            name='2025 (Projected)',
            x=top_countries['entity'],
            y=top_countries['mismanaged_2025'] / 1000000,
            marker_color='#ef4444'
        ))
        fig_compare.update_layout(
            title="Top 10 Countries: 2010 vs 2025 Projections (Million Tonnes)",
            barmode='group',
            height=450
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    
    with col2:
        # Global totals
        total_2010 = projections['mismanaged_2010'].sum() / 1000000
        total_2025 = projections['mismanaged_2025'].sum() / 1000000
        
        fig_global = go.Figure()
        fig_global.add_trace(go.Bar(
            x=['2010', '2025 (Projected)'],
            y=[total_2010, total_2025],
            marker_color=['#3b82f6', '#ef4444'],
            text=[f'{total_2010:.1f}M', f'{total_2025:.1f}M'],
            textposition='auto'
        ))
        fig_global.update_layout(
            title="Global Mismanaged Plastic: 2010 vs 2025",
            yaxis_title="Million Tonnes",
            height=450
        )
        st.plotly_chart(fig_global, use_container_width=True)
    
    st.warning(f"""
    **Alarming Projection:** Global mismanaged plastic waste is projected to increase from 
    {total_2010:.1f} million tonnes in 2010 to {total_2025:.1f} million tonnes by 2025 — 
    a **{((total_2025-total_2010)/total_2010*100):.0f}% increase** in just 15 years.
    """)

# Tab 5: Research Findings
with tab5:
    st.header("Research Findings")
    
    st.markdown("""
    ### Key Insights from Plastic Waste Analysis
    
    This analysis uses data from Jambeck et al. (2015), a landmark study on plastic waste 
    entering the oceans from coastal populations.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 1. The Asia Problem
        
        East and Southeast Asia dominate global ocean plastic pollution:
        - **China**: 8.8 million tonnes of mismanaged plastic (2010)
        - **Indonesia**: 3.2 million tonnes
        - **Philippines**: 1.9 million tonnes
        - **Vietnam**: 1.8 million tonnes
        
        Combined, these four countries account for over **50%** of global 
        mismanaged plastic waste.
        
        **Why?** Large coastal populations combined with rapidly developing 
        economies that lack adequate waste management infrastructure.
        
        ---
        
        #### 2. Per Capita vs Total
        
        Different metrics tell different stories:
        - **Total waste**: Dominated by populous nations (China, Indonesia, India)
        - **Per capita**: Small island nations and developing countries lead
        
        Sri Lanka has the highest per capita rate (0.30 kg/person/day) despite 
        ranking lower in total waste.
        
        ---
        
        #### 3. Waste Management Gap
        
        The key factor isn't how much plastic is used, but how it's managed:
        - Developed nations: **0%** inadequately managed
        - Developing nations: Often **80-90%** inadequately managed
        
        Countries like North Korea, Bangladesh, and Myanmar have 85%+ 
        inadequate management rates.
        """)
    
    with col2:
        st.markdown("""
        #### 4. The 2025 Crisis
        
        Without intervention, mismanaged plastic will more than **double** by 2025:
        - 2010: ~32 million tonnes
        - 2025: ~69 million tonnes (projected)
        
        The biggest increases are projected in:
        - China (+9 million tonnes)
        - Indonesia (+4.2 million tonnes)
        - Philippines (+3.2 million tonnes)
        
        ---
        
        #### 5. Coastal Population Risk
        
        The study focuses on populations within 50km of coastlines because:
        - They generate waste most likely to reach the ocean
        - 2+ billion people live in these zones
        - Rapid urbanization is increasing coastal populations
        
        ---
        
        #### 6. Solutions Focus
        
        The data suggests priority interventions should focus on:
        1. **Waste infrastructure** in high-population Asian countries
        2. **Recycling programs** in small island nations
        3. **Reducing plastic use** in countries with poor management
        4. **International cooperation** for ocean cleanup
        
        **Key insight**: Reducing mismanaged waste by just 50% in the top 10 
        countries would cut global ocean plastic inputs by over 40%.
        """)
    
    st.markdown("""
    ---
    
    ### Data Definitions
    
    | Term | Definition |
    |------|------------|
    | **Coastal Population** | Population living within 50km of coastline |
    | **Mismanaged Waste** | Waste that is littered or inadequately disposed |
    | **Inadequately Disposed** | Disposed in dumps or open, uncontrolled landfills |
    | **Plastic Waste at Risk** | Plastic that could enter ocean via waterways, wind, or tides |
    
    ---
    
    ### Data Limitations
    
    - Data is from 2010 with projections to 2025
    - Estimates are based on coastal populations only
    - Actual ocean input depends on many factors (river systems, weather, etc.)
    - Some small nations may have incomplete data
    
    **Data Source:** [Jambeck et al. (2015) via Our World in Data](https://github.com/owid/owid-datasets/tree/master/datasets/Plastic%20Waste%20-%20Jambeck%20et%20al.%20(2015))
    """)

# Tab 6: Raw Data
with tab6:
    st.header("Raw Data Explorer")
    
    data_view = st.radio(
        "Select data view",
        ["Country Summary", "Regional Summary", "Full Dataset"],
        horizontal=True
    )
    
    if data_view == "Country Summary":
        st.dataframe(data["country_summary"], use_container_width=True, hide_index=True)
    elif data_view == "Regional Summary":
        st.dataframe(data["region_summary"], use_container_width=True, hide_index=True)
    else:
        st.dataframe(data["full"], use_container_width=True, hide_index=True)
    
    # Download button
    csv = data["full"].to_csv(index=False)
    st.download_button(
        label="Download Full Dataset (CSV)",
        data=csv,
        file_name="plastic_waste_jambeck_2015.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("""
### About This Data

This dashboard visualizes data from the landmark study by Jambeck et al. (2015) published in *Science*,
which quantified plastic waste streams from coastal populations worldwide.

**Key Definitions:**
- **Coastal population**: People living within 50km of coastline
- **Mismanaged waste**: Littered or inadequately disposed plastic
- **Inadequate disposal**: Dumps or open landfills where waste is not contained

**Data Source:** [Jambeck et al. (2015) via Our World in Data](https://github.com/owid/owid-datasets/tree/master/datasets/Plastic%20Waste%20-%20Jambeck%20et%20al.%20(2015))
""")

render_site_footer()
