#!/usr/bin/env python3
"""/llm/ field notes, batch F — the writing.

Four notes that all end up on an invoice and are not four readings of one
invoice. Each asks the platform a different question and can only be answered
by a different endpoint.

`frontier-model-on-trivial-workload` is a ratio. Divide output tokens by
request count and you have the shape of the work rather than its volume: a
premium model returning twenty-token answers a hundred thousand times is
answering questions that do not need it. Nothing about the money is in that
finding; it is arithmetic on two integers the usage endpoint already returns.

`per-tenant-cost-attribution-impossible` is not a cost finding at all. It is a
finding about what the reporting dimensions mean. `user_id` on the Usage API
names your own org members and service accounts, never your customers, so the
question "what does customer X cost us" has no answer to look up and no
application change that would create one. The script proves that by resolving
every returned principal against the org directory.

`audio-and-image-line-items-unnoticed` is a reconciliation between two
endpoints that are denominated in different units. Money lives on the cost
report, grouped by `line_item`. Tokens live on completions. Characters,
seconds, images, sessions and calls live on six other usage surfaces that a
token dashboard cannot see at all. The finding is the size of the hole between
them, in dollars.

`fine-tuned-model-never-used` is an inventory join with a clock on it. A
succeeded fine-tuning job names a model id, that id was billed for training,
and thirty days of usage grouped by model shows it was never called once. The
clock is the platform wind-down, which will retire the asset whether or not
anyone decides what to do with it.

Read-only throughout. Three of the four need an organization admin key
provisioned read-only, because `/v1/organization/*` rejects a project key
outright; the fourth needs a project key as well, to read the fine-tuning jobs
that an admin key cannot see. GET requests only, and every repair printed for a
human to run: routing traffic to a different model, minting keys, and deleting
custom models are all deploys, not side effects of an audit.
"""

