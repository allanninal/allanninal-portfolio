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

MARK = "<!-- reveal:fade-up -->"

# Its own tag at the end of <body>, not appended to an existing inline script.
# The first inline <script> on these pages is the analytics tag in <head>, so a
# snippet placed there runs before the body exists and
# document.querySelectorAll('.fade-up') matches nothing -- which is exactly the
# blank page it was meant to fix, with the observer present in the source.
#
# Guarded on readyState so it works whether the parser has finished or not, and
# it reveals whatever is already on screen before observing the rest, so the
# first viewport is never blank while waiting for a scroll event.
SNIPPET = MARK + """
<script>
(function () {
  function reveal() {
    var els = document.querySelectorAll('.fade-up');
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.02, rootMargin: '0px 0px -32px 0px' });
    els.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 1.25) {
        el.classList.add('visible');
      } else {
        io.observe(el);
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', reveal);
  } else {
    reveal();
  }
})();
</script>
"""


def needs_fix(src):
    hides = re.search(r"\.fade-up\s*\{[^}]*opacity:\s*0", src)
    uses = re.search(r'class="[^"]*\bfade-up\b', src)
    reveals = "IntersectionObserver" in src or "classList.add('visible')" in src
    return bool(hides and uses and not reveals)


def fix(path, check):
    src = open(path).read()
    if MARK in src or not needs_fix(src):
        return False
    if check:
        return True
    # End of <body>, never appended to an existing inline script: the first one
    # on these pages is the analytics tag in <head>, where this code would run
    # before the body exists and match nothing.
    if "</body>" not in src:
        raise SystemExit("%s: no </body> to insert before" % path)
    i = src.rindex("</body>")
    open(path, "w").write(src[:i] + SNIPPET + src[i:])
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
