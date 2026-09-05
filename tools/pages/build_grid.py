#!/usr/bin/env python3
"""Regenerate projects/global-grid-analysis.html from data/global-grid CSVs.

    .venv/bin/python tools/pages/build_grid.py

The direct extension of the Philippine electricity page. That one found renewables
falling from 42.89% to 23.32% of generation while renewable output nearly doubled,
because demand grew faster -- a story an annual percentage can tell.

This one is about what an annual percentage cannot tell you. At hourly resolution
across eight European grids for the whole of 2025:

  Austria's annual share is 85.6%, and its worst single hour of the year is 45.92%.
  The Netherlands' annual share is 22.93%. So Austria's worst hour of the entire
  year is exactly twice the Dutch annual average.

  Germany sits at 63.38% for the year, and between 30.26% and 89.48% for 90% of its
  hours -- a 59-point spread around a single published number.

  The Netherlands spent 4,407 hours, 50.3% of the year, at or below one fifth
  renewable.

The second finding is that the worst week is not a national event. Four of the eight
countries had their worst renewable week of the year begin in January 2025, and the
Dutch, Belgian, German and Austrian windows all overlap: a continental Dunkelflaute,
which is exactly the condition under which interconnection cannot help, because
everybody is becalmed at once. France's worst renewable week is 1.52% fossil and
79.79% nuclear, which is the whole argument about what a low-carbon grid needs
standing behind it.

The third is that negative prices are market rules as much as physics. Seven of the
eight zones went negative in 2025, 3,917 intervals in total, Belgium reaching
-462.33 EUR/MWh. Italy never went negative once -- and its minimum was exactly
0.00, which is a floor rather than a coincidence. Spain's floor is exactly -15.00.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-grid"
PAGE = "projects/global-grid-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    cty = rows("gg_country")
    hist = rows("gg_share_hist")
    dun = rows("gg_dunkelflaute")
    px = rows("gg_price_country")
    cov = {x["property"]: x["value"] for x in rows("gg_coverage")}

    cty.sort(key=lambda x: -f(x["annual_renewable_pct"]))
    px.sort(key=lambda x: -f(x["negative_pct"]))
    C = {x["country"]: x for x in cty}
    P = {x["country"]: x for x in px}
    Dun = {x["country"]: x for x in dun}
    top, bot = cty[0], cty[-1]
    zero = [x for x in px if int(x["negative_intervals"]) == 0]
    deepest = min(px, key=lambda x: f(x["min_price"]))
    deepmean = min((x for x in px if int(x["negative_intervals"]) > 0),
                   key=lambda x: f(x["mean_when_negative"]))
    worst = min(dun, key=lambda x: f(x["week_renewable_pct"]))

    F = dict(
        n=int(cov["countries"]), year=int(cov["year"]),
        hours=int(cov["country-hours"]), pxint=int(cov["price intervals"]),
        q15=sum(1 for k, v in cov.items()
                if k.startswith("native resolution") and v == "15min"),
        q60=sum(1 for k, v in cov.items()
                if k.startswith("native resolution") and v == "60min"),
        topc=top["country"], topann=f(top["annual_renewable_pct"]),
        topmin=f(top["min_pct"]), topmax=f(top["max_pct"]),
        top80=int(top["hours_at_or_above_80"]),
        botc=bot["country"], botann=f(bot["annual_renewable_pct"]),
        botmin=f(bot["min_pct"]), botmax=f(bot["max_pct"]),
        bot20=int(bot["hours_at_or_below_20"]),
        bot20pct=r(100.0 * int(bot["hours_at_or_below_20"])
                   / int(bot["hours"]), 1),
        deann=f(C["Germany"]["annual_renewable_pct"]),
        demean=f(C["Germany"]["mean_hourly_pct"]),
        demin=f(C["Germany"]["min_pct"]), demax=f(C["Germany"]["max_pct"]),
        dep5=f(C["Germany"]["p5_pct"]), dep95=f(C["Germany"]["p95_pct"]),
        de80=int(C["Germany"]["hours_at_or_above_80"]),
        de80pct=r(100.0 * int(C["Germany"]["hours_at_or_above_80"])
                  / int(C["Germany"]["hours"]), 1),
        dunc=worst["country"], dunpct=f(worst["week_renewable_pct"]),
        dunann=f(worst["annual_renewable_pct"]),
        dunfos=f(worst["week_fossil_pct"]),
        dunfrom=worst["week_from"][:10],
        dunjan=sum(1 for x in dun if x["week_from"][:7] == "2025-01"),
        dedun=f(Dun["Germany"]["week_renewable_pct"]),
        dedunfos=f(Dun["Germany"]["week_fossil_pct"]),
        frdun=f(Dun["France"]["week_renewable_pct"]),
        frdunfos=f(Dun["France"]["week_fossil_pct"]),
        frdunnuc=f(Dun["France"]["week_nuclear_pct"]),
        negc=px[0]["country"], negint=int(px[0]["negative_intervals"]),
        negpct=f(px[0]["negative_pct"]),
        negn=sum(1 for x in px if int(x["negative_intervals"]) > 0),
        negtot=sum(int(x["negative_intervals"]) for x in px),
        deep=f(deepest["min_price"]), deepc=deepest["country"],
        zeroc=zero[0]["country"] if zero else "",
        zeromin=f(zero[0]["min_price"]) if zero else 0.0,
        esmin=f(P["Spain"]["min_price"]), esneg=int(P["Spain"]["negative_intervals"]),
        dmc=deepmean["country"], dmv=f(deepmean["mean_when_negative"]),
        hic=max(px, key=lambda x: f(x["mean_price"]))["country"],
        hiv=f(max(px, key=lambda x: f(x["mean_price"]))["mean_price"]),
        loc=min(px, key=lambda x: f(x["mean_price"]))["country"],
        lov=f(min(px, key=lambda x: f(x["mean_price"]))["mean_price"]),
    )
    F["ratio"] = r(F["topmin"] / F["botann"], 2)
    F["despread"] = r(F["dep95"] - F["dep5"], 2)

    p = Page(PAGE)
    p.relocate(
        "electricity-analysis",
        og_image="og-grid.png",
        keywords=["European electricity grid", "renewable share", "negative prices",
                  "Dunkelflaute", "ENTSO-E", "open data", "data analysis"],
        dataset_name="European grid generation and day-ahead prices, 2025",
        dataset_desc=("Hourly generation by source for eight European countries and "
                      "day-ahead prices for eight bidding zones across 2025, from "
                      "Fraunhofer ISE Energy-Charts"),
        breadcrumb="The European Grid, Hour By Hour",
        crumb_tail="European Grid",
        creator="Fraunhofer ISE / ENTSO-E / Bundesnetzagentur",
        dataset_url="https://api.energy-charts.info/",
        tags=["\u26a1 Energy", "Energy-Charts", "ENTSO-E", "8 countries",
              "<span class=\"dot\"></span> 2025, hourly"],
        info=[("Data Sources",
               '<a href="https://api.energy-charts.info/" target="_blank" '
               'rel="noopener">Fraunhofer ISE Energy-Charts</a> &middot; '
               '<a href="https://transparency.entsoe.eu/" target="_blank" '
               'rel="noopener">ENTSO-E</a> &middot; '
               '<a href="https://www.smard.de/en" target="_blank" '
               'rel="noopener">SMARD</a>'),
              ("Coverage",
               "8 countries &middot; every hour of 2025 &middot; "
               "%s country-hours and %s price intervals"
               % (format(F["hours"], ","), format(F["pxint"], ","))),
              ("Resolution",
               "%d countries report quarter-hourly, %d hourly &mdash; all "
               "aggregated to hourly" % (F["q15"], F["q60"])),
              ("Licence", "CC BY 4.0")])

    p.hero('''                <h1>An Annual Renewable Share Hides Both Its Tails</h1>
                <p class="{hero_desc}">
                    {n} European grids, every hour of {year}. Austria's annual
                    share is {topann}% and its worst single hour of the year is
                    {topmin}% &mdash; which is exactly {ratio} times the
                    Netherlands' figure for the whole year. Seven of the eight
                    markets paid people to generate at some point.
                </p>

                <div class="header-actions">
                    <a href="https://api.energy-charts.info/" target="_blank" class="btn btn-primary">
                        Energy-Charts API
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="de.spread">{despread}</div>
                        <div class="{label}">Point spread in Germany's hourly share, p5 to p95</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="bottom.hours20">{bot20:,}</div>
                        <div class="{label}">Hours the Dutch grid was under a fifth renewable</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="neg.total">{negtot:,}</div>
                        <div class="{label}">Intervals with a negative day-ahead price</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="dunkel.january">{dunjan} of {n}</div>
                        <div class="{label}">Countries whose worst week began in January</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">{topc} generated <span data-fact="top.annual">{topann}%</span> renewable electricity across {year}, and its worst single hour of the year was <span data-fact="top.min">{topmin}%</span>. The {botc} managed <span data-fact="bottom.annual">{botann}%</span> for the entire year. One grid's worst hour is <span data-fact="worst.hour.beats.annual">{ratio}</span> times another's annual average.</p>
                    <ul class="tldr-list">
                        <li>Germany is published as <span data-fact="de.annual">{deann}%</span> renewable for {year}. Ninety per cent of its hours fall between <span data-fact="de.p5">{dep5}%</span> and <span data-fact="de.p95">{dep95}%</span> &mdash; a <span data-fact="de.spread">{despread}</span>-point spread around that one number &mdash; and it spent <span data-fact="de.hours80">{de80:,}</span> hours, <span data-fact="de.hours80.pct">{de80pct}%</span> of the year, at or above 80%.</li>
                        <li>The {botc} spent <span data-fact="bottom.hours20">{bot20:,}</span> hours &mdash; <span data-fact="bottom.hours20.pct">{bot20pct}%</span> of the year &mdash; at or below a fifth renewable, and reached <span data-fact="bottom.max">{botmax}%</span> at its best.</li>
                        <li>The worst renewable week is not a national event. <span data-fact="dunkel.january">{dunjan}</span> of {n} countries had theirs begin in January {year}, and the windows overlap. The {dunc} week from {dunfrom} ran <span data-fact="dunkel.worst.pct">{dunpct}%</span> renewable against <span data-fact="dunkel.worst.annual">{dunann}%</span> for the year, with <span data-fact="dunkel.worst.fossil">{dunfos}%</span> fossil filling it.</li>
                        <li>France's worst renewable week was <span data-fact="dunkel.fr.pct">{frdun}%</span> renewable and only <span data-fact="dunkel.fr.fossil">{frdunfos}%</span> fossil, because <span data-fact="dunkel.fr.nuclear">{frdunnuc}%</span> was nuclear. That is the entire argument about what a low-carbon grid needs behind it, in one week of data.</li>
                        <li><span data-fact="neg.countries">{negn}</span> of the {n} markets went negative, <span data-fact="neg.total">{negtot:,}</span> intervals in total, {deepc} reaching <span data-fact="neg.deepest">{deep}</span> EUR/MWh. {zeroc} never went negative once &mdash; and its minimum was exactly <span data-fact="neg.zero.min">{zeromin}</span>, which is a price floor rather than a quiet grid.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "One Number, Two Very Different Years",
                  "Every grid here publishes an annual renewable share. Underneath "
                  "each one is a distribution of {hours:,} hourly shares, and the "
                  "distributions do not resemble each other even where the annual "
                  "figures are close.".format(**F),
                  [(F["topc"], "{v}%".format(v=F["topann"]), "top.annual",
                    "Annual share. Its worst hour of the year was "
                    "<span data-fact=\"top.min\">{m}%</span> and its best "
                    "<span data-fact=\"top.max\">{x}%</span>, and it spent "
                    "<span data-fact=\"top.hours80\">{h:,}</span> hours at or above "
                    "80%.".format(m=F["topmin"], x=F["topmax"], h=F["top80"])),
                   (F["botc"], "{v}%".format(v=F["botann"]), "bottom.annual",
                    "Annual share, with a range of "
                    "<span data-fact=\"bottom.min\">{m}%</span> to "
                    "<span data-fact=\"bottom.max\">{x}%</span>."
                    .format(m=F["botmin"], x=F["botmax"])),
                   ("The comparison that matters",
                    "{v}&times;".format(v=F["ratio"]), "worst.hour.beats.annual",
                    "{a}'s worst single hour of the entire year, divided by {b}'s "
                    "average for the entire year. An annual share cannot express "
                    "that.".format(a=F["topc"], b=F["botc"]))],
                  "Annual renewable share against the hourly range behind it",
                  "rangeChart"),
        p.section(2, "Germany, In The Detail",
                  "The grid most people mean when they say &ldquo;the energy "
                  "transition&rdquo;. Its published figure for {year} is one number; "
                  "the year it describes is not.".format(**F),
                  [("Published for the year", "{v}%".format(v=F["deann"]),
                    "de.annual",
                    "Energy-weighted: total renewable megawatt-hours over total. The "
                    "mean of its hourly shares is "
                    "<span data-fact=\"de.mean.hourly\">{m}%</span>, which is a "
                    "different statistic and deliberately shown beside it."
                    .format(m=F["demean"])),
                   ("Ninety per cent of hours",
                    "{a}%&ndash;{b}%".format(a=F["dep5"], b=F["dep95"]), "de.p5",
                    "A <span data-fact=\"de.spread\">{s}</span>-point spread. The "
                    "extremes are wider still: "
                    "<span data-fact=\"de.min\">{lo}%</span> at worst and "
                    "<span data-fact=\"de.max\">{hi}%</span> at best."
                    .format(s=F["despread"], lo=F["demin"], hi=F["demax"])),
                   ("Hours at or above 80%", "{v:,}".format(v=F["de80"]),
                    "de.hours80",
                    "<span data-fact=\"de.hours80.pct\">{p}%</span> of the year "
                    "running on a grid that is four fifths renewable &mdash; and "
                    "the same year contains the January week in the next section."
                    .format(p=F["de80pct"]))],
                  "Hours in each 10-point band of renewable share, by country",
                  "histChart"),
        p.section(3, "The Week The Wind Stopped Everywhere At Once",
                  "For each country, the worst rolling 168-hour window of the year, "
                  "found by search rather than by picking calendar weeks. The dates "
                  "are the finding: {dunjan} of {n} fall in January {year} and the "
                  "windows overlap.".format(**F),
                  [("{c}, week of {d}".format(c=F["dunc"], d=F["dunfrom"]),
                    "{v}%".format(v=F["dunpct"]), "dunkel.worst.pct",
                    "Against <span data-fact=\"dunkel.worst.annual\">{a}%</span> for "
                    "the year, with "
                    "<span data-fact=\"dunkel.worst.fossil\">{f}%</span> fossil "
                    "filling the gap.".format(a=F["dunann"], f=F["dunfos"])),
                   ("Germany, the same week",
                    "{v}%".format(v=F["dedun"]), "dunkel.de.pct",
                    "Down from <span data-fact=\"de.annual\">{a}%</span> for the "
                    "year, with "
                    "<span data-fact=\"dunkel.de.fossil\">{f}%</span> fossil. Two "
                    "neighbouring grids becalmed in the same window is precisely "
                    "when a cable to the neighbour is worth least."
                    .format(a=F["deann"], f=F["dedunfos"])),
                   ("France, for contrast",
                    "{v}% fossil".format(v=F["frdunfos"]), "dunkel.fr.fossil",
                    "Its worst renewable week ran "
                    "<span data-fact=\"dunkel.fr.pct\">{r}%</span> renewable and "
                    "<span data-fact=\"dunkel.fr.nuclear\">{nu}%</span> nuclear. "
                    "Same weather, entirely different bill."
                    .format(r=F["frdun"], nu=F["frdunnuc"]))],
                  "Worst renewable week of the year against the annual share",
                  "dunkelChart"),
        p.section(4, "When Electricity Costs Less Than Nothing",
                  "The day-ahead auction, settled prices, {pxint:,} intervals. A "
                  "negative price means a generator paid to deliver: there was more "
                  "must-run output than demand and something had to give."
                  .format(**F),
                  [("{c}".format(c=F["negc"]), "{v}%".format(v=F["negpct"]),
                    "neg.top.pct",
                    "Of intervals below zero &mdash; "
                    "<span data-fact=\"neg.top.intervals\">{n}</span> of them. "
                    "Across all zones, "
                    "<span data-fact=\"neg.total\">{t:,}</span>."
                    .format(n=F["negint"], t=F["negtot"])),
                   ("Deepest single price", "{v}".format(v=F["deep"]),
                    "neg.deepest",
                    "EUR/MWh, in {c}. Someone was paid nearly five hundred euros a "
                    "megawatt-hour to take electricity away."
                    .format(c=F["deepc"])),
                   ("Where it bites hardest on average", F["dmc"],
                    "neg.deepest.mean",
                    "At <span data-fact=\"neg.deepest.mean.value\">{v}</span> "
                    "EUR/MWh when negative &mdash; deeper than {c}, which goes "
                    "negative almost twice as often. Frequency and severity are "
                    "different questions.".format(v=F["dmv"], c=F["negc"]))],
                  "Negative day-ahead intervals by bidding zone",
                  "negChart"),
        p.section(5, "Some Of This Is Physics And Some Is Rules",
                  "The eight zones do not just differ in how often prices go "
                  "negative. They differ in how far they are allowed to.",
                  [("{c} never went negative".format(c=F["zeroc"]),
                    "{v}".format(v=F["zeromin"]), "neg.zero.min",
                    "EUR/MWh was its minimum for the entire year. Not a low number "
                    "&mdash; exactly zero, which is a floor. Its mean price was "
                    "also the highest of the eight at "
                    "<span data-fact=\"price.highest.mean.value\">{h}</span>."
                    .format(h=F["hiv"])),
                   ("Spain floors elsewhere", "{v}".format(v=F["esmin"]),
                    "es.min",
                    "EUR/MWh, and it still went negative "
                    "<span data-fact=\"es.negative\">{n}</span> times. A different "
                    "floor, not a different grid.".format(n=F["esneg"])),
                   ("Cheapest on average", F["loc"], "price.lowest.mean",
                    "At <span data-fact=\"price.lowest.mean.value\">{v}</span> "
                    "EUR/MWh across the year &mdash; the most nuclear-heavy grid "
                    "here, and the one whose worst renewable week barely touched "
                    "fossil fuel.".format(v=F["lov"]))],
                  "Mean and minimum day-ahead price by zone", "priceChart"),
        p.prose(6, "What A Share Of Generation Is Not",
                "Five limits. The first two would each move every number on this "
                "page if handled differently, so they are stated rather than "
                "buried.",
                [("It is a share of generation, not of consumption",
                  "Cross-border trade is excluded, so a country importing renewable "
                  "power from its neighbour looks less renewable than what it "
                  "actually consumes, and an exporter looks greener. On a coupled "
                  "continent that gap is large, and it is the single biggest reason "
                  "not to read these as national virtue scores."),
                 ("Rooftop solar is largely invisible",
                  "ENTSO-E transparency data covers transmission-connected plant. "
                  "Distribution-level solar &mdash; which in several of these "
                  "countries is most of the solar &mdash; does not appear as "
                  "generation. Every solar share here is understated, and "
                  "understated most in the sunniest countries."),
                 ("Storage is excluded in both directions",
                  "Pumped-storage output and the consumption that fills it are both "
                  "left out. Counting the output as renewable would double-count the "
                  "electricity used to pump the water uphill, which on a windy night "
                  "may itself have been fossil."),
                 ("Curtailed generation is not generation",
                  "A wind farm paid to switch off during a negative-price hour does "
                  "not appear in these figures at all. So the renewable share "
                  "understates what was available, and it understates it precisely "
                  "in the hours the price section is about."),
                 ("Hourly, from mixed native resolutions",
                  "{q15} of these countries report quarter-hourly and {q60} hourly. "
                  "Comparing them requires one grid, so everything is averaged to "
                  "the hour &mdash; averaged rather than summed, which keeps the "
                  "unit as power rather than silently turning it into energy. A "
                  "15-minute analysis would show wider extremes than anything on "
                  "this page.".format(**F))]),
        p.prose(7, "Method",
                "One fetcher, eight CSVs, and a category list written out by hand "
                "on purpose.",
                [("Categories are named, never matched on a substring",
                  "&ldquo;Fossil coal-derived gas&rdquo; contains the word gas and "
                  "is not renewable. &ldquo;Hydro pumped storage&rdquo; contains "
                  "hydro and is not generation. Every production type is assigned by "
                  "name, and a check fails on any type filed as renewable whose name "
                  "begins with Fossil."),
                 ("Two different annual statistics, kept apart",
                  "The energy-weighted share is total renewable megawatt-hours over "
                  "total megawatt-hours. The mean of hourly shares treats a windy "
                  "midnight and a still midday as equally important. Germany's are "
                  "{a}% and {b}%, and a check asserts they never come out equal, "
                  "because if they did one of them is being computed wrongly."
                  .format(a=F["deann"], b=F["demean"])),
                 ("The worst week is searched for, not chosen",
                  "A rolling 168-hour window over the whole ordered year, taking the "
                  "minimum. Picking calendar weeks would have found a different and "
                  "less bad answer, and picking the week after seeing the result "
                  "would be choosing the finding first."),
                 ("The year boundary is local, not UTC",
                  "The API takes start and end in the market's own time, so a "
                  "request for 2025 returns a series labelled from 23:00 on 31 "
                  "December &mdash; central European time is UTC+1 in winter. It is "
                  "a full local year, and the first version of the span check "
                  "assumed UTC and failed on it."),
                 ("Paced, cached, not committed",
                  "The API answers &ldquo;Too Many Requests&rdquo; after a handful "
                  "of quick calls and a year needs about two hundred, so requests "
                  "are spaced and cached on disk. The cache is not committed; the "
                  "eight derived CSVs are."),
                 ("Licensing",
                  "Energy-Charts is CC BY 4.0. Generation derives from ENTSO-E "
                  "transparency data and prices from Bundesnetzagentur / SMARD, both "
                  "cited on this page. ENTSO-E's own API needs a registered token, "
                  "which is why this reads Energy-Charts instead.")]),
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
                        <li>{topc}'s worst single hour of {year}
                        (<span data-fact="top.min">{topmin}%</span> renewable) is
                        <span data-fact="worst.hour.beats.annual">{ratio}</span>
                        times the {botc}' average for the whole year
                        (<span data-fact="bottom.annual">{botann}%</span>).</li>
                        <li>Germany's published
                        <span data-fact="de.annual">{deann}%</span> sits on a
                        distribution running
                        <span data-fact="de.p5">{dep5}%</span> to
                        <span data-fact="de.p95">{dep95}%</span> for ninety per cent
                        of hours &mdash; a
                        <span data-fact="de.spread">{despread}</span>-point
                        spread.</li>
                        <li>The {botc} spent
                        <span data-fact="bottom.hours20">{bot20:,}</span> hours,
                        <span data-fact="bottom.hours20.pct">{bot20pct}%</span> of
                        the year, at or below a fifth renewable.</li>
                        <li><span data-fact="dunkel.january">{dunjan}</span> of {n}
                        countries had their worst renewable week begin in January
                        {year}, with overlapping windows &mdash; a continental event,
                        which is when interconnection helps least.</li>
                        <li>France's worst renewable week was
                        <span data-fact="dunkel.fr.fossil">{frdunfos}%</span> fossil
                        because
                        <span data-fact="dunkel.fr.nuclear">{frdunnuc}%</span> was
                        nuclear.</li>
                        <li><span data-fact="neg.countries">{negn}</span> of the {n}
                        markets went negative,
                        <span data-fact="neg.total">{negtot:,}</span> intervals,
                        deepest <span data-fact="neg.deepest">{deep}</span> EUR/MWh
                        in {deepc}. {zeroc} never did &mdash; its minimum was exactly
                        <span data-fact="neg.zero.min">{zeromin}</span>, a floor
                        rather than a quiet grid.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    CN = [x["country"] for x in cty]
    BANDS = sorted({(int(x["band_from"]), int(x["band_to"])) for x in hist})
    HB = {(x["country"], int(x["band_from"])): int(x["hours"]) for x in hist}
    DUNS = sorted(dun, key=lambda x: f(x["week_renewable_pct"]))
    PXS = px

    charts = ['''        // 01 the annual figure as a point, the p5-p95 as a bar, the min and max as
        //    whiskers drawn as their own thin series. The gap between the dot and the
        //    bar is the argument of the page.
        new Chart(document.getElementById('rangeChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Middle 90%% of hours (p5 to p95)', data: %s,
                      backgroundColor: 'rgba(59,130,246,0.45)',
                      borderColor: '#3b82f6', borderWidth: 1 },
                    { type: 'line', label: 'Annual share (energy-weighted)',
                      data: %s, borderColor: '#ef4444', borderWidth: 0,
                      pointRadius: 6, pointStyle: 'rectRot', showLine: false },
                    { type: 'line', label: 'Worst hour of the year', data: %s,
                      borderColor: '#f59e0b', borderWidth: 0, pointRadius: 4,
                      showLine: false },
                    { type: 'line', label: 'Best hour of the year', data: %s,
                      borderColor: '#22c55e', borderWidth: 0, pointRadius: 4,
                      showLine: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: '%% renewable of generation' } } }
            }
        });''' % (js(CN),
                  js([[f(x["p5_pct"]), f(x["p95_pct"])] for x in cty]),
                  js([f(x["annual_renewable_pct"]) for x in cty]),
                  js([f(x["min_pct"]) for x in cty]),
                  js([f(x["max_pct"]) for x in cty])),

              '''        // 02 the distribution itself, stacked by band. A single annual percentage is
        //    one summary of one of these columns.
        new Chart(document.getElementById('histChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { x: { stacked: true },
                          y: { stacked: true, beginAtZero: true,
                               title: { display: true, text: 'Hours of the year' } } }
            }
        });''' % (js(CN),
                  "[" + ", ".join(
                      "{ label: %s, data: %s, backgroundColor: '%s' }"
                      % (js("%d-%d%%" % (lo, hi) if hi < 999 else "100%+"),
                         js([HB.get((c, lo), 0) for c in CN]), col)
                      for (lo, hi), col in zip(
                          BANDS,
                          ["#7f1d1d", "#9a3412", "#b45309", "#ca8a04", "#65a30d",
                           "#16a34a", "#059669", "#0d9488", "#0891b2", "#2563eb",
                           "#4f46e5"])) + "]"),

              '''        // 03 the worst week against the year. The distance between the pair is what a
        //    grid has to cover with something that is not weather.
        new Chart(document.getElementById('dunkelChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Worst renewable week (%%)', data: %s,
                      backgroundColor: '#ef4444' },
                    { label: 'Annual share (%%)', data: %s,
                      backgroundColor: '#3b82f6' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { tooltip: { callbacks: { afterBody: function (c) {
                    return 'Week of ' + %s[c[0].dataIndex]; } } } },
                scales: { x: { min: 0, max: 100,
                               title: { display: true, text: '%% renewable of generation' } } }
            }
        });''' % (js([x["country"] for x in DUNS]),
                  js([f(x["week_renewable_pct"]) for x in DUNS]),
                  js([f(x["annual_renewable_pct"]) for x in DUNS]),
                  js([x["week_from"][:10] for x in DUNS])),

              '''        // 04 how often each market went below zero. Italy's zero is a rule, not a
        //    quiet grid, which is why it is coloured differently.
        new Chart(document.getElementById('negChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Intervals below zero', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of intervals'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Negative day-ahead intervals, %d' } } }
            }
        });''' % (js([x["country"] for x in PXS]),
                  js([int(x["negative_intervals"]) for x in PXS]),
                  js(["#94a3b8" if int(x["negative_intervals"]) == 0 else "#ef4444"
                      for x in PXS]),
                  js([f(x["negative_pct"]) for x in PXS]), F["year"]),

              '''        // 05 mean price against the floor each market actually reached. The floors are
        //    not the same number anywhere, which is the point of the section.
        new Chart(document.getElementById('priceChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Mean price (EUR/MWh)', data: %s,
                      backgroundColor: '#3b82f6' },
                    { label: 'Minimum reached (EUR/MWh)', data: %s,
                      backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { title: { display: true, text: 'EUR per MWh' } } }
            }
        });''' % (js([x["country"] for x in sorted(PXS, key=lambda z: -f(z["mean_price"]))]),
                  js([f(x["mean_price"]) for x in sorted(PXS, key=lambda z: -f(z["mean_price"]))]),
                  js([f(x["min_price"]) for x in sorted(PXS, key=lambda z: -f(z["mean_price"]))])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "An Annual Renewable Share Hides Both Its Tails",
        "Hourly generation for %d European grids across %d: Austria's worst hour "
        "(%s%%) is %sx the Dutch annual average, Germany's published %s%% spans %s "
        "points of hourly variation, and %s markets paid people to generate."
        % (F["n"], F["year"], F["topmin"], F["ratio"], F["deann"], F["despread"],
           F["negn"]),
        "One grid's worst hour of the year is %sx another's annual average. And %s "
        "intervals cleared below zero." % (F["ratio"], format(F["negtot"], ",")),
        "An Annual Renewable Share Hides Both Its Tails")
    p.faq({
        "What was Germany's renewable electricity share in 2025?":
            "%s%% of generation, energy-weighted across the year. That single figure "
            "sits on a distribution: ninety per cent of Germany's hours fell between "
            "%s%% and %s%% renewable, a %s-point spread, with a worst hour of %s%% "
            "and a best of %s%%. It spent %s hours -- %s%% of the year -- at or above "
            "80%% renewable, and it also contains a January week that ran %s%%."
            % (F["deann"], F["dep5"], F["dep95"], F["despread"], F["demin"],
               F["demax"], format(F["de80"], ","), F["de80pct"], F["dedun"]),
        "Which European country has the highest renewable electricity share?":
            "Of the eight analysed here, %s at %s%% of generation for %d. The more "
            "revealing comparison is that %s's worst single hour of the entire year "
            "was %s%% renewable, which is %s times the %s' average for the whole year "
            "(%s%%). Note these are shares of domestic generation, not of "
            "consumption: imports are excluded, so an importing country looks less "
            "renewable than what it actually uses."
            % (F["topc"], F["topann"], F["year"], F["topc"], F["topmin"], F["ratio"],
               F["botc"], F["botann"]),
        "What is a Dunkelflaute and does interconnection solve it?":
            "A stretch of still, overcast weather when neither wind nor solar "
            "produces much. This data suggests interconnection helps less than hoped, "
            "because the event is continental rather than national: %d of the %d "
            "countries had their worst renewable week of %d begin in January, and the "
            "Dutch, Belgian, German and Austrian windows overlap. The %s week ran "
            "%s%% renewable against %s%% for the year, with %s%% fossil filling it. "
            "France is the exception at %s%% fossil, because %s%% of its worst week "
            "was nuclear."
            % (F["dunjan"], F["n"], F["year"], F["dunc"], F["dunpct"], F["dunann"],
               F["dunfos"], F["frdunfos"], F["frdunnuc"]),
        "Why are European electricity prices sometimes negative?":
            "Because there is more must-run generation than demand and something has "
            "to give, so a generator pays to deliver rather than shut down. In %d it "
            "happened in %d of these %d zones across %s intervals: %s most often at "
            "%s%% of intervals, and %s deepest at %s EUR/MWh. Prices are day-ahead "
            "auction results, so these are settled prices rather than model outputs."
            % (F["year"], F["negn"], F["n"], format(F["negtot"], ","), F["negc"],
               F["negpct"], F["deepc"], F["deep"]),
        "Why did Italy never have a negative electricity price?":
            "Because its market floor is zero, not because its grid is different. "
            "Italy's minimum day-ahead price across the whole of %d was exactly %s "
            "EUR/MWh -- an exact zero is a rule rather than a coincidence -- and its "
            "mean was the highest of the eight zones at %s. Spain shows the same "
            "thing from the other side: its minimum was exactly %s EUR/MWh across "
            "%d negative intervals, a different floor again. How far a price is "
            "allowed to fall is market design, not physics."
            % (F["year"], F["zeromin"], F["hiv"], F["esmin"], F["esneg"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
