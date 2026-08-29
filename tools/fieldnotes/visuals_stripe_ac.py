#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch AC.

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

V["stripe/no-v2-event-destinations"] = {
    "flow_intro": (
        "The script asks the v2 list endpoint what destinations exist, then asks "
        "one v1 endpoint whether anything on the account emits thin events yet, "
        "because an empty list is a gap on one account and an outage on another."
    ),
    "diagram_problem": D.chain(
        "snved-p",
        "A thin event subscribed on a v1 endpoint and delivered nowhere",
        "The v1 prefix in the event name describes the resource, not the delivery "
        "system, and every step of the wrong setup returns success.",
        [
            ("Feature turned on", "billing meters"),
            ("Event named v1.*", "read as a v1 event"),
            ("Added to v1 endpoint", "saved with no error"),
            ("Thin event emitted", "needs a v2 destination"),
            ("Nothing delivered", "handler never runs"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "snved-f",
        "Sorting an account by whether a thin event has anywhere to land",
        "Counting destinations is not the check. A destination that carries "
        "snapshot payloads cannot carry a thin event at all.",
        ("GET /v2/core/event_destinations", "plus one probe for v2 features in use"),
        [
            ("Enabled thin destination", "covered", "good"),
            ("Thin but disabled", "fix the handler, re-enable", "bad"),
            ("Only snapshot payloads", "create a thin destination", "bad"),
            ("None, v2 feature live", "events dropping now", "bad"),
            ("None, nothing emitting", "a gap to close", "plain"),
        ],
    ),
}

V["stripe/radar-blocked-rate-overblocking"] = {
    "flow_intro": (
        "The script measures a rate rather than reading a charge, and takes "
        "Adaptive Acceptance out of the numerator first, because those blocks are "
        "not caused by anything you can edit."
    ),
    "diagram_problem": D.chain(
        "srbro-p",
        "An over broad Radar rule turning good customers away with no trace",
        "A blocked payment never reaches the issuer, so the customer's bank has no "
        "record of the attempt and confirms the card is fine.",
        [
            ("Fraud wave", "broad rule written"),
            ("Wave passes", "rule left in place"),
            ("Good card matches", "attribute, not risk"),
            ("Never sent to network", "no decline code"),
            ("Bank says card works", "both sides correct"),
        ],
        fail_at=2,
        loop=(4, 1, "no chargebacks, so fraud numbers look excellent"),
    ),
    "diagram_fix": D.branch(
        "srbro-f",
        "Sorting a window of charge attempts by the block rate you can change",
        "One predicate causing most blocks on charges Radar scored normal is a "
        "rule matching an attribute rather than fraud.",
        ("GET /v1/charges over a fixed window", "outcome.rule expanded"),
        [
            ("Few blocks", "normal", "good"),
            ("All adaptive acceptance", "not your rules", "good"),
            ("Rate creeping up", "track it as a series", "plain"),
            ("High, spread out", "check the risk threshold", "bad"),
            ("High, one predicate", "narrow that rule", "bad"),
        ],
    ),
}

V["stripe/payment-link-completion-limit-reached"] = {
    "flow_intro": (
        "The script reads the restrictions object on every link, then counts the "
        "sessions a capped link is still creating, because an exhausted link that "
        "nobody clicks is housekeeping and one that people click is lost revenue."
    ),
    "diagram_problem": D.chain(
        "splcl-p",
        "A campaign link meeting its completion cap and closing itself",
        "The link stays active and the URL keeps resolving, so every check anyone "
        "owns still reports it healthy.",
        [
            ("Cap set at creation", "a limited run"),
            ("Campaign published", "URL pasted everywhere"),
            ("Counter reaches cap", "no notification"),
            ("Completions refused", "link still active"),
            ("Blamed on demand", "campaign ran its course"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "splcl-f",
        "Sorting Payment Links by how much of their completion cap is left",
        "The near limit state is the only one where this is still cheap: the cap "
        "can be raised before anyone is turned away.",
        ("GET /v1/payment_links", "plus sessions per capped link"),
        [
            ("No restrictions", "uncapped", "good"),
            ("Well inside the cap", "headroom", "good"),
            ("Counter missing", "unread, not zero", "plain"),
            ("Over 90 percent used", "raise it this week", "bad"),
            ("Cap met, still clicked", "customers turned away", "bad"),
        ],
    ),
}

V["stripe/billing-portal-cancel-disabled"] = {
    "flow_intro": (
        "The script reads one feature flag and then prices it, because a portal "
        "with no cancel button is an opinion until the disputes that name it are "
        "counted against the disputes that do not."
    ),
    "diagram_problem": D.chain(
        "sbpcd-p",
        "A customer who cannot cancel in the portal cancelling at their bank",
        "Nothing errors anywhere in this sequence. The only trace is a dispute "
        "reason code that nobody maps back to a feature flag.",
        [
            ("Customer wants out", "opens the portal"),
            ("No cancel button", "feature off by default"),
            ("Emails support", "waits for a reply"),
            ("Disputes the charge", "reason subscription_canceled"),
            ("Fee plus dispute rate", "cannot be won"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sbpcd-f",
        "Sorting a portal configuration by what a customer can actually do in it",
        "Cancel and card update fail into the same support queue, so they are "
        "worth fixing in the same change.",
        ("GET /v1/billing_portal/configurations", "plus disputes by reason"),
        [
            ("Cancel and reason on", "self serve", "good"),
            ("Cancel on, no reason asked", "free churn data lost", "plain"),
            ("Cancel on, card update off", "expired cards go to support", "bad"),
            ("Cancel off", "the bank is the exit", "bad"),
            ("Cancel off, disputes cite it", "priced already", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
