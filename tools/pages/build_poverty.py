#!/usr/bin/env python3
"""Regenerate projects/poverty-analysis.html from data/ph-poverty CSVs.

    .venv/bin/python tools/pages/build_poverty.py

The page it replaces carried a P188 average daily agricultural wage from 2015, a
P107K farm income from 2002-03 and a 35.7M employment figure from 2016 -- three
figures a decade or more apart, all from PSA surveys that are not fetchable. Nine
of its twelve chart arrays were perfectly monotone.

The national series the World Bank republishes from those same surveys IS open,
so the page covers that and states plainly that everything regional is gone.

One property drives the whole design: these come from household surveys run every
few years, not annually. Fourteen survey points across thirty-eight years. Any
chart that draws them as a smooth line is inventing the years between, so the
distribution charts plot points on a real time axis.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-poverty"
PAGE = "projects/poverty-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_poverty_annual")
    surv = rows("ph_poverty_surveys")
    asean = rows("ph_poverty_asean")
    last = lambda c: [r for r in ann if f(r[c]) is not None][-1]
    first = lambda c: [r for r in ann if f(r[c]) is not None][0]
    ph = [r for r in asean if r["country"] == "Philippines"][0]

    F = dict(
        nat=r(f(last("poverty_national_pct")["poverty_national_pct"]), 1),
        year=last("poverty_national_pct")["year"],
        nat0=r(f(first("poverty_national_pct")["poverty_national_pct"]), 1),
        nat0y=first("poverty_national_pct")["year"],
        p365=r(f(last("poverty_365usd_pct")["poverty_365usd_pct"]), 1),
        p215=r(f(last("poverty_215usd_pct")["poverty_215usd_pct"]), 1),
        gini=r(f(last("gini")["gini"]), 1),
        gini0=r(f(first("gini")["gini"]), 1), gini0y=first("gini")["year"],
        bot=r(f(last("income_share_bottom_20")["income_share_bottom_20"]), 1),
        top=r(f(last("income_share_top_10")["income_share_top_10"]), 1),
        vuln=r(f(last("vulnerable_employment_pct")["vulnerable_employment_pct"]), 1),
        unemp=r(f(last("unemployment_pct")["unemployment_pct"]), 2),
        gni=int(f(last("gni_per_capita_usd")["gni_per_capita_usd"])),
        nsurv=len(surv),
        span=max(int(r["survey_year"]) for r in surv)
        - min(int(r["survey_year"]) for r in surv),
        ayear=asean[0]["year"], an=len(asean),
        aphgini=f(ph["gini"]),
        arank=sum(1 for r in asean if f(r["gini"]) >= f(ph["gini"])),
    )
    F["ginichange"] = r(F["gini"] - F["gini0"], 1)
    F["ratio"] = r(F["top"] / F["bot"], 1)

    p = Page(PAGE)
    p.hero('''                <h1>Poverty, And The Jobs That Do Not Fix It</h1>
                <p class="hero-description">
                    Unemployment is <span>{unemp}%</span> &mdash; near the lowest on
                    record. <span>{vuln}%</span> of workers are in vulnerable
                    employment: own-account and unpaid family work, without a wage or a
                    contract. Almost everyone has work. That is a different thing from
                    almost everyone having a job.
                </p>

                <div class="header-actions">
                    <a href="https://data.worldbank.org/country/philippines" target="_blank" class="btn btn-primary">
                        World Bank poverty data
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="pov.national">{nat}%</div>
                        <div class="stat-label">Below the national poverty line ({year})</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="pov.vulnerable">{vuln}%</div>
                        <div class="stat-label">In vulnerable employment</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="pov.unemployment">{unemp}%</div>
                        <div class="stat-label">Unemployment</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="pov.gini">{gini}</div>
                        <div class="stat-label">Gini coefficient</div>
                    </div>
                </div>
'''.format(**F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The gap between <span data-fact="pov.unemployment">{unemp}%</span> unemployment and <span data-fact="pov.vulnerable">{vuln}%</span> vulnerable employment is the whole story. Work is not scarce here; paid, secure work is.</p>
                    <ul class="tldr-list">
                        <li><span data-fact="pov.national">{nat}%</span> of Filipinos live below the national poverty line, down from <span data-fact="pov.national.first">{nat0}%</span> in {nat0y}. On the World Bank's $3.65-a-day line it is <span data-fact="pov.365">{p365}%</span>.</li>
                        <li>Inequality has barely moved. The Gini coefficient is <span data-fact="pov.gini">{gini}</span> against <span data-fact="pov.gini.first">{gini0}</span> in {gini0y} &mdash; a change of <span data-fact="pov.gini.change">{ginichange}</span> across {span} years of surveys.</li>
                        <li>The poorest fifth of the country receives <span data-fact="pov.bottom20">{bot}%</span> of income. The richest tenth receives <span data-fact="pov.top10">{top}%</span> &mdash; <span data-fact="pov.ratio">{ratio}</span> times as much, spread over half as many people.</li>
                        <li>These come from household surveys run every few years: <span data-fact="pov.surveys">{nsurv}</span> points across {span} years. The charts plot points on a real time axis rather than a smooth line, because the years between were never measured.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Full Employment, Without The Jobs",
                "Two labour figures that are both true and appear to contradict each "
                "other. Unemployment counts people looking for work and not finding it. "
                "Vulnerable employment counts own-account and unpaid family workers "
                "&mdash; people working, without a wage, a contract or any of what "
                "usually comes with a job.",
                [("Unemployment", "{unemp}%".format(**F), "pov.unemployment",
                  "Near the lowest on record. On this measure alone the labour market "
                  "looks excellent."),
                 ("Vulnerable employment", "{vuln}%".format(**F), "pov.vulnerable",
                  "A third of everyone working. Neither unemployed nor securely "
                  "employed, and invisible to the headline rate."),
                 ("Why both matter", "&mdash;", None,
                  "A country can approach full employment and stay poor if the work is "
                  "unpaid or informal. Reporting the first number without the second is "
                  "the most common way to make this look better than it is.")],
                "Unemployment against vulnerable employment, %", "labourChart"),
        p.section(2, "Poverty Is Falling",
                "The national poverty rate and the two international lines, at every "
                "year they were measured. This part is unambiguously good.",
                [("National line", "{nat}%".format(**F), "pov.national",
                  "In {y}, down from {n0}% in {n0y}.".format(
                      y=F["year"], n0=F["nat0"], n0y=F["nat0y"])),
                 ("$3.65 a day", "{p365}%".format(**F), "pov.365",
                  "The World Bank's lower-middle-income line, comparable across "
                  "countries."),
                 ("$2.15 a day", "{p215}%".format(**F), "pov.215",
                  "Extreme poverty. Far lower, and the two lines moving differently is "
                  "why quoting only one is misleading.")],
                "Poverty rate by measure, at survey years", "povChart"),
        p.section(3, "Inequality Has Not",
                "The distribution has been close to static for four decades, through "
                "every administration and every growth episode in that period.",
                [("Gini now", "{gini}".format(**F), "pov.gini",
                  "Against {g0} in {g0y} &mdash; a move of {c} in {s} "
                  "years.".format(g0=F["gini0"], g0y=F["gini0y"], c=F["ginichange"],
                                  s=F["span"])),
                 ("Poorest fifth", "{bot}%".format(**F), "pov.bottom20",
                  "Of all income, shared among 20% of the population."),
                 ("Richest tenth", "{top}%".format(**F), "pov.top10",
                  "{r} times as much, among half as many people. That ratio is what the "
                  "Gini number means in practice.".format(r=F["ratio"]))],
                "Income share of the bottom 20% and top 10%, at survey years",
                "distChart"),
        p.section(4, "Against The Region",
                "Five ASEAN economies at {y}, the latest year all of them have both "
                "measures. Comparing each country at its own latest print would put "
                "different years side by side and call the difference a "
                "gap.".format(y=F["ayear"]),
                [("Gini rank", "{arank} of {an}".format(**F), "pov.asean.gini.rank",
                  "At {g} in the comparison year. The Philippines is the most unequal "
                  "of this group.".format(g=F["aphgini"])),
                 ("GNI per capita", "${gni:,}".format(**F), "pov.gni",
                  "A middle-income country by every classification, with a "
                  "lower-middle-income distribution."),
                 ("The uncomfortable pairing", "&mdash;", None,
                  "Poverty falling while inequality holds means growth reached the poor "
                  "&mdash; but reached everyone else at least as much.")],
                "Gini coefficient and $3.65 poverty rate, ASEAN-5", "aseanChart"),
        p.prose(5, "What This Page Does Not Cover",
                      "The version this replaces charted agricultural wages by region, "
                      "the gender wage gap, farm household income composition, rural "
                      "income distribution and regional employment &mdash; using a 2015 "
                      "wage, a 2002-03 farm income and a 2016 employment figure side by "
                      "side as if they described one moment.",
                      [("Everything regional",
                        "PSA's Family Income and Expenditure Survey carries all of it. "
                        "psa.gov.ph sits behind a managed challenge that scripts do not "
                        "pass, so no regional figure appears here at all."),
                       ("Agricultural wages",
                        "Also PSA, and the specific figure the old page led with was a "
                        "decade old when it was published. Nothing replaced it, because "
                        "nothing open carries it."),
                       ("Farm income composition",
                        "The 2002-03 figures the old page used are three surveys out of "
                        "date. A number that old is not wrong so much as no longer about "
                        "the present, and presenting it beside 2016 employment made it "
                        "look current.")]),
        p.prose(6, "Method",
                      "One fetcher, four CSVs, via the shared helper in "
                      "<code>data/_lib/worldbank.py</code>.",
                      [("Surveys, not years",
                        "Poverty and distribution come from household surveys every few "
                        "years. The survey table is published separately from the annual "
                        "panel precisely so nobody joins the dots: {n} points across {s} "
                        "years.".format(n=F["nsurv"], s=F["span"])),
                       ("Nesting checks",
                        "The $3.65 line must always catch at least as many people as the "
                        "$2.15 line, and the bottom fifth must always hold less than the "
                        "top tenth. Both catch a transposed column pair, which otherwise "
                        "produces entirely plausible-looking output."),
                       ("Gaps stay gaps",
                        "Nulls are never forward-filled. The national poverty series has "
                        "four points; drawing it as annual would invent the rest."),
                       ("Two labour measures, always together",
                        "Unemployment and vulnerable employment appear on the same chart "
                        "by design. Either alone gives a badly wrong impression of the "
                        "same labour market."),
                       ("Like-for-like comparison",
                        "The ASEAN table uses the latest year every country has ({y}), "
                        "which is older than the Philippine latest and is labelled as "
                        "such.".format(y=F["ayear"])),
                       ("Verification",
                        "Eight assertions in <code>checks.sql</code>, and every figure "
                        "bound to a query in <code>facts.sql</code>.")]),
    ]

    S.append('''        <section class="section fade-up">
            <div class="container">
                <div class="section-header fade-up">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Unemployment is
                        <span data-fact="pov.unemployment">{unemp}%</span> while
                        <span data-fact="pov.vulnerable">{vuln}%</span> of workers are in
                        vulnerable employment. Work is not scarce; paid, secure work
                        is.</li>
                        <li>Poverty is falling:
                        <span data-fact="pov.national">{nat}%</span> below the national
                        line in {year}, from
                        <span data-fact="pov.national.first">{nat0}%</span> in {nat0y},
                        and <span data-fact="pov.365">{p365}%</span> on the $3.65
                        line.</li>
                        <li>Inequality is not. The Gini has moved
                        <span data-fact="pov.gini.change">{ginichange}</span> in {span}
                        years, to <span data-fact="pov.gini">{gini}</span>.</li>
                        <li>The poorest fifth holds
                        <span data-fact="pov.bottom20">{bot}%</span> of income against
                        <span data-fact="pov.top10">{top}%</span> for the richest tenth
                        &mdash; <span data-fact="pov.ratio">{ratio}</span> times as much,
                        among half as many people.</li>
                        <li>All national. Every regional figure the previous version
                        carried came from PSA surveys that cannot be fetched, and three
                        of its headline numbers were between eight and twenty-one years
                        apart.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    yrs = [r["year"] for r in ann]
    sy = [int(r["survey_year"]) for r in surv]
    charts = ['''        // 01 the two labour measures on one axis. Separating them is how the
        //    headline unemployment rate ends up telling a story the labour
        //    market does not support.
        new Chart(document.getElementById('labourChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Vulnerable employment (%%)', data: %s,
                      borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.15)',
                      borderWidth: 2, pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Unemployment (%%)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { min: 0, title: { display: true, text: '%% of labour force' } } }
            }
        });''' % (js(yrs),
                  js([f(r["vulnerable_employment_pct"]) for r in ann]),
                  js([f(r["unemployment_pct"]) for r in ann])),
              '''        // 02 poverty at survey years only. A linear time axis with points, not a
        //    category axis with a line: the surveys are years apart and the gaps
        //    are real.
        new Chart(document.getElementById('povChart'), {
            type: 'line',
            data: {
                datasets: [
                    { label: 'National poverty line (%%)', data: %s, borderColor: '#ef4444',
                      borderWidth: 2, pointRadius: 5, showLine: true, spanGaps: true },
                    { label: '$3.65 a day (%%)', data: %s, borderColor: '#f59e0b',
                      borderWidth: 2, pointRadius: 5, showLine: true, spanGaps: true },
                    { label: '$2.15 a day (%%)', data: %s, borderColor: '#22c55e',
                      borderWidth: 2, pointRadius: 5, showLine: true, spanGaps: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { type: 'linear', title: { display: true, text: 'Survey year' },
                         ticks: { callback: function (v) { return v; } } },
                    y: { min: 0, title: { display: true, text: '%% of population' } }
                }
            }
        });''' % (js([{"x": int(r["survey_year"]), "y": f(r["poverty_national_pct"])}
                      for r in surv if f(r["poverty_national_pct"]) is not None]),
                  js([{"x": int(r["year"]), "y": f(r["poverty_365usd_pct"])}
                      for r in ann if f(r["poverty_365usd_pct"]) is not None]),
                  js([{"x": int(r["survey_year"]), "y": f(r["poverty_215usd_pct"])}
                      for r in surv if f(r["poverty_215usd_pct"]) is not None])),
              '''        // 03 income shares at survey years. The gap between the two series is
        //    the finding, and it is almost perfectly flat.
        new Chart(document.getElementById('distChart'), {
            type: 'line',
            data: {
                datasets: [
                    { label: 'Top 10%% share of income', data: %s, borderColor: '#8b5cf6',
                      backgroundColor: 'rgba(139,92,246,0.15)', borderWidth: 2,
                      pointRadius: 5, showLine: true, fill: true },
                    { label: 'Bottom 20%% share of income', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.15)', borderWidth: 2,
                      pointRadius: 5, showLine: true, fill: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { type: 'linear', title: { display: true, text: 'Survey year' },
                         ticks: { callback: function (v) { return v; } } },
                    y: { min: 0, title: { display: true, text: '%% of national income' } }
                }
            }
        });''' % (js([{"x": int(r["survey_year"]), "y": f(r["income_share_top_10"])}
                      for r in surv if f(r["income_share_top_10"]) is not None]),
                  js([{"x": int(r["survey_year"]), "y": f(r["income_share_bottom_20"])}
                      for r in surv if f(r["income_share_bottom_20"]) is not None])),
              '''        // 04 ASEAN, two axes -- a Gini and a poverty rate share no scale
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Gini coefficient', data: %s, backgroundColor: '#8b5cf6',
                      yAxisID: 'y' },
                    { label: '$3.65 poverty rate (%%)', data: %s, backgroundColor: '#f59e0b',
                      yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    y: { position: 'left', title: { display: true, text: 'Gini' } },
                    y1: { position: 'right', title: { display: true, text: '%% below $3.65' },
                          grid: { drawOnChartArea: false } }
                }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([f(r["gini"]) for r in asean]),
                  js([f(r["poverty_365usd_pct"]) for r in asean]))]

    p.sections(S)
    p.charts(charts)
    p.head("Poverty and the Jobs That Do Not Fix It",
           "Philippine poverty is %s%% and falling, while the Gini has moved %s in %s "
           "years. Unemployment is %s%% and %s%% of workers are in vulnerable employment."
           % (F["nat"], F["ginichange"], F["span"], F["unemp"], F["vuln"]),
           "%s%% unemployment, %s%% vulnerable employment. Work is not scarce; paid work is."
           % (F["unemp"], F["vuln"]),
           "Philippine Poverty: Falling Poverty, Static Inequality, and Work Without Wages")
    p.faq({
        "What is the poverty rate in the Philippines?":
            "%s%% of the population lived below the national poverty line at the most "
            "recent survey (%s), down from %s%% in %s. On the World Bank's $3.65-a-day "
            "line it is %s%%, and on the $2.15 extreme-poverty line %s%%. These come from "
            "household surveys run every few years, not annually."
            % (F["nat"], F["year"], F["nat0"], F["nat0y"], F["p365"], F["p215"]),
        "Why is Philippine unemployment low if poverty is high?":
            "Because unemployment counts only people looking for work and not finding "
            "it. It is %s%%. Separately, %s%% of workers are in vulnerable employment -- "
            "own-account and unpaid family work, without a wage or contract. A country "
            "can approach full employment and stay poor if the work is informal, and "
            "quoting the unemployment rate alone hides exactly that."
            % (F["unemp"], F["vuln"]),
        "Is inequality improving in the Philippines?":
            "Barely. The Gini coefficient is %s against %s in %s -- a move of %s across "
            "%s years of surveys. The poorest fifth of the population receives %s%% of "
            "income and the richest tenth receives %s%%, roughly %s times as much among "
            "half as many people."
            % (F["gini"], F["gini0"], F["gini0y"], F["ginichange"], F["span"],
               F["bot"], F["top"], F["ratio"]),
        "Where can I find Philippine poverty data by region?":
            "PSA's Family Income and Expenditure Survey, which is the source for "
            "regional poverty incidence, agricultural wages and farm household income. "
            "It is not analysed here: psa.gov.ph sits behind a managed challenge that "
            "automated requests do not pass, so every figure on this page is national.",
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