CITE_USAGE_COMPLETIONS = ("Usage: completions — OpenAI API reference",
                          "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_USAGE = ("Usage — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage")
CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_ADMIN = ("Administration and the Admin APIs — OpenAI developer docs",
              "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_PROJECTS = ("Projects — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/projects")
CITE_PROJECT_KEYS = ("Project API keys — OpenAI API reference",
                     "https://platform.openai.com/docs/api-reference/project-api-keys")
CITE_OPENAPI = ("openai-openapi — the published OpenAPI specification",
                "https://github.com/openai/openai-openapi/blob/master/openapi.yaml")
CITE_PY_API = ("openai-python api.md — the generated method index",
               "https://github.com/openai/openai-python/blob/main/api.md")
CITE_FINE_TUNING = ("Fine-tuning — OpenAI API reference",
                    "https://developers.openai.com/api/docs/api-reference/fine-tuning")
CITE_DEPRECATIONS = ("Deprecations — OpenAI developer docs",
                     "https://developers.openai.com/api/docs/deprecations")
CITE_FILES = ("Files — OpenAI API reference",
              "https://developers.openai.com/api/docs/api-reference/files")
CITE_AN_USAGE = ("Get messages usage report — Claude Docs",
                 "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")

REL_FRONTIER = ("/llm/frontier-model-on-trivial-workload/",
                "A premium model answering twenty-token questions")
REL_TENANT = ("/llm/per-tenant-cost-attribution-impossible/",
              "Why the Usage API cannot segment by your customers")
REL_MODALITY = ("/llm/audio-and-image-line-items-unnoticed/",
                "Spend that is not denominated in tokens at all")
REL_FT = ("/llm/fine-tuned-model-never-used/",
          "A custom model that was trained, billed, and never called")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")
REL_CACHE = ("/llm/prompt-caching-never-used/",
             "A stable prefix reprocessed at full price on every call")
REL_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                   "Nothing in the platform stops a runaway bill")
REL_ARCHIVED = ("/llm/archived-project-still-holds-keys/",
                "An archived project whose keys still work")
REL_SHUTDOWN = ("/llm/model-past-shutdown-date/",
                "A model id already past the date it stops answering")

GUIDES = [

{
"slug": "frontier-model-on-trivial-workload",
"title": "A frontier model is answering twenty-token questions",
"description": "Divide output_tokens by num_model_requests on the usage endpoint. A premium model whose mean answer is twenty tokens is the wrong size for the work.",
"h1": "a frontier model is answering twenty-token questions",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai usage output tokens per request", "gpt-5-mini vs gpt-5 cost",
             "openai model right sizing", "openai project model_permissions allow_list",
             "openai usage api group_by model"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_ADMIN_KEY, an organization admin key with read scopes.",
"lead": "Somebody built the intent router in an afternoon eighteen months ago. They pasted the model name out of the quickstart, because on that afternoon the question was whether the thing worked at all and the answer was worth whatever it cost. It works. It has worked every day since, four hundred thousand times a month, and every one of those calls returns a single word from a list of nine. The model that returns it is the most expensive one the organization can buy.",
"short_answer": """<p>One call with an organization <strong>admin</strong> key: <code>GET /v1/organization/usage/completions?start_time={now-14d}&amp;bucket_width=1d&amp;limit=14&amp;group_by=model&amp;group_by=project_id</code>. Every result carries <code>input_tokens</code>, <code>output_tokens</code> and <code>num_model_requests</code>. Fold them per model and divide.</p>
<p>The finding is a ratio, not a total. <code>output_tokens / num_model_requests</code> is the mean length of what the model actually said. A premium model with a high request count and a mean answer under about fifty tokens is answering questions a <code>-mini</code> sibling would answer identically, at roughly a tenth of the price.</p>
<p>Two shapes have to be held apart from that one. A premium model with long answers is doing the work it was chosen for. A premium model with short answers and enormous prompts is not a model-size problem at all &mdash; the bill there is input, and the lever is <a href="/llm/prompt-caching-never-used/">caching</a>.</p>""",
"problem": """<p>Nothing is broken. There is no error, no latency complaint, no failing eval, and no dashboard row that looks unusual: the model with the largest spend is the model doing the most work, which is what you would expect. The workload that is mis-sized is buried inside that row, and the only thing that distinguishes it is that its answers are short.</p>
<p>What keeps it alive is that model selection is a string literal. It is chosen once, during prototyping, at the exact moment when correctness matters and cost does not, and then it is inherited &mdash; copied into the next service, pulled from the shared config, defaulted in a wrapper library. Nothing in the API distinguishes a model that is necessary from a model that is habitual, so nothing ever prompts the question. Twelve months later the classifier, the title generator, the tag extractor and the yes/no guardrail are all running on the frontier model, and each of them is one line away from costing a tenth as much.</p>""",
"why": """<p><strong>Shape is visible where quality is not.</strong> The API will never tell you whether a model was needed. It will tell you how many requests were made and how many tokens came back, and the quotient of those two is the closest thing to a description of the task that the platform holds. Twenty tokens is a label. Two thousand is an argument. The first does not need a frontier model and the second might.</p>
<p><strong>Volume and shape are independent, and only one of them is a finding.</strong> A model with a small share of spend can still be mis-sized, and a model with most of the spend can be perfectly chosen. Sorting by cost finds the biggest line; sorting by mean output length finds the wrong one. They are different questions and this script asks the second.</p>
<p><strong>A short answer over a huge prompt is a different problem.</strong> Retrieval and summarisation produce exactly the signature this check looks for &mdash; many requests, tiny outputs &mdash; and swapping the model there saves far less than it looks like, because the money is on the input side. Mean input tokens per request separates the two, and the script reports them as different states rather than one.</p>
<p><strong>The durable fix is a permission, not a config change.</strong> <code>GET /v1/organization/projects/{project_id}/model_permissions</code> returns a <code>mode</code> of <code>allow_list</code> or <code>deny_list</code> and a list of <code>model_ids</code>. A project that is unconstrained will drift back to the expensive model the next time somebody copies a snippet. A project restricted to the cheap models cannot.</p>
<p><strong>This check cannot be done on the Claude side.</strong> <code>GET /v1/organizations/usage_report/messages</code> returns token sums per bucket and carries no request-count field at all, so there is no denominator and no mean answer length to compute. Model right-sizing on Anthropic has to be argued from token volume and from your own client-side call counts, not from the usage report.</p>""",
"steps": [
 {"h": "Pull fourteen days grouped by model and project",
  "body": """<p><code>GET /v1/organization/usage/completions</code> with <code>start_time</code> set to fourteen days ago, <code>bucket_width=1d</code>, <code>limit=14</code>, and both <code>group_by=model</code> and <code>group_by=project_id</code>. Fourteen days is long enough to average out a quiet weekend and short enough that a model changed last month is not still in the numbers.</p>"""},
 {"h": "Fold the buckets before you divide",
  "body": """<p>Each daily bucket holds one result per model and project combination. Sum <code>num_model_requests</code>, <code>input_tokens</code> and <code>output_tokens</code> across the whole window first, then take the quotient. Dividing per bucket and averaging the quotients weights a quiet Sunday the same as a Tuesday.</p>"""},
 {"h": "Put a floor under the request count",
  "body": """<p>A model with forty calls in a fortnight has a mean output length that means nothing, and reporting it wastes the reader's attention on noise. The script reports anything under the floor as <code>low-volume</code> and moves on rather than pretending to have a verdict.</p>"""},
 {"h": "Read mean input as well as mean output",
  "body": """<p>Short answers plus small prompts is a mis-sized model. Short answers plus twenty-thousand-token prompts is a retrieval workload, and the saving there is in the prefix, not the model tier. The script says which one it found, and points the second at the <a href="/llm/prompt-caching-never-used/">caching note</a> instead of at a cheaper model.</p>"""},
 {"h": "Price it, then print the permission body",
  "body": """<p><code>GET /v1/organization/costs?start_time=…&amp;group_by=line_item</code> gives the model's real thirty-day spend, which turns "use the mini one" into a number. Then print the <code>model_permissions</code> body that would stop the project reaching the expensive model at all. Printing it is the whole point: an audit script holding an admin key should not be what decides which model serves your traffic.</p>"""},
],
"verify": """<p>Re-run a fortnight after the router is moved. The model should have dropped out of the findings entirely, not merely shrunk.</p>
<pre><code class="language-bash">python3 openai_model_rightsizing_audit.py
# oversized    gpt-5           412,880 request(s), mean output 19 token(s)
#   repair: gpt-5-mini answers this shape of question; 14d spend on gpt-5 was $3,411.20
# 6 model(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One usage call, one costs call, and one permissions call per project that appeared, all GET. It wants <code>OPENAI_ADMIN_KEY</code>, an organization admin key with read scopes, because a project key is rejected by every <code>/v1/organization</code> endpoint. Five pure functions carry the judgement: which tier a model id belongs to, which cheaper sibling replaces it, how the daily buckets fold, what the folded numbers mean, and whether the project is constrained from reaching the expensive model in the first place.",
"py_file": "openai_model_rightsizing_audit.py",
"py": '''"""Report OpenAI models that are larger than the work they are doing.

Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
organization admin key (sk-admin-...) with read scopes, because every
/v1/organization endpoint rejects a project key outright.

The repair is printed, never performed. Which model serves production traffic
is a deploy, and restricting a project's model permissions changes what your
colleagues are allowed to call. Neither belongs to an audit script.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_model_rightsizing_audit")

API = "https://api.openai.com/v1"

# Substrings that mean "this is already the small sibling". Matched on the model
# id because there is no field on the usage result that says how big a model is.
SMALL_MARKERS = ("mini", "nano", "small", "lite", "embedding", "moderation")

# The families worth right-sizing, in the order they are tested. Each maps to the
# cheaper sibling that answers the same shape of question. Kept as a table rather
# than a string rule because "gpt-5" -> "gpt-5-mini" is a naming convention, not
# a guarantee, and a wrong suggestion here is worse than none.
SIBLINGS = (
    ("gpt-5", "gpt-5-mini"),
    ("gpt-4.1", "gpt-4.1-mini"),
    ("gpt-4o", "gpt-4o-mini"),
    ("o3", "o4-mini"),
    ("o1", "o4-mini"),
)

FINDINGS = ("oversized",)


def tier(model):
    """Classify a model id. Pure, and deliberately conservative.

    Returns "custom" for a fine-tune, "small" for a model that is already the
    cheap sibling, "premium" for a family with a cheaper sibling to move to, and
    "unknown" for everything else. Unknown is not a finding: a model this table
    has never heard of is a model this script has no business advising on.
    """
    name = str(model or "").strip().lower()
    if not name:
        return "unknown"
    if name.startswith("ft:"):
        return "custom"
    if any(marker in name for marker in SMALL_MARKERS):
        return "small"
    for family, _cheaper in SIBLINGS:
        if name.startswith(family):
            return "premium"
    return "unknown"


def sibling(model):
    """The cheaper model that answers the same shape of question, or None. Pure."""
    name = str(model or "").strip().lower()
    if tier(name) != "premium":
        return None
    for family, cheaper in SIBLINGS:
        if name.startswith(family):
            return cheaper
    return None


def fold(pages):
    """Sum the daily buckets into one row per model. Pure.

    Folding before dividing matters: a mean taken per bucket and then averaged
    weights a quiet Sunday exactly as heavily as a Tuesday, which is how a model
    that is busy on weekdays acquires a flattering output-per-request number.

    project_ids are collected as a sorted list so the caller knows which projects
    to ask about model permissions, and so two runs print the same order.
    """
    out = {}
    for page in pages:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                model = str(result.get("model") or "").strip()
                if not model:
                    continue
                row = out.setdefault(model, {"requests": 0, "input": 0,
                                             "output": 0, "projects": set()})
                for field, key in (("num_model_requests", "requests"),
                                   ("input_tokens", "input"),
                                   ("output_tokens", "output")):
                    try:
                        row[key] += int(result.get(field) or 0)
                    except (TypeError, ValueError):
                        pass
                project = result.get("project_id")
                if project:
                    row["projects"].add(str(project))
    return {m: {**row, "projects": sorted(row["projects"])} for m, row in out.items()}


def verdict(model, row, min_requests=500, trivial_output=50, long_input=20000):
    """Classify one folded model row. Pure. Returns (state, detail).

    The order is the argument. A model with too few calls has no shape to read.
    A model that is already small, or that this script does not recognise, is
    not advised on at all. Only then does the ratio decide, and short answers
    over enormous prompts are separated out because the money there is on the
    input side and swapping the model saves almost none of it.
    """
    try:
        requests_made = int(row.get("requests") or 0)
    except (TypeError, ValueError):
        return ("unreadable",
                "num_model_requests did not sum to an integer, so there is no "
                "denominator and no ratio to read")
    if requests_made <= 0:
        return ("unreadable",
                "0 request(s) in the window, so there is nothing to divide by")
    if requests_made < min_requests:
        return ("low-volume",
                "%d request(s) in the window, under the floor of %d. A mean "
                "taken over this few calls is noise, not a shape."
                % (requests_made, min_requests))

    out_per = (row.get("output") or 0) / float(requests_made)
    in_per = (row.get("input") or 0) / float(requests_made)
    shape = ("%d request(s), mean output %.0f token(s), mean input %.0f token(s)"
             % (requests_made, out_per, in_per))

    kind = tier(model)
    if kind == "custom":
        return ("custom-model",
                "%s. This is a fine-tune, and its size is inherited from the "
                "base model rather than chosen here." % shape)
    if kind == "small":
        return ("right-sized",
                "%s. Already the cheap sibling for its family." % shape)
    if kind != "premium":
        return ("unknown-model",
                "%s. No cheaper sibling is known for this model id, so this "
                "script has no recommendation to make about it." % shape)

    if out_per >= trivial_output:
        return ("deliberative",
                "%s. The answers are long enough that the model is plausibly "
                "doing the work it was chosen for." % shape)
    if in_per >= long_input:
        return ("input-bound",
                "%s. Short answers over very large prompts. The bill here is "
                "input, not model tier, so caching the prefix will save more "
                "than downgrading the model." % shape)
    return ("oversized",
            "%s. A premium model returning answers this short is answering "
            "questions a cheaper sibling would answer identically." % shape)


def permissions_state(perms, model):
    """Can this project still reach this model? Pure. Returns a state string.

    GET /v1/organization/projects/{id}/model_permissions returns a mode of
    allow_list or deny_list with a model_ids array. An unconstrained project is
    the durable half of the finding: without a restriction the expensive model
    comes back the next time somebody copies a snippet from the quickstart.
    """
    if not isinstance(perms, dict):
        return "unreadable"
    mode = str(perms.get("mode") or "").strip().lower()
    ids = perms.get("model_ids")
    if not isinstance(ids, list):
        ids = []
    ids = [str(i).strip().lower() for i in ids]
    name = str(model or "").strip().lower()

    if mode == "allow_list":
        if not ids:
            return "blocked"
        return "allowed" if name in ids else "blocked"
    if mode == "deny_list":
        if not ids:
            return "unconstrained"
        return "blocked" if name in ids else "allowed"
    return "unreadable"


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: OPENAI_ADMIN_KEY must be an "
                         "organization admin key, not a project key")
    if r.status_code == 403:
        raise SystemExit("403 from OpenAI: the key is not authorised for "
                         "/v1/organization. A project key cannot read usage.")
    r.raise_for_status()
    return r.json()


def usage_pages(session, start_time, days, max_pages=20):
    """Walk the usage endpoint, which paginates on next_page."""
    params = {"start_time": start_time, "bucket_width": "1d", "limit": days,
              "group_by": ["model", "project_id"]}
    for _ in range(max_pages):
        page = get(session, "/organization/usage/completions", params)
        yield page
        cursor = page.get("next_page")
        if not cursor:
            return
        params = dict(params, page=cursor)


def spend_by_line_item(session, start_time):
    """Thirty days of spend, keyed by the cost report's line_item string."""
    out = {}
    page = get(session, "/organization/costs",
               {"start_time": start_time, "limit": 31, "group_by": "line_item"})
    for bucket in page.get("data") or []:
        for result in bucket.get("results") or []:
            item = str(result.get("line_item") or "")
            amount = (result.get("amount") or {}).get("value") or 0
            try:
                out[item] = out.get(item, 0.0) + float(amount)
            except (TypeError, ValueError):
                pass
    return out


def spend_for(model, spend):
    """Best-effort match of a model id against the cost report's line items."""
    name = str(model or "").strip().lower()
    total = 0.0
    for item, amount in spend.items():
        if name and name in item.lower():
            total += amount
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="days of usage to fold (default 14)")
    ap.add_argument("--min-requests", type=int, default=500,
                    help="ignore models with fewer calls than this (default 500)")
    ap.add_argument("--trivial-output", type=int, default=50,
                    help="mean output tokens under which work is trivial (default 50)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print models that are the right size")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read scopes)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    now = dt.datetime.now(dt.timezone.utc)
    usage_start = int((now - dt.timedelta(days=args.days)).timestamp())
    cost_start = int((now - dt.timedelta(days=30)).timestamp())

    rows = fold(usage_pages(session, usage_start, args.days))
    spend = spend_by_line_item(session, cost_start)

    checked = 0
    bad = 0
    for model in sorted(rows):
        row = rows[model]
        state, detail = verdict(model, row, args.min_requests, args.trivial_output)
        checked += 1
        line = "%-14s %-16s %s" % (state, model, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            cheaper = sibling(model)
            money = spend_for(model, spend)
            log.warning("  repair: %s answers this shape of question; 30d spend "
                        "on %s was $%.2f", cheaper, model, money)
            for project in row["projects"]:
                perms = get(session,
                            "/organization/projects/%s/model_permissions" % project)
                where = permissions_state(perms, model)
                if where == "unconstrained":
                    log.warning("  repair: project %s is unconstrained. To make "
                                "the change durable, set model_permissions to "
                                "mode allow_list with model_ids [%r] so the "
                                "expensive model cannot come back.",
                                project, cheaper)
                else:
                    log.warning("  note: project %s model_permissions say %s",
                                project, where)
        elif state == "input-bound":
            log.warning(line)
            log.warning("  repair: read the prompt-caching note before changing "
                        "the model. A stable prefix at this size is the bill.")
        elif state in ("unreadable",):
            log.warning(line)
        elif args.show_all:
            log.info(line)

    log.info("%d model(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-model-rightsizing-audit.mjs",
"js": '''/**
 * Report OpenAI models that are larger than the work they are doing.
 *
 * Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
 * organization admin key with read scopes, because every /v1/organization
 * endpoint rejects a project key outright. The repair is printed, never
 * performed.
 */
const API = 'https://api.openai.com/v1';

// Substrings that mean "this is already the small sibling".
const SMALL_MARKERS = ['mini', 'nano', 'small', 'lite', 'embedding', 'moderation'];

// The families worth right-sizing, each mapped to the cheaper sibling that
// answers the same shape of question. A table rather than a string rule,
// because a wrong suggestion here is worse than no suggestion.
const SIBLINGS = [
  ['gpt-5', 'gpt-5-mini'],
  ['gpt-4.1', 'gpt-4.1-mini'],
  ['gpt-4o', 'gpt-4o-mini'],
  ['o3', 'o4-mini'],
  ['o1', 'o4-mini'],
];

const FINDINGS = ['oversized'];

/**
 * Classify a model id. Pure, and deliberately conservative: "unknown" is not a
 * finding, because a model this table has never heard of is one this script has
 * no business advising on.
 */
export function tier(model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return 'unknown';
  if (name.startsWith('ft:')) return 'custom';
  if (SMALL_MARKERS.some((m) => name.includes(m))) return 'small';
  for (const [family] of SIBLINGS) if (name.startsWith(family)) return 'premium';
  return 'unknown';
}

/** The cheaper model answering the same shape of question, or null. Pure. */
export function sibling(model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (tier(name) !== 'premium') return null;
  for (const [family, cheaper] of SIBLINGS) {
    if (name.startsWith(family)) return cheaper;
  }
  return null;
}

/**
 * Sum the daily buckets into one row per model. Pure.
 *
 * Folding before dividing matters: a mean taken per bucket and then averaged
 * weights a quiet Sunday as heavily as a Tuesday.
 */
export function fold(pages) {
  const out = new Map();
  for (const page of pages) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const model = String(result.model ?? '').trim();
        if (!model) continue;
        if (!out.has(model)) {
          out.set(model, { requests: 0, input: 0, output: 0, projects: new Set() });
        }
        const row = out.get(model);
        for (const [field, key] of [['num_model_requests', 'requests'],
                                    ['input_tokens', 'input'],
                                    ['output_tokens', 'output']]) {
          const n = Number(result[field] ?? 0);
          if (Number.isFinite(n)) row[key] += Math.trunc(n);
        }
        if (result.project_id) row.projects.add(String(result.project_id));
      }
    }
  }
  const folded = {};
  for (const [model, row] of out) {
    folded[model] = { ...row, projects: [...row.projects].sort() };
  }
  return folded;
}

/**
 * Classify one folded model row. Pure. Returns [state, detail].
 * Short answers over enormous prompts are separated out, because the money
 * there is on the input side and swapping the model saves almost none of it.
 */
export function verdict(model, row, minRequests = 500, trivialOutput = 50,
                        longInput = 20000) {
  const requestsMade = Number(row.requests ?? 0);
  if (!Number.isFinite(requestsMade)) {
    return ['unreadable',
      'num_model_requests did not sum to a number, so there is no denominator ' +
      'and no ratio to read'];
  }
  if (requestsMade <= 0) {
    return ['unreadable', '0 request(s) in the window, so there is nothing to divide by'];
  }
  if (requestsMade < minRequests) {
    return ['low-volume',
      `${requestsMade} request(s) in the window, under the floor of ` +
      `${minRequests}. A mean taken over this few calls is noise, not a shape.`];
  }

  const outPer = Number(row.output ?? 0) / requestsMade;
  const inPer = Number(row.input ?? 0) / requestsMade;
  const shape = `${requestsMade} request(s), mean output ${outPer.toFixed(0)} ` +
                `token(s), mean input ${inPer.toFixed(0)} token(s)`;

  const kind = tier(model);
  if (kind === 'custom') {
    return ['custom-model',
      `${shape}. This is a fine-tune, and its size is inherited from the base ` +
      'model rather than chosen here.'];
  }
  if (kind === 'small') {
    return ['right-sized', `${shape}. Already the cheap sibling for its family.`];
  }
  if (kind !== 'premium') {
    return ['unknown-model',
      `${shape}. No cheaper sibling is known for this model id, so this script ` +
      'has no recommendation to make about it.'];
  }

  if (outPer >= trivialOutput) {
    return ['deliberative',
      `${shape}. The answers are long enough that the model is plausibly doing ` +
      'the work it was chosen for.'];
  }
  if (inPer >= longInput) {
    return ['input-bound',
      `${shape}. Short answers over very large prompts. The bill here is input, ` +
      'not model tier, so caching the prefix will save more than downgrading ' +
      'the model.'];
  }
  return ['oversized',
    `${shape}. A premium model returning answers this short is answering ` +
    'questions a cheaper sibling would answer identically.'];
}

/**
 * Can this project still reach this model? Pure. An unconstrained project is
 * the durable half of the finding: without a restriction the expensive model
 * comes back the next time somebody copies a snippet from the quickstart.
 */
export function permissionsState(perms, model) {
  if (perms === null || typeof perms !== 'object' || Array.isArray(perms)) {
    return 'unreadable';
  }
  const mode = String(perms.mode ?? '').trim().toLowerCase();
  const ids = (Array.isArray(perms.model_ids) ? perms.model_ids : [])
    .map((i) => String(i).trim().toLowerCase());
  const name = String(model ?? '').trim().toLowerCase();

  if (mode === 'allow_list') {
    if (ids.length === 0) return 'blocked';
    return ids.includes(name) ? 'allowed' : 'blocked';
  }
  if (mode === 'deny_list') {
    if (ids.length === 0) return 'unconstrained';
    return ids.includes(name) ? 'blocked' : 'allowed';
  }
  return 'unreadable';
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: OPENAI_ADMIN_KEY must be an organization ' +
                    'admin key, not a project key');
  }
  if (res.status === 403) {
    throw new Error('403 from OpenAI: the key is not authorised for ' +
                    '/v1/organization. A project key cannot read usage.');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function usagePages(key, startTime, days, maxPages = 20) {
  const pages = [];
  let params = {
    start_time: startTime, bucket_width: '1d', limit: days,
    group_by: ['model', 'project_id'],
  };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/usage/completions', params);
    pages.push(page);
    if (!page.next_page) break;
    params = { ...params, page: page.next_page };
  }
  return pages;
}

async function spendByLineItem(key, startTime) {
  const out = {};
  const page = await get(key, '/organization/costs',
    { start_time: startTime, limit: 31, group_by: 'line_item' });
  for (const bucket of page.data ?? []) {
    for (const result of bucket.results ?? []) {
      const item = String(result.line_item ?? '');
      const amount = Number(result.amount?.value ?? 0);
      if (Number.isFinite(amount)) out[item] = (out[item] ?? 0) + amount;
    }
  }
  return out;
}

function spendFor(model, spend) {
  const name = String(model ?? '').trim().toLowerCase();
  let total = 0;
  for (const [item, amount] of Object.entries(spend)) {
    if (name && item.toLowerCase().includes(name)) total += amount;
  }
  return total;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read scopes)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 14);
  const minRequests = Number(process.env.MIN_REQUESTS ?? 500);
  const trivialOutput = Number(process.env.TRIVIAL_OUTPUT ?? 50);
  const showAll = process.argv.includes('--show-all');

  const now = Math.floor(Date.now() / 1000);
  const rows = fold(await usagePages(key, now - days * 86400, days));
  const spend = await spendByLineItem(key, now - 30 * 86400);

  let checked = 0;
  let bad = 0;
  for (const model of Object.keys(rows).sort()) {
    const row = rows[model];
    const [state, detail] = verdict(model, row, minRequests, trivialOutput);
    checked += 1;
    const line = `${state.padEnd(14)} ${model.padEnd(16)} ${detail}`;

    if (FINDINGS.includes(state)) {
      bad += 1;
      console.warn(line);
      const cheaper = sibling(model);
      console.warn(`  repair: ${cheaper} answers this shape of question; 30d ` +
                   `spend on ${model} was $${spendFor(model, spend).toFixed(2)}`);
      for (const project of row.projects) {
        const perms = await get(key,
          `/organization/projects/${project}/model_permissions`);
        const where = permissionsState(perms, model);
        if (where === 'unconstrained') {
          console.warn(`  repair: project ${project} is unconstrained. To make ` +
            `the change durable, set model_permissions to mode allow_list with ` +
            `model_ids ['${cheaper}'] so the expensive model cannot come back.`);
        } else {
          console.warn(`  note: project ${project} model_permissions say ${where}`);
        }
      }
    } else if (state === 'input-bound') {
      console.warn(line);
      console.warn('  repair: read the prompt-caching note before changing the ' +
                   'model. A stable prefix at this size is the bill.');
    } else if (state === 'unreadable') {
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${checked} model(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is that a high-volume premium model with a mean output of nineteen tokens is a finding, and that the same ratio on the mini sibling is not &mdash; the whole note is that shape and tier have to be read together. The rest hold the near misses apart: long answers on a premium model are the model doing its job, short answers over a huge prompt are a caching problem wearing this problem's signature, and a model too quiet to have a shape gets no verdict at all.",
"test_py_file": "test_openai_model_rightsizing_audit.py",
"test_py": '''from openai_model_rightsizing_audit import (fold, permissions_state, sibling,
                                            tier, verdict)


def row(requests=10000, output=190000, input_=900000, projects=("proj_a",)):
    """A folded row shaped like fold() returns them."""
    return {"requests": requests, "output": output, "input": input_,
            "projects": list(projects)}


def bucket(**results):
    """One daily bucket from GET /v1/organization/usage/completions."""
    return {"data": [{"start_time": 0, "results": [
        {"model": m, "num_model_requests": r, "input_tokens": i,
         "output_tokens": o, "project_id": p}
        for m, (r, i, o, p) in results.items()]}]}


def test_a_premium_model_with_tiny_answers_is_the_finding():
    # The whole note: 412,880 calls, mean answer 19 tokens, on the frontier model.
    state, detail = verdict("gpt-5", row(requests=412880, output=7844720,
                                         input_=170000000))
    assert state == "oversized"
    assert "mean output 19 token(s)" in detail
    assert sibling("gpt-5") == "gpt-5-mini"


def test_the_same_shape_on_the_mini_sibling_is_not_a_finding():
    state, _ = verdict("gpt-5-mini", row(requests=412880, output=7844720,
                                         input_=170000000))
    assert state == "right-sized"


def test_long_answers_are_the_model_doing_its_job():
    state, detail = verdict("gpt-5", row(requests=9000, output=18000000,
                                         input_=9000000))
    assert state == "deliberative"
    assert "mean output 2000 token(s)" in detail


def test_short_answers_over_huge_prompts_are_a_caching_problem():
    # Same ratio as the finding on the output side, 40k tokens of prompt on the
    # input side. Downgrading the model here saves almost nothing.
    state, detail = verdict("gpt-4.1", row(requests=5000, output=95000,
                                           input_=200000000))
    assert state == "input-bound"
    assert "caching the prefix" in detail


def test_a_model_too_quiet_to_have_a_shape_gets_no_verdict():
    assert verdict("gpt-5", row(requests=40, output=760))[0] == "low-volume"
    assert verdict("gpt-5", row(requests=0, output=0))[0] == "unreadable"


def test_tiers_are_conservative_about_what_they_claim_to_know():
    assert tier("ft:gpt-4o-mini-2024-07-18:acme::AbC123") == "custom"
    assert tier("text-embedding-3-large") == "small"
    assert tier("some-model-we-have-never-heard-of") == "unknown"
    assert sibling("some-model-we-have-never-heard-of") is None
    assert verdict("ft:gpt-4o-2024-08-06:acme::X", row())[0] == "custom-model"
    assert verdict("some-model-we-have-never-heard-of", row())[0] == "unknown-model"


def test_buckets_are_folded_before_the_division():
    pages = [bucket(**{"gpt-5": (100, 50000, 1000, "proj_a")}),
             bucket(**{"gpt-5": (900, 450000, 9000, "proj_b")})]
    folded = fold(pages)
    assert folded["gpt-5"]["requests"] == 1000
    assert folded["gpt-5"]["output"] == 10000
    assert folded["gpt-5"]["projects"] == ["proj_a", "proj_b"]
    # 10000/1000 = 10 tokens a call. Averaging the two buckets' quotients would
    # have given (10 + 10) / 2 by luck here and something wrong on real data.
    assert "mean output 10 token(s)" in verdict("gpt-5", folded["gpt-5"],
                                                min_requests=100)[1]


def test_permissions_say_whether_the_expensive_model_can_come_back():
    assert permissions_state({"mode": "deny_list", "model_ids": []},
                             "gpt-5") == "unconstrained"
    assert permissions_state({"mode": "deny_list", "model_ids": ["gpt-5"]},
                             "gpt-5") == "blocked"
    assert permissions_state({"mode": "allow_list", "model_ids": ["gpt-5-mini"]},
                             "gpt-5") == "blocked"
    assert permissions_state({"mode": "allow_list", "model_ids": ["gpt-5"]},
                             "gpt-5") == "allowed"
    assert permissions_state({}, "gpt-5") == "unreadable"
    assert permissions_state(None, "gpt-5") == "unreadable"
''',
"test_js_file": "openai-model-rightsizing-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fold, permissionsState, sibling, tier, verdict }
  from './openai-model-rightsizing-audit.mjs';

/** A folded row shaped like fold() returns them. */
function row({ requests = 10000, output = 190000, input = 900000,
               projects = ['proj_a'] } = {}) {
  return { requests, output, input, projects };
}

/** One daily bucket from GET /v1/organization/usage/completions. */
function bucket(results) {
  return {
    data: [{
      start_time: 0,
      results: Object.entries(results).map(([model, [r, i, o, p]]) => ({
        model, num_model_requests: r, input_tokens: i, output_tokens: o,
        project_id: p,
      })),
    }],
  };
}

test('a premium model with tiny answers is the finding', () => {
  const [state, detail] = verdict('gpt-5',
    row({ requests: 412880, output: 7844720, input: 170000000 }));
  assert.equal(state, 'oversized');
  assert.match(detail, /mean output 19 token/);
  assert.equal(sibling('gpt-5'), 'gpt-5-mini');
});

test('the same shape on the mini sibling is not a finding', () => {
  const [state] = verdict('gpt-5-mini',
    row({ requests: 412880, output: 7844720, input: 170000000 }));
  assert.equal(state, 'right-sized');
});

test('long answers are the model doing its job', () => {
  const [state, detail] = verdict('gpt-5',
    row({ requests: 9000, output: 18000000, input: 9000000 }));
  assert.equal(state, 'deliberative');
  assert.match(detail, /mean output 2000 token/);
});

test('short answers over huge prompts are a caching problem', () => {
  const [state, detail] = verdict('gpt-4.1',
    row({ requests: 5000, output: 95000, input: 200000000 }));
  assert.equal(state, 'input-bound');
  assert.match(detail, /caching the prefix/);
});

test('a model too quiet to have a shape gets no verdict', () => {
  assert.equal(verdict('gpt-5', row({ requests: 40, output: 760 }))[0], 'low-volume');
  assert.equal(verdict('gpt-5', row({ requests: 0, output: 0 }))[0], 'unreadable');
});

test('tiers are conservative about what they claim to know', () => {
  assert.equal(tier('ft:gpt-4o-mini-2024-07-18:acme::AbC123'), 'custom');
  assert.equal(tier('text-embedding-3-large'), 'small');
  assert.equal(tier('some-model-we-have-never-heard-of'), 'unknown');
  assert.equal(sibling('some-model-we-have-never-heard-of'), null);
  assert.equal(verdict('ft:gpt-4o-2024-08-06:acme::X', row())[0], 'custom-model');
  assert.equal(verdict('some-model-we-have-never-heard-of', row())[0], 'unknown-model');
});

test('buckets are folded before the division', () => {
  const pages = [bucket({ 'gpt-5': [100, 50000, 1000, 'proj_a'] }),
                 bucket({ 'gpt-5': [900, 450000, 9000, 'proj_b'] })];
  const folded = fold(pages);
  assert.equal(folded['gpt-5'].requests, 1000);
  assert.equal(folded['gpt-5'].output, 10000);
  assert.deepEqual(folded['gpt-5'].projects, ['proj_a', 'proj_b']);
  assert.match(verdict('gpt-5', folded['gpt-5'], 100)[1], /mean output 10 token/);
});

test('permissions say whether the expensive model can come back', () => {
  assert.equal(permissionsState({ mode: 'deny_list', model_ids: [] }, 'gpt-5'),
               'unconstrained');
  assert.equal(permissionsState({ mode: 'deny_list', model_ids: ['gpt-5'] }, 'gpt-5'),
               'blocked');
  assert.equal(permissionsState({ mode: 'allow_list', model_ids: ['gpt-5-mini'] }, 'gpt-5'),
               'blocked');
  assert.equal(permissionsState({ mode: 'allow_list', model_ids: ['gpt-5'] }, 'gpt-5'),
               'allowed');
  assert.equal(permissionsState({}, 'gpt-5'), 'unreadable');
  assert.equal(permissionsState(null, 'gpt-5'), 'unreadable');
});
''',
"faq": [
 ("What counts as a trivial answer?",
  "The default floor in the script is fifty output tokens on average, which is roughly a sentence. Classifiers, routers, tag extractors, yes/no guardrails and title generators all land far below it, usually under twenty. Anything above a couple of hundred tokens is prose the model had to compose, and the check should not be firing on it. Move the threshold to fit your workloads rather than arguing with the default."),
 ("Will a mini model actually give the same answer?",
  "For classification into a fixed set of labels, extraction against a schema, and routing, usually yes, and you can find out cheaply. Run the same thousand production inputs through both, diff the outputs, and look at the disagreements. That is a day's work against a spend difference of roughly an order of magnitude, and it is the only evidence anyone should accept for a model swap."),
 ("Why does the script report short answers over long prompts separately?",
  "Because it is a different bill. A retrieval or summarisation step sends twenty thousand tokens of context and gets three hundred back, so almost all the money is on the input side. Downgrading the model there saves a fraction of what caching the prefix saves, and reporting the two findings with the same sentence sends people to the wrong lever."),
 ("Can I do the same check on the Claude API?",
  "Not this way. GET /v1/organizations/usage_report/messages returns token sums per bucket with no request-count field, so there is no denominator and no mean answer length to compute. On that side you can compare token volume between models and workspaces, but the per-request shape has to come from your own client-side metrics. The right-sizing move is the same shape though: Claude Haiku 4.5 for the trivial workloads, an Opus or Sonnet 5 model where the reasoning is worth paying for."),
 ("Why print the model_permissions body instead of just changing the config?",
  "Because a config change lasts until the next person copies a snippet from the quickstart, and a project restricted to an allow_list does not. The permission is the durable half of the repair, which is also exactly why an audit script should not apply it: restricting which models your colleagues can call is a decision with an owner, and that owner is not a cron job holding an admin key."),
],
"related": [REL_TENANT, REL_OUTPUT_COST, REL_CACHE],
"citations": [CITE_USAGE_COMPLETIONS, CITE_ADMIN, CITE_PROJECTS, CITE_COSTS],
},

{
"slug": "per-tenant-cost-attribution-impossible",
"title": "Per-customer cost is unknowable because tenants share a key",
"description": "user_id on the Usage API names your own org members and service accounts, never your end users. Resolve every principal and the gap becomes provable.",
"h1": "per-customer cost is unknowable because tenants share a key",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai usage api group_by user_id", "openai per customer cost",
             "openai multi tenant cost attribution", "openai user field not in usage api",
             "openai api key per tenant"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_ADMIN_KEY, an organization admin key with read scopes.",
"lead": "Finance asks what the largest account costs to serve. It is a reasonable question and somebody says it will take an afternoon, because the Usage API has a <code>group_by=user_id</code> and the application has been sending a <code>user</code> field on every request since the first week. The afternoon produces a table with eleven rows in it. Nine are engineers, two are service accounts, and not one of them is a customer.",
"short_answer": """<p><code>GET /v1/organization/usage/completions?…&amp;group_by=user_id&amp;group_by=api_key_id&amp;group_by=project_id</code> with an organization <strong>admin</strong> key, then resolve every returned <code>user_id</code> against <code>GET /v1/organization/users?limit=100</code>.</p>
<p>Here is the thing worth stating precisely, because a lot of teams have to learn it twice: <strong><code>user_id</code> on the Usage API is the org member or service account that owns the calling API key.</strong> It is not an end-user identifier you supply. The attribution chain is request &rarr; API key &rarr; key owner &rarr; <code>user_id</code>, and your customer is nowhere in it.</p>
<p>The request-level <code>user</code> field never reaches the Usage API at all. It exists for abuse signals and cache bucketing, and it is now marked deprecated in the OpenAPI spec in favour of <code>safety_identifier</code> and <code>prompt_cache_key</code>. So no change on your side of the wire can make the Usage API segment by customer. The only dimensions the platform can attribute along are the ones it controls: <code>project_id</code>, <code>api_key_id</code>, and its own principals.</p>""",
"problem": """<p>The immediate cost of this is a table that cannot be built. The larger cost is every decision that quietly depends on it. You cannot price the product against its unit economics, because you do not know the unit. You cannot find the one enterprise account whose agent loop is eating the margin on the other four hundred, because its usage is added to everybody else's before you ever see it. You cannot enforce a per-tenant quota from the platform side, because the platform has no idea your tenants exist.</p>
<p>What makes it a trap rather than a limitation is that the API looks like it answers the question. There is a grouping dimension called <code>user_id</code>, and there is a request parameter called <code>user</code>, and the natural reading is that one is a report on the other. They have nothing to do with each other. A team can send a customer identifier on every request for two years, in good faith, and discover on the day they need it that none of it was ever stored anywhere they can read.</p>
<p>And it is not retroactively fixable. Splitting keys per tenant works from the moment you do it and never backwards, so every month spent not knowing is a month that stays unknown.</p>""",
"why": """<p><strong>The Usage API reports on principals, not on end users.</strong> <code>user_id</code> is an OpenAI org member id or a service account id. Its whole job is to tell you which of <em>your people</em> generated usage. On a multi-tenant product the answer is always the same handful of service accounts, which is correct and useless.</p>
<p><strong>The request-level <code>user</code> field is not a reporting dimension.</strong> It goes to abuse detection and cache bucketing. There is no endpoint that groups by it, no field on any usage result that returns it, and the spec now steers you to <code>safety_identifier</code> for the abuse half and <code>prompt_cache_key</code> for the cache half &mdash; two fields, neither of which is a billing dimension either.</p>
<p><strong>There is no request log to fall back on.</strong> Neither provider exposes an endpoint listing individual inference requests. If the aggregate cannot be sliced the way you need, there is no finer-grained source to go and slice yourself.</p>
<p><strong>Key cardinality is the whole ceiling.</strong> The platform can attribute to <code>api_key_id</code> and <code>project_id</code>. That means the finest slicing available to you is exactly as fine as the number of keys or projects you have minted. Four hundred tenants behind three keys is three buckets, permanently, no matter what the application sends.</p>
<p><strong>The fallback is real but it is yours to build.</strong> Every response carries a <code>usage</code> block. Recording it per call, tagged with your own tenant id, gives you attribution the platform will never give you &mdash; and it has to be reconciled against <code>/v1/organization/costs</code> periodically, because your token accounting and their invoice will drift.</p>""",
"steps": [
 {"h": "Ask for all three dimensions at once",
  "body": """<p><code>group_by=user_id</code>, <code>group_by=api_key_id</code> and <code>group_by=project_id</code> on the same seven-day call. The point is not any one of them; it is that these three are the complete list of things the platform can attribute along, and seeing them together is what makes the ceiling visible.</p>"""},
 {"h": "Resolve every user_id against the org directory",
  "body": """<p><code>GET /v1/organization/users?limit=100</code>. Every <code>user_id</code> the usage endpoint returned should map to a member or to a service account, and when it does, that is the finding rather than a reassurance. A <code>user_id</code> that resolves to nothing is a separate and more urgent thing: usage attributed to a principal your directory no longer knows.</p>"""},
 {"h": "Count the distinct keys and compare them to your tenant count",
  "body": """<p>The script takes the tenant count as an argument, because the API has no idea how many customers you have. If distinct <code>api_key_id</code> values are far fewer than tenants, attribution is impossible by construction and no amount of instrumentation changes it. One key is the worst case and gets its own state.</p>"""},
 {"h": "Confirm the concentration on the money side",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-30d}&amp;limit=30&amp;group_by=api_key_id</code>. A small number of keys carrying all of the spend, on a product that serves many customers, is the same finding stated in dollars, and it is the version finance will read.</p>"""},
 {"h": "Print the architecture, not a config flag",
  "body": """<p>The repair is to mint a key or a project per tenant &mdash; or per tenant tier, if per-tenant is thousands &mdash; through <code>POST /v1/organization/projects/{project_id}/service_accounts/{id}/api_keys</code>, and then attribute with <code>group_by=api_key_id</code>. The script prints that and stops, because creating credentials for your customers is not something an audit should do at three in the morning. It should also say plainly that this is forward-only.</p>"""},
],
"verify": """<p>Re-run after keys are split. The distinct key count should be at or above the tenant count, and the state should be <code>segmented</code>.</p>
<pre><code class="language-bash">python3 openai_tenant_attribution_audit.py --tenants 412
# keys-below-tenants  3 distinct api_key_id value(s) against 412 tenant(s)
#   note: all 11 user_id value(s) resolve to org members or service accounts
#   repair: mint one key per tenant tier; attribution is forward-only
# 1 finding(s)</code></pre>""",
"code_intro": "Two GETs and a third for the money, all read-only, all against <code>/v1/organization</code>, so this needs <code>OPENAI_ADMIN_KEY</code> rather than the key your application uses. The tenant count is an argument rather than a lookup because nothing in the API knows what a tenant is &mdash; that number lives in your database, and the check is honest about needing it. Four pure functions: folding the usage into the three dimensions, resolving one principal against the directory, listing the principals that resolve to nothing, and the verdict itself.",
"py_file": "openai_tenant_attribution_audit.py",
"py": '''"""Report whether OpenAI usage can be attributed to your customers at all.

Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
organization admin key (sk-admin-...) with read scopes.

The finding here is not a number, it is a fact about the reporting dimensions.
user_id on the Usage API is the org member or service account that owns the
calling API key. It is never an end-user identifier you supplied, and the
request-level `user` field does not reach this endpoint at all. So the repair is
architectural, it is forward-only, and it is printed rather than performed:
minting credentials for your tenants is not an audit's job.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_tenant_attribution_audit")

API = "https://api.openai.com/v1"

# The complete list of dimensions the platform can attribute along. Not a
# starting point: there is no fourth one, and that is the note.
DIMENSIONS = ("user_id", "api_key_id", "project_id")

FINDINGS = ("single-key", "keys-below-tenants")


def fold(pages):
    """Sum usage into the three dimensions the platform actually holds. Pure.

    Returns {"users": {id: requests}, "keys": {...}, "projects": {...},
    "requests": total}. Buckets with a null grouping value are counted into the
    total but not into a dimension, because a null there means "not attributed"
    and inventing a bucket for it would flatter the result.
    """
    out = {"users": {}, "keys": {}, "projects": {}, "requests": 0}
    for page in pages:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                try:
                    n = int(result.get("num_model_requests") or 0)
                except (TypeError, ValueError):
                    n = 0
                out["requests"] += n
                for field, key in (("user_id", "users"), ("api_key_id", "keys"),
                                   ("project_id", "projects")):
                    value = result.get(field)
                    if value:
                        name = str(value)
                        out[key][name] = out[key].get(name, 0) + n
    return out


def classify(user_id, directory):
    """What kind of principal is this user_id? Pure.

    "service-account", "member", or "unresolved". The first two are the same
    finding wearing different clothes: both are your own principals, neither is
    a customer. The third is a different problem entirely.
    """
    entry = directory.get(str(user_id))
    if entry is None:
        return "unresolved"
    if entry.get("service_account"):
        return "service-account"
    return "member"


def unresolved(folded, directory):
    """user_ids generating usage that the org directory does not know. Pure.

    Sorted, so two runs print the same order. Usually empty; when it is not,
    something is calling the API as a principal nobody can name, which wants
    answering before the attribution question does.
    """
    return sorted(u for u in folded.get("users", {})
                  if classify(u, directory) == "unresolved")


def verdict(folded, directory, tenant_count=None):
    """Can this organization's usage be sliced per customer? Pure.

    Returns (state, detail). tenant_count comes from your database because the
    API has no concept of a tenant; without it the script can still report the
    cardinality and the fact that every principal is one of your own, which is
    most of the answer.
    """
    keys = folded.get("keys") or {}
    users = folded.get("users") or {}
    total = folded.get("requests") or 0

    if total <= 0 and not keys:
        return ("no-usage",
                "no completions usage in the window, so there is nothing to "
                "attribute yet")

    kinds = sorted({classify(u, directory) for u in users})
    principal_note = ("%d user_id value(s), all of them org members or service "
                      "accounts rather than customers" % len(users))
    if "unresolved" in kinds:
        principal_note = ("%d user_id value(s), of which some resolve to nobody "
                          "in the org directory" % len(users))

    if len(keys) == 1:
        return ("single-key",
                "1 api_key_id covers every request in the window. There is one "
                "bucket, so per-customer cost has no place to come from. %s."
                % principal_note)

    if tenant_count is None:
        return ("unknown-tenant-count",
                "%d distinct api_key_id value(s) and %d project(s). %s. Pass "
                "the tenant count to judge whether that is enough buckets."
                % (len(keys), len(folded.get("projects") or {}), principal_note))

    if len(keys) < tenant_count:
        return ("keys-below-tenants",
                "%d distinct api_key_id value(s) against %d tenant(s). Cost per "
                "customer is unrecoverable by construction: the finest slice the "
                "platform can offer is one key, and there are fewer keys than "
                "customers. %s." % (len(keys), tenant_count, principal_note))

    return ("segmented",
            "%d distinct api_key_id value(s) for %d tenant(s), so the platform "
            "can slice finely enough. Confirm your key-to-tenant map is current."
            % (len(keys), tenant_count))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: OPENAI_ADMIN_KEY must be an "
                         "organization admin key, not a project key")
    if r.status_code == 403:
        raise SystemExit("403 from OpenAI: the key is not authorised for "
                         "/v1/organization")
    r.raise_for_status()
    return r.json()


def usage_pages(session, start_time, days, max_pages=20):
    params = {"start_time": start_time, "bucket_width": "1d", "limit": days,
              "group_by": list(DIMENSIONS)}
    for _ in range(max_pages):
        page = get(session, "/organization/usage/completions", params)
        yield page
        cursor = page.get("next_page")
        if not cursor:
            return
        params = dict(params, page=cursor)


def org_directory(session, max_pages=20):
    """The org's own principals, keyed by id, from GET /v1/organization/users."""
    out = {}
    params = {"limit": 100}
    for _ in range(max_pages):
        page = get(session, "/organization/users", params)
        data = page.get("data") or []
        for user in data:
            out[str(user.get("id"))] = {
                "name": user.get("name") or user.get("email") or "?",
                "service_account": bool(user.get("is_service_account")),
            }
        if not page.get("has_more") or not data:
            break
        params = {"limit": 100, "after": data[-1].get("id")}
    return out


def spend_by_key(session, start_time):
    out = {}
    page = get(session, "/organization/costs",
               {"start_time": start_time, "limit": 30, "group_by": "api_key_id"})
    for bucket in page.get("data") or []:
        for result in bucket.get("results") or []:
            key_id = str(result.get("api_key_id") or "unattributed")
            amount = (result.get("amount") or {}).get("value") or 0
            try:
                out[key_id] = out.get(key_id, 0.0) + float(amount)
            except (TypeError, ValueError):
                pass
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tenants", type=int, default=None,
                    help="how many customers you serve; comes from your database")
    ap.add_argument("--days", type=int, default=7,
                    help="days of usage to fold (default 7)")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read scopes)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    now = dt.datetime.now(dt.timezone.utc)
    start = int((now - dt.timedelta(days=args.days)).timestamp())

    folded = fold(usage_pages(session, start, args.days))
    directory = org_directory(session)
    state, detail = verdict(folded, directory, args.tenants)

    log.info("%-20s %s", state, detail)

    for user_id in sorted(folded["users"], key=lambda u: -folded["users"][u]):
        kind = classify(user_id, directory)
        name = directory.get(user_id, {}).get("name", "not in the directory")
        log.info("  principal %-30s %-16s %s", user_id, kind, name)

    orphans = unresolved(folded, directory)
    if orphans:
        log.warning("  %d user_id value(s) resolve to nobody in the org "
                    "directory: %s", len(orphans), ", ".join(orphans))
        log.warning("  repair: find what is calling as these principals before "
                    "you touch the attribution question")

    if state in FINDINGS:
        spend = spend_by_key(session, int((now - dt.timedelta(days=30)).timestamp()))
        for key_id, amount in sorted(spend.items(), key=lambda kv: -kv[1])[:10]:
            log.warning("  30d spend  %-30s $%.2f", key_id, amount)
        log.warning("  repair: the Usage API cannot segment by end user. Mint "
                    "one key, or one project, per tenant or tenant tier via "
                    "/v1/organization/projects/{id}/service_accounts/{id}/api_keys "
                    "and attribute with group_by=api_key_id.")
        log.warning("  repair: this is forward-only and cannot backfill. Until "
                    "then, record each response's usage block against your own "
                    "tenant id and reconcile it against /v1/organization/costs.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-tenant-attribution-audit.mjs",
"js": '''/**
 * Report whether OpenAI usage can be attributed to your customers at all.
 *
 * Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
 * organization admin key with read scopes.
 *
 * The finding is a fact about the reporting dimensions, not a number. user_id
 * on the Usage API is the org member or service account that owns the calling
 * key, never an end-user identifier you supplied. The repair is architectural,
 * forward-only, and printed rather than performed.
 */
const API = 'https://api.openai.com/v1';

// The complete list of dimensions the platform can attribute along.
const DIMENSIONS = ['user_id', 'api_key_id', 'project_id'];

const FINDINGS = ['single-key', 'keys-below-tenants'];

/**
 * Sum usage into the three dimensions the platform actually holds. Pure.
 * A null grouping value counts into the total but into no dimension, because
 * null means "not attributed" and inventing a bucket would flatter the result.
 */
export function fold(pages) {
  const out = { users: {}, keys: {}, projects: {}, requests: 0 };
  for (const page of pages) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const raw = Number(result.num_model_requests ?? 0);
        const n = Number.isFinite(raw) ? Math.trunc(raw) : 0;
        out.requests += n;
        for (const [field, key] of [['user_id', 'users'], ['api_key_id', 'keys'],
                                    ['project_id', 'projects']]) {
          const value = result[field];
          if (value) {
            const name = String(value);
            out[key][name] = (out[key][name] ?? 0) + n;
          }
        }
      }
    }
  }
  return out;
}

