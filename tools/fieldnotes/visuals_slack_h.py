#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch H.

Four notes about access that used to work, drawn so that none of them is the
same picture. Two are changes somebody made to a channel while an integration
was using it: one where a category moves under a fixed ID, and one where the
loop back to the start is the whole story because nothing announced anything.
Two are DMs failing from opposite ends: one where the conversation was never
created, and one where every single box in the chain succeeds and the messages
still go nowhere, so that chain is drawn without a red arrow at all. In Slack
aubergine.

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

V["slack/channel-converted-to-private"] = {
    "flow_intro": (
        "The problem chain is a category moving under an identifier that does "
        "not move, which is why every instinctive check comes back clean. The "
        "fix branch is a comparison rather than a field read: it needs a "
        "recorded past to work at all, and one of its rows exists purely to "
        "stop a confident wrong report."
    ),
    "diagram_problem": D.chain(
        "sccvp-p",
        "A public channel converted to private under a running integration",
        "Nothing about the reference changed. The same ID, the same name, the "
        "same history, and a different scope pair governing all of it from "
        "Tuesday afternoon onwards.",
        [
            ("Reader runs for a year", "public, channels:history"),
            ("Admin converts it", "same ID, new category"),
            ("Info says not found", "the ID never moved"),
            ("ID checked, ID is right", "nothing was deployed"),
            ("Two teams, two bugs", "one Tuesday afternoon"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "sccvp-f",
        "Comparing a recorded visibility against what conversations.info says now",
        "A not found without groups:read is a candidate and never a verdict, "
        "because a deletion looks exactly the same. The creation timestamp row "
        "is what stops a conversion being filed against a channel that did not "
        "exist when the baseline was written.",
        ("Recorded past against today", "baseline versus info"),
        [
            ("Recorded public, now private", "converted in place", "bad"),
            ("Not found, no groups:read", "a candidate, not an answer", "bad"),
            ("Created timestamp moved", "a different channel entirely", "plain"),
            ("Private, scopes fine, no invite", "a person, not a scope", "plain"),
            ("Matches what was recorded", "nothing moved", "good"),
        ],
    ),
}

V["slack/membership-lost-silently"] = {
    "flow_intro": (
        "The loop underneath is the note. A removal produces no signal in "
        "either direction, so the only thing that closes the circle is a "
        "person noticing weeks later. The fix branch turns three sets into "
        "four findings, and grades its own snapshot rather than implying a "
        "precision the API cannot give."
    ),
    "diagram_problem": D.chain(
        "scmls-p",
        "A bot removed from a channel with no notification in either direction",
        "One member tidying a list, and eleven months of a working digest "
        "ends. The send fails inside a 200, the process exits clean, and the "
        "absence of a message is the hardest thing there is to alert on.",
        [
            ("Digest runs for months", "the app sits in the channel"),
            ("A member tidies the list", "one kick, no confirmation"),
            ("Send returns ok false", "inside an HTTP 200"),
            ("Cron exits zero", "nobody reads the body"),
            ("Noticed in week three", "by a person, not a check"),
        ],
        fail_at=0,
        loop=(4, 0, "nothing announced it, in either direction"),
    ),
    "diagram_fix": D.branch(
        "scmls-f",
        "Diffing the bot conversation set against the previous run",
        "Held then and missing now is an incident with a window. Missing from "
        "both sets was never set up. They are the same false on the same "
        "field, and they go to different people.",
        ("Snapshot against today", "one paginated set"),
        [
            ("Held then, missing now", "the removal, with a window", "bad"),
            ("member_left_channel absent", "this run is the only watcher", "bad"),
            ("Missing from both sets", "never invited, not lost", "plain"),
            ("Snapshot four months old", "a window, not a date", "plain"),
            ("Held in both", "membership unchanged", "good"),
        ],
    ),
}

V["slack/dm-never-opened"] = {
    "flow_intro": (
        "The chain is about who did the testing rather than about a bad "
        "value: everyone who has ever used the app has a conversation, and "
        "everyone who has not does not. The fix branch reads an inventory "
        "instead of probing, because the natural probe answers the question by "
        "creating the thing it is asking about."
    ),
    "diagram_problem": D.chain(
        "scdno-p",
        "A DM feature that works for everyone who has already used the app",
        "The recipients it works for are exactly the people who tested it. "
        "That is why it passes every check made by anybody who has ever "
        "touched the feature.",
        [
            ("Pilot users get DMs", "their conversations exist"),
            ("New hire, no conversation", "nothing to deliver into"),
            ("postMessage often opens", "often is not a guarantee"),
            ("File upload refuses", "reads as a new bug"),
            ("Fails only for strangers", "who tested is the variable"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "scdno-f",
        "Sorting configured recipients against the IM conversations that exist",
        "A user ID with a conversation behind it is still wrong, and it is the "
        "row that keeps the bug alive: it delivers today and the file methods "
        "refuse it anyway. The scope row is there because a blind audit "
        "reports everybody as broken.",
        ("The IM list, never a probe", "listing, not opening"),
        [
            ("User ID, no conversation", "the recipient it fails for", "bad"),
            ("User ID, IM already exists", "right by accident", "bad"),
            ("D id outside the inventory", "another install, or no im:read", "plain"),
            ("No im:read granted", "the audit is blind, not the app", "plain"),
            ("D id in the inventory", "every method accepts it", "good"),
        ],
    ),
}

V["slack/dm-to-deactivated-user"] = {
    "flow_intro": (
        "There is no red arrow in the problem chain because there is no "
        "failure in it. Every step succeeds, the metric agrees, and the "
        "messages go nowhere. The fix branch sorts by how a send fails rather "
        "than by what the recipient is, which puts the one invisible outcome "
        "at the top and the ones already in your logs below it."
    ),
    "diagram_problem": D.chain(
        "scddu-p",
        "Notifications delivered into the DM of an account that was deactivated",
        "Every box here succeeds. A dead email address bounces and a "
        "disconnected number errors, but a deactivated Slack account accepts, "
        "because the conversation is real and the write is legitimate.",
        [
            ("Row written at signup", "a D id, kept forever"),
            ("Person leaves in October", "the account stays, deleted true"),
            ("Send returns ok true", "the message is stored"),
            ("Delivery reads 100 percent", "the metric counts ok true"),
            ("Ops asks about approvals", "two years of quiet loss"),
        ],
    ),
    "diagram_fix": D.branch(
        "scddu-f",
        "Joining the recipient table against the paginated user directory",
        "Only one row is silent, and it is the one the note exists for. An ID "
        "the directory does not know is a broken row rather than somebody who "
        "left, so it is kept out of the offboarding count.",
        ("Directory beside the table", "one paginated users.list"),
        [
            ("Deleted is true", "succeeds into a void", "bad"),
            ("Bot or app recipient", "loud, already in the logs", "plain"),
            ("Single channel guest", "delivered, links unreachable", "plain"),
            ("Not in the directory", "a broken row, not a leaver", "plain"),
            ("Active member", "somebody is there to read it", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
