#!/usr/bin/env python3
"""/llm/ field notes, batch Q — the writing.

Four safety and compliance settings the API says are not configured. The
hazard in a batch like this is that every note wants to collapse into advice,
and advice is not what this section sells. So each of the four had to produce a
finding that is a fact about your organization at a timestamp rather than a
maxim: a usage report that reads zero on a product taking public input, a
project whose retention type resolves to something other than what the
questionnaire said, a permission policy that exists and has never excluded
anything, and an encryption key config the API itself describes as inert.

`moderation-never-called` is the only one of the four that reads a usage report
rather than a policy object, and it is deliberately the one that never calls
the thing it is auditing. Proving the moderations endpoint works by sending it
content would be generating, so the script does not, and the finding is instead
a comparison between two request counts the organization already has. The
second half of it is better than the first: requests still attributed to a
`text-moderation-*` id are moderation that is running, was written before
`omni-moderation-latest` existed, and never reads the image half of a product
that now takes images.

`zero-data-retention-not-configured` is a two-level read whose whole value is
in the resolution step. The organization has a default and each project can
override it or inherit it, so the honest question is not "is ZDR on" but "what
does this project resolve to, and did anything on the project pin it there".
A project sitting at `organization_default` while the org default is a ZDR
variant is compliant today and unpinned, which is a different sentence from
either "compliant" or "broken". The script refuses to invent a total order over
the six type values; it takes the posture you claim as a parameter and reports
which projects fail to meet it, because ranking `enhanced_modified_abuse_
monitoring` against `zero_data_retention` is a legal question and not an
arithmetic one.

`project-model-permissions-unrestricted` had to stay off a published note that
already owns model choice by workload. That note reads what was called; this
one reads whether anything would have stopped it. The distinction is carried in
the code: the script never says a model was the wrong choice, and the state it
cares most about is a policy object that exists, appears configured in the
console, and excludes nothing — `mode: "deny_list"` with an empty `model_ids`.
A project with no policy at all and a project with an empty deny list are the
same reachability and two different repairs, because only one of them looks
configured to the person who set it.

`external-key-config-unattached` is the narrowest surface in the section and
the one worth being careful about. It is real: `GET /v1/organizations/
external_keys` is in Anthropic's published SDK surface, the attachment
discriminator carries exactly `attached` and `unattached`, and a workspace
carries `external_key_id` and a `data_residency` block. It is also beta, gated
on CMEK being enabled for the organization, and the attachment object carries
nothing but its own type — no workspace list. So the script reconciles two
listings that paginate differently and says out loud which of them is
authoritative for which half of the question.

Read only throughout. Every request in this batch is a GET, no script
constructs a request body, and the two write calls that exist on these surfaces
— the moderations endpoint and the external key validate call — are named in
the output and deliberately not used. No key value, KMS credential or secret is
printed; AWS account ids inside an ARN are masked.
"""

CITE_OA_MODERATION = ("Moderation — OpenAI platform docs",
                      "https://platform.openai.com/docs/guides/moderation")
CITE_OA_USAGE = ("Usage and costs — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/usage")
CITE_OA_ADMIN_GUIDE = ("Admin APIs — OpenAI platform docs",
                       "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_OA_SDK = ("openai-python admin API surface",
               "https://github.com/openai/openai-python/blob/main/api.md")
CITE_OA_YOUR_DATA = ("Your data — OpenAI platform docs",
                     "https://platform.openai.com/docs/guides/your-data")
CITE_OA_PROJECTS = ("Projects — OpenAI API reference",
                    "https://platform.openai.com/docs/api-reference/projects")
CITE_OA_MODELS = ("Models — OpenAI platform docs",
                  "https://platform.openai.com/docs/models")
CITE_CL_EXTERNAL_KEYS = ("List external keys — Claude Admin API",
                         "https://platform.claude.com/docs/en/api/admin/external_keys/list")
CITE_CL_ADMIN = ("Admin API — Claude Docs",
                 "https://platform.claude.com/docs/en/manage-claude/admin-api")
CITE_CL_WORKSPACES = ("List workspaces — Claude Admin API",
                      "https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces")
CITE_CL_SDK = ("anthropic-sdk-python admin API surface",
               "https://github.com/anthropics/anthropic-sdk-python/blob/main/api.md")

REL_MODERATION = ("/llm/moderation-never-called/",
                  "The other safety control the usage report says nothing calls")
REL_RETENTION = ("/llm/zero-data-retention-not-configured/",
                 "The retention posture each project actually resolves to")
REL_MODELPERM = ("/llm/project-model-permissions-unrestricted/",
                 "Whether any policy would have stopped the call")
REL_CMEK = ("/llm/external-key-config-unattached/",
            "An encryption config the API itself describes as inert")
REL_REFUSAL = ("/llm/refusal-field-ignored/",
               "The model's own refusal, which is not a moderation decision")
REL_ZERO_BUCKETS = ("/llm/live-project-zero-usage-buckets/",
                    "A usage report reading zero for a much duller reason")
REL_FRONTIER = ("/llm/frontier-model-on-trivial-workload/",
                "The spending pattern this policy is the structural answer to")
REL_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                   "The ceiling that is missing rather than empty")
REL_WEBSEARCH = ("/llm/web-search-spend-unnoticed/",
                 "What a hosted tool costs once something starts calling it")
REL_ARCHIVED = ("/llm/archived-project-still-holds-keys/",
                "A container that stops being listed and keeps working")
REL_GEO = ("/llm/us-inference-geo-premium-unnoticed/",
           "The other reading of a geography field nobody set deliberately")
REL_NULL_WS = ("/llm/default-workspace-cost-unattributable/",
               "The Anthropic workspace read from the cost report instead")

GUIDES = [
{
"slug": "moderation-never-called",
"title": "Nothing has ever called the free moderation endpoint",
"description": "Compare the moderations usage report against completions. Zero moderation requests on a public product is one finding; a retired text-moderation-* id the other.",
"h1": "Nothing has ever called the free moderation endpoint",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai moderation endpoint never called",
             "openai organization usage moderations",
             "omni-moderation-latest vs text-moderation-latest",
             "openai moderation coverage audit",
             "text-moderation-007 retired model id"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because both /v1/organization/usage/* endpoints reject a project key.",
"lead": "The product takes free text from anyone with the link and has done since launch. Nobody thinks of it as a moderation problem, because nothing has gone wrong yet and the model refuses most of what it should refuse on its own. Then a support ticket arrives with a screenshot, and somebody asks the only question that matters in the first ten minutes: what do we already screen? The honest answer takes an afternoon to establish, and it turns out to be nothing &mdash; not because anyone decided against it, but because moderation is a separate endpoint you have to go and call, and no line of code ever did.",
"short_answer": """<p>Two GETs with an <strong>organization admin key</strong>. <code>GET /v1/organization/usage/moderations?start_time={now-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=project_id&amp;group_by=model</code>, and the same query against <code>/v1/organization/usage/completions</code>. Both return buckets of results carrying <code>num_model_requests</code>. Fold them per project and compare.</p>
<p>Two findings come out of that comparison, and the second one is the better one. <strong>A project with real completion volume and no moderations bucket at all has never called the endpoint</strong> &mdash; which is the default state, because moderation is opt-in, nothing routes input through it automatically, and it is <em>free</em>, so cost was never the reason it was skipped. And <strong>a project whose moderation requests are attributed to a <code>text-moderation-*</code> model id</strong> is screening through a retired family that predates <code>omni-moderation-latest</code>, which is the current id and the only one that reads images as well as text. That one is worse than it looks on a product that started accepting uploads after the code was written.</p>
<p>The script never calls <code>POST /v1/moderations</code>. Sending content to a model to prove the model answers is generating, and nothing in this section generates. The endpoint is read entirely through the usage report the organization already has.</p>""",
"problem": """<p>Moderation is a separate endpoint, not a property of the completion. There is no flag on a chat request that turns it on, no default that screens input for you, and no error if you never call it. The safety behaviour people actually observe in testing is the model's own refusal, which is a different mechanism with a different purpose: it decides what the model will say, not what your users are allowed to send you, and it tells you nothing you can log, threshold or report on.</p>
<p>So the endpoint gets skipped, and it gets skipped for a reason that sounds better than it is: the model seems to handle it. That holds right up until the thing you needed to catch was in the input rather than the output &mdash; a user pasting something into a support widget, an image upload, a public-facing form &mdash; and at that point there is no record of the input having been assessed at all, because assessing it was never a step.</p>
<p>The retired-id half is a quieter failure with the same shape. Code written before <code>omni-moderation-latest</code> shipped calls <code>text-moderation-latest</code> or a pinned <code>text-moderation-007</code>, and it keeps working, because a moderation call with an old id still returns a verdict. What it does not do is read images. A product that added uploads two years after it added the moderation call has a screening layer that silently covers half its input surface, and nothing anywhere reports that as a gap.</p>""",
"why": """<p><strong>The zero is the finding, and the ratio is not.</strong> A completions:moderations ratio looks like it should be the measurement here and it is not a good one in either direction. It understates coverage, because one moderation request can carry an array of inputs and still counts as one <code>num_model_requests</code>. And it overstates the gap, because the completions figure includes everything &mdash; batch jobs, evaluation suites, internal tooling &mdash; none of which has user input in it at all. So the script grades the ratio as a soft signal with a name that says so, and reserves the word "finding" for the two facts that survive contact with reality: no moderation requests whatsoever against real traffic, and moderation requests on an id that no longer belongs there.</p>
<p><strong>It is free, which removes the only excuse and changes what the report should say.</strong> Almost every other note in this section ends in a trade-off, because the fix costs tokens or latency or engineering time. This one does not. The moderations endpoint bills nothing, so a report that hedges &mdash; "consider whether moderation is appropriate for your workload" &mdash; is worse than useless. The script says the round trip is the entire cost and moves on.</p>
<p><strong>Grouping by project is what makes the report actionable rather than a scold.</strong> An organization-wide zero is not interesting; a zero on the one project serving the public form, next to a non-zero on the internal one, is a work item with an owner. The usage endpoints support <code>group_by=project_id</code> and <code>group_by=model</code> together, so the same two reads produce the per-project split and the per-model split at once, and a floor on completion volume keeps a nine-request scratch project out of the list.</p>
<p><strong>What the usage report cannot tell you, it does not claim.</strong> It knows how many moderation requests were made and under which model id. It does not know whether they were made <em>before</em> the completion or after it, whether the code branched on <code>flagged</code> or logged the result and continued, or whether the input assessed was the user's or something the application generated itself. Those live in your source tree. The script reports the request counts and says which questions it is not answering.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>Both <code>/v1/organization/usage/moderations</code> and <code>/v1/organization/usage/completions</code> need <code>api.usage.read</code> on an organization admin key. A project key is rejected. The script never sends anything to a model.</p>"""},
 {"h": "Read both usage reports over the same window",
  "body": """<p><code>start_time</code> in unix seconds, <code>bucket_width=1d</code>, <code>limit=31</code> &mdash; the daily bucket cap is 31, so a 30-day window at <code>limit=30</code> quietly drops a day. Group by <code>project_id</code> and <code>model</code> together and paginate on <code>next_page</code> using the <code>page</code> parameter, which is not the <code>after</code> cursor the rest of the admin API uses.</p>"""},
 {"h": "Fold per project and set a volume floor",
  "body": """<p>Sum <code>num_model_requests</code> across every bucket for each project. Then drop projects under a completion floor, because a project with forty requests in a month is somebody's laptop and grading it teaches people to ignore the report.</p>"""},
 {"h": "Check the model ids before you check the counts",
  "body": """<p>A project can be moderating every single request and still be a finding, if those requests carry a <code>text-moderation-*</code> id. Test the ids first: a healthy ratio on a retired model is the case a count-based audit reports as fine.</p>"""},
 {"h": "Print what is knowable and name what is not",
  "body": """<p>Per project: completion requests, moderation requests, the model ids seen. The repair is <code>POST /v1/moderations</code> on user input before the completion, branching on <code>flagged</code> and logging <code>category_scores</code> rather than the boolean &mdash; printed, never performed.</p>"""},
],
"verify": """<p>Add the call, deploy, and re-read the same two reports a day later. The moderations bucket for that project should appear with a request count in the same order of magnitude as the user-facing share of its completions, and the model column should read <code>omni-moderation-latest</code>. If the count arrives but the id is still the old one, the deploy picked up an existing helper rather than the new call site.</p>
<pre><code class="language-bash">python3 openai_moderation_coverage_audit.py --days 30 --min-completions 500
# 4 project(s) over the 500 request floor, 2 finding(s)
# never-called        proj_public   41,208 completion request(s) and no moderation
#                                   request at all
#   repair: route user input through POST /v1/moderations before the completion.
#           The endpoint is free, so a round trip is the entire cost.
#   repair: branch on flagged, and log category_scores rather than the single
#           boolean, so a threshold can be tuned per category later.
# retired-model-id    proj_intake   3,904 moderation request(s), 100% of them on
#                                   text-moderation-latest
#   repair: move text-moderation-latest to omni-moderation-latest, which is
#           current and is the only moderation model that reads images.
# not graded: this report counts requests. Whether the code branched on flagged,
#             and whether the input assessed was the user's, are not in the API.</code></pre>""",
"code_intro": "Two paged GETs and five pure functions. The bucket fold, which sums <code>num_model_requests</code> per project and per model and ignores a result whose count is zero rather than creating a phantom entry for it; the retired-id test, which matches the whole <code>text-moderation</code> family by prefix so a pinned <code>-007</code> is caught alongside <code>-latest</code>; the coverage join, which keeps projects with no moderation entry at all rather than dropping them, since those are the note; the classifier, which tests the model ids before it tests any count; and the repair lines. Nothing here constructs a request body, and <code>POST /v1/moderations</code> appears only as printed text.",
"py_file": "openai_moderation_coverage_audit.py",
"py": '''"""Find an OpenAI organization whose moderation endpoint is never called.

Read only. Two paged GETs against /v1/organization/usage/moderations and
/v1/organization/usage/completions with an organization admin key. Every
request is a GET and no request body is constructed.

The script deliberately does not call the moderations endpoint to prove it
works. Sending content to a model to see what comes back is generating, and
nothing in this section generates. The finding comes entirely from two request
counts the organization already has.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_moderation_coverage_audit")

API = "https://api.openai.com/v1"
DAY = 86400

# The whole text-moderation-* family is retired: -latest, -stable and the
# pinned -006 / -007 snapshots. Matched by prefix so a pin is caught too.
RETIRED_PREFIX = "text-moderation"
CURRENT = "omni-moderation-latest"

FINDINGS = ("never-called", "retired-model-id", "thin-coverage")

# An unmoderated public surface outranks a stale model id, which outranks a
# ratio, because the ratio is the weakest of the three signals by some way.
SEVERITY = {"never-called": 0, "retired-model-id": 1, "thin-coverage": 2}


def fold(buckets, count_field="num_model_requests"):
    """{project_id: {"requests": n, "models": {id: n}}} across buckets. Pure.

    A result carrying zero requests creates no entry. That matters: the whole
    detection rests on a project being absent from the moderations fold, and a
    zero-valued row would make it present with a count of nothing.
    """
    out = {}
    for bucket in buckets or []:
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            try:
                n = int(row.get(count_field) or 0)
            except (TypeError, ValueError):
                n = 0
            if n <= 0:
                continue
            pid = str(row.get("project_id") or "unattributed")
            model = str(row.get("model") or "unknown")
            entry = out.setdefault(pid, {"requests": 0, "models": {}})
            entry["requests"] += n
            entry["models"][model] = entry["models"].get(model, 0) + n
    return out


def is_retired(model):
    """Is this a retired moderation model id? Pure. Prefix match, so pins count."""
    return str(model or "").strip().lower().startswith(RETIRED_PREFIX)


def retired_ids(models):
    """Sorted retired ids inside one {model: requests} mapping. Pure."""
    return sorted(m for m in (models or {}) if is_retired(m))


def coverage(completions, moderations):
    """[(project_id, completions, moderations, models)] busiest first. Pure.

    Driven by the completions side, so a project with no moderations entry is
    still a row. Dropping it is exactly the bug this note is about.
    """
    rows = []
    for pid, entry in (completions or {}).items():
        mod = (moderations or {}).get(pid) or {}
        rows.append((pid,
                     int((entry or {}).get("requests") or 0),
                     int(mod.get("requests") or 0),
                     dict(mod.get("models") or {})))
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


def classify(row, min_completions=500, min_ratio=0.2):
    """Classify one coverage row. Pure. Returns (state, detail).

    The model ids are tested BEFORE any count. A project can be moderating
    every request it serves and still be a finding, because a healthy ratio on
    a retired id is exactly what a count-based audit calls fine.
    """
    pid, completions, moderations, models = row
    if completions < min_completions:
        return ("below-floor",
                "%d completion request(s), under the %d floor"
                % (completions, min_completions))

    retired = retired_ids(models)
    if retired:
        share = sum(models[m] for m in retired) / float(max(1, moderations))
        return ("retired-model-id",
                "%d moderation request(s), %d%% of them on %s"
                % (moderations, round(share * 100), ", ".join(retired)))

    if moderations <= 0:
        return ("never-called",
                "%d completion request(s) and no moderation request at all"
                % completions)

    ratio = moderations / float(completions)
    if ratio < min_ratio:
        return ("thin-coverage",
                "%d moderation request(s) against %d completion request(s), a "
                "ratio of %.2f" % (moderations, completions, ratio))
    return ("covered",
            "%d moderation request(s), ratio %.2f" % (moderations, ratio))


def repair_lines(state, row):
    """The repair for one classified project. Pure. Printed, never performed."""
    pid, completions, moderations, models = row
    lines = []
    if state not in FINDINGS:
        return lines
    if state == "never-called":
        lines.append("route user input through the moderations endpoint before "
                     "the completion. It bills nothing, so a round trip is the "
                     "entire cost.")
        lines.append("branch on flagged, and log category_scores rather than the "
                     "single boolean, so a threshold can be tuned per category "
                     "later without another deploy.")
    elif state == "retired-model-id":
        lines.append("move %s to %s, which is current and is the only moderation "
                     "model that reads images as well as text."
                     % (", ".join(retired_ids(models)), CURRENT))
        lines.append("if this product accepts uploads, the retired id has been "
                     "screening the text half only.")
    else:
        lines.append("moderation is being called on a small share of the traffic. "
                     "Find the call sites that skip it before tuning anything; "
                     "the ratio alone cannot tell you which they are.")
    lines.append("re-read project %s with the same two usage reports after the "
                 "deploy, and check the model column, not only the count" % pid)
    return lines


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: the usage reports need an organization "
                         "admin key with api.usage.read, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def usage(session, path, start, end):
    """Every bucket in the window. Paginates on next_page via the page param."""
    params = {"start_time": start, "end_time": end, "bucket_width": "1d",
              "limit": 31, "group_by": ["project_id", "model"]}
    out = []
    while True:
        page = get(session, path, params)
        out.extend(page.get("data") or [])
        cursor = page.get("next_page")
        if not page.get("has_more") or not cursor:
            return out
        params = dict(params, page=cursor)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="window to read")
    ap.add_argument("--min-completions", type=int, default=500,
                    help="completion requests a project needs before it is graded")
    ap.add_argument("--min-ratio", type=float, default=0.2,
                    help="soft floor on moderations per completion")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a project "
                  "key cannot read /v1/organization/usage/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    end = int(time.time())
    start = end - max(1, args.days) * DAY

    completions = fold(usage(s, "/organization/usage/completions", start, end))
    moderations = fold(usage(s, "/organization/usage/moderations", start, end))

    rows = coverage(completions, moderations)
    graded = [(row, classify(row, args.min_completions, args.min_ratio))
              for row in rows]
    bad = [(row, state, detail) for row, (state, detail) in graded
           if state in FINDINGS]
    over_floor = sum(1 for _, (state, _) in graded if state != "below-floor")

    log.info("%d project(s) over the %d request floor, %d finding(s)",
             over_floor, args.min_completions, len(bad))

    bad.sort(key=lambda r: (SEVERITY.get(r[1], 9), -r[0][1]))
    for row, state, detail in bad:
        log.warning("%-18s %-14s %s", state, row[0], detail)
        for line in repair_lines(state, row):
            log.warning("  repair: %s", line)

    log.info("not graded: this report counts requests. Whether the code branched "
             "on flagged, and whether the input assessed was the user's, are not "
             "in the API.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-moderation-coverage-audit.mjs",
"js": '''/**
 * Find an OpenAI organization whose moderation endpoint is never called.
 *
 * Read only. Two paged GETs against /v1/organization/usage/moderations and
 * /v1/organization/usage/completions. No request body is constructed.
 *
 * The script deliberately does not call the moderations endpoint to prove it
 * works: sending content to a model is generating. The finding comes from two
 * request counts the organization already has.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;

const RETIRED_PREFIX = 'text-moderation';
const CURRENT = 'omni-moderation-latest';

const FINDINGS = new Set(['never-called', 'retired-model-id', 'thin-coverage']);
const SEVERITY = { 'never-called': 0, 'retired-model-id': 1, 'thin-coverage': 2 };

/** {project_id: {requests, models}} across buckets. Pure. Zero rows create nothing. */
export function fold(buckets, countField = 'num_model_requests') {
  const out = {};
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const n = Math.trunc(Number(result?.[countField] ?? 0));
      if (!Number.isFinite(n) || n <= 0) continue;
      const pid = String(result?.project_id ?? 'unattributed');
      const model = String(result?.model ?? 'unknown');
      const entry = (out[pid] ??= { requests: 0, models: {} });
      entry.requests += n;
      entry.models[model] = (entry.models[model] ?? 0) + n;
    }
  }
  return out;
}

