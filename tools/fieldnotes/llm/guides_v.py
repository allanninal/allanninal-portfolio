#!/usr/bin/env python3
"""/llm/ field notes, batch V — the writing.

Four assumptions that stop holding the day the model, or the stored object
underneath, changes. That is the premise, and the hazard is that "a migration
broke it" describes half the section. So each of these four owns one artefact
that was true when it was recorded and is not true now, and each reads a
different one.

`token-counts-reused-across-tokenizers` owns a **number you wrote down**. It is
deliberately not a ceiling note. The published `prompt-too-long-context-overflow`
owns one payload measured against `max_input_tokens`, and `request-too-large-413`
owns bytes; both ask "does this fit". This one never asks whether anything fits.
It calls `count_tokens` twice on a byte-identical body under two model ids and
reports the **ratio between the two integers**, because Claude 4.7 and later use
a newer tokenizer that produces roughly 30 percent more tokens for the same
text, billing follows the new counts, and every budget, chunk size and cost
model derived from the old count is now wrong in the expensive direction. A
ceiling tells you a request will fail. A ratio tells you a spreadsheet is wrong,
which is quieter and lasts longer.

`seed-determinism-unreliable` is the one that had to be rebuilt. The obvious
detection is a canary completion whose `system_fingerprint` is diffed against a
stored baseline, and this section does not send completions, so that detection
is unavailable rather than inconvenient. What replaced it is better: OpenAI
stores chat completions created with `store: true` and, unlike `/v1/responses`,
**that collection can be listed**. So the fingerprints are already there, on the
traffic that actually mattered, rather than on a probe that describes the moment
you ran it. The script reads `GET /v1/chat/completions`, groups by model, and
finds the day the fingerprint moved. The honest half is that on many current
models the field comes back null, and a script that cannot see the signal has to
say so rather than report stability it did not observe.

`previous-response-id-chain-broken` owns a **linked list with a clock on it**.
Stored response objects are saved for 30 days by default; items attached to a
conversation are persisted with no 30-day TTL. So a thread built on
`previous_response_id` has an expiry date and a thread built on a conversation
does not, and the script walks the chain upward from the ids you hold to find
which links are already gone and which are days away. Read this against the
published `batch-expired-past-24h-window` and `batch-error-file-never-read`,
which are also retention clocks: those tick in 24 hours and 30 days on a batch
and its files, and neither of them is a chain. Broken links here fail forward,
one turn at a time, on whichever conversation is oldest.

`fine-tune-job-failed-with-error-code` owns a job that was **accepted and then
failed**. It is not the published `fine-tuned-model-never-used`, which is about
a model that trained successfully and nobody calls, and it is not the batch that
covers new jobs being refused platform-wide: those two are about a job that
worked and a job that cannot start. This one is the middle case, where
`POST /v1/fine_tuning/jobs` returned 200 hours ago, the terminal state is
`failed`, and `error.code`, `error.param` and the job events feed have been
sitting there unread ever since. It reads the job list and the events feed and
nothing else — no usage report, no shutdown dates — because both of those
readings belong to the notes that already own them.

Read only, with one exception that is stated everywhere it applies:
`POST /v1/messages/count_tokens` in the first note. It is free, it creates
nothing, it generates no completion, and it has its own rate limit that is
independent of message creation. Every other request in this batch is a GET, and
the seed note in particular sends nothing at all, which is the reason it reads
somebody else's stored responses instead of making one of its own.
"""

CITE_COUNT_GUIDE = ("Token counting, including the Claude 4.7 tokenizer change",
                    "https://platform.claude.com/docs/en/build-with-claude/token-counting")
CITE_COUNT_API = ("Count Message tokens — Claude API reference",
                  "https://platform.claude.com/docs/en/api/messages-count-tokens")
CITE_MODELS = ("Models overview — Claude platform docs",
               "https://platform.claude.com/docs/en/models/overview")
CITE_PRICING = ("Pricing — Claude platform docs",
                "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_CTX = ("Context windows — Claude platform docs",
            "https://platform.claude.com/docs/en/build-with-claude/context-windows")

CITE_OAI_CHAT = ("Chat Completions — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/chat")
CITE_OAI_SEED = ("Reproducible outputs with the seed parameter — OpenAI Cookbook",
                 "https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter")
CITE_OAI_MODELS = ("Models — OpenAI API reference",
                   "https://developers.openai.com/api/docs/api-reference/models")
CITE_OAI_STATE = ("Conversation state, including the 30 day response TTL",
                  "https://developers.openai.com/api/docs/guides/conversation-state")
CITE_OAI_RESP = ("Responses — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/responses")
CITE_OAI_DATA = ("Your data — OpenAI platform docs",
                 "https://developers.openai.com/api/docs/guides/your-data")
CITE_OAI_ERRORS = ("Error codes — OpenAI platform docs",
                   "https://developers.openai.com/api/docs/guides/error-codes")
CITE_OAI_FT = ("Fine-tuning — OpenAI API reference",
               "https://developers.openai.com/api/docs/api-reference/fine-tuning")
CITE_OAI_FT_GUIDE = ("Model optimization and fine-tuning — OpenAI platform docs",
                     "https://developers.openai.com/api/docs/guides/model-optimization")
CITE_OAI_FILES = ("Files — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/files")

REL_TOKENS = ("/llm/token-counts-reused-across-tokenizers/",
              "The other number that stopped meaning what it meant last quarter")
REL_OVERFLOW = ("/llm/prompt-too-long-context-overflow/",
                "The same endpoint asked whether one payload fits, rather than by how much it grew")
REL_BYTES = ("/llm/request-too-large-413/",
             "The ceiling that is measured in bytes and not in tokens")
REL_TOOLSCH = ("/llm/tool-schemas-dominate-input-tokens/",
               "Two counts of the same body, with the tools removed instead of the model swapped")
REL_ALIAS = ("/llm/floating-alias-instead-of-pinned-snapshot/",
             "The model string in your config, and what it resolves to today")
REL_CACHE_STEP = ("/llm/cache-hit-rate-collapsed-after-model-change/",
                  "The other step change that lines up with the day a model id moved")
REL_TRUNC = ("/llm/structured-output-truncated-by-length/",
             "The other reason to read the stored response before you read its text")
REL_BATCH_EXP = ("/llm/batch-expired-past-24h-window/",
                 "A retention clock on a different object, running much faster")
REL_TOOLDEAD = ("/llm/tool-defined-but-never-called/",
                "The other note bounded by the ids you kept, because the collection cannot be listed")
REL_FT_UNUSED = ("/llm/fine-tuned-model-never-used/",
                 "The opposite terminal state: trained, billed, and never called")
REL_BATCH_PART = ("/llm/batch-partial-failure-unnoticed/",
                  "Another asynchronous job whose failure never raised anything")
REL_QUOTA = ("/llm/quota-exhausted-not-rate-limited/",
             "When the error code is about billing rather than about the request")

