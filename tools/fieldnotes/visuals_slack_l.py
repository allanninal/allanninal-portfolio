#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch L.

Four notes that are one causal chain read at four points, which is exactly the
situation where four diagrams turn into one diagram drawn four times. So they
break in four different places on purpose. The handshake chain fails at the
third box, before the app has ever run, and its fix branch is the only one here
whose healthy row is a hand-off rather than a repair. The deadline chain fails
at the acknowledgement itself and its fix branch is a split rather than a
classification, because the finding is which side of the ack each stage is on.
The storm is the only one with an arrow that goes backwards, and it is the
mechanism rather than an embellishment: the box that fails feeds the box that
caused it. And the duplicate chain fails at the guard, which is the one box a
reader expects to be the fix. Drawn in Slack aubergine.

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

V["slack/request-url-unverified"] = {
    "flow_intro": (
        "The only chain in this batch that ends before the app has run once. "
        "Everything in it happens at configuration time, and the box that "
        "fails is not code anybody wrote for Slack: it is the authenticator "
        "that answers strangers, doing exactly its job. The fix branch is the "
        "only one here whose good row is a hand-off, because a verified URL "
        "proves one exchange succeeded and nothing else."
    ),
    "diagram_problem": D.chain(
        "skruv-p",
        "A verification challenge answered by middleware instead of the handler",
        "The handshake is the only request Slack sends while your endpoint is "
        "still a stranger, so every piece of middleware you have is standing "
        "in front of it. The handler never sees the challenge.",
        [
            ("URL pasted into the config", "events already subscribed"),
            ("Slack sends one challenge", "three seconds, no redirects"),
            ("Auth middleware answers", "403 to an unknown caller"),
            ("Red line in the app config", "and nothing in any log"),
            ("Installed, scoped, silent", "for four days"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skruv-f",
        "Reading the manifest and replaying the recorded exchange, without sending anything",
        "Two inputs, neither of them a probe: what the configuration says, and "
        "what your own access log recorded when Slack last asked. Seven "
        "endings, five repairs, and two of them are somebody else's note.",
        ("Manifest plus one recorded exchange", "nothing is sent"),
        [
            ("Subscribed, no request url", "nothing can be delivered", "bad"),
            ("Redirected or behind auth", "Slack did not follow it", "bad"),
            ("Correct echo, four seconds", "right body, too late", "bad"),
            ("Socket Mode, no url", "there is no handshake to fail", "plain"),
            ("Challenge echoed in 180ms", "look at delivery next", "good"),
        ],
    ),
}

V["slack/three-second-timeout"] = {
    "flow_intro": (
        "This chain breaks at the acknowledgement rather than at any of the "
        "work, and the work is all correct: the ticket is created, the message "
        "is posted, the record is written. The fix branch is a split rather "
        "than a classification, because the question is not what went wrong "
        "but which side of the ack each stage belongs on, and the two red rows "
        "at the top are the cases where moving things does not help."
    ),
    "diagram_problem": D.chain(
        "sktsb-p",
        "A handler doing all of its work before answering, and answering late",
        "Nothing here produced a wrong answer. The clock started at Slack, it "
        "included the cold start, and a 200 at 3.2 seconds is counted exactly "
        "like a connection refused.",
        [
            ("Event delivered", "the clock starts at Slack"),
            ("Cold start and lookup", "540ms before your code"),
            ("Downstream call awaited", "2.6 seconds, inline"),
            ("Ack at 3.2 seconds", "late is failed, not slow"),
            ("Delivered again", "the same work, twice"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sktsb-f",
        "Splitting the stage list at the acknowledgement and pricing what is left",
        "Only the pre-ack column is held against three seconds. It is usually "
        "a small fraction of the handler, which is what makes deferring so "
        "effective when it is available, and the top row is where it is not.",
        ("Every stage, split at the ack", "one line each"),
        [
            ("Immovable half over 3s", "deferring saves nothing", "bad"),
            ("Four Slack calls in the path", "a quarter of the budget", "bad"),
            ("views.open pushed to a queue", "trigger_id already expired", "bad"),
            ("Whole handler under 3s", "nothing needs moving", "plain"),
            ("440ms before the ack", "2.6s handed to a queue", "good"),
        ],
    ),
}

V["slack/retry-storm-from-event-retries"] = {
    "flow_intro": (
        "The one chain here with an arrow that goes backwards, and the arrow "
        "is the mechanism rather than a flourish: the box that fails is the "
        "input to the box that caused it. Every step in it is a component "
        "behaving as designed. The fix branch is arithmetic with a ladder at "
        "the end, and the top rung is not a performance verdict at all."
    ),
    "diagram_problem": D.chain(
        "skrst-p",
        "Event retries multiplying API calls until the throttling produces more retries",
        "Four numbers, each defensible on its own, and one of them depends on "
        "the other three. The loop is why this collapses rather than "
        "degrading, and why it recovers all at once instead of gradually.",
        [
            ("One event arrives", "three API calls to serve it"),
            ("The ack is missed", "at three seconds"),
            ("Four deliveries", "at 0s, 60s and 300s"),
            ("Twelve calls where three fit", "the tier starts refusing"),
            ("Handler waits on the 429", "and misses more acks"),
        ],
        fail_at=4,
        loop=(4, 1, "and the miss rate climbs"),
    ),
    "diagram_fix": D.branch(
        "skrst-f",
        "Multiplying events by deliveries by calls, then iterating until the loop settles",
        "The retry ceiling means the loop always settles. Where it settles is "
        "the finding, and the difference between the bottom row and the top "
        "one is two API calls per handler run on identical traffic.",
        ("Events times deliveries times calls", "iterated to a fixed point"),
        [
            ("Settles above 95% missed", "delivery gets switched off", "bad"),
            ("Fixed point at 0.93", "an equilibrium made of failure", "bad"),
            ("Replicas added to catch up", "one bucket, emptied sooner", "bad"),
            ("Saturated, nothing refused", "no feedback engaged yet", "plain"),
            ("One call per handler run", "settles where it started", "good"),
        ],
    ),
}

V["slack/duplicate-processing-on-retry"] = {
    "flow_intro": (
        "The box that goes red here is the guard, which is the one box a "
        "reader arrives expecting to be the fix. It ran on every delivery and "
        "it rejected none of them, because the value it was keyed on is a "
        "property of the request rather than of the event. The fix branch "
        "asks three questions rather than one, and its two failing key rows "
        "fail in opposite directions."
    ),
    "diagram_problem": D.chain(
        "skdpr-p",
        "A dedupe guard keyed on the delivery instead of the event",
        "A retry is a fresh HTTP request with a new timestamp and a new "
        "signature. A set keyed on either of those accumulates one entry per "
        "delivery and turns nothing away.",
        [
            ("Retry arrives", "same event, new request"),
            ("Dedupe check runs", "keyed on the signature"),
            ("The signature is new", "the set has not seen it"),
            ("The work runs again", "a third ticket is created"),
            ("Guard blamed for not firing", "it fired every time"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skdpr-f",
        "Auditing the key for stability and uniqueness, the ttl against the schedule, and the field against real traffic",
        "Stable and unique are separate properties and most wrong keys fail "
        "exactly one. Failing stability produces duplicates that somebody "
        "reports; failing uniqueness produces missing work that nobody does.",
        ("Key, ttl, and field coverage", "three separate questions"),
        [
            ("Keyed on the delivery", "never stable, rejects nothing", "bad"),
            ("Keyed on the message ts", "collides, so work is lost", "bad"),
            ("A ttl of sixty seconds", "expires before the 300s retry", "bad"),
            ("client_msg_id on half", "the rest are unkeyed", "plain"),
            ("event_id with a 600s ttl", "stable, unique, always there", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