/** Is this a retired moderation model id? Pure. Prefix match, so pins count. */
export function isRetired(model) {
  return String(model ?? '').trim().toLowerCase().startsWith(RETIRED_PREFIX);
}

/** Sorted retired ids inside one {model: requests} mapping. Pure. */
export function retiredIds(models) {
  return Object.keys(models ?? {}).filter(isRetired).sort();
}

/** [[project, completions, moderations, models]] busiest first. Pure. */
export function coverage(completions, moderations) {
  const rows = [];
  for (const [pid, entry] of Object.entries(completions ?? {})) {
    const mod = (moderations ?? {})[pid] ?? {};
    rows.push([pid, Math.trunc(Number(entry?.requests ?? 0)),
               Math.trunc(Number(mod.requests ?? 0)), { ...(mod.models ?? {}) }]);
  }
  rows.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return rows;
}

/** Classify one coverage row. Pure. Model ids are tested before any count. */
export function classify(row, minCompletions = 500, minRatio = 0.2) {
  const [pid, completions, moderations, models] = row;
  if (completions < minCompletions) {
    return ['below-floor',
            `${completions} completion request(s), under the ${minCompletions} floor`];
  }
  const retired = retiredIds(models);
  if (retired.length) {
    const share = retired.reduce((a, m) => a + models[m], 0) / Math.max(1, moderations);
    return ['retired-model-id',
            `${moderations} moderation request(s), ${Math.round(share * 100)}% of `
            + `them on ${retired.join(', ')}`];
  }
  if (moderations <= 0) {
    return ['never-called',
            `${completions} completion request(s) and no moderation request at all`];
  }
  const ratio = moderations / completions;
  if (ratio < minRatio) {
    return ['thin-coverage',
            `${moderations} moderation request(s) against ${completions} completion `
            + `request(s), a ratio of ${ratio.toFixed(2)}`];
  }
  return ['covered', `${moderations} moderation request(s), ratio ${ratio.toFixed(2)}`];
}

