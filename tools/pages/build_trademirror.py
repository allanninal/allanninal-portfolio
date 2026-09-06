#!/usr/bin/env python3
"""Regenerate projects/global-trade-mirror-analysis.html from data/global-trade-mirror.

    .venv/bin/python tools/pages/build_trademirror.py

Every export is somebody's import. Both countries report it, and the numbers do
not match.

China reports exporting $116.23bn to Germany in 2022. Germany reports importing
$207.81bn from China. Same goods, same year, two of the most capable statistical
agencies in the world, and a $91.6bn gap.

Part of every gap is definitional and has to be removed before anything is
claimed: exports are valued FOB, at the dock, and imports CIF, with freight and
insurance inside them, so an import figure should exceed its matching export
figure by roughly the cost of shipping. Comtrade publishes both valuations. The
median absolute disagreement across 2,600 matched pairs is 31.15%, and 22.38%
once both sides are put on the same valuation -- so freight explains about a
quarter of it and something else explains the rest.

The disagreement is not evenly spread. Saudi Arabia's partners report a median
291.97% more than it does; Germany's differ by 9.64%. And at the top, the fifty-two
reporters here report $21.43tn of exports and $22.14tn of imports -- $714bn of
trade that one side records and the other does not, on flows that are by
definition the same flows.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-trade-mirror"
PAGE = "projects/global-trade-mirror-analysis.html"
REAL = __import__("re").compile(r"^[A-Z]{3}$")


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    pair = rows("tm_pair")
    rep = rows("tm_reporter")
    cov = {x["property"] + "|" + x["unit"]: x["value"] for x in rows("tm_coverage")}
    selfm = rows("tm_selfmismatch")
    for p in pair:
        for k in ("exporter_reported_usd", "importer_reported_cif_usd",
                  "importer_reported_fob_usd", "gap_cif_usd", "gap_cif_pct",
                  "gap_fob_usd", "gap_fob_pct"):
            p[k] = f(p[k])
    for x in rep:
        for k in ("median_abs_gap_cif_pct", "median_abs_gap_fob_pct",
                  "pairs_as_exporter", "total_exports_usd", "total_imports_usd"):
            x[k] = f(x[k])

    def C(prop, unit):
        return f(cov[prop + "|" + unit])

    real = [p for p in pair
            if REAL.match(p["exporter_iso"] or "") and REAL.match(p["importer_iso"] or "")]
    big = max((p for p in real if p["exporter_reported_usd"] > 5e9),
              key=lambda p: abs(p["gap_cif_usd"]))
    P = {(p["exporter_iso"], p["importer_iso"]): p for p in pair}
    phus, sacn, nlde = P[("PHL", "USA")], P[("SAU", "CHN")], P[("NLD", "DEU")]
    big25 = [x for x in rep if x["pairs_as_exporter"] >= 25]
    worst = max(big25, key=lambda x: x["median_abs_gap_cif_pct"])
    best = min(big25, key=lambda x: x["median_abs_gap_cif_pct"])
    sm = max(selfm, key=lambda x: abs(f(x["diff_pct"])))

    F = dict(
        year=int(C("year", "year")), nrep=int(C("reporters read", "count")),
        npair=int(C("matched pairs", "count")),
        nflow=int(C("flow rows", "count")),
        nfob=int(C("pairs with an importer FOB value", "count")),
        wx=r(C("reported exports, these reporters", "usd") / 1e12, 2),
        wm=r(C("reported imports, these reporters", "usd") / 1e12, 2),
        wgap=r(C("import minus export, these reporters", "usd") / 1e9),
        wgappct=C("import minus export, these reporters", "percent"),
        medcif=C("median absolute gap, CIF", "percent"),
        medfob=C("median absolute gap, FOB", "percent"),
        over10=int(C("pairs disagreeing by more than a tenth", "count")),
        over50=int(C("pairs disagreeing by more than a half", "count")),
        over100=sum(1 for p in pair if abs(p["gap_cif_pct"]) > 100),
        bigx=big["exporter"], bigm=big["importer"],
        bigsaid=r(big["exporter_reported_usd"] / 1e9, 2),
        bigheard=r(big["importer_reported_cif_usd"] / 1e9, 2),
        bigbn=r(abs(big["gap_cif_usd"]) / 1e9, 1), bigpct=big["gap_cif_pct"],
        phsaid=r(phus["exporter_reported_usd"] / 1e9, 2),
        phheard=r(phus["importer_reported_cif_usd"] / 1e9, 2),
        phfob=r(phus["importer_reported_fob_usd"] / 1e9, 2),
        phpct=phus["gap_cif_pct"], phfobpct=phus["gap_fob_pct"],
        sasaid=r(sacn["exporter_reported_usd"] / 1e9, 2),
        saheard=r(sacn["importer_reported_cif_usd"] / 1e9, 2),
        sapct=sacn["gap_cif_pct"],
        nlsaid=r(nlde["exporter_reported_usd"] / 1e9, 2),
        nlheard=r(nlde["importer_reported_cif_usd"] / 1e9, 2),
        nlpct=nlde["gap_cif_pct"],
        worstc=worst["reporter"], worstv=worst["median_abs_gap_cif_pct"],
        bestc=best["reporter"], bestv=best["median_abs_gap_cif_pct"],
        wratio=r(worst["median_abs_gap_cif_pct"] / best["median_abs_gap_cif_pct"], 1),
        smc=sm["reporter"], smstated=r(f(sm["stated_world_total_usd"]) / 1e9, 2),
        smsummed=r(f(sm["partner_rows_sum_usd"]) / 1e9, 2), smpct=f(sm["diff_pct"]),
        smok=104 - len(selfm),
    )
    F["over10pct"] = r(100.0 * F["over10"] / F["npair"], 1)

    p = Page(PAGE)
    p.relocate(
        "global-interconnect-analysis",
        og_image="og-trademirror.png",
        keywords=["mirror statistics", "trade asymmetry", "UN Comtrade",
                  "bilateral trade", "CIF FOB", "open data", "data analysis"],
        dataset_name="Bilateral goods trade reported from both sides, %d" % F["year"],
        dataset_desc=("Every trade flow between 52 major reporters in %d as reported "
                      "by the exporter and by the importer, from UN Comtrade, with "
                      "both CIF and FOB valuations where published" % F["year"]),
        breadcrumb="The Same Trade, Counted Twice",
        crumb_tail="Trade Mirror",
        creator="UN Comtrade",
        dataset_url="https://comtradeapi.un.org/public/v1/preview/C/A/HS",
        tags=["\U0001f4e6 Trade", "UN Comtrade", "%d reporters" % F["nrep"],
              "%s pairs" % format(F["npair"], ","),
              "<span class=\"dot\"></span> %d" % F["year"]],
        info=[("Data Source",
               '<a href="https://comtradeapi.un.org/public/v1/preview/C/A/HS" '
               'target="_blank" rel="noopener">UN Comtrade preview API</a>'),
              ("Coverage",
               "%d reporters &middot; %s matched pairs &middot; %s flow rows for %d"
               % (F["nrep"], format(F["npair"], ","), format(F["nflow"], ","),
                  F["year"])),
              ("Valuation",
               "Exports are FOB and imports CIF; %s pairs carry an importer FOB "
               "value and are compared on it" % format(F["nfob"], ",")),
              ("Licence", "UN Comtrade terms of use")])

    p.head(
        "China Says $116bn. Germany Says $208bn. Same Trade.",
        "Across %s matched pairs of countries in %d, the two sides of the same "
        "trade disagree by a median %s%% — and %s%% even after both are put on "
        "the same valuation. These %d reporters record $%stn of exports and "
        "$%stn of imports."
        % (format(F["npair"], ","), F["year"], F["medcif"], F["medfob"],
           F["nrep"], F["wx"], F["wm"]),
        "Every export is somebody's import. The two numbers disagree by a median "
        "%s%%, and freight explains about a quarter of it." % F["medcif"],
        "China Says $116bn. Germany Says $208bn. Same Trade.")

    p.hero('''                <h1>China Says $116bn. Germany Says $208bn. Same Trade.</h1>
                <p class="{hero_desc}">
                    Every export is somebody&rsquo;s import, so the same goods get
                    counted twice &mdash; once by the country that sent them and
                    once by the country that received them. Across {npair:,}
                    matched pairs in {year} the two figures disagree by a median
                    {medcif}%. Exports are valued before freight and imports
                    after, which explains some of it; putting both sides on the
                    same valuation leaves {medfob}%.
                </p>

                <div class="header-actions">
                    <a href="https://comtradeapi.un.org/public/v1/preview/C/A/HS" target="_blank" class="btn btn-primary">
                        UN Comtrade
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="biggest.gap.bn">${bigbn}B</div>
                        <div class="{label}">Gap on one pair: {bigx} to {bigm}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="median.cif">{medcif}%</div>
                        <div class="{label}">Median disagreement; {medfob}% on like-for-like</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="world.gap.bn">${wgap:,.0f}B</div>
                        <div class="{label}">Imports minus exports, across {nrep} reporters</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="over100">{over100}</div>
                        <div class="{label}">Pairs where one side says more than double</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">{bigx} reports exporting <span data-fact="biggest.gap.said">${bigsaid}</span> billion to {bigm} in {year}. {bigm} reports importing <span data-fact="biggest.gap.heard">${bigheard}</span> billion from {bigx}. The same trade, a <span data-fact="biggest.gap.bn">${bigbn}</span> billion gap, and two of the most capable statistical agencies in the world.</p>
                    <ul class="tldr-list">
                        <li>Across <span data-fact="tm.pairs">{npair:,}</span> matched pairs the median absolute disagreement is <span data-fact="median.cif">{medcif}%</span>. <span data-fact="over10">{over10:,}</span> pairs &mdash; <span data-fact="over10.pct">{over10pct}%</span> &mdash; differ by more than a tenth, <span data-fact="over50">{over50}</span> by more than half, and <span data-fact="over100">{over100}</span> by more than double.</li>
                        <li>Some of that is definitional: exports are valued FOB, at the dock, and imports CIF, with freight and insurance inside. On the <span data-fact="tm.fobpairs">{nfob}</span> pairs where the importer also publishes an FOB figure, the median gap falls to <span data-fact="median.fob">{medfob}%</span>. Shipping explains about a quarter of the disagreement and nothing explains the rest.</li>
                        <li>It is not evenly spread. {worstc}&rsquo;s partners report a median <span data-fact="worst.reporter.pct">{worstv}%</span> more than it does; {bestc}&rsquo;s differ by <span data-fact="best.reporter.pct">{bestv}%</span> &mdash; a factor of <span data-fact="worst.over.best">{wratio}</span>.</li>
                        <li>The gap runs both ways, which is why it is not simply under-reporting. {sasaid} against {saheard}: Saudi Arabia reports <span data-fact="sa.cn.said">${sasaid}</span> billion of exports to China and China reports <span data-fact="sa.cn.heard">${saheard}</span> billion arriving. The Netherlands reports <span data-fact="nl.de.said">${nlsaid}</span> billion to Germany and Germany reports <span data-fact="nl.de.heard">${nlheard}</span> billion &mdash; goods landing at Rotterdam and moving on are Dutch exports and were never German imports.</li>
                        <li>At the top it becomes impossible. These <span data-fact="tm.reporters">{nrep}</span> reporters record <span data-fact="world.exports">${wx}</span> trillion of exports and <span data-fact="world.imports">${wm}</span> trillion of imports: <span data-fact="world.gap.bn">${wgap:,.0f}</span> billion, <span data-fact="world.gap.pct">{wgappct}%</span>, of trade that one side has and the other does not.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "One Pair, Ninety-One Billion Dollars Apart",
                  "Both countries publish a figure for the same goods crossing the "
                  "same border in the same year. Neither is a rough estimate: these "
                  "are customs records, compiled by agencies with every resource.",
                  [("{a} says".format(a=F["bigx"]),
                    "${v}B".format(v=F["bigsaid"]), "biggest.gap.said",
                    "Exported to {b} in {y}.".format(b=F["bigm"], y=F["year"])),
                   ("{b} says".format(b=F["bigm"]),
                    "${v}B".format(v=F["bigheard"]), "biggest.gap.heard",
                    "Imported from {a} in the same year &mdash; "
                    "<span data-fact=\"biggest.gap.bn\">${g}</span> billion more."
                    .format(a=F["bigx"], g=F["bigbn"])),
                   ("The Philippines and the United States",
                    "${a}B vs ${b}B".format(a=F["phsaid"], b=F["phheard"]),
                    "ph.us.exports",
                    "A <span data-fact=\"ph.us.pct\">{p}%</span> gap, and "
                    "<span data-fact=\"ph.us.fobpct\">{q}%</span> once both sides "
                    "are on the same valuation."
                    .format(p=F["phpct"], q=F["phfobpct"]))],
                  "The largest disagreements in dollars, exporter against importer",
                  "pairChart"),

        p.section(2, "Freight Explains About A Quarter Of It",
                  "There is a real and boring reason the two sides differ: an export "
                  "is valued at the dock and an import after it has been shipped and "
                  "insured. That gap is expected. It is also much smaller than what "
                  "is actually there.",
                  [("Median gap, as published",
                    "{v}%".format(v=F["medcif"]), "median.cif",
                    "Absolute difference between the two sides, across all "
                    "<span data-fact=\"tm.pairs\">{n:,}</span> matched pairs."
                    .format(n=F["npair"])),
                   ("Median gap, like for like",
                    "{v}%".format(v=F["medfob"]), "median.fob",
                    "On the <span data-fact=\"tm.fobpairs\">{n}</span> pairs where "
                    "the importer also publishes a pre-freight figure. The rest of "
                    "the gap is not shipping.".format(n=F["nfob"])),
                   ("Pairs differing by more than double",
                    "{v}".format(v=F["over100"]), "over100",
                    "No freight margin is a hundred per cent. "
                    "<span data-fact=\"over50\">{n}</span> pairs differ by more than "
                    "half.".format(n=F["over50"]))],
                  "How far apart the two sides are, by size of disagreement",
                  "gapChart"),

        p.section(3, "It Runs Both Ways",
                  "If this were smuggling or under-invoicing the gap would have a "
                  "sign. It does not. For some pairs the importer records far more "
                  "than the exporter, and for others the exporter records far more "
                  "than the importer.",
                  [("Saudi Arabia to China",
                    "${a}B vs ${b}B".format(a=F["sasaid"], b=F["saheard"]),
                    "sa.cn.said",
                    "China records <span data-fact=\"sa.cn.pct\">{p}%</span> more "
                    "arriving than Saudi Arabia records leaving."
                    .format(p=F["sapct"])),
                   ("Netherlands to Germany",
                    "${a}B vs ${b}B".format(a=F["nlsaid"], b=F["nlheard"]),
                    "nl.de.said",
                    "The other direction: <span data-fact=\"nl.de.pct\">{p}%</span>. "
                    "Goods landing at Rotterdam and moving on are counted as Dutch "
                    "exports and were never German imports."
                    .format(p=F["nlpct"])),
                   ("Worst against best reporter",
                    "{v}&times;".format(v=F["wratio"]), "worst.over.best",
                    "{w}&rsquo;s partners differ from it by a median "
                    "<span data-fact=\"worst.reporter.pct\">{a}%</span>; "
                    "{b}&rsquo;s by <span data-fact=\"best.reporter.pct\">{c}%</span>."
                    .format(w=F["worstc"], a=F["worstv"], b=F["bestc"],
                            c=F["bestv"]))],
                  "Median absolute disagreement between each reporter and its "
                  "partners",
                  "reporterChart"),

        p.section(4, "The Total Is Impossible",
                  "Every export is an import. Summed across the same set of "
                  "reporters, the two totals describe one set of shipments and "
                  "cannot honestly differ. They differ by {wgappct}%.".format(**F),
                  [("Reported exports", "${v}tn".format(v=F["wx"]), "world.exports",
                    "Across all <span data-fact=\"tm.reporters\">{n}</span> "
                    "reporters, {y}.".format(n=F["nrep"], y=F["year"])),
                   ("Reported imports", "${v}tn".format(v=F["wm"]), "world.imports",
                    "The same trade, seen from the other side."),
                   ("The difference", "${v:,.0f}B".format(v=F["wgap"]),
                    "world.gap.bn",
                    "<span data-fact=\"world.gap.pct\">{p}%</span>. Goods that one "
                    "country recorded receiving and no country recorded sending, or "
                    "the reverse.".format(p=F["wgappct"]))],
                  "Reported exports against reported imports, same reporters, same "
                  "year",
                  "worldChart"),

        p.prose(5, "One Country Disagreeing With Itself",
                "The mismatch is not only between countries. Before comparing any "
                "two reporters, this analysis checks each reporter against its own "
                "published total.",
                [("The check",
                  "Comtrade publishes each reporter's trade with partner zero, "
                  "'World', as its own row. That is the country's own total, and it "
                  "should equal the sum of its own partner rows. For %d of the 104 "
                  "reporter-flows read here, it does." % F["smok"]),
                 ("The exception",
                  "%s reports importing $%s billion in total and $%s billion when "
                  "its own partner rows are added up, a %s%% difference. Nothing is "
                  "reconciled here; it is recorded, because a country whose own two "
                  "figures disagree is part of the same story."
                  % (F["smc"], F["smstated"], F["smsummed"], F["smpct"])),
                 ("Why the check exists",
                  "The first version of this analysis read Comtrade's default "
                  "response, which splits every flow by mode of transport and "
                  "customs procedure. Germany's partner rows then summed to 433% of "
                  "its own stated exports and the preview endpoint truncated the "
                  "list at 500 rows. The check caught it; without it the page would "
                  "have shipped confident nonsense.")]),

        p.prose(6, "What These Numbers Are Not",
                "Four limits. The first two would change a conclusion above if "
                "ignored.",
                [("A gap is not fraud",
                  "Several dull mechanisms produce most of it: goods re-exported "
                  "through a third country keep the wrong origin, shipments crossing "
                  "a year end land in different years on the two sides, and low-value "
                  "consignments are excluded at different thresholds. Under-invoicing "
                  "exists too. Nothing here separates them."),
                 ("The FOB comparison is a subset",
                  "Only %s of the %s pairs carry an importer FOB value, so the %s%% "
                  "figure describes those pairs and not the whole set. It is reported "
                  "separately for that reason rather than blended into one number."
                  % (format(F["nfob"], ","), format(F["npair"], ","), F["medfob"])),
                 ("Fifty-two reporters, not the world",
                  "These are the largest traders plus the Philippines, chosen from "
                  "one country's partner list. The totals here are totals for this "
                  "set. A country that reports nothing to Comtrade cannot disagree "
                  "with anybody and is absent from every figure."),
                 ("One year, and a settled one",
                  "%d, because recent years are revised for a long time afterwards "
                  "and a disagreement measured on provisional figures would mostly "
                  "measure the revision cycle." % F["year"])]),
    ]

    HCLS = ("%s fade-up" % p.t["sec_head"]) if p.t["sec_head"] else "fade-up"
    CWRAP = ("%s fade-up" % p.t["card_wrap"]) if p.t["card_wrap"] else "fade-up"
    S.append('''        <section class="{wrap}">
            <div class="container">
                <div class="{hcls}">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="{cwrap}">
                    <ul>
                        <li>{bigx} reports
                        <span data-fact="biggest.gap.said">${bigsaid}</span> billion
                        of exports to {bigm} in {year};
                        {bigm} reports
                        <span data-fact="biggest.gap.heard">${bigheard}</span>
                        billion of imports from {bigx}. A
                        <span data-fact="biggest.gap.bn">${bigbn}</span> billion gap
                        on one pair.</li>
                        <li>Median absolute disagreement across
                        <span data-fact="tm.pairs">{npair:,}</span> pairs is
                        <span data-fact="median.cif">{medcif}%</span>, and
                        <span data-fact="median.fob">{medfob}%</span> once both sides
                        are on the same valuation.</li>
                        <li><span data-fact="over10">{over10:,}</span> pairs differ by
                        more than a tenth,
                        <span data-fact="over50">{over50}</span> by more than half and
                        <span data-fact="over100">{over100}</span> by more than
                        double.</li>
                        <li>{worstc}&rsquo;s partners differ from it by a median
                        <span data-fact="worst.reporter.pct">{worstv}%</span> against
                        {bestc}&rsquo;s
                        <span data-fact="best.reporter.pct">{bestv}%</span>.</li>
                        <li>The gap has no consistent sign: China records
                        <span data-fact="sa.cn.pct">{sapct}%</span> more arriving from
                        Saudi Arabia than Saudi Arabia records sending, while Germany
                        records <span data-fact="nl.de.pct">{nlpct}%</span> against
                        the Netherlands.</li>
                        <li>Summed, these <span data-fact="tm.reporters">{nrep}</span>
                        reporters record
                        <span data-fact="world.exports">${wx}</span> trillion of
                        exports and <span data-fact="world.imports">${wm}</span>
                        trillion of imports &mdash;
                        <span data-fact="world.gap.bn">${wgap:,.0f}</span> billion of
                        trade that only one side has.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    # ---- chart data ---------------------------------------------------------
    TOP = sorted((p_ for p_ in real if p_["exporter_reported_usd"] > 5e9),
                 key=lambda p_: -abs(p_["gap_cif_usd"]))[:14]
    GB = [(0, 5, "0-5%"), (5, 10, "5-10%"), (10, 25, "10-25%"), (25, 50, "25-50%"),
          (50, 100, "50-100%"), (100, 1e9, "over 100%")]
    GC = [sum(1 for p_ in pair if lo <= abs(p_["gap_cif_pct"]) < hi) for lo, hi, _ in GB]
    RS = sorted(big25, key=lambda x: -x["median_abs_gap_cif_pct"])
    RS = RS[:8] + RS[-8:]

    charts = ['''        // 01 the same trade from both sides. Two bars per pair, and the distance
        //    between them is the whole page.
        new Chart(document.getElementById('pairChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'The exporter says', data: %s,
                      backgroundColor: 'rgba(59,130,246,0.85)' },
                    { label: 'The importer says', data: %s,
                      backgroundColor: '#f59e0b' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'USD billions' } } }
            }
        });''' % (js(["%s to %s" % (p_["exporter"][:16], p_["importer"][:16])
                      for p_ in TOP]),
                  js([r(p_["exporter_reported_usd"] / 1e9, 1) for p_ in TOP]),
                  js([r(p_["importer_reported_cif_usd"] / 1e9, 1) for p_ in TOP])),

              '''        // 02 how far apart the two sides are. The last two bars are larger than
        //    any freight margin can account for.
        new Chart(document.getElementById('gapChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Pairs', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Matched pairs' } },
                          x: { title: { display: true, text: 'Absolute disagreement' } } }
            }
        });''' % (js([b[2] for b in GB]), js(GC),
                  js(["#3b82f6", "#3b82f6", "#60a5fa", "#f59e0b", "#f97316",
                      "#ef4444"])),

              '''        // 03 the eight reporters whose partners disagree with them most, and the
        //    eight whose partners disagree least, on one axis.
        new Chart(document.getElementById('reporterChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Median absolute gap (%%)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, type: 'logarithmic',
                               title: { display: true, text: 'Median absolute gap (%%), log scale' } } }
            }
        });''' % (js([x["reporter"][:22] for x in RS]),
                  js([x["median_abs_gap_cif_pct"] for x in RS]),
                  js(["#ef4444"] * 8 + ["#22c55e"] * 8)),

              '''        // 04 the impossible total. Every export is an import, so these two bars
        //    describe one set of shipments.
        new Chart(document.getElementById('worldChart'), {
            type: 'bar',
            data: {
                labels: ['Reported exports', 'Reported imports'],
                datasets: [{ label: 'USD trillions', data: %s,
                             backgroundColor: ['#3b82f6', '#f59e0b'] }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'USD trillions' } } }
            }
        });''' % js([F["wx"], F["wm"]]),
    ]

    p.sections(S)
    p.charts(charts)
    p.faq({
        "Why do two countries report different figures for the same trade?":
            "Several reasons, and fraud is only one of them. Exports are valued FOB "
            "and imports CIF, so freight and insurance sit inside the import figure. "
            "Goods re-exported through a third country keep the wrong origin. "
            "Shipments crossing a year end land in different years on each side. "
            "Low-value consignments are excluded at different thresholds. Across %s "
            "pairs in %d the median absolute gap is %s%%, falling to %s%% when both "
            "sides are put on the same valuation."
            % (format(F["npair"], ","), F["year"], F["medcif"], F["medfob"]),
        "How big can the disagreement get?":
            "%s reports exporting $%s billion to %s in %d and %s reports importing "
            "$%s billion -- a $%s billion gap on one pair. Across the whole set, %s "
            "pairs differ by more than a tenth, %d by more than half and %d by more "
            "than double."
            % (F["bigx"], F["bigsaid"], F["bigm"], F["year"], F["bigm"],
               F["bigheard"], F["bigbn"], format(F["over10"], ","), F["over50"],
               F["over100"]),
        "Does the world import more than it exports?":
            "On these figures, yes, which cannot be true. The %d reporters read here "
            "record $%s trillion of exports and $%s trillion of imports for %d: a "
            "difference of $%s billion, %s%%, on flows that are by definition the "
            "same flows."
            % (F["nrep"], F["wx"], F["wm"], F["year"], format(int(F["wgap"]), ","),
               F["wgappct"]),
        "Which countries disagree with their partners most?":
            "%s: its partners report a median %s%% more or less than it does, across "
            "the pairs where both sides report. %s is the closest to its partners at "
            "%s%%, a factor of %s between them. The gap runs in both directions -- "
            "China records %s%% more arriving from Saudi Arabia than Saudi Arabia "
            "records sending, while Germany records %s%% against the Netherlands, "
            "because goods landing at Rotterdam and moving on are Dutch exports that "
            "were never German imports."
            % (F["worstc"], F["worstv"], F["bestc"], F["bestv"], F["wratio"],
               F["sapct"], F["nlpct"]),
        "Where does this bilateral trade data come from?":
            "UN Comtrade's preview API, which is free and needs no key. It reads %d "
            "reporters for %d, %s flow rows, matched into %s pairs where both sides "
            "report the same trade. Each reporter's partner rows are checked against "
            "that reporter's own published world total before anything is compared; "
            "%d of the 104 reporter-flows agree, and the one that does not is "
            "recorded rather than reconciled."
            % (F["nrep"], F["year"], format(F["nflow"], ","),
               format(F["npair"], ","), F["smok"]),
    })
    p.save(len(S), len(charts))
    blog(F)


BLOG = "blog/global-trade-mirror-analysis.html"
TITLE = "Two Countries Counted The Same Ships. They Got Different Answers."
DESC = ("China says it sent Germany $116 billion of goods. Germany says it got "
        "$208 billion. Same ships, same year, two very careful countries.")
SUB = "China says $116 billion. Germany says $208 billion. Same ships."


def fct(k, v):
    return '<span data-fact="%s">%s</span>' % (k, v)


def blog(F):
    import io, re
    src = io.open(BLOG, encoding="utf-8").read()

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, lambda _m: rep, src, count=1)
        if n != 1:
            raise SystemExit("blog: %s matched %d times" % (why, n))

    swap(r"<title>[^<]*</title>", "<title>%s | Allan Ni\u00f1al</title>" % TITLE, "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % DESC, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="%s | Allan Ni\u00f1al">' % TITLE, "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % DESC, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="%s">' % TITLE, "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % DESC, "tw:desc")
    swap(r'"headline": "[^"]*"', '"headline": "%s"' % TITLE, "headline")
    swap(r'"description": "[^"]*"', '"description": "%s"' % DESC, "ld desc")
    src = src.replace("global-interconnect-analysis", "global-trade-mirror-analysis")
    swap(r'<span class="current">[^<]*</span>',
         '<span class="current">Trade Mirror</span>', "crumb")
    swap(r'<h1>[^<]*</h1>', "<h1>%s</h1>" % TITLE, "h1")
    swap(r'<p class="subtitle">[^<]*</p>', '<p class="subtitle">%s</p>' % SUB, "subtitle")

    a = src.index('<div class="article-content">')
    a = src.index("\n", a) + 1
    b = src.index('                <div class="project-link-box">')
    io.open(BLOG, "w", encoding="utf-8").write(src[:a] + body(F) + src[b:])
    print("rebuilt %s" % BLOG)


def body(F):
    g = fct
    return """                <p>When a ship leaves China for Germany, two countries write down what is on it.</p>

                <p>China writes down what left. Germany writes down what arrived.</p>

                <p>It is the same ship. So the two numbers should match.</p>

                <p>China says it sent {bigsaid} billion dollars of goods in {year}.</p>

                <p>Germany says it got {bigheard} billion.</p>

                <div class="stat-callout">
                    <div class="stat-number">${bigbn_f}B</div>
                    <div class="stat-label">The gap between the two, on one pair of countries</div>
                </div>

                <h2>It Is Not Just Those Two</h2>

                <p>I looked at {npair} pairs of countries. Both sides wrote down a number for each one.</p>

                <p>The middle pair disagreed by {medcif} per cent.</p>

                <p>{over10} pairs disagreed by more than a tenth. {over50} disagreed by more than half.</p>

                <p>And {over100} pairs disagreed by more than double. One side said at least twice what the other said.</p>

                <h2>Some Of It Is Boring</h2>

                <p>There is a dull reason for part of this.</p>

                <p>When a country writes down what left, it counts the goods at the dock. No shipping. No insurance.</p>

                <p>When a country writes down what arrived, it adds the shipping and the insurance on top.</p>

                <p>So the arriving number should be a bit bigger. That is normal.</p>

                <p>Some countries publish both kinds of number. On those {nfob} pairs, I compared like with like.</p>

                <p>The gap only fell from {medcif} per cent to {medfob} per cent.</p>

                <p>So shipping explains about a quarter of it. Nothing explains the rest.</p>

                <h2>It Goes Both Ways</h2>

                <p>If people were hiding goods, the gap would lean one way. It does not.</p>

                <p>Saudi Arabia says it sent China {sasaid} billion. China says it got {saheard} billion. China says much more.</p>

                <p>The Netherlands says it sent Germany {nlsaid} billion. Germany says it got {nlheard} billion. Here the sender says more.</p>

                <p>That second one has a reason. Lots of goods land at Rotterdam and then drive on somewhere else. The Netherlands counts them going out. Germany never counts them coming in.</p>

                <h2>Some Countries Match Better Than Others</h2>

                <p>{bestc} is closest to its partners. They differ by about {bestv} per cent.</p>

                <p>{worstc} is furthest. Its partners differ by about {worstv} per cent.</p>

                <p>That is {wratio} times as far apart.</p>

                <h2>Add It All Up And It Cannot Be True</h2>

                <p>Every ship that leaves somewhere arrives somewhere.</p>

                <p>So if you add up everything all these countries say they sent, and everything they say they got, the two totals have to be the same.</p>

                <p>They say they sent {wx} trillion dollars.</p>

                <p>They say they got {wm} trillion.</p>

                <div class="stat-callout">
                    <div class="stat-number">${wgap_f}B</div>
                    <div class="stat-label">Goods that arrived somewhere but left nowhere</div>
                </div>

                <h2>One Country Did Not Even Match Itself</h2>

                <p>Before comparing any two countries, I checked each one against its own total.</p>

                <p>Each country writes one big number for everything it bought. It also writes a number for each country it bought from. Adding up the small ones should give the big one.</p>

                <p>For {smok} out of 104, it did.</p>

                <p>{smc} said {smstated} billion in total. Its own smaller numbers added up to {smsummed} billion.</p>

                <h2>Three Things I Cannot Tell You</h2>

                <p>A gap is not proof of cheating. Goods that pass through a third country get the wrong home written on them. A ship that leaves in December and lands in January sits in two different years. And each country ignores tiny parcels at a different size.</p>

                <p>The like-for-like number only covers {nfob} of the {npair2} pairs, because most countries only publish one kind of number. So I keep it separate instead of mixing it in.</p>

                <p>And this is {year2}, one year, on purpose. Recent years keep getting corrected, so a gap measured on them would mostly be measuring the corrections.</p>

