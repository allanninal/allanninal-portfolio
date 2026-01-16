"""
Deaths per TWh Energy Production Dashboard
Comparing safety of different energy sources based on mortality rates
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.energy_deaths.database import EnergyDeathsDatabase
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
    page_title="Deaths per TWh Energy | Allan Ninal",
    page_icon="⚡",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load energy deaths data from database."""
    with EnergyDeathsDatabase() as db:
        full_data = db.get_full_data()
        by_safety = db.get_by_safety()
        category_summary = db.get_category_summary()
        fossil_fuels = db.get_fossil_fuels()
        renewables = db.get_renewables()
        clean_energy = db.get_clean_energy()
        stats = db.get_stats()
    return (full_data, by_safety, category_summary, fossil_fuels,
            renewables, clean_energy, stats)


# Load data
(full_data, by_safety, category_summary, fossil_fuels,
 renewables, clean_energy, stats) = load_data()

# Setup page with theme and sidebar
setup_page("Energy Deaths", icon="⚡", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site Header
render_site_header()

# Hero Header
render_hero_header(
    title="Deaths per TWh Energy Production",
    subtitle="Comparing the true human cost of different energy sources - from the most deadly fossil fuels to the safest renewables.",
    data_badge="⚡ Data: Markandya & Wilkinson (2007), Sovacool et al. (2016), Our World in Data"
)

# Key insight banner
render_shocking_fact(
    value=f"{stats['danger_ratio']:.0f}x Safer",
    description=f"<b>Solar energy</b> is <b>{stats['danger_ratio']:.0f} times safer</b> than <b>brown coal</b>. Fossil fuels cause <b>{stats['fossil_avg']:.1f} deaths/TWh</b> on average vs just <b>{stats['renewable_avg']:.2f} deaths/TWh</b> for renewables - a <b>{stats['fossil_vs_renewable']:.0f}x</b> difference.",
    style="primary"
)

st.markdown("---")

# Hero Stats
render_hero_stats([
    HeroStat(f"{stats['highest_deaths']:.1f}", f"Deaths/TWh<br>({stats['most_dangerous']})", "danger"),
    HeroStat(f"{stats['lowest_deaths']:.3f}", f"Deaths/TWh<br>({stats['safest']})", "success"),
    HeroStat(f"{stats['danger_ratio']:.0f}x", "Safety Gap<br>Coal vs Solar", "secondary"),
    HeroStat(f"{stats['sources']}", "Energy Sources<br>Compared", "warning"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Safety Ranking", "Category Comparison", "Interactive Compare",
    "Research Findings", "Raw Data"
])

# Tab 1: Safety Ranking
with tab1:
    st.subheader("Energy Sources Ranked by Safety")

    st.markdown("Deaths include both direct accidents and air pollution mortality. Lower is safer.")

    # Main bar chart - deaths per TWh
    fig = px.bar(
        full_data,
        x='deaths_per_twh',
        y='energy_source',
        orientation='h',
        color='category',
        color_discrete_map={
            'Fossil Fuels': '#ef4444',
            'Biomass': '#f97316',
            'Renewables': '#22c55e',
            'Nuclear': '#3b82f6'
        },
        labels={'deaths_per_twh': 'Deaths per TWh', 'energy_source': '', 'category': 'Category'}
    )

    fig.update_layout(
        height=450,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Log scale version
    st.subheader("Logarithmic Scale (to see smaller values)")

    fig = px.bar(
        full_data,
        x='deaths_per_twh',
        y='energy_source',
        orientation='h',
        color='category',
        color_discrete_map={
            'Fossil Fuels': '#ef4444',
            'Biomass': '#f97316',
            'Renewables': '#22c55e',
            'Nuclear': '#3b82f6'
        },
        log_x=True,
        labels={'deaths_per_twh': 'Deaths per TWh (log scale)', 'energy_source': '', 'category': 'Category'}
    )

    fig.update_layout(
        height=450,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Relative danger
    st.subheader("Relative Danger (compared to safest)")

    fig = px.bar(
        full_data,
        x='relative_danger',
        y='energy_source',
        orientation='h',
        color='safety_tier',
        color_discrete_map={
            'High Risk (20+)': '#7f1d1d',
            'Moderate (5-20)': '#dc2626',
            'Safe (1-5)': '#f97316',
            'Very Safe (0.1-1)': '#22c55e',
            'Extremely Safe (<0.1)': '#15803d'
        },
        labels={'relative_danger': 'Times more deadly than Solar', 'energy_source': '', 'safety_tier': 'Safety Tier'}
    )

    fig.update_layout(
        height=450,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Safety tier distribution
    st.subheader("Sources by Safety Tier")

    tier_counts = full_data['safety_tier'].value_counts().reset_index()
    tier_counts.columns = ['safety_tier', 'count']

    fig = px.pie(
        tier_counts,
        values='count',
        names='safety_tier',
        color='safety_tier',
        color_discrete_map={
            'High Risk (20+)': '#7f1d1d',
            'Moderate (5-20)': '#dc2626',
            'Safe (1-5)': '#f97316',
            'Very Safe (0.1-1)': '#22c55e',
            'Extremely Safe (<0.1)': '#15803d'
        }
    )

    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
        **Safety Tiers (Deaths per TWh):**

        - **Extremely Safe (<0.1)**: Nuclear, Solar, Wind
        - **Very Safe (0.1-1)**: Hydropower
        - **Safe (1-5)**: Gas, Biomass
        - **Moderate (5-20)**: Oil
        - **High Risk (20+)**: Coal, Brown coal
        """)

        st.info("The safest energy sources (nuclear, solar, wind) have death rates **hundreds to thousands of times lower** than fossil fuels.")

# Tab 2: Category Comparison
with tab2:
    st.subheader("Deaths by Energy Category")

    # Category averages
    fig = px.bar(
        category_summary,
        x='avg_deaths',
        y='category',
        orientation='h',
        color='category',
        color_discrete_map={
            'Fossil Fuels': '#ef4444',
            'Biomass': '#f97316',
            'Renewables': '#22c55e',
            'Nuclear': '#3b82f6'
        },
        labels={'avg_deaths': 'Avg Deaths per TWh', 'category': ''}
    )

    fig.update_layout(
        height=350,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Fossil fuels breakdown
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Fossil Fuels Breakdown")

        fig = px.bar(
            fossil_fuels,
            x='deaths_per_twh',
            y='energy_source',
            orientation='h',
            color='deaths_per_twh',
            color_continuous_scale='Reds',
            labels={'deaths_per_twh': 'Deaths per TWh', 'energy_source': ''}
        )

        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Key findings:**
        - Brown coal is the deadliest (32.7/TWh)
        - Gas is cleanest fossil fuel but still 100x more deadly than solar
        - Most deaths from air pollution, not accidents
        """)

    with col2:
        st.subheader("Clean Energy Breakdown")

        fig = px.bar(
            clean_energy,
            x='deaths_per_twh',
            y='energy_source',
            orientation='h',
            color='deaths_per_twh',
            color_continuous_scale='Greens_r',
            labels={'deaths_per_twh': 'Deaths per TWh', 'energy_source': ''}
        )

        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Key findings:**
        - Solar is safest (0.019/TWh)
        - Nuclear is second safest despite Chernobyl/Fukushima
        - Wind is third safest (0.035/TWh)
        - Hydropower has most deaths among clean sources (dam failures)
        """)

    # Side-by-side comparison
    st.subheader("Direct Comparison: Fossil vs Clean")

    fossil_avg = category_summary[category_summary['category'] == 'Fossil Fuels']['avg_deaths'].values[0]
    renewable_avg = category_summary[category_summary['category'] == 'Renewables']['avg_deaths'].values[0]
    nuclear_avg = category_summary[category_summary['category'] == 'Nuclear']['avg_deaths'].values[0]

    compare_data = pd.DataFrame({
        'category': ['Fossil Fuels', 'Renewables', 'Nuclear'],
        'avg_deaths': [fossil_avg, renewable_avg, nuclear_avg]
    })

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=compare_data['category'],
        y=compare_data['avg_deaths'],
        marker_color=['#ef4444', '#22c55e', '#3b82f6'],
        text=[f"{v:.2f}" for v in compare_data['avg_deaths']],
        textposition='outside'
    ))

    fig.update_layout(
        height=400,
        xaxis_title='',
        yaxis_title='Average Deaths per TWh',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**Switching from fossil fuels to renewables/nuclear would reduce energy-related deaths by ~{(1 - renewable_avg/fossil_avg)*100:.0f}%**")

# Tab 3: Interactive Compare
with tab3:
    st.subheader("Compare Any Two Energy Sources")

    col1, col2 = st.columns(2)

    with col1:
        source1 = st.selectbox(
            "First energy source:",
            options=full_data['energy_source'].tolist(),
            index=full_data['energy_source'].tolist().index('Coal')
        )

    with col2:
        source2 = st.selectbox(
            "Second energy source:",
            options=full_data['energy_source'].tolist(),
            index=full_data['energy_source'].tolist().index('Solar')
        )

    if source1 and source2:
        with EnergyDeathsDatabase() as db:
            comparison = db.get_comparison(source1, source2)

        if comparison:
            st.markdown("---")

            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                color1 = "#ef4444" if comparison['rate1'] > comparison['rate2'] else "#22c55e"
                st.markdown(f"""
                <div style="background: {color1}20; padding: 1.5rem; border-radius: 12px; text-align: center; border: 2px solid {color1};">
                    <h3 style="margin: 0; color: {color1};">{source1}</h3>
                    <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{comparison['rate1']:.3f}</p>
                    <p style="margin: 0; opacity: 0.8;">deaths per TWh</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="padding: 1.5rem; text-align: center;">
                    <p style="font-size: 3rem; font-weight: bold; margin: 0;">vs</p>
                    <p style="font-size: 1.5rem; margin: 0.5rem 0;">
                        <b>{comparison['ratio']:.1f}x</b> difference
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                color2 = "#ef4444" if comparison['rate2'] > comparison['rate1'] else "#22c55e"
                st.markdown(f"""
                <div style="background: {color2}20; padding: 1.5rem; border-radius: 12px; text-align: center; border: 2px solid {color2};">
                    <h3 style="margin: 0; color: {color2};">{source2}</h3>
                    <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{comparison['rate2']:.3f}</p>
                    <p style="margin: 0; opacity: 0.8;">deaths per TWh</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Visual comparison
            compare_df = pd.DataFrame({
                'source': [source1, source2],
                'deaths': [comparison['rate1'], comparison['rate2']]
            })

            fig = px.bar(
                compare_df,
                x='source',
                y='deaths',
                color='source',
                color_discrete_sequence=['#ef4444' if comparison['rate1'] > comparison['rate2'] else '#22c55e',
                                         '#22c55e' if comparison['rate1'] > comparison['rate2'] else '#ef4444'],
                labels={'deaths': 'Deaths per TWh', 'source': ''}
            )

            fig.update_layout(
                height=350,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

            # Interpretation
            safer = comparison['safer']
            more_deadly = source1 if safer == source2 else source2
            ratio = comparison['ratio'] if comparison['rate1'] > comparison['rate2'] else 1/comparison['ratio']

            if ratio > 100:
                st.error(f"**{more_deadly}** is **{ratio:.0f}x more deadly** than **{safer}**. This is an enormous difference in safety.")
            elif ratio > 10:
                st.warning(f"**{more_deadly}** is **{ratio:.0f}x more deadly** than **{safer}**. A significant safety gap.")
            elif ratio > 2:
                st.info(f"**{more_deadly}** is **{ratio:.1f}x more deadly** than **{safer}**.")
            else:
                st.success(f"**{source1}** and **{source2}** have similar death rates.")

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("☀️", "Study 1: Solar is Safest",
            "<b>Solar power</b> has the lowest death rate at just <b>0.019 deaths per TWh</b> - making it the safest energy source.",
            "Deaths mainly from manufacturing and installation accidents, not operation."),
        ResearchStudy("☢️", "Study 2: Nuclear's Surprise Safety",
            "Despite Chernobyl and Fukushima, <b>nuclear</b> is the <b>2nd safest</b> at <b>0.03 deaths/TWh</b> - safer than hydropower.",
            "Even worst-case estimates including all possible future deaths keep nuclear extremely safe per TWh generated."),
        ResearchStudy("🏭", "Study 3: Coal's Hidden Toll",
            "<b>Coal kills 24-33 people per TWh</b> - over <b>1,000x more</b> than solar or nuclear.",
            "Most deaths from air pollution causing heart disease, lung cancer, and respiratory illness - not mining accidents."),
        ResearchStudy("💨", "Study 4: Air Pollution Dominates",
            "<b>Over 99%</b> of fossil fuel deaths are from <b>air pollution</b>, not accidents.",
            "PM2.5 particles from burning fossil fuels cause millions of premature deaths globally each year."),
        ResearchStudy("🌊", "Study 5: Hydropower's Dam Problem",
            "<b>Hydropower</b> (1.3/TWh) is the most deadly renewable due to <b>catastrophic dam failures</b>.",
            "The 1975 Banqiao Dam failure in China killed 85,000-240,000 people in a single event."),
    ])

    st.markdown("### Key Takeaways")
    takeaways = [
        "The safest energy sources are solar, nuclear, and wind",
        "Fossil fuels kill through air pollution, not just accidents",
        "Transitioning to clean energy would save millions of lives",
        "Even hydropower is 20x safer than coal"
    ]
    for t in takeaways:
        st.markdown(f"- {t}")

    st.markdown("### Data Sources")
    sources = [
        "**Fossil fuels**: Markandya, A., & Wilkinson, P. (2007) - The Lancet",
        "**Solar & Wind**: Sovacool et al. (2016) - accident database analysis",
        "**Nuclear**: Our World in Data estimates including Chernobyl & Fukushima",
        "**Hydropower**: Historical dam failure database (1965-present)"
    ]
    for s in sources:
        st.markdown(f"- {s}")

# Tab 5: Raw Data
with tab5:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Full Dataset", "By Safety (safest first)", "Category Summary"],
        horizontal=True
    )

    if data_view == "Full Dataset":
        display_data = full_data.copy()
        display_data.columns = ['Energy Source', 'Year', 'Deaths/TWh', 'Category', 'Safety Tier', 'Relative Danger', 'Safety Rank']
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "energy_deaths_full.csv", "text/csv")

    elif data_view == "By Safety (safest first)":
        display_data = by_safety.copy()
        display_data.columns = ['Energy Source', 'Year', 'Deaths/TWh', 'Category', 'Safety Tier', 'Relative Danger', 'Safety Rank']
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "energy_deaths_by_safety.csv", "text/csv")

    else:
        display_data = category_summary.copy()
        display_data.columns = ['Category', 'Sources', 'Avg Deaths', 'Min Deaths', 'Max Deaths']
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        csv = display_data.to_csv(index=False)
        st.download_button("Download CSV", csv, "energy_deaths_categories.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Coal", "Nuclear"),
        ("Gas", "Solar"),
        ("Hydropower", "Wind"),
    ],
    data=full_data,
    name_column="energy_source",
    value_column="deaths_per_twh",
    title="Test Your Energy Safety Knowledge",
    prompt="Can you guess which energy source causes MORE deaths per TWh?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """energy_deaths ────────┐
* energy_source (PK)  │    category_summary
* year                ├──▶ * category (PK)
* deaths_per_twh      │    * avg_deaths
* category            │    * min_deaths
* safety_tier         │    * max_deaths
* relative_danger     │
* safety_rank         │"""

SAMPLE_QUERIES = """-- Rank by safety
SELECT energy_source, deaths_per_twh, category
FROM energy_deaths
ORDER BY deaths_per_twh ASC;

-- Category averages
SELECT category, avg_deaths
FROM category_summary
ORDER BY avg_deaths DESC;

-- Fossil vs Renewable ratio
SELECT
    (SELECT AVG(deaths_per_twh) FROM energy_deaths WHERE category = 'Fossil Fuels') /
    (SELECT AVG(deaths_per_twh) FROM energy_deaths WHERE category = 'Renewables')
    AS fossil_to_renewable_ratio;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["9 energy sources", "Multiple research sources", "Air pollution + accidents", "Relative danger metrics"]
)

# Footer
render_data_footer(
    data_sources=["Markandya & Wilkinson (2007)", "Sovacool et al. (2016)", "Our World in Data"],
    time_period="2021 estimates",
    data_points=f"{stats['sources']} energy sources",
    credits={"Research": "Multiple sources", "Compilation": "Our World in Data"},
    dataset_url="https://ourworldindata.org/safest-sources-of-energy"
)

# Site Footer
render_site_footer()
