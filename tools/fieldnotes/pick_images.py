#!/usr/bin/env python3
"""Give every guide in a section a feature photo, reusing ones already licensed.

The rule from tools/fieldnotes/README.md is that a credit is copied verbatim
from the page the photo already appears on, never re-derived — a wrong
attribution is worse than no photo. So the pool is harvested straight out of the
published pages: the <figure class="feature-img"> block on every note carries the
image, its alt text, the photographer and their profile link, and all four are
carried across unchanged.

It used to read the pool from img_picks.json, which held 26 entries — the ones
the newest sections happened to use. The site actually has 739 credited photos,
so a section of forty notes was repeating images fifteen times over for no
reason.

Photos are deduplicated by file content, because the same photograph appears
under several slugs across the older sections.

    python3 tools/fieldnotes/pick_images.py stripe --apply
    python3 tools/fieldnotes/pick_images.py stripe --apply --reassign
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PICKS = HERE / "img_picks.json"

FIGURE = re.compile(
    r'<figure class="feature-img">\s*<img src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>\s*'
    r'<figcaption>Photo by <a href="([^"]+)"[^>]*>([^<]+)</a>', re.S)

SKIP_SECTIONS = {"templates", "build", "redesign", "blog", "projects", "_astro",
                 "assets", "images", "data", "tools", "spreadsheets"}


def harvest(exclude_section: str) -> list[dict]:
    """Every credited photo already published, one entry per distinct image."""
    pool, by_hash = [], set()
    for page in sorted(ROOT.glob("*/[a-z0-9-]*/index.html")):
        section = page.relative_to(ROOT).parts[0]
        if section in SKIP_SECTIONS or section == exclude_section:
            continue
        m = FIGURE.search(page.read_text(encoding="utf-8", errors="ignore"))
        if not m:
            continue
        src, alt, profile, who = m.groups()
        f = ROOT / src.lstrip("/")
        if not f.is_file():
            continue
        digest = hashlib.md5(f.read_bytes()).hexdigest()
        if digest in by_hash:
            continue
        by_hash.add(digest)
        # utm parameters are appended by the template; store the bare profile.
        pool.append({"src": src.lstrip("/"), "alt": alt,
                     "photographer": who, "profile": profile.split("&utm")[0]})
    return pool


def guides_for(section: str) -> list[str]:
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE / section))
    slugs = []
    for mod in sorted((HERE / section).glob("guides*.py")):
        slugs += [g["slug"] for g in importlib.import_module(mod.stem).GUIDES]
    return slugs


def main(section: str, apply: bool, reassign: bool) -> int:
    picks = json.loads(PICKS.read_text(encoding="utf-8"))
    pool = harvest(section)
    slugs = guides_for(section)

    if reassign:
        for s in slugs:
            picks.pop(f"{section}/{s}", None)

    taken = {picks[k]["src"] for k in picks if k.startswith(f"{section}/")}
    i = 0
    added = 0
    for slug in slugs:
        key = f"{section}/{slug}"
        if key in picks:
            continue
        while i < len(pool) and pool[i]["src"] in taken:
            i += 1
        if i >= len(pool):
            print(f"  ! pool exhausted at {slug}")
            break
        choice = pool[i]
        i += 1
        taken.add(choice["src"])
        picks[key] = dict(choice)
        if apply:
            dest = ROOT / section / "assets" / "img" / slug / "feature.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / choice["src"], dest)
        added += 1

    if apply and added:
        PICKS.write_text(json.dumps(picks, indent=1, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    distinct = len({picks[k]["src"] for k in picks if k.startswith(f"{section}/")})
    print(f"  {section}: {added} assigned, {distinct} distinct photo(s) across "
          f"{len(slugs)} note(s), pool of {len(pool)}")
    print("APPLIED" if apply else "DRY RUN — pass --apply to write")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0], "--apply" in sys.argv, "--reassign" in sys.argv))
