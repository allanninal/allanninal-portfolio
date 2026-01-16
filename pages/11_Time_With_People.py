"""
Time With People Dashboard
Exploring how Americans spend their time with others across the lifespan (2009-2019)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.time_with_people.database import TimeWithPeopleDatabase
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
    page_title="Time With People | Allan Ninal",
    page_icon="",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load time use data from database."""
    with TimeWithPeopleDatabase() as db:
        time_by_age = db.get_time_by_age()
        companion_summary = db.get_companion_summary()
        age_group_summary = db.get_age_group_summary()
        long_format = db.get_long_format()
        stats = db.get_stats()
    return time_by_age, companion_summary, age_group_summary, long_format, stats


# Load data
time_by_age, companion_summary, age_group_summary, long_format, stats = load_data()

# Setup page with theme and sidebar
setup_page("Time With People", icon="👥", tech_tags=["Python", "DuckDB", "Streamlit", "Plotly", "pandas"])

# Site header
render_site_header()

# Additional page-specific styles
st.markdown("""
<style>
    .milestone-box {
        background: var(--surface-bg);
        border: 1px solid var(--border-color);
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header
render_hero_header(
    title="Who Americans Spend Time With",
    subtitle="From teenage years to old age, who we spend our time with changes dramatically.",
    data_badge="📅 Data: 2009-2019 | Ages 15-85 | American Time Use Survey"
)

# Key insight banner
render_shocking_fact(
    value="8+ hours/day",
    description="Time spent <b>alone increases steadily</b> throughout life, from ~3 hours/day at age 15 to <b>over 8 hours/day by age 85</b>. Meanwhile, time with friends drops from nearly 2 hours/day to under 40 minutes.",
    style="primary"
)

st.markdown("---")

# Calculate key stats
elder_alone = time_by_age[time_by_age['age'] == 85]['alone'].iloc[0]
peak_children = companion_summary[companion_summary['companion'] == 'Children']['peak_age'].iloc[0]
friends_teen = time_by_age[time_by_age['age'] == 15]['friends'].iloc[0]
partner_peak = companion_summary[companion_summary['companion'] == 'Partner']['peak_age'].iloc[0]

# Hero Stats using shared component
render_hero_stats([
    HeroStat(f"{elder_alone/60:.1f}h", f"Peak Alone Time<br>At age {stats['peak_alone_age']}", "secondary"),
    HeroStat(f"Age {int(peak_children)}", "Peak Child Time<br>~4 hours/day", "success"),
    HeroStat(f"{friends_teen:.0f}", "Minutes w/ Friends<br>At age 15", "warning"),
    HeroStat(f"Age {int(partner_peak)}", "Peak Partner Time<br>After retirement", "danger"),
])

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Life Curves", "Milestones", "Age Groups",
    "Research Findings", "Explorer", "Raw Data"
])

# Tab 1: Life Curves (main visualization)
with tab1:
    st.subheader("Time Spent With Others Across the Lifespan")

    # Create the famous "Who we spend time with" visualization
    companion_colors = {
        'Alone': '#6366f1',
        'Children': '#10b981',
        'Coworkers': '#64748b',
        'Family': '#22c55e',
        'Friends': '#f59e0b',
        'Other': '#94a3b8',
        'Partner': '#ec4899',
    }

    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_companions = st.multiselect(
            "Select companions to display:",
            options=['Alone', 'Children', 'Coworkers', 'Family', 'Friends', 'Partner'],
            default=['Alone', 'Children', 'Family', 'Friends', 'Partner'],
            key="life_curves_companions"
        )

    with col2:
        show_hours = st.checkbox("Show in hours (instead of minutes)", value=False)

    if selected_companions:
        filtered_long = long_format[long_format['companion'].isin(selected_companions)]

        if show_hours:
            filtered_long = filtered_long.copy()
            filtered_long['minutes'] = filtered_long['minutes'] / 60
            y_title = "Hours per day"
        else:
            y_title = "Minutes per day"

        fig = px.line(
            filtered_long,
            x='age',
            y='minutes',
            color='companion',
            color_discrete_map=companion_colors,
            labels={'age': 'Age', 'minutes': y_title, 'companion': 'With'},
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
            xaxis=dict(dtick=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        fig.update_traces(line_width=3)

        st.plotly_chart(fig, use_container_width=True)

        # Narrative insights
        st.markdown("### Key Observations")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Childhood & Teen Years (15-18)**
            - Family time dominates (~4.5 hours/day)
            - Friends are a close second
            - Very little time with partner or children
            - Alone time starts at ~3 hours/day
            """)

            st.markdown("""
            **Young Adulthood (20-35)**
            - Partner time rises sharply after age 20
            - Time with children peaks around age 35
            - Coworker time at its maximum
            - Friends start to decline
            """)

        with col2:
            st.markdown("""
            **Middle Age (40-60)**
            - Children time gradually decreases
            - Alone time continues steady rise
            - Family time relatively stable
            - Coworker time starts declining post-50

            """)

            st.markdown("""
            **Senior Years (60+)**
            - Alone time accelerates upward
            - Partner time becomes dominant social time
            - Friends, family, coworkers all minimal
            - By 80+, alone time exceeds 8 hours/day
            """)

