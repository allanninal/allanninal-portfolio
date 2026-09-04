#!/usr/bin/env python3
"""Philippine crop and livestock production from the FAOSTAT bulk download.

    .venv/bin/python data/ph-agriculture/_build/fetch_faostat.py

FAO publishes the whole Production_Crops_Livestock domain as a zip per region.
The Asia file is ~4 MB, against ~32 MB for the world, and contains everything
needed here, so that is what is fetched.

Two traps in this dataset, both of which inflate a total silently:

* The Item column mixes individual crops with FAO's own aggregates -- "Rice"
  and "Cereals, primary" are both rows, and the second contains the first.
  Summing the Item column gives roughly double the real harvest. Every crop
  used here is therefore named explicitly in CROPS, and the aggregates are
  never summed with their members.

* The file is wide, one column per year from Y1961 to Y2024, and a year with no
  survey is an empty cell rather than a zero. Unpivoting has to preserve that
  distinction: an empty cell becomes a missing row, not a 0-tonne harvest.

Units differ by element -- production in tonnes for crops but in 1000 head for
some livestock, yield in kg/ha for crops and kg/animal for meat. The unit is
carried on every row rather than assumed downstream.

One unit is rewritten on the way out. FAO writes tonnes as a bare "t", and a
CSV column whose only value is "t" is inferred as BOOLEAN true by DuckDB and by
most other readers, so `where unit = 't'` matches nothing and `trim(unit)`
fails outright. It is spelled "tonnes" here. Nothing else about the value
changes, and the alternative -- casting the column at every call site forever --
puts the trap one query away from being stepped in again.
"""
import csv
import io
import os
import ssl
import sys
import tempfile
import urllib.request
import zipfile

OUT = os.path.join(os.path.dirname(__file__), "..")
URL = ("https://bulks-faostat.fao.org/production/"
       "Production_Crops_Livestock_E_Asia.zip")
MEMBER = "Production_Crops_Livestock_E_Asia_NOFLAG.csv"
SRC = "FAOSTAT Production_Crops_Livestock (Asia bulk)"
UA = "allanninal.dev research (contact via github.com/allanninal)"
AREA = "Philippines"
# See the module docstring: a lone "t" is read as boolean by CSV type inference.
UNITS = {"t": "tonnes"}

# Named explicitly. Anything ending in "primary", "Total" or "Crops Primary" is
# an FAO aggregate and is excluded -- see the module docstring.
CROPS = ["Rice", "Maize (corn)", "Coconuts, in shell", "Sugar cane", "Bananas",
         "Cassava, fresh", "Sweet potatoes", "Coffee, green", "Pineapples",
         "Mangoes, guavas and mangosteens", "Abaca, manila hemp, raw",
         "Onions and shallots, dry (excluding dehydrated)", "Tomatoes",
         "Eggplants (aubergines)", "Cabbages", "Green garlic"]
LIVESTOCK = ["Cattle", "Swine / pigs", "Chickens", "Goats", "Buffalo", "Ducks"]


def download():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300,
                                context=ssl.create_default_context()) as r:
        blob = r.read()
    print("  downloaded %.1f MB" % (len(blob) / 1e6), file=sys.stderr)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = [n for n in z.namelist() if n.endswith(MEMBER)]
        if not names:
            raise SystemExit("%s not in the archive -- FAO renamed a member; "
                             "archive holds %s" % (MEMBER, z.namelist()))
        return z.read(names[0]).decode("utf-8", "replace")


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    text = download()
    rd = csv.DictReader(io.StringIO(text))
    years = [c for c in rd.fieldnames if c.startswith("Y") and c[1:].isdigit()]
    ph = [r for r in rd if r["Area"] == AREA]
    if not ph:
        raise SystemExit("no rows for %r -- FAO area naming changed, which "
                         "returns an empty file rather than an error" % AREA)
    print("  %d Philippine rows, years %s..%s"
          % (len(ph), years[0][1:], years[-1][1:]))

    def long_rows(items, element):
        out = []
        for r in ph:
            if r["Item"] not in items or r["Element"] != element:
                continue
            for y in years:
                v = (r.get(y) or "").strip()
                if not v:
                    continue          # missing year, not a zero harvest
                out.append([r["Item"], int(y[1:]), element, float(v),
                            UNITS.get(r["Unit"], r["Unit"]), SRC])
        return sorted(out, key=lambda x: (x[0], x[1]))

    prod = long_rows(CROPS, "Production")
    write("ph_agri_production.csv",
          ["item", "year", "element", "value", "unit", "source"], prod)

    write("ph_agri_yield.csv",
          ["item", "year", "element", "value", "unit", "source"],
          long_rows(CROPS, "Yield"))

    write("ph_agri_area.csv",
          ["item", "year", "element", "value", "unit", "source"],
          long_rows(CROPS, "Area harvested"))

    write("ph_agri_livestock.csv",
          ["item", "year", "element", "value", "unit", "source"],
          long_rows(LIVESTOCK, "Stocks"))

    # Coverage: which crops actually resolved, and over what span. A crop whose
    # FAO item name changes silently disappears from every chart, so the count
    # of matched items is published rather than assumed.
    cov = []
    for item in CROPS + LIVESTOCK:
        got = [r for r in prod + long_rows(LIVESTOCK, "Stocks") if r[0] == item]
        cov.append([item, len(got), min((r[1] for r in got), default=""),
                    max((r[1] for r in got), default=""),
                    "matched" if got else "NOT FOUND in FAOSTAT items", SRC])
    write("ph_agri_coverage.csv",
          ["item", "rows", "first_year", "last_year", "status", "source"], cov)
    missing = [c[0] for c in cov if not c[1]]
    if missing:
        print("  WARNING: no FAOSTAT rows for %s" % ", ".join(missing))

    # Rice yield against the neighbours. The Asia bulk already holds every
    # country in the region, so this costs nothing extra and answers the
    # question tonnage cannot: the Philippines grows a lot of rice and still
    # imports, which is a yield-per-hectare story rather than an area one.
    rd2 = csv.DictReader(io.StringIO(text))
    peers = ["Philippines", "Viet Nam", "Thailand", "Indonesia", "Malaysia",
             "China, mainland", "India", "Japan"]
    rows = []
    for r in rd2:
        if r["Area"] not in peers or r["Item"] != "Rice" or r["Element"] != "Yield":
            continue
        for y in years:
            v = (r.get(y) or "").strip()
            if v:
                rows.append([r["Area"], int(y[1:]), float(v),
                             UNITS.get(r["Unit"], r["Unit"]), SRC])
    if not rows:
        raise SystemExit("no rice yield rows -- FAO renamed the Rice item or "
                         "the Yield element")
    write("ph_agri_rice_yield_asia.csv",
          ["country", "year", "yield", "unit", "source"],
          sorted(rows, key=lambda x: (x[0], x[1])))
    have = sorted({r[0] for r in rows})
    absent = [p for p in peers if p not in have]
    if absent:
        print("  note: no rice yield for %s" % ", ".join(absent))


if __name__ == "__main__":
    main()
