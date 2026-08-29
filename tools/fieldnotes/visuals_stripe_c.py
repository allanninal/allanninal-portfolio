#!/usr/bin/env python3
"""Diagrams for the /stripe/ subscriptions and billing field notes.

Same two shapes as every other section: the problem is a chain that breaks at one
step, the fix is a branch, because each script here classifies what it finds
rather than guessing. Drawn in Stripe indigo.

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

V["stripe/subscriptions-stuck-incomplete"] = {
    "flow_intro": (
        "The script asks Stripe one question and then does arithmetic on the answer: "
        "which subscriptions are incomplete, and how far each one is through the "
        "23 hour window before it expires for good."
    ),
    "diagram_problem": D.chain(
        "ssi-p",
        "A subscription created but never confirmed, expiring after 23 hours",
        "The creation call succeeds and the confirmation never happens. Stripe waits "
        "23 hours, then voids the invoice and the record is terminal.",
        [
            ("Subscription created", "status incomplete"),
            ("Client secret returned", "handed to the browser"),
            ("Never confirmed", "redirect loses it"),
            ("23 hours pass", "82800 seconds"),
            ("incomplete_expired", "invoice voided"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "ssi-f",
        "Sorting incomplete subscriptions by how long they have gone unconfirmed",
        "Age is the whole signal. Minutes old is a customer mid-flow; hours old is "
        "a confirmation step that never runs.",
        ("GET /v1/subscriptions", "status=incomplete"),
        [
            ("under an hour old", "normal, leave it", "good"),
            ("hours old, unconfirmed", "fix the confirm call", "bad"),
            ("past 23 hours", "gone, sign them up again", "bad"),
        ],
    ),
}

V["stripe/subscription-without-payment-method"] = {
    "flow_intro": (
        "The script walks the same four fields Stripe walks at renewal time, in the "
        "same order, and reports which one the charge will actually come from."
    ),
    "diagram_problem": D.chain(
        "swp-p",
        "A renewal invoice failing because no payment method resolves",
        "Stripe checks four fields in order. With all four null there is nothing to "
        "decline, so no retry is ever scheduled.",
        [
            ("Renewal due", "status active"),
            ("Resolve a method", "four fields, in order"),
            ("All four null", "nothing to charge"),
            ("Invoice fails", "no decline code"),
            ("No retry scheduled", "dunning never starts"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "swp-f",
        "Classifying a subscription by which payment method field resolves",
        "Knowing which field resolved matters as much as knowing that one did, "
        "because retries follow the field the failure happened on.",
        ("GET /v1/subscriptions", "expand[]=data.customer"),
        [
            ("subscription level default", "charges cleanly", "good"),
            ("customer level fallback", "works, worth pinning", "plain"),
            ("all four null", "unchargeable, collect a card", "bad"),
        ],
    ),
}

V["stripe/past-due-subscriptions-accumulating"] = {
    "flow_intro": (
        "The script reads the past due list with each latest invoice expanded, then "
        "uses the invoice age and attempt count to separate live dunning from a "
        "subscription Stripe has finished with."
    ),
    "diagram_problem": D.chain(
        "pds-p",
        "A failed renewal leaving a subscription past due with access intact",
        "Two ordinary decisions combine: Stripe is set to leave past due alone, and "
        "the app grants access to anything that is not canceled.",
        [
            ("Renewal fails", "card declined"),
            ("Status past_due", "retries begin"),
            ("Retries end", "post retry action: leave"),
            ("App checks status", "not canceled, so allow"),
            ("Access forever", "no revenue"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "pds-f",
        "Sorting past due subscriptions by invoice age and attempt count",
        "Only one of these three is a retry problem. The other two need a card or a "
        "cancellation, not a change to the retry schedule.",
        ("GET /v1/subscriptions", "status=past_due, invoice expanded"),
        [
            ("recent invoice, attempts rising", "dunning, may recover", "plain"),
            ("invoice over a month old", "parked, close it out", "bad"),
            ("zero attempts ever", "no payment method to charge", "bad"),
        ],
    ),
}

V["stripe/trial-ends-without-payment-method"] = {
    "flow_intro": (
        "The script finds trials ending inside the next 72 hours with no payment "
        "method, then reads one field to say which of three very different things "
        "will happen to each of them."
    ),
    "diagram_problem": D.chain(
        "tec-p",
        "A card free trial ending and failing on the trial end date",
        "The trial never asked for a card, nothing warned anyone, and the default "
        "end behaviour invoices a subscription that cannot pay.",
        [
            ("Trial starts", "no card required"),
            ("trial_will_end fires", "three days out, unhandled"),
            ("Trial end date", "still no card"),
            ("Invoice created", "default create_invoice"),
            ("Invoice fails", "status past_due"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "tec-f",
        "Predicting what happens to each card free trial from its end behaviour",
        "One field decides between three outcomes, and the check runs before the "
        "date rather than after it.",
        ("GET /v1/subscriptions", "status=trialing, customer expanded"),
        [
            ("a payment method resolves", "converts normally", "good"),
            ("no card, create_invoice", "lands in past_due", "bad"),
            ("no card, pause or cancel", "stops earning, needs a card", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
