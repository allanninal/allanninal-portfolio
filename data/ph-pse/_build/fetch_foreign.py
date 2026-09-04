#!/usr/bin/env python3
"""Daily foreign buying/selling from the PSE Weekly Report PDFs.

The PSE publishes net foreign transactions daily, but only inside PDFs. Page 1
of each Weekly Report carries a "Daily Foreign Transactions" table -- Buying,
Selling, Net, Total and foreign activity share, one row per trading day -- in a
fixed layout that `pdftotext -layout` reads reliably.

Reports are enumerated through the market-report listing's admin-ajax endpoint
rather than by guessing filenames, because the filenames carry inconsistent
suffixes (`-1`, `-final`). The WordPress nonce is short-lived and is re-scraped
on every run.

Values in the PDF are in THOUSAND pesos; they are converted to pesos here.

Outputs (relative to data/ph-pse/):
    ph_pse_foreign_daily.csv     date, buying, selling, net, total
    ph_pse_foreign_monthly.csv   monthly sums
    ph_pse_foreign_annual.csv    annual sums (partial years flagged)
"""
import collections
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
PAGE = "https://www.pse.com.ph/market-report/"
AJAX = "https://www.pse.com.ph/wp-admin/admin-ajax.php"

# The date column changed format across vintages: newer reports print
# "24-Aug-26", older ones just "19-Jun" and rely on the report's own year.
ROW = re.compile(
    r"(\d{1,2}-[A-Za-z]{3}(?:-\d{2})?)\s+"      # date, year optional
    r"(?:[\d,]+\.\d{2}\s+){4}"                  # OHLC
    r"\(?[\d,.]+\)?\s+\(?[\d,.]+\)?\s+"         # point / % change
    r"([\d,]+)\s+([\d,]+)\s+\(?([\d,]+)\)?\s+([\d,]+)\s+([\d,.]+)")


def num(s):
    return float(s.replace(",", ""))


def listing():
    """[(title, pdf_url)] for every Weekly Report, newest first."""
    html = urllib.request.urlopen(urllib.request.Request(PAGE, headers=UA), timeout=60
                                  ).read().decode("utf-8", "replace")
    nonce = re.search(r'"ajax_nonce":"([^"]+)"', html).group(1)
    tid = re.findall(r'<table[^>]+id="(ptp_[^"]+)"', html)[0]
    out, start = [], 0
    while True:
        body = urllib.parse.urlencode({"action": "ptp_load_posts", "security": nonce,
                                       "table_id": tid, "draw": 1, "start": start,
                                       "length": 200}).encode()
        r = urllib.request.urlopen(urllib.request.Request(
            AJAX, data=body, headers={**UA, "Referer": PAGE,
                                      "Content-Type": "application/x-www-form-urlencoded"}),
            timeout=90).read().decode("utf-8", "replace")
        d = json.loads(r)
        for row in d["data"]:
            cat = re.sub(r"<[^>]+>", "", row.get("categories", "")).strip()
            if cat != "Weekly Report":
                continue
            m = re.search(r'href="(https://documents\.pse\.com\.ph[^"]+\.pdf)"',
                          row.get("content", "").replace("\\/", "/"))
            if m:
                out.append((row.get("title", ""), m.group(1)))
        start += 200
        if start >= d["recordsTotal"]:
            return out


def parse(url, tmp, fallback_year=None):
    pdf = os.path.join(tmp, "w.pdf")
    txt = os.path.join(tmp, "w.txt")
    # documents.pse.com.ph 403s a request with no User-Agent, which urlretrieve
    # does not send -- fetch explicitly instead
    # some listed URLs contain literal spaces ("October 19, 2021-WR.pdf")
    safe = urllib.parse.quote(url, safe=":/?&=%")
    data = urllib.request.urlopen(
        urllib.request.Request(safe, headers=UA), timeout=90).read()
    with open(pdf, "wb") as f:
        f.write(data)
    subprocess.run(["pdftotext", "-layout", pdf, txt], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows = []
    for m in ROW.finditer(open(txt, errors="replace").read()):
        stamp = m.group(1)
        if re.search(r"-\d{2}$", stamp):
            d = dt.datetime.strptime(stamp, "%d-%b-%y").date()
        elif fallback_year:
            d = dt.datetime.strptime("%s-%d" % (stamp, fallback_year), "%d-%b-%Y").date()
        else:
            continue
        # the PDF prints net selling in parentheses; sign it from buying - selling
        buy, sell = num(m.group(2)) * 1000, num(m.group(3)) * 1000
        rows.append((d, buy, sell, buy - sell, num(m.group(5)) * 1000))
    return rows


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print("  wrote %-34s %d rows" % (name, len(rows)))


def main():
    reports = listing()
    print("weekly reports listed: %d" % len(reports))
    daily = {}
    tmp = tempfile.mkdtemp()
    ok = fail = 0
    for i, (title, url) in enumerate(reports, 1):
        try:
            ym = re.search(r"(20\d{2})", title)
            for d, b, s, n, t in parse(url, tmp, int(ym.group(1)) if ym else None):
                daily[d] = (b, s, n, t)
            ok += 1
        except Exception:
            fail += 1
        if i % 50 == 0:
            print("    %d/%d  (%d parsed, %d failed, %d days)" % (i, len(reports), ok, fail, len(daily)))
        time.sleep(0.1)
    print("  parsed %d reports, %d failed, %d trading days" % (ok, fail, len(daily)))

    write("ph_pse_foreign_daily.csv",
          ["date", "buying_php", "selling_php", "net_php", "total_php", "source"],
          [[d.isoformat(), "%.0f" % b, "%.0f" % s, "%.0f" % n, "%.0f" % t, "PSE Weekly Report"]
           for d, (b, s, n, t) in sorted(daily.items())])

    mon = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for d, (b, s, n, t) in daily.items():
        k = (d.year, d.month)
        mon[k][0] += b; mon[k][1] += s; mon[k][2] += n; mon[k][3] += 1
    write("ph_pse_foreign_monthly.csv",
          ["year", "month", "buying_php", "selling_php", "net_php", "trading_days", "source"],
          [[y, m, "%.0f" % v[0], "%.0f" % v[1], "%.0f" % v[2], v[3], "PSE Weekly Report"]
           for (y, m), v in sorted(mon.items())])

    ann = collections.defaultdict(lambda: [0.0, 0, set()])
    for d, (b, s, n, t) in daily.items():
        ann[d.year][0] += n; ann[d.year][1] += 1; ann[d.year][2].add(d.month)
    write("ph_pse_foreign_annual.csv",
          ["year", "net_php", "trading_days", "months_covered", "complete", "source"],
          [[y, "%.0f" % v[0], v[1], len(v[2]), "yes" if len(v[2]) == 12 else "no",
            "PSE Weekly Report"] for y, v in sorted(ann.items())])


if __name__ == "__main__":
    main()
