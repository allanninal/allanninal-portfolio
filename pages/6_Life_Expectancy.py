"""Life Expectancy Analysis Dashboard using OECD data."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.life_expectancy import LifeExpectancyDatabase
from components.dashboard import render_site_header, render_site_footer


st.set_page_config(
    page_title="Life Expectancy Analysis",
    page_icon="🏥",
    layout="wide"
)


@st.cache_resource
def get_database():
    """Get database connection."""
    db = LifeExpectancyDatabase().connect()
    return db


@st.cache_data
def load_data():
    """Load all data from database."""
    db = get_database()
    return {
        "full": db.get_full_data(),
        "country_summary": db.get_country_summary(),
        "region_summary": db.get_region_summary(),
        "year_summary": db.get_year_summary(),
        "stats": db.get_stats()
    }


# Load data
data = load_data()
db = get_database()

render_site_header()

# Header
st.title("🏥 Life Expectancy Analysis")
st.markdown("*Exploring 55 years of global health progress through OECD life expectancy data*")

# Hero stats
col1, col2, col3, col4 = st.columns(4)

latest_summary = data["country_summary"]
top_country = latest_summary.iloc[0] if len(latest_summary) > 0 else None
year_data = data["year_summary"]

with col1:
    if top_country is not None:
        st.metric(
            "Highest Life Expectancy (2015)",
            f"{top_country['entity']}",
            f"{top_country['life_expectancy']:.1f} years"
        )

with col2:
    if len(year_data) > 0:
        latest_global = year_data[year_data['year'] == 2015]['global_avg_life_expectancy'].values
        if len(latest_global) > 0:
            st.metric(
                "Global Average (2015)",
                f"{latest_global[0]:.1f} years",
                None
            )

with col3:
    # Calculate improvement
    if len(year_data) > 0:
        start_avg = year_data[year_data['year'] == 1960]['global_avg_life_expectancy'].values
        end_avg = year_data[year_data['year'] == 2015]['global_avg_life_expectancy'].values
        if len(start_avg) > 0 and len(end_avg) > 0:
            improvement = end_avg[0] - start_avg[0]
            st.metric(
                "Years Gained (1960-2015)",
                f"+{improvement:.1f} years",
                None
            )

with col4:
    st.metric(
        "Countries Analyzed",
        data["stats"]["entities"],
        f"{data['stats']['year_range'][1] - data['stats']['year_range'][0]} years"
    )

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Trends", "🌍 Regional Analysis", "🏆 Rankings",
    "🔍 Country Explorer", "📚 Research Findings", "📊 Raw Data"
])

# Tab 1: Trends
with tab1:
    st.header("Global Life Expectancy Trends")
    
    # Global trend line
    fig_trend = px.line(
        year_data,
        x='year',
        y='global_avg_life_expectancy',
        title="Global Average Life Expectancy (1960-2015)",
        labels={'year': 'Year', 'global_avg_life_expectancy': 'Life Expectancy (years)'}
    )
    fig_trend.update_traces(line=dict(width=3, color='#1f77b4'))
    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Min/Max band
    fig_band = go.Figure()
    fig_band.add_trace(go.Scatter(
        x=year_data['year'],
        y=year_data['max_life_expectancy'],
        mode='lines',
        name='Maximum',
        line=dict(color='green')
    ))
    fig_band.add_trace(go.Scatter(
        x=year_data['year'],
        y=year_data['min_life_expectancy'],
        mode='lines',
        name='Minimum',
        line=dict(color='red'),
        fill='tonexty',
        fillcolor='rgba(128, 128, 128, 0.2)'
    ))
    fig_band.add_trace(go.Scatter(
        x=year_data['year'],
        y=year_data['global_avg_life_expectancy'],
        mode='lines',
        name='Global Average',
        line=dict(color='blue', width=2)
    ))
    fig_band.update_layout(
        title="Life Expectancy Range Across Countries",
        xaxis_title="Year",
        yaxis_title="Life Expectancy (years)",
        height=400
    )
    st.plotly_chart(fig_band, use_container_width=True)
    
    # Major economies comparison
    st.subheader("Major Economies Comparison")
    major_economies = ['United States', 'Japan', 'Germany', 'United Kingdom', 'France', 'China', 'India', 'Brazil']
    major_data = data["full"][data["full"]['entity'].isin(major_economies)]
    
    fig_major = px.line(
        major_data,
        x='year',
        y='life_expectancy',
        color='entity',
        title="Life Expectancy: Major Economies (1960-2015)",
        labels={'year': 'Year', 'life_expectancy': 'Life Expectancy (years)', 'entity': 'Country'}
    )
    fig_major.update_layout(height=500)
    st.plotly_chart(fig_major, use_container_width=True)

# Tab 2: Regional Analysis
with tab2:
    st.header("Regional Analysis")
    
    region_summary = data["region_summary"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of regional averages
        fig_region_bar = px.bar(
            region_summary,
            x='region',
            y='avg_life_expectancy',
            color='avg_life_expectancy',
            color_continuous_scale='viridis',
            title="Average Life Expectancy by Region (2015)",
            labels={'region': 'Region', 'avg_life_expectancy': 'Avg Life Expectancy (years)'}
        )
        fig_region_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_region_bar, use_container_width=True)
    
    with col2:
        # Regional data table
        st.dataframe(
            region_summary.round(2),
            use_container_width=True,
            hide_index=True
        )
    
    # Regional trends over time
    st.subheader("Regional Trends Over Time")
    full_data = data["full"]
    regional_trend = full_data.groupby(['year', 'region'])['life_expectancy'].mean().reset_index()
    
    fig_regional_trend = px.line(
        regional_trend,
        x='year',
        y='life_expectancy',
        color='region',
        title="Life Expectancy by Region (1960-2015)",
        labels={'year': 'Year', 'life_expectancy': 'Life Expectancy (years)', 'region': 'Region'}
    )
    fig_regional_trend.update_layout(height=500)
    st.plotly_chart(fig_regional_trend, use_container_width=True)

# Tab 3: Rankings
with tab3:
    st.header("Country Rankings")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_year = st.selectbox(
            "Select Year",
            options=list(range(2015, 1959, -1)),
            index=0
        )
        top_n = st.slider("Number of countries", 10, 44, 20)
    
    # Get top countries for selected year
    top_countries = db.get_top_countries(selected_year, top_n)
    
    with col2:
        fig_ranking = px.bar(
            top_countries.sort_values('life_expectancy'),
            x='life_expectancy',
            y='entity',
            color='region',
            orientation='h',
            title=f"Top {top_n} Countries by Life Expectancy ({selected_year})",
            labels={'entity': 'Country', 'life_expectancy': 'Life Expectancy (years)', 'region': 'Region'}
        )
        fig_ranking.update_layout(height=max(400, top_n * 25))
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    # Improvement rankings
    st.subheader("Biggest Improvements (1960-2015)")
    improvements = db.get_improvement_rates(1960, 2015)
    if len(improvements) > 0:
        improvements_sorted = improvements.sort_values('years_gained', ascending=False).head(15)
        
        fig_improvement = px.bar(
            improvements_sorted,
            x='years_gained',
            y='entity',
            color='region',
            orientation='h',
            title="Countries with Greatest Life Expectancy Gains (1960-2015)",
            labels={'entity': 'Country', 'years_gained': 'Years Gained', 'region': 'Region'}
        )
        fig_improvement.update_layout(height=500)
        st.plotly_chart(fig_improvement, use_container_width=True)

# Tab 4: Country Explorer
with tab4:
    st.header("Country Explorer")
    
    countries = sorted(data["full"]['entity'].unique())
    selected_country = st.selectbox("Select a country", countries, index=countries.index('Japan') if 'Japan' in countries else 0)
    
    # Get country history
    country_history = db.get_country_history(selected_country)
    country_info = data["country_summary"][data["country_summary"]['entity'] == selected_country]
    
    if len(country_info) > 0:
        info = country_info.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Region", info['region'])
        with col2:
            st.metric("Life Expectancy (2015)", f"{info['life_expectancy']:.1f} years")
        with col3:
            st.metric("Data Range", f"{int(info['first_year'])}-{int(info['latest_year'])}")
        with col4:
            if pd.notna(info['change_since_1960']):
                st.metric("Change Since Start", f"+{info['change_since_1960']:.1f} years")
    
    # Country trend
    fig_country = px.line(
        country_history,
        x='year',
        y='life_expectancy',
        title=f"Life Expectancy in {selected_country}",
        labels={'year': 'Year', 'life_expectancy': 'Life Expectancy (years)'}
    )
    fig_country.update_traces(line=dict(width=3))
    fig_country.update_layout(height=400)
    st.plotly_chart(fig_country, use_container_width=True)
    
    # Compare with other countries
    st.subheader("Compare with Other Countries")
    compare_countries = st.multiselect(
        "Select countries to compare",
        [c for c in countries if c != selected_country],
        default=['United States', 'Germany'] if 'United States' in countries and 'Germany' in countries else []
    )
    
    if compare_countries:
        compare_data = data["full"][data["full"]['entity'].isin([selected_country] + compare_countries)]
        
        fig_compare = px.line(
            compare_data,
            x='year',
            y='life_expectancy',
            color='entity',
            title=f"Life Expectancy Comparison",
            labels={'year': 'Year', 'life_expectancy': 'Life Expectancy (years)', 'entity': 'Country'}
        )
        fig_compare.update_layout(height=400)
        st.plotly_chart(fig_compare, use_container_width=True)

# Tab 5: Research Findings
with tab5:
    st.header("Research Findings")

    st.markdown("""
    ### Key Insights from Life Expectancy Data (1960-2015)

    This analysis of OECD life expectancy data reveals fascinating patterns in global health progress
    over 55 years. Here are the major findings:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 1. The Global Health Revolution

        Life expectancy increased dramatically worldwide:
        - **Average gain**: ~10 years across all countries
        - **Fastest improvements**: East Asian nations
        - **Most consistent**: Nordic countries

        The post-WWII era saw unprecedented health improvements driven by:
        - Antibiotics and vaccines
        - Improved sanitation
        - Better nutrition
        - Advances in medical care

        ---

        #### 2. Regional Disparities Persist

        Despite global progress, significant gaps remain:
        - **Top performers**: Japan, Switzerland, Iceland (82+ years)
        - **Struggling regions**: Sub-Saharan Africa, parts of Eastern Europe
        - **Gap between best and worst**: ~20+ years

        Factors contributing to disparities:
        - Healthcare access and quality
        - Economic development
        - Public health infrastructure
        - Social and political stability
        """)

    with col2:
        st.markdown("""
        #### 3. Remarkable Success Stories

        Some countries achieved extraordinary gains:
        - **South Korea**: 52 → 82 years (+30 years)
        - **Turkey**: 48 → 76 years (+28 years)
        - **Chile**: 57 → 80 years (+23 years)
        - **China**: 44 → 76 years (+32 years)

        Common factors in rapid improvement:
        - Economic development
        - Universal healthcare adoption
        - Education improvements
        - Reduced infant mortality

        ---

        #### 4. Concerning Reversals

        Not all trends were positive:
        - **Russia**: Declined in 1990s (69 → 64 years)
        - **South Africa**: HIV/AIDS crisis (60 → 52 years in 2000s)
        - **Baltic states**: Post-Soviet transition challenges

        These reversals highlight that progress is not guaranteed
        and can be undone by:
        - Health crises (epidemics)
        - Economic collapse
        - Political instability
        - Social disruption
        """)

    st.markdown("""
    ---

    ### 5. The Japan Phenomenon

    Japan consistently leads in life expectancy, reaching 83.8 years by 2015. Key factors include:

    | Factor | Description |
    |--------|-------------|
    | **Diet** | Traditional Japanese diet rich in fish, vegetables, and fermented foods |
    | **Healthcare** | Universal healthcare since 1961 with high accessibility |
    | **Social Cohesion** | Strong community bonds and social support systems |
    | **Active Lifestyle** | Walking culture, lower obesity rates |
    | **Preventive Care** | Regular health checkups and early intervention |

    ---

    ### 6. The US Paradox

    Despite being the world's largest economy, the United States lags behind other developed nations:
    - **2015 ranking**: Below most Western European countries
    - **Life expectancy**: 78.7 years (vs 83.8 in Japan)
    - **Healthcare spending**: Highest in the world per capita

    Contributing factors:
    - Healthcare access inequality
    - Higher rates of obesity and chronic disease
    - Drug overdose epidemic (recent years)
    - Gun violence
    - Socioeconomic disparities

    ---

    ### Data Limitations

    - Data covers 44 countries (primarily OECD members and key partners)
    - Some countries have incomplete historical records
    - Life expectancy is a summary measure that doesn't capture health quality
    - Regional aggregations may mask within-country inequalities
    """)

# Tab 6: Raw Data
with tab6:
    st.header("Raw Data Explorer")
    
    data_view = st.radio(
        "Select data view",
        ["Country Summary", "Regional Summary", "Year Summary", "Full Dataset"],
        horizontal=True
    )
    
    if data_view == "Country Summary":
        st.dataframe(data["country_summary"], use_container_width=True, hide_index=True)
    elif data_view == "Regional Summary":
        st.dataframe(data["region_summary"], use_container_width=True, hide_index=True)
    elif data_view == "Year Summary":
        st.dataframe(data["year_summary"], use_container_width=True, hide_index=True)
    else:
        st.dataframe(data["full"], use_container_width=True, hide_index=True)
    
    # Download button
    csv = data["full"].to_csv(index=False)
    st.download_button(
        label="Download Full Dataset (CSV)",
        data=csv,
        file_name="life_expectancy_oecd.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("""
### About This Data

This dashboard visualizes life expectancy data from the OECD, covering 44 countries from 1960 to 2015.
Life expectancy at birth indicates the number of years a newborn infant would live if prevailing patterns
of mortality at the time of birth were to stay the same throughout their life.

**Key Findings:**
- Global average life expectancy increased by approximately 10 years between 1960 and 2015
- Japan consistently leads with the highest life expectancy among major economies
- Developing nations like South Korea and China showed the most dramatic improvements
- Some countries (notably Russia and South Africa) experienced periods of declining life expectancy

**Data Source:** [OECD via Our World in Data](https://github.com/owid/owid-datasets/tree/master/datasets/Life%20expectancy%20-%20OECD)
""")

render_site_footer()
