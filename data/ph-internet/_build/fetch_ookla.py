#!/usr/bin/env python3
"""Philippine internet speeds from Ookla's open Speedtest tile data.

    .venv/bin/python data/ph-internet/_build/fetch_ookla.py

Ookla publishes quarterly parquet tiles of aggregated Speedtest results on S3,
openly and without a key. Each row is a ~600 m web-mercator tile with the mean
download, upload and latency of the tests taken inside it that quarter, plus
the test and device counts. DuckDB reads them over HTTP, so nothing is
downloaded whole: the tiles carry tile_x / tile_y centroids, and a numeric
bounding-box predicate on those is enough to pull the Philippines out of ~6.4
million global tiles in a few seconds per file.

Three things to hold on to when reading anything downstream:

* These are speeds of TESTS, not of connections. People run a speed test when
  they suspect something is wrong, or right after an upgrade. The sample is not
  the population, and the tile aggregates inherit that.

* The country figure here is a test-weighted mean of tile means. Ookla's own
  published headline is a median over tests. The two are not the same statistic
  and will not agree; this one is written as "test-weighted mean" everywhere and
  never as "the average speed in the Philippines".

* Coverage is where the tests are, which is where the people and the connections
  are. A tile count is a measure of testing density, so an area with few tiles is
  not necessarily slow -- it may simply be unmeasured. The per-tile counts are
  published so that limit is visible rather than implied.
"""
import csv
import os

try:
    import duckdb
except ImportError:
    raise SystemExit("needs duckdb:  make venv")

OUT = os.path.join(os.path.dirname(__file__), "..")
SRC = "Ookla Open Data, Speedtest performance tiles"
BOX = dict(lon=(116, 127), lat=(4, 21))
BOX_LABEL = "116-127E,4-21N"
BASE = ("https://ookla-open-data.s3.us-west-2.amazonaws.com/parquet/performance"
        "/type=%s/year=%d/quarter=%d/%d-%02d-01_performance_%s_tiles.parquet")
YEARS = range(2019, 2026)
QUARTER_MONTH = {1: 1, 2: 4, 3: 7, 4: 10}


def url(kind, year, q):
    return BASE % (kind, year, q, year, QUARTER_MONTH[q], kind)


def coords(con, u):
    """(lon_expr, lat_expr) for this file's schema.

    Ookla added tile_x / tile_y centroid columns partway through the archive.
    Files before that -- 2019 and 2021Q3 here -- carry only the WKT polygon, and
    a query naming tile_x fails on them with a binder error, which is how six
    quarters were first recorded as "unavailable" when the data was there all
    along. Where the centroids are missing, the first vertex of the polygon is
    parsed out of the WKT instead. A tile is about 600 m across, so a corner
    rather than a centre moves nothing at this scale.
    """
    cols = [r[0] for r in con.execute(
        "describe select * from read_parquet('%s')" % u).fetchall()]
    if "tile_x" in cols and "tile_y" in cols:
        return "tile_x", "tile_y"
    v = "split_part(replace(tile, 'POLYGON((', ''), ',', 1)"
    return ("try_cast(split_part(%s, ' ', 1) as double)" % v,
            "try_cast(split_part(%s, ' ', 2) as double)" % v)


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    con = duckdb.connect()
    con.execute("install httpfs; load httpfs;")
    quarterly, coverage = [], []
    for kind in ("fixed", "mobile"):
        for y in YEARS:
            for q in (1, 3):          # two snapshots a year is enough for a trend
                u = url(kind, y, q)
                try:
                    lon, lat = coords(con, u)
                    where = ("where %s between %d and %d and %s between %d and %d"
                             % (lon, BOX["lon"][0], BOX["lon"][1], lat,
                                BOX["lat"][0], BOX["lat"][1]))
                    r = con.execute("""
                        select count(*), sum(tests), sum(devices),
                               round(sum(avg_d_kbps * tests) / sum(tests) / 1000.0, 2),
                               round(sum(avg_u_kbps * tests) / sum(tests) / 1000.0, 2),
                               round(sum(avg_lat_ms  * tests) / sum(tests), 1)
                        from read_parquet('%s') %s""" % (u, where)).fetchone()
                except Exception as e:
                    coverage.append([kind, y, q, 0, "error:%s" % str(e)[:60],
                                     BOX_LABEL, SRC])
                    print("  %-6s %dQ%d  unavailable" % (kind, y, q))
                    continue
                if not r[0]:
                    coverage.append([kind, y, q, 0, "no tiles in box", BOX_LABEL, SRC])
                    continue
                quarterly.append([kind, y, q, r[0], r[1], r[2], r[3], r[4], r[5],
                                  BOX_LABEL, SRC])
                coverage.append([kind, y, q, r[0], "parsed", BOX_LABEL, SRC])
                print("  %-6s %dQ%d  %7d tiles  %8s Mbps down"
                      % (kind, y, q, r[0], r[3]))

    if not quarterly:
        raise SystemExit("no Ookla quarters fetched -- refusing to write empty CSVs")
    write("ph_internet_speeds.csv",
          ["type", "year", "quarter", "tiles", "tests", "devices",
           "wmean_down_mbps", "wmean_up_mbps", "wmean_latency_ms", "box", "source"],
          quarterly)
    write("ph_internet_speeds_coverage.csv",
          ["type", "year", "quarter", "tiles", "status", "box", "source"], coverage)

    # Latitude bands, latest available quarter of each type. USGS-style: the
    # tiles carry no administrative labels, so a "region" column would be
    # invented. Bands are the honest unit.
    rows = []
    for kind in ("fixed", "mobile"):
        got = [r for r in quarterly if r[0] == kind]
        if not got:
            continue
        y, q = got[-1][1], got[-1][2]
        for lo, hi, label in [(4, 10, "south (<10N)"), (10, 13, "central (10-13N)"),
                              (13, 21, "north (13N+)")]:
            r = con.execute("""
                select count(*), sum(tests),
                       round(sum(avg_d_kbps * tests) / sum(tests) / 1000.0, 2),
                       round(sum(avg_lat_ms * tests) / sum(tests), 1)
                from read_parquet('%s')
                where tile_x between %d and %d and tile_y >= %d and tile_y < %d"""
                % (url(kind, y, q), BOX["lon"][0], BOX["lon"][1], lo, hi)).fetchone()
            rows.append([kind, y, q, label, r[0], r[1], r[2], r[3], BOX_LABEL, SRC])
            print("  %-6s %s  %7d tiles  %8s Mbps" % (kind, label, r[0], r[2]))
    write("ph_internet_speed_bands.csv",
          ["type", "year", "quarter", "band", "tiles", "tests",
           "wmean_down_mbps", "wmean_latency_ms", "box", "source"], rows)


if __name__ == "__main__":
    main()