/**
 * What kind of principal is this user_id? Pure. "service-account", "member" or
 * "unresolved". The first two are the same finding in different clothes.
 */
export function classify(userId, directory) {
  const entry = directory[String(userId)];
  if (entry === undefined || entry === null) return 'unresolved';
  return entry.service_account ? 'service-account' : 'member';
}

/** user_ids generating usage that the org directory does not know. Pure. */
export function unresolved(folded, directory) {
  return Object.keys(folded.users ?? {})
    .filter((u) => classify(u, directory) === 'unresolved')
    .sort();
}

/**
 * Can this organization's usage be sliced per customer? Pure.
 * Returns [state, detail]. tenantCount comes from your database, because the
 * API has no concept of a tenant.
 */
export function verdict(folded, directory, tenantCount = null) {
  const keys = folded.keys ?? {};
  const users = folded.users ?? {};
  const total = folded.requests ?? 0;
  const keyCount = Object.keys(keys).length;
  const userCount = Object.keys(users).length;

  if (total <= 0 && keyCount === 0) {
    return ['no-usage',
      'no completions usage in the window, so there is nothing to attribute yet'];
  }

  const kinds = new Set(Object.keys(users).map((u) => classify(u, directory)));
  const principalNote = kinds.has('unresolved')
    ? `${userCount} user_id value(s), of which some resolve to nobody in the org directory`
    : `${userCount} user_id value(s), all of them org members or service accounts rather than customers`;

  if (keyCount === 1) {
    return ['single-key',
      '1 api_key_id covers every request in the window. There is one bucket, ' +
      `so per-customer cost has no place to come from. ${principalNote}.`];
  }

  if (tenantCount === null || tenantCount === undefined) {
    return ['unknown-tenant-count',
      `${keyCount} distinct api_key_id value(s) and ` +
      `${Object.keys(folded.projects ?? {}).length} project(s). ${principalNote}. ` +
      'Pass the tenant count to judge whether that is enough buckets.'];
  }

  if (keyCount < tenantCount) {
    return ['keys-below-tenants',
      `${keyCount} distinct api_key_id value(s) against ${tenantCount} ` +
      'tenant(s). Cost per customer is unrecoverable by construction: the ' +
      'finest slice the platform can offer is one key, and there are fewer ' +
      `keys than customers. ${principalNote}.`];
  }

  return ['segmented',
    `${keyCount} distinct api_key_id value(s) for ${tenantCount} tenant(s), so ` +
    'the platform can slice finely enough. Confirm your key-to-tenant map is current.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: OPENAI_ADMIN_KEY must be an organization ' +
                    'admin key, not a project key');
  }
  if (res.status === 403) {
    throw new Error('403 from OpenAI: the key is not authorised for /v1/organization');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function usagePages(key, startTime, days, maxPages = 20) {
  const pages = [];
  let params = {
    start_time: startTime, bucket_width: '1d', limit: days, group_by: DIMENSIONS,
  };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/usage/completions', params);
    pages.push(page);
    if (!page.next_page) break;
    params = { ...params, page: page.next_page };
  }
  return pages;
}

