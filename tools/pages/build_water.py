#!/usr/bin/env python3
"""Regenerate projects/global-water-analysis.html from data/global-water CSVs.

    .venv/bin/python tools/pages/build_water.py

The WHO/UNICEF Joint Monitoring Programme publishes a service ladder for drinking
water, and two of its rungs get quoted as if they were one number:

  at least basic   an improved source within a 30-minute round trip
  safely managed   improved, ON the premises, available when needed, and free
                   from contamination -- and this is SDG indicator 6.1.1

The first finding is that the strict rung does not exist for a quarter of the
world. 62 of the 209 countries with a basic figure have no safely-managed figure
at all: 2.21 billion people, 27.31% of the population those estimates cover.
China alone is 1.4 billion of it. Sixteen of the 62 are high-income countries --
Australia and Saudi Arabia among them -- so this is not a story about poor
countries lacking survey capacity.

The second is that where both rungs exist they are nowhere near each other. The
median distance is 18.4 points across 147 reporting countries and 38 of them are
40 points or more apart. Nepal is 93.64% basic and 16.49% safely managed. The
Philippines is 95.86% and 48.48%.

The third is arithmetic. The world went from 61.26% safely managed in 2000 to
73.74% in 2024 -- 0.52 points a year. Held at that rate, universal coverage
arrives in 2075, forty-five years after the 2030 target, and 30 of the 145
countries with both readings were lower in 2022 than in 2015.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-water"
PAGE = "projects/global-water-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def i(v):
    return int(float(v)) if v not in (None, "", "None") else None


def main():
    cty = rows("gw_country")
    world = rows("gw_world")
    cov = {x["property"]: x["value"] for x in rows("gw_coverage")}
    ser = rows("gw_series")

    for x in cty:
        for k in ("water_basic_pct", "water_safely_managed_pct",
                  "basic_minus_safely_pts", "sanitation_basic_pct",
                  "sanitation_safely_managed_pct", "open_defecation_pct",
                  "handwashing_basic_pct", "water_safely_managed_urban_pct",
                  "water_safely_managed_rural_pct"):
            x[k] = f(x[k])
        x["population"] = i(x["population"]) or 0

    have_b = [x for x in cty if x["water_basic_pct"] is not None]
    have_s = [x for x in cty if x["water_safely_managed_pct"] is not None]
    miss = [x for x in have_b if x["water_safely_managed_pct"] is None]
    miss.sort(key=lambda x: -x["population"])
    gaps = [x for x in cty if x["basic_minus_safely_pts"] is not None]
    big = [x for x in gaps if x["population"] > 20000000]
    big.sort(key=lambda x: -x["basic_minus_safely_pts"])
    C = {x["iso3"]: x for x in cty}

    def W(ind, year, res="total", scope="GLOBAL"):
        for x in world:
            if (x["scope"] == scope and x["indicator"] == ind
                    and int(x["year"]) == year and x["residence"] == res):
                return f(x["pct"])
        return None

    wyears = sorted({int(x["year"]) for x in world
                     if x["scope"] == "GLOBAL" and x["residence"] == "total"
                     and x["indicator"] == "water_safely_managed"})
    y0, y1 = wyears[0], wyears[-1]
    w0, w1 = W("water_safely_managed", y0), W("water_safely_managed", y1)
    rate = (w1 - w0) / (y1 - y0)
    arrive = round(y1 + (100 - w1) / rate)

    # countries lower in 2022 than in 2015, the year the SDGs were adopted
    sm = {}
    for x in ser:
        if x["indicator"] == "water_safely_managed" and x["residence"] == "total":
            sm.setdefault(x["iso3"], {})[int(x["year"])] = f(x["pct"])
    both = [k for k, v in sm.items() if 2015 in v and 2022 in v]
    back = [k for k in both if sm[k][2022] < sm[k][2015]]

    rr = [x for x in cty if x["water_safely_managed_rural_pct"] is not None
          and x["water_safely_managed_urban_pct"] is not None]
    rr_big = [x for x in rr if x["population"] > 20000000]
    rr_big.sort(key=lambda x: -(x["water_safely_managed_urban_pct"]
                                - x["water_safely_managed_rural_pct"]))
    rural_ahead = [x for x in cty
                   if x["water_safely_managed_rural_pct"] is not None
                   and x["water_safely_managed_urban_pct"] is not None
                   and x["water_safely_managed_rural_pct"]
                   > x["water_safely_managed_urban_pct"]]

    gapvals = sorted(x["basic_minus_safely_pts"] for x in gaps)
    n = len(gapvals)
    median_gap = r(gapvals[n // 2] if n % 2
                   else (gapvals[n // 2 - 1] + gapvals[n // 2]) / 2.0, 1)

    misspop = sum(x["population"] for x in miss)
    top = miss[0]
    gtop = big[0]
    rtop = rr_big[0]
    missan = [x for x in cty if x["sanitation_basic_pct"] is not None
              and x["sanitation_safely_managed_pct"] is None]

    F = dict(
        n=len(cty), y0=y0, y1=y1, rows=len(ser),
        checked=i(cov["cross-checked country-year-indicator pairs"]),
        worstdiff=f(cov["worst cross-check disagreement"]),
        onlygho=i(cov["pairs only in WHO GHO"]),
        onlywb=i(cov["pairs only in the World Bank"]),
        odpairs=i(cov["open defecation pairs checked against GHO's rounded copy"]),
        missn=len(miss), misspeople=r(misspop / 1e6),
        missbn=r(misspop / 1e9, 2), misspct=f(cov[
            "share of that population with no safely managed figure"]),
        haveb=len(have_b), haves=len(have_s),
        missrich=sum(1 for x in miss if x["income_group"] == "High income"),
        misstopc=top["country"], misstopp=r(top["population"] / 1e6),
        misstopb=top["water_basic_pct"],
        missan=len(missan),
        missanp=r(sum(x["population"] for x in missan) / 1e6),
        gapc=gtop["country"], gapb=gtop["water_basic_pct"],
        gaps_=gtop["water_safely_managed_pct"],
        gappts=gtop["basic_minus_safely_pts"],
        gapmed=median_gap, gap40=sum(1 for x in gaps
                                     if x["basic_minus_safely_pts"] >= 40),
        gapn=len(gaps),
        idb=C["IDN"]["water_basic_pct"], ids=C["IDN"]["water_safely_managed_pct"],
        idp=r(C["IDN"]["population"] / 1e6),
        phb=C["PHL"]["water_basic_pct"], phs=C["PHL"]["water_safely_managed_pct"],
        phg=C["PHL"]["basic_minus_safely_pts"],
        w0=r(w0, 2), w1=r(w1, 2), rate=r(rate, 2), arrive=arrive,
        late=arrive - 2030,
        backn=len(back), backof=len(both),
        wurb=r(W("water_safely_managed", 2022, "urban"), 2),
        wrur=r(W("water_safely_managed", 2022, "rural"), 2),
        wrrgap=r(W("water_safely_managed", 2022, "urban")
                 - W("water_safely_managed", 2022, "rural"), 2),
        rrn=len(rr), rrahead=len(rural_ahead),
        rrc=rtop["country"], rru=rtop["water_safely_managed_urban_pct"],
        rrr=rtop["water_safely_managed_rural_pct"],
        odw=r(W("open_defecation", max(int(x["year"]) for x in world
                                       if x["scope"] == "GLOBAL"
                                       and x["indicator"] == "open_defecation")), 2),
        od0=r(W("open_defecation", 2000), 2),
        hwmiss=sum(1 for x in cty if x["handwashing_basic_pct"] is None),
        hwhave=sum(1 for x in cty if x["handwashing_basic_pct"] is not None),
    )

    p = Page(PAGE)
    p.relocate(
        "global-grid-analysis",
        og_image="og-water.png",
        keywords=["safely managed drinking water", "SDG 6.1.1", "WASH",
                  "WHO UNICEF Joint Monitoring Programme", "sanitation ladder",
                  "open data", "data analysis"],
        dataset_name="Drinking water, sanitation and hygiene service ladders, "
                     "2000-2024",
        dataset_desc=("Population using at least basic and safely managed drinking "
                      "water and sanitation, by country and by urban/rural "
                      "residence, from the WHO/UNICEF Joint Monitoring Programme as "
                      "published by WHO GHO and the World Bank"),
        breadcrumb="The Water Number That Does Not Exist",
        crumb_tail="Global Water",
        creator="WHO/UNICEF Joint Monitoring Programme",
        dataset_url="https://ghoapi.azureedge.net/api/",
        tags=["\U0001f4a7 Water", "WHO GHO", "World Bank", "%d countries" % F["n"],
              "<span class=\"dot\"></span> %d–%d" % (F["y0"], F["y1"])],
        info=[("Data Sources",
               '<a href="https://ghoapi.azureedge.net/api/" target="_blank" '
               'rel="noopener">WHO Global Health Observatory</a> &middot; '
               '<a href="https://api.worldbank.org/v2/" target="_blank" '
               'rel="noopener">World Bank WDI</a> &middot; '
               '<a href="https://washdata.org/" target="_blank" '
               'rel="noopener">WHO/UNICEF JMP</a>'),
              ("Coverage",
               "%d countries &middot; %d&ndash;%d &middot; %s country-year-indicator "
               "readings" % (F["n"], F["y0"], F["y1"], format(F["rows"], ","))),
              ("Cross-check",
               "%s pairs read from both publishers, worst disagreement %s points"
               % (format(F["checked"], ","), F["worstdiff"])),
              ("Licence", "CC BY-NC-SA 3.0 IGO (WHO) &middot; CC BY 4.0 (World Bank)")])

    p.head(
        "A Quarter Of The World Has No Safe-Water Number At All",
        "%d of the %d countries with a basic drinking water figure have no safely "
        "managed figure at all — %s billion people, %s%% of the population "
        "those estimates cover. Where both rungs of the WHO/UNICEF ladder exist "
        "they sit a median %s points apart."
        % (F["missn"], F["haveb"], F["missbn"], F["misspct"], F["gapmed"]),
        "%s billion people live in a country with no safely managed drinking water "
        "estimate. SDG 6.1.1 is that estimate." % F["missbn"],
        "A Quarter Of The World Has No Safe-Water Number At All")

    p.hero('''                <h1>A Quarter Of The World Has No Safe-Water Number At All</h1>
                <p class="{hero_desc}">
                    The WHO/UNICEF ladder has two rungs that get quoted as one.
                    &ldquo;At least basic&rdquo; is a clean source within a
                    half-hour walk. &ldquo;Safely managed&rdquo; is that source on
                    the premises, working when you turn it on, and free of
                    contamination &mdash; and it is the SDG 6.1.1 indicator. For
                    {missn} countries and {missbn} billion people, the second
                    number does not exist.
                </p>

                <div class="header-actions">
                    <a href="https://washdata.org/" target="_blank" class="btn btn-primary">
                        WHO/UNICEF JMP
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="miss.billion">{missbn}B</div>
                        <div class="{label}">People in a country with no safely-managed figure</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="gap.median">{gapmed}</div>
                        <div class="{label}">Median points between the two rungs, where both exist</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="world.arrival">{arrive}</div>
                        <div class="{label}">Universal coverage at the last 24 years&rsquo; rate</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="back.count">{backn} of {backof}</div>
                        <div class="{label}">Countries lower in 2022 than in 2015</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline"><span data-fact="miss.countries">{missn}</span> of the <span data-fact="have.basic">{haveb}</span> countries that publish a basic drinking water figure publish no safely-managed figure at all &mdash; <span data-fact="miss.billion">{missbn}</span> billion people, <span data-fact="miss.pct">{misspct}%</span> of the population those estimates cover. Safely managed is the SDG 6.1.1 indicator, so for a quarter of the world the goal is being measured with a number nobody has.</p>
                    <ul class="tldr-list">
                        <li>The largest is {misstopc}, <span data-fact="miss.top.people">{misstopp:,}</span> million people, published at <span data-fact="miss.top.basic">{misstopb}%</span> basic and blank on safely managed. <span data-fact="miss.rich">{missrich}</span> of the {missn} are high-income countries &mdash; Australia and Saudi Arabia among them &mdash; so this is not a story about survey capacity.</li>
                        <li>Where both rungs exist they are far apart: a median <span data-fact="gap.median">{gapmed}</span> points across <span data-fact="gap.reporting">{gapn}</span> countries, and <span data-fact="gap.over40">{gap40}</span> of them 40 points or more. {gapc} is <span data-fact="gap.top.basic">{gapb}%</span> basic and <span data-fact="gap.top.safely">{gaps_}%</span> safely managed.</li>
                        <li>Indonesia reports <span data-fact="id.basic">{idb}%</span> basic and <span data-fact="id.safely">{ids}%</span> safely managed across <span data-fact="id.people">{idp:,}</span> million people. The Philippines reports <span data-fact="ph.basic">{phb}%</span> and <span data-fact="ph.safely">{phs}%</span> &mdash; a <span data-fact="ph.gap">{phg}</span>-point difference between the two ways of saying the same sentence.</li>
                        <li>The world went from <span data-fact="world.first">{w0}%</span> safely managed in {y0} to <span data-fact="world.last">{w1}%</span> in {y1}: <span data-fact="world.rate">{rate}</span> points a year. Held at that rate, universal coverage arrives in <span data-fact="world.arrival">{arrive}</span> &mdash; <span data-fact="world.late">{late}</span> years after the 2030 target.</li>
                        <li>Progress is not uniform. <span data-fact="back.count">{backn}</span> of the <span data-fact="back.of">{backof}</span> countries with readings in both years were lower in 2022 than in 2015, the year the goals were adopted. Rural coverage worldwide is <span data-fact="world.rural">{wrur}%</span> against <span data-fact="world.urban">{wurb}%</span> urban.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "The Indicator That Is Not There",
                  "Every country in this dataset is measured against SDG target 6.1, "
                  "and the indicator for it is the safely-managed share. For "
                  "{missn} of them that share has never been estimated. They are not "
                  "zeroes and they are not low numbers &mdash; the column is "
                  "blank.".format(**F),
                  [("No safely-managed figure", "{v}".format(v=F["missn"]),
                    "miss.countries",
                    "Of <span data-fact=\"have.basic\">{b}</span> countries with a "
                    "basic figure. Only <span data-fact=\"have.safely\">{s}</span> "
                    "have the strict one."
                    .format(b=F["haveb"], s=F["haves"])),
                   ("People in them", "{v} billion".format(v=F["missbn"]),
                    "miss.billion",
                    "<span data-fact=\"miss.pct\">{p}%</span> of the population "
                    "these estimates cover. {c} alone is "
                    "<span data-fact=\"miss.top.people\">{n:,}</span> million of it, "
                    "published at <span data-fact=\"miss.top.basic\">{v}%</span> "
                    "basic.".format(p=F["misspct"], c=F["misstopc"],
                                    n=F["misstopp"], v=F["misstopb"])),
                   ("High-income countries among them",
                    "{v}".format(v=F["missrich"]), "miss.rich",
                    "Australia and Saudi Arabia are on this list. Whatever the "
                    "missing rung is, it is not simply a matter of a country being "
                    "too poor to run the survey.")],
                  "Countries with a basic figure but no safely-managed one, by "
                  "population",
                  "missingChart"),

        p.section(2, "Two Rungs, Quoted As One",
                  "Where both figures exist, the distance between them is the "
                  "distance between &ldquo;there is a tap within half an hour&rdquo; "
                  "and &ldquo;the tap is here, it works, and the water is "
                  "clean&rdquo;. Across {gapn} countries the median distance is "
                  "{gapmed} points.".format(**F),
                  [("Median distance", "{v} pts".format(v=F["gapmed"]), "gap.median",
                    "Across <span data-fact=\"gap.reporting\">{n}</span> countries "
                    "reporting both. <span data-fact=\"gap.over40\">{o}</span> of "
                    "them are forty points or more apart."
                    .format(n=F["gapn"], o=F["gap40"])),
                   (F["gapc"], "{a}% &rarr; {b}%".format(a=F["gapb"], b=F["gaps_"]),
                    "gap.top.basic",
                    "The widest of any country over twenty million people: a "
                    "<span data-fact=\"gap.top.pts\">{p}</span>-point drop between "
                    "the generous rung and the strict one."
                    .format(p=F["gappts"])),
                   ("The Philippines",
                    "{a}% &rarr; {b}%".format(a=F["phb"], b=F["phs"]), "ph.basic",
                    "A <span data-fact=\"ph.gap\">{g}</span>-point difference. Both "
                    "numbers are true and they describe very different mornings."
                    .format(g=F["phg"]))],
                  "At least basic against safely managed, for the twenty most "
                  "populous countries reporting both",
                  "gapChart"),

        p.section(3, "2030, Arriving In {arrive}".format(**F),
                  "Target 6.1 is universal and equitable access to safe drinking "
                  "water by 2030. The world moved from {w0}% to {w1}% between {y0} "
                  "and {y1}. That is {rate} points a year, and the arithmetic from "
                  "there is not complicated.".format(**F),
                  [("Rate of progress", "{v} pts/yr".format(v=F["rate"]),
                    "world.rate",
                    "From <span data-fact=\"world.first\">{a}%</span> in {y0} to "
                    "<span data-fact=\"world.last\">{b}%</span> in {y1}, straight-"
                    "line across the whole published series."
                    .format(a=F["w0"], b=F["w1"], y0=F["y0"], y1=F["y1"])),
                   ("Universal coverage", "{v}".format(v=F["arrive"]),
                    "world.arrival",
                    "If that rate simply continues. That is "
                    "<span data-fact=\"world.late\">{l}</span> years after the "
                    "target, and later still for anywhere starting lower than the "
                    "world average.".format(l=F["late"])),
                   ("Countries going backwards",
                    "{a} of {b}".format(a=F["backn"], b=F["backof"]), "back.count",
                    "Lower in 2022 than in 2015, the year the goals were adopted. "
                    "The world total still rose, which is what an average over "
                    "unequal parts does.")],
                  "The world's safely-managed share, {y0} to {y1}, against the line "
                  "that reaches 100% in 2030".format(**F),
                  "trendChart"),

        p.section(4, "Where You Live Inside The Country",
                  "The same ladder, split by residence. Worldwide the urban figure "
                  "is {wurb}% and the rural figure is {wrur}% &mdash; a {wrrgap}-"
                  "point gap that a national average hides in exactly the way an "
                  "annual average hides an hourly one.".format(**F),
                  [("Urban, worldwide", "{v}%".format(v=F["wurb"]), "world.urban",
                    "Against <span data-fact=\"world.rural\">{r}%</span> rural: a "
                    "<span data-fact=\"world.rr.gap\">{g}</span>-point gap in 2022."
                    .format(r=F["wrur"], g=F["wrrgap"])),
                   (F["rrc"], "{a}% vs {b}%".format(a=F["rru"], b=F["rrr"]),
                    "rr.top.urban",
                    "The widest urban&ndash;rural split of any country over twenty "
                    "million people, from "
                    "<span data-fact=\"rr.top.rural\">{b}%</span> rural to {a}% "
                    "urban.".format(a=F["rru"], b=F["rrr"])),
                   ("Countries where rural leads",
                    "{a} of {b}".format(a=F["rrahead"], b=F["rrn"]), "rr.ruralahead",
                    "Small, and not zero. The rule has exceptions and this page "
                    "would rather name them than round them off.")],
                  "Urban against rural safely-managed share, for the countries "
                  "reporting both",
                  "urbanRuralChart"),

        p.section(5, "The Bottom Of The Ladder Did Move",
                  "This page is mostly about a number that is missing or overstated, "
                  "so it is worth being clear where the data shows real and large "
                  "improvement. Open defecation fell from {od0}% of the world in "
                  "{y0} to {odw}% &mdash; and that series is measured, not "
                  "modelled.".format(**F),
                  [("Open defecation, {y0}".format(**F), "{v}%".format(v=F["od0"]),
                    "od.world.2000",
                    "Share of the world's population. The bottom rung of the "
                    "sanitation ladder, and the one that moved most."),
                   ("Open defecation, latest", "{v}%".format(v=F["odw"]), "od.world",
                    "A fall of roughly three quarters in a quarter century. Progress "
                    "at the bottom of a ladder is easier to make and easier to "
                    "measure than progress at the top."),
                   ("Sanitation's missing rung", "{v}".format(v=F["missan"]),
                    "miss.sanitation",
                    "Countries with a basic sanitation figure and no safely-managed "
                    "one, covering "
                    "<span data-fact=\"miss.sanitation.people\">{p:,}</span> million "
                    "people. The same hole, in the other ladder."
                    .format(p=F["missanp"]))],
                  "The world's sanitation ladder over time: open defecation, at "
                  "least basic, and safely managed",
                  "ladderChart"),

        p.prose(6, "Two Publishers, One Set Of Estimates",
                "These figures come from the WHO/UNICEF Joint Monitoring Programme. "
                "Two organisations republish them and neither carries the whole "
                "series, so both are read and every overlapping value is compared.",
                [("The cross-check",
                  "Every country-year-indicator pair the two publishers share is "
                  "compared and the fetch aborts if any disagrees. %s pairs "
                  "overlap and the worst disagreement is %s points. That verifies "
                  "the copies match each other, not that the underlying estimates "
                  "are right."
                  % (format(F["checked"], ","), F["worstdiff"])),
                 ("Neither one is complete",
                  "%s pairs appear only in WHO's copy and %s only in the World "
                  "Bank's. Reading either alone would have quietly dropped part of "
                  "the record, and the union is what this page uses."
                  % (format(F["onlygho"], ","), format(F["onlywb"], ","))),
                 ("A null that is not a zero",
                  "WHO publishes open defecation at country level with a null in "
                  "the numeric field and a whole-percent string beside it. Reading "
                  "it the way every other indicator here is read drops 14,023 rows "
                  "while the request still returns 200. It is taken from the World "
                  "Bank instead and checked against WHO's rounded copy, where the "
                  "worst gap across %s pairs is exactly half a point &mdash; which "
                  "is what rounding to a whole number allows and no more."
                  % format(F["odpairs"], ","))]),

        p.prose(7, "What These Numbers Are Not",
                "A share of a population is a modelled estimate built from household "
                "surveys and censuses, not a meter reading. Four limits matter for "
                "everything above.",
                [("A blank is not a zero",
                  "The %d countries with no safely-managed figure are excluded from "
                  "every average on this page rather than counted as zero. That is "
                  "the honest treatment and it also means every world figure here "
                  "describes the countries that report, not the world."
                  % F["missn"]),
                 ("Estimates, not measurements",
                  "JMP fits a regression through survey points, so a country's "
                  "annual series is smoother than reality and a single year's change "
                  "is rarely a single year's event. This is why the page reads "
                  "2015 against 2022 rather than year on year."),
                 ("Handwashing is the thinnest series",
                  "Only %d of the %d countries have a basic-handwashing figure and "
                  "%d do not, so no world map is drawn from it here. It is in the "
                  "CSVs for anyone who wants it, with the gaps visible."
                  % (F["hwhave"], F["n"], F["hwmiss"])),
                 ("National averages hide their own tails",
                  "The urban and rural split above is one cut of that, and it is the "
                  "only one these estimates support. A national figure of %s%% says "
                  "nothing about which households inside the country are in the "
                  "other %s%%." % (F["w1"], r(100 - F["w1"], 2)))]),
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
                        <li><span data-fact="miss.countries">{missn}</span> of
                        <span data-fact="have.basic">{haveb}</span> countries publish
                        a basic drinking water figure and no safely-managed one:
                        <span data-fact="miss.billion">{missbn}</span> billion people,
                        <span data-fact="miss.pct">{misspct}%</span> of the population
                        covered. That missing figure is the SDG 6.1.1 indicator.</li>
                        <li><span data-fact="miss.rich">{missrich}</span> of them are
                        high-income countries, so the gap is not explained by survey
                        capacity alone.</li>
                        <li>Where both rungs exist the median distance is
                        <span data-fact="gap.median">{gapmed}</span> points across
                        <span data-fact="gap.reporting">{gapn}</span> countries, and
                        <span data-fact="gap.over40">{gap40}</span> are forty points
                        or more apart.</li>
                        <li>The world moved
                        <span data-fact="world.first">{w0}%</span> to
                        <span data-fact="world.last">{w1}%</span> between {y0} and
                        {y1}, <span data-fact="world.rate">{rate}</span> points a
                        year. Universal coverage at that rate arrives in
                        <span data-fact="world.arrival">{arrive}</span>,
                        <span data-fact="world.late">{late}</span> years late.</li>
                        <li><span data-fact="back.count">{backn}</span> of
                        <span data-fact="back.of">{backof}</span> countries were lower
                        in 2022 than in 2015. Rural coverage worldwide is
                        <span data-fact="world.rural">{wrur}%</span> against
                        <span data-fact="world.urban">{wurb}%</span> urban.</li>
                        <li>Open defecation fell from
                        <span data-fact="od.world.2000">{od0}%</span> to
                        <span data-fact="od.world">{odw}%</span> of the world. The
                        bottom of the ladder moved a great deal; the top did not.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    # ---- chart data ---------------------------------------------------------
    M = miss[:16]
    G = sorted([x for x in gaps if x["population"] > 20000000],
               key=lambda x: -x["population"])[:20]
    G.sort(key=lambda x: -x["basic_minus_safely_pts"])
    # every year from the first observation to the target, so the six years
    # between the last reading and 2030 occupy six columns rather than one --
    # a category axis labelled [..., 2023, 2024, 2030] draws that last gap the
    # same width as every other and makes the target line look reachable
    AX = list(range(wyears[0], 2031))
    RR = sorted(rr, key=lambda x: -(x["water_safely_managed_urban_pct"]
                                    - x["water_safely_managed_rural_pct"]))
    RRB = [x for x in RR if x["population"] > 10000000][:18]
    lyears = sorted({int(x["year"]) for x in world
                     if x["scope"] == "GLOBAL" and x["residence"] == "total"
                     and x["indicator"] == "sanitation_basic"})

    charts = ['''        // 01 the countries the strict indicator does not cover, by the number of
        //    people in them. The bar is population; the label carries the basic
        //    figure they DO publish, which is the number that gets quoted instead.
        new Chart(document.getElementById('missingChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Population (millions)', data: %s,
                             backgroundColor: '#0ea5e9' }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: (c) =>
                               'At least basic: ' + %s[c.dataIndex] + '%%  |  '
                               + 'Safely managed: not estimated' } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Population (millions)' } } }
            }
        });''' % (js([x["country"] for x in M]),
                  js([r(x["population"] / 1e6, 1) for x in M]),
                  js([x["water_basic_pct"] for x in M])),

              '''        // 02 the two rungs side by side. The blue bar is what gets quoted; the
        //    amber bar is the SDG indicator. Ordered by the distance between them.
        new Chart(document.getElementById('gapChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'At least basic', data: %s,
                      backgroundColor: 'rgba(59,130,246,0.75)' },
                    { label: 'Safely managed (SDG 6.1.1)', data: %s,
                      backgroundColor: '#f59e0b' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                scales: { x: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of population' } } }
            }
        });''' % (js([x["country"] for x in G]),
                  js([x["water_basic_pct"] for x in G]),
                  js([x["water_safely_managed_pct"] for x in G])),

              '''        // 03 the observed world series against the straight line that would have
        //    reached 100%% in 2030 from where the world stood in 2015. The distance
        //    between the two lines at 2030 is the whole of section 3.
        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Safely managed, observed', data: %s,
                      borderColor: '#0ea5e9', backgroundColor: '#0ea5e9',
                      pointBackgroundColor: '#0ea5e9',
                      borderWidth: 3, pointRadius: 3, fill: false },
                    { label: 'The path to 100%% by 2030', data: %s,
                      borderColor: '#94a3b8', backgroundColor: '#94a3b8',
                      pointBackgroundColor: '#94a3b8',
                      borderWidth: 2, borderDash: [6, 4], pointRadius: 0,
                      fill: false },
                    { label: 'Where the observed rate leads', data: %s,
                      borderColor: '#ef4444', backgroundColor: '#ef4444',
                      pointBackgroundColor: '#ef4444',
                      borderWidth: 2, borderDash: [2, 3], pointRadius: 0,
                      fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { min: 50, max: 100,
                               title: { display: true, text: '%% of world population' } } }
            }
        });''' % (js(AX),
                  js([(r(W("water_safely_managed", y), 2) if y in wyears else None)
                      for y in AX]),
                  js([(None if y < 2015 else
                       r(W("water_safely_managed", 2015)
                         + (100 - W("water_safely_managed", 2015))
                         * (y - 2015) / (2030 - 2015), 2))
                      for y in AX]),
                  js([(r(W("water_safely_managed", y1)
                         + rate * (y - y1), 2) if y >= y1 else None) for y in AX])),

              '''        // 04 urban against rural for the same country, as a paired bar. Every pair
        //    that leans left is a national average concealing a rural figure.
        new Chart(document.getElementById('urbanRuralChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Urban', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Rural', data: %s, backgroundColor: '#22c55e' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                scales: { x: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% safely managed' } } }
            }
        });''' % (js([x["country"] for x in RRB]),
                  js([x["water_safely_managed_urban_pct"] for x in RRB]),
                  js([x["water_safely_managed_rural_pct"] for x in RRB])),

              '''        // 05 the sanitation ladder over time. Open defecation is the series that
        //    moved; safely managed is the series that did not.
        new Chart(document.getElementById('ladderChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'At least basic sanitation', data: %s,
                      borderColor: '#3b82f6', backgroundColor: '#3b82f6',
                      pointBackgroundColor: '#3b82f6',
                      borderWidth: 3, pointRadius: 2, fill: false },
                    { label: 'Safely managed sanitation', data: %s,
                      borderColor: '#f59e0b', backgroundColor: '#f59e0b',
                      pointBackgroundColor: '#f59e0b',
                      borderWidth: 3, pointRadius: 2, fill: false },
                    { label: 'Open defecation', data: %s,
                      borderColor: '#ef4444', backgroundColor: '#ef4444',
                      pointBackgroundColor: '#ef4444',
                      borderWidth: 3, pointRadius: 2, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of world population' } } }
            }
        });''' % (js(lyears),
                  js([r(W("sanitation_basic", y) or 0, 2) or None for y in lyears]),
                  js([(lambda v: r(v, 2) if v is not None else None)(
                      W("sanitation_safely_managed", y)) for y in lyears]),
                  js([(lambda v: r(v, 2) if v is not None else None)(
                      W("open_defecation", y)) for y in lyears])),
    ]

    p.sections(S)
    p.charts(charts)
    p.faq({
        "How many people have no safely managed drinking water estimate?":
            "%s billion, in %d countries -- %s%% of the population these estimates "
            "cover. Those countries publish an at-least-basic figure and nothing for "
            "safely managed, which is the SDG 6.1.1 indicator. The largest is %s at "
            "%s million people, published at %s%% basic. %d of the %d are "
            "high-income countries, so this is not only a question of survey "
            "capacity."
            % (F["missbn"], F["missn"], F["misspct"], F["misstopc"],
               format(int(F["misstopp"]), ","), F["misstopb"], F["missrich"],
               F["missn"]),
        "What is the difference between basic and safely managed drinking water?":
            "At least basic means an improved source within a 30-minute round trip "
            "including queueing. Safely managed means an improved source ON the "
            "premises, available when needed, and free from faecal and priority "
            "chemical contamination. Safely managed is a strict subset of basic, and "
            "across the %d countries reporting both, the median distance between "
            "them is %s points -- %d countries are forty points or more apart."
            % (F["gapn"], F["gapmed"], F["gap40"]),
        "Will the world meet SDG 6.1 by 2030?":
            "Not at the rate it has been moving. The safely-managed share of the "
            "world went from %s%% in %d to %s%% in %d, which is %s points a year. "
            "Continued straight, universal coverage arrives in %d -- %d years after "
            "the target. And progress is uneven: %d of the %d countries with "
            "readings in both years were lower in 2022 than in 2015."
            % (F["w0"], F["y0"], F["w1"], F["y1"], F["rate"], F["arrive"],
               F["late"], F["backn"], F["backof"]),
        "Where does this water and sanitation data come from?":
            "The WHO/UNICEF Joint Monitoring Programme, read from two free APIs that "
            "republish it: the WHO Global Health Observatory and the World Bank's "
            "World Development Indicators. Neither carries the whole series -- %s "
            "country-year-indicator pairs appear only in WHO's copy and %s only in "
            "the World Bank's -- so both are read and all %s overlapping pairs are "
            "compared. The worst disagreement is %s points."
            % (format(F["onlygho"], ","), format(F["onlywb"], ","),
               format(F["checked"], ","), F["worstdiff"]),
        "Is rural water coverage worse than urban?":
            "Almost always, and by a lot. Worldwide the urban safely-managed share "
            "is %s%% against %s%% rural, a %s-point gap. Of the %d countries "
            "reporting both, %d have rural ahead of urban. The widest split among "
            "countries over twenty million people is %s: %s%% urban against %s%% "
            "rural."
            % (F["wurb"], F["wrur"], F["wrrgap"], F["rrn"], F["rrahead"],
               F["rrc"], F["rru"], F["rrr"]),
    })
    p.save(len(S), len(charts))
    blog(F)


BLOG = "blog/global-water-analysis.html"
BLOG_SCAFFOLD = "blog/global-grid-analysis.html"


def blog(F):
    """Write the plain-language companion from the same numbers as the page.

    Hand-writing the blog post is how the two halves drift: the project page gets
    rebuilt from data and its twin keeps a figure from three vintages ago. Every
    number below is interpolated from the same F dict the project page uses, and
    every one carries a data-fact so verify_facts binds it to a CSV row.
    """
    import io
    src = io.open(BLOG_SCAFFOLD, encoding="utf-8").read()

    def swap(pat, rep, why):
        import re
        new, n = re.subn(pat, lambda _m: rep, src_holder[0], count=1)
        if n != 1:
            raise SystemExit("blog: %s matched %d times" % (why, n))
        src_holder[0] = new

    src_holder = [src]
    swap(r"<title>[^<]*</title>",
         "<title>%s | Allan Ni\u00f1al</title>" % TITLE, "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % DESC, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="%s | Allan Ni\u00f1al">' % TITLE,
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % DESC, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="%s">' % TITLE, "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % DESC, "tw:desc")
    swap(r'"headline": "[^"]*"', '"headline": "%s"' % TITLE, "headline")
    swap(r'"description": "[^"]*"', '"description": "%s"' % DESC, "ld desc")
    src_holder[0] = src_holder[0].replace("global-grid-analysis", "global-water-analysis")
    swap(r'<span class="current">[^<]*</span>',
         '<span class="current">Global Water</span>', "crumb")
    swap(r'<span class="meta-tag category">[^<]*</span>',
         '<span class="meta-tag category">Global</span>', "category")
    swap(r'<h1>[^<]*</h1>', "<h1>%s</h1>" % H1, "h1")
    swap(r'<p class="subtitle">[^<]*</p>',
         '<p class="subtitle">%s</p>' % SUB, "subtitle")

    a = src_holder[0].index('<div class="article-content">')
    a = src_holder[0].index("\n", a) + 1
    b = src_holder[0].index('                <div class="project-link-box">')
    src_holder[0] = src_holder[0][:a] + body(F) + src_holder[0][b:]

    io.open(BLOG, "w", encoding="utf-8").write(src_holder[0])
    print("rebuilt %s: %d paragraph(s)"
          % (BLOG, src_holder[0].count("<p>", a, len(src_holder[0]))))


TITLE = "Two Billion People Have No Number For Safe Water"
DESC = ("There are two ways to count who has clean water. One is kind, one is "
        "strict. For 2.21 billion people, nobody has worked out the strict one.")
H1 = "Two Billion People Have No Number For Safe Water"
SUB = "There are two ways to count. Nobody did the strict one for a quarter of us."


def fact(k, v):
    return '<span data-fact="%s">%s</span>' % (k, v)


def body(F):
    f = fact
    return """                <p>There are two ways to say how many people have clean water.</p>

                <p>The kind way asks one thing. Is there a clean tap within a half-hour walk?</p>

                <p>The strict way asks three more. Is the tap at your home? Does it work when you turn it on? Is the water clean?</p>

                <p>The strict one is what the world promised to fix by 2030.</p>

                <p>For {missbn} billion people, nobody has worked it out.</p>

                <div class="stat-callout">
                    <div class="stat-number">{missbn_f}B</div>
                    <div class="stat-label">People in a country with no safe-water number at all</div>
                </div>

                <h2>A Blank, Not A Low Score</h2>

                <p>{haveb} countries give us the kind number. Only {haves} give us the strict one.</p>

                <p>So {missn} countries have a blank. Not a bad score. A blank.</p>

                <p>China is the biggest one. That is {misstopp} million people. China says {misstopb} per cent for the kind number. For the strict one there is nothing at all.</p>

                <p>You might think this is about money. It is not.</p>

                <p>{missrich} of those {missn2} are rich countries. Australia is one of them. So is Saudi Arabia.</p>

                <h2>When Both Numbers Exist</h2>

                <p>Now look at the countries that do have both.</p>

                <p>The two numbers are not close.</p>

                <p>Nepal says {gapb} per cent for the kind one. It says {gaps_} per cent for the strict one.</p>

                <p>The middle country is {gapmed} points apart. And {gap40} countries are more than 40 points apart.</p>

                <p>My own country is one of them. The Philippines says {phb} per cent. Then it says {phs} per cent.</p>

                <p>Both are true. They just answer different questions.</p>

                <h2>2030 Is Not Going To Happen</h2>

                <p>In 2000, {w0} per cent of the world had the strict thing. By 2024 it was {w1} per cent.</p>

                <p>That is {rate} points a year.</p>

                <p>Keep that speed and we all get there in {arrive}.</p>

                <div class="stat-callout">
                    <div class="stat-number">{arrive_f}</div>
                    <div class="stat-label">When everyone gets safe water, at the speed of the last 24 years</div>
                </div>

                <p>The goal says 2030. So we are {late} years late.</p>

                <h2>Some Places Went Backwards</h2>

                <p>{backn} of {backof} countries had a lower score in 2022 than in 2015. 2015 is the year the world set the goal.</p>

                <p>The world total still went up. That is what an average does. It hides the parts.</p>

                <h2>Town And Village</h2>

                <p>In towns, {wurb} per cent of people have the strict thing. In villages and on farms, {wrur} per cent.</p>

                <p>That is a gap of {wrrgap} points.</p>

                <p>Colombia shows it best. Towns: {rru} per cent. Villages: {rrr} per cent.</p>

                <p>In {rrahead} of {rrn} countries it goes the other way. So it is not a rule. But it is close to one.</p>

                <h2>One Thing Did Get Much Better</h2>

                <p>I do not want to leave you with only bad news.</p>

                <p>In 2000, {od0} per cent of the world had no toilet at all. They went outside.</p>

                <p>By 2024 it was {odw} per cent.</p>

                <p>That is a huge drop. The bottom of the ladder moved a lot. The top of it barely moved.</p>

                <h2>I Read The Numbers Twice</h2>

                <p>All of this comes from one group. WHO and UNICEF count it together.</p>

                <p>Two websites hand the numbers out. I read both.</p>

                <p>Neither one has all of it. {onlygho} readings sit only on the first. {onlywb} sit only on the second.</p>

                <p>Where both had a reading, I checked them against each other. That was {checked} pairs. They matched every time.</p>

                <h2>Three Things I Cannot Tell You</h2>

                <p>A blank is not a zero. The {missn3} countries with no strict number are left out of every average here. So my world numbers describe the countries that report. Not the world.</p>

                <p>These are worked out from surveys, not read off a meter. One country's line is smoother than real life is.</p>

                <p>And a country number hides the homes inside it. {w1_f} per cent for the world tells you nothing about who the rest are.</p>

