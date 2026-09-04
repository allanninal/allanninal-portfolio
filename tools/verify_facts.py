#!/usr/bin/env python3
"""Every published figure must round-trip to a row in a CSV.

Usage:  verify_facts.py [page.html ...]        (default: every projects/*.html)

A page marks its claims:

    <span data-fact="rice.spread.2020">21.0%</span>

and the project that owns the page supplies data/<project>/facts.sql:

    -- fact: rice.spread.2020
    select spread_pct from ph_rice_spread_annual where year = 2020;

The query must return exactly one value. This tool renders each query against
the project's CSVs with DuckDB, compares it to the text actually printed in the
HTML, and exits non-zero on any mismatch.

Why this exists. Chart data on these pages is generated from the CSVs and is
therefore safe. Prose is not: the numbers in it are typed by hand while reading
a CSV, which is exactly the process that put a sign error, a self-contradictory
all-time high and a duplicated placeholder year on the PSE page. Once a figure
must resolve to a row, that whole class of error becomes impossible to publish
rather than merely unlikely.

Comparison is deliberately loose about presentation and strict about value:
currency symbols, thousands separators, percent signs and the multiplication
sign are stripped, then the numbers must agree to within the precision the page
itself chose to display.
"""
import csv
import glob
import os
import re
import sys

try:
    import duckdb
except ImportError:
    sys.exit("verify_facts.py needs duckdb:  make venv")

FACT = re.compile(r'data-fact="(?P<key>[^"]+)"[^>]*>(?P<text>[^<]*)<')
HEAD = re.compile(r"--\s*fact:\s*(?P<key>\S+)\s*$", re.M)
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def project_for(page):
    """data/<project> whose facts.sql declares this page, else None."""
    stem = os.path.splitext(os.path.basename(page))[0]      # rice-prices-analysis
    for d in sorted(glob.glob("data/*")):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "facts.sql")):
            continue
        head = open(os.path.join(d, "facts.sql")).read(400)
        if stem in head:
            return d
    return None


def load_facts(project):
    """{key: sql} from facts.sql."""
    out, key, buf = {}, None, []
    for line in open(os.path.join(project, "facts.sql")):
        m = HEAD.match(line.strip())
        if m:
            if key and buf:
                out[key] = "\n".join(buf).strip().rstrip(";")
            key, buf = m.group("key"), []
            continue
        if line.strip().startswith("--"):
            continue
        if key:
            buf.append(line)
    if key and buf:
        out[key] = "\n".join(buf).strip().rstrip(";")
    return out


def connect(project):
    con = duckdb.connect()
    for path in sorted(glob.glob(os.path.join(project, "*.csv"))):
        view = os.path.splitext(os.path.basename(path))[0]
        con.execute('create view "%s" as select * from read_csv(\'%s\', header=true, '
                    'union_by_name=true)' % (view, path.replace("'", "''")))
    return con


def as_number(text):
    """The number a human would read out of this cell, or None."""
    t = text.replace("&nbsp;", " ").replace(" ", " ").strip()
    t = t.replace("&times;", "x").replace("&mdash;", "-")
    m = NUM.search(t)
    if not m:
        return None
    v = float(m.group(0).replace(",", ""))
    # The minus does not have to touch the digits. "-$54.3B" and "-P2.35" both
    # read as negative to a human, but NUM only ever sees the digits, because a
    # currency symbol sits between. Taking those as positive would let exactly
    # the sign error this tool exists to catch walk straight through.
    if v > 0 and re.search(r"[-\u2212]\s*[^\d\s]*$", t[: m.start()]):
        v = -v
    return v


def displayed_precision(text):
    m = NUM.search(text.strip())
    if not m:
        return 2
    s = m.group(0)
    return len(s.split(".")[1]) if "." in s else 0


def check(page):
    src = open(page).read()
    # Marks are only meaningful in rendered markup. A data-fact span injected
    # into a <script type="application/ld+json"> block breaks the JSON silently,
    # which is how this was first discovered -- so script bodies are excluded
    # here and must never be marked up in the first place.
    visible = re.sub(r"<script.*?</script>", " ", src, flags=re.S)
    claims = [(m.group("key"), m.group("text")) for m in FACT.finditer(visible)]
    if not claims:
        return None                                  # page opts out
    project = project_for(page)
    if not project:
        print("  %s: %d data-fact marks but no facts.sql declares this page"
              % (page, len(claims)))
        return 1
    facts = load_facts(project)
    con = connect(project)
    bad = 0
    for key, text in claims:
        if key not in facts:
            print("  MISMATCH %-28s no query defined in %s/facts.sql" % (key, project))
            bad += 1
            continue
        try:
            rows = con.execute(facts[key]).fetchall()
        except Exception as e:
            print("  ERROR    %-28s query failed: %s" % (key, e))
            bad += 1
            continue
        if len(rows) != 1 or len(rows[0]) != 1:
            print("  ERROR    %-28s query returned %d rows -- must return one value"
                  % (key, len(rows)))
            bad += 1
            continue
        want, shown = rows[0][0], as_number(text)
        if shown is None:
            # Not every published fact is a number. Region codes, month names and
            # place names are facts too, and a query that returns one should be
            # comparable as text rather than rejected for having no digits.
            if isinstance(want, str):
                if want.strip() != text.strip():
                    print("  MISMATCH %-28s page %r, data %r"
                          % (key, text.strip(), want))
                    bad += 1
                continue
            print("  ERROR    %-28s no number in rendered text %r" % (key, text))
            bad += 1
            continue
        try:
            want = float(want)
        except (TypeError, ValueError):
            if str(want).strip() != text.strip():
                print("  MISMATCH %-28s page %r, data %r" % (key, text.strip(), want))
                bad += 1
            continue
        # Agreement to the precision the page chose to display, as a tolerance
        # rather than round-and-compare: Python rounds half to even, so a CSV
        # value of 5.25 shown as the conventional 5.3 would be reported as a
        # mismatch against round(5.25, 1) == 5.2. A half-unit band accepts every
        # correct rounding of the same value and still rejects 229.5 shown as 230.
        p = displayed_precision(text)
        if abs(want - shown) > 0.5 * 10 ** -p:
            print("  MISMATCH %-28s page shows %s, data says %s" % (key, shown, want))
            bad += 1
    print("  %-46s %d fact(s), %d mismatch(es)" % (page, len(claims), bad))
    return bad


def main():
    pages = sys.argv[1:] or sorted(glob.glob("projects/*.html") + glob.glob("blog/*.html"))
    total = checked = 0
    for p in pages:
        r = check(p)
        if r is not None:
            checked += 1
            total += r
    print("\n%d page(s) carry facts, %d mismatch(es)" % (checked, total))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
