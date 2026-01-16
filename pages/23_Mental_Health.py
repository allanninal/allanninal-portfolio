"""
Mental Health Services Dashboard
Analyzing treatment gaps across 17 countries (Wang et al. 2007)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mental_health.database import MentalHealthDatabase
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
    page_title="Mental Health Services | Allan Ninal",
    page_icon="🧠",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load mental health data from database."""
    with MentalHealthDatabase() as db:
        full_data = db.get_full_data()
        income_summary = db.get_income_summary()
        service_summary = db.get_service_summary()
        by_treatment = db.get_by_treatment_rate()
        by_severe = db.get_by_severe_treatment()
        treatment_gaps = db.get_treatment_gaps()
        stats = db.get_stats()
    return (full_data, income_summary, service_summary, by_treatment,
            by_severe, treatment_gaps, stats)


# Load data
(full_data, income_summary, service_summary, by_treatment,
 by_severe, treatment_gaps, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Mental Health", icon="🧠", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Mental Health Services Across Incomes",
    subtitle="Revealing the global treatment gap - most people with mental illness never receive care, especially in low-income countries.",
    data_badge=f"🌍 Data: {stats['countries']} Countries | Wang et al. (2007) WHO World Mental Health Surveys"
)

# Calculate key insight
severe_gap = 100 - stats['avg_severe_treated']

# Key insight banner
render_shocking_fact(
    value=f"{severe_gap:.0f}% Untreated",
    description=f"On average, <b>{severe_gap:.0f}%</b> of people with <b>severe mental illness</b> receive NO treatment. In <b>{stats['lowest_treatment_country']}</b>, only <b>{stats['lowest_treatment']:.1f}%</b> of the population receives any mental health care, compared to <b>{stats['highest_treatment']:.1f}%</b> in the <b>{stats['highest_treatment_country']}</b>.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['avg_any_treatment']:.1f}%", "Avg Population<br>Receiving Treatment"),
    HeroStat(f"{stats['avg_severe_treated']:.0f}%", "Severe Cases<br>Getting Care", "success"),
    HeroStat(f"{stats['treatment_range']:.0f}pp", f"Gap: US vs Nigeria<br>Treatment Rate", "secondary"),
    HeroStat(f"{stats['countries']}", "Countries<br>Surveyed", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Treatment Gap", "By Severity", "Service Types",
    "Research Findings", "Country Explorer", "Raw Data"
])