async function orgDirectory(key, maxPages = 20) {
  const out = {};
  let params = { limit: 100 };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/users', params);
    const data = page.data ?? [];
    for (const user of data) {
      out[String(user.id)] = {
        name: user.name ?? user.email ?? '?',
        service_account: Boolean(user.is_service_account),
      };
    }
    if (!page.has_more || data.length === 0) break;
    params = { limit: 100, after: data[data.length - 1].id };
  }
  return out;
}

async function spendByKey(key, startTime) {
  const out = {};
  const page = await get(key, '/organization/costs',
    { start_time: startTime, limit: 30, group_by: 'api_key_id' });
  for (const bucket of page.data ?? []) {
    for (const result of bucket.results ?? []) {
      const keyId = String(result.api_key_id ?? 'unattributed');
      const amount = Number(result.amount?.value ?? 0);
      if (Number.isFinite(amount)) out[keyId] = (out[keyId] ?? 0) + amount;
    }
  }
  return out;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read scopes)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 7);
  const tenantsRaw = process.env.TENANTS;
  const tenants = tenantsRaw === undefined ? null : Number(tenantsRaw);

  const now = Math.floor(Date.now() / 1000);
  const folded = fold(await usagePages(key, now - days * 86400, days));
  const directory = await orgDirectory(key);
  const [state, detail] = verdict(folded, directory, tenants);

  console.log(`${state.padEnd(20)} ${detail}`);

  const byVolume = Object.keys(folded.users)
    .sort((a, b) => folded.users[b] - folded.users[a]);
  for (const userId of byVolume) {
    const kind = classify(userId, directory);
    const name = directory[userId]?.name ?? 'not in the directory';
    console.log(`  principal ${userId.padEnd(30)} ${kind.padEnd(16)} ${name}`);
  }

  const orphans = unresolved(folded, directory);
  if (orphans.length > 0) {
    console.warn(`  ${orphans.length} user_id value(s) resolve to nobody in the ` +
                 `org directory: ${orphans.join(', ')}`);
    console.warn('  repair: find what is calling as these principals before you ' +
                 'touch the attribution question');
  }

  if (FINDINGS.includes(state)) {
    const spend = await spendByKey(key, now - 30 * 86400);
    const top = Object.entries(spend).sort((a, b) => b[1] - a[1]).slice(0, 10);
    for (const [keyId, amount] of top) {
      console.warn(`  30d spend  ${keyId.padEnd(30)} $${amount.toFixed(2)}`);
    }
    console.warn('  repair: the Usage API cannot segment by end user. Mint one ' +
      'key, or one project, per tenant or tenant tier via ' +
      '/v1/organization/projects/{id}/service_accounts/{id}/api_keys and ' +
      'attribute with group_by=api_key_id.');
    console.warn('  repair: this is forward-only and cannot backfill. Until ' +
      'then, record each response usage block against your own tenant id and ' +
      'reconcile it against /v1/organization/costs.');
    process.exitCode = 1;
    return;
  }
  process.exitCode = 0;
}

// Only run when invoked directly, so importing this from the test file does not
// run main(), fail on the missing key, and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests encode the misconception, because the misconception is the note. A directory in which every returned <code>user_id</code> is a service account or an engineer produces a finding and not a clean bill of health, and three keys against four hundred tenants is unrecoverable no matter how tidy the principals look. The rest keep the states apart: one key is its own worst case, a missing tenant count means the script reports cardinality instead of pretending to a verdict, and a principal the directory has never heard of is a different problem that should not be folded into this one.",
"test_py_file": "test_openai_tenant_attribution_audit.py",
"test_py": '''from openai_tenant_attribution_audit import (classify, fold, unresolved,
                                             verdict)

DIRECTORY = {
    "user_eng1": {"name": "an engineer", "service_account": False},
    "user_eng2": {"name": "another engineer", "service_account": False},
    "sa_prod": {"name": "prod-backend", "service_account": True},
}


def folded(users=None, keys=None, projects=None, requests=100000):
    return {"users": users if users is not None else {"sa_prod": 100000},
            "keys": keys if keys is not None else {"key_abc": 100000},
            "projects": projects if projects is not None else {"proj_1": 100000},
            "requests": requests}


def bucket(rows):
    """One daily bucket from the usage endpoint, grouped three ways."""
    return {"data": [{"start_time": 0, "results": [
        {"user_id": u, "api_key_id": k, "project_id": p,
         "num_model_requests": n} for (u, k, p, n) in rows]}]}


def test_every_principal_is_one_of_your_own_and_that_is_the_finding():
    # Eleven rows, none of them a customer. The API answered; the answer is
    # about the org's own service accounts.
    state, detail = verdict(
        folded(users={"sa_prod": 90000, "user_eng1": 10000},
               keys={"key_a": 60000, "key_b": 40000}),
        DIRECTORY, tenant_count=412)
    assert state == "keys-below-tenants"
    assert "2 distinct api_key_id value(s) against 412 tenant(s)" in detail
    assert "org members or service accounts rather than customers" in detail


def test_one_key_is_its_own_worst_case():
    state, detail = verdict(folded(), DIRECTORY, tenant_count=412)
    assert state == "single-key"
    assert "one bucket" in detail


def test_enough_keys_means_the_platform_can_slice():
    state, _ = verdict(
        folded(keys={"key_%d" % i: 10 for i in range(500)}),
        DIRECTORY, tenant_count=412)
    assert state == "segmented"


def test_without_a_tenant_count_the_script_does_not_invent_a_verdict():
    state, detail = verdict(folded(keys={"key_a": 5, "key_b": 5}), DIRECTORY)
    assert state == "unknown-tenant-count"
    assert "Pass the tenant count" in detail
    assert verdict({"users": {}, "keys": {}, "projects": {}, "requests": 0},
                   DIRECTORY)[0] == "no-usage"


def test_a_principal_the_directory_does_not_know_is_a_different_problem():
    f = folded(users={"user_departed": 5000, "sa_prod": 5000},
               keys={"key_a": 5000, "key_b": 5000})
    assert classify("user_departed", DIRECTORY) == "unresolved"
    assert classify("sa_prod", DIRECTORY) == "service-account"
    assert classify("user_eng1", DIRECTORY) == "member"
    assert unresolved(f, DIRECTORY) == ["user_departed"]
    assert "resolve to nobody" in verdict(f, DIRECTORY, tenant_count=412)[1]


def test_fold_counts_the_three_dimensions_and_skips_the_nulls():
    pages = [bucket([("sa_prod", "key_a", "proj_1", 700),
                     (None, "key_b", "proj_1", 300)])]
    f = fold(pages)
    assert f["requests"] == 1000
    assert f["users"] == {"sa_prod": 700}
    assert f["keys"] == {"key_a": 700, "key_b": 300}
    assert f["projects"] == {"proj_1": 1000}
''',
"test_js_file": "openai-tenant-attribution-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, fold, unresolved, verdict }
  from './openai-tenant-attribution-audit.mjs';

const DIRECTORY = {
  user_eng1: { name: 'an engineer', service_account: false },
  user_eng2: { name: 'another engineer', service_account: false },
  sa_prod: { name: 'prod-backend', service_account: true },
};

function folded({ users, keys, projects, requests = 100000 } = {}) {
  return {
    users: users ?? { sa_prod: 100000 },
    keys: keys ?? { key_abc: 100000 },
    projects: projects ?? { proj_1: 100000 },
    requests,
  };
}

/** One daily bucket from the usage endpoint, grouped three ways. */
function bucket(rows) {
  return {
    data: [{
      start_time: 0,
      results: rows.map(([u, k, p, n]) => ({
        user_id: u, api_key_id: k, project_id: p, num_model_requests: n,
      })),
    }],
  };
}

test('every principal is one of your own and that is the finding', () => {
  const [state, detail] = verdict(
    folded({ users: { sa_prod: 90000, user_eng1: 10000 },
             keys: { key_a: 60000, key_b: 40000 } }),
    DIRECTORY, 412);
  assert.equal(state, 'keys-below-tenants');
  assert.match(detail, /2 distinct api_key_id value/);
  assert.match(detail, /org members or service accounts rather than customers/);
});

test('one key is its own worst case', () => {
  const [state, detail] = verdict(folded(), DIRECTORY, 412);
  assert.equal(state, 'single-key');
  assert.match(detail, /one bucket/);
});

test('enough keys means the platform can slice', () => {
  const keys = {};
  for (let i = 0; i < 500; i += 1) keys[`key_${i}`] = 10;
  assert.equal(verdict(folded({ keys }), DIRECTORY, 412)[0], 'segmented');
});

