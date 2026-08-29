#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch AB.

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

V["twilio/dial-number-unsupported-or-invalid-13224"] = {
    "flow_intro": (
        "The script tests the destination strictly rather than tidying it first, "
        "because a number that only becomes E.164 after the audit cleans it is a "
        "number the application should have cleaned and did not."
    ),
    "diagram_problem": D.chain(
        "t13224-p",
        "A Dial leg refused for an unsupported destination while the call completes",
        "The parent call is never abnormal. It runs its TwiML, takes the action "
        "URL and ends as completed, so counting call status finds nothing.",
        [
            ("Row read", "national format in the CRM"),
            ("TwiML built", "Dial Number, no validation"),
            ("Twilio refuses", "13224, often at warning"),
            ("Leg never rings", "no child call created"),
            ("Action URL runs", "sounds like no answer"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "t13224-f",
        "Sorting refused Dial destinations by what is actually wrong with them",
        "An inbound forwarding call cannot answer this question at all: its `to` "
        "is your own number, and the dial target is only on the single alert.",
        ("Alerts at both levels", "joined to the Call resource"),
        [
            ("Strict E.164, unknown", "check it with Lookups", "plain"),
            ("Inbound leg", "target not on the record", "plain"),
            ("No plus, or punctuated", "never normalised", "bad"),
            ("Premium or special range", "unsupported, not invalid", "bad"),
        ],
    ),
}

V["twilio/amd-machine-answer-misrouting"] = {
    "flow_intro": (
        "The script counts only the calls detection actually graded. Leaving the "
        "unanswered and undetected ones in the denominator is what produces a "
        "reassuring machine share on a campaign that is failing."
    ),
    "diagram_problem": D.chain(
        "tamd-p",
        "A person classified as an answering machine and dropped into a voicemail flow",
        "Nothing here is an error. Your flow branched correctly on the value it "
        "was given, and the value was wrong.",
        [
            ("Call answered", "a person says hello"),
            ("Detection decides", "a few seconds of audio"),
            ("machine_start", "slow greeting, noisy line"),
            ("Voicemail branch", "drop starts playing"),
            ("Caller hangs up", "billed, completed"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tamd-f",
        "Sorting an answering machine distribution by which repair it points at",
        "unknown and machine_start are different faults with different levers, "
        "so a report that adds them together names neither.",
        ("answered_by tallied", "machine_start split by duration"),
        [
            ("Human majority", "detection is working", "good"),
            ("Too few graded calls", "widen the window", "plain"),
            ("unknown over threshold", "detection timing out", "bad"),
            ("Machines, short calls", "humans in the drop", "bad"),
        ],
    ),
}

V["twilio/recording-absent-with-error-code"] = {
    "flow_intro": (
        "The script filters on status first and reads error_code afterwards, "
        "because that field is populated only on the absent rows. Scanning for it "
        "across everything makes it look unused."
    ),
    "diagram_problem": D.chain(
        "trabs-p",
        "A recording row created, stored and referenced while the media never arrives",
        "The row is real from the moment recording is requested, which is early "
        "enough to satisfy anything that only checks that it exists.",
        [
            ("Recording asked for", "resource created at once"),
            ("Sid persisted", "your table says recorded"),
            ("Media never lands", "status becomes absent"),
            ("Call completes", "eleven minutes, normal"),
            ("Audit, weeks later", "media URL 404s"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "trabs-f",
        "Sorting recordings by whether the audio behind the row exists",
        "A completed recording of zero duration passes every check for presence "
        "and holds nothing, so it belongs in the same report as the absent ones.",
        ("Recordings over a window", "status, error_code, source"),
        [
            ("Completed with media", "there when asked for", "good"),
            ("Processing", "a moment, not a fault", "plain"),
            ("Absent with error_code", "no audio was produced", "bad"),
            ("Completed, zero seconds", "plays, contains nothing", "bad"),
        ],
    ),
}

V["twilio/voice-dialing-permissions-blocked"] = {
    "flow_intro": (
        "The script resolves destinations to countries by longest dialling prefix "
        "and keeps the ties. Every North American Numbering Plan country answers "
        "to 1, so a match there is a group rather than an answer."
    ),
    "diagram_problem": D.chain(
        "tdperm-p",
        "A call refused because the account may not dial that country",
        "The error names the number, so the number is what gets investigated. It "
        "was never the subject.",
        [
            ("Customer signs up", "in a new country"),
            ("Number validated", "Lookup says valid"),
            ("Call created", "same code as always"),
            ("Permissions refuse", "21215 or 13227"),
            ("Number re-checked", "wrong thing, twice"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tdperm-f",
        "Sorting dialing permissions by whether they are blocking traffic you have",
        "Inheritance is checked separately, because enabling a country on the "
        "parent does nothing for a subaccount when the flag is off.",
        ("Countries plus your traffic", "and the Settings resource"),
        [
            ("Enabled, dialling", "permitted", "good"),
            ("Disabled, never dialled", "context, not a finding", "plain"),
            ("Disabled, refusals seen", "an outage in a live market", "bad"),
            ("Inheritance off", "subaccounts start closed", "bad"),
        ],
    ),
}

V["twilio/high-risk-dialing-permissions-open"] = {
    "flow_intro": (
        "This is the same countries listing as the companion note, read the other "
        "way round: not which legitimate destinations are blocked, but which "
        "expensive ones are still reachable."
    ),
    "diagram_problem": D.chain(
        "thrisk-p",
        "Toll fraud running against ranges that were never switched off",
        "Every call in this chain succeeds. There is no failed request to find "
        "afterwards, only minutes that are already billed.",
        [
            ("Account upgraded", "trial limits lifted"),
            ("High risk left on", "nothing prompts a decision"),
            ("Credential leaks", "dialer, SIP, click to call"),
            ("Premium range dialled", "overnight, at concurrency"),
            ("Found on the invoice", "money already shared out"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "thrisk-f",
        "Sorting countries by which high risk classes are reachable from the account",
        "Low risk off with high risk on is the state nobody configures on "
        "purpose, and it says the three switches were never read together.",
        ("Countries, served set", "plus calls and price"),
        [
            ("Both classes closed", "not reachable", "good"),
            ("Open in a served market", "decide, then narrow", "plain"),
            ("Open, outside the market", "carried for no return", "bad"),
            ("Open and already dialled", "check what placed them", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
