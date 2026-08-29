#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch F.

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

V["stripe/dispute-deadline-72h-no-evidence"] = {
    "flow_intro": (
        "The script measures due_by in hours rather than days, because the last "
        "stretch of a dispute window is where the decision actually gets made and "
        "a day is too coarse a unit to schedule against."
    ),
    "diagram_problem": D.chain(
        "sdd-p",
        "A dispute closing as lost because nobody read the deadline",
        "The evidence existed the whole time. What ran out was the window to send "
        "it, and no field anywhere records that difference afterwards.",
        [
            ("Network files it", "clock starts there"),
            ("Notice to shared inbox", "nobody owns it"),
            ("due_by passes", "no response sent"),
            ("Closed as lost", "funds and fee gone"),
            ("Read as unwinnable", "so the next one is skipped"),
        ],
        fail_at=1,
        loop=(4, 1, "the belief keeps the inbox unwatched"),
    ),
    "diagram_fix": D.branch(
        "sdd-f",
        "Sorting open disputes by hours left and whether evidence was submitted",
        "Staged evidence is not submitted evidence. Only submission_count "
        "separates a response from a draft that will forfeit anyway.",
        ("GET /v1/disputes", "status, due_by, submission_count"),
        [
            ("Over 72 hours left", "time to assemble", "good"),
            ("Under 72, nothing sent", "respond or close today", "bad"),
            ("Under 72, staged only", "the work is done, send it", "bad"),
            ("past_due, still open", "already lost, count it", "bad"),
        ],
    ),
}

V["stripe/disputes-lost-without-response"] = {
    "flow_intro": (
        "The script counts three numbers and reports two ratios, because the "
        "single headline loss rate mixes disputes you fought with disputes you "
        "never opened and measures neither."
    ),
    "diagram_problem": D.chain(
        "sdlw-p",
        "Forfeited disputes making the loss rate look like a verdict on evidence",
        "A forfeit and a defeat share one status, so the number used to decide "
        "whether disputes are worth fighting is built partly from disputes nobody "
        "fought.",
        [
            ("Deadlines pass", "no response sent"),
            ("Closed as lost", "same status as a defeat"),
            ("Loss rate looks awful", "outcomes only, no effort"),
            ("Fighting judged futile", "team stops trying"),
            ("Chargeback rate rises", "monitoring programme"),
        ],
        fail_at=2,
        loop=(3, 0, "the conclusion produces more forfeits"),
    ),
    "diagram_fix": D.branch(
        "sdlw-f",
        "Sorting a year of closed disputes by the share that were never answered",
        "Forfeits belong out of the denominator. What is left is the only number "
        "that says anything about the evidence you send.",
        ("GET /v1/disputes", "one year, won and lost only"),
        [
            ("No losses", "nothing to recover", "good"),
            ("Every loss answered", "a real loss rate", "good"),
            ("Under 30 percent forfeit", "recoverable process loss", "bad"),
            ("Over 30 percent forfeit", "a list, not a workflow", "bad"),
        ],
    ),
}

V["stripe/checkout-sessions-unreconcilable"] = {
    "flow_intro": (
        "The script takes the metadata keys your own code reads as an argument, "
        "because metadata full of campaign tags is not an order id and a "
        "truthiness check would call it one."
    ),
    "diagram_problem": D.chain(
        "scsu-p",
        "A paid Checkout Session that carries no pointer back to the order",
        "Email and amount are nearly unique at low volume, which is exactly how "
        "long the manual reconciliation survives.",
        [
            ("Session created", "no reference, no metadata"),
            ("Customer pays", "money arrives"),
            ("Webhook lands", "nothing to look up"),
            ("Matched by hand", "email and amount"),
            ("Dispute arrives", "evidence cannot be joined"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "scsu-f",
        "Sorting Checkout Sessions by whether they carry an identifier of yours",
        "An abandoned session with no reference is untidy. A paid one is money "
        "you cannot attribute to anything.",
        ("GET /v1/checkout/sessions", "client_reference_id and metadata"),
        [
            ("Reference set", "reconcilable", "good"),
            ("Some keys missing", "half a join", "plain"),
            ("Unpaid, no reference", "nothing taken yet", "plain"),
            ("Paid, no reference", "unattributable money", "bad"),
        ],
    ),
}

V["stripe/duplicate-customers-same-email"] = {
    "flow_intro": (
        "The script lowercases every address before grouping, then asks which of "
        "the duplicates actually hold a card or a subscription, which is what "
        "separates an untidy list from a person being billed twice."
    ),
    "diagram_problem": D.chain(
        "sdce-p",
        "One person split across three Customer records on the same email",
        "Stripe does not enforce uniqueness on customer email, so every create "
        "that skips a lookup mints another record.",
        [
            ("Re-signup at checkout", "no lookup first"),
            ("New cus_ created", "same address"),
            ("Card saved on it", "old record keeps its own"),
            ("Two subscriptions", "renewing independently"),
            ("Cancel one", "the other keeps charging"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "sdce-f",
        "Grouping customers by lowercased email and ranking by what they hold",
        "Case folding matters: Stripe's own email filter is exact, so the "
        "duplicate that differs by one capital hides from every lookup.",
        ("GET /v1/customers", "grouped, then cards and subscriptions"),
        [
            ("One record", "unique, leave it", "good"),
            ("Duplicates hold nothing", "tidy up later", "plain"),
            ("Two hold cards", "support answers the wrong one", "bad"),
            ("Two hold subscriptions", "two bills, one person", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
