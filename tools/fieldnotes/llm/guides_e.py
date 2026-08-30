#!/usr/bin/env python3
"""/llm/ field notes, batch E — the writing.

Four notes that all end up looking at money, and four different questions.

`fast-mode-silently-downgraded` is a mismatch. It never asks whether the bill is
large; it asks whether the tier you configured is the tier you were billed for,
and both directions of the disagreement are findings — a project set to Fast
whose spend lands on standard line items is being downgraded, and a project set
to Standard whose spend carries Fast line items has a code path sending the
parameter nobody budgeted for.

`streaming-usage-lost` is a reconciliation, and it is the only script in the
section that takes your numbers as input. The finding is not that spend moved.
It is that your own record of it is wrong: streamed responses report `usage:
null` on every chunk unless you asked for the totals, so a dashboard built on
per-request telemetry is short by whatever share of your traffic streams.

`spend-spike-week-over-week` is a derivative. Eight weeks of daily cost folded
into whole weeks, and the answer is the *shape* of the change: a spike that came
back down, a step that did not, or a ramp that has been climbing all along. The
three want different people looking at them, so the script refuses to print one
sentence for all three.

`one-model-or-project-dominates-cost` is a distribution at a single moment. No
clock at all: rank the line items and the projects by share of one window, and
name the one row worth working on. Concentration is the normal shape of an LLM
bill, which is exactly why nobody measures it.

Read-only throughout: an organization admin key provisioned read-only for the
three OpenAI notes, an Admin API key for the Anthropic half of the spend-change
one, GET requests only, and every repair printed for a human to run. A key that
can reach these endpoints can also spend money on inference, so none of these
scripts writes anything.
"""

CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_USAGE_COMPLETIONS = ("Usage: completions — OpenAI API reference",
                          "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_ADMIN = ("Admin APIs — OpenAI developer docs",
              "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_FAST = ("Fast mode — OpenAI developer docs",
             "https://developers.openai.com/api/docs/guides/fast-mode")
CITE_PRIORITY = ("API priority processing — OpenAI",
                 "https://openai.com/api-priority-processing/")
CITE_STREAMING = ("Streaming responses — OpenAI developer docs",
                  "https://developers.openai.com/api/docs/guides/streaming-responses")
CITE_USAGE_COOKBOOK = ("Completions usage API — OpenAI Cookbook",
                       "https://developers.openai.com/cookbook/examples/completions_usage_api")
CITE_PY_API = ("openai-python API surface — GitHub",
               "https://github.com/openai/openai-python/blob/main/api.md")
CITE_AN_COST_REPORT = ("Get cost report — Claude Docs",
                       "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report")
CITE_AN_USAGE_COST = ("Usage and cost API — Claude Docs",
                      "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")

REL_FAST = ("/llm/fast-mode-silently-downgraded/",
            "A premium tier billed but not delivered")
REL_STREAM = ("/llm/streaming-usage-lost/",
              "Streamed tokens the dashboard never recorded")
REL_SPIKE = ("/llm/spend-spike-week-over-week/",
             "Spend that moved and the week it moved in")
REL_DOM = ("/llm/one-model-or-project-dominates-cost/",
           "The one line item most of the bill is made of")
REL_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                   "Nothing stops a runaway once it starts")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")
REL_REASONING = ("/llm/reasoning-tokens-billed-invisibly/",
                 "Tokens billed as output and never returned")

