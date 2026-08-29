#!/usr/bin/env python3
"""Regenerate the Field notes block in llms.txt, and the counts around it.

llms.txt is the file an assistant reads to describe this site, so a stale one
gets the site described wrongly at scale. It was listing five of the sixteen
field-note sections and calling the template project "73 live" when 366 are
published, because every one of those numbers was typed by hand once.

Everything here is counted off the deployed tree, the same rule the homepage
follows.

    python3 tools/fieldnotes/update_llms.py --apply
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "nav"))
import header as NAV  # noqa: E402

SITE = "https://www.allanninal.dev"


def notes_in(section: str) -> int:
    d = ROOT / section
    return len([p for p in d.iterdir()
                if p.is_dir() and p.name not in ("assets", "downloads")
                and (p / "index.html").is_file()]) if d.is_dir() else 0


def main(apply: bool) -> int:
    text = (ROOT / "llms.txt").read_text(encoding="utf-8")

    groups = [("Commerce platforms", NAV.COMMERCE),
              ("Platform and infrastructure", NAV.PLATFORM),
              ("APIs", NAV.APIS)]
    total = sum(notes_in(h.strip("/")) for _, g in groups for h, _ in g)

    lines = [
        "## Field notes — fix guides with a script that runs",
        "",
        f"- {total} researched guides across {sum(len(g) for _, g in groups)} platforms. "
        "Each one takes a single real problem, explains the mechanism with diagrams, "
        "and gives you a script in both Python and Node.js with tests and a companion "
        "open-source repo. The platform scripts repair what they find and start in a "
        "dry run; the API scripts are read-only and print the repair for you to run, "
        "because they hold a credential to a live account.",
        "",
    ]
    for label, group in groups:
        items = ", ".join(
            f"[{name.replace('&amp;', 'and')}]({SITE}{href}) ({notes_in(href.strip('/'))})"
            for href, name in group)
        lines.append(f"- {label}: {items}")
    block = "\n".join(lines) + "\n"

    start = text.index("## Field notes")
    end = text.index("## Products", start)
    text = text[:start] + block + "\n" + text[end:]

    # Counts in the summary paragraph and the templates entry.
    templates = notes_in("templates")
    build = notes_in("build")
    text = re.sub(r"\b\d+ AWS automation blueprints", f"{build} AWS automation blueprints", text)
    text = re.sub(r"\(365 planned, \d+ live\)", f"(365 planned, {templates} live)", text)
    text = re.sub(r"\b\d+ also have a paid Pro edition", "Some also have a paid Pro edition", text)

    print(f"  field notes: {total} across {sum(len(g) for _, g in groups)} platforms")
    print(f"  templates: {templates} live   build blueprints: {build}")
    if apply:
        (ROOT / "llms.txt").write_text(text, encoding="utf-8")
    print("APPLIED" if apply else "DRY RUN — pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
