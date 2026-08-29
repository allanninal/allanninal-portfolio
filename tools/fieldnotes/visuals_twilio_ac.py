#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch AC.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

Four of these five chains break at a step that returned a success. A setting
saved and stored, a number accepted and normalised nowhere, a document parsed
and then quietly trimmed, a template approved in March by somebody who has since
changed their mind.

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

V["twilio/verify-lookup-disabled"] = {
    "flow_intro": (
        "The script reads both booleans together, because the setting with the "
        "obvious name is the one that does nothing on its own: the landline skip "
        "is implemented by the Lookup that lookup_enabled authorises."
    ),
    "diagram_problem": D.chain(
        "tvlk-p",
        "A verification sent into a landline because the guard could not run",
        "Nothing here returns an error. The service saved the setting, Verify "
        "accepted the start, and the SMS was priced and sent.",
        [
            ("Skip landlines set", "saved, shown back to you"),
            ("lookup_enabled false", "the default, per service"),
            ("Verification starts", "no line type read"),
            ("SMS to a landline", "billed in full"),
            ("Attempt expires", "no 60205 anywhere"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tvlk-f",
        "Sorting Verify Services by the two settings that decide the landline skip",
        "Four combinations, three of them wrong in different ways. Reading "
        "either field alone gives a green tick to the one that costs money.",
        ("GET Verify Services", "lookup_enabled and skip_sms_to_landlines"),
        [
            ("Both true", "line type checked", "good"),
            ("Both false, no traffic", "fix before launch", "plain"),
            ("Lookup on, skip off", "you pay and still send", "bad"),
            ("Skip on, lookup off", "a guard that never runs", "bad"),
        ],
    ),
}

V["twilio/lookup-invalid-or-uncovered-number"] = {
    "flow_intro": (
        "The script screens the shape locally before spending a Lookup, because "
        "a string with letters in it is unsendable before Twilio is involved and "
        "the paid request belongs on the numbers where the answer is unknown."
    ),
    "diagram_problem": D.chain(
        "tlkv-p",
        "A contact row stored in national format failing one send at a time",
        "There is no batch to look at. Each row fails alone, months apart, "
        "inside whatever job happened to be sending that day.",
        [
            ("Number typed in 2016", "no E.164 anywhere"),
            ("Stored verbatim", "brackets, spaces, no plus"),
            ("Send attempted", "one row, one job"),
            ("21211 at request time", "often no Message row"),
            ("Retried and swallowed", "nothing aggregates it"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tlkv-f",
        "Sorting stored numbers by what Lookup says about each one",
        "Valid and reachable are different questions, and a number can be both "
        "and still be stored in a form your code will send verbatim.",
        ("Local shape check, then Lookup", "valid, validation_errors, phone_number"),
        [
            ("Valid and normalised", "leave the row alone", "good"),
            ("Valid, stored differently", "write back Twilio's form", "plain"),
            ("valid is false", "correct or quarantine", "bad"),
            ("404 or 60600", "unreachable, not misformatted", "bad"),
        ],
    ),
}

V["twilio/webhook-http-retrieval-failure-11200"] = {
    "flow_intro": (
        "The script attributes every failing URL to a handler before it judges "
        "the alert, because the same 11200 is a lost receipt on one endpoint and "
        "a dropped call on another, and the alert does not say which."
    ),
    "diagram_problem": D.chain(
        "t11ri-p",
        "A caller dropped because the TwiML fetch returned a 500",
        "Inbound has no retry. The fallback URL is the only second chance, and "
        "on this number it was never set.",
        [
            ("Caller dials", "call reaches Twilio"),
            ("Twilio fetches voice_url", "15 seconds, one attempt"),
            ("Handler returns 500", "logged as 11200"),
            ("No fallback set", "nothing to execute"),
            ("Error message, hangup", "filed as a receipt bug"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t11ri-f",
        "Sorting 11200 endpoints by which handler they are and what stands behind them",
        "A fallback that is itself returning non 2xx is the worst finding in the "
        "run, and it plays no primary role, so it is easy to file as unknown.",
        ("Alerts joined to numbers and services", "roles per endpoint"),
        [
            ("A status callback URL", "a receipt, another note", "good"),
            ("Not configured anywhere", "TwiML App or Studio", "plain"),
            ("Primary, no fallback", "the call is dropped", "bad"),
            ("The fallback itself", "nothing left behind it", "bad"),
        ],
    ),
}

V["twilio/twiml-schema-validation-warning-12200"] = {
    "flow_intro": (
        "The script sweeps LogLevel=warning, which is the whole trick: 12200 "
        "never appears in an error-only query, so an account can carry it for "
        "months with every dashboard reading green."
    ),
    "diagram_problem": D.chain(
        "t12sv-p",
        "A Gather that submits after one digit because numDigits was lower case",
        "The document is well formed and the call completes. Only the attribute "
        "was dropped, and only a warning records it.",
        [
            ("Template renders", "numdigits, lower case"),
            ("Webhook returns 200", "valid XML"),
            ("Parser accepts it", "so no 12100"),
            ("Schema drops the attribute", "12200 at warning"),
            ("Gather uses its default", "bug filed against your app"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t12sv-f",
        "Sorting 12200 endpoints by what the document Twilio received actually says",
        "SSML inside Say is lower case on purpose, so the scan exempts it. One "
        "false positive on a healthy document and nobody runs this again.",
        ("Warning sweep, then the response body", "scanned against the vocabulary"),
        [
            ("Nothing found", "read line and column", "plain"),
            ("Root is not Response", "every document needs it", "bad"),
            ("Verb differs only in case", "skipped silently", "bad"),
            ("camelCase attribute wrong", "verb runs on its default", "bad"),
        ],
    ),
}

V["twilio/whatsapp-content-template-rejected"] = {
    "flow_intro": (
        "The script reads the approval per template and counts the four WhatsApp "
        "error codes separately, because rejected, paused, disabled and the 24 "
        "hour window are four repairs that look like one outage."
    ),
    "diagram_problem": D.chain(
        "twact-p",
        "An approved template paused by Meta, and the freeform fallback failing too",
        "Nothing on your side changed. The state that decides delivery is edited "
        "by a third party and revoked without a notification.",
        [
            ("Template approved", "months of clean sends"),
            ("Recipients report it", "feedback reaches Meta"),
            ("Status becomes paused", "63041 on every send"),
            ("Code falls back to text", "worked in testing"),
            ("63016 outside the window", "two codes, one feature"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "twact-f",
        "Sorting WhatsApp templates by approval status and by what the alerts show",
        "An approved template on an account logging 63016 is a bug in the "
        "sending code, and resubmitting the template would fix nothing.",
        ("GET Content and ApprovalRequests", "plus the four codes in Alerts"),
        [
            ("Approved, no 63016", "sendable", "good"),
            ("Pending review", "not usable yet", "plain"),
            ("Rejected or disabled", "rewrite and resubmit", "bad"),
            ("Approved, 63016 logged", "your code, not the template", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
