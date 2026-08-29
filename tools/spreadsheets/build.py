#!/usr/bin/env python3
"""Build /spreadsheets/ — one article per live Excel product, plus the index.

    cd tools/spreadsheets && python3 build.py

Writes straight into ~/Projects/allanninal.dev/spreadsheets/, including
sitemap.xml and llms.txt. Exits non-zero if any title or description is over the
length Google will show, so a truncated title cannot ship quietly.

Order of operations when something changes:
    python3 extract_catalog.py   # prices, URLs, tabs — re-checked against the API
    python3 shots.py             # only if a workbook itself changed
    python3 build.py
"""
import sys
from pathlib import Path

from build_product import build
from products_a import PRODUCTS_A
from products_b import PRODUCTS_B
from products_c import PRODUCTS_C
from guides_a import GUIDES_A
from guides_b import GUIDES_B
from guides_c import GUIDES_C
from guides_d import GUIDES_D
from guides_e import GUIDES_E
from guides_f import GUIDES_F

# The free-kit line is described once, in the repo that builds the workbooks, so the site
# and the zips cannot disagree about what a kit contains or whether it has a Pro edition.
sys.path.insert(0, str(Path.home() / "Projects/gumroad-products/spreadsheets"))
from kits import KITS as FREE_KITS

GUIDES = PRODUCTS_A + PRODUCTS_B + PRODUCTS_C
# Guide articles: no product behind them, so they are kept in a separate list and
# rendered by build_guide. See that module for why it is not a flag on the product page.
ARTICLES = GUIDES_A + GUIDES_B + GUIDES_C + GUIDES_D + GUIDES_E + GUIDES_F

# Attach the problem/fix diagrams. Kept out of the guide dicts so the prose and the
# pictures can be edited without stepping on each other, and so a guide with no diagram
# yet is a visible gap rather than a silent one.
from guide_visuals import V as _V
_missing = [a["slug"] for a in ARTICLES if a["slug"] not in _V]
if _missing:
    raise SystemExit(f"no diagrams for: {', '.join(_missing)} — see guide_visuals.py")
for _a in ARTICLES:
    _a["diagram_problem"] = _V[_a["slug"]]["problem"]
    _a["diagram_fix"] = _V[_a["slug"]]["fix"]

