#!/usr/bin/env python3
"""/llm/ field notes, batch N — the writing.

Four checks that a capability the organization has already paid for is actually
reaching production. Not "is it configured" — configuration is the part everyone
already looked at — but "does the provider's own report show it arriving". Each
of the four reads a field that goes quiet rather than wrong, and quiet is why
they survive: a capability that is absent produces no error, no latency change
and no line item.

`priority-tier-model-unsupported` is the narrowest of them and had to be, because
a published note already owns the service-tier configuration-versus-invoice
comparison in both directions. This one is not a misconfiguration at all. It is
coverage: Priority Tier is not supported on Opus 5, Sonnet 5, Mythos 5 or Mythos
Preview, so a migration to a newer model silently drops it, and because Priority
costs are excluded from the cost report entirely, the usage report grouped by
`service_tier` is the only read-only place the absence is visible. The script
refuses to print a dollar figure for the same reason.

`long-context-gated-on-obsolete-beta` reads `max_input_tokens` off the model
object and compares it with a ceiling your own code enforces. The published band
note treats 200k-1M as a size alarm in the usage report; this one is about a
window that was bought and then capped in software — 1M available, 200k enforced,
plus a beta header that is inert on current models and retired on the two where
it once did something.

The two Claude Code notes read a report neither of the caching notes has ever
touched: `GET /v1/organizations/usage_report/claude_code`, which is per actor and
per day and cannot be joined to the messages usage report at all. They are
siblings on that one endpoint and they do not merge, because they read different
blocks of it and reach opposite kinds of conclusion. One reads `tokens.cache_read`
and finds a prefix being repurchased every turn. The other reads `tool_actions`
and finds output that was generated, billed, read by a person and thrown away,
which is the only note in this section whose subject is billed work a human
deliberately discarded.

Read only throughout. Three want an Anthropic Admin key, one a workspace key.
Every request is a GET; nothing here sends a message, and no script has a write
path to disable. Every repair — a model id, a config constant, a session habit,
a project context file — is a change with an owner, so it is printed.
"""

CITE_CL_SERVICE_TIERS = ("Service tiers — Claude Docs",
                         "https://platform.claude.com/docs/en/api/service-tiers")
CITE_CL_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_CL_RATE_LIMITS = ("Rate limits — Claude Docs",
                       "https://platform.claude.com/docs/en/api/rate-limits")
CITE_CL_CONTEXT_WINDOWS = ("Context windows — Claude Docs",
                           "https://platform.claude.com/docs/en/build-with-claude/context-windows")
CITE_CL_MODELS = ("Models — Claude API reference",
                  "https://platform.claude.com/docs/en/api/models")
CITE_CL_MODELS_OVERVIEW = ("Models overview — Claude Docs",
                           "https://platform.claude.com/docs/en/models/overview")
CITE_CL_PRICING = ("Pricing — Claude Docs",
                   "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_CL_CACHING = ("Prompt caching — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
CITE_CC_ANALYTICS = ("Claude Code Analytics API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api")
CITE_CL_ANALYTICS = ("Analytics API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/analytics-api")

REL_FAST_MODE = ("/llm/fast-mode-silently-downgraded/",
                 "The tier you asked for against the tier the invoice says served you")
REL_529 = ("/llm/overloaded-529-clusters/",
           "The overload losses a priority commitment was bought to prevent")
REL_LIMITER = ("/llm/rate-limit-429-limiter-unidentified/",
               "Which of the three token limiters actually emptied")
REL_LONG_BAND = ("/llm/long-context-requests-unwatched/",
                 "How much traffic actually crosses 200k, measured in the usage report")
REL_OVERFLOW = ("/llm/prompt-too-long-context-overflow/",
                "One payload counted against the window before you send it")
REL_MAX_TOKENS = ("/llm/max-tokens-above-model-cap/",
                  "The output ceiling, which is a different number and a different note")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "Prompt caching that was never switched on at all")
REL_CACHE_WRITES = ("/llm/cache-writes-with-no-reads/",
                    "Cache entries written at a premium and never read back")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Why output tokens are where a generation bill actually sits")
REL_FRONTIER = ("/llm/frontier-model-on-trivial-workload/",
                "A model chosen larger than the work it is being given")
REL_CC_CACHE = ("/llm/claude-code-sessions-not-hitting-cache/",
                "The same report read for cache reads instead of acceptance")
REL_CC_REJECT = ("/llm/claude-code-edit-rejection-rate-high/",
                 "The same report read for the diffs nobody kept")

GUIDES = [
{
"slug": "priority-tier-model-unsupported",
"title": "Priority Tier never covered the model you migrated to",
"description": "Group the Claude usage report by service_tier and model. A model that never reports priority is not misconfigured, it has no coverage at all.",
"h1": "Priority Tier never covered the model you migrated to",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic priority tier model support",
             "claude service_tier auto never priority",
             "priority tier not supported opus 5",
             "anthropic usage report group_by service_tier",
             "priority tier missing from cost report"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only, because /v1/organizations/* rejects a workspace key.",
"lead": "The commitment was signed two years ago, and the whole point of it was the 529s. It worked: the overload errors stopped, the on-call rotation got quiet, and everybody moved on. Then the platform team migrated the main assistant to a newer model, which was the correct thing to do on every axis they measured, and nothing in the migration checklist mentioned tiers because <code>service_tier</code> was already set to <code>auto</code> and had been for two years. The 529s came back four months later and nobody connected the two events, because there is no error, no warning and no line on the invoice that says the tier stopped applying.",
"short_answer": """<p>One paged GET with an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=service_tier&amp;group_by[]=model</code>. Each result carries a <code>service_tier</code> of <code>priority</code>, <code>standard</code> or <code>batch</code>. Fold the tokens per model per tier and look for the models where <code>priority</code> never appears at all.</p>
<p>Then read the absence correctly, because there are two very different reasons for it. <strong>Priority Tier is not supported on Claude Opus 5, Claude Sonnet 5, Claude Mythos 5 or Claude Mythos Preview.</strong> A model on that list has no coverage to lose: <code>service_tier: "auto"</code> is accepted, the request succeeds, and it is served standard every time. That is not a setting anyone got wrong. It is a capability that does not exist for that model id.</p>
<p>The other reason is that the organization has no commitment at all &mdash; Priority Tier capacity is no longer available to purchase, so an org without an existing one will show zero <code>priority</code> tokens on <em>every</em> model. The script checks that first and says so, because reporting a per-model coverage gap in an org that has no priority capacity anywhere would be a fabricated finding.</p>
<p>No dollar figure appears in the output, and that is deliberate. <strong>Priority Tier costs are excluded from the Cost API entirely.</strong> The usage report is the only read-only source for this, and it reports tokens, not money.</p>""",
"problem": """<p>Two independent traps sit behind one field, and the field reports success in both. <code>service_tier: "auto"</code> means "use the priority commitment if it applies, otherwise serve me standard". It is a graceful fallback, which is the right design and the reason nothing ever raises. The request is not rejected for being on an unsupported model. The response is not marked. The latency is a distribution, not an alarm.</p>
<p>The first trap is model coverage. Priority Tier runs on most Claude models and specifically not on Opus 5, Sonnet 5, Mythos 5 or Mythos Preview, so the single most routine action a platform team takes &mdash; moving to a newer, better model &mdash; is also the action that silently ends priority routing. Nothing in the migration diff touches tiers, because the tier was never in the diff.</p>
<p>The second is capacity. A commitment buys a fixed input and output tokens per minute; traffic past it falls back to standard automatically, and priority requests draw on the ordinary rate limits too, so one that would breach those is declined rather than served. A commitment that was sized for last year's traffic is a commitment that mostly is not applying, and the shape of that in the report is a small non-zero priority share rather than a clean zero.</p>""",
"why": """<p><strong>This is a coverage question, not a configuration question, and they have different repairs.</strong> A published note already reads the tier you configured against the tier the invoice says served you, in both directions, and that comparison is the right one when a setting is wrong. It is the wrong one here, because nothing is set wrong: the request asks for <code>auto</code>, <code>auto</code> is valid, and the model simply is not on the list. The only repair is a model id or an acceptance that this workload runs standard, and <a href="/llm/fast-mode-silently-downgraded/">the tier-mismatch note</a> is where you go when the setting really is the problem.</p>
<p><strong>An org-wide zero and a per-model zero look identical in one row and mean opposite things.</strong> If no model anywhere in the organization reports <code>priority</code>, the finding is not about any model &mdash; it is that there is no commitment, or none that ever applies, and capacity commitments cannot be bought any more. If some models report priority and one does not, that one model is uncovered. The script establishes the org-level fact before it grades a single model, because getting this backwards produces a confident report blaming a model for something the organization never had.</p>
<p><strong>Priority spend is invisible to the cost report by design.</strong> The Cost API excludes Priority Tier costs, so there is no read-only way to put a number on what priority traffic cost or what standard fallback saved. A script that multiplied token counts by a published rate here would be inventing a figure and presenting it as a reading. This one prints tokens and shares, states that money is not available on this surface, and stops.</p>
<p><strong>A small priority share is a capacity finding and reads differently from a zero.</strong> Zero means never eligible. Fifteen per cent means eligible and mostly over the committed tokens per minute, which is a sizing conversation rather than a model conversation, and which also means your overload protection is protecting about fifteen per cent of your traffic. The two states are graded separately and carry different repairs.</p>
<p><strong>Burndown makes the committed capacity go further or less far than the raw token count suggests.</strong> Against a commitment, cache reads burn at 0.1x, five-minute cache writes at 1.25x, one-hour cache writes at 2.0x, and <code>inference_geo: "us"</code> at 1.1x on 4.6 and later. The script reports the raw tokens it read and names the multipliers rather than applying them, because it cannot see which of your traffic carried which of those attributes without regrouping the whole report.</p>""",
"steps": [
 {"h": "Use an Admin API key, provisioned read-only",
  "body": """<p>Everything under <code>/v1/organizations/*</code> rejects a workspace key outright, and an Admin key can be created read-only. This script issues one paged GET and nothing else.</p>"""},
 {"h": "Group the usage report by service_tier and model together",
  "body": """<p><code>group_by[]=service_tier&amp;group_by[]=model</code>, <code>bucket_width=1d</code>, <code>limit=31</code>, <code>starting_at</code> floored to midnight UTC. Both dimensions matter: grouped by tier alone, one covered model hides every uncovered one behind an organization-wide average that looks fine.</p>"""},
 {"h": "Establish whether the organization has any priority traffic at all",
  "body": """<p>Sum <code>priority</code> tokens across every model in the window. Zero everywhere means there is no commitment in force, and the correct output is one line saying so rather than a list of models. Capacity commitments are no longer sold, so this is a common and entirely legitimate state.</p>"""},
 {"h": "Grade each model against the documented exclusion list",
  "body": """<p>Opus 5, Sonnet 5, Mythos 5 and Mythos Preview are documented as unsupported. A model on that list with zero priority tokens is a structural gap. A model <em>not</em> on the list with zero priority tokens is something else &mdash; a request-side <code>standard_only</code>, a workspace outside the commitment, or capacity that never had headroom &mdash; and the script labels it differently rather than guessing.</p>"""},
 {"h": "Print the coverage table, and refuse to price it",
  "body": """<p>Per model: the priority, standard and batch shares, the tokens behind them, and the repair. No dollars, because Priority costs are excluded from the cost report and the number would have to be invented to appear.</p>"""},
],
"verify": """<p>Re-run after a model change lands. A model that moves from a clean zero to a real priority share is now covered; one that stays at zero after the id changed is either still on the exclusion list or the commitment does not reach that workspace.</p>
<pre><code class="language-bash">python3 anthropic_priority_tier_coverage.py --days 30
# org has priority traffic on 2 of 5 model(s), so a per-model zero is meaningful
# unsupported-model    claude-opus-5          0% priority of 812.4M token(s). Documented as not supported by Priority Tier.
#   repair: service_tier auto is accepted here and served standard every time. This is coverage, not configuration.
# partial-priority     claude-haiku-4-5-20251001  14% priority of 240.1M token(s)
#   repair: traffic past the committed tokens per minute falls back to standard. This is a sizing question.
# priority-covered     claude-opus-4-5        91% priority of 45.9M token(s)
# 5 model(s) checked, 2 finding(s)
# no dollar figure: Priority Tier costs are excluded from the cost report</code></pre>""",
"code_intro": "One paged GET and seven pure functions. The tier normaliser, which keeps an absent <code>service_tier</code> out of the standard bucket; the token weigher, which has to walk the nested <code>cache_creation</code> object; the fold; the exclusion-list matcher, written to match model families without catching <code>claude-opus-4-5</code> on the substring <code>opus-5</code>; the org-level priority check that has to run before any model is graded; the per-model verdict; and the repair lines. Nothing in it converts a token into a dollar, because the surface that would let it does not report this traffic.",
"py_file": "anthropic_priority_tier_coverage.py",
"py": '''"""Find Claude models that never report Priority Tier service.

Read only. One paged GET against the messages usage report with an Admin API
key. Nothing is sent to /v1/messages and no request body is constructed.

The finding is coverage, not misconfiguration: Priority Tier is not supported on
every model id, so a migration to a newer model can end priority routing with no
error and no diff. The absence is only visible in the usage report grouped by
service_tier, because Priority Tier costs are excluded from the cost report.

No dollar figure is printed anywhere. There is no read-only source for the money
on this surface, and a number derived from a published rate would be a guess
wearing the clothes of a reading.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_priority_tier_coverage")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

PRIORITY = "priority"
STANDARD = "standard"
BATCH = "batch"
UNKNOWN = "unknown"
TIERS = (PRIORITY, STANDARD, BATCH, UNKNOWN)

# Documented as NOT supported by Priority Tier. Matched as a family fragment
# rather than an exact id, because ids carry date suffixes. The fragments are
# written with their leading hyphen so that "opus-5" cannot match
# "claude-opus-4-5", which is a supported model and would otherwise be
# condemned by a careless substring test.
UNSUPPORTED_FAMILIES = ("-opus-5", "-sonnet-5", "-mythos-5", "-mythos-preview")

# Burndown multipliers against a commitment. Named in the output, never applied:
# the script cannot see which tokens carried which attribute without regrouping
# the entire report, and applying an average would be worse than saying nothing.
BURNDOWN = ("cache reads 0.1x", "5-minute cache writes 1.25x",
            "1-hour cache writes 2.0x", "inference_geo us 1.1x on 4.6+")

FINDINGS = ("unsupported-model", "uncovered-model", "partial-priority")


def tier(result):
    """Normalise the service_tier on one result row. Pure.

    An absent or unrecognised value becomes "unknown" and never "standard".
    Folding unclassified traffic into standard inflates the standard share,
    which is the direction that makes a coverage gap look worse than it is.
    """
    raw = str((result or {}).get("service_tier") or "").strip().lower()
    return raw if raw in (PRIORITY, STANDARD, BATCH) else UNKNOWN


def weigh(result):
    """Total billed tokens on one result row. Pure.

    cache_creation is an object rather than a scalar, so a reader that treats it
    as an int silently drops every cached write from the weight and understates
    the models that cache the most.
    """
    row = result or {}
    total = 0
    for field in ("uncached_input_tokens", "cache_read_input_tokens",
                  "output_tokens"):
        try:
            total += int(row.get(field) or 0)
        except (TypeError, ValueError):
            pass
    creation = row.get("cache_creation")
    if isinstance(creation, dict):
        for value in creation.values():
            try:
                total += int(value or 0)
            except (TypeError, ValueError):
                pass
    return total


def fold(pages):
    """Sum tokens into {model: {tier: tokens}}. Pure."""
    out = {}
    for page in pages or []:
        for bucket in (page or {}).get("data") or []:
            for result in (bucket or {}).get("results") or []:
                model = str((result or {}).get("model") or "all models")
                row = out.setdefault(model, {t: 0 for t in TIERS})
                row[tier(result)] += weigh(result)
    return out


def is_unsupported(model):
    """Is this model id on the documented Priority Tier exclusion list? Pure.

    Matched on the hyphenated family fragment. claude-opus-4-5 and
    claude-haiku-4-5 are supported and must not match; claude-opus-5 and
    claude-sonnet-5-20260101 must.
    """
    name = "-" + str(model or "").strip().lower().lstrip("-")
    return any(fragment in name for fragment in UNSUPPORTED_FAMILIES)


def org_has_priority(rows):
    """Does any model in the window report priority tokens? Pure.

    Run before any model is graded. Priority Tier capacity can no longer be
    bought, so an organization with no commitment reports zero everywhere, and
    a per-model coverage verdict in that organization would be a finding about
    nothing.
    """
    return any(int((row or {}).get(PRIORITY) or 0) > 0
               for row in (rows or {}).values())


def share(row, which):
    """One tier's share of a model's billed tokens. Pure. 0.0 when empty."""
    data = row or {}
    total = sum(int(data.get(t) or 0) for t in TIERS)
    if total <= 0:
        return 0.0
    return int(data.get(which) or 0) / float(total)


def verdict(model, row, has_priority, min_tokens=1_000_000, thin=0.60):
    """Classify one model's tier coverage. Pure. Returns (state, detail)."""
    data = row or {}
    total = sum(int(data.get(t) or 0) for t in TIERS)
    if total < min_tokens:
        return ("low-volume",
                "%d billed token(s) in the window, too few to conclude anything"
                % total)

    if not has_priority:
        return ("no-priority-in-org",
                "0%% priority of %.1fM token(s), and no model in this "
                "organization reports priority either. That is an organization "
                "without a capacity commitment, not a gap on this model."
                % (total / 1e6))

    got = share(data, PRIORITY)
    if got <= 0:
        if is_unsupported(model):
            return ("unsupported-model",
                    "0%% priority of %.1fM token(s). Documented as not "
                    "supported by Priority Tier, so service_tier auto is "
                    "accepted here and served standard every time."
                    % (total / 1e6))
        return ("uncovered-model",
                "0%% priority of %.1fM token(s), and this id is not on the "
                "documented exclusion list. Something else is keeping it off "
                "the tier: standard_only on the request, a workspace outside "
                "the commitment, or capacity that never had headroom."
                % (total / 1e6))
    if got < thin:
        return ("partial-priority",
                "%.0f%% priority of %.1fM token(s). Eligible, and mostly over "
                "the committed tokens per minute, so the rest fell back to "
                "standard." % (got * 100, total / 1e6))
    return ("priority-covered",
            "%.0f%% priority of %.1fM token(s)" % (got * 100, total / 1e6))


def repair_lines(state, model):
    """The repair for one classified model. Pure. Printed, never performed."""
    if state == "unsupported-model":
        return [
            "this is coverage, not configuration: %s cannot be served on "
            "Priority Tier at all, whatever service_tier says." % model,
            "either move the latency-sensitive traffic to a covered model id, "
            "or accept standard here and stop planning around a tier that "
            "never applies to it.",
            "standard_only is the way to deliberately preserve commitment "
            "capacity for the models that can use it.",
        ]
    if state == "uncovered-model":
        return [
            "check the request side for standard_only, and check that the "
            "workspace sending this traffic is inside the commitment.",
            "the exclusion list is not the explanation for %s, so the answer "
            "is in your own configuration or in capacity." % model,
        ]
    if state == "partial-priority":
        return [
            "the commitment is sized below this traffic. Requests past the "
            "committed input and output tokens per minute fall back to "
            "standard automatically, and one that would breach the ordinary "
            "rate limits is declined rather than served.",
            "burndown against the commitment is not one token per token: %s."
            % ", ".join(BURNDOWN),
        ]
    return []


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
    ap.add_argument("--min-tokens", type=int, default=1_000_000,
                    help="billed tokens below which no claim is made")
    ap.add_argument("--thin", type=float, default=0.60,
                    help="priority share below which coverage is called partial")
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
                       "group_by[]": ["service_tier", "model"]}))
    if not rows:
        log.info("no usage in the last %d day(s)", args.days)
        return 0

    has_priority = org_has_priority(rows)
    covered = sum(1 for row in rows.values() if int(row.get(PRIORITY) or 0) > 0)
    if has_priority:
        log.info("org has priority traffic on %d of %d model(s), so a per-model "
                 "zero is meaningful", covered, len(rows))
    else:
        log.warning("no model in this organization reported any priority "
                    "token(s) in the window. Capacity commitments are no longer "
                    "available to purchase, so this is an organization without "
                    "one rather than a gap on any single model.")

    bad = 0
    for model in sorted(rows, key=lambda m: -sum(rows[m].values())):
        state, detail = verdict(model, rows[model], has_priority,
                                args.min_tokens, args.thin)
        line = "%-20s %-26s %s" % (state, model, detail)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(state, model):
                log.warning("  repair: %s", repair)
        else:
            log.info(line)

    log.info("%d model(s) checked, %d finding(s)", len(rows), bad)
    log.info("no dollar figure: Priority Tier costs are excluded from the cost "
             "report, so tokens are the only read-only reading available here")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-priority-tier-coverage.mjs",
"js": '''/**
 * Find Claude models that never report Priority Tier service.
 *
 * Read only. One paged GET against the messages usage report with an Admin API
 * key. Nothing is sent to /v1/messages.
 *
 * The finding is coverage, not misconfiguration, and no dollar figure is
 * printed: Priority Tier costs are excluded from the cost report, so there is
 * no read-only source for the money on this surface.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const PRIORITY = 'priority';
const STANDARD = 'standard';
const BATCH = 'batch';
const UNKNOWN = 'unknown';
const TIERS = [PRIORITY, STANDARD, BATCH, UNKNOWN];

// Documented as NOT supported by Priority Tier. Family fragments carry their
// leading hyphen so that "-opus-5" cannot match claude-opus-4-5.
const UNSUPPORTED_FAMILIES = ['-opus-5', '-sonnet-5', '-mythos-5', '-mythos-preview'];

const BURNDOWN = ['cache reads 0.1x', '5-minute cache writes 1.25x',
                  '1-hour cache writes 2.0x', 'inference_geo us 1.1x on 4.6+'];

const FINDINGS = new Set(['unsupported-model', 'uncovered-model', 'partial-priority']);

/** Normalise the service_tier on one result row. Pure. Absent is never standard. */
export function tier(result) {
  const raw = String(result?.service_tier ?? '').trim().toLowerCase();
  return [PRIORITY, STANDARD, BATCH].includes(raw) ? raw : UNKNOWN;
}

/** Total billed tokens on one result row. Pure. cache_creation is an object. */
export function weigh(result) {
  const row = result ?? {};
  let total = 0;
  for (const field of ['uncached_input_tokens', 'cache_read_input_tokens',
                       'output_tokens']) {
    const n = Number(row[field] ?? 0);
    if (Number.isFinite(n)) total += Math.trunc(n);
  }
  if (row.cache_creation && typeof row.cache_creation === 'object') {
    for (const value of Object.values(row.cache_creation)) {
      const n = Number(value ?? 0);
      if (Number.isFinite(n)) total += Math.trunc(n);
    }
  }
  return total;
}

/** Sum tokens into { model: { tier: tokens } }. Pure. */
export function fold(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      for (const result of bucket?.results ?? []) {
        const model = String(result?.model ?? 'all models');
        if (!out[model]) {
          out[model] = Object.fromEntries(TIERS.map((t) => [t, 0]));
        }
        out[model][tier(result)] += weigh(result);
      }
    }
  }
  return out;
}

