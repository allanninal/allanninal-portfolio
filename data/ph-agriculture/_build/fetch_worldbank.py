#!/usr/bin/env python3
"""Agriculture's share of the Philippine economy and workforce, World Bank API.

    .venv/bin/python data/ph-agriculture/_build/fetch_worldbank.py

FAOSTAT says how much is grown. These four say what that is worth and who does
it, which is the part of the story tonnage cannot carry:

    NV.AGR.TOTL.ZS   agriculture, forestry and fishing, value added (% of GDP)
    SL.AGR.EMPL.ZS   employment in agriculture (% of total employment)
    AG.LND.ARBL.HA.PC  arable land, hectares per person
    AG.CON.FERT.ZS   fertiliser consumption (kg per hectare of arable land)

Gaps stay as nulls. The employment series in particular is modelled by the ILO
for years without a labour force survey, and forward-filling it would present a
model output as a measurement.
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
    "NV.AGR.TOTL.ZS": "agri_value_added_pct_gdp",
    "SL.AGR.EMPL.ZS": "agri_employment_pct",
    "AG.LND.ARBL.HA.PC": "arable_ha_per_person",
    "AG.CON.FERT.ZS": "fertiliser_kg_per_ha",
}
ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120,
                                context=ssl.create_default_context()) as r:
        return json.loads(r.read())


def series(iso, code):
    d = get("https://api.worldbank.org/v2/country/%s/indicator/%s"
            "?format=json&per_page=500" % (iso, code))
    if len(d) < 2 or not d[1]:
        raise SystemExit("empty payload for %s %s -- a bad indicator or country "
                         "code returns no data rather than an error" % (iso, code))
    return {int(r["date"]): r["value"] for r in d[1]}


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    ph = {label: series("PHL", code) for code, label in IND.items()}
    years = [y for y in range(1961, 2027)
             if any(ph[l].get(y) is not None for l in IND.values())]
    write("ph_agri_economy.csv",
          ["year"] + list(IND.values()) + ["source"],
          [[y] + [None if ph[l].get(y) is None else round(ph[l][y], 3)
                  for l in IND.values()] + [SRC] for y in years])

    # Comparison at the latest year every country has, for the same reason the
    # internet project does it: each-country-own-latest compares 2024 with 2019.
    va = {i: series(i, "NV.AGR.TOTL.ZS") for i in ASEAN}
    em = {i: series(i, "SL.AGR.EMPL.ZS") for i in ASEAN}
    common = [y for y in range(1990, 2027)
              if all(va[i].get(y) is not None and em[i].get(y) is not None
                     for i in ASEAN)]
    if not common:
        raise SystemExit("no year has both indicators for all five countries")
    y = max(common)
    write("ph_agri_asean.csv",
          ["country", "year", "agri_value_added_pct_gdp", "agri_employment_pct", "source"],
          sorted(([ASEAN[i], y, round(va[i][y], 2), round(em[i][y], 2), SRC]
                  for i in ASEAN), key=lambda r: -r[2]))
    print("  ASEAN comparison year: %d" % y)


if __name__ == "__main__":
    main()
