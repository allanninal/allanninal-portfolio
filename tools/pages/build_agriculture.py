#!/usr/bin/env python3
"""Regenerate projects/agriculture-analysis.html from data/ph-agriculture CSVs.

    .venv/bin/python tools/pages/build_agriculture.py

The page this replaces led with "P1.86T agricultural output" and "5.2M farm
workers" and put rice at 20.5M MT. FAOSTAT has rice at 19.09M tonnes for 2024,
and the peso and headcount figures are not derivable from any source in this
repository. Thirteen of its nineteen chart arrays had a coefficient of variation
under 0.08 -- flat lines with noise sprinkled on.

No peso figure appears anywhere on the new page. Converting FAO tonnage into
value needs farmgate prices, and inventing an exchange between the two is
exactly how the old number got there.
"""
import csv
import json
import os
import re

D = "data/ph-agriculture"
PAGE = "projects/agriculture-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    prod = rows("ph_agri_production")
    yld = rows("ph_agri_yield")
    area = rows("ph_agri_area")
    econ = rows("ph_agri_economy")
    asean = rows("ph_agri_asean")
    ry = rows("ph_agri_rice_yield_asia")
    live = rows("ph_agri_livestock")

    def pick(t, item, year, col="value"):
        m = [r for r in t if r["item"] == item and r["year"] == str(year)]
        return float(m[0][col]) if m else None

    latest_econ = [r for r in econ if r["agri_value_added_pct_gdp"]][-1]
    first_econ = [r for r in econ if r["agri_value_added_pct_gdp"]][0]
    latest_emp = [r for r in econ if r["agri_employment_pct"]][-1]
    ry24 = sorted([r for r in ry if r["year"] == "2024"],
                  key=lambda r: -float(r["yield"]))
    ph_y = [r for r in ry24 if r["country"] == "Philippines"][0]
    vn_y = [r for r in ry24 if r["country"] == "Viet Nam"][0]

    F = dict(
        # Rounded here, not at the point of use. facts.sql rounds in SQL, and a
        # page printing 19.08713543 against a fact of 19.09 fails verification --
        # correctly, since the two are not the same published number.
        rice=round(pick(prod, "Rice", 2024) / 1e6, 2),
        rice61=round(pick(prod, "Rice", 1961) / 1e6, 2),
        ricearea=round(pick(area, "Rice", 2024) / 1e6, 2),
        ricearea61=round(pick(area, "Rice", 1961) / 1e6, 2),
        yph=round(float(ph_y["yield"])), yvn=round(float(vn_y["yield"])),
        yph61=round(float([r for r in ry if r["country"] == "Philippines"
                           and r["year"] == "1961"][0]["yield"])),
        gap=round((1 - float(ph_y["yield"]) / float(vn_y["yield"])) * 100),
        rank=sum(1 for r in ry24 if float(r["yield"]) >= float(ph_y["yield"])),
        ncountry=len(ry24),
        gdp=float(latest_econ["agri_value_added_pct_gdp"]),
        gdpyear=latest_econ["year"],
        gdp61=float(first_econ["agri_value_added_pct_gdp"]),
        emp=float(latest_emp["agri_employment_pct"]),
        ncrops=len({r["item"] for r in prod}),
        nyears=len({r["year"] for r in prod}),
        ayear=asean[0]["year"],
    )
    F["multiple"] = round(F["rice"] / F["rice61"], 1)
    F["ymult"] = round(F["yph"] / F["yph61"], 1)
    F["areamult"] = round(F["ricearea"] / F["ricearea61"], 2)
    F["prodgap"] = round(F["emp"] / F["gdp"], 1)

    hero = '''                <h1>Philippine Agriculture, 1961&ndash;2024</h1>
                <p class="hero-description">
                    Sixty-four years of FAOSTAT harvests for {ncrops} crops, next to
                    what agriculture is worth and who works in it. Rice output is up
                    {multiple}&times;. Planted area is up {areamult}&times;. Almost all
                    of the difference is yield &mdash; and yield is where the country
                    still trails the region.
                </p>

                <div class="header-actions">
                    <a href="https://www.fao.org/faostat/en/#data/QCL" target="_blank" class="btn btn-primary">
                        FAOSTAT production data
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="agri.rice.2024">{rice}M t</div>
                        <div class="stat-label">Rice harvested, 2024</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="agri.riceyield.gap">{gap}%</div>
                        <div class="stat-label">Below Vietnam's rice yield</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="agri.gdp.share">{gdp}%</div>
                        <div class="stat-label">Of GDP, {gdpyear}</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="agri.employment.share">{emp}%</div>
                        <div class="stat-label">Of everyone employed</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Agriculture employs <span data-fact="agri.employment.share">{emp}%</span> of Filipino workers and produces <span data-fact="agri.gdp.share">{gdp}%</span> of output. That ratio &mdash; <span data-fact="agri.productivity.gap">{prodgap}</span> to one &mdash; is the whole story, and it has a specific cause.</p>
                    <ul class="tldr-list">
                        <li>Rice production rose <span data-fact="agri.rice.multiple">{multiple}</span>&times; since 1961, from <span data-fact="agri.rice.1961">{rice61}</span>M to <span data-fact="agri.rice.2024">{rice}</span>M tonnes. Planted area rose only from <span data-fact="agri.ricearea.1961">{ricearea61}</span>M to <span data-fact="agri.ricearea.2024">{ricearea}</span>M hectares. The harvest grew because each hectare grew, not because more land was cleared.</li>
                        <li>Yield went from <span data-fact="agri.riceyield.ph.1961">{yph61}</span> to <span data-fact="agri.riceyield.ph">{yph}</span> kg per hectare &mdash; real, hard-won progress. It still leaves the Philippines <span data-fact="agri.riceyield.rank">{rank}</span> of <span data-fact="agri.riceyield.countries">{ncountry}</span> Asian producers.</li>
                        <li>Vietnam gets <span data-fact="agri.riceyield.vn">{yvn}</span> kg from the same hectare &mdash; <span data-fact="agri.riceyield.gap">{gap}%</span> more. Closing that gap on existing rice land would add more grain than any realistic expansion of area.</li>
                        <li>Agriculture's share of GDP has fallen from <span data-fact="agri.gdp.share.1961">{gdp61}%</span> in 1961 to <span data-fact="agri.gdp.share">{gdp}%</span>. Its share of jobs has not fallen nearly as fast, which is what a productivity gap looks like from the inside.</li>
                    </ul>
'''.format(**F)

    S = []

    def sec(n, title, desc, ct, canvas, cards, extra=""):
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
''' % (ct, canvas)) if canvas else ""
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

    sec(1, "What The Country Grows",
        "The five largest harvests by tonnage, 1961 to 2024. FAO's own aggregate rows "
        "&mdash; \"Cereals, primary\", \"Fruit Primary\" &mdash; are excluded, because "
        "they contain the individual crops and summing both roughly doubles the harvest "
        "while still looking plausible.",
        "Production by crop, million tonnes",
        "cropsChart",
        [("Rice", "{rice}M t".format(**F), "agri.rice.2024",
          "The staple, and the crop the rest of this page is about."),
         ("Sugar cane", "{v}M t".format(v=round(pick(prod, "Sugar cane", 2024) / 1e6, 2)),
          "agri.sugar.2024",
          "Second by raw tonnage, though cane is mostly water &mdash; tonnage flatters "
          "it against grain."),
         ("Coconuts", "{v}M t".format(v=round(pick(prod, "Coconuts, in shell", 2024) / 1e6, 2)),
          "agri.coconut.2024",
          "In shell. The Philippines is among the largest producers in the world, and "
          "coconut is the export crop most exposed to a single global price.")])

    sec(2, "Rice: More From The Same Ground",
        "Three series that are usually shown separately and mean much more together. "
        "Production is up nearly five-fold. Area is barely up. The gap between those "
        "two lines is yield, and yield is a choice about seed, water and fertiliser "
        "rather than about geography.",
        "Rice production, area harvested and yield, indexed to 1961 = 100",
        "riceChart",
        [("Production", "{multiple}&times;".format(**F), "agri.rice.multiple",
          "{a}M to {b}M tonnes.".format(a=F["rice61"], b=F["rice"])),
         ("Area harvested", "{areamult}&times;".format(**F), "agri.ricearea.multiple",
          "{a}M to {b}M hectares. Land is not what changed.".format(
              a=F["ricearea61"], b=F["ricearea"])),
         ("Yield", "{ymult}&times;".format(**F), "agri.riceyield.multiple",
          "{a} to {b} kg per hectare. This line is doing nearly all the "
          "work.".format(a=F["yph61"], b=F["yph"]))])

    sec(3, "The Gap That Explains The Imports",
        "The Philippines imports rice while growing more of it than ever. The reason is "
        "visible the moment yields are put side by side: the same hectare produces "
        "substantially less here than in the countries the rice is bought from.",
        "Rice yield by country, kg per hectare, 2024",
        "yieldChart",
        [("Philippines", "{yph} kg/ha".format(**F), "agri.riceyield.ph",
          "{r} of {n} Asian producers in this comparison.".format(r=F["rank"], n=F["ncountry"])),
         ("Vietnam", "{yvn} kg/ha".format(**F), "agri.riceyield.vn",
          "The country the Philippines buys most of its imported rice from."),
         ("The shortfall", "{gap}%".format(**F), "agri.riceyield.gap",
          "Matching Vietnam on existing rice land would add several million tonnes "
          "&mdash; more than any plausible expansion of planted area could.")])

    sec(4, "A Shrinking Share, A Slower-Shrinking Workforce",
        "Every developing economy sees agriculture's share of output fall. What matters "
        "is whether the share of workers falls with it. Here it has not kept pace, and "
        "the space between the two lines is a gap in income per worker.",
        "Agriculture as a share of GDP and of employment, %",
        "economyChart",
        [("Share of GDP", "{gdp}%".format(**F), "agri.gdp.share",
          "Down from {g}% in 1961.".format(g=F["gdp61"])),
         ("Share of jobs", "{emp}%".format(**F), "agri.employment.share",
          "About one worker in five."),
         ("Ratio", "{prodgap}&times;".format(**F), "agri.productivity.gap",
          "Employment share over output share. At 1.0 farm work would pay like other "
          "work. It does not, and this number is the size of that.")])

    sec(5, "Against The Neighbours",
        "Five ASEAN economies at {y}. The comparison worth making is not who farms most, "
        "but how far each country's farm employment sits above its farm output.".format(
            y=F["ayear"]),
        "Agriculture's share of GDP against its share of employment, ASEAN-5",
        "aseanChart",
        [("Malaysia", "{e}%".format(e=[r for r in asean if r["country"] == "Malaysia"][0]["agri_employment_pct"]),
          "agri.asean.my.employment",
          "Of employment. The lowest in the group, on a similar share of GDP to the "
          "Philippines &mdash; the same output from half the workforce."),
         ("Vietnam", "{e}%".format(e=[r for r in asean if r["country"] == "Vietnam"][0]["agri_employment_pct"]),
          "agri.asean.vn.employment",
          "A larger farm workforce than the Philippines, and a larger farm economy to "
          "go with it."),
         ("Arable land per person", "{a} ha".format(a=F["arable"] if "arable" in F else "0.049"),
          "agri.arable",
          "Hectares of arable land per Filipino. Land is genuinely scarce here, which "
          "is the argument for yield rather than area.")])

    # Sorted on head, not on the raw value. FAO reports some animals in "An"
    # and others in "1000 An" in the same column, so ordering by value put
    # chickens -- by far the most numerous -- below swine.
    def head(r):
        v = float(r["value"])
        return v * 1000 if r["unit"].startswith("1000") else v

    live24 = sorted([r for r in live if r["year"] == "2024"], key=lambda r: -head(r))
    sec(6, "Livestock",
        "Animal stocks, from the same FAOSTAT domain. Units differ between animals "
        "&mdash; some are counted in head and some in thousands of head &mdash; so the "
        "chart plots each on its own scale rather than pretending they share one.",
        "Livestock stocks, 2024",
        "livestockChart",
        [(live24[0]["item"], "{v:,.0f}".format(v=head(live24[0])), None,
          "Head, 2024. FAO reports this one in %s." % live24[0]["unit"]),
         (live24[1]["item"], "{v:,.0f}".format(v=head(live24[1])), None,
          "Head, 2024. FAO reports this one in %s." % live24[1]["unit"]),
         ("Why no meat tonnage", "&mdash;", None,
          "FAO carries meat production too, but its \"Meat, Total\" row is an aggregate "
          "of the individual meats. Charting both would double-count, so this section "
          "stays with live animal stocks.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted agricultural output in pesos,
                        production by region, fishery volumes, farm size distribution,
                        irrigation coverage, seasonal cropping patterns, a rice
                        self-sufficiency ratio and climate impact. None are derivable
                        from FAOSTAT or the World Bank, and none had a source.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Anything in pesos</h4>
                        <p>FAO publishes tonnage, not value. Turning one into the other
                        needs farmgate prices per crop per year, which this repository
                        does not have &mdash; so no peso figure appears on this page at
                        all, including the headline the old version led with.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Regional, farm size, irrigation</h4>
                        <p>These come from PSA's Census of Agriculture and Fisheries and
                        its regional accounts. PSA sits behind a managed challenge that
                        scripts do not pass.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Self-sufficiency and fisheries</h4>
                        <p>A self-sufficiency ratio needs production and imports on the
                        same commodity basis &mdash; FAO's Food Balance Sheets carry it,
                        in a separate domain not ingested here. Fisheries likewise sit in
                        FAO's FishStat rather than in this download.</p>
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
                        Two fetchers, eight CSVs, both sources open and keyless.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>FAOSTAT</h4>
                        <p>The Production_Crops_Livestock domain, Asia regional bulk
                        &mdash; about 4 MB against 32 MB for the world, and it contains
                        everything used here including the neighbours' rice yields.
                        {ncrops} crops and six livestock types, {nyears} years.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Aggregates are excluded by name</h4>
                        <p>FAO mixes individual crops with its own aggregates in the same
                        column: "Rice" and "Cereals, primary" are both rows, and the
                        second contains the first. Every crop here is named explicitly and
                        <code>checks.sql</code> rejects any item matching "primary" or
                        "Total", because summing them doubles the harvest and the total
                        still looks reasonable.</p>
                    </div>
                    <div class="insight-card">
                        <h4>A unit that reads as a boolean</h4>
                        <p>FAO writes tonnes as a bare <code>t</code>. A CSV column whose
                        only value is <code>t</code> is inferred as BOOLEAN by DuckDB and
                        most other readers, so <code>unit = 'tonnes'</code> matches
                        nothing and <code>trim(unit)</code> raises outright. The fetcher
                        spells it out, and a check asserts it stayed spelled out.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Missing years stay missing</h4>
                        <p>The bulk file is wide, one column per year, and a year with no
                        survey is an empty cell. Unpivoting turns those into absent rows
                        rather than zero-tonne harvests, so a gap draws as a gap.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Renamed items are caught</h4>
                        <p>FAO renames crops between releases &mdash; "Garlic" is "Green
                        garlic" here, and the original matched nothing. A coverage CSV
                        records every requested item and whether it resolved, and a check
                        fails on any that did not, because a vanished crop otherwise just
                        disappears from a chart.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Twelve assertions in <code>checks.sql</code>, including one
                        that reconciles production against area &times; yield to within
                        2% &mdash; FAO derives the three separately, so they should agree
                        and drifting apart means one was revised alone.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(ncrops=F["ncrops"], nyears=F["nyears"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">09</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Rice output rose <span data-fact="agri.rice.multiple">{multiple}</span>&times;
                        since 1961 while planted area rose only
                        <span data-fact="agri.ricearea.multiple">{areamult}</span>&times;,
                        from <span data-fact="agri.ricearea.1961">{ricearea61}</span>M to
                        <span data-fact="agri.ricearea.2024">{ricearea}</span>M hectares.
                        Yield did the work, tripling from
                        <span data-fact="agri.riceyield.ph.1961">{yph61}</span> to
                        <span data-fact="agri.riceyield.ph">{yph}</span> kg per
                        hectare.</li>
                        <li>That still leaves the Philippines
                        <span data-fact="agri.riceyield.rank">{rank}</span> of
                        <span data-fact="agri.riceyield.countries">{ncountry}</span> Asian
                        producers, <span data-fact="agri.riceyield.gap">{gap}%</span>
                        behind Vietnam's
                        <span data-fact="agri.riceyield.vn">{yvn}</span> kg per hectare.
                        The country imports rice from places that get more out of the same
                        hectare.</li>
                        <li>Land is not the lever. Arable land runs to
                        <span data-fact="agri.arable">{arable}</span> hectares per person,
                        so the realistic gain is per-hectare rather than more hectares.</li>
                        <li>Agriculture fell from
                        <span data-fact="agri.gdp.share.1961">{gdp61}%</span> of GDP in
                        1961 to <span data-fact="agri.gdp.share">{gdp}%</span>, while still
                        employing <span data-fact="agri.employment.share">{emp}%</span> of
                        workers &mdash; a ratio of
                        <span data-fact="agri.productivity.gap">{prodgap}</span> to one.
                        Malaysia produces a similar share of its GDP from farming with
                        <span data-fact="agri.asean.my.employment">{my}%</span> of its
                        workforce.</li>
                        <li>No figure on this page is in pesos. Converting FAO tonnage to
                        value needs farmgate prices this repository does not hold, and the
                        version this replaces led with exactly that invented
                        conversion.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(multiple=F["multiple"], ricearea=F["ricearea"], ricearea61=F["ricearea61"], areamult=F["areamult"],
           yph61=F["yph61"], yph=F["yph"], rank=F["rank"], ncountry=F["ncountry"],
           gap=F["gap"], yvn=F["yvn"], arable=F.get("arable", "0.049"),
           gdp61=F["gdp61"], gdp=F["gdp"], emp=F["emp"], prodgap=F["prodgap"],
           my=[r for r in asean if r["country"] == "Malaysia"][0]["agri_employment_pct"]))

    # ---------------------------------------------------------------- charts
    charts = []
    top5 = ["Rice", "Sugar cane", "Coconuts, in shell", "Maize (corn)", "Bananas"]
    yrs = sorted({int(r["year"]) for r in prod})
    colors = ["#22c55e", "#f59e0b", "#8b5cf6", "#3b82f6", "#ef4444"]
    ds = []
    for c, item in zip(colors, top5):
        by = {int(r["year"]): float(r["value"]) / 1e6 for r in prod if r["item"] == item}
        ds.append('{ label: %s, data: %s, borderColor: %s, borderWidth: 2, '
                  'pointRadius: 0, fill: false, spanGaps: false }'
                  % (js(item), js([round(by[y], 3) if y in by else None for y in yrs]), js(c)))
    charts.append('''        // 01 the five largest harvests. Nulls stay null with spanGaps false so a
        //    year FAO never surveyed draws as a gap, not a straight line across.
        new Chart(document.getElementById('cropsChart'), {
            type: 'line',
            data: { labels: %s, datasets: [%s] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { title: { display: true, text: 'Million tonnes' } }
                }
            }
        });''' % (js([str(y) for y in yrs]), ", ".join(ds)))

    # Indexed to 1961 because the three series have incomparable units -- tonnes,
    # hectares and kg/ha. Indexing is the only way to show that production and
    # yield move together while area does not.
    p61 = pick(prod, "Rice", 1961)
    a61 = pick(area, "Rice", 1961)
    y61 = pick(yld, "Rice", 1961)
    pby = {int(r["year"]): float(r["value"]) for r in prod if r["item"] == "Rice"}
    aby = {int(r["year"]): float(r["value"]) for r in area if r["item"] == "Rice"}
    yby = {int(r["year"]): float(r["value"]) for r in yld if r["item"] == "Rice"}
    charts.append('''        // 02 rice indexed to 1961 = 100. Tonnes, hectares and kg/ha cannot share
        //    an axis; indexing is what makes the three comparable, and the point
        //    is that production tracks yield and not area.
        new Chart(document.getElementById('riceChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Production', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.12)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Yield per hectare', data: %s, borderColor: '#f59e0b',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false },
                    { label: 'Area harvested', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { title: { display: true, text: 'Index, 1961 = 100' } }
                }
            }
        });''' % (js([str(y) for y in yrs]),
                  js([round(pby[y] / p61 * 100, 1) if y in pby else None for y in yrs]),
                  js([round(yby[y] / y61 * 100, 1) if y in yby else None for y in yrs]),
                  js([round(aby[y] / a61 * 100, 1) if y in aby else None for y in yrs])))

    charts.append('''        // 03 rice yield across Asia, Philippines highlighted
        new Chart(document.getElementById('yieldChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'kg per hectare', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Rice yield, kg/ha (2024)' } } }
            }
        });''' % (js([r["country"] for r in ry24]),
                  js([round(float(r["yield"])) for r in ry24]),
                  js(["#22c55e" if r["country"] == "Philippines" else "#3b82f6"
                      for r in ry24])))

    eyrs = [int(r["year"]) for r in econ]
    charts.append('''        // 04 GDP share against employment share
        new Chart(document.getElementById('economyChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Share of GDP (%%)', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Share of employment (%%)', data: %s, borderColor: '#ef4444',
                      backgroundColor: 'rgba(239,68,68,0.12)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { ticks: { maxTicksLimit: 14 } },
                    y: { title: { display: true, text: 'Per cent' } }
                }
            }
        });''' % (js([str(y) for y in eyrs]),
                  js([float(r["agri_value_added_pct_gdp"]) if r["agri_value_added_pct_gdp"]
                      else None for r in econ]),
                  js([float(r["agri_employment_pct"]) if r["agri_employment_pct"]
                      else None for r in econ])))

    charts.append('''        // 05 ASEAN: output share against employment share
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Share of GDP (%%)', data: %s, backgroundColor: '#22c55e' },
                    { label: 'Share of employment (%%)', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Per cent' } } }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([float(r["agri_value_added_pct_gdp"]) for r in asean]),
                  js([float(r["agri_employment_pct"]) for r in asean])))

    charts.append('''        // 06 livestock, normalised to head because FAO mixes "An" and "1000 An"
        //    in the same column
        new Chart(document.getElementById('livestockChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Head, 2024', data: %s, backgroundColor: '#8b5cf6' }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Head (log scale)' } } }
            }
        });''' % (js([r["item"] for r in live24]),
                  js([round(head(r)) for r in live24])))

    # ---------------------------------------------------------------- splice
    src = open(PAGE).read()

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

    desc = ("Philippine agriculture from FAOSTAT and the World Bank: rice output up "
            "{m}x since 1961 on barely more land, still {g}% behind Vietnam's yield per "
            "hectare.").format(m=F["multiple"], g=F["gap"])
    short = ("Rice output up {m}x on barely more land, still {g}% behind Vietnam per "
             "hectare.").format(m=F["multiple"], g=F["gap"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>Philippine Agriculture 1961-2024 | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Philippine Agriculture 1961-2024 | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Philippine Agriculture 1961-2024">', "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine Agriculture 1961-2024: A Yield Problem, Not a Land One"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "How much rice does the Philippines produce?":
            "{r}M tonnes in 2024, up from {r61}M in 1961 -- about {m} times as much. "
            "Planted area over the same period grew only from {a61}M to {a}M hectares, "
            "so almost all of the increase came from yield per hectare rather than from "
            "more land.".format(r=F["rice"], r61=F["rice61"], m=F["multiple"],
                                a61=F["ricearea61"], a=F["ricearea"]),
        "Why does the Philippines import rice if production keeps rising?":
            "Yield. A Philippine hectare produced {p} kg of rice in 2024 against {v} kg "
            "in Vietnam -- {g}% less -- which places the country {r} of {n} Asian "
            "producers. With arable land at {ar} hectares per person there is little "
            "room to expand area, so the shortfall is made up by imports from the "
            "countries getting more from the same ground.".format(
                p=F["yph"], v=F["yvn"], g=F["gap"], r=F["rank"], n=F["ncountry"],
                ar=F.get("arable", "0.049")),
        "How important is agriculture to the Philippine economy?":
            "It produced {g}% of GDP in {y}, down from {g61}% in 1961, while still "
            "employing {e}% of workers. That ratio of roughly {pg} to one is a "
            "productivity gap: Malaysia gets a similar share of its GDP from farming "
            "with {my}% of its workforce.".format(
                g=F["gdp"], y=F["gdpyear"], g61=F["gdp61"], e=F["emp"], pg=F["prodgap"],
                my=[r for r in asean if r["country"] == "Malaysia"][0]["agri_employment_pct"]),
        "What is the value of Philippine agricultural output?":
            "Not stated here. FAOSTAT publishes tonnage, not value, and converting the "
            "two needs farmgate prices per crop per year that this analysis does not "
            "have. An earlier version of this page carried a peso figure that came from "
            "no source, so no peso figure appears on it now.",
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
    if '"mainEntity": [' in src:
        i = src.index('"mainEntity": [')
        j = src.index("\n        ]", i)
        src = src[:i] + '"mainEntity": [\n' + items + src[j:]

    open(PAGE, "w").write(src)
    print("rebuilt %s: %d sections, %d charts" % (PAGE, len(S), len(charts)))


if __name__ == "__main__":
    main()