/** Is this model id on the documented Priority Tier exclusion list? Pure. */
export function isUnsupported(model) {
  const name = `-${String(model ?? '').trim().toLowerCase().replace(/^-+/, '')}`;
  return UNSUPPORTED_FAMILIES.some((fragment) => name.includes(fragment));
}

/**
 * Does any model in the window report priority tokens? Pure.
 * Run before any model is graded: an org with no commitment reports zero
 * everywhere, and grading a model against that is a finding about nothing.
 */
export function orgHasPriority(rows) {
  return Object.values(rows ?? {}).some((row) => Number(row?.[PRIORITY] ?? 0) > 0);
}

/** One tier's share of a model's billed tokens. Pure. 0 when empty. */
export function share(row, which) {
  const data = row ?? {};
  const total = TIERS.reduce((sum, t) => sum + Number(data[t] ?? 0), 0);
  if (total <= 0) return 0;
  return Number(data[which] ?? 0) / total;
}

/** Classify one model's tier coverage. Pure. Returns [state, detail]. */
export function verdict(model, row, hasPriority, minTokens = 1_000_000, thin = 0.6) {
  const data = row ?? {};
  const total = TIERS.reduce((sum, t) => sum + Number(data[t] ?? 0), 0);
  if (total < minTokens) {
    return ['low-volume',
      `${total} billed token(s) in the window, too few to conclude anything`];
  }
  if (!hasPriority) {
    return ['no-priority-in-org',
      `0% priority of ${(total / 1e6).toFixed(1)}M token(s), and no model in ` +
      'this organization reports priority either. That is an organization ' +
      'without a capacity commitment, not a gap on this model.'];
  }
  const got = share(data, PRIORITY);
  if (got <= 0) {
    if (isUnsupported(model)) {
      return ['unsupported-model',
        `0% priority of ${(total / 1e6).toFixed(1)}M token(s). Documented as ` +
        'not supported by Priority Tier, so service_tier auto is accepted ' +
        'here and served standard every time.'];
    }
    return ['uncovered-model',
      `0% priority of ${(total / 1e6).toFixed(1)}M token(s), and this id is ` +
      'not on the documented exclusion list. Something else is keeping it off ' +
      'the tier: standard_only on the request, a workspace outside the ' +
      'commitment, or capacity that never had headroom.'];
  }
  if (got < thin) {
    return ['partial-priority',
      `${(got * 100).toFixed(0)}% priority of ${(total / 1e6).toFixed(1)}M ` +
      'token(s). Eligible, and mostly over the committed tokens per minute, ' +
      'so the rest fell back to standard.'];
  }
  return ['priority-covered',
    `${(got * 100).toFixed(0)}% priority of ${(total / 1e6).toFixed(1)}M token(s)`];
}

/** The repair for one classified model. Pure. Printed, never performed. */
export function repairLines(state, model) {
  if (state === 'unsupported-model') {
    return [
      `this is coverage, not configuration: ${model} cannot be served on ` +
      'Priority Tier at all, whatever service_tier says.',
      'either move the latency-sensitive traffic to a covered model id, or ' +
      'accept standard here and stop planning around a tier that never ' +
      'applies to it.',
      'standard_only is the way to deliberately preserve commitment capacity ' +
      'for the models that can use it.',
    ];
  }
  if (state === 'uncovered-model') {
    return [
      'check the request side for standard_only, and check that the workspace ' +
      'sending this traffic is inside the commitment.',
      `the exclusion list is not the explanation for ${model}, so the answer ` +
      'is in your own configuration or in capacity.',
    ];
  }
  if (state === 'partial-priority') {
    return [
      'the commitment is sized below this traffic. Requests past the committed ' +
      'input and output tokens per minute fall back to standard automatically, ' +
      'and one that would breach the ordinary rate limits is declined rather ' +
      'than served.',
      `burndown against the commitment is not one token per token: ${BURNDOWN.join(', ')}.`,
    ];
  }
  return [];
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. */
export function windowStart(days, now = new Date()) {
  const midnight = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(),
                                     now.getUTCDate()));
  midnight.setUTCDate(midnight.getUTCDate() - days);
  return `${midnight.toISOString().slice(0, 19)}Z`;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, v);
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs ` +
                    'an Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const minTokens = Number(process.env.MIN_TOKENS ?? 1_000_000);

  const base = [['starting_at', windowStart(days)],
                ['bucket_width', '1d'],
                ['limit', String(Math.min(days + 1, 31))],
                ['group_by[]', 'service_tier'],
                ['group_by[]', 'model']];
  const collected = [];
  let params = base;
  for (;;) {
    const page = await get(admin, '/organizations/usage_report/messages', params);
    collected.push(page);
    if (!page?.has_more || !page?.next_page) break;
    params = [...base, ['page', page.next_page]];
  }

  const rows = fold(collected);
  const models = Object.keys(rows);
  if (models.length === 0) {
    console.log(`no usage in the last ${days} day(s)`);
    return;
  }

  const hasPriority = orgHasPriority(rows);
  const covered = models.filter((m) => Number(rows[m][PRIORITY] ?? 0) > 0).length;
  if (hasPriority) {
    console.log(`org has priority traffic on ${covered} of ${models.length} ` +
                'model(s), so a per-model zero is meaningful');
  } else {
    console.warn('no model in this organization reported any priority token(s) ' +
                 'in the window. Capacity commitments are no longer available ' +
                 'to purchase, so this is an organization without one rather ' +
                 'than a gap on any single model.');
  }

  const weight = (m) => TIERS.reduce((sum, t) => sum + Number(rows[m][t] ?? 0), 0);
  let bad = 0;
  for (const model of models.sort((a, b) => weight(b) - weight(a))) {
    const [state, detail] = verdict(model, rows[model], hasPriority, minTokens);
    const line = `${state.padEnd(20)} ${model.padEnd(26)} ${detail}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      for (const repair of repairLines(state, model)) {
        console.warn(`  repair: ${repair}`);
      }
    } else {
      console.log(line);
    }
  }

  console.log(`${models.length} model(s) checked, ${bad} finding(s)`);
  console.log('no dollar figure: Priority Tier costs are excluded from the ' +
              'cost report, so tokens are the only read-only reading here');
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two tests carry the note and they are the same data read under different org-level facts. A corpus where one model reports priority and <code>claude-opus-5</code> reports none has to come back as <code>unsupported-model</code>; the identical corpus with the priority row removed has to come back as <code>no-priority-in-org</code> on every model, because an organization without a commitment has no per-model gap to report. After that: the exclusion matcher, which has to catch <code>claude-sonnet-5-20260101</code> and leave <code>claude-opus-4-5</code> and <code>claude-haiku-4-5-20251001</code> alone; the partial share that is a sizing finding rather than a coverage one; a nested <code>cache_creation</code> object that a scalar reader would drop; and an absent <code>service_tier</code>, which must not land in the standard bucket.",
"test_py_file": "test_anthropic_priority_tier_coverage.py",
"test_py": '''from anthropic_priority_tier_coverage import (fold, is_unsupported,
                                              org_has_priority, repair_lines,
                                              share, tier, verdict, weigh)


def result(model, service_tier, tokens):
    return {"model": model, "service_tier": service_tier,
            "uncached_input_tokens": tokens}


def page(results):
    return {"data": [{"results": results}], "has_more": False}


COVERED_ORG = [page([
    result("claude-opus-5", "standard", 812_400_000),
    result("claude-opus-4-5", "priority", 41_800_000),
    result("claude-opus-4-5", "standard", 4_100_000),
])]


def test_a_model_that_never_reports_priority_has_no_coverage():
    # The note in one assertion. The org clearly has a commitment, because
    # another model is being served on it, so this model's clean zero is a
    # fact about the model rather than about the organization.
    rows = fold(COVERED_ORG)
    assert org_has_priority(rows) is True
    state, detail = verdict("claude-opus-5", rows["claude-opus-5"], True)
    assert state == "unsupported-model"
    assert "not supported by Priority Tier" in detail
    assert verdict("claude-opus-4-5", rows["claude-opus-4-5"], True)[0] == \\
        "priority-covered"
    assert any("coverage, not configuration" in line
               for line in repair_lines(state, "claude-opus-5"))


def test_an_org_with_no_commitment_is_not_a_per_model_finding():
    # Identical traffic with the priority row removed. Nothing about the model
    # changed; the correct verdict did, because there is no commitment anywhere
    # and Priority capacity can no longer be bought.
    rows = fold([page([
        result("claude-opus-5", "standard", 812_400_000),
        result("claude-opus-4-5", "standard", 45_900_000),
    ])])
    assert org_has_priority(rows) is False
    for model in rows:
        state, detail = verdict(model, rows[model], False)
        assert state == "no-priority-in-org"
        assert "without a capacity commitment" in detail
        assert repair_lines(state, model) == []


def test_the_exclusion_list_matches_families_and_not_neighbours():
    assert is_unsupported("claude-opus-5") is True
    assert is_unsupported("claude-sonnet-5-20260101") is True
    assert is_unsupported("claude-mythos-5") is True
    assert is_unsupported("claude-mythos-preview") is True
    # The ones a careless substring test destroys.
    assert is_unsupported("claude-opus-4-5") is False
    assert is_unsupported("claude-haiku-4-5-20251001") is False
    assert is_unsupported("claude-sonnet-4-6") is False
    assert is_unsupported("claude-fable-5") is False
    assert is_unsupported(None) is False


def test_a_model_off_the_list_with_zero_priority_is_a_different_finding():
    rows = fold([page([
        result("claude-haiku-4-5-20251001", "standard", 240_000_000),
        result("claude-opus-4-5", "priority", 40_000_000),
    ])])
    state, detail = verdict("claude-haiku-4-5-20251001",
                            rows["claude-haiku-4-5-20251001"], True)
    assert state == "uncovered-model"
    assert "not on the documented exclusion list" in detail


def test_a_thin_priority_share_is_a_sizing_finding():
    rows = fold([page([
        result("claude-haiku-4-5-20251001", "priority", 14_000_000),
        result("claude-haiku-4-5-20251001", "standard", 86_000_000),
    ])])
    state, detail = verdict("claude-haiku-4-5-20251001",
                            rows["claude-haiku-4-5-20251001"], True)
    assert state == "partial-priority"
    assert "14% priority" in detail
    assert any("burndown" in line for line in
               repair_lines(state, "claude-haiku-4-5-20251001"))


def test_cache_creation_is_an_object_and_all_of_it_counts():
    row = {"uncached_input_tokens": 100, "cache_read_input_tokens": 10,
           "output_tokens": 5,
           "cache_creation": {"ephemeral_5m_input_tokens": 40,
                              "ephemeral_1h_input_tokens": 20}}
    assert weigh(row) == 175
    assert weigh({"uncached_input_tokens": "not a number"}) == 0
    assert weigh({"cache_creation": 12}) == 0
    assert weigh(None) == 0


def test_an_absent_service_tier_never_lands_in_standard():
    assert tier({"service_tier": "priority"}) == "priority"
    assert tier({"service_tier": "BATCH"}) == "batch"
    assert tier({}) == "unknown"
    assert tier({"service_tier": "flex"}) == "unknown"
    rows = fold([page([result("claude-opus-5", None, 5_000_000)])])
    assert rows["claude-opus-5"]["standard"] == 0
    assert rows["claude-opus-5"]["unknown"] == 5_000_000
    assert share(rows["claude-opus-5"], "standard") == 0.0


def test_too_little_traffic_is_never_a_verdict():
    rows = fold([page([result("claude-opus-5", "standard", 900)])])
    state, detail = verdict("claude-opus-5", rows["claude-opus-5"], True)
    assert state == "low-volume"
    assert "too few to conclude" in detail
    assert fold([]) == {} and fold(None) == {}
    assert org_has_priority({}) is False
''',
"test_js_file": "anthropic-priority-tier-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fold, isUnsupported, orgHasPriority, repairLines, share, tier,
         verdict, weigh, windowStart }
  from './anthropic-priority-tier-coverage.mjs';

const result = (model, serviceTier, tokens) =>
  ({ model, service_tier: serviceTier, uncached_input_tokens: tokens });

const page = (results) => ({ data: [{ results }], has_more: false });

const COVERED_ORG = [page([
  result('claude-opus-5', 'standard', 812_400_000),
  result('claude-opus-4-5', 'priority', 41_800_000),
  result('claude-opus-4-5', 'standard', 4_100_000),
])];

test('a model that never reports priority has no coverage', () => {
  const rows = fold(COVERED_ORG);
  assert.equal(orgHasPriority(rows), true);
  const [state, detail] = verdict('claude-opus-5', rows['claude-opus-5'], true);
  assert.equal(state, 'unsupported-model');
  assert.match(detail, /not supported by Priority Tier/);
  assert.equal(verdict('claude-opus-4-5', rows['claude-opus-4-5'], true)[0],
               'priority-covered');
  assert.ok(repairLines(state, 'claude-opus-5')
    .some((line) => line.includes('coverage, not configuration')));
});

test('an org with no commitment is not a per-model finding', () => {
  const rows = fold([page([
    result('claude-opus-5', 'standard', 812_400_000),
    result('claude-opus-4-5', 'standard', 45_900_000),
  ])]);
  assert.equal(orgHasPriority(rows), false);
  for (const model of Object.keys(rows)) {
    const [state, detail] = verdict(model, rows[model], false);
    assert.equal(state, 'no-priority-in-org');
    assert.match(detail, /without a capacity commitment/);
    assert.deepEqual(repairLines(state, model), []);
  }
});

test('the exclusion list matches families and not neighbours', () => {
  assert.equal(isUnsupported('claude-opus-5'), true);
  assert.equal(isUnsupported('claude-sonnet-5-20260101'), true);
  assert.equal(isUnsupported('claude-mythos-5'), true);
  assert.equal(isUnsupported('claude-mythos-preview'), true);
  assert.equal(isUnsupported('claude-opus-4-5'), false);
  assert.equal(isUnsupported('claude-haiku-4-5-20251001'), false);
  assert.equal(isUnsupported('claude-sonnet-4-6'), false);
  assert.equal(isUnsupported('claude-fable-5'), false);
  assert.equal(isUnsupported(null), false);
});

test('a model off the list with zero priority is a different finding', () => {
  const rows = fold([page([
    result('claude-haiku-4-5-20251001', 'standard', 240_000_000),
    result('claude-opus-4-5', 'priority', 40_000_000),
  ])]);
  const [state, detail] = verdict('claude-haiku-4-5-20251001',
    rows['claude-haiku-4-5-20251001'], true);
  assert.equal(state, 'uncovered-model');
  assert.match(detail, /not on the documented exclusion list/);
});

test('a thin priority share is a sizing finding', () => {
  const rows = fold([page([
    result('claude-haiku-4-5-20251001', 'priority', 14_000_000),
    result('claude-haiku-4-5-20251001', 'standard', 86_000_000),
  ])]);
  const [state, detail] = verdict('claude-haiku-4-5-20251001',
    rows['claude-haiku-4-5-20251001'], true);
  assert.equal(state, 'partial-priority');
  assert.match(detail, /14% priority/);
  assert.ok(repairLines(state, 'claude-haiku-4-5-20251001')
    .some((line) => line.includes('burndown')));
});

test('cache_creation is an object and all of it counts', () => {
  assert.equal(weigh({ uncached_input_tokens: 100, cache_read_input_tokens: 10,
                       output_tokens: 5,
                       cache_creation: { ephemeral_5m_input_tokens: 40,
                                         ephemeral_1h_input_tokens: 20 } }), 175);
  assert.equal(weigh({ uncached_input_tokens: 'not a number' }), 0);
  assert.equal(weigh({ cache_creation: 12 }), 0);
  assert.equal(weigh(null), 0);
});

test('an absent service_tier never lands in standard', () => {
  assert.equal(tier({ service_tier: 'priority' }), 'priority');
  assert.equal(tier({ service_tier: 'BATCH' }), 'batch');
  assert.equal(tier({}), 'unknown');
  assert.equal(tier({ service_tier: 'flex' }), 'unknown');
  const rows = fold([page([result('claude-opus-5', null, 5_000_000)])]);
  assert.equal(rows['claude-opus-5'].standard, 0);
  assert.equal(rows['claude-opus-5'].unknown, 5_000_000);
  assert.equal(share(rows['claude-opus-5'], 'standard'), 0);
});

test('too little traffic is never a verdict', () => {
  const rows = fold([page([result('claude-opus-5', 'standard', 900)])]);
  const [state, detail] = verdict('claude-opus-5', rows['claude-opus-5'], true);
  assert.equal(state, 'low-volume');
  assert.match(detail, /too few to conclude/);
  assert.deepEqual(fold([]), {});
  assert.deepEqual(fold(null), {});
  assert.equal(orgHasPriority({}), false);
});

