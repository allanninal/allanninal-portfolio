#!/usr/bin/env python3
"""/llm/ field notes, batch S -- the writing.

Four ceilings nobody in the room set. The section already publishes four notes
about rate limiting and they all answer the same question from different sides:
how much room is left, and which of the three limiters ran out first. None of
these four answers that question, and each was given a different one so that
they do not collapse into a fifth restatement of it.

`project-rate-limit-below-org` reads **configuration, never traffic**. Anthropic
returns a workspace's overrides with `org_limit` sitting next to each `value` on
the same object, which is the only place in either API where the container's
ceiling and the organization's ceiling are legible in one read. OpenAI has no
such field -- verified against the published OpenAPI schema, where
`project.rate_limit` carries `max_requests_per_1_minute` and
`max_tokens_per_1_minute` and nothing about the organization -- so that half of
the script compares the same model row across every project and says out loud
that the peer maximum is a proxy for the org tier rather than the org tier. The
finding that took the longest to see is the one nobody looks for: an override
set to exactly today's organization value is not a no-op, it is a pin, and it
will not follow the next tier increase anywhere.

`acceleration-limit-on-traffic-spike` reads **history, and fires when nothing
saturates**. It walks adjacent one-minute buckets and its finding is a steep
ramp whose peak minute sits far under every configured ceiling. That is the
exact opposite shape from the two published limiter notes, which fire when a
minute reaches its ceiling, and the script hands the reading to them by name
when it finds saturation instead. Anthropic's messages usage report has no
request count -- the field list is tokens and server tool calls only -- so the
ramp here is measured in tokens and the note says so rather than implying a
request rate it cannot see.

`retry-after-header-ignored` reads **transport**. `retry-after` exists only on a
429, so a script that refuses to cause one can never observe it directly; what
it can do is probe the header class that arrives on every response and prove
that class survives the network path. That is the whole note: the same
`GET /v1/models` issued directly and through the gateway your application
actually uses, with the header sets diffed. It is deliberately not the published
note that reads those header values to name which bucket emptied. It never reads
a value to grade headroom; it reads presence, agreement across two paths, and
whether an absolute reset timestamp is consistent with the server's own `date`
header, because a client sleeping until a timestamp on a skewed clock retries
early no matter how good its backoff is.

`flex-resource-unavailable-timeouts` reads **absence**. A `429 Resource
Unavailable` on the Flex tier is explicitly not charged, and an unbilled request
does not appear in a usage report, so this is the one note in the batch whose
evidence is a hole rather than a number. The reading is
`group_by[]=service_tier` on the completions usage report, which is a dimension
this section has not used on the OpenAI side before. Two corrections were made
while writing it. The cost report cannot be grouped by service tier at all --
its `group_by` accepts `project_id`, `line_item` and `api_key_id`, so the
"look for Flex line items" plan does not survive contact with the schema, and
the usage report is the only endpoint that separates tiers. And Anthropic is
absent from this note on purpose: its service tier documentation describes
Priority, Standard and Batch, and its `service_tier` request parameter accepts
only `auto` and `standard_only`, so there is no documented way to ask for Flex
there even though its usage report enumerates `flex` and `flex_discount` as
filter values. The FAQ says exactly that rather than implying parity.

Read only, and stricter than the section baseline. Every request in all four
scripts is a GET, no script constructs a request body, and in particular no
script here deliberately drives traffic into a 429 in order to photograph one.
Provoking the error you are investigating is not a diagnostic; on a saturated
limiter it is a second outage, and on a healthy one it spends capacity that
belongs to production.
"""

CITE_RL = ("Rate limits -- Claude platform docs",
           "https://platform.claude.com/docs/en/api/rate-limits")
CITE_RL_API = ("Rate Limits API -- Claude platform docs",
               "https://platform.claude.com/docs/en/manage-claude/rate-limits-api")
CITE_WS_RL = ("List workspace rate limits -- Claude Admin API reference",
              "https://platform.claude.com/docs/en/api/admin/workspaces/rate_limits/list")
CITE_WS = ("List workspaces -- Claude Admin API reference",
           "https://platform.claude.com/docs/en/api/admin/workspaces/list")
CITE_USAGE_API = ("Usage and Cost API -- Claude platform docs",
                  "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_USAGE_REF = ("Get messages usage report -- Claude Admin API reference",
                  "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_ERRORS = ("Errors -- Claude platform docs",
               "https://platform.claude.com/docs/en/api/errors")
CITE_TIERS = ("Service tiers -- Claude platform docs",
              "https://platform.claude.com/docs/en/api/service-tiers")
CITE_OA_PRL = ("Project rate limits -- OpenAI API reference",
               "https://platform.openai.com/docs/api-reference/project-rate-limits")
CITE_OA_PROJ = ("Projects -- OpenAI API reference",
                "https://platform.openai.com/docs/api-reference/projects")
CITE_OA_USAGE = ("Usage and costs -- OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/usage")
CITE_OA_RL = ("Rate limits -- OpenAI platform docs",
              "https://platform.openai.com/docs/guides/rate-limits")
CITE_OA_FLEX = ("Flex processing -- OpenAI platform docs",
                "https://platform.openai.com/docs/guides/flex-processing")
CITE_OPENAPI = ("openai-openapi -- the published OpenAPI specification",
                "https://github.com/openai/openai-openapi")

REL_FLOOR = ("/llm/project-rate-limit-below-org/",
             "The container that was given a lower ceiling than the organization")
REL_RAMP = ("/llm/acceleration-limit-on-traffic-spike/",
            "429s while every single minute sat under the configured limit")
REL_RETRY = ("/llm/retry-after-header-ignored/",
             "Whether the wait instruction reaches your client at all")
REL_FLEX = ("/llm/flex-resource-unavailable-timeouts/",
            "The tier that fails by not being served rather than by erroring")
REL_HEADROOM = ("/llm/rate-limit-headers-near-exhaustion/",
                "How much room is left right now, read off one live call")
REL_WHICH = ("/llm/rate-limit-429-limiter-unidentified/",
             "Which of the three limiters actually emptied")
REL_ITPM = ("/llm/itpm-exhausted-uncached-input/",
            "When the input limiter really is the ceiling you hit")
REL_OTPM = ("/llm/otpm-exhausted/",
            "When generation, not request rate, is what runs out")
REL_QUOTA = ("/llm/quota-exhausted-not-rate-limited/",
             "The 429 that is a billing wall and never clears on retry")
REL_TOPO = ("/llm/no-prod-dev-project-separation/",
            "Whether the containers those ceilings sit on exist at all")
REL_PRIO = ("/llm/priority-tier-model-unsupported/",
            "The other tier you pay for and may not be getting")
REL_BATCH = ("/llm/batch-discount-left-unused/",
             "The cheaper path that does not fail by going missing")
REL_WALL = ("/llm/non-streaming-request-over-ten-minutes/",
            "The other ten minute clock that kills a request mid flight")
REL_529 = ("/llm/overloaded-529-clusters/",
           "Capacity errors clustered in specific minutes")

