#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch U.

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

V["stripe/customers-missing-address"] = {
    "flow_intro": (
        "The script classifies each address four ways rather than two, because an "
        "address object with a street and a city but no country reads as filled in "
        "everywhere except the one place that resolves a tax location."
    ),
    "diagram_problem": D.chain(
        "scmad-p",
        "A customer created before the address exists, failing at invoice finalization",
        "Every step returns 200. The first thing that objects is a finalization, "
        "months later, on a customer who has already paid several times.",
        [
            ("Customer created", "at signup, no address"),
            ("Address collected", "into your own tables"),
            ("Stripe copy stays null", "nothing writes it back"),
            ("Tax cannot resolve", "no country to use"),
            ("Invoice will not finalize", "customer_tax_location_invalid"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "scmad-f",
        "Sorting customers by whether their address can satisfy Tax, AVS and SCA",
        "Absent and partial fail identically. Only the subscribed cohort has a "
        "finalization due every cycle.",
        ("GET /v1/customers", "plus subscriptions, customer expanded"),
        [
            ("Country and postcode", "complete, leave it", "good"),
            ("Address object all null", "absent, backfill", "bad"),
            ("Street but no country", "tax cannot resolve", "bad"),
            ("Incomplete and subscribed", "a failure every renewal", "bad"),
        ],
    ),
}

V["stripe/setup-intent-on-session-for-off-session"] = {
    "flow_intro": (
        "The script reads the consent recorded at save time, not the card, because "
        "the credential is stored either way and only the mandate decides whether "
        "an unattended charge has anything to show the issuer."
    ),
    "diagram_problem": D.chain(
        "ssios-p",
        "A card saved with usage on_session declining at the first unattended renewal",
        "The save looks perfect in the Dashboard. mandate is null on the "
        "SetupIntent, and that is the only place the difference shows.",
        [
            ("usage = on_session", "consent for customer present"),
            ("SetupIntent succeeds", "card attached, no mandate"),
            ("Customer subscribes", "billing runs unattended"),
            ("Renewal charges", "issuer asks for authentication"),
            ("Decline", "authentication_required"),
        ],
        fail_at=3,
        loop=(4, 2, "smart retries repeat the same decline"),
    ),
    "diagram_fix": D.branch(
        "ssios-f",
        "Sorting saved cards by the consent recorded and by who is billed unattended",
        "Declines alone are not this problem. They mean it only when there are "
        "on_session saves behind them.",
        ("GET /v1/setup_intents", "plus payment intents and subscriptions"),
        [
            ("All off_session", "mandate present, fine", "good"),
            ("on_session, no subscribers", "check the charge model", "plain"),
            ("on_session and subscribed", "re-collect before renewal", "bad"),
            ("Declines already seen", "diagnosis settled", "bad"),
        ],
    ),
}

V["stripe/payment-intents-with-null-customer"] = {
    "flow_intro": (
        "The script groups customerless charges by card fingerprint, because a "
        "share is an argument about how much guest checkout you meant to have and "
        "a fingerprint counted twice is a named buyer you scored as a stranger."
    ),
    "diagram_problem": D.chain(
        "spinc-p",
        "A returning buyer paying four times with no Customer attached to any payment",
        "Nothing fails. The money arrives every time; the history that would have "
        "made the fourth payment an easy approval was never kept.",
        [
            ("Guest checkout", "no customer looked up"),
            ("Intent created", "customer left null"),
            ("Payment succeeds", "card discarded too"),
            ("Buyer returns", "still a stranger"),
            ("Risk score", "no history to lean on"),
        ],
        fail_at=1,
        loop=(3, 0, "every visit starts from nothing"),
    ),
    "diagram_fix": D.branch(
        "spinc-f",
        "Sorting orphaned payments by share and by repeat card fingerprints",
        "Six orphans in four thousand is noise until one of those cards appears "
        "twice, at which point the share stops being the story.",
        ("GET /v1/payment_intents", "plus charges grouped by fingerprint"),
        [
            ("Every intent attached", "clear", "good"),
            ("A few orphans", "fine if guests are deliberate", "plain"),
            ("Majority orphaned", "guest is the default path", "bad"),
            ("Fingerprint paid twice", "a repeat buyer lost", "bad"),
        ],
    ),
}

V["stripe/save-default-payment-method-off"] = {
    "flow_intro": (
        "The script reads the flag, the subscription default and the customer "
        "default together, because the flag being off only matters when neither "
        "default exists to catch the renewal."
    ),
    "diagram_problem": D.chain(
        "ssdpm-p",
        "A first invoice paid by a card the subscription never keeps",
        "The subscription is genuinely healthy at every moment before the second "
        "invoice, which is why a full billing period passes before anyone knows.",
        [
            ("Subscription created", "flag never set, so off"),
            ("First invoice paid", "card confirmed in browser"),
            ("Card not promoted", "default stays null"),
            ("Renewal runs", "nothing to charge"),
            ("past_due", "access carries on"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ssdpm-f",
        "Sorting subscriptions by the flag and by which defaults actually exist",
        "An absent flag is the same as off, and an unexpanded customer looks "
        "exactly like a customer with no default.",
        ("GET /v1/subscriptions", "status filtered, customer expanded"),
        [
            ("on_subscription", "the card is kept", "good"),
            ("Default on the subscription", "flag is moot", "good"),
            ("Customer default only", "works until the flow changes", "plain"),
            ("Neither default set", "nothing to charge next cycle", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
