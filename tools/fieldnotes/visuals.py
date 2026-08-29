#!/usr/bin/env python3
"""Merge the per-guide visuals into the guide dicts before the section is built.

Kept separate from the guides themselves so a diagram edit never risks touching the
prose, and so the guides files stay readable as writing rather than as markup.
"""
import json
from pathlib import Path

import importlib

# Discovered rather than listed. A section is now written in batches, and each
# batch brings its own visuals_<section>_<letter>.py; hand-maintaining the import
# list meant a batch could be written, pass its own tests, and then fail the build
# with "no visuals for ..." purely because one line here was forgotten.
#
# Sorted so the order is stable. Each themed module sets its brand at the top and
# calls reset_theme() at the bottom, so importing them in any order is safe.
VISUALS = {}
for _mod in sorted(p.stem for p in Path(__file__).resolve().parent.glob("visuals_*.py")):
    VISUALS.update(importlib.import_module(_mod).V)
PICKS = json.loads((Path(__file__).resolve().parent / "img_picks.json").read_text())


def apply(section: str, guides: list) -> list:
    """Attach the feature image and both diagrams to every guide in a section.

    Raises if a guide has no visuals rather than quietly building a page that looks
    like the older sections everywhere except the one place someone will notice.
    """
    for g in guides:
        key = f"{section}/{g['slug']}"
        if key not in VISUALS or key not in PICKS:
            raise KeyError(f"no visuals for {key}")
        g.update(VISUALS[key])
        g["feature"] = PICKS[key]
    return guides
