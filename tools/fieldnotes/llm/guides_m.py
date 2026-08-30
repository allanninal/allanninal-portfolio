#!/usr/bin/env python3
"""/llm/ field notes, batch M — the writing.

Four notes about one number. The cached share is zero, or near it, and the
number itself says nothing about why: the same zero is produced by a prompt
that was never eligible, by requests that never reach the machine holding
their cache, by an entry evicted while nobody was calling, and by a model
swap that moved the floor under a prefix nobody touched. Four causes, four
repairs, and no two of them share a fix.

The section already publishes three caching notes, so the ground here is
narrow and the discipline is the same in all four scripts: compute a shape
none of the others computes, and hand away by name every reading that belongs
to somebody else.

`prompt-below-model-cache-minimum` bracket a size. Anthropic's messages usage
report has no request count in it, so the prefix cannot be measured. It can be
cornered. One API key sends one prefix to several models, so if caching works
on the models with a low minimum and stops dead on the models with a high one,
the prefix sits between those two floors. The output is a range in tokens,
derived from a report that was never asked for one.

`prompt-cache-key-not-set` correlates. Routing scatter is the only cache fault
that gets *worse* as you scale out, so the signature is a rank correlation
between the hour's request count and the hour's cached share. Prefix
instability gives a flat low share at every load; this gives a slope. The
hours that follow a gap are dropped before anything is correlated, because
those run cold whatever the routing and leaving them in manufactures the
finding.

`prompt-cache-retention-left-at-default` measures position rather than volume.
It splits the hours into the ones that resume traffic after idle time and the
ones that follow a busy hour, and reports the shortest gap length at which the
share has already collapsed. That number and the retention setting are the
same number, which is what says whether the repair is a parameter or a
schedule.

`cache-hit-rate-collapsed-after-model-change` finds a changepoint and then
tries to disprove it. It computes the largest step down in the daily share
anywhere in the window and requires that step to sit where the new model id
first appears. The switch day itself is thrown away, because a cold cache on
day one of a new model is correct behaviour and a note that fires on it is
simply wrong.

Read only throughout. Two want an Anthropic Admin key, two want an OpenAI
organization admin key. Nothing here posts anything at all: no completion, not
even the free token counter. Every repair is a deploy with an owner, so it is
printed rather than performed.
"""

CITE_CL_CACHING = ("Prompt caching — Claude Docs",
                   "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
CITE_CL_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_CL_PRICING = ("Pricing — Claude Docs",
                   "https://platform.claude.com/docs/en/about-claude/pricing")
CITE_CL_MODELS = ("Models overview — Claude Docs",
                  "https://platform.claude.com/docs/en/models/overview")
CITE_OAI_CACHING = ("Prompt caching — OpenAI developer docs",
                    "https://developers.openai.com/api/docs/guides/prompt-caching")
CITE_OAI_USAGE = ("Usage — OpenAI API reference",
                  "https://platform.openai.com/docs/api-reference/usage")
CITE_OAI_USAGE_COMPLETIONS = ("Completions usage — OpenAI API reference",
                              "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_OAI_ADMIN = ("Admin APIs — OpenAI developer docs",
                  "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_OAI_RESPONSES = ("Responses — OpenAI API reference",
                      "https://platform.openai.com/docs/api-reference/responses")
CITE_OAI_COOKBOOK_USAGE = ("Completions usage API — OpenAI Cookbook",
                           "https://developers.openai.com/cookbook/examples/completions_usage_api")

REL_FLOOR = ("/llm/prompt-below-model-cache-minimum/",
             "A prefix bracketed between the floors of the models it runs on")
REL_SCATTER = ("/llm/prompt-cache-key-not-set/",
               "A cached share that degrades exactly when the fleet is widest")
REL_EVICT = ("/llm/prompt-cache-retention-left-at-default/",
             "Every scheduled run starting on an entry that expired overnight")
REL_STEP = ("/llm/cache-hit-rate-collapsed-after-model-change/",
            "A step down in cache reads aligned with a new model id")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "Prompt caching that was never switched on at all")
REL_CACHE_WRITES = ("/llm/cache-writes-with-no-reads/",
                    "Cache writes paid for at a premium and never read back")
REL_CHURN = ("/llm/cache-invalidated-by-changing-prefix/",
             "A prefix that changes every call, so nothing is ever read back")
REL_ALIAS = ("/llm/floating-alias-instead-of-pinned-snapshot/",
             "A model id that moves under you without a deploy")

