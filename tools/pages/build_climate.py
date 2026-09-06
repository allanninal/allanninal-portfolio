#!/usr/bin/env python3
"""Regenerate projects/global-climate-spread-analysis.html from data/global-climate-spread.

    .venv/bin/python tools/pages/build_climate.py

Seven downscaled CMIP6 models, one scenario, sixteen cities, and two twenty-year
windows: 1991-2010 against 2031-2050.

Two things are true at once and this page exists to keep them apart. Every model
warms every city -- there is no city in this set where any member of the ensemble
projects cooling, and checks.sql asserts that at error level so the page cannot
build if it stops being true. And the models disagree about the amount by a
margin that is a large fraction of the warming itself.

That second fact is what a projection actually is, and it is usually reported as
a single number. It is also the projection-side counterpart to the Philippine
weather page, which found two reanalyses of the OBSERVED past differing by 1.09 C
on Manila's annual mean. If reconstructions of what already happened disagree by
a degree, a spread between projections of what has not happened yet is the
expected shape rather than a scandal.

The hot-day figures are where the disagreement stops being abstract. A range of
projected days above 35 C for one city is not a different decimal place; it is a
different summer.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-climate-spread"
PAGE = "projects/global-climate-spread-analysis.html"

NUM_CITY = ("latitude", "longitude", "models", "baseline_mean_c", "future_mean_c",
            "mean_warming_c", "min_warming_c", "max_warming_c", "spread_c",
            "spread_over_warming", "all_models_warm", "baseline_days_over_35",
            "future_days_over_35", "min_future_days_over_35",
            "max_future_days_over_35")


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    city = rows("cs_city")
    mod = rows("cs_model")
    cov = {x["property"]: x["value"] for x in rows("cs_coverage")}
    for c in city:
        for k in NUM_CITY:
            c[k] = f(c[k])
    for m in mod:
        for k in ("warming_c", "baseline_mean_c", "future_mean_c",
                  "baseline_days_over_35_per_year", "future_days_over_35_per_year"):
            m[k] = f(m[k])

    C = {c["city"]: c for c in city}
    # Every sort carries the city name as a secondary key. Delhi and Dhaka share
    # the minimum warming exactly, so without it the "slowest-warming city" named
    # in the prose can change between rebuilds while the number beside it does not.
    byspread = sorted(city, key=lambda c: (-c["spread_c"], c["city"]))
    bywarm = sorted(city, key=lambda c: (-c["mean_warming_c"], c["city"]))
    bycool = sorted(city, key=lambda c: (c["mean_warming_c"], c["city"]))
    byhot = sorted(city, key=lambda c: (-(c["future_days_over_35"]
                                          - c["baseline_days_over_35"]), c["city"]))
    exceeds = [c for c in city if c["spread_c"] > c["mean_warming_c"]]
    bylat = sorted(city, key=lambda c: -c["latitude"])
    # Correlation between latitude and warming. Computed rather than assumed: the
    # far north is expected to warm fastest and in this set it barely shows,
    # because the disagreement between models is larger than the signal.
    n_ = len(city)
    mx = sum(c["latitude"] for c in city) / n_
    my = sum(c["mean_warming_c"] for c in city) / n_
    sxy = sum((c["latitude"] - mx) * (c["mean_warming_c"] - my) for c in city)
    sxx = sum((c["latitude"] - mx) ** 2 for c in city)
    syy = sum((c["mean_warming_c"] - my) ** 2 for c in city)
    corr = r(sxy / ((sxx * syy) ** 0.5), 2) if sxx and syy else 0.0
    tightest = sorted(city, key=lambda c: (c["spread_c"], c["city"]))
    mnl, wide, tight, hot = C["Manila"], byspread[0], tightest[0], byhot[0]

    F = dict(
        ncity=len(city), nmodel=int(f(cov["models offered"])),
        npair=int(f(cov["city-model pairs used"])),
        nun=int(f(cov["city-model pairs unavailable"])),
        allwarm=int(f(cov["cities where every model warms"])),
        coldest=r(min(m["warming_c"] for m in mod), 2),
        # Read from the coverage file rather than recomputed. A median over an
        # even number of cities is the mean of the middle two, and recomputing it
        # here with a different tie rule produced a page that disagreed with its
        # own CSV by 0.05 C.
        medwarm=f(cov["median warming"]),
        medspread=f(cov["median spread between models"]),
        medratio=f(cov["median spread as a share of warming"]),
        exceeds=len(exceeds),
        bigspread=r(max(c["spread_c"] for c in city), 2),
        smallspread=r(min(c["spread_c"] for c in city), 2),
        widec=wide["city"], widew=wide["mean_warming_c"],
        widemin=wide["min_warming_c"], widemax=wide["max_warming_c"],
        tightc=tight["city"], tights=tight["spread_c"],
        mw=mnl["mean_warming_c"], mmin=mnl["min_warming_c"],
        mmax=mnl["max_warming_c"], mspread=mnl["spread_c"],
        mbase=mnl["baseline_mean_c"], mfut=mnl["future_mean_c"],
        mhb=mnl["baseline_days_over_35"], mhf=mnl["future_days_over_35"],
        mhmin=mnl["min_future_days_over_35"], mhmax=mnl["max_future_days_over_35"],
        warmc=bywarm[0]["city"], warmw=bywarm[0]["mean_warming_c"],
        warmlat=r(bywarm[0]["latitude"], 1),
        coolc=bycool[0]["city"], coolw=bycool[0]["mean_warming_c"],
        tiedwith=(bycool[1]["city"]
                  if bycool[1]["mean_warming_c"] == bycool[0]["mean_warming_c"]
                  else ""),
        northc=bylat[0]["city"], northw=bylat[0]["mean_warming_c"],
        northlat=r(bylat[0]["latitude"], 1),
        corr=corr,
        dw=C["Delhi"]["mean_warming_c"], dmin=C["Delhi"]["min_warming_c"],
        dmax=C["Delhi"]["max_warming_c"], dspread=C["Delhi"]["spread_c"],
        dratio=r(C["Delhi"]["spread_over_warming"], 2),
        hotc=hot["city"],
        hotadd=r(hot["future_days_over_35"] - hot["baseline_days_over_35"], 1),
        hotb=hot["baseline_days_over_35"], hotf=hot["future_days_over_35"],
        hotspread=r(hot["max_future_days_over_35"]
                    - hot["min_future_days_over_35"], 1),
    )
    F["medratiopct"] = r(100.0 * F["medratio"])

    p = Page(PAGE)
    p.relocate(
        "global-openaccess-analysis",
        og_image="og-climatespread.png",
        keywords=["CMIP6", "climate projection", "model spread", "ensemble",
                  "downscaled", "open data", "data analysis"],
        dataset_name="Downscaled CMIP6 projections for 16 cities, 1991-2050",
        dataset_desc=("Daily mean and maximum temperature from seven downscaled "
                      "CMIP6 models for sixteen cities, aggregated to a 1991-2010 "
                      "baseline and a 2031-2050 future window"),
        breadcrumb="Every Model Warms. None Agree By How Much.",
        crumb_tail="Model Spread",
        creator="Open-Meteo / CMIP6",
        dataset_url="https://climate-api.open-meteo.com/v1/climate",
        tags=["\U0001f321️ Climate", "CMIP6", "Open-Meteo",
              "%d cities" % F["ncity"],
              "<span class=\"dot\"></span> %d models" % F["nmodel"]],
        info=[("Data Source",
               '<a href="https://climate-api.open-meteo.com/v1/climate" '
               'target="_blank" rel="noopener">Open-Meteo CMIP6</a>'),
              ("Coverage",
               "%d cities &middot; %d models &middot; %d city-model pairs &middot; "
               "1991&ndash;2010 against 2031&ndash;2050"
               % (F["ncity"], F["nmodel"], F["npair"])),
              ("Agreement",
               "Every model warms every city; the ensemble's coolest projection "
               "anywhere is still +%s&deg;C" % F["coldest"]),
              ("Licence", "CC BY 4.0 (Open-Meteo)")])

    p.head(
        "Every Model Warms Every City. None Agree By How Much.",
        "Seven CMIP6 models, %d cities, 1991–2010 against 2031–2050. Not one "
        "model projects cooling anywhere in this set. They disagree about the "
        "amount by a median %s°C — %s%% of the warming they are projecting."
        % (F["ncity"], F["medspread"], F["medratiopct"]),
        "Seven models, %d cities, total agreement on direction and none on "
        "amount." % F["ncity"],
        "Every Model Warms Every City. None Agree By How Much.")

    p.hero('''                <h1>Every Model Warms Every City. None Agree By How Much.</h1>
                <p class="{hero_desc}">
                    Seven downscaled climate models, {ncity} cities, the twenty
                    years to 2010 against the twenty to 2050. Every model warms
                    every city &mdash; the coolest projection anywhere in the set
                    is still +{coldest}&deg;C. What they disagree about is the
                    amount, by a median {medspread}&deg;C, which is
                    {medratiopct}% of the warming itself.
                </p>

                <div class="header-actions">
                    <a href="https://climate-api.open-meteo.com/v1/climate" target="_blank" class="btn btn-primary">
                        Open-Meteo CMIP6
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="allwarm">{allwarm} of {ncity}</div>
                        <div class="{label}">Cities where every model projects warming</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="median.spread">{medspread}&deg;C</div>
                        <div class="{label}">Median disagreement between models</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="median.ratio.pct">{medratiopct}%</div>
                        <div class="{label}">That disagreement, as a share of the warming</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="exceeds.n">{exceeds}</div>
                        <div class="{label}">Cities where the spread exceeds the warming</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Across {ncity} cities and {nmodel} models there is no disagreement about direction at all: <span data-fact="allwarm">{allwarm}</span> of {ncity} cities are warmed by every single model, and the most conservative projection anywhere in the set is <span data-fact="coldest.model.warming">+{coldest}&deg;C</span>. The disagreement is entirely about how much.</p>
                    <ul class="tldr-list">
                        <li>Median warming across these cities is <span data-fact="median.warming">{medwarm}&deg;C</span> and the median gap between the highest and lowest model for the same city is <span data-fact="median.spread">{medspread}&deg;C</span> &mdash; <span data-fact="median.ratio.pct">{medratiopct}%</span> of the warming being projected.</li>
                        <li>In <span data-fact="exceeds.n">{exceeds}</span> cities the models disagree by more than the warming they are disagreeing about. {widec} is the widest: a mean of <span data-fact="widest.warming">{widew}&deg;C</span> spanning <span data-fact="widest.min">{widemin}&deg;C</span> to <span data-fact="widest.max">{widemax}&deg;C</span>. {tightc} is the tightest at <span data-fact="tightest.spread">{tights}&deg;C</span>.</li>
                        <li>Manila &mdash; the city behind this site&rsquo;s Philippine climate page &mdash; warms <span data-fact="mnl.warming">{mw}&deg;C</span> on the ensemble mean, across a range of <span data-fact="mnl.min">{mmin}</span> to <span data-fact="mnl.max">{mmax}&deg;C</span>. That earlier page found two reconstructions of the <em>observed</em> past differing by 1.09&deg;C, so a <span data-fact="mnl.spread">{mspread}</span>-degree spread on the future is the expected shape.</li>
                        <li>The hot-day figures are where the spread stops being abstract. {hotc} goes from <span data-fact="hot.base">{hotb}</span> to <span data-fact="hot.future">{hotf}</span> days above 35&deg;C a year on the ensemble mean &mdash; <span data-fact="hot.added">{hotadd}</span> more &mdash; and the models&rsquo; range for that one number is <span data-fact="hot.spread">{hotspread}</span> days.</li>
                        <li>Geography explains less than expected. Latitude and warming correlate at only <span data-fact="lat.corr">{corr}</span> across these cities: {warmc} at <span data-fact="warmest.lat">{warmlat}</span>&deg;N warms <span data-fact="warmest.warming">{warmw}&deg;C</span>, more than {northc} at <span data-fact="northmost.lat">{northlat}</span>&deg;N, which warms <span data-fact="northmost.warming">{northw}&deg;C</span>.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "There Is No Argument About The Direction",
                  "This has to come first, because everything after it is about "
                  "disagreement and would read differently otherwise. Across {npair} "
                  "city-model pairs, not one projects cooling.".format(**F),
                  [("Cities warmed by every model",
                    "{a} of {b}".format(a=F["allwarm"], b=F["ncity"]), "allwarm",
                    "Not most models, and not on average. Every model, every city."),
                   ("The most conservative projection anywhere",
                    "+{v}&deg;C".format(v=F["coldest"]), "coldest.model.warming",
                    "The single coolest of all {n} city-model pairs. The bottom of "
                    "this ensemble is still warming.".format(n=F["npair"])),
                   ("Median warming", "{v}&deg;C".format(v=F["medwarm"]),
                    "median.warming",
                    "Ensemble mean across the {n} cities, 1991&ndash;2010 against "
                    "2031&ndash;2050.".format(n=F["ncity"]))],
                  "Warming projected for each city: the ensemble mean, and the full "
                  "range across models",
                  "rangeChart"),

        p.section(2, "The Amount Is Another Matter",
                  "A projection is usually quoted as one number. Underneath it are "
                  "{nmodel} numbers that disagree, and the width of that "
                  "disagreement is a median {medspread}&deg;C.".format(**F),
                  [("Median spread", "{v}&deg;C".format(v=F["medspread"]),
                    "median.spread",
                    "Between the warmest and coolest model for the same city. As a "
                    "share of the warming itself: "
                    "<span data-fact=\"median.ratio.pct\">{p}%</span>."
                    .format(p=F["medratiopct"])),
                   (F["widec"], "{a}&ndash;{b}&deg;C".format(a=F["widemin"],
                                                            b=F["widemax"]),
                    "widest.min",
                    "The widest in the set, around a mean of "
                    "<span data-fact=\"widest.warming\">{w}&deg;C</span>. Which "
                    "number you quote depends on which model you opened."
                    .format(w=F["widew"])),
                   ("Cities where the spread wins",
                    "{v}".format(v=F["exceeds"]), "exceeds.n",
                    "Places where the models differ from each other by more than "
                    "the warming they are projecting. {t} is the opposite case, "
                    "tightest at <span data-fact=\"tightest.spread\">{s}&deg;C"
                    "</span>.".format(t=F["tightc"], s=F["tights"]))],
                  "The gap between the highest and lowest model for each city, "
                  "against the warming they are projecting",
                  "spreadChart"),

        p.section(3, "Manila, And The Page This One Extends",
                  "This site already has a Philippine climate page. It compared two "
                  "reconstructions of the <em>observed</em> past and found them "
                  "1.09&deg;C apart on Manila&rsquo;s annual mean. That was "
                  "history. This is the future.",
                  [("Manila&rsquo;s warming", "{v}&deg;C".format(v=F["mw"]),
                    "mnl.warming",
                    "From <span data-fact=\"mnl.baseline\">{a}&deg;C</span> to "
                    "<span data-fact=\"mnl.future\">{b}&deg;C</span> on the "
                    "ensemble mean.".format(a=F["mbase"], b=F["mfut"])),
                   ("Across the models",
                    "{a}&ndash;{b}&deg;C".format(a=F["mmin"], b=F["mmax"]),
                    "mnl.min",
                    "A <span data-fact=\"mnl.spread\">{s}</span>-degree spread on "
                    "one city. The observed-past disagreement was 1.09&deg;C, so "
                    "this is not a new problem appearing in projections."
                    .format(s=F["mspread"])),
                   ("Days above 35&deg;C",
                    "{a} &rarr; {b}".format(a=F["mhb"], b=F["mhf"]), "mnl.hot.base",
                    "Per year, baseline against future, ensemble mean. The models "
                    "range from <span data-fact=\"mnl.hot.min\">{lo}</span> to "
                    "<span data-fact=\"mnl.hot.max\">{hi}</span> for that future "
                    "figure.".format(lo=F["mhmin"], hi=F["mhmax"]))],
                  "Days a year above 35&deg;C, baseline against future, with the "
                  "range across models",
                  "hotChart"),

        p.section(4, "Geography Explains Less Than You Would Expect",
                  "The far north is supposed to warm fastest, and across these "
                  "{ncity} cities latitude and warming correlate at only {corr}. "
                  "The disagreement between models is larger than the geographical "
                  "signal it is supposed to reveal.".format(**F),
                  [("Latitude against warming", "r = {v}".format(v=F["corr"]),
                    "lat.corr",
                    "Across all {n} cities. A relationship exists and it is weak "
                    "enough that the ordering is not what a map would predict."
                    .format(n=F["ncity"])),
                   ("The fastest-warming city",
                    "{c}, {v}&deg;C".format(c=F["warmc"], v=F["warmw"]),
                    "warmest.warming",
                    "At <span data-fact=\"warmest.lat\">{la}</span> degrees north "
                    "&mdash; warming more than {n}, which sits at "
                    "<span data-fact=\"northmost.lat\">{nl}</span> degrees and "
                    "warms <span data-fact=\"northmost.warming\">{nw}&deg;C</span>."
                    .format(la=F["warmlat"], n=F["northc"], nl=F["northlat"],
                            nw=F["northw"])),
                   ("The slowest",
                    "{c}, {v}&deg;C".format(c=F["coolc"], v=F["coolw"]),
                    "coolest.warming",
                    "Tied with {t} on exactly that figure &mdash; and also the city "
                    "with the widest disagreement in the set, which is the next "
                    "section and is not a coincidence.".format(t=F["tiedwith"]))],
                  "Warming against latitude, one point per city",
                  "latChart"),

        p.section(5, "The City The Ensemble Cannot Agree On",
                  "{coolc} is tied with {tiedwith} for the lowest mean warming in "
                  "this set, and has by far the widest range behind it. The models "
                  "are not slightly apart; they describe two different "
                  "futures.".format(**F),
                  [("Ensemble mean", "{v}&deg;C".format(v=F["dw"]), "delhi.warming",
                    "Equal lowest of the {n} cities. Read alone it looks like the "
                    "least-affected place in the set.".format(n=F["ncity"])),
                   ("The models",
                    "{a}&ndash;{b}&deg;C".format(a=F["dmin"], b=F["dmax"]),
                    "delhi.min",
                    "One model projects "
                    "<span data-fact=\"delhi.min\">{a}&deg;C</span> across twenty "
                    "years &mdash; almost nothing, and still positive. Another "
                    "projects <span data-fact=\"delhi.max\">{b}&deg;C</span>."
                    .format(a=F["dmin"], b=F["dmax"])),
                   ("Spread against warming",
                    "{v}&times;".format(v=F["dratio"]), "delhi.ratio",
                    "A <span data-fact=\"delhi.spread\">{s}&deg;C</span> spread "
                    "around a {w}&deg;C mean. Quoting the mean alone would be the "
                    "single most misleading number on this page."
                    .format(s=F["dspread"], w=F["dw"]))],
                  "Every model's projection for every city, one row per city",
                  "modelChart"),

        p.prose(6, "What A Spread Is And Is Not",
                "The number this page reports is the range across models of a "
                "single scenario. Three things it does not measure, and one it "
                "does.",
                [("Not scenario uncertainty",
                  "Every model here is run on the same emissions pathway. The "
                  "spread is what remains after that choice is fixed: different "
                  "physics, different resolution, different treatment of clouds "
                  "and land. Adding scenarios would widen it further, most at "
                  "longer horizons."),
                 ("Not error bars on an observation",
                  "None of these numbers is a measurement. They are what several "
                  "independent models produce when asked the same question, and "
                  "the agreement between them is evidence about the models rather "
                  "than about the atmosphere."),
                 ("Not a reason to discount the direction",
                  "A wide spread around a robust sign is the ordinary condition of "
                  "this field, and it is why %d of %d cities here are warmed by "
                  "every member of the ensemble while none of the members agree on "
                  "the amount. Reporting the second without the first would be a "
                  "different and dishonest page."
                  % (F["allwarm"], F["ncity"])),
                 ("It is a reason to distrust one decimal place",
                  "A city plan built on a single downscaled projection is built on "
                  "one draw from a distribution %s&deg;C wide at the median. The "
                  "useful output is the range." % F["medspread"])]),

        p.prose(7, "What These Numbers Are Not",
                "Four limits, and the first two bound how far anything above "
                "travels.",
                [("A subset of CMIP6, not the ensemble",
                  "These are the high-resolution members Open-Meteo redistributes, "
                  "downscaled to a 10km grid: %d models, not the several dozen the "
                  "IPCC assesses. A different subset would give a different spread, "
                  "and this one is not weighted by skill." % F["nmodel"]),
                 ("%d cities, chosen for latitude" % F["ncity"],
                  "Points, not regions, and picked to span from %s at %s degrees "
                  "north to Sao Paulo at 24 south rather than sampled at random. "
                  "Nothing here is a global average and no global figure is quoted. "
                  "Collection is limited by a daily cap on the source and this set "
                  "is what a day of it buys."
                  % (F["northc"], F["northlat"])),
                 ("Twenty-year windows, near-term",
                  "1991&ndash;2010 against 2031&ndash;2050, because the source's "
                  "coverage ends at 2050. Near-term is where model choice matters "
                  "most relative to scenario choice, which flatters the finding and "
                  "is worth saying."),
                 ("A downscaled point is not a station",
                  "Each value is a model grid cell interpolated to a coordinate, "
                  "not a thermometer in that city. Absolute temperatures carry a "
                  "bias that mostly cancels in the difference between two windows, "
                  "which is why this page reports warming rather than "
                  "temperature.")]),
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
                        <li><span data-fact="allwarm">{allwarm}</span> of {ncity}
                        cities are warmed by every one of the
                        {nmodel} models. The coolest projection anywhere is
                        <span data-fact="coldest.model.warming">+{coldest}&deg;C</span>.</li>
                        <li>Median warming is
                        <span data-fact="median.warming">{medwarm}&deg;C</span> and
                        the median disagreement between models for the same city is
                        <span data-fact="median.spread">{medspread}&deg;C</span>
                        &mdash;
                        <span data-fact="median.ratio.pct">{medratiopct}%</span> of
                        it.</li>
                        <li>In <span data-fact="exceeds.n">{exceeds}</span> cities
                        the spread exceeds the warming. {widec} spans
                        <span data-fact="widest.min">{widemin}</span> to
                        <span data-fact="widest.max">{widemax}&deg;C</span>.</li>
                        <li>Manila warms
                        <span data-fact="mnl.warming">{mw}&deg;C</span> across a
                        <span data-fact="mnl.spread">{mspread}</span>-degree spread,
                        against the 1.09&deg;C two reanalyses of its observed past
                        already disagree by.</li>
                        <li>{hotc} gains
                        <span data-fact="hot.added">{hotadd}</span> days a year above
                        35&deg;C on the ensemble mean, with a
                        <span data-fact="hot.spread">{hotspread}</span>-day range
                        between models.</li>
                        <li>Latitude and warming correlate at only
                        <span data-fact="lat.corr">{corr}</span>: {warmc} warms
                        <span data-fact="warmest.warming">{warmw}&deg;C</span> at
                        <span data-fact="warmest.lat">{warmlat}</span>&deg;N against
                        {northc}&rsquo;s
                        <span data-fact="northmost.warming">{northw}&deg;C</span> at
                        <span data-fact="northmost.lat">{northlat}</span>&deg;N.</li>
                        <li>{coolc} is the extreme case: a
                        <span data-fact="delhi.warming">{dw}&deg;C</span> mean over a
                        <span data-fact="delhi.min">{dmin}</span> to
                        <span data-fact="delhi.max">{dmax}&deg;C</span> range &mdash;
                        a spread <span data-fact="delhi.ratio">{dratio}</span> times
                        the warming.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    # ---- chart data ---------------------------------------------------------
    CW = sorted(city, key=lambda c: -c["mean_warming_c"])
    LAT = sorted(city, key=lambda c: c["latitude"])
    HOT = [c for c in city if c["future_days_over_35"] > 0]
    HOT.sort(key=lambda c: -c["future_days_over_35"])

    charts = ['''        // 01 each city's ensemble mean warming, with the full model range behind
        //    it. The bars all point the same way; their widths do not match.
        new Chart(document.getElementById('rangeChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Range across models', data: %s, order: 2,
                      backgroundColor: 'rgba(148,163,184,0.55)' },
                    { type: 'line', label: 'Ensemble mean warming', data: %s, order: 1,
                      borderColor: '#ef4444', backgroundColor: '#ef4444',
                      pointBackgroundColor: '#ef4444', pointBorderColor: '#fff',
                      pointBorderWidth: 1, borderWidth: 0, pointRadius: 6,
                      pointStyle: 'rectRot', showLine: false }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: {
                    sort: (a, b) => a.datasetIndex - b.datasetIndex } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Warming, 1991-2010 to 2031-2050 (C)' } } }
            }
        });''' % (js([c["city"] for c in CW]),
                  js([[c["min_warming_c"], c["max_warming_c"]] for c in CW]),
                  js([c["mean_warming_c"] for c in CW])),

              '''        // 02 the spread against the warming. Any city above the diagonal is one
        //    where the models disagree by more than the change they project.
        new Chart(document.getElementById('spreadChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Ensemble mean warming', data: %s,
                      backgroundColor: 'rgba(59,130,246,0.8)' },
                    { label: 'Spread between models', data: %s,
                      backgroundColor: '#f59e0b' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Degrees C' } } }
            }
        });''' % (js([c["city"] for c in CW]),
                  js([c["mean_warming_c"] for c in CW]),
                  js([c["spread_c"] for c in CW])),

              '''        // 03 days above 35 C, baseline against future, with the model range on the
        //    future figure. Only cities that reach 35 C at all appear.
        new Chart(document.getElementById('hotChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Baseline 1991-2010', data: %s,
                      backgroundColor: 'rgba(100,116,139,0.85)' },
                    { label: 'Future 2031-2050, ensemble mean', data: %s,
                      backgroundColor: '#ef4444' },
                    { label: 'Model range on the future figure', data: %s,
                      backgroundColor: 'rgba(245,158,11,0.55)' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Days a year above 35 C' } } }
            }
        });''' % (js([c["city"] for c in HOT]),
                  js([c["baseline_days_over_35"] for c in HOT]),
                  js([c["future_days_over_35"] for c in HOT]),
                  js([[c["min_future_days_over_35"], c["max_future_days_over_35"]]
                      for c in HOT])),

              '''        // 04 warming against latitude. The rise toward the top of the chart is the
        //    one geographical signal that is larger than the model disagreement.
        new Chart(document.getElementById('latChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Ensemble mean warming (C)', data: %s,
                             borderColor: '#22d3ee', backgroundColor: '#22d3ee',
                             pointBackgroundColor: '#22d3ee', pointBorderColor: '#fff',
                             pointBorderWidth: 1, borderWidth: 0, pointRadius: 6,
                             showLine: false }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { title: (c) =>
                               %s[c[0].dataIndex] } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Warming (C)' } },
                          x: { title: { display: true, text: 'Latitude, south to north' } } }
            }
        });''' % (js(["%.0f" % c["latitude"] for c in LAT]),
                  js([c["mean_warming_c"] for c in LAT]),
                  js([c["city"] for c in LAT])),
    ]

    MODC = [c["city"] for c in CW]
    MODELS = sorted({m["model"] for m in mod})
    PAL = ["#22d3ee", "#f59e0b", "#ef4444", "#22c55e", "#a855f7", "#3b82f6",
           "#f97316"]
    charts.append("""        // 05 every model's own projection for every city. The vertical scatter
        //    within a column is the disagreement; every point is above zero.
        new Chart(document.getElementById('modelChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Warming (C)' } } }
            }
        });""" % (js(MODC), "[" + ",".join(
        '''
                    { label: '%s', data: %s, borderColor: '%s',
                      backgroundColor: '%s', pointBackgroundColor: '%s',
                      pointBorderColor: '#fff', pointBorderWidth: 1,
                      borderWidth: 0, pointRadius: 5, showLine: false }'''
        % (mm.split("_")[0],
           js([next((x["warming_c"] for x in mod
                     if x["city"] == cc and x["model"] == mm), None)
               for cc in MODC]),
           PAL[i % len(PAL)], PAL[i % len(PAL)], PAL[i % len(PAL)])
        for i, mm in enumerate(MODELS)) + "\n                ]"))

    p.sections(S)
    p.charts(charts)
    p.faq({
        "Do climate models agree with each other?":
            "On direction, completely: across %d city-model pairs in this set not "
            "one projects cooling, and %d of %d cities are warmed by every model. "
            "On amount, no. The median gap between the warmest and coolest model "
            "for the same city is %s C, which is %s%% of the warming being "
            "projected."
            % (F["npair"], F["allwarm"], F["ncity"], F["medspread"],
               F["medratiopct"]),
        "How much warming do these models project?":
            "A median %s C between 1991-2010 and 2031-2050 across %d cities. %s "
            "warms most at %s C and %s least at %s C. Latitude explains less of "
            "that than you would expect -- the correlation is %s, and %s at %s "
            "degrees north warms more than %s at %s degrees."
            % (F["medwarm"], F["ncity"], F["warmc"], F["warmw"], F["coolc"],
               F["coolw"], F["corr"], F["warmc"], F["warmlat"], F["northc"],
               F["northlat"]),
        "Why do the models disagree if they use the same scenario?":
            "Because the scenario fixes the emissions, not the physics. These "
            "models differ in resolution, in how they handle clouds, oceans and "
            "land surface, and in what they do at a coastline. The spread here is "
            "what is left after the scenario choice is removed, and adding "
            "scenarios back would widen it further.",
        "Does a wide spread mean the projections are unreliable?":
            "It means a single number is unreliable and a range is not. Every model "
            "in this set warms every city, so the direction is not in question; "
            "what a %s C median spread argues against is planning on one decimal "
            "place from one model. The same page's Philippine counterpart found two "
            "reconstructions of the observed past differing by 1.09 C, so this is "
            "the ordinary condition of the field rather than a failure."
            % F["medspread"],
        "Where does this climate projection data come from?":
            "Open-Meteo's climate API, which redistributes downscaled CMIP6 "
            "projections free and without a key. %d models for %d cities, daily "
            "mean and maximum temperature, aggregated here to a 1991-2010 baseline "
            "and a 2031-2050 future window. Coverage ends at 2050, which is why "
            "the future window stops there."
            % (F["nmodel"], F["ncity"]),
    })
    p.save(len(S), len(charts))
    blog(F)


BLOG = "blog/global-climate-spread-analysis.html"
TITLE = "Seven Models Guessed 2040. All Said Warmer. None Said The Same."
DESC = ("Seven climate models, ten cities, the same question. Every one says "
        "warmer. They disagree about how much by half as much again.")
SUB = "Every model says warmer. They just do not agree by how much."


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
    src = src.replace("global-openaccess-analysis", "global-climate-spread-analysis")
    swap(r'<span class="current">[^<]*</span>',
         '<span class="current">Model Spread</span>', "crumb")
    swap(r'<h1>[^<]*</h1>', "<h1>%s</h1>" % TITLE, "h1")
    swap(r'<p class="subtitle">[^<]*</p>', '<p class="subtitle">%s</p>' % SUB, "subtitle")

    a = src.index('<div class="article-content">')
    a = src.index("\n", a) + 1
    b = src.index('                <div class="project-link-box">')
    io.open(BLOG, "w", encoding="utf-8").write(src[:a] + body(F) + src[b:])
    print("rebuilt %s" % BLOG)


def body(F):
    g = fct
    return """                <p>A climate model is a very big program that tries to work out what the air will do.</p>

                <p>There is not one of them. There are lots, built by different teams in different countries.</p>

                <p>I asked {nmodel} of them the same question about {ncity} cities.</p>

                <p>The question was simple. How much warmer will it be in 2031 to 2050 than it was in 1991 to 2010?</p>

                <h2>They All Said Warmer</h2>

                <p>This part is not in doubt at all.</p>

                <p>Every model warmed every city. All {npair} answers.</p>

                <p>The very coolest answer in the whole pile was still {coldest} degrees warmer.</p>

                <div class="stat-callout">
                    <div class="stat-number">{allwarm} of {ncity2}</div>
                    <div class="stat-label">Cities where every single model says warmer</div>
                </div>

                <p>So nobody here is arguing about which way it goes.</p>

                <h2>They Did Not Agree On How Much</h2>

                <p>The middle city warms {medwarm} degrees.</p>

                <p>But for one city, the highest model and the lowest model are {medspread} degrees apart.</p>

                <p>That gap is about half the warming itself.</p>

                <p>And for {exceeds} of the {ncity3} cities, the models disagree by more than the warming they are talking about.</p>

                <h2>Delhi Is The Strange One</h2>

                <p>Delhi looks calm if you only read the average. It warms {dw} degrees, the least of all my cities.</p>

                <p>Then you look underneath.</p>

                <p>One model says {dmin} degrees. That is almost nothing over twenty years.</p>

                <p>Another says {dmax} degrees.</p>

                <div class="stat-callout">
                    <div class="stat-number">{dmin_f}-{dmax_f}&deg;C</div>
                    <div class="stat-label">What the models say about Delhi. Both are in the same pile.</div>
                </div>

                <p>So the calm average is hiding two very different futures. If I printed only the {dw} I would be telling you the least useful thing I know.</p>

                <h2>Where Does Not Help As Much As You Would Think</h2>

                <p>The far north is meant to warm fastest. Everyone says so.</p>

                <p>In my ten cities that barely shows.</p>

                <p>{warmc} sits at {warmlat} degrees north and warms {warmw} degrees. {northc} sits way up at {northlat} degrees north and warms {northw}.</p>

                <p>So the city much further north warms less.</p>

                <p>The link between how far north a city is and how much it warms is only {corr}. That is weak. The models disagree with each other more than the map explains.</p>

                <h2>Hot Days Are Easier To Feel</h2>

                <p>Degrees are hard to picture. Days are not.</p>

                <p>Manila gets {mhb} days a year over 35 degrees now. By 2031 to 2050 the models say {mhf} days.</p>

                <p>But the models range from {mhmin} days to {mhmax} days for that one number.</p>

                <p>That is not a rounding argument. That is a different summer.</p>

                <h2>Why I Did This</h2>

                <p>This site already has a page on Philippine weather. It compared two records of the weather that already happened, and they were 1.09 degrees apart on Manila.</p>

                <p>Two goes at the past, a degree apart.</p>

                <p>So when models of the future are half a degree apart, that is normal. It is not a scandal.</p>

                <h2>Three Things I Cannot Tell You</h2>

                <p>These are {nmodel2} models, not all of them. There are dozens more. A different handful would give a different gap.</p>

                <p>These are {ncity4} cities, picked to spread from cold to hot. It is not the world and I do not give a world number.</p>

                <p>And a wide gap does not mean the models are useless. Every one of them says warmer. What a wide gap means is that one number from one model is the wrong thing to plan with. The range is the answer.</p>