GUIDES = [

{
"slug": "fast-mode-silently-downgraded",
"title": "Fast mode billed at twice the rate and served as default",
"description": "The tier you request and the tier you are served are different fields. Read the project setting against the invoice: both directions of the mismatch cost money.",
"h1": "fast mode billed at twice the rate and served as default",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai service_tier fast", "openai fast mode downgraded",
             "openai priority processing cost", "project service tier openai",
             "service_tier default instead of fast"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because /v1/organization/* rejects a project key.",
"lead": "Somebody turned on Fast mode for the checkout assistant eight months ago, in the console, in an afternoon nobody wrote down. The latency graph looked better for a week. It does not look better now, and the team has spent two sprints on the retrieval step trying to work out why. The requests still carry the premium tier, the responses still return <code>200</code>, and the field that says which tier actually served them is not the field anyone is logging.",
"short_answer": """<p>Two GETs with an <strong>organization admin key</strong>. <code>GET /v1/organization/projects?limit=100</code> tells you which projects are configured for the premium tier. <code>GET /v1/organization/costs?start_time={now-30d}&amp;bucket_width=1d&amp;limit=30&amp;group_by=line_item&amp;group_by=project_id</code> tells you which tier the invoice says served them.</p>
<p>Then compare the two, in both directions. A project set to Fast whose spend sits on standard line items is being <em>downgraded</em>: the ramp limits tripped, you are getting default latency, and the speedup the team is planning around is not there. A project set to Standard carrying Fast or Priority line items is the mirror image: some code path is sending the parameter, and that traffic bills at twice the rate.</p>
<p>The reason this survives is that the request field and the response field have the same name and different meanings. <code>service_tier</code> in the body is what you asked for. <code>service_tier</code> in the response is what you got. Nothing raises when they differ, and almost nobody logs the second one.</p>""",
"problem": """<p>It fails in the shape that is hardest to notice: everything keeps working. The requests succeed, the answers are fine, and the only thing that changed is a latency distribution that drifted back to where it was before anyone paid to move it. Two sprints of profiling later, the retrieval step is faster and the p95 is not, because the premium was never the thing being delivered.</p>
<p>The other direction is worse in dollars and quieter still. A project defaulted to the premium tier bills every request at twice the standard rate with no code change anywhere in the tree, no diff to review, and no line in a changelog. On GPT-5.6 Sol that is $8 per million input tokens instead of $4, and $40 per million output instead of $20. It is a checkbox in a console, and it is the only evidence that exists.</p>""",
"why": """<p><strong>The requested tier and the served tier are separate fields.</strong> You send <code>service_tier</code> and the response returns <code>service_tier</code>, and the API is under no obligation to make them equal. It reports what served the request. Every logging setup that records the request body and not the response envelope is blind to the difference by construction.</p>
<p><strong>Downgrades are a documented behaviour, not an error.</strong> Fast mode carries ramp rate limits, and when they trigger the request is served on the default tier instead of failing. That is the right behaviour — a 429 would be worse — but it means the fallback is silent, and a fallback nobody can see is a fallback nobody manages.</p>
<p><strong>The premium is real in both directions.</strong> Fast mode is priced at twice the standard rate for GPT-5.6 Sol: $8/$40 per million tokens short-context against $4/$20, and $16/$60 against $8/$30 long-context. If you are served the premium you pay for it. If you are downgraded you do not pay it, and you also do not get it, which is the case the latency work is chasing.</p>
<p><strong>A project-level default needs no code at all.</strong> The Project Service Tier setting applies to every request the project makes, whether or not the request body mentions a tier. That is why the audit has to read the project object: grepping your source for <code>service_tier</code> can return nothing while every request you send is billing at 2x.</p>
<p><strong>The line item is a label, not an enum.</strong> The cost report's <code>line_item</code> is a human-readable string such as <code>"gpt-5.6-sol, input"</code>. Premium traffic is identifiable in it, but by substring rather than by a documented field, so a script that reads it should print the strings it matched rather than asking you to trust the match.</p>""",
"steps": [
 {"h": "Get an organization admin key, provisioned read-only",
  "body": """<p>Both calls live under <code>/v1/organization/*</code>, which rejects project keys outright. Use an <code>sk-admin-</code> key with read scopes. This script only issues GETs.</p>"""},
 {"h": "Read the configured tier off the project objects",
  "body": """<p><code>GET /v1/organization/projects?limit=100</code>, paginating on <code>after</code>. The Project Service Tier setting is the one place a premium can be switched on for every request in a project without a single line of code changing, which makes it the first thing to read and the last thing anyone remembers.</p>"""},
 {"h": "Split each project's spend into premium and standard line items",
  "body": """<p><code>GET /v1/organization/costs?bucket_width=1d&amp;limit=30&amp;group_by=line_item&amp;group_by=project_id</code>. Grouping is what populates <code>line_item</code> and <code>project_id</code> at all &mdash; ungrouped, both come back <code>null</code>. Sum <code>amount.value</code> per project into the two halves.</p>"""},
 {"h": "Compare the two and keep both mismatches apart",
  "body": """<p>Fast configured with standard spend is a downgrade and costs you latency. Standard configured with premium spend is an unbudgeted 2x and costs you money. They are opposite findings with opposite repairs, so a script that prints one sentence for both is not much use.</p>"""},
 {"h": "Then log the served tier, not the requested one",
  "body": """<p>The permanent fix is one line in your client: record the <code>service_tier</code> from the response envelope alongside the model and the token counts. Once that is in your telemetry the downgrade rate is a number you watch rather than a thing you audit for, and this script becomes a monthly check on the project settings instead.</p>"""},
],
"verify": """<p>Re-run after the project setting has been changed or the parameter dropped. The mismatch should be gone; the tier and the invoice should say the same thing.</p>
<pre><code class="language-bash">python3 openai_fast_mode_tier_audit.py --days 30
# standard          proj_batch (nightly enrichment)  tier is standard and no premium line items
# 4 project(s) checked, 0 with a tier the invoice disagrees with</code></pre>""",
"code_intro": "Two GETs against the organization endpoints, no writes, and an admin key that should be provisioned read-only. Four pure functions: the tier reader, which is deliberately lenient because a setting that is absent from the object is not the same as a setting that is off; the spend splitter, which keeps the matched line-item strings so the report can show its working; the override parser, for the case where the project object does not carry the field at all; and the classifier, which has to hold two opposite findings apart rather than reporting “mismatch” and leaving you to work out which one you have.",
"py_file": "openai_fast_mode_tier_audit.py",
"py": '''"""Report OpenAI projects whose configured service tier and invoice disagree.

Read only. Two GET requests against the organization endpoints and nothing
else. Those endpoints reject project keys, so this needs an organization admin
key (sk-admin-), which can and should be provisioned read-only.

The finding is a mismatch rather than a total. A project set to the premium tier
whose spend lands on standard line items is being downgraded and is not getting
what it configured; a project set to standard carrying premium line items has a
code path sending the parameter. Both are printed with the repair, and neither
repair is performed here.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_fast_mode_tier_audit")

API = "https://api.openai.com/v1"

# Fast mode is priced at twice the standard rate. The multiplier is here to
# describe the finding, not to price your traffic: the dollars come from the
# cost report, which does not go stale the way a typed-in price table does.
PREMIUM_MULTIPLIER = 2.0

# line_item is a human-readable label, not a documented enum, so premium traffic
# is matched by substring and every matched string is printed for you to check.
PREMIUM_WORDS = ("fast", "priority")

# What the project object calls the setting the console calls Project Service
# Tier. Read leniently and in this order; absent is reported as absent.
TIER_FIELDS = ("service_tier", "default_service_tier")

FINDINGS = ("downgraded", "partly-downgraded", "unrequested-premium")


def tier_of(project):
    """Read a project's configured service tier. Pure.

    Returns a lowercase string, or None when the object carries no such field.
    None is not "standard": a missing field means this script cannot see the
    setting, and reporting that as a configured default would turn every
    unreadable project into a false clean.
    """
    candidates = []
    for field in TIER_FIELDS:
        candidates.append(project.get(field))
    settings = project.get("settings")
    if isinstance(settings, dict):
        for field in TIER_FIELDS:
            candidates.append(settings.get(field))
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


def split_spend(buckets, project_id):
    """Split one project's spend into premium and standard dollars. Pure.

    Returns (premium, standard, labels) where labels are the distinct line_item
    strings that matched as premium. The strings come back so the report can
    show what it matched on rather than asking you to trust a substring test.
    """
    premium = 0.0
    standard = 0.0
    labels = set()
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            if str(result.get("project_id") or "") != str(project_id):
                continue
            label = str(result.get("line_item") or "")
            try:
                value = float((result.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                continue
            low = label.lower()
            if any(word in low for word in PREMIUM_WORDS):
                premium += value
                if value:
                    labels.add(label)
            else:
                standard += value
    return (round(premium, 2), round(standard, 2), sorted(labels))


def overrides(pairs):
    """Parse --tier project_id=tier arguments into a dict. Pure.

    For organizations whose project objects do not carry the setting at all: you
    read it once in the console and hand it to the script, rather than the
    script guessing.
    """
    out = {}
    for pair in pairs or []:
        if "=" not in str(pair):
            continue
        name, _, value = str(pair).partition("=")
        name, value = name.strip(), value.strip().lower()
        if name and value:
            out[name] = value
    return out


def verdict(tier, premium, standard, min_spend=1.0, delivered=0.60):
    """Classify one project. Pure. Returns (state, detail).

    The two findings are opposite and are never collapsed. "downgraded" costs
    latency you thought you had bought; "unrequested-premium" costs money nobody
    budgeted. A script that printed "tier mismatch" for both would leave the
    reader to work out which of those they were looking at.
    """
    premium = max(0.0, float(premium or 0.0))
    standard = max(0.0, float(standard or 0.0))
    total = premium + standard
    tier = (tier or "").strip().lower() or None

    if total < min_spend:
        return ("no-spend",
                "$%.2f of spend in the window, too little to say anything about "
                "which tier served it" % total)

    share = premium / total

    if tier in ("fast", "priority"):
        if premium <= 0:
            return ("downgraded",
                    "configured for the %s tier and not one dollar of $%.2f in "
                    "spend is on a premium line item. Every request in the "
                    "window was served on the default tier."
                    % (tier, total))
        if share < delivered:
            return ("partly-downgraded",
                    "configured for the %s tier, and only %.0f%% of $%.2f in "
                    "spend is on premium line items. The rest was downgraded "
                    "and served at default latency." % (tier, share * 100, total))
        return ("premium-delivered",
                "configured for the %s tier and %.0f%% of $%.2f is billed at it. "
                "The premium is being delivered and charged at about %.1fx the "
                "standard rate, so somebody should still want it."
                % (tier, share * 100, total, PREMIUM_MULTIPLIER))

    if tier is None:
        if premium > 0:
            return ("unknown-tier-premium",
                    "the project object carries no readable service tier and "
                    "$%.2f of $%.2f is on premium line items. Read the setting "
                    "in the console and pass it with --tier."
                    % (premium, total))
        return ("unknown-tier",
                "the project object carries no readable service tier. No "
                "premium line items in $%.2f of spend, so nothing is being "
                "billed at the premium rate today." % total)

    if premium > 0:
        return ("unrequested-premium",
                "the project tier is %s and %.0f%% of $%.2f is on premium line "
                "items, so a code path is sending the tier in the request body. "
                "That traffic bills at about %.1fx the standard rate."
                % (tier, share * 100, total, PREMIUM_MULTIPLIER))
    return ("standard",
            "tier is %s and no premium line items in $%.2f of spend" % (tier, total))


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def projects(session, page_size, max_pages):
    """Walk GET /v1/organization/projects, which paginates on the last id."""
    params = {"limit": page_size}
    for _ in range(max_pages):
        page = get(session, "/organization/projects", params)
        data = page.get("data") or []
        for project in data:
            yield project
        if not page.get("has_more") or not data:
            return
        params = {"limit": page_size, "after": data[-1].get("id")}


def cost_pages(session, params, max_pages=40):
    """Walk the cost report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, "/organization/costs", params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily cost buckets to read (default 30)")
    ap.add_argument("--min-spend", type=float, default=1.0,
                    help="ignore projects below this many dollars (default 1.0)")
    ap.add_argument("--delivered", type=float, default=0.60,
                    help="premium share above which the tier counts as "
                         "delivered (default 0.60)")
    ap.add_argument("--tier", action="append", default=[], metavar="ID=TIER",
                    help="supply a project's configured tier when the object "
                         "does not carry it, e.g. --tier proj_abc=fast")
    ap.add_argument("--show-all", action="store_true",
                    help="also print projects whose tier and invoice agree")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key, read-only "
                  "scopes are enough)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    told = overrides(args.tier)
    costs = list(cost_pages(session, {
        "start_time": int(time.time()) - args.days * 86400,
        "bucket_width": "1d",
        "limit": min(180, max(1, args.days)),
        "group_by": ["line_item", "project_id"],
    }))

    checked = 0
    found = 0
    for project in projects(session, 100, 20):
        project_id = str(project.get("id") or "")
        name = str(project.get("name") or project_id)
        tier = told.get(project_id) or tier_of(project)
        premium, standard, labels = split_spend(costs, project_id)
        state, detail = verdict(tier, premium, standard, args.min_spend,
                                args.delivered)
        checked += 1
        line = "%-21s %s (%s)  %s" % (state, project_id, name, detail)

        if state in FINDINGS:
            found += 1
            log.warning(line)
            if labels:
                log.warning("  matched premium line item(s): %s",
                            ", ".join(labels))
            if state == "unrequested-premium":
                log.warning("  repair: find the call site sending the tier in "
                            "the request body and drop it, or budget for it "
                            "deliberately. Nothing in the project settings asked "
                            "for this.")
            else:
                log.warning("  repair: either stop paying for a tier you are not "
                            "being served (set Project Service Tier back to "
                            "standard) or ask OpenAI to raise the ramp limits "
                            "that are downgrading you. Decide which, then log "
                            "the response envelope's service_tier so the "
                            "downgrade rate is a metric instead of an audit.")
        elif state in ("unknown-tier", "unknown-tier-premium"):
            log.warning(line)
        elif args.show_all:
            log.info(line)

    log.info("%d project(s) checked, %d with a tier the invoice disagrees with",
             checked, found)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-fast-mode-tier-audit.mjs",
"js": '''/**
 * Report OpenAI projects whose configured service tier and invoice disagree.
 *
 * Read only. Two GET requests against the organization endpoints and nothing
 * else. Those endpoints reject project keys, so this needs an organization
 * admin key (sk-admin-), which can and should be provisioned read-only.
 */
const API = 'https://api.openai.com/v1';

// Fast mode is priced at twice the standard rate. The multiplier describes the
// finding; the dollars come from the cost report rather than a price table.
const PREMIUM_MULTIPLIER = 2.0;

// line_item is a human-readable label, not a documented enum.
const PREMIUM_WORDS = ['fast', 'priority'];

// What the project object calls the setting the console calls Project Service
// Tier. Read leniently and in this order; absent is reported as absent.
const TIER_FIELDS = ['service_tier', 'default_service_tier'];

const FINDINGS = ['downgraded', 'partly-downgraded', 'unrequested-premium'];

/**
 * Read a project's configured service tier. Pure. Returns a lowercase string,
 * or null when the object carries no such field. null is not "standard": a
 * missing field means the setting is unreadable here, and treating that as a
 * configured default would turn every unreadable project into a false clean.
 */
export function tierOf(project) {
  const candidates = TIER_FIELDS.map((f) => project[f]);
  const settings = project.settings;
  if (settings !== null && typeof settings === 'object' && !Array.isArray(settings)) {
    for (const f of TIER_FIELDS) candidates.push(settings[f]);
  }
  for (const value of candidates) {
    if (typeof value === 'string' && value.trim()) return value.trim().toLowerCase();
  }
  return null;
}

/**
 * Split one project's spend into premium and standard dollars. Pure. Returns
 * [premium, standard, labels]; the labels are the distinct line_item strings
 * that matched, so the report can show what the substring test caught.
 */
export function splitSpend(buckets, projectId) {
  let premium = 0;
  let standard = 0;
  const labels = new Set();
  for (const bucket of buckets ?? []) {
    for (const result of bucket.results ?? []) {
      if (String(result.project_id ?? '') !== String(projectId)) continue;
      const label = String(result.line_item ?? '');
      const value = Number(result.amount?.value ?? 0);
      if (!Number.isFinite(value)) continue;
      const low = label.toLowerCase();
      if (PREMIUM_WORDS.some((w) => low.includes(w))) {
        premium += value;
        if (value) labels.add(label);
      } else {
        standard += value;
      }
    }
  }
  return [Math.round(premium * 100) / 100, Math.round(standard * 100) / 100,
          [...labels].sort()];
}

/**
 * Parse --tier project_id=tier arguments into a Map. Pure. For organizations
 * whose project objects do not carry the setting: you read it once in the
 * console and hand it over, rather than the script guessing.
 */
export function overrides(pairs) {
  const out = new Map();
  for (const pair of pairs ?? []) {
    const text = String(pair);
    const at = text.indexOf('=');
    if (at < 0) continue;
    const name = text.slice(0, at).trim();
    const value = text.slice(at + 1).trim().toLowerCase();
    if (name && value) out.set(name, value);
  }
  return out;
}

/**
 * Classify one project. Pure. Returns [state, detail]. The two findings are
 * opposite and are never collapsed: one costs latency you thought you bought,
 * the other costs money nobody budgeted.
 */
export function verdict(tier, premium, standard, minSpend = 1.0, delivered = 0.60) {
  const prem = Math.max(0, Number(premium) || 0);
  const std = Math.max(0, Number(standard) || 0);
  const total = prem + std;
  const configured = (tier ?? '').trim().toLowerCase() || null;

  if (total < minSpend) {
    return ['no-spend',
      `$${total.toFixed(2)} of spend in the window, too little to say anything ` +
      'about which tier served it'];
  }

  const share = prem / total;
  const pct = Math.round(share * 100);

  if (configured === 'fast' || configured === 'priority') {
    if (prem <= 0) {
      return ['downgraded',
        `configured for the ${configured} tier and not one dollar of ` +
        `$${total.toFixed(2)} in spend is on a premium line item. Every ` +
        'request in the window was served on the default tier.'];
    }
    if (share < delivered) {
      return ['partly-downgraded',
        `configured for the ${configured} tier, and only ${pct}% of ` +
        `$${total.toFixed(2)} in spend is on premium line items. The rest was ` +
        'downgraded and served at default latency.'];
    }
    return ['premium-delivered',
      `configured for the ${configured} tier and ${pct}% of $${total.toFixed(2)} ` +
      `is billed at it. The premium is being delivered and charged at about ` +
      `${PREMIUM_MULTIPLIER.toFixed(1)}x the standard rate, so somebody should ` +
      'still want it.'];
  }

  if (configured === null) {
    if (prem > 0) {
      return ['unknown-tier-premium',
        `the project object carries no readable service tier and ` +
        `$${prem.toFixed(2)} of $${total.toFixed(2)} is on premium line items. ` +
        'Read the setting in the console and pass it with --tier.'];
    }
    return ['unknown-tier',
      'the project object carries no readable service tier. No premium line ' +
      `items in $${total.toFixed(2)} of spend, so nothing is being billed at ` +
      'the premium rate today.'];
  }

  if (prem > 0) {
    return ['unrequested-premium',
      `the project tier is ${configured} and ${pct}% of $${total.toFixed(2)} is ` +
      'on premium line items, so a code path is sending the tier in the request ' +
      `body. That traffic bills at about ${PREMIUM_MULTIPLIER.toFixed(1)}x the ` +
      'standard rate.'];
  }
  return ['standard',
    `tier is ${configured} and no premium line items in $${total.toFixed(2)} of spend`];
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) v.forEach((one) => url.searchParams.append(k, String(one)));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* walkProjects(key, pageSize, maxPages) {
  let params = { limit: pageSize };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/projects', params);
    const data = page.data ?? [];
    for (const project of data) yield project;
    if (!page.has_more || data.length === 0) return;
    params = { limit: pageSize, after: data[data.length - 1].id };
  }
}

async function costPages(key, params, maxPages = 40) {
  const out = [];
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/organization/costs', query);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) break;
    query = { ...params, page: page.next_page };
  }
  return out;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY ?? process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key, read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 30);
  const minSpend = Number(process.env.MIN_SPEND ?? 1.0);
  const delivered = Number(process.env.DELIVERED ?? 0.60);
  const showAll = process.argv.includes('--show-all');
  const told = overrides(process.argv
    .filter((a) => a.startsWith('--tier='))
    .map((a) => a.slice('--tier='.length)));

  const costs = await costPages(key, {
    start_time: Math.floor(Date.now() / 1000) - days * 86400,
    bucket_width: '1d',
    limit: Math.min(180, Math.max(1, days)),
    group_by: ['line_item', 'project_id'],
  });

  let checked = 0;
  let found = 0;
  for await (const project of walkProjects(key, 100, 20)) {
    const projectId = String(project.id ?? '');
    const name = String(project.name ?? projectId);
    const tier = told.get(projectId) ?? tierOf(project);
    const [premium, standard, labels] = splitSpend(costs, projectId);
    const [state, detail] = verdict(tier, premium, standard, minSpend, delivered);
    checked += 1;
    const line = `${state.padEnd(21)} ${projectId} (${name})  ${detail}`;

    if (FINDINGS.includes(state)) {
      found += 1;
      console.warn(line);
      if (labels.length) {
        console.warn(`  matched premium line item(s): ${labels.join(', ')}`);
      }
      if (state === 'unrequested-premium') {
        console.warn('  repair: find the call site sending the tier in the ' +
          'request body and drop it, or budget for it deliberately. Nothing in ' +
          'the project settings asked for this.');
      } else {
        console.warn('  repair: either stop paying for a tier you are not being ' +
          'served (set Project Service Tier back to standard) or ask OpenAI to ' +
          'raise the ramp limits that are downgrading you. Decide which, then ' +
          'log the response envelope\\'s service_tier so the downgrade rate is a ' +
          'metric instead of an audit.');
      }
    } else if (state === 'unknown-tier' || state === 'unknown-tier-premium') {
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${checked} project(s) checked, ${found} with a tier the invoice ` +
              'disagrees with');
  process.exitCode = found ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two tests that carry the note are the two directions of the mismatch: premium configured with standard spend, and standard configured with premium spend. They must not produce the same state, because they do not have the same repair. The rest pin down the things a lenient reader gets wrong &mdash; a project object with no tier field is unreadable rather than standard, and a project with almost no spend is not evidence of anything either way.",
"test_py_file": "test_openai_fast_mode_tier_audit.py",
"test_py": '''from openai_fast_mode_tier_audit import overrides, split_spend, tier_of, verdict


def cost(project="proj_a", line_item="gpt-5.6-sol, input", value=0.0):
    return {"project_id": project, "line_item": line_item,
            "amount": {"value": value, "currency": "usd"}}


def buckets(*results):
    return [{"start_time": 0, "end_time": 86400, "results": list(results)}]


def test_configured_fast_with_standard_spend_is_a_downgrade():
    # The whole note. Nothing errored, the tier was requested, and the invoice
    # says every request in the window was served on the default tier.
    state, detail = verdict("fast", premium=0.0, standard=420.0)
    assert state == "downgraded"
    assert "not one dollar" in detail
    assert "default tier" in detail


def test_configured_standard_with_premium_spend_is_the_opposite_finding():
    state, detail = verdict("standard", premium=300.0, standard=100.0)
    assert state == "unrequested-premium"
    assert "a code path is sending the tier" in detail
    assert "2.0x" in detail


def test_a_delivered_premium_is_not_reported_as_a_failure():
    state, detail = verdict("fast", premium=380.0, standard=20.0)
    assert state == "premium-delivered"
    assert "95%" in detail


def test_a_partial_downgrade_is_its_own_state():
    state, detail = verdict("fast", premium=100.0, standard=300.0)
    assert state == "partly-downgraded"
    assert "only 25%" in detail


def test_a_missing_tier_field_is_never_read_as_standard():
    assert tier_of({"id": "proj_a", "name": "web"}) is None
    assert tier_of({"id": "proj_a", "service_tier": "  Fast "}) == "fast"
    assert tier_of({"id": "proj_a", "settings": {"service_tier": "priority"}}) == "priority"
    assert tier_of({"id": "proj_a", "settings": "fast"}) is None
    assert verdict(None, premium=0.0, standard=99.0)[0] == "unknown-tier"
    assert verdict(None, premium=50.0, standard=49.0)[0] == "unknown-tier-premium"


def test_a_project_with_no_spend_is_not_evidence_of_anything():
    assert verdict("fast", premium=0.0, standard=0.0)[0] == "no-spend"
    assert verdict("standard", premium=0.2, standard=0.1)[0] == "no-spend"


def test_premium_line_items_are_matched_by_label_and_the_labels_come_back():
    rows = buckets(
        cost(line_item="gpt-5.6-sol, input", value=100.0),
        cost(line_item="gpt-5.6-sol, input (fast)", value=40.0),
        cost(line_item="gpt-5.6-sol, priority output", value=10.0),
        cost(project="proj_b", line_item="gpt-5.6-sol, input (fast)", value=999.0),
    )
    premium, standard, labels = split_spend(rows, "proj_a")
    assert premium == 50.0
    assert standard == 100.0
    assert labels == ["gpt-5.6-sol, input (fast)", "gpt-5.6-sol, priority output"]


def test_tier_overrides_are_parsed_and_junk_is_dropped():
    assert overrides(["proj_a=Fast", "proj_b = standard "]) == {
        "proj_a": "fast", "proj_b": "standard"}
    assert overrides(["nonsense", "=fast", "proj_c="]) == {}
    assert overrides(None) == {}
''',
"test_js_file": "openai-fast-mode-tier-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { overrides, splitSpend, tierOf, verdict }
  from './openai-fast-mode-tier-audit.mjs';

function cost({ project = 'proj_a', lineItem = 'gpt-5.6-sol, input',
                value = 0 } = {}) {
  return { project_id: project, line_item: lineItem,
           amount: { value, currency: 'usd' } };
}

function buckets(...results) {
  return [{ start_time: 0, end_time: 86400, results }];
}

test('configured fast with standard spend is a downgrade', () => {
  const [state, detail] = verdict('fast', 0, 420);
  assert.equal(state, 'downgraded');
  assert.match(detail, /not one dollar/);
  assert.match(detail, /default tier/);
});

test('configured standard with premium spend is the opposite finding', () => {
  const [state, detail] = verdict('standard', 300, 100);
  assert.equal(state, 'unrequested-premium');
  assert.match(detail, /a code path is sending the tier/);
  assert.match(detail, /2\\.0x/);
});

test('a delivered premium is not reported as a failure', () => {
  const [state, detail] = verdict('fast', 380, 20);
  assert.equal(state, 'premium-delivered');
  assert.match(detail, /95%/);
});

test('a partial downgrade is its own state', () => {
  const [state, detail] = verdict('fast', 100, 300);
  assert.equal(state, 'partly-downgraded');
  assert.match(detail, /only 25%/);
});

test('a missing tier field is never read as standard', () => {
  assert.equal(tierOf({ id: 'proj_a', name: 'web' }), null);
  assert.equal(tierOf({ id: 'proj_a', service_tier: '  Fast ' }), 'fast');
  assert.equal(tierOf({ id: 'proj_a', settings: { service_tier: 'priority' } }),
               'priority');
  assert.equal(tierOf({ id: 'proj_a', settings: 'fast' }), null);
  assert.equal(verdict(null, 0, 99)[0], 'unknown-tier');
  assert.equal(verdict(null, 50, 49)[0], 'unknown-tier-premium');
});

test('a project with no spend is not evidence of anything', () => {
  assert.equal(verdict('fast', 0, 0)[0], 'no-spend');
  assert.equal(verdict('standard', 0.2, 0.1)[0], 'no-spend');
});

test('premium line items are matched by label and the labels come back', () => {
  const rows = buckets(
    cost({ lineItem: 'gpt-5.6-sol, input', value: 100 }),
    cost({ lineItem: 'gpt-5.6-sol, input (fast)', value: 40 }),
    cost({ lineItem: 'gpt-5.6-sol, priority output', value: 10 }),
    cost({ project: 'proj_b', lineItem: 'gpt-5.6-sol, input (fast)', value: 999 }),
  );
  const [premium, standard, labels] = splitSpend(rows, 'proj_a');
  assert.equal(premium, 50);
  assert.equal(standard, 100);
  assert.deepEqual(labels,
    ['gpt-5.6-sol, input (fast)', 'gpt-5.6-sol, priority output']);
});

test('tier overrides are parsed and junk is dropped', () => {
  assert.deepEqual([...overrides(['proj_a=Fast', 'proj_b = standard '])],
                   [['proj_a', 'fast'], ['proj_b', 'standard']]);
  assert.deepEqual([...overrides(['nonsense', '=fast', 'proj_c='])], []);
  assert.deepEqual([...overrides(null)], []);
});
''',
"faq": [
 ("What is the difference between the service_tier I send and the one I get back?",
  "The one you send is a request. The one in the response envelope is a statement of fact about how that request was served. Fast mode carries ramp rate limits, and when they trigger the request is served on the default tier rather than rejected, so the two fields differ with no error, no header and no warning. Log the response field."),
 ("How much does the premium tier actually cost?",
  "Twice the standard rate on GPT-5.6 Sol: $8 per million input tokens and $40 per million output short-context, against $4 and $20 standard; $16 and $60 long-context against $8 and $30. Anthropic's fast mode is the same shape, running Claude Opus 5 at $10/$50 per MTok against the standard $5/$25, and it is a per-request parameter there rather than a project setting."),
 ("Can a read-only script see the served tier directly?",
  "Not without making a real inference call, which spends money and is why this script does not. Neither provider exposes a request log, so there is no GET that returns the served tier for calls you already made. The invoice is the closest read-only proxy there is: what you were billed for is what you were served."),
 ("Why does the script report a project whose tier field it cannot read?",
  "Because unreadable is not the same as standard, and folding the two together would turn every project the script cannot see into a clean one. If your project objects do not carry the setting, read it once in the console and pass it in with --tier, or make the response envelope's service_tier part of your telemetry and stop asking the project object at all."),
 ("Is a delivered premium a finding?",
  "No, and the script says so rather than staying silent. Paying 2x for latency you need is a decision, not a bug. It is worth re-confirming annually, because the workload that needed sub-second responses in year one is often a batch job by year three, and nobody goes back to the checkbox."),
],
"related": [REL_DOM, REL_SPIKE, REL_SPEND_LIMIT],
"citations": [CITE_FAST, CITE_PRIORITY, CITE_COSTS, CITE_ADMIN],
},

{
"slug": "streaming-usage-lost",
"title": "Streamed responses report no usage and the dashboard undercounts",
"description": "usage is null on every streamed chunk unless you ask for the totals. Reconcile the org token report against your own telemetry to size the hole.",
"h1": "streamed responses report no usage and the dashboard undercounts",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai stream_options include_usage", "streaming usage null openai",
             "openai token usage streaming", "cost dashboard undercounts tokens",
             "openai usage api reconciliation"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, plus a JSON file of the token counts your own telemetry recorded.",
"lead": "The internal cost dashboard has been trusted for a year. It reads the <code>usage</code> object off every response, sums it per project, multiplies by the price card and draws a line. In January the line and the invoice were within a few percent of each other. They are not now, and the gap is a third. Nothing in the dashboard is broken, and nothing in the pipeline dropped a record: the chat endpoint was switched to streaming in March, and a streamed chunk carries <code>usage: null</code>.",
"short_answer": """<p>Two numbers, and only one of them comes from OpenAI. With an <strong>organization admin key</strong>, read <code>GET /v1/organization/usage/completions?start_time={now-7d}&amp;bucket_width=1d&amp;limit=7&amp;group_by=project_id</code> and sum <code>input_tokens + output_tokens</code> per project. Then hand the script the same week's totals from your own telemetry and compare them.</p>
<p>A persistent shortfall concentrated in the projects that stream is this bug, and the size of the shortfall is the size of the spend you are not recording. An <em>excess</em> is not the same bug and is not reported as one: recording more tokens than the org was billed for is double counting, usually a retry logged twice.</p>
<p>The cause is one parameter. On Chat Completions, <code>usage</code> is <code>null</code> on every chunk unless the request sets <code>stream_options: {"include_usage": true}</code>, which appends a final chunk carrying the totals with an empty <code>choices</code> array. Without it there is nothing to record. With it, there is still nothing to record when the client hangs up before the last chunk arrives.</p>""",
"problem": """<p>The failure is in your numbers, not in OpenAI's. Every token is billed correctly, every response is correct, and the only thing that is wrong is the internal record of what happened &mdash; which is the thing every downstream decision is made from. Per-customer margin, the model comparison that justified a migration, the budget for next quarter: all computed from a number that is short by whatever share of your traffic streams.</p>
<p>It hides well because it degrades rather than breaks. A dashboard reporting zero would have been fixed in a day. A dashboard reporting sixty percent of the truth looks like a dashboard, and the gap gets attributed to rounding, to the price card being out of date, to buckets landing on different day boundaries. The one explanation nobody reaches for is that the pipeline is not recording the tokens at all.</p>""",
"why": """<p><strong>Streaming chunks carry no usage by default.</strong> Chat Completions sets <code>usage</code> to <code>null</code> on every delta. The totals arrive only if you asked for them with <code>stream_options.include_usage</code>, and then only in one extra chunk at the end whose <code>choices</code> array is empty &mdash; which is itself a shape that breaks naive parsers that assume every chunk has a choice in it.</p>
<p><strong>An abandoned stream loses its usage even when you did ask.</strong> The totals ride on the final chunk. If the user closes the tab, the proxy times out or the client cancels, that chunk is never delivered. The tokens generated up to that point are still billed. Your untracked share is therefore bounded below by your client-abandonment rate, and no request-side change can drive it to zero.</p>
<p><strong>Neither provider exposes a request log.</strong> There is no endpoint that lists individual calls with their token counts, so a missing per-request record cannot be backfilled from the API. The aggregate usage report is the only surviving evidence, which is why the check is a reconciliation between two sources rather than a query against one.</p>
<p><strong>The Responses API moves the field but not the problem.</strong> There the totals arrive on the terminal <code>response.completed</code> event as <code>response.usage</code>, with no options parameter needed. Consuming events but stopping at the last text delta produces exactly the same hole.</p>
<p><strong>The reconciliation is per project, because that is the finest grain both sides share.</strong> The usage report groups by <code>project_id</code>, <code>model</code>, <code>api_key_id</code> and a few others; your telemetry probably groups by service or customer. Project is usually the only key both sides agree on, and a project that streams sitting next to one that does not is what makes the finding legible.</p>""",
"steps": [
 {"h": "Export your own token totals for one week, per project",
  "body": """<p>A JSON object keyed by project id: <code>{"proj_abc": 12400000}</code>, or <code>{"proj_abc": {"input_tokens": 9000000, "output_tokens": 3400000}}</code> if you keep the two apart. This is the half the API cannot give you, and getting it out of your own store is most of the work.</p>"""},
 {"h": "Read the same week from the organization usage endpoint",
  "body": """<p><code>GET /v1/organization/usage/completions?start_time={now-7d}&amp;bucket_width=1d&amp;limit=7&amp;group_by=project_id</code> with an admin key, following <code>next_page</code>. Sum <code>input_tokens + output_tokens</code> per project. Use the same week on both sides and the same timezone, or you will spend an afternoon on a gap that is a day boundary.</p>"""},
 {"h": "Compare per project and keep the three disagreements apart",
  "body": """<p>Recorded well below the API is the finding. Recorded well above it is double counting, which is a different bug with a different fix. A project the API has usage for and your telemetry has never heard of is not undercounted at all &mdash; it is unrecorded, and it is usually a project id nobody mapped.</p>"""},
 {"h": "Price the gap from the cost report, not from a price table",
  "body": """<p><code>GET /v1/organization/costs?start_time=…&amp;bucket_width=1d&amp;group_by=project_id</code>, then scale each project's dollars by the share of its tokens you are missing. That is a pro-rata estimate rather than an exact figure &mdash; input and output are priced differently &mdash; but it is honest about the order of magnitude and it does not go stale.</p>"""},
 {"h": "Fix the client, then reconcile monthly anyway",
  "body": """<p>Set <code>stream_options={"include_usage": True}</code> on every streaming Chat Completions call and read the final chunk; on the Responses API, consume <code>response.completed</code> and read <code>response.usage</code>. Then keep running this check, because abandoned streams will always lose their final chunk and the aggregate report is the only place that truth survives.</p>"""},
],
"verify": """<p>Re-run a week after the client change. The gap should collapse to roughly your abandonment rate rather than to zero.</p>
<pre><code class="language-bash">python3 openai_streaming_usage_gap.py --telemetry week.json --days 7
# matched     proj_chat  recorded 41,980,110 tokens against 42,004,900 in the org report (0.1% apart)
# 5 project(s) reconciled, 0 with a gap</code></pre>""",
"code_intro": "One GET for tokens, one for dollars, and a file you supply. Four pure functions: the accumulator over the usage buckets; the lenient reader for your telemetry, which has to tell a project recorded as zero apart from a project not recorded at all; the comparison, which keeps undercount, overcount and unrecorded as three findings rather than one; and the pro-rata pricing, which is deliberately an estimate and says so.",
"py_file": "openai_streaming_usage_gap.py",
"py": '''"""Reconcile OpenAI's token totals against the ones your own telemetry recorded.

Read only. Two GET requests against the organization endpoints and a JSON file
you supply. Those endpoints reject project keys, so this needs an organization
admin key (sk-admin-), which can and should be provisioned read-only.

The finding is a gap between two sources, not a problem with either provider's
billing. Streamed responses carry usage: null on every chunk unless the request
asked for the totals, so a dashboard built on per-request telemetry undercounts
by whatever share of the traffic streams. The repair is printed, not applied.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_streaming_usage_gap")

API = "https://api.openai.com/v1"

FINDINGS = ("undercount", "overcount", "untracked", "phantom")


def api_totals(buckets):
    """Fold usage buckets into one row per project. Pure.

    Requests are carried alongside the tokens because OpenAI reports them and
    Anthropic does not; a project with requests and no output tokens is a
    different note, and this one at least keeps the number in view.
    """
    rows = {}
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            project = str(result.get("project_id") or "unknown")
            row = rows.setdefault(project, {"tokens": 0, "requests": 0})
            row["tokens"] += (int(result.get("input_tokens") or 0)
                              + int(result.get("output_tokens") or 0))
            row["requests"] += int(result.get("num_model_requests") or 0)
    return rows


def recorded_tokens(entry):
    """Read one project's own recorded token count. Pure.

    Returns an int, or None when nothing was recorded for that project at all.
    The distinction is the point: zero means your pipeline saw the project and
    recorded nothing, None means it has never heard of it, and those are two
    different bugs with two different owners.
    """
    if entry is None:
        return None
    if isinstance(entry, bool):
        return None
    if isinstance(entry, (int, float)):
        return int(entry)
    if isinstance(entry, dict):
        if "tokens" in entry:
            try:
                return int(entry["tokens"] or 0)
            except (TypeError, ValueError):
                return None
        if "input_tokens" in entry or "output_tokens" in entry:
            try:
                return (int(entry.get("input_tokens") or 0)
                        + int(entry.get("output_tokens") or 0))
            except (TypeError, ValueError):
                return None
    return None


def compare(api_tokens, recorded, tolerance=0.05, min_tokens=100000):
    """Compare one project's two numbers. Pure. Returns (state, detail).

    Three disagreements, not one. Recorded below the API is the undercount this
    note is about. Recorded above it is double counting, a different bug that
    would be hidden by an absolute-value comparison. A project missing from the
    telemetry entirely is not undercounted, it is unrecorded.
    """
    api_tokens = int(api_tokens or 0)

    if api_tokens <= 0:
        if recorded is None or int(recorded) <= 0:
            return ("idle", "no usage in the org report and none recorded")
        return ("phantom",
                "%d token(s) recorded against a project the org report shows no "
                "usage for. That is a project id mapping, not a streaming "
                "problem." % int(recorded))

    if recorded is None:
        return ("untracked",
                "%d token(s) in the org report and no telemetry for this project "
                "at all. Not an undercount: nothing here is being recorded."
                % api_tokens)

    recorded = int(recorded)
    if api_tokens < min_tokens:
        return ("too-little-traffic",
                "%d token(s) in the window, too few for the comparison to mean "
                "anything" % api_tokens)

    gap = api_tokens - recorded
    share = gap / float(api_tokens)
    if share > tolerance:
        return ("undercount",
                "recorded %d token(s) against %d in the org report, short by %d "
                "(%.1f%%). Streamed responses report usage: null unless the "
                "request asked for the totals."
                % (recorded, api_tokens, gap, share * 100))
    if share < -tolerance:
        return ("overcount",
                "recorded %d token(s) against %d in the org report, over by %d "
                "(%.1f%%). Recording more than you were billed for is double "
                "counting, not a streaming gap."
                % (recorded, api_tokens, -gap, -share * 100))
    return ("matched",
            "recorded %d token(s) against %d in the org report (%.1f%% apart)"
            % (recorded, api_tokens, abs(share) * 100))


def untracked_cost(cost_buckets, project_id, api_tokens, gap_tokens):
    """Pro-rata dollars behind an untracked token gap. Pure.

    An estimate and nothing more: input and output are priced differently, so
    scaling a project's spend by its missing token share is only right when the
    missing traffic has the same mix as the rest. It is the right order of
    magnitude and it is read from the cost report rather than a price table,
    which is the most this can honestly claim.
    """
    api_tokens = int(api_tokens or 0)
    gap_tokens = int(gap_tokens or 0)
    if api_tokens <= 0 or gap_tokens <= 0:
        return 0.0
    spend = 0.0
    for bucket in cost_buckets or []:
        for result in bucket.get("results") or []:
            if str(result.get("project_id") or "") != str(project_id):
                continue
            try:
                spend += float((result.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                continue
    return round(spend * min(1.0, gap_tokens / float(api_tokens)), 2)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk a usage or cost report, which paginates on an opaque page cursor."""
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
    ap.add_argument("--telemetry", required=True,
                    help="JSON file of your own recorded token counts, keyed by "
                         "project id")
    ap.add_argument("--days", type=int, default=7,
                    help="days to reconcile (default 7)")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="fractional disagreement to accept as matched "
                         "(default 0.05)")
    ap.add_argument("--min-tokens", type=int, default=100000,
                    help="ignore projects below this many tokens (default 100000)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print projects that reconcile")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key, read-only "
                  "scopes are enough)")
        return 2

    try:
        with open(args.telemetry, "r", encoding="utf-8") as fh:
            telemetry = json.load(fh)
    except (OSError, ValueError) as exc:
        log.error("could not read %s: %s", args.telemetry, exc)
        return 2
    if not isinstance(telemetry, dict):
        log.error("%s should be a JSON object keyed by project id", args.telemetry)
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    start = int(time.time()) - args.days * 86400
    usage = list(pages(session, "/organization/usage/completions", {
        "start_time": start,
        "bucket_width": "1d",
        "limit": min(31, max(1, args.days)),
        "group_by": ["project_id"],
    }))
    costs = list(pages(session, "/organization/costs", {
        "start_time": start,
        "bucket_width": "1d",
        "limit": min(180, max(1, args.days)),
        "group_by": ["project_id"],
    }))

    rows = api_totals(usage)
    for project in telemetry:
        rows.setdefault(str(project), {"tokens": 0, "requests": 0})
    if not rows:
        log.info("no completions usage in the last %d day(s) and nothing in the "
                 "telemetry file", args.days)
        return 0

    found = 0
    for project in sorted(rows):
        api_tokens = rows[project]["tokens"]
        recorded = recorded_tokens(telemetry.get(project))
        state, detail = compare(api_tokens, recorded, args.tolerance,
                                args.min_tokens)
        line = "%-18s %s  %s" % (state, project, detail)

        if state in FINDINGS:
            found += 1
            log.warning(line)
            if state == "undercount":
                gap = api_tokens - int(recorded or 0)
                money = untracked_cost(costs, project, api_tokens, gap)
                log.warning("  about $%.2f of this project's spend over %d day(s) "
                            "is not in your own numbers", money, args.days)
                log.warning("  repair: set stream_options include_usage on every "
                            "streaming Chat Completions call and read the final "
                            "chunk, or read response.usage from the terminal "
                            "response.completed event on the Responses API. "
                            "Streams the client abandons will still lose theirs.")
            elif state == "overcount":
                log.warning("  repair: this is double counting rather than a "
                            "streaming gap. Look for retries recorded once per "
                            "attempt, or one response written by two consumers.")
            elif state == "untracked":
                log.warning("  repair: this project is absent from your "
                            "telemetry. Map the project id before treating any "
                            "of these numbers as a margin.")
            else:
                log.warning("  repair: your telemetry attributes tokens to a "
                            "project the organization report has no usage for. "
                            "Check the project id, not the streaming client.")
        elif args.show_all:
            log.info(line)

    log.info("%d project(s) reconciled, %d with a gap", len(rows), found)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-streaming-usage-gap.mjs",
"js": '''/**
 * Reconcile OpenAI's token totals against the ones your own telemetry recorded.
 *
 * Read only. Two GET requests against the organization endpoints and a JSON
 * file you supply. Those endpoints reject project keys, so this needs an
 * organization admin key (sk-admin-), provisioned read-only.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.openai.com/v1';

const FINDINGS = ['undercount', 'overcount', 'untracked', 'phantom'];

/**
 * Fold usage buckets into one row per project. Pure. Requests ride along
 * because OpenAI reports them and Anthropic does not.
 */
export function apiTotals(buckets) {
  const rows = new Map();
  for (const bucket of buckets ?? []) {
    for (const result of bucket.results ?? []) {
      const project = String(result.project_id ?? 'unknown');
      const row = rows.get(project) ?? { tokens: 0, requests: 0 };
      row.tokens += (Number(result.input_tokens ?? 0) || 0)
                  + (Number(result.output_tokens ?? 0) || 0);
      row.requests += Number(result.num_model_requests ?? 0) || 0;
      rows.set(project, row);
    }
  }
  return rows;
}

/**
 * Read one project's own recorded token count. Pure. Returns a number, or null
 * when nothing was recorded for that project at all. Zero means your pipeline
 * saw the project and recorded nothing; null means it has never heard of it,
 * and those are two different bugs with two different owners.
 */
export function recordedTokens(entry) {
  if (entry === null || entry === undefined) return null;
  if (typeof entry === 'boolean') return null;
  if (typeof entry === 'number') return Number.isFinite(entry) ? Math.trunc(entry) : null;
  if (typeof entry === 'object' && !Array.isArray(entry)) {
    if ('tokens' in entry) {
      const value = Number(entry.tokens ?? 0);
      return Number.isFinite(value) ? Math.trunc(value) : null;
    }
    if ('input_tokens' in entry || 'output_tokens' in entry) {
      const value = (Number(entry.input_tokens ?? 0) || 0)
                  + (Number(entry.output_tokens ?? 0) || 0);
      return Number.isFinite(value) ? Math.trunc(value) : null;
    }
  }
  return null;
}

/**
 * Compare one project's two numbers. Pure. Returns [state, detail]. Three
 * disagreements, not one: short is the streaming gap, over is double counting,
 * and absent from the telemetry is neither.
 */
export function compare(apiTokens, recorded, tolerance = 0.05, minTokens = 100000) {
  const api = Number(apiTokens) || 0;

  if (api <= 0) {
    if (recorded === null || recorded === undefined || Number(recorded) <= 0) {
      return ['idle', 'no usage in the org report and none recorded'];
    }
    return ['phantom',
      `${Math.trunc(Number(recorded))} token(s) recorded against a project the ` +
      'org report shows no usage for. That is a project id mapping, not a ' +
      'streaming problem.'];
  }

  if (recorded === null || recorded === undefined) {
    return ['untracked',
      `${api} token(s) in the org report and no telemetry for this project at ` +
      'all. Not an undercount: nothing here is being recorded.'];
  }

  const seen = Math.trunc(Number(recorded));
  if (api < minTokens) {
    return ['too-little-traffic',
      `${api} token(s) in the window, too few for the comparison to mean anything`];
  }

  const gap = api - seen;
  const share = gap / api;
  if (share > tolerance) {
    return ['undercount',
      `recorded ${seen} token(s) against ${api} in the org report, short by ` +
      `${gap} (${(share * 100).toFixed(1)}%). Streamed responses report usage: ` +
      'null unless the request asked for the totals.'];
  }
  if (share < -tolerance) {
    return ['overcount',
      `recorded ${seen} token(s) against ${api} in the org report, over by ` +
      `${-gap} (${(-share * 100).toFixed(1)}%). Recording more than you were ` +
      'billed for is double counting, not a streaming gap.'];
  }
  return ['matched',
    `recorded ${seen} token(s) against ${api} in the org report ` +
    `(${(Math.abs(share) * 100).toFixed(1)}% apart)`];
}

/**
 * Pro-rata dollars behind an untracked token gap. Pure. An estimate: input and
 * output are priced differently, so this is only exact when the missing traffic
 * has the same mix as the rest. Read from the cost report, not a price table.
 */
export function untrackedCost(costBuckets, projectId, apiTokens, gapTokens) {
  const api = Number(apiTokens) || 0;
  const gap = Number(gapTokens) || 0;
  if (api <= 0 || gap <= 0) return 0;
  let spend = 0;
  for (const bucket of costBuckets ?? []) {
    for (const result of bucket.results ?? []) {
      if (String(result.project_id ?? '') !== String(projectId)) continue;
      spend += Number(result.amount?.value ?? 0) || 0;
    }
  }
  return Math.round(spend * Math.min(1, gap / api) * 100) / 100;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) v.forEach((one) => url.searchParams.append(k, String(one)));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function pages(key, path, params, maxPages = 40) {
  const out = [];
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) break;
    query = { ...params, page: page.next_page };
  }
  return out;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY ?? process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key, read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }

  const flag = process.argv.find((a) => a.startsWith('--telemetry='));
  const path = flag ? flag.slice('--telemetry='.length) : process.env.TELEMETRY;
  if (!path) {
    console.error('pass --telemetry=week.json (your own recorded token counts, ' +
                  'keyed by project id)');
    process.exitCode = 2;
    return;
  }

  let telemetry;
  try {
    telemetry = JSON.parse(await readFile(path, 'utf8'));
  } catch (err) {
    console.error(`could not read ${path}: ${err.message}`);
    process.exitCode = 2;
    return;
  }
  if (telemetry === null || typeof telemetry !== 'object' || Array.isArray(telemetry)) {
    console.error(`${path} should be a JSON object keyed by project id`);
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 7);
  const tolerance = Number(process.env.TOLERANCE ?? 0.05);
  const minTokens = Number(process.env.MIN_TOKENS ?? 100000);
  const showAll = process.argv.includes('--show-all');

  const start = Math.floor(Date.now() / 1000) - days * 86400;
  const usage = await pages(key, '/organization/usage/completions', {
    start_time: start,
    bucket_width: '1d',
    limit: Math.min(31, Math.max(1, days)),
    group_by: ['project_id'],
  });
  const costs = await pages(key, '/organization/costs', {
    start_time: start,
    bucket_width: '1d',
    limit: Math.min(180, Math.max(1, days)),
    group_by: ['project_id'],
  });

  const rows = apiTotals(usage);
  for (const project of Object.keys(telemetry)) {
    if (!rows.has(project)) rows.set(project, { tokens: 0, requests: 0 });
  }
  if (rows.size === 0) {
    console.log(`no completions usage in the last ${days} day(s) and nothing in ` +
                'the telemetry file');
    return;
  }

  let found = 0;
  for (const project of [...rows.keys()].sort()) {
    const apiTokens = rows.get(project).tokens;
    const recorded = recordedTokens(telemetry[project]);
    const [state, detail] = compare(apiTokens, recorded, tolerance, minTokens);
    const line = `${state.padEnd(18)} ${project}  ${detail}`;

    if (FINDINGS.includes(state)) {
      found += 1;
      console.warn(line);
      if (state === 'undercount') {
        const gap = apiTokens - (recorded ?? 0);
        const money = untrackedCost(costs, project, apiTokens, gap);
        console.warn(`  about $${money.toFixed(2)} of this project's spend over ` +
          `${days} day(s) is not in your own numbers`);
        console.warn('  repair: set stream_options include_usage on every ' +
          'streaming Chat Completions call and read the final chunk, or read ' +
          'response.usage from the terminal response.completed event on the ' +
          'Responses API. Streams the client abandons will still lose theirs.');
      } else if (state === 'overcount') {
        console.warn('  repair: this is double counting rather than a streaming ' +
          'gap. Look for retries recorded once per attempt, or one response ' +
          'written by two consumers.');
      } else if (state === 'untracked') {
        console.warn('  repair: this project is absent from your telemetry. Map ' +
          'the project id before treating any of these numbers as a margin.');
      } else {
        console.warn('  repair: your telemetry attributes tokens to a project ' +
          'the organization report has no usage for. Check the project id, not ' +
          'the streaming client.');
      }
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${rows.size} project(s) reconciled, ${found} with a gap`);
  process.exitCode = found ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note: your number is materially below OpenAI's and the script says so in tokens and in percent. The second is the one that keeps this honest &mdash; recording <em>more</em> than you were billed for is double counting, and a comparison written with an absolute value would report it as the same finding and send somebody to add a streaming parameter that changes nothing. The rest pin the difference between a project recorded as zero and a project never recorded at all.",
"test_py_file": "test_openai_streaming_usage_gap.py",
"test_py": '''from openai_streaming_usage_gap import (api_totals, compare, recorded_tokens,
                                          untracked_cost)


def bucket(*results):
    return {"start_time": 0, "end_time": 86400, "results": list(results)}


def usage(project="proj_chat", input_tokens=0, output_tokens=0, requests=0):
    return {"project_id": project, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "num_model_requests": requests}


def test_a_dashboard_short_of_the_org_report_is_the_finding():
    state, detail = compare(api_tokens=42_000_000, recorded=28_000_000)
    assert state == "undercount"
    assert "short by 14000000" in detail
    assert "33.3%" in detail
    assert "usage: null" in detail


def test_recording_more_than_you_were_billed_for_is_a_different_bug():
    # An absolute-value comparison would call this an undercount and send
    # somebody to add a streaming parameter that changes nothing.
    state, detail = compare(api_tokens=10_000_000, recorded=13_000_000)
    assert state == "overcount"
    assert "double counting" in detail


def test_a_project_missing_from_telemetry_is_not_an_undercount():
    state, detail = compare(api_tokens=9_000_000, recorded=None)
    assert state == "untracked"
    assert "nothing here is being recorded" in detail
    # Recorded as zero is a different sentence: the pipeline saw it.
    assert compare(api_tokens=9_000_000, recorded=0)[0] == "undercount"


def test_tokens_recorded_against_a_project_with_no_usage_are_a_mapping_bug():
    state, detail = compare(api_tokens=0, recorded=5_000_000)
    assert state == "phantom"
    assert "project id mapping" in detail
    assert compare(api_tokens=0, recorded=None)[0] == "idle"
    assert compare(api_tokens=0, recorded=0)[0] == "idle"


def test_small_projects_and_close_numbers_are_not_findings():
    assert compare(api_tokens=5_000, recorded=1)[0] == "too-little-traffic"
    state, detail = compare(api_tokens=1_000_000, recorded=980_000)
    assert state == "matched"
    assert "2.0% apart" in detail


def test_usage_buckets_fold_into_one_row_per_project():
    rows = api_totals([
        bucket(usage(input_tokens=100, output_tokens=20, requests=3),
               usage(project="proj_batch", input_tokens=7, output_tokens=1)),
        bucket(usage(input_tokens=50, output_tokens=5, requests=2)),
    ])
    assert rows["proj_chat"] == {"tokens": 175, "requests": 5}
    assert rows["proj_batch"] == {"tokens": 8, "requests": 0}


def test_telemetry_is_read_leniently_but_absence_is_preserved():
    assert recorded_tokens(1200) == 1200
    assert recorded_tokens({"tokens": 1200}) == 1200
    assert recorded_tokens({"input_tokens": 900, "output_tokens": 300}) == 1200
    assert recorded_tokens(0) == 0
    assert recorded_tokens(None) is None
    assert recorded_tokens({}) is None
    assert recorded_tokens("lots") is None
    assert recorded_tokens(True) is None


def test_the_money_is_a_pro_rata_share_of_reported_spend():
    costs = [bucket({"project_id": "proj_chat",
                     "amount": {"value": 300.0, "currency": "usd"}},
                    {"project_id": "proj_other",
                     "amount": {"value": 900.0, "currency": "usd"}})]
    assert untracked_cost(costs, "proj_chat", 1_000_000, 250_000) == 75.0
    assert untracked_cost(costs, "proj_chat", 1_000_000, 0) == 0.0
    assert untracked_cost(costs, "proj_chat", 0, 100) == 0.0
    assert untracked_cost(costs, "proj_missing", 1_000_000, 500_000) == 0.0
''',
"test_js_file": "openai-streaming-usage-gap.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apiTotals, compare, recordedTokens, untrackedCost }
  from './openai-streaming-usage-gap.mjs';

function bucket(...results) {
  return { start_time: 0, end_time: 86400, results };
}

function usage({ project = 'proj_chat', inputTokens = 0, outputTokens = 0,
                 requests = 0 } = {}) {
  return { project_id: project, input_tokens: inputTokens,
           output_tokens: outputTokens, num_model_requests: requests };
}

test('a dashboard short of the org report is the finding', () => {
  const [state, detail] = compare(42000000, 28000000);
  assert.equal(state, 'undercount');
  assert.match(detail, /short by 14000000/);
  assert.match(detail, /33\\.3%/);
  assert.match(detail, /usage: null/);
});

test('recording more than you were billed for is a different bug', () => {
  const [state, detail] = compare(10000000, 13000000);
  assert.equal(state, 'overcount');
  assert.match(detail, /double counting/);
});

test('a project missing from telemetry is not an undercount', () => {
  const [state, detail] = compare(9000000, null);
  assert.equal(state, 'untracked');
  assert.match(detail, /nothing here is being recorded/);
  assert.equal(compare(9000000, 0)[0], 'undercount');
});

test('tokens recorded against a project with no usage are a mapping bug', () => {
  const [state, detail] = compare(0, 5000000);
  assert.equal(state, 'phantom');
  assert.match(detail, /project id mapping/);
  assert.equal(compare(0, null)[0], 'idle');
  assert.equal(compare(0, 0)[0], 'idle');
});

test('small projects and close numbers are not findings', () => {
  assert.equal(compare(5000, 1)[0], 'too-little-traffic');
  const [state, detail] = compare(1000000, 980000);
  assert.equal(state, 'matched');
  assert.match(detail, /2\\.0% apart/);
});

test('usage buckets fold into one row per project', () => {
  const rows = apiTotals([
    bucket(usage({ inputTokens: 100, outputTokens: 20, requests: 3 }),
           usage({ project: 'proj_batch', inputTokens: 7, outputTokens: 1 })),
    bucket(usage({ inputTokens: 50, outputTokens: 5, requests: 2 })),
  ]);
  assert.deepEqual(rows.get('proj_chat'), { tokens: 175, requests: 5 });
  assert.deepEqual(rows.get('proj_batch'), { tokens: 8, requests: 0 });
});

test('telemetry is read leniently but absence is preserved', () => {
  assert.equal(recordedTokens(1200), 1200);
  assert.equal(recordedTokens({ tokens: 1200 }), 1200);
  assert.equal(recordedTokens({ input_tokens: 900, output_tokens: 300 }), 1200);
  assert.equal(recordedTokens(0), 0);
  assert.equal(recordedTokens(null), null);
  assert.equal(recordedTokens({}), null);
  assert.equal(recordedTokens('lots'), null);
  assert.equal(recordedTokens(true), null);
});

test('the money is a pro rata share of reported spend', () => {
  const costs = [bucket(
    { project_id: 'proj_chat', amount: { value: 300.0, currency: 'usd' } },
    { project_id: 'proj_other', amount: { value: 900.0, currency: 'usd' } },
  )];
  assert.equal(untrackedCost(costs, 'proj_chat', 1000000, 250000), 75);
  assert.equal(untrackedCost(costs, 'proj_chat', 1000000, 0), 0);
  assert.equal(untrackedCost(costs, 'proj_chat', 0, 100), 0);
  assert.equal(untrackedCost(costs, 'proj_missing', 1000000, 500000), 0);
});
''',
"faq": [
 ("What exactly does stream_options include_usage change?",
  "It appends one extra chunk to the end of a streamed Chat Completions response. That chunk carries the usage object with the full token counts, and its choices array is empty. Without the option, usage is null on every chunk and the totals are never sent at all. On the Responses API there is no option to set: the totals arrive on the terminal response.completed event as response.usage."),
 ("If I set it, is the gap closed?",
  "Not entirely, and the note is written on that assumption. The final chunk only helps if the client is still listening when it arrives. A user who closes the tab mid-answer, a proxy that times out, a cancelled request: the tokens generated so far are billed and the usage chunk is never delivered. Your residual gap is roughly your abandonment rate, and the aggregate report is the only place it can be recovered from."),
 ("Why reconcile per project rather than per request?",
  "Because per request is not available. Neither OpenAI nor Anthropic exposes an endpoint that lists individual inference calls, so there is no way to ask which requests your telemetry missed. Project is the finest grain the aggregate report and your own store are likely to share, which makes it the level the comparison can honestly be made at."),
 ("The gap is exactly one day's worth. Is that this bug?",
  "Almost certainly not. Check your window and your timezone first: the usage endpoint buckets on UTC, and a dashboard bucketing on local time will disagree with it by a fixed offset that looks like a percentage. This check is worth running over a whole week for that reason, and a gap that is stable in percent across many weeks is the streaming one."),
 ("Does Anthropic have the same problem?",
  "The same shape with different fields. Claude's streaming responses carry usage on the message_start and message_delta events rather than requiring an option, so the totals are harder to miss, but a client that stops reading before message_stop still loses the final output count. The reconciliation side is blunter: the organization messages usage report has no request-count field at all, so you can compare tokens but not calls."),
],
"related": [REL_REASONING, REL_SPIKE, REL_DOM],
"citations": [CITE_STREAMING, CITE_USAGE_COMPLETIONS, CITE_USAGE_COOKBOOK, CITE_ADMIN],
},

{
"slug": "spend-spike-week-over-week",
"title": "Spend jumped week over week and no release explains it",
"description": "Eight weeks of daily cost folded into whole weeks. The shape of the change is the finding: a spike, a step and a ramp want three different people.",
"h1": "spend jumped week over week and no release explains it",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai spend increase week over week", "anthropic cost report weekly",
             "openai organization costs api", "llm bill doubled no deploy",
             "openai spend alert threshold"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY or ANTHROPIC_ADMIN_KEY, an organization admin key provisioned read-only, because both cost reports reject workspace and project keys.",
"lead": "The invoice is three times last month's and nothing shipped. There is no error to look up, no status code, no failed request &mdash; the API worked perfectly all month, which is the problem. Somewhere in the last six weeks a cron went from hourly to every five minutes, or a prompt template grew a retrieved document, or a customer onboarded, and the feedback loop between that change and the bill is measured in weeks. By the time the number arrives, nobody remembers the week it started in.",
"short_answer": """<p>Read eight weeks of daily cost with an admin key, fold it into whole weeks, and compare the most recent complete week against the mean of the ones before it. On OpenAI: <code>GET /v1/organization/costs?start_time={now-56d}&amp;bucket_width=1d&amp;limit=56</code>. On Anthropic: <code>GET /v1/organizations/cost_report?starting_at={now-56d}&amp;limit=31</code>, paging on <code>next_page</code> because 31 buckets is that endpoint's maximum.</p>
<p>Then classify the <em>shape</em>, because "spend went up" is three different findings. A <strong>spike</strong> is one week high and the rest normal: a job that ran once, a backfill, an incident. A <strong>step</strong> is a new level that has held for two weeks or more: something shipped and is still shipping. A <strong>ramp</strong> is a line that has climbed every week, which a week-over-week comparison never catches, because each week is only a little above the mean of the weeks it raised.</p>
<p>Drop today. The current day's bucket is always partial, and a comparison that includes it reports a fall in spend every time you run it before lunch.</p>""",
"problem": """<p>Nothing about this arrives as an alert, because neither provider pushes one. Cost is a pull surface: an endpoint that answers accurately whenever you ask, and answers nothing at all when you do not. The teams that find a spike in week one have a scheduled job reading the endpoint; everybody else finds it on the invoice, which is 2 to 6 weeks after the change landed.</p>
<p>The delay is what makes it expensive. A retry loop that triples request volume is a five minute fix in the week it ships and a forensic exercise a month later, because by then there have been forty deploys, two new customers and a model migration, and any of them is a plausible cause. The endpoint can tell you the week it started in, which narrows forty deploys to three. That is the whole value of running this weekly rather than reading it annually.</p>""",
"why": """<p><strong>Cost has three inputs and any one can move alone.</strong> Requests, tokens per request, and price per token. A prompt template that grew moves the second without touching the first; a cron schedule moves the first without touching the second; a model migration moves the third. They are indistinguishable in a total and obvious the moment you group, which is why this note ends by handing you to <a href="/llm/one-model-or-project-dominates-cost/">the attribution one</a>.</p>
<p><strong>The current bucket is always partial.</strong> Both cost reports bucket by day and both will happily return today, half full. Include it and the newest week is short by however much of today has not happened yet, so the check reports a fall while spend is climbing. Dropping the incomplete day is not a refinement, it is the difference between a report that works and one that lies every morning.</p>
<p><strong>A ramp is invisible to week-over-week.</strong> Comparing the latest week against the mean of the previous four hides steady growth, because the growth is already in the baseline. Ten percent a week compounds to sixty percent over five weeks and never trips a forty percent threshold once. That is why monotonicity is checked separately from the ratio.</p>
<p><strong>The two providers disagree about what money is.</strong> OpenAI returns <code>amount.value</code> as a float in dollars with a lowercase <code>currency</code>. Anthropic returns <code>amount</code> as a decimal <em>string</em> in <em>cents</em>, which is a deliberate invitation to parse it as a decimal rather than a float. Doing that arithmetic in floats across 56 buckets is how a report ends up a cent adrift and an afternoon gets spent on it.</p>
<p><strong>Late data revises the recent past.</strong> Both reports can be updated as late events land, so the last day or two of a window is soft. Re-read the same window before escalating a finding to a team, and prefer a whole-week comparison over a day-to-day one for exactly this reason.</p>""",
"steps": [
 {"h": "Get an admin key for whichever organization you are reading",
  "body": """<p>OpenAI's <code>/v1/organization/costs</code> rejects project keys; Anthropic's <code>/v1/organizations/cost_report</code> rejects workspace keys. Both accept an admin key provisioned read-only, which is all this script wants.</p>"""},
 {"h": "Ask for the whole window explicitly",
  "body": """<p>Both endpoints default to a handful of buckets. OpenAI's <code>limit</code> runs 1&ndash;180 with a default of 7; Anthropic's tops out at 31, so eight weeks needs paging on <code>next_page</code> until <code>has_more</code> is false. A naive call returns one week and hides the comparison you came for.</p>"""},
 {"h": "Fold days into whole weeks and throw today away",
  "body": """<p>Seven-day windows anchored on the last complete day, not on today. A partial bucket at either end skews the week it lands in, and the newest week is the one every conclusion rests on.</p>"""},
 {"h": "Classify the shape rather than the size",
  "body": """<p>A spike sends someone to look for a job that ran once. A step sends someone to the deploys in that week. A ramp is usually growth &mdash; or a leak that has been open all along &mdash; and wants a projection rather than an investigation. Printing one number for all three loses the only information that tells you who to call.</p>"""},
 {"h": "Print the ceiling, then go and attribute the delta",
  "body": """<p>The repair is a hard spend limit and an alert below it, printed as an exact call for you to run. Then group the same window by line item and project to find what moved: this script deliberately does not, because a script that both detects and attributes ends up doing neither clearly.</p>"""},
],
"verify": """<p>Re-run after a week. A resolved spike drops back into the baseline and the state turns flat.</p>
<pre><code class="language-bash">python3 llm_spend_week_over_week.py --provider openai --weeks 8
# flat        2026-08-16..2026-08-22  $4,102.11 against a $4,020.44 baseline (+2.0%)
# 8 whole week(s) read, no change worth reporting</code></pre>""",
"code_intro": "Two parsers and two pure steps. The parsers exist because the two providers disagree about what money is &mdash; a float in dollars on one side, a decimal string in cents on the other &mdash; and the cents string is parsed as an integer number of millicents rather than as a float, which is the difference between a report that reconciles and one that is mysteriously a cent out. The folding step drops the incomplete day, which is the single most important line in the script. The classifier separates a spike from a step from a ramp, because those want three different people looking at them.",
"py_file": "llm_spend_week_over_week.py",
"py": '''"""Report a change in organization spend and say what shape the change is.

Read only. One paginated GET against whichever provider you point it at, and
nothing else. Both cost reports need an organization admin key: OpenAI's
rejects project keys, Anthropic's rejects workspace keys. Read-only admin keys
work and are what this should hold.

The repair is a spend limit and an alert, printed as an exact call for you to
run. This script never sets one: a script holding an admin key that can also
change your billing configuration is a worse tool than one that cannot.
"""
import argparse
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm_spend_week_over_week")

OPENAI_API = "https://api.openai.com/v1"
ANTHROPIC_API = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

EPOCH = date(1970, 1, 1)

FINDINGS = ("spike", "step", "ramp", "drop", "new-spend")


def _day_number(text):
    """An ISO day string to a day count since the epoch, or None."""
    try:
        return (date.fromisoformat(str(text)[:10]) - EPOCH).days
    except (TypeError, ValueError):
        return None


def _day_iso(number):
    return (EPOCH + timedelta(days=int(number))).isoformat()


def parse_cents(text):
    """Anthropic's decimal string of cents to integer millicents. Pure.

    Returns None on anything unparseable, which the caller skips rather than
    reading as zero. Integer millicents rather than a float because summing 56
    buckets of float cents is how a total ends up a cent adrift and an afternoon
    gets spent working out where.
    """
    raw = str(text if text is not None else "").strip()
    if not raw:
        return None
    negative = raw.startswith("-")
    if raw[:1] in ("+", "-"):
        raw = raw[1:]
    whole, _, frac = raw.partition(".")
    whole = whole or "0"
    frac = (frac + "000")[:3]
    if not whole.isdigit() or not frac.isdigit():
        return None
    value = int(whole) * 1000 + int(frac)
    return -value if negative else value


def daily_from_openai(buckets):
    """Fold GET /v1/organization/costs into {day: dollars}. Pure.

    amount.value is a float in dollars and start_time is a Unix timestamp, so
    the day key is the UTC date the bucket opened on.
    """
    days = {}
    for bucket in buckets or []:
        try:
            opened = int(bucket.get("start_time"))
        except (TypeError, ValueError):
            continue
        key = datetime.fromtimestamp(opened, timezone.utc).date().isoformat()
        for result in bucket.get("results") or []:
            try:
                value = float((result.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                continue
            days[key] = round(days.get(key, 0.0) + value, 6)
    return days


def daily_from_anthropic(buckets):
    """Fold GET /v1/organizations/cost_report into {day: dollars}. Pure.

    amount is a decimal string in cents, so it is parsed as an exact number of
    millicents and only converted to dollars once, at the end.
    """
    days = {}
    for bucket in buckets or []:
        key = str(bucket.get("starting_at") or "")[:10]
        if _day_number(key) is None:
            continue
        for result in bucket.get("results") or []:
            millicents = parse_cents(result.get("amount"))
            if millicents is None:
                continue
            days[key] = days.get(key, 0) + millicents
    return {day: round(total / 100000.0, 4) for day, total in days.items()}


def weeks(daily, today, count=8):
    """Fold {day: dollars} into whole weeks, newest first. Pure.

    Returns [(first_day, last_day, dollars), ...]. Today is excluded, always:
    the current day's bucket is partial, and a comparison that includes it
    reports a fall in spend every time it runs before lunch. The anchor is the
    most recent complete day that carries data rather than yesterday, because
    both cost reports lag by a day or two and an empty tail would otherwise
    drag every week boundary with it.
    """
    end = _day_number(today)
    if end is None:
        return []
    totals = {}
    for key, value in (daily or {}).items():
        number = _day_number(key)
        if number is None or number >= end:
            continue
        try:
            totals[number] = totals.get(number, 0.0) + float(value or 0.0)
        except (TypeError, ValueError):
            continue
    if not totals:
        return []

    first = min(totals)
    stop = min(end, max(totals) + 1)
    out = []
    while len(out) < int(count):
        start = stop - 7
        if start < first:
            break
        total = sum(totals.get(day, 0.0) for day in range(start, stop))
        out.append((_day_iso(start), _day_iso(stop - 1), round(total, 2)))
        stop = start
    return out


def classify(totals, threshold=0.40, min_weeks=3):
    """Classify a list of weekly totals, newest first. Pure. (state, detail).

    Three ways for spend to be higher than it was, and they want three
    different people: a spike is one week and a job that ran once, a step is a
    new level that something shipped into, a ramp is growth that no
    week-over-week ratio will ever catch because it is already in the baseline.
    """
    series = []
    for value in totals or []:
        try:
            series.append(float(value))
        except (TypeError, ValueError):
            return ("unreadable", "a weekly total that is not a number")

    if len(series) < int(min_weeks):
        return ("too-short",
                "%d whole week(s) of history, which is not enough to call "
                "anything a change" % len(series))

    latest, prior = series[0], series[1:]
    baseline = sum(prior) / len(prior)
    if baseline <= 0:
        if latest > 0:
            return ("new-spend",
                    "$%.2f in the latest week against nothing at all before it. "
                    "This organization started spending inside the window."
                    % latest)
        return ("no-spend", "no spend in any of the %d week(s) read" % len(series))

    oldest_first = list(reversed(series))
    climbing = all(b > a for a, b in zip(oldest_first, oldest_first[1:]))
    if (len(series) >= 4 and climbing and oldest_first[0] > 0
            and (latest - oldest_first[0]) / oldest_first[0] > threshold):
        return ("ramp",
                "every one of %d week(s) is higher than the one before it, "
                "$%.2f to $%.2f (+%.0f%%). A week-over-week check never sees "
                "this, because the growth is already in the baseline."
                % (len(series), oldest_first[0], latest,
                   100 * (latest - oldest_first[0]) / oldest_first[0]))

    change = (latest - baseline) / baseline
    if change > threshold:
        older = series[2:]
        older_baseline = sum(older) / len(older) if older else 0.0
        if older_baseline > 0 and (series[1] - older_baseline) / older_baseline > threshold:
            return ("step",
                    "$%.2f in the latest week and $%.2f in the one before it, "
                    "against a $%.2f baseline before that. The new level has "
                    "held for two weeks, so something shipped rather than ran "
                    "once." % (latest, series[1], older_baseline))
        return ("spike",
                "$%.2f in the latest week against a $%.2f baseline (+%.0f%%), "
                "and the week before it was normal. One week high is a job that "
                "ran, not a level that changed."
                % (latest, baseline, change * 100))
    if change < -threshold:
        return ("drop",
                "$%.2f in the latest week against a $%.2f baseline (%.0f%%). "
                "Spend falling this fast is usually traffic that stopped rather "
                "than money that was saved." % (latest, baseline, change * 100))
    return ("flat",
            "$%.2f against a $%.2f baseline (%+.1f%%)"
            % (latest, baseline, change * 100))


def get(session, url, params, headers=None):
    r = session.get(url, params=params, headers=headers or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from the cost report: this endpoint needs an "
                         "organization admin key, not a project or workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def openai_buckets(session, days, max_pages=40):
    params = {"start_time": int(time.time()) - days * 86400,
              "bucket_width": "1d", "limit": min(180, max(1, days))}
    for _ in range(max_pages):
        page = get(session, OPENAI_API + "/organization/costs", params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def anthropic_buckets(session, days, max_pages=40):
    started = datetime.now(timezone.utc) - timedelta(days=days)
    params = {"starting_at": started.strftime("%Y-%m-%dT00:00:00Z"), "limit": 31}
    headers = {"anthropic-version": ANTHROPIC_VERSION}
    for _ in range(max_pages):
        page = get(session, ANTHROPIC_API + "/organizations/cost_report",
                   params, headers)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=("openai", "anthropic"),
                    default="openai", help="which cost report to read")
    ap.add_argument("--weeks", type=int, default=8,
                    help="whole weeks to read (default 8)")
    ap.add_argument("--threshold", type=float, default=0.40,
                    help="fractional change worth reporting (default 0.40)")
    args = ap.parse_args()

    session = requests.Session()
    if args.provider == "openai":
        key = os.environ.get("OPENAI_ADMIN_KEY")
        if not key:
            log.error("set OPENAI_ADMIN_KEY (an organization admin key, "
                      "read-only scopes are enough)")
            return 2
        session.headers.update({"Authorization": "Bearer " + key})
        buckets = list(openai_buckets(session, args.weeks * 7 + 1))
        daily = daily_from_openai(buckets)
    else:
        key = os.environ.get("ANTHROPIC_ADMIN_KEY")
        if not key:
            log.error("set ANTHROPIC_ADMIN_KEY (an Admin API key, sk-ant-admin)")
            return 2
        session.headers.update({"x-api-key": key})
        buckets = list(anthropic_buckets(session, args.weeks * 7 + 1))
        daily = daily_from_anthropic(buckets)

    today = datetime.now(timezone.utc).date().isoformat()
    series = weeks(daily, today, args.weeks)
    if not series:
        log.info("no whole weeks of cost data in the window")
        return 0

    state, detail = classify([total for _, _, total in series], args.threshold)
    first, last, _ = series[0]
    log.info("%d whole week(s) read, most recent %s..%s", len(series), first, last)
    for week_first, week_last, total in series:
        log.info("  %s..%s  $%.2f", week_first, week_last, total)

    if state in FINDINGS:
        log.warning("%-11s %s..%s  %s", state, first, last, detail)
        log.warning("  repair: attribute the delta before you act on it. Group "
                    "the same window by line item and by project and read the "
                    "rows that moved, rather than the rows you remember being "
                    "expensive.")
        if args.provider == "openai":
            log.warning("  repair: print, do not run. Set a ceiling with "
                        "POST /v1/organization/spend_limit "
                        "{'threshold_amount': <cents>, 'currency': 'USD', "
                        "'interval': 'month'} and an early warning with "
                        "POST /v1/organization/spend_alerts at about 60%% of it.")
        else:
            log.warning("  repair: Anthropic has no spend-limit endpoint. Set "
                        "the organization and per-workspace limits in the "
                        "console, and re-read this window first because late "
                        "events revise the recent past.")
        return 1

    log.info("%-11s %s..%s  %s", state, first, last, detail)
    log.info("%d whole week(s) read, no change worth reporting", len(series))
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "llm-spend-week-over-week.mjs",
"js": '''/**
 * Report a change in organization spend and say what shape the change is.
 *
 * Read only. One paginated GET against whichever provider you point it at.
 * Both cost reports need an organization admin key: OpenAI's rejects project
 * keys, Anthropic's rejects workspace keys. Read-only admin keys work.
 */
const OPENAI_API = 'https://api.openai.com/v1';
const ANTHROPIC_API = 'https://api.anthropic.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

const DAY = 86400000;

const FINDINGS = ['spike', 'step', 'ramp', 'drop', 'new-spend'];

/** An ISO day string to a day count since the epoch, or null. */
function dayNumber(text) {
  const parsed = Date.parse(`${String(text ?? '').slice(0, 10)}T00:00:00Z`);
  return Number.isNaN(parsed) ? null : Math.round(parsed / DAY);
}

function dayIso(number) {
  return new Date(number * DAY).toISOString().slice(0, 10);
}

/**
 * Anthropic's decimal string of cents to integer millicents. Pure. Returns
 * null on anything unparseable, which the caller skips rather than reading as
 * zero. Integers rather than floats because summing 56 buckets of float cents
 * is how a total ends up a cent adrift.
 */
export function parseCents(text) {
  let raw = String(text ?? '').trim();
  if (!raw) return null;
  const negative = raw.startsWith('-');
  if (raw[0] === '+' || raw[0] === '-') raw = raw.slice(1);
  const dot = raw.indexOf('.');
  const whole = (dot < 0 ? raw : raw.slice(0, dot)) || '0';
  const frac = `${dot < 0 ? '' : raw.slice(dot + 1)}000`.slice(0, 3);
  if (!/^\\d+$/.test(whole) || !/^\\d+$/.test(frac)) return null;
  const value = Number(whole) * 1000 + Number(frac);
  return negative ? -value : value;
}

/**
 * Fold GET /v1/organization/costs into {day: dollars}. Pure. amount.value is a
 * float in dollars and start_time is a Unix timestamp.
 */
export function dailyFromOpenai(buckets) {
  const days = new Map();
  for (const bucket of buckets ?? []) {
    const opened = Number(bucket.start_time);
    if (!Number.isFinite(opened)) continue;
    const key = new Date(opened * 1000).toISOString().slice(0, 10);
    for (const result of bucket.results ?? []) {
      const value = Number(result.amount?.value ?? 0);
      if (!Number.isFinite(value)) continue;
      days.set(key, Math.round(((days.get(key) ?? 0) + value) * 1e6) / 1e6);
    }
  }
  return days;
}

/**
 * Fold GET /v1/organizations/cost_report into {day: dollars}. Pure. amount is
 * a decimal string in cents, parsed exactly and converted once at the end.
 */
export function dailyFromAnthropic(buckets) {
  const days = new Map();
  for (const bucket of buckets ?? []) {
    const key = String(bucket.starting_at ?? '').slice(0, 10);
    if (dayNumber(key) === null) continue;
    for (const result of bucket.results ?? []) {
      const millicents = parseCents(result.amount);
      if (millicents === null) continue;
      days.set(key, (days.get(key) ?? 0) + millicents);
    }
  }
  const out = new Map();
  for (const [day, total] of days) out.set(day, Math.round(total / 10) / 10000);
  return out;
}

/**
 * Fold a day-to-dollars map into whole weeks, newest first. Pure. Returns
 * [[firstDay, lastDay, dollars], ...]. Today is excluded, always: the current
 * bucket is partial and a comparison that includes it reports a fall in spend
 * every time it runs before lunch.
 */
export function weeks(daily, today, count = 8) {
  const end = dayNumber(today);
  if (end === null) return [];
  const entries = daily instanceof Map ? [...daily] : Object.entries(daily ?? {});
  const totals = new Map();
  for (const [key, value] of entries) {
    const number = dayNumber(key);
    const amount = Number(value);
    if (number === null || number >= end || !Number.isFinite(amount)) continue;
    totals.set(number, (totals.get(number) ?? 0) + amount);
  }
  if (totals.size === 0) return [];

  const numbers = [...totals.keys()];
  const first = Math.min(...numbers);
  let stop = Math.min(end, Math.max(...numbers) + 1);
  const out = [];
  while (out.length < Number(count)) {
    const start = stop - 7;
    if (start < first) break;
    let total = 0;
    for (let day = start; day < stop; day += 1) total += totals.get(day) ?? 0;
    out.push([dayIso(start), dayIso(stop - 1), Math.round(total * 100) / 100]);
    stop = start;
  }
  return out;
}

/**
 * Classify a list of weekly totals, newest first. Pure. Returns [state,
 * detail]. Three ways for spend to be higher and three different people to
 * call: a spike is a job that ran once, a step is a level something shipped
 * into, a ramp is growth no week-over-week ratio will ever catch.
 */
export function classify(totals, threshold = 0.40, minWeeks = 3) {
  const series = [];
  for (const value of totals ?? []) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return ['unreadable', 'a weekly total that is not a number'];
    }
    series.push(number);
  }

  if (series.length < Number(minWeeks)) {
    return ['too-short',
      `${series.length} whole week(s) of history, which is not enough to call ` +
      'anything a change'];
  }

  const latest = series[0];
  const prior = series.slice(1);
  const baseline = prior.reduce((a, b) => a + b, 0) / prior.length;
  if (baseline <= 0) {
    if (latest > 0) {
      return ['new-spend',
        `$${latest.toFixed(2)} in the latest week against nothing at all ` +
        'before it. This organization started spending inside the window.'];
    }
    return ['no-spend', `no spend in any of the ${series.length} week(s) read`];
  }

  const oldestFirst = [...series].reverse();
  const climbing = oldestFirst.every((v, i) => i === 0 || v > oldestFirst[i - 1]);
  if (series.length >= 4 && climbing && oldestFirst[0] > 0
      && (latest - oldestFirst[0]) / oldestFirst[0] > threshold) {
    const growth = 100 * (latest - oldestFirst[0]) / oldestFirst[0];
    return ['ramp',
      `every one of ${series.length} week(s) is higher than the one before it, ` +
      `$${oldestFirst[0].toFixed(2)} to $${latest.toFixed(2)} ` +
      `(+${growth.toFixed(0)}%). A week-over-week check never sees this, ` +
      'because the growth is already in the baseline.'];
  }

  const change = (latest - baseline) / baseline;
  if (change > threshold) {
    const older = series.slice(2);
    const olderBaseline = older.length
      ? older.reduce((a, b) => a + b, 0) / older.length : 0;
    if (olderBaseline > 0 && (series[1] - olderBaseline) / olderBaseline > threshold) {
      return ['step',
        `$${latest.toFixed(2)} in the latest week and $${series[1].toFixed(2)} ` +
        `in the one before it, against a $${olderBaseline.toFixed(2)} baseline ` +
        'before that. The new level has held for two weeks, so something ' +
        'shipped rather than ran once.'];
    }
    return ['spike',
      `$${latest.toFixed(2)} in the latest week against a ` +
      `$${baseline.toFixed(2)} baseline (+${(change * 100).toFixed(0)}%), and ` +
      'the week before it was normal. One week high is a job that ran, not a ' +
      'level that changed.'];
  }
  if (change < -threshold) {
    return ['drop',
      `$${latest.toFixed(2)} in the latest week against a ` +
      `$${baseline.toFixed(2)} baseline (${(change * 100).toFixed(0)}%). Spend ` +
      'falling this fast is usually traffic that stopped rather than money ' +
      'that was saved.'];
  }
  const signed = `${change >= 0 ? '+' : ''}${(change * 100).toFixed(1)}`;
  return ['flat',
    `$${latest.toFixed(2)} against a $${baseline.toFixed(2)} baseline (${signed}%)`];
}

async function get(url, params, headers) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) target.searchParams.set(k, String(v));
  }
  const res = await fetch(target, { headers });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from the cost report: this endpoint needs an ` +
                    'organization admin key, not a project or workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${target.pathname}`);
  return res.json();
}

