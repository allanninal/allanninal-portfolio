#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch K.

Four notes that read the same stored Response object and all four end with a
JSON parse that failed, which makes this the batch most at risk of drawing one
picture four times. The separation has to be visible in the shapes or it is not
really there.

So each problem chain fails at a different arrow, and the arrow is the point.
The truncation chain fails at generation: the ceiling arrives mid-object and
everything after it is a prefix. The refusal chain does not fail at generation
at all, because the model answered perfectly well and the answer was "no"; it
fails at the reader, which is why the red arrow is one box further along than
you expect. The advisory-schema chain never fails anywhere: every arrow works
and the guarantee was simply never bought, so what is drawn is the request that
was accepted rather than a response that broke. And the arguments chain fails
outside the API entirely, in the dispatcher, which is the only one of the four
where the exception is raised by code you wrote.

The fixes are branches because each script sorts what it finds into named
states, and in this batch most of those branches carry at least one state whose
whole job is to hand the reader to a sibling note. Four notes that share a
symptom have to be explicit about where each one stops, and a branch is the
honest place to draw that.

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

V["llm/structured-output-truncated-by-length"] = {
    "flow_intro": (
        "Structured output guarantees the model follows the schema. It does "
        "not guarantee the model finishes. When the ceiling arrives mid-object "
        "the request has still completed successfully by every measure the "
        "transport layer has: 200, a body, a usage block, a bill. What comes "
        "back is a valid prefix of the answer you wanted, and a prefix of "
        "valid JSON is not JSON."
    ),
    "diagram_problem": D.chain(
        "llmcut-p",
        "An output ceiling reached mid-object and a 200 carrying half a record",
        "The only failing arrow is inside generation. Everything downstream of "
        "it behaves exactly as it does on a good day.",
        [
            ("Schema promises a shape", "strict is set, correctly"),
            ("Ceiling arrives mid-object", "the string is still open"),
            ("Status 200 with a body", "incomplete, not an error"),
            ("Parse throws in a worker", "far from the API call"),
            ("Retry class says no", "a 200 is not transient"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "llmcut-f",
        "Sorting a stored response by why it stopped before it is parsed",
        "The reason field decides the repair. Two of these states exist only "
        "to hand the reader to a different note in this batch.",
        ("Read status first", "then incomplete_details"),
        [
            ("Stopped on the ceiling", "raise it, or shrink the schema", "bad"),
            ("Ceiling spent on thinking", "no visible answer started", "bad"),
            ("Declined, not cut", "read the refusal note", "plain"),
            ("Finished, still unparseable", "the schema was advisory", "plain"),
            ("Finished and parses", "nothing to do here", "good"),
        ],
    ),
}

V["llm/refusal-field-ignored"] = {
    "flow_intro": (
        "A refusal is not an error and it is not a truncation. The model was "
        "asked, it declined, and it said so in a content type built for the "
        "purpose so the refusal would not have to be squeezed into your "
        "schema. Everything about that works. The failure is one step later, "
        "in a parser that reaches straight for the text it expected and finds "
        "a channel it has never been taught to look at."
    ),
    "diagram_problem": D.chain(
        "llmrefu-p",
        "A model that declined and a parser that never looked at the channel",
        "Generation succeeded. The red arrow is one box further along than in "
        "a truncation, because nothing about the response is broken.",
        [
            ("Input reaches the model", "billed, read, understood"),
            ("Model declines", "a refusal content item"),
            ("Reader takes the text", "the field it always uses"),
            ("Parsed value is empty", "None, or an empty record"),
            ("Empty row is written", "no error anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmrefu-f",
        "Sorting a stored response by whether the answer was declined",
        "Refusal and filter stop are different events with different owners. "
        "A rate per prompt template is the finding, not one refusal.",
        ("Scan the content types", "before reading any text"),
        [
            ("Refusal item present", "surface it, never parse it", "bad"),
            ("Refusal after partial text", "the turn changed its mind", "bad"),
            ("Stopped by the filter", "platform, not the model", "plain"),
            ("Cut off instead", "read the truncation note", "plain"),
            ("Answered normally", "parse it as usual", "good"),
        ],
    ),
}

V["llm/strict-false-schema-silently-ignored"] = {
    "flow_intro": (
        "The only note in this batch whose problem chain has no failing arrow "
        "at all. Every step works. The schema was attached, the request was "
        "accepted, the model followed the schema most of the time, and the "
        "one call in fifty that it did not follow is the one your validator "
        "sees. What is drawn here is the request that was accepted, because "
        "the guarantee was never bought and nothing along the way said so."
    ),
    "diagram_problem": D.chain(
        "llmadvis-p",
        "A schema attached without strict and accepted exactly like a strict one",
        "Nothing here errors, which is the whole difficulty. The schema is a "
        "hint the model usually follows, and usually is not a contract.",
        [
            ("Schema fails a rule", "one object allows extras"),
            ("strict is dropped", "the request now succeeds"),
            ("Accepted with no warning", "both forms are legal"),
            ("Followed most of the time", "green in every test run"),
            ("Validator throws in prod", "one call in fifty"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmadvis-f",
        "Sorting a stored response by what its echoed format actually promised",
        "Read the format the response carries, not the constant in your "
        "source. Then read why strict was dropped, which is always a schema.",
        ("Read the echoed format", "and every tool beside it"),
        [
            ("json_schema, strict absent", "advisory, not enforced", "bad"),
            ("Legacy json_object", "valid JSON, any shape", "bad"),
            ("Strict text, loose tools", "the gap is per tool", "bad"),
            ("Strict everywhere", "the contract is real", "good"),
        ],
    ),
}

V["llm/tool-call-arguments-unparseable"] = {
    "flow_intro": (
        "Function arguments come back JSON encoded, as a string, and the docs "
        "are explicit that the string may be malformed. Two quite different "
        "faults arrive through that one field. One is a string that will not "
        "parse. The other is a string that parses perfectly and describes a "
        "call your tool cannot accept, and that second one is never caught by "
        "any amount of care around json.loads."
    ),
    "diagram_problem": D.chain(
        "llmargs-p",
        "A tool call that parses cleanly and still cannot be dispatched",
        "The failing arrow is outside the provider. The API returned exactly "
        "what it promised and the exception is raised by your own code.",
        [
            ("Model emits a call", "arguments as a string"),
            ("String parses fine", "json.loads is happy"),
            ("Handler unpacks it", "a key that is not there"),
            ("Turn dies mid-loop", "the tool result never returns"),
            ("Agent retries the turn", "same call, same crash"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmargs-f",
        "Sorting one function call by where between wire and handler it fails",
        "Parsing is the first gate and never the only one. The state that "
        "matters most is the call that passed the parse and failed the schema.",
        ("Parse, then validate", "against the declared tool"),
        [
            ("Parses, breaks the schema", "the contract, not the syntax", "bad"),
            ("Will not parse at all", "no grammar was constraining it", "bad"),
            ("Cut off mid-argument", "read the truncation note", "plain"),
            ("Tool name unknown", "a lookup error, not a parse", "plain"),
            ("Parses and validates", "safe to dispatch", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
