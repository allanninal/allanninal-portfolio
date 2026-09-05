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


# Two class vocabularies exist across these pages and they are not compatible.
# The later, generated pages use stat-*/section-number/grid-3/chart-wrapper; the
# earliest hand-built ones use metric-*/section-desc/insights-grid/chart-card and
# define none of the former. Emitting the wrong family produces markup the page
# has no CSS for, which renders as unstyled stacked text -- correct content,
# broken presentation, and every automated check still passing.
#
# So the theme is detected from what the page's own stylesheet defines.
THEMES = {
    "modern": dict(
        hero_desc="hero-description", grid="stats-grid", card="stat-card",
        value="stat-value", label="stat-label", numbered=True,
        sec_desc="section-description", cards_grid="grid-3",
        card_head="h4", card_body="p", chart_wrap=True),
    "classic": dict(
        hero_desc="hero-desc", grid="metrics-grid", card="metric-card",
        value="metric-value", label="metric-label", numbered=False,
        sec_desc="section-desc", cards_grid="insights-grid",
        card_head="div class=\"insight-title\"", card_body="p class=\"insight-text\"",
        chart_wrap=False),
}


def defines(src, cls):
    return re.search(r"\." + re.escape(cls) + r"\s*[,{ :.]", src) is not None


def pick(src, *candidates):
    """First class name this page's own stylesheet defines.

    Per role rather than per family. A two-family model was too coarse: the
    poverty page defines metric-value AND grid-3 but neither insights-grid nor
    section-description, so classifying it as one family or the other emitted a
    class it has no styling for either way.
    """
    for c in candidates:
        if defines(src, c):
            return c
    return candidates[0]


def detect_theme(src):
    """Legacy two-family label, kept for the numbered/chart-markup choice."""
    if defines(src, "stat-value") and defines(src, "grid-3"):
        return "modern"
    if defines(src, "metric-value") and defines(src, "insights-grid"):
        return "classic"
    return "modern"


def only_defined(src, *candidates):
    """The first candidate this page defines, or "" if it defines none.

    pick() falls back to its first candidate so that a role always has a name.
    That is right for roles the layout cannot do without, and wrong for optional
    wrappers: the food-prices page styles no section-header and no insight-card
    at all, and emitting them anyway put five undefined classes on it. Where a
    page has no candidate, the caller omits the attribute instead.
    """
    for c in candidates:
        if defines(src, c):
            return c
    return ""


