#!/usr/bin/env python3
"""The thousand most common Filipino forenames, and what they can be asked.

The published page had five figures on it -- Mary, 2.23M, 1:48, and "R & A" for
the most common initials. The first three are right. The fourth is half right:
by the number of people carrying them, R is the commonest initial and A is
fourth, behind M and J.

The dataset is one table of 1,000 rows: rank, forename, incidence, frequency as
a 1:N ratio, gender, and the share of bearers of that gender. It has no time
dimension, no regional split and no stated collection date, so most questions
about Philippine names cannot be answered from it. Three can.

The first is how concentrated names are. The 1,000 names cover 74,581,757
people, and the top 100 of them account for 38.57% of that.

The second comes from a cross-check the file makes possible without meaning to.
Incidence is a count of bearers; frequency is 1 in N people. Multiplying them
recovers the population the data was compiled against, and it should be the same
number for every row. It is: the implied base runs from 105,713,344 to
106,995,936 across all thousand names, a spread of 1.2% entirely explained by the
frequency denominator being rounded to a whole number. Two columns agreeing that
closely is worth more than either alone -- and the median, 106,009,905, dates an
undated file, because the Philippines passed 106 million people around 2019-2020.
That is an inference, and the page says so.

The third is gender. 520 of the names are recorded female and 480 male, but the
male names cover more people -- so a male name is carried by more people on
average than a female one, which is a statement about the variety of women's
names rather than about how many women there are.

Writes:
  ph_names_top.csv         all 1,000 rows, cleaned, with the implied base
  ph_names_initials.csv    people per first letter
  ph_names_gender.csv      the two gender groups compared
  ph_names_ambiguous.csv   names whose gender split is not near-unanimous
  ph_names_concentration.csv  cumulative coverage at each rank cut
  ph_names_coverage.csv    what this file is and is not
"""
import csv
import io
import os
import re
import statistics
import zipfile
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
KAGGLE = ("https://www.kaggle.com/api/v1/datasets/download/"
          "jorizivannvillanueva/most-popular-names-in-philippines-dataset")
SRC = ("Kaggle jorizivannvillanueva/most-popular-names-in-philippines-dataset "
       "(1,000 most common Philippine forenames)")

# Below this share, the file does not really claim the name belongs to one
# gender. Stated as a constant because the page quotes the count it produces.
AMBIGUOUS_BELOW = 90
CUTS = [1, 5, 10, 25, 50, 100, 250, 500, 1000]


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-30s %5d rows" % (name, len(rows)))


def num(v):
    """A count from a cell that may carry thousands separators."""
    v = str(v or "").replace(",", "").strip()
    return int(v) if v.isdigit() else None


def main():
    req = urllib.request.Request(KAGGLE, headers={"User-Agent": "Mozilla/5.0"})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=180).read()))
    names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if len(names) != 1:
        raise SystemExit("archive layout changed: %s" % z.namelist())
    raw = list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))
    print("  %d row(s)" % len(raw))

    rows, bases = [], []
    for r in raw:
        inc = num(r["incidence"])
        m = re.match(r"^\s*1\s*:\s*([\d,]+)\s*$", r["frequency"] or "")
        den = num(m.group(1)) if m else None
        if inc is None:
            raise SystemExit("unparseable incidence for %r" % r["forename"])
        if den is None:
            raise SystemExit("unparseable frequency %r for %r"
                             % (r["frequency"], r["forename"]))
        base = inc * den
        bases.append(base)
        gp = num(r["gender_percentage"])
        rows.append([int(r["rank"]), r["forename"].strip(), inc, den, base,
                     r["gender"].strip(), gp,
                     "ambiguous" if gp is not None and gp < AMBIGUOUS_BELOW else "",
                     SRC])

    med = int(statistics.median(bases))
    total = sum(x[2] for x in rows)
    write("ph_names_top.csv",
          ["rank", "forename", "incidence", "one_in_n", "implied_population",
           "gender", "gender_pct", "flag", "source"], rows)
    print("  implied population base: median %s (min %s, max %s)"
          % (format(med, ","), format(min(bases), ","), format(max(bases), ",")))

    # ---- initials -----------------------------------------------------------
    ini = {}
    for x in rows:
        c = x[1][0].upper()
        ini.setdefault(c, [0, 0])
        ini[c][0] += x[2]
        ini[c][1] += 1
    write("ph_names_initials.csv",
          ["initial", "people", "pct_of_covered", "names", "source"],
          sorted(([c, v[0], round(100.0 * v[0] / total, 2), v[1], SRC]
                  for c, v in ini.items()), key=lambda r: -r[1]))

    # ---- gender --------------------------------------------------------------
    g = {}
    for x in rows:
        g.setdefault(x[5], [0, 0])
        g[x[5]][0] += x[2]
        g[x[5]][1] += 1
    write("ph_names_gender.csv",
          ["gender", "names", "people", "pct_of_covered", "people_per_name",
           "source"],
          sorted(([k, v[1], v[0], round(100.0 * v[0] / total, 2),
                   int(round(v[0] / v[1])), SRC] for k, v in g.items()),
                 key=lambda r: -r[2]))

    # ---- names the file is not sure about ------------------------------------
    amb = sorted((x for x in rows if x[7] == "ambiguous"), key=lambda x: x[6])
    write("ph_names_ambiguous.csv",
          ["rank", "forename", "incidence", "gender", "gender_pct",
           "minority_pct", "source"],
          [[x[0], x[1], x[2], x[5], x[6], 100 - x[6], SRC] for x in amb])

    # ---- how concentrated ----------------------------------------------------
    cum, conc = 0, []
    ranked = sorted(rows, key=lambda x: x[0])
    for k, x in enumerate(ranked, 1):
        cum += x[2]
        if k in CUTS:
            conc.append([k, cum, round(100.0 * cum / total, 2),
                         round(100.0 * cum / med, 2), SRC])
    write("ph_names_concentration.csv",
          ["top_n_names", "people", "pct_of_covered", "pct_of_population",
           "source"], conc)

    cov = [
        ["names in the file", len(rows), "the 1,000 most common", SRC],
        ["people covered", total,
         "sum of incidence across the 1,000 names", SRC],
        ["implied population base", med,
         "median of incidence x frequency across all 1,000 rows; the two columns "
         "agree to within 1.2%, which is the frequency denominator being rounded "
         "to a whole number", SRC],
        ["implied base, lowest", min(bases), "", SRC],
        ["implied base, highest", max(bases), "", SRC],
        ["share of the population covered", round(100.0 * total / med, 2),
         "%; the rest carry a forename outside the top 1,000", SRC],
        ["collection date stated in the file", 0,
         "none. The implied base of %s dates it to roughly 2019-2020, when the "
         "Philippine population passed 106 million -- an inference, not a "
         "statement from the source" % format(med, ","), SRC],
        ["time dimension", 0,
         "one snapshot. No name can be shown rising or falling, and the page "
         "makes no claim about naming trends", SRC],
        ["regional or provincial split", 0,
         "national only, so nothing here distinguishes Ilocos from Mindanao", SRC],
        ["surnames", 0,
         "forenames only. Philippine surnames were assigned administratively in "
         "1849 and are a different subject", SRC],
        ["age of bearers", 0,
         "a name common among the living is not a name common among the newborn, "
         "and this file cannot tell the two apart", SRC],
        ["methodology published by the source", 0,
         "how incidence was counted is not documented in the dataset", SRC],
    ]
    write("ph_names_coverage.csv", ["property", "value", "note", "source"], cov)


if __name__ == "__main__":
    main()