/** The repair for one classified project. Pure. Printed, never performed. */
export function repairLines(state, row) {
  const [pid, , , models] = row;
  const lines = [];
  if (!FINDINGS.has(state)) return lines;
  if (state === 'never-called') {
    lines.push('route user input through the moderations endpoint before the '
      + 'completion. It bills nothing, so a round trip is the entire cost.');
    lines.push('branch on flagged, and log category_scores rather than the single '
      + 'boolean, so a threshold can be tuned per category later without another '
      + 'deploy.');
  } else if (state === 'retired-model-id') {
    lines.push(`move ${retiredIds(models).join(', ')} to ${CURRENT}, which is `
      + 'current and is the only moderation model that reads images as well as text.');
    lines.push('if this product accepts uploads, the retired id has been screening '
      + 'the text half only.');
  } else {
    lines.push('moderation is being called on a small share of the traffic. Find '
      + 'the call sites that skip it before tuning anything; the ratio alone cannot '
      + 'tell you which they are.');
  }
  lines.push(`re-read project ${pid} with the same two usage reports after the `
    + 'deploy, and check the model column, not only the count');
  return lines;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const one of v) url.searchParams.append(k, String(one));
    else url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: the usage reports need an `
      + 'organization admin key with api.usage.read, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function usage(key, path, start, end) {
  const params = { start_time: start, end_time: end, bucket_width: '1d',
                   limit: 31, group_by: ['project_id', 'model'] };
  const out = [];
  for (;;) {
    const page = await read(key, path, params);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) return out;
    params.page = page.next_page;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key; a project '
                  + 'key cannot read /v1/organization/usage/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const minCompletions = Number(process.env.MIN_COMPLETIONS ?? 500);
  const minRatio = Number(process.env.MIN_RATIO ?? 0.2);
  const end = Math.floor(Date.now() / 1000);
  const start = end - Math.max(1, days) * DAY;

  const completions = fold(await usage(admin, '/organization/usage/completions', start, end));
  const moderations = fold(await usage(admin, '/organization/usage/moderations', start, end));

  const graded = coverage(completions, moderations)
    .map((row) => [row, classify(row, minCompletions, minRatio)]);
  const bad = graded.filter(([, [state]]) => FINDINGS.has(state));
  const overFloor = graded.filter(([, [state]]) => state !== 'below-floor').length;

  console.log(`${overFloor} project(s) over the ${minCompletions} request floor, `
              + `${bad.length} finding(s)`);

  bad.sort(([ra, [sa]], [rb, [sb]]) =>
    (SEVERITY[sa] ?? 9) - (SEVERITY[sb] ?? 9) || rb[1] - ra[1]);

  for (const [row, [state, detail]] of bad) {
    console.warn(`${state.padEnd(18)} ${row[0].padEnd(14)} ${detail}`);
    for (const line of repairLines(state, row)) console.warn(`  repair: ${line}`);
  }
  console.log('not graded: this report counts requests. Whether the code branched '
              + "on flagged, and whether the input assessed was the user's, are not "
              + 'in the API.');
  process.exitCode = bad.length ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first two tests are the note. A project with forty-one thousand completions and no moderations entry at all has to survive the join and come back as <code>never-called</code>, which is the case a fold that drops empty projects silently deletes. And a project moderating <em>every</em> request through <code>text-moderation-latest</code> has to come back as a finding rather than as coverage, because a count-based audit calls that one fine. Around them: the prefix match, so a pinned <code>text-moderation-007</code> is caught alongside <code>-latest</code> and <code>omni-moderation-latest</code> is not; the volume floor, so a scratch project is never graded; a zero-valued result row, which must not create a phantom entry; and the repair for a retired id, which has to mention images, because that is the half of the gap nobody expects.",
"test_py_file": "test_openai_moderation_coverage_audit.py",
"test_py": '''from openai_moderation_coverage_audit import (classify, coverage, fold,
                                              is_retired, repair_lines,
                                              retired_ids)

COMPLETION = "organization.usage.completions.result"
MODERATION = "organization.usage.moderations.result"


def bucket(*results):
    return {"object": "bucket", "start_time": 0, "end_time": 86400,
            "results": list(results)}


def row(project, model, n, obj=MODERATION):
    return {"object": obj, "project_id": project, "model": model,
            "num_model_requests": n, "input_tokens": n * 12}


def test_a_busy_project_with_no_moderations_entry_survives_the_join():
    # The note. proj_public never appears in the moderations report at all, so
    # a join driven by the moderation side would report nothing wrong.
    completions = fold([bucket(row("proj_public", "gpt-4.1-mini", 20604, COMPLETION),
                               row("proj_intake", "gpt-4.1", 2000, COMPLETION)),
                        bucket(row("proj_public", "gpt-4.1-mini", 20604, COMPLETION))])
    moderations = fold([bucket(row("proj_intake", "omni-moderation-latest", 1900))])

    rows = coverage(completions, moderations)
    assert [r[0] for r in rows] == ["proj_public", "proj_intake"]

    state, detail = classify(rows[0])
    assert state == "never-called"
    assert "41208 completion request(s)" in detail
    lines = repair_lines(state, rows[0])
    assert any("bills nothing" in line for line in lines)
    assert any("category_scores" in line for line in lines)

    assert classify(rows[1])[0] == "covered"


def test_full_coverage_on_a_retired_id_is_a_finding_not_coverage():
    # Every request moderated, ratio near 1.0, and still wrong. A count-based
    # audit reports this project as healthy.
    completions = fold([bucket(row("proj_old", "gpt-4.1", 4000, COMPLETION))])
    moderations = fold([bucket(row("proj_old", "text-moderation-latest", 3904))])
    rows = coverage(completions, moderations)

    state, detail = classify(rows[0])
    assert state == "retired-model-id"
    assert "100% of them on text-moderation-latest" in detail
    lines = repair_lines(state, rows[0])
    assert any("omni-moderation-latest" in line for line in lines)
    assert any("images" in line for line in lines)


def test_a_pinned_snapshot_is_caught_and_the_current_id_is_not():
    assert is_retired("text-moderation-007") is True
    assert is_retired("text-moderation-stable") is True
    assert is_retired("TEXT-MODERATION-LATEST") is True
    assert is_retired("omni-moderation-latest") is False
    assert is_retired("omni-moderation-2024-09-26") is False
    assert is_retired(None) is False
    assert retired_ids({"omni-moderation-latest": 5, "text-moderation-007": 2}) == \\
        ["text-moderation-007"]
    # A part-migrated project is still a finding, and both ids are named.
    mixed = ("proj_half", 4000, 3900,
             {"omni-moderation-latest": 3000, "text-moderation-007": 900})
    state, detail = classify(mixed)
    assert state == "retired-model-id"
    assert "23% of them" in detail


def test_a_low_volume_project_is_never_graded():
    quiet = ("proj_scratch", 41, 0, {})
    state, detail = classify(quiet)
    assert state == "below-floor"
    assert "under the 500 floor" in detail
    assert repair_lines(state, quiet) == []
    # And it becomes gradeable once the floor is lowered deliberately.
    assert classify(quiet, min_completions=10)[0] == "never-called"


def test_a_zero_valued_result_row_creates_no_entry():
    # A project present in the report with a zero count must not look moderated.
    moderations = fold([bucket(row("proj_a", "omni-moderation-latest", 0),
                               row("proj_b", "omni-moderation-latest", 7))])
    assert "proj_a" not in moderations
    assert moderations["proj_b"]["requests"] == 7
    assert fold(None) == {}
    assert fold([{"results": None}]) == {}
    assert fold([bucket({"num_model_requests": "not a number"})]) == {}
    # A result with no project_id is kept under an explicit name, not dropped.
    assert "unattributed" in fold([bucket({"num_model_requests": 3})])


def test_the_ratio_is_graded_as_the_soft_signal_it_is():
    thin = ("proj_thin", 10000, 400, {"omni-moderation-latest": 400})
    state, detail = classify(thin)
    assert state == "thin-coverage"
    assert "ratio of 0.04" in detail
    assert any("cannot tell you which" in line for line in repair_lines(state, thin))
    assert classify(thin, min_ratio=0.01)[0] == "covered"
    assert repair_lines("covered", thin) == []
''',
"test_js_file": "openai-moderation-coverage-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, coverage, fold, isRetired, repairLines, retiredIds }
  from './openai-moderation-coverage-audit.mjs';

const COMPLETION = 'organization.usage.completions.result';
const MODERATION = 'organization.usage.moderations.result';

const bucket = (...results) =>
  ({ object: 'bucket', start_time: 0, end_time: 86400, results });

const row = (project, model, n, obj = MODERATION) =>
  ({ object: obj, project_id: project, model, num_model_requests: n,
     input_tokens: n * 12 });

test('a busy project with no moderations entry survives the join', () => {
  const completions = fold([
    bucket(row('proj_public', 'gpt-4.1-mini', 20604, COMPLETION),
           row('proj_intake', 'gpt-4.1', 2000, COMPLETION)),
    bucket(row('proj_public', 'gpt-4.1-mini', 20604, COMPLETION))]);
  const moderations = fold([bucket(row('proj_intake', 'omni-moderation-latest', 1900))]);

  const rows = coverage(completions, moderations);
  assert.deepEqual(rows.map((r) => r[0]), ['proj_public', 'proj_intake']);

  const [state, detail] = classify(rows[0]);
  assert.equal(state, 'never-called');
  assert.ok(detail.includes('41208 completion request(s)'));
  const lines = repairLines(state, rows[0]);
  assert.ok(lines.some((l) => l.includes('bills nothing')));
  assert.ok(lines.some((l) => l.includes('category_scores')));

  assert.equal(classify(rows[1])[0], 'covered');
});

test('full coverage on a retired id is a finding, not coverage', () => {
  const completions = fold([bucket(row('proj_old', 'gpt-4.1', 4000, COMPLETION))]);
  const moderations = fold([bucket(row('proj_old', 'text-moderation-latest', 3904))]);
  const rows = coverage(completions, moderations);

  const [state, detail] = classify(rows[0]);
  assert.equal(state, 'retired-model-id');
  assert.ok(detail.includes('100% of them on text-moderation-latest'));
  const lines = repairLines(state, rows[0]);
  assert.ok(lines.some((l) => l.includes('omni-moderation-latest')));
  assert.ok(lines.some((l) => l.includes('images')));
});

test('a pinned snapshot is caught and the current id is not', () => {
  assert.equal(isRetired('text-moderation-007'), true);
  assert.equal(isRetired('text-moderation-stable'), true);
  assert.equal(isRetired('TEXT-MODERATION-LATEST'), true);
  assert.equal(isRetired('omni-moderation-latest'), false);
  assert.equal(isRetired('omni-moderation-2024-09-26'), false);
  assert.equal(isRetired(null), false);
  assert.deepEqual(retiredIds({ 'omni-moderation-latest': 5, 'text-moderation-007': 2 }),
                   ['text-moderation-007']);
  const mixed = ['proj_half', 4000, 3900,
                 { 'omni-moderation-latest': 3000, 'text-moderation-007': 900 }];
  const [state, detail] = classify(mixed);
  assert.equal(state, 'retired-model-id');
  assert.ok(detail.includes('23% of them'));
});

test('a low volume project is never graded', () => {
  const quiet = ['proj_scratch', 41, 0, {}];
  const [state, detail] = classify(quiet);
  assert.equal(state, 'below-floor');
  assert.ok(detail.includes('under the 500 floor'));
  assert.deepEqual(repairLines(state, quiet), []);
  assert.equal(classify(quiet, 10)[0], 'never-called');
});

test('a zero valued result row creates no entry', () => {
  const moderations = fold([bucket(row('proj_a', 'omni-moderation-latest', 0),
                                   row('proj_b', 'omni-moderation-latest', 7))]);
  assert.equal(moderations.proj_a, undefined);
  assert.equal(moderations.proj_b.requests, 7);
  assert.deepEqual(fold(null), {});
  assert.deepEqual(fold([{ results: null }]), {});
  assert.deepEqual(fold([bucket({ num_model_requests: 'not a number' })]), {});
  assert.ok('unattributed' in fold([bucket({ num_model_requests: 3 })]));
});

test('the ratio is graded as the soft signal it is', () => {
  const thin = ['proj_thin', 10000, 400, { 'omni-moderation-latest': 400 }];
  const [state, detail] = classify(thin);
  assert.equal(state, 'thin-coverage');
  assert.ok(detail.includes('ratio of 0.04'));
  assert.ok(repairLines(state, thin).some((l) => l.includes('cannot tell you which')));
  assert.equal(classify(thin, 500, 0.01)[0], 'covered');
  assert.deepEqual(repairLines('covered', thin), []);
});
''',
"faq": [
 ("Why does the script not just call the moderations endpoint to test it?",
  "Because calling it is generating, and nothing in this section generates. The moderations endpoint takes content and runs a model over it; a script that sends it a test string to prove the endpoint responds has made an inference request on a key that can make inference requests, which is exactly the line every script here refuses to cross. It costs nothing in money, which is not the point. The finding is available without it: the usage report already counts every moderation request the organization has made, per project and per model id, and that is what the script reads."),
 ("Is the completions-to-moderations ratio really meaningful?",
  "Only weakly, and the script grades it as the weak signal it is. It understates coverage because one moderation request can carry an array of inputs and still counts as a single num_model_requests. It overstates the gap because the completions figure includes batch jobs, evaluation runs and internal tooling, none of which has user input in it. So a ratio below the floor is reported under the name thin-coverage with a repair that says to go and find the call sites, rather than as a number to hit. The two states that are worth acting on are the ones that do not depend on the ratio at all: no moderation requests whatsoever, and requests on a retired model id."),
 ("What is actually wrong with text-moderation-latest? It still returns a verdict.",
  "It does, and that is why nobody notices. The text-moderation family is retired in favour of omni-moderation-latest, and the difference that bites is not the accuracy of the categories, it is that the old family reads text only. A product that added image uploads after the moderation call was written has a screening layer covering one half of its input surface, with no error and no log line anywhere saying so. The newer id also returns category_applied_input_types, which tells you which modality triggered a flag, and that is the field you want when somebody asks why a particular item was blocked."),
 ("Does Anthropic have an equivalent endpoint to audit?",
  "Not a free standalone classifier of this shape, which is why this note is written against OpenAI. Anthropic's safety behaviour is carried in the model's own refusals and in stop_reason, and its usage report has no request-count field at all, so there is nothing to compare a moderation count against even in principle. The nearest Anthropic reading is a separate question about refusals in your own traffic, and it is a different note with a different mechanism."),
 ("The report says never-called, but we do screen input with our own classifier. Is it wrong?",
  "It is right about what it measured and it does not know about your classifier. The usage report can only see requests made to OpenAI, so an in-house model, a third-party service or a rules engine is invisible to it. Read the finding as what it literally says: this project has never used the provider's moderation endpoint. If a different layer covers it, the useful follow-up is whether that layer reads images, whether it produces per-category scores you can threshold, and whether it costs anything, because the endpoint it is replacing does not."),
],
"related": [REL_REFUSAL, REL_MODELPERM, REL_ZERO_BUCKETS],
"citations": [CITE_OA_MODERATION, CITE_OA_USAGE, CITE_OA_ADMIN_GUIDE, CITE_OA_SDK],
},
{
"slug": "zero-data-retention-not-configured",
"title": "Zero data retention is claimed and no project resolves to it",
"description": "The org has a default and each project overrides or inherits it. Read both and report what each project actually resolves to, not what was negotiated.",
"h1": "Zero data retention is claimed and no project resolves to it",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai zero data retention not configured",
             "openai organization data_retention endpoint",
             "openai project data retention organization_default",
             "openai project residency EU_STORAGE_PROCESSING",
             "openai zdr audit admin api"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because /v1/organization/data_retention and the per-project retention endpoint both reject a project key.",
"lead": "The security questionnaire came back with one line highlighted. <em>Prompts and completions are not retained by the model provider.</em> Somebody wrote that eighteen months ago and it was true of the arrangement negotiated at the time, and nobody has looked since, because there is nothing to look at: no header comes back on a completion saying what the retention mode was, no field in the response, no warning in the logs. Meanwhile four projects have been created since that contract was signed, and each one started life on whatever the organization default happened to be that morning.",
"short_answer": """<p>Two levels, both read with an <strong>organization admin key</strong>. <code>GET /v1/organization/data_retention</code> returns an <code>organization.data_retention</code> object with a <code>type</code> drawn from <code>zero_data_retention</code>, <code>modified_abuse_monitoring</code>, <code>enhanced_zero_data_retention</code> and <code>enhanced_modified_abuse_monitoring</code>. Then, for every project from <code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>, <code>GET /v1/organization/projects/{project_id}/data_retention</code> returns a <code>project.data_retention</code> whose <code>type</code> is drawn from a wider set that adds <code>organization_default</code> and <code>none</code>.</p>
<p><strong>The finding is the resolution, not either level on its own.</strong> A project reading <code>organization_default</code> is not configured, it is inherited: it resolves to whatever the org says today and it moves the day the org default moves. A project reading <code>none</code> has no retention control at all regardless of what the org negotiated. Both look identical in a console list of projects, and neither is visible from any request you make.</p>
<p>Read <code>residency</code> off each project object while you are there. It is a separate axis with its own values &mdash; <code>GLOBAL</code>, <code>US_STORAGE_PROCESSING</code>, <code>EU_STORAGE_PROCESSING</code> and a list of country storage options &mdash; and a project can satisfy a retention claim while sitting in the wrong jurisdiction, or the reverse.</p>""",
"problem": """<p>Retention posture is configuration, and configuration set at two levels drifts. The organization has a default; a project can pin its own value or inherit. Nothing forces a choice at project creation, so a project created a year after the contract was signed takes whatever the default was that morning, and a change to the org default silently re-points every inheriting project underneath it.</p>
<p>What makes it invisible rather than merely unfixed is that the inference path never mentions it. There is no response header carrying the retention mode, nothing in the usage report, no warning anywhere. The only way to know is to ask the admin endpoint, and the reason nobody asks is that the answer was established once, in a contract negotiation, by people who were not going to be the ones creating projects two years later.</p>
<p>So the failure is not a setting turned off. It is a claim made in one system &mdash; a DPA, a questionnaire, a page on the trust site &mdash; that was true of the organization at a moment in time and was never a property of the project the regulated workload actually runs in.</p>""",
"why": """<p><strong>The script refuses to rank the six type values, and that refusal is deliberate.</strong> It would be easy to write a severity ladder that puts <code>enhanced_zero_data_retention</code> above <code>zero_data_retention</code> above <code>enhanced_modified_abuse_monitoring</code> and grade against it. That ladder would be an invention. Whether modified abuse monitoring satisfies a particular commitment is a question about the commitment, not about the API, and a script that answers it confidently is producing compliance theatre. So the posture you claim is a parameter: the script groups the types into families, takes the family you say you claim, and reports which projects do not reach it.</p>
<p><strong>Inherited and compliant is a third state, not a pass.</strong> A project sitting at <code>organization_default</code> while the org default is a ZDR variant is compliant right now and pinned to nothing. It is reported separately from both the compliant projects and the failing ones, because the sentence you need is different: not "fix this" and not "this is fine", but "this resolves correctly today and nothing on the project holds it there". That is the state that turns into an incident when somebody changes the org default for an unrelated reason.</p>
<p><strong><code>none</code> is not a weaker retention mode, it is the absence of one, and it must not be mistaken for an inherit.</strong> The two values sit in the same enum and read similarly at a glance. A project at <code>none</code> gets no retention control whatever the organization says, which is the opposite of inheriting, and the script gives it its own state and its own line so it can never be summarised into the same row as an inheriting project.</p>
<p><strong>The request field and the response field have different names, and the printed repair says so.</strong> Reading gives you <code>type</code>. Writing takes <code>retention_type</code>. A repair line copied from the read shape produces a 400, and the person copying it usually concludes the endpoint is broken. The script prints the correct body, and adds the caveat that matters more: ZDR and the enhanced variants generally have to be enabled on the account by OpenAI rather than being self-serve, so the action is to request it, not to set it. The audit script never executes a retention change under any flag.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>Both retention endpoints and the project listing reject a project key. The script only ever issues GETs; there is no flag that makes it write.</p>"""},
 {"h": "Read the organization default first",
  "body": """<p><code>GET /v1/organization/data_retention</code>. Its <code>type</code> is the value every inheriting project resolves to, so nothing below it can be graded until you have it.</p>"""},
 {"h": "List every project, archived ones included",
  "body": """<p><code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>, paginated on <code>after</code>. An archived project cannot take new traffic and its retained data is still retained, so it is graded and labelled rather than skipped.</p>"""},
 {"h": "Resolve each project against the default",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/data_retention</code>. Map <code>organization_default</code> onto the org's value and keep the fact that it was inherited; treat <code>none</code> as its own state; treat an unreadable or unrecognised value as unreadable rather than as safe.</p>"""},
 {"h": "Grade residency as a separate axis and print the repair",
  "body": """<p><code>residency</code> on the project object answers a different question from retention and is reported on its own line. The repair is <code>POST /v1/organization/projects/{project_id}/data_retention</code> with a <code>retention_type</code> body &mdash; printed, never performed, and annotated with the fact that the enhanced variants are requested rather than set.</p>"""},
],
"verify": """<p>Pin the projects that should be pinned, then re-run. Every row that read <code>inherited-not-pinned</code> should read <code>compliant</code> with the value now set on the project itself, and the count of projects resolving through the org default should be the ones you deliberately left inheriting. Change the org default afterwards on purpose, in a test organization if you have one, and confirm the pinned rows do not move.</p>
<pre><code class="language-bash">python3 openai_data_retention_audit.py --require zdr --residency EU_STORAGE_PROCESSING
# organization default: modified_abuse_monitoring
# 9 project(s), 4 finding(s)
# no-retention-control   proj_ingest    Ingest pipeline
#   type is none: no retention control at all, whatever the organization default says
#   repair: POST /v1/organization/projects/proj_ingest/data_retention
#           {"retention_type": "zero_data_retention"}
#   repair: the request field is retention_type; the response field is type. A body
#           copied from the read shape 400s.
# weaker-than-claimed    proj_web       Customer web app
#   resolves to modified_abuse_monitoring (inherited from the organization), and
#   zero data retention was claimed
# inherited-not-pinned   proj_eu        EU tenant
#   resolves to enhanced_zero_data_retention only because the organization default
#   says so. Nothing on the project pins it.
# residency              proj_eu        residency is US_STORAGE_PROCESSING, and
#                                       EU_STORAGE_PROCESSING was claimed</code></pre>""",
"code_intro": "One GET for the org, one paged GET for the projects, one GET per project, and six pure functions. The family map, which groups the six type values into <code>zdr</code>, <code>modified-abuse-monitoring</code> and <code>none</code> without ranking them against each other; the resolver, which returns both the effective type and whether it was inherited, because those are two different facts; the classifier, which tests unreadable before <code>none</code> before family before inheritance; the residency check, which treats a missing value as unset rather than as <code>GLOBAL</code>; the archived label; and the repair lines, which print a <code>retention_type</code> body and say out loud that the enhanced variants are requested rather than set.",
"py_file": "openai_data_retention_audit.py",
"py": '''"""Find OpenAI projects whose retention posture is not the one you claim.

Read only. One GET for the organization default, one paged GET for the project
list, and one GET per project. Every request is a GET and no request body is
constructed anywhere, including for the repair, which is printed as text.

The two levels disagree more often than anyone expects, and the interesting
answer is the resolution: what a project actually gets, and whether anything on
the project holds it there.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_data_retention_audit")

API = "https://api.openai.com/v1"

ZDR = ("zero_data_retention", "enhanced_zero_data_retention")
MAM = ("modified_abuse_monitoring", "enhanced_modified_abuse_monitoring")
INHERIT = "organization_default"
NO_CONTROL = "none"

# Families, not a ranking. Whether modified abuse monitoring satisfies a given
# commitment is a question about the commitment; the script will not answer it.
FAMILY_LABEL = {"zdr": "zero data retention",
                "modified-abuse-monitoring": "modified abuse monitoring"}

# What to write when a project has to be brought up to the claimed family. The
# enhanced variants are requested from OpenAI rather than set, and the printed
# repair says so.
TARGET = {"zdr": "zero_data_retention",
          "modified-abuse-monitoring": "modified_abuse_monitoring"}

FINDINGS = ("retention-unreadable", "no-retention-control", "weaker-than-claimed",
            "inherited-not-pinned")

SEVERITY = {"no-retention-control": 0, "weaker-than-claimed": 1,
            "retention-unreadable": 2, "inherited-not-pinned": 3}


def family(retention_type):
    """Group one type value into a family. Pure. Never ranks families."""
    t = str(retention_type or "").strip().lower()
    if not t:
        return "unreadable"
    if t in ZDR:
        return "zdr"
    if t in MAM:
        return "modified-abuse-monitoring"
    if t == NO_CONTROL:
        return "none"
    return "unrecognised"


def effective(org_type, project_type):
    """(type, inherited) for one project. Pure.

    organization_default is the whole reason this function exists: the project
    reports a word rather than a posture, and the posture is one level up.
    """
    t = str(project_type or "").strip().lower()
    if not t:
        return (None, False)
    if t == INHERIT:
        return (str(org_type or "").strip().lower() or None, True)
    return (t, False)


def archived(project):
    """Is this project archived? Pure. Both signals, because they disagree."""
    row = project or {}
    return bool(row.get("archived_at")) or str(row.get("status") or "") == "archived"


def classify(project, org_type, project_type, require="zdr"):
    """Classify one project's retention. Pure. Returns (state, detail).

    Order matters: unreadable, then none, then family, then inheritance. An
    unrecognised value is never graded as safe, and none is never summarised
    into the same row as an inherit even though they sit in the same enum.
    """
    eff, inherited = effective(org_type, project_type)
    fam = family(eff)
    tail = " (archived, and its retained data is still retained)" if archived(project) else ""
    want = FAMILY_LABEL.get(require, require)

    if fam in ("unreadable", "unrecognised"):
        return ("retention-unreadable",
                "the project reports %s, which this audit will not grade as safe%s"
                % (repr(str(project_type)) if project_type else "nothing", tail))
    if fam == "none":
        return ("no-retention-control",
                "type is none: no retention control at all, whatever the "
                "organization default says%s" % tail)
    if fam != require:
        return ("weaker-than-claimed",
                "resolves to %s (%s)%s, and %s was claimed"
                % (eff,
                   "inherited from the organization" if inherited
                   else "set on the project", tail, want))
    if inherited:
        return ("inherited-not-pinned",
                "resolves to %s only because the organization default says so. "
                "Nothing on the project pins it%s" % (eff, tail))
    return ("compliant", "pinned on the project at %s%s" % (eff, tail))


def residency_note(project, want):
    """(ok, detail) on the residency axis. Pure. Absent is unset, not GLOBAL."""
    if not want:
        return (True, None)
    got = (project or {}).get("residency")
    if got is None:
        return (False, "residency is unset on this project, which is neither "
                       "GLOBAL nor %s" % want)
    if str(got) != str(want):
        return (False, "residency is %s, and %s was claimed" % (got, want))
    return (True, None)


def repair_lines(state, project, require="zdr"):
    """The repair for one project. Pure. Printed, never performed."""
    pid = str((project or {}).get("id") or "unknown")
    lines = []
    if state not in FINDINGS:
        return lines
    if state == "inherited-not-pinned":
        lines.append("this resolves correctly today and moves the day somebody "
                     "changes the organization default. Pin it on the project if "
                     "the commitment is about this workload.")
    elif state == "retention-unreadable":
        lines.append("the endpoint returned a value this audit does not "
                     "recognise. Read it by hand before assuming anything.")
    target = TARGET.get(require)
    if target:
        lines.append("POST /v1/organization/projects/%s/data_retention with a body "
                     'of {"retention_type": "%s"}' % (pid, target))
        lines.append("the request field is retention_type; the response field is "
                     "type. A body copied from the read shape 400s.")
        lines.append("zero data retention and the enhanced variants are generally "
                     "enabled on the account by OpenAI rather than being "
                     "self-serve. Request it; do not assume the call will take.")
    return lines


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an organization "
                         "admin key, not a project key" % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    params = dict(params)
    while True:
        page = get(session, path, params) or {}
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require", default="zdr",
                    choices=sorted(FAMILY_LABEL),
                    help="the retention family your commitments claim")
    ap.add_argument("--residency", default=None,
                    help="the project residency your commitments claim, "
                         "e.g. EU_STORAGE_PROCESSING")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a project "
                  "key cannot read /v1/organization/data_retention")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    org = get(s, "/organization/data_retention") or {}
    org_type = org.get("type")
    log.info("organization default: %s", org_type or "unreadable")

    projects = list(paged(s, "/organization/projects", limit=100,
                          include_archived="true"))
    findings = []
    for project in projects:
        pid = str(project.get("id") or "")
        block = get(s, "/organization/projects/%s/data_retention" % pid) or {}
        state, detail = classify(project, org_type, block.get("type"), args.require)
        if state in FINDINGS:
            findings.append((project, state, detail))

    residency_bad = []
    if args.residency:
        for project in projects:
            ok, detail = residency_note(project, args.residency)
            if not ok:
                residency_bad.append((project, detail))

    log.info("%d project(s), %d retention finding(s), %d residency finding(s)",
             len(projects), len(findings), len(residency_bad))

    findings.sort(key=lambda r: (SEVERITY.get(r[1], 9), str(r[0].get("name") or "")))
    for project, state, detail in findings:
        log.warning("%-22s %-14s %s", state, project.get("id"),
                    project.get("name") or "(unnamed)")
        log.warning("  %s", detail)
        for line in repair_lines(state, project, args.require):
            log.warning("  repair: %s", line)

    for project, detail in residency_bad:
        log.warning("%-22s %-14s %s", "residency", project.get("id"), detail)

    return 1 if (findings or residency_bad) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-data-retention-audit.mjs",
"js": '''/**
 * Find OpenAI projects whose retention posture is not the one you claim.
 *
 * Read only. One GET for the organization default, one paged GET for the
 * project list, one GET per project. No request body is constructed anywhere,
 * including for the repair, which is printed as text.
 */
const API = 'https://api.openai.com/v1';

const ZDR = new Set(['zero_data_retention', 'enhanced_zero_data_retention']);
const MAM = new Set(['modified_abuse_monitoring', 'enhanced_modified_abuse_monitoring']);
const INHERIT = 'organization_default';
const NO_CONTROL = 'none';

const FAMILY_LABEL = { zdr: 'zero data retention',
                       'modified-abuse-monitoring': 'modified abuse monitoring' };
const TARGET = { zdr: 'zero_data_retention',
                 'modified-abuse-monitoring': 'modified_abuse_monitoring' };

const FINDINGS = new Set(['retention-unreadable', 'no-retention-control',
                          'weaker-than-claimed', 'inherited-not-pinned']);
const SEVERITY = { 'no-retention-control': 0, 'weaker-than-claimed': 1,
                   'retention-unreadable': 2, 'inherited-not-pinned': 3 };

/** Group one type value into a family. Pure. Never ranks families. */
export function family(retentionType) {
  const t = String(retentionType ?? '').trim().toLowerCase();
  if (!t) return 'unreadable';
  if (ZDR.has(t)) return 'zdr';
  if (MAM.has(t)) return 'modified-abuse-monitoring';
  if (t === NO_CONTROL) return 'none';
  return 'unrecognised';
}

/** [type, inherited] for one project. Pure. */
export function effective(orgType, projectType) {
  const t = String(projectType ?? '').trim().toLowerCase();
  if (!t) return [null, false];
  if (t === INHERIT) return [String(orgType ?? '').trim().toLowerCase() || null, true];
  return [t, false];
}

/** Is this project archived? Pure. Both signals, because they disagree. */
export function archived(project) {
  return Boolean(project?.archived_at) || String(project?.status ?? '') === 'archived';
}

/** Classify one project's retention. Pure. Returns [state, detail]. */
export function classify(project, orgType, projectType, require = 'zdr') {
  const [eff, inherited] = effective(orgType, projectType);
  const fam = family(eff);
  const tail = archived(project)
    ? ' (archived, and its retained data is still retained)' : '';
  const want = FAMILY_LABEL[require] ?? require;

  if (fam === 'unreadable' || fam === 'unrecognised') {
    return ['retention-unreadable',
            `the project reports ${projectType ? `'${projectType}'` : 'nothing'}, `
            + `which this audit will not grade as safe${tail}`];
  }
  if (fam === 'none') {
    return ['no-retention-control',
            'type is none: no retention control at all, whatever the organization '
            + `default says${tail}`];
  }
  if (fam !== require) {
    return ['weaker-than-claimed',
            `resolves to ${eff} (${inherited ? 'inherited from the organization'
              : 'set on the project'})${tail}, and ${want} was claimed`];
  }
  if (inherited) {
    return ['inherited-not-pinned',
            `resolves to ${eff} only because the organization default says so. `
            + `Nothing on the project pins it${tail}`];
  }
  return ['compliant', `pinned on the project at ${eff}${tail}`];
}

/** [ok, detail] on the residency axis. Pure. Absent is unset, not GLOBAL. */
export function residencyNote(project, want) {
  if (!want) return [true, null];
  const got = project?.residency ?? null;
  if (got === null) {
    return [false, 'residency is unset on this project, which is neither GLOBAL '
                   + `nor ${want}`];
  }
  if (String(got) !== String(want)) {
    return [false, `residency is ${got}, and ${want} was claimed`];
  }
  return [true, null];
}

/** The repair for one project. Pure. Printed, never performed. */
export function repairLines(state, project, require = 'zdr') {
  const pid = String(project?.id ?? 'unknown');
  const lines = [];
  if (!FINDINGS.has(state)) return lines;
  if (state === 'inherited-not-pinned') {
    lines.push('this resolves correctly today and moves the day somebody changes '
      + 'the organization default. Pin it on the project if the commitment is '
      + 'about this workload.');
  } else if (state === 'retention-unreadable') {
    lines.push('the endpoint returned a value this audit does not recognise. Read '
      + 'it by hand before assuming anything.');
  }
  const target = TARGET[require];
  if (target) {
    lines.push(`POST /v1/organization/projects/${pid}/data_retention with a body of `
      + `{"retention_type": "${target}"}`);
    lines.push('the request field is retention_type; the response field is type. A '
      + 'body copied from the read shape 400s.');
    lines.push('zero data retention and the enhanced variants are generally enabled '
      + 'on the account by OpenAI rather than being self-serve. Request it; do not '
      + 'assume the call will take.');
  }
  return lines;
}

async function read(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
      + 'organization admin key, not a project key');
  }
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function paged(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = (await read(key, path, q)) ?? {};
    const data = page.data ?? [];
    out.push(...data);
    if (!page.has_more || data.length === 0) return out;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key; a project '
                  + 'key cannot read /v1/organization/data_retention');
    process.exitCode = 2;
    return;
  }
  const require_ = process.env.REQUIRE ?? 'zdr';
  const wantResidency = process.env.RESIDENCY ?? null;

  const org = (await read(admin, '/organization/data_retention')) ?? {};
  console.log(`organization default: ${org.type ?? 'unreadable'}`);

  const projects = await paged(admin, '/organization/projects',
                               { limit: 100, include_archived: 'true' });
  const findings = [];
  for (const project of projects) {
    const block = (await read(admin,
      `/organization/projects/${String(project.id ?? '')}/data_retention`)) ?? {};
    const [state, detail] = classify(project, org.type, block.type, require_);
    if (FINDINGS.has(state)) findings.push([project, state, detail]);
  }

  const residencyBad = [];
  if (wantResidency) {
    for (const project of projects) {
      const [ok, detail] = residencyNote(project, wantResidency);
      if (!ok) residencyBad.push([project, detail]);
    }
  }

  console.log(`${projects.length} project(s), ${findings.length} retention `
              + `finding(s), ${residencyBad.length} residency finding(s)`);

  findings.sort(([pa, sa], [pb, sb]) =>
    (SEVERITY[sa] ?? 9) - (SEVERITY[sb] ?? 9)
    || String(pa.name ?? '').localeCompare(String(pb.name ?? '')));

  for (const [project, state, detail] of findings) {
    console.warn(`${state.padEnd(22)} ${String(project.id).padEnd(14)} `
                 + `${project.name ?? '(unnamed)'}`);
    console.warn(`  ${detail}`);
    for (const line of repairLines(state, project, require_)) {
      console.warn(`  repair: ${line}`);
    }
  }
  for (const [project, detail] of residencyBad) {
    console.warn(`${'residency'.padEnd(22)} ${String(project.id).padEnd(14)} ${detail}`);
  }
  process.exitCode = (findings.length || residencyBad.length) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note: one project, one value, read twice under two different organization defaults. A project sitting at <code>organization_default</code> is <code>inherited-not-pinned</code> when the org is a ZDR variant and <code>weaker-than-claimed</code> when it is not, and nothing on the project changed between the two readings. The second test keeps <code>none</code> away from the inherit path, because both words live in the same enum and only one of them means &ldquo;ask the level above&rdquo;. Then: the family map, which groups the enhanced variants without ranking them; an unrecognised string, which must be unreadable rather than safe; residency, which is a separate axis where absent is unset and not <code>GLOBAL</code>; and the repair body, which has to say <code>retention_type</code> and has to say the enhanced variants are requested rather than set.",
"test_py_file": "test_openai_data_retention_audit.py",
"test_py": '''from openai_data_retention_audit import (archived, classify, effective,
                                          family, repair_lines, residency_note)

EU = {"id": "proj_eu", "name": "EU tenant", "status": "active",
      "residency": "EU_STORAGE_PROCESSING"}


def test_the_same_project_resolves_two_ways_under_two_org_defaults():
    # The note. Nothing on proj_eu changes between these two readings.
    state, detail = classify(EU, "enhanced_zero_data_retention",
                             "organization_default", "zdr")
    assert state == "inherited-not-pinned"
    assert "only because the organization default says so" in detail
    assert any("moves the day somebody changes" in line
               for line in repair_lines(state, EU, "zdr"))

    state, detail = classify(EU, "modified_abuse_monitoring",
                             "organization_default", "zdr")
    assert state == "weaker-than-claimed"
    assert "inherited from the organization" in detail
    assert "zero data retention was claimed" in detail

    # And pinned on the project is a pass, not a finding.
    assert classify(EU, "modified_abuse_monitoring",
                    "zero_data_retention", "zdr")[0] == "compliant"


def test_none_is_never_treated_as_an_inherit():
    state, detail = classify({"id": "proj_ingest"}, "enhanced_zero_data_retention",
                             "none", "zdr")
    assert state == "no-retention-control"
    assert "whatever the organization default says" in detail
    # The org default is a ZDR variant and the project still fails, which is the
    # whole reason none has its own state.
    assert effective("enhanced_zero_data_retention", "none") == ("none", False)
    assert effective("enhanced_zero_data_retention", "organization_default") == \\
        ("enhanced_zero_data_retention", True)
    assert effective("zero_data_retention", None) == (None, False)


def test_the_family_map_groups_without_ranking():
    assert family("zero_data_retention") == "zdr"
    assert family("enhanced_zero_data_retention") == "zdr"
    assert family("modified_abuse_monitoring") == "modified-abuse-monitoring"
    assert family("enhanced_modified_abuse_monitoring") == "modified-abuse-monitoring"
    assert family("none") == "none"
    assert family(None) == "unreadable"
    assert family("standard") == "unrecognised"
    # Claiming the weaker family makes a MAM project pass, and that is a
    # decision the caller makes rather than one the script makes for them.
    project = {"id": "proj_a"}
    assert classify(project, None, "modified_abuse_monitoring",
                    "modified-abuse-monitoring")[0] == "compliant"
    assert classify(project, None, "modified_abuse_monitoring",
                    "zdr")[0] == "weaker-than-claimed"


def test_an_unrecognised_value_is_never_graded_as_safe():
    state, detail = classify({"id": "proj_x"}, "zero_data_retention",
                             "legacy_mode", "zdr")
    assert state == "retention-unreadable"
    assert "will not grade as safe" in detail
    assert any("Read it by hand" in line for line in repair_lines(state,
                                                                  {"id": "proj_x"}))
    # A project the endpoint would not answer for is unreadable too.
    assert classify({"id": "proj_y"}, "zero_data_retention", None,
                    "zdr")[0] == "retention-unreadable"


def test_archived_projects_are_graded_and_labelled():
    old = {"id": "proj_old", "archived_at": 1_700_000_000}
    assert archived(old) is True
    assert archived({"id": "p", "status": "archived"}) is True
    assert archived({"id": "p", "status": "active"}) is False
    state, detail = classify(old, "modified_abuse_monitoring", "none", "zdr")
    assert state == "no-retention-control"
    assert "its retained data is still retained" in detail


def test_residency_is_a_separate_axis_and_absent_is_not_global():
    ok, detail = residency_note(EU, "EU_STORAGE_PROCESSING")
    assert ok is True and detail is None
    ok, detail = residency_note({"id": "p", "residency": "US_STORAGE_PROCESSING"},
                                "EU_STORAGE_PROCESSING")
    assert ok is False
    assert "residency is US_STORAGE_PROCESSING" in detail
    ok, detail = residency_note({"id": "p"}, "EU_STORAGE_PROCESSING")
    assert ok is False
    assert "neither GLOBAL nor" in detail
    # No claim, no finding.
    assert residency_note({"id": "p"}, None) == (True, None)


def test_the_repair_body_uses_retention_type_and_says_it_is_a_request():
    lines = repair_lines("no-retention-control", {"id": "proj_ingest"}, "zdr")
    assert any('{"retention_type": "zero_data_retention"}' in line for line in lines)
    assert any("the response field is type" in line for line in lines)
    assert any("Request it" in line for line in lines)
    assert repair_lines("compliant", {"id": "proj_ingest"}, "zdr") == []
''',
"test_js_file": "openai-data-retention-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { archived, classify, effective, family, repairLines, residencyNote }
  from './openai-data-retention-audit.mjs';

const EU = { id: 'proj_eu', name: 'EU tenant', status: 'active',
             residency: 'EU_STORAGE_PROCESSING' };

test('the same project resolves two ways under two org defaults', () => {
  let [state, detail] = classify(EU, 'enhanced_zero_data_retention',
                                 'organization_default', 'zdr');
  assert.equal(state, 'inherited-not-pinned');
  assert.ok(detail.includes('only because the organization default says so'));
  assert.ok(repairLines(state, EU, 'zdr')
    .some((l) => l.includes('moves the day somebody changes')));

  [state, detail] = classify(EU, 'modified_abuse_monitoring',
                             'organization_default', 'zdr');
  assert.equal(state, 'weaker-than-claimed');
  assert.ok(detail.includes('inherited from the organization'));
  assert.ok(detail.includes('zero data retention was claimed'));

  assert.equal(classify(EU, 'modified_abuse_monitoring',
                        'zero_data_retention', 'zdr')[0], 'compliant');
});

test('none is never treated as an inherit', () => {
  const [state, detail] = classify({ id: 'proj_ingest' },
    'enhanced_zero_data_retention', 'none', 'zdr');
  assert.equal(state, 'no-retention-control');
  assert.ok(detail.includes('whatever the organization default says'));
  assert.deepEqual(effective('enhanced_zero_data_retention', 'none'), ['none', false]);
  assert.deepEqual(effective('enhanced_zero_data_retention', 'organization_default'),
                   ['enhanced_zero_data_retention', true]);
  assert.deepEqual(effective('zero_data_retention', null), [null, false]);
});

test('the family map groups without ranking', () => {
  assert.equal(family('zero_data_retention'), 'zdr');
  assert.equal(family('enhanced_zero_data_retention'), 'zdr');
  assert.equal(family('modified_abuse_monitoring'), 'modified-abuse-monitoring');
  assert.equal(family('enhanced_modified_abuse_monitoring'),
               'modified-abuse-monitoring');
  assert.equal(family('none'), 'none');
  assert.equal(family(null), 'unreadable');
  assert.equal(family('standard'), 'unrecognised');
  const project = { id: 'proj_a' };
  assert.equal(classify(project, null, 'modified_abuse_monitoring',
                        'modified-abuse-monitoring')[0], 'compliant');
  assert.equal(classify(project, null, 'modified_abuse_monitoring', 'zdr')[0],
               'weaker-than-claimed');
});

test('an unrecognised value is never graded as safe', () => {
  const [state, detail] = classify({ id: 'proj_x' }, 'zero_data_retention',
                                   'legacy_mode', 'zdr');
  assert.equal(state, 'retention-unreadable');
  assert.ok(detail.includes('will not grade as safe'));
  assert.ok(repairLines(state, { id: 'proj_x' })
    .some((l) => l.includes('Read it by hand')));
  assert.equal(classify({ id: 'proj_y' }, 'zero_data_retention', null, 'zdr')[0],
               'retention-unreadable');
});

test('archived projects are graded and labelled', () => {
  const old = { id: 'proj_old', archived_at: 1700000000 };
  assert.equal(archived(old), true);
  assert.equal(archived({ id: 'p', status: 'archived' }), true);
  assert.equal(archived({ id: 'p', status: 'active' }), false);
  const [state, detail] = classify(old, 'modified_abuse_monitoring', 'none', 'zdr');
  assert.equal(state, 'no-retention-control');
  assert.ok(detail.includes('its retained data is still retained'));
});

test('residency is a separate axis and absent is not GLOBAL', () => {
  assert.deepEqual(residencyNote(EU, 'EU_STORAGE_PROCESSING'), [true, null]);
  let [ok, detail] = residencyNote({ id: 'p', residency: 'US_STORAGE_PROCESSING' },
                                   'EU_STORAGE_PROCESSING');
  assert.equal(ok, false);
  assert.ok(detail.includes('residency is US_STORAGE_PROCESSING'));
  [ok, detail] = residencyNote({ id: 'p' }, 'EU_STORAGE_PROCESSING');
  assert.equal(ok, false);
  assert.ok(detail.includes('neither GLOBAL nor'));
  assert.deepEqual(residencyNote({ id: 'p' }, null), [true, null]);
});

test('the repair body uses retention_type and says it is a request', () => {
  const lines = repairLines('no-retention-control', { id: 'proj_ingest' }, 'zdr');
  assert.ok(lines.some((l) => l.includes('{"retention_type": "zero_data_retention"}')));
  assert.ok(lines.some((l) => l.includes('the response field is type')));
  assert.ok(lines.some((l) => l.includes('Request it')));
  assert.deepEqual(repairLines('compliant', { id: 'proj_ingest' }, 'zdr'), []);
});
''',
"faq": [
 ("Why does the script make me tell it what posture I claim?",
  "Because the API returns six values and no ordering, and inventing one would be the worst thing this script could do. It is genuinely unclear whether enhanced_modified_abuse_monitoring satisfies a commitment that a customer signed off as zero data retention; that is a question for whoever wrote the commitment, and the answer differs between contracts. So the script groups the six values into families it can define objectively, takes the family you say you claim, and reports which projects do not reach it. Everything it asserts is then a fact about your organization plus one input you supplied, rather than a compliance opinion it made up."),
 ("Our organization default is set correctly. Why is a project still flagged?",
  "Two reasons, and they are different. If the project reads none, it has no retention control at all and the organization default does not reach it — none and organization_default sit in the same enum and mean opposite things. If the project reads organization_default and the org value satisfies your claim, the script reports inherited-not-pinned, which is not a failure today: it is a note that nothing on the project holds it there, so the posture of that workload changes the next time somebody edits the org default for an unrelated reason. Whether to pin it depends on whether the commitment is about the workload or about the account."),
 ("Can the script fix this for me?",
  "No, and it would be the wrong shape of tool if it could. The corrective call is printed rather than executed, for the usual reason in this section, and for one specific to retention: zero data retention and the enhanced variants generally have to be enabled on the account by OpenAI rather than being self-serve, so a script that fires the POST would report success or failure that has nothing to do with whether your account is entitled to the setting. The repair line says request this rather than set this. There is also a field-name trap worth knowing: you read type and you write retention_type."),
 ("What does residency have to do with retention?",
  "Nothing, which is exactly why it is on a separate line. Retention answers how long prompts and completions are held; residency answers where they are stored and processed. A project can hold zero data retention and still be sitting at GLOBAL when the contract said EU_STORAGE_PROCESSING, and a project can be correctly in the EU and retain everything. The script reads residency off the project object because it is free to read while you are already listing projects, grades it against a separate claim you pass in, and never blends the two into one verdict."),
 ("Does the audit log show me when this last changed?",
  "Partly. GET /v1/organization/audit_logs carries organization.updated and project.updated events, and a retention change shows up as one of those, so you can establish roughly when the posture moved and who moved it. What the log does not do is give you a clean before-and-after of the retention type itself, and it does not reach back further than the log's own retention window. Use it to reconstruct a story once the current-state audit has told you there is a story; do not use it as the primary check."),
],
"related": [REL_CMEK, REL_MODELPERM, REL_ARCHIVED],
"citations": [CITE_OA_YOUR_DATA, CITE_OA_ADMIN_GUIDE, CITE_OA_PROJECTS, CITE_OA_SDK],
},
{
"slug": "project-model-permissions-unrestricted",
"title": "A model permission policy that has never excluded anything",
"description": "mode deny_list with an empty model_ids looks configured and permits every model. Read the policy per project and grade it against what was actually called.",
"h1": "A model permission policy that has never excluded anything",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai project model_permissions api",
             "openai restrict models per project",
             "openai hosted_tool_permissions web_search enabled",
             "openai project allow_list model_ids",
             "openai deny_list empty model permissions"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because the per-project permission endpoints and the usage reports all reject a project key.",
"lead": "The postmortem is short and everybody already knows how it ends. A nightly classification job that labels support tickets was pointed at the most capable model in the catalogue, because that is what the developer had in their editor from the last thing they built, and it ran that way for five weeks. The interesting question is not why they chose it. It is the one somebody asks at the end of the meeting, almost as an aside: what would have stopped it? And the answer is nothing, in that project or any other, because model access is open by default and the control that closes it is per project and opt-in.",
"short_answer": """<p>One GET per project with an <strong>organization admin key</strong>. <code>GET /v1/organization/projects/{project_id}/model_permissions</code> returns a <code>project.model_permissions</code> object with <code>mode</code> &mdash; <code>"allow_list"</code> or <code>"deny_list"</code> &mdash; and <code>model_ids[]</code>. There are three ways for that to mean "everything is reachable":</p>
<p><strong>No policy at all</strong>, where the endpoint has nothing to return, which is the default state of every project ever created. <strong><code>mode: "deny_list"</code> with an empty <code>model_ids</code></strong>, which is the interesting one: an object exists, the console shows a configured policy, and it denies nothing. And <strong>a deny list that names models</strong>, which is not unrestricted but fails open by construction &mdash; anything released next month is permitted the day it ships, without anybody deciding that.</p>
<p>Then grade the policy against reality. <code>GET /v1/organization/usage/completions?group_by=project_id&amp;group_by=model</code> over thirty days gives the models each project actually called. An <code>allow_list</code> naming eleven models where one was used is a policy that has never excluded anything the project wanted, which is a different finding from having no policy and has a different repair.</p>
<p><code>GET /v1/organization/projects/{project_id}/hosted_tool_permissions</code> is the same question for the billable hosted tools: <code>code_interpreter</code>, <code>file_search</code>, <code>image_generation</code>, <code>mcp</code> and <code>web_search</code>, each an <code>{"enabled": bool}</code>, each on by default.</p>""",
"problem": """<p>Model access is open across an organization unless somebody closes it, and closing it is a per-project act. That means the control has the worst possible shape for surviving time: a policy written once, applied to the four projects that existed that afternoon, and silently absent from the eleventh project created two years later by somebody who has never heard of it.</p>
<p>The empty deny list is the version that does real damage, because it is indistinguishable from work having been done. Somebody opened the policy, chose deny list, intended to fill it in, and got pulled onto something else. From that day forward the project has a model permissions object, it appears configured in the console, and every model in the catalogue is reachable from it. An audit that checks whether a policy exists reports it as covered.</p>
<p>Hosted tools have the same default and a sharper cost profile. Web search, code interpreter, file search, image generation and MCP are all enabled on every project unless explicitly disabled, and they are billed on their own line items rather than as tokens. A project that has never made a web search call still has web search available to anything holding one of its keys.</p>""",
"why": """<p><strong>This note is about the policy object, not about the model choice, and the code keeps that line.</strong> A published note already covers spending a frontier model's rate on trivial work; that one reads what was called and prices it. This one never says a model was the wrong pick, has no notion of a model being expensive, and produces no recommendation to switch anything. It asks a single structural question &mdash; is there a policy here, and has it ever excluded anything &mdash; and the observed model list appears only as the raw material for a least-privilege allow list. If you want to know whether the model was wrong, that is the other note.</p>
<p><strong>An absent policy and an empty deny list are the same reachability and two different repairs.</strong> Both permit every model. But one of them was never touched, so the repair is "add a policy to project creation automation", and the other was touched by somebody who meant to finish, so the repair is "finish it, and find out whether anybody has been relying on the assumption that it was done". Collapsing them into one row loses the only fact that tells you which conversation to have.</p>
<p><strong>A deny list that names models is graded, and graded as failing open.</strong> This is not a bug and it is not always wrong &mdash; a deny list is the right shape when you have one specific model to keep out. But its semantics are worth saying plainly in the report: every model that does not exist yet is permitted. A policy whose coverage of tomorrow's catalogue is unconditional is a different risk posture from an allow list, and a report that grades only "is a policy present" cannot tell you which one you have.</p>
<p><strong>Three of the five hosted tools can be counted, one can be counted awkwardly, and one cannot be counted at all.</strong> <code>web_search_calls</code>, <code>code_interpreter_sessions</code> and <code>file_search_calls</code> each have a usage endpoint, so "enabled and never used" is a fact. <code>image_generation</code> shows up under the images usage report. <code>mcp</code> has no usage endpoint at all, so the script reports it as enabled-and-uncountable rather than pretending zero usage is evidence of anything. Saying which of the five it cannot measure is the difference between a report and a guess.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>The permission endpoints and the usage reports all reject a project key. Read scopes are enough. Nothing in the script constructs a request body, so there is no path by which it edits a policy.</p>"""},
 {"h": "List the projects and read both permission objects for each",
  "body": """<p><code>GET /v1/organization/projects?limit=100</code>, then <code>model_permissions</code> and <code>hosted_tool_permissions</code> per project. Treat a 404 on the model policy as "no policy configured", which is a real and common state, not an error.</p>"""},
 {"h": "Separate the three unrestricted shapes",
  "body": """<p>Absent, <code>deny_list</code> with an empty <code>model_ids</code>, and <code>deny_list</code> with entries. The first two are unrestricted; the third is restricted today and open to whatever ships tomorrow. Grade an <code>allow_list</code> with an empty <code>model_ids</code> separately again &mdash; that one permits nothing and is a different kind of surprise.</p>"""},
 {"h": "Read the models actually used, per project",
  "body": """<p><code>GET /v1/organization/usage/completions</code> over thirty days with <code>group_by=project_id</code> and <code>group_by=model</code>, <code>bucket_width=1d</code>, <code>limit=31</code>. Fold <code>num_model_requests</code> per project and model. This is evidence for the allow list, not a judgement about the models.</p>"""},
 {"h": "Check the hosted tools against their own usage endpoints",
  "body": """<p><code>web_search_calls</code>, <code>code_interpreter_sessions</code>, <code>file_search_calls</code> and <code>images</code>. Enabled with nothing counted in the window is unused surface. <code>mcp</code> has no usage endpoint; report it as uncountable rather than as unused.</p>"""},
],
"verify": """<p>Apply a least-privilege allow list to one project and re-run. That project should move from an unrestricted state to <code>restricted</code>, and the models list in the report should match the one the usage report shows. Then create a brand new project and run the script again without touching it: it should appear immediately as <code>no-policy</code>, which is the whole point &mdash; the control does not inherit, and that is the finding you want automated rather than remembered.</p>
<pre><code class="language-bash">python3 openai_project_model_policy_audit.py --days 30
# 6 project(s), 4 finding(s)
# deny-list-empty          proj_batch    Nightly jobs
#   a policy object exists, mode is deny_list, and model_ids is empty. This
#   permits every model and looks configured in the console.
#   repair: POST /v1/organization/projects/proj_batch/model_permissions with
#           {"mode": "allow_list", "model_ids": ["gpt-4.1-mini"]}
# no-policy                proj_demo     Demo sandbox
#   no model permissions policy is configured; every model the organization is
#   entitled to is reachable from this project.
#   repair: add the policy call to whatever creates projects. It does not inherit.
# allow-list-wider-than-use proj_web     Customer web app
#   allow_list names 11 model(s); 1 served any request in the last 30 day(s)
# hosted tools             proj_demo     web_search: enabled, and web_search_calls
#                                        reports nothing in the window
#                                        mcp: enabled, and no usage endpoint counts it</code></pre>""",
"code_intro": "One paged GET for projects, two GETs per project, and five usage reads, against seven pure functions. The policy classifier, which distinguishes absent from an empty deny list from a deny list with entries from an allow list; the <code>unrestricted</code> predicate, which is deliberately narrow; the usage fold; <code>unused_allowed</code>, which subtracts the observed models from an allow list; the hosted-tool grader, which knows which tools have a usage endpoint and says so for the one that does not; the verdict; and the repair lines, which print a least-privilege body built from observed models and never name a model the project did not already call.",
"py_file": "openai_project_model_policy_audit.py",
"py": '''"""Find OpenAI projects whose model permission policy excludes nothing.

Read only. One paged GET for the project list, two GETs per project for the
permission objects, and five usage reads. Every request is a GET and no request
body is constructed; the least-privilege policy is printed as text.

This script has no opinion about which model is appropriate for which workload.
It answers one structural question: is there a policy here, and has it ever
excluded anything the project wanted.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_project_model_policy_audit")

API = "https://api.openai.com/v1"
DAY = 86400

# The hosted tools, and the usage endpoint that can count each one. mcp has no
# usage endpoint, so it is reported as uncountable rather than as unused.
TOOL_USAGE = {
    "web_search": ("/organization/usage/web_search_calls", "num_requests"),
    "code_interpreter": ("/organization/usage/code_interpreter_sessions", "num_sessions"),
    "file_search": ("/organization/usage/file_search_calls", "num_requests"),
    "image_generation": ("/organization/usage/images", "num_model_requests"),
}

FINDINGS = ("no-policy", "deny-list-empty", "allow-list-empty",
            "deny-list-fails-open", "allow-list-wider-than-use",
            "policy-unreadable")

SEVERITY = {"deny-list-empty": 0, "no-policy": 1, "allow-list-wider-than-use": 2,
            "deny-list-fails-open": 3, "allow-list-empty": 4,
            "policy-unreadable": 5}


def policy_ids(policy):
    """The non-empty model ids on a policy. Pure."""
    out = []
    for value in (policy or {}).get("model_ids") or []:
        text = str(value or "").strip()
        if text:
            out.append(text)
    return out


def policy_state(policy):
    """Shape of one model permissions object. Pure.

    absent | deny-empty | deny-list | allow-empty | allow-list | unreadable.
    An absent policy and an empty deny list permit exactly the same set and are
    still two different states, because only one of them looks configured.
    """
    if policy is None:
        return "absent"
    mode = str((policy or {}).get("mode") or "").strip().lower()
    ids = policy_ids(policy)
    if mode == "deny_list":
        return "deny-empty" if not ids else "deny-list"
    if mode == "allow_list":
        return "allow-empty" if not ids else "allow-list"
    return "unreadable"


def unrestricted(policy):
    """Does this policy permit every model? Pure. Narrow on purpose."""
    return policy_state(policy) in ("absent", "deny-empty")


def fold_models(buckets, count_field="num_model_requests"):
    """{project_id: {model: requests}} across usage buckets. Pure."""
    out = {}
    for bucket in buckets or []:
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            try:
                n = int(row.get(count_field) or 0)
            except (TypeError, ValueError):
                n = 0
            if n <= 0:
                continue
            pid = str(row.get("project_id") or "unattributed")
            model = str(row.get("model") or "unknown")
            entry = out.setdefault(pid, {})
            entry[model] = entry.get(model, 0) + n
    return out


def unused_allowed(policy, used):
    """Allow-listed models that served nothing in the window. Pure.

    Only meaningful for an allow list. A deny list says nothing about what a
    project is permitted to reach, so subtracting usage from it is nonsense.
    """
    if policy_state(policy) != "allow-list":
        return []
    return sorted(set(policy_ids(policy)) - set((used or {}).keys()))


def unused_tools(perms, counts):
    """[(tool, why)] for enabled hosted tools. Pure.

    A tool with no usage endpoint is reported as uncountable. Treating its
    absence from a report as zero usage would be inventing evidence.
    """
    out = []
    for tool, block in sorted((perms or {}).items()):
        if not isinstance(block, dict) or not block.get("enabled"):
            continue
        if tool not in TOOL_USAGE:
            out.append((tool, "enabled, and no usage endpoint counts it"))
            continue
        if int((counts or {}).get(tool) or 0) <= 0:
            out.append((tool, "enabled, and %s reports nothing in the window"
                        % TOOL_USAGE[tool][0].rsplit("/", 1)[-1]))
    return out


def classify(policy, used, days=30):
    """Classify one project's model policy. Pure. Returns (state, detail)."""
    shape = policy_state(policy)
    seen = sorted((used or {}).keys())

    if shape == "absent":
        return ("no-policy",
                "no model permissions policy is configured; every model the "
                "organization is entitled to is reachable from this project")
    if shape == "unreadable":
        return ("policy-unreadable",
                "the policy object has no recognisable mode and will not be "
                "graded as restrictive")
    if shape == "deny-empty":
        return ("deny-list-empty",
                "a policy object exists, mode is deny_list, and model_ids is "
                "empty. This permits every model and looks configured")
    if shape == "allow-empty":
        return ("allow-list-empty",
                "mode is allow_list with no model_ids, which permits nothing. If "
                "this project is serving traffic, something else is going on")
    if shape == "deny-list":
        return ("deny-list-fails-open",
                "deny_list naming %d model(s). Restrictive today and open by "
                "construction to anything released tomorrow"
                % len(policy_ids(policy)))

    spare = unused_allowed(policy, used)
    if spare:
        return ("allow-list-wider-than-use",
                "allow_list names %d model(s); %d served any request in the last "
                "%d day(s). Unused: %s"
                % (len(policy_ids(policy)), len(seen), days, ", ".join(spare)))
    return ("restricted",
            "allow_list of %d model(s), all of them in use"
            % len(policy_ids(policy)))


def repair_lines(state, project_id, used):
    """The repair for one project. Pure. Printed, never performed.

    The suggested allow list is exactly the set of models the project already
    called. The script never proposes a model the project has not used.
    """
    lines = []
    if state not in FINDINGS:
        return lines
    if state == "no-policy":
        lines.append("add the policy call to whatever creates projects. It does "
                     "not inherit from the organization or from any other "
                     "project.")
    elif state == "deny-list-empty":
        lines.append("somebody opened this policy and did not finish it. Find out "
                     "who, and whether anything downstream assumed it was done.")
    elif state == "deny-list-fails-open":
        lines.append("a deny list permits every model that does not exist yet. "
                     "Switch to an allow list unless keeping one named model out "
                     "is genuinely the whole requirement.")
    elif state == "allow-list-empty":
        lines.append("this permits nothing. Read it before changing it; an empty "
                     "allow list is more often a mistake than a lockdown.")
    elif state == "policy-unreadable":
        lines.append("read the policy object by hand. This audit will not call an "
                     "unrecognised mode restrictive.")
    observed = sorted((used or {}).keys())
    if observed:
        lines.append('POST /v1/organization/projects/%s/model_permissions with '
                     '{"mode": "allow_list", "model_ids": %s}'
                     % (project_id, list(observed)))
        lines.append("that list is what this project already called in the "
                     "window. It is a starting point, not a recommendation about "
                     "which model suits the work.")
    else:
        lines.append("this project called no model in the window, so there is no "
                     "observed set to build an allow list from. Decide it "
                     "deliberately rather than copying another project.")
    return lines


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an organization "
                         "admin key, not a project key" % r.status_code)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    params = dict(params)
    while True:
        page = get(session, path, params) or {}
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def usage(session, path, start, end):
    params = {"start_time": start, "end_time": end, "bucket_width": "1d",
              "limit": 31, "group_by": ["project_id", "model"]}
    out = []
    while True:
        page = get(session, path, params) or {}
        out.extend(page.get("data") or [])
        cursor = page.get("next_page")
        if not page.get("has_more") or not cursor:
            return out
        params = dict(params, page=cursor)


def tool_counts(session, start, end):
    """{project_id: {tool: count}} for the tools that have a usage endpoint."""
    out = {}
    for tool, (path, field) in TOOL_USAGE.items():
        params = {"start_time": start, "end_time": end, "bucket_width": "1d",
                  "limit": 31, "group_by": ["project_id"]}
        page = get(session, path, params) or {}
        for bucket in page.get("data") or []:
            for result in (bucket or {}).get("results") or []:
                row = result or {}
                try:
                    n = int(row.get(field) or 0)
                except (TypeError, ValueError):
                    n = 0
                pid = str(row.get("project_id") or "unattributed")
                out.setdefault(pid, {})
                out[pid][tool] = out[pid].get(tool, 0) + n
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="usage window to read")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a project "
                  "key cannot read the per-project permission endpoints")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    end = int(time.time())
    start = end - max(1, args.days) * DAY

    used = fold_models(usage(s, "/organization/usage/completions", start, end))
    counts = tool_counts(s, start, end)
    projects = list(paged(s, "/organization/projects", limit=100))

    findings, tool_findings = [], []
    for project in projects:
        pid = str(project.get("id") or "")
        policy = get(s, "/organization/projects/%s/model_permissions" % pid)
        state, detail = classify(policy, used.get(pid), args.days)
        if state in FINDINGS:
            findings.append((project, state, detail))
        perms = get(s, "/organization/projects/%s/hosted_tool_permissions" % pid) or {}
        spare = unused_tools(perms, counts.get(pid))
        if spare:
            tool_findings.append((project, spare))

    log.info("%d project(s), %d policy finding(s), %d project(s) with unused "
             "hosted tools", len(projects), len(findings), len(tool_findings))

    findings.sort(key=lambda r: (SEVERITY.get(r[1], 9), str(r[0].get("name") or "")))
    for project, state, detail in findings:
        pid = str(project.get("id") or "")
        log.warning("%-26s %-14s %s", state, pid, project.get("name") or "(unnamed)")
        log.warning("  %s", detail)
        for line in repair_lines(state, pid, used.get(pid)):
            log.warning("  repair: %s", line)

    for project, spare in tool_findings:
        log.warning("%-26s %-14s %s", "hosted tools", project.get("id"),
                    project.get("name") or "(unnamed)")
        for tool, why in spare:
            log.warning("  %s: %s", tool, why)

    return 1 if (findings or tool_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-project-model-policy-audit.mjs",
"js": '''/**
 * Find OpenAI projects whose model permission policy excludes nothing.
 *
 * Read only. One paged GET for the project list, two GETs per project for the
 * permission objects, and five usage reads. No request body is constructed;
 * the least-privilege policy is printed as text.
 *
 * The script has no opinion about which model suits which workload. It asks
 * whether a policy exists and whether it has ever excluded anything.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;

const TOOL_USAGE = {
  web_search: ['/organization/usage/web_search_calls', 'num_requests'],
  code_interpreter: ['/organization/usage/code_interpreter_sessions', 'num_sessions'],
  file_search: ['/organization/usage/file_search_calls', 'num_requests'],
  image_generation: ['/organization/usage/images', 'num_model_requests'],
};

const FINDINGS = new Set(['no-policy', 'deny-list-empty', 'allow-list-empty',
                          'deny-list-fails-open', 'allow-list-wider-than-use',
                          'policy-unreadable']);

const SEVERITY = { 'deny-list-empty': 0, 'no-policy': 1,
                   'allow-list-wider-than-use': 2, 'deny-list-fails-open': 3,
                   'allow-list-empty': 4, 'policy-unreadable': 5 };

/** The non-empty model ids on a policy. Pure. */
export function policyIds(policy) {
  return (policy?.model_ids ?? [])
    .map((v) => String(v ?? '').trim())
    .filter(Boolean);
}

/** Shape of one model permissions object. Pure. */
export function policyState(policy) {
  if (policy === null || policy === undefined) return 'absent';
  const mode = String(policy?.mode ?? '').trim().toLowerCase();
  const ids = policyIds(policy);
  if (mode === 'deny_list') return ids.length ? 'deny-list' : 'deny-empty';
  if (mode === 'allow_list') return ids.length ? 'allow-list' : 'allow-empty';
  return 'unreadable';
}

/** Does this policy permit every model? Pure. Narrow on purpose. */
export function unrestricted(policy) {
  const shape = policyState(policy);
  return shape === 'absent' || shape === 'deny-empty';
}

/** {project_id: {model: requests}} across usage buckets. Pure. */
export function foldModels(buckets, countField = 'num_model_requests') {
  const out = {};
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const n = Math.trunc(Number(result?.[countField] ?? 0));
      if (!Number.isFinite(n) || n <= 0) continue;
      const pid = String(result?.project_id ?? 'unattributed');
      const model = String(result?.model ?? 'unknown');
      const entry = (out[pid] ??= {});
      entry[model] = (entry[model] ?? 0) + n;
    }
  }
  return out;
}

/** Allow-listed models that served nothing in the window. Pure. */
export function unusedAllowed(policy, used) {
  if (policyState(policy) !== 'allow-list') return [];
  const seen = new Set(Object.keys(used ?? {}));
  return policyIds(policy).filter((m) => !seen.has(m)).sort();
}

/** [[tool, why]] for enabled hosted tools. Pure. */
export function unusedTools(perms, counts) {
  const out = [];
  for (const tool of Object.keys(perms ?? {}).sort()) {
    const block = perms[tool];
    if (!block || typeof block !== 'object' || !block.enabled) continue;
    if (!(tool in TOOL_USAGE)) {
      out.push([tool, 'enabled, and no usage endpoint counts it']);
      continue;
    }
    if (Math.trunc(Number((counts ?? {})[tool] ?? 0)) <= 0) {
      const name = TOOL_USAGE[tool][0].split('/').pop();
      out.push([tool, `enabled, and ${name} reports nothing in the window`]);
    }
  }
  return out;
}

/** Classify one project's model policy. Pure. Returns [state, detail]. */
export function classify(policy, used, days = 30) {
  const shape = policyState(policy);
  const seen = Object.keys(used ?? {}).sort();

  if (shape === 'absent') {
    return ['no-policy',
            'no model permissions policy is configured; every model the '
            + 'organization is entitled to is reachable from this project'];
  }
  if (shape === 'unreadable') {
    return ['policy-unreadable',
            'the policy object has no recognisable mode and will not be graded '
            + 'as restrictive'];
  }
  if (shape === 'deny-empty') {
    return ['deny-list-empty',
            'a policy object exists, mode is deny_list, and model_ids is empty. '
            + 'This permits every model and looks configured'];
  }
  if (shape === 'allow-empty') {
    return ['allow-list-empty',
            'mode is allow_list with no model_ids, which permits nothing. If this '
            + 'project is serving traffic, something else is going on'];
  }
  if (shape === 'deny-list') {
    return ['deny-list-fails-open',
            `deny_list naming ${policyIds(policy).length} model(s). Restrictive `
            + 'today and open by construction to anything released tomorrow'];
  }
  const spare = unusedAllowed(policy, used);
  if (spare.length) {
    return ['allow-list-wider-than-use',
            `allow_list names ${policyIds(policy).length} model(s); ${seen.length} `
            + `served any request in the last ${days} day(s). Unused: ${spare.join(', ')}`];
  }
  return ['restricted',
          `allow_list of ${policyIds(policy).length} model(s), all of them in use`];
}

/** The repair for one project. Pure. Printed, never performed. */
export function repairLines(state, projectId, used) {
  const lines = [];
  if (!FINDINGS.has(state)) return lines;
  if (state === 'no-policy') {
    lines.push('add the policy call to whatever creates projects. It does not '
      + 'inherit from the organization or from any other project.');
  } else if (state === 'deny-list-empty') {
    lines.push('somebody opened this policy and did not finish it. Find out who, '
      + 'and whether anything downstream assumed it was done.');
  } else if (state === 'deny-list-fails-open') {
    lines.push('a deny list permits every model that does not exist yet. Switch to '
      + 'an allow list unless keeping one named model out is genuinely the whole '
      + 'requirement.');
  } else if (state === 'allow-list-empty') {
    lines.push('this permits nothing. Read it before changing it; an empty allow '
      + 'list is more often a mistake than a lockdown.');
  } else if (state === 'policy-unreadable') {
    lines.push('read the policy object by hand. This audit will not call an '
      + 'unrecognised mode restrictive.');
  }
  const observed = Object.keys(used ?? {}).sort();
  if (observed.length) {
    lines.push(`POST /v1/organization/projects/${projectId}/model_permissions with `
      + `{"mode": "allow_list", "model_ids": ${JSON.stringify(observed)}}`);
    lines.push('that list is what this project already called in the window. It is '
      + 'a starting point, not a recommendation about which model suits the work.');
  } else {
    lines.push('this project called no model in the window, so there is no observed '
      + 'set to build an allow list from. Decide it deliberately rather than '
      + 'copying another project.');
  }
  return lines;
}

async function read(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const one of v) url.searchParams.append(k, String(one));
    else url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
      + 'organization admin key, not a project key');
  }
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function paged(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = (await read(key, path, q)) ?? {};
    const data = page.data ?? [];
    out.push(...data);
    if (!page.has_more || data.length === 0) return out;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function usage(key, path, start, end) {
  const params = { start_time: start, end_time: end, bucket_width: '1d',
                   limit: 31, group_by: ['project_id', 'model'] };
  const out = [];
  for (;;) {
    const page = (await read(key, path, params)) ?? {};
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) return out;
    params.page = page.next_page;
  }
}

async function toolCounts(key, start, end) {
  const out = {};
  for (const [tool, [path, field]] of Object.entries(TOOL_USAGE)) {
    const page = (await read(key, path, { start_time: start, end_time: end,
      bucket_width: '1d', limit: 31, group_by: ['project_id'] })) ?? {};
    for (const bucket of page.data ?? []) {
      for (const result of bucket?.results ?? []) {
        const n = Math.trunc(Number(result?.[field] ?? 0)) || 0;
        const pid = String(result?.project_id ?? 'unattributed');
        const entry = (out[pid] ??= {});
        entry[tool] = (entry[tool] ?? 0) + n;
      }
    }
  }
  return out;
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key; a project '
                  + 'key cannot read the per-project permission endpoints');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const end = Math.floor(Date.now() / 1000);
  const start = end - Math.max(1, days) * DAY;

  const used = foldModels(await usage(admin, '/organization/usage/completions', start, end));
  const counts = await toolCounts(admin, start, end);
  const projects = await paged(admin, '/organization/projects', { limit: 100 });

  const findings = [];
  const toolFindings = [];
  for (const project of projects) {
    const pid = String(project.id ?? '');
    const policy = await read(admin, `/organization/projects/${pid}/model_permissions`);
    const [state, detail] = classify(policy, used[pid], days);
    if (FINDINGS.has(state)) findings.push([project, state, detail]);
    const perms = (await read(admin,
      `/organization/projects/${pid}/hosted_tool_permissions`)) ?? {};
    const spare = unusedTools(perms, counts[pid]);
    if (spare.length) toolFindings.push([project, spare]);
  }

  console.log(`${projects.length} project(s), ${findings.length} policy finding(s), `
              + `${toolFindings.length} project(s) with unused hosted tools`);

  findings.sort(([pa, sa], [pb, sb]) =>
    (SEVERITY[sa] ?? 9) - (SEVERITY[sb] ?? 9)
    || String(pa.name ?? '').localeCompare(String(pb.name ?? '')));

  for (const [project, state, detail] of findings) {
    const pid = String(project.id ?? '');
    console.warn(`${state.padEnd(26)} ${pid.padEnd(14)} ${project.name ?? '(unnamed)'}`);
    console.warn(`  ${detail}`);
    for (const line of repairLines(state, pid, used[pid])) {
      console.warn(`  repair: ${line}`);
    }
  }
  for (const [project, spare] of toolFindings) {
    console.warn(`${'hosted tools'.padEnd(26)} ${String(project.id).padEnd(14)} `
                 + `${project.name ?? '(unnamed)'}`);
    for (const [tool, why] of spare) console.warn(`  ${tool}: ${why}`);
  }
  process.exitCode = (findings.length || toolFindings.length) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The headline test is two projects with identical traffic and identical reachability: one with no policy at all, one with <code>mode: \"deny_list\"</code> and an empty <code>model_ids</code>. Both permit every model, both have to come back as findings, and they have to be <em>different</em> findings with different repairs, because only one of them looks configured to whoever set it. After that: a deny list that names models, which is restricted today and graded as failing open tomorrow; an allow list eleven wide over one used model, where the repair proposes exactly the observed set and nothing else; the hosted-tool grader, which reports <code>mcp</code> as uncountable rather than as unused; and one test whose only job is to prove this note stays off the neighbouring one &mdash; no repair line anywhere may recommend a model the project did not already call.",
"test_py_file": "test_openai_project_model_policy_audit.py",
"test_py": '''from openai_project_model_policy_audit import (classify, fold_models,
                                               policy_ids, policy_state,
                                               repair_lines, unrestricted,
                                               unused_allowed, unused_tools)

USED = {"gpt-4.1-mini": 41208}


def bucket(*results):
    return {"object": "bucket", "start_time": 0, "end_time": 86400,
            "results": list(results)}


def test_an_absent_policy_and_an_empty_deny_list_are_two_findings():
    # The note. Identical reachability, identical usage, different repairs,
    # because one of these two looks configured in the console and one does not.
    absent_state, absent_detail = classify(None, USED)
    empty_state, empty_detail = classify({"mode": "deny_list", "model_ids": []}, USED)

    assert unrestricted(None) is True
    assert unrestricted({"mode": "deny_list", "model_ids": []}) is True
    assert absent_state == "no-policy"
    assert empty_state == "deny-list-empty"
    assert "looks configured" in empty_detail
    assert "reachable from this project" in absent_detail

    absent_lines = repair_lines(absent_state, "proj_demo", USED)
    empty_lines = repair_lines(empty_state, "proj_batch", USED)
    assert any("does not inherit" in line for line in absent_lines)
    assert any("did not finish it" in line for line in empty_lines)
    assert absent_lines != empty_lines


def test_a_deny_list_with_entries_is_restrictive_today_and_open_tomorrow():
    policy = {"mode": "deny_list", "model_ids": ["gpt-4.1"]}
    assert unrestricted(policy) is False
    state, detail = classify(policy, USED)
    assert state == "deny-list-fails-open"
    assert "released tomorrow" in detail
    assert any("does not exist yet" in line
               for line in repair_lines(state, "proj_x", USED))
    # Subtracting usage from a deny list would be nonsense, so it is not done.
    assert unused_allowed(policy, USED) == []


def test_an_allow_list_wider_than_use_names_only_what_it_measured():
    policy = {"mode": "allow_list",
              "model_ids": ["gpt-4.1-mini", "gpt-4.1", "o3", "gpt-4.1-nano"]}
    state, detail = classify(policy, USED, days=30)
    assert state == "allow-list-wider-than-use"
    assert "names 4 model(s); 1 served any request" in detail
    assert unused_allowed(policy, USED) == ["gpt-4.1", "gpt-4.1-nano", "o3"]
    # Exactly the observed set, and nothing the project never called.
    lines = repair_lines(state, "proj_web", USED)
    assert any("'model_ids': ['gpt-4.1-mini']" in line
               or '"model_ids": [\\'gpt-4.1-mini\\']' in line
               or "['gpt-4.1-mini']" in line for line in lines)
    assert not any("o3" in line for line in lines)
    # An allow list matching use exactly is not a finding.
    tight = {"mode": "allow_list", "model_ids": ["gpt-4.1-mini"]}
    assert classify(tight, USED)[0] == "restricted"
    assert repair_lines("restricted", "proj_web", USED) == []


def test_the_policy_shape_reader_handles_every_degenerate_case():
    assert policy_state(None) == "absent"
    assert policy_state({"mode": "allow_list", "model_ids": []}) == "allow-empty"
    assert policy_state({"mode": "allow_list", "model_ids": ["  "]}) == "allow-empty"
    assert policy_state({"mode": "ALLOW_LIST", "model_ids": ["a"]}) == "allow-list"
    assert policy_state({"mode": "something_new"}) == "unreadable"
    assert policy_ids({"model_ids": ["a", "", None, " b "]}) == ["a", "b"]
    state, detail = classify({"mode": "allow_list", "model_ids": []}, USED)
    assert state == "allow-list-empty"
    assert "permits nothing" in detail
    assert classify({"mode": "?"}, USED)[0] == "policy-unreadable"


def test_a_tool_with_no_usage_endpoint_is_uncountable_not_unused():
    perms = {"code_interpreter": {"enabled": False},
             "file_search": {"enabled": True},
             "image_generation": {"enabled": True},
             "mcp": {"enabled": True},
             "web_search": {"enabled": True}}
    counts = {"web_search": 4120, "file_search": 0, "image_generation": 0}
    found = dict(unused_tools(perms, counts))
    assert "web_search" not in found          # used, so not reported
    assert "code_interpreter" not in found    # disabled, so not reported
    assert "file_search_calls reports nothing" in found["file_search"]
    assert found["mcp"] == "enabled, and no usage endpoint counts it"
    assert unused_tools(None, None) == []
    assert unused_tools({"web_search": "not a block"}, {}) == []


def test_the_report_never_recommends_a_model_the_project_did_not_call():
    # This note owns the policy object. Which model suits the workload belongs
    # to a different note, and no repair line here may stray into it.
    for state in ("no-policy", "deny-list-empty", "deny-list-fails-open",
                  "allow-list-wider-than-use"):
        for line in repair_lines(state, "proj_a", USED):
            assert "cheaper" not in line and "mini" not in line.replace(
                "gpt-4.1-mini", "")
    empty = repair_lines("no-policy", "proj_idle", {})
    assert any("no observed set" in line for line in empty)
    used = fold_models([bucket({"project_id": "p", "model": "m",
                                "num_model_requests": 4}),
                        bucket({"project_id": "p", "model": "m",
                                "num_model_requests": 0})])
    assert used == {"p": {"m": 4}}
''',
"test_js_file": "openai-project-model-policy-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, foldModels, policyIds, policyState, repairLines, unrestricted,
         unusedAllowed, unusedTools } from './openai-project-model-policy-audit.mjs';

const USED = { 'gpt-4.1-mini': 41208 };

const bucket = (...results) =>
  ({ object: 'bucket', start_time: 0, end_time: 86400, results });

test('an absent policy and an empty deny list are two findings', () => {
  const [absentState, absentDetail] = classify(null, USED);
  const [emptyState, emptyDetail] = classify({ mode: 'deny_list', model_ids: [] }, USED);

  assert.equal(unrestricted(null), true);
  assert.equal(unrestricted({ mode: 'deny_list', model_ids: [] }), true);
  assert.equal(absentState, 'no-policy');
  assert.equal(emptyState, 'deny-list-empty');
  assert.ok(emptyDetail.includes('looks configured'));
  assert.ok(absentDetail.includes('reachable from this project'));

  const absentLines = repairLines(absentState, 'proj_demo', USED);
  const emptyLines = repairLines(emptyState, 'proj_batch', USED);
  assert.ok(absentLines.some((l) => l.includes('does not inherit')));
  assert.ok(emptyLines.some((l) => l.includes('did not finish it')));
  assert.notDeepEqual(absentLines, emptyLines);
});

test('a deny list with entries is restrictive today and open tomorrow', () => {
  const policy = { mode: 'deny_list', model_ids: ['gpt-4.1'] };
  assert.equal(unrestricted(policy), false);
  const [state, detail] = classify(policy, USED);
  assert.equal(state, 'deny-list-fails-open');
  assert.ok(detail.includes('released tomorrow'));
  assert.ok(repairLines(state, 'proj_x', USED)
    .some((l) => l.includes('does not exist yet')));
  assert.deepEqual(unusedAllowed(policy, USED), []);
});

test('an allow list wider than use names only what it measured', () => {
  const policy = { mode: 'allow_list',
                   model_ids: ['gpt-4.1-mini', 'gpt-4.1', 'o3', 'gpt-4.1-nano'] };
  const [state, detail] = classify(policy, USED, 30);
  assert.equal(state, 'allow-list-wider-than-use');
  assert.ok(detail.includes('names 4 model(s); 1 served any request'));
  assert.deepEqual(unusedAllowed(policy, USED), ['gpt-4.1', 'gpt-4.1-nano', 'o3']);
  const lines = repairLines(state, 'proj_web', USED);
  assert.ok(lines.some((l) => l.includes('["gpt-4.1-mini"]')));
  assert.ok(!lines.some((l) => l.includes('o3')));
  const tight = { mode: 'allow_list', model_ids: ['gpt-4.1-mini'] };
  assert.equal(classify(tight, USED)[0], 'restricted');
  assert.deepEqual(repairLines('restricted', 'proj_web', USED), []);
});

test('the policy shape reader handles every degenerate case', () => {
  assert.equal(policyState(null), 'absent');
  assert.equal(policyState(undefined), 'absent');
  assert.equal(policyState({ mode: 'allow_list', model_ids: [] }), 'allow-empty');
  assert.equal(policyState({ mode: 'allow_list', model_ids: ['  '] }), 'allow-empty');
  assert.equal(policyState({ mode: 'ALLOW_LIST', model_ids: ['a'] }), 'allow-list');
  assert.equal(policyState({ mode: 'something_new' }), 'unreadable');
  assert.deepEqual(policyIds({ model_ids: ['a', '', null, ' b '] }), ['a', 'b']);
  const [state, detail] = classify({ mode: 'allow_list', model_ids: [] }, USED);
  assert.equal(state, 'allow-list-empty');
  assert.ok(detail.includes('permits nothing'));
  assert.equal(classify({ mode: '?' }, USED)[0], 'policy-unreadable');
});

test('a tool with no usage endpoint is uncountable, not unused', () => {
  const perms = { code_interpreter: { enabled: false },
                  file_search: { enabled: true },
                  image_generation: { enabled: true },
                  mcp: { enabled: true },
                  web_search: { enabled: true } };
  const counts = { web_search: 4120, file_search: 0, image_generation: 0 };
  const found = Object.fromEntries(unusedTools(perms, counts));
  assert.equal(found.web_search, undefined);
  assert.equal(found.code_interpreter, undefined);
  assert.ok(found.file_search.includes('file_search_calls reports nothing'));
  assert.equal(found.mcp, 'enabled, and no usage endpoint counts it');
  assert.deepEqual(unusedTools(null, null), []);
  assert.deepEqual(unusedTools({ web_search: 'not a block' }, {}), []);
});

test('the report never recommends a model the project did not call', () => {
  for (const state of ['no-policy', 'deny-list-empty', 'deny-list-fails-open',
                       'allow-list-wider-than-use']) {
    for (const line of repairLines(state, 'proj_a', USED)) {
      assert.ok(!line.includes('cheaper'));
    }
  }
  assert.ok(repairLines('no-policy', 'proj_idle', {})
    .some((l) => l.includes('no observed set')));
  const used = foldModels([
    bucket({ project_id: 'p', model: 'm', num_model_requests: 4 }),
    bucket({ project_id: 'p', model: 'm', num_model_requests: 0 })]);
  assert.deepEqual(used, { p: { m: 4 } });
});
''',
"faq": [
 ("How is this different from the note about frontier models on trivial workloads?",
  "That note reads what was called and prices it: it is a spending finding about a usage pattern. This one reads the policy object and asks whether anything would have stopped the call. They meet at exactly one point — the list of models a project actually used — and they use it for opposite purposes. The other note uses it to say a model was overkill for the work. This one uses it only as raw material for a least-privilege allow list, and deliberately never says a model was the wrong choice. If the postmortem question is why did we spend that, read the other note. If it is what would have prevented it, this is the one."),
 ("Why is an empty deny list worse than no policy at all?",
  "Both permit every model, so the reachability is identical. The difference is what a human sees. A project with no policy shows as unconfigured, which is honest. A project with mode deny_list and an empty model_ids shows as having a model permissions policy, and anybody glancing at it — including whoever writes the next compliance answer — will conclude the control is in place. It is the most common way for this to look done. The script grades them as separate states with separate repairs because the follow-up conversation is different: one is a gap in project-creation automation, the other is a half-finished change with a person attached to it."),
 ("Is a deny list wrong?",
  "No, and the script does not say it is. A deny list is the right instrument when the requirement is genuinely to keep one named model out. What the report states plainly is its semantics: everything not on the list is permitted, including every model released after the policy was written, so its coverage of next quarter's catalogue is unconditional. That is a fine trade in some projects and a bad one in a project that exists to run one nightly job. Knowing which one you have is the value; the script names the shape and leaves the decision where it belongs."),
 ("Why not just check the hosted tools by looking at cost?",
  "Because cost cannot distinguish enabled-and-unused from disabled, and unused surface is the finding. A tool that is enabled and never called costs nothing, which is exactly why nobody turns it off, and which is why it is still available to anything holding a key for that project. So the script reads the permission object for the enabled flag and the matching usage endpoint for the count, and reports the pair. It also refuses to guess about mcp, which has no usage endpoint at all: that one is reported as enabled and uncountable, because calling zero evidence of usage zero usage would be inventing a measurement."),
 ("Can I run the repair the script prints?",
  "You can, and you should read it first. The printed body is an allow list built from exactly the models that project called in the window, which is a starting point rather than a policy: a project that ran a quarterly job outside the window will be missing a model it genuinely needs, and applying the list unread will break it on the next run. Widen the window, or add the model deliberately. The script does not execute the call under any flag, and the same applies to the hosted tool body it prints alongside."),
],
"related": [REL_FRONTIER, REL_SPEND_LIMIT, REL_WEBSEARCH],
"citations": [CITE_OA_ADMIN_GUIDE, CITE_OA_PROJECTS, CITE_OA_MODELS, CITE_OA_SDK],
},
{
"slug": "external-key-config-unattached",
"title": "A CMEK key config is inert but assumed to be encrypting",
"description": "attachment.type reads unattached, which the API describes as inert. Reconcile every external key config against the workspaces that actually name it.",
"h1": "A CMEK key config is inert but assumed to be encrypting",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic external key config unattached",
             "anthropic cmek customer managed key audit",
             "anthropic organizations external_keys api",
             "anthropic workspace external_key_id",
             "cmek key config attachment type"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key that can be provisioned read-only. The external keys endpoint is a beta surface and is only present for organizations with CMEK enabled; the script reports that rather than treating it as a finding.",
"lead": "The answer in the security questionnaire is a single sentence and it took three weeks of work to be able to write it: customer data is encrypted at rest under a key we control, in our own KMS, which we can revoke. The engineer who did that work created the key, registered it, and moved on to the next ticket, because from the outside everything looked done &mdash; the config was there, it had the right ARN, the console showed it. What nobody did was the second step, and there is no error anywhere that says so, because an encryption config that is not attached to anything does not fail. It just is not used.",
"short_answer": """<p>Two listings with an <strong>Admin API key</strong>, on a <strong>beta</strong> surface. <code>GET /v1/organizations/external_keys?beta=true&amp;limit=100</code> returns CMEK external key configs, each carrying <code>id</code>, <code>display_name</code>, <code>geo</code>, <code>created_at</code>, a <code>provider_config</code> discriminated on <code>aws</code> / <code>gcp</code> / <code>azure</code>, and an <code>attachment</code> whose <code>type</code> is <code>"attached"</code> or <code>"unattached"</code>.</p>
<p><strong><code>unattached</code> is the finding, and the API's own documentation is unusually direct about it: an unattached config is inert and can be deleted.</strong> It participates in no encryption path. Nothing on the inference path signals which key, if any, is protecting a workspace, so a half-finished CMEK rollout leaves behind exactly this &mdash; an object that exists, looks correct, and does nothing.</p>
<p>The attachment object carries only its type. To find out <em>what</em> is covered you need the other listing: <code>GET /v1/organizations/workspaces?beta=true&amp;limit=100&amp;include_archived=true</code>, where each workspace carries <code>external_key_id</code> (write-once: once attached it cannot be detached or replaced) and a <code>data_residency</code> block with <code>workspace_geo</code>. Reconcile the two, and check the config's <code>geo</code> against the <code>workspace_geo</code> of everything it covers.</p>
<p>The script never calls <code>POST /v1/organizations/external_keys/{id}/validate</code>. It exists, it would be the obvious thing to reach for, and it is a write verb on a read-only audit.</p>""",
"problem": """<p>Creating a key config and attaching it are two separate steps, and only the second one does anything. The first is the visible one: it involves the KMS side, the ARN, the key policy, a colleague from the platform team. The second is a field on a workspace, and it is easy to believe it happened because everything else did.</p>
<p>Nothing downstream contradicts the belief. Requests succeed either way. The console shows the config. The usage reports say nothing about encryption. And the claim itself lives in a document rather than in a system, so the only thing that could catch the gap is somebody deciding, unprompted, to go and read an admin endpoint about a control that has never failed.</p>
<p>The mirror image is worse in a different way. A config that <em>is</em> attached, to a workspace that was archived eighteen months ago, is still holding that workspace's retained data. It looks abandoned, it is not, and the KMS key underneath it is a candidate for the next rotation-and-cleanup sweep. Deleting a config that an archived workspace depends on makes that data unrecoverable, and nothing about the config's appearance in a list tells you which of the two situations you are in.</p>""",
"why": """<p><strong>Two listings, two different authorities, and the script says which is which.</strong> <code>attachment.type</code> is authoritative for one question only: does any workspace, live or archived, use this config. It carries no workspace list, so it cannot tell you what is covered. The workspace listing answers that, through <code>external_key_id</code> &mdash; but only for workspaces this key can see. So <code>unattached</code> is trustworthy as a statement that nothing uses the config, and the workspace scan is trustworthy as a statement about coverage, and the script never lets one stand in for the other. When they disagree &mdash; the config says unattached while a workspace names it &mdash; that is its own state, and the repair refuses to delete anything.</p>
<p><strong><code>external_key_id</code> is write-once, which changes what a repair can even say.</strong> Once a key is attached to a workspace it cannot be detached or replaced; rotating key material means rotating the underlying KMS key while the <code>external_key_id</code> stays the same. That rules out the obvious-sounding fix for a geo or coverage mismatch, which is to point the workspace at a different config. The script does not suggest it, because it is not possible, and a report that recommends an impossible action is worse than one that says the option is closed.</p>
<p><strong>The uncovered workspaces are a separate count, and it is the one the questionnaire is actually about.</strong> A config being attached tells you something is encrypted. It tells you nothing about the workspace that has no <code>external_key_id</code> at all, which is the surface not under CMEK. That is reported as one line with a count and a list, not as a finding per workspace, because in an organization mid-rollout it would otherwise drown everything else.</p>
<p><strong>This is a beta surface on a narrow enterprise feature, and the script is explicit about that.</strong> The endpoint sits behind <code>?beta=true</code> and is only present for organizations with CMEK enabled. A 403 or 404 means the feature is not enabled for your organization, which is not a finding &mdash; it is an answer, and the script prints it as one and exits rather than reporting an empty list as if everything were clean. The same honesty applies to the id format: a config id is normally prefixed <code>ekey_</code>, but for organizations on the Claude Platform on AWS it is the KMS key ARN itself.</p>""",
"steps": [
 {"h": "Use an Admin API key, provisioned read-only",
  "body": """<p>Every <code>/v1/organizations/*</code> path rejects a workspace key. Set <code>ANTHROPIC_ADMIN_KEY</code> in the environment; the script never prints it and never sends anything but GETs.</p>"""},
 {"h": "List the external key configs, and handle not-enabled as an answer",
  "body": """<p><code>GET /v1/organizations/external_keys?beta=true&amp;limit=100</code>, paginated on <code>next_page</code> via the <code>page</code> parameter. A 403 or 404 means CMEK is not enabled for this organization. Say so and stop; an empty list from a feature you do not have is not a clean audit.</p>"""},
 {"h": "List the workspaces, including archived ones",
  "body": """<p><code>GET /v1/organizations/workspaces?beta=true&amp;limit=100&amp;include_archived=true</code>, paginated on <code>after_id</code> &mdash; a different cursor from the one the key listing uses, in the same script. Archived workspaces matter most here: their data is still encrypted under whatever config they name.</p>"""},
 {"h": "Reconcile, and keep the two authorities separate",
  "body": """<p>Build the coverage map from <code>external_key_id</code> on the workspaces. Compare it against <code>attachment.type</code> on the configs. Agreement is the common case; disagreement in either direction is its own state, and neither one is resolved by trusting whichever listing you read first.</p>"""},
 {"h": "Check geo, count the uncovered, and print the repair",
  "body": """<p>The config's <code>geo</code> against each covered workspace's <code>data_residency.workspace_geo</code>. Then one line for the workspaces with no <code>external_key_id</code> at all. The repair prints the attach step for a human to run and the delete call for a genuinely inert config &mdash; and refuses to print a delete for anything attached.</p>"""},
],
"verify": """<p>Attach the config to the workspace it was made for, then re-run. That config moves from <code>unattached-and-unused</code> to <code>covered</code>, and the uncovered-workspace count falls by one. It will not move back: <code>external_key_id</code> is write-once, so the verification is one-way and worth getting right the first time. For a config the script reports as inert, delete it in the console and confirm it disappears from the listing rather than reappearing as attached, which would mean the attachment was to something the admin key cannot enumerate.</p>
<pre><code class="language-bash">python3 anthropic_cmek_external_key_audit.py --geo eu
# 3 external key config(s), 7 workspace(s), 2 finding(s)
# unattached-and-unused    ekey_01hq  EU customer key
#   attachment.type is unattached and no workspace names it. The API describes
#   this state as inert: it takes part in no encryption path.
#   provider: aws arn:aws:kms:eu-west-1:****:key/9f2c
#   repair: attach it to the workspace it was made for. Attachment is the step
#           that makes a config live; creating it is not.
#   repair: if it was superseded, it can be deleted. Nothing depends on it.
# archived-workspaces-only ekey_01gd  Legacy tenant key
#   attached, and the only workspaces naming it are archived (wrk_04). Their
#   retained data is still encrypted under this config.
#   repair: do not delete this. Deleting a config an archived workspace depends
#           on makes that workspace's retained data unrecoverable.
# uncovered: 4 of 7 workspace(s) have no external_key_id at all (wrk_01, wrk_02,
#            wrk_05, wrk_06)</code></pre>""",
"code_intro": "Two paged GETs with two different cursors, and six pure functions. The attachment reader, which refuses to guess at an unrecognised discriminator; the KMS reference formatter, which produces one short line per provider and masks the AWS account id inside an ARN; the coverage map, built from the workspaces because the attachment object carries no workspace list; the uncovered split, which separates live from archived; the geo comparison; and the classifier, which has a state for each direction of disagreement between the two listings and prints a delete for exactly one of the six outcomes.",
"py_file": "anthropic_cmek_external_key_audit.py",
"py": '''"""Find Anthropic CMEK key configs that are not encrypting anything.

Read only. Two paged GETs against /v1/organizations/external_keys and
/v1/organizations/workspaces with an Admin API key. Every request is a GET.

The external keys resource offers a validate call. It is a write verb, so this
script does not use it, and the repair for an unattached config is printed for
a human to run rather than performed.

Nothing secret is printed. Provider coordinates are resource identifiers rather
than credentials, and the AWS account id inside an ARN is masked anyway.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_cmek_external_key_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

FINDINGS = ("unattached-and-unused", "unattached-but-referenced",
            "archived-workspaces-only", "attached-nothing-visible",
            "geo-mismatch", "attachment-unreadable")

SEVERITY = {"unattached-and-unused": 0, "geo-mismatch": 1,
            "unattached-but-referenced": 2, "attached-nothing-visible": 3,
            "archived-workspaces-only": 4, "attachment-unreadable": 5}


def attachment_type(key):
    """"attached" / "unattached" / "unknown". Pure.

    Anything else is unknown rather than assumed unattached: guessing wrong in
    that direction produces a report telling somebody to delete a live key.
    """
    kind = str(((key or {}).get("attachment") or {}).get("type") or "").strip().lower()
    return kind if kind in ("attached", "unattached") else "unknown"


def mask_arn(arn):
    """Hide the account id in an AWS ARN. Pure. Non-ARNs pass through."""
    text = str(arn or "")
    parts = text.split(":")
    if len(parts) < 6 or parts[0] != "arn":
        return text or "unknown"
    parts[4] = "****"
    return ":".join(parts)


def kms_ref(provider_config):
    """One short line naming the KMS key. Pure. No credentials, ever."""
    cfg = provider_config or {}
    kind = str(cfg.get("type") or "").strip().lower()
    if kind == "aws":
        return "aws " + mask_arn(cfg.get("kms_arn"))
    if kind == "gcp":
        return "gcp " + str(cfg.get("key_name") or "unknown")
    if kind == "azure":
        return "azure %s in %s" % (cfg.get("key_name") or "unknown",
                                   cfg.get("vault_uri") or "unknown vault")
    return "unrecognised provider %s" % (kind or "none")


def workspace_geo(workspace):
    """The workspace's storage geo, or None. Pure."""
    geo = ((workspace or {}).get("data_residency") or {}).get("workspace_geo")
    return str(geo) if geo else None


def coverage(workspaces):
    """{external_key_id: {"live": [ids], "archived": [ids]}}. Pure.

    Built from the workspaces, because the attachment object carries only its
    own type and no list of what uses it.
    """
    out = {}
    for workspace in workspaces or []:
        row = workspace or {}
        key_id = row.get("external_key_id")
        if not key_id:
            continue
        entry = out.setdefault(str(key_id), {"live": [], "archived": []})
        bucket = "archived" if row.get("archived_at") else "live"
        entry[bucket].append(str(row.get("id") or "unknown"))
    for entry in out.values():
        entry["live"].sort()
        entry["archived"].sort()
    return out


def uncovered(workspaces):
    """(live, archived) workspace ids with no external_key_id at all. Pure."""
    live, archived = [], []
    for workspace in workspaces or []:
        row = workspace or {}
        if row.get("external_key_id"):
            continue
        (archived if row.get("archived_at") else live).append(
            str(row.get("id") or "unknown"))
    return (sorted(live), sorted(archived))


def classify(key, cover, geos):
    """Classify one key config. Pure. Returns (state, detail).

    cover: {"live": [ids], "archived": [ids]} from the workspace listing.
    geos:  [(workspace_id, workspace_geo)] for the workspaces that name it.
    """
    kind = attachment_type(key)
    live = list((cover or {}).get("live") or [])
    archived = list((cover or {}).get("archived") or [])

    if kind == "unknown":
        return ("attachment-unreadable",
                "attachment.type is not attached or unattached, so this audit "
                "will not say whether the config is in use")

    if kind == "unattached":
        if live or archived:
            return ("unattached-but-referenced",
                    "the config reports unattached while %d workspace(s) name it "
                    "(%s). The two listings disagree"
                    % (len(live) + len(archived), ", ".join(live + archived)))
        return ("unattached-and-unused",
                "attachment.type is unattached and no workspace names it. The API "
                "describes this state as inert: it takes part in no encryption "
                "path")

    if not live and not archived:
        return ("attached-nothing-visible",
                "reported attached, and no workspace this key can enumerate names "
                "it. An attachment you cannot see is still an attachment")
    if not live:
        return ("archived-workspaces-only",
                "attached, and the only workspaces naming it are archived (%s). "
                "Their retained data is still encrypted under this config"
                % ", ".join(archived))

    want = str((key or {}).get("geo") or "")
    mismatched = [(w, g) for w, g in (geos or []) if g and want and str(g) != want]
    if mismatched:
        return ("geo-mismatch",
                "config geo is %s and it covers %s"
                % (want, ", ".join("%s at %s" % pair for pair in mismatched)))

    return ("covered",
            "attached, covering %d live workspace(s)%s"
            % (len(live), " and %d archived" % len(archived) if archived else ""))


def repair_lines(state, key):
    """The repair for one key config. Pure. Printed, never performed.

    A delete is printed for exactly one state. external_key_id is write-once on
    a workspace, so no repair here proposes re-pointing a workspace at a
    different config: that is not something the API allows.
    """
    key_id = str((key or {}).get("id") or "unknown")
    lines = []
    if state not in FINDINGS:
        return lines
    if state == "unattached-and-unused":
        lines.append("attach it to the workspace it was made for. Attachment is "
                     "the step that makes a config live; creating it is not.")
        lines.append("if it was superseded, it can be deleted: DELETE "
                     "/v1/organizations/external_keys/%s. Nothing depends on it."
                     % key_id)
    elif state == "unattached-but-referenced":
        lines.append("do not delete this. Two listings disagree, and the safe "
                     "reading is the one that says something is using it.")
    elif state == "archived-workspaces-only":
        lines.append("do not delete this. Deleting a config an archived workspace "
                     "depends on makes that workspace's retained data "
                     "unrecoverable.")
    elif state == "attached-nothing-visible":
        lines.append("the coverage map is incomplete rather than empty. Widen the "
                     "workspace listing before concluding anything about this "
                     "config.")
    elif state == "geo-mismatch":
        lines.append("a workspace cannot be re-pointed: external_key_id is "
                     "write-once and cannot be detached or replaced. Resolve this "
                     "against the residency commitment, not by swapping keys.")
    else:
        lines.append("read this config by hand. The attachment discriminator was "
                     "not one of the two values this audit recognises.")
    lines.append("the validate call on this resource is a write verb and this "
                 "script does not use it. Run it deliberately if you need it.")
    return lines


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401,):
        raise SystemExit("401 from Anthropic: /v1/organizations/* needs an Admin "
                         "API key, not a workspace key")
    if r.status_code in (403, 404):
        return None
    r.raise_for_status()
    return r.json()


def paged_cursor(session, path, **params):
    """external_keys pagination: next_page fed back as the page parameter."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        if page is None:
            return
        for item in page.get("data") or []:
            yield item
        cursor = page.get("next_page")
        if not page.get("has_more") or not cursor:
            return
        params = dict(params, page=cursor)


def paged_after_id(session, path, **params):
    """workspaces pagination: after_id, a different cursor in the same script."""
    params = dict(params)
    while True:
        page = get(session, path, params) or {}
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after_id"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--geo", default=None,
                    help="the storage geo your residency commitment claims")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key; a workspace key "
                  "cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    keys = list(paged_cursor(s, "/organizations/external_keys",
                             beta="true", limit=100))
    if not keys:
        probe = get(s, "/organizations/external_keys", {"beta": "true", "limit": 1})
        if probe is None:
            log.info("the external keys endpoint is not available to this "
                     "organization. CMEK is a beta enterprise feature and this is "
                     "an answer, not a finding.")
            return 0

    workspaces = list(paged_after_id(s, "/organizations/workspaces",
                                     beta="true", limit=100,
                                     include_archived="true"))
    cover = coverage(workspaces)
    by_id = {str((w or {}).get("id")): w for w in workspaces}

    findings = []
    for key in keys:
        key_id = str(key.get("id") or "")
        entry = cover.get(key_id) or {}
        geos = [(w, workspace_geo(by_id.get(w)))
                for w in (entry.get("live") or []) + (entry.get("archived") or [])]
        state, detail = classify(key, entry, geos)
        if state in FINDINGS:
            findings.append((key, state, detail))

    live_bare, archived_bare = uncovered(workspaces)

    log.info("%d external key config(s), %d workspace(s), %d finding(s)",
             len(keys), len(workspaces), len(findings))

    findings.sort(key=lambda r: (SEVERITY.get(r[1], 9), str(r[0].get("id") or "")))
    for key, state, detail in findings:
        log.warning("%-26s %-12s %s", state, key.get("id"),
                    key.get("display_name") or "(unnamed)")
        log.warning("  %s", detail)
        log.warning("  provider: %s", kms_ref(key.get("provider_config")))
        for line in repair_lines(state, key):
            log.warning("  repair: %s", line)

    if live_bare:
        log.warning("uncovered: %d of %d workspace(s) have no external_key_id at "
                    "all (%s)", len(live_bare), len(workspaces),
                    ", ".join(live_bare))
    if archived_bare:
        log.info("uncovered and archived: %d workspace(s) (%s)",
                 len(archived_bare), ", ".join(archived_bare))
    if args.geo:
        log.info("claimed storage geo: %s", args.geo)
        for workspace in workspaces:
            got = workspace_geo(workspace)
            if got and got != args.geo:
                log.warning("residency  %-12s workspace_geo is %s, and %s was "
                            "claimed", workspace.get("id"), got, args.geo)

    return 1 if (findings or live_bare) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-cmek-external-key-audit.mjs",
"js": '''/**
 * Find Anthropic CMEK key configs that are not encrypting anything.
 *
 * Read only. Two paged GETs against /v1/organizations/external_keys and
 * /v1/organizations/workspaces with an Admin API key.
 *
 * The external keys resource offers a validate call. It is a write verb, so
 * this script does not use it. Provider coordinates are resource identifiers
 * rather than credentials, and the AWS account id inside an ARN is masked.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const FINDINGS = new Set(['unattached-and-unused', 'unattached-but-referenced',
                          'archived-workspaces-only', 'attached-nothing-visible',
                          'geo-mismatch', 'attachment-unreadable']);

const SEVERITY = { 'unattached-and-unused': 0, 'geo-mismatch': 1,
                   'unattached-but-referenced': 2, 'attached-nothing-visible': 3,
                   'archived-workspaces-only': 4, 'attachment-unreadable': 5 };

/** "attached" / "unattached" / "unknown". Pure. Never guesses. */
export function attachmentType(key) {
  const kind = String(key?.attachment?.type ?? '').trim().toLowerCase();
  return (kind === 'attached' || kind === 'unattached') ? kind : 'unknown';
}

/** Hide the account id in an AWS ARN. Pure. Non-ARNs pass through. */
export function maskArn(arn) {
  const text = String(arn ?? '');
  const parts = text.split(':');
  if (parts.length < 6 || parts[0] !== 'arn') return text || 'unknown';
  parts[4] = '****';
  return parts.join(':');
}

/** One short line naming the KMS key. Pure. No credentials, ever. */
export function kmsRef(providerConfig) {
  const cfg = providerConfig ?? {};
  const kind = String(cfg.type ?? '').trim().toLowerCase();
  if (kind === 'aws') return `aws ${maskArn(cfg.kms_arn)}`;
  if (kind === 'gcp') return `gcp ${cfg.key_name ?? 'unknown'}`;
  if (kind === 'azure') {
    return `azure ${cfg.key_name ?? 'unknown'} in ${cfg.vault_uri ?? 'unknown vault'}`;
  }
  return `unrecognised provider ${kind || 'none'}`;
}

/** The workspace's storage geo, or null. Pure. */
export function workspaceGeo(workspace) {
  const geo = workspace?.data_residency?.workspace_geo;
  return geo ? String(geo) : null;
}

/** {external_key_id: {live: [], archived: []}}. Pure. Built from workspaces. */
export function coverage(workspaces) {
  const out = {};
  for (const workspace of workspaces ?? []) {
    const keyId = workspace?.external_key_id;
    if (!keyId) continue;
    const entry = (out[String(keyId)] ??= { live: [], archived: [] });
    entry[workspace?.archived_at ? 'archived' : 'live']
      .push(String(workspace?.id ?? 'unknown'));
  }
  for (const entry of Object.values(out)) {
    entry.live.sort();
    entry.archived.sort();
  }
  return out;
}

/** [live, archived] workspace ids with no external_key_id at all. Pure. */
export function uncovered(workspaces) {
  const live = [];
  const archived = [];
  for (const workspace of workspaces ?? []) {
    if (workspace?.external_key_id) continue;
    (workspace?.archived_at ? archived : live).push(String(workspace?.id ?? 'unknown'));
  }
  return [live.sort(), archived.sort()];
}

/** Classify one key config. Pure. Returns [state, detail]. */
export function classify(key, cover, geos) {
  const kind = attachmentType(key);
  const live = [...(cover?.live ?? [])];
  const archived = [...(cover?.archived ?? [])];

  if (kind === 'unknown') {
    return ['attachment-unreadable',
            'attachment.type is not attached or unattached, so this audit will '
            + 'not say whether the config is in use'];
  }
  if (kind === 'unattached') {
    if (live.length || archived.length) {
      return ['unattached-but-referenced',
              `the config reports unattached while ${live.length + archived.length} `
              + `workspace(s) name it (${[...live, ...archived].join(', ')}). The two `
              + 'listings disagree'];
    }
    return ['unattached-and-unused',
            'attachment.type is unattached and no workspace names it. The API '
            + 'describes this state as inert: it takes part in no encryption path'];
  }
  if (!live.length && !archived.length) {
    return ['attached-nothing-visible',
            'reported attached, and no workspace this key can enumerate names it. '
            + 'An attachment you cannot see is still an attachment'];
  }
  if (!live.length) {
    return ['archived-workspaces-only',
            `attached, and the only workspaces naming it are archived `
            + `(${archived.join(', ')}). Their retained data is still encrypted `
            + 'under this config'];
  }
  const want = String(key?.geo ?? '');
  const mismatched = (geos ?? []).filter(([, g]) => g && want && String(g) !== want);
  if (mismatched.length) {
    return ['geo-mismatch',
            `config geo is ${want} and it covers `
            + mismatched.map(([w, g]) => `${w} at ${g}`).join(', ')];
  }
  return ['covered',
          `attached, covering ${live.length} live workspace(s)`
          + (archived.length ? ` and ${archived.length} archived` : '')];
}

/** The repair for one key config. Pure. Printed, never performed. */
export function repairLines(state, key) {
  const keyId = String(key?.id ?? 'unknown');
  const lines = [];
  if (!FINDINGS.has(state)) return lines;
  if (state === 'unattached-and-unused') {
    lines.push('attach it to the workspace it was made for. Attachment is the step '
      + 'that makes a config live; creating it is not.');
    lines.push('if it was superseded, it can be deleted: DELETE '
      + `/v1/organizations/external_keys/${keyId}. Nothing depends on it.`);
  } else if (state === 'unattached-but-referenced') {
    lines.push('do not delete this. Two listings disagree, and the safe reading is '
      + 'the one that says something is using it.');
  } else if (state === 'archived-workspaces-only') {
    lines.push('do not delete this. Deleting a config an archived workspace depends '
      + "on makes that workspace's retained data unrecoverable.");
  } else if (state === 'attached-nothing-visible') {
    lines.push('the coverage map is incomplete rather than empty. Widen the '
      + 'workspace listing before concluding anything about this config.');
  } else if (state === 'geo-mismatch') {
    lines.push('a workspace cannot be re-pointed: external_key_id is write-once and '
      + 'cannot be detached or replaced. Resolve this against the residency '
      + 'commitment, not by swapping keys.');
  } else {
    lines.push('read this config by hand. The attachment discriminator was not one '
      + 'of the two values this audit recognises.');
  }
  lines.push('the validate call on this resource is a write verb and this script '
    + 'does not use it. Run it deliberately if you need it.');
  return lines;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (r.status === 401) {
    throw new Error('401 from Anthropic: /v1/organizations/* needs an Admin API '
                    + 'key, not a workspace key');
  }
  if (r.status === 403 || r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function pagedCursor(key, path, params) {
  const out = [];
  let q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
    if (page === null) return out;
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) return out;
    q = { ...q, page: page.next_page };
  }
}

async function pagedAfterId(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = (await read(key, path, q)) ?? {};
    const data = page.data ?? [];
    out.push(...data);
    if (!page.has_more || data.length === 0) return out;
    q.after_id = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key; a workspace key '
                  + 'cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const wantGeo = process.env.GEO ?? null;

  const keys = await pagedCursor(admin, '/organizations/external_keys',
                                 { beta: 'true', limit: 100 });
  if (!keys.length) {
    const probe = await read(admin, '/organizations/external_keys',
                             { beta: 'true', limit: 1 });
    if (probe === null) {
      console.log('the external keys endpoint is not available to this '
        + 'organization. CMEK is a beta enterprise feature and this is an answer, '
        + 'not a finding.');
      return;
    }
  }

  const workspaces = await pagedAfterId(admin, '/organizations/workspaces',
    { beta: 'true', limit: 100, include_archived: 'true' });
  const cover = coverage(workspaces);
  const byId = Object.fromEntries(workspaces.map((w) => [String(w?.id), w]));

  const findings = [];
  for (const key of keys) {
    const entry = cover[String(key.id ?? '')] ?? {};
    const geos = [...(entry.live ?? []), ...(entry.archived ?? [])]
      .map((w) => [w, workspaceGeo(byId[w])]);
    const [state, detail] = classify(key, entry, geos);
    if (FINDINGS.has(state)) findings.push([key, state, detail]);
  }

  const [liveBare, archivedBare] = uncovered(workspaces);

  console.log(`${keys.length} external key config(s), ${workspaces.length} `
              + `workspace(s), ${findings.length} finding(s)`);

  findings.sort(([ka, sa], [kb, sb]) =>
    (SEVERITY[sa] ?? 9) - (SEVERITY[sb] ?? 9)
    || String(ka.id ?? '').localeCompare(String(kb.id ?? '')));

  for (const [key, state, detail] of findings) {
    console.warn(`${state.padEnd(26)} ${String(key.id).padEnd(12)} `
                 + `${key.display_name ?? '(unnamed)'}`);
    console.warn(`  ${detail}`);
    console.warn(`  provider: ${kmsRef(key.provider_config)}`);
    for (const line of repairLines(state, key)) console.warn(`  repair: ${line}`);
  }

  if (liveBare.length) {
    console.warn(`uncovered: ${liveBare.length} of ${workspaces.length} workspace(s) `
                 + `have no external_key_id at all (${liveBare.join(', ')})`);
  }
  if (archivedBare.length) {
    console.log(`uncovered and archived: ${archivedBare.length} workspace(s) `
                + `(${archivedBare.join(', ')})`);
  }
  if (wantGeo) {
    console.log(`claimed storage geo: ${wantGeo}`);
    for (const workspace of workspaces) {
      const got = workspaceGeo(workspace);
      if (got && got !== wantGeo) {
        console.warn(`residency  ${String(workspace.id).padEnd(12)} workspace_geo `
                     + `is ${got}, and ${wantGeo} was claimed`);
      }
    }
  }
  process.exitCode = (findings.length || liveBare.length) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is two configs that look identical in a listing and are opposites underneath: neither is named by any live workspace, one is <code>unattached</code> and inert, the other is <code>attached</code> to an archived workspace whose retained data depends on it. Only one of the two repairs is allowed to contain a delete, and the test asserts that directly, because getting it backwards destroys data. Then: the two listings disagreeing, where the safe reading wins; an unrecognised attachment discriminator, which is never assumed to mean unattached; the geo comparison across covered workspaces; the coverage map and the uncovered split, where a <code>null</code> <code>external_key_id</code> must not become a key id called <code>null</code>; and the ARN mask.",
"test_py_file": "test_anthropic_cmek_external_key_audit.py",
"test_py": '''from anthropic_cmek_external_key_audit import (attachment_type, classify,
                                                coverage, kms_ref, mask_arn,
                                                repair_lines, uncovered,
                                                workspace_geo)

ARN = "arn:aws:kms:eu-west-1:210987654321:key/9f2c"


def key(kid, kind="unattached", geo="eu", name="EU customer key"):
    return {"id": kid, "type": "external_key", "display_name": name, "geo": geo,
            "attachment": {"type": kind},
            "provider_config": {"type": "aws", "kms_arn": ARN}}


def workspace(wid, key_id=None, geo="eu", archived=None):
    return {"id": wid, "type": "workspace", "name": wid,
            "external_key_id": key_id, "archived_at": archived,
            "data_residency": {"workspace_geo": geo,
                               "default_inference_geo": geo,
                               "allowed_inference_geos": "unrestricted"}}


def test_two_configs_with_no_live_workspace_and_only_one_may_be_deleted():
    # The note, and the most dangerous thing in it. Neither config covers a live
    # workspace. One is inert; deleting the other destroys retained data.
    inert = key("ekey_01hq", "unattached")
    holding = key("ekey_01gd", "attached", name="Legacy tenant key")
    cover = coverage([workspace("wrk_04", "ekey_01gd", archived=1_700_000_000)])

    state_a, detail_a = classify(inert, cover.get("ekey_01hq"), [])
    assert state_a == "unattached-and-unused"
    assert "inert" in detail_a

    state_b, detail_b = classify(holding, cover.get("ekey_01gd"),
                                 [("wrk_04", "eu")])
    assert state_b == "archived-workspaces-only"
    assert "still encrypted under this config" in detail_b

    lines_a = repair_lines(state_a, inert)
    lines_b = repair_lines(state_b, holding)
    assert any("can be deleted" in line for line in lines_a)
    assert not any("can be deleted" in line for line in lines_b)
    assert any("unrecoverable" in line for line in lines_b)


def test_when_the_two_listings_disagree_the_safe_reading_wins():
    stale = key("ekey_01zz", "unattached")
    cover = coverage([workspace("wrk_09", "ekey_01zz")])
    state, detail = classify(stale, cover.get("ekey_01zz"), [("wrk_09", "eu")])
    assert state == "unattached-but-referenced"
    assert "The two listings disagree" in detail
    lines = repair_lines(state, stale)
    assert any("do not delete this" in line for line in lines)
    assert not any("can be deleted" in line for line in lines)


def test_an_unrecognised_attachment_is_never_assumed_unattached():
    assert attachment_type(key("e", "attached")) == "attached"
    assert attachment_type(key("e", "UNATTACHED")) == "unattached"
    assert attachment_type({"id": "e", "attachment": {"type": "pending"}}) == "unknown"
    assert attachment_type({"id": "e"}) == "unknown"
    assert attachment_type(None) == "unknown"
    state, detail = classify({"id": "e", "attachment": {"type": "pending"}}, {}, [])
    assert state == "attachment-unreadable"
    assert "will not say whether" in detail


def test_a_geo_mismatch_is_read_across_the_workspaces_it_covers():
    eu_key = key("ekey_01eu", "attached", geo="eu")
    cover = coverage([workspace("wrk_01", "ekey_01eu", geo="eu"),
                      workspace("wrk_02", "ekey_01eu", geo="us")])
    geos = [("wrk_01", "eu"), ("wrk_02", "us")]
    state, detail = classify(eu_key, cover.get("ekey_01eu"), geos)
    assert state == "geo-mismatch"
    assert "wrk_02 at us" in detail
    assert "wrk_01" not in detail
    assert any("write-once" in line for line in repair_lines(state, eu_key))
    # Matching geos are simply covered.
    assert classify(eu_key, cover.get("ekey_01eu"),
                    [("wrk_01", "eu")])[0] == "covered"
    assert repair_lines("covered", eu_key) == []


def test_the_coverage_map_and_the_uncovered_split():
    rows = [workspace("wrk_01"), workspace("wrk_02", None),
            workspace("wrk_03", "ekey_01hq"),
            workspace("wrk_04", "ekey_01hq", archived=1_700_000_000),
            workspace("wrk_05", None, archived=1_700_000_001)]
    cover = coverage(rows)
    assert cover == {"ekey_01hq": {"live": ["wrk_03"], "archived": ["wrk_04"]}}
    # A null external_key_id must never become a key id.
    assert "None" not in cover and None not in cover
    assert uncovered(rows) == (["wrk_01", "wrk_02"], ["wrk_05"])
    assert coverage(None) == {}
    assert uncovered(None) == ([], [])
    assert workspace_geo(rows[0]) == "eu"
    assert workspace_geo({"id": "w"}) is None


def test_the_provider_line_names_the_key_and_masks_the_account():
    assert mask_arn(ARN) == "arn:aws:kms:eu-west-1:****:key/9f2c"
    assert mask_arn("not-an-arn") == "not-an-arn"
    assert mask_arn(None) == "unknown"
    assert kms_ref({"type": "aws", "kms_arn": ARN}).startswith("aws arn:aws:kms:")
    assert "210987654321" not in kms_ref({"type": "aws", "kms_arn": ARN})
    assert kms_ref({"type": "gcp", "key_name": "projects/p/locations/eu/x"}) == \\
        "gcp projects/p/locations/eu/x"
    assert "vault.azure.net" in kms_ref(
        {"type": "azure", "key_name": "k", "vault_uri": "https://v.vault.azure.net"})
    assert kms_ref({"type": "quantum"}) == "unrecognised provider quantum"
    assert kms_ref(None) == "unrecognised provider none"
    # Every finding says the validate call was deliberately not made.
    assert any("write verb" in line
               for line in repair_lines("unattached-and-unused", key("ekey_1")))
''',
"test_js_file": "anthropic-cmek-external-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attachmentType, classify, coverage, kmsRef, maskArn, repairLines,
         uncovered, workspaceGeo } from './anthropic-cmek-external-key-audit.mjs';

const ARN = 'arn:aws:kms:eu-west-1:210987654321:key/9f2c';

const key = (id, kind = 'unattached', geo = 'eu', name = 'EU customer key') =>
  ({ id, type: 'external_key', display_name: name, geo,
     attachment: { type: kind },
     provider_config: { type: 'aws', kms_arn: ARN } });

const workspace = (id, keyId = null, geo = 'eu', archived = null) =>
  ({ id, type: 'workspace', name: id, external_key_id: keyId,
     archived_at: archived,
     data_residency: { workspace_geo: geo, default_inference_geo: geo,
                       allowed_inference_geos: 'unrestricted' } });

test('two configs with no live workspace, and only one may be deleted', () => {
  const inert = key('ekey_01hq', 'unattached');
  const holding = key('ekey_01gd', 'attached', 'eu', 'Legacy tenant key');
  const cover = coverage([workspace('wrk_04', 'ekey_01gd', 'eu', 1700000000)]);

  const [stateA, detailA] = classify(inert, cover.ekey_01hq, []);
  assert.equal(stateA, 'unattached-and-unused');
  assert.ok(detailA.includes('inert'));

  const [stateB, detailB] = classify(holding, cover.ekey_01gd, [['wrk_04', 'eu']]);
  assert.equal(stateB, 'archived-workspaces-only');
  assert.ok(detailB.includes('still encrypted under this config'));

  const linesA = repairLines(stateA, inert);
  const linesB = repairLines(stateB, holding);
  assert.ok(linesA.some((l) => l.includes('can be deleted')));
  assert.ok(!linesB.some((l) => l.includes('can be deleted')));
  assert.ok(linesB.some((l) => l.includes('unrecoverable')));
});

test('when the two listings disagree the safe reading wins', () => {
  const stale = key('ekey_01zz', 'unattached');
  const cover = coverage([workspace('wrk_09', 'ekey_01zz')]);
  const [state, detail] = classify(stale, cover.ekey_01zz, [['wrk_09', 'eu']]);
  assert.equal(state, 'unattached-but-referenced');
  assert.ok(detail.includes('The two listings disagree'));
  const lines = repairLines(state, stale);
  assert.ok(lines.some((l) => l.includes('do not delete this')));
  assert.ok(!lines.some((l) => l.includes('can be deleted')));
});

test('an unrecognised attachment is never assumed unattached', () => {
  assert.equal(attachmentType(key('e', 'attached')), 'attached');
  assert.equal(attachmentType(key('e', 'UNATTACHED')), 'unattached');
  assert.equal(attachmentType({ id: 'e', attachment: { type: 'pending' } }), 'unknown');
  assert.equal(attachmentType({ id: 'e' }), 'unknown');
  assert.equal(attachmentType(null), 'unknown');
  const [state, detail] = classify({ id: 'e', attachment: { type: 'pending' } }, {}, []);
  assert.equal(state, 'attachment-unreadable');
  assert.ok(detail.includes('will not say whether'));
});

test('a geo mismatch is read across the workspaces it covers', () => {
  const euKey = key('ekey_01eu', 'attached', 'eu');
  const cover = coverage([workspace('wrk_01', 'ekey_01eu', 'eu'),
                          workspace('wrk_02', 'ekey_01eu', 'us')]);
  const geos = [['wrk_01', 'eu'], ['wrk_02', 'us']];
  const [state, detail] = classify(euKey, cover.ekey_01eu, geos);
  assert.equal(state, 'geo-mismatch');
  assert.ok(detail.includes('wrk_02 at us'));
  assert.ok(!detail.includes('wrk_01'));
  assert.ok(repairLines(state, euKey).some((l) => l.includes('write-once')));
  assert.equal(classify(euKey, cover.ekey_01eu, [['wrk_01', 'eu']])[0], 'covered');
  assert.deepEqual(repairLines('covered', euKey), []);
});

test('the coverage map and the uncovered split', () => {
  const rows = [workspace('wrk_01'), workspace('wrk_02', null),
                workspace('wrk_03', 'ekey_01hq'),
                workspace('wrk_04', 'ekey_01hq', 'eu', 1700000000),
                workspace('wrk_05', null, 'eu', 1700000001)];
  const cover = coverage(rows);
  assert.deepEqual(cover, { ekey_01hq: { live: ['wrk_03'], archived: ['wrk_04'] } });
  assert.equal(Object.keys(cover).length, 1);
  assert.deepEqual(uncovered(rows), [['wrk_01', 'wrk_02'], ['wrk_05']]);
  assert.deepEqual(coverage(null), {});
  assert.deepEqual(uncovered(null), [[], []]);
  assert.equal(workspaceGeo(rows[0]), 'eu');
  assert.equal(workspaceGeo({ id: 'w' }), null);
});

test('the provider line names the key and masks the account', () => {
  assert.equal(maskArn(ARN), 'arn:aws:kms:eu-west-1:****:key/9f2c');
  assert.equal(maskArn('not-an-arn'), 'not-an-arn');
  assert.equal(maskArn(null), 'unknown');
  assert.ok(kmsRef({ type: 'aws', kms_arn: ARN }).startsWith('aws arn:aws:kms:'));
  assert.ok(!kmsRef({ type: 'aws', kms_arn: ARN }).includes('210987654321'));
  assert.equal(kmsRef({ type: 'gcp', key_name: 'projects/p/locations/eu/x' }),
               'gcp projects/p/locations/eu/x');
  assert.ok(kmsRef({ type: 'azure', key_name: 'k',
                     vault_uri: 'https://v.vault.azure.net' })
    .includes('vault.azure.net'));
  assert.equal(kmsRef({ type: 'quantum' }), 'unrecognised provider quantum');
  assert.equal(kmsRef(null), 'unrecognised provider none');
  assert.ok(repairLines('unattached-and-unused', key('ekey_1'))
    .some((l) => l.includes('write verb')));
});
''',
"faq": [
 ("Is this endpoint real, and can a read-only script actually reach it?",
  "Yes, with two caveats worth stating before you go looking. It is a beta surface: the list call is GET /v1/organizations/external_keys with beta=true, and it is present only for organizations that have CMEK enabled, which is a narrow enterprise feature. If your organization does not have it, the call comes back 403 or 404 and the script prints that as an answer and exits, rather than reporting an empty list as a clean audit. The second caveat is the id format: a config id is normally prefixed ekey_, but for organizations on the Claude Platform on AWS it is the KMS key ARN itself, so do not write anything that assumes the prefix."),
 ("Why not just call the validate endpoint to check the key works?",
  "Because it is a POST, and every script in this section is a GET. That is not pedantry about verbs: validate performs a real encrypt and decrypt roundtrip against your KMS key, which touches the provider side, appears in your CloudTrail or equivalent, and can fail for reasons that have nothing to do with the audit. It is a fine thing to run deliberately when you are debugging a key policy. It is not a thing a scheduled read-only report should be doing on your behalf, and the script says so on every finding rather than quietly omitting it."),
 ("Can I just delete every unattached config?",
  "For a config that is genuinely unattached and that no workspace names, yes — the documentation is direct that an unattached config is inert. The states around it are what the script exists for. A config reported unattached while a workspace still names it is a disagreement between two listings, and the safe reading is the one that says something is using it. A config that is attached and covers only archived workspaces looks equally abandoned and is not: archived workspaces keep their retained data, and it stays encrypted under that config, so deleting it makes that data unrecoverable. The script prints a delete for exactly one of its six outcomes."),
 ("A workspace is covered by the wrong key. How do I move it?",
  "You do not, and this is the fact that most often surprises people. external_key_id on a workspace is write-once: once a key is attached it cannot be detached or replaced, because existing encrypted data needs that config to decrypt. Rotating key material is done on your side, by rotating the underlying KMS key, and the external_key_id stays the same. So the repair for a geo or coverage mismatch is a conversation about the residency commitment, or a new workspace, and never a swap. The script deliberately does not print a re-point instruction, since the API would not accept one."),
 ("Does OpenAI have the same thing?",
  "It has something adjacent and it is not the same object, which is why this note is written against Anthropic. An OpenAI project carries an external_key_id field, and the audit log has external_key.registered and external_key.removed events, so you can see that a key exists and when it was registered. What Anthropic exposes and OpenAI does not is the attachment discriminator itself — a first-class attached / unattached state on the config — which is the entire mechanism of this note. Without it there is no read-only way to establish that a config is inert, only that one is referenced."),
],
"related": [REL_RETENTION, REL_GEO, REL_NULL_WS],
"citations": [CITE_CL_EXTERNAL_KEYS, CITE_CL_WORKSPACES, CITE_CL_ADMIN, CITE_CL_SDK],
},
]