GUIDES = [
{
"slug": "project-rate-limit-below-org",
"title": "A project or workspace ceiling set below the org limit",
"description": "Anthropic returns each workspace override with org_limit beside it. OpenAI returns none, so peer projects stand in. Either way one container is throttled.",
"h1": "A project or workspace ceiling set below the org limit",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic workspace rate limit override org_limit",
             "openai project rate limit lower than organization",
             "429 on one project other projects fine",
             "max_tokens_per_1_minute per project openai admin api",
             "workspace inherits organization rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, OPENAI_ADMIN_KEY, or both: whichever is set is the side that gets audited. Both are organization-scoped read credentials. No workspace or project key is used and no response header is read.",
"lead": "The staging project was created for isolation, which is the advice everybody gives, and somebody set its rate limit low on the way past because staging does not need much. Eleven months later that project id is in the production deployment, because reusing it was one line and creating a new one was a ticket. Production now 429s at a fifth of the traffic the organization is entitled to, the organization dashboard shows plenty of headroom, and every other team is fine.",
"short_answer": """<p>Read the container's configured ceiling rather than the organization's. On Anthropic, with an <strong>Admin API key</strong>: <code>GET /v1/organizations/workspaces?limit=100</code> for the ids, then <code>GET /v1/organizations/workspaces/{workspace_id}/rate_limits</code> for each. Every limiter in that response carries both numbers on the same object &mdash; <code>{"type": "input_tokens_per_minute", "value": 500000, "org_limit": 10000000}</code> &mdash; so the comparison needs no second call and no arithmetic you can get wrong.</p>
<p>The response contains <strong>only overrides</strong>. A group missing from <code>data</code> has no workspace override and inherits; a limiter type missing from a group that is present inherits too. That is why <code>GET /v1/organizations/rate_limits</code> is read alongside it: without the organization's own list you cannot tell an inherited limiter from a limiter nobody publishes a number for.</p>
<p>On OpenAI, with an <strong>admin key</strong>: <code>GET /v1/organization/projects?limit=100</code>, then <code>GET /v1/organization/projects/{project_id}/rate_limits?limit=100</code> per project. The <code>project.rate_limit</code> object carries <code>model</code>, <code>max_requests_per_1_minute</code> and <code>max_tokens_per_1_minute</code> and <strong>no organization value at all</strong>, so the script builds a matrix of the same model row across every project and treats the peer maximum as a stand-in for the tier. It prints that it is a stand-in.</p>
<p>Three findings, not one. The obvious one is an override far under the organization value. The second is a group where <em>some</em> limiters are overridden and the rest inherit, which caps you on one dimension and leaves the others wide open. The third is the quiet one: an override set to exactly today's organization value. That is not a no-op. It is a pin, and the day the organization moves up a tier the workspace stays where it is.</p>""",
"problem": """<p>Rate limits are enforced at the organization level, and then you are invited to set lower ones per container to stop any single workspace eating everything. That is a good feature and it is used exactly the way features like it are always used: once, early, by somebody sizing a container for what it was doing that week, and never revisited.</p>
<p>What makes it survive is that nothing about the resulting failure points at the container. The 429 says a rate limit was exceeded. The organization's dashboard shows the organization's ceiling with room underneath it. Other teams, on other containers, are unaffected and will tell you so. The team that is failing goes and asks for a tier increase, gets one, and fails at exactly the same volume as before, because the number that refused them was never the number that moved.</p>
<p>The inheritance rule is the second half of the trap. Workspace overrides are set per limiter type, so a workspace can carry an input-tokens cap and inherit its request and output caps. That is a perfectly reasonable thing to configure deliberately and an extremely easy thing to end up with by accident, and from the outside the two look identical.</p>
<p>And the pin is the third. If a workspace has no override at all, its limits track the organization's, and a tier increase reaches it automatically. If somebody once set an override to the same number the organization had at the time &mdash; which feels like a no-op, and is how a lot of "explicit is better" provisioning ends up &mdash; that workspace has quietly opted out of every future increase. The screen it was configured on will not mention this, and neither will the invoice.</p>""",
"why": """<p><strong>The container's ceiling is configuration, so it is legible when nothing is running.</strong> Everything else this section publishes about rate limits reads either a live response header or a window of traffic, which means it can only speak about containers that are busy right now. This one reads a stored value. A workspace that has been dark for a month, a project that is about to receive a launch, a container created by provisioning automation last Tuesday: all gradeable, none of them sending anything.</p>
<p><strong>Anthropic puts both numbers on one object and OpenAI does not, and pretending otherwise would be an invention.</strong> The workspace limiter object carries <code>value</code> and <code>org_limit</code> together, so the ratio is exact. The <code>project.rate_limit</code> schema carries <code>object</code>, <code>id</code>, <code>model</code>, <code>max_requests_per_1_minute</code>, <code>max_tokens_per_1_minute</code> and some optional per-modality fields, and nothing else. There is no organization value to compare against on that side, so the script compares projects to each other, labels the result a proxy, and refuses to grade at all when there is only one project to look at.</p>
<p><strong>An absent group is not an absent limit.</strong> The workspace response returns overrides only. Reading a missing group as "unlimited" is the single most expensive misreading available here, because it inverts the finding: the container you would conclude is unconstrained is the one that is behaving normally. The script resolves every absence against the organization list and prints the inherited number rather than a blank.</p>
<p><strong>An override equal to the organization value is a finding, and it is the one nobody reports.</strong> Every threshold-based check in this space grades <code>value / org_limit</code> and passes anything at 1.0. But 1.0 is the state where somebody has taken a container off automatic and left it pointing at a number that was current at the time. It is graded separately here, with a repair that is one click: delete the override, do not adjust it.</p>
<p><strong>The repair is a write on both providers, so it is printed.</strong> OpenAI exposes an update at <code>POST /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}</code>, which this script names and does not call. Anthropic exposes no write at all &mdash; its own documentation says workspace rate limits are set in the Console &mdash; so on that side the output is a workspace id, a group, a limiter and a number for a human to go and change.</p>""",
"steps": [
 {"h": "Use organization-scoped read credentials, not a workspace or project key",
  "body": """<p>Both sides of this are Admin API territory. Anthropic accepts an Admin API key, an OAuth token with the <code>org:admin</code> scope, or a personal or service account key that is not scoped to a workspace; a workspace key gets nothing. OpenAI wants an admin key for the <code>/v1/organization/</code> paths. Set <code>ANTHROPIC_ADMIN_KEY</code>, <code>OPENAI_ADMIN_KEY</code>, or both, and the script audits whichever it is given.</p>"""},
 {"h": "Read the organization's own list first",
  "body": """<p><code>GET /v1/organizations/rate_limits</code> returns each group with <code>group_type</code>, a <code>models</code> list for <code>model_group</code> entries, and <code>limits[]</code> of <code>{type, value}</code>. Keep it as a lookup keyed by group. It is what turns every later absence into a number instead of a shrug, and it is the only place the batch, files, token counting, skills and web search groups appear at all.</p>"""},
 {"h": "Read each workspace's overrides and compare value against org_limit",
  "body": """<p><code>GET /v1/organizations/workspaces?limit=100&amp;include_archived=false</code>, paged on <code>after_id</code> with <code>has_more</code> and <code>last_id</code>, then the per-workspace path for each. Grade every limiter's <code>value</code> against its own <code>org_limit</code>, falling back to the organization list when <code>org_limit</code> is <code>null</code>. The default workspace cannot carry overrides and has no entry here, which is expected and is not a finding.</p>"""},
 {"h": "Report the inherited limiters inside an overridden group",
  "body": """<p>Within a group that appears in the response, a limiter type absent from <code>limits[]</code> inherits. Print those by name alongside the overridden ones. A workspace capped on input tokens and inheriting requests and output tokens is a lopsided throttle, and seeing the shape is what tells you whether it was designed or accumulated.</p>"""},
 {"h": "On OpenAI, build the matrix and name the proxy",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/rate_limits</code> per project, folded into <code>{model: {project: {rpm, tpm}}}</code>. For every model row that at least two projects carry, the peer maximum stands in for the tier value. Anything at half of it or less is the outlier. With one project there is nothing to compare and the script says so instead of grading; the repair is printed as the admin update call, never issued.</p>"""},
],
"verify": """<p>Clear one override and re-run. The workspace should move to <code>no-override</code> and its limiters should read as inherited, with the organization number printed next to each. A workspace that moves from <code>throttled-below-org</code> to <code>override-pinned-at-org</code> has had its number raised to today's organization value rather than removed, which is the state that stops tracking the next increase.</p>
<pre><code class="language-bash">python3 rate_limit_below_org_audit.py
# anthropic: 4 workspace(s), 6 organization rate limit group(s)
# throttled-below-org    wrkspc_01ab prod-eu / model_group:claude-opus-5
#   input_tokens_per_minute   500,000 of 10,000,000 (5%)
#   requests_per_minute       1,000 of 4,000 (25%)
#   inherited: output_tokens_per_minute (2,000,000 from the organization)
#   repair: this container is capped at a fraction of the organization ceiling.
#           Open the workspace in the Console, Rate limits tab, and raise or
#           remove the override. There is no write endpoint for this.
# override-pinned-at-org wrkspc_01cd batch-jobs / model_group:claude-sonnet-5
#   input_tokens_per_minute   10,000,000 equal to the organization value
#   repair: an override equal to today's organization value is a pin, not a
#           no-op. Delete it so the workspace follows the next tier increase.
# no-override            wrkspc_01ef sandbox: inherits every organization limit
# openai: 5 project(s), 3 model row(s) carried by 2 or more projects
# project-outlier        proj_9f2 legacy-staging  gpt-5.6
#   max_tokens_per_1_minute   150,000 against a peer maximum of 2,000,000 (7%)
#   note: OpenAI does not return an organization value on this object, so the
#         peer maximum is a proxy for the tier, not the tier itself.
# 3 finding(s)</code></pre>""",
"code_intro": "Two providers, one script, and every decision in a pure function. <code>group_label</code>, which names a rate limit group the same way from either endpoint so the two can be joined; <code>org_index</code>, which folds the organization list into a lookup; <code>overrides_of</code>, which pulls <code>(type, value, org_limit)</code> triples off one workspace group and keeps a null <code>org_limit</code> as a null rather than a zero; <code>grade_override</code>, which is where the four states live, including the equality case; <code>inherited_limiters</code>, which subtracts what was overridden from what the organization publishes; <code>openai_matrix</code> and <code>openai_outliers</code>, which do the peer comparison and refuse to run on a single project; and <code>verdict</code>, which rolls a container's limiters into one word by severity.",
"py_file": "rate_limit_below_org_audit.py",
"py": '''"""Find a container whose rate limit was set below the organization's.

Read only. Every request is a GET, on either or both providers:

  Anthropic, Admin API key
    GET /v1/organizations/rate_limits
    GET /v1/organizations/workspaces
    GET /v1/organizations/workspaces/{workspace_id}/rate_limits
  OpenAI, admin key
    GET /v1/organization/projects
    GET /v1/organization/projects/{project_id}/rate_limits

Nothing here reads a response header and nothing here reads traffic. The subject
is the configured ceiling on a container, which is legible whether or not that
container has sent a single request this month.

Anthropic returns each workspace override with org_limit beside value on the
same object, so the comparison is exact. OpenAI's project.rate_limit object
carries no organization value at all, so the peer maximum across projects stands
in for the tier and is reported as the proxy it is.

The repair is a write on both providers. It is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rate_limit_below_org_audit")

ANTHROPIC = "https://api.anthropic.com/v1"
OPENAI = "https://api.openai.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

# The three limiters a model group carries. Other group types carry their own
# types (enqueued_batch_requests and so on), which is why nothing here assumes
# this tuple is the whole vocabulary: it is only used to order output.
LIMITER_ORDER = ("requests_per_minute", "input_tokens_per_minute",
                 "output_tokens_per_minute")

# Severity order, worst first. verdict() walks this, so adding a state means
# deciding where it sits rather than hoping the dict happened to be ordered.
SEVERITY = ("throttled-below-org", "override-pinned-at-org", "override-above-org",
            "limiter-inherited", "org-limit-unknown", "override-in-range",
            "no-override")

FINDINGS = ("throttled-below-org", "override-pinned-at-org", "override-above-org",
            "project-outlier")


def num(value):
    """An int, or None. Pure.

    None is a real answer here and must survive: org_limit is documented as
    nullable, and coercing a null to 0 would turn "cannot be graded" into
    "throttled to nothing", which is the loudest possible wrong answer.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def group_label(entry):
    """A stable printable name for one rate limit group. Pure.

    The organization endpoint and the workspace endpoint describe the same
    groups with the same models list, so labelling them identically is what lets
    the two be joined without matching on model strings by hand.
    """
    entry = entry or {}
    gtype = str(entry.get("group_type") or "").strip() or "unknown_group"
    models = sorted(str(m) for m in (entry.get("models") or []) if m)
    if not models:
        return gtype
    extra = len(models) - 1
    return "%s:%s%s" % (gtype, models[0], (" +%d" % extra) if extra else "")


def limits_of(entry):
    """{limiter_type: value} for one group entry. Pure. Unparseable values drop."""
    out = {}
    for row in ((entry or {}).get("limits") or []):
        row = row or {}
        ltype = str(row.get("type") or "").strip()
        value = num(row.get("value"))
        if ltype and value is not None:
            out[ltype] = value
    return out


def org_index(pages):
    """{group_label: {limiter_type: value}} from the organization endpoint. Pure.

    Takes an iterable of page payloads so a paginated read folds without the
    caller flattening first.
    """
    out = {}
    for page in pages or []:
        for entry in ((page or {}).get("data") or []):
            out.setdefault(group_label(entry), {}).update(limits_of(entry))
    return out


def overrides_of(entry):
    """[(limiter_type, value, org_limit)] for one workspace group. Pure.

    org_limit stays None when the API reports null. The caller decides whether
    to fall back to the organization listing; this function does not guess.
    """
    out = []
    for row in ((entry or {}).get("limits") or []):
        row = row or {}
        ltype = str(row.get("type") or "").strip()
        if not ltype:
            continue
        out.append((ltype, num(row.get("value")), num(row.get("org_limit"))))
    out.sort(key=lambda r: (LIMITER_ORDER.index(r[0])
                            if r[0] in LIMITER_ORDER else len(LIMITER_ORDER), r[0]))
    return out


def grade_override(value, org_limit, floor=0.5):
    """Grade one workspace limiter against the organization value. Pure.

    Returns (state, detail). The equality case is deliberately not folded into
    the ratio: an override equal to today's organization value is a pin, and a
    threshold check that passes everything at 1.0 will never say so.
    """
    if value is None:
        return ("no-override", "inherits the organization value")
    if org_limit is None:
        return ("org-limit-unknown",
                "value is %s and the organization publishes no number for this "
                "limiter, so the override cannot be graded" % fmt(value))
    if value <= 0:
        return ("throttled-below-org",
                "set to %s, which stops this limiter in this container entirely"
                % fmt(value))
    if value > org_limit:
        return ("override-above-org",
                "%s is above the organization's %s, and the organization limit "
                "applies anyway" % (fmt(value), fmt(org_limit)))
    if value == org_limit:
        return ("override-pinned-at-org",
                "%s, equal to the organization value today, so it will not "
                "follow the next increase" % fmt(value))
    share = float(value) / float(org_limit)
    if share <= floor:
        return ("throttled-below-org",
                "%s of %s (%.0f%%)" % (fmt(value), fmt(org_limit), share * 100))
    return ("override-in-range",
            "%s of %s (%.0f%%)" % (fmt(value), fmt(org_limit), share * 100))


def inherited_limiters(entry, org_types):
    """Limiter types the organization publishes that this group did not override.

    Pure. Returns [(limiter_type, org_value)] in a stable order.
    """
    overridden = {t for t, value, _ in overrides_of(entry) if value is not None}
    rows = [(t, v) for t, v in (org_types or {}).items() if t not in overridden]
    rows.sort(key=lambda r: (LIMITER_ORDER.index(r[0])
                             if r[0] in LIMITER_ORDER else len(LIMITER_ORDER), r[0]))
    return rows


def verdict(states):
    """Roll one container's limiter states into a single word. Pure."""
    present = set(states or [])
    for state in SEVERITY:
        if state in present:
            return state
    return "no-override"


def openai_matrix(by_project):
    """{model: {project_id: {"rpm": int|None, "tpm": int|None}}}. Pure.

    Rows with no model string are dropped rather than collected under a blank
    key, because a blank key would then be compared against real ones.
    """
    out = {}
    for pid, rows in sorted((by_project or {}).items()):
        for row in rows or []:
            row = row or {}
            model = str(row.get("model") or "").strip()
            if not model:
                continue
            out.setdefault(model, {})[str(pid)] = {
                "rpm": num(row.get("max_requests_per_1_minute")),
                "tpm": num(row.get("max_tokens_per_1_minute")),
            }
    return out


def openai_outliers(matrix, floor=0.5):
    """[(model, project_id, dimension, value, peer_max)]. Pure. Worst first.

    A model row carried by fewer than two projects is skipped: with one project
    there is no peer to compare against, and the object carries no organization
    value to compare against instead.
    """
    out = []
    for model, projects in sorted((matrix or {}).items()):
        if len(projects) < 2:
            continue
        for dim in ("rpm", "tpm"):
            values = {p: (v or {}).get(dim) for p, v in projects.items()}
            usable = {p: v for p, v in values.items() if v is not None and v > 0}
            if len(usable) < 2:
                continue
            peer_max = max(usable.values())
            for pid, value in sorted(usable.items()):
                if value <= peer_max * floor:
                    out.append((model, pid, dim, value, peer_max))
    out.sort(key=lambda r: (r[3] / float(r[4]), r[0], r[1], r[2]))
    return out


def fmt(value):
    """Thousands separators, or a dash for None. Pure."""
    if value is None:
        return "-"
    return "{:,}".format(int(value))


def repair_lines(state):
    """The repair for one state. Pure. Printed, never performed."""
    if state == "throttled-below-org":
        return ["this container is capped well under the organization ceiling. "
                "On Anthropic open the workspace in the Console, Rate limits "
                "tab, and raise or remove the override; there is no write "
                "endpoint for it.",
                "check the container id against what production actually uses "
                "before raising anything. A staging id that followed the code "
                "into production is repaired by changing the id, not the limit."]
    if state == "override-pinned-at-org":
        return ["an override equal to today's organization value is a pin, not "
                "a no-op. Delete the override so the container follows the next "
                "tier increase instead of staying on this number.",
                "if the equality is deliberate, write it down somewhere the "
                "next tier increase will be read, because nothing in the API "
                "will mention it again."]
    if state == "override-above-org":
        return ["an override above the organization value has no effect: "
                "organization limits always apply. Remove it so the "
                "configuration says what is actually enforced."]
    if state == "project-outlier":
        return ["raise it with the admin update call at "
                "/v1/organization/projects/{project_id}/rate_limits/"
                "{rate_limit_id}, sending the dimension you want changed. That "
                "is a write and this script does not make it.",
                "the peer maximum is a proxy for the tier value, not the tier "
                "value: this object carries no organization number. Confirm "
                "against the tier before treating the gap as the whole story."]
    if state == "org-limit-unknown":
        return ["the organization publishes no number for this limiter, so the "
                "override is unjudgeable rather than fine. Read "
                "/v1/organizations/rate_limits for the group before acting."]
    return []


def get(session, url, headers=None, **params):
    r = session.get(url, params=params, headers=headers or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from %s: this path needs an organization scoped "
                         "read credential, not a workspace or project key"
                         % (r.status_code, url))
    r.raise_for_status()
    return r.json()


def anthropic_pages(session, path, **params):
    """Walk an Anthropic next_page cursor listing, yielding whole payloads."""
    params = dict(params)
    for _ in range(50):
        page = get(session, ANTHROPIC + path, **params)
        yield page
        nxt = page.get("next_page")
        if not nxt:
            return
        params["page"] = nxt


def anthropic_cursor(session, path, **params):
    """Walk an Anthropic after_id listing, yielding items."""
    params = dict(params)
    for _ in range(50):
        page = get(session, ANTHROPIC + path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after_id"] = page.get("last_id") or (data[-1] or {}).get("id")


def openai_cursor(session, path, **params):
    """Walk an OpenAI after/last_id listing, yielding items."""
    params = dict(params)
    for _ in range(50):
        page = get(session, OPENAI + path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def audit_anthropic(key, floor):
    s = requests.Session()
    s.headers.update({"x-api-key": key,
                      "anthropic-version": ANTHROPIC_VERSION,
                      "User-Agent": "rate-limit-below-org-audit/1.0"})
    org = org_index(anthropic_pages(s, "/organizations/rate_limits"))
    spaces = list(anthropic_cursor(s, "/organizations/workspaces", limit=100))
    log.info("anthropic: %d workspace(s), %d organization rate limit group(s)",
             len(spaces), len(org))

    findings = 0
    for space in spaces:
        wid = (space or {}).get("id") or "?"
        name = (space or {}).get("name") or "(unnamed)"
        entries = []
        for page in anthropic_pages(
                s, "/organizations/workspaces/%s/rate_limits" % wid):
            entries.extend(page.get("data") or [])
        if not entries:
            log.info("%-22s %s %s: inherits every organization limit",
                     "no-override", wid, name)
            continue
        for entry in entries:
            label = group_label(entry)
            org_types = org.get(label) or {}
            states = []
            rows = []
            for ltype, value, org_limit in overrides_of(entry):
                fallback = org_limit if org_limit is not None else org_types.get(ltype)
                state, detail = grade_override(value, fallback, floor)
                states.append(state)
                rows.append((ltype, state, detail))
            inherited = inherited_limiters(entry, org_types)
            if inherited and states:
                states.append("limiter-inherited")
            state = verdict(states)
            emit = log.warning if state in FINDINGS else log.info
            emit("%-22s %s %s / %s", state, wid, name, label)
            for ltype, row_state, detail in rows:
                emit("  %-26s %s", ltype, detail)
            for ltype, value in inherited:
                emit("  inherited: %s (%s from the organization)", ltype, fmt(value))
            for line in repair_lines(state):
                emit("  repair: %s", line)
            if state in FINDINGS:
                findings += 1
    return findings


def audit_openai(key, floor):
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key,
                      "User-Agent": "rate-limit-below-org-audit/1.0"})
    projects = list(openai_cursor(s, "/organization/projects", limit=100,
                                  include_archived="false"))
    by_project = {}
    names = {}
    for project in projects:
        pid = (project or {}).get("id") or "?"
        names[pid] = (project or {}).get("name") or "(unnamed)"
        by_project[pid] = list(openai_cursor(
            s, "/organization/projects/%s/rate_limits" % pid, limit=100))

    matrix = openai_matrix(by_project)
    comparable = sum(1 for m in matrix.values() if len(m) >= 2)
    log.info("openai: %d project(s), %d model row(s) carried by 2 or more "
             "projects", len(projects), comparable)
    if len(projects) < 2:
        log.info("%-22s one project only: this object carries no organization "
                 "value, so there is nothing to compare against", "no-peer")
        return 0

    rows = openai_outliers(matrix, floor)
    dimension = {"rpm": "max_requests_per_1_minute",
                 "tpm": "max_tokens_per_1_minute"}
    seen = set()
    for model, pid, dim, value, peer_max in rows:
        log.warning("%-22s %s %s  %s", "project-outlier", pid,
                    names.get(pid, "(unnamed)"), model)
        log.warning("  %-26s %s against a peer maximum of %s (%.0f%%)",
                    dimension[dim], fmt(value), fmt(peer_max),
                    100.0 * value / peer_max)
        seen.add((pid, model))
    if rows:
        for line in repair_lines("project-outlier"):
            log.warning("  repair: %s", line)
    return len(seen)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--floor", type=float, default=0.5,
                    help="report an override at or below this share of the "
                         "organization value (default 0.5)")
    args = ap.parse_args()

    anthropic_key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    openai_key = os.environ.get("OPENAI_ADMIN_KEY")
    if not anthropic_key and not openai_key:
        log.error("set ANTHROPIC_ADMIN_KEY, OPENAI_ADMIN_KEY, or both. Each "
                  "must be an organization scoped read credential; a workspace "
                  "or project key cannot reach these paths")
        return 2

    findings = 0
    if anthropic_key:
        findings += audit_anthropic(anthropic_key, args.floor)
    if openai_key:
        findings += audit_openai(openai_key, args.floor)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "rate-limit-below-org-audit.mjs",
"js": '''/**
 * Find a container whose rate limit was set below the organization's.
 *
 * Read only. Every request is a GET, on either or both providers. Nothing here
 * reads a response header and nothing here reads traffic: the subject is the
 * configured ceiling on a container, legible whether or not that container has
 * sent a single request this month.
 *
 * Anthropic returns each workspace override with org_limit beside value on the
 * same object. OpenAI's project.rate_limit object carries no organization value
 * at all, so the peer maximum across projects stands in for the tier and is
 * reported as the proxy it is. The repair is a write and is printed only.
 */
const ANTHROPIC = 'https://api.anthropic.com/v1';
const OPENAI = 'https://api.openai.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

export const LIMITER_ORDER = ['requests_per_minute', 'input_tokens_per_minute',
                              'output_tokens_per_minute'];

const SEVERITY = ['throttled-below-org', 'override-pinned-at-org', 'override-above-org',
                  'limiter-inherited', 'org-limit-unknown', 'override-in-range',
                  'no-override'];

const FINDINGS = new Set(['throttled-below-org', 'override-pinned-at-org',
                          'override-above-org', 'project-outlier']);

/** An integer, or null. Pure. null is a real answer and must survive. */
export function num(value) {
  if (value === null || value === undefined || typeof value === 'boolean') return null;
  const n = Number(value);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/** A stable printable name for one rate limit group. Pure. */
export function groupLabel(entry) {
  const gtype = String(entry?.group_type ?? '').trim() || 'unknown_group';
  const models = (entry?.models ?? []).filter(Boolean).map(String).sort();
  if (models.length === 0) return gtype;
  const extra = models.length - 1;
  return `${gtype}:${models[0]}${extra ? ` +${extra}` : ''}`;
}

/** {limiterType: value} for one group entry. Pure. */
export function limitsOf(entry) {
  const out = {};
  for (const row of entry?.limits ?? []) {
    const ltype = String(row?.type ?? '').trim();
    const value = num(row?.value);
    if (ltype && value !== null) out[ltype] = value;
  }
  return out;
}

/** {groupLabel: {limiterType: value}} from the organization endpoint. Pure. */
export function orgIndex(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const entry of page?.data ?? []) {
      out[groupLabel(entry)] = { ...(out[groupLabel(entry)] ?? {}), ...limitsOf(entry) };
    }
  }
  return out;
}

const rank = (t) => (LIMITER_ORDER.indexOf(t) === -1 ? LIMITER_ORDER.length
                                                     : LIMITER_ORDER.indexOf(t));

/** [[limiterType, value, orgLimit]] for one workspace group. Pure. */
export function overridesOf(entry) {
  const out = [];
  for (const row of entry?.limits ?? []) {
    const ltype = String(row?.type ?? '').trim();
    if (!ltype) continue;
    out.push([ltype, num(row?.value), num(row?.org_limit)]);
  }
  out.sort((a, b) => (rank(a[0]) - rank(b[0])) || a[0].localeCompare(b[0]));
  return out;
}

/** Thousands separators, or a dash for null. Pure. */
export function fmt(value) {
  if (value === null || value === undefined) return '-';
  return Math.trunc(Number(value)).toLocaleString('en-US');
}

/** Grade one workspace limiter against the organization value. Pure. */
export function gradeOverride(value, orgLimit, floor = 0.5) {
  if (value === null || value === undefined) {
    return ['no-override', 'inherits the organization value'];
  }
  if (orgLimit === null || orgLimit === undefined) {
    return ['org-limit-unknown',
            `value is ${fmt(value)} and the organization publishes no number for `
            + 'this limiter, so the override cannot be graded'];
  }
  if (value <= 0) {
    return ['throttled-below-org',
            `set to ${fmt(value)}, which stops this limiter in this container entirely`];
  }
  if (value > orgLimit) {
    return ['override-above-org',
            `${fmt(value)} is above the organization's ${fmt(orgLimit)}, and the `
            + 'organization limit applies anyway'];
  }
  if (value === orgLimit) {
    return ['override-pinned-at-org',
            `${fmt(value)}, equal to the organization value today, so it will not `
            + 'follow the next increase'];
  }
  const share = value / orgLimit;
  const detail = `${fmt(value)} of ${fmt(orgLimit)} (${Math.round(share * 100)}%)`;
  return [share <= floor ? 'throttled-below-org' : 'override-in-range', detail];
}

/** [[limiterType, orgValue]] the organization publishes and the group did not override. */
export function inheritedLimiters(entry, orgTypes) {
  const overridden = new Set(overridesOf(entry).filter((r) => r[1] !== null)
    .map((r) => r[0]));
  const rows = Object.entries(orgTypes ?? {}).filter(([t]) => !overridden.has(t));
  rows.sort((a, b) => (rank(a[0]) - rank(b[0])) || a[0].localeCompare(b[0]));
  return rows;
}

/** Roll one container's limiter states into a single word. Pure. */
export function verdict(states) {
  const present = new Set(states ?? []);
  for (const state of SEVERITY) if (present.has(state)) return state;
  return 'no-override';
}

/** {model: {projectId: {rpm, tpm}}}. Pure. */
export function openaiMatrix(byProject) {
  const out = {};
  for (const pid of Object.keys(byProject ?? {}).sort()) {
    for (const row of byProject[pid] ?? []) {
      const model = String(row?.model ?? '').trim();
      if (!model) continue;
      (out[model] ??= {})[String(pid)] = {
        rpm: num(row?.max_requests_per_1_minute),
        tpm: num(row?.max_tokens_per_1_minute),
      };
    }
  }
  return out;
}

/** [[model, projectId, dimension, value, peerMax]]. Pure. Worst first. */
export function openaiOutliers(matrix, floor = 0.5) {
  const out = [];
  for (const model of Object.keys(matrix ?? {}).sort()) {
    const projects = matrix[model];
    if (Object.keys(projects).length < 2) continue;
    for (const dim of ['rpm', 'tpm']) {
      const usable = Object.entries(projects)
        .map(([p, v]) => [p, v?.[dim]])
        .filter(([, v]) => v !== null && v !== undefined && v > 0);
      if (usable.length < 2) continue;
      const peerMax = Math.max(...usable.map(([, v]) => v));
      for (const [pid, value] of usable.sort((a, b) => a[0].localeCompare(b[0]))) {
        if (value <= peerMax * floor) out.push([model, pid, dim, value, peerMax]);
      }
    }
  }
  out.sort((a, b) => (a[3] / a[4]) - (b[3] / b[4])
    || a[0].localeCompare(b[0]) || a[1].localeCompare(b[1]));
  return out;
}

/** The repair for one state. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'throttled-below-org') {
    return ['this container is capped well under the organization ceiling. On '
      + 'Anthropic open the workspace in the Console, Rate limits tab, and raise '
      + 'or remove the override; there is no write endpoint for it.',
      'check the container id against what production actually uses before '
      + 'raising anything. A staging id that followed the code into production '
      + 'is repaired by changing the id, not the limit.'];
  }
  if (state === 'override-pinned-at-org') {
    return ['an override equal to today\\'s organization value is a pin, not a '
      + 'no-op. Delete the override so the container follows the next tier '
      + 'increase instead of staying on this number.',
      'if the equality is deliberate, write it down somewhere the next tier '
      + 'increase will be read, because nothing in the API will mention it again.'];
  }
  if (state === 'override-above-org') {
    return ['an override above the organization value has no effect: organization '
      + 'limits always apply. Remove it so the configuration says what is '
      + 'actually enforced.'];
  }
  if (state === 'project-outlier') {
    return ['raise it with the admin update call at /v1/organization/projects/'
      + '{project_id}/rate_limits/{rate_limit_id}, sending the dimension you want '
      + 'changed. That is a write and this script does not make it.',
      'the peer maximum is a proxy for the tier value, not the tier value: this '
      + 'object carries no organization number. Confirm against the tier before '
      + 'treating the gap as the whole story.'];
  }
  if (state === 'org-limit-unknown') {
    return ['the organization publishes no number for this limiter, so the '
      + 'override is unjudgeable rather than fine. Read '
      + '/v1/organizations/rate_limits for the group before acting.'];
  }
  return [];
}

async function read(url, headers, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) target.searchParams.set(k, String(v));
  const r = await fetch(target, { headers });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from ${url}: this path needs an organization `
                    + 'scoped read credential, not a workspace or project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function anthropicPages(headers, path, params) {
  const out = [];
  const q = { ...(params ?? {}) };
  for (let i = 0; i < 50; i += 1) {
    const page = await read(ANTHROPIC + path, headers, q);
    out.push(page);
    if (!page.next_page) break;
    q.page = page.next_page;
  }
  return out;
}

async function cursor(base, headers, path, params, cursorKey) {
  const out = [];
  const q = { ...(params ?? {}) };
  for (let i = 0; i < 50; i += 1) {
    const page = await read(base + path, headers, q);
    const data = page.data ?? [];
    out.push(...data);
    if (!page.has_more || data.length === 0) break;
    q[cursorKey] = page.last_id ?? data[data.length - 1]?.id;
  }
  return out;
}

async function auditAnthropic(key, floor) {
  const headers = { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION,
                    'User-Agent': 'rate-limit-below-org-audit/1.0' };
  const org = orgIndex(await anthropicPages(headers, '/organizations/rate_limits'));
  const spaces = await cursor(ANTHROPIC, headers, '/organizations/workspaces',
                              { limit: 100 }, 'after_id');
  console.log(`anthropic: ${spaces.length} workspace(s), ${Object.keys(org).length} `
              + 'organization rate limit group(s)');

  let findings = 0;
  for (const space of spaces) {
    const wid = space?.id ?? '?';
    const name = space?.name ?? '(unnamed)';
    const pages = await anthropicPages(
      headers, `/organizations/workspaces/${wid}/rate_limits`);
    const entries = pages.flatMap((p) => p.data ?? []);
    if (entries.length === 0) {
      console.log(`${'no-override'.padEnd(22)} ${wid} ${name}: inherits every `
                  + 'organization limit');
      continue;
    }
    for (const entry of entries) {
      const label = groupLabel(entry);
      const orgTypes = org[label] ?? {};
      const states = [];
      const rows = [];
      for (const [ltype, value, orgLimit] of overridesOf(entry)) {
        const fallback = orgLimit === null ? (orgTypes[ltype] ?? null) : orgLimit;
        const [state, detail] = gradeOverride(value, fallback, floor);
        states.push(state);
        rows.push([ltype, detail]);
      }
      const inherited = inheritedLimiters(entry, orgTypes);
      if (inherited.length && states.length) states.push('limiter-inherited');
      const state = verdict(states);
      console.log(`${state.padEnd(22)} ${wid} ${name} / ${label}`);
      for (const [ltype, detail] of rows) console.log(`  ${ltype.padEnd(26)} ${detail}`);
      for (const [ltype, value] of inherited) {
        console.log(`  inherited: ${ltype} (${fmt(value)} from the organization)`);
      }
      for (const line of repairLines(state)) console.log(`  repair: ${line}`);
      if (FINDINGS.has(state)) findings += 1;
    }
  }
  return findings;
}

async function auditOpenai(key, floor) {
  const headers = { Authorization: `Bearer ${key}`,
                    'User-Agent': 'rate-limit-below-org-audit/1.0' };
  const projects = await cursor(OPENAI, headers, '/organization/projects',
                                { limit: 100, include_archived: 'false' }, 'after');
  const byProject = {};
  const names = {};
  for (const project of projects) {
    const pid = project?.id ?? '?';
    names[pid] = project?.name ?? '(unnamed)';
    byProject[pid] = await cursor(
      OPENAI, headers, `/organization/projects/${pid}/rate_limits`, { limit: 100 }, 'after');
  }

  const matrix = openaiMatrix(byProject);
  const comparable = Object.values(matrix).filter((m) => Object.keys(m).length >= 2).length;
  console.log(`openai: ${projects.length} project(s), ${comparable} model row(s) `
              + 'carried by 2 or more projects');
  if (projects.length < 2) {
    console.log(`${'no-peer'.padEnd(22)} one project only: this object carries no `
                + 'organization value, so there is nothing to compare against');
    return 0;
  }

  const rows = openaiOutliers(matrix, floor);
  const dimension = { rpm: 'max_requests_per_1_minute', tpm: 'max_tokens_per_1_minute' };
  const seen = new Set();
  for (const [model, pid, dim, value, peerMax] of rows) {
    console.log(`${'project-outlier'.padEnd(22)} ${pid} ${names[pid] ?? '(unnamed)'}  ${model}`);
    console.log(`  ${dimension[dim].padEnd(26)} ${fmt(value)} against a peer maximum `
                + `of ${fmt(peerMax)} (${Math.round((100 * value) / peerMax)}%)`);
    seen.add(`${pid}|${model}`);
  }
  if (rows.length) {
    for (const line of repairLines('project-outlier')) console.log(`  repair: ${line}`);
  }
  return seen.size;
}

async function main() {
  const anthropicKey = process.env.ANTHROPIC_ADMIN_KEY;
  const openaiKey = process.env.OPENAI_ADMIN_KEY;
  if (!anthropicKey && !openaiKey) {
    console.error('set ANTHROPIC_ADMIN_KEY, OPENAI_ADMIN_KEY, or both. Each must be '
                  + 'an organization scoped read credential; a workspace or project '
                  + 'key cannot reach these paths');
    process.exitCode = 2;
    return;
  }
  const floor = Number(process.env.FLOOR ?? 0.5);
  let findings = 0;
  if (anthropicKey) findings += await auditAnthropic(anthropicKey, floor);
  if (openaiKey) findings += await auditOpenai(openaiKey, floor);
  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note itself: a workspace limiter at 5% of its own <code>org_limit</code> has to grade as <code>throttled-below-org</code> and print the number it is measured against. Next to it, the case a ratio check silently passes &mdash; an override exactly equal to the organization value, which must come back as a pin with its own repair. Then the null <code>org_limit</code>, which must not become a zero and must not be graded; the group where two limiters are overridden and a third inherits, which has to name the inherited one and the organization's number for it; the OpenAI matrix, where a single project must produce no findings at all because there is no peer and no organization field; and the join between the two endpoints, which is only sound if the same group is labelled identically from both.",
"test_py_file": "test_rate_limit_below_org_audit.py",
"test_py": '''from rate_limit_below_org_audit import (grade_override, group_label,
                                        inherited_limiters, limits_of, num,
                                        openai_matrix, openai_outliers,
                                        org_index, overrides_of, repair_lines,
                                        verdict)


def org_group(models, **limits):
    return {"type": "rate_limit", "group_type": "model_group",
            "models": list(models),
            "limits": [{"type": t, "value": v} for t, v in limits.items()]}


def ws_group(models, limits):
    return {"type": "workspace_rate_limit", "group_type": "model_group",
            "models": list(models), "limits": limits}


def test_a_workspace_capped_at_a_fraction_of_the_org_is_the_finding():
    # The whole note. Both numbers arrive on the same object, so no second
    # lookup can go wrong and no arithmetic is being trusted to a dashboard.
    entry = ws_group(["claude-opus-5"], [
        {"type": "input_tokens_per_minute", "value": 500_000, "org_limit": 10_000_000},
        {"type": "requests_per_minute", "value": 1_000, "org_limit": 4_000},
    ])
    rows = overrides_of(entry)
    assert [r[0] for r in rows] == ["requests_per_minute", "input_tokens_per_minute"]
    state, detail = grade_override(500_000, 10_000_000)
    assert state == "throttled-below-org"
    assert "500,000 of 10,000,000 (5%)" == detail
    assert verdict([s for s, _ in (grade_override(v, o) for _, v, o in rows)]) \\
        == "throttled-below-org"
    assert any("Rate limits tab" in line for line in repair_lines(state))


def test_an_override_equal_to_the_org_value_is_a_pin_not_a_no_op():
    # A ratio check passes this at 1.0 and says nothing. It is the state where
    # a container has quietly opted out of every future tier increase.
    state, detail = grade_override(10_000_000, 10_000_000)
    assert state == "override-pinned-at-org"
    assert "will not follow the next increase" in detail
    assert any("Delete the override" in line for line in repair_lines(state))
    # And above the org value is a third thing again: it simply does not apply.
    above, above_detail = grade_override(20_000_000, 10_000_000)
    assert above == "override-above-org"
    assert "applies anyway" in above_detail


def test_a_null_org_limit_is_unjudgeable_and_never_becomes_zero():
    assert num(None) is None and num("nope") is None and num(True) is None
    state, detail = grade_override(500_000, None)
    assert state == "org-limit-unknown"
    assert "cannot be graded" in detail
    assert any("/v1/organizations/rate_limits" in line for line in repair_lines(state))
    # A zero override is the opposite: a real number, and the worst one.
    assert grade_override(0, 10_000_000)[0] == "throttled-below-org"


def test_limiters_absent_from_an_overridden_group_are_reported_as_inherited():
    org = org_index([{"data": [org_group(["claude-opus-5"],
                                         requests_per_minute=4_000,
                                         input_tokens_per_minute=10_000_000,
                                         output_tokens_per_minute=2_000_000)]}])
    label = group_label(org_group(["claude-opus-5"]))
    entry = ws_group(["claude-opus-5"], [
        {"type": "input_tokens_per_minute", "value": 500_000, "org_limit": 10_000_000},
        {"type": "requests_per_minute", "value": 1_000, "org_limit": 4_000},
    ])
    assert inherited_limiters(entry, org[label]) == [
        ("output_tokens_per_minute", 2_000_000)]
    assert verdict(["override-in-range", "limiter-inherited"]) == "limiter-inherited"


def test_the_two_endpoints_label_the_same_group_identically():
    # The join is by label, so this is the assertion the whole Anthropic side
    # rests on: a workspace entry and an organization entry for the same group
    # must produce the same key even though their type fields differ.
    models = ["claude-opus-4-8", "claude-opus-4-5"]
    assert group_label(org_group(models)) == group_label(ws_group(models, []))
    assert group_label(org_group(models)) == "model_group:claude-opus-4-5 +1"
    assert group_label({"group_type": "batch", "models": None}) == "batch"
    assert group_label(None) == "unknown_group"
    assert limits_of({"limits": [{"type": "x", "value": "not-a-number"}]}) == {}


def test_openai_needs_a_peer_because_the_object_has_no_org_value():
    one = openai_matrix({"proj_a": [
        {"model": "gpt-5.6", "max_requests_per_1_minute": 60,
         "max_tokens_per_1_minute": 150_000}]})
    assert openai_outliers(one) == []
    both = openai_matrix({
        "proj_a": [{"model": "gpt-5.6", "max_requests_per_1_minute": 10_000,
                    "max_tokens_per_1_minute": 2_000_000}],
        "proj_b": [{"model": "gpt-5.6", "max_requests_per_1_minute": 9_000,
                    "max_tokens_per_1_minute": 150_000},
                   {"model": "", "max_tokens_per_1_minute": 1}],
    })
    assert sorted(both["gpt-5.6"]) == ["proj_a", "proj_b"]
    assert "" not in both
    rows = openai_outliers(both)
    assert rows == [("gpt-5.6", "proj_b", "tpm", 150_000, 2_000_000)]
    assert any("proxy for the tier" in line
               for line in repair_lines("project-outlier"))


def test_empty_and_absent_inputs_do_not_raise():
    assert org_index(None) == {} and overrides_of(None) == []
    assert openai_matrix(None) == {} and openai_outliers(None) == []
    assert inherited_limiters(None, None) == []
    assert verdict([]) == "no-override" and verdict(None) == "no-override"
    assert grade_override(None, 10)[0] == "no-override"
    assert repair_lines("no-override") == []
''',
"test_js_file": "rate-limit-below-org-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { gradeOverride, groupLabel, inheritedLimiters, limitsOf, num, openaiMatrix,
         openaiOutliers, orgIndex, overridesOf, repairLines, verdict }
  from './rate-limit-below-org-audit.mjs';

const orgGroup = (models, limits) => ({
  type: 'rate_limit', group_type: 'model_group', models: [...models],
  limits: Object.entries(limits ?? {}).map(([type, value]) => ({ type, value })),
});

const wsGroup = (models, limits) => ({
  type: 'workspace_rate_limit', group_type: 'model_group', models: [...models], limits,
});

test('a workspace capped at a fraction of the org is the finding', () => {
  const entry = wsGroup(['claude-opus-5'], [
    { type: 'input_tokens_per_minute', value: 500000, org_limit: 10000000 },
    { type: 'requests_per_minute', value: 1000, org_limit: 4000 },
  ]);
  const rows = overridesOf(entry);
  assert.deepEqual(rows.map((r) => r[0]),
                   ['requests_per_minute', 'input_tokens_per_minute']);
  const [state, detail] = gradeOverride(500000, 10000000);
  assert.equal(state, 'throttled-below-org');
  assert.equal(detail, '500,000 of 10,000,000 (5%)');
  assert.equal(verdict(rows.map((r) => gradeOverride(r[1], r[2])[0])),
               'throttled-below-org');
  assert.ok(repairLines(state).some((l) => l.includes('Rate limits tab')));
});

test('an override equal to the org value is a pin, not a no-op', () => {
  const [state, detail] = gradeOverride(10000000, 10000000);
  assert.equal(state, 'override-pinned-at-org');
  assert.match(detail, /will not follow the next increase/);
  assert.ok(repairLines(state).some((l) => l.includes('Delete the override')));
  const [above, aboveDetail] = gradeOverride(20000000, 10000000);
  assert.equal(above, 'override-above-org');
  assert.match(aboveDetail, /applies anyway/);
});

test('a null org_limit is unjudgeable and never becomes zero', () => {
  assert.equal(num(null), null);
  assert.equal(num('nope'), null);
  assert.equal(num(true), null);
  const [state, detail] = gradeOverride(500000, null);
  assert.equal(state, 'org-limit-unknown');
  assert.match(detail, /cannot be graded/);
  assert.equal(gradeOverride(0, 10000000)[0], 'throttled-below-org');
});

test('limiters absent from an overridden group are reported as inherited', () => {
  const org = orgIndex([{ data: [orgGroup(['claude-opus-5'], {
    requests_per_minute: 4000,
    input_tokens_per_minute: 10000000,
    output_tokens_per_minute: 2000000,
  })] }]);
  const label = groupLabel(orgGroup(['claude-opus-5'], {}));
  const entry = wsGroup(['claude-opus-5'], [
    { type: 'input_tokens_per_minute', value: 500000, org_limit: 10000000 },
    { type: 'requests_per_minute', value: 1000, org_limit: 4000 },
  ]);
  assert.deepEqual(inheritedLimiters(entry, org[label]),
                   [['output_tokens_per_minute', 2000000]]);
  assert.equal(verdict(['override-in-range', 'limiter-inherited']), 'limiter-inherited');
});

test('the two endpoints label the same group identically', () => {
  const models = ['claude-opus-4-8', 'claude-opus-4-5'];
  assert.equal(groupLabel(orgGroup(models, {})), groupLabel(wsGroup(models, [])));
  assert.equal(groupLabel(orgGroup(models, {})), 'model_group:claude-opus-4-5 +1');
  assert.equal(groupLabel({ group_type: 'batch', models: null }), 'batch');
  assert.equal(groupLabel(null), 'unknown_group');
  assert.deepEqual(limitsOf({ limits: [{ type: 'x', value: 'not-a-number' }] }), {});
});

test('openai needs a peer because the object has no org value', () => {
  const one = openaiMatrix({ proj_a: [{ model: 'gpt-5.6',
    max_requests_per_1_minute: 60, max_tokens_per_1_minute: 150000 }] });
  assert.deepEqual(openaiOutliers(one), []);
  const both = openaiMatrix({
    proj_a: [{ model: 'gpt-5.6', max_requests_per_1_minute: 10000,
               max_tokens_per_1_minute: 2000000 }],
    proj_b: [{ model: 'gpt-5.6', max_requests_per_1_minute: 9000,
               max_tokens_per_1_minute: 150000 },
             { model: '', max_tokens_per_1_minute: 1 }],
  });
  assert.deepEqual(Object.keys(both['gpt-5.6'] ?? {}).sort(), ['proj_a', 'proj_b']);
  assert.equal(both[''], undefined);
  assert.deepEqual(openaiOutliers(both),
                   [['gpt-5.6', 'proj_b', 'tpm', 150000, 2000000]]);
  assert.ok(repairLines('project-outlier').some((l) => l.includes('proxy for the tier')));
});

test('empty and absent inputs do not raise', () => {
  assert.deepEqual(orgIndex(null), {});
  assert.deepEqual(overridesOf(null), []);
  assert.deepEqual(openaiMatrix(null), {});
  assert.deepEqual(openaiOutliers(null), []);
  assert.deepEqual(inheritedLimiters(null, null), []);
  assert.equal(verdict([]), 'no-override');
  assert.equal(verdict(null), 'no-override');
  assert.equal(gradeOverride(null, 10)[0], 'no-override');
  assert.deepEqual(repairLines('no-override'), []);
});
''',
"faq": [
 ("How is this different from reading the x-ratelimit headers on a live call?",
  "Those headers describe the call you just made, at the moment you made it, and they only exist if something is making calls. This reads stored configuration, which is why it can grade a workspace that has been dark for a month, a project that is about to receive a launch, or a container that provisioning automation created last night. The two answer different questions: headroom now, versus which container was given a lower ceiling than the organization and when that decision will start to hurt. If you want the live reading, that is the rate limit headers note."),
 ("A workspace has no entry on the rate limits endpoint at all. Is that bad?",
  "No, that is the healthy state. The workspace endpoint returns overrides only, so an absent group means no override exists and the workspace inherits the organization limit for it. What matters is that inheriting and being unlimited look identical from that response alone, so the script reads the organization endpoint alongside it and prints the inherited number rather than a blank. The default workspace is a special case: it cannot carry overrides at all, so it never appears here and its limits are the organization's by definition."),
 ("Why is an override that equals the organization limit worth reporting?",
  "Because it is the difference between tracking and pinning. With no override, a workspace's limits follow the organization's, so a tier increase reaches it without anybody doing anything. With an override that happens to equal today's organization value, the workspace is on a fixed number, and the next increase goes to every other container and not to that one. It feels like a no-op when you set it, it behaves like one for months, and it stops behaving like one on the day it matters most. The repair is to delete the override rather than to adjust it."),
 ("Why can the OpenAI half only compare projects against each other?",
  "Because the object does not carry the other number. The published schema for project.rate_limit is object, id, model, max_requests_per_1_minute, max_tokens_per_1_minute, and some optional per-modality fields for images, audio, daily requests and batch input tokens. There is no organization value on it and no organization-wide rate limits endpoint to fetch one from. So the script compares the same model row across every project, uses the peer maximum as a stand-in for the tier, prints that it is a stand-in, and refuses to grade at all when there is only one project."),
 ("Can the script just raise the limit once it finds one?",
  "No, and the two providers refuse it differently. OpenAI does expose an update at /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}, which this script prints and never calls, because every script in this section holds a credential that can spend money and none of them write. Anthropic has no write endpoint for workspace rate limits at all: its own Rate Limits API documentation says they are set in the Console. So on that side the output is deliberately a workspace id, a group, a limiter and a number for a person to go and change."),
],
"related": [REL_HEADROOM, REL_RAMP, REL_TOPO],
"citations": [CITE_RL_API, CITE_WS_RL, CITE_OA_PRL, CITE_RL],
},
{
"slug": "acceleration-limit-on-traffic-spike",
"title": "429s while every minute sits under the configured limit",
"description": "Adjacent one-minute buckets show a steep ramp whose peak is far below every ceiling. The acceleration limit refused you, not the number in the tier table.",
"h1": "429s while every minute sits under the configured limit",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic acceleration limit 429 sharp increase",
             "429 below published rate limit tier",
             "60 rpm enforced as 1 request per second",
             "usage_report messages bucket_width 1m ramp",
             "evaluation tier limits below standard"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key or another organization-scoped read credential. Reads two GETs and never sends a message. Usage data lands within about five minutes, so the most recent bucket or two may still be filling.",
"lead": "The backfill went out at 09:00 and 429ed for eleven minutes. Somebody pulled the usage report afterwards, and the worst minute in the whole window used a fifth of the organization's input tokens per minute. Nobody believes the graph, so the ticket says <em>rate limit increase required</em> and the increase, when it arrives, changes nothing: the same job trips at the same point next Tuesday, still using a fifth of a limit that is now twice as big.",
"short_answer": """<p>Two GETs with an <strong>Admin API key</strong>. <code>GET /v1/organizations/usage_report/messages?starting_at={T-4h}&amp;bucket_width=1m&amp;limit=240&amp;group_by[]=model</code> for the minute-by-minute shape, and <code>GET /v1/organizations/rate_limits</code> for the numbers those minutes are being measured against.</p>
<p>Then look at two things rather than one. The <strong>peak</strong> minute against the configured ITPM and OTPM for that model's group, which is the reading everybody already does. And the <strong>ramp</strong>: the ratio between each minute and the one before it. A tenfold step between adjacent minutes with a peak that never gets past a third of the ceiling is the signature, and it is a signature that no limit increase repairs, because the documented cause is the sharpness of the increase rather than its size.</p>
<p>Two mechanisms produce it and the script names both. Acceleration limits fire on a sharp increase in organization usage, and the published advice is to ramp gradually and keep patterns consistent. Sub-minute enforcement does the rest: 60 requests per minute may be enforced as one request per second, so sixty requests fired in the same second trip a limit that a per-minute counter says was never approached.</p>
<p>Input is measured the way the limiter measures it: <code>uncached_input_tokens</code> plus both <code>cache_creation</code> fields, with <code>cache_read_input_tokens</code> left out because cache reads do not count toward ITPM on current models. And the report carries <strong>no request count at all</strong> &mdash; its result fields are token sums and server tool calls &mdash; so the ramp here is measured in tokens, and the script says so rather than implying a request rate it cannot see.</p>
<p>If the peak minute <em>does</em> reach the ceiling, this is not the note. The script says which limiter saturated and hands the reading to <a href="/llm/itpm-exhausted-uncached-input/">the input limiter note</a> or <a href="/llm/otpm-exhausted/">the output one</a> rather than grading a ramp that has an ordinary explanation.</p>""",
"problem": """<p>Rate limiting on this API is a token bucket that refills continuously, and the published tier tables give you one number per limiter per model. Everybody treats those numbers as the contract: stay under them and you are fine. The trouble is that they describe a maximum sustained rate, and nothing in them describes how fast you are allowed to get there.</p>
<p>Two things enforce the approach rather than the level. Acceleration limits are documented plainly: a sharp increase in an organization's usage can produce 429s on its own, and the remedy given is to ramp gradually and keep usage patterns consistent. And enforcement happens over intervals shorter than a minute, so a limit expressed per minute can be applied per second. A cron that fans out its entire fleet at the top of the hour, a queue worker that drains a backlog as fast as it can, a launch that turns a feature on for everybody at once: all of these produce a shape that is nowhere near the ceiling on average and violently over it for a moment.</p>
<p>What makes it so durable is that the evidence looks like exoneration. You go to the usage data, you find the worst minute, it is comfortably under the limit, and the only remaining explanation seems to be that the limit is wrong or the platform is wrong. So the team asks for more capacity. The increase arrives, the same job runs the same way, and the failure comes back at the same point in the ramp, because the thing that refused it was never the headline number.</p>
<p>There is a third possibility that costs a lot of debugging time when nobody knows about it. New organizations and organizations with limited history may sit in an Evaluation tier whose limits are below the published tables entirely. Reading the documentation table and assuming it applies is then wrong before any of this starts.</p>""",
"why": """<p><strong>The finding is a shape between two buckets, not a level in one.</strong> Every other rate-limit note in this section grades a value against a ceiling: how close is the peak, which limiter emptied, how much headroom is left. This one fires precisely when that grading comes back clean. The measurement is minute-over-minute change, the threshold is a factor rather than a number, and a workload with a large steady peak scores better here than a small spiky one, which is the opposite of how the other notes rank things.</p>
<p><strong>A saturated limiter has to be excluded first, or the ramp is a coincidence.</strong> Steep ramps are extremely common and most of them are harmless. What makes one diagnostic is the combination: a steep step <em>and</em> a peak that never gets near the ceiling. So the script checks saturation before it checks anything else and, if it finds it, stops and names the note that owns that reading. A finding that fires alongside its own ordinary explanation is not a finding.</p>
<p><strong>Input has to be summed the way the limiter counts it.</strong> Only uncached input counts toward ITPM: <code>uncached_input_tokens</code> and both <code>cache_creation</code> fields, and not <code>cache_read_input_tokens</code>, on every current model. Summing all input instead inflates every bucket by the cached share, which on a caching workload can be most of it, and turns a comfortable ramp into a false saturation. The one documented exception is Claude Haiku 3.5, where cache reads do count; the script flags that model rather than silently applying the wrong rule to it.</p>
<p><strong>There is no request count on this report, and the honest move is to say so.</strong> The messages usage report returns token sums, cache figures and server tool calls. There is no field anywhere in it for the number of requests, which means the sub-minute burst argument &mdash; sixty requests in one second against a limit enforced per second &mdash; cannot be measured here at all. The script measures the token ramp, reports it as a token ramp, and prints the request-rate question as something to answer from your own client-side counters.</p>
<p><strong>A minute bucket cannot show a one-second burst, and that is exactly why it is the right instrument.</strong> The bucket is not being asked to catch the burst. It is being asked to prove that the minute was not the problem, which it does conclusively, and that proof is what redirects the investigation from the size of the limit to the shape of the traffic.</p>""",
"steps": [
 {"h": "Use an Admin API key and pick a window that contains the incident",
  "body": """<p>The usage report is Admin API territory: an Admin API key, an OAuth token with the <code>org:admin</code> scope, or a personal or service account key that is not scoped to a workspace. Minute buckets go up to 1,440 of them, so 24 hours is the maximum window at this granularity. Four hours around the event is usually enough and pages faster.</p>"""},
 {"h": "Read the minute buckets grouped by model",
  "body": """<p><code>starting_at</code> and <code>ending_at</code> are RFC 3339 and buckets snap to the start of the minute in UTC. <code>group_by[]=model</code> is what makes the comparison possible at all, since limits are per model group. Empty minutes come back as buckets with an empty <code>results</code> list, which is information: a gap is not a missing bucket.</p>"""},
 {"h": "Sum each minute the way the limiter does",
  "body": """<p>Input per minute is <code>uncached_input_tokens</code> plus <code>cache_creation.ephemeral_5m_input_tokens</code> plus <code>cache_creation.ephemeral_1h_input_tokens</code>. Output per minute is <code>output_tokens</code>. Leave <code>cache_read_input_tokens</code> out of the input sum on every current model, and note it separately for Claude Haiku 3.5, where it counts.</p>"""},
 {"h": "Read the configured numbers and check them against the published tier",
  "body": """<p><code>GET /v1/organizations/rate_limits</code> returns each group's <code>models</code> list and its <code>limits[]</code> of <code>{type, value}</code>. Match the model to its group by exact membership. If a configured value sits below the published Start-tier figure for that model, the organization is probably in the Evaluation tier and the documentation tables do not apply to it &mdash; which is worth knowing before anybody reasons from them again.</p>"""},
 {"h": "Grade saturation first, then the ramp",
  "body": """<p>If the peak minute is at or above 85% of a ceiling, name that limiter and stop: the sibling notes own that reading. Otherwise compute the largest ratio between adjacent minutes over a meaningful base, and report a steep step under a low peak as the acceleration signature. The repair is client-side pacing &mdash; ramp gradually, spread bursts across the minute, put a queue in front of the fan-out &mdash; and the script changes no traffic.</p>"""},
],
"verify": """<p>Re-run after pacing the job. The peak minute should barely move &mdash; the same work is being done &mdash; while the largest adjacent-minute ratio falls, and the verdict moves from <code>acceleration-suspect</code> to <code>steady</code>. A run that comes back <code>limiter-saturated</code> instead means the pacing worked well enough that you are now genuinely against a ceiling, which is a different note and a real reason to ask for an increase.</p>
<pre><code class="language-bash">python3 anthropic_ramp_acceleration.py --hours 4
# 240 minute bucket(s), 3 model(s), 6 rate limit group(s)
# acceleration-suspect  claude-opus-5
#   peak input   1,940,000/min against ITPM 10,000,000 (19%)
#   peak output    210,000/min against OTPM  2,000,000 (11%)
#   steepest ramp  14.8x between 09:03 and 09:04 (131,000 -> 1,940,000)
#   note: this report carries no request count, so the ramp above is measured
#         in tokens. Sub-minute bursting is invisible at this granularity.
#   repair: ramp gradually and keep usage patterns consistent. A step this
#           steep can 429 on acceleration alone, well under the tier limits.
#   repair: spread the burst across the minute with client-side pacing or a
#           queue in front of the fan-out. A limit of 60 per minute may be
#           enforced as 1 per second.
# limiter-saturated     claude-sonnet-5: output peaked at 1,870,000/min, 94% of
#                       OTPM. That is the output limiter note, not this one.
# below-published-start claude-fable-5: configured ITPM 250,000 is under the
#                       published Start tier figure of 500,000, so this
#                       organization may be in the Evaluation tier.
# 2 finding(s)</code></pre>""",
"code_intro": "The network part is two GETs; everything that decides anything is pure. <code>uncached_input</code>, which sums a bucket the way ITPM counts it and leaves cache reads out; <code>series</code>, which folds the paged buckets into one ordered list of minutes per model and keeps empty minutes as zeros rather than dropping them; <code>ramp_factors</code>, which computes adjacent-minute ratios only over a base big enough to mean something, so a jump from 12 tokens to 900 is not reported as a 75x ramp; <code>peak</code> and <code>share</code>; <code>group_for_model</code>, which resolves a model id to its limiter group by exact membership; <code>below_published_start</code>, which compares configured numbers against the published Start tier and is the Evaluation-tier check; and <code>verdict</code>, which tests saturation before it tests the ramp and hands saturated models to their own notes by name.",
"py_file": "anthropic_ramp_acceleration.py",
"py": '''"""Find 429s caused by the ramp rather than by the limit.

Read only. Two GETs with an Admin API key:

  GET /v1/organizations/usage_report/messages?bucket_width=1m&group_by[]=model
  GET /v1/organizations/rate_limits

The finding is a shape between two adjacent minutes, not a level in one. A steep
step whose peak never approaches the configured ceiling is the acceleration
signature: a sharp increase in usage can produce 429s on its own, and limits
expressed per minute can be enforced over shorter intervals.

Saturation is graded first. A peak that does reach the ceiling has an ordinary
explanation and belongs to the ITPM or OTPM notes, and this script says so
instead of reporting a ramp next to it.

Input is summed the way the limiter counts it: uncached input plus both cache
creation figures, and not cache reads. This report has no request count of any
kind, so the ramp is measured in tokens and reported as such.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_ramp_acceleration")

API = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

# The published Start tier figures, as (ITPM, OTPM), used only to spot an
# organization whose configured numbers sit below the documented floor, which
# is what the Evaluation tier looks like from the outside. This is a
# documentation table and documentation tables move; it is printed as "below
# the published Start tier", never as a claim about what your tier is.
START_TIER = {
    "claude-fable-5": (500_000, 100_000),
    "claude-haiku-3-5": (100_000, 20_000),
}
START_TIER_DEFAULT = (2_000_000, 400_000)

# Claude Haiku 3.5 counts cache reads toward ITPM. Every other current model
# does not. Applying one rule to both is how a caching workload gets reported
# as saturated when it is nowhere near its limit.
COUNTS_CACHE_READS = ("claude-haiku-3-5",)

SATURATED = 0.85
QUIET = 0.60

FINDINGS = ("acceleration-suspect", "ramp-near-ceiling", "below-published-start")


def num(value):
    """A float, or 0.0. Pure."""
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def cache_creation(result):
    """Both cache creation figures, summed. Pure.

    They are separate fields for the 5 minute and 1 hour entries and both count
    toward the input limiter, so a reader that knows about only one of them
    undercounts every cached workload.
    """
    block = (result or {}).get("cache_creation") or {}
    return (num(block.get("ephemeral_5m_input_tokens"))
            + num(block.get("ephemeral_1h_input_tokens")))


def uncached_input(result):
    """The input tokens that count toward ITPM. Pure.

    uncached_input_tokens plus cache creation. cache_read_input_tokens is
    deliberately absent: it does not count toward the input limiter on current
    models, and including it inflates a cached workload's every bucket.
    """
    return num((result or {}).get("uncached_input_tokens")) + cache_creation(result)


def series(pages, model_key="model"):
    """{model: [(starting_at, input_tokens, output_tokens, cache_read)]}. Pure.

    Ordered by bucket start. A bucket with an empty results list contributes
    nothing, which keeps a gap in traffic visible as a gap rather than being
    silently closed up by the next minute that had data.
    """
    out = {}
    for page in pages or []:
        for bucket in ((page or {}).get("data") or []):
            start = str((bucket or {}).get("starting_at") or "")
            for result in ((bucket or {}).get("results") or []):
                model = str((result or {}).get(model_key) or "(ungrouped)")
                out.setdefault(model, []).append(
                    (start, uncached_input(result),
                     num((result or {}).get("output_tokens")),
                     num((result or {}).get("cache_read_input_tokens"))))
    for rows in out.values():
        rows.sort(key=lambda r: r[0])
    return out


def peak(rows, index):
    """(starting_at, value) for the largest bucket. Pure. ("", 0.0) if empty."""
    best = ("", 0.0)
    for row in rows or []:
        if row[index] > best[1]:
            best = (row[0], row[index])
    return best


def share(value, limit):
    """value / limit, or None when the limit is unknown. Pure."""
    if not limit or limit <= 0:
        return None
    return float(value) / float(limit)


def ramp_factors(rows, index, min_base=10_000.0):
    """[(prev_start, start, factor, prev, current)] between adjacent minutes.

    Pure, largest factor first. Ratios are computed only where the earlier
    minute is above min_base, because 12 tokens followed by 900 is a 75x ratio
    and means nothing at all. A rise from a genuine standing start is real but
    it is not what this measures, so it is left out rather than dominating.
    """
    out = []
    rows = list(rows or [])
    for i in range(1, len(rows)):
        prev = rows[i - 1][index]
        current = rows[i][index]
        if prev < min_base or current <= prev:
            continue
        out.append((rows[i - 1][0], rows[i][0], current / prev, prev, current))
    out.sort(key=lambda r: (-r[2], r[1]))
    return out


def group_for_model(groups, model):
    """{limiter_type: value} for the group that contains this model. Pure.

    Membership is exact: every model id and alias that counts against a group is
    listed on it, so a prefix match would only ever be a way to get the wrong
    group for a model the API already told you about.
    """
    for entry in groups or []:
        models = [str(m) for m in ((entry or {}).get("models") or [])]
        if str(model) in models:
            out = {}
            for row in ((entry or {}).get("limits") or []):
                ltype = str((row or {}).get("type") or "")
                if ltype:
                    out[ltype] = num((row or {}).get("value"))
            return out
    return {}


def below_published_start(model, limits):
    """[(limiter, configured, published_start)] below the documented floor. Pure."""
    itpm_floor, otpm_floor = START_TIER.get(str(model), START_TIER_DEFAULT)
    out = []
    pairs = (("input_tokens_per_minute", itpm_floor),
             ("output_tokens_per_minute", otpm_floor))
    for ltype, floor in pairs:
        configured = (limits or {}).get(ltype)
        if configured and 0 < configured < floor:
            out.append((ltype, configured, floor))
    return out


def verdict(rows, limits, model, ramp_threshold=3.0):
    """Classify one model's window. Pure. Returns (state, detail, facts).

    Saturation is answered first and handed to the note that owns it. A ramp
    reported next to a saturated limiter would be a coincidence dressed up as a
    cause.
    """
    rows = list(rows or [])
    limits = limits or {}
    facts = {
        "peak_in": peak(rows, 1),
        "peak_out": peak(rows, 2),
        "itpm": limits.get("input_tokens_per_minute"),
        "otpm": limits.get("output_tokens_per_minute"),
        "ramps": ramp_factors(rows, 1) + ramp_factors(rows, 2),
        "cache_read_counts": str(model) in COUNTS_CACHE_READS,
    }
    facts["ramps"].sort(key=lambda r: -r[2])
    in_share = share(facts["peak_in"][1], facts["itpm"])
    out_share = share(facts["peak_out"][1], facts["otpm"])
    facts["in_share"] = in_share
    facts["out_share"] = out_share

    if not rows or (facts["peak_in"][1] <= 0 and facts["peak_out"][1] <= 0):
        return ("no-traffic", "no usage in this window", facts)
    if in_share is not None and in_share >= SATURATED:
        return ("limiter-saturated",
                "input peaked at %s/min, %.0f%% of ITPM. That is the input "
                "limiter note, not this one."
                % (fmt(facts["peak_in"][1]), in_share * 100), facts)
    if out_share is not None and out_share >= SATURATED:
        return ("limiter-saturated",
                "output peaked at %s/min, %.0f%% of OTPM. That is the output "
                "limiter note, not this one."
                % (fmt(facts["peak_out"][1]), out_share * 100), facts)

    steepest = facts["ramps"][0][2] if facts["ramps"] else 0.0
    if steepest < ramp_threshold:
        return ("steady",
                "no adjacent minute rose by %.1fx or more" % ramp_threshold, facts)
    quiet = [s for s in (in_share, out_share) if s is not None]
    if quiet and max(quiet) <= QUIET:
        return ("acceleration-suspect",
                "a %.1fx step between adjacent minutes with every peak under "
                "%.0f%% of its ceiling" % (steepest, QUIET * 100), facts)
    return ("ramp-near-ceiling",
            "a %.1fx step between adjacent minutes, and the peak is already "
            "past %.0f%% of a ceiling. Pace it and ask for the increase."
            % (steepest, QUIET * 100), facts)


def fmt(value):
    """Thousands separators. Pure."""
    return "{:,}".format(int(round(num(value))))


def repair_lines(state, facts=None):
    """The repair for one verdict. Pure. Printed, never performed."""
    facts = facts or {}
    if state == "acceleration-suspect":
        lines = ["ramp gradually and keep usage patterns consistent. A step this "
                 "steep can 429 on acceleration alone, well under the tier limits, "
                 "and a limit increase does not change it.",
                 "spread the burst across the minute with client-side pacing or a "
                 "queue in front of the fan-out. A limit of 60 per minute may be "
                 "enforced as 1 per second, so the shape inside the minute matters."]
        if facts.get("cache_read_counts"):
            lines.append("this model counts cache reads toward the input limiter, "
                         "unlike the others. Add cache_read_input_tokens back "
                         "before comparing its peak against ITPM.")
        return lines
    if state == "ramp-near-ceiling":
        return ["pace the ramp and request the increase. Both are true here: the "
                "step is steep enough to trip acceleration and the peak is close "
                "enough that a bigger ceiling would also help."]
    if state == "limiter-saturated":
        return ["this one really is the headline number. Read the input or output "
                "limiter note for the reading that fits, rather than pacing "
                "traffic that is genuinely at its ceiling."]
    if state == "below-published-start":
        return ["configured limits below the published Start tier usually mean an "
                "Evaluation tier organization, where the documentation tables do "
                "not apply. Stop reasoning from the tables and read "
                "/v1/organizations/rate_limits instead.",
                "Evaluation limits rise automatically as the organization builds "
                "usage history, so this is a reason to pace traffic rather than a "
                "reason to file anything."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: the usage report and the rate limits "
                         "endpoint need an Admin API credential, not a workspace "
                         "key" % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, **params):
    params = dict(params)
    for _ in range(50):
        page = get(session, path, **params)
        yield page
        nxt = page.get("next_page")
        if not nxt:
            return
        params["page"] = nxt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=float, default=4.0,
                    help="window to read, in hours (max 24 at minute buckets)")
    ap.add_argument("--ramp", type=float, default=3.0,
                    help="adjacent-minute factor that counts as a steep step")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not key:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key or another "
                  "organization scoped read credential")
        return 2
    hours = max(0.1, min(24.0, args.hours))

    s = requests.Session()
    s.headers.update({"x-api-key": key,
                      "anthropic-version": ANTHROPIC_VERSION,
                      "User-Agent": "anthropic-ramp-acceleration/1.0"})

    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    start = now - dt.timedelta(hours=hours)
    stamp = "%Y-%m-%dT%H:%M:%SZ"

    buckets = list(pages(s, "/organizations/usage_report/messages",
                         starting_at=start.strftime(stamp),
                         ending_at=now.strftime(stamp),
                         bucket_width="1m", limit=1440,
                         **{"group_by[]": "model"}))
    groups = []
    for page in pages(s, "/organizations/rate_limits"):
        groups.extend(page.get("data") or [])

    by_model = series(buckets)
    minutes = sum(len(page.get("data") or []) for page in buckets)
    log.info("%d minute bucket(s), %d model(s), %d rate limit group(s)",
             minutes, len(by_model), len(groups))

    findings = 0
    for model in sorted(by_model):
        rows = by_model[model]
        limits = group_for_model(groups, model)
        state, detail, facts = verdict(rows, limits, model, args.ramp)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-21s %s: %s", state, model, detail)

        if state in ("acceleration-suspect", "ramp-near-ceiling", "steady"):
            emit("  peak input   %s/min against ITPM %s (%s)",
                 fmt(facts["peak_in"][1]), fmt(facts["itpm"] or 0),
                 "unknown" if facts["in_share"] is None
                 else "%.0f%%" % (facts["in_share"] * 100))
            emit("  peak output  %s/min against OTPM %s (%s)",
                 fmt(facts["peak_out"][1]), fmt(facts["otpm"] or 0),
                 "unknown" if facts["out_share"] is None
                 else "%.0f%%" % (facts["out_share"] * 100))
            if facts["ramps"]:
                prev_at, at, factor, prev, current = facts["ramps"][0]
                emit("  steepest ramp %.1fx between %s and %s (%s -> %s)",
                     factor, prev_at[11:16] or prev_at, at[11:16] or at,
                     fmt(prev), fmt(current))
            emit("  note: this report carries no request count, so the ramp above "
                 "is measured in tokens. Sub-minute bursting is invisible here.")

        for line in repair_lines(state, facts):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

        for ltype, configured, floor in below_published_start(model, limits):
            log.warning("%-21s %s: configured %s is %s, under the published Start "
                        "tier figure of %s", "below-published-start", model, ltype,
                        fmt(configured), fmt(floor))
            for line in repair_lines("below-published-start"):
                log.warning("  repair: %s", line)
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-ramp-acceleration.mjs",
"js": '''/**
 * Find 429s caused by the ramp rather than by the limit.
 *
 * Read only. Two GETs with an Admin API key: the messages usage report at
 * minute granularity grouped by model, and the configured rate limits.
 *
 * The finding is a shape between two adjacent minutes, not a level in one: a
 * steep step whose peak never approaches the ceiling. Saturation is graded
 * first and handed to the ITPM and OTPM notes, because a ramp reported next to
 * a saturated limiter is a coincidence dressed up as a cause.
 *
 * Input is summed the way the limiter counts it. This report has no request
 * count of any kind, so the ramp is measured in tokens and reported as such.
 */
const API = 'https://api.anthropic.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

export const START_TIER = {
  'claude-fable-5': [500000, 100000],
  'claude-haiku-3-5': [100000, 20000],
};
const START_TIER_DEFAULT = [2000000, 400000];
const COUNTS_CACHE_READS = new Set(['claude-haiku-3-5']);

const SATURATED = 0.85;
const QUIET = 0.60;
const FINDINGS = new Set(['acceleration-suspect', 'ramp-near-ceiling',
                          'below-published-start']);

/** A number, or 0. Pure. */
export function num(value) {
  if (value === null || value === undefined || typeof value === 'boolean') return 0;
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

/** Both cache creation figures, summed. Pure. */
export function cacheCreation(result) {
  const block = result?.cache_creation ?? {};
  return num(block.ephemeral_5m_input_tokens) + num(block.ephemeral_1h_input_tokens);
}

/** The input tokens that count toward ITPM. Pure. Cache reads excluded. */
export function uncachedInput(result) {
  return num(result?.uncached_input_tokens) + cacheCreation(result);
}

/** {model: [[startingAt, input, output, cacheRead]]}. Pure, ordered. */
export function series(pages, modelKey = 'model') {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      const start = String(bucket?.starting_at ?? '');
      for (const result of bucket?.results ?? []) {
        const model = String(result?.[modelKey] ?? '(ungrouped)');
        (out[model] ??= []).push([start, uncachedInput(result),
                                  num(result?.output_tokens),
                                  num(result?.cache_read_input_tokens)]);
      }
    }
  }
  for (const rows of Object.values(out)) rows.sort((a, b) => a[0].localeCompare(b[0]));
  return out;
}

/** [startingAt, value] for the largest bucket. Pure. */
export function peak(rows, index) {
  let best = ['', 0];
  for (const row of rows ?? []) if (row[index] > best[1]) best = [row[0], row[index]];
  return best;
}

/** value / limit, or null when the limit is unknown. Pure. */
export function share(value, limit) {
  if (!limit || limit <= 0) return null;
  return value / limit;
}

/** [[prevStart, start, factor, prev, current]], largest factor first. Pure. */
export function rampFactors(rows, index, minBase = 10000) {
  const out = [];
  const list = rows ?? [];
  for (let i = 1; i < list.length; i += 1) {
    const prev = list[i - 1][index];
    const current = list[i][index];
    if (prev < minBase || current <= prev) continue;
    out.push([list[i - 1][0], list[i][0], current / prev, prev, current]);
  }
  out.sort((a, b) => (b[2] - a[2]) || a[1].localeCompare(b[1]));
  return out;
}

/** {limiterType: value} for the group containing this model. Pure. Exact match. */
export function groupForModel(groups, model) {
  for (const entry of groups ?? []) {
    const models = (entry?.models ?? []).map(String);
    if (models.includes(String(model))) {
      const out = {};
      for (const row of entry?.limits ?? []) {
        const ltype = String(row?.type ?? '');
        if (ltype) out[ltype] = num(row?.value);
      }
      return out;
    }
  }
  return {};
}

/** [[limiter, configured, publishedStart]] below the documented floor. Pure. */
export function belowPublishedStart(model, limits) {
  const [itpmFloor, otpmFloor] = START_TIER[String(model)] ?? START_TIER_DEFAULT;
  const out = [];
  for (const [ltype, floor] of [['input_tokens_per_minute', itpmFloor],
                                ['output_tokens_per_minute', otpmFloor]]) {
    const configured = limits?.[ltype];
    if (configured && configured > 0 && configured < floor) {
      out.push([ltype, configured, floor]);
    }
  }
  return out;
}

/** Thousands separators. Pure. */
export function fmt(value) {
  return Math.round(num(value)).toLocaleString('en-US');
}

/** Classify one model's window. Pure. Returns [state, detail, facts]. */
export function verdict(rows, limits, model, rampThreshold = 3.0) {
  const list = rows ?? [];
  const lim = limits ?? {};
  const facts = {
    peakIn: peak(list, 1),
    peakOut: peak(list, 2),
    itpm: lim.input_tokens_per_minute,
    otpm: lim.output_tokens_per_minute,
    ramps: [...rampFactors(list, 1), ...rampFactors(list, 2)].sort((a, b) => b[2] - a[2]),
    cacheReadCounts: COUNTS_CACHE_READS.has(String(model)),
  };
  facts.inShare = share(facts.peakIn[1], facts.itpm);
  facts.outShare = share(facts.peakOut[1], facts.otpm);

  if (list.length === 0 || (facts.peakIn[1] <= 0 && facts.peakOut[1] <= 0)) {
    return ['no-traffic', 'no usage in this window', facts];
  }
  if (facts.inShare !== null && facts.inShare >= SATURATED) {
    return ['limiter-saturated',
            `input peaked at ${fmt(facts.peakIn[1])}/min, `
            + `${Math.round(facts.inShare * 100)}% of ITPM. That is the input `
            + 'limiter note, not this one.', facts];
  }
  if (facts.outShare !== null && facts.outShare >= SATURATED) {
    return ['limiter-saturated',
            `output peaked at ${fmt(facts.peakOut[1])}/min, `
            + `${Math.round(facts.outShare * 100)}% of OTPM. That is the output `
            + 'limiter note, not this one.', facts];
  }

  const steepest = facts.ramps.length ? facts.ramps[0][2] : 0;
  if (steepest < rampThreshold) {
    return ['steady', `no adjacent minute rose by ${rampThreshold.toFixed(1)}x or more`,
            facts];
  }
  const shares = [facts.inShare, facts.outShare].filter((s) => s !== null);
  if (shares.length && Math.max(...shares) <= QUIET) {
    return ['acceleration-suspect',
            `a ${steepest.toFixed(1)}x step between adjacent minutes with every `
            + `peak under ${Math.round(QUIET * 100)}% of its ceiling`, facts];
  }
  return ['ramp-near-ceiling',
          `a ${steepest.toFixed(1)}x step between adjacent minutes, and the peak is `
          + `already past ${Math.round(QUIET * 100)}% of a ceiling. Pace it and ask `
          + 'for the increase.', facts];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, facts) {
  if (state === 'acceleration-suspect') {
    const lines = ['ramp gradually and keep usage patterns consistent. A step this '
      + 'steep can 429 on acceleration alone, well under the tier limits, and a '
      + 'limit increase does not change it.',
      'spread the burst across the minute with client-side pacing or a queue in '
      + 'front of the fan-out. A limit of 60 per minute may be enforced as 1 per '
      + 'second, so the shape inside the minute matters.'];
    if (facts?.cacheReadCounts) {
      lines.push('this model counts cache reads toward the input limiter, unlike '
        + 'the others. Add cache_read_input_tokens back before comparing its peak '
        + 'against ITPM.');
    }
    return lines;
  }
  if (state === 'ramp-near-ceiling') {
    return ['pace the ramp and request the increase. Both are true here: the step '
      + 'is steep enough to trip acceleration and the peak is close enough that a '
      + 'bigger ceiling would also help.'];
  }
  if (state === 'limiter-saturated') {
    return ['this one really is the headline number. Read the input or output '
      + 'limiter note for the reading that fits, rather than pacing traffic that '
      + 'is genuinely at its ceiling.'];
  }
  if (state === 'below-published-start') {
    return ['configured limits below the published Start tier usually mean an '
      + 'Evaluation tier organization, where the documentation tables do not '
      + 'apply. Stop reasoning from the tables and read /v1/organizations/'
      + 'rate_limits instead.',
      'Evaluation limits rise automatically as the organization builds usage '
      + 'history, so this is a reason to pace traffic rather than a reason to '
      + 'file anything.'];
  }
  return [];
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) url.searchParams.append(k, String(v));
  const r = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION,
               'User-Agent': 'anthropic-ramp-acceleration/1.0' },
  });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from Anthropic: the usage report and the rate `
                    + 'limits endpoint need an Admin API credential');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function pages(key, path, params) {
  const out = [];
  const q = { ...(params ?? {}) };
  for (let i = 0; i < 50; i += 1) {
    const page = await read(key, path, q);
    out.push(page);
    if (!page.next_page) break;
    q.page = page.next_page;
  }
  return out;
}

async function main() {
  const key = process.env.ANTHROPIC_ADMIN_KEY;
  if (!key) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key or another '
                  + 'organization scoped read credential');
    process.exitCode = 2;
    return;
  }
  const hours = Math.max(0.1, Math.min(24, Number(process.env.HOURS ?? 4)));
  const rampThreshold = Number(process.env.RAMP ?? 3);

  const now = new Date();
  now.setUTCSeconds(0, 0);
  const start = new Date(now.getTime() - hours * 3600 * 1000);
  const stamp = (d) => `${d.toISOString().slice(0, 19)}Z`;

  const buckets = await pages(key, '/organizations/usage_report/messages', {
    starting_at: stamp(start), ending_at: stamp(now),
    bucket_width: '1m', limit: 1440, 'group_by[]': 'model',
  });
  const groups = (await pages(key, '/organizations/rate_limits'))
    .flatMap((p) => p.data ?? []);

  const byModel = series(buckets);
  const minutes = buckets.reduce((n, p) => n + (p.data ?? []).length, 0);
  console.log(`${minutes} minute bucket(s), ${Object.keys(byModel).length} model(s), `
              + `${groups.length} rate limit group(s)`);

  let findings = 0;
  for (const model of Object.keys(byModel).sort()) {
    const limits = groupForModel(groups, model);
    const [state, detail, facts] = verdict(byModel[model], limits, model, rampThreshold);
    console.log(`${state.padEnd(21)} ${model}: ${detail}`);

    if (['acceleration-suspect', 'ramp-near-ceiling', 'steady'].includes(state)) {
      const pct = (s) => (s === null ? 'unknown' : `${Math.round(s * 100)}%`);
      console.log(`  peak input   ${fmt(facts.peakIn[1])}/min against ITPM `
                  + `${fmt(facts.itpm ?? 0)} (${pct(facts.inShare)})`);
      console.log(`  peak output  ${fmt(facts.peakOut[1])}/min against OTPM `
                  + `${fmt(facts.otpm ?? 0)} (${pct(facts.outShare)})`);
      if (facts.ramps.length) {
        const [prevAt, at, factor, prev, current] = facts.ramps[0];
        console.log(`  steepest ramp ${factor.toFixed(1)}x between `
                    + `${prevAt.slice(11, 16) || prevAt} and ${at.slice(11, 16) || at} `
                    + `(${fmt(prev)} -> ${fmt(current)})`);
      }
      console.log('  note: this report carries no request count, so the ramp above '
                  + 'is measured in tokens. Sub-minute bursting is invisible here.');
    }

    for (const line of repairLines(state, facts)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;

    for (const [ltype, configured, floor] of belowPublishedStart(model, limits)) {
      console.log(`${'below-published-start'.padEnd(21)} ${model}: configured `
                  + `${ltype} is ${fmt(configured)}, under the published Start tier `
                  + `figure of ${fmt(floor)}`);
      for (const line of repairLines('below-published-start')) {
        console.log(`  repair: ${line}`);
      }
      findings += 1;
    }
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test builds the shape the note is about &mdash; a flat run of minutes, one enormous step, and a peak at a fifth of the ceiling &mdash; and asserts it comes back as <code>acceleration-suspect</code> with the step reported rather than the level. The second is the guard that keeps this note honest: the identical ramp with a peak at 94% of OTPM must come back as <code>limiter-saturated</code> and hand the reading to the output note by name. Then the input sum, which must include both cache creation fields and exclude cache reads; the ramp floor, which must refuse to call 12 tokens followed by 900 a 75x ramp; the model-to-group resolution, which is exact membership and not a prefix; and the Evaluation tier check against the published Start figures.",
"test_py_file": "test_anthropic_ramp_acceleration.py",
"test_py": '''from anthropic_ramp_acceleration import (below_published_start, cache_creation,
                                         group_for_model, peak, ramp_factors,
                                         repair_lines, series, share,
                                         uncached_input, verdict)

LIMITS = {"requests_per_minute": 4_000,
          "input_tokens_per_minute": 10_000_000,
          "output_tokens_per_minute": 2_000_000}


def bucket(minute, model="claude-opus-5", uncached=0, out=0, read=0,
           create_5m=0, create_1h=0):
    return {"starting_at": "2026-08-31T09:%02d:00Z" % minute,
            "ending_at": "2026-08-31T09:%02d:00Z" % (minute + 1),
            "results": [{"model": model,
                         "uncached_input_tokens": uncached,
                         "output_tokens": out,
                         "cache_read_input_tokens": read,
                         "cache_creation": {
                             "ephemeral_5m_input_tokens": create_5m,
                             "ephemeral_1h_input_tokens": create_1h}}]}


def page(buckets):
    return [{"data": buckets, "has_more": False, "next_page": None}]


def test_a_steep_step_under_a_low_ceiling_is_the_finding():
    # The note. Four quiet minutes, one fifteenfold step, and a peak that never
    # gets past a fifth of the input limiter.
    rows = series(page([bucket(m, uncached=130_000, out=14_000) for m in range(4)]
                       + [bucket(4, uncached=1_940_000, out=140_000)]))
    state, detail, facts = verdict(rows["claude-opus-5"], LIMITS, "claude-opus-5")
    assert state == "acceleration-suspect"
    assert "step between adjacent minutes" in detail
    assert facts["peak_in"] == ("2026-08-31T09:04:00Z", 1_940_000.0)
    assert 0.19 < facts["in_share"] < 0.20
    assert round(facts["ramps"][0][2], 1) == 14.9
    assert any("ramp gradually" in line for line in repair_lines(state, facts))
    assert any("1 per second" in line for line in repair_lines(state, facts))


def test_the_same_ramp_against_a_saturated_limiter_is_the_other_note():
    # The guard. Without this the note fires on every busy workload and takes
    # the credit for a finding that belongs to the output limiter note.
    rows = series(page([bucket(m, out=120_000) for m in range(4)]
                       + [bucket(4, out=1_870_000)]))
    state, detail, _ = verdict(rows["claude-opus-5"], LIMITS, "claude-opus-5")
    assert state == "limiter-saturated"
    assert "output limiter note, not this one" in detail
    assert any("really is the headline number" in line
               for line in repair_lines(state))


def test_input_is_summed_the_way_the_limiter_counts_it():
    result = {"uncached_input_tokens": 1_000, "cache_read_input_tokens": 900_000,
              "cache_creation": {"ephemeral_5m_input_tokens": 400,
                                 "ephemeral_1h_input_tokens": 600}}
    assert cache_creation(result) == 1_000.0
    # 900,000 cache reads are excluded: they do not count toward ITPM.
    assert uncached_input(result) == 2_000.0
    assert uncached_input({}) == 0.0 and uncached_input(None) == 0.0
    rows = series(page([bucket(0, uncached=1_000, read=900_000, create_5m=400,
                               create_1h=600)]))
    assert rows["claude-opus-5"][0][1] == 2_000.0
    assert rows["claude-opus-5"][0][3] == 900_000.0


def test_a_ramp_off_a_trivial_base_is_not_a_ramp():
    rows = [("09:00", 12.0, 0.0, 0.0), ("09:01", 900.0, 0.0, 0.0)]
    assert ramp_factors(rows, 1) == []
    big = [("09:00", 100_000.0, 0.0, 0.0), ("09:01", 400_000.0, 0.0, 0.0),
           ("09:02", 200_000.0, 0.0, 0.0)]
    factors = ramp_factors(big, 1)
    assert len(factors) == 1 and factors[0][2] == 4.0
    assert peak(big, 1) == ("09:01", 400_000.0)
    assert peak([], 1) == ("", 0.0)
    assert share(10, 0) is None and share(10, None) is None


def test_a_model_resolves_to_its_group_by_exact_membership():
    groups = [{"group_type": "model_group",
               "models": ["claude-opus-4-5", "claude-opus-4-8"],
               "limits": [{"type": "input_tokens_per_minute", "value": 10_000_000}]},
              {"group_type": "batch", "models": None,
               "limits": [{"type": "enqueued_batch_requests", "value": 500_000}]}]
    assert group_for_model(groups, "claude-opus-4-8") == {
        "input_tokens_per_minute": 10_000_000.0}
    # A prefix match would hand claude-opus-5 the 4.x group's numbers, which is
    # a different bucket entirely.
    assert group_for_model(groups, "claude-opus-5") == {}
    assert group_for_model(None, "claude-opus-5") == {}


def test_configured_limits_under_the_published_start_tier_are_reported():
    assert below_published_start("claude-fable-5",
                                 {"input_tokens_per_minute": 250_000}) == [
        ("input_tokens_per_minute", 250_000, 500_000)]
    assert below_published_start("claude-opus-5",
                                 {"input_tokens_per_minute": 10_000_000}) == []
    assert below_published_start("claude-opus-5", {}) == []
    assert any("Evaluation tier" in line
               for line in repair_lines("below-published-start"))


def test_an_empty_window_is_not_a_finding():
    state, detail, _ = verdict([], LIMITS, "claude-opus-5")
    assert state == "no-traffic" and "no usage" in detail
    assert verdict(None, None, None)[0] == "no-traffic"
    assert series(None) == {} and repair_lines("steady") == []
    steady = series(page([bucket(m, uncached=100_000) for m in range(3)]))
    assert verdict(steady["claude-opus-5"], LIMITS, "claude-opus-5")[0] == "steady"
''',
"test_js_file": "anthropic-ramp-acceleration.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { belowPublishedStart, cacheCreation, groupForModel, peak, rampFactors,
         repairLines, series, share, uncachedInput, verdict }
  from './anthropic-ramp-acceleration.mjs';

const LIMITS = { requests_per_minute: 4000, input_tokens_per_minute: 10000000,
                 output_tokens_per_minute: 2000000 };

const pad = (n) => String(n).padStart(2, '0');

const bucket = (minute, { model = 'claude-opus-5', uncached = 0, out = 0, read = 0,
                          create5m = 0, create1h = 0 } = {}) => ({
  starting_at: `2026-08-31T09:${pad(minute)}:00Z`,
  ending_at: `2026-08-31T09:${pad(minute + 1)}:00Z`,
  results: [{ model, uncached_input_tokens: uncached, output_tokens: out,
              cache_read_input_tokens: read,
              cache_creation: { ephemeral_5m_input_tokens: create5m,
                                ephemeral_1h_input_tokens: create1h } }],
});

const page = (buckets) => [{ data: buckets, has_more: false, next_page: null }];

test('a steep step under a low ceiling is the finding', () => {
  const quiet = [0, 1, 2, 3].map((m) => bucket(m, { uncached: 130000, out: 14000 }));
  const rows = series(page([...quiet, bucket(4, { uncached: 1940000, out: 140000 })]));
  const [state, detail, facts] = verdict(rows['claude-opus-5'], LIMITS, 'claude-opus-5');
  assert.equal(state, 'acceleration-suspect');
  assert.match(detail, /step between adjacent minutes/);
  assert.deepEqual(facts.peakIn, ['2026-08-31T09:04:00Z', 1940000]);
  assert.ok(facts.inShare > 0.19 && facts.inShare < 0.20);
  assert.equal(Number(facts.ramps[0][2].toFixed(1)), 14.9);
  assert.ok(repairLines(state, facts).some((l) => l.includes('ramp gradually')));
  assert.ok(repairLines(state, facts).some((l) => l.includes('1 per second')));
});

test('the same ramp against a saturated limiter is the other note', () => {
  const quiet = [0, 1, 2, 3].map((m) => bucket(m, { out: 120000 }));
  const rows = series(page([...quiet, bucket(4, { out: 1870000 })]));
  const [state, detail] = verdict(rows['claude-opus-5'], LIMITS, 'claude-opus-5');
  assert.equal(state, 'limiter-saturated');
  assert.match(detail, /output limiter note, not this one/);
  assert.ok(repairLines(state).some((l) => l.includes('really is the headline number')));
});

test('input is summed the way the limiter counts it', () => {
  const result = { uncached_input_tokens: 1000, cache_read_input_tokens: 900000,
                   cache_creation: { ephemeral_5m_input_tokens: 400,
                                     ephemeral_1h_input_tokens: 600 } };
  assert.equal(cacheCreation(result), 1000);
  assert.equal(uncachedInput(result), 2000);
  assert.equal(uncachedInput({}), 0);
  assert.equal(uncachedInput(null), 0);
  const rows = series(page([bucket(0, { uncached: 1000, read: 900000,
                                        create5m: 400, create1h: 600 })]));
  assert.equal(rows['claude-opus-5'][0][1], 2000);
  assert.equal(rows['claude-opus-5'][0][3], 900000);
});

test('a ramp off a trivial base is not a ramp', () => {
  assert.deepEqual(rampFactors([['09:00', 12, 0, 0], ['09:01', 900, 0, 0]], 1), []);
  const big = [['09:00', 100000, 0, 0], ['09:01', 400000, 0, 0],
               ['09:02', 200000, 0, 0]];
  const factors = rampFactors(big, 1);
  assert.equal(factors.length, 1);
  assert.equal(factors[0][2], 4);
  assert.deepEqual(peak(big, 1), ['09:01', 400000]);
  assert.deepEqual(peak([], 1), ['', 0]);
  assert.equal(share(10, 0), null);
  assert.equal(share(10, null), null);
});

test('a model resolves to its group by exact membership', () => {
  const groups = [
    { group_type: 'model_group', models: ['claude-opus-4-5', 'claude-opus-4-8'],
      limits: [{ type: 'input_tokens_per_minute', value: 10000000 }] },
    { group_type: 'batch', models: null,
      limits: [{ type: 'enqueued_batch_requests', value: 500000 }] },
  ];
  assert.deepEqual(groupForModel(groups, 'claude-opus-4-8'),
                   { input_tokens_per_minute: 10000000 });
  assert.deepEqual(groupForModel(groups, 'claude-opus-5'), {});
  assert.deepEqual(groupForModel(null, 'claude-opus-5'), {});
});

test('configured limits under the published Start tier are reported', () => {
  assert.deepEqual(belowPublishedStart('claude-fable-5',
                                       { input_tokens_per_minute: 250000 }),
                   [['input_tokens_per_minute', 250000, 500000]]);
  assert.deepEqual(belowPublishedStart('claude-opus-5',
                                       { input_tokens_per_minute: 10000000 }), []);
  assert.deepEqual(belowPublishedStart('claude-opus-5', {}), []);
  assert.ok(repairLines('below-published-start').some((l) => l.includes('Evaluation tier')));
});

test('an empty window is not a finding', () => {
  const [state, detail] = verdict([], LIMITS, 'claude-opus-5');
  assert.equal(state, 'no-traffic');
  assert.match(detail, /no usage/);
  assert.equal(verdict(null, null, null)[0], 'no-traffic');
  assert.deepEqual(series(null), {});
  assert.deepEqual(repairLines('steady'), []);
  const steady = series(page([0, 1, 2].map((m) => bucket(m, { uncached: 100000 }))));
  assert.equal(verdict(steady['claude-opus-5'], LIMITS, 'claude-opus-5')[0], 'steady');
});
''',
"faq": [
 ("How is this different from the ITPM and OTPM notes?",
  "Those two fire when a minute reaches its ceiling and tell you which limiter emptied. This one fires when no minute gets anywhere near a ceiling and 429s happened anyway. They are opposite readings of the same buckets, which is exactly why the script grades saturation first: if the peak is at or above 85% of a limit, it prints which limiter that is, names the note that owns the reading, and does not report a ramp. A finding that fires alongside its own ordinary explanation is not a finding."),
 ("Why is the ramp measured in tokens rather than requests?",
  "Because the messages usage report has no request count. Its result fields are uncached input tokens, the two cache creation figures, cache reads, output tokens and server tool calls, plus whatever you grouped by. There is no field for the number of requests anywhere in it, so a per-minute request rate cannot be reconstructed on this side at all. The script measures the token ramp, says in its own output that it is a token ramp, and leaves the request-rate question to your client-side counters."),
 ("If a minute bucket cannot see a one-second burst, what is it proving?",
  "That the minute was not the problem. The bucket is not being asked to catch the burst; it is being asked to eliminate the explanation everybody reaches for first. Once the peak minute is demonstrably at a fifth of the ceiling, the remaining candidates are acceleration on a sharp increase and enforcement over an interval shorter than a minute, and both are repaired the same way: pace the ramp and spread the burst. Neither is repaired by a bigger number."),
 ("What is the Evaluation tier and why does the script check for it?",
  "New organizations, and organizations with limited usage history, can start with limits below the standard published tables while account history is established. If that is you, every argument that begins with the tier table is wrong from its first line. The script compares the numbers the API actually reports against the published Start tier figures and flags anything below them, which is the only read-only signal available for it. Those limits rise automatically as usage history accumulates, so it is a reason to pace rather than a reason to file a ticket."),
 ("The report says data lands within about five minutes. Does that matter here?",
  "Yes, at the edges. The most recent minute or two may still be filling, so a run made immediately after an incident can show an artificially low final bucket and a downward step that is an artefact rather than traffic. The script only reports upward steps, which sidesteps most of it, but the honest habit is to wait a few minutes before reading the window and to poll no more than once a minute for sustained use."),
],
"related": [REL_OTPM, REL_ITPM, REL_FLOOR],
"citations": [CITE_RL, CITE_USAGE_REF, CITE_RL_API, CITE_USAGE_API],
},
{
"slug": "retry-after-header-ignored",
"title": "The gateway strips the header your backoff depends on",
"description": "retry-after exists only on a 429. Probe the headers that arrive on every response, through the gateway and around it: if they die in transit, so does it.",
"h1": "The gateway strips the header your backoff depends on",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["retry-after header missing behind proxy llm api",
             "anthropic-ratelimit headers stripped gateway",
             "x-ratelimit headers not returned through proxy openai",
             "retry before retry-after elapses fails again",
             "rate limit reset timestamp clock skew backoff"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY or OPENAI_API_KEY, plus ANTHROPIC_BASE_URL or OPENAI_BASE_URL if your application reaches the provider through a gateway. Issues one GET per path. It will not provoke a 429 to look at one.",
"lead": "The backoff was reviewed, it is textbook, and it reads <code>retry-after</code> before it sleeps. It has also never once seen that header, because the reverse proxy in front of the API forwards a response header allowlist that somebody wrote in 2023 and it contains <code>content-type</code>. So the handler falls through to its default of one second, retries into a bucket that has not refilled, and every retry pushes the reset further out while the incident channel fills up with people saying the backoff must be broken.",
"short_answer": """<p><code>retry-after</code> only exists on a 429, so a script that refuses to cause one can never photograph it. What it can do is probe the header class that arrives on <strong>every</strong> response and prove that class survives the network path your application actually uses.</p>
<p>One <code>GET /v1/models</code> issued twice: once straight at the provider, once through the base URL your client is configured with. Then diff the headers. On Anthropic the always-present set is <code>anthropic-ratelimit-requests-limit</code>, <code>-remaining</code> and <code>-reset</code>, the matching input-token and output-token triples, and the aggregate <code>anthropic-ratelimit-tokens-*</code> triple. On OpenAI it is <code>x-ratelimit-limit-requests</code>, <code>x-ratelimit-remaining-requests</code>, <code>x-ratelimit-reset-requests</code> and the token equivalents. A path that drops those on a 200 will drop <code>retry-after</code> on a 429, and no amount of correct backoff code survives that.</p>
<p>Compare only the <code>-limit-</code> values across the two paths. <code>-remaining</code> and <code>-reset</code> are supposed to differ between two calls made a second apart; a <em>limit</em> that differs means something in the middle is inventing headers rather than forwarding them, which is worse than stripping because it looks like it is working.</p>
<p>Then check the clock. Anthropic's reset values are RFC 3339 timestamps, so a client that sleeps until that instant is trusting its own clock to agree with the server's; the script compares the server's <code>date</code> header against local time and reports the skew. OpenAI's reset values are durations, which are immune to this, and the asymmetry is worth knowing before you write one backoff for both.</p>
<p>What this note is not: it never grades how much headroom is left, and it never names which limiter emptied. <a href="/llm/rate-limit-headers-near-exhaustion/">One published note</a> reads those values for headroom and <a href="/llm/rate-limit-429-limiter-unidentified/">another</a> reads them to name the bucket. This one reads whether they arrive.</p>""",
"problem": """<p>The documentation is unusually blunt about what <code>retry-after</code> is for. It is the number of seconds to wait until you can retry, and earlier retries <em>will</em> fail. The bucket refills continuously, so a retry sent before the stated delay is not a gamble that might pay off; it is a request that is guaranteed to be refused, and it spends a slot doing it.</p>
<p>So everybody writes the handler that reads the header. And then the header does not arrive, for reasons that have nothing to do with the handler. Corporate egress proxies strip unknown response headers. API gateways forward an allowlist. Service meshes normalise. CDN and WAF layers rewrite. Every one of those is a sensible default somewhere else, and every one of them turns a precise wait instruction into a missing key and a fallback constant.</p>
<p>The fallback is where it gets expensive. A missing header means <code>sleep(1)</code>, which means a retry into an empty bucket, which means another 429, which means another slot burned and the reset pushed out again. From the outside this looks exactly like a rate limit that will not clear, and the usual response is to add more retries.</p>
<p>The second failure is quieter and only affects one of the two providers. Anthropic's reset headers are absolute timestamps. A client that computes its sleep from one of those is combining a server timestamp with a local clock, and if the two disagree by thirty seconds the sleep is thirty seconds wrong in whichever direction hurts. Containers with no time sync, virtual machines resuming from suspend, and anything behind a captive NTP source all do this, and it is invisible to code review because the code is correct.</p>
<p>And one case is not a transport failure at all: the 429 you get when the organization has crossed its monthly spend cap carries <strong>no</strong> <code>retry-after</code>, deliberately, because there is nothing to wait for. A client that treats a missing header as a proxy problem will retry that one forever.</p>""",
"why": """<p><strong>The header you care about cannot be observed without causing the failure, so probe its class instead.</strong> This is the whole design. <code>retry-after</code> appears on 429 responses; the rate-limit triples appear on every response including successful ones. They are the same class of header, added by the same layer, and stripped or forwarded by the same middlebox rules. If the triples arrive intact on a 200, the wait instruction will arrive on a 429. Using the healthy call as a canary for the unhealthy one costs one GET and no capacity.</p>
<p><strong>Two paths, because one path cannot tell you whose fault it is.</strong> A single probe that comes back with no rate-limit headers is genuinely ambiguous: it could be the provider, the endpoint, or three hops of your own infrastructure. Issuing the identical call directly and through the configured base URL turns that into an answer. Headers present direct and absent through the gateway is your gateway, in one line, with no argument possible.</p>
<p><strong>Only the limit values are comparable.</strong> The two probes happen at different instants, so <code>-remaining</code> and <code>-reset</code> are expected to differ and comparing them would produce a permanent false positive. <code>-limit-</code> values are configuration and do not move between two calls a second apart. When they do differ across paths, something is synthesising headers rather than forwarding them &mdash; a caching layer replaying a stale response, or a gateway helpfully making up numbers &mdash; and that is a worse state than stripping, because the client believes what it is told.</p>
<p><strong>Absolute resets and duration resets fail differently, and the script parses both.</strong> Anthropic returns RFC 3339 instants; OpenAI returns durations like <code>6m0s</code>. A duration is skew-proof. An instant is only as good as the agreement between two clocks, so the script reads the server's own <code>date</code> header, compares it against local time, and reports the difference. A reset that has already passed according to the server is a separate finding again: any client sleeping until that instant sleeps for nothing.</p>
<p><strong>It will not provoke a 429 to look at one.</strong> Driving traffic into a limiter to photograph its error is not a diagnostic. On a saturated organization it is a second outage; on a healthy one it spends capacity that belongs to production, and the thing it proves was already provable from a single successful call. If a 429 does arrive on its own during the probe, the script records the <code>retry-after</code> it carried, reports it as directly observed, and does not retry.</p>""",
"steps": [
 {"h": "Point the script at the same path your application uses",
  "body": """<p>Set <code>ANTHROPIC_BASE_URL</code> or <code>OPENAI_BASE_URL</code> to the gateway, proxy or mesh address your production client is configured with. Those are the same variables the official SDKs read, so if your application sets one, use the same value. Without a base URL the script still runs, but it can only check presence and clock agreement on one path, not attribute a loss to a hop.</p>"""},
 {"h": "Issue one GET /v1/models per path and keep every header",
  "body": """<p>Both providers answer <code>/v1/models</code> with the same rate-limit header family they attach to inference calls, and it costs no tokens. Lower-case every header name before comparing: HTTP header names are case-insensitive and middleboxes rewrite their casing freely.</p>"""},
 {"h": "Diff the required set, then diff the limit values",
  "body": """<p>Anything required and present on the direct path but absent through the gateway is stripped. Anything present on both is compared on its <code>-limit-</code> value only, because remaining and reset are supposed to move. A value that differs is a rewrite, and a header that appears only through the gateway is an invention.</p>"""},
 {"h": "Check the clock against the server's own date header",
  "body": """<p>Parse the reset values. Durations need no clock. Absolute timestamps do, so compare the server's <code>date</code> header against local time and report the skew, and separately report any reset that is already in the past according to the server, which makes any sleep computed from it a no-op.</p>"""},
 {"h": "Read the output as a checklist for whoever owns the middlebox",
  "body": """<p>The repair is a header allowlist, and the script prints the exact names to add. It changes no configuration, retries nothing, and never sends a second request to see whether the first one was unlucky.</p>"""},
],
"verify": """<p>Add the header names to the gateway allowlist and re-run. Every required header should show <code>intact</code> on both paths, the limit values should agree, and the verdict should be <code>headers-intact</code>. A run that moves from <code>headers-stripped</code> to <code>headers-rewritten</code> means the allowlist now passes the names through but something upstream is still generating the values rather than forwarding them, which is the state that most looks like success and is not.</p>
<pre><code class="language-bash">python3 retry_after_header_probe.py
# anthropic: direct api.anthropic.com, gateway llm-gw.internal
# headers-stripped      6 of 12 rate limit header(s) do not survive the gateway
#   stripped   anthropic-ratelimit-input-tokens-limit
#   stripped   anthropic-ratelimit-input-tokens-remaining
#   stripped   anthropic-ratelimit-input-tokens-reset
#   stripped   anthropic-ratelimit-output-tokens-limit ...
#   intact     anthropic-ratelimit-requests-limit  1000
#   repair: retry-after travels with these. A path that drops them on a 200
#           drops the wait instruction on a 429, and your backoff falls back
#           to a constant. Add the names above to the gateway allowlist.
# clock-skew            local clock is 42s behind the server's date header
#   repair: anthropic reset values are RFC 3339 instants, so a sleep computed
#           from one is only as good as clock agreement. Fix time sync, or
#           prefer retry-after, which is relative and immune to this.
# openai: direct api.openai.com, no gateway configured
# headers-intact        6 of 6 rate limit header(s) present, resets are
#                       durations and need no clock
# 2 finding(s)</code></pre>""",
"code_intro": "One GET per path and every judgement in a pure function. <code>lower_headers</code>, because middleboxes rewrite casing; <code>required</code> and <code>optional</code>, which hold the documented header families per provider; <code>compare</code>, which classifies each name as intact, stripped, added or rewritten and only ever compares a <code>-limit-</code> value; <code>parse_reset</code>, which recognises an RFC 3339 instant and a Go-style duration and says which it got rather than guessing; <code>clock_skew</code>, which reads the server's own <code>date</code> header so the comparison is against the server and not against another server; and <code>verdict</code>, which orders the findings so a stripped header is reported before a skewed clock rather than alongside it.",
"py_file": "retry_after_header_probe.py",
"py": '''"""Prove that retry-after can reach your client before you need it.

Read only, and deliberately small: one GET /v1/models per path. This script
will not drive traffic into a 429 in order to photograph one. Provoking the
failure you are investigating is not a diagnostic; on a saturated organization
it is a second outage, and on a healthy one it spends capacity that belongs to
production.

retry-after appears only on a 429, so its class is probed instead. The rate
limit triples arrive on every response, are added by the same layer, and are
forwarded or dropped by the same middlebox rules. If they survive the path on a
200, the wait instruction survives it on a 429.

Two paths, because one cannot attribute a loss: the same call straight at the
provider and through the base URL the application is configured with. Only the
-limit- values are compared, because remaining and reset are supposed to move
between two calls a second apart.
"""
import argparse
import datetime as dt
import email.utils
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("retry_after_header_probe")

DIRECT = {
    "anthropic": "https://api.anthropic.com/v1",
    "openai": "https://api.openai.com/v1",
}

# The headers documented as arriving on every response. These are the canary:
# retry-after belongs to the same family and is added by the same layer, so a
# path that keeps these keeps it too.
REQUIRED = {
    "anthropic": (
        "anthropic-ratelimit-requests-limit",
        "anthropic-ratelimit-requests-remaining",
        "anthropic-ratelimit-requests-reset",
        "anthropic-ratelimit-input-tokens-limit",
        "anthropic-ratelimit-input-tokens-remaining",
        "anthropic-ratelimit-input-tokens-reset",
        "anthropic-ratelimit-output-tokens-limit",
        "anthropic-ratelimit-output-tokens-remaining",
        "anthropic-ratelimit-output-tokens-reset",
        "anthropic-ratelimit-tokens-limit",
        "anthropic-ratelimit-tokens-remaining",
        "anthropic-ratelimit-tokens-reset",
    ),
    "openai": (
        "x-ratelimit-limit-requests",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-tokens",
    ),
}

# Present in some configurations only, so their absence is reported and never
# counted as a loss: the priority triples require a Priority Tier commitment,
# the project triples appear when a project ceiling applies, and retry-after
# itself is a 429 header that a healthy probe must not expect to see.
OPTIONAL = {
    "anthropic": ("retry-after", "request-id", "anthropic-workspace-id",
                  "anthropic-priority-input-tokens-limit",
                  "anthropic-priority-output-tokens-limit"),
    "openai": ("retry-after", "x-request-id",
               "x-ratelimit-limit-project-tokens",
               "x-ratelimit-remaining-project-tokens",
               "x-ratelimit-reset-project-tokens"),
}

SKEW_SECONDS = 5.0

FINDINGS = ("headers-stripped", "headers-rewritten", "headers-absent",
            "reset-in-the-past", "clock-skew")

DURATION = re.compile(r"(\\d+(?:\\.\\d+)?)(ms|h|m|s)")
UNIT = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


def lower_headers(headers):
    """{lowercase name: value}. Pure.

    HTTP header names are case-insensitive and middleboxes rewrite their casing
    freely, so a comparison that does not normalise reports a stripped header
    every time a proxy prefers title case.
    """
    out = {}
    for key, value in dict(headers or {}).items():
        out[str(key).strip().lower()] = str(value)
    return out


def missing(headers, provider):
    """Required header names absent from this response. Pure. Sorted."""
    present = lower_headers(headers)
    return sorted(n for n in REQUIRED.get(provider, ()) if n not in present)


def compare(direct, gateway, provider):
    """{header: (direct, gateway, state)} across two paths. Pure.

    States: intact, stripped, added, rewritten, absent-both. Only -limit- values
    are compared for equality. remaining and reset are supposed to differ
    between two calls made a second apart, and comparing them would make every
    healthy path look rewritten.
    """
    left = lower_headers(direct)
    right = lower_headers(gateway)
    names = set(REQUIRED.get(provider, ())) | set(OPTIONAL.get(provider, ()))
    names |= {n for n in list(left) + list(right)
              if "ratelimit" in n or n == "retry-after"}
    out = {}
    for name in sorted(names):
        a, b = left.get(name), right.get(name)
        if a is None and b is None:
            state = "absent-both"
        elif a is not None and b is None:
            state = "stripped"
        elif a is None and b is not None:
            state = "added"
        elif "-limit" in name and a != b:
            state = "rewritten"
        else:
            state = "intact"
        out[name] = (a, b, state)
    return out


def parse_reset(value):
    """(kind, seconds) for a reset header. Pure.

    kind is "absolute" with a POSIX timestamp, "duration" with a count of
    seconds, or "unknown" with None. Saying which it got matters: a duration
    needs no clock and an instant needs two clocks to agree.
    """
    text = str(value or "").strip()
    if not text:
        return ("unknown", None)
    try:
        stamp = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=dt.timezone.utc)
        return ("absolute", stamp.timestamp())
    except ValueError:
        pass
    parts = DURATION.findall(text)
    if parts and re.fullmatch(r"(?:\\d+(?:\\.\\d+)?(?:ms|h|m|s))+", text):
        return ("duration", sum(float(n) * UNIT[u] for n, u in parts))
    try:
        return ("duration", float(text))
    except ValueError:
        return ("unknown", None)


def clock_skew(date_header, local_epoch):
    """local clock minus the server's date header, in seconds. Pure.

    None when the header is missing or unparseable. Compared against the
    server's own clock rather than a third source, because the only agreement
    that matters is between this client and the API answering it.
    """
    text = str(date_header or "").strip()
    if not text:
        return None
    try:
        stamp = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if stamp is None:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    return float(local_epoch) - stamp.timestamp()


def stale_resets(headers, provider, server_epoch):
    """[(header, seconds_in_the_past)] for absolute resets already elapsed. Pure."""
    present = lower_headers(headers)
    out = []
    for name in REQUIRED.get(provider, ()):
        if not name.endswith("-reset"):
            continue
        kind, value = parse_reset(present.get(name))
        if kind == "absolute" and value is not None and value < server_epoch:
            out.append((name, server_epoch - value))
    out.sort(key=lambda r: (-r[1], r[0]))
    return out


def verdict(comparison, direct_missing, gateway_used, skew, stale):
    """Classify one provider's probe. Pure. Returns (state, detail).

    Ordered so a transport failure is reported before a clock one: a stripped
    header makes the clock question moot, since there is nothing to compute a
    sleep from in the first place.
    """
    comparison = comparison or {}
    states = [s for _, _, s in comparison.values()]
    stripped = [n for n, (_, _, s) in comparison.items() if s == "stripped"]
    rewritten = [n for n, (_, _, s) in comparison.items() if s == "rewritten"]
    total = len(REQUIRED_ANY(comparison))

    if direct_missing and not gateway_used:
        return ("headers-absent",
                "%d required rate limit header(s) did not arrive at all, and "
                "there is no gateway configured to blame for it"
                % len(direct_missing))
    if stripped:
        return ("headers-stripped",
                "%d of %d rate limit header(s) do not survive the gateway"
                % (len(stripped), max(total, len(stripped))))
    if rewritten:
        return ("headers-rewritten",
                "%d limit value(s) differ between the two paths, so something "
                "is generating headers rather than forwarding them"
                % len(rewritten))
    if direct_missing:
        return ("headers-absent",
                "%d required rate limit header(s) are absent on both paths"
                % len(direct_missing))
    if stale:
        return ("reset-in-the-past",
                "%s is already %.0fs in the past by the server's own clock"
                % (stale[0][0], stale[0][1]))
    if skew is not None and abs(skew) > SKEW_SECONDS:
        return ("clock-skew",
                "local clock is %.0fs %s the server's date header"
                % (abs(skew), "behind" if skew < 0 else "ahead of"))
    intact = states.count("intact")
    return ("headers-intact",
            "%d rate limit header(s) present and consistent across every path "
            "checked" % intact)


def REQUIRED_ANY(comparison):
    """The header names in a comparison that are required somewhere. Pure."""
    names = set()
    for provider, required in REQUIRED.items():
        names |= {n for n in required if n in (comparison or {})}
    return names


def repair_lines(state, provider="", names=()):
    """The repair for one verdict. Pure. Printed, never performed."""
    names = list(names or [])
    if state == "headers-stripped":
        return ["retry-after travels with these. A path that drops them on a 200 "
                "drops the wait instruction on a 429, and your backoff falls "
                "back to a constant that retries into an empty bucket.",
                "add these names to the response header allowlist on the "
                "gateway: " + (", ".join(names[:6]) or "(none recorded)")
                + (" ..." if len(names) > 6 else "")]
    if state == "headers-rewritten":
        return ["a limit value that differs between two paths a second apart is "
                "not a live number. Find the layer caching or synthesising "
                "responses and make it forward the origin's headers unchanged.",
                "this state is more dangerous than stripping, because the client "
                "believes the numbers it is given and has no way to tell."]
    if state == "headers-absent":
        return ["nothing arrived on any path checked, so this is not attributable "
                "yet. Re-run with the gateway base URL set, and confirm the "
                "credential and endpoint are the ones production uses."]
    if state == "reset-in-the-past":
        return ["a reset instant already in the past makes any sleep computed "
                "from it a no-op, so the client retries immediately and 429s "
                "again. Prefer retry-after, which is relative."]
    if state == "clock-skew":
        if provider == "anthropic":
            return ["anthropic reset values are RFC 3339 instants, so a sleep "
                    "computed from one is only as good as clock agreement. Fix "
                    "time sync on this host, or use retry-after instead, which "
                    "is relative and immune to skew.",
                    "the same skew affects any log correlation you do against "
                    "these timestamps, which is usually how it is finally noticed."]
        return ["this provider returns reset values as durations, so backoff is "
                "unaffected, but the skew will still misalign every log line you "
                "correlate against the API's timestamps."]
    return []


def probe(url, headers, timeout=30):
    """One GET. Returns (status, headers, note). Never retried, never repeated."""
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        return (None, {}, "request failed: %s" % exc)
    note = ""
    if r.status_code == 429:
        # Not provoked, and not retried. If one happens to arrive it is the
        # direct observation this script cannot go looking for.
        note = ("a 429 arrived on its own. retry-after came back as %r"
                % r.headers.get("retry-after"))
    elif r.status_code in (401, 403):
        note = "%d: the credential cannot read this path" % r.status_code
    return (r.status_code, dict(r.headers), note)


def audit(provider, key, base_url):
    direct_base = DIRECT[provider]
    auth = ({"x-api-key": key, "anthropic-version": "2023-06-01"}
            if provider == "anthropic" else {"Authorization": "Bearer " + key})
    auth["User-Agent"] = "retry-after-header-probe/1.0"

    log.info("%s: direct %s, %s", provider,
             direct_base.split("//")[-1].split("/")[0],
             "gateway " + base_url.split("//")[-1].split("/")[0]
             if base_url else "no gateway configured")

    status, direct_headers, note = probe(direct_base + "/models", auth)
    if note:
        log.info("  direct: %s", note)
    gateway_headers = {}
    if base_url:
        time.sleep(1)
        _, gateway_headers, gnote = probe(base_url.rstrip("/") + "/models", auth)
        if gnote:
            log.info("  gateway: %s", gnote)

    comparison = compare(direct_headers, gateway_headers or direct_headers, provider)
    direct_missing = missing(direct_headers, provider)
    skew = clock_skew(lower_headers(direct_headers).get("date"), time.time())
    server_epoch = time.time() - (skew or 0.0)
    stale = stale_resets(direct_headers, provider, server_epoch)

    state, detail = verdict(comparison, direct_missing, bool(base_url), skew, stale)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-21s %s", state, detail)

    stripped = [n for n, (_, _, s) in comparison.items() if s == "stripped"]
    for name in stripped[:6]:
        emit("  stripped   %s", name)
    for name, (a, _b, s) in sorted(comparison.items()):
        if s == "intact" and name.endswith("-limit") and a:
            emit("  intact     %-42s %s", name, a)
    for name, seconds in stale[:3]:
        emit("  stale      %s, %.0fs in the past", name, seconds)
    for line in repair_lines(state, provider, stripped):
        emit("  repair: %s", line)
    return 1 if state in FINDINGS else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--anthropic-base-url", default=os.environ.get("ANTHROPIC_BASE_URL"))
    ap.add_argument("--openai-base-url", default=os.environ.get("OPENAI_BASE_URL"))
    args = ap.parse_args()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not anthropic_key and not openai_key:
        log.error("set ANTHROPIC_API_KEY, OPENAI_API_KEY, or both, and set the "
                  "matching base URL if production reaches the API through a "
                  "gateway")
        return 2

    findings = 0
    if anthropic_key:
        findings += audit("anthropic", anthropic_key, args.anthropic_base_url)
    if openai_key:
        findings += audit("openai", openai_key, args.openai_base_url)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "retry-after-header-probe.mjs",
"js": '''/**
 * Prove that retry-after can reach your client before you need it.
 *
 * Read only, and deliberately small: one GET /v1/models per path. This script
 * will not drive traffic into a 429 in order to photograph one.
 *
 * retry-after appears only on a 429, so its class is probed instead: the rate
 * limit triples arrive on every response and are forwarded or dropped by the
 * same middlebox rules. Two paths, because one cannot attribute a loss. Only
 * the -limit- values are compared, because remaining and reset are supposed to
 * move between two calls a second apart.
 */
const DIRECT = {
  anthropic: 'https://api.anthropic.com/v1',
  openai: 'https://api.openai.com/v1',
};

export const REQUIRED = {
  anthropic: [
    'anthropic-ratelimit-requests-limit',
    'anthropic-ratelimit-requests-remaining',
    'anthropic-ratelimit-requests-reset',
    'anthropic-ratelimit-input-tokens-limit',
    'anthropic-ratelimit-input-tokens-remaining',
    'anthropic-ratelimit-input-tokens-reset',
    'anthropic-ratelimit-output-tokens-limit',
    'anthropic-ratelimit-output-tokens-remaining',
    'anthropic-ratelimit-output-tokens-reset',
    'anthropic-ratelimit-tokens-limit',
    'anthropic-ratelimit-tokens-remaining',
    'anthropic-ratelimit-tokens-reset',
  ],
  openai: [
    'x-ratelimit-limit-requests',
    'x-ratelimit-remaining-requests',
    'x-ratelimit-reset-requests',
    'x-ratelimit-limit-tokens',
    'x-ratelimit-remaining-tokens',
    'x-ratelimit-reset-tokens',
  ],
};

export const OPTIONAL = {
  anthropic: ['retry-after', 'request-id', 'anthropic-workspace-id',
              'anthropic-priority-input-tokens-limit',
              'anthropic-priority-output-tokens-limit'],
  openai: ['retry-after', 'x-request-id', 'x-ratelimit-limit-project-tokens',
           'x-ratelimit-remaining-project-tokens', 'x-ratelimit-reset-project-tokens'],
};

const SKEW_SECONDS = 5;
const FINDINGS = new Set(['headers-stripped', 'headers-rewritten', 'headers-absent',
                          'reset-in-the-past', 'clock-skew']);

const UNIT = { ms: 0.001, s: 1, m: 60, h: 3600 };

/** {lowercase name: value}. Pure. Middleboxes rewrite casing freely. */
export function lowerHeaders(headers) {
  const out = {};
  for (const [key, value] of Object.entries(headers ?? {})) {
    out[String(key).trim().toLowerCase()] = String(value);
  }
  return out;
}

/** Required header names absent from this response. Pure. Sorted. */
export function missing(headers, provider) {
  const present = lowerHeaders(headers);
  return (REQUIRED[provider] ?? []).filter((n) => !(n in present)).sort();
}

/** {header: [direct, gateway, state]} across two paths. Pure. */
export function compare(direct, gateway, provider) {
  const left = lowerHeaders(direct);
  const right = lowerHeaders(gateway);
  const names = new Set([...(REQUIRED[provider] ?? []), ...(OPTIONAL[provider] ?? [])]);
  for (const n of [...Object.keys(left), ...Object.keys(right)]) {
    if (n.includes('ratelimit') || n === 'retry-after') names.add(n);
  }
  const out = {};
  for (const name of [...names].sort()) {
    const a = left[name];
    const b = right[name];
    let state;
    if (a === undefined && b === undefined) state = 'absent-both';
    else if (a !== undefined && b === undefined) state = 'stripped';
    else if (a === undefined && b !== undefined) state = 'added';
    else if (name.includes('-limit') && a !== b) state = 'rewritten';
    else state = 'intact';
    out[name] = [a, b, state];
  }
  return out;
}

/** [kind, seconds] for a reset header. Pure. absolute | duration | unknown. */
export function parseReset(value) {
  const text = String(value ?? '').trim();
  if (!text) return ['unknown', null];
  if (/^\\d{4}-\\d{2}-\\d{2}[T ]/.test(text)) {
    const ms = Date.parse(text);
    if (Number.isFinite(ms)) return ['absolute', ms / 1000];
  }
  if (/^(?:\\d+(?:\\.\\d+)?(?:ms|h|m|s))+$/.test(text)) {
    let total = 0;
    for (const [, n, u] of text.matchAll(/(\\d+(?:\\.\\d+)?)(ms|h|m|s)/g)) {
      total += Number(n) * UNIT[u];
    }
    return ['duration', total];
  }
  const plain = Number(text);
  return Number.isFinite(plain) ? ['duration', plain] : ['unknown', null];
}

/** local clock minus the server's date header, in seconds. Pure. null if unknown. */
export function clockSkew(dateHeader, localEpoch) {
  const text = String(dateHeader ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  if (!Number.isFinite(ms)) return null;
  return Number(localEpoch) - ms / 1000;
}

/** [[header, secondsInThePast]] for absolute resets already elapsed. Pure. */
export function staleResets(headers, provider, serverEpoch) {
  const present = lowerHeaders(headers);
  const out = [];
  for (const name of REQUIRED[provider] ?? []) {
    if (!name.endsWith('-reset')) continue;
    const [kind, value] = parseReset(present[name]);
    if (kind === 'absolute' && value !== null && value < serverEpoch) {
      out.push([name, serverEpoch - value]);
    }
  }
  out.sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]));
  return out;
}

const requiredAny = (comparison) => {
  const names = new Set();
  for (const required of Object.values(REQUIRED)) {
    for (const n of required) if (n in (comparison ?? {})) names.add(n);
  }
  return names;
};

/** Classify one provider's probe. Pure. Returns [state, detail]. */
export function verdict(comparison, directMissing, gatewayUsed, skew, stale) {
  const rows = Object.entries(comparison ?? {});
  const stripped = rows.filter(([, v]) => v[2] === 'stripped').map(([n]) => n);
  const rewritten = rows.filter(([, v]) => v[2] === 'rewritten').map(([n]) => n);
  const total = requiredAny(comparison).size;
  const absent = (directMissing ?? []).length;

  if (absent && !gatewayUsed) {
    return ['headers-absent',
            `${absent} required rate limit header(s) did not arrive at all, and `
            + 'there is no gateway configured to blame for it'];
  }
  if (stripped.length) {
    return ['headers-stripped',
            `${stripped.length} of ${Math.max(total, stripped.length)} rate limit `
            + 'header(s) do not survive the gateway'];
  }
  if (rewritten.length) {
    return ['headers-rewritten',
            `${rewritten.length} limit value(s) differ between the two paths, so `
            + 'something is generating headers rather than forwarding them'];
  }
  if (absent) {
    return ['headers-absent',
            `${absent} required rate limit header(s) are absent on both paths`];
  }
  if ((stale ?? []).length) {
    return ['reset-in-the-past',
            `${stale[0][0]} is already ${Math.round(stale[0][1])}s in the past by `
            + "the server's own clock"];
  }
  if (skew !== null && skew !== undefined && Math.abs(skew) > SKEW_SECONDS) {
    return ['clock-skew',
            `local clock is ${Math.round(Math.abs(skew))}s `
            + `${skew < 0 ? 'behind' : 'ahead of'} the server's date header`];
  }
  const intact = rows.filter(([, v]) => v[2] === 'intact').length;
  return ['headers-intact',
          `${intact} rate limit header(s) present and consistent across every path checked`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, provider = '', names = []) {
  const list = names ?? [];
  if (state === 'headers-stripped') {
    return ['retry-after travels with these. A path that drops them on a 200 drops '
      + 'the wait instruction on a 429, and your backoff falls back to a constant '
      + 'that retries into an empty bucket.',
      `add these names to the response header allowlist on the gateway: ${
        list.slice(0, 6).join(', ') || '(none recorded)'}${list.length > 6 ? ' ...' : ''}`];
  }
  if (state === 'headers-rewritten') {
    return ['a limit value that differs between two paths a second apart is not a '
      + 'live number. Find the layer caching or synthesising responses and make it '
      + "forward the origin's headers unchanged.",
      'this state is more dangerous than stripping, because the client believes the '
      + 'numbers it is given and has no way to tell.'];
  }
  if (state === 'headers-absent') {
    return ['nothing arrived on any path checked, so this is not attributable yet. '
      + 'Re-run with the gateway base URL set, and confirm the credential and '
      + 'endpoint are the ones production uses.'];
  }
  if (state === 'reset-in-the-past') {
    return ['a reset instant already in the past makes any sleep computed from it a '
      + 'no-op, so the client retries immediately and 429s again. Prefer '
      + 'retry-after, which is relative.'];
  }
  if (state === 'clock-skew') {
    if (provider === 'anthropic') {
      return ['anthropic reset values are RFC 3339 instants, so a sleep computed '
        + 'from one is only as good as clock agreement. Fix time sync on this host, '
        + 'or use retry-after instead, which is relative and immune to skew.',
        'the same skew affects any log correlation you do against these timestamps, '
        + 'which is usually how it is finally noticed.'];
    }
    return ['this provider returns reset values as durations, so backoff is '
      + 'unaffected, but the skew will still misalign every log line you correlate '
      + "against the API's timestamps."];
  }
  return [];
}

