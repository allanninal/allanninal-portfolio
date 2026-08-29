#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch Y.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

Four of these five chains break at a step where nothing actually failed, which
is the point of the batch: a version pin honoured exactly as asked, a product
retired without changing a field, media stored precisely as configured, and an
error kept for thirty days and then not.

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

V["twilio/pinned-old-api-version"] = {
    "flow_intro": (
        "The script reads the account default as well as the numbers, because that "
        "one field decides what the next number bought on the account arrives "
        "pinned to, and repairing the numbers without it is a treadmill."
    ),
    "diagram_problem": D.chain(
        "tapiv-p",
        "A missing error_code traced back to a number bought in 2014",
        "Nothing fails anywhere along here. The number asked for the 2008 schema "
        "and Twilio served it, exactly as it has since the day it was bought.",
        [
            ("Number bought 2014", "api_version set at purchase"),
            ("Message sent", "from that one number"),
            ("Webhook built", "2008 schema, fewer fields"),
            ("error_code absent", "read as no error at all"),
            ("Dashboard says unknown", "a third of the chart"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tapiv-f",
        "Sorting numbers and the account default by the API version each asks for",
        "A pinned number with no handler is a real finding and not a live one, "
        "and a version nobody can read must never be counted as fine.",
        ("GET account and numbers", "api_version on each"),
        [
            ("On 2010-04-01", "current, leave it", "good"),
            ("Pinned, no handler", "a landmine, not a fire", "plain"),
            ("Pinned and wired up", "old schema on every webhook", "bad"),
            ("Account default is old", "next number arrives pinned", "bad"),
        ],
    ),
}

V["twilio/eol-programmable-chat-in-use"] = {
    "flow_intro": (
        "The script reads the Conversations services in the same run, because the "
        "same three Chat services mean one thing on an account that has never "
        "created a Conversations service and another on one that has twelve."
    ),
    "diagram_problem": D.chain(
        "tchat-p",
        "An end of life that changes nothing at all on the day it arrives",
        "No field flips, no header appears and no request starts failing. The "
        "only signal available is that the account is still calling it.",
        [
            ("EOL announced", "in a changelog"),
            ("Date passes", "nothing changes"),
            ("No error anywhere", "monitoring sees nothing"),
            ("API answers as before", "same 200, same shape"),
            ("Still in the SDK", "shipped in last year's app"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tchat-f",
        "Sorting an account by whether the migration started and what is left",
        "Both products present is the state most likely to be recorded "
        "internally as finished, which is why it needs its own sentence.",
        ("Chat and Conversations", "both lists, one run"),
        [
            ("No Chat services", "clear", "good"),
            ("Chat, no Conversations", "nothing has moved yet", "bad"),
            ("Both products present", "started, then stopped", "bad"),
            ("date_updated is old", "staleness, never traffic", "plain"),
        ],
    ),
}

V["twilio/eol-notify-service-in-use"] = {
    "flow_intro": (
        "The script counts bindings as well as services, because that is the "
        "difference between an outage nobody noticed and a deletion to schedule, "
        "and a sampled page answers it honestly as a floor."
    ),
    "diagram_problem": D.chain(
        "tnfy-p",
        "Push that stopped arriving with nothing on either side to show for it",
        "The REST surface outlived the product. A healthy push and a discarded "
        "one produce exactly the same silence in your own logs.",
        [
            ("Notify EOL passes", "31 December 2025"),
            ("Service still listed", "API answers as before"),
            ("Handset gets nothing", "no delivery receipt exists"),
            ("Push sent", "your code gets a response"),
            ("Nobody reports it", "users never knew it was coming"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tnfy-f",
        "Sorting Notify services by what is still registered against them",
        "Not checked has to stay not checked. An account called abandoned "
        "because nobody passed a flag is the worst line in this report.",
        ("Services plus one page", "of bindings for each"),
        [
            ("No Notify services", "clear", "good"),
            ("Bindings not read", "unknown, and say so", "plain"),
            ("Bindings registered", "devices pointed at nothing", "bad"),
            ("Nothing bound", "cleanup to schedule", "plain"),
        ],
    ),
}

V["twilio/recordings-not-encrypted"] = {
    "flow_intro": (
        "The classifier sorts before it judges, because a mix of encrypted and "
        "unencrypted recordings is two opposite findings and only the ordering "
        "tells you which of them you have."
    ),
    "diagram_problem": D.chain(
        "trenc-p",
        "Four years of recordings readable by anything holding account credentials",
        "Nothing here fails. Encryption is a second switch in a second place, "
        "and the recordings record and play identically without it.",
        [
            ("Recording enabled", "one switch, years ago"),
            ("Encryption never on", "a different switch"),
            ("Files stored", "encryption_details absent"),
            ("Auditor asks", "encrypted at rest or not"),
            ("Answer is since when", "not yes and not no"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "trenc-f",
        "Sorting a date ordered sample by where encryption starts or stops",
        "Enabling encryption does not reach backwards, so the finding lives at "
        "the boundary rather than anywhere in the count.",
        ("Recordings newest first", "encryption_details per row"),
        [
            ("All encrypted", "the clean answer", "good"),
            ("None encrypted", "never switched on", "bad"),
            ("Newest encrypted only", "backlog stays in the clear", "plain"),
            ("Newest not encrypted", "switched off, still growing", "bad"),
        ],
    ),
}

V["twilio/no-error-log-subscription"] = {
    "flow_intro": (
        "The event types live on a subresource, so the script fetches "
        "SubscribedEvents for every subscription: the list response cannot tell a "
        "busy pipeline from a useful one."
    ),
    "diagram_problem": D.chain(
        "telog-p",
        "A postmortem for an hour that no longer exists anywhere",
        "Nothing was lost by accident. Getting errors out of Twilio is opt in, "
        "and an account is created with nothing subscribed to anything.",
        [
            ("Error logged", "kept in the Debugger"),
            ("Nothing subscribed", "no copy ever leaves"),
            ("30 days pass", "the window rolls on"),
            ("Record is gone", "no row in the warehouse"),
            ("Postmortem stalls", "the question cannot be answered"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "telog-f",
        "Sorting an account by what its subscriptions actually carry",
        "The Debugger webhook has no read API, so this check can prove that "
        "coverage exists and can never prove that it does not.",
        ("Subscriptions and types", "plus the sink behind each"),
        [
            ("Error logs, active sink", "covered", "good"),
            ("No subscriptions at all", "check the Debugger webhook", "bad"),
            ("Subscriptions, no errors", "a pipeline without errors", "bad"),
            ("Error logs, dead sink", "subscribed, not delivering", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
