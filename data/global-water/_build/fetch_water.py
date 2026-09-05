#!/usr/bin/env python3
"""Drinking water, sanitation and hygiene: the generous number and the strict one.

The WHO/UNICEF Joint Monitoring Programme publishes a service ladder, and two
rungs of it get quoted as if they were the same thing:

  at least basic   an improved source within a 30-minute round trip
  safely managed   improved, ON the premises, available when needed, and free
                   from faecal and priority chemical contamination

"Safely managed" is the SDG 6.1.1 indicator. "At least basic" is the number that
reaches a headline. They are not close to each other, and for a large part of the
world the strict one does not exist at all.

Two publishers carry the same JMP series and neither carries all of it, so both
are read: WHO's Global Health Observatory, which also splits urban from rural,
and the World Bank's WDI. Every country-year they share is compared and the
script aborts if any pair disagrees.

Free, no key, no account:
  https://ghoapi.azureedge.net/api/      WHO GHO OData
  https://api.worldbank.org/v2/          World Bank WDI
"""
import collections
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
UA = {"User-Agent": "allanninal.dev research (WASH ladder analysis)"}

GHO = "https://ghoapi.azureedge.net/api/"
WB = "https://api.worldbank.org/v2/"

GHO_SRC = "WHO Global Health Observatory (JMP), ghoapi.azureedge.net"
WB_SRC = "World Bank WDI (JMP), api.worldbank.org"

# GHO code -> the short name used in the CSVs
INDICATORS = [
    ("WSH_WATER_BASIC",               "water_basic"),
    ("WSH_WATER_SAFELY_MANAGED",      "water_safely_managed"),
    ("WSH_SANITATION_BASIC",          "sanitation_basic"),
    ("WSH_SANITATION_SAFELY_MANAGED", "sanitation_safely_managed"),
    ("WSH_HYGIENE_BASIC",             "handwashing_basic"),
]

# Open defecation is read from the World Bank rather than from GHO. GHO carries
# the series, but at country level every row has NumericValue null and only a
# string in Value rounded to whole percent -- 14,548 rows, 525 of them numeric,
# and all 525 are regional or global aggregates. Reading NumericValue the way
# every other indicator here is read drops all 14,023 country rows while the
# request itself succeeds, which is the shape of failure this repo distrusts
# most. The rounded copy is still used, below, as a half-point cross-check.
GHO_ROUNDED = {"open_defecation": "WSH_SANITATION_OD"}
ROUNDED_TOLERANCE = 0.51                    # GHO rounds these to whole percent

# the World Bank's copy of the same series, for the cross-check
WB_MIRROR = {"water_basic": "SH.H2O.BASW.ZS",
             "water_safely_managed": "SH.H2O.SMDW.ZS",
             "sanitation_basic": "SH.STA.BASS.ZS",
             "sanitation_safely_managed": "SH.STA.SMSS.ZS",
             "open_defecation": "SH.STA.ODFC.ZS",
             "handwashing_basic": "SH.STA.HYGN.ZS"}

RESIDENCE = {"RESIDENCEAREATYPE_TOTL": "total",
             "RESIDENCEAREATYPE_URB": "urban",
             "RESIDENCEAREATYPE_RUR": "rural"}

# The two publishers round to different precision in a handful of places, so the
# cross-check is not exact-equality; it is a tolerance tight enough that a real
# vintage difference cannot hide under it. Observed maximum in Sept 2026: 0.0.
TOLERANCE = 0.05


def fetch(url, tries=4):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as e:
            if n == tries - 1:
                raise
            sys.stderr.write("  retry %d/%d %s -- %s\n" % (n + 1, tries, url[:70], e))
            time.sleep(3 * (n + 1))


def wb(path, **kw):
    q = "&".join("%s=%s" % (k, v) for k, v in kw.items())
    return fetch(WB + path + "?format=json&per_page=20000&" + q)


