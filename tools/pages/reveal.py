#!/usr/bin/env python3
"""Ensure any page that hides content with .fade-up also has a script to reveal it.

    .venv/bin/python tools/pages/reveal.py          # insert the observer
    .venv/bin/python tools/pages/reveal.py --check  # fail if a page is invisible

The rice-prices and electricity pages declared

    .fade-up { opacity: 0; transform: translateY(30px); ... }
    .fade-up.visible { opacity: 1; ... }

and shipped with nothing that ever adds the `visible` class -- no
IntersectionObserver in the page, and none in assets/site-nav.js. Six wrapper
elements on each page were therefore invisible from the day they were published,
which is why the pages read as "lacking" while every automated check passed:
the markup was present and correct, the facts verified, the HTML was balanced.
Nothing tests what a browser actually paints.

Regenerating those pages raised the count from 6 to 27 and made them blank.
That is the bug this file exists to make impossible.
"""
import glob
import os
import re
import sys

SNIPPET = """        // Reveal .fade-up sections on scroll. Without this the page's own CSS
        // leaves every .fade-up element at opacity 0 forever.
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.classList.add('visible');
            });
        }, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });
        document.querySelectorAll('.fade-up').forEach(el => revealObserver.observe(el));
        // Anything already on screen at load, in case the observer is late.
        window.addEventListener('load', () => {
            document.querySelectorAll('.fade-up').forEach(el => {
                if (el.getBoundingClientRect().top < window.innerHeight) {
                    el.classList.add('visible');
                }
            });
        });

"""


def needs_fix(src):
    hides = re.search(r"\.fade-up\s*\{[^}]*opacity:\s*0", src)
    uses = re.search(r'class="[^"]*\bfade-up\b', src)
    reveals = "IntersectionObserver" in src or "classList.add('visible')" in src
    return bool(hides and uses and not reveals)


def fix(path, check):
    src = open(path).read()
    if not needs_fix(src):
        return False
    if check:
        return True
    m = re.search(r"^[ \t]*<script>\s*$", src, re.M)
    if not m:
        m = re.search(r"^[ \t]*<script>", src, re.M)
    if not m:
        raise SystemExit("%s: no inline <script> to insert the observer into" % path)
    i = m.end()
    src = src[:i] + "\n" + SNIPPET + src[i:].lstrip("\n")
    open(path, "w").write(src)
    return True


def main():
    check = "--check" in sys.argv
    hits = [p for p in sorted(glob.glob("projects/*.html") + glob.glob("blog/*.html"))
            if fix(p, check)]
    for p in hits:
        print("  %-46s %s" % (p, "INVISIBLE" if check else "observer inserted"))
    print("%d page(s) %s" % (len(hits), "invisible" if check else "fixed"))
    sys.exit(1 if (check and hits) else 0)


if __name__ == "__main__":
    main()
