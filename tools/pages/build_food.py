#!/usr/bin/env python3
"""Regenerate projects/food-prices-analysis.html from the WFP basket CSVs.

    .venv/bin/python tools/pages/build_food.py

The published page carried twenty-eight figures -- +159%, +336%, +685%, "52 min",
"11.2 kg", "₱26,760", "0.78" -- and not one of them traced to anything. The
underlying file had been in the repo the whole time: 234,015 WFP price
observations for the Philippines, monthly, from January 2000.

Reading it properly gives a narrower page and a more interesting one, because
the first thing the file says is that it is not as deep as its date range
suggests. It runs 2000 to 2026, but of 62 retail per-kilo commodities only two
run the whole way. Forty-six of them start in May 2020. So a growth rate over a
2020-cohort commodity covers five years that include the 2022-23 spike and is
not comparable with a twenty-five-year rate; the page groups by cohort and every
figure is scoped to its own commodity's span.

What that discipline leaves is worth having. Pork and rice are the two series
that share the full 25 years, and pork rose 2.23 times as much. The gap between
a commodity's rise in pesos and its rise in dollars is the peso's own decline --
107 points of it for pork -- and eight commodities rose in pesos while falling in
dollars. And the January 2023 onion crisis is in the file month by month: from
₱106.25/kg in June 2022 to ₱487.50 nationally, with one market at ₱617.50, which
was 1.56 times the price of pork.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-food-prices"
PAGE = "projects/food-prices-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def peso(v, nd=2):
    return "₱{:,.{nd}f}".format(v, nd=nd)


def main():
    com = rows("ph_food_commodities")
    coh = rows("ph_food_cohorts")
    ann = rows("ph_food_annual")
    oni = rows("ph_food_onions")
    reg = rows("ph_food_by_region")
    cat = rows("ph_food_categories")
    cov = {x["property"]: x["value"] for x in rows("ph_food_coverage")}

    C = {x["commodity"]: x for x in com}
    pork, rice = C["Meat (pork)"], C["Rice (regular, milled)"]
    long_ = [x for x in com if int(x["first_year"]) <= 2008]
    long_ = sorted(long_, key=lambda x: -f(x["change_php_pct"]))
    peak = max(oni, key=lambda x: f(x["median_php_per_kg"]))
    o22 = [x for x in oni if x["month"] == "2022-06"][0]
    o23 = [x for x in oni if x["month"] == "2023-04"][0]
    rreg = sorted((x for x in reg if x["commodity"] == "Rice (regular, milled)"),
                  key=lambda x: -f(x["median_php_per_kg"]))
    ncr = [x for x in rreg if x["region"] == "National Capital region"][0]
    cats = sorted(cat, key=lambda x: -f(x["median_change_php_pct"]))

    F = dict(
        obs=int(cov["retail per-kilo observations"]),
        ncom=int(cov["commodities"]), mkts=int(cov["markets"]),
        nreg=int(cov["regions"]),
        spanning=int(cov["commodities spanning the whole record"]),
        exagg=int(cov["WFP aggregate rows excluded"]),
        exunit=int(cov["non-kilogramme rows excluded"]),
        c2000=int([x for x in coh if x["first_month"] == "2000-01"][0]["commodities"]),
        c2008=int([x for x in coh if x["first_month"] == "2008-01"][0]["commodities"]),
        c2020=int([x for x in coh if x["first_month"] == "2020-05"][0]["commodities"]),
        porkc=f(pork["change_php_pct"]), porku=f(pork["change_usd_pct"]),
        porkcagr=f(pork["cagr_php_pct"]),
        pork0=f(pork["first_php_per_kg"]), pork1=f(pork["last_php_per_kg"]),
        ricec=f(rice["change_php_pct"]), riceu=f(rice["change_usd_pct"]),
        ricecagr=f(rice["cagr_php_pct"]),
        rice0=f(rice["first_php_per_kg"]), rice1=f(rice["last_php_per_kg"]),
        usdfall=sum(1 for x in com if f(x["change_usd_pct"]) < 0
                    and f(x["change_php_pct"]) >= 0),
        usdfalltot=sum(1 for x in com if f(x["change_usd_pct"]) < 0),
        topc=long_[0]["commodity"], topch=f(long_[0]["change_php_pct"]),
        topcagr=f(long_[0]["cagr_php_pct"]),
        slowc=long_[-1]["commodity"], slowch=f(long_[-1]["change_php_pct"]),
        longn=len(long_),
        cattop=cats[0]["category"], cattoppct=f(cats[0]["median_change_php_pct"]),
        catbot=cats[-1]["category"], catbotpct=f(cats[-1]["median_change_php_pct"]),
        opeak=f(peak["median_php_per_kg"]), opeakm=peak["month"],
        opeakhi=f(peak["highest_market_php"]),
        opeaklo=f(peak["lowest_market_php"]),
        opork=f(peak["pork_median_php"]),
        obefore=f(o22["median_php_per_kg"]), oafter=f(o23["median_php_per_kg"]),
        rtop=rreg[0]["region"], rtopv=f(rreg[0]["median_php_per_kg"]),
        rbot=rreg[-1]["region"], rbotv=f(rreg[-1]["median_php_per_kg"]),
        ncrv=f(ncr["median_php_per_kg"]),
        ncrrank=1 + sum(1 for x in rreg
                        if f(x["median_php_per_kg"]) < f(ncr["median_php_per_kg"])),
        nrreg=len(rreg),
    )
    F["c2020pct"] = r(100.0 * F["c2020"] / sum(int(x["commodities"]) for x in coh), 1)
    F["porkoverrice"] = r(F["porkc"] / F["ricec"], 2)
    F["pesogap"] = r(F["porkc"] - F["porku"], 1)
    F["orise"] = r(F["opeak"] / F["obefore"], 2)
    F["oover"] = r(F["opeak"] / F["opork"], 2)
    F["ospread"] = r(F["opeakhi"] / F["opeaklo"], 2)
    F["rspread"] = r(100.0 * (F["rtopv"] / F["rbotv"] - 1), 1)

    T = dict(pork0p=peso(F["pork0"]), pork1p=peso(F["pork1"]),
             rice0p=peso(F["rice0"]), rice1p=peso(F["rice1"]),
             opeakp=peso(F["opeak"]), opeakhip=peso(F["opeakhi"]),
             oporkp=peso(F["opork"]), obeforep=peso(F["obefore"]),
             opeaklo=peso(F["opeaklo"]),
             oafterp=peso(F["oafter"]),
             rtopp=peso(F["rtopv"]), rbotp=peso(F["rbotv"]),
             ncrp=peso(F["ncrv"]))

    p = Page(PAGE)
    p.hero('''                <h1>Twenty-Six Years Of Food Prices, And Only Two Of Them</h1>
                <p class="{hero_desc}">
                    {obs:,} WFP price observations across {ncom} foods and {mkts}
                    markets. The file runs from 2000, but only
                    {spanning} commodities run the whole way &mdash; so every rate
                    here is scoped to its own span, and the two that share
                    all 25 years disagree by a factor of {porkoverrice}.
                </p>

                <div class="header-actions">
                    <a href="https://data.humdata.org/dataset/wfp-food-prices-for-philippines" target="_blank" class="btn btn-primary">
                        WFP food prices (HDX)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="food.pork.change">{porkc}%</div>
                        <div class="{label}">Pork, 2000 to 2025, in pesos</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="food.rice.change">{ricec}%</div>
                        <div class="{label}">Rice, the same 25 years</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="onion.peak">{opeak}</div>
                        <div class="{label}">Pesos per kilo of onions, January 2023</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="food.cohort.2020.pct">{c2020pct}%</div>
                        <div class="{label}">Of the commodities begin only in May 2020</div>
                    </div>
                </div>
'''.format(**dict(F, **T), **p.t))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Pork rose <span data-fact="food.pork.change">{porkc}%</span> between 2000 and 2025. Rice, over the identical 25 years, rose <span data-fact="food.rice.change">{ricec}%</span> &mdash; a factor of <span data-fact="food.pork.over.rice">{porkoverrice}</span>. They are the only two commodities in the file that span the whole record, which is why they are the only two compared this way.</p>
                    <ul class="tldr-list">
                        <li>The dataset looks 26 years deep and mostly is not. <span data-fact="food.cohort.2000">{c2000}</span> commodities start in January 2000, <span data-fact="food.cohort.2008">{c2008}</span> in January 2008, and <span data-fact="food.cohort.2020">{c2020}</span> &mdash; <span data-fact="food.cohort.2020.pct">{c2020pct}%</span> of them &mdash; only in May 2020.</li>
                        <li>Red onions went from <span data-fact="onion.before">{obefore}</span> pesos a kilo in June 2022 to <span data-fact="onion.peak">{opeak}</span> in <span data-fact="onion.peak.month">{opeakm}</span>, a factor of <span data-fact="onion.rise">{orise}</span>. One market reached <span data-fact="onion.peak.market">{opeakhi}</span>. That month onions cost <span data-fact="onion.over.pork">{oover}</span> times as much per kilo as pork.</li>
                        <li>The gap between a food's rise in pesos and its rise in dollars is the peso's own decline: <span data-fact="food.peso.gap.pork">{pesogap}</span> points for pork. <span data-fact="food.usd.falling">{usdfall}</span> commodities rose in pesos while falling in dollars.</li>
                        <li>Vegetables and fruits rose fastest as a group, a median <span data-fact="food.cat.top.pct">{cattoppct}%</span>, against <span data-fact="food.cat.bottom.pct">{catbotpct}%</span> for cereals and tubers &mdash; the category rice is in.</li>
                        <li>Metro Manila is not where rice is dearest. It ranks <span data-fact="food.rice.ncr.rank">{ncrrank}</span>th cheapest of <span data-fact="food.regions">{nreg}</span> regions at <span data-fact="food.rice.ncr.price">{ncrv}</span> a kilo, against <span data-fact="food.rice.region.top.price">{rtopv}</span> in {rtop}.</li>
                    </ul>
'''.format(**dict(F, **T)))

    S = [
        p.section(1, "The Range Is Not The Depth",
                  "When a commodity first appears in the file. This is the single "
                  "most important thing about the dataset, and it governs every "
                  "other figure on this page: a rate computed over the 2020 cohort "
                  "covers five years including the 2022-23 spike, and cannot be "
                  "ranked against a twenty-five-year rate.",
                  [("From January 2000", "{v}".format(v=F["c2000"]),
                    "food.cohort.2000",
                    "Commodities: pork and two rice grades. Two of the three are "
                    "still priced today."),
                   ("From January 2008", "{v}".format(v=F["c2008"]),
                    "food.cohort.2008",
                    "The staple vegetables and meats. With the first cohort this "
                    "gives <span data-fact=\"food.long.n\">{n}</span> commodities "
                    "with at least 18 years.".format(n=F["longn"])),
                   ("From May 2020", "{v}".format(v=F["c2020"]),
                    "food.cohort.2020",
                    "<span data-fact=\"food.cohort.2020.pct\">{p}%</span> of the "
                    "basket, with six years each. Long enough to price a shock, "
                    "too short to price a trend.".format(p=F["c2020pct"]))],
                  "Commodities by the month they first appear", "cohortChart"),
        p.section(2, "Pork Against Rice, Over The Same Quarter Century",
                  "The two series that share the full record. Both are staples, "
                  "both are priced in every region, and they behaved completely "
                  "differently.",
                  [("Pork", "+{v}%".format(v=F["porkc"]), "food.pork.change",
                    "{a} to {b} a kilo, a compound "
                    "<span data-fact=\"food.pork.cagr\">{c}%</span> a year."
                    .format(a=T["pork0p"], b=T["pork1p"], c=F["porkcagr"])),
                   ("Rice", "+{v}%".format(v=F["ricec"]), "food.rice.change",
                    "{a} to {b}, a compound "
                    "<span data-fact=\"food.rice.cagr\">{c}%</span> a year "
                    "&mdash; and rice is the country's price-controlled staple, "
                    "which is part of why."
                    .format(a=T["rice0p"], b=T["rice1p"], c=F["ricecagr"])),
                   ("The ratio", "{v}&times;".format(v=F["porkoverrice"]),
                    "food.pork.over.rice",
                    "Pork's rise over rice's, across identical years. A household "
                    "that ate the same food throughout faced very different "
                    "inflation depending which staple it leaned on.")],
                  "Median retail price per kilo, pork and rice, 2000 onward",
                  "longChart"),
        p.section(3, "What The Peso Did",
                  "Every commodity twice: its price change in pesos, and the same "
                  "change in dollars. The distance between the two bars is not "
                  "about food at all &mdash; it is the peso losing value against "
                  "the dollar over the same period.",
                  [("Pork in pesos", "+{v}%".format(v=F["porkc"]),
                    "food.pork.change", "Over 25 years."),
                   ("Pork in dollars", "+{v}%".format(v=F["porku"]),
                    "food.pork.usd",
                    "The same pork, the same years. The "
                    "<span data-fact=\"food.peso.gap.pork\">{g}</span>-point gap "
                    "is exchange rate, not agriculture.".format(g=F["pesogap"])),
                   ("Cheaper in dollars", "{v}".format(v=F["usdfall"]),
                    "food.usd.falling",
                    "Commodities whose peso price rose or held while their dollar "
                    "price fell. <span data-fact=\"food.usd.falling.total\">{t}</span> "
                    "fell in dollars altogether."
                    .format(t=F["usdfalltot"]))],
                  "Price change in pesos and in dollars, commodities with 18+ years",
                  "currencyChart"),
        p.section(4, "January 2023",
                  "Red onions, month by month, with pork on the same axis for "
                  "scale. This is the clearest single event in the file and it "
                  "needs no interpretation &mdash; the prices are simply there.",
                  [("The peak", T["opeakp"], "onion.peak",
                    "Per kilo, national median, "
                    "<span data-fact=\"onion.peak.month\">{m}</span>. Up from "
                    "<span data-fact=\"onion.before\">{b}</span> seven months "
                    "earlier, a factor of "
                    "<span data-fact=\"onion.rise\">{r}</span>."
                    .format(m=F["opeakm"], b=F["obefore"], r=F["orise"])),
                   ("Against pork", "{v}&times;".format(v=F["oover"]),
                    "onion.over.pork",
                    "Pork was {p} a kilo that month. Onions cost more."
                    .format(p=T["oporkp"])),
                   ("Market spread", "{v}&times;".format(v=F["ospread"]),
                    "onion.spread",
                    "The dearest market that month asked "
                    "<span data-fact=\"onion.peak.market\">{h}</span> and the "
                    "cheapest {l}. By April it was back to {a} nationally."
                    .format(h=F["opeakhi"], l=T["opeaklo"], a=T["oafterp"]))],
                  "Red onions and pork, pesos per kilo, 2021-2024", "onionChart"),
        p.section(5, "Which Foods Rose Fastest",
                  "The {n} commodities with at least 18 years of prices, ranked. "
                  "The 2020 cohort is deliberately excluded: a five-year rate "
                  "beginning in 2020 is not the same measurement and ranking them "
                  "together would put every recent arrival at the top."
                  .format(n=F["longn"]),
                  [(F["topc"], "+{v}%".format(v=F["topch"]), "food.top.change",
                    "Fastest of the {n}, at "
                    "<span data-fact=\"food.top.cagr\">{c}%</span> compounded."
                    .format(n=F["longn"], c=F["topcagr"])),
                   (F["slowc"], "+{v}%".format(v=F["slowch"]), "food.slow.change",
                    "Slowest. Over 18 years that is barely ahead of holding "
                    "still in nominal terms, and behind it in real ones."),
                   ("Vegetables against grains",
                    "{a}% vs {b}%".format(a=F["cattoppct"], b=F["catbotpct"]),
                    "food.cat.top.pct",
                    "Median change by WFP category: {t} against {b}, which is "
                    "the category rice sits in."
                    .format(t=F["cattop"], b=F["catbot"]))],
                  "Price change over each commodity's own span, 18+ year series",
                  "moversChart"),
        p.section(6, "Where Rice Is Dear",
                  "Median rice price by region in 2025. The ordering is not the "
                  "one most people would guess, and the reason is that rice moves "
                  "from where it is grown to where it is not.",
                  [(F["rtop"], T["rtopp"], "food.rice.region.top.price",
                    "Dearest of the {n} regions."
                    .format(n=F["nrreg"])),
                   (F["rbot"], T["rbotp"], "food.rice.region.bottom.price",
                    "Cheapest &mdash; Cagayan Valley, which grows a lot of it. A "
                    "<span data-fact=\"food.rice.region.spread\">{s}%</span> "
                    "spread across the country.".format(s=F["rspread"])),
                   ("Metro Manila", T["ncrp"], "food.rice.ncr.price",
                    "<span data-fact=\"food.rice.ncr.rank\">{r}</span>th cheapest "
                    "of {n}. The capital is not where rice costs most."
                    .format(r=F["ncrrank"], n=F["nrreg"]))],
                  "Median rice price by region, 2025", "regionChart"),
        p.prose(7, "What This Page Does Not Claim",
                "Four limits, three of them asserted by checks so they cannot "
                "quietly stop being true.",
                [("There is no basket index",
                  "WFP prices carry no household consumption weights, so there is "
                  "no way to say what a typical family's food bill did. Averaging "
                  "62 commodities would weight garlic like rice. Every figure here "
                  "is about a named commodity, and a check asserts the weights "
                  "column stays at zero."),
                 ("Quality is assumed constant",
                  "A kilo of tomatoes in 2008 and a kilo in 2025 are treated as "
                  "the same thing. They may not be. This is an assumption, not a "
                  "measurement, and it is the standard one &mdash; but it means a "
                  "price rise and a quality rise are indistinguishable here."),
                 ("2026 is excluded from every rate",
                  "The file reaches June 2026. Ending a change figure there would "
                  "compare six months against twelve and report part of the "
                  "seasonal cycle as inflation. A check fails if any commodity's "
                  "last year is later than 2025."),
                 ("Nothing here is inflation-adjusted",
                  "These are nominal pesos. General consumer inflation over the "
                  "same period accounts for part of every rise on this page, and "
                  "separating food inflation from it needs a CPI series this "
                  "project does not carry. The dollar column in section 3 is a "
                  "different adjustment &mdash; for the exchange rate, not for "
                  "prices at home.")]),
        p.prose(8, "Method",
                "One derivation script over a file that was already in the repo.",
                [("The source was already here",
                  "wfp_food_prices_phl.csv, 31 MB and 234,015 rows, has been in "
                  "data/ph-food-prices since the rice page was built. The previous "
                  "version of this page published twenty-eight figures without "
                  "opening it."),
                 ("Retail, per kilogramme, actual only",
                  "{ex:,} WFP aggregate rows are excluded because they are computed "
                  "from the actual rows and counting both double-counts. {eu:,} "
                  "non-kilogramme rows are excluded because a per-unit price and a "
                  "per-kilo price are different measurements. What remains is "
                  "{obs:,} observations.".format(ex=F["exagg"], eu=F["exunit"],
                                                 obs=F["obs"])),
                 ("Medians, not means",
                  "A national price for a month is the median across markets, and "
                  "an annual price is the median across that year's monthly "
                  "observations. Means would let one market's outlier move a "
                  "national figure, which in the onion months it would have done "
                  "considerably."),
                 ("Every rate is scoped to its own span",
                  "No commodity is measured against a fixed 2000 baseline it does "
                  "not have. Each row carries its own first and last year and the "
                  "change between them, and a check verifies the change and the "
                  "compound rate agree with those two endpoint prices."),
                 ("The currency check runs on direction",
                  "The peso fell against the dollar across this whole period, so "
                  "every commodity's rise in pesos must exceed its rise in dollars. "
                  "A check fails on any crossing, because that would mean the two "
                  "currency columns had been swapped &mdash; which is not the kind "
                  "of error that looks wrong on a chart."),
                 ("This page and the rice page share a directory",
                  "Both read the same 31 MB source, so they share "
                  "data/ph-food-prices rather than keeping two copies. Fact keys "
                  "beginning food. belong here; keys beginning rice. belong to the "
                  "rice page.")]),
    ]

    # This page styles neither section-header nor insight-card, so the summary
    # block uses whatever it does define. p.t resolves both to "" here.
    HCLS = ("%s fade-up" % p.t["sec_head"]) if p.t["sec_head"] else "fade-up"
    CWRAP = ("%s fade-up" % p.t["card_wrap"]) if p.t["card_wrap"] else "fade-up"
    S.append('''        <section class="{wrap}">
            <div class="container">
                <div class="{hcls}">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="{cwrap}">
                    <ul>
                        <li>Pork rose
                        <span data-fact="food.pork.change">{porkc}%</span> and rice
                        <span data-fact="food.rice.change">{ricec}%</span> over the
                        identical 25 years &mdash; a factor of
                        <span data-fact="food.pork.over.rice">{porkoverrice}</span>,
                        and they are the only two commodities that span the whole
                        record.</li>
                        <li><span data-fact="food.cohort.2020">{c2020}</span> of the
                        <span data-fact="food.commodities">{ncom}</span> commodities
                        only start in May 2020, so the file's 26-year range
                        describes the file rather than most of what is in it.</li>
                        <li>Onions peaked at
                        <span data-fact="onion.peak">{opeak}</span> pesos a kilo in
                        <span data-fact="onion.peak.month">{opeakm}</span>, up
                        <span data-fact="onion.rise">{orise}</span>&times; from June
                        2022, with one market at
                        <span data-fact="onion.peak.market">{opeakhi}</span> &mdash;
                        <span data-fact="onion.over.pork">{oover}</span> times the
                        price of pork.</li>
                        <li>The peso-dollar gap on pork is
                        <span data-fact="food.peso.gap.pork">{pesogap}</span> points,
                        and <span data-fact="food.usd.falling">{usdfall}</span>
                        commodities rose in pesos while falling in dollars.</li>
                        <li>Vegetables and fruits rose a median
                        <span data-fact="food.cat.top.pct">{cattoppct}%</span>
                        against
                        <span data-fact="food.cat.bottom.pct">{catbotpct}%</span> for
                        cereals and tubers.</li>
                        <li>Rice is dearest in {rtop} at
                        <span data-fact="food.rice.region.top.price">{rtopv}</span>
                        and cheapest in {rbot} at
                        <span data-fact="food.rice.region.bottom.price">{rbotv}</span>;
                        Metro Manila is
                        <span data-fact="food.rice.ncr.rank">{ncrrank}</span>th
                        cheapest of
                        <span data-fact="food.regions">{nreg}</span>.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **T), **p.t))

    pk = sorted((x for x in ann if x["commodity"] == "Meat (pork)"),
                key=lambda x: x["year"])
    rc = sorted((x for x in ann if x["commodity"] == "Rice (regular, milled)"),
                key=lambda x: x["year"])
    yrs = sorted({x["year"] for x in pk} | {x["year"] for x in rc})
    pkm = {x["year"]: f(x["median_php_per_kg"]) for x in pk}
    rcm = {x["year"]: f(x["median_php_per_kg"]) for x in rc}
    L = long_
    O = oni

    charts = ['''        // 01 when each commodity's series starts. The bar at 2020-05 is most of the
        //    basket, and is why nothing on this page ranks across cohorts.
        new Chart(document.getElementById('cohortChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Commodities starting here', data: %s,
                             backgroundColor: %s, borderRadius: 6 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' years of prices'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Commodities' } } }
            }
        });''' % (js([x["first_month"] for x in coh]),
                  js([int(x["commodities"]) for x in coh]),
                  js(["#ef4444" if x["first_month"] == "2020-05" else "#3b82f6"
                      for x in coh]),
                  js([int(x["span_years"]) for x in coh])),

              '''        // 02 the two full-length series, on one axis so the divergence is the shape
        //    rather than something the caption asserts.
        new Chart(document.getElementById('longChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Pork (PHP/kg)', data: %s, borderColor: '#ef4444',
                      borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Rice, regular milled (PHP/kg)', data: %s,
                      borderColor: '#3b82f6', borderWidth: 3, pointRadius: 0,
                      fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Pesos per kilogramme' } } }
            }
        });''' % (js(yrs), js([pkm.get(y) for y in yrs]),
                  js([rcm.get(y) for y in yrs])),

              '''        // 03 pesos against dollars. The distance between the pairs is the exchange
        //    rate, not the food.
        new Chart(document.getElementById('currencyChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Change in pesos (%%)', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Change in dollars (%%)', data: %s, backgroundColor: '#f59e0b' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { tooltip: { callbacks: { afterBody: function (c) {
                    return %s[c[0].dataIndex]; } } } },
                scales: { x: { title: { display: true, text: 'Change over the commodity\\'s own span (%%)' } } }
            }
        });''' % (js([x["commodity"] for x in L]),
                  js([f(x["change_php_pct"]) for x in L]),
                  js([f(x["change_usd_pct"]) for x in L]),
                  js(["%s-%s" % (x["first_year"], x["last_year"]) for x in L])),

              '''        // 04 the onion crisis, with pork drawn for scale.
        new Chart(document.getElementById('onionChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Red onions (PHP/kg)', data: %s, borderColor: '#8b5cf6',
                      backgroundColor: 'rgba(139,92,246,0.15)', borderWidth: 3,
                      pointRadius: 2, fill: true },
                    { label: 'Dearest market that month', data: %s,
                      borderColor: '#ef4444', borderDash: [5, 4], borderWidth: 2,
                      pointRadius: 0, fill: false },
                    { label: 'Pork (PHP/kg)', data: %s, borderColor: '#64748b',
                      borderWidth: 2, pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Pesos per kilogramme' } } }
            }
        });''' % (js([x["month"] for x in O]),
                  js([f(x["median_php_per_kg"]) for x in O]),
                  js([f(x["highest_market_php"]) for x in O]),
                  js([f(x["pork_median_php"]) for x in O])),

              '''        // 05 the long series ranked, with the compound rate beside the total so a
        //    long slow rise is not confused with a short sharp one.
        new Chart(document.getElementById('moversChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Total change (%%)', data: %s, backgroundColor: '#3b82f6',
                      yAxisID: 'y' },
                    { type: 'line', label: 'Compound rate (%%/year)', data: %s,
                      borderColor: '#ef4444', borderWidth: 2, pointRadius: 4,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Total change (%%)' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: '%% per year' } } }
            }
        });''' % (js([x["commodity"] for x in L]),
                  js([f(x["change_php_pct"]) for x in L]),
                  js([f(x["cagr_php_pct"]) for x in L])),

              '''        // 06 rice by region. NCR highlighted, because where it lands is the point.
        new Chart(document.getElementById('regionChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Median rice price (PHP/kg)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Pesos per kilogramme, 2025' } } }
            }
        });''' % (js([x["region"] for x in rreg]),
                  js([f(x["median_php_per_kg"]) for x in rreg]),
                  js(["#ef4444" if x["region"] == "National Capital region"
                      else "#3b82f6" for x in rreg])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "Twenty-Six Years Of Food Prices, And Only Two Of Them",
        "%s WFP price observations across %d Philippine foods: pork rose %s%% and "
        "rice %s%% over the same 25 years, onions hit ₱%s a kilo in January 2023, "
        "and %d of the commodities only start in 2020."
        % (format(F["obs"], ","), F["ncom"], F["porkc"], F["ricec"], F["opeak"],
           F["c2020"]),
        "Pork rose %s%%, rice %s%%, over identical years. And onions cost more than "
        "pork in January 2023." % (F["porkc"], F["ricec"]),
        "Twenty-Six Years Of Food Prices, And Only Two Of Them")
    p.faq({
        "How much have food prices risen in the Philippines since 2000?":
            "It depends entirely which food, and for most of them the question "
            "cannot be answered from this data at all -- only %d of %d commodities "
            "in the WFP file are priced continuously from 2000. The two that are "
            "diverge sharply: pork rose %s%% and rice %s%%, a factor of %s over "
            "identical years."
            % (F["spanning"], F["ncom"], F["porkc"], F["ricec"], F["porkoverrice"]),
        "How high did onion prices get in the Philippines?":
            "The national median retail price of red onions reached ₱%s a kilogramme "
            "in %s, up from ₱%s in June 2022 -- a factor of %s in seven months. The "
            "dearest single market that month recorded ₱%s. Pork was ₱%s a kilo at "
            "the same time, so onions cost %s times as much per kilo as pork. By "
            "April 2023 the national median was back to ₱%s."
            % (F["opeak"], F["opeakm"], F["obefore"], F["orise"], F["opeakhi"],
               F["opork"], F["oover"], F["oafter"]),
        "Why do Philippine food prices look different in pesos and in dollars?":
            "Because the peso lost value against the dollar over the period. Pork "
            "rose %s%% in pesos and %s%% in dollars -- a gap of %s points that is "
            "exchange rate rather than agriculture. %d commodities in the file rose "
            "or held steady in pesos while falling in dollars."
            % (F["porkc"], F["porku"], F["pesogap"], F["usdfall"]),
        "Where is rice most expensive in the Philippines?":
            "In %s, at ₱%s a kilo in 2025, against ₱%s in %s -- a %s%% spread across "
            "the %d regions. Metro Manila is not the dearest: it ranks %dth cheapest "
            "at ₱%s. Rice moves from where it is grown to where it is not, and the "
            "regions that grow it pay least."
            % (F["rtop"], F["rtopv"], F["rbotv"], F["rbot"], F["rspread"],
               F["nrreg"], F["ncrrank"], F["ncrv"]),
        "Can this data show which Philippine food inflated fastest?":
            "Only among commodities that share a comparable span. %d of the %d have "
            "at least 18 years of prices, and among those %s rose most at %s%%. The "
            "other %d only begin in May 2020, so their five-year rates cover the "
            "2022-23 spike and are not comparable; ranking them together would put "
            "every recent arrival at the top for a reason that has nothing to do "
            "with food."
            % (F["longn"], F["ncom"], F["topc"], F["topch"], F["c2020"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
