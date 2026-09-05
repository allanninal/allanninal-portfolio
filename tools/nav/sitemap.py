#!/usr/bin/env python3
"""Generate sitemap-pages.xml from the filesystem, with git-derived lastmod.

    tools/nav/sitemap.py            rewrite sitemap-pages.xml and the index entry
    tools/nav/sitemap.py --check    exit non-zero if either is out of date

This file was hand-maintained and had drifted twice over. Found 2026-09-05:

  * eight pages were missing entirely, including projects/electricity-analysis
    and projects/rice-prices-analysis, and six blog posts;
  * every lastmod read 2026-08-27 or 2026-08-28 while the pages had been
    rewritten that day. lastmod is how a crawler decides whether to come back,
    so a completely rebuilt page was advertising itself as unchanged since
    August.

Neither failure is visible by looking at the file: it is well-formed XML with
plausible dates, and the missing pages are missing rather than wrong. Generating
it removes both possibilities at once.

lastmod comes from the last commit that touched each file, not from mtime. mtime
changes when a generator runs and rewrites a page byte-identically, which would
churn every date on every build; the commit date is the date the content actually
changed. Uncommitted files fall back to mtime and are reported, because an
uncommitted page has no published date yet.

Sections and priorities follow what the hand-written file used: the root at 1.0
weekly, /blog/ at 0.9, project pages at 0.8, blog posts at 0.7, everything
monthly.
"""
import datetime
import glob
import os
import re
import subprocess
import sys

BASE = "https://www.allanninal.dev/"
OUT = "sitemap-pages.xml"
INDEX = "sitemap.xml"

# (glob or literal path, url override, priority). Order is the order emitted.
SECTIONS = [
    ("__root__", "", 1.0, "weekly"),
    ("blog/index.html", "blog/", 0.9, "monthly"),
    ("projects/*.html", None, 0.8, "monthly"),
    ("blog/*.html", None, 0.7, "monthly"),
]


def commit_date(path):
    """The date of the last commit touching this file, else its mtime."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                             capture_output=True, text=True, timeout=30)
        d = out.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            return d, True
    except (OSError, subprocess.SubprocessError):
        pass
    ts = os.path.getmtime(path)
    return datetime.date.fromtimestamp(ts).isoformat(), False


def entries():
    seen, rows, uncommitted = set(), [], []
    for pattern, override, pri, freq in SECTIONS:
        if pattern == "__root__":
            paths = ["index.html"]
        elif "*" in pattern:
            paths = sorted(glob.glob(pattern))
        else:
            paths = [pattern] if os.path.exists(pattern) else []
        for p in paths:
            # blog/index.html is emitted once as /blog/ by its own section, so
            # the blog/*.html glob must not pick it up again.
            if override is None and os.path.basename(p) == "index.html":
                continue
            url = BASE + (override if override is not None else p)
            if url in seen:
                continue
            seen.add(url)
            d, committed = commit_date(p)
            if not committed:
                uncommitted.append(p)
            rows.append((url, d, freq, pri))
    return rows, uncommitted


def render(rows):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, d, freq, pri in rows:
        out += ["  <url>",
                "    <loc>%s</loc>" % url,
                "    <lastmod>%s</lastmod>" % d,
                "    <changefreq>%s</changefreq>" % freq,
                "    <priority>%s</priority>" % pri,
                "  </url>"]
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def index_updated(newest):
    """Point the sitemap index's own entry for OUT at the newest page date."""
    if not os.path.exists(INDEX):
        return None
    s = open(INDEX).read()
    pat = re.compile(r"(<loc>%s%s</loc>\s*<lastmod>)([^<]*)(</lastmod>)"
                     % (re.escape(BASE), re.escape(OUT)))
    m = pat.search(s)
    if not m:
        return None
    if m.group(2) == newest:
        return s
    return pat.sub(lambda mm: mm.group(1) + newest + mm.group(3), s, count=1)


def main():
    check = "--check" in sys.argv
    rows, uncommitted = entries()
    newest = max(d for _, d, _, _ in rows)
    body = render(rows)
    have = open(OUT).read() if os.path.exists(OUT) else ""
    idx_new = index_updated(newest)
    idx_have = open(INDEX).read() if os.path.exists(INDEX) else ""

    stale = (body != have) or (idx_new is not None and idx_new != idx_have)
    print("  %d url(s), newest page %s" % (len(rows), newest))
    for p in uncommitted:
        print("    uncommitted, dated from mtime: %s" % p)
    if check:
        print("sitemap-pages.xml is %s" % ("STALE" if stale else "current"))
        sys.exit(1 if stale else 0)
    if body != have:
        open(OUT, "w").write(body)
        print("  wrote %s" % OUT)
    if idx_new is not None and idx_new != idx_have:
        open(INDEX, "w").write(idx_new)
        print("  updated the %s entry in %s to %s" % (OUT, INDEX, newest))
    if not stale:
        print("  already current")


if __name__ == "__main__":
    main()
