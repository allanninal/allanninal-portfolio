#!/usr/bin/env python3
"""Philippine seismicity from the USGS FDSN event service.

    python3 fetch_usgs.py            # 2000-01-01 .. today

Free, no key, and the only fully open global catalogue with a stable API. Two
things about it decide the whole design:

* The service caps a single response at 20,000 events, and silently returns
  exactly that many rather than erroring when you ask for more. So the fetch is
  chunked by year and each chunk asserts it came back under the cap -- a chunk
  that hits 20,000 is a truncated year masquerading as a complete one.

* The catalogue is global. "Philippine earthquakes" is a bounding box, and the
  box is a choice that changes every number downstream, so it is stated in the
  CSV (every row carries it) and on the page rather than left implicit. The box
  below is the PHIVOLCS "Philippine region" extent, 4-22N / 116-128E, which is
  wider than the land area on purpose: the trenches that produce the large
  events are offshore.

Magnitude completeness matters more than it looks. USGS detection in this
region is not complete below about M4.5, and the small-magnitude counts rise
sharply over the series purely because the global network improved. Any claim
about "more earthquakes than before" therefore has to be made at M4.5+, which
is why the annual CSV carries counts at several thresholds instead of one.
"""
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date

BOX = dict(minlatitude=4, maxlatitude=22, minlongitude=116, maxlongitude=128)
BOX_LABEL = "4-22N,116-128E"
API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
CAP = 20000                     # USGS hard limit per response
MINMAG = 2.5
OUT = os.path.join(os.path.dirname(__file__), "..")
UA = "allanninal.dev research (contact via github.com/allanninal)"


def get(url, tries=4):
    """urlopen with an explicit Request -- urlretrieve sends no User-Agent."""
    ctx = ssl.create_default_context()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ssl.SSLError) as e:
            if i == tries - 1:
                raise
            print("    retry %d after %s" % (i + 1, e), file=sys.stderr)
            time.sleep(4 * (i + 1))


def year_events(year):
    end = "%d-01-01" % (year + 1)
    q = ["format=geojson", "starttime=%d-01-01" % year, "endtime=" + end,
         "minmagnitude=%s" % MINMAG, "orderby=time-asc", "limit=%d" % CAP]
    q += ["%s=%s" % (k, v) for k, v in BOX.items()]
    d = json.loads(get(API + "?" + "&".join(q)))
    feats = d.get("features", [])
    if len(feats) >= CAP:
        raise SystemExit(
            "%d returned %d events, at or above the %d cap -- the year is "
            "truncated and must be split into sub-year windows before the "
            "counts below can be trusted." % (year, len(feats), CAP))
    return feats


def main():
    today = date.today()
    years = range(2000, today.year + 1)
    rows, coverage = [], []
    for y in years:
        try:
            feats = year_events(y)
        except SystemExit:
            raise
        except Exception as e:
            coverage.append(dict(year=y, events=0, status="error:%s" % e,
                                 box=BOX_LABEL, source="USGS FDSN event/1/query"))
            print("  %d  ERROR %s" % (y, e))
            continue
        for f in feats:
            p, g = f["properties"], f["geometry"]["coordinates"]
            t = p.get("time")
            if t is None or p.get("mag") is None:
                continue
            rows.append(dict(
                id=f["id"],
                time_utc=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t / 1000.0)),
                year=time.gmtime(t / 1000.0).tm_year,
                month=time.gmtime(t / 1000.0).tm_mon,
                mag=round(float(p["mag"]), 2),
                magtype=p.get("magType") or "",
                # geometry is [lon, lat, depth_km] -- in that order, which is
                # the reverse of how every chart axis wants them.
                longitude=round(float(g[0]), 4),
                latitude=round(float(g[1]), 4),
                depth_km=round(float(g[2]), 2) if g[2] is not None else "",
                place=(p.get("place") or "").replace(",", ";"),
                box=BOX_LABEL,
                source="USGS FDSN event/1/query"))
        coverage.append(dict(year=y, events=len(feats), status="parsed",
                             box=BOX_LABEL, source="USGS FDSN event/1/query"))
        print("  %d  %6d events" % (y, len(feats)))

    if not rows:
        raise SystemExit("no events fetched -- refusing to write an empty CSV")

    ev = os.path.join(OUT, "ph_earthquakes.csv")
    with open(ev, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote %s (%d rows)" % (ev, len(rows)))

    cv = os.path.join(OUT, "ph_earthquakes_coverage.csv")
    with open(cv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coverage[0].keys()))
        w.writeheader()
        w.writerows(coverage)
    print("wrote %s (%d rows)" % (cv, len(coverage)))


if __name__ == "__main__":
    main()