# Tab 1: Treatment Gap
with tab1:
    st.subheader("Population Receiving Any Mental Health Treatment")

    fig = px.bar(
        by_treatment,
        x='any_treatment',
        y='country',
        orientation='h',
        color='income_group',
        color_discrete_map={
            'High Income': '#3b82f6',
            'Upper-Middle': '#22c55e',
            'Lower-Middle': '#f97316',
            'Low Income': '#ef4444'
        },
        labels={'any_treatment': '% of Population', 'country': '', 'income_group': 'Income Group'}
    )

    fig.update_layout(
        height=550,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Income group comparison
    st.subheader("Treatment Rate by Income Group")

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.bar(
            income_summary,
            x='income_group',
            y='avg_any_treatment',
            color='income_group',
            color_discrete_map={
                'High Income': '#3b82f6',
                'Upper-Middle': '#22c55e',
                'Lower-Middle': '#f97316',
                'Low Income': '#ef4444'
            },
            labels={'avg_any_treatment': 'Avg % Receiving Treatment', 'income_group': ''}
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Healthcare spending vs treatment
        fig = px.scatter(
            full_data,
            x='gdp_healthcare',
            y='any_treatment',
            color='income_group',
            size='severe_treated',
            hover_name='country',
            color_discrete_map={
                'High Income': '#3b82f6',
                'Upper-Middle': '#22c55e',
                'Lower-Middle': '#f97316',
                'Low Income': '#ef4444'
            },
            labels={
                'gdp_healthcare': 'Healthcare Spending (% of GDP)',
                'any_treatment': '% Receiving Treatment',
                'income_group': 'Income Group'
            }
        )

        fig.update_layout(
            title='Healthcare Spending vs Treatment Rate',
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    st.info("**Key Finding**: Higher healthcare spending correlates with higher mental health treatment rates, but even wealthy countries leave most severe cases untreated.")

# Tab 2: By Severity
with tab2:
    st.subheader("Treatment Rates by Mental Illness Severity")

    st.markdown("Even people with **severe** mental illness often go untreated. The treatment gap widens for moderate and mild cases.")

    # Global averages by severity
    severity_data = pd.DataFrame({
        'severity': ['Severe', 'Moderate', 'Mild'],
        'treated': [stats['avg_severe_treated'], stats['avg_moderate_treated'], stats['avg_mild_treated']],
        'untreated': [100 - stats['avg_severe_treated'], 100 - stats['avg_moderate_treated'], 100 - stats['avg_mild_treated']]
    })

    col1, col2 = st.columns([1, 1])

    with col1:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=severity_data['severity'],
            y=severity_data['treated'],
            name='Treated',
            marker_color='#22c55e'
        ))

        fig.add_trace(go.Bar(
            x=severity_data['severity'],
            y=severity_data['untreated'],
            name='Untreated',
            marker_color='#ef4444'
        ))

        fig.update_layout(
            title='Global Average: Treated vs Untreated by Severity',
            height=400,
            barmode='stack',
            yaxis_title='Percentage',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Treatment Gap by Severity")

        for _, row in severity_data.iterrows():
            st.markdown(f"""
            **{row['severity']}**: {row['untreated']:.0f}% untreated
            """)
            st.progress(row['untreated'] / 100)

        st.markdown("""
        ---
        **Severity Definitions:**
        - **Severe**: Bipolar I, suicide attempts, major functional impairment
        - **Moderate**: Substance dependence, moderate interference
        - **Mild**: Other mental disorders
        """)

    # By country - severe treatment
    st.subheader("Severe Mental Illness Treatment by Country")

    fig = px.bar(
        by_severe,
        x='severe_treated',
        y='country',
        orientation='h',
        color='treatment_gap',
        color_discrete_map={
            'Low Gap (<50% untreated)': '#22c55e',
            'Moderate Gap (50-70% untreated)': '#f97316',
            'High Gap (70-80% untreated)': '#ef4444',
            'Very High Gap (80%+ untreated)': '#7f1d1d'
        },
        labels={'severe_treated': '% Receiving Treatment', 'country': '', 'treatment_gap': 'Gap Category'}
    )

    fig.update_layout(
        height=550,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Heatmap of severity by country
    st.subheader("Treatment Rates Heatmap (by Country & Severity)")

    heatmap_data = full_data[['country', 'severe_treated', 'moderate_treated', 'mild_treated']].copy()
    heatmap_data = heatmap_data.set_index('country')
    heatmap_data.columns = ['Severe', 'Moderate', 'Mild']

    fig = px.imshow(
        heatmap_data,
        color_continuous_scale='RdYlGn',
        labels={'color': 'Treatment Rate (%)'},
        aspect='auto'
    )

    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Service Types
with tab3:
    st.subheader("Where People Seek Mental Health Care")

    st.markdown("Mental health services are classified into four sectors. **General medical** (primary care) is the most common entry point globally.")

    # Global service breakdown
    fig = px.bar(
        service_summary,
        x='avg_usage',
        y='service_type',
        orientation='h',
        color='service_type',
        color_discrete_map={
            'General Medical': '#3b82f6',
            'Mental Health Specialty': '#22c55e',
            'Human Services': '#f97316',
            'Alternative Medicine': '#a855f7'
        },
        labels={'avg_usage': 'Average Usage (%)', 'service_type': ''}
    )

    fig.update_layout(
        title='Global Average Service Usage (among those receiving treatment)',
        height=350,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # By country breakdown
    st.subheader("Service Type Breakdown by Country")

    service_cols = ['specialty_pct', 'general_medical_pct', 'human_services_pct', 'alternative_pct']
    service_labels = ['Mental Health Specialty', 'General Medical', 'Human Services', 'Alternative Medicine']

    fig = go.Figure()

    for col, label in zip(service_cols, service_labels):
        fig.add_trace(go.Bar(
            y=full_data['country'],
            x=full_data[col],
            name=label,
            orientation='h'
        ))

    fig.update_layout(
        height=550,
        barmode='stack',
        xaxis_title='Percentage',
        yaxis={'categoryorder': 'array', 'categoryarray': full_data.sort_values('any_treatment')['country'].tolist()},
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Service descriptions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Mental Health Specialty
        - Psychiatrists
        - Psychologists
        - Mental health counselors
        - Mental health hotlines

        ### General Medical
        - Primary care doctors
        - General practitioners
        - Nurses
        - Other medical professionals
        """)

    with col2:
        st.markdown("""
        ### Human Services
        - Religious/spiritual advisors
        - Social workers (non-specialty)
        - Community counselors

        ### Alternative Medicine
        - Chiropractors
        - Traditional healers
        - Internet support groups
        - Self-help groups
        """)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("🇺🇸", "Study 1: US Leads Despite Gaps",
            "The <b>United States</b> has the highest treatment rate at <b>17.9%</b>, yet still leaves <b>40% of severe cases</b> untreated.",
            "High healthcare spending enables better access, but barriers like stigma and cost persist."),
        ResearchStudy("🇳🇬", "Study 2: Nigeria's Extreme Gap",
            "<b>Nigeria</b> has only <b>1.6%</b> receiving any mental health treatment - the lowest in the study.",
            "With 3.4% of GDP on healthcare and limited mental health infrastructure, the vast majority go untreated."),
        ResearchStudy("🏥", "Study 3: Primary Care Dominates",
            "<b>General medical</b> providers (primary care) are the most common entry point, averaging <b>59%</b> of treatment contacts.",
            "This highlights the need for mental health training in primary care settings globally."),
        ResearchStudy("📊", "Study 4: Severity Doesn't Guarantee Care",
            "Even <b>severe mental illness</b> has only a <b>39% treatment rate</b> globally - 61% get no help.",
            "The treatment gap exists at all severity levels but is most tragic for those suffering the most."),
        ResearchStudy("💰", "Study 5: Income Predicts Access",
            "<b>High-income countries</b> average <b>11%</b> treatment vs <b>2.5%</b> in low-income countries.",
            "The 4-5x gap in treatment access reflects broader healthcare inequalities."),
    ])

    st.markdown("### Survey Methodology")
    methods = [
        "Face-to-face household surveys in 17 countries (2001-2004)",
        "Standardized WHO World Mental Health Survey instrument",
        "Treatment defined as any contact in past 12 months",
        "Severity classified using clinical assessment scales"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Data from 2001-2004 - treatment rates may have changed",
        "Self-reported treatment may underestimate actual contact",
        "Only 17 countries - not globally representative",
        "Doesn't capture treatment quality or adequacy"
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

    with MentalHealthDatabase() as db:
        country_data = db.get_country_data(selected_country)
        service_breakdown = db.get_service_breakdown(selected_country)
        severity_breakdown = db.get_severity_breakdown(selected_country)

    if len(country_data) > 0:
        info = country_data.iloc[0]

        # Country stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Any Treatment", f"{info['any_treatment']:.1f}%")

        with col2:
            st.metric("Healthcare Spending", f"{info['gdp_healthcare']:.1f}% GDP")

        with col3:
            st.metric("Severe Treated", f"{info['severe_treated']:.1f}%")

        with col4:
            st.metric("Income Group", info['income_group'])

        # Service breakdown
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Service Type Breakdown")

            if len(service_breakdown) > 0:
                fig = px.pie(
                    service_breakdown,
                    values='percentage',
                    names='service_type',
                    color='service_type',
                    color_discrete_map={
                        'General Medical': '#3b82f6',
                        'Mental Health Specialty': '#22c55e',
                        'Human Services': '#f97316',
                        'Alternative Medicine': '#a855f7'
                    }
                )

                fig.update_layout(
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )

                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Treatment by Severity")

            if len(severity_breakdown) > 0:
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=severity_breakdown['severity'],
                    y=severity_breakdown['treated_pct'],
                    name='Treated',
                    marker_color='#22c55e'
                ))

                fig.add_trace(go.Bar(
                    x=severity_breakdown['severity'],
                    y=severity_breakdown['untreated_pct'],
                    name='Untreated',
                    marker_color='#ef4444'
                ))

                fig.update_layout(
                    height=350,
                    barmode='stack',
                    yaxis_title='Percentage',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )

                st.plotly_chart(fig, use_container_width=True)

        # Comparison to global average
        st.subheader(f"How {selected_country} Compares to Global Average")

        compare_data = pd.DataFrame({
            'metric': ['Any Treatment', 'Severe Treated', 'Moderate Treated', 'Mild Treated'],
            'country': [info['any_treatment'], info['severe_treated'], info['moderate_treated'], info['mild_treated']],
            'global': [stats['avg_any_treatment'], stats['avg_severe_treated'], stats['avg_moderate_treated'], stats['avg_mild_treated']]
        })

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=compare_data['metric'],
            y=compare_data['country'],
            name=selected_country,
            marker_color='#3b82f6'
        ))

        fig.add_trace(go.Bar(
            x=compare_data['metric'],
            y=compare_data['global'],
            name='Global Average',
            marker_color='#94a3b8'
        ))

        fig.update_layout(
            height=400,
            barmode='group',
            yaxis_title='Treatment Rate (%)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if info['any_treatment'] >= 15:
            st.success(f"**{selected_country}** has one of the highest mental health treatment rates in the study.")
        elif info['any_treatment'] >= 8:
            st.info(f"**{selected_country}** has a moderate treatment rate, around the global average.")
        elif info['any_treatment'] >= 5:
            st.warning(f"**{selected_country}** has a below-average treatment rate - significant gaps exist.")
        else:
            st.error(f"**{selected_country}** has very low mental health treatment access - most people go untreated.")

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "Income Group Summary", "Service Type Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        display_data = full_data.copy()
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "mental_health_full.csv", "text/csv")

    elif data_view == "Income Group Summary":
        st.dataframe(income_summary, use_container_width=True, hide_index=True)
        csv = income_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "mental_health_income.csv", "text/csv")

    else:
        st.dataframe(service_summary, use_container_width=True, hide_index=True)
        csv = service_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "mental_health_services.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("United States", "Germany"),
        ("Belgium", "China"),
        ("New Zealand", "Japan"),
    ],
    data=full_data,
    name_column="country",
    value_column="any_treatment",
    title="Test Your Knowledge",
    prompt="Can you guess which country has the HIGHER mental health treatment rate?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """mental_health ────────┐
* country (PK)        │    income_summary
* gdp_healthcare      ├──▶ * income_group (PK)
* any_treatment       │    * avg_any_treatment
* severe_treated      │    * avg_severe_treated
* moderate_treated    │
* mild_treated        │    service_summary
* specialty_pct       └──▶ * service_type (PK)
* general_medical_pct      * avg_usage"""

SAMPLE_QUERIES = """-- Treatment rate ranking
SELECT country, income_group, any_treatment, severe_treated
FROM mental_health
ORDER BY any_treatment DESC;

-- Income group comparison
SELECT income_group, avg_any_treatment, avg_severe_treated
FROM income_summary
ORDER BY avg_any_treatment DESC;

-- Service type usage
SELECT service_type, avg_usage
FROM service_summary
ORDER BY avg_usage DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["17 countries surveyed", "4 service types", "3 severity levels", "Income-based analysis"]
)

# Footer
render_data_footer(
    data_sources=["Wang et al. (2007) The Lancet", "WHO World Mental Health Surveys"],
    time_period="2001-2004",
    data_points=f"{stats['countries']} countries",
    credits={"Research": "WHO WMH Survey Initiative", "Publication": "The Lancet"},
    dataset_url="https://www.sciencedirect.com/science/article/pii/S0140673607614147"
)

# Mental health resources
st.markdown("---")
st.markdown("""
<div style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 1.5rem; border-radius: 12px; text-align: center;">
    <h4 style="color: white; margin: 0 0 0.5rem 0;">Mental health support is available</h4>
    <p style="color: rgba(255,255,255,0.9); margin: 0;">
        <b>WHO Mental Health Resources:</b>
        <a href="https://www.who.int/health-topics/mental-health" target="_blank" style="color: #fef08a;">Learn More</a>
        <br>
        <b>Find local services:</b> Contact your primary care provider or local health department
    </p>
</div>
""", unsafe_allow_html=True)

# Site Footer
render_site_footer()
