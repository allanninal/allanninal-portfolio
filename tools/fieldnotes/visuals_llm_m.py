#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch M.

Four notes about one number. The cached share is zero, and the number says
nothing at all about why. Three notes already published in this section read
that same number, so all four pictures here are drawn around the one thing
that separates their finding from everybody else's, and every fix branch hands
at least one of its outcomes to a different note by name.

The first bracket a size. Its fix branch is the only one in the section whose
top outcome is a measurement rather than a verdict: caching that works below
one floor and stops above another puts the prefix between the two, on a report
that carries no request count and no prompt.

The second is a slope. Every other cache in a stack gets better under load and
this one gets worse, so its problem chain ends on the sentence nobody expects,
and its fix branch sorts a ratio by how it responds to the request rate rather
than by how large it is.

The third is a position. Two hours with identical traffic get different
verdicts purely because of what happened in the hours before them, so its fix
branch is keyed on gap length, and the two bad outcomes carry two different
repairs: one idle hour means no retention setting helps and the schedule has
to change, a full day means the setting exists and was never set.

The fourth is a changepoint that has to survive a search. A cold cache on the
first day of a new model is correct behaviour, so the healthy outcome in its
fix branch is a dip that recovers, and the branch beside it is the largest
step landing somewhere other than the switch.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further: visuals.py imports several
# of these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/prompt-below-model-cache-minimum"] = {
    "flow_intro": (
        "Nothing in this chain raises and nothing in it is misconfigured. The "
        "breakpoint is set, the request validates, and the API declines to "
        "cache a prefix that never cleared the model's floor. The only trace "
        "is two counters that stay at exactly zero, which is the same trace "
        "three other problems leave. What separates them is a contrast the "
        "account is already running: one key, one prompt, several floors."
    ),
    "diagram_problem": D.chain(
        "llmfloor-p",
        "A cache breakpoint accepted and discarded because the prefix is too short",
        "There is no failing call here. The parameter is valid, the response "
        "is fine, and the discount was never available in the first place.",
        [
            ("cache_control is set", "and has been since March"),
            ("Prefix is 1,500 tokens", "long enough, surely"),
            ("The floor is 4,096", "the breakpoint is dropped"),
            ("No error, no header", "the request is valid"),
            ("Both counters at zero", "and the bill never bends"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmfloor-f",
        "Sorting one key's models by whether caching survives their minimum",
        "The top outcome is a size, not a verdict. The prefix has to be at "
        "least the highest floor that works and under the lowest that does not.",
        ("Models on one key", "sorted by cache minimum"),
        [
            ("Caches low, silent high", "the prefix sits between the two floors", "bad"),
            ("Silent under a caching floor", "it cleared the higher bar already", "plain"),
            ("One model, no contrast", "two notes stay open, and it says so", "plain"),
            ("Caching at every floor", "nothing here to bracket", "good"),
        ],
    ),
}

V["llm/prompt-cache-key-not-set"] = {
    "flow_intro": (
        "This is the only cache fault in the section that gets worse when you "
        "add capacity, which is why it survives so long: every instinct says "
        "volume keeps a cache warm. Here volume spreads the same prompt over "
        "more machines, none of which has seen it before. The evidence is a "
        "slope rather than a level, and the hours that follow a gap are thrown "
        "away first, because those run cold whatever the routing did."
    ),
    "diagram_problem": D.chain(
        "llmscat-p",
        "Identical prompts scattered across a fleet, each backend seeing them cold",
        "Nothing on the busy path is different. There are simply more machines "
        "in it, and the prefix is new to every one of them.",
        [
            ("One template, one prefix", "identical on every call"),
            ("Autoscaler adds workers", "the fleet gets wider"),
            ("Each backend is cold", "no worker sees it twice"),
            ("Peak hour caches worst", "the discount inverts"),
            ("Scaling makes it worse", "which nobody expects"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmscat-f",
        "Sorting an hourly cached share by how it responds to the request rate",
        "The level is shared with three other notes. The response to load is "
        "not, and it is the only thing here that points at routing.",
        ("The hourly cached share", "against the request rate"),
        [
            ("Falls as the load rises", "requests miss a cache that is warm", "bad"),
            ("Flat at every load", "the prefix moves between calls", "plain"),
            ("Cold only after gaps", "that is the retention note", "plain"),
            ("Climbs with the load", "density is keeping entries warm", "good"),
        ],
    ),
}

V["llm/prompt-cache-retention-left-at-default"] = {
    "flow_intro": (
        "The workloads this ruins are the ones that look most cacheable on "
        "paper. A nightly batch sends the same long prefix a hundred thousand "
        "times, so the discount should be enormous, and the first call pays "
        "full price for a prompt that has not changed in months. The signal is "
        "positional: two hours with identical traffic get opposite verdicts "
        "because of what happened in the hours before them."
    ),
    "diagram_problem": D.chain(
        "llmevict-p",
        "A scheduled job whose cache entry expires long before the job returns",
        "Every step here is the documented behaviour. The prompt is perfect "
        "and the schedule is the fault.",
        [
            ("Batch runs at 02:00", "the same prefix for a year"),
            ("First call writes it", "and pays the premium"),
            ("Retention runs out", "the default is minutes"),
            ("Idle until tomorrow", "nothing left to match"),
            ("Cold on the first hour", "every single night"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmevict-f",
        "Sorting resumption hours by how long the traffic had been away",
        "The shortest collapsed band decides the repair. One idle hour and no "
        "setting saves you; a full day and the setting exists already.",
        ("The cached share", "binned by the gap before it"),
        [
            ("Gone after one idle hour", "no ttl covers that: reshape the schedule", "bad"),
            ("Gone after a day away", "the 24h retention that was never set", "bad"),
            ("Busy hours cold too", "the prefix, not the gap", "plain"),
            ("Warm when it resumes", "the entry outlived the quiet stretch", "good"),
        ],
    ),
}

V["llm/cache-hit-rate-collapsed-after-model-change"] = {
    "flow_intro": (
        "A model switch starts from a cold cache by definition, so the first "
        "day is expected to be bad and a check that fires on it is simply "
        "wrong. What matters is the days after. The claim that the collapse "
        "belongs to the switch then has to survive a search of the whole "
        "window: the largest step down anywhere in it must land on the day the "
        "new id first appears, or the switch is not the explanation."
    ),
    "diagram_problem": D.chain(
        "llmstep-p",
        "A model migration that lowers the token rate and switches caching off",
        "The migration was reviewed for quality and for price, and both were "
        "better. The prefix stopped qualifying, and nothing said so.",
        [
            ("A one line model swap", "rate and latency improve"),
            ("Caches are per model", "day one is cold by design"),
            ("The new floor is higher", "and the prefix falls short"),
            ("It never comes back", "week after week"),
            ("Input bill up a third", "with no line item"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmstep-f",
        "Sorting a daily cache read share against the day a new model id arrives",
        "Alignment is what makes this refutable. Any month with a migration "
        "and a decline in it can be told as a story if you only look where "
        "you expect.",
        ("The daily share", "and when the id first appears"),
        [
            ("Biggest step at the switch", "sustained, and the floor moved", "bad"),
            ("Biggest step elsewhere", "something else changed that day", "plain"),
            ("New id on 3% of input", "too small to move the ratio", "plain"),
            ("Down one day, back the next", "a cold cache filling up", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
