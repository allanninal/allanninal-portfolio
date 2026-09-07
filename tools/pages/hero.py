#!/usr/bin/env python3
"""Numbers in a hero paragraph that nothing verifies.

    tools/pages/hero.py            list every unverified hero figure
    tools/pages/hero.py --check    exit non-zero if any is not allowed

verify_facts.py binds every figure wrapped in a data-fact span to a row in a
project's facts.sql. Nothing looks at the rest of the page, and the hero
paragraph -- the first and most-read sentence of every analysis -- turned out to
be entirely outside that net: 29 of 31 heroes carried numbers and not one hero
bound anything.

Most of them were safe by accident. 54 of the 71 repeated a figure that IS bound
somewhere further down, so a drift would have shown up there. The other 17 were
claims made once, in the most prominent place on the page, with nothing checking
them: 32,702 province-week observations, 1,117,692 daily readings, 282 listed
companies.

A hero number passes if it matches the rendered value of a bound fact on the same
page. Anything else has to be named in ALLOWED below, with a reason -- and a
number that is genuinely a fact should be bound rather than listed there.
"""
import glob
import os
import re
import sys

NUM = re.compile(r'(?<![\w.,>-])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d{2,})(?![\w.<-])')
HERO = re.compile(r'<p class="[^"]*hero[^"]*desc[^"]*">(.*?)</p>', re.S)
BOUND = re.compile(r'data-fact="[^"]*">([^<]*)<')
YEAR = re.compile(r'(19|20)\d\d')

# page slug -> {value: why it is not a fact}. Only for numbers that are genuinely
# not claims about the data. A real figure belongs in facts.sql and in a span.
ALLOWED = {
    "traffic": {"15": "part of the date '15 March 2020', not a quantity"},
    "earthquake": {"4.5": "the magnitude threshold the query used, not a result"},
    "dengue": {"32,702": "the province-week row count of the upstream HDX file, "
                         "cited and linked on the page; the committed CSVs are "
                         "aggregates of it and cannot reproduce the figure"},
    "stock-market": {"282": "the whole exchange, cited to the PSE. This dataset's "
                            "own universe is 80 tickers and the page says so, "
                            "which is the distinction worth keeping"},
}


def hero_numbers(path):
    src = open(path, encoding="utf-8").read()
    m = HERO.search(src)
    if not m:
        return None, [], set()
    hero = m.group(1)

    values = set()
    for v in BOUND.findall(src):
        values.add(norm(v))
        for n in NUM.finditer(v):
            values.add(norm(n.group(1)))

    stripped = re.sub(r'<span data-fact="[^"]*">.*?</span>', " ", hero, flags=re.S)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", stripped))
    out = []
    for n in NUM.finditer(text):
        v = n.group(1)
        if YEAR.fullmatch(v):
            continue
        out.append((v, text[max(0, n.start() - 46):n.end() + 24].strip()))
    return hero, out, values


def norm(v):
    v = (v or "").replace(",", "").strip()
    if "." in v:
        v = v.rstrip("0").rstrip(".")
    return v


def main():
    check = "--check" in sys.argv
    pages = sorted(glob.glob("projects/*-analysis.html"))
    heroes = matched = allowed = 0
    bad = []
    for p in pages:
        slug = os.path.basename(p)[:-len("-analysis.html")]
        hero, nums, values = hero_numbers(p)
        if hero is None:
            continue
        heroes += 1
        for v, ctx in nums:
            if norm(v) in values:
                matched += 1
            elif norm(v) in {norm(k) for k in ALLOWED.get(slug, {})}:
                allowed += 1
            else:
                bad.append((slug, v, ctx))

    print("  %d hero(es); %d figure(s) repeat a bound fact, %d allowed, "
          "%d unverified" % (heroes, matched, allowed, len(bad)))
    for slug, v, ctx in bad:
        print("   %-24s %-10s %s" % (slug, v, ctx[:74]))
    if bad and check:
        print("hero figures are not verified by anything")
        sys.exit(1)


if __name__ == "__main__":
    main()
