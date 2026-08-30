#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch K.

Four notes about quantity, drawn so that no two of them read as one picture.
One is the only chain in this section with a growth loop in it: nothing fails
until the count does, so the arrow that goes backwards is the mechanism. Two
are the pagination arguments, and they fail at different points on purpose, one
in the response and one on the restart. And one is a chain where the box that
goes red is not the failure at all but the misfiling of it, because the app
watching the incident is a bystander. Drawn in Slack aubergine.

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

V["slack/bot-in-too-many-channels"] = {
    "flow_intro": (
        "The only chain in this section with an arrow that goes backwards. "
        "Nothing in it is an error until the very end, and the end is not "
        "caused by the step before it: it is caused by the loop underneath, "
        "which has been adding to the count since long before anybody noticed. "
        "The fix branch is arithmetic rather than classification, because the "
        "finding here is a number and not a state."
    ),
    "diagram_problem": D.chain(
        "sktmc-p",
        "A bot invited to every new channel until the inventory could not be read",
        "Every invitation in this chain succeeded. There is no error to catch "
        "and no flag to read, which is why the count has to be asserted by "
        "somebody rather than discovered by a handler.",
        [
            ("Bot invited by hand", "forty channels"),
            ("A rule invites it", "every new channel"),
            ("Inventory per run", "four pages, Tier 2"),
            ("Runs overlap", "two sweeps, one bucket"),
            ("ratelimited", "the sweep cannot finish"),
        ],
        fail_at=3,
        loop=(4, 1, "and the rule is still adding"),
    ),
    "diagram_fix": D.branch(
        "sktmc-f",
        "Pricing one inventory against the Tier 2 budget and the frequency it is taken at",
        "Pages multiplied by frequency, against twenty requests a minute. The "
        "same footprint is affordable hourly and ruinous per queue item, so "
        "the count on its own is not the finding.",
        ("Pages times frequency", "against 20 a minute"),
        [
            ("Over the Tier 2 budget", "1,440 asked of 1,200", "bad"),
            ("Footprint tracks the workspace", "a rule, not a choice", "bad"),
            ("message.channels subscribed", "multiplied by the footprint", "bad"),
            ("The sweep did not finish", "no count is claimed", "plain"),
            ("Cached with a TTL", "four requests an hour", "good"),
        ],
    ),
}

V["slack/invalid-limit"] = {
    "flow_intro": (
        "The chain breaks at the response rather than at the request, which is "
        "the half of this note people miss: the loud version returns an error "
        "and the quiet one returns a smaller page and says ok. The fix branch "
        "keeps four outcomes apart that a single length check collapses into "
        "two, and the two plain rows are the ones that are not bugs."
    ),
    "diagram_problem": D.chain(
        "skiml-p",
        "A page size constant chosen once and quietly overruled by the method",
        "Asking for more than the ceiling is rejected outright. Asking for "
        "less than the ceiling can still come back smaller, with ok: true, "
        "and code that reads a short page as the end of the data truncates "
        "there.",
        [
            ("limit chosen once", "to avoid a loop"),
            ("Asked for 200", "fifteen came back"),
            ("ok: true", "no error anywhere"),
            ("Short page read as end", "the cursor is ignored"),
            ("History is 15 long", "and nobody asks why"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skiml-f",
        "Sorting one response against the request that produced it",
        "A page smaller than the one you asked for means one of two opposite "
        "things, and the cursor is what tells them apart. With a cursor Slack "
        "chose the size; without one the data simply ran out.",
        ("Asked against returned", "one call per method"),
        [
            ("Above the ceiling", "invalid_limit, nothing back", "bad"),
            ("Smaller page, cursor set", "Slack chose the size", "bad"),
            ("Legal and over the guidance", "1000 on users.list", "plain"),
            ("Smaller page, no cursor", "the data ran out", "plain"),
            ("The page you asked for", "the constant is honest", "good"),
        ],
    ),
}

V["slack/invalid-cursor"] = {
    "flow_intro": (
        "This chain fails one step later than the page size one, and on a "
        "restart rather than on a response. The step that goes wrong is the "
        "test that passed: restarting a job immediately is exactly the "
        "experiment a short-lived token survives. The fix branch has three red "
        "rows because three different things produce one error string."
    ),
    "diagram_problem": D.chain(
        "skicu-p",
        "A resumable sync persisting a cursor that only lives for one loop",
        "The string in the database is intact and it is not a checkpoint. A "
        "cursor carries the position and the query together, opaquely, and it "
        "was only ever promised to last for the loop that issued it.",
        [
            ("Loop follows cursors", "correctly, page by page"),
            ("Interrupted", "next_cursor written down"),
            ("Restart in seconds", "the test that passed"),
            ("Restart on Monday", "invalid_cursor"),
            ("Blamed on corruption", "the string is intact"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skicu-f",
        "Dating a stored checkpoint, diffing its query, then replaying it beside a control call",
        "The control call is what makes any of this attributable. A replay "
        "that fails on its own could be a dead cursor, a removed scope or an "
        "archived channel; the same request without a cursor separates them.",
        ("The checkpoint record", "age, query, then replay"),
        [
            ("Older than the budget", "a loop it outlived", "bad"),
            ("types changed since", "the cursor encodes the query", "bad"),
            ("No issued_at at all", "replayed at an unknown age", "bad"),
            ("Control call failed too", "the cursor is not the fault", "plain"),
            ("Resumed on a ts or an id", "survives the weekend", "good"),
        ],
    ),
}

V["slack/message-limit-exceeded"] = {
    "flow_intro": (
        "The box that goes red here is not the failure. The failure is three "
        "steps earlier and belongs to somebody else; the red box is the "
        "investigation arriving at the wrong sender, which is the outcome this "
        "note exists to prevent. The fix branch is a leaderboard rather than a "
        "diagnosis, and the healthy row is your own app being cleared in "
        "writing."
    ),
    "diagram_problem": D.chain(
        "skmle-p",
        "A workspace ceiling exhausted by another integration and filed against yours",
        "This is the rare Slack failure where the correct end of the "
        "investigation is a message to another team. Your logs hold your "
        "sends, and your sends are not the problem.",
        [
            ("Your app posts eleven", "a day, politely"),
            ("Somebody else migrates", "one message per row"),
            ("Workspace ceiling hit", "every app refused"),
            ("Retry-After honoured", "it changes nothing"),
            ("Filed against your app", "the wrong sender"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skmle-f",
        "Ranking every sender in the busiest channels by peak messages per minute",
        "Whole minutes, summed across senders, because the ceiling is an "
        "aggregate. How closely spaced one app's own posts are in one channel "
        "is a cadence question and would rank a chatty deploy bot above the "
        "migration that caused this.",
        ("Whole minutes, every sender", "history, not your logs"),
        [
            ("Another app at sixty a minute", "the likely cause", "bad"),
            ("message_limit_exceeded", "the workspace, not your quota", "bad"),
            ("ratelimited", "your quota, a different branch", "plain"),
            ("Sample too thin to divide", "nothing is ranked", "plain"),
            ("Your app at four a minute", "a bystander, in writing", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
