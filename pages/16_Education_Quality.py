"""
Education Quality Dashboard
Analyzing 50 years of global education quality across 163 countries (1965-2015)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.education_quality.database import EducationQualityDatabase
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
    page_title="Education Quality | Allan Ninal",
    page_icon="🎓",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load education quality data from database."""
    with EducationQualityDatabase() as db:
        full_data = db.get_full_data()
        country_data = db.get_country_data_only()
        country_summary = db.get_country_summary()
        region_summary = db.get_region_summary()
        era_summary = db.get_era_summary()
        tier_summary = db.get_tier_summary()
        top_countries = db.get_top_countries(20)
        bottom_countries = db.get_bottom_countries(20)
        most_improved = db.get_most_improved(15)
        stats = db.get_stats()
    return (full_data, country_data, country_summary, region_summary, era_summary,
            tier_summary, top_countries, bottom_countries, most_improved, stats)


# Load data
(full_data, country_data, country_summary, region_summary, era_summary,
 tier_summary, top_countries, bottom_countries, most_improved, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Education Quality", icon="🎓", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Hero Header
render_hero_header(
    title="Global Education Quality (1965-2015)",
    subtitle="50 years of harmonized learning outcomes from TIMSS, PISA, PIRLS, and regional assessments.",
    data_badge=f"📊 Data: {stats['years'][0]}-{stats['years'][1]} | {stats['countries']} Countries | Altinok, Angrist, and Patrinos (2018)"
)

# Key insight banner
gap = round(stats['best_score'] - bottom_countries['latest_score'].min(), 1)
render_shocking_fact(
    value=f"{gap} pts",
    description=f"The gap between top and bottom performers spans <b>{gap} points</b> on the harmonized scale. <b>{stats['best_entity']}</b> leads with <b>{stats['best_score']}</b>, while the lowest performers score below <b>300</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['global_avg']}", "Global Average<br>Score"),
    HeroStat(f"{stats['best_score']}", f"{stats['best_entity']}<br>World Leader", "success"),
    HeroStat(f"{stats['years'][1] - stats['years'][0]}", "Years<br>Of Data", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Analyzed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Global Rankings", "Trends Over Time", "Regional Analysis",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Global Rankings
with tab1:
    st.subheader("Top 20 Countries by Harmonized Score")

    fig = px.bar(
        top_countries,
        x='latest_score',
        y='entity',
        orientation='h',
        color='latest_score',
        color_continuous_scale='Greens',
        labels={'latest_score': 'Harmonized Score', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Bottom 20 Countries")

    fig = px.bar(
        bottom_countries,
        x='latest_score',
        y='entity',
        orientation='h',
        color='latest_score',
        color_continuous_scale='Reds_r',
        labels={'latest_score': 'Harmonized Score', 'entity': ''}
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Performance tiers
    st.subheader("Countries by Performance Tier")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.pie(
            tier_summary,
            values='countries',
            names='performance_tier',
            color='performance_tier',
            color_discrete_map={
                'High (525+)': '#22c55e',
                'Upper-Middle (475-525)': '#84cc16',
                'Middle (425-475)': '#eab308',
                'Lower-Middle (375-425)': '#f97316',
                'Low (<375)': '#ef4444'
            }
        )

        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tier_display = tier_summary.copy()
        tier_display.columns = ['Tier', 'Countries', 'Avg Score', 'Min', 'Max', 'Avg % Min', 'Avg % Adv']

        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown("""
        **Performance Thresholds:**
        - **High (525+)**: Top-tier education systems
        - **Upper-Middle (475-525)**: Strong performers
        - **Middle (425-475)**: Average performance
        - **Lower-Middle (375-425)**: Below average
        - **Low (<375)**: Significant challenges
        """)

# Tab 2: Trends Over Time
with tab2:
    st.subheader("Score Trends Over Time")

    # Country selection for time series
    available_countries = country_data[country_data['is_country']]['entity'].unique().tolist()
    default_countries = ['Singapore', 'Japan', 'Finland', 'United States', 'Brazil']
    default_selection = [c for c in default_countries if c in available_countries][:5]

    selected_countries = st.multiselect(
        "Select countries to compare:",
        options=sorted(available_countries),
        default=default_selection,
        key="trend_countries"
    )

    if selected_countries:
        filtered_data = country_data[country_data['entity'].isin(selected_countries)]
        filtered_data = filtered_data.dropna(subset=['avg_score'])

        fig = px.line(
            filtered_data,
            x='year',
            y='avg_score',
            color='entity',
            labels={'year': 'Year', 'avg_score': 'Harmonized Score', 'entity': 'Country'},
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

        # Add reference lines for thresholds
        fig.add_hline(y=525, line_dash="dash", line_color="green",
                      annotation_text="High performance (525)")
        fig.add_hline(y=400, line_dash="dash", line_color="orange",
                      annotation_text="Minimum benchmark (400)")

        fig.update_traces(line_width=2.5)

        st.plotly_chart(fig, use_container_width=True)

    # Era analysis
    st.subheader("Average Scores by Era")

    fig = px.bar(
        era_summary,
        x='era',
        y='avg_score',
        color='avg_score',
        color_continuous_scale='Blues',
        labels={'era': 'Era', 'avg_score': 'Average Score'},
        text='avg_score'
    )

    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Most improved countries
    st.subheader("Most Improved Countries")

    improved_display = most_improved.copy()
    improved_display = improved_display[improved_display['score_change'] > 0]

    if len(improved_display) > 0:
        fig = px.bar(
            improved_display.head(15),
            x='score_change',
            y='entity',
            orientation='h',
            color='score_change',
            color_continuous_scale='Greens',
            labels={'score_change': 'Score Improvement', 'entity': ''}
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

# Tab 3: Regional Analysis
with tab3:
    st.subheader("Regional Comparison")

    # Bar chart of regional averages
    fig = px.bar(
        region_summary,
        x='region',
        y='avg_score',
        color='avg_score',
        color_continuous_scale='RdYlGn',
        labels={'region': 'Region', 'avg_score': 'Average Score'},
        text='avg_score'
    )

    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
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
        st.markdown("#### Score Distribution by Region")

        # Get latest data per country
        latest_country = country_data.loc[country_data.groupby('entity')['year'].idxmax()]

        fig = px.box(
            latest_country,
            x='region',
            y='avg_score',
            color='region',
            labels={'region': 'Region', 'avg_score': 'Harmonized Score'},
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
        display_region.columns = ['Region', 'Countries', 'Avg Score', 'Min', 'Max', 'Std', 'Avg % Min', 'Avg % Adv']

        st.dataframe(display_region, use_container_width=True, hide_index=True)

        st.markdown("""
        **Key Regional Patterns:**
        - East Asia & Pacific leads in test scores
        - Europe shows consistent high performance
        - Sub-Saharan Africa faces major challenges
        - Latin America shows wide variability
        """)

    # Proficiency rates by region
    st.subheader("Proficiency Rates by Region")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### % Achieving Minimum Threshold")

        fig = px.bar(
            region_summary.sort_values('avg_pct_minimum', ascending=False),
            x='region',
            y='avg_pct_minimum',
            color='avg_pct_minimum',
            color_continuous_scale='Greens',
            labels={'region': 'Region', 'avg_pct_minimum': '% Students'},
            text='avg_pct_minimum'
        )

        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### % Achieving Advanced Threshold")

        fig = px.bar(
            region_summary.sort_values('avg_pct_advanced', ascending=False),
            x='region',
            y='avg_pct_advanced',
            color='avg_pct_advanced',
            color_continuous_scale='Purples',
            labels={'region': 'Region', 'avg_pct_advanced': '% Students'},
            text='avg_pct_advanced'
        )

        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🥇", "Study 1: Singapore's Dominance",
            "<b>Singapore</b> consistently tops global education rankings with a score of <b>619</b>, nearly <b>40%</b> above the global average.",
            "Singapore's success stems from teacher quality investment, rigorous curriculum, and a culture that highly values education."),
        ResearchStudy("📈", "Study 2: The East Asian Advantage",
            "East Asia & Pacific leads with an average score of <b>485+</b>, with <b>4 of the top 5</b> countries being Asian.",
            "The 'Asian advantage' reflects cultural emphasis on education, teacher preparation, and instructional time allocation."),
        ResearchStudy("📉", "Study 3: The Learning Crisis",
            "In low-performing countries, only <b>25-50%</b> of students achieve even the minimum proficiency threshold.",
            "This 'learning crisis' means children attend school but don't acquire basic skills - what experts call 'schooling without learning'."),
        ResearchStudy("🌍", "Study 4: Regional Disparities",
            "Sub-Saharan Africa averages <b>374 points</b> vs <b>510+ for Europe</b> - a gap equivalent to <b>4+ years</b> of schooling.",
            "These disparities reflect resource differences, teacher quality, and infrastructure challenges that perpetuate inequality."),
        ResearchStudy("📊", "Study 5: Progress Over Decades",
            "Many developing countries showed improvements of <b>50-100+ points</b> over the study period, demonstrating reform is possible.",
            "Countries like Albania, Peru, and Turkey made significant gains through targeted education investments and policy reforms."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Harmonized scores from 14 international and regional assessments (TIMSS, PISA, PIRLS, SACMEQ, PASEC, etc.)",
        "Scores linked using item response theory and equipercentile methods",
        "Scale centered around 500 (equivalent to average OECD performance)",
        "Proficiency thresholds: Minimum (400), Intermediate (475), Advanced (625)"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Not all countries participate in standardized tests",
        "Tests administered in different years require temporal linking",
        "Cultural and linguistic factors may affect comparability",
        "Selection bias in test-taking populations in some countries"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Country Explorer
with tab5:
    st.subheader("Explore Individual Countries")

    selected_entity = st.selectbox(
        "Select a country:",
        options=sorted(country_summary['entity'].unique()),
        index=sorted(country_summary['entity'].unique()).index('United States') if 'United States' in country_summary['entity'].unique() else 0
    )

    entity_data = full_data[full_data['entity'] == selected_entity].sort_values('year')
    entity_info = country_summary[country_summary['entity'] == selected_entity]

    if len(entity_data) > 0 and len(entity_info) > 0:
        info = entity_info.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Latest Score",
                      f"{info['latest_score']:.0f}" if pd.notna(info['latest_score']) else "N/A",
                      f"({int(info['latest_year'])})")

        with col2:
            st.metric("Earliest Score",
                      f"{info['earliest_score']:.0f}" if pd.notna(info['earliest_score']) else "N/A",
                      f"({int(info['earliest_year'])})")

        with col3:
            change = info['score_change']
            st.metric("Score Change",
                      f"{change:+.0f}" if pd.notna(change) else "N/A",
                      delta=f"{change:+.0f}" if pd.notna(change) and change != 0 else None,
                      delta_color="normal" if pd.notna(change) else "off")

        with col4:
            st.metric("Performance Tier", info['performance_tier'].split('(')[0].strip() if pd.notna(info['performance_tier']) else "N/A")

        # Time series if multiple data points
        if len(entity_data) > 1:
            st.subheader(f"Score Trend for {selected_entity}")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=entity_data['year'],
                y=entity_data['avg_score'],
                mode='lines+markers',
                name='Harmonized Score',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=10)
            ))

            # Reference lines
            fig.add_hline(y=525, line_dash="dash", line_color="green",
                          annotation_text="High performance")
            fig.add_hline(y=400, line_dash="dash", line_color="orange",
                          annotation_text="Minimum benchmark")

            fig.update_layout(
                xaxis_title="Year",
                yaxis_title="Harmonized Score",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        # Regional comparison
        st.subheader(f"How {selected_entity} Compares in {info['region']}")

        region_countries = country_summary[country_summary['region'] == info['region']].sort_values('latest_score', ascending=False)

        colors = ['#3b82f6' if c != selected_entity else '#ef4444' for c in region_countries['entity']]

        fig = px.bar(
            region_countries,
            x='latest_score',
            y='entity',
            orientation='h',
            labels={'latest_score': 'Latest Score', 'entity': ''}
        )

        fig.update_traces(marker_color=colors)

        fig.update_layout(
            height=max(400, len(region_countries) * 25),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if pd.notna(info['latest_score']):
            if info['latest_score'] >= 525:
                st.success(f"**{selected_entity}** is among the world's top performers in education quality.")
            elif info['latest_score'] >= 475:
                st.info(f"**{selected_entity}** performs above the global average with room for improvement.")
            elif info['latest_score'] >= 425:
                st.warning(f"**{selected_entity}** has moderate education outcomes with significant potential for growth.")
            else:
                st.error(f"**{selected_entity}** faces substantial challenges in education quality that require urgent attention.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Country Summary", "Region Summary", "Era Summary", "Tier Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        st.dataframe(full_data, use_container_width=True, hide_index=True)
        csv = full_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "education_quality_full.csv", "text/csv")

    elif data_view == "Country Summary":
        st.dataframe(country_summary, use_container_width=True, hide_index=True)
        csv = country_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "education_quality_countries.csv", "text/csv")

    elif data_view == "Region Summary":
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
        csv = region_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "education_quality_regions.csv", "text/csv")

    elif data_view == "Era Summary":
        st.dataframe(era_summary, use_container_width=True, hide_index=True)
        csv = era_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "education_quality_eras.csv", "text/csv")

    else:
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
        csv = tier_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "education_quality_tiers.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Singapore", "Japan"),
        ("Finland", "United States"),
        ("South Korea", "Germany"),
    ],
    data=country_summary,
    name_column="entity",
    value_column="latest_score",
    title="Test Your Education Knowledge",
    prompt="Can you guess which country has HIGHER education quality scores?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """education_quality ────┐
* entity (PK)         │    country_summary
* year (PK)           ├──▶ * entity (PK)
* region              │    * region
* avg_score           │    * latest_score
* pct_minimum         │    * score_change
* pct_advanced        │    * performance_tier
* performance_tier    │
                      │    region_summary
era_summary ──────────┤    * region (PK)
* era (PK)            └──▶ * avg_score
* avg_score                * countries
* countries_tested"""

SAMPLE_QUERIES = """-- Top countries by harmonized score
SELECT entity, region, latest_score, score_change
FROM country_summary
ORDER BY latest_score DESC
LIMIT 10;

-- Regional performance comparison
SELECT region, ROUND(AVG(avg_score), 1) as avg, COUNT(*) as countries
FROM education_quality
WHERE is_country = true
GROUP BY region
ORDER BY avg DESC;

-- Most improved countries
SELECT entity, earliest_score, latest_score, score_change
FROM country_summary
WHERE score_change IS NOT NULL
ORDER BY score_change DESC
LIMIT 10;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["50-year time series (1965-2015)", "14 harmonized assessment sources", "143 countries analyzed", "Proficiency threshold tracking"]
)

# Footer
render_data_footer(
    data_sources=["TIMSS", "PISA", "PIRLS", "SACMEQ", "PASEC", "LLECE"],
    time_period=f"{stats['years'][0]} - {stats['years'][1]}\n{stats['countries']} countries",
    data_points=f"{stats['total_records']} records",
    credits={"Research": "Altinok, Angrist, and Patrinos", "Compilation": "World Bank"},
    dataset_url="http://documents.worldbank.org/curated/en/706141516721172989/Global-data-set-on-education-quality-1965-2015"
)

# Site footer
render_site_footer()