test('without a tenant count the script does not invent a verdict', () => {
  const [state, detail] = verdict(folded({ keys: { key_a: 5, key_b: 5 } }), DIRECTORY);
  assert.equal(state, 'unknown-tenant-count');
  assert.match(detail, /Pass the tenant count/);
  assert.equal(
    verdict({ users: {}, keys: {}, projects: {}, requests: 0 }, DIRECTORY)[0],
    'no-usage');
});

test('a principal the directory does not know is a different problem', () => {
  const f = folded({ users: { user_departed: 5000, sa_prod: 5000 },
                     keys: { key_a: 5000, key_b: 5000 } });
  assert.equal(classify('user_departed', DIRECTORY), 'unresolved');
  assert.equal(classify('sa_prod', DIRECTORY), 'service-account');
  assert.equal(classify('user_eng1', DIRECTORY), 'member');
  assert.deepEqual(unresolved(f, DIRECTORY), ['user_departed']);
  assert.match(verdict(f, DIRECTORY, 412)[1], /resolve to nobody/);
});

test('fold counts the three dimensions and skips the nulls', () => {
  const f = fold([bucket([['sa_prod', 'key_a', 'proj_1', 700],
                          [null, 'key_b', 'proj_1', 300]])]);
  assert.equal(f.requests, 1000);
  assert.deepEqual(f.users, { sa_prod: 700 });
  assert.deepEqual(f.keys, { key_a: 700, key_b: 300 });
  assert.deepEqual(f.projects, { proj_1: 1000 });
});
''',
"faq": [
 ("So what is user_id on the Usage API, exactly?",
  "The OpenAI org member or service account that owns the API key the request was made with. The chain is request, then key, then key owner, then user_id. It answers which of your own people generated the usage, which is a genuinely useful question for an internal platform team and completely the wrong question for a multi-tenant product."),
 ("I send a user field on every request. Where does it go?",
  "To abuse detection and cache bucketing, and nowhere else you can read. It is not a reporting dimension, there is no endpoint that groups by it, and the OpenAPI spec now marks it deprecated in favour of safety_identifier for the abuse signal and prompt_cache_key for the cache one. Neither of those is a billing dimension either."),
 ("How many keys is too many keys?",
  "Per-tenant keys are fine into the hundreds and awkward in the tens of thousands, because every key is a credential somebody has to rotate, revoke and store. The usual compromise is a key per tenant tier or per large account, with everything below a size threshold sharing a key and being attributed from your own token accounting instead. Pick the split you can actually operate."),
 ("Can I recover last quarter's per-customer cost somehow?",
  "No. There is no request log on either provider, the aggregate is already aggregated, and splitting keys works only from the moment you do it. If you have been logging each response's usage block with your own tenant id, you can reconstruct it approximately from that and reconcile the total against the cost report. If you have not, that period is simply unknown, which is worth saying out loud to whoever asked."),
 ("Does the Claude Admin API do this any better?",
  "It has the same ceiling with different names. The usage and cost reports group by workspace_id, api_key_id and model, all of which are your own resources, and there is no end-user dimension. The equivalent architecture is a workspace or a key per tenant. It is also worse in one specific way: the messages usage report carries no request count at all, so even the per-request arithmetic you can do on OpenAI is unavailable there."),
],
"related": [REL_FRONTIER, REL_ARCHIVED, REL_SPEND_LIMIT],
"citations": [CITE_USAGE_COMPLETIONS, CITE_OPENAPI, CITE_PROJECT_KEYS, CITE_ADMIN],
},

{
"slug": "audio-and-image-line-items-unnoticed",
"title": "Audio and image usage never shows up in a token dashboard",
"description": "Speech bills by characters, transcription by seconds, images by count. A dashboard built on usage/completions is structurally unable to see any of it.",
"h1": "audio and image usage never shows up in a token dashboard",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai usage api audio_speeches", "openai usage images endpoint",
             "openai costs group_by line_item", "openai usage dashboard wrong total",
             "openai web search code interpreter billing"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_ADMIN_KEY, an organization admin key with read scopes.",
"lead": "The internal dashboard has been within a few percent of the invoice for a year, and a few percent is what everyone expects a dashboard to be. It is not rounding. It is the text-to-speech in the mobile app, the transcription on the support calls, the thumbnails the marketing tool generates, and the web search the agent does before it answers. None of those are denominated in tokens, and the endpoint the dashboard was built on only knows about tokens.",
"short_answer": """<p>Stop treating <code>/v1/organization/usage/completions</code> as the organization's spend and start treating <code>GET /v1/organization/costs?start_time=…&amp;group_by=line_item</code> as it. Costs are in dollars and cover everything; usage is in whatever unit that surface happens to bill in.</p>
<p>The Usage API is split by modality on purpose, because the units differ. Speech bills by <code>characters</code>, transcription by <code>seconds</code>, images by <code>images</code>, code interpreter by <code>num_sessions</code>, and file search and web search by <code>num_requests</code>. Eight endpoints, five units, and a token dashboard can see none of them.</p>
<p>There is a second, quieter half of this. Multimodal chat sends audio and images <em>through</em> the completions endpoint, where they arrive as <code>input_audio_tokens</code>, <code>output_audio_tokens</code> and <code>input_image_tokens</code> alongside <code>input_text_tokens</code>. A dashboard adding <code>input_tokens + output_tokens</code> is silently mixing token types that are priced differently.</p>""",
"problem": """<p>A discrepancy that is small and stable is the hardest kind to investigate, because it never gets worse quickly enough to be anybody's problem this week. It gets rationalised. Rounding, timing, the cost report lagging real time, currency conversion &mdash; there are four plausible explanations for a three percent gap and all of them are wrong.</p>
<p>Then the product ships a voice feature, or an agent that searches the web before answering, and the gap stops being three percent. Nobody notices the moment it changes, because the dashboard the team looks at every morning cannot render the thing that changed. The first signal is the invoice, and by then the question is not "why is this line here" but "how long has this line been here", which is a much worse conversation.</p>
<p>Web search in particular is priced per thousand calls rather than per token, so an agent that searches twice per turn generates a line item that scales with conversations and appears nowhere in a token graph at all.</p>""",
"why": """<p><strong>The units are genuinely different, so the endpoints have to be.</strong> There is no honest way to express seconds of audio as tokens, and OpenAI does not pretend otherwise: each modality gets its own path under <code>/v1/organization/usage/</code>, its own result object type, and its own quantity field. A script written against one of them is structurally incapable of seeing the others. That is not a bug to work around, it is the shape of the API.</p>
<p><strong>Costs is the only endpoint denominated in money.</strong> <code>GET /v1/organization/costs</code> returns <code>amount.value</code> in a currency, grouped by <code>line_item</code>, and it is the one place where audio, images, tools and tokens are commensurable. Anything that claims to be a spend dashboard and is not driven by this endpoint is a usage dashboard wearing a dollar sign.</p>
<p><strong>Usage explains, costs totals.</strong> The right division of labour is the opposite of the common one: read the money from costs, and reach for the per-modality usage endpoints only to answer why a line item moved. Built the other way round, the dashboard is both incomplete and slower to explain itself.</p>
<p><strong>Multimodal tokens inside completions are a separate hazard.</strong> The completions result carries <code>input_text_tokens</code>, <code>input_audio_tokens</code>, <code>input_image_tokens</code>, <code>output_audio_tokens</code> and friends alongside the totals. Summing the totals treats a text token and an audio token as the same money, and they are not.</p>
<p><strong>An unrecognised line item is a finding, not an error.</strong> The set of billable surfaces changes when the platform ships things. A reconciliation that only knows the line items it was written against will silently drop the next one, so a line item the script cannot classify is reported loudly rather than bucketed into "other" and forgotten.</p>""",
"steps": [
 {"h": "Pull the money first",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-30d}&amp;limit=31&amp;group_by=line_item</code>. Sum <code>results[].amount.value</code> per <code>line_item</code>. This is the denominator for everything that follows, and it is the number the invoice will agree with.</p>"""},
 {"h": "Declare what your dashboard actually covers",
  "body": """<p>Not what it aspires to cover. If it reads completions and nothing else, it covers text tokens. Pass that as an argument, and let the script subtract: the gap is the part of the bill your team has never seen rendered.</p>"""},
 {"h": "Sweep the modality endpoints for the volume behind each line",
  "body": """<p><code>audio_speeches</code> (<code>characters</code>), <code>audio_transcriptions</code> (<code>seconds</code>), <code>images</code> (<code>images</code>, groupable by <code>size</code> and <code>source</code>), <code>code_interpreter_sessions</code> (<code>num_sessions</code>), <code>file_search_calls</code> and <code>web_search_calls</code> (<code>num_requests</code>), plus <code>embeddings</code> and <code>moderations</code>. Same window, same <code>bucket_width=1d</code>. These do not tell you the money; they tell you what the money was for.</p>"""},
 {"h": "Check the token types inside completions too",
  "body": """<p>Read <code>input_text_tokens</code>, <code>input_audio_tokens</code> and <code>input_image_tokens</code> separately rather than taking <code>input_tokens</code> whole. Non-zero audio or image token counts mean multimodal traffic is flowing through chat and your naive sum is mispricing it.</p>"""},
 {"h": "Report the gap in dollars and name the lines",
  "body": """<p>A percentage is arguable and a list of line items with amounts is not. Print each uncovered <code>line_item</code> with its <code>amount.value</code>, and its <code>quantity</code> and <code>quantity_unit</code> where the report carries them, so the reader can see both the money and what was bought with it.</p>"""},
],
"verify": """<p>Re-run after the dashboard is rebuilt on costs. The uncovered share should fall inside the tolerance and stay there when a new surface ships.</p>
<pre><code class="language-bash">python3 openai_modality_spend_reconcile.py --covers text
# gap          $18,402.11 total, $2,914.68 (15.8%) outside what the dashboard covers
#   uncovered  audio      $1,802.40   Text-to-speech        14,209,881 characters
#   uncovered  tool       $  784.00   Web search            78,400 requests
#   uncovered  image      $  328.28   Image generation      6,120 images
# 1 finding(s)</code></pre>""",
"code_intro": "One costs call for the money and eight usage calls for the volume behind it, all GET, all needing <code>OPENAI_ADMIN_KEY</code>. The judgement is in three pure functions: mapping a <code>line_item</code> string onto a modality family, subtracting what your dashboard covers from the total, and deciding whether the remainder is rounding or a hole. A fourth reads the token types hiding inside a completions result, which is the same problem one level down.",
"py_file": "openai_modality_spend_reconcile.py",
"py": '''"""Reconcile an OpenAI token dashboard against the whole bill.

Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
organization admin key (sk-admin-...) with read scopes.

Costs is the only endpoint denominated in money. The per-modality usage
endpoints are denominated in characters, seconds, images, sessions and calls,
and a dashboard built on completions can see none of them. This script prints
the difference and stops.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_modality_spend_reconcile")

API = "https://api.openai.com/v1"

# Every usage surface, with the field it is denominated in. Five different units
# across eight endpoints is the reason a token dashboard cannot be made complete
# by adding one more query to it.
SURFACES = (
    ("completions", "/organization/usage/completions", "num_model_requests", "requests"),
    ("embeddings", "/organization/usage/embeddings", "input_tokens", "tokens"),
    ("moderations", "/organization/usage/moderations", "input_tokens", "tokens"),
    ("audio_speeches", "/organization/usage/audio_speeches", "characters", "characters"),
    ("audio_transcriptions", "/organization/usage/audio_transcriptions", "seconds", "seconds"),
    ("images", "/organization/usage/images", "images", "images"),
    ("code_interpreter_sessions", "/organization/usage/code_interpreter_sessions",
     "num_sessions", "sessions"),
    ("file_search_calls", "/organization/usage/file_search_calls", "num_requests", "calls"),
    ("web_search_calls", "/organization/usage/web_search_calls", "num_requests", "calls"),
)

# Matched in order against a lowercased line_item. Audio, image and tool come
# before text because "gpt-image-1" and "gpt-4o-audio-preview" both contain a
# text-model substring and neither is billed in text tokens.
FAMILIES = (
    ("audio", ("audio", "speech", "transcription", "whisper", "tts", "realtime")),
    ("image", ("image", "dall-e")),
    ("tool", ("web search", "web_search", "file search", "file_search",
              "code interpreter", "code_interpreter", "container")),
    ("embedding", ("embedding",)),
    ("moderation", ("moderation",)),
    ("text", ("input tokens", "output tokens", "cached input", "cached_input",
              "gpt-", "o1-", "o3", "o4-", "chat")),
)

# The token types that hide inside a completions result. Adding input_tokens and
# output_tokens whole treats every one of these as the same money.
MIXED_TOKEN_FIELDS = ("input_audio_tokens", "output_audio_tokens",
                      "input_image_tokens", "output_image_tokens")

FINDINGS = ("gap", "unclassified-line-items")


def family(line_item):
    """Map a cost report line_item onto a modality family. Pure.

    Returns "other" for anything unrecognised, and "other" is deliberately loud
    rather than a quiet bucket: the platform ships new billable surfaces, and a
    reconciliation that silently absorbs the next one is worse than none.
    """
    name = str(line_item or "").strip().lower()
    if not name:
        return "other"
    for label, markers in FAMILIES:
        if any(marker in name for marker in markers):
            return label
    return "other"


def reconcile(items, covers):
    """Split spend into what the dashboard covers and what it does not. Pure.

    items is [(line_item, amount, quantity, quantity_unit), ...] as read off
    GET /v1/organization/costs grouped by line_item. covers is the set of family
    names your dashboard actually renders. Amounts that will not parse are
    counted as unreadable rather than as zero, because zero would shrink the gap.
    """
    out = {"total": 0.0, "covered": 0.0, "uncovered": 0.0, "unreadable": 0,
           "by_family": {}, "rows": []}
    wanted = {str(c).strip().lower() for c in covers}
    for line_item, amount, quantity, unit in items:
        try:
            value = float(amount)
        except (TypeError, ValueError):
            out["unreadable"] += 1
            continue
        label = family(line_item)
        out["total"] += value
        out["by_family"][label] = out["by_family"].get(label, 0.0) + value
        if label in wanted:
            out["covered"] += value
        else:
            out["uncovered"] += value
            out["rows"].append((label, str(line_item), value, quantity, unit))
    out["rows"].sort(key=lambda r: -r[2])
    return out


def verdict(recon, tolerance=0.02):
    """Is the remainder rounding or a hole? Pure. Returns (state, detail).

    tolerance is a fraction of total spend, defaulting to 2%, which is about
    where a gap stops being explicable as timing and lag. A gap made mostly of
    line items the script could not classify gets its own state, because the
    repair is to go and read the strings rather than to add a known endpoint.
    """
    total = recon.get("total") or 0.0
    uncovered = recon.get("uncovered") or 0.0
    if total <= 0:
        return ("no-spend",
                "no spend in the window, so there is nothing to reconcile")

    share = uncovered / total
    money = ("$%.2f total, $%.2f (%.1f%%) outside what the dashboard covers"
             % (total, uncovered, share * 100))

    if share < tolerance:
        return ("reconciled",
                "%s, inside the %.1f%% tolerance" % (money, tolerance * 100))

    other = (recon.get("by_family") or {}).get("other", 0.0)
    if uncovered > 0 and other / uncovered > 0.5:
        return ("unclassified-line-items",
                "%s, and most of it is on line items this script could not "
                "classify. Read the raw line_item strings before assuming which "
                "endpoint explains them." % money)

    biggest = max((recon.get("by_family") or {}).items(),
                  key=lambda kv: kv[1] if kv[0] not in ("text",) else -1,
                  default=("nothing", 0.0))
    return ("gap",
            "%s. Largest uncovered family is %s at $%.2f."
            % (money, biggest[0], biggest[1]))


def hidden_token_types(result):
    """Non-zero audio and image token counts inside a completions result. Pure.

    Returns a sorted list of (field, value). A dashboard summing input_tokens and
    output_tokens whole is mixing these in with text tokens at the text price.
    """
    out = []
    for field in MIXED_TOKEN_FIELDS:
        try:
            value = int(result.get(field) or 0)
        except (TypeError, ValueError):
            continue
        if value:
            out.append((field, value))
    return sorted(out)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: OPENAI_ADMIN_KEY must be an "
                         "organization admin key, not a project key")
    if r.status_code == 403:
        raise SystemExit("403 from OpenAI: the key is not authorised for "
                         "/v1/organization")
    r.raise_for_status()
    return r.json()


def cost_items(session, start_time):
    """[(line_item, amount, quantity, quantity_unit), ...] over the window."""
    out = []
    page = get(session, "/organization/costs",
               {"start_time": start_time, "limit": 31, "group_by": "line_item"})
    for bucket in page.get("data") or []:
        for result in bucket.get("results") or []:
            out.append((result.get("line_item"),
                        (result.get("amount") or {}).get("value"),
                        result.get("quantity"),
                        result.get("quantity_unit")))
    return out


def surface_volume(session, path, field, start_time, days):
    """Sum one usage surface's own quantity field over the window."""
    total = 0
    page = get(session, path,
               {"start_time": start_time, "bucket_width": "1d", "limit": days})
    for bucket in page.get("data") or []:
        for result in bucket.get("results") or []:
            try:
                total += int(result.get(field) or 0)
            except (TypeError, ValueError):
                pass
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days to reconcile (default 30)")
    ap.add_argument("--covers", default="text",
                    help="comma separated families your dashboard renders "
                         "(default 'text', which is what a completions-only "
                         "dashboard covers)")
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="uncovered share below which the gap is rounding")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key with read scopes)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    now = dt.datetime.now(dt.timezone.utc)
    start = int((now - dt.timedelta(days=args.days)).timestamp())
    covers = [c for c in args.covers.split(",") if c.strip()]

    recon = reconcile(cost_items(session, start), covers)
    state, detail = verdict(recon, args.tolerance)
    log.info("%-24s %s", state, detail)

    for label, line_item, value, quantity, unit in recon["rows"][:20]:
        log.warning("  uncovered  %-10s $%9.2f   %-28s %s %s",
                    label, value, line_item, quantity or "", unit or "")

    for name, path, field, unit in SURFACES:
        volume = surface_volume(session, path, field, start, args.days)
        if volume:
            log.info("  volume     %-28s %s %s", name, volume, unit)

    if recon["unreadable"]:
        log.warning("  %d cost row(s) had an unreadable amount and were left out "
                    "of both sides", recon["unreadable"])

    if state in FINDINGS:
        log.warning("  repair: drive the spend dashboard from "
                    "/v1/organization/costs grouped by line_item, which is the "
                    "only endpoint denominated in money, and use the "
                    "per-modality usage endpoints to explain why a line moved")
        log.warning("  repair: inside completions, read input_text_tokens, "
                    "input_audio_tokens and input_image_tokens separately "
                    "instead of summing input_tokens whole")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-modality-spend-reconcile.mjs",
