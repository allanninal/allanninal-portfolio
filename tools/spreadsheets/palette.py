#!/usr/bin/env python3
"""Re-skin the shared diagram engine in Excel/Sheets green.

diagrams.py is imported unchanged and shared with the field-notes sections, so
its geometry stays in exactly one place. But its palette is baked in as module
constants in indigo, and indigo diagrams on green pages look like a mistake.

Importing this module rebinds those constants and rebuilds the two lookup
tables that were derived from them at import time. Import it BEFORE calling
chain() or branch() — importing diagrams alone gives you the indigo original.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fieldnotes"))

import diagrams as D  # noqa: E402

EXCEL = "#217346"        # Microsoft Excel green
EXCEL_TINT = "#e6f4ec"
SHEETS = "#0f9d58"       # Google Sheets green
SHEETS_TINT = "#e6f6ee"
RED = "#c5221f"          # Google red — the expensive mistake
RED_TINT = "#fceceb"
INK = "#14261d"
SUB = "#476455"
BORDER = "#a5cfb9"

D.INK = INK
D.SUB = SUB
D.LINE = SUB
D.ACCENT = EXCEL
D.ACCENT_BG = EXCEL_TINT
D.BORDER = BORDER
D.BAD = RED
D.BAD_BG = RED_TINT
D.GOOD = SHEETS
D.GOOD_BG = SHEETS_TINT

# TONES and ARROW were built from the old constants when diagrams was imported,
# so rebinding the names above is not enough on its own.
D.TONES = {
    "accent": (EXCEL_TINT, BORDER),
    "plain": ("#fff", BORDER),
    "bad": (RED_TINT, "#eab9b7"),
    "good": (SHEETS_TINT, "#a9dcc2"),
}
D.ARROW = {"plain": SUB, "bad": RED, "good": SHEETS, "accent": EXCEL}

chain = D.chain
branch = D.branch
