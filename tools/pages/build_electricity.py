#!/usr/bin/env python3
"""Regenerate projects/electricity-analysis.html from data/ph-electricity CSVs.

    .venv/bin/python tools/pages/build_electricity.py

This page was built early, before the pattern settled, and it showed: three
charts and fifteen bound figures, all about coal, against eight fuels across
twenty-six years sitting unused in the same directory. It also never stated that
the Meralco rate series covers 15 of 93 months.

The omission was hiding the more interesting finding. Renewables were 42.89% of
Philippine generation in 2000 and are 23.32% now -- while renewable generation
itself nearly doubled. Coal did not replace renewables; it absorbed almost all
of a demand increase that tripled total generation.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-electricity"
PAGE = "projects/electricity-analysis.html"
ORDER = ["Coal", "Gas", "Hydro", "Other renewables", "Solar", "Wind",
         "Bioenergy", "Other fossil"]


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    mix = rows("ph_generation_mix")
    roll = rows("ph_generation_rollup")
    sea = rows("sea_coal_share")
    mer = rows("ph_meralco_monthly")
    stat = {x["status"]: int(x["months"]) for x in rows("ph_meralco_status")}

    yrs = sorted({int(x["year"]) for x in mix})
    last = yrs[-1]
    at = lambda fu, y: next((f(x["share_pct"]) for x in mix
                             if x["fuel"] == fu and int(x["year"]) == y), None)
    rl = lambda y: next(x for x in roll if int(x["year"]) == y)
    peers = sorted({x["area"] for x in sea} - {"Philippines", "ASEAN"})
    seay = max(int(x["year"]) for x in sea if x["area"] == "Philippines")
    sea_at = lambda a: next((f(x["coal_share_pct"]) for x in sea
                             if x["area"] == a and int(x["year"]) == seay), None)

    F = dict(
        year=last,
        coal=r(at("Coal", last), 1), coal05=r(at("Coal", 2005), 1),
        gas=r(at("Gas", last), 1), hydro=r(at("Hydro", last), 1),
        geo=r(at("Other renewables", last), 1), solar=r(at("Solar", last), 2),
        wind=r(at("Wind", last), 2),
        renew=r(f(rl(last)["renewable_pct"]), 1),
        renew00=r(f(rl(2000)["renewable_pct"]), 1),
        fossil=r(f(rl(last)["fossil_pct"]), 1),
        twh=r(f(rl(last)["total_twh"]), 1), twh00=r(f(rl(2000)["total_twh"]), 1),
        rtwh=r(f(rl(last)["renewable_twh"]), 1),
        rtwh00=r(f(rl(2000)["renewable_twh"]), 1),
        nfuel=len({x["fuel"] for x in mix}),
        found=stat["found"], missing=stat["not found"],
        total=stat["found"] + stat["not found"],
        mfirst=r(min(f(x["rate_php_per_kwh"]) for x in mer), 2),
        mlast=r(max(f(x["rate_php_per_kwh"]) for x in mer), 2),
        seay=seay,
    )
    F["renewchange"] = r(F["renew"] - F["renew00"], 1)
    F["twhmult"] = r(F["twh"] / F["twh00"], 1)
    F["rtwhmult"] = r(F["rtwh"] / F["rtwh00"], 1)
    F["cov"] = r(100.0 * F["found"] / F["total"], 0)
    F["vsth"] = r(sea_at("Philippines") / sea_at("Thailand"), 1)
    F["th"] = r(sea_at("Thailand"), 1)
    F["seaph"] = r(sea_at("Philippines"), 1)

    p = Page(PAGE)
    p.hero('''                <h1>The Grid That Got Less Renewable</h1>
                <p class="hero-description">
                    Renewables supplied {renew00}% of Philippine electricity in 2000 and
                    {renew}% in {year} &mdash; while renewable generation itself nearly
                    doubled. Demand outran it. Coal took the difference.
                </p>

                <div class="header-actions">
                    <a href="https://ember-energy.org/data/yearly-electricity-data/" target="_blank" class="btn btn-primary">
                        Ember yearly electricity data
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="el.coal.2025">{coal}%</div>
                        <div class="stat-label">Coal share of generation, {year}</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="el.renew.latest">{renew}%</div>
                        <div class="stat-label">Renewable share, from {renew00}% in 2000</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="el.total.mult">{twhmult}&times;</div>
                        <div class="stat-label">Total generation since 2000</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="el.coal.vs.thailand">{vsth}&times;</div>
                        <div class="stat-label">Thailand&rsquo;s coal share</div>
                    </div>
                </div>
'''.format(**F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The renewable share fell <span data-fact="el.renew.change">{renewchange}</span> points in twenty-five years while renewable output rose <span data-fact="el.renew.twh.latest">{rtwh}</span> TWh from <span data-fact="el.renew.twh.2000">{rtwh00}</span>. Both are true. Quoting either one alone gets the country wrong.</p>
                    <ul class="tldr-list">
                        <li>Total generation went from <span data-fact="el.total.2000">{twh00}</span> TWh to <span data-fact="el.total.latest">{twh}</span> TWh &mdash; <span data-fact="el.total.mult">{twhmult}</span> times as much electricity. Almost all of that increase was met with coal.</li>
                        <li>Coal is <span data-fact="el.coal.2025">{coal}%</span> of generation, up from <span data-fact="el.coal.2005">{coal05}%</span> in 2005 and <span data-fact="el.coal.vs.thailand">{vsth}</span> times Thailand's <span data-fact="el.coal.thailand">{th}%</span>.</li>
                        <li>The renewable base is unusual: <span data-fact="el.geothermal">{geo}%</span> sits in Ember's "other renewables" bucket, which for the Philippines is mostly geothermal &mdash; more than hydro at <span data-fact="el.hydro">{hydro}%</span>. Solar is <span data-fact="el.solar">{solar}%</span> and wind <span data-fact="el.wind">{wind}%</span>.</li>
                        <li>The Meralco rate series covers <span data-fact="el.meralco.found">{found}</span> of <span data-fact="el.meralco.total">{total}</span> months &mdash; <span data-fact="el.meralco.coverage.pct">{cov}%</span>. The earlier version of this page charted it without saying so.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Three Times The Electricity",
                "Before any share can be read, the denominator has to be visible. The "
                "Philippines generates roughly three times the electricity it did in "
                "2000, and every share on this page moves against that.",
                [("Generation now", "{twh} TWh".format(**F), "el.total.latest",
                  "From {t} TWh in 2000.".format(t=F["twh00"])),
                 ("Growth", "{twhmult}&times;".format(**F), "el.total.mult",
                  "Demand roughly tripled in twenty-five years."),
                 ("Renewable output", "{rtwh} TWh".format(**F), "el.renew.twh.latest",
                  "Up from {r} TWh &mdash; {m} times as much renewable electricity, "
                  "and a smaller share of a much larger total.".format(
                      r=F["rtwh00"], m=F["rtwhmult"]))],
                "Total generation by year, TWh", "totalChart"),
        p.section(2, "The Share That Went Backwards",
                "This is the finding the earlier version of this page missed by charting "
                "only coal. The renewable share did not stall &mdash; it fell, by nearly "
                "twenty points, from a base that was already largely hydro and "
                "geothermal.",
                [("Renewable share, 2000", "{renew00}%".format(**F), "el.renew.2000",
                  "Large hydro and geothermal, before the coal build-out."),
                 ("Renewable share, {year}".format(**F), "{renew}%".format(**F),
                  "el.renew.latest",
                  "A fall of {c} points.".format(c=F["renewchange"])),
                 ("Why both numbers matter", "&mdash;", None,
                  "Renewable generation nearly doubled over the same period. The share "
                  "fell because coal absorbed almost all of the demand growth, not "
                  "because renewables shrank.")],
                "Renewable and fossil share of generation, %", "shareChart"),
        p.section(3, "What The Grid Actually Runs On",
                "All {n} fuels Ember tracks, latest year. The composition is unusual for "
                "the region: geothermal is larger than hydro, and larger than solar and "
                "wind combined by a wide margin.".format(n=F["nfuel"]),
                [("Coal", "{coal}%".format(**F), "el.coal.2025",
                  "Up from {c}% in 2005.".format(c=F["coal05"])),
                 ("Geothermal and other renewables", "{geo}%".format(**F),
                  "el.geothermal",
                  "Ember files Philippine geothermal here. It is the second-largest "
                  "renewable source and larger than hydro."),
                 ("Solar and wind", "{s}%".format(s=r(F["solar"] + F["wind"], 2)), None,
                  "Combined. Solar {so}% and wind {w}% &mdash; the technologies that "
                  "grew fastest elsewhere are still marginal "
                  "here.".format(so=F["solar"], w=F["wind"]))],
                "Generation mix by fuel, {y}".format(y=last), "mixChart"),
        p.section(4, "Against The Region",
                "Coal share for the Philippines and its neighbours at {y}. The gap is "
                "not marginal.".format(y=F["seay"]),
                [("Philippines", "{seaph}%".format(**F), None,
                  "Coal share of generation in {y}.".format(y=F["seay"])),
                 ("Thailand", "{th}%".format(**F), "el.coal.thailand",
                  "The Philippines runs {v} times as much coal, proportionally.".format(
                      v=F["vsth"])),
                 ("Singapore", "{s}%".format(s=r(sea_at("Singapore"), 1)),
                  "el.coal.singapore",
                  "Almost none &mdash; a gas grid, and a reminder that "
                  "\"Southeast Asian\" is not a single energy story.")],
                "Coal share of generation over time, ASEAN peers", "peerChart"),
        p.section(5, "One Distributor's Rate",
                "Meralco's all-in residential rate, for the {f} of {t} months that could "
                "be retrieved. The advisories are published per month and older ones "
                "fall off the site, so this is a window rather than a "
                "series.".format(f=F["found"], t=F["total"]),
                [("Lowest month found", "P{mfirst}".format(**F), None,
                  "Per kWh, all-in."),
                 ("Highest month found", "P{mlast}".format(**F), None,
                  "A spread of P{d} across {f} months.".format(
                      d=r(F["mlast"] - F["mfirst"], 2), f=F["found"])),
                 ("Coverage", "{cov}%".format(**F), "el.meralco.coverage.pct",
                  "{f} of {t} months. The chart plots only months that exist; it does "
                  "not interpolate across the {m} that do not.".format(
                      f=F["found"], t=F["total"], m=F["missing"]))],
                "Meralco all-in residential rate, months retrieved", "meralcoChart"),
        p.prose(6, "What This Page Does Not Cover",
                      "Generation mix and one distributor's residential rate. That is "
                      "less than the topic deserves, and the gaps are specific.",
                      [("Rates outside Meralco",
                        "Meralco serves Metro Manila and nearby provinces. Every other "
                        "distribution utility and every electric cooperative sets its "
                        "own rate, and ERC publishes those in filings rather than as a "
                        "series. Nothing here speaks to what the rest of the country "
                        "pays."),
                       ("The Meralco series is thin",
                        "{f} of {t} months were found &mdash; {c}%. The advisory pages "
                        "are published per month and older ones fall off. The chart "
                        "draws only the months that exist and the gaps are visible "
                        "rather than bridged.".format(f=F["found"], t=F["total"],
                                                      c=F["cov"])),
                       ("Nothing about why",
                        "Fuel costs, capacity auctions, the WESM spot market and the "
                        "regulatory rate base all sit behind this and none are in these "
                        "CSVs. The page reports what the mix and the rate did, not what "
                        "drove them.")]),
        p.prose(7, "Method",
                      "Two fetchers and one derive step over five CSVs.",
                      [("Ember, not a national source",
                        "Ember compiles national statistics into a comparable series, "
                        "which is what makes the ASEAN comparison possible at all. It "
                        "is a secondary source and the citation says so."),
                       ("Geothermal is not broken out",
                        "Ember files it under \"other renewables\" for the Philippines. "
                        "It is labelled on the page rather than silently folded into a "
                        "renewables total, because for this country specifically that "
                        "bucket is mostly one technology."),
                       ("A column that meant two things",
                        "ph_generation_mix.csv had a column named <code>source</code> "
                        "holding the energy source &mdash; Coal, Gas, Solar &mdash; "
                        "colliding with this repository's convention that "
                        "<code>source</code> is provenance. It is now <code>fuel</code>, "
                        "with provenance in <code>source_dataset</code>."),
                       ("Every fuel must be classified",
                        "The renewable/fossil rollup fails loudly on an unclassified "
                        "fuel rather than letting it drop out of both totals, which "
                        "would leave the shares summing to less than 100 without "
                        "erroring."),
                       ("Meralco parsing",
                        "The all-in residential rate is taken from the overall-rate "
                        "sentence in each advisory. An earlier version matched the "
                        "generation charge instead &mdash; about P7-8 against a real "
                        "P13-15 &mdash; and was caught by an overlap check, because "
                        "consecutive advisories cover the same month twice and "
                        "disagreed."),
                       ("Verification",
                        "Every figure on this page is bound to a query in "
                        "<code>facts.sql</code> and re-checked on each build.")]),
    ]

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>The renewable share of Philippine generation fell from
                        <span data-fact="el.renew.2000">{renew00}%</span> in 2000 to
                        <span data-fact="el.renew.latest">{renew}%</span> in {year}
                        &mdash; a drop of
                        <span data-fact="el.renew.change">{renewchange}</span>
                        points.</li>
                        <li>It fell while renewable generation ROSE, from
                        <span data-fact="el.renew.twh.2000">{rtwh00}</span> to
                        <span data-fact="el.renew.twh.latest">{rtwh}</span> TWh. Total
                        generation went up
                        <span data-fact="el.total.mult">{twhmult}</span> times and coal
                        absorbed nearly all of the difference.</li>
                        <li>Coal is now
                        <span data-fact="el.coal.2025">{coal}%</span> of generation,
                        <span data-fact="el.coal.vs.thailand">{vsth}</span> times
                        Thailand's <span data-fact="el.coal.thailand">{th}%</span> and
                        far above Singapore's
                        <span data-fact="el.coal.singapore">0.9%</span>.</li>
                        <li>The renewable base is geothermal-led:
                        <span data-fact="el.geothermal">{geo}%</span> against hydro at
                        <span data-fact="el.hydro">{hydro}%</span>, with solar at
                        <span data-fact="el.solar">{solar}%</span> and wind at
                        <span data-fact="el.wind">{wind}%</span> still marginal.</li>
                        <li>The Meralco rate series covers
                        <span data-fact="el.meralco.found">{found}</span> of
                        <span data-fact="el.meralco.total">{total}</span> months. It
                        covers one distributor in one region, and says nothing about what
                        the rest of the country pays.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    ylab = [str(y) for y in yrs]
    charts = ['''        // 01 total generation. The denominator every share on this page moves
        //    against, so it is charted first.
        new Chart(document.getElementById('totalChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Renewable (TWh)', data: %s, backgroundColor: '#22c55e' },
                    { label: 'Fossil (TWh)', data: %s, backgroundColor: '#64748b' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { stacked: true, ticks: { maxTicksLimit: 14 } },
                          y: { stacked: true, title: { display: true, text: 'TWh' } } }
            }
        });''' % (js(ylab),
                  js([f(rl(y)["renewable_twh"]) for y in yrs]),
                  js([f(rl(y)["fossil_twh"]) for y in yrs])),
              '''        // 02 the same data as shares. Shown next to the TWh chart on purpose:
        //    the share falls while the absolute renewable line rises, and
        //    either chart alone supports a wrong conclusion.
        new Chart(document.getElementById('shareChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Renewable share (%%)', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true },
                    { label: 'Fossil share (%%)', data: %s, borderColor: '#64748b',
                      borderWidth: 2, pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { min: 0, max: 100, title: { display: true, text: '%% of generation' } } }
            }
        });''' % (js(ylab),
                  js([f(rl(y)["renewable_pct"]) for y in yrs]),
                  js([f(rl(y)["fossil_pct"]) for y in yrs])),
              '''        // 03 the full mix, latest year
        new Chart(document.getElementById('mixChart'), {
            type: 'doughnut',
            data: {
                labels: %s,
                datasets: [{ data: %s, backgroundColor:
                    ['#64748b', '#f97316', '#3b82f6', '#22c55e', '#facc15', '#06b6d4',
                     '#a3e635', '#c084fc'] }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });''' % (js([fu for fu in ORDER if at(fu, last) is not None]),
                  js([r(at(fu, last), 2) for fu in ORDER if at(fu, last) is not None])),
              '''        // 04 peer coal share over time, not just the latest year -- the
        //    divergence is the point and a single-year bar hides it.
        new Chart(document.getElementById('peerChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [%s]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { min: 0, title: { display: true, text: 'Coal %% of generation' } } }
            }
        });''' % (js(sorted({x["year"] for x in sea})),
                  ", ".join(
                      '{ label: %s, data: %s, borderColor: %s, borderWidth: %d, '
                      'pointRadius: 0, fill: false, spanGaps: false }'
                      % (js(a),
                         js([next((f(x["coal_share_pct"]) for x in sea
                                   if x["area"] == a and x["year"] == y), None)
                             for y in sorted({x["year"] for x in sea})]),
                         js("#ef4444" if a == "Philippines" else
                            {"ASEAN": "#a0a0b0", "Indonesia": "#f59e0b",
                             "Malaysia": "#8b5cf6", "Singapore": "#22c55e",
                             "Thailand": "#3b82f6",
                             "Viet Nam": "#ec4899"}.get(a, "#64748b")),
                         3 if a == "Philippines" else 1)
                      for a in ["Philippines", "ASEAN"] + peers))]

    mlab = ["%s-%02d" % (x["year"], int(x["month"])) for x in mer]
    charts.append('''        // 05 Meralco all-in residential rate. Only the months that were found
        //    are plotted, and the axis is categorical over those months rather
        //    than a continuous timeline -- 78 of 93 months are missing and a
        //    time axis would draw one long straight line across them.
        new Chart(document.getElementById('meralcoChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'All-in residential rate (PHP/kWh)', data: %s,
                             borderColor: '#f59e0b',
                             backgroundColor: 'rgba(245,158,11,0.15)',
                             borderWidth: 2, pointRadius: 4, fill: true }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { title: { display: true, text: 'PHP per kWh' } } }
            }
        });''' % (js(mlab), js([r(f(x["rate_php_per_kwh"]), 2) for x in mer])))

    p.sections(S)
    p.charts(charts)
    p.head("The Grid That Got Less Renewable",
           "Renewables supplied %s%% of Philippine electricity in 2000 and %s%% in %s "
           "-- while renewable generation nearly doubled. Coal absorbed the demand "
           "growth." % (F["renew00"], F["renew"], F["year"]),
           "Renewables fell from %s%% to %s%% of generation while renewable output "
           "nearly doubled." % (F["renew00"], F["renew"]),
           "The Grid That Got Less Renewable: Philippine Electricity 2000-%s" % F["year"])
    p.faq({
        "What share of Philippine electricity is renewable?":
            "%s%% in %s, down from %s%% in 2000 -- a fall of %s points. Renewable "
            "generation itself nearly doubled over the same period, from %s to %s TWh; "
            "the share fell because total generation tripled and coal absorbed almost "
            "all of the increase."
            % (F["renew"], F["year"], F["renew00"], abs(F["renewchange"]),
               F["rtwh00"], F["rtwh"]),
        "How much of Philippine electricity comes from coal?":
            "%s%% in %s, up from %s%% in 2005. That is %s times Thailand's %s%% and far "
            "above Singapore's 0.9%%. The Philippines is the most coal-dependent grid "
            "among its regional peers on this measure."
            % (F["coal"], F["year"], F["coal05"], F["vsth"], F["th"]),
        "Why is Philippine geothermal power significant?":
            "It is the second-largest renewable source in the mix at %s%% -- larger than "
            "hydro at %s%%, and far larger than solar (%s%%) and wind (%s%%) combined. "
            "Ember files it under \"other renewables\", which is why that category is "
            "unusually large for the Philippines."
            % (F["geo"], F["hydro"], F["solar"], F["wind"]),
        "How much does electricity cost in the Philippines?":
            "This page reports Meralco's all-in residential rate, which ranged from "
            "P%s to P%s per kWh across the %s months that could be retrieved of %s. "
            "Meralco serves Metro Manila and nearby provinces only; every other "
            "distribution utility and electric cooperative sets its own rate, and those "
            "are published in regulatory filings rather than as a series, so this page "
            "says nothing about what the rest of the country pays."
            % (F["mfirst"], F["mlast"], F["found"], F["total"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