async function readBuckets(url, params, headers, maxPages = 40) {
  const out = [];
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(url, query, headers);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) break;
    query = { ...params, page: page.next_page };
  }
  return out;
}

async function main() {
  const provider = (process.argv.find((a) => a.startsWith('--provider='))
    ?? '--provider=openai').slice('--provider='.length);
  const howMany = Number(process.env.WEEKS ?? 8);
  const threshold = Number(process.env.THRESHOLD ?? 0.40);
  const days = howMany * 7 + 1;

  let daily;
  if (provider === 'anthropic') {
    const key = process.env.ANTHROPIC_ADMIN_KEY;
    if (!key) {
      console.error('set ANTHROPIC_ADMIN_KEY (an Admin API key, sk-ant-admin)');
      process.exitCode = 2;
      return;
    }
    const startedAt = new Date(Date.now() - days * DAY).toISOString().slice(0, 10);
    const buckets = await readBuckets(`${ANTHROPIC_API}/organizations/cost_report`,
      { starting_at: `${startedAt}T00:00:00Z`, limit: 31 },
      { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION });
    daily = dailyFromAnthropic(buckets);
  } else {
    const key = process.env.OPENAI_ADMIN_KEY;
    if (!key) {
      console.error('set OPENAI_ADMIN_KEY (an organization admin key, read-only ' +
                    'scopes are enough)');
      process.exitCode = 2;
      return;
    }
    const buckets = await readBuckets(`${OPENAI_API}/organization/costs`, {
      start_time: Math.floor((Date.now() - days * DAY) / 1000),
      bucket_width: '1d',
      limit: Math.min(180, Math.max(1, days)),
    }, { Authorization: `Bearer ${key}` });
    daily = dailyFromOpenai(buckets);
  }

  const today = new Date().toISOString().slice(0, 10);
  const series = weeks(daily, today, howMany);
  if (series.length === 0) {
    console.log('no whole weeks of cost data in the window');
    return;
  }

  const [state, detail] = classify(series.map(([, , total]) => total), threshold);
  const [first, last] = series[0];
  console.log(`${series.length} whole week(s) read, most recent ${first}..${last}`);
  for (const [weekFirst, weekLast, total] of series) {
    console.log(`  ${weekFirst}..${weekLast}  $${total.toFixed(2)}`);
  }

  if (FINDINGS.includes(state)) {
    console.warn(`${state.padEnd(11)} ${first}..${last}  ${detail}`);
    console.warn('  repair: attribute the delta before you act on it. Group the ' +
      'same window by line item and by project and read the rows that moved, ' +
      'rather than the rows you remember being expensive.');
    console.warn(provider === 'anthropic'
      ? '  repair: Anthropic has no spend-limit endpoint. Set the organization ' +
        'and per-workspace limits in the console, and re-read this window first ' +
        'because late events revise the recent past.'
      : '  repair: print, do not run. Set a ceiling with POST ' +
        "/v1/organization/spend_limit {'threshold_amount': <cents>, 'currency': " +
        "'USD', 'interval': 'month'} and an early warning with POST " +
        '/v1/organization/spend_alerts at about 60% of it.');
    process.exitCode = 1;
    return;
  }

  console.log(`${state.padEnd(11)} ${first}..${last}  ${detail}`);
  console.log(`${series.length} whole week(s) read, no change worth reporting`);
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four tests carry this one. Today must be dropped, or the newest week is short by however much of today has not happened and the script reports a fall every morning. A ramp must be caught, or steady ten-percent-a-week growth passes a forty percent threshold forever. A spike and a step must not collapse into each other, because one sends somebody to look for a job that ran and the other to a week of deploys. And the cents string must parse exactly, because that is the difference between a total that reconciles and one that is mysteriously a cent out.",
"test_py_file": "test_llm_spend_week_over_week.py",
"test_py": '''from llm_spend_week_over_week import (classify, daily_from_anthropic,
                                        daily_from_openai, parse_cents, weeks)


def test_today_is_never_counted_in_the_newest_week():
    # Fifteen days of a dollar a day, run on the fifteenth. The last day is
    # partial by definition, so two whole weeks come back and today is not in
    # either of them.
    daily = {"2026-08-%02d" % day: 1.0 for day in range(1, 16)}
    got = weeks(daily, "2026-08-15")
    assert len(got) == 2
    assert got[0] == ("2026-08-08", "2026-08-14", 7.0)
    assert got[1] == ("2026-08-01", "2026-08-07", 7.0)


def test_a_partial_oldest_week_is_dropped_rather_than_reported_short():
    daily = {"2026-08-%02d" % day: 10.0 for day in range(1, 12)}
    got = weeks(daily, "2026-08-12")
    assert [w[2] for w in got] == [70.0]


def test_one_high_week_is_a_spike_and_two_are_a_step():
    spike, detail = classify([3000.0, 1000.0, 1000.0, 1000.0])
    assert spike == "spike"
    assert "a job that ran" in detail

    step, detail = classify([3000.0, 3000.0, 1000.0, 1000.0])
    assert step == "step"
    assert "held for two weeks" in detail


def test_a_ramp_is_caught_even_though_week_over_week_never_trips():
    # +15% a week. Against the mean of the previous three the newest week is
    # only 31% up, so a ratio threshold of 40% would call this flat forever.
    state, detail = classify([1520.88, 1322.5, 1150.0, 1000.0])
    assert state == "ramp"
    assert "already in the baseline" in detail
    assert classify([1000.0, 1000.0, 1000.0, 1000.0])[0] == "flat"


def test_spend_falling_off_a_cliff_is_reported_rather_than_celebrated():
    state, detail = classify([400.0, 1000.0, 1000.0, 1000.0])
    assert state == "drop"
    assert "traffic that stopped" in detail


def test_a_short_history_and_a_standing_start_are_their_own_answers():
    assert classify([5000.0, 10.0])[0] == "too-short"
    assert classify([500.0, 0.0, 0.0])[0] == "new-spend"
    assert classify([0.0, 0.0, 0.0])[0] == "no-spend"
    assert classify(["lots", 1.0, 2.0])[0] == "unreadable"


def test_anthropic_cents_are_parsed_exactly_and_not_as_floats():
    assert parse_cents("1234.5") == 1234500
    assert parse_cents("0.001") == 1
    assert parse_cents("-250") == -250000
    assert parse_cents("") is None
    assert parse_cents(None) is None
    assert parse_cents("1,234") is None
    assert parse_cents("lots") is None


def test_both_providers_fold_into_the_same_day_keyed_dollars():
    # 2026-08-01T00:00:00Z is 1785542400. Two results in one bucket sum.
    openai = daily_from_openai([{
        "start_time": 1785542400, "end_time": 1785628800,
        "results": [{"amount": {"value": 12.5, "currency": "usd"}},
                    {"amount": {"value": 0.25, "currency": "usd"}}]}])
    assert openai == {"2026-08-01": 12.75}

    anthropic = daily_from_anthropic([{
        "starting_at": "2026-08-01T00:00:00Z",
        "results": [{"amount": "1250.0"}, {"amount": "25"}]}])
    assert anthropic == {"2026-08-01": 12.75}
    assert daily_from_anthropic([{"starting_at": "nonsense",
                                  "results": [{"amount": "1"}]}]) == {}
''',
"test_js_file": "llm-spend-week-over-week.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, dailyFromAnthropic, dailyFromOpenai, parseCents, weeks }
  from './llm-spend-week-over-week.mjs';

function dollarsPerDay(from, to, amount) {
  const daily = {};
  for (let day = from; day <= to; day += 1) {
    daily[`2026-08-${String(day).padStart(2, '0')}`] = amount;
  }
  return daily;
}

test('today is never counted in the newest week', () => {
  const got = weeks(dollarsPerDay(1, 15, 1.0), '2026-08-15');
  assert.equal(got.length, 2);
  assert.deepEqual(got[0], ['2026-08-08', '2026-08-14', 7.0]);
  assert.deepEqual(got[1], ['2026-08-01', '2026-08-07', 7.0]);
});

test('a partial oldest week is dropped rather than reported short', () => {
  const got = weeks(dollarsPerDay(1, 11, 10.0), '2026-08-12');
  assert.deepEqual(got.map((w) => w[2]), [70.0]);
});

test('one high week is a spike and two are a step', () => {
  const [spike, spikeDetail] = classify([3000, 1000, 1000, 1000]);
  assert.equal(spike, 'spike');
  assert.match(spikeDetail, /a job that ran/);

  const [step, stepDetail] = classify([3000, 3000, 1000, 1000]);
  assert.equal(step, 'step');
  assert.match(stepDetail, /held for two weeks/);
});

test('a ramp is caught even though week over week never trips', () => {
  const [state, detail] = classify([1520.88, 1322.5, 1150.0, 1000.0]);
  assert.equal(state, 'ramp');
  assert.match(detail, /already in the baseline/);
  assert.equal(classify([1000, 1000, 1000, 1000])[0], 'flat');
});

test('spend falling off a cliff is reported rather than celebrated', () => {
  const [state, detail] = classify([400, 1000, 1000, 1000]);
  assert.equal(state, 'drop');
  assert.match(detail, /traffic that stopped/);
});

test('a short history and a standing start are their own answers', () => {
  assert.equal(classify([5000, 10])[0], 'too-short');
  assert.equal(classify([500, 0, 0])[0], 'new-spend');
  assert.equal(classify([0, 0, 0])[0], 'no-spend');
  assert.equal(classify(['lots', 1, 2])[0], 'unreadable');
});

test('anthropic cents are parsed exactly and not as floats', () => {
  assert.equal(parseCents('1234.5'), 1234500);
  assert.equal(parseCents('0.001'), 1);
  assert.equal(parseCents('-250'), -250000);
  assert.equal(parseCents(''), null);
  assert.equal(parseCents(null), null);
  assert.equal(parseCents('1,234'), null);
  assert.equal(parseCents('lots'), null);
});

test('both providers fold into the same day keyed dollars', () => {
  const openai = dailyFromOpenai([{
    start_time: 1785542400,
    end_time: 1785628800,
    results: [{ amount: { value: 12.5, currency: 'usd' } },
              { amount: { value: 0.25, currency: 'usd' } }],
  }]);
  assert.deepEqual([...openai], [['2026-08-01', 12.75]]);

  const anthropic = dailyFromAnthropic([{
    starting_at: '2026-08-01T00:00:00Z',
    results: [{ amount: '1250.0' }, { amount: '25' }],
  }]);
  assert.deepEqual([...anthropic], [['2026-08-01', 12.75]]);
  assert.deepEqual([...dailyFromAnthropic([{ starting_at: 'nonsense',
                                             results: [{ amount: '1' }] }])], []);
});
''',
"faq": [
 ("Why compare whole weeks instead of the last seven days against the seven before?",
  "Because a rolling window moves the day boundaries every time you run it, and LLM traffic has a weekly rhythm: a window that starts on a Wednesday contains a different number of weekend days than one that starts on a Monday. Whole weeks anchored on the last complete day make two consecutive runs comparable, which is what turns this into a scheduled check rather than a one-off investigation."),
 ("What counts as a big enough change to care about?",
  "Forty percent above the trailing baseline is the default here and it is a starting point, not a law. Tune it to your own variance: an organization whose weekly spend already swings thirty percent will drown in findings at forty, and one that is flat to within five percent should set it far lower. The shape classification matters more than the threshold."),
 ("The report says my spend dropped. Why is that a finding?",
  "Because spend falling by half in a week is almost never a cost saving. It is traffic that stopped: a broken deploy, an expired key, a spend limit that started enforcing, or a customer who left. All four are worth knowing about within the week, and all four look identical to a cost report, which is why the script reports the drop and does not try to explain it."),
 ("Can the script set the spend limit it prints?",
  "It could, and it will not. Everything in this section holds a credential that can spend money on inference, and the whole design is that these scripts read and print. A hard ceiling on your organization's billing is also exactly the kind of change you want a human to type deliberately, with the number in front of them."),
 ("Anthropic's amounts look like ordinary numbers. Why the parsing fuss?",
  "Because they are strings, in cents, and the docs say to parse them as decimals rather than floats. Read as floats and summed across 56 buckets, the total drifts in the last decimal place, which is invisible until you reconcile it against an invoice and lose an afternoon. Parsing to integer millicents costs six lines and the question never comes up."),
],
"related": [REL_DOM, REL_SPEND_LIMIT, REL_STREAM],
"citations": [CITE_COSTS, CITE_AN_COST_REPORT, CITE_AN_USAGE_COST, CITE_ADMIN],
},

