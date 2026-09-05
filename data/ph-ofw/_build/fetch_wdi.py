#!/usr/bin/env python3
"""Philippine remittances and migration from the World Bank.

    .venv/bin/python data/ph-ofw/_build/fetch_wdi.py

The page this feeds was specified around POEA/DMW deployment statistics -- OFW
headcount by sex, age, occupation, destination and region of origin. DMW
publishes those as annual PDF compendiums and PSA's Survey on Overseas Filipinos
sits behind the same managed challenge as the rest of psa.gov.ph, so none of it
is fetchable. What is open is the money: remittance inflows, their share of GDP,
and net migration, all on a long consistent series.

That is a narrower question -- what migration sends home, not who migrates -- and
the page says so rather than approximating a headcount.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb                                        # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
IND = {
    "BX.TRF.PWKR.CD.DT": "remittances_usd",
    "BX.TRF.PWKR.DT.GD.ZS": "remittances_pct_gdp",
    "SM.POP.NETM": "net_migration",
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NE.EXP.GNFS.CD": "exports_goods_services_usd",
    "BX.KLT.DINV.CD.WD": "fdi_net_inflows_usd",
}
# Large remittance economies. Vietnam is deliberately absent: the World Bank has
# only five points of remittances-as-%-of-GDP for it (2000-2004), which pinned the
# whole like-for-like comparison to 2004 and would have presented a twenty-year-old
# snapshot as current.
PEERS = {"PHL": "Philippines", "IND": "India", "MEX": "Mexico",
         "PAK": "Pakistan", "IDN": "Indonesia", "BGD": "Bangladesh"}


def main():
    labels, rows, got = wb.panel("PHL", IND, first_year=1977)
    # Remittances against FDI and exports: the comparison that says what
    # migration actually is in this economy.
    out = []
    for r in rows:
        d = dict(zip(labels, r[1:]))
        rem, fdi = d["remittances_usd"], d["fdi_net_inflows_usd"]
        out.append(r + [round(rem / fdi, 2) if (rem and fdi and fdi > 0) else None,
                        wb.SRC])
    wb.write(OUT, "ph_ofw_annual.csv",
             ["year"] + labels + ["remittances_over_fdi", "source"], out)

    cov = []
    for label in labels:
        ys = sorted(got[label])
        cov.append([label, ys[0], ys[-1], len(ys),
                    len([y for y in range(ys[0], ys[-1] + 1) if y not in got[label]]),
                    wb.SRC])
    wb.write(OUT, "ph_ofw_coverage.csv",
             ["indicator", "first_year", "last_year", "points",
              "gap_years_inside_range", "source"], cov)

    # Against other large remittance economies, per cent of GDP. Absolute dollars
    # would just rank by country size and say nothing.
    pct = {i: wb.series(i, "BX.TRF.PWKR.DT.GD.ZS") for i in PEERS}
    usd = {i: wb.series(i, "BX.TRF.PWKR.CD.DT") for i in PEERS}
    y = wb.common_year({**{k + "p": v for k, v in pct.items()},
                        **{k + "u": v for k, v in usd.items()}})
    wb.write(OUT, "ph_ofw_peers.csv",
             ["country", "year", "remittances_pct_gdp", "remittances_usd", "source"],
             sorted([[PEERS[i], y, round(pct[i][y], 2), round(usd[i][y]), wb.SRC]
                     for i in PEERS], key=lambda r: -r[2]))
    print("  peer comparison year: %d" % y)


if __name__ == "__main__":
    main()