# Tab 2: Milestones
with tab2:
    st.subheader("Life Milestones in Time Use")

    st.markdown("""
    Certain ages mark significant shifts in who we spend our time with.
    These milestones reflect major life transitions.
    """)

    milestones = [
        {"age": 18, "event": "Leaving Family", "desc": "Time with family drops sharply as young adults move out"},
        {"age": 22, "event": "Partner Time Rises", "desc": "Romantic relationships become significant time investments"},
        {"age": 30, "event": "Peak Coworker Time", "desc": "Career establishment means maximum time with colleagues"},
        {"age": 35, "event": "Peak Children Time", "desc": "Parenting young children demands the most time"},
        {"age": 40, "event": "Friends Decline", "desc": "Time with friends drops below 1 hour/day"},
        {"age": 50, "event": "Children Leave", "desc": "Empty nest begins; children time drops significantly"},
        {"age": 65, "event": "Retirement Transition", "desc": "Coworker time nearly disappears; partner time rises"},
        {"age": 75, "event": "Solitude Dominates", "desc": "Alone time exceeds all social time combined"},
    ]

    for m in milestones:
        age_data = time_by_age[time_by_age['age'] == m['age']]
        if len(age_data) > 0:
            row = age_data.iloc[0]
            st.markdown(f"""
            <div class="milestone-box">
                <strong style="font-size: 1.1rem;">Age {m['age']}: {m['event']}</strong>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">{m['desc']}</p>
                <small style="opacity: 0.6;">Alone: {row['alone']:.0f} min | Partner: {row['partner']:.0f} min | Children: {row['children']:.0f} min | Friends: {row['friends']:.0f} min</small>
            </div>
            """, unsafe_allow_html=True)

    # Crossover visualization
    st.subheader("When Time Alone Exceeds Social Time")

    # Calculate total social time
    time_by_age_plot = time_by_age.copy()
    time_by_age_plot['social'] = (time_by_age_plot['children'] + time_by_age_plot['coworkers'] +
                                   time_by_age_plot['family'] + time_by_age_plot['friends'] +
                                   time_by_age_plot['partner'])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=time_by_age_plot['age'],
        y=time_by_age_plot['alone'],
        name='Alone',
        line=dict(color='#6366f1', width=3),
        fill='tonexty'
    ))

    fig.add_trace(go.Scatter(
        x=time_by_age_plot['age'],
        y=time_by_age_plot['social'],
        name='All Social',
        line=dict(color='#10b981', width=3),
        fill='tozeroy'
    ))

    # Find crossover point
    crossover = time_by_age_plot[time_by_age_plot['alone'] > time_by_age_plot['social']]['age'].min()

    fig.add_vline(x=crossover, line_dash="dash", line_color="red",
                  annotation_text=f"Crossover at age {crossover}")

    fig.update_layout(
        height=400,
        xaxis_title="Age",
        yaxis_title="Minutes per day",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(f"Around age **{crossover}**, Americans spend more time alone than with all other people combined.")

# Tab 3: Age Groups
with tab3:
    st.subheader("Time Use by Life Stage")

    # Heatmap of time by age group and companion
    pivot_data = age_group_summary.set_index('age_group')[['alone', 'children', 'coworkers', 'family', 'friends', 'partner']]

    # Rename columns for display
    pivot_data.columns = ['Alone', 'Children', 'Coworkers', 'Family', 'Friends', 'Partner']

    fig = px.imshow(
        pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale='RdYlGn_r',
        labels={'color': 'Minutes/day'},
        aspect='auto'
    )

    fig.update_layout(
        height=400,
        xaxis_title="",
        yaxis_title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Add text annotations
    for i, row in enumerate(pivot_data.values):
        for j, val in enumerate(row):
            fig.add_annotation(
                x=j, y=i,
                text=f"{val:.0f}",
                showarrow=False,
                font=dict(color='white' if val > 150 else 'black', size=12)
            )

    st.plotly_chart(fig, use_container_width=True)

    # Bar chart comparison
    st.subheader("Total Social Time by Life Stage")

    fig = px.bar(
        age_group_summary,
        x='age_group',
        y='total_social',
        color='total_social',
        color_continuous_scale='Viridis',
        labels={'age_group': 'Life Stage', 'total_social': 'Total Social Minutes/Day'}
    )

    fig.update_layout(
        height=350,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.subheader("Detailed Age Group Statistics")
    display_df = age_group_summary.copy()
    display_df.columns = ['Life Stage', 'Age Range', 'Alone', 'Children', 'Coworkers', 'Family', 'Friends', 'Partner', 'Total Social']

    # Format numeric columns
    for col in ['Alone', 'Children', 'Coworkers', 'Family', 'Friends', 'Partner', 'Total Social']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.0f} min")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Tab 4: Research Findings
with tab4:
    render_research_studies([
        ResearchStudy("📈", "Study 1: The Rise of Solitude",
            "Time spent alone increases <b>monotonically</b> from age 15 to 85, roughly <b>doubling</b> over the lifespan from ~3 hours to 8+ hours daily.",
            "Aging populations face increasing isolation. Social programs and community infrastructure should address the growing solitude of older adults."),
        ResearchStudy("👶", "Study 2: The Parenting Peak",
            "Peak time with children occurs around <b>age 35</b>, coinciding with raising young children. Parents spend approximately <b>4 hours/day</b> with children at this stage.",
            "Work-life balance policies have their greatest impact during this intense parenting phase when time demands are highest."),
        ResearchStudy("👫", "Study 3: The Friendship Decline",
            "Time with friends declines steadily after teenage years, from <b>~110 min/day at 15</b> to <b>~35 min/day at 80</b> - a 70% reduction.",
            "Maintaining friendships requires intentional effort as life progresses. The dramatic decline suggests competing demands crowd out friendship time."),
        ResearchStudy("💕", "Study 4: The Partner U-Curve",
            "Partner time shows an interesting <b>U-shape</b>: rising in 20s, stable during parenting years, then rising again post-retirement to become the dominant social relationship.",
            "Retirement represents a major shift in relationship dynamics, with partners becoming each other's primary companions."),
        ResearchStudy("⚖️", "Study 5: The Solitude Crossover",
            "By age <b>75</b>, alone time exceeds <b>all social time combined</b>. This crossover marks a fundamental shift in daily life structure.",
            "Policy interventions targeting social connection may be most critical after this crossover point when isolation becomes the norm."),
    ])

    st.markdown("### Methodology")
    methods = [
        "Data from American Time Use Survey (ATUS) 2009-2019, pooled using population weights",
        "Time measured in minutes per day with various companions present during activities",
        "People can be counted in multiple categories (e.g., party with friends and spouse counts for both)",
        "Sleeping and grooming excluded from analysis",
        "Original analysis and visualization inspired by Henrik Lindberg's work"
    ]
    for method in methods:
        st.markdown(f"- {method}")

    st.markdown("### Limitations")
    limitations = [
        "Data is US-specific and may not generalize to other cultures",
        "Cross-sectional data (different people at each age) not longitudinal",
        "Self-reported time use may have recall biases",
        "Categories like 'alone' include time with pets"
    ]
    for limitation in limitations:
        st.markdown(f"- {limitation}")

# Tab 5: Explorer
with tab5:
    st.subheader("Explore Time Use at Any Age")

    selected_age = st.slider("Select an age:", min_value=15, max_value=85, value=35)

    age_data = time_by_age[time_by_age['age'] == selected_age]

    if len(age_data) > 0:
        row = age_data.iloc[0]

        # Create pie chart
        companions = ['Alone', 'Children', 'Coworkers', 'Family', 'Friends', 'Partner', 'Other']
        values = [row['alone'], row['children'], row['coworkers'], row['family'],
                  row['friends'], row['partner'], row['other']]
        colors = ['#6366f1', '#10b981', '#64748b', '#22c55e', '#f59e0b', '#ec4899', '#94a3b8']

        col1, col2 = st.columns([1, 1])

        with col1:
            fig = go.Figure(data=[go.Pie(
                labels=companions,
                values=values,
                hole=0.4,
                marker_colors=colors
            )])

            fig.update_layout(
                height=400,
                title=f"Time Distribution at Age {selected_age}",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(f"### At Age {selected_age}")

            # Show each companion type
            for comp, val, color in zip(companions, values, colors):
                hours = val / 60
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div style="width: 12px; height: 12px; background: {color}; border-radius: 2px; margin-right: 8px;"></div>
                    <span><strong>{comp}:</strong> {val:.0f} min ({hours:.1f} hours)</span>
                </div>
                """, unsafe_allow_html=True)

            total = sum(values)
            st.markdown(f"**Total accounted:** {total:.0f} min ({total/60:.1f} hours)")

    # Compare two ages
    st.subheader("Compare Two Ages")
    col1, col2 = st.columns(2)

    with col1:
        age1 = st.selectbox("First age:", options=list(range(15, 86)), index=5, key="compare_age1")

    with col2:
        age2 = st.selectbox("Second age:", options=list(range(15, 86)), index=50, key="compare_age2")

    if age1 != age2:
        data1 = time_by_age[time_by_age['age'] == age1].iloc[0]
        data2 = time_by_age[time_by_age['age'] == age2].iloc[0]

        companions = ['alone', 'children', 'coworkers', 'family', 'friends', 'partner']
        comparison_df = pd.DataFrame({
            'Companion': [c.title() for c in companions],
            f'Age {age1}': [data1[c] for c in companions],
            f'Age {age2}': [data2[c] for c in companions],
        })

        comparison_df['Difference'] = comparison_df[f'Age {age2}'] - comparison_df[f'Age {age1}']

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=f'Age {age1}',
            x=comparison_df['Companion'],
            y=comparison_df[f'Age {age1}'],
            marker_color='#3b82f6'
        ))

        fig.add_trace(go.Bar(
            name=f'Age {age2}',
            x=comparison_df['Companion'],
            y=comparison_df[f'Age {age2}'],
            marker_color='#ef4444'
        ))

        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_title="",
            yaxis_title="Minutes per day",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True)

# Tab 6: Raw Data
with tab6:
    st.subheader("Raw Data")

    data_view = st.radio(
        "Select data view:",
        ["Time by Age", "Companion Summary", "Age Group Summary"],
        horizontal=True
    )

    if data_view == "Time by Age":
        st.dataframe(time_by_age, use_container_width=True, hide_index=True)
        csv = time_by_age.to_csv(index=False)
        st.download_button("Download CSV", csv, "time_by_age.csv", "text/csv")

    elif data_view == "Companion Summary":
        st.dataframe(companion_summary, use_container_width=True, hide_index=True)
        csv = companion_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "companion_summary.csv", "text/csv")

    else:
        st.dataframe(age_group_summary, use_container_width=True, hide_index=True)
        csv = age_group_summary.to_csv(index=False)
        st.download_button("Download CSV", csv, "age_group_summary.csv", "text/csv")

st.markdown("---")

# Quiz Section
render_quiz_section(
    questions=[
        ("Alone", "Friends"),  # At age 40, which is higher?
        ("Partner", "Coworkers"),  # At age 65, which is higher?
        ("Children", "Family"),  # At age 35, which is higher?
    ],
    data=companion_summary,
    name_column="companion",
    value_column="avg_minutes",
    title="Test Your Time Perception",
    prompt="🎯 Can you guess which companion group gets more average daily time?"
)

st.markdown("---")

# Technical Section
SCHEMA_DIAGRAM = """time_by_age ────────┐
• age (PK)          │    companion_summary
• alone             ├───▶ • companion (PK)
• children          │    • avg_minutes
• coworkers         │    • peak_age
• family            │    • min_minutes
• friends           │    • max_minutes
• partner           │
• other             │    age_group_summary
                    └───▶ • age_group (PK)
                         • age_range
                         • total_social"""

SAMPLE_QUERIES = """-- Time alone by age
SELECT age, alone,
       ROUND(alone / 60.0, 1) as hours_alone
FROM time_by_age
WHERE age IN (15, 35, 55, 75, 85);

-- Peak ages for each companion type
SELECT companion, peak_age,
       ROUND(max_minutes, 0) as peak_minutes
FROM companion_summary
ORDER BY peak_age;

-- Life stages with most social time
SELECT age_group, age_range,
       ROUND(total_social, 0) as social_minutes
FROM age_group_summary
ORDER BY total_social DESC;"""

render_technical_section(
    schema_diagram=SCHEMA_DIAGRAM,
    sample_queries=SAMPLE_QUERIES,
    features=["Age-based time series analysis", "Companion category aggregation", "Life stage classification", "Cross-sectional data pooling"]
)

# Footer
render_data_footer(
    data_sources=["Bureau of Labor Statistics", "American Time Use Survey (ATUS)"],
    time_period="2009 - 2019\nAges 15-85",
    data_points=f"{stats['total_records']} records across {stats['companions']} companion types",
    credits={"Original visualization": "Henrik Lindberg", "Data processing": "BLS ATUS"},
    dataset_url="https://www.bls.gov/tus/datafiles-0319.htm"
)

# Site footer
render_site_footer()
