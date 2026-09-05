#!/usr/bin/env python3
"""Fail the build if a page uses a class its own stylesheet never defines.

    .venv/bin/python tools/pages/styling.py [--check]

Two class vocabularies exist across these pages. The generated ones use
stats-grid / stat-value / section-description / grid-3; the earliest hand-built
ones use metrics-grid / metric-value / section-desc / insights-grid and define
none of the former. Emitting the wrong family produced pages of correct content
rendered as unstyled stacked text -- and every other check passed, because a
class the stylesheet has never heard of is still perfectly valid markup.

Only classes this repository controls are checked. Shared nav and any other
class served from an external stylesheet are listed in EXTERNAL, since their
definitions are not in the file.
"""
import glob
import os
import re
import sys

# Classes styled elsewhere (assets/*.css, the shared header) or used purely as
# JS/behaviour hooks rather than for styling.
# Shared nav (anx-*), behaviour hooks, and modifier classes that only vary a
# base class the page does style -- .diagram-tree modifies .diagram-svg.
EXTERNAL = re.compile(r"^(anx-|sr-only$|visible$|fade-up$|container$|tall$|active$"
                      r"|diagram-tree$|red$|blue$|green$|orange$|purple$|cool$)")


def unstyled(path):
    src = open(path).read()
    used = {c for attr in re.findall(r'class="([^"]+)"', src) for c in attr.split()}
    out = []
    for c in sorted(used):
        if EXTERNAL.match(c):
            continue
        if not re.search(r"\." + re.escape(c) + r"\s*[,{ :.]", src):
            out.append(c)
    return out


def main():
    bad = {}
    for p in sorted(glob.glob("projects/*.html") + glob.glob("blog/*.html")):
        u = unstyled(p)
        if u:
            bad[p] = u
            print("  %-46s %s" % (os.path.basename(p), ", ".join(u[:6])))
    print("%d page(s) use classes their stylesheet does not define" % len(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
