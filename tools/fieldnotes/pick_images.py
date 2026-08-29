#!/usr/bin/env python3
"""Give every guide in a section a feature photo, reusing ones already licensed.

The rule from tools/fieldnotes/README.md is that a credit is copied verbatim from
the page the photo already appears on, never re-derived — a wrong attribution is
worse than no photo. So this only ever reuses an existing entry from
img_picks.json, carrying its photographer and profile across unchanged, and
copies the actual JPEG into place.

Assignment is round-robin over the pool, skipping photos already used elsewhere in
the same section, so a section does not open with the same image four times.

    python3 tools/fieldnotes/pick_images.py stripe [--apply]
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PICKS = HERE / "img_picks.json"


def guides_for(section: str) -> list[str]:
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE / section))
    slugs = []
    for mod in sorted((HERE / section).glob("guides*.py")):
        m = importlib.import_module(mod.stem)
        slugs += [g["slug"] for g in getattr(m, "GUIDES", [])]
    return slugs


def main(section: str, apply: bool) -> int:
    picks = json.loads(PICKS.read_text(encoding="utf-8"))

    # One entry per distinct source photo, so the same image is not offered twice.
    pool, seen_src = [], set()
    for entry in picks.values():
        if entry["src"] not in seen_src and (ROOT / entry["src"]).is_file():
            seen_src.add(entry["src"])
            pool.append(entry)
    used_here = {v["src"] for k, v in picks.items() if k.startswith(f"{section}/")}

    added = 0
    for slug in guides_for(section):
        key = f"{section}/{slug}"
        if key in picks:
            continue
        choice = next((e for e in pool if e["src"] not in used_here), None)
        if choice is None:          # pool exhausted; start reusing
            choice = pool[added % len(pool)]
        used_here.add(choice["src"])
        picks[key] = dict(choice)
        dest = ROOT / section / "assets" / "img" / slug / "feature.jpg"
        print(f"  {slug:<44} <- {choice['src']}")
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / choice["src"], dest)
        added += 1

    if apply and added:
        PICKS.write_text(json.dumps(picks, indent=1, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    print(f"  {added} photo(s) assigned, {len(pool)} in the pool")
    print("APPLIED" if apply else "DRY RUN — pass --apply to write")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0], "--apply" in sys.argv))