async function probeOnce(url, headers) {
  try {
    const r = await fetch(url, { headers });
    let note = '';
    if (r.status === 429) {
      note = 'a 429 arrived on its own. retry-after came back as '
             + `${JSON.stringify(r.headers.get('retry-after'))}`;
    } else if (r.status === 401 || r.status === 403) {
      note = `${r.status}: the credential cannot read this path`;
    }
    return [r.status, Object.fromEntries(r.headers.entries()), note];
  } catch (err) {
    return [null, {}, `request failed: ${err.message}`];
  }
}

const host = (url) => String(url).split('//').pop().split('/')[0];

async function audit(provider, key, baseUrl) {
  const directBase = DIRECT[provider];
  const auth = provider === 'anthropic'
    ? { 'x-api-key': key, 'anthropic-version': '2023-06-01' }
    : { Authorization: `Bearer ${key}` };
  auth['User-Agent'] = 'retry-after-header-probe/1.0';

  console.log(`${provider}: direct ${host(directBase)}, `
              + `${baseUrl ? `gateway ${host(baseUrl)}` : 'no gateway configured'}`);

  const [, directHeaders, note] = await probeOnce(`${directBase}/models`, auth);
  if (note) console.log(`  direct: ${note}`);
  let gatewayHeaders = {};
  if (baseUrl) {
    await new Promise((r) => { setTimeout(r, 1000); });
    const [, gh, gnote] = await probeOnce(`${baseUrl.replace(/\\/$/, '')}/models`, auth);
    gatewayHeaders = gh;
    if (gnote) console.log(`  gateway: ${gnote}`);
  }

  const comparison = compare(directHeaders,
                             baseUrl ? gatewayHeaders : directHeaders, provider);
  const directMissing = missing(directHeaders, provider);
  const now = Date.now() / 1000;
  const skew = clockSkew(lowerHeaders(directHeaders).date, now);
  const serverEpoch = now - (skew ?? 0);
  const stale = staleResets(directHeaders, provider, serverEpoch);

  const [state, detail] = verdict(comparison, directMissing, Boolean(baseUrl),
                                  skew, stale);
  console.log(`${state.padEnd(21)} ${detail}`);

  const stripped = Object.entries(comparison)
    .filter(([, v]) => v[2] === 'stripped').map(([n]) => n);
  for (const name of stripped.slice(0, 6)) console.log(`  stripped   ${name}`);
  for (const [name, v] of Object.entries(comparison).sort()) {
    if (v[2] === 'intact' && name.endsWith('-limit') && v[0]) {
      console.log(`  intact     ${name.padEnd(42)} ${v[0]}`);
    }
  }
  for (const [name, seconds] of stale.slice(0, 3)) {
    console.log(`  stale      ${name}, ${Math.round(seconds)}s in the past`);
  }
  for (const line of repairLines(state, provider, stripped)) {
    console.log(`  repair: ${line}`);
  }
  return FINDINGS.has(state) ? 1 : 0;
}

