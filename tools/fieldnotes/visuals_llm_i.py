#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch I.

Four ceilings you can know about before you spend anything, and the drawing
risk is that all four become the same picture of a bar filling up. They are not
the same ceiling and they are not even the same unit, so each problem chain is
built around its own unit: tokens accumulating in a window, megabytes inflating
through base64, one integer inherited across two model tiers, and a clock.

The fixes are branches because every script here sorts what it finds into named
states rather than answering yes or no. The four branch shapes deliberately
diverge: the window one splits on which of the two overflow modes you get, the
byte one splits across three unrelated ceilings that all return the same
rejection, the cap one splits on where the ceiling was read from, and the clock
one splits on the transport rather than on any size.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
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

V["llm/prompt-too-long-context-overflow"] = {
    "flow_intro": (
        "Nobody made this change. Retrieval widened, the conversation grew and "
        "a colleague added a tool, and the sum crossed a line no single "
        "component owns. The fix counts the real assembled body for free and "
        "then adds the one term everybody leaves out, because max_tokens "
        "reserves window space before a single word is written."
    ),
    "diagram_problem": D.chain(
        "llmpre-p",
        "A window filled by three changes that were each reviewed separately",
        "Every component grew inside its own ticket. The ceiling belongs to "
        "their sum, and no ticket was about the sum.",
        [
            ("Retrieval returns more", "five chunks became eight"),
            ("Tool list grows", "resident on every turn"),
            ("History accumulates", "tool results included"),
            ("Nobody counts the total", "no pre flight anywhere"),
            ("400 prompt is too long", "or a 200 that stopped early"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmpre-f",
        "Sorting one counted payload by which side of the window it lands on",
        "Two overflow states, not one. Over on input alone is a 400 on every "
        "model; over on the reservation is a 200 that a client reads as done.",
        ("count_tokens, free", "against max_input_tokens"),
        [
            ("Input alone over", "400 on every model", "bad"),
            ("Input plus max_tokens over", "200, stopped early", "bad"),
            ("Above 90% of the window", "one long turn ends it", "bad"),
            ("Reservation fits", "with turns to spare", "good"),
        ],
    ),
}

V["llm/request-too-large-413"] = {
    "flow_intro": (
        "The only ceiling in the set that is not measured in tokens. Base64 "
        "adds a third on the way in, so a 24 MB file lands on the 32 MB line "
        "exactly, and the rejection happens in a proxy in front of the API "
        "rather than inside it. The fix measures the serialized string and "
        "then confirms it for nothing, by reading a status code and ignoring "
        "the token number that comes with it."
    ),
    "diagram_problem": D.chain(
        "llmbyte-p",
        "A rejection that happens before the API and appears in no report",
        "Nothing was invoked, so nothing was counted. The error body was "
        "written by a proxy and does not match the usual envelope.",
        [
            ("24 MB PDF attached", "well under the window"),
            ("Base64 adds a third", "32 MB on the wire"),
            ("Cloudflare refuses it", "413 request_too_large"),
            ("Usage report is empty", "no model was invoked"),
            ("Team shortens the prompt", "wrong dimension entirely"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmbyte-f",
        "Sorting one serialized body across three unrelated byte level limits",
        "Three ceilings, three units, one rejection. A payload can pass two of "
        "them and be refused by the third.",
        ("Serialized bytes", "plus blobs and blocks"),
        [
            ("Over 32 MB on the wire", "the Files API, not a split", "bad"),
            ("Over the image or page cap", "size was never the issue", "bad"),
            ("Base64 carries line breaks", "a validation failure", "bad"),
            ("Under every ceiling", "and count_tokens agrees", "good"),
        ],
    ),
}

V["llm/max-tokens-above-model-cap"] = {
    "flow_intro": (
        "No payload is sent anywhere in this one. It is a single integer from "
        "your configuration against a single field on the model resource, and "
        "the field wins: the published table lags a release and a constant in "
        "your source lags the table. The endpoint is the second input, because "
        "the batch ceiling is higher and gated on a beta header."
    ),
    "diagram_problem": D.chain(
        "llmcap-p",
        "One shared integer inherited by a call path on a smaller model",
        "The number is invisible at every call site that inherits it, which is "
        "the point of shared config until the ceiling underneath moves.",
        [
            ("max_tokens set once", "for the model writing reports"),
            ("Helper is shared", "four services inherit it"),
            ("Classifier moves tiers", "cheaper model, same helper"),
            ("Cap halves underneath", "nothing in the diff says so"),
            ("Every call 400s", "rejected during validation"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmcap-f",
        "Sorting a configured value by the ceiling that actually applies to it",
        "The ceiling belongs to the model and the endpoint together, so the "
        "docs table cannot express it and the model object can.",
        ("Configured max_tokens", "against the model object"),
        [
            ("Above the model cap", "a 400 on every call", "bad"),
            ("Batch header not sent", "no 300K ceiling after all", "bad"),
            ("One value, two tiers", "smallest cap governs", "bad"),
            ("Under its own cap", "with room to move", "good"),
        ],
    ),
}

V["llm/non-streaming-request-over-ten-minutes"] = {
    "flow_intro": (
        "Nothing here is too large. The prompt is small, the window is empty "
        "and the request still dies, because the ceiling is a clock and "
        "128,000 output tokens take about forty minutes to write. The fix "
        "estimates seconds, normalises the client timeout out of whatever unit "
        "its SDK uses, and then changes the transport rather than the size."
    ),
    "diagram_problem": D.chain(
        "llmwall-p",
        "A ceiling measured in seconds, debugged as though it were a size",
        "Every intuition built on prompt length points the wrong way. The "
        "connection went idle while the model was still writing.",
        [
            ("Small prompt, long answer", "max_tokens left high"),
            ("Generation runs on", "roughly 55 tokens a second"),
            ("Connection sits idle", "a proxy closes it"),
            ("504, or nothing at all", "triaged as a network fault"),
            ("Prompt gets shortened", "the clock does not move"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmwall-f",
        "Sorting an estimated duration by transport rather than by size",
        "Streaming does not generate faster. It keeps the connection busy, "
        "which is the only thing the ten minute ceiling is about.",
        ("Estimated seconds", "prefill plus generation"),
        [
            ("Past 10 min, not streaming", "stream it or batch it", "bad"),
            ("Timeout in the wrong unit", "600 ms, not 10 minutes", "bad"),
            ("Past 10 min, streaming", "the ceiling does not apply", "plain"),
            ("Finishes with margin", "at your measured rate", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
