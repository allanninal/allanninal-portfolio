#!/usr/bin/env python3
"""Derive the rice analysis series from the two raw sources.

Inputs (both in data/ph-food-prices/):
    wfp_food_prices_phl.csv    WFP via HDX, 2000-2026, monthly, nationwide,
                               and the only source carrying farm gate and
                               wholesale as well as retail.
    ph_rice_prices_daily.csv   DA Bantay Presyo, daily NCR retail by grade,
                               scraped from PDFs by fetch_bantay_presyo.py.

Outputs:
    ph_rice_annual.csv           mean PHP/kg by year and price type
    ph_rice_spread_annual.csv    wholesale vs retail for one constant grade
    ph_rice_imported_local.csv   monthly imported vs local, same grade
"""
import collections
import csv
import os
import statistics

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Holding one grade constant matters: the mix of grades reported changes over
# time, so an all-rice average moves when the basket moves, not just the price.
GRADE = "Rice (regular, milled)"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def wfp():
    rows = list(csv.DictReader(open(os.path.join(HERE, "wfp_food_prices_phl.csv"),
                                    encoding="utf-8", errors="replace")))
    if rows and str(rows[0].get("date", "")).startswith("#"):
        rows = rows[1:]                     # HXL tag row
    return [r for r in rows
            if "rice" in (r.get("commodity") or "").lower()
            and (r.get("unit") or "").upper() == "KG"]


def write(name, header, rows):
    with open(os.path.join(HERE, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print("  wrote %-32s %d rows" % (name, len(rows)))


def main():
    rice = wfp()

    by = collections.defaultdict(list)
    for r in rice:
        p = num(r.get("price"))
        if p:
            by[(r["date"][:4], r["pricetype"])].append(p)
    out = []
    for y in sorted({k[0] for k in by}):
        row = [y]
        for t in ("Farm Gate", "Wholesale", "Retail"):
            v = by.get((y, t))
            row.append("%.2f" % statistics.mean(v) if v else "")
            row.append(len(v) if v else 0)
        out.append(row + ["WFP via HDX"])
    write("ph_rice_annual.csv",
          ["year", "farmgate_php_kg", "farmgate_n", "wholesale_php_kg", "wholesale_n",
           "retail_php_kg", "retail_n", "source"], out)

    g = collections.defaultdict(list)
    for r in rice:
        if r.get("commodity") != GRADE:
            continue
        p = num(r.get("price"))
        if p:
            g[(r["date"][:4], r["pricetype"])].append(p)
    out = []
    for y in sorted({k[0] for k in g}):
        w_, r_ = g.get((y, "Wholesale")), g.get((y, "Retail"))
        if not (w_ and r_):
            continue
        mw, mr = statistics.mean(w_), statistics.mean(r_)
        out.append([y, "%.2f" % mw, "%.2f" % mr, "%.2f" % (mr - mw),
                    "%.1f" % ((mr - mw) / mw * 100), GRADE, "WFP via HDX"])
    write("ph_rice_spread_annual.csv",
          ["year", "wholesale_php_kg", "retail_php_kg", "spread_php_kg",
           "spread_pct", "grade", "source"], out)

    b = list(csv.DictReader(open(os.path.join(HERE, "ph_rice_prices_daily.csv"))))
    m = collections.defaultdict(list)
    for r in b:
        sec = r["section"]
        if sec not in ("IMPORTED COMMERCIAL RICE", "LOCAL COMMERCIAL RICE"):
            continue
        if r["commodity"] not in ("Premium", "Well Milled", "Regular Milled"):
            continue
        m[(r["date"][:7], sec.split()[0], r["commodity"])].append(
            float(r["price_php_per_kg"]))
    out = []
    for month in sorted({k[0] for k in m}):
        for grade in ("Premium", "Well Milled", "Regular Milled"):
            i, l = m.get((month, "IMPORTED", grade)), m.get((month, "LOCAL", grade))
            if not (i and l):
                continue
            mi, ml = statistics.mean(i), statistics.mean(l)
            out.append([month, grade, "%.2f" % mi, "%.2f" % ml, "%.2f" % (ml - mi),
                        len(i), len(l), "DA Bantay Presyo"])
    write("ph_rice_imported_local.csv",
          ["month", "grade", "imported_php_kg", "local_php_kg", "local_premium_php_kg",
           "imported_n", "local_n", "source"], out)


if __name__ == "__main__":
    main()