def theme_for(src):
    """Per-role class names resolved against this page's stylesheet.

    Three layout families are in the repo and each has variants, so this resolves
    role by role rather than picking a family. The candidate lists are ordered
    most-specific first and were assembled by listing what each page's own
    stylesheet actually defines; a class emitted without a definition is still
    valid markup, renders as unstyled stacked text, and passes every check that
    does not look for exactly this.
    """
    return dict(
        hero_desc=pick(src, "hero-description", "hero-desc", "hero-subtitle",
                       "header-subtitle"),
        grid=pick(src, "stats-grid", "metrics-grid", "metrics-row", "hero-stats"),
        card=pick(src, "stat-card", "metric-card", "hero-stat"),
        value=pick(src, "stat-value", "metric-value", "hero-stat-value"),
        label=pick(src, "stat-label", "metric-label", "hero-stat-label"),
        sec_desc=pick(src, "section-description", "section-desc", "chart-subtitle"),
        cards_grid=pick(src, "grid-3", "insights-grid", "insight-grid"),
        numbered=defines(src, "section-number"),
        wrap="section fade-up" if defines(src, "section") else "fade-up",
        # Optional wrappers: omitted where the page styles neither name.
        sec_head=only_defined(src, "section-header"),
        card_wrap=only_defined(src, "insight-card", "insight-box"),
        card_head=("h4" if defines(src, "grid-3")
                   else ('div class="insight-title"' if defines(src, "insight-title")
                         else "h4")),
        # Only use the insight-text wrapper where the page styles it; a third
        # layout defines insight-title but not insight-text, and emitting it
        # there produced unstyled body copy.
        card_body=('p class="insight-text"' if defines(src, "insight-text") else "p"),
        chart_wrap=defines(src, "chart-wrapper"),
        # Two pages wrap a canvas in .chart-card inside .charts-grid rather than
        # in .chart-wrapper, and one uses .chart-grid. Resolved, not assumed.
        chart_outer=only_defined(src, "chart-grid", "charts-grid"),
        chart_card=only_defined(src, "chart-card"),
        # The figure inside a section card. Resolved or omitted, not defaulted:
        # the education page styles insight-title and insight-text but no value
        # class at all, and pick() falling through to its first candidate put an
        # undefined insight-value on every card it generated. A bare div reads
        # fine; a class no stylesheet defines does not.
        insight_value=only_defined(src, "insight-value", "insight-number",
                                   "metric-value", "stat-value",
                                   "hero-stat-value"),
    )


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
        self.theme = detect_theme(self.src)
        self.t = theme_for(self.src)


    def retheme(self, html):
        """Translate the modern class names into this page's vocabulary.

        Generators are written once against one vocabulary; a page that defines
        the other gets unstyled stacked text otherwise -- content correct,
        presentation broken, and nothing in the pipeline catches it because the
        markup is valid either way.
        """
        t = self.t
        MAP = {"hero-description": t["hero_desc"], "stats-grid": t["grid"],
               "stat-card": t["card"], "stat-value": t["value"],
               "stat-label": t["label"],
               "section-description": t["sec_desc"], "grid-3": t["cards_grid"]}

        # Whole class tokens only. The first version matched with \b, and "-" is a
        # word boundary, so "stat-value" matched inside "hero-stat-value" -- which
        # a generator emits when the page's own vocabulary is the hero-stat-* one.
        # The result was class="hero-hero-stat-value": a class no stylesheet
        # defines, on the page's headline figures, produced by the very code that
        # exists to prevent that.
        def swap(m):
            names = [MAP.get(c, c) for c in m.group(1).split()]
            # Collapse duplicates a rename can create without reordering.
            seen, out = set(), []
            for c in names:
                if c not in seen:
                    seen.add(c)
                    out.append(c)
            return 'class="%s"' % " ".join(out)

        return re.sub(r'class="([^"]*)"', swap, html)

    def section(self, n, title, desc, cards, chart_title=None, canvas=None, extra=""):
        """Numbered section rendered in this page's own class vocabulary."""
        t = self.t
        head_open = "<" + t["card_head"] + ">"
        head_close = "</" + t["card_head"].split()[0] + ">"
        body_open = "<" + t["card_body"] + ">"
        body_close = "</" + t["card_body"].split()[0] + ">"
        cw = (' class="%s"' % t["card_wrap"]) if t["card_wrap"] else ""
        vc = (' class="%s"' % t["insight_value"]) if t["insight_value"] else ""
        c = "\n".join(
            '                    <div%s>\n'
            '                        %s%s%s\n'
            '                        <div%s%s>%s</div>\n'
            '                        %s%s%s\n'
            '                    </div>'
            % (cw, head_open, h, head_close, vc,
               (' data-fact="%s"' % k) if k else "", v,
               body_open, p, body_close)
            for h, v, k, p in cards)
        if canvas and t["chart_wrap"]:
            cv = ('\n                <div class="chart-container fade-up">\n'
                  '                    <div class="chart-title"><span>%s</span></div>\n'
                  '                    <div class="chart-wrapper"><canvas id="%s"></canvas></div>\n'
                  '                </div>\n' % (chart_title, canvas))
        elif canvas and t["chart_outer"] and t["chart_card"]:
            cv = ('\n                <div class="%s fade-up">\n'
                  '                    <div class="%s">\n'
                  '                        <h3 class="chart-title">%s</h3>\n'
                  '                        <div class="chart-container tall"><canvas id="%s"></canvas></div>\n'
                  '                    </div>\n'
                  '                </div>\n'
                  % (t["chart_outer"], t["chart_card"], chart_title, canvas))
        elif canvas:
            # No grid or card class on this page: the container alone carries the
            # sizing, and the title is a plain heading.
            cv = ('\n                <div class="chart-container fade-up">\n'
                  '                    <h3 class="chart-title">%s</h3>\n'
                  '                    <canvas id="%s"></canvas>\n'
                  '                </div>\n' % (chart_title, canvas))
        else:
            cv = ""
        num = ('                    <div class="section-number">%02d</div>\n' % n) \
            if t["numbered"] else ""
        # class="section" is only styled on the modern pages; emitting it on a
        # classic page adds a class its stylesheet never defines.
        cls = t["wrap"]
        hcls = ("%s fade-up" % t["sec_head"]) if t["sec_head"] else "fade-up"
        return ('        <section class="%s">\n'
                '            <div class="container">\n'
                '                <div class="%s">\n'
                '%s'
                '                    <h2>%s</h2>\n'
                '                    <p class="%s">%s</p>\n'
                '                </div>\n'
                '%s%s\n'
                '                <div class="%s fade-up">\n'
                '%s\n'
                '                </div>\n'
                '            </div>\n'
                '        </section>\n'
                % (cls, hcls, num, title, t["sec_desc"], desc, cv, extra,
                   t["cards_grid"], c))

    def prose(self, n, title, desc, cards):
        """Section of explanatory cards with no figures in them."""
        t = self.t
        head_open = "<" + t["card_head"] + ">"
        head_close = "</" + t["card_head"].split()[0] + ">"
        body_open = "<" + t["card_body"] + ">"
        body_close = "</" + t["card_body"].split()[0] + ">"
        cw = (' class="%s"' % t["card_wrap"]) if t["card_wrap"] else ""
        c = "\n".join(
            '                    <div%s>\n'
            '                        %s%s%s\n'
            '                        %s%s%s\n'
            '                    </div>' % (cw, head_open, h, head_close,
                                            body_open, p, body_close)
            for h, p in cards)
        num = ('                    <div class="section-number">%02d</div>\n' % n) \
            if t["numbered"] else ""
        cls = t["wrap"]
        hcls = ("%s fade-up" % t["sec_head"]) if t["sec_head"] else "fade-up"
        return ('        <section class="%s">\n'
                '            <div class="container">\n'
                '                <div class="%s">\n'
                '%s'
                '                    <h2>%s</h2>\n'
                '                    <p class="%s">%s</p>\n'
                '                </div>\n\n'
                '                <div class="%s fade-up">\n'
                '%s\n'
                '                </div>\n'
                '            </div>\n'
                '        </section>\n'
                % (cls, hcls, num, title, t["sec_desc"], desc, t["cards_grid"], c))

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
        """Replace the <h1> and stats block, keeping the hero's wrappers closed.

        Page order is not consistent. On most pages a project-info block follows
        the hero and the TL;DR comes after it; on the poverty page the TL;DR
        comes first and project-info sits far below, past a block of stale
        metrics. Ending the hero at project-info therefore deleted that page's
        TL;DR, and ending it at </section> ate the container's closing </div>.

        So the end is the hero's own </section> (or project-info if that comes
        first), and the div balance of what was removed is compared with the div
        balance of what is inserted -- any shortfall is closed explicitly. That
        is arithmetic rather than guesswork about which trailing tags belong to
        whom.
        """
        html = self.retheme(html)
        i = self._at("<h1>")
        ends = []
        try:
            ends.append(self._at('<div class="project-info">', i))
        except SystemExit:
            pass
        # The hero is <section class="hero"> on most pages and <header> on at
        # least one. Take whichever closing tag comes first after the <h1>;
        # searching only for </section> ran straight past the header and ate its
        # container's closing </div>.
        cands = [self.src.find(t, i) for t in ("</section>", "</header>")]
        cands = [c for c in cands if c >= 0]
        close = min(cands) if cands else -1
        if close >= 0:
            ends.append(self.src.rfind("\n", 0, close) + 1)
        if not ends:
            raise SystemExit("%s: no boundary after <h1>" % self.path)
        j = min(ends)

        def net(text):
            return (len(re.findall(r"<div\b", text))
                    - len(re.findall(r"</div>", text)))

        # The removed span starts inside the hero's container, so it carries
        # that container's </div> without the matching <div>: its net is
        # negative. To preserve the document's balance the inserted block must
        # end with the same net, so the difference is appended as closers.
        shortfall = net(html) - net(self.src[i:j])
        if shortfall < 0:
            raise SystemExit("%s: hero block closes %d more div(s) than the "
                             "region it replaces" % (self.path, -shortfall))
        closers = "".join("                </div>\n" for _ in range(shortfall))
        self.src = self.src[:i] + html + closers + "\n" + self.src[j:]

    def tldr(self, html):
        html = self.retheme(html)
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
        # Start immediately after the TL;DR rather than at the next <section>.
        # The poverty page keeps a block of fabricated metrics in a bare
        # <div class="container"> between the two, which a <section> anchor
        # skipped straight past and left on the page.
        i = self.src.rfind("\n", 0, self.src.find("\n", after) + 1) + 1
        if i <= after:
            i = after

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

        # Same arithmetic as hero(): the replaced region can begin inside a
        # wrapper it does not open and end outside one it does not close, so the
        # div balance of what goes out is matched by what comes in. On one page
        # the TL;DR sits inside a <div class="container"> that the content
        # region then closed, and cutting there left it open for the rest of the
        # document.
        def net(text):
            return (len(re.findall(r"<div\b", text))
                    - len(re.findall(r"</div>", text)))

        def unclosed_openers(text):
            """Opening <div> tags in this text that it never closes.

            The typhoon page wraps every section in one outer
            <div class="container"> that opens inside the replaced region and
            closes outside it. Emitting sections that each carry their own
            container leaves that outer div unopened, and the balance guard below
            correctly refused. Re-emitting the tags verbatim keeps the class,
            which a generic <div> would not.
            """
            stack = []
            for m in re.finditer(r"<div\b[^>]*>|</div>", text):
                if m.group(0).startswith("</"):
                    if stack:
                        stack.pop()
                else:
                    stack.append(m.group(0))
            return stack

        new = "\n".join(blocks)
        removed = self.src[i:j]
        shortfall = net(new) - net(removed)
        if shortfall < 0:
            # The region opens wrappers it does not close. Re-open the same ones,
            # outermost first, so whatever closes them after j still matches.
            openers = unclosed_openers(removed)
            if len(openers) != -shortfall:
                raise SystemExit(
                    "%s: content blocks close %d more div(s) than the region they "
                    "replace, and %d unclosed opener(s) were found -- the two "
                    "should agree" % (self.path, -shortfall, len(openers)))
            new = ("".join("    %s\n" % t for t in openers)) + new
            shortfall = 0
        new += "".join("        </div>\n" for _ in range(shortfall))
        self.src = self.src[:i] + new + self.src[j:]

    BEGIN = "        // charts:generated -- everything below is rebuilt\n"

    def charts(self, blocks):
        """Replace the page's chart configs, idempotently.

        This used to anchor on the first "new Chart(" and replace from there to
        the closing </script>. Two things went wrong with that, both found by
        loading the page in a browser rather than by reading it:

          * whatever sat between the script's opening tag and the first chart
            survived. On the food-prices page that was
            "document.getElementById('ricePriceChart').getContext('2d')" for a
            canvas the new sections had removed, so the script threw on line one
            and *all six* charts stayed blank -- not just the missing one;
          * it was not idempotent. The comment lines above the first chart were
            not part of the replaced span, so every rebuild prepended another
            copy. Five rebuilds left the same comment four times over.

        So the generated region is now fenced by a sentinel. Lines before it are
        kept only if they are page setup (Chart.defaults and the like) rather than
        a reference to a canvas, since a stale canvas reference is exactly the
        fault above.
        """
        m = re.search(r"^[ \t]*(?:// charts:generated|new Chart\()", self.src, re.M)
        if not m:
            raise SystemExit("%s: no chart block found" % self.path)
        e = re.compile(r"^[ \t]*</script>", re.M).search(self.src, m.start())
        if not e:
            raise SystemExit("%s: chart block is not closed" % self.path)

        # Walk back to the opening <script> so setup above the first chart is
        # visible, and drop from it anything that addresses a canvas.
        o = self.src.rfind("<script>", 0, m.start())
        head = ""
        if o >= 0:
            body_start = self.src.index(">", o) + 1
            keep = []
            for line in self.src[body_start:m.start()].split("\n"):
                if "getElementById" in line or "getContext" in line:
                    continue
                if line.strip().startswith("//") and not line.strip("/ ").startswith(
                        ("Chart.defaults", "Global", "Shared")):
                    # Comments here belong to a previous generated run or to the
                    # canvas line just dropped; the generated blocks carry their
                    # own.
                    continue
                keep.append(line)
            head = "\n".join(keep).rstrip("\n")
            if head.strip():
                head += "\n\n"
            self.src = self.src[:body_start] + head + self.src[m.start():]
            shift = body_start + len(head) - m.start()
            m_start = body_start + len(head)
            e_start = e.start() + shift
        else:
            m_start, e_start = m.start(), e.start()

        self.src = (self.src[:m_start] + self.BEGIN
                    + "\n\n".join(blocks) + "\n" + self.src[e_start:])

    def _swap(self, pat, rep, why):
        # The replacement goes through a lambda so re never interprets it as a
        # template. A page whose description contains a peso sign gets it back
        # from json.dumps as \u20b1, and re.subn reads that \u as a bad escape
        # and raises -- which is a crash triggered by the page's own content.
        self.src, n = re.subn(pat, lambda _m: rep, self.src, count=1)
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

    def relocate(self, old_slug, og_image=None, keywords=None,
                 dataset_name=None, dataset_desc=None, breadcrumb=None):
        """Repoint every self-referential field after copying a page as a scaffold.

        head() rewrites the title, description, OG/Twitter text and the JSON-LD
        headline, which is everything an existing page needs. A page created by
        copying another one needs more: its canonical URL, og:url, og:image,
        keywords, JSON-LD @id, dataset block and breadcrumb all still name the page
        it was copied from.

        Found when the first non-Philippines page was built from a copy of the
        typhoon page and shipped declaring canonical
        /projects/typhoon-analysis.html -- which tells search engines the new page
        is a duplicate of a different article and should not be indexed at all.
        """
        new_slug = os.path.splitext(os.path.basename(self.path))[0]
        if old_slug == new_slug:
            return
        before = self.src
        # Every self-reference: canonical, og:url, JSON-LD @id, breadcrumb item.
        self.src = self.src.replace("/projects/%s.html" % old_slug,
                                    "/projects/%s.html" % new_slug)
        self.src = self.src.replace("/blog/%s.html" % old_slug,
                                    "/blog/%s.html" % new_slug)
        if before == self.src:
            raise SystemExit("%s: relocate found no reference to %s -- is the "
                             "scaffold slug right?" % (self.path, old_slug))
        if og_image:
            self.src = re.sub(r'(og:image" content="[^"]*/)[^"/]+(")',
                              lambda m: m.group(1) + og_image + m.group(2),
                              self.src)
            self.src = re.sub(r'(twitter:image" content="[^"]*/)[^"/]+(")',
                              lambda m: m.group(1) + og_image + m.group(2),
                              self.src)
            self.src = re.sub(r'("image":\s*"[^"]*/)[^"/]+(")',
                              lambda m: m.group(1) + og_image + m.group(2),
                              self.src)
        if keywords:
            self._swap(r'<meta name="keywords" content="[^"]*">',
                       '<meta name="keywords" content="%s">' % ", ".join(keywords),
                       "keywords")
            self.src = re.sub(r'"keywords":\s*\[[^\]]*\]',
                              lambda _m: '"keywords": %s' % json.dumps(keywords),
                              self.src, count=1)
        if dataset_name:
            self.src = re.sub(r'("@type":\s*"Dataset",\s*"name":\s*")[^"]*(")',
                              lambda m: m.group(1) + dataset_name + m.group(2),
                              self.src, count=1)
            # Some pages put name before @type; cover that ordering too.
            self.src = re.sub(r'("name":\s*")[^"]*(",\s*"description":\s*"[^"]*",'
                              r'\s*"@type":\s*"Dataset")',
                              lambda m: m.group(1) + dataset_name + m.group(2),
                              self.src, count=1)
        if dataset_desc:
            i = self.src.find('"Dataset"')
            if i > 0:
                j = self.src.find('"description"', i)
                if 0 < j < i + 400:
                    k = self.src.index('"', self.src.index(":", j) + 1)
                    e = self.src.index('"', k + 1)
                    self.src = self.src[:k + 1] + dataset_desc + self.src[e:]
        if breadcrumb:
            # The last breadcrumb item is this page.
            self.src = re.sub(r'("name":\s*")[^"]*("\s*\}\s*\]\s*\})',
                              lambda m: m.group(1) + breadcrumb + m.group(2),
                              self.src, count=1)

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
