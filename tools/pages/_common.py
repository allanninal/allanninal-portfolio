#!/usr/bin/env python3
"""Shared page-assembly helpers for the tools/pages/build_*.py generators.

The first six generators each carried their own copy of the section builder, the
splice logic and the head-metadata rewriter. They had already drifted -- one used
exact-indent markers and failed on the next page it was pointed at. This is the
common part, extracted once.

Nothing here knows about any particular project: callers pass content, this
places it.
"""
import decimal
import json
import os
import re


def js(x):
    return json.dumps(x)


def r(x, nd=0):
    """Round half away from zero, the way SQL does.

    Python rounds half to even, so round(2.235, 2) is 2.23 while DuckDB gives
    2.24. facts.sql rounds in SQL and the page rounds in Python, so any figure
    landing exactly on a half disagrees between them and verify_facts.py -- quite
    correctly -- refuses to publish it.
    """
    d = decimal.Decimal(str(x)).quantize(decimal.Decimal(1).scaleb(-nd),
                                         rounding=decimal.ROUND_HALF_UP)
    return float(d) if nd else int(d)


def section(n, title, desc, cards, chart_title=None, canvas=None, extra=""):
    """One <section> with a numbered header, optional chart, and insight cards.

    cards: [(heading, value, fact_key_or_None, paragraph)]
    """
    c = "\n".join(
        '''                    <div class="insight-card">
                        <h4>{h}</h4>
                        <div class="insight-value"{fa}>{v}</div>
                        <p>{p}</p>
                    </div>'''.format(h=h, v=v, p=p,
                                     fa=(' data-fact="%s"' % k) if k else "")
        for h, v, k, p in cards)
    cv = ('''
                <div class="chart-container fade-up">
                    <div class="chart-title"><span>%s</span></div>
                    <div class="chart-wrapper"><canvas id="%s"></canvas></div>
                </div>
''' % (chart_title, canvas)) if canvas else ""
    return '''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">{n:02d}</div>
                    <h2>{t}</h2>
                    <p class="section-description">{d}</p>
                </div>
{cv}{ex}
                <div class="grid-3 fade-up">
{c}
                </div>
            </div>
        </section>
'''.format(n=n, t=title, d=desc, cv=cv, ex=extra, c=c)


def prose_section(n, title, desc, cards):
    """A section of explanatory cards with no numbers in them."""
    c = "\n".join(
        '''                    <div class="insight-card">
                        <h4>%s</h4>
                        <p>%s</p>
                    </div>''' % (h, p) for h, p in cards)
    return '''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">{n:02d}</div>
                    <h2>{t}</h2>
                    <p class="section-description">{d}</p>
                </div>

                <div class="grid-3 fade-up">
{c}
                </div>
            </div>
        </section>
'''.format(n=n, t=title, d=desc, c=c)


