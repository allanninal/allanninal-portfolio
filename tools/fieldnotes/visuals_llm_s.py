#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch S.

Four ceilings nobody in the room set, and the reason they need four diagrams
rather than one is that each of them is refused by a different thing. The
section already draws four rate limit chains that all end at the same place: a
bucket empties, a 429 comes back, and the reading is which bucket it was. None
of these four end there.

`llmwsov` ends in a number somebody typed once, on a screen nobody has opened
since, which is why its chain has no traffic in it at all until the last box.
Its fix branch is the only one in the batch whose outcomes are configuration
states rather than observations, and one of those outcomes is the quiet one
worth the whole diagram: an override equal to today's organization value, which
looks like a no-op and is a pin.

`llmramp` is the shape note. Its chain is deliberately drawn as a climb rather
than a wall, and the failure arrow sits between two boxes that are both well
under the limit, because that is the entire argument: nothing here is at its
ceiling and the request is still refused. Its fix branch grades a factor
against a level, and hands two of its five outcomes back to the published
limiter notes, because a ramp reported next to a saturated limiter is a
coincidence dressed up as a cause.

`llmrafter` is about transport, so its chain is the only one in the batch with a
middlebox in it, and the fault is drawn at the hop rather than at either end.
The fix branch is a two path diff, and its outcomes include the state that is
worse than loss: headers that arrive with values something invented, which the
client has no way to disbelieve.

