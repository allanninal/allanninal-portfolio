"""
Data Analysis Module

Provides analytical functions and insights for the media perception dataset.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from src.load.database import DatabaseManager


@dataclass
class InsightResult:
    """Container for analysis insights."""
    title: str
    description: str
    data: pd.DataFrame
    key_stat: str


def get_perception_gap_ranking() -> pd.DataFrame:
    """
    Get causes ranked by their perception gap.

    Returns:
        DataFrame with causes ranked by how much media coverage
        differs from actual death share.
    """
    with DatabaseManager() as db:
        return db.query("""
            SELECT
                cause_name,
                category,
                ROUND(avg_share_deaths, 2) as avg_deaths_pct,
                ROUND(avg_share_media, 2) as avg_media_pct,
                ROUND(avg_gap, 2) as perception_gap,
                CASE
                    WHEN avg_gap > 5 THEN 'Over-covered'
                    WHEN avg_gap < -5 THEN 'Under-covered'
                    ELSE 'Fairly covered'
                END as coverage_status
            FROM v_cause_summary
            ORDER BY avg_gap DESC
        """)


def get_terrorism_911_impact() -> InsightResult:
    """
    Analyze the impact of 9/11 on terrorism coverage.

    Returns:
        InsightResult with terrorism coverage before/after 9/11.
    """
    with DatabaseManager() as db:
        data = db.query("""
            SELECT
                year,
                share_deaths,
                share_nyt,
                share_guardian,
                share_media_avg,
                gap_media_avg
            FROM v_metrics_full
            WHERE cause_name = 'Terrorism'
            ORDER BY year
        """)

    pre_911 = data[data["year"] < 2001]["share_media_avg"].mean()
    post_911 = data[data["year"] >= 2001]["share_media_avg"].mean()
    peak_year = data.loc[data["share_media_avg"].idxmax(), "year"]
    peak_coverage = data["share_media_avg"].max()

    return InsightResult(
        title="Terrorism & 9/11 Impact",
        description=(
            f"Terrorism media coverage averaged {pre_911:.1f}% before 2001, "
            f"then jumped to {post_911:.1f}% after 9/11. "
            f"Peak coverage was {peak_coverage:.1f}% in {int(peak_year)}."
        ),
        data=data,
        key_stat=f"{post_911/pre_911:.1f}x increase post-9/11"
    )


def get_heart_disease_paradox() -> InsightResult:
    """
    Analyze the heart disease coverage paradox.

    Heart disease is the #1 killer but receives minimal coverage.
    """
    with DatabaseManager() as db:
        data = db.query("""
            SELECT
                year,
                share_deaths,
                share_nyt,
                share_guardian,
                share_media_avg,
                gap_media_avg
            FROM v_metrics_full
            WHERE cause_name = 'Heart disease'
            ORDER BY year
        """)

    avg_deaths = data["share_deaths"].mean()
    avg_coverage = data["share_media_avg"].mean()
    coverage_ratio = avg_coverage / avg_deaths

    return InsightResult(
        title="Heart Disease Paradox",
        description=(
            f"Heart disease causes {avg_deaths:.1f}% of deaths but receives only "
            f"{avg_coverage:.1f}% of media coverage - a {coverage_ratio:.1%} coverage ratio. "
            f"It's the #1 killer but among the least covered."
        ),
        data=data,
        key_stat=f"Only {coverage_ratio:.0%} of fair coverage"
    )


def get_violence_vs_disease_comparison() -> InsightResult:
    """
    Compare coverage of violence-related deaths vs chronic diseases.
    """
    with DatabaseManager() as db:
        data = db.query("""
            SELECT
                category,
                SUM(share_deaths) / COUNT(DISTINCT year) as avg_deaths,
                SUM(share_media_avg) / COUNT(DISTINCT year) as avg_media
            FROM v_metrics_full
            WHERE category IN ('violence', 'chronic_disease')
            GROUP BY category
        """)

    violence = data[data["category"] == "violence"].iloc[0]
    chronic = data[data["category"] == "chronic_disease"].iloc[0]

    violence_ratio = violence["avg_media"] / violence["avg_deaths"]
    chronic_ratio = chronic["avg_media"] / chronic["avg_deaths"]

    return InsightResult(
        title="Violence vs Chronic Disease Coverage",
        description=(
            f"Violence-related deaths (homicide, terrorism) cause {violence['avg_deaths']:.1f}% "
            f"of deaths but get {violence['avg_media']:.1f}% of coverage ({violence_ratio:.0f}x over-represented). "
            f"Chronic diseases cause {chronic['avg_deaths']:.1f}% of deaths but get only "
            f"{chronic['avg_media']:.1f}% of coverage ({chronic_ratio:.1%} under-represented)."
        ),
        data=data,
        key_stat=f"Violence: {violence_ratio:.0f}x over-covered"
    )


def get_google_vs_media_correlation() -> InsightResult:
    """
    Analyze correlation between Google searches and media coverage.
    """
    with DatabaseManager() as db:
        data = db.query("""
            SELECT
                cause_name,
                AVG(share_google) as avg_google,
                AVG(share_nyt) as avg_nyt,
                AVG(share_guardian) as avg_guardian,
                AVG(share_deaths) as avg_deaths
            FROM v_metrics_full
            WHERE share_google IS NOT NULL
            GROUP BY cause_name
        """)

    google_media_corr = data["avg_google"].corr(data["avg_nyt"])
    google_deaths_corr = data["avg_google"].corr(data["avg_deaths"])

    return InsightResult(
        title="Google Searches vs Reality",
        description=(
            f"Google searches correlate {google_media_corr:.2f} with NYT coverage "
            f"and {google_deaths_corr:.2f} with actual deaths. "
            f"People search for what media covers, not what kills."
        ),
        data=data,
        key_stat=f"r={google_media_corr:.2f} with media"
    )


def get_yearly_trends() -> pd.DataFrame:
    """Get yearly trends in coverage patterns."""
    with DatabaseManager() as db:
        return db.query("""
            SELECT
                year,
                cause_name,
                share_deaths,
                share_media_avg,
                gap_media_avg
            FROM v_metrics_full
            ORDER BY year, cause_name
        """)


def get_key_statistics() -> Dict:
    """Get key statistics for dashboard summary."""
    with DatabaseManager() as db:
        summary = db.get_cause_summary()

    most_overcovered = summary.loc[summary["avg_gap"].idxmax()]
    most_undercovered = summary.loc[summary["avg_gap"].idxmin()]
    biggest_killer = summary.loc[summary["avg_share_deaths"].idxmax()]

    return {
        "most_overcovered": {
            "cause": most_overcovered["cause_name"],
            "gap": round(most_overcovered["avg_gap"], 1),
        },
        "most_undercovered": {
            "cause": most_undercovered["cause_name"],
            "gap": round(most_undercovered["avg_gap"], 1),
        },
        "biggest_killer": {
            "cause": biggest_killer["cause_name"],
            "share": round(biggest_killer["avg_share_deaths"], 1),
        },
        "total_causes": len(summary),
        "over_covered_count": (summary["avg_gap"] > 5).sum(),
        "under_covered_count": (summary["avg_gap"] < -5).sum(),
    }


if __name__ == "__main__":
    print("Running analysis module...\n")

    # Run all analyses
    print("=" * 60)
    print("PERCEPTION GAP RANKING")
    print("=" * 60)
    print(get_perception_gap_ranking().to_string())

    print("\n" + "=" * 60)
    insights = [
        get_terrorism_911_impact(),
        get_heart_disease_paradox(),
        get_violence_vs_disease_comparison(),
        get_google_vs_media_correlation(),
    ]

    for insight in insights:
        print(f"\n{insight.title}")
        print("-" * 40)
        print(insight.description)
        print(f"Key stat: {insight.key_stat}")

    print("\n" + "=" * 60)
    print("KEY STATISTICS")
    print("=" * 60)
    stats = get_key_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
