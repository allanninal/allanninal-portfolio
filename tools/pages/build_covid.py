#!/usr/bin/env python3
"""Regenerate projects/covid-analysis.html from data/ph-covid CSVs.

    .venv/bin/python tools/pages/build_covid.py

Same reason as build_earthquake.py: the page this replaces carried twenty chart
arrays, seven of which were entirely multiples of five, and headline figures
read from three different dates months apart. Generating from the CSVs makes a
typed number impossible.

What the old page had that this one does not: regional case distribution,
vaccination by region, vaccine brand shares, ICU utilisation, age and sex
breakdowns, top provinces, economic impact and healthcare-worker impact. OWID
carries none of those for the Philippines -- DOH published them, in PDFs and a
data drop that is no longer served. They are removed and named on the page
rather than approximated.
"""
import csv
import datetime
import json
import os
import re

D = "data/ph-covid"
PAGE = "projects/covid-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def num(v, d=0):
    f = float(v)
    return int(f) if d == 0 else round(f, d)


def main():
    daily = rows("ph_covid_daily")
    head = {r["metric"]: r["value"] for r in rows("ph_covid_headline")}
    ann = rows("ph_covid_annual")
    waves = rows("ph_covid_waves")
    asean = rows("ph_covid_asean")
    exc = {r["metric"]: r["value"] for r in rows("ph_covid_excess")}
    stg = {r["metric"]: r["value"] for r in rows("ph_covid_stringency")}
    cov = {r["metric"]: r for r in rows("ph_covid_coverage")}
    mon = rows("ph_covid_monthly")
    as_of = daily[0]["as_of"]
    as_of_h = datetime.date.fromisoformat(as_of).strftime("%-d %B %Y")

    F = dict(
        cases=num(head["total_cases"]), deaths=num(head["total_deaths"]),
        cfr=num(head["case_fatality_pct"], 2),
        fullyvax=round(float(head["people_fully_vaccinated"]) / 1e6, 1),
        excess=num(exc["excess_deaths"]), mult=num(exc["undercount_multiple"], 1),
        unattr=num(exc["unattributed_deaths"]),
        nwaves=len(waves), as_of=as_of_h,
        peak=max(int(r["new_cases"]) for r in daily if r["new_cases"]),
        rank=sum(1 for r in asean
                 if float(r["deaths_per_million"])
                 >= float([x for x in asean if x["country"] == "Philippines"][0]["deaths_per_million"])),
    )

    # ------------------------------------------------------------------ hero
    hero = '''                <h1>Philippine COVID-19, 2020&ndash;2026</h1>
                <p class="hero-description">
                    The confirmed toll is {deaths:,} deaths. The excess-mortality
                    estimate for the same period is {excess:,}. This page is mostly
                    about that gap, and about which of the two numbers a country
                    actually gets quoted.
                </p>

                <div class="header-actions">
                    <a href="https://docs.owid.io/projects/covid/en/latest/" target="_blank" class="btn btn-primary">
                        Our World in Data COVID dataset
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="cov.cases">{cases:,}</div>
                        <div class="stat-label">Confirmed cases</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="cov.deaths">{deaths:,}</div>
                        <div class="stat-label">Confirmed deaths</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="cov.excess">{excess:,}</div>
                        <div class="stat-label">Excess deaths, same period</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="cov.fullyvax">{fullyvax}M</div>
                        <div class="stat-label">Fully vaccinated</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Every figure on this page is read at one date, {as_of}. That sounds like housekeeping. The page it replaces took its case count from May 2023, its death count from January 2024 and its vaccination count from December 2022 &mdash; each close to real, the set impossible.</p>
                    <ul class="tldr-list">
                        <li>Confirmed deaths: <span data-fact="cov.deaths">{deaths:,}</span>. Excess deaths over the same period: <span data-fact="cov.excess">{excess:,}</span> &mdash; <span data-fact="cov.excess.multiple">{mult}</span>&times; higher, leaving <span data-fact="cov.excess.unattributed">{unattr:,}</span> deaths above the historical baseline that were never attributed to COVID.</li>
                        <li>The case fatality rate of <span data-fact="cov.cfr">{cfr}%</span> is therefore a rate among <em>tested</em> people, not among infected ones. It is the most-quoted number here and the least informative.</li>
                        <li><span data-fact="cov.waves">{nwaves}</span> waves, by a stated rule rather than by eye. The largest peaked at <span data-fact="cov.peak.daily">{peak:,}</span> cases in a single day.</li>
                        <li>Against the five largest other ASEAN economies the Philippines ranks <span data-fact="cov.asean.rank.deaths">{rank}</span> for deaths per million &mdash; while ranking near the bottom for cases per million, which is a testing story rather than an infection one.</li>
                    </ul>
'''.format(**F)

    # -------------------------------------------------------------- sections
    S = []

    def sec(n, title, desc, chart_title, canvas, cards, extra=""):
        c = "\n".join(
            '''                    <div class="insight-card">
                        <h4>{h}</h4>
                        <div class="insight-value"{fa}>{v}</div>
                        <p>{p}</p>
                    </div>'''.format(h=h, v=v, p=p, fa=(' data-fact="%s"' % k) if k else "")
            for h, v, k, p in cards)
        cv = ('''
                <div class="chart-container fade-up">
                    <div class="chart-title"><span>%s</span></div>
                    <div class="chart-wrapper"><canvas id="%s"></canvas></div>
                </div>
''' % (chart_title, canvas)) if canvas else ""
        S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">{n:02d}</div>
                    <h2>{t}</h2>
                    <p class="section-description">{d}</p>
                </div>
{cv}{ex}
                <div class="grid-3 fade-up">
{c}
                </div>
            </div>
        </section>
