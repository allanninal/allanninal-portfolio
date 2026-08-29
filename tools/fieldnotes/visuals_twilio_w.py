#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch W.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#F22F46"
D.set_theme(BRAND)

V = {}

V["twilio/studio-flow-invalid-definition"] = {
    "flow_intro": (
        "The diagnosis is read from the single flow rather than the list, because "
        "errors[] and warnings[] are carried there. status only decides who is "
        "affected: a published Flow is failing now, a draft cannot be published."
    ),
    "diagram_problem": D.chain(
        "tsiv-p",
        "An execution that stops halfway because the definition does not compile",
        "The canvas renders a widget whose transition points at nothing as a "
        "widget with one fewer arrow. Nothing turns red, so the drawing keeps "
        "looking finished.",
        [
            ("Widget deleted", "no longer needed"),
            ("Transitions kept it", "reference left behind"),
            ("valid is false", "errors[] populated"),
            ("Execution starts", "greeting plays"),
            ("Stops at the fault", "caller hears silence"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tsiv-f",
        "Sorting Studio Flows by whether the definition behind the canvas compiles",
        "An invalid draft must never be told to press Publish: the widget has to "
        "be fixed first. Warnings belong in their own column or the one line that "
        "meant an outage arrives eleventh.",
        ("GET /v2/Flows/{FlowSid}", "valid, errors[], warnings[], status"),
        [
            ("valid, no warnings", "compiles and runs", "good"),
            ("valid, with warnings", "worth reading, not urgent", "plain"),
            ("Invalid and draft", "publishing is blocked", "bad"),
            ("Invalid and published", "executions stop at the fault", "bad"),
        ],
    ),
}

V["twilio/conversations-webhook-filters-empty"] = {
    "flow_intro": (
        "filters is an allowlist rather than a mute list, and one list feeds two "
        "webhooks. The past tense suffix is the only thing deciding whether an "
        "event goes to the post URL or the pre URL."
    ),
    "diagram_problem": D.chain(
        "tcfe-p",
        "A message added to a conversation while the webhook subscribes to nothing",
        "No delivery was attempted, so no delivery failed. There is no error code "
        "for this and the Debugger stays empty all day.",
        [
            ("URL configured", "post_webhook_url set"),
            ("Filters left empty", "the list names no events"),
            ("Message added", "conversation is fine"),
            ("Event matches nothing", "no request made"),
            ("App never called", "no error to look up"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tcfe-f",
        "Sorting a Conversations webhook configuration by what it can deliver",
        "A populated list missing the one event your handler branches on is the "
        "version that survives for months, because most of the integration works.",
        ("GET /v1/Configuration/Webhooks", "filters against the two URLs"),
        [
            ("Every needed event listed", "delivering", "good"),
            ("No URL at all", "the filters have nowhere to go", "plain"),
            ("Filters empty", "an allowlist naming nothing", "bad"),
            ("Wrong tense for the URL", "pre names, post webhook", "bad"),
        ],
    ),
}

V["twilio/conversations-webhook-limit"] = {
    "flow_intro": (
        "The count comes from meta.total rather than the length of the page, and "
        "the destinations are compared, because the ceiling is usually one "
        "integration registered twice rather than five that all belong there."
    ),
    "diagram_problem": D.chain(
        "tcwl-p",
        "A sixth webhook rejected on a conversation that already holds five",
        "The thing that breaks is not the thing that is wrong. The newest "
        "integration is refused, and it is the one with the least context about "
        "the five already there.",
        [
            ("Integrations add hooks", "one per conversation"),
            ("A create is retried", "duplicate, same URL"),
            ("Five slots used", "cap reached quietly"),
            ("Sixth create refused", "error 50361"),
            ("Newest deploy blamed", "culprit is elsewhere"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tcwl-f",
        "Sorting conversations by how many webhook slots are left and who holds them",
        "A duplicate below the cap is still a finding: both webhooks fire, so the "
        "endpoint has been called twice for every event since the retry.",
        ("Conversations, then their Webhooks", "meta.total and each destination"),
        [
            ("Slots left, no duplicates", "healthy", "good"),
            ("Four distinct hooks", "one create from failing", "plain"),
            ("Five, two the same URL", "a slot back for free", "bad"),
            ("Five distinct hooks", "move one to the account level", "bad"),
        ],
    ),
}

V["twilio/sync-webhook-url-invalid"] = {
    "flow_intro": (
        "Two failures share one symptom. The invalid URL raises 54051 and lands "
        "in the alerts; the suppressed callback raises nothing at all and is only "
        "visible as a boolean on the service."
    ),
    "diagram_problem": D.chain(
        "tsyw-p",
        "A Sync document changed over REST while the callback is switched off",
        "The URL is correct, HTTPS and reachable. It is simply not called for the "
        "one kind of change this architecture produces.",
        [
            ("Webhook URL set", "tested from a browser SDK"),
            ("Shipped", "server writes the documents"),
            ("REST write lands", "document changes"),
            ("Callbacks off for REST", "false by default"),
            ("Backend hears nothing", "and no error is raised"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tsyw-f",
        "Sorting Sync Services by whether their webhook can fire at all",
        "Whether the flag is a fault depends on where your writes come from, so "
        "the script is told rather than left to guess and report every service on "
        "the account.",
        ("GET /v1/Services plus the alerts", "webhook_url and the REST flag"),
        [
            ("https URL, REST included", "fires on every change", "good"),
            ("Flag off, SDK writes only", "correct as configured", "plain"),
            ("Empty or plain http URL", "rejected as 54051", "bad"),
            ("Flag off, server writes", "silent, with no error", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
