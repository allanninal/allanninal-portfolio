#!/usr/bin/env python3
"""Daily NCR rice prices from the DA's Bantay Presyo PDF archive.

The Department of Agriculture publishes prevailing retail prices every trading
day, but only as PDFs. `da.gov.ph/price-monitoring/` lists the whole archive --
about 3,200 files, 2018 to present -- on a single page with no pagination, so
the index is one fetch.

The catch, and the reason no machine-readable panel exists: the report has been
through at least four layout generations. Roughly:

    2018            "Price Watch" bulletins
    2019-10..2021   plain tabular: COMMODITY | SPEC | unit | prevailing/low/high/avg
    2021-11..2025-02  a graphic infographic layout with prices scattered in
                      boxes -- not reliably parseable line by line
    2025-03..now    numbered tabular: "1  Fancy  White Rice  56.15", with
                      lettered section heads ("A  IMPORTED COMMERCIAL RICE")

This script parses the two tabular generations and *records every file it could
not parse* rather than quietly dropping them, so the coverage of the resulting
panel is visible in the output rather than assumed. Extending it to the
infographic era is a separate job.

Filenames are unreliable: some "Price-Monitoring-*.pdf" files are cigarette
reports. Content is classified after extraction, not from the name.

Outputs (relative to data/ph-food-prices/):
    ph_rice_prices_daily.csv   date, section, commodity, spec, price
    ph_rice_prices_coverage.csv  one row per source PDF: parsed or not
"""
import csv
import datetime as dt
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
INDEX = "https://www.da.gov.ph/price-monitoring/"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

# Only the NCR "Daily Price Index" commodity table is parsed: a narrow
# COMMODITY | SPECIFICATION | PREVAILING PRICE layout. The per-market range
# reports are a different, much wider shape and are rejected outright rather
# than half-parsed -- an earlier permissive version "covered" 80/80 files
# while filing section headers as commodities, splitting "150.00 - 190.00"
# across two columns, and putting Frozen Liempo under RICE.
TABLE_HEAD = re.compile(r"COMMODITY.*SPECIFICATION", re.I)
# The 2019-2024 layout prints four price columns (Prevailing, Low, High,
# Average); 2025+ prints one. Detect which from the header rather than
# assuming, and always take Prevailing.
MULTI_HEAD = re.compile(r"prevailing", re.I)
MULTI_COLS = re.compile(r"low|high|average", re.I)
SECTIONS = re.compile(
    r"^\s*(?:[A-Z]\d?|\d{1,2})?\s*"
    r"((?:NFA|IMPORTED COMMERCIAL|LOCAL COMMERCIAL|KADIWA)\s*RICE"
    r"(?:[- ]FOR[- ]ALL)?)\s*$", re.I)
OTHER_HEAD = re.compile(r"^\s*(?:[A-Z]\d?|\d{1,2})?\s*[A-Z][A-Z /()&'.,-]{6,}\s*$")
BAD = re.compile(r"page|prepared|source|note:|as of|hotline|contact|email|annex", re.I)
NUM = re.compile(r"^\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?$")
ROWNUM = re.compile(r"^\d{1,3}$")
# rows in the narrow table name a rice grade or variety
RICE_WORD = re.compile(
    r"basmati|glutinous|japonica|jasponica|special|premium|fancy|well[ -]?milled"
    r"|regular[ -]?milled|nfa|benteng|bigas|brown rice|red rice|white rice|rice", re.I)


def cells(line):
    """Split a fixed-layout row into columns on runs of 2+ spaces.

    Deliberately not one big regex. An earlier version used a single pattern
    with a lazy name group, an optional spec group and a repeated numeric
    group anchored to end-of-line; on the wide per-market rows that backtracks
    catastrophically -- it burned 65 minutes of CPU before being killed.
    """
    return [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]


def normalise(name):
    """Fold naming drift so a variety is one series, not two.

    The same grade is printed as "Basmati" in one vintage and "Basmati Rice"
    in the next, and Japonica/Jasponica swaps order between reports.
    """
    n = re.sub(r"\s+", " ", name).strip().rstrip("*\u1d43 ")
    n = re.sub(r"\s+Rice$", "", n, flags=re.I)
    n = re.sub(r"^Jasponica/Japonica$", "Japonica/Jasponica", n, flags=re.I)
    n = re.sub(r"^Well[ -]?Milled$", "Well Milled", n, flags=re.I)
    n = re.sub(r"^Regular[ -]?Milled$", "Regular Milled", n, flags=re.I)
    return n