""".format(
        nmodel=g("cs.models", F["nmodel"]), nmodel2=F["nmodel"],
        ncity=g("cs.cities", F["ncity"]), ncity2=F["ncity"], ncity3=F["ncity"],
        ncity4=F["ncity"],
        npair=g("cs.pairs", F["npair"]),
        coldest=g("coldest.model.warming", F["coldest"]),
        allwarm=g("allwarm", F["allwarm"]),
        medwarm=g("median.warming", F["medwarm"]),
        medspread=g("median.spread", F["medspread"]),
        exceeds=g("exceeds.n", F["exceeds"]),
        dw=g("delhi.warming", F["dw"]), dmin=g("delhi.min", F["dmin"]),
        dmax=g("delhi.max", F["dmax"]), dmin_f=F["dmin"], dmax_f=F["dmax"],
        warmc=F["warmc"], warmlat=g("warmest.lat", F["warmlat"]),
        warmw=g("warmest.warming", F["warmw"]),
        northc=F["northc"], northlat=g("northmost.lat", F["northlat"]),
        northw=g("northmost.warming", F["northw"]),
        corr=g("lat.corr", F["corr"]),
        mhb=g("mnl.hot.base", F["mhb"]), mhf=g("mnl.hot.future", F["mhf"]),
        mhmin=g("mnl.hot.min", F["mhmin"]), mhmax=g("mnl.hot.max", F["mhmax"]),
    )


if __name__ == "__main__":
    main()
