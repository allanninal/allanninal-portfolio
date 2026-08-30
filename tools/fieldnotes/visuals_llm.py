#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch A.

Four problems that all start from a model string in a config file and end in four
different places: a date that passed, a date that has not, an id that is no longer
listed anywhere, and an id that still works but no longer means the same thing. The
problem chains differ because the failures differ; the fix is a branch every time,
because each script sorts what it finds rather than guessing at it. Drawn in teal.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/model-past-shutdown-date"] = {
    "flow_intro": (
        "The script compares one field against one date, and the reason that is "
        "worth writing down is the ambiguity it removes: the 404 alone cannot "
        "tell a retired model from a typo, and the models list can."
    ),
    "diagram_problem": D.chain(
        "llmshut-p",
        "A pinned snapshot that routes normally until the published date, then stops",
        "Nothing along the way carries a warning. The successful calls before the "
        "date look exactly like the successful calls a year earlier.",
        [
            ("Snapshot pinned", "the correct thing to do"),
            ("Date published", "months ahead, on a page"),
            ("Calls keep passing", "no header, no warning"),
            ("Shutdown date", "routing removed"),
            ("404 model_not_found", "reads like a typo"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmshut-f",
        "Sorting model ids by what the shutdown_date field actually says",
        "A date of today is not a warning and a null date is not a promise, so "
        "neither is allowed to collapse into the state next to it.",
        ("shutdown_date on each id", "compared against today"),
        [
            ("Date already passed", "dead now, calls are failing", "bad"),
            ("Date is today", "an outage in progress", "bad"),
            ("Date in the future", "the 90 day check owns this", "plain"),
            ("No date at all", "unscheduled, not permanent", "good"),
        ],
    ),
}

V["llm/model-retiring-within-90-days"] = {
    "flow_intro": (
        "The date comes from the models list and the traffic comes from the "
        "organization usage endpoint, on a different credential. The finding is "
        "the join: a deadline without a size gets deferred at every planning "
        "meeting until it cannot be."
    ),
    "diagram_problem": D.chain(
        "llmwin-p",
        "A deadline that exists in a field nobody reads until it has passed",
        "Every channel that could have carried the notice is one a busy team "
        "misses, and the request path carries nothing at all.",
        [
            ("Retirement announced", "three to six months out"),
            ("Notice goes to email", "and a changelog"),
            ("Nothing reads the field", "no check exists"),
            ("Migration deferred", "nobody can size it"),
            ("Deadline arrives", "every call site at once"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmwin-f",
        "Sorting dated model ids into a schedule by days left and by traffic",
        "Zero requests is a finding rather than a pass, and no admin key means "
        "unmeasured rather than unused. Those two must not print the same.",
        ("Dates joined to usage", "window and urgency as arguments"),
        [
            ("Under a month left", "schedule the work now", "bad"),
            ("Inside the window", "next cycle, with a size", "bad"),
            ("Outside the window", "nothing to do yet", "good"),
            ("Dated but no traffic", "a config string, not a service", "plain"),
        ],
    ),
}

V["llm/retired-model-id-still-in-code"] = {
    "flow_intro": (
        "There is no date to read on this API, so the whole detection is a set "
        "difference: your own model strings on one side, the live models list on "
        "the other, and the finding is whatever is only on your side."
    ),
    "diagram_problem": D.chain(
        "llmdead-p",
        "A model string that survives the migration in a path nobody exercises",
        "The main call path moved months ago. The string that did not move is in "
        "the branch that only runs when something is already wrong.",
        [
            ("Main path migrated", "tested, shipped, closed"),
            ("String left in a fallback", "and a monthly batch"),
            ("Id retired", "dropped from the list"),
            ("Rare path runs", "a bad day, or the 1st"),
            ("404 not_found_error", "in a log nobody tails"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmdead-f",
        "Sorting your model strings against the list of what is callable today",
        "Missing from the live list is not the same as retired. Bedrock and "
        "Vertex retire later, so an unplaceable id is reported as unknown.",
        ("Config strings diffed", "against GET /v1/models"),
        [
            ("In the live list", "callable by this workspace", "good"),
            ("Missing, on the table", "retired, with a replacement", "bad"),
            ("Missing, not on it", "typo, or another platform", "plain"),
            ("Listed but table says dead", "the table is stale, not the API", "plain"),
        ],
    ),
}

V["llm/floating-alias-instead-of-pinned-snapshot"] = {
    "flow_intro": (
        "The only question this script asks is what the string resolves to, "
        "because the shape of the name stopped answering it: before the 4.6 "
        "generation a dateless id was a pointer, and from 4.6 on it is the "
        "snapshot itself."
    ),
    "diagram_problem": D.chain(
        "llmalias-p",
        "An alias repointed at new weights with no deploy and no error",
        "Nothing in this chain returns a status code. Every symptom is a number "
        "that moved by an amount small enough to be called noise.",
        [
            ("Alias in the config", "convenient, undated"),
            ("Pointer moves", "no notice, no deploy"),
            ("Same string, new model", "requests keep succeeding"),
            ("Evals and cache drift", "a few points each"),
            ("Blamed on the data", "days of the wrong search"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmalias-f",
        "Sorting model strings by what the Models API resolves each one to",
        "The dateless snapshot is the case that matters: appending a date to it "
        "is the obvious repair and it returns a 404.",
        ("Each string resolved", "asked, not pattern matched"),
        [
            ("Resolves elsewhere", "an alias, pin what it returns", "bad"),
            ("Dated, resolves to itself", "already pinned", "good"),
            ("Dateless, resolves to itself", "pinned, do not add a date", "good"),
            ("Resolves to nothing", "404, likely a date appended", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
