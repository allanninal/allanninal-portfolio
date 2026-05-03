"""Stream-clip PH OSM roads to Cebu Province polygon.

Reads:  hotosm_phl_roads_lines_geojson.geojson (~988 MB)
Writes: cebu_roads.geojson  +  cebu_roads_summary.csv
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

import decimal
import ijson
from shapely.geometry import shape, mapping
from shapely.prepared import prep


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)

HERE = Path("/tmp/cebu-logistics")
ADM2 = HERE / "phl_adm2.geojson"
ROADS = HERE / "hotosm_phl_roads_lines_geojson.geojson"
OUT_GEOJSON = HERE / "cebu_roads.geojson"
OUT_CSV = HERE / "cebu_roads_summary.csv"

print("→ loading Cebu Province polygon")
with ADM2.open() as f:
    adm2 = json.load(f)
cebu_feat = next(
    f for f in adm2["features"]
    if f["properties"]["shapeName"].lower() == "cebu"
)
cebu_geom = shape(cebu_feat["geometry"])
cebu_prep = prep(cebu_geom)
minx, miny, maxx, maxy = cebu_geom.bounds
print(f"  bbox: {minx:.3f},{miny:.3f},{maxx:.3f},{maxy:.3f}")

print("→ streaming roads and clipping")
total = 0
kept = 0
hwy_counter = Counter()
t0 = time.time()

with ROADS.open("rb") as src, OUT_GEOJSON.open("w") as dst:
    dst.write('{"type":"FeatureCollection","features":[\n')
    first = True
    for feat in ijson.items(src, "features.item"):
        total += 1
        geom_dict = feat.get("geometry")
        if not geom_dict:
            continue
        gtype = geom_dict["type"]
        coords = geom_dict["coordinates"]
        if gtype == "LineString":
            flat = coords
        elif gtype == "MultiLineString":
            flat = [pt for line in coords for pt in line]
        else:
            continue
        xs = [float(pt[0]) for pt in flat]
        ys = [float(pt[1]) for pt in flat]
        if max(xs) < minx or min(xs) > maxx or max(ys) < miny or min(ys) > maxy:
            continue
        g = shape(geom_dict)
        if not cebu_prep.intersects(g):
            continue
        kept += 1
        hwy_counter[feat["properties"].get("highway", "?")] += 1
        if not first:
            dst.write(",\n")
        json.dump(feat, dst, cls=DecimalEncoder)
        first = False
        if total % 100_000 == 0:
            print(f"  scanned {total:>8,}  kept {kept:>6,}  elapsed {time.time()-t0:.1f}s", file=sys.stderr)
    dst.write("\n]}\n")

print(f"\n✓ scanned {total:,} features, kept {kept:,} in Cebu Province")
print(f"  elapsed {time.time()-t0:.1f}s")
print(f"  output: {OUT_GEOJSON}  ({OUT_GEOJSON.stat().st_size/1e6:.1f} MB)")

print("\nhighway tag distribution (top 15):")
with OUT_CSV.open("w") as f:
    f.write("highway_class,count\n")
    for hwy, n in sorted(hwy_counter.items(), key=lambda x: -x[1]):
        f.write(f"{hwy},{n}\n")
    for hwy, n in sorted(hwy_counter.items(), key=lambda x: -x[1])[:15]:
        print(f"  {hwy:<20} {n:>6,}")
print(f"\n  summary csv: {OUT_CSV}")
