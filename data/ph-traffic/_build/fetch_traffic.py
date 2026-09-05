#!/usr/bin/env python3
"""MMDA traffic incident tweets, cleaned, plus national road-death rates.

The published page reported 17,312 incidents (right), 11,781 vehicular accidents
(wrong -- there are 11,775) and "15 Cities/Areas". That last one is the
interesting mistake: the City column really does hold 15 distinct strings, but
two of them are the same city. "Parañaque" appears both correctly and as
"ParaÃ±aque", which is its UTF-8 bytes read as Latin-1. Counting distinct strings
counted it twice.

Opening the file turns up five more faults, none of which is visible from a
summary:

  * 55 rows carry latitude and longitude of exactly 0.0, which is in the Gulf of
    Guinea. Any map built from this data without checking plots them there;
  * 138 rows have a time that does not parse -- 122 blank, and sixteen typos
    including "22:55 PM", "12:04 PA" and "8:20 AM AM";
  * 187 rows have no city and 57 no incident type;
  * July and August 2020 contain no rows at all. Not zero incidents in Metro
    Manila for two months -- a reporting gap, and a monthly chart that plots it
    as zero is asserting something false;
  * Quezon City holds 50.4% of every incident in the file. That is a fact about
    which MMDA units tweet, not about which roads are dangerous.

So this is a dataset about MMDA's Twitter output, and the page says so. The
counterweight is WHO road traffic death rates via the World Bank, which are
national, annual, and comparable across ASEAN -- and which put the Philippines
mid-pack rather than worst.

The one thing the tweets do carry that no national series does is 15 March 2020.
Metro Manila went into enhanced community quarantine that day, and the file
records 775 incidents in February against 11 in April.

Writes:
  ph_traffic_incidents.csv   one row per incident, cleaned, faults flagged
  ph_traffic_monthly.csv     incidents per month, with reporting days
  ph_traffic_hourly.csv      by hour of day
  ph_traffic_dow.csv         by day of week
  ph_traffic_by_city.csv     by city, with the encoding repaired
  ph_traffic_by_type.csv     by incident type, grouped into families
  ph_traffic_locations.csv   the most-reported locations
  ph_traffic_ecq.csv         before, during and after the March 2020 lockdown
  ph_traffic_deaths.csv      WHO road traffic deaths per 100k, ASEAN, 2000-2019
  ph_traffic_coverage.csv    every fault above, counted
"""
import csv
import io
import os
import re
import sys
import zipfile
import datetime
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
KAGGLE = ("https://www.kaggle.com/api/v1/datasets/download/"
          "esparko/mmda-traffic-incident-data")
SRC = "Kaggle esparko/mmda-traffic-incident-data (MMDA @mmda tweets, 2018-2020)"
SRC_WHO = "WHO Global Health Observatory road traffic deaths, via World Bank WDI"

ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia", "SGP": "Singapore"}

# Metro Manila's bounding box, generously drawn. Anything outside is a bad fix,
# not a distant incident: MMDA reports on NCR roads only.
BOX = (14.30, 14.85, 120.88, 121.18)

ECQ_START = datetime.date(2020, 3, 15)      # NCR enhanced community quarantine
ECQ_END = datetime.date(2020, 5, 31)        # ECQ/MECQ ended 31 May 2020

# TIME accepts "7:55 AM", "3:20PM" and "7:55" -- the file uses all three -- and
# nothing else. Anchored, with bounded digit runs, so it cannot backtrack.
TIME = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$")


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-30s %5d rows" % (name, len(rows)))


def demojibake(s):
    """Undo one round of UTF-8 bytes decoded as Latin-1.

    "ParaÃ±aque" is what "Parañaque" becomes when its UTF-8 bytes are read as
    Latin-1. Re-encoding to Latin-1 and decoding as UTF-8 reverses it exactly.
    Applied only when the marker byte is present, so a correctly encoded string
    is never touched.
    """
    if "Ã" not in s and "Â" not in s:
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def hour_of(t):
    """(hour, fault) for a time string. hour is None when nothing parses."""
    t = (t or "").strip().upper()
    if not t:
        return None, "time missing"
    m = TIME.match(t)
    if not m:
        return None, "time unparseable"
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if mi > 59:
        return None, "time unparseable"
    if ap == "AM":
        # 12:xx AM is midnight. And "22:55 PM" is in the file: a 24-hour clock
        # wearing a 12-hour marker. Taking the marker at face value there gives
        # hour 34, which is how it was found.
        if h > 12:
            return None, "time unparseable"
        h = 0 if h == 12 else h
    elif ap == "PM":
        if h > 12:
            return None, "time unparseable"
        h = 12 if h == 12 else h + 12
    elif h > 23:
        return None, "time unparseable"
    return h, ""


