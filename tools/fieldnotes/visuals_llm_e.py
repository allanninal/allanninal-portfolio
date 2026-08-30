#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch E.

Four notes that all end at the invoice and four different questions asked of
it. The problem chains have to make the difference visible before the prose
does: a tier that was configured once and quietly stopped being delivered, a
number your own dashboard never recorded, a change nobody was watching for, and
a total read as a single figure when it has a shape inside it. Every fix is a
branch, because each script sorts what it finds rather than guessing. Drawn in
amber.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
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

V["llm/fast-mode-silently-downgraded"] = {
    "flow_intro": (
        "Neither half of this is readable on its own. The project object says "
        "which tier was asked for and the cost report says which one was "
        "served, and the finding is the disagreement between them. It runs in "
        "both directions, which is why the fix is a sort rather than a test: a "
        "premium you are not getting and a premium you never asked for are "
        "opposite problems with opposite repairs."
    ),
    "diagram_problem": D.chain(
        "lfast-p",
        "A premium tier requested on every call and served on some of them",
        "Nothing in this chain returns an error. The request field and the "
        "response field have the same name and say different things.",
        [
            ("Request sends fast", "service_tier in the body"),
            ("Ramp limit trips", "no error, no header"),
            ("Served as default", "the response field, not yours"),
            ("Logs record the request", "what you asked for"),
            ("Dashboard shows fast", "for traffic that was not"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lfast-f",
        "Sorting projects by whether the configured tier and the invoice agree",
        "A delivered premium is an answer, not a gap in the detection. Only a "
        "disagreement between the two sides is a finding.",
        ("Project tier", "against premium line items"),
        [
            ("Fast set, standard billed", "downgraded, the speedup is not there", "bad"),
            ("Standard set, fast billed", "a code path paying 2x unasked", "bad"),
            ("Fast set and fast billed", "2x, and somebody should want it", "plain"),
            ("Standard on both sides", "nothing to reconcile", "good"),
        ],
    ),
}

V["llm/streaming-usage-lost"] = {
    "flow_intro": (
        "The only script in this section that takes your numbers as input, "
        "because half the comparison does not exist on the API side. What "
        "OpenAI reports is the truth about what was billed; what your pipeline "
        "recorded is the number every downstream decision was made from, and "
        "the gap between them is the finding."
    ),
    "diagram_problem": D.chain(
        "lstrm-p",
        "Tokens billed correctly and recorded nowhere because the response was streamed",
        "Every token here is billed correctly. The only thing that is wrong is "
        "the internal record of it.",
        [
            ("Streamed request", "no stream_options set"),
            ("Every chunk usage null", "documented behaviour"),
            ("No final usage chunk", "nothing to record"),
            ("Dashboard reads zero", "for the whole stream"),
            ("The invoice does not", "the tokens were billed"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lstrm-f",
        "Sorting projects by how their recorded tokens compare to the organization report",
        "Recording too many is not the same bug as recording too few, and a "
        "project your telemetry has never heard of is neither.",
        ("Org token totals", "against your own record"),
        [
            ("Recorded far below", "streaming, and abandoned streams", "bad"),
            ("Absent from your record", "not undercounted, unrecorded", "bad"),
            ("Recorded above the API", "double counting, another bug", "bad"),
            ("Inside the tolerance", "the two sources agree", "good"),
        ],
    ),
}

V["llm/spend-spike-week-over-week"] = {
    "flow_intro": (
        "One number over eight weeks, and the answer is its shape rather than "
        "its size. Today is dropped before anything is compared, because the "
        "current bucket is always partial and a report that includes it "
        "announces a fall in spend every morning."
    ),
    "diagram_problem": D.chain(
        "lspike-p",
        "A change that lands weeks before the invoice that reveals it",
        "No error, no status code, no failed request. The API worked perfectly "
        "the entire time, which is what makes the delay expensive.",
        [
            ("Cron goes to 5 minutes", "one line, no release note"),
            ("Daily cost doubles", "nothing pushes an alert"),
            ("The report is a pull", "and nobody pulls it"),
            ("Invoice arrives", "two to six weeks later"),
            ("Forty deploys ago", "nobody remembers the week"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lspike-f",
        "Sorting a weekly cost series by the shape of the change in it",
        "Three ways to be higher than you were, and three different people to "
        "call about it.",
        ("Whole weeks of cost", "today excluded, always"),
        [
            ("One week up, then back", "a job that ran once", "bad"),
            ("Up and staying up", "a level something shipped into", "bad"),
            ("Higher every single week", "growth no ratio ever catches", "bad"),
            ("Flat, or too little history", "no shape worth reporting", "good"),
        ],
    ),
}

V["llm/one-model-or-project-dominates-cost"] = {
    "flow_intro": (
        "No clock in this one. It reads a single window and asks how the money "
        "inside it is distributed, on two axes that have two different "
        "repairs: a line item is a model or a token side and wants a "
        "substitution, a project is an owner and wants a boundary."
    ),
    "diagram_problem": D.chain(
        "ldom-p",
        "A total read as one number while three quarters of it sits in one row",
        "Nothing failed and nothing is missing. The default response is a "
        "total, and a total is the one thing everybody already knew.",
        [
            ("Ungrouped cost call", "one amount per day"),
            ("Total looks expected", "so nobody opens it"),
            ("One row is 78%", "invisible without group_by"),
            ("A sprint on a 3% row", "the one somebody remembered"),
            ("The bill does not move", "and the argument restarts"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ldom-f",
        "Sorting a ranked cost report by how concentrated the spend in it is",
        "A bill with no row above half is an answer worth printing, and a top "
        "row with no name is an attribution problem rather than a cost one.",
        ("Rows ranked by share", "line item, then project"),
        [
            ("One row above half", "name it, price the substitute", "bad"),
            ("Two rows above three quarters", "concentrated, not dominated", "bad"),
            ("The top row has no name", "spend belonging to no project", "plain"),
            ("Spread across many rows", "no single lever to pull", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
