#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch I.

Four notes that all end with a message not landing, drawn so that no two of them
read as one picture. One is a policy that belongs to the workspace rather than
to the channel, where the investigation walks away from the answer and towards
the OAuth screen. One is a hunt through a fixed grant for a permission that was
never in the grant at all. One is a mode chosen once, years ago, meeting a
channel that does it the other way. And one is the odd chain in this section
where no arrow fails: the sends all succeed, and that is the finding. Drawn in
Slack aubergine.

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

V["slack/general-channel-restricted"] = {
    "flow_intro": (
        "The chain is drawn as an investigation walking away from the answer: "
        "the refusal is real, the surface that reported it mangled the body, "
        "and every subsequent step is spent on a grant that has nothing to do "
        "with it. The fix branch sorts on one boolean, and gives the channel "
        "that merely carries the name a row of its own."
    ),
    "diagram_problem": D.chain(
        "scgen-p",
        "An integration pointed at the default channel and refused after the workspace locked it",
        "The webhook is one of the few Slack surfaces that answers with a real "
        "status code and a body that is not JSON, so the client that parses "
        "everything reports a permissions failure as a broken connection.",
        [
            ("Wired up on a Friday", "posts to #general"),
            ("Workspace grows", "admin locks the default"),
            ("403, plain text body", "not JSON at all"),
            ("Filed as a network bug", "nothing could parse it"),
            ("Scopes added twice", "no scope governs this"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scgen-f",
        "Sorting configured targets on the is_general flag rather than on the channel name",
        "The renamed default and the channel that inherited its name are "
        "separate rows on purpose. An audit that greps configuration for the "
        "word general flags the harmless one and misses the restricted one, in "
        "the same pass.",
        ("The flag, not the name", "is_general"),
        [
            ("Target is the default", "the whole workspace", "bad"),
            ("Bare restricted_action", "two policies, one string", "bad"),
            ("#general is not the default", "the name was reclaimed", "plain"),
            ("Grid has several", "one default per workspace", "plain"),
            ("Purpose built channel", "an audience you chose", "good"),
        ],
    ),
}

V["slack/read-only-channel"] = {
    "flow_intro": (
        "Every step of the problem chain is a reasonable move and none of them "
        "can work, because the thing being searched is the grant and the answer "
        "is a channel setting. The fix branch is ordered by confidence rather "
        "than by severity: one row is a fact, two are inferences, and the "
        "healthy row is the app finding its own name in the history."
    ),
    "diagram_problem": D.chain(
        "scrdo-p",
        "An app with chat:write refused by a channel posting permission",
        "chat:write authorises the method. Whether this channel accepts the "
        "message is decided afterwards, by a person, in a menu that no OAuth "
        "screen mentions.",
        [
            ("Member with chat:write", "every check passes"),
            ("Post refused", "read_only_channel"),
            ("More scopes added", "nothing changes"),
            ("App reinstalled", "still refused"),
            ("A channel setting", "and a channel manager"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "scrdo-f",
        "Reading the flag if it exists and the authorship of the history if it does not",
        "Absent is not false. The field is only returned on the plans that "
        "expose it, so the obvious one line check reports every locked channel "
        "in the workspace as writable, with complete confidence.",
        ("Presence, then value", "then who has spoken"),
        [
            ("is_read_only true", "certain, and an admin action", "bad"),
            ("Flag never returned", "not a writable channel", "plain"),
            ("Few voices, large room", "an inference, labelled", "plain"),
            ("Joins counted as posts", "a locked room looks busy", "plain"),
            ("Our own past message", "we were allowed in here", "good"),
        ],
    ),
}

V["slack/thread-only-or-non-threadable"] = {
    "flow_intro": (
        "This is the one note here where nothing is forbidden: the message is "
        "allowed, in the other position. The chain shows a global decision "
        "meeting a channel that was added long afterwards, and the fix branch "
        "keeps the dead thread anchor apart from the two channel refusals, "
        "because it is a data lifetime bug rather than a convention."
    ),
    "diagram_problem": D.chain(
        "scthr-p",
        "A single posting mode meeting a channel that is run entirely in threads",
        "The two failures look alike and want opposite repairs. One is fixed by "
        "changing where in the channel you post. The other is fixed by not "
        "caching a thread anchor for longer than the message it points at.",
        [
            ("One posting mode", "chosen years ago"),
            ("A channel run in threads", "added last quarter"),
            ("Top level refused", "thread_only_channel"),
            ("Stored anchor dies", "the parent aged out"),
            ("Both blamed on policy", "one was the parent"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scthr-f",
        "Comparing the channel's threading convention against the mode the integration uses",
        "Fifteen messages is what a non Marketplace app gets per history call, "
        "and fifteen messages can make an ordinary channel look like either "
        "extreme. Below the floor the script claims nothing at all.",
        ("Convention against mode", "history versus your code"),
        [
            ("Threaded room, flat poster", "thread_only_channel", "bad"),
            ("Flat room, threading app", "non_threadable_channel", "bad"),
            ("Anchor points at nothing", "a tombstone or a retention edge", "bad"),
            ("Sample below the floor", "nothing is claimed", "plain"),
            ("Mode stored per target", "each channel its own", "good"),
        ],
    ),
}

V["slack/slack-connect-external-channel"] = {
    "flow_intro": (
        "No arrow in this chain fails, which is the only honest way to draw it. "
        "Every send returned ok, the ID never moved, and the symptom is the "
        "absence of a symptom. The fix branch separates the two kinds of "
        "sharing, because a Grid workspace has plenty of the internal one and "
        "flagging those is how the real finding gets scrolled past."
    ),
    "diagram_problem": D.chain(
        "scext-p",
        "An internal alerting bot posting into a channel that was shared with a vendor",
        "Nothing here is an error, so nothing here can be caught by an error "
        "handler. Detection has to be a scheduled assertion about state, "
        "because the failure is that every single call worked.",
        [
            ("Vendor joins the room", "four clicks, no deploy"),
            ("Same channel ID", "nothing in config moves"),
            ("ok: true, every send", "no error to find"),
            ("Eight months of alerts", "stack traces, names"),
            ("Nothing ever raised", "the silence is the bug"),
        ],
    ),
    "diagram_fix": D.branch(
        "scext-f",
        "Sorting a channel by its sharing flags and its membership against your own team",
        "A member who will not resolve is the answer rather than a failed call. "
        "They belong to the other organisation, they are not in your user "
        "table, and code that resolves before deciding what to send needs a "
        "branch that sends less.",
        ("Flags, then every member", "against your own team id"),
        [
            ("is_ext_shared", "outside the company", "bad"),
            ("Invitation pending", "accepted without asking you", "bad"),
            ("is_org_shared", "another workspace, internal", "plain"),
            ("Member will not resolve", "that is the classification", "plain"),
            ("No flags set", "internal, nothing listed", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
