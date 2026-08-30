#!/usr/bin/env python3
"""/llm/ field notes, batch G — the writing.

Four dimensions of an Anthropic bill that are not priced per token. The section
already has a note about reconciling an invoice against a token dashboard in
general; this batch is the opposite move. Each of these reads exactly one field,
in one report, and says one thing about it.

`web-search-spend-unnoticed` prices a per-invocation tool fee.
`server_tool_use.web_search_requests` is a counter sitting beside the token
fields on the messages usage report, and $10 per 1,000 searches is charged on
top of whatever the tokens cost. Multiply the counter, confirm against the
cost report's own `web_search` rows, and the number exists.

`code-execution-hours-exceed-free-allowance` reads a `cost_type` the messages
usage report does not carry at all. Code execution is not in that report, in any
field, under any grouping. It appears only as money, and because the first 1,550
container hours each month are free, any non-zero amount at all is already the
finding rather than a number to compare against a threshold.

`us-inference-geo-premium-unnoticed` is about a multiplier on the rate card
rather than a volume of anything. `inference_geo: "us"` bills every token
category at 1.1x, and the parameter is usually inherited from a workspace's
`data_residency` block rather than chosen by any caller. So the usage report
says how much traffic is paying it and the workspaces endpoint says who decided.

`long-context-requests-unwatched` is the one that has to talk a reader out of a
belief. Grouping by `context_window` shows the `200k-1M` band's share of
uncached input, and the natural reading — that crossing 200k triggers premium
pricing — is wrong on current models. The band is a size alarm. It measures a
prefix that grows every turn, which costs base rate on a very large number and
degrades the answer as it fills.

Read-only throughout, and all four are Anthropic Admin API reads, so each wants
`ANTHROPIC_ADMIN_KEY` — an Admin key (`sk-ant-admin...`) that can be provisioned
read-only. A workspace key is rejected by every `/v1/organizations/*` path, and
an Admin key cannot send a message even if the script wanted to. GET requests
only. Every repair is printed: capping a tool's `max_uses`, detaching files from
a route, changing a workspace's residency and compacting an agent's context are
all decisions with owners, and none of those owners is a cron job.
"""

CITE_AN_USAGE = ("Get messages usage report — Claude Docs",
                 "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_AN_COST = ("Get cost report — Claude Docs",
                "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report")
CITE_AN_PRICING = ("Pricing — Claude Docs",
                   "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_AN_USAGE_COST_API = ("Usage and Cost API — Claude Docs",
                          "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_AN_WEB_SEARCH = ("Web search tool — Claude Docs",
                      "https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool")
CITE_AN_CODE_EXEC = ("Code execution tool — Claude Docs",
                     "https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool")
CITE_AN_WORKSPACES = ("List workspaces — Claude Docs",
                      "https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces")
CITE_AN_CONTEXT = ("Context windows — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/context-windows")
CITE_AN_CACHING = ("Prompt caching — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")

REL_WEBSEARCH = ("/llm/web-search-spend-unnoticed/",
                 "A tool fee charged per search, not per token")
REL_CODEEXEC = ("/llm/code-execution-hours-exceed-free-allowance/",
                "Container hours billed after the free 1,550 are gone")
REL_GEO = ("/llm/us-inference-geo-premium-unnoticed/",
           "A workspace setting that multiplies every token price")
REL_LONGCTX = ("/llm/long-context-requests-unwatched/",
               "The 200k-1M band is a size alarm, not a price band")
REL_MODALITY = ("/llm/audio-and-image-line-items-unnoticed/",
                "Spend that is not denominated in tokens at all")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")
REL_DOMINATES = ("/llm/one-model-or-project-dominates-cost/",
                 "One model or project carrying the whole invoice")
REL_SPIKE = ("/llm/spend-spike-week-over-week/",
             "A week that cost materially more than the ones before it")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "A stable prefix reprocessed at full price on every call")
REL_CACHE_WRITES = ("/llm/cache-writes-with-no-reads/",
                    "Cache entries written every call and never read back")
REL_FAST_MODE = ("/llm/fast-mode-silently-downgraded/",
                 "A service tier you configured and did not get")

GUIDES = [

{
"slug": "web-search-spend-unnoticed",
"title": "Web search is billing $10 per 1,000 searches unnoticed",
"description": "Sum server_tool_use.web_search_requests per key on the Claude usage report. The tool fee is $10 per 1,000 searches and no token graph can show it.",
"h1": "web search is billing $10 per 1,000 searches unnoticed",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic web search tool cost", "server_tool_use web_search_requests",
             "claude usage report server tool use", "claude web search max_uses",
             "anthropic cost report cost_type web_search"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only.",
"lead": "The research agent was allowed to search the web in March, because an agent that cannot look anything up is a party trick. Nobody put a ceiling on how many times it could search in one turn, because in March it searched twice. It now runs on every support ticket, it searches until it is satisfied, and satisfied averages eleven. None of that is a token, so the token dashboard on the wall behind the standup has never once flickered.",
"short_answer": """<p>With an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=api_key_id</code>. Every result carries a <code>server_tool_use</code> object beside the token fields. Sum <code>server_tool_use.web_search_requests</code> per key and multiply by $10 per 1,000.</p>
<p>That product is a real charge and it is not a token price. Web search is billed <strong>per search</strong>, at $10 per 1,000, on top of whatever the tokens for the turn cost. One search is one use whatever comes back, and a search that errors is not billed at all.</p>
<p>Confirm it on the money side with <code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=description</code>, keeping only the results whose <code>cost_type</code> is <code>web_search</code>. Those rows are the invoice's own name for the same thing, and if your estimate and their total disagree by much, read the rows rather than trusting either.</p>""",
"problem": """<p>The number climbs without a single symptom. Latency is fine, because search is fast. Quality is fine, because search is why the answers are good. Token volume is fine, or at least it moves for reasons everyone can already explain. And the graph that would show the problem does not have an axis for it, because the fee is denominated in searches and every graph in the building is denominated in tokens.</p>
<p>What turns it from an expense into a surprise is that the tool has no natural stopping point. A model that is allowed to search will search until it has what it needs, and the definition of "what it needs" moves with the prompt, the model version and the difficulty of the ticket. Nothing in the API caps it unless you set <code>max_uses</code>, and almost nobody sets <code>max_uses</code> on the afternoon they wire up the tool, because on that afternoon the agent searches twice.</p>
<p>There is a second charge stacked behind the first, and it is the one that compounds. Search results come back as input tokens for the turn that fetched them, and they stay in the conversation, so every subsequent turn pays for them again at input rates. The $10 per 1,000 is the part with a price list. The re-billed results are the part that grows with conversation length.</p>""",
"why": """<p><strong><code>server_tool_use</code> is a sibling of the token fields, not one of them.</strong> It is a nested object on each usage result, holding counters like <code>web_search_requests</code>. Code that walks the result flat, summing <code>input_tokens</code> and <code>output_tokens</code> and whatever else is at the top level, reads straight past it and reports an organization running a million searches a month as running none.</p>
<p><strong>The fee has its own <code>cost_type</code> on the cost report.</strong> Money for a server tool does not arrive as a <code>token_type</code>. It arrives as rows whose <code>cost_type</code> is <code>web_search</code>, which is why a dashboard that groups cost by token type sees the total shrink by exactly the amount it cannot explain.</p>
<p><strong>Counted searches and billed searches are allowed to differ.</strong> Each search is one use regardless of how many results it returns, and errored searches are not billed. So the counter can legitimately run ahead of the invoice. The script reports that as a state of its own rather than averaging the two into a number that is wrong in a way nobody can see.</p>
<p><strong>The cap is per tool definition, and it is the whole repair.</strong> <code>max_uses</code> on the web search tool bounds how many searches one request may make. <code>allowed_domains</code> narrows what it may reach. Both are one line in the tool definition, and both are decisions about what the agent is permitted to do, which is why an audit prints them instead of applying them.</p>
<p><strong>Grouping by <code>api_key_id</code> is what makes it actionable.</strong> An org-wide search count is a number to be alarmed by. A per-key count names the service, and the service names the route, and the route is where the <code>max_uses</code> line has to go.</p>""",
"steps": [
 {"h": "Read thirty days of usage grouped by key",
  "body": """<p><code>GET /v1/organizations/usage_report/messages</code> with <code>starting_at</code> at midnight UTC thirty days back, <code>bucket_width=1d</code>, <code>limit=31</code> and <code>group_by[]=api_key_id</code>. <code>starting_at</code> has to sit on a bucket boundary, so floor it to midnight rather than passing "now minus thirty days" and wondering why the first bucket is short.</p>"""},
 {"h": "Reach into server_tool_use rather than past it",
  "body": """<p>The counter is at <code>results[].server_tool_use.web_search_requests</code>. Any other counter that appears in that object is kept and reported under its own name: Anthropic ships new server tools, and a script that sums only the field it was written for keeps printing a reassuring number after the next billable tool arrives.</p>"""},
 {"h": "Multiply by ten per thousand, not by ten",
  "body": """<p>$10 per 1,000 searches. The arithmetic is trivial and the mistake is not: quoting a bill a thousand times too large in a channel where somebody is about to make a decision is worse than not having run the check.</p>"""},
 {"h": "Confirm against the cost report's own rows",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=description</code>, filtered to <code>cost_type == "web_search"</code>. <code>amount</code> comes back as a decimal string, so parse it. The script reports "confirmed", "billed with nothing counted", "counted with nothing billed" and "materially apart" as four different states, because they have four different explanations.</p>"""},
 {"h": "Print the cap and stop",
  "body": """<p>For the top keys, print the <code>max_uses</code> value that would have bounded last month's searches and the <code>allowed_domains</code> narrowing that would keep them useful. Then stop. Capping an agent's ability to look things up changes what it can answer, and that is a product decision with a named owner.</p>"""},
],
"verify": """<p>Set <code>max_uses</code>, redeploy, and re-read the same window a week later. The per-key search count should fall to roughly <code>max_uses</code> multiplied by request volume rather than to zero &mdash; the tool is supposed to still work.</p>
<pre><code class="language-bash">python3 anthropic_web_search_spend_audit.py
# search-fee     apikey_01Rs  118,400 search(es) at $10 per 1,000, a tool fee of about $1184.00 before a single token is priced
#   repair: set max_uses on the web search tool definition and narrow allowed_domains
# confirmed      $1174.40 billed against $1184.00 estimated, within 25%
# 4 key(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Two GETs against the Claude Admin API and nothing else, so <code>ANTHROPIC_ADMIN_KEY</code> has to be an Admin key (<code>sk-ant-admin...</code>); a workspace key is rejected by every <code>/v1/organizations/*</code> path. Five pure functions carry the whole check: the fold that reaches into <code>server_tool_use</code>, the fee arithmetic with its unit in the name, the cost-report filter that parses a decimal string, the per-key verdict, and the reconciliation that refuses to average two numbers that mean different things.",
"py_file": "anthropic_web_search_spend_audit.py",
"py": '''"""Report the per-search tool fee Claude web search is adding to the bill.

Read only. GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an Admin
API key (sk-ant-admin...), which can be provisioned read-only. A workspace key
is rejected by every /v1/organizations/* path.

This fee is not a token price. Web search bills $10 per 1,000 searches on top of
whatever the tokens cost, so no graph built on input and output tokens can show
it however carefully it is drawn.

The repair is printed, never applied. A max_uses cap and an allowed_domains
narrowing change what the agent is able to answer, and that belongs to whoever
owns the product, not to an audit holding an admin key.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_web_search_spend_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# $10 per 1,000 searches, charged per search regardless of how many results come
# back. The unit is in the name because the natural slip is to multiply by ten
# and quote a bill a thousand times too large.
FEE_PER_THOUSAND = 10.0

# The cost report's own name for the row. Money for a server tool does not
# arrive as a token_type; it arrives under its own cost_type.
COST_TYPE = "web_search"

FINDINGS = ("search-fee",)


def fold(pages):
    """Sum server tool invocations per API key. Pure.

    server_tool_use is a nested object sitting beside the token fields, not one
    of them. Walking the result flat finds nothing and reports an organization
    running a million searches a month as running none.

    Counters other than web_search_requests are kept under their own names
    rather than dropped. New server tools ship, and a script that sums only the
    field it was written for keeps printing the same reassuring number after the
    next billable one arrives.
    """
    out = {}
    for page in pages:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                key = str(result.get("api_key_id") or "unattributed")
                row = out.setdefault(key, {"web_search": 0, "other_tools": {}})
                use = result.get("server_tool_use")
                if not isinstance(use, dict):
                    continue
                for name, value in use.items():
                    try:
                        count = int(value or 0)
                    except (TypeError, ValueError):
                        continue
                    if count <= 0:
                        continue
                    if name == "web_search_requests":
                        row["web_search"] += count
                    else:
                        row["other_tools"][name] = row["other_tools"].get(name, 0) + count
    return out


def fee(searches, per_thousand=FEE_PER_THOUSAND):
    """Dollars owed for a number of searches. Pure."""
    try:
        n = int(searches or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(0, n) * per_thousand / 1000.0


def search_spend(cost_buckets, cost_type=COST_TYPE):
    """Sum the cost report rows the platform itself calls web search. Pure.

    amount arrives as a decimal string, not a number. Summing the raw values
    concatenates them in one language and throws in the other, and the failure
    is quiet enough to ship.
    """
    total = 0.0
    for bucket in cost_buckets or []:
        for result in bucket.get("results") or []:
            if str(result.get("cost_type") or "") != cost_type:
                continue
            raw = result.get("amount")
            if raw is None or raw == "":
                continue
            try:
                total += float(raw)
            except (TypeError, ValueError):
                pass
    return total


def verdict(row, min_searches=100):
    """Classify one key's search volume. Pure. Returns (state, detail).

    The floor exists because a handful of searches is a demo, not a bill, and a
    finding printed against it costs the reader more attention than it saves
    them money.
    """
    searches = int((row or {}).get("web_search") or 0)
    if searches <= 0:
        return ("no-searches", "the web search tool was never invoked by this key")
    if searches < min_searches:
        return ("low-volume",
                "%d search(es), under the floor of %d, worth about $%.2f"
                % (searches, min_searches, fee(searches)))
    return ("search-fee",
            "%d search(es) at $%.0f per 1,000, a tool fee of about $%.2f before "
            "a single token is priced"
            % (searches, FEE_PER_THOUSAND, fee(searches)))


def reconcile(estimate, billed, tolerance=0.25):
    """Compare the estimate against what was actually charged. Pure.

    Four states, not two, because the ways these two numbers can disagree have
    different explanations. A search that errors is counted as a use and not
    billed, so the estimate may legitimately run ahead. The cost report also
    lags. Neither is a licence to present one number as the other.
    """
    if estimate <= 0 and billed <= 0:
        return ("no-searches", "no searches counted and no web_search row billed")
    if billed <= 0:
        return ("unpriced",
                "$%.2f of searches counted and no web_search row on the cost "
                "report. Either the report has not caught up with the window, "
                "or the searches errored and were never billed." % estimate)
    if estimate <= 0:
        return ("billed-without-count",
                "$%.2f billed as web_search with no searches counted. The two "
                "reports are not covering the same days." % billed)
    drift = abs(billed - estimate) / estimate
    if drift <= tolerance:
        return ("confirmed",
                "$%.2f billed against $%.2f estimated, within %.0f%%"
                % (billed, estimate, tolerance * 100))
    return ("mismatch",
            "$%.2f billed against $%.2f estimated, %.0f%% apart. Read the "
            "web_search rows directly before quoting either number."
            % (billed, estimate, drift * 100))


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk the paginated usage or cost report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days):
    """Floor to midnight UTC: starting_at must sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily buckets to read (default 30)")
    ap.add_argument("--min-searches", type=int, default=100,
                    help="searches below which no claim is made (default 100)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print keys that never used the tool")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    start = window_start(args.days)
    rows = fold(pages(s, "/organizations/usage_report/messages",
                      {"starting_at": start, "bucket_width": "1d",
                       "limit": min(args.days + 1, 31),
                       "group_by[]": ["api_key_id"]}))

    cost_buckets = []
    for page in pages(s, "/organizations/cost_report",
                      {"starting_at": start, "limit": 31,
                       "group_by[]": ["description"]}):
        cost_buckets.extend(page.get("data") or [])

    checked = 0
    bad = 0
    estimate = 0.0
    for key in sorted(rows, key=lambda k: -rows[k]["web_search"]):
        row = rows[key]
        state, detail = verdict(row, args.min_searches)
        checked += 1
        estimate += fee(row["web_search"])
        line = "%-14s %-14s %s" % (state, key, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            log.warning("  repair: set max_uses on the web search tool "
                        "definition for this service and narrow allowed_domains "
                        "to the hosts its answers actually cite")
            log.warning("  note: search results also re-enter input tokens on "
                        "every later turn of the same conversation, which is a "
                        "second charge this fee does not include")
        elif state == "low-volume" or args.show_all:
            log.info(line)

        for name, count in sorted(row["other_tools"].items()):
            log.info("  other server tool %s: %d use(s) by %s", name, count, key)

    billed = search_spend(cost_buckets)
    state, detail = reconcile(estimate, billed)
    (log.info if state in ("confirmed", "no-searches") else log.warning)(
        "%-14s %s", state, detail)

    log.info("%d key(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-web-search-spend-audit.mjs",
"js": '''/**
 * Report the per-search tool fee Claude web search is adding to the bill.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path, and an Admin key can be provisioned read-only.
 *
 * The fee is not a token price. Web search bills $10 per 1,000 searches on top
 * of the tokens, so no graph built on input and output tokens can show it. The
 * repair is printed, never applied.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// $10 per 1,000 searches, charged per search regardless of how many results
// come back. The unit is in the name because the natural slip is to multiply by
// ten and quote a bill a thousand times too large.
const FEE_PER_THOUSAND = 10.0;

// The cost report's own name for the row. Server tool money does not arrive as
// a token_type; it arrives under its own cost_type.
const COST_TYPE = 'web_search';

const FINDINGS = ['search-fee'];

/**
 * Sum server tool invocations per API key. Pure.
 *
 * server_tool_use is a nested object sitting beside the token fields, not one
 * of them. Walking the result flat finds nothing. Counters other than
 * web_search_requests are kept under their own names, because new server tools
 * ship and a script that sums one field keeps printing a reassuring number.
 */
export function fold(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const key = String(result.api_key_id ?? 'unattributed');
        if (!out[key]) out[key] = { web_search: 0, other_tools: {} };
        const row = out[key];
        const use = result.server_tool_use;
        if (use === null || typeof use !== 'object' || Array.isArray(use)) continue;
        for (const [name, value] of Object.entries(use)) {
          const count = Math.trunc(Number(value ?? 0));
          if (!Number.isFinite(count) || count <= 0) continue;
          if (name === 'web_search_requests') row.web_search += count;
          else row.other_tools[name] = (row.other_tools[name] ?? 0) + count;
        }
      }
    }
  }
  return out;
}

/** Dollars owed for a number of searches. Pure. */
export function fee(searches, perThousand = FEE_PER_THOUSAND) {
  const n = Math.trunc(Number(searches ?? 0));
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, n) * perThousand / 1000;
}

