#!/usr/bin/env python3
"""Shared page-assembly helpers for the tools/pages/build_*.py generators.

The first six generators each carried their own copy of the section builder, the
splice logic and the head-metadata rewriter. They had already drifted -- one used
exact-indent markers and failed on the next page it was pointed at. This is the
common part, extracted once.

Nothing here knows about any particular project: callers pass content, this
places it.
"""
import json
import os
import re


def js(x):
    return json.dumps(x)


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
        # Indentation-agnostic: these pages were written at different times and
        # nest the same blocks at different depths, so an exact-indent index()
        # silently fails on the next page it is pointed at.
        m = re.search(r"^[ \t]*" + re.escape(marker), self.src[start:], re.M)
        if not m:
            raise SystemExit("%s: marker not found: %r" % (self.path, marker))
        return start + m.start()

    def hero(self, html):
        i = self._at("<h1>")
        j = self._at('<div class="project-info">', i)
        self.src = self.src[:i] + html + "\n" + self.src[j:]

    def tldr(self, html):
        i = self._at('<span class="tldr-badge">')
        j = self._at("</div>", i + 1)
        self.src = self.src[:i] + html + self.src[j:]

    def sections(self, blocks):
        i = self._at('<section class="section">')
        j = self.src.index("<h2>Related Projects</h2>")
        j = self.src.rindex("<section", 0, j)
        j = self.src.rindex("\n", 0, j) + 1
        self.src = self.src[:i] + "\n".join(blocks) + self.src[j:]

    def charts(self, blocks):
        i = self.src.index("        new Chart(")
        j = self.src.index("    </script>", i)
        self.src = self.src[:i] + "\n\n".join(blocks) + "\n" + self.src[j:]

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
        i = self.src.index('"mainEntity": [')
        j = self.src.index("\n        ]", i)
        self.src = self.src[:i] + '"mainEntity": [\n' + items + self.src[j:]

    def save(self, nsec, ncharts):
        open(self.path, "w").write(self.src)
        print("rebuilt %s: %d sections, %d charts" % (self.path, nsec, ncharts))
