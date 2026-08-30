#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch M.

Four notes about delivery, drawn so that no two of them are the same picture.
One has a tail on the end that is not a failure but a wasted repair, because
the thing everybody reaches for here changes nothing. One is a chain in which
nothing goes wrong at all until the box where nothing was ever configured, and
the last step is an absence rather than an error. One has its cause three steps
and several months before its symptom. And one goes red at the second box,
because the mistake is an assumption made while the code still worked. Drawn in
Slack aubergine.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/accesslimited-ip-allowlist"] = {
    "flow_intro": (
        "The only chain in this section whose last box is not a consequence "
        "but a repair that did not work. Nothing in the first three steps is a "
        "mistake and nothing was deployed, which is why the investigation "
        "starts by reading a diff with nothing in it. The fix branch has two "
        "red rows because two different error strings mean the same thing "
        "here, and the second one is the expensive one."
    ),
    "diagram_problem": D.chain(
        "skaipl-p",
        "A working app refused by network origin after the egress address moved",
        "The token is valid, the scopes are right and the code is unchanged. "
        "What changed is the address the request left from, which belongs to "
        "the platform rather than to the application.",
        [
            ("Token valid", "scopes correct"),
            ("Cluster scaled", "new NAT gateway"),
            ("accesslimited", "refused by origin"),
            ("Token rotated", "twice, for safety"),
            ("Still refused", "nothing was wrong with it"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skaipl-f",
        "One token run from two networks, with the observed egress address recorded",
        "A single failing call is compatible with a bad credential. The same "
        "token succeeding from one address and refused from another is "
        "compatible with one thing only, which is why the comparison is the "
        "whole proof.",
        ("One token, two networks", "and the address it left from"),
        [
            ("accesslimited here, ok there", "an IP restriction, proved", "bad"),
            ("invalid_auth here, ok there", "the allowlist in disguise", "bad"),
            ("Refused from both", "ask for the current ranges", "plain"),
            ("Same failure everywhere", "the credential after all", "plain"),
            ("Inside a supplied range", "this network is not it", "good"),
        ],
    ),
}

V["slack/no-event-subscriptions"] = {
    "flow_intro": (
        "Every box in this chain is green except one, and the one that is not "
        "is an empty list rather than an error. The last step is an absence: "
        "no request, no log line, nothing to search for, which is what makes "
        "this the hardest of the four to file. The fix branch keeps a read "
        "apart from a reading, and the two plain rows are both refusals to "
        "conclude."
    ),
    "diagram_problem": D.chain(
        "sknesb-p",
        "An app that is installed, scoped and present, and was never subscribed to anything",
        "The scope makes the event available. It does not turn it on. Those "
        "are two screens and two steps, and every screen a developer thinks to "
        "open is the green one.",
        [
            ("Scope added", "app_mentions:read"),
            ("App installed", "ok: true"),
            ("Nothing subscribed", "bot_events is empty"),
            ("Bot invited", "member of the channel"),
            ("Handler never called", "no logs to read"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sknesb-f",
        "The subscription list held against the grant, with reply history as corroboration",
        "An unreadable manifest is not an empty one. Keeping those apart is "
        "the difference between a fact and a reading, and only one of them "
        "should send somebody to change a configuration.",
        ("bot_events and the grant", "plus who has replied"),
        [
            ("bot_events is empty", "read, not inferred", "bad"),
            ("Never replied, manifest unread", "a reading, not a fact", "bad"),
            ("Replied, then a cliff", "a different note entirely", "plain"),
            ("Nobody addressed it", "silence is correct", "plain"),
            ("Subscribed and answering", "nothing to do", "good"),
        ],
    ),
}

V["slack/event-scope-mismatch"] = {
    "flow_intro": (
        "The cause here is three steps and several months away from the "
        "symptom, and the two are joined by a reinstall that nobody connected "
        "to either of them. The chain ends on a misattribution rather than on "
        "the failure, because the part of the system that varies is the "
        "channel type and that is where the search goes. The fix branch is a "
        "two by two: two switches, four states, and only one of them is this "
        "note."
    ),
    "diagram_problem": D.chain(
        "skevsm-p",
        "A scope trimmed in a security pass, and one event that stops arriving at the next install",
        "There is no artefact anywhere. Not a missing_scope, because nobody "
        "called a method; not a delivery failure, because there was no "
        "delivery. Only a subscription that has never produced traffic.",
        [
            ("Installed broad", "groups:history granted"),
            ("Security pass", "the scope is trimmed"),
            ("Reinstall", "months later"),
            ("message.groups stops", "no error anywhere"),
            ("Blamed on private channels", "membership audited twice"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skevsm-f",
        "Subscribed events and granted scopes as two independent switches",
        "Subscription and scope do not imply each other, so there are four "
        "states rather than two. Reporting the middle two as one thing "
        "produces the wrong repair half the time.",
        ("Subscribed against granted", "two switches, four states"),
        [
            ("Subscribed, scope absent", "never sent, never errors", "bad"),
            ("And handled in code", "a feature that never ran", "bad"),
            ("Scope held, not subscribed", "the note next door", "plain"),
            ("Event not in the table", "checked by hand", "plain"),
            ("Both switches on", "delivered", "good"),
        ],
    ),
}

V["slack/message-subtypes-ignored"] = {
    "flow_intro": (
        "This chain goes red at the second box, earlier than the other three, "
        "because the mistake is an assumption made while the code still "
        "worked perfectly. Everything after it is correct behaviour acting on "
        "a wrong premise. The fix branch is a lookup rather than a diagnosis, "
        "and one of its plain rows is a row this note deliberately declines to "
        "own."
    ),
    "diagram_problem": D.chain(
        "skmsti-p",
        "A four line handler meeting a channel where people join, edit and delete",
        "Nothing errors. Every one of these payloads is a valid message event "
        "delivered correctly, and the handler processes each of them without "
        "complaint, which is why the symptom surfaces as a data problem.",
        [
            ("Four line handler", "reads event.text"),
            ("Every message is new", "subtype never read"),
            ("Real channel", "joins, edits, file shares"),
            ("Replies to an edit", "archives a deletion"),
            ("Filed as a data bug", "months of rows"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skmsti-f",
        "One page of history sorted by subtype, and where each one keeps its text",
        "The useful column is not the subtype but the field the content is "
        "actually in. message.text for an edit, previous_message.text for a "
        "deletion, files for a share.",
        ("subtype, and where the text is", "one page of history"),
        [
            ("message_changed", "the text is at message.text", "bad"),
            ("channel_join, channel_leave", "text a matcher will match", "bad"),
            ("bot_message", "the echo loop note owns it", "plain"),
            ("Edit too close to the post", "not attributable", "plain"),
            ("No subtype, no edited block", "a person, saying something", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