async function main() {
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  const openaiKey = process.env.OPENAI_API_KEY;
  if (!anthropicKey && !openaiKey) {
    console.error('set ANTHROPIC_API_KEY, OPENAI_API_KEY, or both, and set the '
                  + 'matching base URL if production reaches the API through a gateway');
    process.exitCode = 2;
    return;
  }
  let findings = 0;
  if (anthropicKey) {
    findings += await audit('anthropic', anthropicKey, process.env.ANTHROPIC_BASE_URL);
  }
  if (openaiKey) {
    findings += await audit('openai', openaiKey, process.env.OPENAI_BASE_URL);
  }
  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note: the same headers on both paths except that the gateway response has lost the input-token triple, which must come back as <code>headers-stripped</code> with the names printed for an allowlist. The second is the false positive this design has to avoid &mdash; two probes a second apart legitimately disagree on <code>-remaining</code> and <code>-reset</code>, and that must grade as <code>intact</code>, while a <code>-limit</code> that differs must grade as <code>rewritten</code>. Then the two reset formats, one an RFC 3339 instant and one a Go-style duration, told apart rather than guessed at; the clock read against the server's own <code>date</code> header; a reset already elapsed; and the ordering rule, which reports a stripped header before a skewed clock because there is nothing left to compute a sleep from.",
"test_py_file": "test_retry_after_header_probe.py",
"test_py": '''from retry_after_header_probe import (clock_skew, compare, lower_headers,
                                      missing, parse_reset, repair_lines,
                                      stale_resets, verdict)

ANTHROPIC_OK = {
    "Anthropic-Ratelimit-Requests-Limit": "1000",
    "anthropic-ratelimit-requests-remaining": "998",
    "anthropic-ratelimit-requests-reset": "2026-08-31T09:12:00Z",
    "anthropic-ratelimit-input-tokens-limit": "10000000",
    "anthropic-ratelimit-input-tokens-remaining": "9998000",
    "anthropic-ratelimit-input-tokens-reset": "2026-08-31T09:12:00Z",
    "anthropic-ratelimit-output-tokens-limit": "2000000",
    "anthropic-ratelimit-output-tokens-remaining": "1999000",
    "anthropic-ratelimit-output-tokens-reset": "2026-08-31T09:12:00Z",
    "anthropic-ratelimit-tokens-limit": "12000000",
    "anthropic-ratelimit-tokens-remaining": "11997000",
    "anthropic-ratelimit-tokens-reset": "2026-08-31T09:12:00Z",
    "date": "Mon, 31 Aug 2026 09:11:00 GMT",
}


def without(headers, prefix):
    return {k: v for k, v in headers.items()
            if not k.lower().startswith(prefix)}


def test_a_gateway_that_drops_the_triples_is_the_finding():
    # The note. Header casing differs between the two paths on purpose: a
    # comparison that does not normalise reports every proxy as stripping.
    gateway = without(ANTHROPIC_OK, "anthropic-ratelimit-input")
    rows = compare(ANTHROPIC_OK, gateway, "anthropic")
    stripped = [n for n, (_, _, s) in rows.items() if s == "stripped"]
    assert stripped == ["anthropic-ratelimit-input-tokens-limit",
                        "anthropic-ratelimit-input-tokens-remaining",
                        "anthropic-ratelimit-input-tokens-reset"]
    state, detail = verdict(rows, [], True, 0.0, [])
    assert state == "headers-stripped"
    assert "do not survive the gateway" in detail
    lines = repair_lines(state, "anthropic", stripped)
    assert any("retry-after travels with these" in line for line in lines)
    assert any("allowlist" in line for line in lines)


def test_remaining_may_differ_across_paths_but_a_limit_may_not():
    # Two calls a second apart. remaining and reset are supposed to move, so
    # comparing them would make every healthy path look rewritten.
    later = dict(ANTHROPIC_OK)
    later["anthropic-ratelimit-requests-remaining"] = "997"
    later["anthropic-ratelimit-requests-reset"] = "2026-08-31T09:12:01Z"
    rows = compare(ANTHROPIC_OK, later, "anthropic")
    assert rows["anthropic-ratelimit-requests-remaining"][2] == "intact"
    assert rows["anthropic-ratelimit-requests-reset"][2] == "intact"
    assert verdict(rows, [], True, 0.0, [])[0] == "headers-intact"

    faked = dict(ANTHROPIC_OK)
    faked["anthropic-ratelimit-requests-limit"] = "50"
    rows = compare(ANTHROPIC_OK, faked, "anthropic")
    assert rows["anthropic-ratelimit-requests-limit"][2] == "rewritten"
    state, detail = verdict(rows, [], True, 0.0, [])
    assert state == "headers-rewritten"
    assert "generating headers rather than forwarding" in detail
    assert any("more dangerous than stripping" in line
               for line in repair_lines(state))


def test_the_two_reset_formats_are_told_apart_rather_than_guessed():
    kind, value = parse_reset("2026-08-31T09:12:00Z")
    assert kind == "absolute" and value == 1788167520.0
    assert parse_reset("6m0s") == ("duration", 360.0)
    assert parse_reset("30s") == ("duration", 30.0)
    assert parse_reset("1h2m3s") == ("duration", 3723.0)
    assert parse_reset("500ms") == ("duration", 0.5)
    assert parse_reset("12") == ("duration", 12.0)
    assert parse_reset("") == ("unknown", None)
    assert parse_reset("soon") == ("unknown", None)


def test_the_clock_is_read_against_the_server_and_a_stale_reset_is_its_own_state():
    # 09:11:00 on the server, 09:11:42 locally: 42 seconds ahead.
    skew = clock_skew("Mon, 31 Aug 2026 09:11:00 GMT", 1788167502.0)
    assert round(skew) == 42
    assert clock_skew("", 0) is None and clock_skew("not a date", 0) is None
    state, detail = verdict(compare(ANTHROPIC_OK, ANTHROPIC_OK, "anthropic"),
                            [], True, skew, [])
    assert state == "clock-skew"
    assert "ahead of" in detail
    assert any("RFC 3339 instants" in line
               for line in repair_lines(state, "anthropic"))
    # Reset instants already elapsed on the server's own clock.
    stale = stale_resets(ANTHROPIC_OK, "anthropic", 1788167600.0)
    assert len(stale) == 4 and stale[0][1] == 80.0
    assert verdict(compare(ANTHROPIC_OK, ANTHROPIC_OK, "anthropic"),
                   [], True, 0.0, stale)[0] == "reset-in-the-past"


def test_a_transport_failure_is_reported_before_a_clock_one():
    gateway = without(ANTHROPIC_OK, "anthropic-ratelimit-input")
    rows = compare(ANTHROPIC_OK, gateway, "anthropic")
    stale = stale_resets(ANTHROPIC_OK, "anthropic", 1788167600.0)
    # Stripped headers, a stale reset and a large skew all at once. There is
    # nothing to compute a sleep from, so the transport answer comes first.
    assert verdict(rows, [], True, 300.0, stale)[0] == "headers-stripped"


def test_openai_headers_and_the_no_gateway_case():
    openai = {"x-ratelimit-limit-requests": "10000",
              "x-ratelimit-remaining-requests": "9999",
              "x-ratelimit-reset-requests": "6m0s",
              "x-ratelimit-limit-tokens": "2000000",
              "x-ratelimit-remaining-tokens": "1999000",
              "x-ratelimit-reset-tokens": "6m0s"}
    assert missing(openai, "openai") == []
    assert stale_resets(openai, "openai", 1788167600.0) == []
    assert verdict(compare(openai, openai, "openai"), [], False, 0.0, [])[0] \\
        == "headers-intact"
    bare = missing({}, "openai")
    assert len(bare) == 6
    state, detail = verdict(compare({}, {}, "openai"), bare, False, None, [])
    assert state == "headers-absent"
    assert "no gateway configured to blame" in detail
    assert any("not attributable yet" in line for line in repair_lines(state))
    assert lower_headers(None) == {} and repair_lines("headers-intact") == []
''',
"test_js_file": "retry-after-header-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { clockSkew, compare, lowerHeaders, missing, parseReset, repairLines,
         staleResets, verdict } from './retry-after-header-probe.mjs';

