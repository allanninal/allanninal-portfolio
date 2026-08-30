#!/usr/bin/env python3
"""/llm/ field notes, batch I — the writing.

Four ceilings you can know about before you spend anything, and the whole risk
in the batch is that they collapse into one note about a prompt being too big.
They are not the same ceiling and they are not even the same unit.

`prompt-too-long-context-overflow` is measured in tokens against the context
window. The counted input plus the reserved `max_tokens` has to fit inside
`max_input_tokens`, and the reason it needs saying twice is that the two ways
it fails do not look alike: input alone over the window is a 400 on every
model, while input plus the reservation over the window is a **200** on Claude
4.5 and newer that stops with `model_context_window_exceeded`.

`request-too-large-413` is measured in bytes, and it is the only note in the
batch that never looks at a token count. Thirty-two megabytes is enforced by
Cloudflare in front of the API, so the rejection happens before Anthropic sees
the request and never appears in any usage report. Base64 inflates a payload by
about a third on the way in, which is how a 24 MB PDF becomes a 413.

`max-tokens-above-model-cap` never sends a payload at all. It reads one integer
out of your configuration and one integer off the model object, and the second
one is the source of truth: the published table lags, and a value that is legal
on Opus 5 is illegal on Haiku 4.5 the moment a shared config crosses tiers.

`non-streaming-request-over-ten-minutes` is measured in seconds. Nothing about
it is a size problem: the prompt can be small, the window can be empty, and the
request still dies at ten minutes because 128,000 output tokens cannot be
generated inside them on one non-streaming call. The repair is streaming, not
a shorter prompt, and the second finding in it is a client timeout expressed in
the wrong unit.

Read only, with one deliberate exception that is stated in every script that
uses it. `POST /v1/messages/count_tokens` is free, creates no object, generates
no completion and bills nothing; it returns an `input_tokens` number and runs
against its own rate limit. Three of these four scripts send a payload there
because it is the only way to learn what a body costs before paying for an
answer. Everything else in the batch is a GET, there is no write path, and no
script here ever calls `/v1/messages`.
"""

CITE_CL_CONTEXT = ("Context windows — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/context-windows")
CITE_CL_COUNT = ("Token counting — Claude Docs",
                 "https://platform.claude.com/docs/en/build-with-claude/token-counting")
CITE_CL_STOP = ("Handling stop reasons — Claude Docs",
                "https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons")
CITE_CL_ERRORS = ("Errors — Claude API",
                  "https://platform.claude.com/docs/en/api/errors")
CITE_CL_MODELS = ("Models — Claude API reference",
                  "https://platform.claude.com/docs/en/api/models")
CITE_CL_OVERVIEW = ("Models overview — Claude Docs",
                    "https://platform.claude.com/docs/en/models/overview")
CITE_CL_BATCHES = ("Message Batches — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/batch-processing")
CITE_CL_FILES = ("Files API — Claude Docs",
                 "https://platform.claude.com/docs/en/build-with-claude/files")

REL_OVERFLOW = ("/llm/prompt-too-long-context-overflow/",
                "The same payload measured in tokens against the context window")
REL_BYTES = ("/llm/request-too-large-413/",
             "The same payload measured in bytes against the 32 MB ceiling")
REL_CAP = ("/llm/max-tokens-above-model-cap/",
           "A max_tokens value the model object says is illegal")
REL_WALL = ("/llm/non-streaming-request-over-ten-minutes/",
            "A request that dies on the clock rather than on any size limit")
REL_LONGCTX = ("/llm/long-context-requests-unwatched/",
               "How much traffic is already running in the long-context band")
REL_RETIRED = ("/llm/retired-model-id-still-in-code/",
               "Config model strings diffed against the live model list")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")
REL_BATCH_DISCOUNT = ("/llm/batch-discount-left-unused/",
                      "Latency-tolerant work paying full price on the synchronous path")
REL_STREAMING = ("/llm/streaming-usage-lost/",
                 "Usage totals thrown away because the stream was read wrong")

