#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch K — payments and intents.

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

V["stripe/testmode-decline-in-live-mode"] = {
    "flow_intro": (
        "The script reads the mode off the key prefix before it reads anything "
        "else, then asks the account whether it can charge at all, because both "
        "answers change what the decline count is allowed to mean."
    ),
    "diagram_problem": D.chain(
        "stdl-p",
        "A test key surviving to production because every test uses test cards",
        "The configuration is only wrong for real cards, and no test in the suite "
        "pays with one.",
        [
            ("Keys pasted in", "test pair, during an incident"),
            ("Suite passes", "4242 works perfectly"),
            ("Deploy ships", "nothing looks wrong"),
            ("Real card pays", "testmode_decline"),
            ("Blamed on bank", "customer leaves"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "stdl-f",
        "Sorting a live account by key mode, activation state and decline count",
        "Three unrelated mistakes produce one symptom, so the order of the "
        "questions is what tells them apart.",
        ("Key prefix, GET /v1/account", "then charges and intents"),
        [
            ("Key is not live", "re-run with a live key", "plain"),
            ("charges_enabled false", "activation unfinished", "bad"),
            ("testmode_decline seen", "test artefact in production", "bad"),
            ("Live account is empty", "app is writing to test", "bad"),
            ("Live objects, no declines", "modes are matched", "good"),
        ],
    ),
}

V["stripe/card-only-payment-method-types"] = {
    "flow_intro": (
        "The script reads two fields on every intent rather than one, because a "
        "dynamic intent in a card only market carries exactly the same "
        "payment_method_types as a hardcoded one."
    ),
    "diagram_problem": D.chain(
        "scop-p",
        "An explicit method list making every Dashboard toggle inert",
        "Nothing errors. The intent named its methods and Stripe honoured the "
        "list exactly as given.",
        [
            ("Tutorial copied", "payment_method_types card"),
            ("Methods enabled", "iDEAL, Klarna, Link"),
            ("Intent created", "explicit list wins"),
            ("Element renders", "one card form"),
            ("Conversion flat", "blamed on the market"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "scop-f",
        "Sorting intents by whether the method list was passed in or computed",
        "A method enabled and never offered means a hardcoded list on some "
        "intents and an eligibility mismatch on none.",
        ("GET /v1/payment_intents", "plus payment_method_configurations"),
        [
            ("Most intents pinned", "drop the array", "bad"),
            ("Some intents pinned", "a half done migration", "bad"),
            ("None pinned, gaps left", "check currency and amount", "plain"),
            ("Every method reaches an intent", "dynamic and working", "good"),
        ],
    ),
}

V["stripe/off-session-authentication-required-declines"] = {
    "flow_intro": (
        "The script groups declines by customer before it asks about mandates, "
        "because the mandate is a property of how one card was saved and six "
        "failed renewals for one customer are a single problem."
    ),
    "diagram_problem": D.chain(
        "soam-p",
        "A card attached without a SetupIntent failing every off session charge",
        "The first charge is on session and works, so the bug is invisible until "
        "the next billing cycle.",
        [
            ("Card attached", "bare attach call"),
            ("No mandate recorded", "nothing to prove consent"),
            ("First charge works", "customer was present"),
            ("Renewal declines", "authentication_required"),
            ("Retries repeat", "identical answer"),
        ],
        fail_at=2,
        loop=(4, 3, "every retry declines identically"),
    ),
    "diagram_fix": D.branch(
        "soam-f",
        "Sorting customers by declines seen and by whether a mandate exists",
        "A decline without a mandate is a card saving bug. A decline with one is "
        "the issuer stepping up, and the repairs differ.",
        ("Declines per customer", "plus GET /v1/setup_intents"),
        [
            ("Declines, no mandate", "re authenticate the card", "bad"),
            ("Declines, mandate on file", "finish this one on session", "bad"),
            ("No declines, no mandate", "will fail at renewal", "bad"),
            ("Saved cards, mandate on file", "chargeable off session", "good"),
        ],
    ),
}

V["stripe/wallet-domain-not-registered"] = {
    "flow_intro": (
        "The script checks livemode before it checks anything else, then reads "
        "each wallet status on its own, because one domain can serve Link "
        "happily while Apple Pay is dark."
    ),
    "diagram_problem": D.chain(
        "swdr-p",
        "A subdomain move removing every wallet from the checkout page",
        "Registration is per host, so the apex domain next to it stays registered "
        "and healthy the whole time.",
        [
            ("example.com registered", "wallets render"),
            ("Checkout moves", "checkout.example.com"),
            ("Host unregistered", "no new registration"),
            ("Wallet filtered out", "no error, no request"),
            ("Mobile drops", "blamed on layout"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "swdr-f",
        "Sorting registered payment method domains by mode, state and wallet status",
        "A test mode registration is what people find when they check, and it is "
        "why they stop checking.",
        ("GET /v1/payment_method_domains", "against the hosts you serve"),
        [
            ("Nothing registered", "every wallet dark", "bad"),
            ("Registered in test only", "no effect on live", "bad"),
            ("Live but a wallet inactive", "read status_details", "bad"),
            ("Host serving, not listed", "register that host", "bad"),
            ("Live, enabled, all active", "wallets render", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