const ANTHROPIC_OK = {
  'Anthropic-Ratelimit-Requests-Limit': '1000',
  'anthropic-ratelimit-requests-remaining': '998',
  'anthropic-ratelimit-requests-reset': '2026-08-31T09:12:00Z',
  'anthropic-ratelimit-input-tokens-limit': '10000000',
  'anthropic-ratelimit-input-tokens-remaining': '9998000',
  'anthropic-ratelimit-input-tokens-reset': '2026-08-31T09:12:00Z',
  'anthropic-ratelimit-output-tokens-limit': '2000000',
  'anthropic-ratelimit-output-tokens-remaining': '1999000',
  'anthropic-ratelimit-output-tokens-reset': '2026-08-31T09:12:00Z',
  'anthropic-ratelimit-tokens-limit': '12000000',
  'anthropic-ratelimit-tokens-remaining': '11997000',
  'anthropic-ratelimit-tokens-reset': '2026-08-31T09:12:00Z',
  date: 'Mon, 31 Aug 2026 09:11:00 GMT',
};

const without = (headers, prefix) => Object.fromEntries(
  Object.entries(headers).filter(([k]) => !k.toLowerCase().startsWith(prefix)));

test('a gateway that drops the triples is the finding', () => {
  const gateway = without(ANTHROPIC_OK, 'anthropic-ratelimit-input');
  const rows = compare(ANTHROPIC_OK, gateway, 'anthropic');
  const stripped = Object.entries(rows).filter(([, v]) => v[2] === 'stripped')
    .map(([n]) => n);
  assert.deepEqual(stripped, ['anthropic-ratelimit-input-tokens-limit',
                              'anthropic-ratelimit-input-tokens-remaining',
                              'anthropic-ratelimit-input-tokens-reset']);
  const [state, detail] = verdict(rows, [], true, 0, []);
  assert.equal(state, 'headers-stripped');
  assert.match(detail, /do not survive the gateway/);
  const lines = repairLines(state, 'anthropic', stripped);
  assert.ok(lines.some((l) => l.includes('retry-after travels with these')));
  assert.ok(lines.some((l) => l.includes('allowlist')));
});

