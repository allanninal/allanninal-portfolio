#!/usr/bin/env python3
"""Per-stock daily history from PSE Edge, for the sections the index feed cannot answer.

PSE Edge is the exchange's own disclosure portal. Its chart endpoint is a JSON
POST API (a GET returns 415, which is why it looks closed), needs no key, and
reaches back to 2014. Each bar carries CLOSE and VALUE, where VALUE is peso
turnover -- the field that makes real turnover, breadth and gainer/loser
analysis possible without a paid feed.

Universe: the N largest domestic companies by market capitalisation, taken from
a dated stockanalysis.com snapshot with the Manulife and Sun Life cross-listings
excluded. This is a *stated* universe, not the whole exchange: turnover and
breadth computed here describe the large-cap market, and small caps -- usually
the most violent movers -- are deliberately out of scope. Any chart built from
this must say so.

Outputs (relative to data/ph-pse/):
    ph_pse_stock_daily.csv       date, ticker, close, value_php
    ph_pse_turnover_monthly.csv  monthly peso turnover across the universe
    ph_pse_annual_returns.csv    per-stock calendar-year return
    ph_pse_breadth_monthly.csv   advancing / declining / unchanged per month
"""
import collections
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
      "Referer": "https://edge.pse.com.ph/"}
UNIVERSE_N = int(os.environ.get("PSE_UNIVERSE_N", "80"))
CROSS_LISTED = {"MFC", "SLF"}


def _post(url, data=None, form=None):
    if form is not None:
        body = urllib.parse.urlencode(form).encode(); ct = "application/x-www-form-urlencoded"
    else:
        body = json.dumps(data).encode(); ct = "application/json"
    h = dict(UA); h["Content-Type"] = ct
    return urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h),
                                  timeout=60).read().decode("utf-8", "replace")


def universe():
    """Largest domestic tickers by market cap, from a dated snapshot."""
    raw = urllib.request.urlopen(urllib.request.Request(
        "https://stockanalysis.com/list/philippine-stock-exchange/", headers=UA
    ), timeout=60).read().decode("utf-8", "replace")
    body = raw[raw.find("<tbody"):raw.find("</tbody>")]
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).replace("<!--[!-->", "").replace("<!--]-->", "").strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 4 or not cells[1] or cells[1] in CROSS_LISTED:
            continue
        mc = cells[3].replace(",", "")
        mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
        try:
            v = float(mc[:-1]) * mult[mc[-1]] if mc and mc[-1] in mult else float(mc)
        except ValueError:
            continue
        out.append((cells[1], v))
    out.sort(key=lambda x: -x[1])
    return [t for t, _ in out[:UNIVERSE_N]]


def ids_for(ticker):
    r = _post(f"https://edge.pse.com.ph/autoComplete/searchCompanyNameSymbol.ax?term={ticker}", form={})
    hits = [h for h in json.loads(r) if h.get("symbol", "").upper() == ticker.upper()]
    if not hits:
        return None
    cmpy = hits[0]["cmpyId"]
    html = urllib.request.urlopen(urllib.request.Request(
        f"https://edge.pse.com.ph/companyPage/stockData.do?cmpy_id={cmpy}", headers=UA), timeout=60
    ).read().decode("utf-8", "replace")
    m = re.search(r'security_id\s*=\s*["\'](\d+)["\']', html)
    return (int(cmpy), int(m.group(1))) if m else None


def daily(cmpy_id, security_id):
    r = _post("https://edge.pse.com.ph/common/DisclosureCht.ax",
              data={"cmpy_id": cmpy_id, "security_id": security_id,
                    "startDate": "01-01-2014", "endDate": "12-31-2026"})
    rows = []
    for b in (json.loads(r).get("chartData") or []):
        try:
            d = dt.datetime.strptime(b["CHART_DATE"].split(" 00:00:00")[0], "%b %d, %Y").date()
        except ValueError:
            continue
        rows.append((d, b.get("CLOSE"), b.get("VALUE")))
    return rows


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print("  wrote %-34s %d rows" % (name, len(rows)))


def main():
    tickers = universe()
    print("universe: %d tickers, %s ..." % (len(tickers), ", ".join(tickers[:8])))
    data, failed = {}, []
    for i, t in enumerate(tickers, 1):
        try:
            ids = ids_for(t)
            if not ids:
                failed.append(t); continue
            data[t] = daily(*ids)
        except Exception as e:
            failed.append(t)
            print("    %s failed: %s" % (t, type(e).__name__))
        if i % 20 == 0:
            print("    %d/%d" % (i, len(tickers)))
        time.sleep(0.25)
    print("  fetched %d tickers, %d failed%s"
          % (len(data), len(failed), (": " + ", ".join(failed)) if failed else ""))

    write("ph_pse_stock_daily.csv", ["date", "ticker", "close", "value_php", "source"],
          [[d.isoformat(), t, c, v, "PSE Edge"]
           for t, rows in sorted(data.items()) for d, c, v in rows if c is not None])

    # monthly turnover across the universe
    mon = collections.defaultdict(float)
    cnt = collections.defaultdict(set)
    for t, rows in data.items():
        for d, c, v in rows:
            if v:
                mon[(d.year, d.month)] += v
                cnt[(d.year, d.month)].add(d)
    write("ph_pse_turnover_monthly.csv",
          ["year", "month", "turnover_php", "trading_days", "avg_daily_php", "universe", "source"],
          [[y, m, "%.0f" % mon[(y, m)], len(cnt[(y, m)]),
            "%.0f" % (mon[(y, m)] / max(1, len(cnt[(y, m)]))), len(data), "PSE Edge"]
           for (y, m) in sorted(mon)])

    # per-stock calendar-year return
    ann = []
    for t, rows in sorted(data.items()):
        ye = {}
        for d, c, _ in rows:
            if c:
                ye[d.year] = c
        yrs = sorted(ye)
        for a, b in zip(yrs, yrs[1:]):
            if b == a + 1 and ye[a]:
                ann.append([b, t, "%.4f" % ye[a], "%.4f" % ye[b],
                            "%.2f" % ((ye[b] / ye[a] - 1) * 100), "PSE Edge"])
    write("ph_pse_annual_returns.csv",
          ["year", "ticker", "prev_close", "close", "return_pct", "source"], ann)

    # monthly breadth: how many names rose vs fell that month
    per = collections.defaultdict(dict)
    for t, rows in data.items():
        for d, c, _ in rows:
            if c:
                per[(d.year, d.month)][t] = c
    keys = sorted(per)
    br = []
    for a, b in zip(keys, keys[1:]):
        up = down = flat = 0
        for t, c in per[b].items():
            p = per[a].get(t)
            if not p:
                continue
            if c > p: up += 1
            elif c < p: down += 1
            else: flat += 1
        n = up + down + flat
        if n:
            br.append([b[0], b[1], up, down, flat, n,
                       "%.1f" % (up / n * 100), len(data), "PSE Edge"])
    write("ph_pse_breadth_monthly.csv",
          ["year", "month", "advancing", "declining", "unchanged", "counted",
           "advancing_share_pct", "universe", "source"], br)


if __name__ == "__main__":
    main()
