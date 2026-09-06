#!/usr/bin/env python3
"""Every export is somebody's import, and the two numbers do not match.

The Philippines reports exporting $12.48bn to the United States in 2022. The
United States reports importing $16.88bn from the Philippines. Same goods, same
ocean, same year, two national statistics offices, a 35% disagreement.

Part of that gap is definitional and has to be removed before anything is
claimed. Exports are valued FOB -- at the dock, before freight and insurance --
and imports CIF, with freight and insurance included, so an import figure should
exceed its matching export figure by roughly the cost of shipping. Comtrade
publishes both valuations, so this script compares FOB against FOB and reports
the residual, which is the part shipping cannot explain.

The residual is not small and it is not random. It is also, at world level,
impossible: summed across every reporter, the planet does not trade in balance
with itself.

One call per reporter returns every partner, so the whole panel is a few hundred
requests. Everything is cached on disk.

Free, no key:
  https://comtradeapi.un.org/public/v1/preview/C/A/HS   UN Comtrade preview
  https://comtradeapi.un.org/files/v1/app/reference/     reporter and partner lists
"""
import collections
import csv
import hashlib
import json
import os
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
UA = {"User-Agent": "allanninal.dev research (landix.ninal@gmail.com)"}

API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REF = "https://comtradeapi.un.org/files/v1/app/reference/"
SRC = "UN Comtrade, comtradeapi.un.org"

YEAR = 2022                      # settled; recent years get revised for a long time
TOP_N = 55                       # reporters, by total trade
PAUSE = 0.6
RETRY_CAP = 600                  # never sleep longer than this on a 429