test('remaining may differ across paths but a limit may not', () => {
  const later = { ...ANTHROPIC_OK,
    'anthropic-ratelimit-requests-remaining': '997',
    'anthropic-ratelimit-requests-reset': '2026-08-31T09:12:01Z' };
  let rows = compare(ANTHROPIC_OK, later, 'anthropic');
  assert.equal(rows['anthropic-ratelimit-requests-remaining'][2], 'intact');
  assert.equal(rows['anthropic-ratelimit-requests-reset'][2], 'intact');
  assert.equal(verdict(rows, [], true, 0, [])[0], 'headers-intact');

  const faked = { ...ANTHROPIC_OK, 'anthropic-ratelimit-requests-limit': '50' };
  rows = compare(ANTHROPIC_OK, faked, 'anthropic');
  assert.equal(rows['anthropic-ratelimit-requests-limit'][2], 'rewritten');
  const [state, detail] = verdict(rows, [], true, 0, []);
  assert.equal(state, 'headers-rewritten');
  assert.match(detail, /generating headers rather than forwarding/);
  assert.ok(repairLines(state).some((l) => l.includes('more dangerous than stripping')));
});

test('the two reset formats are told apart rather than guessed', () => {
  assert.deepEqual(parseReset('2026-08-31T09:12:00Z'), ['absolute', 1788167520]);
  assert.deepEqual(parseReset('6m0s'), ['duration', 360]);
  assert.deepEqual(parseReset('30s'), ['duration', 30]);
  assert.deepEqual(parseReset('1h2m3s'), ['duration', 3723]);
  assert.deepEqual(parseReset('500ms'), ['duration', 0.5]);
  assert.deepEqual(parseReset('12'), ['duration', 12]);
  assert.deepEqual(parseReset(''), ['unknown', null]);
  assert.deepEqual(parseReset('soon'), ['unknown', null]);
});

