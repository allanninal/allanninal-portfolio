#!/usr/bin/env python3
"""Check a section's guides before it is built.

The generator only flags title and description length, and `visuals.apply()` only
fails on a missing diagram. Everything else a guide can get wrong — a key left
out, a duplicate slug, a related link that 404s, a script that writes when the
section promises it never will — shows up as a broken published page instead.

    python3 tools/fieldnotes/check_section.py stripe [--run-tests]
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

KEYS = [
    "slug", "title", "description", "h1", "category", "pill", "chips", "keywords",
    "deps", "lead", "short_answer", "problem", "why", "steps", "verify", "code_intro",
    "py_file", "py", "js_file", "js", "test_intro", "test_py_file", "test_py",
    "test_js_file", "test_js", "faq", "related", "citations",
]

# Sections whose scripts hold a live payments or messaging credential and must
# never write. Keep in step with READ_ONLY in add_repo_links.py.
READ_ONLY = {"stripe"}
WRITE_CALLS = re.compile(r'"(POST|PUT|PATCH|DELETE)"|\bmethod:\s*[\'"](POST|PUT|PATCH|DELETE)|--apply')


def load(section: str) -> list[dict]:
    sys.path.insert(0, str(ROOT / "tools" / "fieldnotes" / section))
    guides: list[dict] = []
    for mod in sorted((ROOT / "tools" / "fieldnotes" / section).glob("guides*.py")):
        m = importlib.import_module(mod.stem)
        guides.extend(getattr(m, "GUIDES", []) or getattr(m, "GUIDES2", []))
    return guides


def check(section: str, run_tests: bool) -> int:
    guides = load(section)
    problems: list[str] = []
    seen: set[str] = set()

    for g in guides:
        slug = g.get("slug", "<no slug>")
        for k in KEYS:
            if k not in g:
                problems.append(f"{slug}: missing key {k!r}")
        if slug in seen:
            problems.append(f"{slug}: duplicate slug")
        seen.add(slug)

        if len(g.get("title", "")) > 65:
            problems.append(f"{slug}: title is {len(g['title'])} chars (max 65)")
        if len(g.get("description", "")) > 160:
            problems.append(f"{slug}: description is {len(g['description'])} chars (max 160)")

        if len(g.get("faq", [])) < 3:
            problems.append(f"{slug}: only {len(g.get('faq', []))} FAQ entries")
        if not g.get("citations"):
            problems.append(f"{slug}: no citations")

        # A related link that does not resolve is a 404 shipped to a reader.
        for href, _label in g.get("related", []):
            if href.startswith("/") and not (ROOT / href.strip("/") / "index.html").exists():
                problems.append(f"{slug}: related link {href} does not exist")

        if section in READ_ONLY:
            for field in ("py", "js"):
                hit = WRITE_CALLS.search(g.get(field, ""))
                if hit:
                    problems.append(
                        f"{slug}: {field} contains {hit.group(0)!r} but /{section}/ "
                        f"promises its scripts never write")

        # The repo builder finds the code by these exact filename conventions.
        if not g.get("test_py_file", "").startswith("test_"):
            problems.append(f"{slug}: test_py_file should be test_<name>.py")
        if not g.get("test_js_file", "").endswith(".test.mjs"):
            problems.append(f"{slug}: test_js_file should be <name>.test.mjs")

        if run_tests:
            problems.extend(run_guide_tests(g))

    # Every guide needs diagrams and a photo, or the build raises.
    from visuals import VISUALS, PICKS
    for g in guides:
        key = f"{section}/{g['slug']}"
        if key not in VISUALS:
            problems.append(f"{g['slug']}: no diagrams in any visuals_*.py")
        if key not in PICKS:
            problems.append(f"{g['slug']}: no entry in img_picks.json")
        img = ROOT / section / "assets" / "img" / g["slug"] / "feature.jpg"
        if not img.exists():
            problems.append(f"{g['slug']}: feature.jpg missing at {img.relative_to(ROOT)}")

    print(f"  {section}: {len(guides)} guide(s)")
    for p in problems:
        print(f"    FAIL  {p}")
    print(f"  {len(problems)} problem(s)")
    return 1 if problems else 0


def run_guide_tests(g: dict) -> list[str]:
    """Write the guide's four code blocks to a temp dir and run both suites."""
    out = []
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        for key, name in (("py", "py_file"), ("js", "js_file"),
                          ("test_py", "test_py_file"), ("test_js", "test_js_file")):
            (p / g[name]).write_text(g[key], encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", g["test_py_file"]],
                           cwd=p, capture_output=True, text=True)
        if r.returncode:
            out.append(f"{g['slug']}: pytest failed — {r.stdout.strip().splitlines()[-1:]}")
        r = subprocess.run(["node", "--test"], cwd=p, capture_output=True, text=True)
        if r.returncode:
            tail = [l for l in r.stdout.splitlines() if l.startswith("ℹ fail")]
            out.append(f"{g['slug']}: node --test failed — {tail}")
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(check(args[0], "--run-tests" in sys.argv))
