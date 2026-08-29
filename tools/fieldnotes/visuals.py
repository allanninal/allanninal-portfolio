#!/usr/bin/env python3
"""Merge the per-guide visuals into the guide dicts before the section is built.

Kept separate from the guides themselves so a diagram edit never risks touching the
prose, and so the guides files stay readable as writing rather than as markup.
"""
import json
from pathlib import Path

from visuals_cf_seo import V as _CF_SEO
from visuals_ci_aws import V as _CI_AWS
from visuals_email import V as _EMAIL
from visuals_stripe import V as _STRIPE

VISUALS = {**_CF_SEO, **_CI_AWS, **_EMAIL, **_STRIPE}
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
