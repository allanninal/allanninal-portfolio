"""Does OpenAlex's "diamond" label mean the journal charges nothing? Often not.

OpenAlex classifies every work into one of six open-access states:

  diamond   fully-OA journal that charges no author fee
  gold      fully-OA journal, usually paid for by the author
  hybrid    a free article inside a subscription journal; the most expensive kind
  bronze    free on the publisher's site with NO licence -- revocable, unreusable
  green     the version of record is still paywalled; a manuscript sits in a repo
  closed    paywalled

diamond is the second-largest of the six and the fastest-growing, and it is the
one people cite when they say open access does not have to cost authors money.

DOAJ asks journals directly whether they charge an author fee and records the
answer with a price and a currency. Comparing the two sources journal by journal
shows the label does not mean what it says: a large share of journals that DOAJ
records as fee-charging are labelled diamond by OpenAlex, because OpenAlex has no
apc_usd value for them and the classification falls through.

The error is not evenly spread. It is roughly four times more likely when the fee
is priced in something other than a hard currency, which means the country map of
diamond open access is partly a map of which currencies have been converted.

This script measures that rate rather than assuming it, on a two-way sample: DOAJ
journals that say they charge, and DOAJ journals that say they do not.

Three free sources, no keys:
  https://api.openalex.org/    OpenAlex, a works and sources index
  https://doaj.org/api/        DOAJ, a journal registry with a direct fee answer
  https://api.worldbank.org/   income group and GNI per capita
"""
import collections
import csv
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")            # not committed; see .gitignore note
OUT = os.path.dirname(HERE)
MAIL = "landix.ninal@gmail.com"
UA = {"User-Agent": "allanninal.dev research (mailto:%s)" % MAIL}

OA_SRC = "OpenAlex, api.openalex.org"
DOAJ_SRC = "DOAJ, doaj.org/api"
WB_SRC = "World Bank WDI, api.worldbank.org"

YEAR = 2023                      # the most recent year with a settled record
YEARS = list(range(2014, 2025))
STATUSES = ["diamond", "gold", "hybrid", "bronze", "green", "closed"]
BUCKETS = [(0, 500), (500, 1000), (1000, 2000), (2000, 3000),
           (3000, 5000), (5000, 100000)]
TOP_N = 60                       # countries, by works in YEAR
# Sized to the daily allowance. Each journal costs two metered calls (resolve the
# source, then group its works by oa_status), and the country and year series
# above cost about 150 more on a cold cache. 450 journals is 900 calls, which
# fits inside BUDGET with room for retries.
AUDIT_CHARGING = 300             # DOAJ journals that say they DO charge a fee
AUDIT_FREE = 150                 # DOAJ journals that say they do NOT -- the control
PAUSE = 0.28                     # OpenAlex's polite pool allows 10/s; stay well under

# Currencies OpenAlex reliably carries a converted apc_usd for. The split is the
# finding: the label is far more often wrong when the fee is priced outside this
# set, which is what makes the country pattern partly an artefact of conversion.
HARD = {"USD", "EUR", "GBP", "CHF", "AUD", "CAD", "JPY", "SEK", "NOK", "DKK",
        "NZD", "SGD"}

# The audit MEASURES disagreement rather than asserting a tolerance for it, so
# there is no threshold here to tune. What still aborts the run is a source that
# has changed shape underneath the analysis: see the guards in main().
MIN_AUDIT = 150                  # too small a sample is a failed run, not a result

