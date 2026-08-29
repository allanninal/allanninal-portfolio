#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch K.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

Every chain here breaks late on purpose. These four failures all happen after
Twilio has reached the handler, so the early steps are genuinely fine and the
picture has to show that.

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

V["twilio/webhook-signature-validation-403-behind-proxy"] = {
    "flow_intro": (
        "The script fetches alerts one at a time to read the response body, because "
        "the list blanks that field and the error code alone cannot tell a signature "
        "rejection from a 404 or a crash."
    ),
    "diagram_problem": D.chain(
        "tsig-p",
        "A legitimate Twilio request rejected by the app's own signature check",
        "Nothing along the way is broken. The proxy is doing its job and the "
        "validator is doing its job, on two different URLs.",
        [
            ("Twilio signs", "HMAC over the full URL"),
            ("Request sent", "https, public host"),
            ("Proxy forwards", "http, internal host"),
            ("App rebuilds URL", "different string, different HMAC"),
            ("403 to Twilio", "logged as 11200"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tsig-f",
        "Sorting 11200 alerts by what the endpoint actually returned",
        "The error code is the same for all four. Only the response body, which "
        "lives on the single alert fetch, tells them apart.",
        ("GET Alerts, then GET Alerts/{Sid}", "error_code plus response_body"),
        [
            ("Body names a signature", "the URL, rebuild it", "bad"),
            ("Bare 403 page", "a WAF in front, other owner", "bad"),
            ("Stack trace", "the app threw, not validation", "plain"),
            ("Empty body", "read the status and the logs", "plain"),
        ],
    ),
}

V["twilio/webhook-invalid-content-type-12300"] = {
    "flow_intro": (
        "The script reads the header rather than counting error codes, because a "
        "response with no Content-Type at all is reported as 502 Bad Gateway and "
        "never appears in a search for 12300."
    ),
    "diagram_problem": D.chain(
        "tctype-p",
        "Valid TwiML refused on its media type before the body is read",
        "The document is correct and Twilio never looks at it. The decision is "
        "made one header earlier.",
        [
            ("Twilio calls", "the webhook answers"),
            ("Handler builds TwiML", "well formed, correct"),
            ("Framework default", "Content-Type text/html"),
            ("Twilio dispatches", "not a TwiML media type"),
            ("12300, call ends", "body never parsed"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tctype-f",
        "Sorting endpoints by the Content-Type they actually sent",
        "Four states, four different files to edit. The empty one matters most, "
        "because the Debugger files it under a gateway error.",
        ("GET Alerts/{Sid}", "Content-Type from response_headers"),
        [
            ("text/xml or application/xml", "parsed as TwiML", "good"),
            ("text/html or json", "framework default, set it", "bad"),
            ("No header at all", "shows up as 502 instead", "bad"),
            ("An audio type", "a Play target, not TwiML", "plain"),
        ],
    ),
}

V["twilio/twiml-document-parse-failure-12100"] = {
    "flow_intro": (
        "The script sweeps warnings as well as errors, because 12200 schema "
        "validation is logged at warning level and an error only query reports the "
        "account as clean while calls skip a verb."
    ),
    "diagram_problem": D.chain(
        "tparse-p",
        "A call dropped by one blank line in front of the XML declaration",
        "The handler returned 200 and logged nothing. The refusal happens inside "
        "Twilio's parser, after the response left your process.",
        [
            ("Template renders", "TwiML is correct"),
            ("Header file emits", "one trailing newline"),
            ("Response sent", "200, looks healthy"),
            ("Parser stops", "nothing allowed before the declaration"),
            ("Caller hears an error", "12100, call ends"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tparse-f",
        "Sorting malformed TwiML by the first thing wrong with the bytes",
        "Ordered so the earliest byte wins. A document with a leading newline and "
        "an unclosed tag failed at the newline.",
        ("GET Alerts/{Sid}", "response_body plus alert_text"),
        [
            ("Whitespace or a BOM first", "commonest cause by far", "bad"),
            ("An HTML error page", "the handler threw", "bad"),
            ("A bare ampersand", "one customer name breaks it", "bad"),
            ("Parses here", "read the line and column", "plain"),
        ],
    ),
}

V["twilio/twiml-response-body-too-large-11750"] = {
    "flow_intro": (
        "The script judges what the body is rather than how long it is, because the "
        "stored copy of response_body is truncated and its length is a floor rather "
        "than a measurement."
    ),
    "diagram_problem": D.chain(
        "tbig-p",
        "A debug page returned where TwiML was expected, refused for its size",
        "The error names a size, so the hunt starts with the largest document the "
        "app can build. That document is usually innocent.",
        [
            ("Twilio calls", "the webhook answers"),
            ("Handler throws", "an ordinary exception"),
            ("Debug page renders", "source, locals, styling"),
            ("Over 64 kB", "refused on size"),
            ("Call drops", "11750 logged"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbig-f",
        "Sorting 11750 endpoints by what came back instead of TwiML",
        "Two causes with nothing in common: an exception to fix, or a document to "
        "split across Redirect hops.",
        ("GET Alerts/{Sid}", "response_body, measured in bytes"),
        [
            ("HTML or a stack trace", "the app threw, size is a symptom", "bad"),
            ("Real TwiML over the cap", "split it across Redirect hops", "bad"),
            ("Real TwiML under the cap", "stored copy is truncated", "plain"),
            ("Empty body", "reproduce it against the handler", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