test('the clock is read against the server and a stale reset is its own state', () => {
  const skew = clockSkew('Mon, 31 Aug 2026 09:11:00 GMT', 1788167502);
  assert.equal(Math.round(skew), 42);
  assert.equal(clockSkew('', 0), null);
  assert.equal(clockSkew('not a date', 0), null);
  const [state, detail] = verdict(compare(ANTHROPIC_OK, ANTHROPIC_OK, 'anthropic'),
                                  [], true, skew, []);
  assert.equal(state, 'clock-skew');
  assert.match(detail, /ahead of/);
  assert.ok(repairLines(state, 'anthropic').some((l) => l.includes('RFC 3339 instants')));
  const stale = staleResets(ANTHROPIC_OK, 'anthropic', 1788167600);
  assert.equal(stale.length, 4);
  assert.equal(stale[0][1], 80);
  assert.equal(verdict(compare(ANTHROPIC_OK, ANTHROPIC_OK, 'anthropic'),
                       [], true, 0, stale)[0], 'reset-in-the-past');
});

test('a transport failure is reported before a clock one', () => {
  const gateway = without(ANTHROPIC_OK, 'anthropic-ratelimit-input');
  const rows = compare(ANTHROPIC_OK, gateway, 'anthropic');
  const stale = staleResets(ANTHROPIC_OK, 'anthropic', 1788167600);
  assert.equal(verdict(rows, [], true, 300, stale)[0], 'headers-stripped');
});

test('openai headers and the no gateway case', () => {
  const openai = {
    'x-ratelimit-limit-requests': '10000',
    'x-ratelimit-remaining-requests': '9999',
    'x-ratelimit-reset-requests': '6m0s',
    'x-ratelimit-limit-tokens': '2000000',
    'x-ratelimit-remaining-tokens': '1999000',
    'x-ratelimit-reset-tokens': '6m0s',
  };
  assert.deepEqual(missing(openai, 'openai'), []);
  assert.deepEqual(staleResets(openai, 'openai', 1788167600), []);
  assert.equal(verdict(compare(openai, openai, 'openai'), [], false, 0, [])[0],
               'headers-intact');
  const bare = missing({}, 'openai');
  assert.equal(bare.length, 6);
  const [state, detail] = verdict(compare({}, {}, 'openai'), bare, false, null, []);
  assert.equal(state, 'headers-absent');
  assert.match(detail, /no gateway configured to blame/);
  assert.ok(repairLines(state).some((l) => l.includes('not attributable yet')));
  assert.deepEqual(lowerHeaders(null), {});
  assert.deepEqual(repairLines('headers-intact'), []);
});
''',
"faq": [
 ("Why not just trigger a 429 and read the header directly?",
  "Because provoking the failure you are investigating is not a diagnostic. On an organization that is already saturated it is a second outage, and on a healthy one it burns capacity that belongs to production in order to learn something a single successful call already proves. The rate-limit triples and retry-after are the same class of header, added by the same layer and forwarded or dropped by the same middlebox rules, so the healthy call is a sound canary. If a 429 does arrive on its own while the script is probing, it records the retry-after that came with it and does not retry."),
 ("How is this different from the note about which limiter hit?",
  "That note reads the header values to tell you which of the three buckets emptied, and the headroom note reads them to tell you how much room is left. Both assume the headers arrived. This one asks the prior question and never grades a value: does the header class survive the path your application actually uses, do the two paths agree about the limits, and is the reset timestamp usable on this host's clock. Different question, different output, and the three are usually read in that order once something has gone wrong."),
 ("What if there is no gateway between my code and the API?",
  "Then set no base URL and the script checks one path: whether the required headers arrive at all, whether any absolute reset has already elapsed, and whether this host's clock agrees with the server's. That is still worth running, but it cannot attribute a loss. A single probe that comes back with nothing is genuinely ambiguous between the provider, the endpoint and your own infrastructure, and only the second path turns that into an answer."),
 ("A 429 arrived with no retry-after at all. Is that a stripped header?",
  "Not necessarily, and this is the case worth knowing about. The 429 you get after an organization crosses its monthly spend cap deliberately carries no retry-after, because there is nothing to wait for: access resumes at the start of the next month or when the limit is raised. It is documented to be distinguishable by its error code rather than its headers. A client that treats every missing retry-after as a proxy problem will retry that one forever, which is the billing wall note rather than this one."),
 ("Which header names should the allowlist contain?",
  "The script prints them for the provider it probed. On Anthropic that is the requests, input-token and output-token triples plus the aggregate tokens triple, and retry-after itself; on OpenAI, the request and token limit, remaining and reset headers, plus retry-after and the project-scoped triple if a project ceiling applies. Add retry-after explicitly even though a healthy probe never sees it, because it is the one that matters on the day the rest of this stops being theoretical."),
],
"related": [REL_WHICH, REL_QUOTA, REL_RAMP],
"citations": [CITE_RL, CITE_OA_RL, CITE_ERRORS, CITE_RL_API],
},
{
"slug": "flex-resource-unavailable-timeouts",
"title": "The flex tier fails by not being served, and bills nothing",
"description": "A 429 Resource Unavailable is not charged, so it never reaches the usage report. Group completions usage by service_tier and read the hours that are missing.",
"h1": "The flex tier fails by not being served, and bills nothing",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai flex processing 429 resource unavailable",
             "service_tier flex not billed no capacity",
             "group_by service_tier usage completions openai",
             "flex processing timeout 10 minutes increase",
             "flex requested but served as default tier"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an admin key that can read the organization usage endpoints. Pass the model ids your code configures for flex with --flex-model so the script can tell a tier that was never served from a tier you never asked for.",
"lead": "The nightly enrichment job was moved to flex processing because it is not urgent and flex is priced like batch. It has been fine for six weeks. It is still fine, in the sense that nothing has ever paged: the job logs a count at the end, the count is lower some nights, and the difference is a few thousand records that quietly did not get enriched. The invoice is lower too, which is exactly what everybody expected to see, and which is why nobody looked.",
"short_answer": """<p>One GET with an <strong>admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={T-7d}&amp;bucket_width=1h&amp;limit=168&amp;group_by[]=service_tier&amp;group_by[]=model</code>. Every result carries <code>num_model_requests</code>, <code>input_tokens</code>, <code>output_tokens</code> and, because of the grouping, the <code>service_tier</code> the request was actually <em>served</em> on.</p>
<p>Two findings, and they are opposite mistakes. The first is a model you configured for flex that has <strong>no flex rows at all</strong> while it has plenty on <code>default</code>: the parameter is not reaching the API, so you are paying standard rates for a workload you believe is discounted. That needs the model names as input, which is why the script takes <code>--flex-model</code>; the platform cannot tell you what you meant to ask for.</p>
<p>The second is the one this note is named after. A <code>429 Resource Unavailable</code> means flex had no capacity right now, and it is <strong>explicitly not charged</strong>. An unbilled request does not appear in a usage report, so those failures leave no row, no error count and no token anywhere in the API. The only trace is a hole: hours where flex volume collapses while the same organization is demonstrably still serving traffic on other tiers.</p>
<p>Absence is a weaker signal than an error, and the script treats it that way. It compares each hour's flex request count against the median of the hours that did get served, requires the organization to have been active in that hour before calling it a gap, and refuses to grade at all on fewer than a handful of served hours.</p>
<p>The cost report cannot help here: its <code>group_by</code> accepts <code>project_id</code>, <code>line_item</code> and <code>api_key_id</code>, and nothing about service tiers. The usage endpoint is the only place the tiers are separated, which is why this note reads one endpoint and not two.</p>""",
"problem": """<p>Flex processing trades latency and availability for much cheaper tokens, which is a good trade for evals, backfills, enrichment and anything else that runs overnight. The part that surprises people is how it declines. It does not queue and it does not degrade: when there is no capacity it answers <code>429 Resource Unavailable</code>, and you are not charged for it.</p>
<p>Not being charged is the humane behaviour and it is also why this is invisible. The organization usage endpoints report what was processed. A request that was refused for lack of capacity was not processed, produced no tokens, and does not increment <code>num_model_requests</code>. There is no error counter on the API, no failed-request feed, and no field anywhere that says how many times flex said no. The only place those failures exist is in your own client logs, and the client that swallowed them is usually a batch script whose logs roll over.</p>
<p>The second failure mode is the clock. The official SDKs default to a ten-minute request timeout, and flex responses regularly take longer than standard ones, so the recommendation is to raise the client timeout to at least fifteen minutes. A client left on the default aborts a request that the server may well go on to finish, which means the tokens can be billed to an answer nobody received. The SDKs then retry a 408 automatically, which triples the wall clock before anything surfaces to a human.</p>
<p>And the third is the quiet one: flex not being applied at all. <code>service_tier</code> is a request parameter, and a gateway that normalises request bodies, an SDK wrapper with its own defaults, or a code path that never set it will simply send the request at standard tier. Every one of those requests succeeds. The bill is the only place it shows up, and it shows up as a number that is higher than expected rather than as anything that looks like a fault.</p>""",
"why": """<p><strong>The evidence is a hole, so the script has to be honest about how weak that is.</strong> Every other reading in this section counts something that happened. This one counts something that did not, which is one inference further from the data, and inference dressed up as measurement is how a diagnostic loses its credibility. So the gap test has three guards: the hour must be below half the median of the hours that were served, the organization must have been serving something on some tier in that same hour, and there must be enough served hours to have a median worth comparing against. Below that, the script says it cannot tell.</p>
<p><strong>The tier in the report is the tier that was served, not the tier that was asked for.</strong> That is the property that makes the whole reading possible. The <code>service_tier</code> on a response reflects the processing mode actually used, and the grouped usage report inherits that. So flex rows are proof of flex being served, and their absence next to a healthy <code>default</code> row for the same model is proof that something dropped your parameter on the way.</p>
<p><strong>Which models you meant to run on flex is not knowable from the API, so it is an input.</strong> Nothing OpenAI returns knows what your code sends. A script that guessed &mdash; by treating any model with no flex rows as misconfigured, say &mdash; would report every model you deliberately run at standard tier as a fault. Passing the model ids explicitly is the difference between a finding and a list of every model you own.</p>
<p><strong>The cost report is the wrong instrument and saying so is part of the answer.</strong> It is the natural place to look, and its <code>group_by</code> supports <code>project_id</code>, <code>line_item</code> and <code>api_key_id</code> only. There is no service tier dimension on it, so flex spend cannot be separated from standard spend there at any granularity. The reading has to be done in the usage endpoint, in requests and tokens, and converted to money by you.</p>
<p><strong>The timeout cannot be read from the API at all, so it is printed as a repair rather than detected.</strong> Client configuration lives in your source tree and nothing either provider returns describes it. The script says what the floor should be and why, and does not pretend to have measured it.</p>""",
"steps": [
 {"h": "Use an admin key and name the models you configured for flex",
  "body": """<p><code>/v1/organization/usage/completions</code> needs an admin key. Pass <code>--flex-model gpt-5.6</code> once per model id your code sends <code>service_tier: "flex"</code> for. Without them the script can still find shortfalls, but it cannot tell a tier that was never served from a tier you never requested, and it says which of the two checks it had to skip.</p>"""},
 {"h": "Read seven days of hourly buckets grouped by tier and model",
  "body": """<p><code>bucket_width=1h</code> allows up to 168 buckets, which is exactly a week. Group by <code>service_tier</code> and <code>model</code>; both appear as fields on each result, <code>null</code> when you did not group by them. Page on <code>next_page</code> until <code>has_more</code> is false.</p>"""},
 {"h": "Check the models you named for any flex row at all",
  "body": """<p>A named model with zero flex requests and a healthy <code>default</code> count is the parameter never arriving. Print the tiers it actually ran on and the request counts, because that is the sentence that ends the argument about whether the gateway rewrites bodies.</p>"""},
 {"h": "Compare each hour's flex volume against the median served hour",
  "body": """<p>Build the per-hour flex request counts, take the median over the hours that were served, and flag hours at or below half of it &mdash; but only where some tier served something that hour, so a quiet night is not reported as a capacity failure. Fewer than a handful of served hours means no median worth having, and the script declines rather than guessing.</p>"""},
 {"h": "Read the repairs, none of which the script performs",
  "body": """<p>Raise the client timeout to at least fifteen minutes, back off on <code>429 Resource Unavailable</code> rather than treating it as a limit you exceeded, and fall back to <code>service_tier: "auto"</code> when completion matters more than price. Keep flex on evals, enrichment and background work, and off anything a person is waiting for.</p>"""},
],
"verify": """<p>Fix the parameter or the timeout and re-run a week later. A model that was <code>flex-never-served</code> should now carry flex rows with request counts in the same order as its old <code>default</code> counts, and the shortfall count should fall. A run that stays at <code>flex-shortfall</code> after the client is correct is telling you something real about capacity at those hours, and the repair for that is scheduling rather than code.</p>
<pre><code class="language-bash">python3 openai_flex_tier_served.py --flex-model gpt-5.6 --days 7
# 168 hourly bucket(s), 4 tier(s) observed: batch, default, flex, priority
# flex-never-served     gpt-5.6: 0 flex request(s) in 7 days, and 41,208 on
#                       default. The service_tier parameter is not reaching
#                       the API.
#   repair: the tier in this report is the tier that was served. Check for a
#           gateway that rewrites request bodies, an SDK wrapper with its own
#           defaults, or a code path that never set service_tier at all.
# flex-shortfall        gpt-5.3-mini: 9 hour(s) at or below half the median
#                       served hour (median 2,140 requests)
#   2026-08-27T02:00Z        0 requests, other tiers served 8,400 that hour
#   2026-08-28T02:00Z      130 requests, other tiers served 7,900 that hour
#   note: a 429 Resource Unavailable is not charged and never reaches this
#         report, so these hours are absence rather than error counts.
#   repair: back off and retry on 429 Resource Unavailable, which means no
#           capacity rather than a limit you exceeded.
#   repair: raise the client timeout to at least 15 minutes. The SDK default
#           is 10 and flex responses regularly exceed it.
# 2 finding(s)</code></pre>""",
"code_intro": "One paged GET and seven pure functions. <code>tier_rows</code>, which folds the buckets into <code>{(model, tier): {hour: counts}}</code> and keeps hours with no rows out rather than inventing zeros; <code>totals_by_tier</code>; <code>hours_active</code>, which records how much every tier together served in each hour, because that is the control that stops a quiet night reading as a capacity failure; <code>median</code>, chosen over the mean because one enormous backfill hour would drag a mean far enough to hide the gaps; <code>flex_gaps</code>, which applies the three guards and returns nothing when there is not enough served history to have an opinion; <code>never_served</code>, which needs the configured model ids as input because the API cannot know them; and <code>verdict</code>.",
"py_file": "openai_flex_tier_served.py",
"py": '''"""Find flex tier work that was never served, and flex you never actually asked for.

Read only. One paged GET with an admin key:

  GET /v1/organization/usage/completions
      ?bucket_width=1h&group_by[]=service_tier&group_by[]=model

The tier on each result is the tier the request was actually served on, which is
what makes this readable at all. Two opposite findings come out of it: a model
configured for flex with no flex rows anywhere (the parameter is not arriving),
and hours where flex volume collapses while other tiers keep serving (capacity
was refused).

A 429 Resource Unavailable is explicitly not charged, so it never appears in any
usage report. The evidence for it is a hole, which is one inference further from
the data than everything else in this section, so the gap test is deliberately
conservative: below half the median served hour, in an hour the organization was
otherwise active, with enough served hours to have a median worth comparing to.

The cost report cannot substitute: its group_by accepts project_id, line_item
and api_key_id and has no service tier dimension at all.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_flex_tier_served")

API = "https://api.openai.com/v1"
FLEX = "flex"

# Enough served hours to have a median worth comparing against. Below this the
# script says it cannot tell rather than grading two data points.
MIN_SERVED_HOURS = 6

FINDINGS = ("flex-never-served", "flex-shortfall")


def num(value):
    """A float, or 0.0. Pure."""
    if value is None or isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def tier_rows(pages):
    """{(model, tier): {hour: {"requests", "input", "output"}}}. Pure.

    Hours with no row for a pairing are simply absent. Filling them with zeros
    here would destroy the difference between "served nothing" and "was not
    grouped this way", which is the whole subject.
    """
    out = {}
    for page in pages or []:
        for bucket in ((page or {}).get("data") or []):
            hour = int(num((bucket or {}).get("start_time")))
            for result in ((bucket or {}).get("results") or []):
                result = result or {}
                key = (str(result.get("model") or "(all models)"),
                       str(result.get("service_tier") or "(untiered)"))
                row = out.setdefault(key, {}).setdefault(
                    hour, {"requests": 0.0, "input": 0.0, "output": 0.0})
                row["requests"] += num(result.get("num_model_requests"))
                row["input"] += num(result.get("input_tokens"))
                row["output"] += num(result.get("output_tokens"))
    return out


def totals_by_tier(rows):
    """{tier: total requests}. Pure."""
    out = {}
    for (_model, tier), hours in (rows or {}).items():
        out[tier] = out.get(tier, 0.0) + sum(h["requests"] for h in hours.values())
    return out


def hours_active(rows):
    """{hour: requests served across every tier}. Pure.

    The control. Without it a night when the job did not run reads exactly like
    a night when flex refused every request.
    """
    out = {}
    for hours in (rows or {}).values():
        for hour, counts in hours.items():
            out[hour] = out.get(hour, 0.0) + counts["requests"]
    return out


def median(values):
    """The median of a list. Pure. 0.0 when empty.

    Median rather than mean on purpose: one enormous backfill hour drags a mean
    high enough to swallow the very gaps this is looking for.
    """
    ordered = sorted(float(v) for v in (values or []))
    if not ordered:
        return 0.0
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def flex_by_hour(rows, model):
    """{hour: flex requests} for one model. Pure."""
    return {hour: counts["requests"]
            for hour, counts in ((rows or {}).get((model, FLEX)) or {}).items()}


def tiers_for_model(rows, model):
    """{tier: requests} for one model across every tier. Pure."""
    out = {}
    for (candidate, tier), hours in (rows or {}).items():
        if candidate != model:
            continue
        out[tier] = out.get(tier, 0.0) + sum(h["requests"] for h in hours.values())
    return out


def flex_gaps(flex_hours, active, floor=0.5, min_served=MIN_SERVED_HOURS):
    """[(hour, flex_requests, other_requests, median)] where flex collapsed. Pure.

    Three guards, all of them there to stop absence being over-read. The hour
    must be at or below floor times the median served hour; some tier must have
    served something in that same hour; and there must be at least min_served
    hours of flex traffic to take a median from at all.
    """
    served = [v for v in (flex_hours or {}).values() if v > 0]
    if len(served) < min_served:
        return []
    mid = median(served)
    if mid <= 0:
        return []
    out = []
    for hour, total in sorted((active or {}).items()):
        flex = float((flex_hours or {}).get(hour, 0.0))
        other = float(total) - flex
        if flex <= mid * floor and other > 0:
            out.append((hour, flex, other, mid))
    out.sort(key=lambda r: (r[1], r[0]))
    return out


def never_served(rows, configured):
    """[(model, flex_requests, {tier: requests})] for models with no flex rows.

    Pure. configured is the list of model ids your code sends flex for, because
    nothing the API returns knows what you meant to ask for. Without it this
    check cannot run, and guessing would report every deliberately standard
    model as a fault.
    """
    out = []
    for model in sorted(set(str(m) for m in (configured or []) if m)):
        tiers = tiers_for_model(rows, model)
        if tiers.get(FLEX, 0.0) > 0:
            continue
        if sum(tiers.values()) <= 0:
            continue
        out.append((model, 0.0, tiers))
    return out


def verdict(model, flex_hours, gaps, tiers, configured):
    """Classify one model. Pure. Returns (state, detail)."""
    tiers = tiers or {}
    flex_total = tiers.get(FLEX, 0.0)
    other_total = sum(v for t, v in tiers.items() if t != FLEX)
    if flex_total <= 0 and model in set(configured or []):
        if other_total <= 0:
            return ("no-usage", "no requests on any tier in this window")
        return ("flex-never-served",
                "%s flex request(s) in this window, and %s on other tiers. The "
                "service_tier parameter is not reaching the API."
                % (fmt(flex_total), fmt(other_total)))
    if flex_total <= 0:
        return ("no-flex-usage", "never served on flex in this window")
    if gaps:
        mid = gaps[0][3]
        return ("flex-shortfall",
                "%d hour(s) at or below half the median served hour (median %s "
                "requests)" % (len(gaps), fmt(mid)))
    served = len([v for v in (flex_hours or {}).values() if v > 0])
    if served < MIN_SERVED_HOURS:
        return ("too-little-history",
                "%d hour(s) of flex traffic, which is not enough to take a "
                "median from" % served)
    return ("flex-served",
            "%s flex request(s) across %d hour(s), no collapsed hours"
            % (fmt(flex_total), served))


def fmt(value):
    """Thousands separators. Pure."""
    return "{:,}".format(int(round(num(value))))


def stamp(hour):
    """An hour bucket's start as a readable UTC string. Pure."""
    return dt.datetime.fromtimestamp(int(hour), dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:00Z")


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "flex-never-served":
        return ["the tier in this report is the tier that was served. Check for a "
                "gateway that rewrites request bodies, an SDK wrapper with its "
                "own defaults, or a code path that never set service_tier at all.",
                "until it arrives you are paying standard rates for a workload "
                "you believe is discounted, and nothing will raise about it."]
    if state == "flex-shortfall":
        return ["back off and retry on 429 Resource Unavailable, which means no "
                "capacity right now rather than a limit you exceeded. Retrying "
                "it genuinely helps, unlike the billing 429s.",
                "raise the client timeout to at least 15 minutes. The official "
                "SDK default is 10 and flex responses regularly exceed it, and "
                "an aborted request can still be billed if the server finishes.",
                "fall back to service_tier auto when completing the work matters "
                "more than the discount, and keep flex off anything a person is "
                "waiting for."]
    if state == "too-little-history":
        return ["not a clean bill of health, just too little to read. Re-run over "
                "a longer window once the job has more served hours behind it."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: the organization usage endpoints need "
                         "an admin key" % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, **params):
    params = dict(params)
    for _ in range(50):
        page = get(session, path, **params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--flex-model", action="append", default=[],
                    help="a model id your code sends service_tier flex for "
                         "(repeatable)")
    ap.add_argument("--days", type=float, default=7.0,
                    help="window in days (max 7 at hourly buckets)")
    ap.add_argument("--floor", type=float, default=0.5,
                    help="share of the median served hour below which an hour "
                         "counts as collapsed")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY to an admin key that can read the "
                  "organization usage endpoints")
        return 2
    days = max(0.5, min(7.0, args.days))

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key,
                      "User-Agent": "openai-flex-tier-served/1.0"})

    now = dt.datetime.now(dt.timezone.utc)
    start = int((now - dt.timedelta(days=days)).timestamp())
    payloads = list(pages(s, "/organization/usage/completions",
                          start_time=start, bucket_width="1h", limit=168,
                          **{"group_by[]": ["service_tier", "model"]}))

    rows = tier_rows(payloads)
    totals = totals_by_tier(rows)
    active = hours_active(rows)
    buckets = sum(len(page.get("data") or []) for page in payloads)
    log.info("%d hourly bucket(s), %d tier(s) observed: %s",
             buckets, len(totals), ", ".join(sorted(totals)) or "none")

    configured = [str(m) for m in args.flex_model if m]
    if not configured:
        log.info("no --flex-model given, so the never-served check is skipped: "
                 "nothing the API returns knows which models your code asks for "
                 "flex on")

    findings = 0
    models = sorted({model for model, _tier in rows} | set(configured))
    for model in models:
        flex_hours = flex_by_hour(rows, model)
        gaps = flex_gaps(flex_hours, active, args.floor)
        tiers = tiers_for_model(rows, model)
        state, detail = verdict(model, flex_hours, gaps, tiers, configured)
        if state in ("no-flex-usage", "no-usage") and model not in configured:
            continue
        emit = log.warning if state in FINDINGS else log.info
        emit("%-21s %s: %s", state, model, detail)
        for hour, flex, other, _mid in gaps[:5]:
            emit("  %s  %s requests, other tiers served %s that hour",
                 stamp(hour), fmt(flex), fmt(other))
        if state == "flex-shortfall":
            emit("  note: a 429 Resource Unavailable is not charged and never "
                 "reaches this report, so these hours are absence rather than "
                 "error counts.")
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    for model, _flex, tiers in never_served(rows, configured):
        if model in models:
            continue
        log.warning("%-21s %s: served only on %s", "flex-never-served", model,
                    ", ".join("%s (%s)" % (t, fmt(v))
                              for t, v in sorted(tiers.items())))
        findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-flex-tier-served.mjs",