CFG = {
    "date": "2026-08-29",

    "index_title": "Spreadsheets That Do the Hard Part — Excel & Google Sheets",
    "index_desc": "Working Excel and Google Sheets workbooks for jobs where the arithmetic is "
                  "easy to get wrong: WIP schedules, bid pricing, landed cost, SPC and more.",
    "index_h1": "spreadsheets that do the part everyone gets wrong",
    "index_lead": "Every one of these exists because there is a rule in the middle of it that a "
                  "free template does not know about &mdash; a loss that has to be taken all at "
                  "once, a yield that changes the cost of everything, a fringe credit divided by "
                  "the wrong number. They are ordinary <code>.xlsx</code> files: no macros, no "
                  "add-ins, and they open in Excel, Google Sheets, Numbers and LibreOffice.",
    "index_chips": ["Excel + Google Sheets", "No macros, no add-ins",
                    "One-off price", "Free lifetime updates"],

    "scope_title": "How these are built, and what that is worth to you",
    "scope_body": """<p>Every workbook here has a checker sitting next to it that reimplements its
    maths from scratch in Python, recalculates the real file in LibreOffice, and compares the two.
    Where a product rests on an identity that must hold &mdash; a schedule that ties to the income
    statement, a break-even that has to balance to zero &mdash; the checker asserts that too.</p>
    <p>Each page below tells you what the workbook does in plain language first, then shows the
    arithmetic and the checker's last result, so you can decide whether I have actually understood
    the problem before you spend anything.</p>""",

    "group_order": ["Construction and contracting", "Manufacturing and quality",
                    "Property and deal analysis", "Food and hospitality",
                    "Importing and pricing", "Grants and compliance"],
    "group_blurb": {
        "Construction and contracting":
            "Estimate the job, bill it, earn it, collect it, and know what the equipment costs. "
            "Five stages of the same money.",
        "Manufacturing and quality":
            "The statistics that keep a customer audit happy, without a licence that costs more "
            "than the machine.",
        "Property and deal analysis":
            "Ten-year proformas with real amortisation, levered and unlevered IRR and a "
            "sensitivity grid — for the asset classes nobody writes models for.",
        "Food and hospitality":
            "Cost the plate properly, then find out which dishes are actually paying for the "
            "kitchen.",
        "Importing and pricing":
            "What a shipment truly costs once duty, freight and fees land on it — and what you "
            "have to charge as a result.",
        "Grants and compliance":
            "Budgets that have to survive somebody else checking them.",
    },

    # Guide groups, rendered after the products on the index. Ordered by measured demand:
    # the data-integrity cluster is the largest by a wide margin (see RESEARCH-EXCEL-PAINS.md
    # in the gumroad-products repo), so it leads.
    "guide_group_order": ["When Excel changes your data",
                          "Formulas that do not behave as they read",
                          "Cleaning a real export",
                          "Power Query — clean it once, not every month",
                          "One formula, many answers",
                          "Text work that used to need a macro",
                          "Formatting that follows a rule",
                          "Lookups past the basics",
                          "When the file goes wrong"],
    "guide_group_blurb": {
        "When Excel changes your data":
            "The faults that happen on open or on paste, before you type anything — and "
            "which of them can still be undone.",
        "Formulas that do not behave as they read":
            "Formulas that are doing exactly what they were told, which is not what you "
            "meant. Each one explained once, properly.",
        "Cleaning a real export":
            "One export, start to finish: which column to fix first, and the fault that is "
            "characteristic of that file.",
        "Power Query — clean it once, not every month":
            "The sequel to all of the above. Power Query records the cleaning as steps and "
            "replays them on next month's file, so the work stops being manual.",
        "One formula, many answers":
            "Modern Excel lets one formula fill a whole column and resize itself. What that "
            "changes, and the errors it introduces.",
        "Text work that used to need a macro":
            "Pulling a code out of messy text needed VBA for twenty years. It does not any "
            "more, and almost all the advice online still says it does.",
        "Formatting that follows a rule":
            "Where advanced actually begins for most people: the moment a colour is decided "
            "by a formula rather than a preset.",
        "Lookups past the basics":
            "The last match rather than the first, the end of a growing column, and the "
            "references that are awkward to build.",
        "When the file goes wrong":
            "Getting unsaved work back, and removing the link to a file you deleted years "
            "ago that Excel still asks about.",
    },
    "kit_groups": [
        {"title": "Free workbooks you can download now",
         "blurb": "Twelve finished workbooks, free and hosted here rather than behind a "
                  "checkout. Each one exists because it contains a calculation that free "
                  "templates normally get wrong.",
         "kits": FREE_KITS},
    ],

    "soon": {
        "group": "In development",
        "blurb": "Not finished, so not for sale. Listed because the free workbook's read-me "
                 "mentions it, and a promise made in a download should be visible here too.",
        "title": "Data Reconciliation Workbook (Pro)",
        "body": "The free workbook cleans one column. The Pro edition is for reconciling two "
                "lists that should agree and do not: fuzzy matching for names and addresses, "
                "many-to-one matching with a running variance, an audit column recording what "
                "changed, and no row limit.",
    },
}


if __name__ == "__main__":
    print(f"building /spreadsheets/ — {len(GUIDES)} products, {len(ARTICLES)} guides")
    fails = build(CFG, GUIDES, ARTICLES)
    if fails:
        print(f"\n{fails} page(s) FAILED the title/description length check")
    sys.exit(1 if fails else 0)
