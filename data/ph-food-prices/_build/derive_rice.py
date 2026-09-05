#!/usr/bin/env python3
"""Extra rice aggregates the page was not using.

    .venv/bin/python data/ph-food-prices/_build/derive_rice.py

The rice page shipped with three charts drawn from two of the six CSVs in this
directory. wfp_food_prices_phl.csv alone holds 234,015 observations across 108
markets, 17 regions and six distinct rice commodities, and none of the regional
or varietal structure was on the page. This adds it.

No network access; everything here reads the committed CSVs.
"""
import csv
import os

import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
SRC = "WFP via HDX"


def write(name, cols, rows):
    with open(os.path.join(D, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    con = duckdb.connect()
    con.execute("create view w as select * from read_csv('%s/wfp_food_prices_phl.csv', "
                "header=true, union_by_name=true, ignore_errors=true)" % D)
    # Retail rice only, and only the price flag WFP marks as actual -- the file
    # also carries aggregated and forecast rows, and mixing them would blend
    # observations with estimates.
    con.execute("""create view rice as
        select * from w
        where commodity ilike 'Rice%' and lower(pricetype) = 'retail'
          and lower(priceflag) = 'actual' and price is not null and price > 0""")
    n = con.execute("select count(*) from rice").fetchone()[0]
    print("  %d retail rice observations" % n)
    if not n:
        raise SystemExit("no retail rice rows -- the priceflag/pricetype vocabulary "
                         "changed and the filter now matches nothing")

    latest = con.execute("select max(year(date)) from rice").fetchone()[0]
    full = con.execute("""select max(y) from (
        select year(date) y, count(distinct month(date)) m from rice group by y
        having count(distinct month(date)) >= 10)""").fetchone()[0]
    print("  latest year %d; latest reasonably complete year %d" % (latest, full))

    # -- by region, most recent complete year
    rows = con.execute("""
        select admin1, round(avg(price), 2) mean_php_kg,
               round(median(price), 2) median_php_kg,
               count(*) observations, count(distinct market) markets
        from rice where year(date) = ? and admin1 is not null
        group by admin1 having count(*) >= 12
        order by mean_php_kg desc""", [full]).fetchall()
    write("ph_rice_by_region.csv",
          ["region", "mean_php_kg", "median_php_kg", "observations", "markets",
           "year", "source"],
          [list(r) + [full, SRC] for r in rows])

    # -- by variety over time. Varieties are separate commodities in WFP, and a
    #    national "rice price" that averages across them moves when the mix of
    #    reporting markets changes rather than when prices do.
    rows = con.execute("""
        select commodity, year(date) y, round(avg(price), 2) mean_php_kg, count(*) n
        from rice group by commodity, y
        having count(*) >= 12 order by commodity, y""").fetchall()
    write("ph_rice_by_variety.csv",
          ["commodity", "year", "mean_php_kg", "observations", "source"],
          [list(r) + [SRC] for r in rows])

    # -- market coverage over time: how many markets actually reported. A price
    #    series whose panel is shrinking is partly measuring the panel.
    rows = con.execute("""
        select year(date) y, count(distinct market) markets,
               count(distinct admin1) regions, count(*) observations
        from rice group by y order by y""").fetchall()
    write("ph_rice_market_coverage.csv",
          ["year", "markets", "regions", "observations", "source"],
          [list(r) + [SRC] for r in rows])

    # -- the margin chain, from the annual farmgate/wholesale/retail table
    con.execute("create view a as select * from read_csv('%s/ph_rice_annual.csv', "
                "header=true, union_by_name=true)" % D)
    rows = con.execute("""
        select year, farmgate_php_kg, wholesale_php_kg, retail_php_kg,
               round(wholesale_php_kg - farmgate_php_kg, 2) farm_to_wholesale,
               round(retail_php_kg - wholesale_php_kg, 2) wholesale_to_retail,
               round(retail_php_kg - farmgate_php_kg, 2) farm_to_retail,
               round(100.0 * farmgate_php_kg / retail_php_kg, 1) farmer_share_pct
        from a
        where farmgate_php_kg is not null and wholesale_php_kg is not null
          and retail_php_kg is not null and retail_php_kg > 0
        order by year""").fetchall()
    if not rows:
        raise SystemExit("no year has all three of farmgate, wholesale and retail")
    write("ph_rice_margin_chain.csv",
          ["year", "farmgate_php_kg", "wholesale_php_kg", "retail_php_kg",
           "farm_to_wholesale", "wholesale_to_retail", "farm_to_retail",
           "farmer_share_pct", "source"],
          [list(r) + ["WFP via HDX; DA Bantay Presyo"] for r in rows])


if __name__ == "__main__":
    main()
