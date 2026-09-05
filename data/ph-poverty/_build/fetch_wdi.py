#!/usr/bin/env python3
"""Philippine poverty and income distribution from the World Bank.

    .venv/bin/python data/ph-poverty/_build/fetch_wdi.py

The page this feeds was specified around PSA's Family Income and Expenditure
Survey at regional granularity -- agricultural wages by region, farm household
income composition, rural income distribution. PSA is behind a managed challenge
and none of that is fetchable, so the page covers the national series the World
Bank republishes from the same underlying surveys.

One property to hold on to: poverty and inequality figures come from household
surveys run every three years, not annually. The series has four national
poverty points and fourteen distribution points across four decades. Anything
drawn as a smooth annual line would be inventing the years between.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb                                        # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
IND = {
    "SI.POV.NAHC": "poverty_national_pct",
    "SI.POV.DDAY": "poverty_215usd_pct",
    "SI.POV.LMIC": "poverty_365usd_pct",
    "SI.POV.GINI": "gini",
    "SI.DST.FRST.20": "income_share_bottom_20",
    "SI.DST.10TH.10": "income_share_top_10",
    "SL.UEM.TOTL.ZS": "unemployment_pct",
    "SL.EMP.VULN.ZS": "vulnerable_employment_pct",
    "NY.GNP.PCAP.CD": "gni_per_capita_usd",
}
ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia"}


def main():
    labels, rows, got = wb.panel("PHL", IND, first_year=1980)
    wb.write(OUT, "ph_poverty_annual.csv",
             ["year"] + labels + ["source"], [r + [wb.SRC] for r in rows])

    # Survey years only, for the distribution measures. Publishing these as an
    # annual panel invites a line chart through years nobody surveyed.
    surv = sorted(set(got["gini"]) | set(got["poverty_national_pct"]))
    wb.write(OUT, "ph_poverty_surveys.csv",
             ["survey_year", "gini", "income_share_bottom_20", "income_share_top_10",
              "poverty_national_pct", "poverty_215usd_pct", "source"],
             [[y, got["gini"].get(y), got["income_share_bottom_20"].get(y),
               got["income_share_top_10"].get(y),
               got["poverty_national_pct"].get(y),
               got["poverty_215usd_pct"].get(y), wb.SRC] for y in surv])

    cov = []
    for label in labels:
        ys = sorted(got[label])
        cov.append([label, ys[0], ys[-1], len(ys),
                    len([y for y in range(ys[0], ys[-1] + 1) if y not in got[label]]),
                    wb.SRC])
    wb.write(OUT, "ph_poverty_coverage.csv",
             ["indicator", "first_year", "last_year", "points",
              "gap_years_inside_range", "source"], cov)

    gini = {i: wb.series(i, "SI.POV.GINI") for i in ASEAN}
    pov = {i: wb.series(i, "SI.POV.LMIC") for i in ASEAN}
    y = wb.common_year({**{k + "g": v for k, v in gini.items()},
                        **{k + "p": v for k, v in pov.items()}})
    wb.write(OUT, "ph_poverty_asean.csv",
             ["country", "year", "gini", "poverty_365usd_pct", "source"],
             sorted([[ASEAN[i], y, round(gini[i][y], 2), round(pov[i][y], 2), wb.SRC]
                     for i in ASEAN], key=lambda r: -r[2]))
    print("  ASEAN comparison year: %d" % y)


if __name__ == "__main__":
    main()
