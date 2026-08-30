#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch Q.

Four notes about a write that will not happen, drawn as four different shapes
so that the two which are nearly the same note from the outside cannot be
mistaken for each other on the page.

The first fails at the second box, because the damage was done in storage
hours before anybody called anything. The second fails at the last one, because
every single thing about that message is correct right up to the moment two
identities are compared. The third has no red box anywhere, since the call
returns ok with a timestamp on it and the only failure is a person seeing
nothing. And the fourth carries the loop, because a time_in_past failure gets a
retry wrapped around it that recomputes the same too-close number and loses the
same race. Drawn in Slack aubergine.

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

V["slack/chat-update-message-not-found"] = {
    "flow_intro": (
        "The red box is the second one, and every box after it is a "
        "consequence rather than a cause. Nothing failed at the moment "
        "anything was written: a value went into a column typed as a number "
        "and came out four invisible characters shorter, and the first thing "
        "anybody sees is an edit refusing an hour later. The fix branch sorts "
        "four causes that share one error string, and the two at the bottom "
        "are the two that most often get merged into one row and should not "
        "be."
    ),
    "diagram_problem": D.chain(
        "skmnf-p",
        "A timestamp stored as a number, and every later edit refused",
        "The message is still in the channel and the key to it is not. Slack "
        "matches a channel and a ts exactly, and a float has no memory of the "
        "trailing zeros it dropped on the way in.",
        [
            ("Post returns ok", "ts as a string"),
            ("Stored as a number", "a JSON column"),
            ("Read back short", "four digits gone"),
            ("chat.update", "the pair matches nothing"),
            ("Frozen at starting", "for the whole deploy"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skmnf-f",
        "One error string sorted into the four causes it actually covers",
        "Ask for the one message window, then widen it by a second. The "
        "neighbour whose ts re-pads to yours is the proof, and it is the only "
        "output that ends the argument in one line.",
        ("The stored pair, read back", "shape first, then the window"),
        [
            ("Fraction shorter than six", "a float dropped the zeros", "bad"),
            ("Neighbours, none of them yours", "the ts came from another channel", "bad"),
            ("No ts was ever returned", "posted through a webhook", "bad"),
            ("Window empty either side", "somebody deleted it", "plain"),
            ("Exactly one, matching", "the pair is fine, look elsewhere", "good"),
        ],
    ),
}

V["slack/cant-update-or-delete-message"] = {
    "flow_intro": (
        "This chain goes red at the last arrow, which is the opposite of the "
        "note before it. The message exists, the pair resolves, the channel "
        "is right and the scope is granted, so there is nothing to colour "
        "until two identities are put beside each other. The fix branch is a "
        "list of authors rather than a list of faults, and only one row on it "
        "is a thing your own app can change."
    ),
    "diagram_problem": D.chain(
        "skown-p",
        "A handler that edits its own bot's message while holding the other token",
        "Adding a scope is the reflex and it changes nothing here. Editing is "
        "the one place where the token has to be the author, and an author is "
        "not something a scope grants.",
        [
            ("Bot posts", "with a button on it"),
            ("Click arrives", "handler wakes up"),
            ("Reads the ts", "it resolves fine"),
            ("Edits on a user token", "a different author"),
            ("cant_update_message", "reinstalled twice by now"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skown-f",
        "Every message compared against the bot_id and user_id this token actually holds",
        "auth.test names the identity you are holding, and the message names "
        "the one that wrote it. The comparison is cheap, and the answer is a "
        "sentence about who rather than a boolean about whether.",
        ("auth.test, and the authors", "bot_id, app_id, user"),
        [
            ("Your bot, wrong token class", "the one row you can fix today", "bad"),
            ("A different app entirely", "no scope reaches it", "bad"),
            ("bot_id with no app_id", "a webhook, so nobody can", "bad"),
            ("A person wrote it", "removal wants an admin user token", "plain"),
            ("Yours, overrides and all", "a username change is decoration", "good"),
        ],
    ),
}

V["slack/ephemeral-user-not-in-channel"] = {
    "flow_intro": (
        "No red box anywhere in this chain, which is the note. The command "
        "runs, the handler answers, the API returns ok and hands back a "
        "timestamp, and a person sees nothing. There is no failure to colour "
        "because nothing failed; the timestamp refers to a rendering that was "
        "attempted in a view that does not exist. The fix branch is the only "
        "one in this batch that sorts people rather than payloads, and the "
        "actions matter more than the verdicts."
    ),
    "diagram_problem": D.chain(
        "skeph-p",
        "An ephemeral answered with ok and a timestamp, and drawn for nobody",
        "Ephemerals are not stored, so there is nothing in history to inspect "
        "afterwards and nothing the user can screenshot. The bug report "
        "arrives as the bot ignored me.",
        [
            ("Reviewer named", "picked from a ticket"),
            ("postEphemeral", "channel and user"),
            ("ok, and a message_ts", "logged as delivered"),
            ("No view to draw into", "they are not a member"),
            ("Nothing in history", "and nothing to show"),
        ],
    ),
    "diagram_fix": D.branch(
        "skeph-f",
        "Each recipient checked for existence, activity and membership before the send",
        "The permanent conditions are checked ahead of the routing one, "
        "because a fallback DM to a deactivated account is a retry loop with "
        "a nicer name. Every row ends in an action rather than a score.",
        ("users.info, then the members", "the recipient, not the app"),
        [
            ("Not in the channel", "open a DM, do not add them", "bad"),
            ("Deactivated in March", "skip it, and fix the rota", "bad"),
            ("A bot or an app user", "nothing renders, skip it", "bad"),
            ("Membership unreadable", "a missing scope, not a send bug", "plain"),
            ("A member, and it is short", "an acknowledgement, which is the use", "good"),
        ],
    ),
}

V["slack/scheduled-message-in-past"] = {
    "flow_intro": (
        "The only chain here with a loop under it, and the loop is the real "
        "shape of the bug: the send fails, something retries it, the retry "
        "recomputes the same number a few seconds nearer the target, and it "
        "loses the same race again. The red box is the fourth one because the "
        "arithmetic is fine on a warm morning. The fix branch sorts by cause, "
        "and the bottom two are the rows where nothing about the code is "
        "wrong at all."
    ),
    "diagram_problem": D.chain(
        "skpast-p",
        "A nine o'clock digest that fails on the mornings the worker cold starts",
        "Slack reads post_at when it processes the request rather than when "
        "you computed it, so every second of queueing spends the margin you "
        "left, and a retry starts from a worse position than the first try.",
        [
            ("Nine in the morning", "computed locally"),
            ("Handed over as UTC", "off by the offset"),
            ("Worker cold starts", "forty seconds late"),
            ("time_in_past", "no digest today"),
            ("Retry, same number", "nearer the target"),
        ],
        fail_at=2,
        loop=(4, 3, "recompute, resend, lose the same race"),
    ),
    "diagram_fix": D.branch(
        "skpast-f",
        "The pending queue read back, with every post_at held against the clock and the units",
        "The units are decided before the clock, because a value in "
        "milliseconds is not early or late, it is the wrong kind of number, "
        "and a bare wrong sends somebody to look at a horizon that has "
        "nothing to do with it.",
        ("The queue, and one number", "post_at, date_created, now"),
        [
            ("Thirteen digits", "milliseconds, so fifty thousand years", "bad"),
            ("Behind the clock", "computed before a queue got involved", "bad"),
            ("A clean five hours out", "a wall clock handed over as UTC", "bad"),
            ("Past one hundred and twenty days", "correct, and further than the API goes",
             "plain"),
            ("A minute of room, in seconds", "and it survives a cold start", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