class Page(object):
    """Load a page, replace its data regions, write it back."""

    def __init__(self, path):
        self.path = path
        self.src = open(path).read()

    def _at(self, marker, start=0):
        # Tolerant of two things these pages vary in. Indentation: they were
        # written at different times and nest the same blocks at different
        # depths, so an exact-indent index() silently fails on the next page it
        # is pointed at. And extra classes: one page has
        # <div class="project-info fade-up"> where the rest have
        # <div class="project-info">, which is enough to break an exact match.
        pat = re.escape(marker)
        if marker.endswith('">'):
            pat = re.escape(marker[:-2]) + r'[^"]*">'
        m = re.search(r"^[ \t]*" + pat, self.src[start:], re.M)
        if not m:
            raise SystemExit("%s: marker not found: %r" % (self.path, marker))
        return start + m.start()

    def hero(self, html):
        """Replace the <h1> and stats block, stopping at whatever comes next.

        Page order is not consistent. On most pages the project-info block
        follows the hero and the TL;DR comes after it; on the poverty page the
        TL;DR comes FIRST and project-info sits below it. Ending the hero at
        project-info unconditionally therefore deleted that page's whole TL;DR
        section, and the next call then failed looking for a marker this method
        had just removed. Stop at whichever boundary appears first.
        """
        i = self._at("<h1>")
        ends = []
        for marker in ('<div class="project-info">', '<section class="tldr-section">',
                       '<span class="tldr-badge">', '<section class="section">'):
            try:
                ends.append(self._at(marker, i))
            except SystemExit:
                pass
        if not ends:
            raise SystemExit("%s: no boundary after <h1>" % self.path)
        j = min(ends)
        self.src = self.src[:i] + html + "\n" + self.src[j:]

    def tldr(self, html):
        i = self._at('<span class="tldr-badge">')
        j = self._at("</div>", i + 1)
        self.src = self.src[:i] + html + self.src[j:]

    def sections(self, blocks):
        """Replace the page's content sections, whatever they are called.

        The pages disagree on markup. The ones generated later use
        <section class="section">; the earliest hand-built ones use
        <section class="fade-up"> and have no Related Projects block at all.
        Anchoring on one class meant this method silently targeted the Sources
        section on those pages instead of the content.

        So: start at the first <section> after the TL;DR closes, and end at the
        sources marker if present, else Related Projects, else the footer.
        """
        after = 0
        for marker in ('<section class="tldr-section">', '<span class="tldr-badge">'):
            try:
                after = self.src.index("</section>", self._at(marker)) + len("</section>")
                break
            except (SystemExit, ValueError):
                continue
        i = self.src.index("<section", after)
        i = self.src.rfind("\n", 0, i) + 1

        j = None
        for end in ("<!-- sources:start -->", "<h2>Related Projects</h2>"):
            k = self.src.find(end, i)
            if k >= 0:
                j = k if end.startswith("<!--") else self.src.rfind("<section", i, k)
                j = self.src.rfind("\n", 0, j) + 1
                break
        if j is None:
            k = self.src.rindex("<footer")
            j = self.src.rfind("\n", 0, k) + 1
        if j <= i:
            raise SystemExit("%s: content region resolved to nothing" % self.path)
        self.src = self.src[:i] + "\n".join(blocks) + self.src[j:]

    def charts(self, blocks):
        # Indentation varies: the later pages close with "    </script>" and the
        # earliest ones with "</script>" at column zero, which threw here.
        m = re.search(r"^[ \t]*new Chart\(", self.src, re.M)
        if not m:
            raise SystemExit("%s: no chart block found" % self.path)
        i = m.start()
        e = re.compile(r"^[ \t]*</script>", re.M).search(self.src, i)
        if not e:
            raise SystemExit("%s: chart block is not closed" % self.path)
        self.src = self.src[:i] + "\n\n".join(blocks) + "\n" + self.src[e.start():]

    def _swap(self, pat, rep, why):
        self.src, n = re.subn(pat, rep, self.src, count=1)
        if not n:
            raise SystemExit("%s: head patch failed (%s)" % (self.path, why))

    def head(self, title, description, short, headline):
        """Title, meta description, OG and Twitter cards, JSON-LD headline.

        These carry the page's numbers into search results and social previews,
        so leaving them stale keeps publishing figures the body no longer makes.
        """
        self._swap(r"<title>[^<]*</title>",
                   "<title>%s | Allan Niñal - Data Analyst Portfolio</title>" % title,
                   "title")
        self._swap(r'<meta name="description" content="[^"]*">',
                   '<meta name="description" content="%s">' % description, "description")
        self._swap(r'<meta property="og:title" content="[^"]*">',
                   '<meta property="og:title" content="%s | Allan Niñal">' % title,
                   "og:title")
        self._swap(r'<meta property="og:description" content="[^"]*">',
                   '<meta property="og:description" content="%s">' % short, "og:desc")
        self._swap(r'<meta name="twitter:title" content="[^"]*">',
                   '<meta name="twitter:title" content="%s">' % title, "tw:title")
        self._swap(r'<meta name="twitter:description" content="[^"]*">',
                   '<meta name="twitter:description" content="%s">' % short, "tw:desc")
        self._swap(r'"headline": "[^"]*"', '"headline": %s' % json.dumps(headline),
                   "headline")
        self._swap(r'"description": "[^"]*"',
                   '"description": %s' % json.dumps(description), "ld desc")

    def faq(self, pairs):
        if '"mainEntity": [' not in self.src:
            return
        items = ",\n".join(
            '            {\n'
            '                "@type": "Question",\n'
            '                "name": %s,\n'
            '                "acceptedAnswer": {\n'
            '                    "@type": "Answer",\n'
            '                    "text": %s\n'
            '                }\n'
            '            }' % (json.dumps(q), json.dumps(a)) for q, a in pairs.items())
        # Find the array's own closing bracket by matching, not by assuming a
        # layout. Some pages pretty-print the FAQ across many lines and others
        # keep the whole array on one line; anchoring on "\n        ]" worked
        # only for the first kind.
        i = self.src.index('"mainEntity": [')
        k = i + len('"mainEntity": [')
        depth, j = 1, None
        while k < len(self.src):
            ch = self.src[k]
            if ch == '"':                       # skip over strings
                k += 1
                while k < len(self.src) and self.src[k] != '"':
                    k += 2 if self.src[k] == "\\" else 1
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
                if depth == 0:
                    j = k
                    break
            k += 1
        if j is None:
            raise SystemExit("%s: mainEntity array is not closed" % self.path)
        self.src = self.src[:i] + '"mainEntity": [\n' + items + "\n        " + self.src[j:]

    def save(self, nsec, ncharts):
        open(self.path, "w").write(self.src)
        print("rebuilt %s: %d sections, %d charts" % (self.path, nsec, ncharts))
