#!/usr/bin/env python3
"""/llm/ field notes, batch J — the writing.

Four notes with one thing in common and nothing else: neither OpenAI nor
Anthropic lists individual requests. There is no endpoint on either API that
returns a call with its status code and its error body, so none of these four
findings is a log line. Each one is a *shape* in the usage buckets, and the
whole craft of the batch is that the four shapes are genuinely different and
the scripts reach them differently.

`reasoning-model-rejects-max-tokens` looks for requests that were counted and
produced nothing: `num_model_requests` above zero with `output_tokens` at zero
and, in the buckets that matter, no input tokens either. Nothing was read and
nothing was written, which is what a request body rejected at validation looks
like from the aggregate. The parameter is not too large; it is refused by name.

`requests-diverge-from-token-volume` reads the same OpenAI report and divides.
A retry storm moves the request count and leaves the token count where it was,
so tokens per request collapses while requests climb. Both numbers come off one
call, which is what makes this note runnable by anyone with an admin key and no
telemetry of their own at all. It was also rewritten mid-draft: the growth
divergence and the collapse in tokens per request are algebraically the same
statement, so the corroboration had to become something else, and what it
became is where in the week the surplus requests landed.

`overloaded-529-clusters` is the one that cannot be run that way. Anthropic's
messages usage report has no request-count field, so there is no "requests the
platform billed" to subtract from. The residual has to be derived from the work
that was done: your own attempt counter, minus the attempts the billed tokens
account for, clustered by minute. Contiguity is the finding, because a platform
capacity condition arrives in a run of minutes and a bucket-boundary artefact
does not.

`live-project-zero-usage-buckets` is the only one whose finding is an absence.
A project with traffic in the first twelve days of a fortnight and none in the
last two has not errored, because nothing was sent. The endpoint answers with
buckets whose `results` arrays are empty, and no dashboard built on error rates
and latency has ever alerted on that.

Read only throughout. Three want an organization admin key, one of those also
takes an OpenAI project key set to Read Only for a single model lookup, and one
wants an Anthropic Admin key plus a file of numbers you supply. GET requests
only: no completions, no token counting, nothing that costs anything. Every
repair — a renamed request field, a collapsed retry layer, a retry class that
includes 529, a liveness alarm with a floor — is a deploy with an owner, so it
is printed rather than performed.
"""

CITE_OAI_REASONING = ("Reasoning models — OpenAI developer docs",
                      "https://developers.openai.com/api/docs/guides/reasoning")
CITE_OAI_USAGE = ("Usage — OpenAI API reference",
                  "https://platform.openai.com/docs/api-reference/usage")
CITE_OAI_USAGE_COMPLETIONS = ("Completions usage — OpenAI API reference",
                              "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_OAI_MODELS = ("Models — OpenAI API reference",
                   "https://platform.openai.com/docs/api-reference/models")
CITE_OAI_ADMIN = ("Administration and the Admin APIs — OpenAI developer docs",
                  "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_OAI_RATE = ("Rate limits — OpenAI API",
                 "https://developers.openai.com/api/docs/guides/rate-limits")
CITE_OAI_PROJECT_RATE = ("Project rate limits — OpenAI API reference",
                         "https://platform.openai.com/docs/api-reference/project-rate-limits")
CITE_OAI_PROJECTS = ("Projects — OpenAI API reference",
                     "https://platform.openai.com/docs/api-reference/projects")
CITE_OAI_PROJECT_KEYS = ("Project API keys — OpenAI API reference",
                         "https://platform.openai.com/docs/api-reference/project-api-keys")

CITE_CL_ERRORS = ("Errors — Claude API",
                  "https://platform.claude.com/docs/en/api/errors")
CITE_CL_TIERS = ("Service tiers — Claude Docs",
                 "https://platform.claude.com/docs/en/api/service-tiers")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_CL_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")

REL_REASONING_TOKENS = ("/llm/reasoning-tokens-billed-invisibly/",
                        "Output tokens you are billed for and never see")
REL_RETIRED = ("/llm/retired-model-id-still-in-code/",
               "A model id in the config that the API no longer knows")
REL_RETIRING = ("/llm/model-retiring-within-90-days/",
                "The shutdown date that forces the migration in the first place")
REL_SPIKE = ("/llm/spend-spike-week-over-week/",
             "The shape of a change in spend: a spike, a step or a ramp")
REL_HEADROOM = ("/llm/rate-limit-headers-near-exhaustion/",
                "How much request and token headroom is actually left")
REL_LIMITER = ("/llm/rate-limit-429-limiter-unidentified/",
               "Naming which of the three limiters actually emptied")
REL_STREAMING = ("/llm/streaming-usage-lost/",
                 "Tokens the provider billed that your telemetry never recorded")
REL_KEY_OWNER = ("/llm/key-owner-lost-project-access/",
                 "A live key whose owner is no longer on the project")
REL_ARCHIVED = ("/llm/archived-project-still-holds-keys/",
                "Keys that survive the project being archived")
REL_QUOTA = ("/llm/quota-exhausted-not-rate-limited/",
             "A 429 that is a billing wall rather than a throttle")
REL_STORM = ("/llm/requests-diverge-from-token-volume/",
             "Request count climbing while token volume stays flat")
REL_529 = ("/llm/overloaded-529-clusters/",
           "Attempts the platform never served, clustered by minute")

