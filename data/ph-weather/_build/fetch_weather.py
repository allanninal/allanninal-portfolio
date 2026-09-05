#!/usr/bin/env python3
"""Eighty-five years of Philippine daily weather, from two reanalyses that disagree.

The published page was built on a Kaggle scrape of OpenWeather readings covering
about fourteen months, and reported "447K+ records" as though volume were the
point. Fourteen months cannot show a climate trend, and the page's charts about
warming had nothing to compute one from.

Open-Meteo's archive API serves ERA5 daily data from 1940 without a key: 31,047
days per city in a single request, no nulls. That is enough for a real record.

The important thing it also shows is that the answer depends on which reanalysis
you ask. For Manila over 1950-2024:

    ERA5 (0.25 degree atmospheric)   mean 27.69 C, trend +0.12 C/decade
    ERA5-Land (0.1 degree surface)   mean 26.60 C, trend +0.07 C/decade

Those are two reconstructions of the same atmosphere. They differ by 1.09 C in
absolute level and by a factor of 1.7 in trend. So this page quotes no single
absolute temperature as "the temperature", reports the trend as a range, and
treats the gap between the two models as a floor on the uncertainty rather than
a rounding detail. Both agree on the two things that matter: it is warming, and
the last decade is the warmest in the record.

PAGASA would be the authority for station observations. pagasa.dost.gov.ph is not
reachable from a script here, and reanalysis is not the same thing as a
thermometer -- it is a model constrained by observations, on a grid of roughly 25
or 10 kilometres. A city is a grid cell, not a weather station.

Writes:
  ph_weather_annual.csv      city-year means and extremes, default model
  ph_weather_monthly.csv     the seasonal cycle, city by calendar month
  ph_weather_decades.csv     decadal means, so the acceleration is visible
  ph_weather_models.csv      annual means from both reanalyses, per city
  ph_weather_trends.csv      one row per city per model: trend, and its spread
  ph_weather_hotdays.csv     days at or above 35 C by decade
  ph_weather_records.csv     the hottest and wettest days in the record
  ph_weather_coverage.csv    what this data is and is not
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request
import collections

OUT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(os.path.dirname(__file__), ".cache")
API = "https://archive-api.open-meteo.com/v1/archive"

START, END = "1940-01-01", "2024-12-31"
FIRST_FULL, LAST_FULL = 1940, 2024
HOT = 35.0            # a "hot day" threshold, stated rather than implied

# Nine points spread the length of the archipelago. Each is a grid cell centred
# near the named city, not the city itself.
CITIES = [
    ("Laoag",      18.1978, 120.5936, "Ilocos Norte, far north"),
    ("Baguio",     16.4023, 120.5960, "Benguet, 1,500 m highland"),
    ("Manila",     14.5995, 120.9842, "National Capital Region"),
    ("Legazpi",    13.1391, 123.7438, "Albay, eastern Bicol"),
    ("Iloilo",     10.7202, 122.5621, "Panay, western Visayas"),
    ("Cebu",       10.3157, 123.8854, "central Visayas"),
    ("Tacloban",   11.2444, 125.0048, "Leyte, eastern Visayas"),
    ("Zamboanga",   6.9214, 122.0790, "western Mindanao"),
    ("Davao",       7.1907, 125.4553, "southern Mindanao"),
]

# The default (era5_seamless) is used for the daily statistics; the two named
# models are fetched for the cross-check. Naming them explicitly matters: the
# default silently resolves to one of them, and a page that quotes "the" value
# without saying which model produced it is quoting a coin flip.
MODELS = ["era5", "era5_land"]

SRC = ("Open-Meteo archive API (ECMWF ERA5 / ERA5-Land reanalysis), "
       "https://open-meteo.com/")


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-28s %5d rows" % (name, len(rows)))


def fetch(lat, lon, daily, model=None):
    """One archive request, cached on disk.

    The daily payload for one city is about 3 MB of JSON and 31,047 days. It is
    cached so that re-running to change an aggregate does not re-fetch 85 years
    from a free API nine times over.
    """
    q = {"latitude": lat, "longitude": lon, "start_date": START,
         "end_date": END, "daily": ",".join(daily), "timezone": "Asia/Manila"}
    if model:
        q["model"] = model
        q["models"] = model
    url = API + "?" + urllib.parse.urlencode(q)
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, "%.4f_%.4f_%s_%s.json"
                       % (lat, lon, model or "default", "-".join(daily)))
    if os.path.exists(key):
        return json.load(open(key))["daily"]
    # Open-Meteo's free tier returns 429 well before nine cities x three requests
    # are done, and it counts a long date range as many calls. The backoff is
    # minutes rather than seconds for that reason, and the cache above means a
    # run that gives up resumes where it stopped rather than starting over.
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=300))
            break
        except Exception as e:
            if attempt == 5:
                raise SystemExit("archive request failed for %s: %s" % (key, e))
            wait = 30 * (2 ** attempt)
            print("    %s -- retrying in %ds" % (e, wait))
            time.sleep(wait)
    time.sleep(3)                       # be a decent client between requests
    if "daily" not in d or not d["daily"].get("time"):
        raise SystemExit("empty payload for %s -- a bad variable name returns "
                         "an object with no daily block rather than an error" % key)
    json.dump(d, open(key, "w"))
    return d["daily"]


def ols(pairs):
    """Least-squares slope per year over (year, value)."""
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    den = sum((x - mx) ** 2 for x, _ in pairs)
    return sum((x - mx) * (y - my) for x, y in pairs) / den


def main():
    DAILY = ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
             "precipitation_sum"]
    annual, monthly, decades, hot, records = [], [], [], [], []
    models, trends = [], []
    span = None

    for name, lat, lon, where in CITIES:
        d = fetch(lat, lon, DAILY)
        days = d["time"]
        if span is None:
            span = (days[0], days[-1], len(days))
        print("  %-10s %d day(s) %s..%s" % (name, len(days), days[0], days[-1]))

        by_y = collections.defaultdict(lambda: collections.defaultdict(list))
        by_m = collections.defaultdict(lambda: collections.defaultdict(list))
        for i, day in enumerate(days):
            y, m = int(day[:4]), int(day[5:7])
            for k in DAILY:
                v = d[k][i]
                if v is not None:
                    by_y[y][k].append(v)
                    by_m[m][k].append(v)

        # ---- annual, only over years with essentially complete coverage -----
        full = []
        for y in sorted(by_y):
            n = len(by_y[y]["temperature_2m_mean"])
            if n < 360:
                continue
            full.append(y)
            annual.append([
                name, y, n,
                round(sum(by_y[y]["temperature_2m_mean"]) / n, 2),
                round(sum(by_y[y]["temperature_2m_max"])
                      / len(by_y[y]["temperature_2m_max"]), 2),
                round(sum(by_y[y]["temperature_2m_min"])
                      / len(by_y[y]["temperature_2m_min"]), 2),
                round(max(by_y[y]["temperature_2m_max"]), 1),
                round(min(by_y[y]["temperature_2m_min"]), 1),
                round(sum(by_y[y]["precipitation_sum"]), 1),
                sum(1 for x in by_y[y]["temperature_2m_max"] if x >= HOT),
                SRC])

        # ---- the seasonal cycle ---------------------------------------------
        for m in range(1, 13):
            monthly.append([
                name, m,
                round(sum(by_m[m]["temperature_2m_mean"])
                      / len(by_m[m]["temperature_2m_mean"]), 2),
                round(sum(by_m[m]["temperature_2m_max"])
                      / len(by_m[m]["temperature_2m_max"]), 2),
                # Monthly rainfall per year, not the 85-year total.
                round(sum(by_m[m]["precipitation_sum"]) / len(full), 1),
                len(full), SRC])

        # ---- decades, complete ones only ------------------------------------
        by_d = collections.defaultdict(list)
        for y in full:
            by_d[y - y % 10].extend(by_y[y]["temperature_2m_mean"])
        for dec in sorted(by_d):
            yrs = [y for y in full if y - y % 10 == dec]
            decades.append([name, "%ds" % dec, len(yrs),
                            round(sum(by_d[dec]) / len(by_d[dec]), 2),
                            "complete" if len(yrs) == 10 else "partial", SRC])
            nh = sum(1 for y in yrs for x in by_y[y]["temperature_2m_max"]
                     if x >= HOT)
            nd = sum(len(by_y[y]["temperature_2m_max"]) for y in yrs)
            hot.append([name, "%ds" % dec, len(yrs), nh, nd,
                        round(365.25 * nh / nd, 2),
                        "complete" if len(yrs) == 10 else "partial", SRC])

        # ---- records ---------------------------------------------------------
        hi = max(range(len(days)), key=lambda i: d["temperature_2m_max"][i] or -99)
        lo = min(range(len(days)),
                 key=lambda i: (d["temperature_2m_min"][i]
                                if d["temperature_2m_min"][i] is not None else 99))
        wet = max(range(len(days)),
                  key=lambda i: d["precipitation_sum"][i] or -1)
        records += [
            [name, "hottest day", days[hi],
             round(d["temperature_2m_max"][hi], 1), "°C daily maximum", SRC],
            [name, "coolest night", days[lo],
             round(d["temperature_2m_min"][lo], 1), "°C daily minimum", SRC],
            [name, "wettest day", days[wet],
             round(d["precipitation_sum"][wet], 1), "mm of rain", SRC]]

        # ---- the two models, on annual mean temperature only ----------------
        per_model = {}
        for mo in MODELS:
            md = fetch(lat, lon, ["temperature_2m_mean"], model=mo)
            ys = collections.defaultdict(list)
            for day, t in zip(md["time"], md["temperature_2m_mean"]):
                if t is not None:
                    ys[int(day[:4])].append(t)
            ser = {y: sum(v) / len(v) for y, v in ys.items() if len(v) >= 360}
            if not ser:
                raise SystemExit("no complete year for %s from %s" % (name, mo))
            per_model[mo] = ser
            for y in sorted(ser):
                models.append([name, mo, y, round(ser[y], 2), SRC])
            pairs = sorted(ser.items())
            recent = [ser[y] for y in sorted(ser)[-10:]]
            early = [ser[y] for y in sorted(ser)[:10]]
            trends.append([
                name, mo, min(ser), max(ser), len(ser),
                round(sum(ser.values()) / len(ser), 2),
                round(ols(pairs) * 10, 3),
                round(sum(early) / len(early), 2),
                round(sum(recent) / len(recent), 2),
                round(sum(recent) / len(recent) - sum(early) / len(early), 2),
                SRC])
        # The spread between two reconstructions of the same atmosphere, which is
        # a floor on how precisely any of this is known.
        common = sorted(set(per_model[MODELS[0]]) & set(per_model[MODELS[1]]))
        gap = [abs(per_model[MODELS[0]][y] - per_model[MODELS[1]][y])
               for y in common]
        trends.append([
            name, "model spread", min(common), max(common), len(common),
            round(sum(gap) / len(gap), 2),
            round(abs(ols(sorted((y, per_model[MODELS[0]][y]) for y in common)) * 10
                      - ols(sorted((y, per_model[MODELS[1]][y]) for y in common)) * 10), 3),
            "", "", round(max(gap), 2), SRC])

    write("ph_weather_annual.csv",
          ["city", "year", "days", "mean_c", "mean_max_c", "mean_min_c",
           "hottest_day_c", "coolest_night_c", "rainfall_mm", "days_over_35c",
           "source"], annual)
    write("ph_weather_monthly.csv",
          ["city", "month", "mean_c", "mean_max_c", "mean_rainfall_mm",
           "years", "source"], monthly)
    write("ph_weather_decades.csv",
          ["city", "decade", "years", "mean_c", "completeness", "source"], decades)
    write("ph_weather_hotdays.csv",
          ["city", "decade", "years", "days_over_35c", "days_measured",
           "days_over_35c_per_year", "completeness", "source"], hot)
    write("ph_weather_records.csv",
          ["city", "record", "date", "value", "unit", "source"], records)
    write("ph_weather_models.csv",
          ["city", "model", "year", "mean_c", "source"], models)
    write("ph_weather_trends.csv",
          ["city", "model", "first_year", "last_year", "years", "mean_c",
           "trend_c_per_decade", "first_decade_mean_c", "last_decade_mean_c",
           "change_c", "source"], trends)

    ph = [t for t in trends if t[0] == "Manila"]
    cov = [
        ["cities", len(CITIES), "grid cells near named cities, not weather stations", SRC],
        ["first day", span[0], "", SRC],
        ["last day", span[1], "", SRC],
        ["days per city", span[2], "", SRC],
        ["daily observations read", span[2] * len(CITIES) * 4,
         "four variables per city-day", SRC],
        ["complete years per city",
         len([r for r in annual if r[0] == "Manila"]),
         "years with at least 360 days; partial years are excluded from every "
         "trend", SRC],
        ["reanalysis models compared", len(MODELS),
         ", ".join(MODELS), SRC],
        ["absolute disagreement between models, Manila",
         [t[5] for t in ph if t[1] == "model spread"][0],
         "°C, mean absolute difference in annual mean temperature", SRC],
        ["trend disagreement between models, Manila",
         [t[6] for t in ph if t[1] == "model spread"][0],
         "°C per decade -- the gap between two reconstructions of the same "
         "atmosphere", SRC],
        ["station observations", 0,
         "reanalysis is a model constrained by observations, not a thermometer "
         "reading; PAGASA holds the station record and is unreachable from a "
         "script here", SRC],
        ["typhoon tracks", 0,
         "wind and storm tracks are not in this dataset; a daily rainfall total "
         "does not identify a typhoon", SRC],
        ["urban heat island", 0,
         "a 25 km grid cell cannot separate a city from the land around it, so "
         "none of this measures urbanisation", SRC],
    ]
    write("ph_weather_coverage.csv",
          ["property", "value", "note", "source"], cov)


if __name__ == "__main__":
    main()
