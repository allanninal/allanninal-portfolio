#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch J.

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

V["stripe/unattached-payment-methods-orphaned"] = {
    "flow_intro": (
        "The script counts unattached PaymentMethods against attached ones, then "
        "looks at the PaymentIntents that created them, because the ratio says how "
        "bad it is and the intents say which line of code did it."
    ),
    "diagram_problem": D.chain(
        "sopm-p",
        "A PaymentMethod consumed once without being attached to a customer",
        "Nothing fails on the day the card is saved. The failure waits for the "
        "second purchase, which is a month or a quarter later.",
        [
            ("Elements makes a pm_", "customer is null"),
            ("Intent charges it", "no setup_future_usage"),
            ("pm_ id stored", "looks saved to you"),
            ("Second checkout", "reuses the same id"),
            ("Rejected", "unexpected state"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sopm-f",
        "Sorting card PaymentMethods by whether they were ever attached",
        "A count of orphans is history. A share of orphans is the behaviour of the "
        "checkout that is running right now.",
        ("GET /v1/payment_methods", "type=card, plus /v1/payment_intents"),
        [
            ("All attached", "cards are reusable", "good"),
            ("A few orphans", "residue, not the live path", "plain"),
            ("Quarter unattached", "reuse will fail", "bad"),
            ("A reuse already failed", "customers stuck at checkout", "bad"),
        ],
    ),
}

V["stripe/cards-expiring-within-60-days"] = {
    "flow_intro": (
        "The script starts from active subscriptions rather than from customers, "
        "converts each card expiry into an instant, and drops wallet credentials "
        "before anything reaches the warning list."
    ),
    "diagram_problem": D.chain(
        "scew-p",
        "A saved card expiring on a known date with nobody warned in advance",
        "Every date in this chain was readable from the API on the day the card "
        "was saved.",
        [
            ("Card saved", "exp 09/2026"),
            ("Months pass", "nothing reads the date"),
            ("Card expires", "issuer reissues or not"),
            ("Renewal declines", "expired_card"),
            ("Dunning email", "first the customer hears"),
        ],
        fail_at=2,
        loop=(4, 1, "recovery depends on an email"),
    ),
    "diagram_fix": D.branch(
        "scew-f",
        "Sorting saved cards by how long they have left and what kind they are",
        "A wallet token is reissued with the card, so warning that customer costs "
        "a support ticket and buys nothing.",
        ("GET /v1/payment_methods", "for each active subscriber"),
        [
            ("Over 60 days left", "outside the window", "good"),
            ("Wallet credential", "survives reissue, skip it", "good"),
            ("Under 60 days", "nudge at 45 days", "bad"),
            ("Under 60 and default", "name the renewal that fails", "bad"),
        ],
    ),
}

V["stripe/customers-missing-email"] = {
    "flow_intro": (
        "The script counts the blank emails, then asks which of those customers "
        "are being billed and which have already disputed a charge, because those "
        "two questions turn a percentage into a cost."
    ),
    "diagram_problem": D.chain(
        "scme-p",
        "A charge with no email behind it ending as an unrecognised dispute",
        "No bounce, no error, no field recording that the receipt went nowhere. "
        "The payment succeeded, which is the part anyone watches.",
        [
            ("Customer created", "email left null"),
            ("Charge succeeds", "200 as always"),
            ("No receipt sent", "nothing to send it to"),
            ("Descriptor unfamiliar", "weeks later"),
            ("Dispute opened", "unrecognised"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scme-f",
        "Sorting the missing email gap by what it is already costing",
        "One dispute on an emailless customer outranks any percentage, because "
        "that money has already left.",
        ("GET /v1/customers", "plus subscriptions and charges"),
        [
            ("Every customer has one", "receipts are sent", "good"),
            ("Guest charges only", "set receipt_email", "plain"),
            ("A quarter blank", "the signup path does this", "bad"),
            ("Blank with a subscription", "dunning has nowhere to go", "bad"),
        ],
    ),
}

V["stripe/setup-intents-never-confirmed"] = {
    "flow_intro": (
        "The script ages the window by a day, buckets the three unresolved "
        "statuses, and lets the dominant bucket name the defect rather than "
        "reporting one undifferentiated pile."
    ),
    "diagram_problem": D.chain(
        "ssinc-p",
        "A SetupIntent created server side and never confirmed by the browser",
        "The failure happens in the browser, which is also where the success "
        "message lives. The server hears nothing either way.",
        [
            ("Server creates intent", "returns a client secret"),
            ("Client never confirms", "error or closed tab"),
            ("UI says saved", "on the network response"),
            ("No mandate exists", "status stays stuck"),
            ("Renewal fails", "nothing to charge"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ssinc-f",
        "Sorting stuck SetupIntents by which status the pile sits in",
        "People really do abandon card forms. The bucket the stuck ones land in "
        "is what separates that from a defect.",
        ("GET /v1/setup_intents", "created over a day ago, by status"),
        [
            ("All resolved", "the confirm path works", "good"),
            ("Under a fifth stuck", "ordinary drop off", "plain"),
            ("Mostly requires_confirmation", "confirmSetup never runs", "bad"),
            ("Mostly requires_action", "the return_url landing page", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
