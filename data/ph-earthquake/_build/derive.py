#!/usr/bin/env python3
"""Aggregates for projects/earthquake-analysis.html, all from ph_earthquakes.csv.

Run fetch_usgs.py first. Nothing here reaches the network, so the aggregates
can always be rebuilt from the checked-in event table.

The one judgement call worth stating: every rate claim is made at M4.5+, not at
the M2.5 the catalogue nominally starts at. ph_earthquakes_completeness.csv is
the reason -- the count per half-magnitude bin RISES from M2.5 to M4.0 instead
of falling, which is physically impossible (Gutenberg-Richter says small quakes
outnumber large ones roughly tenfold per magnitude unit). The rise is the global
network failing to detect small Philippine events, not the ground being quiet.
Below M4.5 the series measures instrumentation; above it, seismicity.
"""
import csv
import os
from collections import Counter, defaultdict

D = os.path.join(os.path.dirname(__file__), "..")
SRC = "USGS FDSN event/1/query"
BOX = "4-22N,116-128E"


def write(name, fields, rows):
    p = os.path.join(D, name)
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    ev = list(csv.DictReader(open(os.path.join(D, "ph_earthquakes.csv"))))
    for e in ev:
        e["mag"] = float(e["mag"])
        e["year"] = int(e["year"])
        e["month"] = int(e["month"])
        e["depth_km"] = float(e["depth_km"]) if e["depth_km"] else None
    print("%d events" % len(ev))

    # -- completeness: counts per half-magnitude bin, all years pooled
    bins = Counter()
    for e in ev:
        bins[round(e["mag"] * 2) / 2 if e["mag"] < 6 else 6.0] += 1
    rows = []
    for b in sorted(bins):
        rows.append(dict(mag_bin=("%.1f" % b) if b < 6 else "6.0+",
                         events=bins[b], box=BOX, source=SRC))
    write("ph_earthquakes_completeness.csv",
          ["mag_bin", "events", "box", "source"], rows)

    # -- annual counts at several thresholds
    years = sorted({e["year"] for e in ev})
    rows = []
    for y in years:
        ys = [e for e in ev if e["year"] == y]
        rows.append(dict(
            year=y,
            m25plus=len(ys),
            m40plus=sum(1 for e in ys if e["mag"] >= 4.0),
            m45plus=sum(1 for e in ys if e["mag"] >= 4.5),
            m50plus=sum(1 for e in ys if e["mag"] >= 5.0),
            m60plus=sum(1 for e in ys if e["mag"] >= 6.0),
            m70plus=sum(1 for e in ys if e["mag"] >= 7.0),
            max_mag=max(e["mag"] for e in ys),
            box=BOX, source=SRC))
    write("ph_earthquakes_annual.csv", list(rows[0].keys()), rows)

    # -- magnitude bands at the completeness threshold
    tot = sum(1 for e in ev if e["mag"] >= 4.5)
    band = lambda m: ("M4.5-4.9" if m < 5 else "M5.0-5.9" if m < 6
                      else "M6.0-6.9" if m < 7 else "M7.0+")
    cnt = Counter(band(e["mag"]) for e in ev if e["mag"] >= 4.5)
    rows = [dict(band=b, events=cnt[b], share_pct=round(100.0 * cnt[b] / tot, 1),
                 threshold="M4.5+", box=BOX, source=SRC)
            for b in ["M4.5-4.9", "M5.0-5.9", "M6.0-6.9", "M7.0+"]]
    write("ph_earthquakes_magnitude_bands.csv", list(rows[0].keys()), rows)

    # -- depth bands. USGS assigns many shallow events a default depth of
    #    exactly 10 km when depth is not resolved, so that count is reported
    #    rather than blended into the shallow band silently.
    withd = [e for e in ev if e["depth_km"] is not None and e["mag"] >= 4.5]
    dband = lambda d: ("shallow (<70 km)" if d < 70 else
                       "intermediate (70-300 km)" if d < 300 else "deep (300+ km)")
    cnt = Counter(dband(e["depth_km"]) for e in withd)
    rows = [dict(band=b, events=cnt[b], share_pct=round(100.0 * cnt[b] / len(withd), 1),
                 threshold="M4.5+", box=BOX, source=SRC)
            for b in ["shallow (<70 km)", "intermediate (70-300 km)", "deep (300+ km)"]]
    rows.append(dict(band="of which depth fixed at exactly 10.0 km",
                     events=sum(1 for e in withd if e["depth_km"] == 10.0),
                     share_pct=round(100.0 * sum(1 for e in withd if e["depth_km"] == 10.0)
                                     / len(withd), 1),
                     threshold="M4.5+", box=BOX, source=SRC))
    write("ph_earthquakes_depth_bands.csv", list(rows[0].keys()), rows)

    # -- monthly, to test the folk claim that quakes have a season.
    #
    #    The raw column looks seasonal -- December carries 13.0% of M4.5+ events
    #    against an 8.3% expectation. It is not a season. A single M7.6 on
    #    2 December 2023 was followed by 510 M4.5+ events in thirty days. So the
    #    second column repeats the count with every 30-day window after an M7+
    #    removed, which is the only version of this table that says anything
    #    about background rate. Publishing the raw column alone would put a
    #    seasonal claim on the page that the aftershocks fully explain.
    import datetime as _dt
    big_t = [_dt.datetime.fromisoformat(e["time_utc"]) for e in ev if e["mag"] >= 7.0]

    def in_aftershock(e):
        t = _dt.datetime.fromisoformat(e["time_utc"])
        return any(0 < (t - b).total_seconds() <= 30 * 86400 for b in big_t)

    m45 = [e for e in ev if e["mag"] >= 4.5]
    cnt = Counter(e["month"] for e in m45)
    bg = Counter(e["month"] for e in m45 if not in_aftershock(e))
    n, nb = sum(cnt.values()), sum(bg.values())
    rows = [dict(month=m, events=cnt[m], share_pct=round(100.0 * cnt[m] / n, 2),
                 events_ex_aftershocks=bg[m],
                 share_ex_aftershocks_pct=round(100.0 * bg[m] / nb, 2),
                 expected_pct=round(100.0 / 12, 2), threshold="M4.5+",
                 box=BOX, source=SRC) for m in range(1, 13)]
    write("ph_earthquakes_monthly.csv", list(rows[0].keys()), rows)

    # -- largest events
    rows = [dict(time_utc=e["time_utc"], mag=e["mag"], depth_km=e["depth_km"],
                 latitude=e["latitude"], longitude=e["longitude"],
                 place=e["place"], box=BOX, source=SRC)
            for e in sorted(ev, key=lambda e: -e["mag"])[:20]]
    write("ph_earthquakes_largest.csv", list(rows[0].keys()), rows)

    # -- aftershock signature of the largest events: how the 30 days after a
    #    M7+ compare with that year's ordinary daily rate.
    import datetime
    big = [e for e in ev if e["mag"] >= 7.0]
    rows = []
    for b in sorted(big, key=lambda e: e["time_utc"]):
        t0 = datetime.datetime.fromisoformat(b["time_utc"])
        win = [e for e in ev if e["mag"] >= 4.5
               and 0 < (datetime.datetime.fromisoformat(e["time_utc"]) - t0).total_seconds() <= 30 * 86400]
        yr = sum(1 for e in ev if e["mag"] >= 4.5 and e["year"] == b["year"])
        base = yr / 365.0 * 30
        rows.append(dict(mainshock_utc=b["time_utc"], mainshock_mag=b["mag"],
                         place=b["place"], m45_next_30d=len(win),
                         year_baseline_30d=round(base, 1),
                         ratio=round(len(win) / base, 1) if base else "",
                         box=BOX, source=SRC))
    write("ph_earthquakes_aftershocks.csv", list(rows[0].keys()), rows)

    # -- regional split. USGS "place" strings name the nearest settlement, not a
    #    region, so the only defensible grouping is by latitude band: Mindanao
    #    and the Sulu/Celebes seas below 10N, the Visayas 10-13N, Luzon and the
    #    Philippine Sea above 13N. Stated on the page as latitude bands for
    #    exactly that reason -- a "region" column here would be invented.
    def latband(la):
        return ("south (<10N)" if la < 10 else
                "central (10-13N)" if la < 13 else "north (13N+)")
    m45 = [e for e in ev if e["mag"] >= 4.5]
    cnt = Counter(latband(float(e["latitude"])) for e in m45)
    rows = [dict(band=b, events=cnt[b],
                 share_pct=round(100.0 * cnt[b] / len(m45), 1),
                 max_mag=max((e["mag"] for e in m45 if latband(float(e["latitude"])) == b),
                             default=""),
                 threshold="M4.5+", box=BOX, source=SRC)
            for b in ["south (<10N)", "central (10-13N)", "north (13N+)"]]
    write("ph_earthquakes_latitude_bands.csv", list(rows[0].keys()), rows)

    # -- mean depth per magnitude band, replacing a "magnitude vs depth
    #    correlation" claim. The Pearson r is reported alongside because it is
    #    near zero, and a scatter that shows no relationship is a finding.
    withd = [e for e in ev if e["depth_km"] is not None and e["mag"] >= 4.5]
    n = len(withd)
    mx = sum(e["mag"] for e in withd) / n
    dy = sum(e["depth_km"] for e in withd) / n
    sxy = sum((e["mag"] - mx) * (e["depth_km"] - dy) for e in withd)
    sxx = sum((e["mag"] - mx) ** 2 for e in withd) ** 0.5
    syy = sum((e["depth_km"] - dy) ** 2 for e in withd) ** 0.5
    r = sxy / (sxx * syy)
    rows = []
    for lo, hi, lab in [(4.5, 5.0, "M4.5-4.9"), (5.0, 5.5, "M5.0-5.4"),
                        (5.5, 6.0, "M5.5-5.9"), (6.0, 7.0, "M6.0-6.9"),
                        (7.0, 10.0, "M7.0+")]:
        g = [e for e in withd if lo <= e["mag"] < hi]
        if not g:
            continue
        g.sort(key=lambda e: e["depth_km"])
        rows.append(dict(band=lab, events=len(g),
                         mean_depth_km=round(sum(e["depth_km"] for e in g) / len(g), 1),
                         median_depth_km=round(g[len(g) // 2]["depth_km"], 1),
                         pearson_r_all_bands=round(r, 3),
                         threshold="M4.5+", box=BOX, source=SRC))
    write("ph_earthquakes_mag_depth.csv", list(rows[0].keys()), rows)

    # -- decade comparison at the completeness threshold
    rows = []
    for lo, hi, lab in [(2000, 2009, "2000-2009"), (2010, 2019, "2010-2019"),
                        (2020, 2026, "2020-2026 (partial)")]:
        g = [e for e in ev if lo <= e["year"] <= hi and e["mag"] >= 4.5]
        yrs = hi - lo + 1
        rows.append(dict(period=lab, years=yrs, m45plus=len(g),
                         per_year=round(len(g) / yrs, 1),
                         m60plus=sum(1 for e in g if e["mag"] >= 6.0),
                         m70plus=sum(1 for e in g if e["mag"] >= 7.0),
                         max_mag=max(e["mag"] for e in g),
                         threshold="M4.5+", box=BOX, source=SRC))
    write("ph_earthquakes_decades.csv", list(rows[0].keys()), rows)


if __name__ == "__main__":
    main()
