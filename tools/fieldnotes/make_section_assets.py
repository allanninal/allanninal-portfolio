#!/usr/bin/env python3
"""Write a field-notes section's stylesheet and script from one brand colour.

Until now these were byte-for-byte copies: all six of the newest sections ship the
identical 14,581-byte stylesheet (md5 0416163119…) differing only in the 24-line
`:root` palette, and `seo/assets/seo.js` still opens with a comment about
WooCommerce because the copy was never edited. Copying it again for each new API
section would keep multiplying that.

So the body is read from an existing section — it stays the single shared
stylesheet, and edits to it still propagate by re-running this — and only the
palette is generated, derived from the provider's own brand hex the way
/woocommerce/ is built around #7f54b3 and /magento/ around #f26322.

    python3 tools/fieldnotes/make_section_assets.py stripe --brand '#635BFF'
"""

from __future__ import annotations

import argparse
import colorsys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dns" / "assets"          # the reference copy of the shared theme

# Each palette token as (name, saturation multiplier, target lightness). The
# multipliers and lightnesses are read off the existing sections: every one of them
# is the same ramp around a different hue, so reproducing the ramp reproduces the
# look without hand-picking fourteen hexes per provider.
RAMP = [
    ("--woo-purple",        1.00, None),   # the brand colour itself, untouched
    ("--woo-purple-deep",   None, "mix:0.18"),
    ("--woo-purple-dark",   None, "mix:0.38"),
    ("--woo-purple-tint",   0.55, 0.957),
    ("--woo-ink",           0.30, 0.169),
    ("--woo-ink-soft",      0.14, 0.384),
    ("--woo-ink-faint",     0.12, 0.555),
    ("--woo-paper",         None, None),   # always #ffffff
    ("--woo-surface",       0.45, 0.980),
    ("--woo-surface-2",     0.55, 0.957),  # same as the tint, as in every section
    ("--woo-border",        0.50, 0.912),
    ("--woo-border-strong", 0.52, 0.855),
    ("--woo-code-bg",       0.42, 0.165),
    ("--woo-code-bar",      0.46, 0.137),
]

# Status colours carry meaning rather than brand, so they are identical everywhere.
FIXED = """  --woo-green: #4c9a2a;
  --woo-green-tint: #eef6e8;
  --woo-red: #cf4b3f;
  --woo-red-tint: #fbeeec;
  --woo-amber: #b9791a;
  --woo-amber-tint: #fbf3e3;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", Menlo, Consolas, monospace;
  --wrap: 46rem;
  --radius: 12px;"""


def hex_to_hls(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def hls_to_hex(hue: float, light: float, sat: float) -> str:
    r, g, b = colorsys.hls_to_rgb(hue, max(0.0, min(1.0, light)), max(0.0, min(1.0, sat)))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def relative_luminance(h: str) -> float:
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def report_contrast(brand: str) -> None:
    """Flag a brand colour that cannot carry the roles the stylesheet gives it.

    Two ratios matter, and they are not the obvious one. Body links are
    `--woo-purple-deep` on white, so that is the 4.5:1 test. `--woo-purple` is
    only ever a solid fill behind white text (`.step__n`), which is large and
    bold, so 3:1 applies there. Printing both keeps a brand like Twilio's red
    from failing quietly the way Magento's orange already does.
    """
    deep = mix_to_black(brand, 0.18)
    link = contrast(deep, "#ffffff")
    fill = contrast("#ffffff", brand)
    print(f"    link {deep} on white  {link:.2f}:1  {'AA' if link >= 4.5 else 'BELOW AA — links will be hard to read'}")
    print(f"    white on {brand.lower()}  {fill:.2f}:1  "
          f"{'AA' if fill >= 4.5 else 'large text only' if fill >= 3 else 'BELOW AA-large — do not use as a fill'}")


def mix_to_black(h: str, amount: float) -> str:
    h = h.lstrip("#")
    rgb = [int(h[i:i + 2], 16) * (1 - amount) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(c) for c in rgb)


def palette(brand: str) -> str:
    hue, light, sat = hex_to_hls(brand)
    lines = []
    for name, sat_mul, target in RAMP:
        if isinstance(target, str) and target.startswith("mix:"):
            # Darken by mixing toward black in RGB, not by dropping lightness in
            # HLS. At constant saturation a vivid brand like Stripe's #635BFF gets
            # *more* vivid as it darkens — #635bff became #2d22ff, brighter than
            # the colour it was supposed to deepen. Mixing dims it as expected, and
            # reproduces the existing sections closely (#7f54b3 -> #684593 against
            # the shipped #674399).
            value = mix_to_black(brand, float(target.split(":")[1]))
        elif sat_mul is None:
            value = "#ffffff"
        elif target is None:
            value = brand.lower()
        else:
            value = hls_to_hex(hue, target, sat * sat_mul)
        lines.append(f"  {name}: {value};")
    return "\n".join(lines)


def build(section: str, brand: str, label: str, apply: bool) -> None:
    css = (SOURCE / "dns.css").read_text(encoding="utf-8")
    js = (SOURCE / "dns.js").read_text(encoding="utf-8")

    root = re.search(r":root \{\n.*?\n\}", css, re.S)
    if not root:
        raise SystemExit("could not find the :root block in dns.css")
    new_root = ":root {\n" + palette(brand) + "\n" + FIXED + "\n}"
    css = css[: root.start()] + new_root + css[root.end():]
    css = re.sub(r"\A/\*.*?\*/", f"/* {label} field notes theme */", css, count=1, flags=re.S)

    # The shared script is genuinely section-agnostic; only its stale header lied.
    js = re.sub(r"\A/\*.*?\*/",
                "/* Field notes — code tabs, copy, and a small syntax highlighter.\n"
                "   No external dependencies so the pages stay self contained and fast. */",
                js, count=1, flags=re.S)

    out = ROOT / section / "assets"
    print(f"  {section:<10} brand={brand}  css={len(css):,}b  js={len(js):,}b  -> {out}")
    print(palette(brand))
    report_contrast(brand)
    if not apply:
        return
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{section}.css").write_text(css, encoding="utf-8")
    (out / f"{section}.js").write_text(js, encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("section")
    ap.add_argument("--brand", required=True, help="the provider's brand hex, e.g. '#635BFF'")
    ap.add_argument("--label", required=True, help="human name, for the stylesheet comment")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    build(a.section, a.brand, a.label, a.apply)
    print("APPLIED" if a.apply else "DRY RUN — pass --apply to write")
