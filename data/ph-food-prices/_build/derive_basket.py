#!/usr/bin/env python3
"""Basket-wide aggregates from the WFP price file, for the food-prices page.

    .venv/bin/python data/ph-food-prices/_build/derive_basket.py

derive_rice.py takes the rice slice of wfp_food_prices_phl.csv for the
rice-prices page. This takes the rest: 62 retail commodities priced per kilo
across 108 markets, monthly, from January 2000.

The published food-prices page carried twenty-eight figures -- +159%, +336%,
+685%, "52 min", "11.2 kg", "₱26,760" -- none of which traced to anything. What
the file actually supports is narrower and more interesting.

The thing that governs every number here is that the dataset's depth is not what
its date range suggests. It runs 2000 to 2026, but only three commodities run the
whole way:

    from 2000-01   3 commodities   pork, and two rice grades
    from 2008-01  11 commodities   the staple vegetables and meats
    from 2012-05   2 commodities
    from 2020-05  46 commodities   most of the file

So a growth rate over a 2020-cohort commodity covers five years including the
2022-23 inflation spike, and is not comparable with a 25-year rate. Every row
here carries its own first and last year for that reason, and the page groups
commodities by cohort rather than ranking them against each other.

Writes:
  ph_food_commodities.csv   one row per retail commodity: span, change, CAGR
  ph_food_cohorts.csv       how many commodities start when
  ph_food_annual.csv        annual national median price, PHP and USD
  ph_food_onions.csv        the 2022-23 onion crisis, month by month
  ph_food_by_region.csv     regional spread for the long-series commodities
  ph_food_categories.csv    coverage by WFP food category
  ph_food_coverage.csv      what this file does and does not support
"""
import csv
import os
import sys

try:
    import duckdb
except ImportError:
    sys.exit("derive_basket.py needs duckdb:  make venv")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..")
SRC = ("WFP Global Food Prices via HDX, wfp_food_prices_phl.csv "
       "(retail, per kilogramme, priceflag=actual)")

# Prices are compared only within these constraints, because mixing them is how
# a basket comparison becomes meaningless: a "Unit" price and a "KG" price are
# not the same measurement, and WFP's own aggregate rows are computed from the
# actual ones and would be double-counted alongside them.
BASE = ("pricetype = 'Retail' and unit = 'KG' and priceflag = 'actual'")

LAST_FULL = 2025          # 2026 is partial in the file; excluded from any change


