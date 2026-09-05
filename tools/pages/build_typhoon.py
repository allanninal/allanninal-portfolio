#!/usr/bin/env python3
"""Regenerate projects/typhoon-analysis.html from data/ph-typhoon CSVs.

    .venv/bin/python tools/pages/build_typhoon.py

The published page reported 23 major typhoons, 43.9 million people affected, 4.2
million houses damaged and 65,870 barangays hit, sourced to NDRRMC/DROMIC. Those
are disaster-response impact figures and none of them traced to anything here.

IBTrACS is the authoritative track archive -- 243,281 observations of 4,105
western Pacific storms since 1884 -- and it carries no impact data whatsoever. So
this page is about where storms go and how strong they get, and it says so.

The governing fact about the archive is that most of it cannot be used for rates.
Intensity is missing for 100% of pre-1945 observations and 43.3% of 1945-69,
because nobody was measuring. Storm counts from 1884 chart the arrival of aircraft
reconnaissance and then satellites, not any change in the weather. Everything here
that is a rate, a trend or a ranking starts at 1980, the threshold is a named
constant, and the earlier data is written out with its own gaps recorded so the
reason is visible rather than asserted.

What that leaves is worth the page. 957 storms entered Philippine waters in the 45
finalised satellite-era seasons -- 21.27 a year, and 66.2% of every storm in the
basin. 80 of them reached category 5. Four share the intensity record at 170 knots:
Haiyan in 2013, Meranti 2016, Goni 2020 and Surigae 2021. And no month of the year
is empty, which is the thing that distinguishes the Philippines from almost
anywhere else.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-typhoon"
PAGE = "projects/typhoon-analysis.html"
MONTH = ["", "January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"]


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    sea = sorted(rows("ph_typhoon_seasons"), key=lambda x: int(x["season"]))
    mon = sorted(rows("ph_typhoon_monthly"), key=lambda x: int(x["month"]))
    inten = sorted(rows("ph_typhoon_intensity"), key=lambda x: int(x["peak_sshs"]))
    strong = sorted(rows("ph_typhoon_strongest"), key=lambda x: int(x["rank"]))
    land = sorted(rows("ph_typhoon_landfall"), key=lambda x: int(x["season"]))
    storms = rows("ph_typhoon_storms")
    cov = {x["property"]: x["value"] for x in rows("ph_typhoon_coverage")}

    ERA = int(f(cov["first season used for rates and trends"]))
    LAST = int(f(cov["last finalised season"]))
    sat = [x for x in sea if x["era"] == "satellite"]
    counts = [int(x["storms_in_box"]) for x in sat]
    c5 = [x for x in inten if x["peak_sshs"] == "5"][0]
    top = strong[0]
    tied = [x for x in strong
            if f(x["peak_wind_kt"]) == f(top["peak_wind_kt"])]
    mpk = max(mon, key=lambda x: int(x["storms"]))
    mqt = min(mon, key=lambda x: int(x["storms"]))

    F = dict(
        obs=int(f(cov["observations in the archive"])),
        archstorms=int(f(cov["storms in the archive"])),
        first=min(int(x["season"]) for x in sea), last=LAST,
        box=int(f(cov["storms entering the box"])),
        pre=int(f(cov["storms before 1945"])),
        prenw=f(cov["observations before 1945 with no wind speed"]),
        midnw=f(cov["observations 1945-1969 with no wind speed"]),
        satnw=f(cov["observations since 1980 with no wind speed"]),
        era=ERA,
        n=sum(1 for x in storms if x["era"] == "satellite"),
        years=len(sat),
        per=r(sum(counts) / len(counts), 2),
        mx=max(counts), mn=min(counts),
        mxy=max(sat, key=lambda x: (int(x["storms_in_box"]),
                                    -int(x["season"])))["season"],
        mny=min(sat, key=lambda x: (int(x["storms_in_box"]),
                                    int(x["season"])))["season"],
        share=r(100.0 * sum(counts)
                / sum(int(x["storms_in_basin"]) for x in sat), 1),
        c5=int(c5["storms"]), c5pct=f(c5["pct_of_storms"]),
        c45=sum(int(x["storms"]) for x in inten if int(x["peak_sshs"]) >= 4),
        c45pct=r(sum(f(x["pct_of_storms"]) for x in inten
                     if int(x["peak_sshs"]) >= 4), 2),
        below=r(sum(f(x["pct_of_storms"]) for x in inten
                    if int(x["peak_sshs"]) < 1), 2),
        peak=int(f(top["peak_wind_kt"])), peakkmh=int(f(top["peak_wind_kmh"])),
        tied=len(tied), tiednames=", ".join(x["name"].title() for x in tied),
        tiedrecent=max(int(x["season"]) for x in tied),
        since2000=sum(1 for x in strong if int(x["season"]) >= 2000),
        top25=len(strong),
        mpk=MONTH[int(mpk["month"])], mpkn=int(mpk["storms"]),
        mpkpct=f(mpk["pct_of_storms"]),
        mqt=MONTH[int(mqt["month"])], mqtn=int(mqt["storms"]),
        julocy=r(sum(f(x["pct_of_storms"]) for x in mon
                     if 7 <= int(x["month"]) <= 10), 2),
        offseason=r(sum(f(x["pct_of_storms"]) for x in mon
                        if int(x["month"]) <= 4), 2),
        lfpct=r(100.0 * sum(int(x["storms_with_landfall_obs"]) for x in land)
                / sum(int(x["storms_in_box"]) for x in land), 1),
        lftot=sum(int(x["storms_with_landfall_obs"]) for x in land),
        lfmax=max(f(x["pct_with_landfall"]) for x in land),
        lfmaxy=max(land, key=lambda x: (f(x["pct_with_landfall"]),
                                        -int(x["season"])))["season"],
        lfmin=min(f(x["pct_with_landfall"]) for x in land),
        lfminy=min(land, key=lambda x: (f(x["pct_with_landfall"]),
                                        int(x["season"])))["season"],
    )
    F["c5per"] = r(F["c5"] / F["years"], 2)

    p = Page(PAGE)
    p.hero('''                <h1>Two Thirds Of Every Pacific Storm Comes Here</h1>
                <p class="{hero_desc}">
                    {n} storms entered Philippine waters across the {years}
                    finalised satellite-era seasons &mdash; {share}% of every
                    storm in the western Pacific, the busiest basin on earth.
                    {c5} of them reached category 5. This is a track archive,
                    so it says nothing about what any of them cost.
                </p>

                <div class="header-actions">
                    <a href="https://www.ncei.noaa.gov/products/international-best-track-archive" target="_blank" class="btn btn-primary">
                        IBTrACS v04r01 (NOAA NCEI)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="par.per.year">{per}</div>
                        <div class="{label}">Storms in Philippine waters per year, {era}&ndash;{last}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="par.share.of.basin">{share}%</div>
                        <div class="{label}">Of all western Pacific storms reach them</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="cat5">{c5}</div>
                        <div class="{label}">Reached category 5, about {c5per} a year</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="peak.wind.kmh">{peakkmh}</div>
                        <div class="{label}">km/h, the record, shared by {tied} storms</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The archive holds <span data-fact="arch.storms">{archstorms:,}</span> western Pacific storms since {first}, and <span data-fact="arch.box">{box:,}</span> of them passed through Philippine waters. But only <span data-fact="par.storms">{n}</span> can be used for any rate: intensity is missing for <span data-fact="arch.pre1945.nowind">{prenw}%</span> of pre-1945 observations, so a storm count from {first} charts the arrival of satellites rather than any change in the weather.</p>
                    <ul class="tldr-list">
                        <li>Across the {years} finalised seasons from {era}, <span data-fact="par.per.year">{per}</span> storms a year entered Philippine waters &mdash; between <span data-fact="par.min">{mn}</span> in {mny} and <span data-fact="par.max">{mx}</span> in {mxy}. That is <span data-fact="par.share.of.basin">{share}%</span> of everything the basin produced.</li>
                        <li><span data-fact="cat5">{c5}</span> reached category 5, <span data-fact="cat5.pct">{c5pct}%</span> of them, about <span data-fact="cat5.per.year">{c5per}</span> a year. But <span data-fact="below.typhoon.pct">{below}%</span> never became a typhoon at all, which is the half of the distribution that does not make the news.</li>
                        <li>Four storms share the intensity record at <span data-fact="peak.wind">{peak}</span> knots &mdash; <span data-fact="peak.wind.kmh">{peakkmh}</span> km/h: {tiednames}. Three of the four are from the last decade, and <span data-fact="top25.since2000">{since2000}</span> of the <span data-fact="top25.n">{top25}</span> most intense are since 2000 &mdash; which is partly real and partly better instruments, and this page does not separate them.</li>
                        <li>{mpk} is the peak month with <span data-fact="month.peak.pct">{mpkpct}%</span> of storms, and July to October carry <span data-fact="season.jul.oct.pct">{julocy}%</span>. But no month is empty: {mqt}, the quietest, still has <span data-fact="month.quiet.n">{mqtn}</span> across {years} years. There is no safe season.</li>
                        <li>IBTrACS carries no deaths, no damage and no people affected. The previous version of this page led with all three; none of them are in this archive, and the page does not estimate them.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Why This Page Starts In 1980",
                  "The archive goes back to {first} and the temptation is to use "
                  "all of it. The intensity column says why that would be wrong: "
                  "before anyone was measuring, there is nothing to measure."
                  .format(**F),
                  [("Before 1945", "{v}%".format(v=F["prenw"]),
                    "arch.pre1945.nowind",
                    "Of observations carry no wind speed &mdash; "
                    "<span data-fact=\"arch.pre1945\">{n:,}</span> storms with no "
                    "intensity of any kind. A check asserts none of them is given "
                    "one.".format(n=F["pre"])),
                   ("1945 to 1969", "{v}%".format(v=F["midnw"]), "arch.mid.nowind",
                    "Aircraft reconnaissance. Better, and still missing more than "
                    "two observations in five."),
                   ("Since {e}".format(e=F["era"]), "{v}%".format(v=F["satnw"]),
                    "arch.sat.nowind",
                    "Satellite era. Every rate, trend and ranking on this page "
                    "uses only these <span data-fact=\"par.storms\">{n}</span> "
                    "storms, out of "
                    "<span data-fact=\"arch.box\">{b:,}</span> that reached these "
                    "waters in total.".format(n=F["n"], b=F["box"]))],
                  "Storms recorded per season, and the share of observations with "
                  "no wind speed", "qualityChart"),
        p.section(2, "Twenty-One A Year, And Two Thirds Of The Basin",
                  "Storms entering the box each season since {era}. The count "
                  "moves around a lot &mdash; between {mn} and {mx} &mdash; and "
                  "the page draws no trend line through it, because {years} "
                  "seasons of a noisy count is not enough to establish one."
                  .format(**F),
                  [("Per season", "{v}".format(v=F["per"]), "par.per.year",
                    "Mean across the {y} finalised seasons from {e}."
                    .format(y=F["years"], e=F["era"])),
                   ("Range", "{a} to {b}".format(a=F["mn"], b=F["mx"]),
                    "par.min",
                    "<span data-fact=\"par.min.year\">{ay}</span> was the quietest "
                    "and <span data-fact=\"par.max.year\">{by}</span> the busiest, "
                    "at <span data-fact=\"par.max\">{b}</span>."
                    .format(ay=F["mny"], by=F["mxy"], b=F["mx"])),
                   ("Share of the basin", "{v}%".format(v=F["share"]),
                    "par.share.of.basin",
                    "Of every storm the western Pacific produced. This is the "
                    "single most important number about Philippine geography.")],
                  "Storms entering Philippine waters per season, %d onward"
                  % F["era"], "seasonChart"),
        p.section(3, "Most Of Them Are Not Typhoons",
                  "Each storm counted once, at its own peak category, so a slow "
                  "storm does not outweigh a fast one. The distribution has two "
                  "humps and the lower one is bigger.",
                  [("Never a typhoon", "{v}%".format(v=F["below"]),
                    "below.typhoon.pct",
                    "Peaked below category 1: depressions and tropical storms. "
                    "They still flood."),
                   ("Category 4 or 5", "{v}%".format(v=F["c45pct"]),
                    "cat45.pct",
                    "<span data-fact=\"cat45\">{n}</span> storms. The tail that "
                    "does the damage.".format(n=F["c45"])),
                   ("Category 5", "{v}".format(v=F["c5"]), "cat5",
                    "<span data-fact=\"cat5.pct\">{p}%</span> of the total, about "
                    "<span data-fact=\"cat5.per.year\">{r}</span> a year across "
                    "the period.".format(p=F["c5pct"], r=F["c5per"]))],
                  "Storms by peak Saffir-Simpson category, %d onward" % F["era"],
                  "intensityChart"),
        p.section(4, "The Record Is Shared By Four",
                  "The most intense storms to enter these waters since {era}, by "
                  "peak one-minute sustained wind. Note what this ranking is "
                  "sensitive to: satellite intensity estimation improved "
                  "substantially over the period, so a list weighted toward "
                  "recent decades is partly a real signal and partly a measurement "
                  "one.".format(**F),
                  [("The record", "{v} kt".format(v=F["peak"]), "peak.wind",
                    "<span data-fact=\"peak.wind.kmh\">{k}</span> km/h, shared by "
                    "<span data-fact=\"peak.tied\">{n}</span> storms: {names}."
                    .format(k=F["peakkmh"], n=F["tied"], names=F["tiednames"])),
                   ("Three of the four", "since 2013", None,
                    "The record-holders cluster in the last decade, the most "
                    "recent in {y}. Whether that is intensification or better "
                    "measurement is not something this archive can settle."
                    .format(y=F["tiedrecent"])),
                   ("Of the top {n}".format(n=F["top25"]),
                    "{v} since 2000".format(v=F["since2000"]),
                    "top25.since2000",
                    "Same caveat, more sharply. The Dvorak technique for "
                    "estimating intensity from satellite imagery was revised "
                    "repeatedly across this period.")],
                  "Peak sustained wind, the %d most intense storms since %d"
                  % (F["top25"], F["era"]), "strongestChart"),
        p.section(5, "No Safe Month",
                  "Storms by calendar month across the whole satellite era. Most "
                  "tropical basins have a closed season. This one does not, and "
                  "a check asserts all twelve months are present so a quiet month "
                  "cannot silently drop off the chart.",
                  [(F["mpk"], "{v}%".format(v=F["mpkpct"]), "month.peak.pct",
                    "The peak month, with "
                    "<span data-fact=\"month.peak.n\">{n}</span> storms across "
                    "{y} years.".format(n=F["mpkn"], y=F["years"])),
                   ("July to October", "{v}%".format(v=F["julocy"]),
                    "season.jul.oct.pct",
                    "Four months carrying nearly two thirds of the year."),
                   ("January to April", "{v}%".format(v=F["offseason"]),
                    "season.offseason.pct",
                    "The quiet quarter, and still not zero. {q} is the quietest "
                    "month of all with "
                    "<span data-fact=\"month.quiet.n\">{n}</span> storms in {y} "
                    "years.".format(q=F["mqt"], n=F["mqtn"], y=F["years"]))],
                  "Storms by calendar month, %d onward" % F["era"], "monthChart"),
        p.section(6, "How Many Reach Land",
                  "Share of storms in the box each season that record a landfall "
                  "observation. This is the weakest measure on the page and the "
                  "reason is worth stating: IBTrACS gives distance to the nearest "
                  "land, not which country's land, so a storm counted here may "
                  "have made landfall on Taiwan or Vietnam.",
                  [("Overall", "{v}%".format(v=F["lfpct"]), "landfall.pct",
                    "<span data-fact=\"landfall.total\">{n}</span> of the storms "
                    "in these waters record a landfall.".format(n=F["lftot"])),
                   ("Worst season", "{v}%".format(v=F["lfmax"]),
                    "landfall.max.pct",
                    "In <span data-fact=\"landfall.max.year\">{y}</span>."
                    .format(y=F["lfmaxy"])),
                   ("Quietest", "{v}%".format(v=F["lfmin"]), "landfall.min.pct",
                    "In <span data-fact=\"landfall.min.year\">{y}</span>. The "
                    "year-to-year swing is larger than any trend in it."
                    .format(y=F["lfminy"]))],
                  "Share of storms recording a landfall, by season",
                  "landfallChart"),
        p.prose(7, "What This Archive Does Not Contain",
                "The page this replaced was built on impact figures. IBTrACS has "
                "none, and that gap is the most important thing to be clear about.",
                [("No deaths, damage or people affected",
                  "Not one column. The previous version of this page led with 43.9 "
                  "million people affected and 4.2 million houses damaged, sourced "
                  "to NDRRMC and DROMIC. Those are real organisations publishing "
                  "real reports, and this analysis does not read them &mdash; so "
                  "the figures are gone rather than restated. A check asserts the "
                  "impact count stays at zero."),
                 ("The box is not the PAR",
                  "5-25N, 115-135E is the bounding rectangle of the Philippine "
                  "Area of Responsibility, which is a polygon. Counts here "
                  "slightly exceed true PAR entries. The rectangle is used because "
                  "it is reproducible from two lines of SQL; the difference is "
                  "stated rather than hidden."),
                 ("Landfall is not attributed to a country",
                  "The archive records distance to the nearest land. A storm with "
                  "a landfall observation inside the box may have come ashore in "
                  "Taiwan, Vietnam or southern China. Section 6 is a share of "
                  "storms recording any landfall, not a count of Philippine "
                  "landfalls, and it says so on the page rather than only here."),
                 ("International names, not local ones",
                  "PAGASA assigns its own names inside the PAR, which is why the "
                  "2013 storm is Yolanda in the Philippines and Haiyan everywhere "
                  "else. IBTrACS carries the international name and this page uses "
                  "it throughout."),
                 ("No trend is claimed",
                  "{y} seasons of a count that swings between {mn} and {mx} does "
                  "not establish a direction, and the intensity ranking is "
                  "confounded by measurement improvement. The page reports the "
                  "distribution and declines the trend."
                  .format(y=F["years"], mn=F["mn"], mx=F["mx"]))]),
        p.prose(8, "Method",
                "One fetcher over a 109 MB archive, with the interesting decisions "
                "in the filtering.",
                [("Only finalised tracks are read",
                  "TRACK_TYPE is filtered to 'main', which drops spur and "
                  "provisional duplicates of the same storm. It also excludes the "
                  "current season, whose tracks are still provisional, so the "
                  "latest season present is finalised by construction &mdash; and "
                  "that is how the last usable year is derived rather than written "
                  "into the script, where it would go stale."),
                 ("The units row is dropped by parsing, not by counting",
                  "IBTrACS puts column names on line 1 and units on line 2. "
                  "Skipping two lines loses the header; the second row is dropped "
                  "instead by requiring SEASON to parse as an integer, which is "
                  "true of every real row and of no units row."),
                 ("Each storm is counted once, at its own peak",
                  "The intensity distribution groups by storm id and takes the "
                  "maximum category. Counting observations instead would weight a "
                  "slow-moving storm above a fast one, and a check asserts the "
                  "distribution sums to the storm count rather than the "
                  "observation count."),
                 ("Category and wind speed are checked against each other",
                  "Category 5 begins at 137 knots. A check fails on any storm "
                  "flagged 5 below that, or above it and not flagged 5, because "
                  "two columns coming apart produces a ranking that still looks "
                  "plausible."),
                 ("The satellite threshold is a named constant",
                  "ERA = {e}, used for every rate and stated on the page. It is a "
                  "judgement, and the checks record what it is a judgement about: "
                  "one asserts that seasons before 1940 carry essentially no "
                  "intensity data, so if that ever stopped being true the "
                  "threshold should be revisited.".format(e=F["era"])),
                 ("The archive is cached, not re-downloaded",
                  "109 MB that NOAA revises far less often than this page is "
                  "rebuilt. It is not committed.")]),
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
                        <li><span data-fact="par.share.of.basin">{share}%</span> of
                        every western Pacific storm enters Philippine waters &mdash;
                        <span data-fact="par.per.year">{per}</span> a year across
                        the {years} finalised seasons since {era}, ranging from
                        <span data-fact="par.min">{mn}</span> to
                        <span data-fact="par.max">{mx}</span>.</li>
                        <li><span data-fact="cat5">{c5}</span> reached category 5,
                        <span data-fact="cat5.pct">{c5pct}%</span> of the total
                        &mdash; but
                        <span data-fact="below.typhoon.pct">{below}%</span> never
                        became a typhoon at all.</li>
                        <li>The record is <span data-fact="peak.wind">{peak}</span>
                        knots,
                        <span data-fact="peak.wind.kmh">{peakkmh}</span> km/h,
                        shared by <span data-fact="peak.tied">{tied}</span> storms:
                        {tiednames}.
                        <span data-fact="top25.since2000">{since2000}</span> of the
                        <span data-fact="top25.n">{top25}</span> most intense are
                        since 2000, which is partly instruments and partly
                        weather.</li>
                        <li>{mpk} peaks at
                        <span data-fact="month.peak.pct">{mpkpct}%</span> and July
                        to October carry
                        <span data-fact="season.jul.oct.pct">{julocy}%</span>, but
                        no month is empty &mdash; {mqt} still has
                        <span data-fact="month.quiet.n">{mqtn}</span>.</li>
                        <li>Only <span data-fact="par.storms">{n}</span> of the
                        <span data-fact="arch.box">{box:,}</span> storms that have
                        reached these waters can be used for any rate, because
                        <span data-fact="arch.pre1945.nowind">{prenw}%</span> of
                        pre-1945 observations carry no intensity at all.</li>
                        <li>This is a track archive. It contains no deaths, no
                        damage and no people affected, and this page estimates
                        none.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    ALL = sea
    SAT = sat
    TOPN = strong[:15]

    charts = ['''        // 01 the reason the page starts in 1980: storm counts rise as the share of
        //    observations with no wind speed falls. Two axes, one story.
        new Chart(document.getElementById('qualityChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Storms recorded in the basin', data: %s,
                      borderColor: '#3b82f6', borderWidth: 2, pointRadius: 0,
                      fill: false, yAxisID: 'y' },
                    { label: 'Observations with no wind speed (%%)', data: %s,
                      borderColor: '#ef4444', borderWidth: 2, pointRadius: 0,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Storms' } },
                          y1: { position: 'right', min: 0, max: 100,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: '%% with no wind speed' } } }
            }
        });''' % (js([int(x["season"]) for x in ALL]),
                  js([int(x["storms_in_basin"]) for x in ALL]),
                  js([f(x["pct_obs_without_wind"]) for x in ALL])),

              '''        // 02 storms entering the box per season, satellite era only. No trend line:
        //    45 noisy seasons do not establish one, and drawing it would claim more
        //    than the data supports.
        new Chart(document.getElementById('seasonChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Storms entering Philippine waters', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' in the basin that year'; } } } },
                scales: { x: { ticks: { maxTicksLimit: 16 } },
                          y: { beginAtZero: true,
                               title: { display: true, text: 'Storms' } } }
            }
        });''' % (js([int(x["season"]) for x in SAT]),
                  js([int(x["storms_in_box"]) for x in SAT]),
                  js(["#ef4444" if int(x["storms_in_box"]) >= 26
                      else "#22c55e" if int(x["storms_in_box"]) <= 15
                      else "#3b82f6" for x in SAT]),
                  js([int(x["storms_in_basin"]) for x in SAT])),

              '''        // 03 peak category, one count per storm. Sub-typhoon categories in grey so
        //    the two humps are visible.
        new Chart(document.getElementById('intensityChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Storms', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of storms'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Storms reaching this peak' } } }
            }
        });''' % (js([x["peak_category"] for x in inten]),
                  js([int(x["storms"]) for x in inten]),
                  js(["#ef4444" if int(x["peak_sshs"]) == 5
                      else "#f59e0b" if int(x["peak_sshs"]) >= 1
                      else "#94a3b8" for x in inten]),
                  js([f(x["pct_of_storms"]) for x in inten])),

              '''        // 04 the strongest, with the season on the tooltip so the clustering in
        //    recent decades is visible without being asserted as a trend.
        new Chart(document.getElementById('strongestChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Peak sustained wind (kt)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' km/h'; } } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Peak one-minute sustained wind (knots)' } } }
            }
        });''' % (js(["%s (%s)" % (x["name"].title(), x["season"]) for x in TOPN]),
                  js([f(x["peak_wind_kt"]) for x in TOPN]),
                  js(["#ef4444" if int(x["season"]) >= 2010 else "#3b82f6"
                      for x in TOPN]),
                  js([int(x["peak_wind_kmh"]) for x in TOPN])),

              '''        // 05 the calendar. Nothing is zero, which is the point.
        new Chart(document.getElementById('monthChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Storms', data: %s, backgroundColor: %s,
                             borderRadius: 6 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of the year'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Storms, %d-%d' } } }
            }
        });''' % (js([MONTH[int(x["month"])][:3] for x in mon]),
                  js([int(x["storms"]) for x in mon]),
                  js(["#ef4444" if 7 <= int(x["month"]) <= 10 else "#3b82f6"
                      for x in mon]),
                  js([f(x["pct_of_storms"]) for x in mon]),
                  F["era"], F["last"]),

              '''        // 06 the share recording a landfall. Noisy, and labelled as the weakest
        //    measure here because the archive does not say whose land.
        new Chart(document.getElementById('landfallChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Share recording a landfall (%%)', data: %s,
                             borderColor: '#8b5cf6',
                             backgroundColor: 'rgba(139,92,246,0.15)',
                             borderWidth: 3, pointRadius: 3, fill: true }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' of ' + %s[c.dataIndex] + ' storms'; } } } },
                scales: { x: { ticks: { maxTicksLimit: 16 } },
                          y: { min: 0, max: 100,
                               title: { display: true, text: '%% of storms in the box' } } }
            }
        });''' % (js([int(x["season"]) for x in land]),
                  js([f(x["pct_with_landfall"]) for x in land]),
                  js([int(x["storms_with_landfall_obs"]) for x in land]),
                  js([int(x["storms_in_box"]) for x in land])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "Two Thirds Of Every Pacific Storm Comes Here",
        "IBTrACS track data for Philippine waters: %s storms across %d "
        "satellite-era seasons, %s%% of the whole western Pacific basin, %d of them "
        "category 5 -- and no month of the year without one."
        % (F["n"], F["years"], F["share"], F["c5"]),
        "%s%% of western Pacific storms enter Philippine waters. And no month is "
        "empty." % F["share"],
        "Two Thirds Of Every Pacific Storm Comes Here")
    p.faq({
        "How many typhoons hit the Philippines each year?":
            "%s storms entered Philippine waters per year on average across the %d "
            "finalised satellite-era seasons from %d, ranging from %d to %d. But "
            "%s%% of them never reached typhoon strength at all -- they peaked as "
            "tropical depressions or tropical storms. %d reached category 5 over the "
            "whole period, about %s a year."
            % (F["per"], F["years"], F["era"], F["mn"], F["mx"], F["below"],
               F["c5"], F["c5per"]),
        "What was the strongest typhoon to hit the Philippines?":
            "Four storms share the record at %d knots -- %d km/h of one-minute "
            "sustained wind: %s. Haiyan, known in the Philippines as Yolanda, is "
            "the 2013 one. Three of the four are from the last decade, and %d of "
            "the %d most intense storms since %d are from this century -- though "
            "satellite intensity estimation improved substantially over the period, "
            "so that ranking mixes a real signal with a measurement one."
            % (F["peak"], F["peakkmh"], F["tiednames"], F["since2000"], F["top25"],
               F["era"]),
        "When is typhoon season in the Philippines?":
            "%s is the peak month with %s%% of storms, and July through October "
            "carry %s%% of the year between them. But there is no closed season: "
            "January to April still account for %s%%, and %s -- the quietest month "
            "of all -- recorded %d storms across %d years. Every month of the "
            "Philippine calendar has had storms in it."
            % (F["mpk"], F["mpkpct"], F["julocy"], F["offseason"], F["mqt"],
               F["mqtn"], F["years"]),
        "Why does the Philippines get so many typhoons?":
            "Position. %s%% of every storm the western Pacific produces enters "
            "Philippine waters -- and the western Pacific is the most active "
            "tropical cyclone basin on earth. The archipelago sits directly across "
            "the track that storms forming east of it tend to follow."
            % F["share"],
        "How many people have Philippine typhoons killed or affected?":
            "This analysis cannot say, and it is important to be clear about why. "
            "IBTrACS is a track archive: it records where storms went and how "
            "strong they were, and carries no deaths, damage or people-affected "
            "figures at all. NDRRMC and DROMIC publish that data in situational "
            "reports; this page does not read them, so it states no impact figures "
            "rather than repeating unsourced ones.",
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
