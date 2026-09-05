#!/usr/bin/env python3
"""Shared World Bank WDI helpers.

Three projects pull from the same API with the same failure modes, so the
handling lives here once:

* A wrong indicator or country code returns an empty payload with HTTP 200, not
  an error. `series()` raises instead, because a silently empty series becomes a
  blank chart rather than a stack trace.
* Gaps are real. A country-year with no survey is null and stays null -- never
  forward-filled -- so a chart draws a gap where the data has one.
* Every row carries the source string, per the repo convention that a figure
  stays attributable after someone filters or joins it.
"""
import csv
import json
import os
import ssl
import time
import urllib.error
import urllib.request

SRC = "World Bank World Development Indicators API v2"
UA = "allanninal.dev research (contact via github.com/allanninal)"
BASE = "https://api.worldbank.org/v2/country/%s/indicator/%s?format=json&per_page=500"


def series(iso, code, tries=4):
    """{year: value} for one country and indicator, nulls omitted."""
    url = BASE % (iso, code)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120,
                                        context=ssl.create_default_context()) as r:
                d = json.loads(r.read())
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == tries - 1:
                raise SystemExit("World Bank fetch failed for %s %s: %s"
                                 % (iso, code, e))
            time.sleep(5 * (attempt + 1))
    if len(d) < 2 or not d[1]:
        raise SystemExit(
            "empty payload for %s %s -- a wrong indicator or country code returns "
            "no data rather than an error, which becomes a blank chart" % (iso, code))
    return {int(r["date"]): r["value"] for r in d[1] if r["value"] is not None}


def panel(iso, indicators, first_year=1960):
    """Wide rows [year, v1, v2, ...] over the union of years present."""
    got = {label: series(iso, code) for code, label in indicators.items()}
    years = sorted({y for s in got.values() for y in s if y >= first_year})
    labels = list(indicators.values())
    return labels, [[y] + [got[l].get(y) for l in labels] for y in years], got


def common_year(per_country, upto=None):
    """Latest year every country in the dict has a value for."""
    if not per_country:
        raise SystemExit("no countries supplied for comparison")
    years = set.intersection(*(set(s) for s in per_country.values()))
    if upto is not None:
        years = {y for y in years if y <= upto}
    if not years:
        raise SystemExit("no year has data for every country -- a like-for-like "
                         "comparison is impossible and each-country-own-latest "
                         "would compare different years")
    return max(years)


def write(outdir, name, cols, rows):
    path = os.path.join(outdir, name)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))
