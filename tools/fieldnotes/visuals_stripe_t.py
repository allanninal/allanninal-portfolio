#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch T.

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

V["stripe/checkout-guest-customer-null"] = {
    "flow_intro": (
        "The script reads a window of completed sessions once, counts how many "
        "share each email address, and only then classifies them, because a single "
        "session cannot tell you whether its buyer has been here before."
    ),
    "diagram_problem": D.chain(
        "scgn-p",
        "A payment mode Checkout Session completing with no Customer attached",
        "Nothing in the flow looks wrong. Stripe emails a receipt to an address "
        "that is a string on the Session and not a Customer.",
        [
            ("Session created", "customer_creation default"),
            ("Buyer pays", "as a guest"),
            ("Stripe makes no Customer", "not required here"),
            ("Receipt sent", "to customer_details.email"),
            ("Buyer returns", "a stranger again"),
        ],
        fail_at=1,
        loop=(4, 0, "every visit starts over"),
    ),
    "diagram_fix": D.branch(
        "scgn-f",
        "Sorting completed Checkout Sessions by whether they left a Customer behind",
        "The guest count says the flag is on the default. The repeat count says "
        "what that costs you this quarter.",
        ("GET /v1/checkout/sessions", "status=complete, grouped by email"),
        [
            ("Customer attached", "linked, leave it", "good"),
            ("Guest, seen once", "customer_creation=always", "bad"),
            ("Guest, seen again", "a repeat buyer you miss", "bad"),
            ("Guest with no email", "nothing to match later", "bad"),
        ],
    ),
}

V["stripe/checkout-recovery-never-enabled"] = {
    "flow_intro": (
        "The script classifies every lapse in the window, then asks the other half "
        "of the question: has any completed session ever carried recovered_from? "
        "Configuration says what should happen; that field says what did."
    ),
    "diagram_problem": D.chain(
        "scrne-p",
        "A Checkout Session expiring with no recovery url to email",
        "Recovery is opt in at session creation. A lapse without it has no url, "
        "and no endpoint mints one afterwards.",
        [
            ("Session created", "recovery not set"),
            ("Cart abandoned", "nobody pays"),
            ("Session expires", "status expired"),
            ("Payload has no url", "recovery.url null"),
            ("No email sent", "cart written off"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "scrne-f",
        "Sorting expired Checkout Sessions by whether the lapse can still be mailed",
        "Four outcomes, four different jobs: a code change, a scheduling fix, a "
        "consent problem, and a send you have not made.",
        ("GET /v1/checkout/sessions", "status=expired, plus recovered_from"),
        [
            ("Recovery never enabled", "set it at creation", "bad"),
            ("Url past expires_at", "30 days from the lapse", "bad"),
            ("Url live, no opt in", "collect consent too", "bad"),
            ("Url live and consented", "send the email", "good"),
        ],
    ),
}

V["stripe/checkout-embedded-no-return-url"] = {
    "flow_intro": (
        "The script splits sessions by ui_mode first, because embedded and hosted "
        "checkouts fail in different fields, and then compares two fields that are "
        "each valid on their own and wrong together."
    ),
    "diagram_problem": D.chain(
        "senr-p",
        "An embedded Checkout Session with no return url losing a redirect payment",
        "Cards never leave the page, so the return leg is never exercised until a "
        "live customer authenticates at a bank.",
        [
            ("Embedded form", "ui_mode embedded"),
            ("Buyer picks iDEAL", "leaves your page"),
            ("Bank authenticates", "payment succeeds"),
            ("Return leg", "return_url is null"),
            ("Buyer sees nothing", "reports a failure"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "senr-f",
        "Sorting Checkout Sessions by whether the customer has somewhere to return to",
        "A session can be blocked with a perfectly good return_url, because never "
        "removes the payment method rather than the redirect.",
        ("GET /v1/checkout/sessions", "split by ui_mode"),
        [
            ("Return url present", "ok, leave it", "good"),
            ("Embedded, no return url", "no destination", "bad"),
            ("never plus iDEAL", "method never offered", "bad"),
            ("Hosted, no session id", "landing page knows nothing", "bad"),
        ],
    ),
}

V["stripe/payment-link-hosted-confirmation-no-fulfilment"] = {
    "flow_intro": (
        "Two GETs, joined: what each link does after payment, and whether any "
        "enabled endpoint on the account listens for the completion event. Neither "
        "fact means much without the other."
    ),
    "diagram_problem": D.chain(
        "splhc-p",
        "A Payment Link ending on Stripe's confirmation page with nothing fulfilling",
        "The buyer's browser never touches your domain, so no page of yours could "
        "have started the work.",
        [
            ("Link shared", "after_completion default"),
            ("Buyer pays", "money arrives"),
            ("Stripe shows its page", "flow ends there"),
            ("No redirect, no webhook", "nothing is told"),
            ("Nothing provisioned", "buyer emails support"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "splhc-f",
        "Sorting Payment Links by after completion type and webhook coverage",
        "The same link is untidy on an account that subscribes the event and a "
        "silent outage on one that does not.",
        ("GET /v1/payment_links", "plus GET /v1/webhook_endpoints"),
        [
            ("Redirect and event", "covered", "good"),
            ("Stripe page, event set", "webhook does the work", "plain"),
            ("Redirect, no event", "browser is the only trigger", "bad"),
            ("Stripe page, no event", "nothing fulfils at all", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
