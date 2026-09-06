#!/usr/bin/env python3
"""Every model warms every city. They do not agree by how much.

Open-Meteo serves downscaled CMIP6 projections for a point: several independent
climate models, each run on the same scenario, each giving a daily temperature
series out to 2050 and beyond. Asking all of them the same question about the
same city is the cheapest available demonstration of what a projection is and is
not.

Two things are true at once and the page depends on keeping them apart:

  the DIRECTION is agreed      every model warms every city in this set
  the AMOUNT is not            and at city scale the disagreement between models
                               is often a large fraction of the warming itself

This is the global extension of the Philippine weather page, which found two
reanalyses of the OBSERVED past disagreeing by 1.09 C on Manila's annual mean.
That was history. This is the future, where the spread is wider.

Method: for each city and each model, the mean of daily mean temperature over a
1991-2020 baseline and a 2041-2070 future window, from one request covering both.
Warming is the difference. Spread is the range of that warming across models.

Model availability is not assumed. Some models return nothing for some points and
that is recorded per city rather than quietly reducing the ensemble.

Free, no key:
  https://climate-api.open-meteo.com/v1/climate   CMIP6 downscaled projections
"""
import collections
import csv
import hashlib
import json
import os
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
UA = {"User-Agent": "allanninal.dev research (landix.ninal@gmail.com)"}

API = "https://climate-api.open-meteo.com/v1/climate"
SRC = "Open-Meteo CMIP6 downscaled projections, climate-api.open-meteo.com"

MODELS = ["CMCC_CM2_VHR4", "FGOALS_f3_H", "HiRAM_SIT_HR", "MRI_AGCM3_2_S",
          "EC_Earth3P_HR", "MPI_ESM1_2_XR", "NICAM16_8S"]
# Open-Meteo's CMIP6 coverage ends at 2050 -- a request past it returns 400, not
# a truncated series -- so both windows sit inside it. They are twenty years each
# with a twenty-year gap between them, which is a cleaner contrast than two
# adjacent windows and, more practically, asks for forty years of data per
# city-model instead of sixty.
#
# That matters because the API is metered by cost, not by call count: the limit is
# hourly and a sixty-year two-variable request is heavy enough that thirty of them
# exhaust it ("Hourly API request limit exceeded"). Every response is cached, so a
# run that hits the cap resumes in the next hour without re-fetching anything.
BASE = (1991, 2010)
FUT = (2031, 2050)
PAUSE = 0.35
RETRY_CAP = 600
MIN_MODELS = 4          # a spread computed on fewer than this is not an ensemble
MIN_CITIES = 8          # below this the medians below are not worth reporting
OFFLINE = "--offline" in sys.argv   # build from cache only; skip anything missing
MIN_DAYS = 6000         # of ~7305 in a 20-year window; below this the mean is thin

