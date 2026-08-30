#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch J.

Four rate-limit notes, which is four chances to draw the same picture. So each
one is drawn around a different quantity. The first is about a number that
arrived and was thrown away, so its chain ends where the header did. The second
is about a cadence, so the fix branch sorts on how many messages fit in one
second rather than on any tier. The third is about a budget, so the chain is a
poll interval chosen against nothing and the branch is the division. And the
fourth is about a key: one bucket, several processes, and a loop that closes
because every replica woke at the same instant. Drawn in Slack aubergine.

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

V["slack/ratelimited-retry-after-ignored"] = {
    "flow_intro": (
        "The chain is drawn around one number: Slack computed it, put it in a "
        "header, and the client dropped it on the floor. Every step after that "
        "is a guess at a value that was already known. The fix branch sorts the "
        "header itself, because the parser has more states than present and "
        "absent, and four of them are not a number of seconds."
    ),
    "diagram_problem": D.chain(
        "sjrate-p",
        "A client discarding the Retry-After header and retrying into a closed window",
        "A retry that lands inside a window which has not reopened is still a "
        "request. Undercutting the header turns a short wait into a long one, "
        "which is why the impatient job finishes after the polite one.",
        [
            ("Backfill starts", "ninety good seconds"),
            ("Window is spent", "Retry-After: 12"),
            ("Header not read", "generic failure path"),
            ("Retry immediately", "inside the closed window"),
            ("Job never finishes", "backoff blamed"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sjrate-f",
        "Parsing Retry-After defensively and replaying the refusals already logged",
        "Absent, empty and unparseable are three different situations and none "
        "of them is an answer. Each returns a documented default, labelled as a "
        "default, so a log line never reports a guess as a schedule.",
        ("Status, error, header", "captured together"),
        [
            ("Present and numeric", "the whole schedule", "good"),
            ("Absent or empty", "a default, said out loud", "plain"),
            ("Not a number at all", "no exception in the error path", "plain"),
            ("Retried early", "the outage got longer", "bad"),
            ("Fixed sleep instead", "idle and looking throttled", "bad"),
        ],
    ),
}

V["slack/postmessage-one-per-second"] = {
    "flow_intro": (
        "Nothing in this chain consults a tier, because the tier table does not "
        "cover the method. The burst allowance carries the first sixty messages, "
        "which is what makes the failure look like it started halfway through. "
        "The fix branch is measured in timestamps: what one second of your own "
        "sending already contains."
    ),
    "diagram_problem": D.chain(
        "sjcad-p",
        "A fan-out job exceeding the per channel posting envelope for chat.postMessage",
        "The limit follows the channel, not the method and not the process. A "
        "load test across eight channels passes and production, which posts "
        "into one, does not.",
        [
            ("200 alerts to send", "one channel"),
            ("Burst allowance", "the first sixty land"),
            ("Envelope spent", "about one per second"),
            ("Tier table consulted", "the method is not in it"),
            ("More workers added", "same channel, same bucket"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sjcad-f",
        "Measuring the app's own send cadence from the ts values already in the channel",
        "An average hides this completely: five messages in one second and "
        "silence for an hour averages to almost nothing. The window slides, so "
        "a burst straddling a second boundary still counts as a burst.",
        ("Peak second, not average", "your own ts values"),
        [
            ("Three in one second", "carried by the allowance", "bad"),
            ("Two in one second", "the top of the envelope", "plain"),
            ("Fewer than five samples", "no verdict is offered", "plain"),
            ("Fifty blocks, one message", "the budget that is not scarce", "good"),
            ("A bucket per channel", "queue, do not drop", "good"),
        ],
    ),
}

V["slack/tier1-method-hammered"] = {
    "flow_intro": (
        "The problem chain is a number nobody chose meeting a number nobody "
        "read, and the interesting part is that everything else in the app stays "
        "healthy, so the investigation starts at the endpoint instead of at the "
        "traffic. The fix branch is a division, and it keeps not knowing the "
        "tier as a row of its own rather than folding it into a guess."
    ),
    "diagram_problem": D.chain(
        "sjtier-p",
        "A Tier 1 method placed inside a polling loop that runs every thirty seconds",
        "Backoff recovers a temporary overshoot. A loop asking for twice the "
        "budget is overshooting permanently, so the throughput is the tier "
        "whatever the client does; the sleeping only makes it quieter.",
        [
            ("Interval picked", "thirty felt responsive"),
            ("Tier never read", "it is on the method page"),
            ("One call throttles", "everything else is fine"),
            ("Looks like a bad endpoint", "not like a limit"),
            ("Backoff added", "quieter, not faster"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sjtier-f",
        "Dividing sixty by the polling interval against the documented tier floor",
        "The floor is what you may design against and the plus is headroom you "
        "are not entitled to. A schedule that only works on the burst allowance "
        "fails the first time the app has a busy minute for any other reason.",
        ("Sixty over the interval", "against the tier floor"),
        [
            ("Tier 1 in a loop", "no sleep makes this fit", "bad"),
            ("Past the floor", "throughput is the floor", "bad"),
            ("Tier not known here", "go read the method page", "plain"),
            ("Special tier", "the table does not apply", "plain"),
            ("Subscribed instead", "an event, not a timer", "good"),
        ],
    ),
}

V["slack/parallel-workers-share-quota"] = {
    "flow_intro": (
        "This is the only chain in the batch that loops, and the loop is the "
        "note: every replica received the same Retry-After, so every replica "
        "wakes at the same instant and empties the new window together. The fix "
        "branch is about the key rather than the rate, because two processes "
        "that land in one group are one caller however many hosts they run on."
    ),
    "diagram_problem": D.chain(
        "sjherd-p",
        "Eight replicas sharing one per method quota and resynchronising on every retry",
        "Correct, uniform, documented backoff is what builds the herd. "
        "Uniformity is exactly the wrong property when the wake up time is "
        "handed to every caller by the same server.",
        [
            ("Job is slow", "scaled to eight workers"),
            ("One bucket, not eight", "method, workspace, app"),
            ("All refused together", "identical Retry-After"),
            ("All sleep the same", "no jitter anywhere"),
        ],
        fail_at=1,
        loop=(3, 2, "the pool wakes in lockstep and empties the next window"),
    ),
    "diagram_fix": D.branch(
        "sjherd-f",
        "Grouping auth.test bodies by the quota key and subtracting to find unseen callers",
        "Being refused at a rate well under the floor is a measurement of "
        "everybody else. The difference is traffic that has to be coming from "
        "somewhere, and it is usually staging, a cron box, or a laptop.",
        ("team_id and bot_id", "the key Slack actually uses"),
        [
            ("Replicas in one group", "one budget between them", "bad"),
            ("Second token, same app", "still the same bucket", "bad"),
            ("Throttled below the floor", "somebody else is spending it", "bad"),
            ("Another workspace", "genuinely its own bucket", "plain"),
            ("One shared limiter", "plus jitter, plus channels", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