test('the window start is floored to midnight utc', () => {
  assert.equal(windowStart(30, new Date('2026-08-31T17:45:12Z')),
               '2026-08-01T00:00:00Z');
  assert.equal(windowStart(0, new Date('2026-08-31T17:45:12Z')),
               '2026-08-31T00:00:00Z');
});
''',
"faq": [
 ("Which Claude models does Priority Tier not support?",
  "Claude Opus 5, Claude Sonnet 5, Claude Mythos 5 and Claude Mythos Preview. Everything else that is generally available is covered. The practical consequence is that the most routine platform action there is, moving to a newer and better model, is also the action that ends priority routing, and it does so with no error, no warning and no diff to review, because service_tier is set once and never mentioned in a migration."),
 ("Why does the script not tell me what Priority Tier is costing me?",
  "Because there is no read-only source for it. Priority Tier costs are excluded from the Cost API entirely, so a number in that output would have to be produced by multiplying token counts from the usage report by a rate copied off a pricing page. That is a guess with a decimal point on it. The script prints tokens and shares, says plainly that money is not available on this surface, and leaves the arithmetic to you if you want it."),
 ("Can I just buy more priority capacity?",
  "Not any more. Priority Tier capacity commitments are no longer available for purchase, so only organizations with an existing commitment have any at all. That is why the script establishes whether the organization has any priority traffic before it grades a single model: in an org without a commitment, every model reports zero, and calling that a coverage gap on one model would be inventing a fault."),
 ("My priority share is fifteen per cent rather than zero. Is that broken?",
  "No, it is undersized. A commitment buys a fixed number of input and output tokens per minute; traffic beyond that falls back to standard automatically rather than failing, and a priority request that would breach your ordinary rate limits is declined rather than served. Fifteen per cent means the tier is working and covering fifteen per cent of your traffic, which is worth knowing before the next overload incident is blamed on the provider."),
 ("Does the burndown really not match the token count?",
  "It does not. Against a commitment, cache reads burn at 0.1x, five-minute cache writes at 1.25x, one-hour cache writes at 2.0x, and inference_geo set to us adds 1.1x on 4.6 and later models. The script names these and does not apply them, because it cannot see which of your tokens carried which attribute without regrouping the whole report, and an averaged multiplier would be a worse number than none."),
],
"related": [REL_FAST_MODE, REL_529, REL_LIMITER],
"citations": [CITE_CL_SERVICE_TIERS, CITE_CL_USAGE_REPORT, CITE_CL_USAGE_API,
              CITE_CL_RATE_LIMITS],
},
{
"slug": "long-context-gated-on-obsolete-beta",
"title": "The 1M context window is capped at 200k in your own code",
"description": "GET /v1/models gives max_input_tokens per id. Compare it with the ceiling your application enforces: a bought 1M window is often capped in software.",
"h1": "The 1M context window is capped at 200k in your own code",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic context-1m-2025-08-07 beta",
             "claude max_input_tokens models api",
             "claude 1m context default no beta header",
             "sonnet 4.5 1m context retired",
             "claude long context premium removed"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a workspace key, plus a small JSON file describing the ceiling your own code enforces per model id. The API cannot read your source, so the ceiling has to be declared.",
"lead": "The long-context work took a quarter. There is a constant called <code>MAX_CONTEXT_TOKENS</code>, there is a guard that truncates the retrieved documents before they reach it, there is a branch that routes anything over the line to a summarise-first path, and there is a comment above all of it citing a beta header. Every one of those was correct when it was written. The model ids in the config have changed four times since, the window they now report is a million tokens, and the constant still says two hundred thousand, so the truncation still fires, the summarise path still runs, and the capability the company is paying for stops at the same place it stopped eighteen months ago.",
"short_answer": """<p>Ask the API what the window actually is, per id. <code>GET /v1/models/{model_id}</code> with a <strong>workspace key</strong> returns <code>max_input_tokens</code>, and it is authoritative: <code>200000</code> or <code>1000000</code>, no interpretation required. Then compare it with the ceiling your application enforces, which you have to declare in a small config file, because nothing in either API can read your source tree.</p>
<p>Three things go wrong at that comparison and they have three different repairs. A model reporting <code>1000000</code> against a code ceiling of <code>200000</code> is <strong>a window bought and capped in software</strong>. A model reporting <code>1000000</code> where the code still sends <code>anthropic-beta: context-1m-2025-08-07</code> has an <strong>inert header</strong>: 1M is the default on Opus 5, Opus 4.8, 4.7 and 4.6, Sonnet 5 and 4.6, Fable 5, Mythos 5 and Mythos Preview, and the beta does nothing. A model reporting <code>200000</code> where the code sends that same header is worse: the beta was <strong>retired for Claude Sonnet 4.5 and Claude Sonnet 4 on 30 April 2026</strong>, so anything over 200k now returns <code>400 invalid_request_error</code> with <em>prompt is too long</em>, header or no header.</p>
<p>The fourth thing is a price branch. There is no long-context premium on current models: a 900k-token request bills at the same per-token rate as a 9k one, and the dedicated 1M rate limits were removed too. Code that still charges or throttles for a premium is enforcing a rule that no longer exists.</p>
<p>Probing the header proves nothing, so this script does not. <code>GET /v1/models</code> with <code>anthropic-beta: context-1m-2025-08-07</code> still returns <code>200</code>, because the beta name is still recognised. Acceptance is not effect.</p>""",
"problem": """<p>This is the failure mode of a capability that graduated. When the 1M window was a beta it needed a header, it had its own rate limits, and on some models it carried a premium, so every serious integration grew code to handle all three. Then it became the default, the beta was retired on the models where it had been a beta, the separate limits were removed and the premium went away &mdash; and none of those changes produce an error in an application that is still being careful about them. Careful code keeps working. It just keeps working at 200k.</p>
<p>What makes it durable is that the constant is defensible. Two hundred thousand is a real number, it was correct, and it is protecting you from a real error on the models where it still applies. Nobody deletes a guard that has never failed. Meanwhile the model ids in the config rotate every few months as part of ordinary maintenance, and each rotation moves the true ceiling without touching the enforced one, because they live in different files and nothing joins them.</p>
<p>The visible symptoms are all downstream and all easy to misattribute. Documents get truncated, so retrieval quality is blamed. A summarise-first path runs on inputs that never needed it, so latency and cost are blamed on the summariser. And on Sonnet 4.5 or Sonnet 4 the error is a real 400 that says <em>prompt is too long</em> while the request carries the header that was supposed to prevent exactly that, which reads as a provider bug and is not one.</p>""",
"why": """<p><strong>The model object is the only source that cannot go stale.</strong> Anthropic's <code>GET /v1/models/{id}</code> returns <code>max_input_tokens</code> and <code>max_output_tokens</code> per id. A docs table lags, a blog post is a snapshot, and a constant in your repo is a memory of a fact rather than the fact. Read the number from the id you actually send and the whole class of drift disappears.</p>
<p><strong>The header probe is a non-signal, and knowing that saves you a wrong conclusion.</strong> Sending <code>anthropic-beta: context-1m-2025-08-07</code> on a read-only <code>GET /v1/models</code> returns <code>200</code> whether or not the beta does anything on any model, because the name is still valid. A script that treated that <code>200</code> as confirmation would report health on precisely the configuration that is broken. This one refuses to make the call and says why.</p>
<p><strong>A ceiling that is too low and a ceiling that is too high are opposite findings.</strong> Enforcing 200k against a 1M model wastes the window silently. Enforcing 1M against a 200k model produces a hard 400 on the first long request, which is loud, and which <a href="/llm/prompt-too-long-context-overflow/">the overflow note</a> covers properly by counting an actual payload. This script grades both, because they come out of the same comparison, and hands the second one on rather than restating it.</p>
<p><strong>The output ceiling is a different number and a different note.</strong> Every model with a 1M window is still capped at 128k output tokens per request, and a configured <code>max_tokens</code> above a model's own <code>max_output_tokens</code> is its own failure with its own repair. That belongs to <a href="/llm/max-tokens-above-model-cap/">the output-cap note</a>, so this script prints the reported output ceiling as context and does not grade it.</p>
<p><strong>This is not the same question as how much long traffic you send.</strong> Grouping the usage report by <code>context_window</code> tells you how much of your input actually crosses 200k, which is a size alarm about prefixes that grow; <a href="/llm/long-context-requests-unwatched/">that note</a> owns it. This one is about a ceiling: a window that is available, paid for, and unreachable because a constant in your own code says so. You can have the second problem while sending no long requests at all &mdash; in fact that is exactly what it looks like.</p>""",
"steps": [
 {"h": "Write down the ceiling your code actually enforces",
  "body": """<p>A small JSON file keyed by model id: the input ceiling the application applies, any <code>anthropic-beta</code> values it still sends, and whether a long-context price or throttle branch still exists. Nothing in either API can read your source, so this half of the comparison has to be declared. Declaring it is also the first time most teams look at all four facts together.</p>"""},
 {"h": "Read max_input_tokens per id from the Models API",
  "body": """<p><code>GET /v1/models/{model_id}</code> with a workspace key, one call per id in the config. The ids are validated before they reach the URL, because a value out of a config file becoming a path segment is one typo away from requesting something else entirely. A 404 means the id no longer resolves, which is a different note.</p>"""},
 {"h": "Compare the two ceilings in both directions",
  "body": """<p>Reported 1M against enforced 200k is the headline: the window is bought and capped. Enforced above reported is the opposite fault and will 400 on the first long request. Equal is aligned, and gets one quiet line.</p>"""},
 {"h": "Grade every beta header against the model it is sent on",
  "body": """<p>On a model that reports <code>1000000</code>, <code>context-1m-2025-08-07</code> is inert and should be deleted. On a model that reports <code>200000</code>, the same header is a retired beta and the code around it is relying on something that stopped working on 30 April 2026.</p>"""},
 {"h": "Print the repair per model, including the branches to delete",
  "body": """<p>The constant to raise, the header to remove, the premium branch that prices something that no longer costs extra, and the separate long-context rate limit that no longer exists. All printed. Raising a context ceiling is a deploy with a blast radius and an owner.</p>"""},
],
"verify": """<p>Re-run after the constant moves. The reported window will not change &mdash; it was never the thing that was wrong &mdash; but every model should come back <code>aligned</code>, and the truncation path should stop firing on inputs it was never supposed to catch.</p>
<pre><code class="language-bash">python3 anthropic_context_window_cap.py --config context_rules.json
# capped-in-code       claude-opus-5        model reports 1000000, code enforces 200000: 800000 token(s) bought and unreachable
#   repair: raise the enforced ceiling to the reported window, then delete the truncation path that exists to serve the old one.
# inert-beta-header    claude-opus-5        context-1m-2025-08-07 is sent here and does nothing: 1M is the default on this model
# retired-beta         claude-sonnet-4-5    model reports 200000 and the beta was retired for this family on 2026-04-30
#   repair: over 200k this id now returns 400 prompt is too long, header or not. The path forward is Sonnet 4.6 or later.
# phantom-premium      claude-opus-5        a long-context price branch is declared, and there is no long-context premium
# aligned              claude-haiku-4-5-20251001  model reports 200000, code enforces 200000
# 4 model(s) checked, 3 finding(s). Output ceilings are reported and not graded.</code></pre>""",
"code_intro": "One GET per configured model id and no probe, because the probe would lie. Seven pure functions: the rules parser, which is also the guard that stops a config value becoming a URL path segment; the window and output readers, which return <code>None</code> rather than a default when the field is absent; the shortfall arithmetic; the beta grader, which needs the reported window to know whether a header is inert or retired; the premium grader; and the audit, which returns a <em>list</em> of findings per model rather than one state, because a single misconfigured id routinely has three of them at once.",
"py_file": "anthropic_context_window_cap.py",
"py": '''"""Compare the context window a Claude model reports with the one your code enforces.

Read only. One GET per configured model id against the Models API with a
workspace key. No message is ever sent and no long request is constructed.

The API cannot read your source tree, so the enforced ceiling, the beta headers
still in the request path and any surviving long-context price branch are
declared in a small JSON file. That declaration is half the comparison and the
script says so rather than pretending to have discovered it.

There is deliberately no beta-header probe. GET /v1/models with
anthropic-beta: context-1m-2025-08-07 returns 200 whether or not the beta does
anything on any model, because the name is still recognised. Acceptance is not
effect, and a script that read that 200 as confirmation would report health on
exactly the configuration that is broken.

Every repair is printed. Raising a context ceiling is a deploy.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_context_window_cap")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

BETA_1M = "context-1m-2025-08-07"
BETA_RETIRED_ON = "2026-04-30"
STANDARD_WINDOW = 200_000
LONG_WINDOW = 1_000_000

FINDINGS = ("capped-in-code", "ceiling-below-model", "cap-above-model",
            "inert-beta-header", "retired-beta", "phantom-premium")


def _int(value):
    """Read a positive integer, or None. Pure. Absent is never zero.

    None and 0 mean very different things about a context window, and a reader
    that collapses them reports a model with no window rather than a model that
    did not say.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def valid_model_id(model_id):
    """Is this a plausible model id? Pure.

    The guard that stops a line of a config file becoming a URL path segment.
    Model ids are letters, digits, hyphens, dots and underscores, and anything
    else is discarded rather than sent.
    """
    text = str(model_id or "").strip()
    if not text or len(text) > 128:
        return False
    if not text[0].isalpha():
        return False
    return all(ch.isalnum() or ch in "-._" for ch in text)


def parse_rules(config):
    """Read the declared per-model rules. Pure. Invalid ids are dropped.

    Each rule carries the enforced input ceiling, any anthropic-beta values the
    request path still sends, and whether a long-context price or throttle
    branch still exists.
    """
    rules = {}
    for model_id, raw in (config or {}).items():
        if not valid_model_id(model_id):
            continue
        row = raw if isinstance(raw, dict) else {}
        betas = row.get("beta_headers")
        if isinstance(betas, str):
            betas = [betas]
        rules[str(model_id).strip()] = {
            "cap": _int(row.get("max_input_tokens")),
            "betas": [str(b).strip().lower() for b in (betas or [])
                      if str(b or "").strip()],
            "premium": bool(row.get("long_context_premium")),
        }
    return rules


def reported_window(model):
    """max_input_tokens off the model object. Pure. None when absent."""
    return _int((model or {}).get("max_input_tokens"))


def reported_output(model):
    """max_output_tokens off the model object. Pure. Context, never graded here."""
    return _int((model or {}).get("max_output_tokens"))


def shortfall(reported, enforced):
    """Tokens of window that exist and cannot be reached. Pure. None when unknown."""
    if reported is None or enforced is None:
        return None
    return max(0, reported - enforced)


def grade_ceiling(reported, enforced):
    """The enforced ceiling against the reported window. Pure. (state, detail) or None."""
    if reported is None:
        return ("window-not-reported",
                "the model object carried no max_input_tokens, so no claim is "
                "made about the enforced ceiling")
    if enforced is None:
        return None
    if enforced > reported:
        return ("cap-above-model",
                "model reports %d, code enforces %d: the first request over "
                "the reported window returns 400 prompt is too long"
                % (reported, enforced))
    gap = shortfall(reported, enforced)
    if gap == 0:
        return ("aligned", "model reports %d, code enforces %d"
                % (reported, enforced))
    if reported >= LONG_WINDOW and enforced <= STANDARD_WINDOW:
        return ("capped-in-code",
                "model reports %d, code enforces %d: %d token(s) of window "
                "bought and unreachable" % (reported, enforced, gap))
    return ("ceiling-below-model",
            "model reports %d, code enforces %d: %d token(s) of window left "
            "unused" % (reported, enforced, gap))


def grade_betas(reported, betas):
    """Every declared beta header against the window the model reports. Pure.

    The same header name is two different findings depending on the model. On a
    model that already defaults to 1M it is inert. On one that reports the
    standard window it is a retired beta, and the code around it is relying on
    something that stopped working.
    """
    out = []
    for beta in betas or []:
        if beta != BETA_1M:
            continue
        if reported is None:
            continue
        if reported >= LONG_WINDOW:
            out.append(("inert-beta-header",
                        "%s is sent here and does nothing: the 1M window is "
                        "the default on this model and needs no header"
                        % BETA_1M))
        else:
            out.append(("retired-beta",
                        "model reports %d and %s was retired for the Sonnet "
                        "4.5 and Sonnet 4 family on %s: over the standard "
                        "window this id now returns 400, header or not"
                        % (reported, BETA_1M, BETA_RETIRED_ON)))
    return out


def grade_premium(reported, premium):
    """A surviving long-context price or throttle branch. Pure. None when absent."""
    if not premium:
        return None
    if reported is None or reported < LONG_WINDOW:
        return None
    return ("phantom-premium",
            "a long-context price or throttle branch is declared for this "
            "model, and there is no long-context premium: a 900k-token request "
            "bills at the same per-token rate as a 9k one, and the dedicated "
            "1M rate limits were removed")


def audit(model, rule):
    """Every finding for one model. Pure. Returns a list of (state, detail).

    A list rather than a single state on purpose. One stale id routinely
    carries three at once - a ceiling frozen at 200k, an inert header, and a
    premium branch pricing something that is free - and collapsing them to the
    first would hide two repairs behind one line.
    """
    rule = rule or {}
    reported = reported_window(model)
    out = []
    ceiling = grade_ceiling(reported, rule.get("cap"))
    if ceiling is not None:
        out.append(ceiling)
    out.extend(grade_betas(reported, rule.get("betas")))
    premium = grade_premium(reported, rule.get("premium"))
    if premium is not None:
        out.append(premium)
    return out


def repair_lines(state, model_id):
    """The repair for one finding. Pure. Printed, never performed."""
    if state == "capped-in-code":
        return [
            "raise the enforced ceiling for %s to the window the model "
            "reports, then delete the truncation path that exists to serve "
            "the old one." % model_id,
            "read the ceiling from the model object at start-up instead of "
            "hardcoding it, and this cannot drift again when the id rotates.",
        ]
    if state == "ceiling-below-model":
        return ["the enforced ceiling for %s is below the reported window. "
                "Confirm that is deliberate rather than inherited." % model_id]
    if state == "cap-above-model":
        return ["this direction fails loudly rather than quietly: count a real "
                "payload against the reported window before you send it."]
    if state == "inert-beta-header":
        return ["delete %s from the request path for %s. It is not harmful and "
                "it is not doing anything, and leaving it in is what keeps the "
                "rest of the obsolete branch alive." % (BETA_1M, model_id)]
    if state == "retired-beta":
        return ["over the standard window this id now returns 400 whatever the "
                "header says. The path forward is a 4.6 or later id, where 1M "
                "is the default and no header is involved."]
    if state == "phantom-premium":
        return ["delete the premium branch and the separate long-context "
                "throttle. Standard account rate limits apply at every context "
                "length now."]
    return []


