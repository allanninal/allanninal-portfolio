"""Series card thumbnails, dark and colour-coded like the diagrams inside."""
import pathlib

from .icons import tile, category_of, GLYPHS
from .palette import CAT

W, H = 480, 270
BG = "#16212f"
BOX = "#20303f"
STROKE = "#3f5169"
LINE = "#6b8199"
TEXT = "#e6edf5"
FAINT = "#8d99a8"
ACCENT = "#ff9900"
FONT = "ui-sans-serif,system-ui,sans-serif"


def _wrap(name, n=22):
    words, lines, cur = name.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:2]


def thumb(name, icons, parts=7):
    icons = [i if i in GLYPHS else "compute" for i in (list(icons) + ["compute"] * 3)[:3]]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-label="{name} — series thumbnail">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<rect x="8" y="8" width="{W-16}" height="{H-16}" rx="12" fill="none" '
         f'stroke="{STROKE}" stroke-width="1.4"/>',
         f'<line x1="20" y1="11" x2="{W-20}" y2="11" stroke="{ACCENT}" stroke-width="4" '
         f'stroke-linecap="round"/>',
         f'<text x="30" y="48" font-family="{FONT}" font-size="11" font-weight="700" '
         f'letter-spacing="3" fill="{FAINT}">SERIES</text>',
         f'<text x="450" y="48" text-anchor="end" font-family="{FONT}" font-size="11" '
         f'font-weight="700" letter-spacing="2" fill="{FAINT}">{parts} PARTS</text>',
         f'<rect x="30" y="70" width="420" height="98" rx="8" fill="none" stroke="#37506b" '
         f'stroke-width="1.3" stroke-dasharray="6 4"/>',
         f'<text x="44" y="90" font-family="{FONT}" font-size="10" font-weight="700" '
         f'letter-spacing="2" fill="{FAINT}">AWS</text>',
         f'<defs><marker id="tar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
         f'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/>'
         f'</marker></defs>']
    xs = [78, 210, 342]
    for i, (x, ic) in enumerate(zip(xs, icons)):
        col = CAT[category_of(ic)]
        o.append(f'<rect x="{x - 34}" y="{100}" width="68" height="52" rx="8" fill="{BOX}" '
                 f'stroke="{STROKE}" stroke-width="1.3"/>')
        o.append(f'<line x1="{x - 30}" y1="102" x2="{x + 30}" y2="102" stroke="{col}" '
                 f'stroke-width="3" stroke-linecap="round"/>')
        o.append(tile(ic, x - 14, 114, 28, 6))
        if i < 2:
            o.append(f'<line x1="{x + 38}" y1="126" x2="{xs[i + 1] - 40}" y2="126" '
                     f'stroke="{LINE}" stroke-width="1.8" marker-end="url(#tar)"/>')
    lines = _wrap(name)
    size = 26 if len(lines) == 1 else 23
    o.append(f'<text font-family="{FONT}" font-size="{size}" font-weight="700" fill="{TEXT}">')
    y = 212 if len(lines) == 1 else 202
    for i, ln in enumerate(lines):
        o.append(f'<tspan x="30" y="{y + i * 27}">{ln}</tspan>')
    o.append("</text></svg>")
    return "".join(o)


def write(slug, name, icons, root=None):
    root = pathlib.Path(root or (pathlib.Path(__file__).resolve().parents[2]
                                 / "build/assets/thumbs"))
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{slug}.svg").write_text(thumb(name, icons), encoding="utf-8")
