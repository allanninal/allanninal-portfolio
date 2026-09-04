#!/usr/bin/env python3
"""Build the PSE datasets for projects/stock-market-analysis.html.

Two independent sources, deliberately:

  1. Yahoo `PSEI.PS` -- the PSEi index. Full daily history back to 1987 in one
     request, no key. Note this is the *index* ticker; Yahoo's individual PH
     equity tickers (e.g. SMPH.PS) have been frozen since 2019-06-28 and must
     not be used.
  2. PSE's own `frames.pse.com.ph/compositeSector` -- daily OHLC for the PSEi
     and all six sector indices, but only a rolling ~5-year window.

Source 1 gives depth, source 2 gives authority and the sector breakdown. Where
they overlap they are compared, and the run fails loudly if they disagree.

Because source 2 is a rolling window, the CSVs written here -- not the live
feeds -- are the system of record for years that have scrolled out of it.

Outputs (relative to data/ph-pse/):
    ph_psei_daily.csv           every daily close, 1987 -> today
    ph_psei_annual.csv          year-end close and change
    ph_psei_sector_annual.csv   year-end close and change, 6 sector indices
"""
import csv
import datetime as dt
import html
import json
import os
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/PSEI.PS"
         "?period1=0&period2=2000000000&interval=1d")
FRAMES = "https://frames.pse.com.ph/compositeSector"

SECTORS = [("PSEI", "PSEi"), ("ALL", "All Shares"), ("FIN", "Financials"),
           ("IND", "Industrial"), ("HDG", "Holding Firms"), ("PRO", "Property"),
           ("SVC", "Services"), ("M-O", "Mining & Oil")]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()


def yahoo_daily():
    """[(date, close)] for the PSEi, oldest first."""
    r = json.loads(get(YAHOO))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, dt.UTC).date(), c)
            for t, c in zip(r["timestamp"], q["close"]) if c is not None]


def frames_series():
    """{code: [(date, close)]} for every index PSE publishes on that page."""
    raw = get(FRAMES).decode("utf-8", "replace")
    out = {}
    for code, _ in SECTORS:
        m = re.search(r'id="%s-value-values"[^>]*value="([^"]*)"' % re.escape(code), raw)
        if not m:
            continue
        d = json.loads(html.unescape(m.group(1)))
        bars = d[0] if d and isinstance(d[0], list) else d
        out[code] = [(dt.datetime.fromtimestamp(b["time"], dt.UTC).date(), b["close"])
                     for b in bars]
    return out


def year_end(series):
    """{year: (date, close)} keeping the last trading day of each year."""
    by = {}
    for d, c in sorted(series):
        by[d.year] = (d, c)
    return by


def write(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-32s %d rows" % (name, len(rows)))


def main():
    print("fetching Yahoo PSEI.PS ...")
    daily = yahoo_daily()
    print("  %d sessions, %s -> %s" % (len(daily), daily[0][0], daily[-1][0]))

    print("fetching PSE compositeSector ...")
    frames = frames_series()
    print("  %d indices, PSEi window %s -> %s"
          % (len(frames), frames["PSEI"][0][0], frames["PSEI"][-1][0]))

    ye_y = year_end(daily)
    ye_f = year_end(frames["PSEI"])

    # cross-check every overlapping year; disagreement means one feed moved
    print("cross-checking overlapping years ...")
    checked = 0
    for year in sorted(set(ye_y) & set(ye_f)):
        cy, cf = ye_y[year][1], ye_f[year][1]
        if abs(cy - cf) > 0.02:
            raise SystemExit("MISMATCH %d: Yahoo %.2f vs PSE %.2f" % (year, cy, cf))
        checked += 1
    print("  %d years agree to the centavo" % checked)

    write("ph_psei_daily.csv", ["date", "close", "source"],
          [[d.isoformat(), "%.2f" % c, "Yahoo PSEI.PS"] for d, c in daily])

    # annual: skip the current, incomplete year
    this_year = dt.date.today().year
    rows, prev = [], None
    for year in sorted(ye_y):
        if year == this_year:
            continue
        d, c = ye_y[year]
        chg = "" if prev is None else "%.2f" % ((c / prev - 1) * 100)
        src = "Yahoo PSEI.PS" + (" + PSE compositeSector" if year in ye_f else "")
        rows.append([year, "%.2f" % c, chg, d.isoformat(), src])
        prev = c
    write("ph_psei_annual.csv",
          ["year", "close", "change_pct", "last_trading_day", "source"], rows)

    # sectors: only the years PSE's rolling window still covers
    srows = []
    for code, label in SECTORS:
        if code not in frames:
            continue
        ye = year_end(frames[code])
        prev = None
        for year in sorted(ye):
            if year == this_year:
                continue
            d, c = ye[year]
            chg = "" if prev is None else "%.2f" % ((c / prev - 1) * 100)
            srows.append([year, code, label, "%.2f" % c, chg, d.isoformat(),
                          "PSE compositeSector"])
            prev = c
    write("ph_psei_sector_annual.csv",
          ["year", "code", "index", "close", "change_pct", "last_trading_day", "source"],
          srows)


if __name__ == "__main__":
    main()
