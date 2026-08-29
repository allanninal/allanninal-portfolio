#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch V.

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

V["stripe/person-requirements-outstanding"] = {
    "flow_intro": (
        "The script splits every account level requirement on its first dot before "
        "it fetches anything, because the part on the left is a resource id and the "
        "part on the right is the field that one human still owes."
    ),
    "diagram_problem": D.chain(
        "spro-p",
        "An account blocked by a requirement that names a Person, not a field",
        "Everything the onboarding form knows how to collect is already collected. "
        "The outstanding item is on an object the integration never reads.",
        [
            ("Company onboards", "form fully completed"),
            ("Account looks done", "details_submitted true"),
            ("currently_due", "person_1Mq.verification"),
            ("No matching field", "form has nothing to ask"),
            ("charges_enabled false", "blocked indefinitely"),
        ],
        fail_at=2,
        loop=(4, 0, "form is rebuilt, requirement stays"),
    ),
    "diagram_fix": D.branch(
        "spro-f",
        "Sorting the Persons on an account by what each of them still owes",
        "A person under review needs nothing collected. Sending them a link opens "
        "a form with no fields on it.",
        ("GET /accounts/{id}/persons", "one requirements hash each"),
        [
            ("past_due not empty", "capabilities already off", "bad"),
            ("currently_due not empty", "collect these fields", "bad"),
            ("verification pending", "under review, wait", "plain"),
            ("verified, nothing due", "clear", "good"),
        ],
    ),
}

V["stripe/future-requirements-deadline-ignored"] = {
    "flow_intro": (
        "The script reads the hash that does not affect anything yet, then sorts by "
        "the date on which it will, because the only useful form of this warning is "
        "an ordered list with days remaining next to each account."
    ),
    "diagram_problem": D.chain(
        "sfrd-p",
        "A cohort of verified accounts disabled together at one deadline",
        "Nothing changes state before the deadline, so a monitor reading "
        "requirements has nothing to report right up to the morning it breaks.",
        [
            ("Rule change lands", "future_requirements set"),
            ("Capabilities unaffected", "account stays active"),
            ("Monitor reads requirements", "hash still empty"),
            ("Deadline passes", "entries migrate across"),
            ("14 accounts down", "same morning"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sfrd-f",
        "Sorting accounts by the deadline attached to their future requirements",
        "Accounts whose requirements Stripe collects are dropped first. Their "
        "state is not yours to act on either way.",
        ("GET /v1/accounts", "future_requirements plus controller"),
        [
            ("collection by stripe", "not yours to chase", "plain"),
            ("deadline passed", "migrating into requirements", "bad"),
            ("deadline within 14 days", "collect this week", "bad"),
            ("deadline further out", "schedule it", "plain"),
            ("due but no deadline", "coming, date unknown", "plain"),
            ("nothing future", "clear", "good"),
        ],
    ),
}

V["stripe/card-payments-inactive-cascades"] = {
    "flow_intro": (
        "The script reads both halves of the coupled pair, then unions the "
        "outstanding fields across every capability on the account, keeping the "
        "name of whichever capability asked for each one."
    ),
    "diagram_problem": D.chain(
        "scpic-p",
        "Transfers held down by a requirement filed under card_payments",
        "The capability being worked has an empty requirement list, so every "
        "piece of evidence in front of the reader says the fix already landed.",
        [
            ("transfers inactive", "the symptom"),
            ("Read its requirements", "two fields listed"),
            ("Fields submitted", "Stripe accepts them"),
            ("Still inactive", "card_payments is the block"),
            ("Cycle repeats", "list is empty now"),
        ],
        fail_at=3,
        loop=(4, 1, "one capability at a time cannot converge"),
    ),
    "diagram_fix": D.branch(
        "scpic-f",
        "Sorting the card_payments and transfers pair by their two statuses",
        "The coupling is symmetric, so the status alone says something is wrong "
        "without saying which half caused it.",
        ("capabilities on the account", "both halves read together"),
        [
            ("both active", "healthy", "good"),
            ("either inactive", "both disabled, union the fields", "bad"),
            ("either pending", "Stripe is verifying, wait", "plain"),
            ("only one present", "no coupling, different fault", "plain"),
        ],
    ),
}

V["stripe/external-account-currency-mismatch"] = {
    "flow_intro": (
        "The script checks whether the payout route is legal before it looks at any "
        "bank details, because an unsupported corridor also produces a currency "
        "mismatch and no bank account will ever resolve it."
    ),
    "diagram_problem": D.chain(
        "seacm-p",
        "A payout with no destination in the currency the balance settles in",
        "Stripe does not convert to reach a destination, so a bank account in "
        "another currency is not a worse option than the right one.",
        [
            ("Seller adds bank", "AUD account, accepted"),
            ("Balance builds", "settles in USD"),
            ("Payout attempted", "needs a USD destination"),
            ("No match found", "error names the currency"),
            ("Details re-entered", "same account, same result"),
        ],
        fail_at=2,
        loop=(4, 0, "the numbers were never wrong"),
    ),
    "diagram_fix": D.branch(
        "seacm-f",
        "Sorting settlement paths by corridor, currency and default flag",
        "The corridor is checked first. Where the route is unsupported the "
        "currency is not what is wrong and collecting a bank account cannot help.",
        ("country spec plus", "GET /accounts/{id}/external_accounts"),
        [
            ("country not transferable", "no API fix, change product", "bad"),
            ("country cannot hold it", "different bank required", "bad"),
            ("no matching currency", "add a destination in it", "bad"),
            ("match, not the default", "one flag away", "plain"),
            ("match and default", "settles", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
