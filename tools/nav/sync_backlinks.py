#!/usr/bin/env python3
"""Keep each project page's blog back-link text matching the blog post's title.

    .venv/bin/python tools/nav/sync_backlinks.py [--check]

Every projects/*.html carries a box quoting the title of its blog counterpart.
Retitling a blog post leaves that quote stale, and it is easy to miss because it
sits below the fold in prose rather than in a heading. Five pages were rebuilt
before this existed and all five ended up quoting a title that no longer exists.
"""
import glob
import os
import re
import sys

QUOTE = re.compile(r"(companion post &mdash; &ldquo;)(.*?)(&rdquo;)", re.S)


def title_of(blog_path):
    s = open(blog_path).read()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else None


def main():
    check = "--check" in sys.argv
    changed = stale = 0
    for page in sorted(glob.glob("projects/*.html")):
        blog = os.path.join("blog", os.path.basename(page))
        if not os.path.exists(blog):
            continue
        want = title_of(blog)
        if not want:
            continue
        src = open(page).read()
        m = QUOTE.search(src)
        if not m or m.group(2).strip() == want:
            continue
        stale += 1
        print("  %-46s %r -> %r" % (page, m.group(2).strip(), want))
        if not check:
            open(page, "w").write(QUOTE.sub(lambda x: x.group(1) + want + x.group(3),
                                            src, count=1))
            changed += 1
    print("%d stale, %d rewritten" % (stale, changed))
    sys.exit(1 if (check and stale) else 0)


if __name__ == "__main__":
    main()
