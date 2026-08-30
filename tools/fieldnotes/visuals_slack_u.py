#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch U.

Four notes about one WebSocket, and the batch most at risk of becoming one
drawing four times. So the red arrow sits in a different place in each chain,
and each branch sorts a different kind of thing.

The first fails at the very first arrow, before any application code exists:
the credential is refused, so the connection is never minted and every box
after it is a consequence of an absence. The second carries the loop, because
the leak is the only failure of the four that gets worse while nobody touches
anything: every restart leaves another registration standing. The third goes
red in the middle, since the connection is perfectly healthy right up to the
moment Slack takes it back on schedule and the client closes before it opens.
The fourth fails at the second arrow, at the routing decision, and the boxes
after it are the two outcomes of a coin toss rather than of a fault.

The branches sort four different things on purpose: the contents of an
environment, a budget of ten, four disconnect reasons, and the outcome of a
single trigger.

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

V["slack/connections-open-unusable"] = {
    "flow_intro": (
        "The red arrow is the first one, which is the shape of a failure that "
        "happens before your application exists. There is no handler to "
        "instrument and no event to trace, because the credential was refused "
        "at the door and the WebSocket was never minted. Every box after that "
        "arrow is an absence wearing the costume of a healthy service: a "
        "process that stays up, a probe that passes, a log line that repeats. "
        "The fix branch sorts the contents of an environment rather than any "
        "answer from Slack, and it does so offline, because a prefix settles "
        "the question and sending the token would consume one of ten "
        "connections to learn the same thing."
    ),
    "diagram_problem": D.chain(
        "skcou-p",
        "A Socket Mode app that was refused its connection and stayed green for nine days",
        "The refusal is permanent and the client treats it as weather. Nothing "
        "crashes, nothing alerts, and the first line of your own code has "
        "still never run.",
        [
            ("Process starts", "SLACK_APP_TOKEN is set"),
            ("Ask for a socket", "the value begins xoxb-"),
            ("Refused", "wrong class of token"),
            ("Reconnect, forever", "a permanent fault, retried"),
            ("Green and deaf", "no event has ever arrived"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skcou-f",
        "Each variable in the deployment classified by its first characters, offline",
        "Nothing is transmitted and no token is printed. The class comes from "
        "the prefix and the fault comes from the slot, so the credential under "
        "suspicion is never exercised by the act of checking it.",
        ("Every slot, read locally", "prefix, consumer, length"),
        [
            ("xoxb- in the app slot", "the opener takes only xapp-", "bad"),
            ("One string in two slots", "somebody found the Slack token", "bad"),
            ("Quotes came along", "copied out of a dotenv file", "bad"),
            ("xapp-, and still silent", "next question is the scopes", "plain"),
            ("Right class, right slot", "and the channel says it answers", "good"),
        ],
    ),
}

V["slack/socket-connection-cap"] = {
    "flow_intro": (
        "This is the only chain in the batch with a loop under it, and the "
        "loop is the note: every restart leaves one more registration "
        "standing, so the failure gets worse while nobody touches anything. "
        "The red arrow is late because each individual step is correct, "
        "including the reconnect. The fix branch sorts a budget of ten rather "
        "than a set of errors, and the fourth row is the one that keeps this "
        "check honest: losses that arrive in a huddle are not a leak, and "
        "attributing them here would produce a confident, wrong number."
    ),
    "diagram_problem": D.chain(
        "skscc-p",
        "Ten permitted connections filling up with registrations nobody reads",
        "Slack sends each payload to one open connection. A registration left "
        "behind by a reconnect is a hole, and the share of traffic it "
        "swallows is exactly its share of the set.",
        [
            ("A rolling restart", "the pod goes away"),
            ("A new socket opens", "the client reconnects"),
            ("The old one stands", "no close ever reached Slack"),
            ("Four registrations", "one process is reading"),
            ("Three payloads in four", "delivered to nothing"),
        ],
        fail_at=3,
        loop=(4, 1, "every restart leaves another one standing"),
    ),
    "diagram_fix": D.branch(
        "skscc-f",
        "The connection budget counted from the deployment and from the observed loss",
        "The count is arithmetic and the leak is an inversion: if payloads go "
        "to one of N registrations and L of them are read, the loss fraction "
        "is the ghost proportion, so it can be run backwards.",
        ("Replicas times sockets", "against ten, then the loss"),
        [
            ("Over ten already", "before anything has leaked", "bad"),
            ("Implied count above ten", "and Slack said too_many", "bad"),
            ("Ghosts under the cap", "a steady tax on every payload", "bad"),
            ("Losses in a huddle", "not a leak, read the refresh note", "plain"),
            ("Implied equals live", "the budget and the reality agree", "good"),
        ],
    ),
}

V["slack/refresh-requested-unhandled"] = {
    "flow_intro": (
        "The red arrow is in the middle here, later than in either of the "
        "notes before it, because nothing is wrong with this connection until "
        "Slack takes it back. The warning arrives on time, the disconnect "
        "arrives on time, and the fault is one line of ordering: close, then "
        "open, with a seam in between that has nowhere to put a payload. The "
        "fix branch is the only one in the batch that sorts reasons, and the "
        "point of it is that two of these four arrive in the same handler and "
        "want opposite responses."
    ),
    "diagram_problem": D.chain(
        "skrru-p",
        "A scheduled connection refresh handled as a close followed by an open",
        "Slack warns ten seconds ahead so the replacement can be ready. A "
        "client that swaps instead of overlapping loses whatever arrives in "
        "the seam, and Socket Mode has no redelivery.",
        [
            ("Hours of healthy events", "one open connection"),
            ("A warning frame", "ten seconds of notice"),
            ("Discarded as noise", "the handler wants events"),
            ("Close, then open", "a seam with no listener"),
            ("A cluster of losses", "and it recovers by itself"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skrru-f",
        "Four disconnect reasons sorted into the four responses they actually want",
        "Two of these land in the same handler and mean opposite things. A "
        "single catch around all of them is what turns a routine refresh, a "
        "switched-off setting and a full connection budget into one loop.",
        ("The reason, then the clock", "your log, then the history"),
        [
            ("refresh_requested", "open the new one first", "bad"),
            ("Periodic narrow gaps", "a seam, measured rather than seen", "bad"),
            ("link_disabled", "permanent, so stop reconnecting", "bad"),
            ("too_many_websockets", "the cap, and a different note", "plain"),
            ("Overlapped, then closed", "hello on the new one first", "good"),
        ],
    ),
}

V["slack/socket-mode-single-instance"] = {
    "flow_intro": (
        "The red arrow here is at the routing decision, and the two boxes "
        "after it are the outcomes of a coin toss rather than of a fault: "
        "every component in this picture is behaving exactly as designed, "
        "including the dedupe cache that misses. The fix branch sorts the "
        "outcome of one trigger, and it is the only branch in the batch whose "
        "rows name other notes, because duplicates and drops look identical "
        "apart from whether they appear together."
    ),
    "diagram_problem": D.chain(
        "sksmsi-p",
        "Three replicas holding three connections and Slack choosing one per payload",
        "This is not a consumer group. There is no redelivery to a different "
        "consumer and no ordering, so a retry can land on a pod that never "
        "saw the original and a payload can land on a pod that is restarting.",
        [
            ("Scaled to three pods", "for launch headroom"),
            ("Three open sockets", "one app, three places"),
            ("Slack picks one", "no distribution promise"),
            ("Retry lands elsewhere", "the cache is per process"),
            ("Twice, or not at all", "and a restart changes which"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sksmsi-f",
        "Every mention scored by how many answers it got, and the pair that identifies the cause",
        "Counted per trigger rather than in total, because a duplicate count "
        "says nothing about the mentions that got nothing. It is the "
        "combination that names the failure, not either half.",
        ("Answers per mention", "none, once, many, and spacing"),
        [
            ("Duplicates and drops", "several live connections", "bad"),
            ("Duplicates at retry gaps", "one listener, other note", "plain"),
            ("Duplicates in the same second", "two subscriptions, other note", "plain"),
            ("Drops on their own", "the cap or a refresh", "plain"),
            ("Exactly once, every time", "the number to get back to", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
