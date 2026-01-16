"""
Female Labor Force Participation Dashboard
Analyzing 126 years of women's workforce participation across 42 countries (1890-2016)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.female_labor.database import FemaleLaborDatabase
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
    page_title="Female Labor Force Participation | Allan Ninal",
    page_icon="",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load female labor data from database."""
    with FemaleLaborDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        decade_summary = db.get_decade_summary()
        top_countries = db.get_top_countries(15)
        most_improved = db.get_most_improved(15)
        stats = db.get_stats()
    return (full_data, country_summary, region_summary, decade_summary,
            top_countries, most_improved, stats)


# Load data
(full_data, country_summary, region_summary, decade_summary,
 top_countries, most_improved, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Female Labor Force Participation", icon="👩‍💼", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Hero Header
render_hero_header(
    title="Female Labor Force Participation",
    subtitle="How has women's participation in the workforce evolved over more than a century?",
    data_badge=f"📅 Data: {stats['years'][0]}-{stats['years'][1]} | {stats['countries']} Countries | OECD & Historical Sources"
)

# Key insight banner
highest_country = top_countries.iloc[0] if len(top_countries) > 0 else None
most_improved_country = most_improved.iloc[0] if len(most_improved) > 0 else None

if highest_country is not None and most_improved_country is not None:
    render_shocking_fact(
        value=f"{highest_country['latest_rate']:.0f}%",
        description=f"From less than 20% in the early 1900s, female labor force participation has risen to over 50% in most developed nations. <b>{highest_country['country']}</b> leads today, while <b>{most_improved_country['country']}</b> saw the largest historical gain of <b>+{most_improved_country['rate_change']:.1f}</b> percentage points.",
        style="primary"
    )

st.markdown("---")

# Hero Stats using shared component
years_span = stats['years'][1] - stats['years'][0]
render_hero_stats([
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed"),
    HeroStat(f"{years_span}", f"Years of Data<br>Since {stats['years'][0]}", "secondary"),
    HeroStat(f"{stats['latest_avg_rate']}%", "Average Rate<br>Current participation", "success"),
    HeroStat(f"{highest_country['latest_rate']:.1f}%" if highest_country is not None else "N/A", f"{highest_country['country'] if highest_country is not None else ''}<br>Highest rate", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Historical Trends", "Country Rankings", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Historical Trends
with tab1:
    st.subheader("Female Labor Force Participation Over Time")

    # Country selection for time series
    available_countries = full_data['country'].unique().tolist()
    default_countries = ['United States', 'Sweden', 'Japan', 'Germany', 'OECD countries']
    default_selection = [c for c in default_countries if c in available_countries][:5]

    selected_countries = st.multiselect(
        "Select countries to compare:",
        options=available_countries,
        default=default_selection,
        key="historical_countries"
    )

    if selected_countries:
        filtered_data = full_data[full_data['country'].isin(selected_countries)]

        fig = px.line(
            filtered_data,
            x='year',
            y='participation_rate',
            color='country',
            labels={'year': 'Year', 'participation_rate': 'Participation Rate (%)', 'country': 'Country'},
        )

        fig.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        fig.update_traces(line_width=2.5)

        st.plotly_chart(fig, use_container_width=True)

    # Decade trends
    st.subheader("Average Participation by Decade")

    fig = px.bar(
        decade_summary,
        x='decade',
        y='avg_rate',
        color='avg_rate',
        color_continuous_scale='Viridis',
        labels={'decade': 'Decade', 'avg_rate': 'Average Rate (%)'},
        text='avg_rate'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Key observations
    st.markdown("### Key Historical Patterns")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Early 20th Century (1890-1940)**
        - Participation rates typically under 25%
        - Limited data availability (mainly US, UK)
        - Women primarily in domestic roles
        - Some wartime increases (WWI, WWII)
        """)

    with col2:
        st.markdown("""
        **Post-War Era to Present (1950-2016)**
        - Dramatic increase from 1960s onwards
        - Nordic countries lead the transformation
        - Average rates now exceed 50%
        - Convergence across developed nations
        """)

# Tab 2: Country Rankings
with tab2:
    st.subheader("Country Rankings by Participation Rate")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Highest Participation (Latest Data)")

        fig = px.bar(
            top_countries,
            x='latest_rate',
            y='country',
            orientation='h',
            color='latest_rate',
            color_continuous_scale='Greens',
            labels={'latest_rate': 'Participation Rate (%)', 'country': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Most Improved (Historical Change)")

        fig = px.bar(
            most_improved,
            x='rate_change',
            y='country',
            orientation='h',
            color='rate_change',
            color_continuous_scale='Purples',
            labels={'rate_change': 'Change (pp)', 'country': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Full country table
    st.subheader("Complete Country Summary")

    display_df = country_summary[['country', 'region', 'latest_year', 'latest_rate',
                                   'earliest_year', 'earliest_rate', 'rate_change', 'data_points']].copy()
    display_df.columns = ['Country', 'Region', 'Latest Year', 'Latest Rate (%)',
                          'Earliest Year', 'Earliest Rate (%)', 'Change (pp)', 'Data Points']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Regional Comparison")

    # Bar chart of regional averages
    fig = px.bar(
        region_summary,
        x='region',
        y='avg_rate',
        color='avg_rate',
        color_continuous_scale='RdYlGn',
        labels={'region': 'Region', 'avg_rate': 'Average Rate (%)'},
        text='avg_rate'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional details
    st.subheader("Regional Statistics")

    col1, col2 = st.columns(2)

    with col1:
        # Box plot by region
        fig = px.box(
            full_data[full_data['region'] != 'OECD Aggregate'],
            x='region',
            y='participation_rate',
            color='region',
            labels={'region': 'Region', 'participation_rate': 'Participation Rate (%)'},
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Regional Summary Table")

        display_region = region_summary.copy()
        display_region.columns = ['Region', 'Countries', 'Avg Rate (%)', 'Min (%)', 'Max (%)', 'Data Points']

        st.dataframe(display_region, use_container_width=True, hide_index=True)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📈", "Study 1: A Century of Growth",
            "Female labor force participation has <b>more than doubled</b> globally since the early 20th century, from under 20% to over 50% in most developed nations.",
            "This transformation represents one of the most significant social and economic shifts of the modern era, reshaping family structures and economies worldwide."),
        ResearchStudy("🏔️", "Study 2: Nordic Leadership",
            "Nordic countries (Iceland, Sweden, Norway) consistently lead with rates <b>above 60%</b>, pioneering policies that support working mothers.",
            "Strong parental leave, subsidized childcare, and flexible work arrangements create models other nations seek to emulate."),
        ResearchStudy("🚀", "Study 3: The Great Acceleration",
            "The most dramatic increases occurred between <b>1960-1990</b> in developed economies, with some countries seeing 30+ percentage point gains in a single generation.",
            "This period coincided with second-wave feminism, contraception access, and changing social attitudes about women's roles."),
        ResearchStudy("🇺🇸", "Study 4: The American Transformation",
            "The US saw participation rise from <b>18% (1890)</b> to <b>56% (2016)</b> - a 38 percentage point gain over 126 years.",
            "The longest continuous dataset reveals how wars, recessions, and social movements shaped women's workforce entry."),
        ResearchStudy("⚖️", "Study 5: The Plateau Effect",
            "The OECD average has <b>stabilized around 52%</b> since 2000, suggesting structural barriers may limit further gains without policy intervention.",
            "Understanding what causes this plateau is critical for designing effective policies to close remaining gaps."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Primary data from OECD.stat for most recent observations",
        "Historical data from Long (1958) and Heckman & Killingsworth (1986)",
        "Participation rate = economically active female population / total female population (15+)",
        "Some pre-1960 data based on population 14+"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Data availability varies significantly by country",
        "Definition of 'labor force participation' has evolved over time",
        "Informal and unpaid work not captured",
        "Part-time vs full-time not distinguished"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_country = st.selectbox(
        "Select a country:",
        options=sorted(full_data['country'].unique()),
        index=sorted(full_data['country'].unique()).index('United States') if 'United States' in full_data['country'].unique() else 0
    )

    country_data = full_data[full_data['country'] == selected_country].sort_values('year')
    country_info = country_summary[country_summary['country'] == selected_country]

    if len(country_data) > 0 and len(country_info) > 0:
        info = country_info.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Latest Rate", f"{info['latest_rate']:.1f}%", f"({info['latest_year']})")

        with col2:
            st.metric("Earliest Rate", f"{info['earliest_rate']:.1f}%", f"({info['earliest_year']})")

        with col3:
            change = info['rate_change']
            st.metric("Total Change", f"{change:+.1f} pp" if change else "N/A")

        with col4:
            st.metric("Data Points", info['data_points'])

        # Time series
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data['participation_rate'],
            mode='lines+markers',
            name=selected_country,
            line=dict(color='#ec4899', width=3),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title=f"Female Labor Force Participation in {selected_country}",
            xaxis_title="Year",
            yaxis_title="Participation Rate (%)",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.markdown("#### Historical Data")
        display_country = country_data[['year', 'participation_rate', 'decade']].copy()
        display_country.columns = ['Year', 'Participation Rate (%)', 'Decade']
        display_country['Participation Rate (%)'] = display_country['Participation Rate (%)'].round(2)

        st.dataframe(display_country, use_container_width=True, hide_index=True)

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Country Summary", "Region Summary", "Decade Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "female_labor_full.csv", "text/csv")

    elif data_view == "Country Summary":
        st.dataframe(country_summary, use_container_width=True, hide_index=True)
        csv = country_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "female_labor_countries.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "female_labor_regions.csv", "text/csv")

    else:
        st.dataframe(decade_summary, use_container_width=True, hide_index=True)
        csv = decade_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "female_labor_decades.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Sweden", "United States"),
        ("Japan", "Germany"),
        ("Iceland", "Norway"),
    ],
    data=country_summary,
    name_column="country",
    value_column="latest_rate",
    title="Test Your Knowledge",
    prompt="🎯 Can you guess which country has higher female labor force participation?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """labor_participation ──┐
• country (PK)        │    country_summary
• year (PK)           ├───▶ • country (PK)
• participation_rate  │    • region
• region              │    • latest_rate
• decade              │    • earliest_rate
                      │    • rate_change
                      │
region_summary ───────┤    decade_summary
• region (PK)         └───▶ • decade (PK)
• countries                 • avg_rate
• avg_rate                  • countries_with_data"""

SAMPLE_QUERIES = """-- Countries with highest participation
SELECT country, region, latest_rate, rate_change
FROM country_summary
ORDER BY latest_rate DESC
LIMIT 10;

-- Historical US progression
SELECT year, participation_rate, decade
FROM labor_participation
WHERE country = 'United States'
ORDER BY year;

-- Regional comparison
SELECT region, countries, avg_rate, max_rate
FROM region_summary
ORDER BY avg_rate DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["126-year historical time series", "42-country comparison", "Regional aggregation", "Decade-level trend analysis"]
)

# Footer
render_data_footer(
    data_sources=["OECD.stat", "Long (1958)", "Heckman & Killingsworth (1986)"],
    time_period=f"{stats['years'][0]} - {stats['years'][1]}\n{stats['countries']} countries",
    data_points=f"{stats['total_records']} records",
    credits={"Data compilation": "Our World in Data", "Historical research": "OECD Employment Database"},
    dataset_url="http://stats.oecd.org/"
)

# Site footer
render_site_footer()
