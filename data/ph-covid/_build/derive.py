#!/usr/bin/env python3
"""Aggregates for projects/covid-analysis.html, all from ph_covid_daily.csv.

No network access; run fetch_owid.py first.

The wave detection here is deliberately mechanical and its rule is stated on
the page. "Four waves" is the kind of claim that gets asserted because it
sounds right, so this defines a wave as a local maximum of the 7-day smoothed
case curve that (a) exceeds 1,000 cases/day and (b) is separated from any
larger peak by a trough falling to under 40% of the smaller of the two. Change
those numbers and the wave count changes -- which is the honest situation, and
better said out loud than hidden behind a round number.
"""
import csv
import datetime
import os

D = os.path.join(os.path.dirname(__file__), "..")
MIN_PEAK = 1000.0
TROUGH_FRAC = 0.40


def rows(name):
    return list(csv.DictReader(open(os.path.join(D, name + ".csv"))))


def write(name, cols, data):
    with open(os.path.join(D, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(data)
    print("wrote %s (%d rows)" % (name, len(data)))


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    d = rows("ph_covid_daily")
    as_of = d[0]["as_of"]
    src = d[0]["source"]
    for r in d:
        r["date"] = datetime.date.fromisoformat(r["date"])
        for k in ("new_cases", "new_deaths", "new_cases_smoothed", "new_deaths_smoothed",
                  "stringency_index", "positive_rate", "reproduction_rate",
                  "people_fully_vaccinated", "total_cases", "total_deaths"):
            r[k] = f(r[k])

    # ---------------------------------------------------------------- waves
    s = [(r["date"], r["new_cases_smoothed"]) for r in d
         if r["new_cases_smoothed"] is not None]
    peaks = []
    for i in range(1, len(s) - 1):
        if s[i][1] >= MIN_PEAK and s[i][1] >= s[i - 1][1] and s[i][1] > s[i + 1][1]:
            peaks.append(i)
    # merge peaks not separated by a deep enough trough
    keep = []
    for i in peaks:
        if not keep:
            keep.append(i)
            continue
        j = keep[-1]
        trough = min(v for _, v in s[j:i + 1])
        if trough < TROUGH_FRAC * min(s[i][1], s[j][1]):
            keep.append(i)
        elif s[i][1] > s[j][1]:
            keep[-1] = i
    # Wave boundaries are the LOWEST point between consecutive peaks, not the
    # first local trough. Walking outward until the curve stops falling ends at
    # the first one-day wobble on a noisy series, which produced a "wave" seven
    # days long covering the whole of 2020. The global minimum between peaks is
    # the only boundary that survives noise.
    waves = []
    for n, i in enumerate(keep, 1):
        prev_peak = keep[n - 2] if n > 1 else 0
        next_peak = keep[n] if n < len(keep) else len(s) - 1
        a = min(range(prev_peak, i + 1), key=lambda k: s[k][1]) if n > 1 else 0
        b = min(range(i, next_peak + 1), key=lambda k: s[k][1]) if n < len(keep) else len(s) - 1
        # Half-open on the left for every wave after the first, so the shared
        # trough day is not counted twice. Without this the wave totals summed
        # to 34,027 more cases than the country recorded -- four boundary days
        # double-counted, which is small enough to look like rounding and is
        # not. checks.sql asserts the sum matches exactly.
        lo, hi = s[a][0], s[b][0]
        sel = [r for r in d if (lo < r["date"] if n > 1 else lo <= r["date"]) and r["date"] <= hi]
        cases = sum(r["new_cases"] or 0 for r in sel)
        deaths = sum(r["new_deaths"] or 0 for r in sel)
        waves.append([n, lo, s[i][0], hi, round(s[i][1]),
                      int(cases), int(deaths), len(sel), as_of, src])
    write("ph_covid_waves.csv",
          ["wave", "start", "peak_date", "end", "peak_smoothed_cases",
           "cases_in_wave", "deaths_in_wave", "days", "as_of", "source"], waves)

    # -------------------------------------------------------------- monthly
    m = {}
    for r in d:
        k = (r["date"].year, r["date"].month)
        a = m.setdefault(k, [0, 0, [], []])
        a[0] += r["new_cases"] or 0
        a[1] += r["new_deaths"] or 0
        if r["stringency_index"] is not None:
            a[2].append(r["stringency_index"])
        if r["positive_rate"] is not None:
            a[3].append(r["positive_rate"])
    write("ph_covid_monthly.csv",
          ["year", "month", "cases", "deaths", "mean_stringency",
           "mean_positive_rate_pct", "as_of", "source"],
          [[y, mo, int(a[0]), int(a[1]),
            round(sum(a[2]) / len(a[2]), 1) if a[2] else "",
            round(sum(a[3]) / len(a[3]), 2) if a[3] else "", as_of, src]
           for (y, mo), a in sorted(m.items())])

    # --------------------------------------------------------------- excess
    # The gap between excess deaths and confirmed deaths is the largest single
    # fact about this pandemic in this country, and the page it replaces did not
    # mention it once.
    h = {r["metric"]: r["value"] for r in rows("ph_covid_headline")}
    excess = float(h["excess_deaths_cumulative"])
    conf = float(h["total_deaths"])
    write("ph_covid_excess.csv",
          ["metric", "value", "as_of", "source"],
          [["confirmed_deaths", int(conf), as_of, src],
           ["excess_deaths", int(excess), as_of, src],
           ["undercount_multiple", round(excess / conf, 1), as_of, src],
           ["unattributed_deaths", int(excess - conf), as_of, src]])

    # ------------------------------------------------------------ reporting
    # OWID forward-fills new_cases with 0 once a country stops reporting, so the
    # series runs to as_of with 916 trailing zeros that mean "no report", not
    # "no cases". Charting them draws two flat years along the axis and reads as
    # the pandemic ending. The last date the country actually reported is
    # recorded here so the page can stop its curve there.
    nz = [r for r in d if r["new_cases"]]
    last_report = max(r["date"] for r in nz)
    write("ph_covid_reporting.csv",
          ["metric", "value", "as_of", "source"],
          [["last_report_date", last_report, as_of, src],
           ["trailing_zero_days", sum(1 for r in d if r["date"] > last_report), as_of, src],
           ["positivity_is_percent", "yes", as_of, src]])

    # --------------------------------------------- stringency against spread
    # Paired only where both series exist. Stringency stops at the end of 2022,
    # so any correlation quoted over the whole pandemic is quoting two-thirds of
    # it; the pairing count is published for exactly that reason.
    pairs = [(r["stringency_index"], r["new_cases_smoothed"]) for r in d
             if r["stringency_index"] is not None and r["new_cases_smoothed"] is not None]
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxy = sum((a - mx) * (b - my) for a, b in pairs)
    sxx = sum((a - mx) ** 2 for a, _ in pairs) ** 0.5
    syy = sum((b - my) ** 2 for _, b in pairs) ** 0.5
    write("ph_covid_stringency.csv",
          ["metric", "value", "as_of", "source"],
          [["paired_days", n, as_of, src],
           ["first_paired", min(r["date"] for r in d if r["stringency_index"] is not None), as_of, src],
           ["last_paired", max(r["date"] for r in d if r["stringency_index"] is not None), as_of, src],
           ["max_stringency", round(max(p[0] for p in pairs), 1), as_of, src],
           ["mean_stringency", round(mx, 1), as_of, src],
           ["pearson_r_same_day", round(sxy / (sxx * syy), 3), as_of, src]])


if __name__ == "__main__":
    main()
