#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes.

Same two shapes as the other sections: the problem is a chain that breaks at one
step, the fix is a branch, because every script here classifies what it finds
rather than guessing. Drawn in Stripe indigo — diagrams.set_theme() is called by
the section's build.py before these are built.

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

V["stripe/webhook-endpoint-disabled"] = {
    "flow_intro": (
        "The script asks Stripe two questions: which endpoints are disabled, and how "
        "many events failed to deliver. The first tells you what broke, the second "
        "tells you how much you have to replay once it is fixed."
    ),
    "diagram_problem": D.chain(
        "swd-p",
        "A webhook endpoint failing repeatedly until Stripe disables it",
        "Stripe retries a failing endpoint for up to three days, then stops. "
        "Nothing arrives after that, and nothing logs an error.",
        [
            ("Event created", "payment succeeds"),
            ("Stripe delivers", "POST to your URL"),
            ("Handler returns 404", "route moved"),
            ("Retries for 3 days", "exponential backoff"),
            ("Endpoint disabled", "delivery stops"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "swd-f",
        "Sorting webhook endpoints by status and counting undelivered events",
        "Every endpoint lands in one of three states, and only one of them needs "
        "a replay afterwards.",
        ("GET /v1/webhook_endpoints", "and /v1/events?delivery_success=false"),
        [
            ("enabled, nothing pending", "healthy, leave it", "good"),
            ("enabled, events failing", "fix the handler now", "bad"),
            ("disabled by Stripe", "re-enable, then replay", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