/**
 * Sum the cost report rows the platform itself calls web search. Pure.
 * amount arrives as a decimal string, not a number.
 */
export function searchSpend(costBuckets, costType = COST_TYPE) {
  let total = 0;
  for (const bucket of costBuckets ?? []) {
    for (const result of bucket.results ?? []) {
      if (String(result.cost_type ?? '') !== costType) continue;
      const raw = result.amount;
      if (raw === null || raw === undefined || raw === '') continue;
      const value = Number(raw);
      if (Number.isFinite(value)) total += value;
    }
  }
  return total;
}

/**
 * Classify one key's search volume. Pure. Returns [state, detail].
 * The floor exists because a handful of searches is a demo, not a bill.
 */
export function verdict(row, minSearches = 100) {
  const searches = Math.trunc(Number(row?.web_search ?? 0)) || 0;
  if (searches <= 0) {
    return ['no-searches', 'the web search tool was never invoked by this key'];
  }
  if (searches < minSearches) {
    return ['low-volume',
      `${searches} search(es), under the floor of ${minSearches}, worth about ` +
      `$${fee(searches).toFixed(2)}`];
  }
  return ['search-fee',
    `${searches} search(es) at $${FEE_PER_THOUSAND.toFixed(0)} per 1,000, a ` +
    `tool fee of about $${fee(searches).toFixed(2)} before a single token is priced`];
}

/**
 * Compare the estimate against what was actually charged. Pure.
 *
 * Four states, not two. An errored search is counted as a use and not billed,
 * so the estimate may legitimately run ahead, and the cost report also lags.
 * Neither is a licence to present one number as the other.
 */