GUIDES = [
{
"slug": "reasoning-model-rejects-max-tokens",
"title": "Requests billed, zero output tokens: max_tokens refused",
"description": "A reasoning model rejects max_tokens by name, so every call 400s before generation. In the usage report that is requests with no tokens either side.",
"h1": "Requests billed, zero output tokens: max_tokens refused",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["unsupported_parameter max_tokens", "max_completion_tokens",
             "gpt-5 max_tokens not supported", "openai reasoning model 400",
             "num_model_requests with zero output_tokens"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only. Optionally OPENAI_API_KEY, a project key set to Read Only, for one model lookup.",
"lead": "The model constant changed in a one-line pull request, because the old id has a shutdown date and somebody diaried it properly. The deploy went out on Thursday. Nothing paged: the endpoint returns a 500 to the user and the retry wrapper swallows it, and the error-rate dashboard is scoped to the gateway rather than to this worker. What the organization usage report shows for Friday is eleven thousand requests against the new model, no input tokens, and no output tokens at all.",
"short_answer": """<p>Read the buckets and look for the impossible row. With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={now-24h}&amp;bucket_width=1h&amp;group_by=model&amp;group_by=project_id</code>. A result with <code>num_model_requests</code> above zero, <code>output_tokens</code> at zero and <code>input_tokens</code> at zero is a set of calls that never reached the model: the request body was rejected on validation.</p>
<p>On the reasoning families that is almost always one field. Chat Completions replaced <code>max_tokens</code> with <code>max_completion_tokens</code>, because the cap now has to cover reasoning tokens as well as visible output, and the old name is refused outright with <code>code: "unsupported_parameter"</code>. On the Responses API the field is <code>max_output_tokens</code>. The same rejection covers <code>temperature</code>, <code>top_p</code>, <code>presence_penalty</code> and <code>frequency_penalty</code>, which reasoning models replace with a reasoning effort setting.</p>
<p>This is not a number that is too large. No value of <code>max_tokens</code> works, so raising or lowering it changes nothing; the parameter is refused by name. Confirm with one <code>GET /v1/models/{model}</code> using a Read Only project key: a <code>200</code> proves the id is valid and reachable, which puts the fault in the request body rather than in access or retirement.</p>""",
"problem": """<p>There is no request log to check. Neither API has an endpoint that lists calls with their status codes, so a fleet that is 400ing on every single request looks, from the provider's side, exactly like a fleet that is quietly succeeding &mdash; unless you notice that the successful ones would have produced tokens. Requests are counted. Tokens are not. That gap is the entire signal.</p>
<p>What makes it survive a week is the retry layer. A 400 is not retryable, but a wrapper that catches broadly retries it anyway, three times, and then raises something the caller has always treated as transient. Users see a slow failure. The queue drains, eventually, into a dead-letter table nobody reads. The invoice for the model goes to nearly nothing, which is the one visible symptom, and a bill that went down is not a bill anyone investigates.</p>""",
"why": """<p><strong>The cap changed meaning, not just its name.</strong> A reasoning model generates tokens you never see before it generates the ones you do, and both are billed as output. <code>max_completion_tokens</code> caps the sum. Renaming the field and keeping the number is a second bug waiting behind the first: a budget that used to fit a four-hundred-word answer now has to fit the thinking as well, and a request that runs out mid-reasoning comes back with an empty message and a <code>length</code> finish reason. Rename it and raise it.</p>
<p><strong>A rejected parameter and a parameter that is out of range are different findings.</strong> A <code>max_tokens</code> above the model's own ceiling is a number to lower, provable in advance against the model object, and it fails with a value error. This one fails with <code>unsupported_parameter</code> and no value of the field is acceptable. They read almost identically in an incident channel and they have nothing in common in the code.</p>
<p><strong>Zero output with input tokens present is a different problem again.</strong> If the buckets show input tokens being read and nothing coming back, the prompt reached the model and generation was blocked: organization verification on a streaming path, a content filter, or a cap set to zero. This script keeps those apart rather than folding both into "the model is broken", because the second one sends you to the console and the first one sends you to a diff.</p>
<p><strong>Partial silence means a partial deploy.</strong> A share of requests generating nothing, rather than all of them, is usually one replica set that did not restart, one Lambda alias still on the old package, or a canary. The finding is the same field and the repair is a rollout rather than a code change, so the script reports the share instead of rounding it to yes or no.</p>
<p><strong>The sampling parameters go the same way.</strong> <code>temperature=0</code> "for determinism" is one of the most common defaults in the ecosystem, and reasoning models reject it with <code>unsupported_value</code> because variance is controlled by effort rather than by sampling. A codebase that fixes only <code>max_tokens</code> ships, fails identically the same afternoon, and nobody believes the diagnosis the second time. Print the whole list at once.</p>""",
"steps": [
 {"h": "Read a day of hourly buckets grouped by model and project",
  "body": """<p><code>GET /v1/organization/usage/completions</code> with <code>bucket_width=1h</code>, <code>group_by=model</code> and <code>group_by=project_id</code>. Both groupings matter: the model tells you which family refused the parameter and the project tells you whose deploy did it. An hour is the right grain because the fault starts at a deploy, and a daily bucket smears the before and the after together.</p>"""},
 {"h": "Find rows with requests and no tokens on either side",
  "body": """<p><code>num_model_requests &gt; 0</code> with <code>output_tokens == 0</code>. Then split on input: no input tokens means the body was rejected before the prompt was read, input tokens present means the prompt was read and generation did not happen. Only the first is this note.</p>"""},
 {"h": "Confirm the model id is reachable before blaming the model",
  "body": """<p>One <code>GET /v1/models/{model}</code> with a Read Only project key. A <code>200</code> says the id exists and this key can use it, which leaves the request body as the only remaining suspect. A <code>404</code> says the opposite and hands you to the retirement and entitlement notes instead &mdash; same symptom in the log, unrelated repair.</p>"""},
 {"h": "Print the rename for the surface the code actually uses",
  "body": """<p>Chat Completions wants <code>max_completion_tokens</code>. The Responses API wants <code>max_output_tokens</code>. They are not interchangeable, and a wrapper library that supports both surfaces needs the branch rather than one global replace. Print both lines and let the reader pick.</p>"""},
 {"h": "Fix the sampling parameters in the same change",
  "body": """<p><code>temperature</code>, <code>top_p</code>, <code>presence_penalty</code>, <code>frequency_penalty</code> and <code>logprobs</code> are refused by the same models for the same reason. Remove them, express the intent as a reasoning effort instead, and do not send <code>temperature: 1</code> explicitly to be safe &mdash; omit the field. Two deploys for one incident is how a team stops trusting the diagnosis.</p>"""},
],
"verify": """<p>Re-run an hour after the deploy. The row should keep its request count and grow output tokens; a row that keeps 100% silence has a second rejected field in it.</p>
<pre><code class="language-bash">python3 openai_zero_output_buckets.py --hours 24
# parameter-rejected  proj_api / gpt-5.1  11482 request(s) over 24 bucket(s), 0 input token(s) and 0 output token(s). Nothing was read and nothing was generated.
#   the id resolves for this key, so the fault is in the request body and not in access
#   repair: Chat Completions: send max_completion_tokens instead of max_tokens, and raise the number.
# 6 model/project row(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET for the buckets and, when a finding turns up, one cheap GET per model id to prove the id is reachable. Six pure functions: the fold, which keeps the silent buckets countable rather than summing them away; the family test, which has to say no to <code>gpt-4o</code> as confidently as it says yes to <code>o3-mini</code>; the share; the classifier, which splits a rejected body from blocked generation on whether any input tokens were read; the repair lines for each API surface; and the reading of the model lookup's status code, because a 404 there is a different note with the same symptom.",
"py_file": "openai_zero_output_buckets.py",
"py": '''"""Find OpenAI usage buckets that counted requests and generated nothing.

Read only. One GET against the organization usage report, which needs an
organization admin key (sk-admin-) and can be provisioned read-only, plus an
optional GET /v1/models/{id} with a project key set to Read Only.

Neither API lists individual requests, so this is a shape in the aggregate
rather than an error log: num_model_requests above zero with output_tokens at
zero is a set of calls that never reached generation, and no input tokens with
it means the request body was rejected before the prompt was read.

The repair is printed, never performed. Renaming a request field is a deploy.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_zero_output_buckets")

API = "https://api.openai.com/v1"

# The families that replaced max_tokens with max_completion_tokens and refuse
# the sampling parameters outright. Matched as whole id prefixes, because a
# substring test for "o1" or "o3" also matches ids that have nothing to do with
# reasoning and a substring test for "o" matches gpt-4o.
REASONING_PREFIXES = ("o1", "o3", "o4", "gpt-5")

FINDINGS = ("parameter-rejected", "partial-rejection")


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def is_reasoning_model(model):
    """Is this id one of the families that refuse max_tokens? Pure.

    Whole-prefix matching only. gpt-4o must come back False here or the script
    prints a rename that does not apply and sends somebody to change a field
    that was never the problem.
    """
    name = str(model or "").strip().lower()
    if not name:
        return False
    for prefix in REASONING_PREFIXES:
        if name == prefix or name.startswith(prefix + "-") or name.startswith(prefix + "."):
            return True
    return False


def fold(buckets):
    """Fold usage buckets into one row per (project, model). Pure.

    The silent buckets are counted rather than summed away. "Every bucket in
    the window generated nothing" and "one bucket in twelve generated nothing"
    are a broken deploy and a half-finished rollout, and a total cannot tell
    them apart.
    """
    rows = {}
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            key = (str(result.get("project_id") or "unknown"),
                   str(result.get("model") or "unknown"))
            row = rows.setdefault(key, {"requests": 0, "input": 0, "output": 0,
                                        "buckets": 0, "silent_buckets": 0,
                                        "silent_requests": 0, "silent_input": 0})
            made = _int(result.get("num_model_requests"))
            read = _int(result.get("input_tokens"))
            wrote = _int(result.get("output_tokens"))
            row["requests"] += made
            row["input"] += read
            row["output"] += wrote
            row["buckets"] += 1
            if made > 0 and wrote == 0:
                row["silent_buckets"] += 1
                row["silent_requests"] += made
                row["silent_input"] += read
    return rows


def silent_share(row):
    """Share of a row's requests that generated no output at all. Pure.

    None when there were no requests, which is a different state from zero and
    must not be rounded into one.
    """
    requests_made = _int((row or {}).get("requests"))
    if requests_made <= 0:
        return None
    return min(1.0, _int(row.get("silent_requests")) / float(requests_made))


def classify(model, row, min_requests=50, partial_floor=0.2, total_floor=0.99):
    """Classify one (project, model) row. Pure. Returns (state, detail).

    The split that matters is on input tokens inside the silent buckets. No
    input and no output means the request body was rejected on validation.
    Input read with no output means the prompt reached the model and generation
    was blocked, which is verification or a filter and a different repair.
    """
    row = row or {}
    requests_made = _int(row.get("requests"))
    if requests_made < min_requests:
        return ("too-few-requests",
                "%d request(s) in the window, under the floor of %d. A silence "
                "this small is not evidence of anything."
                % (requests_made, min_requests))

    share = silent_share(row) or 0.0
    shape = ("%d request(s) over %d bucket(s), %d input token(s) and %d output "
             "token(s)" % (requests_made, _int(row.get("buckets")),
                           _int(row.get("input")), _int(row.get("output"))))

    if share >= total_floor:
        if _int(row.get("silent_input")) == 0:
            return ("parameter-rejected",
                    shape + ". Nothing was read and nothing was generated, so "
                    "these calls were rejected on the request body before the "
                    "prompt was processed.")
        return ("generation-blocked",
                shape + ". The prompt was read and nothing came back, which is "
                "not a refused parameter name: look at organization "
                "verification, a content filter, or an output cap of zero.")

    if share >= partial_floor:
        return ("partial-rejection",
                "%s, and %.0f%% of those requests generated nothing. Part of "
                "the fleet is still sending the old field."
                % (shape, share * 100))

    return ("generating", shape + ".")


def repair_lines(model):
    """The exact request-body repair for one model id. Pure.

    Both API surfaces, because they are not interchangeable and a wrapper that
    supports both needs the branch rather than one global replace.
    """
    if is_reasoning_model(model):
        return [
            "Chat Completions: send max_completion_tokens instead of "
            "max_tokens, and raise the number. The cap now has to absorb "
            "reasoning tokens as well as the visible answer.",
            "Responses API: the same field is called max_output_tokens.",
            "Remove temperature, top_p, presence_penalty, frequency_penalty "
            "and logprobs for this model and express the intent as a reasoning "
            "effort setting. Do not send temperature 1 explicitly; omit it.",
        ]
    return [
        "This id is not one of the reasoning families, so a refused parameter "
        "name is the less likely cause here. Read one 400 body for its code "
        "and param fields before changing anything.",
    ]


def model_verdict(status):
    """What the model lookup says about whose fault the failure is. Pure."""
    if status is None:
        return ("unchecked",
                "no project key was supplied, so the model id itself was not "
                "checked")
    if status == 200:
        return ("id-resolves",
                "the id resolves for this key, so the fault is in the request "
                "body and not in access")
    if status == 404:
        return ("id-unreachable",
                "the id does not resolve for this key. That is retirement or "
                "entitlement rather than a parameter name, and it is a "
                "different repair")
    if status in (401, 403):
        return ("check-refused",
                "the project key could not read the model list, so the id was "
                "not confirmed either way")
    return ("check-inconclusive", "the model lookup returned %d" % int(status))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk the usage report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def check_model(key, model):
    """One cheap GET to prove the id is reachable. Returns a status code."""
    if not key:
        return None
    try:
        r = requests.get(API + "/models/" + str(model),
                         headers={"Authorization": "Bearer " + key}, timeout=30)
    except requests.RequestException:
        return None
    return r.status_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=int, default=24,
                    help="hours of hourly buckets to read (default 24)")
    ap.add_argument("--min-requests", type=int, default=50,
                    help="ignore rows below this many requests (default 50)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print rows that are generating normally")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key; read-only "
                  "scopes are enough)")
        return 2
    project_key = os.environ.get("OPENAI_API_KEY")

    hours = max(1, min(int(args.hours), 168))
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    buckets = pages(session, "/organization/usage/completions", {
        "start_time": int(time.time()) - hours * 3600,
        "bucket_width": "1h",
        "limit": hours,
        "group_by": ["model", "project_id"],
    })
    rows = fold(buckets)
    if not rows:
        log.info("no completions usage in the last %d hour(s)", hours)
        return 0

    checked = 0
    bad = 0
    for project, model in sorted(rows, key=lambda k: -rows[k]["requests"]):
        row = rows[(project, model)]
        state, detail = classify(model, row, args.min_requests)
        checked += 1
        line = "%-19s %s / %s  %s" % (state, project, model, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            _, note = model_verdict(check_model(project_key, model))
            log.warning("  %s", note)
            for repair in repair_lines(model):
                log.warning("  repair: %s", repair)
        elif state == "generation-blocked":
            log.warning(line)
            log.warning("  repair: this is not the parameter rename. Check "
                        "organization verification for the streaming path and "
                        "the project's model permissions before touching the "
                        "request body.")
        elif args.show_all:
            log.info(line)

    log.info("%d model/project row(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-zero-output-buckets.mjs",
"js": '''/**
 * Find OpenAI usage buckets that counted requests and generated nothing.
 *
 * Read only. One GET against the organization usage report, which needs an
 * organization admin key (sk-admin-), plus an optional GET /v1/models/{id}
 * with a project key set to Read Only.
 *
 * num_model_requests above zero with output_tokens at zero is a set of calls
 * that never reached generation; no input tokens with it means the body was
 * rejected before the prompt was read. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// Whole-id prefixes. A substring test for "o" would match gpt-4o.
const REASONING_PREFIXES = ['o1', 'o3', 'o4', 'gpt-5'];

const FINDINGS = new Set(['parameter-rejected', 'partial-rejection']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Is this id one of the families that refuse max_tokens? Pure.
 * gpt-4o must be false here, or the script prints a rename that does not apply.
 */
export function isReasoningModel(model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return false;
  return REASONING_PREFIXES.some(
    (p) => name === p || name.startsWith(`${p}-`) || name.startsWith(`${p}.`));
}

/**
 * Fold usage buckets into one row per (project, model). Pure.
 * Silent buckets are counted rather than summed away: all of them and one in
 * twelve are a broken deploy and a half-finished rollout.
 */
export function fold(buckets) {
  const rows = new Map();
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const key = `${result?.project_id ?? 'unknown'}\\u0000${result?.model ?? 'unknown'}`;
      if (!rows.has(key)) {
        rows.set(key, { project: String(result?.project_id ?? 'unknown'),
                        model: String(result?.model ?? 'unknown'),
                        requests: 0, input: 0, output: 0, buckets: 0,
                        silentBuckets: 0, silentRequests: 0, silentInput: 0 });
      }
      const row = rows.get(key);
      const made = readInt(result?.num_model_requests);
      const read = readInt(result?.input_tokens);
      const wrote = readInt(result?.output_tokens);
      row.requests += made;
      row.input += read;
      row.output += wrote;
      row.buckets += 1;
      if (made > 0 && wrote === 0) {
        row.silentBuckets += 1;
        row.silentRequests += made;
        row.silentInput += read;
      }
    }
  }
  return rows;
}

/** Share of a row's requests that generated no output. Pure. Null when none. */
export function silentShare(row) {
  const made = readInt(row?.requests);
  if (made <= 0) return null;
  return Math.min(1, readInt(row?.silentRequests) / made);
}

/**
 * Classify one (project, model) row. Pure. Returns [state, detail].
 * The split is on input tokens inside the silent buckets: none means the body
 * was rejected on validation, some means generation was blocked instead.
 */
export function classify(model, row, minRequests = 50, partialFloor = 0.2,
                         totalFloor = 0.99) {
  const made = readInt(row?.requests);
  if (made < minRequests) {
    return ['too-few-requests',
      `${made} request(s) in the window, under the floor of ${minRequests}. ` +
      'A silence this small is not evidence of anything.'];
  }

  const share = silentShare(row) ?? 0;
  const shape = `${made} request(s) over ${readInt(row?.buckets)} bucket(s), ` +
    `${readInt(row?.input)} input token(s) and ${readInt(row?.output)} output token(s)`;

  if (share >= totalFloor) {
    if (readInt(row?.silentInput) === 0) {
      return ['parameter-rejected',
        `${shape}. Nothing was read and nothing was generated, so these calls ` +
        'were rejected on the request body before the prompt was processed.'];
    }
    return ['generation-blocked',
      `${shape}. The prompt was read and nothing came back, which is not a ` +
      'refused parameter name: look at organization verification, a content ' +
      'filter, or an output cap of zero.'];
  }

  if (share >= partialFloor) {
    return ['partial-rejection',
      `${shape}, and ${(share * 100).toFixed(0)}% of those requests generated ` +
      'nothing. Part of the fleet is still sending the old field.'];
  }

  return ['generating', `${shape}.`];
}

/** The exact request-body repair for one model id. Pure. */
export function repairLines(model) {
  if (isReasoningModel(model)) {
    return [
      'Chat Completions: send max_completion_tokens instead of max_tokens, and ' +
      'raise the number. The cap now has to absorb reasoning tokens as well as ' +
      'the visible answer.',
      'Responses API: the same field is called max_output_tokens.',
      'Remove temperature, top_p, presence_penalty, frequency_penalty and ' +
      'logprobs for this model and express the intent as a reasoning effort ' +
      'setting. Do not send temperature 1 explicitly; omit it.',
    ];
  }
  return [
    'This id is not one of the reasoning families, so a refused parameter name ' +
    'is the less likely cause here. Read one 400 body for its code and param ' +
    'fields before changing anything.',
  ];
}

/** What the model lookup says about whose fault the failure is. Pure. */
export function modelVerdict(status) {
  if (status === null || status === undefined) {
    return ['unchecked',
      'no project key was supplied, so the model id itself was not checked'];
  }
  if (status === 200) {
    return ['id-resolves',
      'the id resolves for this key, so the fault is in the request body and ' +
      'not in access'];
  }
  if (status === 404) {
    return ['id-unreachable',
      'the id does not resolve for this key. That is retirement or entitlement ' +
      'rather than a parameter name, and it is a different repair'];
  }
  if (status === 401 || status === 403) {
    return ['check-refused',
      'the project key could not read the model list, so the id was not ' +
      'confirmed either way'];
  }
  return ['check-inconclusive', `the model lookup returned ${status}`];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* pages(key, path, params, maxPages = 40) {
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    for (const bucket of page?.data ?? []) yield bucket;
    if (!page?.has_more || !page?.next_page) return;
    query = { ...params, page: page.next_page };
  }
}

async function checkModel(key, model) {
  if (!key) return null;
  try {
    const res = await fetch(`${API}/models/${model}`,
                            { headers: { Authorization: `Bearer ${key}` } });
    return res.status;
  } catch {
    return null;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key; read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }
  const projectKey = process.env.OPENAI_API_KEY;
  const hours = Math.max(1, Math.min(Number(process.env.HOURS ?? 24), 168));
  const minRequests = Number(process.env.MIN_REQUESTS ?? 50);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of pages(admin, '/organization/usage/completions', {
    start_time: Math.floor(Date.now() / 1000) - hours * 3600,
    bucket_width: '1h',
    limit: hours,
    group_by: ['model', 'project_id'],
  })) buckets.push(bucket);

  const rows = fold(buckets);
  if (rows.size === 0) {
    console.log(`no completions usage in the last ${hours} hour(s)`);
    return;
  }

  let checked = 0;
  let bad = 0;
  const ordered = [...rows.values()].sort((a, b) => b.requests - a.requests);
  for (const row of ordered) {
    const [state, detail] = classify(row.model, row, minRequests);
    checked += 1;
    const line = `${state.padEnd(19)} ${row.project} / ${row.model}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      const [, note] = modelVerdict(await checkModel(projectKey, row.model));
      console.warn(`  ${note}`);
      for (const repair of repairLines(row.model)) console.warn(`  repair: ${repair}`);
    } else if (state === 'generation-blocked') {
      console.warn(line);
      console.warn('  repair: this is not the parameter rename. Check organization ' +
                   'verification for the streaming path and the project model ' +
                   'permissions before touching the request body.');
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${checked} model/project row(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is the row that has requests and nothing else: eleven thousand calls, no input tokens, no output tokens, classified as a rejected body rather than as a quiet model. Beside it sits the row this note is most often confused with &mdash; same request count, same zero output, but input tokens were read &mdash; and it has to come back as a different state with a different repair. The family test earns its place by saying no to <code>gpt-4o</code>, which a substring match on <code>o</code> would happily call a reasoning model, and the partial case pins the share so a half-finished rollout is not rounded up into a total outage.",
"test_py_file": "test_openai_zero_output_buckets.py",
"test_py": '''from openai_zero_output_buckets import (classify, fold, is_reasoning_model,
                                        model_verdict, repair_lines,
                                        silent_share)


def bucket(project, model, requests_made, input_tokens, output_tokens):
    return {"results": [{"project_id": project, "model": model,
                         "num_model_requests": requests_made,
                         "input_tokens": input_tokens,
                         "output_tokens": output_tokens}]}


def test_requests_with_no_tokens_either_side_is_a_rejected_body():
    # The note in one assertion. Every call counted, nothing read, nothing
    # written: the body never got past validation.
    rows = fold([bucket("proj_api", "gpt-5.1", 500, 0, 0) for _ in range(24)])
    row = rows[("proj_api", "gpt-5.1")]
    assert row["requests"] == 12000
    assert row["buckets"] == 24 and row["silent_buckets"] == 24
    assert silent_share(row) == 1.0

    state, detail = classify("gpt-5.1", row)
    assert state == "parameter-rejected"
    assert "0 input token(s) and 0 output token(s)" in detail
    assert "max_completion_tokens" in repair_lines("gpt-5.1")[0]
    assert "max_output_tokens" in repair_lines("gpt-5.1")[1]


def test_input_read_and_nothing_generated_is_a_different_finding():
    # Same request count, same zero output, and not this note: the prompt
    # reached the model, so the body was accepted and generation was blocked.
    rows = fold([bucket("proj_api", "gpt-5.1", 500, 900000, 0) for _ in range(24)])
    state, detail = classify("gpt-5.1", rows[("proj_api", "gpt-5.1")])
    assert state == "generation-blocked"
    assert "verification" in detail


def test_a_partial_rollout_is_not_rounded_up_to_a_total_outage():
    silent = [bucket("proj_api", "o3-mini", 100, 0, 0) for _ in range(6)]
    healthy = [bucket("proj_api", "o3-mini", 100, 200000, 40000) for _ in range(18)]
    row = fold(silent + healthy)[("proj_api", "o3-mini")]
    assert silent_share(row) == 0.25
    state, detail = classify("o3-mini", row)
    assert state == "partial-rejection"
    assert "25%" in detail


def test_the_reasoning_families_are_matched_as_whole_prefixes():
    for model in ("o1", "o3-mini", "o4-mini", "gpt-5", "gpt-5.1-mini",
                  "gpt-5-2026-01-15"):
        assert is_reasoning_model(model) is True
    # gpt-4o is the one a careless substring match gets wrong.
    for model in ("gpt-4o", "gpt-4o-mini", "gpt-4.1", "claude-sonnet-5", "", None):
        assert is_reasoning_model(model) is False
    assert "reasoning families" in repair_lines("gpt-4o")[0]


def test_a_quiet_row_is_not_a_silent_one():
    assert silent_share({"requests": 0, "silent_requests": 0}) is None
    assert silent_share(None) is None
    state, _ = classify("gpt-5.1", {"requests": 4, "silent_requests": 4})
    assert state == "too-few-requests"
    healthy = fold([bucket("p", "gpt-5.1", 500, 200000, 60000)])
    assert classify("gpt-5.1", healthy[("p", "gpt-5.1")])[0] == "generating"


def test_a_404_on_the_model_lookup_is_a_different_note_entirely():
    assert model_verdict(200)[0] == "id-resolves"
    assert model_verdict(404)[0] == "id-unreachable"
    assert "retirement or entitlement" in model_verdict(404)[1]
    assert model_verdict(403)[0] == "check-refused"
    assert model_verdict(None)[0] == "unchecked"


def test_unreadable_usage_fields_do_not_become_phantom_requests():
    rows = fold([{"results": [{"project_id": "p", "model": "gpt-5.1",
                               "num_model_requests": None,
                               "input_tokens": "nonsense",
                               "output_tokens": None}]}])
    assert rows[("p", "gpt-5.1")]["requests"] == 0
    assert rows[("p", "gpt-5.1")]["silent_buckets"] == 0
    assert fold([]) == {}
    assert fold(None) == {}
''',
"test_js_file": "openai-zero-output-buckets.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, fold, isReasoningModel, modelVerdict, repairLines, silentShare }
  from './openai-zero-output-buckets.mjs';

const bucket = (project, model, made, input, output) => ({
  results: [{ project_id: project, model, num_model_requests: made,
              input_tokens: input, output_tokens: output }],
});

const rowFor = (buckets, project, model) =>
  [...fold(buckets).values()].find((r) => r.project === project && r.model === model);

test('requests with no tokens either side is a rejected body', () => {
  const buckets = Array.from({ length: 24 },
    () => bucket('proj_api', 'gpt-5.1', 500, 0, 0));
  const row = rowFor(buckets, 'proj_api', 'gpt-5.1');
  assert.equal(row.requests, 12000);
  assert.equal(row.buckets, 24);
  assert.equal(row.silentBuckets, 24);
  assert.equal(silentShare(row), 1);

  const [state, detail] = classify('gpt-5.1', row);
  assert.equal(state, 'parameter-rejected');
  assert.match(detail, /0 input token\\(s\\) and 0 output token\\(s\\)/);
  assert.match(repairLines('gpt-5.1')[0], /max_completion_tokens/);
  assert.match(repairLines('gpt-5.1')[1], /max_output_tokens/);
});

test('input read and nothing generated is a different finding', () => {
  const buckets = Array.from({ length: 24 },
    () => bucket('proj_api', 'gpt-5.1', 500, 900000, 0));
  const [state, detail] = classify('gpt-5.1', rowFor(buckets, 'proj_api', 'gpt-5.1'));
  assert.equal(state, 'generation-blocked');
  assert.match(detail, /verification/);
});

test('a partial rollout is not rounded up to a total outage', () => {
  const silent = Array.from({ length: 6 }, () => bucket('proj_api', 'o3-mini', 100, 0, 0));
  const healthy = Array.from({ length: 18 },
    () => bucket('proj_api', 'o3-mini', 100, 200000, 40000));
  const row = rowFor([...silent, ...healthy], 'proj_api', 'o3-mini');
  assert.equal(silentShare(row), 0.25);
  const [state, detail] = classify('o3-mini', row);
  assert.equal(state, 'partial-rejection');
  assert.match(detail, /25%/);
});

test('the reasoning families are matched as whole prefixes', () => {
  for (const model of ['o1', 'o3-mini', 'o4-mini', 'gpt-5', 'gpt-5.1-mini',
                       'gpt-5-2026-01-15']) {
    assert.equal(isReasoningModel(model), true, model);
  }
  for (const model of ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'claude-sonnet-5', '', null]) {
    assert.equal(isReasoningModel(model), false, String(model));
  }
  assert.match(repairLines('gpt-4o')[0], /reasoning families/);
});

test('a quiet row is not a silent one', () => {
  assert.equal(silentShare({ requests: 0, silentRequests: 0 }), null);
  assert.equal(silentShare(null), null);
  assert.equal(classify('gpt-5.1', { requests: 4, silentRequests: 4 })[0], 'too-few-requests');
  const healthy = rowFor([bucket('p', 'gpt-5.1', 500, 200000, 60000)], 'p', 'gpt-5.1');
  assert.equal(classify('gpt-5.1', healthy)[0], 'generating');
});

test('a 404 on the model lookup is a different note entirely', () => {
  assert.equal(modelVerdict(200)[0], 'id-resolves');
  assert.equal(modelVerdict(404)[0], 'id-unreachable');
  assert.match(modelVerdict(404)[1], /retirement or entitlement/);
  assert.equal(modelVerdict(403)[0], 'check-refused');
  assert.equal(modelVerdict(null)[0], 'unchecked');
});

test('unreadable usage fields do not become phantom requests', () => {
  const row = rowFor([{ results: [{ project_id: 'p', model: 'gpt-5.1',
                                    num_model_requests: null,
                                    input_tokens: 'nonsense',
                                    output_tokens: null }] }], 'p', 'gpt-5.1');
  assert.equal(row.requests, 0);
  assert.equal(row.silentBuckets, 0);
  assert.equal(fold([]).size, 0);
  assert.equal(fold(null).size, 0);
});
''',
"faq": [
 ("Why not just read the 400 body instead of the usage report?",
  "Because you cannot, from the API. Neither OpenAI nor Anthropic exposes an endpoint that lists individual requests with their status codes and error bodies, so the only place a fleet-wide 400 shows up in the platform's own data is as requests that consumed nothing. If your application logs the response bodies then read those first, obviously; this script exists for the case where the errors were swallowed by a retry wrapper and the logs say nothing useful."),
 ("Is this the same as max_tokens being above the model's cap?",
  "No, and they are worth keeping apart because they read the same in an incident channel. A value above the model's ceiling is a number to lower and it can be checked in advance against the model object's own max output tokens. This one is a field refused by name, with code unsupported_parameter, and no value of it is accepted. One is arithmetic; the other is a rename."),
 ("The buckets show input tokens and no output. Same bug?",
  "Different bug. Input tokens mean the prompt reached the model, so the request body was accepted. Generation was blocked afterwards: organization verification on a streaming path, a content filter, or an output cap of zero. The script reports that as its own state precisely so nobody spends an afternoon renaming a field that was never rejected."),
 ("Do the failed requests cost anything?",
  "A request rejected on validation generates nothing and there is nothing to bill for, which is exactly why the row looks the way it does. The cost is elsewhere: the work is not being done, the retries are consuming rate-limit budget, and the spend against that model has quietly gone to near zero, which is the one visible symptom and the one nobody investigates."),
 ("Which parameters do reasoning models refuse, other than max_tokens?",
  "temperature, top_p, presence_penalty, frequency_penalty and logprobs, all with unsupported_value rather than unsupported_parameter. Variance is controlled by the reasoning effort setting instead, which is why the sampling knobs are refused rather than ignored. Fix them in the same change: shipping the max_tokens rename alone means failing again the same afternoon, and nobody believes the second diagnosis."),
],
"related": [REL_REASONING_TOKENS, REL_RETIRING, REL_RETIRED],
"citations": [CITE_OAI_REASONING, CITE_OAI_USAGE_COMPLETIONS, CITE_OAI_MODELS, CITE_OAI_ADMIN],
},
{
"slug": "requests-diverge-from-token-volume",
"title": "Request count tripled while token volume stayed flat",
"description": "A retry storm moves one of the two series the usage report carries. Tokens per request collapsing while requests climb is the only thing that does it.",
"h1": "Request count tripled while token volume stayed flat",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai retry storm", "num_model_requests growth",
             "tokens per request dropped", "openai rpm ceiling not tpm",
             "double retry layer sdk max_retries"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only. Nothing else: both series come off the same report.",
"lead": "Latency got worse over about a fortnight, in the way that nobody can date precisely. Then 429s started arriving at a volume that used to be comfortable, and the obvious explanation was growth, except that the invoice barely moved. Two numbers sit in the same usage report and they have come apart: requests are up three times and tokens are up not at all. Two thirds of the extra calls landed in seventeen hours out of a hundred and sixty-eight, which is not what a new customer looks like.",
"short_answer": """<p>Read both series off one call and divide. With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={now-14d}&amp;bucket_width=1h&amp;group_by=model&amp;group_by=project_id</code>. Each result carries <code>num_model_requests</code> alongside <code>input_tokens</code> and <code>output_tokens</code>, so the whole finding is available without any telemetry of your own.</p>
<p>Compare the last seven days against the seven before. Real growth moves both series by roughly the same factor. A retry storm moves the request count and leaves the token count almost where it was, so <code>(input + output) / num_model_requests</code> collapses: many short calls that failed early, retried, and eventually succeeded.</p>
<p>Then ask <em>where in the week</em> the extra calls landed, because that is the only independent evidence available. Retries amplify during the incidents that caused them, so a storm piles its surplus requests into a handful of hours. A workload that genuinely got shorter spreads them evenly across all of them.</p>
<p>Then confirm which ceiling you are pressed against: <code>GET /v1/organization/projects/{project_id}/rate_limits</code>. A retry storm sits near <code>max_requests_per_1_minute</code> while nowhere near <code>max_tokens_per_1_minute</code>, which is itself diagnostic, because genuine traffic growth pushes both up together.</p>""",
"problem": """<p>Every OpenAI SDK retries on 429 and 5xx by default. Application code then adds a second layer &mdash; a decorator, a queue redelivery, a job runner that re-enqueues on failure &mdash; and the layers multiply rather than add. Three attempts inside three attempts is nine requests for one logical call, and each of the nine consumes request-rate budget. The work still gets done, so nothing raises, so nobody looks.</p>
<p>What it costs is capacity rather than money. Rate limits start binding at volumes that were fine a month ago, tail latency climbs because every logical call now carries the time of its failed attempts, and the system becomes less stable exactly when it is under load, since the retries amplify precisely when failures are most likely. The bill is a poor alarm here: retried attempts that failed early generated few tokens, so a storm can triple your request rate and move the invoice by single digits.</p>""",
"why": """<p><strong>The two series come apart in only one way.</strong> Genuine growth is more calls of the same shape, so requests and tokens rise together. A prompt that grew moves tokens and leaves requests alone. Only re-issuing the same work moves requests without moving tokens, which is why the ratio between the two growth rates is a fingerprint rather than a heuristic.</p>
<p><strong>Tokens per request is not corroboration, and this note was rewritten when that became obvious.</strong> The first draft flagged a storm when request growth outran token growth <em>and</em> the mean call size collapsed, as though those were two agreeing witnesses. They are one witness: request growth divided by token growth is exactly the reciprocal of the change in tokens per request, so the second test can never disagree with the first. It is arithmetic, not evidence. The script now says so in the function that computes it.</p>
<p><strong>The independent signal is where in the week the extra calls landed.</strong> Retries amplify during the failures that caused them, so a storm concentrates its surplus requests into the hours when something was wrong. A new short workload &mdash; a classifier endpoint, a health check that started calling the model &mdash; produces the same weekly ratios spread evenly across every hour. Take the busiest tenth of the recent hours: even traffic puts about a tenth of its requests there, and a storm puts most of them there. That comparison needs the hourly buckets kept rather than summed, which is why the script does not fold the window until the last moment.</p>
<p><strong>The RPM ceiling fills while the TPM ceiling stays empty.</strong> Retried attempts are charged against the request limiter whether or not they generate anything. A project pinned near <code>max_requests_per_1_minute</code> with its token limit barely touched is the same finding from the other side, and it is the reason raising the rate limit feels like it works: it does, for a fortnight, and then the amplification catches up.</p>
<p><strong>Hourly buckets cannot resolve a minute.</strong> The rate-limit comparison here is an hourly mean spread across sixty minutes, which is a floor on the real peak and never the peak itself. That is fine for this purpose: if even the mean is close to the ceiling, the peak went past it long ago. It is not fine as a capacity plan, and the script says so rather than quietly implying a precision it does not have.</p>
<p><strong>This is not the same read as a spend spike.</strong> A <a href="/llm/spend-spike-week-over-week/">week-over-week cost check</a> folds one series &mdash; money &mdash; and classifies its shape as a spike, a step or a ramp. This note ignores money entirely and compares two token-and-request series against each other. A storm that triples requests can be invisible to the cost check and unmissable here, which is the whole reason both exist.</p>
<p><strong>It is also not the same read as a 529 cluster.</strong> Both notes are about requests that did not do the work you expected, but the arithmetic runs in opposite directions and needs different inputs. Here every number is the provider's: requests it counted and tokens it billed. In the <a href="/llm/overloaded-529-clusters/">overload note</a> the requests were never counted at all, so the only way to see them is to bring your own attempt counter. A retry storm inflates the provider's request count; a 529 never reaches it.</p>""",
"steps": [
 {"h": "Pull fourteen days of hourly buckets, grouped",
  "body": """<p><code>bucket_width=1h</code> with <code>group_by=model</code> and <code>group_by=project_id</code>, paging on <code>next_page</code> until it stops. Hourly rather than daily because the ratio you are about to compute is meaningless if a busy hour and an idle one are averaged together first, and grouped because a storm in one worker is invisible in an organization total.</p>"""},
 {"h": "Throw away the hour the clock is still inside",
  "body": """<p>The newest bucket is always partial. Leave it in and every run before the hour is up reports a decline, which is the fastest way to teach a team to ignore a scheduled report. Drop it, and compare whole hours only.</p>"""},
 {"h": "Compute both growth rates, then the ratio between them",
  "body": """<p>Requests last week over requests the week before; the same for input plus output tokens. Then divide one growth rate by the other. A factor above two &mdash; request growth outpacing token growth by more than double &mdash; is the threshold this note is built on, and it is a starting point rather than a law.</p>"""},
 {"h": "Look at where in the week the surplus requests landed",
  "body": """<p>Report <code>(input + output) / num_model_requests</code> for each window, because it is the number a reader recognises &mdash; but do not treat it as a second opinion, since it is the first one inverted. The independent test is concentration: the share of the recent window's requests falling in its busiest tenth of hours. Around a tenth means even traffic. Most of them means the surplus arrived in bursts, which is what retries do.</p>"""},
 {"h": "Print the retry layering, not a rate-limit increase",
  "body": """<p>The repair is to collapse to a single layer: set <code>max_retries</code> explicitly on the SDK client and delete the outer wrapper, or set it to zero and keep the wrapper, with exponential backoff, jitter, and a circuit breaker so a sustained failure stops re-amplifying. Raising the project's RPM is printed too, second and clearly marked, because doing it first buys a fortnight and hides the cause.</p>"""},
],
"verify": """<p>Re-run a week after the retry layers are collapsed. Requests should fall back toward the token series and tokens per request should climb back to roughly where it was.</p>
<pre><code class="language-bash">python3 openai_retry_storm_shape.py --days 14
# retry-storm  proj_ingest / gpt-5.1  requests x3.04, tokens x1.00, tokens per request 5000 then 1647; 67% of the surplus landed in the busiest 10% of hours
#   hourly mean sits at 82% of the RPM ceiling and 9% of the TPM ceiling
#   repair: collapse to one retry layer. Set max_retries on the client and remove the outer wrapper.
# 7 model/project series checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET for both series, and a second only when there is a finding to attribute. Eight pure functions: the series builder, which keeps each bucket rather than a total; the window fold, which drops the partial hour and splits on a cutoff; the growth ratio, which returns nothing rather than infinity when there is no prior week; the mean call size; the divergence ratio, whose docstring admits it is the same statement as the mean call size inverted; the concentration measure that is therefore the only independent evidence; the classifier; and the limiter comparison, which is honest that an hourly mean is a floor on the peak and not the peak.",
"py_file": "openai_retry_storm_shape.py",
"py": '''"""Report OpenAI request volume growing faster than the tokens it carries.

Read only. One GET against the organization usage report, plus one per finding
against the project rate limits. Both need an organization admin key
(sk-admin-), which can be provisioned read-only.

Everything here comes from the provider's own numbers: num_model_requests and
the token counts arrive on the same result object, so no telemetry of your own
is required. Requests climbing while tokens stay flat, with the mean call size
collapsing underneath, is the retry-storm signature and nothing else makes it.

The repair is printed, never performed. Retry layering lives in your client.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_retry_storm_shape")

API = "https://api.openai.com/v1"

FINDINGS = ("retry-storm", "requests-outpacing-tokens")


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def series(buckets):
    """Per (project, model), the hourly points. Pure.

    Buckets are kept rather than totalled, because the whole method is a
    comparison between two halves of the window and a sum has already thrown
    the halves away.
    """
    out = {}
    for bucket in buckets or []:
        start = _int(bucket.get("start_time"))
        for result in bucket.get("results") or []:
            key = (str(result.get("project_id") or "unknown"),
                   str(result.get("model") or "unknown"))
            out.setdefault(key, []).append({
                "start": start,
                "requests": _int(result.get("num_model_requests")),
                "tokens": (_int(result.get("input_tokens"))
                           + _int(result.get("output_tokens"))),
            })
    for points in out.values():
        points.sort(key=lambda p: p["start"])
    return out


def fold_windows(points, cutoff, partial_after=None):
    """Sum one series into (prior, recent) either side of a cutoff. Pure.

    Points at or after partial_after are dropped. The hour the clock is still
    inside is always short, and a growth ratio computed with it in reports a
    decline every single time the job runs before the hour is up.
    """
    prior = {"requests": 0, "tokens": 0, "buckets": 0}
    recent = {"requests": 0, "tokens": 0, "buckets": 0}
    for point in points or []:
        start = _int(point.get("start"))
        if partial_after is not None and start >= partial_after:
            continue
        window = recent if start >= cutoff else prior
        window["requests"] += _int(point.get("requests"))
        window["tokens"] += _int(point.get("tokens"))
        window["buckets"] += 1
    return prior, recent


def growth(prior_value, recent_value):
    """recent / prior, or None when there is nothing to divide by. Pure.

    None rather than infinity. A workload that did not exist last week has no
    growth rate, and reporting one as an enormous number puts every new
    deployment at the top of the report.
    """
    prior_value = float(prior_value or 0)
    if prior_value <= 0:
        return None
    return float(recent_value or 0) / prior_value


def tokens_per_request(window):
    """Mean tokens per request in one window, or None. Pure."""
    made = _int((window or {}).get("requests"))
    if made <= 0:
        return None
    return _int(window.get("tokens")) / float(made)


def divergence_ratio(prior, recent):
    """Request growth divided by token growth. Pure. None when unavailable.

    Worth stating in the code rather than only in the prose: this number is
    exactly the reciprocal of the change in tokens per request. The first
    version of this script tested both and read them as two agreeing witnesses.
    They are one witness stated twice, so the corroboration has to come from
    somewhere else, which is what burstiness() is for.
    """
    request_growth = growth(_int((prior or {}).get("requests")),
                            _int((recent or {}).get("requests")))
    token_growth = growth(_int((prior or {}).get("tokens")),
                          _int((recent or {}).get("tokens")))
    if request_growth is None or token_growth is None or token_growth <= 0:
        return None
    return request_growth / token_growth


def burstiness(points, cutoff, partial_after=None, top_share=0.1, min_buckets=24):
    """Share of the recent window's requests in its busiest hours. Pure.

    The busiest top_share of hours, by request count. Evenly spread traffic
    puts about top_share of its requests there. A retry storm puts most of them
    there, because retries amplify during the failures that caused them, and
    that concentration is the only evidence in this report that is independent
    of the growth ratio.

    None when there are too few hours for the share to mean anything.
    """
    recent = []
    for point in points or []:
        start = _int(point.get("start"))
        if partial_after is not None and start >= partial_after:
            continue
        if start >= cutoff:
            recent.append(_int(point.get("requests")))
    if len(recent) < min_buckets:
        return None
    total = sum(recent)
    if total <= 0:
        return None
    top = max(1, int(round(len(recent) * top_share)))
    return sum(sorted(recent, reverse=True)[:top]) / float(total)


def classify(prior, recent, burst=None, divergence=2.0, min_requests=1000,
             burst_floor=0.35):
    """Compare two windows of one series. Pure. Returns (state, detail).

    Four ways two series can move relative to each other, and only one of them
    is a retry storm. The divergence says the request count grew on its own;
    the burst share says whether it grew in the shape retries have.
    """
    prior = prior or {}
    recent = recent or {}
    prior_requests = _int(prior.get("requests"))
    recent_requests = _int(recent.get("requests"))

    if prior_requests < min_requests and recent_requests < min_requests:
        return ("too-little-traffic",
                "%d request(s) then %d, both under the floor of %d"
                % (prior_requests, recent_requests, min_requests))

    request_growth = growth(prior_requests, recent_requests)
    token_growth = growth(_int(prior.get("tokens")), _int(recent.get("tokens")))
    if request_growth is None or token_growth is None:
        return ("new-workload",
                "nothing in the prior window to compare against: %d request(s) "
                "and %d token(s) appeared this week"
                % (recent_requests, _int(recent.get("tokens"))))

    before = tokens_per_request(prior) or 0.0
    after = tokens_per_request(recent) or 0.0
    shape = ("requests x%.2f, tokens x%.2f, tokens per request %d then %d"
             % (request_growth, token_growth, before, after))
    if burst is not None:
        shape += ("; %.0f%% of the surplus landed in the busiest 10%% of hours"
                  % (burst * 100))

    if request_growth >= divergence * token_growth:
        if burst is None:
            return ("retry-storm",
                    shape + ". Too few hourly buckets to measure how "
                    "concentrated the surplus was, so this rests on the growth "
                    "ratio alone.")
        if burst < burst_floor:
            return ("requests-outpacing-tokens",
                    shape + ". The extra calls are spread evenly across the "
                    "hours rather than piled into a few, which is a workload "
                    "that got shorter rather than one being retried.")
        return ("retry-storm",
                shape + ". The surplus arrived in bursts, which is what "
                "retries do: they amplify during the failures that caused "
                "them.")

    if token_growth >= divergence * request_growth:
        return ("prompts-grew",
                shape + ". Tokens moved and the call count did not, so this is "
                "prompt or answer length, not call volume.")

    if request_growth >= 1.25 and token_growth >= 1.25:
        return ("traffic-growth",
                shape + ". Both series moved together, which is traffic rather "
                "than amplification.")

    if request_growth <= 0.75:
        return ("quieter", shape + ". Fewer calls than the week before.")

    return ("steady", shape + ".")


def rate_limit_values(payload, model):
    """The RPM and TPM this project publishes for a model. Pure.

    Longest matching prefix wins, so a dated id resolves to the most specific
    entry that claims it rather than to whichever one came back first.
    """
    best_key, best_len = None, -1
    name = str(model or "").strip().lower()
    for entry in (payload or {}).get("data") or []:
        candidate = str(entry.get("model") or "").strip().lower()
        if not candidate:
            continue
        if name == candidate or name.startswith(candidate):
            if len(candidate) > best_len:
                best_key, best_len = entry, len(candidate)
    if best_key is None:
        return {"requests": None, "tokens": None}
    out = {}
    for field, key in (("max_requests_per_1_minute", "requests"),
                       ("max_tokens_per_1_minute", "tokens")):
        try:
            out[key] = int(best_key.get(field))
        except (TypeError, ValueError):
            out[key] = None
    return out


def limiter_pressure(window, hours, limits, near=0.7, idle=0.3):
    """Where a window's mean traffic sits against RPM and TPM. Pure.

    Hourly buckets cannot resolve a minute, so this is the hourly mean spread
    across sixty minutes: a floor on the real peak and never the peak itself.
    If even the mean is near the ceiling then the peak went past it long ago,
    which is all this needs to say.
    """
    limits = limits or {}
    rpm_limit = limits.get("requests")
    tpm_limit = limits.get("tokens")
    minutes = max(1, int(hours or 0) * 60)
    if not rpm_limit and not tpm_limit:
        return ("no-limits-published",
                "this project publishes no rate limit for the model, so there "
                "is no ceiling to compare the mean against")

    rpm_used = (_int((window or {}).get("requests")) / float(minutes) / rpm_limit
                if rpm_limit else None)
    tpm_used = (_int((window or {}).get("tokens")) / float(minutes) / tpm_limit
                if tpm_limit else None)
    shape = "hourly mean sits at %s of the RPM ceiling and %s of the TPM ceiling" % (
        "%.0f%%" % (rpm_used * 100) if rpm_used is not None else "an unpublished share",
        "%.0f%%" % (tpm_used * 100) if tpm_used is not None else "an unpublished share")

    if rpm_used is not None and tpm_used is not None:
        if rpm_used >= near and tpm_used <= idle:
            return ("rpm-bound-tpm-idle",
                    shape + ", which is what amplification looks like from the "
                    "limiter side: the request bucket fills and the token "
                    "bucket does not")
        if rpm_used >= near and tpm_used >= near:
            return ("both-near", shape + ", so both limiters are under pressure")
        if tpm_used >= near:
            return ("tpm-bound",
                    shape + ", so the token limiter is the binding one and this "
                    "is volume rather than retries")
    return ("headroom", shape)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk the usage report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="days to read, split into two halves (default 14)")
    ap.add_argument("--divergence", type=float, default=2.0,
                    help="how far request growth must outpace token growth "
                         "(default 2.0)")
    ap.add_argument("--min-requests", type=int, default=1000,
                    help="ignore series below this many requests (default 1000)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print series that moved together")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key; read-only "
                  "scopes are enough)")
        return 2

    days = max(2, min(int(args.days), 30))
    half = days // 2
    now = int(time.time())
    start = now - days * 86400
    cutoff = now - half * 86400
    partial_after = now - (now % 3600)

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    buckets = pages(session, "/organization/usage/completions", {
        "start_time": start,
        "bucket_width": "1h",
        "limit": 168,
        "group_by": ["model", "project_id"],
    })
    rows = series(buckets)
    if not rows:
        log.info("no completions usage in the last %d day(s)", days)
        return 0

    checked = 0
    bad = 0
    for project, model in sorted(rows):
        points = rows[(project, model)]
        prior, recent = fold_windows(points, cutoff, partial_after)
        burst = burstiness(points, cutoff, partial_after)
        state, detail = classify(prior, recent, burst, args.divergence,
                                 min_requests=args.min_requests)
        checked += 1
        line = "%-26s %s / %s  %s" % (state, project, model, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            limits = {"requests": None, "tokens": None}
            if project != "unknown":
                try:
                    limits = rate_limit_values(
                        get(session, "/organization/projects/%s/rate_limits" % project,
                            {"limit": 100}), model)
                except (requests.RequestException, SystemExit):
                    limits = {"requests": None, "tokens": None}
            _, pressure = limiter_pressure(recent, half * 24, limits)
            log.warning("  %s", pressure)
            if state == "retry-storm":
                log.warning("  repair: collapse to one retry layer. Set "
                            "max_retries explicitly on the SDK client and "
                            "remove the outer wrapper, or set it to 0 and keep "
                            "the wrapper. Exponential backoff with jitter, and "
                            "a circuit breaker so a sustained failure stops "
                            "re-amplifying.")
                log.warning("  repair: raising the project rate limit is the "
                            "second measure, not the first. An admin can call "
                            "POST /v1/organization/projects/{project_id}"
                            "/rate_limits/{rate_limit_id} once the layering is "
                            "fixed. It is printed here, not run.")
            else:
                log.warning("  repair: nothing yet. Confirm the shorter calls "
                            "are a real workload before changing any retry "
                            "policy, and re-run next week.")
        elif args.show_all:
            log.info(line)

    log.info("%d model/project series checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-retry-storm-shape.mjs",
"js": '''/**
 * Report OpenAI request volume growing faster than the tokens it carries.
 *
 * Read only. One GET against the organization usage report, plus one per
 * finding against the project rate limits. Both need an organization admin key
 * (sk-admin-), which can be provisioned read-only.
 *
 * Both series come off the provider's own report, so no telemetry of your own
 * is required. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

const FINDINGS = new Set(['retry-storm', 'requests-outpacing-tokens']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Per (project, model), the hourly points. Pure.
 * Buckets are kept rather than totalled: the method is a comparison between
 * two halves of the window, and a sum has already thrown the halves away.
 */
export function series(buckets) {
  const out = new Map();
  for (const bucket of buckets ?? []) {
    const start = readInt(bucket?.start_time);
    for (const result of bucket?.results ?? []) {
      const key = `${result?.project_id ?? 'unknown'}\\u0000${result?.model ?? 'unknown'}`;
      if (!out.has(key)) {
        out.set(key, { project: String(result?.project_id ?? 'unknown'),
                       model: String(result?.model ?? 'unknown'), points: [] });
      }
      out.get(key).points.push({
        start,
        requests: readInt(result?.num_model_requests),
        tokens: readInt(result?.input_tokens) + readInt(result?.output_tokens),
      });
    }
  }
  for (const row of out.values()) row.points.sort((a, b) => a.start - b.start);
  return out;
}

/**
 * Sum one series into [prior, recent] either side of a cutoff. Pure.
 * Points at or after partialAfter are dropped: the hour the clock is still
 * inside is always short, and leaving it in reports a decline every run.
 */
export function foldWindows(points, cutoff, partialAfter = null) {
  const prior = { requests: 0, tokens: 0, buckets: 0 };
  const recent = { requests: 0, tokens: 0, buckets: 0 };
  for (const point of points ?? []) {
    const start = readInt(point?.start);
    if (partialAfter !== null && partialAfter !== undefined && start >= partialAfter) continue;
    const window = start >= cutoff ? recent : prior;
    window.requests += readInt(point?.requests);
    window.tokens += readInt(point?.tokens);
    window.buckets += 1;
  }
  return [prior, recent];
}

/**
 * recent / prior, or null when there is nothing to divide by. Pure.
 * Null rather than Infinity: a workload that did not exist last week has no
 * growth rate, and a huge number would put every new deployment on top.
 */
export function growth(priorValue, recentValue) {
  const prior = Number(priorValue ?? 0);
  if (!(prior > 0)) return null;
  return Number(recentValue ?? 0) / prior;
}

/** Mean tokens per request in one window, or null. Pure. */
export function tokensPerRequest(window) {
  const made = readInt(window?.requests);
  if (made <= 0) return null;
  return readInt(window?.tokens) / made;
}

/**
 * Request growth divided by token growth. Pure. Null when unavailable.
 * This number is exactly the reciprocal of the change in tokens per request.
 * The first version of this script tested both and read them as two agreeing
 * witnesses; they are one witness stated twice, which is why burstiness exists.
 */
export function divergenceRatio(prior, recent) {
  const requestGrowth = growth(readInt(prior?.requests), readInt(recent?.requests));
  const tokenGrowth = growth(readInt(prior?.tokens), readInt(recent?.tokens));
  if (requestGrowth === null || tokenGrowth === null || tokenGrowth <= 0) return null;
  return requestGrowth / tokenGrowth;
}

/**
 * Share of the recent window's requests in its busiest hours. Pure.
 * Evenly spread traffic puts about topShare of its requests there; a retry
 * storm puts most of them there, because retries amplify during the failures
 * that caused them. Null when there are too few hours to mean anything.
 */
export function burstiness(points, cutoff, partialAfter = null, topShare = 0.1,
                           minBuckets = 24) {
  const recent = [];
  for (const point of points ?? []) {
    const start = readInt(point?.start);
    if (partialAfter !== null && partialAfter !== undefined && start >= partialAfter) continue;
    if (start >= cutoff) recent.push(readInt(point?.requests));
  }
  if (recent.length < minBuckets) return null;
  const total = recent.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;
  const top = Math.max(1, Math.round(recent.length * topShare));
  const head = [...recent].sort((a, b) => b - a).slice(0, top);
  return head.reduce((a, b) => a + b, 0) / total;
}

/**
 * Compare two windows of one series. Pure. Returns [state, detail].
 * The divergence says the request count grew on its own; the burst share says
 * whether it grew in the shape retries have.
 */
export function classify(prior, recent, burst = null, divergence = 2.0,
                         minRequests = 1000, burstFloor = 0.35) {
  const priorRequests = readInt(prior?.requests);
  const recentRequests = readInt(recent?.requests);

  if (priorRequests < minRequests && recentRequests < minRequests) {
    return ['too-little-traffic',
      `${priorRequests} request(s) then ${recentRequests}, both under the ` +
      `floor of ${minRequests}`];
  }

  const requestGrowth = growth(priorRequests, recentRequests);
  const tokenGrowth = growth(readInt(prior?.tokens), readInt(recent?.tokens));
  if (requestGrowth === null || tokenGrowth === null) {
    return ['new-workload',
      `nothing in the prior window to compare against: ${recentRequests} ` +
      `request(s) and ${readInt(recent?.tokens)} token(s) appeared this week`];
  }

  const before = tokensPerRequest(prior) ?? 0;
  const after = tokensPerRequest(recent) ?? 0;
  let shape = `requests x${requestGrowth.toFixed(2)}, tokens x` +
    `${tokenGrowth.toFixed(2)}, tokens per request ${Math.trunc(before)} then ` +
    `${Math.trunc(after)}`;
  if (burst !== null && burst !== undefined) {
    shape += `; ${(burst * 100).toFixed(0)}% of the surplus landed in the ` +
      'busiest 10% of hours';
  }

  if (requestGrowth >= divergence * tokenGrowth) {
    if (burst === null || burst === undefined) {
      return ['retry-storm',
        `${shape}. Too few hourly buckets to measure how concentrated the ` +
        'surplus was, so this rests on the growth ratio alone.'];
    }
    if (burst < burstFloor) {
      return ['requests-outpacing-tokens',
        `${shape}. The extra calls are spread evenly across the hours rather ` +
        'than piled into a few, which is a workload that got shorter rather ' +
        'than one being retried.'];
    }
    return ['retry-storm',
      `${shape}. The surplus arrived in bursts, which is what retries do: they ` +
      'amplify during the failures that caused them.'];
  }

  if (tokenGrowth >= divergence * requestGrowth) {
    return ['prompts-grew',
      `${shape}. Tokens moved and the call count did not, so this is prompt ` +
      'or answer length, not call volume.'];
  }

  if (requestGrowth >= 1.25 && tokenGrowth >= 1.25) {
    return ['traffic-growth',
      `${shape}. Both series moved together, which is traffic rather than ` +
      'amplification.'];
  }

  if (requestGrowth <= 0.75) {
    return ['quieter', `${shape}. Fewer calls than the week before.`];
  }

  return ['steady', `${shape}.`];
}

/** The RPM and TPM this project publishes for a model. Pure. Longest prefix wins. */
export function rateLimitValues(payload, model) {
  const name = String(model ?? '').trim().toLowerCase();
  let best = null;
  let bestLen = -1;
  for (const entry of payload?.data ?? []) {
    const candidate = String(entry?.model ?? '').trim().toLowerCase();
    if (!candidate) continue;
    if ((name === candidate || name.startsWith(candidate)) && candidate.length > bestLen) {
      best = entry;
      bestLen = candidate.length;
    }
  }
  if (best === null) return { requests: null, tokens: null };
  const read = (field) => {
    const n = Number(best[field]);
    return Number.isFinite(n) ? Math.trunc(n) : null;
  };
  return { requests: read('max_requests_per_1_minute'),
           tokens: read('max_tokens_per_1_minute') };
}

/**
 * Where a window's mean traffic sits against RPM and TPM. Pure.
 * An hourly mean spread across sixty minutes is a floor on the real peak and
 * never the peak itself, which is all this needs to be.
 */
export function limiterPressure(window, hours, limits, near = 0.7, idle = 0.3) {
  const rpmLimit = limits?.requests;
  const tpmLimit = limits?.tokens;
  const minutes = Math.max(1, readInt(hours) * 60);
  if (!rpmLimit && !tpmLimit) {
    return ['no-limits-published',
      'this project publishes no rate limit for the model, so there is no ' +
      'ceiling to compare the mean against'];
  }

  const rpmUsed = rpmLimit ? readInt(window?.requests) / minutes / rpmLimit : null;
  const tpmUsed = tpmLimit ? readInt(window?.tokens) / minutes / tpmLimit : null;
  const pct = (v) => (v === null ? 'an unpublished share' : `${(v * 100).toFixed(0)}%`);
  const shape = `hourly mean sits at ${pct(rpmUsed)} of the RPM ceiling and ` +
    `${pct(tpmUsed)} of the TPM ceiling`;

  if (rpmUsed !== null && tpmUsed !== null) {
    if (rpmUsed >= near && tpmUsed <= idle) {
      return ['rpm-bound-tpm-idle',
        `${shape}, which is what amplification looks like from the limiter ` +
        'side: the request bucket fills and the token bucket does not'];
    }
    if (rpmUsed >= near && tpmUsed >= near) {
      return ['both-near', `${shape}, so both limiters are under pressure`];
    }
    if (tpmUsed >= near) {
      return ['tpm-bound',
        `${shape}, so the token limiter is the binding one and this is volume ` +
        'rather than retries'];
    }
  }
  return ['headroom', shape];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* pages(key, path, params, maxPages = 40) {
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    for (const bucket of page?.data ?? []) yield bucket;
    if (!page?.has_more || !page?.next_page) return;
    query = { ...params, page: page.next_page };
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key; read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(2, Math.min(Number(process.env.DAYS ?? 14), 30));
  const half = Math.floor(days / 2);
  const now = Math.floor(Date.now() / 1000);
  const cutoff = now - half * 86400;
  const partialAfter = now - (now % 3600);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of pages(admin, '/organization/usage/completions', {
    start_time: now - days * 86400,
    bucket_width: '1h',
    limit: 168,
    group_by: ['model', 'project_id'],
  })) buckets.push(bucket);

  const rows = series(buckets);
  if (rows.size === 0) {
    console.log(`no completions usage in the last ${days} day(s)`);
    return;
  }

  let checked = 0;
  let bad = 0;
  for (const row of [...rows.values()].sort((a, b) =>
    `${a.project}${a.model}`.localeCompare(`${b.project}${b.model}`))) {
    const [prior, recent] = foldWindows(row.points, cutoff, partialAfter);
    const burst = burstiness(row.points, cutoff, partialAfter);
    const [state, detail] = classify(prior, recent, burst);
    checked += 1;
    const line = `${state.padEnd(26)} ${row.project} / ${row.model}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      let limits = { requests: null, tokens: null };
      if (row.project !== 'unknown') {
        try {
          limits = rateLimitValues(
            await get(admin, `/organization/projects/${row.project}/rate_limits`,
                      { limit: 100 }), row.model);
        } catch {
          limits = { requests: null, tokens: null };
        }
      }
      const [, pressure] = limiterPressure(recent, half * 24, limits);
      console.warn(`  ${pressure}`);
      if (state === 'retry-storm') {
        console.warn('  repair: collapse to one retry layer. Set max_retries ' +
                     'explicitly on the SDK client and remove the outer wrapper, ' +
                     'or set it to 0 and keep the wrapper. Exponential backoff ' +
                     'with jitter, and a circuit breaker so a sustained failure ' +
                     'stops re-amplifying.');
        console.warn('  repair: raising the project rate limit is the second ' +
                     'measure, not the first. An admin can call POST ' +
                     '/v1/organization/projects/{project_id}/rate_limits/' +
                     '{rate_limit_id} once the layering is fixed. It is printed ' +
                     'here, not run.');
      } else {
        console.warn('  repair: nothing yet. Confirm the shorter calls are a ' +
                     'real workload before changing any retry policy, and ' +
                     're-run next week.');
      }
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${checked} model/project series checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two tests carry this note and they are deliberately a pair: two fortnights with byte-identical weekly arithmetic &mdash; three times the requests, no more tokens, the mean call down from five thousand to sixteen hundred &mdash; where one piles its surplus into eighteen hours and the other spreads it across all hundred and sixty-eight. One is a retry storm and one is a workload that got shorter, and nothing in the weekly totals can tell them apart. A third test asserts the embarrassing identity that forced the rewrite: the divergence ratio is the change in mean call size inverted, so it can never be a second opinion. The rest pin the partial hour, the new workload that must not report infinite growth, and the limiter reading that names a full request bucket beside an empty token one.",
"test_py_file": "test_openai_retry_storm_shape.py",
"test_py": '''from openai_retry_storm_shape import (burstiness, classify, divergence_ratio,
                                       fold_windows, growth, limiter_pressure,
                                       rate_limit_values, series,
                                       tokens_per_request)

CUTOFF = 1_000_000
HOUR = 3600


def hours(start, count, requests_each, tokens_each):
    return [{"start": start + i * HOUR, "requests": requests_each,
             "tokens": tokens_each} for i in range(count)]


PRIOR_WEEK = hours(CUTOFF - 168 * HOUR, 168, 1000, 5_000_000)
# Same weekly totals, two different shapes. The storm piles its surplus into
# eighteen hours; the short workload spreads the identical surplus evenly.
STORM = (hours(CUTOFF, 150, 1000, 5_000_000)
         + hours(CUTOFF + 150 * HOUR, 18, 20_000, 5_000_000))
EVEN = hours(CUTOFF, 168, 3000, 5_000_000)


def test_requests_climb_in_bursts_while_tokens_stand_still():
    # The note in one assertion. Three times the calls, no more tokens, the
    # mean call down from 5000 to 1647, and two thirds of the surplus landing
    # in the busiest tenth of the hours.
    prior, recent = fold_windows(PRIOR_WEEK + STORM, CUTOFF)
    assert prior["requests"] == 168_000 and prior["tokens"] == 840_000_000
    assert recent["requests"] == 510_000 and recent["tokens"] == 840_000_000
    assert round(growth(prior["requests"], recent["requests"]), 3) == 3.036
    assert growth(prior["tokens"], recent["tokens"]) == 1.0
    assert int(tokens_per_request(prior)) == 5000
    assert int(tokens_per_request(recent)) == 1647

    burst = burstiness(PRIOR_WEEK + STORM, CUTOFF)
    assert round(burst, 3) == 0.667
    state, detail = classify(prior, recent, burst)
    assert state == "retry-storm"
    assert "requests x3.04, tokens x1.00" in detail
    assert "tokens per request 5000 then 1647" in detail
    assert "67% of the surplus landed in the busiest 10% of hours" in detail


def test_the_same_ratios_spread_evenly_are_not_a_storm():
    # Identical weekly arithmetic, opposite conclusion. This pair is the reason
    # the concentration measure exists at all.
    prior, recent = fold_windows(PRIOR_WEEK + EVEN, CUTOFF)
    assert round(divergence_ratio(prior, recent), 2) == 3.0
    burst = burstiness(PRIOR_WEEK + EVEN, CUTOFF)
    assert round(burst, 3) == 0.101
    state, detail = classify(prior, recent, burst)
    assert state == "requests-outpacing-tokens"
    assert "spread evenly across the hours" in detail


def test_the_divergence_ratio_is_the_mean_call_size_inverted():
    # Stated as a test because the first draft treated these as two agreeing
    # signals. They cannot disagree.
    prior, recent = fold_windows(PRIOR_WEEK + STORM, CUTOFF)
    identity = tokens_per_request(prior) / tokens_per_request(recent)
    assert round(divergence_ratio(prior, recent), 9) == round(identity, 9)


def test_a_real_customer_moves_both_series_together():
    state, detail = classify({"requests": 100_000, "tokens": 500_000_000},
                             {"requests": 300_000, "tokens": 1_500_000_000}, 0.1)
    assert state == "traffic-growth"
    assert "moved together" in detail


def test_a_prompt_that_grew_moves_only_the_token_series():
    state, _ = classify({"requests": 100_000, "tokens": 200_000_000},
                        {"requests": 100_000, "tokens": 600_000_000}, 0.1)
    assert state == "prompts-grew"


def test_the_partial_hour_is_dropped_before_anything_is_divided():
    tail = [{"start": CUTOFF + 200 * HOUR, "requests": 1, "tokens": 10}]
    prior, recent = fold_windows(PRIOR_WEEK + EVEN + tail, CUTOFF,
                                 partial_after=CUTOFF + 200 * HOUR)
    assert recent["buckets"] == 168 and recent["requests"] == 504_000
    assert burstiness(EVEN + tail, CUTOFF, partial_after=CUTOFF + 200 * HOUR) \\
        == burstiness(EVEN, CUTOFF)


def test_a_workload_with_no_prior_week_has_no_growth_rate():
    assert growth(0, 5000) is None
    assert growth(None, 5000) is None
    assert divergence_ratio({"requests": 1, "tokens": 0},
                            {"requests": 2, "tokens": 0}) is None
    assert tokens_per_request({"requests": 0, "tokens": 0}) is None
    state, _ = classify({"requests": 0, "tokens": 0},
                        {"requests": 40_000, "tokens": 90_000_000})
    assert state == "new-workload"
    assert classify({"requests": 10, "tokens": 900},
                    {"requests": 12, "tokens": 1000})[0] == "too-little-traffic"


def test_too_few_hours_reports_no_concentration_rather_than_a_wrong_one():
    short = [{"start": CUTOFF + i * HOUR, "requests": 10, "tokens": 1}
             for i in range(6)]
    assert burstiness(short, CUTOFF) is None
    assert burstiness([], CUTOFF) is None
    state, detail = classify({"requests": 100_000, "tokens": 500_000_000},
                             {"requests": 400_000, "tokens": 520_000_000})
    assert state == "retry-storm"
    assert "Too few hourly buckets" in detail


def test_the_request_bucket_is_full_while_the_token_bucket_is_empty():
    payload = {"data": [{"model": "gpt-5.1", "max_requests_per_1_minute": 10_000,
                         "max_tokens_per_1_minute": 20_000_000},
                        {"model": "gpt-5", "max_requests_per_1_minute": 1,
                         "max_tokens_per_1_minute": 1}]}
    limits = rate_limit_values(payload, "gpt-5.1-2026-01-15")
    assert limits == {"requests": 10_000, "tokens": 20_000_000}

    state, detail = limiter_pressure(
        {"requests": 82_656_000, "tokens": 18_144_000_000}, 168, limits)
    assert state == "rpm-bound-tpm-idle"
    assert "82% of the RPM ceiling and 9% of the TPM ceiling" in detail


def test_an_unpublished_limit_is_not_a_missing_one():
    assert rate_limit_values({"data": []}, "gpt-5.1") == {"requests": None,
                                                          "tokens": None}
    assert limiter_pressure({"requests": 1}, 24, None)[0] == "no-limits-published"
    assert series([]) == {}
    assert series(None) == {}
''',
"test_js_file": "openai-retry-storm-shape.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { burstiness, classify, divergenceRatio, foldWindows, growth,
         limiterPressure, rateLimitValues, series, tokensPerRequest }
  from './openai-retry-storm-shape.mjs';

const CUTOFF = 1000000;
const HOUR = 3600;

const hours = (start, count, requests, tokens) =>
  Array.from({ length: count }, (_, i) => ({ start: start + i * HOUR, requests, tokens }));

const PRIOR_WEEK = hours(CUTOFF - 168 * HOUR, 168, 1000, 5000000);
// Same weekly totals, two different shapes.
const STORM = [...hours(CUTOFF, 150, 1000, 5000000),
               ...hours(CUTOFF + 150 * HOUR, 18, 20000, 5000000)];
const EVEN = hours(CUTOFF, 168, 3000, 5000000);

test('requests climb in bursts while tokens stand still', () => {
  const [prior, recent] = foldWindows([...PRIOR_WEEK, ...STORM], CUTOFF);
  assert.equal(prior.requests, 168000);
  assert.equal(prior.tokens, 840000000);
  assert.equal(recent.requests, 510000);
  assert.equal(recent.tokens, 840000000);
  assert.equal(Number(growth(prior.requests, recent.requests).toFixed(3)), 3.036);
  assert.equal(growth(prior.tokens, recent.tokens), 1);
  assert.equal(Math.trunc(tokensPerRequest(prior)), 5000);
  assert.equal(Math.trunc(tokensPerRequest(recent)), 1647);

  const burst = burstiness([...PRIOR_WEEK, ...STORM], CUTOFF);
  assert.equal(Number(burst.toFixed(3)), 0.667);
  const [state, detail] = classify(prior, recent, burst);
  assert.equal(state, 'retry-storm');
  assert.match(detail, /requests x3\\.04, tokens x1\\.00/);
  assert.match(detail, /tokens per request 5000 then 1647/);
  assert.match(detail, /67% of the surplus landed in the busiest 10% of hours/);
});

test('the same ratios spread evenly are not a storm', () => {
  const [prior, recent] = foldWindows([...PRIOR_WEEK, ...EVEN], CUTOFF);
  assert.equal(Number(divergenceRatio(prior, recent).toFixed(2)), 3);
  const burst = burstiness([...PRIOR_WEEK, ...EVEN], CUTOFF);
  assert.equal(Number(burst.toFixed(3)), 0.101);
  const [state, detail] = classify(prior, recent, burst);
  assert.equal(state, 'requests-outpacing-tokens');
  assert.match(detail, /spread evenly across the hours/);
});

test('the divergence ratio is the mean call size inverted', () => {
  const [prior, recent] = foldWindows([...PRIOR_WEEK, ...STORM], CUTOFF);
  const identity = tokensPerRequest(prior) / tokensPerRequest(recent);
  assert.equal(divergenceRatio(prior, recent).toFixed(9), identity.toFixed(9));
});

test('a real customer moves both series together', () => {
  const [state, detail] = classify({ requests: 100000, tokens: 500000000 },
                                   { requests: 300000, tokens: 1500000000 }, 0.1);
  assert.equal(state, 'traffic-growth');
  assert.match(detail, /moved together/);
});

test('a prompt that grew moves only the token series', () => {
  const [state] = classify({ requests: 100000, tokens: 200000000 },
                           { requests: 100000, tokens: 600000000 }, 0.1);
  assert.equal(state, 'prompts-grew');
});

test('the partial hour is dropped before anything is divided', () => {
  const tail = [{ start: CUTOFF + 200 * HOUR, requests: 1, tokens: 10 }];
  const [, recent] = foldWindows([...PRIOR_WEEK, ...EVEN, ...tail], CUTOFF,
                                 CUTOFF + 200 * HOUR);
  assert.equal(recent.buckets, 168);
  assert.equal(recent.requests, 504000);
  assert.equal(burstiness([...EVEN, ...tail], CUTOFF, CUTOFF + 200 * HOUR),
               burstiness(EVEN, CUTOFF));
});

test('a workload with no prior week has no growth rate', () => {
  assert.equal(growth(0, 5000), null);
  assert.equal(growth(null, 5000), null);
  assert.equal(divergenceRatio({ requests: 1, tokens: 0 },
                               { requests: 2, tokens: 0 }), null);
  assert.equal(tokensPerRequest({ requests: 0, tokens: 0 }), null);
  assert.equal(classify({ requests: 0, tokens: 0 },
                        { requests: 40000, tokens: 90000000 })[0], 'new-workload');
  assert.equal(classify({ requests: 10, tokens: 900 },
                        { requests: 12, tokens: 1000 })[0], 'too-little-traffic');
});

test('too few hours reports no concentration rather than a wrong one', () => {
  const short = Array.from({ length: 6 },
    (_, i) => ({ start: CUTOFF + i * HOUR, requests: 10, tokens: 1 }));
  assert.equal(burstiness(short, CUTOFF), null);
  assert.equal(burstiness([], CUTOFF), null);
  const [state, detail] = classify({ requests: 100000, tokens: 500000000 },
                                   { requests: 400000, tokens: 520000000 });
  assert.equal(state, 'retry-storm');
  assert.match(detail, /Too few hourly buckets/);
});

test('the request bucket is full while the token bucket is empty', () => {
  const payload = { data: [
    { model: 'gpt-5.1', max_requests_per_1_minute: 10000,
      max_tokens_per_1_minute: 20000000 },
    { model: 'gpt-5', max_requests_per_1_minute: 1, max_tokens_per_1_minute: 1 },
  ] };
  const limits = rateLimitValues(payload, 'gpt-5.1-2026-01-15');
  assert.deepEqual(limits, { requests: 10000, tokens: 20000000 });

  const [state, detail] = limiterPressure(
    { requests: 82656000, tokens: 18144000000 }, 168, limits);
  assert.equal(state, 'rpm-bound-tpm-idle');
  assert.match(detail, /82% of the RPM ceiling and 9% of the TPM ceiling/);
});

test('an unpublished limit is not a missing one', () => {
  assert.deepEqual(rateLimitValues({ data: [] }, 'gpt-5.1'),
                   { requests: null, tokens: null });
  assert.equal(limiterPressure({ requests: 1 }, 24, null)[0], 'no-limits-published');
  assert.equal(series([]).size, 0);
  assert.equal(series(null).size, 0);
});
''',
"faq": [
 ("How is this different from watching spend go up?",
  "A cost check folds one series and asks what shape its change is. This one carries two series and asks whether they still agree with each other. They catch different things: a retry storm that triples your request rate might move the invoice by a few percent, because the extra attempts failed early and generated almost nothing, and a prompt that doubled in size moves the invoice sharply without touching the request count at all."),
 ("Why does the token count barely move during a storm?",
  "Because most retried attempts never got as far as generating. A 429 or a connection reset costs you a request against the limiter and produces no tokens, so nine attempts at one logical call bill roughly the tokens of the one that succeeded. That is exactly why the request series is the sensitive one and the token series is the control."),
 ("Could this be a legitimate change in traffic shape?",
  "Yes, and the script keeps that as its own state rather than calling it a storm. A new endpoint doing many small classifications pushes requests up faster than tokens with no amplification anywhere. The weekly ratios cannot separate the two cases, because the drop in tokens per request is the growth divergence restated. What separates them is concentration: the script measures how much of the recent surplus landed in the busiest tenth of the hours, and even traffic puts about a tenth of it there while retries put most of it there."),
 ("Should I raise the rate limit?",
  "Not first. A higher RPM absorbs the amplification for a while and leaves the multiplier in place, so the next incident is larger and arrives with less warning. Collapse the retry layers to one, verify the request series comes back down toward the token series, and then decide whether the ceiling was ever the problem."),
 ("Does Anthropic support the same check?",
  "Not directly. Anthropic's messages usage report carries token sums and no request-count field at all, so there is no request series to compare a token series against. The nearest equivalent on that side is the overload note, which reconstructs the missing count from your own attempt counter instead."),
],
"related": [REL_529, REL_SPIKE, REL_HEADROOM],
"citations": [CITE_OAI_USAGE_COMPLETIONS, CITE_OAI_RATE, CITE_OAI_PROJECT_RATE, CITE_OAI_ADMIN],
},
{
"slug": "overloaded-529-clusters",
"title": "529 overloaded errors arrive in clusters and get dropped",
"description": "Anthropic bills no request count, so 5xx loss shows up only as your own attempt counter minus the work the usage report proves was actually done.",
"h1": "529 overloaded errors arrive in clusters and get dropped",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic 529 overloaded_error", "overloaded_error retry",
             "anthropic 5xx not retried", "attempted vs billed requests",
             "anthropic usage report no request count"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin...), plus a JSON file of the requests your own client attempted, per minute.",
"lead": "Three minutes on a Tuesday afternoon, and about fourteen hundred jobs are simply not in the output table. Nothing crashed. The worker's error counter shows a spike of something it logged as <code>unexpected status</code>, because the client special-cases 429 and 500 and lets everything else fall through to a generic failure path that drops the work. The status was 529, the platform was over capacity for four minutes, and the only trace left is that Anthropic did no work in those minutes while your client believed it was sending plenty.",
"short_answer": """<p>Two numbers, and Anthropic can only supply one of them. Read the per-minute usage buckets with an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={now-4h}&amp;bucket_width=1m&amp;group_by[]=service_tier</code>. Then hand the script your own count of requests attempted, per minute, because that number exists nowhere in the API.</p>
<p>The report has <em>no request-count field at all</em> &mdash; only token sums &mdash; so served requests have to be inferred from the work that was done. Take the median tokens per attempt across the window as a baseline, divide each minute's billed tokens by it to estimate how many attempts were served, and subtract. The remainder is requests that produced nothing.</p>
<p>Then look only at <strong>contiguous runs</strong> of such minutes. A single bad minute is a bucket-boundary artefact: a call that starts at 14:03:58 and finishes at 14:04:06 lands its attempt in one minute and its tokens in the next. A platform capacity condition affects everyone at once and lasts, so it arrives as a run. That is why this note is about clusters rather than about a rate.</p>""",
"problem": """<p>529 is <code>overloaded_error</code>, and the docs are explicit that it happens when the API is under high traffic across all users. It is not caused by your traffic and it is not something a smaller prompt or a lower concurrency avoids. It is retryable, it clusters in time, and the official SDKs already retry it. Hand-rolled clients frequently do not, because the error class list in the code was written from the errors that had been seen so far, and 529 is unusual enough that it was not one of them.</p>
<p>What that produces is silent data loss with a perfect-looking error rate. The failures are counted somewhere as a generic exception, the queue moves on, and the work is gone. Because the loss is measured in requests and Anthropic reports only tokens, there is no report you can pull that names it &mdash; which is exactly why teams find it months later, in a reconciliation between what was submitted and what came back.</p>""",
"why": """<p><strong>Anthropic's messages usage report has no request count.</strong> This is the single fact that shapes the whole script. The buckets carry <code>uncached_input_tokens</code>, <code>cache_read_input_tokens</code>, the nested <code>cache_creation</code> pair and <code>output_tokens</code>, and nothing that counts calls. So "billed requests" cannot be read; it can only be estimated from tokens, and every number this script prints is an estimate that says so out loud.</p>
<p><strong>The baseline has to be a median, not a mean.</strong> The minutes being hunted are exactly the ones that would drag a mean tokens-per-attempt down, so a mean baseline quietly absorbs the loss it was computed to reveal. The median over the window survives a cluster covering up to half of it, which is a much better failure mode than the alternative.</p>
<p><strong>Contiguity separates a real cluster from bucket arithmetic.</strong> A request spans a minute boundary all the time, so isolated minutes with a shortfall are noise and always will be. Requiring three or more adjacent minutes is what turns a noisy residual into a finding, and it matches the mechanism: a capacity condition on the platform is not a coin flip per request.</p>
<p><strong>This is the mirror image of the streaming reconciliation, not a copy of it.</strong> The <a href="/llm/streaming-usage-lost/">streaming note</a> finds the provider's number <em>larger</em> than yours and concludes your pipeline is failing to record tokens you were billed for. This one finds your number larger than the provider's and concludes the platform never did the work. Same style of comparison, opposite sign, and opposite owner: there the bug is in your telemetry, here the telemetry is right and the requests are gone. The script reports an excess as its own state and hands that reader straight to the other note rather than calling it overload.</p>
<p><strong>It is also not the retry-storm read.</strong> The <a href="/llm/requests-diverge-from-token-volume/">divergence note</a> runs on OpenAI, needs nothing from you, and looks for requests the provider <em>did</em> count. This one cannot run at all without a number you supply, and looks for requests the provider never counted. A retry storm inflates the provider's own request count; a 529 never reaches it. If your client retries 529 successfully, both are true at once and the residual measures only the attempts that were never served.</p>
<p><strong>Priority Tier is not the escape hatch it used to be.</strong> Grouping by <code>service_tier</code> tells you whether any of your traffic was served as <code>priority</code>, and on most organizations the answer is now none, because capacity commitments are no longer sold. That makes 529 handling everybody's problem rather than something a purchase order solves, which is worth printing next to the clusters.</p>""",
"steps": [
 {"h": "Export your own attempt counter, per minute",
  "body": """<p>A JSON object keyed by minute: <code>{"2026-08-30T14:03Z": 900}</code>. Count <em>attempts</em>, including retries, at the point the request leaves your process &mdash; not logical jobs, and not successes. This is the half of the comparison the API cannot give you, and getting it wrong in either direction moves the whole finding.</p>"""},
 {"h": "Read one-minute usage buckets for the same window",
  "body": """<p><code>bucket_width=1m</code> with <code>group_by[]=service_tier</code>, paging on <code>next_page</code>. Sum every token field, cache reads and both cache-creation fields included: the question is whether the platform did work in that minute, not what that work cost. A parser that looks for a flat <code>cache_creation_input_tokens</code> finds nothing, because it is a nested object.</p>"""},
 {"h": "Establish a baseline with the median, never the mean",
  "body": """<p>Median tokens per attempt across the minutes both sources cover. Take the median because a mean would be pulled down by the very minutes you are looking for, which is how a first draft of this check comes back clean during an actual outage.</p>"""},
 {"h": "Estimate served attempts and keep only the adjacent minutes",
  "body": """<p>Billed tokens divided by the baseline is roughly how many attempts were served; attempts minus that is the residual. Group the minutes whose residual share crosses the floor into contiguous runs and discard the runs shorter than three minutes. Those are boundary artefacts, and reporting them is how a check gets muted.</p>"""},
 {"h": "Print the retry class, and never retry anything",
  "body": """<p>The repair is one retryable class containing 429, every 5xx and 529, with exponential backoff and jitter &mdash; or simply the SDK's own retry rather than a hand-rolled <code>except</code>. Print the affected minutes, the estimated loss and the <code>request-id</code> values your logs should already be capturing from every response, error responses included. An audit script that starts re-sending traffic into a platform that is over capacity is the one thing worse than the bug.</p>"""},
],
"verify": """<p>Re-run after the retry class is widened. The clusters should still appear in the platform's bad minutes and no longer correspond to lost work, because the attempts now succeed on the second try.</p>
<pre><code class="language-bash">python3 anthropic_overload_residual.py --attempts attempts.json --minutes 240
# overload-cluster  2026-08-30T14:04Z through 2026-08-30T14:06Z: 1800 attempt(s) over 3 minute(s), about 1440 of them produced no billed tokens (80%)
#   baseline 5000 token(s) per attempt, taken as the median across 240 minute(s)
#   no traffic in this window was served as priority
# 240 minute(s) compared, 1 cluster(s)</code></pre>""",
"code_intro": "One GET and a file you supply. The Admin key reads the per-minute buckets; the attempt counts come from you, because the report has no request-count field to compare against. Eight pure functions: the minute normaliser, which has to make your timestamps and Anthropic's agree; the minute index that makes adjacency testable; the token sum, which reaches into the nested cache-creation object; the attempt reader; the median baseline; the per-minute residual; the clustering, which is where the finding actually lives; and the classifier that throws away everything shorter than three minutes.",
"py_file": "anthropic_overload_residual.py",
"py": '''"""Size the Anthropic requests that were attempted and never served.

Read only. One GET against the Admin API, which needs an Admin API key
(sk-ant-admin...); a workspace key is rejected by every /v1/organizations/*
path, and an Admin key can be provisioned read-only.

The messages usage report carries token sums and no request count at all, so
"requests the platform served" cannot be read. It is estimated from the work
that was done: median tokens per attempt as a baseline, billed tokens divided
by it, subtracted from your own attempt counter. Every number here is an
estimate and the output says so.

Nothing is retried and nothing is sent. A script that starts re-issuing traffic
into a platform that is over capacity is worse than the bug it found.
"""
import argparse
import datetime as dt
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_overload_residual")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Every token field the messages usage report returns. cache_creation is a
# nested object; a parser looking for a flat cache_creation_input_tokens sums
# zero and reports a heavily cached minute as one where nothing happened.
TOKEN_FIELDS = ("uncached_input_tokens", "input_tokens",
                "cache_read_input_tokens", "output_tokens")
CACHE_CREATION_FIELDS = ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens")

FINDINGS = ("overload-cluster",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def minute_key(stamp):
    """Normalise a timestamp to a UTC minute key. Pure. None if unreadable.

    Accepts the RFC 3339 strings the usage report returns and the shapes your
    own counter is likely to emit: with or without seconds, with a space
    instead of a T, or as epoch seconds. Two sources that disagree about
    timestamp format produce a comparison with no overlap and a clean bill of
    health, which is the worst possible failure for this check.
    """
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


def minute_index(key):
    """Minutes since the epoch for a minute key. Pure. None if unreadable.

    Adjacency is the whole finding, so it needs to be arithmetic on integers
    rather than string comparison, which gets 14:59 and 15:00 wrong.
    """
    normalised = minute_key(key)
    if normalised is None:
        return None
    try:
        when = dt.datetime(int(normalised[0:4]), int(normalised[5:7]),
                           int(normalised[8:10]), int(normalised[11:13]),
                           int(normalised[14:16]), tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return int(when.timestamp()) // 60


def tokens_by_minute(buckets):
    """Total billed tokens per minute. Pure.

    Every field is summed, cache reads and cache creation included, because the
    question is whether the platform did any work in that minute and not what
    the work cost.
    """
    out = {}
    for bucket in buckets or []:
        key = minute_key(bucket.get("starting_at") or bucket.get("start_time"))
        if key is None:
            continue
        total = 0
        for result in bucket.get("results") or []:
            for field in TOKEN_FIELDS:
                total += _int(result.get(field))
            creation = result.get("cache_creation") or {}
            for field in CACHE_CREATION_FIELDS:
                total += _int(creation.get(field))
        out[key] = out.get(key, 0) + total
    return out


def attempts_by_minute(raw):
    """Read your own attempt counter into minute keys. Pure.

    Accepts {"2026-08-30T14:03Z": 900} or {"...": {"attempts": 900}}. Minutes
    that cannot be parsed are dropped rather than folded into a neighbour: an
    attempt attributed to the wrong minute breaks the contiguity test, which is
    the only thing separating a finding from noise.
    """
    out = {}
    for stamp, value in (raw or {}).items():
        key = minute_key(stamp)
        if key is None:
            continue
        if isinstance(value, dict):
            count = _int(value.get("attempts"))
        elif isinstance(value, bool):
            count = 0
        else:
            count = _int(value)
        out[key] = out.get(key, 0) + count
    return out


def _median(values):
    """Median of a list of numbers. Pure. None when empty."""
    ordered = sorted(values or [])
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (float(ordered[middle - 1]) + float(ordered[middle])) / 2.0


def baseline_tokens_per_attempt(tokens, attempts, min_minutes=5, min_attempts=1):
    """Median tokens per attempt across the covered minutes. Pure.

    The median, never the mean. The minutes this script is hunting are exactly
    the ones that would drag a mean down, so a mean baseline absorbs the loss
    it was computed to reveal and the check comes back clean during an outage.
    """
    ratios = []
    for key, made in (attempts or {}).items():
        made = _int(made)
        if made < min_attempts:
            continue
        ratios.append(_int((tokens or {}).get(key)) / float(made))
    if len(ratios) < min_minutes:
        return None
    value = _median(ratios)
    return value if value and value > 0 else None


def residual_rows(tokens, attempts, baseline):
    """One row per minute: attempts, tokens, estimated served and residual. Pure.

    served is tokens / baseline, which is an estimate and the only one
    available: the report has no request count to read instead.
    """
    out = []
    if not baseline or baseline <= 0:
        return out
    for key in sorted(attempts or {}):
        made = _int(attempts.get(key))
        if made <= 0:
            continue
        billed = _int((tokens or {}).get(key))
        served = billed / float(baseline)
        residual = max(0.0, made - served)
        out.append({"minute": key, "index": minute_index(key), "attempts": made,
                    "tokens": billed, "served": served, "residual": residual,
                    "share": residual / float(made)})
    return out


def clusters(rows, floor=0.3, min_attempts=20):
    """Group the shortfall minutes into contiguous runs. Pure.

    Contiguity is the finding. A request that starts at 14:03:58 and finishes
    at 14:04:06 lands its attempt in one minute and its tokens in the next, so
    isolated minutes are bucket arithmetic. A platform capacity condition is
    not a coin flip per request and arrives as a run.
    """
    bad = [r for r in rows or []
           if r.get("index") is not None
           and _int(r.get("attempts")) >= min_attempts
           and float(r.get("share") or 0.0) >= floor]
    bad.sort(key=lambda r: r["index"])

    runs = []
    for row in bad:
        if runs and row["index"] == runs[-1][-1]["index"] + 1:
            runs[-1].append(row)
        else:
            runs.append([row])
    return runs


def classify(cluster, min_minutes=3):
    """Classify one run of minutes. Pure. Returns (state, detail)."""
    cluster = cluster or []
    if not cluster:
        return ("no-cluster", "nothing to classify")
    attempts = sum(_int(r.get("attempts")) for r in cluster)
    lost = sum(float(r.get("residual") or 0.0) for r in cluster)
    share = (lost / attempts) if attempts else 0.0
    detail = ("%s through %s: %d attempt(s) over %d minute(s), about %d of them "
              "produced no billed tokens (%.0f%%)"
              % (cluster[0]["minute"], cluster[-1]["minute"], attempts,
                 len(cluster), int(lost), share * 100))
    if len(cluster) < min_minutes:
        return ("single-minute-dip",
                detail + ". Shorter than the %d minute floor, so this is most "
                "likely a request that straddled a bucket boundary rather than "
                "a capacity condition." % min_minutes)
    return ("overload-cluster",
            detail + ". A run this long is a platform capacity condition, "
            "which is what 529 is, and it is retryable.")


def excess_minutes(rows, tolerance=0.25):
    """Minutes where far more work was billed than the attempts explain. Pure.

    The opposite sign, and a different note. Being billed for tokens your own
    counter cannot account for is a recording gap in your telemetry, not
    requests the platform failed to serve.
    """
    out = []
    for row in rows or []:
        made = _int(row.get("attempts"))
        if made <= 0:
            continue
        if float(row.get("served") or 0.0) > made * (1.0 + tolerance):
            out.append(row["minute"])
    return out


def tiers_seen(buckets):
    """Every service_tier value present in the window. Pure.

    Priority Tier used to be the answer to 529 and capacity commitments are no
    longer sold, so "none of your traffic was served as priority" is usually
    the true and useful thing to print.
    """
    out = set()
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            tier = str(result.get("service_tier") or "").strip()
            if tier:
                out.add(tier)
    return out


def window_start(minutes):
    """Floor to the minute: starting_at has to sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    return (now - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
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
    ap.add_argument("--attempts", required=True,
                    help="JSON file of the requests your client attempted, "
                         "keyed by minute")
    ap.add_argument("--minutes", type=int, default=240,
                    help="minutes of one-minute buckets to read (max 1440)")
    ap.add_argument("--floor", type=float, default=0.3,
                    help="residual share above which a minute joins a cluster "
                         "(default 0.3)")
    ap.add_argument("--min-cluster", type=int, default=3,
                    help="adjacent minutes needed to call it a cluster "
                         "(default 3)")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key "
                  "(sk-ant-admin...); a workspace key cannot read "
                  "/v1/organizations/*")
        return 2

    try:
        with open(args.attempts, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as exc:
        log.error("could not read %s: %s", args.attempts, exc)
        return 2
    if not isinstance(raw, dict):
        log.error("%s should be a JSON object keyed by minute", args.attempts)
        return 2

    minutes = max(1, min(int(args.minutes), 1440))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    buckets = list(read_buckets(session, "/organizations/usage_report/messages", {
        "starting_at": window_start(minutes),
        "bucket_width": "1m",
        "limit": minutes,
        "group_by[]": ["service_tier"],
    }))

    tokens = tokens_by_minute(buckets)
    attempts = attempts_by_minute(raw)
    if not attempts:
        log.error("no readable minutes in %s. Keys should look like "
                  "2026-08-30T14:03Z", args.attempts)
        return 2

    baseline = baseline_tokens_per_attempt(tokens, attempts)
    if baseline is None:
        log.info("not enough overlapping minutes to establish a baseline; "
                 "nothing can be said about loss in this window")
        return 0
    log.info("baseline %d token(s) per attempt, taken as the median across "
             "%d minute(s)", int(baseline), len(attempts))

    rows = residual_rows(tokens, attempts, baseline)
    found = 0
    for cluster in clusters(rows, args.floor):
        state, detail = classify(cluster, args.min_cluster)
        if state in FINDINGS:
            found += 1
            log.warning("%-18s %s", state, detail)
        else:
            log.info("%-18s %s", state, detail)

    over = excess_minutes(rows)
    if over:
        log.warning("  %d minute(s) billed far more work than your attempts "
                    "explain, starting at %s. That is the opposite sign and a "
                    "different problem: tokens you were billed for and did not "
                    "record.", len(over), over[0])

    tiers = tiers_seen(buckets)
    if tiers and "priority" not in tiers:
        log.info("  no traffic in this window was served as priority (%s)",
                 ", ".join(sorted(tiers)))

    if found:
        log.warning("  repair: put 429, every 5xx and 529 in one retryable "
                    "class with exponential backoff and jitter, or use the "
                    "SDK's own retry instead of a hand-rolled except. 529 is "
                    "overloaded_error and is a platform capacity condition, "
                    "not something your request caused.")
        log.warning("  repair: capture the request-id header from every "
                    "response including errors. It is the only identifier "
                    "support can act on, and this report cannot recover it "
                    "after the fact.")

    log.info("%d minute(s) compared, %d cluster(s)", len(rows), found)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-overload-residual.mjs",
"js": '''/**
 * Size the Anthropic requests that were attempted and never served.
 *
 * Read only. One GET against the Admin API, which needs an Admin API key
 * (sk-ant-admin...). The messages usage report carries token sums and no
 * request count, so served requests are estimated from the work that was done:
 * median tokens per attempt, billed tokens divided by it, subtracted from your
 * own attempt counter.
 *
 * Nothing is retried and nothing is sent.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// cache_creation is a nested object; a flat reader sums zero.
const TOKEN_FIELDS = ['uncached_input_tokens', 'input_tokens',
                      'cache_read_input_tokens', 'output_tokens'];
const CACHE_CREATION_FIELDS = ['ephemeral_5m_input_tokens', 'ephemeral_1h_input_tokens'];

const FINDINGS = new Set(['overload-cluster']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Normalise a timestamp to a UTC minute key. Pure. Null if unreadable.
 * Two sources that disagree about timestamp format produce a comparison with
 * no overlap and a clean bill of health, which is the worst failure here.
 */
export function minuteKey(stamp) {
  if (typeof stamp === 'boolean') return null;
  if (typeof stamp === 'number') {
    if (!Number.isFinite(stamp)) return null;
    const when = new Date(Math.trunc(stamp) * 1000);
    if (Number.isNaN(when.getTime())) return null;
    return `${when.toISOString().slice(0, 16)}Z`;
  }
  const text = String(stamp ?? '').trim().replace(' ', 'T');
  if (text.length < 16) return null;
  const head = text.slice(0, 16);
  if (head[4] !== '-' || head[7] !== '-' || head[10] !== 'T' || head[13] !== ':') return null;
  for (const part of [head.slice(0, 4), head.slice(5, 7), head.slice(8, 10),
                      head.slice(11, 13), head.slice(14, 16)]) {
    if (!/^[0-9]+$/.test(part)) return null;
  }
  return `${head}Z`;
}

/**
 * Minutes since the epoch for a minute key. Pure. Null if unreadable.
 * Adjacency has to be integer arithmetic; string comparison gets 14:59 and
 * 15:00 wrong.
 */
export function minuteIndex(key) {
  const normalised = minuteKey(key);
  if (normalised === null) return null;
  const ms = Date.UTC(Number(normalised.slice(0, 4)), Number(normalised.slice(5, 7)) - 1,
                      Number(normalised.slice(8, 10)), Number(normalised.slice(11, 13)),
                      Number(normalised.slice(14, 16)));
  return Number.isFinite(ms) ? Math.floor(ms / 60000) : null;
}

/** Total billed tokens per minute. Pure. Every field, cache included. */
export function tokensByMinute(buckets) {
  const out = new Map();
  for (const bucket of buckets ?? []) {
    const key = minuteKey(bucket?.starting_at ?? bucket?.start_time);
    if (key === null) continue;
    let total = 0;
    for (const result of bucket?.results ?? []) {
      for (const field of TOKEN_FIELDS) total += readInt(result?.[field]);
      const creation = result?.cache_creation ?? {};
      for (const field of CACHE_CREATION_FIELDS) total += readInt(creation?.[field]);
    }
    out.set(key, (out.get(key) ?? 0) + total);
  }
  return out;
}

/**
 * Read your own attempt counter into minute keys. Pure.
 * Unparseable minutes are dropped rather than folded into a neighbour: a
 * misattributed attempt breaks the contiguity test.
 */
export function attemptsByMinute(raw) {
  const out = new Map();
  for (const [stamp, value] of Object.entries(raw ?? {})) {
    const key = minuteKey(stamp);
    if (key === null) continue;
    let count;
    if (value !== null && typeof value === 'object') count = readInt(value.attempts);
    else if (typeof value === 'boolean') count = 0;
    else count = readInt(value);
    out.set(key, (out.get(key) ?? 0) + count);
  }
  return out;
}

function median(values) {
  const ordered = [...(values ?? [])].sort((a, b) => a - b);
  if (ordered.length === 0) return null;
  const middle = Math.floor(ordered.length / 2);
  if (ordered.length % 2) return ordered[middle];
  return (ordered[middle - 1] + ordered[middle]) / 2;
}

/**
 * Median tokens per attempt across the covered minutes. Pure.
 * The median, never the mean: a mean would be dragged down by the very minutes
 * this is meant to find, so it would come back clean during an outage.
 */
export function baselineTokensPerAttempt(tokens, attempts, minMinutes = 5, minAttempts = 1) {
  const ratios = [];
  for (const [key, value] of attempts ?? new Map()) {
    const made = readInt(value);
    if (made < minAttempts) continue;
    ratios.push(readInt(tokens?.get(key)) / made);
  }
  if (ratios.length < minMinutes) return null;
  const value = median(ratios);
  return value && value > 0 ? value : null;
}

/** One row per minute: attempts, tokens, estimated served and residual. Pure. */
export function residualRows(tokens, attempts, baseline) {
  const out = [];
  if (!baseline || baseline <= 0) return out;
  for (const key of [...(attempts?.keys() ?? [])].sort()) {
    const made = readInt(attempts.get(key));
    if (made <= 0) continue;
    const billed = readInt(tokens?.get(key));
    const served = billed / baseline;
    const residual = Math.max(0, made - served);
    out.push({ minute: key, index: minuteIndex(key), attempts: made, tokens: billed,
               served, residual, share: residual / made });
  }
  return out;
}

/**
 * Group the shortfall minutes into contiguous runs. Pure.
 * Contiguity is the finding: a call spanning a bucket boundary lands its
 * attempt in one minute and its tokens in the next, so isolated minutes are
 * arithmetic rather than overload.
 */
export function clusters(rows, floor = 0.3, minAttempts = 20) {
  const bad = (rows ?? [])
    .filter((r) => r?.index !== null && r?.index !== undefined
      && readInt(r?.attempts) >= minAttempts && Number(r?.share ?? 0) >= floor)
    .sort((a, b) => a.index - b.index);

  const runs = [];
  for (const row of bad) {
    const last = runs[runs.length - 1];
    if (last && row.index === last[last.length - 1].index + 1) last.push(row);
    else runs.push([row]);
  }
  return runs;
}

/** Classify one run of minutes. Pure. Returns [state, detail]. */
export function classify(cluster, minMinutes = 3) {
  const run = cluster ?? [];
  if (run.length === 0) return ['no-cluster', 'nothing to classify'];
  const attempts = run.reduce((sum, r) => sum + readInt(r?.attempts), 0);
  const lost = run.reduce((sum, r) => sum + Number(r?.residual ?? 0), 0);
  const share = attempts ? lost / attempts : 0;
  const detail = `${run[0].minute} through ${run[run.length - 1].minute}: ` +
    `${attempts} attempt(s) over ${run.length} minute(s), about ` +
    `${Math.trunc(lost)} of them produced no billed tokens ` +
    `(${(share * 100).toFixed(0)}%)`;
  if (run.length < minMinutes) {
    return ['single-minute-dip',
      `${detail}. Shorter than the ${minMinutes} minute floor, so this is most ` +
      'likely a request that straddled a bucket boundary rather than a ' +
      'capacity condition.'];
  }
  return ['overload-cluster',
    `${detail}. A run this long is a platform capacity condition, which is ` +
    'what 529 is, and it is retryable.'];
}

/**
 * Minutes where far more work was billed than the attempts explain. Pure.
 * The opposite sign and a different note: a recording gap in your telemetry.
 */
export function excessMinutes(rows, tolerance = 0.25) {
  const out = [];
  for (const row of rows ?? []) {
    const made = readInt(row?.attempts);
    if (made <= 0) continue;
    if (Number(row?.served ?? 0) > made * (1 + tolerance)) out.push(row.minute);
  }
  return out;
}

/** Every service_tier value present in the window. Pure. */
export function tiersSeen(buckets) {
  const out = new Set();
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const tier = String(result?.service_tier ?? '').trim();
      if (tier) out.add(tier);
    }
  }
  return out;
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
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs an ` +
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
    query = { ...query, page: page.next_page };
  }
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const file = process.env.ATTEMPTS;
  if (!file) {
    console.error('set ATTEMPTS to a JSON file of the requests your client ' +
                  'attempted, keyed by minute');
    process.exitCode = 2;
    return;
  }
  const minutes = Math.max(1, Math.min(Number(process.env.MINUTES ?? 240), 1440));
  const floor = Number(process.env.FLOOR ?? 0.3);
  const minCluster = Number(process.env.MIN_CLUSTER ?? 3);

  let raw;
  try {
    raw = JSON.parse(await readFile(file, 'utf8'));
  } catch (err) {
    console.error(`could not read ${file}: ${err.message}`);
    process.exitCode = 2;
    return;
  }

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organizations/usage_report/messages', {
    starting_at: windowStart(minutes),
    bucket_width: '1m',
    limit: minutes,
    'group_by[]': ['service_tier'],
  })) buckets.push(bucket);

  const tokens = tokensByMinute(buckets);
  const attempts = attemptsByMinute(raw);
  if (attempts.size === 0) {
    console.error(`no readable minutes in ${file}. Keys should look like ` +
                  '2026-08-30T14:03Z');
    process.exitCode = 2;
    return;
  }

  const baseline = baselineTokensPerAttempt(tokens, attempts);
  if (baseline === null) {
    console.log('not enough overlapping minutes to establish a baseline; nothing ' +
                'can be said about loss in this window');
    return;
  }
  console.log(`baseline ${Math.trunc(baseline)} token(s) per attempt, taken as ` +
              `the median across ${attempts.size} minute(s)`);

  const rows = residualRows(tokens, attempts, baseline);
  let found = 0;
  for (const cluster of clusters(rows, floor)) {
    const [state, detail] = classify(cluster, minCluster);
    if (FINDINGS.has(state)) { found += 1; console.warn(`${state.padEnd(18)} ${detail}`); }
    else console.log(`${state.padEnd(18)} ${detail}`);
  }

  const over = excessMinutes(rows);
  if (over.length > 0) {
    console.warn(`  ${over.length} minute(s) billed far more work than your ` +
                 `attempts explain, starting at ${over[0]}. That is the opposite ` +
                 'sign and a different problem: tokens you were billed for and ' +
                 'did not record.');
  }

  const tiers = tiersSeen(buckets);
  if (tiers.size > 0 && !tiers.has('priority')) {
    console.log(`  no traffic in this window was served as priority ` +
                `(${[...tiers].sort().join(', ')})`);
  }

  if (found) {
    console.warn('  repair: put 429, every 5xx and 529 in one retryable class ' +
                 'with exponential backoff and jitter, or use the SDK own retry ' +
                 'instead of a hand-rolled catch. 529 is overloaded_error and is ' +
                 'a platform capacity condition, not something your request caused.');
    console.warn('  repair: capture the request-id header from every response ' +
                 'including errors. It is the only identifier support can act on, ' +
                 'and this report cannot recover it after the fact.');
  }

  console.log(`${rows.length} minute(s) compared, ${found} cluster(s)`);
  process.exitCode = found ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is a ten-minute window in which three adjacent minutes billed a fifth of the tokens their attempt counts should have produced. It asserts the cluster covers exactly those three minutes and no others, and it asserts the baseline is still five thousand tokens per attempt &mdash; which is the point of using a median, since a mean over the same data comes out low enough to make the outage look like a normal afternoon. The rest defend the two things that quietly break this check: an isolated bad minute has to come back as bucket arithmetic rather than as overload, and a minute key has to normalise your timestamps and Anthropic's to the same string, because two formats that never match produce a clean report during a real incident.",
"test_py_file": "test_anthropic_overload_residual.py",
"test_py": '''from anthropic_overload_residual import (attempts_by_minute,
                                          baseline_tokens_per_attempt,
                                          classify, clusters, excess_minutes,
                                          minute_index, minute_key,
                                          residual_rows, tiers_seen,
                                          tokens_by_minute)


def minute(n):
    return "2026-08-30T14:%02dZ" % n


# Ten minutes at 600 attempts each. Seven of them do the full 3,000,000 tokens
# of work that 600 calls at 5000 tokens implies; minutes 4, 5 and 6 do a fifth
# of it, because the platform was over capacity and served 120 of the 600.
ATTEMPTS = {minute(n): 600 for n in range(10)}
TOKENS = {minute(n): (600_000 if n in (4, 5, 6) else 3_000_000) for n in range(10)}


def test_three_adjacent_bad_minutes_are_one_overload_cluster():
    baseline = baseline_tokens_per_attempt(TOKENS, ATTEMPTS)
    # The median survives the outage. A mean over the same data is 3800, which
    # would hide most of the loss it was computed to find.
    assert baseline == 5000.0

    rows = residual_rows(TOKENS, ATTEMPTS, baseline)
    assert len(rows) == 10
    bad = [r for r in rows if r["share"] > 0.5]
    assert [r["minute"] for r in bad] == [minute(4), minute(5), minute(6)]
    assert round(bad[0]["residual"]) == 480

    runs = clusters(rows)
    assert len(runs) == 1
    state, detail = classify(runs[0])
    assert state == "overload-cluster"
    assert "2026-08-30T14:04Z through 2026-08-30T14:06Z" in detail
    assert "1800 attempt(s) over 3 minute(s)" in detail
    assert "about 1440 of them produced no billed tokens (80%)" in detail


def test_one_bad_minute_on_its_own_is_bucket_arithmetic():
    attempts = dict(ATTEMPTS)
    tokens = {k: 3_000_000 for k in attempts}
    tokens[minute(4)] = 600_000
    rows = residual_rows(tokens, attempts,
                         baseline_tokens_per_attempt(tokens, attempts))
    runs = clusters(rows)
    assert len(runs) == 1 and len(runs[0]) == 1
    state, detail = classify(runs[0])
    assert state == "single-minute-dip"
    assert "straddled a bucket boundary" in detail


def test_minutes_that_are_not_adjacent_do_not_become_one_cluster():
    tokens = {k: 3_000_000 for k in ATTEMPTS}
    for n in (1, 5, 9):
        tokens[minute(n)] = 100_000
    rows = residual_rows(tokens, ATTEMPTS,
                         baseline_tokens_per_attempt(tokens, ATTEMPTS))
    assert [len(run) for run in clusters(rows)] == [1, 1, 1]


def test_the_two_clocks_are_normalised_to_the_same_minute():
    # Anthropic returns full RFC 3339; your counter probably does not. Two
    # formats that never match produce a clean report during a real incident.
    for stamp in ("2026-08-30T14:03:27Z", "2026-08-30T14:03Z",
                  "2026-08-30 14:03:00+00:00", "2026-08-30T14:03:59.512Z"):
        assert minute_key(stamp) == "2026-08-30T14:03Z"
    assert minute_key(1788098580) == "2026-08-30T14:03Z"
    assert minute_key("last tuesday") is None
    assert minute_key("") is None
    assert minute_key(None) is None
    assert minute_key(True) is None
    # Adjacency is arithmetic, not string order: 14:59 and 15:00 are neighbours.
    assert minute_index("2026-08-30T15:00Z") - minute_index("2026-08-30T14:59Z") == 1


def test_the_nested_cache_creation_object_is_counted_as_work():
    buckets = [{"starting_at": "2026-08-30T14:03:00Z",
                "results": [{"uncached_input_tokens": 10,
                             "cache_read_input_tokens": 20,
                             "output_tokens": 5,
                             "service_tier": "standard",
                             "cache_creation": {"ephemeral_5m_input_tokens": 100,
                                                "ephemeral_1h_input_tokens": 65}}]}]
    assert tokens_by_minute(buckets) == {"2026-08-30T14:03Z": 200}
    assert tiers_seen(buckets) == {"standard"}
    assert tokens_by_minute([]) == {}


def test_an_attempt_file_is_read_leniently_and_bad_keys_are_dropped():
    assert attempts_by_minute({"2026-08-30T14:03:00Z": 900}) == {"2026-08-30T14:03Z": 900}
    assert attempts_by_minute({"2026-08-30T14:03Z": {"attempts": 900}}) \\
        == {"2026-08-30T14:03Z": 900}
    assert attempts_by_minute({"whenever": 900}) == {}
    assert attempts_by_minute(None) == {}


def test_more_work_than_the_attempts_explain_is_the_other_note():
    attempts = {minute(n): 100 for n in range(10)}
    tokens = {minute(n): 500_000 for n in range(10)}
    tokens[minute(3)] = 2_000_000
    baseline = baseline_tokens_per_attempt(tokens, attempts)
    rows = residual_rows(tokens, attempts, baseline)
    assert excess_minutes(rows) == [minute(3)]
    assert clusters(rows) == []


def test_too_little_overlap_produces_no_baseline_rather_than_a_guess():
    assert baseline_tokens_per_attempt({}, {}) is None
    assert baseline_tokens_per_attempt({minute(0): 5000}, {minute(0): 1}) is None
    assert baseline_tokens_per_attempt({}, ATTEMPTS) is None
    assert residual_rows(TOKENS, ATTEMPTS, None) == []
    assert classify([])[0] == "no-cluster"
''',
"test_js_file": "anthropic-overload-residual.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attemptsByMinute, baselineTokensPerAttempt, classify, clusters,
         excessMinutes, minuteIndex, minuteKey, residualRows, tiersSeen,
         tokensByMinute } from './anthropic-overload-residual.mjs';

const minute = (n) => `2026-08-30T14:${String(n).padStart(2, '0')}Z`;

// Ten minutes at 600 attempts each; minutes 4, 5 and 6 did a fifth of the work.
const ATTEMPTS = new Map(Array.from({ length: 10 }, (_, n) => [minute(n), 600]));
const TOKENS = new Map(Array.from({ length: 10 },
  (_, n) => [minute(n), [4, 5, 6].includes(n) ? 600000 : 3000000]));

test('three adjacent bad minutes are one overload cluster', () => {
  const baseline = baselineTokensPerAttempt(TOKENS, ATTEMPTS);
  // The median survives the outage; a mean over the same data is 3800.
  assert.equal(baseline, 5000);

  const rows = residualRows(TOKENS, ATTEMPTS, baseline);
  assert.equal(rows.length, 10);
  const bad = rows.filter((r) => r.share > 0.5);
  assert.deepEqual(bad.map((r) => r.minute), [minute(4), minute(5), minute(6)]);
  assert.equal(Math.round(bad[0].residual), 480);

  const runs = clusters(rows);
  assert.equal(runs.length, 1);
  const [state, detail] = classify(runs[0]);
  assert.equal(state, 'overload-cluster');
  assert.match(detail, /2026-08-30T14:04Z through 2026-08-30T14:06Z/);
  assert.match(detail, /1800 attempt\\(s\\) over 3 minute\\(s\\)/);
  assert.match(detail, /about 1440 of them produced no billed tokens \\(80%\\)/);
});

test('one bad minute on its own is bucket arithmetic', () => {
  const tokens = new Map([...ATTEMPTS.keys()].map((k) => [k, 3000000]));
  tokens.set(minute(4), 600000);
  const rows = residualRows(tokens, ATTEMPTS,
                            baselineTokensPerAttempt(tokens, ATTEMPTS));
  const runs = clusters(rows);
  assert.equal(runs.length, 1);
  assert.equal(runs[0].length, 1);
  const [state, detail] = classify(runs[0]);
  assert.equal(state, 'single-minute-dip');
  assert.match(detail, /straddled a bucket boundary/);
});

test('minutes that are not adjacent do not become one cluster', () => {
  const tokens = new Map([...ATTEMPTS.keys()].map((k) => [k, 3000000]));
  for (const n of [1, 5, 9]) tokens.set(minute(n), 100000);
  const rows = residualRows(tokens, ATTEMPTS,
                            baselineTokensPerAttempt(tokens, ATTEMPTS));
  assert.deepEqual(clusters(rows).map((run) => run.length), [1, 1, 1]);
});

test('the two clocks are normalised to the same minute', () => {
  for (const stamp of ['2026-08-30T14:03:27Z', '2026-08-30T14:03Z',
                       '2026-08-30 14:03:00+00:00', '2026-08-30T14:03:59.512Z']) {
    assert.equal(minuteKey(stamp), '2026-08-30T14:03Z');
  }
  assert.equal(minuteKey(1788098580), '2026-08-30T14:03Z');
  assert.equal(minuteKey('last tuesday'), null);
  assert.equal(minuteKey(''), null);
  assert.equal(minuteKey(null), null);
  assert.equal(minuteKey(true), null);
  assert.equal(minuteIndex('2026-08-30T15:00Z') - minuteIndex('2026-08-30T14:59Z'), 1);
});

test('the nested cache creation object is counted as work', () => {
  const buckets = [{ starting_at: '2026-08-30T14:03:00Z',
    results: [{ uncached_input_tokens: 10, cache_read_input_tokens: 20,
                output_tokens: 5, service_tier: 'standard',
                cache_creation: { ephemeral_5m_input_tokens: 100,
                                  ephemeral_1h_input_tokens: 65 } }] }];
  assert.deepEqual([...tokensByMinute(buckets)], [['2026-08-30T14:03Z', 200]]);
  assert.deepEqual([...tiersSeen(buckets)], ['standard']);
  assert.equal(tokensByMinute([]).size, 0);
});

test('an attempt file is read leniently and bad keys are dropped', () => {
  assert.deepEqual([...attemptsByMinute({ '2026-08-30T14:03:00Z': 900 })],
                   [['2026-08-30T14:03Z', 900]]);
  assert.deepEqual([...attemptsByMinute({ '2026-08-30T14:03Z': { attempts: 900 } })],
                   [['2026-08-30T14:03Z', 900]]);
  assert.equal(attemptsByMinute({ whenever: 900 }).size, 0);
  assert.equal(attemptsByMinute(null).size, 0);
});

test('more work than the attempts explain is the other note', () => {
  const attempts = new Map(Array.from({ length: 10 }, (_, n) => [minute(n), 100]));
  const tokens = new Map(Array.from({ length: 10 }, (_, n) => [minute(n), 500000]));
  tokens.set(minute(3), 2000000);
  const rows = residualRows(tokens, attempts,
                            baselineTokensPerAttempt(tokens, attempts));
  assert.deepEqual(excessMinutes(rows), [minute(3)]);
  assert.deepEqual(clusters(rows), []);
});

test('too little overlap produces no baseline rather than a guess', () => {
  assert.equal(baselineTokensPerAttempt(new Map(), new Map()), null);
  assert.equal(baselineTokensPerAttempt(new Map([[minute(0), 5000]]),
                                        new Map([[minute(0), 1]])), null);
  assert.equal(baselineTokensPerAttempt(new Map(), ATTEMPTS), null);
  assert.deepEqual(residualRows(TOKENS, ATTEMPTS, null), []);
  assert.equal(classify([])[0], 'no-cluster');
});
''',
"faq": [
 ("Why do I have to supply the attempt count myself?",
  "Because Anthropic does not publish one. The messages usage report returns token sums per bucket and has no request-count field at all, which is a documented difference from OpenAI's usage endpoints. Without a count from your side there is no subtraction to do, and the best the API can offer on its own is that some minutes look quieter than others."),
 ("How accurate is the estimate of served requests?",
  "It is an estimate and the script never pretends otherwise. Dividing billed tokens by a median tokens-per-attempt assumes the requests in a bad minute would have been about the same size as the ones around it, which holds for a homogeneous workload and does not hold if your traffic mixes tiny classifications with enormous summaries. Read the finding as a shape and a rough magnitude, not as an accounting record."),
 ("Is this the same check as reconciling streamed usage?",
  "No, and the sign is the difference. Reconciling streamed usage finds the provider's token count larger than your own and concludes your pipeline is not recording what you were billed for. This one finds your attempt count larger than the work the provider did and concludes the platform never served the requests. The script reports an excess as its own state and points you at the other note rather than calling it overload."),
 ("How is this different from spotting a retry storm?",
  "A retry storm is visible in the provider's own numbers, because the attempts were served and counted. A 529 cluster never reaches the provider's numbers at all, which is why this check needs a number from you and the storm check does not. If your client retries 529 and eventually succeeds, both are happening and the residual measures only the attempts that were never served."),
 ("Should the script retry the lost requests?",
  "No, and it will not. It holds a key that can spend money on inference, the condition it just detected is the platform being over capacity, and re-sending traffic into that is how a transient becomes an incident. It prints the affected minutes, the estimated loss and the retry class to adopt, and you decide what to replay."),
],
"related": [REL_STREAMING, REL_STORM, REL_LIMITER],
"citations": [CITE_CL_ERRORS, CITE_CL_USAGE_REPORT, CITE_CL_TIERS, CITE_CL_USAGE_API],
},
{
"slug": "live-project-zero-usage-buckets",
"title": "A live project's usage buckets have been empty for days",
"description": "Nothing errored because nothing was sent. The usage endpoint answers with empty results arrays, and no monitor anywhere alerts on the absence of traffic.",
"h1": "A live project's usage buckets have been empty for days",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai project no usage", "usage buckets empty results",
             "integration silently stopped calling the api",
             "alert on absence of traffic", "last_used_at api key"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because usage, the project list and the key roster all live on the organization.",
"lead": "A customer asks, politely, when the summaries are coming back. Nobody on the call knows what they mean, because the feature works: the page renders, the job runs, the queue is empty, the error rate is zero and the latency graph is the flattest it has been all year. It is flat because for eleven days that project has sent the API nothing at all. A feature flag went the wrong way in an unrelated release, and every dashboard the team owns measures things that only exist when requests do.",
"short_answer": """<p>Ask for a fortnight of daily buckets per project and look for the ones that stop. With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={now-14d}&amp;bucket_width=1d&amp;limit=14&amp;group_by=project_id</code>. Buckets come back for the whole range whether or not there was traffic, so a project that has gone dark shows <code>results</code> as an empty array for the recent days while the earlier ones are full.</p>
<p>The rule is: non-zero in the first part of the window, zero for the last 48 hours, and the project still <code>active</code>. Drop today's bucket, which is always partial, and treat a project whose traffic <em>starts</em> in the tail as a launch rather than a death &mdash; those two look identical if you only compare halves.</p>
<p>Then sweep the other usage surfaces, because completions is one of eight: embeddings, images, audio speeches, audio transcriptions, moderations, file search and web search all take the same parameters. Quiet everywhere is a credential or a deploy. Quiet on one surface while another is still busy is one code path, which is a much smaller search.</p>""",
"problem": """<p>Every alarm a team owns is a ceiling. Error rate above a threshold, latency above a threshold, spend above a threshold, queue depth above a threshold. All of them read perfectly when the number is zero, and an integration that stops calling the API produces zeroes everywhere at once. There is no exception to catch, because nothing was attempted; no 4xx, no 5xx, no timeout, no retry. Silence is the one state monitoring built on thresholds cannot see.</p>
<p>So these get found by customers, or by a quarterly reconciliation, or not at all. The causes are dull and common: a feature flag flipped in an unrelated release, a consumer that died and was never restarted, a config that now points at a key in a different project, a refactor that left a condition permanently false, an upstream producer that stopped emitting the events which triggered the calls. None of them announces itself, and all of them look the same from the outside.</p>""",
"why": """<p><strong>The endpoint answers with a shape, not with a zero.</strong> A project with no traffic in a bucket does not come back as <code>num_model_requests: 0</code>; it comes back as a bucket whose <code>results</code> array is empty, or with that project absent from the results entirely. A parser that assumes every project appears in every bucket silently skips exactly the case this note is about, so the day axis has to come from the window you asked for rather than from what the response happened to contain.</p>
<p><strong>A launch and a death are the same shape read backwards.</strong> Traffic in one half of the window and none in the other is the finding, and which half decides everything. The check is directional or it fires on every new project in the organization, once, and then gets muted.</p>
<p><strong>The key roster corroborates the silence and says how wide it is.</strong> <code>GET /v1/organization/projects/{project_id}/api_keys?owner_project_access=any</code> returns <code>last_used_at</code> per key. Frozen at about the hour the buckets stopped means the whole integration went quiet. Still moving while usage is empty means something is authenticating and not inferring &mdash; a health check, a listing call, a surface this sweep did not read &mdash; and that is a much narrower fault. The <code>owner_project_access=any</code> parameter matters: without it the roster can be filtered to keys the caller can see and an audit quietly reads a subset.</p>
<p><strong>Usage data lags, so never alert on the current bucket.</strong> Today is always partial and cost and usage can both be revised as late events land. A 48-hour quiet window is short enough to be useful and long enough not to fire on a slow Sunday plus reporting lag, and the current day is dropped before anything is compared.</p>
<p><strong>This is not the orphaned-key check.</strong> When a key's owner loses access to a project, the platform sets a flag and there is <a href="/llm/key-owner-lost-project-access/">a note about reading it</a>. Here nothing is flagged, nothing is disabled, the key is valid, the project is active and the credential would work perfectly if anything called it. The provider has no opinion to read, so the only evidence is the absence, which is why this check has to be built rather than subscribed to.</p>
<p><strong>It is also not a spend anomaly.</strong> A <a href="/llm/spend-spike-week-over-week/">week-over-week cost check</a> classifies the shape of a change in one org-wide series, and a fall in dollars is one of the things it reports. This one runs per project, at day granularity, and its only interesting output is a floor being crossed: it is the check whose entire value is that it fires on zero.</p>""",
"steps": [
 {"h": "List the projects and keep the active ones",
  "body": """<p><code>GET /v1/organization/projects?limit=100</code>, paging on <code>after</code>. Archived projects going quiet is expected and is a different note's business, so filter to <code>status == "active"</code> before anything else. A project that has never had traffic in the window is also not a finding &mdash; it is either new or dormant, and both are reported as their own state.</p>"""},
 {"h": "Read fourteen daily buckets per usage surface",
  "body": """<p><code>bucket_width=1d</code>, <code>limit=14</code>, <code>group_by=project_id</code>, repeated across the surfaces the organization actually uses. Build the day axis from the window you requested rather than from the days that came back, because the missing days are the finding.</p>"""},
 {"h": "Drop today before comparing anything",
  "body": """<p>The current bucket is partial by definition and usage data arrives with some lag. Compare complete days only. This is the same discipline the cost checks need and it matters more here, because the whole signal is a run of zeroes and a partial day is a small zero.</p>"""},
 {"h": "Split the window and require the traffic to be in the early half",
  "body": """<p>Non-zero before the quiet window, zero inside it. Reverse that and you have a launch. Report the last day with traffic, how many complete days ago it was, and the mean daily volume before it stopped, because those three numbers are what turn "it is quiet" into "it stopped on the sixteenth, and it was doing four thousand calls a day".</p>"""},
 {"h": "Corroborate with the keys, then print an alarm with a floor",
  "body": """<p>Check <code>last_used_at</code> across the project's keys to separate a dead integration from a live one that stopped inferring. The repair is not a code change the script can name, because the cause is in your deploy: it is a scheduled liveness check that treats absence as an alert condition, per project, with a floor rather than a ceiling. Print it, including the endpoint and the threshold to use.</p>"""},
],
"verify": """<p>Once the floor alarm exists, this script stops being interesting, which is the goal. Until then run it daily; a project that has resumed moves to <code>live</code> on the next run.</p>
<pre><code class="language-bash">python3 openai_project_went_quiet.py --days 14 --quiet-days 2
# went-quiet   proj_summaries  completions: last traffic on 2026-08-16, 2 complete day(s) ago, after a prior mean of 4102 request(s) a day
#   the newest key use is 2.1 day(s) ago, which lines up with the buckets. The integration went quiet, not one call site.
#   still live on: embeddings
# 6 active project(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Three GETs: the project roster, one usage sweep per surface, and the key list only for projects that turn up quiet. Seven pure functions: the day key and the complete-day axis, which is built from the window rather than from the response because the missing days are the point; the fold; the classifier, which is directional so a launch is not reported as a death; the key reader; the corroboration that separates a dead integration from one that is still authenticating; and the surface split, which turns &ldquo;the project is quiet&rdquo; into &ldquo;one code path is quiet&rdquo; when another surface is still busy.",
"py_file": "openai_project_went_quiet.py",
"py": '''"""Find OpenAI projects whose usage buckets went empty while the project is live.

Read only. GET requests against the organization endpoints, which reject
project keys: this needs an organization admin key (sk-admin-), and read-only
scopes are enough.

The finding is an absence. Nothing errored, because nothing was sent, so there
is no status code anywhere to look up. The usage endpoint returns buckets for
the whole window whether or not there was traffic, which makes the empty ones
readable, and the day axis is built from the window requested rather than from
the days that came back.

The repair is printed, never performed. What is missing is an alarm with a
floor instead of a ceiling, and that lives in your monitoring, not here.
"""
import argparse
import datetime as dt
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_project_went_quiet")

API = "https://api.openai.com/v1"

# Completions is one surface of eight, and a project can go quiet on one while
# staying busy on another. Quiet everywhere is a credential or a deploy; quiet
# on one is a code path, which is a far smaller thing to search.
SURFACES = ("completions", "embeddings", "images", "audio_speeches",
            "audio_transcriptions", "moderations", "file_search_calls",
            "web_search_calls")

# Each surface counts a different thing, and exactly one of these appears on any
# given result.
COUNT_FIELDS = ("num_model_requests", "num_requests", "num_images",
                "num_seconds", "num_characters")

FINDINGS = ("went-quiet",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def day_key(epoch):
    """The UTC day a bucket start belongs to. Pure. None if unreadable."""
    try:
        return dt.datetime.fromtimestamp(int(epoch), dt.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def complete_days(now_epoch, days):
    """The last N complete UTC days, oldest first. Pure.

    Today is excluded. The current bucket is partial by definition and usage
    data lags, so a run of zeroes that includes today is one day shorter than
    it looks, and the whole finding is a run of zeroes.

    Built here rather than read off the response, because a project with no
    traffic may be absent from a bucket entirely and the missing days are the
    thing being looked for.
    """
    out = []
    for offset in range(int(days), 0, -1):
        key = day_key(int(now_epoch) - offset * 86400)
        if key is not None:
            out.append(key)
    return out


def daily(buckets):
    """{project_id: {day: count}} from one usage surface. Pure.

    Surfaces count different things, so the first recognised field wins rather
    than being summed: a result carrying both would otherwise be counted twice.
    """
    out = {}
    for bucket in buckets or []:
        day = day_key(bucket.get("start_time"))
        if day is None:
            continue
        for result in bucket.get("results") or []:
            project = str(result.get("project_id") or "unknown")
            count = 0
            for field in COUNT_FIELDS:
                if field in result:
                    count = _int(result.get(field))
                    break
            row = out.setdefault(project, {})
            row[day] = row.get(day, 0) + count
    return out


def classify(series, days, quiet_days=2, min_requests=100):
    """Classify one project's daily series. Pure. Returns (state, detail).

    Directional on purpose. Traffic in the early days and none in the last two
    is a project that stopped; the reverse is a project that started, and a
    check that cannot tell them apart fires on every launch and gets muted.
    """
    days = list(days or [])
    if len(days) <= quiet_days:
        return ("window-too-short",
                "%d complete day(s) is not enough to hold a %d day quiet "
                "window" % (len(days), quiet_days))

    series = series or {}
    head, tail = days[:-quiet_days], days[-quiet_days:]
    prior = sum(_int(series.get(day)) for day in head)
    recent = sum(_int(series.get(day)) for day in tail)
    active = [day for day in days if _int(series.get(day)) > 0]

    if not active:
        return ("never-active",
                "no traffic at all across %d complete day(s)" % len(days))
    if prior == 0:
        return ("new-traffic",
                "first traffic in this window landed on %s, inside the last %d "
                "day(s). A launch reads exactly like a death if you only "
                "compare halves." % (active[0], quiet_days))
    if recent > 0:
        return ("live",
                "%d request(s) in the last %d day(s), against a prior mean of "
                "%d a day" % (recent, quiet_days, prior / float(len(head))))
    if prior < min_requests:
        return ("too-little-traffic",
                "%d request(s) before the quiet window, under the floor of %d. "
                "Too sporadic for a gap to mean anything." % (prior, min_requests))

    since = len(days) - 1 - days.index(active[-1])
    return ("went-quiet",
            "last traffic on %s, %d complete day(s) ago, after a prior mean of "
            "%d request(s) a day"
            % (active[-1], since, prior / float(len(head))))


def key_activity(keys, now_epoch):
    """The newest last_used_at across a project's keys. Pure.

    Returns (epoch, days_since), or (None, None) when no key reports a use.
    """
    best = None
    for key in keys or []:
        try:
            used = key.get("last_used_at")
        except AttributeError:
            continue
        if used is None:
            continue
        try:
            used = int(used)
        except (TypeError, ValueError):
            continue
        if best is None or used > best:
            best = used
    if best is None:
        return (None, None)
    return (best, max(0.0, (int(now_epoch) - best) / 86400.0))


def corroborate(days_since, quiet_days=2):
    """Line the key roster up against the silence. Pure. Returns (state, detail).

    A key still in use while the buckets are empty is a much narrower fault
    than a key that went quiet at the same moment: something is authenticating
    and not inferring.
    """
    if days_since is None:
        return ("no-key-use",
                "no key on this project reports a last use, so there is "
                "nothing here to corroborate the silence with")
    if days_since <= quiet_days:
        return ("key-still-used",
                "a key on this project was used %.1f day(s) ago while the "
                "usage buckets were empty. Something is still authenticating "
                "and not inferring: a health check, or a surface this sweep "
                "did not read." % days_since)
    return ("key-quiet-too",
            "the newest key use is %.1f day(s) ago, which lines up with the "
            "buckets. The integration went quiet, not one call site."
            % days_since)


def surface_split(states):
    """(quiet, live) surface names for one project. Pure.

    Quiet on one surface while another is still busy is a code path rather than
    a credential, and that difference is worth more than the finding itself.
    """
    quiet = sorted(name for name, state in (states or {}).items()
                   if state == "went-quiet")
    live = sorted(name for name, state in (states or {}).items()
                  if state == "live")
    return (quiet, live)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk a usage report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def listing(session, path, params, max_pages=20):
    """Walk a list endpoint, which paginates on an object id."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params = dict(params)
        params["after"] = data[-1].get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="complete days to read (default 14)")
    ap.add_argument("--quiet-days", type=int, default=2,
                    help="days of silence that make a finding (default 2)")
    ap.add_argument("--min-requests", type=int, default=100,
                    help="ignore projects quieter than this before the gap "
                         "(default 100)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print projects that are still live")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key; read-only "
                  "scopes are enough)")
        return 2

    now = int(time.time())
    days = complete_days(now, max(3, min(int(args.days), 30)))
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    projects = [p for p in listing(session, "/organization/projects", {"limit": 100})
                if str(p.get("status") or "") == "active"]
    if not projects:
        log.info("no active projects in this organization")
        return 0

    per_surface = {}
    for surface in SURFACES:
        try:
            per_surface[surface] = daily(pages(
                session, "/organization/usage/" + surface,
                {"start_time": now - (len(days) + 1) * 86400,
                 "bucket_width": "1d", "limit": len(days) + 1,
                 "group_by": ["project_id"]}))
        except requests.HTTPError:
            # A surface the organization has never used can 400 rather than
            # returning an empty window. Not a finding, and not fatal.
            log.info("skipped the %s usage surface", surface)

    checked = 0
    bad = 0
    for project in projects:
        project_id = str(project.get("id") or "")
        states = {}
        details = {}
        for surface, rows in per_surface.items():
            state, detail = classify(rows.get(project_id), days,
                                     args.quiet_days, args.min_requests)
            states[surface] = state
            details[surface] = detail
        checked += 1

        quiet, live = surface_split(states)
        if not quiet:
            if args.show_all:
                log.info("%-18s %s  no surface went quiet", "live", project_id)
            continue

        bad += 1
        log.warning("%-18s %s  %s: %s", "went-quiet", project_id, quiet[0],
                    details[quiet[0]])
        keys = list(listing(session,
                            "/organization/projects/%s/api_keys" % project_id,
                            {"limit": 100, "owner_project_access": "any"}))
        _, note = corroborate(key_activity(keys, now)[1], args.quiet_days)
        log.warning("  %s", note)
        if live:
            log.warning("  still live on: %s", ", ".join(live))
            log.warning("  repair: one code path stopped calling, not the "
                        "credential. Look at the deploy that touched it rather "
                        "than at the key.")
        else:
            log.warning("  repair: every surface is quiet, so look at the "
                        "credential, the feature flag or the consumer before "
                        "the call site.")
        log.warning("  repair: add a scheduled liveness check that alerts on "
                    "absence. Read /v1/organization/usage/completions daily "
                    "with group_by=project_id and page on next_page, and alert "
                    "when a project falls below a floor rather than above a "
                    "ceiling. This is the one check whose value is that it "
                    "fires on zero.")

    log.info("%d active project(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-project-went-quiet.mjs",
"js": '''/**
 * Find OpenAI projects whose usage buckets went empty while the project is live.
 *
 * Read only. GET requests against the organization endpoints, which reject
 * project keys: this needs an organization admin key (sk-admin-).
 *
 * The finding is an absence, so the day axis is built from the window that was
 * requested rather than from the days that came back. The repair is printed,
 * never performed: what is missing is an alarm with a floor instead of a
 * ceiling, and that lives in your monitoring.
 */
const API = 'https://api.openai.com/v1';

const SURFACES = ['completions', 'embeddings', 'images', 'audio_speeches',
                  'audio_transcriptions', 'moderations', 'file_search_calls',
                  'web_search_calls'];

const COUNT_FIELDS = ['num_model_requests', 'num_requests', 'num_images',
                      'num_seconds', 'num_characters'];

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/** The UTC day a bucket start belongs to. Pure. Null if unreadable. */
export function dayKey(epoch) {
  const n = Number(epoch);
  if (!Number.isFinite(n)) return null;
  const when = new Date(Math.trunc(n) * 1000);
  if (Number.isNaN(when.getTime())) return null;
  return when.toISOString().slice(0, 10);
}

/**
 * The last N complete UTC days, oldest first. Pure.
 * Today is excluded: the current bucket is partial and usage data lags, so a
 * run of zeroes that includes it is one day shorter than it looks.
 */
export function completeDays(nowEpoch, days) {
  const out = [];
  for (let offset = Math.trunc(days); offset > 0; offset -= 1) {
    const key = dayKey(Math.trunc(nowEpoch) - offset * 86400);
    if (key !== null) out.push(key);
  }
  return out;
}

/**
 * {project_id: {day: count}} from one usage surface. Pure.
 * First recognised count field wins rather than being summed.
 */
export function daily(buckets) {
  const out = new Map();
  for (const bucket of buckets ?? []) {
    const day = dayKey(bucket?.start_time);
    if (day === null) continue;
    for (const result of bucket?.results ?? []) {
      const project = String(result?.project_id ?? 'unknown');
      let count = 0;
      for (const field of COUNT_FIELDS) {
        if (result && field in result) { count = readInt(result[field]); break; }
      }
      if (!out.has(project)) out.set(project, new Map());
      const row = out.get(project);
      row.set(day, (row.get(day) ?? 0) + count);
    }
  }
  return out;
}

/**
 * Classify one project's daily series. Pure. Returns [state, detail].
 * Directional on purpose: traffic early and none late is a project that
 * stopped, the reverse is one that started, and a check that cannot tell them
 * apart fires on every launch and gets muted.
 */
export function classify(series, days, quietDays = 2, minRequests = 100) {
  const axis = [...(days ?? [])];
  if (axis.length <= quietDays) {
    return ['window-too-short',
      `${axis.length} complete day(s) is not enough to hold a ${quietDays} ` +
      'day quiet window'];
  }

  const at = (day) => readInt(series?.get ? series.get(day) : series?.[day]);
  const head = axis.slice(0, axis.length - quietDays);
  const tail = axis.slice(axis.length - quietDays);
  const prior = head.reduce((sum, day) => sum + at(day), 0);
  const recent = tail.reduce((sum, day) => sum + at(day), 0);
  const active = axis.filter((day) => at(day) > 0);

  if (active.length === 0) {
    return ['never-active', `no traffic at all across ${axis.length} complete day(s)`];
  }
  if (prior === 0) {
    return ['new-traffic',
      `first traffic in this window landed on ${active[0]}, inside the last ` +
      `${quietDays} day(s). A launch reads exactly like a death if you only ` +
      'compare halves.'];
  }
  if (recent > 0) {
    return ['live',
      `${recent} request(s) in the last ${quietDays} day(s), against a prior ` +
      `mean of ${Math.trunc(prior / head.length)} a day`];
  }
  if (prior < minRequests) {
    return ['too-little-traffic',
      `${prior} request(s) before the quiet window, under the floor of ` +
      `${minRequests}. Too sporadic for a gap to mean anything.`];
  }

  const last = active[active.length - 1];
  const since = axis.length - 1 - axis.indexOf(last);
  return ['went-quiet',
    `last traffic on ${last}, ${since} complete day(s) ago, after a prior mean ` +
    `of ${Math.trunc(prior / head.length)} request(s) a day`];
}

/** The newest last_used_at across a project's keys. Pure. [epoch, daysSince]. */
export function keyActivity(keys, nowEpoch) {
  let best = null;
  for (const key of keys ?? []) {
    const used = key?.last_used_at;
    if (used === null || used === undefined) continue;
    const n = Number(used);
    if (!Number.isFinite(n)) continue;
    if (best === null || n > best) best = Math.trunc(n);
  }
  if (best === null) return [null, null];
  return [best, Math.max(0, (Math.trunc(nowEpoch) - best) / 86400)];
}

/**
 * Line the key roster up against the silence. Pure. Returns [state, detail].
 * A key still in use while the buckets are empty is a much narrower fault.
 */
export function corroborate(daysSince, quietDays = 2) {
  if (daysSince === null || daysSince === undefined) {
    return ['no-key-use',
      'no key on this project reports a last use, so there is nothing here to ' +
      'corroborate the silence with'];
  }
  if (daysSince <= quietDays) {
    return ['key-still-used',
      `a key on this project was used ${daysSince.toFixed(1)} day(s) ago while ` +
      'the usage buckets were empty. Something is still authenticating and not ' +
      'inferring: a health check, or a surface this sweep did not read.'];
  }
  return ['key-quiet-too',
    `the newest key use is ${daysSince.toFixed(1)} day(s) ago, which lines up ` +
    'with the buckets. The integration went quiet, not one call site.'];
}

/** [quiet, live] surface names for one project. Pure. */
export function surfaceSplit(states) {
  const entries = states instanceof Map ? [...states] : Object.entries(states ?? {});
  const quiet = entries.filter(([, s]) => s === 'went-quiet').map(([n]) => n).sort();
  const live = entries.filter(([, s]) => s === 'live').map(([n]) => n).sort();
  return [quiet, live];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* pages(key, path, params, maxPages = 40) {
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    for (const bucket of page?.data ?? []) yield bucket;
    if (!page?.has_more || !page?.next_page) return;
    query = { ...params, page: page.next_page };
  }
}

async function* listing(key, path, params, maxPages = 20) {
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    const data = page?.data ?? [];
    for (const item of data) yield item;
    if (!page?.has_more || data.length === 0) return;
    query = { ...params, after: data[data.length - 1]?.id };
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key; read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }
  const now = Math.floor(Date.now() / 1000);
  const quietDays = Number(process.env.QUIET_DAYS ?? 2);
  const minRequests = Number(process.env.MIN_REQUESTS ?? 100);
  const showAll = process.env.SHOW_ALL === '1';
  const days = completeDays(now, Math.max(3, Math.min(Number(process.env.DAYS ?? 14), 30)));

  const projects = [];
  for await (const project of listing(admin, '/organization/projects', { limit: 100 })) {
    if (String(project?.status ?? '') === 'active') projects.push(project);
  }
  if (projects.length === 0) {
    console.log('no active projects in this organization');
    return;
  }

  const perSurface = new Map();
  for (const surface of SURFACES) {
    try {
      const buckets = [];
      for await (const bucket of pages(admin, `/organization/usage/${surface}`, {
        start_time: now - (days.length + 1) * 86400,
        bucket_width: '1d',
        limit: days.length + 1,
        group_by: ['project_id'],
      })) buckets.push(bucket);
      perSurface.set(surface, daily(buckets));
    } catch {
      console.log(`skipped the ${surface} usage surface`);
    }
  }

  let checked = 0;
  let bad = 0;
  for (const project of projects) {
    const projectId = String(project?.id ?? '');
    const states = new Map();
    const details = new Map();
    for (const [surface, rows] of perSurface) {
      const [state, detail] = classify(rows.get(projectId), days, quietDays, minRequests);
      states.set(surface, state);
      details.set(surface, detail);
    }
    checked += 1;

    const [quiet, live] = surfaceSplit(states);
    if (quiet.length === 0) {
      if (showAll) console.log(`live               ${projectId}  no surface went quiet`);
      continue;
    }

    bad += 1;
    console.warn(`went-quiet         ${projectId}  ${quiet[0]}: ${details.get(quiet[0])}`);
    const keys = [];
    for await (const key of listing(admin, `/organization/projects/${projectId}/api_keys`,
                                    { limit: 100, owner_project_access: 'any' })) {
      keys.push(key);
    }
    const [, note] = corroborate(keyActivity(keys, now)[1], quietDays);
    console.warn(`  ${note}`);
    if (live.length > 0) {
      console.warn(`  still live on: ${live.join(', ')}`);
      console.warn('  repair: one code path stopped calling, not the credential. ' +
                   'Look at the deploy that touched it rather than at the key.');
    } else {
      console.warn('  repair: every surface is quiet, so look at the credential, ' +
                   'the feature flag or the consumer before the call site.');
    }
    console.warn('  repair: add a scheduled liveness check that alerts on absence. ' +
                 'Read /v1/organization/usage/completions daily with ' +
                 'group_by=project_id and page on next_page, and alert when a ' +
                 'project falls below a floor rather than above a ceiling. This is ' +
                 'the one check whose value is that it fires on zero.');
  }

  console.log(`${checked} active project(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is a fortnight where one project stops on the sixteenth and its neighbour does not, and it asserts the report says the date, how many complete days ago it was, and what the project used to do daily &mdash; because &ldquo;quiet&rdquo; on its own sends nobody anywhere. Immediately after it is the test that stops this check from being muted within a week: the same shape reversed, a project whose traffic <em>starts</em> in the last two days, which has to come back as a launch. The rest pin the day axis excluding today, the key roster telling a dead integration apart from one that is still authenticating, and the surface split that narrows a credential problem down to a single code path.",
"test_py_file": "test_openai_project_went_quiet.py",
"test_py": '''from openai_project_went_quiet import (classify, complete_days, corroborate,
                                       daily, day_key, key_activity,
                                       surface_split)

DAYS = ["2026-08-%02d" % n for n in range(5, 19)]  # 14 complete days
NOW = 1787097600  # 2026-08-19T00:00:00Z


def test_a_project_that_stops_is_named_with_a_date_and_a_volume():
    # The note in one assertion. Twelve busy days, then two empty ones, and the
    # report has to say when it stopped and what it used to do.
    series = {day: 4102 for day in DAYS[:12]}
    state, detail = classify(series, DAYS)
    assert state == "went-quiet"
    assert "last traffic on 2026-08-16" in detail
    assert "2 complete day(s) ago" in detail
    assert "prior mean of 4102 request(s) a day" in detail

    # The project next to it never stopped, and must not be reported.
    assert classify({day: 4102 for day in DAYS}, DAYS)[0] == "live"


def test_a_launch_is_not_a_death_read_backwards():
    # The same shape, reversed. Get this wrong and the check fires on every new
    # project once and is muted by the end of the week.
    state, detail = classify({DAYS[12]: 900, DAYS[13]: 1200}, DAYS)
    assert state == "new-traffic"
    assert "first traffic in this window landed on 2026-08-17" in detail


def test_the_quiet_states_that_are_not_findings():
    assert classify({}, DAYS)[0] == "never-active"
    assert classify({DAYS[0]: 4}, DAYS)[0] == "too-little-traffic"
    assert classify({DAYS[0]: 4102}, DAYS[:2])[0] == "window-too-short"
    assert classify(None, DAYS)[0] == "never-active"


def test_today_is_never_in_the_axis():
    days = complete_days(NOW, 14)
    assert days == DAYS
    assert day_key(NOW) == "2026-08-19"
    assert day_key(NOW) not in days
    assert day_key("not an epoch") is None


def test_a_project_absent_from_a_bucket_is_a_zero_not_a_gap():
    # Buckets come back for the whole range; a project with no traffic is
    # simply not in the results. The day axis has to come from the window.
    buckets = [{"start_time": 1786579200,
                "results": [{"project_id": "proj_busy", "num_model_requests": 10}]},
               {"start_time": 1786665600, "results": []}]
    rows = daily(buckets)
    assert rows == {"proj_busy": {"2026-08-13": 10}}
    assert rows.get("proj_quiet") is None
    # Other surfaces count other things, and only one field is ever present.
    assert daily([{"start_time": 1786579200,
                   "results": [{"project_id": "p", "num_images": 7}]}]) \\
        == {"p": {"2026-08-13": 7}}
    assert daily([]) == {}


def test_a_key_still_in_use_means_something_is_authenticating():
    keys = [{"last_used_at": NOW - 3600}, {"last_used_at": None},
            {"last_used_at": NOW - 900000}]
    used, since = key_activity(keys, NOW)
    assert used == NOW - 3600
    assert round(since, 2) == 0.04
    state, detail = corroborate(since)
    assert state == "key-still-used"
    assert "authenticating and not inferring" in detail


def test_a_key_frozen_with_the_buckets_means_the_integration_died():
    _, since = key_activity([{"last_used_at": NOW - 11 * 86400}], NOW)
    state, detail = corroborate(since)
    assert state == "key-quiet-too"
    assert "11.0 day(s) ago" in detail
    assert key_activity([], NOW) == (None, None)
    assert key_activity([{"last_used_at": "never"}], NOW) == (None, None)
    assert corroborate(None)[0] == "no-key-use"


def test_one_quiet_surface_beside_a_live_one_is_a_code_path():
    quiet, live = surface_split({"completions": "went-quiet",
                                 "embeddings": "live",
                                 "images": "never-active"})
    assert quiet == ["completions"]
    assert live == ["embeddings"]
    assert surface_split({}) == ([], [])
''',
"test_js_file": "openai-project-went-quiet.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, completeDays, corroborate, daily, dayKey, keyActivity,
         surfaceSplit } from './openai-project-went-quiet.mjs';

const DAYS = Array.from({ length: 14 }, (_, i) => `2026-08-${String(i + 5).padStart(2, '0')}`);
const NOW = 1787097600; // 2026-08-19T00:00:00Z

test('a project that stops is named with a date and a volume', () => {
  const series = new Map(DAYS.slice(0, 12).map((day) => [day, 4102]));
  const [state, detail] = classify(series, DAYS);
  assert.equal(state, 'went-quiet');
  assert.match(detail, /last traffic on 2026-08-16/);
  assert.match(detail, /2 complete day\\(s\\) ago/);
  assert.match(detail, /prior mean of 4102 request\\(s\\) a day/);

  const busy = new Map(DAYS.map((day) => [day, 4102]));
  assert.equal(classify(busy, DAYS)[0], 'live');
});

test('a launch is not a death read backwards', () => {
  const [state, detail] = classify(new Map([[DAYS[12], 900], [DAYS[13], 1200]]), DAYS);
  assert.equal(state, 'new-traffic');
  assert.match(detail, /first traffic in this window landed on 2026-08-17/);
});

test('the quiet states that are not findings', () => {
  assert.equal(classify(new Map(), DAYS)[0], 'never-active');
  assert.equal(classify(new Map([[DAYS[0], 4]]), DAYS)[0], 'too-little-traffic');
  assert.equal(classify(new Map([[DAYS[0], 4102]]), DAYS.slice(0, 2))[0],
               'window-too-short');
  assert.equal(classify(null, DAYS)[0], 'never-active');
});

test('today is never in the axis', () => {
  const days = completeDays(NOW, 14);
  assert.deepEqual(days, DAYS);
  assert.equal(dayKey(NOW), '2026-08-19');
  assert.ok(!days.includes(dayKey(NOW)));
  assert.equal(dayKey('not an epoch'), null);
});

test('a project absent from a bucket is a zero not a gap', () => {
  const buckets = [
    { start_time: 1786579200,
      results: [{ project_id: 'proj_busy', num_model_requests: 10 }] },
    { start_time: 1786665600, results: [] },
  ];
  const rows = daily(buckets);
  assert.deepEqual([...rows.get('proj_busy')], [['2026-08-13', 10]]);
  assert.equal(rows.get('proj_quiet'), undefined);
  const images = daily([{ start_time: 1786579200,
                          results: [{ project_id: 'p', num_images: 7 }] }]);
  assert.deepEqual([...images.get('p')], [['2026-08-13', 7]]);
  assert.equal(daily([]).size, 0);
});

test('a key still in use means something is authenticating', () => {
  const keys = [{ last_used_at: NOW - 3600 }, { last_used_at: null },
                { last_used_at: NOW - 900000 }];
  const [used, since] = keyActivity(keys, NOW);
  assert.equal(used, NOW - 3600);
  assert.equal(Number(since.toFixed(2)), 0.04);
  const [state, detail] = corroborate(since);
  assert.equal(state, 'key-still-used');
  assert.match(detail, /authenticating and not inferring/);
});

test('a key frozen with the buckets means the integration died', () => {
  const [, since] = keyActivity([{ last_used_at: NOW - 11 * 86400 }], NOW);
  const [state, detail] = corroborate(since);
  assert.equal(state, 'key-quiet-too');
  assert.match(detail, /11\\.0 day\\(s\\) ago/);
  assert.deepEqual(keyActivity([], NOW), [null, null]);
  assert.deepEqual(keyActivity([{ last_used_at: 'never' }], NOW), [null, null]);
  assert.equal(corroborate(null)[0], 'no-key-use');
});

test('one quiet surface beside a live one is a code path', () => {
  const [quiet, live] = surfaceSplit({ completions: 'went-quiet',
                                       embeddings: 'live',
                                       images: 'never-active' });
  assert.deepEqual(quiet, ['completions']);
  assert.deepEqual(live, ['embeddings']);
  assert.deepEqual(surfaceSplit({}), [[], []]);
});
''',
"faq": [
 ("Does the usage endpoint really return buckets for days with no traffic?",
  "It returns a bucket for every interval in the range you asked for, and for an interval with nothing in it the results array comes back empty. That is what makes the silence readable at all. It also means a project with no traffic is simply absent from the results rather than present with a zero, so the day axis has to be built from the window you requested and not from the days the response happened to contain."),
 ("Why not just alert on spend dropping?",
  "Because spend is an organization-level series and this failure is project-level and often small. A project that does four thousand calls a day inside an organization doing four hundred thousand can go completely dark without moving the invoice enough to notice. Cost anomaly detection and a per-project floor answer different questions, and only one of them fires when a feature quietly stops working."),
 ("How long a quiet window should I use?",
  "Long enough to survive the traffic pattern and the reporting lag, short enough to be worth having. Forty-eight hours suits a service that runs every day; a batch job that only runs on Mondays needs a window measured in weeks, or a schedule-aware check instead of a flat one. The wrong answer is a window so short that a quiet Sunday pages somebody, because that is how the alarm gets turned off."),
 ("Isn't this the same as finding a key whose owner left?",
  "No. That check reads a flag the platform sets for you, on a key whose owner lost access to the project. Here nothing is flagged: the key is valid, the project is active, and the credential would work perfectly if anything called it. The provider has no opinion to read, which is why the evidence has to be assembled out of an absence."),
 ("The project is quiet on completions but busy on embeddings. What does that mean?",
  "That the credential is fine and one code path stopped. It is a much narrower search than a dead project: look at what shipped near the last day with traffic, at the feature flag guarding that call, and at whatever produces the events that used to trigger it. The script reports the surfaces separately for exactly this reason."),
],
"related": [REL_KEY_OWNER, REL_ARCHIVED, REL_SPIKE],
"citations": [CITE_OAI_USAGE, CITE_OAI_PROJECTS, CITE_OAI_PROJECT_KEYS, CITE_OAI_ADMIN],
},
]
