#!/usr/bin/env python3
"""Philippine logistics competitiveness, from the World Bank's LPI.

    .venv/bin/python data/ph-logistics/_build/fetch_lpi.py

This project exists because the page it feeds could not be built as specified.
That page ranked 149 Philippine cities on the DTI's Cities and Municipalities
Competitiveness Index. cmci.dti.gov.ph returns 403 to anything that is not a
browser and there is no open CMCI feed, so the city rankings are unreachable and
the page says so rather than approximating them.

What IS open is the Logistics Performance Index: a survey of freight forwarders
scoring each country 1-5 on six dimensions plus an overall score. It measures a
real and specific slice of competitiveness -- how well goods actually move -- for
the Philippines and its neighbours on the same scale in the same rounds.

Two properties that shape every chart downstream:

* The LPI is a SURVEY, not a measurement. Scores come from forwarders rating
  countries they ship to, so a change between rounds can reflect a change in
  respondents as easily as a change in ports. The World Bank itself warns
  against reading single-round movements as trend.
* Rounds are irregular -- 2007, 2010, 2012, 2014, 2016, 2018, 2023 -- with a
  five-year gap over the pandemic. Plotting them on an evenly spaced axis
  implies a regular series that does not exist, so the year is carried and the
  page uses a linear time axis.
"""
import csv
import json
import os
import ssl
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
UA = "allanninal.dev research (contact via github.com/allanninal)"
SRC = "World Bank Logistics Performance Index"
DIM = {
    "LP.LPI.OVRL.XQ": "overall",
    "LP.LPI.CUST.XQ": "customs",
    "LP.LPI.INFR.XQ": "infrastructure",
    "LP.LPI.ITRN.XQ": "international shipments",
    "LP.LPI.LOGS.XQ": "logistics competence",
    "LP.LPI.TRAC.XQ": "tracking and tracing",
    "LP.LPI.TIME.XQ": "timeliness",
}
ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia", "SGP": "Singapore"}


def wb(iso, code):
    url = ("https://api.worldbank.org/v2/country/%s/indicator/%s"
           "?format=json&per_page=500" % (iso, code))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120,
                                context=ssl.create_default_context()) as r:
        d = json.loads(r.read())
    if len(d) < 2 or not d[1]:
        raise SystemExit("empty payload for %s %s -- a bad code returns no data "
                         "rather than an error" % (iso, code))
    return {int(r["date"]): r["value"] for r in d[1] if r["value"] is not None}


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    data = {}
    for iso in ASEAN:
        for code, dim in DIM.items():
            for year, val in wb(iso, code).items():
                data[(iso, dim, year)] = val
    if not data:
        raise SystemExit("no LPI observations fetched")
    years = sorted({y for _, _, y in data})
    print("  %d observations, rounds: %s"
          % (len(data), ", ".join(str(y) for y in years)))

    write("ph_lpi_scores.csv",
          ["country", "iso", "dimension", "year", "score", "scale", "source"],
          sorted([[ASEAN[i], i, d, y, round(v, 3), "1-5 survey scale", SRC]
                  for (i, d, y), v in data.items()],
                 key=lambda r: (r[0], r[2], r[3])))

    # Rank within the ASEAN-6 on the overall score, per round. Rank is a more
    # honest headline than the raw score: a survey scale moves between rounds for
    # reasons that have nothing to do with any one country.
    rows = []
    for y in years:
        got = sorted(((i, data[(i, "overall", y)]) for i in ASEAN
                      if (i, "overall", y) in data), key=lambda t: -t[1])
        for rank, (i, v) in enumerate(got, 1):
            rows.append([ASEAN[i], i, y, rank, len(got), round(v, 3), SRC])
    write("ph_lpi_ranks.csv",
          ["country", "iso", "year", "rank_in_asean6", "countries_ranked",
           "overall_score", "source"], rows)

    # Coverage: which rounds exist and how far apart they sit. The 2018-2023 gap
    # is five years and the page must not draw it as if it were two.
    cov = []
    for a, b in zip(years, years[1:]):
        cov.append([a, b, b - a, SRC])
    write("ph_lpi_rounds.csv",
          ["round_year", "next_round_year", "gap_years", "source"], cov)


if __name__ == "__main__":
    main()