# Comtrade publishes each reporter's trade with partner 0, "World", as its own
# row. That is the reporter's own total, computed by them, and it must equal the
# sum of the individual partner rows this script adds up. If it does not, the
# aggregation here is wrong and every gap below it is meaningless.
# Observed agreement is exact -- the partner rows sum to the reporter's own World
# total at a ratio of 1.000 -- so this is a guard against structural error rather
# than a precision allowance. It is what caught the un-aggregated first version,
# where Germany's exports summed to 433% of its stated total.
TOTAL_TOLERANCE = 0.02


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch(url, tries=5):
    cp = _cache_path(url)
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as fh:
            return json.load(fh)
    time.sleep(PAUSE)
    for n in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=300) as r:
                d = json.loads(r.read().decode("utf-8"))
            os.makedirs(CACHE, exist_ok=True)
            with open(cp, "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            return d
        except urllib.error.HTTPError as e:
            asked = float(e.headers.get("Retry-After") or 0)
            if e.code == 429 and asked > RETRY_CAP:
                raise SystemExit(
                    "\nRATE LIMIT: Comtrade asks for %.0f seconds (%.1f hours). That "
                    "is an allowance, not a queue. Anything fetched so far is cached "
                    "under %s and a later run resumes.\n"
                    % (asked, asked / 3600.0, CACHE))
            if e.code not in (429, 500, 502, 503) or n == tries - 1:
                raise
            w = asked or min(90, 15 * (n + 1))
            sys.stderr.write("  %d, waiting %.0fs (%d/%d)\n" % (e.code, w, n + 1, tries))
            time.sleep(w)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as e:
            if n == tries - 1:
                raise
            sys.stderr.write("  retry %d/%d -- %s\n" % (n + 1, tries, e))
            time.sleep(5 * (n + 1))


# Without these three, Comtrade returns the trade broken down by mode of
# transport, customs procedure and second partner -- 66 combinations for Germany
# -- so a partner appears many times and the preview endpoint's 500-row cap
# truncates the list somewhere arbitrary. Germany came back as 500 rows summing
# to a fifth of its real exports. motCode=0, customsCode=C00 and partner2Code=0
# are the "all of them" codes and give exactly one row per partner.
AGGREGATED = "&motCode=0&customsCode=C00&partner2Code=0"
ROW_CAP = 500                    # the preview endpoint's limit; hitting it is a bug


def flows(reporter, flow):
    d = fetch("%s?reporterCode=%d&period=%d&cmdCode=TOTAL&flowCode=%s%s"
              % (API, reporter, YEAR, flow, AGGREGATED))
    rows = d.get("data") or []
    if len(rows) >= ROW_CAP:
        raise SystemExit(
            "\nTRUNCATED: reporter %d flow %s returned %d rows, the preview "
            "endpoint's cap. The partner list is incomplete and every total "
            "derived from it would be wrong.\n" % (reporter, flow, len(rows)))
    seen = collections.Counter(r["partnerCode"] for r in rows)
    dupes = [k for k, n in seen.items() if n > 1]
    if dupes:
        raise SystemExit(
            "\nNOT AGGREGATED: reporter %d flow %s returns %d partner(s) more than "
            "once, so the rows are still split by some dimension.\n"
            % (reporter, flow, len(dupes)))
    return rows


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("  %-24s %6d row(s)" % (name, len(rows)))


def v(x, k):
    n = x.get(k)
    return float(n) if isinstance(n, (int, float)) and n > 0 else None


def main():
    # Two reference files, two different key prefixes for the same fields:
    # Reporters.json uses reporterCodeIsoAlpha3 and partnerAreas.json uses
    # PartnerCodeIsoAlpha3. Reading one with the other's key silently yields an
    # empty string for every country, which does not raise anything -- it just
    # makes every per-country filter match everything.
    name, iso = {}, {}
    for f in ("Reporters.json", "partnerAreas.json"):
        ref = fetch(REF + f)
        ref = ref["results"] if isinstance(ref, dict) and "results" in ref else ref
        for r in ref:
            if r.get("isGroup"):
                continue
            code = int(r.get("id") or r.get("reporterCode") or r.get("PartnerCode"))
            nm = (r.get("text") or r.get("reporterDesc") or r.get("PartnerDesc") or "")
            i3 = (r.get("reporterCodeIsoAlpha3") or r.get("PartnerCodeIsoAlpha3") or "")
            name.setdefault(code, nm.split(" (")[0])
            if i3:
                iso.setdefault(code, i3)
    have = sum(1 for v in iso.values() if v)
    print("reference: %d areas, %d with an ISO3 code" % (len(name), have))
    if have < 0.5 * len(name):
        raise SystemExit(
            "\nREFERENCE BROKEN: only %d of %d areas resolved an ISO3 code. The key "
            "names in the reference files have changed, and every per-country "
            "filter downstream would match everything.\n" % (have, len(name)))

    # ---- who to read: the largest traders, found from one probe call --------
    probe = flows(842, "M")                      # every partner of the United States
    rank = sorted((x for x in probe if x["partnerCode"] and x["partnerCode"] in name),
                  key=lambda x: -(v(x, "primaryValue") or 0))
    codes, seen = [], set()
    for x in rank:
        c = x["partnerCode"]
        if c not in seen:
            seen.add(c)
            codes.append(c)
        if len(codes) >= TOP_N - 1:
            break
    if 842 not in codes:
        codes.insert(0, 842)
    if 608 not in codes:                         # the Philippines, for the local hook
        codes.append(608)
    print("reading %d reporters" % len(codes))

    # ---- pull both directions for each -------------------------------------
    X = collections.defaultdict(dict)            # X[reporter][partner] = row
    M = collections.defaultdict(dict)
    totals = {}
    got = []
    for n, c in enumerate(codes, 1):
        xs, ms = flows(c, "X"), flows(c, "M")
        if not xs and not ms:
            print("  %-3d %-28s no data" % (c, name.get(c, "?")[:28]))
            continue
        got.append(c)
        for r in xs:
            (totals.setdefault(c, {}).__setitem__("X", v(r, "primaryValue"))
             if r["partnerCode"] == 0 else X[c].__setitem__(r["partnerCode"], r))
        for r in ms:
            (totals.setdefault(c, {}).__setitem__("M", v(r, "primaryValue"))
             if r["partnerCode"] == 0 else M[c].__setitem__(r["partnerCode"], r))
        print("  %3d/%d  %-28s exports to %d partners, imports from %d"
              % (n, len(codes), name.get(c, "?")[:28], len(X[c]), len(M[c])))

    # ---- the reporter's own total must equal the sum of its partner rows ---
    bad = []
    for c in got:
        for flow, d in (("X", X[c]), ("M", M[c])):
            stated = (totals.get(c) or {}).get(flow)
            if not stated:
                continue
            summed = sum(v(r, "primaryValue") or 0 for r in d.values())
            if summed and abs(summed - stated) / stated > TOTAL_TOLERANCE:
                bad.append((name.get(c, c), flow, stated, summed,
                            100.0 * (summed - stated) / stated))
    # Two different failures share this symptom and they need separating. If many
    # reporters disagree, or any disagrees wildly, the aggregation in this script
    # is broken and nothing below it can be trusted -- that is how the first
    # version was caught, with Germany's partner rows summing to 433% of its own
    # stated total. If one or two reporters disagree by a few per cent, that is a
    # country whose own submission is internally inconsistent, which is a fact
    # about the data and is recorded rather than hidden.
    checked = sum(1 for c in got for f in ("X", "M") if (totals.get(c) or {}).get(f))
    worst = max([abs(b[4]) for b in bad] or [0])
    if bad and (len(bad) > 0.1 * checked or worst > 50):
        sys.stderr.write("\nAGGREGATION FAILED: %d of %d reporter-flows disagree with "
                         "the reporter's own World total, worst %+.2f%%. That is a bug "
                         "in this script, not a quirk of one country.\n"
                         % (len(bad), checked, worst))
        for b in bad[:8]:
            sys.stderr.write("  %-24s %s stated %.4g summed %.4g (%+.2f%%)\n" % b)
        raise SystemExit(1)
    print("  aggregation check: %d of %d reporter-flows sum to the reporter's own "
          "World total within %.0f%%" % (checked - len(bad), checked,
                                         100 * TOTAL_TOLERANCE))
    for b in bad:
        print("    internally inconsistent: %s %s stated %.4g, own partner rows "
              "sum to %.4g (%+.2f%%)" % b)
    write("tm_selfmismatch.csv",
          ["reporter", "flow", "stated_world_total_usd", "partner_rows_sum_usd",
           "diff_pct", "source"],
          [[b[0], b[1], round(b[2]), round(b[3]), round(b[4], 2), SRC] for b in bad])

    # ---- flows ---------------------------------------------------------------
    frows = []
    for c in got:
        for flow, d in (("X", X[c]), ("M", M[c])):
            for p, r in sorted(d.items()):
                frows.append([c, iso.get(c, ""), name.get(c, ""), p, iso.get(p, ""),
                              name.get(p, ""), flow, YEAR,
                              v(r, "primaryValue") or "", v(r, "fobvalue") or "",
                              v(r, "cifvalue") or "", SRC])
    write("tm_flow.csv",
          ["reporter_code", "reporter_iso", "reporter", "partner_code", "partner_iso",
           "partner", "flow", "year", "primary_value_usd", "fob_value_usd",
           "cif_value_usd", "source"], frows)

    # ---- the pairs: the same trade, counted twice ---------------------------
    prows, gaps, fobgaps = [], [], []
    for a in got:
        for b in got:
            if a == b:
                continue
            xr, mr = X[a].get(b), M[b].get(a)
            if not xr or not mr:
                continue
            xv = v(xr, "primaryValue")
            mv = v(mr, "primaryValue")
            mfob = v(mr, "fobvalue")
            if not xv or not mv:
                continue
            # Round first, then derive. Storing a percentage computed from full
            # precision beside dollar values rounded to the nearest dollar makes
            # the published row unable to reproduce its own published figure --
            # which a check caught on three small pairs.
            xr_, mr_ = round(xv), round(mv)
            mf_ = round(mfob) if mfob else None
            gap = mr_ - xr_
            pct = round(100.0 * gap / xr_, 2)
            gaps.append(abs(pct))
            fg = fpct = ""
            if mf_:
                fg = mf_ - xr_
                fpct = round(100.0 * fg / xr_, 2)
                fobgaps.append(abs(fpct))
            prows.append([iso.get(a, ""), name.get(a, ""), iso.get(b, ""),
                          name.get(b, ""), YEAR, xr_, mr_,
                          (mf_ if mf_ else ""), gap, pct,
                          (fg if fg != "" else ""),
                          (fpct if fpct != "" else ""), SRC])
    write("tm_pair.csv",
          ["exporter_iso", "exporter", "importer_iso", "importer", "year",
           "exporter_reported_usd", "importer_reported_cif_usd",
           "importer_reported_fob_usd", "gap_cif_usd", "gap_cif_pct",
           "gap_fob_usd", "gap_fob_pct", "source"], prows)

    # ---- per reporter --------------------------------------------------------
    rrows = []
    for c in got:
        mine = [p for p in prows if p[0] == iso.get(c, "") or p[2] == iso.get(c, "")]
        asx = [p for p in prows if p[0] == iso.get(c, "")]
        rrows.append([iso.get(c, ""), name.get(c, ""), YEAR,
                      (totals.get(c) or {}).get("X") or "",
                      (totals.get(c) or {}).get("M") or "",
                      len(X[c]), len(M[c]), len(asx),
                      (round(statistics.median([abs(p[9]) for p in asx]), 2)
                       if asx else ""),
                      (round(statistics.median(
                          [abs(p[11]) for p in asx if p[11] != ""]), 2)
                       if [p for p in asx if p[11] != ""] else ""),
                      SRC])
    write("tm_reporter.csv",
          ["iso3", "reporter", "year", "total_exports_usd", "total_imports_usd",
           "export_partners", "import_partners", "pairs_as_exporter",
           "median_abs_gap_cif_pct", "median_abs_gap_fob_pct", "source"], rrows)

    # ---- the world does not balance with itself ----------------------------
    wx = sum((totals.get(c) or {}).get("X") or 0 for c in got)
    wm = sum((totals.get(c) or {}).get("M") or 0 for c in got)
    pair_x = sum(p[5] for p in prows)
    pair_m = sum(p[6] for p in prows)
    pair_mf = sum(p[7] for p in prows if p[7] != "")
    pair_xf = sum(p[5] for p in prows if p[7] != "")

    cov = [
     ["year", YEAR, "year", SRC],
     ["reporters read", len(got), "count", SRC],
     ["matched pairs", len(prows), "count", SRC],
     ["flow rows", len(frows), "count", SRC],
     ["reported exports, these reporters", round(wx), "usd", SRC],
     ["reported imports, these reporters", round(wm), "usd", SRC],
     ["import minus export, these reporters", round(wm - wx), "usd", SRC],
     ["import minus export, these reporters",
      round(100.0 * (wm - wx) / wx, 2), "percent", SRC],
     ["matched pairs, exporter side", round(pair_x), "usd", SRC],
     ["matched pairs, importer side CIF", round(pair_m), "usd", SRC],
     ["matched pairs, gap CIF", round(pair_m - pair_x), "usd", SRC],
     ["matched pairs, gap CIF", round(100.0 * (pair_m - pair_x) / pair_x, 2),
      "percent", SRC],
     ["pairs with an importer FOB value", len([p for p in prows if p[7] != ""]),
      "count", SRC],
     ["matched pairs, gap FOB",
      (round(100.0 * (pair_mf - pair_xf) / pair_xf, 2) if pair_xf else ""),
      "percent", SRC],
     ["median absolute gap, CIF", round(statistics.median(gaps), 2), "percent", SRC],
     ["median absolute gap, FOB",
      (round(statistics.median(fobgaps), 2) if fobgaps else ""), "percent", SRC],
     ["pairs disagreeing by more than a tenth",
      sum(1 for g in gaps if g > 10), "count", SRC],
     ["pairs disagreeing by more than a half",
      sum(1 for g in gaps if g > 50), "count", SRC],
     ["valuation note", 1, "flag",
      "exports are FOB and imports CIF, so a positive gap is expected; the FOB "
      "columns are the comparison that removes it"],
    ]
    write("tm_coverage.csv", ["property", "value", "unit", "source"], cov)

    print("\n%d matched pairs. Median absolute disagreement %.2f%% on the published "
          "values and %.2f%% after both sides are put on the same valuation."
          % (len(prows), statistics.median(gaps),
             statistics.median(fobgaps) if fobgaps else 0))
    print("These %d reporters together report %.4g dollars of exports and %.4g of "
          "imports: a %+.2f%% difference on trade that is the same trade."
          % (len(got), wx, wm, 100.0 * (wm - wx) / wx))


if __name__ == "__main__":
    main()
