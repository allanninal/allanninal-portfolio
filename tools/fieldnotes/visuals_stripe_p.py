#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch P.

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

V["stripe/unpaid-subscriptions-still-provisioned"] = {
    "flow_intro": (
        "The script reads the unpaid list, then the draft invoices behind each "
        "row, because the drafts are the only place the growing balance is "
        "recorded and auto_advance is what says whether anyone can still collect "
        "it."
    ),
    "diagram_problem": D.chain(
        "sussp-p",
        "A subscription marked unpaid keeping its access while billing stops",
        "Nothing fails after the status change, because nothing is attempted "
        "after the status change.",
        [
            ("Renewal fails", "dunning starts"),
            ("Retries run out", "end action: mark unpaid"),
            ("Status unpaid", "not canceled"),
            ("Invoices closed", "no attempt made"),
            ("Access kept", "check reads not canceled"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sussp-f",
        "Sorting an unpaid subscription by the draft invoices left behind it",
        "The drafts decide whether there is a balance to chase. The status "
        "decides whether the access should have ended months ago.",
        ("GET /v1/subscriptions", "status=unpaid, then its invoices"),
        [
            ("Not unpaid", "a different problem", "good"),
            ("Drafts with auto_advance", "collection restarted", "plain"),
            ("Drafts closed on creation", "finalise them, revoke access", "bad"),
            ("No invoices at all", "billing stopped, revoke access", "bad"),
        ],
    ),
}

V["stripe/paused-subscriptions-never-resumed"] = {
    "flow_intro": (
        "The script expands the customer on every paused subscription, because a "
        "card that turned up after the pause makes the row the easiest recovery "
        "on the list rather than the oldest entry on it."
    ),
    "diagram_problem": D.chain(
        "spsnr-p",
        "A trial ending without a card and parking the subscription in paused",
        "The pause setting is the safe choice. It is also a queue with nothing "
        "reading from it.",
        [
            ("Trial ends", "no payment method"),
            ("end_behavior pause", "safer than dunning"),
            ("Status paused", "invoicing stops"),
            ("No timeout", "waits indefinitely"),
            ("Nobody resumes", "cohort forgotten"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "spsnr-f",
        "Sorting paused subscriptions by recoverability rather than by date",
        "One billing interval is the honest cutoff, and it comes from this "
        "subscription's own price rather than a fixed number of days.",
        ("GET /v1/subscriptions", "status=paused, customer expanded"),
        [
            ("Card already on file", "resume it today", "bad"),
            ("Inside one interval", "win-back still open", "plain"),
            ("Past one interval", "dead inventory, count as churn", "bad"),
            ("Not paused", "a different problem", "good"),
        ],
    ),
}

V["stripe/pause-collection-left-on-indefinitely"] = {
    "flow_intro": (
        "The script never looks at the status, because the status is exactly what "
        "this field leaves alone. It reads pause_collection, then resumes_at, "
        "then the behaviour that decides what survives the pause."
    ),
    "diagram_problem": D.chain(
        "spcli-p",
        "A support grace period suppressing billing on a subscription that still reads active",
        "resumes_at is optional, and leaving it out means the pause lasts until "
        "a person notices.",
        [
            ("Customer asks", "grace period granted"),
            ("pause_collection set", "no resumes_at"),
            ("Status unchanged", "still active"),
            ("Invoices suppressed", "draft, void or written off"),
            ("Months pass", "absence is the only signal"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "spcli-f",
        "Sorting a paused collection by its resume date and its behaviour",
        "Two identical pauses cost different amounts. keep_as_draft leaves "
        "invoices to finalise; void throws each one away as it is made.",
        ("GET /v1/subscriptions", "status=active, read pause_collection"),
        [
            ("No pause", "collecting normally", "good"),
            ("Future resumes_at", "a pause with an end", "good"),
            ("Resumes_at already passed", "still paused, look at it", "bad"),
            ("No resumes_at, keep_as_draft", "resume and finalise the drafts", "bad"),
            ("No resumes_at, void", "those periods are gone", "bad"),
        ],
    ),
}

V["stripe/cancel-at-period-end-churn-backlog"] = {
    "flow_intro": (
        "The script counts the flag against the whole active list to get a rate, "
        "and takes the end date from the subscription item rather than from "
        "canceled_at, which records the click and not the departure."
    ),
    "diagram_problem": D.chain(
        "scape-p",
        "Committed churn staying invisible because the status is still active",
        "Every dashboard queries the status, and the status is correct about "
        "today and wrong about next month.",
        [
            ("Customer cancels", "in the billing portal"),
            ("Flag set", "cancel_at_period_end"),
            ("Status stays active", "paid through the period"),
            ("Reports flat", "churn not counted yet"),
            ("Period ends", "a fifth leaves at once"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "scape-f",
        "Sorting a pending churn backlog by rate and by the nearest end date",
        "A single cancellation three days out is more urgent than sixty spread "
        "across a year, so the date is checked before the rate.",
        ("GET /v1/subscriptions", "status=active, count the flag"),
        [
            ("None scheduled", "clear", "good"),
            ("First ends within a week", "a cliff, answer it now", "bad"),
            ("Over 10 percent scheduled", "a trend with a cause", "bad"),
            ("A handful, far out", "backlog, run save offers", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
