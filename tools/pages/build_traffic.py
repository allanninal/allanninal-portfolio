#!/usr/bin/env python3
"""Regenerate projects/traffic-analysis.html from data/ph-traffic CSVs.

    .venv/bin/python tools/pages/build_traffic.py

The published page reported 17,312 incidents, 11,781 vehicular accidents, and
"15 Cities/Areas". The first is right. The second matches no count in the file --
the exact string VEHICULAR ACCIDENT appears 11,775 times and the family that
groups its 26 spellings has 11,818, so 11,781 is between them and equal to
neither, which is what happens when free text is counted as though it were a code
list. The third is the interesting one: the City column really does hold 15
distinct strings, but two are the same city. "Parañaque" appears both correctly
and as "ParaÃ±aque" -- its UTF-8 bytes read as Latin-1 -- so counting distinct
strings counted it twice. There are 14 cities, out of Metro Manila's 17.

Opening the file also turns up 55 rows geocoded to exactly 0,0 (the Gulf of
Guinea), 138 unparseable times including "22:55 PM", 146 days inside the span
with no report at all, two entire months with no rows, and Quezon City holding
50.4% of everything. So the page is now explicit that this measures MMDA's
Twitter output rather than Metro Manila's roads, and carries WHO national road
death rates as the counterweight.

What the tweets do carry that no annual series does is 15 March 2020. Metro
Manila entered enhanced community quarantine that day, and the file records
28.24 incidents per reporting day before, 3.12 during, and 10.74 after -- still
62% below pre-lockdown when the data ends in December.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-traffic"
PAGE = "projects/traffic-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    inc_cov = {x["property"]: x["value"] for x in rows("ph_traffic_coverage")}
    city = [x for x in rows("ph_traffic_by_city") if x["city"] != "(no city given)"]
    typ = rows("ph_traffic_by_type")
    hour = rows("ph_traffic_hourly")
    dow = rows("ph_traffic_dow")
    mon = rows("ph_traffic_monthly")
    ecq = rows("ph_traffic_ecq")
    loc = rows("ph_traffic_locations")
    dth = rows("ph_traffic_deaths")

    E = {x["period"]: x for x in ecq}
    ly = max(int(x["year"]) for x in dth)
    latest = sorted((x for x in dth if int(x["year"]) == ly),
                    key=lambda x: f(x["deaths_per_100k"]))
    ph = [x for x in latest if x["country"] == "Philippines"][0]
    ph00 = [x for x in dth
            if x["country"] == "Philippines" and x["year"] == "2000"][0]
    rising = [c for c in {x["country"] for x in dth}
              if f([y for y in dth if y["country"] == c
                    and int(y["year"]) == ly][0]["deaths_per_100k"])
              > f([y for y in dth if y["country"] == c
                   and y["year"] == "2000"][0]["deaths_per_100k"])]

    hpk = max(hour, key=lambda x: int(x["incidents"]))
    hqt = min(hour, key=lambda x: int(x["incidents"]))
    h13 = [x for x in hour if x["hour"] == "13"][0]
    dbusy = max(dow, key=lambda x: f(x["incidents_per_reporting_day"]))
    dquiet = min(dow, key=lambda x: f(x["incidents_per_reporting_day"]))
    mbusy = max(mon, key=lambda x: int(x["incidents"]))
    edsa = sum(1 for x in rows("ph_traffic_incidents")
               if x["location"].startswith("EDSA"))
    located = sum(1 for x in rows("ph_traffic_incidents") if x["location"])

    F = dict(
        n=int(inc_cov["rows in file"]),
        first=inc_cov["first date"], last=inc_cov["last date"],
        span=int(inc_cov["calendar days in span"]),
        days=int(inc_cov["days with at least one report"]),
        cities=len(city), missing=17 - len(city),
        locations=len({x["location"] for x in rows("ph_traffic_incidents")
                       if x["location"]}),
        topcity=city[0]["city"], topn=int(city[0]["incidents"]),
        toppct=f(city[0]["pct_of_all"]),
        top4=r(sum(f(x["pct_of_all"]) for x in city[:4]), 2),
        botcity=city[-1]["city"], botn=int(city[-1]["incidents"]),
        moji=int(inc_cov["city name double-encoded"]),
        null0=int(inc_cov["coordinates at exactly 0,0"]),
        nocity=int(inc_cov["city missing"]),
        notype=int(inc_cov["incident type missing"]),
        tmiss=int(inc_cov["time missing"]),
        tbad=int(inc_cov["time unparseable"]),
        mappable=int(inc_cov["incidents usable on a map"]),
        timed=int(inc_cov["incidents with a usable time"]),
        blankm=sum(1 for x in mon if x["incidents"] == "0"),
        hpk=int(hpk["hour"]), hpkn=int(hpk["incidents"]),
        hpkpct=f(hpk["pct_of_timed"]),
        hqt=int(hqt["hour"]), hqtn=int(hqt["incidents"]),
        h13=int(h13["incidents"]),
        morning=r(sum(f(x["pct_of_timed"]) for x in hour
                      if 6 <= int(x["hour"]) <= 9), 2),
        evening=r(sum(f(x["pct_of_timed"]) for x in hour
                      if 16 <= int(x["hour"]) <= 19), 2),
        dbusy=dbusy["day_of_week"], dbusyr=f(dbusy["incidents_per_reporting_day"]),
        dquiet=dquiet["day_of_week"],
        dquietr=f(dquiet["incidents_per_reporting_day"]),
        before=f(E["before ECQ"]["incidents_per_reporting_day"]),
        during=f(E["ECQ and MECQ"]["incidents_per_reporting_day"]),
        after=f(E["after MECQ"]["incidents_per_reporting_day"]),
        ecqn=int(E["ECQ and MECQ"]["incidents"]),
        feb=int([x for x in mon if x["month"] == "2020-02"][0]["incidents"]),
        apr=int([x for x in mon if x["month"] == "2020-04"][0]["incidents"]),
        mbusy=mbusy["month"], mbusyn=int(mbusy["incidents"]),
        ttop=typ[0]["type_family"], ttopn=int(typ[0]["incidents"]),
        ttoppct=f(typ[0]["pct_of_all"]),
        ttopstr=int(typ[0]["distinct_raw_strings"]),
        stalled=int([x for x in typ if x["type_family"] == "stalled vehicle"][0]["incidents"]),
        stalledpct=f([x for x in typ if x["type_family"] == "stalled vehicle"][0]["pct_of_all"]),
        stalledstr=int([x for x in typ if x["type_family"] == "stalled vehicle"][0]["distinct_raw_strings"]),
        families=len(typ),
        strings=len({x["incident_type"] for x in rows("ph_traffic_incidents")
                     if x["incident_type"]}),
        ltop=loc[0]["location"], ltopn=int(loc[0]["incidents"]),
        ltopcity=loc[0]["city"],
        edsan=edsa, edsapct=r(100.0 * edsa / located, 2),
        rd=f(ph["deaths_per_100k"]), ry=ly, rd00=f(ph00["deaths_per_100k"]),
        rrank=1 + sum(1 for x in latest
                      if f(x["deaths_per_100k"]) < f(ph["deaths_per_100k"])),
        rn=len(latest), rworst=latest[-1]["country"],
        rworstv=f(latest[-1]["deaths_per_100k"]),
        rrising=len(rising),
        rother=", ".join(sorted(c for c in rising if c != "Philippines")),
    )
    F["silent"] = F["span"] - F["days"]
    F["tbadtot"] = F["tmiss"] + F["tbad"]
    F["drop"] = r(100.0 * (1 - F["during"] / F["before"]), 1)
    F["recovery"] = r(100.0 * (1 - F["after"] / F["before"]), 1)
    F["h13pct"] = r(100.0 * F["h13"] / F["hpkn"], 1)
    F["dowratio"] = r(100.0 * F["dquietr"] / F["dbusyr"], 1)
    F["banddiff"] = r(F["morning"] - F["evening"], 2)
    F["rdchange"] = r(100.0 * (F["rd"] / F["rd00"] - 1), 1)

    p = Page(PAGE)
    p.hero('''                <h1>17,312 Tweets About Traffic, And What They Are Not</h1>
                <p class="{hero_desc}">
                    Every incident MMDA posted between {first} and {last}. Half of
                    them are in one city and {silent} days in the span have no
                    report at all &mdash; so this measures a Twitter account, not
                    a road network. What it does capture is 15 March 2020, when
                    the daily rate fell from {before} to {during}.
                </p>

                <div class="header-actions">
                    <a href="https://www.kaggle.com/datasets/esparko/mmda-traffic-incident-data" target="_blank" class="btn btn-primary">
                        MMDA incident data (Kaggle)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="mmda.n">{n:,}</div>
                        <div class="{label}">Incident reports, {first} to {last}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="mmda.top.city.pct">{toppct}%</div>
                        <div class="{label}">Of them in {topcity} alone</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="ecq.drop">{drop}%</div>
                        <div class="{label}">Fall in the daily rate under lockdown</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="road.ph">{rd}</div>
                        <div class="{label}">National road deaths per 100,000, {ry}</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">This is a record of what MMDA tweeted, and the distribution proves it: <span data-fact="mmda.top.city.pct">{toppct}%</span> of all {n:,} incidents are in {topcity}, <span data-fact="mmda.top4.pct">{top4}%</span> are in four cities, and {botcity} has <span data-fact="mmda.bottom.city.n">{botn}</span> in two and a half years.</p>
                    <ul class="tldr-list">
                        <li>The previous version of this page reported &ldquo;15 Cities/Areas&rdquo;. The column holds 15 distinct strings but two are the same city: &ldquo;Parañaque&rdquo; also appears as &ldquo;ParaÃ±aque&rdquo; in <span data-fact="bad.mojibake">{moji}</span> rows, its UTF-8 bytes read as Latin-1. There are <span data-fact="mmda.cities">{cities}</span> cities, and Metro Manila has 17 &mdash; <span data-fact="mmda.missing.lgus">{missing}</span> never appear.</li>
                        <li><span data-fact="bad.nullisland">{null0}</span> rows are geocoded to exactly 0,0, which is in the Gulf of Guinea. <span data-fact="bad.time.total">{tbadtot}</span> have a time that does not parse, including &ldquo;22:55 PM&rdquo;. <span data-fact="mmda.blank.months">{blankm}</span> months contain no rows at all.</li>
                        <li>The lockdown is the cleanest signal in the file: <span data-fact="ecq.before">{before}</span> incidents per reporting day before 15 March 2020, <span data-fact="ecq.during">{during}</span> during ECQ, and <span data-fact="ecq.after">{after}</span> afterwards &mdash; still <span data-fact="ecq.recovery">{recovery}%</span> below where it started when the data ends.</li>
                        <li>The morning peak is worse than the evening one: <span data-fact="band.morning">{morning}%</span> of timed incidents fall in 06:00&ndash;09:59 against <span data-fact="band.evening">{evening}%</span> in 16:00&ndash;19:59. The sharpest trough is 1pm, at <span data-fact="hour.lunch">{h13}</span> against <span data-fact="hour.peak.n">{hpkn:,}</span> at 7am.</li>
                        <li>Nationally, road deaths run at <span data-fact="road.ph">{rd}</span> per 100,000 &mdash; <span data-fact="road.rank">{rrank}</span>rd lowest of <span data-fact="road.n">{rn}</span> in ASEAN. But it is up <span data-fact="road.ph.change">{rdchange}%</span> since 2000, and only <span data-fact="road.rising">{rrising}</span> of the six moved that way.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Half The File Is One City",
                  "Incidents by city, after repairing the encoding. This is not a "
                  "ranking of dangerous places &mdash; it is a ranking of which "
                  "MMDA units post to Twitter, and it is the single most important "
                  "thing to know before reading anything else here.",
                  [(F["topcity"], "{v}%".format(v=F["toppct"]), "mmda.top.city.pct",
                    "{n:,} of {t:,} incidents. Four cities carry {f}% between them."
                    .format(n=F["topn"], t=F["n"], f=F["top4"])),
                   ("Cities present", "{v} of 17".format(v=F["cities"]),
                    "mmda.cities",
                    "Metro Manila has 17 local government units; {m} never appear "
                    "in the file. The published figure of 15 counted Parañaque "
                    "twice.".format(m=F["missing"])),
                   (F["botcity"], "{v}".format(v=F["botn"]),
                    "mmda.bottom.city.n",
                    "Incidents in two and a half years. Not a safe city &mdash; an "
                    "unreported one.")],
                  "Incidents by city, share of the whole file", "cityChart"),
        p.section(2, "Fifteen March 2020",
                  "Metro Manila entered enhanced community quarantine on 15 March "
                  "2020 and stayed under ECQ or MECQ until 31 May. Rates are per "
                  "reporting day, not per calendar day, because the account goes "
                  "quiet for stretches and dividing by calendar days would blame "
                  "the roads for a silent feed.",
                  [("Before", "{v}/day".format(v=F["before"]), "ecq.before",
                    "{a} to 14 March 2020.".format(a=F["first"])),
                   ("Under ECQ and MECQ", "{v}/day".format(v=F["during"]),
                    "ecq.during",
                    "A fall of {d}%. February had {f} incidents; April had {a}."
                    .format(d=F["drop"], f=F["feb"], a=F["apr"])),
                   ("After", "{v}/day".format(v=F["after"]), "ecq.after",
                    "Through to {l} &mdash; still {r}% below the pre-lockdown "
                    "rate seven months later.".format(l=F["last"],
                                                      r=F["recovery"]))],
                  "Incidents per month, with months that have no rows marked",
                  "monthChart"),
        p.section(3, "The Morning Is Worse Than The Evening",
                  "Incidents by hour, across the {t:,} rows with a time that "
                  "parses. Two things stand out: the morning peak is larger than "
                  "the evening one, and 1pm is a deeper trough than any hour "
                  "either side of it.".format(t=F["timed"]),
                  [("Peak hour", "{h}:00".format(h=F["hpk"]), "hour.peak",
                    '<span data-fact="hour.peak.n">{n:,}</span> incidents, '
                    '<span data-fact="hour.peak.pct">{p}%</span> of all timed '
                    'reports.'.format(n=F["hpkn"], p=F["hpkpct"])),
                   ("Morning against evening",
                    "{a}% vs {b}%".format(a=F["morning"], b=F["evening"]),
                    "band.morning",
                    "06:00&ndash;09:59 against 16:00&ndash;19:59, a gap of "
                    "<span data-fact=\"band.diff\">{d}</span> points."
                    .format(d=F["banddiff"])),
                   ("The 1pm trough", "{v}".format(v=F["h13"]), "hour.lunch",
                    "Against {n:,} at the {h}am peak &mdash; "
                    "<span data-fact=\"hour.lunch.vs.peak\">{p}%</span> of it. The "
                    "quietest hour is {q}:00 with {qn}."
                    .format(n=F["hpkn"], h=F["hpk"], p=F["h13pct"], q=F["hqt"],
                            qn=F["hqtn"]))],
                  "Incidents by hour of day, share of timed reports", "hourChart"),
        p.section(4, "And Sunday Is Half A Tuesday",
                  "Incidents per reporting day by weekday. Dividing by reporting "
                  "days rather than totals matters here: Sunday has fewer "
                  "reporting days as well as fewer incidents, and a raw total "
                  "would confuse the two.",
                  [(F["dbusy"], "{v}/day".format(v=F["dbusyr"]),
                    "dow.busiest.rate", "The busiest weekday."),
                   (F["dquiet"], "{v}/day".format(v=F["dquietr"]),
                    "dow.quietest.rate",
                    "<span data-fact=\"dow.ratio\">{p}%</span> of {b}. The "
                    "weekday-to-weekend difference is the clearest ordinary "
                    "pattern in the file.".format(p=F["dowratio"],
                                                  b=F["dbusy"])),
                   ("Silent days", "{v}".format(v=F["silent"]),
                    "mmda.silent.days",
                    "Days inside the {s}-day span with no report at all. Metro "
                    "Manila did not have {v} incident-free days."
                    .format(s=F["span"], v=F["silent"]))],
                  "Incidents per reporting day, by weekday", "dowChart"),
        p.section(5, "What Counts As An Incident",
                  "The type column is free text, not a code list: {st} distinct "
                  "strings across {n:,} rows, including at least five misspellings "
                  "of &ldquo;vehicular&rdquo;. Grouping by substring rather than by "
                  "exact match is why the family totals differ from the published "
                  "figure of 11,781, which matched neither."
                  .format(st=F["strings"], n=F["n"]),
                  [("Vehicular accidents", "{v}%".format(v=F["ttoppct"]),
                    "type.top.pct",
                    "{n:,} incidents across "
                    "<span data-fact=\"type.top.strings\">{s}</span> distinct "
                    "spellings.".format(n=F["ttopn"], s=F["ttopstr"])),
                   ("Stalled vehicles", "{v}%".format(v=F["stalledpct"]),
                    "type.stalled.pct",
                    "{n:,} incidents across "
                    "<span data-fact=\"type.stalled.strings\">{s}</span> spellings "
                    "&mdash; mostly &ldquo;STALLED &lt;vehicle&gt; DUE TO "
                    "MECHANICAL PROBLEM&rdquo; with the vehicle changing."
                    .format(n=F["stalled"], s=F["stalledstr"])),
                   ("Distinct raw strings", "{v}".format(v=F["strings"]),
                    "type.strings",
                    "Grouped into <span data-fact=\"type.families\">{f}</span> "
                    "families by what the string says, so a new vehicle in a later "
                    "vintage lands in the right family rather than falling out. "
                    "The families also catch protests and DPWH road works, which "
                    "MMDA reports as traffic incidents.".format(f=F["families"]))],
                  "Incidents by type family", "typeChart"),
        p.section(6, "EDSA Is Half Of Everything",
                  "The most-reported locations, all of them on two roads. EDSA "
                  "alone accounts for nearly half of every located incident, which "
                  "is partly about EDSA and partly about where MMDA has cameras "
                  "and enforcers.",
                  [(F["ltop"], "{v}".format(v=F["ltopn"]), "loc.top.n",
                    "In {c}. The single most-reported spot in the file."
                    .format(c=F["ltopcity"])),
                   ("EDSA's share", "{v}%".format(v=F["edsapct"]),
                    "loc.edsa.pct",
                    "<span data-fact=\"loc.edsa.n\">{n:,}</span> incidents on one "
                    "road, out of every row that names a location."
                    .format(n=F["edsan"])),
                   ("Distinct locations", "{v:,}".format(v=F["locations"]),
                    "mmda.locations",
                    "Free text again, so &ldquo;EDSA GUADALUPE&rdquo; and "
                    "&ldquo;EDSA GUADALUPE NB&rdquo; are two entries. The count is "
                    "an upper bound on distinct places.")],
                  "Most-reported locations", "locChart"),
        p.section(7, "What The Country Looks Like Instead",
                  "WHO estimates of road traffic deaths per 100,000, for the "
                  "Philippines and five ASEAN neighbours. These are national, "
                  "annual and comparable &mdash; everything the tweets are not. "
                  "They are also modelled rather than counted: WHO adjusts "
                  "national registrations for known under-reporting.",
                  [("Philippines, {y}".format(y=F["ry"]), "{v}".format(v=F["rd"]),
                    "road.ph",
                    "Deaths per 100,000. "
                    "<span data-fact=\"road.rank\">{r}</span>rd lowest of "
                    "<span data-fact=\"road.n\">{n}</span>."
                    .format(r=F["rrank"], n=F["rn"])),
                   ("Direction of travel", "+{v}%".format(v=F["rdchange"]),
                    "road.ph.change",
                    "Since 2000, when it was "
                    "<span data-fact=\"road.ph.2000\">{a}</span>. Only "
                    "<span data-fact=\"road.rising\">{k}</span> of the six moved "
                    "that way; the other is {o}."
                    .format(a=F["rd00"], k=F["rrising"], o=F["rother"])),
                   (F["rworst"], "{v}".format(v=F["rworstv"]), "road.worst.rate",
                    "The highest of the six, and falling. A low rate that is "
                    "rising and a high rate that is falling are different "
                    "problems.")],
                  "Road traffic deaths per 100,000, 2000 onward", "deathChart"),
        p.prose(8, "What This Data Cannot Say",
                "Four limits, all of them structural rather than fixable.",
                [("It is not a count of incidents",
                  "It is a count of tweets. {silent} of the {span} days in the span "
                  "have no report at all and {blankm} whole months are empty, which "
                  "means the series measures reporting activity and traffic "
                  "together with no way to separate them. Every rate on this page "
                  "is per reporting day for that reason.".format(**F)),
                 ("There is no severity",
                  "The tweets say a vehicular accident occurred and how many lanes "
                  "were blocked. They do not say whether anyone was hurt. A check "
                  "asserts the injury and fatality counts stay at zero so a later "
                  "column cannot quietly turn an incident count into a casualty "
                  "figure."),
                 ("There is no denominator",
                  "An incident count without traffic volume is not a rate. Quezon "
                  "City has more reports than Navotas and also vastly more road, "
                  "more vehicles and more MMDA presence; nothing here separates "
                  "those. The national death rates in section 7 are per capita, "
                  "which is a denominator, and they rank the cities differently "
                  "than the tweet counts would."),
                 ("It stops in December 2020",
                  "Which means the recovery from lockdown is only partly visible: "
                  "the rate was still {recovery}% below its pre-March level when "
                  "the data ends, and whether it returned is outside this "
                  "file.".format(**F))]),
        p.prose(9, "Method",
                "One fetcher, ten CSVs, and a coverage table that counts every "
                "fault rather than silently repairing it.",
                [("The encoding is repaired, not worked around",
                  "&ldquo;ParaÃ±aque&rdquo; is &ldquo;Parañaque&rdquo; whose UTF-8 "
                  "bytes were decoded as Latin-1. Re-encoding to Latin-1 and "
                  "decoding as UTF-8 reverses it exactly, and is applied only when "
                  "the marker byte is present so a correct string is never touched. "
                  "A check then fails if any double-encoded name survives, and "
                  "another asserts Parañaque is one row rather than two."),
                 ("Bad coordinates are blanked, not dropped",
                  "The {null0} rows at exactly 0,0 are real incidents with a broken "
                  "geocode. Dropping them would understate the counts; keeping the "
                  "coordinate would put them in the Gulf of Guinea. The coordinate "
                  "is cleared, the incident still counts, and a check asserts every "
                  "surviving coordinate is inside a Metro Manila bounding "
                  "box.".format(**F)),
                 ("Times are parsed strictly",
                  "The file uses &ldquo;7:55 AM&rdquo;, &ldquo;3:20PM&rdquo; and "
                  "bare &ldquo;7:55&rdquo;. One row reads &ldquo;22:55 PM&rdquo; "
                  "&mdash; a 24-hour clock wearing a 12-hour marker &mdash; which a "
                  "naive conversion turns into hour 34. That is how it was found. "
                  "Anything that does not match an anchored pattern is recorded as "
                  "unparseable rather than guessed at."),
                 ("Empty months are rows, not gaps",
                  "The monthly table is built across the whole calendar span rather "
                  "than over the months that happen to have data, so July and "
                  "August 2020 appear as zero rows carrying a note. A check fails "
                  "if a zero month has no note, because a chart that plots a "
                  "reporting gap as zero is asserting something false."),
                 ("Types are grouped by substring",
                  "{st} distinct free-text strings, including VEHCICULAR, VEHICUKAR "
                  "and VEHICHULAR ACCIDENT. Grouping on what the string contains "
                  "rather than matching a hand-kept list means the misspellings "
                  "land in the right family and a new vehicle in a later vintage "
                  "does not fall out. A warn-level check lists the "
                  "&ldquo;vehicular&rdquo; variants that still sort into "
                  "&ldquo;other&rdquo;.".format(st=F["strings"])),
                 ("The national series comes through the World Bank",
                  "WHO Global Health Observatory road death estimates, fetched from "
                  "the World Bank WDI API because it is reachable and returns a "
                  "clean error on a wrong indicator code rather than an empty "
                  "success.")]),
    ]

    S.append('''        <section class="{wrap}">
            <div class="container">
                <div class="section-header fade-up">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li><span data-fact="mmda.top.city.pct">{toppct}%</span> of
                        the <span data-fact="mmda.n">{n:,}</span> incidents are in
                        {topcity} and
                        <span data-fact="mmda.top4.pct">{top4}%</span> in four
                        cities, so this ranks MMDA's reporting rather than Metro
                        Manila's roads.</li>
                        <li>&ldquo;15 Cities/Areas&rdquo; counted Parañaque twice,
                        because <span data-fact="bad.mojibake">{moji}</span> rows
                        spell it &ldquo;ParaÃ±aque&rdquo;. There are
                        <span data-fact="mmda.cities">{cities}</span> cities of a
                        possible 17.</li>
                        <li>The lockdown cut the daily rate from
                        <span data-fact="ecq.before">{before}</span> to
                        <span data-fact="ecq.during">{during}</span> &mdash;
                        <span data-fact="ecq.drop">{drop}%</span> &mdash; and it was
                        still <span data-fact="ecq.recovery">{recovery}%</span> down
                        when the file ends.</li>
                        <li>Morning beats evening,
                        <span data-fact="band.morning">{morning}%</span> against
                        <span data-fact="band.evening">{evening}%</span>, and 1pm
                        (<span data-fact="hour.lunch">{h13}</span>) is a sharper
                        trough than either night.
                        <span data-fact="dow.quietest.rate">{dquietr}</span> per day
                        on Sunday against
                        <span data-fact="dow.busiest.rate">{dbusyr}</span> on
                        Tuesday.</li>
                        <li>EDSA carries
                        <span data-fact="loc.edsa.pct">{edsapct}%</span> of every
                        located incident, on its own.</li>
                        <li>Nationally the death rate is
                        <span data-fact="road.ph">{rd}</span> per 100,000, third
                        lowest of <span data-fact="road.n">{rn}</span> in ASEAN, but
                        up <span data-fact="road.ph.change">{rdchange}%</span> since
                        2000 &mdash; one of only
                        <span data-fact="road.rising">{rrising}</span> in the group
                        moving that way.</li>
                        <li><span data-fact="bad.nullisland">{null0}</span> rows are
                        geocoded to 0,0,
                        <span data-fact="bad.time.total">{tbadtot}</span> have no
                        usable time, and
                        <span data-fact="mmda.silent.days">{silent}</span> days in
                        the span have no report at all.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**dict(F, **p.t)))

    MON = mon
    charts = ['''        // 01 by city. Log x, because Quezon City is 2,900 times Navotas and a
        //    linear axis renders twelve of the fourteen cities as nothing.
        new Chart(document.getElementById('cityChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Incidents', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of the file'; } } } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Incidents (log scale)' } } }
            }
        });''' % (js([x["city"] for x in city]),
                  js([int(x["incidents"]) for x in city]),
                  js(["#ef4444" if f(x["pct_of_all"]) > 40 else "#3b82f6"
                      for x in city]),
                  js([f(x["pct_of_all"]) for x in city])),

              '''        // 02 monthly. The two empty months are drawn as gaps rather than zeroes --
        //    plotting them at zero would assert there were no incidents.
        new Chart(document.getElementById('monthChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Incidents', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex]; } } } },
                scales: { x: { title: { display: true, text: 'Month (15 March 2020: ECQ begins)' } },
                          y: { beginAtZero: true,
                               title: { display: true, text: 'Incidents reported' } } }
            }
        });''' % (js([x["month"] for x in MON]),
                  js([None if x["incidents"] == "0" else int(x["incidents"])
                      for x in MON]),
                  js(["#94a3b8" if x["incidents"] == "0"
                      else "#ef4444" if "2020-0" in x["month"] and
                      x["month"] >= "2020-03" else "#3b82f6" for x in MON]),
                  js([x["note"] or "%s reporting day(s)" % x["reporting_days"]
                      for x in MON])),

              '''        // 03 by hour. The 1pm notch and the taller morning shoulder are the point.
        new Chart(document.getElementById('hourChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Incidents', data: %s, borderColor: '#f59e0b',
                             backgroundColor: 'rgba(245,158,11,0.18)',
                             borderWidth: 3, pointRadius: 3, fill: true, tension: 0.25 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Hour of day' } },
                          y: { beginAtZero: true,
                               title: { display: true, text: 'Incidents' } } }
            }
        });''' % (js(["%02d:00" % int(x["hour"]) for x in hour]),
                  js([int(x["incidents"]) for x in hour])),

              '''        // 04 per reporting day by weekday, not raw totals: Sunday has fewer
        //    reporting days as well as fewer incidents.
        new Chart(document.getElementById('dowChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Incidents per reporting day', data: %s,
                             backgroundColor: %s, borderRadius: 6 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' reporting days'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Incidents per reporting day' } } }
            }
        });''' % (js([x["day_of_week"][:3] for x in dow]),
                  js([f(x["incidents_per_reporting_day"]) for x in dow]),
                  js(["#8b5cf6" if x["day_of_week"] in ("Saturday", "Sunday")
                      else "#3b82f6" for x in dow]),
                  js([int(x["reporting_days"]) for x in dow])),

              '''        // 05 type families, with the number of distinct spellings each one absorbs.
        new Chart(document.getElementById('typeChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Incidents', data: %s, backgroundColor: '#3b82f6',
                      yAxisID: 'y' },
                    { type: 'line', label: 'Distinct free-text spellings', data: %s,
                      borderColor: '#ef4444', borderWidth: 2, pointRadius: 4,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Incidents' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Distinct strings' } } }
            }
        });''' % (js([x["type_family"] for x in typ]),
                  js([int(x["incidents"]) for x in typ]),
                  js([int(x["distinct_raw_strings"]) for x in typ])),

              '''        // 06 top locations. Coloured by road so EDSA's dominance is visible without
        //    being asserted in a caption.
        new Chart(document.getElementById('locChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Incidents', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex]; } } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Incidents reported' } } }
            }
        });''' % (js([x["location"] for x in loc[:22]]),
                  js([int(x["incidents"]) for x in loc[:22]]),
                  js(["#ef4444" if x["location"].startswith("EDSA")
                      else "#f59e0b" if x["location"].startswith("C5")
                      else "#3b82f6" for x in loc[:22]]),
                  js([x["city"] for x in loc[:22]])),

              '''        // 07 national road deaths. The Philippines is low and rising; Thailand is
        //    high and falling.
        new Chart(document.getElementById('deathChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Road deaths per 100,000' } } }
            }
        });''' % (js(sorted({int(x["year"]) for x in dth})),
                  "[" + ", ".join(
                      "{ label: %s, data: %s, borderColor: '%s', borderWidth: %d, "
                      "pointRadius: 0, fill: false }"
                      % (js(c), js([f(x["deaths_per_100k"]) for x in dth
                                    if x["country"] == c]),
                         "#ef4444" if c == "Philippines" else col, 3 if c == "Philippines" else 2)
                      for c, col in zip(
                          ["Philippines"] + sorted(set(x["country"] for x in dth)
                                                   - {"Philippines"}),
                          ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6",
                           "#64748b"])) + "]"),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "17,312 Tweets About Traffic, And What They Are Not",
        "MMDA incident reports from 2018 to 2020, read as what they are: %s%% of "
        "them are in one city, %d rows are geocoded to 0,0, and the March 2020 "
        "lockdown cut the daily rate by %s%%. Set against WHO national road death "
        "rates." % (F["toppct"], F["null0"], F["drop"]),
        "Half the file is one city. The lockdown cut the daily rate by %s%%."
        % F["drop"],
        "17,312 Tweets About Traffic, And What They Are Not")
    p.faq({
        "Which city in Metro Manila has the most traffic accidents?":
            "This data cannot answer that, and the shape of it shows why. Quezon "
            "City holds %s%% of all %s MMDA incident reports and Navotas holds %d, "
            "which reflects which MMDA units post to Twitter rather than which "
            "roads are dangerous. There is also no denominator -- no traffic volume "
            "and no road length -- so an incident count is not a rate."
            % (F["toppct"], format(F["n"], ","), F["botn"]),
        "How many cities does the MMDA traffic dataset cover?":
            "Fourteen, out of Metro Manila's 17 local government units. The City "
            "column holds 15 distinct strings, but two of them are the same city: "
            "%d rows spell Parañaque as \"ParaÃ±aque\", which is its UTF-8 bytes "
            "decoded as Latin-1. Counting distinct strings counts it twice, which is "
            "where the previously published figure of 15 came from."
            % F["moji"],
        "What happened to Metro Manila traffic during the COVID-19 lockdown?":
            "Incident reports fell from %s per reporting day before 15 March 2020 to "
            "%s during ECQ and MECQ, a drop of %s%%. February 2020 had %d reports; "
            "April had %d. By the end of the data in December 2020 the rate had "
            "recovered to %s per day, still %s%% below where it started."
            % (F["before"], F["during"], F["drop"], F["feb"], F["apr"], F["after"],
               F["recovery"]),
        "When do most Metro Manila traffic incidents happen?":
            "The morning peak is larger than the evening one: %s%% of timed "
            "incidents fall between 06:00 and 09:59 against %s%% between 16:00 and "
            "19:59. The single busiest hour is %d:00 with %s reports. The sharpest "
            "trough in daylight is 1pm, at %d -- %s%% of the morning peak. Sunday "
            "runs %s incidents per reporting day against Tuesday's %s."
            % (F["morning"], F["evening"], F["hpk"], format(F["hpkn"], ","),
               F["h13"], F["h13pct"], F["dquietr"], F["dbusyr"]),
        "How dangerous are Philippine roads compared with its neighbours?":
            "WHO estimates %s road deaths per 100,000 people in %d, which is the "
            "third lowest of six ASEAN countries -- below Malaysia, Vietnam and "
            "Thailand, whose rate is %s. But the Philippine figure has risen %s%% "
            "since 2000, from %s, and it is one of only %d of the six moving that "
            "way. A low rate that is rising and a high rate that is falling are "
            "different problems."
            % (F["rd"], F["ry"], F["rworstv"], F["rdchange"], F["rd00"],
               F["rrising"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