"js": '''/**
 * Reconcile an OpenAI token dashboard against the whole bill.
 *
 * Read only. GET requests and nothing else: OPENAI_ADMIN_KEY must be an
 * organization admin key with read scopes.
 *
 * Costs is the only endpoint denominated in money. The per-modality usage
 * endpoints are denominated in characters, seconds, images, sessions and calls.
 */
const API = 'https://api.openai.com/v1';

// Every usage surface, with the field it is denominated in.
const SURFACES = [
  ['completions', '/organization/usage/completions', 'num_model_requests', 'requests'],
  ['embeddings', '/organization/usage/embeddings', 'input_tokens', 'tokens'],
  ['moderations', '/organization/usage/moderations', 'input_tokens', 'tokens'],
  ['audio_speeches', '/organization/usage/audio_speeches', 'characters', 'characters'],
  ['audio_transcriptions', '/organization/usage/audio_transcriptions', 'seconds', 'seconds'],
  ['images', '/organization/usage/images', 'images', 'images'],
  ['code_interpreter_sessions', '/organization/usage/code_interpreter_sessions',
    'num_sessions', 'sessions'],
  ['file_search_calls', '/organization/usage/file_search_calls', 'num_requests', 'calls'],
  ['web_search_calls', '/organization/usage/web_search_calls', 'num_requests', 'calls'],
];

// Matched in order. Audio, image and tool come before text because
// "gpt-image-1" and "gpt-4o-audio-preview" both contain a text-model substring.
const FAMILIES = [
  ['audio', ['audio', 'speech', 'transcription', 'whisper', 'tts', 'realtime']],
  ['image', ['image', 'dall-e']],
  ['tool', ['web search', 'web_search', 'file search', 'file_search',
            'code interpreter', 'code_interpreter', 'container']],
  ['embedding', ['embedding']],
  ['moderation', ['moderation']],
  ['text', ['input tokens', 'output tokens', 'cached input', 'cached_input',
            'gpt-', 'o1-', 'o3', 'o4-', 'chat']],
];

const MIXED_TOKEN_FIELDS = ['input_audio_tokens', 'output_audio_tokens',
                            'input_image_tokens', 'output_image_tokens'];

const FINDINGS = ['gap', 'unclassified-line-items'];

/**
 * Map a cost report line_item onto a modality family. Pure. "other" is
 * deliberately loud rather than a quiet bucket.
 */
export function family(lineItem) {
  const name = String(lineItem ?? '').trim().toLowerCase();
  if (!name) return 'other';
  for (const [label, markers] of FAMILIES) {
    if (markers.some((m) => name.includes(m))) return label;
  }
  return 'other';
}

/**
 * Split spend into what the dashboard covers and what it does not. Pure.
 * Amounts that will not parse count as unreadable rather than as zero, because
 * zero would shrink the gap.
 */
export function reconcile(items, covers) {
  const out = { total: 0, covered: 0, uncovered: 0, unreadable: 0,
                by_family: {}, rows: [] };
  const wanted = new Set([...covers].map((c) => String(c).trim().toLowerCase()));
  for (const [lineItem, amount, quantity, unit] of items) {
    const value = Number(amount);
    if (!Number.isFinite(value) || amount === null || amount === undefined
        || amount === '') {
      out.unreadable += 1;
      continue;
    }
    const label = family(lineItem);
    out.total += value;
    out.by_family[label] = (out.by_family[label] ?? 0) + value;
    if (wanted.has(label)) out.covered += value;
    else {
      out.uncovered += value;
      out.rows.push([label, String(lineItem), value, quantity, unit]);
    }
  }
  out.rows.sort((a, b) => b[2] - a[2]);
  return out;
}

/**
 * Is the remainder rounding or a hole? Pure. Returns [state, detail].
 * A gap made mostly of unclassifiable line items gets its own state, because
 * the repair is to read the strings rather than to add a known endpoint.
 */
export function verdict(recon, tolerance = 0.02) {
  const total = recon.total ?? 0;
  const uncovered = recon.uncovered ?? 0;
  if (total <= 0) {
    return ['no-spend', 'no spend in the window, so there is nothing to reconcile'];
  }

  const share = uncovered / total;
  const money = `$${total.toFixed(2)} total, $${uncovered.toFixed(2)} ` +
                `(${(share * 100).toFixed(1)}%) outside what the dashboard covers`;

  if (share < tolerance) {
    return ['reconciled', `${money}, inside the ${(tolerance * 100).toFixed(1)}% tolerance`];
  }

  const other = (recon.by_family ?? {}).other ?? 0;
  if (uncovered > 0 && other / uncovered > 0.5) {
    return ['unclassified-line-items',
      `${money}, and most of it is on line items this script could not ` +
      'classify. Read the raw line_item strings before assuming which endpoint ' +
      'explains them.'];
  }

  let biggest = ['nothing', 0];
  for (const [label, value] of Object.entries(recon.by_family ?? {})) {
    if (label === 'text') continue;
    if (value > biggest[1]) biggest = [label, value];
  }
  return ['gap',
    `${money}. Largest uncovered family is ${biggest[0]} at $${biggest[1].toFixed(2)}.`];
}

/**
 * Non-zero audio and image token counts inside a completions result. Pure.
 * A dashboard summing input_tokens and output_tokens whole is mixing these in
 * with text tokens at the text price.
 */
export function hiddenTokenTypes(result) {
  const out = [];
  for (const field of MIXED_TOKEN_FIELDS) {
    const value = Number(result[field] ?? 0);
    if (Number.isFinite(value) && value !== 0) out.push([field, Math.trunc(value)]);
  }
  return out.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: OPENAI_ADMIN_KEY must be an organization ' +
                    'admin key, not a project key');
  }
  if (res.status === 403) {
    throw new Error('403 from OpenAI: the key is not authorised for /v1/organization');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function costItems(key, startTime) {
  const out = [];
  const page = await get(key, '/organization/costs',
    { start_time: startTime, limit: 31, group_by: 'line_item' });
  for (const bucket of page.data ?? []) {
    for (const result of bucket.results ?? []) {
      out.push([result.line_item, result.amount?.value, result.quantity,
                result.quantity_unit]);
    }
  }
  return out;
}

async function surfaceVolume(key, path, field, startTime, days) {
  let total = 0;
  const page = await get(key, path,
    { start_time: startTime, bucket_width: '1d', limit: days });
  for (const bucket of page.data ?? []) {
    for (const result of bucket.results ?? []) {
      const n = Number(result[field] ?? 0);
      if (Number.isFinite(n)) total += Math.trunc(n);
    }
  }
  return total;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key with read scopes)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const covers = (process.env.COVERS ?? 'text').split(',').filter((c) => c.trim());
  const tolerance = Number(process.env.TOLERANCE ?? 0.02);

  const now = Math.floor(Date.now() / 1000);
  const start = now - days * 86400;

  const recon = reconcile(await costItems(key, start), covers);
  const [state, detail] = verdict(recon, tolerance);
  console.log(`${state.padEnd(24)} ${detail}`);

  for (const [label, lineItem, value, quantity, unit] of recon.rows.slice(0, 20)) {
    console.warn(`  uncovered  ${label.padEnd(10)} $${value.toFixed(2).padStart(9)}` +
                 `   ${String(lineItem).padEnd(28)} ${quantity ?? ''} ${unit ?? ''}`);
  }

  for (const [name, path, field, unit] of SURFACES) {
    const volume = await surfaceVolume(key, path, field, start, days);
    if (volume) console.log(`  volume     ${name.padEnd(28)} ${volume} ${unit}`);
  }

  if (recon.unreadable) {
    console.warn(`  ${recon.unreadable} cost row(s) had an unreadable amount and ` +
                 'were left out of both sides');
  }

  if (FINDINGS.includes(state)) {
    console.warn('  repair: drive the spend dashboard from /v1/organization/costs ' +
      'grouped by line_item, which is the only endpoint denominated in money, ' +
      'and use the per-modality usage endpoints to explain why a line moved');
    console.warn('  repair: inside completions, read input_text_tokens, ' +
      'input_audio_tokens and input_image_tokens separately instead of summing ' +
      'input_tokens whole');
    process.exitCode = 1;
    return;
  }
  process.exitCode = 0;
}

// Only run when invoked directly, so importing this from the test file does not
// run main(), fail on the missing key, and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist because of specific string collisions that would make the reconciliation lie. <code>gpt-image-1</code> contains <code>gpt-</code> and is not billed in text tokens; <code>gpt-4o-audio-preview</code> contains the same substring and is not either. Classifying by first match in the wrong order would quietly move real money into the covered column. The rest hold the states apart: a small gap is rounding, a large one is a hole, a gap made of line items nobody can name is a third thing, and a cost row with an unparseable amount is excluded from both sides rather than counted as zero.",
"test_py_file": "test_openai_modality_spend_reconcile.py",
"test_py": '''from openai_modality_spend_reconcile import (family, hidden_token_types,
                                             reconcile, verdict)


def items(*rows):
    """[(line_item, amount, quantity, quantity_unit), ...] from the cost report."""
    return [(r[0], r[1], r[2] if len(r) > 2 else None,
             r[3] if len(r) > 3 else None) for r in rows]


def test_the_dashboard_covers_text_and_the_bill_does_not_stop_there():
    recon = reconcile(items(("gpt-5, input tokens", 9000.00),
                            ("gpt-5, output tokens", 6487.43),
                            ("Text-to-speech", 1802.40, 14209881, "characters"),
                            ("Web search", 784.00, 78400, "requests"),
                            ("Image generation", 328.28, 6120, "images")),
                      covers=["text"])
    state, detail = verdict(recon)
    assert state == "gap"
    assert "$18402.11 total" in detail
    assert "$2914.68" in detail
    assert recon["rows"][0][0] == "audio"


def test_model_names_that_look_like_text_but_are_not():
    # Both contain "gpt-", and matching text first would move real money into
    # the covered column and shrink the gap to nothing.
    assert family("gpt-image-1") == "image"
    assert family("gpt-4o-audio-preview, input tokens") == "audio"
    assert family("gpt-5, input tokens") == "text"
    assert family("Code interpreter session") == "tool"
    assert family("text-embedding-3-small") == "embedding"


def test_a_small_gap_is_rounding_and_a_large_one_is_not():
    small = reconcile(items(("gpt-5, input tokens", 1000.00),
                            ("Moderations", 5.00)), covers=["text"])
    assert verdict(small)[0] == "reconciled"
    assert verdict(small, tolerance=0.001)[0] == "gap"


def test_line_items_nobody_can_classify_are_their_own_state():
    recon = reconcile(items(("gpt-5, input tokens", 500.00),
                            ("Some New Surface We Shipped Tuesday", 400.00)),
                      covers=["text"])
    state, detail = verdict(recon)
    assert state == "unclassified-line-items"
    assert "read the raw line_item strings" in detail.lower()


def test_an_unreadable_amount_is_not_counted_as_zero():
    recon = reconcile(items(("gpt-5, input tokens", 100.00),
                            ("Text-to-speech", None),
                            ("Web search", "n/a")), covers=["text"])
    assert recon["unreadable"] == 2
    assert recon["total"] == 100.00
    assert verdict(recon)[0] == "reconciled"


def test_nothing_to_reconcile_is_not_a_finding():
    assert verdict(reconcile([], covers=["text"]))[0] == "no-spend"


def test_multimodal_tokens_hide_inside_the_completions_result():
    result = {"input_tokens": 100000, "output_tokens": 8000,
              "input_text_tokens": 60000, "input_audio_tokens": 40000,
              "output_audio_tokens": 3000, "input_image_tokens": 0}
    assert hidden_token_types(result) == [("input_audio_tokens", 40000),
                                          ("output_audio_tokens", 3000)]
    assert hidden_token_types({"input_tokens": 100000}) == []
''',
"test_js_file": "openai-modality-spend-reconcile.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { family, hiddenTokenTypes, reconcile, verdict }
  from './openai-modality-spend-reconcile.mjs';

/** [[line_item, amount, quantity, quantity_unit], ...] from the cost report. */
function items(rows) {
  return rows.map((r) => [r[0], r[1], r[2] ?? null, r[3] ?? null]);
}

test('the dashboard covers text and the bill does not stop there', () => {
  const recon = reconcile(items([
    ['gpt-5, input tokens', 9000.00],
    ['gpt-5, output tokens', 6487.43],
    ['Text-to-speech', 1802.40, 14209881, 'characters'],
    ['Web search', 784.00, 78400, 'requests'],
    ['Image generation', 328.28, 6120, 'images'],
  ]), ['text']);
  const [state, detail] = verdict(recon);
  assert.equal(state, 'gap');
  assert.match(detail, /18402.11 total/);
  assert.match(detail, /2914.68/);
  assert.equal(recon.rows[0][0], 'audio');
});

test('model names that look like text but are not', () => {
  assert.equal(family('gpt-image-1'), 'image');
  assert.equal(family('gpt-4o-audio-preview, input tokens'), 'audio');
  assert.equal(family('gpt-5, input tokens'), 'text');
  assert.equal(family('Code interpreter session'), 'tool');
  assert.equal(family('text-embedding-3-small'), 'embedding');
});

test('a small gap is rounding and a large one is not', () => {
  const small = reconcile(items([['gpt-5, input tokens', 1000.00],
                                 ['Moderations', 5.00]]), ['text']);
  assert.equal(verdict(small)[0], 'reconciled');
  assert.equal(verdict(small, 0.001)[0], 'gap');
});

test('line items nobody can classify are their own state', () => {
  const recon = reconcile(items([['gpt-5, input tokens', 500.00],
                                 ['Some New Surface We Shipped Tuesday', 400.00]]),
                          ['text']);
  const [state, detail] = verdict(recon);
  assert.equal(state, 'unclassified-line-items');
  assert.match(detail.toLowerCase(), /read the raw line_item strings/);
});

test('an unreadable amount is not counted as zero', () => {
  const recon = reconcile(items([['gpt-5, input tokens', 100.00],
                                 ['Text-to-speech', null],
                                 ['Web search', 'n/a']]), ['text']);
  assert.equal(recon.unreadable, 2);
  assert.equal(recon.total, 100.00);
  assert.equal(verdict(recon)[0], 'reconciled');
});

test('nothing to reconcile is not a finding', () => {
  assert.equal(verdict(reconcile([], ['text']))[0], 'no-spend');
});

test('multimodal tokens hide inside the completions result', () => {
  const result = {
    input_tokens: 100000, output_tokens: 8000, input_text_tokens: 60000,
    input_audio_tokens: 40000, output_audio_tokens: 3000, input_image_tokens: 0,
  };
  assert.deepEqual(hiddenTokenTypes(result),
                   [['input_audio_tokens', 40000], ['output_audio_tokens', 3000]]);
  assert.deepEqual(hiddenTokenTypes({ input_tokens: 100000 }), []);
});
''',
"faq": [
 ("Which endpoint should a spend dashboard actually be built on?",
  "/v1/organization/costs grouped by line_item. It is the only one denominated in money, it covers every billable surface including ones that do not exist yet, and it is what the invoice agrees with. The per-modality usage endpoints belong underneath it, answering why a line item moved rather than what the total is."),
 ("Why can the usage endpoints not just report dollars?",
  "Because they report quantities, and the quantities are in incompatible units: characters for speech, seconds for transcription, images for generation, sessions for code interpreter, calls for web and file search, tokens for chat. Pricing each of those requires a price table that changes without warning, which is precisely the thing the cost report already does for you server-side."),
 ("What is the smallest useful version of this check?",
  "One call. Fetch costs grouped by line_item for the last thirty days and read the list of distinct line_item strings out loud. If any of them names something your dashboard does not render, you have the finding, and the full sweep of usage endpoints is only there to tell you how much of the thing was bought."),
 ("Does web search really bill separately from tokens?",
  "Yes, per call rather than per token, which is what makes it invisible in a token graph. An agent that searches twice per turn generates a line item that scales with conversation volume and never appears in input or output token counts. Code interpreter is the same shape, billed by container session with a free allowance you can exceed without noticing."),
 ("What about audio and images inside a chat completion?",
  "Those do flow through the completions endpoint, and they arrive as separate token type fields: input_audio_tokens, output_audio_tokens, input_image_tokens and their text sibling input_text_tokens. They are priced differently from text tokens, so a dashboard adding input_tokens and output_tokens whole is mispricing them rather than missing them. Read the type fields individually."),
],
"related": [REL_FT, REL_FRONTIER, REL_SPEND_LIMIT],
"citations": [CITE_USAGE, CITE_COSTS, CITE_PY_API, CITE_ADMIN],
},

