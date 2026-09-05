#!/usr/bin/env python3
"""Order the /blog index by each post's own datePublished, newest first.

    tools/pages/blog_order.py            reorder blog/index.html
    tools/pages/blog_order.py --check    exit non-zero if the order is wrong

The index was hand-ordered and approximately newest-first, which is how eight
rewritten posts ended up at positions 8 to 18 with January posts leading the page.
It had also drifted internally -- cebu-logistics (3 May) sat above dengue (5 May)
and tourism (4 May).

Each card's markup is moved verbatim: only the order of the blocks changes, so the
excerpts, images and any per-card wording written by hand survive untouched. Cards
are located by the post they link to, and the sort key is that post's own
datePublished, so the index cannot disagree with the articles again.

Ties keep their existing relative order, which matters on a day when several posts
share a date and one of them is deliberately first.

The visible date on each card is rewritten from the same datePublished. Sorting by
the real date while displaying a stale one is the version of this bug a reader can
actually see: the index was correctly ordered and still showed "Jan 2026" on
thirteen cards when only three posts were from January, which reads as an index
that was never sorted at all.
"""
import os
import re
import sys

INDEX = "blog/index.html"
CARD = re.compile(r'[ \t]*<a href="([a-z0-9-]+\.html)".*?</a>\s*', re.S)
PUB = re.compile(r'"datePublished"\s*:\s*"([^"]+)"')
DATE = re.compile(r'(<span class="article-date">)([^<]*)(</span>)')
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def label(iso):
    """2026-09-06 -> "Sep 2026", the form the cards already use."""
    if not iso or len(iso) < 7:
        return ""
    return "%s %s" % (MON[int(iso[5:7]) - 1], iso[:4])


def published(slug):
    p = os.path.join("blog", slug)
    if not os.path.exists(p):
        return ""
    m = PUB.search(open(p).read())
    return m.group(1)[:10] if m else ""


def main():
    check = "--check" in sys.argv
    src = open(INDEX).read()
    cards = list(CARD.finditer(src))
    if len(cards) < 2:
        sys.exit("%s: found %d card(s); the pattern no longer matches" % (INDEX, len(cards)))

    # The cards must be contiguous for a reorder to be a pure permutation.
    for a, b in zip(cards, cards[1:]):
        if a.end() != b.start():
            sys.exit("%s: cards are not contiguous (gap before %s); reorder aborted"
                     % (INDEX, b.group(1)))

    start, end = cards[0].start(), cards[-1].end()
    blocks = [(m.group(1), src[m.start():m.end()]) for m in cards]

    # rewrite each card's visible date from the post it links to
    stale, fixed = [], []
    for i, (slug, html) in enumerate(blocks):
        want = label(published(slug))
        m = DATE.search(html)
        if not want or not m or m.group(2).strip() == want:
            fixed.append((slug, html))
            continue
        stale.append((slug, m.group(2).strip(), want))
        fixed.append((slug, DATE.sub(lambda x: x.group(1) + want + x.group(3),
                                     html, count=1)))
    blocks = fixed
    order = sorted(range(len(blocks)),
                   key=lambda i: (published(blocks[i][0]), -i), reverse=True)
    new_blocks = [blocks[i] for i in order]

    same_order = [b[0] for b in new_blocks] == [b[0] for b in blocks]
    if stale:
        print("  %d card(s) show a date their post does not claim" % len(stale))
        for slug, was, want in stale[:12]:
            print("   %-34s %-9s -> %s" % (slug[:-5], was, want))
    if same_order and not stale:
        print("  %d card(s), already in date order" % len(blocks))
        sys.exit(0)
    if same_order:
        if check:
            print("blog/index.html shows stale card dates")
            sys.exit(1)
        open(INDEX, "w").write(src[:start] + "".join(b for _, b in blocks) + src[end:])
        print("  rewrote %s (dates only, order unchanged)" % INDEX)
        sys.exit(0)

    print("  %d card(s); order changes" % len(blocks))
    for i, (slug, _) in enumerate(new_blocks[:10], 1):
        was = [b[0] for b in blocks].index(slug) + 1
        print("   %2d  %-34s %s%s" % (i, slug[:-5], published(slug),
                                      "" if was == i else "   (was %d)" % was))
    if check:
        print("blog/index.html is OUT OF DATE ORDER")
        sys.exit(1)
    out = src[:start] + "".join(b for _, b in new_blocks) + src[end:]
    open(INDEX, "w").write(out)
    print("  rewrote %s" % INDEX)


if __name__ == "__main__":
    main()
