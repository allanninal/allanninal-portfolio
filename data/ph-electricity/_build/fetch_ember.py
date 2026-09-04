#!/usr/bin/env python3
"""Philippine generation mix and Southeast Asian peers, from Ember.

Ember publishes a global yearly electricity dataset, free and keyless. The
download link on the data page is the stable entry point; the versioned
uploads path under ember-energy.org/app/uploads redirects to an HTML page and
must not be used.

One trap worth recording: Ember names the country "The Philippines", not
"Philippines". Filtering on the obvious string returns zero rows and an empty
chart rather than an error.

Outputs (relative to data/ph-electricity/):
    ph_generation_mix.csv    PH share of generation by source and year
    sea_coal_share.csv       coal share of generation, PH vs SEA peers
"""
import csv
import io
import os
import urllib.request

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
URL = ("https://files.ember-energy.org/public-downloads/generation/outputs/"
       "release_generation_yearly_global.csv")

PH = "The Philippines"          # not "Philippines" -- see module docstring
PEERS = [PH, "Thailand", "Viet Nam", "Indonesia", "Malaysia", "Singapore", "ASEAN"]
SOURCES = ["Coal", "Gas", "Hydro", "Solar", "Wind", "Bioenergy",
           "Other renewables", "Other fossil"]


def main():
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers=UA),
                                 timeout=240).read().decode("utf-8", "replace")
    rows = list(csv.DictReader(io.StringIO(raw)))
    print("  %d rows, %d areas" % (len(rows), len({r["Area"] for r in rows})))
    if not any(r["Area"] == PH for r in rows):
        raise SystemExit("Ember area name changed -- %r not found" % PH)

    mix = [[r["Year"], r["Electricity source"], r["Share of generation (%)"],
            r["Generation (TWh)"], "Ember yearly electricity"]
           for r in rows
           if r["Area"] == PH and r["Electricity source"] in SOURCES
           and r["Share of generation (%)"]]
    mix.sort(key=lambda x: (int(x[0]), x[1]))
    with open(os.path.join(OUT, "ph_generation_mix.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "source", "share_pct", "generation_twh", "source_dataset"])
        w.writerows(mix)
    print("  wrote ph_generation_mix.csv  %d rows" % len(mix))

    coal = [[r["Area"].replace("The Philippines", "Philippines"), r["Year"],
             r["Share of generation (%)"], "Ember yearly electricity"]
            for r in rows
            if r["Area"] in PEERS and r["Electricity source"] == "Coal"
            and r["Share of generation (%)"]]
    coal.sort(key=lambda x: (x[0], int(x[1])))
    with open(os.path.join(OUT, "sea_coal_share.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["area", "year", "coal_share_pct", "source_dataset"])
        w.writerows(coal)
    print("  wrote sea_coal_share.csv     %d rows" % len(coal))


if __name__ == "__main__":
    main()