GUIDES = [
{
"slug": "token-counts-reused-across-tokenizers",
"title": "The same body counts 30% more tokens on the newer model",
"description": "Claude 4.7 and later use a newer tokenizer. Call count_tokens twice on one identical body under two model ids and re-baseline every budget on the ratio.",
"h1": "The same body counts 30% more tokens on the newer model",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude 4.7 tokenizer 30 percent more tokens",
             "count_tokens different model different input_tokens",
             "claude opus 5 token count higher than sonnet 4.6",
             "recount prompts after claude model migration",
             "anthropic token budget wrong after upgrade"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a workspace key. The only non-GET in this section: POST /v1/messages/count_tokens, which is free, creates no completion and bills nothing. Also needs one or more real request bodies as JSON files, and the token budgets your code has hard-coded.",
"lead": "The migration went fine. The evaluations were better, the latency was acceptable, nothing 500ed, and the rollout took an afternoon. Three weeks later the finance channel asks why input spend is up by a third on flat traffic, and somebody else opens a ticket about retrieval quality, and a third person notices that the conversation compactor now triggers two turns earlier than it used to. None of these is a bug. They are all the same fact arriving in three different rooms: the number your code uses to mean <em>how big is this</em> was measured against a model you no longer call.",
"short_answer": """<p>Measure the delta rather than assume the headline. <code>POST /v1/messages/count_tokens</code> with a <strong>workspace key</strong>, <strong>twice on the byte-identical body</strong>, once with the model you are leaving and once with the model you are moving to. The endpoint returns <code>{\"input_tokens\": N}</code> under the tokenizer of the <code>model</code> you passed, so the two integers are directly comparable and their ratio is the number you need.</p>
<p>Both calls are free. Token counting is documented as free to use, it creates no message, and its requests-per-minute limit is separate from and independent of message creation, so this measurement costs nothing but a few seconds.</p>
<p>Claude 4.7 and later models use a newer tokenizer that produces <strong>roughly 30 percent more tokens for the same text</strong>, and the exact increase depends on content and workload shape. That last clause is the reason to measure: prose, code, JSON, and a tool schema full of enum values do not move by the same amount, and your bill is computed from the real number rather than the round one.</p>
<p>Then apply the measured ratio to the constants in your code. Chunk sizes, history-trim thresholds, per-request token budgets, the tokens-per-document figure in the capacity plan, and any count you cached alongside a document instead of alongside a document <em>and</em> a model. Each of those was correct against the old tokenizer and is now wrong by the ratio.</p>
<p>This note is about a ratio, not a ceiling. If the question is whether one payload still fits in the window, that is a different reading and a different note.</p>""",
"problem": """<p>A token count is not a property of a string. It is a property of a string <em>and</em> a tokenizer, and for most of the last few years that distinction cost nothing because the tokenizer did not move. So counts got treated as intrinsic. They were written into constants, cached next to documents, quoted in capacity plans, and used to size chunks in a retrieval index that has been rebuilt exactly once, when it was created.</p>
<p>Claude 4.7 introduced a new tokenizer, and every model from 4.7 forward uses it. The same input text produces approximately 30 percent more tokens than on earlier models. Billing reflects the new counts, because billing has always reflected what the model actually consumed. So the invoice moves on the day of the migration even if the traffic does not, and nothing anywhere announces the change: no error, no header, no deprecation notice on a number in your source tree.</p>
<p>The failures are diffuse and they arrive separately, which is what makes this hard to see as one thing. Cost goes up. Prompts assembled to a fixed token budget now carry less content than they used to, so retrieval quality drops without any retrieval code changing. A conversation compactor keyed to a threshold fires earlier. A chunker that produced 800-token chunks now produces chunks that count as roughly a thousand, so the number of chunks that fit under a per-request budget falls. And a scheduled job that packs documents up to a limit starts overflowing that limit and 400ing on the largest inputs.</p>
<p>The mirror image is worth stating because it catches capacity planning going the other way. A context window is a count of tokens and that count has not changed; what changed is how much of your text fits inside it. The model comparison table puts it plainly: 1M tokens is roughly 555k words on the current tokenizer, and models before Claude Opus 4.7 fit about 750k words in the same 1M. A window that was sized in documents rather than in tokens has quietly shrunk by the same ratio, in the same direction.</p>""",
"why": """<p><strong>The generic 30 percent is not your number.</strong> The documentation says approximately, and says the exact increase depends on content and workload shape, which is an instruction to measure rather than a hedge. A prompt that is mostly English prose and a prompt that is mostly minified JSON with long identifiers do not shift by the same amount. Applying 1.3 to a budget is closer than applying 1.0, and both are guesses. Two integers from the endpoint are not.</p>
<p><strong>The two counts have to come from one body, and the script proves it rather than trusting it.</strong> If the second call is made against a body that was rebuilt, re-serialised with different whitespace, or assembled from a slightly different fixture, the ratio measures your test harness rather than the tokenizer. So the only permitted difference between the two request bodies is the <code>model</code> field, and there is a function whose whole job is to assert that, with a test that fails when a system prompt drifts by one word.</p>
<p><strong>This is a budgeting error, not a ceiling error, and the difference decides what the script does.</strong> A ceiling check asks whether one payload fits and answers with yes or no; there is a published note that does exactly that against <code>max_input_tokens</code>, and another that does it in bytes. Neither of them tells you that a constant three modules away is now 30 percent optimistic. This script never asks whether anything fits. It reports a ratio and then applies it to the numbers you declare, because the thing that is broken is arithmetic you did once and wrote down.</p>
<p><strong>A cached count keyed only by text is the same bug in storage form.</strong> If your ingestion pipeline stores <code>{doc_id: token_count}</code>, that table silently describes whichever model was current when each row was written, and a mixed table is worse than a wrong one because part of it is still right. The repair is to key by model as well, or to drop the cache. The script cannot see your cache, so it says this in the output rather than pretending to detect it.</p>
<p><strong>Counting is free, so measure the bodies you actually send.</strong> Token counting is free and separately rate-limited, which makes it reasonable to run this over a handful of representative production bodies rather than one toy message. The workload ratio the script prints is the token-weighted ratio across everything you gave it, and it is only as representative as that sample, which is why the sample size is printed next to it every time.</p>""",
"steps": [
 {"h": "Use a workspace key, and understand the one POST",
  "body": """<p>Anthropic has no read-only tier on the data plane, so the same workspace key that counts tokens could send a message. This script does not. It makes exactly one kind of request, <code>POST /v1/messages/count_tokens</code>, which is documented as free, produces no completion, and is rate-limited separately from message creation. Nothing else in this section sends a POST at all.</p>"""},
 {"h": "Export the bodies you really send",
  "body": """<p>One JSON file per representative request, in the shape you would pass to the Messages API: <code>system</code>, <code>messages</code>, <code>tools</code>, <code>thinking</code>, images, PDFs. The counting endpoint accepts the same structured input as message creation. Take these out of your logs or your fixtures, not out of your imagination, and include the ones that are mostly code or mostly JSON, because those are the ones that move furthest.</p>"""},
 {"h": "Name the model you are leaving and the model you are moving to",
  "body": """<p><code>--from claude-sonnet-4-6 --to claude-opus-5</code>. The script strips the generation-only fields the counting endpoint does not take, swaps only <code>model</code>, and asserts that the two bodies are otherwise identical before it sends either of them.</p>"""},
 {"h": "Declare the token constants your code holds",
  "body": """<p><code>--budget history=120000 --budget chunk=800</code>, or <code>ANTHROPIC_TOKEN_BUDGETS</code> as a comma-separated list. These are the numbers that were measured under the old tokenizer: chunk sizes, trim thresholds, per-request caps, the figure in the capacity plan. The script re-baselines each one on the measured ratio and prints the pair.</p>"""},
 {"h": "Read the ratio, then fix the constants",
  "body": """<p>The output is one ratio per body, one token-weighted ratio for the sample, and a re-baselined value for every budget you declared. Nothing is changed for you. The repair is a code change in your tree, plus a decision about any table that stores a token count keyed by text alone.</p>"""},
],
"verify": """<p>Re-run after the constants move. The ratio will not change, because it describes the two tokenizers rather than your code, and that is the point: this script does not go green when you fix the problem. What should change is the second column of the budget table, where each re-baselined number now matches the constant in your source. Keep the run in CI over a couple of representative bodies and it becomes a migration checklist that executes.</p>
<pre><code class="language-bash">ANTHROPIC_TOKEN_BUDGETS=history=120000,chunk=800 \\
  python3 anthropic_tokenizer_delta.py --from claude-sonnet-4-6 --to claude-opus-5 \\
    --body bodies/support-thread.json --body bodies/code-review.json
# support-thread.json   claude-sonnet-4-6  18,204 -> claude-opus-5  23,551   x1.294
# code-review.json      claude-sonnet-4-6  31,880 -> claude-opus-5  43,109   x1.352
# tokenizer-delta       the workload counts 1.330x more tokens on claude-opus-5,
#                       measured over 2 body/bodies totalling 50,084 -> 66,660
#   measured: two input_tokens values from count_tokens on identical bodies
#   inferred: that this ratio holds for traffic these 2 bodies represent
#   budget history   120,000 -> 159,600 tokens of the old measurement
#   budget chunk         800 ->   1,064 tokens of the old measurement
#   repair: re-baseline each constant above, and key any stored token count by
#           model as well as by text. A count with no model attached is wrong
#           for one of the two models and you cannot tell which.
# 1 finding(s)</code></pre>""",
"code_intro": "Two POSTs per body to one free endpoint, and seven pure functions. <code>count_body</code>, which drops the generation-only fields the counting endpoint does not accept and keeps everything that occupies the window; <code>swap_model</code>, which changes exactly one key; <code>same_apart_from_model</code>, which is the guard that makes the measurement mean anything and is asserted by its own test; <code>ratio</code>, which refuses to divide by a zero count; <code>workload_ratio</code>, which is token-weighted across the sample rather than an average of ratios; <code>rebaseline</code>, which applies the measured ratio to the constants you declared; and <code>verdict</code>, which always prints what was measured next to what is being inferred from it.",
"py_file": "anthropic_tokenizer_delta.py",
"py": '''"""Measure the token delta between two Claude models on one identical body.

Claude 4.7 and later use a newer tokenizer that produces roughly 30 percent
more tokens for the same text, and the exact increase depends on the content.
This measures the increase for your bodies instead of assuming the headline.

The only non-GET request in this section: POST /v1/messages/count_tokens. It is
documented as free, it creates no message, it generates nothing, and its rate
limit is separate from message creation. Nothing else here contacts the API.

The two calls must differ only in the model field. A ratio taken across two
bodies that drifted apart measures the harness rather than the tokenizer, so
that is asserted before either request is sent.

This is a budgeting reading, not a ceiling one. It never asks whether a payload
fits: see prompt-too-long-context-overflow for max_input_tokens and
request-too-large-413 for the byte limit.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_tokenizer_delta")

# POST to /v1/messages/count_tokens, and this is the only write-shaped call in
# the section. It creates nothing, returns no completion, and bills nothing.
COUNT_TOKENS_URL = "https://api.anthropic.com/v1/messages/count_tokens"

# Fields that belong to message creation and are not part of counting. Sending
# them is not useful and max_tokens in particular describes output, which the
# counting endpoint has no opinion about.
GENERATION_ONLY = ("max_tokens", "temperature", "top_p", "top_k", "stream",
                   "stop_sequences", "service_tier", "metadata")

# Below this the two tokenizers are the same one and the run is a no-op.
TOLERANCE = 0.02

MEASURED = "measured: two input_tokens values from count_tokens on identical bodies"
INFERRED = "inferred: that this ratio holds for traffic these %d bodies represent"

FINDINGS = ("tokenizer-delta", "count-failed", "bodies-differ")


def count_body(body):
    """A counting body from a Messages body. Pure. Generation fields removed.

    Everything that occupies the input window is kept: system, tools,
    tool_choice, thinking and the messages themselves, including images and
    documents. Only the knobs that describe generation are dropped.
    """
    if not isinstance(body, dict):
        return {}
    return {k: v for k, v in body.items() if k not in GENERATION_ONLY}


def swap_model(body, model):
    """The same body under a different model id. Pure. One key changes."""
    out = dict(body or {})
    out["model"] = str(model)
    return out


def same_apart_from_model(left, right):
    """True when the only difference is the model field. Pure.

    The guard the whole measurement rests on. Two counts of two different
    bodies is not a tokenizer ratio, it is noise with a decimal point.
    """
    a = {k: v for k, v in (left or {}).items() if k != "model"}
    b = {k: v for k, v in (right or {}).items() if k != "model"}
    return (json.dumps(a, sort_keys=True, separators=(",", ":"))
            == json.dumps(b, sort_keys=True, separators=(",", ":")))


def ratio(base, target):
    """target / base as a float. Pure. None when the base count is unusable."""
    try:
        base = int(base)
        target = int(target)
    except (TypeError, ValueError):
        return None
    if base <= 0:
        return None
    return target / base


def workload_ratio(rows):
    """Token-weighted ratio across the sample. Pure. None when nothing counted.

    Weighted, not averaged. A mean of per-body ratios lets a two-line fixture
    count as much as the 40k-token thread that is most of the bill.
    """
    base = sum(int(r.get("base_tokens") or 0) for r in rows or []
               if r.get("base_tokens"))
    target = sum(int(r.get("target_tokens") or 0) for r in rows or []
                 if r.get("target_tokens"))
    return ratio(base, target)


def rebaseline(budgets, r):
    """[(name, old, new)] for each declared constant. Pure. Sorted by name."""
    out = []
    if not r:
        return out
    for name in sorted(budgets or {}):
        old = int(budgets[name])
        out.append((name, old, int(round(old * r))))
    return out


def parse_budgets(raw):
    """{name: tokens} from name=tokens pairs. Pure. Bad pairs are dropped."""
    out = {}
    for item in raw or []:
        for part in str(item).split(","):
            if "=" not in part:
                continue
            name, _, value = part.partition("=")
            name = name.strip()
            try:
                tokens = int(str(value).strip().replace("_", ""))
            except ValueError:
                continue
            if name and tokens > 0:
                out[name] = tokens
    return out


def verdict(rows, base_model, target_model):
    """Grade the run. Pure. Returns (state, detail)."""
    rows = list(rows or [])
    if not rows:
        return ("no-bodies", "no bodies were counted, so there is nothing to "
                             "compare")
    failed = [r for r in rows if r.get("error")]
    if len(failed) == len(rows):
        return ("count-failed",
                "every count failed: %s" % failed[0].get("error"))
    if any(r.get("mismatch") for r in rows):
        return ("bodies-differ",
                "at least one pair of bodies differed by more than the model "
                "field, so no ratio was taken for it")
    r = workload_ratio(rows)
    if r is None:
        return ("count-failed", "no usable input_tokens came back")
    counted = [x for x in rows if not x.get("error")]
    if abs(r - 1.0) < TOLERANCE:
        return ("counts-agree",
                "%s and %s count this workload within %d%% of each other, so "
                "they share a tokenizer and no constant needs re-baselining"
                % (base_model, target_model, int(TOLERANCE * 100)))
    return ("tokenizer-delta",
            "the workload counts %.3fx more tokens on %s, measured over %d "
            "body/bodies" % (r, target_model, len(counted)))


def repair_lines(state, r):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "tokenizer-delta":
        lines = ["re-baseline every constant above, and key any stored token "
                 "count by model as well as by text. A count with no model "
                 "attached is wrong for one of the two models and you cannot "
                 "tell which."]
        if r and r > 1:
            lines.append("expect input spend on this workload to move by about "
                         "%d%% at flat traffic, since billing follows the count "
                         "the model actually consumed." % round((r - 1) * 100))
            lines.append("prompts assembled to a fixed token budget now carry "
                         "less content than they did. Check retrieval quality "
                         "and any compaction threshold before blaming the model.")
        return lines
    if state == "bodies-differ":
        return ["the two bodies differed by more than the model field, so the "
                "ratio would have measured the harness. Count one body, swap "
                "only model, and send it twice."]
    if state == "count-failed":
        return ["read the error text above. A 400 naming the model is an id "
                "this account cannot reach; a 413 is the 32 MB byte ceiling, "
                "which is a different note."]
    if state == "counts-agree":
        return ["nothing to change here. Both ids are on the same tokenizer, "
                "so counts measured on one transfer to the other."]
    return []


def count_tokens(body, key, timeout=30):
    """One count. Returns (input_tokens, error). Free, and creates nothing."""
    headers = {"x-api-key": key,
               "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    try:
        # POST to /v1/messages/count_tokens: free, no completion, no billing.
        r = requests.post(COUNT_TOKENS_URL, headers=headers, json=body,
                          timeout=timeout)
    except requests.RequestException as exc:
        return (None, "request failed: %s" % exc)
    if r.status_code != 200:
        detail = ""
        try:
            detail = str((r.json().get("error") or {}).get("message") or "")
        except ValueError:
            detail = (r.text or "")[:160]
        return (None, "HTTP %d %s" % (r.status_code, detail))
    try:
        return (int(r.json()["input_tokens"]), None)
    except (ValueError, KeyError, TypeError):
        return (None, "no input_tokens in the response")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="base", required=True,
                    help="the model the counts were originally measured on")
    ap.add_argument("--to", dest="target", required=True,
                    help="the model you are migrating to")
    ap.add_argument("--body", action="append", default=[],
                    help="a JSON file holding one real Messages request body")
    ap.add_argument("--budget", action="append", default=[],
                    help="name=tokens, repeatable, for a constant in your code")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key. It is used only "
                  "for POST /v1/messages/count_tokens, which is free and "
                  "creates nothing")
        return 2
    if not args.body:
        log.error("pass --body at least once with a real request body. A toy "
                  "message measures a toy ratio")
        return 2

    budgets = parse_budgets(list(args.budget)
                            + [os.environ.get("ANTHROPIC_TOKEN_BUDGETS", "")])
    rows = []
    for path in args.body:
        name = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError) as exc:
            rows.append({"name": name, "error": "unreadable: %s" % exc})
            log.warning("%-24s unreadable: %s", name, exc)
            continue

        base_body = swap_model(count_body(raw), args.base)
        target_body = swap_model(count_body(raw), args.target)
        if not same_apart_from_model(base_body, target_body):
            rows.append({"name": name, "mismatch": True})
            log.warning("%-24s the two bodies differ by more than model", name)
            continue

        base_tokens, base_err = count_tokens(base_body, key)
        target_tokens, target_err = count_tokens(target_body, key)
        err = base_err or target_err
        if err:
            rows.append({"name": name, "error": err})
            log.warning("%-24s %s", name, err)
            continue

        r = ratio(base_tokens, target_tokens)
        rows.append({"name": name, "base_tokens": base_tokens,
                     "target_tokens": target_tokens, "ratio": r})
        log.info("%-24s %s %7d -> %s %7d   x%.3f", name, args.base,
                 base_tokens, args.target, target_tokens, r or 0.0)

    state, detail = verdict(rows, args.base, args.target)
    r = workload_ratio(rows)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    if state in ("tokenizer-delta", "counts-agree"):
        emit("  %s", MEASURED)
        emit("  %s", INFERRED % len([x for x in rows if x.get("ratio")]))
    for name, old, new in rebaseline(budgets, r):
        emit("  budget %-10s %9d -> %9d tokens of the old measurement",
             name, old, new)
    if not budgets:
        emit("  no budgets declared. Pass --budget name=tokens for each token "
             "constant in your code to see it re-baselined")
    for line in repair_lines(state, r):
        emit("  repair: %s", line)

    log.info("%d finding(s)", 1 if state in FINDINGS else 0)
    return 1 if state in FINDINGS else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-tokenizer-delta.mjs",
"js": '''/**
 * Measure the token delta between two Claude models on one identical body.
 *
 * Claude 4.7 and later use a newer tokenizer that produces roughly 30 percent
 * more tokens for the same text; the exact increase depends on the content.
 *
 * The only non-GET request in this section: POST /v1/messages/count_tokens,
 * which is free, creates no message and generates nothing.
 *
 * The two calls may differ only in the model field, which is asserted before
 * either one is sent. A budgeting reading, never a ceiling one.
 */
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const COUNT_TOKENS_URL = 'https://api.anthropic.com/v1/messages/count_tokens';

const GENERATION_ONLY = new Set(['max_tokens', 'temperature', 'top_p', 'top_k',
  'stream', 'stop_sequences', 'service_tier', 'metadata']);

export const TOLERANCE = 0.02;

export const MEASURED =
  'measured: two input_tokens values from count_tokens on identical bodies';

const FINDINGS = new Set(['tokenizer-delta', 'count-failed', 'bodies-differ']);

/** A counting body from a Messages body. Pure. Generation fields removed. */
export function countBody(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return {};
  const out = {};
  for (const [k, v] of Object.entries(body)) {
    if (!GENERATION_ONLY.has(k)) out[k] = v;
  }
  return out;
}

/** The same body under a different model id. Pure. One key changes. */
export function swapModel(body, model) {
  return { ...(body ?? {}), model: String(model) };
}

const canonical = (value) => {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = canonical(value[key]);
    return out;
  }
  return value;
};

/** True when the only difference is the model field. Pure. */
export function sameApartFromModel(left, right) {
  const strip = (obj) => {
    const { model, ...rest } = obj ?? {};
    return JSON.stringify(canonical(rest));
  };
  return strip(left) === strip(right);
}

/** target / base. Pure. Null when the base count is unusable. */
export function ratio(base, target) {
  const b = Number(base);
  const t = Number(target);
  if (!Number.isFinite(b) || !Number.isFinite(t) || b <= 0) return null;
  return t / b;
}

/** Token-weighted ratio across the sample. Pure. Null when nothing counted. */
export function workloadRatio(rows) {
  let base = 0;
  let target = 0;
  for (const row of rows ?? []) {
    base += Number(row?.baseTokens ?? 0) || 0;
    target += Number(row?.targetTokens ?? 0) || 0;
  }
  return ratio(base, target);
}

/** [[name, old, new]] for each declared constant. Pure. Sorted by name. */
export function rebaseline(budgets, r) {
  if (!r) return [];
  return Object.keys(budgets ?? {}).sort()
    .map((name) => [name, Math.trunc(budgets[name]),
                    Math.round(Math.trunc(budgets[name]) * r)]);
}

/** {name: tokens} from name=tokens pairs. Pure. Bad pairs are dropped. */
export function parseBudgets(raw) {
  const out = {};
  for (const item of raw ?? []) {
    for (const part of String(item).split(',')) {
      const at = part.indexOf('=');
      if (at < 0) continue;
      const name = part.slice(0, at).trim();
      const tokens = Number.parseInt(part.slice(at + 1).trim().replace(/_/g, ''), 10);
      if (name && Number.isFinite(tokens) && tokens > 0) out[name] = tokens;
    }
  }
  return out;
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(rows, baseModel, targetModel) {
  const list = [...(rows ?? [])];
  if (!list.length) {
    return ['no-bodies', 'no bodies were counted, so there is nothing to compare'];
  }
  const failed = list.filter((r) => r?.error);
  if (failed.length === list.length) {
    return ['count-failed', `every count failed: ${failed[0].error}`];
  }
  if (list.some((r) => r?.mismatch)) {
    return ['bodies-differ',
      'at least one pair of bodies differed by more than the model field, so no '
      + 'ratio was taken for it'];
  }
  const r = workloadRatio(list);
  if (r === null) return ['count-failed', 'no usable input_tokens came back'];
  const counted = list.filter((x) => !x?.error);
  if (Math.abs(r - 1) < TOLERANCE) {
    return ['counts-agree',
      `${baseModel} and ${targetModel} count this workload within `
      + `${Math.trunc(TOLERANCE * 100)}% of each other, so they share a `
      + 'tokenizer and no constant needs re-baselining'];
  }
  return ['tokenizer-delta',
    `the workload counts ${r.toFixed(3)}x more tokens on ${targetModel}, `
    + `measured over ${counted.length} body/bodies`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, r) {
  if (state === 'tokenizer-delta') {
    const lines = ['re-baseline every constant above, and key any stored token '
      + 'count by model as well as by text. A count with no model attached is '
      + 'wrong for one of the two models and you cannot tell which.'];
    if (r && r > 1) {
      lines.push('expect input spend on this workload to move by about '
        + `${Math.round((r - 1) * 100)}% at flat traffic, since billing follows `
        + 'the count the model actually consumed.');
      lines.push('prompts assembled to a fixed token budget now carry less '
        + 'content than they did. Check retrieval quality and any compaction '
        + 'threshold before blaming the model.');
    }
    return lines;
  }
  if (state === 'bodies-differ') {
    return ['the two bodies differed by more than the model field, so the ratio '
      + 'would have measured the harness. Count one body, swap only model, and '
      + 'send it twice.'];
  }
  if (state === 'count-failed') {
    return ['read the error text above. A 400 naming the model is an id this '
      + 'account cannot reach; a 413 is the 32 MB byte ceiling, which is a '
      + 'different note.'];
  }
  if (state === 'counts-agree') {
    return ['nothing to change here. Both ids are on the same tokenizer, so '
      + 'counts measured on one transfer to the other.'];
  }
  return [];
}

async function countTokens(body, key) {
  let res;
  try {
    res = await fetch(COUNT_TOKENS_URL, {
      method: 'POST', // /v1/messages/count_tokens: free, creates and bills nothing
      headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01',
                 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (err) {
    return [null, `request failed: ${err.message}`];
  }
  if (res.status !== 200) {
    let detail = '';
    try { detail = String((await res.json())?.error?.message ?? ''); } catch { detail = ''; }
    return [null, `HTTP ${res.status} ${detail}`];
  }
  try {
    const parsed = await res.json();
    return [Math.trunc(Number(parsed.input_tokens)), null];
  } catch {
    return [null, 'no input_tokens in the response'];
  }
}

function args(argv) {
  const out = { body: [], budget: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    if (flag === '--from') out.from = argv[i += 1];
    else if (flag === '--to') out.to = argv[i += 1];
    else if (flag === '--body') out.body.push(argv[i += 1]);
    else if (flag === '--budget') out.budget.push(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key. It is used only for '
      + 'POST /v1/messages/count_tokens, which is free and creates nothing');
    process.exitCode = 2;
    return;
  }
  if (!opts.from || !opts.to || !opts.body.length) {
    console.error('usage: --from <model> --to <model> --body <file.json> '
      + '[--budget name=tokens]');
    process.exitCode = 2;
    return;
  }

  const budgets = parseBudgets([...opts.budget,
                                process.env.ANTHROPIC_TOKEN_BUDGETS ?? '']);
  const rows = [];
  for (const file of opts.body) {
    const name = path.basename(file);
    let raw;
    try {
      raw = JSON.parse(await readFile(file, 'utf8'));
    } catch (err) {
      rows.push({ name, error: `unreadable: ${err.message}` });
      console.log(`${name.padEnd(24)} unreadable: ${err.message}`);
      continue;
    }
    const baseBody = swapModel(countBody(raw), opts.from);
    const targetBody = swapModel(countBody(raw), opts.to);
    if (!sameApartFromModel(baseBody, targetBody)) {
      rows.push({ name, mismatch: true });
      console.log(`${name.padEnd(24)} the two bodies differ by more than model`);
      continue;
    }
    const [baseTokens, baseErr] = await countTokens(baseBody, key);
    const [targetTokens, targetErr] = await countTokens(targetBody, key);
    const err = baseErr || targetErr;
    if (err) {
      rows.push({ name, error: err });
      console.log(`${name.padEnd(24)} ${err}`);
      continue;
    }
    const r = ratio(baseTokens, targetTokens);
    rows.push({ name, baseTokens, targetTokens, ratio: r });
    console.log(`${name.padEnd(24)} ${opts.from} ${baseTokens} -> ${opts.to} `
      + `${targetTokens}   x${(r ?? 0).toFixed(3)}`);
  }

  const [state, detail] = verdict(rows, opts.from, opts.to);
  const r = workloadRatio(rows);
  console.log(`${state.padEnd(20)} ${detail}`);
  if (state === 'tokenizer-delta' || state === 'counts-agree') {
    console.log(`  ${MEASURED}`);
    console.log(`  inferred: that this ratio holds for traffic these `
      + `${rows.filter((x) => x.ratio).length} bodies represent`);
  }
  for (const [name, old, next] of rebaseline(budgets, r)) {
    console.log(`  budget ${name.padEnd(10)} ${old} -> ${next} tokens of the old measurement`);
  }
  if (!Object.keys(budgets).length) {
    console.log('  no budgets declared. Pass --budget name=tokens for each token '
      + 'constant in your code to see it re-baselined');
  }
  for (const line of repairLines(state, r)) console.log(`  repair: ${line}`);
  console.log(`${FINDINGS.has(state) ? 1 : 0} finding(s)`);
  process.exitCode = FINDINGS.has(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the guard the measurement rests on: a body whose system prompt drifted by one word between the two calls must be caught by <code>same_apart_from_model</code> and must never produce a ratio, because a number taken across two different bodies looks exactly like a tokenizer delta and is not one. The second is the weighting &mdash; a 40k-token thread and a 200-token fixture must not count equally, so the workload ratio is token-weighted and there is a case that fails if it is ever changed to a mean. Then the two ids that share a tokenizer, which has to come back as <code>counts-agree</code> and as a non-finding rather than as a very small delta. Then <code>count_body</code>, asserted to drop <code>max_tokens</code> and to keep <code>tools</code> and <code>thinking</code>, since dropping the wrong one would quietly measure a different prompt. Then the budget re-baselining, rounded and paired with the original. And last the failure paths, where a 413 is handed to the byte note by name instead of being reported as a ratio of zero.",
"test_py_file": "test_anthropic_tokenizer_delta.py",
"test_py": '''from anthropic_tokenizer_delta import (TOLERANCE, count_body, parse_budgets,
                                       ratio, rebaseline, repair_lines,
                                       same_apart_from_model, swap_model,
                                       verdict, workload_ratio)

BODY = {
    "model": "claude-sonnet-4-6",
    "system": "You are a scientist",
    "messages": [{"role": "user", "content": "Hello, Claude"}],
    "tools": [{"name": "get_weather", "description": "weather",
               "input_schema": {"type": "object", "properties": {}}}],
    "thinking": {"type": "enabled", "budget_tokens": 16000},
    "max_tokens": 1024,
    "temperature": 0.2,
}


def test_a_body_that_drifted_never_produces_a_ratio():
    left = swap_model(count_body(BODY), "claude-sonnet-4-6")
    right = swap_model(count_body(BODY), "claude-opus-5")
    assert same_apart_from_model(left, right)
    # One word of drift in the system prompt looks exactly like a tokenizer
    # delta and is not one.
    drifted = dict(right, system="You are a careful scientist")
    assert not same_apart_from_model(left, drifted)
    state, detail = verdict([{"name": "a.json", "mismatch": True}],
                            "claude-sonnet-4-6", "claude-opus-5")
    assert state == "bodies-differ"
    assert "no ratio was taken" in detail
    assert any("swap only model" in line for line in repair_lines(state, None))


def test_the_workload_ratio_is_token_weighted_and_not_a_mean_of_ratios():
    rows = [{"base_tokens": 40000, "target_tokens": 52000, "ratio": 1.3},
            {"base_tokens": 200, "target_tokens": 400, "ratio": 2.0}]
    # A mean of the two ratios would be 1.65. The bill follows the tokens.
    assert abs(workload_ratio(rows) - (52400 / 40200)) < 1e-9
    assert workload_ratio(rows) < 1.32
    assert workload_ratio([]) is None
    assert workload_ratio([{"base_tokens": 0, "target_tokens": 10}]) is None


def test_two_ids_on_the_same_tokenizer_are_a_non_finding():
    rows = [{"name": "a.json", "base_tokens": 1000, "target_tokens": 1005,
             "ratio": 1.005}]
    state, detail = verdict(rows, "claude-opus-5", "claude-sonnet-5")
    assert state == "counts-agree"
    assert "share a tokenizer" in detail
    assert any("transfer to the other" in line for line in repair_lines(state, 1.005))
    assert abs(1.005 - 1.0) < TOLERANCE


def test_the_delta_is_reported_with_what_it_costs_and_what_it_breaks():
    rows = [{"name": "a.json", "base_tokens": 18204, "target_tokens": 23551,
             "ratio": 1.2937}]
    state, detail = verdict(rows, "claude-sonnet-4-6", "claude-opus-5")
    assert state == "tokenizer-delta"
    assert "claude-opus-5" in detail and "1.294" in detail
    lines = repair_lines(state, workload_ratio(rows))
    assert any("key any stored token count by model" in line for line in lines)
    assert any("29%" in line for line in lines)
    assert any("retrieval quality" in line for line in lines)


def test_counting_bodies_drop_generation_fields_and_keep_the_window():
    counted = count_body(BODY)
    assert "max_tokens" not in counted and "temperature" not in counted
    for kept in ("system", "messages", "tools", "thinking"):
        assert kept in counted
    assert count_body(None) == {}
    assert swap_model(counted, "claude-fable-5")["model"] == "claude-fable-5"
    # swap_model does not mutate what it was handed.
    assert counted["model"] == "claude-sonnet-4-6"


def test_budgets_are_parsed_forgivingly_and_rebaselined_in_order():
    budgets = parse_budgets(["history=120000,chunk=800", "junk", "bad=x",
                             "zero=0"])
    assert budgets == {"history": 120000, "chunk": 800}
    assert rebaseline(budgets, 1.33) == [("chunk", 800, 1064),
                                         ("history", 120000, 159600)]
    assert rebaseline(budgets, None) == []


def test_a_413_is_handed_to_the_byte_note_rather_than_counted():
    rows = [{"name": "big.json", "error": "HTTP 413 Request exceeds the "
                                          "maximum allowed number of bytes."}]
    state, detail = verdict(rows, "claude-sonnet-4-6", "claude-opus-5")
    assert state == "count-failed"
    assert "413" in detail
    assert any("32 MB byte ceiling" in line for line in repair_lines(state, None))
    assert ratio(0, 10) is None and ratio(None, 10) is None
    assert verdict([], "a", "b")[0] == "no-bodies"
''',
"test_js_file": "anthropic-tokenizer-delta.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TOLERANCE, countBody, parseBudgets, ratio, rebaseline, repairLines,
         sameApartFromModel, swapModel, verdict,
         workloadRatio } from './anthropic-tokenizer-delta.mjs';

const BODY = {
  model: 'claude-sonnet-4-6',
  system: 'You are a scientist',
  messages: [{ role: 'user', content: 'Hello, Claude' }],
  tools: [{ name: 'get_weather', description: 'weather',
            input_schema: { type: 'object', properties: {} } }],
  thinking: { type: 'enabled', budget_tokens: 16000 },
  max_tokens: 1024,
  temperature: 0.2,
};

test('a body that drifted never produces a ratio', () => {
  const left = swapModel(countBody(BODY), 'claude-sonnet-4-6');
  const right = swapModel(countBody(BODY), 'claude-opus-5');
  assert.ok(sameApartFromModel(left, right));
  assert.ok(!sameApartFromModel(left, { ...right, system: 'You are a careful scientist' }));
  const [state, detail] = verdict([{ name: 'a.json', mismatch: true }],
                                  'claude-sonnet-4-6', 'claude-opus-5');
  assert.equal(state, 'bodies-differ');
  assert.ok(detail.includes('no ratio was taken'));
  assert.ok(repairLines(state, null).some((l) => l.includes('swap only model')));
});

test('the workload ratio is token weighted and not a mean of ratios', () => {
  const rows = [{ baseTokens: 40000, targetTokens: 52000, ratio: 1.3 },
                { baseTokens: 200, targetTokens: 400, ratio: 2.0 }];
  assert.ok(Math.abs(workloadRatio(rows) - (52400 / 40200)) < 1e-9);
  assert.ok(workloadRatio(rows) < 1.32);
  assert.equal(workloadRatio([]), null);
  assert.equal(workloadRatio([{ baseTokens: 0, targetTokens: 10 }]), null);
});

test('two ids on the same tokenizer are a non finding', () => {
  const rows = [{ name: 'a.json', baseTokens: 1000, targetTokens: 1005, ratio: 1.005 }];
  const [state, detail] = verdict(rows, 'claude-opus-5', 'claude-sonnet-5');
  assert.equal(state, 'counts-agree');
  assert.ok(detail.includes('share a tokenizer'));
  assert.ok(repairLines(state, 1.005).some((l) => l.includes('transfer to the other')));
  assert.ok(Math.abs(1.005 - 1) < TOLERANCE);
});

test('the delta is reported with what it costs and what it breaks', () => {
  const rows = [{ name: 'a.json', baseTokens: 18204, targetTokens: 23551, ratio: 1.2937 }];
  const [state, detail] = verdict(rows, 'claude-sonnet-4-6', 'claude-opus-5');
  assert.equal(state, 'tokenizer-delta');
  assert.ok(detail.includes('claude-opus-5') && detail.includes('1.294'));
  const lines = repairLines(state, workloadRatio(rows));
  assert.ok(lines.some((l) => l.includes('key any stored token count by model')));
  assert.ok(lines.some((l) => l.includes('29%')));
  assert.ok(lines.some((l) => l.includes('retrieval quality')));
});

test('counting bodies drop generation fields and keep the window', () => {
  const counted = countBody(BODY);
  assert.ok(!('max_tokens' in counted) && !('temperature' in counted));
  for (const kept of ['system', 'messages', 'tools', 'thinking']) {
    assert.ok(kept in counted);
  }
  assert.deepEqual(countBody(null), {});
  assert.equal(swapModel(counted, 'claude-fable-5').model, 'claude-fable-5');
  assert.equal(counted.model, 'claude-sonnet-4-6');
});

test('budgets are parsed forgivingly and rebaselined in order', () => {
  const budgets = parseBudgets(['history=120000,chunk=800', 'junk', 'bad=x', 'zero=0']);
  assert.deepEqual(budgets, { history: 120000, chunk: 800 });
  assert.deepEqual(rebaseline(budgets, 1.33),
                   [['chunk', 800, 1064], ['history', 120000, 159600]]);
  assert.deepEqual(rebaseline(budgets, null), []);
});

test('a 413 is handed to the byte note rather than counted', () => {
  const rows = [{ name: 'big.json',
                  error: 'HTTP 413 Request exceeds the maximum allowed number of bytes.' }];
  const [state, detail] = verdict(rows, 'claude-sonnet-4-6', 'claude-opus-5');
  assert.equal(state, 'count-failed');
  assert.ok(detail.includes('413'));
  assert.ok(repairLines(state, null).some((l) => l.includes('32 MB byte ceiling')));
  assert.equal(ratio(0, 10), null);
  assert.equal(ratio(null, 10), null);
  assert.equal(verdict([], 'a', 'b')[0], 'no-bodies');
});
''',
"faq": [
 ("Is it really 30 percent?",
  "Approximately, and the documentation says so in those words: Claude 4.7 and later models use a newer tokenizer that produces about 30 percent more tokens for the same text, with the exact increase depending on the content and workload shape. That last clause is why this note exists as a script rather than a multiplication. English prose, minified JSON, source code and a tool schema full of enum strings do not move by the same amount, and the number that decides your invoice is the one measured on your bodies rather than the one in the release note."),
 ("Which models are on which tokenizer?",
  "Claude 4.7 and later use the newer one; models before Claude Opus 4.7 use the previous one. That is the boundary, and it is a boundary rather than a per-model table, which is why the script takes two ids from you instead of shipping a list that would go stale. If both ids you pass are on the same side of it, the run comes back as counts-agree and there is nothing to re-baseline. That is a useful answer too, and it is the one you want before a migration rather than after."),
 ("Does counting tokens cost anything or eat my rate limit?",
  "No and no. Token counting is documented as free to use, and it has its own requests-per-minute limit that is separate from and independent of message creation: usage of one does not count against the other. That is the reason a note in a read-only section can send a POST at all. It creates no message, returns no completion, and produces nothing that appears on a bill."),
 ("The count and the billed input tokens do not match exactly. Why?",
  "Because the count is documented as an estimate, and the actual number of input tokens used when creating a message can differ by a small amount. It can also include tokens Anthropic adds automatically for system optimizations, which you are not billed for. Neither of those matters much here: both counts in a pair are estimates produced the same way, so the systematic part cancels in the ratio. Do not use a single count as an invoice line, and do use the ratio as a ratio."),
 ("We cache a token count next to each document. Is that safe?",
  "Only if the cache key includes the model. A table of {document: token_count} describes whichever tokenizer was current when each row was written, so after a migration it is a mixture of right and wrong answers with no way to tell them apart, which is worse than being uniformly wrong. The script cannot see your cache, so it prints this rather than detecting it. Add the model to the key, or drop the table and recount, which is free."),
],
"related": [REL_OVERFLOW, REL_TOOLSCH, REL_BYTES],
"citations": [CITE_COUNT_GUIDE, CITE_COUNT_API, CITE_MODELS, CITE_PRICING],
},
{
"slug": "seed-determinism-unreliable",
"title": "system_fingerprint moved and seed stopped reproducing",
"description": "Read system_fingerprint off the chat completions you already stored. Two values for one model void every seed-keyed cache and baseline spanning that day.",
"h1": "system_fingerprint moved and seed stopped reproducing",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai system_fingerprint changed seed different output",
             "seed parameter best effort not deterministic",
             "list stored chat completions system_fingerprint",
             "golden file test fails after openai backend change",
             "system_fingerprint null gpt-5"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only. Reads GET /v1/chat/completions, which lists only completions your application created with store set to true. Sends nothing, and creates nothing.",
"lead": "The golden-file suite has been green for eight months. It pins <code>seed</code>, it pins <code>temperature</code> to zero, it asserts on the exact string the model returned the day the fixtures were recorded, and everybody agreed at the time that this was a reasonable way to test an LLM because it worked. This morning forty of them fail. The diffs are trivial &mdash; a comma, a reordered clause, one adjective &mdash; and nothing in the repository changed. The commit that broke them is not in your repository.",
"short_answer": """<p>Read the fingerprints you already have. Chat completions created with <code>store: true</code> can be listed: <code>GET /v1/chat/completions?limit=100&amp;order=asc</code> with a <strong>project key set to Read Only</strong>, optionally filtered by <code>model</code> or by <code>metadata</code>. Each stored completion carries <code>system_fingerprint</code>, which represents the backend configuration the model ran with and exists precisely so that it can be used together with <code>seed</code> to tell when a backend change has happened.</p>
<p>Group by <code>model</code>, order by <code>created</code>, and look for the day the value changed. <strong>Two distinct fingerprints for one model id inside your window means every seed-keyed cache entry and every golden file that spans that day is describing a backend that no longer exists.</strong> The script prints the transition, both values and the timestamp.</p>
<p><strong>This script does not send a canary completion, and that is a deliberate design decision rather than a limitation.</strong> The obvious version of this check posts a fixed prompt and diffs the fingerprint that comes back. That generates, it bills, and this section does not do it. It is also the weaker reading: a canary describes the backend that served one request at the moment you ran it, while your stored completions describe the backend that served the traffic you are actually worried about.</p>
<p>There is an honest failure mode and the script reports it as a finding rather than as silence. On many current models <code>system_fingerprint</code> comes back null or absent. Where every stored completion for a model has no fingerprint, the signal does not exist, you cannot detect a backend change through it even in principle, and the only correct conclusion is to stop building reproducibility on <code>seed</code> for that model.</p>""",
"problem": """<p><code>seed</code> is documented as best effort. The exact words are that the system will make a best effort to sample deterministically, such that repeated requests with the same seed and parameters <em>should</em> return the same result. It is not a guarantee, it has never been one, and the parameter is described as a beta feature. Determinism was always conditional on the backend staying still.</p>
<p><code>system_fingerprint</code> is the field that tells you whether it did. It represents the backend configuration the model runs with, and its documented purpose is to be used in conjunction with the seed request parameter to understand when backend changes have been made that might impact determinism. When that string changes, the same seed and the same prompt can produce different output, and nothing else announces it: no version bump, no deprecation, no header on your requests, and no entry in any log you own.</p>
<p>What breaks is everything downstream that treated identical output as a contract. Golden-file tests fail with meaningless diffs. A response cache keyed on a hash of <code>(prompt, seed, params)</code> stops hitting, which is expensive and quiet. An evaluation harness that compares a new prompt against a stored baseline now compares two things that differ for two reasons and cannot separate them. And a snapshot test in CI turns into a flaky test, which is worse than a failing one, because the team learns to re-record it.</p>
<p>The migration angle is the sharp end. Moving onto a reasoning model removes the sampling knobs entirely, so a strategy built on <code>seed</code> plus <code>temperature: 0</code> does not survive the move. And the Responses API object carries neither <code>seed</code> nor <code>system_fingerprint</code> at all, so a team that migrated off Chat Completions did not weaken this signal, they deleted it.</p>""",
"why": """<p><strong>The canary is the obvious design and it is the wrong one twice over.</strong> Sending a fixed prompt to compare fingerprints generates output and bills for it, which this section does not do. But even with a budget for it, it answers a narrower question: a canary tells you the configuration that served one request from one host at one moment, while the stored completions tell you which configurations served the requests whose outputs you cached, tested against and shipped. The evidence you want is already sitting in the account.</p>
<p><strong>This works because stored chat completions can be listed, and stored responses cannot.</strong> That asymmetry is the whole reason this note has a script. <code>/v1/responses</code> has no list endpoint, so every note in this section that reads a stored response takes a file of ids from your own logs. <code>GET /v1/chat/completions</code> is a real listing with <code>model</code>, <code>metadata</code>, <code>after</code>, <code>limit</code> and <code>order</code>, so the sample is whatever your application stored rather than whatever you happened to write down.</p>
<p><strong>A missing fingerprint is a finding, not a pass.</strong> The field is optional and on a good deal of current traffic it is null. A script that only alarmed on a change would report a clean run for a model whose determinism signal is entirely absent, which is the most misleading output it could produce. So absence gets its own verdict, its own repair, and the plainest wording in the script: this cannot be detected here, stop depending on it.</p>
<p><strong>Two fingerprints in a window is not always a clean switchover.</strong> If the values interleave &mdash; A, then B, then A again &mdash; you are being served by a fleet running more than one configuration at once, and two calls made the same afternoon can land on different backends. That is a materially different situation from a single dated change, so the script distinguishes them, because the repair for one is to re-record baselines and the repair for the other is to stop believing in reproducibility altogether.</p>
<p><strong>Stability inside your window is not a guarantee outside it.</strong> When one fingerprint holds across the whole sample, the script says that the parameter is behaving as documented so far, and says explicitly that this is not a promise. The documented contract is best effort. A run of good luck is not a change in that contract, and a script that printed a green tick here would be teaching the wrong lesson.</p>""",
"steps": [
 {"h": "Use a project key set to Read Only",
  "body": """<p>Everything here is a GET of <code>/v1/chat/completions</code>. No completion is created, nothing is stored, nothing is deleted, and no admin key is needed: this is project-scoped data rather than organization usage.</p>"""},
 {"h": "Check that anything is stored at all",
  "body": """<p>Only completions created with <code>store: true</code> appear in the listing. An empty list is one of the more useful outcomes: it means this question cannot currently be answered from the API, and the first repair is to store a sample of traffic, or to accept that reproducibility has no evidence behind it. A Zero Data Retention organization will never have anything here, and that is a decision rather than a bug.</p>"""},
 {"h": "List the window, oldest first",
  "body": """<p><code>limit=100</code>, <code>order=asc</code>, paginating on <code>after</code>, optionally narrowed with <code>--model</code> or a <code>metadata</code> filter if your application tags its calls. Ordering ascending matters: the finding is the moment a value changed, and that is only readable in sequence.</p>"""},
 {"h": "Group by model and read the transitions",
  "body": """<p>Per model id, the script reports the number of completions, how many carry a fingerprint, the distinct values, and every point where consecutive values differ, with the timestamp. It also says whether the values switched once or interleaved, because those are different problems.</p>"""},
 {"h": "Take the repair out of the test suite, not out of the API",
  "body": """<p>There is nothing to fix on the platform. Pin the model snapshot rather than a floating alias, assert on structure and semantics instead of exact strings, record <code>system_fingerprint</code> next to every golden file so a change explains a diff rather than failing a build, and if you need true determinism, cache your own responses.</p>"""},
],
"verify": """<p>Re-run after the baselines are re-recorded. The transition does not disappear, because it is a fact about the platform's history rather than about your code; what changes is that your fixtures now sit entirely on one side of it. The check worth automating is the fingerprint one: run this weekly against the last seven days, and treat a new transition as a scheduled task to re-record baselines rather than as a broken build on a Tuesday morning.</p>
<pre><code class="language-bash">python3 openai_fingerprint_drift.py --days 30
# gpt-5.6-sol          412 stored, 412 with a fingerprint, 2 distinct
#   fp_9c1a44d2e8 -> fp_7be03f1a55  at 2026-08-14T02:11:07Z
# fingerprint-moved    gpt-5.6-sol ran under 2 backend configurations in this
#                      window, switching once
#   measured: distinct system_fingerprint values on completions you already made
#   inferred: that output recorded before the switch is not reproducible after it
#   repair: stop using seed as a cache key or a test oracle. Assert on structure
#           and semantics, and record system_fingerprint beside every baseline.
# gpt-5.6-terra         88 stored, 0 with a fingerprint, 0 distinct
# fingerprint-absent   no stored completion on gpt-5.6-terra carries a
#                      system_fingerprint, so a backend change cannot be
#                      detected here even in principle
#   repair: do not build reproducibility on seed for this model. There is no
#           signal to alarm on, so cache your own responses instead.
# 2 finding(s)</code></pre>""",
"code_intro": "One paged GET and six pure functions. <code>flatten</code>, which turns pages into rows and coerces a missing fingerprint to an empty string rather than letting <code>None</code> reach a comparison; <code>within</code>, which applies the window against a cutoff passed in, so the function is testable without a clock; <code>by_model</code>, which groups and sorts by <code>created</code> because a transition is only visible in order; <code>transitions</code>, which returns every point where consecutive non-empty values differ, with the timestamp; <code>interleaved</code>, which separates one dated switchover from a fleet serving two configurations at once; and <code>verdict</code>, which treats an absent fingerprint as a finding rather than as a clean run.",
"py_file": "openai_fingerprint_drift.py",
"py": '''"""Find the day system_fingerprint moved, using completions you already stored.

Read only, and it sends nothing at all. One paged GET of /v1/chat/completions,
which lists chat completions your application created with store set to true.
No completion is created here, which is why this reads somebody else's stored
traffic rather than posting a canary of its own: a canary would generate, would
bill, and would only describe the backend that served one request at the moment
the script ran.

system_fingerprint represents the backend configuration the model runs with and
exists to be read alongside seed, which is documented as best effort rather than
a guarantee. Two distinct values for one model inside the window means any
seed-keyed cache entry or golden file spanning that point is void.

The field is optional. Where it comes back empty on every stored completion for
a model, that is reported as a finding, because a determinism signal you cannot
read is not a determinism signal.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_fingerprint_drift")

LIST_URL = "https://api.openai.com/v1/chat/completions"

MEASURED = ("measured: distinct system_fingerprint values on completions you "
            "already made")
INFERRED = ("inferred: that output recorded before the switch is not "
            "reproducible after it")

FINDINGS = ("fingerprint-moved", "fingerprint-absent", "nothing-stored")


def iso(ts):
    """A UTC timestamp string. Pure. Empty for anything unusable."""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts)))
    except (TypeError, ValueError, OSError):
        return ""


def flatten(pages):
    """Rows from listing pages. Pure. A missing fingerprint becomes "".

    Coerced rather than passed through: None and an absent key both mean "no
    fingerprint here", and letting either reach a comparison would make an
    absent value look like a distinct one.
    """
    rows = []
    for page in pages or []:
        for item in (page or {}).get("data") or []:
            if not isinstance(item, dict):
                continue
            try:
                created = int(item.get("created") or 0)
            except (TypeError, ValueError):
                created = 0
            rows.append({"id": str(item.get("id") or ""),
                         "created": created,
                         "model": str(item.get("model") or "(unknown)"),
                         "fingerprint": str(item.get("system_fingerprint") or "")})
    return rows


def within(rows, cutoff):
    """Rows created at or after cutoff. Pure. The clock is passed in."""
    if not cutoff:
        return list(rows or [])
    return [r for r in rows or [] if int(r.get("created") or 0) >= int(cutoff)]


def by_model(rows):
    """{model: [row, ...]} sorted by created. Pure. Order is the whole finding."""
    grouped = {}
    for row in rows or []:
        grouped.setdefault(row.get("model") or "(unknown)", []).append(row)
    for model in grouped:
        grouped[model].sort(key=lambda r: (int(r.get("created") or 0),
                                           r.get("id") or ""))
    return grouped


def transitions(rows):
    """[(created, old, new)] where consecutive fingerprints differ. Pure."""
    out = []
    previous = ""
    for row in rows or []:
        current = str(row.get("fingerprint") or "")
        if not current:
            continue
        if previous and current != previous:
            out.append((int(row.get("created") or 0), previous, current))
        previous = current
    return out


def interleaved(rows):
    """True when a fingerprint reappears after another one. Pure.

    One dated switchover and a fleet serving two configurations at once look
    identical in a set of distinct values and are different problems: the first
    invalidates baselines recorded before a date, the second invalidates the
    idea that two calls this afternoon agree with each other.
    """
    runs = []
    for row in rows or []:
        current = str(row.get("fingerprint") or "")
        if not current:
            continue
        if not runs or runs[-1] != current:
            runs.append(current)
    return len(runs) > len(set(runs))


def verdict(model, rows):
    """Grade one model. Pure. Returns (state, detail)."""
    rows = list(rows or [])
    with_fp = [r for r in rows if r.get("fingerprint")]
    distinct = sorted({r["fingerprint"] for r in with_fp})
    if not rows:
        return ("nothing-stored",
                "no stored completions for %s in this window" % model)
    if not with_fp:
        return ("fingerprint-absent",
                "no stored completion on %s carries a system_fingerprint, so a "
                "backend change cannot be detected here even in principle"
                % model)
    if len(distinct) == 1 and len(with_fp) == 1:
        return ("single-observation",
                "one stored completion on %s carries a fingerprint, which is a "
                "reading and not a comparison" % model)
    if len(distinct) == 1:
        return ("fingerprint-stable",
                "%s ran under one backend configuration across %d stored "
                "completions. seed is documented as best effort, so this is "
                "the parameter behaving rather than a guarantee"
                % (model, len(with_fp)))
    shape = ("interleaving, so more than one configuration is being served at "
             "once" if interleaved(rows) else "switching once")
    return ("fingerprint-moved",
            "%s ran under %d backend configurations in this window, %s"
            % (model, len(distinct), shape))


def repair_lines(state, mixed=False):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "fingerprint-moved":
        lines = ["stop using seed as a cache key or a test oracle. Assert on "
                 "structure and semantics, and record system_fingerprint beside "
                 "every baseline so a change explains a diff instead of failing "
                 "a build.",
                 "pin the model snapshot rather than a floating alias, so at "
                 "least the weights are not a second moving part."]
        if mixed:
            lines.append("the values interleave rather than switching once, so "
                         "two calls made minutes apart can land on different "
                         "configurations. Re-recording baselines will not fix "
                         "that; only caching your own responses will.")
        return lines
    if state == "fingerprint-absent":
        return ["do not build reproducibility on seed for this model. There is "
                "no signal to alarm on, so cache your own responses instead.",
                "if a test needs stability, freeze the response in the fixture "
                "rather than asking the platform to reproduce it."]
    if state == "nothing-stored":
        return ["nothing was stored, so this question cannot be answered from "
                "the API. Set store: true on a sample of traffic, or accept "
                "that reproducibility has no evidence behind it.",
                "note that the Responses API object carries neither seed nor "
                "system_fingerprint, and /v1/responses cannot be listed, so a "
                "migration onto it removes this reading entirely."]
    if state == "fingerprint-stable":
        return ["nothing to do today. Keep this run on a schedule: the value "
                "held across the window, which is best effort holding, not a "
                "promise that it will."]
    if state == "single-observation":
        return ["store more traffic or widen the window. One fingerprint is a "
                "reading, and this note needs two to say anything."]
    return []


def fetch(key, model=None, metadata=None, timeout=30):
    """Paged GET of the stored chat completions. Returns (pages, error)."""
    pages = []
    params = {"limit": 100, "order": "asc"}
    if model:
        params["model"] = model
    for pair in metadata or []:
        name, _, value = str(pair).partition("=")
        if name and value:
            params["metadata[%s]" % name.strip()] = value.strip()
    headers = {"Authorization": "Bearer " + key}
    for _ in range(200):
        try:
            r = requests.get(LIST_URL, headers=headers, params=params,
                             timeout=timeout)
        except requests.RequestException as exc:
            return (pages, "request failed: %s" % exc)
        if r.status_code != 200:
            return (pages, "HTTP %d %s" % (r.status_code, (r.text or "")[:160]))
        body = r.json()
        pages.append(body)
        if not body.get("has_more") or not body.get("last_id"):
            break
        params["after"] = body["last_id"]
    return (pages, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read, in days")
    ap.add_argument("--model", help="narrow the listing to one model id")
    ap.add_argument("--metadata", action="append", default=[],
                    help="key=value filter, if your calls are tagged")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only. It is "
                  "used for one paged GET of /v1/chat/completions")
        return 2

    pages, err = fetch(key, args.model, args.metadata)
    if err:
        log.error("%s", err)
        return 2

    cutoff = int(time.time()) - args.days * 86400
    rows = within(flatten(pages), cutoff)
    grouped = by_model(rows)
    findings = 0

    if not rows:
        state, detail = verdict("(any model)", [])
        log.warning("%-20s %s", state, detail)
        for line in repair_lines(state):
            log.warning("  repair: %s", line)
        log.info("1 finding(s)")
        return 1

    for model in sorted(grouped):
        entries = grouped[model]
        with_fp = [r for r in entries if r.get("fingerprint")]
        distinct = sorted({r["fingerprint"] for r in with_fp})
        log.info("%-20s %d stored, %d with a fingerprint, %d distinct",
                 model, len(entries), len(with_fp), len(distinct))
        for created, old, new in transitions(entries):
            log.warning("  %s -> %s  at %s", old, new, iso(created))

        state, detail = verdict(model, entries)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s", state, detail)
        if state == "fingerprint-moved":
            emit("  %s", MEASURED)
            emit("  %s", INFERRED)
        for line in repair_lines(state, interleaved(entries)):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-fingerprint-drift.mjs",
"js": '''/**
 * Find the day system_fingerprint moved, using completions you already stored.
 *
 * Read only, and it sends nothing at all. One paged GET of
 * /v1/chat/completions, which lists chat completions created with store set to
 * true. No canary is posted: that would generate and bill, and it would only
 * describe the backend serving one request at the moment the script ran.
 *
 * The field is optional. Where it is empty on every stored completion for a
 * model, that is a finding, because a signal you cannot read is not a signal.
 */
const LIST_URL = 'https://api.openai.com/v1/chat/completions';

export const MEASURED =
  'measured: distinct system_fingerprint values on completions you already made';

const FINDINGS = new Set(['fingerprint-moved', 'fingerprint-absent', 'nothing-stored']);

/** A UTC timestamp string. Pure. Empty for anything unusable. */
export function iso(ts) {
  const seconds = Number(ts);
  if (!Number.isFinite(seconds) || seconds <= 0) return '';
  return `${new Date(seconds * 1000).toISOString().slice(0, 19)}Z`;
}

/** Rows from listing pages. Pure. A missing fingerprint becomes ''. */
export function flatten(pages) {
  const rows = [];
  for (const page of pages ?? []) {
    for (const item of page?.data ?? []) {
      if (!item || typeof item !== 'object') continue;
      const created = Number(item.created ?? 0);
      rows.push({
        id: String(item.id ?? ''),
        created: Number.isFinite(created) ? Math.trunc(created) : 0,
        model: String(item.model ?? '(unknown)'),
        fingerprint: String(item.system_fingerprint ?? ''),
      });
    }
  }
  return rows;
}

/** Rows created at or after cutoff. Pure. The clock is passed in. */
export function within(rows, cutoff) {
  if (!cutoff) return [...(rows ?? [])];
  return (rows ?? []).filter((r) => Number(r?.created ?? 0) >= Number(cutoff));
}

/** {model: [row]} sorted by created. Pure. Order is the whole finding. */
export function byModel(rows) {
  const grouped = {};
  for (const row of rows ?? []) {
    const model = row?.model || '(unknown)';
    (grouped[model] ??= []).push(row);
  }
  for (const model of Object.keys(grouped)) {
    grouped[model].sort((a, b) => (a.created - b.created)
      || String(a.id).localeCompare(String(b.id)));
  }
  return grouped;
}

/** [[created, old, new]] where consecutive fingerprints differ. Pure. */
export function transitions(rows) {
  const out = [];
  let previous = '';
  for (const row of rows ?? []) {
    const current = String(row?.fingerprint ?? '');
    if (!current) continue;
    if (previous && current !== previous) {
      out.push([Math.trunc(Number(row.created ?? 0)), previous, current]);
    }
    previous = current;
  }
  return out;
}

/** True when a fingerprint reappears after another one. Pure. */
export function interleaved(rows) {
  const runs = [];
  for (const row of rows ?? []) {
    const current = String(row?.fingerprint ?? '');
    if (!current) continue;
    if (!runs.length || runs[runs.length - 1] !== current) runs.push(current);
  }
  return runs.length > new Set(runs).size;
}

/** Grade one model. Pure. Returns [state, detail]. */
export function verdict(model, rows) {
  const list = [...(rows ?? [])];
  const withFp = list.filter((r) => r?.fingerprint);
  const distinct = [...new Set(withFp.map((r) => r.fingerprint))].sort();
  if (!list.length) {
    return ['nothing-stored', `no stored completions for ${model} in this window`];
  }
  if (!withFp.length) {
    return ['fingerprint-absent',
      `no stored completion on ${model} carries a system_fingerprint, so a `
      + 'backend change cannot be detected here even in principle'];
  }
  if (distinct.length === 1 && withFp.length === 1) {
    return ['single-observation',
      `one stored completion on ${model} carries a fingerprint, which is a `
      + 'reading and not a comparison'];
  }
  if (distinct.length === 1) {
    return ['fingerprint-stable',
      `${model} ran under one backend configuration across ${withFp.length} `
      + 'stored completions. seed is documented as best effort, so this is the '
      + 'parameter behaving rather than a guarantee'];
  }
  const shape = interleaved(list)
    ? 'interleaving, so more than one configuration is being served at once'
    : 'switching once';
  return ['fingerprint-moved',
    `${model} ran under ${distinct.length} backend configurations in this `
    + `window, ${shape}`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, mixed = false) {
  if (state === 'fingerprint-moved') {
    const lines = ['stop using seed as a cache key or a test oracle. Assert on '
      + 'structure and semantics, and record system_fingerprint beside every '
      + 'baseline so a change explains a diff instead of failing a build.',
      'pin the model snapshot rather than a floating alias, so at least the '
      + 'weights are not a second moving part.'];
    if (mixed) {
      lines.push('the values interleave rather than switching once, so two calls '
        + 'made minutes apart can land on different configurations. Re-recording '
        + 'baselines will not fix that; only caching your own responses will.');
    }
    return lines;
  }
  if (state === 'fingerprint-absent') {
    return ['do not build reproducibility on seed for this model. There is no '
      + 'signal to alarm on, so cache your own responses instead.',
      'if a test needs stability, freeze the response in the fixture rather than '
      + 'asking the platform to reproduce it.'];
  }
  if (state === 'nothing-stored') {
    return ['nothing was stored, so this question cannot be answered from the '
      + 'API. Set store: true on a sample of traffic, or accept that '
      + 'reproducibility has no evidence behind it.',
      'note that the Responses API object carries neither seed nor '
      + 'system_fingerprint, and /v1/responses cannot be listed, so a migration '
      + 'onto it removes this reading entirely.'];
  }
  if (state === 'fingerprint-stable') {
    return ['nothing to do today. Keep this run on a schedule: the value held '
      + 'across the window, which is best effort holding, not a promise that it '
      + 'will.'];
  }
  if (state === 'single-observation') {
    return ['store more traffic or widen the window. One fingerprint is a '
      + 'reading, and this note needs two to say anything.'];
  }
  return [];
}

async function fetchPages(key, model, metadata) {
  const pages = [];
  const params = new URLSearchParams({ limit: '100', order: 'asc' });
  if (model) params.set('model', model);
  for (const pair of metadata ?? []) {
    const at = String(pair).indexOf('=');
    if (at > 0) {
      params.set(`metadata[${pair.slice(0, at).trim()}]`, pair.slice(at + 1).trim());
    }
  }
  for (let page = 0; page < 200; page += 1) {
    const url = `${LIST_URL}?${params.toString()}`;
    let res;
    try {
      res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    } catch (err) {
      return [pages, `request failed: ${err.message}`];
    }
    if (res.status !== 200) {
      return [pages, `HTTP ${res.status} ${(await res.text()).slice(0, 160)}`];
    }
    const body = await res.json();
    pages.push(body);
    if (!body.has_more || !body.last_id) break;
    params.set('after', body.last_id);
  }
  return [pages, null];
}

function args(argv) {
  const out = { days: 30, metadata: [] };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--days') out.days = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--model') out.model = argv[i += 1];
    else if (argv[i] === '--metadata') out.metadata.push(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only. It is '
      + 'used for one paged GET of /v1/chat/completions');
    process.exitCode = 2;
    return;
  }
  const [pages, err] = await fetchPages(key, opts.model, opts.metadata);
  if (err) {
    console.error(err);
    process.exitCode = 2;
    return;
  }
  const cutoff = Math.trunc(Date.now() / 1000) - (opts.days || 30) * 86400;
  const rows = within(flatten(pages), cutoff);
  const grouped = byModel(rows);
  let findings = 0;

  if (!rows.length) {
    const [state, detail] = verdict('(any model)', []);
    console.log(`${state.padEnd(20)} ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    console.log('1 finding(s)');
    process.exitCode = 1;
    return;
  }

  for (const model of Object.keys(grouped).sort()) {
    const entries = grouped[model];
    const withFp = entries.filter((r) => r.fingerprint);
    const distinct = new Set(withFp.map((r) => r.fingerprint));
    console.log(`${model.padEnd(20)} ${entries.length} stored, ${withFp.length} `
      + `with a fingerprint, ${distinct.size} distinct`);
    for (const [created, old, next] of transitions(entries)) {
      console.log(`  ${old} -> ${next}  at ${iso(created)}`);
    }
    const [state, detail] = verdict(model, entries);
    console.log(`${state.padEnd(20)} ${detail}`);
    if (state === 'fingerprint-moved') {
      console.log(`  ${MEASURED}`);
      console.log('  inferred: that output recorded before the switch is not '
        + 'reproducible after it');
    }
    for (const line of repairLines(state, interleaved(entries))) {
      console.log(`  repair: ${line}`);
    }
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note itself: two fingerprints on one model, in order, produce <code>fingerprint-moved</code> and a transition carrying both values and the timestamp of the first completion under the new one. The second is the outcome that most scripts would get wrong &mdash; every stored completion with a null fingerprint must be a finding named <code>fingerprint-absent</code>, never a quiet pass, and its repair has to say that the signal does not exist rather than that nothing changed. The third separates one dated switchover from an interleaved fleet, because the first is repaired by re-recording baselines and the second is not repaired at all. Then the single observation, which refuses to conclude. Then the empty listing, which must point at <code>store</code> and at the Responses API by name. And last, ordering: rows arriving out of sequence must be sorted by <code>created</code> before any transition is read off them, since an unsorted list invents transitions that never happened.",
"test_py_file": "test_openai_fingerprint_drift.py",
"test_py": '''from openai_fingerprint_drift import (by_model, flatten, interleaved, iso,
                                     repair_lines, transitions, verdict, within)

DAY = 86400


def page(*rows):
    return {"object": "list", "data": list(rows), "has_more": False}


def completion(cid, created, model, fingerprint):
    return {"id": cid, "object": "chat.completion", "created": created,
            "model": model, "system_fingerprint": fingerprint}


def test_two_fingerprints_in_order_are_the_finding_with_a_date():
    rows = flatten([page(completion("c_1", 1000, "gpt-5.6-sol", "fp_aa11"),
                         completion("c_2", 2000, "gpt-5.6-sol", "fp_aa11"),
                         completion("c_3", 3000, "gpt-5.6-sol", "fp_bb22"))])
    entries = by_model(rows)["gpt-5.6-sol"]
    assert transitions(entries) == [(3000, "fp_aa11", "fp_bb22")]
    state, detail = verdict("gpt-5.6-sol", entries)
    assert state == "fingerprint-moved"
    assert "2 backend configurations" in detail and "switching once" in detail
    assert iso(3000) == "1970-01-01T00:50:00Z"
    assert any("not a test oracle" in line or "test oracle" in line
               for line in repair_lines(state))


def test_an_absent_fingerprint_is_a_finding_and_never_a_quiet_pass():
    rows = flatten([page(completion("c_1", 1000, "gpt-5.6-terra", None),
                         completion("c_2", 2000, "gpt-5.6-terra", ""))])
    entries = by_model(rows)["gpt-5.6-terra"]
    assert transitions(entries) == []
    state, detail = verdict("gpt-5.6-terra", entries)
    assert state == "fingerprint-absent"
    assert "even in principle" in detail
    lines = repair_lines(state)
    assert any("no signal to alarm on" in line for line in lines)
    # Never phrased as stability. Nothing was observed.
    assert not any("stable" in line for line in lines)


def test_an_interleaved_fleet_is_separated_from_one_dated_switchover():
    mixed = [{"fingerprint": "fp_aa11"}, {"fingerprint": "fp_bb22"},
             {"fingerprint": "fp_aa11"}]
    once = [{"fingerprint": "fp_aa11"}, {"fingerprint": "fp_aa11"},
            {"fingerprint": "fp_bb22"}]
    assert interleaved(mixed) and not interleaved(once)
    state, detail = verdict("gpt-5.6-sol", mixed)
    assert state == "fingerprint-moved"
    assert "more than one configuration is being served at once" in detail
    assert any("minutes apart" in line for line in repair_lines(state, True))
    assert not any("minutes apart" in line for line in repair_lines(state, False))


def test_one_fingerprint_is_a_reading_rather_than_a_comparison():
    single = [{"fingerprint": "fp_aa11"}]
    assert verdict("gpt-5.6-sol", single)[0] == "single-observation"
    steady = [{"fingerprint": "fp_aa11"}] * 40
    state, detail = verdict("gpt-5.6-sol", steady)
    assert state == "fingerprint-stable"
    assert "best effort" in detail
    assert any("not a promise" in line for line in repair_lines(state))


def test_an_empty_listing_points_at_store_and_at_the_responses_api():
    state, detail = verdict("(any model)", [])
    assert state == "nothing-stored"
    assert "no stored completions" in detail
    lines = repair_lines(state)
    assert any("store: true" in line for line in lines)
    assert any("Responses API" in line and "cannot be listed" in line
               for line in lines)


def test_rows_are_ordered_before_transitions_are_read_off_them():
    rows = flatten([page(completion("c_2", 2000, "m", "fp_aa11"),
                         completion("c_3", 3000, "m", "fp_bb22"),
                         completion("c_1", 1000, "m", "fp_aa11"))])
    # Unsorted, this reads as two transitions. Sorted, it is one.
    assert len(transitions(rows)) == 2
    assert transitions(by_model(rows)["m"]) == [(3000, "fp_aa11", "fp_bb22")]
    assert len(within(by_model(rows)["m"], 1500)) == 2
    assert within(rows, 0) == rows
    assert iso("nonsense") == "" and iso(None) == ""
''',
"test_js_file": "openai-fingerprint-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { byModel, flatten, interleaved, iso, repairLines, transitions, verdict,
         within } from './openai-fingerprint-drift.mjs';

const page = (...rows) => ({ object: 'list', data: rows, has_more: false });
const completion = (id, created, model, system_fingerprint) =>
  ({ id, object: 'chat.completion', created, model, system_fingerprint });

test('two fingerprints in order are the finding with a date', () => {
  const rows = flatten([page(completion('c_1', 1000, 'gpt-5.6-sol', 'fp_aa11'),
                             completion('c_2', 2000, 'gpt-5.6-sol', 'fp_aa11'),
                             completion('c_3', 3000, 'gpt-5.6-sol', 'fp_bb22'))]);
  const entries = byModel(rows)['gpt-5.6-sol'];
  assert.deepEqual(transitions(entries), [[3000, 'fp_aa11', 'fp_bb22']]);
  const [state, detail] = verdict('gpt-5.6-sol', entries);
  assert.equal(state, 'fingerprint-moved');
  assert.ok(detail.includes('2 backend configurations'));
  assert.ok(detail.includes('switching once'));
  assert.equal(iso(3000), '1970-01-01T00:50:00Z');
  assert.ok(repairLines(state).some((l) => l.includes('test oracle')));
});

test('an absent fingerprint is a finding and never a quiet pass', () => {
  const rows = flatten([page(completion('c_1', 1000, 'gpt-5.6-terra', null),
                             completion('c_2', 2000, 'gpt-5.6-terra', ''))]);
  const entries = byModel(rows)['gpt-5.6-terra'];
  assert.deepEqual(transitions(entries), []);
  const [state, detail] = verdict('gpt-5.6-terra', entries);
  assert.equal(state, 'fingerprint-absent');
  assert.ok(detail.includes('even in principle'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('no signal to alarm on')));
  assert.ok(!lines.some((l) => l.includes('stable')));
});

test('an interleaved fleet is separated from one dated switchover', () => {
  const mixed = [{ fingerprint: 'fp_aa11' }, { fingerprint: 'fp_bb22' },
                 { fingerprint: 'fp_aa11' }];
  const once = [{ fingerprint: 'fp_aa11' }, { fingerprint: 'fp_aa11' },
                { fingerprint: 'fp_bb22' }];
  assert.ok(interleaved(mixed));
  assert.ok(!interleaved(once));
  const [state, detail] = verdict('gpt-5.6-sol', mixed);
  assert.equal(state, 'fingerprint-moved');
  assert.ok(detail.includes('more than one configuration is being served at once'));
  assert.ok(repairLines(state, true).some((l) => l.includes('minutes apart')));
  assert.ok(!repairLines(state, false).some((l) => l.includes('minutes apart')));
});

test('one fingerprint is a reading rather than a comparison', () => {
  assert.equal(verdict('gpt-5.6-sol', [{ fingerprint: 'fp_aa11' }])[0],
               'single-observation');
  const steady = Array.from({ length: 40 }, () => ({ fingerprint: 'fp_aa11' }));
  const [state, detail] = verdict('gpt-5.6-sol', steady);
  assert.equal(state, 'fingerprint-stable');
  assert.ok(detail.includes('best effort'));
  assert.ok(repairLines(state).some((l) => l.includes('not a promise')));
});

test('an empty listing points at store and at the responses api', () => {
  const [state, detail] = verdict('(any model)', []);
  assert.equal(state, 'nothing-stored');
  assert.ok(detail.includes('no stored completions'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('store: true')));
  assert.ok(lines.some((l) => l.includes('Responses API') && l.includes('cannot be listed')));
});

test('rows are ordered before transitions are read off them', () => {
  const rows = flatten([page(completion('c_2', 2000, 'm', 'fp_aa11'),
                             completion('c_3', 3000, 'm', 'fp_bb22'),
                             completion('c_1', 1000, 'm', 'fp_aa11'))]);
  assert.equal(transitions(rows).length, 2);
  assert.deepEqual(transitions(byModel(rows).m), [[3000, 'fp_aa11', 'fp_bb22']]);
  assert.equal(within(byModel(rows).m, 1500).length, 2);
  assert.deepEqual(within(rows, 0), rows);
  assert.equal(iso('nonsense'), '');
  assert.equal(iso(null), '');
});
''',
"faq": [
 ("Why not just send one request and compare the fingerprint?",
  "Because that generates a completion and bills for it, and no script in this section does that. It is also the weaker measurement. A canary tells you which backend configuration served one request at the moment you ran the script; your stored completions tell you which configurations served the traffic whose outputs you cached, tested against and shipped. The evidence is already in the account, it covers the window you care about, and reading it costs nothing."),
 ("Our completions are not stored. Can we still check this?",
  "Not through the API, and the script says so as a finding rather than pretending the run was clean. Listing only returns chat completions created with store set to true, and a Zero Data Retention organization will never have any. The options are to store a representative sample of traffic, or to accept that reproducibility has no evidence behind it and stop depending on it. Both are decisions worth making explicitly."),
 ("We moved to the Responses API. What is the equivalent?",
  "There is not one, and that is the honest answer. The Response object carries no system_fingerprint, and /v1/responses has no list endpoint, so neither half of this reading survives the migration. If reproducibility matters to you, that is an argument for keeping a stored sample on Chat Completions, or for caching your own responses so determinism is a property of your infrastructure rather than a favour from someone else's."),
 ("The fingerprint is null on our model. Is that a bug?",
  "No. The field is optional, and it is empty on a good deal of current traffic. What it means is specific and worth being blunt about: there is no signal, so a backend change cannot be detected here even in principle, and any determinism strategy for that model is running without instrumentation. The script reports it as a finding for that reason. A run that called it stable would be claiming an observation it never made."),
 ("Does pinning a model snapshot fix this?",
  "It removes one of the two moving parts, not both. Pinning stops the weights changing under a floating alias, which is a separate published note and a good idea regardless. The fingerprint describes the backend configuration the model runs with, which includes infrastructure beyond the weights, so it can move under a pinned snapshot as well. Pin the snapshot, record the fingerprint next to every baseline, and assert on structure rather than on exact strings."),
],
"related": [REL_ALIAS, REL_CACHE_STEP, REL_TOKENS],
"citations": [CITE_OAI_CHAT, CITE_OAI_SEED, CITE_OAI_MODELS, CITE_OAI_DATA],
},
{
"slug": "previous-response-id-chain-broken",
"title": "previous_response_id 404s once the parent has aged out",
"description": "Response objects are saved 30 days by default. Walk each recorded chain with GET /v1/responses/{id} to find the links already gone and the ones days away.",
"h1": "previous_response_id 404s once the parent has aged out",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["previous_response_id 404 not found openai",
             "responses api conversation state expired 30 days",
             "openai response id no longer exists mid thread",
             "previous_response_id vs conversations object",
             "responses api retention 30 days store true"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, and a file of response ids: /v1/responses has no list endpoint, so the chains have to start from ids your application recorded.",
"lead": "The support assistant remembers everything, which is the entire product. A customer opens a thread in March, adds to it in April, and comes back in June to ask about the thing they described the first time. This time the request 404s. Not the model, not the key, not the prompt: the id of the message before this one, which your code has been passing forward faithfully for three months. Server-side conversation state is a convenience with an expiry date on it, and nobody read the date.",
"short_answer": """<p>Walk the chain before a customer does. With a <strong>project key set to Read Only</strong>, take the response ids your application recorded and call <code>GET /v1/responses/{response_id}</code>. A <strong>404</strong> is a link that is already gone, and the next turn on that thread will fail. A 200 gives you <code>created_at</code> and <code>previous_response_id</code>, so the script hops upward and repeats until it reaches a root or a gap.</p>
<p>The clock is documented and it is short. <strong>Response objects are saved for 30 days by default.</strong> So a chain is only as durable as its oldest surviving link, and the script computes the runway from that link rather than from the newest one, which is the mistake the calendar invites you to make.</p>
<p>There is one documented exception and it is also the repair: a response attached to a <strong>conversation</strong> has its items persisted with no 30-day TTL. The script reads the <code>conversation</code> field off every link it resolves and reports a chain whose history lives in a conversation object separately, because that history survives whether or not the individual response objects do.</p>
<p>You cannot enumerate this. <code>/v1/responses</code> has no list endpoint, so the ids come from your own records and every verdict is bounded by the chains you handed over. If you are not recording response ids, that is the first repair, and it is a column.</p>""",
"problem": """<p><code>previous_response_id</code> looks like memory and behaves like a cache. It chains server-side state so that a turn only has to carry the newest message, which is genuinely useful: less bandwidth, less assembly code, no local history store. What it does not look like, anywhere in the call site, is a reference into storage with a retention policy.</p>
<p>Response objects are saved for 30 days by default. Past that the parent is gone, and the next request that names it comes back as a 404 that points at <code>previous_response_id</code>. Nothing warns at write time, because at write time everything is fine; the break happens on the turn after the gap, which may be weeks later and will be in front of whoever is using the product.</p>
<p>Storage is also conditional in the first place. A response only exists to be chained from if the call that created it was stored, which is the default and is not universal: a Zero Data Retention organization does not get stored responses at all, a call that opted out has nothing to chain from, and a cleanup sweep that deletes responses does the same damage as the clock does, only faster.</p>
<p>The failure shape is what makes this expensive. It is not uniform, so it does not look like an outage: the threads that break are the oldest ones, which correlate with your most engaged users, and they break one at a time. A dashboard sees a handful of 404s a day and a rounding error in the error rate. A customer sees an assistant that forgot a conversation they have been having for a month.</p>""",
"why": """<p><strong>A chain is exactly as durable as its oldest surviving link, and that is not the link you would think to check.</strong> The natural instinct is to test the most recent id, which is the one that is freshest and will always pass. The turn that fails is the one that walks back to a parent recorded a month ago. So the script hops upward until it reaches a root or a gap, and it computes the runway from the oldest link it found rather than from the leaf it started at.</p>
<p><strong>A 200 is the proof of storage, because there is no field for it.</strong> The Response object does not carry a <code>store</code> flag to read back, so the honest test of "was this stored" is whether retrieving it works. The script says exactly that rather than reporting a field that does not exist, and it treats a 404 as one fact with two possible causes &mdash; it aged out, or it was never stored &mdash; which are separated by whether the chain has other links that resolve.</p>
<p><strong>The conversation exception is a different object with a different rule, and it is the repair.</strong> Items attached to a conversation are persisted with no 30-day TTL, so a thread built on a conversation does not have this failure mode. That is why the script reads the <code>conversation</code> field on every link it resolves: a chain that is already conversation-backed has its history somewhere durable, whatever happens to the individual response objects, and it is not this note's problem.</p>
<p><strong>This clock is not the batch clock.</strong> The section has notes about a batch abandoning unfinished rows after a 24-hour completion window, and about batch error files that expire before anyone reads them. Those are deadlines on a job you submitted. This is a retention policy on an object your application keeps pointing at, it fails forward one turn at a time rather than all at once, and its repair is a design change rather than a resubmission.</p>
<p><strong>Every verdict here is bounded by the ids you supplied.</strong> There is no list endpoint for <code>/v1/responses</code>, so this cannot sweep the account; it can only grade the chains you know about. That makes the sample part of the finding, which is why the script prints how many chains it walked next to what it concluded, and why the first repair for an application that keeps no ids is to start keeping them.</p>""",
"steps": [
 {"h": "Export the newest response id per thread",
  "body": """<p>One id per line, from your own records. The newest id in each thread is the right starting point because the script walks upward from it; starting at a root tells you nothing about the chain hanging below it. Blank lines and <code>#</code> comments are ignored, so a file exported straight out of a query works.</p>"""},
 {"h": "Use a project key set to Read Only",
  "body": """<p>Every call is <code>GET /v1/responses/{response_id}</code>. Nothing is created, nothing is deleted, and no completion is generated. An admin key is the wrong credential: stored responses are project data.</p>"""},
 {"h": "Walk each chain upward to a root or a gap",
  "body": """<p>On a 200 the script reads <code>created_at</code>, <code>previous_response_id</code> and <code>conversation</code>, then follows the parent. It stops at a response with no parent, at the first 404, or at <code>--max-hops</code>, which exists so that a chain of a thousand turns does not become a thousand requests. A chain cut short by the hop limit is reported as unfinished rather than as healthy.</p>"""},
 {"h": "Read the runway off the oldest link, not the newest",
  "body": """<p>The script reports the age of the oldest surviving link in each chain and the days remaining against the documented 30-day retention. <code>--warn-days</code> sets how close to the edge counts as a finding; five is a reasonable default because it is longer than a weekend.</p>"""},
 {"h": "Take the repair, which is a design change",
  "body": """<p>Either move the thread onto a conversation object, whose items are persisted with no 30-day TTL, or keep the full message history in your own store and replay it. Before continuing an old thread, verify the parent resolves and fall back to replaying local history when it does not. The script prints this and changes nothing.</p>"""},
],
"verify": """<p>Re-run with the same id file after the change. Chains that moved onto a conversation come back as <code>conversation-backed</code>; chains you rebuilt from local history come back as roots, because there is no longer a parent to walk to. The number that should keep falling on every run is the count of chains whose oldest link is inside the warning window, and that is the one worth putting on a schedule &mdash; weekly, against the threads that have not been touched in a fortnight.</p>
<pre><code class="language-bash">python3 openai_response_chain_probe.py --ids thread-heads.txt --warn-days 5
# resp_c9  chain of 4, oldest resp_a1 at 2026-07-24T09:02:11Z, 38.2 days old
# chain-broken         resp_c9: the parent resp_a1 no longer resolves, so the
#                      next turn on this thread will 404
#   repair: fall back to replaying local history for this thread, and stop
#           chaining from an id you did not verify.
# resp_f2  chain of 3, oldest resp_d7 at 2026-08-05T14:40:03Z, 26.4 days old
# chain-expiring       resp_f2: the oldest link is 26.4 days old, so this chain
#                      has about 3.6 days of the documented 30 day retention left
# resp_k4  chain of 2, conversation conv_x1 on every link
# conversation-backed  resp_k4: items attached to a conversation are persisted
#                      with no 30 day TTL
# 3 chain(s) walked, 2 finding(s)</code></pre>""",
"code_intro": "One GET per link and six pure functions. <code>parse_ids</code>, which reads a file exported by somebody in a hurry, ignoring blanks, comments and duplicates; <code>link_row</code>, which reduces a retrieved response to the four fields that matter and never invents a <code>store</code> flag, because the object does not carry one; <code>age_days</code> and <code>runway_days</code>, which take the clock as an argument so the whole retention calculation is testable without one; <code>oldest_link</code>, which is where the finding actually lives; and <code>classify_chain</code>, which grades a walked chain and treats a chain cut short by the hop limit as unfinished rather than as healthy.",
"py_file": "openai_response_chain_probe.py",
"py": '''"""Walk recorded previous_response_id chains and find the links already gone.

Read only. One GET of /v1/responses/{response_id} per link, and nothing else.
No completion is created, nothing is stored and nothing is deleted.

Response objects are saved for 30 days by default, so a chain is exactly as
durable as its oldest surviving link. This walks upward from the newest id you
recorded to a root or to a gap, and reports the runway from the oldest link
rather than from the newest.

The one documented exception is also the repair: a response attached to a
conversation has its items persisted with no 30 day TTL, so a conversation
backed chain keeps its history whatever happens to the response objects.

/v1/responses has no list endpoint, so the ids come from your own records and
every verdict is bounded by the chains you supply.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_response_chain_probe")

BASE_URL = "https://api.openai.com/v1/responses"

# The documented default: response objects are saved for 30 days.
RETENTION_DAYS = 30

FINDINGS = ("chain-broken", "chain-expiring", "chain-unreadable")


def parse_ids(text):
    """Response ids from a file. Pure. Blanks, comments and repeats dropped."""
    seen = []
    for line in str(text or "").splitlines():
        item = line.split("#", 1)[0].strip()
        if item and item not in seen:
            seen.append(item)
    return seen


def link_row(body):
    """One retrieved response, reduced. Pure. Four fields and no invention.

    There is deliberately no "stored" field here. The Response object does not
    carry a store flag, so the only honest evidence that a response was stored
    is that retrieving it worked, and that is recorded as the status code.
    """
    body = body if isinstance(body, dict) else {}
    conversation = body.get("conversation")
    if isinstance(conversation, dict):
        conversation = conversation.get("id")
    try:
        created = int(body.get("created_at") or 0)
    except (TypeError, ValueError):
        created = 0
    return {"id": str(body.get("id") or ""),
            "created_at": created,
            "previous_response_id": str(body.get("previous_response_id") or ""),
            "conversation": str(conversation or ""),
            "status": str(body.get("status") or "")}


def age_days(created_at, now):
    """Age of one link in days. Pure. The clock is an argument."""
    try:
        created = int(created_at)
        now = int(now)
    except (TypeError, ValueError):
        return None
    if created <= 0:
        return None
    return (now - created) / 86400.0


def oldest_link(chain):
    """The link that decides the chain. Pure. None for an empty chain."""
    usable = [row for row in chain or [] if int(row.get("created_at") or 0) > 0]
    if not usable:
        return None
    return min(usable, key=lambda row: int(row["created_at"]))


def runway_days(chain, now, retention=RETENTION_DAYS):
    """Days left on the oldest link. Pure. None when nothing is datable."""
    row = oldest_link(chain)
    if row is None:
        return None
    age = age_days(row["created_at"], now)
    if age is None:
        return None
    return retention - age


def classify_chain(head, chain, gap, unreadable, truncated, now, warn_days):
    """Grade one walked chain. Pure. Returns (state, detail)."""
    if unreadable:
        return ("chain-unreadable",
                "%s: %s, so nothing about this chain was established"
                % (head, unreadable))
    if gap:
        others = len(chain)
        if others:
            return ("chain-broken",
                    "%s: the parent %s no longer resolves, so the next turn on "
                    "this thread will 404" % (head, gap))
        return ("chain-broken",
                "%s: this id itself does not resolve. It has either aged out of "
                "the 30 day retention or was never stored" % head)
    if not chain:
        return ("nothing-walked", "%s: no links were read" % head)

    conversations = {row.get("conversation") for row in chain}
    if conversations and "" not in conversations:
        return ("conversation-backed",
                "%s: items attached to a conversation are persisted with no 30 "
                "day TTL" % head)

    left = runway_days(chain, now)
    if left is None:
        return ("undatable",
                "%s: no link carried a usable created_at, so the runway cannot "
                "be computed" % head)
    if left <= 0:
        return ("chain-broken",
                "%s: the oldest link is past the documented %d day retention "
                "and is only resolving on borrowed time"
                % (head, RETENTION_DAYS))
    if left <= warn_days:
        row = oldest_link(chain)
        return ("chain-expiring",
                "%s: the oldest link is %.1f days old, so this chain has about "
                "%.1f days of the documented %d day retention left"
                % (head, age_days(row["created_at"], now), left, RETENTION_DAYS))
    if truncated:
        return ("chain-unfinished",
                "%s: stopped at the hop limit before reaching a root, so the "
                "oldest link was never seen" % head)
    return ("chain-intact",
            "%s: walked to a root with %.1f days left on the oldest link"
            % (head, left))


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    move = ("move this thread onto a conversation object, whose items are "
            "persisted with no 30 day TTL, or keep the full message history in "
            "your own store and replay it.")
    if state == "chain-broken":
        return ["fall back to replaying local history for this thread, and stop "
                "chaining from an id you did not verify.", move]
    if state == "chain-expiring":
        return [move,
                "until then, verify the parent resolves before continuing an "
                "old thread rather than discovering it inside a user request."]
    if state == "chain-unreadable":
        return ["the key could not read this response. Check that it belongs to "
                "the project that created it before concluding anything about "
                "retention."]
    if state == "chain-unfinished":
        return ["raise --max-hops for this thread. A chain graded without "
                "reaching its oldest link has not been graded."]
    if state == "undatable":
        return ["the links resolved but carried no created_at, which is odd "
                "enough to read one of them by hand before trusting the rest."]
    return []


def retrieve(response_id, key, timeout=30):
    """One GET. Returns (status, body). A 404 is the answer, not an error."""
    try:
        r = requests.get("%s/%s" % (BASE_URL, response_id),
                         headers={"Authorization": "Bearer " + key},
                         timeout=timeout)
    except requests.RequestException as exc:
        log.debug("retrieve of %s failed: %s", response_id, exc)
        return (None, None)
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, None)


def walk(head, key, max_hops):
    """Follow one chain upward. Returns (chain, gap, unreadable, truncated)."""
    chain = []
    current = head
    for _ in range(max_hops):
        status, body = retrieve(current, key)
        if status == 404:
            return (chain, current, "", False)
        if status in (401, 403):
            return (chain, "", "HTTP %d reading %s" % (status, current), False)
        if status != 200:
            return (chain, "", "HTTP %s reading %s" % (status, current), False)
        row = link_row(body)
        chain.append(row)
        if not row["previous_response_id"]:
            return (chain, "", "", False)
        current = row["previous_response_id"]
    return (chain, "", "", True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True,
                    help="file of response ids, newest per thread, one per line")
    ap.add_argument("--max-hops", type=int, default=20,
                    help="how far up one chain to walk")
    ap.add_argument("--warn-days", type=float, default=5.0,
                    help="days of remaining retention that count as a finding")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only. Every "
                  "call is a GET of /v1/responses/{response_id}")
        return 2
    try:
        with open(args.ids, "r", encoding="utf-8") as fh:
            heads = parse_ids(fh.read())
    except OSError as exc:
        log.error("could not read %s: %s", args.ids, exc)
        return 2
    if not heads:
        log.error("no response ids in %s. /v1/responses cannot be listed, so "
                  "the chains have to start from ids you recorded", args.ids)
        return 2

    now = int(time.time())
    findings = 0
    for head in heads:
        chain, gap, unreadable, truncated = walk(head, key, args.max_hops)
        row = oldest_link(chain)
        if row:
            age = age_days(row["created_at"], now)
            log.info("%-10s chain of %d, oldest %s, %.1f days old",
                     head, len(chain), row["id"], age or 0.0)
        else:
            log.info("%-10s chain of %d", head, len(chain))

        state, detail = classify_chain(head, chain, gap, unreadable, truncated,
                                       now, args.warn_days)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s", state, detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d chain(s) walked, %d finding(s)", len(heads), findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-response-chain-probe.mjs",
"js": '''/**
 * Walk recorded previous_response_id chains and find the links already gone.
 *
 * Read only. One GET of /v1/responses/{response_id} per link. No completion is
 * created, nothing is stored and nothing is deleted.
 *
 * Response objects are saved for 30 days by default, so a chain is only as
 * durable as its oldest surviving link. A response attached to a conversation
 * has its items persisted with no 30 day TTL, which is the repair.
 *
 * /v1/responses has no list endpoint, so the ids come from your own records.
 */
import { readFile } from 'node:fs/promises';

const BASE_URL = 'https://api.openai.com/v1/responses';

export const RETENTION_DAYS = 30;

const FINDINGS = new Set(['chain-broken', 'chain-expiring', 'chain-unreadable']);

/** Response ids from a file. Pure. Blanks, comments and repeats dropped. */
export function parseIds(text) {
  const seen = [];
  for (const line of String(text ?? '').split('\\n')) {
    const item = line.split('#')[0].trim();
    if (item && !seen.includes(item)) seen.push(item);
  }
  return seen;
}

/** One retrieved response, reduced. Pure. Four fields and no invention. */
export function linkRow(body) {
  const row = (body && typeof body === 'object') ? body : {};
  const conversation = (row.conversation && typeof row.conversation === 'object')
    ? row.conversation.id : row.conversation;
  const created = Number(row.created_at ?? 0);
  return {
    id: String(row.id ?? ''),
    created_at: Number.isFinite(created) ? Math.trunc(created) : 0,
    previous_response_id: String(row.previous_response_id ?? ''),
    conversation: String(conversation ?? ''),
    status: String(row.status ?? ''),
  };
}

/** Age of one link in days. Pure. The clock is an argument. */
export function ageDays(createdAt, now) {
  const created = Number(createdAt);
  const at = Number(now);
  if (!Number.isFinite(created) || !Number.isFinite(at) || created <= 0) return null;
  return (at - created) / 86400;
}

/** The link that decides the chain. Pure. Null for an empty chain. */
export function oldestLink(chain) {
  const usable = (chain ?? []).filter((row) => Number(row?.created_at ?? 0) > 0);
  if (!usable.length) return null;
  return usable.reduce((a, b) => (Number(a.created_at) <= Number(b.created_at) ? a : b));
}

/** Days left on the oldest link. Pure. Null when nothing is datable. */
export function runwayDays(chain, now, retention = RETENTION_DAYS) {
  const row = oldestLink(chain);
  if (!row) return null;
  const age = ageDays(row.created_at, now);
  return age === null ? null : retention - age;
}

/** Grade one walked chain. Pure. Returns [state, detail]. */
export function classifyChain(head, chain, gap, unreadable, truncated, now, warnDays) {
  if (unreadable) {
    return ['chain-unreadable',
      `${head}: ${unreadable}, so nothing about this chain was established`];
  }
  if (gap) {
    if ((chain ?? []).length) {
      return ['chain-broken',
        `${head}: the parent ${gap} no longer resolves, so the next turn on this `
        + 'thread will 404'];
    }
    return ['chain-broken',
      `${head}: this id itself does not resolve. It has either aged out of the `
      + '30 day retention or was never stored'];
  }
  if (!(chain ?? []).length) return ['nothing-walked', `${head}: no links were read`];

  const conversations = new Set(chain.map((row) => row.conversation ?? ''));
  if (!conversations.has('')) {
    return ['conversation-backed',
      `${head}: items attached to a conversation are persisted with no 30 day TTL`];
  }

  const left = runwayDays(chain, now);
  if (left === null) {
    return ['undatable',
      `${head}: no link carried a usable created_at, so the runway cannot be computed`];
  }
  if (left <= 0) {
    return ['chain-broken',
      `${head}: the oldest link is past the documented ${RETENTION_DAYS} day `
      + 'retention and is only resolving on borrowed time'];
  }
  if (left <= warnDays) {
    const row = oldestLink(chain);
    return ['chain-expiring',
      `${head}: the oldest link is ${ageDays(row.created_at, now).toFixed(1)} days `
      + `old, so this chain has about ${left.toFixed(1)} days of the documented `
      + `${RETENTION_DAYS} day retention left`];
  }
  if (truncated) {
    return ['chain-unfinished',
      `${head}: stopped at the hop limit before reaching a root, so the oldest `
      + 'link was never seen'];
  }
  return ['chain-intact',
    `${head}: walked to a root with ${left.toFixed(1)} days left on the oldest link`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const move = 'move this thread onto a conversation object, whose items are '
    + 'persisted with no 30 day TTL, or keep the full message history in your '
    + 'own store and replay it.';
  if (state === 'chain-broken') {
    return ['fall back to replaying local history for this thread, and stop '
      + 'chaining from an id you did not verify.', move];
  }
  if (state === 'chain-expiring') {
    return [move, 'until then, verify the parent resolves before continuing an '
      + 'old thread rather than discovering it inside a user request.'];
  }
  if (state === 'chain-unreadable') {
    return ['the key could not read this response. Check that it belongs to the '
      + 'project that created it before concluding anything about retention.'];
  }
  if (state === 'chain-unfinished') {
    return ['raise --max-hops for this thread. A chain graded without reaching '
      + 'its oldest link has not been graded.'];
  }
  if (state === 'undatable') {
    return ['the links resolved but carried no created_at, which is odd enough '
      + 'to read one of them by hand before trusting the rest.'];
  }
  return [];
}

async function retrieve(responseId, key) {
  try {
    const res = await fetch(`${BASE_URL}/${responseId}`,
      { headers: { Authorization: `Bearer ${key}` } });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    return [res.status, body];
  } catch {
    return [null, null];
  }
}

async function walk(head, key, maxHops) {
  const chain = [];
  let current = head;
  for (let hop = 0; hop < maxHops; hop += 1) {
    const [status, body] = await retrieve(current, key);
    if (status === 404) return [chain, current, '', false];
    if (status !== 200) return [chain, '', `HTTP ${status} reading ${current}`, false];
    const row = linkRow(body);
    chain.push(row);
    if (!row.previous_response_id) return [chain, '', '', false];
    current = row.previous_response_id;
  }
  return [chain, '', '', true];
}

function args(argv) {
  const out = { maxHops: 20, warnDays: 5 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--ids') out.ids = argv[i += 1];
    else if (argv[i] === '--max-hops') out.maxHops = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--warn-days') out.warnDays = Number(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only. Every '
      + 'call is a GET of /v1/responses/{response_id}');
    process.exitCode = 2;
    return;
  }
  if (!opts.ids) {
    console.error('usage: --ids <file> [--max-hops 20] [--warn-days 5]');
    process.exitCode = 2;
    return;
  }
  let heads;
  try {
    heads = parseIds(await readFile(opts.ids, 'utf8'));
  } catch (err) {
    console.error(`could not read ${opts.ids}: ${err.message}`);
    process.exitCode = 2;
    return;
  }
  if (!heads.length) {
    console.error(`no response ids in ${opts.ids}. /v1/responses cannot be `
      + 'listed, so the chains have to start from ids you recorded');
    process.exitCode = 2;
    return;
  }

  const now = Math.trunc(Date.now() / 1000);
  let findings = 0;
  for (const head of heads) {
    const [chain, gap, unreadable, truncated] = await walk(head, key, opts.maxHops);
    const row = oldestLink(chain);
    if (row) {
      console.log(`${head.padEnd(10)} chain of ${chain.length}, oldest ${row.id}, `
        + `${(ageDays(row.created_at, now) ?? 0).toFixed(1)} days old`);
    } else {
      console.log(`${head.padEnd(10)} chain of ${chain.length}`);
    }
    const [state, detail] = classifyChain(head, chain, gap, unreadable, truncated,
                                          now, opts.warnDays);
    console.log(`${state.padEnd(20)} ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }
  console.log(`${heads.length} chain(s) walked, ${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the failure the note is named after: a chain whose parent 404s comes back as <code>chain-broken</code>, names the missing parent, and says that the next turn will fail rather than that a request failed. The second is the one that decides whether the script is useful at all &mdash; the runway has to be computed from the oldest link, so a chain with a fresh leaf and a month-old root is a finding, and a test asserts that reading the newest link instead would have called it healthy. The third is the documented exception: every link carrying a conversation is not this note's problem, and mixed chains do not qualify for it. Then the hop limit, which must produce <code>chain-unfinished</code> rather than a clean bill on a chain whose oldest link was never seen. Then <code>link_row</code>, asserted to invent no <code>store</code> field, because the object does not have one. And last the id file, read the way a file exported in a hurry actually looks.",
"test_py_file": "test_openai_response_chain_probe.py",
"test_py": '''from openai_response_chain_probe import (RETENTION_DAYS, age_days,
                                        classify_chain, link_row, oldest_link,
                                        parse_ids, repair_lines, runway_days)

NOW = 1_800_000_000
DAY = 86400


def link(rid, days_old, parent="", conversation=""):
    return link_row({"id": rid, "created_at": NOW - int(days_old * DAY),
                     "previous_response_id": parent,
                     "conversation": ({"id": conversation} if conversation
                                      else None),
                     "status": "completed"})


def test_a_missing_parent_is_the_finding_and_names_the_next_turn():
    chain = [link("resp_c9", 1.0, parent="resp_a1")]
    state, detail = classify_chain("resp_c9", chain, "resp_a1", "", False,
                                   NOW, 5.0)
    assert state == "chain-broken"
    assert "resp_a1 no longer resolves" in detail
    assert "next turn on this thread will 404" in detail
    lines = repair_lines(state)
    assert any("replaying local history" in line for line in lines)
    assert any("no 30 day TTL" in line for line in lines)

    # The head itself missing is the same verdict with a different sentence,
    # because a 404 there has two causes and the script names both.
    state, detail = classify_chain("resp_c9", [], "resp_c9", "", False, NOW, 5.0)
    assert state == "chain-broken"
    assert "aged out" in detail and "never stored" in detail


def test_the_runway_comes_from_the_oldest_link_and_not_the_newest():
    chain = [link("resp_f2", 0.5, parent="resp_e1"),
             link("resp_e1", 12.0, parent="resp_d7"),
             link("resp_d7", 26.4)]
    assert oldest_link(chain)["id"] == "resp_d7"
    assert abs(runway_days(chain, NOW) - (RETENTION_DAYS - 26.4)) < 0.01
    state, detail = classify_chain("resp_f2", chain, "", "", False, NOW, 5.0)
    assert state == "chain-expiring"
    assert "26.4 days old" in detail and "3.6 days" in detail
    # Read from the newest link this chain looks like it has 29.5 days left.
    assert age_days(chain[0]["created_at"], NOW) < 1.0


def test_a_conversation_backed_chain_is_not_this_note():
    chain = [link("resp_k4", 1.0, parent="resp_k3", conversation="conv_x1"),
             link("resp_k3", 44.0, conversation="conv_x1")]
    state, detail = classify_chain("resp_k4", chain, "", "", False, NOW, 5.0)
    assert state == "conversation-backed"
    assert "no 30 day TTL" in detail
    assert repair_lines(state) == []
    # One link without a conversation is not a conversation backed chain.
    mixed = [chain[0], link("resp_k3", 44.0)]
    assert classify_chain("resp_k4", mixed, "", "", False, NOW, 5.0)[0] \\
        == "chain-broken"


def test_a_chain_cut_short_by_the_hop_limit_is_not_graded_healthy():
    chain = [link("resp_z9", 1.0, parent="resp_z8"),
             link("resp_z8", 2.0, parent="resp_z7")]
    state, detail = classify_chain("resp_z9", chain, "", "", True, NOW, 5.0)
    assert state == "chain-unfinished"
    assert "oldest link was never seen" in detail
    assert any("--max-hops" in line for line in repair_lines(state))
    # The same chain walked to a root is intact.
    rooted = [chain[0], link("resp_z8", 2.0)]
    assert classify_chain("resp_z9", rooted, "", "", False, NOW, 5.0)[0] \\
        == "chain-intact"


def test_link_row_reads_four_fields_and_invents_no_store_flag():
    row = link_row({"id": "resp_a1", "created_at": 1700000000,
                    "previous_response_id": None,
                    "conversation": {"id": "conv_x1"}, "status": "completed"})
    assert row == {"id": "resp_a1", "created_at": 1700000000,
                   "previous_response_id": "", "conversation": "conv_x1",
                   "status": "completed"}
    assert "store" not in row and "stored" not in row
    assert link_row(None)["id"] == ""
    assert link_row({"created_at": "nonsense"})["created_at"] == 0
    assert age_days(0, NOW) is None and runway_days([], NOW) is None


def test_the_id_file_is_read_the_way_it_is_actually_exported():
    ids = parse_ids("resp_a1\\n\\n# heads exported 2026-08-30\\nresp_b2  # oldest\\n"
                    "resp_a1\\n   \\nresp_c3\\n")
    assert ids == ["resp_a1", "resp_b2", "resp_c3"]
    assert parse_ids("") == [] and parse_ids(None) == []
    state, detail = classify_chain("resp_a1", [], "", "HTTP 403 reading resp_a1",
                                   False, NOW, 5.0)
    assert state == "chain-unreadable"
    assert "nothing about this chain was established" in detail
''',
"test_js_file": "openai-response-chain-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { RETENTION_DAYS, ageDays, classifyChain, linkRow, oldestLink, parseIds,
         repairLines, runwayDays } from './openai-response-chain-probe.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;

const link = (id, daysOld, parent = '', conversation = '') => linkRow({
  id,
  created_at: NOW - Math.trunc(daysOld * DAY),
  previous_response_id: parent,
  conversation: conversation ? { id: conversation } : null,
  status: 'completed',
});

test('a missing parent is the finding and names the next turn', () => {
  const chain = [link('resp_c9', 1, 'resp_a1')];
  const [state, detail] = classifyChain('resp_c9', chain, 'resp_a1', '', false, NOW, 5);
  assert.equal(state, 'chain-broken');
  assert.ok(detail.includes('resp_a1 no longer resolves'));
  assert.ok(detail.includes('next turn on this thread will 404'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('replaying local history')));
  assert.ok(lines.some((l) => l.includes('no 30 day TTL')));

  const [headState, headDetail] = classifyChain('resp_c9', [], 'resp_c9', '', false, NOW, 5);
  assert.equal(headState, 'chain-broken');
  assert.ok(headDetail.includes('aged out') && headDetail.includes('never stored'));
});

test('the runway comes from the oldest link and not the newest', () => {
  const chain = [link('resp_f2', 0.5, 'resp_e1'),
                 link('resp_e1', 12, 'resp_d7'),
                 link('resp_d7', 26.4)];
  assert.equal(oldestLink(chain).id, 'resp_d7');
  assert.ok(Math.abs(runwayDays(chain, NOW) - (RETENTION_DAYS - 26.4)) < 0.01);
  const [state, detail] = classifyChain('resp_f2', chain, '', '', false, NOW, 5);
  assert.equal(state, 'chain-expiring');
  assert.ok(detail.includes('26.4 days old') && detail.includes('3.6 days'));
  assert.ok(ageDays(chain[0].created_at, NOW) < 1);
});

test('a conversation backed chain is not this note', () => {
  const chain = [link('resp_k4', 1, 'resp_k3', 'conv_x1'),
                 link('resp_k3', 44, '', 'conv_x1')];
  const [state, detail] = classifyChain('resp_k4', chain, '', '', false, NOW, 5);
  assert.equal(state, 'conversation-backed');
  assert.ok(detail.includes('no 30 day TTL'));
  assert.deepEqual(repairLines(state), []);
  const mixed = [chain[0], link('resp_k3', 44)];
  assert.equal(classifyChain('resp_k4', mixed, '', '', false, NOW, 5)[0], 'chain-broken');
});

test('a chain cut short by the hop limit is not graded healthy', () => {
  const chain = [link('resp_z9', 1, 'resp_z8'), link('resp_z8', 2, 'resp_z7')];
  const [state, detail] = classifyChain('resp_z9', chain, '', '', true, NOW, 5);
  assert.equal(state, 'chain-unfinished');
  assert.ok(detail.includes('oldest link was never seen'));
  assert.ok(repairLines(state).some((l) => l.includes('--max-hops')));
  const rooted = [chain[0], link('resp_z8', 2)];
  assert.equal(classifyChain('resp_z9', rooted, '', '', false, NOW, 5)[0], 'chain-intact');
});

test('linkRow reads four fields and invents no store flag', () => {
  const row = linkRow({ id: 'resp_a1', created_at: 1700000000,
                        previous_response_id: null,
                        conversation: { id: 'conv_x1' }, status: 'completed' });
  assert.deepEqual(row, { id: 'resp_a1', created_at: 1700000000,
                          previous_response_id: '', conversation: 'conv_x1',
                          status: 'completed' });
  assert.ok(!('store' in row) && !('stored' in row));
  assert.equal(linkRow(null).id, '');
  assert.equal(linkRow({ created_at: 'nonsense' }).created_at, 0);
  assert.equal(ageDays(0, NOW), null);
  assert.equal(runwayDays([], NOW), null);
});

test('the id file is read the way it is actually exported', () => {
  const ids = parseIds('resp_a1\\n\\n# heads exported 2026-08-30\\nresp_b2  # oldest\\n'
    + 'resp_a1\\n   \\nresp_c3\\n');
  assert.deepEqual(ids, ['resp_a1', 'resp_b2', 'resp_c3']);
  assert.deepEqual(parseIds(''), []);
  assert.deepEqual(parseIds(null), []);
  const [state, detail] = classifyChain('resp_a1', [], '', 'HTTP 403 reading resp_a1',
                                        false, NOW, 5);
  assert.equal(state, 'chain-unreadable');
  assert.ok(detail.includes('nothing about this chain was established'));
});
''',
"faq": [
 ("How long do stored responses actually last?",
  "Response objects are saved for 30 days by default. That is the number the script computes against, and it is the reason a thread that a customer returns to after a month is the one that breaks. The exception is documented and specific: any response attached to a conversation has its items persisted with no 30 day TTL. So the durability of a thread depends on which object you built it out of, not on how you feel about it."),
 ("Why walk the whole chain instead of checking the id we are about to use?",
  "Because the id you are about to use is the newest one, and it always passes. The request that fails is the one that resolves your parent, and its parent, back to the beginning of a conversation that started weeks ago. A chain is exactly as durable as its oldest surviving link, so a script that checked the leaf would report perfect health on a thread that is four days from breaking. That is the specific mistake this note exists to prevent, and there is a test that fails if the calculation ever moves to the newest link."),
 ("Can we just list our stored responses and audit all of them?",
  "No, and this is a real gap rather than an omission here. /v1/responses has no list endpoint: stored responses are reachable only by an id you already hold. So the chains have to come from your own records, and every verdict is bounded by the ids you supplied, which is why the script prints how many chains it walked next to how many findings it produced. If you are not recording response ids, that is the first repair and it costs a column."),
 ("Is a 404 always retention? It could be a delete, or a call that was never stored.",
  "It could be any of the three and the script says so instead of guessing. A 404 on the head id gets a sentence naming both possibilities, aged out or never stored. A 404 on a parent inside a chain whose other links resolve is stronger evidence of the clock, because storage was clearly working for that thread. Deletion looks identical from outside; if you run a cleanup sweep over responses, it is doing the same damage as the retention window, only faster."),
 ("Should we move to conversations, or keep our own history?",
  "Both are correct and they solve different problems. A conversation is an explicit, deletable object whose items are persisted with no 30 day TTL, which fixes the expiry without you building anything. Keeping the full message history in your own store fixes it as well and additionally makes your product portable, testable and replayable, at the cost of assembling every turn yourself. What is not an option is the third thing, which is chaining from an id nobody verified and finding out inside a user request."),
],
"related": [REL_TRUNC, REL_BATCH_EXP, REL_TOOLDEAD],
"citations": [CITE_OAI_STATE, CITE_OAI_RESP, CITE_OAI_DATA, CITE_OAI_ERRORS],
},
{
"slug": "fine-tune-job-failed-with-error-code",
"title": "The fine-tuning job failed and error.code was never read",
"description": "Job creation returns 200 and fails hours later. List the jobs, flag status failed, and print error.code, error.param and the events feed that explains them.",
"h1": "The fine-tuning job failed and error.code was never read",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["fine_tuning job status failed error code",
             "invalid_training_file unexpected file format openai",
             "fine tuning job stuck validating_files",
             "GET fine_tuning jobs events level error",
             "openai fine tune exceeded_quota"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only. Two read paths: GET /v1/fine_tuning/jobs and, for anything that failed, GET /v1/fine_tuning/jobs/{id}/events. Nothing is created, cancelled or deleted.",
"lead": "Someone kicked off the training run on a Thursday afternoon, watched the 200 come back, pasted the job id into the channel, and went home. The following Tuesday the deploy that was supposed to point at the new model is still pointing at the old one, which nobody notices because it works. Three weeks later a stakeholder asks how the fine-tune is performing and the honest answer turns out to be that it never trained. The job object has been sitting there the entire time with a status, an error code and the name of the field that was wrong, and nothing ever asked it.",
"short_answer": """<p>Ask the job, because the job knows. With a <strong>project key set to Read Only</strong>: <code>GET /v1/fine_tuning/jobs?limit=100</code>, paginating on <code>after</code>. Flag every object where <code>status</code> is <code>\"failed\"</code> and print its <code>error.code</code>, <code>error.message</code> and <code>error.param</code> &mdash; the last of which names the input that was rejected, usually <code>training_file</code> or <code>validation_file</code>.</p>
<p>Creation is asynchronous and creation succeeded. The job moves <code>validating_files</code> to <code>queued</code> to <code>running</code> and then to one of <code>succeeded</code>, <code>failed</code> or <code>cancelled</code>. Validation and training failures surface <strong>only on the job object</strong>, never as an HTTP error on the call that started it, so a caller that checks the status code of the create request has checked nothing that matters.</p>
<p>For narrative detail, <code>GET /v1/fine_tuning/jobs/{id}/events</code> returns the job's own log with a <code>level</code> and a <code>message</code> per entry. That is where the per-line validation complaints live when <code>error.message</code> is too terse to act on, and the script fetches it only for jobs that actually failed.</p>
<p>The other state worth catching is a job that never got a verdict at all: <code>validating_files</code> hours after it was created is not progress. It is treated here as a finding in its own right, because a job that is neither running nor failed is one nobody is watching.</p>
<p>This is the middle of three fine-tuning failures and it owns only the middle. A job that trained fine and never got any traffic, and the question of whether new jobs can be created at all, are both somebody else's note.</p>""",
"problem": """<p><code>POST /v1/fine_tuning/jobs</code> returns 200 as soon as the job is accepted, which is minutes or hours before anything is known about whether it will work. The Files API accepted the upload too, because it does not parse what you give it: any bytes are a valid <code>fine-tune</code> file at upload time, and the format is only checked later, inside the job.</p>
<p>So the failure lands in a place nobody is looking. <code>status</code> becomes <code>failed</code>, <code>fine_tuned_model</code> and <code>trained_tokens</code> stay null, and <code>error</code> fills in with a machine-readable <code>code</code>, a human-readable <code>message</code>, and a <code>param</code> naming the offending input. All of that is retrievable forever and none of it is pushed anywhere. There is no webhook in the default setup, no email, and no exception in the process that created the job, because that process exited successfully a week ago.</p>
<p>The causes are mundane and they repeat. A JSONL file with a trailing blank line, or a BOM, or a JSON array instead of one object per line. A row with no assistant message. A schema half-migrated between the legacy prompt/completion form and the chat form. Too few examples, or too many. And <code>exceeded_quota</code>, which is not a data problem at all and will not be fixed by editing the file, however long you stare at it.</p>
<p>The compounding cost is the deploy that quietly did not change. Everything downstream keeps using the previous model, which works, so the absence of the new one produces no symptom until somebody asks a question about a model that does not exist.</p>""",
"why": """<p><strong>A 200 on create is a receipt, not a result.</strong> This is the single sentence the note exists to install. The create call tells you the job was accepted; the terminal status tells you what happened. Any pipeline that treats the first as the second will fail silently every time, and the fix is to poll the job to a terminal state in CI rather than to check a status code and move on.</p>
<p><strong><code>error.param</code> is the field that saves the afternoon.</strong> <code>error.code</code> tells you what class of thing went wrong and <code>error.param</code> tells you which input it went wrong on, which is the difference between rewriting the training set and rewriting the validation set. The script prints all three fields verbatim and in that order, because the message is often the only part that names the actual line.</p>
<p><strong>The error codes are an open set, so the script does not pretend to know them all.</strong> A handful are documented and worth translating into an action &mdash; a malformed training file, a bad example count, an exhausted quota. Everything else is printed exactly as returned, with no guess attached. A diagnostic that invents an interpretation for a code it does not recognise is worse than one that prints the code, because it sends someone confidently in a direction the API never suggested.</p>
<p><strong>A job stuck in <code>validating_files</code> is a finding, not a job in progress.</strong> Validation is quick. A job that has been validating for hours is not going to finish validating, and it occupies the same blind spot as the failed one: no error was raised, nothing is polling it, and the file it is chewing on is still billing storage. So it gets its own verdict rather than being folded into "running".</p>
<p><strong>This note deliberately does not read usage or shutdown dates.</strong> Whether a fine-tuned model that trained successfully is ever called is a published note that joins the job list to the usage report, and whether new jobs can be created at all is a platform question about dates. Both would need different credentials and would answer different questions. This one holds a project key and reads two endpoints, which is all a failed job requires.</p>""",
"steps": [
 {"h": "Use a project key set to Read Only",
  "body": """<p>Both calls are GETs and both are project-scoped. No admin key is needed, no job is created, cancelled or deleted, and no file is touched. The script reads the job list and, for jobs that failed, the events feed for those jobs only.</p>"""},
 {"h": "List every job, not just the recent ones",
  "body": """<p><code>GET /v1/fine_tuning/jobs?limit=100</code>, paginating on <code>after</code>. If your jobs are tagged, <code>metadata</code> filters narrow the listing. The interesting jobs are usually not the recent ones: a failure from two months ago is exactly the sort of thing that is still quietly absent from a deploy.</p>"""},
 {"h": "Sort by terminal status rather than by date",
  "body": """<p><code>failed</code> is the finding. <code>succeeded</code> is somebody else's note. <code>cancelled</code> is reported without alarm, because a person did that on purpose. And <code>validating_files</code> older than <code>--stall-hours</code> is treated as its own finding rather than as work in progress.</p>"""},
 {"h": "Read the code, the param and then the events",
  "body": """<p>For each failed job the script prints <code>error.code</code>, <code>error.param</code> and <code>error.message</code>, then pulls <code>GET /v1/fine_tuning/jobs/{id}/events</code> and shows the error-level entries, which is where per-line validation complaints appear. Unknown codes are printed exactly as returned with no interpretation attached.</p>"""},
 {"h": "Fix the input, then fix the pipeline",
  "body": """<p>The immediate repair depends on the code and the script prints it. The durable repair does not: poll the job to a terminal status in CI, and fail the build on anything that is not <code>succeeded</code>. Nothing here re-uploads a file or re-creates a job.</p>"""},
],
"verify": """<p>Re-run after the corrected job finishes. The failed job does not disappear &mdash; it is a permanent record and it will keep being reported, which is why the output is grouped by status rather than counted as a single number. What should appear is a <code>succeeded</code> job newer than the failure. Then make the run part of the pipeline that creates jobs, so the next failure is discovered by the build rather than by a question in a meeting.</p>
<pre><code class="language-bash">python3 openai_fine_tune_failures.py --stall-hours 2
# ftjob_a1  failed        base gpt-5.6-terra   created 2026-08-11T18:04:02Z
#   error.code    invalid_training_file
#   error.param   training_file
#   error.message The job failed due to an invalid training file. Unexpected
#                 file format, expected either prompt/completion pairs or chat
#                 messages.
#   event         Validating training file: line 4108 has no assistant message
# job-failed           ftjob_a1: failed on training_file with invalid_training_file
#   repair: the JSONL is malformed. One JSON object per line, no trailing blank
#           line, no BOM, each row a messages array with at least one assistant
#           turn, and one schema across every row.
# ftjob_b2  validating_files  base gpt-5.6-terra  created 2026-08-30T22:41:55Z
# stalled-in-validation ftjob_b2: 9.4 hours in validating_files, which is not
#                       progress
#   repair: read GET /v1/fine_tuning/jobs/ftjob_b2/events for the line that
#           validation stopped on, and delete the file if it is a dead upload.
# 12 job(s), 2 finding(s)</code></pre>""",
"code_intro": "One paged GET plus one events GET per failed job, and six pure functions. <code>job_row</code>, which reduces a job to the eight fields worth printing and flattens the error object so a missing <code>error</code> and an empty one behave the same; <code>hours_since</code>, which takes the clock as an argument so the stall threshold is testable; <code>classify_job</code>, which separates a failure that explained itself from one that did not and treats a long validation as its own state; <code>error_advice</code>, which translates only the codes that are documented and returns nothing for the rest; <code>error_events</code>, which pulls the error-level entries out of the events feed in the order they happened; and <code>repair_lines</code>, which never invents a fix for a code it does not recognise.",
"py_file": "openai_fine_tune_failures.py",
"py": '''"""Find fine-tuning jobs that were accepted, then failed, and never read.

Read only. GET /v1/fine_tuning/jobs, paginated, plus GET on the events feed for
jobs that failed. Nothing is created, cancelled, deleted or re-uploaded.

Job creation is asynchronous. The create call returns 200 as soon as the job is
accepted, and validation and training failures surface only on the job object:
status becomes failed, fine_tuned_model and trained_tokens stay null, and error
carries code, message and param. None of that is pushed anywhere.

The error codes are an open set. The documented ones are translated into an
action; everything else is printed exactly as returned, because inventing an
interpretation sends somebody confidently in a direction the API never suggested.

Scope: this note owns a job that failed. Whether a job that succeeded is ever
called is fine-tuned-model-never-used, and whether new jobs can be created at
all is a platform question about dates. Neither is read here.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_fine_tune_failures")

JOBS_URL = "https://api.openai.com/v1/fine_tuning/jobs"

TERMINAL = ("succeeded", "failed", "cancelled")

# Only the codes with a documented meaning. Anything else is printed verbatim.
ADVICE = {
    "invalid_training_file":
        "the JSONL is malformed. One JSON object per line, no trailing blank "
        "line, no BOM, each row a messages array with at least one assistant "
        "turn, and one schema across every row.",
    "invalid_validation_file":
        "the validation file has the same problem as a malformed training "
        "file, and error.param says which of the two was rejected.",
    "invalid_n_examples":
        "the example count is out of range: too few rows to train on, or more "
        "than the method accepts. Count the lines before uploading.",
    "exceeded_quota":
        "this is a billing problem rather than a data one. Editing the file "
        "will not help; check the account's quota and spend limits.",
}

FINDINGS = ("job-failed", "failed-without-error", "stalled-in-validation")


def job_row(body):
    """One job, reduced. Pure. The error object is flattened.

    Flattened deliberately: a job with no error key and a job with an empty
    error object mean the same thing to a reader and should not need two code
    paths to say so.
    """
    body = body if isinstance(body, dict) else {}
    error = body.get("error") if isinstance(body.get("error"), dict) else {}
    try:
        created = int(body.get("created_at") or 0)
    except (TypeError, ValueError):
        created = 0
    return {"id": str(body.get("id") or ""),
            "status": str(body.get("status") or ""),
            "model": str(body.get("model") or ""),
            "fine_tuned_model": str(body.get("fine_tuned_model") or ""),
            "created_at": created,
            "code": str((error or {}).get("code") or ""),
            "param": str((error or {}).get("param") or ""),
            "message": str((error or {}).get("message") or "")}


def hours_since(created_at, now):
    """Age in hours. Pure. The clock is an argument."""
    try:
        created = int(created_at)
        now = int(now)
    except (TypeError, ValueError):
        return None
    if created <= 0:
        return None
    return (now - created) / 3600.0


def error_advice(code):
    """The documented meaning of one code. Pure. Empty for anything else."""
    return ADVICE.get(str(code or "").strip(), "")


def error_events(events):
    """Error-level messages in order. Pure. De-duplicated, never reordered."""
    out = []
    for item in events or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("level") or "").lower() != "error":
            continue
        message = str(item.get("message") or "").strip()
        if message and message not in out:
            out.append(message)
    return out


def classify_job(row, now, stall_hours):
    """Grade one job. Pure. Returns (state, detail)."""
    row = row or {}
    status = str(row.get("status") or "")
    job_id = row.get("id") or "(no id)"
    if status == "failed" and row.get("code"):
        return ("job-failed",
                "%s: failed on %s with %s"
                % (job_id, row.get("param") or "an unnamed input",
                   row.get("code")))
    if status == "failed":
        return ("failed-without-error",
                "%s: failed with no error code on the job object, so the events "
                "feed is the only account of why" % job_id)
    if status == "validating_files":
        age = hours_since(row.get("created_at"), now)
        if age is not None and age >= stall_hours:
            return ("stalled-in-validation",
                    "%s: %.1f hours in validating_files, which is not progress"
                    % (job_id, age))
        return ("validating", "%s: validating files" % job_id)
    if status == "succeeded":
        return ("succeeded",
                "%s: succeeded, which is a different note" % job_id)
    if status == "cancelled":
        return ("cancelled", "%s: cancelled by somebody on purpose" % job_id)
    if status in ("queued", "running"):
        return ("running", "%s: %s" % (job_id, status))
    return ("unknown-status",
            "%s: status %r is not one this script recognises"
            % (job_id, status or "(none)"))


def repair_lines(state, code=""):
    """The repair for one verdict. Pure. Printed, never performed."""
    poll = ("poll the job to a terminal status in CI and fail the build on "
            "anything that is not succeeded. A 200 on create is a receipt, not "
            "a result.")
    if state == "job-failed":
        advice = error_advice(code)
        if advice:
            return [advice, poll]
        return ["the code %r is not one this script has a documented meaning "
                "for. Read error.message and the events feed above as printed, "
                "and do not act on a guess." % (code or "(none)"), poll]
    if state == "failed-without-error":
        return ["read GET /v1/fine_tuning/jobs/{id}/events for this job. The "
                "terminal status is all the job object recorded.", poll]
    if state == "stalled-in-validation":
        return ["read the events feed for the line that validation stopped on, "
                "and delete the file if it is a dead upload still counting "
                "against project storage.", poll]
    if state == "succeeded":
        return []
    return []


def fetch_jobs(key, timeout=30):
    """Paged GET of the job list. Returns (rows, error)."""
    rows = []
    params = {"limit": 100}
    headers = {"Authorization": "Bearer " + key}
    for _ in range(100):
        try:
            r = requests.get(JOBS_URL, headers=headers, params=params,
                             timeout=timeout)
        except requests.RequestException as exc:
            return (rows, "request failed: %s" % exc)
        if r.status_code != 200:
            return (rows, "HTTP %d %s" % (r.status_code, (r.text or "")[:160]))
        body = r.json()
        data = body.get("data") or []
        rows.extend(job_row(item) for item in data)
        if not body.get("has_more") or not data:
            break
        params["after"] = data[-1].get("id")
    return (rows, None)


def fetch_events(job_id, key, timeout=30):
    """GET the events feed for one job. Returns a list, empty on any problem."""
    try:
        r = requests.get("%s/%s/events" % (JOBS_URL, job_id),
                         headers={"Authorization": "Bearer " + key},
                         params={"limit": 100}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("events for %s failed: %s", job_id, exc)
        return []
    if r.status_code != 200:
        return []
    try:
        return list(reversed(r.json().get("data") or []))
    except ValueError:
        return []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stall-hours", type=float, default=2.0,
                    help="hours in validating_files that count as stalled")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only. Both "
                  "calls are GETs of /v1/fine_tuning/jobs")
        return 2

    rows, err = fetch_jobs(key)
    if err:
        log.error("%s", err)
        return 2
    if not rows:
        log.info("no fine-tuning jobs in this project, so there is nothing to "
                 "grade")
        return 0

    now = int(time.time())
    findings = 0
    for row in sorted(rows, key=lambda r: -int(r.get("created_at") or 0)):
        state, detail = classify_job(row, now, args.stall_hours)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-10s %-16s base %-16s created %s", row["id"], row["status"],
             row["model"] or "(none)",
             time.strftime("%Y-%m-%dT%H:%M:%SZ",
                           time.gmtime(row["created_at"] or 0)))
        if row.get("code"):
            emit("  error.code    %s", row["code"])
        if row.get("param"):
            emit("  error.param   %s", row["param"])
        if row.get("message"):
            emit("  error.message %s", row["message"])
        if state in ("job-failed", "failed-without-error",
                     "stalled-in-validation"):
            for message in error_events(fetch_events(row["id"], key))[:5]:
                emit("  event         %s", message)
        emit("%-21s %s", state, detail)
        for line in repair_lines(state, row.get("code")):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d job(s), %d finding(s)", len(rows), findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-fine-tune-failures.mjs",
"js": '''/**
 * Find fine-tuning jobs that were accepted, then failed, and never read.
 *
 * Read only. GET /v1/fine_tuning/jobs, paginated, plus GET on the events feed
 * for jobs that failed. Nothing is created, cancelled or deleted.
 *
 * Creation is asynchronous, so the create call returning 200 says only that the
 * job was accepted. Validation and training failures surface on the job object
 * and nowhere else.
 *
 * The error codes are an open set: documented ones are translated into an
 * action, everything else is printed exactly as returned.
 */
const JOBS_URL = 'https://api.openai.com/v1/fine_tuning/jobs';

const ADVICE = {
  invalid_training_file:
    'the JSONL is malformed. One JSON object per line, no trailing blank line, '
    + 'no BOM, each row a messages array with at least one assistant turn, and '
    + 'one schema across every row.',
  invalid_validation_file:
    'the validation file has the same problem as a malformed training file, and '
    + 'error.param says which of the two was rejected.',
  invalid_n_examples:
    'the example count is out of range: too few rows to train on, or more than '
    + 'the method accepts. Count the lines before uploading.',
  exceeded_quota:
    'this is a billing problem rather than a data one. Editing the file will not '
    + "help; check the account's quota and spend limits.",
};

const FINDINGS = new Set(['job-failed', 'failed-without-error',
  'stalled-in-validation']);

/** One job, reduced. Pure. The error object is flattened. */
export function jobRow(body) {
  const job = (body && typeof body === 'object') ? body : {};
  const error = (job.error && typeof job.error === 'object') ? job.error : {};
  const created = Number(job.created_at ?? 0);
  return {
    id: String(job.id ?? ''),
    status: String(job.status ?? ''),
    model: String(job.model ?? ''),
    fine_tuned_model: String(job.fine_tuned_model ?? ''),
    created_at: Number.isFinite(created) ? Math.trunc(created) : 0,
    code: String(error.code ?? ''),
    param: String(error.param ?? ''),
    message: String(error.message ?? ''),
  };
}

/** Age in hours. Pure. The clock is an argument. */
export function hoursSince(createdAt, now) {
  const created = Number(createdAt);
  const at = Number(now);
  if (!Number.isFinite(created) || !Number.isFinite(at) || created <= 0) return null;
  return (at - created) / 3600;
}

/** The documented meaning of one code. Pure. Empty for anything else. */
export function errorAdvice(code) {
  return ADVICE[String(code ?? '').trim()] ?? '';
}

/** Error-level messages in order. Pure. De-duplicated, never reordered. */
export function errorEvents(events) {
  const out = [];
  for (const item of events ?? []) {
    if (!item || typeof item !== 'object') continue;
    if (String(item.level ?? '').toLowerCase() !== 'error') continue;
    const message = String(item.message ?? '').trim();
    if (message && !out.includes(message)) out.push(message);
  }
  return out;
}

/** Grade one job. Pure. Returns [state, detail]. */
export function classifyJob(row, now, stallHours) {
  const job = row ?? {};
  const status = String(job.status ?? '');
  const id = job.id || '(no id)';
  if (status === 'failed' && job.code) {
    return ['job-failed',
      `${id}: failed on ${job.param || 'an unnamed input'} with ${job.code}`];
  }
  if (status === 'failed') {
    return ['failed-without-error',
      `${id}: failed with no error code on the job object, so the events feed is `
      + 'the only account of why'];
  }
  if (status === 'validating_files') {
    const age = hoursSince(job.created_at, now);
    if (age !== null && age >= stallHours) {
      return ['stalled-in-validation',
        `${id}: ${age.toFixed(1)} hours in validating_files, which is not progress`];
    }
    return ['validating', `${id}: validating files`];
  }
  if (status === 'succeeded') {
    return ['succeeded', `${id}: succeeded, which is a different note`];
  }
  if (status === 'cancelled') {
    return ['cancelled', `${id}: cancelled by somebody on purpose`];
  }
  if (status === 'queued' || status === 'running') {
    return ['running', `${id}: ${status}`];
  }
  return ['unknown-status',
    `${id}: status '${status || '(none)'}' is not one this script recognises`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, code = '') {
  const poll = 'poll the job to a terminal status in CI and fail the build on '
    + 'anything that is not succeeded. A 200 on create is a receipt, not a result.';
  if (state === 'job-failed') {
    const advice = errorAdvice(code);
    if (advice) return [advice, poll];
    return [`the code '${code || '(none)'}' is not one this script has a `
      + 'documented meaning for. Read error.message and the events feed above as '
      + 'printed, and do not act on a guess.', poll];
  }
  if (state === 'failed-without-error') {
    return ['read GET /v1/fine_tuning/jobs/{id}/events for this job. The terminal '
      + 'status is all the job object recorded.', poll];
  }
  if (state === 'stalled-in-validation') {
    return ['read the events feed for the line that validation stopped on, and '
      + 'delete the file if it is a dead upload still counting against project '
      + 'storage.', poll];
  }
  return [];
}

async function fetchJobs(key) {
  const rows = [];
  const params = new URLSearchParams({ limit: '100' });
  for (let page = 0; page < 100; page += 1) {
    let res;
    try {
      res = await fetch(`${JOBS_URL}?${params.toString()}`,
        { headers: { Authorization: `Bearer ${key}` } });
    } catch (err) {
      return [rows, `request failed: ${err.message}`];
    }
    if (res.status !== 200) {
      return [rows, `HTTP ${res.status} ${(await res.text()).slice(0, 160)}`];
    }
    const body = await res.json();
    const data = body.data ?? [];
    for (const item of data) rows.push(jobRow(item));
    if (!body.has_more || !data.length) break;
    params.set('after', data[data.length - 1].id);
  }
  return [rows, null];
}

async function fetchEvents(jobId, key) {
  try {
    const res = await fetch(`${JOBS_URL}/${jobId}/events?limit=100`,
      { headers: { Authorization: `Bearer ${key}` } });
    if (res.status !== 200) return [];
    return [...((await res.json()).data ?? [])].reverse();
  } catch {
    return [];
  }
}

function args(argv) {
  const out = { stallHours: 2 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--stall-hours') out.stallHours = Number(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only. Both '
      + 'calls are GETs of /v1/fine_tuning/jobs');
    process.exitCode = 2;
    return;
  }
  const [rows, err] = await fetchJobs(key);
  if (err) {
    console.error(err);
    process.exitCode = 2;
    return;
  }
  if (!rows.length) {
    console.log('no fine-tuning jobs in this project, so there is nothing to grade');
    return;
  }

  const now = Math.trunc(Date.now() / 1000);
  let findings = 0;
  for (const row of [...rows].sort((a, b) => b.created_at - a.created_at)) {
    const [state, detail] = classifyJob(row, now, opts.stallHours);
    const when = row.created_at
      ? `${new Date(row.created_at * 1000).toISOString().slice(0, 19)}Z` : '(unknown)';
    console.log(`${row.id.padEnd(10)} ${row.status.padEnd(16)} base `
      + `${(row.model || '(none)').padEnd(16)} created ${when}`);
    if (row.code) console.log(`  error.code    ${row.code}`);
    if (row.param) console.log(`  error.param   ${row.param}`);
    if (row.message) console.log(`  error.message ${row.message}`);
    if (FINDINGS.has(state)) {
      const events = errorEvents(await fetchEvents(row.id, key)).slice(0, 5);
      for (const message of events) console.log(`  event         ${message}`);
    }
    console.log(`${state.padEnd(21)} ${detail}`);
    for (const line of repairLines(state, row.code)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }
  console.log(`${rows.length} job(s), ${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note in one assertion: a failed job produces <code>job-failed</code>, the detail names the parameter that was rejected before it names anything else, and the repair is the documented meaning of the code rather than a general apology. The second is the honesty rule &mdash; an error code the script does not recognise must still be a finding, must be printed verbatim, and must come with an instruction not to act on a guess, because a diagnostic that invents meanings is worse than one that prints strings. The third is the state everybody folds into <em>running</em>: hours in <code>validating_files</code> has to be its own verdict, and the same job an hour after creation must not be. Then the failed job with an empty error object, which is handed to the events feed. Then the boundary that keeps this out of the neighbouring note: a succeeded job is not a finding and its repair list is empty. And last the events feed, filtered to error level and de-duplicated without being reordered.",
"test_py_file": "test_openai_fine_tune_failures.py",
"test_py": '''from openai_fine_tune_failures import (classify_job, error_advice,
                                      error_events, hours_since, job_row,
                                      repair_lines)

NOW = 1_800_000_000
HOUR = 3600


def job(status, code="", param="", message="", hours_old=1.0, jid="ftjob_a1"):
    return job_row({"id": jid, "object": "fine_tuning.job", "status": status,
                    "model": "gpt-5.6-terra",
                    "created_at": NOW - int(hours_old * HOUR),
                    "fine_tuned_model": None, "trained_tokens": None,
                    "error": ({"code": code, "message": message,
                               "param": param} if code or message else None)})


def test_a_failed_job_names_the_rejected_input_and_the_documented_fix():
    row = job("failed", "invalid_training_file", "training_file",
              "The job failed due to an invalid training file.")
    state, detail = classify_job(row, NOW, 2.0)
    assert state == "job-failed"
    assert "failed on training_file with invalid_training_file" in detail
    lines = repair_lines(state, row["code"])
    assert lines[0] == error_advice("invalid_training_file")
    assert "no trailing blank line" in lines[0]
    assert any("receipt, not a result" in line for line in lines)


def test_an_unknown_code_is_printed_and_never_interpreted():
    row = job("failed", "some_new_code_2027", "training_file", "...")
    state, _ = classify_job(row, NOW, 2.0)
    assert state == "job-failed"
    assert error_advice("some_new_code_2027") == ""
    lines = repair_lines(state, row["code"])
    assert "some_new_code_2027" in lines[0]
    assert "do not act on a guess" in lines[0]
    # exceeded_quota is documented, and it is not a data problem.
    assert "billing problem" in error_advice("exceeded_quota")
    assert "Editing the file will not help" in error_advice("exceeded_quota")


def test_hours_in_validating_files_is_its_own_finding():
    stalled = job("validating_files", hours_old=9.4, jid="ftjob_b2")
    state, detail = classify_job(stalled, NOW, 2.0)
    assert state == "stalled-in-validation"
    assert "9.4 hours in validating_files" in detail
    assert any("dead upload" in line for line in repair_lines(state))
    # The same job an hour in is simply validating.
    fresh = job("validating_files", hours_old=1.0, jid="ftjob_b3")
    assert classify_job(fresh, NOW, 2.0)[0] == "validating"
    assert abs(hours_since(NOW - 5 * HOUR, NOW) - 5.0) < 1e-9
    assert hours_since(0, NOW) is None


def test_a_failure_with_no_error_object_is_sent_to_the_events_feed():
    row = job("failed")
    assert row["code"] == "" and row["param"] == ""
    state, detail = classify_job(row, NOW, 2.0)
    assert state == "failed-without-error"
    assert "the only account of why" in detail
    assert any("/events" in line for line in repair_lines(state))


def test_a_succeeded_job_is_handed_to_the_other_note():
    state, detail = classify_job(job("succeeded", hours_old=200.0), NOW, 2.0)
    assert state == "succeeded"
    assert "a different note" in detail
    assert repair_lines(state) == []
    assert classify_job(job("cancelled"), NOW, 2.0)[0] == "cancelled"
    assert classify_job(job("running"), NOW, 2.0)[0] == "running"
    assert classify_job(job("beaming_up"), NOW, 2.0)[0] == "unknown-status"


def test_the_events_feed_is_filtered_to_errors_and_kept_in_order():
    feed = [{"level": "info", "message": "Created fine-tuning job"},
            {"level": "error", "message": "line 4108 has no assistant message"},
            {"level": "warn", "message": "..."},
            {"level": "ERROR", "message": "line 4108 has no assistant message"},
            {"level": "error", "message": "validation failed"},
            "not a dict"]
    assert error_events(feed) == ["line 4108 has no assistant message",
                                  "validation failed"]
    assert error_events(None) == []
    assert job_row(None)["id"] == ""
    assert job_row({"created_at": "nonsense"})["created_at"] == 0
''',
"test_js_file": "openai-fine-tune-failures.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyJob, errorAdvice, errorEvents, hoursSince, jobRow,
         repairLines } from './openai-fine-tune-failures.mjs';

const NOW = 1_800_000_000;
const HOUR = 3600;

const job = (status, { code = '', param = '', message = '', hoursOld = 1,
                       id = 'ftjob_a1' } = {}) => jobRow({
  id,
  object: 'fine_tuning.job',
  status,
  model: 'gpt-5.6-terra',
  created_at: NOW - Math.trunc(hoursOld * HOUR),
  fine_tuned_model: null,
  trained_tokens: null,
  error: (code || message) ? { code, message, param } : null,
});

test('a failed job names the rejected input and the documented fix', () => {
  const row = job('failed', { code: 'invalid_training_file', param: 'training_file',
                              message: 'The job failed due to an invalid training file.' });
  const [state, detail] = classifyJob(row, NOW, 2);
  assert.equal(state, 'job-failed');
  assert.ok(detail.includes('failed on training_file with invalid_training_file'));
  const lines = repairLines(state, row.code);
  assert.equal(lines[0], errorAdvice('invalid_training_file'));
  assert.ok(lines[0].includes('no trailing blank line'));
  assert.ok(lines.some((l) => l.includes('receipt, not a result')));
});

test('an unknown code is printed and never interpreted', () => {
  const row = job('failed', { code: 'some_new_code_2027', param: 'training_file',
                              message: '...' });
  assert.equal(classifyJob(row, NOW, 2)[0], 'job-failed');
  assert.equal(errorAdvice('some_new_code_2027'), '');
  const lines = repairLines('job-failed', row.code);
  assert.ok(lines[0].includes('some_new_code_2027'));
  assert.ok(lines[0].includes('do not act on a guess'));
  assert.ok(errorAdvice('exceeded_quota').includes('billing problem'));
  assert.ok(errorAdvice('exceeded_quota').includes('Editing the file will not help'));
});

test('hours in validating_files is its own finding', () => {
  const stalled = job('validating_files', { hoursOld: 9.4, id: 'ftjob_b2' });
  const [state, detail] = classifyJob(stalled, NOW, 2);
  assert.equal(state, 'stalled-in-validation');
  assert.ok(detail.includes('9.4 hours in validating_files'));
  assert.ok(repairLines(state).some((l) => l.includes('dead upload')));
  assert.equal(classifyJob(job('validating_files', { hoursOld: 1 }), NOW, 2)[0],
               'validating');
  assert.ok(Math.abs(hoursSince(NOW - 5 * HOUR, NOW) - 5) < 1e-9);
  assert.equal(hoursSince(0, NOW), null);
});

test('a failure with no error object is sent to the events feed', () => {
  const row = job('failed');
  assert.equal(row.code, '');
  assert.equal(row.param, '');
  const [state, detail] = classifyJob(row, NOW, 2);
  assert.equal(state, 'failed-without-error');
  assert.ok(detail.includes('the only account of why'));
  assert.ok(repairLines(state).some((l) => l.includes('/events')));
});

test('a succeeded job is handed to the other note', () => {
  const [state, detail] = classifyJob(job('succeeded', { hoursOld: 200 }), NOW, 2);
  assert.equal(state, 'succeeded');
  assert.ok(detail.includes('a different note'));
  assert.deepEqual(repairLines(state), []);
  assert.equal(classifyJob(job('cancelled'), NOW, 2)[0], 'cancelled');
  assert.equal(classifyJob(job('running'), NOW, 2)[0], 'running');
  assert.equal(classifyJob(job('beaming_up'), NOW, 2)[0], 'unknown-status');
});

test('the events feed is filtered to errors and kept in order', () => {
  const feed = [{ level: 'info', message: 'Created fine-tuning job' },
                { level: 'error', message: 'line 4108 has no assistant message' },
                { level: 'warn', message: '...' },
                { level: 'ERROR', message: 'line 4108 has no assistant message' },
                { level: 'error', message: 'validation failed' },
                'not a dict'];
  assert.deepEqual(errorEvents(feed),
                   ['line 4108 has no assistant message', 'validation failed']);
  assert.deepEqual(errorEvents(null), []);
  assert.equal(jobRow(null).id, '');
  assert.equal(jobRow({ created_at: 'nonsense' }).created_at, 0);
});
''',
"faq": [
 ("Why does creating the job return 200 if it is going to fail?",
  "Because creation and training are different operations and only the first one is synchronous. The 200 means the job was accepted into the queue. From there it moves through validating_files, queued and running to a terminal state, and everything that can go wrong with your data goes wrong inside that sequence. The Files API is the same shape: it accepts any bytes for a fine-tune purpose without parsing them, so an unusable file uploads perfectly and fails much later, in the job."),
 ("What do the error codes actually mean?",
  "A few are documented and the script translates those: a malformed training file, an example count out of range, an exhausted quota. error.param is often more useful than the code, because it names which input was rejected. Beyond that the set is open and the script prints unrecognised codes exactly as returned, with an instruction not to act on a guess. If the code is unfamiliar, error.message and the events feed are the two places with the real detail."),
 ("The job has been validating_files for hours. Is it just slow?",
  "Treat it as stuck. Validation is quick, and a job that has been validating for hours occupies the same blind spot a failed one does: nothing raised, nothing is polling it, and the file it is working on is still counting against project storage. The events feed usually names the line it stopped on. That is why this gets its own verdict rather than being reported as a job in progress, and why the threshold is a flag you can lower."),
 ("Is this the same as a fine-tune nobody uses?",
  "No, and they are worth keeping apart because the repairs are opposite. A model that trained successfully and gets no traffic is a deployment problem: the training was billed, the model exists, and the routing never changed. That is a separate published note and it needs a usage report and an admin key to prove. This one is about a job that never produced a model at all, which needs only the job object and its events, and whose repair is to fix an input and run it again."),
 ("How do we stop finding these weeks late?",
  "Poll the job to a terminal status in the pipeline that creates it, and fail the build on anything that is not succeeded. That one change turns this class of failure from a silent absence into a red build within the hour. Running this script on a schedule is the backstop rather than the fix: it catches the jobs somebody started by hand, which are exactly the ones nobody is watching."),
],
"related": [REL_FT_UNUSED, REL_BATCH_PART, REL_QUOTA],
"citations": [CITE_OAI_FT, CITE_OAI_FT_GUIDE, CITE_OAI_FILES, CITE_OAI_ERRORS],
},
]
