"""The five diagram layouts the /build series use, built on svgkit.Canvas."""
from .svgkit import Canvas, figure, LINE, SUB, TEXT, FAINT, CAT, category_of

W = 940


def _wrap(s, n):
    out, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > n:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


# --------------------------------------------------------------------------
def system(outside, inside, note=None, account="AWS account", edges=None):
    """Part 1: a row of things outside the account feeding a row inside it."""
    n_out, n_in = len(outside), len(inside)
    gap = 26
    ow = min(230, (W - 60 - gap * (n_out - 1)) / n_out)
    iw = min(230, (W - 100 - gap * (n_in - 1)) / n_in)
    oh, ih = 88, 104
    top = 22
    cont_y = 214
    in_y = 268
    h = in_y + ih + (78 if note else 40)

    c = Canvas(W, h)
    ox0 = (W - (ow * n_out + gap * (n_out - 1))) / 2
    ix0 = (W - (iw * n_in + gap * (n_in - 1))) / 2

    c.container(24, cont_y, W - 48, h - cont_y - 20, account)

    ocx, icx = [], []
    for i, o in enumerate(outside):
        x = ox0 + i * (ow + gap)
        c.node(x, top, ow, oh, o["title"], o.get("sub", ()), o.get("icon"), "external")
        ocx.append(x + ow / 2)
    for i, o in enumerate(inside):
        x = ix0 + i * (iw + gap)
        c.node(x, in_y, iw, ih, o["title"], o.get("sub", ()), o.get("icon"))
        icx.append(x + iw / 2)

    for e in (edges or []):
        a, b, label, up = e["from"], e["to"], e.get("label", ""), e.get("up", False)
        x1 = ocx[a] if not up else icx[a]
        x2 = icx[b] if not up else ocx[b]
        if up:
            c.line(x1, in_y, x2, top + oh + 4)
        else:
            c.line(x1, top + oh, x2, in_y - 4)
        if label:
            for j, ln in enumerate(_wrap(label, 18)):
                c.text(max(x1, x2) + 9, (top + oh + in_y) / 2 - 6 + j * 15, ln,
                       size=11.5, fill=SUB, weight=400, anchor="start")

    for i in range(n_in - 1):
        x1 = ix0 + i * (iw + gap) + iw
        c.line(x1 + 3, in_y + ih / 2, x1 + gap - 3, in_y + ih / 2)

    if note:
        c.note(h - 24, note)
    return c


# --------------------------------------------------------------------------
def chain(steps, note=None, account="AWS account", entry=None):
    """A vertical run of steps; each may take a side input and drop a side exit."""
    bh, vgap = 66, 32
    has_side = any(s.get("side") for s in steps)
    has_exit = any(s.get("exit") for s in steps)
    ew = 170 if has_exit else 0
    sw = 196 if has_side else 0
    x = 206 if entry else 40
    bw = W - x - 24 - (sw + 44 if has_side else 0) - (ew + 40 if has_exit else 0)
    bw = max(210, min(bw, 300))

    y0 = 78
    n = len(steps)
    h = y0 + n * bh + (n - 1) * vgap + 34 + (34 if note else 0)

    c = Canvas(W, h)
    cont_x = x - 22
    c.container(cont_x, y0 - 38, W - cont_x - 16, n * bh + (n - 1) * vgap + 56, account)

    if entry:
        c.node(12, y0 + 4, 152, bh, entry["title"], entry.get("sub", ()),
               entry.get("icon"), "external")
        c.line(168, y0 + 4 + bh / 2, x - 6, y0 + bh / 2)

    for i, s in enumerate(steps):
        y = y0 + i * (bh + vgap)
        c.node(x, y, bw, bh, s["title"], s.get("sub", ()), s.get("icon"))
        if i:
            c.line(x + bw / 2, y - vgap + 3, x + bw / 2, y - 5)
        right = x + bw
        side = s.get("side")
        if side:
            sx = x + bw + 44
            c.node(sx, y, sw, bh, side["title"], side.get("sub", ()), side.get("icon"))
            c.line(sx - 5, y + bh / 2, x + bw + 5, y + bh / 2)
            right = sx + sw
        out = s.get("exit")
        if out:
            ex = W - ew - 16
            c.node(ex, y, ew, bh, out["title"], out.get("sub", ()), out.get("icon", "stop"))
            c.line(right + 5, y + bh / 2, ex - 5, y + bh / 2)
            if out.get("label"):
                c.text((right + ex) / 2, y + bh / 2 - 10, out["label"], size=11,
                       fill=SUB, weight=700)
    if note:
        c.note(h - 12, note)
    return c


