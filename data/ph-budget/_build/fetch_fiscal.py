#!/usr/bin/env python3
"""Philippine public finances, from the World Bank and the IMF.

    .venv/bin/python data/ph-budget/_build/fetch_fiscal.py

DBM publishes the enacted budget and BTr the debt stock, but neither offers a
machine-readable series and dof.gov.ph returns 403 to scripts. What is open, and
internationally comparable, is the World Bank's central-government fiscal
indicators and the IMF's general-government aggregates. Both are keyless JSON.

Two things this pipeline is careful about:

* The IMF DataMapper returns FORECASTS in the same array as history -- the debt
  series runs to 2031. Charting them together draws a projection as if it were a
  measurement. Every IMF row is therefore flagged actual or projection against
  the vintage year, and the page draws projections as a separate dashed series.

* "Central government" (World Bank) and "general government" (IMF) are different
  perimeters -- the second includes local government and social security. Their
  numbers do not agree and are not supposed to. They are kept in separate tables
  with the perimeter named in the column, rather than blended into one series
  that would be wrong at every point.

Peso absolutes are derived, never quoted: a share of GDP multiplied by GDP in
current pesos. The derivation is marked on the row so nobody mistakes it for a
published figure from DBM.
"""
import csv
import json
import os
import ssl
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
UA = "allanninal.dev research (contact via github.com/allanninal)"
WB = "World Bank World Development Indicators API v2"
IMF = "IMF DataMapper API v1 (World Economic Outlook)"

WB_IND = {
    "GC.XPN.TOTL.GD.ZS": "expense_pct_gdp",
    "GC.REV.XGRT.GD.ZS": "revenue_ex_grants_pct_gdp",
    "GC.TAX.TOTL.GD.ZS": "tax_revenue_pct_gdp",
    "GC.NLD.TOTL.GD.ZS": "net_lending_pct_gdp",
    "GC.XPN.INTP.ZS": "interest_pct_of_expense",
    "NY.GDP.MKTP.CN": "gdp_current_php",
}
IMF_IND = {"GGXWDG_NGDP": "gross_debt_pct_gdp",
           "GGXCNL_NGDP": "net_lending_pct_gdp",
           "rev": "revenue_pct_gdp",
           "exp": "expenditure_pct_gdp"}
# ASEAN-5. Singapore is left out because the IMF publishes no general
# government revenue series for it, and a comparison that quietly drops a
# country reads as a comparison that never included it.
ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia"}
# The last year the IMF treats as observed rather than projected. WEO vintages
# move this forward; it is asserted in checks.sql rather than assumed silently.
LAST_ACTUAL = 2024


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120,
                                context=ssl.create_default_context()) as r:
        return json.loads(r.read())


def wb(iso, code):
    d = fetch("https://api.worldbank.org/v2/country/%s/indicator/%s"
              "?format=json&per_page=500" % (iso, code))
    if len(d) < 2 or not d[1]:
        raise SystemExit("empty World Bank payload for %s %s" % (iso, code))
    return {int(r["date"]): r["value"] for r in d[1] if r["value"] is not None}


_IMF_CACHE = {}


def imf_all(code):
    """{iso: {year: value}} for one indicator, fetched once.

    The DataMapper ignores the country path segments and returns every country
    regardless, so asking per country is one HTTP round trip per country for the
    same payload -- and doing that in a loop gets the client rate-limited with a
    403 partway through, which looks exactly like a missing indicator. Fetch
    once, filter locally.
    """
    if code not in _IMF_CACHE:
        d = fetch("https://www.imf.org/external/datamapper/api/v1/%s" % code)
        vals = d.get("values", {}).get(code, {})
        if not vals:
            raise SystemExit("empty IMF payload for %s -- a wrong indicator code "
                             "returns {} rather than an error" % code)
        _IMF_CACHE[code] = {iso: {int(y): v for y, v in series.items()
                                  if v is not None}
                            for iso, series in vals.items()}
    return _IMF_CACHE[code]