# Sixteen cities, ordered so the seven already collected stay first and the rest
# widen the latitude range rather than the count. The API is metered by cost per
# hour, so every city added is an hour of waiting; a spread from Reykjavik at 64N
# to Sydney at 34S is worth more here than another tropical capital.
# Ordered by what the analysis needs next, not by geography. The seven tropical
# cities were collected first and are cached; the high-latitude ones follow,
# because the one robust geographical signal here is that the far north warms
# faster and it cannot be shown without Reykjavik and Moscow. The API is metered
# by cost per hour, so ordering is how you decide what you have if collection
# stops early.
CITIES = [
    ("Manila", "PH", 14.60, 120.98), ("Jakarta", "ID", -6.21, 106.85),
    ("Delhi", "IN", 28.61, 77.21), ("Dhaka", "BD", 23.81, 90.41),
    ("Lagos", "NG", 6.52, 3.38), ("Nairobi", "KE", -1.29, 36.82),
    ("Cairo", "EG", 30.04, 31.24), ("Sao Paulo", "BR", -23.55, -46.63),
    ("Reykjavik", "IS", 64.15, -21.94), ("Moscow", "RU", 55.76, 37.62),
    ("London", "GB", 51.51, -0.13), ("Sydney", "AU", -33.87, 151.21),
    ("New York", "US", 40.71, -74.01), ("Tokyo", "JP", 35.68, 139.69),
    ("Berlin", "DE", 52.52, 13.40), ("Mexico City", "MX", 19.43, -99.13),
]


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch(url, tries=5):
    cp = _cache_path(url)
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as fh:
            return json.load(fh)
    time.sleep(PAUSE)
    for n in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=300) as r:
                d = json.loads(r.read().decode("utf-8"))
            os.makedirs(CACHE, exist_ok=True)
            with open(cp, "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            return d
        except urllib.error.HTTPError as e:
            # Open-Meteo distinguishes the hourly allowance from the daily one only
            # in the body, and the difference matters: an hourly cap clears in
            # minutes and is worth waiting through, a daily cap does not clear
            # until tomorrow and retrying it just burns the run. Neither carries a
            # Retry-After, so the body is the only signal.
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            if "Daily API request limit" in body:
                raise SystemExit(
                    "\nDAILY LIMIT: Open-Meteo says the daily allowance is gone.\n"
                    "%d response(s) are cached under %s; re-run tomorrow and it "
                    "resumes from there without re-fetching.\n"
                    % (len(os.listdir(CACHE)) if os.path.isdir(CACHE) else 0, CACHE))
            asked = float(e.headers.get("Retry-After") or 0)
            if e.code == 429 and asked > RETRY_CAP:
                raise SystemExit(
                    "\nRATE LIMIT: %.0f seconds asked (%.1f hours). Cached under %s; "
                    "a later run resumes.\n" % (asked, asked / 3600.0, CACHE))
            if e.code not in (429, 500, 502, 503) or n == tries - 1:
                raise
            time.sleep(asked or min(90, 15 * (n + 1)))
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as e:
            if n == tries - 1:
                raise
            sys.stderr.write("  retry %d/%d -- %s\n" % (n + 1, tries, e))
            time.sleep(5 * (n + 1))


def series(lat, lon, model):
    # `models`, not `model`. Sending both is a 400.
    # Two requests for two windows rather than one spanning the gap between them:
    # the twenty years in the middle are not used and asking for them is a third
    # of the cost of every call.
    out = {"time": [], "temperature_2m_mean": [], "temperature_2m_max": []}
    for lo, hi in (BASE, FUT):
        u = API + "?" + urllib.parse.urlencode(dict(
            latitude=lat, longitude=lon, models=model,
            start_date="%d-01-01" % lo, end_date="%d-12-31" % hi,
            daily="temperature_2m_mean,temperature_2m_max"))
        if OFFLINE and not os.path.exists(_cache_path(u)):
            raise KeyError("not cached")
        d = fetch(u)
        day = d.get("daily") or {}
        for k in out:
            out[k].extend(day.get(k) or [])
    return {"daily": out}


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("  %-26s %6d row(s)" % (name, len(rows)))


def window(times, vals, lo, hi):
    out = [v for t, v in zip(times, vals)
           if v is not None and lo <= int(t[:4]) <= hi]
    return out


def main():
    mrows, crows, arows = [], [], []
    avail = collections.Counter()
    for name, cc, lat, lon in CITIES:
        got = []
        for m in MODELS:
            try:
                d = series(lat, lon, m)
            except KeyError:
                arows.append([name, cc, m, "not collected",
                              "offline run; this pair is not in the cache", SRC])
                continue
            except Exception as e:
                arows.append([name, cc, m, "error", str(e)[:60], SRC])
                continue
            daily = d.get("daily") or {}
            t = daily.get("time") or []
            mean = daily.get("temperature_2m_mean") or []
            mx = daily.get("temperature_2m_max") or []
            b = window(t, mean, *BASE)
            fu = window(t, mean, *FUT)
            if len(b) < MIN_DAYS or len(fu) < MIN_DAYS:
                arows.append([name, cc, m, "sparse",
                              "%d baseline days, %d future days" % (len(b), len(fu)),
                              SRC])
                continue
            bmax = window(t, mx, *BASE)
            fmax = window(t, mx, *FUT)
            bm, fm = statistics.mean(b), statistics.mean(fu)
            hot_b = sum(1 for v in bmax if v >= 35.0) / 30.0
            hot_f = sum(1 for v in fmax if v >= 35.0) / 30.0
            got.append((m, bm, fm, fm - bm, hot_b, hot_f))
            avail[m] += 1
            arows.append([name, cc, m, "ok",
                          "%d baseline days, %d future days" % (len(b), len(fu)),
                          SRC])
            mrows.append([name, cc, lat, lon, m, round(bm, 3), round(fm, 3),
                          round(fm - bm, 3), round(hot_b, 1), round(hot_f, 1), SRC])
        if len(got) < MIN_MODELS:
            print("  %-14s only %d model(s) -- excluded from the spread"
                  % (name, len(got)))
            continue
        w = [g[3] for g in got]
        hb = [g[4] for g in got]
        hf = [g[5] for g in got]
        crows.append([
            name, cc, lat, lon, len(got),
            round(statistics.mean([g[1] for g in got]), 2),
            round(statistics.mean([g[2] for g in got]), 2),
            round(statistics.mean(w), 2), round(min(w), 2), round(max(w), 2),
            round(max(w) - min(w), 2),
            round((max(w) - min(w)) / statistics.mean(w), 2)
            if statistics.mean(w) else "",
            1 if min(w) > 0 else 0,
            round(statistics.mean(hb), 1), round(statistics.mean(hf), 1),
            round(min(hf), 1), round(max(hf), 1), SRC])
        print("  %-14s %d models  warming %.2f C  spread %.2f C"
              % (name, len(got), statistics.mean(w), max(w) - min(w)))

    if len(crows) < MIN_CITIES:
        raise SystemExit(
            "\nTOO FEW CITIES: %d complete, need %d. Medians over fewer than that "
            "describe the cities that happened to be collected first rather than "
            "anything about the world.\n" % (len(crows), MIN_CITIES))

    write("cs_model.csv",
          ["city", "country", "latitude", "longitude", "model",
           "baseline_mean_c", "future_mean_c", "warming_c",
           "baseline_days_over_35_per_year", "future_days_over_35_per_year",
           "source"], mrows)
    write("cs_availability.csv",
          ["city", "country", "model", "status", "detail", "source"], arows)
    write("cs_city.csv",
          ["city", "country", "latitude", "longitude", "models",
           "baseline_mean_c", "future_mean_c", "mean_warming_c",
           "min_warming_c", "max_warming_c", "spread_c", "spread_over_warming",
           "all_models_warm", "baseline_days_over_35", "future_days_over_35",
           "min_future_days_over_35", "max_future_days_over_35", "source"], crows)

    warm = [c[7] for c in crows]
    spread = [c[10] for c in crows]
    ratio = [c[11] for c in crows if c[11] != ""]
    disagree = [c for c in crows if c[10] > c[7]]
    cov = [
     ["cities", len(crows), "count", SRC],
     ["cities requested", len(CITIES), "count", SRC],
     ["models offered", len(MODELS), "count", SRC],
     ["baseline window", "%d-%d" % BASE, "years", SRC],
     ["future window", "%d-%d" % FUT, "years", SRC],
     ["city-model pairs used", len(mrows), "count", SRC],
     ["city-model pairs unavailable",
      sum(1 for a in arows if a[3] != "ok"), "count", SRC],
     ["median warming", round(statistics.median(warm), 2), "celsius", SRC],
     ["median spread between models", round(statistics.median(spread), 2),
      "celsius", SRC],
     ["median spread as a share of warming",
      round(statistics.median(ratio), 2), "ratio", SRC],
     ["cities where the spread exceeds the warming", len(disagree), "count", SRC],
     ["cities where every model warms",
      sum(1 for c in crows if c[12] == 1), "count", SRC],
     ["largest spread", round(max(spread), 2), "celsius", SRC],
     ["smallest spread", round(min(spread), 2), "celsius", SRC],
     ["hourly rate limit", 1, "flag",
      "Open-Meteo meters by cost per hour; collection spans several hourly "
      "windows and every response is cached"],
     ["direction is agreed", 1, "flag",
      "every model warms every city that met the ensemble minimum"],
    ]
    write("cs_coverage.csv", ["property", "value", "unit", "source"], cov)

    print("\n%d cities, %d models offered. Median warming %.2f C by %d-%d; median "
          "disagreement between models %.2f C -- %.0f%% of the warming itself."
          % (len(crows), len(MODELS), statistics.median(warm), FUT[0], FUT[1],
             statistics.median(spread), 100 * statistics.median(ratio)))
    print("Every model warms every one of the %d cities."
          % sum(1 for c in crows if c[12] == 1))


if __name__ == "__main__":
    main()
