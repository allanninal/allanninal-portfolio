#!/usr/bin/env python3
"""Headline annual figures from the PSE's own Stock Market Infographics.

These one-page PDFs are the exchange's own published summary and are the
authoritative source for four numbers the index feeds do not carry: total
market capitalisation, average daily value traded, total capital raised, and
net foreign transactions. They also state the listed-company count.

Two layout generations exist and both are handled:
    FY21-FY23:  "+1.1% | Php 16.74 tn"   (percent first, pipe separator)
    FY24-FY25:  "Php 18.73tn   6.4%"     (value first, percent after)

Reports are enumerated through the market-report admin-ajax listing because
filenames are inconsistent (`-final`, `-clean`, `-v3`, `1QFY25` vs `1Q24`).

Output (relative to data/ph-pse/):
    ph_pse_annual_indicators.csv
"""
import csv
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
PAGE = "https://www.pse.com.ph/market-report/"
AJAX = "https://www.pse.com.ph/wp-admin/admin-ajax.php"

MULT = {"tn": 1e12, "bn": 1e9, "mn": 1e6}


def listing(category):
    html = urllib.request.urlopen(urllib.request.Request(PAGE, headers=UA), timeout=60
                                  ).read().decode("utf-8", "replace")
    nonce = re.search(r'"ajax_nonce":"([^"]+)"', html).group(1)
    tid = re.findall(r'<table[^>]+id="(ptp_[^"]+)"', html)[0]
    out, start = [], 0
    while True:
        body = urllib.parse.urlencode({"action": "ptp_load_posts", "security": nonce,
                                       "table_id": tid, "draw": 1, "start": start,
                                       "length": 200}).encode()
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            AJAX, data=body, headers={**UA, "Referer": PAGE,
                                      "Content-Type": "application/x-www-form-urlencoded"}),
            timeout=90).read().decode("utf-8", "replace"))
        for row in d["data"]:
            if re.sub(r"<[^>]+>", "", row.get("categories", "")).strip() != category:
                continue
            m = re.search(r'href="(https://documents\.pse\.com\.ph[^"]+\.pdf)"',
                          row.get("content", "").replace("\\/", "/"))
            if m:
                out.append((row.get("title", ""), m.group(1)))
        start += 200
        if start >= d["recordsTotal"]:
            return out


def text_of(url, tmp):
    data = urllib.request.urlopen(urllib.request.Request(
        urllib.parse.quote(url, safe=":/?&=%"), headers=UA), timeout=90).read()
    pdf, txt = os.path.join(tmp, "i.pdf"), os.path.join(tmp, "i.txt")
    open(pdf, "wb").write(data)
    subprocess.run(["pdftotext", "-layout", pdf, txt], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # NOTE: do not collapse runs of spaces here. The FY21-FY23 layout is
    # two-column and money_after() relies on horizontal position to tell the
    # columns apart; normalising whitespace destroys exactly that signal.
    return open(txt, errors="replace").read()


def money_after(text, label, window=260):
    """The 'Php N.NN tn|bn' belonging to a label.

    The FY21-FY23 layout puts two labels side by side on one line and their
    two values side by side on the next, so a plain forward search picks up
    the neighbouring column. Match on horizontal position instead: find the
    label's start column, then take the first Php value on a later line that
    begins within a few characters of it. Fall back to the forward search for
    the single-column FY24+ layout.
    """
    lines = text.splitlines()
    lab = label.upper()
    for li, line in enumerate(lines):
        col = line.upper().find(lab)
        if col < 0:
            continue
        for nxt in lines[li + 1:li + 6]:
            for m in re.finditer(r"Php\s*([\d,.]+)\s*(tn|bn|mn)", nxt, re.I):
                # allow the value to sit slightly left of its label
                if abs(m.start() - col) <= 30:
                    return float(m.group(1).replace(",", "")) * MULT[m.group(2).lower()]
        break
    i = text.upper().find(lab)
    if i < 0:
        return None
    m = re.search(r"Php\s*([\d,.]+)\s*(tn|bn|mn)", text[i:i + window], re.I)
    return float(m.group(1).replace(",", "")) * MULT[m.group(2).lower()] if m else None


def main():
    tmp = tempfile.mkdtemp()
    reports = [(t, u) for t, u in listing("Quarterly Stock Market Infographic")
               if re.match(r"FY\d\d", t)]
    print("FY infographics: %d" % len(reports))
    rows = []
    for title, url in sorted(reports):
        year = 2000 + int(re.search(r"FY(\d\d)", title).group(1))
        try:
            t = text_of(url, tmp)
        except Exception as e:
            print("  %s failed: %s" % (title, type(e).__name__)); continue
        listed = re.search(r"(\d{3}) listed companies", t)
        net = money_after(t, "FOREIGN TRANSACTIONS")
        direction = ""
        i = t.upper().find("FOREIGN TRANSACTIONS")
        if i >= 0:
            seg = t[i:i + 260].lower()
            direction = "net selling" if "net selling" in seg else (
                "net buying" if "net buying" in seg else "")
        rows.append([year,
                     "%.0f" % (money_after(t, "TOTAL MARKET CAPITALIZATION") or 0) or "",
                     "%.0f" % (money_after(t, "AVERAGE DAILY VALUE TRADED") or 0) or "",
                     "%.0f" % (money_after(t, "TOTAL CAPITAL RAISED") or 0) or "",
                     "%.0f" % (net or 0) or "", direction,
                     listed.group(1) if listed else "", "PSE FY Infographic"])
        print("  %s: mktcap=%s adv=%s raised=%s foreign=%s %s listed=%s" %
              (title,
               f"{(money_after(t,'TOTAL MARKET CAPITALIZATION') or 0)/1e12:.2f}tn",
               f"{(money_after(t,'AVERAGE DAILY VALUE TRADED') or 0)/1e9:.2f}bn",
               f"{(money_after(t,'TOTAL CAPITAL RAISED') or 0)/1e9:.2f}bn",
               f"{(net or 0)/1e9:.2f}bn", direction,
               listed.group(1) if listed else "?"))

    with open(os.path.join(OUT, "ph_pse_annual_indicators.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "market_cap_php", "avg_daily_value_php", "capital_raised_php",
                    "foreign_net_php", "foreign_direction", "listed_companies", "source"])
        w.writerows(rows)
    print("  wrote ph_pse_annual_indicators.csv  %d rows" % len(rows))


if __name__ == "__main__":
    main()