`llmflexq` is the absence note. Its chain deliberately ends with a box that is
not an error, because the tier refused capacity, was not charged, and therefore
left nothing behind at all. Its fix branch is the only one here whose best
outcome is a negative result: a quiet hour with no other traffic in it is a
quiet night, and grading it as a capacity failure would be the easiest possible
way to lose the reader's trust.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/project-rate-limit-below-org"] = {
    "flow_intro": (
        "Nothing in this chain is traffic until the last box, which is what "
        "makes it survive: the decision that refuses production was taken "
        "months earlier, on a container that was doing something else at the "
        "time. Anthropic returns the override and the organization value on "
        "the same object, so the comparison is exact once anybody makes it. "
        "OpenAI returns no organization value at all, so the same reading has "
        "to be assembled by comparing projects to each other."
    ),
    "diagram_problem": D.chain(
        "llmwsov-p",
        "How a ceiling set for staging ends up refusing production",
        "Every step is reasonable on the day it happens. The number that "
        "refuses you is the only one nobody looks at again.",
        [
            ("Container made for isolation", "good advice, followed"),
            ("Limit sized for that week", "small, because staging"),
            ("Id reused for production", "one line, not a ticket"),
            ("429 at a fifth of volume", "org has plenty of room"),
            ("Tier increase changes nothing", "wrong number moved"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmwsov-f",
        "Grading a container's configured ceiling against the organization's",
        "The override and the organization value are read together, because "
        "the interesting states are the ones only the pair can show.",
        ("Every container's limits", "value against org_limit"),
        [
            ("Far under the org value", "the throttle that binds", "bad"),
            ("Equal to the org value", "a pin, not a no op", "bad"),
            ("Some limiters inherited", "lopsided, by accident", "plain"),
            ("No organization number", "unjudgeable, not fine", "plain"),
            ("No override at all", "tracks every increase", "good"),
        ],
    ),
}

V["llm/acceleration-limit-on-traffic-spike"] = {
    "flow_intro": (
        "The chain that matters here is a climb rather than a wall. Every box "
        "in it is under the published limit, including the one where the 429s "
        "start, and that is the whole argument: the tier table describes a "
        "level you may sustain and says nothing about how fast you are allowed "
        "to reach it. A limit increase moves the wall this traffic never "
        "touched."
    ),
    "diagram_problem": D.chain(
        "llmramp-p",
        "How a launch trips a limit it never approaches",
        "The worst minute in the window uses a fifth of the ceiling, which is "
        "why the graph reads as an alibi rather than as evidence.",
        [
            ("Fan out at the top of the hour", "cron, backfill or launch"),
            ("Traffic jumps in one minute", "fifteenfold, from quiet"),
            ("Acceleration limit fires", "sharp increase, not size"),
            ("Peak minute still under limit", "usage graph looks fine"),
            ("Increase requested and granted", "same failure next week"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmramp-f",
        "Reading the step between minutes against the level inside them",
        "Saturation is graded first. A steep ramp next to a full limiter has "
        "an ordinary explanation and belongs to the limiter notes.",
        ("Adjacent one minute buckets", "factor and peak together"),
        [
            ("Steep step, low peak", "acceleration, not the number", "bad"),
            ("Steep step, high peak", "pace it and ask for more", "bad"),
            ("Peak at the ceiling", "the input or output note", "plain"),
            ("Limits under the tier table", "evaluation tier, probably", "plain"),
            ("No step worth the name", "shape is not the problem", "good"),
        ],
    ),
}

V["llm/retry-after-header-ignored"] = {
    "flow_intro": (
        "The only chain in the batch with a middlebox in it, and the fault is "
        "drawn at the hop rather than at either end, because both ends are "
        "behaving correctly. The API sends the wait instruction and the client "
        "reads it; the allowlist between them was written before either "
        "existed. Since the header itself only appears on a 429, the probe "
        "watches the family that arrives on every response instead."
    ),
    "diagram_problem": D.chain(
        "llmrafter-p",
        "How a correct backoff ends up retrying into an empty bucket",
        "Nobody wrote a bug. The wait instruction is sent, dropped in "
        "transit, and its absence reads as a missing key.",
        [
            ("429 with retry-after", "the API says how long"),
            ("Proxy forwards an allowlist", "written years earlier"),
            ("Header never reaches client", "the key is simply absent"),
            ("Handler falls back to one second", "the documented default"),
            ("Retry fails, reset pushed out", "and the loop repeats"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmrafter-f",
        "Diffing the header family across the direct path and the gateway",
        "Only limit values are compared. Remaining and reset are supposed to "
        "differ between two calls a second apart.",
        ("One GET, issued twice", "direct and through the gateway"),
        [
            ("Present direct, gone via gateway", "your allowlist, in one line", "bad"),
            ("Limit values disagree", "invented, not forwarded", "bad"),
            ("Reset already elapsed", "any sleep computed is zero", "bad"),
            ("Clock differs from the server", "absolute resets misfire", "plain"),
            ("Same on both paths", "the instruction will arrive", "good"),
        ],
    ),
}

V["llm/flex-resource-unavailable-timeouts"] = {
    "flow_intro": (
        "This chain ends in a box that is not an error, which is unusual "
        "enough to be the point. Capacity was refused, nothing was charged, "
        "and an unbilled request never reaches a usage report, so there is no "
        "row to find and no counter to read. What is left is a hole in the "
        "hours, and reading a hole responsibly means proving the organization "
        "was awake at the time."
    ),
    "diagram_problem": D.chain(
        "llmflexq-p",
        "How work sent to the cheap tier disappears without an error",
        "The invoice goes down, which is what everybody was expecting to see, "
        "and is the reason nobody looks at the record count.",
        [
            ("Job moved to the flex tier", "priced like batch"),
            ("Capacity unavailable", "429, best effort tier"),
            ("Not charged for the refusal", "the humane behaviour"),
            ("No row in the usage report", "unbilled means unrecorded"),
            ("Records quietly not processed", "and the bill looks better"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmflexq-f",
        "Grading flex volume per hour against the rest of the organization",
        "An empty hour is only evidence if something else was being served in "
        "it. Otherwise it is a night the job did not run.",
        ("Hourly usage by service tier", "flex against every other"),
        [
            ("Flex collapses, others serve", "capacity was refused", "bad"),
            ("Named model, no flex ever", "the parameter never arrived", "bad"),
            ("Too few served hours", "no median worth having", "plain"),
            ("Empty hour, nothing else ran", "a quiet night, not a fault", "plain"),
            ("Flex steady across the week", "the discount is real", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
