#!/usr/bin/env python3
"""Validate a project's CSVs. Exit non-zero if anything is ERROR.

Usage:  check.py data/<project> [...]

Each project supplies a checks.sql. Every statement in it is a SELECT whose
returned rows are failures, preceded by a comment naming the check and its
level:

    -- check: vocabulary closure
    -- level: error
    select distinct commodity from rice where commodity not in (...);

Design notes worth keeping:

* DuckDB reads the CSVs directly, so a check is the same SQL you would type
  while exploring. One dependency, no dataframe library, no warehouse.

* Range checks must be PER SERIES, never global. A global 10-200 PHP/kg band
  over the rice panel flags 173 perfectly good Basmati rows, because Basmati
  genuinely costs 215-250. A check that cries wolf gets switched off, which is
  worse than no check.

* Vocabulary closure is the cheapest high-value check there is. The rice panel
  shipped with a single 'sGlutinous' row -- a parse artifact among 20 otherwise
  clean variety names. No range or type check would ever have seen it.

* Coverage continuity catches the opposite failure: a parser that silently
  stops working. If a year has source documents but zero output rows, that is
  an error, not an empty chart.
"""
import glob
import os
import re
import sys

try:
    import duckdb
except ImportError:
    sys.exit("check.py needs duckdb:  uv pip install --python .venv/bin/python duckdb")

HEAD = re.compile(r"--\s*check:\s*(?P<name>.+?)\s*$", re.M)
LEVEL = re.compile(r"--\s*level:\s*(?P<level>error|warn)\s*$", re.M | re.I)


def statements(sql):
    """[(name, level, sql)] -- split on blank-line-separated blocks."""
    out = []
    for block in re.split(r"\n\s*\n", sql):
        if not block.strip() or block.strip().startswith("--") and "select" not in block.lower():
            continue
        name = (HEAD.search(block).group("name") if HEAD.search(block) else "unnamed")
        level = (LEVEL.search(block).group("level").lower() if LEVEL.search(block) else "error")
        body = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--"))
        if body.strip():
            out.append((name, level, body.strip().rstrip(";")))
    return out


def run(project):
    checks_path = os.path.join(project, "checks.sql")
    if not os.path.exists(checks_path):
        print("  %-40s no checks.sql, skipped" % project)
        return 0, 0

    con = duckdb.connect()
    # every CSV in the project becomes a view named after its file
    for csv_path in sorted(glob.glob(os.path.join(project, "*.csv"))):
        view = os.path.splitext(os.path.basename(csv_path))[0]
        # DuckDB cannot bind a parameter inside CREATE VIEW, so the path is
        # inlined; it comes from glob() on our own repo, not user input.
        con.execute('create view "%s" as select * from read_csv(\'%s\', '
                    'header=true, union_by_name=true, filename=true)'
                    % (view, csv_path.replace("'", "''")))

    errors = warns = 0
    for name, level, body in statements(open(checks_path).read()):
        try:
            rows = con.execute(body).fetchall()
        except Exception as e:
            print("  ERROR  %-34s check itself failed: %s" % (name, e))
            errors += 1
            continue
        if rows:
            tag = "ERROR" if level == "error" else "warn "
            print("  %s  %-34s %d row(s)" % (tag, name, len(rows)))
            for r in rows[:5]:
                print("         %s" % (r,))
            if len(rows) > 5:
                print("         ... and %d more" % (len(rows) - 5))
            if level == "error":
                errors += 1
            else:
                warns += 1
        else:
            print("  ok     %s" % name)
    return errors, warns


def main():
    targets = sys.argv[1:] or sorted(
        d for d in glob.glob("data/*") if os.path.isdir(d) and not d.endswith("_lib"))
    total_e = total_w = 0
    for t in targets:
        print("%s" % t)
        e, w = run(t)
        total_e += e
        total_w += w
    print("\n%d error(s), %d warning(s)" % (total_e, total_w))
    sys.exit(1 if total_e else 0)


if __name__ == "__main__":
    main()
