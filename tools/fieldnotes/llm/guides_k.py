#!/usr/bin/env python3
"""/llm/ field notes, batch K — the writing.

Four notes that all read the same object and all four end, in production, with
the same traceback: a JSON parse that failed. That is the whole hazard of the
batch. Written carelessly they are one note four times, so the discipline here
was to make each script reach a different field and stop somewhere the other
three do not.

`structured-output-truncated-by-length` is a completed request whose answer was
cut. Status incomplete, reason max_output_tokens, and a body that is a valid
prefix of the record you asked for. It is not a configuration checked before
sending and not a parameter refused by name: the call was made, the tokens were
billed, and the ceiling arrived in the middle of a string.

`refusal-field-ignored` has nothing cut at all. The model was asked, it
declined, and it said so through a content type built for the purpose so the
refusal would not have to pretend to be schema-shaped. The response completed.
The only thing that went wrong is that a parser reached for the text and found
a channel it had never been taught to look at.

`strict-false-schema-silently-ignored` never had a contract to break. Structured
Outputs guarantees adherence only when strict is true, and with the flag absent
the schema is a hint the model usually follows. The script reads the format the
response echoes back, and then does the part that actually helps: it walks the
schema and prints every rule that would have to be fixed before the flag could
go back on, because "set strict: true" on its own is advice somebody already
tried.

`tool-call-arguments-unparseable` is the only one where the exception is raised
by code you wrote. Arguments arrive JSON encoded, as a string, and two very
different faults come through that field: a string that will not parse, and a
string that parses beautifully and describes a call your handler cannot accept.
The second is the one this note owns, and it is invisible to any amount of care
around json.loads.

Read only throughout, and unusually literally so: every script here is a GET
against stored objects, which is exactly why they can be. Nothing in this batch
sends a completion, counts a token, or writes anything at all. The repairs are
a raised ceiling, a new branch before parsing, a flag with a schema rewrite
behind it, and a validation step in a dispatcher. All four are deploys with
owners, so all four are printed.

One shared limitation, stated in every note rather than buried: /v1/responses
cannot be enumerated. There is no list endpoint. Every script here takes a file
of response ids that you already hold, and a note that pretended otherwise
would be a note nobody could run.
"""

CITE_OAI_STRUCTURED = ("Structured Outputs — OpenAI developer docs",
                       "https://developers.openai.com/api/docs/guides/structured-outputs")
CITE_OAI_RESPONSES = ("Responses — OpenAI API reference",
                      "https://developers.openai.com/api/docs/api-reference/responses")
CITE_OAI_FUNCTION = ("Function calling — OpenAI developer docs",
                     "https://developers.openai.com/api/docs/guides/function-calling")
CITE_AZ_STRUCTURED = ("Structured outputs — Azure OpenAI, Microsoft Learn",
                      "https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs")
CITE_OAI_LIMITS = ("Structured Outputs limits raised for larger schemas — OpenAI community",
                   "https://community.openai.com/t/structured-outputs-limits-are-raised-to-support-larger-schemas/1313593")
CITE_CL_STOP = ("Handling stop reasons — Claude API",
                "https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons")
CITE_CL_BATCH = ("Batch processing — Claude API",
                 "https://platform.claude.com/docs/en/build-with-claude/batch-processing")

REL_TRUNC = ("/llm/structured-output-truncated-by-length/",
             "A 200 whose JSON stops mid-object because the ceiling arrived")
REL_REFUSAL = ("/llm/refusal-field-ignored/",
               "The channel a declined answer arrives on, and nobody reads")
REL_ADVISORY = ("/llm/strict-false-schema-silently-ignored/",
                "A schema that was only ever a suggestion")
REL_ARGS = ("/llm/tool-call-arguments-unparseable/",
            "Tool arguments your dispatcher cannot use")
REL_MAXCAP = ("/llm/max-tokens-above-model-cap/",
              "The ceiling checked against the model's own maximum before you send")
REL_REASONING_TOKENS = ("/llm/reasoning-tokens-billed-invisibly/",
                        "Output tokens you are billed for and never see")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "When the expensive half of the bill is the half you generate")
REL_ALIAS = ("/llm/floating-alias-instead-of-pinned-snapshot/",
             "The model id that changes under you between deploys")

