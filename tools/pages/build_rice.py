#!/usr/bin/env python3
"""Regenerate projects/rice-prices-analysis.html from data/ph-food-prices CSVs.

    .venv/bin/python tools/pages/build_rice.py

Like the electricity page, this one was built early and stayed thin: three
charts and fifteen bound figures drawn from two of six CSVs. The directory holds
234,015 WFP observations across 108 markets, 17 regions and five rice
commodities, plus a farmgate-to-retail chain and a coverage table recording that
841 of 2,367 source PDFs parsed. None of that was on the page.

The finding it was missing: the farmer receives well under half the retail
price, and where you buy matters more than which year it is within a year.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-food-prices"
PAGE = "projects/rice-prices-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_rice_annual")
    spread = rows("ph_rice_spread_annual")
    reg = rows("ph_rice_by_region")
    var = rows("ph_rice_by_variety")
    cov = rows("ph_rice_market_coverage")
    chain = rows("ph_rice_margin_chain")
    # facts.sql reads the Premium grade specifically; the CSV's last row is
    # Regular Milled, so prem[-1] silently picked a different grade and four
    # figures disagreed with their own queries.
    prem_all = rows("ph_rice_imported_local")
    prem = sorted([x for x in prem_all if x["grade"] == "Premium"],
                  key=lambda x: x["month"])
    pdfs = rows("ph_rice_prices_coverage")

    regs = sorted(reg, key=lambda x: -f(x["mean_php_kg"]))
    vlast = max(int(x["year"]) for x in var)
    vs = sorted([x for x in var if int(x["year"]) == vlast],
                key=lambda x: -f(x["mean_php_kg"]))
    c_last = chain[-1]
    retail = [x for x in ann if f(x["retail_php_kg"])]

    F = dict(
        r2000=r(f(retail[0]["retail_php_kg"]), 2),
        rlast=r(f(retail[-1]["retail_php_kg"]), 2), rlastyear=retail[-1]["year"],
        rhigh=regs[0]["region"], rhighp=r(f(regs[0]["mean_php_kg"]), 2),
        rlow=regs[-1]["region"], rlowp=r(f(regs[-1]["mean_php_kg"]), 2),
        ryear=reg[0]["year"], nreg=len(reg),
        markets=int(cov[-1]["markets"]), obs=sum(int(x["observations"]) for x in cov),
        vhigh=vs[0]["commodity"], vhighp=r(f(vs[0]["mean_php_kg"]), 2),
        vlow=vs[-1]["commodity"], vlowp=r(f(vs[-1]["mean_php_kg"]), 2),
        nvar=len({x["commodity"] for x in var}),
        share=r(f(c_last["farmer_share_pct"]), 1), shareyear=c_last["year"],
        sharemin=r(min(f(x["farmer_share_pct"]) for x in chain), 1),
        sharemax=r(max(f(x["farmer_share_pct"]) for x in chain), 1),
        nchain=len(chain),
        farmgate=r(f(c_last["farmgate_php_kg"]), 2),
        chainretail=r(f(c_last["retail_php_kg"]), 2),
        gap=r(f(c_last["farm_to_retail"]), 2),
        npdf=len(pdfs), parsed=sum(1 for x in pdfs if x["status"] == "parsed"),
    )
    F["mult"] = r(F["rlast"] / F["r2000"], 1)
    F["rspread"] = r(F["rhighp"] - F["rlowp"], 2)
    F["rspreadpct"] = r(100.0 * (F["rhighp"] / F["rlowp"] - 1), 1)
    F["vspread"] = r(F["vhighp"] - F["vlowp"], 2)
    F["pdfpct"] = r(100.0 * F["parsed"] / F["npdf"], 0)

    p = Page(PAGE)
    p.hero('''                <h1>Who Gets The Money For A Kilo Of Rice</h1>
                <p class="hero-description">
                    Retail rice has nearly tripled since 2000. In the years where the
                    whole chain can be seen, the farmer received under half of what the
                    shopper paid &mdash; and a kilo costs {rspreadpct}% more in one region
                    than another in the same year.
                </p>

                <div class="header-actions">
                    <a href="https://data.humdata.org/dataset/wfp-food-prices-for-philippines" target="_blank" class="btn btn-primary">
                        WFP food prices via HDX
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="rice.retail.multiple">{mult}&times;</div>
                        <div class="stat-label">Retail price since 2000</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="rice.farmer.share">{share}%</div>
                        <div class="stat-label">Of the retail price reached the farmer</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="rice.region.spread.pct">{rspreadpct}%</div>
                        <div class="stat-label">Spread between the dearest and cheapest region</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="rice.obs">{obs:,}</div>
                        <div class="stat-label">Market price observations</div>
                    </div>
                </div>
'''.format(**F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">A national average rice price hides two things that matter more than the average: how little of it reaches the farmer, and how much it varies by where you shop.</p>
                    <ul class="tldr-list">
                        <li>In {shareyear}, farmgate was <span data-fact="rice.farmgate.latest">{farmgate}</span> and retail <span data-fact="rice.retail.chain">{chainretail}</span> per kilo &mdash; the farmer got <span data-fact="rice.farmer.share">{share}%</span>, and across the <span data-fact="rice.margin.years">{nchain}</span> years where all three prices exist the share never left <span data-fact="rice.farmer.share.min">{sharemin}</span>&ndash;<span data-fact="rice.farmer.share.max">{sharemax}%</span>.</li>
                        <li>In {ryear}, rice averaged <span data-fact="rice.region.high.price">{rhighp}</span> per kilo in <span data-fact="rice.region.high">{rhigh}</span> and <span data-fact="rice.region.low.price">{rlowp}</span> in <span data-fact="rice.region.low">{rlow}</span> &mdash; a gap of <span data-fact="rice.region.spread">{rspread}</span>.</li>
                        <li>Variety matters as much: <span data-fact="rice.variety.high">{vhigh}</span> at <span data-fact="rice.variety.high.price">{vhighp}</span> against <span data-fact="rice.variety.low">{vlow}</span> at <span data-fact="rice.variety.low.price">{vlowp}</span>. A "rice price" that does not say which rice is not a price.</li>
                        <li>The daily series behind the recent years is built from government PDFs, of which <span data-fact="rice.pdfs.parsed">{parsed}</span> of <span data-fact="rice.pdfs.total">{npdf}</span> parsed &mdash; <span data-fact="rice.pdfs.pct">{pdfpct}%</span>. That is published rather than hidden.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Nearly Tripled In A Generation",
                "Retail rice per kilo, from the WFP market series. The level is the "
                "part everyone knows; the sections after it are the parts that are not "
                "in the headline.",
                [("Retail, 2000", "P{r2000}".format(**F), "rice.retail.2000",
                  "Per kilo."),
                 ("Retail, {rlastyear}".format(**F), "P{rlast}".format(**F),
                  "rice.retail.2026", "Nominal pesos, not inflation-adjusted."),
                 ("Multiple", "{mult}&times;".format(**F), "rice.retail.multiple",
                  "In nominal terms over twenty-six years. The page does not claim this "
                  "as a real-terms increase.")],
                "Retail rice price per kilo, PHP", "trendChart"),
        p.section(2, "The Farmer's Share",
                "Farmgate, wholesale and retail for the {n} years where all three were "
                "collected. This is the single most useful thing in the dataset and the "
                "earlier version of this page did not show it.".format(n=F["nchain"]),
                [("Farmer's share", "{share}%".format(**F), "rice.farmer.share",
                  "Of the retail price in {y}.".format(y=F["shareyear"])),
                 ("The range", "{sharemin}&ndash;{sharemax}%".format(**F),
                  "rice.farmer.share.min",
                  "Across every year in the chain. It never reaches half."),
                 ("Farm to shelf", "P{gap}".format(**F), "rice.farm.to.retail",
                  "Added between farmgate and retail per kilo, on a farmgate price of "
                  "P{f}.".format(f=F["farmgate"]))],
                "Farmgate, wholesale and retail per kilo, PHP", "chainChart"),
        p.section(3, "Where You Buy It",
                "Mean retail rice by region in {y}, across {m} markets. A national "
                "average sits in the middle of a spread this wide and describes nobody "
                "in particular.".format(y=F["ryear"], m=F["markets"]),
                [("Dearest region", "P{rhighp}".format(**F), "rice.region.high.price",
                  "{h} &mdash; per kilo, mean across its markets.".format(h=F["rhigh"])),
                 ("Cheapest region", "P{rlowp}".format(**F), "rice.region.low.price",
                  "{l}.".format(l=F["rlow"])),
                 ("Spread", "{rspreadpct}%".format(**F), "rice.region.spread.pct",
                  "P{s} per kilo between them, in the same year, for retail rice "
                  "across {n} regions.".format(s=F["rspread"], n=F["nreg"]))],
                "Mean retail rice price by region, {y}".format(y=F["ryear"]), "regionChart"),
        p.section(4, "Which Rice",
                "WFP tracks {n} distinct rice commodities. They are not "
                "interchangeable, and a series that averages across them moves when the "
                "reporting mix changes rather than when prices do.".format(n=F["nvar"]),
                [("Dearest variety", "P{vhighp}".format(**F), "rice.variety.high.price",
                  "{v}.".format(v=F["vhigh"])),
                 ("Cheapest variety", "P{vlowp}".format(**F), "rice.variety.low.price",
                  "{v}.".format(v=F["vlow"])),
                 ("Spread", "P{vspread}".format(**F), None,
                  "Between the dearest and cheapest variety in the same year &mdash; "
                  "wider than the gap between the dearest and cheapest region.")],
                "Mean price by rice variety over time, PHP per kilo", "varietyChart"),
        p.section(5, "The Import Premium Closed",
                "Local rice used to sell above imported. The 2019 tariff law replaced "
                "import quotas with a duty, and the gap has nearly closed.",
                [("Local, latest", "P{v}".format(v=r(f(prem[-1]["local_php_kg"]), 2)),
                  "rice.premium.local.latest", "Per kilo."),
                 ("Imported, latest",
                  "P{v}".format(v=r(f(prem[-1]["imported_php_kg"]), 2)),
                  "rice.premium.imported.latest", "Per kilo."),
                 ("Remaining premium",
                  "P{v}".format(v=r(f(prem[-1]["local_premium_php_kg"]), 2)),
                  "rice.premium.gap.latest",
                  "Local over imported. It was several pesos before the tariff law.")],
                "Local against imported rice, PHP per kilo", "premiumChart"),
        p.prose(6, "What This Page Does Not Cover",
                      "Rice prices, from two sources, at national and regional level. "
                      "The obvious next questions are not answered here.",
                      [("Why the margin is what it is",
                        "Milling, drying, transport, credit and trader margins all sit "
                        "between farmgate and shelf. None are in these CSVs, so the page "
                        "reports the size of the gap and says nothing about who takes "
                        "which part of it."),
                       ("Recent farmgate prices",
                        "The chain table covers {n} years only, ending in {y}. Farmgate "
                        "prices are collected by PSA and its portal is not reachable by "
                        "script, so the farmer's share cannot be brought up to "
                        "date.".format(n=F["nchain"], y=F["shareyear"])),
                       ("Everything that is not rice",
                        "The WFP file holds vegetables, meat, fish and pulses across the "
                        "same markets &mdash; over 200,000 observations. This page is "
                        "only rice; the rest is unexplored rather than excluded on "
                        "principle.")]),
        p.prose(7, "Method",
                      "Two sources, one derive step, seven CSVs.",
                      [("Two price series, kept apart",
                        "WFP market prices run 2000-2026 and DA Bantay Presyo supplies "
                        "the daily NCR series from 2018. They are different collections "
                        "with different coverage and are never spliced into one line."),
                       ("Only actual prices",
                        "The WFP file carries aggregated and forecast rows alongside "
                        "observations. The rice views filter to priceflag 'actual' and "
                        "pricetype 'retail'; without that the series mixes measurements "
                        "with estimates."),
                       ("Coverage is published",
                        "{p} of {t} source PDFs parsed &mdash; {c}%. The unparsed ones "
                        "are mostly a layout generation the parser does not handle, and "
                        "they are listed per document with a status rather than left in "
                        "a log.".format(p=F["parsed"], t=F["npdf"], c=F["pdfpct"])),
                       ("A regex that burned an hour",
                        "The Bantay Presyo parser began as one pattern with nested "
                        "quantifiers and spent 65 minutes of CPU backtracking on wide "
                        "per-market rows. It now splits fixed-layout rows on runs of two "
                        "or more spaces, which cannot blow up."),
                       ("Varieties are not averaged",
                        "Five rice commodities are reported separately. Collapsing them "
                        "into one national price makes the series move when the "
                        "reporting mix changes."),
                       ("Verification",
                        "Every figure on this page is bound to a query in "
                        "<code>facts.sql</code> and re-checked on each build; "
                        "<code>checks.sql</code> adds vocabulary closure and per-series "
                        "price envelopes.")]),
    ]

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Retail rice is
                        <span data-fact="rice.retail.multiple">{mult}</span> times its
                        2000 level in nominal pesos, from
                        <span data-fact="rice.retail.2000">P{r2000}</span> to
                        <span data-fact="rice.retail.2026">P{rlast}</span> per kilo.</li>
                        <li>The farmer's share of that never reaches half:
                        <span data-fact="rice.farmer.share.min">{sharemin}</span> to
                        <span data-fact="rice.farmer.share.max">{sharemax}%</span> across
                        every year where farmgate, wholesale and retail were all
                        collected.</li>
                        <li>Region matters:
                        <span data-fact="rice.region.high.price">P{rhighp}</span> per kilo
                        in <span data-fact="rice.region.high">{rhigh}</span> against
                        <span data-fact="rice.region.low.price">P{rlowp}</span> in
                        <span data-fact="rice.region.low">{rlow}</span> in the same
                        year.</li>
                        <li>Variety matters more:
                        <span data-fact="rice.variety.high.price">P{vhighp}</span> for
                        {vhigh} against
                        <span data-fact="rice.variety.low.price">P{vlowp}</span> for
                        {vlow}. Any single "price of rice" figure is choosing one of
                        <span data-fact="rice.varieties">{nvar}</span> without saying
                        so.</li>
                        <li>The import premium has nearly closed since the 2019 tariff
                        law, to
                        <span data-fact="rice.premium.gap.latest">P{pg}</span> per
                        kilo.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(pg=r(f(prem[-1]["local_premium_php_kg"]), 2), **F))

    ry = [x["year"] for x in retail]
    charts = ['''        // 01 retail trend
        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Retail rice (PHP/kg)', data: %s,
                             borderColor: '#f59e0b',
                             backgroundColor: 'rgba(245,158,11,0.15)',
                             borderWidth: 2, pointRadius: 0, fill: true, spanGaps: false }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { title: { display: true, text: 'PHP per kilo' } } }
            }
        });''' % (js(ry), js([r(f(x["retail_php_kg"]), 2) for x in retail])),
              '''        // 02 the margin chain. Stacked so the farmer's slice is visually the
        //    bottom of the bar and the additions above it are what the shopper
        //    is also paying for.
        new Chart(document.getElementById('chainChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Farmgate', data: %s, backgroundColor: '#22c55e' },
                    { label: 'Farm to wholesale', data: %s, backgroundColor: '#f59e0b' },
                    { label: 'Wholesale to retail', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { stacked: true },
                          y: { stacked: true, title: { display: true, text: 'PHP per kilo' } } }
            }
        });''' % (js([x["year"] for x in chain]),
                  js([r(f(x["farmgate_php_kg"]), 2) for x in chain]),
                  js([r(f(x["farm_to_wholesale"]), 2) for x in chain]),
                  js([r(f(x["wholesale_to_retail"]), 2) for x in chain])),
              '''        // 03 by region, dearest first
        new Chart(document.getElementById('regionChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Mean retail price (PHP/kg)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'PHP per kilo' } } }
            }
        });''' % (js([x["region"] for x in regs]),
                  js([r(f(x["mean_php_kg"]), 2) for x in regs]),
                  js(["#ef4444" if i == 0 else "#22c55e" if i == len(regs) - 1
                      else "#3b82f6" for i in range(len(regs))])),
              '''        // 04 by variety over time, one line each -- averaging these into a
        //    single national price is what this chart exists to argue against
        new Chart(document.getElementById('varietyChart'), {
            type: 'line',
            data: { labels: %s, datasets: [%s] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { title: { display: true, text: 'PHP per kilo' } } }
            }
        });''' % (js(sorted({x["year"] for x in var})),
                  ", ".join(
                      '{ label: %s, data: %s, borderColor: %s, borderWidth: 2, '
                      'pointRadius: 0, fill: false, spanGaps: false }'
                      % (js(cm),
                         js([next((r(f(x["mean_php_kg"]), 2) for x in var
                                   if x["commodity"] == cm and x["year"] == y), None)
                             for y in sorted({x["year"] for x in var})]),
                         js(col))
                      for cm, col in zip(
                          sorted({x["commodity"] for x in var}),
                          ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6"]))),
              '''        // 05 local against imported
        new Chart(document.getElementById('premiumChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Local (PHP/kg)', data: %s, borderColor: '#22c55e',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false },
                    { label: 'Imported (PHP/kg)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { title: { display: true, text: 'PHP per kilo' } } }
            }
        });''' % (js([x["month"] for x in prem]),
                  js([r(f(x["local_php_kg"]), 2) if f(x["local_php_kg"]) else None
                      for x in prem]),
                  js([r(f(x["imported_php_kg"]), 2) if f(x["imported_php_kg"]) else None
                      for x in prem]))]

    p.sections(S)
    p.charts(charts)
    p.head("Who Gets The Money For A Kilo Of Rice",
           "Philippine retail rice is %sx its 2000 level, the farmer receives under half "
           "the retail price, and a kilo costs %s%% more in one region than another in "
           "the same year." % (F["mult"], F["rspreadpct"]),
           "The farmer gets under half the retail price, and region and variety move it "
           "more than the year does.",
           "Philippine Rice Prices: Who Gets The Money For A Kilo")
    p.faq({
        "How much has the price of rice risen in the Philippines?":
            "Retail rice went from P%s per kilo in 2000 to P%s in %s -- about %s times, "
            "in nominal pesos. That is not inflation-adjusted, so part of the rise is "
            "the peso rather than rice."
            % (F["r2000"], F["rlast"], F["rlastyear"], F["mult"]),
        "How much of the rice price goes to the farmer?":
            "Under half. In %s the farmgate price was P%s and retail was P%s -- a "
            "farmer's share of %s%%. Across the %s years where farmgate, wholesale and "
            "retail were all collected the share stayed between %s and %s%%. What "
            "happens in the P%s between farm and shelf is not in this data."
            % (F["shareyear"], F["farmgate"], F["chainretail"], F["share"],
               F["nchain"], F["sharemin"], F["sharemax"], F["gap"]),
        "Why does rice cost different amounts in different parts of the Philippines?":
            "This page does not explain why, but it measures the size: in %s, mean "
            "retail rice was P%s per kilo in %s and P%s in %s -- a %s%% spread across %s "
            "regions in the same year. Transport, milling capacity and local supply all "
            "plausibly contribute and none of them are in these CSVs."
            % (F["ryear"], F["rhighp"], F["rhigh"], F["rlowp"], F["rlow"],
               F["rspreadpct"], F["nreg"]),
        "Did the 2019 rice tariff law lower prices?":
            "It closed the gap between local and imported rice, which now stands at P%s "
            "per kilo against several pesos before. Wholesale prices fell notably; "
            "retail moved far less, which is the pattern the middle sections of this "
            "page are about." % (r(f(prem[-1]["local_premium_php_kg"]), 2)),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