def get(session, path):
    r = session.get(API + path, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: ANTHROPIC_API_KEY needs to be a "
                         "workspace key that can read the Models API"
                         % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, metavar="FILE",
                    help="JSON: model id to the ceiling your code enforces, "
                         "the anthropic-beta values it sends, and whether a "
                         "long-context price branch still exists")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key that can read the "
                  "Models API")
        return 2

    try:
        with open(args.config, "r", encoding="utf-8") as fh:
            rules = parse_rules(json.load(fh))
    except (OSError, ValueError) as exc:
        log.error("could not read %s: %s", args.config, exc)
        return 2
    if not rules:
        log.error("no valid model ids in %s", args.config)
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})
    log.info("no beta-header probe is made: %s is still a recognised name, so "
             "a 200 would prove the name is valid and nothing about its effect",
             BETA_1M)

    bad = 0
    for model_id in sorted(rules):
        model = get(session, "/models/" + model_id)
        if model is None:
            log.warning("%-20s %-26s the id no longer resolves on the Models "
                        "API, which is a retirement rather than a ceiling "
                        "problem", "unknown-model-id", model_id)
            bad += 1
            continue

        for state, detail in audit(model, rules[model_id]):
            line = "%-20s %-26s %s" % (state, model_id, detail)
            if state in FINDINGS:
                bad += 1
                log.warning(line)
                for repair in repair_lines(state, model_id):
                    log.warning("  repair: %s", repair)
            else:
                log.info(line)

        out = reported_output(model)
        if out is not None:
            log.info("%-20s %-26s reports max_output_tokens %d, which is a "
                     "separate ceiling and is not graded here",
                     "output-ceiling", model_id, out)

    log.info("%d model(s) checked, %d finding(s)", len(rules), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-context-window-cap.mjs",
"js": '''/**
 * Compare the context window a Claude model reports with the one your code enforces.
 *
 * Read only. One GET per configured model id against the Models API with a
 * workspace key. No message is ever sent.
 *
 * There is deliberately no beta-header probe. GET /v1/models with
 * anthropic-beta: context-1m-2025-08-07 returns 200 whether or not the beta
 * does anything, because the name is still recognised. Acceptance is not
 * effect.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const BETA_1M = 'context-1m-2025-08-07';
const BETA_RETIRED_ON = '2026-04-30';
const STANDARD_WINDOW = 200_000;
const LONG_WINDOW = 1_000_000;

const FINDINGS = new Set(['capped-in-code', 'ceiling-below-model',
                          'cap-above-model', 'inert-beta-header',
                          'retired-beta', 'phantom-premium']);

/** Read a positive integer, or null. Pure. Absent is never zero. */
export function readInt(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  const whole = Math.trunc(n);
  return whole > 0 ? whole : null;
}

/**
 * Is this a plausible model id? Pure.
 * The guard that stops a config value becoming a URL path segment.
 */
export function validModelId(modelId) {
  const text = String(modelId ?? '').trim();
  if (!text || text.length > 128) return false;
  return /^[A-Za-z][A-Za-z0-9._-]*$/.test(text);
}

/** Read the declared per-model rules. Pure. Invalid ids are dropped. */
export function parseRules(config) {
  const rules = {};
  for (const [modelId, raw] of Object.entries(config ?? {})) {
    if (!validModelId(modelId)) continue;
    const row = raw && typeof raw === 'object' ? raw : {};
    let betas = row.beta_headers;
    if (typeof betas === 'string') betas = [betas];
    rules[String(modelId).trim()] = {
      cap: readInt(row.max_input_tokens),
      betas: (betas ?? []).map((b) => String(b ?? '').trim().toLowerCase())
        .filter((b) => b.length > 0),
      premium: Boolean(row.long_context_premium),
    };
  }
  return rules;
}

/** max_input_tokens off the model object. Pure. Null when absent. */
export function reportedWindow(model) {
  return readInt(model?.max_input_tokens);
}

/** max_output_tokens off the model object. Pure. Context, never graded here. */
export function reportedOutput(model) {
  return readInt(model?.max_output_tokens);
}

/** Tokens of window that exist and cannot be reached. Pure. Null when unknown. */
export function shortfall(reported, enforced) {
  if (reported === null || enforced === null) return null;
  return Math.max(0, reported - enforced);
}

/** The enforced ceiling against the reported window. Pure. [state, detail] or null. */
export function gradeCeiling(reported, enforced) {
  if (reported === null) {
    return ['window-not-reported',
      'the model object carried no max_input_tokens, so no claim is made ' +
      'about the enforced ceiling'];
  }
  if (enforced === null) return null;
  if (enforced > reported) {
    return ['cap-above-model',
      `model reports ${reported}, code enforces ${enforced}: the first ` +
      'request over the reported window returns 400 prompt is too long'];
  }
  const gap = shortfall(reported, enforced);
  if (gap === 0) {
    return ['aligned', `model reports ${reported}, code enforces ${enforced}`];
  }
  if (reported >= LONG_WINDOW && enforced <= STANDARD_WINDOW) {
    return ['capped-in-code',
      `model reports ${reported}, code enforces ${enforced}: ${gap} token(s) ` +
      'of window bought and unreachable'];
  }
  return ['ceiling-below-model',
    `model reports ${reported}, code enforces ${enforced}: ${gap} token(s) ` +
    'of window left unused'];
}

/** Every declared beta header against the window the model reports. Pure. */
export function gradeBetas(reported, betas) {
  const out = [];
  for (const beta of betas ?? []) {
    if (beta !== BETA_1M || reported === null) continue;
    if (reported >= LONG_WINDOW) {
      out.push(['inert-beta-header',
        `${BETA_1M} is sent here and does nothing: the 1M window is the ` +
        'default on this model and needs no header']);
    } else {
      out.push(['retired-beta',
        `model reports ${reported} and ${BETA_1M} was retired for the Sonnet ` +
        `4.5 and Sonnet 4 family on ${BETA_RETIRED_ON}: over the standard ` +
        'window this id now returns 400, header or not']);
    }
  }
  return out;
}

/** A surviving long-context price or throttle branch. Pure. Null when absent. */
export function gradePremium(reported, premium) {
  if (!premium) return null;
  if (reported === null || reported < LONG_WINDOW) return null;
  return ['phantom-premium',
    'a long-context price or throttle branch is declared for this model, and ' +
    'there is no long-context premium: a 900k-token request bills at the same ' +
    'per-token rate as a 9k one, and the dedicated 1M rate limits were removed'];
}

/**
 * Every finding for one model. Pure. Returns a list of [state, detail].
 * A list rather than one state: a stale id routinely carries a frozen ceiling,
 * an inert header and a phantom premium at the same time.
 */
export function audit(model, rule) {
  const row = rule ?? {};
  const reported = reportedWindow(model);
  const out = [];
  const ceiling = gradeCeiling(reported, row.cap ?? null);
  if (ceiling !== null) out.push(ceiling);
  out.push(...gradeBetas(reported, row.betas));
  const premium = gradePremium(reported, row.premium);
  if (premium !== null) out.push(premium);
  return out;
}

/** The repair for one finding. Pure. Printed, never performed. */
export function repairLines(state, modelId) {
  if (state === 'capped-in-code') {
    return [
      `raise the enforced ceiling for ${modelId} to the window the model ` +
      'reports, then delete the truncation path that exists to serve the old one.',
      'read the ceiling from the model object at start-up instead of ' +
      'hardcoding it, and this cannot drift again when the id rotates.',
    ];
  }
  if (state === 'ceiling-below-model') {
    return [`the enforced ceiling for ${modelId} is below the reported window. ` +
            'Confirm that is deliberate rather than inherited.'];
  }
  if (state === 'cap-above-model') {
    return ['this direction fails loudly rather than quietly: count a real ' +
            'payload against the reported window before you send it.'];
  }
  if (state === 'inert-beta-header') {
    return [`delete ${BETA_1M} from the request path for ${modelId}. It is not ` +
            'harmful and it is not doing anything, and leaving it in is what ' +
            'keeps the rest of the obsolete branch alive.'];
  }
  if (state === 'retired-beta') {
    return ['over the standard window this id now returns 400 whatever the ' +
            'header says. The path forward is a 4.6 or later id, where 1M is ' +
            'the default and no header is involved.'];
  }
  if (state === 'phantom-premium') {
    return ['delete the premium branch and the separate long-context throttle. ' +
            'Standard account rate limits apply at every context length now.'];
  }
  return [];
}

async function get(key, path) {
  const res = await fetch(API + path, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: ANTHROPIC_API_KEY needs to ` +
                    'be a workspace key that can read the Models API');
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key that can read the ' +
                  'Models API');
    process.exitCode = 2;
    return;
  }
  const file = process.argv.slice(2).find((a) => !a.startsWith('--'));
  if (!file) {
    console.error('pass a JSON file of per-model rules: enforced ceiling, beta ' +
                  'headers, and whether a long-context price branch exists');
    process.exitCode = 2;
    return;
  }

  let rules;
  try {
    rules = parseRules(JSON.parse(await readFile(file, 'utf8')));
  } catch (err) {
    console.error(`could not read ${file}: ${err.message}`);
    process.exitCode = 2;
    return;
  }
  const ids = Object.keys(rules).sort();
  if (ids.length === 0) {
    console.error(`no valid model ids in ${file}`);
    process.exitCode = 2;
    return;
  }

  console.log(`no beta-header probe is made: ${BETA_1M} is still a recognised ` +
              'name, so a 200 would prove the name is valid and nothing about ' +
              'its effect');

  let bad = 0;
  for (const modelId of ids) {
    const model = await get(key, `/models/${modelId}`);
    if (model === null) {
      console.warn(`${'unknown-model-id'.padEnd(20)} ${modelId.padEnd(26)} the ` +
                   'id no longer resolves on the Models API, which is a ' +
                   'retirement rather than a ceiling problem');
      bad += 1;
      continue;
    }

    for (const [state, detail] of audit(model, rules[modelId])) {
      const line = `${state.padEnd(20)} ${modelId.padEnd(26)} ${detail}`;
      if (FINDINGS.has(state)) {
        bad += 1;
        console.warn(line);
        for (const repair of repairLines(state, modelId)) {
          console.warn(`  repair: ${repair}`);
        }
      } else {
        console.log(line);
      }
    }

    const out = reportedOutput(model);
    if (out !== null) {
      console.log(`${'output-ceiling'.padEnd(20)} ${modelId.padEnd(26)} reports ` +
                  `max_output_tokens ${out}, which is a separate ceiling and ` +
                  'is not graded here');
    }
  }

  console.log(`${ids.length} model(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The headline test is one model object reporting <code>1000000</code> against a config that enforces <code>200000</code>, and the assertion is on the shortfall: eight hundred thousand tokens that exist, are paid for and cannot be reached. Beside it is the test that keeps the two directions apart, because an enforced ceiling <em>above</em> the reported window is the opposite fault and fails loudly. Then the same beta header graded twice &mdash; inert on a model that already defaults to 1M, retired on one that reports the standard window &mdash; the premium branch that prices something free, the multiple-findings shape that stops one stale id hiding two repairs behind one line, and the id validation that stops a config value walking into a URL path.",
"test_py_file": "test_anthropic_context_window_cap.py",
"test_py": '''from anthropic_context_window_cap import (audit, grade_betas, grade_ceiling,
                                           grade_premium, parse_rules,
                                           repair_lines, reported_output,
                                           reported_window, shortfall,
                                           valid_model_id)

OPUS_5 = {"id": "claude-opus-5", "max_input_tokens": 1_000_000,
          "max_output_tokens": 128_000}
SONNET_4_5 = {"id": "claude-sonnet-4-5", "max_input_tokens": 200_000,
              "max_output_tokens": 64_000}
HAIKU = {"id": "claude-haiku-4-5-20251001", "max_input_tokens": 200_000,
         "max_output_tokens": 64_000}


def test_a_million_token_window_enforced_at_two_hundred_thousand():
    # The note in one assertion. Nothing is misconfigured on the provider side
    # and nothing errors; the window is simply unreachable because a constant
    # in the application says so.
    rules = parse_rules({"claude-opus-5": {"max_input_tokens": 200_000}})
    state, detail = grade_ceiling(reported_window(OPUS_5),
                                  rules["claude-opus-5"]["cap"])
    assert state == "capped-in-code"
    assert "800000 token(s) of window bought and unreachable" in detail
    assert shortfall(1_000_000, 200_000) == 800_000
    assert any("raise the enforced ceiling" in line
               for line in repair_lines(state, "claude-opus-5"))


def test_the_opposite_direction_is_a_different_and_louder_fault():
    state, detail = grade_ceiling(reported_window(SONNET_4_5), 1_000_000)
    assert state == "cap-above-model"
    assert "400 prompt is too long" in detail
    # And an aligned pair is not a finding at all.
    assert grade_ceiling(reported_window(HAIKU), 200_000)[0] == "aligned"


def test_the_same_beta_header_is_two_findings_depending_on_the_model():
    inert = grade_betas(reported_window(OPUS_5), ["context-1m-2025-08-07"])
    assert [s for s, _ in inert] == ["inert-beta-header"]
    assert "does nothing" in inert[0][1]

    retired = grade_betas(reported_window(SONNET_4_5), ["context-1m-2025-08-07"])
    assert [s for s, _ in retired] == ["retired-beta"]
    assert "2026-04-30" in retired[0][1]
    # An unrelated beta is not this note's business.
    assert grade_betas(1_000_000, ["some-other-beta"]) == []
    assert grade_betas(None, ["context-1m-2025-08-07"]) == []


def test_a_long_context_premium_branch_prices_something_that_is_free():
    state, detail = grade_premium(reported_window(OPUS_5), True)
    assert state == "phantom-premium"
    assert "same per-token rate" in detail
    assert grade_premium(reported_window(OPUS_5), False) is None
    # On a 200k model there is no long-context branch to be wrong about.
    assert grade_premium(reported_window(SONNET_4_5), True) is None


def test_one_stale_id_carries_several_findings_at_once():
    rules = parse_rules({"claude-opus-5": {
        "max_input_tokens": 200_000,
        "beta_headers": "context-1m-2025-08-07",
        "long_context_premium": True}})
    states = [s for s, _ in audit(OPUS_5, rules["claude-opus-5"])]
    assert states == ["capped-in-code", "inert-beta-header", "phantom-premium"]
    # A clean model produces one quiet line and no findings.
    clean = parse_rules({"claude-haiku-4-5-20251001": {"max_input_tokens": 200_000}})
    assert [s for s, _ in audit(HAIKU, clean["claude-haiku-4-5-20251001"])] == \\
        ["aligned"]


def test_model_ids_are_validated_before_they_reach_a_url():
    assert valid_model_id("claude-opus-5") is True
    assert valid_model_id("claude-haiku-4-5-20251001") is True
    assert valid_model_id("../../organizations") is False
    assert valid_model_id("claude opus 5") is False
    assert valid_model_id("") is False
    assert valid_model_id(None) is False
    rules = parse_rules({"../../etc": {"max_input_tokens": 1},
                         "claude-opus-5": {"max_input_tokens": 200_000}})
    assert list(rules) == ["claude-opus-5"]


def test_a_missing_window_is_not_a_window_of_zero():
    assert reported_window({}) is None
    assert reported_window({"max_input_tokens": 0}) is None
    assert reported_window({"max_input_tokens": "1000000"}) == 1_000_000
    assert reported_output(OPUS_5) == 128_000
    assert shortfall(None, 200_000) is None
    state, detail = grade_ceiling(None, 200_000)
    assert state == "window-not-reported"
    assert "no claim is made" in detail


def test_rules_default_safely_when_the_config_is_thin():
    rules = parse_rules({"claude-opus-5": {}})
    assert rules["claude-opus-5"] == {"cap": None, "betas": [], "premium": False}
    assert audit(OPUS_5, rules["claude-opus-5"]) == []
    assert parse_rules(None) == {}
    assert parse_rules({"claude-opus-5": "not a dict"})["claude-opus-5"]["cap"] is None
''',
"test_js_file": "anthropic-context-window-cap.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { audit, gradeBetas, gradeCeiling, gradePremium, parseRules,
         repairLines, reportedOutput, reportedWindow, shortfall, validModelId }
  from './anthropic-context-window-cap.mjs';

const OPUS_5 = { id: 'claude-opus-5', max_input_tokens: 1_000_000,
                 max_output_tokens: 128_000 };
const SONNET_4_5 = { id: 'claude-sonnet-4-5', max_input_tokens: 200_000,
                     max_output_tokens: 64_000 };
const HAIKU = { id: 'claude-haiku-4-5-20251001', max_input_tokens: 200_000,
                max_output_tokens: 64_000 };

test('a million token window enforced at two hundred thousand', () => {
  const rules = parseRules({ 'claude-opus-5': { max_input_tokens: 200_000 } });
  const [state, detail] = gradeCeiling(reportedWindow(OPUS_5),
                                       rules['claude-opus-5'].cap);
  assert.equal(state, 'capped-in-code');
  assert.match(detail, /800000 token\\(s\\) of window bought and unreachable/);
  assert.equal(shortfall(1_000_000, 200_000), 800_000);
  assert.ok(repairLines(state, 'claude-opus-5')
    .some((line) => line.includes('raise the enforced ceiling')));
});

test('the opposite direction is a different and louder fault', () => {
  const [state, detail] = gradeCeiling(reportedWindow(SONNET_4_5), 1_000_000);
  assert.equal(state, 'cap-above-model');
  assert.match(detail, /400 prompt is too long/);
  assert.equal(gradeCeiling(reportedWindow(HAIKU), 200_000)[0], 'aligned');
});

test('the same beta header is two findings depending on the model', () => {
  const inert = gradeBetas(reportedWindow(OPUS_5), ['context-1m-2025-08-07']);
  assert.deepEqual(inert.map(([s]) => s), ['inert-beta-header']);
  assert.match(inert[0][1], /does nothing/);

  const retired = gradeBetas(reportedWindow(SONNET_4_5), ['context-1m-2025-08-07']);
  assert.deepEqual(retired.map(([s]) => s), ['retired-beta']);
  assert.match(retired[0][1], /2026-04-30/);
  assert.deepEqual(gradeBetas(1_000_000, ['some-other-beta']), []);
  assert.deepEqual(gradeBetas(null, ['context-1m-2025-08-07']), []);
});

test('a long context premium branch prices something that is free', () => {
  const [state, detail] = gradePremium(reportedWindow(OPUS_5), true);
  assert.equal(state, 'phantom-premium');
  assert.match(detail, /same per-token rate/);
  assert.equal(gradePremium(reportedWindow(OPUS_5), false), null);
  assert.equal(gradePremium(reportedWindow(SONNET_4_5), true), null);
});

test('one stale id carries several findings at once', () => {
  const rules = parseRules({ 'claude-opus-5': {
    max_input_tokens: 200_000,
    beta_headers: 'context-1m-2025-08-07',
    long_context_premium: true } });
  assert.deepEqual(audit(OPUS_5, rules['claude-opus-5']).map(([s]) => s),
    ['capped-in-code', 'inert-beta-header', 'phantom-premium']);
  const clean = parseRules({ 'claude-haiku-4-5-20251001': { max_input_tokens: 200_000 } });
  assert.deepEqual(audit(HAIKU, clean['claude-haiku-4-5-20251001']).map(([s]) => s),
    ['aligned']);
});

test('model ids are validated before they reach a url', () => {
  assert.equal(validModelId('claude-opus-5'), true);
  assert.equal(validModelId('claude-haiku-4-5-20251001'), true);
  assert.equal(validModelId('../../organizations'), false);
  assert.equal(validModelId('claude opus 5'), false);
  assert.equal(validModelId(''), false);
  assert.equal(validModelId(null), false);
  const rules = parseRules({ '../../etc': { max_input_tokens: 1 },
                             'claude-opus-5': { max_input_tokens: 200_000 } });
  assert.deepEqual(Object.keys(rules), ['claude-opus-5']);
});

test('a missing window is not a window of zero', () => {
  assert.equal(reportedWindow({}), null);
  assert.equal(reportedWindow({ max_input_tokens: 0 }), null);
  assert.equal(reportedWindow({ max_input_tokens: '1000000' }), 1_000_000);
  assert.equal(reportedOutput(OPUS_5), 128_000);
  assert.equal(shortfall(null, 200_000), null);
  const [state, detail] = gradeCeiling(null, 200_000);
  assert.equal(state, 'window-not-reported');
  assert.match(detail, /no claim is made/);
});

test('rules default safely when the config is thin', () => {
  const rules = parseRules({ 'claude-opus-5': {} });
  assert.deepEqual(rules['claude-opus-5'], { cap: null, betas: [], premium: false });
  assert.deepEqual(audit(OPUS_5, rules['claude-opus-5']), []);
  assert.deepEqual(parseRules(null), {});
  assert.equal(parseRules({ 'claude-opus-5': 'not a dict' })['claude-opus-5'].cap,
               null);
});
''',
"faq": [
 ("Why does the script need a config file instead of finding the ceiling itself?",
  "Because no endpoint on either API can see your source. The provider knows what the model supports; only your repository knows what your code enforces, which header values the request path still attaches, and whether a long-context price branch still exists. Half of this comparison has to be declared, and the script says so rather than presenting a declaration as a discovery. Writing that file down is usually the first time the four facts are looked at together."),
 ("Is the 1M context window still behind a beta header?",
  "No, and that is the whole point. On Claude Opus 5, Opus 4.8, 4.7 and 4.6, Sonnet 5 and 4.6, Fable 5, Mythos 5 and Mythos Preview, the 1M window is the default: no header, standard pricing across the full window, prompt caching and batch discounts at standard rates, and no separate long-context rate limits. The header only ever applied to Sonnet 4.5 and Sonnet 4, and on those it was retired on 30 April 2026."),
 ("The header is still accepted, so surely it still works?",
  "Acceptance is not effect. The beta name is still recognised, so a request carrying it does not fail, which is exactly what makes it convincing. On a model that already defaults to 1M the header changes nothing, and on Sonnet 4.5 or Sonnet 4 it changes nothing either, but there anything over 200k now returns 400 invalid_request_error with prompt is too long. That is why this script does not probe the header at all: a 200 back from a probe would be evidence of nothing."),
 ("Does a very long request cost more per token?",
  "Not on current models. A 900k-token request bills at the same per-token rate as a 9k one, and the dedicated long-context rate limits were removed along with the premium, so standard account limits apply at every context length. The belief that crossing 200k triggers premium pricing was true of the retired beta and is not true now, which is why a surviving price or throttle branch is graded as a finding rather than as prudence."),
 ("What about max_tokens, since 1M models cap output at 128k?",
  "That is a real ceiling and a separate one, so it has its own note. The model object carries max_output_tokens alongside max_input_tokens, and a configured max_tokens above it fails differently and is repaired differently. This script prints the reported output ceiling as context and deliberately does not grade it, because duplicating a check in two places is how two places end up disagreeing."),
],
"related": [REL_LONG_BAND, REL_OVERFLOW, REL_MAX_TOKENS],
"citations": [CITE_CL_CONTEXT_WINDOWS, CITE_CL_MODELS, CITE_CL_PRICING,
              CITE_CL_MODELS_OVERVIEW],
},
{
"slug": "claude-code-sessions-not-hitting-cache",
"title": "Claude Code sessions billed with zero cache reads",
"description": "A different report entirely: the Claude Code usage report, per actor. Two or more sessions with cache_read at zero means the prefix is bought again every turn.",
"h1": "Claude Code sessions billed with zero cache reads",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude code analytics api cache_read",
             "claude code usage report per developer",
             "claude code cost per session",
             "anthropic usage_report claude_code",
             "claude code prefix not cached"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only. The report is daily UTC and only returns records older than one hour.",
"lead": "Two developers on the same team, the same repository, the same model, and one of them costs four times what the other does. The expensive one is not doing more work &mdash; fewer commits, in fact &mdash; and the cheap one has not configured anything. The difference is a habit: one of them keeps a session open and talks to it, and the other opens a fresh session for every question, which feels tidier and means the project context, the tool definitions and the file contents are paid for again at full rate every single time.",
"short_answer": """<p>This is a <strong>different report</strong> from the one the other caching notes read. <code>GET /v1/organizations/usage_report/claude_code?starting_at=YYYY-MM-DD&amp;limit=1000</code> with an <strong>Admin API key</strong> returns one record per actor per UTC day, and it cannot be joined to the messages usage report at all &mdash; different grain, different keys, no shared id. It is the only place per-developer Claude Code behaviour is visible.</p>
<p>Per record, read <code>core_metrics.num_sessions</code> and every <code>model_breakdown[]</code> entry's <code>tokens.input</code>, <code>tokens.cache_read</code> and <code>tokens.cache_creation</code>, plus <code>estimated_cost.amount</code>. The finding is <code>num_sessions &gt;= 2</code> with <code>cache_read == 0</code>: two or more sessions in a day and not one token ever read back from a cached prefix.</p>
<p>Split the zero. <code>cache_creation == 0</code> as well means nothing is being cached at all. <code>cache_creation &gt; 0</code> with <code>cache_read == 0</code> means entries are being written, at a premium, and never matched. The two have different causes and the second is the more expensive mistake.</p>
<p>It matters more here than almost anywhere else because Claude Code sends very large prefixes. The gap between a read at 0.1x and uncached input at 1.0x is most of the per-developer bill, and nothing about it is visible to the developer.</p>""",
"problem": """<p>Everything Claude Code does well depends on a long, stable prefix: the project context file, the tool definitions, the contents of the files it has already read. That prefix is re-sent on every turn, because the API is stateless, and the only thing standing between you and paying full price for it every time is a cache entry that matches byte for byte and is still alive.</p>
<p>The failure is behavioural rather than technical, which is why no configuration audit finds it. A session that runs for forty turns writes the prefix once and reads it thirty-nine times. Forty separate one-turn sessions write it forty times and read it never, and there is no error, no warning and no difference in the answers. The two workflows are indistinguishable from the inside and differ by roughly an order of magnitude on the input half of the bill.</p>
<p>It also hides inside an average. Rolled up to the organization the cached share looks respectable, because the developers who keep long sessions carry it. The report is per actor precisely so that the four people whose share is zero can be seen at all, and they will not appear in any aggregate that anyone else is looking at.</p>""",
"why": """<p><strong>This is not the messages usage report, and the distinction is the reason the note exists.</strong> Two published notes already read <code>cache_creation</code> and <code>cache_read</code> on <code>/v1/organizations/usage_report/messages</code>, one for a cached share of zero and one for writes that outnumber reads. Those read organization traffic grouped by model, key or workspace. This reads <code>/v1/organizations/usage_report/claude_code</code>, whose unit is a person and a day, whose records carry session counts and tool actions that exist nowhere else, and which cannot be joined to the other report by any field. Same two token names, different report, different subject.</p>
<p><strong>One session is never evidence.</strong> A single session with a single turn has no earlier turn to read a prefix back from, so a zero there is arithmetic rather than a finding. The floor is <code>num_sessions &gt;= 2</code>, and the script prints the session count beside every verdict so a reader can see which side of it a person fell on.</p>
<p><strong>Writes with no reads is a different diagnosis from no cache at all.</strong> Zero writes and zero reads means the prefix is never being cached, which is usually very short sessions. Writes with no reads means something is invalidating the prefix between turns &mdash; a timestamp, a re-ordered tool list, per-turn context injected ahead of the stable block &mdash; and it is worse, because five-minute cache writes cost more than plain input. <a href="/llm/cache-writes-with-no-reads/">The write-without-read note</a> covers that mechanism properly on the other report, and this script names it rather than restating it.</p>
<p><strong>The savings cannot be computed and the script will not pretend otherwise.</strong> Cache reads bill at 0.1x, so it is tempting to multiply. But the report does not say how much of an actor's <code>tokens.input</code> was a reusable prefix and how much was genuinely new, and that ratio is the whole calculation. The output pairs the observed cost with the observed shares and refuses to produce a savings figure, because a plausible number here would be indistinguishable from a real one.</p>
<p><strong>The report has real edges and the output says them out loud.</strong> It covers Claude Code on the Claude API only &mdash; usage through Bedrock, Google Cloud, Foundry or Claude Platform on AWS is not reported here at all. Records are daily UTC aggregates and only those older than one hour are returned, so today is always incomplete. And the actor is an email address, which is personal data walking into a terminal, so the script masks it unless you ask for it in full.</p>""",
"steps": [
 {"h": "Use an Admin API key and request one UTC day at a time",
  "body": """<p><code>GET /v1/organizations/usage_report/claude_code?starting_at=YYYY-MM-DD&amp;limit=1000</code>, paging on <code>next_page</code> until <code>has_more</code> is false, once per day in the window. The script starts at yesterday, because only records older than an hour are returned and today's would be a partial day masquerading as a light one.</p>"""},
 {"h": "Fold the model breakdown per actor",
  "body": """<p>An actor's record carries a <code>model_breakdown[]</code> array, not a single total. Sum <code>tokens.input</code>, <code>tokens.cache_read</code>, <code>tokens.cache_creation</code> and <code>estimated_cost.amount</code> across every entry, and keep <code>core_metrics.num_sessions</code> from the record itself. Reading only the first breakdown entry is the easy mistake and it understates anyone who used two models.</p>"""},
 {"h": "Apply the session floor before you grade anything",
  "body": """<p>Fewer than two sessions in the window is not a finding, whatever the cache numbers say. There was nothing to read back. The script reports those separately rather than padding the list with people who used the tool once.</p>"""},
 {"h": "Split the zero into never cached and never matched",
  "body": """<p>Reads and writes both zero: the prefix is never being cached. Writes present, reads zero: it is being cached and never matched, which costs more than not caching it. Different repairs, so different labels.</p>"""},
 {"h": "Print the actors, masked, with the sessions and the cost beside them",
  "body": """<p>Email addresses are personal data. The default output masks the local part; a flag prints them in full for the conversation where you actually need to reach someone. No savings estimate appears, because the report does not carry the ratio that would make one honest.</p>"""},
],
"verify": """<p>Re-run on the same window a week after the habit changes. A developer who moves from fresh sessions to continued ones should show a real <code>cache_read</code> share and a lower cost per session on the same volume of work. The session count is the control: if it fell and the reads did not appear, the change was fewer sessions rather than longer ones.</p>
<pre><code class="language-bash">python3 claude_code_cache_coverage.py --days 7
# no-cache-at-all      a***@example.com     11 session(s), 0% of input read from cache, no cache writes either, $41.20
#   repair: check whether these sessions are one prompt each. A prefix is only reusable across turns of the same session.
# writes-never-read    b***@example.com     6 session(s), 0% read with 2.1M token(s) written, $58.90
#   repair: entries are being written and never matched. Something ahead of the stable block is changing between turns.
# cached               c***@example.com     4 session(s), 84% of input read from cache, $9.40
# 7 actor(s) over 7 day(s), 2 finding(s)
# no savings figure: the report does not say how much of tokens.input was reusable prefix</code></pre>""",
"code_intro": "One GET per day, paged, and eight pure functions. The actor reader, which has to cope with a user actor, an api actor and neither; the mask, because an email address is personal data and the default should not print it; the token reader; the fold across <code>model_breakdown[]</code>, which is the step everyone shortcuts; the cost parser, which treats <code>estimated_cost.amount</code> as a decimal string of cents rather than a float; the read share; the verdict with its session floor; and the repair lines. There is no savings estimator, deliberately.",
"py_file": "claude_code_cache_coverage.py",
"py": '''"""Find Claude Code actors whose sessions never read a cached prefix.

Read only. One paged GET per UTC day against the Claude Code usage report with
an Admin API key. No message is sent and nothing is written.

This is a different report from the messages usage report. Its unit is an actor
and a day, it carries session counts and tool actions that exist nowhere else,
and it cannot be joined to the other report by any field. Two token names are
the same; nothing else is.

The report covers Claude Code on the Claude API only. Usage through Bedrock,
Google Cloud, Foundry or Claude Platform on AWS is not reported here, so a
finding of "no evidence" is not a finding of "no problem" for those paths.

No savings figure is printed. Cache reads bill at 0.1x, but the report does not
say how much of tokens.input was reusable prefix and how much was genuinely
new, and that ratio is the entire calculation.
"""
import argparse
import datetime as dt
import decimal
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("claude_code_cache_coverage")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

FINDINGS = ("no-cache-at-all", "writes-never-read", "thin-cache")


def actor_name(record):
    """Who the record belongs to. Pure. Both actor shapes, plus neither.

    A user actor carries an email address; an api actor carries a key name.
    A reader that knows only the first drops every service account silently,
    which is the half of the roster nobody is watching.
    """
    actor = (record or {}).get("actor")
    if not isinstance(actor, dict):
        return "unattributed"
    for field in ("email_address", "api_key_name"):
        value = str(actor.get(field) or "").strip()
        if value:
            return value
    return "unattributed"


def mask(name):
    """Hide the local part of an email address. Pure. Non-emails pass through.

    The actor on this report is usually a person, and a per-developer cost
    table is personal data. Masking by default costs nothing and makes the
    output safe to paste into a channel.
    """
    text = str(name or "").strip()
    if "@" not in text:
        return text or "unattributed"
    local, _, domain = text.partition("@")
    if not local:
        return text
    return local[0] + "***@" + domain


def tokens_of(entry):
    """The four token counts off one model_breakdown entry. Pure."""
    tokens = (entry or {}).get("tokens")
    tokens = tokens if isinstance(tokens, dict) else {}
    out = {}
    for field in ("input", "output", "cache_read", "cache_creation"):
        try:
            out[field] = max(0, int(tokens.get(field) or 0))
        except (TypeError, ValueError):
            out[field] = 0
    return out


def cost_cents(entry):
    """estimated_cost.amount as a Decimal of cents. Pure. 0 when unreadable.

    A decimal string, parsed as a decimal. Money through a float is how a
    per-developer table ends up disagreeing with itself in the third place.
    """
    cost = (entry or {}).get("estimated_cost")
    cost = cost if isinstance(cost, dict) else {}
    try:
        return decimal.Decimal(str(cost.get("amount") or "0"))
    except (decimal.InvalidOperation, ValueError):
        return decimal.Decimal("0")


def fold(pages):
    """Fold every record into one row per actor. Pure.

    Sums across model_breakdown[] rather than reading the first entry, and
    sums sessions across days. An actor who used two models in one day has two
    entries, and taking the first understates them by whatever the second held.
    """
    rows = {}
    for page in pages or []:
        for record in (page or {}).get("data") or []:
            if not isinstance(record, dict):
                continue
            who = actor_name(record)
            row = rows.setdefault(who, {
                "sessions": 0, "days": 0, "input": 0, "output": 0,
                "cache_read": 0, "cache_creation": 0,
                "cents": decimal.Decimal("0"), "models": set()})
            row["days"] += 1
            core = record.get("core_metrics")
            core = core if isinstance(core, dict) else {}
            try:
                row["sessions"] += max(0, int(core.get("num_sessions") or 0))
            except (TypeError, ValueError):
                pass
            for entry in record.get("model_breakdown") or []:
                counts = tokens_of(entry)
                for field, value in counts.items():
                    row[field] += value
                row["cents"] += cost_cents(entry)
                model = str((entry or {}).get("model") or "").strip()
                if model:
                    row["models"].add(model)
    return rows


def read_share(row):
    """Share of an actor's input that was read back from cache. Pure.

    Reads over reads plus uncached input. Cache writes are deliberately not in
    the denominator: they are a cost, not a hit, and putting them there makes a
    prefix that is written and never matched look partly cached.
    """
    data = row or {}
    reads = max(0, int(data.get("cache_read") or 0))
    fresh = max(0, int(data.get("input") or 0))
    total = reads + fresh
    if total <= 0:
        return 0.0
    return reads / float(total)


def cost_per_session(row):
    """Cents per session for one actor. Pure. None when there are no sessions."""
    data = row or {}
    sessions = max(0, int(data.get("sessions") or 0))
    if sessions <= 0:
        return None
    return decimal.Decimal(data.get("cents") or 0) / decimal.Decimal(sessions)


def verdict(row, min_sessions=2, min_input=100_000, floor=0.10):
    """Classify one actor's cache behaviour. Pure. Returns (state, detail)."""
    data = row or {}
    sessions = max(0, int(data.get("sessions") or 0))
    reads = max(0, int(data.get("cache_read") or 0))
    writes = max(0, int(data.get("cache_creation") or 0))
    fresh = max(0, int(data.get("input") or 0))

    if sessions < min_sessions:
        return ("too-few-sessions",
                "%d session(s) in the window: there was no earlier turn for a "
                "prefix to be read back from, so a zero here is arithmetic "
                "rather than a finding" % sessions)
    if reads + fresh < min_input:
        return ("low-volume",
                "%d session(s) and %d input token(s), too few to conclude "
                "anything" % (sessions, reads + fresh))

    share = read_share(data)
    if reads == 0 and writes == 0:
        return ("no-cache-at-all",
                "%d session(s), 0%% of input read from cache, and no cache "
                "writes either: the prefix is never being cached at all"
                % sessions)
    if reads == 0:
        return ("writes-never-read",
                "%d session(s), 0%% read with %.1fM token(s) written: entries "
                "are being created at a premium and never matched"
                % (sessions, writes / 1e6))
    if share < floor:
        return ("thin-cache",
                "%d session(s), %.0f%% of input read from cache, under the "
                "floor of %.0f%%" % (sessions, share * 100, floor * 100))
    return ("cached",
            "%d session(s), %.0f%% of input read from cache"
            % (sessions, share * 100))


def repair_lines(state):
    """The repair for one classified actor. Pure. Printed, never performed."""
    if state == "no-cache-at-all":
        return [
            "check whether these sessions are one prompt each. A prefix is "
            "only reusable across turns of the same session, so a fresh "
            "session per question pays full rate for the project context, the "
            "tool definitions and every file already read.",
            "continuing a session rather than starting one is the whole fix, "
            "and it is a habit rather than a setting.",
        ]
    if state == "writes-never-read":
        return [
            "entries are being written and never matched, so something ahead "
            "of the stable block is changing between turns.",
            "this is the more expensive of the two zeros: cache writes cost "
            "more than plain input, so the current state is worse than not "
            "caching at all.",
        ]
    if state == "thin-cache":
        return [
            "some turns are matching and most are not. Look for a mix of long "
            "sessions and one-shot invocations under the same actor before "
            "concluding the prefix is unstable.",
        ]
    return []


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk one day of the paginated Claude Code usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def day_strings(days, today=None):
    """The UTC dates to request, newest first. Pure. Today is excluded.

    Only records older than an hour are returned, so today is always a partial
    day, and a partial day reads as a quiet one.
    """
    end = today or dt.datetime.now(dt.timezone.utc).date()
    return [(end - dt.timedelta(days=n)).isoformat()
            for n in range(1, max(1, int(days)) + 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="UTC days to read, ending yesterday (default 7)")
    ap.add_argument("--min-sessions", type=int, default=2,
                    help="sessions below which no claim is made (default 2)")
    ap.add_argument("--floor", type=float, default=0.10,
                    help="cache read share below which coverage is thin")
    ap.add_argument("--show-actors", action="store_true",
                    help="print email addresses in full instead of masked")
    ap.add_argument("--show-all", action="store_true",
                    help="also print actors whose caching is healthy")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    collected = []
    days = day_strings(args.days)
    for day in days:
        collected.extend(pages(s, "/organizations/usage_report/claude_code",
                               {"starting_at": day, "limit": 1000}))

    rows = fold(collected)
    if not rows:
        log.info("no Claude Code records over %d day(s). This report covers "
                 "Claude Code on the Claude API only: Bedrock, Google Cloud, "
                 "Foundry and Claude Platform on AWS usage is not here.",
                 len(days))
        return 0

    bad = 0
    for who in sorted(rows, key=lambda a: -rows[a]["cents"]):
        row = rows[who]
        state, detail = verdict(row, args.min_sessions, floor=args.floor)
        label = who if args.show_actors else mask(who)
        line = "%-20s %-22s %s, $%.2f" % (state, label, detail,
                                          float(row["cents"]) / 100.0)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(state):
                log.warning("  repair: %s", repair)
        elif args.show_all or state != "cached":
            log.info(line)

    log.info("%d actor(s) over %d day(s), %d finding(s)",
             len(rows), len(days), bad)
    log.info("no savings figure: the report does not say how much of "
             "tokens.input was reusable prefix, and that ratio is the whole "
             "calculation")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "claude-code-cache-coverage.mjs",
"js": '''/**
 * Find Claude Code actors whose sessions never read a cached prefix.
 *
 * Read only. One paged GET per UTC day against the Claude Code usage report
 * with an Admin API key.
 *
 * This is a different report from the messages usage report: its unit is an
 * actor and a day, and it cannot be joined to the other by any field. It also
 * covers Claude Code on the Claude API only, so Bedrock, Google Cloud, Foundry
 * and Claude Platform on AWS usage is simply absent.
 *
 * No savings figure is printed. The report does not say how much of
 * tokens.input was reusable prefix, and that ratio is the whole calculation.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const FINDINGS = new Set(['no-cache-at-all', 'writes-never-read', 'thin-cache']);

/** Who the record belongs to. Pure. Both actor shapes, plus neither. */
export function actorName(record) {
  const actor = record?.actor;
  if (!actor || typeof actor !== 'object') return 'unattributed';
  for (const field of ['email_address', 'api_key_name']) {
    const value = String(actor[field] ?? '').trim();
    if (value) return value;
  }
  return 'unattributed';
}

/** Hide the local part of an email address. Pure. Non-emails pass through. */
export function mask(name) {
  const text = String(name ?? '').trim();
  if (!text.includes('@')) return text || 'unattributed';
  const at = text.indexOf('@');
  const local = text.slice(0, at);
  if (!local) return text;
  return `${local[0]}***${text.slice(at)}`;
}

/** The four token counts off one model_breakdown entry. Pure. */
export function tokensOf(entry) {
  const tokens = entry?.tokens && typeof entry.tokens === 'object' ? entry.tokens : {};
  const out = {};
  for (const field of ['input', 'output', 'cache_read', 'cache_creation']) {
    const n = Number(tokens[field] ?? 0);
    out[field] = Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0;
  }
  return out;
}

/**
 * estimated_cost.amount in cents. Pure. 0 when unreadable.
 * Kept as a number of cents rather than dollars so the rounding happens once,
 * at the point of printing, instead of on every addition.
 */
export function costCents(entry) {
  const cost = entry?.estimated_cost && typeof entry.estimated_cost === 'object'
    ? entry.estimated_cost : {};
  const n = Number(cost.amount ?? 0);
  return Number.isFinite(n) ? n : 0;
}

/** Fold every record into one row per actor. Pure. Sums across model_breakdown. */
export function fold(pages) {
  const rows = {};
  for (const page of pages ?? []) {
    for (const record of page?.data ?? []) {
      if (!record || typeof record !== 'object') continue;
      const who = actorName(record);
      const row = rows[who] ?? { sessions: 0, days: 0, input: 0, output: 0,
                                 cache_read: 0, cache_creation: 0, cents: 0,
                                 models: new Set() };
      rows[who] = row;
      row.days += 1;
      const core = record.core_metrics && typeof record.core_metrics === 'object'
        ? record.core_metrics : {};
      const sessions = Number(core.num_sessions ?? 0);
      if (Number.isFinite(sessions)) row.sessions += Math.max(0, Math.trunc(sessions));
      for (const entry of record.model_breakdown ?? []) {
        const counts = tokensOf(entry);
        for (const [field, value] of Object.entries(counts)) row[field] += value;
        row.cents += costCents(entry);
        const model = String(entry?.model ?? '').trim();
        if (model) row.models.add(model);
      }
    }
  }
  return rows;
}

/**
 * Share of an actor's input that was read back from cache. Pure.
 * Writes are not in the denominator: they are a cost, not a hit.
 */
export function readShare(row) {
  const reads = Math.max(0, Number(row?.cache_read ?? 0));
  const fresh = Math.max(0, Number(row?.input ?? 0));
  const total = reads + fresh;
  if (total <= 0) return 0;
  return reads / total;
}

/** Cents per session for one actor. Pure. Null when there are no sessions. */
export function costPerSession(row) {
  const sessions = Math.max(0, Number(row?.sessions ?? 0));
  if (sessions <= 0) return null;
  return Number(row?.cents ?? 0) / sessions;
}

/** Classify one actor's cache behaviour. Pure. Returns [state, detail]. */
export function verdict(row, minSessions = 2, minInput = 100_000, floor = 0.1) {
  const data = row ?? {};
  const sessions = Math.max(0, Number(data.sessions ?? 0));
  const reads = Math.max(0, Number(data.cache_read ?? 0));
  const writes = Math.max(0, Number(data.cache_creation ?? 0));
  const fresh = Math.max(0, Number(data.input ?? 0));

  if (sessions < minSessions) {
    return ['too-few-sessions',
      `${sessions} session(s) in the window: there was no earlier turn for a ` +
      'prefix to be read back from, so a zero here is arithmetic rather than ' +
      'a finding'];
  }
  if (reads + fresh < minInput) {
    return ['low-volume',
      `${sessions} session(s) and ${reads + fresh} input token(s), too few to ` +
      'conclude anything'];
  }

  const share = readShare(data);
  if (reads === 0 && writes === 0) {
    return ['no-cache-at-all',
      `${sessions} session(s), 0% of input read from cache, and no cache ` +
      'writes either: the prefix is never being cached at all'];
  }
  if (reads === 0) {
    return ['writes-never-read',
      `${sessions} session(s), 0% read with ${(writes / 1e6).toFixed(1)}M ` +
      'token(s) written: entries are being created at a premium and never matched'];
  }
  if (share < floor) {
    return ['thin-cache',
      `${sessions} session(s), ${(share * 100).toFixed(0)}% of input read ` +
      `from cache, under the floor of ${(floor * 100).toFixed(0)}%`];
  }
  return ['cached',
    `${sessions} session(s), ${(share * 100).toFixed(0)}% of input read from cache`];
}

/** The repair for one classified actor. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'no-cache-at-all') {
    return [
      'check whether these sessions are one prompt each. A prefix is only ' +
      'reusable across turns of the same session, so a fresh session per ' +
      'question pays full rate for the project context, the tool definitions ' +
      'and every file already read.',
      'continuing a session rather than starting one is the whole fix, and it ' +
      'is a habit rather than a setting.',
    ];
  }
  if (state === 'writes-never-read') {
    return [
      'entries are being written and never matched, so something ahead of the ' +
      'stable block is changing between turns.',
      'this is the more expensive of the two zeros: cache writes cost more ' +
      'than plain input, so the current state is worse than not caching at all.',
    ];
  }
  if (state === 'thin-cache') {
    return ['some turns are matching and most are not. Look for a mix of long ' +
            'sessions and one-shot invocations under the same actor before ' +
            'concluding the prefix is unstable.'];
  }
  return [];
}

/** The UTC dates to request, newest first. Pure. Today is excluded. */
export function dayStrings(days, today = new Date()) {
  const out = [];
  const count = Math.max(1, Math.trunc(Number(days) || 1));
  for (let n = 1; n <= count; n += 1) {
    const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(),
                                today.getUTCDate() - n));
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, v);
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs ` +
                    'an Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 7);
  const showActors = process.env.SHOW_ACTORS === '1';
  const showAll = process.env.SHOW_ALL === '1';

  const dates = dayStrings(days);
  const collected = [];
  for (const day of dates) {
    const base = [['starting_at', day], ['limit', '1000']];
    let params = base;
    for (;;) {
      const page = await get(admin, '/organizations/usage_report/claude_code', params);
      collected.push(page);
      if (!page?.has_more || !page?.next_page) break;
      params = [...base, ['page', page.next_page]];
    }
  }

  const rows = fold(collected);
  const actors = Object.keys(rows);
  if (actors.length === 0) {
    console.log(`no Claude Code records over ${dates.length} day(s). This ` +
                'report covers Claude Code on the Claude API only: Bedrock, ' +
                'Google Cloud, Foundry and Claude Platform on AWS usage is not here.');
    return;
  }

  let bad = 0;
  for (const who of actors.sort((a, b) => rows[b].cents - rows[a].cents)) {
    const row = rows[who];
    const [state, detail] = verdict(row, 2);
    const label = showActors ? who : mask(who);
    const line = `${state.padEnd(20)} ${label.padEnd(22)} ${detail}, ` +
                 `$${(row.cents / 100).toFixed(2)}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      for (const repair of repairLines(state)) console.warn(`  repair: ${repair}`);
    } else if (showAll || state !== 'cached') {
      console.log(line);
    }
  }

  console.log(`${actors.length} actor(s) over ${dates.length} day(s), ${bad} finding(s)`);
  console.log('no savings figure: the report does not say how much of ' +
              'tokens.input was reusable prefix, and that ratio is the whole ' +
              'calculation');
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The headline is an actor with eleven sessions in a week, two million input tokens and not one cache read, next to a colleague on the same data with a healthy share &mdash; the whole note is that those two people are indistinguishable from the inside. The test immediately after it is the guard: the same zero on a single session is arithmetic, not a finding, and has to come back as <code>too-few-sessions</code>. Then the split between never cached and never matched, the fold across a two-model breakdown that a first-entry reader would halve, both actor shapes plus neither, the mask that keeps an email out of a pasted terminal, and the day list that stops today's partial data being read as a quiet day.",
"test_py_file": "test_claude_code_cache_coverage.py",
"test_py": '''import datetime as dt

from claude_code_cache_coverage import (actor_name, cost_cents,
                                        cost_per_session, day_strings, fold,
                                        mask, read_share, repair_lines,
                                        tokens_of, verdict)


def breakdown(model, input_tokens, cache_read=0, cache_creation=0, cents="0"):
    return {"model": model,
            "tokens": {"input": input_tokens, "output": 12_000,
                       "cache_read": cache_read,
                       "cache_creation": cache_creation},
            "estimated_cost": {"currency": "USD", "amount": cents}}


def record(email, sessions, entries):
    return {"date": "2026-08-30",
            "actor": {"type": "user_actor", "email_address": email},
            "core_metrics": {"num_sessions": sessions,
                             "lines_of_code": {"added": 90, "removed": 12},
                             "commits_by_claude_code": 2},
            "model_breakdown": entries}


def page(records):
    return {"data": records, "has_more": False}


def test_two_developers_on_the_same_work_and_one_never_reads_a_prefix():
    # The note in one assertion. Same repository, same model, same week; the
    # difference is whether a session was continued or restarted.
    rows = fold([page([
        record("nobody@example.com", 11,
               [breakdown("claude-opus-5", 2_000_000, cents="4120")]),
        record("someone@example.com", 4,
               [breakdown("claude-opus-5", 300_000, cache_read=1_600_000,
                          cache_creation=200_000, cents="940")]),
    ])])

    state, detail = verdict(rows["nobody@example.com"])
    assert state == "no-cache-at-all"
    assert "11 session(s), 0%" in detail
    assert any("turns of the same session" in line
               for line in repair_lines(state))

    good, good_detail = verdict(rows["someone@example.com"])
    assert good == "cached"
    assert "84% of input read from cache" in good_detail


def test_a_single_session_zero_is_arithmetic_not_a_finding():
    rows = fold([page([
        record("once@example.com", 1,
               [breakdown("claude-opus-5", 2_000_000, cents="900")])])])
    state, detail = verdict(rows["once@example.com"])
    assert state == "too-few-sessions"
    assert "no earlier turn" in detail
    assert repair_lines(state) == []


def test_written_and_never_matched_is_the_more_expensive_zero():
    rows = fold([page([
        record("churn@example.com", 6,
               [breakdown("claude-opus-5", 900_000, cache_creation=2_100_000,
                          cents="5890")])])])
    state, detail = verdict(rows["churn@example.com"])
    assert state == "writes-never-read"
    assert "2.1M token(s) written" in detail
    assert any("worse than not caching at all" in line
               for line in repair_lines(state))


def test_the_whole_model_breakdown_is_summed_and_not_just_the_first_entry():
    rows = fold([page([
        record("two@example.com", 5, [
            breakdown("claude-opus-5", 1_000_000, cache_read=500_000, cents="1000"),
            breakdown("claude-haiku-4-5-20251001", 400_000, cache_read=100_000,
                      cents="250"),
        ])])])
    row = rows["two@example.com"]
    assert row["input"] == 1_400_000
    assert row["cache_read"] == 600_000
    assert row["cents"] == 1250
    assert row["models"] == {"claude-opus-5", "claude-haiku-4-5-20251001"}
    assert float(cost_per_session(row)) == 250.0


def test_sessions_and_cost_accumulate_across_days():
    day = [record("daily@example.com", 3,
                  [breakdown("claude-opus-5", 500_000, cents="600")])]
    rows = fold([page(day), page(day), page(day)])
    assert rows["daily@example.com"]["sessions"] == 9
    assert rows["daily@example.com"]["days"] == 3
    assert rows["daily@example.com"]["cents"] == 1800


def test_both_actor_shapes_are_read_and_neither_is_handled():
    assert actor_name({"actor": {"type": "user_actor",
                                 "email_address": "a@example.com"}}) == \\
        "a@example.com"
    assert actor_name({"actor": {"type": "api_actor",
                                 "api_key_name": "ci-runner"}}) == "ci-runner"
    assert actor_name({"actor": {}}) == "unattributed"
    assert actor_name({}) == "unattributed"
    assert actor_name(None) == "unattributed"


def test_an_email_address_is_masked_before_it_is_printed():
    assert mask("someone@example.com") == "s***@example.com"
    assert mask("ci-runner") == "ci-runner"
    assert mask("") == "unattributed"
    assert mask(None) == "unattributed"


def test_reads_over_reads_plus_input_and_writes_are_not_a_hit():
    assert read_share({"cache_read": 900, "input": 100}) == 0.9
    # A prefix written and never matched is not partly cached.
    assert read_share({"cache_read": 0, "input": 100, "cache_creation": 900}) == 0.0
    assert read_share({}) == 0.0
    assert cost_per_session({"sessions": 0, "cents": 100}) is None
    assert tokens_of(None) == {"input": 0, "output": 0, "cache_read": 0,
                               "cache_creation": 0}
    assert tokens_of({"tokens": {"input": "x"}})["input"] == 0
    assert cost_cents({"estimated_cost": {"amount": "12.50"}}) == 12.5
    assert cost_cents({"estimated_cost": {"amount": "not money"}}) == 0


def test_today_is_never_requested_because_today_is_always_partial():
    days = day_strings(3, dt.date(2026, 8, 31))
    assert days == ["2026-08-30", "2026-08-29", "2026-08-28"]
    assert day_strings(1, dt.date(2026, 1, 1)) == ["2025-12-31"]
    assert fold([]) == {} and fold(None) == {}
''',
"test_js_file": "claude-code-cache-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { actorName, costCents, costPerSession, dayStrings, fold, mask,
         readShare, repairLines, tokensOf, verdict }
  from './claude-code-cache-coverage.mjs';