GUIDES = [
{
"slug": "structured-output-truncated-by-length",
"title": "JSON cut off mid-object because the ceiling was reached",
"description": "A completed request whose answer was cut: status incomplete, reason max_output_tokens, and a body that is a valid prefix of the JSON you asked for.",
"h1": "JSON cut off mid-object because the ceiling was reached",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["incomplete_details max_output_tokens", "structured output truncated",
             "finish_reason length json", "stop_reason max_tokens anthropic",
             "json.loads unterminated string openai"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, plus a file of stored response ids. ANTHROPIC_API_KEY, a workspace key, only for the optional batch read.",
"lead": "The extraction pipeline had been green for six weeks and then started dropping about one document in forty into the dead-letter queue with a JSONDecodeError. The traceback pointed at a worker three hops from any HTTP client, so the first day went on the queue and the second on the worker. What it turned out to be was a 200. The model had followed the schema exactly, the way strict mode promises, and had been cut off halfway through the fourth line item of an unusually long invoice. Everything about that request succeeded, including the bill.",
"short_answer": """<p>Read the stored response before you read its text. With a <strong>project key set to Read Only</strong>: <code>GET /v1/responses/{response_id}</code>, then check <code>status</code>. A response with <code>status: \"incomplete\"</code> and <code>incomplete_details.reason == \"max_output_tokens\"</code> was cut off by the output ceiling; on Chat Completions the same event is <code>finish_reason: \"length\"</code>.</p>
<p>Structured Outputs guarantees that the model <em>follows</em> the schema. It does not guarantee that the model <em>finishes</em>. When generation hits the ceiling the response is truncated exactly like any other completion, which leaves a half-written object: a string still open, a bracket still owed. That text is a valid prefix of valid JSON, and a prefix of valid JSON is not JSON.</p>
<p>On the Anthropic side the same finding is a whole corpus rather than one id. <code>GET /v1/messages/batches/{batch_id}/results</code> streams one JSON object per finished request, and every line with <code>stop_reason: \"max_tokens\"</code> is this note. Key by <code>custom_id</code> and never by position, because results come back in any order.</p>
<p>Then split the finding in two, because it has two repairs. If <code>usage.output_tokens_details.reasoning_tokens</code> accounts for most of the output, the ceiling was spent thinking and the answer never started; raising the cap and lowering the effort are both available. If it did not, the schema simply emits more than the cap allows.</p>""",
"problem": """<p>Nothing raises. The transport layer saw a 200, the SDK saw a well-formed response object, the usage block is populated and the invoice is correct. Every retry policy in the stack is keyed on exceptions and status codes, and there is no exception and the status code is fine. The first thing that objects is a JSON parser somewhere downstream, and by then the API call is several frames away and often several services away.</p>
<p>What makes it so hard to date is that it is proportional to the input. A cap that fits ninety-eight documents in a hundred is invisible until the day somebody uploads a longer one, and then it is a trickle rather than an outage &mdash; a rate low enough to look like bad data, high enough to matter, and stable enough that nobody suspects a deploy. The failures also cluster on your largest customers, because their records are the long ones.</p>""",
"why": """<p><strong>Following a schema and finishing an answer are different promises.</strong> Constrained decoding restricts which token can come next; it has no opinion about how many tokens there is room for. The two guarantees are independent and only one of them is on offer. A team that has just adopted strict mode is the most likely to be surprised by this, because strict mode has been working so well that the output stopped being checked at all.</p>
<p><strong>The ceiling covers the thinking too.</strong> On a reasoning model the cap has to absorb tokens you never see before it absorbs the ones you do, so a cap sized for the previous model can be entirely consumed before the JSON begins. That produces an incomplete response with almost no text in it, which reads as an empty answer rather than a truncated one. The script names that case separately because the repair is different: raise the ceiling, or spend less on deliberation.</p>
<p><strong>This is not the same as a cap above the model's limit.</strong> <a href=\"/llm/max-tokens-above-model-cap/\">A configured <code>max_tokens</code> larger than the model allows</a> is a 400 with a message, provable in advance against the model object, and no request is ever made. This is the opposite: the request was made, served and billed, and the number was too small rather than too large. They share a field name and nothing else.</p>
<p><strong>It is not a rejected parameter either.</strong> A reasoning model that refuses <code>max_tokens</code> by name fails every call before generation and leaves requests with no tokens under them. Here the tokens are all there, right up to the cap, which is the tell: output that sits exactly on a round number is a ceiling and not a distribution.</p>
<p><strong>A cut answer and a wrong answer are worth telling apart in code.</strong> Both make <code>json.loads</code> raise with the same class of exception. But a document that stops inside a string was interrupted, and a document that closes every bracket it opened and still fails to parse was written badly &mdash; which is <a href=\"/llm/strict-false-schema-silently-ignored/\">a schema that was never enforced</a>, not a ceiling. The script scans for that difference rather than reporting one parse error for both, because the two send you to different files.</p>
<p><strong>The most expensive version ends in a tool call.</strong> When the ceiling lands mid-<code>tool_use</code>, the final block is a call whose arguments cannot be executed. In a single-turn extraction that is one lost record; in an agent loop it poisons the conversation, because the turn now contains a call with no result and every subsequent turn inherits it. The batch reader flags that case on its own line.</p>""",
"steps": [
 {"h": "Collect the response ids you can actually read",
  "body": """<p>There is no list endpoint for <code>/v1/responses</code>: stored responses are reachable only by an id you already hold, and only if the call was made with storage on. Export the ids from your own records into a file, one per line. If you do not store them, this is the first repair and it is worth making before anything else here is runnable.</p>"""},
 {"h": "Read status before you read text",
  "body": """<p><code>GET /v1/responses/{response_id}</code> and branch on <code>status</code>, then on <code>incomplete_details.reason</code>. Do this in the script and do it in the application: the rule that fixes this class of bug permanently is that no text goes to a JSON parser until the response has said it completed.</p>"""},
 {"h": "Ask where the document stops",
  "body": """<p>A text that leaves a string open or a bracket owed is a cut answer. A text that balances and still fails to parse is a model that wrote the wrong thing, which is a different note with a different repair. The script scans for the difference rather than trusting the parse error, because the exception message is the same either way.</p>"""},
 {"h": "Check whether the ceiling was spent on reasoning",
  "body": """<p>Compare <code>usage.output_tokens_details.reasoning_tokens</code> against <code>usage.output_tokens</code>. When the first is most of the second the visible answer never began, and the finding is reported under its own name so that nobody reshapes a schema to fix a thinking budget.</p>"""},
 {"h": "Sweep a batch results file for the same shape at scale",
  "body": """<p>One stored response proves the mechanism; a batch results file measures it. Stream <code>GET /v1/messages/batches/{batch_id}/results</code>, count the lines with <code>stop_reason: \"max_tokens\"</code>, and key everything by <code>custom_id</code>. Flag separately any line whose last content block is a <code>tool_use</code>, because those are the ones that break an agent loop rather than a record.</p>"""},
],
"verify": """<p>After the ceiling is raised, re-read the same ids. The finding should disappear without the token counts changing much: the answers were nearly complete, which is why nobody noticed.</p>
<pre><code class=\"language-bash\">python3 openai_truncated_structured_output.py --ids response_ids.txt
# truncated-by-length        resp_68c4a1  Stopped on the output ceiling mid-object: the text is a valid prefix that never closes. Output sat at 100% of the configured ceiling.
#   repair: Check that the response completed before parsing anything: branch on status and on incomplete_details.reason.
#   repair: This call was capped at 1024 output tokens and used 1024 of them. Raise the ceiling above the largest record the schema can emit, with room for reasoning.
# 240 response(s) checked, 6 cut short</code></pre>""",
"code_intro": "Two GETs, both of them reads of things that already exist: one stored response per id, and optionally one batch results file streamed a line at a time. Eight pure functions carry the judgement. <code>json_state</code> is the one that earns the note, because it separates a document that was interrupted from a document that was wrong and those are different bugs. Beside it: the text reader, which has to handle both API surfaces; the reason reader, which maps two vocabularies onto one word; the refusal test, which exists only to hand a response to another note; the two ratios, which return nothing rather than zero when the response does not carry the numbers; the classifier; the repair lines, which quote this call's own cap; and the batch line reader, keyed by <code>custom_id</code> because results arrive in any order.",
"py_file": "openai_truncated_structured_output.py",
"py": '''"""Find stored OpenAI responses whose structured output was cut off mid-object.

Read only. GET /v1/responses/{response_id} for each id you supply, with a
project key set to Read Only, and optionally one GET against an Anthropic
Message Batches results file, which is a complete corpus of finished responses
and needs a workspace key.

There is no list endpoint for /v1/responses, so the ids have to come from your
own records: one id per line in a file. That is a limitation of the API and not
of this script.

The finding is a request that succeeded and stopped early: status "incomplete"
with an incomplete_details reason of max_output_tokens on the Responses API,
stop_reason "max_tokens" in an Anthropic batch result. The body is a valid
prefix of the answer, and a prefix of valid JSON is not JSON.

The repair is printed, never performed. Raising a ceiling or reshaping a schema
is a deploy with an owner.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_truncated_structured_output")

OPENAI_API = "https://api.openai.com/v1"
ANTHROPIC_API = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

# The states this note owns. Everything else the classifier can return is a
# handoff to a sibling note and is reported without being counted as a finding.
FINDINGS = ("truncated-by-length", "ceiling-spent-on-reasoning", "cut-without-a-reason")

# Above this share of the output tokens, the ceiling was consumed by reasoning
# before the visible answer began. That is a different repair from a schema
# that is simply too large, so it gets its own state.
REASONING_DOMINANT = 0.6


def output_text(response):
    """Concatenate the visible text of a stored response. Pure.

    Both surfaces, because a codebase that has half-migrated to the Responses
    API stores both shapes and a checker that only reads one of them reports
    every Chat Completions record as empty.
    """
    parts = []
    response = response or {}
    for item in response.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in ("output_text", "text"):
                parts.append(str(content.get("text") or ""))
    for choice in response.get("choices") or []:
        text = (choice.get("message") or {}).get("content")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def json_state(text):
    """Where a JSON document stops. Pure. One of empty, parses, truncated,
    malformed.

    "truncated" means the text is a valid prefix that never closes: a string
    still open, or a brace still owed. That is the difference between an answer
    that was cut and an answer the model got wrong, and json.loads collapses
    both into one exception with the same message.
    """
    body = str(text or "").strip()
    if not body:
        return "empty"
    try:
        json.loads(body)
        return "parses"
    except ValueError:
        pass

    depth = 0
    in_string = False
    escaped = False
    for ch in body:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth < 0:
                return "malformed"
    if in_string or escaped or depth > 0:
        return "truncated"
    return "malformed"


def incomplete_reason(response):
    """Why a stored response stopped early, or None. Pure.

    The Responses API says it in status plus incomplete_details.reason. Chat
    Completions said it in finish_reason, and the two vocabularies are mapped
    onto one here so the rest of the script has a single word to branch on.
    """
    response = response or {}
    if str(response.get("status") or "") == "incomplete":
        details = response.get("incomplete_details") or {}
        return str(details.get("reason") or "unknown")
    for choice in response.get("choices") or []:
        finish = str(choice.get("finish_reason") or "")
        if finish == "length":
            return "max_output_tokens"
        if finish == "content_filter":
            return "content_filter"
    return None


def has_refusal(response):
    """Does this response carry a refusal rather than an answer? Pure."""
    response = response or {}
    for item in response.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "refusal":
                return True
    for choice in response.get("choices") or []:
        if (choice.get("message") or {}).get("refusal"):
            return True
    return False


def ceiling_use(response):
    """Output tokens as a share of the configured ceiling. Pure.

    None when the response does not carry a ceiling, which is a different state
    from zero and must not be printed as one.
    """
    response = response or {}
    usage = response.get("usage") or {}
    try:
        cap = int(response.get("max_output_tokens"))
        used = int(usage.get("output_tokens"))
    except (TypeError, ValueError):
        return None
    if cap <= 0:
        return None
    return min(1.0, used / float(cap))


def reasoning_share(response):
    """Share of the output tokens that were never returned to you. Pure.

    Reasoning tokens sit inside the same ceiling as the visible answer, so a
    cap sized for the old model can be entirely consumed before generation of
    the JSON starts. None when the response does not report them.
    """
    usage = (response or {}).get("usage") or {}
    details = usage.get("output_tokens_details") or {}
    try:
        total = int(usage.get("output_tokens"))
        reasoning = int(details.get("reasoning_tokens"))
    except (TypeError, ValueError):
        return None
    if total <= 0:
        return None
    return min(1.0, reasoning / float(total))


def classify(response):
    """Classify one stored response. Pure. Returns (state, detail).

    Four of the states are handoffs. Two notes in this batch read the same
    object and reach a different conclusion from it, and a script that folded
    them in here would be telling a reader to raise a ceiling that was never
    reached.
    """
    response = response or {}
    reason = incomplete_reason(response)
    text = output_text(response)
    shape = json_state(text)
    used = ceiling_use(response)
    at_cap = "" if used is None else " Output sat at %.0f%% of the configured ceiling." % (used * 100)

    if reason == "max_output_tokens":
        thinking = reasoning_share(response)
        if thinking is not None and thinking >= REASONING_DOMINANT:
            return ("ceiling-spent-on-reasoning",
                    "Stopped on the output ceiling with %.0f%% of the output "
                    "tokens spent on reasoning, so the visible answer barely "
                    "started.%s" % (thinking * 100, at_cap))
        if shape == "truncated":
            return ("truncated-by-length",
                    "Stopped on the output ceiling mid-object: the text is a "
                    "valid prefix that never closes.%s" % at_cap)
        return ("truncated-by-length",
                "Stopped on the output ceiling. The stored text is %s.%s"
                % (shape, at_cap))

    if reason == "content_filter":
        return ("stopped-by-filter",
                "Generation was halted by the content filter rather than by "
                "the ceiling. That is the refusal note, not this one.")
    if reason is not None:
        return ("incomplete-other",
                "Incomplete for reason %r, which is not an output ceiling." % reason)

    if has_refusal(response):
        return ("refused",
                "The response completed and carries a refusal instead of an "
                "answer. Nothing was cut. Read the refusal note.")

    if shape == "parses":
        return ("complete", "Completed and the stored text parses.")
    if shape == "empty":
        return ("empty-output",
                "Completed with no text at all, which a ceiling reached during "
                "reasoning can also produce without reporting one.")
    if shape == "truncated":
        return ("cut-without-a-reason",
                "The text stops mid-object and the response reports no reason "
                "for it. Read the raw record: a Chat Completions row stored "
                "without its finish_reason looks exactly like this.")
    return ("schema-not-followed",
            "Completed, and the text is broken in a way truncation does not "
            "explain. That is an advisory schema, not a ceiling.")


def repair_lines(state, response):
    """The repair for one state, with the numbers from this response. Pure."""
    usage = (response or {}).get("usage") or {}
    cap = (response or {}).get("max_output_tokens")
    used = usage.get("output_tokens")

    if state == "truncated-by-length":
        lines = ["Check that the response completed before parsing anything: "
                 "branch on status and on incomplete_details.reason, and never "
                 "hand the text to a JSON parser until it says completed."]
        if cap and used:
            lines.append("This call was capped at %s output tokens and used %s "
                         "of them. Raise the ceiling above the largest record "
                         "the schema can emit, with room for reasoning."
                         % (cap, used))
        else:
            lines.append("Raise the output ceiling above the largest record "
                         "the schema can emit, with room for reasoning.")
        lines.append("Or reshape the schema so one call emits fewer and "
                     "shorter fields, and paginate. A long free-text field or "
                     "an unbounded array inside the schema is the usual cause.")
        return lines

    if state == "ceiling-spent-on-reasoning":
        return ["The ceiling covers reasoning tokens as well as the answer, and "
                "here it was gone before the JSON began. Raise it, or lower the "
                "reasoning effort for this call.",
                "A structured-output call that needs no deliberation is the "
                "cheapest place to spend less thinking."]

    if state == "cut-without-a-reason":
        return ["Store the whole response object, not just its text. Without "
                "status, incomplete_details and usage there is no way to tell a "
                "cut answer from a wrong one after the fact."]

    if state == "stopped-by-filter":
        return ["Not a ceiling. Handle the filter stop and the refusal channel "
                "together, as a first-class branch before parsing."]
    if state == "refused":
        return ["Not a ceiling. Read the refusal text and surface it; a refusal "
                "is an answer, not an error and not a truncation."]
    if state == "schema-not-followed":
        return ["Not a ceiling. Check whether strict was set on the schema at "
                "all, because an advisory schema produces exactly this."]
    return []


def batch_line_verdict(line):
    """Read one line of an Anthropic batch results file. Pure.

    Returns (custom_id, state, detail). Results arrive in any order, so the
    custom_id is the only safe key; position is meaningless.
    """
    try:
        record = json.loads(str(line or ""))
    except ValueError:
        return (None, "unreadable", "the line is not JSON")
    if not isinstance(record, dict):
        return (None, "unreadable", "the line is not an object")

    custom_id = record.get("custom_id")
    result = record.get("result") or {}
    if str(result.get("type") or "") != "succeeded":
        return (custom_id, "not-succeeded",
                "result type %r, which is a different note"
                % str(result.get("type") or "missing"))

    message = result.get("message") or {}
    stop = str(message.get("stop_reason") or "")
    blocks = message.get("content") or []
    last = (blocks[-1] or {}).get("type") if blocks else None
    if stop == "max_tokens":
        if last == "tool_use":
            return (custom_id, "truncated-tool-use",
                    "cut on the ceiling and the final block is an incomplete "
                    "tool_use, so the arguments cannot be executed at all")
        return (custom_id, "truncated-by-length",
                "cut on the ceiling with %s output token(s)"
                % ((message.get("usage") or {}).get("output_tokens", "an unknown number of")))
    return (custom_id, "complete", "stop_reason %r" % (stop or "missing"))


def read_ids(path):
    """One response id per line, blanks and # comments ignored."""
    ids = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def fetch_response(session, response_id):
    r = session.get(OPENAI_API + "/responses/" + response_id, timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: this needs a project key that can "
                         "read stored responses" % r.status_code)
    r.raise_for_status()
    return r.json()


def fetch_batch_results(key, batch_id):
    """Stream an Anthropic batch results file, one JSONL line at a time."""
    url = ANTHROPIC_API + "/messages/batches/" + batch_id + "/results"
    with requests.get(url, headers={"x-api-key": key,
                                    "anthropic-version": ANTHROPIC_VERSION},
                      stream=True, timeout=300) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line:
                yield line


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", help="file of stored response ids, one per line")
    ap.add_argument("--batch", help="Anthropic message batch id to read results for")
    ap.add_argument("--show-all", action="store_true",
                    help="also print responses that completed cleanly")
    args = ap.parse_args()

    if not args.ids and not args.batch:
        log.error("give --ids (a file of stored response ids) or --batch "
                  "(an Anthropic batch id), or both")
        return 2

    checked = 0
    bad = 0

    if args.ids:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            log.error("set OPENAI_API_KEY, a project key set to Read Only")
            return 2
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer " + key})
        for response_id in read_ids(args.ids):
            stored = fetch_response(session, response_id)
            checked += 1
            if stored is None:
                log.warning("%-26s %s  not found. Stored responses expire, and "
                            "a response created without storage was never "
                            "readable.", "unreadable", response_id)
                continue
            state, detail = classify(stored)
            line = "%-26s %s  %s" % (state, response_id, detail)
            if state in FINDINGS:
                bad += 1
                log.warning(line)
                for repair in repair_lines(state, stored):
                    log.warning("  repair: %s", repair)
            elif state in ("complete",):
                if args.show_all:
                    log.info(line)
            else:
                log.info(line)
                for repair in repair_lines(state, stored):
                    log.info("  note: %s", repair)

    if args.batch:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            log.error("set ANTHROPIC_API_KEY, a workspace key, to read batch results")
            return 2
        counts = {}
        for line in fetch_batch_results(key, args.batch):
            custom_id, state, detail = batch_line_verdict(line)
            checked += 1
            counts[state] = counts.get(state, 0) + 1
            if state in ("truncated-by-length", "truncated-tool-use"):
                bad += 1
                log.warning("%-26s %s  %s", state, custom_id, detail)
        for state in sorted(counts):
            log.info("batch %s: %d line(s) %s", args.batch, counts[state], state)

    log.info("%d response(s) checked, %d cut short", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-truncated-structured-output.mjs",
"js": '''/**
 * Find stored OpenAI responses whose structured output was cut off mid-object.
 *
 * Read only. GET /v1/responses/{response_id} for each id you supply, with a
 * project key set to Read Only, and optionally one GET against an Anthropic
 * Message Batches results file, which needs a workspace key.
 *
 * There is no list endpoint for /v1/responses, so the ids come from your own
 * records: one id per line in a file. The finding is a request that succeeded
 * and stopped early, leaving a valid prefix of the answer behind. A prefix of
 * valid JSON is not JSON. The repair is printed, never performed.
 */
import { readFile } from 'node:fs/promises';

const OPENAI_API = 'https://api.openai.com/v1';
const ANTHROPIC_API = 'https://api.anthropic.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

const FINDINGS = new Set([
  'truncated-by-length', 'ceiling-spent-on-reasoning', 'cut-without-a-reason']);

const REASONING_DOMINANT = 0.6;

/** Concatenate the visible text of a stored response. Pure. Both surfaces. */
export function outputText(response) {
  const parts = [];
  for (const item of response?.output ?? []) {
    for (const content of item?.content ?? []) {
      if (content?.type === 'output_text' || content?.type === 'text') {
        parts.push(String(content.text ?? ''));
      }
    }
  }
  for (const choice of response?.choices ?? []) {
    const text = choice?.message?.content;
    if (typeof text === 'string') parts.push(text);
  }
  return parts.join('');
}

/**
 * Where a JSON document stops. Pure. empty | parses | truncated | malformed.
 * "truncated" means a valid prefix that never closes, which is the difference
 * between an answer that was cut and an answer the model got wrong.
 */
export function jsonState(text) {
  const body = String(text ?? '').trim();
  if (!body) return 'empty';
  try {
    JSON.parse(body);
    return 'parses';
  } catch { /* fall through to the scanner */ }

  let depth = 0;
  let inString = false;
  let escaped = false;
  for (const ch of body) {
    if (inString) {
      if (escaped) escaped = false;
      else if (ch === '\\\\') escaped = true;
      else if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') inString = true;
    else if (ch === '{' || ch === '[') depth += 1;
    else if (ch === '}' || ch === ']') {
      depth -= 1;
      if (depth < 0) return 'malformed';
    }
  }
  return (inString || escaped || depth > 0) ? 'truncated' : 'malformed';
}

/** Why a stored response stopped early, or null. Pure. Both vocabularies. */
export function incompleteReason(response) {
  if (String(response?.status ?? '') === 'incomplete') {
    return String(response?.incomplete_details?.reason ?? 'unknown');
  }
  for (const choice of response?.choices ?? []) {
    const finish = String(choice?.finish_reason ?? '');
    if (finish === 'length') return 'max_output_tokens';
    if (finish === 'content_filter') return 'content_filter';
  }
  return null;
}

/** Does this response carry a refusal rather than an answer? Pure. */
export function hasRefusal(response) {
  for (const item of response?.output ?? []) {
    for (const content of item?.content ?? []) {
      if (content?.type === 'refusal') return true;
    }
  }
  for (const choice of response?.choices ?? []) {
    if (choice?.message?.refusal) return true;
  }
  return false;
}

/** Output tokens as a share of the configured ceiling. Pure. Null, not zero. */
export function ceilingUse(response) {
  const cap = Number(response?.max_output_tokens);
  const used = Number(response?.usage?.output_tokens);
  if (!Number.isFinite(cap) || !Number.isFinite(used) || cap <= 0) return null;
  return Math.min(1, used / cap);
}

/** Share of the output tokens that were never returned to you. Pure. */
export function reasoningShare(response) {
  const total = Number(response?.usage?.output_tokens);
  const reasoning = Number(response?.usage?.output_tokens_details?.reasoning_tokens);
  if (!Number.isFinite(total) || !Number.isFinite(reasoning) || total <= 0) return null;
  return Math.min(1, reasoning / total);
}

/** Classify one stored response. Pure. Four of the states are handoffs. */
export function classify(response) {
  const reason = incompleteReason(response);
  const shape = jsonState(outputText(response));
  const used = ceilingUse(response);
  const atCap = used === null ? ''
    : ` Output sat at ${(used * 100).toFixed(0)}% of the configured ceiling.`;

  if (reason === 'max_output_tokens') {
    const thinking = reasoningShare(response);
    if (thinking !== null && thinking >= REASONING_DOMINANT) {
      return ['ceiling-spent-on-reasoning',
        `Stopped on the output ceiling with ${(thinking * 100).toFixed(0)}% of ` +
        'the output tokens spent on reasoning, so the visible answer barely ' +
        `started.${atCap}`];
    }
    if (shape === 'truncated') {
      return ['truncated-by-length',
        'Stopped on the output ceiling mid-object: the text is a valid prefix ' +
        `that never closes.${atCap}`];
    }
    return ['truncated-by-length',
      `Stopped on the output ceiling. The stored text is ${shape}.${atCap}`];
  }

  if (reason === 'content_filter') {
    return ['stopped-by-filter',
      'Generation was halted by the content filter rather than by the ceiling. ' +
      'That is the refusal note, not this one.'];
  }
  if (reason !== null) {
    return ['incomplete-other',
      `Incomplete for reason '${reason}', which is not an output ceiling.`];
  }

  if (hasRefusal(response)) {
    return ['refused',
      'The response completed and carries a refusal instead of an answer. ' +
      'Nothing was cut. Read the refusal note.'];
  }

  if (shape === 'parses') return ['complete', 'Completed and the stored text parses.'];
  if (shape === 'empty') {
    return ['empty-output',
      'Completed with no text at all, which a ceiling reached during reasoning ' +
      'can also produce without reporting one.'];
  }
  if (shape === 'truncated') {
    return ['cut-without-a-reason',
      'The text stops mid-object and the response reports no reason for it. ' +
      'Read the raw record: a Chat Completions row stored without its ' +
      'finish_reason looks exactly like this.'];
  }
  return ['schema-not-followed',
    'Completed, and the text is broken in a way truncation does not explain. ' +
    'That is an advisory schema, not a ceiling.'];
}

/** The repair for one state, with the numbers from this response. Pure. */
export function repairLines(state, response) {
  const cap = response?.max_output_tokens;
  const used = response?.usage?.output_tokens;

  if (state === 'truncated-by-length') {
    const lines = ['Check that the response completed before parsing anything: ' +
      'branch on status and on incomplete_details.reason, and never hand the ' +
      'text to a JSON parser until it says completed.'];
    if (cap && used) {
      lines.push(`This call was capped at ${cap} output tokens and used ${used} ` +
        'of them. Raise the ceiling above the largest record the schema can ' +
        'emit, with room for reasoning.');
    } else {
      lines.push('Raise the output ceiling above the largest record the schema ' +
        'can emit, with room for reasoning.');
    }
    lines.push('Or reshape the schema so one call emits fewer and shorter ' +
      'fields, and paginate. A long free-text field or an unbounded array ' +
      'inside the schema is the usual cause.');
    return lines;
  }

  if (state === 'ceiling-spent-on-reasoning') {
    return ['The ceiling covers reasoning tokens as well as the answer, and here ' +
      'it was gone before the JSON began. Raise it, or lower the reasoning ' +
      'effort for this call.',
    'A structured-output call that needs no deliberation is the cheapest place ' +
      'to spend less thinking.'];
  }
  if (state === 'cut-without-a-reason') {
    return ['Store the whole response object, not just its text. Without status, ' +
      'incomplete_details and usage there is no way to tell a cut answer from a ' +
      'wrong one after the fact.'];
  }
  if (state === 'stopped-by-filter') {
    return ['Not a ceiling. Handle the filter stop and the refusal channel ' +
      'together, as a first-class branch before parsing.'];
  }
  if (state === 'refused') {
    return ['Not a ceiling. Read the refusal text and surface it; a refusal is ' +
      'an answer, not an error and not a truncation.'];
  }
  if (state === 'schema-not-followed') {
    return ['Not a ceiling. Check whether strict was set on the schema at all, ' +
      'because an advisory schema produces exactly this.'];
  }
  return [];
}

/**
 * Read one line of an Anthropic batch results file. Pure.
 * Results arrive in any order, so custom_id is the only safe key.
 */
export function batchLineVerdict(line) {
  let record;
  try {
    record = JSON.parse(String(line ?? ''));
  } catch {
    return [null, 'unreadable', 'the line is not JSON'];
  }
  if (!record || typeof record !== 'object' || Array.isArray(record)) {
    return [null, 'unreadable', 'the line is not an object'];
  }

  const customId = record.custom_id ?? null;
  const result = record.result ?? {};
  if (String(result.type ?? '') !== 'succeeded') {
    return [customId, 'not-succeeded',
      `result type '${String(result.type ?? 'missing')}', which is a different note`];
  }

  const message = result.message ?? {};
  const stop = String(message.stop_reason ?? '');
  const blocks = message.content ?? [];
  const last = blocks.length ? blocks[blocks.length - 1]?.type : null;
  if (stop === 'max_tokens') {
    if (last === 'tool_use') {
      return [customId, 'truncated-tool-use',
        'cut on the ceiling and the final block is an incomplete tool_use, so ' +
        'the arguments cannot be executed at all'];
    }
    const tokens = message.usage?.output_tokens ?? 'an unknown number of';
    return [customId, 'truncated-by-length',
      `cut on the ceiling with ${tokens} output token(s)`];
  }
  return [customId, 'complete', `stop_reason '${stop || 'missing'}'`];
}

async function fetchResponse(key, responseId) {
  const res = await fetch(`${OPENAI_API}/responses/${responseId}`,
    { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: this needs a project key that ` +
                    'can read stored responses');
  }
  if (!res.ok) throw new Error(`${res.status} from /responses/${responseId}`);
  return res.json();
}

async function* batchResults(key, batchId) {
  const res = await fetch(`${ANTHROPIC_API}/messages/batches/${batchId}/results`,
    { headers: { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION } });
  if (!res.ok) throw new Error(`${res.status} from the batch results file`);
  const text = await res.text();
  for (const line of text.split('\\n')) if (line.trim()) yield line;
}

async function main() {
  const idsFile = process.env.RESPONSE_IDS;
  const batchId = process.env.BATCH_ID;
  if (!idsFile && !batchId) {
    console.error('set RESPONSE_IDS (a file of stored response ids) or BATCH_ID ' +
                  '(an Anthropic batch id), or both');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';
  let checked = 0;
  let bad = 0;

  if (idsFile) {
    const key = process.env.OPENAI_API_KEY;
    if (!key) {
      console.error('set OPENAI_API_KEY, a project key set to Read Only');
      process.exitCode = 2;
      return;
    }
    const ids = (await readFile(idsFile, 'utf8')).split('\\n')
      .map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
    for (const responseId of ids) {
      const stored = await fetchResponse(key, responseId);
      checked += 1;
      if (stored === null) {
        console.warn(`${'unreadable'.padEnd(26)} ${responseId}  not found. Stored ` +
          'responses expire, and a response created without storage was never readable.');
        continue;
      }
      const [state, detail] = classify(stored);
      const line = `${state.padEnd(26)} ${responseId}  ${detail}`;
      if (FINDINGS.has(state)) {
        bad += 1;
        console.warn(line);
        for (const repair of repairLines(state, stored)) console.warn(`  repair: ${repair}`);
      } else if (state === 'complete') {
        if (showAll) console.log(line);
      } else {
        console.log(line);
        for (const repair of repairLines(state, stored)) console.log(`  note: ${repair}`);
      }
    }
  }

  if (batchId) {
    const key = process.env.ANTHROPIC_API_KEY;
    if (!key) {
      console.error('set ANTHROPIC_API_KEY, a workspace key, to read batch results');
      process.exitCode = 2;
      return;
    }
    const counts = new Map();
    for await (const line of batchResults(key, batchId)) {
      const [customId, state, detail] = batchLineVerdict(line);
      checked += 1;
      counts.set(state, (counts.get(state) ?? 0) + 1);
      if (state === 'truncated-by-length' || state === 'truncated-tool-use') {
        bad += 1;
        console.warn(`${state.padEnd(26)} ${customId}  ${detail}`);
      }
    }
    for (const state of [...counts.keys()].sort()) {
      console.log(`batch ${batchId}: ${counts.get(state)} line(s) ${state}`);
    }
  }

  console.log(`${checked} response(s) checked, ${bad} cut short`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is one incomplete response holding a string that never closes: the reason field says the ceiling, the scanner says truncated, and the repair quotes the cap the call was made under. Beside it sit the three responses this note keeps having to disown &mdash; a refusal, a filter stop, and a completed response whose text balances and still will not parse &mdash; each of which has to come back as a different state pointing at a different note. The scanner is tested on a trailing comma specifically, because that closes every bracket it opened and is therefore not a truncation however much the exception looks like one.",
"test_py_file": "test_openai_truncated_structured_output.py",
"test_py": '''import json

from openai_truncated_structured_output import (batch_line_verdict, ceiling_use,
                                                classify, incomplete_reason,
                                                json_state, output_text,
                                                reasoning_share, repair_lines)


def stored(text, *, status="completed", reason=None, cap=None, used=None,
           reasoning=None):
    body = {"id": "resp_1", "status": status,
            "output": [{"type": "message",
                        "content": [{"type": "output_text", "text": text}]}]}
    if reason:
        body["incomplete_details"] = {"reason": reason}
    if cap is not None:
        body["max_output_tokens"] = cap
    if used is not None:
        body["usage"] = {"output_tokens": used}
        if reasoning is not None:
            body["usage"]["output_tokens_details"] = {"reasoning_tokens": reasoning}
    return body


def test_an_incomplete_response_holding_a_json_prefix_is_the_whole_note():
    # 200, a body, a bill, and a record that stops inside a string.
    half = '{"invoice_id": "INV-8817", "lines": [{"sku": "AB-1", "note": "part'
    response = stored(half, status="incomplete", reason="max_output_tokens",
                      cap=1024, used=1024)
    assert incomplete_reason(response) == "max_output_tokens"
    assert json_state(half) == "truncated"
    assert ceiling_use(response) == 1.0

    state, detail = classify(response)
    assert state == "truncated-by-length"
    assert "valid prefix that never closes" in detail
    repairs = repair_lines(state, response)
    assert "incomplete_details.reason" in repairs[0]
    assert "1024 output tokens" in repairs[1]


def test_a_ceiling_eaten_by_reasoning_gets_its_own_state():
    # Same reason, same 200, and raising the cap is not the only repair on
    # offer: the answer never started because the thinking used the budget.
    response = stored("", status="incomplete", reason="max_output_tokens",
                      cap=2000, used=2000, reasoning=1900)
    assert reasoning_share(response) == 0.95
    state, detail = classify(response)
    assert state == "ceiling-spent-on-reasoning"
    assert "visible answer barely started" in detail
    assert "reasoning effort" in " ".join(repair_lines(state, response))


def test_json_state_separates_a_cut_document_from_a_wrong_one():
    assert json_state('{"a": 1}') == "parses"
    assert json_state('{"a": [1, 2,') == "truncated"
    assert json_state('{"a": "unter') == "truncated"
    assert json_state('{"a": "esc\\\\\\\\') == "truncated"
    # A trailing comma closes every bracket it opened, so nothing was cut:
    # the model wrote invalid JSON and finished doing it.
    assert json_state('{"a": 1,}') == "malformed"
    assert json_state("Sorry, I cannot help with that.") == "malformed"
    assert json_state("   ") == "empty"
    assert json_state(None) == "empty"


def test_a_refusal_and_a_filter_stop_are_handed_to_the_other_note():
    refusal = {"status": "completed",
               "output": [{"type": "message",
                           "content": [{"type": "refusal",
                                        "refusal": "I can't help with that."}]}]}
    state, detail = classify(refusal)
    assert state == "refused"
    assert "Nothing was cut" in detail

    filtered = stored("", status="incomplete", reason="content_filter")
    assert classify(filtered)[0] == "stopped-by-filter"
    assert "refusal note" in classify(filtered)[1]


def test_a_completed_response_that_still_fails_to_parse_is_not_this_note():
    # Finished, and broken in a way a ceiling cannot explain. That is a schema
    # that was never enforced, and it has its own note.
    state, detail = classify(stored('{"total": 12,}'))
    assert state == "schema-not-followed"
    assert "advisory schema" in detail
    assert classify(stored('{"total": 12}'))[0] == "complete"
    assert classify(stored('{"total": 12,')) [0] == "cut-without-a-reason"


def test_chat_completions_rows_are_read_as_well_as_responses_rows():
    legacy = {"choices": [{"finish_reason": "length",
                           "message": {"content": '{"rows": [{"id": 1'}}]}
    assert output_text(legacy) == '{"rows": [{"id": 1'
    assert incomplete_reason(legacy) == "max_output_tokens"
    assert classify(legacy)[0] == "truncated-by-length"


def test_a_missing_ceiling_is_not_a_ceiling_of_zero():
    assert ceiling_use(stored("{}")) is None
    assert ceiling_use(stored("{}", cap=0, used=0)) is None
    assert ceiling_use(None) is None
    assert reasoning_share(stored("{}", cap=10, used=0)) is None
    assert classify(None)[0] == "empty-output"


def test_batch_results_are_keyed_by_custom_id_and_read_line_by_line():
    cut = json.dumps({"custom_id": "row-9", "result": {
        "type": "succeeded",
        "message": {"stop_reason": "max_tokens",
                    "usage": {"output_tokens": 4096},
                    "content": [{"type": "text", "text": '{"a": 1'}]}}})
    assert batch_line_verdict(cut)[:2] == ("row-9", "truncated-by-length")
    assert "4096" in batch_line_verdict(cut)[2]

    tool = json.dumps({"custom_id": "row-10", "result": {
        "type": "succeeded",
        "message": {"stop_reason": "max_tokens",
                    "content": [{"type": "tool_use", "name": "charge",
                                 "input": {}}]}}})
    assert batch_line_verdict(tool)[1] == "truncated-tool-use"
    assert "cannot be executed" in batch_line_verdict(tool)[2]

    done = json.dumps({"custom_id": "row-11", "result": {
        "type": "succeeded", "message": {"stop_reason": "end_turn",
                                         "content": []}}})
    assert batch_line_verdict(done)[1] == "complete"
    errored = json.dumps({"custom_id": "row-12", "result": {"type": "errored"}})
    assert batch_line_verdict(errored)[1] == "not-succeeded"
    assert batch_line_verdict("{not json")[1] == "unreadable"
    assert batch_line_verdict("")[1] == "unreadable"
''',
"test_js_file": "openai-truncated-structured-output.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  batchLineVerdict, ceilingUse, classify, incompleteReason, jsonState,
  outputText, reasoningShare, repairLines,
} from './openai-truncated-structured-output.mjs';

const stored = (text, opts = {}) => {
  const body = {
    id: 'resp_1',
    status: opts.status ?? 'completed',
    output: [{ type: 'message', content: [{ type: 'output_text', text }] }],
  };
  if (opts.reason) body.incomplete_details = { reason: opts.reason };
  if (opts.cap !== undefined) body.max_output_tokens = opts.cap;
  if (opts.used !== undefined) {
    body.usage = { output_tokens: opts.used };
    if (opts.reasoning !== undefined) {
      body.usage.output_tokens_details = { reasoning_tokens: opts.reasoning };
    }
  }
  return body;
};

test('an incomplete response holding a json prefix is the whole note', () => {
  const half = '{"invoice_id": "INV-8817", "lines": [{"sku": "AB-1", "note": "part';
  const response = stored(half, {
    status: 'incomplete', reason: 'max_output_tokens', cap: 1024, used: 1024 });
  assert.equal(incompleteReason(response), 'max_output_tokens');
  assert.equal(jsonState(half), 'truncated');
  assert.equal(ceilingUse(response), 1);

  const [state, detail] = classify(response);
  assert.equal(state, 'truncated-by-length');
  assert.match(detail, /valid prefix that never closes/);
  const repairs = repairLines(state, response);
  assert.match(repairs[0], /incomplete_details\\.reason/);
  assert.match(repairs[1], /1024 output tokens/);
});

test('a ceiling eaten by reasoning gets its own state', () => {
  const response = stored('', {
    status: 'incomplete', reason: 'max_output_tokens',
    cap: 2000, used: 2000, reasoning: 1900 });
  assert.equal(reasoningShare(response), 0.95);
  const [state, detail] = classify(response);
  assert.equal(state, 'ceiling-spent-on-reasoning');
  assert.match(detail, /visible answer barely started/);
  assert.match(repairLines(state, response).join(' '), /reasoning effort/);
});

test('jsonState separates a cut document from a wrong one', () => {
  assert.equal(jsonState('{"a": 1}'), 'parses');
  assert.equal(jsonState('{"a": [1, 2,'), 'truncated');
  assert.equal(jsonState('{"a": "unter'), 'truncated');
  assert.equal(jsonState('{"a": "esc\\\\\\\\'), 'truncated');
  assert.equal(jsonState('{"a": 1,}'), 'malformed');
  assert.equal(jsonState('Sorry, I cannot help with that.'), 'malformed');
  assert.equal(jsonState('   '), 'empty');
  assert.equal(jsonState(null), 'empty');
});

test('a refusal and a filter stop are handed to the other note', () => {
  const refusal = { status: 'completed', output: [{ type: 'message',
    content: [{ type: 'refusal', refusal: "I can't help with that." }] }] };
  const [state, detail] = classify(refusal);
  assert.equal(state, 'refused');
  assert.match(detail, /Nothing was cut/);

  const filtered = stored('', { status: 'incomplete', reason: 'content_filter' });
  assert.equal(classify(filtered)[0], 'stopped-by-filter');
  assert.match(classify(filtered)[1], /refusal note/);
});

test('a completed response that still fails to parse is not this note', () => {
  const [state, detail] = classify(stored('{"total": 12,}'));
  assert.equal(state, 'schema-not-followed');
  assert.match(detail, /advisory schema/);
  assert.equal(classify(stored('{"total": 12}'))[0], 'complete');
  assert.equal(classify(stored('{"total": 12,'))[0], 'cut-without-a-reason');
});

test('chat completions rows are read as well as responses rows', () => {
  const legacy = { choices: [{ finish_reason: 'length',
    message: { content: '{"rows": [{"id": 1' } }] };
  assert.equal(outputText(legacy), '{"rows": [{"id": 1');
  assert.equal(incompleteReason(legacy), 'max_output_tokens');
  assert.equal(classify(legacy)[0], 'truncated-by-length');
});

test('a missing ceiling is not a ceiling of zero', () => {
  assert.equal(ceilingUse(stored('{}')), null);
  assert.equal(ceilingUse(stored('{}', { cap: 0, used: 0 })), null);
  assert.equal(ceilingUse(null), null);
  assert.equal(reasoningShare(stored('{}', { cap: 10, used: 0 })), null);
  assert.equal(classify(null)[0], 'empty-output');
});

test('batch results are keyed by custom_id and read line by line', () => {
  const cut = JSON.stringify({ custom_id: 'row-9', result: {
    type: 'succeeded',
    message: { stop_reason: 'max_tokens', usage: { output_tokens: 4096 },
      content: [{ type: 'text', text: '{"a": 1' }] } } });
  assert.deepEqual(batchLineVerdict(cut).slice(0, 2), ['row-9', 'truncated-by-length']);
  assert.match(batchLineVerdict(cut)[2], /4096/);

  const tool = JSON.stringify({ custom_id: 'row-10', result: {
    type: 'succeeded',
    message: { stop_reason: 'max_tokens',
      content: [{ type: 'tool_use', name: 'charge', input: {} }] } } });
  assert.equal(batchLineVerdict(tool)[1], 'truncated-tool-use');
  assert.match(batchLineVerdict(tool)[2], /cannot be executed/);

  const done = JSON.stringify({ custom_id: 'row-11', result: {
    type: 'succeeded', message: { stop_reason: 'end_turn', content: [] } } });
  assert.equal(batchLineVerdict(done)[1], 'complete');
  const errored = JSON.stringify({ custom_id: 'row-12', result: { type: 'errored' } });
  assert.equal(batchLineVerdict(errored)[1], 'not-succeeded');
  assert.equal(batchLineVerdict('{not json')[1], 'unreadable');
  assert.equal(batchLineVerdict('')[1], 'unreadable');
});
''',
"faq": [
 ("Why can the script not just list my responses and check them all?",
  "Because /v1/responses has no list endpoint. Stored responses are reachable only by an id you already hold, and conversations are the same. That is a genuine gap in the API rather than an omission here, and it is why every script in this batch takes a file of ids. If you are not recording response ids, start there: it costs a column and it is the difference between being able to answer this question and not."),
 ("Is this the same as max_tokens being set above the model's cap?",
  "No, and they are almost opposites. A cap above the model's own maximum is a 400 before anything is generated, catchable in advance against the model object, and the fix is a smaller number. This one is a 200 after everything was generated and billed, and the fix is a larger number. The only thing they share is the field."),
 ("The response is incomplete but there is no text at all. Same thing?",
  "Usually yes, and the script says so under a different name. On a reasoning model the output ceiling covers the thinking as well as the answer, so a cap sized for an older model can be spent before the JSON starts. That comes back as ceiling-spent-on-reasoning, because raising the cap and lowering the reasoning effort are both real repairs and reshaping the schema is not."),
 ("Do I pay for a truncated response?",
  "Fully, for everything that was generated, including reasoning tokens you never received. That is the sharpest part of this: the money is spent, the work is not done, and the record is thrown away by a parser several services downstream. A truncation rate is a waste rate, which is a better argument for fixing it than the error count is."),
 ("How do I catch this without a script, in the application?",
  "One rule: never hand model output to a JSON parser until the response says it completed. Branch on status and incomplete_details.reason for the Responses API, on finish_reason for Chat Completions, and on stop_reason for Anthropic. Everything else here is archaeology for the responses you already stored under the old rule."),
],
"related": [REL_ARGS, REL_MAXCAP, REL_REASONING_TOKENS],
"citations": [CITE_OAI_STRUCTURED, CITE_OAI_RESPONSES, CITE_CL_STOP, CITE_CL_BATCH],
},
{
"slug": "refusal-field-ignored",
"title": "The model refused and the refusal field was never read",
"description": "A refusal arrives in its own content type, not as an error and not as text. A parser reaching for the answer finds nothing and writes an empty record.",
"h1": "The model refused and the refusal field was never read",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai refusal field", "message.refusal null content",
             "structured outputs refusal", "incomplete_details content_filter",
             "parsed is None openai"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, plus a file of stored response ids. Nothing else: the whole finding is in the stored object.",
"lead": "The support summariser stopped producing summaries for a particular kind of ticket. Not all of them, and not with an error: the row was written, the summary column held an empty string, and the dashboard that counts summaries counted them. It took a week and a customer complaint before anyone read a stored response end to end, and there it was, in a content item nobody's code had ever touched: the model had declined, politely, and said why.",
"short_answer": """<p>Look at the content <em>types</em> before you look at the content. With a <strong>project key set to Read Only</strong>: <code>GET /v1/responses/{response_id}</code>, then scan <code>output[].content[]</code> for an item whose <code>type</code> is <code>\"refusal\"</code> and read its <code>refusal</code> string. On Chat Completions the same event is a non-null <code>choices[0].message.refusal</code> with <code>message.content</code> set to null, which is why <code>.parsed</code> comes back as <code>None</code>.</p>
<p>Structured Outputs gives a refusal its own channel precisely so it does not have to be squeezed into your schema. That is the right design, and it is also why a parser that reaches straight for the text or the parsed object misses it completely. The request succeeded. The model answered. The answer was no.</p>
<p>Check the adjacent case in the same pass: <code>status: \"incomplete\"</code> with <code>incomplete_details.reason == \"content_filter\"</code>. That is the platform halting generation rather than the model declining, and it needs the same caller-facing handling with different metrics behind it.</p>
<p>Then stop looking at single responses. One refusal is not a finding. A refusal rate per prompt template is, which is why the script groups by <code>metadata</code> before it judges and refuses to publish a rate for a group too small to have one.</p>""",
"problem": """<p>A refusal is the only failure in this batch where everything worked. The input was read and billed, generation happened, the schema was respected in the sense that the model declined to produce a fabricated object rather than producing a bad one, and the response completed. There is no status code to catch, no reason field to branch on, and nothing anywhere in the response that looks like an error.</p>
<p>So the damage is quiet and it is data-shaped. Code that reaches for the parsed object gets <code>None</code> and either crashes on the attribute access or, far worse, writes an empty record and moves on. Empty records do not page anyone. They accumulate, they look like a source-data problem, and they are usually discovered by a human noticing that a particular category of thing never has a summary.</p>""",
"why": """<p><strong>A refusal is not an error and treating it as one costs money.</strong> Retry logic that fires on empty output re-sends the same prompt and is declined again, at full price, as many times as the policy allows. The model was not flaky; it made a decision, and it will make the same decision. The only sane response is to surface the refusal text to whoever asked.</p>
<p><strong>It is not a truncation either, and that is the confusion that costs a day.</strong> <a href=\"/llm/structured-output-truncated-by-length/\">A cut answer</a> and a refusal both return 200 with nothing your parser can use. One means the model was interrupted and the ceiling is the thing to change; the other means the model declined and the input is the thing to look at. The script reports them as different states so the reader does not go tuning a token budget to fix a policy decision.</p>
<p><strong>The dangerous shape is a refusal with a preamble.</strong> When the turn produces some text and then refuses, a reader that concatenates output items ends up with a plausible-looking fragment and stores it as the answer. That is worse than an empty record, because it is wrong rather than missing, and nothing downstream can tell. The script reports it under its own state for exactly that reason.</p>
<p><strong>A filter stop is a different event with the same user-facing shape.</strong> <code>incomplete_details.reason == \"content_filter\"</code> is the platform stopping the turn, not the model declining it. Users need the same message; you need different metrics, because the two move for different reasons and folding them together hides both.</p>
<p><strong>The number worth having is a rate per prompt, not a count.</strong> Refusal rates are meaningful per template, because a template is the thing you can change. A template that refuses one call in three usually has a bad instruction or a bad input source feeding it, not bad users. The script therefore groups by whatever you put in <code>metadata</code> and falls back to the model id, which is the least useful grouping that is still true.</p>
<p><strong>A rate from a handful of calls is a rumour.</strong> One refusal in one response is a hundred percent, and a report that says so is a report people learn to ignore within a fortnight. Below the floor the script counts and withholds the rate rather than printing a number it cannot stand behind.</p>""",
"steps": [
 {"h": "Gather the ids and expect some of them to be gone",
  "body": """<p>Stored responses are reachable only by id and only if the call stored them at all; they also expire. A 404 here is not a finding, it is the retention window, and the script says so rather than counting it as a clean response.</p>"""},
 {"h": "Scan content types, not content",
  "body": """<p>Walk <code>output[].content[]</code> and look at <code>type</code> on each item. <code>refusal</code> is a peer of <code>output_text</code>, not a variant of it. Read the Chat Completions shape in the same pass: <code>message.refusal</code> alongside a null <code>message.content</code> is the same event on the older surface, and a half-migrated codebase has both in its records.</p>"""},
 {"h": "Separate a refusal from a filter stop and from a truncation",
  "body": """<p>Three different states, three different owners. A refusal points at the prompt and the input; a filter stop points at the platform; a truncation points at the ceiling. Reporting them under one heading is how a team ends up changing all three things at once and learning nothing.</p>"""},
 {"h": "Group by prompt template before counting anything",
  "body": """<p>Tag your calls with a template name in <code>metadata</code> and this becomes sharp. Without tags the script groups by model id, which is honest and nearly useless: it will tell you that refusals happen, not which prompt causes them.</p>"""},
 {"h": "Print the rate only where there is enough of it",
  "body": """<p>Below the floor, count and say the count. Above it, print a percentage. The point of the floor is that this report gets read every week for a year, and a report that cries wolf on a single call does not survive that.</p>"""},
],
"verify": """<p>After the refusal branch is added, re-run. The refusals do not go away &mdash; they are not a bug &mdash; but the empty records do, and the rate per template becomes a number you can watch.</p>
<pre><code class=\"language-bash\">python3 openai_refusal_channel.py --ids response_ids.txt
# refused                resp_68d1f0  Completed with a refusal and no answer: \"I'm sorry, I can't help with that.\". There is nothing to parse and nothing went wrong.
#   repair: Handle refusal as a first-class branch before parsing: surface the refusal text to the caller and do not attempt schema parsing at all.
# group                  kyc-extract  30.0% of 30 response(s) refused or filtered
# 240 response(s) checked, 9 refused or filtered</code></pre>""",
"code_intro": "One GET per id and no second call at all: everything this note needs is inside the stored object. Seven pure functions. <code>refusals</code> reads the channel itself on both API surfaces and returns the text rather than a boolean, because showing the reader what the model actually said is most of the value. <code>visible_text</code> is deliberately not called \"the answer\", since on a refused turn it is either empty or a preamble and treating it as the answer is the bug. Then the stop-reason reader that keeps a truncation out of this note, the grouping key with its honest fallback, the classifier, the rate function that withholds a percentage below the floor, and the repair lines.",
"py_file": "openai_refusal_channel.py",
"py": '''"""Find stored OpenAI responses that carry a refusal nobody read.

Read only. GET /v1/responses/{response_id} for each id you supply, with a
project key set to Read Only. There is no list endpoint for /v1/responses, so
the ids come from your own records: one id per line in a file.

Structured Outputs gives a safety refusal its own content type so it does not
have to be squeezed into your schema. That is the right design and it is also
why a parser reaching straight for the text finds nothing: the refusal is not
an error, not a truncation, and not schema-shaped. The response completed.

One refusal is not a finding. A refusal rate per prompt template is, which is
why this script groups before it judges: a template that refuses one call in
three has a bad input source or a bad instruction, not bad users.

The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_refusal_channel")

API = "https://api.openai.com/v1"

# States this note owns. "truncated" is a handoff: an answer that was cut short
# is a different note with a different repair.
FINDINGS = ("refused", "refused-after-partial", "stopped-by-filter")

# Below this many responses in a group, a rate is a rumour.
GROUP_FLOOR = 20


def refusals(response):
    """Every refusal carried by a stored response. Pure.

    Returns dicts with the output index and the refusal text, so a caller can
    show the reader what the model actually said rather than the fact that it
    said something. Both surfaces: the Responses API puts a refusal content
    item in output[], Chat Completions puts a string on message.refusal.
    """
    found = []
    response = response or {}
    for index, item in enumerate(response.get("output") or []):
        for content in item.get("content") or []:
            if content.get("type") == "refusal":
                found.append({"index": index,
                              "text": str(content.get("refusal") or "").strip()})
    for index, choice in enumerate(response.get("choices") or []):
        text = (choice.get("message") or {}).get("refusal")
        if text:
            found.append({"index": index, "text": str(text).strip()})
    return found


def visible_text(response):
    """The text a parser would have reached for. Pure.

    Deliberately not "the answer": on a refused turn this is empty or a partial
    preamble, and the whole bug is that the calling code treats emptiness as a
    transport problem rather than as a decision the model made.
    """
    parts = []
    response = response or {}
    for item in response.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in ("output_text", "text"):
                parts.append(str(content.get("text") or ""))
    for choice in response.get("choices") or []:
        text = (choice.get("message") or {}).get("content")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts).strip()


def stop_reason(response):
    """Why the response stopped, in one vocabulary. Pure. None when it did not."""
    response = response or {}
    if str(response.get("status") or "") == "incomplete":
        return str((response.get("incomplete_details") or {}).get("reason") or "unknown")
    for choice in response.get("choices") or []:
        finish = str(choice.get("finish_reason") or "")
        if finish == "length":
            return "max_output_tokens"
        if finish == "content_filter":
            return "content_filter"
    return None


def group_key(response):
    """What to count refusals against. Pure.

    A refusal rate is only interesting per prompt, so metadata wins over the
    model id. Tag your calls and this script gets sharper; do not, and it still
    works at model granularity, which is the least useful grouping that is
    still true.
    """
    response = response or {}
    metadata = response.get("metadata") or {}
    for field in ("template", "prompt_template", "prompt_id", "use_case"):
        value = metadata.get(field)
        if value:
            return str(value)
    prompt = response.get("prompt") or {}
    if prompt.get("id"):
        return "prompt:" + str(prompt["id"])
    return "model:" + str(response.get("model") or "unknown")


def classify(response):
    """Classify one stored response. Pure. Returns (state, detail).

    The distinction that costs people a day is refusal against truncation. Both
    return 200 with no usable payload. One means the model declined and the
    input is the thing to look at; the other means the model was interrupted
    and the ceiling is the thing to look at.
    """
    response = response or {}
    declined = refusals(response)
    text = visible_text(response)
    reason = stop_reason(response)

    if declined:
        said = declined[0]["text"] or "(the refusal string was empty)"
        if text:
            return ("refused-after-partial",
                    "The turn produced %d character(s) of text and then "
                    "refused: %r. A reader that concatenates output items ends "
                    "up storing the preamble as if it were the answer."
                    % (len(text), said))
        return ("refused",
                "Completed with a refusal and no answer: %r. There is nothing "
                "to parse and nothing went wrong." % said)

    if reason == "content_filter":
        return ("stopped-by-filter",
                "Incomplete because the content filter halted generation. That "
                "is the platform stopping the turn, not the model declining "
                "it, and the two are worth separating in your metrics.")
    if reason == "max_output_tokens":
        return ("truncated",
                "Incomplete because the output ceiling was reached. Nothing "
                "was refused. Read the truncation note.")
    if reason is not None:
        return ("incomplete-other",
                "Incomplete for reason %r, which is neither a refusal nor a "
                "ceiling." % reason)

    if not text:
        return ("empty-answer",
                "Completed, no refusal, and no text either. Check whether the "
                "output items are a tool call rather than a message.")
    return ("answered", "Completed with %d character(s) of text." % len(text))


def refusal_rate(rows, floor=GROUP_FLOOR):
    """Refusal rate per group. Pure. Rows are (group, state) pairs.

    Returns rate None below the floor rather than a number, because one refusal
    in one call is 100% and reporting it that way trains people to ignore the
    report. Counting is still done, so a small group grows into a real one.
    """
    totals = {}
    for group, state in rows or []:
        row = totals.setdefault(str(group), {"total": 0, "refused": 0,
                                             "filtered": 0, "rate": None})
        row["total"] += 1
        if state in ("refused", "refused-after-partial"):
            row["refused"] += 1
        elif state == "stopped-by-filter":
            row["filtered"] += 1
    for row in totals.values():
        if row["total"] >= floor:
            row["rate"] = (row["refused"] + row["filtered"]) / float(row["total"])
    return totals


def repair_lines(state):
    """The repair for one state. Pure."""
    if state in ("refused", "refused-after-partial"):
        return ["Handle refusal as a first-class branch before parsing: if any "
                "output content item has type refusal, surface the refusal text "
                "to the caller and do not attempt schema parsing at all.",
                "Never treat an empty parsed value as a transport failure. A "
                "refusal is a completed answer and retrying it unchanged spends "
                "money to be told no again.",
                "Log the refusal rate per prompt template. A spike is almost "
                "always a prompt change or a bad input source, not a change in "
                "who your users are."]
    if state == "stopped-by-filter":
        return ["Branch on incomplete_details.reason as well as on the refusal "
                "content type. A filter stop is the platform halting the turn "
                "and it needs the same caller-facing message as a refusal.",
                "Count filter stops separately from model refusals. They move "
                "for different reasons and folding them together hides both."]
    if state == "truncated":
        return ["Not a refusal. Check the output ceiling before you look at the "
                "prompt: the model was interrupted, not unwilling."]
    if state == "empty-answer":
        return ["Not a refusal either. Inspect the output item types before "
                "concluding anything: a function call is not a message."]
    return []


def read_ids(path):
    """One response id per line, blanks and # comments ignored."""
    ids = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def fetch_response(session, response_id):
    r = session.get(API + "/responses/" + response_id, timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: this needs a project key that can "
                         "read stored responses" % r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True,
                    help="file of stored response ids, one per line")
    ap.add_argument("--floor", type=int, default=GROUP_FLOOR,
                    help="responses a group needs before a rate is printed")
    ap.add_argument("--show-all", action="store_true",
                    help="also print responses that were answered normally")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY, a project key set to Read Only")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    rows = []
    checked = 0
    bad = 0
    for response_id in read_ids(args.ids):
        stored = fetch_response(session, response_id)
        checked += 1
        if stored is None:
            log.warning("%-22s %s  not found. Stored responses expire, and a "
                        "response created without storage was never readable.",
                        "unreadable", response_id)
            continue
        state, detail = classify(stored)
        rows.append((group_key(stored), state))
        line = "%-22s %s  %s" % (state, response_id, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(state):
                log.warning("  repair: %s", repair)
        elif state == "answered":
            if args.show_all:
                log.info(line)
        else:
            log.info(line)
            for repair in repair_lines(state):
                log.info("  note: %s", repair)

    rates = refusal_rate(rows, args.floor)
    for group in sorted(rates):
        row = rates[group]
        if row["rate"] is None:
            log.info("%-22s %s  %d response(s), under the floor of %d so no "
                     "rate is claimed", "group", group, row["total"], args.floor)
        else:
            log.warning("%-22s %s  %.1f%% of %d response(s) refused or filtered",
                        "group", group, row["rate"] * 100, row["total"])

    log.info("%d response(s) checked, %d refused or filtered", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-refusal-channel.mjs",
"js": '''/**
 * Find stored OpenAI responses that carry a refusal nobody read.
 *
 * Read only. GET /v1/responses/{response_id} for each id you supply, with a
 * project key set to Read Only. There is no list endpoint for /v1/responses,
 * so the ids come from your own records: one id per line in a file.
 *
 * Structured Outputs gives a safety refusal its own content type so it does
 * not have to be squeezed into your schema. The response completed, nothing
 * errored, and the field a parser reaches for is simply not where the answer
 * went. One refusal is not a finding; a rate per prompt template is.
 *
 * The repair is printed, never performed.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

const FINDINGS = new Set(['refused', 'refused-after-partial', 'stopped-by-filter']);

const GROUP_FLOOR = 20;

/** Every refusal carried by a stored response. Pure. Both surfaces. */
export function refusals(response) {
  const found = [];
  (response?.output ?? []).forEach((item, index) => {
    for (const content of item?.content ?? []) {
      if (content?.type === 'refusal') {
        found.push({ index, text: String(content.refusal ?? '').trim() });
      }
    }
  });
  (response?.choices ?? []).forEach((choice, index) => {
    const text = choice?.message?.refusal;
    if (text) found.push({ index, text: String(text).trim() });
  });
  return found;
}

/** The text a parser would have reached for. Pure. Not "the answer". */
export function visibleText(response) {
  const parts = [];
  for (const item of response?.output ?? []) {
    for (const content of item?.content ?? []) {
      if (content?.type === 'output_text' || content?.type === 'text') {
        parts.push(String(content.text ?? ''));
      }
    }
  }
  for (const choice of response?.choices ?? []) {
    const text = choice?.message?.content;
    if (typeof text === 'string') parts.push(text);
  }
  return parts.join('').trim();
}

/** Why the response stopped, in one vocabulary. Pure. Null when it did not. */
export function stopReason(response) {
  if (String(response?.status ?? '') === 'incomplete') {
    return String(response?.incomplete_details?.reason ?? 'unknown');
  }
  for (const choice of response?.choices ?? []) {
    const finish = String(choice?.finish_reason ?? '');
    if (finish === 'length') return 'max_output_tokens';
    if (finish === 'content_filter') return 'content_filter';
  }
  return null;
}

/** What to count refusals against. Pure. Metadata wins over the model id. */
export function groupKey(response) {
  const metadata = response?.metadata ?? {};
  for (const field of ['template', 'prompt_template', 'prompt_id', 'use_case']) {
    if (metadata[field]) return String(metadata[field]);
  }
  if (response?.prompt?.id) return `prompt:${response.prompt.id}`;
  return `model:${String(response?.model ?? 'unknown')}`;
}

/** Classify one stored response. Pure. Refusal against truncation is the split. */
export function classify(response) {
  const declined = refusals(response);
  const text = visibleText(response);
  const reason = stopReason(response);

  if (declined.length) {
    const said = declined[0].text || '(the refusal string was empty)';
    if (text) {
      return ['refused-after-partial',
        `The turn produced ${text.length} character(s) of text and then ` +
        `refused: '${said}'. A reader that concatenates output items ends up ` +
        'storing the preamble as if it were the answer.'];
    }
    return ['refused',
      `Completed with a refusal and no answer: '${said}'. There is nothing to ` +
      'parse and nothing went wrong.'];
  }

  if (reason === 'content_filter') {
    return ['stopped-by-filter',
      'Incomplete because the content filter halted generation. That is the ' +
      'platform stopping the turn, not the model declining it, and the two are ' +
      'worth separating in your metrics.'];
  }
  if (reason === 'max_output_tokens') {
    return ['truncated',
      'Incomplete because the output ceiling was reached. Nothing was refused. ' +
      'Read the truncation note.'];
  }
  if (reason !== null) {
    return ['incomplete-other',
      `Incomplete for reason '${reason}', which is neither a refusal nor a ceiling.`];
  }

  if (!text) {
    return ['empty-answer',
      'Completed, no refusal, and no text either. Check whether the output ' +
      'items are a tool call rather than a message.'];
  }
  return ['answered', `Completed with ${text.length} character(s) of text.`];
}

/**
 * Refusal rate per group. Pure. Rows are [group, state] pairs.
 * Rate stays null below the floor: one refusal in one call is 100%, and
 * printing that teaches people to ignore the report.
 */
export function refusalRate(rows, floor = GROUP_FLOOR) {
  const totals = new Map();
  for (const [group, state] of rows ?? []) {
    const key = String(group);
    if (!totals.has(key)) {
      totals.set(key, { total: 0, refused: 0, filtered: 0, rate: null });
    }
    const row = totals.get(key);
    row.total += 1;
    if (state === 'refused' || state === 'refused-after-partial') row.refused += 1;
    else if (state === 'stopped-by-filter') row.filtered += 1;
  }
  for (const row of totals.values()) {
    if (row.total >= floor) row.rate = (row.refused + row.filtered) / row.total;
  }
  return totals;
}

/** The repair for one state. Pure. */
export function repairLines(state) {
  if (state === 'refused' || state === 'refused-after-partial') {
    return ['Handle refusal as a first-class branch before parsing: if any output ' +
      'content item has type refusal, surface the refusal text to the caller and ' +
      'do not attempt schema parsing at all.',
    'Never treat an empty parsed value as a transport failure. A refusal is a ' +
      'completed answer and retrying it unchanged spends money to be told no again.',
    'Log the refusal rate per prompt template. A spike is almost always a prompt ' +
      'change or a bad input source, not a change in who your users are.'];
  }
  if (state === 'stopped-by-filter') {
    return ['Branch on incomplete_details.reason as well as on the refusal content ' +
      'type. A filter stop is the platform halting the turn and it needs the same ' +
      'caller-facing message as a refusal.',
    'Count filter stops separately from model refusals. They move for different ' +
      'reasons and folding them together hides both.'];
  }
  if (state === 'truncated') {
    return ['Not a refusal. Check the output ceiling before you look at the prompt: ' +
      'the model was interrupted, not unwilling.'];
  }
  if (state === 'empty-answer') {
    return ['Not a refusal either. Inspect the output item types before concluding ' +
      'anything: a function call is not a message.'];
  }
  return [];
}

async function fetchResponse(key, responseId) {
  const res = await fetch(`${API}/responses/${responseId}`,
    { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: this needs a project key that ` +
                    'can read stored responses');
  }
  if (!res.ok) throw new Error(`${res.status} from /responses/${responseId}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  const idsFile = process.env.RESPONSE_IDS;
  if (!key || !idsFile) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only) and ' +
                  'RESPONSE_IDS (a file of stored response ids, one per line)');
    process.exitCode = 2;
    return;
  }
  const floor = Number(process.env.FLOOR ?? GROUP_FLOOR);
  const showAll = process.env.SHOW_ALL === '1';

  const ids = (await readFile(idsFile, 'utf8')).split('\\n')
    .map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));

  const rows = [];
  let checked = 0;
  let bad = 0;
  for (const responseId of ids) {
    const stored = await fetchResponse(key, responseId);
    checked += 1;
    if (stored === null) {
      console.warn(`${'unreadable'.padEnd(22)} ${responseId}  not found. Stored ` +
        'responses expire, and a response created without storage was never readable.');
      continue;
    }
    const [state, detail] = classify(stored);
    rows.push([groupKey(stored), state]);
    const line = `${state.padEnd(22)} ${responseId}  ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      for (const repair of repairLines(state)) console.warn(`  repair: ${repair}`);
    } else if (state === 'answered') {
      if (showAll) console.log(line);
    } else {
      console.log(line);
      for (const repair of repairLines(state)) console.log(`  note: ${repair}`);
    }
  }

  const rates = refusalRate(rows, floor);
  for (const group of [...rates.keys()].sort()) {
    const row = rates.get(group);
    if (row.rate === null) {
      console.log(`${'group'.padEnd(22)} ${group}  ${row.total} response(s), ` +
        `under the floor of ${floor} so no rate is claimed`);
    } else {
      console.warn(`${'group'.padEnd(22)} ${group}  ${(row.rate * 100).toFixed(1)}% ` +
        `of ${row.total} response(s) refused or filtered`);
    }
  }

  console.log(`${checked} response(s) checked, ${bad} refused or filtered`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note itself: a completed response, no stop reason at all, no text, and a refusal item carrying a sentence. The second is the shape that does real damage &mdash; a preamble followed by a refusal, where naive concatenation produces something that looks like an answer. Then the Chat Completions form, a filter stop that has to stay a separate state, and a truncated response that has to be handed away to the other note rather than counted here. The last two pin the arithmetic: a rate per template over thirty calls, and a single refusal that must not be published as a hundred percent.",
"test_py_file": "test_openai_refusal_channel.py",
"test_py": '''from openai_refusal_channel import (classify, group_key, refusal_rate,
                                    refusals, repair_lines, stop_reason,
                                    visible_text)


def refused(text="I'm sorry, I can't help with that.", preamble=None,
            metadata=None):
    content = []
    if preamble:
        content.append({"type": "output_text", "text": preamble})
    content.append({"type": "refusal", "refusal": text})
    return {"id": "resp_r", "status": "completed", "model": "gpt-5.1",
            "metadata": metadata or {},
            "output": [{"type": "message", "content": content}]}


def answered(text='{"ok": true}', metadata=None):
    return {"id": "resp_a", "status": "completed", "model": "gpt-5.1",
            "metadata": metadata or {},
            "output": [{"type": "message",
                        "content": [{"type": "output_text", "text": text}]}]}


def test_a_refusal_is_a_completed_answer_with_nothing_to_parse():
    # The note in one assertion: 200, status completed, and the payload the
    # parser wanted is simply not the thing the model returned.
    response = refused()
    assert stop_reason(response) is None
    assert visible_text(response) == ""
    assert refusals(response) == [{"index": 0,
                                   "text": "I'm sorry, I can't help with that."}]

    state, detail = classify(response)
    assert state == "refused"
    assert "nothing went wrong" in detail
    assert "first-class branch before parsing" in repair_lines(state)[0]


def test_a_refusal_that_follows_a_preamble_is_not_an_answer_either():
    # The dangerous shape: concatenating the output items produces text, so a
    # naive reader stores the preamble as though it were the record.
    response = refused(preamble="Here is what I found so far. ")
    state, detail = classify(response)
    assert state == "refused-after-partial"
    assert "storing the preamble" in detail
    assert visible_text(response) == "Here is what I found so far."


def test_the_chat_completions_shape_is_read_as_well():
    legacy = {"choices": [{"finish_reason": "stop",
                           "message": {"content": None,
                                       "refusal": "I can't assist with that."}}]}
    assert refusals(legacy)[0]["text"] == "I can't assist with that."
    assert visible_text(legacy) == ""
    assert classify(legacy)[0] == "refused"


def test_a_filter_stop_is_counted_apart_from_a_model_refusal():
    filtered = {"status": "incomplete",
                "incomplete_details": {"reason": "content_filter"},
                "output": []}
    state, detail = classify(filtered)
    assert state == "stopped-by-filter"
    assert "not the model declining it" in detail
    assert "separately from model refusals" in repair_lines(state)[1]


def test_a_truncated_response_is_handed_to_the_other_note():
    # Same 200, same missing payload, and the repair is a ceiling rather than
    # a prompt. Getting these two confused costs an afternoon.
    cut = {"status": "incomplete",
           "incomplete_details": {"reason": "max_output_tokens"},
           "output": [{"type": "message",
                       "content": [{"type": "output_text", "text": '{"a": 1'}]}]}
    state, detail = classify(cut)
    assert state == "truncated"
    assert "Nothing was refused" in detail
    assert "interrupted, not unwilling" in repair_lines(state)[0]


def test_the_rate_is_grouped_by_template_and_withheld_below_the_floor():
    rows = ([(group_key(refused(metadata={"template": "kyc-extract"})), "refused")] * 9
            + [(group_key(answered(metadata={"template": "kyc-extract"})), "answered")] * 21
            + [(group_key(refused(metadata={"template": "rare-path"})), "refused")])
    rates = refusal_rate(rows)
    assert set(rates) == {"kyc-extract", "rare-path"}
    assert rates["kyc-extract"]["total"] == 30
    assert rates["kyc-extract"]["refused"] == 9
    assert abs(rates["kyc-extract"]["rate"] - 0.3) < 1e-9
    # One refusal in one call is 100%, and printing that teaches people to
    # ignore the report.
    assert rates["rare-path"]["total"] == 1
    assert rates["rare-path"]["rate"] is None


def test_grouping_falls_back_without_pretending_it_is_sharp():
    assert group_key(refused(metadata={"template": "kyc-extract"})) == "kyc-extract"
    assert group_key({"prompt": {"id": "pmpt_9"}}) == "prompt:pmpt_9"
    assert group_key({"model": "gpt-5.1"}) == "model:gpt-5.1"
    assert group_key({}) == "model:unknown"
    assert group_key(None) == "model:unknown"


def test_normal_and_empty_responses_are_left_alone():
    assert classify(answered())[0] == "answered"
    assert refusals(answered()) == []
    assert refusals(None) == []
    assert classify({"status": "completed", "output": []})[0] == "empty-answer"
    assert refusal_rate([]) == {}
    assert refusal_rate(None) == {}
''',
"test_js_file": "openai-refusal-channel.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, groupKey, refusalRate, refusals, repairLines, stopReason, visibleText,
} from './openai-refusal-channel.mjs';

const refused = ({ text = "I'm sorry, I can't help with that.",
  preamble = null, metadata = {} } = {}) => {
  const content = [];
  if (preamble) content.push({ type: 'output_text', text: preamble });
  content.push({ type: 'refusal', refusal: text });
  return { id: 'resp_r', status: 'completed', model: 'gpt-5.1', metadata,
    output: [{ type: 'message', content }] };
};

const answered = ({ text = '{"ok": true}', metadata = {} } = {}) => ({
  id: 'resp_a', status: 'completed', model: 'gpt-5.1', metadata,
  output: [{ type: 'message', content: [{ type: 'output_text', text }] }],
});

test('a refusal is a completed answer with nothing to parse', () => {
  const response = refused();
  assert.equal(stopReason(response), null);
  assert.equal(visibleText(response), '');
  assert.deepEqual(refusals(response),
    [{ index: 0, text: "I'm sorry, I can't help with that." }]);

  const [state, detail] = classify(response);
  assert.equal(state, 'refused');
  assert.match(detail, /nothing went wrong/);
  assert.match(repairLines(state)[0], /first-class branch before parsing/);
});

test('a refusal that follows a preamble is not an answer either', () => {
  const response = refused({ preamble: 'Here is what I found so far. ' });
  const [state, detail] = classify(response);
  assert.equal(state, 'refused-after-partial');
  assert.match(detail, /storing the preamble/);
  assert.equal(visibleText(response), 'Here is what I found so far.');
});

test('the chat completions shape is read as well', () => {
  const legacy = { choices: [{ finish_reason: 'stop',
    message: { content: null, refusal: "I can't assist with that." } }] };
  assert.equal(refusals(legacy)[0].text, "I can't assist with that.");
  assert.equal(visibleText(legacy), '');
  assert.equal(classify(legacy)[0], 'refused');
});

test('a filter stop is counted apart from a model refusal', () => {
  const filtered = { status: 'incomplete',
    incomplete_details: { reason: 'content_filter' }, output: [] };
  const [state, detail] = classify(filtered);
  assert.equal(state, 'stopped-by-filter');
  assert.match(detail, /not the model declining it/);
  assert.match(repairLines(state)[1], /separately from model refusals/);
});

test('a truncated response is handed to the other note', () => {
  const cut = { status: 'incomplete',
    incomplete_details: { reason: 'max_output_tokens' },
    output: [{ type: 'message', content: [{ type: 'output_text', text: '{"a": 1' }] }] };
  const [state, detail] = classify(cut);
  assert.equal(state, 'truncated');
  assert.match(detail, /Nothing was refused/);
  assert.match(repairLines(state)[0], /interrupted, not unwilling/);
});

test('the rate is grouped by template and withheld below the floor', () => {
  const rows = [];
  for (let i = 0; i < 9; i += 1) rows.push(['kyc-extract', 'refused']);
  for (let i = 0; i < 21; i += 1) rows.push(['kyc-extract', 'answered']);
  rows.push(['rare-path', 'refused']);

  const rates = refusalRate(rows);
  assert.deepEqual([...rates.keys()].sort(), ['kyc-extract', 'rare-path']);
  assert.equal(rates.get('kyc-extract').total, 30);
  assert.equal(rates.get('kyc-extract').refused, 9);
  assert.ok(Math.abs(rates.get('kyc-extract').rate - 0.3) < 1e-9);
  assert.equal(rates.get('rare-path').total, 1);
  assert.equal(rates.get('rare-path').rate, null);
});

test('grouping falls back without pretending it is sharp', () => {
  assert.equal(groupKey(refused({ metadata: { template: 'kyc-extract' } })), 'kyc-extract');
  assert.equal(groupKey({ prompt: { id: 'pmpt_9' } }), 'prompt:pmpt_9');
  assert.equal(groupKey({ model: 'gpt-5.1' }), 'model:gpt-5.1');
  assert.equal(groupKey({}), 'model:unknown');
  assert.equal(groupKey(null), 'model:unknown');
});

test('normal and empty responses are left alone', () => {
  assert.equal(classify(answered())[0], 'answered');
  assert.deepEqual(refusals(answered()), []);
  assert.deepEqual(refusals(null), []);
  assert.equal(classify({ status: 'completed', output: [] })[0], 'empty-answer');
  assert.equal(refusalRate([]).size, 0);
  assert.equal(refusalRate(null).size, 0);
});
''',
"faq": [
 ("Is a refusal a failure I should alert on?",
  "Not per call. A refusal is a legitimate outcome and alerting on each one produces a channel nobody reads. The rate per prompt template is the thing to watch: a step change there means a prompt shipped, an input source changed, or a new category of request started arriving. That is worth a look. One refusal is worth a log line."),
 ("Why is message.content null instead of holding the refusal text?",
  "Because the refusal is deliberately kept out of the content channel. If it were text, a schema-shaped parse would either fail confusingly or, worse, succeed on something that was never a real answer. Putting it in its own field is what makes it detectable at all. The cost is that code written before the field existed cannot see it."),
 ("How is this different from the response being cut off?",
  "A truncation was interrupted mid-answer and reports a reason for stopping; a refusal completed and reports nothing wrong at all. The repairs have nothing in common: one is a token ceiling, the other is the prompt or the input. Both look identical from a parser, which is why the script names them separately before anything else happens."),
 ("Does Anthropic have the same field?",
  "Not the same shape. Claude reports a declined answer through stop_reason rather than through a distinct content type, so the equivalent check there is on the stop reason of the message. The failure mode is the same one: code that reads content without first reading why the model stopped."),
 ("Should I retry a refusal with a different prompt?",
  "Automatically, no. Re-sending the same prompt is money spent to be told no again, and rewriting the prompt in a retry loop means your production behaviour is a prompt nobody reviewed. Surface the refusal, count it against the template, and change the template deliberately if the rate says it needs changing."),
],
"related": [REL_TRUNC, REL_ADVISORY, REL_OUTPUT_COST],
"citations": [CITE_OAI_STRUCTURED, CITE_OAI_RESPONSES, CITE_AZ_STRUCTURED, CITE_CL_STOP],
},
{
"slug": "strict-false-schema-silently-ignored",
"title": "strict omitted, so the JSON schema is only a suggestion",
"description": "Structured Outputs only guarantees the schema when strict is true. Absent or false, it is a hint the model usually follows, and nothing warns you.",
"h1": "strict omitted, so the JSON schema is only a suggestion",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["strict true structured outputs", "additionalProperties false openai",
             "json_schema strict false", "json_object legacy mode",
             "pydantic validation error intermittent openai"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, plus a file of stored response ids. The schema audit runs on what the response echoes back.",
"lead": "The validator threw about once every fifty calls, always in production, never in a test. Sometimes an extra key nobody had asked for; sometimes an optional field missing that the schema said was required; once a number arriving as a string. It read like flakiness, so it got a retry, and the retry mostly worked, which settled the matter for four months. The schema had been attached to every one of those calls. It had also never once been enforced, because somebody had taken the strict flag out eleven months earlier to make a 400 go away.",
"short_answer": """<p>Read the flag off the response rather than out of your source tree. With a <strong>project key set to Read Only</strong>: <code>GET /v1/responses/{response_id}</code> and inspect the echoed <code>text.format</code>. If <code>type</code> is <code>\"json_schema\"</code> and <code>strict</code> is absent or <code>false</code>, the schema was a hint. If <code>type</code> is <code>\"json_object\"</code>, it is legacy JSON mode: the output is guaranteed to be valid JSON and nothing whatever about its shape.</p>
<p>Structured Outputs guarantees adherence only with <code>strict: true</code> &mdash; in <code>text.format</code> on the Responses API, in <code>response_format.json_schema</code> on Chat Completions, and per tool in <code>tools[].function.strict</code>. Without it the model usually follows the schema, which is precisely why this survives testing: usually is enough for a test suite and not enough for production.</p>
<p>Then answer the question that actually unblocks anyone: <em>why</em> is the flag off? Almost always because the schema cannot satisfy the strict subset. Every object needs <code>additionalProperties: false</code>, every property must appear in <code>required</code>, the root must be a plain object, and a dozen familiar keywords are ignored entirely. The script walks the echoed schema and prints each rule it breaks, with the path.</p>""",
"problem": """<p>Both forms of the request are legal, so nothing anywhere tells you which one you sent. The API accepts a schema with <code>strict: true</code> and a schema without it, and returns a 200 either way. The response looks the same. The output usually looks the same. There is no warning, no header, no deprecation notice, and no difference at all in the happy case, which is most cases.</p>
<p>The failure surfaces at your own validator, at a rate low enough to be mistaken for infrastructure. Pydantic or Zod throws on a field, somebody adds a retry, the retry usually succeeds because the model usually complies, and the incident closes. Meanwhile the records that did get written are the ones where the model complied &mdash; and where it complied differently, with an extra key or a coerced type, nobody checked at all.</p>""",
"why": """<p><strong>Constrained decoding is either on or it is not.</strong> With <code>strict: true</code> the sampler cannot emit a token that would break the schema, so adherence is structural. Without it, the schema is text in the prompt and adherence is a behaviour. Those are not two settings on a dial; they are two different mechanisms, and only one of them has a guarantee attached.</p>
<p><strong>The flag comes out because the schema cannot support it.</strong> The strict subset is narrower than JSON Schema: <code>additionalProperties: false</code> on every object, every property listed in <code>required</code>, a root that is a plain object and never an <code>anyOf</code>. A schema that breaks any of those is rejected outright with strict on, which is a 400 during development, which is when somebody removes the flag and the request starts working. That is why telling people to set strict: true is useless on its own, and why this script prints the blockers instead.</p>
<p><strong>Optional fields are the usual blocker and the fix is counter-intuitive.</strong> Every property must be in <code>required</code>, so an optional field is expressed as a nullable type rather than by omission. Teams reach for leaving it out, get a 400, and conclude the strict subset cannot model their data. It can; the idiom is just unfamiliar.</p>
<p><strong>Several keywords you rely on are silently unenforced.</strong> <code>minLength</code>, <code>maxLength</code>, <code>pattern</code>, <code>format</code>, <code>minimum</code>, <code>maximum</code>, <code>minItems</code>, <code>maxItems</code> and <code>uniqueItems</code> do not constrain decoding. Keeping them for your own validator is fine. Believing the model honours them is not, and the script lists the ones your schema carries so the belief can be corrected explicitly.</p>
<p><strong>Legacy JSON mode is a third state and deserves its own name.</strong> <code>json_object</code> promises valid syntax and says nothing about shape. It is not a weaker schema; it is no schema. Reporting it as \"strict is off\" would understate it, because there is nothing to turn strict on.</p>
<p><strong>Tools carry the flag separately.</strong> A response can declare a strict text format and a function definition with no strict flag at all, and the guarantee then covers exactly the half that asked for it. Tool arguments are constrained per tool. The script reports the gap per tool name rather than as one verdict for the response, which is also where this note stops: <a href=\"/llm/tool-call-arguments-unparseable/\">what an unconstrained tool actually emits</a> is the next note along.</p>""",
"steps": [
 {"h": "Read the format the response carries, not the constant in the repository",
  "body": """<p>The echoed <code>text.format</code> is the only place outside your source tree where the flag can be read back, and it has the advantage of describing the deploy that actually ran. A wrapper library, a feature flag or an older service can all send something different from what the code you are reading appears to send.</p>"""},
 {"h": "Sort into three states, not two",
  "body": """<p><code>json_schema</code> with strict true is enforced. <code>json_schema</code> without it is advisory. <code>json_object</code> is no schema at all. The third is a different conversation from the second and collapsing them makes the report less useful, not shorter.</p>"""},
 {"h": "Walk the schema for every rule the strict subset requires",
  "body": """<p>Per object: <code>additionalProperties: false</code>, and every property present in <code>required</code>. At the root: a plain object, never a composition keyword. Overall: at most five levels of nesting. The script reports each violation with its path, because \"the schema is not eligible\" is not a work item and \"$.lines[].note is missing from required\" is.</p>"""},
 {"h": "List the keywords that will not be enforced whatever you do",
  "body": """<p>They are legal in the schema and ignored by the decoder. Print them explicitly, because a team that believes <code>pattern</code> is holding the line on an identifier format has a validation gap it does not know about, and that gap survives turning strict on.</p>"""},
 {"h": "Check every tool beside the format",
  "body": """<p><code>strict</code> is declared per tool. Report the loose ones by name. A response whose text format is strict and whose <code>refund</code> tool is not is not a passing response; it is a response with a specific, nameable hole in it.</p>"""},
],
"verify": """<p>Fix the blockers, set the flag, and re-read the same ids. The state should move to enforced, and the intermittent validator failures should stop rather than get quieter.</p>
<pre><code class=\"language-bash\">python3 openai_advisory_schema.py --ids response_ids.txt
# advisory-schema    resp_68e0b2  schema 'invoice' was attached with strict absent, so it is a hint the model usually follows rather than a guarantee.
#   repair: strict: true would be refused for this schema until these are fixed:
#   repair:   $: needs additionalProperties: false
#   repair:   $: every property must be listed in required; missing lines, note.
#   repair:   $.invoice_id: minLength are silently unenforced under constrained decoding.
# 240 response(s) checked, 31 with a schema nobody was holding to</code></pre>""",
"code_intro": "One GET per id, and the rest is a walk over data that came back with it. Seven pure functions. <code>declared_format</code> normalises two request shapes into one tuple, because a half-migrated codebase stores both. <code>strict_state</code> is three words long and is the whole finding. <code>schema_blockers</code> is where the work is: a recursive walk that reports, with paths, every reason strict mode would refuse this schema, which is the difference between advice somebody has already tried and a list they can work through. <code>schema_size</code> measures against the documented ceilings, <code>loose_tools</code> finds the per-tool gaps, and the classifier and repair lines assemble the verdict without ever looking at the output text &mdash; because whether this particular call happened to comply is not the question.",
"py_file": "openai_advisory_schema.py",
"py": '''"""Find stored OpenAI responses whose JSON schema was never actually enforced.

Read only. GET /v1/responses/{response_id} for each id you supply, with a
project key set to Read Only. There is no list endpoint for /v1/responses, so
the ids come from your own records: one id per line in a file.

Structured Outputs guarantees schema adherence only when strict is true. With
strict absent or false the schema degrades to a hint the model usually follows,
and the request is accepted either way with no warning of any kind. The stored
response echoes the format it was given, which is the only place outside your
source tree where the flag can be read back.

When strict is off, the interesting question is why, and the answer is almost
always that the schema cannot satisfy the strict subset. So this script does
not stop at the flag: it walks the schema and prints every rule that would have
to be fixed before strict: true could be turned on.

The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_advisory_schema")

API = "https://api.openai.com/v1"

FINDINGS = ("advisory-schema", "no-schema", "advisory-tools")

# Constrained decoding ignores these entirely. A schema that carries them is
# not wrong, but the constraints they express are not enforced by anyone.
UNENFORCED_KEYWORDS = ("minLength", "maxLength", "pattern", "format", "minimum",
                       "maximum", "multipleOf", "minItems", "maxItems",
                       "uniqueItems", "default")

# The documented ceilings for a strict schema.
MAX_DEPTH = 5
MAX_PROPERTIES = 5000
MAX_ENUM_VALUES = 1000


def declared_format(response):
    """The output format the response was generated under. Pure.

    Returns (kind, name, strict, schema). kind is json_schema, json_object,
    text or none. Read from the response rather than from your source tree,
    because the constant in the repository is not necessarily what the running
    deploy sent.
    """
    response = response or {}
    fmt = ((response.get("text") or {}).get("format")
           or response.get("response_format") or {})
    if not isinstance(fmt, dict) or not fmt:
        return ("none", None, None, None)

    kind = str(fmt.get("type") or "none")
    if kind == "json_schema":
        # The Responses API flattens the schema onto the format object; Chat
        # Completions nests it under json_schema. Both shapes are stored.
        inner = fmt.get("json_schema") if isinstance(fmt.get("json_schema"), dict) else fmt
        return ("json_schema", inner.get("name"), inner.get("strict"),
                inner.get("schema"))
    return (kind, None, None, None)


def strict_state(kind, strict):
    """What the declared format actually promises. Pure."""
    if kind == "json_schema":
        return "enforced" if strict is True else "advisory"
    if kind == "json_object":
        return "no-schema"
    if kind in ("text", "none"):
        return "free-text"
    return "unknown-format"


def schema_size(schema, depth=1):
    """Count properties, depth and the largest enum in a schema. Pure.

    Returned as a dict rather than printed, because the interesting comparison
    is against the documented ceilings and those change more often than this
    walk does.
    """
    totals = {"properties": 0, "depth": depth, "enum": 0}
    if not isinstance(schema, dict):
        return totals
    if isinstance(schema.get("enum"), list):
        totals["enum"] = max(totals["enum"], len(schema["enum"]))
    children = []
    properties = schema.get("properties")
    if isinstance(properties, dict):
        totals["properties"] += len(properties)
        children.extend(properties.values())
    items = schema.get("items")
    if isinstance(items, dict):
        children.append(items)
    for group in ("anyOf", "oneOf", "allOf"):
        if isinstance(schema.get(group), list):
            children.extend(x for x in schema[group] if isinstance(x, dict))
    defs = schema.get("$defs")
    if isinstance(defs, dict):
        children.extend(x for x in defs.values() if isinstance(x, dict))

    for child in children:
        below = schema_size(child, depth + 1)
        totals["properties"] += below["properties"]
        totals["depth"] = max(totals["depth"], below["depth"])
        totals["enum"] = max(totals["enum"], below["enum"])
    return totals


def schema_blockers(schema, path="$", depth=1):
    """Every reason strict: true would be refused for this schema. Pure.

    This is the part of the note that pays for itself. Telling somebody to set
    strict: true is useless on its own, because they tried that, the request
    400ed, and the flag came back out. The list of rules the schema breaks is
    the actual work.
    """
    problems = []
    if not isinstance(schema, dict):
        return ["%s: not a schema object" % path] if depth == 1 else problems

    kinds = schema.get("type")
    kinds = kinds if isinstance(kinds, list) else ([kinds] if kinds else [])
    kinds = [str(k) for k in kinds]

    if depth == 1:
        if any(schema.get(group) for group in ("anyOf", "oneOf", "allOf")):
            problems.append("$: the root may not be anyOf, oneOf or allOf; it "
                            "must be a plain object")
        elif "object" not in kinds:
            problems.append("$: the root type must be object, not %s"
                            % (", ".join(kinds) or "unset"))

    if "object" in kinds:
        if schema.get("additionalProperties") is not False:
            problems.append("%s: needs additionalProperties: false" % path)
        properties = schema.get("properties")
        properties = properties if isinstance(properties, dict) else {}
        required = schema.get("required")
        required = set(required) if isinstance(required, list) else set()
        missing = sorted(set(properties) - required)
        if missing:
            problems.append("%s: every property must be listed in required; "
                            "missing %s. Use a nullable type for the optional "
                            "ones rather than leaving them out."
                            % (path, ", ".join(missing)))

    present = [k for k in UNENFORCED_KEYWORDS if k in schema]
    if present:
        problems.append("%s: %s are silently unenforced under constrained "
                        "decoding. Keep them for your own validator if you "
                        "like, but do not rely on the model honouring them."
                        % (path, ", ".join(present)))

    if depth > MAX_DEPTH:
        problems.append("%s: nested %d levels deep, past the limit of %d"
                        % (path, depth, MAX_DEPTH))
        return problems

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name in sorted(properties):
            problems.extend(schema_blockers(properties[name],
                                            "%s.%s" % (path, name), depth + 1))
    items = schema.get("items")
    if isinstance(items, dict):
        problems.extend(schema_blockers(items, path + "[]", depth + 1))
    return problems


def loose_tools(response):
    """Tools echoed on the response whose strict flag is not true. Pure.

    Per tool, because strict is declared per tool. A response can carry a
    strict text format and a function definition with no strict flag at all,
    and the guarantee covers only the half that asked for it.
    """
    loose = []
    for tool in (response or {}).get("tools") or []:
        if not isinstance(tool, dict):
            continue
        if str(tool.get("type") or "function") != "function":
            continue
        inner = tool.get("function") if isinstance(tool.get("function"), dict) else tool
        if inner.get("strict") is not True:
            loose.append(str(inner.get("name") or "unnamed"))
    return loose


def classify(response):
    """Classify one stored response. Pure. Returns (state, detail).

    Nothing here reads the output text. Whether this particular call happened
    to produce a well-shaped object is not the point: the point is that no call
    made under this format was ever obliged to.
    """
    kind, name, strict, schema = declared_format(response)
    state = strict_state(kind, strict)
    loose = loose_tools(response)
    label = ("schema %r" % name) if name else "the declared schema"

    if state == "advisory":
        return ("advisory-schema",
                "%s was attached with strict %s, so it is a hint the model "
                "usually follows rather than a guarantee. Valid JSON of the "
                "wrong shape is a legal outcome here."
                % (label, "false" if strict is False else "absent"))
    if state == "no-schema":
        return ("no-schema",
                "Legacy json_object mode: the output is guaranteed to be valid "
                "JSON and nothing else. No schema was ever attached, so no "
                "shape was ever promised.")
    if state == "free-text":
        return ("free-text",
                "No output format was declared, so there is no contract to "
                "enforce and nothing to report.")
    if state == "unknown-format":
        return ("unknown-format",
                "Format type %r is not one this script knows. Read the raw "
                "record before drawing a conclusion." % kind)

    if loose:
        return ("advisory-tools",
                "The text format is strict, but %d tool definition(s) are not: "
                "%s. Tool arguments are constrained per tool, and an unstrict "
                "tool is unconstrained." % (len(loose), ", ".join(loose)))
    return ("enforced",
            "%s was attached with strict: true, and no tool beside it is "
            "loose." % label)


def repair_lines(response, state):
    """The repair, built from the schema this response actually carried. Pure."""
    _kind, _name, _strict, schema = declared_format(response)
    if state == "free-text" or state == "unknown-format":
        return []
    if state == "enforced":
        return []

    lines = []
    if state == "no-schema":
        lines.append("Move from json_object to a json_schema format with "
                     "strict: true. JSON mode promises syntax and nothing "
                     "about shape, which is why your validator is the first "
                     "thing that ever sees the mismatch.")
    if state == "advisory-tools":
        lines.append("Set strict: true on every tool as well as on the text "
                     "format, with additionalProperties: false and every "
                     "parameter listed in required.")

    blockers = schema_blockers(schema) if schema else []
    if blockers:
        lines.append("strict: true would be refused for this schema until "
                     "these are fixed:")
        lines.extend("  " + b for b in blockers)
    elif state == "advisory-schema":
        lines.append("This schema already satisfies the strict subset, so "
                     "setting strict: true is a one-line change. Somebody "
                     "dropped the flag and the request kept succeeding.")

    if schema:
        size = schema_size(schema)
        if size["properties"] > MAX_PROPERTIES:
            lines.append("The schema declares %d properties, past the limit of "
                         "%d." % (size["properties"], MAX_PROPERTIES))
        if size["enum"] > MAX_ENUM_VALUES:
            lines.append("The largest enum holds %d values, past the limit of "
                         "%d." % (size["enum"], MAX_ENUM_VALUES))
    return lines


def read_ids(path):
    """One response id per line, blanks and # comments ignored."""
    ids = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def fetch_response(session, response_id):
    r = session.get(API + "/responses/" + response_id, timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: this needs a project key that can "
                         "read stored responses" % r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True,
                    help="file of stored response ids, one per line")
    ap.add_argument("--show-all", action="store_true",
                    help="also print responses whose schema is enforced")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY, a project key set to Read Only")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    checked = 0
    bad = 0
    for response_id in read_ids(args.ids):
        stored = fetch_response(session, response_id)
        checked += 1
        if stored is None:
            log.warning("%-18s %s  not found. Stored responses expire, and a "
                        "response created without storage was never readable.",
                        "unreadable", response_id)
            continue
        state, detail = classify(stored)
        line = "%-18s %s  %s" % (state, response_id, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(stored, state):
                log.warning("  repair: %s", repair)
        elif args.show_all or state not in ("enforced", "free-text"):
            log.info(line)

    log.info("%d response(s) checked, %d with a schema nobody was holding to",
             checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-advisory-schema.mjs",
"js": '''/**
 * Find stored OpenAI responses whose JSON schema was never actually enforced.
 *
 * Read only. GET /v1/responses/{response_id} for each id you supply, with a
 * project key set to Read Only. There is no list endpoint for /v1/responses,
 * so the ids come from your own records: one id per line in a file.
 *
 * Structured Outputs guarantees schema adherence only when strict is true.
 * With strict absent or false the schema degrades to a hint the model usually
 * follows, and the request is accepted either way with no warning. The stored
 * response echoes the format it was given, which is the only place outside
 * your source tree where the flag can be read back.
 *
 * When strict is off, the interesting question is why, so this script walks
 * the schema and prints every rule that would have to be fixed first.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

const FINDINGS = new Set(['advisory-schema', 'no-schema', 'advisory-tools']);

// Constrained decoding ignores these entirely.
const UNENFORCED_KEYWORDS = ['minLength', 'maxLength', 'pattern', 'format',
  'minimum', 'maximum', 'multipleOf', 'minItems', 'maxItems', 'uniqueItems',
  'default'];

const MAX_DEPTH = 5;
const MAX_PROPERTIES = 5000;
const MAX_ENUM_VALUES = 1000;

/**
 * The output format the response was generated under. Pure.
 * Returns [kind, name, strict, schema]. Read from the response, not from your
 * source tree: the constant in the repository is not necessarily what the
 * running deploy sent.
 */
export function declaredFormat(response) {
  const fmt = response?.text?.format ?? response?.response_format ?? {};
  if (!fmt || typeof fmt !== 'object' || Object.keys(fmt).length === 0) {
    return ['none', null, null, null];
  }
  const kind = String(fmt.type ?? 'none');
  if (kind === 'json_schema') {
    const inner = (fmt.json_schema && typeof fmt.json_schema === 'object')
      ? fmt.json_schema : fmt;
    return ['json_schema', inner.name ?? null, inner.strict ?? null,
      inner.schema ?? null];
  }
  return [kind, null, null, null];
}

/** What the declared format actually promises. Pure. */
export function strictState(kind, strict) {
  if (kind === 'json_schema') return strict === true ? 'enforced' : 'advisory';
  if (kind === 'json_object') return 'no-schema';
  if (kind === 'text' || kind === 'none') return 'free-text';
  return 'unknown-format';
}

/** Count properties, depth and the largest enum in a schema. Pure. */
export function schemaSize(schema, depth = 1) {
  const totals = { properties: 0, depth, enum: 0 };
  if (!schema || typeof schema !== 'object') return totals;
  if (Array.isArray(schema.enum)) totals.enum = Math.max(totals.enum, schema.enum.length);

  const children = [];
  if (schema.properties && typeof schema.properties === 'object') {
    const values = Object.values(schema.properties);
    totals.properties += values.length;
    children.push(...values);
  }
  if (schema.items && typeof schema.items === 'object') children.push(schema.items);
  for (const group of ['anyOf', 'oneOf', 'allOf']) {
    if (Array.isArray(schema[group])) {
      children.push(...schema[group].filter((x) => x && typeof x === 'object'));
    }
  }
  if (schema.$defs && typeof schema.$defs === 'object') {
    children.push(...Object.values(schema.$defs).filter((x) => x && typeof x === 'object'));
  }

  for (const child of children) {
    const below = schemaSize(child, depth + 1);
    totals.properties += below.properties;
    totals.depth = Math.max(totals.depth, below.depth);
    totals.enum = Math.max(totals.enum, below.enum);
  }
  return totals;
}

/**
 * Every reason strict: true would be refused for this schema. Pure.
 * Telling somebody to set strict: true is useless on its own: they tried, the
 * request 400ed, and the flag came back out. This list is the actual work.
 */
export function schemaBlockers(schema, path = '$', depth = 1) {
  const problems = [];
  if (!schema || typeof schema !== 'object' || Array.isArray(schema)) {
    return depth === 1 ? [`${path}: not a schema object`] : problems;
  }

  const raw = schema.type;
  const kinds = (Array.isArray(raw) ? raw : (raw ? [raw] : [])).map(String);

  if (depth === 1) {
    if (['anyOf', 'oneOf', 'allOf'].some((g) => schema[g])) {
      problems.push('$: the root may not be anyOf, oneOf or allOf; it must be ' +
        'a plain object');
    } else if (!kinds.includes('object')) {
      problems.push(`$: the root type must be object, not ${kinds.join(', ') || 'unset'}`);
    }
  }

  if (kinds.includes('object')) {
    if (schema.additionalProperties !== false) {
      problems.push(`${path}: needs additionalProperties: false`);
    }
    const properties = (schema.properties && typeof schema.properties === 'object')
      ? schema.properties : {};
    const required = new Set(Array.isArray(schema.required) ? schema.required : []);
    const missing = Object.keys(properties).filter((k) => !required.has(k)).sort();
    if (missing.length) {
      problems.push(`${path}: every property must be listed in required; ` +
        `missing ${missing.join(', ')}. Use a nullable type for the optional ` +
        'ones rather than leaving them out.');
    }
  }

  const present = UNENFORCED_KEYWORDS.filter((k) => k in schema);
  if (present.length) {
    problems.push(`${path}: ${present.join(', ')} are silently unenforced under ` +
      'constrained decoding. Keep them for your own validator if you like, but ' +
      'do not rely on the model honouring them.');
  }

  if (depth > MAX_DEPTH) {
    problems.push(`${path}: nested ${depth} levels deep, past the limit of ${MAX_DEPTH}`);
    return problems;
  }

  if (schema.properties && typeof schema.properties === 'object') {
    for (const name of Object.keys(schema.properties).sort()) {
      problems.push(...schemaBlockers(schema.properties[name], `${path}.${name}`, depth + 1));
    }
  }
  if (schema.items && typeof schema.items === 'object') {
    problems.push(...schemaBlockers(schema.items, `${path}[]`, depth + 1));
  }
  return problems;
}

/** Tools echoed on the response whose strict flag is not true. Pure. Per tool. */
export function looseTools(response) {
  const loose = [];
  for (const tool of response?.tools ?? []) {
    if (!tool || typeof tool !== 'object') continue;
    if (String(tool.type ?? 'function') !== 'function') continue;
    const inner = (tool.function && typeof tool.function === 'object') ? tool.function : tool;
    if (inner.strict !== true) loose.push(String(inner.name ?? 'unnamed'));
  }
  return loose;
}

/**
 * Classify one stored response. Pure.
 * Nothing here reads the output text: whether this call happened to produce a
 * well-shaped object is not the point. No call under this format was obliged to.
 */
export function classify(response) {
  const [kind, name, strict] = declaredFormat(response);
  const state = strictState(kind, strict);
  const loose = looseTools(response);
  const label = name ? `schema '${name}'` : 'the declared schema';

  if (state === 'advisory') {
    return ['advisory-schema',
      `${label} was attached with strict ${strict === false ? 'false' : 'absent'}, ` +
      'so it is a hint the model usually follows rather than a guarantee. Valid ' +
      'JSON of the wrong shape is a legal outcome here.'];
  }
  if (state === 'no-schema') {
    return ['no-schema',
      'Legacy json_object mode: the output is guaranteed to be valid JSON and ' +
      'nothing else. No schema was ever attached, so no shape was ever promised.'];
  }
  if (state === 'free-text') {
    return ['free-text',
      'No output format was declared, so there is no contract to enforce and ' +
      'nothing to report.'];
  }
  if (state === 'unknown-format') {
    return ['unknown-format',
      `Format type '${kind}' is not one this script knows. Read the raw record ` +
      'before drawing a conclusion.'];
  }

  if (loose.length) {
    return ['advisory-tools',
      `The text format is strict, but ${loose.length} tool definition(s) are ` +
      `not: ${loose.join(', ')}. Tool arguments are constrained per tool, and ` +
      'an unstrict tool is unconstrained.'];
  }
  return ['enforced',
    `${label} was attached with strict: true, and no tool beside it is loose.`];
}

/** The repair, built from the schema this response actually carried. Pure. */
export function repairLines(response, state) {
  const schema = declaredFormat(response)[3];
  if (state === 'free-text' || state === 'unknown-format' || state === 'enforced') {
    return [];
  }

  const lines = [];
  if (state === 'no-schema') {
    lines.push('Move from json_object to a json_schema format with strict: true. ' +
      'JSON mode promises syntax and nothing about shape, which is why your ' +
      'validator is the first thing that ever sees the mismatch.');
  }
  if (state === 'advisory-tools') {
    lines.push('Set strict: true on every tool as well as on the text format, ' +
      'with additionalProperties: false and every parameter listed in required.');
  }

  const blockers = schema ? schemaBlockers(schema) : [];
  if (blockers.length) {
    lines.push('strict: true would be refused for this schema until these are fixed:');
    lines.push(...blockers.map((b) => `  ${b}`));
  } else if (state === 'advisory-schema') {
    lines.push('This schema already satisfies the strict subset, so setting ' +
      'strict: true is a one-line change. Somebody dropped the flag and the ' +
      'request kept succeeding.');
  }

  if (schema) {
    const size = schemaSize(schema);
    if (size.properties > MAX_PROPERTIES) {
      lines.push(`The schema declares ${size.properties} properties, past the ` +
        `limit of ${MAX_PROPERTIES}.`);
    }
    if (size.enum > MAX_ENUM_VALUES) {
      lines.push(`The largest enum holds ${size.enum} values, past the limit of ` +
        `${MAX_ENUM_VALUES}.`);
    }
  }
  return lines;
}

async function fetchResponse(key, responseId) {
  const res = await fetch(`${API}/responses/${responseId}`,
    { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: this needs a project key that ` +
                    'can read stored responses');
  }
  if (!res.ok) throw new Error(`${res.status} from /responses/${responseId}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  const idsFile = process.env.RESPONSE_IDS;
  if (!key || !idsFile) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only) and ' +
                  'RESPONSE_IDS (a file of stored response ids, one per line)');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';

  const ids = (await readFile(idsFile, 'utf8')).split('\\n')
    .map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));

  let checked = 0;
  let bad = 0;
  for (const responseId of ids) {
    const stored = await fetchResponse(key, responseId);
    checked += 1;
    if (stored === null) {
      console.warn(`${'unreadable'.padEnd(18)} ${responseId}  not found. Stored ` +
        'responses expire, and a response created without storage was never readable.');
      continue;
    }
    const [state, detail] = classify(stored);
    const line = `${state.padEnd(18)} ${responseId}  ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      for (const repair of repairLines(stored, state)) console.warn(`  repair: ${repair}`);
    } else if (showAll || (state !== 'enforced' && state !== 'free-text')) {
      console.log(line);
    }
  }

  console.log(`${checked} response(s) checked, ${bad} with a schema nobody was ` +
              'holding to');
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the trap in one assertion: a response carrying perfectly valid JSON of exactly the right shape, which is nonetheless a finding, because nothing obliged it to be. Then strict false reading identically to strict missing, and legacy JSON mode getting its own name rather than being folded in. The schema walker is tested on a schema that breaks three rules at once and must report all three with paths &mdash; and, just as importantly, must stay quiet about the nested object that already complies, since a checker that flags everything gets muted. The last two cover the root that cannot be strict at all and a strict format sitting beside a loose tool.",
"test_py_file": "test_openai_advisory_schema.py",
"test_py": '''from openai_advisory_schema import (classify, declared_format, loose_tools,
                                    repair_lines, schema_blockers, schema_size,
                                    strict_state)

TIGHT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["invoice_id", "total"],
    "properties": {"invoice_id": {"type": "string"},
                   "total": {"type": "number"}},
}


def response(fmt, tools=None):
    body = {"id": "resp_s", "status": "completed", "model": "gpt-5.1",
            "text": {"format": fmt},
            "output": [{"type": "message",
                        "content": [{"type": "output_text",
                                     "text": '{"invoice_id": "INV-1", "total": 1}'}]}]}
    if tools is not None:
        body["tools"] = tools
    return body


def test_a_schema_without_strict_is_advice_and_the_json_still_parsed():
    # The trap: this response is a 200 carrying perfectly valid JSON of the
    # right shape. Nothing about the output says the contract was optional.
    stored = response({"type": "json_schema", "name": "invoice", "schema": TIGHT})
    assert declared_format(stored)[:3] == ("json_schema", "invoice", None)
    assert strict_state("json_schema", None) == "advisory"

    state, detail = classify(stored)
    assert state == "advisory-schema"
    assert "strict absent" in detail
    assert "wrong shape is a legal outcome" in detail
    # The schema is already eligible, so the repair is one line rather than a
    # rewrite. Saying so is the difference between a useful report and a chore.
    assert "one-line change" in " ".join(repair_lines(stored, state))


def test_strict_false_reads_the_same_as_strict_missing():
    stored = response({"type": "json_schema", "name": "invoice",
                       "strict": False, "schema": TIGHT})
    state, detail = classify(stored)
    assert state == "advisory-schema"
    assert "strict false" in detail


def test_legacy_json_object_mode_is_named_as_its_own_thing():
    stored = response({"type": "json_object"})
    state, detail = classify(stored)
    assert state == "no-schema"
    assert "valid JSON and nothing else" in detail
    assert "json_object to a json_schema" in repair_lines(stored, state)[0]


def test_schema_blockers_names_every_rule_the_subset_requires():
    loose = {
        "type": "object",
        "required": ["invoice_id"],
        "properties": {
            "invoice_id": {"type": "string", "minLength": 3},
            "note": {"type": "string"},
            "lines": {"type": "array",
                      "items": {"type": "object",
                                "additionalProperties": False,
                                "properties": {"sku": {"type": "string"}},
                                "required": ["sku"]}},
        },
    }
    found = " | ".join(schema_blockers(loose))
    assert "$: needs additionalProperties: false" in found
    assert "missing lines, note" in found
    assert "minLength are silently unenforced" in found
    # The nested object below the array already obeys the rules, so it must
    # not be reported. A checker that flags everything gets muted.
    assert "$.lines[]" not in found
    assert schema_blockers(TIGHT) == []


def test_a_root_that_is_not_a_plain_object_cannot_be_strict_at_all():
    assert "root may not be anyOf" in schema_blockers(
        {"anyOf": [TIGHT, {"type": "object"}]})[0]
    assert "root type must be object, not array" in schema_blockers(
        {"type": "array", "items": TIGHT})[0]
    assert "not a schema object" in schema_blockers(None)[0]


def test_depth_beyond_five_levels_is_reported_and_the_walk_stops():
    schema = {"type": "object", "additionalProperties": False,
              "required": ["a"], "properties": {"a": {"type": "string"}}}
    for _ in range(6):
        schema = {"type": "object", "additionalProperties": False,
                  "required": ["child"], "properties": {"child": schema}}
    found = schema_blockers(schema)
    assert any("past the limit of 5" in f for f in found)
    assert schema_size(schema)["depth"] > 5


def test_a_strict_format_beside_a_loose_tool_is_still_a_gap():
    tools = [{"type": "function", "name": "charge", "parameters": TIGHT,
              "strict": True},
             {"type": "function", "name": "refund", "parameters": TIGHT}]
    stored = response({"type": "json_schema", "name": "invoice",
                       "strict": True, "schema": TIGHT}, tools=tools)
    assert loose_tools(stored) == ["refund"]
    state, detail = classify(stored)
    assert state == "advisory-tools"
    assert "refund" in detail
    assert "every tool as well as on the text format" in repair_lines(stored, state)[0]


def test_the_chat_completions_shape_and_the_clean_cases():
    legacy = {"response_format": {"type": "json_schema",
                                  "json_schema": {"name": "invoice",
                                                  "strict": True,
                                                  "schema": TIGHT}}}
    assert declared_format(legacy)[:3] == ("json_schema", "invoice", True)
    assert classify(legacy)[0] == "enforced"
    assert classify({})[0] == "free-text"
    assert classify(None)[0] == "free-text"
    assert repair_lines({}, "free-text") == []
    assert loose_tools({}) == []
    assert schema_size({}) == {"properties": 0, "depth": 1, "enum": 0}
''',
"test_js_file": "openai-advisory-schema.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, declaredFormat, looseTools, repairLines, schemaBlockers, schemaSize,
  strictState,
} from './openai-advisory-schema.mjs';

const TIGHT = {
  type: 'object',
  additionalProperties: false,
  required: ['invoice_id', 'total'],
  properties: { invoice_id: { type: 'string' }, total: { type: 'number' } },
};

const response = (format, tools) => {
  const body = { id: 'resp_s', status: 'completed', model: 'gpt-5.1',
    text: { format },
    output: [{ type: 'message', content: [{ type: 'output_text',
      text: '{"invoice_id": "INV-1", "total": 1}' }] }] };
  if (tools !== undefined) body.tools = tools;
  return body;
};

test('a schema without strict is advice and the json still parsed', () => {
  const stored = response({ type: 'json_schema', name: 'invoice', schema: TIGHT });
  assert.deepEqual(declaredFormat(stored).slice(0, 3), ['json_schema', 'invoice', null]);
  assert.equal(strictState('json_schema', null), 'advisory');

  const [state, detail] = classify(stored);
  assert.equal(state, 'advisory-schema');
  assert.match(detail, /strict absent/);
  assert.match(detail, /wrong shape is a legal outcome/);
  assert.match(repairLines(stored, state).join(' '), /one-line change/);
});

test('strict false reads the same as strict missing', () => {
  const stored = response({ type: 'json_schema', name: 'invoice',
    strict: false, schema: TIGHT });
  const [state, detail] = classify(stored);
  assert.equal(state, 'advisory-schema');
  assert.match(detail, /strict false/);
});

test('legacy json_object mode is named as its own thing', () => {
  const stored = response({ type: 'json_object' });
  const [state, detail] = classify(stored);
  assert.equal(state, 'no-schema');
  assert.match(detail, /valid JSON and nothing else/);
  assert.match(repairLines(stored, state)[0], /json_object to a json_schema/);
});

test('schemaBlockers names every rule the subset requires', () => {
  const loose = {
    type: 'object',
    required: ['invoice_id'],
    properties: {
      invoice_id: { type: 'string', minLength: 3 },
      note: { type: 'string' },
      lines: { type: 'array',
        items: { type: 'object', additionalProperties: false,
          properties: { sku: { type: 'string' } }, required: ['sku'] } },
    },
  };
  const found = schemaBlockers(loose).join(' | ');
  assert.match(found, /\\$: needs additionalProperties: false/);
  assert.match(found, /missing lines, note/);
  assert.match(found, /minLength are silently unenforced/);
  assert.ok(!found.includes('$.lines[]'));
  assert.deepEqual(schemaBlockers(TIGHT), []);
});

test('a root that is not a plain object cannot be strict at all', () => {
  assert.match(schemaBlockers({ anyOf: [TIGHT, { type: 'object' }] })[0],
    /root may not be anyOf/);
  assert.match(schemaBlockers({ type: 'array', items: TIGHT })[0],
    /root type must be object, not array/);
  assert.match(schemaBlockers(null)[0], /not a schema object/);
});

test('depth beyond five levels is reported and the walk stops', () => {
  let schema = { type: 'object', additionalProperties: false,
    required: ['a'], properties: { a: { type: 'string' } } };
  for (let i = 0; i < 6; i += 1) {
    schema = { type: 'object', additionalProperties: false,
      required: ['child'], properties: { child: schema } };
  }
  assert.ok(schemaBlockers(schema).some((f) => f.includes('past the limit of 5')));
  assert.ok(schemaSize(schema).depth > 5);
});

test('a strict format beside a loose tool is still a gap', () => {
  const tools = [
    { type: 'function', name: 'charge', parameters: TIGHT, strict: true },
    { type: 'function', name: 'refund', parameters: TIGHT },
  ];
  const stored = response({ type: 'json_schema', name: 'invoice',
    strict: true, schema: TIGHT }, tools);
  assert.deepEqual(looseTools(stored), ['refund']);
  const [state, detail] = classify(stored);
  assert.equal(state, 'advisory-tools');
  assert.match(detail, /refund/);
  assert.match(repairLines(stored, state)[0], /every tool as well as on the text format/);
});

test('the chat completions shape and the clean cases', () => {
  const legacy = { response_format: { type: 'json_schema',
    json_schema: { name: 'invoice', strict: true, schema: TIGHT } } };
  assert.deepEqual(declaredFormat(legacy).slice(0, 3), ['json_schema', 'invoice', true]);
  assert.equal(classify(legacy)[0], 'enforced');
  assert.equal(classify({})[0], 'free-text');
  assert.equal(classify(null)[0], 'free-text');
  assert.deepEqual(repairLines({}, 'free-text'), []);
  assert.deepEqual(looseTools({}), []);
  assert.deepEqual(schemaSize({}), { properties: 0, depth: 1, enum: 0 });
});
''',
"faq": [
 ("If the model follows the schema anyway, does the flag matter?",
  "It matters exactly as much as the tail matters to you. Without strict you are relying on a behaviour that holds most of the time and has no floor: it can shift with a model version, with prompt length, with how unusual the input is. If a wrong-shaped record costs nothing, live with it. If it reaches a database or a payment, the guarantee is the whole point of using structured outputs at all."),
 ("Why was strict removed in the first place?",
  "Almost always because turning it on produced a 400. The strict subset is narrower than JSON Schema and a real-world schema usually breaks two or three of its rules on the first attempt. Removing the flag makes the error go away instantly and changes nothing visible, which is a nearly perfect trap. That is why this script prints the specific rules rather than the advice."),
 ("How do I express an optional field if everything must be required?",
  "As a nullable type: list the property in required and give it a type of string or null. The field is then always present and may be null, which is the same information in a shape constrained decoding can hold. Leaving properties out of required is the single most common reason a schema cannot be made strict."),
 ("Is json_object mode just a weaker version of this?",
  "No, it is a different thing and the script names it separately. JSON mode guarantees the output parses as JSON. It says nothing about keys, types, or structure, so there is no schema to enforce and no flag to set. Moving from json_object to a json_schema format is a change to the request, not a flag flip."),
 ("What about tools? Does the format flag cover them?",
  "It does not. strict is declared per tool in tools[].function.strict, so a response can have a strict text format and an entirely unconstrained function definition beside it. The script reports the loose tools by name. What those tools then emit, and how it breaks a dispatcher, is the subject of the tool-arguments note."),
],
"related": [REL_ARGS, REL_TRUNC, REL_ALIAS],
"citations": [CITE_OAI_STRUCTURED, CITE_AZ_STRUCTURED, CITE_OAI_LIMITS, CITE_OAI_RESPONSES],
},
{
"slug": "tool-call-arguments-unparseable",
"title": "Tool-call arguments that parse and still break the schema",
"description": "Function arguments arrive as a JSON string that may be malformed, or may parse cleanly and violate the declared schema. Your dispatcher throws, not the API.",
"h1": "Tool-call arguments that parse and still break the schema",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["tool_calls arguments json decode error", "function_call arguments string",
             "openai tool arguments malformed", "strict true tool schema",
             "agent loop crashes on tool call"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, plus a file of stored response ids. The tool schemas come back on the response itself.",
"lead": "The agent had been running for a month when a run started dying in the middle of a turn, roughly once in three hundred calls, always on the same tool. The traceback was a KeyError inside the handler, four frames below anything that knew about HTTP. The arguments string had parsed without complaint. It was well-formed JSON, it was even plausible JSON, and it described a call to a function whose signature had changed in a pull request the tool schema had not followed.",
"short_answer": """<p>Parse the arguments, and then keep going. With a <strong>project key set to Read Only</strong>: <code>GET /v1/responses/{response_id}</code>, take every output item with <code>type: \"function_call\"</code>, and read its <code>arguments</code> field &mdash; which is a <strong>string</strong> containing JSON, not an object. The documentation is explicit that the string may be malformed.</p>
<p>The second half is the half nobody writes. The same response object carries the <code>tools</code> it was generated with, so the declared parameter schema is right there beside the emitted call. Validate one against the other: required parameters that are absent, keys that were never declared, values of the wrong type, enum values that are not in the enum. Every one of those parses perfectly and none of them is dispatchable.</p>
<p>Attribute a parse failure before you report it. If the response also stopped on the output ceiling, the argument string was cut mid-write and belongs to <a href=\"/llm/structured-output-truncated-by-length/\">the truncation note</a>; the tool schema is not the problem and tightening it will not help.</p>
<p>And treat an unknown tool name as its own state. A dispatcher that indexes a handler map by name raises there, before any argument is touched, which is a different bug with a different cause: a tool renamed on one side of the wire only.</p>""",
"problem": """<p>Everything the API promised, it delivered. The response is a 200, the tool call is well-formed as a protocol object, and <code>arguments</code> contains exactly what the model produced. The contract that broke is between the model and your handler, and there is no layer in between that was ever asked to check it.</p>
<p>In a single-turn application that is a lost record. In an agent loop it is worse, because the turn dies with a tool call in the conversation and no result beside it. Retrying the turn replays the same broken call. Retrying the whole run costs every token spent so far. And the failure rate is low enough &mdash; a few calls in a thousand &mdash; that it reads as a transient until somebody reads a stored response carefully.</p>""",
"why": """<p><strong>Arguments are a string, deliberately, and strings can be wrong.</strong> They arrive JSON-encoded rather than as a parsed object, and the docs say plainly that they may not parse. Without <code>strict: true</code> on the tool there is no grammar constraining generation at all: the model is writing JSON from memory, and mostly it is very good at that.</p>
<p><strong>The failure this note is about survives a perfect parse.</strong> Wrapping <code>json.loads</code> in a try/except is the advice everyone has heard and it catches the smaller half of the problem. A missing required parameter, a string where an integer belongs, an extra key, an enum value that is close but not in the list &mdash; all of those are valid JSON. The exception they cause is raised by your dispatcher, sometimes several frames into a handler, and it is not a JSON error at all.</p>
<p><strong>The schema is on the response, which makes this checkable without your source.</strong> Because the tool definitions are echoed back, the comparison can be made from stored data alone: this is the call the model made, and this is the schema it was given. No guessing about what the running deploy sent, and no need to keep a copy of the schema in the checker.</p>
<p><strong>A cut argument string is a different note wearing this one's clothes.</strong> When the ceiling lands mid-write the arguments are a truncated prefix, and the parse error is downstream of a token budget rather than a schema. The script checks the response status first and says so, because tightening a tool schema to fix an output ceiling is a change that cannot possibly work.</p>
<p><strong>An unknown tool name is a lookup failure, not a parse failure.</strong> It comes from a tool renamed on one side of the wire, a handler map that drifted from the tool list, or a model recalling a tool from earlier in the conversation. The arguments may be immaculate. The dispatcher still raises, and it raises earlier, which is why the state is separate.</p>
<p><strong>Even a valid call deserves a note when the tool is not strict.</strong> This one matched the schema. Nothing promised the next one would. That is <a href=\"/llm/strict-false-schema-silently-ignored/\">the advisory-schema note</a> seen from the tool side, and the script reports it quietly rather than as a finding, because it is a risk rather than a defect.</p>""",
"steps": [
 {"h": "Pull every function call out of the stored responses",
  "body": """<p>Responses API: output items with <code>type: \"function_call\"</code>, each carrying <code>name</code>, <code>call_id</code> and <code>arguments</code>. Chat Completions: <code>message.tool_calls[]</code> with the same content under <code>function</code>. Read both, in emission order, because a half-migrated codebase has both in its records and a turn with several calls needs each one judged separately.</p>"""},
 {"h": "Check whether the response was cut before blaming the arguments",
  "body": """<p><code>status: \"incomplete\"</code> with <code>incomplete_details.reason == \"max_output_tokens\"</code> means the argument string was truncated mid-write. Report that as its own state and send the reader to the ceiling. Doing this check second, after the parse, produces a report full of parse errors with one real cause hidden inside them.</p>"""},
 {"h": "Parse, and treat an empty string as an empty object",
  "body": """<p>A tool that takes no parameters is legally called with an empty <code>arguments</code> string, and a bare <code>json.loads</code> raises on it. That single case accounts for a surprising share of the JSONDecodeErrors people attribute to model behaviour.</p>"""},
 {"h": "Validate the parsed object against the declared schema",
  "body": """<p>Required parameters present, no undeclared keys where <code>additionalProperties: false</code>, types matching, enums respected, and the same rules applied to nested objects and array items. Report the path of each violation. This is the step that finds the calls a try/except will never see.</p>"""},
 {"h": "Print the repair as a loop change, not just a flag",
  "body": """<p>Two things fix this permanently. Validate before dispatch and return the validation error to the model as the tool result, so it corrects itself instead of crashing the turn. And set <code>strict: true</code> on the tool, with <code>additionalProperties: false</code> and every parameter required, so the grammar is constrained in the first place.</p>"""},
],
"verify": """<p>After validation moves in front of dispatch, re-run over a fresh window of ids. The violations should still appear in the report &mdash; the model has not changed &mdash; and none of them should be reaching a handler any more.</p>
<pre><code class=\"language-bash\">python3 openai_tool_call_arguments.py --ids response_ids.txt
# arguments-violate-schema    resp_68f11c charge/call_1  the arguments parse cleanly and break the declared schema in 3 place(s): arguments.amount_cents: expected integer, got str; arguments.currency: 'gbp' is not one of the 2 declared value(s); arguments.idempotency_key: not declared, and the schema forbids extra keys
#   repair: Validate arguments against the tool schema before dispatch, and feed the validation error back to the model as the tool result so it can correct itself.
#   repair: Set strict: true on tool charge, with additionalProperties: false and every parameter listed in required.
# 512 tool call(s) checked, 7 your dispatcher cannot use</code></pre>""",
"code_intro": "One GET per id and nothing else; the tool schemas travel with the response. Eight pure functions. <code>function_calls</code> and <code>declared_tools</code> read the two API surfaces into one shape. <code>parse_arguments</code> is small and opinionated: an empty string is an empty object, because a tool that takes nothing is called that way and a bare parse raises on it. <code>schema_violations</code> is the centre of the note &mdash; a recursive walk covering types, required keys, undeclared keys and enums, which is deliberately not a full JSON Schema implementation and is exactly the set of failures that reach a dispatcher. Then the truncation test that keeps another note's findings out of this one, the classifier whose ordering matters, and the repair lines.",
"py_file": "openai_tool_call_arguments.py",
"py": '''"""Check every stored tool call against the tool schema declared beside it.

Read only. GET /v1/responses/{response_id} for each id you supply, with a
project key set to Read Only. There is no list endpoint for /v1/responses, so
the ids come from your own records: one id per line in a file.

Function arguments come back JSON encoded, as a string, and the documentation
is explicit that the string may be malformed. Two quite different faults arrive
through that one field:

  * the string will not parse, which a careful try/except catches;
  * the string parses perfectly and describes a call your handler cannot
    accept, which nothing around json.loads will ever catch.

The second one is why this script exists. The response object carries the tool
definitions it was generated with, so the declared schema and the emitted call
can be compared without reading a line of your source, and the thing that
throws in production is your dispatcher rather than the API.

The repair is printed, never performed.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_tool_call_arguments")

API = "https://api.openai.com/v1"

FINDINGS = ("arguments-violate-schema", "arguments-unparseable", "unknown-tool")

# JSON Schema type names mapped onto what a parsed document can actually be.
TYPE_TESTS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
}


def function_calls(response):
    """Every function call in a stored response. Pure.

    Returns dicts with name, call_id and the raw arguments string, in the order
    the model emitted them. Both surfaces: the Responses API puts a
    function_call item in output[], Chat Completions puts tool_calls on the
    message.
    """
    calls = []
    response = response or {}
    for item in response.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "function_call":
            continue
        calls.append({"name": str(item.get("name") or ""),
                      "call_id": str(item.get("call_id") or item.get("id") or ""),
                      "arguments": item.get("arguments")})
    for choice in response.get("choices") or []:
        for call in (choice.get("message") or {}).get("tool_calls") or []:
            fn = call.get("function") or {}
            calls.append({"name": str(fn.get("name") or ""),
                          "call_id": str(call.get("id") or ""),
                          "arguments": fn.get("arguments")})
    return calls


def declared_tools(response):
    """The tool definitions the response was generated with. Pure.

    Keyed by name, carrying the parameter schema and the strict flag. Taken
    from the response rather than from your source tree, because the definition
    that matters is the one that was actually sent.
    """
    tools = {}
    for tool in (response or {}).get("tools") or []:
        if not isinstance(tool, dict):
            continue
        if str(tool.get("type") or "function") != "function":
            continue
        inner = tool.get("function") if isinstance(tool.get("function"), dict) else tool
        name = str(inner.get("name") or "")
        if name:
            tools[name] = {"parameters": inner.get("parameters"),
                           "strict": inner.get("strict") is True}
    return tools


def parse_arguments(text):
    """Parse one arguments string. Pure. Returns (value, error).

    error is None on success. An empty string is a legal way for a model to
    call a tool that takes nothing, so it parses to an empty object rather than
    failing, which is a distinction a naive json.loads gets wrong on its first
    day in production.
    """
    if text is None:
        return (None, "the arguments field is absent")
    if isinstance(text, dict):
        # Some SDKs hand back a parsed object. Nothing to do.
        return (text, None)
    body = str(text).strip()
    if not body:
        return ({}, None)
    try:
        value = json.loads(body)
    except ValueError as exc:
        return (None, str(exc))
    if not isinstance(value, dict):
        return (None, "arguments parsed to %s, not an object"
                % type(value).__name__)
    return (value, None)


def schema_violations(value, schema, path="arguments"):
    """Where a parsed argument object departs from its declared schema. Pure.

    Deliberately small: types, required keys, unexpected keys and enums. Those
    four cover the failures that actually reach a dispatcher, and a full JSON
    Schema implementation in a field note would be a library nobody asked for.
    """
    problems = []
    if not isinstance(schema, dict) or not schema:
        return problems

    raw = schema.get("type")
    kinds = raw if isinstance(raw, list) else ([raw] if raw else [])
    kinds = [str(k) for k in kinds]
    known = [k for k in kinds if k in TYPE_TESTS]
    if known and not any(TYPE_TESTS[k](value) for k in known):
        got = "null" if value is None else type(value).__name__
        return ["%s: expected %s, got %s" % (path, " or ".join(known), got)]

    choices = schema.get("enum")
    if isinstance(choices, list) and choices and value not in choices:
        problems.append("%s: %r is not one of the %d declared value(s)"
                        % (path, value, len(choices)))

    if isinstance(value, dict):
        properties = schema.get("properties")
        properties = properties if isinstance(properties, dict) else {}
        required = schema.get("required")
        required = required if isinstance(required, list) else []
        for name in required:
            if name not in value:
                problems.append("%s.%s: required and missing" % (path, name))
        if schema.get("additionalProperties") is False:
            for name in sorted(set(value) - set(properties)):
                problems.append("%s.%s: not declared, and the schema forbids "
                                "extra keys" % (path, name))
        for name in sorted(set(value) & set(properties)):
            problems.extend(schema_violations(value[name], properties[name],
                                              "%s.%s" % (path, name)))

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, entry in enumerate(value):
                problems.extend(schema_violations(entry, items,
                                                  "%s[%d]" % (path, index)))
    return problems


def classify(call, tools, truncated=False):
    """Classify one function call. Pure. Returns (state, detail).

    The order matters. A call whose arguments were cut off belongs to the
    truncation note, and saying so before reporting a parse error keeps the
    reader from tuning a tool schema to fix an output ceiling.
    """
    call = call or {}
    name = str(call.get("name") or "")
    tools = tools or {}
    value, error = parse_arguments(call.get("arguments"))

    if error is not None:
        if truncated:
            return ("arguments-truncated",
                    "the arguments string does not parse (%s) and the response "
                    "stopped on the output ceiling, so it was cut mid-write "
                    "rather than written wrongly" % error)
        return ("arguments-unparseable",
                "the arguments string does not parse (%s) and the response "
                "completed, so nothing was constraining the grammar" % error)

    if name not in tools:
        return ("unknown-tool",
                "the arguments parse cleanly and no tool named %r was declared "
                "on this response. A dispatcher that indexes a handler map by "
                "name raises here, not at the parse." % name)

    schema = tools[name].get("parameters")
    problems = schema_violations(value, schema)
    if problems:
        return ("arguments-violate-schema",
                "the arguments parse cleanly and break the declared schema in "
                "%d place(s): %s" % (len(problems), "; ".join(problems)))

    if not tools[name].get("strict"):
        return ("dispatchable-unconstrained",
                "this call matches the schema, but the tool was declared "
                "without strict: true, so nothing guaranteed that it would")
    return ("dispatchable", "parses and matches the declared schema")


def repair_lines(state, name=None):
    """The repair for one state. Pure."""
    if state == "arguments-violate-schema":
        return ["Validate arguments against the tool schema before dispatch, "
                "and feed the validation error back to the model as the tool "
                "result so it can correct itself. A crashed turn teaches the "
                "model nothing; a returned error usually fixes the next call.",
                "Set strict: true on tool %s, with additionalProperties: false "
                "and every parameter listed in required. Without it the schema "
                "is a suggestion." % (name or "this tool")]
    if state == "arguments-unparseable":
        return ["Wrap every argument parse in try/except and return the parse "
                "error to the model as the tool result rather than raising "
                "through the turn.",
                "Set strict: true on the tool so constrained decoding holds the "
                "grammar in the first place."]
    if state == "arguments-truncated":
        return ["Not a schema problem. The output ceiling cut the argument "
                "string mid-write, so raise it and check the response status "
                "before touching any tool call."]
    if state == "unknown-tool":
        return ["Handle an unknown tool name explicitly: return a tool result "
                "saying the tool does not exist. A KeyError out of the handler "
                "map ends the turn and loses the conversation state.",
                "Check that the tool list sent on this call matches the handler "
                "map. A tool renamed on one side only produces exactly this."]
    if state == "dispatchable-unconstrained":
        return ["This call was fine. Set strict: true on the tool anyway, "
                "because nothing about this response promised it would be."]
    return []


def read_ids(path):
    """One response id per line, blanks and # comments ignored."""
    ids = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def was_truncated(response):
    """Did this response stop on the output ceiling? Pure."""
    response = response or {}
    if str(response.get("status") or "") == "incomplete":
        reason = (response.get("incomplete_details") or {}).get("reason")
        return str(reason or "") == "max_output_tokens"
    for choice in response.get("choices") or []:
        if str(choice.get("finish_reason") or "") == "length":
            return True
    return False


def fetch_response(session, response_id):
    r = session.get(API + "/responses/" + response_id, timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: this needs a project key that can "
                         "read stored responses" % r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True,
                    help="file of stored response ids, one per line")
    ap.add_argument("--show-all", action="store_true",
                    help="also print calls that parse and validate")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY, a project key set to Read Only")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    checked = 0
    bad = 0
    for response_id in read_ids(args.ids):
        stored = fetch_response(session, response_id)
        if stored is None:
            log.warning("%-27s %s  not found. Stored responses expire, and a "
                        "response created without storage was never readable.",
                        "unreadable", response_id)
            continue
        tools = declared_tools(stored)
        truncated = was_truncated(stored)
        calls = function_calls(stored)
        if not calls:
            continue
        if len(calls) > 1:
            log.info("%-27s %s  %d call(s) in one turn", "parallel-calls",
                     response_id, len(calls))
        for call in calls:
            checked += 1
            state, detail = classify(call, tools, truncated)
            line = "%-27s %s %s/%s  %s" % (state, response_id, call["name"],
                                           call["call_id"] or "-", detail)
            if state in FINDINGS:
                bad += 1
                log.warning(line)
                for repair in repair_lines(state, call["name"]):
                    log.warning("  repair: %s", repair)
            elif state == "dispatchable":
                if args.show_all:
                    log.info(line)
            else:
                log.info(line)
                for repair in repair_lines(state, call["name"]):
                    log.info("  note: %s", repair)

    log.info("%d tool call(s) checked, %d your dispatcher cannot use",
             checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-tool-call-arguments.mjs",
"js": '''/**
 * Check every stored tool call against the tool schema declared beside it.
 *
 * Read only. GET /v1/responses/{response_id} for each id you supply, with a
 * project key set to Read Only. There is no list endpoint for /v1/responses,
 * so the ids come from your own records: one id per line in a file.
 *
 * Function arguments come back JSON encoded, as a string, and the docs are
 * explicit that the string may be malformed. Two different faults arrive
 * through that one field: a string that will not parse, which a careful
 * try/catch handles, and a string that parses perfectly and describes a call
 * your handler cannot accept, which nothing around JSON.parse will catch.
 *
 * The response carries the tool definitions it was generated with, so the
 * declared schema and the emitted call can be compared without reading a line
 * of your source. The repair is printed, never performed.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

const FINDINGS = new Set([
  'arguments-violate-schema', 'arguments-unparseable', 'unknown-tool']);

/** What a parsed JSON value actually is, in schema vocabulary. Pure. */
export function typeName(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  if (typeof value === 'number') return Number.isInteger(value) ? 'integer' : 'number';
  return typeof value;
}

const TYPE_TESTS = {
  object: (v) => v !== null && typeof v === 'object' && !Array.isArray(v),
  array: (v) => Array.isArray(v),
  string: (v) => typeof v === 'string',
  boolean: (v) => typeof v === 'boolean',
  null: (v) => v === null,
  number: (v) => typeof v === 'number' && Number.isFinite(v),
  integer: (v) => typeof v === 'number' && Number.isInteger(v),
};

/** Every function call in a stored response, in emission order. Pure. */
export function functionCalls(response) {
  const calls = [];
  for (const item of response?.output ?? []) {
    if (!item || typeof item !== 'object' || item.type !== 'function_call') continue;
    calls.push({ name: String(item.name ?? ''),
      callId: String(item.call_id ?? item.id ?? ''),
      arguments: item.arguments });
  }
  for (const choice of response?.choices ?? []) {
    for (const call of choice?.message?.tool_calls ?? []) {
      const fn = call?.function ?? {};
      calls.push({ name: String(fn.name ?? ''),
        callId: String(call?.id ?? ''),
        arguments: fn.arguments });
    }
  }
  return calls;
}

/** The tool definitions the response was generated with, keyed by name. Pure. */
export function declaredTools(response) {
  const tools = new Map();
  for (const tool of response?.tools ?? []) {
    if (!tool || typeof tool !== 'object') continue;
    if (String(tool.type ?? 'function') !== 'function') continue;
    const inner = (tool.function && typeof tool.function === 'object') ? tool.function : tool;
    const name = String(inner.name ?? '');
    if (name) tools.set(name, { parameters: inner.parameters, strict: inner.strict === true });
  }
  return tools;
}

/**
 * Parse one arguments string. Pure. Returns [value, error].
 * An empty string is a legal way to call a tool that takes nothing, so it
 * parses to an empty object rather than failing.
 */
export function parseArguments(text) {
  if (text === null || text === undefined) return [null, 'the arguments field is absent'];
  if (typeof text === 'object' && !Array.isArray(text)) return [text, null];
  const body = String(text).trim();
  if (!body) return [{}, null];
  let value;
  try {
    value = JSON.parse(body);
  } catch (err) {
    return [null, err.message];
  }
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    return [null, `arguments parsed to ${typeName(value)}, not an object`];
  }
  return [value, null];
}

/**
 * Where a parsed argument object departs from its declared schema. Pure.
 * Types, required keys, unexpected keys and enums: the four failures that
 * actually reach a dispatcher.
 */
export function schemaViolations(value, schema, path = 'arguments') {
  const problems = [];
  if (!schema || typeof schema !== 'object' || Object.keys(schema).length === 0) {
    return problems;
  }

  const raw = schema.type;
  const kinds = (Array.isArray(raw) ? raw : (raw ? [raw] : [])).map(String);
  const known = kinds.filter((k) => k in TYPE_TESTS);
  if (known.length && !known.some((k) => TYPE_TESTS[k](value))) {
    return [`${path}: expected ${known.join(' or ')}, got ${typeName(value)}`];
  }

  if (Array.isArray(schema.enum) && schema.enum.length && !schema.enum.includes(value)) {
    problems.push(`${path}: ${JSON.stringify(value)} is not one of the ` +
      `${schema.enum.length} declared value(s)`);
  }

  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    const properties = (schema.properties && typeof schema.properties === 'object')
      ? schema.properties : {};
    for (const name of Array.isArray(schema.required) ? schema.required : []) {
      if (!(name in value)) problems.push(`${path}.${name}: required and missing`);
    }
    if (schema.additionalProperties === false) {
      for (const name of Object.keys(value).filter((k) => !(k in properties)).sort()) {
        problems.push(`${path}.${name}: not declared, and the schema forbids extra keys`);
      }
    }
    for (const name of Object.keys(value).filter((k) => k in properties).sort()) {
      problems.push(...schemaViolations(value[name], properties[name], `${path}.${name}`));
    }
  }

  if (Array.isArray(value) && schema.items && typeof schema.items === 'object') {
    value.forEach((entry, index) => {
      problems.push(...schemaViolations(entry, schema.items, `${path}[${index}]`));
    });
  }
  return problems;
}

/**
 * Classify one function call. Pure. Returns [state, detail].
 * Order matters: a call whose arguments were cut off belongs to the truncation
 * note, and saying so first keeps the reader from tuning a tool schema to fix
 * an output ceiling.
 */
export function classify(call, tools, truncated = false) {
  const name = String(call?.name ?? '');
  const map = tools instanceof Map ? tools : new Map(Object.entries(tools ?? {}));
  const [value, error] = parseArguments(call?.arguments);

  if (error !== null) {
    if (truncated) {
      return ['arguments-truncated',
        `the arguments string does not parse (${error}) and the response ` +
        'stopped on the output ceiling, so it was cut mid-write rather than ' +
        'written wrongly'];
    }
    return ['arguments-unparseable',
      `the arguments string does not parse (${error}) and the response ` +
      'completed, so nothing was constraining the grammar'];
  }

  if (!map.has(name)) {
    return ['unknown-tool',
      `the arguments parse cleanly and no tool named '${name}' was declared on ` +
      'this response. A dispatcher that indexes a handler map by name raises ' +
      'here, not at the parse.'];
  }

  const tool = map.get(name);
  const problems = schemaViolations(value, tool.parameters);
  if (problems.length) {
    return ['arguments-violate-schema',
      `the arguments parse cleanly and break the declared schema in ` +
      `${problems.length} place(s): ${problems.join('; ')}`];
  }

  if (!tool.strict) {
    return ['dispatchable-unconstrained',
      'this call matches the schema, but the tool was declared without ' +
      'strict: true, so nothing guaranteed that it would'];
  }
  return ['dispatchable', 'parses and matches the declared schema'];
}

/** The repair for one state. Pure. */
export function repairLines(state, name) {
  if (state === 'arguments-violate-schema') {
    return ['Validate arguments against the tool schema before dispatch, and feed ' +
      'the validation error back to the model as the tool result so it can correct ' +
      'itself. A crashed turn teaches the model nothing; a returned error usually ' +
      'fixes the next call.',
    `Set strict: true on tool ${name ?? 'this tool'}, with additionalProperties: ` +
      'false and every parameter listed in required. Without it the schema is a ' +
      'suggestion.'];
  }
  if (state === 'arguments-unparseable') {
    return ['Wrap every argument parse in try/catch and return the parse error to ' +
      'the model as the tool result rather than raising through the turn.',
    'Set strict: true on the tool so constrained decoding holds the grammar in ' +
      'the first place.'];
  }
  if (state === 'arguments-truncated') {
    return ['Not a schema problem. The output ceiling cut the argument string ' +
      'mid-write, so raise it and check the response status before touching any ' +
      'tool call.'];
  }
  if (state === 'unknown-tool') {
    return ['Handle an unknown tool name explicitly: return a tool result saying ' +
      'the tool does not exist. A thrown lookup error out of the handler map ends ' +
      'the turn and loses the conversation state.',
    'Check that the tool list sent on this call matches the handler map. A tool ' +
      'renamed on one side only produces exactly this.'];
  }
  if (state === 'dispatchable-unconstrained') {
    return ['This call was fine. Set strict: true on the tool anyway, because ' +
      'nothing about this response promised it would be.'];
  }
  return [];
}

/** Did this response stop on the output ceiling? Pure. */
export function wasTruncated(response) {
  if (String(response?.status ?? '') === 'incomplete') {
    return String(response?.incomplete_details?.reason ?? '') === 'max_output_tokens';
  }
  for (const choice of response?.choices ?? []) {
    if (String(choice?.finish_reason ?? '') === 'length') return true;
  }
  return false;
}

async function fetchResponse(key, responseId) {
  const res = await fetch(`${API}/responses/${responseId}`,
    { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: this needs a project key that ` +
                    'can read stored responses');
  }
  if (!res.ok) throw new Error(`${res.status} from /responses/${responseId}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  const idsFile = process.env.RESPONSE_IDS;
  if (!key || !idsFile) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only) and ' +
                  'RESPONSE_IDS (a file of stored response ids, one per line)');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';

  const ids = (await readFile(idsFile, 'utf8')).split('\\n')
    .map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));

  let checked = 0;
  let bad = 0;
  for (const responseId of ids) {
    const stored = await fetchResponse(key, responseId);
    if (stored === null) {
      console.warn(`${'unreadable'.padEnd(27)} ${responseId}  not found. Stored ` +
        'responses expire, and a response created without storage was never readable.');
      continue;
    }
    const tools = declaredTools(stored);
    const truncated = wasTruncated(stored);
    const calls = functionCalls(stored);
    if (!calls.length) continue;
    if (calls.length > 1) {
      console.log(`${'parallel-calls'.padEnd(27)} ${responseId}  ${calls.length} ` +
        'call(s) in one turn');
    }
    for (const call of calls) {
      checked += 1;
      const [state, detail] = classify(call, tools, truncated);
      const line = `${state.padEnd(27)} ${responseId} ${call.name}/` +
        `${call.callId || '-'}  ${detail}`;
      if (FINDINGS.has(state)) {
        bad += 1;
        console.warn(line);
        for (const repair of repairLines(state, call.name)) console.warn(`  repair: ${repair}`);
      } else if (state === 'dispatchable') {
        if (showAll) console.log(line);
      } else {
        console.log(line);
        for (const repair of repairLines(state, call.name)) console.log(`  note: ${repair}`);
      }
    }
  }

  console.log(`${checked} tool call(s) checked, ${bad} your dispatcher cannot use`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one that justifies the note: a call whose arguments parse without complaint and break the schema in three separate ways at once, each reported with its path. Nothing built around a try/except sees any of it. Then a missing required parameter, then the two attributions that keep this note honest &mdash; a truncated argument string handed to the ceiling note, and an unknown tool name named as a lookup failure rather than a parse failure. The last three cover a valid call, a valid call on a tool that never asked for strict, and the empty argument string that a bare parse raises on.",
"test_py_file": "test_openai_tool_call_arguments.py",
"test_py": '''from openai_tool_call_arguments import (classify, declared_tools,
                                        function_calls, parse_arguments,
                                        repair_lines, schema_violations,
                                        was_truncated)

CHARGE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["account_id", "amount_cents", "currency"],
    "properties": {
        "account_id": {"type": "string"},
        "amount_cents": {"type": "integer"},
        "currency": {"type": "string", "enum": ["usd", "eur"]},
    },
}


def response(arguments, *, name="charge", strict=True, status="completed"):
    return {"id": "resp_t", "status": status,
            "tools": [{"type": "function", "name": "charge",
                       "parameters": CHARGE, "strict": strict}],
            "output": [{"type": "function_call", "name": name,
                        "call_id": "call_1", "arguments": arguments}]}


def test_arguments_that_parse_and_still_break_the_contract():
    # The centre of the note. json.loads is perfectly happy; the handler is
    # not, and no amount of care around the parse would have caught it.
    stored = response('{"account_id": "acct_9", "amount_cents": "1200", '
                      '"currency": "gbp", "idempotency_key": "k1"}')
    call = function_calls(stored)[0]
    value, error = parse_arguments(call["arguments"])
    assert error is None and isinstance(value, dict)

    state, detail = classify(call, declared_tools(stored))
    assert state == "arguments-violate-schema"
    assert "amount_cents: expected integer, got str" in detail
    assert "currency: 'gbp' is not one of the 2 declared value(s)" in detail
    assert "idempotency_key: not declared" in detail
    assert "feed the validation error back to the model" in repair_lines(state)[0]


def test_a_missing_required_argument_is_found_before_the_handler_is_called():
    stored = response('{"account_id": "acct_9", "currency": "usd"}')
    state, detail = classify(function_calls(stored)[0], declared_tools(stored))
    assert state == "arguments-violate-schema"
    assert "arguments.amount_cents: required and missing" in detail


def test_a_cut_argument_string_belongs_to_the_truncation_note():
    stored = response('{"account_id": "acct_9", "amount_cent',
                      status="incomplete")
    stored["incomplete_details"] = {"reason": "max_output_tokens"}
    assert was_truncated(stored) is True
    state, detail = classify(function_calls(stored)[0], declared_tools(stored),
                             was_truncated(stored))
    assert state == "arguments-truncated"
    assert "cut mid-write rather than written wrongly" in detail
    assert "Not a schema problem" in repair_lines(state)[0]


def test_a_broken_string_on_a_completed_response_is_the_models_own_work():
    stored = response('{{"account_id": "acct_9"}}')
    assert was_truncated(stored) is False
    state, detail = classify(function_calls(stored)[0], declared_tools(stored))
    assert state == "arguments-unparseable"
    assert "nothing was constraining the grammar" in detail


def test_an_unknown_tool_name_is_a_lookup_error_not_a_parse_error():
    stored = response('{"account_id": "acct_9"}', name="charge_v2")
    state, detail = classify(function_calls(stored)[0], declared_tools(stored))
    assert state == "unknown-tool"
    assert "indexes a handler map by name raises here" in detail
    assert "renamed on one side only" in repair_lines(state)[1]


def test_a_valid_call_is_dispatchable_and_an_unstrict_one_is_flagged_anyway():
    good = '{"account_id": "acct_9", "amount_cents": 1200, "currency": "usd"}'
    stored = response(good)
    assert classify(function_calls(stored)[0], declared_tools(stored))[0] == "dispatchable"

    loose = response(good, strict=False)
    state, detail = classify(function_calls(loose)[0], declared_tools(loose))
    assert state == "dispatchable-unconstrained"
    assert "nothing guaranteed that it would" in detail


def test_the_chat_completions_shape_and_the_empty_argument_string():
    legacy = {"choices": [{"finish_reason": "tool_calls", "message": {
        "tool_calls": [{"id": "call_9", "type": "function",
                        "function": {"name": "ping", "arguments": ""}}]}}],
        "tools": [{"type": "function",
                   "function": {"name": "ping", "strict": True,
                                "parameters": {"type": "object",
                                               "additionalProperties": False,
                                               "properties": {},
                                               "required": []}}}]}
    call = function_calls(legacy)[0]
    assert call["name"] == "ping" and call["call_id"] == "call_9"
    # A tool that takes nothing is legally called with an empty string, and a
    # bare json.loads raises on it.
    assert parse_arguments("") == ({}, None)
    assert classify(call, declared_tools(legacy))[0] == "dispatchable"


def test_the_walker_and_the_readers_survive_junk():
    assert parse_arguments(None)[1] == "the arguments field is absent"
    assert parse_arguments("[1, 2]")[1] == "arguments parsed to list, not an object"
    assert schema_violations({"a": 1}, None) == []
    assert schema_violations({"a": 1}, {}) == []
    assert schema_violations(True, {"type": "integer"}) == [
        "arguments: expected integer, got bool"]
    assert schema_violations({"rows": [{"sku": 1}]}, {
        "type": "object", "properties": {"rows": {
            "type": "array", "items": {"type": "object",
                                       "properties": {"sku": {"type": "string"}}}}}}) == [
        "arguments.rows[0].sku: expected string, got int"]
    assert function_calls(None) == []
    assert declared_tools(None) == {}
    assert was_truncated(None) is False
''',
"test_js_file": "openai-tool-call-arguments.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, declaredTools, functionCalls, parseArguments, repairLines,
  schemaViolations, wasTruncated,
} from './openai-tool-call-arguments.mjs';

const CHARGE = {
  type: 'object',
  additionalProperties: false,
  required: ['account_id', 'amount_cents', 'currency'],
  properties: {
    account_id: { type: 'string' },
    amount_cents: { type: 'integer' },
    currency: { type: 'string', enum: ['usd', 'eur'] },
  },
};

const response = (args, { name = 'charge', strict = true,
  status = 'completed' } = {}) => ({
  id: 'resp_t', status,
  tools: [{ type: 'function', name: 'charge', parameters: CHARGE, strict }],
  output: [{ type: 'function_call', name, call_id: 'call_1', arguments: args }],
});

test('arguments that parse and still break the contract', () => {
  const stored = response('{"account_id": "acct_9", "amount_cents": "1200", ' +
    '"currency": "gbp", "idempotency_key": "k1"}');
  const call = functionCalls(stored)[0];
  const [value, error] = parseArguments(call.arguments);
  assert.equal(error, null);
  assert.equal(typeof value, 'object');

  const [state, detail] = classify(call, declaredTools(stored));
  assert.equal(state, 'arguments-violate-schema');
  assert.match(detail, /amount_cents: expected integer, got string/);
  assert.match(detail, /currency: "gbp" is not one of the 2 declared value\\(s\\)/);
  assert.match(detail, /idempotency_key: not declared/);
  assert.match(repairLines(state)[0], /feed the validation error back to the model/);
});

test('a missing required argument is found before the handler is called', () => {
  const stored = response('{"account_id": "acct_9", "currency": "usd"}');
  const [state, detail] = classify(functionCalls(stored)[0], declaredTools(stored));
  assert.equal(state, 'arguments-violate-schema');
  assert.match(detail, /arguments\\.amount_cents: required and missing/);
});

test('a cut argument string belongs to the truncation note', () => {
  const stored = response('{"account_id": "acct_9", "amount_cent',
    { status: 'incomplete' });
  stored.incomplete_details = { reason: 'max_output_tokens' };
  assert.equal(wasTruncated(stored), true);
  const [state, detail] = classify(functionCalls(stored)[0],
    declaredTools(stored), wasTruncated(stored));
  assert.equal(state, 'arguments-truncated');
  assert.match(detail, /cut mid-write rather than written wrongly/);
  assert.match(repairLines(state)[0], /Not a schema problem/);
});

test('a broken string on a completed response is the model own work', () => {
  const stored = response('{{"account_id": "acct_9"}}');
  assert.equal(wasTruncated(stored), false);
  const [state, detail] = classify(functionCalls(stored)[0], declaredTools(stored));
  assert.equal(state, 'arguments-unparseable');
  assert.match(detail, /nothing was constraining the grammar/);
});

test('an unknown tool name is a lookup error not a parse error', () => {
  const stored = response('{"account_id": "acct_9"}', { name: 'charge_v2' });
  const [state, detail] = classify(functionCalls(stored)[0], declaredTools(stored));
  assert.equal(state, 'unknown-tool');
  assert.match(detail, /indexes a handler map by name raises here/);
  assert.match(repairLines(state)[1], /renamed on one side only/);
});

test('a valid call is dispatchable and an unstrict one is flagged anyway', () => {
  const good = '{"account_id": "acct_9", "amount_cents": 1200, "currency": "usd"}';
  const stored = response(good);
  assert.equal(classify(functionCalls(stored)[0], declaredTools(stored))[0],
    'dispatchable');

  const loose = response(good, { strict: false });
  const [state, detail] = classify(functionCalls(loose)[0], declaredTools(loose));
  assert.equal(state, 'dispatchable-unconstrained');
  assert.match(detail, /nothing guaranteed that it would/);
});

test('the chat completions shape and the empty argument string', () => {
  const legacy = {
    choices: [{ finish_reason: 'tool_calls', message: { tool_calls: [
      { id: 'call_9', type: 'function',
        function: { name: 'ping', arguments: '' } }] } }],
    tools: [{ type: 'function', function: { name: 'ping', strict: true,
      parameters: { type: 'object', additionalProperties: false,
        properties: {}, required: [] } } }],
  };
  const call = functionCalls(legacy)[0];
  assert.equal(call.name, 'ping');
  assert.equal(call.callId, 'call_9');
  assert.deepEqual(parseArguments(''), [{}, null]);
  assert.equal(classify(call, declaredTools(legacy))[0], 'dispatchable');
});

test('the walker and the readers survive junk', () => {
  assert.equal(parseArguments(null)[1], 'the arguments field is absent');
  assert.equal(parseArguments('[1, 2]')[1], 'arguments parsed to array, not an object');
  assert.deepEqual(schemaViolations({ a: 1 }, null), []);
  assert.deepEqual(schemaViolations({ a: 1 }, {}), []);
  assert.deepEqual(schemaViolations(true, { type: 'integer' }),
    ['arguments: expected integer, got boolean']);
  assert.deepEqual(schemaViolations({ rows: [{ sku: 1 }] }, {
    type: 'object',
    properties: { rows: { type: 'array', items: { type: 'object',
      properties: { sku: { type: 'string' } } } } },
  }), ['arguments.rows[0].sku: expected string, got integer']);
  assert.deepEqual(functionCalls(null), []);
  assert.equal(declaredTools(null).size, 0);
  assert.equal(wasTruncated(null), false);
});
''',
"faq": [
 ("I already wrap the parse in try/except. Is that not enough?",
  "It covers the half where the string is broken and misses the half where it is not. A missing required parameter, a wrong type, an undeclared key and an out-of-range enum value are all valid JSON, so the parse succeeds and the failure moves into your handler. That is where the KeyErrors and TypeErrors in agent loops come from, and no amount of care around json.loads reaches them."),
 ("Does strict: true make this go away?",
  "It removes most of it and not all of it. Constrained decoding holds the grammar and the declared shape, which kills the unparseable strings and the wrong types. It does not help when the response is truncated mid-argument, and it does not help when the tool list and the handler map have drifted apart. Set it anyway; keep the validation step."),
 ("Why validate against the schema on the response instead of my own copy?",
  "Because the schema on the response is the one that was actually sent. A wrapper library, a feature flag, or an older service can send a definition that differs from the constant you are reading in the repository. Checking the emitted call against the definition it was generated under is the only comparison that cannot be wrong about which version ran."),
 ("What should the handler do when validation fails?",
  "Return the validation error to the model as the tool result. Models correct themselves well when told what was wrong with a call, and the turn survives. Raising through the turn loses the conversation state, and retrying the turn replays the same broken call, so the expensive failure mode is the one that looks like the careful one."),
 ("The arguments were cut off halfway. Is that this note?",
  "Only as an attribution. When the response also reports stopping on the output ceiling, the argument string was truncated mid-write and the repair is a bigger ceiling, not a tighter schema. The script checks that before it reports a parse error, because a report that blames the schema for a token budget sends people to change the wrong file."),
],
"related": [REL_TRUNC, REL_ADVISORY, REL_MAXCAP],
"citations": [CITE_OAI_FUNCTION, CITE_OAI_RESPONSES, CITE_OAI_STRUCTURED, CITE_CL_STOP],
},
]
