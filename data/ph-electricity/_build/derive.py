#!/usr/bin/env python3
"""Aggregates the electricity page was not using.

    .venv/bin/python data/ph-electricity/_build/derive.py

The page shipped with three charts, all about coal. ph_generation_mix.csv holds
eight fuels across twenty-six years and sea_coal_share.csv holds six peers over
the same period; only the latest coal figures were on the page.

The rollup below is what that omission was hiding: renewables were 42.9% of
Philippine generation in 2000 and are 23.3% now. The country did not fail to
build renewables so much as it added coal far faster than anything else, against
a base that was already largely hydro and geothermal. That is a different -- and
more accurate -- story than "coal is rising".

Geothermal sits inside Ember's "Other renewables" bucket for the Philippines,
which is why that category is unusually large here and is labelled rather than
silently folded into a renewables total.
"""
import csv
import os

import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
RENEW = ("Hydro", "Solar", "Wind", "Bioenergy", "Other renewables")
FOSSIL = ("Coal", "Gas", "Other fossil")
SRC = "Ember yearly electricity"


def write(name, cols, rows):
    with open(os.path.join(D, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    con = duckdb.connect()
    con.execute("create view g as select * from read_csv('%s/ph_generation_mix.csv', "
                "header=true, union_by_name=true)" % D)
    fuels = {r[0] for r in con.execute("select distinct fuel from g").fetchall()}
    unknown = fuels - set(RENEW) - set(FOSSIL)
    if unknown:
        raise SystemExit("unclassified fuel(s): %s -- add them to RENEW or FOSSIL "
                         "rather than letting them fall out of the totals"
                         % ", ".join(sorted(unknown)))

    rows = con.execute("""
        select year,
               round(sum(case when fuel in %s then share_pct else 0 end), 2) renewable_pct,
               round(sum(case when fuel in %s then share_pct else 0 end), 2) fossil_pct,
               round(sum(case when fuel in %s then generation_twh else 0 end), 2) renewable_twh,
               round(sum(case when fuel in %s then generation_twh else 0 end), 2) fossil_twh,
               round(sum(generation_twh), 2) total_twh
        from g group by year order by year""" % (RENEW, FOSSIL, RENEW, FOSSIL)).fetchall()
    write("ph_generation_rollup.csv",
          ["year", "renewable_pct", "fossil_pct", "renewable_twh", "fossil_twh",
           "total_twh", "source"], [list(r) + [SRC] for r in rows])

    # Meralco coverage: which months were found and which were not. The rate
    # series has gaps and a chart that joins across them implies months that
    # were never published.
    con.execute("create view c as select * from read_csv('%s/ph_meralco_coverage.csv', "
                "header=true, union_by_name=true)" % D)
    rows = con.execute("""
        select status, count(*) as n_months from c group by status order by n_months desc
    """).fetchall()
    write("ph_meralco_status.csv", ["status", "months", "source"],
          [list(r) + ["Meralco rate advisory"] for r in rows])


if __name__ == "__main__":
    main()