def main():
    con = duckdb.connect()
    con.execute(
        "create view w as select "
        " try_cast(date as date) d, admin1, market, category, commodity, unit, "
        " priceflag, pricetype, try_cast(price as double) price, "
        " try_cast(usdprice as double) usd "
        "from read_csv('%s/wfp_food_prices_phl.csv', header=true, all_varchar=true)"
        % OUT.replace("'", "''"))
    n = con.execute("select count(*) from w").fetchone()[0]
    if n < 200000:
        raise SystemExit("wfp_food_prices_phl.csv has only %d rows -- the file is "
                         "the system of record and should only grow" % n)
    con.execute("create view r as select * from w where %s" % BASE)

    def write(name, header, rows):
        with open(os.path.join(OUT, name), "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows(rows)
        print("  wrote %-30s %5d rows" % (name, len(rows)))

    def rows(sql):
        return con.execute(sql).fetchall()

    # ---- annual national median per commodity -------------------------------
    con.execute("""create view ann as
        select commodity, category, year(d) y,
               round(median(price), 2) php, round(median(usd), 4) usd,
               count(distinct market) markets, count(*) obs
        from r group by 1, 2, 3""")
    write("ph_food_annual.csv",
          ["commodity", "category", "year", "median_php_per_kg",
           "median_usd_per_kg", "markets", "observations", "source"],
          [list(x) + [SRC] for x in rows(
              "select commodity, category, y, php, usd, markets, obs from ann "
              "order by commodity, y")])

    # ---- per commodity: its own span, and the change across it --------------
    # The change is measured between each commodity's own first and last complete
    # year, never against a fixed 2000 baseline it may not have.
    write("ph_food_commodities.csv",
          ["commodity", "category", "first_year", "last_year", "years",
           "first_php_per_kg", "last_php_per_kg", "change_php_pct",
           "change_usd_pct", "cagr_php_pct", "markets", "observations", "source"],
          [list(x) + [SRC] for x in rows("""
            with f as (
              select commodity, category, min(y) y0, max(y) y1,
                     max(markets) mk, sum(obs) ob
              from ann where y <= %d group by 1, 2)
            select f.commodity, f.category, f.y0, f.y1, f.y1 - f.y0 + 1,
                   s.php, e.php,
                   round(100.0 * (e.php / s.php - 1), 1),
                   round(100.0 * (e.usd / s.usd - 1), 1),
                   round(100.0 * (power(e.php / s.php, 1.0 / (f.y1 - f.y0)) - 1), 2),
                   f.mk, f.ob
            from f
            join ann s on s.commodity = f.commodity and s.y = f.y0
            join ann e on e.commodity = f.commodity and e.y = f.y1
            where f.y1 > f.y0
            order by 8 desc""" % LAST_FULL)])

    # ---- cohorts ------------------------------------------------------------
    write("ph_food_cohorts.csv",
          ["first_month", "commodities", "span_years", "example_commodities",
           "source"],
          [list(x) + [SRC] for x in rows("""
            with f as (select commodity, min(d) mn from r group by 1)
            select strftime(mn, '%%Y-%%m') fm, count(*) nc,
                   %d - min(cast(strftime(mn, '%%Y') as int)) + 1,
                   string_agg(commodity, '; ' order by commodity)
            from f group by 1 order by 1""" % LAST_FULL)])

    # ---- the onion crisis ---------------------------------------------------
    # Red onions cost more per kilo than pork in the Philippines in January 2023.
    # The file records it month by month, so the page shows it rather than
    # describing it.
    write("ph_food_onions.csv",
          ["month", "median_php_per_kg", "highest_market_php", "lowest_market_php",
           "markets", "pork_median_php", "source"],
          [list(x) + [SRC] for x in rows("""
            with o as (select strftime(d, '%Y-%m') m, median(price) p,
                              max(price) hi, min(price) lo, count(distinct market) mk
                       from r where commodity = 'Onions (red)'
                         and d between DATE '2021-01-01' and DATE '2024-12-31'
                       group by 1),
                 k as (select strftime(d, '%Y-%m') m, median(price) p
                       from r where commodity = 'Meat (pork)'
                         and d between DATE '2021-01-01' and DATE '2024-12-31'
                       group by 1)
            select o.m, round(o.p, 2), round(o.hi, 2), round(o.lo, 2), o.mk,
                   round(k.p, 2)
            from o left join k on k.m = o.m order by o.m""")])

    # ---- regional spread, long-series commodities only ----------------------
    write("ph_food_by_region.csv",
          ["commodity", "region", "year", "median_php_per_kg", "markets",
           "observations", "source"],
          [list(x) + [SRC] for x in rows("""
            select commodity, admin1, year(d), round(median(price), 2),
                   count(distinct market), count(*)
            from r
            where year(d) = %d
              and commodity in ('Rice (regular, milled)', 'Meat (pork)',
                                'Meat (chicken, whole)', 'Onions (red)',
                                'Tomatoes', 'Cabbage')
            group by 1, 2, 3
            having count(*) >= 12
            order by commodity, 4 desc""" % LAST_FULL)])

    # ---- categories ---------------------------------------------------------
    write("ph_food_categories.csv",
          ["category", "commodities", "observations", "first_year", "last_year",
           "median_change_php_pct", "source"],
          [list(x) + [SRC] for x in rows("""
            with ch as (
              with f as (select commodity, category, min(y) y0, max(y) y1
                         from ann where y <= %d group by 1, 2)
              select f.category, f.commodity, f.y0, f.y1,
                     100.0 * (e.php / s.php - 1) pct
              from f join ann s on s.commodity = f.commodity and s.y = f.y0
                     join ann e on e.commodity = f.commodity and e.y = f.y1
              where f.y1 > f.y0)
            select category, count(*), 0, min(y0), max(y1),
                   round(median(pct), 1)
            from ch group by 1 order by 6 desc""" % LAST_FULL)])
    # observations per category, filled in separately so the query above stays
    # about price change rather than doing two jobs
    obs = dict(rows("select category, count(*) from r group by 1"))
    p = os.path.join(OUT, "ph_food_categories.csv")
    lines = list(csv.reader(open(p)))
    for row in lines[1:]:
        row[2] = obs.get(row[0], 0)
    with open(p, "w", newline="") as f:
        csv.writer(f).writerows(lines)

    # ---- coverage -----------------------------------------------------------
    tot = con.execute("select count(*) from r").fetchone()[0]
    cov = [
        ["retail per-kilo observations", tot,
         "of %d rows in the file; the rest are wholesale, farm gate, "
         "non-kilo units, or WFP aggregates" % n, SRC],
        ["commodities", con.execute(
            "select count(distinct commodity) from r").fetchone()[0], "", SRC],
        ["markets", con.execute(
            "select count(distinct market) from r").fetchone()[0], "", SRC],
        ["regions", con.execute(
            "select count(distinct admin1) from r").fetchone()[0],
         "the Philippines has 17", SRC],
        ["first month", str(con.execute("select min(d) from r").fetchone()[0]),
         "", SRC],
        ["last month", str(con.execute("select max(d) from r").fetchone()[0]),
         "", SRC],
        ["commodities spanning the whole record", con.execute("""
            select count(*) from (select commodity from r group by 1
            having year(min(d)) <= 2000 and year(max(d)) >= %d)"""
            % LAST_FULL).fetchone()[0],
         "out of %d -- the date range describes the file, not most of its "
         "commodities" % con.execute(
             "select count(distinct commodity) from r").fetchone()[0], SRC],
        ["WFP aggregate rows excluded", con.execute(
            "select count(*) from w where priceflag <> 'actual'").fetchone()[0],
         "computed by WFP from the actual rows; counting both double-counts", SRC],
        ["non-kilogramme rows excluded", con.execute(
            "select count(*) from w where unit <> 'KG'").fetchone()[0],
         "a per-unit price and a per-kilo price are different measurements", SRC],
        ["farm gate observations", con.execute(
            "select count(*) from w where pricetype = 'Farm Gate'").fetchone()[0],
         "one commodity only, so no farm-to-retail margin is computed for the "
         "basket", SRC],
        ["household spending weights", 0,
         "WFP prices carry no consumption weights, so no basket index is built "
         "and no commodity is called typical", SRC],
        ["quality or grade adjustment", 0,
         "a kilo of tomatoes in 2008 and in 2025 are assumed comparable, which "
         "is an assumption and not a measurement", SRC],
        ["2026 in change figures", 0,
         "the file reaches June 2026; partial years are excluded from every "
         "change and growth rate", SRC],
    ]
    write("ph_food_coverage.csv", ["property", "value", "note", "source"], cov)


if __name__ == "__main__":
    main()
