#!/usr/bin/env python3
"""/llm/ field notes, batch L — the writing.

Four notes about what you attach to every request. A tool definition is not
uploaded once and remembered; it is part of the prompt, re-sent and re-billed
on every call. A cached prefix is not a stored object; it is a byte-for-byte
match that either lands or does not. Both are paid for continuously and neither
raises anything when it stops earning its keep.

`tool-defined-but-never-called` is a set difference across a corpus. Every tool
name the requests declared, minus every tool name that ever came back as a
`function_call`. What is left is dead weight: billed on every turn, delivering
nothing. The care in it is the distinction between never called and never
offered, because a tool that `tool_choice` never let the model near has not
been ignored and does not need rewriting.

`tool-schemas-dominate-input-tokens` measures the same block in tokens rather
than in names. `POST /v1/messages/count_tokens` is free, generates nothing and
bills nothing, so the same body can be counted with `tools` and then without,
and the difference is the per-call overhead exactly. Ablating one tool at a
time gives a per-tool price, and the deltas deliberately do not sum to the
whole: a fixed charge arrives with any tools at all and no single ablation
removes it.

`parallel-tool-calls-with-strict-schema` is the only one whose unit is a single
turn. Structured Outputs is not supported alongside parallel function calls,
and `parallel_tool_calls` defaults to true, so a guarantee that holds for one
call silently stops holding for two. Tests send one call. Production sends
whatever the model decided.

`cache-invalidated-by-changing-prefix` had the hardest job in the batch,
because two published notes already read the same two numbers. It does not
own "caching is off" and it does not own "the writes outnumber the reads". It
owns the cause: a prefix that differs on every call. The evidence is adjacency
at one-minute resolution. A run of minutes that each write and never read is
longer than the entry's own TTL, which means the entry was alive and unmatched
the whole time, which no gap or warm-up story explains. Both of the other two
notes are named in the output when the shape says the finding is theirs.

Read only throughout. Two want an OpenAI project key and a file of stored
response ids, because `/v1/responses` cannot be enumerated; one wants an
Anthropic workspace key and uses the free token counter; one wants an Anthropic
Admin key. Nothing here calls `/v1/messages` or `/v1/responses` to make a
completion. Every repair — a pruned tool, a cache breakpoint, one boolean, a
timestamp moved after the breakpoint — is a deploy with an owner, so it is
printed rather than performed.
"""

CITE_OAI_FUNCTION_CALLING = ("Function calling — OpenAI developer docs",
                             "https://developers.openai.com/api/docs/guides/function-calling")
CITE_OAI_STRUCTURED = ("Structured outputs — OpenAI developer docs",
                       "https://developers.openai.com/api/docs/guides/structured-outputs")
CITE_OAI_RESPONSES = ("Responses — OpenAI API reference",
                      "https://platform.openai.com/docs/api-reference/responses")
CITE_OAI_CONVERSATION_STATE = ("Conversation state — OpenAI developer docs",
                               "https://developers.openai.com/api/docs/guides/conversation-state")
CITE_OAI_USAGE_COMPLETIONS = ("Completions usage — OpenAI API reference",
                              "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_MS_STRUCTURED = ("Structured outputs — Microsoft Learn, Azure AI Foundry",
                      "https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs")

CITE_CL_TOOL_USE = ("Tool use overview — Claude Docs",
                    "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview")
CITE_CL_TOKEN_COUNTING = ("Token counting — Claude Docs",
                          "https://platform.claude.com/docs/en/build-with-claude/token-counting")
CITE_CL_PRICING = ("Pricing — Claude Docs",
                   "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_CL_CACHING = ("Prompt caching — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
CITE_CL_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")

REL_DEAD_TOOL = ("/llm/tool-defined-but-never-called/",
                 "Which declared tools the model has never once chosen")
REL_TOOL_TOKENS = ("/llm/tool-schemas-dominate-input-tokens/",
                   "What the tools block actually weighs on every call")
REL_PARALLEL = ("/llm/parallel-tool-calls-with-strict-schema/",
                "The fan-out that voids a strict schema guarantee")
REL_CHURN = ("/llm/cache-invalidated-by-changing-prefix/",
             "A prefix that changes every call, so nothing is ever read back")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "Prompt caching that was never switched on at all")
REL_CACHE_WRITES = ("/llm/cache-writes-with-no-reads/",
                    "Cache writes paid for at a premium and never read back")
REL_FINE_TUNED = ("/llm/fine-tuned-model-never-used/",
                  "A capability that was provisioned and then never called")
REL_CONTEXT = ("/llm/prompt-too-long-context-overflow/",
               "The same payload measured against the model context window")
REL_ZERO_OUTPUT = ("/llm/reasoning-model-rejects-max-tokens/",
                   "A request-body field whose meaning is not what the code assumes")