{
"slug": "fine-tuned-model-never-used",
"title": "A fine-tuned model was trained, billed, and never called once",
"description": "Succeeded fine-tuning jobs name a model id. Thirty days of usage grouped by model shows zero requests against it. Training was paid for; inference never ran.",
"h1": "a fine-tuned model was trained, billed, and never called once",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai fine_tuning jobs list", "fine tuned model never used",
             "openai trained_tokens billed", "openai fine-tune-results files",
             "openai fine tuning deprecation 2027"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY (a project key set to Read Only) and OPENAI_ADMIN_KEY (an organization admin key with read scopes).",
"lead": "There was a quarter when fine-tuning was going to be the answer. Four jobs were queued over three weeks, each on a slightly better training file, and the last one came back with a loss curve somebody screenshotted into Slack. Then the base model got better, or the prompt got better, or the person who cared moved teams. The model ids are still there. They still resolve. They have between them served zero requests, and the training was invoiced the month it ran.",
"short_answer": """<p>Two keys, three reads. With a project key: <code>GET /v1/fine_tuning/jobs?limit=100</code>, and keep every job whose <code>status</code> is <code>succeeded</code> and whose <code>fine_tuned_model</code> is populated. With an organization admin key: <code>GET /v1/organization/usage/completions?start_time={now-30d}&amp;bucket_width=1d&amp;group_by=model</code>. Any custom model id with zero summed <code>num_model_requests</code> was trained and never called.</p>
<p>The job object also carries <code>trained_tokens</code>, which is what you paid for. Printing it next to a request count of zero is the entire finding in one line.</p>
<p>Then check the base. <code>GET /v1/models</code> lists what your key can actually call, and a fine-tune whose base model is no longer on that list is on borrowed time regardless of whether anybody uses it: inference on a fine-tune dies with its base model.</p>""",
"problem": """<p>Nothing here fails. The model exists, the id resolves, and a request to it would be served today. That is what makes it durable: there is no error to trigger a cleanup, no expiry to force a decision, and no field anywhere that says "this succeeded and then nobody wanted it".</p>
<p>Deploying a fine-tune is a change on your side. The API trains the model and hands you a string; switching traffic to that string is a config edit somebody has to make deliberately. So the natural end state of an experiment is a succeeded job whose output was never wired up, and the natural end state of a series of experiments is four of them, each superseded by the next, all still listed.</p>
<p>The residue is not only the model. Each job leaves <code>result_files</code> and, if checkpoints were enabled, intermediate model ids of its own. Those files sit against your storage quota and bill for it, quietly, for as long as nobody goes looking.</p>""",
"why": """<p><strong>Training and inference are separately billed and separately triggered.</strong> <code>trained_tokens</code> was charged when the job ran. Inference is charged per call, and if there are no calls there is no further charge &mdash; which is exactly why nothing ever complains. The waste is entirely in the past tense, and past-tense waste generates no signal.</p>
<p><strong>Zero usage is only readable from the org side.</strong> The job list is a project-key read; the request count per model is an admin read on <code>/v1/organization/usage/completions</code>. Neither key can do both, so this check genuinely needs two credentials, and a script that only has one of them can prove the model exists but not that it is idle.</p>
<p><strong>Absence of evidence is bounded by the window.</strong> Thirty days of zero usage is a strong signal and not a proof. A model called once a quarter for a compliance report will read as never-called, so the script says how long a window it looked at and the reader decides whether that is long enough.</p>
<p><strong>A fine-tune inherits its base model's mortality.</strong> Fine-tuned snapshots built on a retired base model stop answering when the base does. <code>GET /v1/models</code> is the cheap read for this: a base id that no longer appears there is already on the way out, and the custom model built on it goes with it whether or not anyone had plans for it.</p>
<p><strong>The platform is closing the door anyway.</strong> New fine-tuning jobs are being wound down &mdash; announced in May 2026, with active customers unable to create new jobs after 6 January 2027 &mdash; and fine-tuned snapshots on retired bases shut down on 23 October 2026. An unused custom model is not a debt that can be repaid later; the window in which it could be useful is closing on a published date.</p>""",
"steps": [
 {"h": "List the jobs with the project key",
  "body": """<p><code>GET /v1/fine_tuning/jobs?limit=100</code>, paginating on <code>after</code> while <code>has_more</code> is true. Keep <code>status</code>, <code>fine_tuned_model</code>, <code>model</code> (the base), <code>trained_tokens</code> and <code>result_files</code>. A job in any status other than <code>succeeded</code> is a different note.</p>"""},
 {"h": "Count requests per model with the admin key",
  "body": """<p><code>GET /v1/organization/usage/completions</code> over thirty days with <code>group_by=model</code>, summing <code>num_model_requests</code>. Custom model ids appear in that grouping exactly as they appear in the job object, so the join is a string match and needs no mapping table.</p>"""},
 {"h": "Read the base models that still exist",
  "body": """<p><code>GET /v1/models</code> with the project key. This is the list your key can actually call. A fine-tune whose base id is missing from it is a finding with a deadline attached, and it is a more urgent one than a fine-tune that is merely idle.</p>"""},
 {"h": "Follow the checkpoints and the result files",
  "body": """<p><code>GET /v1/fine_tuning/jobs/{id}/checkpoints</code> returns intermediate <code>fine_tuned_model_checkpoint</code> ids, each of which is another model nobody is calling. <code>GET /v1/files?purpose=fine-tune-results</code> lists the artefacts still occupying storage. Both are read-only and both add to the bill.</p>"""},
 {"h": "Print the decision, do not make it",
  "body": """<p>Two outcomes are legitimate: route traffic to the fine-tune, or retire it and delete its result files. The script prints both with the numbers attached &mdash; trained tokens, request count, window length, days until the base retirement date &mdash; and deletes nothing. A custom model somebody spent a quarter on is not something a cron job should remove at three in the morning.</p>"""},
],
"verify": """<p>Re-run after the decision is made either way. A model that is now serving traffic reads <code>in-service</code>; one that was deleted drops off the list entirely.</p>
<pre><code class="language-bash">python3 openai_fine_tune_usage_audit.py
# never-called   ft:gpt-4o-mini-2024-07-18:acme::AbC123  0 request(s) in 30 days, 4,182,900 trained token(s)
#   repair: route traffic to it or retire it; delete its result_files to stop storage charges
# 5 succeeded job(s) checked, 3 finding(s)</code></pre>""",
"code_intro": "Two credentials, because no single key can answer the question: <code>OPENAI_API_KEY</code> as a project key set to Read Only for the jobs, the models and the files, and <code>OPENAI_ADMIN_KEY</code> for the usage counts, which live on the organization. Every call is a GET. Three pure functions: parsing a base model id out of a fine-tune id, counting whole days to a published shutdown date with the clock passed in, and the verdict, which separates an idle model from an idle model whose base is already disappearing.",
"py_file": "openai_fine_tune_usage_audit.py",
"py": '''"""Report OpenAI fine-tuned models that were trained, billed, and never called.

Read only. GET requests and nothing else, and it needs two credentials because
no single key can answer the question:

  OPENAI_API_KEY    a project key set to Read Only, for /v1/fine_tuning/jobs,
                    /v1/models and /v1/files
  OPENAI_ADMIN_KEY  an organization admin key with read scopes, for
                    /v1/organization/usage/completions

The repair is printed, never performed. Deleting a custom model somebody spent
a quarter producing is a decision with an owner, and that owner is not a cron.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_fine_tune_usage_audit")

API = "https://api.openai.com/v1"

# Published platform dates. Fine-tuned snapshots built on a retired base model
# stop answering on the first; new fine-tuning jobs cannot be created after the
# second. Both are printed rather than acted on.
BASE_RETIREMENT = "2026-10-23"
NEW_JOBS_BLOCKED = "2027-01-06"

FINDINGS = ("never-called", "never-called-base-gone", "in-service-base-gone")


def base_model(fine_tuned_model):
    """The base model a fine-tune id was built on, or None. Pure.

    "ft:gpt-4o-mini-2024-07-18:acme::AbC123" -> "gpt-4o-mini-2024-07-18". The
    optional suffix segment moves the trailing id along, so this reads the
    second field rather than counting from the end.
    """
    name = str(fine_tuned_model or "").strip()
    if not name.lower().startswith("ft:"):
        return None
    parts = name.split(":")
    if len(parts) < 3 or not parts[1]:
        return None
    return parts[1]


def days_until(date_str, now):
    """Whole days from now until an ISO date, or None if unreadable. Pure.

    Negative once the date has passed. Floored toward the past, so a deadline
    fourteen hours away reads as 0 days rather than 1: this number is printed to
    somebody who will act on it tomorrow.
    """
    try:
        year, month, day = (int(p) for p in str(date_str).split("-"))
        target = dt.datetime(year, month, day, tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None
    return int((target - now).total_seconds() // 86400)


def verdict(job, requests_made, available_models, now, window_days=30):
    """Classify one fine-tuning job against its usage. Pure. Returns (state, detail).

    available_models is the set of ids GET /v1/models returned, which is what the
    key can actually call. A base missing from it puts a deadline on the custom
    model whether or not anyone is using it, so that case is split out rather
    than folded into the idle one.
    """
    status = str(job.get("status") or "").strip().lower()
    if status != "succeeded":
        return ("not-succeeded",
                "status is %s, so there is no model id to look for usage against"
                % (status or "missing"))

    model_id = str(job.get("fine_tuned_model") or "").strip()
    if not model_id:
        return ("unnamed",
                "the job succeeded and carries no fine_tuned_model. Read the "
                "object by hand rather than assuming nothing was produced.")

    try:
        trained = int(job.get("trained_tokens") or 0)
    except (TypeError, ValueError):
        trained = 0
    try:
        calls = int(requests_made or 0)
    except (TypeError, ValueError):
        calls = 0

    base = job.get("model") or base_model(model_id)
    base_gone = bool(base) and base not in set(available_models or ())
    deadline = days_until(BASE_RETIREMENT, now)
    clock = ("" if deadline is None else
             " Fine-tunes on retired base models stop answering in %d day(s)."
             % deadline)

    if calls > 0:
        if base_gone:
            return ("in-service-base-gone",
                    "%d request(s) in %d days, but the base model %s is no "
                    "longer listed by GET /v1/models. This fine-tune is serving "
                    "traffic and is going to stop.%s"
                    % (calls, window_days, base, clock))
        return ("in-service",
                "%d request(s) in %d days" % (calls, window_days))

    if base_gone:
        return ("never-called-base-gone",
                "0 request(s) in %d days, %d trained token(s), and the base "
                "model %s is no longer listed. Nothing to migrate and nothing "
                "to lose.%s" % (window_days, trained, base, clock))

    return ("never-called",
            "0 request(s) in %d days, %d trained token(s). Training was billed "
            "and inference never happened." % (window_days, trained))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI on %s: wrong key for this endpoint. "
                         "Jobs, models and files want the project key; usage "
                         "wants the admin key." % path)
    r.raise_for_status()
    return r.json()


def jobs(session, max_pages=20):
    """Walk GET /v1/fine_tuning/jobs, which paginates on the last job's id."""
    params = {"limit": 100}
    for _ in range(max_pages):
        page = get(session, "/fine_tuning/jobs", params)
        data = page.get("data") or []
        for job in data:
            yield job
        if not page.get("has_more") or not data:
            return
        params = {"limit": 100, "after": data[-1].get("id")}


def requests_by_model(session, start_time, days, max_pages=20):
    """Summed num_model_requests per model id. Needs the admin key."""
    out = {}
    params = {"start_time": start_time, "bucket_width": "1d", "limit": days,
              "group_by": "model"}
    for _ in range(max_pages):
        page = get(session, "/organization/usage/completions", params)
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                model = str(result.get("model") or "")
                if not model:
                    continue
                try:
                    out[model] = out.get(model, 0) + int(
                        result.get("num_model_requests") or 0)
                except (TypeError, ValueError):
                    pass
        cursor = page.get("next_page")
        if not cursor:
            return out
        params = dict(params, page=cursor)
    return out


def available_model_ids(session):
    page = get(session, "/models")
    return {str(m.get("id")) for m in page.get("data") or [] if m.get("id")}


def result_file_bytes(session):
    """Total bytes still held by fine-tune result files, and how many there are."""
    page = get(session, "/files", {"purpose": "fine-tune-results", "limit": 100})
    files = page.get("data") or []
    total = 0
    for f in files:
        try:
            total += int(f.get("bytes") or 0)
        except (TypeError, ValueError):
            pass
    return len(files), total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="usage window in days (default 30)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print jobs that are in service or not succeeded")
    args = ap.parse_args()

    project_key = os.environ.get("OPENAI_API_KEY")
    admin_key = os.environ.get("OPENAI_ADMIN_KEY")
    if not project_key or not admin_key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only) and "
                  "OPENAI_ADMIN_KEY (an organization admin key with read scopes)")
        return 2

    project = requests.Session()
    project.headers.update({"Authorization": "Bearer " + project_key})
    admin = requests.Session()
    admin.headers.update({"Authorization": "Bearer " + admin_key})

    now = dt.datetime.now(dt.timezone.utc)
    start = int((now - dt.timedelta(days=args.days)).timestamp())

    usage = requests_by_model(admin, start, args.days)
    available = available_model_ids(project)

    checked = 0
    bad = 0
    for job in jobs(project):
        model_id = str(job.get("fine_tuned_model") or "")
        state, detail = verdict(job, usage.get(model_id, 0), available, now,
                                args.days)
        if state != "not-succeeded":
            checked += 1
        line = "%-22s %-42s %s" % (state, model_id or job.get("id"), detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            checkpoints = get(project, "/fine_tuning/jobs/%s/checkpoints"
                              % job.get("id")).get("data") or []
            for cp in checkpoints:
                cp_id = cp.get("fine_tuned_model_checkpoint")
                if cp_id:
                    log.warning("  checkpoint %s: %d request(s) in the window",
                                cp_id, usage.get(str(cp_id), 0))
            log.warning("  repair: route traffic to it or retire it. Deleting "
                        "the custom model and its result_files stops the "
                        "storage charge; GET /v1/files?purpose=fine-tune-results "
                        "lists them.")
            left = days_until(NEW_JOBS_BLOCKED, now)
            if left is not None:
                log.warning("  repair: decide before the platform decides. New "
                            "fine-tuning jobs cannot be created after %s, %d "
                            "day(s) away.", NEW_JOBS_BLOCKED, left)
        elif args.show_all:
            log.info(line)

    count, total_bytes = result_file_bytes(project)
    if count:
        log.info("%d fine-tune result file(s) still stored, %.1f MB",
                 count, total_bytes / 1048576.0)

    log.info("%d succeeded job(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-fine-tune-usage-audit.mjs",
"js": '''/**
 * Report OpenAI fine-tuned models that were trained, billed, and never called.
 *
 * Read only. GET requests and nothing else, and it needs two credentials
 * because no single key can answer the question:
 *
 *   OPENAI_API_KEY    a project key set to Read Only, for /v1/fine_tuning/jobs,
 *                     /v1/models and /v1/files
 *   OPENAI_ADMIN_KEY  an organization admin key with read scopes, for
 *                     /v1/organization/usage/completions
 *
 * The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// Published platform dates. Fine-tuned snapshots on a retired base model stop
// answering on the first; new fine-tuning jobs cannot be created after the second.
const BASE_RETIREMENT = '2026-10-23';
const NEW_JOBS_BLOCKED = '2027-01-06';

const FINDINGS = ['never-called', 'never-called-base-gone', 'in-service-base-gone'];

/**
 * The base model a fine-tune id was built on, or null. Pure.
 * "ft:gpt-4o-mini-2024-07-18:acme::AbC123" -> "gpt-4o-mini-2024-07-18".
 */
export function baseModel(fineTunedModel) {
  const name = String(fineTunedModel ?? '').trim();
  if (!name.toLowerCase().startsWith('ft:')) return null;
  const parts = name.split(':');
  if (parts.length < 3 || !parts[1]) return null;
  return parts[1];
}

/**
 * Whole days from now until an ISO date, or null if unreadable. Pure.
 * Negative once the date has passed, and floored toward the past so a deadline
 * fourteen hours away reads as 0 days rather than 1.
 */
export function daysUntil(dateStr, now) {
  const parts = String(dateStr ?? '').split('-');
  if (parts.length !== 3) return null;
  const [year, month, day] = parts.map((p) => Number(p));
  if (![year, month, day].every(Number.isFinite)) return null;
  const target = Date.UTC(year, month - 1, day);
  const from = now instanceof Date ? now.getTime() : Number(now);
  if (!Number.isFinite(from)) return null;
  return Math.floor((target - from) / 86400000);
}

/**
 * Classify one fine-tuning job against its usage. Pure. Returns [state, detail].
 * A base model missing from GET /v1/models puts a deadline on the custom model
 * whether or not anyone is using it, so that case is split out.
 */
export function verdict(job, requestsMade, availableModels, now, windowDays = 30) {
  const status = String(job.status ?? '').trim().toLowerCase();
  if (status !== 'succeeded') {
    return ['not-succeeded',
      `status is ${status || 'missing'}, so there is no model id to look for ` +
      'usage against'];
  }

  const modelId = String(job.fine_tuned_model ?? '').trim();
  if (!modelId) {
    return ['unnamed',
      'the job succeeded and carries no fine_tuned_model. Read the object by ' +
      'hand rather than assuming nothing was produced.'];
  }

  const trainedRaw = Number(job.trained_tokens ?? 0);
  const trained = Number.isFinite(trainedRaw) ? Math.trunc(trainedRaw) : 0;
  const callsRaw = Number(requestsMade ?? 0);
  const calls = Number.isFinite(callsRaw) ? Math.trunc(callsRaw) : 0;

  const base = job.model ?? baseModel(modelId);
  const available = new Set(availableModels ?? []);
  const baseGone = Boolean(base) && !available.has(base);
  const deadline = daysUntil(BASE_RETIREMENT, now);
  const clock = deadline === null ? ''
    : ` Fine-tunes on retired base models stop answering in ${deadline} day(s).`;

  if (calls > 0) {
    if (baseGone) {
      return ['in-service-base-gone',
        `${calls} request(s) in ${windowDays} days, but the base model ${base} ` +
        'is no longer listed by GET /v1/models. This fine-tune is serving ' +
        `traffic and is going to stop.${clock}`];
    }
    return ['in-service', `${calls} request(s) in ${windowDays} days`];
  }

  if (baseGone) {
    return ['never-called-base-gone',
      `0 request(s) in ${windowDays} days, ${trained} trained token(s), and ` +
      `the base model ${base} is no longer listed. Nothing to migrate and ` +
      `nothing to lose.${clock}`];
  }

  return ['never-called',
    `0 request(s) in ${windowDays} days, ${trained} trained token(s). Training ` +
    'was billed and inference never happened.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error(`401 from OpenAI on ${path}: wrong key for this endpoint. ` +
      'Jobs, models and files want the project key; usage wants the admin key.');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* walkJobs(key, maxPages = 20) {
  let params = { limit: 100 };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/fine_tuning/jobs', params);
    const data = page.data ?? [];
    for (const job of data) yield job;
    if (!page.has_more || data.length === 0) return;
    params = { limit: 100, after: data[data.length - 1].id };
  }
}

async function requestsByModel(key, startTime, days, maxPages = 20) {
  const out = {};
  let params = {
    start_time: startTime, bucket_width: '1d', limit: days, group_by: 'model',
  };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/usage/completions', params);
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const model = String(result.model ?? '');
        if (!model) continue;
        const n = Number(result.num_model_requests ?? 0);
        if (Number.isFinite(n)) out[model] = (out[model] ?? 0) + Math.trunc(n);
      }
    }
    if (!page.next_page) return out;
    params = { ...params, page: page.next_page };
  }
  return out;
}

