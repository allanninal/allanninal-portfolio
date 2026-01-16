"""
Working Hours Dashboard
Analyzing 130 years of work hours across 14 countries (1870-2000)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.working_hours.database import WorkingHoursDatabase
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
    page_title="Working Hours | Allan Ninal",
    page_icon="⏰",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load working hours data from database."""
    with WorkingHoursDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        era_summary = db.get_era_summary()
        shortest_week = db.get_shortest_week(14)
        most_improved = db.get_most_improved(14)
        most_vacation = db.get_most_vacation(14)
        stats = db.get_stats()
    return (full_data, country_summary, region_summary, era_summary,
            shortest_week, most_improved, most_vacation, stats)


# Load data
(full_data, country_summary, region_summary, era_summary,
 shortest_week, most_improved, most_vacation, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Working Hours", icon="⏰", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Hero Header
render_hero_header(
    title="Working Hours Through History",
    subtitle="How the work week transformed over 130 years across the industrialized world.",
    data_badge=f"📅 Data: {stats['years'][0]}-{stats['years'][1]} | {stats['countries']} Countries | Huberman & Minns (2007)"
)

# Key insight banner
shortest_country = shortest_week.iloc[0] if len(shortest_week) > 0 else None
most_improved_country = most_improved.iloc[0] if len(most_improved) > 0 else None

if shortest_country is not None and most_improved_country is not None:
    render_shocking_fact(
        value=f"-{abs(most_improved_country['weekly_change']):.0f}h",
        description=f"The average work week dropped dramatically from <b>60+ hours in 1870</b> to under <b>40 hours by 2000</b>. <b>{most_improved_country['country']}</b> saw the largest reduction of <b>{abs(most_improved_country['weekly_change']):.1f} hours/week</b>, while <b>{shortest_country['country']}</b> now has the shortest at <b>{shortest_country['latest_weekly_hours']:.1f}h</b>.",
        style="primary"
    )

st.markdown("---")

# Hero Stats using shared component
years_span = stats['years'][1] - stats['years'][0]
render_hero_stats([
    HeroStat(f"{stats['latest_avg_weekly']}h", "Average Week<br>In 2000"),
    HeroStat(f"{shortest_country['latest_weekly_hours']:.1f}h" if shortest_country is not None else "N/A", f"{shortest_country['country'] if shortest_country is not None else ''}<br>Shortest week", "success"),
    HeroStat(f"{years_span}", "Years<br>Of data tracked", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Historical Trends", "Country Rankings", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Historical Trends
with tab1:
    st.subheader("Weekly Working Hours Over Time")

    # Country selection
    available_countries = full_data['country'].unique().tolist()
    default_countries = ['United States', 'United Kingdom', 'Germany', 'France', 'Netherlands']
    default_selection = [c for c in default_countries if c in available_countries][:5]

    selected_countries = st.multiselect(
        "Select countries to compare:",
        options=available_countries,
        default=default_selection,
        key="historical_countries"
    )

    if selected_countries:
        filtered_data = full_data[full_data['country'].isin(selected_countries)]
        filtered_data = filtered_data.dropna(subset=['weekly_hours'])

        fig = px.line(
            filtered_data,
            x='year',
            y='weekly_hours',
            color='country',
            labels={'year': 'Year', 'weekly_hours': 'Weekly Hours', 'country': 'Country'},
            markers=True
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

        # Add reference lines
        fig.add_hline(y=40, line_dash="dash", line_color="green",
                      annotation_text="40-hour standard")

        fig.update_traces(line_width=2.5)

        st.plotly_chart(fig, use_container_width=True)

    # Era trends
    st.subheader("Average Hours by Era")

    era_display = era_summary.dropna(subset=['avg_weekly'])

    fig = px.bar(
        era_display,
        x='era',
        y='avg_weekly',
        color='avg_weekly',
        color_continuous_scale='RdYlGn_r',
        labels={'era': 'Era', 'avg_weekly': 'Average Weekly Hours'},
        text='avg_weekly'
    )

    fig.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
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
        **Industrial Era (1870-1913)**
        - Work weeks of 60-70 hours common
        - 6-day work weeks standard
        - Limited vacation (4-18 days/year)
        - Labor movements begin organizing
        """)

    with col2:
        st.markdown("""
        **Modern Era (1950-2000)**
        - 40-hour week becomes standard
        - 5-day work weeks emerge
        - Vacation time expands (20-40 days)
        - Work-life balance prioritized
        """)

# Tab 2: Country Rankings
with tab2:
    st.subheader("Country Rankings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Shortest Work Week (2000)")

        fig = px.bar(
            shortest_week.dropna(subset=['latest_weekly_hours']),
            x='latest_weekly_hours',
            y='country',
            orientation='h',
            color='latest_weekly_hours',
            color_continuous_scale='Greens_r',
            labels={'latest_weekly_hours': 'Weekly Hours', 'country': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Largest Reduction (1870-2000)")

        improved_display = most_improved.dropna(subset=['weekly_change']).copy()
        improved_display['reduction'] = -improved_display['weekly_change']

        fig = px.bar(
            improved_display,
            x='reduction',
            y='country',
            orientation='h',
            color='reduction',
            color_continuous_scale='Purples',
            labels={'reduction': 'Hours Reduced', 'country': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Vacation days ranking
    st.subheader("Vacation Days (Latest Available)")

    vacation_display = most_vacation.dropna(subset=['latest_vacation_days'])

    fig = px.bar(
        vacation_display,
        x='latest_vacation_days',
        y='country',
        orientation='h',
        color='latest_vacation_days',
        color_continuous_scale='Blues',
        labels={'latest_vacation_days': 'Days', 'country': ''}
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Full country table
    st.subheader("Complete Country Summary")

    display_df = country_summary[['country', 'region', 'latest_year', 'latest_weekly_hours',
                                   'earliest_weekly_hours', 'weekly_change', 'latest_vacation_days']].copy()
    display_df.columns = ['Country', 'Region', 'Latest Year', 'Latest Hours',
                          'Earliest Hours', 'Change', 'Vacation Days']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Regional Comparison")

    # Bar chart of regional averages
    fig = px.bar(
        region_summary.dropna(subset=['avg_weekly']),
        x='region',
        y='avg_weekly',
        color='avg_weekly',
        color_continuous_scale='RdYlGn_r',
        labels={'region': 'Region', 'avg_weekly': 'Average Weekly Hours'},
        text='avg_weekly'
    )

    fig.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Hours Distribution by Region")

        fig = px.box(
            full_data.dropna(subset=['weekly_hours']),
            x='region',
            y='weekly_hours',
            color='region',
            labels={'region': 'Region', 'weekly_hours': 'Weekly Hours'},
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
        display_region.columns = ['Region', 'Countries', 'Avg Weekly', 'Min', 'Max', 'Avg Annual', 'Avg Vacation']

        st.dataframe(display_region, use_container_width=True, hide_index=True)

        st.markdown("""
        **Key Regional Patterns:**
        - Nordic countries lead in work-life balance
        - Western Europe shows consistent reductions
        - North America maintains longer hours
        - Southern Europe has mixed patterns
        """)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📉", "Study 1: The Great Reduction",
            "Working hours fell from an average of <b>65 hours/week in 1870</b> to <b>38 hours in 2000</b> - a <b>40% reduction</b> over 130 years.",
            "The transformation of work represents one of the most significant improvements in quality of life, driven by labor movements, productivity gains, and policy changes."),
        ResearchStudy("🇳🇱", "Study 2: The Dutch Model",
            "The Netherlands achieved the <b>shortest work week at 33.8 hours</b>, pioneering part-time work arrangements and work-life balance policies.",
            "The Dutch approach demonstrates that shorter hours can coexist with economic prosperity and high productivity."),
        ResearchStudy("🏖️", "Study 3: The Vacation Revolution",
            "Vacation days increased from <b>4-18 days in 1870</b> to <b>20-42 days by 2000</b>. Germany leads with <b>42.5 days</b> of vacation and holidays.",
            "Mandatory vacation laws in Europe created a significant quality-of-life gap compared to countries without such requirements."),
        ResearchStudy("🇺🇸", "Study 4: The American Exception",
            "The United States maintains <b>longer work hours (40.2h)</b> and <b>fewer vacation days (20)</b> compared to European peers, despite higher productivity.",
            "Cultural and policy differences explain why Americans work approximately 300 more hours per year than Germans."),
        ResearchStudy("⚡", "Study 5: Productivity Paradox",
            "Despite working <b>40% fewer hours</b>, modern workers produce far more output than their 1870 counterparts due to technological advancement.",
            "The decoupling of hours from output suggests further reductions may be possible without economic harm."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Data from full-time production workers (male and female) in non-agricultural activities",
        "Primary sources: ILO statistics, national labor surveys, historical archives",
        "Weekly hours derived from employer records and labor force surveys",
        "Vacation data includes paid holidays and statutory leave"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Data limited to 14 industrialized nations",
        "Self-employment and informal work not fully captured",
        "Definition of 'full-time' varies across countries and eras",
        "Pre-1950 data relies on historical estimates"
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
            st.metric("Latest Weekly Hours",
                      f"{info['latest_weekly_hours']:.1f}h" if pd.notna(info['latest_weekly_hours']) else "N/A",
                      f"({info['latest_year']})")

        with col2:
            st.metric("Earliest Weekly Hours",
                      f"{info['earliest_weekly_hours']:.1f}h" if pd.notna(info['earliest_weekly_hours']) else "N/A",
                      f"({info['earliest_year']})")

        with col3:
            change = info['weekly_change']
            st.metric("Total Change", f"{change:+.1f}h" if pd.notna(change) else "N/A")

        with col4:
            st.metric("Vacation Days",
                      f"{int(info['latest_vacation_days'])}" if pd.notna(info['latest_vacation_days']) else "N/A")

        # Time series
        fig = go.Figure()

        # Weekly hours
        weekly_data = country_data.dropna(subset=['weekly_hours'])
        fig.add_trace(go.Scatter(
            x=weekly_data['year'],
            y=weekly_data['weekly_hours'],
            mode='lines+markers',
            name='Weekly Hours',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))

        fig.add_hline(y=40, line_dash="dash", line_color="green",
                      annotation_text="40-hour standard")

        fig.update_layout(
            title=f"Working Hours in {selected_country}",
            xaxis_title="Year",
            yaxis_title="Weekly Hours",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Vacation days over time
        vacation_data = country_data.dropna(subset=['vacation_days'])
        if len(vacation_data) > 1:
            st.subheader("Vacation Days Over Time")

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=vacation_data['year'],
                y=vacation_data['vacation_days'],
                marker_color='#22c55e'
            ))

            fig2.update_layout(
                xaxis_title="Year",
                yaxis_title="Vacation Days",
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig2, use_container_width=True)

        # Historical interpretation
        if pd.notna(info['weekly_change']) and info['weekly_change'] < -20:
            st.success(f"**Major Transformation:** {selected_country} reduced working hours by {abs(info['weekly_change']):.1f} hours per week over 130 years.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Country Summary", "Region Summary", "Era Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "working_hours_full.csv", "text/csv")

    elif data_view == "Country Summary":
        st.dataframe(country_summary, use_container_width=True, hide_index=True)
        csv = country_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "working_hours_countries.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "working_hours_regions.csv", "text/csv")

    else:
        st.dataframe(era_summary, use_container_width=True, hide_index=True)
        csv = era_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "working_hours_eras.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Netherlands", "United States"),
        ("Germany", "United Kingdom"),
        ("France", "Canada"),
    ],
    data=country_summary,
    name_column="country",
    value_column="latest_weekly_hours",
    title="Test Your Work Hours Knowledge",
    prompt="🎯 Can you guess which country has SHORTER working hours?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """working_hours ────────┐
• country (PK)        │    country_summary
• year (PK)           ├───▶ • country (PK)
• weekly_hours        │    • region
• annual_hours        │    • latest_weekly_hours
• vacation_days       │    • weekly_change
• era                 │    • latest_vacation_days
                      │
region_summary ───────┤    era_summary
• region (PK)         └───▶ • era (PK)
• countries                 • avg_weekly
• avg_weekly                • avg_vacation"""

SAMPLE_QUERIES = """-- Countries with shortest work weeks
SELECT country, region, latest_weekly_hours, weekly_change
FROM country_summary
ORDER BY latest_weekly_hours ASC
LIMIT 5;

-- Hours reduction over time
SELECT year, AVG(weekly_hours) as avg_hours
FROM working_hours
GROUP BY year
ORDER BY year;

-- Vacation days comparison
SELECT country, latest_vacation_days, vacation_change
FROM country_summary
WHERE latest_vacation_days IS NOT NULL
ORDER BY latest_vacation_days DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["130-year historical time series", "14-country comparison", "Era-based trend analysis", "Vacation days tracking"]
)

# Footer
render_data_footer(
    data_sources=["Huberman & Minns (2007)", "ILO Statistics", "OECD Employment Database"],
    time_period=f"{stats['years'][0]} - {stats['years'][1]}\n{stats['countries']} industrialized nations",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "Huberman & Minns", "Compilation": "Our World in Data"},
    dataset_url="http://www.sciencedirect.com/science/article/pii/S0014498307000058"
)

# Site footer
render_site_footer()
