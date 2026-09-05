#!/usr/bin/env python3
"""European grid generation and prices at native resolution, for one year.

Fraunhofer ISE's Energy-Charts API, CC BY 4.0, no key. Two endpoints:

  public_power?country=..   generation by source, 15-minute or hourly depending on
                            the country, from ENTSO-E transparency data
  price?bzn=..              day-ahead market price per bidding zone, EUR/MWh

The Philippine electricity page established the method this extends: renewables
fell from 42.89% to 23.32% of generation while renewable output nearly doubled,
because demand grew faster. That is a story an annual percentage can tell.

What an annual percentage cannot tell you is that the renewable share is a
distribution, not a number. At hourly resolution a decarbonised grid spends part of
the year with renewables covering almost everything and part of it covering almost
nothing, and both tails are invisible in the mean. The negative-price hours are the
first tail made visible in money: when there is more must-run generation than
demand, the price to deliver a megawatt-hour goes below zero.

The second finding is that this is not a German phenomenon. On a single day in June
2025 the minimum price in Germany, France, Belgium and Austria was identical to the
cent -- minus 20.41 EUR/MWh -- because the day-ahead markets are coupled and the
same price forms across them when nothing is congested.

One honest limit shapes the comparison: resolution is not uniform. Spain, Poland,
the Netherlands and Austria return 15-minute data; France, Denmark, Belgium and
Italy return hourly. Everything here is aggregated to hourly so the countries can
be compared at all, and the coverage file records which is which.

Writes:
  gg_hourly.csv          one row per country-hour: load, renewable, fossil, share
  gg_country.csv         per country: annual share, and the distribution behind it
  gg_share_hist.csv      hours in each 10-point band of renewable share
  gg_price.csv           one row per zone-hour
  gg_price_country.csv   per zone: negative hours, mean, extremes
  gg_dunkelflaute.csv    the worst renewable week per country, and what filled it
  gg_sources.csv         generation by source and country for the year
  gg_coverage.csv        resolution per country, and what the data does not carry
"""
import calendar
import csv
import datetime
import json
import os
import time
import urllib.error
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(os.path.dirname(__file__), ".cache")
API = "https://api.energy-charts.info"
UA = "allanninal.dev research (https://www.allanninal.dev)"
SRC = ("Fraunhofer ISE Energy-Charts (ENTSO-E transparency; prices from "
       "Bundesnetzagentur / SMARD), CC BY 4.0")

YEAR = 2025
# Paced deliberately. The API answers "Too Many Requests" after a handful of quick
# calls, and a whole year needs about two hundred of them.
PAUSE = 7.0

COUNTRIES = [
    ("de", "Germany", "DE-LU"), ("fr", "France", "FR"),
    ("es", "Spain", "ES"), ("pl", "Poland", "PL"),
    ("nl", "Netherlands", "NL"), ("be", "Belgium", "BE"),
    ("at", "Austria", "AT"), ("it", "Italy", "IT-North"),
]

# Which production types count as renewable. Named explicitly rather than matched
# on a substring: "Fossil coal-derived gas" contains "gas" and is not renewable,
# and "Hydro pumped storage" is storage rather than generation -- counting it as
# renewable would double-count the electricity used to fill it.
RENEWABLE = {
    "Wind onshore", "Wind offshore", "Solar", "Hydro Run-of-River",
    "Hydro water reservoir", "Biomass", "Geothermal", "Waste",
    "Renewable share of load", "Hydro", "Wind",
}
FOSSIL = {
    "Fossil brown coal / lignite", "Fossil hard coal", "Fossil oil",
    "Fossil gas", "Fossil coal-derived gas", "Fossil peat", "Fossil oil shale",
    "Others", "Other fossil",
}
NUCLEAR = {"Nuclear"}
# Excluded from every total: storage flows and trade are not generation.
NOT_GENERATION = {
    "Hydro pumped storage", "Hydro pumped storage consumption",
    "Cross border electricity trading", "Load", "Residual load",
    "Renewable share of generation", "Renewable share of load",
}


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-24s %7d rows" % (name, len(rows)))


def get(path, key):
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, key + ".json")
    if os.path.exists(cf):
        return json.load(open(cf))
    for attempt in range(6):
        try:
            req = urllib.request.Request(API + path, headers={"User-Agent": UA})
            body = urllib.request.urlopen(req, timeout=180).read()
            d = json.loads(body)
            if isinstance(d, str):
                raise SystemExit("%s -> %s" % (path, d[:120]))
            json.dump(d, open(cf, "w"))
            time.sleep(PAUSE)
            return d
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            if attempt == 5:
                raise SystemExit("%s -> HTTP %s" % (path, e.code))
            time.sleep(10 * (attempt + 1))
        except Exception as e:                                   # noqa: BLE001
            if attempt == 5:
                raise SystemExit("%s -> %s" % (path, e))
            time.sleep(10 * (attempt + 1))


def months(year):
    for m in range(1, 13):
        last = calendar.monthrange(year, m)[1]
        yield (m, "%04d-%02d-01" % (year, m), "%04d-%02d-%02d" % (year, m, last))


