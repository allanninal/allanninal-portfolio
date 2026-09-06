#!/usr/bin/env python3
"""An internet exchange with one member is not an internet exchange.

PeeringDB is the registry the internet's operators keep about themselves: every
internet exchange point, every colocation facility, and how many networks are
present at each. It is the closest thing there is to a public map of where
networks actually meet.

Counting buildings is the wrong measure and it is the one that gets quoted. A
country can host a hundred data centres and still have almost nowhere that two
networks exchange traffic. So this reads the network count -- how many networks
are actually present -- rather than the number of facilities.

The finding is at the bottom of the distribution rather than the top. A large
number of the world's internet exchanges have no networks on them at all, and
more have exactly one. An exchange with one member is a room with a switch in it.

PeeringDB carries two independent counts of the same thing, which is unusual and
useful: net_count is what the exchange operator records, and ixf_net_count is
imported from the exchange's own published IX-F member list. Where both exist
they are compared, and a systematic disagreement aborts the run.

Everything is cached on disk, because PeeringDB rate-limits anonymous clients and
re-fetching five thousand rows to change one line of analysis is rude.

Free, no key:
  https://www.peeringdb.com/api/          exchanges and facilities
  https://www.submarinecablemap.com/      cable landing points (TeleGeography)
  https://api.worldbank.org/v2/           population, income group
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

PDB = "https://www.peeringdb.com/api/"
SCM = "https://www.submarinecablemap.com/api/v3/"
PDB_SRC = "PeeringDB, peeringdb.com/api"
SCM_SRC = "TeleGeography Submarine Cable Map, submarinecablemap.com"
WB_SRC = "World Bank WDI, api.worldbank.org"

# net_count is what the exchange operator types in. ixf_net_count is machine-read
# from the exchange's own member list. They measure the same quantity by different
# routes, so they should track; a large median gap means one of them has stopped
# being maintained and neither can then be used to say an exchange is empty.
GAP_TOLERANCE = 12

# Never sleep longer than this on a 429, whatever the server asks for.
RETRY_CAP = 600


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch(url, tries=6):
    cp = _cache_path(url)
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as fh:
            return json.load(fh)
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
            if e.code != 429 or n == tries - 1:
                raise
            # Cap what the server asks for. A Retry-After is a hint, and a large
            # one is a daily quota rather than a queue -- sleeping through it
            # burns the run for no gain. OpenAlex sends 72000 here; assume any
            # host can.
            asked = float(e.headers.get("Retry-After") or 0)
            if asked > RETRY_CAP:
                raise SystemExit(
                    "\nRATE LIMIT: %s asks for a %.0f second wait (%.1f hours).\n"
                    "That is an allowance, not a queue. Anything already fetched is "
                    "cached under %s and a later run resumes from there.\n"
                    % (urllib.parse.urlsplit(url).netloc, asked, asked / 3600.0, CACHE))
            wait = asked or min(120, 20 * (n + 1))
            sys.stderr.write("  429, waiting %.0fs (%d/%d)\n" % (wait, n + 1, tries))
            time.sleep(wait)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, ValueError) as e:
            if n == tries - 1:
                raise
            sys.stderr.write("  retry %d/%d -- %s\n" % (n + 1, tries, e))
            time.sleep(5 * (n + 1))


def wb(path, **kw):
    return fetch("https://api.worldbank.org/v2/" + path + "?format=json&per_page=20000&"
                 + urllib.parse.urlencode(kw))


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("  %-24s %6d row(s)" % (name, len(rows)))


def i(x, k):
    v = x.get(k)
    return int(v) if isinstance(v, (int, float)) else 0


def main():
    ix = fetch(PDB + "ix?limit=0")["data"]
    fac = fetch(PDB + "fac?limit=0")["data"]
    print("PeeringDB: %d exchanges, %d facilities" % (len(ix), len(fac)))

    # ---- the two counts have to agree before either can be trusted ---------
    both = [(x, i(x, "net_count"), i(x, "ixf_net_count"))
            for x in ix if i(x, "ixf_net_count") > 0]
    gaps = sorted(abs(a - b) for _, a, b in both)
    med = statistics.median(gaps) if gaps else 0
    print("  %d exchanges publish an IX-F member list; median gap against the "
          "operator's own count: %d" % (len(both), med))
    if med > GAP_TOLERANCE:
        sys.stderr.write("\nCROSS-CHECK FAILED: the operator count and the imported "
                         "member list disagree by a median of %d networks, above the "
                         "%d tolerance. One of the two has stopped being maintained "
                         "and 'this exchange is empty' is no longer a claim this data "
                         "supports.\n" % (med, GAP_TOLERANCE))
        raise SystemExit(1)

    # An exchange the operator records as empty, whose own member list shows
    # members, is a registry gap rather than an empty exchange. Counted, and
    # excluded from the empty tally.
    ghost = [x for x in ix if i(x, "net_count") == 0 and i(x, "ixf_net_count") > 0]
    print("  recorded empty but publishing members: %d (excluded from the count)"
          % len(ghost))

    xrows = []
    for x in ix:
        nc, ic = i(x, "net_count"), i(x, "ixf_net_count")
        xrows.append([x["id"], (x.get("name") or "").replace(",", " "),
                      (x.get("city") or "").replace(",", " ").strip(),
                      x.get("country") or "", x.get("region_continent") or "",
                      nc, ic, i(x, "fac_count"),
                      "empty" if (nc == 0 and ic == 0) else
                      ("registry gap" if nc == 0 else
                       ("single member" if nc == 1 else "in use")),
                      PDB_SRC])
    write("gi_exchange.csv",
          ["ix_id", "name", "city", "country", "continent", "net_count",
           "ixf_net_count", "fac_count", "status", "source"], xrows)

    frows = []
    for f in fac:
        frows.append([f["id"], (f.get("name") or "").replace(",", " "),
                      (f.get("city") or "").replace(",", " ").strip(),
                      f.get("country") or "", f.get("region_continent") or "",
                      i(f, "net_count"), i(f, "ix_count"), i(f, "carrier_count"),
                      f.get("latitude") if f.get("latitude") is not None else "",
                      f.get("longitude") if f.get("longitude") is not None else "",
                      PDB_SRC])
    write("gi_facility.csv",
          ["fac_id", "name", "city", "country", "continent", "net_count",
           "ix_count", "carrier_count", "latitude", "longitude", "source"], frows)

    # ---- submarine cable landing points ------------------------------------
    lp = fetch(SCM + "landing-point/landing-point-geo.json")
    cab = fetch(SCM + "cable/cable-geo.json")
    lrows, lc = [], collections.Counter()
    for feat in lp.get("features", []):
        p = feat.get("properties", {})
        g = feat.get("geometry") or {}
        c = g.get("coordinates") or [None, None]
        name = (p.get("name") or "").replace(",", " ")
        lrows.append([p.get("id", ""), name, c[0], c[1], SCM_SRC])
    write("gi_landing_point.csv",
          ["landing_point_id", "name", "longitude", "latitude", "source"], lrows)
    print("  submarine: %d landing points, %d cables"
          % (len(lrows), len(cab.get("features", []))))

    # ---- per country --------------------------------------------------------
    meta, pop = {}, {}
    for c in wb("country")[1]:
        meta[c["iso2Code"]] = {"name": c["name"], "iso3": c["id"],
                               "region": c["region"]["value"],
                               "income": c["incomeLevel"]["value"],
                               "is_country": c["region"]["id"] != "NA"}
    for r in wb("country/all/indicator/SP.POP.TOTL", date="2022:2024")[1]:
        if r["value"] is not None:
            pop.setdefault(r["countryiso3code"], {})[int(r["date"])] = int(r["value"])

    ccs = sorted({x.get("country") for x in ix if x.get("country")}
                 | {f.get("country") for f in fac if f.get("country")})
    crows = []
    for cc in ccs:
        m = meta.get(cc, {})
        xs = [x for x in ix if x.get("country") == cc]
        fs = [f for f in fac if f.get("country") == cc]
        pv = pop.get(m.get("iso3", ""), {})
        crows.append([
            cc, m.get("iso3", ""), m.get("name", cc), m.get("region", ""),
            m.get("income", ""), (max(pv.items())[1] if pv else ""),
            len(xs),
            sum(1 for x in xs if i(x, "net_count") == 0 and i(x, "ixf_net_count") == 0),
            sum(1 for x in xs if i(x, "net_count") == 1),
            sum(i(x, "net_count") for x in xs),
            max([i(x, "net_count") for x in xs] or [0]),
            len(fs), sum(i(f, "net_count") for f in fs),
            PDB_SRC])
    write("gi_country.csv",
          ["iso2", "iso3", "country", "region", "income_group", "population",
           "exchanges", "empty_exchanges", "single_member_exchanges",
           "networks_at_exchanges", "largest_exchange_networks",
           "facilities", "network_presences_in_facilities", "source"], crows)

    # ---- per city -----------------------------------------------------------
    city = collections.defaultdict(lambda: [0, 0, 0])
    for f in fac:
        k = (f.get("country") or "", (f.get("city") or "").strip())
        city[k][0] += 1
        city[k][1] += i(f, "net_count")
    for x in ix:
        k = (x.get("country") or "", (x.get("city") or "").strip())
        city[k][2] += i(x, "net_count")
    crows2 = [[c, ct.replace(",", " "), v[0], v[1], v[2], PDB_SRC]
              for (c, ct), v in sorted(city.items(), key=lambda kv: -kv[1][1])
              if ct]
    write("gi_city.csv",
          ["country", "city", "facilities", "network_presences", "networks_at_exchanges",
           "source"], crows2)

    # ---- coverage -----------------------------------------------------------
    nc = [i(x, "net_count") for x in ix]
    empty = sum(1 for x in ix
                if i(x, "net_count") == 0 and i(x, "ixf_net_count") == 0)
    single = sum(1 for v in nc if v == 1)
    tot_pres = sum(i(f, "net_count") for f in fac)
    top20 = sum(sorted(nc, reverse=True)[:20])
    cov = [
     ["exchanges", len(ix), "count", PDB_SRC],
     ["facilities", len(fac), "count", PDB_SRC],
     ["network presences in facilities", tot_pres, "count", PDB_SRC],
     ["networks at exchanges", sum(nc), "count", PDB_SRC],
     ["empty exchanges", empty, "count", PDB_SRC],
     ["empty exchanges", round(100.0 * empty / len(ix), 2), "percent", PDB_SRC],
     ["single-member exchanges", single, "count", PDB_SRC],
     ["empty or single-member exchanges",
      round(100.0 * (empty + single) / len(ix), 2), "percent", PDB_SRC],
     ["registry gaps excluded from the empty count", len(ghost), "count", PDB_SRC],
     ["median networks per exchange", int(statistics.median(nc)), "count", PDB_SRC],
     ["largest exchange", max(nc), "networks", PDB_SRC],
     ["share of exchange presences at the twenty largest",
      round(100.0 * top20 / sum(nc), 2), "percent", PDB_SRC],
     ["countries or territories with at least one exchange",
      len({x.get("country") for x in ix if x.get("country")}), "count", PDB_SRC],
     ["exchanges publishing a member list", len(both), "count", PDB_SRC],
     ["median gap between the two counts", int(med), "networks",
      "operator net_count vs imported ixf_net_count"],
     ["submarine cable landing points", len(lrows), "count", SCM_SRC],
     ["submarine cables", len(cab.get("features", [])), "count", SCM_SRC],
     ["self-reported registry", 1, "flag",
      "PeeringDB is maintained by network operators about themselves; absence is "
      "not proof of absence"],
    ]
    write("gi_coverage.csv", ["property", "value", "unit", "source"], cov)

    print("\n%d of %d exchanges have no networks on them and %d have exactly one: "
          "%.2f%% of the world's internet exchanges are empty or have a single "
          "member." % (empty, len(ix), single,
                       100.0 * (empty + single) / len(ix)))


if __name__ == "__main__":
    main()
