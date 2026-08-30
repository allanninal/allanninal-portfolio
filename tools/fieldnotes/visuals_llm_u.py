#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch U.

Four surfaces closing rather than four models retiring, which is the premise
and also the hazard: drawn carelessly these are one picture of a 404 repeated
four times. So none of the four fix branches sorts a status code. Each sorts
something the endpoint cannot tell you on its own.

`llmasst` is the only one drawn past its date, so its polarity is inverted: the
404 branch is the healthy one and the 200 branch is the finding. Its outcomes
are about a *pair* of paths, because a 404 from a closed endpoint and a 404
from a key that reads nothing are the same picture until a control path is
drawn beside it.

`llmsora` is the only closure with nothing on the right-hand side to migrate
to, so its fix branch sorts assets by *deadline* rather than by status. Two
clocks, one per asset, and the outcomes are which of the two lands first. The
one outcome that would ruin the note, a helpful successor model, is deliberately
absent from the drawing as well as from the code.

`llmexpo` sorts three surfaces by how far the API reaches into each, which is a
different axis from every other branch in the batch. Its bottom outcome is a
person rather than a state, because one of the three has no endpoint at all and
a diagram that left it out would look complete while covering two thirds of a
problem.

`llmftgate` is the only chain here where nothing breaks. Both of its clocks run
in the background of a working system, and its fix branch is the only one whose
outcomes come in pairs: one verb refused while the other is still serving. That
crossing is the finding, so the branch is drawn as two verbs rather than as one
endpoint.

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