GUIDES = [
{
"slug": "prompt-below-model-cache-minimum",
"title": "Prompt sits under the model's cache minimum, so nothing caches",
"description": "cache_control is accepted and ignored below the floor. Caching that works on one model and stops on another brackets the prefix between two minimums.",
"h1": "Prompt sits under the model's cache minimum, so nothing caches",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["minimum cacheable prompt length claude",
             "cache_control ignored no error",
             "cache_creation zero cache_read zero",
             "claude haiku 4.5 cache minimum 4096",
             "prompt too short to cache"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin...) provisioned read-only. A workspace key is rejected by every /v1/organizations/ path.",
"lead": "The <code>cache_control</code> breakpoint has been in that request builder since March, and the Haiku route has never reported a cache read. Not a small number: zero, in every daily bucket, on a key whose Opus traffic caches beautifully off the same code path. Nothing errored, because nothing was wrong. The prefix is about fifteen hundred tokens. Opus 5 starts caching at five hundred and twelve. Haiku 4.5 does not start until four thousand and ninety six. The parameter was accepted and thrown away.",
"short_answer": """<p>With an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=model&amp;group_by[]=api_key_id</code>.</p>
<p>For each key, split its models into the ones with any cache activity and the ones where <code>cache_creation.*</code> and <code>cache_read_input_tokens</code> are both <em>exactly</em> zero with real <code>uncached_input_tokens</code> behind them. Attach each model's documented minimum cacheable length. If every silent model sits above every caching one, the prefix is bracketed: at least the highest floor that still works, and under the lowest floor that does not.</p>
<p>That bracket is a size, and the report it came from has no request count and no prompt in it. It is the only way to measure a prefix here without sending anything.</p>
<p>The minimums are <strong>512</strong> (Opus 5, Fable 5, Mythos 5), <strong>1,024</strong> (Sonnet 5, Sonnet 4.6, Sonnet 4.5, Sonnet 4, Opus 4.8, Opus 4.1, Opus 4), <strong>2,048</strong> (Opus 4.7, Mythos Preview, Haiku 3.5) and <strong>4,096</strong> (Opus 4.6, Opus 4.5, Haiku 4.5). A migration from Opus 5 to Haiku 4.5 raises the bar eightfold on a prompt nobody edited.</p>""",
"problem": """<p>Prompt caching on Claude is opt-in and, below a certain prefix length, inert. You set <code>cache_control: {"type": "ephemeral"}</code>, the request validates, the response comes back, and the API silently declines to cache anything because the prefix did not clear the model's minimum. There is no error, no warning header and no field on the response saying the breakpoint was ignored. The only trace is an absence: two counters that stay at zero while the code that should be filling them runs thousands of times a day.</p>
<p>What makes it survive review is that the absence looks exactly like three other absences. A team that never switched caching on sees the same two zeros. A team whose prefix changes on every call sees zero reads. A team whose traffic is slower than the TTL sees zero reads too. Four different problems, one dashboard tile, and the tile is the same shade of nothing in all four cases.</p>""",
"why": """<p><strong>The prefix cannot be measured from this report, so it has to be bracketed instead.</strong> Anthropic's messages usage report returns token sums per bucket and carries no request count at all, which means there is no honest way to divide input tokens by calls and get a prefix size. What there is instead is a natural experiment already running in your account: one API key, one request builder, several model ids. The prompt is the same for all of them and only the floor moves. Caching that works below one floor and stops above another puts the prefix between the two, and that is a number rather than a shrug.</p>
<p><strong>Zero is not a small number here, it is a different state.</strong> The check requires <code>cache_creation.ephemeral_5m_input_tokens</code>, <code>cache_creation.ephemeral_1h_input_tokens</code> and <code>cache_read_input_tokens</code> to be exactly zero on the silent side. A model that writes a little and reads nothing is not ineligible, it is failing to match, and that is <a href="/llm/cache-invalidated-by-changing-prefix/">a different note</a> with a different repair. Ineligibility means the API never even tried.</p>
<p><strong>A silent model beneath a caching one disproves the whole story.</strong> If Opus 5 with a floor of 512 is silent while Haiku 4.5 with a floor of 4,096 is caching, the same prompt already cleared the higher bar and size cannot be the explanation. The bracket is only computed when the split is clean, and when it is not, the script says so and hands the reader elsewhere rather than reporting a range it cannot support.</p>
<p><strong>A model with no known floor is left out, never assumed to be zero.</strong> The minimums come from a table, and a table goes stale the moment a model ships. An unrecognised id is skipped in both directions: it cannot be the low end of a bracket, where a floor of zero would invent one out of nothing, and it cannot be the high end. Being unable to judge a model is a better outcome than judging it wrongly and printing a token range with false precision.</p>
<p><strong>One prefix per key is the assumption, and it is stated rather than hidden.</strong> A key that deliberately sends a short prompt to Haiku and a long one to Opus brackets nothing, because the premise of the comparison is broken. The aggregate cannot see inside a key, so the finding is strongest on a key serving one workload and the output says exactly that. The cross-check for the ambiguous case is a peer key: if another key in the organization caches on the same model, the model's floor is not what is stopping you.</p>""",
"steps": [
 {"h": "Pull thirty days grouped by model and by key",
  "body": """<p><code>bucket_width=1d</code>, <code>group_by[]=model</code> and <code>group_by[]=api_key_id</code> together. Grouping by model alone folds a caching route and a silent one into a single row and destroys the contrast the whole check runs on. Thirty days is long enough that a quiet weekend cannot fake a zero.</p>"""},
 {"h": "Split each key's models into caching and silent",
  "body": """<p>Caching means <code>cache_creation.ephemeral_5m_input_tokens + cache_creation.ephemeral_1h_input_tokens + cache_read_input_tokens</code> greater than zero. Silent means all three at exactly zero with a material <code>uncached_input_tokens</code> behind them. A model that barely ran is evidence of nothing and is dropped.</p>"""},
 {"h": "Attach the documented minimum to each model id",
  "body": """<p>Longest-prefix match against the published table, because the ids in a usage report are dated snapshots: <code>claude-haiku-4-5-20251001</code> has to resolve through <code>claude-haiku-4-5</code>, and <code>claude-opus-4-5</code> must not be swallowed by <code>claude-opus-4</code>, which has a different floor. Anything unrecognised gets no floor and no vote.</p>"""},
 {"h": "Check the split is clean before believing the bracket",
  "body": """<p>Every silent model must sit above every caching one. If a low-floor model is silent while a high-floor one caches, the prompt has already proved it can clear the higher bar and the finding belongs to the prefix-instability note instead.</p>"""},
 {"h": "Read the bracket, then decide which side to move",
  "body": """<p>The output is a range in tokens. Either lift the cached prefix past the upper floor with genuinely stable material &mdash; full tool schemas, few-shot examples, retrieval instructions &mdash; or drop <code>cache_control</code> on the routes above the boundary so the code stops claiming a discount it will never get. Do not pad with filler: padding is billed at the full input rate on the write.</p>"""},
],
"verify": """<p>Re-read the same window the day after the breakpoint moves. What should appear first is a non-zero <code>cache_creation</code> on the model that was silent; reads follow on the second day, once there is an entry to match.</p>
<pre><code class="language-bash">python3 anthropic_cache_floor_bracket.py --days 30
# below-cache-minimum              apikey_01Ab  caching works up to a floor of 1024 (claude-sonnet-5) and stops at 2048 (claude-haiku-3-5), so the cached prefix is at least 1024 tokens and under 2048. cache_control is being accepted and ignored above the boundary.
#   repair: move more genuinely stable material in front of the last cache_control breakpoint until the prefix clears 2048 tokens
#   repair: or drop cache_control on the routes above the boundary so the code is honest about not caching there
#   note: the bracket assumes one prefix per key.
# 6 key(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET and no second call, because the contrast the check needs is already inside the one response. Eight pure functions: the floor lookup, which is longest-prefix so a dated snapshot resolves and <code>claude-opus-4-5</code> is not swallowed by <code>claude-opus-4</code>; the accumulator, which reaches into the nested <code>cache_creation</code> object; the regrouping into one row per model per key; the org-wide set of models that cache for <em>anyone</em>, which is the control for the single-model case; the three-way split into caching, silent and unjudgeable; the bracket itself, which returns nothing unless the split is clean; the repair lines, sized to the bracket; and the classifier, whose first four branches exist to give the finding away.",
"py_file": "anthropic_cache_floor_bracket.py",
"py": '''"""Bracket a cached prefix against the cache minimums of the models it runs on.

Read only. One GET against the Admin API, which needs an Admin API key
(sk-ant-admin...); a workspace key is rejected by every /v1/organizations/
path, and an Admin key can be provisioned read-only.

A prefix shorter than a model's minimum cacheable token count is not cached and
no error is raised for it: cache_control is accepted and ignored. The messages
usage report carries no request count, so the prefix cannot be measured
directly from it. It can be bracketed. One API key that runs several models
sends the same prefix to all of them, so if caching works on the models with a
low minimum and stops dead on the models with a high one, the prefix sits
between the two floors. That bracket is the finding, and it is a size the
report was never asked for.

The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_cache_floor_bracket")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Published minimum cacheable prompt length per model family, in tokens. Longest
# prefix wins, so a dated id such as claude-haiku-4-5-20251001 resolves through
# claude-haiku-4-5. A model that is not in this table gets no floor and is left
# out of the verdict rather than guessed at: a wrong floor here would invent a
# bracket that does not exist.
CACHE_MINIMUMS = {
    "claude-opus-5": 512,
    "claude-fable-5": 512,
    "claude-mythos-5": 512,
    "claude-mythos-preview": 2048,
    "claude-opus-4-8": 1024,
    "claude-opus-4-7": 2048,
    "claude-opus-4-6": 4096,
    "claude-opus-4-5": 4096,
    "claude-opus-4-1": 1024,
    "claude-opus-4": 1024,
    "claude-sonnet-5": 1024,
    "claude-sonnet-4-6": 1024,
    "claude-sonnet-4-5": 1024,
    "claude-sonnet-4": 1024,
    "claude-haiku-4-5": 4096,
    "claude-haiku-3-5": 2048,
}

FINDINGS = ("below-cache-minimum",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def cache_minimum(model):
    """The model's minimum cacheable prompt length, in tokens. Pure.

    Longest prefix match, because the ids that actually appear in a usage report
    are dated snapshots. None for anything unrecognised, and None has to mean
    "no opinion" everywhere downstream rather than "no floor": a model quietly
    treated as floor zero would land on the caching side of every bracket.
    """
    name = str(model or "").strip().lower()
    if not name:
        return None
    best = None
    for family, floor in CACHE_MINIMUMS.items():
        if name == family or name.startswith(family + "-"):
            if best is None or len(family) > len(best[0]):
                best = (family, floor)
    return best[1] if best else None


def series(buckets):
    """Per (api_key_id, model), the window's token totals. Pure."""
    out = {}
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            ident = (str(result.get("api_key_id") or "unknown"),
                     str(result.get("model") or "unknown"))
            creation = result.get("cache_creation") or {}
            row = out.setdefault(ident, {"uncached": 0, "writes": 0, "reads": 0})
            row["uncached"] += _int(result.get("uncached_input_tokens"))
            row["writes"] += (_int(creation.get("ephemeral_5m_input_tokens"))
                              + _int(creation.get("ephemeral_1h_input_tokens")))
            row["reads"] += _int(result.get("cache_read_input_tokens"))
    return out


def by_key(totals):
    """Regroup the series into one list of model rows per api_key_id. Pure."""
    out = {}
    for (key, model), row in (totals or {}).items():
        out.setdefault(key, []).append({
            "model": model, "floor": cache_minimum(model),
            "uncached": _int(row.get("uncached")), "writes": _int(row.get("writes")),
            "reads": _int(row.get("reads")),
        })
    for rows in out.values():
        rows.sort(key=lambda r: (r["floor"] if r["floor"] is not None else 10 ** 9,
                                 r["model"]))
    return out


def models_caching_anywhere(totals):
    """Models that cache for at least one key in the org. Pure.

    The cross-key control. If another key caches on the same model, that model
    is not the obstacle and this key's silence is about its own prompt.
    """
    return {model for (_key, model), row in (totals or {}).items()
            if _int(row.get("writes")) + _int(row.get("reads")) > 0}


def split_rows(rows, min_input=100_000):
    """Sort a key's models into caching, silent and unusable. Pure.

    Silent means both cache counters are exactly zero with real input behind
    them. Zero is not a small number here; it is the state cache_control
    produces when the API declines to honour it.
    """
    caching, silent, skipped = [], [], []
    for row in rows or []:
        if row.get("floor") is None:
            skipped.append(row)
        elif _int(row.get("writes")) + _int(row.get("reads")) > 0:
            caching.append(row)
        elif _int(row.get("uncached")) >= min_input:
            silent.append(row)
        else:
            skipped.append(row)
    return caching, silent, skipped


def floor_bracket(caching, silent):
    """Bracket the cached prefix between two floors. Pure. None if it does not.

    lo is the highest floor the key still caches at, hi the lowest floor at
    which it stops. The bracket exists only when the split is clean: every
    silent model sits above every caching one. A silent model beneath a caching
    one is not an eligibility story at all, because the same prompt cleared the
    higher bar.
    """
    if not caching or not silent:
        return None
    lo = max(_int(r.get("floor")) for r in caching)
    hi = min(_int(r.get("floor")) for r in silent)
    if hi <= lo:
        return None
    return (lo, hi)


def handoff(state):
    """Which note owns this shape, when it is not this one. Pure."""
    if state == "no-caching-anywhere":
        return ("this key writes and reads nothing on any model, so there is no "
                "contrast to bracket against. Read the prompt-caching-never-used "
                "note: with no cache_control anywhere the floors are irrelevant.")
    if state == "silent-model-under-a-caching-floor":
        return ("a model with a lower floor is silent while a model with a "
                "higher floor caches, so the prefix cleared the higher bar and "
                "size cannot be the reason. Read the "
                "cache-invalidated-by-changing-prefix note.")
    if state == "peer-caches-same-model":
        return ("another key in this organization caches on this same model, so "
                "the model's floor is not the obstacle. Read the "
                "cache-invalidated-by-changing-prefix note.")
    if state == "single-silent-model":
        return ("one model and no contrast, so this check cannot separate a "
                "prefix under the floor from caching that was never switched "
                "on. Both prompt-caching-never-used and this note remain open. "
                "Route a sample of the traffic through a model with a lower "
                "floor and the ambiguity resolves itself.")
    return ""


def classify(rows, caching_models=(), min_input=100_000):
    """Classify one api_key_id. Pure. Returns (state, detail).

    Only a key that caches under one floor and goes silent above it belongs to
    this note. Everything else is handed away, most of it by name.
    """
    caching, silent, skipped = split_rows(rows, min_input)
    if not caching and not silent:
        return ("too-little-traffic",
                "%d model(s) seen, none with a known floor and enough input to "
                "judge" % len(skipped or []))

    if not caching:
        if len(silent) == 1:
            model = silent[0]["model"]
            if model in set(caching_models or ()):
                return ("peer-caches-same-model",
                        "silent on %s (floor %d) while another key caches on the "
                        "same model" % (model, _int(silent[0]["floor"])))
            return ("single-silent-model",
                    "silent on %s (floor %d) and running nothing else, so there "
                    "is no second floor to bracket against"
                    % (model, _int(silent[0]["floor"])))
        return ("no-caching-anywhere",
                "silent on all %d model(s) with known floors: %s"
                % (len(silent), ", ".join(r["model"] for r in silent)))

    if not silent:
        return ("caches-on-every-model",
                "cache activity on all %d model(s) with known floors" % len(caching))

    bracket = floor_bracket(caching, silent)
    if bracket is None:
        low = min(silent, key=lambda r: _int(r.get("floor")))
        high = max(caching, key=lambda r: _int(r.get("floor")))
        return ("silent-model-under-a-caching-floor",
                "%s (floor %d) is silent while %s (floor %d) caches"
                % (low["model"], _int(low["floor"]), high["model"],
                   _int(high["floor"])))

    lo, hi = bracket
    return ("below-cache-minimum",
            "caching works up to a floor of %d (%s) and stops at %d (%s), so the "
            "cached prefix is at least %d tokens and under %d. cache_control is "
            "being accepted and ignored above the boundary."
            % (lo, ", ".join(r["model"] for r in caching if _int(r["floor"]) == lo),
               hi, ", ".join(r["model"] for r in silent if _int(r["floor"]) == hi),
               lo, hi))


def repair_lines(bracket):
    """The two honest repairs, sized to the bracket. Pure."""
    if not bracket:
        return []
    lo, hi = bracket
    return [
        "move more genuinely stable material in front of the last cache_control "
        "breakpoint until the prefix clears %d tokens: full tool schemas, "
        "few-shot examples, retrieval instructions." % hi,
        "or drop cache_control on the routes above the boundary so the code is "
        "honest about not caching there, and stop budgeting for a discount that "
        "cannot arrive.",
        "do not pad with filler to cross %d. Padding is billed at the full input "
        "rate on the write and only pays back at high repeat volume." % hi,
        "the bracket is %d to %d tokens. If that straddles a route you thought "
        "was much longer, the prefix is being truncated or rebuilt somewhere "
        "before the breakpoint." % (lo, hi),
    ]


def window_start(days):
    """Floor to the day: starting_at has to sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0,
                                                   microsecond=0)
    return (now - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily buckets to read (max 90)")
    ap.add_argument("--min-input", type=int, default=100_000,
                    help="uncached input tokens a silent model needs before its "
                         "silence counts as evidence")
    ap.add_argument("--show-all", action="store_true",
                    help="also print keys that are behaving")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key "
                  "(sk-ant-admin...); a workspace key cannot read "
                  "/v1/organizations/")
        return 2

    days = max(2, min(int(args.days), 90))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    buckets = read_buckets(session, "/organizations/usage_report/messages", {
        "starting_at": window_start(days),
        "bucket_width": "1d",
        "limit": days + 1,
        "group_by[]": ["model", "api_key_id"],
    })

    totals = series(buckets)
    if not totals:
        log.info("no messages usage in the last %d day(s)", days)
        return 0

    caching_models = models_caching_anywhere(totals)
    keyed = by_key(totals)

    checked = 0
    bad = 0
    for key in sorted(keyed):
        rows = keyed[key]
        state, detail = classify(rows, caching_models, args.min_input)
        checked += 1
        line = "%-32s %s  %s" % (state, key, detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            caching, silent, _ = split_rows(rows, args.min_input)
            for repair in repair_lines(floor_bracket(caching, silent)):
                log.warning("  repair: %s", repair)
            log.warning("  note: the bracket assumes one prefix per key. A key "
                        "that sends a different prompt per model brackets "
                        "nothing, and the report cannot see inside a key.")
        else:
            note = handoff(state)
            if note:
                log.info(line)
                log.info("  %s", note)
            elif args.show_all:
                log.info(line)

    log.info("%d key(s) checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-cache-floor-bracket.mjs",
"js": '''/**
 * Bracket a cached prefix against the cache minimums of the models it runs on.
 *
 * Read only. One GET against the Admin API, which needs an Admin API key
 * (sk-ant-admin...). A workspace key is rejected by /v1/organizations/.
 *
 * A prefix under a model's minimum cacheable length is silently not cached.
 * The messages usage report has no request count, so the prefix cannot be
 * measured from it. It can be bracketed: one key that runs several models
 * sends the same prefix to all of them, so caching that works below one floor
 * and stops above another puts the prefix between the two.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const FINDINGS = new Set(['below-cache-minimum']);

/**
 * Published minimum cacheable prompt length per model family, in tokens.
 * A model absent from this table gets no floor and is left out of the verdict
 * rather than guessed at.
 */
export const CACHE_MINIMUMS = {
  'claude-opus-5': 512,
  'claude-fable-5': 512,
  'claude-mythos-5': 512,
  'claude-mythos-preview': 2048,
  'claude-opus-4-8': 1024,
  'claude-opus-4-7': 2048,
  'claude-opus-4-6': 4096,
  'claude-opus-4-5': 4096,
  'claude-opus-4-1': 1024,
  'claude-opus-4': 1024,
  'claude-sonnet-5': 1024,
  'claude-sonnet-4-6': 1024,
  'claude-sonnet-4-5': 1024,
  'claude-sonnet-4': 1024,
  'claude-haiku-4-5': 4096,
  'claude-haiku-3-5': 2048,
};

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * The model's minimum cacheable prompt length. Pure. Null if unrecognised.
 * Longest prefix match, because usage reports carry dated snapshot ids, and
 * null has to mean "no opinion" rather than "floor zero" downstream.
 */
export function cacheMinimum(model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return null;
  let best = null;
  for (const [family, floor] of Object.entries(CACHE_MINIMUMS)) {
    if (name === family || name.startsWith(`${family}-`)) {
      if (best === null || family.length > best[0].length) best = [family, floor];
    }
  }
  return best ? best[1] : null;
}

/** Per api_key_id and model, the window's token totals. Pure. */
export function series(buckets) {
  const out = new Map();
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      if (!result || typeof result !== 'object') continue;
      const ident = `${result.api_key_id ?? 'unknown'}\\t${result.model ?? 'unknown'}`;
      if (!out.has(ident)) out.set(ident, { uncached: 0, writes: 0, reads: 0 });
      const row = out.get(ident);
      const creation = result.cache_creation ?? {};
      row.uncached += readInt(result.uncached_input_tokens);
      row.writes += readInt(creation.ephemeral_5m_input_tokens)
        + readInt(creation.ephemeral_1h_input_tokens);
      row.reads += readInt(result.cache_read_input_tokens);
    }
  }
  return out;
}

/** Regroup the series into one list of model rows per api_key_id. Pure. */
export function byKey(totals) {
  const out = new Map();
  for (const [ident, row] of totals ?? new Map()) {
    const [key, model] = String(ident).split('\\t');
    if (!out.has(key)) out.set(key, []);
    out.get(key).push({
      model,
      floor: cacheMinimum(model),
      uncached: readInt(row?.uncached),
      writes: readInt(row?.writes),
      reads: readInt(row?.reads),
    });
  }
  for (const rows of out.values()) {
    rows.sort((a, b) => (a.floor ?? 1e9) - (b.floor ?? 1e9)
      || a.model.localeCompare(b.model));
  }
  return out;
}

/** Models that cache for at least one key in the org. Pure. The cross-key control. */
export function modelsCachingAnywhere(totals) {
  const out = new Set();
  for (const [ident, row] of totals ?? new Map()) {
    if (readInt(row?.writes) + readInt(row?.reads) > 0) {
      out.add(String(ident).split('\\t')[1]);
    }
  }
  return out;
}

/** Sort a key's models into caching, silent and unusable. Pure. */
export function splitRows(rows, minInput = 100000) {
  const caching = [];
  const silent = [];
  const skipped = [];
  for (const row of rows ?? []) {
    if (row?.floor === null || row?.floor === undefined) skipped.push(row);
    else if (readInt(row?.writes) + readInt(row?.reads) > 0) caching.push(row);
    else if (readInt(row?.uncached) >= minInput) silent.push(row);
    else skipped.push(row);
  }
  return { caching, silent, skipped };
}

/**
 * Bracket the cached prefix between two floors. Pure. Null if it does not.
 * The bracket exists only when the split is clean: every silent model above
 * every caching one. A silent model beneath a caching one means the prompt
 * already cleared the higher bar, so size is not the story.
 */
export function floorBracket(caching, silent) {
  if (!caching?.length || !silent?.length) return null;
  const lo = Math.max(...caching.map((r) => readInt(r?.floor)));
  const hi = Math.min(...silent.map((r) => readInt(r?.floor)));
  if (hi <= lo) return null;
  return [lo, hi];
}

/** Which note owns this shape, when it is not this one. Pure. */
export function handoff(state) {
  if (state === 'no-caching-anywhere') {
    return 'this key writes and reads nothing on any model, so there is no '
      + 'contrast to bracket against. Read the prompt-caching-never-used note: '
      + 'with no cache_control anywhere the floors are irrelevant.';
  }
  if (state === 'silent-model-under-a-caching-floor') {
    return 'a model with a lower floor is silent while a model with a higher '
      + 'floor caches, so the prefix cleared the higher bar and size cannot be '
      + 'the reason. Read the cache-invalidated-by-changing-prefix note.';
  }
  if (state === 'peer-caches-same-model') {
    return 'another key in this organization caches on this same model, so the '
      + "model's floor is not the obstacle. Read the "
      + 'cache-invalidated-by-changing-prefix note.';
  }
  if (state === 'single-silent-model') {
    return 'one model and no contrast, so this check cannot separate a prefix '
      + 'under the floor from caching that was never switched on. Both '
      + 'prompt-caching-never-used and this note remain open. Route a sample of '
      + 'the traffic through a model with a lower floor and the ambiguity '
      + 'resolves itself.';
  }
  return '';
}

/** Classify one api_key_id. Pure. Returns [state, detail]. */
export function classify(rows, cachingModels = new Set(), minInput = 100000) {
  const { caching, silent, skipped } = splitRows(rows, minInput);
  if (!caching.length && !silent.length) {
    return ['too-little-traffic',
      `${skipped.length} model(s) seen, none with a known floor and enough input to judge`];
  }

  if (!caching.length) {
    if (silent.length === 1) {
      const row = silent[0];
      if (cachingModels?.has?.(row.model)) {
        return ['peer-caches-same-model',
          `silent on ${row.model} (floor ${readInt(row.floor)}) while another `
          + 'key caches on the same model'];
      }
      return ['single-silent-model',
        `silent on ${row.model} (floor ${readInt(row.floor)}) and running `
        + 'nothing else, so there is no second floor to bracket against'];
    }
    return ['no-caching-anywhere',
      `silent on all ${silent.length} model(s) with known floors: `
      + silent.map((r) => r.model).join(', ')];
  }

  if (!silent.length) {
    return ['caches-on-every-model',
      `cache activity on all ${caching.length} model(s) with known floors`];
  }

  const bracket = floorBracket(caching, silent);
  if (bracket === null) {
    const low = silent.reduce((a, b) => (readInt(a.floor) <= readInt(b.floor) ? a : b));
    const high = caching.reduce((a, b) => (readInt(a.floor) >= readInt(b.floor) ? a : b));
    return ['silent-model-under-a-caching-floor',
      `${low.model} (floor ${readInt(low.floor)}) is silent while ${high.model} `
      + `(floor ${readInt(high.floor)}) caches`];
  }

  const [lo, hi] = bracket;
  const loNames = caching.filter((r) => readInt(r.floor) === lo).map((r) => r.model).join(', ');
  const hiNames = silent.filter((r) => readInt(r.floor) === hi).map((r) => r.model).join(', ');
  return ['below-cache-minimum',
    `caching works up to a floor of ${lo} (${loNames}) and stops at ${hi} `
    + `(${hiNames}), so the cached prefix is at least ${lo} tokens and under `
    + `${hi}. cache_control is being accepted and ignored above the boundary.`];
}

/** The two honest repairs, sized to the bracket. Pure. */
export function repairLines(bracket) {
  if (!bracket) return [];
  const [lo, hi] = bracket;
  return [
    'move more genuinely stable material in front of the last cache_control '
    + `breakpoint until the prefix clears ${hi} tokens: full tool schemas, `
    + 'few-shot examples, retrieval instructions.',
    'or drop cache_control on the routes above the boundary so the code is '
    + 'honest about not caching there, and stop budgeting for a discount that '
    + 'cannot arrive.',
    `do not pad with filler to cross ${hi}. Padding is billed at the full input `
    + 'rate on the write and only pays back at high repeat volume.',
    `the bracket is ${lo} to ${hi} tokens. If that straddles a route you thought `
    + 'was much longer, the prefix is being truncated or rebuilt somewhere '
    + 'before the breakpoint.',
  ];
}

function windowStart(days) {
  const now = new Date();
  now.setUTCHours(0, 0, 0, 0);
  return `${new Date(now.getTime() - days * 86400000).toISOString().slice(0, 19)}Z`;
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
    throw new Error(`${res.status} from Anthropic: /v1/organizations/ needs an `
                    + 'Admin API key (sk-ant-admin...), not a workspace key');
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
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); '
                  + 'a workspace key cannot read /v1/organizations/');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(2, Math.min(Number(process.env.DAYS ?? 30), 90));
  const minInput = Number(process.env.MIN_INPUT ?? 100000);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organizations/usage_report/messages', {
    starting_at: windowStart(days),
    bucket_width: '1d',
    limit: days + 1,
    'group_by[]': ['model', 'api_key_id'],
  })) buckets.push(bucket);

  const totals = series(buckets);
  if (totals.size === 0) {
    console.log(`no messages usage in the last ${days} day(s)`);
    return;
  }

  const cachingModels = modelsCachingAnywhere(totals);
  const keyed = byKey(totals);

  let checked = 0;
  let bad = 0;
  for (const key of [...keyed.keys()].sort()) {
    const rows = keyed.get(key);
    const [state, detail] = classify(rows, cachingModels, minInput);
    checked += 1;
    const line = `${state.padEnd(32)} ${key}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      const { caching, silent } = splitRows(rows, minInput);
      for (const repair of repairLines(floorBracket(caching, silent))) {
        console.warn(`  repair: ${repair}`);
      }
      console.warn('  note: the bracket assumes one prefix per key. A key that '
                   + 'sends a different prompt per model brackets nothing, and '
                   + 'the report cannot see inside a key.');
    } else {
      const note = handoff(state);
      if (note) {
        console.log(line);
        console.log(`  ${note}`);
      } else if (showAll) {
        console.log(line);
      }
    }
  }

  console.log(`${checked} key(s) checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture is one key running four models on one prompt: Opus 5 at 512 and Sonnet 5 at 1,024 both caching, Haiku 3.5 at 2,048 and Haiku 4.5 at 4,096 both silent. The assertion is a range, 1,024 to 2,048, which is a measurement of something the API never returns. Around it sit the cases that must not produce a range: a low-floor model silent while a high-floor one caches, which disproves the premise outright; an unrecognised model id, which would drag the low end to zero and invent a bracket of nothing to 4,096; a single silent model, where the honest answer names two open notes rather than picking one; and a dated snapshot id, because a floor lookup that misses <code>claude-haiku-4-5-20251001</code> reports every real organization as unrecognisable.",
"test_py_file": "test_anthropic_cache_floor_bracket.py",
"test_py": '''from anthropic_cache_floor_bracket import (by_key, cache_minimum, classify,
                                           floor_bracket, handoff,
                                           models_caching_anywhere, repair_lines,
                                           series, split_rows)


def model(name, uncached=5_000_000, writes=0, reads=0):
    return {"model": name, "floor": cache_minimum(name), "uncached": uncached,
            "writes": writes, "reads": reads}


# One key, one prompt, four models. Caching works at 512 and 1,024 and stops
# dead at 2,048 and 4,096. The prefix is therefore between 1,024 and 2,048.
BRACKETED = [
    model("claude-opus-5", writes=2_000_000, reads=9_000_000),
    model("claude-sonnet-5-20260115", writes=1_500_000, reads=7_000_000),
    model("claude-haiku-3-5"),
    model("claude-haiku-4-5-20251001"),
]


def test_the_bracket_is_the_finding():
    # The note in one assertion: a size derived from a report with no request
    # count and no prompt in it, purely from where caching stops working.
    state, detail = classify(BRACKETED)
    assert state == "below-cache-minimum"
    assert "caching works up to a floor of 1024" in detail
    assert "stops at 2048" in detail
    assert "at least 1024 tokens and under 2048" in detail

    caching, silent, _ = split_rows(BRACKETED)
    assert floor_bracket(caching, silent) == (1024, 2048)
    assert handoff(state) == ""


def test_a_dated_snapshot_resolves_to_its_family_floor():
    # The ids in a usage report are dated. A floor lookup that misses them
    # reports every real organization as unrecognised.
    assert cache_minimum("claude-haiku-4-5-20251001") == 4096
    assert cache_minimum("claude-sonnet-4-5-20250929") == 1024
    assert cache_minimum("claude-opus-5") == 512
    assert cache_minimum("claude-fable-5") == 512
    # Longest prefix wins: opus-4 and opus-4-5 have different floors and the
    # shorter family must not swallow the longer one.
    assert cache_minimum("claude-opus-4-5-20251101") == 4096
    assert cache_minimum("claude-opus-4-20250514") == 1024
    assert cache_minimum("gpt-5.6") is None
    assert cache_minimum("") is None


def test_an_unknown_floor_is_never_treated_as_zero():
    # A model with no floor on the caching side would drag lo down to 0 and
    # invent a bracket of 0 to 4096, which is not a finding, it is a shrug.
    rows = [model("claude-future-9", writes=1_000_000, reads=5_000_000),
            model("claude-haiku-4-5")]
    caching, silent, skipped = split_rows(rows)
    assert [r["model"] for r in skipped] == ["claude-future-9"]
    assert caching == []
    state, _ = classify(rows)
    assert state == "single-silent-model"


def test_a_silent_model_under_a_caching_floor_is_someone_elses_note():
    # opus-5 needs 512 and is silent while haiku-4-5 needs 4,096 and caches.
    # The prompt cleared the higher bar, so size cannot be the explanation.
    rows = [model("claude-opus-5"),
            model("claude-haiku-4-5", writes=2_000_000, reads=8_000_000)]
    state, detail = classify(rows)
    assert state == "silent-model-under-a-caching-floor"
    assert "claude-opus-5 (floor 512) is silent" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)
    caching, silent, _ = split_rows(rows)
    assert floor_bracket(caching, silent) is None


def test_no_caching_at_all_is_the_never_switched_on_note():
    rows = [model("claude-opus-5"), model("claude-haiku-4-5")]
    state, detail = classify(rows)
    assert state == "no-caching-anywhere"
    assert "silent on all 2 model(s)" in detail
    assert "prompt-caching-never-used" in handoff(state)


def test_one_silent_model_is_ambiguous_and_says_so():
    # No contrast, no bracket. This is the case the note refuses to claim.
    state, detail = classify([model("claude-haiku-4-5")])
    assert state == "single-silent-model"
    assert "no second floor to bracket against" in detail
    note = handoff(state)
    assert "prompt-caching-never-used" in note and "remain open" in note


def test_a_peer_key_caching_the_same_model_clears_the_model():
    peers = {"claude-haiku-4-5"}
    state, detail = classify([model("claude-haiku-4-5")], peers)
    assert state == "peer-caches-same-model"
    assert "another key caches on the same model" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)


def test_a_thin_silent_model_is_not_evidence():
    # Silence on a model that barely ran proves nothing, and must not be the
    # hi end of a bracket.
    rows = [model("claude-opus-5", writes=1_000_000, reads=4_000_000),
            model("claude-haiku-4-5", uncached=900)]
    caching, silent, skipped = split_rows(rows)
    assert silent == [] and len(skipped) == 1
    assert classify(rows)[0] == "caches-on-every-model"


def test_the_report_is_folded_into_keys_and_models():
    buckets = [{"starting_at": "2026-08-%02dT00:00:00Z" % day,
                "results": [
                    {"api_key_id": "apikey_01Ab", "model": "claude-opus-5",
                     "uncached_input_tokens": 1_000_000,
                     "cache_read_input_tokens": 4_000_000,
                     "cache_creation": {"ephemeral_5m_input_tokens": 500_000,
                                        "ephemeral_1h_input_tokens": 0}},
                    {"api_key_id": "apikey_01Ab", "model": "claude-haiku-4-5",
                     "uncached_input_tokens": 3_000_000,
                     "cache_read_input_tokens": 0,
                     "cache_creation": {}},
                ]} for day in range(1, 6)]
    totals = series(buckets)
    assert totals[("apikey_01Ab", "claude-opus-5")]["reads"] == 20_000_000
    assert totals[("apikey_01Ab", "claude-haiku-4-5")]["writes"] == 0
    assert models_caching_anywhere(totals) == {"claude-opus-5"}

    keyed = by_key(totals)
    rows = keyed["apikey_01Ab"]
    assert [r["floor"] for r in rows] == [512, 4096]
    state, _ = classify(rows)
    assert state == "below-cache-minimum"
    assert any("4096 tokens" in line for line in repair_lines((512, 4096)))


def test_empty_and_unreadable_input_produce_no_verdict():
    assert classify([])[0] == "too-little-traffic"
    assert classify(None)[0] == "too-little-traffic"
    assert series([]) == {}
    assert series([{"results": [None, "nonsense"]}]) == {}
    assert by_key({}) == {}
    assert floor_bracket([], []) is None
    assert repair_lines(None) == []
''',
"test_js_file": "anthropic-cache-floor-bracket.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { byKey, cacheMinimum, classify, floorBracket, handoff,
         modelsCachingAnywhere, repairLines, series, splitRows }
  from './anthropic-cache-floor-bracket.mjs';

const model = (name, { uncached = 5000000, writes = 0, reads = 0 } = {}) => ({
  model: name, floor: cacheMinimum(name), uncached, writes, reads,
});

const BRACKETED = [
  model('claude-opus-5', { writes: 2000000, reads: 9000000 }),
  model('claude-sonnet-5-20260115', { writes: 1500000, reads: 7000000 }),
  model('claude-haiku-3-5'),
  model('claude-haiku-4-5-20251001'),
];

test('the bracket is the finding', () => {
  const [state, detail] = classify(BRACKETED);
  assert.equal(state, 'below-cache-minimum');
  assert.match(detail, /caching works up to a floor of 1024/);
  assert.match(detail, /stops at 2048/);
  assert.match(detail, /at least 1024 tokens and under 2048/);

  const { caching, silent } = splitRows(BRACKETED);
  assert.deepEqual(floorBracket(caching, silent), [1024, 2048]);
  assert.equal(handoff(state), '');
});

test('a dated snapshot resolves to its family floor', () => {
  assert.equal(cacheMinimum('claude-haiku-4-5-20251001'), 4096);
  assert.equal(cacheMinimum('claude-sonnet-4-5-20250929'), 1024);
  assert.equal(cacheMinimum('claude-opus-5'), 512);
  assert.equal(cacheMinimum('claude-fable-5'), 512);
  assert.equal(cacheMinimum('claude-opus-4-5-20251101'), 4096);
  assert.equal(cacheMinimum('claude-opus-4-20250514'), 1024);
  assert.equal(cacheMinimum('gpt-5.6'), null);
  assert.equal(cacheMinimum(''), null);
});

test('an unknown floor is never treated as zero', () => {
  const rows = [model('claude-future-9', { writes: 1000000, reads: 5000000 }),
                model('claude-haiku-4-5')];
  const { caching, skipped } = splitRows(rows);
  assert.deepEqual(skipped.map((r) => r.model), ['claude-future-9']);
  assert.equal(caching.length, 0);
  assert.equal(classify(rows)[0], 'single-silent-model');
});

test('a silent model under a caching floor is someone elses note', () => {
  const rows = [model('claude-opus-5'),
                model('claude-haiku-4-5', { writes: 2000000, reads: 8000000 })];
  const [state, detail] = classify(rows);
  assert.equal(state, 'silent-model-under-a-caching-floor');
  assert.match(detail, /claude-opus-5 \\(floor 512\\) is silent/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
  const { caching, silent } = splitRows(rows);
  assert.equal(floorBracket(caching, silent), null);
});

test('no caching at all is the never switched on note', () => {
  const rows = [model('claude-opus-5'), model('claude-haiku-4-5')];
  const [state, detail] = classify(rows);
  assert.equal(state, 'no-caching-anywhere');
  assert.match(detail, /silent on all 2 model\\(s\\)/);
  assert.match(handoff(state), /prompt-caching-never-used/);
});

test('one silent model is ambiguous and says so', () => {
  const [state, detail] = classify([model('claude-haiku-4-5')]);
  assert.equal(state, 'single-silent-model');
  assert.match(detail, /no second floor to bracket against/);
  assert.match(handoff(state), /prompt-caching-never-used/);
  assert.match(handoff(state), /remain open/);
});

test('a peer key caching the same model clears the model', () => {
  const peers = new Set(['claude-haiku-4-5']);
  const [state, detail] = classify([model('claude-haiku-4-5')], peers);
  assert.equal(state, 'peer-caches-same-model');
  assert.match(detail, /another key caches on the same model/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
});

test('a thin silent model is not evidence', () => {
  const rows = [model('claude-opus-5', { writes: 1000000, reads: 4000000 }),
                model('claude-haiku-4-5', { uncached: 900 })];
  const { silent, skipped } = splitRows(rows);
  assert.equal(silent.length, 0);
  assert.equal(skipped.length, 1);
  assert.equal(classify(rows)[0], 'caches-on-every-model');
});

test('the report is folded into keys and models', () => {
  const buckets = Array.from({ length: 5 }, (_, i) => ({
    starting_at: `2026-08-0${i + 1}T00:00:00Z`,
    results: [
      { api_key_id: 'apikey_01Ab', model: 'claude-opus-5',
        uncached_input_tokens: 1000000, cache_read_input_tokens: 4000000,
        cache_creation: { ephemeral_5m_input_tokens: 500000,
                          ephemeral_1h_input_tokens: 0 } },
      { api_key_id: 'apikey_01Ab', model: 'claude-haiku-4-5',
        uncached_input_tokens: 3000000, cache_read_input_tokens: 0,
        cache_creation: {} },
    ],
  }));
  const totals = series(buckets);
  assert.equal(totals.get('apikey_01Ab\\tclaude-opus-5').reads, 20000000);
  assert.equal(totals.get('apikey_01Ab\\tclaude-haiku-4-5').writes, 0);
  assert.deepEqual([...modelsCachingAnywhere(totals)], ['claude-opus-5']);

  const rows = byKey(totals).get('apikey_01Ab');
  assert.deepEqual(rows.map((r) => r.floor), [512, 4096]);
  assert.equal(classify(rows)[0], 'below-cache-minimum');
  assert.ok(repairLines([512, 4096]).some((l) => l.includes('4096 tokens')));
});

test('empty and unreadable input produce no verdict', () => {
  assert.equal(classify([])[0], 'too-little-traffic');
  assert.equal(classify(null)[0], 'too-little-traffic');
  assert.equal(series([]).size, 0);
  assert.equal(series([{ results: [null, 'nonsense'] }]).size, 0);
  assert.equal(byKey(new Map()).size, 0);
  assert.equal(floorBracket([], []), null);
  assert.deepEqual(repairLines(null), []);
});
''',
"faq": [
 ("How is this different from prompt caching never being used?",
  "That note reads organization-wide totals and answers a yes-or-no question: is there any cache activity anywhere. When the answer is no, the repair is to add a cache_control breakpoint. This note starts where there is cache activity and it is uneven, and asks why it stops on some models and not others. The two produce the same pair of zeros on the silent model, which is exactly why the contrast between models on one key is the only thing that separates them. With one model and no contrast, this script refuses the verdict and names both notes as still open."),
 ("Why not just count the prefix with the token counter?",
  "Because that is a POST, and every script in this section is read-only. Anthropic's count_tokens endpoint generates nothing and bills nothing, so it is a perfectly reasonable thing for you to run by hand against a copy of your prompt, and it will give you the exact number this check can only bracket. What it will not tell you is which of your production routes are affected, which key they run on, or how much uncached input they have already burned. The bracket comes from traffic that actually happened."),
 ("The minimums are in a table. What happens when they change?",
  "The table goes stale, so an unrecognised model id is skipped rather than guessed at. It cannot be the low end of a bracket, where an assumed floor of zero would invent a range out of nothing, and it cannot be the high end either. The failure mode of a stale table is therefore a check that declines to judge a new model, not one that prints a confident token range that happens to be wrong. When a model you use is missing, add it and the contrast comes back."),
 ("Could a multi-tenant key produce a false bracket?",
  "Yes, and the output says so. The bracket assumes one prefix per key: the whole argument is that the same prompt met two different floors. A key that deliberately sends a short prompt to a cheap model and a long one to an expensive one satisfies the arithmetic and means nothing by it. Group by key and model, treat the finding as strong on a key with one workload, and check the request builder before acting."),
 ("Should I pad the prompt to clear the floor?",
  "Only with material you would want cached anyway. Padding is billed at the full input rate on the write and at 1.25x on top of that for a five-minute entry, so filler pays back only at very high repeat volume and often not at all. The honest choices are to move real stable content forward &mdash; tool schemas, few-shot examples, retrieval instructions &mdash; or to accept that this route cannot be cached on this model and stop budgeting for a discount that will never arrive."),
],
"related": [REL_CACHE_NEVER, REL_CHURN, REL_STEP],
"citations": [CITE_CL_CACHING, CITE_CL_USAGE_REPORT, CITE_CL_MODELS, CITE_CL_PRICING],
},
{
"slug": "prompt-cache-key-not-set",
"title": "Cache hits fall away exactly when the fleet scales out",
"description": "Without prompt_cache_key, identical prompts scatter across backends. The signature is a cached share negatively correlated with the hour's request rate.",
"h1": "Cache hits fall away exactly when the fleet scales out",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["prompt_cache_key openai", "cached_tokens erratic same prompt",
             "cache hit rate drops under load",
             "openai prompt caching routing", "input_cached_tokens peak hours"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key (sk-admin-...) with the read scopes. A project key cannot read /v1/organization/.",
"lead": "The cached share was fine in staging and fine in the first week of the rollout. Then autoscaling started doing its job, and the discount went the wrong way. At three in the morning the prompt caches at seventy per cent; at two in the afternoon, on the same template, the same model and the same code, it caches at sixteen. Everybody's first instinct is that something about the busy path is different. Nothing about the busy path is different. There are simply more machines in it, and none of them has seen this prefix before.",
"short_answer": """<p>With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={T-7d}&amp;bucket_width=1h&amp;limit=168&amp;group_by[]=project_id&amp;group_by[]=model</code>. Per hour, <code>input_cached_tokens / input_tokens</code> against <code>num_model_requests</code>.</p>
<p>Then correlate the two. A <strong>rank correlation at or below about -0.4</strong>, with the quiet third of hours caching well and the busy third caching at well under half that, is routing scatter. Prefix instability does not produce a slope; it produces a flat low line at every load.</p>
<p>Drop the hours that follow a gap in traffic before correlating. Those start cold no matter how the requests were routed, and if the batch that opens a burst is also its busiest hour &mdash; which is normal &mdash; leaving them in manufactures precisely the negative correlation you are testing for. Those hours belong to <a href="/llm/prompt-cache-retention-left-at-default/">the retention note</a>.</p>
<p>The repair is one parameter: <code>prompt_cache_key</code>, set to something coarse and stable per template. It influences routing. It does not pin a request to a machine and does not guarantee a hit.</p>""",
"problem": """<p>OpenAI's prompt caching is automatic, which is usually described as a convenience and is occasionally a problem: there is no flag to switch on, so there is no flag whose absence explains a miss. Lookup is prefix-based, and it is also routing-sensitive. A cached prefix lives on the machine that served the request that created it. Send the next identical request to a different backend and it is a first call again, at full price, and nothing tells you that is what happened.</p>
<p>The consequence is genuinely counter-intuitive, which is why it survives so long. Every other cache in your stack gets more effective as traffic rises, because volume is what keeps entries warm. This one gets less effective, because volume is what spreads the traffic over more caches. A team scaling a service horizontally watches its per-request cost climb and reaches for the explanations that usually fit &mdash; a longer prompt, more retrieved context, a model change &mdash; and none of them fit, because the prompt is byte-identical and always was.</p>""",
"why": """<p><strong>The slope is the finding, not the level.</strong> Three published notes and one sibling all read a cached share, so a low share is not evidence of anything by itself. What no other note here computes is the relationship between that share and the hour's request count. A rank correlation is used rather than a straight one because request counts are heavy tailed: one incident hour at ten times normal volume would otherwise decide the answer on its own.</p>
<p><strong>Post-gap hours are excluded, and that exclusion is the whole boundary with the retention note.</strong> An hour that resumes traffic after idle time starts from an evicted cache regardless of routing, so it can say nothing about routing. Worse, scheduled work usually opens at full tilt, which makes the coldest hour also the busiest one and forges a strong negative correlation out of an eviction problem. The script computes the correlation over linked hours only, reports how many hours it threw away, and names the note those hours belong to.</p>
<p><strong>Two degenerate cases get two different answers on purpose.</strong> A request rate that never varies returns no correlation at all, because nothing can be said about concurrency from a flat load. A cached share that never varies returns exactly zero, because "no relationship" is itself a finding and it is the one that points at a prefix changing between calls. Collapsing those two into one number would hide the difference between "cannot tell" and "definitely not this".</p>
<p><strong>A share that <em>rises</em> with load is reported and is not a fault.</strong> Density keeps entries warm, so on a well-keyed fleet the busy hours should cache better than the quiet ones. Seeing that is the confirmation that the prefix is stable and the routing hint is doing its job, and the script prints it rather than staying silent, because a check that only ever speaks up when it is unhappy teaches you nothing about the healthy shape.</p>
<p><strong>The quiet hours have to actually cache before any of this means anything.</strong> The finding requires a quiet-third share above a floor. If the prompt caches badly even at four in the morning with two workers running, the problem is not where the requests landed, and no routing hint will fix it. That branch is handed to the prefix note and to the eligibility check on the mean input size.</p>""",
"steps": [
 {"h": "Pull a week of hourly buckets with the request count",
  "body": """<p><code>bucket_width=1h</code> with <code>group_by[]=project_id</code> and <code>group_by[]=model</code>. <code>num_model_requests</code> is the field that makes this note possible and it is the one Anthropic's equivalent report does not have, which is why this check is an OpenAI check.</p>"""},
 {"h": "Drop every hour that follows a gap",
  "body": """<p>Keep only hours whose preceding hour also carried traffic. This is not tidying: post-gap hours run cold for a reason that has nothing to do with concurrency, and they cluster at the start of scheduled work, which is exactly when load spikes.</p>"""},
 {"h": "Pool the share, do not average it",
  "body": """<p>Cached tokens over input tokens across the set, not the mean of the per-hour ratios. An hour with nine requests must not outvote an hour with nine thousand, and the whole quantity under test is what happens in the big hours.</p>"""},
 {"h": "Rank-correlate the share against the request rate",
  "body": """<p>Spearman across the linked hours. At or below about -0.4, with the quiet third caching above a floor and the busy third at under sixty per cent of it, the share is degrading with load. Report both the correlation and the two shares: the number that persuades anyone is "seventy per cent at night, sixteen at noon".</p>"""},
 {"h": "Set a coarse cache key and re-measure the busy end",
  "body": """<p><code>prompt_cache_key="rag-answer-v3"</code>, or the template name plus a tenant. Coarse enough that traffic concentrates; a per-request id scatters the fleet as thoroughly as no key at all. It is a routing hint, not content, so keep it out of the prompt. What moves first afterwards is the gap between the quiet and busy shares, not the average.</p>"""},
],
"verify": """<p>Re-run over the same seven days after the key ships. The quiet share should barely move and the busy share should climb toward it; the correlation is the number to watch, because it goes to roughly zero long before the average looks impressive.</p>
<pre><code class="language-bash">python3 openai_cache_key_routing_scatter.py --days 7
# load-correlated-misses   proj_abc123 / gpt-5.6  cached share 68% in the quietest hours (187 req/h) and 16% in the busiest (3405 req/h), rank correlation -1.00 against request rate. The prefix is cacheable; the requests are not landing where it is cached.
#   21 hour(s) that follow a gap in traffic were excluded before correlating
#   repair: set prompt_cache_key on the route
#   repair: make it coarse. The template name, or the template plus tenant
# 5 project/model series checked, 1 finding(s)</code></pre>""",
"code_intro": "One paginated GET and no writes. Ten pure functions, and the two that carry the note are the exclusion and the correlation. <code>continuation_rows</code> keeps only hours whose predecessor also had traffic, which is what stops an eviction problem being read as a routing one; <code>resumption_rows</code> is its complement, kept so the count of discarded hours can be printed rather than quietly vanishing. <code>spearman</code> ranks with ties shared and returns two different degenerate answers on purpose: nothing at all when the load is flat, and exactly zero when the share is. <code>load_split</code> turns the slope into the pair of numbers anyone will actually quote.",
"py_file": "openai_cache_key_routing_scatter.py",
"py": '''"""Find OpenAI traffic whose cached share falls as concurrency rises.

Read only. One paginated GET against the Usage API, which needs an admin key
(sk-admin-...); a project key is rejected by every /v1/organization/ path, and
an admin key can be provisioned with the read scopes only.

Cache lookup is prefix-based and routing-sensitive. Without prompt_cache_key a
fleet sprays byte-identical prompts across many backends and each one sees a
cold prefix, so the hit rate gets *worse* as you scale out. That is the whole
signature: a cached share that is negatively correlated with the hour's request
count. A prefix that is simply unstable produces a flat low share at every load
and belongs to a different note.

Hours that follow a gap in traffic are dropped before anything is correlated.
Those hours run cold because the entry was evicted while nobody was calling,
which is a third note again, and leaving them in would manufacture exactly the
negative correlation this one is looking for.

The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_cache_key_routing_scatter")

API = "https://api.openai.com/v1"

FINDINGS = ("load-correlated-misses",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def hour_index(stamp):
    """Hours since the epoch. Pure. None if unreadable.

    The usage buckets carry start_time as a unix integer, but the same code has
    to survive an ISO string, and adjacency has to be integer arithmetic: gap
    detection on formatted timestamps gets 23:00 and 00:00 wrong every night.
    """
    if isinstance(stamp, bool) or stamp is None:
        return None
    if isinstance(stamp, (int, float)):
        return int(stamp) // 3600
    text = str(stamp).strip().replace(" ", "T")
    if len(text) < 13:
        return None
    head = text[:13]
    if head[4] != "-" or head[7] != "-" or head[10] != "T":
        return None
    for part in (head[0:4], head[5:7], head[8:10], head[11:13]):
        if not part.isdigit():
            return None
    try:
        when = dt.datetime(int(head[0:4]), int(head[5:7]), int(head[8:10]),
                           int(head[11:13]), tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return int(when.timestamp()) // 3600


def hour_label(index):
    """Render an hour index back as a UTC stamp. Pure."""
    if index is None:
        return "unknown"
    when = dt.datetime.fromtimestamp(int(index) * 3600, dt.timezone.utc)
    return when.strftime("%Y-%m-%dT%H:00Z")


def rows_by_series(buckets):
    """Per (project_id, model), one row per active hour, sorted. Pure."""
    merged = {}
    for bucket in buckets or []:
        index = hour_index(bucket.get("start_time"))
        if index is None:
            continue
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            ident = (str(result.get("project_id") or "unknown"),
                     str(result.get("model") or "unknown"))
            row = merged.setdefault((ident, index),
                                    {"index": index, "hour": hour_label(index),
                                     "requests": 0, "input": 0, "cached": 0})
            row["requests"] += _int(result.get("num_model_requests"))
            row["input"] += _int(result.get("input_tokens"))
            row["cached"] += _int(result.get("input_cached_tokens"))
    out = {}
    for (ident, _index), row in merged.items():
        if row["requests"] > 0 or row["input"] > 0:
            out.setdefault(ident, []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: r["index"])
    return out


def cached_share(rows):
    """Pooled cached share over a set of hours. Pure. None when nothing ran.

    Pooled rather than averaged: an hour with nine requests must not carry the
    same weight as an hour with nine thousand, which is the entire quantity
    under test here.
    """
    total = sum(_int(r.get("input")) for r in rows or [])
    if total <= 0:
        return None
    return sum(_int(r.get("cached")) for r in rows or []) / float(total)


def continuation_rows(rows):
    """Hours whose previous hour also carried traffic. Pure.

    The exclusion that keeps this note off someone else's ground. An hour that
    follows idle time starts from an evicted cache no matter how the requests
    were routed, so it cannot be evidence about routing.
    """
    active = {_int(r.get("index")) for r in rows or []}
    return [r for r in rows or [] if _int(r.get("index")) - 1 in active]


def resumption_rows(rows):
    """The hours the correlation deliberately threw away. Pure."""
    active = {_int(r.get("index")) for r in rows or []}
    return [r for r in rows or [] if _int(r.get("index")) - 1 not in active]


def _ranks(values):
    """Average ranks, ties shared. Pure."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def spearman(xs, ys):
    """Rank correlation between two equal-length series. Pure. None if flat.

    Rank rather than Pearson because request counts are heavy tailed and one
    incident hour would otherwise decide the answer.

    The two degenerate cases are deliberately different answers. A load that
    never varies returns None, because nothing at all can be said about
    concurrency from a flat request rate. A share that never varies returns
    0.0, because "no relationship" is a real finding here and it is the one
    that sends the reader to the prefix-instability note.
    """
    xs = list(xs or [])
    ys = list(ys or [])
    if len(xs) != len(ys) or len(xs) < 8:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    n = float(len(xs))
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx <= 0:
        return None
    if syy <= 0:
        return 0.0
    return sxy / ((sxx ** 0.5) * (syy ** 0.5))


def load_split(rows, fraction=0.33):
    """Pooled cached share in the quietest and busiest hours. Pure.

    Returns (quiet_share, busy_share, quiet_rate, busy_rate) or Nones. The
    correlation says the relationship is monotone; this says how big it is in
    the only units anyone will act on, which is the discount you are not getting
    at peak.
    """
    active = [r for r in rows or [] if _int(r.get("requests")) > 0]
    if len(active) < 6:
        return (None, None, None, None)
    ordered = sorted(active, key=lambda r: _int(r.get("requests")))
    size = max(2, int(len(ordered) * fraction))
    quiet, busy = ordered[:size], ordered[-size:]

    def rate(part):
        return sum(_int(r.get("requests")) for r in part) / float(len(part))

    return (cached_share(quiet), cached_share(busy), rate(quiet), rate(busy))


def handoff(state):
    """Which note owns this shape, when it is not this one. Pure."""
    if state == "no-cached-tokens":
        return ("not one cached token at any load, so the traffic never becomes "
                "eligible rather than being routed away from its cache. Read the "
                "prompt-below-model-cache-minimum note and check the mean input "
                "per request against the model's floor first.")
    if state == "flat-low-share":
        return ("the share is low and stays low whatever the load, which is a "
                "prefix that differs between calls rather than requests landing "
                "on different machines. Read the "
                "cache-invalidated-by-changing-prefix note.")
    if state == "cold-only-after-idle":
        return ("the cold hours are the ones that follow gaps in traffic, and "
                "the busy hours are fine. That is eviction during idle time: "
                "read the prompt-cache-retention-left-at-default note.")
    return ""


def classify(rows, rho_floor=-0.4, ratio_floor=0.6, quiet_floor=0.15,
             min_hours=24):
    """Classify one project and model series. Pure. Returns (state, detail).

    Only a series whose cached share falls monotonically as the hour gets busier
    belongs to this note, and only after the post-gap hours have been removed.
    """
    rows = rows or []
    linked = continuation_rows(rows)
    if len(linked) < min_hours:
        return ("too-few-linked-hours",
                "%d hour(s) with traffic in the hour before them, under the "
                "floor of %d. Correlating against load needs a run of busy "
                "hours." % (len(linked), min_hours))

    overall = cached_share(linked)
    if overall is not None and overall <= 0.0:
        return ("no-cached-tokens",
                "%d input token(s) across %d linked hour(s) and not one cached"
                % (sum(_int(r.get("input")) for r in linked), len(linked)))

    quiet, busy, quiet_rate, busy_rate = load_split(linked)
    rho = spearman([_int(r.get("requests")) for r in linked],
                   [cached_share([r]) or 0.0 for r in linked])

    if rho is None or quiet is None or busy is None:
        return ("load-does-not-vary",
                "the request rate barely moves across the window, so nothing "
                "here can be attributed to concurrency")

    if rho <= rho_floor and quiet >= quiet_floor and busy <= quiet * ratio_floor:
        return ("load-correlated-misses",
                "cached share %.0f%% in the quietest hours (%.0f req/h) and "
                "%.0f%% in the busiest (%.0f req/h), rank correlation %.2f "
                "against request rate. The prefix is cacheable; the requests "
                "are not landing where it is cached."
                % (quiet * 100, quiet_rate, busy * 100, busy_rate, rho))

    if rho >= -rho_floor:
        return ("share-rises-with-load",
                "cached share climbs with the request rate (%.2f): density is "
                "keeping entries warm, which is the opposite of scatter" % rho)

    cold = resumption_rows(rows)
    cold_share = cached_share(cold)
    if (overall is not None and cold_share is not None and cold_share <= 0.02
            and overall >= quiet_floor and len(cold) >= 3):
        return ("cold-only-after-idle",
                "%.0f%% cached in linked hours against %.0f%% in the %d hour(s) "
                "that follow a gap" % (overall * 100, cold_share * 100, len(cold)))

    if overall is not None and overall < quiet_floor:
        return ("flat-low-share",
                "cached share %.0f%% overall with rank correlation %.2f against "
                "load: low everywhere rather than low under load"
                % (overall * 100, rho))

    return ("healthy",
            "cached share %.0f%% quiet and %.0f%% busy, correlation %.2f"
            % (quiet * 100, busy * 100, rho))


def repair_lines():
    """The routing hint, and what makes a good one. Pure."""
    return [
        "set prompt_cache_key on the route: "
        "client.responses.create(..., prompt_cache_key=\\"rag-answer-v3\\").",
        "make it coarse. The template name, or the template plus tenant, so "
        "traffic concentrates on a few caches. A per-request id scatters the "
        "fleet exactly as badly as no key at all.",
        "keep it out of the prompt. It is a routing hint, not content, and it "
        "does not pin a request to a machine or guarantee a hit.",
        "then re-read these same hourly buckets. What should move first is the "
        "busy end: the gap between the quiet and busy shares closes before the "
        "average does.",
    ]


def window_start(days):
    """Floor to the hour so start_time lands on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    return int((now - dt.timedelta(days=days)).timestamp())


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/ needs an admin key "
                         "(sk-admin-...), not a project key" % r.status_code)
    r.raise_for_status()
    return r.json()


def read_buckets(session, path, params):
    """Walk the paginated usage endpoint."""
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
    ap.add_argument("--days", type=int, default=7,
                    help="days of hourly buckets to read (max 30)")
    ap.add_argument("--rho-floor", type=float, default=-0.4,
                    help="rank correlation at or below which the share is "
                         "treated as load-correlated")
    ap.add_argument("--show-all", action="store_true",
                    help="also print series that are behaving")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key "
                  "(sk-admin-...); a project key cannot read /v1/organization/")
        return 2

    days = max(2, min(int(args.days), 30))
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    buckets = read_buckets(session, "/organization/usage/completions", {
        "start_time": window_start(days),
        "bucket_width": "1h",
        "limit": 168,
        "group_by[]": ["project_id", "model"],
    })

    series = rows_by_series(buckets)
    if not series:
        log.info("no completions usage in the last %d day(s)", days)
        return 0

    checked = 0
    bad = 0
    for ident in sorted(series):
        rows = series[ident]
        state, detail = classify(rows, args.rho_floor)
        checked += 1
        line = "%-24s %s / %s  %s" % (state, ident[0], ident[1], detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            log.warning("  %d hour(s) that follow a gap in traffic were excluded "
                        "before correlating; those run cold for a different "
                        "reason.", len(resumption_rows(rows)))
            for repair in repair_lines():
                log.warning("  repair: %s", repair)
        else:
            note = handoff(state)
            if note:
                log.info(line)
                log.info("  %s", note)
            elif args.show_all:
                log.info(line)

    log.info("%d project/model series checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-cache-key-routing-scatter.mjs",
"js": '''/**
 * Find OpenAI traffic whose cached share falls as concurrency rises.
 *
 * Read only. One paginated GET against the Usage API, which needs an admin key
 * (sk-admin-...). A project key is rejected by /v1/organization/.
 *
 * Cache lookup is prefix-based and routing-sensitive. Without prompt_cache_key
 * a fleet sprays byte-identical prompts across many backends and each one sees
 * a cold prefix, so the hit rate gets worse as you scale out. The signature is
 * a cached share negatively correlated with the hour's request count. A prefix
 * that is simply unstable gives a flat low share at every load, which is a
 * different note.
 *
 * Hours that follow a gap in traffic are dropped before anything is
 * correlated: they run cold because the entry was evicted while nobody was
 * calling, and leaving them in manufactures the very correlation being tested.
 */
const API = 'https://api.openai.com/v1';

const FINDINGS = new Set(['load-correlated-misses']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Hours since the epoch. Pure. Null if unreadable.
 * The buckets carry start_time as a unix integer, but the same code has to
 * survive an ISO string, and gap detection has to be integer arithmetic:
 * comparing formatted stamps gets 23:00 and 00:00 wrong every night.
 */
export function hourIndex(stamp) {
  if (typeof stamp === 'boolean' || stamp === null || stamp === undefined) return null;
  if (typeof stamp === 'number' && Number.isFinite(stamp)) {
    return Math.floor(Math.trunc(stamp) / 3600);
  }
  const text = String(stamp).trim().replace(' ', 'T');
  if (text.length < 13) return null;
  const head = text.slice(0, 13);
  if (!/^\\d{4}-\\d{2}-\\d{2}T\\d{2}$/.test(head)) return null;
  const when = Date.parse(`${head}:00:00Z`);
  if (Number.isNaN(when)) return null;
  return Math.floor(when / 3600000);
}

/** Render an hour index back as a UTC stamp. Pure. */
export function hourLabel(index) {
  if (index === null || index === undefined) return 'unknown';
  return `${new Date(Math.trunc(index) * 3600000).toISOString().slice(0, 13)}:00Z`;
}

/** Per project_id and model, one row per active hour, sorted. Pure. */
export function rowsBySeries(buckets) {
  const merged = new Map();
  for (const bucket of buckets ?? []) {
    const index = hourIndex(bucket?.start_time);
    if (index === null) continue;
    for (const result of bucket?.results ?? []) {
      if (!result || typeof result !== 'object') continue;
      const ident = `${result.project_id ?? 'unknown'}\\t${result.model ?? 'unknown'}`;
      const cell = `${ident}\\t${index}`;
      if (!merged.has(cell)) {
        merged.set(cell, { ident, index, hour: hourLabel(index),
                           requests: 0, input: 0, cached: 0 });
      }
      const row = merged.get(cell);
      row.requests += readInt(result.num_model_requests);
      row.input += readInt(result.input_tokens);
      row.cached += readInt(result.input_cached_tokens);
    }
  }
  const out = new Map();
  for (const row of merged.values()) {
    if (row.requests <= 0 && row.input <= 0) continue;
    if (!out.has(row.ident)) out.set(row.ident, []);
    out.get(row.ident).push(row);
  }
  for (const rows of out.values()) rows.sort((a, b) => a.index - b.index);
  return out;
}

/**
 * Pooled cached share over a set of hours. Pure. Null when nothing ran.
 * Pooled rather than averaged: an hour with nine requests must not carry the
 * same weight as an hour with nine thousand.
 */
export function cachedShare(rows) {
  let input = 0;
  let cached = 0;
  for (const row of rows ?? []) {
    input += readInt(row?.input);
    cached += readInt(row?.cached);
  }
  if (input <= 0) return null;
  return cached / input;
}

/**
 * Hours whose previous hour also carried traffic. Pure.
 * The exclusion that keeps this note off someone else's ground.
 */
export function continuationRows(rows) {
  const active = new Set((rows ?? []).map((r) => readInt(r?.index)));
  return (rows ?? []).filter((r) => active.has(readInt(r?.index) - 1));
}

/** The hours the correlation deliberately threw away. Pure. */
export function resumptionRows(rows) {
  const active = new Set((rows ?? []).map((r) => readInt(r?.index)));
  return (rows ?? []).filter((r) => !active.has(readInt(r?.index) - 1));
}

/** Average ranks, ties shared. Pure. */
function ranks(values) {
  const order = values.map((_v, i) => i).sort((a, b) => values[a] - values[b]);
  const out = new Array(values.length).fill(0);
  let i = 0;
  while (i < order.length) {
    let j = i;
    while (j + 1 < order.length && values[order[j + 1]] === values[order[i]]) j += 1;
    const shared = (i + j) / 2 + 1;
    for (let k = i; k <= j; k += 1) out[order[k]] = shared;
    i = j + 1;
  }
  return out;
}

/**
 * Rank correlation between two equal-length series. Pure. Null if flat.
 *
 * Rank rather than Pearson because request counts are heavy tailed and one
 * incident hour would otherwise decide the answer. The two degenerate cases
 * are deliberately different answers: a load that never varies returns null,
 * because nothing can be said about concurrency from a flat request rate,
 * while a share that never varies returns 0, because "no relationship" is a
 * real finding and it is the one that points at prefix instability.
 */
export function spearman(xs, ys) {
  const a = [...(xs ?? [])];
  const b = [...(ys ?? [])];
  if (a.length !== b.length || a.length < 8) return null;
  const rx = ranks(a);
  const ry = ranks(b);
  const n = a.length;
  const mx = rx.reduce((s, v) => s + v, 0) / n;
  const my = ry.reduce((s, v) => s + v, 0) / n;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (let i = 0; i < n; i += 1) {
    sxy += (rx[i] - mx) * (ry[i] - my);
    sxx += (rx[i] - mx) ** 2;
    syy += (ry[i] - my) ** 2;
  }
  if (sxx <= 0) return null;
  if (syy <= 0) return 0;
  return sxy / (Math.sqrt(sxx) * Math.sqrt(syy));
}

/**
 * Pooled cached share in the quietest and busiest hours. Pure.
 * Returns [quietShare, busyShare, quietRate, busyRate], or nulls.
 */
export function loadSplit(rows, fraction = 0.33) {
  const active = (rows ?? []).filter((r) => readInt(r?.requests) > 0);
  if (active.length < 6) return [null, null, null, null];
  const ordered = [...active].sort((a, b) => readInt(a?.requests) - readInt(b?.requests));
  const size = Math.max(2, Math.trunc(ordered.length * fraction));
  const quiet = ordered.slice(0, size);
  const busy = ordered.slice(-size);
  const rate = (part) => part.reduce((s, r) => s + readInt(r?.requests), 0) / part.length;
  return [cachedShare(quiet), cachedShare(busy), rate(quiet), rate(busy)];
}

/** Which note owns this shape, when it is not this one. Pure. */
export function handoff(state) {
  if (state === 'no-cached-tokens') {
    return 'not one cached token at any load, so the traffic never becomes '
      + 'eligible rather than being routed away from its cache. Read the '
      + "prompt-below-model-cache-minimum note and check the mean input per "
      + "request against the model's floor first.";
  }
  if (state === 'flat-low-share') {
    return 'the share is low and stays low whatever the load, which is a prefix '
      + 'that differs between calls rather than requests landing on different '
      + 'machines. Read the cache-invalidated-by-changing-prefix note.';
  }
  if (state === 'cold-only-after-idle') {
    return 'the cold hours are the ones that follow gaps in traffic, and the '
      + 'busy hours are fine. That is eviction during idle time: read the '
      + 'prompt-cache-retention-left-at-default note.';
  }
  return '';
}

/** Classify one project and model series. Pure. Returns [state, detail]. */
export function classify(rows, rhoFloor = -0.4, ratioFloor = 0.6,
                         quietFloor = 0.15, minHours = 24) {
  const all = rows ?? [];
  const linked = continuationRows(all);
  if (linked.length < minHours) {
    return ['too-few-linked-hours',
      `${linked.length} hour(s) with traffic in the hour before them, under the `
      + `floor of ${minHours}. Correlating against load needs a run of busy hours.`];
  }

  const overall = cachedShare(linked);
  if (overall !== null && overall <= 0) {
    const input = linked.reduce((s, r) => s + readInt(r?.input), 0);
    return ['no-cached-tokens',
      `${input} input token(s) across ${linked.length} linked hour(s) and not one cached`];
  }

  const [quiet, busy, quietRate, busyRate] = loadSplit(linked);
  const rho = spearman(linked.map((r) => readInt(r?.requests)),
                       linked.map((r) => cachedShare([r]) ?? 0));

  if (rho === null || quiet === null || busy === null) {
    return ['load-does-not-vary',
      'the request rate barely moves across the window, so nothing here can be '
      + 'attributed to concurrency'];
  }

  if (rho <= rhoFloor && quiet >= quietFloor && busy <= quiet * ratioFloor) {
    return ['load-correlated-misses',
      `cached share ${(quiet * 100).toFixed(0)}% in the quietest hours `
      + `(${quietRate.toFixed(0)} req/h) and ${(busy * 100).toFixed(0)}% in the `
      + `busiest (${busyRate.toFixed(0)} req/h), rank correlation `
      + `${rho.toFixed(2)} against request rate. The prefix is cacheable; the `
      + 'requests are not landing where it is cached.'];
  }

  if (rho >= -rhoFloor) {
    return ['share-rises-with-load',
      `cached share climbs with the request rate (${rho.toFixed(2)}): density is `
      + 'keeping entries warm, which is the opposite of scatter'];
  }

  const cold = resumptionRows(all);
  const coldShare = cachedShare(cold);
  if (overall !== null && coldShare !== null && coldShare <= 0.02
      && overall >= quietFloor && cold.length >= 3) {
    return ['cold-only-after-idle',
      `${(overall * 100).toFixed(0)}% cached in linked hours against `
      + `${(coldShare * 100).toFixed(0)}% in the ${cold.length} hour(s) that follow a gap`];
  }

  if (overall !== null && overall < quietFloor) {
    return ['flat-low-share',
      `cached share ${(overall * 100).toFixed(0)}% overall with rank correlation `
      + `${rho.toFixed(2)} against load: low everywhere rather than low under load`];
  }

  return ['healthy',
    `cached share ${(quiet * 100).toFixed(0)}% quiet and ${(busy * 100).toFixed(0)}% `
    + `busy, correlation ${rho.toFixed(2)}`];
}

/** The routing hint, and what makes a good one. Pure. */
export function repairLines() {
  return [
    'set prompt_cache_key on the route: '
    + 'client.responses.create(..., prompt_cache_key="rag-answer-v3").',
    'make it coarse. The template name, or the template plus tenant, so traffic '
    + 'concentrates on a few caches. A per-request id scatters the fleet exactly '
    + 'as badly as no key at all.',
    'keep it out of the prompt. It is a routing hint, not content, and it does '
    + 'not pin a request to a machine or guarantee a hit.',
    'then re-read these same hourly buckets. What should move first is the busy '
    + 'end: the gap between the quiet and busy shares closes before the average does.',
  ];
}

function windowStart(days) {
  const now = new Date();
  now.setUTCMinutes(0, 0, 0);
  return Math.floor((now.getTime() - days * 86400000) / 1000);
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/ needs an admin `
                    + 'key (sk-admin-...), not a project key');
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
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key '
                  + '(sk-admin-...); a project key cannot read /v1/organization/');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(2, Math.min(Number(process.env.DAYS ?? 7), 30));
  const rhoFloor = Number(process.env.RHO_FLOOR ?? -0.4);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organization/usage/completions', {
    start_time: windowStart(days),
    bucket_width: '1h',
    limit: 168,
    'group_by[]': ['project_id', 'model'],
  })) buckets.push(bucket);

  const series = rowsBySeries(buckets);
  if (series.size === 0) {
    console.log(`no completions usage in the last ${days} day(s)`);
    return;
  }

  let checked = 0;
  let bad = 0;
  for (const ident of [...series.keys()].sort()) {
    const rows = series.get(ident);
    const [state, detail] = classify(rows, rhoFloor);
    checked += 1;
    const line = `${state.padEnd(24)} ${ident.replace('\\t', ' / ')}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      console.warn(`  ${resumptionRows(rows).length} hour(s) that follow a gap in `
                   + 'traffic were excluded before correlating; those run cold '
                   + 'for a different reason.');
      for (const repair of repairLines()) console.warn(`  repair: ${repair}`);
    } else {
      const note = handoff(state);
      if (note) {
        console.log(line);
        console.log(`  ${note}`);
      } else if (showAll) {
        console.log(line);
      }
    }
  }

  console.log(`${checked} project/model series checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three fixtures share one traffic profile &mdash; a week of a normal daily load curve, quiet overnight and a broad afternoon peak &mdash; and differ only in how the cached share responds to it. One falls with load, one ignores it, one rises with it, and the three land on three different verdicts from byte-identical request counts. The fourth fixture is the trap: bursts that open at full tilt after a five-hour gap, where the busiest hour of every burst is also the coldest. Correlate that raw and it reads as a textbook scatter signature at -0.87. Drop the post-gap hours first and the linked hours are uniformly warm, and the script hands it to the retention note by name.",
"test_py_file": "test_openai_cache_key_routing_scatter.py",
"test_py": '''from openai_cache_key_routing_scatter import (cached_share, classify,
                                              continuation_rows, handoff,
                                              hour_index, hour_label,
                                              load_split, resumption_rows,
                                              rows_by_series, spearman)

BASE = hour_index("2026-08-17T00:00Z")

# A daily traffic shape: quiet overnight, a broad afternoon peak.
LOAD = [200, 150, 120, 100, 120, 200, 400, 900, 1800, 3000, 3600, 3800,
        3900, 3800, 3600, 3000, 2400, 1800, 1200, 800, 600, 450, 350, 260]


def hour(offset, requests, share):
    tokens = requests * 2000
    return {"index": BASE + offset, "hour": hour_label(BASE + offset),
            "requests": requests, "input": tokens,
            "cached": int(round(tokens * share))}


def contiguous(share_of_load):
    """Seven contiguous days on the daily load shape, no gaps anywhere."""
    return [hour(i, LOAD[i % 24], share_of_load(LOAD[i % 24])) for i in range(168)]


# The note. The prefix is provably cacheable, because the quiet hours cache
# beautifully; the share falls away as the fleet fans out.
SCATTER = contiguous(lambda load: 0.72 - 0.00016 * load)
# Identical traffic, a share that ignores the load entirely. Prefix instability.
FLAT = contiguous(lambda _load: 0.10)
# Identical traffic, a share that improves with density. Not a fault.
RISING = contiguous(lambda load: 0.10 + 0.00016 * load)


def bursty():
    """Three-hour bursts five hours apart, each opening at full tilt.

    The busiest hour of every burst is also the coldest one, because it is the
    hour that follows the idle stretch. That is the trap: correlate the raw
    series and the load looks guilty.
    """
    shape = [(3000, 0.0), (1000, 0.7), (400, 0.7)]
    rows = []
    for burst in range(21):
        for step, (requests, share) in enumerate(shape):
            rows.append(hour(burst * 8 + step, requests, share))
    return rows


BURSTY = bursty()


def test_the_cached_share_falling_with_load_is_the_finding():
    # The note in one assertion: same prefix, same code, and the discount
    # evaporates exactly when the fleet is widest.
    quiet, busy, quiet_rate, busy_rate = load_split(SCATTER)
    assert round(quiet, 2) == 0.69 and round(busy, 2) == 0.16
    assert quiet_rate < 300 and busy_rate > 3400

    rho = spearman([r["requests"] for r in SCATTER],
                   [cached_share([r]) for r in SCATTER])
    assert round(rho, 3) == -1.0

    state, detail = classify(SCATTER)
    assert state == "load-correlated-misses"
    assert "68% in the quietest hours" in detail
    assert "16% in the busiest" in detail
    assert "rank correlation -1.00" in detail
    assert handoff(state) == ""


def test_the_same_traffic_with_a_flat_share_is_the_prefix_note():
    # The control that makes the finding mean something. Byte-identical load,
    # a share that does not move with it, and a different note owns it.
    assert [r["requests"] for r in FLAT] == [r["requests"] for r in SCATTER]
    assert spearman([r["requests"] for r in FLAT],
                    [cached_share([r]) for r in FLAT]) == 0.0
    state, detail = classify(FLAT)
    assert state == "flat-low-share"
    assert "low everywhere rather than low under load" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)


def test_a_share_that_climbs_with_load_is_not_scatter():
    state, detail = classify(RISING)
    assert state == "share-rises-with-load"
    assert "the opposite of scatter" in detail
    assert handoff(state) == ""


def test_hours_after_a_gap_are_excluded_before_correlating():
    # The exclusion, tested by the case it exists for. Leave the post-gap hours
    # in and the correlation goes sharply negative, because the cold hours are
    # also the ones that open a burst as it scales up. Take them out and the
    # linked hours are uniformly warm.
    everything = spearman([r["requests"] for r in BURSTY],
                          [cached_share([r]) for r in BURSTY])
    assert everything is not None and round(everything, 2) == -0.87

    assert len(continuation_rows(BURSTY)) == 42
    assert len(resumption_rows(BURSTY)) == 21
    assert cached_share(continuation_rows(BURSTY)) == 0.7
    assert cached_share(resumption_rows(BURSTY)) == 0.0

    state, detail = classify(BURSTY)
    assert state == "cold-only-after-idle"
    assert "70% cached in linked hours against 0% in the 21 hour(s)" in detail
    assert "prompt-cache-retention-left-at-default" in handoff(state)


def test_no_cached_tokens_at_any_load_is_an_eligibility_question():
    state, detail = classify(contiguous(lambda _load: 0.0))
    assert state == "no-cached-tokens"
    assert "not one cached" in detail
    assert "prompt-below-model-cache-minimum" in handoff(state)


def test_a_flat_request_rate_supports_no_verdict():
    # Nothing can be said about concurrency when the concurrency never moves,
    # and returning 0.0 there would read as "no relationship" rather than
    # "no evidence".
    steady = [hour(i, 1000, 0.6 if i % 2 else 0.2) for i in range(168)]
    assert spearman([r["requests"] for r in steady],
                    [cached_share([r]) for r in steady]) is None
    assert classify(steady)[0] == "load-does-not-vary"


def test_pooled_share_is_weighted_by_traffic():
    # An hour with nine requests must not outvote an hour with nine thousand.
    mixed = [hour(0, 10, 1.0), hour(1, 10_000, 0.1)]
    assert round(cached_share(mixed), 4) == 0.1009
    assert cached_share([]) is None
    assert cached_share([{"input": 0, "cached": 0}]) is None


def test_the_hour_index_survives_both_shapes_and_midnight():
    assert hour_index(1_755_388_800) == 1_755_388_800 // 3600
    assert hour_index("2026-08-17T23:00Z") + 1 == hour_index("2026-08-18T00:00Z")
    assert hour_label(hour_index("2026-08-17T09:00Z")) == "2026-08-17T09:00Z"
    assert hour_index("nonsense") is None
    assert hour_index(None) is None


def test_buckets_are_folded_into_project_and_model_series():
    buckets = [{"start_time": (BASE + i) * 3600,
                "results": [{"project_id": "proj_abc123", "model": "gpt-5.6",
                             "num_model_requests": LOAD[i % 24],
                             "input_tokens": LOAD[i % 24] * 2000,
                             "input_cached_tokens":
                                 int(LOAD[i % 24] * 2000
                                     * (0.72 - 0.00016 * LOAD[i % 24]))}]}
               for i in range(168)]
    series = rows_by_series(buckets)
    rows = series[("proj_abc123", "gpt-5.6")]
    assert len(rows) == 168
    assert [r["index"] for r in rows] == sorted(r["index"] for r in rows)
    assert classify(rows)[0] == "load-correlated-misses"


def test_thin_and_unreadable_windows_produce_no_verdict():
    assert classify([hour(i, 500, 0.5) for i in range(10)])[0] == "too-few-linked-hours"
    assert classify([])[0] == "too-few-linked-hours"
    assert classify(None)[0] == "too-few-linked-hours"
    assert spearman([1, 2], [1, 2]) is None
    assert spearman([1, 2, 3], None) is None
    assert load_split([]) == (None, None, None, None)
    assert rows_by_series([{"start_time": "bad", "results": []}]) == {}
''',
"test_js_file": "openai-cache-key-routing-scatter.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cachedShare, classify, continuationRows, handoff, hourIndex, hourLabel,
         loadSplit, resumptionRows, rowsBySeries, spearman }
  from './openai-cache-key-routing-scatter.mjs';

const BASE = hourIndex('2026-08-17T00:00Z');

const LOAD = [200, 150, 120, 100, 120, 200, 400, 900, 1800, 3000, 3600, 3800,
              3900, 3800, 3600, 3000, 2400, 1800, 1200, 800, 600, 450, 350, 260];

const hour = (offset, requests, share) => {
  const tokens = requests * 2000;
  return { index: BASE + offset, hour: hourLabel(BASE + offset), requests,
           input: tokens, cached: Math.round(tokens * share) };
};

const contiguous = (shareOfLoad) => Array.from({ length: 168 },
  (_, i) => hour(i, LOAD[i % 24], shareOfLoad(LOAD[i % 24])));

const SCATTER = contiguous((load) => 0.72 - 0.00016 * load);
const FLAT = contiguous(() => 0.10);
const RISING = contiguous((load) => 0.10 + 0.00016 * load);

// Three-hour bursts five hours apart, each opening at full tilt: the busiest
// hour of every burst is also the coldest, because it follows the idle stretch.
const BURSTY = (() => {
  const shape = [[3000, 0.0], [1000, 0.7], [400, 0.7]];
  const rows = [];
  for (let burst = 0; burst < 21; burst += 1) {
    shape.forEach(([requests, share], step) => {
      rows.push(hour(burst * 8 + step, requests, share));
    });
  }
  return rows;
})();

test('the cached share falling with load is the finding', () => {
  const [quiet, busy, quietRate, busyRate] = loadSplit(SCATTER);
  assert.equal(Number(quiet.toFixed(2)), 0.69);
  assert.equal(Number(busy.toFixed(2)), 0.16);
  assert.ok(quietRate < 300 && busyRate > 3400);

  const rho = spearman(SCATTER.map((r) => r.requests),
                       SCATTER.map((r) => cachedShare([r])));
  assert.equal(Number(rho.toFixed(3)), -1);

  const [state, detail] = classify(SCATTER);
  assert.equal(state, 'load-correlated-misses');
  assert.match(detail, /68% in the quietest hours/);
  assert.match(detail, /16% in the busiest/);
  assert.match(detail, /rank correlation -1\\.00/);
  assert.equal(handoff(state), '');
});

test('the same traffic with a flat share is the prefix note', () => {
  assert.deepEqual(FLAT.map((r) => r.requests), SCATTER.map((r) => r.requests));
  assert.equal(spearman(FLAT.map((r) => r.requests),
                        FLAT.map((r) => cachedShare([r]))), 0);
  const [state, detail] = classify(FLAT);
  assert.equal(state, 'flat-low-share');
  assert.match(detail, /low everywhere rather than low under load/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
});

test('a share that climbs with load is not scatter', () => {
  const [state, detail] = classify(RISING);
  assert.equal(state, 'share-rises-with-load');
  assert.match(detail, /the opposite of scatter/);
  assert.equal(handoff(state), '');
});

test('hours after a gap are excluded before correlating', () => {
  const everything = spearman(BURSTY.map((r) => r.requests),
                              BURSTY.map((r) => cachedShare([r])));
  assert.equal(Number(everything.toFixed(2)), -0.87);

  assert.equal(continuationRows(BURSTY).length, 42);
  assert.equal(resumptionRows(BURSTY).length, 21);
  assert.equal(cachedShare(continuationRows(BURSTY)), 0.7);
  assert.equal(cachedShare(resumptionRows(BURSTY)), 0);

  const [state, detail] = classify(BURSTY);
  assert.equal(state, 'cold-only-after-idle');
  assert.match(detail, /70% cached in linked hours against 0% in the 21 hour\\(s\\)/);
  assert.match(handoff(state), /prompt-cache-retention-left-at-default/);
});

test('no cached tokens at any load is an eligibility question', () => {
  const [state, detail] = classify(contiguous(() => 0));
  assert.equal(state, 'no-cached-tokens');
  assert.match(detail, /not one cached/);
  assert.match(handoff(state), /prompt-below-model-cache-minimum/);
});

test('a flat request rate supports no verdict', () => {
  const steady = Array.from({ length: 168 },
    (_, i) => hour(i, 1000, i % 2 ? 0.6 : 0.2));
  assert.equal(spearman(steady.map((r) => r.requests),
                        steady.map((r) => cachedShare([r]))), null);
  assert.equal(classify(steady)[0], 'load-does-not-vary');
});

test('pooled share is weighted by traffic', () => {
  const mixed = [hour(0, 10, 1.0), hour(1, 10000, 0.1)];
  assert.equal(Number(cachedShare(mixed).toFixed(4)), 0.1009);
  assert.equal(cachedShare([]), null);
  assert.equal(cachedShare([{ input: 0, cached: 0 }]), null);
});

test('the hour index survives both shapes and midnight', () => {
  assert.equal(hourIndex(1755388800), Math.floor(1755388800 / 3600));
  assert.equal(hourIndex('2026-08-17T23:00Z') + 1, hourIndex('2026-08-18T00:00Z'));
  assert.equal(hourLabel(hourIndex('2026-08-17T09:00Z')), '2026-08-17T09:00Z');
  assert.equal(hourIndex('nonsense'), null);
  assert.equal(hourIndex(null), null);
});

test('buckets are folded into project and model series', () => {
  const buckets = Array.from({ length: 168 }, (_, i) => ({
    start_time: (BASE + i) * 3600,
    results: [{ project_id: 'proj_abc123', model: 'gpt-5.6',
                num_model_requests: LOAD[i % 24],
                input_tokens: LOAD[i % 24] * 2000,
                input_cached_tokens: Math.trunc(LOAD[i % 24] * 2000
                  * (0.72 - 0.00016 * LOAD[i % 24])) }],
  }));
  const rows = rowsBySeries(buckets).get('proj_abc123\\tgpt-5.6');
  assert.equal(rows.length, 168);
  assert.deepEqual(rows.map((r) => r.index), [...rows.map((r) => r.index)].sort((a, b) => a - b));
  assert.equal(classify(rows)[0], 'load-correlated-misses');
});

test('thin and unreadable windows produce no verdict', () => {
  const thin = Array.from({ length: 10 }, (_, i) => hour(i, 500, 0.5));
  assert.equal(classify(thin)[0], 'too-few-linked-hours');
  assert.equal(classify([])[0], 'too-few-linked-hours');
  assert.equal(classify(null)[0], 'too-few-linked-hours');
  assert.equal(spearman([1, 2], [1, 2]), null);
  assert.equal(spearman([1, 2, 3], null), null);
  assert.deepEqual(loadSplit([]), [null, null, null, null]);
  assert.equal(rowsBySeries([{ start_time: 'bad', results: [] }]).size, 0);
});
''',
"faq": [
 ("Why is a low cached share not enough on its own?",
  "Because four different faults produce one. A prompt under the model's floor never caches at all. A prefix that changes between calls caches and never matches. An entry evicted during idle time is gone before the next run. And requests scattered across a fleet miss a cache that exists and is warm. Every one of those shows up as the same low number in the same field, and each has a different repair. The slope against load is what separates the fourth from the other three: it is the only one of the four that gets worse as you add capacity."),
 ("What does prompt_cache_key actually do?",
  "It influences routing so that requests carrying the same key are more likely to reach the same cache. The documentation is careful about this and so should you be: it does not pin a request to a machine and it does not guarantee a cache read. It is a hint that raises the odds, and the effect is statistical and visible in aggregate over hours rather than deterministic per call. It is also not part of the prompt, so it does not change the prefix and cannot invalidate anything by being set."),
 ("How coarse should the key be?",
  "Coarse enough to concentrate traffic and no coarser. The template name, or the template name plus a tenant id, is usually right. A per-request id is the classic mistake: it looks like a cache key, it satisfies whatever review asked for one, and it scatters the fleet exactly as badly as having no key at all, because no two requests ever share it. If you find yourself putting anything that varies per call into it, you have built a request id."),
 ("Why exclude the hours that follow a gap?",
  "Because they run cold for a reason that has nothing to do with routing, and because scheduled work tends to open at its busiest. A nightly batch that fires hard at 02:00 after six idle hours produces a cold hour and a high request count at the same moment, which is a textbook negative correlation with no routing problem anywhere in it. The tests build exactly that series and check the script does not claim it. The count of dropped hours is printed so the exclusion is visible rather than assumed."),
 ("Should the cached share climb as traffic grows?",
  "On a well-keyed fleet, yes, and the script reports that case rather than staying quiet about it. Density is what keeps entries warm, so busy hours ought to cache better than quiet ones. That is the shape to aim for after the repair, and it is a useful thing to be able to point at: a positive correlation is evidence that the prefix is stable and the routing hint is landing, which is a stronger statement than an average that happens to look acceptable this week."),
],
"related": [REL_EVICT, REL_CHURN, REL_FLOOR],
"citations": [CITE_OAI_CACHING, CITE_OAI_USAGE_COMPLETIONS, CITE_OAI_ADMIN, CITE_OAI_RESPONSES],
},
{
"slug": "prompt-cache-retention-left-at-default",
"title": "Every scheduled run starts on a cache that was evicted",
"description": "The cold hours are the ones that resume after idle time. Binning cached share by preceding gap length says whether the repair is a parameter or a schedule.",
"h1": "Every scheduled run starts on a cache that was evicted",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["prompt_cache_retention 24h", "prompt_cache_options ttl 30m",
             "cached tokens zero after idle", "nightly batch cache cold",
             "openai prompt cache eviction"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key (sk-admin-...) with the read scopes. A project key cannot read /v1/organization/.",
"lead": "The nightly enrichment job has run at 02:00 for a year and its prompt has not changed since June. Its cached share is zero. Not low, and not erratic &mdash; zero, on the first hour, every single night, while the two hours that follow it cache at seventy-five per cent off the same prefix. Nothing is misconfigured. The entry written at 02:00 last night was evicted somewhere around 02:40, and by the time the job came back twenty-three hours later there was nothing left to match.",
"short_answer": """<p>With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={T-14d}&amp;bucket_width=1h&amp;limit=168&amp;group_by[]=project_id&amp;group_by[]=model</code>.</p>
<p>Do not zero-fill the idle hours. Keep only the hours that carried traffic, and label each one with how many idle hours sat immediately before it. Then compute the cached share separately for the hours that <em>resume</em> after a gap and the hours that simply <em>continue</em> from a busy hour.</p>
<p>The finding is a healthy continuation share next to a resumption share of roughly zero. Report it as the <strong>shortest gap length at which the share has already collapsed</strong>: one hour, two to five, six to twenty-three, or a day and over. That number is the same number as the retention setting, and it is what tells you whether the repair is a parameter or a schedule.</p>
<p>If the continuously busy hours are cold too, the entry is being lost while it is certainly still alive, which is <a href="/llm/cache-invalidated-by-changing-prefix/">a prefix problem</a> and not this. If there are no gaps at all, read <a href="/llm/prompt-cache-key-not-set/">the routing note</a> instead.</p>""",
"problem": """<p>Cached prefixes do not live forever, and the default retention is measured in minutes rather than hours. On GPT-5.6 and later the window is controlled by <code>prompt_cache_options.ttl</code>; on earlier models by <code>prompt_cache_retention</code>, which accepts <code>"in_memory"</code> &mdash; the short default &mdash; or <code>"24h"</code>. Neither is difficult to set. Both are almost always left alone, because the default is invisible and nothing ever fails.</p>
<p>The workloads this ruins are the ones that look most cacheable on paper. A nightly batch sends the same four-thousand-token prefix a hundred thousand times, so the discount ought to be enormous, and the first call of the run pays full price for a prefix that has not changed in months. A cron job every three hours does the same thing eight times a day. A tenant in a quiet time zone does it whenever they wake up. In each case the prompt is perfect and the schedule is the fault, and the usage report shows a cached share tracking request density rather than prefix stability &mdash; which is the wrong thing for it to track, and the sentence nobody says out loud.</p>""",
"why": """<p><strong>The finding is positional, and nothing else in the section is.</strong> The other caching notes read a ratio against totals, against time, or against load. This one reads it against how long the traffic had been away. Two hours with identical request counts, identical input tokens and identical prompts get different verdicts here purely because of what happened in the hours before them, and that is the only signal that separates eviction from every other cause of a zero.</p>
<p><strong>The idle hours must not become rows.</strong> A gap is the distance between two rows that carried traffic. Zero-filling the empty hours makes the series contiguous, which removes every gap in it and turns the check into an expensive way of computing the average. It also invents zero-share hours that would be the largest anomaly in most windows.</p>
<p><strong>The shortest collapsed band is reported, not the worst one.</strong> Everything caches badly after a week; that tells you nothing. What decides the repair is whether a <em>single</em> idle hour was already enough, which means no retention option on offer covers the gap and the schedule has to change, or whether it takes a full day, which is precisely the case the 24-hour setting exists for. Reporting the worst band would send every reader to the same answer.</p>
<p><strong>The warm baseline is the workload's own best hour.</strong> The comparison is against the same prefix on the same model at continuous traffic, not against a target borrowed from a docs page. That is what makes the foregone-token number defensible: it is the discount this exact traffic is already proving it can get, applied to the hours that did not get it. If the continuous hours are themselves weak, the script refuses the finding and says the gaps are not the main story.</p>
<p><strong>Hourly buckets cannot see an idle stretch shorter than an hour, and the output says so.</strong> A gap band of "1h" is a ceiling on how quickly the entry went, not a measurement of it: the entry may well have expired thirty minutes in. The first row of the window is also dropped rather than guessed, because nothing is visible before the window opens and calling it a continuation would flatter the baseline the whole finding rests on.</p>""",
"steps": [
 {"h": "Pull a fortnight of hourly buckets per project and model",
  "body": """<p>Fourteen days rather than seven, because a nightly job produces one resumption hour per day and a check that rests on thirteen of them wants more than seven. Group by <code>project_id</code> and <code>model</code>: a continuously busy service in the same project will otherwise supply a warm average that hides the batch entirely.</p>"""},
 {"h": "Keep only the hours with traffic, and measure the gaps between them",
  "body": """<p>The gap before an hour is the number of empty hours immediately preceding it, computed on integer hour indices so a gap that crosses midnight is not counted wrongly. Drop the first row of the window; its gap is unknowable and guessing it either way biases the baseline.</p>"""},
 {"h": "Split into continuation hours and resumption hours",
  "body": """<p>Gap of zero is a continuation, and those hours are the warm baseline. Anything above zero is a resumption. If there are almost no resumptions, this series has no idle periods and the note does not apply; if there are almost no continuations, there is no baseline to compare against and the script says so.</p>"""},
 {"h": "Bin the resumptions by gap length and find the shortest cold band",
  "body": """<p>1h, 2&ndash;5h, 6&ndash;23h, 24h and over. Each band maps onto a different repair, and the shortest one already at zero is the answer. A band with only one or two hours in it decides nothing and is skipped.</p>"""},
 {"h": "Set the retention explicitly, then reshape the schedule",
  "body": """<p><code>prompt_cache_retention="24h"</code> on pre-GPT-5.6 routes; <code>prompt_cache_options={"ttl": "30m"}</code> on GPT-5.6 and later so the intent is visible in the code rather than inherited. Then the part no parameter fixes: run intermittent work in one contiguous window instead of scattering it across the day, so the first call warms an entry the rest of the batch reads.</p>"""},
],
"verify": """<p>Re-read the same fortnight after the change. The band that was at zero should come up toward the continuation share; if it does not, the gap is longer than the retention you set and the remaining repair is the schedule.</p>
<pre><code class="language-bash">python3 openai_cache_cold_after_idle.py --days 14
# cold-after-idle          proj_abc123 / gpt-5.6  75% cached in continuously busy hours and 0% in the 13 hour(s) that resume after a gap of 6-23h. The prefix is fine; the entry is evicted while nobody is calling.
#   after a gap of 6-23h  13 hour(s), 0% cached
#   repair: the cache survives a busy hour and not a gap of 6-23h
#   repair: on models before GPT-5.6, set prompt_cache_retention="24h" on this route
#   repair: about 15600000 input token(s) in this window would have been cached at this workload's own continuous rate
# 4 project/model series checked, 1 finding(s)</code></pre>""",
"code_intro": "One paginated GET and no writes. The three functions that carry the note are <code>with_gaps</code>, <code>bin_shares</code> and <code>collapse_bin</code>. The first annotates every active hour with the idle hours before it and deliberately discards the first row of the window, because its gap is unknowable and a guess in either direction biases the baseline. The second is the shape nothing else in this section computes: a cached share per gap length. The third picks the <em>shortest</em> band that has already collapsed rather than the worst, because that is the number that decides between a parameter and a schedule. <code>foregone_tokens</code> prices the loss against this workload's own continuous rate rather than a borrowed target.",
"py_file": "openai_cache_cold_after_idle.py",
"py": '''"""Find OpenAI traffic that runs cold in the hours that follow a gap.

Read only. One paginated GET against the Usage API, which needs an admin key
(sk-admin-...); a project key is rejected by every /v1/organization/ path, and
an admin key can be provisioned with the read scopes only.

Cached prefixes are evicted after an idle period, and the default window is
short. A nightly batch, a low-traffic tenant or a cron job that fires every few
hours therefore starts cold every single time, on a prefix that has not changed
in months. The signature is positional rather than arithmetic: the cold hours
are the ones that resume traffic after a gap, and the hours that follow a busy
hour are fine. Nothing about the prompt is wrong.

The finding is reported as the shortest gap length at which the share has
already collapsed, because that number and the retention setting are the same
number, and it is what tells you whether the repair is a parameter or a
schedule.

The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_cache_cold_after_idle")

API = "https://api.openai.com/v1"

# Gap lengths in hours, coarse enough that each bin maps onto a different
# repair. Ordered shortest first: the finding is the first one that is already
# cold, not the worst one.
BIN_ORDER = ("1h", "2-5h", "6-23h", "24h+")

FINDINGS = ("cold-after-idle",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def hour_index(stamp):
    """Hours since the epoch. Pure. None if unreadable.

    Gaps have to be integer arithmetic. Counting idle hours by comparing
    formatted stamps gets 23:00 and 00:00 wrong every night, and a nightly job
    is exactly the workload this note is about.
    """
    if isinstance(stamp, bool) or stamp is None:
        return None
    if isinstance(stamp, (int, float)):
        return int(stamp) // 3600
    text = str(stamp).strip().replace(" ", "T")
    if len(text) < 13:
        return None
    head = text[:13]
    if head[4] != "-" or head[7] != "-" or head[10] != "T":
        return None
    for part in (head[0:4], head[5:7], head[8:10], head[11:13]):
        if not part.isdigit():
            return None
    try:
        when = dt.datetime(int(head[0:4]), int(head[5:7]), int(head[8:10]),
                           int(head[11:13]), tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return int(when.timestamp()) // 3600


def hour_label(index):
    """Render an hour index back as a UTC stamp. Pure."""
    if index is None:
        return "unknown"
    when = dt.datetime.fromtimestamp(int(index) * 3600, dt.timezone.utc)
    return when.strftime("%Y-%m-%dT%H:00Z")


def rows_by_series(buckets):
    """Per (project_id, model), one row per active hour, sorted. Pure.

    Only hours that actually carried traffic become rows. The idle hours are
    not rows and must not be: the gap is the distance between two rows, and a
    zero-filled series would have no gaps in it at all.
    """
    merged = {}
    for bucket in buckets or []:
        index = hour_index(bucket.get("start_time"))
        if index is None:
            continue
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            ident = (str(result.get("project_id") or "unknown"),
                     str(result.get("model") or "unknown"))
            row = merged.setdefault((ident, index),
                                    {"index": index, "hour": hour_label(index),
                                     "requests": 0, "input": 0, "cached": 0})
            row["requests"] += _int(result.get("num_model_requests"))
            row["input"] += _int(result.get("input_tokens"))
            row["cached"] += _int(result.get("input_cached_tokens"))
    out = {}
    for (ident, _index), row in merged.items():
        if row["requests"] > 0 or row["input"] > 0:
            out.setdefault(ident, []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: r["index"])
    return out


def cached_share(rows):
    """Pooled cached share over a set of hours. Pure. None when nothing ran."""
    total = sum(_int(r.get("input")) for r in rows or [])
    if total <= 0:
        return None
    return sum(_int(r.get("cached")) for r in rows or []) / float(total)


def with_gaps(rows):
    """Annotate each hour with the idle hours immediately before it. Pure.

    The first row in the window is dropped rather than given a gap of zero.
    Nothing is visible before the window starts, so whether it resumed after
    idle time or continued from a busy hour is unknowable, and guessing either
    way biases the very comparison this note rests on.
    """
    ordered = sorted(rows or [], key=lambda r: _int(r.get("index")))
    out = []
    previous = None
    for row in ordered:
        index = _int(row.get("index"))
        if previous is not None:
            annotated = dict(row)
            annotated["gap"] = index - previous - 1
            out.append(annotated)
        previous = index
    return out


def gap_bin(gap):
    """Bucket a gap length into the band its repair belongs to. Pure."""
    gap = _int(gap)
    if gap <= 0:
        return "continuous"
    if gap == 1:
        return "1h"
    if gap <= 5:
        return "2-5h"
    if gap <= 23:
        return "6-23h"
    return "24h+"


def bin_shares(annotated):
    """Cached share per gap band. Pure. Returns {band: {hours, input, share}}.

    This is the finding's shape. Everything else in the section reads a ratio
    against time or against load; this reads it against how long the traffic
    had been away.
    """
    out = {}
    for row in annotated or []:
        band = gap_bin(row.get("gap"))
        cell = out.setdefault(band, {"hours": 0, "input": 0, "cached": 0})
        cell["hours"] += 1
        cell["input"] += _int(row.get("input"))
        cell["cached"] += _int(row.get("cached"))
    for cell in out.values():
        cell["share"] = (cell["cached"] / float(cell["input"])
                         if cell["input"] > 0 else None)
    return out


def collapse_bin(bands, cold_ceiling=0.05, min_hours=3):
    """The shortest gap at which the share has already gone. Pure. None if none.

    Shortest rather than worst on purpose. Everything caches badly after a
    week; what decides the repair is whether one idle hour was already enough,
    which is a retention default, or whether it takes a day, which is a
    schedule.
    """
    for band in BIN_ORDER:
        cell = (bands or {}).get(band)
        if not cell or cell.get("share") is None:
            continue
        if cell["hours"] >= min_hours and cell["share"] <= cold_ceiling:
            return band
    return None


def foregone_tokens(bands, warm_share):
    """Tokens that would have been cached at the warm rate. Pure.

    The money. Uncached input in the resumption hours priced against the share
    the same prefix achieves when traffic is continuous, which is the only
    honest benchmark available: it is this workload's own best hour, not a
    target borrowed from somewhere else.
    """
    if warm_share is None:
        return 0
    total = 0
    for band in BIN_ORDER:
        cell = (bands or {}).get(band)
        if not cell or cell.get("share") is None:
            continue
        total += int(max(0.0, warm_share - cell["share"]) * cell["input"])
    return total


def handoff(state):
    """Which note owns this shape, when it is not this one. Pure."""
    if state == "never-idle":
        return ("this series has no gaps at all, so eviction between runs "
                "cannot be the story. If the share is still low, read the "
                "prompt-cache-key-not-set note and check whether it degrades "
                "at peak instead.")
    if state == "cold-everywhere":
        return ("the continuously busy hours are cold too, so the prefix is "
                "not being matched even when the entry is certainly alive. "
                "Read cache-invalidated-by-changing-prefix, and "
                "prompt-below-model-cache-minimum if nothing caches at all.")
    return ""


def classify(rows, cold_ceiling=0.05, warm_floor=0.20, min_hours=24,
             min_band_hours=3):
    """Classify one project and model series. Pure. Returns (state, detail)."""
    annotated = with_gaps(rows)
    if len(annotated) < min_hours:
        return ("too-few-hours",
                "%d usable hour(s) after dropping the first, under the floor of "
                "%d" % (len(annotated), min_hours))

    bands = bin_shares(annotated)
    warm = bands.get("continuous") or {}
    warm_share = warm.get("share")
    idle_hours = sum(cell["hours"] for band, cell in bands.items()
                     if band != "continuous")

    if idle_hours < min_band_hours:
        return ("never-idle",
                "%d hour(s) of traffic and only %d of them resume after a gap"
                % (len(annotated), idle_hours))

    if warm_share is None or warm["hours"] < min_band_hours:
        return ("no-continuous-hours",
                "traffic never runs two hours back to back, so there is no warm "
                "baseline to compare a resumption against")

    if warm_share <= cold_ceiling:
        return ("cold-everywhere",
                "%.0f%% cached even in continuously busy hours" % (warm_share * 100))

    if warm_share < warm_floor:
        return ("warm-baseline-too-weak",
                "%.0f%% cached in continuously busy hours, under the floor of "
                "%.0f%%. The prefix is barely caching at the best of times, so "
                "the gaps are not the main story" % (warm_share * 100, warm_floor * 100))

    band = collapse_bin(bands, cold_ceiling, min_band_hours)
    if band is None:
        return ("warm-after-idle",
                "%.0f%% cached when continuous and no gap band has collapsed"
                % (warm_share * 100))

    cell = bands[band]
    return ("cold-after-idle",
            "%.0f%% cached in continuously busy hours and %.0f%% in the %d "
            "hour(s) that resume after a gap of %s. The prefix is fine; the "
            "entry is evicted while nobody is calling."
            % (warm_share * 100, cell["share"] * 100, cell["hours"], band))


def repair_lines(band, foregone):
    """The repair, keyed to how short a gap already loses the cache. Pure."""
    lines = []
    if band == "1h":
        lines.append("a single idle hour is already enough, so no retention "
                     "setting on offer covers it on its own: the 30m ttl "
                     "expires inside the gap.")
    elif band in ("2-5h", "6-23h"):
        lines.append("the cache survives a busy hour and not a gap of %s, which "
                     "is the default retention window doing exactly what it "
                     "says." % band)
    elif band == "24h+":
        lines.append("gaps of a day or more, which is the one case the 24h "
                     "retention option was added for.")
    lines.extend([
        "on models before GPT-5.6, set prompt_cache_retention=\\"24h\\" on this "
        "route. It is opt-in and costs nothing extra to set.",
        "on GPT-5.6 and later, set prompt_cache_options={\\"ttl\\": \\"30m\\"} "
        "explicitly so the retention is visible in the code rather than "
        "inherited, then check it against your actual gap length.",
        "reshape the schedule. Run intermittent work in one contiguous window "
        "instead of scattering it across the day, so the first call warms an "
        "entry the rest of the batch reads.",
        "about %d input token(s) in this window would have been cached at this "
        "workload's own continuous rate." % foregone,
    ])
    return lines


def window_start(days):
    """Floor to the hour so start_time lands on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    return int((now - dt.timedelta(days=days)).timestamp())


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/ needs an admin key "
                         "(sk-admin-...), not a project key" % r.status_code)
    r.raise_for_status()
    return r.json()


def read_buckets(session, path, params):
    """Walk the paginated usage endpoint."""
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
    ap.add_argument("--days", type=int, default=14,
                    help="days of hourly buckets to read (max 30)")
    ap.add_argument("--cold-ceiling", type=float, default=0.05,
                    help="cached share at or below which a band counts as cold")
    ap.add_argument("--show-all", action="store_true",
                    help="also print series that are behaving")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key "
                  "(sk-admin-...); a project key cannot read /v1/organization/")
        return 2

    days = max(2, min(int(args.days), 30))
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    buckets = read_buckets(session, "/organization/usage/completions", {
        "start_time": window_start(days),
        "bucket_width": "1h",
        "limit": 168,
        "group_by[]": ["project_id", "model"],
    })

    series = rows_by_series(buckets)
    if not series:
        log.info("no completions usage in the last %d day(s)", days)
        return 0

    checked = 0
    bad = 0
    for ident in sorted(series):
        rows = series[ident]
        state, detail = classify(rows, args.cold_ceiling)
        checked += 1
        line = "%-24s %s / %s  %s" % (state, ident[0], ident[1], detail)

        if state in FINDINGS:
            bad += 1
            log.warning(line)
            bands = bin_shares(with_gaps(rows))
            warm = (bands.get("continuous") or {}).get("share")
            band = collapse_bin(bands, args.cold_ceiling)
            for name in BIN_ORDER:
                cell = bands.get(name)
                if cell and cell.get("share") is not None:
                    log.warning("  after a gap of %-5s %d hour(s), %.0f%% cached",
                                name, cell["hours"], cell["share"] * 100)
            for repair in repair_lines(band, foregone_tokens(bands, warm)):
                log.warning("  repair: %s", repair)
            log.warning("  note: hourly buckets cannot see an idle stretch "
                        "shorter than an hour, so a gap band of 1h is a ceiling "
                        "on how quickly the entry actually went.")
        else:
            note = handoff(state)
            if note:
                log.info(line)
                log.info("  %s", note)
            elif args.show_all:
                log.info(line)

    log.info("%d project/model series checked, %d finding(s)", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-cache-cold-after-idle.mjs",
"js": '''/**
 * Find OpenAI traffic that runs cold in the hours that follow a gap.
 *
 * Read only. One paginated GET against the Usage API, which needs an admin key
 * (sk-admin-...). A project key is rejected by /v1/organization/.
 *
 * Cached prefixes are evicted after an idle period and the default window is
 * short, so a nightly batch or a cron job starts cold every time on a prefix
 * that has not changed in months. The signature is positional rather than
 * arithmetic: the cold hours are the ones that resume after a gap, and the
 * hours that follow a busy hour are fine.
 *
 * The finding is the shortest gap length at which the share has already
 * collapsed, because that number and the retention setting are the same
 * number, and it says whether the repair is a parameter or a schedule.
 */
const API = 'https://api.openai.com/v1';

/**
 * Gap lengths in hours, coarse enough that each band maps onto a different
 * repair. Shortest first: the finding is the first band that is already cold.
 */
export const BIN_ORDER = ['1h', '2-5h', '6-23h', '24h+'];

const FINDINGS = new Set(['cold-after-idle']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Hours since the epoch. Pure. Null if unreadable.
 * Gaps have to be integer arithmetic: counting idle hours by comparing
 * formatted stamps gets 23:00 and 00:00 wrong every night, and a nightly job
 * is exactly the workload this note is about.
 */
export function hourIndex(stamp) {
  if (typeof stamp === 'boolean' || stamp === null || stamp === undefined) return null;
  if (typeof stamp === 'number' && Number.isFinite(stamp)) {
    return Math.floor(Math.trunc(stamp) / 3600);
  }
  const text = String(stamp).trim().replace(' ', 'T');
  if (text.length < 13) return null;
  const head = text.slice(0, 13);
  if (!/^\\d{4}-\\d{2}-\\d{2}T\\d{2}$/.test(head)) return null;
  const when = Date.parse(`${head}:00:00Z`);
  if (Number.isNaN(when)) return null;
  return Math.floor(when / 3600000);
}

/** Render an hour index back as a UTC stamp. Pure. */
export function hourLabel(index) {
  if (index === null || index === undefined) return 'unknown';
  return `${new Date(Math.trunc(index) * 3600000).toISOString().slice(0, 13)}:00Z`;
}

/**
 * Per project_id and model, one row per active hour, sorted. Pure.
 * Only hours that carried traffic become rows, and they must not be
 * zero-filled: the gap is the distance between two rows.
 */
export function rowsBySeries(buckets) {
  const merged = new Map();
  for (const bucket of buckets ?? []) {
    const index = hourIndex(bucket?.start_time);
    if (index === null) continue;
    for (const result of bucket?.results ?? []) {
      if (!result || typeof result !== 'object') continue;
      const ident = `${result.project_id ?? 'unknown'}\\t${result.model ?? 'unknown'}`;
      const cell = `${ident}\\t${index}`;
      if (!merged.has(cell)) {
        merged.set(cell, { ident, index, hour: hourLabel(index),
                           requests: 0, input: 0, cached: 0 });
      }
      const row = merged.get(cell);
      row.requests += readInt(result.num_model_requests);
      row.input += readInt(result.input_tokens);
      row.cached += readInt(result.input_cached_tokens);
    }
  }
  const out = new Map();
  for (const row of merged.values()) {
    if (row.requests <= 0 && row.input <= 0) continue;
    if (!out.has(row.ident)) out.set(row.ident, []);
    out.get(row.ident).push(row);
  }
  for (const rows of out.values()) rows.sort((a, b) => a.index - b.index);
  return out;
}

/** Pooled cached share over a set of hours. Pure. Null when nothing ran. */
export function cachedShare(rows) {
  let input = 0;
  let cached = 0;
  for (const row of rows ?? []) {
    input += readInt(row?.input);
    cached += readInt(row?.cached);
  }
  if (input <= 0) return null;
  return cached / input;
}

/**
 * Annotate each hour with the idle hours immediately before it. Pure.
 * The first row is dropped rather than given a gap of zero: nothing is visible
 * before the window starts, and guessing either way biases the comparison this
 * note rests on.
 */
export function withGaps(rows) {
  const ordered = [...(rows ?? [])].sort((a, b) => readInt(a?.index) - readInt(b?.index));
  const out = [];
  let previous = null;
  for (const row of ordered) {
    const index = readInt(row?.index);
    if (previous !== null) out.push({ ...row, gap: index - previous - 1 });
    previous = index;
  }
  return out;
}

/** Bucket a gap length into the band its repair belongs to. Pure. */
export function gapBin(gap) {
  const n = readInt(gap);
  if (n <= 0) return 'continuous';
  if (n === 1) return '1h';
  if (n <= 5) return '2-5h';
  if (n <= 23) return '6-23h';
  return '24h+';
}

/**
 * Cached share per gap band. Pure. The finding's shape: everything else in the
 * section reads a ratio against time or against load, this reads it against
 * how long the traffic had been away.
 */
export function binShares(annotated) {
  const out = {};
  for (const row of annotated ?? []) {
    const band = gapBin(row?.gap);
    if (!out[band]) out[band] = { hours: 0, input: 0, cached: 0, share: null };
    out[band].hours += 1;
    out[band].input += readInt(row?.input);
    out[band].cached += readInt(row?.cached);
  }
  for (const cell of Object.values(out)) {
    cell.share = cell.input > 0 ? cell.cached / cell.input : null;
  }
  return out;
}

/**
 * The shortest gap at which the share has already gone. Pure. Null if none.
 * Shortest rather than worst on purpose: what decides the repair is whether
 * one idle hour was already enough, or whether it takes a day.
 */
export function collapseBin(bands, coldCeiling = 0.05, minHours = 3) {
  for (const band of BIN_ORDER) {
    const cell = (bands ?? {})[band];
    if (!cell || cell.share === null || cell.share === undefined) continue;
    if (cell.hours >= minHours && cell.share <= coldCeiling) return band;
  }
  return null;
}

/**
 * Tokens that would have been cached at the warm rate. Pure.
 * Priced against the share this same prefix achieves when traffic is
 * continuous, which is this workload's own best hour rather than a borrowed
 * target.
 */
export function foregoneTokens(bands, warmShare) {
  if (warmShare === null || warmShare === undefined) return 0;
  let total = 0;
  for (const band of BIN_ORDER) {
    const cell = (bands ?? {})[band];
    if (!cell || cell.share === null || cell.share === undefined) continue;
    total += Math.trunc(Math.max(0, warmShare - cell.share) * cell.input);
  }
  return total;
}

/** Which note owns this shape, when it is not this one. Pure. */
export function handoff(state) {
  if (state === 'never-idle') {
    return 'this series has no gaps at all, so eviction between runs cannot be '
      + 'the story. If the share is still low, read the prompt-cache-key-not-set '
      + 'note and check whether it degrades at peak instead.';
  }
  if (state === 'cold-everywhere') {
    return 'the continuously busy hours are cold too, so the prefix is not being '
      + 'matched even when the entry is certainly alive. Read '
      + 'cache-invalidated-by-changing-prefix, and '
      + 'prompt-below-model-cache-minimum if nothing caches at all.';
  }
  return '';
}

/** Classify one project and model series. Pure. Returns [state, detail]. */
export function classify(rows, coldCeiling = 0.05, warmFloor = 0.20,
                         minHours = 24, minBandHours = 3) {
  const annotated = withGaps(rows);
  if (annotated.length < minHours) {
    return ['too-few-hours',
      `${annotated.length} usable hour(s) after dropping the first, under the `
      + `floor of ${minHours}`];
  }

  const bands = binShares(annotated);
  const warm = bands.continuous ?? {};
  const warmShare = warm.share ?? null;
  let idleHours = 0;
  for (const [band, cell] of Object.entries(bands)) {
    if (band !== 'continuous') idleHours += cell.hours;
  }

  if (idleHours < minBandHours) {
    return ['never-idle',
      `${annotated.length} hour(s) of traffic and only ${idleHours} of them `
      + 'resume after a gap'];
  }

  if (warmShare === null || (warm.hours ?? 0) < minBandHours) {
    return ['no-continuous-hours',
      'traffic never runs two hours back to back, so there is no warm baseline '
      + 'to compare a resumption against'];
  }

  if (warmShare <= coldCeiling) {
    return ['cold-everywhere',
      `${(warmShare * 100).toFixed(0)}% cached even in continuously busy hours`];
  }

  if (warmShare < warmFloor) {
    return ['warm-baseline-too-weak',
      `${(warmShare * 100).toFixed(0)}% cached in continuously busy hours, under `
      + `the floor of ${(warmFloor * 100).toFixed(0)}%. The prefix is barely `
      + 'caching at the best of times, so the gaps are not the main story'];
  }

  const band = collapseBin(bands, coldCeiling, minBandHours);
  if (band === null) {
    return ['warm-after-idle',
      `${(warmShare * 100).toFixed(0)}% cached when continuous and no gap band has collapsed`];
  }

  const cell = bands[band];
  return ['cold-after-idle',
    `${(warmShare * 100).toFixed(0)}% cached in continuously busy hours and `
    + `${(cell.share * 100).toFixed(0)}% in the ${cell.hours} hour(s) that resume `
    + `after a gap of ${band}. The prefix is fine; the entry is evicted while `
    + 'nobody is calling.'];
}

/** The repair, keyed to how short a gap already loses the cache. Pure. */
export function repairLines(band, foregone) {
  const lines = [];
  if (band === '1h') {
    lines.push('a single idle hour is already enough, so no retention setting '
      + 'on offer covers it on its own: the 30m ttl expires inside the gap.');
  } else if (band === '2-5h' || band === '6-23h') {
    lines.push(`the cache survives a busy hour and not a gap of ${band}, which `
      + 'is the default retention window doing exactly what it says.');
  } else if (band === '24h+') {
    lines.push('gaps of a day or more, which is the one case the 24h retention '
      + 'option was added for.');
  }
  lines.push(
    'on models before GPT-5.6, set prompt_cache_retention="24h" on this route. '
    + 'It is opt-in and costs nothing extra to set.',
    'on GPT-5.6 and later, set prompt_cache_options={"ttl": "30m"} explicitly so '
    + 'the retention is visible in the code rather than inherited, then check it '
    + 'against your actual gap length.',
    'reshape the schedule. Run intermittent work in one contiguous window '
    + 'instead of scattering it across the day, so the first call warms an entry '
    + 'the rest of the batch reads.',
    `about ${foregone} input token(s) in this window would have been cached at `
    + "this workload's own continuous rate.",
  );
  return lines;
}

function windowStart(days) {
  const now = new Date();
  now.setUTCMinutes(0, 0, 0);
  return Math.floor((now.getTime() - days * 86400000) / 1000);
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/ needs an admin `
                    + 'key (sk-admin-...), not a project key');
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
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key '
                  + '(sk-admin-...); a project key cannot read /v1/organization/');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(2, Math.min(Number(process.env.DAYS ?? 14), 30));
  const coldCeiling = Number(process.env.COLD_CEILING ?? 0.05);
  const showAll = process.env.SHOW_ALL === '1';

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organization/usage/completions', {
    start_time: windowStart(days),
    bucket_width: '1h',
    limit: 168,
    'group_by[]': ['project_id', 'model'],
  })) buckets.push(bucket);

  const series = rowsBySeries(buckets);
  if (series.size === 0) {
    console.log(`no completions usage in the last ${days} day(s)`);
    return;
  }

  let checked = 0;
  let bad = 0;
  for (const ident of [...series.keys()].sort()) {
    const rows = series.get(ident);
    const [state, detail] = classify(rows, coldCeiling);
    checked += 1;
    const line = `${state.padEnd(24)} ${ident.replace('\\t', ' / ')}  ${detail}`;

    if (FINDINGS.has(state)) {
      bad += 1;
      console.warn(line);
      const bands = binShares(withGaps(rows));
      const warm = bands.continuous?.share ?? null;
      const band = collapseBin(bands, coldCeiling);
      for (const name of BIN_ORDER) {
        const cell = bands[name];
        if (cell && cell.share !== null) {
          console.warn(`  after a gap of ${name.padEnd(5)} ${cell.hours} hour(s), `
                       + `${(cell.share * 100).toFixed(0)}% cached`);
        }
      }
      for (const repair of repairLines(band, foregoneTokens(bands, warm))) {
        console.warn(`  repair: ${repair}`);
      }
      console.warn('  note: hourly buckets cannot see an idle stretch shorter '
                   + 'than an hour, so a gap band of 1h is a ceiling on how '
                   + 'quickly the entry actually went.');
    } else {
      const note = handoff(state);
      if (note) {
        console.log(line);
        console.log(`  ${note}`);
      } else if (showAll) {
        console.log(line);
      }
    }
  }

  console.log(`${checked} project/model series checked, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The main fixture is a batch that runs 02:00 to 05:00 and then sleeps for twenty-one hours, and its load-bearing detail is that <em>every hour sends exactly the same number of requests</em>. Nothing about volume separates the cold hour from the warm ones; only its position after the gap does, which is the claim the note makes and the reason it is not the routing note wearing a different hat. Beside it sits a two-hours-on, one-hour-off series whose collapse is already total after a single idle hour, which is a different repair and a different printed line. Then the refusals: a batch whose continuous hours are cold too, a series with no gaps at all, and a warm baseline too weak to compare against.",
"test_py_file": "test_openai_cache_cold_after_idle.py",
"test_py": '''from openai_cache_cold_after_idle import (bin_shares, cached_share, classify,
                                          collapse_bin, foregone_tokens,
                                          gap_bin, handoff, hour_index,
                                          hour_label, repair_lines,
                                          rows_by_series, with_gaps)

BASE = hour_index("2026-08-17T00:00Z")


def hour(offset, share, requests=800):
    tokens = requests * 2000
    return {"index": BASE + offset, "hour": hour_label(BASE + offset),
            "requests": requests, "input": tokens,
            "cached": int(round(tokens * share))}


def nightly(resume_share=0.0, warm_share=0.75):
    """A batch that runs 02:00 to 05:00 and then sleeps for twenty-one hours.

    Every hour sends the same number of requests, so nothing about load can
    explain the difference between them.
    """
    rows = []
    for day in range(14):
        for step in range(3):
            rows.append(hour(day * 24 + 2 + step,
                             resume_share if step == 0 else warm_share))
    return rows


def two_on_one_off(resume_share=0.0, warm_share=0.70):
    """Two hours on, one hour off, for a fortnight. Every gap is a single hour."""
    rows = []
    for pair in range(112):
        rows.append(hour(pair * 3, resume_share))
        rows.append(hour(pair * 3 + 1, warm_share))
    return rows


NIGHTLY = nightly()
HOURLY_GAPS = two_on_one_off()
CONTINUOUS = [hour(i, 0.60) for i in range(336)]


def test_the_share_against_gap_length_is_the_finding():
    # The note in one assertion. Same prefix, same request rate, and the only
    # thing that separates a cold hour from a warm one is what happened in the
    # twenty-one hours before it.
    annotated = with_gaps(NIGHTLY)
    assert len(annotated) == 41
    assert {r["requests"] for r in annotated} == {800}

    bands = bin_shares(annotated)
    assert bands["continuous"]["hours"] == 28
    assert bands["continuous"]["share"] == 0.75
    assert bands["6-23h"]["hours"] == 13
    assert bands["6-23h"]["share"] == 0.0
    assert collapse_bin(bands) == "6-23h"

    state, detail = classify(NIGHTLY)
    assert state == "cold-after-idle"
    assert "75% cached in continuously busy hours" in detail
    assert "0% in the 13 hour(s) that resume after a gap of 6-23h" in detail
    assert handoff(state) == ""


def test_the_shortest_collapsed_band_is_the_one_reported():
    # Shortest, not worst. A single idle hour losing the entry is a retention
    # default; a day losing it is a schedule, and the repair differs.
    bands = bin_shares(with_gaps(HOURLY_GAPS))
    assert bands["1h"]["hours"] == 111
    assert bands["1h"]["share"] == 0.0
    assert collapse_bin(bands) == "1h"

    state, detail = classify(HOURLY_GAPS)
    assert state == "cold-after-idle"
    assert "gap of 1h" in detail
    assert "a single idle hour is already enough" in repair_lines("1h", 0)[0]
    assert "24h retention option" in repair_lines("24h+", 0)[0]


def test_a_series_with_no_gaps_is_someone_elses_note():
    state, detail = classify(CONTINUOUS)
    assert state == "never-idle"
    assert "only 0 of them resume after a gap" in detail
    assert "prompt-cache-key-not-set" in handoff(state)


def test_cold_in_the_busy_hours_too_is_not_eviction():
    # If the entry is cold when it is certainly still alive, the gap is not
    # what is losing it.
    state, detail = classify(nightly(resume_share=0.0, warm_share=0.0))
    assert state == "cold-everywhere"
    assert "0% cached even in continuously busy hours" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)
    assert "prompt-below-model-cache-minimum" in handoff(state)


def test_a_weak_warm_baseline_refuses_the_finding():
    state, detail = classify(nightly(resume_share=0.0, warm_share=0.10))
    assert state == "warm-baseline-too-weak"
    assert "barely caching at the best of times" in detail


def test_a_batch_that_resumes_warm_is_not_a_finding():
    state, detail = classify(nightly(resume_share=0.55))
    assert state == "warm-after-idle"
    assert "no gap band has collapsed" in detail


def test_the_first_hour_of_the_window_is_dropped_not_guessed():
    # Nothing is visible before the window starts, so the first row's gap is
    # unknowable and counting it as continuous would flatter the baseline.
    rows = [hour(0, 0.0), hour(1, 0.9), hour(9, 0.0), hour(10, 0.9)]
    annotated = with_gaps(rows)
    assert [r["gap"] for r in annotated] == [0, 7, 0]
    assert len(annotated) == len(rows) - 1
    assert with_gaps([hour(0, 0.5)]) == []
    assert with_gaps([]) == []


def test_the_gap_bands_line_up_with_the_repairs():
    assert gap_bin(0) == "continuous"
    assert gap_bin(1) == "1h"
    assert gap_bin(2) == "2-5h" and gap_bin(5) == "2-5h"
    assert gap_bin(6) == "6-23h" and gap_bin(23) == "6-23h"
    assert gap_bin(24) == "24h+" and gap_bin(500) == "24h+"
    # A band with almost no hours in it cannot decide anything.
    thin = {"1h": {"hours": 1, "input": 100, "cached": 0, "share": 0.0},
            "24h+": {"hours": 40, "input": 100, "cached": 0, "share": 0.0}}
    assert collapse_bin(thin) == "24h+"


def test_the_foregone_tokens_are_priced_at_the_workloads_own_warm_rate():
    bands = bin_shares(with_gaps(NIGHTLY))
    # 13 resumption hours of 1.6M input tokens, 75% of which would have been
    # cached had the entry survived the night.
    assert bands["6-23h"]["input"] == 13 * 800 * 2000
    assert foregone_tokens(bands, 0.75) == 15_600_000
    assert foregone_tokens(bands, None) == 0
    assert foregone_tokens({}, 0.75) == 0


def test_buckets_are_folded_and_idle_hours_never_become_rows():
    buckets = [{"start_time": (BASE + day * 24 + 2 + step) * 3600,
                "results": [{"project_id": "proj_abc123", "model": "gpt-5.6",
                             "num_model_requests": 800,
                             "input_tokens": 1_600_000,
                             "input_cached_tokens": 0 if step == 0 else 1_200_000}]}
               for day in range(14) for step in range(3)]
    series = rows_by_series(buckets)
    rows = series[("proj_abc123", "gpt-5.6")]
    assert len(rows) == 42
    assert cached_share(rows) == 0.5
    assert classify(rows)[0] == "cold-after-idle"


def test_thin_and_unreadable_windows_produce_no_verdict():
    assert classify([hour(i, 0.5) for i in range(10)])[0] == "too-few-hours"
    assert classify([])[0] == "too-few-hours"
    assert classify(None)[0] == "too-few-hours"
    assert cached_share([]) is None
    assert bin_shares([]) == {}
    assert collapse_bin({}) is None
    assert hour_index("nonsense") is None
    assert rows_by_series([{"start_time": "bad", "results": []}]) == {}
''',
"test_js_file": "openai-cache-cold-after-idle.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { binShares, cachedShare, classify, collapseBin, foregoneTokens, gapBin,
         handoff, hourIndex, hourLabel, repairLines, rowsBySeries, withGaps }
  from './openai-cache-cold-after-idle.mjs';

const BASE = hourIndex('2026-08-17T00:00Z');

const hour = (offset, share, requests = 800) => {
  const tokens = requests * 2000;
  return { index: BASE + offset, hour: hourLabel(BASE + offset), requests,
           input: tokens, cached: Math.round(tokens * share) };
};

/** A batch that runs 02:00 to 05:00 and then sleeps for twenty-one hours. */
const nightly = (resumeShare = 0.0, warmShare = 0.75) => {
  const rows = [];
  for (let day = 0; day < 14; day += 1) {
    for (let step = 0; step < 3; step += 1) {
      rows.push(hour(day * 24 + 2 + step, step === 0 ? resumeShare : warmShare));
    }
  }
  return rows;
};

/** Two hours on, one hour off, for a fortnight. Every gap is a single hour. */
const twoOnOneOff = (resumeShare = 0.0, warmShare = 0.70) => {
  const rows = [];
  for (let pair = 0; pair < 112; pair += 1) {
    rows.push(hour(pair * 3, resumeShare));
    rows.push(hour(pair * 3 + 1, warmShare));
  }
  return rows;
};

const NIGHTLY = nightly();
const HOURLY_GAPS = twoOnOneOff();
const CONTINUOUS = Array.from({ length: 336 }, (_, i) => hour(i, 0.60));

test('the share against gap length is the finding', () => {
  const annotated = withGaps(NIGHTLY);
  assert.equal(annotated.length, 41);
  assert.deepEqual([...new Set(annotated.map((r) => r.requests))], [800]);

  const bands = binShares(annotated);
  assert.equal(bands.continuous.hours, 28);
  assert.equal(bands.continuous.share, 0.75);
  assert.equal(bands['6-23h'].hours, 13);
  assert.equal(bands['6-23h'].share, 0);
  assert.equal(collapseBin(bands), '6-23h');

  const [state, detail] = classify(NIGHTLY);
  assert.equal(state, 'cold-after-idle');
  assert.match(detail, /75% cached in continuously busy hours/);
  assert.match(detail, /0% in the 13 hour\\(s\\) that resume after a gap of 6-23h/);
  assert.equal(handoff(state), '');
});

test('the shortest collapsed band is the one reported', () => {
  const bands = binShares(withGaps(HOURLY_GAPS));
  assert.equal(bands['1h'].hours, 111);
  assert.equal(bands['1h'].share, 0);
  assert.equal(collapseBin(bands), '1h');

  const [state, detail] = classify(HOURLY_GAPS);
  assert.equal(state, 'cold-after-idle');
  assert.match(detail, /gap of 1h/);
  assert.match(repairLines('1h', 0)[0], /a single idle hour is already enough/);
  assert.match(repairLines('24h+', 0)[0], /24h retention option/);
});

test('a series with no gaps is someone elses note', () => {
  const [state, detail] = classify(CONTINUOUS);
  assert.equal(state, 'never-idle');
  assert.match(detail, /only 0 of them resume after a gap/);
  assert.match(handoff(state), /prompt-cache-key-not-set/);
});

test('cold in the busy hours too is not eviction', () => {
  const [state, detail] = classify(nightly(0.0, 0.0));
  assert.equal(state, 'cold-everywhere');
  assert.match(detail, /0% cached even in continuously busy hours/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
  assert.match(handoff(state), /prompt-below-model-cache-minimum/);
});

test('a weak warm baseline refuses the finding', () => {
  const [state, detail] = classify(nightly(0.0, 0.10));
  assert.equal(state, 'warm-baseline-too-weak');
  assert.match(detail, /barely caching at the best of times/);
});

test('a batch that resumes warm is not a finding', () => {
  const [state, detail] = classify(nightly(0.55));
  assert.equal(state, 'warm-after-idle');
  assert.match(detail, /no gap band has collapsed/);
});

test('the first hour of the window is dropped not guessed', () => {
  const rows = [hour(0, 0.0), hour(1, 0.9), hour(9, 0.0), hour(10, 0.9)];
  const annotated = withGaps(rows);
  assert.deepEqual(annotated.map((r) => r.gap), [0, 7, 0]);
  assert.equal(annotated.length, rows.length - 1);
  assert.deepEqual(withGaps([hour(0, 0.5)]), []);
  assert.deepEqual(withGaps([]), []);
});

test('the gap bands line up with the repairs', () => {
  assert.equal(gapBin(0), 'continuous');
  assert.equal(gapBin(1), '1h');
  assert.equal(gapBin(2), '2-5h');
  assert.equal(gapBin(5), '2-5h');
  assert.equal(gapBin(6), '6-23h');
  assert.equal(gapBin(23), '6-23h');
  assert.equal(gapBin(24), '24h+');
  assert.equal(gapBin(500), '24h+');
  const thin = { '1h': { hours: 1, input: 100, cached: 0, share: 0 },
                 '24h+': { hours: 40, input: 100, cached: 0, share: 0 } };
  assert.equal(collapseBin(thin), '24h+');
});

test('the foregone tokens are priced at the workloads own warm rate', () => {
  const bands = binShares(withGaps(NIGHTLY));
  assert.equal(bands['6-23h'].input, 13 * 800 * 2000);
  assert.equal(foregoneTokens(bands, 0.75), 15600000);
  assert.equal(foregoneTokens(bands, null), 0);
  assert.equal(foregoneTokens({}, 0.75), 0);
});

test('buckets are folded and idle hours never become rows', () => {
  const buckets = [];
  for (let day = 0; day < 14; day += 1) {
    for (let step = 0; step < 3; step += 1) {
      buckets.push({
        start_time: (BASE + day * 24 + 2 + step) * 3600,
        results: [{ project_id: 'proj_abc123', model: 'gpt-5.6',
                    num_model_requests: 800, input_tokens: 1600000,
                    input_cached_tokens: step === 0 ? 0 : 1200000 }],
      });
    }
  }
  const rows = rowsBySeries(buckets).get('proj_abc123\\tgpt-5.6');
  assert.equal(rows.length, 42);
  assert.equal(cachedShare(rows), 0.5);
  assert.equal(classify(rows)[0], 'cold-after-idle');
});

test('thin and unreadable windows produce no verdict', () => {
  assert.equal(classify(Array.from({ length: 10 }, (_, i) => hour(i, 0.5)))[0],
    'too-few-hours');
  assert.equal(classify([])[0], 'too-few-hours');
  assert.equal(classify(null)[0], 'too-few-hours');
  assert.equal(cachedShare([]), null);
  assert.deepEqual(binShares([]), {});
  assert.equal(collapseBin({}), null);
  assert.equal(hourIndex('nonsense'), null);
  assert.equal(rowsBySeries([{ start_time: 'bad', results: [] }]).size, 0);
});
''',
"faq": [
 ("How is this different from the routing note?",
  "The routing note asks whether the cached share moves with the request rate; this one asks whether it moves with the time since the last request. They are deliberately built to hand each other the cases they cannot claim. The routing check drops every post-gap hour before it correlates anything, precisely so an eviction problem cannot be read as scatter. This check requires gaps to exist at all, and when a series has none it says the eviction story is unavailable and names the routing note. A workload can have both problems, and then both scripts fire."),
 ("Why bin by gap length instead of just reporting the resumption share?",
  "Because the resumption share tells you there is a problem and the bins tell you which repair. If the share is already zero after one idle hour, no retention option on offer covers it, the 30-minute ttl expires inside the gap, and the only real fix is to stop scattering the work. If it survives five hours and dies at twenty-four, the 24-hour retention setting is exactly the thing that was built for you. Same symptom, opposite conclusions, and the only difference between them is the length of the gap."),
 ("Why not zero-fill the idle hours to get a regular series?",
  "Because that deletes the finding. A gap is the distance between two hours that carried traffic; zero-filling makes every series contiguous and there are no gaps left to measure. It also invents hours with zero requests and zero cached tokens, which then look like the most dramatic collapse in the window and have to be explained away by every branch downstream. The idle hours are absent from the report for a good reason and they stay absent here."),
 ("Can hourly buckets really see this?",
  "They can see the shape, not the moment. A collapse in the one-hour band means the entry was gone within an hour, which is a ceiling on how long it survived and not a measurement: it may well have expired thirty minutes in. That is stated in the output rather than glossed over. For the repairs this check leads to it does not matter much, because the choice between a retention parameter and a schedule change turns on whether the gap is hours or a day, and hourly resolution answers that cleanly."),
 ("How is the wasted spend calculated?",
  "Uncached input in the resumption hours, priced at the cached share the same prefix achieves in continuously busy hours. That benchmark is deliberately this workload's own best hour rather than a figure from a pricing page, so it cannot be argued with: the traffic has already demonstrated it can hit that share on this exact prompt and model. If the continuous hours are weak, the script refuses the finding entirely rather than producing a number nobody can defend."),
],
"related": [REL_SCATTER, REL_CACHE_WRITES, REL_CHURN],
"citations": [CITE_OAI_CACHING, CITE_OAI_USAGE, CITE_OAI_COOKBOOK_USAGE, CITE_OAI_ADMIN],
},
{
"slug": "cache-hit-rate-collapsed-after-model-change",
"title": "Cache read share stepped down the day the model changed",
"description": "A model switch starts cold, which is expected. A sustained collapse aligned with the day the new id first appears is a floor or a default that moved.",
"h1": "Cache read share stepped down the day the model changed",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["cache hit rate dropped after model upgrade",
             "claude model migration cache read share",
             "cache_read_input_tokens step change",
             "new model id cache cold", "cache minimum changed with model"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin...) provisioned read-only. A workspace key is rejected by every /v1/organizations/ path.",
"lead": "The migration was a one-line change and it went perfectly: latency improved, quality held, the per-token rate went down. Three weeks later the input bill was up by a third and nobody could see why, because the thing that changed is not on the invoice as a line item. The cache-read share was sixty-eight per cent for a fortnight, dropped to eleven on the day the new model id first appears in the usage report, and has been eleven ever since. The prompt was never edited.",
"short_answer": """<p>With an <strong>Admin API key</strong>: <code>GET /v1/organizations/usage_report/messages?starting_at={T-31d}&amp;bucket_width=1d&amp;limit=32&amp;group_by[]=model</code>. Per day, <code>cache_read_input_tokens / (cache_read_input_tokens + uncached_input_tokens)</code>.</p>
<p>Find the day each model id <em>first</em> appears. Then do the part that makes the claim falsifiable: compute the largest downward step anywhere in the series, and require it to land on the arrival day. A collapse that is biggest three weeks either side of the switch was not caused by the switch, and the script says so.</p>
<p><strong>Throw the switch day itself away.</strong> Caches are keyed per model, so the first day on a new id is cold by definition and every byte of it is expected. The comparison is the days before against the days after, with the day between them excluded. A dip that recovers is a cache warming up; only a floor that never comes back is structural.</p>
<p>The usual mechanism is the minimum cacheable length: Opus 4.6, Opus 4.5 and Haiku 4.5 need 4,096 tokens where Opus 5 needs 512, so a prompt that never changed can stop qualifying overnight. That is <a href="/llm/prompt-below-model-cache-minimum/">the floor note</a>, and this one names it.</p>""",
"problem": """<p>Model migrations are reviewed for output quality and for the per-token rate, and both of those are visible before you ship. What is not visible is that a cache is keyed per model, so the switch throws away every warm entry you had and starts again. That part is fine and everybody expects it: one cold day, then back to normal.</p>
<p>The failure is when it does not come back. Three things can hold it down and none of them is in the diff. The new model's minimum cacheable prompt length may be higher, so a prefix that used to qualify no longer does &mdash; and the jump is not small, from 512 tokens on Opus 5 to 4,096 on Haiku 4.5. Thinking or effort defaults differ per model and sit inside the cached prefix, so a different default is a different prefix. And a newer tokenizer can produce materially more tokens for the same text, which moves a prefix that used to sit just above a boundary. In all three cases the prompt is untouched, the code is untouched, and the caching outcome changed anyway.</p>""",
"why": """<p><strong>The switch day is excluded, and that single decision is most of the note.</strong> A cold cache on day one of a new model is correct behaviour, so a check that averages that day into either side turns a successful migration into an alarm. Every organization that upgrades a model would fire it. The comparison is strictly the days before against the days after, and the dip on the day itself is reported as context rather than evidence.</p>
<p><strong>Alignment is checked against the whole window, not assumed.</strong> Any thirty-one day window containing both a new model and a decline can be told as a causal story if you only look where you expect. So the script computes the largest downward step at every possible split point and requires the winner to be the arrival. If the biggest fall is somewhere else, the verdict is that something else changed on that day, and the reader is sent to look at deploys with a date in hand.</p>
<p><strong>A model nobody uses is never blamed.</strong> A canary taking three per cent of input cannot move an organization-wide ratio, but it will happily appear as a new id on exactly the day someone else broke the prefix. The check requires the new model to carry at least a fifth of input since it arrived before it is allowed to be the explanation.</p>
<p><strong>Sustained means every day after sits below every day before.</strong> Not a lower mean, which a single bad week can produce; a floor that never recovers. A window where some days since the switch have climbed back above the pre-switch minimum is reported as suggestive and not conclusive, with the advice to widen the window rather than a verdict.</p>
<p><strong>This is an organization-wide ratio and the note says so out loud.</strong> Grouped by model, a second workload that changed on the same day is folded into the same number, and the report carries no request count to normalise against. The output is a date and a magnitude, which is enough to line up against a deploy, and it is deliberately not enough to skip that step.</p>""",
"steps": [
 {"h": "Pull thirty-one daily buckets grouped by model",
  "body": """<p>Daily rather than hourly, because the thing being detected is a permanent shift and not a spacing. Grouping by model is what supplies the arrival dates; the share itself is computed across all models, because the question is what happened to the organization's caching, not to one id's.</p>"""},
 {"h": "Skip the days with no traffic instead of zero-filling them",
  "body": """<p>A day with no input has no share. Inventing a zero for a quiet weekend creates the largest step in most windows, and every branch afterwards then has to explain it away.</p>"""},
 {"h": "Find the arrival day of each model id, and ignore day one",
  "body": """<p>A model present on the first day of the window may have been running for a year; its "arrival" is an artefact of where you started reading. Only ids that first appear after the window opens count. Among those, take the one that carries the most input afterwards.</p>"""},
 {"h": "Compute the step across the arrival, with that day removed",
  "body": """<p>Mean share before against mean share after, excluding the arrival day itself. A drop of about fifteen share points, with the after-share under sixty per cent of the before-share, is a step worth explaining. Then check it is sustained: every day since below every day before.</p>"""},
 {"h": "Prove the alignment, then read the floors",
  "body": """<p>Compute the largest step at every split point and require it at the arrival. Once it holds, compare the two models' minimum cacheable lengths and their thinking and effort defaults, move the breakpoint, and re-measure over three days rather than one &mdash; the day after any breakpoint change is cold for the same reason the switch day was.</p>"""},
],
"verify": """<p>Re-run after the breakpoint moves. Give it three days: the first is cold by construction, and a one-day read on this check is how a successful repair gets rolled back.</p>
<pre><code class="language-bash">python3 anthropic_cache_step_after_model_switch.py --days 31
# collapsed-after-model-change     cache-read share 70% before claude-haiku-4-5-20251001 arrived on 2026-08-16 and 10% after, with the switch day itself excluded. claude-haiku-4-5-20251001 now carries 100% of input and the largest step in the window is exactly there.
#   repair: claude-haiku-4-5-20251001 needs 4096 tokens before a prefix is cacheable and claude-opus-5 needed 512
#   repair: compare their thinking and effort defaults
#   note: this is an organization-wide ratio.
# 31 day(s) checked, 1 finding(s)</code></pre>""",
"code_intro": "One GET and eleven pure functions, three of which exist to try to falsify the finding rather than to make it. <code>step_at</code> measures the change across the arrival with that day deleted, because a cold first day is what a model switch is supposed to cost. <code>best_split</code> computes the largest downward step at every possible split point, so the claim \"the collapse aligns with the switch\" has to survive a search of the whole window rather than being asserted where it was expected. <code>input_share_after</code> refuses to blame a model that carries three per cent of traffic. <code>floor_note</code> reaches for the mechanism only once the step is confirmed, and names the sibling note that owns it.",
"py_file": "anthropic_cache_step_after_model_switch.py",
"py": '''"""Align a collapse in cache-read share with the day a new model id appeared.

Read only. One GET against the Admin API, which needs an Admin API key
(sk-ant-admin...); a workspace key is rejected by every /v1/organizations/
path, and an Admin key can be provisioned read-only.

Caches are keyed per model, so the first day on a new model is cold by
definition and a note that fires on it is wrong. What matters is what happens
on the days after. This finds the single largest step down in the daily
cache-read share anywhere in the window, and then asks whether that step sits
where the new model id first appears. A collapse that lines up with the switch
is the switch; a collapse three weeks either side of it is something else, and
this says so rather than taking the credit.

The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_cache_step_after_model_switch")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Published minimum cacheable prompt length per model family, in tokens. Only
# used to explain a confirmed step, never to make one: a migration from a 512
# floor to a 4,096 floor is the most common reason the share never comes back.
CACHE_MINIMUMS = {
    "claude-opus-5": 512, "claude-fable-5": 512, "claude-mythos-5": 512,
    "claude-mythos-preview": 2048, "claude-opus-4-8": 1024,
    "claude-opus-4-7": 2048, "claude-opus-4-6": 4096, "claude-opus-4-5": 4096,
    "claude-opus-4-1": 1024, "claude-opus-4": 1024, "claude-sonnet-5": 1024,
    "claude-sonnet-4-6": 1024, "claude-sonnet-4-5": 1024, "claude-sonnet-4": 1024,
    "claude-haiku-4-5": 4096, "claude-haiku-3-5": 2048,
}

FINDINGS = ("collapsed-after-model-change",)


def _int(value):
    """Read a usage field as an int. Pure. Missing and unreadable both mean 0."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def cache_minimum(model):
    """The model's minimum cacheable prompt length. Pure. None if unrecognised."""
    name = str(model or "").strip().lower()
    if not name:
        return None
    best = None
    for family, floor in CACHE_MINIMUMS.items():
        if name == family or name.startswith(family + "-"):
            if best is None or len(family) > len(best[0]):
                best = (family, floor)
    return best[1] if best else None


def day_key(stamp):
    """Normalise a timestamp to a UTC day. Pure. None if unreadable."""
    if isinstance(stamp, bool):
        return None
    if isinstance(stamp, (int, float)):
        try:
            when = dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
        return when.strftime("%Y-%m-%d")
    text = str(stamp or "").strip().replace(" ", "T")
    if len(text) < 10:
        return None
    head = text[:10]
    if head[4] != "-" or head[7] != "-":
        return None
    for part in (head[0:4], head[5:7], head[8:10]):
        if not part.isdigit():
            return None
    return head


def daily_rows(buckets):
    """One row per day that carried input, sorted. Pure.

    Days with no traffic are left out rather than zero-filled. A zero-share day
    invented for a weekend would be the largest step in most windows and would
    then have to be explained away by every branch below it.
    """
    merged = {}
    for bucket in buckets or []:
        day = day_key(bucket.get("starting_at") or bucket.get("start_time"))
        if day is None:
            continue
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            model = str(result.get("model") or "unknown")
            creation = result.get("cache_creation") or {}
            row = merged.setdefault(day, {"day": day, "uncached": 0, "reads": 0,
                                          "writes": 0, "by_model": {}})
            uncached = _int(result.get("uncached_input_tokens"))
            reads = _int(result.get("cache_read_input_tokens"))
            writes = (_int(creation.get("ephemeral_5m_input_tokens"))
                      + _int(creation.get("ephemeral_1h_input_tokens")))
            row["uncached"] += uncached
            row["reads"] += reads
            row["writes"] += writes
            row["by_model"][model] = (row["by_model"].get(model, 0)
                                      + uncached + reads + writes)
    rows = [r for r in merged.values() if r["uncached"] + r["reads"] > 0]
    rows.sort(key=lambda r: r["day"])
    for position, row in enumerate(rows):
        row["position"] = position
        row["share"] = row["reads"] / float(row["reads"] + row["uncached"])
    return rows


def arrival_positions(rows):
    """Models that first appear after the window opens. Pure.

    A model present on day one might have been running for a year, so its
    "arrival" is an artefact of where the window starts and it is excluded.
    """
    first = {}
    for row in rows or []:
        for model in (row.get("by_model") or {}):
            first.setdefault(model, _int(row.get("position")))
    return {model: position for model, position in first.items() if position > 0}


def input_share_after(rows, model, position):
    """Fraction of input on one model from a position onward. Pure. None if idle.

    The guard against blaming a model nobody uses. A canary taking one percent
    of traffic cannot move an organization-wide ratio, and a note that lets it
    take the blame will point at the wrong deploy every time.
    """
    total = 0
    mine = 0
    for row in rows or []:
        if _int(row.get("position")) < position:
            continue
        for name, tokens in (row.get("by_model") or {}).items():
            total += _int(tokens)
            if name == model:
                mine += _int(tokens)
    if total <= 0:
        return None
    return mine / float(total)


def step_at(shares, position, min_side=3):
    """The step across one position, with that day itself left out. Pure.

    Returns (before, after, delta) or Nones. Excluding the day is the whole
    care in this function: a new model's first day is cold because the cache is
    empty, which is correct behaviour, and averaging it into either side turns
    an expected cold start into a finding.
    """
    shares = list(shares or [])
    before = shares[:position]
    after = shares[position + 1:]
    if len(before) < min_side or len(after) < min_side:
        return (None, None, None)
    b = sum(before) / float(len(before))
    a = sum(after) / float(len(after))
    return (b, a, b - a)


def best_split(shares, min_side=3):
    """The largest downward step anywhere in the series. Pure.

    Returns (position, delta) or (None, None). This is what makes the alignment
    claim falsifiable: without it, any window containing both a new model and a
    decline reads as causation. With it, the decline has to be biggest at the
    switch and nowhere else.
    """
    shares = list(shares or [])
    n = len(shares)
    if n < min_side * 2:
        return (None, None)
    best_position, best_delta = None, None
    for position in range(min_side, n - min_side + 1):
        b = sum(shares[:position]) / float(position)
        a = sum(shares[position:]) / float(n - position)
        delta = b - a
        if best_delta is None or delta > best_delta:
            best_position, best_delta = position, delta
    return (best_position, best_delta)


def sustained(shares, position, min_side=3):
    """True when every day after the switch sits below every day before. Pure.

    A dip that recovers is a deploy that was rolled back, or a cache warming up
    over a few days. Only a floor that never comes back is structural.
    """
    shares = list(shares or [])
    before = shares[:position]
    after = shares[position + 1:]
    if len(before) < min_side or len(after) < min_side:
        return False
    return max(after) < min(before)


def floor_note(old_model, new_model):
    """Why the share might not come back, when the floors explain it. Pure."""
    old_floor = cache_minimum(old_model)
    new_floor = cache_minimum(new_model)
    if old_floor is None or new_floor is None:
        return ""
    if new_floor > old_floor:
        return ("%s needs %d tokens before a prefix is cacheable and %s needed "
                "%d, so a prompt that has not changed can have stopped "
                "qualifying. That is the prompt-below-model-cache-minimum note, "
                "and it is the most likely mechanism here."
                % (new_model, new_floor, old_model, old_floor))
    return ("%s has the same or a lower cache minimum (%d) as %s (%d), so the "
            "floor does not explain this. Look at thinking or effort defaults "
            "and at the tokenizer instead."
            % (new_model, new_floor, old_model, old_floor))


def handoff(state):
    """Which note owns this shape, when it is not this one. Pure."""
    if state == "no-new-model":
        return ("no model id appeared for the first time in this window, so "
                "nothing here can be attributed to a switch. If the share is "
                "low, read cache-invalidated-by-changing-prefix and "
                "prompt-caching-never-used.")
    if state == "step-elsewhere":
        return ("the largest step in the series is not where the new model "
                "arrived, so something else changed on that day. Read the "
                "cache-invalidated-by-changing-prefix note and line the step up "
                "against your deploys.")
    if state == "expected-cold-start":
        return ("the share dropped on the switch day and came back. That is a "
                "cold cache filling up, which is what a model change is "
                "supposed to cost, and it is not a finding.")
    return ""


def classify(rows, min_days=14, min_drop=0.15, ratio_floor=0.6,
             min_migration=0.20, min_side=3):
    """Classify one window. Pure. Returns (state, detail)."""
    rows = rows or []
    if len(rows) < min_days:
        return ("too-few-days",
                "%d day(s) with input in the window, under the floor of %d"
                % (len(rows), min_days))

    shares = [r["share"] for r in rows]
    arrivals = arrival_positions(rows)
    if not arrivals:
        return ("no-new-model",
                "every model id in this window was already present on day one")

    ranked = sorted(arrivals.items(),
                    key=lambda item: input_share_after(rows, item[0], item[1]) or 0.0,
                    reverse=True)
    model, position = ranked[0]
    migration = input_share_after(rows, model, position) or 0.0
    if migration < min_migration:
        return ("new-model-marginal",
                "%s arrived on %s but carries only %.0f%% of input since, under "
                "the floor of %.0f%%. Too small to move the ratio."
                % (model, rows[position]["day"], migration * 100,
                   min_migration * 100))

    before, after, delta = step_at(shares, position, min_side)
    if delta is None:
        return ("window-too-short-around-the-switch",
                "%s arrived on %s with fewer than %d day(s) either side of it"
                % (model, rows[position]["day"], min_side))

    # Alignment is checked before magnitude, and only against a step that is
    # material on its own. A big fall somewhere else in the window disqualifies
    # the switch outright, however the numbers either side of the switch read.
    peak, peak_delta = best_split(shares, min_side)
    if (peak is not None and peak_delta is not None and peak_delta >= min_drop
            and abs(peak - position) > 1):
        return ("step-elsewhere",
                "the share falls hardest at %s, not at the %s switch on %s"
                % (rows[peak]["day"], model, rows[position]["day"]))

    if delta < min_drop or after > before * ratio_floor:
        if before - shares[position] >= min_drop:
            return ("expected-cold-start",
                    "%s arrived on %s, the share dipped to %.0f%% that day and "
                    "settled back at %.0f%% against %.0f%% before"
                    % (model, rows[position]["day"], shares[position] * 100,
                       after * 100, before * 100))
        return ("steady",
                "%s arrived on %s and the share held at %.0f%% against %.0f%% "
                "before" % (model, rows[position]["day"], after * 100,
                            before * 100))

    if peak is None or abs(peak - position) > 1:
        return ("step-elsewhere",
                "the share falls hardest at %s, not at the %s switch on %s"
                % (rows[peak]["day"] if peak is not None else "no single day",
                   model, rows[position]["day"]))

    if not sustained(shares, position, min_side):
        return ("partial-recovery",
                "%.0f%% before the %s switch and %.0f%% after, but some days "
                "since have recovered above the pre-switch floor. Suggestive "
                "and not conclusive: widen the window."
                % (before * 100, model, after * 100))

    return ("collapsed-after-model-change",
            "cache-read share %.0f%% before %s arrived on %s and %.0f%% after, "
            "with the switch day itself excluded. %s now carries %.0f%% of "
            "input and the largest step in the window is exactly there."
            % (before * 100, model, rows[position]["day"], after * 100, model,
               migration * 100))


def previous_model(rows, position):
    """The model carrying the most input before the switch. Pure."""
    totals = {}
    for row in rows or []:
        if _int(row.get("position")) >= position:
            continue
        for name, tokens in (row.get("by_model") or {}).items():
            totals[name] = totals.get(name, 0) + _int(tokens)
    if not totals:
        return None
    return max(totals.items(), key=lambda item: item[1])[0]


def repair_lines(old_model, new_model):
    """What to check about the new model, in the order that pays. Pure."""
    lines = []
    note = floor_note(old_model, new_model)
    if note:
        lines.append(note)
    lines.extend([
        "compare the two models' minimum cacheable token counts and move the "
        "cache_control breakpoint so the prefix clears the higher one.",
        "compare their thinking and effort defaults. Those are model-specific "
        "and they sit inside the cached prefix, so a different default is a "
        "different prefix.",
        "count the prefix again under the new model id. A newer tokenizer can "
        "produce materially more tokens for the same text, which moves a prefix "
        "that used to sit just above a boundary.",
        "then re-measure the cache-read share over the following three days, "
        "not the following one. The first day after any breakpoint change is "
        "cold for the same reason the switch day was.",
    ])
    return lines


def window_start(days):
    """Floor to the day: starting_at has to sit on a bucket boundary."""
    now = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0,
                                                   microsecond=0)
    return (now - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    ap.add_argument("--days", type=int, default=31,
                    help="days of daily buckets to read (max 90)")
    ap.add_argument("--min-drop", type=float, default=0.15,
                    help="fall in cache-read share, in share points, that counts "
                         "as a step")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key "
                  "(sk-ant-admin...); a workspace key cannot read "
                  "/v1/organizations/")
        return 2

    days = max(14, min(int(args.days), 90))
    session = requests.Session()
    session.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    buckets = read_buckets(session, "/organizations/usage_report/messages", {
        "starting_at": window_start(days),
        "bucket_width": "1d",
        "limit": days + 1,
        "group_by[]": ["model"],
    })

    rows = daily_rows(buckets)
    if not rows:
        log.info("no messages usage in the last %d day(s)", days)
        return 0

    state, detail = classify(rows, min_drop=args.min_drop)
    line = "%-32s %s" % (state, detail)

    if state in FINDINGS:
        log.warning(line)
        arrivals = arrival_positions(rows)
        ranked = sorted(arrivals.items(),
                        key=lambda item: input_share_after(rows, item[0], item[1]) or 0.0,
                        reverse=True)
        model, position = ranked[0]
        for repair in repair_lines(previous_model(rows, position), model):
            log.warning("  repair: %s", repair)
        log.warning("  note: this is an organization-wide ratio. A second "
                    "workload that changed on the same day would be folded into "
                    "it, so line the date up against a deploy before acting.")
        log.info("%d day(s) checked, 1 finding(s)", len(rows))
        return 1

    note = handoff(state)
    log.info(line)
    if note:
        log.info("  %s", note)
    log.info("%d day(s) checked, 0 finding(s)", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-cache-step-after-model-switch.mjs",
"js": '''/**
 * Align a collapse in cache-read share with the day a new model id appeared.
 *
 * Read only. One GET against the Admin API, which needs an Admin API key
 * (sk-ant-admin...). A workspace key is rejected by /v1/organizations/.
 *
 * Caches are keyed per model, so the first day on a new model is cold by
 * definition and a note that fires on it is wrong. This finds the single
 * largest step down in the daily cache-read share anywhere in the window and
 * asks whether it sits where the new model id first appears. A collapse three
 * weeks either side of the switch is something else, and this says so rather
 * than taking the credit.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

/**
 * Published minimum cacheable prompt length per model family, in tokens. Used
 * only to explain a confirmed step, never to make one.
 */
export const CACHE_MINIMUMS = {
  'claude-opus-5': 512,
  'claude-fable-5': 512,
  'claude-mythos-5': 512,
  'claude-mythos-preview': 2048,
  'claude-opus-4-8': 1024,
  'claude-opus-4-7': 2048,
  'claude-opus-4-6': 4096,
  'claude-opus-4-5': 4096,
  'claude-opus-4-1': 1024,
  'claude-opus-4': 1024,
  'claude-sonnet-5': 1024,
  'claude-sonnet-4-6': 1024,
  'claude-sonnet-4-5': 1024,
  'claude-sonnet-4': 1024,
  'claude-haiku-4-5': 4096,
  'claude-haiku-3-5': 2048,
};

const FINDINGS = new Set(['collapsed-after-model-change']);

/** Read a usage field as an integer. Pure. Missing and unreadable both mean 0. */
export function readInt(value) {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/** The model's minimum cacheable prompt length. Pure. Null if unrecognised. */
export function cacheMinimum(model) {
  const name = String(model ?? '').trim().toLowerCase();
  if (!name) return null;
  let best = null;
  for (const [family, floor] of Object.entries(CACHE_MINIMUMS)) {
    if (name === family || name.startsWith(`${family}-`)) {
      if (best === null || family.length > best[0].length) best = [family, floor];
    }
  }
  return best ? best[1] : null;
}

/** Normalise a timestamp to a UTC day. Pure. Null if unreadable. */
export function dayKey(stamp) {
  if (typeof stamp === 'boolean') return null;
  if (typeof stamp === 'number' && Number.isFinite(stamp)) {
    const when = new Date(Math.trunc(stamp) * 1000);
    if (Number.isNaN(when.getTime())) return null;
    return when.toISOString().slice(0, 10);
  }
  const text = String(stamp ?? '').trim().replace(' ', 'T');
  if (text.length < 10) return null;
  const head = text.slice(0, 10);
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(head)) return null;
  return head;
}

/**
 * One row per day that carried input, sorted. Pure.
 * Days with no traffic are left out rather than zero-filled: an invented
 * zero-share weekend would be the largest step in most windows.
 */
export function dailyRows(buckets) {
  const merged = new Map();
  for (const bucket of buckets ?? []) {
    const day = dayKey(bucket?.starting_at ?? bucket?.start_time);
    if (day === null) continue;
    for (const result of bucket?.results ?? []) {
      if (!result || typeof result !== 'object') continue;
      const model = String(result.model ?? 'unknown');
      const creation = result.cache_creation ?? {};
      if (!merged.has(day)) {
        merged.set(day, { day, uncached: 0, reads: 0, writes: 0, byModel: {} });
      }
      const row = merged.get(day);
      const uncached = readInt(result.uncached_input_tokens);
      const reads = readInt(result.cache_read_input_tokens);
      const writes = readInt(creation.ephemeral_5m_input_tokens)
        + readInt(creation.ephemeral_1h_input_tokens);
      row.uncached += uncached;
      row.reads += reads;
      row.writes += writes;
      row.byModel[model] = (row.byModel[model] ?? 0) + uncached + reads + writes;
    }
  }
  const rows = [...merged.values()].filter((r) => r.uncached + r.reads > 0);
  rows.sort((a, b) => a.day.localeCompare(b.day));
  rows.forEach((row, position) => {
    row.position = position;
    row.share = row.reads / (row.reads + row.uncached);
  });
  return rows;
}

/**
 * Models that first appear after the window opens. Pure.
 * A model present on day one might have been running for a year, so its
 * arrival is an artefact of where the window starts.
 */
export function arrivalPositions(rows) {
  const first = new Map();
  for (const row of rows ?? []) {
    for (const model of Object.keys(row?.byModel ?? {})) {
      if (!first.has(model)) first.set(model, readInt(row?.position));
    }
  }
  const out = new Map();
  for (const [model, position] of first) if (position > 0) out.set(model, position);
  return out;
}

/**
 * Fraction of input on one model from a position onward. Pure. Null if idle.
 * The guard against blaming a model nobody uses: a canary on one percent of
 * traffic cannot move an organization-wide ratio.
 */
export function inputShareAfter(rows, model, position) {
  let total = 0;
  let mine = 0;
  for (const row of rows ?? []) {
    if (readInt(row?.position) < position) continue;
    for (const [name, tokens] of Object.entries(row?.byModel ?? {})) {
      total += readInt(tokens);
      if (name === model) mine += readInt(tokens);
    }
  }
  if (total <= 0) return null;
  return mine / total;
}

/**
 * The step across one position, with that day itself left out. Pure.
 * Excluding the day is the whole care here: a new model's first day is cold
 * because the cache is empty, which is correct behaviour.
 */
export function stepAt(shares, position, minSide = 3) {
  const all = [...(shares ?? [])];
  const before = all.slice(0, position);
  const after = all.slice(position + 1);
  if (before.length < minSide || after.length < minSide) return [null, null, null];
  const b = before.reduce((s, v) => s + v, 0) / before.length;
  const a = after.reduce((s, v) => s + v, 0) / after.length;
  return [b, a, b - a];
}

/**
 * The largest downward step anywhere in the series. Pure.
 * What makes the alignment claim falsifiable: without it, any window holding
 * both a new model and a decline reads as causation.
 */
export function bestSplit(shares, minSide = 3) {
  const all = [...(shares ?? [])];
  const n = all.length;
  if (n < minSide * 2) return [null, null];
  let bestPosition = null;
  let bestDelta = null;
  for (let position = minSide; position <= n - minSide; position += 1) {
    const b = all.slice(0, position).reduce((s, v) => s + v, 0) / position;
    const a = all.slice(position).reduce((s, v) => s + v, 0) / (n - position);
    const delta = b - a;
    if (bestDelta === null || delta > bestDelta) {
      bestPosition = position;
      bestDelta = delta;
    }
  }
  return [bestPosition, bestDelta];
}

/** True when every day after the switch sits below every day before. Pure. */
export function sustained(shares, position, minSide = 3) {
  const all = [...(shares ?? [])];
  const before = all.slice(0, position);
  const after = all.slice(position + 1);
  if (before.length < minSide || after.length < minSide) return false;
  return Math.max(...after) < Math.min(...before);
}

/** Why the share might not come back, when the floors explain it. Pure. */
export function floorNote(oldModel, newModel) {
  const oldFloor = cacheMinimum(oldModel);
  const newFloor = cacheMinimum(newModel);
  if (oldFloor === null || newFloor === null) return '';
  if (newFloor > oldFloor) {
    return `${newModel} needs ${newFloor} tokens before a prefix is cacheable `
      + `and ${oldModel} needed ${oldFloor}, so a prompt that has not changed `
      + 'can have stopped qualifying. That is the '
      + 'prompt-below-model-cache-minimum note, and it is the most likely '
      + 'mechanism here.';
  }
  return `${newModel} has the same or a lower cache minimum (${newFloor}) as `
    + `${oldModel} (${oldFloor}), so the floor does not explain this. Look at `
    + 'thinking or effort defaults and at the tokenizer instead.';
}

/** Which note owns this shape, when it is not this one. Pure. */
export function handoff(state) {
  if (state === 'no-new-model') {
    return 'no model id appeared for the first time in this window, so nothing '
      + 'here can be attributed to a switch. If the share is low, read '
      + 'cache-invalidated-by-changing-prefix and prompt-caching-never-used.';
  }
  if (state === 'step-elsewhere') {
    return 'the largest step in the series is not where the new model arrived, '
      + 'so something else changed on that day. Read the '
      + 'cache-invalidated-by-changing-prefix note and line the step up against '
      + 'your deploys.';
  }
  if (state === 'expected-cold-start') {
    return 'the share dropped on the switch day and came back. That is a cold '
      + 'cache filling up, which is what a model change is supposed to cost, '
      + 'and it is not a finding.';
  }
  return '';
}

/** Classify one window. Pure. Returns [state, detail]. */
export function classify(rows, minDays = 14, minDrop = 0.15, ratioFloor = 0.6,
                         minMigration = 0.20, minSide = 3) {
  const all = rows ?? [];
  if (all.length < minDays) {
    return ['too-few-days',
      `${all.length} day(s) with input in the window, under the floor of ${minDays}`];
  }

  const shares = all.map((r) => r.share);
  const arrivals = arrivalPositions(all);
  if (arrivals.size === 0) {
    return ['no-new-model', 'every model id in this window was already present on day one'];
  }

  const ranked = [...arrivals.entries()].sort(
    (a, b) => (inputShareAfter(all, b[0], b[1]) ?? 0) - (inputShareAfter(all, a[0], a[1]) ?? 0));
  const [model, position] = ranked[0];
  const migration = inputShareAfter(all, model, position) ?? 0;
  if (migration < minMigration) {
    return ['new-model-marginal',
      `${model} arrived on ${all[position].day} but carries only `
      + `${(migration * 100).toFixed(0)}% of input since, under the floor of `
      + `${(minMigration * 100).toFixed(0)}%. Too small to move the ratio.`];
  }

  const [before, after, delta] = stepAt(shares, position, minSide);
  if (delta === null) {
    return ['window-too-short-around-the-switch',
      `${model} arrived on ${all[position].day} with fewer than ${minSide} day(s) `
      + 'either side of it'];
  }

  // Alignment before magnitude, and only against a step that is material on
  // its own: a big fall elsewhere disqualifies the switch outright.
  const [peak, peakDelta] = bestSplit(shares, minSide);
  if (peak !== null && peakDelta !== null && peakDelta >= minDrop
      && Math.abs(peak - position) > 1) {
    return ['step-elsewhere',
      `the share falls hardest at ${all[peak].day}, not at the ${model} switch `
      + `on ${all[position].day}`];
  }

  if (delta < minDrop || after > before * ratioFloor) {
    if (before - shares[position] >= minDrop) {
      return ['expected-cold-start',
        `${model} arrived on ${all[position].day}, the share dipped to `
        + `${(shares[position] * 100).toFixed(0)}% that day and settled back at `
        + `${(after * 100).toFixed(0)}% against ${(before * 100).toFixed(0)}% before`];
    }
    return ['steady',
      `${model} arrived on ${all[position].day} and the share held at `
      + `${(after * 100).toFixed(0)}% against ${(before * 100).toFixed(0)}% before`];
  }

  if (peak === null || Math.abs(peak - position) > 1) {
    return ['step-elsewhere',
      `the share falls hardest at ${peak === null ? 'no single day' : all[peak].day}, `
      + `not at the ${model} switch on ${all[position].day}`];
  }

  if (!sustained(shares, position, minSide)) {
    return ['partial-recovery',
      `${(before * 100).toFixed(0)}% before the ${model} switch and `
      + `${(after * 100).toFixed(0)}% after, but some days since have recovered `
      + 'above the pre-switch floor. Suggestive and not conclusive: widen the window.'];
  }

  return ['collapsed-after-model-change',
    `cache-read share ${(before * 100).toFixed(0)}% before ${model} arrived on `
    + `${all[position].day} and ${(after * 100).toFixed(0)}% after, with the `
    + `switch day itself excluded. ${model} now carries `
    + `${(migration * 100).toFixed(0)}% of input and the largest step in the `
    + 'window is exactly there.'];
}

/** The model carrying the most input before the switch. Pure. */
export function previousModel(rows, position) {
  const totals = new Map();
  for (const row of rows ?? []) {
    if (readInt(row?.position) >= position) continue;
    for (const [name, tokens] of Object.entries(row?.byModel ?? {})) {
      totals.set(name, (totals.get(name) ?? 0) + readInt(tokens));
    }
  }
  if (totals.size === 0) return null;
  return [...totals.entries()].reduce((a, b) => (a[1] >= b[1] ? a : b))[0];
}

/** What to check about the new model, in the order that pays. Pure. */
export function repairLines(oldModel, newModel) {
  const lines = [];
  const note = floorNote(oldModel, newModel);
  if (note) lines.push(note);
  lines.push(
    "compare the two models' minimum cacheable token counts and move the "
    + 'cache_control breakpoint so the prefix clears the higher one.',
    'compare their thinking and effort defaults. Those are model-specific and '
    + 'they sit inside the cached prefix, so a different default is a different prefix.',
    'count the prefix again under the new model id. A newer tokenizer can '
    + 'produce materially more tokens for the same text, which moves a prefix '
    + 'that used to sit just above a boundary.',
    'then re-measure the cache-read share over the following three days, not '
    + 'the following one. The first day after any breakpoint change is cold for '
    + 'the same reason the switch day was.',
  );
  return lines;
}

function windowStart(days) {
  const now = new Date();
  now.setUTCHours(0, 0, 0, 0);
  return `${new Date(now.getTime() - days * 86400000).toISOString().slice(0, 19)}Z`;
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
    throw new Error(`${res.status} from Anthropic: /v1/organizations/ needs an `
                    + 'Admin API key (sk-ant-admin...), not a workspace key');
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
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); '
                  + 'a workspace key cannot read /v1/organizations/');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(14, Math.min(Number(process.env.DAYS ?? 31), 90));
  const minDrop = Number(process.env.MIN_DROP ?? 0.15);

  const buckets = [];
  for await (const bucket of readBuckets(admin, '/organizations/usage_report/messages', {
    starting_at: windowStart(days),
    bucket_width: '1d',
    limit: days + 1,
    'group_by[]': ['model'],
  })) buckets.push(bucket);

  const rows = dailyRows(buckets);
  if (rows.length === 0) {
    console.log(`no messages usage in the last ${days} day(s)`);
    return;
  }

  const [state, detail] = classify(rows, 14, minDrop);
  const line = `${state.padEnd(32)} ${detail}`;

  if (FINDINGS.has(state)) {
    console.warn(line);
    const arrivals = arrivalPositions(rows);
    const ranked = [...arrivals.entries()].sort(
      (a, b) => (inputShareAfter(rows, b[0], b[1]) ?? 0)
              - (inputShareAfter(rows, a[0], a[1]) ?? 0));
    const [model, position] = ranked[0];
    for (const repair of repairLines(previousModel(rows, position), model)) {
      console.warn(`  repair: ${repair}`);
    }
    console.warn('  note: this is an organization-wide ratio. A second workload '
                 + 'that changed on the same day would be folded into it, so '
                 + 'line the date up against a deploy before acting.');
    console.log(`${rows.length} day(s) checked, 1 finding(s)`);
    process.exitCode = 1;
    return;
  }

  const note = handoff(state);
  console.log(line);
  if (note) console.log(`  ${note}`);
  console.log(`${rows.length} day(s) checked, 0 finding(s)`);
  process.exitCode = 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two fixtures are identical for the first sixteen days and differ only in what happens on day seventeen. Both run Opus 5 at a seventy per cent cache-read share for a fortnight, both switch to Haiku 4.5, and both dip to twenty per cent on the switch day. One stays down and one comes back, and they get opposite verdicts &mdash; which is the entire argument for deleting the switch day from the comparison. Around them: a collapse five days after an arrival but fifteen days before its own changepoint, which fails the alignment test outright; a canary model on three per cent of input, which is never allowed to be the cause; and a window whose every model id was already present on day one, where no claim is available at all.",
"test_py_file": "test_anthropic_cache_step_after_model_switch.py",
"test_py": '''from anthropic_cache_step_after_model_switch import (arrival_positions,
                                                     best_split, cache_minimum,
                                                     classify, daily_rows,
                                                     day_key, floor_note,
                                                     handoff, input_share_after,
                                                     previous_model,
                                                     repair_lines, step_at,
                                                     sustained)

OLD = "claude-opus-5"
NEW = "claude-haiku-4-5-20251001"


def day(position, share, models):
    """One day of the org-wide report. models maps id to input tokens."""
    total = sum(models.values())
    reads = int(round(total * share))
    return {"day": "2026-08-%02d" % (position + 1), "position": position,
            "share": share, "reads": reads, "uncached": total - reads,
            "writes": 0, "by_model": dict(models)}


def switched(before=0.70, cold=0.20, after=0.10, at=15, new_share=1.0,
             days=31):
    """A migration on day `at`, with the new model taking `new_share` of input."""
    rows = []
    for position in range(days):
        if position < at:
            rows.append(day(position, before, {OLD: 40_000_000}))
        else:
            mix = {NEW: int(40_000_000 * new_share)}
            if new_share < 1.0:
                mix[OLD] = 40_000_000 - mix[NEW]
            rows.append(day(position, cold if position == at else after, mix))
    return rows


STEP = switched()


def test_the_step_aligned_with_the_arrival_is_the_finding():
    # The note in one assertion. The switch day itself is thrown away, because
    # a cold cache on day one of a new model is correct behaviour.
    assert arrival_positions(STEP) == {NEW: 15}
    assert round(input_share_after(STEP, NEW, 15), 3) == 1.0

    shares = [r["share"] for r in STEP]
    before, after, delta = step_at(shares, 15)
    assert round(before, 2) == 0.70 and round(after, 2) == 0.10
    assert round(delta, 2) == 0.60
    assert best_split(shares)[0] == 15
    assert sustained(shares, 15) is True

    state, detail = classify(STEP)
    assert state == "collapsed-after-model-change"
    assert "70% before claude-haiku-4-5-20251001 arrived on 2026-08-16" in detail
    assert "10% after, with the switch day itself excluded" in detail
    assert "largest step in the window is exactly there" in detail
    assert handoff(state) == ""


def test_a_dip_that_recovers_is_the_cold_cache_doing_its_job():
    # Identical arrival, identical switch-day dip, opposite verdict. This is
    # the case that excluding the switch day exists for.
    recovered = switched(before=0.70, cold=0.20, after=0.70)
    assert [r["share"] for r in recovered][15] == 0.20
    state, detail = classify(recovered)
    assert state == "expected-cold-start"
    assert "dipped to 20% that day and settled back at 70%" in detail
    assert "not a finding" in handoff(state)


def test_a_collapse_somewhere_else_is_not_the_switch():
    # The new model arrives on day 5 and the share holds for another fortnight
    # before falling off a cliff. Alignment is what makes the claim falsifiable.
    rows = []
    for position in range(31):
        models = {OLD: 40_000_000} if position < 5 else {NEW: 40_000_000}
        rows.append(day(position, 0.70 if position < 20 else 0.10, models))
    shares = [r["share"] for r in rows]
    assert arrival_positions(rows) == {NEW: 5}
    assert best_split(shares)[0] == 20

    state, detail = classify(rows)
    assert state == "step-elsewhere"
    assert "falls hardest at 2026-08-21" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)


def test_a_canary_model_is_never_blamed():
    # A new id carrying three percent of input cannot move an org-wide ratio,
    # and letting it take the blame points at the wrong deploy.
    rows = switched(new_share=0.03)
    assert round(input_share_after(rows, NEW, 15), 2) == 0.03
    state, detail = classify(rows)
    assert state == "new-model-marginal"
    assert "carries only 3% of input since" in detail


def test_a_window_with_no_new_model_makes_no_claim():
    rows = [day(p, 0.70 if p < 15 else 0.10, {OLD: 40_000_000}) for p in range(31)]
    assert arrival_positions(rows) == {}
    state, detail = classify(rows)
    assert state == "no-new-model"
    assert "already present on day one" in detail
    assert "cache-invalidated-by-changing-prefix" in handoff(state)


def test_a_share_that_holds_across_the_switch_is_steady():
    state, detail = classify(switched(before=0.70, cold=0.70, after=0.70))
    assert state == "steady"
    assert "held at 70% against 70% before" in detail


def test_a_recovery_after_the_step_is_only_suggestive():
    rows = switched()
    rows[28]["share"] = 0.90
    state, detail = classify(rows)
    assert state == "partial-recovery"
    assert "recovered above the pre-switch floor" in detail
    assert sustained([r["share"] for r in rows], 15) is False


def test_the_floors_explain_the_step_without_making_it():
    assert cache_minimum(NEW) == 4096
    assert cache_minimum(OLD) == 512
    note = floor_note(OLD, NEW)
    assert "needs 4096 tokens" in note
    assert "prompt-below-model-cache-minimum" in note
    # A move to a lower floor gets the opposite sentence, not silence.
    other = floor_note("claude-haiku-4-5", "claude-opus-5")
    assert "does not explain this" in other
    assert floor_note(OLD, "gpt-5.6") == ""
    assert any("thinking" in line for line in repair_lines(OLD, NEW))


def test_the_report_is_folded_into_days_and_models():
    buckets = []
    for position in range(31):
        model = OLD if position < 15 else NEW
        share = 0.70 if position < 15 else (0.20 if position == 15 else 0.10)
        total = 40_000_000
        reads = int(total * share)
        buckets.append({"starting_at": "2026-08-%02dT00:00:00Z" % (position + 1),
                        "results": [{"model": model,
                                     "uncached_input_tokens": total - reads,
                                     "cache_read_input_tokens": reads,
                                     "cache_creation": {
                                         "ephemeral_5m_input_tokens": 0,
                                         "ephemeral_1h_input_tokens": 0}}]})
    rows = daily_rows(buckets)
    assert len(rows) == 31
    assert [r["position"] for r in rows] == list(range(31))
    assert round(rows[0]["share"], 2) == 0.70
    assert previous_model(rows, 15) == OLD
    assert classify(rows)[0] == "collapsed-after-model-change"


def test_thin_and_unreadable_windows_produce_no_verdict():
    assert classify([day(p, 0.5, {OLD: 1000}) for p in range(5)])[0] == "too-few-days"
    assert classify([])[0] == "too-few-days"
    assert classify(None)[0] == "too-few-days"
    assert step_at([0.1, 0.2], 1) == (None, None, None)
    assert best_split([0.1, 0.2]) == (None, None)
    assert sustained([], 3) is False
    assert input_share_after([], OLD, 0) is None
    assert previous_model([], 3) is None
    assert day_key("nonsense") is None
    assert daily_rows([{"starting_at": "bad", "results": []}]) == []
''',
"test_js_file": "anthropic-cache-step-after-model-switch.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { arrivalPositions, bestSplit, cacheMinimum, classify, dailyRows, dayKey,
         floorNote, handoff, inputShareAfter, previousModel, repairLines,
         stepAt, sustained }
  from './anthropic-cache-step-after-model-switch.mjs';

const OLD = 'claude-opus-5';
const NEW = 'claude-haiku-4-5-20251001';

const day = (position, share, models) => {
  const total = Object.values(models).reduce((s, v) => s + v, 0);
  const reads = Math.round(total * share);
  return { day: `2026-08-${String(position + 1).padStart(2, '0')}`, position,
           share, reads, uncached: total - reads, writes: 0,
           byModel: { ...models } };
};

const switched = ({ before = 0.70, cold = 0.20, after = 0.10, at = 15,
                    newShare = 1.0, days = 31 } = {}) => {
  const rows = [];
  for (let position = 0; position < days; position += 1) {
    if (position < at) {
      rows.push(day(position, before, { [OLD]: 40000000 }));
    } else {
      const mix = { [NEW]: Math.trunc(40000000 * newShare) };
      if (newShare < 1.0) mix[OLD] = 40000000 - mix[NEW];
      rows.push(day(position, position === at ? cold : after, mix));
    }
  }
  return rows;
};

const STEP = switched();

test('the step aligned with the arrival is the finding', () => {
  assert.deepEqual([...arrivalPositions(STEP)], [[NEW, 15]]);
  assert.equal(Number(inputShareAfter(STEP, NEW, 15).toFixed(3)), 1);

  const shares = STEP.map((r) => r.share);
  const [before, after, delta] = stepAt(shares, 15);
  assert.equal(Number(before.toFixed(2)), 0.70);
  assert.equal(Number(after.toFixed(2)), 0.10);
  assert.equal(Number(delta.toFixed(2)), 0.60);
  assert.equal(bestSplit(shares)[0], 15);
  assert.equal(sustained(shares, 15), true);

  const [state, detail] = classify(STEP);
  assert.equal(state, 'collapsed-after-model-change');
  assert.match(detail, /70% before claude-haiku-4-5-20251001 arrived on 2026-08-16/);
  assert.match(detail, /10% after, with the switch day itself excluded/);
  assert.match(detail, /largest step in the window is exactly there/);
  assert.equal(handoff(state), '');
});

test('a dip that recovers is the cold cache doing its job', () => {
  const recovered = switched({ after: 0.70 });
  assert.equal(recovered.map((r) => r.share)[15], 0.20);
  const [state, detail] = classify(recovered);
  assert.equal(state, 'expected-cold-start');
  assert.match(detail, /dipped to 20% that day and settled back at 70%/);
  assert.match(handoff(state), /not a finding/);
});

test('a collapse somewhere else is not the switch', () => {
  const rows = [];
  for (let position = 0; position < 31; position += 1) {
    const models = position < 5 ? { [OLD]: 40000000 } : { [NEW]: 40000000 };
    rows.push(day(position, position < 20 ? 0.70 : 0.10, models));
  }
  const shares = rows.map((r) => r.share);
  assert.deepEqual([...arrivalPositions(rows)], [[NEW, 5]]);
  assert.equal(bestSplit(shares)[0], 20);

  const [state, detail] = classify(rows);
  assert.equal(state, 'step-elsewhere');
  assert.match(detail, /falls hardest at 2026-08-21/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
});

test('a canary model is never blamed', () => {
  const rows = switched({ newShare: 0.03 });
  assert.equal(Number(inputShareAfter(rows, NEW, 15).toFixed(2)), 0.03);
  const [state, detail] = classify(rows);
  assert.equal(state, 'new-model-marginal');
  assert.match(detail, /carries only 3% of input since/);
});

test('a window with no new model makes no claim', () => {
  const rows = Array.from({ length: 31 },
    (_, p) => day(p, p < 15 ? 0.70 : 0.10, { [OLD]: 40000000 }));
  assert.equal(arrivalPositions(rows).size, 0);
  const [state, detail] = classify(rows);
  assert.equal(state, 'no-new-model');
  assert.match(detail, /already present on day one/);
  assert.match(handoff(state), /cache-invalidated-by-changing-prefix/);
});

test('a share that holds across the switch is steady', () => {
  const [state, detail] = classify(switched({ cold: 0.70, after: 0.70 }));
  assert.equal(state, 'steady');
  assert.match(detail, /held at 70% against 70% before/);
});

test('a recovery after the step is only suggestive', () => {
  const rows = switched();
  rows[28].share = 0.90;
  const [state, detail] = classify(rows);
  assert.equal(state, 'partial-recovery');
  assert.match(detail, /recovered above the pre-switch floor/);
  assert.equal(sustained(rows.map((r) => r.share), 15), false);
});

test('the floors explain the step without making it', () => {
  assert.equal(cacheMinimum(NEW), 4096);
  assert.equal(cacheMinimum(OLD), 512);
  const note = floorNote(OLD, NEW);
  assert.match(note, /needs 4096 tokens/);
  assert.match(note, /prompt-below-model-cache-minimum/);
  assert.match(floorNote('claude-haiku-4-5', 'claude-opus-5'), /does not explain this/);
  assert.equal(floorNote(OLD, 'gpt-5.6'), '');
  assert.ok(repairLines(OLD, NEW).some((l) => l.includes('thinking')));
});

test('the report is folded into days and models', () => {
  const buckets = Array.from({ length: 31 }, (_, position) => {
    const model = position < 15 ? OLD : NEW;
    const share = position < 15 ? 0.70 : (position === 15 ? 0.20 : 0.10);
    const total = 40000000;
    const reads = Math.trunc(total * share);
    return { starting_at: `2026-08-${String(position + 1).padStart(2, '0')}T00:00:00Z`,
             results: [{ model, uncached_input_tokens: total - reads,
                         cache_read_input_tokens: reads,
                         cache_creation: { ephemeral_5m_input_tokens: 0,
                                           ephemeral_1h_input_tokens: 0 } }] };
  });
  const rows = dailyRows(buckets);
  assert.equal(rows.length, 31);
  assert.deepEqual(rows.map((r) => r.position), Array.from({ length: 31 }, (_, i) => i));
  assert.equal(Number(rows[0].share.toFixed(2)), 0.70);
  assert.equal(previousModel(rows, 15), OLD);
  assert.equal(classify(rows)[0], 'collapsed-after-model-change');
});

test('thin and unreadable windows produce no verdict', () => {
  const thin = Array.from({ length: 5 }, (_, p) => day(p, 0.5, { [OLD]: 1000 }));
  assert.equal(classify(thin)[0], 'too-few-days');
  assert.equal(classify([])[0], 'too-few-days');
  assert.equal(classify(null)[0], 'too-few-days');
  assert.deepEqual(stepAt([0.1, 0.2], 1), [null, null, null]);
  assert.deepEqual(bestSplit([0.1, 0.2]), [null, null]);
  assert.equal(sustained([], 3), false);
  assert.equal(inputShareAfter([], OLD, 0), null);
  assert.equal(previousModel([], 3), null);
  assert.equal(dayKey('nonsense'), null);
  assert.deepEqual(dailyRows([{ starting_at: 'bad', results: [] }]), []);
});
''',
"faq": [
 ("Is a drop on the day of the switch a problem?",
  "No, and treating it as one is the mistake this note is built around. Caches are keyed per model, so the day you switch you have no warm entries and every call writes. That is the documented cost of a migration and it should recover within a day or two. The script removes the switch day from both sides of the comparison entirely and reports it separately as context. A dip that recovers gets its own verdict that says, in as many words, this is not a finding."),
 ("Why check the largest step in the whole window?",
  "Because otherwise the check cannot be wrong. Take any month containing a model migration and a rise in cost, look only at the migration date, and you will find a story. Computing the biggest downward step at every split point and requiring it to land on the arrival makes the claim refutable: if the share actually fell off a cliff two weeks later, the script names that date instead and tells you to line it up against your deploys. Most of the value of this note is in the cases where it declines to blame the model."),
 ("What actually causes the share not to come back?",
  "Three things, in rough order of likelihood. The new model's minimum cacheable prompt length may be higher, and the jump is not subtle: 512 tokens on Opus 5, 4,096 on Opus 4.6, Opus 4.5 and Haiku 4.5. Thinking and effort parameters have model-specific defaults and they sit inside the cached prefix, so a default that differs is a prefix that differs. And a newer tokenizer can produce materially more tokens for the same text, which can push a prefix across a boundary in either direction."),
 ("How does this differ from the cache minimum note?",
  "That note is the mechanism and this one is the event. It looks across models on one key at a single moment and brackets the prefix between two floors; it will find a route that has never cached on a given model regardless of when that started. This one looks along time at an organization-wide ratio and finds the day it changed. When the finding here is confirmed and the new model's floor is higher, the script points straight at that note by name, because the repair lives there."),
 ("Can this fire on something other than a model change?",
  "It can be confounded, and the output warns about it. The ratio is organization-wide and the report carries no request count, so a second workload that changed its prompt on the same day is folded into the same number. Two guards limit the damage: the new model must carry at least a fifth of input, and the largest step in the window must be at the arrival rather than somewhere else. What comes out is a date and a magnitude, which is exactly enough to check against a deploy log and deliberately not enough to skip doing so."),
],
"related": [REL_FLOOR, REL_ALIAS, REL_CACHE_NEVER],
"citations": [CITE_CL_CACHING, CITE_CL_USAGE_REPORT, CITE_CL_USAGE_API, CITE_CL_MODELS],
},
]
