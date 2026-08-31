"""A small diagram DSL for /build.

Every diagram on the site is hand-placed inline SVG. Writing 385 more of those
by hand would guarantee drift, so the new posts describe a diagram as data and
this module lays it out: consistent geometry, AWS-category colours, a service
tile on every box, and a <desc> long enough to stand in for the picture in a
screen reader.

Five shapes cover everything the series need:

    system(...)  the whole thing on one page -- outside row, AWS container
    chain(...)   a vertical run of steps with side inputs and side exits
    lanes(...)   two or more parallel routes into the same place
    bars(...)    stacked cost bars per volume tier
    strip(...)   a horizontal at-a-glance run of stages
"""
import html
import itertools

from .icons import tile, category_of, GLYPHS
from .palette import CAT, CAT_LABEL

BG = "#16212f"
BOX = "#20303f"
BOX_EXT = "#1a2634"
STROKE = "#3f5169"
LINE = "#6b8199"
TEXT = "#e6edf5"
SUB = "#9fb0c4"
FAINT = "#8d99a8"
FONT = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

_ids = itertools.count(1)


# SVG text is character data, not HTML, so an entity written in a spec would
# render literally. Turn the few the specs use back into characters first.
_UNENT = {"&mdash;": "\u2014", "&ndash;": "\u2013", "&rsquo;": "\u2019",
          "&lsquo;": "\u2018", "&ldquo;": "\u201c", "&rdquo;": "\u201d",
          "&amp;": "&", "&nbsp;": "\u00a0", "&pound;": "\u00a3", "&hellip;": "\u2026"}


def esc(s):
    s = str(s)
    for k, v in _UNENT.items():
        s = s.replace(k, v)
    return html.escape(s, quote=False)


class Canvas:
    def __init__(self, w, h, pfx=None):
        self.w, self.h = w, h
        self.pfx = pfx or f"d{next(_ids)}"
        self.body = []
        self.cats = set()

    # -- primitives --------------------------------------------------------
    def rect(self, x, y, w, h, fill=BOX, stroke=STROKE, rx=6, dash=None, sw=1.5):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.body.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=13, fill=TEXT, weight=600, anchor="middle", italic=False):
        it = ' font-style="italic"' if italic else ""
        self.body.append(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}"{it}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, colour=LINE, sw=1.9, arrow=True, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        a = f' marker-end="url(#{self.pfx}-ar)"' if arrow else ""
        self.body.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{colour}" '
            f'stroke-width="{sw}" stroke-linecap="round"{d}{a}/>')

    def elbow(self, x1, y1, x2, y2, colour=LINE, arrow=True):
        a = f' marker-end="url(#{self.pfx}-ar)"' if arrow else ""
        self.body.append(
            f'<path d="M{x1:.0f} {y1:.0f} H{(x1 + x2) / 2:.0f} V{y2:.0f} H{x2:.0f}" fill="none" '
            f'stroke="{colour}" stroke-width="1.9" stroke-linejoin="round" '
            f'stroke-linecap="round"{a}/>')

    def tile(self, name, x, y, size=22):
        self.cats.add(category_of(name))
        self.body.append(tile(name, x, y, size, 4.5))

    # -- composites --------------------------------------------------------
    def node(self, x, y, w, h, title, sub=(), icon=None, kind="node"):
        """A component box: accent rule, service tile in a left gutter, label
        block centred in whatever width the tile leaves."""
        fill = BOX_EXT if kind == "external" else BOX
        self.rect(x, y, w, h, fill=fill)
        icon = icon or ("external" if kind == "external" else "compute")
        if icon not in GLYPHS:
            icon = "compute"
        col = CAT[category_of(icon)]
        self.body.append(
            f'<line x1="{x + 4:.0f}" y1="{y + 2:.0f}" x2="{x + w - 4:.0f}" y2="{y + 2:.0f}" '
            f'stroke="{col}" stroke-width="3.4" stroke-linecap="round"/>')
        gut = 40
        self.tile(icon, x + 11, y + (h - 22) / 2 if not sub else y + 13, 22)
        cx = x + gut + (w - gut) / 2
        n = 1 + len(sub)
        ty = y + h / 2 - (n - 1) * 8.5 + 5
        self.text(cx, ty, title, size=14, fill=TEXT, weight=700)
        for i, t in enumerate(sub):
            self.text(cx, ty + 18 + i * 16, t, size=11.5, fill=SUB, weight=400)

    def container(self, x, y, w, h, label="AWS account"):
        self.rect(x, y, w, h, fill="none", stroke="#37506b", rx=10, dash="7 5", sw=1.4)
        self.body.append(
            f'<text x="{x + 18:.0f}" y="{y + 24:.0f}" font-family="{FONT}" font-size="11.5" '
            f'font-weight="700" fill="{FAINT}" letter-spacing="1.6">{esc(label.upper())}</text>')

    def note(self, y, s):
        self.text(self.w / 2, y, s, size=12.5, fill=SUB, weight=400, italic=True)

    # -- output ------------------------------------------------------------
    def render(self, title, desc, wide=False):
        cls = "diagram diagram--wide" if wide else "diagram"
        p = self.pfx
        return (
            f'<svg class="{cls}" data-gen="1" viewBox="0 0 {self.w} {self.h}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-labelledby="{p}-t {p}-d">'
            f'<title id="{p}-t">{esc(title)}</title>'
            f'<desc id="{p}-d">{esc(desc)}</desc>'
            f'<defs><marker id="{p}-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/>'
            f'</marker></defs>'
            + "".join(self.body) + "</svg>")


ORDER = ["compute", "storage", "database", "integration", "ml", "network", "security",
         "management", "analytics", "frontend", "containers", "devtools", "business",
         "human", "external"]


def legend(cats):
    cats = [c for c in ORDER if c in cats and c in CAT_LABEL]
    if len(cats) < 3:
        return ""
    items = "".join(f'<li><span class="dot" style="background:{CAT[c]}"></span>{CAT_LABEL[c]}</li>'
                    for c in cats)
    return f'<ul class="diagram-legend" aria-label="Icon colour key">{items}</ul>'


def figure(svg, caption, cats, wide=False):
    w = " diagram-wrap--wide" if wide else ""
    return (f'<figure><div class="diagram-wrap{w}">{svg}</div>'
            f'<figcaption>{caption}</figcaption>{legend(cats)}</figure>')
