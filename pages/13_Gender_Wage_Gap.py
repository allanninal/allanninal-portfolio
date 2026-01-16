"""
Gender Wage Gap Dashboard
Analyzing 46 years of pay inequality across 38 OECD countries (1970-2016)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.gender_wage_gap.database import GenderWageGapDatabase
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
    page_title="Gender Wage Gap | Allan Ninal",
    page_icon="",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load gender wage gap data from database."""
    with GenderWageGapDatabase() as db:
        full_data = db.get_full_data()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        decade_summary = db.get_decade_summary()
        lowest_gap = db.get_lowest_gap(15)
        highest_gap = db.get_highest_gap(15)
        most_improved = db.get_most_improved(15)
        stats = db.get_stats()
    return (full_data, country_summary, region_summary, decade_summary,
            lowest_gap, highest_gap, most_improved, stats)


# Load data
(full_data, country_summary, region_summary, decade_summary,
 lowest_gap, highest_gap, most_improved, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Gender Wage Gap", icon="💰", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Hero Header
render_hero_header(
    title="Gender Wage Gap",
    subtitle="The gender wage gap measures how much less women earn compared to men.",
    data_badge=f"📅 Data: {stats['years'][0]}-{stats['years'][1]} | {stats['countries']} Countries | OECD"
)

# Definition box
st.info("""
**How is the wage gap measured?** The OECD gender wage gap is the difference between median earnings
of men and women, expressed as a percentage of men's median earnings. A gap of 15% means women earn
15% less than men. Data refers to full-time employees and self-employed.
""")

# Key insight banner
worst_country = highest_gap.iloc[0] if len(highest_gap) > 0 else None
best_country = lowest_gap.iloc[0] if len(lowest_gap) > 0 else None

if worst_country is not None and best_country is not None:
    render_shocking_fact(
        value=f"{stats['latest_avg_gap']}%",
        description=f"While progress has been made, significant disparities remain. <b>{best_country['country']}</b> leads with just a <b>{best_country['latest_gap']:.1f}%</b> gap, while <b>{worst_country['country']}</b> has the highest at <b>{worst_country['latest_gap']:.1f}%</b>.",
        style="danger"
    )

st.markdown("---")

# Hero Stats using shared component
years_span = stats['years'][1] - stats['years'][0]
render_hero_stats([
    HeroStat(f"{stats['latest_avg_gap']}%", "Average Gap<br>OECD countries"),
    HeroStat(f"{best_country['latest_gap']:.1f}%" if best_country is not None else "N/A", f"{best_country['country'] if best_country is not None else ''}<br>Most equal", "success"),
    HeroStat(f"{worst_country['latest_gap']:.1f}%" if worst_country is not None else "N/A", f"{worst_country['country'] if worst_country is not None else ''}<br>Largest gap", "danger"),
    HeroStat(f"{years_span}", "Years<br>Of data tracked", "secondary"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Historical Trends", "Country Rankings", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Historical Trends
with tab1:
    st.subheader("Gender Wage Gap Over Time")

    # Country selection
    available_countries = full_data['country'].unique().tolist()
    default_countries = ['United States', 'United Kingdom', 'Germany', 'Japan', 'Sweden']
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
            y='wage_gap',
            color='country',
            labels={'year': 'Year', 'wage_gap': 'Wage Gap (%)', 'country': 'Country'},
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

        # Add reference line at 0
        fig.add_hline(y=0, line_dash="dash", line_color="green",
                      annotation_text="Equal pay")

        fig.update_traces(line_width=2.5)

        st.plotly_chart(fig, use_container_width=True)

    # Decade trends
    st.subheader("Average Gap by Decade")

    fig = px.bar(
        decade_summary,
        x='decade',
        y='avg_gap',
        color='avg_gap',
        color_continuous_scale='RdYlGn_r',
        labels={'decade': 'Decade', 'avg_gap': 'Average Gap (%)'},
        text='avg_gap'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Country Rankings
with tab2:
    st.subheader("Country Rankings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Most Equal (Lowest Gap)")

        fig = px.bar(
            lowest_gap,
            x='latest_gap',
            y='country',
            orientation='h',
            color='latest_gap',
            color_continuous_scale='Greens_r',
            labels={'latest_gap': 'Wage Gap (%)', 'country': ''}
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
        st.markdown("#### Least Equal (Highest Gap)")

        fig = px.bar(
            highest_gap,
            x='latest_gap',
            y='country',
            orientation='h',
            color='latest_gap',
            color_continuous_scale='Reds',
            labels={'latest_gap': 'Wage Gap (%)', 'country': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    # Most improved
    st.subheader("Most Improved (Largest Gap Reduction)")

    # Filter for negative gap_change (improvement)
    improved = most_improved[most_improved['gap_change'] < 0].head(10)

    if len(improved) > 0:
        improved_display = improved.copy()
        improved_display['gap_reduction'] = -improved_display['gap_change']

        fig = px.bar(
            improved_display,
            x='gap_reduction',
            y='country',
            orientation='h',
            color='gap_reduction',
            color_continuous_scale='Purples',
            labels={'gap_reduction': 'Gap Reduction (pp)', 'country': ''}
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

    display_df = country_summary[['country', 'region', 'latest_year', 'latest_gap',
                                   'earliest_gap', 'gap_change', 'gap_tier']].copy()
    display_df.columns = ['Country', 'Region', 'Latest Year', 'Latest Gap (%)',
                          'Earliest Gap (%)', 'Change (pp)', 'Category']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Regional Comparison")

    # Bar chart of regional averages
    fig = px.bar(
        region_summary.sort_values('avg_gap'),
        x='region',
        y='avg_gap',
        color='avg_gap',
        color_continuous_scale='RdYlGn_r',
        labels={'region': 'Region', 'avg_gap': 'Average Gap (%)'},
        text='avg_gap'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Regional details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Gap Distribution by Region")

        fig = px.box(
            full_data,
            x='region',
            y='wage_gap',
            color='region',
            labels={'region': 'Region', 'wage_gap': 'Wage Gap (%)'},
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
        st.markdown("#### Regional Summary")

        display_region = region_summary.copy()
        display_region.columns = ['Region', 'Countries', 'Avg Gap (%)', 'Min (%)', 'Max (%)']

        st.dataframe(display_region, use_container_width=True, hide_index=True)

        st.markdown("""
        **Key Regional Patterns:**
        - Nordic countries consistently show the lowest wage gaps
        - Asia-Pacific has significant variation (Japan high, New Zealand low)
        - Latin American countries tend toward higher gaps
        - Central/Eastern Europe shows moderate gaps with improving trends
        """)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📉", "Study 1: Decades of Progress",
            "The average OECD gender wage gap has declined from <b>~20% in the 1970s</b> to <b>~14% today</b> - a 6 percentage point improvement over 46 years.",
            "While progress is real, the pace of change suggests achieving full pay equity could take decades more without accelerated policy intervention."),
        ResearchStudy("🏆", "Study 2: Nordic Success Story",
            "Nordic countries (Belgium, Denmark, Norway) consistently have the <b>lowest wage gaps (<10%)</b>, demonstrating that near-parity is achievable.",
            "Strong labor protections, transparent pay policies, and cultural attitudes about gender equality contribute to narrower gaps."),
        ResearchStudy("⚠️", "Study 3: Persistent Outliers",
            "South Korea and Japan have the <b>highest wage gaps among developed nations (>30%)</b>, despite economic development.",
            "Cultural factors, occupational segregation, and work-life balance policies significantly impact wage equality."),
        ResearchStudy("📊", "Study 4: The Participation Paradox",
            "The gap tends to be <b>larger in countries with lower female labor force participation</b>, suggesting selection effects.",
            "When only highest-earning women work, the gap may appear smaller than the true structural inequality."),
        ResearchStudy("🎯", "Study 5: The Stubborn Gap",
            "Even in the <b>most equal countries, a measurable gap of 5-8%</b> persists despite decades of policy efforts.",
            "This 'last mile' gap may require fundamentally different approaches addressing unconscious bias and structural factors."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Wage gap = (Male median earnings - Female median earnings) / Male median earnings × 100",
        "Data covers full-time employees and self-employed workers",
        "Median earnings used to reduce impact of outliers",
        "Unadjusted gap - does not control for occupation, experience, education"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Unadjusted gap doesn't account for differences in jobs, hours, experience",
        "Part-time work exclusion may not capture full picture",
        "Different countries have different definitions of 'full-time'",
        "Historical data may have measurement inconsistencies"
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
            st.metric("Latest Gap", f"{info['latest_gap']:.1f}%", f"({info['latest_year']})")

        with col2:
            st.metric("Earliest Gap", f"{info['earliest_gap']:.1f}%", f"({info['earliest_year']})")

        with col3:
            change = info['gap_change']
            delta_color = "inverse" if change and change < 0 else "normal"
            st.metric("Change", f"{change:+.1f} pp" if change else "N/A",
                     delta="Improved" if change and change < 0 else "Widened" if change and change > 0 else None,
                     delta_color=delta_color)

        with col4:
            st.metric("Category", info['gap_tier'])

        # Time series
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data['wage_gap'],
            mode='lines+markers',
            name=selected_country,
            line=dict(color='#ec4899', width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(236, 72, 153, 0.1)'
        ))

        fig.add_hline(y=0, line_dash="dash", line_color="green")

        fig.update_layout(
            title=f"Gender Wage Gap in {selected_country}",
            xaxis_title="Year",
            yaxis_title="Wage Gap (%)",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if info['gap_change'] and info['gap_change'] < -5:
            st.success(f"**Significant Progress:** {selected_country} has reduced its gender wage gap by {-info['gap_change']:.1f} percentage points over the measurement period.")
        elif info['gap_change'] and info['gap_change'] > 5:
            st.warning(f"**Gap Widened:** {selected_country}'s gender wage gap has increased by {info['gap_change']:.1f} percentage points over the measurement period.")

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
        st.download_button("Download CSV", csv, "gender_wage_gap_full.csv", "text/csv")

    elif data_view == "Country Summary":
        st.dataframe(country_summary, use_container_width=True, hide_index=True)
        csv = country_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "gender_wage_gap_countries.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "gender_wage_gap_regions.csv", "text/csv")

    else:
        st.dataframe(decade_summary, use_container_width=True, hide_index=True)
        csv = decade_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "gender_wage_gap_decades.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("South Korea", "Japan"),
        ("Belgium", "Norway"),
        ("United States", "United Kingdom"),
    ],
    data=country_summary,
    name_column="country",
    value_column="latest_gap",
    title="Test Your Wage Gap Knowledge",
    prompt="🎯 Can you guess which country has the larger gender wage gap?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """wage_gap ─────────────┐
• country (PK)        │    country_summary
• year (PK)           ├───▶ • country (PK)
• wage_gap            │    • region
• region              │    • latest_gap
• decade              │    • gap_change
• gap_tier            │    • gap_tier
                      │
region_summary ───────┤    decade_summary
• region (PK)         └───▶ • decade (PK)
• countries                 • avg_gap
• avg_gap                   • min_gap
• min_gap                   • max_gap"""

SAMPLE_QUERIES = """-- Countries with lowest wage gaps
SELECT country, region, latest_gap, gap_change, gap_tier
FROM country_summary
ORDER BY latest_gap ASC
LIMIT 10;

-- Gap trend over decades
SELECT decade, avg_gap, countries_with_data
FROM decade_summary
ORDER BY decade;

-- Regional comparison
SELECT region, countries, avg_gap, min_gap, max_gap
FROM region_summary
ORDER BY avg_gap ASC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["46-year historical time series", "38-country OECD comparison", "Gap tier classification", "Regional aggregation"]
)

# Footer
render_data_footer(
    data_sources=["OECD Employment Database", "OECD.stat"],
    time_period=f"{stats['years'][0]} - {stats['years'][1]}\n{stats['countries']} OECD countries",
    data_points=f"{stats['total_records']} records",
    credits={"Data source": "OECD", "Compiled by": "Our World in Data"},
    dataset_url="https://data.oecd.org/earnwage/gender-wage-gap.htm"
)

# Site footer
render_site_footer()
