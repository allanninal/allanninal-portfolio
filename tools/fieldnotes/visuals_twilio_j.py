#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch J.

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

V["twilio/no-usage-trigger-configured"] = {
    "flow_intro": (
        "The script judges the triggers as a set rather than one at a time, because "
        "an account with six triggers and no recurring price cap is exactly as "
        "unwatched as an account with none."
    ),
    "diagram_problem": D.chain(
        "tusg-p",
        "A pumping burst running to the end of the balance with nothing watching",
        "Every send is valid, every status callback says delivered, and no alarm "
        "exists to notice the rate at which money is leaving.",
        [
            ("Account opened", "zero usage triggers"),
            ("Signup form abused", "OTPs to premium ranges"),
            ("Sends succeed", "delivered, no errors"),
            ("Nothing watching", "no threshold, no webhook"),
            ("Balance gone", "20005 or an invoice"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tusg-f",
        "Sorting an account's Usage Triggers by whether they can still alarm",
        "A fired one-shot and a trigger with no callback both read as configured "
        "in a list. Neither will reach anybody at three on a Saturday morning.",
        ("GET Usage/Triggers.json", "recurring, callback_url, trigger_by"),
        [
            ("Recurring price cap", "covered, leave it", "good"),
            ("Price cap on one category", "money leaves elsewhere", "plain"),
            ("One shot, already fired", "the fuse blew long ago", "bad"),
            ("No triggers at all", "nothing is watching", "bad"),
        ],
    ),
}

V["twilio/auth-token-used-instead-of-api-key"] = {
    "flow_intro": (
        "The script reads which keys exist, and then reads the one thing the API "
        "never reports: the basic-auth username it authenticated with. An account "
        "SID in that position means the password beside it was the auth token."
    ),
    "diagram_problem": D.chain(
        "tcred-p",
        "One leaked auth token taking every service down at the same moment",
        "Nothing was broken before the rotation. The blast radius is the whole "
        "integration, which is why the rotation keeps getting postponed.",
        [
            ("One secret", "auth token everywhere"),
            ("It leaks", "a log line, a screenshot"),
            ("Rotate it", "account wide, instant"),
            ("Every service 20003", "no per service fallback"),
            ("Signatures fail too", "same value signs webhooks"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tcred-f",
        "Sorting a Twilio account by which credential its services actually hold",
        "The username is the tell. SK is a key you can revoke on its own; AC is "
        "the account SID, and the only password that pairs with it is the token.",
        ("Keys, services and the username", "what exists, and what this run used"),
        [
            ("A key per workload", "revocable one at a time", "good"),
            ("Fewer keys than services", "a shared credential", "plain"),
            ("No keys on the account", "the token is doing the work", "bad"),
            ("This run used AC plus token", "proof, not inference", "bad"),
        ],
    ),
}

V["twilio/stale-or-orphaned-api-keys"] = {
    "flow_intro": (
        "There is no last-used field on a Twilio key, so the script cannot ask "
        "which keys are live. It asks whether a human can account for them, which "
        "makes friendly_name the control and an empty name the finding."
    ),
    "diagram_problem": D.chain(
        "tkeys-p",
        "An unnamed API key surviving every review because deleting it is unsafe",
        "The key is a full privilege path into the account, and nothing in the "
        "API can tell you what would break if it went away.",
        [
            ("Key created", "one off, left unnamed"),
            ("Owner leaves", "nobody knows its purpose"),
            ("Review reaches it", "no last used field"),
            ("Deleting is unsafe", "kills REST and access tokens"),
            ("It survives", "another year, still live"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tkeys-f",
        "Sorting API keys by whether a person can be attached to them",
        "date_updated moves when the name is edited and never when the key is "
        "used, so a recent rename is not evidence that anything still needs it.",
        ("GET Keys.json", "name, date_created, date_updated"),
        [
            ("Named and inside the window", "leave it", "good"),
            ("Date will not parse", "RFC 2822, not ISO", "plain"),
            ("Named but years old", "rotate on a schedule", "bad"),
            ("No name or a placeholder", "nobody can retire it", "bad"),
        ],
    ),
}

V["twilio/regulatory-bundle-expiring"] = {
    "flow_intro": (
        "The classifier keys on valid_until, because that field is the entire "
        "warning. A null value is a regulation with no renewal and a healthy "
        "bundle, and reporting it as expired buries the ones that matter."
    ),
    "diagram_problem": D.chain(
        "tbund-p",
        "German numbers stopping eighteen months after the bundle was approved",
        "No deploy, no ticket, no human decision. The bundle simply reached its "
        "date and the approval it carried stopped being true.",
        [
            ("Bundle approved", "documents accepted once"),
            ("Numbers work", "eighteen quiet months"),
            ("valid_until passes", "nobody was polling it"),
            ("Bundle auto rejected", "no ticket, no email"),
            ("Numbers non compliant", "and subject to loss"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbund-f",
        "Sorting regulatory bundles by the date their approval stops being true",
        "Renewal takes weeks: new documents, an item assignment, a resubmission "
        "and a review. The horizon has to be longer than that process.",
        ("GET RegulatoryCompliance/Bundles", "sorted ascending on valid-until"),
        [
            ("Approved, date far off", "current", "good"),
            ("Approved, no valid_until", "no re-attestation needed", "good"),
            ("Inside the horizon", "start the renewal now", "bad"),
            ("Date already passed", "the numbers are exposed", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
