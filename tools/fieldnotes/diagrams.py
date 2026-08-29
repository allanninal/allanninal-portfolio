#!/usr/bin/env python3
"""Inline SVG flow diagrams for the field-notes guides.

Two shapes cover every guide in these sections, so the geometry is computed rather
than hand-written per page. Hand-authoring 52 SVGs by coordinate is how you end up
with text overflowing a box on one page in fifty and never noticing.

  chain(...)  a left-to-right sequence, optionally with one step that fails and an
              optional curved arrow looping back — the shape of "the problem".
  branch(...) one input fanning out into the outcomes a script sorts it into — the
              shape of "the fix", because every script here classifies rather than
              guesses.

Palette matches the existing /dns/ diagrams exactly: indigo accent, the same greys,
#cf4b3f for the failing path, #4c9a2a for the healthy one.
"""
import html as H

W = 760
INK = "#1e1b3a"
SUB = "#565175"
LINE = "#565175"
ACCENT = "#4f46e5"
ACCENT_BG = "#eef2ff"
BORDER = "#c7c5f0"
BAD = "#cf4b3f"
BAD_BG = "#fbeeec"
GOOD = "#4c9a2a"
GOOD_BG = "#eef7ea"

TONES = {
    "accent": (ACCENT_BG, BORDER),
    "plain": ("#fff", BORDER),
    "bad": (BAD_BG, "#e8bdb6"),
    "good": (GOOD_BG, "#bfdcb1"),
}
ARROW = {"plain": LINE, "bad": BAD, "good": GOOD, "accent": ACCENT}