def write(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("  %-26s %6d row(s)" % (name, len(rows)))


def main():
    # ---- country metadata: which codes are countries and which are aggregates
    meta = {}
    for c in wb("country")[1]:
        meta[c["id"]] = {
            "name": c["name"],
            "region": c["region"]["value"],
            "region_id": c["region"]["id"],
            "income": c["incomeLevel"]["value"],
        }
    countries = {k for k, v in meta.items() if v["region_id"] != "NA"}
    print("country metadata: %d countries, %d aggregates"
          % (len(countries), len(meta) - len(countries)))

    # ---- population, for weighting a share by the people it describes
    pop = collections.defaultdict(dict)
    for r in wb("country/all/indicator/SP.POP.TOTL", date="2000:2024")[1]:
        if r["value"] is not None:
            pop[r["countryiso3code"]][int(r["date"])] = int(r["value"])

    # ---- the ladder, from WHO GHO (which also splits urban from rural)
    gho = collections.defaultdict(dict)          # (iso3, year, residence) -> {ind: val}
    world = collections.defaultdict(dict)        # (scope, year, residence) -> {ind: val}
    region_of = {}
    for code, short in INDICATORS:
        d = fetch(GHO + code)
        n = 0
        for r in d["value"]:
            res = RESIDENCE.get(r.get("Dim1"))
            v = r.get("NumericValue")
            if res is None or v is None:
                continue
            y = r["TimeDim"]
            if r["SpatialDimType"] == "COUNTRY":
                gho[(r["SpatialDim"], y, res)][short] = v
                if r.get("ParentLocationCode"):
                    region_of[r["SpatialDim"]] = r["ParentLocationCode"]
                n += 1
            elif r["SpatialDimType"] in ("GLOBAL", "REGION"):
                world[(r["SpatialDim"], y, res)][short] = v
        print("  %-32s %6d country row(s)" % (code, n))

    # ---- the rounded-only series, kept for the half-point cross-check
    rounded = collections.defaultdict(dict)
    for short, code in GHO_ROUNDED.items():
        d = fetch(GHO + code)
        n = 0
        for r in d["value"]:
            res = RESIDENCE.get(r.get("Dim1"))
            raw = r.get("Value")
            if res is None or raw in (None, ""):
                continue
            # the aggregates DO carry a real NumericValue -- it is only the
            # country rows that arrive rounded -- so world and regional totals
            # for this indicator are as precise as every other one here
            if r["SpatialDimType"] in ("GLOBAL", "REGION"):
                if r.get("NumericValue") is not None:
                    world[(r["SpatialDim"], r["TimeDim"], res)][short] = r["NumericValue"]
                continue
            if res != "total" or r["SpatialDimType"] != "COUNTRY":
                continue
            try:
                rounded[(r["SpatialDim"], r["TimeDim"])][short] = float(raw)
            except ValueError:
                continue
            n += 1
        print("  %-32s %6d country row(s), rounded to whole percent" % (code, n))

    # ---- WASH-attributable mortality, the consequence the ladder is measuring
    deaths = {}
    for r in fetch(GHO + "WSH_3")["value"]:
        if r["SpatialDimType"] == "COUNTRY" and r.get("NumericValue") is not None:
            deaths[(r["SpatialDim"], r["TimeDim"])] = r["NumericValue"]
    print("  %-32s %6d country row(s)" % ("WSH_3 (deaths per 100k)", len(deaths)))

    # ---- the same series from the World Bank, for the cross-check
    wbv = collections.defaultdict(dict)
    for short, ind in WB_MIRROR.items():
        for r in wb("country/all/indicator/" + ind, date="2000:2024")[1]:
            if r["value"] is not None and r["countryiso3code"]:
                wbv[(r["countryiso3code"], int(r["date"]))][short] = r["value"]

    # ---- open defecation, from the World Bank, checked against GHO's rounding
    od_rows, od_worst, od_n = [], 0.0, 0
    for (iso, y), vals in wbv.items():
        v = vals.get("open_defecation")
        if v is None:
            continue
        gho[(iso, y, "total")]["open_defecation"] = v
        g = rounded.get((iso, y), {}).get("open_defecation")
        if g is None:
            continue
        od_n += 1
        od_worst = max(od_worst, abs(v - g))
        od_rows.append([iso, y, "open_defecation", "%.4f" % g, "%.4f" % v,
                        "%.4f" % abs(v - g), "WHO GHO (rounded) vs World Bank WDI"])
    if od_worst > ROUNDED_TOLERANCE:
        sys.stderr.write("\nCROSS-CHECK FAILED: open defecation disagrees by %.4f "
                         "points, more than the %.2f a whole-percent rounding "
                         "can explain\n" % (od_worst, ROUNDED_TOLERANCE))
        raise SystemExit(1)
    print("open defecation: %d pair(s) checked against GHO's rounded copy, "
          "worst gap %.4f points (rounding allows %.2f)"
          % (od_n, od_worst, ROUNDED_TOLERANCE))

    # ---- cross-check, and abort on any disagreement -------------------------
    rows, worst, checked = [], 0.0, 0
    for (iso, y, res), vals in gho.items():
        if res != "total":
            continue
        for short, v in vals.items():
            if short == "open_defecation":
                continue                     # sourced from the World Bank above
            w = wbv.get((iso, y), {}).get(short)
            if w is None:
                continue
            checked += 1
            worst = max(worst, abs(v - w))
            rows.append([iso, y, short, "%.4f" % v, "%.4f" % w, "%.4f" % abs(v - w),
                         "WHO GHO vs World Bank WDI"])
    if worst > TOLERANCE:
        bad = [r for r in rows if float(r[5]) > TOLERANCE]
        sys.stderr.write("\nCROSS-CHECK FAILED: %d country-year-indicator pair(s) "
                         "disagree by more than %.2f points\n" % (len(bad), TOLERANCE))
        for r in bad[:12]:
            sys.stderr.write("  %s %s %s: GHO %s  WB %s\n" % tuple(r[:5]))
        raise SystemExit(1)
    print("cross-check: %d overlapping country-year-indicator pair(s), "
          "worst disagreement %.4f points" % (checked, worst))
    write("gw_crosscheck.csv",
          ["iso3", "year", "indicator", "who_gho", "world_bank", "abs_diff", "source"],
          sorted(rows + od_rows, key=lambda r: (-float(r[5]), r[0], r[1])))

    # ---- union of the two publishers: neither carries the whole series -------
    only_gho = only_wb = 0
    for (iso, y, res), vals in gho.items():
        if res == "total":
            for short in vals:
                if short not in wbv.get((iso, y), {}):
                    only_gho += 1
    for (iso, y), vals in wbv.items():
        for short in vals:
            if short not in gho.get((iso, y, "total"), {}):
                only_wb += 1
    print("union: %d pair(s) only in GHO, %d only in the World Bank" % (only_gho, only_wb))

    # ---- the long series ----------------------------------------------------
    years = sorted({y for (_, y, _) in gho})
    srows = []
    for (iso, y, res), vals in sorted(gho.items()):
        if iso not in countries:
            continue
        for short, v in sorted(vals.items()):
            srows.append([iso, meta[iso]["name"], y, res, short, round(v, 4), GHO_SRC])
    write("gw_series.csv",
          ["iso3", "country", "year", "residence", "indicator", "pct", "source"], srows)

    # ---- one row per country, at the most recent year each one has ----------
    latest = max(years)
    crows = []
    for iso in sorted(countries):
        # the latest year with a total-residence reading of anything
        ys = [y for (i, y, r) in gho if i == iso and r == "total"]
        if not ys:
            continue
        y = max(ys)
        tot = gho.get((iso, y, "total"), {})
        urb = gho.get((iso, y, "urban"), {})
        rur = gho.get((iso, y, "rural"), {})
        g = lambda d, k: ("" if d.get(k) is None else round(d[k], 2))
        wb_ = g(tot, "water_basic")
        wsm = g(tot, "water_safely_managed")
        crows.append([
            iso, meta[iso]["name"], meta[iso]["region"], meta[iso]["income"], y,
            pop.get(iso, {}).get(y) or pop.get(iso, {}).get(latest) or "",
            wb_, wsm,
            ("" if wb_ == "" or wsm == "" else round(wb_ - wsm, 2)),
            g(tot, "sanitation_basic"), g(tot, "sanitation_safely_managed"),
            g(tot, "open_defecation"), g(tot, "handwashing_basic"),
            g(urb, "water_safely_managed"), g(rur, "water_safely_managed"),
            ("" if deaths.get((iso, y)) is None else round(deaths[(iso, y)], 2)),
            GHO_SRC,
        ])
    write("gw_country.csv",
          ["iso3", "country", "region", "income_group", "year", "population",
           "water_basic_pct", "water_safely_managed_pct", "basic_minus_safely_pts",
           "sanitation_basic_pct", "sanitation_safely_managed_pct",
           "open_defecation_pct", "handwashing_basic_pct",
           "water_safely_managed_urban_pct", "water_safely_managed_rural_pct",
           "wash_deaths_per_100k", "source"], crows)

    # ---- the coverage file: who has a strict figure and who does not --------
    mrows = []
    for r in crows:
        iso, name, region, income, y, p = r[0], r[1], r[2], r[3], r[4], r[5]
        has_w = r[7] != ""
        has_s = r[10] != ""
        mrows.append([iso, name, region, income, y, p,
                      "yes" if r[6] != "" else "no",
                      "yes" if has_w else "no",
                      "yes" if has_s else "no",
                      "reported" if has_w else "basic only, no safely-managed estimate",
                      GHO_SRC])
    write("gw_coverage_country.csv",
          ["iso3", "country", "region", "income_group", "year", "population",
           "has_water_basic", "has_water_safely_managed",
           "has_sanitation_safely_managed", "status", "source"], mrows)

    # ---- world and WHO-region aggregates, as published ----------------------
    wrows = []
    for (scope, y, res), vals in sorted(world.items()):
        for short, v in sorted(vals.items()):
            wrows.append([scope, y, res, short, round(v, 4), GHO_SRC])
    write("gw_world.csv", ["scope", "year", "residence", "indicator", "pct", "source"],
          wrows)

    # ---- the headline coverage numbers, as their own file -------------------
    have_b = [r for r in crows if r[6] != ""]
    have_s = [r for r in crows if r[7] != ""]
    miss = [r for r in crows if r[6] != "" and r[7] == ""]
    p = lambda rs: sum(int(r[5]) for r in rs if r[5] != "")
    cov = [
        ["countries with a basic drinking water figure", len(have_b), "count", GHO_SRC],
        ["countries with a safely managed drinking water figure", len(have_s), "count", GHO_SRC],
        ["countries with basic but no safely managed figure", len(miss), "count", GHO_SRC],
        ["population in those countries", p(miss), "people", WB_SRC],
        ["population in all countries with a basic figure", p(have_b), "people", WB_SRC],
        ["share of that population with no safely managed figure",
         round(100.0 * p(miss) / p(have_b), 2) if p(have_b) else "", "percent", WB_SRC],
        ["first year", min(years), "year", GHO_SRC],
        ["last year", latest, "year", GHO_SRC],
        ["cross-checked country-year-indicator pairs", checked, "count",
         "WHO GHO vs World Bank WDI"],
        ["worst cross-check disagreement", round(worst, 4), "percentage points",
         "WHO GHO vs World Bank WDI"],
        ["pairs only in WHO GHO", only_gho, "count", GHO_SRC],
        ["pairs only in the World Bank", only_wb, "count", WB_SRC],
        ["open defecation pairs checked against GHO's rounded copy", od_n, "count",
         "WHO GHO (rounded) vs World Bank WDI"],
        ["worst open defecation gap", round(od_worst, 4), "percentage points",
         "GHO rounds these to whole percent, so anything up to 0.5 is the rounding"],
        ["service ladder rungs compared", 2, "count",
         "at least basic, and safely managed"],
    ]
    write("gw_coverage.csv", ["property", "value", "unit", "source"], cov)

    print("\n%d countries have a basic figure; %d of them have no safely managed "
          "figure, covering %.0f million people (%.1f%%)."
          % (len(have_b), len(miss), p(miss) / 1e6, 100.0 * p(miss) / p(have_b)))


if __name__ == "__main__":
    main()
