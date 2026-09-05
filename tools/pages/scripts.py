#!/usr/bin/env python3
"""Every <script> on every page must be well formed, and must be able to run.

    tools/pages/scripts.py [page.html ...]        (default: every HTML file)

Why this exists. The dengue page shipped with two blank charts from publication.
An older version of the nav injector had put

    <script defer src="/assets/site-nav.js">

between chart 6 and chart 7 instead of before </body>, and left it open. A
script element with a src attribute ignores its inline content entirely, so the
two serotype chart configs sat inside a tag that would never execute them. Every
static check passed the whole time: the configs were valid JavaScript, the facts
verified, the tags balanced across the file as a whole, the JSON-LD parsed. Only
a browser knew the canvases were empty, and nothing was looking.

Three faults are checked, all of which make code silently not run:

  1. a script tag carrying src that also has inline content -- the content is
     dead, and this is what happened above;
  2. unbalanced <script> and </script> counts, which reparents whatever follows;
  3. the same external script included more than once, which is how the split
     above announced itself (two site-nav.js tags on one page).

Exits non-zero on any of them.
"""
import glob
import os
import re
import sys

OPEN = re.compile(r"<script\b([^>]*)>", re.I)
CLOSE = re.compile(r"</script\s*>", re.I)
SRC = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)


def spans(src):
    """(attrs, inner_text, line) for each script element, in document order."""
    out, pos = [], 0
    while True:
        m = OPEN.search(src, pos)
        if not m:
            return out
        c = CLOSE.search(src, m.end())
        if not c:
            out.append((m.group(1), src[m.end():], src.count("\n", 0, m.start()) + 1))
            return out
        out.append((m.group(1), src[m.end():c.start()],
                    src.count("\n", 0, m.start()) + 1))
        pos = c.end()


def problems(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    bad = []

    nopen, nclose = len(OPEN.findall(src)), len(CLOSE.findall(src))
    if nopen != nclose:
        bad.append("%d <script> against %d </script>" % (nopen, nclose))

    seen = {}
    for attrs, inner, line in spans(src):
        m = SRC.search(attrs)
        if m:
            seen.setdefault(m.group(1), []).append(line)
            # A src script's inner text never executes. Whitespace is harmless;
            # anything else is code that has been silently switched off.
            if inner.strip():
                bad.append("line %d: <script src=\"%s\"> has %d bytes of inline "
                           "content, which never runs"
                           % (line, m.group(1), len(inner.strip())))
    for url, lines in seen.items():
        if len(lines) > 1:
            bad.append("%s included %d times (lines %s)"
                       % (url, len(lines), ", ".join(str(x) for x in lines)))
    return bad


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = args or sorted(
        p for p in glob.glob("**/*.html", recursive=True)
        if not p.startswith(("node_modules", "redesign/", "dist/", ".venv"))
        and "/_astro/" not in p)
    bad = 0
    for path in pages:
        for msg in problems(path):
            bad += 1
            print("  %-46s %s" % (os.path.basename(path), msg))
    print("%d page(s) checked, %d script fault(s)" % (len(pages), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