"js": '''/**
 * Find flex tier work that was never served, and flex you never actually asked for.
 *
 * Read only. One paged GET of the completions usage report, grouped by
 * service_tier and model. The tier on each result is the tier the request was
 * actually served on, which is what makes this readable at all.
 *
 * A 429 Resource Unavailable is explicitly not charged, so it never appears in
 * any usage report: the evidence is a hole. The gap test is deliberately
 * conservative because absence is one inference further from the data than
 * everything else in this section.
 *
 * The cost report cannot substitute: its group_by accepts project_id, line_item
 * and api_key_id and has no service tier dimension at all.
 */
const API = 'https://api.openai.com/v1';
const FLEX = 'flex';

export const MIN_SERVED_HOURS = 6;
const FINDINGS = new Set(['flex-never-served', 'flex-shortfall']);

/** A number, or 0. Pure. */
export function num(value) {
  if (value === null || value === undefined || typeof value === 'boolean') return 0;
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

const key = (model, tier) => `${model}\\u0000${tier}`;

/** {"model\\0tier": {hour: {requests, input, output}}}. Pure. */
export function tierRows(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      const hour = Math.trunc(num(bucket?.start_time));
      for (const result of bucket?.results ?? []) {
        const k = key(String(result?.model ?? '(all models)'),
                      String(result?.service_tier ?? '(untiered)'));
        const hours = (out[k] ??= {});
        const row = (hours[hour] ??= { requests: 0, input: 0, output: 0 });
        row.requests += num(result?.num_model_requests);
        row.input += num(result?.input_tokens);
        row.output += num(result?.output_tokens);
      }
    }
  }
  return out;
}

/** {tier: total requests}. Pure. */
export function totalsByTier(rows) {
  const out = {};
  for (const [k, hours] of Object.entries(rows ?? {})) {
    const tier = k.split('\\u0000')[1];
    out[tier] = (out[tier] ?? 0)
      + Object.values(hours).reduce((n, h) => n + h.requests, 0);
  }
  return out;
}

/** {hour: requests served across every tier}. Pure. The control. */
export function hoursActive(rows) {
  const out = {};
  for (const hours of Object.values(rows ?? {})) {
    for (const [hour, counts] of Object.entries(hours)) {
      out[hour] = (out[hour] ?? 0) + counts.requests;
    }
  }
  return out;
}

/** The median of a list. Pure. 0 when empty. */
export function median(values) {
  const ordered = [...(values ?? [])].map(Number).sort((a, b) => a - b);
  if (ordered.length === 0) return 0;
  const mid = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[mid] : (ordered[mid - 1] + ordered[mid]) / 2;
}

/** {hour: flex requests} for one model. Pure. */
export function flexByHour(rows, model) {
  const hours = (rows ?? {})[key(model, FLEX)] ?? {};
  return Object.fromEntries(Object.entries(hours).map(([h, c]) => [h, c.requests]));
}

/** {tier: requests} for one model across every tier. Pure. */
export function tiersForModel(rows, model) {
  const out = {};
  for (const [k, hours] of Object.entries(rows ?? {})) {
    const [candidate, tier] = k.split('\\u0000');
    if (candidate !== model) continue;
    out[tier] = (out[tier] ?? 0)
      + Object.values(hours).reduce((n, h) => n + h.requests, 0);
  }
  return out;
}

/** [[hour, flexRequests, otherRequests, median]] where flex collapsed. Pure. */
export function flexGaps(flexHours, active, floor = 0.5, minServed = MIN_SERVED_HOURS) {
  const served = Object.values(flexHours ?? {}).filter((v) => v > 0);
  if (served.length < minServed) return [];
  const mid = median(served);
  if (mid <= 0) return [];
  const out = [];
  for (const hour of Object.keys(active ?? {}).sort((a, b) => Number(a) - Number(b))) {
    const flex = Number((flexHours ?? {})[hour] ?? 0);
    const other = Number(active[hour]) - flex;
    if (flex <= mid * floor && other > 0) out.push([Number(hour), flex, other, mid]);
  }
  out.sort((a, b) => (a[1] - b[1]) || (a[0] - b[0]));
  return out;
}

/** [[model, 0, {tier: requests}]] for configured models with no flex rows. Pure. */
export function neverServed(rows, configured) {
  const out = [];
  const models = [...new Set((configured ?? []).filter(Boolean).map(String))].sort();
  for (const model of models) {
    const tiers = tiersForModel(rows, model);
    if ((tiers[FLEX] ?? 0) > 0) continue;
    if (Object.values(tiers).reduce((n, v) => n + v, 0) <= 0) continue;
    out.push([model, 0, tiers]);
  }
  return out;
}

/** Thousands separators. Pure. */
export function fmt(value) {
  return Math.round(num(value)).toLocaleString('en-US');
}

/** Classify one model. Pure. Returns [state, detail]. */
export function verdict(model, flexHours, gaps, tiers, configured) {
  const byTier = tiers ?? {};
  const flexTotal = byTier[FLEX] ?? 0;
  const otherTotal = Object.entries(byTier)
    .filter(([t]) => t !== FLEX).reduce((n, [, v]) => n + v, 0);
  if (flexTotal <= 0 && (configured ?? []).includes(model)) {
    if (otherTotal <= 0) return ['no-usage', 'no requests on any tier in this window'];
    return ['flex-never-served',
            `${fmt(flexTotal)} flex request(s) in this window, and ${fmt(otherTotal)} `
            + 'on other tiers. The service_tier parameter is not reaching the API.'];
  }
  if (flexTotal <= 0) return ['no-flex-usage', 'never served on flex in this window'];
  if ((gaps ?? []).length) {
    return ['flex-shortfall',
            `${gaps.length} hour(s) at or below half the median served hour `
            + `(median ${fmt(gaps[0][3])} requests)`];
  }
  const served = Object.values(flexHours ?? {}).filter((v) => v > 0).length;
  if (served < MIN_SERVED_HOURS) {
    return ['too-little-history',
            `${served} hour(s) of flex traffic, which is not enough to take a median from`];
  }
  return ['flex-served',
          `${fmt(flexTotal)} flex request(s) across ${served} hour(s), no collapsed hours`];
}

/** An hour bucket's start as a readable UTC string. Pure. */
export function stamp(hour) {
  return `${new Date(Number(hour) * 1000).toISOString().slice(0, 13)}:00Z`;
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'flex-never-served') {
    return ['the tier in this report is the tier that was served. Check for a '
      + 'gateway that rewrites request bodies, an SDK wrapper with its own '
      + 'defaults, or a code path that never set service_tier at all.',
      'until it arrives you are paying standard rates for a workload you believe '
      + 'is discounted, and nothing will raise about it.'];
  }
  if (state === 'flex-shortfall') {
    return ['back off and retry on 429 Resource Unavailable, which means no '
      + 'capacity right now rather than a limit you exceeded. Retrying it '
      + 'genuinely helps, unlike the billing 429s.',
      'raise the client timeout to at least 15 minutes. The official SDK default '
      + 'is 10 and flex responses regularly exceed it, and an aborted request can '
      + 'still be billed if the server finishes.',
      'fall back to service_tier auto when completing the work matters more than '
      + 'the discount, and keep flex off anything a person is waiting for.'];
  }
  if (state === 'too-little-history') {
    return ['not a clean bill of health, just too little to read. Re-run over a '
      + 'longer window once the job has more served hours behind it.'];
  }
  return [];
}

async function read(apiKey, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, String(one));
  }
  const r = await fetch(url, { headers: { Authorization: `Bearer ${apiKey}`,
                                          'User-Agent': 'openai-flex-tier-served/1.0' } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: the organization usage endpoints need `
                    + 'an admin key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function main() {
  const apiKey = process.env.OPENAI_ADMIN_KEY;
  if (!apiKey) {
    console.error('set OPENAI_ADMIN_KEY to an admin key that can read the '
                  + 'organization usage endpoints');
    process.exitCode = 2;
    return;
  }
  const days = Math.max(0.5, Math.min(7, Number(process.env.DAYS ?? 7)));
  const floor = Number(process.env.FLOOR ?? 0.5);
  const configured = (process.env.FLEX_MODELS ?? '').split(/[,\\s]+/).filter(Boolean);

  const start = Math.floor(Date.now() / 1000 - days * 86400);
  const payloads = [];
  const params = { start_time: start, bucket_width: '1h', limit: 168,
                   'group_by[]': ['service_tier', 'model'] };
  for (let i = 0; i < 50; i += 1) {
    const page = await read(apiKey, '/organization/usage/completions', params);
    payloads.push(page);
    if (!page.has_more || !page.next_page) break;
    params.page = page.next_page;
  }

  const rows = tierRows(payloads);
  const totals = totalsByTier(rows);
  const active = hoursActive(rows);
  const buckets = payloads.reduce((n, p) => n + (p.data ?? []).length, 0);
  console.log(`${buckets} hourly bucket(s), ${Object.keys(totals).length} tier(s) `
              + `observed: ${Object.keys(totals).sort().join(', ') || 'none'}`);
  if (configured.length === 0) {
    console.log('no FLEX_MODELS given, so the never-served check is skipped: nothing '
                + 'the API returns knows which models your code asks for flex on');
  }

  let findings = 0;
  const models = [...new Set([...Object.keys(rows).map((k) => k.split('\\u0000')[0]),
                              ...configured])].sort();
  for (const model of models) {
    const flexHours = flexByHour(rows, model);
    const gaps = flexGaps(flexHours, active, floor);
    const tiers = tiersForModel(rows, model);
    const [state, detail] = verdict(model, flexHours, gaps, tiers, configured);
    if (['no-flex-usage', 'no-usage'].includes(state) && !configured.includes(model)) {
      continue;
    }
    console.log(`${state.padEnd(21)} ${model}: ${detail}`);
    for (const [hour, flex, other] of gaps.slice(0, 5)) {
      console.log(`  ${stamp(hour)}  ${fmt(flex)} requests, other tiers served `
                  + `${fmt(other)} that hour`);
    }
    if (state === 'flex-shortfall') {
      console.log('  note: a 429 Resource Unavailable is not charged and never reaches '
                  + 'this report, so these hours are absence rather than error counts.');
    }
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test builds a week where flex is served every hour except three, with other tiers busy throughout, and asserts those three come back as gaps with the median printed. The second is the control that keeps the note honest: the same three empty hours with <em>no</em> traffic on any tier are a quiet night and must produce nothing. Then the never-served case, which only fires for a model passed in as configured, because the API cannot know what your code asks for; the minimum history rule, which must decline rather than grade two data points; the median, which has to be a median and not a mean or one backfill hour hides everything; and the tier fold, which must keep hours with no row absent rather than inventing zeros.",
"test_py_file": "test_openai_flex_tier_served.py",
"test_py": '''from openai_flex_tier_served import (flex_by_hour, flex_gaps, hours_active,
                                     median, never_served, stamp, repair_lines,
                                     tier_rows, tiers_for_model, totals_by_tier,
                                     verdict)

HOUR = 3600
BASE = 1787000000 // HOUR * HOUR


def result(model, tier, requests, out=0):
    return {"object": "organization.usage.completions.result",
            "input_tokens": requests * 800, "output_tokens": out,
            "num_model_requests": requests, "project_id": None,
            "model": model, "batch": False, "service_tier": tier}


def week(flex_per_hour, other_per_hour, hours=24, model="gpt-5.6"):
    data = []
    for i in range(hours):
        results = []
        flex = flex_per_hour(i)
        other = other_per_hour(i)
        if flex:
            results.append(result(model, "flex", flex))
        if other:
            results.append(result(model, "default", other))
        data.append({"object": "bucket", "start_time": BASE + i * HOUR,
                     "end_time": BASE + (i + 1) * HOUR, "results": results})
    return [{"object": "page", "data": data, "has_more": False, "next_page": None}]


def test_hours_where_flex_collapsed_while_other_tiers_kept_serving():
    # The note. Flex runs at about 2,000 an hour except for three hours where
    # it is refused, and default keeps going throughout, which is what makes
    # those three hours a capacity signal rather than a quiet night.
    dead = {5, 11, 19}
    pages = week(lambda i: 0 if i in dead else 2_000, lambda i: 8_000)
    rows = tier_rows(pages)
    gaps = flex_gaps(flex_by_hour(rows, "gpt-5.6"), hours_active(rows))
    assert [g[0] for g in gaps] == [BASE + h * HOUR for h in sorted(dead)]
    assert gaps[0][1] == 0.0 and gaps[0][2] == 8_000.0 and gaps[0][3] == 2_000.0
    state, detail = verdict("gpt-5.6", flex_by_hour(rows, "gpt-5.6"), gaps,
                            tiers_for_model(rows, "gpt-5.6"), ["gpt-5.6"])
    assert state == "flex-shortfall"
    assert "3 hour(s)" in detail
    lines = repair_lines(state)
    assert any("Resource Unavailable" in line for line in lines)
    assert any("15 minutes" in line for line in lines)
    assert stamp(BASE).endswith(":00Z")


def test_a_quiet_night_is_not_a_capacity_failure():
    # The control. Same three empty flex hours, but nothing else ran either.
    dead = {5, 11, 19}
    pages = week(lambda i: 0 if i in dead else 2_000,
                 lambda i: 0 if i in dead else 8_000)
    rows = tier_rows(pages)
    assert flex_gaps(flex_by_hour(rows, "gpt-5.6"), hours_active(rows)) == []
    state, _ = verdict("gpt-5.6", flex_by_hour(rows, "gpt-5.6"), [],
                       tiers_for_model(rows, "gpt-5.6"), ["gpt-5.6"])
    assert state == "flex-served"


def test_a_model_configured_for_flex_that_never_gets_it():
    pages = week(lambda i: 0, lambda i: 1_717)
    rows = tier_rows(pages)
    tiers = tiers_for_model(rows, "gpt-5.6")
    assert tiers == {"default": 41_208.0}
    state, detail = verdict("gpt-5.6", {}, [], tiers, ["gpt-5.6"])
    assert state == "flex-never-served"
    assert "41,208 on other tiers" in detail
    assert any("rewrites request bodies" in line for line in repair_lines(state))
    # And the same model, not declared as configured, is nobody's business.
    assert verdict("gpt-5.6", {}, [], tiers, [])[0] == "no-flex-usage"
    assert never_served(rows, ["gpt-5.6"])[0][0] == "gpt-5.6"
    assert never_served(rows, []) == []
    assert never_served(rows, ["never-called-model"]) == []


def test_too_little_flex_history_declines_rather_than_grading():
    pages = week(lambda i: 2_000 if i < 4 else 0, lambda i: 8_000)
    rows = tier_rows(pages)
    flex_hours = flex_by_hour(rows, "gpt-5.6")
    assert flex_gaps(flex_hours, hours_active(rows)) == []
    state, detail = verdict("gpt-5.6", flex_hours, [],
                            tiers_for_model(rows, "gpt-5.6"), ["gpt-5.6"])
    assert state == "too-little-history"
    assert "not enough to take a median" in detail
    assert any("not a clean bill of health" in line for line in repair_lines(state))


def test_the_median_is_a_median_and_not_a_mean():
    # One enormous backfill hour. The mean of this is over 12,000, which would
    # put every ordinary hour under half of it and report the whole week.
    values = [2_000, 2_000, 2_000, 2_000, 2_000, 100_000]
    assert median(values) == 2_000.0
    assert sum(values) / len(values) > 12_000
    assert median([]) == 0.0
    assert median([5]) == 5.0
    assert median([1, 3]) == 2.0


def test_the_fold_keeps_absent_hours_absent():
    pages = week(lambda i: 0 if i % 2 else 100, lambda i: 50)
    rows = tier_rows(pages)
    flex_hours = flex_by_hour(rows, "gpt-5.6")
    # Twelve flex hours out of twenty four, and the other twelve are missing
    # rather than present with a zero.
    assert len(flex_hours) == 12
    assert all(v == 100.0 for v in flex_hours.values())
    assert len(hours_active(rows)) == 24
    assert totals_by_tier(rows) == {"flex": 1_200.0, "default": 1_200.0}
    assert tier_rows(None) == {} and totals_by_tier(None) == {}
    assert hours_active(None) == {} and flex_by_hour(None, "x") == {}
    assert verdict("x", {}, [], {}, [])[0] == "no-flex-usage"
    assert repair_lines("flex-served") == []
''',
"test_js_file": "openai-flex-tier-served.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { flexByHour, flexGaps, hoursActive, median, neverServed, repairLines,
         stamp, tierRows, tiersForModel, totalsByTier, verdict }
  from './openai-flex-tier-served.mjs';

const HOUR = 3600;
const BASE = Math.floor(1787000000 / HOUR) * HOUR;

const result = (model, tier, requests) => ({
  object: 'organization.usage.completions.result',
  input_tokens: requests * 800, output_tokens: 0,
  num_model_requests: requests, project_id: null,
  model, batch: false, service_tier: tier,
});

const week = (flexPerHour, otherPerHour, hours = 24, model = 'gpt-5.6') => {
  const data = [];
  for (let i = 0; i < hours; i += 1) {
    const results = [];
    const flex = flexPerHour(i);
    const other = otherPerHour(i);
    if (flex) results.push(result(model, 'flex', flex));
    if (other) results.push(result(model, 'default', other));
    data.push({ object: 'bucket', start_time: BASE + i * HOUR,
                end_time: BASE + (i + 1) * HOUR, results });
  }
  return [{ object: 'page', data, has_more: false, next_page: null }];
};

test('hours where flex collapsed while other tiers kept serving', () => {
  const dead = new Set([5, 11, 19]);
  const rows = tierRows(week((i) => (dead.has(i) ? 0 : 2000), () => 8000));
  const gaps = flexGaps(flexByHour(rows, 'gpt-5.6'), hoursActive(rows));
  assert.deepEqual(gaps.map((g) => g[0]),
                   [...dead].sort((a, b) => a - b).map((h) => BASE + h * HOUR));
  assert.equal(gaps[0][1], 0);
  assert.equal(gaps[0][2], 8000);
  assert.equal(gaps[0][3], 2000);
  const [state, detail] = verdict('gpt-5.6', flexByHour(rows, 'gpt-5.6'), gaps,
                                  tiersForModel(rows, 'gpt-5.6'), ['gpt-5.6']);
  assert.equal(state, 'flex-shortfall');
  assert.match(detail, /3 hour\\(s\\)/);
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('Resource Unavailable')));
  assert.ok(lines.some((l) => l.includes('15 minutes')));
  assert.ok(stamp(BASE).endsWith(':00Z'));
});

test('a quiet night is not a capacity failure', () => {
  const dead = new Set([5, 11, 19]);
  const rows = tierRows(week((i) => (dead.has(i) ? 0 : 2000),
                             (i) => (dead.has(i) ? 0 : 8000)));
  assert.deepEqual(flexGaps(flexByHour(rows, 'gpt-5.6'), hoursActive(rows)), []);
  const [state] = verdict('gpt-5.6', flexByHour(rows, 'gpt-5.6'), [],
                          tiersForModel(rows, 'gpt-5.6'), ['gpt-5.6']);
  assert.equal(state, 'flex-served');
});

test('a model configured for flex that never gets it', () => {
  const rows = tierRows(week(() => 0, () => 1717));
  const tiers = tiersForModel(rows, 'gpt-5.6');
  assert.deepEqual(tiers, { default: 41208 });
  const [state, detail] = verdict('gpt-5.6', {}, [], tiers, ['gpt-5.6']);
  assert.equal(state, 'flex-never-served');
  assert.match(detail, /41,208 on other tiers/);
  assert.ok(repairLines(state).some((l) => l.includes('rewrites request bodies')));
  assert.equal(verdict('gpt-5.6', {}, [], tiers, [])[0], 'no-flex-usage');
  assert.equal(neverServed(rows, ['gpt-5.6'])[0][0], 'gpt-5.6');
  assert.deepEqual(neverServed(rows, []), []);
  assert.deepEqual(neverServed(rows, ['never-called-model']), []);
});

test('too little flex history declines rather than grading', () => {
  const rows = tierRows(week((i) => (i < 4 ? 2000 : 0), () => 8000));
  const flexHours = flexByHour(rows, 'gpt-5.6');
  assert.deepEqual(flexGaps(flexHours, hoursActive(rows)), []);
  const [state, detail] = verdict('gpt-5.6', flexHours, [],
                                  tiersForModel(rows, 'gpt-5.6'), ['gpt-5.6']);
  assert.equal(state, 'too-little-history');
  assert.match(detail, /not enough to take a median/);
  assert.ok(repairLines(state).some((l) => l.includes('not a clean bill of health')));
});

test('the median is a median and not a mean', () => {
  const values = [2000, 2000, 2000, 2000, 2000, 100000];
  assert.equal(median(values), 2000);
  assert.ok(values.reduce((a, b) => a + b, 0) / values.length > 12000);
  assert.equal(median([]), 0);
  assert.equal(median([5]), 5);
  assert.equal(median([1, 3]), 2);
});

test('the fold keeps absent hours absent', () => {
  const rows = tierRows(week((i) => (i % 2 ? 0 : 100), () => 50));
  const flexHours = flexByHour(rows, 'gpt-5.6');
  assert.equal(Object.keys(flexHours).length, 12);
  assert.ok(Object.values(flexHours).every((v) => v === 100));
  assert.equal(Object.keys(hoursActive(rows)).length, 24);
  assert.deepEqual(totalsByTier(rows), { flex: 1200, default: 1200 });
  assert.deepEqual(tierRows(null), {});
  assert.deepEqual(totalsByTier(null), {});
  assert.deepEqual(hoursActive(null), {});
  assert.deepEqual(flexByHour(null, 'x'), {});
  assert.equal(verdict('x', {}, [], {}, [])[0], 'no-flex-usage');
  assert.deepEqual(repairLines('flex-served'), []);
});
''',
"faq": [
 ("Why not retry a flex request and see whether it gets served?",
  "Because that is a generation. Every script in this section holds a key that can spend money on inference and none of them send one, and a note about capacity has no business creating traffic against the tier it is complaining about. The reading here is entirely a GET of the usage report. The consequence is that the script cannot tell you how many 429 Resource Unavailable responses you got, only that flex volume collapsed in hours when the rest of the organization was busy."),
 ("Why not read the cost report? Flex is cheaper, so the spend should show it.",
  "It should, and the cost report cannot show it. Its group_by supports project_id, line_item and api_key_id and has no service tier dimension at all, so flex spend and standard spend land in the same line item for the same model with no way to separate them. That is why this note reads one endpoint rather than reconciling two: the usage report is the only place the tiers are distinguished, and the money has to be worked out from the request and token counts it returns."),
 ("Does Anthropic have a flex tier this script should be checking too?",
  "Not in any form you can ask for. Its service tier documentation describes Priority, Standard and Batch, and the service_tier request parameter on the Messages API accepts auto and standard_only. Its usage report does enumerate flex and flex_discount among the values its service_tiers filter accepts, which is worth knowing if you are writing a report parser, but there is no documented way to request that tier, so there is nothing for a script to detect and this note stays on OpenAI."),
 ("How is this different from the priority tier note?",
  "That one is about a capacity commitment on Anthropic that a particular model may have no coverage for, and its finding is that a tier never appears for a model at all. This one is about a tier that appears, works, and then intermittently is not served, which is a different shape in a different provider's report: hours rather than models, and a collapse relative to a median rather than an absence relative to a purchase. They also fail in opposite directions financially. Priority is capacity you have paid for and may not be using; flex is a discount you may not be getting."),
 ("What about the timeouts in the title? Can the script see those?",
  "No, and it says so rather than implying otherwise. Client configuration lives in your source tree and neither API returns anything that describes it. What the script prints is the floor: raise the client timeout to at least fifteen minutes, because the official SDK default is ten and flex responses regularly exceed it. The part worth internalising is that a client-side abort does not necessarily cancel the work, so an aborted request can still be billed for an answer nobody collected, which is the opposite of the unbilled 429 and lands in the same report."),
],
"related": [REL_PRIO, REL_WALL, REL_RETRY],
"citations": [CITE_OA_FLEX, CITE_OA_USAGE, CITE_OPENAPI, CITE_TIERS],
},
]