""".format(
        bigsaid=g("biggest.gap.said", F["bigsaid"]),
        bigheard=g("biggest.gap.heard", F["bigheard"]),
        bigbn_f=F["bigbn"], year=F["year"], year2=F["year"],
        npair=g("tm.pairs", format(F["npair"], ",")), npair2=format(F["npair"], ","),
        medcif=g("median.cif", F["medcif"]), medfob=g("median.fob", F["medfob"]),
        over10=g("over10", format(F["over10"], ",")),
        over50=g("over50", F["over50"]), over100=g("over100", F["over100"]),
        nfob=g("tm.fobpairs", F["nfob"]),
        sasaid=g("sa.cn.said", F["sasaid"]), saheard=g("sa.cn.heard", F["saheard"]),
        nlsaid=g("nl.de.said", F["nlsaid"]), nlheard=g("nl.de.heard", F["nlheard"]),
        bestc=F["bestc"], bestv=g("best.reporter.pct", F["bestv"]),
        worstc=F["worstc"], worstv=g("worst.reporter.pct", F["worstv"]),
        wratio=g("worst.over.best", F["wratio"]),
        wx=g("world.exports", F["wx"]), wm=g("world.imports", F["wm"]),
        wgap_f="{:,.0f}".format(F["wgap"]),
        smok=g("self.consistent", F["smok"]), smc=F["smc"],
        smstated=g("self.stated", F["smstated"]),
        smsummed=g("self.summed", F["smsummed"]),
    )


if __name__ == "__main__":
    main()
