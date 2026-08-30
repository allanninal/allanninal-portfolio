#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch J.

Four notes that all read usage buckets, which is precisely why the pictures
have to work hard. Neither API lists individual requests, so none of these
chains can end in an error the way a status-code note would: each one has to
end in a number that is missing from a report, and the four numbers are
different numbers.

The rejected parameter is a chain that fails at the model boundary and leaves
a request count with no tokens under it. The retry storm is a chain where
nothing fails at all and one series quietly detaches from the other. The
overload cluster fails outside the chain entirely, at the platform, so the
requests never reach the accounting. And the quiet project has no failing arrow
anywhere: the last step simply stops happening, and every alarm downstream of
it reads clean.

The fixes are branches, because each script sorts what it finds into named
states. Two of these branches carry a state whose only job is to hand the
reader to a different note, which is the honest thing to draw when two findings
share a symptom.

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

V["llm/reasoning-model-rejects-max-tokens"] = {
    "flow_intro": (
        "A model id changed, and the field that used to cap the answer is now "
        "refused by name rather than by value. Nothing in the aggregate says "
        "400, because the aggregate has no status codes in it. What it has is "
        "a request count sitting on top of no tokens at all, which is the only "
        "shape a body rejected before generation can make."
    ),
    "diagram_problem": D.chain(
        "llmzout-p",
        "A model swap that fails on every call and shows up as a quieter bill",
        "Every arrow here works except one, and the one that fails is caught "
        "by a wrapper that was written for transient errors.",
        [
            ("Model id is swapped", "the retirement was diaried"),
            ("Old field still sent", "max_tokens, unchanged"),
            ("Rejected on validation", "before the prompt is read"),
            ("Retry wrapper swallows it", "a 400 is not transient"),
            ("Spend for that model falls", "nobody investigates that"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmzout-f",
        "Sorting a bucket with requests and no tokens by where it stopped",
        "The split is on input tokens. Nothing read means the body never got "
        "past validation; something read means generation was blocked instead.",
        ("Requests above zero", "output tokens at zero"),
        [
            ("No input read either", "the field is refused by name", "bad"),
            ("Input read, nothing back", "verification or a filter", "plain"),
            ("Only part of the fleet", "one replica set never restarted", "bad"),
            ("Model lookup returns 404", "access, not a parameter", "plain"),
        ],
    ),
}

V["llm/requests-diverge-from-token-volume"] = {
    "flow_intro": (
        "Two series arrive on the same result object and they have stopped "
        "agreeing. The trap is that the obvious second opinion is not one: "
        "request growth over token growth is the change in tokens per request "
        "inverted, so it can never disagree. The independent evidence is where "
        "in the week the extra calls landed."
    ),
    "diagram_problem": D.chain(
        "llmstorm-p",
        "Two retry layers multiplying into requests that carry no tokens",
        "No step in this chain raises. The work completes, which is why the "
        "amplification survives a fortnight of standups.",
        [
            ("SDK retries by default", "429 and 5xx, twice"),
            ("Wrapper retries as well", "three times three"),
            ("Requests climb, tokens do not", "failed attempts generate little"),
            ("Rate limits bind sooner", "at volumes that used to fit"),
            ("Read as growth", "the invoice barely moved"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmstorm-f",
        "Sorting two growth rates and the concentration behind them",
        "Identical weekly ratios, two conclusions. Only the busiest tenth of "
        "the hours can tell a storm from a workload that got shorter.",
        ("Requests against tokens", "then hour by hour"),
        [
            ("Diverged, surplus in bursts", "retries amplify on failure", "bad"),
            ("Diverged, spread evenly", "shorter calls, no repair", "plain"),
            ("Tokens moved, requests flat", "prompt length, not volume", "plain"),
            ("Both moved together", "a customer, not a bug", "good"),
        ],
    ),
}

V["llm/overloaded-529-clusters"] = {
    "flow_intro": (
        "The messages usage report has no request count, so there is nothing "
        "to subtract your attempts from. Served requests have to be inferred "
        "from the work that was done, against a median baseline that a cluster "
        "cannot drag down, and only runs of adjacent minutes count: one bad "
        "minute is a call that straddled a bucket boundary."
    ),
    "diagram_problem": D.chain(
        "llm529-p",
        "A platform capacity condition that never reaches your accounting",
        "The failure happens before anything is billed, so the provider's own "
        "numbers have no record of the requests at all.",
        [
            ("Platform over capacity", "529 overloaded_error"),
            ("Client handles 429 and 500", "529 falls through"),
            ("Generic failure path", "the work is dropped"),
            ("No tokens billed", "no request count either"),
            ("Error rate looks normal", "logged as unexpected status"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llm529-f",
        "Sorting minutes by the work the billed tokens can account for",
        "Your attempts minus the attempts the tokens explain. The excess state "
        "exists so a recording gap is handed to the streaming note instead.",
        ("Attempts you counted", "against tokens billed"),
        [
            ("Three or more minutes short", "capacity, and retryable", "bad"),
            ("One minute short alone", "a call crossed a boundary", "plain"),
            ("More billed than attempted", "read the streaming note", "plain"),
            ("Tokens match the attempts", "nothing was lost here", "good"),
        ],
    ),
}

V["llm/live-project-zero-usage-buckets"] = {
    "flow_intro": (
        "The only note in the batch whose finding is an absence. Every alarm a "
        "team owns is a ceiling, and a ceiling reads perfectly at zero. The "
        "endpoint returns a bucket for every day you asked for, so the day "
        "axis comes from the window rather than from the response, and the "
        "check is directional because a launch is a death read backwards."
    ),
    "diagram_problem": D.chain(
        "llmquiet-p",
        "An integration that stops calling and every dashboard reading clean",
        "There is no failing arrow to draw. The last step stops happening, and "
        "everything measured downstream of it is a threshold at zero.",
        [
            ("Flag flips in a release", "an unrelated one"),
            ("Call site never runs", "nothing is attempted"),
            ("No error, no latency", "both perfect at zero"),
            ("Alarms are all ceilings", "none has a floor"),
            ("A customer asks", "eleven days later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmquiet-f",
        "Sorting a project by which half of the window held its traffic",
        "Direction decides everything. Reverse the test and it fires on every "
        "new project once, and is muted by the end of the week.",
        ("Busy early, silent late", "complete days only"),
        [
            ("Quiet on every surface", "credential, flag or consumer", "bad"),
            ("Quiet on one surface only", "one code path, not the key", "bad"),
            ("Silent early, busy late", "a launch, not a death", "good"),
            ("Traffic in the last two days", "still live, nothing to say", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
