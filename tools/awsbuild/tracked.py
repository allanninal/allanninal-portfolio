#!/usr/bin/env python3
"""Every part of every /build series must be tracked by git.

    tools/awsbuild/tracked.py          report
    tools/awsbuild/tracked.py --check  exit non-zero if anything is untracked

Why this exists. `.gitignore` carried `!/build/` on line 3 with a comment saying
/build is published site content and must be force-included -- and then a bare
`build/` on line 60. Gitignore is last-match-wins, so line 60 won and every NEW
file under build/ was silently excluded from `git add -A`. The 1,067 files added
before that rule stayed tracked, which is what made it invisible: 133 days were
fine and only the next one broke.

Day 134 was generated, validated, committed and pushed with its landing card and
sitemap entry deploying correctly while all seven of its articles returned 404.
Nothing in the build pipeline noticed, because everything it checks -- the
registry, the sitemap, the feed, the thumbnails, the JSON-LD -- was correct. The
files existed on disk and were simply never committed.

So this compares the registry against `git ls-files` rather than against the
filesystem. A part that exists locally but is not tracked is a part that will
404 in production, and that is exactly the failure this catches.
"""
import json
import os
import subprocess
import sys

REGISTRY = "tools/awsbuild/registry.json"


def main():
    check = "--check" in sys.argv
    reg = json.load(open(REGISTRY))
    tracked = set(subprocess.run(["git", "ls-files", "build/"],
                                 capture_output=True, text=True).stdout.split())
    bad, ondisk_only = [], []
    for slug, v in sorted(reg.items(), key=lambda kv: kv[1]["date"]):
        for part in v["parts"]:
            s = part["slug"] if isinstance(part, dict) else part
            path = "build/%s/index.html" % s
            if path in tracked:
                continue
            bad.append((v["date"], slug, s))
            if os.path.exists(path):
                ondisk_only.append(path)
    total = sum(len(v["parts"]) for v in reg.values())
    print("  %d series, %d parts, %d tracked, %d untracked"
          % (len(reg), total, total - len(bad), len(bad)))
    for d, slug, s in bad:
        where = "on disk, not committed" if ("build/%s/index.html" % s) in ondisk_only \
            else "missing entirely"
        print("    %s  %-34s %s  (%s)" % (d, slug, s, where))
    if bad:
        print("  these will 404 in production")
    if check:
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
