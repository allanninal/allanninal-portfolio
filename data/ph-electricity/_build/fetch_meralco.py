#!/usr/bin/env python3
"""Meralco monthly residential rate, scraped from its own rate advisories.

Meralco announces the all-in residential rate every month in a press advisory.
The rates archive is a JavaScript shell -- there is no sitemap, no feed, and
robots.txt itself returns the SPA HTML -- so advisories are reached by URL
pattern instead. Five slug shapes cover the range observed:

    lower-rates-{month}-{year}            higher-rates-{month}-{year}
    lower-residential-rates-{month}-{year}  higher-residential-rates-{month}-{year}
    rates-{month}-{year}

Each advisory states two months at once:

    "bringing down the overall rate for a typical household to P14.7833
     from P14.8261 per kWh in July"

so the current and prior month are both captured, and the overlap between
consecutive advisories is a free consistency check -- where two advisories
disagree about the same month the run reports it rather than silently
picking one.

Coverage is written per attempted month, not just the successes.

Outputs (relative to data/ph-electricity/):
    ph_meralco_monthly.csv    year, month, rate_php_per_kwh, source_slug
    ph_meralco_coverage.csv   one row per month attempted
"""
import csv
import datetime as dt
import os
import re
import sys
import time
import urllib.error
import urllib.request

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
BASE = "https://company.meralco.com.ph/news-and-advisories/"
MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
PATTERNS = ["lower-rates-{m}-{y}", "higher-rates-{m}-{y}",
            "lower-residential-rates-{m}-{y}", "higher-residential-rates-{m}-{y}",
            "rates-{m}-{y}"]

# The advisory quotes several figures per kWh. Only the all-in household rate
# is wanted, so the pattern is anchored to that phrasing rather than matching
# any "to P.. from P.. per kWh" -- the generation charge is written the same
# way and is a component of the total (about P7-8 against P13-15), so an
# unanchored pattern silently captures the wrong series.
PAIR = re.compile(
    r"(?:overall rate|overall electricity rate)[^.]{0,120}?"
    r"\bto\s*P\s?([\d,]+\.\d{2,4})\s*from\s*P\s?([\d,]+\.\d{2,4})\s*per kWh"
    r"(?:\s*in\s*([A-Z][a-z]+))?", re.I)
SINGLE = re.compile(
    r"(?:overall rate|typical household)[^.]{0,140}?P\s?([\d,]+\.\d{2,4})\s*per kWh", re.I)
# a sanity band: a residential all-in rate is not 0.38 and not 40
def plausible(v):
    return 8.0 <= v <= 20.0


def text_of(url):
    h = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                               timeout=45).read().decode("utf-8", "replace")
    t = re.sub(r"<[^>]+>", " ", h)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    return re.sub(r"\s+", " ", t)


def num(s):
    return float(s.replace(",", ""))


def main():
    today = dt.date.today()
    start_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
    rates, cover = {}, []          # rates[(y,m_idx)] = (value, slug)
    conflicts = []

    for y in range(start_year, today.year + 1):
        for mi, m in enumerate(MONTHS, 1):
            if (y, mi) > (today.year, today.month):
                continue
            found = None
            for p in PATTERNS:
                slug = p.format(m=m, y=y)
                try:
                    t = text_of(BASE + slug)
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                    continue
                except Exception:
                    continue
                if "per kWh" not in t:
                    continue
                pair = PAIR.search(t)
                if pair and plausible(num(pair.group(1))) and plausible(num(pair.group(2))):
                    cur, prev = num(pair.group(1)), num(pair.group(2))
                    found = (cur, slug)
                    pm = mi - 1 if mi > 1 else 12
                    py = y if mi > 1 else y - 1
                    key = (py, pm)
                    if key in rates and abs(rates[key][0] - prev) > 0.0001:
                        conflicts.append((key, rates[key][0], prev, slug))
                    elif key not in rates and py >= start_year:
                        rates[key] = (prev, slug + " (prior month)")
                else:
                    s = SINGLE.search(t)
                    if s and plausible(num(s.group(1))):
                        found = (num(s.group(1)), slug)
                if found:
                    break
                time.sleep(0.05)

            if found:
                if (y, mi) in rates and abs(rates[(y, mi)][0] - found[0]) > 0.0001:
                    conflicts.append(((y, mi), rates[(y, mi)][0], found[0], found[1]))
                rates[(y, mi)] = found
                cover.append([y, mi, "found", found[1]])
            else:
                cover.append([y, mi, "not found", ""])
        print("  %d: %d months so far" % (y, len(rates)))

    rows = [[y, m, "%.4f" % v, slug, "Meralco rate advisory"]
            for (y, m), (v, slug) in sorted(rates.items())]
    with open(os.path.join(OUT, "ph_meralco_monthly.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "rate_php_per_kwh", "source_slug", "source"])
        w.writerows(rows)
    with open(os.path.join(OUT, "ph_meralco_coverage.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "status", "source_slug"])
        w.writerows(cover)
    print("  wrote %d monthly rates, %d months attempted" % (len(rows), len(cover)))
    if conflicts:
        print("  %d overlap conflicts (same month, two advisories):" % len(conflicts))
        for k, a, b, s in conflicts[:8]:
            print("    %s: %.4f vs %.4f  (%s)" % (k, a, b, s))
    else:
        print("  no overlap conflicts -- consecutive advisories agree")


if __name__ == "__main__":
    main()