async function availableModelIds(key) {
  const page = await get(key, '/models');
  return new Set((page.data ?? []).filter((m) => m.id).map((m) => String(m.id)));
}

async function resultFileBytes(key) {
  const page = await get(key, '/files', { purpose: 'fine-tune-results', limit: 100 });
  const files = page.data ?? [];
  let total = 0;
  for (const f of files) {
    const n = Number(f.bytes ?? 0);
    if (Number.isFinite(n)) total += Math.trunc(n);
  }
  return [files.length, total];
}

async function main() {
  const projectKey = process.env.OPENAI_API_KEY;
  const adminKey = process.env.OPENAI_ADMIN_KEY;
  if (!projectKey || !adminKey) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only) and ' +
                  'OPENAI_ADMIN_KEY (an organization admin key with read scopes)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const showAll = process.argv.includes('--show-all');

  const nowMs = Date.now();
  const now = new Date(nowMs);
  const start = Math.floor(nowMs / 1000) - days * 86400;

  const usage = await requestsByModel(adminKey, start, days);
  const available = await availableModelIds(projectKey);

  let checked = 0;
  let bad = 0;
  for await (const job of walkJobs(projectKey)) {
    const modelId = String(job.fine_tuned_model ?? '');
    const [state, detail] = verdict(job, usage[modelId] ?? 0, available, now, days);
    if (state !== 'not-succeeded') checked += 1;
    const line = `${state.padEnd(22)} ${(modelId || job.id).padEnd(42)} ${detail}`;

    if (FINDINGS.includes(state)) {
      bad += 1;
      console.warn(line);
      const page = await get(projectKey, `/fine_tuning/jobs/${job.id}/checkpoints`);
      for (const cp of page.data ?? []) {
        const cpId = cp.fine_tuned_model_checkpoint;
        if (cpId) {
          console.warn(`  checkpoint ${cpId}: ${usage[String(cpId)] ?? 0} ` +
                       'request(s) in the window');
        }
      }
      console.warn('  repair: route traffic to it or retire it. Deleting the ' +
        'custom model and its result_files stops the storage charge; ' +
        'GET /v1/files?purpose=fine-tune-results lists them.');
      const left = daysUntil(NEW_JOBS_BLOCKED, now);
      if (left !== null) {
        console.warn('  repair: decide before the platform decides. New ' +
          `fine-tuning jobs cannot be created after ${NEW_JOBS_BLOCKED}, ` +
          `${left} day(s) away.`);
      }
    } else if (showAll) {
      console.log(line);
    }
  }

  const [count, totalBytes] = await resultFileBytes(projectKey);
  if (count) {
    console.log(`${count} fine-tune result file(s) still stored, ` +
                `${(totalBytes / 1048576).toFixed(1)} MB`);
  }

  console.log(`${checked} succeeded job(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this from the test file does not
// run main(), fail on the missing keys, and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note: a succeeded job with four million trained tokens and zero requests in thirty days. The second is the reason the check needs a fixed clock &mdash; a base model that has dropped off <code>GET /v1/models</code> turns an idle model into one with a published expiry date, and a model still serving traffic on a vanishing base is more urgent than either. The parsing test exists because a fine-tune id has an optional suffix segment, so counting fields from the end reads the wrong one.",
"test_py_file": "test_openai_fine_tune_usage_audit.py",
"test_py": '''import datetime as dt

from openai_fine_tune_usage_audit import base_model, days_until, verdict

NOW = dt.datetime(2026, 8, 30, 12, 0, tzinfo=dt.timezone.utc)
LIVE = {"gpt-4o-mini-2024-07-18", "gpt-5", "gpt-5-mini"}


def job(status="succeeded", model_id="ft:gpt-4o-mini-2024-07-18:acme::AbC123",
        base="gpt-4o-mini-2024-07-18", trained=4182900, **extra):
    body = {"id": "ftjob-test", "status": status, "fine_tuned_model": model_id,
            "model": base, "trained_tokens": trained}
    body.update(extra)
    return body


def test_trained_billed_and_never_called():
    state, detail = verdict(job(), 0, LIVE, NOW)
    assert state == "never-called"
    assert "0 request(s) in 30 days" in detail
    assert "4182900 trained token(s)" in detail


def test_a_model_serving_traffic_is_not_a_finding():
    assert verdict(job(), 91204, LIVE, NOW)[0] == "in-service"


def test_a_vanished_base_model_changes_both_answers():
    # Idle on a base that is going away: nothing to migrate, delete it.
    state, detail = verdict(job(base="gpt-4-0613",
                                model_id="ft:gpt-4-0613:acme::Old1"),
                            0, LIVE, NOW)
    assert state == "never-called-base-gone"
    assert "no longer listed" in detail
    assert "stop answering in 53 day(s)" in detail

    # In service on a base that is going away: this one is urgent.
    state, detail = verdict(job(base="gpt-4-0613",
                                model_id="ft:gpt-4-0613:acme::Old1"),
                            50000, LIVE, NOW)
    assert state == "in-service-base-gone"
    assert "going to stop" in detail


def test_jobs_that_produced_nothing_are_not_this_note():
    assert verdict(job(status="failed"), 0, LIVE, NOW)[0] == "not-succeeded"
    assert verdict(job(status="running"), 0, LIVE, NOW)[0] == "not-succeeded"
    assert verdict(job(status="cancelled"), 0, LIVE, NOW)[0] == "not-succeeded"
    state, detail = verdict(job(model_id=None), 0, LIVE, NOW)
    assert state == "unnamed"
    assert "by hand" in detail


def test_the_base_is_the_second_field_not_the_last_one():
    assert base_model("ft:gpt-4o-mini-2024-07-18:acme::AbC123") == "gpt-4o-mini-2024-07-18"
    # An optional suffix moves the trailing id along; the base does not move.
    assert base_model("ft:gpt-4o-2024-08-06:acme:nightly:AbC123") == "gpt-4o-2024-08-06"
    assert base_model("gpt-5") is None
    assert base_model("") is None
    assert base_model(None) is None


def test_the_deadline_is_floored_toward_the_past():
    assert days_until("2026-10-23", NOW) == 53
    # 12 hours short of the date is 0 days left, not 1.
    assert days_until("2026-08-31", NOW) == 0
    assert days_until("2026-08-30", NOW) == -1
    assert days_until("not-a-date", NOW) is None


def test_a_job_with_no_base_field_falls_back_to_the_model_id():
    # Some job objects carry the base only inside fine_tuned_model.
    state, _ = verdict({"id": "ftjob-x", "status": "succeeded",
                        "fine_tuned_model": "ft:gpt-4-0613:acme::Old1",
                        "trained_tokens": 100}, 0, LIVE, NOW)
    assert state == "never-called-base-gone"
''',
"test_js_file": "openai-fine-tune-usage-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { baseModel, daysUntil, verdict }
  from './openai-fine-tune-usage-audit.mjs';

const NOW = new Date(Date.UTC(2026, 7, 30, 12, 0, 0));
const LIVE = ['gpt-4o-mini-2024-07-18', 'gpt-5', 'gpt-5-mini'];

function job({ status = 'succeeded',
               modelId = 'ft:gpt-4o-mini-2024-07-18:acme::AbC123',
               base = 'gpt-4o-mini-2024-07-18', trained = 4182900,
               ...extra } = {}) {
  return {
    id: 'ftjob-test', status, fine_tuned_model: modelId, model: base,
    trained_tokens: trained, ...extra,
  };
}

test('trained, billed and never called', () => {
  const [state, detail] = verdict(job(), 0, LIVE, NOW);
  assert.equal(state, 'never-called');
  assert.match(detail, /0 request.s. in 30 days/);
  assert.match(detail, /4182900 trained token/);
});

test('a model serving traffic is not a finding', () => {
  assert.equal(verdict(job(), 91204, LIVE, NOW)[0], 'in-service');
});

test('a vanished base model changes both answers', () => {
  const idle = verdict(job({ base: 'gpt-4-0613', modelId: 'ft:gpt-4-0613:acme::Old1' }),
                       0, LIVE, NOW);
  assert.equal(idle[0], 'never-called-base-gone');
  assert.match(idle[1], /no longer listed/);
  assert.match(idle[1], /stop answering in 53 day/);

  const live = verdict(job({ base: 'gpt-4-0613', modelId: 'ft:gpt-4-0613:acme::Old1' }),
                       50000, LIVE, NOW);
  assert.equal(live[0], 'in-service-base-gone');
  assert.match(live[1], /going to stop/);
});

test('jobs that produced nothing are not this note', () => {
  for (const status of ['failed', 'running', 'cancelled']) {
    assert.equal(verdict(job({ status }), 0, LIVE, NOW)[0], 'not-succeeded');
  }
  const [state, detail] = verdict(job({ modelId: null }), 0, LIVE, NOW);
  assert.equal(state, 'unnamed');
  assert.match(detail, /by hand/);
});

test('the base is the second field not the last one', () => {
  assert.equal(baseModel('ft:gpt-4o-mini-2024-07-18:acme::AbC123'),
               'gpt-4o-mini-2024-07-18');
  assert.equal(baseModel('ft:gpt-4o-2024-08-06:acme:nightly:AbC123'),
               'gpt-4o-2024-08-06');
  assert.equal(baseModel('gpt-5'), null);
  assert.equal(baseModel(''), null);
  assert.equal(baseModel(null), null);
});

test('the deadline is floored toward the past', () => {
  assert.equal(daysUntil('2026-10-23', NOW), 53);
  assert.equal(daysUntil('2026-08-31', NOW), 0);
  assert.equal(daysUntil('2026-08-30', NOW), -1);
  assert.equal(daysUntil('not-a-date', NOW), null);
});

test('a job with no base field falls back to the model id', () => {
  const [state] = verdict({
    id: 'ftjob-x', status: 'succeeded',
    fine_tuned_model: 'ft:gpt-4-0613:acme::Old1', trained_tokens: 100,
  }, 0, LIVE, NOW);
  assert.equal(state, 'never-called-base-gone');
});
''',
"faq": [
 ("Thirty days of zero usage, is that really proof nobody wants it?",
  "It is evidence, not proof, and the script says how long a window it looked at for exactly that reason. A model called once a quarter for a compliance report will read as never-called. Widen the window before you delete anything, and note that the usage endpoint's own retention bounds how far back you can widen it."),
 ("Why does this need two API keys?",
  "Because the two halves of the question live on different sides of the platform. /v1/fine_tuning/jobs, /v1/models and /v1/files are project-scoped reads. Request counts per model live on /v1/organization/usage/completions, which rejects a project key outright. Neither credential can answer the question alone, which is why the script asks for both and says which one each call needs."),
 ("What does deleting the model actually save?",
  "Not inference, since nobody is calling it. It saves the storage charged against your result files and checkpoints, and it removes an id that will otherwise sit in someone's config waiting to be pasted into production by mistake. The storage number is usually small; the tidiness is worth more than the money."),
 ("Is fine-tuning going away entirely?",
  "New job creation is being wound down. It was announced in May 2026, and active customers cannot create new fine-tuning jobs after 6 January 2027. Separately, fine-tuned snapshots built on retired base models shut down on 23 October 2026, which is the deadline that actually bites: your custom model dies with the base it was trained on, regardless of the job-creation timeline."),
 ("Does Anthropic have an equivalent to audit?",
  "Not on the public API. There is no fine-tuning endpoint to list, so the analogous question there is about custom capacity and workspace-level commitments, which the Admin API does not expose either. The nearest read-only check on that side is the usage report grouped by model, which will tell you if a model id you expected to see is generating nothing."),
],
"related": [REL_MODALITY, REL_SHUTDOWN, REL_FRONTIER],
"citations": [CITE_FINE_TUNING, CITE_DEPRECATIONS, CITE_USAGE_COMPLETIONS, CITE_FILES],
},

]