# --------------------------------------------------------------------------
def lanes(routes, target, note=None, title_label="Three ways in"):
    """Parallel routes converging on one component."""
    lw, lh, vgap = 316, 70, 26
    n = len(routes)
    y0 = 34
    tw, th, tx = 300, 92, 596
    span = n * (lh + vgap) - vgap
    ty = y0 + span / 2 - th / 2
    bottom = max(y0 + span, ty + th + (110 if target.get("then") else 0))
    h = bottom + (52 if note else 22)
    c = Canvas(W, h)
    for i, r in enumerate(routes):
        y = y0 + i * (lh + vgap)
        c.node(30, y, lw, lh, r["title"], r.get("sub", ()), r.get("icon"), "external")
        aim = ty + th * (i + 1) / (n + 1)
        c.elbow(30 + lw + 5, y + lh / 2, tx - 6, aim)
        if r.get("label"):
            c.text(30 + lw + 22, y + lh / 2 - 10, r["label"], size=11, fill=SUB,
                   weight=700, anchor="start")

    c.node(tx, ty, tw, th, target["title"], target.get("sub", ()), target.get("icon"))
    if target.get("then"):
        c.line(tx + tw / 2, ty + th + 3, tx + tw / 2, ty + th + 36)
        c.node(tx, ty + th + 40, tw, 70, target["then"]["title"],
               target["then"].get("sub", ()), target["then"].get("icon"))
    if note:
        c.note(h - 18, note)
    return c


# --------------------------------------------------------------------------
def _nice(v):
    """Round an axis maximum up to something a reader can hold in their head."""
    import math
    if v <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(v))
    for step in (1, 2, 2.5, 5, 10):
        if v <= step * mag:
            return step * mag
    return 10 * mag


def bars(tiers, series, note=None, unit="$"):
    """Stacked cost bars, one per volume tier, coloured by AWS service.

    `series` is [(key, label, colour)]; every tier's parts are [(key, value)],
    so the bar and its legend swatch can never drift apart.
    """
    plot_h, plot_top, left = 244, 40, 108
    n = len(tiers)
    bw, bgap = 104, 96
    total_w = n * bw + (n - 1) * bgap
    x0 = left + (W - left - 48 - total_w) / 2
    peak = max(sum(v for _, v in t["parts"]) for t in tiers)
    ticks = 4
    step = _nice(peak * 1.18 / ticks)
    ymax = step * ticks
    base = plot_top + plot_h
    rows = (len(series) + 1) // 2
    h = base + 62 + rows * 26 + (30 if note else 6)
    c = Canvas(W, h)

    for i in range(ticks + 1):
        v = step * i
        y = base - plot_h * i / ticks
        c.line(left - 8, y, W - 48, y, colour="#243547", sw=1, arrow=False)
        lbl = f"{unit}{v:g}" if v < 10 else f"{unit}{v:.0f}"
        c.text(left - 16, y + 4, lbl, size=11, fill=FAINT, weight=400, anchor="end")
    c.line(left - 8, base, W - 48, base, colour=LINE, sw=1.6, arrow=False)

    colours = {k: col for k, _, col in series}
    for i, t in enumerate(tiers):
        x = x0 + i * (bw + bgap)
        acc = 0.0
        for key, v in t["parts"]:
            hh = plot_h * v / ymax
            c.body.append(
                f'<rect x="{x:.0f}" y="{base - acc - hh:.1f}" width="{bw}" height="{hh:.1f}" '
                f'fill="{colours.get(key, "#7D8CA3")}" stroke="#16212f" stroke-width="1"/>')
            acc += hh
        total = sum(v for _, v in t["parts"])
        c.text(x + bw / 2, base - acc - 13, f"~{unit}{total:g}", size=14, fill=TEXT, weight=700)
        c.text(x + bw / 2, base + 25, t["label"], size=12.5, fill=TEXT, weight=600)

    ly = base + 62
    for i, (_k, label, col) in enumerate(series):
        cx = 108 + (i % 2) * 400
        cy = ly + (i // 2) * 26
        c.body.append(f'<rect x="{cx}" y="{cy - 11}" width="14" height="14" rx="3" fill="{col}"/>')
        c.text(cx + 22, cy, label, size=11.5, fill=SUB, weight=400, anchor="start")
    if note:
        c.note(h - 12, note)
    return c


# --------------------------------------------------------------------------
def strip(stages, note=None, title=None):
    """A horizontal at-a-glance run of stages -- the 'whole thing in one line'."""
    n = len(stages)
    gap = 22
    bw = min(200, (W - 60 - gap * (n - 1)) / n)
    bh = 96
    y = 46 if title else 30
    h = y + bh + (58 if note else 26)
    c = Canvas(W, h)
    x0 = (W - (bw * n + gap * (n - 1))) / 2
    if title:
        c.text(W / 2, 24, title, size=12, fill=FAINT, weight=700)
    for i, s in enumerate(stages):
        x = x0 + i * (bw + gap)
        c.node(x, y, bw, bh, s["title"], s.get("sub", ()), s.get("icon"))
        if i:
            c.line(x - gap + 3, y + bh / 2, x - 4, y + bh / 2)
    if note:
        c.note(h - 20, note)
    return c
