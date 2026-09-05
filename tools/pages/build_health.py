#!/usr/bin/env python3
"""Regenerate projects/health-analysis.html from data/ph-health CSVs.

    .venv/bin/python tools/pages/build_health.py

The page it replaces led with a 2016 life expectancy, a 2018 infant mortality
rate, a 2019 HIV count and a 2018 TB rate -- four figures from four different
years presented as one picture, the same failure the COVID page had. Fourteen of
its eighteen chart arrays were near-flat with noise added.

Everything here is read at the latest year each indicator actually has, and the
year is printed next to the number rather than implied.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, section, prose_section          # noqa: E402

D = "data/ph-health"
PAGE = "projects/health-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_health_annual")
    asean = rows("ph_health_asean")
    last = lambda col: [r for r in ann if f(r[col]) is not None][-1]
    first = lambda col: [r for r in ann if f(r[col]) is not None][0]
    ph = [r for r in asean if r["country"] == "Philippines"][0]

    F = dict(
        life=round(f(last("life_expectancy")["life_expectancy"]), 1),
        year=last("life_expectancy")["year"],
        life60=round(f(first("life_expectancy")["life_expectancy"]), 1),
        lf=round(f(last("life_expectancy_female")["life_expectancy_female"]), 1),
        lm=round(f(last("life_expectancy_male")["life_expectancy_male"]), 1),
        inf=round(f(last("infant_mortality_per_1000")["infant_mortality_per_1000"]), 1),
        inf60=round(f(first("infant_mortality_per_1000")["infant_mortality_per_1000"]), 1),
        u5=round(f(last("under5_mortality_per_1000")["under5_mortality_per_1000"]), 1),
        mat=round(f(last("maternal_mortality_per_100k")["maternal_mortality_per_100k"])),
        tb=round(f(last("tb_incidence_per_100k")["tb_incidence_per_100k"])),
        tb2000=round(f([r for r in ann if r["year"] == "2000"][0]["tb_incidence_per_100k"])),
        tbyear=last("tb_incidence_per_100k")["year"],
        oop=round(f(last("out_of_pocket_pct_of_health_spend")["out_of_pocket_pct_of_health_spend"]), 1),
        spend=round(f(last("health_spend_pct_gdp")["health_spend_pct_gdp"]), 1),
        meas=round(f(last("measles_immunisation_pct")["measles_immunisation_pct"])),
        measpk=round(max(f(r["measles_immunisation_pct"]) for r in ann
                         if f(r["measles_immunisation_pct"]) is not None)),
        dpt=round(f(last("dpt_immunisation_pct")["dpt_immunisation_pct"])),
        stunt=round(f(last("stunting_under5_pct")["stunting_under5_pct"]), 1),
        fert=round(f(last("fertility_rate")["fertility_rate"]), 2),
        ayear=asean[0]["year"], an=len(asean),
        tbbest=round(min(f(r["tb_incidence_per_100k"]) for r in asean)),
        tbrank=sum(1 for r in asean if f(r["tb_incidence_per_100k"])
                   >= f(ph["tb_incidence_per_100k"])),
        ooprank=sum(1 for r in asean if f(r["out_of_pocket_pct_of_health_spend"])
                    >= f(ph["out_of_pocket_pct_of_health_spend"])),
    )
    F["gain"] = round(F["life"] - F["life60"], 1)
    F["tbchange"] = round(F["tb"] - F["tb2000"])
    # From the raw CSV values, not from the rounded display figures. Dividing
    # 625 by a tbbest already rounded to 97 gives 6.4; facts.sql divides the raw
    # values and gets 6.5, and the two must be the same number.
    F["tbmult"] = round(f(ph["tb_incidence_per_100k"])
                        / min(f(r["tb_incidence_per_100k"]) for r in asean), 1)
    F["measdrop"] = round(F["measpk"] - F["meas"])

    p = Page(PAGE)
    p.hero('''                <h1>Philippine Health, 1960&ndash;{year}</h1>
                <p class="hero-description">
                    Life expectancy is up {gain} years since 1960 and infant deaths are
                    down by two thirds. Two things went the other way, and they are the
                    ones worth the page: tuberculosis, and how much of a hospital bill a
                    household pays itself.
                </p>

                <div class="header-actions">
                    <a href="https://data.worldbank.org/country/philippines" target="_blank" class="btn btn-primary">
                        World Bank health indicators
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="hl.life">{life}</div>
                        <div class="stat-label">Life expectancy, {year}</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="hl.infant">{inf}</div>
                        <div class="stat-label">Infant deaths per 1,000 births</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="hl.tb">{tb}</div>
                        <div class="stat-label">TB cases per 100,000 ({tbyear})</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="hl.oop">{oop}%</div>
                        <div class="stat-label">Of health spending, paid out of pocket</div>
                    </div>
                </div>
'''.format(**F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Almost every Philippine health indicator improved for sixty years. The two that did not are tuberculosis and the share of the bill households pay themselves &mdash; and they are related.</p>
                    <ul class="tldr-list">
                        <li>TB incidence is <span data-fact="hl.tb">{tb}</span> per 100,000 in {tbyear}, <em>higher</em> than the <span data-fact="hl.tb.2000">{tb2000}</span> of 2000. It is the worst of <span data-fact="hl.asean.n">{an}</span> ASEAN economies compared here, at <span data-fact="hl.asean.tb.best">{tbbest}</span> for the best.</li>
                        <li><span data-fact="hl.oop">{oop}%</span> of all health spending is paid directly by households at the point of care &mdash; also the highest in the group. Total health spending is only <span data-fact="hl.spend">{spend}%</span> of GDP.</li>
                        <li>Measles immunisation is <span data-fact="hl.measles">{meas}%</span>, down <span data-fact="hl.measles.peak">{measpk}</span> percentage points from its own peak. Coverage below about 95% is where measles starts circulating again.</li>
                        <li>The wins are real and large: life expectancy from <span data-fact="hl.life.1960">{life60}</span> to <span data-fact="hl.life">{life}</span>, infant mortality from <span data-fact="hl.infant.1960">{inf60}</span> to <span data-fact="hl.infant">{inf}</span> per 1,000.</li>
                    </ul>
'''.format(**F))

    S = [
        section(1, "Sixty Years Of Improvement",
                "Life expectancy and child mortality, the two indicators that summarise "
                "most of what a health system does. Both moved a long way, and most of "
                "the movement was early.",
                [("Life expectancy now", "{life} yrs".format(**F), "hl.life",
                  "Women {lf}, men {lm}.".format(lf=F["lf"], lm=F["lm"])),
                 ("In 1960", "{life60} yrs".format(**F), "hl.life.1960",
                  "A gain of {g} years, most of it before 1990.".format(g=F["gain"])),
                 ("Infant mortality", "{inf}".format(**F), "hl.infant",
                  "Per 1,000 live births, down from {i} in 1960. Under-five mortality "
                  "is {u}.".format(i=F["inf60"], u=F["u5"]))],
                "Life expectancy and infant mortality, 1960 onward", "lifeChart"),
        section(2, "The One That Went Backwards",
                "Tuberculosis is curable, and the Philippines has more of it now than at "
                "the start of the century. This is the single clearest failure in the "
                "dataset and it does not appear in any summary that leads with life "
                "expectancy.",
                [("TB now", "{tb}".format(**F), "hl.tb",
                  "Cases per 100,000 people in {y}.".format(y=F["tbyear"])),
                 ("In 2000", "{tb2000}".format(**F), "hl.tb.2000",
                  "The rate went UP by {c} over the period.".format(c=F["tbchange"])),
                 ("Against the region", "{tbmult}&times;".format(**F), "hl.asean.tb.mult",
                  "The Philippine rate is {m} times the best in this ASEAN group "
                  "({b} per 100,000). Worst of {n}.".format(
                      m=F["tbmult"], b=F["tbbest"], n=F["an"]))],
                "TB incidence per 100,000, ASEAN comparison ({y})".format(y=F["ayear"]),
                "tbChart"),
        section(3, "Who Pays",
                "Health spending is low and the share of it borne directly by patients "
                "is high. Out-of-pocket spending is the mechanism by which illness turns "
                "into poverty, which is why it belongs next to the TB number rather than "
                "in a separate finance section.",
                [("Out of pocket", "{oop}%".format(**F), "hl.oop",
                  "Of all health spending, paid at the point of care. Highest of "
                  "{n}.".format(n=F["an"])),
                 ("Total health spending", "{spend}% of GDP".format(**F), "hl.spend",
                  "Low by any comparison. A small pot, and a large share of it out of "
                  "pocket."),
                 ("Maternal mortality", "{mat}".format(**F), "hl.maternal",
                  "Deaths per 100,000 live births. Improved substantially, and still "
                  "well above where the spending peers sit.")],
                "Out-of-pocket share of health spending, ASEAN ({y})".format(y=F["ayear"]),
                "oopChart"),
        section(4, "Immunisation Is Slipping",
                "Vaccination coverage rose for decades and has fallen back. Measles needs "
                "roughly 95% coverage to stop circulating; below that it returns, and it "
                "returns first among the youngest.",
                [("Measles coverage", "{meas}%".format(**F), "hl.measles",
                  "Down {d} points from its own peak of {p}%.".format(
                      d=F["measdrop"], p=F["measpk"])),
                 ("DPT coverage", "{dpt}%".format(**F), "hl.dpt",
                  "The other routine childhood series, moving the same way."),
                 ("Stunting under five", "{stunt}%".format(**F), "hl.stunting",
                  "Roughly one child in four. Stunting is largely irreversible after "
                  "age two, so this number is a forecast as much as a measurement.")],
                "Measles and DPT immunisation coverage, %", "immChart"),
        prose_section(5, "What This Page Does Not Cover",
                      "The version this replaces charted HIV counts, measles outbreak "
                      "curves, non-communicable disease breakdowns, hospital beds and "
                      "regional health indicators. Those come from DOH's Field Health "
                      "Services Information System and the HIV/AIDS registry.",
                      [("DOH is closed to scripts",
                        "<code>doh.gov.ph</code> sits behind a managed challenge that "
                        "automated requests do not pass. Its registries are the proper "
                        "source for Philippine disease counts and none of them are "
                        "fetchable here."),
                       ("So no HIV, no outbreak curves",
                        "The previous page carried a 2019 HIV figure with no source "
                        "behind it. The epidemic is real and rising; this page stays "
                        "quiet about its size rather than quoting a number it cannot "
                        "check."),
                       ("Nothing sub-national",
                        "Every figure here is national. Regional health indicators need "
                        "PSA or DOH, and both are unreachable, so no regional claim "
                        "appears.")]),
        prose_section(6, "Method",
                      "One fetcher, three CSVs, from the shared World Bank helper in "
                      "<code>data/_lib/worldbank.py</code>.",
                      [("Each figure at its own latest year",
                        "The page this replaces mixed 2016, 2018 and 2019 figures into "
                        "one summary. Here every number is the most recent the indicator "
                        "actually has, and the year is printed beside it."),
                       ("Gaps stay gaps",
                        "A country-year with no survey is null and is never "
                        "forward-filled. Stunting has 13 points across 34 years; drawing "
                        "it as an annual line would invent the years between."),
                       ("Ordering checks",
                        "<code>checks.sql</code> asserts female life expectancy exceeds "
                        "male, that combined sits between them, and that under-five "
                        "mortality is never below infant mortality &mdash; each of which "
                        "catches a transposed column pair that would otherwise look "
                        "entirely plausible."),
                       ("A standing warning",
                        "A check fires while TB incidence remains above its 2000 level. "
                        "It is the page's central claim, so if it ever reverses the "
                        "framing gets revisited rather than quietly outliving the data."),
                       ("Like-for-like comparison",
                        "The ASEAN table uses the latest year every country in it has a "
                        "value for ({y}), not each country's own latest print, which "
                        "would compare different years and call the difference a "
                        "gap.".format(y=F["ayear"])),
                       ("Verification",
                        "Ten assertions in <code>checks.sql</code>, and every figure "
                        "above bound to a query in <code>facts.sql</code>.")]),
    ]

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Life expectancy rose from
                        <span data-fact="hl.life.1960">{life60}</span> to
                        <span data-fact="hl.life">{life}</span> years and infant mortality
                        fell from <span data-fact="hl.infant.1960">{inf60}</span> to
                        <span data-fact="hl.infant">{inf}</span> per 1,000. The long
                        trend is genuinely good.</li>
                        <li>Tuberculosis is the exception:
                        <span data-fact="hl.tb">{tb}</span> per 100,000 in {tbyear}
                        against <span data-fact="hl.tb.2000">{tb2000}</span> in 2000, and
                        <span data-fact="hl.asean.tb.rank">{tbrank}</span>st worst of
                        <span data-fact="hl.asean.n">{an}</span> ASEAN economies.</li>
                        <li>Households pay
                        <span data-fact="hl.oop">{oop}%</span> of all health spending
                        directly, the highest share in the group, out of a total health
                        budget of just
                        <span data-fact="hl.spend">{spend}%</span> of GDP.</li>
                        <li>Measles immunisation has fallen to
                        <span data-fact="hl.measles">{meas}%</span> from a peak of
                        <span data-fact="hl.measles.peak">{measpk}%</span>, below the
                        level at which measles stops circulating.</li>
                        <li>No figure here is sub-national and none covers HIV or
                        outbreak counts. DOH's registries are the right source and are
                        not reachable by script; the previous version of this page quoted
                        them anyway.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    yrs = [r["year"] for r in ann]
    charts = ['''        // 01 life expectancy against infant mortality, two axes -- years and
        //    deaths-per-1000 share no scale
        new Chart(document.getElementById('lifeChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Life expectancy (years)', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.12)', borderWidth: 2,
                      pointRadius: 0, fill: true, yAxisID: 'y', spanGaps: false },
                    { label: 'Infant mortality (per 1,000)', data: %s,
                      borderColor: '#ef4444', borderWidth: 2, pointRadius: 0,
                      fill: false, yAxisID: 'y1', spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { position: 'left', title: { display: true, text: 'Years' } },
                    y1: { position: 'right', title: { display: true, text: 'Deaths per 1,000' },
                          grid: { drawOnChartArea: false } }
                }
            }
        });''' % (js(yrs),
                  js([f(r["life_expectancy"]) for r in ann]),
                  js([f(r["infant_mortality_per_1000"]) for r in ann])),
              '''        // 02 TB across ASEAN, Philippines highlighted
        new Chart(document.getElementById('tbChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'TB cases per 100,000', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Cases per 100,000' } } }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([f(r["tb_incidence_per_100k"]) for r in asean]),
                  js(["#ef4444" if r["country"] == "Philippines" else "#3b82f6"
                      for r in asean])),
              '''        // 03 out-of-pocket share across ASEAN
        new Chart(document.getElementById('oopChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Out-of-pocket %% of health spending', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { title: { display: true, text: '%% of health spending' } } }
            }
        });''' % (js([r["country"] for r in sorted(
                  asean, key=lambda r: -f(r["out_of_pocket_pct_of_health_spend"]))]),
                  js([f(r["out_of_pocket_pct_of_health_spend"]) for r in sorted(
                      asean, key=lambda r: -f(r["out_of_pocket_pct_of_health_spend"]))]),
                  js(["#ef4444" if r["country"] == "Philippines" else "#3b82f6"
                      for r in sorted(asean, key=lambda r: -f(
                          r["out_of_pocket_pct_of_health_spend"]))])),
              '''        // 04 immunisation. The 95%% herd-immunity line is drawn because "coverage
        //    fell" and "coverage fell below the level that stops measles" are
        //    different claims.
        new Chart(document.getElementById('immChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Measles (%%)', data: %s, borderColor: '#f59e0b',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false },
                    { label: 'DPT (%%)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false },
                    { label: '95%% herd-immunity threshold', data: %s,
                      borderColor: '#22c55e', borderDash: [6, 4], pointRadius: 0,
                      fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { min: 0, max: 100, title: { display: true, text: 'Coverage (%%)' } }
                }
            }
        });''' % (js(yrs),
                  js([f(r["measles_immunisation_pct"]) for r in ann]),
                  js([f(r["dpt_immunisation_pct"]) for r in ann]),
                  js([95] * len(ann)))]

    p.sections(S)
    p.charts(charts)
    p.head("Philippine Health 1960-%s" % F["year"],
           "Philippine health from the World Bank: life expectancy up %s years since "
           "1960, but TB incidence higher than in 2000 and %s%% of health spending paid "
           "out of pocket." % (F["gain"], F["oop"]),
           "Life expectancy up %s years since 1960 — and TB higher than in 2000."
           % F["gain"],
           "Philippine Health: Sixty Years of Progress, and Two Indicators Going Backwards")
    p.faq({
        "What is life expectancy in the Philippines?":
            "%s years as of %s -- %s for women and %s for men -- up from %s in 1960. "
            "Infant mortality fell over the same period from %s to %s deaths per 1,000 "
            "live births." % (F["life"], F["year"], F["lf"], F["lm"], F["life60"],
                              F["inf60"], F["inf"]),
        "Is tuberculosis getting worse in the Philippines?":
            "Yes, on this data. Incidence is %s cases per 100,000 in %s against %s in "
            "2000 -- a rise of %s. It is the highest of the %s ASEAN economies compared "
            "here, roughly %s times the best rate in the group. TB is curable, which is "
            "what makes it the clearest failure in the dataset."
            % (F["tb"], F["tbyear"], F["tb2000"], F["tbchange"], F["an"], F["tbmult"]),
        "How much do Filipinos pay out of pocket for healthcare?":
            "%s%% of all health spending is paid directly by households at the point of "
            "care, the highest share among the ASEAN economies compared here. Total "
            "health spending is %s%% of GDP -- a small pot, of which a large share comes "
            "straight from patients." % (F["oop"], F["spend"]),
        "Why is measles returning in the Philippines?":
            "Immunisation coverage has fallen to %s%% from a peak of %s%%. Measles needs "
            "roughly 95%% coverage to stop circulating, so below that it returns -- and "
            "it returns first among the youngest children. DPT coverage is %s%% and "
            "moving the same way." % (F["meas"], F["measpk"], F["dpt"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
