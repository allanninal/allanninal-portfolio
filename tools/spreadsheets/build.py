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

from build_product import build
from products_a import PRODUCTS_A
from products_b import PRODUCTS_B
from products_c import PRODUCTS_C
from guides_a import GUIDES_A
from guides_b import GUIDES_B
from guides_c import GUIDES_C

GUIDES = PRODUCTS_A + PRODUCTS_B + PRODUCTS_C
# Guide articles: no product behind them, so they are kept in a separate list and
# rendered by build_guide. See that module for why it is not a flag on the product page.
ARTICLES = GUIDES_A + GUIDES_B + GUIDES_C

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
                          "Cleaning a real export"],
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
    },
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
