#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch P.

Two notes about what a message is made of and two about where a reply goes,
drawn so no two are the same picture. The attachments one is the only chain in
the section whose last two boxes are both red, because the migration everybody
reaches for lands on a tighter ceiling than the one they left. The empty
message one is the only chain that ends in silence rather than in an error, and
its branch sorts by what Slack does rather than by how empty the payload is.
The two threading chains are deliberately opposites: one ends in a refusal you
can read, the other ends in a reply that arrived, was accepted, and is in the
wrong thread. Drawn in Slack aubergine.

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

V["slack/too-many-attachments"] = {
    "flow_intro": (
        "The only chain in this section that goes red twice, and the second "
        "red box is the repair. A monitoring tool emits one attachment per "
        "result, the results grow past a hundred, and the obvious fix is to "
        "move to blocks, which is a ceiling of fifty. The fix branch is "
        "therefore a sort by what each attachment is actually doing, because "
        "one of the things it does has no replacement and two of them cost "
        "nothing to move."
    ),
    "diagram_problem": D.chain(
        "sklegat-p",
        "One attachment per result, a hundred results, and a migration onto a tighter ceiling",
        "The attachment count and the block count are two different ceilings "
        "on two different surfaces, and the smaller of the two is the one on "
        "the surface everybody is told to move to.",
        [
            ("One bar per result", "colour coded by severity"),
            ("Results pass a hundred", "on a bad afternoon"),
            ("too_many_attachments", "the ceiling is 100"),
            ("Rewritten as blocks", "one section per result"),
            ("Over fifty blocks", "a tighter ceiling"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sklegat-f",
        "Every attachment sorted by what it does, with the block cost of moving it",
        "Attachments are legacy and are still the only way to get a coloured "
        "bar, so a report that says migrate everything is a report nobody "
        "acts on. The useful column is what each one costs to leave behind.",
        ("Count, bytes, and what for", "measured per message"),
        [
            ("Past a hundred bars", "refused outright", "bad"),
            ("Serialized size over", "not a published number", "bad"),
            ("mrkdwn with no mrkdwn_in", "renders its own asterisks", "bad"),
            ("Only the colour bar", "no Block Kit equivalent", "plain"),
            ("Text only, moves for free", "one section each", "good"),
        ],
    ),
}

V["slack/no-text-empty-message"] = {
    "flow_intro": (
        "This chain ends in silence rather than in a symptom, which is the "
        "point: the query returns nothing, the template renders nothing, the "
        "send is refused, and the only person who could notice is waiting for "
        "a message that was never going to arrive. The fix branch sorts by "
        "what Slack does with the payload rather than by how empty it is, "
        "because a payload that is refused and one that posts a bare "
        "horizontal rule need opposite repairs."
    ),
    "diagram_problem": D.chain(
        "sknotxt-p",
        "A zero row query, an empty render, a refused send and a report nobody misses",
        "The quiet case is the one nobody writes a fixture for, so the first "
        "time the template renders nothing is in production, and the failure "
        "is a report that simply does not appear.",
        [
            ("Digest joins the rows", "into one string"),
            ("Zero rows today", "nothing upstream broke"),
            ("The string is empty", "and is sent anyway"),
            ("no_text", "nothing is delivered"),
            ("Nobody notices", "an absent report"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sknotxt-f",
        "A payload sorted by what Slack does with it, from refusal to a bare rule",
        "Refused and delivered empty are two different afternoons. One is an "
        "error in a log, the other is a heading over nothing that a reader "
        "quietly stops opening.",
        ("Text, blocks, attachments", "which one carries anything"),
        [
            ("Nothing anywhere", "refused with no_text", "bad"),
            ("Invisible characters", "present, and not a message", "bad"),
            ("A heading over nothing", "accepted, and unreadable", "bad"),
            ("Dividers and no words", "a rule, posted on purpose", "plain"),
            ("Skip the send instead", "silence is the right output", "good"),
        ],
    ),
}

V["slack/cannot-reply-to-message"] = {
    "flow_intro": (
        "A chain about a message that stopped being able to host a reply "
        "while nothing about your code changed. The parent is deleted three "
        "weeks after the ts was written into a config file, and the red box "
        "is the deletion rather than the reply. The fix branch is a sort by "
        "who has to act next, because a parent that is gone needs a new "
        "parent, a locked one needs a person, and an unreadable one needs a "
        "scope."
    ),
    "diagram_problem": D.chain(
        "skcrtm-p",
        "A stored thread parent deleted weeks later, and every reply after it refused",
        "A ts captured once and threaded under forever is a reference to "
        "something somebody else can delete, lock or archive without ever "
        "knowing your app was pointing at it.",
        [
            ("A ts is captured", "and stored as the parent"),
            ("Weeks of replies", "all landing correctly"),
            ("The parent is deleted", "a tombstone is left"),
            ("cannot_reply_to_message", "every reply, from now on"),
            ("The thread is orphaned", "and the alerts stop"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skcrtm-f",
        "Each stored parent read back once, sorted by who has to act on it",
        "conversations.replies with a limit of one answers the whole question "
        "without sending anything. The states it returns want four different "
        "people, and reporting them as one count sends the wrong one.",
        ("One read per stored parent", "limit of one, nothing sent"),
        [
            ("Deleted, a tombstone left", "establish a new parent", "bad"),
            ("Gone entirely", "thread_not_found", "bad"),
            ("Locked by an admin", "needs a person, not a retry", "bad"),
            ("Unreadable from here", "a scope answer, not a thread one", "plain"),
            ("Present and a root", "still takes a reply", "good"),
        ],
    ),
}

V["slack/thread-ts-is-a-reply"] = {
    "flow_intro": (
        "The opposite chain to the one next door. Nothing is refused, "
        "everything returns ok, and the reply is in the wrong thread. The red "
        "box is a capture two steps before the symptom, and the symptom is a "
        "conversation that reads as though people are talking past each "
        "other. The fix branch classifies a ts rather than an error, since "
        "there is no error, and the field that settles it is on the message "
        "already."
    ),
    "diagram_problem": D.chain(
        "sktsrep-p",
        "A reply ts captured as a parent, and every later reply moved without a word",
        "Slack threads are one level deep, so a reply used as a parent is not "
        "refused, it is reparented. The send returns ok and the reply appears "
        "beside the message it was answering rather than under it.",
        [
            ("A reply is captured", "response ts, stored"),
            ("Threaded under it", "for months"),
            ("Slack reparents it", "to the original root"),
            ("ok true, every time", "no error, no log line"),
            ("Answers beside questions", "read as people talking past"),
        ],
    ),
    "diagram_fix": D.branch(
        "sktsrep-f",
        "Every stored parent read back and sorted into root, reply or broadcast",
        "A root has no thread_ts, or one equal to its own ts. A reply carries "
        "both and they differ. That single comparison is the whole detection, "
        "and Slack has been returning the field all along.",
        ("Stored ts, read back", "thread_ts beside ts"),
        [
            ("thread_ts differs from ts", "a reply, used as a root", "bad"),
            ("Sent with reply_broadcast", "looks top level, is not", "bad"),
            ("Not in the thread at all", "the note next door", "plain"),
            ("thread_ts equals ts", "a root, and safe", "good"),
            ("Captured as thread_ts or ts", "correct for both events", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
