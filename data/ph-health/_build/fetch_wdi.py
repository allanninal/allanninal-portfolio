#!/usr/bin/env python3
"""Philippine health indicators from the World Bank.

    .venv/bin/python data/ph-health/_build/fetch_wdi.py

DOH publishes the Field Health Services Information System, which is where
disease-specific Philippine numbers properly come from. doh.gov.ph sits behind a
managed challenge that scripts do not pass. The World Bank republishes the
internationally comparable subset -- mortality, life expectancy, immunisation,
TB, health spending -- sourced from WHO and UN IGME, and that is what this uses.

The two figures the page is built around are both spending-side, and both are
the kind of number that gets left out of health write-ups: what share of health
spending comes straight out of a household's pocket, and how TB incidence has
moved while everything else improved.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb                                        # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
IND = {
    "SP.DYN.LE00.IN": "life_expectancy",
    "SP.DYN.LE00.FE.IN": "life_expectancy_female",
    "SP.DYN.LE00.MA.IN": "life_expectancy_male",
    "SP.DYN.IMRT.IN": "infant_mortality_per_1000",
    "SH.DYN.MORT": "under5_mortality_per_1000",
    "SH.STA.MMRT": "maternal_mortality_per_100k",
    "SH.TBS.INCD": "tb_incidence_per_100k",
    "SH.IMM.MEAS": "measles_immunisation_pct",
    "SH.IMM.IDPT": "dpt_immunisation_pct",
    "SH.STA.STNT.ZS": "stunting_under5_pct",
    "SH.XPD.CHEX.GD.ZS": "health_spend_pct_gdp",
    "SH.XPD.OOPC.CH.ZS": "out_of_pocket_pct_of_health_spend",
    "SP.DYN.TFRT.IN": "fertility_rate",
}
ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia"}


def main():
    labels, rows, got = wb.panel("PHL", IND, first_year=1960)
    wb.write(OUT, "ph_health_annual.csv",
             ["year"] + labels + ["source"],
             [r + [wb.SRC] for r in rows])

    cov = []
    for label in labels:
        ys = sorted(got[label])
        cov.append([label, ys[0], ys[-1], len(ys),
                    len([y for y in range(ys[0], ys[-1] + 1) if y not in got[label]]),
                    wb.SRC])
    wb.write(OUT, "ph_health_coverage.csv",
             ["indicator", "first_year", "last_year", "points",
              "gap_years_inside_range", "source"], cov)

    # Comparison on the two indicators that carry the page: TB burden and the
    # out-of-pocket share of health spending.
    tb = {i: wb.series(i, "SH.TBS.INCD") for i in ASEAN}
    oop = {i: wb.series(i, "SH.XPD.OOPC.CH.ZS") for i in ASEAN}
    le = {i: wb.series(i, "SP.DYN.LE00.IN") for i in ASEAN}
    y = wb.common_year({**{k + "_tb": v for k, v in tb.items()},
                        **{k + "_oop": v for k, v in oop.items()},
                        **{k + "_le": v for k, v in le.items()}})
    wb.write(OUT, "ph_health_asean.csv",
             ["country", "year", "tb_incidence_per_100k",
              "out_of_pocket_pct_of_health_spend", "life_expectancy", "source"],
             sorted([[ASEAN[i], y, round(tb[i][y], 2), round(oop[i][y], 2),
                      round(le[i][y], 2), wb.SRC] for i in ASEAN],
                    key=lambda r: -r[2]))
    print("  ASEAN comparison year: %d" % y)


if __name__ == "__main__":
    main()