V["llm/assistants-api-already-shut-down"] = {
    "flow_intro": (
        "Past a published shutdown date the usual reading runs backwards. A "
        "404 is the documented answer and tells you nothing you did not "
        "already know; a 200 is the finding, because it means this "
        "organization is still being served an API that is over. And one "
        "status code cannot carry either claim, since a closed path and a key "
        "that reads nothing produce the same number. So the unit is a pair of "
        "paths on one credential, and the date the traffic actually stopped is "
        "a separate, weaker reading kept separate on purpose."
    ),
    "diagram_problem": D.chain(
        "llmasst-p",
        "How an endpoint family closing looks exactly like a mistyped id",
        "Every step is the reasonable one. The hour is spent on the id "
        "because a 404 is almost always about an id.",
        [
            ("Runs call threads", "the shape of the old API"),
            ("Shutdown date passes", "nothing is deployed"),
            ("404 on every call", "same class as a typo"),
            ("Model id checked first", "and it is fine"),
            ("Staging still answers", "so the theory breaks"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmasst-f",
        "Sorting one credential by path rather than grading a status code",
        "The path is the only thing that varies. Read the outcomes with the "
        "polarity inverted: the 404 row is the calm one.",
        ("Subject and control path", "same key, same headers"),
        [
            ("Control 200, subject 404", "closed, as published", "good"),
            ("Control 200, subject 200", "still on grace, and undated", "bad"),
            ("Control not 200", "nothing was proved at all", "plain"),
            ("Requests end on the date", "the closure, not a deploy", "bad"),
            ("Requests end elsewhere", "something you did", "plain"),
        ],
    ),
}

V["llm/sora-videos-api-no-replacement"] = {
    "flow_intro": (
        "Every other deprecation in this section ends in a string you paste "
        "into a config file. This one ends in a decision, because the "
        "replacement column is empty for all five ids and no other model "
        "absorbs the work. What is worth measuring instead is time, twice "
        "over: the endpoint has a date, and every rendered asset carries an "
        "expiry of its own. The deadline that matters is per file, and for "
        "some files it is the earlier one."
    ),
    "diagram_problem": D.chain(
        "llmsora-p",
        "How a capability removal is mistaken for a model retirement",
        "The muscle memory is right for every other row in the table and "
        "wrong for this one, and the empty cell looks like a gap.",
        [
            ("Notice arrives", "one date, five model ids"),
            ("Triaged as a swap", "find id, write successor"),
            ("Replacement cell empty", "read as not filled in yet"),
            ("Six months pass", "endpoint answers throughout"),
            ("Feature 404s at once", "and the renders go too"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmsora-f",
        "Sorting stored assets by deadline rather than by status code",
        "Nothing here sorts by health, because nothing is unhealthy. Each "
        "outcome is which of the two clocks runs out first.",
        ("Every asset, two clocks", "own expiry and shutdown"),
        [
            ("Expiry lands first", "the front of the queue", "bad"),
            ("Expiry already past", "the bytes are gone", "bad"),
            ("No expiry of its own", "inherits the endpoint date", "bad"),
            ("Endpoint closes first", "download before the date", "bad"),
            ("Successor to move to", "there is not one", "plain"),
        ],
    ),
}

V["llm/prompts-evals-agentbuilder-sunset"] = {
    "flow_intro": (
        "Three things close on one date and the code change is the small half "
        "of the work. What is actually at risk is content held on the "
        "provider's side: prompt versions, graders, published workflows. So "
        "the useful question is not whether an endpoint answers but how far "
        "the API reaches into each surface, and the answer is different three "
        "times. One lists cleanly, one has no documented listing, and one has "
        "no endpoints at all."
    ),
    "diagram_problem": D.chain(
        "llmexpo-p",
        "How a stored prompt disappears without breaking a single build",
        "Nothing in review shows it. The call site is one ordinary line and "
        "the words it stands for were never in the repository.",
        [
            ("Prompt saved server side", "versioned, out of the repo"),
            ("Call site holds an id", "one ordinary looking line"),
            ("Notice read as a rewrite", "queued behind other work"),
            ("Date passes", "code still compiles"),
            ("Text is simply gone", "nothing to restore from"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmexpo-f",
        "Sorting three closing surfaces by how far the API reaches into each",
        "The last row is an owner rather than a state. A surface with no "
        "endpoint cannot be covered by a script, and hiding it looks green.",
        ("Three surfaces, one date", "graded by reach"),
        [
            ("Listing returns full objects", "the listing is the export", "good"),
            ("No documented listing", "ids come from your tree", "bad"),
            ("Id resolves on probe", "exportable one at a time", "good"),
            ("Id does not resolve", "dashboard, before the date", "bad"),
            ("No endpoint exists at all", "a person, not a script", "bad"),
        ],
    ),
}

V["llm/fine-tuning-jobs-blocked"] = {
    "flow_intro": (
        "This is the only note in the batch where the endpoint keeps working. "
        "Jobs list, models resolve, inference bills, and one verb has quietly "
        "stopped being accepted. Creating and serving are separate rights with "
        "separate clocks, and the create clock is not a date at all: it is a "
        "rolling window over your own recent traffic, which closes on a quiet "
        "week when nobody does anything. That is readable, so the script "
        "computes it rather than testing it by submitting a job."
    ),
    "diagram_problem": D.chain(
        "llmftgate-p",
        "How the right to retrain expires while nothing at all breaks",
        "No error, no deploy, no notification. The window closed because "
        "somebody stopped doing something, which is the hardest change to see.",
        [
            ("Fine tune serves traffic", "everything green"),
            ("Replaced by a prompt", "one batch job left"),
            ("Last ft call ages out", "sixty days, quietly"),
            ("Retrain is now refused", "on the day it is needed"),
            ("Bases die in October", "before the retrain window"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmftgate-f",
        "Sorting one resource by verb rather than grading the endpoint",
        "Each outcome names a verb. The pair that matters is the one where "
        "they disagree: refused on create, healthy on serve.",
        ("One resource, two verbs", "create against serve"),
        [
            ("No ft traffic in 60 days", "create already refused", "bad"),
            ("Job list is empty", "create was never available", "bad"),
            ("Window closing this month", "retrain while you still can", "bad"),
            ("Base dated by the API", "serving ends on that day", "bad"),
            ("Base has no date anywhere", "undated, and not safe", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
