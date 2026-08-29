#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch E: Connect and payouts.

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

V["stripe/connected-accounts-charges-disabled"] = {
    "flow_intro": (
        "The script reads every connected account and sorts it by who can fix it, "
        "because an account waiting on a form and an account Stripe has rejected "
        "look identical through the charges_enabled flag alone."
    ),
    "diagram_problem": D.chain(
        "scad-p",
        "A connected account losing charges while the platform sees nothing",
        "The platform's own account stays healthy throughout, so no graph moves "
        "and no request of yours ever errors.",
        [
            ("Capability goes inactive", "unmet verification"),
            ("charges_enabled false", "checkout starts failing"),
            ("account.updated fires", "nothing subscribed"),
            ("Platform sees nothing", "own account is fine"),
            ("Seller emails support", "two weeks later"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "scad-f",
        "Sorting disabled connected accounts by who is able to fix them",
        "An onboarding link sent to a rejected account produces a completed form "
        "and no change in status.",
        ("GET /v1/accounts", "charges_enabled and disabled_reason"),
        [
            ("charges_enabled true", "live, nothing to chase", "good"),
            ("details_submitted false", "never opened, not an incident", "plain"),
            ("requirements past due", "collect fields, send a link", "bad"),
            ("rejected or under review", "Dashboard only, no API fix", "bad"),
        ],
    ),
}

V["stripe/requirements-past-due-disables-account"] = {
    "flow_intro": (
        "The script reads the requirement arrays innermost first, because "
        "past_due sits inside currently_due and a length check on the outer array "
        "reports an already broken account as routine paperwork."
    ),
    "diagram_problem": D.chain(
        "srpd-p",
        "A currently_due monitor missing the account whose payouts already stopped",
        "The monitor is not broken. It fires on a real field, and that field "
        "cannot tell a warning apart from a disabled account.",
        [
            ("Threshold crossed", "current_deadline set"),
            ("Fields go uncollected", "still in currently_due"),
            ("Deadline passes", "fields move to past_due"),
            ("Payouts disabled", "payouts_enabled false"),
            ("Monitor stays green", "one array, one count"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "srpd-f",
        "Sorting connected accounts by requirement state and deadline",
        "Already broken, breaks on a known date, and nothing wrong yet are three "
        "different answers with three different response times.",
        ("GET /v1/accounts", "past_due, currently_due, current_deadline"),
        [
            ("No requirements", "clear", "good"),
            ("eventually_due only", "not urgent", "plain"),
            ("Deadline inside 14 days", "collect the cohort now", "bad"),
            ("past_due not empty", "capabilities already off", "bad"),
        ],
    ),
}

V["stripe/payouts-failing-bank-rejection"] = {
    "flow_intro": (
        "The script groups failed payouts by failure_code, because that enum is "
        "the only thing that says whether the fix belongs to the seller, their "
        "bank, or your own balance."
    ),
    "diagram_problem": D.chain(
        "spbr-p",
        "A payout reaching paid and then being rejected by the receiving bank",
        "The funds return to your balance days later, so a report that sums "
        "payouts without the reversals counts money that never left.",
        [
            ("Payout created", "pending"),
            ("Sent to the bank", "in_transit, then paid"),
            ("Bank rejects it", "up to 5 business days later"),
            ("Status flips to failed", "funds return to balance"),
            ("Destination frozen", "later payouts never run"),
        ],
        fail_at=2,
        loop=(4, 1, "no attempts, so no new failures"),
    ),
    "diagram_fix": D.branch(
        "spbr-f",
        "Sorting failed payouts by the person who can act on the failure code",
        "account_closed and debit_not_authorized both leave a recipient unpaid "
        "and need opposite actions.",
        ("GET /v1/payouts", "status=failed, grouped by failure_code"),
        [
            ("account_closed, no_account", "attach fresh bank details", "bad"),
            ("debit_not_authorized", "holder authorises with the bank", "bad"),
            ("insufficient_funds", "your balance, top it up", "bad"),
            ("could_not_process", "transient, one retry", "plain"),
        ],
    ),
}

V["stripe/no-external-account-attached"] = {
    "flow_intro": (
        "The script asks each account for its destinations and checks the default "
        "for the account's own currency, because a bank account attached in the "
        "wrong currency pays out exactly as often as none at all."
    ),
    "diagram_problem": D.chain(
        "snea-p",
        "A connected account accumulating a balance it has no destination for",
        "There is no payout object, no failure code and no event, because nothing "
        "was ever attempted.",
        [
            ("Collection turned off", "platform will gather details"),
            ("Onboarding completes", "details_submitted true"),
            ("No destination attached", "the other half never built"),
            ("No payout attempted", "nothing fails, nothing logs"),
            ("Balance climbs", "found months later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "snea-f",
        "Sorting connected accounts by whether their balance has anywhere to go",
        "A row count passes an account whose only destination is in a currency "
        "the balance is not in.",
        ("GET external_accounts", "plus default_currency and currently_due"),
        [
            ("Default set for the currency", "payouts can run", "good"),
            ("Attached, no default", "flag one for the currency", "bad"),
            ("Attached, wrong currency", "attach one that matches", "bad"),
            ("Nothing attached", "collect details or re-enable", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