const breakdown = (model, input, cacheRead = 0, cacheCreation = 0, cents = 0) => ({
  model,
  tokens: { input, output: 12_000, cache_read: cacheRead,
            cache_creation: cacheCreation },
  estimated_cost: { currency: 'USD', amount: cents },
});

const record = (email, sessions, entries) => ({
  date: '2026-08-30',
  actor: { type: 'user_actor', email_address: email },
  core_metrics: { num_sessions: sessions,
                  lines_of_code: { added: 90, removed: 12 },
                  commits_by_claude_code: 2 },
  model_breakdown: entries,
});

const page = (records) => ({ data: records, has_more: false });

test('two developers on the same work and one never reads a prefix', () => {
  const rows = fold([page([
    record('nobody@example.com', 11, [breakdown('claude-opus-5', 2_000_000, 0, 0, 4120)]),
    record('someone@example.com', 4,
      [breakdown('claude-opus-5', 300_000, 1_600_000, 200_000, 940)]),
  ])]);

  const [state, detail] = verdict(rows['nobody@example.com']);
  assert.equal(state, 'no-cache-at-all');
  assert.match(detail, /11 session/);
  assert.ok(repairLines(state).some((l) => l.includes('turns of the same session')));

  const [good, goodDetail] = verdict(rows['someone@example.com']);
  assert.equal(good, 'cached');
  assert.match(goodDetail, /84% of input read from cache/);
});

