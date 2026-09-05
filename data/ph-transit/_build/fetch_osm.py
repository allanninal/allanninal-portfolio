#!/usr/bin/env python3
"""Metro Manila public transport, from OpenStreetMap via Overpass.

    .venv/bin/python data/ph-transit/_build/fetch_osm.py

The single most important thing about this dataset, stated here and on the page:
OpenStreetMap is a volunteer map, and its Philippine public-transport coverage is
partial. It holds 26 jeepney (share_taxi) route relations for a metro that runs
them in the thousands. Every count below is therefore a FLOOR -- what has been
mapped, not what exists -- and no figure here should be read as a count of the
transport system itself.

That is worth publishing rather than hiding, because the gap is the finding: the
rail network is essentially completely mapped (49 stations, and the line lengths
match published figures), while the road-based network that actually moves most
people is barely mapped at all. Formal, legible infrastructure gets recorded;
informal infrastructure does not.

Two mechanical notes:

* Overpass rejects an unbounded area query for "Metro Manila" -- the admin
  relation does not resolve by that name -- so the metro extent is a bounding
  box, carried on every row. The per-city queries name each of the 17 NCR
  local government units explicitly, because a bounding box over the metro also
  catches Bacoor, Antipolo and half of Bulacan.
* Queries are cached to _build/.cache so re-running does not hammer a free
  community endpoint. Delete that directory to force a refetch.
"""
import csv
import hashlib
import http.client
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

OUT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(os.path.dirname(__file__), ".cache")
API = "https://overpass-api.de/api/interpreter"
UA = "allanninal.dev research (contact via github.com/allanninal)"
SRC = "OpenStreetMap via Overpass API"
BOX = "14.35,120.90,14.80,121.15"
BOX_LABEL = "14.35-14.80N,120.90-121.15E"
NCR = ["Caloocan", "Las Piñas", "Makati", "Malabon", "Mandaluyong", "Manila",
       "Marikina", "Muntinlupa", "Navotas", "Parañaque", "Pasay", "Pasig",
       "Pateros", "Quezon City", "San Juan", "Taguig", "Valenzuela"]
ROUTE_TYPES = "bus|share_taxi|light_rail|subway|train|monorail|ferry"


