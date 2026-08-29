#!/usr/bin/env python3
"""Prove the read-only sections never ship a script that writes.

check_section.py scans the guide dicts, which is the right place to catch a
mistake early. This scans the other end: the files extracted into the public
repo, which is what somebody actually clones and runs against their own live
payments or messaging account. Those are produced by a separate extraction step,
so verifying the source does not verify them.

A printed repair line legitimately contains the word POST — that is the whole
design. An actual request does not, so the patterns match calls rather than
words.

    python3 tools/fieldnotes/audit_readonly.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_repo_links import READ_ONLY, REPO  # noqa: E402

REPOS = Path.home() / "Projects"

REQUEST_PY = re.compile(r'\b(?:requests|session|s|client|http)\.(post|put|patch|delete)\s*\(', re.I)
REQUEST_JS = re.compile(r'method\s*:\s*[\'"](POST|PUT|PATCH|DELETE)', re.I)
CURL_WRITE = re.compile(r'\bcurl\b[^\n]*-X\s*(POST|PUT|PATCH|DELETE)')
APPLY_FLAG = re.compile(r'--apply\b')

CHECKS = (("python write call", REQUEST_PY),
          ("node write call", REQUEST_JS),
          ("curl write", CURL_WRITE),
          ("--apply flag", APPLY_FLAG))


def main() -> int:
    problems = 0
    for section in sorted(READ_ONLY):
        root = REPOS / REPO[section]
        if not root.is_dir():
            print(f"  {section}: no local clone at {root} — skipped")
            continue
        scripts = [p for p in root.rglob("*")
                   if p.suffix in (".py", ".mjs", ".js") and "test" not in p.name]
        bad = []
        for f in scripts:
            text = f.read_text(encoding="utf-8", errors="ignore")
            for label, rx in CHECKS:
                m = rx.search(text)
                if m:
                    bad.append(f"{f.relative_to(root)}  [{label}: {m.group(0)!r}]")
        problems += len(bad)
        print(f"  {section:<8} {len(scripts):3d} published script(s), "
              f"{len(bad)} with a write path")
        for b in bad:
            print(f"      FAIL  {b}")
    print(f"  {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
