#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch L.

Four notes about the things you attach to every request and pay for whether or
not they earn it. Tools and prefixes are not sent once and remembered; they are
re-sent, re-read and re-billed on every single call, and none of the four
failures here raises anything.

The first two are the same object read from opposite ends. One asks which
declared tools ever get chosen, and its chain ends in a capability that is
absent while its cost is continuous. The other asks what the same block weighs
in tokens, and its chain ends in a bill that is mostly schema before the user
has typed a word. Neither diagram has an error in it, because there isn't one.

The third fails inside a single turn: a guarantee that holds for one tool call
and quietly stops holding for two, which is why its problem chain ends green in
test and red in production rather than ending in an error at all.

The fourth is the one that had to be drawn carefully, because two published
notes already own neighbouring ground. Its picture is not "the cache is cold"
and not "the writes outnumber the reads"; it is a run of adjacent minutes that
each write and never read, which is the only shape a prefix changing on every
call can make. The fix branch hands two of its four states to those other
notes by name, which is the honest thing to draw when three findings share one
number.

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

V["llm/tool-defined-but-never-called"] = {
    "flow_intro": (
        "Nothing here errors and nothing here is slow. A tool definition is "
        "part of the prompt, so it is re-sent and re-billed on every turn, and "
        "the only evidence that the model never picks it is a name that is "
        "present in the request and absent from the output. The set difference "
        "is the whole finding, and it needs a sample rather than a single call."
    ),
    "diagram_problem": D.chain(
        "llmtdead-p",
        "A tool that is paid for on every request and never once selected",
        "There is no failing call in this chain. The capability is simply "
        "absent, and its cost is the one thing that never stops.",
        [
            ("Tool added in a sprint", "with a vague description"),
            ("Shipped on every request", "billed as input each turn"),
            ("Model never selects it", "tool_choice is auto"),
            ("Handler logs stay empty", "nobody owns that dashboard"),
            ("Capability is absent", "and the cost is continuous"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmtdead-f",
        "Sorting declared tool names by whether they were ever chosen",
        "Never called and never offered are different findings. One is dead "
        "weight; the other is a tool_choice that never let the model near it.",
        ("Declared names", "minus the names ever called"),
        [
            ("Never called, freely offered", "dead weight: prune or rewrite", "bad"),
            ("Never offered at all", "tool_choice ruled it out", "plain"),
            ("Called once in a hundred", "keep it, narrow the turn", "plain"),
            ("Called across the sample", "earning its place", "good"),
        ],
    ),
}

V["llm/tool-schemas-dominate-input-tokens"] = {
    "flow_intro": (
        "The only ceiling either API will state before you spend anything is a "
        "token count, and it is free. Count the same body twice, once with the "
        "tools block and once without, and the difference is what the schemas "
        "cost on every call. Ablate one tool at a time and the deltas sum to "
        "less than the whole, because a fixed charge arrives with any tools."
    ),
    "diagram_problem": D.chain(
        "llmtsch-p",
        "A tool registry that outweighs the conversation on every request",
        "No step raises. The schemas are correct, the calls succeed, and the "
        "prompt is mostly machinery by the time the user is reached.",
        [
            ("Forty tools on one client", "from one shared registry"),
            ("Every schema resent", "tools sit first in the prompt"),
            ("Schemas outweigh the message", "before the user types a word"),
            ("No error anywhere", "the bill is the only sign"),
            ("A tool edit voids the cache", "and everything after it"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmtsch-f",
        "Sorting a measured tools block by what actually carries the weight",
        "Two counts and an ablation. The split that matters is between your "
        "schemas and the fixed charge that arrives with any tools at all.",
        ("Count with tools", "then count without"),
        [
            ("Schemas are most of the input", "cache the block, defer the rest", "bad"),
            ("Heavy but not dominant", "one breakpoint pays for itself", "plain"),
            ("Fixed charge, not your schemas", "the automatic tool preamble", "plain"),
            ("Message outweighs the tools", "nothing to repair here", "good"),
        ],
    ),
}

V["llm/parallel-tool-calls-with-strict-schema"] = {
    "flow_intro": (
        "This one is a documented interaction rather than a bug, which is "
        "exactly why it survives review: every part of the configuration is "
        "correct on its own. The guarantee holds for one call in a turn and "
        "stops holding for two, and the default is the setting that lets the "
        "model choose. A test suite sends one call and never sees it."
    ),
    "diagram_problem": D.chain(
        "llmpar-p",
        "A strict schema guarantee that stops applying the moment a turn fans out",
        "Nothing in this chain is misconfigured in isolation. The failure is "
        "the pair, and it only fires when the model decides to fan out.",
        [
            ("strict true on every tool", "the schema is guaranteed"),
            ("parallel_tool_calls default", "and the default is true"),
            ("Model fans out one turn", "two calls, sometimes three"),
            ("The guarantee is void", "arguments stop conforming"),
            ("Green in test, red live", "tests send one call"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmpar-f",
        "Sorting one turn of output against the request configuration it echoes",
        "The unit is the turn, not the corpus. A single call under the same "
        "configuration is not a finding yet, and it is not safe either.",
        ("One turn of output", "against the request it echoes"),
        [
            ("Several calls, strict declared", "the guarantee is void here", "bad"),
            ("Same tool called twice", "handlers double apply", "bad"),
            ("Strict, parallel on, one call", "loaded and did not fire", "plain"),
            ("Parallel turned off", "the guarantee holds", "good"),
        ],
    ),
}

V["llm/cache-invalidated-by-changing-prefix"] = {
    "flow_intro": (
        "Three notes in this section read the same two numbers and reach three "
        "different conclusions, so this one has to earn its ground on shape "
        "rather than on totals. A cache that was never warmed writes once. A "
        "cache whose traffic is slower than its TTL writes in isolated "
        "minutes. A prefix that changes every call writes in every minute, "
        "back to back, and never reads. Only the last of those is this note."
    ),
    "diagram_problem": D.chain(
        "llmchurn-p",
        "A prefix that changes on every call, so every call writes and none reads",
        "One byte anywhere before the breakpoint does all of this. The feature "
        "is on, the writes are billed at a premium, and no read ever lands.",
        [
            ("Timestamp in the prompt", "or a reordered tool list"),
            ("Prefix differs every call", "one byte is enough"),
            ("Lookup misses, entry written", "at 1.25x base input"),
            ("Nothing is ever read", "the next call misses too"),
            ("Reads sit at zero", "as if caching were off"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmchurn-f",
        "Sorting minutes of cache activity by how the writes are spaced",
        "Adjacency is the discriminator. A run longer than the TTL proves the "
        "entry was alive and unmatched, which no gap story can explain.",
        ("Adjacent writing minutes", "with reads at zero"),
        [
            ("Runs longer than the TTL", "the prefix moves every call", "bad"),
            ("Isolated minutes, long gaps", "traffic slower than the TTL", "plain"),
            ("Reads present anywhere", "read the write to read note", "plain"),
            ("No writes and no reads", "caching was never switched on", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
