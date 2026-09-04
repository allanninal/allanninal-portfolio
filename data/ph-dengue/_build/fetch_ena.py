#!/usr/bin/env python3
"""Pull Philippine dengue virus genomic records from the ENA portal API.

The ENA portal API is free, needs no key, and imposes no rate wall for
queries this size. Two result types are collected:

  sequence  -- deposited nucleotide sequences (the richer set). Serotype is
               taken from scientific_name ("dengue virus type 3"), which is
               populated far more reliably than the `serotype` field.
  read_run  -- raw sequencing runs, with platform, centre and study.

IMPORTANT CAVEAT, carried into the CSVs and any chart built from them:
a sequence count is a measure of *sequencing effort*, not of incidence.
Years with more sequences are years someone funded sequencing. Only the
serotype *composition* within a year is epidemiologically meaningful, and
even that is subject to which outbreaks got investigated.

Outputs (relative to data/ph-dengue/):
    ph_dengue_ena_sequences.csv        one row per sequence
    ph_dengue_ena_serotype_by_year.csv counts and shares by year
    ph_dengue_ena_runs.csv             one row per sequencing run
    ph_dengue_ena_studies.csv          runs grouped by study and centre
"""
import collections
import csv
import io
import os
import re
import urllib.parse
import urllib.request

API = "https://www.ebi.ac.uk/ena/portal/api/search"
# NCBI taxon 12637 = Dengue virus; tax_tree() pulls all four serotypes below it
QUERY = 'tax_tree(12637) AND country="Philippines"'
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "allanninal.dev data pipeline (contact via allanninal.dev)"}

SEQ_FIELDS = ("accession,sequence_accession,scientific_name,tax_id,collection_date,"
              "first_public,last_updated,country,location,host,serotype,strain,isolate,"
              "base_count,description,study_accession,sample_accession,collected_by,"
              "isolation_source,mol_type")
RUN_FIELDS = ("run_accession,study_accession,sample_accession,scientific_name,tax_id,"
              "instrument_platform,instrument_model,center_name,collection_date,"
              "first_public,host,serotype,strain,isolate,read_count,base_count,"
              "library_strategy")


def fetch(result, fields):
    q = urllib.parse.urlencode({"result": result, "query": QUERY, "fields": fields,
                                "format": "tsv", "limit": 0, "dataPortal": "ena"})
    raw = urllib.request.urlopen(
        urllib.request.Request(API + "?" + q, headers=UA), timeout=180
    ).read().decode("utf-8", "replace")
    return list(csv.DictReader(io.StringIO(raw), delimiter="\t"))


def serotype(row):
    """DENV-1..4 from scientific_name, falling back to the serotype field."""
    name = (row.get("scientific_name") or "").lower()
    for token, label in (("type 1", "DENV-1"), ("type 2", "DENV-2"),
                         ("type 3", "DENV-3"), ("type 4", "DENV-4")):
        if token in name:
            return label
    s = (row.get("serotype") or "").strip()
    return "DENV-" + s if s in ("1", "2", "3", "4") else "unspecified"


def year_of(row):
    """Collection year where given, else the year it was made public."""
    for field in ("collection_date", "first_public"):
        m = re.match(r"(\d{4})", (row.get(field) or "").strip())
        if m:
            y = int(m.group(1))
            if 1990 <= y <= 2030:
                return y, ("collected" if field == "collection_date" else "published")
    return None, None


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-42s %d rows" % (name, len(rows)))


def main():
    print("querying ENA: %s" % QUERY)
    seqs = fetch("sequence", SEQ_FIELDS)
    runs = fetch("read_run", RUN_FIELDS)
    print("  %d sequences, %d runs" % (len(seqs), len(runs)))

    write("ph_dengue_ena_sequences.csv",
          ["accession", "serotype", "year", "year_basis", "collection_date",
           "first_public", "host", "strain", "isolate", "base_count",
           "study_accession", "source"],
          [[r["accession"], serotype(r), year_of(r)[0] or "", year_of(r)[1] or "",
            r["collection_date"], r["first_public"], r["host"], r["strain"],
            r["isolate"], r["base_count"], r["study_accession"], "ENA portal API"]
           for r in sorted(seqs, key=lambda r: (year_of(r)[0] or 0, r["accession"]))])

    by = collections.defaultdict(collections.Counter)
    for r in seqs:
        y, _ = year_of(r)
        if y:
            by[y][serotype(r)] += 1
    order = ["DENV-1", "DENV-2", "DENV-3", "DENV-4", "unspecified"]
    rows = []
    for y in sorted(by):
        c = by[y]
        n = sum(c.values())
        # deterministic: rank by count then name, and say so when it is a tie
        known = sorted(((v, k) for k, v in c.items() if k != "unspecified"),
                       key=lambda t: (-t[0], t[1]))
        if not known:
            dom = ""
        elif len(known) > 1 and known[0][0] == known[1][0]:
            dom = "tie: " + "/".join(k for v, k in known if v == known[0][0])
        else:
            dom = known[0][1]
        rows.append([y] + [c[k] for k in order] + [n]
                    + ["%.1f" % (c[k] / n * 100) for k in order[:4]]
                    + [dom, "ENA portal API"])
    write("ph_dengue_ena_serotype_by_year.csv",
          ["year"] + [k.lower().replace("-", "") for k in order] + ["total"]
          + ["%s_share_pct" % k.lower().replace("-", "") for k in order[:4]]
          + ["dominant", "source"], rows)

    write("ph_dengue_ena_runs.csv",
          ["run_accession", "study_accession", "serotype", "year", "instrument_platform",
           "instrument_model", "center_name", "library_strategy", "read_count", "source"],
          [[r["run_accession"], r["study_accession"], serotype(r), year_of(r)[0] or "",
            r["instrument_platform"], r["instrument_model"], r["center_name"],
            r["library_strategy"], r["read_count"], "ENA portal API"]
           for r in sorted(runs, key=lambda r: (year_of(r)[0] or 0, r["run_accession"]))])

    studies = collections.defaultdict(lambda: [0, set(), set(), set()])
    for r in runs:
        st = studies[r["study_accession"]]
        st[0] += 1
        st[1].add(r["center_name"])
        st[2].add(r["instrument_platform"])
        y, _ = year_of(r)
        if y:
            st[3].add(y)
    write("ph_dengue_ena_studies.csv",
          ["study_accession", "runs", "centers", "platforms", "years", "source"],
          [[k, v[0], "; ".join(sorted(x for x in v[1] if x)),
            "; ".join(sorted(x for x in v[2] if x)),
            "%s-%s" % (min(v[3]), max(v[3])) if v[3] else "", "ENA portal API"]
           for k, v in sorted(studies.items(), key=lambda kv: -kv[1][0])])


if __name__ == "__main__":
    main()