export function reconcile(estimate, billed, tolerance = 0.25) {
  if (estimate <= 0 && billed <= 0) {
    return ['no-searches', 'no searches counted and no web_search row billed'];
  }
  if (billed <= 0) {
    return ['unpriced',
      `$${estimate.toFixed(2)} of searches counted and no web_search row on ` +
      'the cost report. Either the report has not caught up with the window, ' +
      'or the searches errored and were never billed.'];
  }
  if (estimate <= 0) {
    return ['billed-without-count',
      `$${billed.toFixed(2)} billed as web_search with no searches counted. ` +
      'The two reports are not covering the same days.'];
  }
  const drift = Math.abs(billed - estimate) / estimate;
  if (drift <= tolerance) {
    return ['confirmed',
      `$${billed.toFixed(2)} billed against $${estimate.toFixed(2)} estimated, ` +
      `within ${(tolerance * 100).toFixed(0)}%`];
  }
  return ['mismatch',
    `$${billed.toFixed(2)} billed against $${estimate.toFixed(2)} estimated, ` +
    `${(drift * 100).toFixed(0)}% apart. Read the web_search rows directly ` +
    'before quoting either number.'];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
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

async function readPages(key, path, params) {
  const out = [];
  let next = { ...params };
  for (;;) {
    const page = await get(key, path, next);
    out.push(page);
    if (!page.has_more || !page.next_page) return out;
    next = { ...next, page: page.next_page };
  }
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. */
function windowStart(days) {
  const midnight = new Date();
  midnight.setUTCHours(0, 0, 0, 0);
  midnight.setUTCDate(midnight.getUTCDate() - days);
  return midnight.toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const minSearches = Number(process.env.MIN_SEARCHES ?? 100);
  const showAll = process.argv.includes('--show-all');
  const start = windowStart(days);

  const usage = await readPages(key, '/organizations/usage_report/messages', {
    starting_at: start, bucket_width: '1d', limit: Math.min(days + 1, 31),
    'group_by[]': ['api_key_id'],
  });
  const rows = fold(usage);

  const costBuckets = [];
  for (const page of await readPages(key, '/organizations/cost_report',
    { starting_at: start, limit: 31, 'group_by[]': ['description'] })) {
    costBuckets.push(...(page.data ?? []));
  }

  let checked = 0;
  let bad = 0;
  let estimate = 0;
  const keys = Object.keys(rows).sort((a, b) => rows[b].web_search - rows[a].web_search);
  for (const id of keys) {
    const row = rows[id];
    const [state, detail] = verdict(row, minSearches);
    checked += 1;
    estimate += fee(row.web_search);
    const line = `${state.padEnd(14)} ${id.padEnd(14)} ${detail}`;

    if (FINDINGS.includes(state)) {
      bad += 1;
      console.warn(line);
      console.warn('  repair: set max_uses on the web search tool definition ' +
                   'for this service and narrow allowed_domains to the hosts ' +
                   'its answers actually cite');
      console.warn('  note: search results also re-enter input tokens on every ' +
                   'later turn of the same conversation, which is a second ' +
                   'charge this fee does not include');
    } else if (state === 'low-volume' || showAll) {
      console.log(line);
    }

    for (const name of Object.keys(row.other_tools).sort()) {
      console.log(`  other server tool ${name}: ${row.other_tools[name]} use(s) by ${id}`);
    }
  }

  const billed = searchSpend(costBuckets);
  const [state, detail] = reconcile(estimate, billed);
  const say = (state === 'confirmed' || state === 'no-searches') ? console.log : console.warn;
  say(`${state.padEnd(14)} ${detail}`);

  console.log(`${checked} key(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing key, and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test is that <code>server_tool_use</code> is nested: a fold that reads the usage result flat returns zero searches for a key running a hundred thousand of them, and that is the entire failure this note exists to catch. After that the tests hold the fee arithmetic to its unit &mdash; $10 per <em>thousand</em>, not per search &mdash; keep an unrecognised server tool counter visible instead of dropped, and make sure the four ways the estimate and the invoice can disagree stay four separate answers.",
"test_py_file": "test_anthropic_web_search_spend_audit.py",
"test_py": '''from anthropic_web_search_spend_audit import (fee, fold, reconcile,
                                              search_spend, verdict)


def page(*results):
    """One page of GET /v1/organizations/usage_report/messages."""
    return {"data": [{"starting_at": "2026-08-01T00:00:00Z", "results": list(results)}],
            "has_more": False}


def usage(key="apikey_01Rs", searches=None, **tools):
    """One usage result. server_tool_use is nested beside the token fields."""
    use = dict(tools)
    if searches is not None:
        use["web_search_requests"] = searches
    row = {"api_key_id": key, "uncached_input_tokens": 900000,
           "output_tokens": 40000}
    if use:
        row["server_tool_use"] = use
    return row


def cost(cost_type="web_search", amount="1174.40"):
    """One bucket of GET /v1/organizations/cost_report."""
    return {"starting_at": "2026-08-01T00:00:00Z",
            "results": [{"cost_type": cost_type, "amount": amount,
                         "currency": "USD"}]}


def test_the_counter_is_nested_and_a_flat_read_finds_nothing():
    # The whole note. Both results carry a five figure search count, and a fold
    # that only looks at top-level fields reports this key as never searching.
    rows = fold([page(usage(searches=60000), usage(searches=58400))])
    assert rows["apikey_01Rs"]["web_search"] == 118400
    # A result with no server_tool_use at all is still a key, with zero searches.
    assert fold([page(usage())])["apikey_01Rs"]["web_search"] == 0


def test_the_fee_is_per_thousand_searches_not_per_search():
    assert fee(118400) == 1184.00
    assert fee(1) == 0.01
    assert fee(0) == 0.0
    assert fee(None) == 0.0


def test_a_high_volume_key_is_the_finding_and_quotes_the_fee():
    state, detail = verdict({"web_search": 118400, "other_tools": {}})
    assert state == "search-fee"
    assert "tool fee of about $1184.00" in detail


def test_a_handful_of_searches_is_a_demo_and_not_a_bill():
    assert verdict({"web_search": 12, "other_tools": {}})[0] == "low-volume"
    assert verdict({"web_search": 0, "other_tools": {}})[0] == "no-searches"
    assert verdict({})[0] == "no-searches"


def test_an_unknown_server_tool_counter_stays_visible():
    # A counter this script was not written for must not be silently dropped,
    # or the next billable server tool arrives and nothing changes on screen.
    rows = fold([page(usage(searches=200, web_fetch_requests=90,
                            code_execution_sessions=0))])
    row = rows["apikey_01Rs"]
    assert row["web_search"] == 200
    assert row["other_tools"] == {"web_fetch_requests": 90}


def test_only_the_web_search_cost_type_counts_and_amount_is_a_string():
    buckets = [cost("web_search", "1174.40"),
               cost("web_search", "10.00"),
               cost("code_execution", "500.00"),
               cost("web_search", "")]
    assert search_spend(buckets) == 1184.40
    assert search_spend([]) == 0.0


def test_the_four_ways_the_two_reports_can_disagree_stay_four_answers():
    assert reconcile(1184.00, 1174.40)[0] == "confirmed"
    # Counted but not billed: errored searches are free, and the report lags.
    assert reconcile(1184.00, 0.0)[0] == "unpriced"
    # Billed but not counted: the two windows do not line up.
    assert reconcile(0.0, 1174.40)[0] == "billed-without-count"
    state, detail = reconcile(100.00, 900.00)
    assert state == "mismatch"
    assert "800% apart" in detail
    assert reconcile(0.0, 0.0)[0] == "no-searches"
''',
"test_js_file": "anthropic-web-search-spend-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fee, fold, reconcile, searchSpend, verdict }
  from './anthropic-web-search-spend-audit.mjs';

/** One page of GET /v1/organizations/usage_report/messages. */
function page(...results) {
  return { data: [{ starting_at: '2026-08-01T00:00:00Z', results }], has_more: false };
}

/** One usage result. server_tool_use is nested beside the token fields. */
function usage({ key = 'apikey_01Rs', searches = null, tools = {} } = {}) {
  const use = { ...tools };
  if (searches !== null) use.web_search_requests = searches;
  const row = { api_key_id: key, uncached_input_tokens: 900000, output_tokens: 40000 };
  if (Object.keys(use).length) row.server_tool_use = use;
  return row;
}

/** One bucket of GET /v1/organizations/cost_report. */
function cost(costType = 'web_search', amount = '1174.40') {
  return {
    starting_at: '2026-08-01T00:00:00Z',
    results: [{ cost_type: costType, amount, currency: 'USD' }],
  };
}

test('the counter is nested and a flat read finds nothing', () => {
  const rows = fold([page(usage({ searches: 60000 }), usage({ searches: 58400 }))]);
  assert.equal(rows.apikey_01Rs.web_search, 118400);
  assert.equal(fold([page(usage())]).apikey_01Rs.web_search, 0);
});

test('the fee is per thousand searches, not per search', () => {
  assert.equal(fee(118400), 1184.00);
  assert.equal(fee(1), 0.01);
  assert.equal(fee(0), 0);
  assert.equal(fee(null), 0);
});

test('a high volume key is the finding and quotes the fee', () => {
  const [state, detail] = verdict({ web_search: 118400, other_tools: {} });
  assert.equal(state, 'search-fee');
  assert.match(detail, /tool fee of about \\$1184\\.00/);
});

test('a handful of searches is a demo and not a bill', () => {
  assert.equal(verdict({ web_search: 12, other_tools: {} })[0], 'low-volume');
  assert.equal(verdict({ web_search: 0, other_tools: {} })[0], 'no-searches');
  assert.equal(verdict({})[0], 'no-searches');
});

test('an unknown server tool counter stays visible', () => {
  const rows = fold([page(usage({
    searches: 200,
    tools: { web_fetch_requests: 90, code_execution_sessions: 0 },
  }))]);
  assert.equal(rows.apikey_01Rs.web_search, 200);
  assert.deepEqual(rows.apikey_01Rs.other_tools, { web_fetch_requests: 90 });
});

test('only the web_search cost type counts and amount is a string', () => {
  const buckets = [cost('web_search', '1174.40'), cost('web_search', '10.00'),
                   cost('code_execution', '500.00'), cost('web_search', '')];
  assert.equal(searchSpend(buckets), 1184.40);
  assert.equal(searchSpend([]), 0);
});

test('the four ways the two reports can disagree stay four answers', () => {
  assert.equal(reconcile(1184.00, 1174.40)[0], 'confirmed');
  assert.equal(reconcile(1184.00, 0)[0], 'unpriced');
  assert.equal(reconcile(0, 1174.40)[0], 'billed-without-count');
  const [state, detail] = reconcile(100.00, 900.00);
  assert.equal(state, 'mismatch');
  assert.match(detail, /800% apart/);
  assert.equal(reconcile(0, 0)[0], 'no-searches');
});
''',
"faq": [
 ("Does the $10 per 1,000 include the tokens the results add?",
  "No, and that is the part that compounds. The search fee is charged per invocation on top of token costs. The results themselves come back as input tokens for the turn that fetched them, and because they stay in the conversation, every later turn pays for them again at input rates. A ten-turn conversation that searched once in turn two has paid for those results nine more times. The fee is the part with a price list; the re-billing is the part that grows with conversation length."),
 ("Why can't I see this on a usage dashboard?",
  "Because there is no token axis it can sit on. The count lives at results[].server_tool_use.web_search_requests, which is a nested object beside the token fields rather than one of them, and the money lives on cost rows whose cost_type is web_search rather than a token_type. A dashboard that walks usage results flat and groups cost by token type is structurally unable to render either one."),
 ("My counted searches are higher than the billed amount. Is something wrong?",
  "Probably not. A search that errors is still counted as one use and is not billed, and the cost report lags real time by hours. That is why the script reports the comparison as a state rather than silently reconciling it: counted-but-not-billed and billed-but-not-counted have different explanations, and both are normal in small amounts. A persistent gap of more than a quarter is worth reading the raw rows over."),
 ("What does max_uses actually do to the agent?",
  "It bounds how many searches the model may make while answering one request. Set it too low and the agent stops before it has the answer, which shows up as worse answers rather than as an error, so pick the number from the distribution rather than from a hunch: if the ninetieth percentile of a good conversation is four searches, a cap of six costs nothing and removes the tail. allowed_domains is the other half, and it usually costs even less, because the domains a good answer cites are a short list."),
 ("Is there an equivalent check on OpenAI?",
  "The web search tool is billed per call there too, but the Usage API carries no server-tool counter, so there is no count to multiply. It surfaces only as a cost line item, which is a different reading with a different weakness, and the note on line items a token dashboard cannot render covers that side."),
],
"related": [REL_CODEEXEC, REL_MODALITY, REL_DOMINATES],
"citations": [CITE_AN_WEB_SEARCH, CITE_AN_USAGE, CITE_AN_COST, CITE_AN_PRICING],
},

{
"slug": "code-execution-hours-exceed-free-allowance",
"title": "Code execution has spent its free 1,550 container hours",
"description": "A non-zero code_execution row on the Claude cost report means the free 1,550 container hours are gone. The messages usage report never shows it.",
"h1": "code execution has spent its free 1,550 container hours",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic code execution container hours", "claude code_execution cost_type",
             "claude code execution free allowance 1550", "anthropic cost report code execution",
             "claude code execution billed without calling"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only.",
"lead": "The analytics route attaches the customer's CSV to the request, because sometimes the question is about the numbers in it and when it is, the model should be able to run something. Sometimes is about one call in forty. The other thirty-nine attach the file, spin up a container to hold it, ask something that needs no arithmetic at all, and are billed for five minutes of a machine that was never asked to do anything.",
"short_answer": """<p>One call with an <strong>Admin API key</strong>: <code>GET /v1/organizations/cost_report?starting_at={month start}&amp;limit=31&amp;group_by[]=description&amp;group_by[]=workspace_id</code>. Keep the results whose <code>cost_type</code> is <code>code_execution</code> and sum <code>amount</code> per workspace.</p>
<p><strong>Any non-zero total is the finding.</strong> There is no threshold to argue about. Each organization gets 1,550 free container hours a month, they are consumed before anything is charged, and billing at $0.05 per container-hour starts only once they are gone. A dollar on that row means the allowance is already spent.</p>
<p>Do not go looking for this in <code>GET /v1/organizations/usage_report/messages</code>. Code execution is excluded from that report entirely &mdash; no field, no grouping, no counter. It exists on the invoice and nowhere else, which is why a dashboard built on the usage report can be complete, correct and blind to it at the same time.</p>""",
"problem": """<p>Two things make this expensive quietly rather than loudly. The first is that a container is billed for wall-clock time with a five-minute minimum per execution, so a request that runs one line of Python for four hundred milliseconds costs the same as one that grinds for five minutes. A route that calls the tool often and briefly is the worst possible shape, and it is also the most common one.</p>
<p>The second is worse, because it does not require the tool to be called at all. If files are attached to a request, they are preloaded onto a container, and container time accrues whether or not the model ever reaches for the tool. So the cost is not driven by how often the model decides to compute something. It is driven by how often your code decides to attach a file just in case, which is a decision made once, in a code path, and never revisited.</p>
<p>Nothing in the API is going to raise this. The cost report will show it if you ask for the right <code>cost_type</code>, and the usage report will not show it under any circumstances, so the natural monitoring surface for an LLM integration &mdash; tokens over time, per model, per key &mdash; has no way to represent it. The first signal most teams get is the invoice.</p>""",
"why": """<p><strong>The allowance is the threshold, and the platform has already applied it.</strong> 1,550 container hours per organization per month, free, consumed first. You are not comparing a number against a budget; the platform did that before it wrote the row. Reading a non-zero <code>amount</code> and inferring "the allowance is gone" is exact, not heuristic.</p>
<p><strong>The messages usage report cannot see this line.</strong> It carries token fields, a <code>server_tool_use</code> object and grouping dimensions, and none of them account for code execution. That is a structural blind spot rather than an omission you can grouping your way around, and it is the reason this note reads the cost report first and the usage report only to prove the absence.</p>
<p><strong>Hours are derived, not reported.</strong> The API gives you dollars. At $0.05 per container-hour, dollars divided by the rate is billed hours, and adding the free 1,550 gives total container time for the month. The rate is a published price rather than a field, so the script keeps it as a named constant and lets you override it rather than pretending it read it.</p>
<p><strong>The five-minute minimum turns hours into a ceiling on executions, not a count.</strong> Every execution bills at least five minutes, so twelve billed hours could be one long job or one hundred and forty-four short ones, and never more than that. Reporting the ceiling is honest; reporting an execution count would not be.</p>
<p><strong>The charge can be removed rather than reduced.</strong> Code execution is free when bundled with a current web search or web fetch tool version (<code>web_search_20260209</code>, <code>web_fetch_20260209</code> or later). That makes the repair a tool-version question as often as it is a usage question, which is not where anyone looks first.</p>""",
"steps": [
 {"h": "Align the window to the calendar month",
  "body": """<p>The allowance resets monthly, so a rolling thirty-day window straddles two allowances and the arithmetic stops meaning anything. The script defaults <code>starting_at</code> to the first of the current month at midnight UTC, and takes <code>--days</code> only if you deliberately want a rolling read.</p>"""},
 {"h": "Group by description and workspace",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={month start}&amp;limit=31&amp;group_by[]=description&amp;group_by[]=workspace_id</code>. The workspace grouping is what makes the finding actionable: the org total tells you the allowance is gone, and the per-workspace split tells you whose route to go and read.</p>"""},
 {"h": "Filter on cost_type, and keep what you did not filter",
  "body": """<p>Keep <code>cost_type == "code_execution"</code>. Also keep a tally of every other <code>cost_type</code> the report returned, and print it. A cost type this script has never heard of is the next billable surface arriving, and a filter that silently discards everything it does not recognise is how it stays invisible for another quarter.</p>"""},
 {"h": "Prove the usage report cannot see it",
  "body": """<p>Read one page of <code>GET /v1/organizations/usage_report/messages</code> and scan every field name in every result for anything mentioning code execution. There is nothing, which is the point: the script says so out loud rather than leaving the reader to wonder whether it simply forgot to look.</p>"""},
 {"h": "Convert to hours, print the two repairs",
  "body": """<p>Dollars over $0.05 gives billed hours; add 1,550 for the month's total container time. Then print both repairs: find the routes attaching files to requests that never need the tool, and check whether pairing code execution with a current web search or web fetch tool version removes the charge outright.</p>"""},
],
"verify": """<p>Detach the file from the route that does not need it, then re-read the same month. The <code>code_execution</code> amount should stop growing day over day; it will not fall, because you cannot un-spend an allowance.</p>
<pre><code class="language-bash">python3 anthropic_code_execution_hours_audit.py
# allowance-spent  wrkspc_01Qy  $84.60 billed, which is 1692 container hour(s) on top of the free 1,550
#   at the 5 minute minimum that is at most 20304 execution(s)
#   repair: find the routes attaching files to requests that never call the tool
#   repair: bundling code execution with web_search_20260209 or later removes the charge
# note: the messages usage report carries no code execution field at all
# 3 workspace(s) with cost, 1 finding(s)</code></pre>""",
"code_intro": "One cost-report read and one page of the usage report, both GET, both against <code>/v1/organizations/*</code>, so this needs <code>ANTHROPIC_ADMIN_KEY</code> as an Admin key. The usage read is there only to demonstrate an absence. Six pure functions: parsing the decimal-string amount, folding cost into workspace and type, pulling out the one type that matters, converting dollars to container hours, bounding executions by the five-minute minimum, and the verdict &mdash; which has no threshold to tune, because the platform applied the only threshold there is before it wrote the row.",
"py_file": "anthropic_code_execution_hours_audit.py",
"py": '''"""Report that Claude code execution has spent its free container hours.

Read only. GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an Admin
API key (sk-ant-admin...), which can be provisioned read-only. A workspace key
is rejected by every /v1/organizations/* path.

The finding has no threshold. Each organization gets 1,550 free container hours
a month and they are consumed before anything is billed, so a non-zero amount on
a code_execution cost row means the allowance is already gone. The messages
usage report does not carry this line under any grouping, which is why the check
lives on the cost report and reads usage only to prove the absence.

The repair is printed, never applied. Detaching a file from a request path is a
deploy, and changing a tool version changes what the model can do.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_code_execution_hours_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Free container hours per organization per month. Consumed before anything is
# charged, which is what makes any non-zero amount a finding on its own.
FREE_CONTAINER_HOURS = 1550

# Published price per container hour, and the per-execution minimum. Both are
# prices rather than fields, so they are constants you can override rather than
# something this script pretends to have read from the API.
HOURLY_RATE = 0.05
MINIMUM_MINUTES = 5

COST_TYPE = "code_execution"

FINDINGS = ("allowance-just-crossed", "allowance-spent", "allowance-dwarfed")


def amount(row):
    """Read a cost row's amount as a float. Pure.

    The cost report returns amount as a decimal STRING. Summing the raw values
    concatenates them in one language and throws in the other.
    """
    raw = (row or {}).get("amount")
    if raw is None or raw == "":
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def fold(cost_buckets):
    """Sum spend into {workspace_id: {cost_type: dollars}}. Pure.

    Every cost_type is kept, not just the one being looked for. A filter that
    discards what it does not recognise is how the next billable surface stays
    invisible for a quarter.
    """
    out = {}
    for bucket in cost_buckets or []:
        for result in bucket.get("results") or []:
            workspace = str(result.get("workspace_id") or "default workspace")
            kind = str(result.get("cost_type") or "unspecified")
            per_type = out.setdefault(workspace, {})
            per_type[kind] = per_type.get(kind, 0.0) + amount(result)
    return out


def code_execution_spend(folded, cost_type=COST_TYPE):
    """Dollars of code execution per workspace, zeros dropped. Pure."""
    return {workspace: types[cost_type]
            for workspace, types in (folded or {}).items()
            if types.get(cost_type, 0.0) > 0}


def billed_hours(dollars, rate=HOURLY_RATE):
    """Container hours behind a dollar amount. Pure.

    Rounded rather than left raw. Dollars are a decimal quantity and 0.05 has no
    exact binary representation, so 84.60 / 0.05 comes out at 1691.9999999999998
    and every later int() reports an hour that was never missing.
    """
    if rate <= 0:
        raise ValueError("rate must be positive")
    return round(max(0.0, float(dollars or 0.0)) / rate, 6)


def executions_ceiling(hours, minimum_minutes=MINIMUM_MINUTES):
    """The most executions that could account for these hours. Pure.

    A ceiling and never a count. Every execution bills at least the minimum, so
    twelve hours is one long job or 144 short ones and nothing above that. The
    API does not report an execution count, and inventing one would be worse
    than saying how far the number could go.
    """
    if minimum_minutes <= 0:
        raise ValueError("minimum_minutes must be positive")
    return int(max(0.0, float(hours or 0.0)) * 60.0 / minimum_minutes)


def usage_report_mentions_code_execution(pages):
    """Does the messages usage report carry this line anywhere? Pure.

    The answer today is no, under any grouping, in any field. The check is here
    so the script can state that as an observation rather than an assumption,
    and so it starts reporting the field on the day one appears.
    """
    for page in pages or []:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                for name in result.keys():
                    if "code_execution" in str(name).lower():
                        return True
    return False


def verdict(dollars, free_hours=FREE_CONTAINER_HOURS, rate=HOURLY_RATE,
            marginal=5.0):
    """Classify one workspace's code execution spend. Pure. Returns (state, detail).

    There is no threshold to tune. The platform consumed the free allowance
    before it wrote the row, so zero means "inside the allowance" and anything
    else means "past it". The marginal band exists only to keep the language
    proportionate, not to suppress a finding.
    """
    spend = float(dollars or 0.0)
    if spend <= 0:
        return ("within-allowance",
                "no code_execution rows, so the free %d container hour(s) cover "
                "this workspace, or the tool is bundled free with a current web "
                "search or web fetch version" % free_hours)

    hours = billed_hours(spend, rate)
    shape = ("$%.2f billed, which is %d container hour(s) on top of the free %d"
             % (spend, int(hours), free_hours))

    if spend < marginal:
        return ("allowance-just-crossed",
                "%s. The allowance is gone; the overage is still small enough "
                "to fix before it is not." % shape)
    if hours > free_hours:
        return ("allowance-dwarfed",
                "%s. Billed hours now exceed the whole free allowance, so the "
                "free tier has stopped being a meaningful part of this bill."
                % shape)
    return ("allowance-spent",
            "%s. Container time is being charged on every execution from here "
            "to the end of the month." % shape)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk the paginated usage or cost report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def month_start():
    """First of the current month, midnight UTC.

    The allowance resets monthly, so a rolling window straddles two of them and
    the arithmetic stops meaning anything.
    """
    now = dt.datetime.now(dt.timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0,
                       microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def rolling_start(days):
    """Midnight UTC, days ago, for a deliberate rolling read."""
    now = dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=0,
                    help="read a rolling window instead of the calendar month")
    ap.add_argument("--rate", type=float, default=HOURLY_RATE,
                    help="dollars per container hour (default 0.05)")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    start = rolling_start(args.days) if args.days else month_start()
    if args.days:
        log.warning("reading a rolling %d day window: the free allowance resets "
                    "monthly, so this may span two of them", args.days)

    cost_buckets = []
    for page in pages(s, "/organizations/cost_report",
                      {"starting_at": start, "limit": 31,
                       "group_by[]": ["description", "workspace_id"]}):
        cost_buckets.extend(page.get("data") or [])

    folded = fold(cost_buckets)
    spend = code_execution_spend(folded)

    bad = 0
    for workspace in sorted(folded, key=lambda w: -folded[w].get(COST_TYPE, 0.0)):
        state, detail = verdict(spend.get(workspace, 0.0), rate=args.rate)
        line = "%-24s %-16s %s" % (state, workspace, detail)
        if state not in FINDINGS:
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        hours = billed_hours(spend[workspace], args.rate)
        log.warning("  at the %d minute minimum that is at most %d execution(s)",
                    MINIMUM_MINUTES, executions_ceiling(hours))
        log.warning("  repair: find the routes attaching files to requests that "
                    "never call the tool. Attached files are preloaded onto a "
                    "container and bill time whether the tool runs or not.")
        log.warning("  repair: bundling code execution with web_search_20260209 "
                    "or web_fetch_20260209 or later removes the charge entirely")

    seen = sorted({kind for types in folded.values() for kind in types})
    log.info("cost_type values in this window: %s", ", ".join(seen) or "none")

    usage = [next(iter(pages(s, "/organizations/usage_report/messages",
                             {"starting_at": start, "bucket_width": "1d",
                              "limit": 1})), {})]
    if usage_report_mentions_code_execution(usage):
        log.warning("the messages usage report now carries a code execution "
                    "field: read it, this script predates it")
    else:
        log.info("note: the messages usage report carries no code execution "
                 "field at all, which is why this check reads the cost report")

    log.info("%d workspace(s) with cost, %d finding(s)", len(folded), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-code-execution-hours-audit.mjs",
"js": '''/**
 * Report that Claude code execution has spent its free container hours.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path.
 *
 * The finding has no threshold. 1,550 free container hours per organization per
 * month are consumed before anything is billed, so a non-zero amount on a
 * code_execution cost row means the allowance is already gone. The messages
 * usage report does not carry this line under any grouping.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// Free container hours per organization per month, consumed before anything is
// charged. That is what makes any non-zero amount a finding on its own.
const FREE_CONTAINER_HOURS = 1550;

// Published price per container hour, and the per-execution minimum. Prices
// rather than fields, so they are constants rather than something this script
// pretends to have read from the API.
const HOURLY_RATE = 0.05;
const MINIMUM_MINUTES = 5;

const COST_TYPE = 'code_execution';

const FINDINGS = ['allowance-just-crossed', 'allowance-spent', 'allowance-dwarfed'];

/** Read a cost row's amount as a number. Pure. amount is a decimal STRING. */
export function amount(row) {
  const raw = row?.amount;
  if (raw === null || raw === undefined || raw === '') return 0;
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

/**
 * Sum spend into {workspace_id: {cost_type: dollars}}. Pure.
 * Every cost_type is kept. A filter that discards what it does not recognise is
 * how the next billable surface stays invisible for a quarter.
 */
export function fold(costBuckets) {
  const out = {};
  for (const bucket of costBuckets ?? []) {
    for (const result of bucket.results ?? []) {
      const workspace = String(result.workspace_id ?? 'default workspace');
      const kind = String(result.cost_type ?? 'unspecified');
      if (!out[workspace]) out[workspace] = {};
      out[workspace][kind] = (out[workspace][kind] ?? 0) + amount(result);
    }
  }
  return out;
}

/** Dollars of code execution per workspace, zeros dropped. Pure. */
export function codeExecutionSpend(folded, costType = COST_TYPE) {
  const out = {};
  for (const [workspace, types] of Object.entries(folded ?? {})) {
    if ((types[costType] ?? 0) > 0) out[workspace] = types[costType];
  }
  return out;
}

/**
 * Container hours behind a dollar amount. Pure.
 *
 * Rounded rather than left raw. Dollars are a decimal quantity and 0.05 has no
 * exact binary representation, so 84.60 / 0.05 comes out at 1691.9999999999998
 * and every later truncation reports an hour that was never missing.
 */
export function billedHours(dollars, rate = HOURLY_RATE) {
  if (rate <= 0) throw new Error('rate must be positive');
  return Math.round(Math.max(0, Number(dollars ?? 0)) / rate * 1e6) / 1e6;
}

/**
 * The most executions that could account for these hours. Pure.
 * A ceiling and never a count: every execution bills at least the minimum, and
 * the API reports no execution count at all.
 */
export function executionsCeiling(hours, minimumMinutes = MINIMUM_MINUTES) {
  if (minimumMinutes <= 0) throw new Error('minimumMinutes must be positive');
  return Math.trunc(Math.max(0, Number(hours ?? 0)) * 60 / minimumMinutes);
}

/**
 * Does the messages usage report carry this line anywhere? Pure.
 * The answer today is no, under any grouping. The check exists so the script
 * states that as an observation, and so it notices the day one appears.
 */
export function usageReportMentionsCodeExecution(pages) {
  for (const page of pages ?? []) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        for (const name of Object.keys(result ?? {})) {
          if (String(name).toLowerCase().includes('code_execution')) return true;
        }
      }
    }
  }
  return false;
}

/**
 * Classify one workspace's code execution spend. Pure. Returns [state, detail].
 * No threshold to tune: the platform consumed the free allowance before it
 * wrote the row, so zero is inside it and anything else is past it.
 */
export function verdict(dollars, freeHours = FREE_CONTAINER_HOURS,
                        rate = HOURLY_RATE, marginal = 5.0) {
  const spend = Number(dollars ?? 0);
  if (!(spend > 0)) {
    return ['within-allowance',
      `no code_execution rows, so the free ${freeHours} container hour(s) cover ` +
      'this workspace, or the tool is bundled free with a current web search ' +
      'or web fetch version'];
  }

  const hours = billedHours(spend, rate);
  const shape = `$${spend.toFixed(2)} billed, which is ${Math.trunc(hours)} ` +
                `container hour(s) on top of the free ${freeHours}`;

  if (spend < marginal) {
    return ['allowance-just-crossed',
      `${shape}. The allowance is gone; the overage is still small enough to ` +
      'fix before it is not.'];
  }
  if (hours > freeHours) {
    return ['allowance-dwarfed',
      `${shape}. Billed hours now exceed the whole free allowance, so the free ` +
      'tier has stopped being a meaningful part of this bill.'];
  }
  return ['allowance-spent',
    `${shape}. Container time is being charged on every execution from here to ` +
    'the end of the month.'];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
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

async function readPages(key, path, params) {
  const out = [];
  let next = { ...params };
  for (;;) {
    const page = await get(key, path, next);
    out.push(page);
    if (!page.has_more || !page.next_page) return out;
    next = { ...next, page: page.next_page };
  }
}

/** First of the current month, midnight UTC. The allowance resets monthly. */
function monthStart() {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1))
    .toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

/** Midnight UTC, days ago, for a deliberate rolling read. */
function rollingStart(days) {
  const midnight = new Date();
  midnight.setUTCHours(0, 0, 0, 0);
  midnight.setUTCDate(midnight.getUTCDate() - days);
  return midnight.toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 0);
  const rate = Number(process.env.RATE ?? HOURLY_RATE);
  const start = days ? rollingStart(days) : monthStart();
  if (days) {
    console.warn(`reading a rolling ${days} day window: the free allowance ` +
                 'resets monthly, so this may span two of them');
  }

  const costBuckets = [];
  for (const page of await readPages(key, '/organizations/cost_report',
    { starting_at: start, limit: 31, 'group_by[]': ['description', 'workspace_id'] })) {
    costBuckets.push(...(page.data ?? []));
  }

  const folded = fold(costBuckets);
  const spend = codeExecutionSpend(folded);

  let bad = 0;
  const workspaces = Object.keys(folded).sort(
    (a, b) => (folded[b][COST_TYPE] ?? 0) - (folded[a][COST_TYPE] ?? 0));
  for (const workspace of workspaces) {
    const [state, detail] = verdict(spend[workspace] ?? 0,
                                    FREE_CONTAINER_HOURS, rate);
    const line = `${state.padEnd(24)} ${workspace.padEnd(16)} ${detail}`;
    if (!FINDINGS.includes(state)) {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    const hours = billedHours(spend[workspace], rate);
    console.warn(`  at the ${MINIMUM_MINUTES} minute minimum that is at most ` +
                 `${executionsCeiling(hours)} execution(s)`);
    console.warn('  repair: find the routes attaching files to requests that ' +
                 'never call the tool. Attached files are preloaded onto a ' +
                 'container and bill time whether the tool runs or not.');
    console.warn('  repair: bundling code execution with web_search_20260209 ' +
                 'or web_fetch_20260209 or later removes the charge entirely');
  }

  const seen = [...new Set(Object.values(folded).flatMap((t) => Object.keys(t)))].sort();
  console.log(`cost_type values in this window: ${seen.join(', ') || 'none'}`);

  const usage = await readPages(key, '/organizations/usage_report/messages',
    { starting_at: start, bucket_width: '1d', limit: 1 });
  if (usageReportMentionsCodeExecution(usage.slice(0, 1))) {
    console.warn('the messages usage report now carries a code execution field: ' +
                 'read it, this script predates it');
  } else {
    console.log('note: the messages usage report carries no code execution ' +
                'field at all, which is why this check reads the cost report');
  }

  console.log(`${Object.keys(folded).length} workspace(s) with cost, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note in one line: sixty cents on a <code>code_execution</code> row is a finding, because the free hours were spent before that cent was charged. The second is the blind spot &mdash; a realistic messages usage result, with tokens and a <code>server_tool_use</code> object on it, contains no mention of code execution anywhere, and the function that looks would report one the day it appeared. The rest pin the decimal-string amount, the derived hours, and the fact that the execution figure is a ceiling rather than a count.",
"test_py_file": "test_anthropic_code_execution_hours_audit.py",
"test_py": '''from anthropic_code_execution_hours_audit import (amount, billed_hours,
                                                  code_execution_spend,
                                                  executions_ceiling, fold,
                                                  usage_report_mentions_code_execution,
                                                  verdict)


def cost(workspace="wrkspc_01Qy", cost_type="code_execution", value="84.60"):
    """One bucket of GET /v1/organizations/cost_report."""
    return {"starting_at": "2026-08-01T00:00:00Z",
            "results": [{"workspace_id": workspace, "cost_type": cost_type,
                         "description": "Code Execution Usage",
                         "amount": value, "currency": "USD"}]}


def usage_page():
    """One page of the messages usage report, as rich as it actually gets."""
    return {"data": [{"starting_at": "2026-08-01T00:00:00Z", "results": [{
        "uncached_input_tokens": 900000, "output_tokens": 40000,
        "cache_read_input_tokens": 120000,
        "cache_creation": {"ephemeral_5m_input_tokens": 30000,
                           "ephemeral_1h_input_tokens": 0},
        "server_tool_use": {"web_search_requests": 200},
        "model": "claude-sonnet-5", "api_key_id": "apikey_01Rs",
    }]}], "has_more": False}


def test_any_non_zero_amount_means_the_allowance_is_already_gone():
    # No threshold to argue about: the platform consumed the free 1,550 hours
    # before it wrote this row, so sixty cents is a finding.
    state, detail = verdict(0.60)
    assert state == "allowance-just-crossed"
    assert "12 container hour(s) on top of the free 1550" in detail
    assert verdict(0.0)[0] == "within-allowance"


def test_the_states_scale_with_how_far_past_the_allowance_you_are():
    assert verdict(40.00)[0] == "allowance-spent"
    state, detail = verdict(84.60)
    assert state == "allowance-dwarfed"
    assert "1692 container hour(s)" in detail


def test_the_usage_report_cannot_see_this_line_at_all():
    # The spine of the note. A usage result carrying tokens, cache fields and a
    # server_tool_use object still has nothing about code execution on it.
    assert usage_report_mentions_code_execution([usage_page()]) is False
    # And the check would notice the day a field did appear.
    future = {"data": [{"results": [{"code_execution_container_hours": 12}]}]}
    assert usage_report_mentions_code_execution([future]) is True


def test_amount_is_a_decimal_string_and_folds_by_workspace_and_type():
    assert amount({"amount": "84.60"}) == 84.60
    assert amount({"amount": ""}) == 0.0
    assert amount({}) == 0.0
    folded = fold([cost(value="80.00"), cost(value="4.60"),
                   cost(cost_type="web_search", value="500.00"),
                   cost(workspace="wrkspc_02Zz", cost_type="tokens", value="9.00")])
    assert folded["wrkspc_01Qy"]["code_execution"] == 84.60
    # Every cost_type is kept, not only the one being looked for.
    assert folded["wrkspc_01Qy"]["web_search"] == 500.00
    assert code_execution_spend(folded) == {"wrkspc_01Qy": 84.60}


def test_hours_are_derived_from_the_published_rate():
    assert billed_hours(84.60) == 1692.0
    assert billed_hours(0.0) == 0.0
    assert billed_hours(0.60) == 12.0


def test_the_execution_figure_is_a_ceiling_and_not_a_count():
    # Twelve billed hours is one long job or 144 short ones, and never more.
    assert executions_ceiling(12) == 144
    assert executions_ceiling(0) == 0
''',
"test_js_file": "anthropic-code-execution-hours-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { amount, billedHours, codeExecutionSpend, executionsCeiling, fold,
         usageReportMentionsCodeExecution, verdict }
  from './anthropic-code-execution-hours-audit.mjs';

/** One bucket of GET /v1/organizations/cost_report. */
function cost({ workspace = 'wrkspc_01Qy', costType = 'code_execution',
                value = '84.60' } = {}) {
  return {
    starting_at: '2026-08-01T00:00:00Z',
    results: [{ workspace_id: workspace, cost_type: costType,
                description: 'Code Execution Usage', amount: value, currency: 'USD' }],
  };
}

/** One page of the messages usage report, as rich as it actually gets. */
function usagePage() {
  return {
    data: [{
      starting_at: '2026-08-01T00:00:00Z',
      results: [{
        uncached_input_tokens: 900000, output_tokens: 40000,
        cache_read_input_tokens: 120000,
        cache_creation: { ephemeral_5m_input_tokens: 30000, ephemeral_1h_input_tokens: 0 },
        server_tool_use: { web_search_requests: 200 },
        model: 'claude-sonnet-5', api_key_id: 'apikey_01Rs',
      }],
    }],
    has_more: false,
  };
}

test('any non-zero amount means the allowance is already gone', () => {
  const [state, detail] = verdict(0.60);
  assert.equal(state, 'allowance-just-crossed');
  assert.match(detail, /12 container hour\\(s\\) on top of the free 1550/);
  assert.equal(verdict(0)[0], 'within-allowance');
});

test('the states scale with how far past the allowance you are', () => {
  assert.equal(verdict(40.00)[0], 'allowance-spent');
  const [state, detail] = verdict(84.60);
  assert.equal(state, 'allowance-dwarfed');
  assert.match(detail, /1692 container hour/);
});

test('the usage report cannot see this line at all', () => {
  assert.equal(usageReportMentionsCodeExecution([usagePage()]), false);
  const future = { data: [{ results: [{ code_execution_container_hours: 12 }] }] };
  assert.equal(usageReportMentionsCodeExecution([future]), true);
});

test('amount is a decimal string and folds by workspace and type', () => {
  assert.equal(amount({ amount: '84.60' }), 84.60);
  assert.equal(amount({ amount: '' }), 0);
  assert.equal(amount({}), 0);
  const folded = fold([cost({ value: '80.00' }), cost({ value: '4.60' }),
                       cost({ costType: 'web_search', value: '500.00' }),
                       cost({ workspace: 'wrkspc_02Zz', costType: 'tokens', value: '9.00' })]);
  assert.equal(folded.wrkspc_01Qy.code_execution, 84.60);
  assert.equal(folded.wrkspc_01Qy.web_search, 500.00);
  assert.deepEqual(codeExecutionSpend(folded), { wrkspc_01Qy: 84.60 });
});

test('hours are derived from the published rate', () => {
  assert.equal(billedHours(84.60), 1692);
  assert.equal(billedHours(0), 0);
  assert.equal(billedHours(0.60), 12);
});

test('the execution figure is a ceiling and not a count', () => {
  assert.equal(executionsCeiling(12), 144);
  assert.equal(executionsCeiling(0), 0);
});
''',
"faq": [
 ("Why is a single cent on that row a finding?",
  "Because the free allowance is applied before billing, not after. Every organization gets 1,550 container hours a month and they are consumed first, so the platform does not write a code_execution amount until they are gone. That makes the check exact rather than heuristic: there is no threshold to tune and no argument to have about where to set it. Zero means inside the allowance and anything else means past it."),
 ("How can I be charged when nobody called the tool?",
  "Attach a file to a request and it is preloaded onto a container, which starts accruing time whether or not the model ever reaches for code execution. That is the single most common cause of a surprising number here, because attaching a document just in case looks free from the call site. Find the routes that attach unconditionally and make the attachment conditional on the question."),
 ("Can I get container hours per workspace straight from the API?",
  "No. The report gives dollars, and hours are dollars divided by the published $0.05 rate. The script keeps the rate as an overridable constant rather than pretending it read it. The execution count is worse: with a five-minute minimum per execution, all you can honestly derive is a ceiling, so the script prints at most N executions and never a count."),
 ("Does the allowance reset, and does the window matter?",
  "It resets monthly, per organization, which is why the script defaults to the first of the current calendar month rather than a rolling thirty days. A rolling window spans two allowances and the arithmetic stops meaning anything. You can still ask for a rolling read with --days, and the script warns you when you do."),
 ("Is there a way to make the charge go away rather than shrink it?",
  "Sometimes. Code execution is free when it is bundled with a current web search or web fetch tool version, web_search_20260209 or web_fetch_20260209 or later, so a route that already uses both may be paying for something it could get at no charge by moving to a newer tool version string. That is worth checking before anyone starts optimising how often the model computes things."),
],
"related": [REL_WEBSEARCH, REL_MODALITY, REL_SPIKE],
"citations": [CITE_AN_CODE_EXEC, CITE_AN_COST, CITE_AN_USAGE_COST_API, CITE_AN_PRICING],
},

{
"slug": "us-inference-geo-premium-unnoticed",
"title": "US inference geo is billing every token at 1.1x",
"description": "Group the Claude usage report by inference_geo. A workspace whose data_residency defaults to us pays a 1.1x multiplier on every token category.",
"h1": "US inference geo is billing every token at 1.1x",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude inference_geo us premium", "anthropic data residency multiplier",
             "claude usage report group_by inference_geo", "anthropic us inference 1.1x pricing",
             "claude workspace default_inference_geo"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only.",
"lead": "Somebody in a procurement call last spring said that the data has to stay in the US, and somebody else, being helpful, went and set the workspace default that afternoon. Nobody wrote it down, because it took four seconds. The contract that prompted it was signed for one customer. The workspace serves all of them, and every token any of them has generated since has been billed at one and a tenth times the rate card.",
"short_answer": """<p><code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=inference_geo&amp;group_by[]=workspace_id</code> with an <strong>Admin API key</strong>. The <code>inference_geo</code> field comes back as <code>"global"</code>, <code>"us"</code>, <code>"not_available"</code> or null.</p>
<p>On Claude 4.6 and later, <code>inference_geo: "us"</code> applies a <strong>1.1x multiplier to every token pricing category</strong> &mdash; input, output, cache writes and cache reads alike. Caching does not dilute it, because the cache rates are multiplied too.</p>
<p>Then find out who chose it. <code>GET /v1/organizations/workspaces</code> returns each workspace's <code>data_residency</code> block with <code>default_inference_geo</code> and <code>allowed_inference_geos</code>. The parameter can be set per request, but far more often it is inherited from that default, which means the premium is being paid by traffic whose callers never asked for it and cannot see it.</p>""",
"problem": """<p>This is not a bug and not a mistake in the ordinary sense. US-only inference is a real product with a real reason to exist, and 10% is a reasonable price for it. The problem is that the decision is made once, in a workspace setting, on behalf of everything that will ever run in that workspace, and then it stops being visible to anyone.</p>
<p>The engineer writing the request does not set <code>inference_geo</code> and would not know it existed. The dashboard does not show it, because it is not a token count and not a model. The invoice shows a total that is 10% larger than a spreadsheet built from the public rate card, which reads as a rounding error, a mis-estimate, or someone's arithmetic being slightly off &mdash; three explanations that are all more comfortable than the real one.</p>
<p>And the blast radius is wrong. One customer's residency requirement is being satisfied by applying the premium to every customer's traffic, because the boundary that the requirement was scoped to is a contract and the boundary the setting applies to is a workspace, and nobody checked whether those two were the same shape.</p>""",
"why": """<p><strong>The multiplier is on the rate, not on a volume.</strong> Every other cost note in this section is about how much of something you bought. This one is about what each unit cost. That means no amount of tuning volume fixes it and no amount of caching dilutes it: cache reads at 0.1x base become 0.11x base, which is exactly as much of a premium proportionally as everything else.</p>
<p><strong>The premium is not ten percent of the bill.</strong> The billed amount already contains the multiplier, so recovering the premium from a US-attributed dollar figure is <code>(1.1 - 1) / 1.1</code>, about 9.09%, not 10%. Getting this backwards inflates the saving by a tenth in the one sentence a reader is going to quote at somebody.</p>
<p><strong>The workspace default and a per-request parameter are different findings.</strong> If <code>data_residency.default_inference_geo</code> is <code>us</code>, the traffic is paying because of a configuration decision, and the fix is a conversation about which workspaces actually carry regulated traffic. If the default is global and US traffic is still appearing, callers are setting the parameter explicitly, and the fix is in code. Same premium, different owner, so the script never reports them as one thing.</p>
<p><strong><code>not_available</code> is not <code>global</code>.</strong> Models released before February 2026 do not support the parameter at all and report <code>not_available</code>. That traffic pays no premium and has no lever, so folding it in with global traffic quietly overstates how much of your workload you could move.</p>
<p><strong>This is not the service-tier question.</strong> A tier decides what capacity serves you and how fast. <code>inference_geo</code> decides where the inference happens and multiplies the rate card. They are configured in different places, they fail in different directions, and a note about one is not a note about the other.</p>""",
"steps": [
 {"h": "Group thirty days by inference_geo and workspace",
  "body": """<p><code>GET /v1/organizations/usage_report/messages</code> with <code>group_by[]=inference_geo</code> and <code>group_by[]=workspace_id</code>, <code>bucket_width=1d</code>, <code>limit=31</code>, <code>starting_at</code> floored to midnight UTC. You can also filter directly with <code>inference_geo[]=us</code>, but grouping gives you the share, and the share is what makes the number mean anything.</p>"""},
 {"h": "Sum every priced token category, not just input",
  "body": """<p>The multiplier applies to all of them, so the measure has to be all of them: <code>uncached_input_tokens</code>, <code>output_tokens</code>, <code>cache_read_input_tokens</code>, and both nested fields under <code>cache_creation</code>. Reading <code>cache_creation</code> as if it were a number sums zero and understates a heavily cached workspace.</p>"""},
 {"h": "Read the residency block that decided it",
  "body": """<p><code>GET /v1/organizations/workspaces</code> and read <code>data_residency.default_inference_geo</code> and <code>data_residency.allowed_inference_geos</code> for every workspace that showed US traffic. This is the step that turns "we are paying a premium" into "this workspace is configured to, and here is when".</p>"""},
 {"h": "Price the premium out of the billed amount",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=workspace_id</code> gives spend per workspace. Multiply by the US token share and then by <code>(1.1 - 1) / 1.1</code>. The script states its assumption plainly: it takes the token mix as roughly the same across geos within one workspace, which is an approximation and is labelled as one.</p>"""},
 {"h": "Print the finding and leave the setting alone",
  "body": """<p>For a workspace defaulting to <code>us</code> with no stated compliance reason, print the monthly premium and the two questions worth asking: which contract required it, and whether that contract's traffic could live in its own workspace. Then stop. Data residency is a compliance setting and an audit script has no business changing one.</p>"""},
],
"verify": """<p>Move the regulated traffic into its own workspace, leave that one on <code>us</code>, set the rest back to <code>global</code>, and re-read the window. The US share should fall to roughly the regulated customers' share of volume rather than to zero.</p>
<pre><code class="language-bash">python3 anthropic_inference_geo_premium_audit.py
# us-by-workspace-default  wrkspc_01Qy  98% of 412.4M priced token(s) on inference_geo us; data_residency.default_inference_geo is us
#   estimated premium about $874.31 of $10192.00 spend in this window
#   repair: confirm which contract requires US residency, and whether that traffic can live in its own workspace
# 4 workspace(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "Three GETs, all read-only, all against <code>/v1/organizations/*</code>, so <code>ANTHROPIC_ADMIN_KEY</code> has to be an Admin key. Six pure functions: normalising the geo value so a null does not become <code>global</code>, summing the five priced token fields including the nested cache-creation pair, folding into workspace and geo, computing the US share, backing the premium out of a billed amount rather than adding it on, and the verdict that keeps a workspace default and a per-request parameter as two separate findings.",
"py_file": "anthropic_inference_geo_premium_audit.py",
"py": '''"""Report Claude traffic paying the US inference geo premium.

Read only. GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an Admin
API key (sk-ant-admin...), which can be provisioned read-only. A workspace key
is rejected by every /v1/organizations/* path.

inference_geo "us" multiplies every token pricing category by 1.1 on Claude 4.6
and later. The parameter is usually not chosen per request: it is inherited from
a workspace's data_residency.default_inference_geo, which means the premium is
paid by traffic whose callers never asked for it.

The repair is printed, never applied. Data residency is a compliance setting.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_inference_geo_premium_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# 1.1x on every token pricing category: input, output, cache writes and cache
# reads alike. Caching does not dilute it, because the cache rates move too.
GEO_MULTIPLIER = 1.1

# Every token field the multiplier touches. cache_creation is nested, and a flat
# read of it sums zero and understates a heavily cached workspace.
FLAT_TOKEN_FIELDS = ("uncached_input_tokens", "output_tokens",
                     "cache_read_input_tokens")
NESTED_TOKEN_FIELDS = ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens")

FINDINGS = ("us-by-workspace-default", "us-by-request", "us-unexplained")


def geo_of(result):
    """Normalise the inference_geo value. Pure.

    A null becomes "unspecified" and never "global". They are different facts:
    one is traffic served globally, the other is traffic the report declined to
    place, and quietly merging them flatters the share in the wrong direction.
    """
    raw = str((result or {}).get("inference_geo") or "").strip().lower()
    if raw in ("us", "global", "not_available"):
        return raw
    return "unspecified"


def tokens_of(result):
    """Sum every priced token category on one usage result. Pure.

    All of them, because the multiplier applies to all of them. cache_creation
    is a nested object; reading it as a number is how a cached workspace comes
    out looking small.
    """
    total = 0
    for field in FLAT_TOKEN_FIELDS:
        try:
            total += int((result or {}).get(field) or 0)
        except (TypeError, ValueError):
            pass
    creation = (result or {}).get("cache_creation")
    if isinstance(creation, dict):
        for field in NESTED_TOKEN_FIELDS:
            try:
                total += int(creation.get(field) or 0)
            except (TypeError, ValueError):
                pass
    return total


def fold(pages):
    """Sum priced tokens into {workspace_id: {geo: tokens}}. Pure."""
    out = {}
    for page in pages:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                workspace = str(result.get("workspace_id") or "default workspace")
                geo = geo_of(result)
                per_geo = out.setdefault(workspace, {})
                per_geo[geo] = per_geo.get(geo, 0) + tokens_of(result)
    return out


def us_share(geo_totals):
    """The share of priced tokens served on inference_geo us. Pure."""
    total = sum(int(v or 0) for v in (geo_totals or {}).values())
    if total <= 0:
        return 0.0
    return int((geo_totals or {}).get("us") or 0) / float(total)


def premium_estimate(billed_dollars, share, multiplier=GEO_MULTIPLIER):
    """Back the premium out of an amount that already contains it. Pure.

    NOT billed * share * 0.1. The billed figure is already 1.1x the base rate,
    so the premium is (m - 1) / m of it, about 9.09%. Adding the multiplier on
    instead of removing it overstates the saving by a tenth, in the one sentence
    somebody is going to quote at whoever owns the budget.

    Assumes the token mix is roughly the same across geos inside one workspace,
    which is an approximation and is labelled as one wherever it is printed.
    """
    if multiplier <= 1.0:
        return 0.0
    dollars = max(0.0, float(billed_dollars or 0.0))
    fraction = min(1.0, max(0.0, float(share or 0.0)))
    return dollars * fraction * (multiplier - 1.0) / multiplier


def residency_default(workspace):
    """A workspace's configured default inference geo. Pure.

    Returns "us", "global", "not_available" or "unset". "unset" covers both a
    missing data_residency block and one this script cannot read, because the
    repair is the same in either case: go and look at the workspace.
    """
    block = (workspace or {}).get("data_residency")
    if not isinstance(block, dict):
        return "unset"
    value = str(block.get("default_inference_geo") or "").strip().lower()
    return value if value in ("us", "global", "not_available") else "unset"


def verdict(geo_totals, default_geo, min_tokens=1_000_000):
    """Classify one workspace. Pure. Returns (state, detail).

    A workspace default and an explicit per-request parameter are kept apart
    deliberately. The premium is identical; the owner of the fix is not.
    """
    totals = geo_totals or {}
    total = sum(int(v or 0) for v in totals.values())
    if total < min_tokens:
        return ("low-volume",
                "%d priced token(s) in the window, too few to conclude anything"
                % total)

    us = int(totals.get("us") or 0)
    if us <= 0:
        if int(totals.get("not_available") or 0) >= total:
            return ("geo-unsupported",
                    "%.1fM priced token(s), all on models that predate the "
                    "inference_geo parameter. No premium and no lever."
                    % (total / 1e6))
        return ("no-us-traffic",
                "%.1fM priced token(s) and none of it on inference_geo us"
                % (total / 1e6))

    share = us / float(total)
    shape = ("%.0f%% of %.1fM priced token(s) on inference_geo us"
             % (share * 100, total / 1e6))

    if default_geo == "us":
        return ("us-by-workspace-default",
                "%s; data_residency.default_inference_geo is us, so every "
                "caller pays the 1.1x whether or not any of them asked."
                % shape)
    if default_geo == "global":
        return ("us-by-request",
                "%s while the workspace default is global, so callers are "
                "setting inference_geo explicitly. The fix is in code, not in "
                "the workspace." % shape)
    return ("us-unexplained",
            "%s with no readable data_residency default. Read the workspace "
            "before deciding whether this is deliberate." % shape)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk the paginated usage or cost report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def workspaces(session):
    """Every workspace, keyed by id, including archived ones."""
    out = {}
    params = {"limit": 100, "include_archived": "true"}
    while True:
        page = get(session, "/organizations/workspaces", params)
        for item in page.get("data") or []:
            out[str(item.get("id"))] = item
        if not page.get("has_more") or not page.get("last_id"):
            return out
        params = dict(params, after_id=page["last_id"])


def spend_by_workspace(session, start):
    """Thirty days of spend per workspace. amount is a decimal string."""
    out = {}
    for page in pages(session, "/organizations/cost_report",
                      {"starting_at": start, "limit": 31,
                       "group_by[]": ["workspace_id"]}):
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                workspace = str(result.get("workspace_id") or "default workspace")
                raw = result.get("amount")
                try:
                    out[workspace] = out.get(workspace, 0.0) + float(raw or 0.0)
                except (TypeError, ValueError):
                    pass
    return out


def window_start(days):
    """Floor to midnight UTC: starting_at must sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily buckets to read (default 30)")
    ap.add_argument("--min-tokens", type=int, default=1_000_000,
                    help="priced tokens below which no claim is made")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    start = window_start(args.days)
    rows = fold(pages(s, "/organizations/usage_report/messages",
                      {"starting_at": start, "bucket_width": "1d",
                       "limit": min(args.days + 1, 31),
                       "group_by[]": ["inference_geo", "workspace_id"]}))
    directory = workspaces(s)
    spend = spend_by_workspace(s, start)

    checked = 0
    bad = 0
    for workspace in sorted(rows, key=lambda w: -(rows[w].get("us") or 0)):
        totals = rows[workspace]
        default_geo = residency_default(directory.get(workspace))
        state, detail = verdict(totals, default_geo, args.min_tokens)
        checked += 1
        line = "%-24s %-16s %s" % (state, workspace, detail)

        if state not in FINDINGS:
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        billed = spend.get(workspace, 0.0)
        log.warning("  estimated premium about $%.2f of $%.2f spend in this "
                    "window, assuming a similar token mix across geos",
                    premium_estimate(billed, us_share(totals)), billed)
        allowed = ((directory.get(workspace) or {}).get("data_residency")
                   or {}).get("allowed_inference_geos")
        if allowed:
            log.warning("  allowed_inference_geos: %s", ", ".join(map(str, allowed)))
        if state == "us-by-workspace-default":
            log.warning("  repair: confirm which contract requires US residency, "
                        "and whether that traffic can live in its own workspace "
                        "instead of every workspace paying for it")
        elif state == "us-by-request":
            log.warning("  repair: the callers are setting inference_geo "
                        "themselves. Find them before changing anything here.")
        else:
            log.warning("  repair: read this workspace's data_residency block "
                        "and record why it is set the way it is")
        log.warning("  do not change residency from a script: it is a "
                    "compliance setting with a named owner")

    log.info("%d workspace(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-inference-geo-premium-audit.mjs",
"js": '''/**
 * Report Claude traffic paying the US inference geo premium.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path.
 *
 * inference_geo "us" multiplies every token pricing category by 1.1 on Claude
 * 4.6 and later, and is usually inherited from a workspace's
 * data_residency.default_inference_geo rather than chosen per request. The
 * repair is printed, never applied: residency is a compliance setting.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// 1.1x on every token pricing category. Caching does not dilute it, because
// the cache rates are multiplied too.
const GEO_MULTIPLIER = 1.1;

// Every token field the multiplier touches. cache_creation is nested, and a
// flat read of it sums zero.
const FLAT_TOKEN_FIELDS = ['uncached_input_tokens', 'output_tokens',
                           'cache_read_input_tokens'];
const NESTED_TOKEN_FIELDS = ['ephemeral_5m_input_tokens', 'ephemeral_1h_input_tokens'];

const FINDINGS = ['us-by-workspace-default', 'us-by-request', 'us-unexplained'];

/**
 * Normalise the inference_geo value. Pure. A null becomes "unspecified" and
 * never "global": one is traffic served globally, the other is traffic the
 * report declined to place.
 */
export function geoOf(result) {
  const raw = String(result?.inference_geo ?? '').trim().toLowerCase();
  return ['us', 'global', 'not_available'].includes(raw) ? raw : 'unspecified';
}

/** Sum every priced token category on one usage result. Pure. */
export function tokensOf(result) {
  let total = 0;
  for (const field of FLAT_TOKEN_FIELDS) {
    const n = Number(result?.[field] ?? 0);
    if (Number.isFinite(n)) total += Math.trunc(n);
  }
  const creation = result?.cache_creation;
  if (creation !== null && typeof creation === 'object' && !Array.isArray(creation)) {
    for (const field of NESTED_TOKEN_FIELDS) {
      const n = Number(creation[field] ?? 0);
      if (Number.isFinite(n)) total += Math.trunc(n);
    }
  }
  return total;
}

/** Sum priced tokens into {workspace_id: {geo: tokens}}. Pure. */
export function fold(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const workspace = String(result.workspace_id ?? 'default workspace');
        const geo = geoOf(result);
        if (!out[workspace]) out[workspace] = {};
        out[workspace][geo] = (out[workspace][geo] ?? 0) + tokensOf(result);
      }
    }
  }
  return out;
}

/** The share of priced tokens served on inference_geo us. Pure. */
export function usShare(geoTotals) {
  const values = Object.values(geoTotals ?? {}).map((v) => Number(v) || 0);
  const total = values.reduce((a, b) => a + b, 0);
  if (total <= 0) return 0;
  return (Number(geoTotals?.us) || 0) / total;
}

/**
 * Back the premium out of an amount that already contains it. Pure.
 *
 * NOT billed * share * 0.1. The billed figure is already 1.1x the base rate, so
 * the premium is (m - 1) / m of it, about 9.09%. Adding the multiplier on
 * instead of removing it overstates the saving by a tenth.
 */
export function premiumEstimate(billedDollars, share, multiplier = GEO_MULTIPLIER) {
  if (multiplier <= 1) return 0;
  const dollars = Math.max(0, Number(billedDollars ?? 0));
  const fraction = Math.min(1, Math.max(0, Number(share ?? 0)));
  return dollars * fraction * (multiplier - 1) / multiplier;
}

/**
 * A workspace's configured default inference geo. Pure. "unset" covers a
 * missing block and an unreadable one alike, because the repair is the same.
 */
export function residencyDefault(workspace) {
  const block = workspace?.data_residency;
  if (block === null || typeof block !== 'object' || Array.isArray(block)) return 'unset';
  const value = String(block.default_inference_geo ?? '').trim().toLowerCase();
  return ['us', 'global', 'not_available'].includes(value) ? value : 'unset';
}

/**
 * Classify one workspace. Pure. Returns [state, detail].
 * A workspace default and an explicit per-request parameter are kept apart:
 * the premium is identical, the owner of the fix is not.
 */
export function verdict(geoTotals, defaultGeo, minTokens = 1000000) {
  const totals = geoTotals ?? {};
  const total = Object.values(totals).reduce((a, b) => a + (Number(b) || 0), 0);
  if (total < minTokens) {
    return ['low-volume',
      `${total} priced token(s) in the window, too few to conclude anything`];
  }

  const us = Number(totals.us) || 0;
  if (us <= 0) {
    if ((Number(totals.not_available) || 0) >= total) {
      return ['geo-unsupported',
        `${(total / 1e6).toFixed(1)}M priced token(s), all on models that ` +
        'predate the inference_geo parameter. No premium and no lever.'];
    }
    return ['no-us-traffic',
      `${(total / 1e6).toFixed(1)}M priced token(s) and none of it on inference_geo us`];
  }

  const share = us / total;
  const shape = `${(share * 100).toFixed(0)}% of ${(total / 1e6).toFixed(1)}M ` +
                'priced token(s) on inference_geo us';

  if (defaultGeo === 'us') {
    return ['us-by-workspace-default',
      `${shape}; data_residency.default_inference_geo is us, so every caller ` +
      'pays the 1.1x whether or not any of them asked.'];
  }
  if (defaultGeo === 'global') {
    return ['us-by-request',
      `${shape} while the workspace default is global, so callers are setting ` +
      'inference_geo explicitly. The fix is in code, not in the workspace.'];
  }
  return ['us-unexplained',
    `${shape} with no readable data_residency default. Read the workspace ` +
    'before deciding whether this is deliberate.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
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

async function readPages(key, path, params) {
  const out = [];
  let next = { ...params };
  for (;;) {
    const page = await get(key, path, next);
    out.push(page);
    if (!page.has_more || !page.next_page) return out;
    next = { ...next, page: page.next_page };
  }
}

async function readWorkspaces(key) {
  const out = {};
  let params = { limit: 100, include_archived: 'true' };
  for (;;) {
    const page = await get(key, '/organizations/workspaces', params);
    for (const item of page.data ?? []) out[String(item.id)] = item;
    if (!page.has_more || !page.last_id) return out;
    params = { ...params, after_id: page.last_id };
  }
}

async function spendByWorkspace(key, start) {
  const out = {};
  for (const page of await readPages(key, '/organizations/cost_report',
    { starting_at: start, limit: 31, 'group_by[]': ['workspace_id'] })) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const workspace = String(result.workspace_id ?? 'default workspace');
        const value = Number(result.amount ?? 0);
        if (Number.isFinite(value)) out[workspace] = (out[workspace] ?? 0) + value;
      }
    }
  }
  return out;
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. */
function windowStart(days) {
  const midnight = new Date();
  midnight.setUTCHours(0, 0, 0, 0);
  midnight.setUTCDate(midnight.getUTCDate() - days);
  return midnight.toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const minTokens = Number(process.env.MIN_TOKENS ?? 1000000);
  const start = windowStart(days);

  const rows = fold(await readPages(key, '/organizations/usage_report/messages', {
    starting_at: start, bucket_width: '1d', limit: Math.min(days + 1, 31),
    'group_by[]': ['inference_geo', 'workspace_id'],
  }));
  const directory = await readWorkspaces(key);
  const spend = await spendByWorkspace(key, start);

  let checked = 0;
  let bad = 0;
  const ids = Object.keys(rows).sort((a, b) => (rows[b].us ?? 0) - (rows[a].us ?? 0));
  for (const workspace of ids) {
    const totals = rows[workspace];
    const defaultGeo = residencyDefault(directory[workspace]);
    const [state, detail] = verdict(totals, defaultGeo, minTokens);
    checked += 1;
    const line = `${state.padEnd(24)} ${workspace.padEnd(16)} ${detail}`;

    if (!FINDINGS.includes(state)) {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    const billed = spend[workspace] ?? 0;
    console.warn(`  estimated premium about ` +
      `$${premiumEstimate(billed, usShare(totals)).toFixed(2)} of ` +
      `$${billed.toFixed(2)} spend in this window, assuming a similar token ` +
      'mix across geos');
    const allowed = directory[workspace]?.data_residency?.allowed_inference_geos;
    if (allowed) console.warn(`  allowed_inference_geos: ${allowed.join(', ')}`);
    if (state === 'us-by-workspace-default') {
      console.warn('  repair: confirm which contract requires US residency, and ' +
                   'whether that traffic can live in its own workspace instead ' +
                   'of every workspace paying for it');
    } else if (state === 'us-by-request') {
      console.warn('  repair: the callers are setting inference_geo themselves. ' +
                   'Find them before changing anything here.');
    } else {
      console.warn("  repair: read this workspace's data_residency block and " +
                   'record why it is set the way it is');
    }
    console.warn('  do not change residency from a script: it is a compliance ' +
                 'setting with a named owner');
  }

  console.log(`${checked} workspace(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that earns its place is the arithmetic one: a billed figure already contains the multiplier, so the premium inside $1,100 is $100 and not $110, and getting that backwards inflates the number in the exact sentence somebody will repeat. After that the tests keep the three US states apart &mdash; workspace default, per-request parameter, unreadable configuration &mdash; and make sure a null geo does not quietly become <code>global</code> and a <code>not_available</code> workload does not get offered a lever it does not have.",
"test_py_file": "test_anthropic_inference_geo_premium_audit.py",
"test_py": '''from anthropic_inference_geo_premium_audit import (fold, geo_of,
                                                   premium_estimate,
                                                   residency_default, tokens_of,
                                                   us_share, verdict)


def result(geo="us", workspace="wrkspc_01Qy", uncached=100_000_000,
           output=8_000_000, cache_read=0, write_5m=0, write_1h=0):
    """One result from the messages usage report."""
    return {"inference_geo": geo, "workspace_id": workspace,
            "uncached_input_tokens": uncached, "output_tokens": output,
            "cache_read_input_tokens": cache_read,
            "cache_creation": {"ephemeral_5m_input_tokens": write_5m,
                               "ephemeral_1h_input_tokens": write_1h}}


def page(*results):
    return {"data": [{"starting_at": "2026-08-01T00:00:00Z",
                      "results": list(results)}], "has_more": False}


def test_the_premium_is_inside_the_billed_amount_not_added_to_it():
    # $1,100 billed at 1.1x is $1,000 of base rate and $100 of premium. The
    # tempting arithmetic, 1100 * 0.1, gives $110 and is wrong by a tenth.
    assert abs(premium_estimate(1100.0, 1.0) - 100.0) < 1e-6
    assert abs(premium_estimate(1100.0, 0.5) - 50.0) < 1e-6
    assert premium_estimate(1100.0, 0.0) == 0.0
    assert premium_estimate(0.0, 1.0) == 0.0
    # A multiplier of 1 is no premium at all, not a division by zero.
    assert premium_estimate(1100.0, 1.0, multiplier=1.0) == 0.0


def test_a_workspace_default_and_a_per_request_parameter_are_two_findings():
    totals = {"us": 400_000_000, "global": 8_000_000}
    assert verdict(totals, "us")[0] == "us-by-workspace-default"
    assert verdict(totals, "global")[0] == "us-by-request"
    assert verdict(totals, "unset")[0] == "us-unexplained"
    detail = verdict(totals, "us")[1]
    assert "98% of 408.0M priced token(s)" in detail


def test_models_that_predate_the_parameter_are_not_a_finding():
    assert verdict({"not_available": 50_000_000}, "unset")[0] == "geo-unsupported"
    assert verdict({"global": 50_000_000}, "us")[0] == "no-us-traffic"
    assert verdict({"us": 900}, "us")[0] == "low-volume"


def test_a_null_geo_is_unspecified_and_never_global():
    assert geo_of({"inference_geo": None}) == "unspecified"
    assert geo_of({}) == "unspecified"
    assert geo_of({"inference_geo": "US"}) == "us"
    assert geo_of({"inference_geo": "global"}) == "global"
    assert geo_of({"inference_geo": "not_available"}) == "not_available"


def test_every_priced_category_counts_including_the_nested_cache_writes():
    # The multiplier applies to cache writes and reads too, so a flat read that
    # misses cache_creation understates a heavily cached workspace.
    assert tokens_of(result(uncached=10, output=5, cache_read=3,
                            write_5m=2, write_1h=1)) == 21
    assert tokens_of({"uncached_input_tokens": 10, "cache_creation": None}) == 10
    assert tokens_of({}) == 0


def test_folding_keeps_workspaces_and_geos_apart():
    folded = fold([page(result(geo="us", uncached=400_000_000, output=0),
                        result(geo="global", uncached=8_000_000, output=0),
                        result(geo="us", workspace="wrkspc_02Zz",
                               uncached=1_000_000, output=0))])
    assert folded["wrkspc_01Qy"] == {"us": 400_000_000, "global": 8_000_000}
    assert folded["wrkspc_02Zz"] == {"us": 1_000_000}
    assert abs(us_share(folded["wrkspc_01Qy"]) - 400 / 408) < 1e-9
    assert us_share({}) == 0.0


def test_residency_is_read_from_the_nested_block():
    assert residency_default({"data_residency":
                              {"default_inference_geo": "us"}}) == "us"
    assert residency_default({"data_residency":
                              {"default_inference_geo": "global"}}) == "global"
    assert residency_default({"data_residency": {}}) == "unset"
    assert residency_default({}) == "unset"
    assert residency_default(None) == "unset"
''',
"test_js_file": "anthropic-inference-geo-premium-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fold, geoOf, premiumEstimate, residencyDefault, tokensOf, usShare,
         verdict } from './anthropic-inference-geo-premium-audit.mjs';

/** One result from the messages usage report. */
function result({ geo = 'us', workspace = 'wrkspc_01Qy', uncached = 100000000,
                  output = 8000000, cacheRead = 0, write5m = 0, write1h = 0 } = {}) {
  return {
    inference_geo: geo, workspace_id: workspace,
    uncached_input_tokens: uncached, output_tokens: output,
    cache_read_input_tokens: cacheRead,
    cache_creation: { ephemeral_5m_input_tokens: write5m,
                      ephemeral_1h_input_tokens: write1h },
  };
}

function page(...results) {
  return { data: [{ starting_at: '2026-08-01T00:00:00Z', results }], has_more: false };
}

test('the premium is inside the billed amount, not added to it', () => {
  assert.ok(Math.abs(premiumEstimate(1100.0, 1.0) - 100.0) < 1e-6);
  assert.ok(Math.abs(premiumEstimate(1100.0, 0.5) - 50.0) < 1e-6);
  assert.equal(premiumEstimate(1100.0, 0), 0);
  assert.equal(premiumEstimate(0, 1.0), 0);
  assert.equal(premiumEstimate(1100.0, 1.0, 1.0), 0);
});

test('a workspace default and a per-request parameter are two findings', () => {
  const totals = { us: 400000000, global: 8000000 };
  assert.equal(verdict(totals, 'us')[0], 'us-by-workspace-default');
  assert.equal(verdict(totals, 'global')[0], 'us-by-request');
  assert.equal(verdict(totals, 'unset')[0], 'us-unexplained');
  assert.match(verdict(totals, 'us')[1], /98% of 408\\.0M priced token\\(s\\)/);
});

test('models that predate the parameter are not a finding', () => {
  assert.equal(verdict({ not_available: 50000000 }, 'unset')[0], 'geo-unsupported');
  assert.equal(verdict({ global: 50000000 }, 'us')[0], 'no-us-traffic');
  assert.equal(verdict({ us: 900 }, 'us')[0], 'low-volume');
});

test('a null geo is unspecified and never global', () => {
  assert.equal(geoOf({ inference_geo: null }), 'unspecified');
  assert.equal(geoOf({}), 'unspecified');
  assert.equal(geoOf({ inference_geo: 'US' }), 'us');
  assert.equal(geoOf({ inference_geo: 'global' }), 'global');
  assert.equal(geoOf({ inference_geo: 'not_available' }), 'not_available');
});

test('every priced category counts, including the nested cache writes', () => {
  assert.equal(tokensOf(result({ uncached: 10, output: 5, cacheRead: 3,
                                 write5m: 2, write1h: 1 })), 21);
  assert.equal(tokensOf({ uncached_input_tokens: 10, cache_creation: null }), 10);
  assert.equal(tokensOf({}), 0);
});

test('folding keeps workspaces and geos apart', () => {
  const folded = fold([page(
    result({ geo: 'us', uncached: 400000000, output: 0 }),
    result({ geo: 'global', uncached: 8000000, output: 0 }),
    result({ geo: 'us', workspace: 'wrkspc_02Zz', uncached: 1000000, output: 0 }),
  )]);
  assert.deepEqual(folded.wrkspc_01Qy, { us: 400000000, global: 8000000 });
  assert.deepEqual(folded.wrkspc_02Zz, { us: 1000000 });
  assert.ok(Math.abs(usShare(folded.wrkspc_01Qy) - 400 / 408) < 1e-9);
  assert.equal(usShare({}), 0);
});

test('residency is read from the nested block', () => {
  assert.equal(residencyDefault({ data_residency: { default_inference_geo: 'us' } }), 'us');
  assert.equal(residencyDefault({ data_residency: { default_inference_geo: 'global' } }),
               'global');
  assert.equal(residencyDefault({ data_residency: {} }), 'unset');
  assert.equal(residencyDefault({}), 'unset');
  assert.equal(residencyDefault(null), 'unset');
});
''',
"faq": [
 ("Does the 1.1x apply to cached tokens too?",
  "Yes, to every token pricing category: input, output, cache writes and cache reads. That is why caching does not help you here. A cache read at 0.1x base becomes 0.11x base, which is proportionally exactly the same premium as everything else. Caching is still worth doing for its own reasons; it just does not touch this."),
 ("Why isn't the premium ten percent of the US spend?",
  "Because the US spend already includes it. If the base cost was $1,000, the billed figure is $1,100, and the premium inside that is $100 — which is 9.09% of $1,100, not 10%. Multiplying the billed amount by 0.1 gives $110 and overstates the saving by a tenth. It is a small error in a number people quote out loud, which is the worst kind."),
 ("What does not_available mean on the inference_geo field?",
  "That the model serving those requests predates the parameter. Models released before February 2026 do not support inference_geo at all, so that traffic pays no premium and has no geography lever to pull. The script reports it as its own state rather than folding it in with global, because a workload with nothing to change should not appear in a list of things you could change."),
 ("Should I just set everything back to global?",
  "No, and the script deliberately will not do it for you. Somebody chose US residency for a reason, and that reason may be a signed contract. The useful question is a scoping one: if one customer requires US inference and the workspace serves four hundred, the premium is being paid four hundred times over for one obligation, and a separate workspace for the regulated traffic satisfies the requirement at a fraction of the cost. That is a conversation, not a config change."),
 ("Is this the same thing as the service tier note?",
  "No. A service tier decides what capacity serves your requests and how quickly, and it fails by silently downgrading you to the standard tier. inference_geo decides where inference happens and multiplies the rate card by 1.1. Different setting, different failure, different fix — and the fast-mode note covers the tier side."),
],
"related": [REL_LONGCTX, REL_FAST_MODE, REL_OUTPUT_COST],
"citations": [CITE_AN_PRICING, CITE_AN_USAGE, CITE_AN_WORKSPACES, CITE_AN_COST],
},

{
"slug": "long-context-requests-unwatched",
"title": "Most of your input tokens sit in the 200k-1M band",
"description": "Group the Claude usage report by context_window. A growing 200k-1M share of uncached input is context bloat, not a price band, and compaction is the fix.",
"h1": "most of your input tokens sit in the 200k-1M band",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude context_window usage report", "anthropic 200k-1M context band",
             "claude long context pricing 1m", "anthropic context bloat agent loop",
             "claude context editing compaction"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only.",
"lead": "The agent keeps everything. That was the design: give it the whole ticket history, the whole document, every tool result it has ever produced in this session, and let it decide what matters. It worked beautifully in testing, where a session was four turns. In production a session is forty, each turn carries everything the previous thirty-nine produced, and the prefix has quietly grown to four hundred thousand tokens that get sent again from scratch every single time somebody types.",
"short_answer": """<p><code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=context_window&amp;group_by[]=model</code> with an <strong>Admin API key</strong>. <code>context_window</code> comes back as <code>"0-200k"</code>, <code>"200k-1M"</code> or null. Compute the <code>200k-1M</code> share of <code>uncached_input_tokens</code>, and read <code>cache_read_input_tokens</code> in the same results.</p>
<p>Now the part that has to be said before anything else: <strong>this is not a price band.</strong> On current models the 1M window is the default, no beta header is involved, and long-context requests bill at standard rates. The widespread belief that crossing 200k triggers premium pricing is out of date &mdash; it was true of a retired 1M-context beta and is not true now.</p>
<p>What the band actually measures is size. A large and growing <code>200k-1M</code> share means a prefix that grows every turn, and at $5 per million input tokens a 400k-token prefix is about $2 on every uncached call, before the model has said a word. The same growth degrades the answer as the window fills. Cache reads in that band are the difference between paying full rate for it and paying a tenth.</p>""",
"problem": """<p>The shape of this is unusual: the money is real, the alarm people expect is imaginary, and the correction usually goes the wrong way. Someone sees the <code>200k-1M</code> bucket, remembers hearing about long-context pricing, and either panics about a premium that no longer exists or &mdash; having checked and found there is no premium &mdash; concludes there is nothing to look at. Both readings miss it.</p>
<p>What is actually happening is that a conversation or an agent loop is resending a very large prefix on every turn. Each turn appends: the tool result, the retrieved document, the model's own last answer. Nothing removes anything, because nothing was ever written to remove anything. The prefix is a monotonic function of session length, and sessions in production are longer than sessions in testing, always.</p>
<p>The second cost is not on the invoice at all. Accuracy degrades as the window fills &mdash; the failure people have started calling context rot &mdash; so the same growth that is doubling the input bill is also making the answers worse. That is the version of this finding that gets a fix prioritised, and it is invisible to every cost dashboard by construction.</p>""",
"why": """<p><strong>The band is a size alarm, not a price alarm.</strong> Every model with a 1M-token context window defaults to it, no beta header is required, and tokens in the <code>200k-1M</code> band bill at standard rates. Reporting this finding as a pricing tier would be wrong, and it would also be the version a reader dismisses as soon as they check the pricing page.</p>
<p><strong>Standard rates on an enormous number is still an enormous number.</strong> At $5 per million input tokens, 400k tokens of prefix is $2 per uncached call. A thousand calls a day is $2,000 a day of input, all of it re-sending text the model has already seen. The size is the whole finding; the rate never had to be unusual.</p>
<p><strong>Cache reads change the severity, not the diagnosis.</strong> A long prefix that is cached is read back at 0.1x, which is a tenfold improvement and worth having. It does not shrink the context, so it does not touch the accuracy half of the problem at all. That is why this script grades a cached long-context workload as a note rather than a finding, and still says it out loud.</p>
<p><strong>A null <code>context_window</code> is not the short band.</strong> Some results come back unbanded. Counting them as <code>0-200k</code> deflates the long share and turns a real finding into a comfortable number, so the script keeps them separate and reports the share of banded traffic only.</p>
<p><strong>The repair is to remove context, not to buy a cheaper token.</strong> Server-side compaction and context editing shrink what gets resent; a <code>cache_control</code> breakpoint on the stable part makes what remains cheap. In that order, because caching a prefix that should not exist is optimising the wrong thing.</p>""",
"steps": [
 {"h": "Group by context_window and model",
  "body": """<p><code>group_by[]=context_window</code> and <code>group_by[]=model</code>, <code>bucket_width=1d</code>, <code>limit=31</code>, <code>starting_at</code> floored to midnight UTC. Grouping by model matters because one agent on a 1M-window model will otherwise be averaged against every ordinary chat request in the organization.</p>"""},
 {"h": "Keep unbanded traffic out of the denominator",
  "body": """<p>The field takes <code>"0-200k"</code>, <code>"200k-1M"</code> or null. The script maps null to <code>unbanded</code> and computes the long share against banded tokens only, then reports the unbanded volume separately. Folding nulls into the short band is the quiet way to make this finding disappear.</p>"""},
 {"h": "Read cache reads inside the same band",
  "body": """<p><code>cache_read_input_tokens</code> on the <code>200k-1M</code> results tells you whether the big prefix is being read back from cache or reprocessed from scratch. Large volume with near-zero reads is the expensive combination and the one worth waking someone for.</p>"""},
 {"h": "Price it at a rate you pass in",
  "body": """<p>The script takes the input rate per million tokens as an argument rather than shipping a price table that will be wrong in a quarter. Default it to the model you actually run. The output is a dollar figure for the uncached long-context input in the window, which is the number that makes compaction a scheduled piece of work rather than an idea.</p>"""},
 {"h": "Print compaction first, caching second",
  "body": """<p>Recommend server-side compaction or context editing for the routes generating 200k-plus prefixes, then a <code>cache_control</code> breakpoint on whatever stable portion remains. Both are application changes, both are printed, and the order matters: caching a prefix that should have been compacted away locks in the accuracy problem at a tenth of the price.</p>"""},
],
"verify": """<p>Add compaction, redeploy, and re-read the same grouping a week later. The <code>200k-1M</code> share of uncached input should fall; if it holds steady while total tokens fall, the sessions got shorter rather than the context getting smaller, which is not the same fix.</p>
<pre><code class="language-bash">python3 anthropic_long_context_audit.py --input-rate 5.0
# long-context-uncached  claude-opus-5  71% of banded uncached input is 200k-1M, with 2% of that band read from cache
#   408.0M uncached token(s) in the band, about $2040.00 at $5.00 per million
#   repair: compact or edit the context on the routes generating 200k+ prefixes, then cache what stays stable
# 3 model(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One usage read, GET, against <code>/v1/organizations/usage_report/messages</code>, so <code>ANTHROPIC_ADMIN_KEY</code> has to be an Admin key. Five pure functions, and the interesting one is the smallest: <code>band()</code> maps a null <code>context_window</code> to <code>unbanded</code> rather than to the short band, which is the difference between this check finding something and reassuring you. The rest fold the buckets per model and band, compute the long share against banded traffic only, compute the cached share inside the band, and price the uncached remainder at a rate you supply.",
"py_file": "anthropic_long_context_audit.py",
"py": '''"""Report Claude workloads whose input has grown into the 200k-1M band.

Read only. GET requests and nothing else: ANTHROPIC_ADMIN_KEY must be an Admin
API key (sk-ant-admin...), which can be provisioned read-only. A workspace key
is rejected by every /v1/organizations/* path.

This is a SIZE alarm and not a price alarm. On current models the 1M context
window is the default, no beta header is involved, and long-context requests
bill at standard rates. The old belief that crossing 200k triggers premium
pricing came from a retired beta and is not true now.

What the band measures is a prefix that grows every turn: expensive because it
is enormous at an ordinary rate, and inaccurate because the window fills. The
repair is compaction first and caching second, and it is printed, because both
are application changes.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_long_context_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

SHORT_BAND = "0-200k"
LONG_BAND = "200k-1M"
UNBANDED = "unbanded"

FINDINGS = ("long-context-uncached",)


def band(result):
    """Normalise the context_window value. Pure.

    A null becomes "unbanded", never "0-200k". Folding unbanded traffic into the
    short band deflates the long share and turns a real finding into a
    comfortable number, which is the one outcome this whole check exists to
    prevent.
    """
    raw = str((result or {}).get("context_window") or "").strip().lower()
    if raw == LONG_BAND.lower():
        return LONG_BAND
    if raw == SHORT_BAND.lower():
        return SHORT_BAND
    return UNBANDED


def fold(pages):
    """Sum input tokens into {model: {band: {uncached, cache_read}}}. Pure."""
    out = {}
    for page in pages:
        for bucket in page.get("data") or []:
            for result in bucket.get("results") or []:
                model = str(result.get("model") or "all models")
                where = band(result)
                row = out.setdefault(model, {}).setdefault(
                    where, {"uncached": 0, "cache_read": 0})
                for field, key in (("uncached_input_tokens", "uncached"),
                                   ("cache_read_input_tokens", "cache_read")):
                    try:
                        row[key] += int(result.get(field) or 0)
                    except (TypeError, ValueError):
                        pass
    return out


def long_share(model_rows):
    """Share of BANDED uncached input sitting in the 200k-1M band. Pure.

    Banded only. Unbanded traffic cannot be placed on either side, and putting
    it in the denominator would make a workload look shorter than it is purely
    because the report declined to classify some of it.
    """
    rows = model_rows or {}
    short = int((rows.get(SHORT_BAND) or {}).get("uncached") or 0)
    long_ = int((rows.get(LONG_BAND) or {}).get("uncached") or 0)
    banded = short + long_
    if banded <= 0:
        return 0.0
    return long_ / float(banded)


def cached_share(row):
    """Share of a band's input that was read back from cache. Pure.

    Grades severity, not diagnosis: a cached long prefix costs a tenth as much
    and is exactly as long, so it fixes the money and none of the accuracy.
    """
    data = row or {}
    reads = int(data.get("cache_read") or 0)
    uncached = int(data.get("uncached") or 0)
    total = reads + uncached
    if total <= 0:
        return 0.0
    return reads / float(total)


def uncached_cost(tokens, rate_per_mtok):
    """Dollars for a number of uncached input tokens. Pure.

    The rate is passed in rather than baked into a table. A price table in an
    audit script is a fact with an expiry date on it, and nothing warns you the
    day it passes.
    """
    if rate_per_mtok < 0:
        raise ValueError("rate_per_mtok must not be negative")
    return max(0, int(tokens or 0)) / 1e6 * float(rate_per_mtok)


def verdict(model_rows, min_tokens=10_000_000, long_threshold=0.25,
            cache_floor=0.30):
    """Classify one model's context profile. Pure. Returns (state, detail)."""
    rows = model_rows or {}
    banded = sum(int((rows.get(b) or {}).get("uncached") or 0)
                 for b in (SHORT_BAND, LONG_BAND))
    unbanded = int((rows.get(UNBANDED) or {}).get("uncached") or 0)
    total = banded + unbanded

    if total < min_tokens:
        return ("low-volume",
                "%d uncached input token(s) in the window, too few to conclude "
                "anything" % total)
    if banded <= 0:
        return ("unbanded-only",
                "%.1fM uncached input token(s) with no context_window on any "
                "result, so this traffic cannot be placed in a band at all"
                % (unbanded / 1e6))

    share = long_share(rows)
    long_row = rows.get(LONG_BAND) or {}
    cached = cached_share(long_row)
    shape = ("%.0f%% of banded uncached input is %s, with %.0f%% of that band "
             "read from cache" % (share * 100, LONG_BAND, cached * 100))

    if share < long_threshold:
        return ("short-context",
                "%s. The prefix is not where the money is going here." % shape)
    if cached >= cache_floor:
        return ("long-context-cached",
                "%s. The big prefix is being read back rather than reprocessed, "
                "so it costs a tenth of full rate. It is still just as long, "
                "and length is what degrades the answer." % shape)
    return ("long-context-uncached",
            "%s. A very large prefix reprocessed from scratch on every call. "
            "Standard rates, extraordinary volume." % shape)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk the paginated usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days):
    """Floor to midnight UTC: starting_at must sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily buckets to read (default 30)")
    ap.add_argument("--input-rate", type=float, default=5.0,
                    help="dollars per million uncached input tokens, for the "
                         "printed estimate only (default 5.0)")
    ap.add_argument("--min-tokens", type=int, default=10_000_000,
                    help="uncached input tokens below which no claim is made")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    rows = fold(pages(s, "/organizations/usage_report/messages",
                      {"starting_at": window_start(args.days),
                       "bucket_width": "1d", "limit": min(args.days + 1, 31),
                       "group_by[]": ["context_window", "model"]}))

    checked = 0
    bad = 0
    for model in sorted(rows, key=lambda m: -((rows[m].get(LONG_BAND) or {})
                                              .get("uncached") or 0)):
        state, detail = verdict(rows[model], args.min_tokens)
        checked += 1
        line = "%-22s %-22s %s" % (state, model, detail)

        if state == "long-context-cached":
            log.warning(line)
            log.warning("  note: caching fixed the price and not the length. "
                        "Compaction is still the lever for answer quality.")
            continue
        if state not in FINDINGS:
            log.info(line)
            continue

        bad += 1
        log.warning(line)
        tokens = (rows[model].get(LONG_BAND) or {}).get("uncached") or 0
        log.warning("  %.1fM uncached token(s) in the band, about $%.2f at "
                    "$%.2f per million", tokens / 1e6,
                    uncached_cost(tokens, args.input_rate), args.input_rate)
        log.warning("  repair: compact or edit the context on the routes "
                    "generating 200k+ prefixes, then put a cache_control "
                    "breakpoint on whatever stays stable. In that order.")
        log.warning("  note: this band is not a premium price tier. It is "
                    "standard rates on a very large number of tokens.")

    unbanded = sum((rows[m].get(UNBANDED) or {}).get("uncached") or 0 for m in rows)
    if unbanded:
        log.info("%.1fM uncached token(s) carried no context_window and were "
                 "excluded from every share above", unbanded / 1e6)

    log.info("%d model(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-long-context-audit.mjs",
"js": '''/**
 * Report Claude workloads whose input has grown into the 200k-1M band.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path.
 *
 * A SIZE alarm and not a price alarm. On current models the 1M window is the
 * default, no beta header is involved, and long-context requests bill at
 * standard rates. What the band measures is a prefix that grows every turn.
 * The repair is compaction first, caching second, and it is printed.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const SHORT_BAND = '0-200k';
const LONG_BAND = '200k-1M';
const UNBANDED = 'unbanded';

const FINDINGS = ['long-context-uncached'];

/**
 * Normalise the context_window value. Pure.
 * A null becomes "unbanded", never "0-200k": folding unbanded traffic into the
 * short band deflates the long share and turns a real finding into a
 * comfortable number.
 */
export function band(result) {
  const raw = String(result?.context_window ?? '').trim().toLowerCase();
  if (raw === LONG_BAND.toLowerCase()) return LONG_BAND;
  if (raw === SHORT_BAND.toLowerCase()) return SHORT_BAND;
  return UNBANDED;
}

/** Sum input tokens into {model: {band: {uncached, cache_read}}}. Pure. */
export function fold(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page.data ?? []) {
      for (const result of bucket.results ?? []) {
        const model = String(result.model ?? 'all models');
        const where = band(result);
        if (!out[model]) out[model] = {};
        if (!out[model][where]) out[model][where] = { uncached: 0, cache_read: 0 };
        const row = out[model][where];
        for (const [field, key] of [['uncached_input_tokens', 'uncached'],
                                    ['cache_read_input_tokens', 'cache_read']]) {
          const n = Number(result[field] ?? 0);
          if (Number.isFinite(n)) row[key] += Math.trunc(n);
        }
      }
    }
  }
  return out;
}

/**
 * Share of BANDED uncached input sitting in the 200k-1M band. Pure.
 * Banded only: unbanded traffic cannot be placed on either side, and putting it
 * in the denominator makes a workload look shorter than it is.
 */
export function longShare(modelRows) {
  const rows = modelRows ?? {};
  const short = Number(rows[SHORT_BAND]?.uncached ?? 0) || 0;
  const long = Number(rows[LONG_BAND]?.uncached ?? 0) || 0;
  const banded = short + long;
  if (banded <= 0) return 0;
  return long / banded;
}

/**
 * Share of a band's input read back from cache. Pure. Grades severity, not
 * diagnosis: a cached long prefix costs a tenth and is exactly as long.
 */
export function cachedShare(row) {
  const reads = Number(row?.cache_read ?? 0) || 0;
  const uncached = Number(row?.uncached ?? 0) || 0;
  const total = reads + uncached;
  if (total <= 0) return 0;
  return reads / total;
}

/**
 * Dollars for a number of uncached input tokens. Pure. The rate is passed in
 * rather than baked into a table: a price table in an audit script is a fact
 * with an expiry date and nothing warns you the day it passes.
 */
export function uncachedCost(tokens, ratePerMtok) {
  if (ratePerMtok < 0) throw new Error('ratePerMtok must not be negative');
  return Math.max(0, Math.trunc(Number(tokens ?? 0))) / 1e6 * Number(ratePerMtok);
}

/** Classify one model's context profile. Pure. Returns [state, detail]. */
export function verdict(modelRows, minTokens = 10000000, longThreshold = 0.25,
                        cacheFloor = 0.30) {
  const rows = modelRows ?? {};
  const banded = [SHORT_BAND, LONG_BAND]
    .reduce((a, b) => a + (Number(rows[b]?.uncached ?? 0) || 0), 0);
  const unbanded = Number(rows[UNBANDED]?.uncached ?? 0) || 0;
  const total = banded + unbanded;

  if (total < minTokens) {
    return ['low-volume',
      `${total} uncached input token(s) in the window, too few to conclude anything`];
  }
  if (banded <= 0) {
    return ['unbanded-only',
      `${(unbanded / 1e6).toFixed(1)}M uncached input token(s) with no ` +
      'context_window on any result, so this traffic cannot be placed in a band at all'];
  }

  const share = longShare(rows);
  const cached = cachedShare(rows[LONG_BAND]);
  const shape = `${(share * 100).toFixed(0)}% of banded uncached input is ` +
                `${LONG_BAND}, with ${(cached * 100).toFixed(0)}% of that band ` +
                'read from cache';

  if (share < longThreshold) {
    return ['short-context',
      `${shape}. The prefix is not where the money is going here.`];
  }
  if (cached >= cacheFloor) {
    return ['long-context-cached',
      `${shape}. The big prefix is being read back rather than reprocessed, so ` +
      'it costs a tenth of full rate. It is still just as long, and length is ' +
      'what degrades the answer.'];
  }
  return ['long-context-uncached',
    `${shape}. A very large prefix reprocessed from scratch on every call. ` +
    'Standard rates, extraordinary volume.'];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
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

async function readPages(key, path, params) {
  const out = [];
  let next = { ...params };
  for (;;) {
    const page = await get(key, path, next);
    out.push(page);
    if (!page.has_more || !page.next_page) return out;
    next = { ...next, page: page.next_page };
  }
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. */
function windowStart(days) {
  const midnight = new Date();
  midnight.setUTCHours(0, 0, 0, 0);
  midnight.setUTCDate(midnight.getUTCDate() - days);
  return midnight.toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const inputRate = Number(process.env.INPUT_RATE ?? 5.0);
  const minTokens = Number(process.env.MIN_TOKENS ?? 10000000);

  const rows = fold(await readPages(key, '/organizations/usage_report/messages', {
    starting_at: windowStart(days), bucket_width: '1d',
    limit: Math.min(days + 1, 31),
    'group_by[]': ['context_window', 'model'],
  }));

  let checked = 0;
  let bad = 0;
  const models = Object.keys(rows).sort(
    (a, b) => (rows[b][LONG_BAND]?.uncached ?? 0) - (rows[a][LONG_BAND]?.uncached ?? 0));
  for (const model of models) {
    const [state, detail] = verdict(rows[model], minTokens);
    checked += 1;
    const line = `${state.padEnd(22)} ${model.padEnd(22)} ${detail}`;

    if (state === 'long-context-cached') {
      console.warn(line);
      console.warn('  note: caching fixed the price and not the length. ' +
                   'Compaction is still the lever for answer quality.');
      continue;
    }
    if (!FINDINGS.includes(state)) {
      console.log(line);
      continue;
    }

    bad += 1;
    console.warn(line);
    const tokens = rows[model][LONG_BAND]?.uncached ?? 0;
    console.warn(`  ${(tokens / 1e6).toFixed(1)}M uncached token(s) in the band, ` +
                 `about $${uncachedCost(tokens, inputRate).toFixed(2)} at ` +
                 `$${inputRate.toFixed(2)} per million`);
    console.warn('  repair: compact or edit the context on the routes generating ' +
                 '200k+ prefixes, then put a cache_control breakpoint on whatever ' +
                 'stays stable. In that order.');
    console.warn('  note: this band is not a premium price tier. It is standard ' +
                 'rates on a very large number of tokens.');
  }

  const unbanded = Object.values(rows)
    .reduce((a, r) => a + (r[UNBANDED]?.uncached ?? 0), 0);
  if (unbanded) {
    console.log(`${(unbanded / 1e6).toFixed(1)}M uncached token(s) carried no ` +
                'context_window and were excluded from every share above');
  }

  console.log(`${checked} model(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two tests carry the note. The first is that a null <code>context_window</code> becomes <code>unbanded</code> and stays out of the denominator &mdash; treat it as short traffic and a 71% long share reads as 41%, which is the difference between an investigation and a shrug. The second is that a heavily cached long-context workload is a different state from an uncached one, with a different sentence attached, because caching fixes the price and leaves the length exactly where it was.",
"test_py_file": "test_anthropic_long_context_audit.py",
"test_py": '''from anthropic_long_context_audit import (band, cached_share, fold,
                                           long_share, uncached_cost, verdict)


def result(window="200k-1M", model="claude-opus-5", uncached=400_000_000,
           cache_read=0):
    """One result from the messages usage report."""
    return {"context_window": window, "model": model,
            "uncached_input_tokens": uncached,
            "cache_read_input_tokens": cache_read}


def page(*results):
    return {"data": [{"starting_at": "2026-08-01T00:00:00Z",
                      "results": list(results)}], "has_more": False}


def rows(long_uncached=400_000_000, long_read=0, short_uncached=160_000_000,
         unbanded=0):
    """A folded model row shaped like fold() returns them."""
    out = {"200k-1M": {"uncached": long_uncached, "cache_read": long_read},
           "0-200k": {"uncached": short_uncached, "cache_read": 0}}
    if unbanded:
        out["unbanded"] = {"uncached": unbanded, "cache_read": 0}
    return out


def test_a_null_context_window_is_unbanded_and_not_the_short_band():
    # The load-bearing one. 400M long against 160M short is 71%. Counting a
    # further 400M of unbanded traffic as short would report 41% and nothing
    # would ever be looked at.
    assert band({"context_window": None}) == "unbanded"
    assert band({}) == "unbanded"
    assert band({"context_window": "200k-1M"}) == "200k-1M"
    assert band({"context_window": "0-200k"}) == "0-200k"
    with_nulls = rows(unbanded=400_000_000)
    assert abs(long_share(with_nulls) - 400 / 560) < 1e-9
    state, detail = verdict(with_nulls)
    assert state == "long-context-uncached"
    assert "71% of banded uncached input" in detail


def test_a_cached_long_prefix_is_a_different_state_with_a_different_sentence():
    state, detail = verdict(rows(long_uncached=40_000_000,
                                 long_read=360_000_000,
                                 short_uncached=10_000_000))
    assert state == "long-context-cached"
    assert "It is still just as long" in detail


def test_a_short_context_workload_is_not_a_finding():
    assert verdict(rows(long_uncached=10_000_000,
                        short_uncached=400_000_000))[0] == "short-context"
    assert verdict(rows(long_uncached=100, short_uncached=100))[0] == "low-volume"


def test_traffic_the_report_never_banded_is_reported_as_such():
    state, detail = verdict({"unbanded": {"uncached": 400_000_000, "cache_read": 0}})
    assert state == "unbanded-only"
    assert "cannot be placed in a band" in detail


def test_the_cached_share_is_read_inside_the_band():
    assert cached_share({"uncached": 0, "cache_read": 100}) == 1.0
    assert cached_share({"uncached": 100, "cache_read": 0}) == 0.0
    assert cached_share({"uncached": 50, "cache_read": 50}) == 0.5
    assert cached_share({}) == 0.0


def test_the_rate_is_supplied_rather_than_baked_in():
    # 408M uncached input tokens at $5 per million.
    assert uncached_cost(408_000_000, 5.0) == 2040.0
    assert uncached_cost(0, 5.0) == 0.0
    assert uncached_cost(1_000_000, 0.0) == 0.0


def test_folding_keeps_models_and_bands_apart():
    folded = fold([page(result(window="200k-1M", uncached=200_000_000),
                        result(window="200k-1M", uncached=200_000_000,
                               cache_read=5_000_000),
                        result(window="0-200k", uncached=160_000_000),
                        result(window=None, model="claude-haiku-4-5-20251001",
                               uncached=9_000_000))])
    assert folded["claude-opus-5"]["200k-1M"]["uncached"] == 400_000_000
    assert folded["claude-opus-5"]["200k-1M"]["cache_read"] == 5_000_000
    assert folded["claude-opus-5"]["0-200k"]["uncached"] == 160_000_000
    assert folded["claude-haiku-4-5-20251001"]["unbanded"]["uncached"] == 9_000_000
''',
"test_js_file": "anthropic-long-context-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { band, cachedShare, fold, longShare, uncachedCost, verdict }
  from './anthropic-long-context-audit.mjs';

/** One result from the messages usage report. */
function result({ window = '200k-1M', model = 'claude-opus-5',
                  uncached = 400000000, cacheRead = 0 } = {}) {
  return {
    context_window: window, model,
    uncached_input_tokens: uncached, cache_read_input_tokens: cacheRead,
  };
}

function page(...results) {
  return { data: [{ starting_at: '2026-08-01T00:00:00Z', results }], has_more: false };
}

/** A folded model row shaped like fold() returns them. */
function rows({ longUncached = 400000000, longRead = 0,
                shortUncached = 160000000, unbanded = 0 } = {}) {
  const out = {
    '200k-1M': { uncached: longUncached, cache_read: longRead },
    '0-200k': { uncached: shortUncached, cache_read: 0 },
  };
  if (unbanded) out.unbanded = { uncached: unbanded, cache_read: 0 };
  return out;
}

test('a null context_window is unbanded and not the short band', () => {
  assert.equal(band({ context_window: null }), 'unbanded');
  assert.equal(band({}), 'unbanded');
  assert.equal(band({ context_window: '200k-1M' }), '200k-1M');
  assert.equal(band({ context_window: '0-200k' }), '0-200k');
  const withNulls = rows({ unbanded: 400000000 });
  assert.ok(Math.abs(longShare(withNulls) - 400 / 560) < 1e-9);
  const [state, detail] = verdict(withNulls);
  assert.equal(state, 'long-context-uncached');
  assert.match(detail, /71% of banded uncached input/);
});

test('a cached long prefix is a different state with a different sentence', () => {
  const [state, detail] = verdict(rows({ longUncached: 40000000,
                                         longRead: 360000000,
                                         shortUncached: 10000000 }));
  assert.equal(state, 'long-context-cached');
  assert.match(detail, /It is still just as long/);
});

test('a short context workload is not a finding', () => {
  assert.equal(verdict(rows({ longUncached: 10000000, shortUncached: 400000000 }))[0],
               'short-context');
  assert.equal(verdict(rows({ longUncached: 100, shortUncached: 100 }))[0], 'low-volume');
});

test('traffic the report never banded is reported as such', () => {
  const [state, detail] = verdict({ unbanded: { uncached: 400000000, cache_read: 0 } });
  assert.equal(state, 'unbanded-only');
  assert.match(detail, /cannot be placed in a band/);
});

test('the cached share is read inside the band', () => {
  assert.equal(cachedShare({ uncached: 0, cache_read: 100 }), 1);
  assert.equal(cachedShare({ uncached: 100, cache_read: 0 }), 0);
  assert.equal(cachedShare({ uncached: 50, cache_read: 50 }), 0.5);
  assert.equal(cachedShare({}), 0);
});

test('the rate is supplied rather than baked in', () => {
  assert.equal(uncachedCost(408000000, 5.0), 2040);
  assert.equal(uncachedCost(0, 5.0), 0);
  assert.equal(uncachedCost(1000000, 0), 0);
});

test('folding keeps models and bands apart', () => {
  const folded = fold([page(
    result({ window: '200k-1M', uncached: 200000000 }),
    result({ window: '200k-1M', uncached: 200000000, cacheRead: 5000000 }),
    result({ window: '0-200k', uncached: 160000000 }),
    result({ window: null, model: 'claude-haiku-4-5-20251001', uncached: 9000000 }),
  )]);
  assert.equal(folded['claude-opus-5']['200k-1M'].uncached, 400000000);
  assert.equal(folded['claude-opus-5']['200k-1M'].cache_read, 5000000);
  assert.equal(folded['claude-opus-5']['0-200k'].uncached, 160000000);
  assert.equal(folded['claude-haiku-4-5-20251001'].unbanded.uncached, 9000000);
});
''',
"faq": [
 ("Doesn't crossing 200k tokens trigger premium pricing?",
  "Not on current models. Every model with a 1M-token context window defaults to it, no beta header is required, and tokens in the 200k-1M band bill at standard rates. The belief comes from a retired 1M-context beta that did carry a premium, and it is worth correcting explicitly, because both wrong readings of it are harmful: panic about a price tier that no longer exists, or relief that leads to ignoring a real and growing bill."),
 ("Then why should I care about the band at all?",
  "Because standard rates on an enormous number is still an enormous number. At $5 per million input tokens, a 400k-token prefix is about $2 on every uncached call. A thousand calls a day is $2,000 a day, spent re-sending text the model already saw. And the second cost is not financial: accuracy degrades as the window fills, so the same growth that doubles the bill is also making the answers worse."),
 ("Is this just the prompt caching note again?",
  "No, and the script keeps them apart deliberately. The caching notes ask whether caching is switched on and whether it earns back what it costs. This one asks how big the prefix is. A workload with excellent caching can still be growing its context every turn — it pays a tenth of the rate for it, which is a real saving, and it keeps the entire accuracy problem. Cache reads grade the severity here; they do not resolve the finding."),
 ("What does compaction actually mean in practice?",
  "Summarising or dropping the parts of the conversation that are no longer load-bearing before the next turn is sent, rather than appending forever. Context editing does the same thing to tool results, which are usually the largest and most disposable part of an agent's history. Both are application changes, both are dull to build, and both attack the size rather than the price of it — which is why the script prints them ahead of the cache_control suggestion."),
 ("Some of my results have no context_window. What does that mean?",
  "That the report did not band that traffic, which is a third answer rather than a small one. The script maps it to unbanded, keeps it out of the share denominator, and prints the volume separately. Counting it as 0-200k would be the easy choice and the wrong one: it deflates the long share, and a finding that quietly disappears is worse than one that never ran."),
],
"related": [REL_CACHE_NEVER, REL_CACHE_WRITES, REL_GEO],
"citations": [CITE_AN_CONTEXT, CITE_AN_USAGE, CITE_AN_PRICING, CITE_AN_CACHING],
},

]
