#!/usr/bin/env python3
"""2015 Philippine Family Income and Expenditure Survey, from the public copy.

    .venv/bin/python data/ph-fies/_build/fetch_fies.py

PSA runs FIES and psa.gov.ph sits behind a managed challenge that scripts do not
pass. The public microdata is mirrored on Kaggle, which serves it without
authentication, and the page it feeds already cited that mirror -- it had simply
never been opened. 41,544 households, 60 columns.

Two properties that shape everything downstream:

* These are UNWEIGHTED household records. FIES ships sampling weights so results
  can be grossed up to the population; this public extract does not include
  them. Every figure here therefore describes the 41,544 sampled households, not
  the country, and the page says so rather than implying national totals.

* Income and expenditure are annual pesos for 2015, and the distribution is very
  right-skewed. The mean sits well above the median, so medians are used
  throughout and the mean is shown only where the gap between them is the point.

Only aggregates are written out. The microdata itself is not committed: it is
22 MB, it is redistributable but not ours, and a checked-in copy would go stale
against the mirror without anyone noticing.
"""
import csv
import io
import os
import ssl
import sys
import urllib.request
import zipfile

try:
    import duckdb
except ImportError:
    raise SystemExit("needs duckdb:  make venv")

OUT = os.path.join(os.path.dirname(__file__), "..")
URL = ("https://www.kaggle.com/api/v1/datasets/download/"
       "grosvenpaul/family-income-and-expenditure")
MEMBER = "Family Income and Expenditure.csv"
SRC = "PSA FIES 2015 via Kaggle (grosvenpaul/family-income-and-expenditure)"
UA = "allanninal.dev research (contact via github.com/allanninal)"

# Expenditure columns that partition household spending. Named explicitly: the
# file also carries subtotals such as Total Food Expenditure, and summing those
# alongside their components double-counts.
SPEND = [
    ("Bread and Cereals Expenditure", "bread and cereals"),
    ("Total Rice Expenditure", "rice"),
    ("Meat Expenditure", "meat"),
    ("Total Fish and  marine products Expenditure", "fish and seafood"),
    ("Fruit Expenditure", "fruit"),
    ("Vegetables Expenditure", "vegetables"),
    ("Restaurant and hotels Expenditure", "restaurants and hotels"),
    ("Alcoholic Beverages Expenditure", "alcohol"),
    ("Tobacco Expenditure", "tobacco"),
    ("Clothing, Footwear and Other Wear Expenditure", "clothing and footwear"),
    ("Housing and water Expenditure", "housing and water"),
    ("Medical Care Expenditure", "medical care"),
    ("Transportation Expenditure", "transport"),
    ("Communication Expenditure", "communication"),
    ("Education Expenditure", "education"),
    ("Miscellaneous Goods and Services Expenditure", "miscellaneous"),
    ("Special Occasions Expenditure", "special occasions"),
]


