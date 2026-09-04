#!/usr/bin/env python3
"""Philippine connectivity indicators from the World Bank API.

    .venv/bin/python data/ph-internet/_build/fetch_worldbank.py

Free, no key, JSON. Four indicators plus an ASEAN comparison:

    IT.NET.USER.ZS   individuals using the internet, % of population
    IT.CEL.SETS.P2   mobile cellular subscriptions per 100 people
    IT.NET.BBND.P2   fixed broadband subscriptions per 100 people
    IT.MLT.MAIN.P2   fixed telephone subscriptions per 100 people

The World Bank reports these with a long lag and leaves gaps -- a country-year
with no survey is null, not zero. The rows are written with the null intact
rather than forward-filled, and the coverage CSV records the latest year each
indicator actually has a value, because a chart that carries the last known
figure forward to the present is asserting a measurement nobody made.
"""
import csv
import json
import os
import ssl
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
SRC = "World Bank World Development Indicators API v2"
UA = "allanninal.dev research (contact via github.com/allanninal)"
IND = {
    "IT.NET.USER.ZS": "internet_users_pct",
    "IT.CEL.SETS.P2": "mobile_per_100",
    "IT.NET.BBND.P2": "fixed_broadband_per_100",
    "IT.MLT.MAIN.P2": "fixed_telephone_per_100",
}
ASEAN = ["PHL", "IDN", "VNM", "THA", "MYS", "SGP"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120,
                                context=ssl.create_default_context()) as r:
        return json.loads(r.read())


def series(iso, code):
    url = ("https://api.worldbank.org/v2/country/%s/indicator/%s"
           "?format=json&per_page=500" % (iso, code))
    d = get(url)
    if len(d) < 2 or not d[1]:
        raise SystemExit("no data for %s %s -- the indicator code or country "
                         "code is wrong, which returns an empty payload rather "
                         "than an error" % (iso, code))
    return {int(r["date"]): r["value"] for r in d[1]}


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    ph = {label: series("PHL", code) for code, label in IND.items()}
    years = sorted(set().union(*[set(v) for v in ph.values()]))
    years = [y for y in years if y >= 2000]
    rows = [[y] + [ph[l].get(y) if ph[l].get(y) is None else round(ph[l][y], 2)
                   for l in IND.values()] + [SRC] for y in years]
    write("ph_internet_annual.csv",
          ["year"] + list(IND.values()) + ["source"], rows)

    cov = []
    for label in IND.values():
        got = sorted(y for y, v in ph[label].items() if v is not None and y >= 2000)
        cov.append([label, got[0], got[-1], len(got),
                    len([y for y in range(got[0], got[-1] + 1)
                         if ph[label].get(y) is None]), SRC])
    write("ph_internet_coverage.csv",
          ["indicator", "first_year", "last_year", "years_with_data",
           "gap_years_inside_range", "source"], cov)

    # ASEAN at the latest year every country in the set actually has, so the
    # comparison is like-for-like. Picking each country's own latest year would
    # compare 2023 against 2019 and call it a gap.
    per = {iso: series(iso, "IT.NET.USER.ZS") for iso in ASEAN}
    common = [y for y in range(2000, 2027)
              if all(per[i].get(y) is not None for i in ASEAN)]
    if not common:
        raise SystemExit("no year has internet-use data for all six countries")
    y = max(common)
    bb = {iso: series(iso, "IT.NET.BBND.P2") for iso in ASEAN}
    mb = {iso: series(iso, "IT.CEL.SETS.P2") for iso in ASEAN}
    names = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
             "THA": "Thailand", "MYS": "Malaysia", "SGP": "Singapore"}
    rows = sorted(([names[i], y, round(per[i][y], 2),
                    round(bb[i][y], 2) if bb[i].get(y) is not None else "",
                    round(mb[i][y], 2) if mb[i].get(y) is not None else "", SRC]
                   for i in ASEAN), key=lambda r: -r[2])
    write("ph_internet_asean.csv",
          ["country", "year", "internet_users_pct", "fixed_broadband_per_100",
           "mobile_per_100", "source"], rows)
    print("  ASEAN comparison year: %d" % y)


if __name__ == "__main__":
    main()