def imf(code, iso):
    got = imf_all(code).get(iso)
    if not got:
        raise SystemExit("IMF publishes no %s series for %s" % (code, iso))
    return got


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    ph = {label: wb("PHL", code) for code, label in WB_IND.items()}
    years = sorted(set().union(*[set(v) for v in ph.values()]))
    years = [y for y in years if y >= 1990]
    rows = []
    for y in years:
        gdp = ph["gdp_current_php"].get(y)
        # Derived from the ROUNDED share that this CSV publishes, not from the
        # full-precision API value. Otherwise the peso column cannot be
        # recomputed from the columns beside it, and checks.sql -- which
        # recomputes it -- fails by a few thousand pesos on every row.
        exp = round(ph["expense_pct_gdp"][y], 3) if y in ph["expense_pct_gdp"] else None
        rev = (round(ph["revenue_ex_grants_pct_gdp"][y], 3)
               if y in ph["revenue_ex_grants_pct_gdp"] else None)
        rows.append([
            y,
            exp,
            rev,
            round(ph["tax_revenue_pct_gdp"][y], 3) if y in ph["tax_revenue_pct_gdp"] else None,
            round(ph["net_lending_pct_gdp"][y], 3) if y in ph["net_lending_pct_gdp"] else None,
            round(ph["interest_pct_of_expense"][y], 3)
            if y in ph["interest_pct_of_expense"] else None,
            int(gdp) if gdp is not None else None,
            # Derived, not published. Marked as such on the row.
            round(gdp * exp / 100) if (gdp is not None and exp is not None) else None,
            round(gdp * rev / 100) if (gdp is not None and rev is not None) else None,
            "central government", "derived: share of GDP x GDP in current PHP", WB])
    write("ph_budget_annual.csv",
          ["year", "expense_pct_gdp", "revenue_ex_grants_pct_gdp",
           "tax_revenue_pct_gdp", "net_lending_pct_gdp", "interest_pct_of_expense",
           "gdp_current_php", "expense_php_derived", "revenue_php_derived",
           "perimeter", "derivation", "source"], rows)

    dr = []
    for code, label in IMF_IND.items():
        s = imf(code, "PHL")
        for y in sorted(s):
            dr.append([y, label, round(s[y], 3),
                       "actual" if y <= LAST_ACTUAL else "projection",
                       "general government", IMF])
    write("ph_budget_imf.csv",
          ["year", "metric", "value_pct_gdp", "basis", "perimeter", "source"], dr)

    # ASEAN at the latest year every country actually has, so the comparison is
    # like for like rather than each country's own most recent print.
    # World Bank tax revenue cannot carry this comparison: it has nothing at all
    # for Vietnam and stops at 2009 for Indonesia. IMF general-government revenue
    # covers all five, so the comparison uses it -- and says "revenue", not
    # "tax", because they are not the same thing.
    rev = {i: imf("rev", i) for i in ASEAN}
    debt = {i: imf("GGXWDG_NGDP", i) for i in ASEAN}
    common = [y for y in range(1990, LAST_ACTUAL + 1)
              if all(y in rev[i] and y in debt[i] for i in ASEAN)]
    if not common:
        raise SystemExit("no year has revenue and debt for all five countries")
    y = max(common)
    write("ph_budget_asean.csv",
          ["country", "year", "revenue_pct_gdp", "gross_debt_pct_gdp",
           "perimeter", "basis", "source"],
          sorted(([ASEAN[i], y, round(rev[i][y], 2), round(debt[i][y], 2),
                   "general government", "actual", IMF] for i in ASEAN),
                 key=lambda r: r[2]))
    print("  ASEAN comparison year: %d" % y)

    cov = []
    for label, series in ph.items():
        got = sorted(k for k in series if k >= 1990)
        cov.append([label, "central government", got[0], got[-1], len(got),
                    len([k for k in range(got[0], got[-1] + 1) if k not in series]),
                    WB])
    for code, label in IMF_IND.items():
        s = imf(code, "PHL")
        got = sorted(s)
        cov.append([label, "general government", got[0], got[-1], len(got),
                    len([k for k in range(got[0], got[-1] + 1) if k not in s]), IMF])
    write("ph_budget_coverage.csv",
          ["metric", "perimeter", "first_year", "last_year", "points",
           "gap_years_inside_range", "source"], cov)


if __name__ == "__main__":
    main()
