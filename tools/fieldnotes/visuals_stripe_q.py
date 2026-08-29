#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch Q.

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

V["stripe/connect-reserved-balance-growing"] = {
    "flow_intro": (
        "The script reads what is held now, then two lists of balance transactions "
        "behind it, because a reserve balance is a level and only the movement "
        "underneath it says whether the money is coming back."
    ),
    "diagram_problem": D.chain(
        "scrb-p",
        "A negative connected account turning a reserve into a permanent loss",
        "Every step succeeds. The only thing that happens is that the platform's "
        "own payouts get quietly smaller each month.",
        [
            ("Seller refunds", "balance goes negative"),
            ("Seller stops trading", "nothing earns it back"),
            ("Platform reserved", "held from available"),
            ("180 days pass", "no one is watching"),
            ("Collection transfer", "reserve gone for good"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scrb-f",
        "Sorting a connect_reserved currency bucket by the movement behind it",
        "The same positive number means a business still taking losses or one dead "
        "account counting down. Only the balance transactions tell them apart.",
        ("GET /v1/balance", "plus 90 days of balance transactions"),
        [
            ("Nothing reserved", "clear", "good"),
            ("Reserved and released", "normal operation", "plain"),
            ("Held, no movement", "one dead account, 180 day clock", "bad"),
            ("Collection transfer seen", "already lost, fix the setting", "bad"),
        ],
    ),
}

V["stripe/stranded-currency-balance"] = {
    "flow_intro": (
        "The script reads both balance arrays, the external accounts and the recent "
        "payouts, because a missing destination and a destination nobody uses look "
        "identical on the balance and need different repairs."
    ),
    "diagram_problem": D.chain(
        "sscb-p",
        "A second currency settling into a balance bucket with no way out",
        "A reconciler that reads available index zero gets the healthy currency and "
        "reports a perfect match.",
        [
            ("Checkout localised", "EUR accepted"),
            ("EUR charges settle", "second balance entry"),
            ("No EUR destination", "payout cannot target it"),
            ("Payouts skip it", "USD keeps clearing"),
            ("Books never close", "fixed gap every month"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sscb-f",
        "Sorting each balance currency by whether it has an exit and uses it",
        "Money still in pending is the same problem a few days early, which is the "
        "only point at which it is cheap to fix.",
        ("GET /v1/balance", "plus external accounts and payouts"),
        [
            ("Destination and payouts", "draining normally", "good"),
            ("Pending, no destination", "strands when it settles", "bad"),
            ("Settled, no destination", "stuck now, add one", "bad"),
            ("Destination, no payouts", "check default_for_currency", "bad"),
        ],
    ),
}

V["stripe/application-fees-zero-on-platform"] = {
    "flow_intro": (
        "The script counts fee objects on one side and destination charges on the "
        "other, because the useful number is the fraction of charges carrying a fee "
        "rather than whether any fee exists at all."
    ),
    "diagram_problem": D.chain(
        "safz-p",
        "A destination charge transferring the full amount with no fee taken",
        "Nothing errors. The charge did exactly what it was told, which was to pass "
        "everything through to the seller.",
        [
            ("Charge created", "transfer_data destination"),
            ("No fee parameter", "application_fee_amount absent"),
            ("Full amount moves", "seller paid in full"),
            ("No fee object", "nothing to report on"),
            ("Revenue line zero", "since launch"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "safz-f",
        "Sorting a platform by how its destination charges take a fee",
        "Under transferring keeps the money and creates no fee object, so the "
        "revenue is real and every fee report reads zero.",
        ("GET /v1/application_fees", "plus a pass over /v1/charges"),
        [
            ("Every charge has a fee", "collecting", "good"),
            ("Some charges have none", "one code path forgot", "bad"),
            ("Kept via transfer_data", "revenue exists, reporting does not", "bad"),
            ("No fees anywhere", "add the parameter, check capabilities", "bad"),
        ],
    ),
}

V["stripe/payout-reconciliation-unavailable"] = {
    "flow_intro": (
        "The script reads two fields per payout and then checks the arithmetic on "
        "the ones that have a breakdown, because an endpoint that responds is not "
        "the same as a total that adds up."
    ),
    "diagram_problem": D.chain(
        "spru-p",
        "A manual payout schedule destroying the link between deposits and charges",
        "The payouts all worked. It is the audit trail that was never recorded, and "
        "it cannot be added afterwards.",
        [
            ("Schedule set manual", "during testing"),
            ("Payouts created by hand", "reconciliation not_applicable"),
            ("Deposit lands", "one number in the bank"),
            ("Filter by payout", "empty list, no error"),
            ("Quarter close", "nothing can be explained"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "spru-f",
        "Sorting payouts by reconciliation_status and by whether the total agrees",
        "not_applicable means two different things. On a manual payout it is a "
        "decision; on an automatic one Stripe simply does not itemise that kind.",
        ("GET /v1/payouts", "then balance transactions per payout"),
        [
            ("completed, total matches", "reconciled", "good"),
            ("in_progress", "still assembling, wait", "plain"),
            ("completed, total differs", "second currency or a reversal", "bad"),
            ("not_applicable, manual", "itemized report is the only route", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
