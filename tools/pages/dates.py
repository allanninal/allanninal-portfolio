#!/usr/bin/env python3
"""dateModified on a page must match the last commit that changed it.

    tools/pages/dates.py            update every stale dateModified
    tools/pages/dates.py --check    exit non-zero if any page is stale

Eight project pages and eight blog posts were rewritten from scratch on
2026-09-05 -- new title, new thesis, every figure recomputed -- and every one of
them still declared dateModified as 2026-01-26. The blog index is ordered by
date, so the day's work sorted into the middle of the list while January posts
led the page, and every machine-readable signal said the content was seven months
old.

datePublished is deliberately left alone. These are the same articles about the
same datasets, rewritten rather than replaced, so the date they first appeared is
still true and dateModified is exactly the field that carries a rewrite. Changing
datePublished would also silently reorder a reader's sense of what came first.

The date comes from the last commit that touched the file, not from today, so
running this twice does not keep moving dates and a page nobody has edited keeps
the date it earned.
"""
import glob
import json
import os
import re
import subprocess
import sys

PAGES = sorted(glob.glob("projects/*.html")) + sorted(glob.glob("blog/*.html"))
MOD = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')


def commit_date(path):
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                         capture_output=True, text=True).stdout.strip()
    return out if re.fullmatch(r"\d{4}-\d{2}-\d{2}", out) else None


def main():
    check = "--check" in sys.argv
    stale, fixed, nofield = [], [], []
    for p in PAGES:
        if os.path.basename(p) == "index.html":
            continue
        s = open(p).read()
        m = MOD.search(s)
        if not m:
            nofield.append(p)
            continue
        want = commit_date(p)
        if not want:
            continue
        have = m.group(2)[:10]
        if have == want:
            continue
        stale.append((p, have, want))
        if not check:
            # Preserve whatever time component the page already used, if any.
            tail = m.group(2)[10:]
            s = MOD.sub(lambda mm: mm.group(1) + want + tail + mm.group(3), s, count=1)
            # And keep the JSON-LD parseable, which is the whole point of the field.
            open(p, "w").write(s)
            for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                  s, re.S):
                json.loads(blk)
            fixed.append(p)
    for p, have, want in stale:
        print("  %-42s %s -> %s" % (p, have, want))
    for p in nofield:
        print("  %-42s no dateModified field" % p)
    print("%d page(s) checked, %d stale%s"
          % (len(PAGES) - 2, len(stale), ", %d updated" % len(fixed) if fixed else ""))
    if check:
        sys.exit(1 if stale else 0)


if __name__ == "__main__":
    main()