def download():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300,
                                context=ssl.create_default_context()) as r:
        blob = r.read()
    print("  downloaded %.1f MB" % (len(blob) / 1e6), file=sys.stderr)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = [n for n in z.namelist() if n.endswith(MEMBER)]
        if not names:
            raise SystemExit("%s not in the archive; it holds %s"
                             % (MEMBER, z.namelist()))
        return z.read(names[0])


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    import tempfile
    blob = download()
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.write(blob)
    tmp.close()
    try:
        con = duckdb.connect()
        con.execute("create view f as select * from read_csv('%s', header=true, "
                    "union_by_name=true, ignore_errors=true, sample_size=-1)" % tmp.name)
        n = con.execute("select count(*) from f").fetchone()[0]
        print("  %d households" % n)
        if n < 40000:
            raise SystemExit("only %d rows -- the mirror changed shape" % n)

        con.execute('''create view h as select
            "Total Household Income"::double income,
            "Total Food Expenditure"::double food,
            "Region" region,
            "Main Source of Income" income_source,
            "Household Head Sex" head_sex,
            "Household Head Age"::int head_age,
            "Household Head Highest Grade Completed" head_education,
            "Total Number of Family members"::int members,
            "Agricultural Household indicator"::int agri
            from f where "Total Household Income" is not null''')

        # -- income deciles. Computed here rather than on the page so the cut
        #    points are in a CSV somebody can argue with.
        rows = con.execute('''
            with d as (select income, ntile(10) over (order by income) as decile_n from h)
            select decile_n, count(*) households,
                   round(min(income)) min_income, round(max(income)) max_income,
                   round(median(income)) median_income, round(avg(income)) mean_income,
                   round(100.0 * sum(income) / (select sum(income) from h), 2) income_share_pct
            from d group by decile_n order by decile_n''').fetchall()
        write("ph_fies_deciles.csv",
              ["decile", "households", "min_income", "max_income", "median_income",
               "mean_income", "income_share_pct", "source"],
              [list(r) + [SRC] for r in rows])

        # -- headline distribution
        rows = con.execute('''select
            count(*) households,
            round(median(income)) median_income,
            round(avg(income)) mean_income,
            round(quantile_cont(income, 0.10)) p10,
            round(quantile_cont(income, 0.90)) p90,
            round(min(income)) min_income, round(max(income)) max_income,
            round(median(food)) median_food,
            round(median(members), 1) median_members
            from h''').fetchone()
        write("ph_fies_headline.csv",
              ["metric", "value", "source"],
              [[k, v, SRC] for k, v in zip(
                  ["households", "median_income", "mean_income", "p10_income",
                   "p90_income", "min_income", "max_income", "median_food_spend",
                   "median_household_size"], rows)])

        # -- food share of income by decile: Engel's law, testable here
        rows = con.execute('''
            with d as (select income, food, ntile(10) over (order by income) as decile_n from h)
            select decile_n, round(median(100.0 * food / nullif(income, 0)), 2) median_food_share_pct,
                   round(median(food)) median_food, round(median(income)) median_income
            from d group by decile_n order by decile_n''').fetchall()
        write("ph_fies_food_share.csv",
              ["decile", "median_food_share_pct", "median_food", "median_income",
               "source"], [list(r) + [SRC] for r in rows])

        # -- spending mix, poorest decile against richest
        parts = []
        for col, label in SPEND:
            r = con.execute('''
                with d as (select "%s"::double amt,
                                  ntile(10) over (order by "Total Household Income") as decile_n
                           from f where "Total Household Income" is not null)
                select round(median(case when decile_n = 1 then amt end)) poorest,
                       round(median(case when decile_n = 10 then amt end)) richest
                from d''' % col).fetchone()
            parts.append([label, r[0] or 0, r[1] or 0, SRC])
        write("ph_fies_spending.csv",
              ["category", "median_poorest_decile", "median_richest_decile", "source"],
              sorted(parts, key=lambda x: -(x[2] or 0)))

        # -- Gini from the microdata, by the standard covariance form. Computed
        #    here rather than quoted from elsewhere so the page's inequality
        #    number and its decile table come from the same 41,544 rows.
        gini = con.execute('''
            with r as (select income, row_number() over (order by income) i,
                              count(*) over () n, sum(income) over () tot from h)
            select round((2.0 * sum(i * income)) / (n * tot) - (n + 1.0) / n, 4)
            from r group by n, tot''').fetchone()[0]
        top1 = con.execute('''
            with r as (select income, ntile(100) over (order by income) pct from h)
            select round(100.0 * sum(case when pct = 100 then income else 0 end)
                       / sum(income), 2) from r''').fetchone()[0]
        agri = con.execute('''select round(median(income)) from h where agri = 1''').fetchone()[0]
        nonagri = con.execute('''select round(median(income)) from h where agri = 0''').fetchone()[0]
        write("ph_fies_inequality.csv",
              ["metric", "value", "note", "source"],
              [["gini", gini, "computed from the 41,544 unweighted household records", SRC],
               ["top_1pct_income_share", top1, "", SRC],
               ["median_income_agricultural", agri, "", SRC],
               ["median_income_non_agricultural", nonagri, "", SRC]])

        # -- by region
        rows = con.execute('''select region, count(*) households,
                   round(median(income)) median_income,
                   round(median(100.0 * food / nullif(income, 0)), 2) median_food_share_pct
            from h group by region having count(*) >= 200
            order by median_income desc''').fetchall()
        write("ph_fies_regions.csv",
              ["region", "households", "median_income", "median_food_share_pct",
               "source"], [list(r) + [SRC] for r in rows])

        # -- household head characteristics
        rows = con.execute('''select head_sex, count(*) households,
                   round(median(income)) median_income,
                   round(median(members), 1) median_members
            from h where head_sex is not null group by head_sex
            order by households desc''').fetchall()
        write("ph_fies_head_sex.csv",
              ["head_sex", "households", "median_income", "median_members", "source"],
              [list(r) + [SRC] for r in rows])

        rows = con.execute('''select income_source, count(*) households,
                   round(median(income)) median_income
            from h where income_source is not null group by income_source
            having count(*) >= 100 order by households desc''').fetchall()
        write("ph_fies_income_source.csv",
              ["income_source", "households", "median_income", "source"],
              [list(r) + [SRC] for r in rows])
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    main()