# OpenAlex is metered. The anonymous tier is 1000 requests a day -- the response
# carries x-ratelimit-limit: 1000 and x-ratelimit-remaining -- and when it runs
# out the 429 arrives with a Retry-After of about twenty HOURS, not seconds.
# Two consequences, both handled below:
#   * every response is cached on disk, so a resumed run re-spends nothing;
#   * a Retry-After longer than RETRY_CAP aborts with the reset time rather than
#     sleeping through most of a day.
# --offline spends nothing and runs entirely from the cache, stopping the audit
# at whatever was already paid for. Useful when the allowance is gone but enough
# journals are cached to exceed MIN_AUDIT.
BUDGET = 0 if "--offline" in sys.argv else 950
RETRY_CAP = 600                  # seconds; anything longer is a quota, not a queue
SPENT = [0]


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch(url, tries=5, metered=False):
    """GET with an on-disk cache and honest 429 handling.

    The cache is what makes a metered source workable: a run that dies halfway
    resumes without paying for anything it already has. `metered` marks the
    requests that draw on the OpenAlex allowance, so the budget guard only counts
    those and DOAJ or the World Bank cost nothing.
    """
    cp = _cache_path(url)
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as fh:
            return json.load(fh)
    if metered:
        if SPENT[0] >= BUDGET:
            raise SystemExit(
                "\nBUDGET EXHAUSTED: %d metered requests this run, limit %d.\n"
                "OpenAlex allows about 1000 a day anonymously. Everything fetched so "
                "far is cached under %s, so re-running tomorrow resumes from here "
                "without re-spending.\n" % (SPENT[0], BUDGET, CACHE))
        SPENT[0] += 1
    for n in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=120) as r:
                d = json.loads(r.read().decode("utf-8"))
            os.makedirs(CACHE, exist_ok=True)
            with open(cp, "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            return d
        except urllib.error.HTTPError as e:
            wait = float(e.headers.get("Retry-After") or 0)
            if e.code == 429 and wait > RETRY_CAP:
                rem = e.headers.get("x-ratelimit-remaining")
                raise SystemExit(
                    "\nRATE LIMIT: OpenAlex says retry in %.0f seconds (%.1f hours), "
                    "remaining credits %s.\nThat is the daily allowance, not a queue. "
                    "Everything fetched so far is cached under %s; re-run after the "
                    "reset and it will resume.\n"
                    % (wait, wait / 3600.0, rem, CACHE))
            if e.code != 429 or n == tries - 1:
                raise
            w = wait or min(60, 8 * (n + 1))
            sys.stderr.write("  429, waiting %.0fs (%d/%d)\n" % (w, n + 1, tries))
            time.sleep(w)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as e:
            if n == tries - 1:
                raise
            sys.stderr.write("  retry %d/%d -- %s\n" % (n + 1, tries, e))
            time.sleep(3 * (n + 1))


def oa(path, **kw):
    kw.setdefault("mailto", MAIL)
    url = "https://api.openalex.org/" + path + "?" + urllib.parse.urlencode(kw)
    if not os.path.exists(_cache_path(url)):
        time.sleep(PAUSE)
    return fetch(url, metered=True)


def count(**kw):
    return oa("works", per_page=1, **kw)["meta"]["count"]


def group(field, **kw):
    g = oa("works", group_by=field, per_page=200, **kw)["group_by"]
    return {x["key"]: x["count"] for x in g}


def doaj(q, **kw):
    kw.setdefault("pageSize", 1)
    time.sleep(PAUSE)
    return fetch("https://doaj.org/api/search/journals/"
                 + urllib.parse.quote(q, safe="") + "?" + urllib.parse.urlencode(kw))


def wb(path, **kw):
    time.sleep(PAUSE)
    return fetch("https://api.worldbank.org/v2/" + path + "?format=json&per_page=20000&"
                 + urllib.parse.urlencode(kw))


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("  %-24s %6d row(s)" % (name, len(rows)))


def main():
    # ---- the world, by year ------------------------------------------------
    yrows, ytot = [], {}
    for y in YEARS:
        g = group("open_access.oa_status", filter="publication_year:%d" % y)
        tot = sum(g.values())
        ytot[y] = tot
        for st in STATUSES:
            n = g.get(st, 0)
            yrows.append([y, st, n, round(100.0 * n / tot, 2) if tot else "", OA_SRC])
        print("  %d  %s works" % (y, format(tot, ",")))
    write("oa_year.csv", ["year", "oa_status", "works", "pct_of_year", "source"], yrows)

    # ---- the point of the page: which categories actually cost money -------
    srows = []
    for st in STATUSES:
        n = count(filter="publication_year:%d,open_access.oa_status:%s" % (YEAR, st))
        p = count(filter="publication_year:%d,open_access.oa_status:%s,apc_paid.value:>0"
                         % (YEAR, st))
        srows.append([YEAR, st, n, p, round(100.0 * p / n, 2) if n else "", OA_SRC])
        print("  %-8s %-10s paid APC %-9s %5.2f%%"
              % (st, format(n, ","), format(p, ","), 100.0 * p / n if n else 0))
    write("oa_status_apc.csv",
          ["year", "oa_status", "works", "works_with_paid_apc", "pct_with_paid_apc",
           "source"], srows)

    # ---- what an article processing charge actually costs -------------------
    brows = []
    for lo, hi in BUCKETS:
        n = count(filter="publication_year:%d,apc_paid.value:>%d,apc_paid.value:<%d"
                         % (YEAR, lo, hi))
        brows.append(["WORLD", YEAR, lo, hi, n, OA_SRC])
    write("oa_apc_bucket.csv",
          ["scope", "year", "usd_from", "usd_to", "works", "source"], brows)

    # ---- countries ----------------------------------------------------------
    top = oa("works", group_by="authorships.countries", per_page=200,
             filter="publication_year:%d" % YEAR)["group_by"]
    codes = []
    for g in top:
        cc = g["key"].rstrip("/").rsplit("/", 1)[-1].upper()
        if len(cc) == 2:
            codes.append((cc, g["key_display_name"], g["count"]))
        if len(codes) >= TOP_N:
            break
    print("  %d countries, largest %s (%s works)"
          % (len(codes), codes[0][1], format(codes[0][2], ",")))

    meta = {}
    for c in wb("country")[1]:
        meta[c["iso2Code"]] = {"income": c["incomeLevel"]["value"],
                               "region": c["region"]["value"],
                               "iso3": c["id"]}
    gni = {}
    for r in wb("country/all/indicator/NY.GNP.PCAP.CD", date="2022:2024")[1]:
        if r["value"] is not None:
            gni.setdefault(r["countryiso3code"], {})[int(r["date"])] = r["value"]

    crows = []
    for cc, name, tot in codes:
        f = "publication_year:%d,authorships.countries:%s" % (YEAR, cc)
        g = group("open_access.oa_status", filter=f)
        paid = count(filter=f + ",apc_paid.value:>0")
        m = meta.get(cc, {})
        iso3 = m.get("iso3", "")
        gv = gni.get(iso3, {})
        crows.append([cc, iso3, name, m.get("region", ""), m.get("income", ""),
                      (max(gv.items())[1] if gv else ""), YEAR, tot]
                     + [g.get(st, 0) for st in STATUSES]
                     + [round(100.0 * g.get(st, 0) / tot, 2) if tot else ""
                        for st in STATUSES]
                     + [paid, round(100.0 * paid / tot, 2) if tot else "", OA_SRC])
        print("  %-3s %-28s %8s works  diamond %5.2f%%"
              % (cc, name[:28], format(tot, ","),
                 100.0 * g.get("diamond", 0) / tot if tot else 0))
    write("oa_country.csv",
          ["iso2", "iso3", "country", "region", "income_group", "gni_per_capita_usd",
           "year", "works"] + ["%s_works" % s for s in STATUSES]
          + ["%s_pct" % s for s in STATUSES]
          + ["apc_paid_works", "apc_paid_pct", "source"], crows)

    # ---- DOAJ: a direct answer to the question the label claims to answer ---
    dj_total = doaj("*")["total"]
    dj_apc = doaj("bibjson.apc.has_apc:true")["total"]
    dj_free = doaj("bibjson.apc.has_apc:false")["total"]
    print("  DOAJ %s journals: %s charge an author fee, %s charge nothing"
          % (format(dj_total, ","), format(dj_apc, ","), format(dj_free, ",")))
    if dj_apc + dj_free != dj_total:
        sys.stderr.write("DOAJ: has_apc true+false (%d) != total (%d); the field has "
                         "gained a third state and the audit below is no longer a "
                         "two-way comparison\n" % (dj_apc + dj_free, dj_total))
        raise SystemExit(1)

    # ---- the audit ----------------------------------------------------------
    def harvest(query, want):
        """DOAJ journals matching a query, with an ISSN and a stated fee position."""
        out, page = [], 1
        while len(out) < want:
            d = doaj(query, pageSize=100, page=page)
            if not d.get("results"):
                break
            for j in d["results"]:
                b = j["bibjson"]
                issn = b.get("eissn") or b.get("pissn")
                apcb = b.get("apc") or {}
                mx = apcb.get("max") or []
                out.append({
                    "issn": issn,
                    "title": (b.get("title") or "")[:70].replace(",", " "),
                    "charges": bool(apcb.get("has_apc")),
                    "currency": (mx[0].get("currency") if mx else "") or "",
                    "price": (mx[0].get("price") if mx else "") or "",
                    "country": (b.get("publisher") or {}).get("country", ""),
                })
            page += 1
        return [x for x in out if x["issn"]][:want]

    arows, cells = [], collections.Counter()
    by_cur = collections.defaultdict(lambda: [0, 0])
    absent = 0
    # A run that reaches the allowance mid-audit should use the sample it has
    # rather than throw it away. Two metered calls are needed per journal, so the
    # loop stops while there is still room for one more pair; MIN_AUDIT below
    # then decides whether what was collected is enough to report.
    budget_limited = False
    for want, q in ((AUDIT_CHARGING, "bibjson.apc.has_apc:true"),
                    (AUDIT_FREE, "bibjson.apc.has_apc:false")):
        for j in harvest(q, want):
            if SPENT[0] > BUDGET - 3 and not os.path.exists(_cache_path(
                    "https://api.openalex.org/sources?"
                    + urllib.parse.urlencode(
                        {"filter": "issn:%s" % j["issn"], "per_page": 1,
                         "mailto": MAIL}))):
                budget_limited = True
                break
            src = (oa("sources", filter="issn:%s" % j["issn"], per_page=1)
                   .get("results") or [])
            if not src:
                absent += 1
                continue
            sid = src[0]["id"].rsplit("/", 1)[-1]
            apc_usd = src[0].get("apc_usd")
            g = group("open_access.oa_status",
                      filter="primary_location.source.id:%s,publication_year:%d"
                             % (sid, YEAR))
            n = sum(g.values())
            if not n:
                continue
            dia = g.get("diamond", 0) / n
            labelled = dia > 0.5
            hard = j["currency"] in HARD
            cells[(j["charges"], labelled)] += 1
            if j["charges"]:
                k = "hard" if hard else "other"
                by_cur[k][0] += 1
                by_cur[k][1] += labelled
            arows.append([j["issn"], j["title"], j["country"],
                          "yes" if j["charges"] else "no", j["currency"], j["price"],
                          "yes" if hard else "no",
                          ("" if apc_usd is None else apc_usd), n,
                          round(100.0 * dia, 2), "yes" if labelled else "no",
                          "wrong" if (j["charges"] and labelled) else "consistent",
                          "DOAJ has_apc vs OpenAlex oa_status"])

    audited = sum(cells.values())
    if budget_limited:
        print("  NOTE: the daily allowance was reached; the audit below is the "
              "sample collected before it, not the full %d journals."
              % (AUDIT_CHARGING + AUDIT_FREE))
    if audited < MIN_AUDIT:
        sys.stderr.write("AUDIT TOO SMALL: %d journals resolved, need %d. Either DOAJ "
                         "paging or the OpenAlex source lookup is failing, and a rate "
                         "computed on this is not a result.\n" % (audited, MIN_AUDIT))
        raise SystemExit(1)

    charging = cells[(True, True)] + cells[(True, False)]
    free_j = cells[(False, True)] + cells[(False, False)]
    wrong = cells[(True, True)]
    wrong_pct = round(100.0 * wrong / charging, 2) if charging else 0
    hard_n, hard_w = by_cur["hard"]
    oth_n, oth_w = by_cur["other"]
    hard_pct = round(100.0 * hard_w / hard_n, 2) if hard_n else 0
    oth_pct = round(100.0 * oth_w / oth_n, 2) if oth_n else 0

    write("oa_label_audit.csv",
          ["issn", "journal", "publisher_country", "doaj_charges_fee", "currency",
           "price", "hard_currency", "openalex_apc_usd", "works_in_year",
           "diamond_pct_of_works", "openalex_labels_diamond", "verdict", "source"],
          arows)

    print("  audit: %d journals resolved (%d fee-charging, %d fee-free), "
          "%d absent from OpenAlex" % (audited, charging, free_j, absent))
    print("  fee-charging journals labelled diamond: %d of %d (%.2f%%)"
          % (wrong, charging, wrong_pct))
    print("    priced in a hard currency: %d of %d (%.2f%%)" % (hard_w, hard_n, hard_pct))
    print("    priced in anything else:   %d of %d (%.2f%%)" % (oth_w, oth_n, oth_pct))

    # ---- coverage -----------------------------------------------------------
    wy = {st: sum(r[2] for r in yrows if r[0] == YEAR and r[1] == st) for st in STATUSES}
    free = sum(wy[s] for s in ("diamond", "gold", "hybrid", "bronze", "green"))
    cov = [
     ["works in the year analysed", ytot[YEAR], "works", OA_SRC],
     ["year analysed", YEAR, "year", OA_SRC],
     ["first year", YEARS[0], "year", OA_SRC],
     ["last year", YEARS[-1], "year", OA_SRC],
     ["countries", len(crows), "count", OA_SRC],
     ["open access, any kind", free, "works", OA_SRC],
     ["open access, any kind", round(100.0 * free / ytot[YEAR], 2), "percent", OA_SRC],
     ["free to read and free to publish (diamond)", wy["diamond"], "works", OA_SRC],
     ["author-pays kinds (gold and hybrid)", wy["gold"] + wy["hybrid"], "works", OA_SRC],
     ["revocable kind (bronze)", wy["bronze"], "works", OA_SRC],
     ["DOAJ journals", dj_total, "journals", DOAJ_SRC],
     ["DOAJ journals charging no author fee", dj_free, "journals", DOAJ_SRC],
     ["DOAJ journals charging no author fee",
      round(100.0 * dj_free / dj_total, 2), "percent", DOAJ_SRC],
     ["journals audited against DOAJ", audited, "count",
      "DOAJ has_apc vs OpenAlex oa_status"],
     ["fee-charging journals audited", charging, "count", DOAJ_SRC],
     ["fee-free journals audited", free_j, "count", DOAJ_SRC],
     ["fee-charging journals labelled diamond", wrong, "count",
      "DOAJ has_apc vs OpenAlex oa_status"],
     ["fee-charging journals labelled diamond", wrong_pct, "percent",
      "DOAJ has_apc vs OpenAlex oa_status"],
     ["mislabel rate, fee in a hard currency", hard_pct, "percent",
      "DOAJ has_apc vs OpenAlex oa_status"],
     ["mislabel rate, fee in another currency", oth_pct, "percent",
      "DOAJ has_apc vs OpenAlex oa_status"],
     ["hard-currency journals audited", hard_n, "count", DOAJ_SRC],
     ["other-currency journals audited", oth_n, "count", DOAJ_SRC],
     ["sampled journals absent from OpenAlex", absent, "count", OA_SRC],
     ["audit stopped by the daily allowance", 1 if budget_limited else 0, "flag",
      "OpenAlex allows about 1000 requests a day anonymously"],
     ["a work is counted once per author country", 1, "flag",
      "multi-country papers appear in each country's total"],
    ]
    write("oa_coverage.csv", ["property", "value", "unit", "source"], cov)

    dia = sorted(crows, key=lambda r: -r[14])[0]
    print("\n%s of %s works in %d are labelled diamond -- supposedly free to publish."
          % (format(wy["diamond"], ","), format(ytot[YEAR], ","), YEAR))
    print("%.2f%% of the journals DOAJ records as fee-charging carry that label anyway: "
          "%.2f%% when the fee is in a hard currency, %.2f%% when it is not."
          % (wrong_pct, hard_pct, oth_pct))
    print("Highest national diamond share: %s at %.2f%%." % (dia[2], dia[14]))


if __name__ == "__main__":
    try:
        main()
    finally:
        print("\nmetered OpenAlex requests this run: %d of %d" % (SPENT[0], BUDGET))
