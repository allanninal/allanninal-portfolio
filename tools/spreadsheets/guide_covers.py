#!/usr/bin/env python3
"""One featured image per guide article — 1280x800 PNG, same size as the product covers.

These are not decorative. Every guide on this section is about a specific thing Excel
does to a specific value, so the image shows THAT: the value as you typed it, and the
value Excel gave back, in the same monospace the article uses. A reader who sees the
card in a search result or a social embed learns the actual failure before clicking, and
two guides never produce the same picture because the data differs.

Palette is read from the section's own stylesheet variables (the green re-skin), so a
change there is a one-line change here rather than a set of drifting hex codes.

Fonts: DejaVu ships with matplotlib/PIL on this machine and covers the box-drawing and
arrow glyphs used below. If a face is missing, PIL silently falls back to a bitmap font
at a fixed tiny size — so the loader raises instead, rather than shipping 23 covers with
unreadable type.

Usage: python3 guide_covers.py [--only <slug> ...]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path.home() / "Projects/allanninal.dev/spreadsheets/assets/img/guides"
W, H = 1280, 800

# The section's green re-skin, from spreadsheets.css.
INK = "#14261d"; INK_SOFT = "#476455"; INK_FAINT = "#7b9488"
GREEN = "#217346"; GREEN_DEEP = "#1a5c38"; TINT = "#e6f4ec"
PAPER = "#ffffff"; SURFACE = "#f6fbf8"; BORDER = "#d2e8dc"
RED = "#c5221f"; RED_TINT = "#fceceb"; OK = "#0f9d58"; OK_TINT = "#e6f6ee"

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
MONOS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
]


def _font(paths, size, index=0):
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size, index=index)
            except Exception:
                continue
    raise SystemExit(
        f"No usable font among {paths}. PIL would silently substitute a bitmap face "
        f"and every cover would ship with unreadable type, so this stops instead.")


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def cover(slug: str, kicker: str, headline: str, before: str, after: str,
          caption: str) -> Path:
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)

    f_kick = _font(FONTS, 26)
    f_head = _font(FONTS, 62)
    f_cap = _font(FONTS, 25)
    f_mono = _font(MONOS, 46)
    f_small = _font(MONOS, 22)

    M = 84                                   # margin
    # Top rule + kicker
    d.rectangle([0, 0, W, 10], fill=GREEN)
    d.text((M, 62), kicker.upper(), font=f_kick, fill=GREEN)

    # Headline
    y = 116
    for line in wrap(d, headline, f_head, W - 2 * M)[:3]:
        d.text((M, y), line, font=f_head, fill=INK)
        y += 74

    # The transformation panel — the actual point of the image.
    py = max(y + 44, 380)
    ph = 200
    d.rounded_rectangle([M, py, W - M, py + ph], radius=16, fill=SURFACE, outline=BORDER, width=2)

    cx = W // 2
    # before (what you typed) — correct, so green
    bw = d.textlength(before, font=f_mono)
    d.rounded_rectangle([M + 40, py + 52, M + 40 + bw + 36, py + 52 + 74],
                        radius=10, fill=OK_TINT)
    d.text((M + 58, py + 68), before, font=f_mono, fill=OK)
    d.text((M + 40, py + 140), "what you had", font=f_small, fill=INK_FAINT)

    # arrow
    ay = py + 88
    d.line([cx - 30, ay, cx + 30, ay], fill=INK_FAINT, width=4)
    d.polygon([(cx + 30, ay - 12), (cx + 30, ay + 12), (cx + 54, ay)], fill=INK_FAINT)

    # after (what Excel gave back) — the damage, so red
    aw = d.textlength(after, font=f_mono)
    ax = W - M - 40 - aw - 36
    d.rounded_rectangle([ax, py + 52, ax + aw + 36, py + 52 + 74],
                        radius=10, fill=RED_TINT)
    d.text((ax + 18, py + 68), after, font=f_mono, fill=RED)
    # Right-align the label to the panel edge. Anchoring it to the value box ran it off
    # the page whenever the label was wider than the value, which was most of them.
    lbl = "what Excel gave back"
    d.text((W - M - 40 - d.textlength(lbl, font=f_small), py + 140), lbl,
           font=f_small, fill=INK_FAINT)

    # Caption
    cy = py + ph + 46
    for line in wrap(d, caption, f_cap, W - 2 * M)[:2]:
        d.text((M, cy), line, font=f_cap, fill=INK_SOFT)
        cy += 34

    # Footer
    d.line([M, H - 92, W - M, H - 92], fill=BORDER, width=2)
    d.text((M, H - 68), "allanninal.dev/spreadsheets", font=f_small, fill=INK_FAINT)
    tag = "FREE WORKBOOK + GUIDE"
    d.text((W - M - d.textlength(tag, font=f_small), H - 68), tag, font=f_small, fill=GREEN)

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{slug}.png"
    im.save(p, "PNG", optimize=True)
    return p


def index_cover(n_guides: int, n_kits: int, n_products: int) -> Path:
    """The featured image for /spreadsheets/ itself.

    A different layout from the per-guide covers: this one has no before/after pair,
    because the section is not about a single failure. It shows what is actually here.

    The three numbers are PASSED IN and rendered at build time, never typed. Every stale
    figure on this site started life as a number somebody typed into a design once — see
    the profile card and the gallery stat tile, both of which froze for weeks.
    """
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    f_kick = _font(FONTS, 26)
    f_head = _font(FONTS, 66)
    f_cap = _font(FONTS, 26)
    f_num = _font(FONTS, 76)
    f_lbl = _font(MONOS, 21)
    f_small = _font(MONOS, 22)

    M = 84
    d.rectangle([0, 0, W, 10], fill=GREEN)
    d.text((M, 62), "ALLANNINAL.DEV / SPREADSHEETS", font=f_kick, fill=GREEN)

    # Deliberately NOT the page's own H1. The image sits directly beneath the headline,
    # and repeating it word for word inside the picture reads as a mistake rather than as
    # emphasis. This line says the thing the headline does not.
    y = 122
    for line in wrap(d, "Free workbooks, and guides to what Excel does without asking",
                     f_head, W - 2 * M)[:2]:
        d.text((M, y), line, font=f_head, fill=INK)
        y += 80

    cy = max(y + 30, 330)
    for line in wrap(d, "Every one contains a calculation that free templates normally get "
                        "wrong. Plain .xlsx — nothing to install.", f_cap, W - 2 * M)[:2]:
        d.text((M, cy), line, font=f_cap, fill=INK_SOFT)
        cy += 36

    # three tiles, evenly spaced across the safe width
    ty = cy + 54
    tw = (W - 2 * M - 2 * 26) // 3
    tiles = [(n_kits, "FREE WORKBOOKS", OK, OK_TINT),
             (n_guides, "GUIDES", GREEN, TINT),
             (n_products, "PAID WORKBOOKS", INK_SOFT, SURFACE)]
    for i, (num, label, fg, bg) in enumerate(tiles):
        x = M + i * (tw + 26)
        d.rounded_rectangle([x, ty, x + tw, ty + 168], radius=16, fill=bg, outline=BORDER, width=2)
        d.text((x + 28, ty + 26), str(num), font=f_num, fill=fg)
        d.text((x + 28, ty + 118), label, font=f_lbl, fill=INK_FAINT)

    d.line([M, H - 92, W - M, H - 92], fill=BORDER, width=2)
    d.text((M, H - 68), "Excel + Google Sheets", font=f_small, fill=INK_FAINT)
    tag = "NO MACROS, NO ADD-INS"
    d.text((W - M - d.textlength(tag, font=f_small), H - 68), tag, font=f_small, fill=GREEN)

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "index.png"
    im.save(p, "PNG", optimize=True)
    return p


def build(specs: list[dict], only: set | None = None) -> int:
    n = 0
    for s in specs:
        if only and s["slug"] not in only:
            continue
        p = cover(**s)
        print(f"  ok   {s['slug']:42s} {p.stat().st_size // 1024:>4} KB")
        n += 1
    return n


if __name__ == "__main__":
    from guide_covers_data import COVERS
    only = {a for a in sys.argv[1:] if not a.startswith("--")} or None
    print(f"guide covers -> {OUT}")
    n = build(COVERS, only)
    print(f"  {n} cover(s)")