def to_hourly(seconds, series):
    """Average each named series into clock hours.

    Countries report at 15-minute or hourly resolution and the comparison has to
    be like for like, so everything is averaged to the hour. Averaging rather than
    summing keeps the unit as power (MW) rather than turning it into energy, which
    matters because the shares below are ratios of simultaneous power.
    """
    buckets = {}
    for i, sec in enumerate(seconds):
        h = sec - (sec % 3600)
        b = buckets.setdefault(h, {})
        for name, data in series.items():
            v = data[i] if i < len(data) else None
            if v is None:
                continue
            acc = b.setdefault(name, [0.0, 0])
            acc[0] += v
            acc[1] += 1
    out = {}
    for h, b in buckets.items():
        out[h] = {n: (t / c) for n, (t, c) in b.items() if c}
    return out


def main():
    hourly_rows, native_res = [], {}
    src_totals = {}

    for code, name, _bzn in COUNTRIES:
        per_hour = {}
        for m, s, e in months(YEAR):
            d = get("/public_power?country=%s&start=%s&end=%s" % (code, s, e),
                    "gen_%s_%04d%02d" % (code, YEAR, m))
            secs = d.get("unix_seconds") or []
            if not secs:
                continue
            series = {t["name"]: t["data"] for t in d.get("production_types", [])}
            # Native resolution: seconds between the first two samples.
            if len(secs) > 1:
                native_res.setdefault(code, set()).add(secs[1] - secs[0])
            per_hour.update(to_hourly(secs, series))
            print("    %-12s %04d-%02d  %6d samples" % (name, YEAR, m, len(secs)))

        for h in sorted(per_hour):
            b = per_hour[h]
            gen = {k: v for k, v in b.items() if k not in NOT_GENERATION}
            total = sum(v for v in gen.values() if v and v > 0)
            if total <= 0:
                continue
            ren = sum(v for k, v in gen.items() if k in RENEWABLE and v and v > 0)
            fos = sum(v for k, v in gen.items() if k in FOSSIL and v and v > 0)
            nuc = sum(v for k, v in gen.items() if k in NUCLEAR and v and v > 0)
            load = b.get("Load")
            for k, v in gen.items():
                if v and v > 0:
                    key = (code, k)
                    src_totals[key] = src_totals.get(key, 0.0) + v
            hourly_rows.append([
                code, name,
                datetime.datetime.fromtimestamp(h, datetime.timezone.utc).strftime("%Y-%m-%d %H:00"),
                round(total, 1), round(ren, 1), round(fos, 1), round(nuc, 1),
                round(load, 1) if load else "",
                round(100.0 * ren / total, 2), SRC])

    write("gg_hourly.csv",
          ["country_code", "country", "hour_utc", "generation_mw", "renewable_mw",
           "fossil_mw", "nuclear_mw", "load_mw", "renewable_pct", "source"],
          hourly_rows)

    # ---- per country: the annual number, and the distribution behind it -------
    crows, hist, dunkel = [], [], []
    for code, name, _bzn in COUNTRIES:
        mine = [r for r in hourly_rows if r[0] == code]
        if not mine:
            continue
        shares = sorted(r[8] for r in mine)
        tot_gen = sum(r[3] for r in mine)
        tot_ren = sum(r[4] for r in mine)

        def q(p):
            return shares[min(len(shares) - 1, int(p * (len(shares) - 1)))]

        crows.append([
            code, name, len(mine),
            round(100.0 * tot_ren / tot_gen, 2),      # energy-weighted annual share
            round(sum(shares) / len(shares), 2),      # mean of the hourly shares
            q(0.0), q(0.05), q(0.5), q(0.95), q(1.0),
            sum(1 for x in shares if x >= 80),
            sum(1 for x in shares if x <= 20),
            SRC])

        for lo in range(0, 100, 10):
            n = sum(1 for x in shares if lo <= x < lo + 10)
            hist.append([code, name, lo, lo + 10, n,
                         round(100.0 * n / len(shares), 2), SRC])
        n100 = sum(1 for x in shares if x >= 100)
        hist.append([code, name, 100, 999, n100,
                     round(100.0 * n100 / len(shares), 2), SRC])

        # ---- the worst renewable week ----------------------------------------
        # A rolling 168-hour window over the ordered series, so the answer is a
        # real calendar week rather than an arbitrary Monday-to-Sunday slice.
        best = None
        for i in range(0, max(1, len(mine) - 168)):
            w = mine[i:i + 168]
            if len(w) < 168:
                break
            s = sum(x[4] for x in w) / sum(x[3] for x in w) * 100.0
            if best is None or s < best[0]:
                best = (s, w)
        if best:
            s, w = best
            dunkel.append([
                code, name, w[0][2], w[-1][2], round(s, 2),
                round(sum(x[5] for x in w) / sum(x[3] for x in w) * 100.0, 2),
                round(sum(x[6] for x in w) / sum(x[3] for x in w) * 100.0, 2),
                round(min(x[8] for x in w), 2),
                round(100.0 * tot_ren / tot_gen, 2), SRC])

    write("gg_country.csv",
          ["country_code", "country", "hours", "annual_renewable_pct",
           "mean_hourly_pct", "min_pct", "p5_pct", "median_pct", "p95_pct",
           "max_pct", "hours_at_or_above_80", "hours_at_or_below_20", "source"],
          crows)
    write("gg_share_hist.csv",
          ["country_code", "country", "band_from", "band_to", "hours",
           "pct_of_hours", "source"], hist)
    write("gg_dunkelflaute.csv",
          ["country_code", "country", "week_from", "week_to",
           "week_renewable_pct", "week_fossil_pct", "week_nuclear_pct",
           "worst_hour_pct", "annual_renewable_pct", "source"], dunkel)

    write("gg_sources.csv",
          ["country_code", "country", "production_type", "category",
           "mean_mw", "source"],
          sorted(([c, dict((a, b) for a, b, _ in COUNTRIES)[c], k,
                   ("renewable" if k in RENEWABLE else
                    "fossil" if k in FOSSIL else
                    "nuclear" if k in NUCLEAR else "other"),
                   round(v / max(1, sum(1 for r in hourly_rows if r[0] == c)), 1),
                   SRC]
                  for (c, k), v in src_totals.items()),
                 key=lambda r: (r[1], -r[4])))

    # ---- prices ---------------------------------------------------------------
    prows = []
    for code, name, bzn in COUNTRIES:
        for m, s, e in months(YEAR):
            d = get("/price?bzn=%s&start=%s&end=%s" % (bzn, s, e),
                    "price_%s_%04d%02d" % (bzn, YEAR, m))
            secs = d.get("unix_seconds") or []
            px = d.get("price") or []
            for i, sec in enumerate(secs):
                if i >= len(px) or px[i] is None:
                    continue
                prows.append([
                    bzn, name,
                    datetime.datetime.fromtimestamp(sec, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    round(px[i], 2), d.get("unit", "EUR / MWh"), SRC])
            print("    price %-9s %04d-%02d  %5d" % (bzn, YEAR, m, len(secs)))
    write("gg_price.csv",
          ["bidding_zone", "country", "timestamp_utc", "price", "unit", "source"],
          prows)

    procs = []
    for code, name, bzn in COUNTRIES:
        mine = [r for r in prows if r[0] == bzn]
        if not mine:
            continue
        vals = sorted(r[3] for r in mine)
        neg = [x for x in vals if x < 0]
        procs.append([bzn, name, len(mine), len(neg),
                      round(100.0 * len(neg) / len(mine), 2),
                      round(sum(vals) / len(vals), 2),
                      vals[0], vals[-1],
                      round(sum(neg) / len(neg), 2) if neg else "", SRC])
    procs.sort(key=lambda r: -r[4])
    write("gg_price_country.csv",
          ["bidding_zone", "country", "intervals", "negative_intervals",
           "negative_pct", "mean_price", "min_price", "max_price",
           "mean_when_negative", "source"], procs)

    # ---- coverage -------------------------------------------------------------
    cov = [["countries", len(COUNTRIES), "", SRC],
           ["year", YEAR, "one complete calendar year", SRC],
           ["country-hours", len(hourly_rows), "", SRC],
           ["price intervals", len(prows), "", SRC]]
    for code, name, _b in COUNTRIES:
        res = sorted(native_res.get(code, []))
        label = "/".join("%dmin" % (s // 60) for s in res) or "unknown"
        cov.append(["native resolution: %s" % name, label,
                    "aggregated to hourly for comparability", SRC])
    cov += [
        ["everything aggregated to hourly", 1,
         "countries report at 15-minute or hourly resolution; comparing them "
         "requires one grid, and averaging preserves power rather than turning it "
         "into energy", SRC],
        ["storage counted as generation", 0,
         "pumped-storage output and consumption are both excluded. Counting the "
         "output as renewable would double-count the electricity used to fill it", SRC],
        ["imports counted as generation", 0,
         "cross-border trade is excluded, so a share here is of domestic "
         "generation and not of domestic consumption -- a country importing "
         "renewable power looks less renewable than its consumption is", SRC],
        ["distribution-level solar included", 0,
         "ENTSO-E transparency covers transmission-connected plant. Rooftop solar "
         "is largely invisible, which understates the solar share in every country "
         "here and understates it most in the sunniest ones", SRC],
        ["timestamps are UTC, year boundaries are local", 1,
         "the API takes start and end in the market's local time, so a request for "
         "a calendar year returns a series labelled from 23:00 on 31 December -- "
         "central European time is UTC+1 in winter. It is a full local year", SRC],
        ["prices are day-ahead", 1,
         "the day-ahead auction, not intraday or balancing. A negative day-ahead "
         "price is a real settled price, not a modelled one", SRC],
        ["curtailment", 0,
         "generation that was paid to switch off does not appear as generation, so "
         "the renewable share understates what was available", SRC],
    ]
    write("gg_coverage.csv", ["property", "value", "note", "source"], cov)


if __name__ == "__main__":
    main()