test('a single session zero is arithmetic not a finding', () => {
  const rows = fold([page([
    record('once@example.com', 1, [breakdown('claude-opus-5', 2_000_000, 0, 0, 900)]),
  ])]);
  const [state, detail] = verdict(rows['once@example.com']);
  assert.equal(state, 'too-few-sessions');
  assert.match(detail, /no earlier turn/);
  assert.deepEqual(repairLines(state), []);
});

test('written and never matched is the more expensive zero', () => {
  const rows = fold([page([
    record('churn@example.com', 6,
      [breakdown('claude-opus-5', 900_000, 0, 2_100_000, 5890)]),
  ])]);
  const [state, detail] = verdict(rows['churn@example.com']);
  assert.equal(state, 'writes-never-read');
  assert.match(detail, /2.1M token/);
  assert.ok(repairLines(state).some((l) => l.includes('worse than not caching at all')));
});

test('the whole model breakdown is summed and not just the first entry', () => {
  const rows = fold([page([
    record('two@example.com', 5, [
      breakdown('claude-opus-5', 1_000_000, 500_000, 0, 1000),
      breakdown('claude-haiku-4-5-20251001', 400_000, 100_000, 0, 250),
    ]),
  ])]);
  const row = rows['two@example.com'];
  assert.equal(row.input, 1_400_000);
  assert.equal(row.cache_read, 600_000);
  assert.equal(row.cents, 1250);
  assert.deepEqual([...row.models].sort(),
    ['claude-haiku-4-5-20251001', 'claude-opus-5']);
  assert.equal(costPerSession(row), 250);
});

test('sessions and cost accumulate across days', () => {
  const day = [record('daily@example.com', 3,
    [breakdown('claude-opus-5', 500_000, 0, 0, 600)])];
  const rows = fold([page(day), page(day), page(day)]);
  assert.equal(rows['daily@example.com'].sessions, 9);
  assert.equal(rows['daily@example.com'].days, 3);
  assert.equal(rows['daily@example.com'].cents, 1800);
});

test('both actor shapes are read and neither is handled', () => {
  assert.equal(actorName({ actor: { type: 'user_actor',
                                    email_address: 'a@example.com' } }),
               'a@example.com');
  assert.equal(actorName({ actor: { type: 'api_actor', api_key_name: 'ci-runner' } }),
               'ci-runner');
  assert.equal(actorName({ actor: {} }), 'unattributed');
  assert.equal(actorName({}), 'unattributed');
  assert.equal(actorName(null), 'unattributed');
});

test('an email address is masked before it is printed', () => {
  assert.equal(mask('someone@example.com'), 's***@example.com');
  assert.equal(mask('ci-runner'), 'ci-runner');
  assert.equal(mask(''), 'unattributed');
  assert.equal(mask(null), 'unattributed');
});

test('reads over reads plus input and writes are not a hit', () => {
  assert.equal(readShare({ cache_read: 900, input: 100 }), 0.9);
  assert.equal(readShare({ cache_read: 0, input: 100, cache_creation: 900 }), 0);
  assert.equal(readShare({}), 0);
  assert.equal(costPerSession({ sessions: 0, cents: 100 }), null);
  assert.deepEqual(tokensOf(null),
    { input: 0, output: 0, cache_read: 0, cache_creation: 0 });
  assert.equal(tokensOf({ tokens: { input: 'x' } }).input, 0);
  assert.equal(costCents({ estimated_cost: { amount: '12.50' } }), 12.5);
  assert.equal(costCents({ estimated_cost: { amount: 'not money' } }), 0);
});

