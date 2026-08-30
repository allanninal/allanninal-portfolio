#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch G.

Four notes that all point at a channel, drawn so that no two of them look like
the same picture. One is a fork in a code path: the same string travels down two
routes and only one of them refuses it. One is a state change nobody made a
request about, where every arrow succeeds and the traffic still stops. One never
reaches a channel at all and settles on a header instead, with one branch that
deliberately ends in a question rather than an answer. And one is a clock: a
name released, claimed again, and delivery resuming into the wrong room. Drawn
in Slack aubergine.

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

V["slack/channel-name-instead-of-id"] = {
    "flow_intro": (
        "The grammar settles most of this before a request is sent, which is "
        "why the fix branch is drawn as a sort rather than as a probe. The one "
        "network call exists to hand back the ID, and it only runs when "
        "something in the configuration still needs resolving."
    ),
    "diagram_problem": D.chain(
        "scnid-p",
        "One configured channel name travelling down two code paths",
        "Three features share one config value and only one of them breaks, "
        "which sends everybody to read the broken feature instead of the string "
        "all three of them load.",
        [
            ("Config says #alerts", "one string, three features"),
            ("chat.postMessage", "legacy name resolution"),
            ("conversations.history", "channel_not_found"),
            ("Digest still fine", "so the value looks correct"),
            ("Read path debugged", "the string never checked"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scnid-f",
        "Sorting each configured reference by its shape before any request",
        "The user ID has to leave the name bucket. It is the one shape here "
        "that produces no error at all: the message is delivered, to one "
        "person, and the channel stays silent.",
        ("Reference shape", "checked offline"),
        [
            ("Name in an ID slot", "one family accepts it", "bad"),
            ("User ID as channel", "a DM, delivered", "bad"),
            ("Permalink pasted", "the ID is inside it", "bad"),
            ("Two channels, one name", "never picked silently", "plain"),
            ("C prefixed ID", "every family accepts", "good"),
        ],
    ),
}

V["slack/archived-channel-target"] = {
    "flow_intro": (
        "Nothing in the problem chain is an error, which is the point: the ID "
        "resolves, the read succeeds, and the traffic stops anyway. The fix "
        "branch sorts targets against one swept inventory, and keeps the "
        "suggestion of a replacement room visibly weaker than the findings."
    ),
    "diagram_problem": D.chain(
        "scarc-p",
        "A channel archived during a reorganisation while an integration keeps sending",
        "Every reasonable health check passes here. The ID resolves, the info "
        "call succeeds, the bot is still a member. One boolean changed and no "
        "check was reading it.",
        [
            ("Reorg tidies up", "a dozen channels archived"),
            ("Sends refused", "is_archived"),
            ("Cron exits zero", "nobody reads the body"),
            ("Info still ok", "membership intact"),
            ("Alerts just stop", "silence pages nobody"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "scarc-f",
        "Sorting configured targets against one swept workspace inventory",
        "A target missing from the sweep is not archived, it is unreadable, and "
        "the two verdicts send a reader to two different screens. The successor "
        "is offered as a candidate, never as an instruction.",
        ("One sweep, archives kept", "targets against inventory"),
        [
            ("Archived target", "frozen, still resolves", "bad"),
            ("Not in the sweep", "a scope question", "bad"),
            ("Dated by last message", "when it went quiet", "plain"),
            ("No obvious successor", "offers nothing at all", "plain"),
            ("Live target", "accepts messages", "good"),
        ],
    ),
}

V["slack/private-channel-invisible"] = {
    "flow_intro": (
        "The detection never asks about the channel, because the channel is the "
        "one thing Slack will not discuss. It reads the grant off a response "
        "header and interprets that instead, and one branch of the sort ends in "
        "a question for a colleague rather than in a verdict."
    ),
    "diagram_problem": D.chain(
        "scpiv-p",
        "A private channel answering channel_not_found to a token without groups:read",
        "The error is a statement about the ID, and the ID is fine. Slack "
        "collapses no permission and no such channel into one answer so that "
        "the difference cannot be used to enumerate private rooms.",
        [
            ("Channel on screen", "ID copied from Slack"),
            ("Token has channels:read", "groups:read never asked for"),
            ("Info says not found", "not a permission error"),
            ("ID checked twice", "the ID was always right"),
            ("Afternoon gone", "the error named the wrong thing"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scpiv-f",
        "Reading the granted scope header instead of the error it produces",
        "No scope and no invitation look identical from outside and need "
        "opposite repairs, so they get separate rows. The last unresolved case "
        "is left unresolved on purpose.",
        ("The grant, off the header", "X-OAuth-Scopes"),
        [
            ("No groups:read", "absent, not empty", "bad"),
            ("Read without history", "lists, never reads", "bad"),
            ("Scope, no membership", "a person must invite", "plain"),
            ("Outside the visible set", "cannot be answered here", "plain"),
            ("Inside the visible set", "metadata readable", "good"),
        ],
    ),
}

V["slack/channel-renamed-hardcoded"] = {
    "flow_intro": (
        "The chain runs on a calendar rather than on a request: a name "
        "released, claimed again, and delivery quietly resuming. The fix branch "
        "ranks by who already knows, which is why a successful send to the "
        "wrong room sits above an outage that has been paging people all day."
    ),
    "diagram_problem": D.chain(
        "scrnh-p",
        "A channel name released by a rename and claimed by a different team",
        "The recovery is the dangerous half. Once somebody claims the freed "
        "name the calls succeed again, so the error disappears and the "
        "misdelivery does not.",
        [
            ("Two quiet years", "a name in an env var"),
            ("Team renames it", "the old name released"),
            ("Alerts stop", "channel_not_found"),
            ("Name claimed again", "by another team"),
            ("Delivery resumes", "into the wrong room"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scrnh-f",
        "Ranking configured references by whether anybody already knows",
        "A stale label beside a correct ID must never fail a deploy: the "
        "traffic was always going to the right place and only the comment is "
        "wrong. Flattening it into the failures is how the real finding gets "
        "ignored.",
        ("Stored value against today", "created versus config age"),
        [
            ("Resolves to a newer channel", "delivered, wrong room", "bad"),
            ("Resolves to nothing", "failing since rename day", "bad"),
            ("Renamed before", "a moving target", "plain"),
            ("Label beside the ID stale", "warn, never fail", "plain"),
            ("ID with a current label", "nothing can drift", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
