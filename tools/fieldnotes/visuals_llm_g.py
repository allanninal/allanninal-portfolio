#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch G.

Four dimensions of a bill that is not priced per token, so none of these can be
a picture of an invoice. Each problem chain has to draw the specific way its
number stays invisible: a counter nested beside the token fields, a cost type
that is absent from the usage report entirely, a multiplier inherited from a
setting nobody remembers, and a band everyone reads as a price tier when it is a
size. The fixes are branches, because each script sorts what it finds into named
states rather than answering yes or no. Teal, matching the rest of the section.

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

V["llm/web-search-spend-unnoticed"] = {
    "flow_intro": (
        "The count is already in the usage report. It is one level down, in a "
        "server_tool_use object sitting beside the token fields rather than "
        "among them, which is exactly deep enough that a dashboard walking the "
        "result flat never sees it. The fix reaches in, multiplies by ten per "
        "thousand, and then refuses to pretend the estimate and the invoice are "
        "the same number when they disagree."
    ),
    "diagram_problem": D.chain(
        "llmwebs-p",
        "A per search fee accumulating one level below every graph in the building",
        "Nothing errors and no token count looks odd, because the fee is not "
        "denominated in tokens and the counter is not where anyone is reading.",
        [
            ("Agent may search", "no max_uses set"),
            ("Eleven per ticket", "satisfied, not capped"),
            ("Counter nests one level", "beside the token fields"),
            ("Dashboard reads flat", "sees zero searches"),
            ("$10 per 1,000 accrues", "invisible until billed"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmwebs-f",
        "Sorting keys by search volume, then holding the estimate against the invoice",
        "Counted and billed are allowed to differ: an errored search is a use "
        "and is free. Averaging the two into one number hides which is which.",
        ("server_tool_use per key", "times ten per thousand"),
        [
            ("High volume key", "cap max_uses on this one", "bad"),
            ("Counted, nothing billed", "errors, or a lagging report", "plain"),
            ("Billed, nothing counted", "the windows do not line up", "plain"),
            ("Estimate matches invoice", "now you know the number", "good"),
        ],
    ),
}

V["llm/code-execution-hours-exceed-free-allowance"] = {
    "flow_intro": (
        "This line is not in the usage report at all: no field, no grouping, no "
        "counter. It exists as money and nowhere else. And because the free "
        "1,550 container hours are consumed before anything is charged, there "
        "is no threshold to argue about on the fix side, only a question of how "
        "far past the allowance a workspace already is."
    ),
    "diagram_problem": D.chain(
        "llmcodex-p",
        "Container time billed for a tool the model was never asked to use",
        "The free hours run out quietly, and the route that spends them fastest "
        "is the one that attaches a file it needs about once in forty calls.",
        [
            ("File attached just in case", "one route, always"),
            ("Container preloads it", "tool never called"),
            ("Five minute minimum", "per execution, always"),
            ("1,550 free hours gone", "no notification"),
            ("Usage report is silent", "money only"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmcodex-f",
        "Sorting workspaces by how far past the free container hours they already are",
        "Zero is the only reassuring answer, because the platform spends the "
        "allowance before it writes a row. Every other number is past it.",
        ("cost_type code_execution", "per workspace"),
        [
            ("Billed hours beat the grant", "free tier stopped mattering", "bad"),
            ("Charging every execution", "find the attached files", "bad"),
            ("Just over the line", "cheapest moment to fix it", "bad"),
            ("No rows at all", "inside the grant, or bundled free", "good"),
        ],
    ),
}

V["llm/us-inference-geo-premium-unnoticed"] = {
    "flow_intro": (
        "Every other cost note in this section is about how much of something "
        "you bought. This one is about what each unit cost, which is why no "
        "amount of volume tuning or caching touches it. The fix asks who chose "
        "it, because a workspace default and a per request parameter are the "
        "same premium with two different owners."
    ),
    "diagram_problem": D.chain(
        "llmgeo-p",
        "One contract's residency requirement multiplying every customer's rate card",
        "A ten percent gap against a spreadsheet built from the public rates "
        "reads as rounding, a mis-estimate, or somebody's arithmetic. Never as this.",
        [
            ("One customer needs US", "one contract, one clause"),
            ("Workspace default set", "four seconds, unrecorded"),
            ("All traffic inherits it", "callers never asked"),
            ("1.1x on every category", "cache reads included"),
            ("Invoice runs ten percent high", "filed as rounding"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmgeo-f",
        "Sorting workspaces by who decided the traffic would be served in the US",
        "The premium is identical in the first two rows and the person who can "
        "fix it is not. Models that predate the parameter have no lever at all.",
        ("inference_geo by workspace", "against data_residency"),
        [
            ("Default says us", "config decision, scope it", "bad"),
            ("Callers set it themselves", "the fix is in code", "bad"),
            ("No readable default", "read the workspace first", "plain"),
            ("Model predates the field", "no premium, no lever", "good"),
        ],
    ),
}

V["llm/long-context-requests-unwatched"] = {
    "flow_intro": (
        "The band is a size alarm and everybody reads it as a price alarm, so "
        "the fix has to say the quiet part first: standard rates, extraordinary "
        "volume. Cache reads inside the band grade how bad it is without "
        "changing what it is, and traffic the report never banded is kept out "
        "of the share rather than counted as short."
    ),
    "diagram_problem": D.chain(
        "llmctxb-p",
        "A prefix that grows every turn because nothing was ever written to shrink it",
        "Four turns in testing, forty in production. The prefix is a monotonic "
        "function of session length and no code path subtracts from it.",
        [
            ("Agent keeps everything", "by design, at first"),
            ("Each turn appends", "results, documents, answers"),
            ("Sessions run long", "forty, not four"),
            ("400k resent per turn", "standard rate, huge number"),
            ("Answers get worse too", "no line item for that"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmctxb-f",
        "Sorting workloads by the share of banded input sitting above 200k",
        "Counting unbanded traffic as short would deflate the share and make "
        "the finding vanish, which is the one outcome this check exists to stop.",
        ("context_window share", "of uncached input"),
        [
            ("Big band, no cache reads", "compact first, then cache", "bad"),
            ("Big band, well cached", "a tenth the price, same length", "plain"),
            ("No context_window at all", "cannot be placed either side", "plain"),
            ("Prefix is small", "the money is elsewhere", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
