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

The date comes from the last commit that made a *content* change, not from today
and not from the last commit of any kind. Commits that only rewrote a date field
are skipped, because otherwise this tool chases its own tail: it writes a date,
that write is itself a commit, and the next run wants to bump it again. Four blog
posts did exactly that on the first run after the fix, flipping 09-04 to 09-05.
"""
import glob
import json
import os
import re
import subprocess
import sys

PAGES = sorted(glob.glob("projects/*.html")) + sorted(glob.glob("blog/*.html"))
MOD = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')


# A commit that only rewrote a date field is not a content change. Without this
# the tool chases its own tail: it writes the last commit date into the page, that
# write becomes a new commit, and on the next run the page looks stale again.
# Found immediately -- four blog posts flipped 2026-09-04 -> 2026-09-05 on the run
# straight after the one that had just set them to 2026-09-04.
DATEISH = re.compile(r'"date(?:Published|Modified)"|<time[^>]*datetime=')


def commit_date(path, depth=12):
    """Date of the last commit that changed something other than a date field."""
    log = subprocess.run(["git", "log", "--format=%H %cs", "-n", str(depth),
                          "--", path], capture_output=True, text=True).stdout.split("\n")
    for line in log:
        if not line.strip():
            continue
        sha, _, day = line.partition(" ")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day.strip()):
            continue
        diff = subprocess.run(["git", "show", "--format=", "--unified=0", sha,
                               "--", path], capture_output=True, text=True).stdout
        changed = [l for l in diff.split("\n")
                   if (l.startswith("+") or l.startswith("-"))
                   and not l.startswith(("+++", "---"))]
        if any(not DATEISH.search(l) for l in changed):
            return day.strip()
        # else: a dates-only commit, keep walking back
    return None


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