def set_theme(brand: str) -> None:
    """Retint the diagrams to a section's brand colour.

    The older sections already did this — a WooCommerce diagram is drawn in
    WooCommerce purple, a Magento one in Adobe orange — but this module fixed the
    palette to /dns/ indigo, so every section built through it came out indigo
    whatever its stylesheet said. That is invisible while the sections using it
    happen to be indigo-ish and glaring the moment one is Twilio red.

    Only the neutral and accent tones move. #cf4b3f and #4c9a2a stay put in every
    section because they mean "this is the step that fails" and "this is the one
    that works", and a reader should not have to relearn that per page.

    Module-level because a build is one section per process; a section that never
    calls this keeps the indigo it shipped with.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from make_section_assets import hex_to_hls, hls_to_hex, mix_to_black

    global INK, SUB, LINE, ACCENT, ACCENT_BG, BORDER, TONES, ARROW
    hue, _light, sat = hex_to_hls(brand)
    INK = hls_to_hex(hue, 0.169, sat * 0.30)
    SUB = hls_to_hex(hue, 0.384, sat * 0.14)
    LINE = SUB
    ACCENT = mix_to_black(brand, 0.18)
    ACCENT_BG = hls_to_hex(hue, 0.957, sat * 0.55)
    BORDER = hls_to_hex(hue, 0.855, sat * 0.52)
    TONES = {
        "accent": (ACCENT_BG, BORDER),
        "plain": ("#fff", BORDER),
        "bad": (BAD_BG, "#e8bdb6"),
        "good": (GOOD_BG, "#bfdcb1"),
    }
    ARROW = {"plain": LINE, "bad": BAD, "good": GOOD, "accent": ACCENT}


def esc(t):
    return H.escape(str(t), quote=True)


def _wrap(text, limit):
    """Greedy wrap to at most two lines; the caller keeps labels short anyway."""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if len(cand) <= limit or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines[:2]


def _box(x, y, w, h, title, sub, tone):
    fill, stroke = TONES[tone]
    cx = x + w / 2
    lines = _wrap(title, max(14, int(w / 7.2)))
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}"/>']
    ty = y + (26 if len(lines) == 1 and sub else 22 if len(lines) == 2 else 34)
    for i, ln in enumerate(lines):
        out.append(f'<text x="{cx:.0f}" y="{ty + i * 15}" text-anchor="middle" '
                   f'font-family="sans-serif" font-size="12.5" font-weight="700" '
                   f'fill="{INK}">{esc(ln)}</text>')
    if sub:
        sy = ty + len(lines) * 15 + 2
        for i, ln in enumerate(_wrap(sub, max(18, int(w / 6.0)))):
            out.append(f'<text x="{cx:.0f}" y="{sy + i * 13}" text-anchor="middle" '
                       f'font-family="sans-serif" font-size="11" fill="{SUB}">{esc(ln)}</text>')
    return "".join(out)


def _markers(uid):
    return ("<defs>" + "".join(
        f'<marker id="{uid}-{k}" markerWidth="9" markerHeight="9" refX="7" refY="4.5" '
        f'orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="{c}"/></marker>'
        for k, c in ARROW.items()) + "</defs>")


def _figure(uid, height, aria, body, caption):
    return (f'<figure class="diagram">\n'
            f'<svg viewBox="0 0 {W} {height}" role="img" aria-label="{esc(aria)}">'
            f'{_markers(uid)}{body}</svg>\n'
            f'<figcaption>{esc(caption)}</figcaption>\n</figure>')


def chain(uid, aria, caption, steps, *, fail_at=None, loop=None, height=None):
    """steps: [(title, sub), ...] laid out left to right.

    fail_at: index of the ARROW (0 = between step 0 and 1) that fails; drawn red,
             and the step it points at is toned bad.
    loop:    (from_step, to_step, label) drawn as a curved arrow underneath.
    """
    n = len(steps)
    gap = 46
    bw = (W - 20 - gap * (n - 1)) / n
    bh = 66
    height = height or (216 if loop else 168)
    y = 34 if loop else (height - bh) / 2
    body = []
    for i, (title, sub) in enumerate(steps):
        x = 10 + i * (bw + gap)
        tone = "bad" if (fail_at is not None and i == fail_at + 1) else ("accent" if i == 0 else "plain")
        body.append(_box(x, y, bw, bh, title, sub, tone))
    for i in range(n - 1):
        x1 = 10 + i * (bw + gap) + bw + 3
        x2 = x1 + gap - 9
        tone = "bad" if fail_at == i else "plain"
        body.append(f'<line x1="{x1:.0f}" y1="{y + bh / 2:.0f}" x2="{x2:.0f}" y2="{y + bh / 2:.0f}" '
                    f'stroke="{ARROW[tone]}" stroke-width="2" marker-end="url(#{uid}-{tone})"/>')
    if loop:
        a, b, label = loop
        ax = 10 + a * (bw + gap) + bw / 2
        bx = 10 + b * (bw + gap) + bw / 2
        ly = y + bh + 52
        body.append(f'<path d="M{ax:.0f},{y + bh} C{ax:.0f},{ly} {bx:.0f},{ly} {bx:.0f},{y + bh + 3}" '
                    f'fill="none" stroke="{BAD}" stroke-width="2" marker-end="url(#{uid}-bad)"/>')
        body.append(f'<text x="{(ax + bx) / 2:.0f}" y="{ly + 4}" text-anchor="middle" '
                    f'font-family="sans-serif" font-size="11.5" font-weight="700" '
                    f'fill="{BAD}">{esc(label)}</text>')
    return _figure(uid, height, aria, "".join(body), caption)


def branch(uid, aria, caption, source, outcomes):
    """source: (title, sub). outcomes: [(title, sub, tone), ...] stacked on the right."""
    oh, ogap = 54, 12
    total = len(outcomes) * oh + (len(outcomes) - 1) * ogap
    height = max(170, total + 44)
    sw, sh = 216, 70
    sy = (height - sh) / 2
    ox, ow = 300, W - 300 - 10
    body = [_box(10, sy, sw, sh, source[0], source[1], "accent")]
    top = (height - total) / 2
    for i, (title, sub, tone) in enumerate(outcomes):
        oy = top + i * (oh + ogap)
        body.append(_box(ox, oy, ow, oh, title, sub, tone))
        mid = oy + oh / 2
        body.append(f'<path d="M{10 + sw + 3},{sy + sh / 2:.0f} C{ox - 40},{sy + sh / 2:.0f} '
                    f'{ox - 40},{mid:.0f} {ox - 6},{mid:.0f}" fill="none" '
                    f'stroke="{ARROW[tone if tone in ARROW else "plain"]}" stroke-width="2" '
                    f'marker-end="url(#{uid}-{tone if tone in ARROW else "plain"})"/>')
    return _figure(uid, height, aria, "".join(body), caption)