""".format(
        missbn=f("miss.billion", F["missbn"]), missbn_f=F["missbn"],
        haveb=f("have.basic", F["haveb"]), haves=f("have.safely", F["haves"]),
        missn=f("miss.countries", F["missn"]), missn2=F["missn"], missn3=F["missn"],
        misstopp=f("miss.top.people", format(int(F["misstopp"]), ",")),
        misstopb=f("miss.top.basic", F["misstopb"]),
        missrich=f("miss.rich", F["missrich"]),
        gapb=f("gap.top.basic", F["gapb"]), gaps_=f("gap.top.safely", F["gaps_"]),
        gapmed=f("gap.median", F["gapmed"]), gap40=f("gap.over40", F["gap40"]),
        phb=f("ph.basic", F["phb"]), phs=f("ph.safely", F["phs"]),
        w0=f("world.first", F["w0"]), w1=f("world.last", F["w1"]), w1_f=F["w1"],
        rate=f("world.rate", F["rate"]),
        arrive=f("world.arrival", F["arrive"]), arrive_f=F["arrive"],
        late=f("world.late", F["late"]),
        backn=f("back.count", F["backn"]), backof=f("back.of", F["backof"]),
        wurb=f("world.urban", F["wurb"]), wrur=f("world.rural", F["wrur"]),
        wrrgap=f("world.rr.gap", F["wrrgap"]),
        rru=f("rr.top.urban", F["rru"]), rrr=f("rr.top.rural", F["rrr"]),
        rrahead=f("rr.ruralahead", F["rrahead"]), rrn=f("rr.countries", F["rrn"]),
        od0=f("od.world.2000", F["od0"]), odw=f("od.world", F["odw"]),
        onlygho=f("gw.onlygho", format(F["onlygho"], ",")),
        onlywb=f("gw.onlywb", format(F["onlywb"], ",")),
        checked=f("gw.crosschecked", format(F["checked"], ",")),
    )


if __name__ == "__main__":
    main()
