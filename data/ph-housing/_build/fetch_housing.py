#!/usr/bin/env python3
"""Two sources, because one of them cannot carry the page on its own.

The published page was built on a Kaggle scrape of 1,500 property listings and
presented it as "Philippine Housing Market Analysis" with an average price of
32.8 million pesos. The scrape is real and the average is arithmetically
correct, but a listing dump is not a market:

  * these are asking prices from a property portal, not transactions, and no
    listing carries a date, so there is no time dimension at all;
  * the mean is 3.57x the median because 103 of the 1,500 listings ask a hundred
    million pesos or more, one of them 2.5 billion -- so the "average price" is a
    statement about the advertised luxury tail, not about houses;
  * coverage is whatever the scraper happened to hit. Muntinlupa gets 138
    listings; most of the Visayas gets none. It is not a sample of anything.

So the listings stay -- they are genuinely interesting about how a portal's
inventory is shaped -- but the page also carries World Bank / WHO-UNICEF JMP
figures on how Philippine households actually live, which are national, have a
time series, and split urban from rural. The two halves disagree, and that
disagreement is the finding.

Writes:
  ph_housing_listings.csv        one row per listing, cleaned
  ph_housing_by_city.csv         listing counts and medians per city token
  ph_housing_by_bedroom.csv      median price by bedroom count, with n
  ph_housing_price_bands.csv     how the 1,500 distribute across price bands
  ph_housing_conditions.csv      national service levels, 2000-2024
  ph_housing_urban_rural.csv     the same, split urban / rural
  ph_housing_asean.csv           clean cooking and safe water across ASEAN
  ph_housing_coverage.csv        what the listing scrape does and does not reach
"""
import csv
import io
import os
import sys
import zipfile
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
KAGGLE = ("https://www.kaggle.com/api/v1/datasets/download/"
          "klekzee/phillipines-housing-market")
SRC_L = "Kaggle klekzee/phillipines-housing-market (portal scrape, 2024)"
SRC_W = "World Bank WDI (WHO/UNICEF JMP; IEA/WHO for cooking fuel)"

ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia", "SGP": "Singapore"}


def write(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-32s %5d rows" % (name, len(rows)))


def listings():
    """Download the scrape and clean it, without committing the archive."""
    req = urllib.request.Request(KAGGLE, headers={"User-Agent": "Mozilla/5.0"})
    blob = urllib.request.urlopen(req, timeout=180).read()
    z = zipfile.ZipFile(io.BytesIO(blob))
    # Two files ship: Housing_v2.csv and PH_Housing.csv. The latter is the same
    # rows with an id column added, so prefer it and do not merge them -- they
    # would double every listing.
    name = "PH_Housing.csv"
    if name not in z.namelist():
        raise SystemExit("archive layout changed: %s" % z.namelist())
    txt = z.read(name).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(txt)))
    if len(rows) != 1500:
        print("  note: %d listings, not the 1,500 the page was built on" % len(rows))

    def num(v):
        v = (v or "").strip()
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    out, seen, dupes = [], set(), 0
    for r in rows:
        price = num(r.get("Price"))
        loc = (r.get("Location") or "").strip()
        desc = (r.get("Description") or "").strip()
        key = (desc, loc, r.get("Price"))
        if key in seen:
            dupes += 1
        seen.add(key)
        # City is the token after the last comma. It is a city for most rows and
        # a province for some, so the column is named for what it is.
        city = loc.split(",")[-1].strip() if loc else "(no location given)"
        out.append([
            r.get("HouseID"), desc[:180], loc, city,
            "" if price is None else int(price),
            _i(num(r.get("Bedrooms"))), _i(num(r.get("Bathrooms"))),
            _f(num(r.get("Floor Area"))), _f(num(r.get("Land Area"))),
            _f(num(r.get("Latitude")), 6), _f(num(r.get("Longitude")), 6),
            "",  # occurrence, filled in below
            SRC_L,
        ])
    # Mark duplicates properly: a row is a repeat if an identical
    # (description, location, price) appeared earlier in the file.
    seen2, marks = set(), []
    for r in out:
        key = (r[1], r[2], r[4])
        marks.append("repeat" if key in seen2 else "first")
        seen2.add(key)
    for r, m in zip(out, marks):
        r[11] = m
    write("ph_housing_listings.csv",
          ["listing_id", "description", "location", "city_token", "price_php",
           "bedrooms", "bathrooms", "floor_area_sqm", "land_area_sqm",
           "latitude", "longitude", "occurrence", "source"], out)
    print("  %d listing(s) repeat an earlier row exactly" % marks.count("repeat"))
    return out


def _i(v):
    return "" if v is None else int(v)


