#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch O.

Four notes about the payload rather than the destination, drawn so that no two
of them are the same picture. One is the only chain in the section with a loop
on it, because the debugging method it describes is literally a loop: comment
out half the blocks, post, look. One has a cause that is not a mistake at all,
only a busy day, so its red box is the last one. One has no red box anywhere,
which is the entire point of the note and the only chain here drawn that way.
And one goes red in the middle and then keeps going, because half of these
failures do not stop anything. Drawn in Slack aubergine.

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

V["slack/invalid-blocks"] = {
    "flow_intro": (
        "The only chain in this section with a loop drawn under it, because "
        "the method this note replaces is a loop: comment out half the "
        "blocks, post, look, repeat, and leave the debris in a channel. The "
        "cause is three steps back and did not look like a cause, since the "
        "URL opened perfectly in the browser that had the session cookie. The "
        "fix branch is a sort by severity, and the two plain rows are both "
        "refusals to call something a fault."
    ),
    "diagram_problem": D.chain(
        "skiblk-p",
        "A chart URL that works in the browser, and one opaque rejection with no block named",
        "The payload is the right shape and the channel is fine. One image "
        "URL needs a session cookie, Slack has none, and an image Slack "
        "cannot fetch takes the whole message with it.",
        [
            ("Digest built", "eleven blocks"),
            ("Chart URL added", "opens in the browser"),
            ("invalid_blocks", "no block named"),
            ("Bisect by sending", "half the blocks, post"),
            ("Debris in channel", "and still no answer"),
        ],
        fail_at=1,
        loop=(4, 3, "comment out, post, look, repeat"),
    ),
    "diagram_fix": D.branch(
        "skiblk-f",
        "A payload validated locally, with every image URL fetched carrying no credentials",
        "The structural rules are published and the payload is yours, so the "
        "index Slack will not give you can be computed before the call. The "
        "one rule that needs a request is the one that causes most of these.",
        ("The payload, and one HEAD", "sent with nothing attached"),
        [
            ("Image answers 401 or 403", "Slack has no session, you do", "bad"),
            ("Section with no text", "an empty template variable", "bad"),
            ("Host is private or loopback", "decided without asking", "bad"),
            ("Block type not in the table", "newer, or a typo", "plain"),
            ("A field over its ceiling", "the note next door", "plain"),
        ],
    ),
}

V["slack/msg-blocks-too-long"] = {
    "flow_intro": (
        "Nothing in this chain is a mistake and nothing was deployed. The "
        "generator is correct, every block is valid, and the input got "
        "bigger, so the red box is the last one rather than the first. The "
        "fix branch is a capacity report rather than a diagnosis: two "
        "ceilings, and the useful output is which of them your payload "
        "reaches first, because they want opposite repairs."
    ),
    "diagram_problem": D.chain(
        "skb50-p",
        "A digest of one block per item, meeting the day sixty things went wrong",
        "The payload is a function of the traffic rather than of the code, so "
        "the alert that would have explained the incident is the one message "
        "the incident stops from arriving.",
        [
            ("One block per item", "twelve on a good day"),
            ("Eight months pass", "no code changes"),
            ("Incident", "sixty failing checks"),
            ("Sixty two blocks", "past the fifty"),
            ("Alerting goes quiet", "when it matters most"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skb50-f",
        "Block count and encoded size measured together, reported as a growth multiple",
        "A cap on the block count does nothing for a payload that is bound by "
        "size, and an assertion on len(blocks) is exactly the check a "
        "size bound payload sails past on its way to being refused.",
        ("Count and encoded size", "and how much room is left"),
        [
            ("Breaks on the block count", "fewer rows is the repair", "bad"),
            ("Breaks on encoded size", "shorter rows is the repair", "bad"),
            ("Inside the last fifth", "one busy day from failing", "bad"),
            ("Modal, so a hundred", "a different ceiling", "plain"),
            ("Survives three times today", "real room, measured", "good"),
        ],
    ),
}

V["slack/blocks-without-text-fallback"] = {
    "flow_intro": (
        "The only chain in this section with no red box in it, and that is "
        "the note. Every step succeeds. The send returns ok, the channel "
        "renders correctly, the screenshot in the pull request looks right, "
        "and the push notification is blank. There is no failure to colour. "
        "The fix branch is the only one here that classifies a string rather "
        "than an error, because presence is not the test."
    ),
    "diagram_problem": D.chain(
        "skfbk-p",
        "A message that succeeds at every step and notifies as nothing",
        "Every feedback loop a team has points at the one surface where the "
        "fallback is never used. Nobody checks their own lock screen, and the "
        "complaint arrives as a comment about the product being bad.",
        [
            ("blocks, no text", "the builder omits it"),
            ("ok: true", "nothing to log"),
            ("Renders in channel", "the screenshot looks right"),
            ("Push is blank", "and search finds nothing"),
            ("Useless on mobile", "reported as a complaint"),
        ],
    ),
    "diagram_fix": D.branch(
        "skfbk-f",
        "Your own posted messages, with the notification each one produced rendered back",
        "A presence check passes a zero width space, the word message, and a "
        "JSON dump. The output that changes anybody's mind is the string a "
        "person on a phone was actually shown.",
        ("Your history, read back", "and the push it produced"),
        [
            ("No text beside blocks", "the notification is blank", "bad"),
            ("A zero width space", "present, and says nothing", "bad"),
            ("The literal word message", "put there to stop no_text", "bad"),
            ("Attachment fallback set", "Slack uses it, so this is fine", "plain"),
            ("A one line summary", "useful on a lock screen", "good"),
        ],
    ),
}

V["slack/text-length-limits"] = {
    "flow_intro": (
        "This chain goes red in the middle and then carries on, because the "
        "rejection is only half of it: the same class of mistake in a "
        "different field posts successfully and quietly loses the end of the "
        "message. That split is why this never feels like one problem. The "
        "fix branch sorts by what Slack does on overflow rather than by how "
        "far over the field is."
    ),
    "diagram_problem": D.chain(
        "sktlen-p",
        "A stack trace interpolated into a section, and a fallback quietly cut",
        "The formatter is correct and the tests pass, because the fixtures in "
        "the tests are short. What changed is the content, and the things "
        "that get long are the things most worth alerting about.",
        [
            ("One line errors", "for eight months"),
            ("A stack trace arrives", "interpolated whole"),
            ("Section at 3140", "the ceiling is 3000"),
            ("Fallback at 41000", "cut, not refused"),
            ("Two symptoms, one cause", "filed as two bugs"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sktlen-f",
        "Every text bearing field measured against its ceiling, with the overflow behaviour",
        "Reporting a bare over sends half the readers hunting for an error "
        "that was never raised. The behaviour column is the one that decides "
        "what anybody does next.",
        ("Field, length, ceiling", "and what happens past it"),
        [
            ("Section over 3000", "rejects the whole message", "bad"),
            ("Fallback over 40000", "cut, and nobody told", "bad"),
            ("Header over 150", "shorter than anyone expects", "bad"),
            ("Inside ten percent", "not failed yet, and will", "plain"),
            ("Bounded in the builder", "with a visible marker", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
