"""Apply the dark recolour + AWS service icons to every diagram under /build."""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from awsbuild import diagrams
from awsbuild.palette import CAT, CAT_LABEL

FIGURE_RE = re.compile(r"<figure\b(?:(?!</figure>).)*?</figure>", re.S)
LEGEND_RE = re.compile(r'<ul class="diagram-legend">.*?</ul>', re.S)
ORDER = ["compute", "storage", "database", "integration", "ml", "network",
         "security", "management", "analytics", "frontend", "containers",
         "devtools", "business", "human", "external"]


def legend(cats):
    cats = [c for c in ORDER if c in cats and c in CAT_LABEL]
    if len(cats) < 3:
        return ""
    items = "".join(
        f'<li><span class="dot" style="background:{CAT[c]}"></span>{CAT_LABEL[c]}</li>'
        for c in cats)
    return f'<ul class="diagram-legend" aria-label="Icon colour key">{items}</ul>'


def do_figure(m):
    fig = LEGEND_RE.sub("", m.group(0))
    if "<svg" not in fig or 'data-gen="1"' in fig:
        # generated diagrams already carry the palette and picked their own
        # icons from the spec; re-deriving them from labels would be a downgrade
        return m.group(0)
    fig, cats = diagrams.transform_page(fig)
    leg = legend(cats)
    if leg:
        if "</figcaption>" in fig:
            fig = fig.replace("</figcaption>", "</figcaption>" + leg, 1)
        else:
            fig = fig.replace("</figure>", leg + "</figure>", 1)
    return fig


def main(root="build"):
    changed = svgs = 0
    for f in sorted(pathlib.Path(root).rglob("*.html")):
        s = f.read_text(encoding="utf-8")
        if "<svg" not in s:
            continue
        n = s.count("<svg")
        out = FIGURE_RE.sub(do_figure, s)
        # svgs that live outside a <figure> still get recoloured
        out, _ = diagrams.transform_page(out) if "#111111" in out else (out, None)
        if out != s:
            f.write_text(out, encoding="utf-8")
            changed += 1
            svgs += n
    print(f"pages changed: {changed}   svgs touched: {svgs}")


if __name__ == "__main__":
    main(*sys.argv[1:])