def overpass(query):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha256(query.encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    data = urllib.parse.urlencode({"data": query}).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(API, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=240,
                                        context=ssl.create_default_context()) as r:
                d = json.loads(r.read())
            json.dump(d, open(path, "w"))
            return d
        # Overpass is a free community endpoint under real load. It answers with
        # 429, 504, and bare connection drops -- RemoteDisconnected is not a
        # URLError, so an earlier version died on it mid-run after 13 of 17
        # cities. Catch broadly and back off hard; the cache means a re-run
        # resumes rather than repeating the work.
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                http.client.HTTPException, ConnectionError, OSError) as e:
            if attempt == 5:
                raise SystemExit("Overpass failed after 6 attempts: %s" % e)
            print("    retry %d (%s)" % (attempt + 1, e), file=sys.stderr)
            time.sleep(20 * (attempt + 1))


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    # ---- routes
    d = overpass("[out:json][timeout:180];"
                 '(relation["type"="route"]["route"~"^(%s)$"](%s););out tags;'
                 % (ROUTE_TYPES, BOX))
    routes = d.get("elements", [])
    if not routes:
        raise SystemExit("no route relations returned -- Overpass changed or the "
                         "box is wrong; refusing to write empty CSVs")
    print("  %d route relations" % len(routes))
    by_type = Counter(r["tags"].get("route") for r in routes)
    write("ph_transit_routes.csv",
          ["route_type", "routes", "named_routes", "with_operator", "box", "source"],
          [[t, n,
            sum(1 for r in routes if r["tags"].get("route") == t and r["tags"].get("name")),
            sum(1 for r in routes if r["tags"].get("route") == t and r["tags"].get("operator")),
            BOX_LABEL, SRC] for t, n in by_type.most_common()])

    # ---- rail lines named individually: the part of the network OSM has
    #      essentially complete, and the contrast the page is built on.
    rail = [r for r in routes
            if r["tags"].get("route") in ("light_rail", "subway", "train", "monorail")]
    write("ph_transit_rail_routes.csv",
          ["name", "route_type", "operator", "network", "box", "source"],
          sorted([[r["tags"].get("name", ""), r["tags"].get("route"),
                   r["tags"].get("operator", ""), r["tags"].get("network", ""),
                   BOX_LABEL, SRC] for r in rail]))

    # ---- stops
    d = overpass("[out:json][timeout:240];("
                 'node["railway"="station"](%s);'
                 'node["railway"="halt"](%s);'
                 'node["highway"="bus_stop"](%s);'
                 'node["public_transport"="platform"](%s);'
                 'node["amenity"="bus_station"](%s););out tags;'
                 % (BOX, BOX, BOX, BOX, BOX))
    stops = d.get("elements", [])
    if not stops:
        raise SystemExit("no stop nodes returned -- refusing to write empty CSVs")
    print("  %d stop nodes" % len(stops))

    def kind(e):
        t = e.get("tags", {})
        if t.get("railway") in ("station", "halt"):
            return "rail station"
        if t.get("amenity") == "bus_station":
            return "bus terminal"
        if t.get("highway") == "bus_stop":
            return "bus stop"
        return "platform"

    ks = Counter(kind(e) for e in stops)
    write("ph_transit_stops.csv",
          ["stop_type", "count", "named", "pct_named", "box", "source"],
          [[k, n,
            sum(1 for e in stops if kind(e) == k and e.get("tags", {}).get("name")),
            round(100.0 * sum(1 for e in stops if kind(e) == k
                              and e.get("tags", {}).get("name")) / n, 1),
            BOX_LABEL, SRC] for k, n in ks.most_common()])

    # ---- per city, resolved by OSM relation id rather than by name.
    #
    #      area["name"="San Juan"] matches SIX admin_level=6 boundaries
    #      worldwide -- San Juan in Metro Manila, one in Negros Oriental, one
    #      in Batangas, and San Juan in Puerto Rico, Honduras and El Salvador.
    #      Overpass unions them all and returns one total, so the first run
    #      credited Metro Manila's smallest city with 948 bus stops, more
    #      than Manila. Puerto Rico has a real bus network.
    #
    #      So the boundaries are fetched once inside the metro bounding box,
    #      matched by name there, and each city is then queried by its own
    #      area id. A name that resolves to zero or more than one relation
    #      inside the box is an error rather than a silent sum.
    d = overpass('[out:json][timeout:180];'
                 'rel["boundary"="administrative"]["admin_level"="6"](%s);'
                 'out tags;' % BOX)
    found = {}
    for e in d.get("elements", []):
        nm = e.get("tags", {}).get("name")
        if nm in NCR:
            found.setdefault(nm, []).append(e["id"])
    missing = [c for c in NCR if c not in found]
    ambiguous = {c: v for c, v in found.items() if len(v) > 1}
    if missing:
        raise SystemExit("no boundary inside the box for: %s" % ", ".join(missing))
    if ambiguous:
        raise SystemExit("more than one boundary inside the box for: %s"
                         % ", ".join(ambiguous))

    rows = []
    for city in NCR:
        area = 3600000000 + found[city][0]
        q = ('[out:json][timeout:120];'
             '(node["highway"="bus_stop"](area:%d);'
             'node["public_transport"="platform"](area:%d);'
             'node["amenity"="bus_station"](area:%d););out count;'
             % (area, area, area))
        d = overpass(q)
        stopn = int(d["elements"][0]["tags"]["total"]) if d.get("elements") else 0
        q = ('[out:json][timeout:120];'
             '(node["railway"="station"](area:%d);'
             'node["railway"="halt"](area:%d););out count;' % (area, area))
        d = overpass(q)
        railn = int(d["elements"][0]["tags"]["total"]) if d.get("elements") else 0
        rows.append([city, found[city][0], stopn, railn, SRC])
        print("    %-14s rel=%-9d %5d road stops  %3d rail stations"
              % (city, found[city][0], stopn, railn))
        time.sleep(3)
    if sum(r[2] for r in rows) == 0:
        raise SystemExit("every city returned zero stops")
    write("ph_transit_by_city.csv",
          ["city", "osm_relation_id", "road_stops", "rail_stations", "source"], rows)
    # ---- coverage note, as data rather than prose
    write("ph_transit_coverage.csv",
          ["metric", "value", "note", "source"],
          [["route_relations", len(routes), "all mapped transport routes in the box", SRC],
           ["share_taxi_routes", by_type.get("share_taxi", 0),
            "jeepney routes mapped in OSM; the real network runs to thousands, so "
            "this is a floor on mapping, not a count of the system", SRC],
           ["bus_routes", by_type.get("bus", 0), "", SRC],
           ["rail_routes", len(rail), "", SRC],
           ["rail_stations", ks.get("rail station", 0), "", SRC],
           ["road_stops", ks.get("bus stop", 0) + ks.get("platform", 0)
            + ks.get("bus terminal", 0), "", SRC],
           ["stop_nodes_total", len(stops), "", SRC]])


if __name__ == "__main__":
    main()
