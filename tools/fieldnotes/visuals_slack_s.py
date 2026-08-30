#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch S.

Four notes about a file you cannot get at, and the batch most at risk of
becoming one drawing four times. So each chain fails somewhere different and
each branch sorts a different kind of thing.

The first has no red box at all: every step returns ok and the failure is an
absence, a parameter nobody passed, so the chain ends in people looking for a
file that is exactly where it was put. The second goes red at the last arrow,
because the file is fine, the id is fine, and the refusal happens the moment a
token is compared against an audience. The third carries the loop, since rot is
the only one of the four that gets worse on its own: every ingestion adds
references and every deletion silently kills some. And the fourth fails at the
first arrow, at the request, and every box after it is a consequence that looks
like a success.

The branches sort four different things on purpose: audiences, error strings,
the fate of a stored reference, and the bytes on a disk.

Drawn in Slack aubergine. No em dashes inside SVG text: one mis-sniffed
encoding turns a single character into three mojibake ones inside an image,
where nothing will catch it.
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

V["slack/file-not-shared-to-channel"] = {
    "flow_intro": (
        "There is no red box in this chain and that is the note. Every step "
        "returns ok, the file is created exactly as asked, and the failure is "
        "an absence: one parameter that was never passed, so the file has no "
        "audience and nothing anywhere reports that as a problem. The fix "
        "branch sorts audiences rather than faults, and only the top two rows "
        "are findings. The two below them are narrow audiences, and reporting "
        "those as broken is how a check like this gets switched off in its "
        "first week."
    ),
    "diagram_problem": D.chain(
        "skfns-p",
        "An upload that completes correctly and lands the file in front of nobody",
        "Uploading and sharing are two things and only one of them was asked "
        "for. The logs are honest, the file is real, and the people looking "
        "for it conclude they are searching the wrong channel.",
        [
            ("Get an upload URL", "filename and length"),
            ("Bytes go up", "a plain POST, not Slack"),
            ("Complete the upload", "no channel_id"),
            ("ok, with a file id", "logged as delivered"),
            ("Shares empty", "and nobody can search it"),
        ],
    ),
    "diagram_fix": D.branch(
        "skfns-f",
        "Every file the app owns, sorted by the audience it actually has",
        "Both representations of a share are read together, because the "
        "legacy channels array is empty for a file in a private channel and a "
        "check built on it alone cries wolf on every correct row.",
        ("files.list, scoped to the bot", "shares, channels, groups, ims"),
        [
            ("Nothing in any of them", "no channel_id at upload time", "bad"),
            ("Nothing, and a public link", "unreachable inside, open outside", "bad"),
            ("Direct messages only", "narrow, and not a fault", "plain"),
            ("A private channel", "a real share with an empty array", "plain"),
            ("A channel, and a comment", "which is what good looks like", "good"),
        ],
    ),
}