GUIDES = [
{
"slug": "tool-defined-but-never-called",
"title": "Tool shipped on every request and never once called",
"description": "The declared tool names minus the names that ever come back as a function_call. A tool the model never picks is billed every turn and delivers nothing.",
"h1": "Tool shipped on every request and never once called",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai tool never called", "function_call missing from output",
             "tool_choice auto ignores tool", "too many tools in one turn",
             "unused tool definition cost"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key that can read stored responses, and a file of response ids: /v1/responses cannot be listed, so the sample has to come from your own logs.",
"lead": "The tool registry has twenty-six entries. Nineteen of them were written in the same fortnight by four people, and the descriptions read like function signatures because that is what they were copied from. Every one of them goes out on every request, because the registry is built once at start-up and handed to the client whole. Nothing is broken. The handlers for six of those tools have not been entered in production since the day they were merged, and the tools are still being paid for on every turn.",
"short_answer": """<p>Build two sets from a sample of stored responses and subtract. With a <strong>project key</strong> that can read them: <code>GET /v1/responses/{response_id}</code>. The response object echoes the <code>tools</code> the request declared, and its <code>output[]</code> array carries the items of <code>type: "function_call"</code> the model produced. Every name in the first that never appears in the second, across a large enough sample, is a definition you pay for and never use.</p>
<p>There is no list endpoint. <code>/v1/responses</code> cannot be enumerated, so the ids have to come from your own request log, and the sample has to be big enough that "never" means something. A few hundred turns is a finding; nine is a coincidence.</p>
<p>Split never called from <em>never offered</em> before you conclude anything. A response sent with <code>tool_choice: "none"</code>, or with a named tool, never gave the model the chance, and counting those turns as evidence condemns tools that were simply not on the table. This script counts a tool as offered only in the turns where the model was free to pick it.</p>
<p>The repair is a rewrite before it is a deletion. A tool that is never selected usually has a description that says what it is rather than when to call it. If a call is mandatory, say so with <code>tool_choice: "required"</code> or a named tool rather than hoping.</p>""",
"problem": """<p>Tool definitions are prompt. Names, descriptions and the whole JSON schema are serialised into the request and billed as input tokens on every single call, and unlike a system prompt nobody thinks of them as text at all &mdash; they are code, they live in a registry module, and they get added the way a route gets added. Nothing in the API charges you differently for a tool that is used and one that is not.</p>
<p>What makes it invisible is that the failure mode is an absence on both sides. The tool never fires, so its handler emits no logs, no metrics and no errors; a dashboard built on the handler shows a flat zero that looks exactly like a quiet week. And the cost never spikes, because it was there from the first deploy: a fixed addition to every request is a baseline, and baselines do not alert. The capability you thought you shipped is missing, and the only trace is a name in a request payload that no one reads.</p>""",
"why": """<p><strong>Never called and never offered are different findings with different repairs.</strong> A tool that appears in <code>tools</code> on two hundred turns and was free to be chosen on none of them &mdash; because <code>tool_choice</code> was <code>"none"</code>, or named another tool every time &mdash; has not been ignored by the model. It has been ruled out by your own request. Rewriting its description will change nothing. The script tracks a separate offered count per tool for exactly this, and refuses to call a tool dead on turns where it was never in the running.</p>
<p><strong>Crowding is a real cause and it is the one nobody suspects.</strong> The guidance is to keep fewer than twenty tools available at the start of a turn. Past that, selection quality falls, and it falls unevenly: the tools with the vaguest descriptions lose first. A registry that grew to forty is not a configuration problem, it is a prompt problem, and the fix is <code>allowed_tools</code> or a per-turn subset rather than a better description on any one entry.</p>
<p><strong>A description that says what a tool <em>is</em> reads as documentation and selects badly.</strong> "Looks up an order" is a signature. "Call this when the user asks about the status, contents or delivery date of an order they have already placed; do not call it for refunds" is a selection rule. The model is choosing between twenty-six of these under a token budget, and the ones that read like a rule win.</p>
<p><strong>This note counts names; the cost of those names is a separate measurement.</strong> A character count of a JSON schema is not a token count, and printing one as if it were the other is worse than printing nothing. The script reports the share of the declared schema, <em>in characters</em>, that belongs to tools nobody calls, and says plainly that the token price belongs to <a href="/llm/tool-schemas-dominate-input-tokens/">the token-overhead note</a>, which measures it exactly and for free.</p>
<p><strong>"Never in this sample" is the only claim available, and the script says so.</strong> There is no list endpoint for stored responses and no aggregate that counts tool selections, so every statement here is bounded by the ids you supplied. A tool called once a month by one support workflow will look dead in a day of traffic. The output always carries the sample size beside the verdict, and a tool that was offered fewer than fifty times comes back as insufficient evidence rather than as a finding.</p>""",
"steps": [
 {"h": "Collect a sample of stored response ids",
  "body": """<p><code>/v1/responses</code> has no list endpoint, so the ids come from your own request log. Sample across a full week rather than an afternoon: a tool used by one weekly workflow is dead on Tuesday and alive on Sunday. Responses have to have been stored in the first place &mdash; <code>store</code> defaults to true on the Responses API, but a client that turned it off leaves nothing to read.</p>"""},
 {"h": "Read each response and take the two sets",
  "body": """<p><code>GET /v1/responses/{response_id}</code>. The declared names come from <code>tools[]</code>, handling both shapes: the Responses API puts <code>name</code> at the top level of the tool object, Chat Completions nests it under <code>function</code>. The called names come from <code>output[]</code> items whose <code>type</code> is <code>function_call</code>.</p>"""},
 {"h": "Count offers separately from declarations",
  "body": """<p>Read <code>tool_choice</code> on each response. <code>"none"</code> means no tool was on the table in that turn and it counts for nothing. A named tool means only that one was on the table. <code>"auto"</code>, <code>"required"</code> and an absent field mean every declared tool was in the running. Only the last group is evidence.</p>"""},
 {"h": "Sort by call count and read the zeros against the sample size",
  "body": """<p>A tool offered four hundred times and never chosen is a finding. A tool offered eleven times and never chosen is nothing at all, and the script says so rather than padding the list. The rare bucket matters too: one call in five hundred turns is a tool to keep and to stop sending on every turn.</p>"""},
 {"h": "Print the repair per tool, not per registry",
  "body": """<p>Rewrite the description as a selection rule; narrow the turn with <code>allowed_tools</code> so the model chooses among five rather than forty; force the call with <code>tool_choice: "required"</code> or a named tool where a call is mandatory; delete what nothing needs. Then measure what the surviving block weighs, because pruning six of twenty-six tools is a smaller saving than it feels like.</p>"""},
],
"verify": """<p>Re-run on a fresh week of ids after the descriptions change. A tool that moves from zero to a handful of calls was a description problem; one that stays at zero after being offered freely a thousand times is a deletion.</p>
<pre><code class="language-bash">python3 openai_dead_tool_definitions.py --responses ids.txt
# never-called       escalate_to_human      offered in 412 of 412 turn(s), called 0 time(s), 1180 schema char(s)
#   repair: the description reads like a signature. Say when to call it, not what it is.
# never-offered      run_refund             declared in 412 turn(s), free to be chosen in 0 of them
#   repair: tool_choice never let the model near this one. Fix the request before the description.
# rarely-called      lookup_invoice         offered in 412 turn(s), called 2 time(s) (0.5%)
# 26 declared tool(s) over 412 response(s), 6 finding(s)
# 31% of the declared schema, in characters, belongs to tools nothing ever called</code></pre>""",
"code_intro": "One GET per response id and no aggregate anywhere, because there is no aggregate that counts tool selections. Nine pure functions: the id parser, which is also the guard that stops an arbitrary string being pasted into a URL path; the name reader, which has to cope with both tool shapes; the declared and called readers; the <code>tool_choice</code> reader, which decides whether a turn is evidence at all; the fold; the coverage table; the classifier; the dead-weight share, which is measured in characters and says so; and the crowding check against the twenty-tool guidance.",
"py_file": "openai_dead_tool_definitions.py",
"py": '''"""Find OpenAI tool definitions that are sent on every call and never chosen.

Read only. One GET per stored response id, using a project key. No completion
is created and nothing is written; /v1/responses is read, never posted to.

There is no list endpoint for stored responses, so the sample comes from a file
of ids you supply. Every claim this script makes is bounded by that sample and
the output says so: "never called in 412 turns" is the finding, not "never
called".

The repair is printed, never performed. Pruning a tool registry is a deploy.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_dead_tool_definitions")

API = "https://api.openai.com/v1"

# Output item types that represent the model choosing a tool. Anything else in
# output[] is a message, a reasoning item or a hosted tool call, and none of
# those is evidence that one of your function definitions was selected.
CALL_TYPES = ("function_call", "custom_tool_call")

# The documented guidance is fewer than twenty tools available at the start of
# a turn. Past that, selection quality falls and it falls on the vaguest
# descriptions first.
CROWD_CEILING = 20

FINDINGS = ("never-called", "never-offered")


def _int(value):
    """Read a count as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_ids(text):
    """Response ids out of a plain text file. Pure. Order kept, duplicates dropped.

    Also the guard that stops an arbitrary line of a file becoming a URL path
    segment. Anything that is not a plausible response id is discarded rather
    than sent, because a script that interpolates unvalidated text into a
    provider URL is one typo away from requesting something else entirely.
    """
    out = []
    seen = set()
    for line in str(text or "").splitlines():
        candidate = line.split("#", 1)[0].strip()
        if not candidate or not candidate.startswith("resp_"):
            continue
        if not all(ch.isalnum() or ch in "_-" for ch in candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append(candidate)
    return out


def tool_name(tool):
    """The function name out of either tool shape. Pure. None when absent.

    The Responses API puts name at the top level of the tool object; Chat
    Completions nests it under function. A reader that knows only one shape
    reports every tool as undeclared on half the corpus.
    """
    if not isinstance(tool, dict):
        return None
    name = tool.get("name")
    if not name and isinstance(tool.get("function"), dict):
        name = tool["function"].get("name")
    name = str(name or "").strip()
    return name or None


def declared_tools(response):
    """Every named tool the request declared, with its serialized size. Pure.

    Size in characters, never tokens. Hosted tools carry no name and are
    skipped: web search is not a definition you wrote and not one you can prune.
    """
    out = {}
    for tool in (response or {}).get("tools") or []:
        name = tool_name(tool)
        if name is None:
            continue
        try:
            size = len(json.dumps(tool, separators=(",", ":"), sort_keys=True))
        except (TypeError, ValueError):
            size = 0
        out[name] = max(out.get(name, 0), size)
    return out


def called_tools(response):
    """Tool names the model actually chose in one response, counted. Pure."""
    counts = {}
    for item in (response or {}).get("output") or []:
        if not isinstance(item, dict) or item.get("type") not in CALL_TYPES:
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    return counts


def choice_mode(response):
    """How free the model was to pick a tool in this turn. Pure.

    Returns "free", "blocked", or "named:<tool>". An absent tool_choice is
    auto, which is free. This is the difference between a tool the model
    ignored and a tool your own request never put on the table.
    """
    choice = (response or {}).get("tool_choice")
    if choice is None:
        return "free"
    if isinstance(choice, str):
        lowered = choice.strip().lower()
        if lowered == "none":
            return "blocked"
        return "free"
    if isinstance(choice, dict):
        name = tool_name(choice)
        if name:
            return "named:" + name
        return "free"
    return "free"


def fold(responses):
    """Fold a sample of stored responses into one corpus. Pure.

    Declarations and offers are counted separately on purpose. A tool declared
    on four hundred turns and offered on none of them is not dead weight, it is
    a tool_choice that never let the model near it, and the two have nothing in
    common as repairs.
    """
    corpus = {"sampled": 0, "with_tools": 0, "widest_turn": 0, "calls": 0,
              "declared": {}, "offered": {}, "called": {}}
    for response in responses or []:
        if not isinstance(response, dict):
            continue
        corpus["sampled"] += 1
        declared = declared_tools(response)
        calls = called_tools(response)
        for name, count in calls.items():
            corpus["called"][name] = corpus["called"].get(name, 0) + count
            corpus["calls"] += count
        if not declared:
            continue
        corpus["with_tools"] += 1
        corpus["widest_turn"] = max(corpus["widest_turn"], len(declared))
        mode = choice_mode(response)
        for name, size in declared.items():
            row = corpus["declared"].setdefault(name, {"turns": 0, "chars": 0})
            row["turns"] += 1
            row["chars"] = max(row["chars"], size)
            if mode == "blocked":
                continue
            if mode.startswith("named:") and mode[len("named:"):] != name:
                continue
            corpus["offered"][name] = corpus["offered"].get(name, 0) + 1
    return corpus


def coverage(corpus):
    """One row per declared tool. Pure. Least used and most expensive first."""
    rows = []
    for name, row in ((corpus or {}).get("declared") or {}).items():
        rows.append({
            "name": name,
            "turns": _int(row.get("turns")),
            "chars": _int(row.get("chars")),
            "offered": _int(((corpus or {}).get("offered") or {}).get(name)),
            "calls": _int(((corpus or {}).get("called") or {}).get(name)),
        })
    rows.sort(key=lambda r: (r["calls"], -r["chars"], r["name"]))
    return rows


def orphan_calls(corpus):
    """Names the model called that no sampled request declared. Pure.

    Not a fault in the registry: it means the sample mixes two configurations,
    and a set difference computed across two configurations is meaningless.
    """
    declared = set(((corpus or {}).get("declared") or {}))
    return sorted(n for n in ((corpus or {}).get("called") or {}) if n not in declared)


def classify(row, min_offered=50, rare=0.01):
    """Classify one tool's coverage across the sample. Pure. Returns (state, detail)."""
    row = row or {}
    name = str(row.get("name") or "unknown")
    turns = _int(row.get("turns"))
    offered = _int(row.get("offered"))
    calls = _int(row.get("calls"))

    if turns and offered == 0:
        return ("never-offered",
                "declared in %d turn(s), free to be chosen in 0 of them. "
                "tool_choice ruled it out every time, so the model never "
                "declined it and rewriting the description changes nothing."
                % turns)
    if offered < min_offered:
        return ("too-small-a-sample",
                "offered in %d turn(s), under the floor of %d. Not enough to "
                "call anything dead." % (offered, min_offered))
    if calls == 0:
        return ("never-called",
                "offered in %d of %d turn(s), called 0 time(s), %d schema "
                "char(s). Sent and billed on every one of those turns."
                % (offered, turns, _int(row.get("chars"))))
    share = calls / float(offered)
    if share < rare:
        return ("rarely-called",
                "offered in %d turn(s), called %d time(s) (%.1f%%). Worth "
                "keeping and worth not sending on every turn."
                % (offered, calls, share * 100))
    return ("called",
            "offered in %d turn(s), called %d time(s) (%.1f%%)."
            % (offered, calls, share * 100))


def dead_weight(rows, min_offered=50, rare=0.01):
    """Share of the declared schema, in characters, that nothing ever calls. Pure.

    Characters, and the docstring is the place to be blunt about it: this is
    not a token count and must never be read as one. Tokens are measured
    exactly and for free by the token-overhead note, and a character count
    dressed up as a token count is worse than no number at all.
    """
    total = 0
    dead = 0
    for row in rows or []:
        chars = _int(row.get("chars"))
        total += chars
        if classify(row, min_offered, rare)[0] == "never-called":
            dead += chars
    if total <= 0:
        return None
    return dead / float(total)


def crowding(widest_turn, ceiling=CROWD_CEILING):
    """What the widest turn in the sample looked like. Pure.

    Above the guidance the finding changes shape: the problem is no longer any
    one description, it is that the model is choosing among too many at once,
    and the repair is a narrower turn rather than better prose.
    """
    widest = _int(widest_turn)
    if widest <= 0:
        return ("no-tools", "no sampled response declared any named tool")
    if widest > ceiling:
        return ("crowded",
                "the widest turn offered %d tools, above the guidance of fewer "
                "than %d. Selection quality falls with crowding and it falls on "
                "the vaguest descriptions first." % (widest, ceiling))
    return ("within-guidance",
            "the widest turn offered %d tool(s), inside the guidance of fewer "
            "than %d" % (widest, ceiling))


def repair_lines(state, name):
    """The repair for one classified tool. Pure."""
    if state == "never-called":
        return [
            "the description probably reads like a signature. Rewrite it as a "
            "selection rule: when to call %s, and when not to." % name,
            "if a call is mandatory, say so with tool_choice required or a "
            "named tool rather than hoping the model picks it up.",
            "if nothing needs it, delete it. It is billed on every turn.",
        ]
    if state == "never-offered":
        return [
            "tool_choice never let the model near %s. Fix the request before "
            "you touch the description." % name,
        ]
    if state == "rarely-called":
        return [
            "keep %s, but stop sending it on every turn. allowed_tools narrows "
            "the set for the turns where it is plausible." % name,
        ]
    return []


def get(session, path):
    r = session.get(API + path, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: OPENAI_API_KEY needs read access to "
                         "stored responses in this project" % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--responses", metavar="FILE",
                    help="a text file of stored response ids, one per line")
    ap.add_argument("--response-id", action="append", default=[],
                    help="a single response id; repeatable")
    ap.add_argument("--min-offered", type=int, default=50,
                    help="turns a tool must have been offered in before "
                         "silence counts as evidence (default 50)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print tools that are being called normally")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key that can read stored "
                  "responses")
        return 2

    ids = list(args.response_id)
    if args.responses:
        try:
            with open(args.responses, "r", encoding="utf-8") as fh:
                ids.extend(parse_ids(fh.read()))
        except OSError as exc:
            log.error("could not read %s: %s", args.responses, exc)
            return 2
    ids = parse_ids("\\n".join(ids))
    if not ids:
        log.error("no usable response ids. /v1/responses cannot be listed, so "
                  "the sample has to come from your own request log")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    responses = []
    missing = 0
    for response_id in ids:
        body = get(session, "/responses/" + response_id)
        if body is None:
            missing += 1
            continue
        responses.append(body)
    if missing:
        log.info("%d of %d id(s) no longer resolve; stored responses are not "
                 "kept forever", missing, len(ids))

    corpus = fold(responses)
    rows = coverage(corpus)
    if not rows:
        log.info("no named tools declared in %d sampled response(s)",
                 corpus["sampled"])
        return 0

    orphans = orphan_calls(corpus)
    if orphans:
        log.warning("called but never declared in this sample: %s. The sample "
                    "mixes two configurations, so the set difference below is "
                    "not reliable.", ", ".join(orphans))

    bad = 0
    for row in rows:
        state, detail = classify(row, args.min_offered)
        line = "%-19s %-22s %s" % (state, row["name"], detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(state, row["name"]):
                log.warning("  repair: %s", repair)
        elif state == "rarely-called":
            log.warning(line)
            for repair in repair_lines(state, row["name"]):
                log.warning("  repair: %s", repair)
        elif args.show_all or state == "too-small-a-sample":
            log.info(line)

    log.info("%d declared tool(s) over %d response(s), %d finding(s)",
             len(rows), corpus["sampled"], bad)

    share = dead_weight(rows, args.min_offered)
    if share is not None:
        log.info("%.0f%% of the declared schema, in characters, belongs to "
                 "tools nothing ever called. Characters are not tokens: count "
                 "the block for free against count_tokens before pricing it.",
                 share * 100)

    state, detail = crowding(corpus["widest_turn"])
    if state == "crowded":
        log.warning("%-19s %s", state, detail)
        log.warning("  repair: narrow the turn with allowed_tools rather than "
                    "rewriting one description at a time.")
    else:
        log.info("%-19s %s", state, detail)

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-dead-tool-definitions.mjs",
"js": '''/**
 * Find OpenAI tool definitions that are sent on every call and never chosen.
 *
 * Read only. One GET per stored response id, using a project key. No
 * completion is created: /v1/responses is read, never posted to.
 *
 * There is no list endpoint for stored responses, so the sample comes from a
 * file of ids you supply, and every claim is bounded by that sample.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

// Output items that represent the model choosing one of your function tools.
const CALL_TYPES = new Set(['function_call', 'custom_tool_call']);

const CROWD_CEILING = 20;

const FINDINGS = new Set(['never-called', 'never-offered']);

/** Read a count as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Response ids out of a plain text file. Pure. Order kept, duplicates dropped.
 * Also the guard that stops an arbitrary line becoming a URL path segment.
 */
export function parseIds(text) {
  const out = [];
  const seen = new Set();
  for (const line of String(text ?? '').split('\\n')) {
    const candidate = line.split('#')[0].trim();
    if (!candidate || !candidate.startsWith('resp_')) continue;
    if (!/^[A-Za-z0-9_-]+$/.test(candidate)) continue;
    if (seen.has(candidate)) continue;
    seen.add(candidate);
    out.push(candidate);
  }
  return out;
}

/**
 * The function name out of either tool shape. Pure. Null when absent.
 * Responses puts name at the top level; Chat Completions nests it under
 * function, and a reader that knows one shape is blind on half a corpus.
 */
export function toolName(tool) {
  if (!tool || typeof tool !== 'object') return null;
  let name = tool.name;
  if (!name && tool.function && typeof tool.function === 'object') {
    name = tool.function.name;
  }
  const text = String(name ?? '').trim();
  return text || null;
}

/** Every named tool the request declared, with its size in characters. Pure. */
export function declaredTools(response) {
  const out = {};
  for (const tool of response?.tools ?? []) {
    const name = toolName(tool);
    if (name === null) continue;
    let size = 0;
    try {
      size = JSON.stringify(tool, Object.keys(tool).sort()).length;
    } catch {
      size = 0;
    }
    out[name] = Math.max(out[name] ?? 0, size);
  }
  return out;
}

/** Tool names the model actually chose in one response, counted. Pure. */
export function calledTools(response) {
  const counts = {};
  for (const item of response?.output ?? []) {
    if (!item || typeof item !== 'object' || !CALL_TYPES.has(item.type)) continue;
    const name = String(item.name ?? '').trim();
    if (!name) continue;
    counts[name] = (counts[name] ?? 0) + 1;
  }
  return counts;
}

/**
 * How free the model was to pick a tool in this turn. Pure.
 * "free", "blocked", or "named:<tool>". Absent tool_choice is auto, which is
 * free, and that is the line between a tool ignored and a tool ruled out.
 */
export function choiceMode(response) {
  const choice = response?.tool_choice;
  if (choice === null || choice === undefined) return 'free';
  if (typeof choice === 'string') {
    return choice.trim().toLowerCase() === 'none' ? 'blocked' : 'free';
  }
  if (typeof choice === 'object') {
    const name = toolName(choice);
    return name ? `named:${name}` : 'free';
  }
  return 'free';
}

/**
 * Fold a sample of stored responses into one corpus. Pure.
 * Declarations and offers are counted separately: a tool ruled out by
 * tool_choice on every turn is not dead weight and needs a different repair.
 */
export function fold(responses) {
  const corpus = { sampled: 0, withTools: 0, widestTurn: 0, calls: 0,
                   declared: {}, offered: {}, called: {} };
  for (const response of responses ?? []) {
    if (!response || typeof response !== 'object') continue;
    corpus.sampled += 1;
    const declared = declaredTools(response);
    for (const [name, count] of Object.entries(calledTools(response))) {
      corpus.called[name] = (corpus.called[name] ?? 0) + count;
      corpus.calls += count;
    }
    const names = Object.keys(declared);
    if (names.length === 0) continue;
    corpus.withTools += 1;
    corpus.widestTurn = Math.max(corpus.widestTurn, names.length);
    const mode = choiceMode(response);
    for (const name of names) {
      const row = corpus.declared[name] ?? { turns: 0, chars: 0 };
      row.turns += 1;
      row.chars = Math.max(row.chars, declared[name]);
      corpus.declared[name] = row;
      if (mode === 'blocked') continue;
      if (mode.startsWith('named:') && mode.slice('named:'.length) !== name) continue;
      corpus.offered[name] = (corpus.offered[name] ?? 0) + 1;
    }
  }
  return corpus;
}

/** One row per declared tool. Pure. Least used and most expensive first. */
export function coverage(corpus) {
  const rows = [];
  for (const [name, row] of Object.entries(corpus?.declared ?? {})) {
    rows.push({ name,
                turns: readInt(row?.turns),
                chars: readInt(row?.chars),
                offered: readInt(corpus?.offered?.[name]),
                calls: readInt(corpus?.called?.[name]) });
  }
  rows.sort((a, b) => (a.calls - b.calls) || (b.chars - a.chars)
    || a.name.localeCompare(b.name));
  return rows;
}

/** Names the model called that no sampled request declared. Pure. */
export function orphanCalls(corpus) {
  const declared = new Set(Object.keys(corpus?.declared ?? {}));
  return Object.keys(corpus?.called ?? {}).filter((n) => !declared.has(n)).sort();
}

/** Classify one tool's coverage across the sample. Pure. Returns [state, detail]. */
export function classify(row, minOffered = 50, rare = 0.01) {
  const name = String(row?.name ?? 'unknown');
  const turns = readInt(row?.turns);
  const offered = readInt(row?.offered);
  const calls = readInt(row?.calls);

  if (turns > 0 && offered === 0) {
    return ['never-offered',
      `declared in ${turns} turn(s), free to be chosen in 0 of them. ` +
      'tool_choice ruled it out every time, so the model never declined it ' +
      'and rewriting the description changes nothing.'];
  }
  if (offered < minOffered) {
    return ['too-small-a-sample',
      `offered in ${offered} turn(s), under the floor of ${minOffered}. ` +
      'Not enough to call anything dead.'];
  }
  if (calls === 0) {
    return ['never-called',
      `offered in ${offered} of ${turns} turn(s), called 0 time(s), ` +
      `${readInt(row?.chars)} schema char(s). Sent and billed on every one ` +
      'of those turns.'];
  }
  const share = calls / offered;
  if (share < rare) {
    return ['rarely-called',
      `offered in ${offered} turn(s), called ${calls} time(s) ` +
      `(${(share * 100).toFixed(1)}%). Worth keeping and worth not sending ` +
      `on every turn. ${name} is the exception, not the default.`];
  }
  return ['called',
    `offered in ${offered} turn(s), called ${calls} time(s) ` +
    `(${(share * 100).toFixed(1)}%).`];
}

/**
 * Share of the declared schema, in characters, that nothing ever calls. Pure.
 * Characters, never tokens. The token price is measured exactly and for free
 * elsewhere, and a character count dressed as a token count is worse than none.
 */
export function deadWeight(rows, minOffered = 50, rare = 0.01) {
  let total = 0;
  let dead = 0;
  for (const row of rows ?? []) {
    const chars = readInt(row?.chars);
    total += chars;
    if (classify(row, minOffered, rare)[0] === 'never-called') dead += chars;
  }
  if (total <= 0) return null;
  return dead / total;
}

/** What the widest turn in the sample looked like. Pure. */
export function crowding(widestTurn, ceiling = CROWD_CEILING) {
  const widest = readInt(widestTurn);
  if (widest <= 0) return ['no-tools', 'no sampled response declared any named tool'];
  if (widest > ceiling) {
    return ['crowded',
      `the widest turn offered ${widest} tools, above the guidance of fewer ` +
      `than ${ceiling}. Selection quality falls with crowding and it falls on ` +
      'the vaguest descriptions first.'];
  }
  return ['within-guidance',
    `the widest turn offered ${widest} tool(s), inside the guidance of fewer ` +
    `than ${ceiling}`];
}

/** The repair for one classified tool. Pure. */
export function repairLines(state, name) {
  if (state === 'never-called') {
    return [
      `the description probably reads like a signature. Rewrite it as a ` +
      `selection rule: when to call ${name}, and when not to.`,
      'if a call is mandatory, say so with tool_choice required or a named ' +
      'tool rather than hoping the model picks it up.',
      'if nothing needs it, delete it. It is billed on every turn.',
    ];
  }
  if (state === 'never-offered') {
    return [`tool_choice never let the model near ${name}. Fix the request ` +
            'before you touch the description.'];
  }
  if (state === 'rarely-called') {
    return [`keep ${name}, but stop sending it on every turn. allowed_tools ` +
            'narrows the set for the turns where it is plausible.'];
  }
  return [];
}

async function get(key, path) {
  const res = await fetch(API + path, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: OPENAI_API_KEY needs read ` +
                    'access to stored responses in this project');
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key that can read stored responses');
    process.exitCode = 2;
    return;
  }
  const file = process.argv.slice(2).find((a) => !a.startsWith('--'));
  if (!file) {
    console.error('pass a text file of stored response ids, one per line');
    process.exitCode = 2;
    return;
  }
  const minOffered = Number(process.env.MIN_OFFERED ?? 50);
  const showAll = process.env.SHOW_ALL === '1';

  const ids = parseIds(await readFile(file, 'utf8'));
  if (ids.length === 0) {
    console.error('no usable response ids. /v1/responses cannot be listed, so ' +
                  'the sample has to come from your own request log');
    process.exitCode = 2;
    return;
  }

  const responses = [];
  let missing = 0;
  for (const id of ids) {
    const body = await get(key, `/responses/${id}`);
    if (body === null) missing += 1;
    else responses.push(body);
  }
  if (missing > 0) {
    console.log(`${missing} of ${ids.length} id(s) no longer resolve; stored ` +
                'responses are not kept forever');
  }

  const corpus = fold(responses);
  const rows = coverage(corpus);
  if (rows.length === 0) {
    console.log(`no named tools declared in ${corpus.sampled} sampled response(s)`);
    return;
  }

  const orphans = orphanCalls(corpus);
  if (orphans.length > 0) {
    console.warn(`called but never declared in this sample: ${orphans.join(', ')}. ` +
                 'The sample mixes two configurations, so the set difference ' +
                 'below is not reliable.');
  }

  let bad = 0;
  for (const row of rows) {
    const [state, detail] = classify(row, minOffered);
    const line = `${state.padEnd(19)} ${row.name.padEnd(22)} ${detail}`;
    if (FINDINGS.has(state) || state === 'rarely-called') {
      if (FINDINGS.has(state)) bad += 1;
      console.warn(line);
      for (const repair of repairLines(state, row.name)) {
        console.warn(`  repair: ${repair}`);
      }
    } else if (showAll || state === 'too-small-a-sample') {
      console.log(line);
    }
  }

  console.log(`${rows.length} declared tool(s) over ${corpus.sampled} ` +
              `response(s), ${bad} finding(s)`);

  const share = deadWeight(rows, minOffered);
  if (share !== null) {
    console.log(`${(share * 100).toFixed(0)}% of the declared schema, in ` +
                'characters, belongs to tools nothing ever called. Characters ' +
                'are not tokens: count the block for free against count_tokens ' +
                'before pricing it.');
  }

  const [state, detail] = crowding(corpus.widestTurn);
  if (state === 'crowded') {
    console.warn(`${state.padEnd(19)} ${detail}`);
    console.warn('  repair: narrow the turn with allowed_tools rather than ' +
                 'rewriting one description at a time.');
  } else {
    console.log(`${state.padEnd(19)} ${detail}`);
  }

  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is the set difference itself: four hundred turns, six declared tools, one of them absent from every <code>output[]</code> array, and the classifier has to call that one dead while leaving the other five alone. Immediately beside it sits the case this note is most often wrong about &mdash; the same tool, the same four hundred turns, the same zero calls, but <code>tool_choice</code> named another tool every time &mdash; and it has to come back as a different state with a different repair, because the model never declined anything. The rest pin the two tool shapes, the sample floor that stops eleven turns becoming a verdict, the character share that is careful never to claim to be tokens, and the crowding check at exactly twenty.",
"test_py_file": "test_openai_dead_tool_definitions.py",
"test_py": '''from openai_dead_tool_definitions import (choice_mode, classify, coverage,
                                          crowding, dead_weight,
                                          declared_tools, fold, orphan_calls,
                                          parse_ids, tool_name)

TOOLS = [
    {"type": "function", "name": "lookup_order", "description": "x" * 200},
    {"type": "function", "name": "cancel_order", "description": "x" * 200},
    {"type": "function", "name": "lookup_invoice", "description": "x" * 200},
    {"type": "function", "name": "escalate_to_human", "description": "x" * 1000},
]


def turn(calls, choice=None, tools=None):
    body = {"tools": tools if tools is not None else TOOLS,
            "output": [{"type": "function_call", "name": n, "call_id": "call_1"}
                       for n in calls]}
    if choice is not None:
        body["tool_choice"] = choice
    return body


def test_a_tool_declared_on_every_turn_and_never_chosen_is_dead_weight():
    # The note in one assertion. Four hundred turns, four tools, one of them
    # absent from every output array.
    sample = [turn(["lookup_order"]) for _ in range(300)]
    sample += [turn(["cancel_order"]) for _ in range(98)]
    sample += [turn(["lookup_invoice"]) for _ in range(2)]
    corpus = fold(sample)
    assert corpus["sampled"] == 400 and corpus["with_tools"] == 400

    rows = {r["name"]: r for r in coverage(corpus)}
    assert rows["escalate_to_human"]["offered"] == 400
    assert rows["escalate_to_human"]["calls"] == 0

    state, detail = classify(rows["escalate_to_human"])
    assert state == "never-called"
    assert "offered in 400 of 400 turn(s), called 0 time(s)" in detail
    assert classify(rows["lookup_order"])[0] == "called"
    assert classify(rows["lookup_invoice"])[0] == "rarely-called"


def test_a_tool_tool_choice_never_offered_is_a_different_finding():
    # Same tool, same zero calls, and not this note: the model never had the
    # chance to decline it, so its description is not the problem.
    sample = [turn(["lookup_order"], choice={"type": "function",
                                             "name": "lookup_order"})
              for _ in range(400)]
    rows = {r["name"]: r for r in coverage(fold(sample))}
    state, detail = classify(rows["escalate_to_human"])
    assert state == "never-offered"
    assert "free to be chosen in 0 of them" in detail
    # And the named tool itself was on the table every time.
    assert rows["lookup_order"]["offered"] == 400
    assert classify(rows["lookup_order"])[0] == "called"


def test_tool_choice_none_is_not_evidence_about_anything():
    sample = [turn([], choice="none") for _ in range(400)]
    rows = {r["name"]: r for r in coverage(fold(sample))}
    assert rows["lookup_order"]["turns"] == 400
    assert rows["lookup_order"]["offered"] == 0
    assert classify(rows["lookup_order"])[0] == "never-offered"
    assert choice_mode({"tool_choice": "none"}) == "blocked"
    assert choice_mode({}) == "free"
    assert choice_mode({"tool_choice": "auto"}) == "free"
    assert choice_mode({"tool_choice": "required"}) == "free"


def test_both_tool_shapes_are_read():
    nested = [{"type": "function", "function": {"name": "run_refund"}}]
    assert tool_name(nested[0]) == "run_refund"
    assert tool_name({"type": "function", "name": "flat"}) == "flat"
    assert tool_name({"type": "web_search"}) is None
    assert tool_name(None) is None
    # A hosted tool carries no name and is not a definition you can prune.
    assert declared_tools({"tools": [{"type": "web_search"}]}) == {}
    assert set(declared_tools({"tools": nested})) == {"run_refund"}


def test_a_small_sample_is_not_a_verdict():
    rows = {r["name"]: r for r in coverage(fold([turn([]) for _ in range(11)]))}
    state, detail = classify(rows["lookup_order"])
    assert state == "too-small-a-sample"
    assert "under the floor of 50" in detail
    assert classify(rows["lookup_order"], min_offered=5)[0] == "never-called"


def test_the_dead_weight_share_is_characters_and_stays_characters():
    sample = [turn(["lookup_order", "cancel_order", "lookup_invoice"])
              for _ in range(400)]
    rows = coverage(fold(sample))
    share = dead_weight(rows)
    # escalate_to_human carries the 1000 character description; the other three
    # carry 200 each, so the dead share is well over half.
    assert 0.5 < share < 0.75
    assert dead_weight([]) is None
    assert dead_weight([{"name": "a", "chars": 0, "turns": 1, "offered": 1,
                         "calls": 0}]) is None


def test_a_crowded_turn_is_its_own_finding():
    wide = [{"type": "function", "name": "tool_%d" % i} for i in range(26)]
    corpus = fold([turn([], tools=wide) for _ in range(60)])
    state, detail = crowding(corpus["widest_turn"])
    assert state == "crowded"
    assert "offered 26 tools" in detail
    assert crowding(20)[0] == "within-guidance"
    assert crowding(0)[0] == "no-tools"


def test_a_mixed_sample_is_reported_rather_than_silently_subtracted():
    corpus = fold([turn(["from_another_config"])])
    assert orphan_calls(corpus) == ["from_another_config"]
    assert orphan_calls(fold([turn(["lookup_order"])])) == []
    assert fold([]) == fold(None)
    assert coverage(fold(None)) == []


def test_response_ids_are_validated_before_they_reach_a_url():
    text = "resp_abc123\\n# a comment\\n\\nresp_abc123\\nresp_def456\\n../../etc\\n"
    assert parse_ids(text) == ["resp_abc123", "resp_def456"]
    assert parse_ids("resp_bad/../x") == []
    assert parse_ids(None) == []
''',
"test_js_file": "openai-dead-tool-definitions.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { choiceMode, classify, coverage, crowding, deadWeight, declaredTools,
         fold, orphanCalls, parseIds, toolName }
  from './openai-dead-tool-definitions.mjs';

const TOOLS = [
  { type: 'function', name: 'lookup_order', description: 'x'.repeat(200) },
  { type: 'function', name: 'cancel_order', description: 'x'.repeat(200) },
  { type: 'function', name: 'lookup_invoice', description: 'x'.repeat(200) },
  { type: 'function', name: 'escalate_to_human', description: 'x'.repeat(1000) },
];

const turn = (calls, choice, tools) => {
  const body = {
    tools: tools ?? TOOLS,
    output: calls.map((name) => ({ type: 'function_call', name, call_id: 'call_1' })),
  };
  if (choice !== undefined) body.tool_choice = choice;
  return body;
};

const byName = (corpus) =>
  Object.fromEntries(coverage(corpus).map((r) => [r.name, r]));

test('a tool declared on every turn and never chosen is dead weight', () => {
  const sample = [
    ...Array.from({ length: 300 }, () => turn(['lookup_order'])),
    ...Array.from({ length: 98 }, () => turn(['cancel_order'])),
    ...Array.from({ length: 2 }, () => turn(['lookup_invoice'])),
  ];
  const corpus = fold(sample);
  assert.equal(corpus.sampled, 400);
  assert.equal(corpus.withTools, 400);

  const rows = byName(corpus);
  assert.equal(rows.escalate_to_human.offered, 400);
  assert.equal(rows.escalate_to_human.calls, 0);

  const [state, detail] = classify(rows.escalate_to_human);
  assert.equal(state, 'never-called');
  assert.match(detail, /offered in 400 of 400 turn/);
  assert.equal(classify(rows.lookup_order)[0], 'called');
  assert.equal(classify(rows.lookup_invoice)[0], 'rarely-called');
});

test('a tool tool_choice never offered is a different finding', () => {
  const sample = Array.from({ length: 400 },
    () => turn(['lookup_order'], { type: 'function', name: 'lookup_order' }));
  const rows = byName(fold(sample));
  const [state, detail] = classify(rows.escalate_to_human);
  assert.equal(state, 'never-offered');
  assert.match(detail, /free to be chosen in 0 of them/);
  assert.equal(rows.lookup_order.offered, 400);
  assert.equal(classify(rows.lookup_order)[0], 'called');
});

test('tool_choice none is not evidence about anything', () => {
  const rows = byName(fold(Array.from({ length: 400 }, () => turn([], 'none'))));
  assert.equal(rows.lookup_order.turns, 400);
  assert.equal(rows.lookup_order.offered, 0);
  assert.equal(classify(rows.lookup_order)[0], 'never-offered');
  assert.equal(choiceMode({ tool_choice: 'none' }), 'blocked');
  assert.equal(choiceMode({}), 'free');
  assert.equal(choiceMode({ tool_choice: 'auto' }), 'free');
  assert.equal(choiceMode({ tool_choice: 'required' }), 'free');
});

test('both tool shapes are read', () => {
  const nested = [{ type: 'function', function: { name: 'run_refund' } }];
  assert.equal(toolName(nested[0]), 'run_refund');
  assert.equal(toolName({ type: 'function', name: 'flat' }), 'flat');
  assert.equal(toolName({ type: 'web_search' }), null);
  assert.equal(toolName(null), null);
  assert.deepEqual(declaredTools({ tools: [{ type: 'web_search' }] }), {});
  assert.deepEqual(Object.keys(declaredTools({ tools: nested })), ['run_refund']);
});

test('a small sample is not a verdict', () => {
  const rows = byName(fold(Array.from({ length: 11 }, () => turn([]))));
  const [state, detail] = classify(rows.lookup_order);
  assert.equal(state, 'too-small-a-sample');
  assert.match(detail, /under the floor of 50/);
  assert.equal(classify(rows.lookup_order, 5)[0], 'never-called');
});

test('the dead weight share is characters and stays characters', () => {
  const sample = Array.from({ length: 400 },
    () => turn(['lookup_order', 'cancel_order', 'lookup_invoice']));
  const share = deadWeight(coverage(fold(sample)));
  assert.ok(share > 0.5 && share < 0.75);
  assert.equal(deadWeight([]), null);
  assert.equal(deadWeight([{ name: 'a', chars: 0, turns: 1, offered: 1, calls: 0 }]),
               null);
});

test('a crowded turn is its own finding', () => {
  const wide = Array.from({ length: 26 },
    (_, i) => ({ type: 'function', name: `tool_${i}` }));
  const corpus = fold(Array.from({ length: 60 }, () => turn([], undefined, wide)));
  const [state, detail] = crowding(corpus.widestTurn);
  assert.equal(state, 'crowded');
  assert.match(detail, /offered 26 tools/);
  assert.equal(crowding(20)[0], 'within-guidance');
  assert.equal(crowding(0)[0], 'no-tools');
});

test('a mixed sample is reported rather than silently subtracted', () => {
  assert.deepEqual(orphanCalls(fold([turn(['from_another_config'])])),
                   ['from_another_config']);
  assert.deepEqual(orphanCalls(fold([turn(['lookup_order'])])), []);
  assert.deepEqual(fold([]), fold(null));
  assert.deepEqual(coverage(fold(null)), []);
});

test('response ids are validated before they reach a url', () => {
  const text = 'resp_abc123\\n# a comment\\n\\nresp_abc123\\nresp_def456\\n../../etc\\n';
  assert.deepEqual(parseIds(text), ['resp_abc123', 'resp_def456']);
  assert.deepEqual(parseIds('resp_bad/../x'), []);
  assert.deepEqual(parseIds(null), []);
});
''',
"faq": [
 ("Why do I have to supply the response ids myself?",
  "Because /v1/responses cannot be listed. OpenAI exposes retrieval by id and nothing else, so there is no way to ask the API for the last thousand responses in a project. The ids have to come from your own request log. That is a real limitation and it shapes the note: every verdict here is bounded by the sample you supplied, which is why the output prints the sample size next to every finding."),
 ("Does a tool cost anything if the model never calls it?",
  "Yes, on every single request. Tool definitions are part of the prompt: the name, the description and the full JSON schema are serialised into the request and billed as input tokens whether or not anything is selected. That is the whole point of the note. A tool that never fires is not free capacity, it is a fixed line on every call, and because it was there from the first deploy it never shows up as a spike."),
 ("The script says a tool was never offered. What does that mean?",
  "It means your own request took it off the table. A turn sent with tool_choice set to none gives the model no tools at all, and a turn that names one tool gives it exactly one. On those turns the other definitions were still sent and still billed, but the model was never allowed to choose them, so their silence says nothing about their descriptions. The repair is in the request, not in the prose."),
 ("How many tools is too many in one turn?",
  "The documented guidance is fewer than twenty available at the start of a turn. It is not a hard limit and nothing 400s at twenty-one; selection quality just degrades, and it degrades first on the tools whose descriptions are vaguest. Once you are past it, no amount of description rewriting fixes the worst offenders, because the problem is the size of the choice rather than any one option in it."),
 ("Should I delete a tool that is called twice in five hundred turns?",
  "Usually not. Rare is not dead, and a tool that handles an uncommon but important path is doing its job. What you should stop doing is sending it on all five hundred turns: narrow the set per turn with allowed_tools so the model chooses among a handful, and keep the rare tool in the turns where it is plausible. That saves the tokens without losing the capability."),
],
"related": [REL_TOOL_TOKENS, REL_PARALLEL, REL_FINE_TUNED],
"citations": [CITE_OAI_FUNCTION_CALLING, CITE_OAI_RESPONSES,
              CITE_OAI_CONVERSATION_STATE, CITE_OAI_USAGE_COMPLETIONS],
},
{
"slug": "tool-schemas-dominate-input-tokens",
"title": "Tool schemas are most of the input tokens on every call",
"description": "Count the same body with tools and without. The difference is what the schemas cost per call, and the counting endpoint is free and bills nothing.",
"h1": "Tool schemas are most of the input tokens on every call",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude tool definition tokens", "count_tokens with and without tools",
             "tool use system prompt tokens", "defer_loading tool search",
             "tools first in cache order"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a workspace key. One GET for the model object plus the free count_tokens pre-flight, which creates nothing, generates nothing and is not billed.",
"lead": "The agent has forty tools because forty things are worth doing, and each definition is a careful JSON schema with descriptions on every property because that is how you get the arguments right. A support turn is one sentence from a customer. Nobody has ever asked what the block in front of that sentence weighs, and the answer, when somebody finally counts it, is that the machinery is thirteen times the conversation on every single call.",
"short_answer": """<p>Count the same request twice. <code>POST /v1/messages/count_tokens</code> is free, creates nothing, generates no completion and is not billed &mdash; it is the only pre-flight either provider offers. Send the exact body with its <code>tools</code>, then send it again with <code>tools</code> and <code>tool_choice</code> removed. The difference is the per-call tool overhead, exactly, before you spend anything.</p>
<p>Two things live inside that difference and they have different repairs. Your schemas are one. The other is an automatic tool-use system prompt that Claude adds whenever any tools are present at all: <strong>286 tokens</strong> on Claude Opus 5 for <code>tool_choice</code> of <code>auto</code> or <code>none</code> and <strong>406</strong> for <code>any</code> or a named tool, <strong>354/474</strong> on Sonnet 5, and larger on several older ids. Ablate one tool at a time and the deltas will not sum to the whole overhead, because no single ablation removes that fixed charge.</p>
<p>Then price it. Overhead tokens multiplied by calls per day, at your model's input rate, is a monthly number, and it is charged at the full uncached rate unless a <code>cache_control</code> breakpoint sits after the tool block.</p>
<p>This is a per-call weight, not a per-minute limiter. If the symptom is 429s rather than an invoice, the question is which limiter emptied, and <a href="/llm/itpm-exhausted-uncached-input/">the input-tokens-per-minute note</a> owns that.</p>""",
"problem": """<p>Everything in <code>tools</code> is input tokens: names, descriptions, and every line of the JSON schema including the property descriptions that make the arguments come back right. It is prompt, and it is re-sent on every request, because the API is stateless and there is nowhere to leave it. A registry that grew one tool at a time, each addition obviously worth it, arrives at a fixed per-call cost that nobody ever decided on.</p>
<p>The second cost is the one nobody expects, because it is not in your code at all. The moment any tool is present, an automatic tool-use system prompt is added to the request, and it is not small: several hundred tokens, varying by model id and by whether <code>tool_choice</code> forces a call. And the whole block sits <em>first</em> in the cache order &mdash; <code>tools</code>, then <code>system</code>, then <code>messages</code> &mdash; so editing one description invalidates not just the tools but everything cached behind them.</p>""",
"why": """<p><strong>The measurement is free, exact, and nobody takes it.</strong> <code>count_tokens</code> is a real tokenizer pass over the real body, so it is not an estimate and not a character heuristic. It creates no message, generates no output and costs nothing. Two calls give you the number for one request shape; a handful gives you the number for your whole surface. There is no reason to guess and every codebase guesses.</p>
<p><strong>Ablation prices each tool, and the residual is the interesting part.</strong> Remove one tool, count again, and the delta is that tool's schema weight. Do it for all of them and the deltas sum to <em>less</em> than the total overhead, because every ablated body still has tools in it and therefore still carries the automatic tool-use system prompt. What is left over is a fixed charge for having any tools at all, and it cannot be optimised by pruning &mdash; only by not sending tools on turns that do not need them.</p>
<p><strong>Anthropic's own server tools are priced the same way and are much larger.</strong> The bash tool is <strong>325</strong> tokens on Opus 5, 4.8 and 4.7 and 244 on Opus 4.6, Sonnet 4.6 and earlier; the text editor is about <strong>700</strong>; the computer toolset is around <strong>4,500</strong> and the browser toolset around <strong>6,600</strong>. Enabling one of those is a decision with a per-call price attached, and the price is not on the pricing page next to the model.</p>
<p><strong>The repair is a cache breakpoint before it is a smaller registry.</strong> Tool definitions are the most stable part of a prompt and they sit at the very front of the cache order, which makes them the single best thing to put a <code>cache_control</code> breakpoint after. A read costs 0.1x base input. The corollary is uncomfortable and worth saying out loud: once the block is cached, <em>editing a tool description is expensive</em>, because it invalidates the tools, the system prompt and the conversation behind them.</p>
<p><strong>Deferred loading is the other lever and it has a trap in it.</strong> The tool search tool lets rarely-used definitions carry <code>defer_loading: true</code> so their schemas are fetched on demand rather than sent every turn. Set it on every tool and the API returns 400 &mdash; <em>All tools have defer_loading set</em> &mdash; so the function in this script that picks candidates is written to be structurally incapable of returning the whole list. Which tools are rare is not a question this script can answer; <a href="/llm/tool-defined-but-never-called/">the call-coverage note</a> answers it.</p>""",
"steps": [
 {"h": "Capture one real request body as JSON",
  "body": """<p>The exact <code>model</code>, <code>system</code>, <code>tools</code>, <code>tool_choice</code> and a representative one-line <code>messages</code> array. A trimmed or idealised body measures a request you do not send. The sampling fields &mdash; <code>max_tokens</code>, <code>temperature</code>, <code>stream</code> and the rest &mdash; are stripped before counting, because the counting endpoint refuses them.</p>"""},
 {"h": "Count with tools, then count without",
  "body": """<p>Two calls to <code>POST /v1/messages/count_tokens</code>. Free, non-billed, and they generate nothing. The second body has <code>tools</code> and <code>tool_choice</code> removed and is otherwise byte-identical, so the difference is attributable to the tools and to nothing else.</p>"""},
 {"h": "Ablate one tool at a time for a per-tool price",
  "body": """<p>One more free call per tool. Each delta is that tool's schema weight in tokens. Sum them and subtract from the total overhead: what remains is the automatic tool-use system prompt, the fixed charge that no amount of pruning removes.</p>"""},
 {"h": "Turn tokens into a monthly number",
  "body": """<p>Overhead per call, times calls per day, times thirty, at your model's input rate. Do it at the uncached rate first, because that is what you are paying today, and quote the cached figure as the target rather than the baseline.</p>"""},
 {"h": "Print the breakpoint, then the deferral, then the pruning",
  "body": """<p>A <code>cache_control</code> breakpoint after the tool block is the cheapest change and the first one to make. Deferred loading on rarely-used tools is second, and never on all of them. Deleting tools is third, and it needs the coverage data this note does not have.</p>"""},
],
"verify": """<p>Re-run after the breakpoint lands. The counted overhead does not change &mdash; it is the same tokens &mdash; but the usage report should start showing cache reads against them at a tenth of the rate. Re-run again after any tool edit, because that edit invalidated the block.</p>
<pre><code class="language-bash">python3 anthropic_tool_schema_overhead.py --payload body.json --calls-per-day 10000
# schema-dominates   body.json  11500 of 12388 input token(s) are the tools block (93%)
#   888 token(s) of system and messages, so the tools outweigh the conversation 13.0 to 1
#   286 of the overhead is the automatic tool-use system prompt for claude-opus-5 at tool_choice auto
#   the fixed charge no ablation removes: 286 token(s); your schemas account for 11214
#   heaviest: search_knowledge_base 2140, create_ticket 1880, lookup_order 1210
#   6% of the 200000 token context window is spent before the user says anything
#   at 10000 call(s) a day and 3.00 per million input tokens that is 10350.00 a month, uncached
#   repair: put a cache_control breakpoint after the tools block. A read costs 0.1x base input.
# 1 payload(s) measured, 1 finding(s)</code></pre>""",
"code_intro": "One GET for the model object and then nothing but the free counter. Ten pure functions: the field stripper, which removes what the counting endpoint refuses without touching what is being measured; the two body transforms, whole-tools and one-tool-out; the overhead and its share; the classifier; the published tool-use system prompt table, matched on longest model prefix so <code>claude-opus-4-5</code> is never read as <code>claude-opus-5</code>; the residual, which is the honest way to say that ablation deltas do not add up to the whole; the deferral picker, written so it cannot return every tool and reproduce the 400; the monthly price; and the share of the context window the fixed prefix eats before anyone speaks.",
"py_file": "anthropic_tool_schema_overhead.py",
"py": '''"""Measure what a Claude tools block costs in input tokens on every call.

Read only. One GET for the model object and a handful of calls to
/v1/messages/count_tokens, which is free, creates no object, generates no
completion and is not billed. /v1/messages is never called.

The method is subtraction: count the exact body, count it again with tools
removed, and the difference is the per-call tool overhead. Ablating one tool at
a time prices each schema, and the deltas deliberately do not sum to the whole,
because every ablated body still carries the automatic tool-use system prompt.

The repair is printed, never performed. A cache breakpoint is a deploy.
"""
import argparse
import copy
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_tool_schema_overhead")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Fields the counting endpoint refuses. Stripped from every body before it is
# counted, and stripped identically from all of them so the subtraction stays
# honest: a field removed from one body and not another moves the difference.
SAMPLING_ONLY = ("max_tokens", "stream", "temperature", "top_p", "top_k",
                 "stop_sequences", "metadata", "service_tier")

# The automatic tool-use system prompt, per model, as (auto_or_none,
# any_or_tool). Added by the API whenever any tool is present, so it is part of
# the overhead and no amount of pruning removes it. Matched on longest prefix:
# a substring test reads claude-opus-4-5 as claude-opus-5 and reports the wrong
# fixed charge with total confidence.
TOOL_SYSTEM_PROMPT = {
    "claude-opus-5": (286, 406),
    "claude-opus-4-8": (290, 410),
    "claude-opus-4-7": (675, 804),
    "claude-opus-4-6": (497, 589),
    "claude-sonnet-4-6": (497, 589),
    "claude-sonnet-5": (354, 474),
    "claude-opus-4-5": (496, 588),
    "claude-sonnet-4-5": (496, 588),
    "claude-haiku-4-5": (496, 588),
}

FINDINGS = ("schema-dominates", "schema-heavy")


def _int(value):
    """Read a token count as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def countable(body):
    """A body the counting endpoint will accept. Pure. Does not mutate.

    Only the sampling fields go. Everything being measured stays, because the
    number is worthless if the thing counted is not the thing sent.
    """
    if not isinstance(body, dict):
        return {}
    return {k: copy.deepcopy(v) for k, v in body.items() if k not in SAMPLING_ONLY}


def without_tools(body):
    """The same body with the whole tools block removed. Pure.

    tool_choice goes with it. A body that names a tool it no longer declares is
    rejected, and the rejection would be read as "the counter is broken".
    """
    stripped = countable(body)
    stripped.pop("tools", None)
    stripped.pop("tool_choice", None)
    return stripped


def tool_names(body):
    """Named tools in a body, in declaration order. Pure."""
    out = []
    for tool in (body or {}).get("tools") or []:
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def without_tool(body, name):
    """The same body with exactly one tool removed. Pure. Does not mutate."""
    stripped = countable(body)
    kept = [t for t in stripped.get("tools") or []
            if not (isinstance(t, dict) and str(t.get("name") or "") == str(name))]
    stripped["tools"] = kept
    if not kept:
        stripped.pop("tools", None)
        stripped.pop("tool_choice", None)
    return stripped


def overhead(total, base):
    """Tokens attributable to the tools block. Pure. Never negative."""
    return max(0, _int(total) - _int(base))


def overhead_share(total, base):
    """Share of the counted input that the tools block accounts for. Pure.

    None when nothing was counted, which is a different state from zero and
    must not be printed as 0%.
    """
    counted = _int(total)
    if counted <= 0:
        return None
    return overhead(total, base) / float(counted)


def choice_kind(body):
    """Which column of the tool-use system prompt table applies. Pure.

    auto and none share one size; any and a named tool share the larger one.
    """
    choice = (body or {}).get("tool_choice")
    kind = ""
    if isinstance(choice, str):
        kind = choice.strip().lower()
    elif isinstance(choice, dict):
        kind = str(choice.get("type") or "").strip().lower()
    if kind in ("any", "tool"):
        return "any"
    return "auto"


def system_prompt_tokens(model, kind="auto"):
    """The automatic tool-use system prompt for one model. Pure. None if unlisted.

    Longest prefix wins. Unlisted ids return None rather than a neighbour's
    number, because a plausible wrong number here silently corrupts the split
    between "your schemas" and "the fixed charge".
    """
    name = str(model or "").strip().lower()
    best = None
    best_len = -1
    for prefix, sizes in TOOL_SYSTEM_PROMPT.items():
        if (name == prefix or name.startswith(prefix + "-")) and len(prefix) > best_len:
            best = sizes
            best_len = len(prefix)
    if best is None:
        return None
    return best[1] if str(kind).lower() == "any" else best[0]


def fixed_overhead(total_overhead, per_tool):
    """The part of the tool overhead that belongs to no single tool. Pure.

    Ablating one tool never removes the automatic tool-use system prompt,
    because the remaining tools still require it. So the per-tool deltas sum to
    the schema weight alone and the residual is the fixed charge for having any
    tools at all. Printing the sum as if it were the total is the mistake this
    function exists to make impossible.
    """
    measured = sum(max(0, _int(row.get("tokens"))) for row in per_tool or [])
    return max(0, _int(total_overhead) - measured), measured


def classify(total, base, dominate=0.5, heavy=0.25):
    """Classify one measured payload. Pure. Returns (state, detail)."""
    counted = _int(total)
    if counted <= 0:
        return ("nothing-counted",
                "the counting endpoint returned no tokens for this body")
    weight = overhead(total, base)
    if weight <= 0:
        return ("no-tools",
                "%d input token(s) and no measurable tools block" % counted)
    share = weight / float(counted)
    rest = counted - weight
    shape = ("%d of %d input token(s) are the tools block (%.0f%%)"
             % (weight, counted, share * 100))
    if rest > 0:
        shape += (", against %d token(s) of system and messages, a ratio of "
                  "%.1f to 1" % (rest, weight / float(rest)))
    if share >= dominate:
        return ("schema-dominates",
                shape + ". The machinery outweighs the conversation on every "
                "call, cached or not.")
    if share >= heavy:
        return ("schema-heavy",
                shape + ". Not dominant, and still the single largest stable "
                "block in the prompt, which makes it the cheapest thing to "
                "cache.")
    return ("schema-modest", shape + ".")


def defer_candidates(rows, hot=(), keep_eager=1):
    """Tools that could carry defer_loading, and never all of them. Pure.

    The API answers a request whose every tool defers with 400, "All tools have
    defer_loading set". A function able to return the whole list is a function
    that has already caused an outage, so at least one tool always stays eager
    whatever the arithmetic says.
    """
    names = [str(r.get("name")) for r in rows or [] if r.get("name")]
    if len(names) <= keep_eager:
        return []
    hot_set = {str(h) for h in hot or []}
    candidates = [n for n in names if n not in hot_set]
    if len(candidates) >= len(names):
        heaviest = sorted(rows, key=lambda r: -_int(r.get("tokens")))
        eager = {str(r.get("name")) for r in heaviest[:max(1, keep_eager)]}
        candidates = [n for n in names if n not in eager]
    return candidates


def monthly_cost(tokens_per_call, calls_per_day, rate_per_mtok, days=30):
    """What one per-call token count costs in a month. Pure. None if unpriced."""
    tokens = _int(tokens_per_call)
    calls = _int(calls_per_day)
    try:
        rate = float(rate_per_mtok)
    except (TypeError, ValueError):
        return None
    if tokens <= 0 or calls <= 0 or rate <= 0:
        return None
    return tokens * calls * int(days) / 1_000_000.0 * rate


def window_share(total, window):
    """Share of the model context window spent before the user speaks. Pure."""
    size = _int(window)
    if size <= 0:
        return None
    return min(1.0, _int(total) / float(size))


def get(session, path):
    r = session.get(API + path, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY has to be a "
                         "workspace key" % r.status_code)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


def count(session, body):
    """The one non-GET call. It creates nothing, generates nothing, bills nothing."""
    r = session.post(API + "/messages/count_tokens", json=body, timeout=120)
    if r.status_code >= 400:
        log.warning("count_tokens answered %d: %s", r.status_code, r.text[:200])
        return None
    return _int((r.json() or {}).get("input_tokens"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", action="append", default=[], required=True,
                    metavar="FILE", help="a JSON file holding a real request body")
    ap.add_argument("--calls-per-day", type=int, default=10000,
                    help="calls of this shape per day, for the monthly price")
    ap.add_argument("--input-rate", type=float, default=3.0,
                    help="your model's uncached input rate per million tokens")
    ap.add_argument("--hot", action="append", default=[],
                    help="a tool name that must stay eagerly loaded; repeatable")
    ap.add_argument("--no-per-tool", action="store_true",
                    help="skip the per-tool ablation")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION,
                            "content-type": "application/json"})

    checked = 0
    bad = 0
    for path in args.payload:
        with open(path, "r", encoding="utf-8") as fh:
            body = json.load(fh)
        checked += 1

        total = count(session, countable(body))
        base = count(session, without_tools(body))
        if total is None or base is None:
            log.warning("could not measure %s", path)
            continue

        state, detail = classify(total, base)
        line = "%-18s %-24s %s" % (state, path, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
        else:
            log.info(line)

        model = str(body.get("model") or "")
        kind = choice_kind(body)
        fixed = system_prompt_tokens(model, kind)
        if fixed is None:
            log.info("  no published tool-use system prompt size for %r, so "
                     "the fixed charge cannot be separated out here", model)
        else:
            log.info("  %d of the overhead is the automatic tool-use system "
                     "prompt for %s at tool_choice %s", fixed, model, kind)

        rows = []
        if not args.no_per_tool:
            for name in tool_names(body):
                one = count(session, without_tool(body, name))
                if one is None:
                    continue
                rows.append({"name": name, "tokens": max(0, total - one)})
            rows.sort(key=lambda r: -r["tokens"])
            residual, measured = fixed_overhead(overhead(total, base), rows)
            log.info("  the fixed charge no ablation removes: %d token(s); "
                     "your schemas account for %d", residual, measured)
            if rows:
                log.info("  heaviest: %s", ", ".join(
                    "%s %d" % (r["name"], r["tokens"]) for r in rows[:3]))

        window = get(session, "/models/" + model).get("max_input_tokens") if model else None
        share = window_share(total, window)
        if share is not None:
            log.info("  %.0f%% of the %d token context window is spent before "
                     "the user says anything. Whether a real conversation still "
                     "fits is the context-overflow question, not this one.",
                     share * 100, _int(window))

        price = monthly_cost(overhead(total, base), args.calls_per_day,
                             args.input_rate)
        if price is not None:
            log.info("  at %d call(s) a day and %.2f per million input tokens "
                     "that is %.2f a month, uncached", args.calls_per_day,
                     args.input_rate, price)

        if state in FINDINGS:
            log.warning("  repair: put a cache_control breakpoint after the "
                        "tools block. A read costs 0.1x base input, and tools "
                        "are the most stable thing in the prompt.")
            log.warning("  repair: editing any tool description after that "
                        "invalidates the tools, the system prompt and the "
                        "messages behind them. Batch tool edits.")
            candidates = defer_candidates(rows, args.hot)
            if candidates:
                log.warning("  repair: defer_loading on rarely used tools only "
                            "(%s). Never on all of them: the API answers 400, "
                            "All tools have defer_loading set. Which are rare "
                            "is a call-coverage question this script cannot "
                            "answer.", ", ".join(candidates[:5]))

    log.info("%d payload(s) measured, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-tool-schema-overhead.mjs",
"js": '''/**
 * Measure what a Claude tools block costs in input tokens on every call.
 *
 * Read only. One GET for the model object and a handful of calls to
 * /v1/messages/count_tokens, which is free, creates no object, generates no
 * completion and is not billed. /v1/messages is never called.
 *
 * Count the body, count it again with tools removed, subtract. Ablate one tool
 * at a time for a per-tool price, and note that the deltas do not sum to the
 * whole: every ablated body still carries the tool-use system prompt.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// Fields the counting endpoint refuses, stripped identically from every body.
const SAMPLING_ONLY = new Set(['max_tokens', 'stream', 'temperature', 'top_p',
  'top_k', 'stop_sequences', 'metadata', 'service_tier']);

// The automatic tool-use system prompt per model, as [autoOrNone, anyOrTool].
// Longest prefix wins: a substring test reads claude-opus-4-5 as claude-opus-5.
const TOOL_SYSTEM_PROMPT = {
  'claude-opus-5': [286, 406],
  'claude-opus-4-8': [290, 410],
  'claude-opus-4-7': [675, 804],
  'claude-opus-4-6': [497, 589],
  'claude-sonnet-4-6': [497, 589],
  'claude-sonnet-5': [354, 474],
  'claude-opus-4-5': [496, 588],
  'claude-sonnet-4-5': [496, 588],
  'claude-haiku-4-5': [496, 588],
};

const FINDINGS = new Set(['schema-dominates', 'schema-heavy']);

/** Read a token count as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/** A body the counting endpoint will accept. Pure. Does not mutate. */
export function countable(body) {
  if (!body || typeof body !== 'object') return {};
  const out = {};
  for (const [k, v] of Object.entries(body)) {
    if (!SAMPLING_ONLY.has(k)) out[k] = structuredClone(v);
  }
  return out;
}

/**
 * The same body with the whole tools block removed. Pure.
 * tool_choice goes with it: a body naming a tool it no longer declares is
 * rejected, and the rejection reads as a broken counter.
 */
export function withoutTools(body) {
  const stripped = countable(body);
  delete stripped.tools;
  delete stripped.tool_choice;
  return stripped;
}

/** Named tools in a body, in declaration order. Pure. */
export function toolNames(body) {
  const out = [];
  for (const tool of body?.tools ?? []) {
    if (!tool || typeof tool !== 'object') continue;
    const name = String(tool.name ?? '').trim();
    if (name && !out.includes(name)) out.push(name);
  }
  return out;
}

/** The same body with exactly one tool removed. Pure. Does not mutate. */
export function withoutTool(body, name) {
  const stripped = countable(body);
  const kept = (stripped.tools ?? []).filter(
    (t) => !(t && typeof t === 'object' && String(t.name ?? '') === String(name)));
  stripped.tools = kept;
  if (kept.length === 0) {
    delete stripped.tools;
    delete stripped.tool_choice;
  }
  return stripped;
}

/** Tokens attributable to the tools block. Pure. Never negative. */
export function overhead(total, base) {
  return Math.max(0, readInt(total) - readInt(base));
}

/** Share of counted input the tools block accounts for. Pure. Null when none. */
export function overheadShare(total, base) {
  const counted = readInt(total);
  if (counted <= 0) return null;
  return overhead(total, base) / counted;
}

/** Which column of the tool-use system prompt table applies. Pure. */
export function choiceKind(body) {
  const choice = body?.tool_choice;
  let kind = '';
  if (typeof choice === 'string') kind = choice.trim().toLowerCase();
  else if (choice && typeof choice === 'object') {
    kind = String(choice.type ?? '').trim().toLowerCase();
  }
  return kind === 'any' || kind === 'tool' ? 'any' : 'auto';
}

/**
 * The automatic tool-use system prompt for one model. Pure. Null if unlisted.
 * Unlisted returns null rather than a neighbour's number: a plausible wrong
 * value here silently corrupts the split between schemas and fixed charge.
 */
export function systemPromptTokens(model, kind = 'auto') {
  const name = String(model ?? '').trim().toLowerCase();
  let best = null;
  let bestLen = -1;
  for (const [prefix, sizes] of Object.entries(TOOL_SYSTEM_PROMPT)) {
    if ((name === prefix || name.startsWith(`${prefix}-`)) && prefix.length > bestLen) {
      best = sizes;
      bestLen = prefix.length;
    }
  }
  if (best === null) return null;
  return String(kind).toLowerCase() === 'any' ? best[1] : best[0];
}

/**
 * The part of the tool overhead that belongs to no single tool. Pure.
 * Returns [residual, measured]. Ablation never removes the tool-use system
 * prompt, so the deltas sum to the schema weight and the rest is fixed.
 */
export function fixedOverhead(totalOverhead, perTool) {
  let measured = 0;
  for (const row of perTool ?? []) measured += Math.max(0, readInt(row?.tokens));
  return [Math.max(0, readInt(totalOverhead) - measured), measured];
}

/** Classify one measured payload. Pure. Returns [state, detail]. */
export function classify(total, base, dominate = 0.5, heavy = 0.25) {
  const counted = readInt(total);
  if (counted <= 0) {
    return ['nothing-counted', 'the counting endpoint returned no tokens for this body'];
  }
  const weight = overhead(total, base);
  if (weight <= 0) {
    return ['no-tools', `${counted} input token(s) and no measurable tools block`];
  }
  const share = weight / counted;
  const rest = counted - weight;
  let shape = `${weight} of ${counted} input token(s) are the tools block ` +
    `(${(share * 100).toFixed(0)}%)`;
  if (rest > 0) {
    shape += `, against ${rest} token(s) of system and messages, a ratio of ` +
      `${(weight / rest).toFixed(1)} to 1`;
  }
  if (share >= dominate) {
    return ['schema-dominates',
      `${shape}. The machinery outweighs the conversation on every call, ` +
      'cached or not.'];
  }
  if (share >= heavy) {
    return ['schema-heavy',
      `${shape}. Not dominant, and still the single largest stable block in ` +
      'the prompt, which makes it the cheapest thing to cache.'];
  }
  return ['schema-modest', `${shape}.`];
}

/**
 * Tools that could carry defer_loading, and never all of them. Pure.
 * The API answers a fully deferred request with 400, "All tools have
 * defer_loading set", so at least one tool always stays eager.
 */
export function deferCandidates(rows, hot = [], keepEager = 1) {
  const names = (rows ?? []).map((r) => String(r?.name ?? '')).filter(Boolean);
  if (names.length <= keepEager) return [];
  const hotSet = new Set((hot ?? []).map(String));
  let candidates = names.filter((n) => !hotSet.has(n));
  if (candidates.length >= names.length) {
    const heaviest = [...rows].sort((a, b) => readInt(b?.tokens) - readInt(a?.tokens));
    const eager = new Set(heaviest.slice(0, Math.max(1, keepEager))
      .map((r) => String(r?.name ?? '')));
    candidates = names.filter((n) => !eager.has(n));
  }
  return candidates;
}

/** What one per-call token count costs in a month. Pure. Null if unpriced. */
export function monthlyCost(tokensPerCall, callsPerDay, ratePerMtok, days = 30) {
  const tokens = readInt(tokensPerCall);
  const calls = readInt(callsPerDay);
  const rate = Number(ratePerMtok);
  if (!Number.isFinite(rate) || tokens <= 0 || calls <= 0 || rate <= 0) return null;
  return (tokens * calls * Math.trunc(days)) / 1000000 * rate;
}

/** Share of the model context window spent before the user speaks. Pure. */
export function windowShare(total, window) {
  const size = readInt(window);
  if (size <= 0) return null;
  return Math.min(1, readInt(total) / size);
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
  if (res.status === 404) return {};
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

/** The one non-GET call. It creates nothing, generates nothing, bills nothing. */
async function count(key, body) {
  const res = await fetch(`${API}/messages/count_tokens`, {
    method: 'POST',  // count_tokens creates nothing and bills nothing
    headers: headers(key),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    console.warn(`count_tokens answered ${res.status}`);
    return null;
  }
  return readInt((await res.json())?.input_tokens);
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
  const callsPerDay = Number(process.env.CALLS_PER_DAY ?? 10000);
  const inputRate = Number(process.env.INPUT_RATE ?? 3.0);
  const hot = String(process.env.HOT ?? '').split(',').filter(Boolean);
  const perTool = process.env.NO_PER_TOOL !== '1';

  let checked = 0;
  let bad = 0;
  for (const path of paths) {
    const body = JSON.parse(await readFile(path, 'utf8'));
    checked += 1;

    const total = await count(key, countable(body));
    const base = await count(key, withoutTools(body));
    if (total === null || base === null) {
      console.warn(`could not measure ${path}`);
      continue;
    }

    const [state, detail] = classify(total, base);
    const line = `${state.padEnd(18)} ${path.padEnd(24)} ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
    } else {
      console.log(line);
    }

    const model = String(body.model ?? '');
    const kind = choiceKind(body);
    const fixed = systemPromptTokens(model, kind);
    if (fixed === null) {
      console.log(`  no published tool-use system prompt size for ${model}, so ` +
                  'the fixed charge cannot be separated out here');
    } else {
      console.log(`  ${fixed} of the overhead is the automatic tool-use system ` +
                  `prompt for ${model} at tool_choice ${kind}`);
    }

    let rows = [];
    if (perTool) {
      for (const name of toolNames(body)) {
        const one = await count(key, withoutTool(body, name));
        if (one === null) continue;
        rows.push({ name, tokens: Math.max(0, total - one) });
      }
      rows.sort((a, b) => b.tokens - a.tokens);
      const [residual, measured] = fixedOverhead(overhead(total, base), rows);
      console.log(`  the fixed charge no ablation removes: ${residual} token(s); ` +
                  `your schemas account for ${measured}`);
      if (rows.length > 0) {
        console.log(`  heaviest: ${rows.slice(0, 3)
          .map((r) => `${r.name} ${r.tokens}`).join(', ')}`);
      }
    }

    const window = model ? (await get(key, `/models/${model}`))?.max_input_tokens : null;
    const share = windowShare(total, window);
    if (share !== null) {
      console.log(`  ${(share * 100).toFixed(0)}% of the ${readInt(window)} token ` +
                  'context window is spent before the user says anything. Whether ' +
                  'a real conversation still fits is the context-overflow ' +
                  'question, not this one.');
    }

    const price = monthlyCost(overhead(total, base), callsPerDay, inputRate);
    if (price !== null) {
      console.log(`  at ${callsPerDay} call(s) a day and ${inputRate.toFixed(2)} ` +
                  `per million input tokens that is ${price.toFixed(2)} a month, uncached`);
    }

    if (FINDINGS.has(state)) {
      console.warn('  repair: put a cache_control breakpoint after the tools ' +
                   'block. A read costs 0.1x base input, and tools are the most ' +
                   'stable thing in the prompt.');
      console.warn('  repair: editing any tool description after that ' +
                   'invalidates the tools, the system prompt and the messages ' +
                   'behind them. Batch tool edits.');
      const candidates = deferCandidates(rows, hot);
      if (candidates.length > 0) {
        console.warn(`  repair: defer_loading on rarely used tools only ` +
                     `(${candidates.slice(0, 5).join(', ')}). Never on all of ` +
                     'them: the API answers 400, All tools have defer_loading ' +
                     'set. Which are rare is a call-coverage question this ' +
                     'script cannot answer.');
      }
    }
  }

  console.log(`${checked} payload(s) measured, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the subtraction the whole note rests on: 12,388 counted with tools and 888 without, so 11,500 tokens of the request are machinery and the conversation is seven percent of what you pay for. The second is the one that stops a plausible lie being printed &mdash; the per-tool ablation deltas sum to <em>less</em> than the total overhead, and the residual is asserted to be exactly the tool-use system prompt for the model in the body, because a script that reported the sum as the total would be wrong by several hundred tokens on every call and look right. The rest pin the longest-prefix lookup that must never read <code>claude-opus-4-5</code> as <code>claude-opus-5</code>, the deferral picker that is structurally unable to return every tool and reproduce the documented 400, and the two body transforms, which have to remove <code>tool_choice</code> alongside the tools and leave everything else untouched.",
"test_py_file": "test_anthropic_tool_schema_overhead.py",
"test_py": '''from anthropic_tool_schema_overhead import (choice_kind, classify, countable,
                                            defer_candidates, fixed_overhead,
                                            monthly_cost, overhead,
                                            overhead_share,
                                            system_prompt_tokens, tool_names,
                                            window_share, without_tool,
                                            without_tools)

BODY = {
    "model": "claude-opus-5",
    "max_tokens": 1024,
    "temperature": 0,
    "system": "You are a support agent.",
    "tool_choice": {"type": "auto"},
    "messages": [{"role": "user", "content": "where is my order"}],
    "tools": [
        {"name": "search_knowledge_base", "input_schema": {"type": "object"}},
        {"name": "create_ticket", "input_schema": {"type": "object"}},
        {"name": "lookup_order", "input_schema": {"type": "object"}},
    ],
}


def test_the_tools_block_is_most_of_what_you_pay_for():
    # The note in one assertion. Two free counts, one subtraction.
    total, base = 12388, 888
    assert overhead(total, base) == 11500
    assert round(overhead_share(total, base), 4) == 0.9283

    state, detail = classify(total, base)
    assert state == "schema-dominates"
    assert "11500 of 12388 input token(s) are the tools block (93%)" in detail
    assert "888 token(s) of system and messages, a ratio of 13.0 to 1" in detail

    # 11500 tokens on 10000 calls a day for 30 days at $3 per million.
    assert monthly_cost(11500, 10000, 3.0) == 10350.0


def test_the_ablation_deltas_do_not_add_up_to_the_whole():
    # The trap. Removing one tool never removes the tool-use system prompt, so
    # the per-tool sum is the schema weight and the residual is the fixed
    # charge. A script that printed the sum as the total would be wrong by 286
    # tokens on every call and would look right.
    per_tool = [{"name": "search_knowledge_base", "tokens": 6200},
                {"name": "create_ticket", "tokens": 3100},
                {"name": "lookup_order", "tokens": 1914}]
    residual, measured = fixed_overhead(11500, per_tool)
    assert measured == 11214
    assert residual == 286
    assert residual == system_prompt_tokens("claude-opus-5", "auto")
    assert fixed_overhead(0, per_tool) == (0, 11214)


def test_the_system_prompt_table_matches_on_longest_prefix():
    assert system_prompt_tokens("claude-opus-5") == 286
    assert system_prompt_tokens("claude-opus-5", "any") == 406
    assert system_prompt_tokens("claude-sonnet-5") == 354
    # The one a careless substring match gets wrong: 4-5 is not 5.
    assert system_prompt_tokens("claude-opus-4-5") == 496
    assert system_prompt_tokens("claude-haiku-4-5-20251001") == 496
    assert system_prompt_tokens("claude-opus-4-7", "any") == 804
    # Unlisted returns nothing rather than a neighbour's number.
    assert system_prompt_tokens("claude-fable-5") is None
    assert system_prompt_tokens("") is None
    assert system_prompt_tokens(None) is None


def test_removing_the_tools_removes_the_tool_choice_with_them():
    stripped = without_tools(BODY)
    assert "tools" not in stripped and "tool_choice" not in stripped
    assert stripped["system"] == BODY["system"]
    assert stripped["messages"] == BODY["messages"]
    # And the original is untouched, or the second count measures the first.
    assert len(BODY["tools"]) == 3 and "tool_choice" in BODY

    one_out = without_tool(BODY, "create_ticket")
    assert tool_names(one_out) == ["search_knowledge_base", "lookup_order"]
    assert one_out["tool_choice"] == BODY["tool_choice"]
    # Removing the last tool has to take tool_choice with it as well.
    bare = without_tool({"tools": [{"name": "only"}], "tool_choice": "any"}, "only")
    assert "tools" not in bare and "tool_choice" not in bare


def test_the_deferral_picker_can_never_return_every_tool():
    rows = [{"name": "a", "tokens": 900}, {"name": "b", "tokens": 400},
            {"name": "c", "tokens": 100}]
    picked = defer_candidates(rows)
    assert picked == ["b", "c"]
    assert len(picked) < len(rows)
    # Naming every tool hot leaves nothing to defer, which is also fine.
    assert defer_candidates(rows, hot=["a", "b", "c"]) == []
    assert defer_candidates(rows, hot=["a"]) == ["b", "c"]
    assert defer_candidates([{"name": "only", "tokens": 10}]) == []
    assert defer_candidates([]) == []


def test_the_counting_body_keeps_what_is_being_measured():
    body = countable(BODY)
    assert "max_tokens" not in body and "temperature" not in body
    assert body["tools"] == BODY["tools"]
    assert body["model"] == "claude-opus-5"
    assert countable(None) == {}
    assert choice_kind(BODY) == "auto"
    assert choice_kind({"tool_choice": {"type": "tool", "name": "x"}}) == "any"
    assert choice_kind({"tool_choice": "any"}) == "any"
    assert choice_kind({}) == "auto"


def test_the_states_are_bounded_and_a_missing_number_stays_missing():
    assert classify(1000, 900)[0] == "schema-modest"
    assert classify(1000, 700)[0] == "schema-heavy"
    assert classify(1000, 500)[0] == "schema-dominates"
    assert classify(1000, 1000)[0] == "no-tools"
    assert classify(0, 0)[0] == "nothing-counted"
    assert overhead_share(0, 0) is None
    assert overhead(500, 900) == 0
    assert monthly_cost(11500, 0, 3.0) is None
    assert monthly_cost(11500, 10, "free") is None
    assert window_share(12388, 200000) == 0.06194
    assert window_share(12388, 0) is None
''',
"test_js_file": "anthropic-tool-schema-overhead.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { choiceKind, classify, countable, deferCandidates, fixedOverhead,
         monthlyCost, overhead, overheadShare, systemPromptTokens, toolNames,
         windowShare, withoutTool, withoutTools }
  from './anthropic-tool-schema-overhead.mjs';

const BODY = {
  model: 'claude-opus-5',
  max_tokens: 1024,
  temperature: 0,
  system: 'You are a support agent.',
  tool_choice: { type: 'auto' },
  messages: [{ role: 'user', content: 'where is my order' }],
  tools: [
    { name: 'search_knowledge_base', input_schema: { type: 'object' } },
    { name: 'create_ticket', input_schema: { type: 'object' } },
    { name: 'lookup_order', input_schema: { type: 'object' } },
  ],
};

test('the tools block is most of what you pay for', () => {
  const total = 12388;
  const base = 888;
  assert.equal(overhead(total, base), 11500);
  assert.equal(Number(overheadShare(total, base).toFixed(4)), 0.9283);

  const [state, detail] = classify(total, base);
  assert.equal(state, 'schema-dominates');
  assert.match(detail, /11500 of 12388 input token/);
  assert.match(detail, /888 token\\(s\\) of system and messages, a ratio of 13.0 to 1/);

  assert.equal(monthlyCost(11500, 10000, 3.0), 10350);
});

test('the ablation deltas do not add up to the whole', () => {
  const perTool = [{ name: 'search_knowledge_base', tokens: 6200 },
                   { name: 'create_ticket', tokens: 3100 },
                   { name: 'lookup_order', tokens: 1914 }];
  const [residual, measured] = fixedOverhead(11500, perTool);
  assert.equal(measured, 11214);
  assert.equal(residual, 286);
  assert.equal(residual, systemPromptTokens('claude-opus-5', 'auto'));
  assert.deepEqual(fixedOverhead(0, perTool), [0, 11214]);
});

test('the system prompt table matches on longest prefix', () => {
  assert.equal(systemPromptTokens('claude-opus-5'), 286);
  assert.equal(systemPromptTokens('claude-opus-5', 'any'), 406);
  assert.equal(systemPromptTokens('claude-sonnet-5'), 354);
  assert.equal(systemPromptTokens('claude-opus-4-5'), 496);
  assert.equal(systemPromptTokens('claude-haiku-4-5-20251001'), 496);
  assert.equal(systemPromptTokens('claude-opus-4-7', 'any'), 804);
  assert.equal(systemPromptTokens('claude-fable-5'), null);
  assert.equal(systemPromptTokens(''), null);
  assert.equal(systemPromptTokens(null), null);
});

test('removing the tools removes the tool_choice with them', () => {
  const stripped = withoutTools(BODY);
  assert.equal('tools' in stripped, false);
  assert.equal('tool_choice' in stripped, false);
  assert.equal(stripped.system, BODY.system);
  assert.deepEqual(stripped.messages, BODY.messages);
  assert.equal(BODY.tools.length, 3);
  assert.equal('tool_choice' in BODY, true);

  const oneOut = withoutTool(BODY, 'create_ticket');
  assert.deepEqual(toolNames(oneOut), ['search_knowledge_base', 'lookup_order']);
  assert.deepEqual(oneOut.tool_choice, BODY.tool_choice);

  const bare = withoutTool({ tools: [{ name: 'only' }], tool_choice: 'any' }, 'only');
  assert.equal('tools' in bare, false);
  assert.equal('tool_choice' in bare, false);
});

test('the deferral picker can never return every tool', () => {
  const rows = [{ name: 'a', tokens: 900 }, { name: 'b', tokens: 400 },
                { name: 'c', tokens: 100 }];
  const picked = deferCandidates(rows);
  assert.deepEqual(picked, ['b', 'c']);
  assert.ok(picked.length < rows.length);
  assert.deepEqual(deferCandidates(rows, ['a', 'b', 'c']), []);
  assert.deepEqual(deferCandidates(rows, ['a']), ['b', 'c']);
  assert.deepEqual(deferCandidates([{ name: 'only', tokens: 10 }]), []);
  assert.deepEqual(deferCandidates([]), []);
});

test('the counting body keeps what is being measured', () => {
  const body = countable(BODY);
  assert.equal('max_tokens' in body, false);
  assert.equal('temperature' in body, false);
  assert.deepEqual(body.tools, BODY.tools);
  assert.equal(body.model, 'claude-opus-5');
  assert.deepEqual(countable(null), {});
  assert.equal(choiceKind(BODY), 'auto');
  assert.equal(choiceKind({ tool_choice: { type: 'tool', name: 'x' } }), 'any');
  assert.equal(choiceKind({ tool_choice: 'any' }), 'any');
  assert.equal(choiceKind({}), 'auto');
});

test('the states are bounded and a missing number stays missing', () => {
  assert.equal(classify(1000, 900)[0], 'schema-modest');
  assert.equal(classify(1000, 700)[0], 'schema-heavy');
  assert.equal(classify(1000, 500)[0], 'schema-dominates');
  assert.equal(classify(1000, 1000)[0], 'no-tools');
  assert.equal(classify(0, 0)[0], 'nothing-counted');
  assert.equal(overheadShare(0, 0), null);
  assert.equal(overhead(500, 900), 0);
  assert.equal(monthlyCost(11500, 0, 3.0), null);
  assert.equal(monthlyCost(11500, 10, 'free'), null);
  assert.equal(windowShare(12388, 200000), 0.06194);
  assert.equal(windowShare(12388, 0), null);
});
''',
"faq": [
 ("Does count_tokens cost anything or generate anything?",
  "No to both. It runs the tokenizer over the body and returns an input_tokens number. No message is created, no completion is generated and nothing is billed, which is why it is the one non-GET call the scripts in this section are allowed to make. It is also exact rather than an estimate: it is the same tokenizer that will run when you actually send the request."),
 ("Why do the per-tool numbers not add up to the total overhead?",
  "Because every ablated body still has tools in it. The automatic tool-use system prompt is added whenever any tool is present, so removing one tool at a time never removes it, and the deltas therefore measure schemas only. The leftover is that fixed charge. It is several hundred tokens on every call, it is not in your code, and pruning tools does not touch it."),
 ("Is caching the tool block safe if the tools change occasionally?",
  "Yes, and the cost of a change is worth knowing before you make it. Tools sit first in the cache order, ahead of the system prompt and the messages, so any edit to a tool definition invalidates everything behind it and the next call pays a full write at 1.25x. That is fine monthly and painful hourly, so batch tool edits into a deploy rather than trickling them."),
 ("Should I put defer_loading on all the rarely used tools?",
  "On the rarely used ones, yes. On all of them, no: the API rejects a request in which every tool defers with a 400 reading All tools have defer_loading set, which is why the function that picks candidates here always keeps at least one eager. Deciding which tools are rare needs call data, and that is a different note in this section."),
 ("The bill is fine but I keep getting 429s. Is this the same problem?",
  "Related cause, different note. A large fixed prefix does eat input-tokens-per-minute headroom, but the finding there is which limiter emptied and the fix is throughput rather than cost. This note measures per-call weight and prices it. If the symptom is rate limiting rather than an invoice, start with the input-tokens-per-minute note and come back here for the size of the block."),
],
"related": [REL_DEAD_TOOL, REL_CHURN, REL_CONTEXT],
"citations": [CITE_CL_TOOL_USE, CITE_CL_TOKEN_COUNTING, CITE_CL_PRICING,
              CITE_CL_CACHING],
},
{
"slug": "parallel-tool-calls-with-strict-schema",
"title": "Parallel tool calls void the strict schema guarantee",
"description": "Structured Outputs is not supported alongside parallel function calls, and parallel_tool_calls defaults to true. The guarantee holds until the model fans out.",
"h1": "Parallel tool calls void the strict schema guarantee",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["parallel_tool_calls strict", "structured outputs parallel function calls",
             "strict true arguments invalid", "two function_call items one turn",
             "duplicate tool call double side effect"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key that can read stored responses, and a file of response ids: /v1/responses cannot be listed, so the sample has to come from your own logs.",
"lead": "The schemas are strict, every one of them, because somebody read the Structured Outputs page properly and did the work. The parser has no try/except around it, deliberately: the arguments are guaranteed to conform, so a failure there should be loud. It has been loud four times in three months, always on a Tuesday afternoon, always with a stack trace that says a required field was missing, and always unreproducible from the same prompt. The four turns have one thing in common that nobody looked at: each of them called two tools instead of one.",
"short_answer": """<p>Read stored responses one turn at a time and look for fan-out. With a <strong>project key</strong>: <code>GET /v1/responses/{response_id}</code>. Flag any response whose <code>output[]</code> contains more than one item of <code>type: "function_call"</code> while the request it echoes has <code>parallel_tool_calls</code> true or absent and any tool declaring <code>strict: true</code>.</p>
<p>Structured Outputs is not supported together with parallel function calls. The documented guidance is to set <code>parallel_tool_calls: false</code> when you are relying on strict schemas. The field defaults to <strong>true</strong>, so the guarantee degrades silently, and it degrades exactly when the model decides to fan out rather than when anything changed in your code.</p>
<p>That is why it is deterministic in tests and flaky in production. A test sends a prompt that provokes one call. Real traffic sends whatever the user typed, and some fraction of it provokes two. The script reports that fraction as a rate, because a documented interaction becomes a priority only once it has a number attached.</p>
<p>Flag repeated calls to the <em>same</em> tool in one turn separately. That is a second fault with the same trigger: a handler written for one call per turn double-applies. Key every handler on <code>call_id</code>.</p>""",
"problem": """<p>Every part of the configuration is correct in isolation, which is why this survives review. <code>strict: true</code> is right. The schemas are right. <code>parallel_tool_calls</code> was never set, because nobody sets it, and its default is the one that lets the model fan out. The interaction between the two is documented and it is one sentence in the middle of a guide about something else.</p>
<p>What comes back on a fan-out turn is an HTTP 200 with several <code>function_call</code> items whose <code>arguments</code> strings are no longer constrained by the schema you declared. Usually they are fine anyway &mdash; the model is good at this &mdash; which is worse than if they were always broken, because the parser that trusts the guarantee runs unprotected for months and then meets one argument object with a missing required field. The trace points at the parser. The cause is a boolean nobody wrote.</p>""",
"why": """<p><strong>The default is the unsafe half of the pair.</strong> <code>parallel_tool_calls</code> defaults to true. Strict schemas are opt-in and take deliberate work; the setting that voids them is on by default and takes none. A codebase that did the hard part correctly and skipped the easy part is the normal case here, not a careless one.</p>
<p><strong>A single call under the same configuration is not safe, it is lucky.</strong> The script reports those turns as at risk rather than as clean, because the configuration is loaded and simply did not fire. Counting them as passes is how a sample of a thousand responses with twelve fan-outs gets read as "99% fine". The right reading is that the guarantee is void on 1.2% of turns and the parser has no handling for any of them.</p>
<p><strong>Fan-out without strict schemas is a different note and a real problem anyway.</strong> If no tool declares <code>strict</code> at all then there was never a guarantee to void, and the fault is that the arguments were never validated in the first place &mdash; a separate failure with its own repair. The script names that state rather than folding it in, because telling someone to set <code>parallel_tool_calls: false</code> when they never had strict schemas fixes nothing.</p>
<p><strong>Duplicate calls to one tool are the second bug and they cost money rather than correctness.</strong> A turn that calls <code>create_ticket</code> twice will create two tickets, because the handler was written when a turn meant a call. It is not a schema problem and turning off parallel calls does fix it, but so does keying the handler on <code>call_id</code>, which is the change that survives someone turning parallel calls back on for latency next year.</p>
<p><strong>You cannot check this from the aggregate, and you cannot enumerate the sample either.</strong> No usage report counts tool calls, so there is no shape in the buckets to find. And <code>/v1/responses</code> has no list endpoint, so the ids have to come from your own log. Every rate this script prints is a rate over the sample you handed it, which makes the sampling strategy part of the finding: sample the turns your users actually send, not the ones your fixtures do.</p>""",
"steps": [
 {"h": "Sample stored responses from real traffic, not from tests",
  "body": """<p>The whole finding is a rate over turns that fan out, and fixtures do not fan out. Take ids from production logs across a full week. Responses must have been stored to be readable at all.</p>"""},
 {"h": "Read the request configuration back off each response",
  "body": """<p>The response object echoes <code>tools</code>, <code>tool_choice</code> and <code>parallel_tool_calls</code>. Collect the tools declaring <code>strict: true</code>, handling both shapes &mdash; top level on the Responses API, nested under <code>function</code> on Chat Completions &mdash; and treat an absent <code>parallel_tool_calls</code> as true, because that is what it is.</p>"""},
 {"h": "Count the function_call items in one turn",
  "body": """<p>More than one <code>function_call</code> item in a single <code>output[]</code> array is a fan-out. That, plus strict declared, plus parallel allowed, is the finding. One call under the same configuration is at risk and gets its own state.</p>"""},
 {"h": "Compute the rate, not just the list",
  "body": """<p>Fan-outs divided by turns that were at risk. That number is what makes this actionable: 0.4% and 22% get the same repair and deserve very different urgency, and neither is visible from a list of four incident ids.</p>"""},
 {"h": "Print the boolean first and the idempotency second",
  "body": """<p><code>parallel_tool_calls: false</code> restores the guarantee. If you need the fan-out for latency, drop <code>strict</code> and validate the arguments yourself rather than believing a promise that is not being kept. Either way, key every handler on <code>call_id</code> so a duplicate call cannot double-apply.</p>"""},
],
"verify": """<p>Re-run on a fresh week after the flag ships. The at-risk count should go to zero and the serialised count should replace it; any remaining fan-out means one client or one code path was missed.</p>
<pre><code class="language-bash">python3 openai_parallel_strict_calls.py --responses ids.txt
# strict-void        resp_0f21a  3 function_call item(s) in one turn with strict declared and parallel_tool_calls left on
#   calls: lookup_order, create_ticket, create_ticket
#   duplicate: create_ticket called 2 time(s) in one turn; handlers keyed on the tool name will double apply
#   repair: set parallel_tool_calls false whenever strict schemas matter.
# exposure: 12 of 1000 at-risk turn(s) fanned out (1.2%), covering 27 argument object(s) with no guarantee
# 1000 response(s) read, 12 finding(s)</code></pre>""",
"code_intro": "One GET per response id, and the unit of analysis is a single turn rather than a corpus &mdash; which is what keeps this apart from the coverage note that reads the same endpoint. Nine pure functions: the id parser and path guard; the name reader for both tool shapes; the strict-tool set; the parallel-calls reader, which has to treat an absent field as true; the call extractor, which keeps <code>call_id</code> because the repair depends on it; the duplicate detector; the classifier; the exposure rate over at-risk turns; and the count of argument objects that came back with no guarantee behind them.",
"py_file": "openai_parallel_strict_calls.py",
"py": '''"""Find OpenAI turns where parallel tool calls voided a strict schema.

Read only. One GET per stored response id, using a project key. No completion
is created and nothing is written; /v1/responses is read, never posted to.

Structured Outputs is not supported alongside parallel function calls, and
parallel_tool_calls defaults to true. So a turn that returns more than one
function_call item while any tool declares strict: true came back without the
guarantee the parser is relying on, and it did so with an HTTP 200.

The repair is printed, never performed. One boolean is still a deploy.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_parallel_strict_calls")

API = "https://api.openai.com/v1"

CALL_TYPES = ("function_call", "custom_tool_call")

FINDINGS = ("strict-void",)


def _int(value):
    """Read a count as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_ids(text):
    """Response ids out of a plain text file. Pure. Order kept, duplicates dropped.

    Also the guard that stops an arbitrary line of a file becoming a URL path
    segment: anything that is not a plausible response id is discarded rather
    than interpolated into a provider URL.
    """
    out = []
    seen = set()
    for line in str(text or "").splitlines():
        candidate = line.split("#", 1)[0].strip()
        if not candidate or not candidate.startswith("resp_"):
            continue
        if not all(ch.isalnum() or ch in "_-" for ch in candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append(candidate)
    return out


def tool_name(tool):
    """The function name out of either tool shape. Pure. None when absent."""
    if not isinstance(tool, dict):
        return None
    name = tool.get("name")
    if not name and isinstance(tool.get("function"), dict):
        name = tool["function"].get("name")
    name = str(name or "").strip()
    return name or None


def declared_names(response):
    """Every named tool the request declared. Pure. Sorted."""
    out = set()
    for tool in (response or {}).get("tools") or []:
        name = tool_name(tool)
        if name:
            out.add(name)
    return sorted(out)


def strict_tools(response):
    """Tools declaring strict: true, in either shape. Pure. Sorted.

    strict false and strict absent are the same thing here and neither counts.
    A note about a voided guarantee has to be certain the guarantee was claimed.
    """
    out = set()
    for tool in (response or {}).get("tools") or []:
        if not isinstance(tool, dict):
            continue
        strict = tool.get("strict")
        if strict is not True and isinstance(tool.get("function"), dict):
            strict = tool["function"].get("strict")
        if strict is not True:
            continue
        name = tool_name(tool)
        if name:
            out.add(name)
    return sorted(out)


def parallel_allowed(response):
    """Could the model return more than one tool call in this turn? Pure.

    An absent parallel_tool_calls is true, and reading it as false is the exact
    mistake that makes this whole class of failure invisible.
    """
    value = (response or {}).get("parallel_tool_calls")
    return value is not False


def function_calls(response):
    """The tool calls in one turn, in order. Pure.

    call_id is kept because half the repair depends on it: a handler keyed on
    call_id cannot double-apply when the same tool is called twice.
    """
    out = []
    for item in (response or {}).get("output") or []:
        if not isinstance(item, dict) or item.get("type") not in CALL_TYPES:
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        out.append({"name": name, "call_id": str(item.get("call_id") or "")})
    return out


def duplicate_names(calls):
    """Tool names called more than once in one turn. Pure.

    A separate fault with the same trigger. It costs side effects rather than
    correctness, and turning parallel calls off is not the only fix for it.
    """
    counts = {}
    for call in calls or []:
        name = str((call or {}).get("name") or "")
        if name:
            counts[name] = counts.get(name, 0) + 1
    return {name: n for name, n in counts.items() if n > 1}


def classify(response):
    """Classify one turn. Pure. Returns (state, detail).

    The unit is the turn and not the corpus, because the guarantee is voided or
    kept per response and a rate computed over anything else means nothing.
    """
    declared = declared_names(response)
    if not declared:
        return ("no-tools", "no named tools declared in this turn")

    strict = strict_tools(response)
    calls = function_calls(response)
    parallel = parallel_allowed(response)
    names = ", ".join(c["name"] for c in calls) or "none"

    if not strict:
        if len(calls) > 1:
            return ("fanout-no-strict",
                    "%d function_call item(s) in one turn (%s) and no tool "
                    "declares strict. There was no guarantee to void here: the "
                    "arguments were never validated by the API at all, which "
                    "is a different fault with a different repair."
                    % (len(calls), names))
        return ("no-strict-declared",
                "%d tool(s) declared, none of them strict. Nothing in this turn "
                "was schema-guaranteed." % len(declared))

    if not parallel:
        return ("strict-serialised",
                "strict declared on %d tool(s) and parallel_tool_calls is "
                "false. The guarantee holds." % len(strict))

    if len(calls) > 1:
        return ("strict-void",
                "%d function_call item(s) in one turn with strict declared and "
                "parallel_tool_calls left on (%s). Structured Outputs is not "
                "supported alongside parallel calls, so these argument objects "
                "carry no schema guarantee." % (len(calls), names))

    return ("strict-at-risk",
            "strict declared on %d tool(s) with parallel_tool_calls left on, "
            "and this turn happened to return %d call(s). The configuration is "
            "loaded; it did not fire here." % (len(strict), len(calls)))


def exposure(states):
    """How often the fan-out that voids the guarantee actually happens. Pure.

    The denominator is turns that were at risk, never all turns: a rate over
    responses that declared no strict tools flatters the number by however much
    unrelated traffic happened to be in the sample. None when nothing was at
    risk, because a rate over an empty denominator invents a number.
    """
    at_risk = sum(1 for s in states or [] if s in ("strict-void", "strict-at-risk"))
    void = sum(1 for s in states or [] if s == "strict-void")
    if at_risk <= 0:
        return {"at_risk": 0, "void": void, "rate": None}
    return {"at_risk": at_risk, "void": void, "rate": void / float(at_risk)}


def unvalidated_calls(rows):
    """Argument objects that came back with no guarantee behind them. Pure.

    Counted only in the turns where the guarantee was actually void. The number
    the parser cares about is objects, not turns.
    """
    return sum(_int(row.get("calls")) for row in rows or []
               if row.get("state") == "strict-void")


def repair_lines(state):
    """The repair for one classified turn. Pure."""
    if state == "strict-void":
        return [
            "set parallel_tool_calls false whenever strict schemas matter. It "
            "defaults to true, which is why this was never a decision anyone "
            "made.",
            "if you need the fan-out for latency, drop strict and validate the "
            "arguments yourself. Do not keep a guarantee you know is not held.",
            "key every tool handler on call_id and make it idempotent, so a "
            "duplicate parallel call cannot double-apply.",
        ]
    if state == "strict-at-risk":
        return [
            "this turn was fine and the configuration is not. The same request "
            "shape returns several calls whenever the model decides to, so set "
            "parallel_tool_calls false before it does.",
        ]
    if state == "fanout-no-strict":
        return [
            "no schema guarantee was in place to lose. Validate tool arguments "
            "in your own handler, or declare strict and serialise the calls.",
        ]
    return []


def get(session, path):
    r = session.get(API + path, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: OPENAI_API_KEY needs read access to "
                         "stored responses in this project" % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--responses", metavar="FILE",
                    help="a text file of stored response ids, one per line")
    ap.add_argument("--response-id", action="append", default=[],
                    help="a single response id; repeatable")
    ap.add_argument("--show-all", action="store_true",
                    help="also print turns that are correctly configured")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key that can read stored "
                  "responses")
        return 2

    ids = list(args.response_id)
    if args.responses:
        try:
            with open(args.responses, "r", encoding="utf-8") as fh:
                ids.extend(parse_ids(fh.read()))
        except OSError as exc:
            log.error("could not read %s: %s", args.responses, exc)
            return 2
    ids = parse_ids("\\n".join(ids))
    if not ids:
        log.error("no usable response ids. /v1/responses cannot be listed, so "
                  "the sample has to come from your own request log")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    rows = []
    bad = 0
    read = 0
    for response_id in ids:
        body = get(session, "/responses/" + response_id)
        if body is None:
            continue
        read += 1
        state, detail = classify(body)
        calls = function_calls(body)
        rows.append({"id": response_id, "state": state, "calls": len(calls)})

        line = "%-19s %-14s %s" % (state, response_id, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            log.warning("  calls: %s", ", ".join(c["name"] for c in calls))
        elif state == "fanout-no-strict":
            log.warning(line)
        elif args.show_all or state == "strict-at-risk":
            log.info(line)

        dupes = duplicate_names(calls)
        if dupes:
            log.warning("  duplicate: %s. Handlers keyed on the tool name "
                        "rather than call_id will double apply.",
                        "; ".join("%s called %d time(s) in one turn" % (n, c)
                                  for n, c in sorted(dupes.items())))

        if state in ("strict-void", "fanout-no-strict"):
            for repair in repair_lines(state):
                log.warning("  repair: %s", repair)

    shape = exposure([r["state"] for r in rows])
    if shape["rate"] is None:
        log.info("no turn in this sample declared a strict tool with parallel "
                 "calls left on, so there is no exposure to report")
    else:
        log.info("exposure: %d of %d at-risk turn(s) fanned out (%.1f%%), "
                 "covering %d argument object(s) with no guarantee",
                 shape["void"], shape["at_risk"], shape["rate"] * 100,
                 unvalidated_calls(rows))
        if shape["void"] == 0:
            log.warning("  every at-risk turn happened to return one call. That "
                        "is luck, not configuration: set parallel_tool_calls "
                        "false before it stops being lucky.")

    log.info("%d response(s) read, %d finding(s)", read, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-parallel-strict-calls.mjs",
"js": '''/**
 * Find OpenAI turns where parallel tool calls voided a strict schema.
 *
 * Read only. One GET per stored response id, using a project key. No
 * completion is created: /v1/responses is read, never posted to.
 *
 * Structured Outputs is not supported alongside parallel function calls, and
 * parallel_tool_calls defaults to true. A turn returning more than one
 * function_call item while any tool declares strict came back without the
 * guarantee the parser relies on, and it did so with an HTTP 200.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

const CALL_TYPES = new Set(['function_call', 'custom_tool_call']);

const FINDINGS = new Set(['strict-void']);

/** Read a count as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Response ids out of a plain text file. Pure. Order kept, duplicates dropped.
 * Also the guard that stops an arbitrary line becoming a URL path segment.
 */
export function parseIds(text) {
  const out = [];
  const seen = new Set();
  for (const line of String(text ?? '').split('\\n')) {
    const candidate = line.split('#')[0].trim();
    if (!candidate || !candidate.startsWith('resp_')) continue;
    if (!/^[A-Za-z0-9_-]+$/.test(candidate)) continue;
    if (seen.has(candidate)) continue;
    seen.add(candidate);
    out.push(candidate);
  }
  return out;
}

/** The function name out of either tool shape. Pure. Null when absent. */
export function toolName(tool) {
  if (!tool || typeof tool !== 'object') return null;
  let name = tool.name;
  if (!name && tool.function && typeof tool.function === 'object') {
    name = tool.function.name;
  }
  const text = String(name ?? '').trim();
  return text || null;
}

/** Every named tool the request declared. Pure. Sorted. */
export function declaredNames(response) {
  const out = new Set();
  for (const tool of response?.tools ?? []) {
    const name = toolName(tool);
    if (name) out.add(name);
  }
  return [...out].sort();
}

/**
 * Tools declaring strict true, in either shape. Pure. Sorted.
 * strict false and strict absent are the same thing here and neither counts.
 */
export function strictTools(response) {
  const out = new Set();
  for (const tool of response?.tools ?? []) {
    if (!tool || typeof tool !== 'object') continue;
    let strict = tool.strict;
    if (strict !== true && tool.function && typeof tool.function === 'object') {
      strict = tool.function.strict;
    }
    if (strict !== true) continue;
    const name = toolName(tool);
    if (name) out.add(name);
  }
  return [...out].sort();
}

/**
 * Could the model return more than one tool call in this turn? Pure.
 * An absent parallel_tool_calls is true, and reading it as false is the exact
 * mistake that makes this whole class of failure invisible.
 */
export function parallelAllowed(response) {
  return response?.parallel_tool_calls !== false;
}

/** The tool calls in one turn, in order. Pure. call_id is kept deliberately. */
export function functionCalls(response) {
  const out = [];
  for (const item of response?.output ?? []) {
    if (!item || typeof item !== 'object' || !CALL_TYPES.has(item.type)) continue;
    const name = String(item.name ?? '').trim();
    if (!name) continue;
    out.push({ name, callId: String(item.call_id ?? '') });
  }
  return out;
}

/** Tool names called more than once in one turn. Pure. */
export function duplicateNames(calls) {
  const counts = {};
  for (const call of calls ?? []) {
    const name = String(call?.name ?? '');
    if (name) counts[name] = (counts[name] ?? 0) + 1;
  }
  return Object.fromEntries(Object.entries(counts).filter(([, n]) => n > 1));
}

/** Classify one turn. Pure. Returns [state, detail]. The unit is the turn. */
export function classify(response) {
  const declared = declaredNames(response);
  if (declared.length === 0) return ['no-tools', 'no named tools declared in this turn'];

  const strict = strictTools(response);
  const calls = functionCalls(response);
  const parallel = parallelAllowed(response);
  const names = calls.map((c) => c.name).join(', ') || 'none';

  if (strict.length === 0) {
    if (calls.length > 1) {
      return ['fanout-no-strict',
        `${calls.length} function_call item(s) in one turn (${names}) and no ` +
        'tool declares strict. There was no guarantee to void here: the ' +
        'arguments were never validated by the API at all, which is a ' +
        'different fault with a different repair.'];
    }
    return ['no-strict-declared',
      `${declared.length} tool(s) declared, none of them strict. Nothing in ` +
      'this turn was schema-guaranteed.'];
  }

  if (!parallel) {
    return ['strict-serialised',
      `strict declared on ${strict.length} tool(s) and parallel_tool_calls is ` +
      'false. The guarantee holds.'];
  }

  if (calls.length > 1) {
    return ['strict-void',
      `${calls.length} function_call item(s) in one turn with strict declared ` +
      `and parallel_tool_calls left on (${names}). Structured Outputs is not ` +
      'supported alongside parallel calls, so these argument objects carry no ' +
      'schema guarantee.'];
  }

  return ['strict-at-risk',
    `strict declared on ${strict.length} tool(s) with parallel_tool_calls left ` +
    `on, and this turn happened to return ${calls.length} call(s). The ` +
    'configuration is loaded; it did not fire here.'];
}

/**
 * How often the fan-out that voids the guarantee actually happens. Pure.
 * The denominator is turns that were at risk, never all turns, and it is null
 * when nothing was at risk rather than a number invented over zero.
 */
export function exposure(states) {
  const list = states ?? [];
  const atRisk = list.filter((s) => s === 'strict-void' || s === 'strict-at-risk').length;
  const voided = list.filter((s) => s === 'strict-void').length;
  if (atRisk <= 0) return { atRisk: 0, void: voided, rate: null };
  return { atRisk, void: voided, rate: voided / atRisk };
}

/** Argument objects that came back with no guarantee behind them. Pure. */
export function unvalidatedCalls(rows) {
  let total = 0;
  for (const row of rows ?? []) {
    if (row?.state === 'strict-void') total += readInt(row?.calls);
  }
  return total;
}

/** The repair for one classified turn. Pure. */
export function repairLines(state) {
  if (state === 'strict-void') {
    return [
      'set parallel_tool_calls false whenever strict schemas matter. It ' +
      'defaults to true, which is why this was never a decision anyone made.',
      'if you need the fan-out for latency, drop strict and validate the ' +
      'arguments yourself. Do not keep a guarantee you know is not held.',
      'key every tool handler on call_id and make it idempotent, so a ' +
      'duplicate parallel call cannot double-apply.',
    ];
  }
  if (state === 'strict-at-risk') {
    return ['this turn was fine and the configuration is not. The same request ' +
            'shape returns several calls whenever the model decides to, so set ' +
            'parallel_tool_calls false before it does.'];
  }
  if (state === 'fanout-no-strict') {
    return ['no schema guarantee was in place to lose. Validate tool arguments ' +
            'in your own handler, or declare strict and serialise the calls.'];
  }
  return [];
}

async function get(key, path) {
  const res = await fetch(API + path, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: OPENAI_API_KEY needs read ` +
                    'access to stored responses in this project');
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key that can read stored responses');
    process.exitCode = 2;
    return;
  }
  const file = process.argv.slice(2).find((a) => !a.startsWith('--'));
  if (!file) {
    console.error('pass a text file of stored response ids, one per line');
    process.exitCode = 2;
    return;
  }
  const showAll = process.env.SHOW_ALL === '1';

  const ids = parseIds(await readFile(file, 'utf8'));
  if (ids.length === 0) {
    console.error('no usable response ids. /v1/responses cannot be listed, so ' +
                  'the sample has to come from your own request log');
    process.exitCode = 2;
    return;
  }

  const rows = [];
  let bad = 0;
  let read = 0;
  for (const id of ids) {
    const body = await get(key, `/responses/${id}`);
    if (body === null) continue;
    read += 1;
    const [state, detail] = classify(body);
    const calls = functionCalls(body);
    rows.push({ id, state, calls: calls.length });

    const line = `${state.padEnd(19)} ${id.padEnd(14)} ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      console.warn(`  calls: ${calls.map((c) => c.name).join(', ')}`);
    } else if (state === 'fanout-no-strict') {
      console.warn(line);
    } else if (showAll || state === 'strict-at-risk') {
      console.log(line);
    }

    const dupes = duplicateNames(calls);
    if (Object.keys(dupes).length > 0) {
      console.warn(`  duplicate: ${Object.entries(dupes).sort()
        .map(([n, c]) => `${n} called ${c} time(s) in one turn`).join('; ')}. ` +
        'Handlers keyed on the tool name rather than call_id will double apply.');
    }

    if (state === 'strict-void' || state === 'fanout-no-strict') {
      for (const repair of repairLines(state)) console.warn(`  repair: ${repair}`);
    }
  }

  const shape = exposure(rows.map((r) => r.state));
  if (shape.rate === null) {
    console.log('no turn in this sample declared a strict tool with parallel ' +
                'calls left on, so there is no exposure to report');
  } else {
    console.log(`exposure: ${shape.void} of ${shape.atRisk} at-risk turn(s) ` +
                `fanned out (${(shape.rate * 100).toFixed(1)}%), covering ` +
                `${unvalidatedCalls(rows)} argument object(s) with no guarantee`);
    if (shape.void === 0) {
      console.warn('  every at-risk turn happened to return one call. That is ' +
                   'luck, not configuration: set parallel_tool_calls false ' +
                   'before it stops being lucky.');
    }
  }

  console.log(`${read} response(s) read, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is a pair of turns that came out of the same client with the same configuration: one returned a single tool call and one returned three, and the classifier has to call the second void and the first <em>at risk</em> rather than clean. The exposure test then puts a number on that pair &mdash; twelve fan-outs in a thousand at-risk turns is 1.2%, and the denominator deliberately excludes every turn that never declared a strict tool, because including them flatters the rate by however much unrelated traffic was in the sample. The rest pin the absent <code>parallel_tool_calls</code> that must read as true, the nested and flat <code>strict</code> shapes, the duplicate call that keeps both <code>call_id</code> values because the repair depends on them, and the fan-out with no strict tools anywhere, which is a different fault and must not be handed the same advice.",
"test_py_file": "test_openai_parallel_strict_calls.py",
"test_py": '''from openai_parallel_strict_calls import (classify, duplicate_names,
                                          exposure, function_calls,
                                          parallel_allowed, parse_ids,
                                          repair_lines, strict_tools,
                                          unvalidated_calls)

STRICT_TOOLS = [
    {"type": "function", "name": "lookup_order", "strict": True},
    {"type": "function", "name": "create_ticket", "strict": True},
]


def turn(calls, tools=None, parallel=None):
    body = {"tools": tools if tools is not None else STRICT_TOOLS,
            "output": [{"type": "function_call", "name": n,
                        "call_id": "call_%d" % i}
                       for i, n in enumerate(calls)]}
    if parallel is not None:
        body["parallel_tool_calls"] = parallel
    return body


def test_a_turn_that_fans_out_under_strict_schemas_has_no_guarantee():
    # The note in one assertion. Three calls, strict declared, and
    # parallel_tool_calls never set, which means true.
    body = turn(["lookup_order", "create_ticket", "create_ticket"])
    assert parallel_allowed(body) is True
    assert strict_tools(body) == ["create_ticket", "lookup_order"]
    assert len(function_calls(body)) == 3

    state, detail = classify(body)
    assert state == "strict-void"
    assert "3 function_call item(s) in one turn" in detail
    assert "carry no schema guarantee" in detail
    assert "parallel_tool_calls false" in repair_lines(state)[0]


def test_the_same_configuration_returning_one_call_is_at_risk_not_clean():
    # The pair. Identical request, one call instead of three, and calling this
    # a pass is how a thousand responses with twelve fan-outs read as fine.
    state, detail = classify(turn(["lookup_order"]))
    assert state == "strict-at-risk"
    assert "The configuration is loaded; it did not fire here." in detail

    states = ["strict-void"] * 12 + ["strict-at-risk"] * 988
    # And 400 unrelated turns that never claimed a guarantee, which must not
    # dilute the denominator.
    states += ["no-strict-declared"] * 400
    shape = exposure(states)
    assert shape["at_risk"] == 1000 and shape["void"] == 12
    assert round(shape["rate"], 4) == 0.012

    rows = [{"state": "strict-void", "calls": 3} for _ in range(9)]
    rows += [{"state": "strict-at-risk", "calls": 1} for _ in range(988)]
    assert unvalidated_calls(rows) == 27


def test_turning_parallel_calls_off_restores_the_guarantee():
    state, detail = classify(turn(["lookup_order"], parallel=False))
    assert state == "strict-serialised"
    assert "The guarantee holds." in detail
    assert parallel_allowed({"parallel_tool_calls": False}) is False
    assert parallel_allowed({"parallel_tool_calls": True}) is True
    assert parallel_allowed({}) is True
    assert exposure(["strict-serialised"] * 40)["rate"] is None


def test_the_same_tool_called_twice_keeps_both_call_ids():
    calls = function_calls(turn(["create_ticket", "create_ticket"]))
    assert duplicate_names(calls) == {"create_ticket": 2}
    assert [c["call_id"] for c in calls] == ["call_0", "call_1"]
    assert duplicate_names([{"name": "a"}, {"name": "b"}]) == {}
    assert duplicate_names(None) == {}


def test_a_fan_out_with_no_strict_tools_is_a_different_fault():
    loose = [{"type": "function", "name": "lookup_order"},
             {"type": "function", "name": "create_ticket", "strict": False}]
    state, detail = classify(turn(["lookup_order", "create_ticket"], tools=loose))
    assert state == "fanout-no-strict"
    assert "no tool declares strict" in detail
    assert "different fault" in detail
    assert "Validate tool arguments" in repair_lines(state)[0]
    assert classify(turn([], tools=loose))[0] == "no-strict-declared"
    assert strict_tools({"tools": loose}) == []


def test_strict_is_read_in_both_tool_shapes():
    nested = [{"type": "function",
               "function": {"name": "run_refund", "strict": True}}]
    assert strict_tools({"tools": nested}) == ["run_refund"]
    state, _ = classify({"tools": nested,
                         "output": [{"type": "function_call", "name": "run_refund",
                                     "call_id": "c1"},
                                    {"type": "function_call", "name": "run_refund",
                                     "call_id": "c2"}]})
    assert state == "strict-void"


def test_turns_without_tools_and_junk_do_not_become_findings():
    assert classify({})[0] == "no-tools"
    assert classify(None)[0] == "no-tools"
    assert classify({"tools": [], "output": []})[0] == "no-tools"
    # A message item is not a tool call.
    body = turn([])
    body["output"] = [{"type": "message", "content": []}, None, "nonsense"]
    assert function_calls(body) == []
    assert classify(body)[0] == "strict-at-risk"
    assert unvalidated_calls(None) == 0


def test_response_ids_are_validated_before_they_reach_a_url():
    text = "resp_abc123\\n# note\\n\\nresp_abc123\\nresp_def456\\n../../etc\\n"
    assert parse_ids(text) == ["resp_abc123", "resp_def456"]
    assert parse_ids("resp_bad/../x") == []
    assert parse_ids(None) == []
''',
"test_js_file": "openai-parallel-strict-calls.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, duplicateNames, exposure, functionCalls, parallelAllowed,
         parseIds, repairLines, strictTools, unvalidatedCalls }
  from './openai-parallel-strict-calls.mjs';

const STRICT_TOOLS = [
  { type: 'function', name: 'lookup_order', strict: true },
  { type: 'function', name: 'create_ticket', strict: true },
];

const turn = (calls, tools, parallel) => {
  const body = {
    tools: tools ?? STRICT_TOOLS,
    output: calls.map((name, i) => ({ type: 'function_call', name,
                                      call_id: `call_${i}` })),
  };
  if (parallel !== undefined) body.parallel_tool_calls = parallel;
  return body;
};

test('a turn that fans out under strict schemas has no guarantee', () => {
  const body = turn(['lookup_order', 'create_ticket', 'create_ticket']);
  assert.equal(parallelAllowed(body), true);
  assert.deepEqual(strictTools(body), ['create_ticket', 'lookup_order']);
  assert.equal(functionCalls(body).length, 3);

  const [state, detail] = classify(body);
  assert.equal(state, 'strict-void');
  assert.match(detail, /3 function_call item/);
  assert.match(detail, /carry no schema guarantee/);
  assert.match(repairLines(state)[0], /parallel_tool_calls false/);
});

test('the same configuration returning one call is at risk not clean', () => {
  const [state, detail] = classify(turn(['lookup_order']));
  assert.equal(state, 'strict-at-risk');
  assert.match(detail, /did not fire here/);

  const states = [
    ...Array.from({ length: 12 }, () => 'strict-void'),
    ...Array.from({ length: 988 }, () => 'strict-at-risk'),
    ...Array.from({ length: 400 }, () => 'no-strict-declared'),
  ];
  const shape = exposure(states);
  assert.equal(shape.atRisk, 1000);
  assert.equal(shape.void, 12);
  assert.equal(Number(shape.rate.toFixed(4)), 0.012);

  const rows = [
    ...Array.from({ length: 9 }, () => ({ state: 'strict-void', calls: 3 })),
    ...Array.from({ length: 988 }, () => ({ state: 'strict-at-risk', calls: 1 })),
  ];
  assert.equal(unvalidatedCalls(rows), 27);
});

test('turning parallel calls off restores the guarantee', () => {
  const [state, detail] = classify(turn(['lookup_order'], undefined, false));
  assert.equal(state, 'strict-serialised');
  assert.match(detail, /The guarantee holds/);
  assert.equal(parallelAllowed({ parallel_tool_calls: false }), false);
  assert.equal(parallelAllowed({ parallel_tool_calls: true }), true);
  assert.equal(parallelAllowed({}), true);
  assert.equal(exposure(Array.from({ length: 40 }, () => 'strict-serialised')).rate,
               null);
});

test('the same tool called twice keeps both call ids', () => {
  const calls = functionCalls(turn(['create_ticket', 'create_ticket']));
  assert.deepEqual(duplicateNames(calls), { create_ticket: 2 });
  assert.deepEqual(calls.map((c) => c.callId), ['call_0', 'call_1']);
  assert.deepEqual(duplicateNames([{ name: 'a' }, { name: 'b' }]), {});
  assert.deepEqual(duplicateNames(null), {});
});

test('a fan out with no strict tools is a different fault', () => {
  const loose = [{ type: 'function', name: 'lookup_order' },
                 { type: 'function', name: 'create_ticket', strict: false }];
  const [state, detail] = classify(turn(['lookup_order', 'create_ticket'], loose));
  assert.equal(state, 'fanout-no-strict');
  assert.match(detail, /no tool declares strict/);
  assert.match(detail, /different fault/);
  assert.match(repairLines(state)[0], /Validate tool arguments/);
  assert.equal(classify(turn([], loose))[0], 'no-strict-declared');
  assert.deepEqual(strictTools({ tools: loose }), []);
});

test('strict is read in both tool shapes', () => {
  const nested = [{ type: 'function',
                    function: { name: 'run_refund', strict: true } }];
  assert.deepEqual(strictTools({ tools: nested }), ['run_refund']);
  const [state] = classify({
    tools: nested,
    output: [{ type: 'function_call', name: 'run_refund', call_id: 'c1' },
             { type: 'function_call', name: 'run_refund', call_id: 'c2' }],
  });
  assert.equal(state, 'strict-void');
});

test('turns without tools and junk do not become findings', () => {
  assert.equal(classify({})[0], 'no-tools');
  assert.equal(classify(null)[0], 'no-tools');
  assert.equal(classify({ tools: [], output: [] })[0], 'no-tools');
  const body = turn([]);
  body.output = [{ type: 'message', content: [] }, null, 'nonsense'];
  assert.deepEqual(functionCalls(body), []);
  assert.equal(classify(body)[0], 'strict-at-risk');
  assert.equal(unvalidatedCalls(null), 0);
});

test('response ids are validated before they reach a url', () => {
  const text = 'resp_abc123\\n# note\\n\\nresp_abc123\\nresp_def456\\n../../etc\\n';
  assert.deepEqual(parseIds(text), ['resp_abc123', 'resp_def456']);
  assert.deepEqual(parseIds('resp_bad/../x'), []);
  assert.deepEqual(parseIds(null), []);
});
''',
"faq": [
 ("Is this a bug in the API?",
  "No, it is a documented interaction, which is precisely why it is dangerous. Structured Outputs is not supported alongside parallel function calls and the guidance is to set parallel_tool_calls to false when you depend on strict schemas. Nothing errors and nothing warns; the guarantee simply does not apply on the turns where the model fans out. The bug is in the code that assumed a default it never read."),
 ("Why is a turn with one tool call reported as at risk instead of fine?",
  "Because the configuration is what is broken, not the turn. The same request shape returns several calls whenever the model decides to, so a single-call turn is a turn that happened not to fan out. Reporting those as clean is how a sample of a thousand responses with twelve fan-outs gets summarised as ninety-nine percent healthy, which is the reading that keeps the boolean unset for another quarter."),
 ("Can I keep parallel calls and keep strict schemas?",
  "Not with the guarantee intact. If the fan-out matters for latency, the honest move is to drop strict and validate the arguments in your own handler, so the validation exists somewhere rather than being believed to exist in the API. Keeping strict declared while knowing it does not hold is the worst of the three options, because it is exactly what convinces the next person not to write a check."),
 ("What about the same tool being called twice in one turn?",
  "Separate fault, same trigger, and it costs side effects rather than correctness. A handler written when a turn meant a call will create two tickets or issue two refunds. Turning off parallel calls fixes it today; keying the handler on call_id and making it idempotent fixes it permanently, including for whoever turns parallel calls back on next year for latency."),
 ("Why can the script not just scan all my responses?",
  "There is no list endpoint. /v1/responses supports retrieval by id and nothing else, so the ids have to come from your own request log, and every rate the script prints is a rate over the sample you supplied. That makes sampling part of the method: take ids from real production traffic across a full week, because fixtures send the prompts that produce one call and that is the whole reason this survives testing."),
],
"related": [REL_DEAD_TOOL, REL_TOOL_TOKENS, REL_ZERO_OUTPUT],
"citations": [CITE_OAI_FUNCTION_CALLING, CITE_OAI_STRUCTURED, CITE_OAI_RESPONSES,
              CITE_MS_STRUCTURED],
},
{
"slug": "cache-invalidated-by-changing-prefix",
"title": "Cache written on every call by a prefix that keeps moving",
"description": "Writes in every minute, back to back, and reads at zero. A run longer than the TTL proves the entry was alive and never matched: the prefix changes.",
"h1": "Cache written on every call by a prefix that keeps moving",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["cache_creation ephemeral_5m_input_tokens every call",
             "cache_read_input_tokens zero", "prompt cache prefix invalidated",
             "timestamp in system prompt breaks cache",
             "unordered tool list cache miss"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin...) provisioned read-only. A workspace key is rejected by every /v1/organizations/ path.",
"lead": "Caching went in six weeks ago and the cached share never moved off zero. The obvious explanations were checked and cleared: the breakpoint is there, the prefix is long, the traffic is constant. What nobody looked at until somebody pulled the minute buckets is that the writes are not occasional. There is a write in every single minute of the window, one after another for four hours, and not one read anywhere in them. A five minute entry written at 14:03 was still alive at 14:07, and the call at 14:07 wrote a new one.",
"short_answer": """<p>Read the usage report at one-minute resolution and look at the <em>spacing</em>, not the totals. With an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-4h}&amp;bucket_width=1m&amp;limit=240&amp;group_by[]=api_key_id&amp;group_by[]=model</code>.</p>
<p>The finding is a run of <em>adjacent</em> minutes that each carry <code>cache_creation.ephemeral_5m_input_tokens</code> and none of which carry <code>cache_read_input_tokens</code>. A run of five or more is longer than the 5-minute TTL, so the entry written at the start of it was still alive at the end and was never matched. Nothing about warm-up or traffic rate explains that. Only a prefix that differs on every call does.</p>
<p>This is one of three notes that read the same two numbers, so the boundaries matter. If writes and reads are both zero, caching was never switched on and <a href="/llm/prompt-caching-never-used/">that note</a> owns it. If reads are present at all, entries <em>are</em> being matched and the question is whether they are matched often enough to pay for the premium, which is <a href="/llm/cache-writes-with-no-reads/">the write-to-read ratio note</a>. This one is the case where reads are absent and the writes are back to back.</p>
<p>The cause is a byte. The cache is a prefix match rendered <code>tools</code>, then <code>system</code>, then <code>messages</code>, so a <code>datetime.now()</code> in the system prompt, a tool list built from an unordered dict, a per-request id, or an option like <code>reasoning.effort</code> or <code>tool_choice</code> flipping per call invalidates everything after it.</p>""",
"problem": """<p>Prompt caching is not storage, it is a prefix match. The API hashes the request from the front and reuses the longest run of tokens that is byte-for-byte identical to something it has seen. Change one character anywhere before the breakpoint and there is no partial credit: the lookup misses, a fresh entry is written at <strong>1.25x</strong> base input for a 5-minute TTL or <strong>2x</strong> for an hour, and nothing anywhere reports a miss. A miss looks exactly like a first call, and every call is a first call.</p>
<p>So the integration pays a premium on every request for a feature that never returns anything, and the number on the dashboard &mdash; cached share, zero &mdash; is the same number a team gets when they have not switched caching on at all. The two are opposite problems: one is a discount not taken, the other is a surcharge being paid. They are indistinguishable from a total, and they are trivially distinguishable from the spacing.</p>""",
"why": """<p><strong>Adjacency is the evidence, and it is the only thing here that is not shared with the neighbouring notes.</strong> The totals cannot separate these cases: a key that writes sixty million tokens with no reads reads identically whether those writes arrived in one hundred and twenty consecutive minutes or in six minutes twenty minutes apart. The first is a prefix changing on every call. The second is traffic slower than the TTL, where each entry genuinely expires before the next call arrives, and the repair for that is a longer TTL or a faster arrival rate rather than a hunt through the prompt. The script builds both cases and refuses to call them the same thing.</p>
<p><strong>A run longer than the TTL is a proof rather than a heuristic.</strong> If minute one wrote a 5-minute entry and minutes two through five also wrote and never read, the entry from minute one was still live for all of them. Either the requests in those minutes were asking for a different prefix, or the cache is broken, and the second is not a hypothesis worth entertaining. On 1-hour writes the argument gets stronger and the premium doubles: the entry is alive for sixty minutes and every one of them wrote a new one.</p>
<p><strong>The invalidators are ordered, and knowing the order narrows the hunt.</strong> The prefix renders <code>tools</code>, then <code>system</code>, then <code>messages</code>. Changing a tool definition invalidates the tools, the system prompt and the messages behind them. Toggling web search, citations or <code>tool_choice</code>, or adding an image, invalidates progressively less. So if the cached share is total rather than partial, look at the tool block first &mdash; and <a href="/llm/tool-schemas-dominate-input-tokens/">measure what it weighs</a> while you are there, because it is both the first thing invalidated and usually the largest thing being rewritten.</p>
<p><strong>The honest limit is a key that serves more than one prefix.</strong> Grouped by <code>api_key_id</code>, a key that multiplexes many tenants with a per-tenant system prompt writes constantly and legitimately: every entry is a different prefix and every write is correct. This check cannot see inside that. Grouping by model as well narrows it, and the output says plainly that the finding is strongest on a key that serves one workload. A note that pretended otherwise would fire on the healthiest multi-tenant deployments in the estate.</p>
<p><strong>Anthropic's usage report has no request count, so none of this can be per-call.</strong> The report returns token sums per bucket and nothing else. Everything here is tokens and minutes, which is why the write share is computed against uncached input rather than against calls, and why the finding is a shape in time rather than a per-request diagnosis. Per-request cache diagnosis does exist, but it is a beta Messages feature needing a workspace key, not an Admin read.</p>""",
"steps": [
 {"h": "Pull minute buckets, not hourly ones",
  "body": """<p><code>bucket_width=1m</code> with <code>group_by[]=api_key_id</code> and <code>group_by[]=model</code>. Four hours is plenty, because the fault is per call and continuous. An hourly bucket destroys the only evidence this note has: it folds a hundred and twenty adjacent minutes and six isolated ones into the same row.</p>"""},
 {"h": "Rule out the two neighbouring findings first",
  "body": """<p>Writes and reads both zero is caching switched off. Reads present at all means entries are being matched and the question becomes the write-to-read ratio. Both have their own notes and their own repairs, and the script names them rather than absorbing them.</p>"""},
 {"h": "Check the write share of input before looking at spacing",
  "body": """<p><code>writes / (uncached_input_tokens + writes)</code> above about a half means most of what you send is being marked cacheable and re-marked every time. Below that, something is being cached but it is a minority of the prompt, which is a different and much smaller problem.</p>"""},
 {"h": "Find the longest run of adjacent writing minutes with no read",
  "body": """<p>Five or more is the finding, because five exceeds the 5-minute TTL. Report the run with its start and end minute so it can be lined up against a deploy. Isolated writing minutes separated by gaps longer than the TTL are the other story entirely.</p>"""},
 {"h": "Print the invalidator hunt in cache order",
  "body": """<p>Tools first, then the system prompt, then the messages. Timestamps, unsorted JSON keys, a conditionally appended tool, a per-request id, a per-user preamble, a toggled option. Move each one after the last <code>cache_control</code> breakpoint and re-read the same minute buckets.</p>"""},
],
"verify": """<p>Re-run the same window after the invalidator moves. What should change is the spacing before the totals: the runs break up first, and reads appear in the minutes that follow the first surviving write.</p>
<pre><code class="language-bash">python3 anthropic_cache_prefix_churn.py --minutes 240
# prefix-churn       apikey_01Ab / claude-opus-5  writes are 83% of input with reads at 0; longest run 120 adjacent minute(s) from 2026-08-31T10:04Z to 2026-08-31T12:03Z
#   the writes are 5 minute entries at 1.25x base input, so a run of 120 means every entry outlived four calls that never matched it
#   note: grouped by key and model. A key serving many tenants with a per tenant prefix writes constantly and correctly; this finding is strongest on a key with one workload.
#   repair: hunt the invalidator in cache order: tools, then system, then messages.
# 4 key/model series checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET and no second opinion needed, because the second opinion is in the spacing of the same read. Nine pure functions: the minute normaliser and the minute index, which make adjacency integer arithmetic rather than string comparison that gets 14:59 and 15:00 wrong; the row builder, which reaches into the nested <code>cache_creation</code> object; the write share; the run finder, which is the whole finding; the gap profile, which is the alternative explanation stated as a number; the totals; the TTL split, because an hour-long entry makes a run far more damning; and the classifier, whose first three branches exist only to hand the reader to a different note.",
"py_file": "anthropic_cache_prefix_churn.py",
"py": '''"""Find Anthropic keys whose cache is rewritten on every call and never read.

Read only. One GET against the Admin API, which needs an Admin API key
(sk-ant-admin...); a workspace key is rejected by every /v1/organizations/
path, and an Admin key can be provisioned read-only.

Totals cannot tell this apart from two neighbouring problems, so the evidence
is spacing. A run of adjacent one-minute buckets that each write a cache entry
and never read one is longer than the entry's own TTL, which means the entry
was alive and unmatched the whole time. Only a prefix that differs on every
call does that. Caching switched off, and caching that is read but not read
enough, are named and handed to their own notes.

The repair is printed, never performed. Moving a timestamp is a deploy.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_cache_prefix_churn")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# cache_creation is a nested object. A parser looking for a flat
# cache_creation_input_tokens sums zero and reports a key that writes on every
# call as one that never caches at all, which is the opposite finding.
CACHE_CREATION_FIELDS = ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens")

FINDINGS = ("prefix-churn",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def minute_key(stamp):
    """Normalise a timestamp to a UTC minute key. Pure. None if unreadable."""
    if isinstance(stamp, bool):
        return None
    if isinstance(stamp, (int, float)):
        try:
            when = dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
        return when.strftime("%Y-%m-%dT%H:%MZ")
    text = str(stamp or "").strip().replace(" ", "T")
    if len(text) < 16:
        return None
    head = text[:16]
    if head[4] != "-" or head[7] != "-" or head[10] != "T" or head[13] != ":":
        return None
    for part in (head[0:4], head[5:7], head[8:10], head[11:13], head[14:16]):
        if not part.isdigit():
            return None
    return head + "Z"


def minute_index(stamp):
    """Minutes since the epoch. Pure. None if unreadable.

    Adjacency is the entire finding, so it has to be arithmetic on integers.
    String comparison puts 14:59 and 15:00 two apart, which breaks every run
    that crosses an hour boundary and quietly halves the longest one.
    """
    key = minute_key(stamp)
    if key is None:
        return None
    try:
        when = dt.datetime(int(key[0:4]), int(key[5:7]), int(key[8:10]),
                           int(key[11:13]), int(key[14:16]), tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return int(when.timestamp()) // 60


def rows_by_key(buckets):
    """Per (api_key_id, model), one row per minute, sorted. Pure."""
    merged = {}
    for bucket in buckets or []:
        stamp = bucket.get("starting_at") or bucket.get("start_time")
        key = minute_key(stamp)
        index = minute_index(stamp)
        if key is None or index is None:
            continue
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            ident = (str(result.get("api_key_id") or "unknown"),
                     str(result.get("model") or "unknown"))
            creation = result.get("cache_creation") or {}
            row = merged.setdefault((ident, index),
                                    {"minute": key, "index": index, "uncached": 0,
                                     "write5m": 0, "write1h": 0, "reads": 0})
            row["uncached"] += _int(result.get("uncached_input_tokens"))
            row["write5m"] += _int(creation.get("ephemeral_5m_input_tokens"))
            row["write1h"] += _int(creation.get("ephemeral_1h_input_tokens"))
            row["reads"] += _int(result.get("cache_read_input_tokens"))
    out = {}
    for (ident, _index), row in merged.items():
        out.setdefault(ident, []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: r["index"])
    return out


def writes(row):
    """Cache creation tokens in one minute, both TTLs. Pure."""
    return _int((row or {}).get("write5m")) + _int((row or {}).get("write1h"))


def write_share(row):
    """Share of a minute's input that was written as a fresh cache entry. Pure.

    None when nothing was sent, which is a different state from zero: an idle
    minute must not be counted as a minute that cached nothing.
    """
    total = _int((row or {}).get("uncached")) + writes(row)
    if total <= 0:
        return None
    return writes(row) / float(total)


def totals(rows):
    """Sum a series, and count the minutes that carried any traffic. Pure."""
    out = {"uncached": 0, "write5m": 0, "write1h": 0, "reads": 0, "active": 0}
    for row in rows or []:
        out["uncached"] += _int(row.get("uncached"))
        out["write5m"] += _int(row.get("write5m"))
        out["write1h"] += _int(row.get("write1h"))
        out["reads"] += _int(row.get("reads"))
        if _int(row.get("uncached")) + writes(row) + _int(row.get("reads")) > 0:
            out["active"] += 1
    out["writes"] = out["write5m"] + out["write1h"]
    return out


def churn_runs(rows, share_floor=0.5, read_floor=0.01):
    """Maximal runs of adjacent minutes that wrote and never read. Pure.

    This is the finding and nothing else in the section computes it. A five
    minute entry written in the first minute of a run is still alive in the
    fifth, so a run that long with no read in it means the entry was live and
    unmatched throughout. Neither a cold start nor a TTL expiring between calls
    can produce that; a prefix that differs on every call is the only thing
    that can.
    """
    runs = []
    current = []
    for row in rows or []:
        made = writes(row)
        share = write_share(row)
        churning = (made > 0 and share is not None and share >= share_floor
                    and _int(row.get("reads")) <= made * read_floor)
        if not churning:
            if current:
                runs.append(current)
                current = []
            continue
        if current and _int(row.get("index")) == _int(current[-1].get("index")) + 1:
            current.append(row)
        else:
            if current:
                runs.append(current)
            current = [row]
    if current:
        runs.append(current)
    return runs


def gap_profile(rows):
    """Median gap in minutes between minutes that wrote. Pure. None under two.

    The alternative explanation, stated as a number. Traffic arriving less
    often than the TTL writes an entry that expires before anything can read
    it, and that is a different note with a different repair. Its signature is
    isolated writing minutes; churn's is adjacent ones.
    """
    indices = [_int(r.get("index")) for r in rows or [] if writes(r) > 0]
    indices.sort()
    if len(indices) < 2:
        return None
    gaps = sorted(indices[i + 1] - indices[i] for i in range(len(indices) - 1))
    middle = len(gaps) // 2
    if len(gaps) % 2:
        return float(gaps[middle])
    return (gaps[middle - 1] + gaps[middle]) / 2.0


def ttl_split(sums):
    """Which TTL the writes were bought at. Pure. Returns (state, detail).

    It changes how damning a run is and what it cost. A 5 minute entry has to
    be matched within five minutes and is billed at 1.25x base input; a 1 hour
    entry is alive for sixty and is billed at 2x, so an adjacent run against
    hour-long writes is both stronger evidence and twice the surcharge.
    """
    sums = sums or {}
    five = _int(sums.get("write5m"))
    hour = _int(sums.get("write1h"))
    if five + hour <= 0:
        return ("no-writes", "nothing was written to the cache in this window")
    if hour > five:
        return ("1h-dominant",
                "the writes are mostly 1 hour entries at 2x base input, so each "
                "one was alive for sixty minutes and never matched in any of them")
    if five > hour:
        return ("5m-dominant",
                "the writes are 5 minute entries at 1.25x base input, so any run "
                "longer than five minutes outlived calls that never matched it")
    return ("mixed", "the writes are split evenly between the 5 minute and 1 "
                     "hour TTLs")


def handoff(state):
    """Which note owns this shape, when it is not this one. Pure.

    Three findings read the same two numbers. Naming the other two in the
    output is the difference between a check that classifies and a check that
    claims everything it sees.
    """
    if state == "caching-off":
        return ("no writes and no reads anywhere: caching was never switched "
                "on for this key. Read the prompt-caching-never-used note; the "
                "loss there is a discount not taken rather than a surcharge "
                "paid.")
    if state == "cache-is-read":
        return ("entries are being matched, so the prefix is stable enough to "
                "hit. Whether it hits often enough to pay for the write "
                "premium is the write-to-read ratio, which is the "
                "cache-writes-with-no-reads note.")
    if state == "gap-driven-misses":
        return ("the writing minutes are isolated rather than adjacent, so each "
                "entry plausibly expired before the next call arrived. That is "
                "arrival rate against TTL, and it is the "
                "cache-writes-with-no-reads note rather than this one.")
    return ""


def classify(rows, min_run=5, share_floor=0.5, read_floor=0.01, min_active=10):
    """Classify one key and model series. Pure. Returns (state, detail).

    The first three branches exist to give the finding away. Only a series with
    writes, no reads, a majority write share and adjacent writing minutes
    belongs to this note.
    """
    sums = totals(rows)
    if sums["active"] < min_active:
        return ("too-little-traffic",
                "%d active minute(s), under the floor of %d. Nothing can be "
                "said about spacing with fewer." % (sums["active"], min_active))

    if sums["writes"] == 0 and sums["reads"] == 0:
        return ("caching-off",
                "%d uncached input token(s), no cache writes and no cache reads"
                % sums["uncached"])
    if sums["writes"] == 0:
        return ("reads-only",
                "%d cache read(s) and no writes in this window: the entries "
                "were written before it started" % sums["reads"])
    if sums["reads"] > sums["writes"] * read_floor:
        return ("cache-is-read",
                "%d cache read token(s) against %d written"
                % (sums["reads"], sums["writes"]))

    share = sums["writes"] / float(sums["uncached"] + sums["writes"])
    if share < share_floor:
        return ("small-cached-prefix",
                "writes are %.0f%% of input with reads at 0, under the floor of "
                "%.0f%%. Something is being cached and never matched, and it is "
                "a minority of the prompt rather than the prefix."
                % (share * 100, share_floor * 100))

    runs = churn_runs(rows, share_floor, read_floor)
    longest = max(runs, key=len) if runs else []
    if len(longest) >= min_run:
        return ("prefix-churn",
                "writes are %.0f%% of input with reads at 0; longest run %d "
                "adjacent minute(s) from %s to %s. The entry written at the "
                "start of that run was still alive at the end and was never "
                "matched, so the prefix differs on every call."
                % (share * 100, len(longest), longest[0]["minute"],
                   longest[-1]["minute"]))

    gap = gap_profile(rows)
    if gap is not None and gap > min_run:
        return ("gap-driven-misses",
                "writes are %.0f%% of input with reads at 0, and the writing "
                "minutes sit a median of %.0f minute(s) apart"
                % (share * 100, gap))

    return ("intermittent-misses",
            "writes are %.0f%% of input with reads at 0, and the longest run of "
            "adjacent writing minutes is %d, under the floor of %d. Suggestive "
            "and not conclusive: widen the window."
            % (share * 100, len(longest), min_run))


def repair_lines():
    """The invalidator hunt, in cache order. Pure."""
    return [
        "hunt the invalidator in cache order: tools, then system, then "
        "messages. A change to the tools invalidates all three.",
        "the usual suspects are a clock (datetime.now in a system prompt), a "
        "tool list built from an unordered dict, a per-request id, a per-user "
        "preamble placed before the breakpoint, and an option toggled per call "
        "such as tool_choice, citations, web search or reasoning effort.",
        "move each one strictly after the last cache_control breakpoint, then "
        "re-read these same minute buckets. The runs should break up before "
        "the totals move.",
    ]


def window_start(minutes):
    """Floor to the minute: starting_at has to sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    return (now - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/ needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def read_buckets(session, path, params):
    """Walk the paginated usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=int, default=240,
                    help="minutes of one-minute buckets to read (max 1440)")
    ap.add_argument("--min-run", type=int, default=5,
                    help="adjacent writing minutes with no read that make a "
                         "finding (default 5, the 5m TTL)")
    ap.add_argument("--share-floor", type=float, default=0.5,
                    help="write share of input above which the prefix, rather "
                         "than a fragment of it, is being rewritten")
    ap.add_argument("--show-all", action="store_true",
                    help="also print series that are behaving")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key "
                  "(sk-ant-admin...); a workspace key cannot read "
                  "/v1/organizations/")
        return 2

    minutes = max(30, min(int(args.minutes), 1440))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    buckets = read_buckets(session, "/organizations/usage_report/messages", {
        "starting_at": window_start(minutes),
        "bucket_width": "1m",
        "limit": minutes,
        "group_by[]": ["api_key_id", "model"],
    })

    series = rows_by_key(buckets)
    if not series:
        log.info("no messages usage in the last %d minute(s)", minutes)
        return 0

    checked = 0
    bad = 0
    for ident in sorted(series):
        rows = series[ident]
        state, detail = classify(rows, args.min_run, args.share_floor)
        checked += 1
        line = "%-20s %s / %s  %s" % (state, ident[0], ident[1], detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            _, ttl = ttl_split(totals(rows))
            log.warning("  %s", ttl)
            log.warning("  note: grouped by key and model. A key serving many "
                        "tenants with a per tenant prefix writes constantly and "
                        "correctly; this finding is strongest on a key with one "
                        "workload.")
            for repair in repair_lines():
                log.warning("  repair: %s", repair)
        else:
            note = handoff(state)
            if note:
                log.info(line)
                log.info("  %s", note)
            elif args.show_all or state == "intermittent-misses":
                log.info(line)

    log.info("%d key/model series checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-cache-prefix-churn.mjs",
"js": '''/**
 * Find Anthropic keys whose cache is rewritten on every call and never read.
 *
 * Read only. One GET against the Admin API, which needs an Admin API key
 * (sk-ant-admin...). A workspace key is rejected by /v1/organizations/.
 *
 * Totals cannot separate this from two neighbouring problems, so the evidence
 * is spacing: a run of adjacent one-minute buckets that each write and never
 * read is longer than the entry's TTL, so the entry was alive and unmatched.
 * Caching switched off, and caching read but not read enough, are named and
 * handed to their own notes.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const FINDINGS = new Set(['prefix-churn']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/** Normalise a timestamp to a UTC minute key. Pure. Null if unreadable. */
export function minuteKey(stamp) {
  if (typeof stamp === 'boolean') return null;
  if (typeof stamp === 'number' && Number.isFinite(stamp)) {
    const when = new Date(Math.trunc(stamp) * 1000);
    if (Number.isNaN(when.getTime())) return null;
    return `${when.toISOString().slice(0, 16)}Z`;
  }
  const text = String(stamp ?? '').trim().replace(' ', 'T');
  if (text.length < 16) return null;
  const head = text.slice(0, 16);
  if (!/^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}$/.test(head)) return null;
  return `${head}Z`;
}

/**
 * Minutes since the epoch. Pure. Null if unreadable.
 * Adjacency has to be integer arithmetic: string comparison puts 14:59 and
 * 15:00 two apart and quietly halves every run that crosses an hour.
 */
export function minuteIndex(stamp) {
  const key = minuteKey(stamp);
  if (key === null) return null;
  const when = Date.parse(`${key.slice(0, 16)}:00Z`);
  if (Number.isNaN(when)) return null;
  return Math.floor(when / 60000);
}

/** Per api_key_id and model, one row per minute, sorted. Pure. */
export function rowsByKey(buckets) {
  const merged = new Map();
  for (const bucket of buckets ?? []) {
    const stamp = bucket?.starting_at ?? bucket?.start_time;
    const key = minuteKey(stamp);
    const index = minuteIndex(stamp);
    if (key === null || index === null) continue;
    for (const result of bucket?.results ?? []) {
      if (!result || typeof result !== 'object') continue;
      const ident = `${result.api_key_id ?? 'unknown'}\\t${result.model ?? 'unknown'}`;
      const cell = `${ident}\\t${index}`;
      if (!merged.has(cell)) {
        merged.set(cell, { ident, minute: key, index, uncached: 0,
                           write5m: 0, write1h: 0, reads: 0 });
      }
      const row = merged.get(cell);
      const creation = result.cache_creation ?? {};
      row.uncached += readInt(result.uncached_input_tokens);
      row.write5m += readInt(creation.ephemeral_5m_input_tokens);
      row.write1h += readInt(creation.ephemeral_1h_input_tokens);
      row.reads += readInt(result.cache_read_input_tokens);
    }
  }
  const out = new Map();
  for (const row of merged.values()) {
    if (!out.has(row.ident)) out.set(row.ident, []);
    out.get(row.ident).push(row);
  }
  for (const rows of out.values()) rows.sort((a, b) => a.index - b.index);
  return out;
}

/** Cache creation tokens in one minute, both TTLs. Pure. */
export function writes(row) {
  return readInt(row?.write5m) + readInt(row?.write1h);
}

/** Share of a minute's input written as a fresh entry. Pure. Null when idle. */
export function writeShare(row) {
  const total = readInt(row?.uncached) + writes(row);
  if (total <= 0) return null;
  return writes(row) / total;
}

/** Sum a series, and count the minutes that carried any traffic. Pure. */
export function totals(rows) {
  const out = { uncached: 0, write5m: 0, write1h: 0, reads: 0, active: 0 };
  for (const row of rows ?? []) {
    out.uncached += readInt(row?.uncached);
    out.write5m += readInt(row?.write5m);
    out.write1h += readInt(row?.write1h);
    out.reads += readInt(row?.reads);
    if (readInt(row?.uncached) + writes(row) + readInt(row?.reads) > 0) out.active += 1;
  }
  out.writes = out.write5m + out.write1h;
  return out;
}

/**
 * Maximal runs of adjacent minutes that wrote and never read. Pure.
 * The finding. A 5 minute entry written at the start of a five minute run was
 * still alive at the end of it, so nothing but a moving prefix explains a run.
 */
export function churnRuns(rows, shareFloor = 0.5, readFloor = 0.01) {
  const runs = [];
  let current = [];
  for (const row of rows ?? []) {
    const made = writes(row);
    const share = writeShare(row);
    const churning = made > 0 && share !== null && share >= shareFloor
      && readInt(row?.reads) <= made * readFloor;
    if (!churning) {
      if (current.length > 0) { runs.push(current); current = []; }
      continue;
    }
    if (current.length > 0 && readInt(row?.index) === readInt(current[current.length - 1]?.index) + 1) {
      current.push(row);
    } else {
      if (current.length > 0) runs.push(current);
      current = [row];
    }
  }
  if (current.length > 0) runs.push(current);
  return runs;
}

/**
 * Median gap in minutes between minutes that wrote. Pure. Null under two.
 * The alternative explanation as a number: traffic slower than the TTL writes
 * isolated entries that expire before anything can read them.
 */
export function gapProfile(rows) {
  const indices = (rows ?? []).filter((r) => writes(r) > 0)
    .map((r) => readInt(r?.index)).sort((a, b) => a - b);
  if (indices.length < 2) return null;
  const gaps = [];
  for (let i = 0; i < indices.length - 1; i += 1) gaps.push(indices[i + 1] - indices[i]);
  gaps.sort((a, b) => a - b);
  const middle = Math.floor(gaps.length / 2);
  if (gaps.length % 2) return gaps[middle];
  return (gaps[middle - 1] + gaps[middle]) / 2;
}

/** Which TTL the writes were bought at. Pure. Returns [state, detail]. */
export function ttlSplit(sums) {
  const five = readInt(sums?.write5m);
  const hour = readInt(sums?.write1h);
  if (five + hour <= 0) {
    return ['no-writes', 'nothing was written to the cache in this window'];
  }
  if (hour > five) {
    return ['1h-dominant',
      'the writes are mostly 1 hour entries at 2x base input, so each one was ' +
      'alive for sixty minutes and never matched in any of them'];
  }
  if (five > hour) {
    return ['5m-dominant',
      'the writes are 5 minute entries at 1.25x base input, so any run longer ' +
      'than five minutes outlived calls that never matched it'];
  }
  return ['mixed', 'the writes are split evenly between the 5 minute and 1 hour TTLs'];
}

/** Which note owns this shape, when it is not this one. Pure. */
export function handoff(state) {
  if (state === 'caching-off') {
    return 'no writes and no reads anywhere: caching was never switched on for ' +
      'this key. Read the prompt-caching-never-used note; the loss there is a ' +
      'discount not taken rather than a surcharge paid.';
  }
  if (state === 'cache-is-read') {
    return 'entries are being matched, so the prefix is stable enough to hit. ' +
      'Whether it hits often enough to pay for the write premium is the ' +
      'write-to-read ratio, which is the cache-writes-with-no-reads note.';
  }
  if (state === 'gap-driven-misses') {
    return 'the writing minutes are isolated rather than adjacent, so each ' +
      'entry plausibly expired before the next call arrived. That is arrival ' +
      'rate against TTL, and it is the cache-writes-with-no-reads note rather ' +
      'than this one.';
  }
  return '';
}

/** Classify one key and model series. Pure. Returns [state, detail]. */
export function classify(rows, minRun = 5, shareFloor = 0.5, readFloor = 0.01,
                         minActive = 10) {
  const sums = totals(rows);
  if (sums.active < minActive) {
    return ['too-little-traffic',
      `${sums.active} active minute(s), under the floor of ${minActive}. ` +
      'Nothing can be said about spacing with fewer.'];
  }

  if (sums.writes === 0 && sums.reads === 0) {
    return ['caching-off',
      `${sums.uncached} uncached input token(s), no cache writes and no cache reads`];
  }
  if (sums.writes === 0) {
    return ['reads-only',
      `${sums.reads} cache read(s) and no writes in this window: the entries ` +
      'were written before it started'];
  }
  if (sums.reads > sums.writes * readFloor) {
    return ['cache-is-read',
      `${sums.reads} cache read token(s) against ${sums.writes} written`];
  }

  const share = sums.writes / (sums.uncached + sums.writes);
  if (share < shareFloor) {
    return ['small-cached-prefix',
      `writes are ${(share * 100).toFixed(0)}% of input with reads at 0, under ` +
      `the floor of ${(shareFloor * 100).toFixed(0)}%. Something is being ` +
      'cached and never matched, and it is a minority of the prompt rather ' +
      'than the prefix.'];
  }

  const runs = churnRuns(rows, shareFloor, readFloor);
  let longest = [];
  for (const run of runs) if (run.length > longest.length) longest = run;
  if (longest.length >= minRun) {
    return ['prefix-churn',
      `writes are ${(share * 100).toFixed(0)}% of input with reads at 0; ` +
      `longest run ${longest.length} adjacent minute(s) from ` +
      `${longest[0].minute} to ${longest[longest.length - 1].minute}. The ` +
      'entry written at the start of that run was still alive at the end and ' +
      'was never matched, so the prefix differs on every call.'];
  }

  const gap = gapProfile(rows);
  if (gap !== null && gap > minRun) {
    return ['gap-driven-misses',
      `writes are ${(share * 100).toFixed(0)}% of input with reads at 0, and ` +
      `the writing minutes sit a median of ${gap.toFixed(0)} minute(s) apart`];
  }

  return ['intermittent-misses',
    `writes are ${(share * 100).toFixed(0)}% of input with reads at 0, and the ` +
    `longest run of adjacent writing minutes is ${longest.length}, under the ` +
    `floor of ${minRun}. Suggestive and not conclusive: widen the window.`];
}

/** The invalidator hunt, in cache order. Pure. */
export function repairLines() {
  return [
    'hunt the invalidator in cache order: tools, then system, then messages. ' +
    'A change to the tools invalidates all three.',
    'the usual suspects are a clock (datetime.now in a system prompt), a tool ' +
    'list built from an unordered dict, a per-request id, a per-user preamble ' +
    'placed before the breakpoint, and an option toggled per call such as ' +
    'tool_choice, citations, web search or reasoning effort.',
    'move each one strictly after the last cache_control breakpoint, then ' +
    're-read these same minute buckets. The runs should break up before the ' +
    'totals move.',
  ];
}

function windowStart(minutes) {
  const now = new Date();
  now.setUTCSeconds(0, 0);
  return `${new Date(now.getTime() - minutes * 60000).toISOString().slice(0, 19)}Z`;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/ needs an ` +
                    'Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* readBuckets(key, path, params) {
  let query = { ...params };
  for (;;) {
    const page = await get(key, path, query);
    for (const bucket of page?.data ?? []) yield bucket;
    if (!page?.has_more || !page?.next_page) return;
    query = { ...params, page: page.next_page };
  }
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/');
    process.exitCode = 2;
    return;
  }
  const minutes = Math.max(30, Math.min(Number(process.env.MINUTES ?? 240), 1440));
  const minRun = Number(process.env.MIN_RUN ?? 5);
  const shareFloor = Number(process.env.SHARE_FLOOR ?? 0.5);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organizations/usage_report/messages', {
    starting_at: windowStart(minutes),
    bucket_width: '1m',
    limit: minutes,
    'group_by[]': ['api_key_id', 'model'],
  })) buckets.push(bucket);

  const series = rowsByKey(buckets);
  if (series.size === 0) {
    console.log(`no messages usage in the last ${minutes} minute(s)`);
    return;
  }

  let checked = 0;
  let bad = 0;
  for (const ident of [...series.keys()].sort()) {
    const rows = series.get(ident);
    const [state, detail] = classify(rows, minRun, shareFloor);
    checked += 1;
    const line = `${state.padEnd(20)} ${ident.replace('\\t', ' / ')}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      const [, ttl] = ttlSplit(totals(rows));
      console.warn(`  ${ttl}`);
      console.warn('  note: grouped by key and model. A key serving many tenants ' +
                   'with a per tenant prefix writes constantly and correctly; ' +
                   'this finding is strongest on a key with one workload.');
      for (const repair of repairLines()) console.warn(`  repair: ${repair}`);
    } else {
      const note = handoff(state);
      if (note) {
        console.log(line);
        console.log(`  ${note}`);
      } else if (showAll || state === 'intermittent-misses') {
        console.log(line);
      }
    }
  }

  console.log(`${checked} key/model series checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The whole note is one pair of fixtures, and the pair is the reason it exists as a separate note at all. Two series with <em>byte-identical totals</em> &mdash; sixty million write tokens, twelve million uncached, not one read &mdash; where the first writes in a hundred and twenty consecutive minutes and the second writes in six minutes spaced twenty apart. Every summed number an hourly report can produce is the same for both, and the first is a prefix changing on every call while the second is traffic slower than the TTL. The classifier has to separate them and hand the second one to a different note by name. Around that sit the two other handoffs, the write share that keeps a minority cached fragment out of the finding, and a run that crosses an hour boundary, which is the case a string comparison of timestamps silently breaks in half.",
"test_py_file": "test_anthropic_cache_prefix_churn.py",
"test_py": '''from anthropic_cache_prefix_churn import (churn_runs, classify, gap_profile,
                                         handoff, minute_index, minute_key,
                                         rows_by_key, totals, ttl_split,
                                         write_share, writes)

BASE = minute_index("2026-08-31T10:00Z")


def minute(offset, uncached=100_000, write5m=0, write1h=0, reads=0):
    index = BASE + offset
    hour, rest = divmod(offset, 60)
    return {"minute": "2026-08-31T%02d:%02dZ" % (10 + hour, rest), "index": index,
            "uncached": uncached, "write5m": write5m, "write1h": write1h,
            "reads": reads}


# Every call writes: a hundred and twenty adjacent minutes, never a read.
CHURN = [minute(i, write5m=500_000) for i in range(120)]
# Byte-identical totals, six writing minutes twenty apart. Traffic slower than
# the TTL, which is a different note.
SLOW = [minute(i, write5m=10_000_000 if i % 20 == 0 else 0) for i in range(120)]


def test_a_write_in_every_adjacent_minute_and_never_a_read():
    # The note in one assertion. The run is longer than the TTL, so the entry
    # written at 10:00 was alive at 10:04 and the call at 10:04 wrote another.
    sums = totals(CHURN)
    assert sums["writes"] == 60_000_000 and sums["uncached"] == 12_000_000
    assert sums["reads"] == 0 and sums["active"] == 120
    assert round(write_share(CHURN[0]), 4) == 0.8333

    runs = churn_runs(CHURN)
    assert len(runs) == 1 and len(runs[0]) == 120

    state, detail = classify(CHURN)
    assert state == "prefix-churn"
    assert "longest run 120 adjacent minute(s)" in detail
    assert "from 2026-08-31T10:00Z to 2026-08-31T11:59Z" in detail
    assert ttl_split(sums)[0] == "5m-dominant"


def test_identical_totals_spaced_out_are_a_different_note():
    # The pair. Same writes, same uncached input, same zero reads, and the
    # opposite conclusion. Nothing an hourly bucket can see separates these.
    assert totals(SLOW)["writes"] == totals(CHURN)["writes"]
    assert totals(SLOW)["uncached"] == totals(CHURN)["uncached"]
    assert totals(SLOW)["reads"] == totals(CHURN)["reads"] == 0

    assert max(len(r) for r in churn_runs(SLOW)) == 1
    assert gap_profile(SLOW) == 20.0
    assert gap_profile(CHURN) == 1.0

    state, detail = classify(SLOW)
    assert state == "gap-driven-misses"
    assert "median of 20 minute(s) apart" in detail
    assert "cache-writes-with-no-reads" in handoff(state)


def test_reads_anywhere_hand_the_finding_to_the_ratio_note():
    warm = [minute(i, write5m=500_000 if i == 0 else 0,
                   reads=400_000 if i else 0) for i in range(120)]
    state, detail = classify(warm)
    assert state == "cache-is-read"
    assert "against 500000 written" in detail
    assert "write-to-read ratio" in handoff(state)


def test_no_writes_and_no_reads_is_the_never_switched_on_note():
    off = [minute(i) for i in range(120)]
    state, detail = classify(off)
    assert state == "caching-off"
    assert "no cache writes and no cache reads" in detail
    assert "prompt-caching-never-used" in handoff(state)
    assert ttl_split(totals(off))[0] == "no-writes"
    reads_only = [minute(i, reads=400_000) for i in range(120)]
    assert classify(reads_only)[0] == "reads-only"


def test_a_minority_cached_fragment_is_not_the_prefix():
    small = [minute(i, uncached=900_000, write5m=100_000) for i in range(120)]
    state, detail = classify(small)
    assert state == "small-cached-prefix"
    assert "writes are 10% of input" in detail
    assert handoff(state) == ""


def test_an_hour_long_ttl_makes_the_same_run_worse():
    hourly = [minute(i, write1h=500_000) for i in range(120)]
    state, _ = classify(hourly)
    assert state == "prefix-churn"
    ttl_state, ttl_detail = ttl_split(totals(hourly))
    assert ttl_state == "1h-dominant"
    assert "2x base input" in ttl_detail
    assert ttl_split({"write5m": 10, "write1h": 10})[0] == "mixed"


def test_a_run_crossing_an_hour_boundary_is_not_broken_in_half():
    # 10:57 through 11:02. Comparing the minute strings puts 10:59 and 11:00
    # sixty apart and reports two runs of three.
    crossing = [minute(i, write5m=500_000) for i in range(57, 63)]
    assert [r["minute"] for r in crossing][:4] == [
        "2026-08-31T10:57Z", "2026-08-31T10:58Z", "2026-08-31T10:59Z",
        "2026-08-31T11:00Z"]
    runs = churn_runs(crossing)
    assert len(runs) == 1 and len(runs[0]) == 6
    assert minute_index("2026-08-31T11:00Z") - minute_index("2026-08-31T10:59Z") == 1


def test_the_nested_cache_creation_object_is_actually_read():
    buckets = [{"starting_at": "2026-08-31T10:0%dZ" % i,
                "results": [{"api_key_id": "apikey_01Ab", "model": "claude-opus-5",
                             "uncached_input_tokens": 100_000,
                             "cache_read_input_tokens": 0,
                             "cache_creation": {"ephemeral_5m_input_tokens": 500_000,
                                                "ephemeral_1h_input_tokens": 0}}]}
               for i in range(6)]
    series = rows_by_key(buckets)
    rows = series[("apikey_01Ab", "claude-opus-5")]
    assert len(rows) == 6
    assert writes(rows[0]) == 500_000
    assert [r["index"] for r in rows] == sorted(r["index"] for r in rows)
    state, _ = classify(rows, min_active=6)
    assert state == "prefix-churn"


def test_thin_and_unreadable_windows_produce_no_verdict():
    assert classify([minute(i, write5m=500_000) for i in range(4)])[0] == "too-little-traffic"
    assert classify([])[0] == "too-little-traffic"
    assert classify(None)[0] == "too-little-traffic"
    assert write_share({"uncached": 0, "write5m": 0, "write1h": 0}) is None
    assert gap_profile([]) is None
    assert minute_key("nonsense") is None
    assert minute_index(None) is None
    assert rows_by_key([{"starting_at": "bad", "results": []}]) == {}
''',
"test_js_file": "anthropic-cache-prefix-churn.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { churnRuns, classify, gapProfile, handoff, minuteIndex, minuteKey,
         rowsByKey, totals, ttlSplit, writeShare, writes }
  from './anthropic-cache-prefix-churn.mjs';

const BASE = minuteIndex('2026-08-31T10:00Z');

const minute = (offset, { uncached = 100000, write5m = 0, write1h = 0,
                          reads = 0 } = {}) => {
  const hour = Math.floor(offset / 60);
  const rest = offset % 60;
  const pad = (n) => String(n).padStart(2, '0');
  return { minute: `2026-08-31T${pad(10 + hour)}:${pad(rest)}Z`,
           index: BASE + offset, uncached, write5m, write1h, reads };
};

const CHURN = Array.from({ length: 120 }, (_, i) => minute(i, { write5m: 500000 }));
const SLOW = Array.from({ length: 120 },
  (_, i) => minute(i, { write5m: i % 20 === 0 ? 10000000 : 0 }));

test('a write in every adjacent minute and never a read', () => {
  const sums = totals(CHURN);
  assert.equal(sums.writes, 60000000);
  assert.equal(sums.uncached, 12000000);
  assert.equal(sums.reads, 0);
  assert.equal(sums.active, 120);
  assert.equal(Number(writeShare(CHURN[0]).toFixed(4)), 0.8333);

  const runs = churnRuns(CHURN);
  assert.equal(runs.length, 1);
  assert.equal(runs[0].length, 120);

  const [state, detail] = classify(CHURN);
  assert.equal(state, 'prefix-churn');
  assert.match(detail, /longest run 120 adjacent minute/);
  assert.match(detail, /from 2026-08-31T10:00Z to 2026-08-31T11:59Z/);
  assert.equal(ttlSplit(sums)[0], '5m-dominant');
});

test('identical totals spaced out are a different note', () => {
  assert.equal(totals(SLOW).writes, totals(CHURN).writes);
  assert.equal(totals(SLOW).uncached, totals(CHURN).uncached);
  assert.equal(totals(SLOW).reads, 0);
  assert.equal(totals(CHURN).reads, 0);

  assert.equal(Math.max(...churnRuns(SLOW).map((r) => r.length)), 1);
  assert.equal(gapProfile(SLOW), 20);
  assert.equal(gapProfile(CHURN), 1);

  const [state, detail] = classify(SLOW);
  assert.equal(state, 'gap-driven-misses');
  assert.match(detail, /median of 20 minute\\(s\\) apart/);
  assert.match(handoff(state), /cache-writes-with-no-reads/);
});

test('reads anywhere hand the finding to the ratio note', () => {
  const warm = Array.from({ length: 120 }, (_, i) => minute(i, {
    write5m: i === 0 ? 500000 : 0, reads: i ? 400000 : 0 }));
  const [state, detail] = classify(warm);
  assert.equal(state, 'cache-is-read');
  assert.match(detail, /against 500000 written/);
  assert.match(handoff(state), /write-to-read ratio/);
});

test('no writes and no reads is the never switched on note', () => {
  const off = Array.from({ length: 120 }, (_, i) => minute(i));
  const [state, detail] = classify(off);
  assert.equal(state, 'caching-off');
  assert.match(detail, /no cache writes and no cache reads/);
  assert.match(handoff(state), /prompt-caching-never-used/);
  assert.equal(ttlSplit(totals(off))[0], 'no-writes');
  const readsOnly = Array.from({ length: 120 }, (_, i) => minute(i, { reads: 400000 }));
  assert.equal(classify(readsOnly)[0], 'reads-only');
});

test('a minority cached fragment is not the prefix', () => {
  const small = Array.from({ length: 120 },
    (_, i) => minute(i, { uncached: 900000, write5m: 100000 }));
  const [state, detail] = classify(small);
  assert.equal(state, 'small-cached-prefix');
  assert.match(detail, /writes are 10% of input/);
  assert.equal(handoff(state), '');
});

test('an hour long ttl makes the same run worse', () => {
  const hourly = Array.from({ length: 120 }, (_, i) => minute(i, { write1h: 500000 }));
  assert.equal(classify(hourly)[0], 'prefix-churn');
  const [ttlState, ttlDetail] = ttlSplit(totals(hourly));
  assert.equal(ttlState, '1h-dominant');
  assert.match(ttlDetail, /2x base input/);
  assert.equal(ttlSplit({ write5m: 10, write1h: 10 })[0], 'mixed');
});

test('a run crossing an hour boundary is not broken in half', () => {
  const crossing = Array.from({ length: 6 },
    (_, i) => minute(57 + i, { write5m: 500000 }));
  assert.deepEqual(crossing.slice(0, 4).map((r) => r.minute),
    ['2026-08-31T10:57Z', '2026-08-31T10:58Z', '2026-08-31T10:59Z',
     '2026-08-31T11:00Z']);
  const runs = churnRuns(crossing);
  assert.equal(runs.length, 1);
  assert.equal(runs[0].length, 6);
  assert.equal(minuteIndex('2026-08-31T11:00Z') - minuteIndex('2026-08-31T10:59Z'), 1);
});

test('the nested cache creation object is actually read', () => {
  const buckets = Array.from({ length: 6 }, (_, i) => ({
    starting_at: `2026-08-31T10:0${i}Z`,
    results: [{ api_key_id: 'apikey_01Ab', model: 'claude-opus-5',
                uncached_input_tokens: 100000,
                cache_read_input_tokens: 0,
                cache_creation: { ephemeral_5m_input_tokens: 500000,
                                  ephemeral_1h_input_tokens: 0 } }],
  }));
  const series = rowsByKey(buckets);
  const rows = [...series.values()][0];
  assert.equal(rows.length, 6);
  assert.equal(writes(rows[0]), 500000);
  assert.equal(classify(rows, 5, 0.5, 0.01, 6)[0], 'prefix-churn');
});

test('thin and unreadable windows produce no verdict', () => {
  const thin = Array.from({ length: 4 }, (_, i) => minute(i, { write5m: 500000 }));
  assert.equal(classify(thin)[0], 'too-little-traffic');
  assert.equal(classify([])[0], 'too-little-traffic');
  assert.equal(classify(null)[0], 'too-little-traffic');
  assert.equal(writeShare({ uncached: 0, write5m: 0, write1h: 0 }), null);
  assert.equal(gapProfile([]), null);
  assert.equal(minuteKey('nonsense'), null);
  assert.equal(minuteIndex(null), null);
  assert.equal(rowsByKey([{ starting_at: 'bad', results: [] }]).size, 0);
});
''',
"faq": [
 ("How is this different from cache writes with no reads?",
  "That note asks whether caching is paying for itself and answers it with a ratio: read tokens over write tokens, against a break-even computed from the 1.25x and 2x write premiums. It fires on plenty of shapes, including traffic that simply arrives less often than the TTL. This note is narrower and answers a different question, which is why the reads are zero rather than merely low. The evidence is adjacency: writing minutes back to back, longer than the TTL, so the entry provably outlived calls that never matched it. If your writing minutes are isolated, this is not your note and the script says so by name."),
 ("How is it different from prompt caching never being used?",
  "That one has no writes at all. Caching is opt-in, and without a cache_control breakpoint nothing is ever written or read, so both numbers are flat zero and the loss is a discount you never took. Here the feature is switched on and working exactly as documented: it writes an entry every time, at a 25 to 100 percent premium over plain input, and nothing ever matches it. You are paying more than you would with caching switched off, which is the worse of the two positions."),
 ("What actually invalidates a prefix?",
  "Any byte before the breakpoint. The prefix renders in the order tools, then system, then messages, so a change to a tool definition invalidates the tools, the system prompt and the conversation behind it, while toggling web search, citations, tool_choice, reasoning effort or adding an image invalidates progressively less. In practice the culprit is usually a clock in a system prompt, a tool list built from an unordered dictionary, a per-request id, or a per-user preamble placed before the breakpoint rather than after it."),
 ("Why one-minute buckets rather than the hourly ones?",
  "Because hourly buckets destroy the only evidence this note has. A hundred and twenty adjacent writing minutes and six isolated ones twenty minutes apart produce identical hourly rows: same writes, same uncached input, same zero reads. One is a prefix changing on every call and the other is traffic slower than the TTL, and the repairs have nothing in common. The spacing is the finding, so the resolution has to be finer than the TTL you are testing against."),
 ("Could this fire on a healthy multi-tenant service?",
  "Yes, and the script says so in the output rather than hiding it. Grouped by API key, a service that puts a per-tenant system prompt in front of every request writes constantly and correctly: every entry is a genuinely different prefix. Grouping by model as well narrows it, but the aggregate cannot see inside a key. Treat the finding as strong on a key serving one workload and as a prompt to look rather than a verdict on a key serving many."),
],
"related": [REL_CACHE_WRITES, REL_CACHE_NEVER, REL_TOOL_TOKENS],
"citations": [CITE_CL_CACHING, CITE_CL_USAGE_REPORT, CITE_CL_PRICING,
              CITE_CL_USAGE_API],
},
]