test('today is never requested because today is always partial', () => {
  assert.deepEqual(dayStrings(3, new Date('2026-08-31T09:00:00Z')),
    ['2026-08-30', '2026-08-29', '2026-08-28']);
  assert.deepEqual(dayStrings(1, new Date('2026-01-01T00:30:00Z')), ['2025-12-31']);
  assert.deepEqual(fold([]), {});
  assert.deepEqual(fold(null), {});
});
''',
"faq": [
 ("Is this the same check as the prompt caching notes?",
  "No, and the difference is the report rather than the wording. Those read /v1/organizations/usage_report/messages, which aggregates organization traffic by model, key or workspace. This reads /v1/organizations/usage_report/claude_code, whose unit is one actor on one UTC day and which carries session counts and tool-action counts that appear nowhere else. The two reports share two token field names and nothing else, and they cannot be joined by any field, so a healthy cached share on one tells you nothing about a person on the other."),
 ("Why is one session not enough to make a finding?",
  "Because there was nothing to read back. Caching pays off when a later turn matches a prefix an earlier turn wrote, so a session with a single turn has no earlier turn and reports zero reads with nothing wrong. The script sets the floor at two sessions in the window and prints the session count next to every verdict, so a reader can see which side of the floor a person fell on rather than trusting the label."),
 ("What is the difference between no cache writes and writes with no reads?",
  "Cause and cost. Both zero means nothing is being cached, which is usually very short sessions. Writes present with reads at zero means entries are being created and never matched, so something ahead of the stable block changes between turns, and it is the worse of the two because cache writes bill above plain input. That state is genuinely worse than not caching at all, and the script says so instead of grading them together."),
 ("Why does the output not tell me how much money this is costing?",
  "Because the number is not derivable from what the report returns. Cache reads bill at a tenth of base input, so the arithmetic is easy, but it needs to know what fraction of an actor's tokens.input was reusable prefix and what fraction was genuinely new text, and the report does not carry that split. Any figure produced here would be a guess presented in the same font as a measurement, which is worse than no figure."),
 ("Does this cover Claude Code running through Bedrock or Vertex?",
  "It does not. The Claude Code usage report covers Claude Code on the Claude API only; usage through Bedrock, Google Cloud, Foundry or Claude Platform on AWS is not reported on this endpoint at all. If part of your organization runs on one of those, the absence of records for those developers is a coverage gap rather than a clean bill of health, and the script prints that caveat with the empty result rather than reporting nothing to see."),
],
"related": [REL_CACHE_NEVER, REL_CACHE_WRITES, REL_CC_REJECT],
"citations": [CITE_CC_ANALYTICS, CITE_CL_ANALYTICS, CITE_CL_CACHING,
              CITE_CL_PRICING],
},
{
"slug": "claude-code-edit-rejection-rate-high",
"title": "Claude Code edits rejected more often than they are kept",
"description": "The same Claude Code report, read for tool_actions. Accepted over accepted plus rejected: output that was generated, billed, read by a person and dropped.",
"h1": "Claude Code edits rejected more often than they are kept",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude code tool_actions accepted rejected",
             "claude code edit acceptance rate",
             "claude code analytics rejected diffs",
             "claude code cost per accepted edit",
             "anthropic claude code usage report tools"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only. Daily UTC records, returned only once they are more than an hour old.",
"lead": "The diff comes up, it is forty lines, it is confidently wrong about where the validation lives, and it gets rejected in about two seconds. That happens eleven times before lunch, and none of those eleven rejections is recorded anywhere a person would look, because rejecting a proposal is not an error and not a failure and not, from the tool's point of view, an event worth complaining about. Every one of those forty-line diffs was generated at frontier output rates and paid for in full before anybody read it.",
"short_answer": """<p>The same report as the cache note, a different block of it. <code>GET /v1/organizations/usage_report/claude_code?starting_at=YYYY-MM-DD&amp;limit=1000</code> with an <strong>Admin API key</strong> returns <code>tool_actions</code> per record, with <code>accepted</code> and <code>rejected</code> counts for <code>edit_tool</code>, <code>multi_edit_tool</code>, <code>write_tool</code> and <code>notebook_edit_tool</code>.</p>
<p>The rate is directly computable: <code>accepted / (accepted + rejected)</code>. Below one half means a majority of the diffs an actor was shown got thrown away. Pair it with <code>model_breakdown[].estimated_cost.amount</code> and with <code>core_metrics.commits_by_claude_code</code>, <code>pull_requests_by_claude_code</code> and <code>lines_of_code</code>, because a low rate next to real commits is a different story from a low rate next to nothing.</p>
<p>This is the only measurement in this section whose subject is <strong>billed output that a human read and discarded</strong>. Every other note here is about tokens spent on machinery, on retries, on prefixes or on capacity. This one is about generation that completed successfully, cost full output rates, and was then declined by the person it was produced for.</p>
<p>The cause is almost never the tool. A sustained low acceptance rate points at missing project context, task framing that is too broad, or a model and effort level mismatched to the work &mdash; and the API cannot tell you which, so the script names the three and stops.</p>""",
"problem": """<p>Rejection is a healthy operation. Somebody read a proposed change, decided it was wrong, and did not apply it, which is the review step working exactly as intended. Nothing about a single rejection is a problem, and that is precisely why a sustained one is invisible: there is no threshold at which the tool starts objecting, no error, and no aggregate anyone watches.</p>
<p>The money is already spent by then. A rejected edit was fully generated before it was displayed, so the output tokens are billed identically whether the diff is applied or dismissed with a keystroke. At frontier output rates, on multi-file edits, an actor running below fifty per cent acceptance is spending the majority of their output budget on work that reaches nobody.</p>
<p>And the loss compounds past the invoice. A rejected proposal costs the developer the time to read it and the context switch to recover from it, and it usually costs another turn to try again, which is another full generation. The cost per <em>accepted</em> change is the number that matters and it is not on any dashboard, because no dashboard joins these two fields.</p>""",
"why": """<p><strong>This is the sibling of the cache note, not a variation of it.</strong> They read the same endpoint and they do not merge, because they read different blocks and answer different questions. The cache note reads <code>model_breakdown[].tokens</code> and asks whether a prefix is being repurchased; it is about money spent twice on the same input. This reads <code>tool_actions</code> and asks whether generated output survived contact with a person; it is about money spent once, correctly, on something nobody wanted. One is a caching repair and the other is a project-setup repair, and neither of them is a substitute for reading the other.</p>
<p><strong>A low rate on a handful of proposals is noise, and the floor is the difference between an audit and an accusation.</strong> Three rejections out of four is a bad afternoon. Three hundred out of five hundred is a pattern. The script sets a proposal floor before it grades anything, and an actor under it comes back as insufficient evidence rather than as a finding, because this measurement is attached to a named person and getting it wrong is not a neutral event.</p>
<p><strong>The cost and the rate go side by side and are deliberately never multiplied.</strong> It is tempting to report "sixty per cent of this developer's spend was wasted", and it would be false: the report gives no per-proposal token counts, so there is no way to know whether the rejected diffs were the large ones or the small ones. The output prints the acceptance rate and the estimated cost as two separate readings and states that the product of them is not a number this API can support.</p>
<p><strong>Per-tool rates say more than a single average.</strong> <code>edit_tool</code>, <code>multi_edit_tool</code>, <code>write_tool</code> and <code>notebook_edit_tool</code> are counted separately, and they fail differently: a bad <code>multi_edit_tool</code> rate usually means a task that was scoped too wide, while a bad <code>write_tool</code> rate often means whole files being generated where an edit was wanted. Averaging them hides which of those is happening.</p>
<p><strong>The API will never tell you why, and pretending otherwise would be the failure mode of this note.</strong> There is no reason code on a rejection, no diff content, no prompt. What the report supports is naming the actors and the tools, printing the rate beside the volume and the commits, and handing that to the team that owns the repository. The repair &mdash; a project context file, a narrower task, a different model or effort level &mdash; is a judgement made by people who can see the code.</p>""",
"steps": [
 {"h": "Read the same report, one UTC day at a time",
  "body": """<p><code>GET /v1/organizations/usage_report/claude_code?starting_at=YYYY-MM-DD&amp;limit=1000</code>, paged on <code>next_page</code>, once per day. Records arrive with up to an hour's delay, so the window ends yesterday.</p>"""},
 {"h": "Sum tool_actions per actor and per tool",
  "body": """<p>Keep the four edit-producing tools apart: <code>edit_tool</code>, <code>multi_edit_tool</code>, <code>write_tool</code>, <code>notebook_edit_tool</code>. Sum <code>accepted</code> and <code>rejected</code> across days, per tool, per actor.</p>"""},
 {"h": "Apply the proposal floor before grading anyone",
  "body": """<p>An actor with fewer proposals than the floor is reported as insufficient evidence. This number sits next to a person's name, and a bad afternoon must not read as a pattern.</p>"""},
 {"h": "Compute the rate, and put the productivity metrics beside it",
  "body": """<p><code>accepted / (accepted + rejected)</code>, per tool and overall. Then <code>commits_by_claude_code</code>, <code>pull_requests_by_claude_code</code> and <code>lines_of_code</code>, because a low rate that still lands commits is a different conversation from a low rate that lands nothing.</p>"""},
 {"h": "Print the actors, the worst tool, and the cost as a separate reading",
  "body": """<p>The rate and the estimated cost are printed side by side and never multiplied, because the report carries no per-proposal token counts. The suggestion is to review project setup for those repositories, and it goes to the team, not into a change.</p>"""},
],
"verify": """<p>Re-run a fortnight after a project context file lands or a task pattern changes. The acceptance rate should move on the same volume of proposals. If the proposal count collapsed instead, the change was people using the tool less, which is not the improvement it looks like on this chart.</p>
<pre><code class="language-bash">python3 claude_code_edit_acceptance.py --days 14
# rejected-more-than-kept  d***@example.com   38% accepted over 412 proposal(s); worst tool multi_edit_tool at 21%, $310.40
#   repair: a majority of proposals are being discarded. Review project setup: a CLAUDE.md context file, and narrower task scoping.
# low-acceptance           e***@example.com   61% accepted over 208 proposal(s); worst tool write_tool at 44%, $96.10
# too-few-proposals        f***@example.com   9 proposal(s), under the floor of 20
# healthy                  g***@example.com   88% accepted over 340 proposal(s), 26 commit(s)
# 4 actor(s) over 14 day(s), 2 finding(s)
# the rate and the cost are separate readings: no per-proposal token counts exist to join them</code></pre>""",
"code_intro": "One GET per day and eight pure functions, none of which is shared with the cache note even though both read this endpoint. The actor reader and the mask; the <code>tool_actions</code> reader, which keeps the four tools apart; the fold, which also carries the commits, pull requests and lines so a rate is never read alone; the acceptance calculation, which returns <code>None</code> rather than zero when nobody proposed anything; the worst-tool picker with its own volume floor; the verdict with the proposal floor; and the repair lines, which suggest a conversation rather than a change. There is no function that multiplies a rate by a cost, and the absence is the point.",
"py_file": "claude_code_edit_acceptance.py",
"py": '''"""Find Claude Code actors whose edit proposals are mostly rejected.

Read only. One paged GET per UTC day against the Claude Code usage report with
an Admin API key. No message is sent and nothing is written.

Every rejected proposal was fully generated and fully billed before it was
displayed, so this is the one audit in the set whose subject is output that
succeeded, cost full rates, and was then thrown away by the person it was
produced for.

The acceptance rate and the estimated cost are printed as two separate
readings and are never multiplied. The report carries no per-proposal token
counts, so there is no way to know whether the rejected diffs were the large
ones or the small ones, and "60% of the spend was wasted" would be a sentence
this API cannot support.

The API never says why a proposal was rejected. The repair is a conversation
with the team that owns the repository, so it is printed rather than performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("claude_code_edit_acceptance")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The tools that propose a change a person then keeps or discards. Counted
# apart rather than averaged: a bad multi_edit rate usually means a task scoped
# too wide, and a bad write rate usually means whole files where an edit was
# wanted, and one number cannot say either.
EDIT_TOOLS = ("edit_tool", "multi_edit_tool", "write_tool", "notebook_edit_tool")

FINDINGS = ("rejected-more-than-kept", "low-acceptance")


def actor_name(record):
    """Who the record belongs to. Pure. Both actor shapes, plus neither."""
    actor = (record or {}).get("actor")
    if not isinstance(actor, dict):
        return "unattributed"
    for field in ("email_address", "api_key_name"):
        value = str(actor.get(field) or "").strip()
        if value:
            return value
    return "unattributed"


def mask(name):
    """Hide the local part of an email address. Pure. Non-emails pass through.

    This output attaches a quality number to a named person. Masked by default
    is the only sensible default for that.
    """
    text = str(name or "").strip()
    if "@" not in text:
        return text or "unattributed"
    local, _, domain = text.partition("@")
    if not local:
        return text
    return local[0] + "***@" + domain


def actions_of(record):
    """Accepted and rejected counts per edit tool on one record. Pure.

    Tools absent from the record are omitted rather than zeroed, because a tool
    nobody used and a tool used with nothing accepted must not look alike.
    """
    actions = (record or {}).get("tool_actions")
    actions = actions if isinstance(actions, dict) else {}
    out = {}
    for tool in EDIT_TOOLS:
        row = actions.get(tool)
        if not isinstance(row, dict):
            continue
        counts = {}
        for field in ("accepted", "rejected"):
            try:
                counts[field] = max(0, int(row.get(field) or 0))
            except (TypeError, ValueError):
                counts[field] = 0
        if counts["accepted"] or counts["rejected"]:
            out[tool] = counts
    return out


def fold(pages):
    """Fold every record into one row per actor. Pure.

    The productivity fields travel with the rate on purpose. A low acceptance
    rate beside twenty-six commits is a different conversation from a low rate
    beside none, and separating them invites the wrong one.
    """
    rows = {}
    for page in pages or []:
        for record in (page or {}).get("data") or []:
            if not isinstance(record, dict):
                continue
            who = actor_name(record)
            row = rows.setdefault(who, {
                "tools": {}, "days": 0, "sessions": 0, "commits": 0, "prs": 0,
                "added": 0, "removed": 0, "cents": 0.0})
            row["days"] += 1
            for tool, counts in actions_of(record).items():
                into = row["tools"].setdefault(tool, {"accepted": 0, "rejected": 0})
                into["accepted"] += counts["accepted"]
                into["rejected"] += counts["rejected"]

            core = record.get("core_metrics")
            core = core if isinstance(core, dict) else {}
            for field, key in (("num_sessions", "sessions"),
                               ("commits_by_claude_code", "commits"),
                               ("pull_requests_by_claude_code", "prs")):
                try:
                    row[key] += max(0, int(core.get(field) or 0))
                except (TypeError, ValueError):
                    pass
            lines = core.get("lines_of_code")
            lines = lines if isinstance(lines, dict) else {}
            for field, key in (("added", "added"), ("removed", "removed")):
                try:
                    row[key] += max(0, int(lines.get(field) or 0))
                except (TypeError, ValueError):
                    pass

            for entry in record.get("model_breakdown") or []:
                cost = (entry or {}).get("estimated_cost")
                cost = cost if isinstance(cost, dict) else {}
                try:
                    row["cents"] += float(cost.get("amount") or 0)
                except (TypeError, ValueError):
                    pass
    return rows


def totals(row):
    """Accepted and rejected across every edit tool for one actor. Pure."""
    accepted = 0
    rejected = 0
    for counts in ((row or {}).get("tools") or {}).values():
        accepted += max(0, int((counts or {}).get("accepted") or 0))
        rejected += max(0, int((counts or {}).get("rejected") or 0))
    return accepted, rejected


def acceptance(counts):
    """accepted / (accepted + rejected). Pure. None when nothing was proposed.

    None rather than 0.0. An actor who proposed nothing has no acceptance rate,
    and reporting one as zero would put them at the top of a list of the worst.
    """
    data = counts or {}
    accepted = max(0, int(data.get("accepted") or 0))
    rejected = max(0, int(data.get("rejected") or 0))
    total = accepted + rejected
    if total <= 0:
        return None
    return accepted / float(total)


def worst_tool(row, min_proposals=10):
    """The lowest-scoring tool with enough volume to mean it. Pure.

    Returns (tool, rate) or None. The per-tool floor is separate from and lower
    than the actor floor, because one tool is a slice of an actor's traffic.
    """
    worst = None
    for tool, counts in sorted(((row or {}).get("tools") or {}).items()):
        total = (max(0, int((counts or {}).get("accepted") or 0))
                 + max(0, int((counts or {}).get("rejected") or 0)))
        if total < min_proposals:
            continue
        rate = acceptance(counts)
        if rate is None:
            continue
        if worst is None or rate < worst[1]:
            worst = (tool, rate)
    return worst


def verdict(row, min_proposals=20, keep_floor=0.50, thin=0.70):
    """Classify one actor's acceptance. Pure. Returns (state, detail)."""
    accepted, rejected = totals(row)
    total = accepted + rejected
    if total < min_proposals:
        return ("too-few-proposals",
                "%d proposal(s), under the floor of %d: a bad afternoon is not "
                "a pattern" % (total, min_proposals))

    rate = acceptance({"accepted": accepted, "rejected": rejected})
    worst = worst_tool(row)
    tail = ""
    if worst is not None:
        tail = "; worst tool %s at %.0f%%" % (worst[0], worst[1] * 100)

    if rate < keep_floor:
        return ("rejected-more-than-kept",
                "%.0f%% accepted over %d proposal(s)%s: a majority of the "
                "diffs shown were discarded after being generated and billed"
                % (rate * 100, total, tail))
    if rate < thin:
        return ("low-acceptance",
                "%.0f%% accepted over %d proposal(s)%s"
                % (rate * 100, total, tail))
    return ("healthy",
            "%.0f%% accepted over %d proposal(s)%s" % (rate * 100, total, tail))


