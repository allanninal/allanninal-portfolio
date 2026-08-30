#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch A.

All four notes share one spine, so all four problem chains do too: a call that
returns 200, a body nobody reads, and an outcome that never raises anywhere. The
fix is a branch every time, because each script sorts what it found into states
that need different people to act on them. Drawn in Slack aubergine.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/http-200-ok-false"] = {
    "flow_intro": (
        "The script keeps the status line and the parsed body side by side for "
        "every probe, because the whole finding is the gap between them: one says "
        "the request arrived, the other says whether anything happened."
    ),
    "diagram_problem": D.chain(
        "sokf-p",
        "A Slack call that returns 200 and does nothing at all",
        "Nothing in this path throws. The client was built to read the status "
        "line, and the status line is telling the truth about the wrong thing.",
        [
            ("Call sent", "bearer token attached"),
            ("Slack answers 200", "request parsed"),
            ("Body says ok false", "error in the JSON"),
            ("Client reads status", "200 means done"),
            ("Logged as delivered", "no alert exists"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sokf-f",
        "Sorting responses by the body rather than by the status line",
        "A warning on a successful call and a 200 with no ok field are different "
        "findings, and collapsing either into success is how this hides.",
        ("Status and parsed body", "kept for every probe"),
        [
            ("ok is true", "the only success signal", "good"),
            ("ok true, warning set", "not fatal, still news", "plain"),
            ("ok false", "200 carrying an error", "bad"),
            ("no ok field", "something else replied", "bad"),
        ],
    ),
}

V["slack/bot-not-in-channel"] = {
    "flow_intro": (
        "The script reads is_archived before is_member, because an archived "
        "channel refuses members too and reporting it as a membership gap sends "
        "somebody to invite a bot into a room that accepts nothing."
    ),
    "diagram_problem": D.chain(
        "sbnc-p",
        "An app installed to the workspace and invited to no channel",
        "Every step is configured correctly. The one that is missing was never "
        "part of the install flow and nothing in the app config mentions it.",
        [
            ("App installed", "scopes granted"),
            ("Token works", "auth.test is happy"),
            ("Never invited", "install joins nothing"),
            ("Post returns 200", "ok false, not_in_channel"),
            ("Queue marks it sent", "message is gone"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sbnc-f",
        "Sorting target channels by what would actually let the bot in",
        "Public and private need different people: one is an API call the app "
        "can make, the other is a human who is already in the room.",
        ("conversations.info", "per target channel"),
        [
            ("is_member true", "nothing to do", "good"),
            ("Public, not a member", "join or invite", "bad"),
            ("Private, not a member", "a human must invite", "bad"),
            ("Archived", "accepts nobody at all", "bad"),
        ],
    ),
}

V["slack/missing-scope-on-read"] = {
    "flow_intro": (
        "The script reads X-OAuth-Scopes off the same response it judges, so the "
        "granted list and the refusal always describe one token. Comparing a "
        "cached list against a live call is how the wrong scope gets added."
    ),
    "diagram_problem": D.chain(
        "smsr-p",
        "A scope added to the app config and never reaching the live token",
        "The configuration is correct and the token is old. Nothing connects the "
        "two until somebody runs the install flow again.",
        [
            ("Scope added in config", "requested at next install"),
            ("App not reinstalled", "old token still deployed"),
            ("Read call refused", "missing_scope"),
            ("needed and provided", "both named in the body"),
            ("Body never read", "200 hid the answer"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "smsr-f",
        "Sorting refusals into the ones a scope would actually fix",
        "A credential error wearing a permission error's clothes is the expensive "
        "one: it sends a team through a reinstall that changes nothing.",
        ("Probe plus scope header", "read from one response"),
        [
            ("ok is true", "the grant covers it", "good"),
            ("missing_scope", "needed is an OR list", "bad"),
            ("invalid_auth and kin", "the token, not the grant", "bad"),
            ("Any other error", "not a scope finding", "plain"),
        ],
    ),
}

V["slack/pagination-not-followed"] = {
    "flow_intro": (
        "The script probes with the page size your application uses, then walks "
        "the whole list once. The delta between those two numbers is the finding, "
        "because a cursor on its own persuades nobody."
    ),
    "diagram_problem": D.chain(
        "spnf-p",
        "A list read one page deep and treated as the whole workspace",
        "This code was correct when it was written and stayed correct until the "
        "workspace crossed one hundred. No deploy marks the day it broke.",
        [
            ("List call sent", "limit defaults to 100"),
            ("Slack returns a page", "ok is true"),
            ("next_cursor is set", "more data behind it"),
            ("Array read, loop absent", "cursor ignored"),
            ("Four fifths dropped", "no error anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "spnf-f",
        "Sorting first pages by the cursor rather than by their length",
        "Page length is the heuristic that fails here: a short page can have more "
        "behind it, and a full one can be the end.",
        ("First page plus cursor", "then a bounded full walk"),
        [
            ("Full page, cursor set", "the truncation signature", "bad"),
            ("Short page, cursor set", "short is not last", "bad"),
            ("Full page, no cursor", "complete, for today", "plain"),
            ("Short page, no cursor", "the whole set", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