GUIDES = [
{
"slug": "prompt-too-long-context-overflow",
"title": "Prompts overflow the context window and 400 as too long",
"description": "count_tokens is free and returns the exact number a window check needs. Nothing calls it, so overflow arrives as a 400 in production or a 200 nobody reads.",
"h1": "Prompts overflow the context window and 400 as too long",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["prompt is too long anthropic", "claude context window exceeded",
             "model_context_window_exceeded", "anthropic count_tokens max_input_tokens",
             "claude 400 invalid_request_error prompt too long"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key. GET requests plus the free count_tokens pre-flight.",
"lead": "The retrieval step got better last quarter, so it returns eight chunks instead of five. The agent loop got longer, because agents do. The tool list grew by four definitions nobody costed. None of those three changes touched the prompt template, and none of them was reviewed as a capacity change, and one afternoon the request that has worked for a year comes back <code>400</code> with <code>prompt is too long</code>.",
"short_answer": """<p>Count the real payload before you send it. <code>POST /v1/messages/count_tokens</code> takes the same structured body as message creation &mdash; <code>system</code>, every message, <code>tools</code>, images, PDFs, thinking blocks &mdash; and returns <code>{"input_tokens": N}</code>. It is free, it generates nothing and it bills nothing. Compare <code>N</code> against <code>GET /v1/models/{id}.max_input_tokens</code>.</p>
<p>Compare the <em>reservation</em>, not just the input. <code>max_tokens</code> occupies the window too, so the number that has to fit is <code>input_tokens + max_tokens</code>. Input alone over the window is a 400 on every model. Input plus the reservation over the window is something else entirely.</p>
<p>On Claude 4.5 and newer that second case returns <strong>HTTP 200</strong> with <code>stop_reason: "model_context_window_exceeded"</code>. It is a truncated answer wearing a success code, and a client that only checks for <code>end_turn</code> will file it as complete.</p>""",
"problem": """<p>Everything counts toward the window and almost nothing about that is visible from the call site. The system prompt counts. Every message counts, including tool results, which are the ones that grow without anybody writing them. Images and documents count. The <code>tools</code> definitions count, on every single turn, whether or not the model calls any of them. And the output the model has not generated yet counts, because <code>max_tokens</code> is a reservation against the same window.</p>
<p>So the overflow is nobody's change. Retrieval widened, the conversation got longer, a colleague added a tool, and the sum crossed a line that no one component owns. The failure lands on whichever request happened to be the longest that day, which makes it look intermittent, and the first instinct is to retry it &mdash; which fails identically, because the prompt is deterministic and so is the ceiling.</p>
<p>The version of this that costs the most is the one that does not error. On recent models a request whose input fits but whose input plus <code>max_tokens</code> does not is accepted, run, billed and returned with a 200. The answer stops early. Downstream, JSON fails to parse, or worse, parses into something plausible and short.</p>""",
"why": """<p><strong>Caching changes the price of those tokens, not their presence.</strong> <code>input_tokens</code>, <code>cache_read_input_tokens</code> and <code>cache_creation_input_tokens</code> all occupy the window. A team that adds a cache breakpoint and watches the bill fall can be forgiven for assuming the window pressure fell with it. It did not move at all. Caching is a discount and a throughput lever; it is not a compression scheme.</p>
<p><strong>The reservation is the part people leave out.</strong> Checking <code>input_tokens &lt; max_input_tokens</code> passes on a request that is going to fail, because <code>max_tokens</code> has not been added yet. A 200,000-token window with 190,000 tokens of input and a routine <code>max_tokens: 16000</code> is over by six thousand, and the check that was written to catch this says it is fine.</p>
<p><strong>A 200 is the harder failure, not the softer one.</strong> <code>stop_reason: "model_context_window_exceeded"</code> was introduced so that long agent loops degrade rather than crash, which is the right design and a trap for any client that branches on the status code. Nothing raises, nothing retries, the usage report shows a normal request, and the only evidence is a field nobody reads. Earlier models turn the same combination into a validation error unless you send the <code>model-context-window-exceeded-2025-08-26</code> beta header, so the <em>same</em> payload changes failure mode when you change model id.</p>
<p><strong>The count is an estimate, and it is the right estimate to use anyway.</strong> The docs are explicit that <code>count_tokens</code> may differ slightly from the number the Messages API charges, partly because of system-added tokens that are not billed. It is still the tokenizer that will actually be used, which no local library can claim, and the margin it leaves you is a rounding error against the thing this note is about. Do not substitute <code>tiktoken</code>; that is a different tokenizer for a different vendor's models.</p>
<p><strong>This is not the same question as how long the window is.</strong> A <a href="/llm/long-context-requests-unwatched/">separate note</a> watches what share of your traffic is running in the 200k-to-1M band, which is a question about workload shape and cost. This one is a yes-or-no about one concrete payload, answered before it is sent.</p>""",
"steps": [
 {"h": "Get a real payload, not a representative one",
  "body": """<p>Serialize the body your code actually builds, at its worst realistic size: full retrieval, full tool list, a conversation at the length your product allows. Dump it to a JSON file. The whole value of this check is that it operates on the real assembled body rather than on a template with the variables left out, because the variables are the part that overflows.</p>"""},
 {"h": "Strip the sampling parameters before counting",
  "body": """<p><code>count_tokens</code> accepts <code>model</code>, <code>system</code>, <code>messages</code>, <code>tools</code>, <code>tool_choice</code> and <code>thinking</code>. It rejects <code>max_tokens</code>, <code>stream</code>, <code>temperature</code> and the rest of the sampling block, so passing your body through untouched is a 400 that reads like an outage and is not one. Remove them by name and keep <code>max_tokens</code> to one side, because you need it for the arithmetic.</p>"""},
 {"h": "Read the window off the model object",
  "body": """<p><code>GET /v1/models/{model_id}</code> returns <code>max_input_tokens</code> for that id. Read it rather than hardcoding 200,000: the value differs by model and by whether the workspace has the long-context window enabled, and a constant in your source is a constant that will be wrong on the day somebody changes the model string.</p>"""},
 {"h": "Add max_tokens before comparing",
  "body": """<p>The number that has to fit is <code>input_tokens + max_tokens</code>. Report the two failure modes separately, because they have separate symptoms: over on input alone is a 400 everywhere, over on the sum is a 200 with <code>model_context_window_exceeded</code> on 4.5 and newer and a validation error on older ones.</p>"""},
 {"h": "Confirm against a finished batch, then print the repair",
  "body": """<p><code>GET /v1/messages/batches/{id}/results</code> is a complete read-only corpus of finished responses. Count the lines whose <code>stop_reason</code> is <code>model_context_window_exceeded</code> and the errored lines whose message contains <code>prompt is too long</code>, keyed by <code>custom_id</code> and never by position. Then print the repair &mdash; server-side compaction, context editing, or deferring tool definitions &mdash; and stop. Deciding which half of a conversation to drop is a product decision.</p>"""},
],
"verify": """<p>Re-run against the same payload files after the change. The reservation should sit well under the window with room for the turns your product still allows.</p>
<pre><code class="language-bash">python3 anthropic_context_preflight.py --payload agent-turn.json --per-turn 1800
# budget-over-window   agent-turn.json   188400 input + 16000 max_tokens = 204400 of a 200000 token window. ...
#   repair: server side compaction (compact-2026-01-12) for long conversations, ...
# 1 payload(s) and batch result(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET for the model object, one free <code>count_tokens</code> call per payload, and an optional GET over a finished batch's results. The <code>count_tokens</code> call is the single non-GET in the script and it is there because it is the only way to learn a body's token cost without paying for a completion: it creates nothing, generates nothing and bills nothing. Six pure functions carry the judgement &mdash; the filter that decides which keys the counting endpoint will accept, the window reader that refuses to treat a missing ceiling as a generous one, the reservation, the verdict that keeps the 400 and the 200 apart, the turns-of-headroom estimate, and the batch scanner that finds both shapes in a results file.",
"py_file": "anthropic_context_preflight.py",
"py": '''"""Pre-flight a Claude payload against the model's context window.

Read only, with one deliberate exception. Nothing here creates a completion:
the payload goes to /v1/messages/count_tokens, which is free, generates no
output, creates no object and bills nothing. It returns an input_tokens number
and runs against its own rate limit. That is the only way to learn what a body
costs in tokens without paying for an answer, so it is the one non-GET call in
this script. Everything else is a GET, and /v1/messages is never called.

The repair is printed, never applied. Deciding which half of a conversation to
drop is a product decision, not the side effect of an audit.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_context_preflight")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# count_tokens takes the same structured body as message creation minus the
# parameters that only mean something when text is actually generated. Sending
# max_tokens to it is a 400, which is a confusing way for a pre-flight to fail,
# so these are stripped by name rather than hoped over.
SAMPLING_ONLY = ("max_tokens", "stream", "temperature", "top_p", "top_k",
                 "stop_sequences", "metadata", "service_tier")

OVERFLOW_STOP = "model_context_window_exceeded"
TOO_LONG = "prompt is too long"

FINDINGS = ("input-over-window", "budget-over-window", "window-tight")


def count_body(body):
    """The subset of a Messages body the counting endpoint accepts. Pure.

    Everything structural stays: system, messages, tools, tool_choice, thinking.
    All of it occupies the window, so dropping any of it to make the count
    simpler would produce a number about a request you are not sending.
    """
    if not isinstance(body, dict):
        return {}
    return {k: v for k, v in body.items() if k not in SAMPLING_ONLY}


def window_of(model_obj):
    """max_input_tokens off a model object, or None. Pure.

    None is not a large window. The field is returned by the API, but a proxy
    or gateway that reshapes the model object can drop it, and a ceiling that
    went missing has to stay missing rather than defaulting to something
    generous enough to let every payload pass.
    """
    if not isinstance(model_obj, dict):
        return None
    value = model_obj.get("max_input_tokens")
    return value if isinstance(value, int) and value > 0 else None


def budget(counted_input, max_tokens):
    """What one request reserves in the window. Pure.

    Input plus the room set aside for output, because max_tokens occupies the
    window whether or not the model uses it. Checking input alone is the common
    version of this check and it passes requests that are going to fail.
    """
    return int(counted_input or 0) + max(0, int(max_tokens or 0))


def verdict(counted_input, max_tokens, window, tight=0.9):
    """Classify one payload against one model's window. Pure. (state, detail).

    Two overflow states rather than one, because they do not fail alike: over
    on input alone is a 400 on every model, and over on the reservation is a
    200 on Claude 4.5 and newer that stops with model_context_window_exceeded.
    """
    counted_input = int(counted_input or 0)
    reserved = budget(counted_input, max_tokens)

    if window is None:
        return ("window-unknown",
                "%d input token(s) counted, and the model object carried no "
                "max_input_tokens, so there is no ceiling to compare against"
                % counted_input)

    shape = ("%d input + %d max_tokens = %d of a %d token window"
             % (counted_input, max(0, int(max_tokens or 0)), reserved, window))

    if counted_input > window:
        return ("input-over-window",
                "%s. The input alone is over the window, so this 400s with "
                "prompt is too long on every model, before max_tokens is even "
                "considered." % shape)
    if reserved > window:
        return ("budget-over-window",
                "%s. The input fits and the reservation does not. On Claude 4.5 "
                "and newer that returns 200 with stop_reason %s, which a client "
                "checking only for end_turn files as a complete answer."
                % (shape, OVERFLOW_STOP))

    share = reserved / float(window)
    if share >= tight:
        return ("window-tight",
                "%s (%.0f%%). It fits today and one longer turn ends that."
                % (shape, share * 100))
    return ("fits", "%s (%.0f%%)." % (shape, share * 100))


def turns_remaining(counted_input, max_tokens, window, per_turn):
    """How many more turns of `per_turn` tokens fit. Pure. None if unanswerable.

    A conversational product's real question is not whether this payload fits
    but how many exchanges are left before one stops fitting, and that is the
    number that turns an overflow into a scheduled piece of work.
    """
    if not window or not per_turn or per_turn <= 0:
        return None
    room = window - budget(counted_input, max_tokens)
    return max(0, int(room // per_turn))


def batch_overflows(lines):
    """Find window overflows in a batch results stream. Pure.

    Both shapes, because the same fault wears two faces. A succeeded result
    carrying stop_reason model_context_window_exceeded is the 200 nobody
    noticed; an errored result whose message says the prompt is too long is the
    400. Keyed by custom_id and never by position: results arrive in any order.
    """
    out = {}
    for line in lines or []:
        record = line
        if isinstance(record, (str, bytes)):
            text = record.decode("utf-8") if isinstance(record, bytes) else record
            text = text.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except ValueError:
                continue
        if not isinstance(record, dict):
            continue

        custom_id = record.get("custom_id")
        result = record.get("result") or {}
        message = result.get("message") or {}
        if message.get("stop_reason") == OVERFLOW_STOP:
            out[custom_id] = "truncated-with-200"
            continue
        error = result.get("error") or {}
        if TOO_LONG in str(error.get("message") or "").lower():
            out[custom_id] = "rejected-with-400"
    return out


def get(session, path):
    """Every model and batch read in this script. GET only."""
    r = session.get(API + path, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY has to be a "
                         "workspace key that can reach /v1/models" % r.status_code)
    r.raise_for_status()
    return r.json()


def count_tokens(session, body):
    """The one call here that is not a GET, and it is not a write either.

    /v1/messages/count_tokens creates no object, generates no completion and
    is not billed. It carries its own rate limit, so a pre-flight on every
    request does not eat into the message limiter. A 413 back from it means the
    body is over the 32 MB byte ceiling, which is a different problem with a
    different note.
    """
    r = session.post(API + "/messages/count_tokens",
                     json=count_body(body), timeout=60)
    if r.status_code == 413:
        raise SystemExit("413 from the counting endpoint: this body is over the "
                         "32 MB request ceiling, which is a byte problem rather "
                         "than a token one")
    r.raise_for_status()
    return int((r.json() or {}).get("input_tokens") or 0)


def batch_results(session, batch_id):
    """Stream one batch's results file. GET, and read as lines."""
    r = session.get(API + "/messages/batches/" + str(batch_id) + "/results",
                    timeout=120, stream=True)
    r.raise_for_status()
    return list(r.iter_lines(decode_unicode=True))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", action="append", default=[], metavar="FILE",
                    help="a JSON file holding a real Messages request body")
    ap.add_argument("--batch-id", action="append", default=[],
                    help="also scan a finished batch's results for overflows")
    ap.add_argument("--per-turn", type=int, default=0,
                    help="average tokens one conversational turn adds, used to "
                         "report how many turns of headroom are left")
    ap.add_argument("--tight", type=float, default=0.9,
                    help="share of the window above which a payload that still "
                         "fits is reported anyway (default 0.9)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print payloads with plenty of window left")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key")
        return 2
    if not args.payload and not args.batch_id:
        log.error("give at least one --payload FILE or --batch-id ID")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION,
                            "content-type": "application/json"})

    windows = {}
    checked = 0
    bad = 0

    for path in args.payload:
        with open(path, "r", encoding="utf-8") as fh:
            body = json.load(fh)
        model = str(body.get("model") or "")
        if not model:
            bad += 1
            log.warning("%-20s %-30s no model field, so there is no window to "
                        "check it against", "no-model", path)
            continue
        if model not in windows:
            windows[model] = window_of(get(session, "/models/" + model))

        counted = count_tokens(session, body)
        state, detail = verdict(counted, body.get("max_tokens"),
                                windows[model], args.tight)
        checked += 1
        line = "%-20s %-30s %s" % (state, path, detail)
        if state in FINDINGS or state == "window-unknown":
            if state in FINDINGS:
                bad += 1
            log.warning(line)
        elif args.show_all:
            log.info(line)

        left = turns_remaining(counted, body.get("max_tokens"),
                               windows[model], args.per_turn)
        if left is not None:
            log.info("  room for %d more turn(s) at %d tokens each",
                     left, args.per_turn)
        if state in FINDINGS:
            log.warning("  repair: server side compaction (compact-2026-01-12) "
                        "for long conversations, context editing "
                        "(clear_tool_uses_20250919 / clear_thinking_20251015) "
                        "for agent loops, or the tool search tool so tool "
                        "definitions stop being resident on every turn")
            log.warning("  repair: caching does not help here. Cached tokens "
                        "still occupy the window; they only cost less.")

    for batch_id in args.batch_id:
        found = batch_overflows(batch_results(session, batch_id))
        checked += len(found)
        for custom_id, shape in sorted(found.items(), key=lambda kv: str(kv[0])):
            bad += 1
            log.warning("%-20s %-30s in batch %s", shape, custom_id, batch_id)

    log.info("%d payload(s) and batch result(s) checked, %d finding(s)",
             checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-context-preflight.mjs",
"js": '''/**
 * Pre-flight a Claude payload against the model's context window.
 *
 * Read only, with one deliberate exception. Nothing here creates a completion:
 * the payload goes to /v1/messages/count_tokens, which is free, generates no
 * output, creates no object and bills nothing. Everything else is a GET, and
 * /v1/messages is never called.
 *
 * The repair is printed, never applied.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const SAMPLING_ONLY = new Set(['max_tokens', 'stream', 'temperature', 'top_p',
  'top_k', 'stop_sequences', 'metadata', 'service_tier']);

const OVERFLOW_STOP = 'model_context_window_exceeded';
const TOO_LONG = 'prompt is too long';

const FINDINGS = new Set(['input-over-window', 'budget-over-window', 'window-tight']);

/** The subset of a Messages body the counting endpoint accepts. Pure. */
export function countBody(body) {
  if (!body || typeof body !== 'object') return {};
  return Object.fromEntries(
    Object.entries(body).filter(([k]) => !SAMPLING_ONLY.has(k)));
}

/**
 * max_input_tokens off a model object, or null. Pure.
 * Null is not a large window: a ceiling a gateway dropped has to stay missing
 * rather than defaulting to something every payload fits under.
 */
export function windowOf(modelObj) {
  if (!modelObj || typeof modelObj !== 'object') return null;
  const value = modelObj.max_input_tokens;
  return Number.isInteger(value) && value > 0 ? value : null;
}

/** What one request reserves in the window: input plus room for output. Pure. */
export function budget(countedInput, maxTokens) {
  return Math.trunc(countedInput || 0) + Math.max(0, Math.trunc(maxTokens || 0));
}

/** Classify one payload against one model's window. Pure. [state, detail]. */
export function verdict(countedInput, maxTokens, window, tight = 0.9) {
  const input = Math.trunc(countedInput || 0);
  const reserved = budget(input, maxTokens);

  if (window === null || window === undefined) {
    return ['window-unknown',
      `${input} input token(s) counted, and the model object carried no ` +
      'max_input_tokens, so there is no ceiling to compare against'];
  }

  const room = Math.max(0, Math.trunc(maxTokens || 0));
  const shape = `${input} input + ${room} max_tokens = ${reserved} of a ` +
                `${window} token window`;

  if (input > window) {
    return ['input-over-window',
      `${shape}. The input alone is over the window, so this 400s with prompt ` +
      'is too long on every model, before max_tokens is even considered.'];
  }
  if (reserved > window) {
    return ['budget-over-window',
      `${shape}. The input fits and the reservation does not. On Claude 4.5 ` +
      `and newer that returns 200 with stop_reason ${OVERFLOW_STOP}, which a ` +
      'client checking only for end_turn files as a complete answer.'];
  }

  const share = reserved / window;
  const pct = (share * 100).toFixed(0);
  if (share >= tight) {
    return ['window-tight',
      `${shape} (${pct}%). It fits today and one longer turn ends that.`];
  }
  return ['fits', `${shape} (${pct}%).`];
}

/** How many more turns of `perTurn` tokens fit. Pure. null if unanswerable. */
export function turnsRemaining(countedInput, maxTokens, window, perTurn) {
  if (!window || !perTurn || perTurn <= 0) return null;
  const room = window - budget(countedInput, maxTokens);
  return Math.max(0, Math.floor(room / perTurn));
}

/**
 * Find window overflows in a batch results stream. Pure.
 * Both shapes: a 200 carrying the overflow stop reason, and an errored result
 * whose message says the prompt is too long. Keyed by custom_id, never by
 * position, because results arrive in any order.
 */
export function batchOverflows(lines) {
  const out = {};
  for (const line of lines ?? []) {
    let record = line;
    if (typeof record === 'string') {
      const text = record.trim();
      if (!text) continue;
      try { record = JSON.parse(text); } catch { continue; }
    }
    if (!record || typeof record !== 'object') continue;

    const customId = record.custom_id;
    const result = record.result ?? {};
    const message = result.message ?? {};
    if (message.stop_reason === OVERFLOW_STOP) {
      out[customId] = 'truncated-with-200';
      continue;
    }
    const error = result.error ?? {};
    if (String(error.message ?? '').toLowerCase().includes(TOO_LONG)) {
      out[customId] = 'rejected-with-400';
    }
  }
  return out;
}

function headers(key) {
  return { 'x-api-key': key, 'anthropic-version': VERSION,
           'content-type': 'application/json' };
}

async function get(key, path) {
  const res = await fetch(API + path, { headers: headers(key) });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY has to be ` +
                    'a workspace key that can reach /v1/models');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

/**
 * The one call here that is not a GET, and not a write either: the counting
 * endpoint creates nothing, generates nothing and is not billed.
 */
async function countTokens(key, body) {
  const res = await fetch(`${API}/messages/count_tokens`, {
    method: 'POST',  // count_tokens creates nothing and bills nothing
    headers: headers(key),
    body: JSON.stringify(countBody(body)),
  });
  if (res.status === 413) {
    throw new Error('413 from the counting endpoint: this body is over the ' +
                    '32 MB request ceiling, which is a byte problem rather ' +
                    'than a token one');
  }
  if (!res.ok) throw new Error(`${res.status} from /messages/count_tokens`);
  return Math.trunc((await res.json())?.input_tokens ?? 0);
}

async function batchResults(key, batchId) {
  const res = await fetch(`${API}/messages/batches/${batchId}/results`,
                          { headers: headers(key) });
  if (!res.ok) throw new Error(`${res.status} from batch ${batchId} results`);
  return (await res.text()).split('\\n');
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key');
    process.exitCode = 2;
    return;
  }
  const paths = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  const batchIds = (process.env.BATCH_IDS ?? '').split(',')
    .map((s) => s.trim()).filter(Boolean);
  if (paths.length === 0 && batchIds.length === 0) {
    console.error('pass one or more payload JSON files, or set BATCH_IDS');
    process.exitCode = 2;
    return;
  }
  const perTurn = Math.trunc(Number(process.env.PER_TURN ?? 0));
  const tight = Number(process.env.TIGHT ?? 0.9);
  const showAll = process.env.SHOW_ALL === '1';

  const windows = new Map();
  let checked = 0;
  let bad = 0;

  for (const path of paths) {
    const body = JSON.parse(await readFile(path, 'utf8'));
    const model = String(body.model ?? '');
    if (!model) {
      bad += 1;
      console.warn(`${'no-model'.padEnd(20)} ${path.padEnd(30)} no model field, ` +
                   'so there is no window to check it against');
      continue;
    }
    if (!windows.has(model)) windows.set(model, windowOf(await get(key, `/models/${model}`)));

    const counted = await countTokens(key, body);
    const [state, detail] = verdict(counted, body.max_tokens, windows.get(model), tight);
    checked += 1;
    const line = `${state.padEnd(20)} ${path.padEnd(30)} ${detail}`;
    if (FINDINGS.has(state) || state === 'window-unknown') {
      if (FINDINGS.has(state)) bad += 1;
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }

    const left = turnsRemaining(counted, body.max_tokens, windows.get(model), perTurn);
    if (left !== null) console.log(`  room for ${left} more turn(s) at ${perTurn} tokens each`);
    if (FINDINGS.has(state)) {
      console.warn('  repair: server side compaction (compact-2026-01-12) for long ' +
                   'conversations, context editing (clear_tool_uses_20250919 / ' +
                   'clear_thinking_20251015) for agent loops, or the tool search ' +
                   'tool so tool definitions stop being resident on every turn');
      console.warn('  repair: caching does not help here. Cached tokens still ' +
                   'occupy the window; they only cost less.');
    }
  }

  for (const batchId of batchIds) {
    const found = batchOverflows(await batchResults(key, batchId));
    const ids = Object.keys(found).sort();
    checked += ids.length;
    for (const customId of ids) {
      bad += 1;
      console.warn(`${found[customId].padEnd(20)} ${String(customId).padEnd(30)} ` +
                   `in batch ${batchId}`);
    }
  }

  console.log(`${checked} payload(s) and batch result(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is the pair that a single comparison would collapse: 190,000 tokens of input under a 200,000-token window is fine on its own and is a finding the moment a routine <code>max_tokens: 16000</code> is added, and the state it produces is the one that returns <strong>200</strong> rather than the one that 400s. The rest hold the edges that make the check usable: the counting endpoint rejects <code>max_tokens</code> so the filter has to strip it while keeping every structural key, a model object with no <code>max_input_tokens</code> must not read as an infinite window, and a batch results file has to yield both the truncated 200 and the errored 400 keyed by <code>custom_id</code> rather than by line number.",
"test_py_file": "test_anthropic_context_preflight.py",
"test_py": '''from anthropic_context_preflight import (batch_overflows, budget, count_body,
                                          turns_remaining, verdict, window_of)


def test_input_fits_but_the_reservation_does_not():
    # The whole note in two assertions. 190k of input under a 200k window is
    # fine; the same input with a routine max_tokens is over, and it is over in
    # the way that comes back as a 200 rather than as a 400.
    ok_state, _ = verdict(190_000, 0, 200_000)
    assert ok_state == "window-tight"

    state, detail = verdict(190_000, 16_000, 200_000)
    assert state == "budget-over-window"
    assert "190000 input + 16000 max_tokens = 206000 of a 200000 token window" in detail
    assert "model_context_window_exceeded" in detail
    assert "200" in detail


def test_input_alone_over_the_window_is_the_other_failure():
    state, detail = verdict(260_000, 4_000, 200_000)
    assert state == "input-over-window"
    assert "prompt is too long" in detail
    assert budget(260_000, 4_000) == 264_000


def test_a_comfortable_payload_is_not_a_finding():
    state, detail = verdict(40_000, 8_000, 200_000)
    assert state == "fits"
    assert "(24%)" in detail


def test_the_counting_endpoint_only_gets_the_keys_it_accepts():
    body = {"model": "claude-sonnet-5", "system": "s", "messages": [],
            "tools": [{"name": "t"}], "tool_choice": {"type": "auto"},
            "thinking": {"type": "enabled"}, "max_tokens": 16_000,
            "temperature": 0.2, "stream": True, "service_tier": "auto"}
    trimmed = count_body(body)
    # Sampling parameters out, because count_tokens 400s on them.
    assert "max_tokens" not in trimmed
    assert "temperature" not in trimmed
    assert "stream" not in trimmed
    assert "service_tier" not in trimmed
    # Everything that occupies the window stays, because dropping any of it
    # would count a request you are not sending.
    assert set(trimmed) == {"model", "system", "messages", "tools",
                            "tool_choice", "thinking"}
    assert count_body(None) == {}


def test_a_missing_window_is_not_an_infinite_one():
    assert window_of({"id": "claude-sonnet-5", "max_input_tokens": 200_000}) == 200_000
    assert window_of({"id": "claude-sonnet-5"}) is None
    assert window_of({"max_input_tokens": 0}) is None
    assert window_of({"max_input_tokens": "200000"}) is None
    assert window_of(None) is None
    state, detail = verdict(500_000, 8_000, None)
    assert state == "window-unknown"
    assert "no max_input_tokens" in detail


def test_turns_remaining_is_the_number_a_product_team_wants():
    assert turns_remaining(120_000, 16_000, 200_000, 1_800) == 35
    assert turns_remaining(199_000, 16_000, 200_000, 1_800) == 0
    assert turns_remaining(120_000, 16_000, None, 1_800) is None
    assert turns_remaining(120_000, 16_000, 200_000, 0) is None


def test_batch_results_yield_both_shapes_keyed_by_custom_id():
    lines = [
        '{"custom_id": "doc-9", "result": {"type": "succeeded", "message": '
        '{"stop_reason": "model_context_window_exceeded"}}}',
        '{"custom_id": "doc-3", "result": {"type": "errored", "error": '
        '{"type": "invalid_request_error", "message": "prompt is too long: '
        '412000 tokens > 200000 maximum"}}}',
        '{"custom_id": "doc-1", "result": {"type": "succeeded", "message": '
        '{"stop_reason": "end_turn"}}}',
        "",
        "not json at all",
    ]
    assert batch_overflows(lines) == {"doc-9": "truncated-with-200",
                                      "doc-3": "rejected-with-400"}
    assert batch_overflows([]) == {}
    assert batch_overflows(None) == {}
''',
"test_js_file": "anthropic-context-preflight.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { batchOverflows, budget, countBody, turnsRemaining, verdict, windowOf }
  from './anthropic-context-preflight.mjs';

test('input fits but the reservation does not', () => {
  assert.equal(verdict(190000, 0, 200000)[0], 'window-tight');
  const [state, detail] = verdict(190000, 16000, 200000);
  assert.equal(state, 'budget-over-window');
  assert.match(detail, /190000 input \\+ 16000 max_tokens = 206000 of a 200000 token window/);
  assert.match(detail, /model_context_window_exceeded/);
  assert.match(detail, /200/);
});

test('input alone over the window is the other failure', () => {
  const [state, detail] = verdict(260000, 4000, 200000);
  assert.equal(state, 'input-over-window');
  assert.match(detail, /prompt is too long/);
  assert.equal(budget(260000, 4000), 264000);
});

test('a comfortable payload is not a finding', () => {
  const [state, detail] = verdict(40000, 8000, 200000);
  assert.equal(state, 'fits');
  assert.match(detail, /\\(24%\\)/);
});

test('the counting endpoint only gets the keys it accepts', () => {
  const trimmed = countBody({
    model: 'claude-sonnet-5', system: 's', messages: [], tools: [{ name: 't' }],
    tool_choice: { type: 'auto' }, thinking: { type: 'enabled' },
    max_tokens: 16000, temperature: 0.2, stream: true, service_tier: 'auto',
  });
  assert.deepEqual(Object.keys(trimmed).sort(),
    ['messages', 'model', 'system', 'thinking', 'tool_choice', 'tools']);
  assert.deepEqual(countBody(null), {});
});

test('a missing window is not an infinite one', () => {
  assert.equal(windowOf({ id: 'claude-sonnet-5', max_input_tokens: 200000 }), 200000);
  assert.equal(windowOf({ id: 'claude-sonnet-5' }), null);
  assert.equal(windowOf({ max_input_tokens: 0 }), null);
  assert.equal(windowOf({ max_input_tokens: '200000' }), null);
  assert.equal(windowOf(null), null);
  const [state, detail] = verdict(500000, 8000, null);
  assert.equal(state, 'window-unknown');
  assert.match(detail, /no max_input_tokens/);
});

test('turnsRemaining is the number a product team wants', () => {
  assert.equal(turnsRemaining(120000, 16000, 200000, 1800), 35);
  assert.equal(turnsRemaining(199000, 16000, 200000, 1800), 0);
  assert.equal(turnsRemaining(120000, 16000, null, 1800), null);
  assert.equal(turnsRemaining(120000, 16000, 200000, 0), null);
});

test('batch results yield both shapes keyed by custom_id', () => {
  const lines = [
    '{"custom_id": "doc-9", "result": {"type": "succeeded", "message": {"stop_reason": "model_context_window_exceeded"}}}',
    '{"custom_id": "doc-3", "result": {"type": "errored", "error": {"type": "invalid_request_error", "message": "prompt is too long: 412000 tokens > 200000 maximum"}}}',
    '{"custom_id": "doc-1", "result": {"type": "succeeded", "message": {"stop_reason": "end_turn"}}}',
    '',
    'not json at all',
  ];
  assert.deepEqual(batchOverflows(lines),
    { 'doc-9': 'truncated-with-200', 'doc-3': 'rejected-with-400' });
  assert.deepEqual(batchOverflows([]), {});
  assert.deepEqual(batchOverflows(null), {});
});
''',
"faq": [
 ("Is calling count_tokens really free?",
  "Yes, and it is the reason this note has a script at all. The endpoint creates no message, generates no output and appears on no invoice. It also has its own rate limit group, separate from message creation, so a pre-flight on every request does not eat the limiter your traffic needs. It is the one non-GET call in this batch and it is a read of a number, not a write."),
 ("The count does not exactly match what I was billed. Which is right?",
  "Both, for different questions. The counting endpoint returns an estimate that can include system-added tokens which are not billed, so it is very slightly conservative. For a window check conservative is the direction you want, and the margin is nowhere near the size of the overflow you are trying to catch. Do not swap it for tiktoken, which is a different vendor's tokenizer entirely."),
 ("Does prompt caching buy me more window?",
  "No, and this is the most common wrong turn here. input_tokens, cache_read_input_tokens and cache_creation_input_tokens all occupy the window. Caching changes what those tokens cost and how they count against the input limiter; it does not change how much room they take. A cache breakpoint will move your bill and leave this number exactly where it was."),
 ("Why does the same payload 400 on one model and return 200 on another?",
  "Because the behaviour changed with the model generation. On Claude 4.5 and newer, input that fits with a max_tokens reservation that does not is accepted and stops with model_context_window_exceeded. On earlier models the same combination is a validation error unless the model-context-window-exceeded-2025-08-26 beta header is sent. That is why a model swap can turn a loud failure into a quiet one."),
 ("What actually reduces the count?",
  "In order of how much they usually give back: server-side compaction for long conversations, context editing to clear old tool results and thinking blocks in an agent loop, and the tool search tool so that tool definitions stop being resident on every turn. Trimming the system prompt is the one everyone tries first and it is almost never where the tokens are."),
],
"related": [REL_BYTES, REL_CAP, REL_LONGCTX],
"citations": [CITE_CL_CONTEXT, CITE_CL_COUNT, CITE_CL_STOP, CITE_CL_MODELS],
},
{
"slug": "request-too-large-413",
"title": "A 32 MB request is rejected with 413 before Anthropic sees it",
"description": "The only ceiling in this set measured in bytes, not tokens. Cloudflare rejects it in front of the API, so the failure appears in no usage report at all.",
"h1": "A 32 MB request is rejected with 413 before Anthropic sees it",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic 413 request_too_large", "claude 32mb request limit",
             "claude base64 pdf too large", "anthropic files api file_id",
             "request exceeds the maximum allowed number of bytes"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key. GET requests plus the free count_tokens probe.",
"lead": "The PDF is 24 MB, which everybody agreed was fine, because the context window is 200,000 tokens and a 24 MB PDF is nothing like 200,000 tokens. The request comes back <code>413</code> anyway, with a body that does not look like Anthropic's usual error envelope, and nothing about it appears in the usage report. It never reached Anthropic. It was refused by a proxy in front of the API, for a reason that has nothing to do with tokens.",
"short_answer": """<p>This ceiling is in <strong>bytes</strong>. The Messages API and the Token Counting API both cap a request at <strong>32 MB</strong>; the Batch API allows 256 MB and the Files API 500 MB. Serialize the body your client actually sends and measure its length. No token count is involved anywhere in this check.</p>
<p>Base64 is what closes the gap. Encoding inflates a payload by about a third, so a 24 MB file becomes 32 MB of JSON string before the envelope is added. That is the arithmetic behind almost every 413 anyone hits.</p>
<p>Confirm it for free: <code>POST /v1/messages/count_tokens</code> shares the same 32 MB ceiling and costs nothing, so posting the identical body there returns 413 on exactly the bodies message creation would reject. Read its <em>status code</em>, not its token number.</p>""",
"problem": """<p>A 413 from the Claude API is unlike the other errors in the platform, because Anthropic did not produce it. Cloudflare sits in front of the API and refuses oversized requests before they are routed, so the rejection happens outside the application. That has three consequences and all of them are confusing at three in the morning.</p>
<p>The error body may not be Anthropic's JSON envelope, so an SDK that expects <code>{"type": "error", "error": {...}}</code> can fail to parse the failure and raise something unhelpful about the response instead. The request appears in no usage report, because nothing was ever counted. And the size that matters is the size on the wire, which nobody in the room has ever looked at &mdash; the team knows the page count, the token estimate and the file size in the bucket, and none of those three is the number Cloudflare measured.</p>
<p>Meanwhile the check people write is the wrong check. They compare the document against the context window, find 40,000 tokens against 200,000, and conclude there is room. There is room. The request is still refused, because a request can be far under the token ceiling and far over the byte one, and those two limits do not know about each other.</p>""",
"why": """<p><strong>Base64 costs you a third, exactly and predictably.</strong> Three raw bytes become four ASCII characters, so the encoded string is 4/3 the size of the file. A 24 MiB PDF encodes to precisely 32 MiB before you have added a single key of JSON around it. Anything you were planning to attach inline has to be under about 24 MB raw, and that number is the one worth writing down.</p>
<p><strong>The content ceiling is a third, independent limit.</strong> One request may include up to <strong>600</strong> images or PDF pages, and only <strong>100</strong> on the 200k-context models. A 300-page scanned document can be comfortably under 32 MB, comfortably under the window, and still refused for the page count alone. Three ceilings, three units, one request.</p>
<p><strong>Your JSON encoder may be inflating the payload after you measure it.</strong> An encoder configured to escape non-ASCII turns one three-byte character into six ASCII ones. On a payload that is mostly Japanese, Arabic or emoji that is close to a doubling, and it happens between the size you measured and the bytes on the wire. Measuring the object rather than the serialized string is how a payload passes your check and fails Cloudflare's.</p>
<p><strong>A newline inside the base64 string is its own rejection.</strong> Inline base64 must be unbroken; a library that wraps encoded output at 76 characters, which several still do by default, produces a string the API will not accept. That is a validation failure rather than a size one, and it is worth reporting separately so nobody spends an afternoon shrinking a file that was never too big.</p>
<p><strong>The free probe is a status code, not a number.</strong> The counting endpoint shares the 32 MB limit, so it 413s on exactly the bodies message creation would 413 on, at no cost. It also returns an <code>input_tokens</code> number, and this script deliberately ignores it. That number answers <a href="/llm/prompt-too-long-context-overflow/">a different question</a> with a different ceiling and a different repair.</p>""",
"steps": [
 {"h": "Serialize the body, then measure the string",
  "body": """<p>Not the file, not the object, not the sum of the parts: the exact JSON your HTTP client will send, encoded as UTF-8, measured in bytes. Compact separators, and the same non-ASCII escaping setting your client uses. This is the only measurement Cloudflare agrees with.</p>"""},
 {"h": "Compare against the ceiling for the endpoint you are calling",
  "body": """<p>32 MB for Messages and for Token Counting, 256 MB for the Batch API, 500 MB for the Files API. The batch case has a second ceiling to check at the same time: 100,000 requests per batch, and the sum of every serialized <code>params</code> block against 256 MB.</p>"""},
 {"h": "Count the images and pages separately",
  "body": """<p>Read <code>max_input_tokens</code> from <code>GET /v1/models/{id}</code> and use it to pick the content cap: 100 on a 200k-context model, 600 on the larger ones. Then count the <code>image</code> and <code>document</code> blocks. This ceiling is unrelated to the other two and fails with its own error.</p>"""},
 {"h": "Probe for free with the counting endpoint",
  "body": """<p>Post the identical body to <code>POST /v1/messages/count_tokens</code>. It is free, it generates nothing, it creates nothing, and it enforces the same 32 MB limit. A 413 back is proof; a 200 back means you are inside the byte ceiling. Read the status, ignore the token count, and remember this is an oracle for the 32 MB endpoints only &mdash; a 200 MB batch body will 413 here and be perfectly legal where it is going.</p>"""},
 {"h": "Print the repair: the Files API, or a split",
  "body": """<p>The fix for a large attachment is almost always the Files API: upload once at up to 500 MB, then reference it by <code>file_id</code> on every subsequent request, which removes the bytes from the request entirely and stops you re-uploading the same document on every turn. The fix for too many pages is a split. Neither is something an audit should do on your behalf, so the script prints them.</p>"""},
],
"verify": """<p>Re-run against the same payload after moving the attachment to a <code>file_id</code>. The serialized body should collapse to a few kilobytes.</p>
<pre><code class="language-bash">python3 anthropic_request_bytes.py --payload invoice-batch.json
# over-byte-ceiling    invoice-batch.json   34.1 MB of 32.0 MB (107%). Cloudflare rejects ...
#   base64: 1 blob, 25.6 MB raw inflated to 34.1 MB encoded (133%)
#   largest raw file that still fits inline on this endpoint: 24.0 MB
# 1 payload(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Bytes throughout. One GET for the model object, so the per-request content cap is read rather than guessed, and one optional free <code>count_tokens</code> call used purely as a 413 oracle &mdash; the script never reads the token number it returns, because that is the other note's ceiling. Nine pure functions and not one of them touches a tokenizer: the serializer that measures what goes on the wire, the base64 size arithmetic in both directions, the inline budget that tells you the largest raw file that still fits, the escaping penalty a JSON encoder can add after you measure, the content cap that depends on the model's window, the newline check, and the verdicts.",
"py_file": "anthropic_request_bytes.py",
"py": '''"""Measure a Claude request in bytes against the 32 MB ceiling.

Read only. One GET for the model object, and one optional call to
/v1/messages/count_tokens, which is free, creates no object, generates no
completion and is not billed. That call is used here only as an oracle: it
shares the same 32 MB ceiling, so its status code tells you whether message
creation would refuse the same body, at no cost. Its input_tokens number is
deliberately never read, because this script is about bytes.

/v1/messages is never called and nothing is uploaded. The repair is printed.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_request_bytes")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

MB = 1024 * 1024

# Per endpoint, in bytes. Binary megabytes: if a payload lands within a percent
# of one of these lines, treat it as over rather than arguing about whether the
# published number meant 1000 or 1024, because the margin is not worth an
# outage.
CEILINGS = {
    "messages": 32 * MB,
    "count_tokens": 32 * MB,
    "batches": 256 * MB,
    "files": 500 * MB,
}

# Sampling parameters the counting endpoint rejects. Stripped only for the
# probe; the measurement is always taken on the real body.
SAMPLING_ONLY = ("max_tokens", "stream", "temperature", "top_p", "top_k",
                 "stop_sequences", "metadata", "service_tier")

NEWLINES = ("\\n", "\\r")

FINDINGS = ("over-byte-ceiling", "near-byte-ceiling", "over-content-cap",
            "base64-has-newlines")


def serialized_bytes(body, escape_non_ascii=False):
    """The size of the JSON that actually goes on the wire. Pure.

    Measuring the object rather than the string is the mistake this exists to
    stop: a payload can be well inside the ceiling as a dict and outside it as
    the bytes a client sends, which is the only size the proxy in front of the
    API ever sees.
    """
    text = json.dumps(body, separators=(",", ":"), ensure_ascii=escape_non_ascii)
    return len(text.encode("utf-8"))


def human(size):
    """Bytes as a short readable string. Pure. Binary units throughout."""
    n = float(size or 0)
    if n < 1024:
        return "%d B" % int(n)
    if n < MB:
        return "%.1f KB" % (n / 1024.0)
    return "%.1f MB" % (n / float(MB))


def b64_encoded_size(raw_bytes):
    """How large a file becomes once base64 encoded. Pure.

    Three bytes in, four characters out, rounded up to the padding boundary.
    Exactly a third larger, which is why a 24 MiB file lands on precisely the
    32 MiB line before a single key of JSON is wrapped around it.
    """
    raw = max(0, int(raw_bytes or 0))
    return ((raw + 2) // 3) * 4


def b64_decoded_size(text):
    """The raw size behind a base64 string, without decoding it. Pure.

    Decoding a 32 MB string to find out how big the original was allocates 24 MB
    to answer a question arithmetic answers for free.
    """
    clean = "".join(str(text or "").split())
    if not clean:
        return 0
    return (len(clean) // 4) * 3 - clean.count("=")


def inline_budget(ceiling, envelope=0):
    """The largest raw file that still fits inline under `ceiling`. Pure.

    The number worth writing on the ticket. Everything above it has to go
    through the Files API whatever anybody hoped.
    """
    room = max(0, int(ceiling or 0) - max(0, int(envelope or 0)))
    return (room // 4) * 3


def content_blocks(body):
    """Every content block in a Messages body, flattened. Pure."""
    out = []
    if not isinstance(body, dict):
        return out
    system = body.get("system")
    if isinstance(system, list):
        out.extend(b for b in system if isinstance(b, dict))
    for message in body.get("messages") or []:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, list):
            out.extend(b for b in content if isinstance(b, dict))
    return out


def content_units(body):
    """Images and documents in one request. Pure.

    Counted against a ceiling that has nothing to do with bytes or tokens: a
    request may carry a limited number of images and PDF pages whatever its
    size, and a scanned document can pass both other checks and fail this one.
    """
    return sum(1 for b in content_blocks(body)
               if b.get("type") in ("image", "document"))


def base64_blobs(body):
    """Every inline base64 attachment, sized. Pure."""
    out = []
    for block in content_blocks(body):
        source = block.get("source")
        if not isinstance(source, dict) or source.get("type") != "base64":
            continue
        data = source.get("data")
        if not isinstance(data, str):
            continue
        out.append({
            "block": block.get("type"),
            "media_type": source.get("media_type"),
            "encoded": len(data.encode("utf-8")),
            "raw": b64_decoded_size(data),
            "newlines": any(ch in data for ch in NEWLINES),
        })
    return out


def escaping_penalty(body):
    """How much larger the body gets if the client escapes non-ASCII. Pure.

    A JSON encoder writing backslash-u escapes turns one three-byte character
    into six ASCII ones. On a payload that is mostly CJK or emoji that is close
    to a doubling, and it happens after you measured and before the request
    leaves.
    """
    plain = serialized_bytes(body, escape_non_ascii=False)
    if plain <= 0:
        return 1.0
    return serialized_bytes(body, escape_non_ascii=True) / float(plain)


def content_cap(window):
    """Images and PDF pages allowed in one request. Pure. None if unknown.

    Read off the model's context window because the two move together: 100 on
    the 200k-context models, 600 on the larger ones. This is still not a token
    check. The window is being used here only to pick which content cap applies.
    """
    if not isinstance(window, int) or window <= 0:
        return None
    return 100 if window <= 200_000 else 600


def size_verdict(endpoint, size, near=0.8):
    """Classify one serialized body against one endpoint ceiling. Pure."""
    ceiling = CEILINGS.get(endpoint)
    if ceiling is None:
        return ("endpoint-unknown",
                "no published byte ceiling for %r, so there is nothing to "
                "compare %s against" % (endpoint, human(size)))
    shape = "%s of %s (%.0f%%)" % (human(size), human(ceiling),
                                   size / float(ceiling) * 100)
    if size > ceiling:
        return ("over-byte-ceiling",
                "%s. Cloudflare refuses this in front of the API with 413 "
                "request_too_large, so it never reaches Anthropic and never "
                "appears in any usage report." % shape)
    if size >= ceiling * near:
        return ("near-byte-ceiling",
                "%s. Base64 costs a third on the way in, so one more "
                "attachment crosses the line." % shape)
    return ("fits", "%s." % shape)


def content_verdict(units, cap):
    """Classify the image and page count against the per request cap. Pure."""
    if cap is None:
        return ("content-cap-unknown",
                "%d image or document block(s), and no window on the model "
                "object to size the per request cap from" % units)
    if units > cap:
        return ("over-content-cap",
                "%d image or document block(s) against a cap of %d for this "
                "model, which is refused whatever the payload weighs"
                % (units, cap))
    return ("content-fits", "%d image or document block(s) of a %d cap"
            % (units, cap))


def probe_state(status):
    """What the free counting endpoint's status code proves. Pure.

    Status only. The body carries a token count and this script does not read
    it: that number belongs to the context window ceiling, which is a separate
    limit with a separate repair.
    """
    if status == 413:
        return ("confirmed-413",
                "the counting endpoint refused this body at the same 32 MB "
                "ceiling, so message creation refuses it too")
    if status == 200:
        return ("under-byte-ceiling",
                "the counting endpoint accepted the body, so it is inside the "
                "32 MB ceiling for the endpoints that share it")
    return ("probe-inconclusive",
            "the counting endpoint answered %s, which is neither the 413 nor "
            "the 200 this probe reads" % status)


def get(session, path):
    r = session.get(API + path, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY has to be a "
                         "workspace key" % r.status_code)
    r.raise_for_status()
    return r.json()


def probe(session, body):
    """The one non-GET call, and it neither creates nor bills anything.

    The trimmed body is a few dozen bytes smaller than the one you will send.
    That matters only if you are within a few dozen bytes of 32 MB, and if you
    are, you are over.
    """
    trimmed = {k: v for k, v in (body or {}).items() if k not in SAMPLING_ONLY}
    r = session.post(API + "/messages/count_tokens", json=trimmed, timeout=120)
    return r.status_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", action="append", default=[], required=True,
                    metavar="FILE", help="a JSON file holding a real request body")
    ap.add_argument("--endpoint", default="messages",
                    choices=sorted(CEILINGS), help="which ceiling applies")
    ap.add_argument("--near", type=float, default=0.8,
                    help="share of the ceiling at which a body that still fits "
                         "is reported anyway (default 0.8)")
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the free count_tokens status check")
    ap.add_argument("--show-all", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION,
                            "content-type": "application/json"})

    windows = {}
    checked = 0
    bad = 0

    for path in args.payload:
        with open(path, "r", encoding="utf-8") as fh:
            body = json.load(fh)
        checked += 1

        size = serialized_bytes(body)
        state, detail = size_verdict(args.endpoint, size, args.near)
        line = "%-20s %-30s %s" % (state, path, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
        elif state == "endpoint-unknown":
            log.warning(line)
        elif args.show_all:
            log.info(line)

        blobs = base64_blobs(body)
        if blobs:
            raw = sum(b["raw"] for b in blobs)
            encoded = sum(b["encoded"] for b in blobs)
            log.info("  base64: %d blob(s), %s raw inflated to %s encoded (%.0f%%)",
                     len(blobs), human(raw), human(encoded),
                     encoded / float(raw) * 100 if raw else 0)
        broken = [b for b in blobs if b["newlines"]]
        if broken:
            bad += 1
            log.warning("%-20s %-30s %d inline blob(s) contain line breaks; "
                        "inline base64 has to be unbroken, and several encoders "
                        "still wrap at 76 characters by default",
                        "base64-has-newlines", path, len(broken))

        penalty = escaping_penalty(body)
        if penalty > 1.05:
            log.warning("  a client escaping non-ASCII would send %.0f%% more "
                        "than measured here (%s), which is enough to cross the "
                        "ceiling on its own",
                        (penalty - 1) * 100, human(int(size * penalty)))

        model = str(body.get("model") or "")
        window = None
        if model:
            if model not in windows:
                obj = get(session, "/models/" + model)
                windows[model] = obj.get("max_input_tokens")
            window = windows[model]
        units = content_units(body)
        if units:
            cstate, cdetail = content_verdict(units, content_cap(window))
            if cstate == "over-content-cap":
                bad += 1
                log.warning("%-20s %-30s %s", cstate, path, cdetail)
            elif cstate == "content-cap-unknown":
                log.warning("%-20s %-30s %s", cstate, path, cdetail)
            elif args.show_all:
                log.info("%-20s %-30s %s", cstate, path, cdetail)

        if not args.no_probe:
            pstate, pdetail = probe_state(probe(session, body))
            log.info("  probe: %s, %s", pstate, pdetail)

        if state in ("over-byte-ceiling", "near-byte-ceiling"):
            ceiling = CEILINGS[args.endpoint]
            envelope = size - sum(b["encoded"] for b in blobs)
            log.warning("  largest raw file that still fits inline on this "
                        "endpoint: %s", human(inline_budget(ceiling, envelope)))
            log.warning("  repair: upload the attachment once through the Files "
                        "API (500 MB) and reference it by file_id, which takes "
                        "the bytes out of every request rather than one. Or "
                        "split the request. Printed, not performed.")

    log.info("%d payload(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-request-bytes.mjs",
"js": '''/**
 * Measure a Claude request in bytes against the 32 MB ceiling.
 *
 * Read only. One GET for the model object, and one optional call to
 * /v1/messages/count_tokens, which is free, creates no object, generates no
 * completion and is not billed. It is used purely as an oracle: it shares the
 * same 32 MB ceiling, so its status code answers the byte question at no cost.
 * The token number it returns is deliberately never read.
 *
 * /v1/messages is never called and nothing is uploaded.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const MB = 1024 * 1024;

const CEILINGS = {
  messages: 32 * MB,
  count_tokens: 32 * MB,
  batches: 256 * MB,
  files: 500 * MB,
};

const SAMPLING_ONLY = new Set(['max_tokens', 'stream', 'temperature', 'top_p',
  'top_k', 'stop_sequences', 'metadata', 'service_tier']);

const FINDINGS = new Set(['over-byte-ceiling', 'near-byte-ceiling',
  'over-content-cap', 'base64-has-newlines']);

/** The size of the JSON that actually goes on the wire. Pure. */
export function serializedBytes(body, escapeNonAscii = false) {
  let text = JSON.stringify(body);
  if (text === undefined) text = 'null';
  if (escapeNonAscii) {
    text = text.replace(/[\\u0080-\\uffff]/g, (ch) =>
      '\\\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'));
  }
  return Buffer.byteLength(text, 'utf8');
}

/** Bytes as a short readable string. Pure. Binary units throughout. */
export function human(size) {
  const n = Number(size || 0);
  if (n < 1024) return `${Math.trunc(n)} B`;
  if (n < MB) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / MB).toFixed(1)} MB`;
}

/**
 * How large a file becomes once base64 encoded. Pure.
 * Three bytes in, four characters out: exactly a third larger, which is why a
 * 24 MiB file lands on precisely the 32 MiB line.
 */
export function b64EncodedSize(rawBytes) {
  const raw = Math.max(0, Math.trunc(rawBytes || 0));
  return Math.floor((raw + 2) / 3) * 4;
}

/** The raw size behind a base64 string, without decoding it. Pure. */
export function b64DecodedSize(text) {
  const clean = String(text ?? '').replace(/\\s+/g, '');
  if (!clean) return 0;
  const pad = (clean.match(/=/g) ?? []).length;
  return Math.floor(clean.length / 4) * 3 - pad;
}

/** The largest raw file that still fits inline under `ceiling`. Pure. */
export function inlineBudget(ceiling, envelope = 0) {
  const room = Math.max(0, Math.trunc(ceiling || 0) - Math.max(0, Math.trunc(envelope || 0)));
  return Math.floor(room / 4) * 3;
}

/** Every content block in a Messages body, flattened. Pure. */
export function contentBlocks(body) {
  const out = [];
  if (!body || typeof body !== 'object') return out;
  if (Array.isArray(body.system)) {
    out.push(...body.system.filter((b) => b && typeof b === 'object'));
  }
  for (const message of body.messages ?? []) {
    if (!message || typeof message !== 'object') continue;
    if (Array.isArray(message.content)) {
      out.push(...message.content.filter((b) => b && typeof b === 'object'));
    }
  }
  return out;
}

/** Images and documents in one request. Pure. A ceiling of its own. */
export function contentUnits(body) {
  return contentBlocks(body).filter((b) => b.type === 'image' || b.type === 'document').length;
}

/** Every inline base64 attachment, sized. Pure. */
export function base64Blobs(body) {
  const out = [];
  for (const block of contentBlocks(body)) {
    const source = block.source;
    if (!source || typeof source !== 'object' || source.type !== 'base64') continue;
    const data = source.data;
    if (typeof data !== 'string') continue;
    out.push({
      block: block.type,
      media_type: source.media_type,
      encoded: Buffer.byteLength(data, 'utf8'),
      raw: b64DecodedSize(data),
      newlines: data.includes('\\n') || data.includes('\\r'),
    });
  }
  return out;
}

/** How much larger the body gets if the client escapes non-ASCII. Pure. */
export function escapingPenalty(body) {
  const plain = serializedBytes(body, false);
  if (plain <= 0) return 1;
  return serializedBytes(body, true) / plain;
}

/** Images and PDF pages allowed in one request. Pure. null if unknown. */
export function contentCap(window) {
  if (!Number.isInteger(window) || window <= 0) return null;
  return window <= 200000 ? 100 : 600;
}

/** Classify one serialized body against one endpoint ceiling. Pure. */
export function sizeVerdict(endpoint, size, near = 0.8) {
  const ceiling = CEILINGS[endpoint];
  if (ceiling === undefined) {
    return ['endpoint-unknown',
      `no published byte ceiling for '${endpoint}', so there is nothing to ` +
      `compare ${human(size)} against`];
  }
  const shape = `${human(size)} of ${human(ceiling)} (${(size / ceiling * 100).toFixed(0)}%)`;
  if (size > ceiling) {
    return ['over-byte-ceiling',
      `${shape}. Cloudflare refuses this in front of the API with 413 ` +
      'request_too_large, so it never reaches Anthropic and never appears in ' +
      'any usage report.'];
  }
  if (size >= ceiling * near) {
    return ['near-byte-ceiling',
      `${shape}. Base64 costs a third on the way in, so one more attachment ` +
      'crosses the line.'];
  }
  return ['fits', `${shape}.`];
}

/** Classify the image and page count against the per request cap. Pure. */
export function contentVerdict(units, cap) {
  if (cap === null || cap === undefined) {
    return ['content-cap-unknown',
      `${units} image or document block(s), and no window on the model object ` +
      'to size the per request cap from'];
  }
  if (units > cap) {
    return ['over-content-cap',
      `${units} image or document block(s) against a cap of ${cap} for this ` +
      'model, which is refused whatever the payload weighs'];
  }
  return ['content-fits', `${units} image or document block(s) of a ${cap} cap`];
}

/** What the free counting endpoint's status code proves. Pure. Status only. */
export function probeState(status) {
  if (status === 413) {
    return ['confirmed-413',
      'the counting endpoint refused this body at the same 32 MB ceiling, so ' +
      'message creation refuses it too'];
  }
  if (status === 200) {
    return ['under-byte-ceiling',
      'the counting endpoint accepted the body, so it is inside the 32 MB ' +
      'ceiling for the endpoints that share it'];
  }
  return ['probe-inconclusive',
    `the counting endpoint answered ${status}, which is neither the 413 nor ` +
    'the 200 this probe reads'];
}

function headers(key) {
  return { 'x-api-key': key, 'anthropic-version': VERSION,
           'content-type': 'application/json' };
}

async function get(key, path) {
  const res = await fetch(API + path, { headers: headers(key) });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY has to be a workspace key`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

/** The one non-GET call, and it neither creates nor bills anything. */
async function probe(key, body) {
  const trimmed = Object.fromEntries(
    Object.entries(body ?? {}).filter(([k]) => !SAMPLING_ONLY.has(k)));
  const res = await fetch(`${API}/messages/count_tokens`, {
    method: 'POST',  // count_tokens creates nothing and bills nothing
    headers: headers(key),
    body: JSON.stringify(trimmed),
  });
  return res.status;
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key');
    process.exitCode = 2;
    return;
  }
  const paths = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  if (paths.length === 0) {
    console.error('pass one or more payload JSON files');
    process.exitCode = 2;
    return;
  }
  const endpoint = process.env.ENDPOINT ?? 'messages';
  const near = Number(process.env.NEAR ?? 0.8);
  const noProbe = process.env.NO_PROBE === '1';
  const showAll = process.env.SHOW_ALL === '1';

  const windows = new Map();
  let checked = 0;
  let bad = 0;

  for (const path of paths) {
    const body = JSON.parse(await readFile(path, 'utf8'));
    checked += 1;

    const size = serializedBytes(body);
    const [state, detail] = sizeVerdict(endpoint, size, near);
    const line = `${state.padEnd(20)} ${path.padEnd(30)} ${detail}`;
    if (FINDINGS.has(state)) { bad += 1; console.warn(line); }
    else if (state === 'endpoint-unknown') console.warn(line);
    else if (showAll) console.log(line);

    const blobs = base64Blobs(body);
    if (blobs.length) {
      const raw = blobs.reduce((s, b) => s + b.raw, 0);
      const encoded = blobs.reduce((s, b) => s + b.encoded, 0);
      console.log(`  base64: ${blobs.length} blob(s), ${human(raw)} raw inflated ` +
                  `to ${human(encoded)} encoded ` +
                  `(${raw ? (encoded / raw * 100).toFixed(0) : 0}%)`);
    }
    const broken = blobs.filter((b) => b.newlines);
    if (broken.length) {
      bad += 1;
      console.warn(`${'base64-has-newlines'.padEnd(20)} ${path.padEnd(30)} ` +
                   `${broken.length} inline blob(s) contain line breaks; inline ` +
                   'base64 has to be unbroken, and several encoders still wrap ' +
                   'at 76 characters by default');
    }

    const penalty = escapingPenalty(body);
    if (penalty > 1.05) {
      console.warn(`  a client escaping non-ASCII would send ` +
                   `${((penalty - 1) * 100).toFixed(0)}% more than measured here ` +
                   `(${human(Math.trunc(size * penalty))}), which is enough to ` +
                   'cross the ceiling on its own');
    }

    const model = String(body.model ?? '');
    let window = null;
    if (model) {
      if (!windows.has(model)) {
        windows.set(model, (await get(key, `/models/${model}`)).max_input_tokens ?? null);
      }
      window = windows.get(model);
    }
    const units = contentUnits(body);
    if (units) {
      const [cstate, cdetail] = contentVerdict(units, contentCap(window));
      const cline = `${cstate.padEnd(20)} ${path.padEnd(30)} ${cdetail}`;
      if (cstate === 'over-content-cap') { bad += 1; console.warn(cline); }
      else if (cstate === 'content-cap-unknown') console.warn(cline);
      else if (showAll) console.log(cline);
    }

    if (!noProbe) {
      const [pstate, pdetail] = probeState(await probe(key, body));
      console.log(`  probe: ${pstate}, ${pdetail}`);
    }

    if (state === 'over-byte-ceiling' || state === 'near-byte-ceiling') {
      const envelope = size - blobs.reduce((s, b) => s + b.encoded, 0);
      console.warn('  largest raw file that still fits inline on this endpoint: ' +
                   human(inlineBudget(CEILINGS[endpoint], envelope)));
      console.warn('  repair: upload the attachment once through the Files API ' +
                   '(500 MB) and reference it by file_id, which takes the bytes ' +
                   'out of every request rather than one. Or split the request. ' +
                   'Printed, not performed.');
    }
  }

  console.log(`${checked} payload(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the arithmetic the whole note rests on: 24 MiB of raw file base64 encodes to exactly 33,554,432 bytes, which is the 32 MB ceiling to the byte, so the JSON wrapped around it is what pushes the request over. The second is the trap &mdash; a payload can be a long way inside the byte ceiling and still be refused for carrying more images than the model allows, and the cap it is refused against depends on the model's window. The rest pin the parts that move between measuring and sending: a JSON encoder that escapes non-ASCII, a base64 library that wraps at 76 characters, and a probe whose <em>status code</em> is the answer while its token count is somebody else's question.",
"test_py_file": "test_anthropic_request_bytes.py",
"test_py": '''from anthropic_request_bytes import (b64_decoded_size, b64_encoded_size,
                                      base64_blobs, content_cap, content_units,
                                      content_verdict, escaping_penalty, human,
                                      inline_budget, probe_state,
                                      serialized_bytes, size_verdict)

MB = 1024 * 1024


def test_a_24mb_file_lands_exactly_on_the_32mb_line():
    # The arithmetic the note is about. Three bytes become four characters, so
    # 24 MiB encodes to precisely 32 MiB and everything else in the request is
    # what takes it over.
    assert b64_encoded_size(24 * MB) == 32 * MB == 33_554_432
    assert size_verdict("messages", 32 * MB)[0] == "near-byte-ceiling"
    state, detail = size_verdict("messages", 32 * MB + 4_096)
    assert state == "over-byte-ceiling"
    assert "Cloudflare" in detail
    assert "never appears in any usage report" in detail
    # And the number to put on the ticket, once the envelope is accounted for.
    assert inline_budget(32 * MB, 4_096) == 24 * MB - 3_072


def test_the_image_cap_is_a_separate_ceiling_from_the_bytes():
    # 300 pages of tiny scans: nowhere near 32 MB, refused anyway, and the cap
    # depends on the model's window rather than on the payload.
    assert content_cap(200_000) == 100
    assert content_cap(1_000_000) == 600
    assert content_cap(None) is None
    assert content_verdict(300, 100)[0] == "over-content-cap"
    assert content_verdict(300, 600)[0] == "content-fits"
    assert content_verdict(300, None)[0] == "content-cap-unknown"
    assert size_verdict("messages", 2 * MB)[0] == "fits"


def test_the_ceiling_depends_on_the_endpoint_not_on_the_body():
    body_size = 200 * MB
    assert size_verdict("messages", body_size)[0] == "over-byte-ceiling"
    assert size_verdict("batches", body_size)[0] == "fits"
    assert size_verdict("files", body_size)[0] == "fits"
    assert size_verdict("responses", body_size)[0] == "endpoint-unknown"


def test_blobs_are_sized_without_decoding_them():
    data = "QUJDREVGR0g="  # eight raw bytes, twelve encoded characters
    body = {"model": "claude-sonnet-5", "messages": [{"role": "user", "content": [
        {"type": "text", "text": "read this"},
        {"type": "document", "source": {"type": "base64",
                                        "media_type": "application/pdf",
                                        "data": data}},
    ]}]}
    blobs = base64_blobs(body)
    assert len(blobs) == 1
    assert blobs[0]["media_type"] == "application/pdf"
    assert blobs[0]["encoded"] == 12
    assert blobs[0]["raw"] == b64_decoded_size(data) == 8
    assert blobs[0]["newlines"] is False
    assert content_units(body) == 1


def test_line_wrapped_base64_is_its_own_rejection():
    # Not a size problem at all: several encoders wrap at 76 characters by
    # default and the API will not accept the result.
    body = {"messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                     "data": "QUJDREVG\\nR0g="}}]}]}
    assert base64_blobs(body)[0]["newlines"] is True
    # And the whitespace is not counted as payload when the size is worked out.
    assert base64_blobs(body)[0]["raw"] == 8


def test_a_client_that_escapes_non_ascii_sends_more_than_you_measured():
    body = {"messages": [{"role": "user", "content": "\\u3053\\u3093\\u306b\\u3061\\u306f" * 100}]}
    plain = serialized_bytes(body)
    escaped = serialized_bytes(body, escape_non_ascii=True)
    assert escaped > plain
    assert escaping_penalty(body) == escaped / float(plain)
    assert escaping_penalty(body) > 1.9
    # ASCII payloads are unaffected, so this never fires as noise.
    assert escaping_penalty({"messages": [{"role": "user", "content": "hello"}]}) == 1.0


def test_the_probe_is_read_as_a_status_code_not_as_a_token_count():
    assert probe_state(413)[0] == "confirmed-413"
    assert probe_state(200)[0] == "under-byte-ceiling"
    assert probe_state(400)[0] == "probe-inconclusive"
    assert probe_state(429)[0] == "probe-inconclusive"


def test_sizes_are_printed_in_binary_units():
    assert human(0) == "0 B"
    assert human(1023) == "1023 B"
    assert human(1024) == "1.0 KB"
    assert human(32 * MB) == "32.0 MB"
''',
"test_js_file": "anthropic-request-bytes.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { b64DecodedSize, b64EncodedSize, base64Blobs, contentCap, contentUnits,
         contentVerdict, escapingPenalty, human, inlineBudget, probeState,
         serializedBytes, sizeVerdict } from './anthropic-request-bytes.mjs';

const MB = 1024 * 1024;

test('a 24mb file lands exactly on the 32mb line', () => {
  assert.equal(b64EncodedSize(24 * MB), 32 * MB);
  assert.equal(b64EncodedSize(24 * MB), 33554432);
  assert.equal(sizeVerdict('messages', 32 * MB)[0], 'near-byte-ceiling');
  const [state, detail] = sizeVerdict('messages', 32 * MB + 4096);
  assert.equal(state, 'over-byte-ceiling');
  assert.match(detail, /Cloudflare/);
  assert.match(detail, /never appears in any usage report/);
  assert.equal(inlineBudget(32 * MB, 4096), 24 * MB - 3072);
});

test('the image cap is a separate ceiling from the bytes', () => {
  assert.equal(contentCap(200000), 100);
  assert.equal(contentCap(1000000), 600);
  assert.equal(contentCap(null), null);
  assert.equal(contentVerdict(300, 100)[0], 'over-content-cap');
  assert.equal(contentVerdict(300, 600)[0], 'content-fits');
  assert.equal(contentVerdict(300, null)[0], 'content-cap-unknown');
  assert.equal(sizeVerdict('messages', 2 * MB)[0], 'fits');
});

test('the ceiling depends on the endpoint not on the body', () => {
  const size = 200 * MB;
  assert.equal(sizeVerdict('messages', size)[0], 'over-byte-ceiling');
  assert.equal(sizeVerdict('batches', size)[0], 'fits');
  assert.equal(sizeVerdict('files', size)[0], 'fits');
  assert.equal(sizeVerdict('responses', size)[0], 'endpoint-unknown');
});

test('blobs are sized without decoding them', () => {
  const data = 'QUJDREVGR0g=';  // eight raw bytes, twelve encoded characters
  const body = { model: 'claude-sonnet-5', messages: [{ role: 'user', content: [
    { type: 'text', text: 'read this' },
    { type: 'document', source: { type: 'base64', media_type: 'application/pdf', data } },
  ] }] };
  const blobs = base64Blobs(body);
  assert.equal(blobs.length, 1);
  assert.equal(blobs[0].media_type, 'application/pdf');
  assert.equal(blobs[0].encoded, 12);
  assert.equal(blobs[0].raw, b64DecodedSize(data));
  assert.equal(blobs[0].raw, 8);
  assert.equal(blobs[0].newlines, false);
  assert.equal(contentUnits(body), 1);
});

test('line wrapped base64 is its own rejection', () => {
  const body = { messages: [{ role: 'user', content: [
    { type: 'image', source: { type: 'base64', media_type: 'image/png',
                               data: 'QUJDREVG\\nR0g=' } }] }] };
  assert.equal(base64Blobs(body)[0].newlines, true);
  assert.equal(base64Blobs(body)[0].raw, 8);
});

test('a client that escapes non ascii sends more than you measured', () => {
  const body = { messages: [{ role: 'user', content: '\\u3053\\u3093\\u306b\\u3061\\u306f'.repeat(100) }] };
  const plain = serializedBytes(body);
  const escaped = serializedBytes(body, true);
  assert.ok(escaped > plain);
  assert.equal(escapingPenalty(body), escaped / plain);
  assert.ok(escapingPenalty(body) > 1.9);
  assert.equal(escapingPenalty({ messages: [{ role: 'user', content: 'hello' }] }), 1);
});

test('the probe is read as a status code not as a token count', () => {
  assert.equal(probeState(413)[0], 'confirmed-413');
  assert.equal(probeState(200)[0], 'under-byte-ceiling');
  assert.equal(probeState(400)[0], 'probe-inconclusive');
  assert.equal(probeState(429)[0], 'probe-inconclusive');
});

test('sizes are printed in binary units', () => {
  assert.equal(human(0), '0 B');
  assert.equal(human(1023), '1023 B');
  assert.equal(human(1024), '1.0 KB');
  assert.equal(human(32 * MB), '32.0 MB');
});
''',
"faq": [
 ("Why does the 413 not show up in my usage report?",
  "Because nothing was used. On the direct Claude API a request over the byte ceiling is refused by Cloudflare in front of Anthropic's servers, so no model was invoked, no tokens were counted and no line item exists. This also explains the odd error body: what you are reading was written by the proxy, not by the API, which is why an SDK expecting Anthropic's error envelope can fail to parse it."),
 ("How big can an inline file actually be?",
  "About 24 MB raw on the Messages API, because base64 makes it a third larger and 24 MiB encodes to exactly 32 MiB before any JSON is wrapped around it. Subtract whatever your system prompt, tools and conversation weigh and the practical number is a little lower. Anything above that has to go through the Files API."),
 ("Is the probe safe to run against production?",
  "Yes, and that is the point of using it. The counting endpoint creates no message, generates no output, is not billed, and runs on its own rate limit rather than the message limiter. It shares the 32 MB ceiling, so its status code answers the byte question exactly. It is the one non-GET call in this batch and it changes nothing on your account."),
 ("I am under 32 MB and under the context window and still getting rejected.",
  "Check the two ceilings that are neither of those. A request may carry at most 600 images or PDF pages, and only 100 on the 200k-context models, whatever the payload weighs. And inline base64 must be unbroken: an encoder that wraps at 76 characters produces a string the API refuses on validation grounds rather than size grounds."),
 ("Does the Batch API make this go away?",
  "It moves the line rather than removing it. A batch submission may be up to 256 MB and up to 100,000 requests, but each individual params block still has to be a legal Messages request, so an oversized document is oversized there too. The Files API is the fix for size; batching is the fix for latency and price."),
],
"related": [REL_OVERFLOW, REL_WALL, REL_LONGCTX],
"citations": [CITE_CL_ERRORS, CITE_CL_COUNT, CITE_CL_FILES, CITE_CL_CONTEXT],
},
{
"slug": "max-tokens-above-model-cap",
"title": "max_tokens is set above the model's own output cap",
"description": "The model object publishes the legal ceiling for max_tokens and the docs table lags it. One shared config across two tiers 400s on the smaller model.",
"h1": "max_tokens is set above the model's own output cap",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic max_tokens invalid_request_error", "claude max output tokens per model",
             "claude haiku 64k max tokens", "GET /v1/models max_tokens",
             "output-300k-2026-03-24 beta"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key, and sends only GET requests.",
"lead": "The classifier was moved onto the cheap model on a Friday, which is the correct thing to do with a classifier. It is the same helper function everything else uses, so it inherited the same <code>max_tokens</code>, which is a number somebody picked for the model that writes reports. Every call to it now comes back <code>400</code>, and the message says exactly what is wrong, and the message is in a log that no dashboard reads.",
"short_answer": """<p><code>GET /v1/models/{model_id}</code> returns a field called <code>max_tokens</code>, documented as the maximum value for the <code>max_tokens</code> parameter when using this model. Loop it over every model id in your configuration and compare each configured value against it. That is the whole check, and there is no payload involved.</p>
<p><strong>Do not read the cap out of the docs table.</strong> The table lags releases and a constant in your source lags the table. The model object is the source of truth and it is one GET away.</p>
<p>The ceiling depends on the endpoint too. Synchronous Messages calls cap at <strong>128K</strong> output tokens on Fable 5, Opus 5, Sonnet 5, Opus 4.8, 4.7, 4.6 and Sonnet 4.6, and at <strong>64K</strong> on Haiku 4.5. On the Message Batches API the 1M-context models go to <strong>300K</strong>, but only with the <code>output-300k-2026-03-24</code> beta header.</p>""",
"problem": """<p><code>max_tokens</code> is a required parameter with no safe default, so it gets set once, early, by whoever wrote the first call, and then it propagates. It ends up in a shared helper's signature, in a config file read by four services, in the <code>params</code> block of a batch. The number is invisible at every call site that inherits it, which is exactly the property you want from shared configuration right up until the ceiling underneath it moves.</p>
<p>The ceiling moves whenever the model does. A value of 64,000 is comfortably legal on Sonnet 5 and is the entire budget on Haiku 4.5; 128,000 is legal on one and a hard 400 on the other. Nothing in a model swap flags this, because the model id and the token ceiling live in different places and only one of them was in the diff.</p>
<p>And this failure is total rather than partial. It is not a slow path or a degraded answer: the request is rejected during validation, so every single call on that path fails identically and immediately, from the first one. If the path is a nightly batch or a rarely-taken fallback branch, the first one is days away.</p>""",
"why": """<p><strong>The model object is authoritative and the table is documentation.</strong> Anthropic publishes the per-model ceiling as a field on the model resource, which means it is versioned with the model rather than with a page. Any local table of caps &mdash; in a wiki, in a constant, in this note &mdash; is a snapshot that starts drifting the day a model ships. Reading it costs one GET.</p>
<p><strong>The cap is a property of the model and the endpoint together.</strong> The same model id allows a different maximum on the Batch API than on synchronous message creation, and the higher batch ceiling is gated on a beta header. A checker that knows only the model id will clear a batch config that is over, or flag one that is fine. So will a human reading the docs table, which describes the synchronous path.</p>
<p><strong>A shared value across tiers is the finding, not a symptom of it.</strong> When one number is used by several call paths on different models, the effective ceiling is the smallest cap among them, and nobody wrote that down anywhere. This is worth reporting even when every path currently passes, because the next model swap is the one that breaks it.</p>
<p><strong>This is not a model id that stopped existing.</strong> If <code>GET /v1/models/{id}</code> 404s, the id is retired or mistyped and belongs to <a href="/llm/retired-model-id-still-in-code/">a different note</a> with a different repair. Here the id is fine, the key is fine, the endpoint is fine, and one integer is too large.</p>
<p><strong>Setting it to the ceiling is not the fix either.</strong> <code>max_tokens</code> is a hard cutoff the model cannot see, so an enormous value trades a 400 for a truncated answer and, on a non-streaming path, for <a href="/llm/non-streaming-request-over-ten-minutes/">a ten-minute timeout</a>. The repair this script prints is the model's cap and the delta, not an instruction to max it out.</p>""",
"steps": [
 {"h": "Collect the pairs, not just the model ids",
  "body": """<p>What this check needs is every <em>(call path, model id, max_tokens, endpoint)</em> tuple in your tree. Grep for <code>max_tokens</code> as well as for the model prefix: a config that names the model in one file and the token budget in another is the common shape, and only the join of the two can be wrong.</p>"""},
 {"h": "Read the cap off each model",
  "body": """<p><code>GET /v1/models/{model_id}</code> with <code>x-api-key</code> and <code>anthropic-version: 2023-06-01</code>. The <code>max_tokens</code> field on the response is the ceiling for the parameter of the same name. A 404 here is not this problem: it means the id is gone, which is a different note.</p>"""},
 {"h": "Apply the endpoint's ceiling, not the model's alone",
  "body": """<p>For a synchronous path the model object's number is the answer. For a batch path, the 1M-context models allow up to 300,000 output tokens with the <code>output-300k-2026-03-24</code> beta header, and without the header they are capped exactly as they are synchronously. Check the header is actually sent before crediting the higher ceiling.</p>"""},
 {"h": "Compare, and flag the shared values across tiers",
  "body": """<p>Report each path's configured value against its cap, with the delta. Then group by value: any number used on two model ids where the smaller cap is below it is a finding today, and any number used across tiers at all is a finding waiting for the next model swap. Also check the floor &mdash; inside a batch the minimum is <code>max_tokens &gt;= 1</code>.</p>"""},
 {"h": "Print the numbers and leave the config alone",
  "body": """<p>The output is a table: path, model, configured, cap, delta. Choosing a new value is a judgement about how long your answers need to be, and the sensible number is usually far below the ceiling. An audit script that edits a shared config is an audit script that causes an incident.</p>"""},
],
"verify": """<p>Re-run after the change. Every path should sit under its cap with visible room, and no value should be shared across two tiers.</p>
<pre><code class="language-bash">python3 anthropic_max_tokens_cap.py --config call-paths.json
# above-cap        classifier      claude-haiku-4-5-20251001  max_tokens is 128000 against a cap of 64000, ... 64000 over
#   shared value 128000 is configured on 2 model(s): claude-haiku-4-5-20251001, claude-opus-5
# 4 path(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "GET requests and nothing else. No payload is sent anywhere, no tokens are counted, and the counting endpoint is not involved: this note is one integer from your configuration against one integer on the model resource. Six pure functions &mdash; the argument parser for the shorthand form, the two field readers, the effective cap that combines the model with the endpoint and its beta header, the verdict with its separate state for a value sitting exactly on the ceiling, and the grouping that finds one number shared across two model tiers before the next swap makes it a 400.",
"py_file": "anthropic_max_tokens_cap.py",
"py": '''"""Compare each configured max_tokens against the model's own published cap.

Read only. GET requests and nothing else: give this a workspace API key. No
payload is ever sent, no tokens are counted, and /v1/messages is never called.
The repair is printed, because choosing an output budget is a judgement about
your product and not a side effect of an audit.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_max_tokens_cap")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The Batch API raises the output ceiling on the 1M-context models, and only
# behind this header. A batch path that does not send it is capped exactly as a
# synchronous one, which is why the header is an input to the check rather than
# an assumption.
BATCH_300K_BETA = "output-300k-2026-03-24"
BATCH_MAX_TOKENS = 300_000
LONG_CONTEXT_WINDOW = 1_000_000

FINDINGS = ("above-cap", "below-minimum", "cap-unknown", "model-not-found")


def parse_path(spec):
    """Read a NAME=MODEL:MAX_TOKENS argument. Pure. (name, entry) or None."""
    text = str(spec or "").strip()
    if "=" not in text:
        return None
    name, rest = text.split("=", 1)
    if ":" not in rest:
        return None
    model, value = rest.rsplit(":", 1)
    try:
        configured = int(value)
    except (TypeError, ValueError):
        return None
    name, model = name.strip(), model.strip()
    if not name or not model:
        return None
    return (name, {"model": model, "max_tokens": configured, "endpoint": "messages"})


def sync_cap(model_obj):
    """The model object's own max_tokens field. Pure. None if absent.

    This is the source of truth. The published table lags a release and a
    constant in your source lags the table, so a missing field is reported as
    missing rather than filled in from either.
    """
    if not isinstance(model_obj, dict):
        return None
    value = model_obj.get("max_tokens")
    return value if isinstance(value, int) and value > 0 else None


def window_of(model_obj):
    """max_input_tokens off a model object. Pure. Used only to size the batch
    ceiling, which applies to the 1M-context models."""
    if not isinstance(model_obj, dict):
        return None
    value = model_obj.get("max_input_tokens")
    return value if isinstance(value, int) and value > 0 else None


def effective_cap(model_obj, endpoint="messages", betas=()):
    """The legal ceiling for max_tokens on one model at one endpoint. Pure.

    Two inputs, because the ceiling belongs to the pair and not to the model.
    A batch path with the output-300k header on a 1M-context model gets the
    higher number; the same path without the header does not, and neither does
    a 200k-context model that has it.
    """
    cap = sync_cap(model_obj)
    if cap is None:
        return (None, "the model object carried no max_tokens field")
    if str(endpoint) == "batches" and BATCH_300K_BETA in set(betas or ()):
        window = window_of(model_obj)
        if window is not None and window >= LONG_CONTEXT_WINDOW:
            return (BATCH_MAX_TOKENS, "the Batch API with " + BATCH_300K_BETA)
        return (cap, "the model object; the 300K batch ceiling needs a "
                     "1M context model")
    return (cap, "the model object")


def verdict(configured, cap):
    """Classify one configured value against one cap. Pure. (state, detail)."""
    configured = int(configured or 0)
    if configured < 1:
        return ("below-minimum",
                "max_tokens is %d, and the minimum accepted value is 1"
                % configured)
    if cap is None:
        return ("cap-unknown",
                "max_tokens is %d and no ceiling could be read for this model "
                "and endpoint" % configured)
    if configured > cap:
        return ("above-cap",
                "max_tokens is %d against a cap of %d, which is a 400 "
                "invalid_request_error on every call, %d over"
                % (configured, cap, configured - cap))
    if configured == cap:
        return ("at-cap",
                "max_tokens is %d, exactly the cap, so any move to a smaller "
                "model breaks this path" % configured)
    return ("within-cap",
            "max_tokens is %d of a %d cap (%.0f%%)"
            % (configured, cap, configured / float(cap) * 100))


def tier_spans(rows):
    """One configured value reused across models with different ceilings. Pure.

    rows: [(name, model_id, configured, cap)]. Returns [(value, [model ids])].

    The number appears once in the source, so nothing at any call site says
    that its effective ceiling is the smallest cap among the models using it.
    That is the finding even on the day every path still passes, because the
    next model swap is the one that turns it into a 400.
    """
    by_value = {}
    for name, model, configured, cap in rows or []:
        by_value.setdefault(int(configured or 0), []).append((name, model, cap))
    out = []
    for value in sorted(by_value):
        entries = by_value[value]
        models = sorted({m for _n, m, _c in entries})
        if len(models) < 2:
            continue
        out.append((value, models))
    return out


def get_model(session, model_id):
    """One GET per distinct model id. A 404 here belongs to a different note."""
    r = session.get(API + "/models/" + str(model_id), timeout=30)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY has to be a "
                         "workspace key" % r.status_code)
    r.raise_for_status()
    return r.json()


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", help="JSON file of call paths: "
                                     '{"name": {"model": ..., "max_tokens": ..., '
                                     '"endpoint": "messages|batches", "betas": []}}')
    ap.add_argument("--path", action="append", default=[], metavar="NAME=MODEL:MAX",
                    help="one call path in shorthand, repeatable")
    ap.add_argument("--show-all", action="store_true",
                    help="also print paths comfortably under their cap")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key")
        return 2

    paths = dict(load_config(args.config)) if args.config else {}
    for spec in args.path:
        parsed = parse_path(spec)
        if parsed is None:
            log.error("cannot read --path %r, expected NAME=MODEL:MAX_TOKENS", spec)
            return 2
        paths[parsed[0]] = parsed[1]
    if not paths:
        log.error("give --config FILE or at least one --path NAME=MODEL:MAX_TOKENS")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    models = {}
    rows = []
    bad = 0

    for name in sorted(paths):
        entry = paths[name] or {}
        model_id = str(entry.get("model") or "")
        configured = entry.get("max_tokens")
        endpoint = entry.get("endpoint") or "messages"
        betas = entry.get("betas") or []

        if model_id not in models:
            models[model_id] = get_model(session, model_id)
        model_obj = models[model_id]
        if model_obj is None:
            bad += 1
            log.warning("%-14s %-16s %-28s the model id is not in the live list "
                        "at all, which is a retirement or a typo rather than a "
                        "max_tokens problem", "model-not-found", name, model_id)
            continue

        cap, source = effective_cap(model_obj, endpoint, betas)
        state, detail = verdict(configured, cap)
        rows.append((name, model_id, int(configured or 0), cap))

        line = "%-14s %-16s %-28s %s" % (state, name, model_id, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            log.warning("  ceiling read from %s", source)
        elif state == "at-cap":
            log.warning(line)
        elif args.show_all:
            log.info(line)

    for value, shared in tier_spans(rows):
        caps = [cap for _n, _m, configured, cap in rows
                if configured == value and cap is not None]
        note = "shared value %d is configured on %d model(s): %s" % (
            value, len(shared), ", ".join(shared))
        if caps and min(caps) < value:
            bad += 1
            log.warning("%-14s %s, and the smallest cap among them is %d",
                        "spans-tiers", note, min(caps))
        else:
            log.info("  %s, so the effective ceiling is the smallest of their "
                     "caps whether or not anything says so", note)

    if bad:
        log.warning("  repair: set each path's max_tokens from the cap the "
                    "Models API reports for its own model, not from a shared "
                    "constant and not from the docs table, which lags. Note "
                    "that maxing it out trades a 400 for truncated answers and "
                    "long non-streaming requests. Printed, not applied.")

    log.info("%d path(s) checked, %d finding(s)", len(paths), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-max-tokens-cap.mjs",
"js": '''/**
 * Compare each configured max_tokens against the model's own published cap.
 *
 * Read only. GET requests and nothing else: give this a workspace API key. No
 * payload is ever sent, no tokens are counted, and /v1/messages is never
 * called. The repair is printed.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const BATCH_300K_BETA = 'output-300k-2026-03-24';
const BATCH_MAX_TOKENS = 300000;
const LONG_CONTEXT_WINDOW = 1000000;

const FINDINGS = new Set(['above-cap', 'below-minimum', 'cap-unknown', 'model-not-found']);

/** Read a NAME=MODEL:MAX_TOKENS argument. Pure. [name, entry] or null. */
export function parsePath(spec) {
  const text = String(spec ?? '').trim();
  const eq = text.indexOf('=');
  if (eq < 0) return null;
  const name = text.slice(0, eq).trim();
  const rest = text.slice(eq + 1);
  const colon = rest.lastIndexOf(':');
  if (colon < 0) return null;
  const model = rest.slice(0, colon).trim();
  const value = rest.slice(colon + 1).trim();
  if (!name || !model || !/^-?[0-9]+$/.test(value)) return null;
  return [name, { model, max_tokens: Number(value), endpoint: 'messages' }];
}

/** The model object's own max_tokens field. Pure. null if absent. */
export function syncCap(modelObj) {
  if (!modelObj || typeof modelObj !== 'object') return null;
  const value = modelObj.max_tokens;
  return Number.isInteger(value) && value > 0 ? value : null;
}

/** max_input_tokens off a model object. Pure. Sizes the batch ceiling only. */
export function windowOf(modelObj) {
  if (!modelObj || typeof modelObj !== 'object') return null;
  const value = modelObj.max_input_tokens;
  return Number.isInteger(value) && value > 0 ? value : null;
}

/**
 * The legal ceiling for max_tokens on one model at one endpoint. Pure.
 * The ceiling belongs to the pair: a batch path with the output-300k header on
 * a 1M-context model gets the higher number and nothing else does.
 */
export function effectiveCap(modelObj, endpoint = 'messages', betas = []) {
  const cap = syncCap(modelObj);
  if (cap === null) return [null, 'the model object carried no max_tokens field'];
  if (String(endpoint) === 'batches' && new Set(betas ?? []).has(BATCH_300K_BETA)) {
    const window = windowOf(modelObj);
    if (window !== null && window >= LONG_CONTEXT_WINDOW) {
      return [BATCH_MAX_TOKENS, `the Batch API with ${BATCH_300K_BETA}`];
    }
    return [cap, 'the model object; the 300K batch ceiling needs a 1M context model'];
  }
  return [cap, 'the model object'];
}

/** Classify one configured value against one cap. Pure. [state, detail]. */
export function verdict(configured, cap) {
  const value = Math.trunc(configured || 0);
  if (value < 1) {
    return ['below-minimum',
      `max_tokens is ${value}, and the minimum accepted value is 1`];
  }
  if (cap === null || cap === undefined) {
    return ['cap-unknown',
      `max_tokens is ${value} and no ceiling could be read for this model and endpoint`];
  }
  if (value > cap) {
    return ['above-cap',
      `max_tokens is ${value} against a cap of ${cap}, which is a 400 ` +
      `invalid_request_error on every call, ${value - cap} over`];
  }
  if (value === cap) {
    return ['at-cap',
      `max_tokens is ${value}, exactly the cap, so any move to a smaller model ` +
      'breaks this path'];
  }
  return ['within-cap',
    `max_tokens is ${value} of a ${cap} cap (${(value / cap * 100).toFixed(0)}%)`];
}

/**
 * One configured value reused across models with different ceilings. Pure.
 * rows: [[name, modelId, configured, cap]]. Returns [[value, [modelIds]]].
 */
export function tierSpans(rows) {
  const byValue = new Map();
  for (const [name, model, configured, cap] of rows ?? []) {
    const value = Math.trunc(configured || 0);
    if (!byValue.has(value)) byValue.set(value, []);
    byValue.get(value).push([name, model, cap]);
  }
  const out = [];
  for (const value of [...byValue.keys()].sort((a, b) => a - b)) {
    const models = [...new Set(byValue.get(value).map(([, m]) => m))].sort();
    if (models.length < 2) continue;
    out.push([value, models]);
  }
  return out;
}

async function getModel(key, modelId) {
  const res = await fetch(`${API}/models/${modelId}`, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY has to be a workspace key`);
  }
  if (!res.ok) throw new Error(`${res.status} from /models/${modelId}`);
  return res.json();
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key');
    process.exitCode = 2;
    return;
  }
  const paths = {};
  if (process.env.CONFIG) Object.assign(paths, JSON.parse(await readFile(process.env.CONFIG, 'utf8')));
  for (const spec of process.argv.slice(2).filter((a) => !a.startsWith('--'))) {
    const parsed = parsePath(spec);
    if (!parsed) {
      console.error(`cannot read '${spec}', expected NAME=MODEL:MAX_TOKENS`);
      process.exitCode = 2;
      return;
    }
    paths[parsed[0]] = parsed[1];
  }
  if (Object.keys(paths).length === 0) {
    console.error('set CONFIG to a JSON file, or pass NAME=MODEL:MAX_TOKENS arguments');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';

  const models = new Map();
  const rows = [];
  let bad = 0;

  for (const name of Object.keys(paths).sort()) {
    const entry = paths[name] ?? {};
    const modelId = String(entry.model ?? '');
    const endpoint = entry.endpoint ?? 'messages';
    const betas = entry.betas ?? [];

    if (!models.has(modelId)) models.set(modelId, await getModel(key, modelId));
    const modelObj = models.get(modelId);
    if (modelObj === null) {
      bad += 1;
      console.warn(`${'model-not-found'.padEnd(14)} ${name.padEnd(16)} ` +
                   `${modelId.padEnd(28)} the model id is not in the live list at ` +
                   'all, which is a retirement or a typo rather than a max_tokens problem');
      continue;
    }

    const [cap, source] = effectiveCap(modelObj, endpoint, betas);
    const [state, detail] = verdict(entry.max_tokens, cap);
    rows.push([name, modelId, Math.trunc(entry.max_tokens || 0), cap]);

    const line = `${state.padEnd(14)} ${name.padEnd(16)} ${modelId.padEnd(28)} ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      console.warn(`  ceiling read from ${source}`);
    } else if (state === 'at-cap') {
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  for (const [value, shared] of tierSpans(rows)) {
    const caps = rows.filter(([, , configured, cap]) => configured === value && cap !== null)
      .map(([, , , cap]) => cap);
    const note = `shared value ${value} is configured on ${shared.length} model(s): ` +
                 shared.join(', ');
    if (caps.length && Math.min(...caps) < value) {
      bad += 1;
      console.warn(`${'spans-tiers'.padEnd(14)} ${note}, and the smallest cap ` +
                   `among them is ${Math.min(...caps)}`);
    } else {
      console.log(`  ${note}, so the effective ceiling is the smallest of their ` +
                  'caps whether or not anything says so');
    }
  }

  if (bad) {
    console.warn('  repair: set each path\\'s max_tokens from the cap the Models API ' +
                 'reports for its own model, not from a shared constant and not from ' +
                 'the docs table, which lags. Note that maxing it out trades a 400 for ' +
                 'truncated answers and long non-streaming requests. Printed, not applied.');
  }

  console.log(`${Object.keys(paths).length} path(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the Friday afternoon in the opening paragraph: 128,000 is a legal value on Sonnet 5 and sixty-four thousand tokens over the ceiling on Haiku 4.5, and the same shared number is what put it there. The second is the pair the docs table cannot express &mdash; the batch ceiling is a property of the model <em>and</em> the endpoint <em>and</em> the beta header, so all three combinations have to come out differently. The rest hold the states that stop the report being wrong in a quiet direction: a model object with no cap must not read as unlimited, a value sitting exactly on the ceiling is its own warning, and one number shared across two tiers is reported before anything has failed.",
"test_py_file": "test_anthropic_max_tokens_cap.py",
"test_py": '''from anthropic_max_tokens_cap import (effective_cap, parse_path, sync_cap,
                                       tier_spans, verdict, window_of)

SONNET = {"id": "claude-sonnet-5", "max_tokens": 128_000,
          "max_input_tokens": 1_000_000}
HAIKU = {"id": "claude-haiku-4-5-20251001", "max_tokens": 64_000,
         "max_input_tokens": 200_000}


def test_the_same_value_is_legal_on_one_model_and_a_400_on_the_other():
    # The whole note. One shared constant, two tiers, one of them rejected on
    # every call from the first one.
    assert verdict(128_000, effective_cap(SONNET)[0])[0] == "at-cap"
    state, detail = verdict(128_000, effective_cap(HAIKU)[0])
    assert state == "above-cap"
    assert "against a cap of 64000" in detail
    assert "64000 over" in detail
    assert "400" in detail


def test_the_batch_ceiling_needs_the_endpoint_and_the_header_and_the_window():
    # Three inputs, and dropping any one of them gives the wrong ceiling.
    cap, source = effective_cap(SONNET, "batches", ["output-300k-2026-03-24"])
    assert (cap, "output-300k-2026-03-24" in source) == (300_000, True)
    # Same model, same header, synchronous endpoint: the model object wins.
    assert effective_cap(SONNET, "messages", ["output-300k-2026-03-24"])[0] == 128_000
    # Same model, batch endpoint, header not sent: the model object again.
    assert effective_cap(SONNET, "batches", [])[0] == 128_000
    # Header sent on a 200k-context model: it does not qualify.
    cap, source = effective_cap(HAIKU, "batches", ["output-300k-2026-03-24"])
    assert cap == 64_000
    assert "1M context model" in source


def test_a_model_object_with_no_cap_is_not_an_unlimited_one():
    assert sync_cap({"id": "claude-sonnet-5"}) is None
    assert sync_cap({"max_tokens": 0}) is None
    assert sync_cap({"max_tokens": "128000"}) is None
    assert sync_cap(None) is None
    assert window_of(HAIKU) == 200_000
    assert window_of({}) is None
    state, detail = verdict(128_000, effective_cap({"id": "x"})[0])
    assert state == "cap-unknown"
    assert "no ceiling could be read" in detail


def test_the_floor_is_one_and_it_is_a_different_finding():
    assert verdict(0, 128_000)[0] == "below-minimum"
    assert verdict(-1, 128_000)[0] == "below-minimum"
    assert verdict(1, 128_000)[0] == "within-cap"


def test_a_value_sitting_exactly_on_the_ceiling_is_its_own_warning():
    state, detail = verdict(64_000, 64_000)
    assert state == "at-cap"
    assert "any move to a smaller model breaks this path" in detail
    assert verdict(16_000, 64_000) == (
        "within-cap", "max_tokens is 16000 of a 64000 cap (25%)")


def test_one_number_shared_across_two_tiers_is_reported_before_it_breaks():
    rows = [("reports", "claude-opus-5", 64_000, 128_000),
            ("classifier", "claude-haiku-4-5-20251001", 64_000, 64_000),
            ("summaries", "claude-sonnet-5", 8_000, 128_000)]
    # 64000 passes on both today, and it is still the number the next model
    # swap turns into a 400, so it is named.
    assert tier_spans(rows) == [(64_000, ["claude-haiku-4-5-20251001",
                                          "claude-opus-5"])]
    # A value used by one model only is not a span.
    assert tier_spans(rows[2:]) == []
    assert tier_spans([]) == []
    assert tier_spans(None) == []


def test_the_shorthand_argument_parses_model_ids_that_contain_no_colon():
    assert parse_path("classifier=claude-haiku-4-5-20251001:64000") == (
        "classifier", {"model": "claude-haiku-4-5-20251001",
                       "max_tokens": 64000, "endpoint": "messages"})
    assert parse_path("reports=claude-opus-5:128000")[1]["max_tokens"] == 128000
    assert parse_path("no-colon=claude-opus-5") is None
    assert parse_path("claude-opus-5:128000") is None
    assert parse_path("reports=claude-opus-5:lots") is None
    assert parse_path("") is None
    assert parse_path(None) is None
''',
"test_js_file": "anthropic-max-tokens-cap.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { effectiveCap, parsePath, syncCap, tierSpans, verdict, windowOf }
  from './anthropic-max-tokens-cap.mjs';

const SONNET = { id: 'claude-sonnet-5', max_tokens: 128000, max_input_tokens: 1000000 };
const HAIKU = { id: 'claude-haiku-4-5-20251001', max_tokens: 64000, max_input_tokens: 200000 };

test('the same value is legal on one model and a 400 on the other', () => {
  assert.equal(verdict(128000, effectiveCap(SONNET)[0])[0], 'at-cap');
  const [state, detail] = verdict(128000, effectiveCap(HAIKU)[0]);
  assert.equal(state, 'above-cap');
  assert.match(detail, /against a cap of 64000/);
  assert.match(detail, /64000 over/);
  assert.match(detail, /400/);
});

test('the batch ceiling needs the endpoint and the header and the window', () => {
  const [cap, source] = effectiveCap(SONNET, 'batches', ['output-300k-2026-03-24']);
  assert.equal(cap, 300000);
  assert.match(source, /output-300k-2026-03-24/);
  assert.equal(effectiveCap(SONNET, 'messages', ['output-300k-2026-03-24'])[0], 128000);
  assert.equal(effectiveCap(SONNET, 'batches', [])[0], 128000);
  const [haikuCap, haikuSource] = effectiveCap(HAIKU, 'batches', ['output-300k-2026-03-24']);
  assert.equal(haikuCap, 64000);
  assert.match(haikuSource, /1M context model/);
});

test('a model object with no cap is not an unlimited one', () => {
  assert.equal(syncCap({ id: 'claude-sonnet-5' }), null);
  assert.equal(syncCap({ max_tokens: 0 }), null);
  assert.equal(syncCap({ max_tokens: '128000' }), null);
  assert.equal(syncCap(null), null);
  assert.equal(windowOf(HAIKU), 200000);
  assert.equal(windowOf({}), null);
  const [state, detail] = verdict(128000, effectiveCap({ id: 'x' })[0]);
  assert.equal(state, 'cap-unknown');
  assert.match(detail, /no ceiling could be read/);
});

test('the floor is one and it is a different finding', () => {
  assert.equal(verdict(0, 128000)[0], 'below-minimum');
  assert.equal(verdict(-1, 128000)[0], 'below-minimum');
  assert.equal(verdict(1, 128000)[0], 'within-cap');
});

test('a value sitting exactly on the ceiling is its own warning', () => {
  const [state, detail] = verdict(64000, 64000);
  assert.equal(state, 'at-cap');
  assert.match(detail, /any move to a smaller model breaks this path/);
  assert.deepEqual(verdict(16000, 64000),
    ['within-cap', 'max_tokens is 16000 of a 64000 cap (25%)']);
});

test('one number shared across two tiers is reported before it breaks', () => {
  const rows = [['reports', 'claude-opus-5', 64000, 128000],
                ['classifier', 'claude-haiku-4-5-20251001', 64000, 64000],
                ['summaries', 'claude-sonnet-5', 8000, 128000]];
  assert.deepEqual(tierSpans(rows),
    [[64000, ['claude-haiku-4-5-20251001', 'claude-opus-5']]]);
  assert.deepEqual(tierSpans(rows.slice(2)), []);
  assert.deepEqual(tierSpans([]), []);
  assert.deepEqual(tierSpans(null), []);
});

test('the shorthand argument parses model ids that contain no colon', () => {
  assert.deepEqual(parsePath('classifier=claude-haiku-4-5-20251001:64000'),
    ['classifier', { model: 'claude-haiku-4-5-20251001', max_tokens: 64000,
                     endpoint: 'messages' }]);
  assert.equal(parsePath('reports=claude-opus-5:128000')[1].max_tokens, 128000);
  assert.equal(parsePath('no-colon=claude-opus-5'), null);
  assert.equal(parsePath('claude-opus-5:128000'), null);
  assert.equal(parsePath('reports=claude-opus-5:lots'), null);
  assert.equal(parsePath(''), null);
  assert.equal(parsePath(null), null);
});
''',
"faq": [
 ("Why not just read the cap from the documentation?",
  "Because the table lags and your copy of it lags further. The model object carries the ceiling as a field, versioned with the model itself, so it is correct on the day a new model ships and a wiki page is not. It is one GET per distinct model id and it removes an entire class of stale-constant bug."),
 ("Should I just set max_tokens to the model's maximum?",
  "No. It is a hard cutoff the model cannot see, not a budget it paces itself against, so a very large value does not make answers better. It makes truncation more likely to happen late instead of early, and on a non-streaming path it pushes you towards the ten-minute request timeout. Around 16,000 is a sane synchronous default and 256 is only for genuine classification."),
 ("My batch config uses 300,000 and the checker says it is over.",
  "Then one of the three conditions is missing. The 300K ceiling applies on the Batch API only, only on the 1M-context models, and only when the output-300k-2026-03-24 beta header is actually sent. Drop any one of those and the ceiling falls back to the model object's own number, which is 128K on the current large models."),
 ("The model id returns 404. Is that this problem?",
  "No, and the script says so rather than guessing. A 404 from the model endpoint means the id is retired or mistyped, which fails every call for an unrelated reason and has an unrelated repair: diffing your config strings against the live model list. That is the retired-model-id note, not this one."),
 ("Every path passes today. Why is it still flagging a shared value?",
  "Because the number appears once in the source and its effective ceiling is the smallest cap among every model that uses it, and nothing at any call site records that. Reporting it while it still passes is the only moment the fix is cheap; after the next model swap it is an incident with a very obvious cause and a very unhappy afternoon."),
],
"related": [REL_RETIRED, REL_WALL, REL_OUTPUT_COST],
"citations": [CITE_CL_MODELS, CITE_CL_OVERVIEW, CITE_CL_BATCHES, CITE_CL_ERRORS],
},
{
"slug": "non-streaming-request-over-ten-minutes",
"title": "A non-streaming request over 10 minutes times out with 504",
"description": "Not a size problem. A large max_tokens on a non-streaming path runs past a wall clock, and the repair is streaming rather than a shorter prompt.",
"h1": "A non-streaming request over 10 minutes times out with 504",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic 504 timeout_error", "claude 10 minute request limit",
             "claude streaming long running request", "anthropic sdk timeout milliseconds",
             "claude max_tokens 128000 non streaming"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key. GET requests plus the free count_tokens pre-flight.",
"lead": "The prompt is two thousand tokens. The context window is nowhere near full. Nothing is too large by any measure anybody in the room has checked, and the request still dies &mdash; sometimes as <code>504</code> with <code>timeout_error</code>, more often as nothing at all, because a load balancer somewhere between you and Anthropic closed an idle connection while the model was still writing. The ceiling this hit is a clock.",
"short_answer": """<p>Estimate the time, not the size. Generation runs at roughly fifty to sixty output tokens a second, so <code>max_tokens</code> divided by that rate is how long the call takes. A non-streaming request is documented not to run past <strong>10 minutes</strong>, and the current large models allow <strong>128,000</strong> output tokens &mdash; which at that rate is nearly forty minutes on a single call.</p>
<p>At about fifty-five tokens a second the largest <code>max_tokens</code> that can finish inside ten minutes is roughly <strong>33,000</strong>. Anything above that on a non-streaming path is a timeout waiting for a verbose answer.</p>
<p><strong>The fix is streaming, not a smaller prompt.</strong> <code>.stream()</code> followed by <code>.get_final_message()</code> hands you the identical <code>Message</code> object with no event handling, and the connection never goes idle. For anything latency-tolerant, the Message Batches API removes the clock entirely.</p>""",
"problem": """<p>Every other ceiling in this section is a size. This one is a duration, and duration is the dimension nobody instruments, because it is not in the request and it is not in the usage report. The request that fails is not big. It asked for a long answer, the model obliged, and the answer took longer than the connection was allowed to stay open.</p>
<p>The failure mode is unusually unhelpful. Sometimes it is a clean <code>504</code> with <code>"type": "timeout_error"</code>. Often it is worse: no response at all, because an intermediate hop &mdash; a corporate proxy, a cloud load balancer, an ingress with a sixty-second idle timeout &mdash; dropped the connection before Anthropic answered. Then your client raises a connection error, which reads like a network fault, which is triaged as a network fault, and the network is fine.</p>
<p>Then the wrong repair gets applied. Somebody raises the client timeout, which changes nothing, because the ceiling is not the client's. Somebody shortens the prompt, which changes nothing, because the input side was never the problem. The SDKs actually guard against this &mdash; they validate that a non-streaming Messages request is not expected to exceed ten minutes and refuse the combination &mdash; but a raw HTTP client, a proxy layer or a homegrown wrapper has no such check, and those are exactly the places long-running calls end up.</p>""",
"why": """<p><strong>The clock is a property of the answer, not of the question.</strong> A two-thousand-token prompt with <code>max_tokens: 64000</code> takes twenty minutes to generate and a sixty-thousand-token prompt with <code>max_tokens: 1024</code> takes about twenty seconds. Every intuition built on prompt size points the wrong way here, which is why this note estimates seconds and reports seconds.</p>
<p><strong>Thinking tokens are output tokens, so they are on the clock too.</strong> Extended thinking is generated, billed and timed like anything else the model writes. Raising an effort setting is a change to how long every request takes, made in a config file, with no diff anywhere near the timeout.</p>
<p><strong>Client timeout units genuinely differ between SDKs, and the mistake is silent.</strong> Python and Ruby take seconds. The TypeScript client takes <strong>milliseconds</strong>. Go takes a <code>time.Duration</code>, Java a <code>Duration</code>, C# a <code>TimeSpan</code>. A <code>600</code> copied from a Python example into a TypeScript constructor is six hundred milliseconds, and it produces a timeout on nearly every call that gets blamed on the API.</p>
<p><strong>Streaming does not make it faster. It makes the connection busy.</strong> The same tokens are generated at the same rate; the difference is that bytes are arriving continuously, so nothing between you and the API decides the connection is idle. That is the entire mechanism, and it is why the repair here is a transport change rather than a size change.</p>
<p><strong>This is not the model's cap.</strong> A <code>max_tokens</code> the model refuses outright is <a href="/llm/max-tokens-above-model-cap/">a different note</a> and a 400 during validation. Here the value is perfectly legal &mdash; that is the problem. The model will happily accept a request for 128,000 tokens and then spend forty minutes trying to deliver them.</p>""",
"steps": [
 {"h": "List the call paths with their transport, not just their parameters",
  "body": """<p>The tuple that matters is <em>(model, max_tokens, streams or does not, client timeout, SDK)</em>. The transport is the field people leave out of configuration entirely, because it is expressed in code as a different method call rather than as a setting, and it is the field that decides whether the ceiling applies.</p>"""},
 {"h": "Estimate generation time from max_tokens",
  "body": """<p><code>max_tokens</code> divided by your observed output rate. Fifty-five tokens a second is a reasonable starting figure; measure your own from a handful of real responses and use that instead. Add prefill, which is fast &mdash; thousands of tokens a second &mdash; and matters only on genuinely enormous inputs.</p>"""},
 {"h": "Size the input side for free",
  "body": """<p><code>POST /v1/messages/count_tokens</code> gives you the input token count at no cost, and here it is being used to convert into seconds rather than to check a window. Prefill is usually a small share of the total, and the check is worth doing precisely so you can prove that and stop shortening prompts to fix a timeout.</p>"""},
 {"h": "Convert the client timeout into seconds before comparing it",
  "body": """<p>Python and Ruby take seconds; TypeScript takes milliseconds; Go, Java and C# take duration types. Normalise before comparing, and flag anything under a second on a millisecond SDK as a copied number rather than a chosen one. Then note that a client timeout above ten minutes on a non-streaming path buys nothing at all.</p>"""},
 {"h": "Print the transport change, do not make it",
  "body": """<p>For each path over the line: stream it, with <code>.stream()</code> and <code>.get_final_message()</code> in Python or <code>.finalMessage()</code> in TypeScript, which returns the same <code>Message</code> object and needs no event handling. For anything nobody is waiting on, the Message Batches API. For direct HTTP integrations, TCP keep-alive so the intermediate hops stop killing the socket. Switching a production call path to streaming changes error handling and back-pressure, so it is printed.</p>"""},
],
"verify": """<p>Re-run after the change. Streaming paths should report comfortably, and any remaining non-streaming path should sit well under ten minutes at your measured rate.</p>
<pre><code class="language-bash">python3 anthropic_wall_clock_preflight.py --config call-paths.json --tps 55
# over-wall-clock-not-streaming  report-writer  19m 23s of generation estimated on a non-streaming path, past the 10m 00s ceiling. ...
#   at 55 tok/s the largest max_tokens that finishes inside the ceiling is 32,978
#   this model allows 128000 output tokens, which is 38m 47s on one call
# timeout-unit-mistake           report-writer  timeout 600 on the typescript client is 0.6s, not 10 minutes
# 3 path(s) checked, 2 finding(s)</code></pre>""",
"code_intro": "Seconds throughout. One GET per model for the cap, and one free <code>count_tokens</code> call per path that names a payload &mdash; used here to turn the input into prefill seconds rather than to check it against anything. Seven pure functions and none of them compares a size to a ceiling: the two rate conversions, the timeout normaliser that knows Python takes seconds and TypeScript takes milliseconds, the suspicion check for a number copied between them, the largest <code>max_tokens</code> that still finishes in time, the duration formatter, and a verdict that puts the wall clock ahead of the client timeout because raising the client timeout is the repair that does not work.",
"py_file": "anthropic_wall_clock_preflight.py",
"py": '''"""Estimate whether a non-streaming Claude call can finish inside 10 minutes.

Read only, with one deliberate exception. Nothing here creates a completion:
where a call path names a payload file, that body goes to
/v1/messages/count_tokens, which is free, creates no object, generates no
output and is not billed. It is used to turn the input into prefill seconds.
Everything else is a GET, and /v1/messages is never called.

The repair is a transport change and it is printed. Moving a production call
path onto streaming changes error handling and back pressure, which is a
decision, not an audit's side effect.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_wall_clock_preflight")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The documented ceiling for a single non-streaming Messages request.
WALL_CLOCK = 600.0

# Starting figures, both meant to be replaced with your own measurements.
# Generation is the one that decides the answer; prefill is fast enough that it
# only matters on very large inputs, and proving that is half the point.
DEFAULT_TPS = 55.0
DEFAULT_PREFILL_TPS = 6000.0

# Client timeouts are not expressed in the same unit across SDKs, and a number
# copied from one language's example into another's constructor is the quiet
# half of this note.
SDK_TIMEOUT_UNITS = {
    "python": ("seconds", 1.0),
    "ruby": ("seconds", 1.0),
    "php": ("seconds", 1.0),
    "typescript": ("milliseconds", 0.001),
    "javascript": ("milliseconds", 0.001),
    "node": ("milliseconds", 0.001),
    "go": ("a time.Duration", 1.0),
    "java": ("a Duration", 1.0),
    "csharp": ("a TimeSpan", 1.0),
}
MILLISECOND_SDKS = ("typescript", "javascript", "node")

SAMPLING_ONLY = ("max_tokens", "stream", "temperature", "top_p", "top_k",
                 "stop_sequences", "metadata", "service_tier")

FINDINGS = ("over-wall-clock-not-streaming", "over-client-timeout",
            "near-wall-clock-not-streaming")


def duration(seconds):
    """Seconds as minutes and seconds. Pure."""
    total = int(max(0.0, float(seconds or 0)))
    return "%dm %02ds" % (total // 60, total % 60)


def generation_seconds(max_tokens, tps=DEFAULT_TPS):
    """How long it takes to write max_tokens output tokens. Pure.

    This is the number the whole note turns on, and it has nothing to do with
    the size of the prompt. Thinking tokens are output tokens, so an effort
    setting moves it too.
    """
    rate = float(tps or 0)
    if rate <= 0:
        return 0.0
    return max(0, int(max_tokens or 0)) / rate


def prefill_seconds(input_tokens, prefill_tps=DEFAULT_PREFILL_TPS):
    """How long it takes to read the input. Pure.

    Kept separate and reported separately because it is almost always small,
    and the point of measuring it is to stop people shortening prompts to fix a
    problem that lives entirely on the output side.
    """
    rate = float(prefill_tps or 0)
    if rate <= 0:
        return 0.0
    return max(0, int(input_tokens or 0)) / rate


def timeout_seconds(sdk, value):
    """A client timeout in seconds, whatever unit the SDK takes. Pure.

    None when the SDK is unknown, because guessing the unit is precisely the
    mistake this function exists to catch.
    """
    if value is None:
        return None
    unit = SDK_TIMEOUT_UNITS.get(str(sdk or "").strip().lower())
    if unit is None:
        return None
    try:
        return float(value) * unit[1]
    except (TypeError, ValueError):
        return None


def unit_suspicion(sdk, value):
    """True when a timeout looks written in the wrong unit. Pure.

    600 in the TypeScript client is six hundred milliseconds, not ten minutes.
    Nobody chooses a sub-second timeout for an LLM call on purpose, so anything
    under a second on a millisecond SDK is a number copied from a seconds-based
    example.
    """
    seconds = timeout_seconds(sdk, value)
    if seconds is None:
        return False
    return str(sdk or "").strip().lower() in MILLISECOND_SDKS and seconds < 1.0


def safe_max_tokens(tps=DEFAULT_TPS, wall_clock=WALL_CLOCK, prefill=0.0):
    """The largest max_tokens that still finishes inside the ceiling. Pure.

    The number to put in the config, as opposed to the model's cap, which is
    the number that fits in the request.
    """
    rate = float(tps or 0)
    room = max(0.0, float(wall_clock or 0) - max(0.0, float(prefill or 0)))
    if rate <= 0:
        return 0
    return int(room * rate)


def verdict(seconds, streams, timeout_s=None, wall_clock=WALL_CLOCK, near=0.8):
    """Classify one call path against the clock. Pure. (state, detail).

    Order matters. The wall clock is checked before the client timeout, because
    a non-streaming request past ten minutes fails on the far side whatever the
    client is configured to wait for, and raising the client timeout is both
    the first repair people reach for and the one that does nothing.
    """
    shape = "%s of generation estimated" % duration(seconds)

    if not streams and seconds > wall_clock:
        return ("over-wall-clock-not-streaming",
                "%s on a non-streaming path, past the %s ceiling. That is a 504 "
                "timeout_error, or no response at all when an intermediate hop "
                "drops the idle connection first. Raising the client timeout "
                "does not move it." % (shape, duration(wall_clock)))
    if timeout_s is not None and seconds > timeout_s:
        return ("over-client-timeout",
                "%s against a client timeout of %s, so the client gives up "
                "before the API is finished." % (shape, duration(timeout_s)))
    if not streams and seconds >= wall_clock * near:
        return ("near-wall-clock-not-streaming",
                "%s on a non-streaming path, inside %.0f%% of the %s ceiling. "
                "One unusually long answer crosses it."
                % (shape, near * 100, duration(wall_clock)))
    if streams and seconds > wall_clock:
        return ("streams-past-ten-minutes",
                "%s, and the path streams, so the connection never goes idle "
                "and the ceiling does not apply. Worth the Message Batches API "
                "if nobody is waiting on it." % shape)
    return ("within-budget", "%s." % shape)


def get(session, path):
    r = session.get(API + path, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY has to be a "
                         "workspace key" % r.status_code)
    r.raise_for_status()
    return r.json()


def count_input(session, payload_path):
    """The one non-GET call, and it neither creates nor bills anything.

    The counting endpoint returns an input_tokens number for free. Here that
    number is converted straight into seconds of prefill; it is not compared
    against any ceiling, which is a different note.
    """
    with open(payload_path, "r", encoding="utf-8") as fh:
        body = json.load(fh)
    trimmed = {k: v for k, v in body.items() if k not in SAMPLING_ONLY}
    r = session.post(API + "/messages/count_tokens", json=trimmed, timeout=60)
    r.raise_for_status()
    return int((r.json() or {}).get("input_tokens") or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True,
                    help="JSON file of call paths: "
                         '{"name": {"model": ..., "max_tokens": ..., '
                         '"stream": false, "sdk": "typescript", '
                         '"timeout": 600, "payload": "body.json"}}')
    ap.add_argument("--tps", type=float, default=DEFAULT_TPS,
                    help="observed output tokens per second (default 55)")
    ap.add_argument("--prefill-tps", type=float, default=DEFAULT_PREFILL_TPS,
                    help="observed input tokens per second (default 6000)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print paths comfortably inside the clock")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key")
        return 2

    with open(args.config, "r", encoding="utf-8") as fh:
        paths = json.load(fh)

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION,
                            "content-type": "application/json"})

    caps = {}
    bad = 0

    for name in sorted(paths):
        entry = paths[name] or {}
        model_id = str(entry.get("model") or "")
        streams = bool(entry.get("stream"))
        sdk = entry.get("sdk")

        if model_id and model_id not in caps:
            caps[model_id] = get(session, "/models/" + model_id).get("max_tokens")

        input_tokens = int(entry.get("input_tokens") or 0)
        if entry.get("payload"):
            input_tokens = count_input(session, entry["payload"])

        prefill = prefill_seconds(input_tokens, args.prefill_tps)
        seconds = prefill + generation_seconds(entry.get("max_tokens"), args.tps)
        client = timeout_seconds(sdk, entry.get("timeout"))

        state, detail = verdict(seconds, streams, client)
        line = "%-30s %-16s %s" % (state, name, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
        elif state == "streams-past-ten-minutes":
            log.info(line)
        elif args.show_all:
            log.info(line)

        if unit_suspicion(sdk, entry.get("timeout")):
            bad += 1
            log.warning("%-30s %-16s timeout %s on the %s client is %.1fs, not "
                        "%s: that unit is milliseconds",
                        "timeout-unit-mistake", name, entry.get("timeout"), sdk,
                        client or 0.0, duration(entry.get("timeout") or 0))

        if state in ("over-wall-clock-not-streaming",
                     "near-wall-clock-not-streaming"):
            log.warning("  at %.0f tok/s the largest max_tokens that finishes "
                        "inside the ceiling is %d",
                        args.tps, safe_max_tokens(args.tps, WALL_CLOCK, prefill))
            cap = caps.get(model_id)
            if cap:
                log.warning("  this model allows %d output tokens, which is %s "
                            "on one call", cap,
                            duration(generation_seconds(cap, args.tps)))
            log.warning("  repair: stream it. .stream() plus "
                        ".get_final_message() returns the identical Message "
                        "object with no event handling, and the connection "
                        "never goes idle. For latency tolerant work use the "
                        "Message Batches API, which has no such clock. Printed, "
                        "not applied.")

    log.info("%d path(s) checked, %d finding(s)", len(paths), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-wall-clock-preflight.mjs",
"js": '''/**
 * Estimate whether a non-streaming Claude call can finish inside 10 minutes.
 *
 * Read only, with one deliberate exception. Nothing here creates a completion:
 * where a call path names a payload file, that body goes to
 * /v1/messages/count_tokens, which is free, creates no object, generates no
 * output and is not billed. It is used to turn the input into prefill seconds.
 * Everything else is a GET, and /v1/messages is never called.
 *
 * The repair is a transport change and it is printed.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const WALL_CLOCK = 600;
const DEFAULT_TPS = 55;
const DEFAULT_PREFILL_TPS = 6000;

const SDK_TIMEOUT_UNITS = {
  python: ['seconds', 1],
  ruby: ['seconds', 1],
  php: ['seconds', 1],
  typescript: ['milliseconds', 0.001],
  javascript: ['milliseconds', 0.001],
  node: ['milliseconds', 0.001],
  go: ['a time.Duration', 1],
  java: ['a Duration', 1],
  csharp: ['a TimeSpan', 1],
};
const MILLISECOND_SDKS = new Set(['typescript', 'javascript', 'node']);

const SAMPLING_ONLY = new Set(['max_tokens', 'stream', 'temperature', 'top_p',
  'top_k', 'stop_sequences', 'metadata', 'service_tier']);

const FINDINGS = new Set(['over-wall-clock-not-streaming', 'over-client-timeout',
  'near-wall-clock-not-streaming']);

/** Seconds as minutes and seconds. Pure. */
export function duration(seconds) {
  const total = Math.trunc(Math.max(0, Number(seconds || 0)));
  return `${Math.floor(total / 60)}m ${String(total % 60).padStart(2, '0')}s`;
}

/** How long it takes to write maxTokens output tokens. Pure. */
export function generationSeconds(maxTokens, tps = DEFAULT_TPS) {
  const rate = Number(tps || 0);
  if (rate <= 0) return 0;
  return Math.max(0, Math.trunc(maxTokens || 0)) / rate;
}

/** How long it takes to read the input. Pure. Reported separately on purpose. */
export function prefillSeconds(inputTokens, prefillTps = DEFAULT_PREFILL_TPS) {
  const rate = Number(prefillTps || 0);
  if (rate <= 0) return 0;
  return Math.max(0, Math.trunc(inputTokens || 0)) / rate;
}

/**
 * A client timeout in seconds, whatever unit the SDK takes. Pure.
 * Null when the SDK is unknown, because guessing the unit is the mistake this
 * function exists to catch.
 */
export function timeoutSeconds(sdk, value) {
  if (value === null || value === undefined) return null;
  const unit = SDK_TIMEOUT_UNITS[String(sdk ?? '').trim().toLowerCase()];
  if (!unit) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n * unit[1] : null;
}

/**
 * True when a timeout looks written in the wrong unit. Pure.
 * 600 in the TypeScript client is six hundred milliseconds, not ten minutes.
 */
export function unitSuspicion(sdk, value) {
  const seconds = timeoutSeconds(sdk, value);
  if (seconds === null) return false;
  return MILLISECOND_SDKS.has(String(sdk ?? '').trim().toLowerCase()) && seconds < 1;
}

/** The largest max_tokens that still finishes inside the ceiling. Pure. */
export function safeMaxTokens(tps = DEFAULT_TPS, wallClock = WALL_CLOCK, prefill = 0) {
  const rate = Number(tps || 0);
  const room = Math.max(0, Number(wallClock || 0) - Math.max(0, Number(prefill || 0)));
  if (rate <= 0) return 0;
  return Math.trunc(room * rate);
}

/**
 * Classify one call path against the clock. Pure. [state, detail].
 * The wall clock is checked before the client timeout, because a non-streaming
 * request past ten minutes fails on the far side whatever the client waits for.
 */
export function verdict(seconds, streams, timeoutS = null, wallClock = WALL_CLOCK, near = 0.8) {
  const shape = `${duration(seconds)} of generation estimated`;

  if (!streams && seconds > wallClock) {
    return ['over-wall-clock-not-streaming',
      `${shape} on a non-streaming path, past the ${duration(wallClock)} ` +
      'ceiling. That is a 504 timeout_error, or no response at all when an ' +
      'intermediate hop drops the idle connection first. Raising the client ' +
      'timeout does not move it.'];
  }
  if (timeoutS !== null && timeoutS !== undefined && seconds > timeoutS) {
    return ['over-client-timeout',
      `${shape} against a client timeout of ${duration(timeoutS)}, so the ` +
      'client gives up before the API is finished.'];
  }
  if (!streams && seconds >= wallClock * near) {
    return ['near-wall-clock-not-streaming',
      `${shape} on a non-streaming path, inside ${(near * 100).toFixed(0)}% of ` +
      `the ${duration(wallClock)} ceiling. One unusually long answer crosses it.`];
  }
  if (streams && seconds > wallClock) {
    return ['streams-past-ten-minutes',
      `${shape}, and the path streams, so the connection never goes idle and ` +
      'the ceiling does not apply. Worth the Message Batches API if nobody is ' +
      'waiting on it.'];
  }
  return ['within-budget', `${shape}.`];
}

function headers(key) {
  return { 'x-api-key': key, 'anthropic-version': VERSION,
           'content-type': 'application/json' };
}

async function get(key, path) {
  const res = await fetch(API + path, { headers: headers(key) });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY has to be a workspace key`);
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

/** The one non-GET call, and it neither creates nor bills anything. */
async function countInput(key, payloadPath) {
  const body = JSON.parse(await readFile(payloadPath, 'utf8'));
  const trimmed = Object.fromEntries(
    Object.entries(body).filter(([k]) => !SAMPLING_ONLY.has(k)));
  const res = await fetch(`${API}/messages/count_tokens`, {
    method: 'POST',  // count_tokens creates nothing and bills nothing
    headers: headers(key),
    body: JSON.stringify(trimmed),
  });
  if (!res.ok) throw new Error(`${res.status} from /messages/count_tokens`);
  return Math.trunc((await res.json())?.input_tokens ?? 0);
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key');
    process.exitCode = 2;
    return;
  }
  const configPath = process.env.CONFIG ?? process.argv[2];
  if (!configPath) {
    console.error('set CONFIG, or pass the call-paths JSON file as an argument');
    process.exitCode = 2;
    return;
  }
  const paths = JSON.parse(await readFile(configPath, 'utf8'));
  const tps = Number(process.env.TPS ?? DEFAULT_TPS);
  const prefillTps = Number(process.env.PREFILL_TPS ?? DEFAULT_PREFILL_TPS);
  const showAll = process.env.SHOW_ALL === '1';

  const caps = new Map();
  let bad = 0;

  for (const name of Object.keys(paths).sort()) {
    const entry = paths[name] ?? {};
    const modelId = String(entry.model ?? '');
    const streams = Boolean(entry.stream);
    const sdk = entry.sdk;

    if (modelId && !caps.has(modelId)) {
      caps.set(modelId, (await get(key, `/models/${modelId}`)).max_tokens ?? null);
    }

    let inputTokens = Math.trunc(entry.input_tokens ?? 0);
    if (entry.payload) inputTokens = await countInput(key, entry.payload);

    const prefill = prefillSeconds(inputTokens, prefillTps);
    const seconds = prefill + generationSeconds(entry.max_tokens, tps);
    const client = timeoutSeconds(sdk, entry.timeout);

    const [state, detail] = verdict(seconds, streams, client);
    const line = `${state.padEnd(30)} ${name.padEnd(16)} ${detail}`;
    if (FINDINGS.has(state)) { bad += 1; console.warn(line); }
    else if (state === 'streams-past-ten-minutes') console.log(line);
    else if (showAll) console.log(line);

    if (unitSuspicion(sdk, entry.timeout)) {
      bad += 1;
      console.warn(`${'timeout-unit-mistake'.padEnd(30)} ${name.padEnd(16)} ` +
                   `timeout ${entry.timeout} on the ${sdk} client is ` +
                   `${(client ?? 0).toFixed(1)}s, not ${duration(entry.timeout ?? 0)}: ` +
                   'that unit is milliseconds');
    }

    if (state === 'over-wall-clock-not-streaming' || state === 'near-wall-clock-not-streaming') {
      console.warn(`  at ${tps.toFixed(0)} tok/s the largest max_tokens that ` +
                   `finishes inside the ceiling is ${safeMaxTokens(tps, WALL_CLOCK, prefill)}`);
      const cap = caps.get(modelId);
      if (cap) {
        console.warn(`  this model allows ${cap} output tokens, which is ` +
                     `${duration(generationSeconds(cap, tps))} on one call`);
      }
      console.warn('  repair: stream it. .stream() plus .finalMessage() returns the ' +
                   'identical Message object with no event handling, and the ' +
                   'connection never goes idle. For latency tolerant work use the ' +
                   'Message Batches API, which has no such clock. Printed, not applied.');
    }
  }

  console.log(`${Object.keys(paths).length} path(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the sentence the note exists for: the same two-thousand-token prompt with <code>max_tokens: 64000</code> is nineteen minutes and a finding, and with <code>stream: true</code> it is nineteen minutes and fine. Nothing about the prompt changed. The second is its mirror &mdash; sixty thousand tokens of input with a small <code>max_tokens</code> takes about twenty seconds, so shortening the prompt was never going to help. The rest hold the units: <code>600</code> on the Python client is ten minutes and <code>600</code> on the TypeScript client is six hundred milliseconds, and the wall clock has to be reported ahead of the client timeout because raising the client timeout is the repair that does nothing.",
"test_py_file": "test_anthropic_wall_clock_preflight.py",
"test_py": '''from anthropic_wall_clock_preflight import (duration, generation_seconds,
                                             prefill_seconds, safe_max_tokens,
                                             timeout_seconds, unit_suspicion,
                                             verdict)


def test_the_transport_decides_it_and_the_prompt_does_not():
    # A two thousand token prompt asking for 64,000 tokens back.
    seconds = prefill_seconds(2_000) + generation_seconds(64_000)
    assert duration(seconds) == "19m 23s"

    state, detail = verdict(seconds, streams=False)
    assert state == "over-wall-clock-not-streaming"
    assert "504" in detail
    assert "Raising the client timeout does not move it" in detail

    # Same seconds, same prompt, streaming: not a finding at all.
    state, detail = verdict(seconds, streams=True)
    assert state == "streams-past-ten-minutes"
    assert "never goes idle" in detail


def test_an_enormous_prompt_with_a_small_answer_is_quick():
    # The mirror image, and the reason this script reports prefill separately:
    # thirty times the input, a twentieth of the time.
    seconds = prefill_seconds(60_000) + generation_seconds(1_024)
    assert duration(seconds) == "0m 28s"
    assert verdict(seconds, streams=False)[0] == "within-budget"


def test_the_models_own_cap_is_forty_minutes_of_generation():
    # Legal to request, impossible to deliver on a non-streaming call.
    assert duration(generation_seconds(128_000)) == "38m 47s"
    assert safe_max_tokens() == 33_000
    assert safe_max_tokens(55.0, 600.0, prefill=100.0) == 27_500
    assert safe_max_tokens(tps=0) == 0


def test_six_hundred_means_two_different_things_in_two_sdks():
    assert timeout_seconds("python", 600) == 600.0
    assert timeout_seconds("ruby", 600) == 600.0
    assert timeout_seconds("typescript", 600) == 0.6
    assert timeout_seconds("TypeScript", 600) == 0.6
    assert unit_suspicion("typescript", 600) is True
    assert unit_suspicion("node", 600) is True
    assert unit_suspicion("python", 600) is False
    # A deliberate ten minutes on the TypeScript client is not suspicious.
    assert unit_suspicion("typescript", 600_000) is False
    # An SDK this script does not know about gets no guess at all.
    assert timeout_seconds("rust", 600) is None
    assert unit_suspicion("rust", 600) is False
    assert timeout_seconds("python", None) is None


def test_the_wall_clock_is_reported_ahead_of_the_client_timeout():
    # Both are true for this path. The wall clock is the one that matters,
    # because raising the client timeout leaves the request failing.
    state, _ = verdict(1_200, streams=False, timeout_s=300.0)
    assert state == "over-wall-clock-not-streaming"
    # Streaming removes the wall clock, and then the client timeout is the
    # binding number.
    state, detail = verdict(1_200, streams=True, timeout_s=300.0)
    assert state == "over-client-timeout"
    assert "gives up before the API is finished" in detail


def test_a_path_close_to_the_ceiling_is_reported_before_it_crosses():
    state, detail = verdict(540, streams=False)
    assert state == "near-wall-clock-not-streaming"
    assert "inside 80% of the 10m 00s ceiling" in detail
    assert verdict(400, streams=False)[0] == "within-budget"


def test_durations_read_as_minutes_and_seconds():
    assert duration(0) == "0m 00s"
    assert duration(59.9) == "0m 59s"
    assert duration(600) == "10m 00s"
    assert duration(-5) == "0m 00s"
    assert duration(None) == "0m 00s"
''',
"test_js_file": "anthropic-wall-clock-preflight.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { duration, generationSeconds, prefillSeconds, safeMaxTokens,
         timeoutSeconds, unitSuspicion, verdict }
  from './anthropic-wall-clock-preflight.mjs';

test('the transport decides it and the prompt does not', () => {
  const seconds = prefillSeconds(2000) + generationSeconds(64000);
  assert.equal(duration(seconds), '19m 23s');

  const [state, detail] = verdict(seconds, false);
  assert.equal(state, 'over-wall-clock-not-streaming');
  assert.match(detail, /504/);
  assert.match(detail, /Raising the client timeout does not move it/);

  const [streamState, streamDetail] = verdict(seconds, true);
  assert.equal(streamState, 'streams-past-ten-minutes');
  assert.match(streamDetail, /never goes idle/);
});

test('an enormous prompt with a small answer is quick', () => {
  const seconds = prefillSeconds(60000) + generationSeconds(1024);
  assert.equal(duration(seconds), '0m 28s');
  assert.equal(verdict(seconds, false)[0], 'within-budget');
});

test('the models own cap is forty minutes of generation', () => {
  assert.equal(duration(generationSeconds(128000)), '38m 47s');
  assert.equal(safeMaxTokens(), 33000);
  assert.equal(safeMaxTokens(55, 600, 100), 27500);
  assert.equal(safeMaxTokens(0), 0);
});

test('six hundred means two different things in two sdks', () => {
  assert.equal(timeoutSeconds('python', 600), 600);
  assert.equal(timeoutSeconds('ruby', 600), 600);
  assert.equal(timeoutSeconds('typescript', 600), 0.6);
  assert.equal(timeoutSeconds('TypeScript', 600), 0.6);
  assert.equal(unitSuspicion('typescript', 600), true);
  assert.equal(unitSuspicion('node', 600), true);
  assert.equal(unitSuspicion('python', 600), false);
  assert.equal(unitSuspicion('typescript', 600000), false);
  assert.equal(timeoutSeconds('rust', 600), null);
  assert.equal(unitSuspicion('rust', 600), false);
  assert.equal(timeoutSeconds('python', null), null);
});

test('the wall clock is reported ahead of the client timeout', () => {
  assert.equal(verdict(1200, false, 300)[0], 'over-wall-clock-not-streaming');
  const [state, detail] = verdict(1200, true, 300);
  assert.equal(state, 'over-client-timeout');
  assert.match(detail, /gives up before the API is finished/);
});

test('a path close to the ceiling is reported before it crosses', () => {
  const [state, detail] = verdict(540, false);
  assert.equal(state, 'near-wall-clock-not-streaming');
  assert.match(detail, /inside 80% of the 10m 00s ceiling/);
  assert.equal(verdict(400, false)[0], 'within-budget');
});

test('durations read as minutes and seconds', () => {
  assert.equal(duration(0), '0m 00s');
  assert.equal(duration(59.9), '0m 59s');
  assert.equal(duration(600), '10m 00s');
  assert.equal(duration(-5), '0m 00s');
  assert.equal(duration(null), '0m 00s');
});
''',
"faq": [
 ("Does streaming make the model faster?",
  "No. The same tokens are generated at the same rate. What changes is that bytes arrive continuously, so nothing between you and the API concludes the connection is idle and closes it, and the documented ten-minute ceiling on non-streaming requests stops applying. It is a transport change, not a performance one, which is exactly why shortening the prompt does nothing."),
 ("I raised the client timeout to thirty minutes and it still fails.",
  "It would. The ceiling is not yours to raise. A non-streaming Messages request is not expected to run past ten minutes on Anthropic's side, and the SDKs will refuse the combination outright rather than let you wait for something that is not coming. A raw HTTP client has no such guard, which is why this failure clusters in hand-rolled wrappers and proxy layers."),
 ("Why do I sometimes get no response at all instead of a 504?",
  "Because something closer to you gave up first. Corporate proxies, cloud load balancers and ingress controllers routinely close connections that have been idle for sixty seconds, and a non-streaming request is idle by definition while the model writes. Your client then raises a connection error, which looks like a network fault and is triaged as one."),
 ("What is a safe max_tokens for a non-streaming path?",
  "Measure your own output rate and divide ten minutes by it, then leave real margin. At around fifty-five tokens a second that puts the arithmetic ceiling near 33,000 and a sensible working value nearer 16,000. Remember thinking tokens count toward this, so raising an effort setting shortens the budget without touching the number."),
 ("Does the Batch API have the same limit?",
  "No, and that is what makes it the other half of the repair. Batches are asynchronous by design, so there is no connection to hold open and no ten-minute clock; the trade is that results arrive when they arrive rather than in the request. For work nobody is waiting on it is the better answer than streaming, and it is cheaper."),
],
"related": [REL_CAP, REL_BATCH_DISCOUNT, REL_STREAMING],
"citations": [CITE_CL_ERRORS, CITE_CL_MODELS, CITE_CL_OVERVIEW, CITE_CL_BATCHES],
},
]