def repair_lines(state, row):
    """The repair for one classified actor. Pure. A conversation, not a change."""
    if state not in FINDINGS:
        return []
    commits = max(0, int((row or {}).get("commits") or 0))
    lines = [
        "review project setup for these repositories: a CLAUDE.md context "
        "file so the model knows where things live, and narrower task "
        "scoping so a proposal is small enough to be judged.",
        "check the model and effort level against the work. A frontier model "
        "on a mechanical edit produces confident, wide diffs that get "
        "rejected on scope rather than on correctness.",
    ]
    if commits > 0:
        lines.append("this actor still landed %d commit(s) in the window, so "
                     "the tool is producing accepted work as well. Read the "
                     "rate as a cost per accepted change, not as a failure."
                     % commits)
    else:
        lines.append("no commits landed through Claude Code in the window, so "
                     "there is no accepted work to weigh the rejections "
                     "against.")
    return lines


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params):
    """Walk one day of the paginated Claude Code usage report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def day_strings(days, today=None):
    """The UTC dates to request, newest first. Pure. Today is excluded."""
    end = today or dt.datetime.now(dt.timezone.utc).date()
    return [(end - dt.timedelta(days=n)).isoformat()
            for n in range(1, max(1, int(days)) + 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14,
                    help="UTC days to read, ending yesterday (default 14)")
    ap.add_argument("--min-proposals", type=int, default=20,
                    help="proposals below which no claim is made (default 20)")
    ap.add_argument("--floor", type=float, default=0.70,
                    help="acceptance below which a rate is called low")
    ap.add_argument("--show-actors", action="store_true",
                    help="print email addresses in full instead of masked")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    collected = []
    days = day_strings(args.days)
    for day in days:
        collected.extend(pages(s, "/organizations/usage_report/claude_code",
                               {"starting_at": day, "limit": 1000}))

    rows = fold(collected)
    if not rows:
        log.info("no Claude Code records over %d day(s). This report covers "
                 "Claude Code on the Claude API only.", len(days))
        return 0

    bad = 0
    for who in sorted(rows, key=lambda a: -rows[a]["cents"]):
        row = rows[who]
        state, detail = verdict(row, args.min_proposals, thin=args.floor)
        label = who if args.show_actors else mask(who)
        line = "%-24s %-20s %s, $%.2f" % (state, label, detail,
                                          row["cents"] / 100.0)
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            for repair in repair_lines(state, row):
                log.warning("  repair: %s", repair)
        else:
            log.info(line)

    log.info("%d actor(s) over %d day(s), %d finding(s)",
             len(rows), len(days), bad)
    log.info("the rate and the cost are separate readings: no per-proposal "
             "token counts exist to join them, so the share of spend that was "
             "discarded is not a number this API can support")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "claude-code-edit-acceptance.mjs",
"js": '''/**
 * Find Claude Code actors whose edit proposals are mostly rejected.
 *
 * Read only. One paged GET per UTC day against the Claude Code usage report
 * with an Admin API key.
 *
 * Every rejected proposal was fully generated and fully billed before it was
 * displayed. The acceptance rate and the estimated cost are printed as two
 * separate readings and are never multiplied: the report carries no
 * per-proposal token counts, so the share of spend that was discarded is not a
 * number this API can support.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// The tools that propose a change a person then keeps or discards. Counted
// apart rather than averaged, because they fail for different reasons.
const EDIT_TOOLS = ['edit_tool', 'multi_edit_tool', 'write_tool',
                    'notebook_edit_tool'];

const FINDINGS = new Set(['rejected-more-than-kept', 'low-acceptance']);

/** Who the record belongs to. Pure. Both actor shapes, plus neither. */
export function actorName(record) {
  const actor = record?.actor;
  if (!actor || typeof actor !== 'object') return 'unattributed';
  for (const field of ['email_address', 'api_key_name']) {
    const value = String(actor[field] ?? '').trim();
    if (value) return value;
  }
  return 'unattributed';
}

/** Hide the local part of an email address. Pure. Non-emails pass through. */
export function mask(name) {
  const text = String(name ?? '').trim();
  if (!text.includes('@')) return text || 'unattributed';
  const at = text.indexOf('@');
  const local = text.slice(0, at);
  if (!local) return text;
  return `${local[0]}***${text.slice(at)}`;
}

/**
 * Accepted and rejected counts per edit tool on one record. Pure.
 * A tool nobody used is omitted rather than zeroed.
 */
export function actionsOf(record) {
  const actions = record?.tool_actions && typeof record.tool_actions === 'object'
    ? record.tool_actions : {};
  const out = {};
  for (const tool of EDIT_TOOLS) {
    const row = actions[tool];
    if (!row || typeof row !== 'object') continue;
    const counts = {};
    for (const field of ['accepted', 'rejected']) {
      const n = Number(row[field] ?? 0);
      counts[field] = Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0;
    }
    if (counts.accepted || counts.rejected) out[tool] = counts;
  }
  return out;
}

/** Fold every record into one row per actor. Pure. Productivity travels with the rate. */
export function fold(pages) {
  const rows = {};
  for (const page of pages ?? []) {
    for (const record of page?.data ?? []) {
      if (!record || typeof record !== 'object') continue;
      const who = actorName(record);
      const row = rows[who] ?? { tools: {}, days: 0, sessions: 0, commits: 0,
                                 prs: 0, added: 0, removed: 0, cents: 0 };
      rows[who] = row;
      row.days += 1;
      for (const [tool, counts] of Object.entries(actionsOf(record))) {
        const into = row.tools[tool] ?? { accepted: 0, rejected: 0 };
        into.accepted += counts.accepted;
        into.rejected += counts.rejected;
        row.tools[tool] = into;
      }

      const core = record.core_metrics && typeof record.core_metrics === 'object'
        ? record.core_metrics : {};
      for (const [field, key] of [['num_sessions', 'sessions'],
                                  ['commits_by_claude_code', 'commits'],
                                  ['pull_requests_by_claude_code', 'prs']]) {
        const n = Number(core[field] ?? 0);
        if (Number.isFinite(n)) row[key] += Math.max(0, Math.trunc(n));
      }
      const lines = core.lines_of_code && typeof core.lines_of_code === 'object'
        ? core.lines_of_code : {};
      for (const key of ['added', 'removed']) {
        const n = Number(lines[key] ?? 0);
        if (Number.isFinite(n)) row[key] += Math.max(0, Math.trunc(n));
      }

      for (const entry of record.model_breakdown ?? []) {
        const cost = entry?.estimated_cost && typeof entry.estimated_cost === 'object'
          ? entry.estimated_cost : {};
        const n = Number(cost.amount ?? 0);
        if (Number.isFinite(n)) row.cents += n;
      }
    }
  }
  return rows;
}

/** Accepted and rejected across every edit tool for one actor. Pure. */
export function totals(row) {
  let accepted = 0;
  let rejected = 0;
  for (const counts of Object.values(row?.tools ?? {})) {
    accepted += Math.max(0, Number(counts?.accepted ?? 0));
    rejected += Math.max(0, Number(counts?.rejected ?? 0));
  }
  return [accepted, rejected];
}

/**
 * accepted / (accepted + rejected). Pure. Null when nothing was proposed.
 * Null rather than 0: an actor who proposed nothing has no rate, and zero
 * would put them at the top of a list of the worst.
 */
export function acceptance(counts) {
  const accepted = Math.max(0, Number(counts?.accepted ?? 0));
  const rejected = Math.max(0, Number(counts?.rejected ?? 0));
  const total = accepted + rejected;
  if (total <= 0) return null;
  return accepted / total;
}

/** The lowest-scoring tool with enough volume to mean it. Pure. Null when none. */
export function worstTool(row, minProposals = 10) {
  let worst = null;
  for (const [tool, counts] of Object.entries(row?.tools ?? {}).sort()) {
    const total = Math.max(0, Number(counts?.accepted ?? 0))
      + Math.max(0, Number(counts?.rejected ?? 0));
    if (total < minProposals) continue;
    const rate = acceptance(counts);
    if (rate === null) continue;
    if (worst === null || rate < worst[1]) worst = [tool, rate];
  }
  return worst;
}

/** Classify one actor's acceptance. Pure. Returns [state, detail]. */
export function verdict(row, minProposals = 20, keepFloor = 0.5, thin = 0.7) {
  const [accepted, rejected] = totals(row);
  const total = accepted + rejected;
  if (total < minProposals) {
    return ['too-few-proposals',
      `${total} proposal(s), under the floor of ${minProposals}: a bad ` +
      'afternoon is not a pattern'];
  }
  const rate = acceptance({ accepted, rejected });
  const worst = worstTool(row);
  const tail = worst === null ? ''
    : `; worst tool ${worst[0]} at ${(worst[1] * 100).toFixed(0)}%`;

  if (rate < keepFloor) {
    return ['rejected-more-than-kept',
      `${(rate * 100).toFixed(0)}% accepted over ${total} proposal(s)${tail}: ` +
      'a majority of the diffs shown were discarded after being generated and billed'];
  }
  if (rate < thin) {
    return ['low-acceptance',
      `${(rate * 100).toFixed(0)}% accepted over ${total} proposal(s)${tail}`];
  }
  return ['healthy',
    `${(rate * 100).toFixed(0)}% accepted over ${total} proposal(s)${tail}`];
}

/** The repair for one classified actor. Pure. A conversation, not a change. */
export function repairLines(state, row) {
  if (!FINDINGS.has(state)) return [];
  const commits = Math.max(0, Number(row?.commits ?? 0));
  const lines = [
    'review project setup for these repositories: a CLAUDE.md context file so ' +
    'the model knows where things live, and narrower task scoping so a ' +
    'proposal is small enough to be judged.',
    'check the model and effort level against the work. A frontier model on a ' +
    'mechanical edit produces confident, wide diffs that get rejected on ' +
    'scope rather than on correctness.',
  ];
  if (commits > 0) {
    lines.push(`this actor still landed ${commits} commit(s) in the window, so ` +
               'the tool is producing accepted work as well. Read the rate as ' +
               'a cost per accepted change, not as a failure.');
  } else {
    lines.push('no commits landed through Claude Code in the window, so there ' +
               'is no accepted work to weigh the rejections against.');
  }
  return lines;
}

/** The UTC dates to request, newest first. Pure. Today is excluded. */
export function dayStrings(days, today = new Date()) {
  const out = [];
  const count = Math.max(1, Math.trunc(Number(days) || 1));
  for (let n = 1; n <= count; n += 1) {
    const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(),
                                today.getUTCDate() - n));
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, v);
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs ` +
                    'an Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 14);
  const minProposals = Number(process.env.MIN_PROPOSALS ?? 20);
  const showActors = process.env.SHOW_ACTORS === '1';

  const dates = dayStrings(days);
  const collected = [];
  for (const day of dates) {
    const base = [['starting_at', day], ['limit', '1000']];
    let params = base;
    for (;;) {
      const page = await get(admin, '/organizations/usage_report/claude_code', params);
      collected.push(page);
      if (!page?.has_more || !page?.next_page) break;
      params = [...base, ['page', page.next_page]];
    }
  }

  const rows = fold(collected);
  const actors = Object.keys(rows);
  if (actors.length === 0) {
    console.log(`no Claude Code records over ${dates.length} day(s). This ` +
                'report covers Claude Code on the Claude API only.');
    return;
  }

  let bad = 0;
  for (const who of actors.sort((a, b) => rows[b].cents - rows[a].cents)) {
    const row = rows[who];
    const [state, detail] = verdict(row, minProposals);
    const label = showActors ? who : mask(who);
    const line = `${state.padEnd(24)} ${label.padEnd(20)} ${detail}, ` +
                 `$${(row.cents / 100).toFixed(2)}`;
    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      for (const repair of repairLines(state, row)) console.warn(`  repair: ${repair}`);
    } else {
      console.log(line);
    }
  }

  console.log(`${actors.length} actor(s) over ${dates.length} day(s), ${bad} finding(s)`);
  console.log('the rate and the cost are separate readings: no per-proposal ' +
              'token counts exist to join them, so the share of spend that was ' +
              'discarded is not a number this API can support');
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The headline test is four hundred and twelve proposals with a thirty-eight per cent acceptance rate, and the assertion that goes with it names the worst tool rather than the average, because <code>multi_edit_tool</code> at twenty-one per cent and <code>edit_tool</code> at sixty are two different repairs hiding in one number. The test beside it is the floor: nine proposals is a bad afternoon and must come back as insufficient evidence, because this figure sits next to a person's name. The rest pin the null rate for an actor who proposed nothing, the commits that travel with the verdict so a low rate is never read alone, tools that are absent rather than zeroed, and the accumulation across days.",
"test_py_file": "test_claude_code_edit_acceptance.py",
"test_py": '''import datetime as dt

from claude_code_edit_acceptance import (acceptance, actions_of, actor_name,
                                         day_strings, fold, mask, repair_lines,
                                         totals, verdict, worst_tool)


def record(email, tools, commits=0, cents="0", prs=0):
    return {"date": "2026-08-30",
            "actor": {"type": "user_actor", "email_address": email},
            "core_metrics": {"num_sessions": 6,
                             "commits_by_claude_code": commits,
                             "pull_requests_by_claude_code": prs,
                             "lines_of_code": {"added": 400, "removed": 90}},
            "tool_actions": tools,
            "model_breakdown": [{"model": "claude-opus-5",
                                 "tokens": {"input": 1, "output": 1},
                                 "estimated_cost": {"currency": "USD",
                                                    "amount": cents}}]}


def page(records):
    return {"data": records, "has_more": False}


def test_a_majority_of_generated_diffs_being_thrown_away_is_the_finding():
    # The note in one assertion. Every one of these 256 rejections was fully
    # generated and fully billed before anybody read it.
    rows = fold([page([record("busy@example.com", {
        "edit_tool": {"accepted": 120, "rejected": 80},
        "multi_edit_tool": {"accepted": 36, "rejected": 136},
        "write_tool": {"accepted": 0, "rejected": 40},
    }, commits=4, cents="31040")])])
    row = rows["busy@example.com"]
    assert totals(row) == (156, 256)

    state, detail = verdict(row)
    assert state == "rejected-more-than-kept"
    assert "38% accepted over 412 proposal(s)" in detail
    # The average hides which tool is the problem, so the worst is named.
    assert "worst tool write_tool at 0%" in detail
    assert worst_tool(row)[0] == "write_tool"
    assert any("CLAUDE.md" in line for line in repair_lines(state, row))


def test_a_bad_afternoon_is_not_a_pattern():
    rows = fold([page([record("quiet@example.com", {
        "edit_tool": {"accepted": 2, "rejected": 7}})])])
    state, detail = verdict(rows["quiet@example.com"])
    assert state == "too-few-proposals"
    assert "under the floor of 20" in detail
    assert repair_lines(state, rows["quiet@example.com"]) == []


def test_the_commits_travel_with_the_rate_so_it_is_never_read_alone():
    landing = fold([page([record("lands@example.com", {
        "edit_tool": {"accepted": 90, "rejected": 160}}, commits=26)])])
    row = landing["lands@example.com"]
    state, _ = verdict(row)
    assert state == "rejected-more-than-kept"
    assert any("26 commit(s)" in line for line in repair_lines(state, row))

    empty = fold([page([record("none@example.com", {
        "edit_tool": {"accepted": 90, "rejected": 160}}, commits=0)])])
    lines = repair_lines("rejected-more-than-kept", empty["none@example.com"])
    assert any("no commits landed" in line for line in lines)


def test_an_actor_who_proposed_nothing_has_no_rate_rather_than_zero():
    assert acceptance({"accepted": 0, "rejected": 0}) is None
    assert acceptance({}) is None
    assert acceptance({"accepted": 3, "rejected": 1}) == 0.75
    assert worst_tool({"tools": {}}) is None
    # Under the per-tool floor there is no worst tool to name.
    assert worst_tool({"tools": {"edit_tool": {"accepted": 1, "rejected": 2}}}) is None


def test_a_tool_nobody_used_is_absent_and_not_a_zero():
    actions = actions_of({"tool_actions": {
        "edit_tool": {"accepted": 4, "rejected": 1},
        "write_tool": {"accepted": 0, "rejected": 0},
        "bash_tool": {"accepted": 99, "rejected": 99}}})
    assert list(actions) == ["edit_tool"]
    assert actions_of({}) == {}
    assert actions_of(None) == {}
    assert actions_of({"tool_actions": {"edit_tool": {"accepted": "x",
                                                      "rejected": 3}}}) == \\
        {"edit_tool": {"accepted": 0, "rejected": 3}}


def test_counts_accumulate_across_days_and_across_actor_shapes():
    day = [record("a@example.com", {"edit_tool": {"accepted": 10, "rejected": 5}},
                  commits=1, cents="500"),
           {"actor": {"type": "api_actor", "api_key_name": "ci-runner"},
            "core_metrics": {"num_sessions": 1},
            "tool_actions": {"edit_tool": {"accepted": 30, "rejected": 2}},
            "model_breakdown": []}]
    rows = fold([page(day), page(day)])
    assert totals(rows["a@example.com"]) == (20, 10)
    assert rows["a@example.com"]["commits"] == 2
    assert rows["a@example.com"]["cents"] == 1000
    assert rows["a@example.com"]["added"] == 800
    assert totals(rows["ci-runner"]) == (60, 4)
    assert verdict(rows["ci-runner"])[0] == "healthy"


def test_actors_are_resolved_and_masked_before_being_printed():
    assert actor_name({"actor": {"email_address": "a@example.com"}}) == "a@example.com"
    assert actor_name({"actor": {"api_key_name": "ci"}}) == "ci"
    assert actor_name({}) == "unattributed"
    assert mask("someone@example.com") == "s***@example.com"
    assert mask("ci-runner") == "ci-runner"
    assert mask(None) == "unattributed"


def test_the_thin_band_sits_between_kept_and_healthy():
    row = {"tools": {"edit_tool": {"accepted": 61, "rejected": 39}}, "commits": 0}
    assert verdict(row)[0] == "low-acceptance"
    row = {"tools": {"edit_tool": {"accepted": 88, "rejected": 12}}, "commits": 0}
    assert verdict(row)[0] == "healthy"
    assert day_strings(2, dt.date(2026, 3, 1)) == ["2026-02-28", "2026-02-27"]
    assert fold([]) == {} and fold(None) == {}
''',
"test_js_file": "claude-code-edit-acceptance.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { acceptance, actionsOf, actorName, dayStrings, fold, mask, repairLines,
         totals, verdict, worstTool }
  from './claude-code-edit-acceptance.mjs';

const record = (email, tools, commits = 0, cents = 0, prs = 0) => ({
  date: '2026-08-30',
  actor: { type: 'user_actor', email_address: email },
  core_metrics: { num_sessions: 6, commits_by_claude_code: commits,
                  pull_requests_by_claude_code: prs,
                  lines_of_code: { added: 400, removed: 90 } },
  tool_actions: tools,
  model_breakdown: [{ model: 'claude-opus-5', tokens: { input: 1, output: 1 },
                      estimated_cost: { currency: 'USD', amount: cents } }],
});

const page = (records) => ({ data: records, has_more: false });

test('a majority of generated diffs being thrown away is the finding', () => {
  const rows = fold([page([record('busy@example.com', {
    edit_tool: { accepted: 120, rejected: 80 },
    multi_edit_tool: { accepted: 36, rejected: 136 },
    write_tool: { accepted: 0, rejected: 40 },
  }, 4, 31040)])]);
  const row = rows['busy@example.com'];
  assert.deepEqual(totals(row), [156, 256]);

  const [state, detail] = verdict(row);
  assert.equal(state, 'rejected-more-than-kept');
  assert.match(detail, /38% accepted over 412 proposal/);
  assert.match(detail, /worst tool write_tool at 0%/);
  assert.equal(worstTool(row)[0], 'write_tool');
  assert.ok(repairLines(state, row).some((l) => l.includes('CLAUDE.md')));
});

test('a bad afternoon is not a pattern', () => {
  const rows = fold([page([record('quiet@example.com', {
    edit_tool: { accepted: 2, rejected: 7 } })])]);
  const [state, detail] = verdict(rows['quiet@example.com']);
  assert.equal(state, 'too-few-proposals');
  assert.match(detail, /under the floor of 20/);
  assert.deepEqual(repairLines(state, rows['quiet@example.com']), []);
});

test('the commits travel with the rate so it is never read alone', () => {
  const landing = fold([page([record('lands@example.com', {
    edit_tool: { accepted: 90, rejected: 160 } }, 26)])]);
  const row = landing['lands@example.com'];
  const [state] = verdict(row);
  assert.equal(state, 'rejected-more-than-kept');
  assert.ok(repairLines(state, row).some((l) => l.includes('26 commit(s)')));

  const empty = fold([page([record('none@example.com', {
    edit_tool: { accepted: 90, rejected: 160 } }, 0)])]);
  assert.ok(repairLines('rejected-more-than-kept', empty['none@example.com'])
    .some((l) => l.includes('no commits landed')));
});

test('an actor who proposed nothing has no rate rather than zero', () => {
  assert.equal(acceptance({ accepted: 0, rejected: 0 }), null);
  assert.equal(acceptance({}), null);
  assert.equal(acceptance({ accepted: 3, rejected: 1 }), 0.75);
  assert.equal(worstTool({ tools: {} }), null);
  assert.equal(worstTool({ tools: { edit_tool: { accepted: 1, rejected: 2 } } }), null);
});

test('a tool nobody used is absent and not a zero', () => {
  const actions = actionsOf({ tool_actions: {
    edit_tool: { accepted: 4, rejected: 1 },
    write_tool: { accepted: 0, rejected: 0 },
    bash_tool: { accepted: 99, rejected: 99 } } });
  assert.deepEqual(Object.keys(actions), ['edit_tool']);
  assert.deepEqual(actionsOf({}), {});
  assert.deepEqual(actionsOf(null), {});
  assert.deepEqual(actionsOf({ tool_actions: { edit_tool: { accepted: 'x', rejected: 3 } } }),
    { edit_tool: { accepted: 0, rejected: 3 } });
});

test('counts accumulate across days and across actor shapes', () => {
  const day = [
    record('a@example.com', { edit_tool: { accepted: 10, rejected: 5 } }, 1, 500),
    { actor: { type: 'api_actor', api_key_name: 'ci-runner' },
      core_metrics: { num_sessions: 1 },
      tool_actions: { edit_tool: { accepted: 30, rejected: 2 } },
      model_breakdown: [] },
  ];
  const rows = fold([page(day), page(day)]);
  assert.deepEqual(totals(rows['a@example.com']), [20, 10]);
  assert.equal(rows['a@example.com'].commits, 2);
  assert.equal(rows['a@example.com'].cents, 1000);
  assert.equal(rows['a@example.com'].added, 800);
  assert.deepEqual(totals(rows['ci-runner']), [60, 4]);
  assert.equal(verdict(rows['ci-runner'])[0], 'healthy');
});

test('actors are resolved and masked before being printed', () => {
  assert.equal(actorName({ actor: { email_address: 'a@example.com' } }),
               'a@example.com');
  assert.equal(actorName({ actor: { api_key_name: 'ci' } }), 'ci');
  assert.equal(actorName({}), 'unattributed');
  assert.equal(mask('someone@example.com'), 's***@example.com');
  assert.equal(mask('ci-runner'), 'ci-runner');
  assert.equal(mask(null), 'unattributed');
});

test('the thin band sits between kept and healthy', () => {
  assert.equal(verdict({ tools: { edit_tool: { accepted: 61, rejected: 39 } },
                         commits: 0 })[0], 'low-acceptance');
  assert.equal(verdict({ tools: { edit_tool: { accepted: 88, rejected: 12 } },
                         commits: 0 })[0], 'healthy');
  assert.deepEqual(dayStrings(2, new Date('2026-03-01T06:00:00Z')),
    ['2026-02-28', '2026-02-27']);
  assert.deepEqual(fold([]), {});
  assert.deepEqual(fold(null), {});
});
''',
"faq": [
 ("Is a rejected edit wasted money?",
  "The tokens are spent either way, so in the narrow sense yes: the diff was generated at full output rates before it was displayed, and dismissing it does not refund anything. But rejection is also the review step working, and an occasional no is the system behaving correctly. What the note is about is a sustained majority, where the bulk of an actor's output budget goes to work nobody keeps, and that is a pattern rather than an event."),
 ("Why does the script not report the share of my spend that was discarded?",
  "Because the report carries no per-proposal token counts. To turn a rejection rate into a share of cost you would have to know whether the rejected diffs were the large ones or the small ones, and nothing on this endpoint says. The acceptance rate and the estimated cost are printed side by side and never multiplied, because a plausible-looking product of the two would be indistinguishable from a measurement."),
 ("How is this different from the other Claude Code note?",
  "Same endpoint, different block, opposite kind of conclusion. The cache note reads model_breakdown[].tokens and finds input being paid for twice because a prefix was not reused; that is a caching repair. This reads tool_actions and finds output that was generated once, correctly, and then discarded by the person it was for; that is a project-setup repair. Neither number tells you anything about the other, which is why they are two notes."),
 ("Which tool usually drags the rate down?",
  "In practice multi_edit_tool and write_tool, and for different reasons. A poor multi-edit rate usually means the task was scoped too wide, so one proposal touches more than a reviewer is willing to accept in one go. A poor write rate often means whole files being generated where a targeted edit was wanted. That is why the script keeps the four tools apart and names the worst one, instead of reporting a single average that hides both."),
 ("Can the API tell me why a proposal was rejected?",
  "No. There is no reason code, no diff content and no prompt on this endpoint; there is a count of accepted and a count of rejected, and that is the whole surface. The script names the actors, the tools and the rates, puts the commits and lines of code beside them so a low rate is not read in isolation, and hands the question to people who can see the repository. Anything more would be the script inventing an explanation."),
],
"related": [REL_CC_CACHE, REL_OUTPUT_COST, REL_FRONTIER],
"citations": [CITE_CC_ANALYTICS, CITE_CL_ANALYTICS, CITE_CL_PRICING,
              CITE_CL_USAGE_API],
},
]
# END OF BATCH N