# Incident types are free text -- 100-odd distinct strings, most of them a
# variation on "STALLED <vehicle> DUE TO MECHANICAL PROBLEM". Grouped by what
# the string says rather than by a hand-kept list, so a new vehicle in a later
# vintage lands in the right family instead of falling out.
def family(ty):
    t = (ty or "").upper()
    if not t.strip():
        return "unclassified"
    if "STALLED" in t:
        return "stalled vehicle"
    if "MULTIPLE COLLISION" in t:
        return "multiple collision"
    if "SELF ACCIDENT" in t:
        return "self accident"
    if "VEHICULAR ACCIDENT" in t:
        return "vehicular accident"
    if "HIT" in t and "RUN" in t:
        return "hit and run"
    return "other"


def load():
    req = urllib.request.Request(KAGGLE, headers={"User-Agent": "Mozilla/5.0"})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=180).read()))
    name = "data_mmda_traffic_spatial.csv"
    if name not in z.namelist():
        raise SystemExit("archive layout changed: %s" % z.namelist())
    txt = z.read(name).decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(txt)))


def main():
    raw = load()
    print("  %d raw row(s)" % len(raw))
    fault = {}

    def count(k, n=1):
        fault[k] = fault.get(k, 0) + n

    out = []
    for i, r in enumerate(raw, 1):
        faults = []
        city_raw = (r.get("City") or "").strip()
        city = demojibake(city_raw)
        if city != city_raw:
            faults.append("city mojibake")
            count("city name double-encoded")
        if not city:
            faults.append("city missing")
            count("city missing")

        try:
            d = datetime.date.fromisoformat((r.get("Date") or "").strip())
        except ValueError:
            count("date unparseable")
            continue

        hr, tf = hour_of(r.get("Time"))
        if tf:
            faults.append(tf)
            count(tf)

        lat = float(r["Latitude"]) if r.get("Latitude") else None
        lon = float(r["Longitude"]) if r.get("Longitude") else None
        geo_ok = (lat is not None and lon is not None
                  and BOX[0] <= lat <= BOX[1] and BOX[2] <= lon <= BOX[3])
        if not geo_ok:
            if lat == 0 and lon == 0:
                faults.append("coordinates at 0,0")
                count("coordinates at exactly 0,0")
            else:
                faults.append("coordinates outside Metro Manila")
                count("coordinates outside the NCR box")

        ty = (r.get("Type") or "").strip()
        if not ty:
            faults.append("type missing")
            count("incident type missing")

        out.append([i, d.isoformat(), hr if hr is not None else "",
                    city, (r.get("Location") or "").strip()[:90],
                    lat if geo_ok else "", lon if geo_ok else "",
                    ty[:90], family(ty),
                    (r.get("Direction") or "").strip(),
                    r.get("Lanes_Blocked") or "",
                    "; ".join(faults), SRC])

    write("ph_traffic_incidents.csv",
          ["incident_id", "date", "hour", "city", "location", "latitude",
           "longitude", "incident_type", "type_family", "direction",
           "lanes_blocked", "faults", "source"], out)

    days = sorted({x[1] for x in out})
    first = datetime.date.fromisoformat(days[0])
    last = datetime.date.fromisoformat(days[-1])
    span = (last - first).days + 1

    # ---- monthly, with reporting days, so a gap cannot read as a zero -------
    by_m = {}
    for x in out:
        by_m.setdefault(x[1][:7], []).append(x)
    months, cur = [], datetime.date(first.year, first.month, 1)
    while cur <= last:
        k = cur.strftime("%Y-%m")
        rs = by_m.get(k, [])
        nxt = (cur.replace(day=28) + datetime.timedelta(days=7)).replace(day=1)
        cal = (min(nxt, last + datetime.timedelta(days=1))
               - max(cur, first)).days
        months.append([k, len(rs), len({x[1] for x in rs}), cal,
                       "no rows at all" if not rs else "", SRC])
        cur = nxt
    write("ph_traffic_monthly.csv",
          ["month", "incidents", "reporting_days", "calendar_days_in_span",
           "note", "source"], months)
    for m in months:
        if m[4]:
            count("month with no rows at all")

    # ---- hour of day --------------------------------------------------------
    hrs = {}
    for x in out:
        if x[2] != "":
            hrs[x[2]] = hrs.get(x[2], 0) + 1
        tot = sum(hrs.values())
    write("ph_traffic_hourly.csv",
          ["hour", "incidents", "pct_of_timed", "source"],
          [[h, hrs.get(h, 0), round(100.0 * hrs.get(h, 0) / tot, 2), SRC]
           for h in range(24)])

    # ---- day of week --------------------------------------------------------
    NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
    dw, dwd = {}, {}
    for x in out:
        d = datetime.date.fromisoformat(x[1])
        dw[d.weekday()] = dw.get(d.weekday(), 0) + 1
        dwd.setdefault(d.weekday(), set()).add(x[1])
    write("ph_traffic_dow.csv",
          ["day_of_week", "weekday_index", "incidents", "reporting_days",
           "incidents_per_reporting_day", "source"],
          [[NAMES[i], i, dw.get(i, 0), len(dwd.get(i, ())),
            round(dw.get(i, 0) / len(dwd[i]), 2) if dwd.get(i) else "", SRC]
           for i in range(7)])

    # ---- city ---------------------------------------------------------------
    bc = {}
    for x in out:
        bc.setdefault(x[3] or "(no city given)", []).append(x)
    write("ph_traffic_by_city.csv",
          ["city", "incidents", "pct_of_all", "geocoded_in_ncr", "source"],
          sorted(([c, len(rs), round(100.0 * len(rs) / len(out), 2),
                   sum(1 for x in rs if x[5] != ""), SRC]
                  for c, rs in bc.items()), key=lambda r: -r[1]))

    # ---- type family --------------------------------------------------------
    bf = {}
    for x in out:
        bf[x[8]] = bf.get(x[8], 0) + 1
    write("ph_traffic_by_type.csv",
          ["type_family", "incidents", "pct_of_all", "distinct_raw_strings",
           "source"],
          sorted(([k, v, round(100.0 * v / len(out), 2),
                   len({x[7] for x in out if x[8] == k}), SRC]
                  for k, v in bf.items()), key=lambda r: -r[1]))

    # ---- locations ----------------------------------------------------------
    bl = {}
    for x in out:
        if x[4]:
            bl.setdefault(x[4], []).append(x)
    write("ph_traffic_locations.csv",
          ["location", "city", "incidents", "source"],
          sorted(([loc, rs[0][3], len(rs), SRC] for loc, rs in bl.items()),
                 key=lambda r: -r[2])[:60])

    # ---- the lockdown -------------------------------------------------------
    # Per reporting day, not per calendar day: the file stops reporting for
    # stretches, and dividing by calendar days would blame the roads for a
    # silent Twitter account.
    def window(a, b, label):
        rs = [x for x in out if a <= datetime.date.fromisoformat(x[1]) <= b]
        nd = len({x[1] for x in rs})
        return [label, a.isoformat(), b.isoformat(), len(rs), nd,
                (b - a).days + 1,
                round(len(rs) / nd, 2) if nd else "", SRC]

    ecq = [window(first, ECQ_START - datetime.timedelta(days=1),
                  "before ECQ"),
           window(ECQ_START, ECQ_END, "ECQ and MECQ"),
           window(ECQ_END + datetime.timedelta(days=1), last, "after MECQ")]
    write("ph_traffic_ecq.csv",
          ["period", "from_date", "to_date", "incidents", "reporting_days",
           "calendar_days", "incidents_per_reporting_day", "source"], ecq)

    # ---- national road deaths ----------------------------------------------
    got = {i: wb.series(i, "SH.STA.TRAF.P5") for i in ASEAN}
    years = sorted(set().union(*(set(v) for v in got.values())))
    write("ph_traffic_deaths.csv",
          ["country", "year", "deaths_per_100k", "source"],
          [[ASEAN[i], y, round(got[i][y], 2), SRC_WHO]
           for i in ASEAN for y in years if y in got[i]])
    ly = max(y for y in years if all(y in got[i] for i in ASEAN))
    print("  road-death comparison year: %d" % ly)

    # ---- coverage -----------------------------------------------------------
    cov = [["rows in file", len(raw), "", SRC],
           ["incidents kept", len(out), "rows with an unparseable date are dropped",
            SRC],
           ["first date", days[0], "", SRC],
           ["last date", days[-1], "", SRC],
           ["calendar days in span", span, "", SRC],
           ["days with at least one report", len(days),
            "%d day(s) in the span have no report at all"
            % (span - len(days)), SRC],
           ["cities present", len(bc) - (1 if "(no city given)" in bc else 0),
            "Metro Manila has 17 local government units", SRC],
           ["share in the single most-reported city",
            round(100.0 * max(len(v) for v in bc.values()) / len(out), 2),
            max(bc, key=lambda k: len(bc[k])), SRC],
           ["incidents usable on a map", sum(1 for x in out if x[5] != ""),
            "the rest have no coordinate inside Metro Manila", SRC],
           ["incidents with a usable time",
            sum(1 for x in out if x[2] != ""), "", SRC],
           ["injury or fatality counts", 0,
            "the tweets do not state them, so no severity is derived", SRC],
           ["traffic volume", 0,
            "no denominator: an incident count is not a rate", SRC]]
    for k in sorted(fault):
        cov.append([k, fault[k], "fault found and flagged per row", SRC])
    write("ph_traffic_coverage.csv",
          ["property", "value", "note", "source"], cov)
    for k in sorted(fault):
        print("    %-34s %d" % (k, fault[k]))


if __name__ == "__main__":
    main()
