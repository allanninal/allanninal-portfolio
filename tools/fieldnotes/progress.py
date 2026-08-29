#!/usr/bin/env python3
"""How much of each researched enumeration is actually published.

A section's research.md lists every problem found for that provider; the section
directory holds the ones written. This prints the gap, and with --remaining lists
what has not been written yet, which is where the next batch comes from.

    python3 tools/fieldnotes/progress.py
    python3 tools/fieldnotes/progress.py stripe --remaining
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

SKIP_HEADINGS = ("Table of contents", "Scope and known")


def enumerated(section: str) -> list[str]:
    f = HERE / section / "research.md"
    if not f.is_file():
        return []
    return [l[3:].strip() for l in f.read_text(encoding="utf-8").splitlines()
            if l.startswith("## ") and not l[3:].startswith(SKIP_HEADINGS)]


def published(section: str) -> set[str]:
    d = ROOT / section
    if not d.is_dir():
        return set()
    return {p.name for p in d.iterdir()
            if p.is_dir() and p.name != "assets" and (p / "index.html").is_file()}


def main(only: str | None, show_remaining: bool) -> int:
    sections = [only] if only else sorted(
        p.name for p in HERE.iterdir() if p.is_dir() and (p / "research.md").is_file())
    for sec in sections:
        all_slugs, live = enumerated(sec), published(sec)
        done = [s for s in all_slugs if s in live]
        left = [s for s in all_slugs if s not in live]
        pct = 100 * len(done) // len(all_slugs) if all_slugs else 0
        bar = "#" * (pct // 4) + "." * (25 - pct // 4)
        print(f"  {sec:<10} [{bar}] {len(done):3d}/{len(all_slugs):<4} {pct:3d}%   "
              f"{len(left)} remaining")
        # Written but not in the enumeration: fine, but worth surfacing.
        extra = sorted(live - set(all_slugs))
        if extra:
            print(f"             (+{len(extra)} published outside the enumeration)")
        if show_remaining:
            for s in left:
                print(f"                {s}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0] if args else None, "--remaining" in sys.argv))
