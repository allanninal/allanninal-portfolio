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
     above announced itself (two site-nav.js tags on one page);
  4. an unguarded getElementById for an id the page does not contain. On the
     food-prices page a rebuild removed a canvas but left
     getElementById('ricePriceChart').getContext('2d') above the chart configs.
     That threw on the first line of the script, so all six charts on the page
     stayed blank -- one stale reference taking down every chart after it. Only
     direct dereferences count: code that stores the result and null-checks it,
     or uses ?., is correct and is not reported.

Exits non-zero on any of them.
"""
import glob
import os
import re
import sys

OPEN = re.compile(r"<script\b([^>]*)>", re.I)
CLOSE = re.compile(r"</script\s*>", re.I)
SRC = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)
# Only an *unguarded* dereference is a fault. getElementById returns null for a
# missing id, and null on its own is harmless: two template pages in this repo do
# "const t = getElementById(x); if (!t) return;" and one uses "a?.querySelector",
# both of which are correct. What throws is reaching straight through the result
# with a plain dot, which is what the food-prices page did with
# getElementById('ricePriceChart').getContext('2d').
BYID = re.compile(r"""getElementById\(\s*['"]([A-Za-z][\w:.-]*)['"]\s*\)\s*\.""")
HASID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.I)


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

    # Ids the document actually has, against the ids the scripts ask for. Only
    # literal single-argument lookups are checked; anything computed is skipped
    # rather than guessed at.
    present = set(HASID.findall(src))
    for attrs, inner, line in spans(src):
        if SRC.search(attrs):
            continue
        for want in set(BYID.findall(inner)):
            if want not in present:
                bad.append('getElementById("%s").<...> dereferences a missing '
                           "id, which throws and stops every statement after it "
                           "(script at line %d)" % (want, line))
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
            # The full path, not the basename: the first version printed
            # "index.html" for faults in five different template directories,
            # which made them impossible to find.
            print("  %-52s %s" % (path, msg))
    print("%d page(s) checked, %d script fault(s)" % (len(pages), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
