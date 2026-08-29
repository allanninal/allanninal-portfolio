#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch M.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Stripe indigo.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#635BFF"
D.set_theme(BRAND)

V = {}

V["stripe/metered-items-with-no-usage-reported"] = {
    "flow_intro": (
        "The script asks the meter what it aggregated for that customer this "
        "period, because the emitter's own logs cannot tell you whether Stripe "
        "counted an event or quietly dropped it."
    ),
    "diagram_problem": D.chain(
        "smnu-p",
        "Metered usage dropped by a meter because the event name never matched",
        "Every request succeeds. The meter ignores what it does not recognise, "
        "and ignoring is not an error.",
        [
            ("Emitter posts usage", "2xx on every call"),
            ("Meter compares", "event_name and payload keys"),
            ("No match", "event dropped silently"),
            ("Meter aggregates 0", "nothing to bill"),
            ("Invoice finalizes", "backfill impossible"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "smnu-f",
        "Sorting metered items by what the meter actually aggregated",
        "No summary rows and rows that all read zero look identical on the "
        "invoice and have different repairs.",
        ("GET event_summaries", "per customer, per period"),
        [
            ("Usage aggregated", "reporting, leave it", "good"),
            ("Period hours old", "too early to judge", "plain"),
            ("No summary rows", "check event_name first", "bad"),
            ("Rows all zero", "check the value payload key", "bad"),
            ("Cycles billed at 0", "revenue already lost", "bad"),
        ],
    ),
}

V["stripe/orphaned-pending-invoice-items"] = {
    "flow_intro": (
        "The script buckets pending items by customer and then asks the only "
        "question that decides anything: is any invoice still scheduled for that "
        "customer at all."
    ),
    "diagram_problem": D.chain(
        "sopi-p",
        "A pending invoice item orphaned when the subscription was cancelled",
        "Stripe holds the item exactly as instructed. The instruction was to wait "
        "for an invoice that will now never be raised.",
        [
            ("One off charge", "created with invoice null"),
            ("Waits for next cycle", "the documented behaviour"),
            ("Subscription cancelled", "no future invoices"),
            ("Item still pending", "no status change"),
            ("Never billed", "found only by looking"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sopi-f",
        "Sorting pending invoice items by whether an invoice is still coming",
        "Age alone cannot separate an annual cycle from an item nothing will ever "
        "collect.",
        ("GET invoiceitems", "pending=true, bucketed by customer"),
        [
            ("Live sub, under a cycle", "waiting, leave it", "good"),
            ("Live sub, past a cycle", "confirm the interval", "plain"),
            ("Live sub, past two", "stalled, look at it", "bad"),
            ("No active subscription", "orphaned at any age", "bad"),
        ],
    ),
}

V["stripe/no-tax-registrations-while-selling-abroad"] = {
    "flow_intro": (
        "The script compares the countries you are registered in against the "
        "countries your paid invoices went to, because a correct calculation of "
        "zero looks exactly like a working tax setup."
    ),
    "diagram_problem": D.chain(
        "sntr-p",
        "Zero tax on foreign invoices because no registration authorises collection",
        "The status field reads complete throughout. The liability accrues out of "
        "margin already recognised as revenue.",
        [
            ("Stripe Tax enabled", "calculation switched on"),
            ("Invoice to Germany", "customer address resolved"),
            ("No registration there", "nothing authorises collection"),
            ("Tax computed as 0", "reason not_collecting"),
            ("Threshold crossed", "liability plus interest"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sntr-f",
        "Sorting billed countries against the active registration list",
        "A registration that expired and one that never existed produce identical "
        "invoices and need different phone calls.",
        ("Registrations vs invoices", "active, expired, billed countries"),
        [
            ("Registered", "covered, leave it", "good"),
            ("Never registered", "unregistered, register it", "bad"),
            ("Registration expired", "collection stopped on a date", "bad"),
            ("Large untaxed revenue", "threshold likely crossed", "bad"),
        ],
    ),
}

V["stripe/prices-with-tax-behavior-unspecified"] = {
    "flow_intro": (
        "The script counts the active subscriptions on every unspecified price, "
        "because that count is the whole difference between a setting you change "
        "this afternoon and a priced migration."
    ),
    "diagram_problem": D.chain(
        "sptb-p",
        "An unspecified tax behavior blocking a line item on an automatic tax invoice",
        "The default value is the unsafe one, and it bills perfectly until "
        "somebody switches automatic tax on.",
        [
            ("Price created", "tax_behavior omitted"),
            ("Defaults to unspecified", "no warning anywhere"),
            ("Bills fine for years", "no tax being computed"),
            ("Automatic tax on", "line item rejected"),
            ("Value now permanent", "replace the price"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sptb-f",
        "Sorting prices by tax behavior and by how live the price is",
        "The same unspecified value means three different amounts of work "
        "depending on what is billing on it.",
        ("GET /v1/prices", "active=true, plus subscription counts"),
        [
            ("Explicit, product coded", "ready", "good"),
            ("Explicit, no tax code", "rate falls back to default", "plain"),
            ("Unspecified, dormant", "set it now, once", "bad"),
            ("Unspecified, live", "replacement price, migration", "bad"),
            ("Unspecified, tax on", "line items rejected today", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