def parse_rice(text):
    """[(section, commodity, spec, price)] from the narrow NCR commodity table.

    Returns [] for any report that does not contain that table, so the caller
    can record the file as an unsupported layout instead of inventing rows.
    """
    out, section, in_table, multi = [], None, False, False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or BAD.search(line):
            continue
        if TABLE_HEAD.search(line):
            in_table = True
            continue
        if in_table and MULTI_HEAD.search(line) and MULTI_COLS.search(line):
            multi = True                       # Prevailing | Low | High | Average
            continue
        if not in_table:
            continue

        m = SECTIONS.match(line)
        if m:
            section = re.sub(r"\s+", " ", m.group(1).upper()).strip()
            continue
        if section and OTHER_HEAD.match(line):
            section = None                     # a non-rice heading ends the block
            continue
        if not section:
            continue

        col = cells(line)
        if ROWNUM.match(col[0] if col else ""):
            col = col[1:]
        if len(col) < 2:
            continue
        # a range row ("150.00 - 190.00") or a wide per-market row: not this table
        if any("-" in c and NUM.match(c.replace("-", "").strip() or "x") for c in col):
            continue
        nums = [c for c in col if NUM.match(c)]
        if multi:
            if not 2 <= len(nums) <= 4:        # Prevailing plus Low/High/Average
                continue
        elif len(nums) != 1:                   # single-price layout
            continue
        name = col[0]
        if len(name) < 3 or NUM.match(name) or not RICE_WORD.search(name):
            continue
        price = float(nums[0].replace(",", ""))
        if not (5 <= price <= 500):
            continue
        spec = next((c for c in col[1:] if not NUM.match(c)), "")
        out.append((section, normalise(name), spec, price))
    return out


def file_date(name):
    m = re.search(r"(January|February|March|April|May|June|July|August|September|"
                  r"October|November|December)-(\d{1,2})-(\d{4})", name)
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    except ValueError:
        return None


def index_pdfs():
    html = urllib.request.urlopen(urllib.request.Request(INDEX, headers=UA),
                                  timeout=120).read().decode("utf-8", "replace")
    return sorted(set(re.findall(r'href="(https?://[^"]+\.pdf)"', html)))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    pdfs = index_pdfs()
    print("archive lists %d PDFs" % len(pdfs))
    cand = []
    for u in pdfs:
        n = u.split("/")[-1]
        if "Cigarette" in n:
            continue
        if not n.startswith(("Price-Monitoring", "Daily-Price-Index", "Weekly-Average-Prices")):
            continue
        d = file_date(n)
        if d:
            cand.append((d, u))
    cand.sort()
    if limit:
        cand = cand[-limit:]
    print("dated candidates: %d  (%s -> %s)" % (len(cand), cand[0][0], cand[-1][0]))

    tmp = tempfile.mkdtemp()
    rows, cover = [], []
    ok = 0
    for i, (d, u) in enumerate(cand, 1):
        name = u.split("/")[-1]
        try:
            data = urllib.request.urlopen(urllib.request.Request(
                urllib.parse.quote(u, safe=":/?&=%"), headers=UA), timeout=90).read()
            pdf, txt = os.path.join(tmp, "a.pdf"), os.path.join(tmp, "a.txt")
            open(pdf, "wb").write(data)
            subprocess.run(["pdftotext", "-layout", pdf, txt], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            got = parse_rice(open(txt, errors="replace").read())
            for sec, com, spec, price in got:
                rows.append([d.isoformat(), sec, com, spec, "%.2f" % price, name])
            cover.append([d.isoformat(), name, len(got), "parsed" if got else "no rice table"])
            if got:
                ok += 1
        except Exception as e:
            cover.append([d.isoformat(), name, 0, "error:%s" % type(e).__name__])
        if i % 100 == 0:
            print("    %d/%d  parsed=%d  rows=%d" % (i, len(cand), ok, len(rows)))
        time.sleep(0.05)

    print("  parsed %d of %d files, %d price rows" % (ok, len(cand), len(rows)))
    with open(os.path.join(OUT, "ph_rice_prices_daily.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "section", "commodity", "specification", "price_php_per_kg", "source_pdf"])
        w.writerows(rows)
    with open(os.path.join(OUT, "ph_rice_prices_coverage.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "source_pdf", "rows_parsed", "status"])
        w.writerows(cover)
    print("  wrote ph_rice_prices_daily.csv and ph_rice_prices_coverage.csv")


if __name__ == "__main__":
    main()
