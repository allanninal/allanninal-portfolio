#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch B.

All four notes are about money, and all four problem chains share the same
spine: a request that succeeds, or a limit that was never set, followed by an
absence rather than an error. Neither provider exposes a per-request log, so
every fix diagram branches on a shape read out of aggregate buckets rather than
on a failed call anybody could have alerted on. Drawn in the section teal.

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

V["llm/quota-exhausted-not-rate-limited"] = {
    "flow_intro": (
        "The classifier branches on the error code before it looks at the status, "
        "because the status is the same for a throttle you should wait out and a "
        "balance that will still be empty tomorrow."
    ),
    "diagram_problem": D.chain(
        "lqta-p",
        "A billing wall raised as a rate limit and retried until somebody notices",
        "Nothing here throws. The wrapper is doing exactly what it was written to "
        "do, against a condition that no amount of waiting changes.",
        [
            ("Balance runs out", "or a spend cap is hit"),
            ("API answers 429", "code insufficient_quota"),
            ("SDK raises", "RateLimitError, as always"),
            ("Wrapper backs off", "sleeps, doubles, asks again"),
            ("Still 429 at hour 8", "traffic stopped, no page"),
        ],
        fail_at=1,
        loop=(4, 3, "forever"),
    ),
    "diagram_fix": D.branch(
        "lqta-f",
        "Sorting a 429 by the code inside it rather than by the status on it",
        "Four billing codes, four different consoles. Printing one message for "
        "all of them sends the on call engineer to the wrong place.",
        ("429 received", "read error.code first"),
        [
            ("rate_limit_exceeded", "a real throttle, back off", "good"),
            ("insufficient_quota", "no balance, add credits", "bad"),
            ("spend_limit_exceeded", "a cap you set, raise it", "bad"),
            ("A code nobody knows", "fail loudly, do not loop", "plain"),
        ],
    ),
}

V["llm/no-organization-spend-limit"] = {
    "flow_intro": (
        "The script reads the limit, the alerts and month to date spend as three "
        "separate things, because an org can hold any two of them and still have "
        "nothing that would stop a runaway."
    ),
    "diagram_problem": D.chain(
        "lspl-p",
        "A runaway agent spending for days because the ceiling was never turned on",
        "Post paid billing with auto recharge has no natural ceiling. The "
        "platform serves requests; that is its job.",
        [
            ("Agent loop breaks", "no termination condition"),
            ("Requests keep landing", "every one is valid"),
            ("No limit configured", "the console shows a chart"),
            ("No alert configured", "separate endpoint, opt in"),
            ("Invoice arrives", "the first real signal"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lspl-f",
        "Sorting a scope by whether anything would actually refuse a request",
        "A limit set to fifty times the run rate and a limit typed in dollars "
        "instead of cents are opposite mistakes with the same repair endpoint.",
        ("spend_limit and alerts", "judged against month to date"),
        [
            ("Enforcing, with alerts", "a brake and a warning", "good"),
            ("No limit, or inactive", "nothing refuses anything", "bad"),
            ("Cents typed as dollars", "100x low, fires today", "bad"),
            ("Limit but no alerts", "a brake, no warning light", "plain"),
        ],
    ),
}

V["llm/reasoning-tokens-billed-invisibly"] = {
    "flow_intro": (
        "The script compares output tokens per request against input tokens per "
        "request across a boundary you choose, because a total tells you the bill "
        "moved and a ratio tells you which of three ordinary things moved it."
    ),
    "diagram_problem": D.chain(
        "lrsn-p",
        "A model constant changed and the cost per request quadrupled invisibly",
        "The tokens are generated, billed at the output rate, and then not "
        "returned. Measuring the text you received underestimates by all of them.",
        [
            ("Model constant bumped", "one line in a config"),
            ("Reasoning runs", "tokens generated"),
            ("Billed as output", "and never returned"),
            ("Answers look identical", "same visible length"),
            ("Invoice up 4x", "weeks after the deploy"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lrsn-f",
        "Sorting a cost jump by which ratio actually moved",
        "Three of these four are ordinary and only one is worth changing a "
        "setting over, which is why the denominator matters.",
        ("Daily buckets by model", "recent window against prior"),
        [
            ("Output per request up", "input flat: reasoning", "bad"),
            ("Both ratios up", "the prompts grew", "plain"),
            ("Requests up, ratios flat", "just more traffic", "good"),
            ("No request count", "a weaker claim, said so", "plain"),
        ],
    ),
}

V["llm/output-tokens-dominate-cost"] = {
    "flow_intro": (
        "The script sums money by token type rather than counting tokens, because "
        "output is priced at five times input and a token count is the wrong "
        "denominator for deciding which lever to pull."
    ),
    "diagram_problem": D.chain(
        "lout-p",
        "A caching project that worked, against a bill made of output tokens",
        "Every step is correct work. It lands on the smaller half of the invoice, "
        "and there is no caching discount on the larger half at all.",
        [
            ("Cost review opens", "everyone looks at the prompt"),
            ("Caching shipped", "input line falls"),
            ("Total barely moves", "nobody can say why"),
            ("Output is 75% of it", "priced at 5x input"),
            ("No discount exists", "generate less or nothing"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "lout-f",
        "Sorting a Claude bill by which side of the request the money is on",
        "Each state names a different repair. Shipping the caching one against "
        "an output dominated bill is a month of work and a flat invoice.",
        ("cost_report by token_type", "share of amount, not of tokens"),
        [
            ("Output above 70%", "generate less, no discount", "bad"),
            ("Input side above 60%", "cache the stable prefix", "good"),
            ("Writes above reads", "paying the premium twice", "bad"),
            ("Roughly even", "both help, neither much", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
