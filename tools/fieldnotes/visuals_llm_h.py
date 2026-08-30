#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch H.

Four notes about which limiter is binding, and the risk in drawing them is that
they all become one picture of a bucket emptying. So each problem chain has to
carry the thing that is actually different: a signal that arrives on every
successful response and is thrown away, a 429 caught as an exception class
before anything reads the response it came on, a limiter spent on text the
model has already been shown, and a ceiling that counts what comes out rather
than how many connections it came out of.

The fixes are branches, because each script sorts what it finds into named
states rather than answering yes or no. The two token-limiter branches are
deliberately different shapes: the input one sorts by why the ceiling is full,
and the output one sorts by which limiter is full at all, including the state
that hands the reader to the other note.

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

V["llm/rate-limit-headers-near-exhaustion"] = {
    "flow_intro": (
        "There is no endpoint to ask. The only forward looking number OpenAI "
        "emits rides on responses that succeeded, which is to say on the ones "
        "nobody opens. The fix makes one cheap real call, reads both triples, "
        "and then refuses to average two buckets that empty independently."
    ),
    "diagram_problem": D.chain(
        "llmhdr-p",
        "A quota signal that arrives on every success and is read on none",
        "Nothing errors anywhere in this chain. The headroom was on the "
        "response the whole time, one attribute deeper than the parsed body.",
        [
            ("Every 200 carries it", "x-ratelimit-remaining"),
            ("SDK returns the body", "headers left behind"),
            ("Traffic grows quietly", "no dashboard for this"),
            ("Latency creeps", "requests queue, nothing logs"),
            ("First spike 429s", "at 4% for a fortnight"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmhdr-f",
        "Sorting one probe by which bucket is scarcest and who owns the ceiling",
        "Tokens and requests empty independently, so the mean of the two is a "
        "number about nothing. Missing headers are a finding, not a pass.",
        ("One GET /v1/models", "read both triples"),
        [
            ("Scarcest bucket under 20%", "the one that 429s first", "bad"),
            ("Project ceiling is lower", "org headroom is not yours", "bad"),
            ("No headers arrived at all", "a proxy is stripping them", "bad"),
            ("Both triples comfortable", "and the reset window is short", "good"),
        ],
    ),
}

V["llm/rate-limit-429-limiter-unidentified"] = {
    "flow_intro": (
        "Four header triples arrive and one of them already contains the "
        "answer: the aggregate reports whichever token ceiling is most "
        "restrictive, so matching it back to the named ones names the bucket. "
        "The script then reads the configured limits per model group, because "
        "the probe's own headers describe the endpoint it probed."
    ),
    "diagram_problem": D.chain(
        "llmwhich-p",
        "A 429 caught as an exception class before anything reads the response",
        "The message named the limit, the headers counted three buckets, and "
        "retry-after said how long. All of it reached the process and none of "
        "it reached the log.",
        [
            ("429 comes back", "message names the limit"),
            ("Handler catches a class", "response is discarded"),
            ("Log records 429", "and nothing else"),
            ("Review picks a lever", "concurrency, always"),
            ("Output bucket was full", "so nothing moved"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmwhich-f",
        "Sorting four header triples into a named limiter",
        "The tightest ceiling and the emptiest bucket are two questions. When "
        "they disagree, both belong in the report.",
        ("Aggregate ceiling", "against the named ones"),
        [
            ("Aggregate mirrors one", "that bucket is the tightest", "good"),
            ("Emptiest bucket differs", "record both, not one", "bad"),
            ("Aggregate matches neither", "a third limit is in effect", "bad"),
            ("No triples arrived", "a 429 here is unclassifiable", "bad"),
        ],
    ),
}

V["llm/itpm-exhausted-uncached-input"] = {
    "flow_intro": (
        "Only uncached input is charged against the input limiter: uncached "
        "tokens plus both cache creation fields, with cache reads excluded on "
        "every model but one. That exclusion is why this is a throughput note "
        "rather than a discount note, and why the multiplier is one over one "
        "minus the read share."
    ),
    "diagram_problem": D.chain(
        "llmitpm-p",
        "An input limiter spent on text the model has already been shown",
        "Concurrency is the knob everyone has, and it is charged in "
        "connections while the limiter is charged in tokens.",
        [
            ("Stable prefix, 40k tokens", "tools, system, few shot"),
            ("Re-sent on every call", "nothing is cached"),
            ("Input bucket empties", "requests bucket is fine"),
            ("Team lowers concurrency", "same tokens, fewer workers"),
            ("Still 429 every afternoon", "the ceiling never moved"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmitpm-f",
        "Sorting a full input limiter by the reason it is full",
        "Three ways an ITPM ceiling fills and they do not share a repair. On "
        "Claude Haiku 3.5 cache reads are charged, so caching buys no headroom.",
        ("Peak charged minute", "against the ITPM ceiling"),
        [
            ("Full, read share near zero", "caching buys throughput", "bad"),
            ("Full, prefix already cached", "only a limit increase left", "bad"),
            ("Full, model charges reads", "caching cuts cost, not the ceiling", "bad"),
            ("Peak well under the ceiling", "the input limiter is not it", "good"),
        ],
    ),
}

V["llm/otpm-exhausted"] = {
    "flow_intro": (
        "The same minute buckets, a different ceiling, and a conclusion that "
        "runs the other way. Nothing about the prompt moves this number, "
        "because there is no cached output. Peak output divided by the "
        "configured RPM gives the answer length below which the request rate "
        "would have mattered, which is how a report with no request count "
        "still rules the request rate out."
    ),
    "diagram_problem": D.chain(
        "llmotpm-p",
        "A ceiling that counts what comes out, planned for in connections",
        "No prompt changed and no traffic changed. Thinking tokens are output "
        "tokens, so an effort setting is a capacity change with no diff.",
        [
            ("Effort setting rises", "answers get longer"),
            ("Request rate unchanged", "prompts unchanged"),
            ("Output bucket saturates", "input still comfortable"),
            ("Plan says add workers", "capacity is in RPM"),
            ("Same tokens, same bucket", "429s continue"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmotpm-f",
        "Sorting the peak minute by which of the two token limiters is full",
        "The input bound state exists so this script hands that reader to the "
        "other note instead of prescribing batching for a caching problem.",
        ("Peak output minute", "and the input beside it"),
        [
            ("Output full, input free", "workers add nothing", "bad"),
            ("Both limiters full", "volume, not shape", "bad"),
            ("Input full, output free", "read the ITPM note", "plain"),
            ("Neither near its ceiling", "the limiter is elsewhere", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