V["slack/file-not-visible"] = {
    "flow_intro": (
        "This chain goes red at the very last arrow, which is the opposite of "
        "the one before it. The event is genuine, the id is genuine, the "
        "token is valid and the scope is granted, so there is nothing to "
        "colour until an identity is held against an audience. The fix branch "
        "sorts error strings rather than files, because the entire cost of "
        "this bug is four different answers being read as one, and the bottom "
        "row is the only one anybody can act on today."
    ),
    "diagram_problem": D.chain(
        "skfnv-p",
        "A file_shared event that names a file the same token may not read",
        "An event is a notification and not a grant. Slack hands out ids more "
        "freely than it hands out access, and not_visible is the sentence "
        "where those two part company.",
        [
            ("file_shared arrives", "id, user, channel"),
            ("Handler wakes", "index this attachment"),
            ("files.info on the id", "files:read granted"),
            ("not_visible", "exists, and not for you"),
            ("Retried all night", "no backoff can help"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skfnv-f",
        "Four errors that look alike, sorted into the four repairs they want",
        "The API refuses to name the room, so the room comes from the event "
        "payload instead and is held against the conversations this token can "
        "see. One row ends in an invitation; the rest end somewhere else "
        "entirely.",
        ("files.info, then the rooms", "the error, then the membership"),
        [
            ("file_not_found", "wrong id or wrong workspace", "bad"),
            ("file_deleted", "gone, so drop the reference", "bad"),
            ("access_denied", "a Connect policy, ask an admin", "bad"),
            ("not_visible, and a member", "the share you were told of is gone",
             "plain"),
            ("not_visible, and outside", "one invitation, and it is named", "good"),
        ],
    ),
}

V["slack/file-deleted-link-rot"] = {
    "flow_intro": (
        "The only chain in this batch with a loop under it, and the loop is "
        "the whole point: this is the one failure of the four that gets worse "
        "while nobody touches anything. Every ingestion adds references and "
        "every deletion quietly kills some of them, so the corpus decays at "
        "whatever rate the workspace deletes. The red box is late because the "
        "reference was fine on the day it was stored. The fix branch sorts "
        "the fate of a stored id, and the fourth row is the one deliberately "
        "kept out of the number."
    ),
    "diagram_problem": D.chain(
        "skfrot-p",
        "An index built from Slack files decaying one deletion at a time",
        "Deleting a file does not touch the message that carried it or the "
        "row that points at it. A file id stays a plausible looking string "
        "forever, so nothing fails until somebody follows one.",
        [
            ("Walk the channels", "store id and text"),
            ("Searches resolve", "for months"),
            ("Somebody deletes it", "or retention does"),
            ("file_deleted on read", "one result in nine"),
            ("Message still there", "still rendering a link"),
        ],
        fail_at=2,
        loop=(4, 1, "every ingestion adds more of them"),
    ),
    "diagram_fix": D.branch(
        "skfrot-f",
        "Every harvested reference resolved, and the fraction taken over the decidable ones",
        "References are harvested from the files array and from permalinks "
        "pasted as text, because the second half is older and is the half a "
        "flat scan never sees. Unreadable stays out of the fraction.",
        ("Harvest, then files.info", "history and your own store"),
        [
            ("file_deleted", "rot, and it counts", "bad"),
            ("file_not_found", "dead to you, named separately", "bad"),
            ("Resolves cleanly", "the denominator", "good"),
            ("not_visible", "membership, so out of the number", "plain"),
            ("A fraction, kept and compared", "one reading is not a direction",
             "accent"),
        ],
    ),
}

V["slack/file-download-without-auth"] = {
    "flow_intro": (
        "This chain is red at the very first arrow, at the request, and every "
        "box after it is a consequence wearing the costume of a success: a "
        "200, a body, a write, a folder that looks right by every measure "
        "except opening a file. The fix branch is the only one in this batch "
        "that sorts bytes rather than API answers, and the order of its rows "
        "is the design. HTML is decided before length, because a sign-in page "
        "is also the wrong size and the wrong size sends you to the wrong "
        "part of your own code."
    ),
    "diagram_problem": D.chain(
        "skfdla-p",
        "A year of downloads that saved the sign-in page instead of the file",
        "An anonymous request for a file URL looks like a person clicking a "
        "link, and the right answer to a person who is not signed in is a "
        "page. It arrives with a 200 like every other page.",
        [
            ("Fetch url_private", "no bearer header"),
            ("200, and a body", "not a 401"),
            ("Written to disk", "no error anywhere"),
            ("Three kilobytes", "of the same markup"),
            ("Found a year later", "when one is needed"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skfdla-f",
        "The bytes already on disk held against the mimetype and size the API reports",
        "Nothing is fetched and no URL is printed. The API describes the file, "
        "your disk holds the bytes, and the comparison needs neither a "
        "transfer nor the credential that is under suspicion.",
        ("files.info, and the local copy", "mimetype, size, first bytes"),
        [
            ("Starts an HTML document", "the header, on every hop", "bad"),
            ("Nothing was written", "a body that never arrived", "bad"),
            ("A quarter of the length", "a short write, a different bug", "bad"),
            ("A permalink was stored", "a page, never the file", "plain"),
            ("Type and length agree", "validate this before the write", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
