#!/usr/bin/env python3
"""Regenerate projects/weather-analysis.html from data/ph-weather CSVs.

    .venv/bin/python tools/pages/build_weather.py

The published page reported "447K+ records" from a Kaggle scrape of OpenWeather
readings covering about fourteen months, and carried charts about warming.
Fourteen months has nothing in it that a climate trend can be computed from.

Open-Meteo serves ERA5 daily data from 1940 without a key: 31,047 days per city
in a single request, no gaps. Nine points from Laoag to Davao gives 1,117,692
daily observations and 85 complete years each.

The thing that makes this page worth writing is that the answer depends on which
reanalysis you ask, and by a lot. Over the 75 years both cover:

    ERA5       Manila mean 27.69 C, warming 0.122 C/decade
    ERA5-Land  Manila mean 26.60 C, warming 0.072 C/decade

Same atmosphere, two reconstructions, 1.09 C apart on the level and a factor of
1.9 apart on the rate across the six cities checked both ways. So this page quotes
no single absolute temperature as "the temperature", reports every trend as a
range, and treats the gap between the models as a floor on the uncertainty rather
than a rounding detail. Both agree on what matters: every city warmed, and the
recent decades are the warmest.

The most robust finding is a threshold count rather than a trend. Eight of the
nine cities set their hottest day on record in 2020 or later -- only Baguio's
stands from 1966 -- and eight of nine had their warmest complete decade in the
2010s. Days above 35 C in Laoag went from 0.3 a year in the 1950s to 30.99 in the
2020s. The direction of that is robust; its magnitude is not, because a threshold
count depends on absolute temperature and the two models are more than a degree
apart. The page says so.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-weather"
PAGE = "projects/weather-analysis.html"
MONTH = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
         "Oct", "Nov", "Dec"]


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_weather_annual")
    mon = rows("ph_weather_monthly")
    dec = rows("ph_weather_decades")
    hot = rows("ph_weather_hotdays")
    rec = rows("ph_weather_records")
    mdl = rows("ph_weather_models")
    trd = rows("ph_weather_trends")
    cov = {x["property"]: x["value"] for x in rows("ph_weather_coverage")}

    shared = [x for x in trd if x["basis"] == "shared period"]
    e5 = [x for x in shared if x["model"] == "era5"]
    el = [x for x in shared if x["model"] == "era5_land"]
    spread = [x for x in shared if x["model"] == "model spread"]
    CITIES = [x["city"] for x in e5]

    def tr(city, model):
        return [x for x in shared if x["city"] == city and x["model"] == model][0]

    hotrec = [x for x in rec if x["record"] == "hottest day"]
    hottest = max(hotrec, key=lambda x: f(x["value"]))
    old = [x for x in hotrec if x["date"] < "2020-01-01"]

    def rain(city):
        got = [f(x["rainfall_mm"]) for x in ann if x["city"] == city]
        return sum(got) / len(got)
    bycity = sorted({x["city"] for x in ann}, key=lambda c: -rain(c))

    def hd(city, d):
        got = [x for x in hot if x["city"] == city and x["decade"] == d]
        return f(got[0]["days_over_35c_per_year"]) if got else None

    manila_dec = sorted((x for x in dec if x["city"] == "Manila"),
                        key=lambda x: x["decade"])
    complete = [x for x in manila_dec if x["completeness"] == "complete"]
    warm_last = sum(1 for c in {x["city"] for x in dec}
                    if max((f(x["mean_c"]) for x in dec
                            if x["city"] == c and x["completeness"] == "complete"))
                    == f([x for x in dec if x["city"] == c
                          and x["decade"] == "2010s"][0]["mean_c"]))
    lao_mon = [x for x in mon if x["city"] == "Laoag"]

    F = dict(
        cities=int(f(cov["cities"])), days=int(f(cov["days per city"])),
        obs=int(f(cov["daily observations read"])),
        years=int(f(cov["complete years per city"])),
        first=min(int(x["year"]) for x in ann),
        last=max(int(x["year"]) for x in ann),
        models=int(f(cov["reanalysis models compared"])),
        gapabs=f(cov["absolute disagreement between models, Manila"]),
        gaptrend=f(cov["trend disagreement between models, Manila"]),
        e5min=min(f(x["trend_c_per_decade"]) for x in e5),
        e5max=max(f(x["trend_c_per_decade"]) for x in e5),
        elmin=min(f(x["trend_c_per_decade"]) for x in el),
        elmax=max(f(x["trend_c_per_decade"]) for x in el),
        ratio=r(sum(f(tr(c, "era5")["trend_c_per_decade"])
                    / f(tr(c, "era5_land")["trend_c_per_decade"])
                    for c in CITIES) / len(CITIES), 2),
        ncross=len(CITIES),
        shfirst=min(int(x["first_year"]) for x in shared),
        warmall=sum(1 for c in CITIES
                    if min(f(tr(c, "era5")["trend_c_per_decade"]),
                           f(tr(c, "era5_land")["trend_c_per_decade"])) > 0),
        me5=f(tr("Manila", "era5")["trend_c_per_decade"]),
        mel=f(tr("Manila", "era5_land")["trend_c_per_decade"]),
        me5m=f(tr("Manila", "era5")["mean_c"]),
        melm=f(tr("Manila", "era5_land")["mean_c"]),
        me5c=f(tr("Manila", "era5")["change_c"]),
        melc=f(tr("Manila", "era5_land")["change_c"]),
        d70=f([x for x in dec if x["city"] == "Manila"
               and x["decade"] == "1970s"][0]["mean_c"]),
        d10=f([x for x in dec if x["city"] == "Manila"
               and x["decade"] == "2010s"][0]["mean_c"]),
        warmdec=max(complete, key=lambda x: f(x["mean_c"]))["decade"],
        cooldec=min(complete, key=lambda x: f(x["mean_c"]))["decade"],
        warmlast=warm_last,
        partial=int([x for x in dec if x["city"] == "Manila"
                     and x["decade"] == "2020s"][0]["years"]),
        recent=len([x for x in hotrec if x["date"] >= "2020-01-01"]),
        hotv=f(hottest["value"]), hotc=hottest["city"], hotd=hottest["date"],
        oldc=old[0]["city"] if old else "", oldy=old[0]["date"][:4] if old else "",
        lao50=hd("Laoag", "1950s"), lao20=hd("Laoag", "2020s"),
        man50=hd("Manila", "1950s"), man20=hd("Manila", "2020s"),
        wet=bycity[0], wetmm=r(rain(bycity[0])),
        dry=bycity[-1], drymm=r(rain(bycity[-1])),
        laowet=r(max(f(x["mean_rainfall_mm"]) for x in lao_mon)),
        laodry=r(min(f(x["mean_rainfall_mm"]) for x in lao_mon)),
        # Unrounded, for the ratios below. Dividing the rounded millimetre figures
        # gave 2.06 against SQL's 2.05 and 27 against 28, because 16 mm is rounded
        # up from 15.5 -- a ratio of two rounded numbers is not the rounded ratio.
        _wetraw=rain(bycity[0]), _dryraw=rain(bycity[-1]),
        _laowetraw=max(f(x["mean_rainfall_mm"]) for x in lao_mon),
        _laodryraw=min(f(x["mean_rainfall_mm"]) for x in lao_mon),
        bag=f(tr("Baguio", "era5_land")["mean_c"]),
    )
    F["manratio"] = r(F["man20"] / F["man50"], 1)
    F["rainratio"] = r(F["_wetraw"] / F["_dryraw"], 2)
    F["laoratio"] = r(F["_laowetraw"] / F["_laodryraw"])
    F["bagvsman"] = r(F["melm"] - F["bag"], 2)

    p = Page(PAGE)
    p.hero('''                <h1>How Much Warmer? That Depends Which Model You Ask</h1>
                <p class="{hero_desc}">
                    {obs:,} daily observations across {cities} Philippine grid
                    cells, {first} to {last}. Two reanalyses of the same
                    atmosphere put Manila's warming at {mel} and {me5}&nbsp;&deg;C
                    a decade &mdash; so this page reports ranges. Both agree
                    {recent} of the {cities} cities set their hottest day on
                    record since 2020.
                </p>

                <div class="header-actions">
                    <a href="https://open-meteo.com/en/docs/historical-weather-api" target="_blank" class="btn btn-primary">
                        ERA5 archive (Open-Meteo)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="heat.recent.records">{recent} of {cities}</div>
                        <div class="{label}">Cities whose hottest day on record is since 2020</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="trend.ratio">{ratio}&times;</div>
                        <div class="{label}">How much faster one reanalysis warms than the other</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="wx.gap.abs">{gapabs}</div>
                        <div class="{label}">&deg;C apart on Manila's mean temperature</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="hot.laoag.2020s">{lao20}</div>
                        <div class="{label}">Days a year over 35&deg;C in Laoag, from {lao50} in the 1950s</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Two reanalyses of the same atmosphere disagree by <span data-fact="wx.gap.abs">{gapabs}</span>&nbsp;&deg;C on Manila's mean temperature and by a factor of <span data-fact="trend.ratio">{ratio}</span> on how fast it is warming. That is not a rounding detail, so no single absolute temperature appears on this page and every trend is a range.</p>
                    <ul class="tldr-list">
                        <li>Across the <span data-fact="trend.cities">{ncross}</span> cities checked both ways over the {shfirst}&ndash;{last} period they share, warming runs from <span data-fact="trend.land.min">{elmin}</span> to <span data-fact="trend.land.max">{elmax}</span>&nbsp;&deg;C a decade on ERA5-Land and <span data-fact="trend.era5.min">{e5min}</span> to <span data-fact="trend.era5.max">{e5max}</span> on ERA5. The two agree on direction in <span data-fact="trend.warming.everywhere">{warmall}</span> of {ncross} cities &mdash; all of them.</li>
                        <li>The firmest finding is a count, not a slope. <span data-fact="heat.recent.records">{recent}</span> of the <span data-fact="wx.cities">{cities}</span> cities set their hottest day on record in 2020 or later; only {oldc}'s stands, from {oldy}. And <span data-fact="dec.warmest.is.last">{warmlast}</span> of {cities} had their warmest complete decade in the 2010s.</li>
                        <li>Days above 35&nbsp;&deg;C in Laoag went from <span data-fact="hot.laoag.1950s">{lao50}</span> a year in the 1950s to <span data-fact="hot.laoag.2020s">{lao20}</span> in the 2020s; Manila from <span data-fact="hot.manila.1950s">{man50}</span> to <span data-fact="hot.manila.2020s">{man20}</span>. A threshold count depends on absolute temperature, though, and the models are more than a degree apart &mdash; so the direction is solid and the magnitude is not.</li>
                        <li>Manila's coolest complete decade was the {cooldec} at <span data-fact="dec.manila.1970s">{d70}</span>&nbsp;&deg;C and its warmest the {warmdec} at <span data-fact="dec.manila.2010s">{d10}</span>. The 2020s hold only <span data-fact="dec.partial">{partial}</span> years and are labelled partial everywhere they appear.</li>
                        <li>This is reanalysis: a physical model constrained by whatever was measured, on a grid of roughly 25&nbsp;km. Not a thermometer record, and not fine enough to see a city apart from the land around it.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "The Same Atmosphere, Reconstructed Twice",
                  "ERA5 and ERA5-Land are both ECMWF reanalyses of the same "
                  "period, the second at higher resolution over land. Where they "
                  "disagree is the honest measure of how well any of this is "
                  "known, and they disagree more than most charts of warming "
                  "would suggest.",
                  [("On the level", "{v} &deg;C".format(v=F["gapabs"]),
                    "wx.gap.abs",
                    "Mean absolute difference on Manila's annual mean: "
                    "<span data-fact=\"manila.era5.mean\">{a}</span> against "
                    "<span data-fact=\"manila.land.mean\">{b}</span>&nbsp;&deg;C. "
                    "Neither is quoted on this page as the temperature."
                    .format(a=F["me5m"], b=F["melm"])),
                   ("On the rate", "{v}&times;".format(v=F["ratio"]),
                    "trend.ratio",
                    "ERA5 warms faster in every city checked. For Manila, "
                    "<span data-fact=\"manila.era5.trend\">{a}</span> against "
                    "<span data-fact=\"manila.land.trend\">{b}</span>&nbsp;&deg;C "
                    "a decade.".format(a=F["me5"], b=F["mel"])),
                   ("Where they agree", "{v} of {n}".format(v=F["warmall"],
                                                            n=F["ncross"]),
                    "trend.warming.everywhere",
                    "Cities where both models show warming. A check asserts it, "
                    "because the page's whole framing depends on the two "
                    "disagreeing about how much and not about whether.")],
                  "Annual mean temperature for Manila under both reanalyses",
                  "modelChart"),
        p.section(2, "Warming, As A Range",
                  "Trend per decade for the {n} cities fetched from both models, "
                  "computed over the {sf}&ndash;{last} years they both cover. "
                  "Comparing ERA5's 1940 start against ERA5-Land's 1950 one would "
                  "be partly a comparison of periods, and a check asserts the "
                  "shared window is used.".format(n=F["ncross"], sf=F["shfirst"],
                                                  last=F["last"]),
                  [("ERA5-Land",
                    "{a}&ndash;{b}".format(a=F["elmin"], b=F["elmax"]),
                    "trend.land.min",
                    "&deg;C per decade across the {n} cities. The more "
                    "conservative of the two.".format(n=F["ncross"])),
                   ("ERA5", "{a}&ndash;{b}".format(a=F["e5min"], b=F["e5max"]),
                    "trend.era5.min",
                    "The same cities, the same years. The upper bound is "
                    "<span data-fact=\"trend.era5.max\">{v}</span>."
                    .format(v=F["e5max"])),
                   ("Manila, first decade to last",
                    "+{a} to +{b} &deg;C".format(a=F["melc"], b=F["me5c"]),
                    "manila.land.change",
                    "Last ten years of the window against the first ten, on the "
                    "conservative model and then the other. Even the low end is a "
                    "shift a person would notice over a lifetime.")],
                  "Warming per decade by city, both reanalyses, %d onward"
                  % F["shfirst"], "trendChart"),
        p.section(3, "Eight Of Nine Records Are From The Last Five Years",
                  "The hottest single day in each city's 85-year record. This is "
                  "the most robust thing on the page, because a maximum does not "
                  "care about a model's mean bias in the way a trend line does.",
                  [("Records since 2020", "{v} of {n}".format(v=F["recent"],
                                                              n=F["cities"]),
                    "heat.recent.records",
                    "Cities whose hottest day on record falls in 2020 or later, "
                    "out of {n}.".format(n=F["cities"])),
                   ("The hottest", "{v} &deg;C".format(v=F["hotv"]),
                    "heat.hottest",
                    "In {c} on {d}. Every one of the nine records but one is from "
                    "this decade.".format(c=F["hotc"], d=F["hotd"])),
                   ("The exception: {c}".format(c=F["oldc"]),
                    "{y}".format(y=F["oldy"]), "heat.only.old.year",
                    'Whose record still stands from that year. It is the one city '
                    'in this set at altitude, '
                    '<span data-fact="baguio.vs.manila">{a}</span>&nbsp;&deg;C '
                    'cooler than Manila on average.'.format(a=F["bagvsman"]))],
                  "Hottest day on record, by city and year", "recordChart"),
        p.section(4, "Days Over Thirty-Five Degrees",
                  "A threshold count rather than a mean, by decade. The threshold "
                  "is a stated constant, and the caveat matters: because the two "
                  "reanalyses sit more than a degree apart on absolute "
                  "temperature, the number of days crossing any fixed line is "
                  "model-dependent. The direction here is robust; treat the "
                  "magnitude as indicative.",
                  [("Laoag", "{a} → {b}".format(a=F["lao50"], b=F["lao20"]),
                    "hot.laoag.1950s",
                    "Days a year above 35&nbsp;&deg;C, 1950s to 2020s &mdash; "
                    "from <span data-fact=\"hot.laoag.1950s\">{a}</span> to "
                    "<span data-fact=\"hot.laoag.2020s\">{b}</span>."
                    .format(a=F["lao50"], b=F["lao20"])),
                   ("Manila", "{a} → {b}".format(a=F["man50"], b=F["man20"]),
                    "hot.manila.1950s",
                    "<span data-fact=\"hot.manila.ratio\">{r}</span> times as "
                    "many, reaching "
                    "<span data-fact=\"hot.manila.2020s\">{b}</span> a year."
                    .format(r=F["manratio"], b=F["man20"])),
                   ("The 2020s are five years",
                    "{v} years".format(v=F["partial"]), "dec.partial",
                    "Not ten. Every decadal figure on this page carries its year "
                    "count, and a check fails if a partial decade is not labelled "
                    "as one.")],
                  "Days per year above 35 °C, by decade", "hotChart"),
        p.section(5, "Decade By Decade",
                  "Mean temperature per decade for all {n} cities. Two things are "
                  "visible: the 1970s are the coolest decade in most of them, and "
                  "the curve is flat until roughly 2000 and then is not."
                  .format(n=F["cities"]),
                  [("Manila's coolest", "{v} &deg;C".format(v=F["d70"]),
                    "dec.manila.1970s",
                    "The {c}. Cooler than the 1940s, which is why a straight line "
                    "through the whole record understates the recent part."
                    .format(c=F["cooldec"])),
                   ("Manila's warmest complete decade",
                    "{v} &deg;C".format(v=F["d10"]), "dec.manila.2010s",
                    "The {w}, and the partial 2020s are running warmer still."
                    .format(w=F["warmdec"])),
                   ("Across the set", "{v} of {n}".format(v=F["warmlast"],
                                                          n=F["cities"]),
                    "dec.warmest.is.last",
                    "Cities whose warmest complete decade is the 2010s &mdash; "
                    "the most recent complete one available.")],
                  "Mean temperature by decade, all cities", "decadeChart"),
        p.section(6, "Rain Is A Different Country",
                  "Mean annual rainfall and the shape of the year. Temperature "
                  "varies modestly across the archipelago; rainfall varies by more "
                  "than a factor of two, and the timing varies more than the "
                  "total.",
                  [(F["wet"], "{v:,.0f} mm".format(v=F["wetmm"]),
                    "rain.wettest.mm",
                    "A year, on average. The wettest of the nine."),
                   (F["dry"], "{v:,.0f} mm".format(v=F["drymm"]),
                    "rain.driest.mm",
                    "The driest, a ratio of "
                    "<span data-fact=\"rain.ratio\">{r}</span> between the two "
                    "&mdash; much wider than any temperature difference here."
                    .format(r=F["rainratio"])),
                   ("Laoag's wet against dry",
                    "{a:,.0f} vs {b:,.0f} mm".format(a=F["laowet"], b=F["laodry"]),
                    "rain.laoag.wet",
                    "Wettest month against driest, "
                    "<span data-fact=\"rain.laoag.ratio\">{r}</span> times apart. "
                    "The sharpest monsoon split in the set; an annual total hides "
                    "it completely.".format(r=F["laoratio"]))],
                  "Mean rainfall by month, all cities", "rainChart"),
        p.prose(7, "What Reanalysis Is Not",
                "This page is built on a model, and that changes what its numbers "
                "mean.",
                [("It is not a thermometer record",
                  "ERA5 is a physical model of the atmosphere run backwards, "
                  "constrained by whatever observations existed at the time. Its "
                  "1940s values rest on far fewer measurements than its 2020s "
                  "ones, which is part of why the two reanalyses disagree more "
                  "about early decades than recent ones. PAGASA holds the "
                  "Philippine station record and is not reachable from a script "
                  "here."),
                 ("A city is a grid cell",
                  "Roughly 25 km for ERA5 and 10 km for ERA5-Land. That cannot "
                  "separate Manila from the land around it, so nothing here "
                  "measures urban heat island effects, and \"Manila\" means a "
                  "cell centred near it rather than the city."),
                 ("No storms",
                  "Daily rainfall totals do not identify a typhoon, and wind is "
                  "not in this dataset at all. The typhoon page uses IBTrACS "
                  "track data for that, which is a different archive entirely."),
                 ("The trend is a range and stays one",
                  "Reporting the midpoint of two models that differ by a factor "
                  "of {r} would be a false precision. Where this page gives a "
                  "single trend it names the model it came from, and a check fails "
                  "if the two ever converge to within 0.02&nbsp;&deg;C a decade, "
                  "because then this whole framing should be "
                  "revisited.".format(r=F["ratio"]))]),
        p.prose(8, "Method",
                "One fetcher, nine cities, eight CSVs, and a cache.",
                [("Both models are asked explicitly",
                  "The API's default silently resolves to one of them. A page that "
                  "quotes \"the\" temperature without saying which model produced "
                  "it is quoting a coin flip, so era5 and era5_land are named in "
                  "the request and carried through as separate rows."),
                 ("Trends use only the shared years",
                  "ERA5 begins in {f} and ERA5-Land in {sf}. Comparing a "
                  "{f}-{last} slope against a {sf}-{last} one is partly a "
                  "comparison of periods, and the early decades are exactly the "
                  "ones whose inclusion changes the answer. Each model's own "
                  "full-span trend is kept in a separate row labelled with its "
                  "span.".format(f=F["first"], sf=F["shfirst"], last=F["last"])),
                 ("A year needs 360 days to count",
                  "Partial years are excluded from every mean and trend. A missing "
                  "January would otherwise drag a mean down and read as a cold "
                  "year, and a check asserts no annual row falls below the "
                  "threshold."),
                 ("Partial decades are labelled, not hidden",
                  "The 2020s hold {p} years. They appear on the charts because "
                  "leaving them off would hide the warmest data in the record, and "
                  "they carry their year count because plotting five years beside "
                  "ten as though both were decades would be worse."
                  .format(p=F["partial"])),
                 ("The cross-check runs on six cities, not nine",
                  "Open-Meteo's free tier counts an 85-year request as many calls "
                  "and returns 429 well before 27 of them finish. Six cities from "
                  "Luzon to Mindanao establish the disagreement as well as nine "
                  "would; all nine still get the full daily series. The cities "
                  "chosen are named in the fetcher rather than left implicit."),
                 ("Responses are cached on disk",
                  "About 3 MB of JSON per city per model. Cached so that changing "
                  "an aggregate does not re-fetch 85 years from a free API "
                  "eighteen times over, and not committed.")]),
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
                        <li>Two reanalyses of the same atmosphere sit
                        <span data-fact="wx.gap.abs">{gapabs}</span>&nbsp;&deg;C
                        apart on Manila's mean and a factor of
                        <span data-fact="trend.ratio">{ratio}</span> apart on its
                        warming rate, so every trend here is a range and no single
                        absolute temperature is quoted.</li>
                        <li>Warming runs
                        <span data-fact="trend.land.min">{elmin}</span>&ndash;<span data-fact="trend.land.max">{elmax}</span>&nbsp;&deg;C
                        a decade on ERA5-Land and
                        <span data-fact="trend.era5.min">{e5min}</span>&ndash;<span data-fact="trend.era5.max">{e5max}</span>
                        on ERA5, and both agree on direction in all
                        <span data-fact="trend.warming.everywhere">{warmall}</span>
                        cities checked.</li>
                        <li><span data-fact="heat.recent.records">{recent}</span> of
                        <span data-fact="wx.cities">{cities}</span> cities set their
                        hottest day on record since 2020 &mdash; the exception is
                        {oldc}, from
                        <span data-fact="heat.only.old.year">{oldy}</span> &mdash;
                        and
                        <span data-fact="dec.warmest.is.last">{warmlast}</span> of
                        {cities} had their warmest complete decade in the
                        2010s.</li>
                        <li>Days above 35&nbsp;&deg;C rose from
                        <span data-fact="hot.laoag.1950s">{lao50}</span> a year to
                        <span data-fact="hot.laoag.2020s">{lao20}</span> in Laoag
                        and from
                        <span data-fact="hot.manila.1950s">{man50}</span> to
                        <span data-fact="hot.manila.2020s">{man20}</span> in
                        Manila.</li>
                        <li>Rainfall varies far more than temperature:
                        <span data-fact="rain.wettest.mm">{wetmm:,.0f}</span> mm a
                        year in {wet} against
                        <span data-fact="rain.driest.mm">{drymm:,.0f}</span> in
                        {dry}, and Laoag's wettest month is
                        <span data-fact="rain.laoag.ratio">{laoratio}</span> times
                        its driest.</li>
                        <li>All of it is reanalysis on a ~25&nbsp;km grid, not
                        station data. It cannot see a city apart from the land
                        around it.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    MAN = sorted((x for x in mdl if x["city"] == "Manila"),
                 key=lambda x: int(x["year"]))
    myrs = sorted({int(x["year"]) for x in MAN})
    m_e5 = {int(x["year"]): f(x["mean_c"]) for x in MAN if x["model"] == "era5"}
    m_el = {int(x["year"]): f(x["mean_c"]) for x in MAN
            if x["model"] == "era5_land"}
    DECS = sorted({x["decade"] for x in dec})
    ALLC = sorted({x["city"] for x in ann})
    PAL = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#14b8a6",
           "#ec4899", "#64748b", "#a3620b"]

    charts = ['''        // 01 Manila under both reanalyses. They move together and sit a degree
        //    apart, which is the whole argument of the page in one chart.
        new Chart(document.getElementById('modelChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'ERA5 (°C)', data: %s, borderColor: '#ef4444',
                      borderWidth: 2, pointRadius: 0, fill: false },
                    { label: 'ERA5-Land (°C)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { title: { display: true, text: 'Annual mean temperature (°C)' } } }
            }
        });''' % (js(myrs), js([m_e5.get(y) for y in myrs]),
                  js([m_el.get(y) for y in myrs])),

              '''        // 02 warming per decade, both models, over their shared years. Every pair
        //    leans the same way and by roughly the same factor.
        new Chart(document.getElementById('trendChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'ERA5 (°C/decade)', data: %s, backgroundColor: '#ef4444' },
                    { label: 'ERA5-Land (°C/decade)', data: %s, backgroundColor: '#3b82f6' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: '°C per decade, %d-%d' } } }
            }
        });''' % (js(CITIES),
                  js([f(tr(c, "era5")["trend_c_per_decade"]) for c in CITIES]),
                  js([f(tr(c, "era5_land")["trend_c_per_decade"])
                      for c in CITIES]),
                  F["shfirst"], F["last"]),

              '''        // 03 the hottest day in each city's record, coloured by whether it is from
        //    this decade. Eight of nine are.
        new Chart(document.getElementById('recordChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Hottest day on record (°C)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return 'Set ' + %s[c.dataIndex]; } } } },
                scales: { y: { beginAtZero: false,
                               title: { display: true, text: '°C' } } }
            }
        });''' % (js([x["city"] for x in hotrec]),
                  js([f(x["value"]) for x in hotrec]),
                  js(["#ef4444" if x["date"] >= "2020-01-01" else "#64748b"
                      for x in hotrec]),
                  js([x["date"] for x in hotrec])),

              '''        // 04 days over 35 C per year by decade. Log y: Laoag goes from 0.1 to 31 and
        //    a linear axis renders the first forty years as nothing at all.
        new Chart(document.getElementById('hotChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { type: 'logarithmic',
                               title: { display: true, text: 'Days per year over 35°C (log)' } } }
            }
        });''' % (js(DECS),
                  "[" + ", ".join(
                      "{ label: %s, data: %s, borderColor: '%s', borderWidth: 2, "
                      "pointRadius: 3, fill: false, spanGaps: true }"
                      % (js(c),
                         js([(hd(c, d) or None) for d in DECS]), PAL[i % len(PAL)])
                      for i, c in enumerate(ALLC)) + "]"),

              '''        // 05 decadal means for every city. The 2020s point is five years, which the
        //    tooltip states.
        new Chart(document.getElementById('decadeChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { tooltip: { callbacks: { afterBody: function (c) {
                    return c[0].label === '2020s' ? 'five years, not ten' : ''; } } } },
                scales: { y: { title: { display: true, text: 'Mean temperature (°C)' } } }
            }
        });''' % (js(DECS),
                  "[" + ", ".join(
                      "{ label: %s, data: %s, borderColor: '%s', borderWidth: 2, "
                      "pointRadius: 3, fill: false }"
                      % (js(c),
                         js([next((f(x["mean_c"]) for x in dec
                                   if x["city"] == c and x["decade"] == d), None)
                             for d in DECS]), PAL[i % len(PAL)])
                      for i, c in enumerate(ALLC)) + "]"),

              '''        // 06 the shape of the year. Baguio's monsoon peak dwarfs everything, which
        //    is why an annual total is the wrong summary for rainfall here.
        new Chart(document.getElementById('rainChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Mean rainfall (mm/month)' } } }
            }
        });''' % (js([MONTH[m] for m in range(1, 13)]),
                  "[" + ", ".join(
                      "{ label: %s, data: %s, borderColor: '%s', borderWidth: 2, "
                      "pointRadius: 2, fill: false }"
                      % (js(c),
                         js([next((f(x["mean_rainfall_mm"]) for x in mon
                                   if x["city"] == c and int(x["month"]) == m),
                                  None) for m in range(1, 13)]),
                         PAL[i % len(PAL)])
                      for i, c in enumerate(ALLC)) + "]"),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "How Much Warmer? That Depends Which Model You Ask",
        "%s daily ERA5 observations for %d Philippine grid cells, 1940-2024. Two "
        "reanalyses disagree by %s C on Manila's mean and a factor of %s on its "
        "warming rate -- but agree that %d of %d cities set their hottest day since "
        "2020."
        % (format(F["obs"], ","), F["cities"], F["gapabs"], F["ratio"], F["recent"],
           F["cities"]),
        "The warming rate depends on which reanalysis by a factor of %s. Both agree "
        "on the records." % F["ratio"],
        "How Much Warmer? That Depends Which Model You Ask")
    p.faq({
        "How much is the Philippines warming?":
            "Between %s and %s C per decade on ERA5-Land and between %s and %s on "
            "ERA5, across six cities over the 1950-2024 period both reanalyses "
            "cover. Those are reconstructions of the same atmosphere and ERA5 warms "
            "about %s times faster, which is why this is a range rather than a "
            "number. Both agree on direction in every city checked, and both put "
            "the recent decades warmest."
            % (F["elmin"], F["elmax"], F["e5min"], F["e5max"], F["ratio"]),
        "When was the hottest day recorded in the Philippines?":
            "In this nine-city ERA5 dataset the highest daily maximum is %s C in %s "
            "on %s. More telling than any single record: %d of the %d cities set "
            "their hottest day on record in 2020 or later. The only exception is "
            "%s, whose record still stands from %s -- and it is the one city here "
            "at altitude, averaging %s C cooler than Manila."
            % (F["hotv"], F["hotc"], F["hotd"], F["recent"], F["cities"], F["oldc"],
               F["oldy"], F["bagvsman"]),
        "Are hot days becoming more common in the Philippines?":
            "Sharply, on this data. Laoag averaged %s days a year above 35 C in the "
            "1950s and %s in the 2020s; Manila went from %s to %s, about %s times "
            "as many. One caveat matters: a count of days crossing a fixed "
            "threshold depends on absolute temperature, and the two reanalyses sit "
            "%s C apart on that. The direction is robust; treat the magnitude as "
            "indicative rather than exact."
            % (F["lao50"], F["lao20"], F["man50"], F["man20"], F["manratio"],
               F["gapabs"]),
        "Is this Philippine weather data from actual weather stations?":
            "No, and the difference matters. ERA5 is a reanalysis: a physical model "
            "of the atmosphere constrained by whatever observations existed, output "
            "on a grid of roughly 25 km -- 10 km for ERA5-Land. A city here is a "
            "grid cell near it, not a station in it, which also means none of this "
            "can measure urban heat island effects. PAGASA holds the Philippine "
            "station record; pagasa.dost.gov.ph is not reachable from a script "
            "here, so it is named as a gap rather than substituted for.",
        "Where does it rain most in the Philippines?":
            "Of the nine cities here, %s at about %s mm a year, against %s at %s mm "
            "-- a ratio of %s, far wider than any temperature difference across the "
            "archipelago. The timing varies more than the total: Laoag's wettest "
            "month averages %s mm and its driest %s mm, %s times apart, so an "
            "annual figure hides the monsoon entirely."
            % (F["wet"], format(int(F["wetmm"]), ","), F["dry"],
               format(int(F["drymm"]), ","), F["rainratio"], int(F["laowet"]),
               int(F["laodry"]), F["laoratio"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