def _f(v, nd=2):
    return "" if v is None else round(v, nd)


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def derived(rows):
    priced = [r for r in rows if r[4] != ""]

    by = {}
    for r in rows:
        by.setdefault(r[3], []).append(r)
    city_rows = []
    for city, rs in by.items():
        ps = [r[4] for r in rs if r[4] != ""]
        # Price per square metre of floor area is the only figure that compares a
        # Muntinlupa mansion with a Cavite townhouse, so it is carried per city
        # alongside the raw medians -- but only where both fields are present.
        psm = [r[4] / r[7] for r in rs if r[4] != "" and r[7] not in ("", 0)]
        city_rows.append([city, len(rs), len(ps),
                          int(med(ps)) if ps else "",
                          int(round(sum(ps) / len(ps))) if ps else "",
                          len(psm), int(round(med(psm))) if psm else "", SRC_L])
    city_rows.sort(key=lambda r: (-r[1], r[0]))
    write("ph_housing_by_city.csv",
          ["city_token", "listings", "listings_priced", "median_price_php",
           "mean_price_php", "listings_with_floor_area", "median_price_per_sqm",
           "source"], city_rows)

    bed = {}
    for r in priced:
        if r[5] != "":
            bed.setdefault(int(r[5]), []).append(r[4])
    write("ph_housing_by_bedroom.csv",
          ["bedrooms", "listings", "median_price_php", "source"],
          [[b, len(v), int(med(v)), SRC_L] for b, v in sorted(bed.items())])

    BANDS = [(0, 3e6, "under ₱3M"), (3e6, 6e6, "₱3M–6M"),
             (6e6, 10e6, "₱6M–10M"), (10e6, 20e6, "₱10M–20M"),
             (20e6, 50e6, "₱20M–50M"), (50e6, 100e6, "₱50M–100M"),
             (100e6, float("inf"), "₱100M and up")]
    ps = [r[4] for r in priced]
    write("ph_housing_price_bands.csv",
          ["band", "lower_php", "upper_php", "listings", "pct_of_priced",
           "source"],
          [[lab, int(lo), "" if hi == float("inf") else int(hi),
            sum(1 for p in ps if lo <= p < hi),
            round(100.0 * sum(1 for p in ps if lo <= p < hi) / len(ps), 2),
            SRC_L] for lo, hi, lab in BANDS])

    # What the scrape reaches. Coverage that lives only in a log is coverage
    # nobody can audit.
    lats = [r[9] for r in rows if r[9] != ""]
    cov = [
        ["listings in file", len(rows), "", SRC_L],
        ["listings with a price", len(priced),
         "%.2f%% of rows" % (100.0 * len(priced) / len(rows)), SRC_L],
        ["listings repeating an earlier row", sum(1 for r in rows if r[11] == "repeat"),
         "identical description, location and price", SRC_L],
        ["distinct city or province tokens", len(by), "", SRC_L],
        ["listings in the single most-covered token", max(len(v) for v in by.values()),
         max(by, key=lambda k: len(by[k])), SRC_L],
        ["southernmost latitude reached", min(lats),
         "Mindanao is reached but thinly", SRC_L],
        ["northernmost latitude reached", max(lats), "", SRC_L],
        ["listings asking ₱100M or more", sum(1 for p in ps if p >= 100e6),
         "these set the mean", SRC_L],
        ["dated listings", 0,
         "no listing carries a date, so no trend can be computed", SRC_L],
        ["transaction prices", 0,
         "every price is an asking price", SRC_L],
        ["survey weights", 0,
         "a portal scrape is not a sample; nothing scales to the country", SRC_L],
    ]
    write("ph_housing_coverage.csv",
          ["property", "value", "note", "source"], cov)


IND = [("SH.H2O.BASW.ZS", "basic_water_pct"),
       ("SH.H2O.SMDW.ZS", "safe_water_pct"),
       ("SH.STA.BASS.ZS", "basic_sanitation_pct"),
       ("SH.STA.SMSS.ZS", "safe_sanitation_pct"),
       ("EG.ELC.ACCS.ZS", "electricity_pct"),
       ("EG.CFT.ACCS.ZS", "clean_cooking_pct"),
       ("SP.URB.TOTL.IN.ZS", "urban_pop_pct"),
       ("EN.POP.SLUM.UR.ZS", "urban_slum_pct")]

SPLIT = [("SH.H2O.BASW", "basic_water"), ("SH.STA.BASS", "basic_sanitation"),
         ("EG.ELC.ACCS", "electricity"), ("EG.CFT.ACCS", "clean_cooking")]


def conditions():
    got = {n: wb.series("PHL", c) for c, n in IND}
    years = sorted(set().union(*(set(v) for v in got.values())))
    rows = [[y] + [round(got[n][y], 2) if y in got[n] else "" for _, n in IND]
            + [SRC_W] for y in years]
    write("ph_housing_conditions.csv",
          ["year"] + [n for _, n in IND] + ["source"], rows)

    rows = []
    for base, name in SPLIT:
        u = wb.series("PHL", base + ".UR.ZS")
        r = wb.series("PHL", base + ".RU.ZS")
        for y in sorted(set(u) & set(r)):
            rows.append([name, y, round(u[y], 2), round(r[y], 2),
                         round(u[y] - r[y], 2), SRC_W])
    write("ph_housing_urban_rural.csv",
          ["service", "year", "urban_pct", "rural_pct", "gap_pp", "source"], rows)

    # The ASEAN comparison uses the *basic* service tiers, not the safely-managed
    # ones. Safely-managed drinking water is unpublished for Thailand and
    # safely-managed sanitation for Indonesia, and a six-country chart that
    # quietly becomes a five-country chart reads as though the missing country
    # was never in it. So the harder measures stay on the national section, where
    # the Philippines has them, and the comparison sticks to what all six report.
    cook = {i: wb.series(i, "EG.CFT.ACCS.ZS") for i in ASEAN}
    sani = {i: wb.series(i, "SH.STA.BASS.ZS") for i in ASEAN}
    common = [y for y in range(2000, 2025)
              if all(y in cook[i] and y in sani[i] for i in ASEAN)]
    if not common:
        raise SystemExit("no year carries both series for all six countries")
    y = max(common)
    write("ph_housing_asean.csv",
          ["country", "year", "clean_cooking_pct", "basic_sanitation_pct",
           "tier", "source"],
          sorted(([ASEAN[i], y, round(cook[i][y], 2), round(sani[i][y], 2),
                   "basic", SRC_W] for i in ASEAN), key=lambda r: r[2]))
    print("  ASEAN comparison year: %d" % y)


if __name__ == "__main__":
    print("listings")
    derived(listings())
    print("conditions")
    conditions()
