#!/usr/bin/env python3
"""Philippine COVID-19 series from Our World in Data.

    .venv/bin/python data/ph-covid/_build/fetch_owid.py

OWID's compact table is the only open source that carries cases, deaths,
testing, stringency, excess mortality and vaccinations for every country on one
consistent date index. It is ~180 MB of every country, so this script streams it
to a temporary file, filters with DuckDB, and writes only the Philippine rows
plus a small ASEAN comparison set.

The reason this pipeline exists, rather than a page quoting OWID from memory:
the page it replaces carried a total case count taken from May 2023, a death
count from January 2024 and a vaccination count from December 2022, presented
side by side as one snapshot. Every figure was individually close to real and
the set was mutually impossible. Pinning all of them to one as_of date, carried
on every row, makes that specific failure visible instead of invisible.

Two OWID conventions worth knowing before reading anything downstream:

* Cumulative columns are forward-filled, so total_cases on a date with no report
  repeats the previous value. Differencing them is safe; treating a flat stretch
  as "no cases that week" is not.
* Reporting moved from daily to weekly in 2023 and stopped entirely in most
  countries after that. The tail of the series is therefore sparse by design,
  and the coverage CSV records the last date each metric actually moved so a
  chart does not present a reporting change as an epidemiological one.
"""
import csv
import os
import ssl
import sys
import tempfile
import urllib.request

try:
    import duckdb
except ImportError:
    sys.exit("needs duckdb:  make venv")

URL = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
OUT = os.path.join(os.path.dirname(__file__), "..")
SRC = "Our World in Data, compact.csv"
# Comparators are the ASEAN-6 with populations large enough that per-million
# rates are stable. Brunei, Laos, Cambodia and Timor-Leste are omitted for that
# reason and the page says so rather than implying ASEAN is six countries.
ASEAN = ["Philippines", "Indonesia", "Vietnam", "Thailand", "Malaysia", "Singapore"]
UA = "allanninal.dev research (contact via github.com/allanninal)"


def download(path):
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=600, context=ctx) as r, open(path, "wb") as fh:
        n = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            n += len(chunk)
            print("\r  downloaded %.0f MB" % (n / 1e6), end="", file=sys.stderr)
    print(file=sys.stderr)
    return n


def write(name, cols, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.close()
    try:
        download(tmp.name)
        con = duckdb.connect()
        con.execute("create view raw as select * from read_csv('%s', header=true, "
                    "union_by_name=true, ignore_errors=true)" % tmp.name)
        con.execute("create view ph as select * from raw where country = 'Philippines'")

        as_of = con.execute("select max(date) from ph").fetchone()[0]
        print("  as_of %s" % as_of)

        # ---- daily series
        rows = con.execute("""
            select date, total_cases, new_cases, new_cases_smoothed,
                   total_deaths, new_deaths, new_deaths_smoothed,
                   stringency_index, reproduction_rate, positive_rate,
                   new_tests_smoothed, people_vaccinated, people_fully_vaccinated,
                   total_boosters
            from ph order by date""").fetchall()
        write("ph_covid_daily.csv",
              ["date", "total_cases", "new_cases", "new_cases_smoothed",
               "total_deaths", "new_deaths", "new_deaths_smoothed",
               "stringency_index", "reproduction_rate", "positive_rate",
               "new_tests_smoothed", "people_vaccinated", "people_fully_vaccinated",
               "total_boosters", "as_of", "source"],
              [list(r) + [as_of, SRC] for r in rows])

        # ---- one consistent headline snapshot. Every figure below is read at
        #      the same as_of date; that is the entire point of this table.
        head = con.execute("""
            select max(total_cases), max(total_deaths),
                   max(people_vaccinated), max(people_fully_vaccinated),
                   max(total_boosters),
                   max(excess_mortality_cumulative_absolute)
            from ph""").fetchone()
        write("ph_covid_headline.csv",
              ["metric", "value", "as_of", "source"],
              [["total_cases", head[0], as_of, SRC],
               ["total_deaths", head[1], as_of, SRC],
               ["people_vaccinated", int(head[2]) if head[2] else "", as_of, SRC],
               ["people_fully_vaccinated", int(head[3]) if head[3] else "", as_of, SRC],
               ["total_boosters", int(head[4]) if head[4] else "", as_of, SRC],
               ["excess_deaths_cumulative", int(head[5]) if head[5] else "", as_of, SRC],
               ["case_fatality_pct", round(100.0 * head[1] / head[0], 2), as_of, SRC]])

        # ---- annual
        rows = con.execute("""
            select year(date) y, sum(coalesce(new_cases,0)), sum(coalesce(new_deaths,0)),
                   max(new_cases), round(avg(stringency_index), 1)
            from ph group by y order by y""").fetchall()
        write("ph_covid_annual.csv",
              ["year", "cases", "deaths", "peak_daily_cases", "mean_stringency",
               "as_of", "source"],
              [list(r) + [as_of, SRC] for r in rows])

        # ---- ASEAN comparison, per million so size does not decide the ranking
        rows = con.execute("""
            select country,
                   max(total_cases), max(total_cases_per_million),
                   max(total_deaths), max(total_deaths_per_million),
                   max(people_fully_vaccinated_per_hundred)
            from raw where country in (%s)
            group by country order by max(total_deaths_per_million) desc
        """ % ",".join("'%s'" % c for c in ASEAN)).fetchall()
        write("ph_covid_asean.csv",
              ["country", "total_cases", "cases_per_million", "total_deaths",
               "deaths_per_million", "fully_vaccinated_per_hundred", "as_of", "source"],
              [list(r) + [as_of, SRC] for r in rows])

        # ---- coverage: the last date each metric actually moved. Reporting went
        #      weekly and then stopped; without this a chart reads the end of
        #      reporting as the end of the pandemic.
        rows = []
        for col in ["new_cases", "new_deaths", "stringency_index", "positive_rate",
                    "new_tests_smoothed", "people_fully_vaccinated", "reproduction_rate"]:
            r = con.execute("select min(date), max(date), count(%s) from ph where %s is not null"
                            % (col, col)).fetchone()
            rows.append([col, r[0], r[1], r[2], as_of, SRC])
        write("ph_covid_coverage.csv",
              ["metric", "first_date", "last_date", "non_null_days", "as_of", "source"], rows)
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    main()