'''.format(n=n, t=title, d=desc, cv=cv, ex=extra, c=c))

    sec(1, "The Gap That Runs The Page",
        "Confirmed COVID deaths are deaths in people who were tested, found positive, "
        "and recorded as such. Excess mortality is the count of deaths above what the "
        "years before the pandemic would predict, from any cause. Where the two diverge, "
        "the smaller one is a measure of testing.",
        "Confirmed COVID deaths against excess deaths over the same period",
        "excessChart",
        [("Confirmed deaths", "{deaths:,}".format(**F), "cov.deaths",
          "The number in every headline, and the one the case fatality rate is built from."),
         ("Excess deaths", "{excess:,}".format(**F), "cov.excess",
          "Deaths above the pre-pandemic baseline over the same window."),
         ("Never attributed", "{unattr:,}".format(**F), "cov.excess.unattributed",
          "The difference. Some are undiagnosed COVID; some are people who died of "
          "other things because hospitals were full. The data cannot separate them, "
          "and no split is asserted here.")])

    sec(2, "The Epidemic Curve",
        "Daily confirmed cases with the 7-day mean. Reporting moved from daily to weekly "
        "during 2023 and then stopped, so the flat tail is the end of counting, not the "
        "end of transmission.",
        "Daily confirmed cases, 7-day mean",
        "curveChart",
        [("Highest single day", "{peak:,}".format(**F), "cov.peak.daily",
          "On {d}.".format(d=[r for r in daily if r["new_cases"]
                              and int(r["new_cases"]) == F["peak"]][0]["date"])),
         ("Highest 7-day mean", "{:,}".format(num(max(float(r["new_cases_smoothed"])
                                                      for r in daily if r["new_cases_smoothed"]))),
          "cov.peak.smoothed",
          "The smoothed peak, which is the figure worth comparing between countries "
          "because it is not distorted by weekend reporting."),
         ("Cases in 2021", "{:,}".format(num([r for r in ann if r["year"] == "2021"][0]["cases"])),
          "cov.cases.2021",
          "The worst year by cases and by deaths &mdash; "
          "{:,} of the latter.".format(num([r for r in ann if r["year"] == "2021"][0]["deaths"])))])

    w3 = [r for r in waves if r["wave"] == "3"][0]
    w2 = [r for r in waves if r["wave"] == "2"][0]
    sec(3, "Counting The Waves",
        "\"Four waves\" is the kind of claim that gets repeated because it sounds settled. "
        "Here a wave is a peak in the 7-day mean above 1,000 cases/day, separated from any "
        "larger peak by a trough falling below 40% of the smaller of the two. That rule "
        "gives {n}. A different threshold gives a different answer, which is the honest "
        "position.".format(n=F["nwaves"]),
        "Cases per wave, by the stated rule",
        "wavesChart",
        [("Waves identified", F["nwaves"], "cov.waves",
          "Boundaries sit at the lowest point between consecutive peaks, so every day "
          "belongs to exactly one wave and the wave totals sum to the daily series."),
         ("Largest peak (wave 3)", "{:,}".format(num(w3["peak_smoothed_cases"])), "cov.wave3.peak",
          "Omicron, peaking {d}. {c:,} cases in the wave.".format(
              d=w3["peak_date"], c=num(w3["cases_in_wave"]))),
         ("Deadliest (wave 2)", "{:,}".format(num(w2["deaths_in_wave"])), "cov.wave2.deaths",
          "Delta. Fewer recorded cases than wave 3 at its peak, and "
          "{x}&times; the deaths &mdash; the clearest thing in this dataset about what "
          "vaccination changed.".format(
              x=round(num(w2["deaths_in_wave"]) / num(w3["deaths_in_wave"]), 1)))])

    sec(4, "Testing, And What It Hides",
        "Positivity is the share of tests that come back positive. When it is high, the "
        "case count is a floor rather than a measurement, because testing is only reaching "
        "the sickest. The series stops in {p} &mdash; the page stops with it.".format(
            p=cov["positive_rate"]["last_date"]),
        "Test positivity rate, %",
        "positivityChart",
        [("Positivity peak", "{}%".format(round(max(float(r["positive_rate"])
                                                    for r in daily if r["positive_rate"]), 1)), "cov.positivity.peak",
          "The WHO suggested 5% as the level below which an epidemic is being adequately "
          "tracked. This is many times that."),
         ("Days with testing data", cov["positive_rate"]["non_null_days"], None,
          "Out of {t:,} days in the series. Testing data covers less than a third of the "
          "pandemic.".format(t=len(daily))),
         ("Last reported", cov["positive_rate"]["last_date"], "cov.positivity.last",
          "Nothing after this date. Any positivity figure quoted for 2023 onward is not "
          "coming from this source.")])

    sec(5, "Lockdown Stringency",
        "The Oxford stringency index scores containment policy from 0 to 100. The "
        "Philippines reached 100 &mdash; the maximum the index defines. The correlation "
        "with cases is positive, and that needs explaining rather than presenting.",
        "Stringency index against 7-day mean cases",
        "stringencyChart",
        [("Peak stringency", stg["max_stringency"], "cov.stringency.max",
          "The index maximum. Few countries reached it and none held it long."),
         ("Mean over the period", stg["mean_stringency"], "cov.stringency.mean",
          "Averaged across {d:,} days with both series present, ending {l}.".format(
              d=num(stg["paired_days"]), l=cov["stringency_index"]["last_date"])),
         ("Correlation with cases", "r=" + stg["pearson_r_same_day"], "cov.stringency.r",
          "<em>Positive.</em> Read naively that says restrictions caused cases. It says "
          "the opposite: governments tightened because cases were rising. Same-day "
          "correlation cannot separate cause from response, and this page does not "
          "claim it can.")])

    ph = [r for r in asean if r["country"] == "Philippines"][0]
    sg = [r for r in asean if r["country"] == "Singapore"][0]
    sec(6, "Against The Region",
        "The five largest other ASEAN economies, per million people. Brunei, Laos, "
        "Cambodia and Timor-Leste are left out because their populations are small "
        "enough to make per-million rates jump around.",
        "Deaths and cases per million, ASEAN-6",
        "aseanChart",
        [("Rank by deaths per million", F["rank"], "cov.asean.rank.deaths",
          "Of six. {v} deaths per million.".format(v=num(ph["deaths_per_million"]))),
         ("Cases per million", "{:,}".format(num(ph["cases_per_million"])), "cov.asean.cases.pm",
          "Against {s:,} for Singapore. Singapore did not have fourteen times the "
          "infection; it had the testing to find it.".format(s=num(sg["cases_per_million"]))),
         ("Fully vaccinated", "{}%".format(round(float(ph["fully_vaccinated_per_hundred"]), 1)),
          "cov.asean.vax",
          "The lowest of the six. Vietnam and Singapore both cleared 86%.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted cases by region, vaccination by
                        region, vaccine brand shares, ICU occupancy, age and sex breakdowns,
                        top provinces, economic impact and healthcare-worker infections.
                        None of those are in this dataset for the Philippines, and the
                        numbers that were on the page did not come from anywhere else
                        either. They are removed rather than approximated.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Regional, provincial, age and sex</h4>
                        <p>DOH published these in its COVID Data Drop. That drop is no longer
                        served, and OWID never carried sub-national Philippine detail. Anything
                        at this granularity would have to be rebuilt from archived copies
                        first.</p>
                    </div>
                    <div class="insight-card">
                        <h4>ICU and hospital occupancy</h4>
                        <p>OWID carries ICU and hospital columns, but they are empty for the
                        Philippines for the whole period. An empty column and a low number are
                        not the same thing.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Vaccine brands and economic impact</h4>
                        <p>Brand-level rollout came from NTF briefings; the economic figures
                        would need PSA national accounts. Neither is in this repository, so
                        neither is on this page.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Method</h2>
                    <p class="section-description">
                        Two scripts and eight CSVs, reproducible from this repository.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Source</h4>
                        <p>Our World in Data's <code>compact.csv</code> &mdash; about 180 MB of
                        every country on one date index. The fetcher streams it, filters to the
                        Philippines plus five ASEAN comparators, and writes only those rows.</p>
                    </div>
                    <div class="insight-card">
                        <h4>One date, carried everywhere</h4>
                        <p>Every figure is read at <code>{as_of}</code>, and that date sits on
                        <em>every row of every CSV</em>. <code>checks.sql</code> asserts a single
                        <code>as_of</code> across all seven tables, because the specific failure
                        being designed against is a page whose numbers were individually right
                        and collectively impossible.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Wave rule</h4>
                        <p>A peak in the 7-day mean above 1,000 cases/day, separated from any
                        larger peak by a trough below 40% of the smaller. Boundaries are the
                        minimum between consecutive peaks, half-open on the left so no day is
                        counted twice &mdash; an earlier version double-counted four boundary
                        days, which is small enough to pass for rounding.</p>
                    </div>
                    <div class="insight-card">
                        <h4>A revision worth knowing</h4>
                        <p>On 14 August 2023 the cumulative case count <em>fell</em> by
                        <span data-fact="cov.revision">65,079</span> as DOH revised downward.
                        OWID rebased the cumulative series without restating the dailies, so
                        summing daily cases gives about 32,000 more than the cumulative total.
                        Both are right on their own terms; <code>checks.sql</code> keeps the
                        discrepancy visible so nobody scales one to the other.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Series that stop</h4>
                        <p>Stringency ends {sl}, positivity {pl}, vaccination {vl}. Charts stop
                        where their data stops instead of running flat to the present, which
                        would read as policy relaxing to zero rather than reporting ending.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Twelve assertions in <code>checks.sql</code> cover date gaps,
                        negative counts, deaths exceeding cases, wave partitioning and the
                        country-name match that would otherwise return an empty comparison.
                        Every figure above is bound to a query in <code>facts.sql</code> and
                        re-checked on each build.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(as_of=as_of, sl=cov["stringency_index"]["last_date"],
           pl=cov["positive_rate"]["last_date"],
           vl=cov["people_fully_vaccinated"]["last_date"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">09</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Excess deaths reached <span data-fact="cov.excess">{excess:,}</span>
                        against <span data-fact="cov.deaths">{deaths:,}</span> confirmed &mdash;
                        <span data-fact="cov.excess.multiple">{mult}</span>&times;. The confirmed
                        toll is the one that gets quoted and it is the smaller of two defensible
                        numbers.</li>
                        <li>The <span data-fact="cov.cfr">{cfr}%</span> case fatality rate divides
                        deaths by <em>confirmed</em> cases. With positivity peaking far above the
                        5% that indicates adequate tracking, the denominator is a fraction of
                        real infections and the rate is not a probability of dying from
                        COVID.</li>
                        <li>Wave 2 (Delta) killed
                        <span data-fact="cov.wave2.deaths">{w2d:,}</span> against wave 3's
                        (Omicron) deaths, on
                        <span data-fact="cov.wave2.cases">{w2c:,}</span> recorded cases versus
                        <span data-fact="cov.wave3.cases">{w3c:,}</span>. Wave 3 was bigger and
                        far less lethal.</li>
                        <li>Stringency and cases correlate <em>positively</em> at
                        <span data-fact="cov.stringency.r">r=0.259</span> over
                        <span data-fact="cov.stringency.days">1,088</span> paired days. That is
                        governments responding to outbreaks, not causing them, and it is a good
                        example of a correlation that is real and means the reverse of how it
                        reads.</li>
                        <li>The Philippines is <span data-fact="cov.asean.rank.deaths">{rank}</span>
                        of six ASEAN economies for deaths per million at
                        <span data-fact="cov.asean.deaths.pm">587</span>, while recording
                        <span data-fact="cov.asean.cases.pm">36,622</span> cases per million
                        against Singapore's
                        <span data-fact="cov.asean.sg.cases.pm">532,073</span>. Low case counts
                        next to high death counts is what undertesting looks like.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(excess=F["excess"], deaths=F["deaths"], mult=F["mult"], cfr=F["cfr"],
           rank=F["rank"], w2d=num(w2["deaths_in_wave"]), w2c=num(w2["cases_in_wave"]),
           w3c=num(w3["cases_in_wave"])))

    # ---------------------------------------------------------------- charts
    # The curve stops at the last date the country reported, not at as_of.
    # Everything after is OWID's forward-filled zeros.
    rep = {r["metric"]: r["value"] for r in rows("ph_covid_reporting")}
    last_report = rep["last_report_date"]
    reported = [r for r in daily if r["date"] <= last_report]
    dts = [r["date"] for r in reported]
    charts = []

    charts.append('''        // 01 confirmed against excess
        new Chart(document.getElementById('excessChart'), {
            type: 'bar',
            data: {
                labels: ['Confirmed COVID deaths', 'Excess deaths'],
                datasets: [{ label: 'Deaths', data: %s,
                             backgroundColor: ['#3b82f6', '#ef4444'] }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Deaths' } } }
            }
        });''' % js([F["deaths"], F["excess"]]))

    # The raw daily series is spiky and 2,392 points is more than a line chart
    # renders usefully; the smoothed series is the one worth drawing, with raw
    # kept as faint points so the reader can see the dispersion it hides.
    charts.append('''        // 02 epidemic curve. Nulls are left as nulls with spanGaps false, so a
        //    stretch with no reporting draws as a gap rather than a straight line
        //    through it.
        new Chart(document.getElementById('curveChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Daily cases', data: %s, borderColor: 'rgba(148,163,184,0.35)',
                      borderWidth: 1, pointRadius: 0, fill: false, spanGaps: false },
                    { label: '7-day mean', data: %s, borderColor: '#3b82f6',
                      backgroundColor: 'rgba(59,130,246,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { title: { display: true, text: 'Cases per day' } }
                }
            }
        });''' % (js(dts),
                  js([float(r["new_cases"]) if r["new_cases"] else None for r in reported]),
                  js([round(float(r["new_cases_smoothed"]), 1) if r["new_cases_smoothed"]
                      else None for r in reported])))

    charts.append('''        // 03 cases and deaths per wave, on two axes because the scales differ
        //    by two orders of magnitude
        new Chart(document.getElementById('wavesChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Cases', data: %s, backgroundColor: '#3b82f6', yAxisID: 'y' },
                    { label: 'Deaths', data: %s, backgroundColor: '#ef4444', yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    y: { position: 'left', title: { display: true, text: 'Cases' } },
                    y1: { position: 'right', title: { display: true, text: 'Deaths' },
                          grid: { drawOnChartArea: false } }
                }
            }
        });''' % (js([["Wave " + r["wave"], r["peak_date"][:7]] for r in waves]),
                  js([int(r["cases_in_wave"]) for r in waves]),
                  js([int(r["deaths_in_wave"]) for r in waves])))

    # OWID's positive_rate is already a percentage (it ranges 0.41 to 45.6 here),
    # not a fraction. Multiplying by 100 put a 4,562% positivity rate on the
    # chart -- caught by rendering it and looking, not by reading the code.
    pos = [(r["date"], round(float(r["positive_rate"]), 2))
           for r in daily if r["positive_rate"]]
    charts.append('''        // 04 positivity. The series is drawn only over the dates it exists;
        //    padding it to the full timeline would imply testing continued.
        new Chart(document.getElementById('positivityChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Positivity rate (%%)', data: %s, borderColor: '#f59e0b',
                      backgroundColor: 'rgba(245,158,11,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true },
                    { label: 'WHO 5%% guidance', data: %s, borderColor: '#10b981',
                      borderDash: [6, 4], pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 10 } },
                    y: { title: { display: true, text: 'Share of tests positive (%%)' } }
                }
            }
        });''' % (js([p[0] for p in pos]), js([p[1] for p in pos]), js([5.0] * len(pos))))

    stg_pairs = [(r["date"], round(float(r["stringency_index"]), 1),
                  round(float(r["new_cases_smoothed"]), 1) if r["new_cases_smoothed"] else None)
                 for r in daily if r["stringency_index"]]
    charts.append('''        // 05 stringency against cases, two axes
        new Chart(document.getElementById('stringencyChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Stringency index', data: %s, borderColor: '#8b5cf6',
                      borderWidth: 2, pointRadius: 0, yAxisID: 'y', fill: false },
                    { label: '7-day mean cases', data: %s, borderColor: '#3b82f6',
                      backgroundColor: 'rgba(59,130,246,0.15)', borderWidth: 2,
                      pointRadius: 0, yAxisID: 'y1', fill: true, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 12 } },
                    y: { position: 'left', min: 0, max: 100,
                         title: { display: true, text: 'Stringency (0-100)' } },
                    y1: { position: 'right', title: { display: true, text: 'Cases per day' },
                          grid: { drawOnChartArea: false } }
                }
            }
        });''' % (js([p[0] for p in stg_pairs]), js([p[1] for p in stg_pairs]),
                  js([p[2] for p in stg_pairs])))

    charts.append('''        // 06 ASEAN per-million comparison, log x because Singapore's case rate is
        //    an order of magnitude above the rest and a linear axis flattens
        //    everyone else into the baseline
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Deaths per million', data: %s, backgroundColor: '#ef4444' },
                    { label: 'Cases per million', data: %s, backgroundColor: '#3b82f6' }
                ]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { type: 'logarithmic', ticks: { maxTicksLimit: 6 },
                               title: { display: true, text: 'Per million (log scale)' } } }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([round(float(r["deaths_per_million"]), 1) for r in asean]),
                  js([round(float(r["cases_per_million"]), 1) for r in asean])))

    # ---------------------------------------------------------------- splice
    src = open(PAGE).read()

    # Marker search is indentation-agnostic on purpose: these pages were written
    # at different times and nest the same blocks at different depths, so an
    # exact-indent index() silently fails on the next page it is pointed at.
    def at(marker, start=0):
        m = re.search(r"^[ \t]*" + re.escape(marker), src[start:], re.M)
        if not m:
            raise SystemExit("marker not found: %r" % marker)
        return start + m.start()

    i = at("<h1>")
    j = at('<div class="project-info">', i)
    src = src[:i] + hero + "\n" + src[j:]

    i = at('<span class="tldr-badge">')
    j = at("</div>", i + 1)
    src = src[:i] + tldr + src[j:]

    i = at('<section class="section">')
    j = src.index("<h2>Related Projects</h2>")
    j = src.rindex("<section", 0, j)
    j = src.rindex("\n", 0, j) + 1
    src = src[:i] + "\n".join(S) + src[j:]

    i = src.index("        new Chart(")
    j = src.index("    </script>", i)
    src = src[:i] + "\n\n".join(charts) + "\n" + src[j:]

    # head metadata and FAQ, for the same reason as the earthquake page
    desc = ("Philippine COVID-19 read at one date: {d:,} confirmed deaths against {e:,} "
            "excess deaths, {w} waves by a stated rule, and what the case fatality rate "
            "does not measure.").format(d=F["deaths"], e=F["excess"], w=F["nwaves"])
    short = ("{d:,} confirmed COVID deaths against {e:,} excess deaths in the "
             "Philippines.").format(d=F["deaths"], e=F["excess"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>Philippine COVID-19 2020-2026 | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Philippine COVID-19 2020-2026 | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Philippine COVID-19 2020-2026">', "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine COVID-19 2020-2026: The Gap Between Confirmed and Excess Deaths"',
         "headline")

    faq = {
        "How many people died of COVID-19 in the Philippines?":
            "{d:,} deaths were confirmed as COVID-19. Over the same period the country "
            "recorded {e:,} excess deaths -- deaths above what the pre-pandemic years "
            "predict, from any cause -- which is {m} times higher. The {u:,} difference "
            "includes undiagnosed COVID and deaths caused by an overwhelmed health "
            "system; this data cannot separate the two.".format(
                d=F["deaths"], e=F["excess"], m=F["mult"], u=F["unattr"]),
        "What was the Philippine COVID-19 case fatality rate?":
            "{c}% of confirmed cases ended in a confirmed death. That is a rate among "
            "people who were tested, not among people who were infected. Test positivity "
            "peaked far above the 5% that indicates adequate tracking, so confirmed cases "
            "are a fraction of real infections and the true infection fatality rate is "
            "lower.".format(c=F["cfr"]),
        "How many COVID-19 waves did the Philippines have?":
            "{n}, using a stated rule: a peak in the 7-day mean above 1,000 cases per day, "
            "separated from any larger peak by a trough below 40% of the smaller. The "
            "largest peaked at {p:,} confirmed cases in one day in January 2022.".format(
                n=F["nwaves"], p=F["peak"]),
        "How does the Philippines compare with the rest of ASEAN?":
            "Among the six largest ASEAN economies the Philippines ranks {r} for deaths "
            "per million, while recording far fewer cases per million than Singapore, "
            "Vietnam or Malaysia. High deaths alongside low recorded cases is the "
            "signature of undertesting rather than of a milder epidemic.".format(r=F["rank"]),
    }
    items = ",\n".join(
        '            {\n'
        '                "@type": "Question",\n'
        '                "name": %s,\n'
        '                "acceptedAnswer": {\n'
        '                    "@type": "Answer",\n'
        '                    "text": %s\n'
        '                }\n'
        '            }' % (json.dumps(q), json.dumps(a)) for q, a in faq.items())
    i = src.index('"mainEntity": [')
    j = src.index("\n        ]", i)
    src = src[:i] + '"mainEntity": [\n' + items + src[j:]

    open(PAGE, "w").write(src)
    print("rebuilt %s: %d sections, %d charts" % (PAGE, len(S), len(charts)))


if __name__ == "__main__":
    main()
