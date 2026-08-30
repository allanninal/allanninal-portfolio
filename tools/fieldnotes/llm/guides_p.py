#!/usr/bin/env python3
"""/llm/ field notes, batch P — the writing.

The shape of the organization, not the credentials inside it. Four reads that
answer a question no usage report can: how many containers does this org have,
who is allowed to spend from them, and who was handed the right to and never
collected it. Nothing here is about a key being wrong. Three of the four are
about there being nowhere for a key to be right.

`no-prod-dev-project-separation` had the hardest job, because a published note
already ranks cost rows by share of total and names the dominant one. This one
counts containers before it ranks anything, and the two findings are not the
same finding: a project holding ninety-six per cent of the bill in a nine-project
org is a concentration you can act on inside the structure you have, while a
single-project org has a hundred per cent share by construction and no second
row to compare it with. The script says so out loud — when it finds concentration
in an org that does have a boundary, it names the other reading and declines to
report a topology fault.

`default-workspace-cost-unattributable` is the narrow, fixable cousin of the
published note that says per-customer cost has no answer at all. That one is a
permanent property of the platform: your tenant is nowhere in the attribution
chain and no change on your side can put it there. This one is a bucket with two
named causes, one of which is a list of API keys you can move. The script's whole
value is refusing to report the bucket as one number: keys landing in the default
workspace have a repair, and Console playground traffic carries no key at all and
does not.

`too-many-organization-owners` and `openai-invites-pending-past-expiry` are
governance rather than money, and both had to clear the same bar as the rest of
the section: a read-only script has to find them through the provider's own API,
and the finding has to be an operational fact rather than a maxim. The first one
is a ratio computed off a roster with service accounts removed, because service
accounts are returned in the same list and are frequently owners by construction,
and counting them produces a confident finding about robots. The second turns on
a discrepancy the API itself creates: an invite whose `status` still reads
`pending` while its `expires_at` is already in the past. Filter on the status and
you will not see it.

Three of the four read OpenAI's Admin API, which is where the topology of an
organization is most legible; the second reads Anthropic's, because the default
workspace is an Anthropic object and has no OpenAI equivalent. The invite note is
OpenAI by name and stays there: Anthropic does list invites with the same status
and expiry test, and it does not carry the per-project role grants or the invite
audit trail that make the OpenAI record more than a membership.

Read only throughout, and stricter than usual: every request in this batch is a
GET, no script constructs a request body, and no output line contains a key
value, a secret or an invite token. Email addresses are masked, because three of
these four reports are lists of people.
"""

CITE_OA_PROJECTS = ("Projects — OpenAI API reference",
                    "https://platform.openai.com/docs/api-reference/projects")
CITE_OA_PROJECT_KEYS = ("Project API keys — OpenAI API reference",
                        "https://platform.openai.com/docs/api-reference/project-api-keys")
CITE_OA_ADMIN = ("Administration — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/administration")
CITE_OA_ADMIN_GUIDE = ("Admin APIs — OpenAI platform docs",
                       "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_OA_USAGE = ("Usage and costs — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/usage")
CITE_OA_INVITE = ("Invites — OpenAI API reference",
                  "https://platform.openai.com/docs/api-reference/invite")
CITE_OA_AUDIT = ("Audit logs — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/audit-logs")
CITE_OA_PROJECTS_HELP = ("Managing projects in the API platform — OpenAI help",
                         "https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform")
CITE_OA_SDK = ("openai-python admin API surface",
               "https://github.com/openai/openai-python/blob/main/api.md")
CITE_CL_USAGE_API = ("Usage and Cost API — Claude Docs",
                     "https://platform.claude.com/docs/en/manage-claude/usage-cost-api")
CITE_CL_COST_REPORT = ("Get cost report — Claude Admin API",
                       "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report")
CITE_CL_LIST_KEYS = ("List API keys — Claude Admin API",
                     "https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys")
CITE_CL_WORKSPACES = ("List workspaces — Claude Admin API",
                      "https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces")
CITE_CL_RATE_LIMITS_API = ("Rate limits API — Claude Docs",
                           "https://platform.claude.com/docs/en/manage-claude/rate-limits-api")

REL_DOMINATES = ("/llm/one-model-or-project-dominates-cost/",
                 "The concentration reading, which needs a second container to mean anything")
REL_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                   "The only ceiling an org without projects has left")
REL_TENANT = ("/llm/per-tenant-cost-attribution-impossible/",
              "The attribution question that has no answer at any threshold")
REL_ARCHIVED = ("/llm/archived-project-still-holds-keys/",
                "A container that stops appearing in the listing and keeps its keys")
REL_OWNER_LOST = ("/llm/key-owner-lost-project-access/",
                  "A credential that outlives the access it was minted under")
REL_TOPOLOGY = ("/llm/no-prod-dev-project-separation/",
                "Whether there is more than one container to grant anybody a role in")
REL_NULL_WS = ("/llm/default-workspace-cost-unattributable/",
               "The Anthropic half of the same topology, read from the cost report")
REL_OWNERS = ("/llm/too-many-organization-owners/",
              "Who already holds the role that invite is offering")
REL_INVITES = ("/llm/openai-invites-pending-past-expiry/",
               "The grants that were offered and never collected")

GUIDES = [
{
"slug": "no-prod-dev-project-separation",
"title": "One project holds every environment, so nothing can be capped",
"description": "Count the active projects before you rank them. One active project means there is no boundary to cap, alert or attribute against, only an org-wide total.",
"h1": "One project holds every environment, so nothing can be capped",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai default project everything",
             "openai separate prod and dev projects",
             "openai project spend limit per environment",
             "openai organization projects api audit",
             "openai cost by project_id single project"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because /v1/organization/projects and /v1/organization/costs both reject a project key.",
"lead": "Somebody asks what production costs. Not the API bill, which everyone knows to the dollar, but the production share of it, and the answer takes four days to arrive because there is no answer. Every request the company has ever made to OpenAI &mdash; the customer-facing assistant, the nightly evaluation suite, the CI job that regenerates fixtures, eleven laptops, and the prototype somebody wrote in March and never turned off &mdash; landed in a project called <code>Default project</code> that was created before anybody had an opinion about structure.",
"short_answer": """<p>Two GETs with an <strong>organization admin key</strong>. <code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code> for the containers, and <code>GET /v1/organization/costs?start_time={now-30d}&amp;bucket_width=1d&amp;limit=30&amp;group_by=project_id</code> for the money. The finding is the first number: how many projects have <code>status</code> of <code>"active"</code>.</p>
<p>One is the whole note. The project is the unit of nearly every control the platform offers &mdash; spend limits, spend alerts, rate limits, model permissions, hosted tool permissions, data retention &mdash; and every one of those is configured per project. An organization with one active project cannot apply any of them differentially. You cannot cap the experiments without capping the product, and you cannot grant a frontier model to research without granting it to the batch job.</p>
<p>Do the count before the ranking, because the ranking cannot tell you this. Grouped by <code>project_id</code>, a single-project org returns one row at a hundred per cent, which is arithmetic rather than a discovery, and it looks identical in a table to a genuine concentration finding in an org that has nine projects and puts everything in one of them. Those are different problems with different repairs, and <a href="/llm/one-model-or-project-dominates-cost/">the concentration note</a> is the one for the second.</p>
<p>Archived projects do not count as a boundary. They cannot receive new traffic, they are excluded from the default listing, and <code>include_archived=true</code> is passed here only so they can be counted and then set aside honestly.</p>""",
"problem": """<p>The default project is created for you and works from the first request, so there is never a moment at which anyone is forced to choose a structure. That is a good onboarding decision and a bad steady state, because it means the structural choice gets made by not making it, at the exact time when nobody yet knows what the environments will be.</p>
<p>What is lost is not visibility. Visibility is recoverable: the usage and cost reports will happily group by API key, and a disciplined team can name its keys well enough to reconstruct a rough split after the fact. What is lost is <strong>enforcement</strong>. A spend limit on the only project is a spend limit on production. A rate-limit override on the only project throttles the customer-facing path along with the evaluation run that caused the problem. A model permission that stops an experiment reaching an expensive model stops the product reaching it too. Every control the platform gives you is scoped to a container, and there is only one container.</p>
<p>And there is a one-way door in it. Projects can be archived; they cannot be deleted. The split you make is permanent in the sense that the names you choose are permanent, which is worth ten minutes of thought before the first one is created and is the usual reason the ten minutes never happen.</p>""",
"why": """<p><strong>Count containers first, and rank rows second, because the ranking is uninformative when the count is one.</strong> A share of total is a comparison, and a comparison needs something to compare with. In a single-project org the top row is a hundred per cent of spend for the same reason the only runner wins the race. The script therefore establishes the boundary count before it looks at a single dollar, and when it finds a dominant project in an org that <em>does</em> have several, it says explicitly that this is not a topology finding and points at the other reading.</p>
<p><strong>An ungrouped cost row is not a giant project, and mistaking it for one manufactures this exact finding.</strong> <code>GET /v1/organization/costs</code> without <code>group_by</code> returns <code>project_id: null</code> on every result. A reader that folds those nulls into a bucket and ranks it will report one enormous project in an organization that has twelve, which is a false positive in the most embarrassing direction. The fold keeps null rows out of the ranking and reports them separately as what they are: a call that was not grouped.</p>
<p><strong>Projects that exist and never receive traffic are a different state from projects that do not exist.</strong> Plenty of organizations created <code>staging</code> and <code>dev</code> during a security review and then never issued a key for either. The containers are there, every control on them is configured, and none of it does anything, because no traffic routes to them. That reads as a healthy topology in a project count and as a broken one in the cost report, so the script grades it separately and prints a different repair: the boundary is not the problem, the routing is.</p>
<p><strong>Key names inside the single project are corroboration, not evidence.</strong> When one project holds keys called <code>prod-worker</code>, <code>local-adam</code> and <code>ci-fixtures</code>, the environments already exist as a fact about how people work and are simply not represented in the platform. The script reads key <em>names</em> only, never values, matches environment words as whole tokens so that <code>devops-runner</code> is not read as a development key, and treats a match as a supporting line rather than a verdict.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>Every path under <code>/v1/organization/*</code> rejects a project key with a 401. Read scopes are enough for all three calls here, and this script has no other kind.</p>"""},
 {"h": "List the projects with include_archived=true, then set the archived ones aside",
  "body": """<p><code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>, paginated on <code>after</code>. Archived projects are excluded by default; asking for them and then excluding them deliberately is different from never seeing them. An archived project cannot take new traffic, so it is not a boundary &mdash; but if one is still billing, that is <a href="/llm/archived-project-still-holds-keys/">its own note</a>.</p>"""},
 {"h": "Count the active projects before you look at any money",
  "body": """<p>A count of one is the finding, whatever the spend report says. A count above one moves the question to whether the extra containers are actually used, which is a different grading path.</p>"""},
 {"h": "Group thirty days of cost by project_id, and drop the null rows",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-30d}&amp;bucket_width=1d&amp;limit=30&amp;group_by=project_id</code>. Results with a null <code>project_id</code> are ungrouped rows, not a project; they are reported separately and never ranked.</p>"""},
 {"h": "Read the key names in the dominant project, and print the repair",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code>, names only. Two or more environment words inside one project is the split that already exists in people's heads. The repair is a project per environment, each with its own service account, spend limit and rate limits &mdash; printed, never performed, and worth naming carefully because archiving is the only undo.</p>"""},
],
"verify": """<p>Re-run after the second project has a key and has served real traffic. The state moves from <code>no-boundary</code> to <code>boundary-unused</code> the moment the container exists, and only to <code>separated</code> once cost actually lands in more than one of them &mdash; which is the point, because a project with no traffic in it enforces nothing.</p>
<pre><code class="language-bash">python3 openai_project_boundary_audit.py --days 30
# 1 active project(s), 2 archived, $18,406.11 in the last 30 day(s)
# no-boundary          1 active project holds 100% of $18,406.11. There is no second
#                      container to cap, alert on, rate limit or attribute against.
#   corroboration: key names in Default project already name 3 environment(s): ci, local, prod
#   repair: create prod, staging and dev with POST /v1/organization/projects
#   repair: give each a service account and its own key, then move traffic key by key
#   repair: a spend limit, spend alerts and rate limits only exist per project
#   repair: projects can be archived but never deleted, so get the names right once
# 1 finding(s)</code></pre>""",
"code_intro": "Two paged GETs, one optional third for key names, and six pure functions. <code>active</code>, which drops archived projects by both <code>status</code> and <code>archived_at</code> because the two disagree in older responses; the cost fold, which keeps ungrouped null rows out of the ranking so a forgotten <code>group_by</code> cannot fabricate a giant project; the share ranking; a whole-token environment matcher; the verdict, which counts containers before it compares any money and hands concentration back to the other note when the org has a boundary; and the repair lines.",
"py_file": "openai_project_boundary_audit.py",
"py": '''"""Find an OpenAI organization with no project boundary to enforce anything on.

Read only. Two paged GETs against /v1/organization/projects and
/v1/organization/costs, plus one per dominant project for its key NAMES. Every
request is a GET and no request body is ever built.

The finding is the absence of a boundary, not the concentration of spend. A
single active project holds 100% of cost by construction, which is arithmetic;
a dominant project in an organization that has nine is a different reading with
a different repair, and this script names that reading rather than claiming it.

Key values are never read or printed. The key listing is used for the `name`
field only, and only as corroboration.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_project_boundary_audit")

API = "https://api.openai.com/v1"
UNGROUPED = "ungrouped"

# Environment words, matched as WHOLE tokens after splitting on anything that is
# not a letter or a digit. Substring matching here is how "devops-runner" gets
# reported as a development key and "provider-proxy" as a production one, which
# is a false positive attached to a person's naming habits.
ENV_WORDS = {
    "prod": "prod", "production": "prod", "live": "prod",
    "stage": "staging", "staging": "staging", "preprod": "staging",
    "dev": "dev", "development": "dev",
    "local": "local", "laptop": "local",
    "test": "test", "testing": "test", "qa": "test",
    "ci": "ci", "build": "ci",
    "sandbox": "sandbox", "scratch": "sandbox", "playground": "sandbox",
}

FINDINGS = ("no-boundary", "boundary-unused")


def active(projects):
    """Projects that can still receive traffic. Pure.

    Archived projects are dropped on either signal. `status` is the documented
    field and `archived_at` is the one that is reliably present, and a listing
    that carries one without the other is common enough that trusting a single
    field over-counts the boundary.
    """
    out = []
    for project in projects or []:
        row = project or {}
        if str(row.get("status") or "").strip().lower() == "archived":
            continue
        if row.get("archived_at"):
            continue
        out.append(row)
    return out


def spend_by_project(buckets):
    """{project_id: dollars} from the cost report. Pure.

    A result with a null project_id is an UNGROUPED row, not a project. Folding
    those into the ranking is how a forgotten group_by turns into a confident
    report of one enormous project in an organization that has twelve.
    """
    rows = {}
    for bucket in buckets or []:
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            name = row.get("project_id") or UNGROUPED
            try:
                value = float((row.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                continue
            rows[str(name)] = rows.get(str(name), 0.0) + value
    return rows


def shares(spend):
    """[(project_id, dollars, share)] over real projects only. Pure.

    Sorted by dollars descending. UNGROUPED is excluded from both the ranking
    and the denominator, so a share is always a share of attributable spend.
    """
    rows = {k: v for k, v in (spend or {}).items() if k != UNGROUPED}
    total = sum(rows.values())
    out = [(k, round(v, 2), (v / total) if total > 0 else 0.0)
           for k, v in rows.items()]
    out.sort(key=lambda r: (-r[1], r[0]))
    return out


def environments(name):
    """The environment classes named in one identifier. Pure.

    Tokenised on non-alphanumerics and matched whole, so "devops" is a team and
    "provider" is a noun. Returns a set, possibly empty.
    """
    tokens = re.split(r"[^a-z0-9]+", str(name or "").strip().lower())
    return {ENV_WORDS[t] for t in tokens if t in ENV_WORDS}


def mixed(names):
    """Every environment class named across a set of identifiers. Pure."""
    found = set()
    for name in names or []:
        found |= environments(name)
    return found


def verdict(active_count, ranked, min_spend=1.0, dominant=0.95):
    """Classify the organization's topology. Pure. Returns (state, detail).

    The container count is read before any money, because a share of total is a
    comparison and a single-project organization has nothing to compare with.
    """
    rows = list(ranked or [])
    total = round(sum(row[1] for row in rows), 2)

    if active_count <= 0:
        return ("no-active-projects",
                "the listing returned no active project at all, which usually "
                "means the key could not see them rather than that none exist")
    if active_count == 1:
        return ("no-boundary",
                "1 active project holds 100%% of $%s. There is no second "
                "container to cap, alert on, rate limit or attribute against."
                % format(total, ",.2f"))
    if total < min_spend:
        return ("no-spend-yet",
                "%d active project(s) and $%s of attributable spend in the "
                "window. The boundary exists and nothing has tested it yet."
                % (active_count, format(total, ",.2f")))

    top_id, top_amount, top_share = rows[0]
    quiet = [row for row in rows[1:] if row[1] <= 0.0]
    if top_share >= dominant and len(quiet) == len(rows) - 1:
        return ("boundary-unused",
                "%d active project(s), and %s carries %.0f%% of $%s while every "
                "other project has no spend at all. The containers exist and no "
                "traffic routes to them, so the controls on them enforce nothing."
                % (active_count, top_id, top_share * 100, format(total, ",.2f")))
    if top_share >= dominant:
        return ("concentration-not-topology",
                "%d active project(s), and %s carries %.0f%% of $%s. This "
                "organization has a boundary, so that is a concentration "
                "reading rather than a topology one and has a different repair."
                % (active_count, top_id, top_share * 100, format(total, ",.2f")))
    return ("separated",
            "%d active project(s) sharing $%s, top project at %.0f%%"
            % (active_count, format(total, ",.2f"), top_share * 100))


def repair_lines(state, envs=()):
    """The repair for one topology verdict. Pure. Printed, never performed."""
    found = sorted(envs or ())
    if state == "no-boundary":
        lines = [
            "create prod, staging and dev with POST /v1/organization/projects, "
            "which is the smallest split that lets any control differ.",
            "give each project its own service account and key, then move "
            "traffic one key at a time rather than in one cutover.",
            "spend limits, spend alerts, rate limits, model permissions and "
            "data retention are all configured per project and cannot differ "
            "until the projects do.",
            "projects can be archived but never deleted, so the names are "
            "permanent. Spend ten minutes on them once.",
        ]
        if found:
            lines.insert(0, "the environments already exist in your key names "
                            "(%s); they are simply not represented in the "
                            "platform." % ", ".join(found))
        return lines
    if state == "boundary-unused":
        return [
            "the projects are not the problem. Nothing routes to them.",
            "issue a key in the quiet projects and move the traffic that "
            "belongs there, then set the limits per project afterwards.",
            "until traffic actually lands in a project, every control "
            "configured on it is inert.",
        ]
    if state == "concentration-not-topology":
        return [
            "do not restructure on this reading. Rank the cost rows by share "
            "of total and ask which line item is expensive instead.",
        ]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    while True:
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def cost_buckets(session, params, max_pages=40):
    """Walk the paged cost report."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, "/organization/costs", **params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days, now=None):
    """Unix seconds at midnight UTC, `days` ago."""
    now = now or dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - dt.timedelta(days=days)).timestamp())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of cost to read (default 30)")
    ap.add_argument("--dominant", type=float, default=0.95,
                    help="share above which one project is called dominant")
    ap.add_argument("--no-key-names", action="store_true",
                    help="skip the key-name corroboration read")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a "
                  "project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    projects = list(paged(s, "/organization/projects", limit=100,
                          include_archived="true"))
    live = active(projects)
    spend = spend_by_project(cost_buckets(
        s, {"start_time": window_start(args.days), "bucket_width": "1d",
            "limit": min(args.days, 30), "group_by": "project_id"}))
    ranked = shares(spend)
    total = round(sum(row[1] for row in ranked), 2)

    log.info("%d active project(s), %d archived, $%s in the last %d day(s)",
             len(live), len(projects) - len(live), format(total, ",.2f"),
             args.days)
    if spend.get(UNGROUPED):
        log.info("$%s of cost came back ungrouped and is not counted as a "
                 "project", format(spend[UNGROUPED], ",.2f"))

    envs = set()
    if not args.no_key_names and live:
        target = live[0]
        if ranked:
            by_id = {p.get("id"): p for p in live}
            target = by_id.get(ranked[0][0], target)
        names = [(k or {}).get("name") or ""
                 for k in paged(s, "/organization/projects/%s/api_keys"
                                % target.get("id"), limit=100,
                                owner_project_access="any")]
        envs = mixed(names)
        if envs:
            log.info("key names in %s already name %d environment(s): %s",
                     target.get("name") or target.get("id"), len(envs),
                     ", ".join(sorted(envs)))

    state, detail = verdict(len(live), ranked, dominant=args.dominant)
    if state in FINDINGS:
        log.warning("%-26s %s", state, detail)
        for line in repair_lines(state, envs):
            log.warning("  repair: %s", line)
        log.info("1 finding(s)")
        return 1

    log.info("%-26s %s", state, detail)
    for line in repair_lines(state, envs):
        log.info("  note: %s", line)
    log.info("0 finding(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-project-boundary-audit.mjs",
"js": '''/**
 * Find an OpenAI organization with no project boundary to enforce anything on.
 *
 * Read only. Two paged GETs plus one for key NAMES. No request body is built,
 * no key value is read or printed.
 *
 * The finding is the absence of a boundary rather than the concentration of
 * spend: a single active project holds 100% by construction, and a dominant
 * project in an org that has nine is a different reading with a different
 * repair.
 */
const API = 'https://api.openai.com/v1';
const UNGROUPED = 'ungrouped';

// Whole-token matches only. Substring matching reports "devops-runner" as a
// development key and "provider-proxy" as a production one.
const ENV_WORDS = {
  prod: 'prod', production: 'prod', live: 'prod',
  stage: 'staging', staging: 'staging', preprod: 'staging',
  dev: 'dev', development: 'dev',
  local: 'local', laptop: 'local',
  test: 'test', testing: 'test', qa: 'test',
  ci: 'ci', build: 'ci',
  sandbox: 'sandbox', scratch: 'sandbox', playground: 'sandbox',
};

const FINDINGS = new Set(['no-boundary', 'boundary-unused']);

const money = (n) => Number(n).toLocaleString('en-US',
  { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Projects that can still receive traffic. Pure. Archived drops on either signal. */
export function active(projects) {
  return (projects ?? []).filter((project) => {
    const row = project ?? {};
    if (String(row.status ?? '').trim().toLowerCase() === 'archived') return false;
    if (row.archived_at) return false;
    return true;
  });
}

/** {project_id: dollars} from the cost report. Pure. Null project_id is ungrouped. */
export function spendByProject(buckets) {
  const rows = {};
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const name = String(result?.project_id ?? UNGROUPED);
      const value = Number(result?.amount?.value ?? 0);
      if (!Number.isFinite(value)) continue;
      rows[name] = (rows[name] ?? 0) + value;
    }
  }
  return rows;
}

/** [[project_id, dollars, share]] over real projects only. Pure. */
export function shares(spend) {
  const rows = Object.entries(spend ?? {}).filter(([k]) => k !== UNGROUPED);
  const total = rows.reduce((a, [, v]) => a + v, 0);
  const out = rows.map(([k, v]) => [k, Math.round(v * 100) / 100,
                                    total > 0 ? v / total : 0]);
  out.sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]));
  return out;
}

/** The environment classes named in one identifier. Pure. Whole tokens only. */
export function environments(name) {
  const tokens = String(name ?? '').trim().toLowerCase().split(/[^a-z0-9]+/);
  return new Set(tokens.filter((t) => ENV_WORDS[t]).map((t) => ENV_WORDS[t]));
}

/** Every environment class named across a set of identifiers. Pure. */
export function mixed(names) {
  const found = new Set();
  for (const name of names ?? []) for (const e of environments(name)) found.add(e);
  return found;
}

/** Classify the organization's topology. Pure. Returns [state, detail]. */
export function verdict(activeCount, ranked, minSpend = 1.0, dominant = 0.95) {
  const rows = [...(ranked ?? [])];
  const total = Math.round(rows.reduce((a, r) => a + r[1], 0) * 100) / 100;

  if (activeCount <= 0) {
    return ['no-active-projects',
            'the listing returned no active project at all, which usually means '
            + 'the key could not see them rather than that none exist'];
  }
  if (activeCount === 1) {
    return ['no-boundary',
            `1 active project holds 100% of $${money(total)}. There is no second `
            + 'container to cap, alert on, rate limit or attribute against.'];
  }
  if (total < minSpend) {
    return ['no-spend-yet',
            `${activeCount} active project(s) and $${money(total)} of attributable `
            + 'spend in the window. The boundary exists and nothing has tested it yet.'];
  }

  const [topId, , topShare] = rows[0];
  const quiet = rows.slice(1).filter((r) => r[1] <= 0);
  if (topShare >= dominant && quiet.length === rows.length - 1) {
    return ['boundary-unused',
            `${activeCount} active project(s), and ${topId} carries `
            + `${(topShare * 100).toFixed(0)}% of $${money(total)} while every other `
            + 'project has no spend at all. The containers exist and no traffic '
            + 'routes to them, so the controls on them enforce nothing.'];
  }
  if (topShare >= dominant) {
    return ['concentration-not-topology',
            `${activeCount} active project(s), and ${topId} carries `
            + `${(topShare * 100).toFixed(0)}% of $${money(total)}. This organization `
            + 'has a boundary, so that is a concentration reading rather than a '
            + 'topology one and has a different repair.'];
  }
  return ['separated',
          `${activeCount} active project(s) sharing $${money(total)}, top project at `
          + `${(topShare * 100).toFixed(0)}%`];
}

/** The repair for one topology verdict. Pure. Printed, never performed. */
export function repairLines(state, envs = []) {
  const found = [...envs].sort();
  if (state === 'no-boundary') {
    const lines = [
      'create prod, staging and dev with POST /v1/organization/projects, which is '
      + 'the smallest split that lets any control differ.',
      'give each project its own service account and key, then move traffic one '
      + 'key at a time rather than in one cutover.',
      'spend limits, spend alerts, rate limits, model permissions and data '
      + 'retention are all configured per project and cannot differ until the '
      + 'projects do.',
      'projects can be archived but never deleted, so the names are permanent. '
      + 'Spend ten minutes on them once.',
    ];
    if (found.length) {
      lines.unshift(`the environments already exist in your key names (${found.join(', ')}); `
        + 'they are simply not represented in the platform.');
    }
    return lines;
  }
  if (state === 'boundary-unused') {
    return [
      'the projects are not the problem. Nothing routes to them.',
      'issue a key in the quiet projects and move the traffic that belongs there, '
      + 'then set the limits per project afterwards.',
      'until traffic actually lands in a project, every control configured on it '
      + 'is inert.',
    ];
  }
  if (state === 'concentration-not-topology') {
    return ['do not restructure on this reading. Rank the cost rows by share of '
            + 'total and ask which line item is expensive instead.'];
  }
  return [];
}

/** Unix seconds at midnight UTC, `days` ago. Pure given `now`. */
export function windowStart(days, now = new Date()) {
  const midnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.floor(midnight / 1000) - days * 86400;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
                    + 'organization admin key, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* paged(key, path, params) {
  const q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function* costBuckets(key, params, maxPages = 40) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, '/organization/costs', q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key; a project '
                  + 'key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);

  const projects = [];
  for await (const p of paged(admin, '/organization/projects',
                              { limit: 100, include_archived: 'true' })) {
    projects.push(p);
  }
  const live = active(projects);

  const buckets = [];
  for await (const b of costBuckets(admin, {
    start_time: windowStart(days), bucket_width: '1d',
    limit: Math.min(days, 30), group_by: 'project_id',
  })) buckets.push(b);

  const spend = spendByProject(buckets);
  const ranked = shares(spend);
  const total = Math.round(ranked.reduce((a, r) => a + r[1], 0) * 100) / 100;

  console.log(`${live.length} active project(s), ${projects.length - live.length} `
              + `archived, $${money(total)} in the last ${days} day(s)`);
  if (spend[UNGROUPED]) {
    console.log(`$${money(spend[UNGROUPED])} of cost came back ungrouped and is not `
                + 'counted as a project');
  }

  let envs = new Set();
  if (live.length) {
    const byId = new Map(live.map((p) => [p.id, p]));
    const target = byId.get(ranked[0]?.[0]) ?? live[0];
    const names = [];
    for await (const k of paged(admin, `/organization/projects/${target.id}/api_keys`,
                                { limit: 100, owner_project_access: 'any' })) {
      names.push(k?.name ?? '');
    }
    envs = mixed(names);
    if (envs.size) {
      console.log(`key names in ${target.name ?? target.id} already name ${envs.size} `
                  + `environment(s): ${[...envs].sort().join(', ')}`);
    }
  }

  const [state, detail] = verdict(live.length, ranked);
  console.log(`${state.padEnd(26)} ${detail}`);
  for (const line of repairLines(state, envs)) console.log(`  repair: ${line}`);
  process.exitCode = FINDINGS.has(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The two tests at the top are the same organization read twice, and they are the note. One active project holding everything has to come back as <code>no-boundary</code>; four active projects with one of them at ninety-six per cent has to come back as <code>concentration-not-topology</code>, and must not be a finding, because that org has a boundary and needs the other reading. Next to them: containers that exist and never receive traffic, which is a third state with a third repair; archived projects dropped on either signal; the ungrouped null row that a careless fold turns into one enormous fictional project; and the environment matcher, which has to catch <code>prod-worker</code> and leave <code>devops-runner</code> alone.",
"test_py_file": "test_openai_project_boundary_audit.py",
"test_py": '''from openai_project_boundary_audit import (active, environments, mixed,
                                             repair_lines, shares,
                                             spend_by_project, verdict,
                                             window_start)


def project(pid, name, status="active", archived_at=None):
    return {"id": pid, "name": name, "status": status,
            "archived_at": archived_at}


def cost(pid, value):
    return {"project_id": pid, "amount": {"value": value, "currency": "usd"}}


def buckets(*results):
    return [{"results": list(results)}]


def test_one_active_project_is_the_finding_whatever_the_bill_says():
    # The note in one assertion. There is nothing wrong with the spend; there
    # is nowhere to put a limit, an alert or a model permission.
    live = active([project("proj_a", "Default project"),
                   project("proj_old", "Prototype", status="archived")])
    assert len(live) == 1
    ranked = shares(spend_by_project(buckets(cost("proj_a", 18406.11))))
    state, detail = verdict(len(live), ranked)
    assert state == "no-boundary"
    assert "no second container" in detail
    repairs = repair_lines(state, {"prod", "ci", "local"})
    assert any("archived but never deleted" in line for line in repairs)
    assert any("key names" in line for line in repairs)


def test_a_dominant_project_in_a_split_org_is_the_other_note():
    # Identical arithmetic, opposite conclusion. This organization already has
    # the boundary this note is about, so the finding belongs to the
    # concentration reading and the script says so rather than claiming it.
    ranked = shares(spend_by_project(buckets(
        cost("proj_prod", 96_000.0), cost("proj_stage", 2_400.0),
        cost("proj_dev", 1_100.0), cost("proj_ci", 500.0))))
    state, detail = verdict(4, ranked)
    assert state == "concentration-not-topology"
    assert "different repair" in detail
    assert any("Rank the cost rows" in line for line in repair_lines(state))


def test_projects_that_exist_and_never_receive_traffic():
    ranked = shares(spend_by_project(buckets(
        cost("proj_prod", 9_900.0), cost("proj_stage", 0.0),
        cost("proj_dev", 0.0))))
    state, detail = verdict(3, ranked)
    assert state == "boundary-unused"
    assert "no traffic routes to them" in detail
    assert any("Nothing routes to them" in line for line in repair_lines(state))


def test_archived_projects_are_dropped_on_either_signal():
    rows = [project("a", "live"),
            project("b", "by status", status="archived"),
            project("c", "by timestamp", archived_at=1_700_000_000),
            project("d", "shouty", status="ARCHIVED")]
    assert [p["id"] for p in active(rows)] == ["a"]
    assert active([]) == [] and active(None) == []


def test_an_ungrouped_row_is_never_ranked_as_a_project():
    # The failure this guards: forget group_by, every project_id comes back
    # null, and the fold reports one enormous project in an org that has three.
    spend = spend_by_project(buckets(cost(None, 41_000.0), cost("proj_a", 900.0),
                                     cost("proj_b", 100.0)))
    assert spend["ungrouped"] == 41_000.0
    ranked = shares(spend)
    assert [row[0] for row in ranked] == ["proj_a", "proj_b"]
    assert round(ranked[0][2], 2) == 0.90
    assert verdict(3, ranked)[0] == "separated"


def test_environment_words_match_whole_tokens_only():
    assert environments("prod-worker") == {"prod"}
    assert environments("Local Adam") == {"local"}
    assert environments("ci-fixtures") == {"ci"}
    # The ones a substring test destroys.
    assert environments("devops-runner") == set()
    assert environments("provider-proxy") == set()
    assert environments("protest") == set()
    assert environments(None) == set()
    assert mixed(["prod-worker", "local-adam", "ci-fixtures"]) == \\
        {"prod", "local", "ci"}
    assert mixed([]) == set()


def test_no_spend_and_no_projects_are_never_verdicts():
    assert verdict(0, [])[0] == "no-active-projects"
    state, detail = verdict(3, shares(spend_by_project(buckets(cost("a", 0.2)))))
    assert state == "no-spend-yet"
    assert "nothing has tested it" in detail
    assert repair_lines("separated") == []
    assert spend_by_project(None) == {} and shares(None) == []


def test_the_window_starts_at_midnight_utc():
    import datetime as dt
    now = dt.datetime(2026, 8, 31, 17, 45, 12, tzinfo=dt.timezone.utc)
    assert window_start(30, now) == int(
        dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc).timestamp())
''',
"test_js_file": "openai-project-boundary-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { active, environments, mixed, repairLines, shares, spendByProject,
         verdict, windowStart } from './openai-project-boundary-audit.mjs';

const project = (id, name, status = 'active', archivedAt = null) =>
  ({ id, name, status, archived_at: archivedAt });

const cost = (projectId, value) =>
  ({ project_id: projectId, amount: { value, currency: 'usd' } });

const buckets = (...results) => [{ results }];

test('one active project is the finding whatever the bill says', () => {
  const live = active([project('proj_a', 'Default project'),
                       project('proj_old', 'Prototype', 'archived')]);
  assert.equal(live.length, 1);
  const ranked = shares(spendByProject(buckets(cost('proj_a', 18406.11))));
  const [state, detail] = verdict(live.length, ranked);
  assert.equal(state, 'no-boundary');
  assert.match(detail, /no second container/);
  const repairs = repairLines(state, new Set(['prod', 'ci', 'local']));
  assert.ok(repairs.some((l) => l.includes('archived but never deleted')));
  assert.ok(repairs.some((l) => l.includes('key names')));
});

test('a dominant project in a split org is the other note', () => {
  const ranked = shares(spendByProject(buckets(
    cost('proj_prod', 96000), cost('proj_stage', 2400),
    cost('proj_dev', 1100), cost('proj_ci', 500))));
  const [state, detail] = verdict(4, ranked);
  assert.equal(state, 'concentration-not-topology');
  assert.match(detail, /different repair/);
  assert.ok(repairLines(state).some((l) => l.includes('Rank the cost rows')));
});

test('projects that exist and never receive traffic', () => {
  const ranked = shares(spendByProject(buckets(
    cost('proj_prod', 9900), cost('proj_stage', 0), cost('proj_dev', 0))));
  const [state, detail] = verdict(3, ranked);
  assert.equal(state, 'boundary-unused');
  assert.match(detail, /no traffic routes to them/);
});

test('archived projects are dropped on either signal', () => {
  const rows = [project('a', 'live'), project('b', 'by status', 'archived'),
                project('c', 'by timestamp', 'active', 1700000000),
                project('d', 'shouty', 'ARCHIVED')];
  assert.deepEqual(active(rows).map((p) => p.id), ['a']);
  assert.deepEqual(active(null), []);
});

test('an ungrouped row is never ranked as a project', () => {
  const spend = spendByProject(buckets(cost(null, 41000), cost('proj_a', 900),
                                       cost('proj_b', 100)));
  assert.equal(spend.ungrouped, 41000);
  const ranked = shares(spend);
  assert.deepEqual(ranked.map((r) => r[0]), ['proj_a', 'proj_b']);
  assert.equal(Math.round(ranked[0][2] * 100) / 100, 0.9);
  assert.equal(verdict(3, ranked)[0], 'separated');
});

test('environment words match whole tokens only', () => {
  assert.deepEqual([...environments('prod-worker')], ['prod']);
  assert.deepEqual([...environments('Local Adam')], ['local']);
  assert.deepEqual([...environments('devops-runner')], []);
  assert.deepEqual([...environments('provider-proxy')], []);
  assert.deepEqual([...environments('protest')], []);
  assert.deepEqual([...environments(null)], []);
  assert.deepEqual([...mixed(['prod-worker', 'local-adam', 'ci-fixtures'])].sort(),
                   ['ci', 'local', 'prod']);
});

test('no spend and no projects are never verdicts', () => {
  assert.equal(verdict(0, [])[0], 'no-active-projects');
  const [state, detail] = verdict(3, shares(spendByProject(buckets(cost('a', 0.2)))));
  assert.equal(state, 'no-spend-yet');
  assert.match(detail, /nothing has tested it/);
  assert.deepEqual(repairLines('separated'), []);
  assert.deepEqual(spendByProject(null), {});
  assert.deepEqual(shares(null), []);
});

test('the window starts at midnight utc', () => {
  assert.equal(windowStart(30, new Date('2026-08-31T17:45:12Z')),
               Date.UTC(2026, 7, 1) / 1000);
});
''',
"faq": [
 ("How is this different from finding out that one project dominates the bill?",
  "By what it counts. The concentration reading ranks cost rows by share of total and tells you which line item or project is expensive, and it is a useful reading in an organization that has several projects, because you can act inside the structure you already have: cap that project, move that workload, change that model. In a single-project organization the top row is a hundred per cent by construction, so the ranking has told you nothing you did not know, and the repair is not rebalancing but creating containers that do not exist yet. The script counts active projects before it looks at any money, and when it finds a dominant project in an org that has a boundary it names the concentration reading and refuses to report a topology fault."),
 ("What actually breaks with one project? The bill is the same either way.",
  "The bill is the same. The controls are not. Spend limits, spend alerts, rate limits, model permissions, hosted tool permissions and data retention are all configured per project, so with one project every one of them is an all-or-nothing switch over your entire organization. You cannot cap the experiments without capping production, cannot throttle the evaluation run without throttling the customer path, and cannot stop a prototype reaching an expensive model without stopping the product reaching it too. Attribution is the symptom people notice; enforcement is what is missing."),
 ("We created staging and dev months ago. Why is the script still complaining?",
  "Because nothing routes to them. That is a separate state with a separate name in the output, boundary-unused, and it comes with a different repair: the containers are fine and the traffic is the problem. A project with no keys and no spend enforces nothing at all, and every limit configured on it is inert until a request actually arrives there. This is common after a security review, where the projects get created as an artefact of the review and the key migration never follows."),
 ("Does the script read my API keys to work out which environments exist?",
  "It reads key names, never key values, and the platform would not return a value anyway. The name read is corroboration only and never changes the verdict: when one project holds keys called prod-worker, local-adam and ci-fixtures, the environments already exist as a fact about how people work and are simply not represented in the platform. Environment words are matched as whole tokens after splitting on punctuation, so devops-runner is a team name rather than a development key, and provider-proxy is not production."),
 ("Is there an Anthropic version of this?",
  "The equivalent container is a workspace, and the same reasoning applies: one workspace means no boundary to attribute or rate limit against. The reason it is not this script is that Anthropic's topology has a second problem OpenAI does not have at all, the default workspace, whose cost reports with a null workspace id and which cannot carry a rate-limit override even if you want one. That is the subject of the sibling note rather than a footnote to this one."),
],
"related": [REL_DOMINATES, REL_SPEND_LIMIT, REL_NULL_WS],
"citations": [CITE_OA_PROJECTS, CITE_OA_PROJECTS_HELP, CITE_OA_USAGE,
              CITE_OA_ADMIN_GUIDE],
},
{
"slug": "default-workspace-cost-unattributable",
"title": "Cost lands in the default workspace and cannot be charged back",
"description": "Rows with a null workspace_id are two different causes. One is a list of API keys you can move; the other is Console playground traffic with no key at all.",
"h1": "Cost lands in the default workspace and cannot be charged back",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic cost report workspace_id null",
             "claude default workspace cost attribution",
             "anthropic admin api key scope workspace",
             "claude usage report api_key_id null playground",
             "anthropic chargeback by workspace"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY, an Admin API key (sk-ant-admin) that can be provisioned read-only, because every /v1/organizations/* path rejects a workspace key.",
"lead": "The chargeback spreadsheet has one row that never shrinks. Four workspaces are named after the teams that own them and add up to about sixty per cent of the bill; the rest arrives under a heading somebody typed once as <em>Unallocated</em> and has been carrying forward every month since. It is not a rounding error and it is not fraud. It is the default workspace, and it is reported as <code>null</code>, which is not a workspace you can go and talk to.",
"short_answer": """<p>Three GETs with an <strong>Admin API key</strong>. <code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=workspace_id</code> sizes the bucket: sum <code>amount</code> where <code>workspace_id</code> is <code>null</code> and take its share. Usage and costs in the organization's default workspace report a null workspace id, so that share is the part of your bill with no team on it.</p>
<p>Then split the null bucket into its two causes, because they are not the same problem. <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=api_key_id&amp;group_by[]=workspace_id</code> returns rows where <code>api_key_id</code> is also null &mdash; that is <strong>Console playground</strong> traffic, which is not associated with any API key at all and therefore cannot be moved anywhere by changing a key. Everything else in the null bucket came from a key.</p>
<p>Finally, name those keys. <code>GET /v1/organizations/api_keys?limit=100</code>, paged on <code>has_more</code> and <code>last_id</code>. Read <code>scope.type</code>: an <strong>organization</strong>-scoped key is not bound to a workspace at all, and a workspace-scoped key whose workspace id does not resolve is bound to the default one. Those keys are the movable half of the finding, and the output is a list of them with the named workspace each ought to move to.</p>
<p>The default workspace also cannot carry a rate-limit override. So this bucket is not only the part of the bill nobody owns, it is the part that cannot be bounded below the organization limit either.</p>""",
"problem": """<p><code>null</code> means "cannot attribute" twice over in these reports, and the two meanings have different repairs. Cost and usage in the default workspace come back with <code>workspace_id: null</code> because the default workspace has no id to report. Usage from the Console playground comes back with <code>api_key_id: null</code> because no key was involved in the request. A chargeback report that adds those together produces one large unallocated number and no next action.</p>
<p>The default workspace fills up because it is the path of least resistance and nothing pushes back. Every user whose org role permits API access can use it, in addition to whatever workspaces they were explicitly added to, and so can every service account. A key created in a hurry lands there. A key created before the workspace structure existed stays there. An organization-scoped key was never in a workspace to begin with.</p>
<p>And it is the one workspace you cannot put a guard on. Rate-limit overrides are configured per workspace and the default workspace cannot have them, so traffic there is unbounded relative to the organization limit &mdash; it can consume the whole org allocation and starve the named workspaces that are being careful.</p>""",
"why": """<p><strong>This is the fixable cousin of a question that has no answer, and confusing them wastes a quarter.</strong> A published note explains why per-customer cost is unknowable: your tenant is nowhere in the attribution chain, the chain runs from request to key to key owner, and nothing you send can change that. This is a smaller and much better-behaved problem. The null bucket here decomposes into a finite list of API keys, each with an id and a name, each of which can be recreated inside a named workspace. There is a repair, it is boring, and it works.</p>
<p><strong>Splitting the bucket is the whole value of the script, because half of it has no repair.</strong> Playground traffic carries no key. You cannot move it, rescope it, or attribute it, and an audit that reports "move these keys and the unallocated row goes away" is wrong in exactly the proportion that the playground contributed. The script reports the split first and grades the finding on it: when the playground is the majority of the null usage, the state says so and the repair is a conversation about where people run experiments, not a key migration.</p>
<p><strong><code>scope.type</code> is the field, and the deprecated top-level <code>workspace_id</code> is the trap.</strong> For a key bound to the default workspace the deprecated top-level field is null while <code>scope.workspace_id</code> carries the real id, so a reader that consults only one of them will misclassify keys in both directions. The script resolves the scope id first, falls back to the deprecated field, and refuses to classify a scope type it does not recognise rather than guessing that an unknown scope is harmless.</p>
<p><strong>An unallocated share is not automatically a finding.</strong> Small organizations run everything in the default workspace deliberately and correctly; a hundred per cent null share in an org with one workspace is a topology fact, not an attribution failure, and it belongs to <a href="/llm/no-prod-dev-project-separation/">the boundary note</a>. This script grades the share against a threshold, states the dollar figure behind it, and says nothing at all when the window has no spend in it.</p>""",
"steps": [
 {"h": "Use an Admin API key, provisioned read-only",
  "body": """<p>Every <code>/v1/organizations/*</code> path rejects a workspace key. An Admin key with read scopes covers all three calls, and there is no fourth.</p>"""},
 {"h": "Size the null bucket on the cost report",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;limit=31&amp;group_by[]=workspace_id</code>. <code>amount</code> arrives as a decimal <em>string</em>, so parse it rather than summing raw values. The share of total with a null <code>workspace_id</code> is the number the chargeback spreadsheet has been carrying forward.</p>"""},
 {"h": "Split it into playground traffic and key traffic",
  "body": """<p><code>group_by[]=api_key_id&amp;group_by[]=workspace_id</code> on the messages usage report. A row with a null <code>api_key_id</code> is Console playground usage and has no key to move; classify that first, because a playground request made in the default workspace has both fields null and would otherwise be counted twice.</p>"""},
 {"h": "Name the keys whose scope explains the rest",
  "body": """<p><code>GET /v1/organizations/api_keys?limit=100</code>. Keep <code>status == "active"</code>. Resolve each key's workspace as <code>scope.workspace_id</code> first and the deprecated top-level <code>workspace_id</code> second; a key that resolves to nothing is in the default workspace, and a key whose <code>scope.type</code> is <code>organization</code> was never in a workspace at all.</p>"""},
 {"h": "Print the movable list, and say what will not move",
  "body": """<p>Per key: id, name, scope, and the fact that it lands in the default workspace. The repair is to recreate the key inside a named workspace and cut over &mdash; and the output states the playground share explicitly, because that part of the bucket will still be there afterwards.</p>"""},
],
"verify": """<p>Move one key, wait a day, and re-read the same window. The null share should fall by roughly that key's volume and no more. If it does not fall at all, the remainder is playground traffic or a key that was deleted before the window closed, and the script's split already told you which to expect.</p>
<pre><code class="language-bash">python3 anthropic_default_workspace_cost.py --days 30
# $41,208.55 in the last 30 day(s) across 5 workspace row(s)
# unattributed: $15,706.09 (38% of spend) has a null workspace_id
# usage split of the null bucket: 91% from API keys, 9% Console playground
# movable-keys      38% of $41,208.55 has no workspace on it, and 4 active key(s)
#                   land in the default workspace or carry organization scope.
#   apikey_01aa  nightly-summaries      organization-scoped
#   apikey_01bb  ingest-worker          default-workspace
#   apikey_01cc  eval-runner            default-workspace
#   apikey_01dd  adam-scratch           default-workspace
#   repair: recreate each key inside a named workspace and cut over, key by key
#   repair: 9% of the null usage is Console playground and no key move touches it
#   repair: the default workspace cannot carry a rate-limit override at all
# 1 finding(s)</code></pre>""",
"code_intro": "Three paged GETs and seven pure functions. The decimal-string amount parser; the cost fold, which keeps the null workspace under an explicit sentinel rather than dropping it; the token weigher, which has to walk the nested <code>cache_creation</code> object; the usage split, which classifies a null <code>api_key_id</code> before a null <code>workspace_id</code> so a playground request in the default workspace is counted once; the scope resolver, which prefers <code>scope.workspace_id</code> over the deprecated top-level field and refuses to classify an unknown scope type; the verdict, which grades the movable half against the playground half; and the repair lines, which always state the part that will not move.",
"py_file": "anthropic_default_workspace_cost.py",
"py": '''"""Find Anthropic cost that reports no workspace, and the keys behind it.

Read only. Three paged GETs against /v1/organizations/* with an Admin API key.
Nothing is sent to /v1/messages and no request body is constructed.

The unallocated bucket has two causes and only one of them has a repair. Cost
and usage in the organization's default workspace report workspace_id: null,
and Console playground usage reports api_key_id: null because no key was
involved. Keys can be moved; playground traffic cannot, so the script sizes
both before it recommends anything.

Key values are never read or printed. The key listing is used for ids, names
and scope only.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_default_workspace_cost")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The default workspace has no id to report, so the reports return null for it.
# Kept under an explicit sentinel rather than dropped, because dropping it is
# how a chargeback report silently stops adding up to the invoice.
DEFAULT_WS = "(default workspace)"

PLAYGROUND = "console-playground"
DEFAULT_KEYED = "default-workspace"
ATTRIBUTED = "attributed"

ORG_SCOPED = "organization-scoped"
NAMED = "named-workspace"
UNKNOWN_SCOPE = "unknown-scope"

MOVABLE = (ORG_SCOPED, DEFAULT_KEYED)
FINDINGS = ("movable-keys", "console-playground", "unattributable-no-key-to-move")


def amount(row):
    """One cost row's amount as a float. Pure.

    The cost report returns amount as a decimal STRING. Summing the raw values
    concatenates them, which produces a number large enough that nobody reads
    it as money and small enough that nobody notices it is text.
    """
    try:
        return float((row or {}).get("amount") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def cost_by_workspace(pages):
    """{workspace_id: dollars} from the cost report. Pure. Null uses a sentinel."""
    rows = {}
    for page in pages or []:
        for bucket in (page or {}).get("data") or []:
            for result in (bucket or {}).get("results") or []:
                key = (result or {}).get("workspace_id") or DEFAULT_WS
                rows[str(key)] = rows.get(str(key), 0.0) + amount(result)
    return rows


def unattributed_share(rows):
    """The null workspace's share of total cost. Pure. 0.0 when empty."""
    data = rows or {}
    total = sum(data.values())
    if total <= 0:
        return 0.0
    return float(data.get(DEFAULT_WS, 0.0)) / total


def weigh(result):
    """Total billed tokens on one usage row. Pure.

    cache_creation is an object rather than a scalar, so a reader that treats
    it as an int drops every cached write out of the weight.
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


def usage_split(pages):
    """{cause: tokens} across the usage report. Pure.

    A null api_key_id is classified BEFORE a null workspace_id. A playground
    request made in the default workspace has both fields null, and counting it
    in both buckets inflates the movable half of the finding, which is the half
    the script is about to recommend work on.
    """
    out = {PLAYGROUND: 0, DEFAULT_KEYED: 0, ATTRIBUTED: 0}
    for page in pages or []:
        for bucket in (page or {}).get("data") or []:
            for result in (bucket or {}).get("results") or []:
                row = result or {}
                tokens = weigh(row)
                if not row.get("api_key_id"):
                    out[PLAYGROUND] += tokens
                elif not row.get("workspace_id"):
                    out[DEFAULT_KEYED] += tokens
                else:
                    out[ATTRIBUTED] += tokens
    return out


def playground_share(split):
    """Playground share of the null bucket only. Pure. 0.0 when the bucket is empty."""
    data = split or {}
    null_bucket = int(data.get(PLAYGROUND, 0)) + int(data.get(DEFAULT_KEYED, 0))
    if null_bucket <= 0:
        return 0.0
    return int(data.get(PLAYGROUND, 0)) / float(null_bucket)


def key_attribution(key):
    """Where one API key's traffic lands. Pure. Returns (kind, workspace_id).

    scope.workspace_id is read before the deprecated top-level workspace_id,
    which is null for keys bound to the default workspace. An unrecognised
    scope type is returned as unknown rather than assumed harmless.
    """
    row = key or {}
    scope = row.get("scope") or {}
    kind = str(scope.get("type") or "").strip().lower()
    workspace = scope.get("workspace_id") or row.get("workspace_id")

    if kind == "organization":
        return (ORG_SCOPED, None)
    if kind and kind != "workspace":
        return (UNKNOWN_SCOPE, workspace and str(workspace) or None)
    if workspace:
        return (NAMED, str(workspace))
    return (DEFAULT_KEYED, None)


def fold_keys(keys):
    """{kind: [{id, name, workspace_id}]} over ACTIVE keys only. Pure.

    An inactive key cannot be the cause of spend in the window and must not
    appear in a migration list somebody is going to work through by hand.
    """
    out = {ORG_SCOPED: [], DEFAULT_KEYED: [], NAMED: [], UNKNOWN_SCOPE: []}
    for key in keys or []:
        row = key or {}
        if str(row.get("status") or "active").strip().lower() != "active":
            continue
        kind, workspace = key_attribution(row)
        out[kind].append({"id": str(row.get("id") or "unknown"),
                          "name": str(row.get("name") or "unnamed"),
                          "workspace_id": workspace})
    return out


def verdict(share, total, folded, split, min_spend=1.0, min_share=0.10,
            playground_max=0.50):
    """Classify the unallocated bucket. Pure. Returns (state, detail)."""
    movable = sum(len(folded.get(kind) or []) for kind in MOVABLE)
    if total < min_spend:
        return ("no-spend-yet",
                "$%s of cost in the window, too little to conclude anything"
                % format(total, ",.2f"))
    if share < min_share:
        return ("attributed",
                "%.0f%% of $%s has a null workspace_id, under the threshold"
                % (share * 100, format(total, ",.2f")))

    plays = playground_share(split)
    if plays > playground_max:
        return ("console-playground",
                "%.0f%% of $%s has no workspace on it, and %.0f%% of that usage "
                "carries no api_key_id either. That is Console playground "
                "traffic, and no key can be moved to make it land anywhere."
                % (share * 100, format(total, ",.2f"), plays * 100))
    if movable:
        return ("movable-keys",
                "%.0f%% of $%s has no workspace on it, and %d active key(s) "
                "land in the default workspace or carry organization scope."
                % (share * 100, format(total, ",.2f"), movable))
    return ("unattributable-no-key-to-move",
            "%.0f%% of $%s has no workspace on it, and every active key "
            "resolves to a named workspace. The spend came from a key that has "
            "since been deleted, or from the playground."
            % (share * 100, format(total, ",.2f")))


def repair_lines(state, folded, split):
    """The repair for one verdict. Pure. Printed, never performed."""
    plays = playground_share(split)
    if state == "movable-keys":
        lines = ["recreate each key inside a named workspace and cut over, key "
                 "by key. A key's workspace is fixed when it is created."]
        if folded.get(ORG_SCOPED):
            lines.append("%d of them carry organization scope, which is not a "
                         "workspace at all: those cannot be reassigned, only "
                         "replaced." % len(folded[ORG_SCOPED]))
        if plays > 0:
            lines.append("%.0f%% of the null usage is Console playground and no "
                         "key move touches it." % (plays * 100))
        lines.append("the default workspace cannot carry a rate-limit override "
                     "at all, so this traffic is also unbounded relative to the "
                     "organization limit.")
        return lines
    if state == "console-playground":
        return [
            "there is no key migration here. The requests carried no key.",
            "decide where experiments should run: a named workspace with its "
            "own key, or an accepted line in the chargeback report.",
            "the default workspace cannot carry a rate-limit override, so "
            "playground traffic competes with production for the org limit.",
        ]
    if state == "unattributable-no-key-to-move":
        return [
            "do not open a migration ticket. Every active key already resolves "
            "to a named workspace.",
            "the spend predates a key deletion or came from the playground; "
            "narrow the window and read the daily buckets to see which.",
        ]
    return []


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def report_pages(session, path, params):
    """Walk a usage or cost report on next_page."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def listing(session, path, params):
    """Walk an Admin list endpoint on after_id."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        for item in page.get("data") or []:
            yield item
        if not page.get("has_more") or not page.get("last_id"):
            return
        params["after_id"] = page["last_id"]


def window_start(days, now=None):
    """Floor to midnight UTC: starting_at must sit on a bucket boundary."""
    now = now or dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily buckets to read (default 30)")
    ap.add_argument("--min-share", type=float, default=0.10,
                    help="null share below which nothing is reported")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})
    start = window_start(args.days)

    costs = cost_by_workspace(report_pages(
        s, "/organizations/cost_report",
        {"starting_at": start, "limit": min(args.days + 1, 31),
         "group_by[]": ["workspace_id"]}))
    total = round(sum(costs.values()), 2)
    share = unattributed_share(costs)

    split = usage_split(report_pages(
        s, "/organizations/usage_report/messages",
        {"starting_at": start, "bucket_width": "1d",
         "limit": min(args.days + 1, 31),
         "group_by[]": ["api_key_id", "workspace_id"]}))

    folded = fold_keys(listing(s, "/organizations/api_keys", {"limit": 100}))

    log.info("$%s in the last %d day(s) across %d workspace row(s)",
             format(total, ",.2f"), args.days, len(costs))
    log.info("unattributed: $%s (%.0f%% of spend) has a null workspace_id",
             format(costs.get(DEFAULT_WS, 0.0), ",.2f"), share * 100)
    plays = playground_share(split)
    log.info("usage split of the null bucket: %.0f%% from API keys, %.0f%% "
             "Console playground", (1 - plays) * 100, plays * 100)

    state, detail = verdict(share, total, folded, split, min_share=args.min_share)
    if state not in FINDINGS:
        log.info("%-18s %s", state, detail)
        return 0

    log.warning("%-18s %s", state, detail)
    for kind in MOVABLE:
        for key in folded.get(kind) or []:
            log.warning("  %-12s %-22s %s", key["id"], key["name"], kind)
    for line in repair_lines(state, folded, split):
        log.warning("  repair: %s", line)
    log.info("1 finding(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-default-workspace-cost.mjs",
"js": '''/**
 * Find Anthropic cost that reports no workspace, and the keys behind it.
 *
 * Read only. Three paged GETs against /v1/organizations/* with an Admin API
 * key. No request body is constructed and no key value is read or printed.
 *
 * The unallocated bucket has two causes and only one has a repair: keys that
 * land in the default workspace can be moved, and Console playground traffic
 * carries no key at all.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

const DEFAULT_WS = '(default workspace)';

const PLAYGROUND = 'console-playground';
const DEFAULT_KEYED = 'default-workspace';
const ATTRIBUTED = 'attributed';

const ORG_SCOPED = 'organization-scoped';
const NAMED = 'named-workspace';
const UNKNOWN_SCOPE = 'unknown-scope';

const MOVABLE = [ORG_SCOPED, DEFAULT_KEYED];
const FINDINGS = new Set(['movable-keys', 'console-playground',
                          'unattributable-no-key-to-move']);

const money = (n) => Number(n).toLocaleString('en-US',
  { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** One cost row's amount as a number. Pure. amount is a decimal STRING. */
export function amount(row) {
  const value = Number(row?.amount ?? 0);
  return Number.isFinite(value) ? value : 0;
}

/** {workspace_id: dollars} from the cost report. Pure. Null uses a sentinel. */
export function costByWorkspace(pages) {
  const rows = {};
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      for (const result of bucket?.results ?? []) {
        const key = String(result?.workspace_id ?? DEFAULT_WS);
        rows[key] = (rows[key] ?? 0) + amount(result);
      }
    }
  }
  return rows;
}

/** The null workspace's share of total cost. Pure. */
export function unattributedShare(rows) {
  const data = rows ?? {};
  const total = Object.values(data).reduce((a, v) => a + v, 0);
  if (total <= 0) return 0;
  return (data[DEFAULT_WS] ?? 0) / total;
}

/** Total billed tokens on one usage row. Pure. cache_creation is an object. */
export function weigh(result) {
  const row = result ?? {};
  let total = 0;
  for (const field of ['uncached_input_tokens', 'cache_read_input_tokens',
                       'output_tokens']) {
    const value = Number(row[field] ?? 0);
    if (Number.isFinite(value)) total += value;
  }
  const creation = row.cache_creation;
  if (creation && typeof creation === 'object' && !Array.isArray(creation)) {
    for (const value of Object.values(creation)) {
      const n = Number(value ?? 0);
      if (Number.isFinite(n)) total += n;
    }
  }
  return total;
}

/** {cause: tokens}. Pure. A null api_key_id is classified before a null workspace. */
export function usageSplit(pages) {
  const out = { [PLAYGROUND]: 0, [DEFAULT_KEYED]: 0, [ATTRIBUTED]: 0 };
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      for (const result of bucket?.results ?? []) {
        const tokens = weigh(result);
        if (!result?.api_key_id) out[PLAYGROUND] += tokens;
        else if (!result?.workspace_id) out[DEFAULT_KEYED] += tokens;
        else out[ATTRIBUTED] += tokens;
      }
    }
  }
  return out;
}

/** Playground share of the null bucket only. Pure. */
export function playgroundShare(split) {
  const data = split ?? {};
  const bucket = (data[PLAYGROUND] ?? 0) + (data[DEFAULT_KEYED] ?? 0);
  if (bucket <= 0) return 0;
  return (data[PLAYGROUND] ?? 0) / bucket;
}

/** Where one API key's traffic lands. Pure. Returns [kind, workspaceId]. */
export function keyAttribution(key) {
  const row = key ?? {};
  const scope = row.scope ?? {};
  const kind = String(scope.type ?? '').trim().toLowerCase();
  const workspace = scope.workspace_id ?? row.workspace_id ?? null;

  if (kind === 'organization') return [ORG_SCOPED, null];
  if (kind && kind !== 'workspace') {
    return [UNKNOWN_SCOPE, workspace ? String(workspace) : null];
  }
  if (workspace) return [NAMED, String(workspace)];
  return [DEFAULT_KEYED, null];
}

/** {kind: [{id, name, workspace_id}]} over ACTIVE keys only. Pure. */
export function foldKeys(keys) {
  const out = { [ORG_SCOPED]: [], [DEFAULT_KEYED]: [], [NAMED]: [],
                [UNKNOWN_SCOPE]: [] };
  for (const key of keys ?? []) {
    const row = key ?? {};
    if (String(row.status ?? 'active').trim().toLowerCase() !== 'active') continue;
    const [kind, workspace] = keyAttribution(row);
    out[kind].push({ id: String(row.id ?? 'unknown'),
                     name: String(row.name ?? 'unnamed'),
                     workspace_id: workspace });
  }
  return out;
}

/** Classify the unallocated bucket. Pure. Returns [state, detail]. */
export function verdict(share, total, folded, split, minSpend = 1.0,
                        minShare = 0.10, playgroundMax = 0.50) {
  const movable = MOVABLE.reduce((a, kind) => a + (folded?.[kind]?.length ?? 0), 0);
  if (total < minSpend) {
    return ['no-spend-yet',
            `$${money(total)} of cost in the window, too little to conclude anything`];
  }
  if (share < minShare) {
    return ['attributed',
            `${(share * 100).toFixed(0)}% of $${money(total)} has a null `
            + 'workspace_id, under the threshold'];
  }
  const plays = playgroundShare(split);
  if (plays > playgroundMax) {
    return ['console-playground',
            `${(share * 100).toFixed(0)}% of $${money(total)} has no workspace on it, `
            + `and ${(plays * 100).toFixed(0)}% of that usage carries no api_key_id `
            + 'either. That is Console playground traffic, and no key can be moved '
            + 'to make it land anywhere.'];
  }
  if (movable) {
    return ['movable-keys',
            `${(share * 100).toFixed(0)}% of $${money(total)} has no workspace on it, `
            + `and ${movable} active key(s) land in the default workspace or carry `
            + 'organization scope.'];
  }
  return ['unattributable-no-key-to-move',
          `${(share * 100).toFixed(0)}% of $${money(total)} has no workspace on it, `
          + 'and every active key resolves to a named workspace. The spend came from '
          + 'a key that has since been deleted, or from the playground.'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, folded, split) {
  const plays = playgroundShare(split);
  if (state === 'movable-keys') {
    const lines = ['recreate each key inside a named workspace and cut over, key by '
                   + "key. A key's workspace is fixed when it is created."];
    if (folded?.[ORG_SCOPED]?.length) {
      lines.push(`${folded[ORG_SCOPED].length} of them carry organization scope, `
        + 'which is not a workspace at all: those cannot be reassigned, only replaced.');
    }
    if (plays > 0) {
      lines.push(`${(plays * 100).toFixed(0)}% of the null usage is Console `
        + 'playground and no key move touches it.');
    }
    lines.push('the default workspace cannot carry a rate-limit override at all, so '
      + 'this traffic is also unbounded relative to the organization limit.');
    return lines;
  }
  if (state === 'console-playground') {
    return [
      'there is no key migration here. The requests carried no key.',
      'decide where experiments should run: a named workspace with its own key, or '
      + 'an accepted line in the chargeback report.',
      'the default workspace cannot carry a rate-limit override, so playground '
      + 'traffic competes with production for the org limit.',
    ];
  }
  if (state === 'unattributable-no-key-to-move') {
    return [
      'do not open a migration ticket. Every active key already resolves to a '
      + 'named workspace.',
      'the spend predates a key deletion or came from the playground; narrow the '
      + 'window and read the daily buckets to see which.',
    ];
  }
  return [];
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. Pure given now. */
export function windowStart(days, now = new Date()) {
  const midnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return `${new Date(midnight - days * 86400000).toISOString().slice(0, 19)}Z`;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const one of v) url.searchParams.append(k, String(one));
    else url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from Anthropic: /v1/organizations/* needs an Admin `
                    + 'API key (sk-ant-admin...), not a workspace key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function reportPages(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
    out.push(page);
    if (!page.has_more || !page.next_page) return out;
    q.page = page.next_page;
  }
}

async function listing(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.last_id) return out;
    q.after_id = page.last_id;
  }
}

async function main() {
  const admin = process.env.ANTHROPIC_ADMIN_KEY;
  if (!admin) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); '
                  + 'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const start = windowStart(days);
  const limit = Math.min(days + 1, 31);

  const costs = costByWorkspace(await reportPages(admin, '/organizations/cost_report',
    { starting_at: start, limit, 'group_by[]': ['workspace_id'] }));
  const total = Math.round(Object.values(costs).reduce((a, v) => a + v, 0) * 100) / 100;
  const share = unattributedShare(costs);

  const split = usageSplit(await reportPages(admin,
    '/organizations/usage_report/messages',
    { starting_at: start, bucket_width: '1d', limit,
      'group_by[]': ['api_key_id', 'workspace_id'] }));

  const folded = foldKeys(await listing(admin, '/organizations/api_keys', { limit: 100 }));

  console.log(`$${money(total)} in the last ${days} day(s) across `
              + `${Object.keys(costs).length} workspace row(s)`);
  console.log(`unattributed: $${money(costs[DEFAULT_WS] ?? 0)} `
              + `(${(share * 100).toFixed(0)}% of spend) has a null workspace_id`);
  const plays = playgroundShare(split);
  console.log(`usage split of the null bucket: ${((1 - plays) * 100).toFixed(0)}% from `
              + `API keys, ${(plays * 100).toFixed(0)}% Console playground`);

  const [state, detail] = verdict(share, total, folded, split);
  console.log(`${state.padEnd(18)} ${detail}`);
  if (FINDINGS.has(state)) {
    for (const kind of MOVABLE) {
      for (const key of folded[kind] ?? []) {
        console.log(`  ${key.id.padEnd(12)} ${key.name.padEnd(22)} ${kind}`);
      }
    }
    for (const line of repairLines(state, folded, split)) {
      console.log(`  repair: ${line}`);
    }
  }
  process.exitCode = FINDINGS.has(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note: a thirty-eight per cent null bucket that is ninety per cent keys, four of them named, and a repair that still states the playground remainder out loud. The second is the same null share with the usage split inverted, and it has to come back as a different state with no migration in it, because those requests never carried a key. After that: the scope resolver, which has to prefer <code>scope.workspace_id</code> over the deprecated top-level field and refuse to classify a scope type it does not recognise; the classification order that stops a playground request in the default workspace being counted twice; the decimal-string amount that a naive sum concatenates; inactive keys, which must never reach a list somebody is going to work through by hand; and the floor below which no share is a finding.",
"test_py_file": "test_anthropic_default_workspace_cost.py",
"test_py": '''from anthropic_default_workspace_cost import (amount, cost_by_workspace,
                                                fold_keys, key_attribution,
                                                playground_share, repair_lines,
                                                unattributed_share, usage_split,
                                                verdict, weigh)


def cost(workspace_id, value):
    return {"workspace_id": workspace_id, "amount": value, "currency": "USD"}


def use(api_key_id, workspace_id, tokens):
    return {"api_key_id": api_key_id, "workspace_id": workspace_id,
            "uncached_input_tokens": tokens}


def page(results):
    return {"data": [{"results": list(results)}], "has_more": False}


def key(kid, name, scope_type="workspace", scope_ws=None, top_ws=None,
        status="active"):
    return {"id": kid, "name": name, "status": status,
            "scope": {"type": scope_type, "workspace_id": scope_ws},
            "workspace_id": top_ws}


KEYS = [
    key("apikey_01aa", "nightly-summaries", scope_type="organization"),
    key("apikey_01bb", "ingest-worker"),
    key("apikey_01cc", "eval-runner"),
    key("apikey_01dd", "adam-scratch"),
    key("apikey_01ee", "billing-team", scope_ws="wrkspc_01"),
]


def test_the_unallocated_bucket_is_two_causes_and_one_of_them_moves():
    # The note in one assertion. A large null share, mostly from keys, with
    # four named keys to move and a playground remainder that will not budge.
    costs = cost_by_workspace([page([cost(None, "15706.09"),
                                     cost("wrkspc_01", "17000.00"),
                                     cost("wrkspc_02", "8502.46")])])
    total = round(sum(costs.values()), 2)
    share = unattributed_share(costs)
    assert round(share, 2) == 0.38
    split = usage_split([page([use(None, None, 900_000),
                               use("apikey_01bb", None, 9_100_000),
                               use("apikey_01ee", "wrkspc_01", 40_000_000)])])
    folded = fold_keys(KEYS)
    state, detail = verdict(share, total, folded, split)
    assert state == "movable-keys"
    assert "4 active key(s)" in detail
    repairs = repair_lines(state, folded, split)
    assert any("organization scope" in line for line in repairs)
    assert any("Console playground" in line for line in repairs)
    assert any("rate-limit override" in line for line in repairs)


def test_playground_traffic_has_no_key_to_move():
    # Identical cost shape, inverted usage split. Nothing about the keys
    # changed and the correct answer did: this bucket has no migration in it.
    costs = cost_by_workspace([page([cost(None, "15706.09"),
                                     cost("wrkspc_01", "25502.46")])])
    split = usage_split([page([use(None, None, 9_000_000),
                               use("apikey_01bb", None, 1_000_000)])])
    assert round(playground_share(split), 2) == 0.90
    state, detail = verdict(unattributed_share(costs),
                            round(sum(costs.values()), 2), fold_keys(KEYS), split)
    assert state == "console-playground"
    assert "no key can be moved" in detail
    assert not any("recreate each key" in line
                   for line in repair_lines(state, fold_keys(KEYS), split))


def test_the_scope_resolver_prefers_scope_over_the_deprecated_field():
    assert key_attribution(key("k", "n", scope_type="organization")) == \\
        ("organization-scoped", None)
    assert key_attribution(key("k", "n", scope_ws="wrkspc_01")) == \\
        ("named-workspace", "wrkspc_01")
    # Deprecated top-level field is the fallback, never the first read.
    assert key_attribution(key("k", "n", top_ws="wrkspc_09")) == \\
        ("named-workspace", "wrkspc_09")
    assert key_attribution(key("k", "n", scope_ws="wrkspc_01",
                               top_ws="wrkspc_09"))[1] == "wrkspc_01"
    # No workspace anywhere: the default workspace, which has no id to report.
    assert key_attribution(key("k", "n")) == ("default-workspace", None)
    assert key_attribution({}) == ("default-workspace", None)
    # An unrecognised scope is never assumed harmless.
    assert key_attribution(key("k", "n", scope_type="service_account"))[0] == \\
        "unknown-scope"


def test_a_playground_request_in_the_default_workspace_is_counted_once():
    # Both fields null. Counting it in both buckets inflates the movable half,
    # which is the half the script is about to recommend work on.
    split = usage_split([page([use(None, None, 1_000)])])
    assert split["console-playground"] == 1_000
    assert split["default-workspace"] == 0
    assert playground_share(split) == 1.0
    assert playground_share({}) == 0.0


def test_amount_is_a_decimal_string_and_null_gets_a_sentinel():
    assert amount({"amount": "1174.40"}) == 1174.40
    assert amount({"amount": None}) == 0.0
    assert amount({"amount": "not money"}) == 0.0
    assert amount(None) == 0.0
    rows = cost_by_workspace([page([cost(None, "10.00"), cost(None, "5.00"),
                                    cost("wrkspc_01", "85.00")])])
    assert rows["(default workspace)"] == 15.0
    assert round(unattributed_share(rows), 2) == 0.15
    assert unattributed_share({}) == 0.0


def test_inactive_keys_never_reach_the_migration_list():
    folded = fold_keys(KEYS + [key("apikey_01ff", "retired",
                                   status="inactive"),
                               key("apikey_01gg", "gone", status="archived")])
    ids = [k["id"] for k in folded["default-workspace"]]
    assert "apikey_01ff" not in ids and "apikey_01gg" not in ids
    assert len(folded["default-workspace"]) == 3
    assert len(folded["organization-scoped"]) == 1
    assert len(folded["named-workspace"]) == 1
    assert fold_keys(None)["default-workspace"] == []


def test_a_small_share_and_an_empty_window_are_never_findings():
    costs = cost_by_workspace([page([cost(None, "40.00"),
                                     cost("wrkspc_01", "960.00")])])
    state, _ = verdict(unattributed_share(costs), 1000.0, fold_keys(KEYS),
                       usage_split([]))
    assert state == "attributed"
    assert verdict(1.0, 0.0, fold_keys([]), {})[0] == "no-spend-yet"
    assert repair_lines("attributed", {}, {}) == []
    assert weigh({"uncached_input_tokens": 10, "output_tokens": 5,
                  "cache_creation": {"ephemeral_5m_input_tokens": 7}}) == 22
    assert weigh({"cache_creation": 3}) == 0
    assert weigh(None) == 0


def test_every_active_key_is_placed_and_the_bucket_still_has_spend():
    folded = fold_keys([key("apikey_01ee", "billing-team", scope_ws="wrkspc_01")])
    state, detail = verdict(0.31, 41_208.55, folded,
                            usage_split([page([use("apikey_01ee", None, 5)])]))
    assert state == "unattributable-no-key-to-move"
    assert "since been deleted" in detail
    assert any("do not open a migration ticket" in line
               for line in repair_lines(state, folded, {}))
''',
"test_js_file": "anthropic-default-workspace-cost.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { amount, costByWorkspace, foldKeys, keyAttribution, playgroundShare,
         repairLines, unattributedShare, usageSplit, verdict, weigh, windowStart }
  from './anthropic-default-workspace-cost.mjs';

const cost = (workspaceId, value) =>
  ({ workspace_id: workspaceId, amount: value, currency: 'USD' });

const use = (apiKeyId, workspaceId, tokens) =>
  ({ api_key_id: apiKeyId, workspace_id: workspaceId, uncached_input_tokens: tokens });

const page = (results) => ({ data: [{ results }], has_more: false });

const key = (id, name, { scopeType = 'workspace', scopeWs = null, topWs = null,
                         status = 'active' } = {}) =>
  ({ id, name, status, scope: { type: scopeType, workspace_id: scopeWs },
     workspace_id: topWs });

const KEYS = [
  key('apikey_01aa', 'nightly-summaries', { scopeType: 'organization' }),
  key('apikey_01bb', 'ingest-worker'),
  key('apikey_01cc', 'eval-runner'),
  key('apikey_01dd', 'adam-scratch'),
  key('apikey_01ee', 'billing-team', { scopeWs: 'wrkspc_01' }),
];

test('the unallocated bucket is two causes and one of them moves', () => {
  const costs = costByWorkspace([page([cost(null, '15706.09'),
                                       cost('wrkspc_01', '17000.00'),
                                       cost('wrkspc_02', '8502.46')])]);
  const total = Math.round(Object.values(costs).reduce((a, v) => a + v, 0) * 100) / 100;
  const share = unattributedShare(costs);
  assert.equal(Math.round(share * 100) / 100, 0.38);
  const split = usageSplit([page([use(null, null, 900000),
                                  use('apikey_01bb', null, 9100000),
                                  use('apikey_01ee', 'wrkspc_01', 40000000)])]);
  const folded = foldKeys(KEYS);
  const [state, detail] = verdict(share, total, folded, split);
  assert.equal(state, 'movable-keys');
  assert.match(detail, /4 active key\\(s\\)/);
  const repairs = repairLines(state, folded, split);
  assert.ok(repairs.some((l) => l.includes('organization scope')));
  assert.ok(repairs.some((l) => l.includes('Console playground')));
  assert.ok(repairs.some((l) => l.includes('rate-limit override')));
});

test('playground traffic has no key to move', () => {
  const costs = costByWorkspace([page([cost(null, '15706.09'),
                                       cost('wrkspc_01', '25502.46')])]);
  const split = usageSplit([page([use(null, null, 9000000),
                                  use('apikey_01bb', null, 1000000)])]);
  assert.equal(Math.round(playgroundShare(split) * 100) / 100, 0.9);
  const total = Math.round(Object.values(costs).reduce((a, v) => a + v, 0) * 100) / 100;
  const [state, detail] = verdict(unattributedShare(costs), total, foldKeys(KEYS), split);
  assert.equal(state, 'console-playground');
  assert.match(detail, /no key can be moved/);
  assert.ok(!repairLines(state, foldKeys(KEYS), split)
    .some((l) => l.includes('recreate each key')));
});

test('the scope resolver prefers scope over the deprecated field', () => {
  assert.deepEqual(keyAttribution(key('k', 'n', { scopeType: 'organization' })),
                   ['organization-scoped', null]);
  assert.deepEqual(keyAttribution(key('k', 'n', { scopeWs: 'wrkspc_01' })),
                   ['named-workspace', 'wrkspc_01']);
  assert.deepEqual(keyAttribution(key('k', 'n', { topWs: 'wrkspc_09' })),
                   ['named-workspace', 'wrkspc_09']);
  assert.equal(keyAttribution(key('k', 'n', { scopeWs: 'wrkspc_01', topWs: 'wrkspc_09' }))[1],
               'wrkspc_01');
  assert.deepEqual(keyAttribution(key('k', 'n')), ['default-workspace', null]);
  assert.deepEqual(keyAttribution({}), ['default-workspace', null]);
  assert.equal(keyAttribution(key('k', 'n', { scopeType: 'service_account' }))[0],
               'unknown-scope');
});

test('a playground request in the default workspace is counted once', () => {
  const split = usageSplit([page([use(null, null, 1000)])]);
  assert.equal(split['console-playground'], 1000);
  assert.equal(split['default-workspace'], 0);
  assert.equal(playgroundShare(split), 1);
  assert.equal(playgroundShare({}), 0);
});

test('amount is a decimal string and null gets a sentinel', () => {
  assert.equal(amount({ amount: '1174.40' }), 1174.4);
  assert.equal(amount({ amount: null }), 0);
  assert.equal(amount({ amount: 'not money' }), 0);
  assert.equal(amount(null), 0);
  const rows = costByWorkspace([page([cost(null, '10.00'), cost(null, '5.00'),
                                      cost('wrkspc_01', '85.00')])]);
  assert.equal(rows['(default workspace)'], 15);
  assert.equal(Math.round(unattributedShare(rows) * 100) / 100, 0.15);
  assert.equal(unattributedShare({}), 0);
});

test('inactive keys never reach the migration list', () => {
  const folded = foldKeys([...KEYS,
    key('apikey_01ff', 'retired', { status: 'inactive' }),
    key('apikey_01gg', 'gone', { status: 'archived' })]);
  const ids = folded['default-workspace'].map((k) => k.id);
  assert.ok(!ids.includes('apikey_01ff') && !ids.includes('apikey_01gg'));
  assert.equal(folded['default-workspace'].length, 3);
  assert.equal(folded['organization-scoped'].length, 1);
  assert.equal(folded['named-workspace'].length, 1);
  assert.deepEqual(foldKeys(null)['default-workspace'], []);
});

test('a small share and an empty window are never findings', () => {
  const costs = costByWorkspace([page([cost(null, '40.00'),
                                       cost('wrkspc_01', '960.00')])]);
  assert.equal(verdict(unattributedShare(costs), 1000, foldKeys(KEYS),
                       usageSplit([]))[0], 'attributed');
  assert.equal(verdict(1, 0, foldKeys([]), {})[0], 'no-spend-yet');
  assert.deepEqual(repairLines('attributed', {}, {}), []);
  assert.equal(weigh({ uncached_input_tokens: 10, output_tokens: 5,
                       cache_creation: { ephemeral_5m_input_tokens: 7 } }), 22);
  assert.equal(weigh({ cache_creation: 3 }), 0);
  assert.equal(weigh(null), 0);
});

test('every active key is placed and the bucket still has spend', () => {
  const folded = foldKeys([key('apikey_01ee', 'billing-team', { scopeWs: 'wrkspc_01' })]);
  const [state, detail] = verdict(0.31, 41208.55, folded,
    usageSplit([page([use('apikey_01ee', null, 5)])]));
  assert.equal(state, 'unattributable-no-key-to-move');
  assert.match(detail, /since been deleted/);
  assert.ok(repairLines(state, folded, {})
    .some((l) => l.includes('do not open a migration ticket')));
});

test('the window start is floored to midnight utc', () => {
  assert.equal(windowStart(30, new Date('2026-08-31T17:45:12Z')),
               '2026-08-01T00:00:00Z');
});
''',
"faq": [
 ("Is this the same as not being able to attribute cost per customer?",
  "No, and the difference is the point. Per-customer cost is unknowable on both platforms: your tenant is not in the attribution chain, which runs from request to API key to key owner, and nothing you send with a request can put it there. That question has no answer at any threshold. This one has a list of answers. The null workspace bucket decomposes into API keys with ids and names, and every one of them can be recreated inside a named workspace, after which its cost lands somewhere a team can be charged for it. One is a property of the platform and the other is a Tuesday afternoon."),
 ("Can I just move an existing key into a workspace?",
  "No. A key's workspace is fixed when it is created, so the repair is to create a replacement key in the named workspace, cut the workload over, and then disable the old one. That is why the script prints the list rather than a single command: this is a migration with as many steps as you have keys, and each step has an owner who has to be told before their job starts failing. Organization-scoped keys are the same story with one extra wrinkle, in that they were never bound to a workspace in the first place."),
 ("Why does the script care about Console playground traffic?",
  "Because it is the part of the unallocated bucket that no key migration will ever shrink, and reporting the bucket as one number promises a fix that only works on part of it. Playground requests are not associated with any API key, so they report a null api_key_id even when they also report a null workspace id. If they are the majority of the null usage, the script says so and stops recommending a migration, because the real question is where people should be running experiments."),
 ("The default workspace is fine for us. Are we wrong?",
  "Not necessarily, and the script has a threshold rather than a rule. A small organization running everything in the default workspace has a topology fact rather than an attribution failure, and the note about having no boundary at all is the one that applies. What is worth knowing either way is that the default workspace cannot carry a rate-limit override, so traffic there is unbounded relative to the organization limit and can consume the allocation the named workspaces are relying on."),
 ("Which field tells me a key is in the default workspace?",
  "Read scope.workspace_id first and the deprecated top-level workspace_id second. For a key bound to the default workspace the deprecated field is null while the scope carries the real id, so a reader that consults only one of them misclassifies keys in both directions. A scope.type of organization means the key was never bound to a workspace at all. The script also refuses to classify a scope type it does not recognise, because an unfamiliar scope showing up in a future API version should appear in the output as unknown rather than be silently filed as safe."),
],
"related": [REL_TENANT, REL_TOPOLOGY, REL_ARCHIVED],
"citations": [CITE_CL_USAGE_API, CITE_CL_COST_REPORT, CITE_CL_LIST_KEYS,
              CITE_CL_RATE_LIMITS_API],
},
{
"slug": "too-many-organization-owners",
"title": "Almost everyone in the organization holds the owner role",
"description": "The org role model is owner or reader, so every unblock is a promotion. Count owners with service accounts removed, then check the project level too.",
"h1": "Almost everyone in the organization holds the owner role",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai organization users role owner",
             "openai admin api list users",
             "openai reader role api platform",
             "openai admin_api_keys owner",
             "openai project users member owner"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because /v1/organization/users and /v1/organization/admin_api_keys both reject a project key.",
"lead": "Nobody decided this. Someone needed to create a project in week three and the fastest unblock was to make them an owner; someone needed to raise a rate limit in month five and the same thing happened; the contractor needed a key for a fortnight in March. Every one of those was the right call at the time and none of them was ever undone, because demotion is a visible act with a social cost and nothing in the platform ever asks. Two years later the roster has fourteen names on it and thirteen can change the billing settings.",
"short_answer": """<p><code>GET /v1/organization/users?limit=100</code> with an <strong>organization admin key</strong>, paginated on <code>after</code>. Each <code>organization.user</code> carries <code>role</code> (<code>"owner"</code> or <code>"reader"</code>), <code>is_service_account</code>, <code>is_scim_managed</code>, <code>added_at</code> and <code>api_key_last_used_at</code>. Compute the owner share <strong>with service accounts removed</strong>, because they are returned in the same list and are frequently owners by construction; counting them produces a confident finding about robots.</p>
<p>The role model is the reason this happens. There are two org roles and <code>reader</code> is genuinely restrictive, so the first time anyone needs to do anything at all &mdash; create a project, mint a key, change a limit &mdash; the only move available is promotion to owner. An owner can create and archive projects, provision admin keys, change rate limits, alter billing, invite further owners, and remove other members.</p>
<p>Then go one level down. <code>GET /v1/organization/projects/{project_id}/users?limit=100</code> per project returns a per-project <code>role</code> of <code>"member"</code> or <code>"owner"</code>. An organization that has already granted project owner to everyone will not change behaviour when you demote at the org level, so the two readings belong in one report.</p>
<p>And read <code>GET /v1/organization/admin_api_keys</code>, which returns each key's <code>owner</code>. That is the list of people whose demotion actually breaks something, and it is much shorter than the roster.</p>""",
"problem": """<p>The coarseness is the mechanism. With two roles and no middle, "can do their job" and "can change the billing settings" are the same grant, so every unblock in the organization's history is recorded as a promotion. There is no forcing function in the other direction: nothing expires, nothing reviews, and demoting a colleague is a small act of distrust that nobody wants to perform on a Tuesday.</p>
<p>What the organization loses is not really security in the dramatic sense. It is <strong>accountability</strong>. When fourteen people can change a rate limit, a rate limit that changed has no owner, and the question "who did this and why" has fourteen candidate answers and no shorter list. The same is true of a project that was archived, a spend limit that was raised, and an admin key that appeared.</p>
<p>The sharper edge is that an owner can provision an <strong>admin API key</strong>, and an admin key reads the whole organization's usage, costs, users, projects and audit log. So the owner count is not a count of people who can administer the platform through a console session; it is a count of people who can mint a long-lived credential that does the same thing from anywhere.</p>""",
"why": """<p><strong>Service accounts are in the same list, and including them is the most common way to get this wrong.</strong> <code>GET /v1/organization/users</code> returns service accounts alongside people, marked with <code>is_service_account</code>, and a service account created to run a job is often an owner because that is what it needed to be. Counting them inflates the ratio, sometimes past the threshold on its own, and produces a report recommending that you demote a cron job. The script filters first and says how many it removed.</p>
<p><strong>A null <code>api_key_last_used_at</code> is not evidence of an unused privilege.</strong> It means this principal has not authenticated an API request, which is exactly what you would expect of somebody who administers the platform through the console and never writes code. The field is genuinely useful &mdash; an owner with no API usage is a candidate for demotion &mdash; but the script reports it as a question rather than a verdict, because the console leaves no trace in this field and treating silence as absence would recommend demoting the person who actually runs your billing.</p>
<p><strong>SCIM-managed members cannot be fixed here, and changing them through the API is worse than doing nothing.</strong> <code>is_scim_managed</code> means the membership and role are projected from your identity provider. A role changed through the API will be reverted at the next sync, leaving an audit-log entry that says somebody tried and a roster that is unchanged. Those names need a different ticket, pointed at a different system, and the script separates them for exactly that reason.</p>
<p><strong>The org roster is half the picture, because project roles are granted separately.</strong> Reading only <code>/v1/organization/users</code> can show a tidy organization whose every project grants owner to every member, which is the same problem one level down and is invisible from the top. The script tallies per-project roles too, and the repair it prints for a real demotion is to grant the person a project role instead, so they keep the access they actually use.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>All four reads are under <code>/v1/organization/*</code>, which rejects a project key. Read scopes are sufficient; nothing here changes a role, and role changes should not be automated anyway.</p>"""},
 {"h": "List the roster and remove the service accounts",
  "body": """<p><code>GET /v1/organization/users?limit=100</code>, paginated on <code>after</code>. Filter on <code>is_service_account</code> before computing anything. The endpoint also accepts an <code>emails[]</code> filter if you want to check a specific person rather than audit the whole list.</p>"""},
 {"h": "Compute the owner share, and hold the floor",
  "body": """<p>Two owners in a three-person company is not a governance finding, it is a company. The script refuses to grade an organization below a small member floor, because a ratio computed over four people is a statement about the founders rather than about access control.</p>"""},
 {"h": "Separate the SCIM-managed names",
  "body": """<p><code>is_scim_managed</code> members are projected from your identity provider. Their roles are not repairable through this API, so they go in their own list with their own instruction: change the group mapping in the IdP, because a change made here reverts at the next sync.</p>"""},
 {"h": "Read the admin keys and the project roles, then print the demotion list",
  "body": """<p><code>GET /v1/organization/admin_api_keys</code> names the owners who hold a long-lived org-wide credential; those are the demotions with consequences. <code>GET /v1/organization/projects/{project_id}/users</code> shows whether the same over-granting has already happened one level down. The repair is <code>reader</code> at the org level plus a project role where the person actually works &mdash; printed, never performed.</p>"""},
],
"verify": """<p>Re-run after a demotion round. The ratio moves, and the more useful number is the second one: the count of owners with no API usage should fall to the people who genuinely administer billing and keys. If an owner reappears after a sync, that name was SCIM-managed and the change belonged in the identity provider.</p>
<pre><code class="language-bash">python3 openai_owner_ratio_audit.py --days 180
# 14 member(s), 3 service account(s) excluded, 2 SCIM-managed
# owner-majority     11 of 14 human member(s) hold the owner role (79%)
#   a***@example.com      owner   added 2024-03-11  no API key use on record
#   m***@example.com      owner   added 2024-06-02  last key use 214 day(s) ago
#   p***@example.com      owner   added 2025-01-19  holds 1 admin API key
#   project roles: 3 of 4 project(s) also grant owner to every member
#   repair: demote to reader anyone who does not administer billing, keys or projects
#   repair: grant a project role instead, so people keep the access they use
#   repair: 2 owner(s) are SCIM-managed; change the group mapping, not the API
#   repair: 1 owner holds an admin API key; revoke the key before the role
# 1 finding(s)</code></pre>""",
"code_intro": "Three paged GETs plus one per project, and eight pure functions. The service-account filter, which runs before any arithmetic; the role tally, which files an unrecognised role under <code>other</code> rather than assuming it is harmless; the ratio; the email mask, so the output is safe to paste into a channel; the unused-privilege test, which is deliberately reported as a question; the admin-key owner index, which reads names and ids and never a key value; the project-level tally; and the verdict, which holds a member floor because a ratio over four people is not a finding about access control.",
"py_file": "openai_owner_ratio_audit.py",
"py": '''"""Find an OpenAI organization where the owner role is the default.

Read only. Paged GETs against /v1/organization/users, /admin_api_keys,
/projects and each project's /users, with an organization admin key. Every
request is a GET and no request body is constructed.

No key value is read or printed. The admin key listing is used for its `owner`
block only, and email addresses are masked, because this report is a list of
named colleagues.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_owner_ratio_audit")

API = "https://api.openai.com/v1"
DAY = 86400

OWNER = "owner"
READER = "reader"
OTHER = "other"

FINDINGS = ("everyone-is-owner", "owner-majority", "owner-count-high")


def humans(users):
    """The roster with service accounts removed. Pure.

    Service accounts are returned by this endpoint alongside people and are
    frequently owners because that is what the job needed. Counting them
    inflates the ratio and produces a report that recommends demoting a cron.
    """
    return [u for u in (users or []) if not (u or {}).get("is_service_account")]


def role_of(user):
    """Normalise one member's org role. Pure.

    An unrecognised role is filed under "other" rather than folded into reader:
    a future role this script has never heard of should show up in the output
    as unknown, not be silently counted as restricted.
    """
    raw = str((user or {}).get("role") or "").strip().lower()
    return raw if raw in (OWNER, READER) else OTHER


def role_counts(people):
    """{role: count} over a roster. Pure."""
    counts = {OWNER: 0, READER: 0, OTHER: 0}
    for person in people or []:
        counts[role_of(person)] += 1
    return counts


def owner_ratio(counts):
    """Owners as a share of the roster. Pure. 0.0 when the roster is empty."""
    data = counts or {}
    total = sum(int(data.get(r) or 0) for r in (OWNER, READER, OTHER))
    if total <= 0:
        return 0.0
    return int(data.get(OWNER) or 0) / float(total)


def mask(email):
    """Hide the local part of an email address. Pure. Non-emails pass through.

    Every row of this report names a colleague and their privileges. Masking by
    default costs nothing and makes the output safe to paste into a channel.
    """
    text = str(email or "").strip()
    if "@" not in text:
        return text or "unknown"
    local, _, domain = text.partition("@")
    if not local:
        return text
    return local[0] + "***@" + domain


def unused_privilege(user, now, days=180):
    """Has this member authenticated an API request recently? Pure.

    Reported as a question, never as a verdict. A null api_key_last_used_at
    means no API request, which is exactly what an administrator who works
    through the console looks like.
    """
    stamp = (user or {}).get("api_key_last_used_at")
    if not stamp:
        return (True, "no API key use on record")
    try:
        age = (int(now) - int(stamp)) // DAY
    except (TypeError, ValueError):
        return (True, "unreadable api_key_last_used_at")
    if age >= days:
        return (True, "last key use %d day(s) ago" % age)
    return (False, "last key use %d day(s) ago" % age)


def admin_key_owners(keys):
    """{owner_id: owner_name} from the admin key listing. Pure.

    Reads the owner block and nothing else. The key value is not returned by
    this endpoint and is not wanted.
    """
    out = {}
    for key in keys or []:
        owner = (key or {}).get("owner") or {}
        oid = owner.get("id") or (owner.get("user") or {}).get("id")
        if not oid:
            continue
        name = owner.get("name") or (owner.get("user") or {}).get("email") or "unnamed"
        out[str(oid)] = str(name)
    return out


def project_owner_share(members):
    """(owners, total, ratio) for one project's member list. Pure."""
    rows = [m for m in (members or []) if not (m or {}).get("is_service_account")]
    owners = sum(1 for m in rows
                 if str((m or {}).get("role") or "").strip().lower() == OWNER)
    total = len(rows)
    return (owners, total, (owners / float(total)) if total else 0.0)


def verdict(counts, min_members=3, ratio_max=0.50, count_max=5):
    """Classify the roster. Pure. Returns (state, detail).

    The member floor comes first. Two owners in a three-person company is a
    company, not a governance finding, and grading it produces a report that
    nobody can act on and everybody learns to ignore.
    """
    data = counts or {}
    owners = int(data.get(OWNER) or 0)
    total = sum(int(data.get(r) or 0) for r in (OWNER, READER, OTHER))
    ratio = owner_ratio(data)

    if total < min_members:
        return ("too-few-members",
                "%d human member(s) in the organization, too few for a role "
                "distribution to mean anything" % total)
    if ratio >= 0.90 and owners >= 3:
        return ("everyone-is-owner",
                "%d of %d human member(s) hold the owner role (%.0f%%). The "
                "distinction between owner and reader has stopped existing here."
                % (owners, total, ratio * 100))
    if ratio > ratio_max:
        return ("owner-majority",
                "%d of %d human member(s) hold the owner role (%.0f%%)"
                % (owners, total, ratio * 100))
    if owners > count_max:
        return ("owner-count-high",
                "%d of %d human member(s) hold the owner role. The share is "
                "fine and the absolute count is past the %d this audit treats "
                "as a working ceiling, which is a convention rather than a "
                "platform rule." % (owners, total, count_max))
    return ("scoped",
            "%d of %d human member(s) hold the owner role (%.0f%%)"
            % (owners, total, ratio * 100))


def repair_lines(state, scim_owners=0, key_holders=0, loose_projects=0):
    """The repair for one roster verdict. Pure. Printed, never performed."""
    if state not in FINDINGS:
        return []
    lines = [
        "demote to reader anyone who does not administer billing, keys or "
        "projects, with POST /v1/organization/users/{user_id} and role reader.",
        "grant a project role instead, so people keep the access they actually "
        "use: POST /v1/organization/projects/{project_id}/users with member.",
    ]
    if scim_owners:
        lines.append("%d owner(s) are SCIM-managed. Change the group mapping in "
                     "the identity provider; a role changed through this API is "
                     "reverted at the next sync." % scim_owners)
    if key_holders:
        lines.append("%d owner(s) hold an admin API key. Revoke the key before "
                     "the role, or the credential outlives the demotion."
                     % key_holders)
    if loose_projects:
        lines.append("%d project(s) also grant owner to every member, so an "
                     "org-level demotion alone will not change what anybody can "
                     "do there." % loose_projects)
    return lines


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    while True:
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=180,
                    help="days of API silence before privilege is questioned")
    ap.add_argument("--ratio", type=float, default=0.50,
                    help="owner share above which the roster is flagged")
    ap.add_argument("--max-owners", type=int, default=5,
                    help="absolute owner count treated as a working ceiling")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a "
                  "project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    now = int(time.time())

    users = list(paged(s, "/organization/users", limit=100))
    people = humans(users)
    counts = role_counts(people)
    owners = [p for p in people if role_of(p) == OWNER]
    scim = [p for p in owners if p.get("is_scim_managed")]
    holders = admin_key_owners(paged(s, "/organization/admin_api_keys", limit=100))

    loose = 0
    projects = [p for p in paged(s, "/organization/projects", limit=100)
                if str(p.get("status") or "").lower() != "archived"]
    for project in projects:
        members = list(paged(s, "/organization/projects/%s/users" % project.get("id"),
                             limit=100))
        got, total, ratio = project_owner_share(members)
        if total and ratio >= 0.90:
            loose += 1

    log.info("%d member(s), %d service account(s) excluded, %d SCIM-managed",
             len(people), len(users) - len(people), len(scim))

    state, detail = verdict(counts, ratio_max=args.ratio, count_max=args.max_owners)
    if state not in FINDINGS:
        log.info("%-18s %s", state, detail)
        return 0

    log.warning("%-18s %s", state, detail)
    for person in sorted(owners, key=lambda p: int(p.get("added_at") or 0)):
        _, note = unused_privilege(person, now, args.days)
        extra = " holds an admin API key" if str(person.get("id")) in holders else ""
        log.warning("  %-24s owner   added %s  %s%s", mask(person.get("email")),
                    time.strftime("%Y-%m-%d",
                                  time.gmtime(int(person.get("added_at") or 0))),
                    note, extra)
    if loose:
        log.warning("  project roles: %d of %d project(s) also grant owner to "
                    "every member", loose, len(projects))
    key_holders = sum(1 for p in owners if str(p.get("id")) in holders)
    for line in repair_lines(state, len(scim), key_holders, loose):
        log.warning("  repair: %s", line)
    log.info("1 finding(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-owner-ratio-audit.mjs",
"js": '''/**
 * Find an OpenAI organization where the owner role is the default.
 *
 * Read only. Paged GETs against /v1/organization/users, /admin_api_keys,
 * /projects and each project's /users. No request body is constructed and no
 * key value is read or printed; email addresses are masked.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;

const OWNER = 'owner';
const READER = 'reader';
const OTHER = 'other';

const FINDINGS = new Set(['everyone-is-owner', 'owner-majority', 'owner-count-high']);

/** The roster with service accounts removed. Pure. */
export function humans(users) {
  return (users ?? []).filter((u) => !(u ?? {}).is_service_account);
}

/** Normalise one member's org role. Pure. Unknown roles are "other". */
export function roleOf(user) {
  const raw = String(user?.role ?? '').trim().toLowerCase();
  return raw === OWNER || raw === READER ? raw : OTHER;
}

/** {role: count} over a roster. Pure. */
export function roleCounts(people) {
  const counts = { [OWNER]: 0, [READER]: 0, [OTHER]: 0 };
  for (const person of people ?? []) counts[roleOf(person)] += 1;
  return counts;
}

/** Owners as a share of the roster. Pure. */
export function ownerRatio(counts) {
  const data = counts ?? {};
  const total = [OWNER, READER, OTHER].reduce((a, r) => a + (data[r] ?? 0), 0);
  if (total <= 0) return 0;
  return (data[OWNER] ?? 0) / total;
}

/** Hide the local part of an email address. Pure. Non-emails pass through. */
export function mask(email) {
  const text = String(email ?? '').trim();
  if (!text.includes('@')) return text || 'unknown';
  const at = text.indexOf('@');
  const local = text.slice(0, at);
  if (!local) return text;
  return `${local[0]}***${text.slice(at)}`;
}

/** Has this member authenticated an API request recently? Pure. A question, not a verdict. */
export function unusedPrivilege(user, now, days = 180) {
  const stamp = user?.api_key_last_used_at;
  if (!stamp) return [true, 'no API key use on record'];
  const value = Number(stamp);
  if (!Number.isFinite(value)) return [true, 'unreadable api_key_last_used_at'];
  const age = Math.floor((Number(now) - value) / DAY);
  return [age >= days, `last key use ${age} day(s) ago`];
}

/** {owner_id: owner_name} from the admin key listing. Pure. Owner block only. */
export function adminKeyOwners(keys) {
  const out = {};
  for (const key of keys ?? []) {
    const owner = key?.owner ?? {};
    const id = owner.id ?? owner.user?.id;
    if (!id) continue;
    out[String(id)] = String(owner.name ?? owner.user?.email ?? 'unnamed');
  }
  return out;
}

/** [owners, total, ratio] for one project's member list. Pure. */
export function projectOwnerShare(members) {
  const rows = (members ?? []).filter((m) => !(m ?? {}).is_service_account);
  const owners = rows.filter(
    (m) => String(m?.role ?? '').trim().toLowerCase() === OWNER).length;
  const total = rows.length;
  return [owners, total, total ? owners / total : 0];
}

/** Classify the roster. Pure. Returns [state, detail]. The member floor comes first. */
export function verdict(counts, minMembers = 3, ratioMax = 0.50, countMax = 5) {
  const data = counts ?? {};
  const owners = data[OWNER] ?? 0;
  const total = [OWNER, READER, OTHER].reduce((a, r) => a + (data[r] ?? 0), 0);
  const ratio = ownerRatio(data);

  if (total < minMembers) {
    return ['too-few-members',
            `${total} human member(s) in the organization, too few for a role `
            + 'distribution to mean anything'];
  }
  if (ratio >= 0.90 && owners >= 3) {
    return ['everyone-is-owner',
            `${owners} of ${total} human member(s) hold the owner role `
            + `(${(ratio * 100).toFixed(0)}%). The distinction between owner and `
            + 'reader has stopped existing here.'];
  }
  if (ratio > ratioMax) {
    return ['owner-majority',
            `${owners} of ${total} human member(s) hold the owner role `
            + `(${(ratio * 100).toFixed(0)}%)`];
  }
  if (owners > countMax) {
    return ['owner-count-high',
            `${owners} of ${total} human member(s) hold the owner role. The share `
            + `is fine and the absolute count is past the ${countMax} this audit `
            + 'treats as a working ceiling, which is a convention rather than a '
            + 'platform rule.'];
  }
  return ['scoped',
          `${owners} of ${total} human member(s) hold the owner role `
          + `(${(ratio * 100).toFixed(0)}%)`];
}

/** The repair for one roster verdict. Pure. Printed, never performed. */
export function repairLines(state, scimOwners = 0, keyHolders = 0, looseProjects = 0) {
  if (!FINDINGS.has(state)) return [];
  const lines = [
    'demote to reader anyone who does not administer billing, keys or projects, '
    + 'with POST /v1/organization/users/{user_id} and role reader.',
    'grant a project role instead, so people keep the access they actually use: '
    + 'POST /v1/organization/projects/{project_id}/users with member.',
  ];
  if (scimOwners) {
    lines.push(`${scimOwners} owner(s) are SCIM-managed. Change the group mapping in `
      + 'the identity provider; a role changed through this API is reverted at the '
      + 'next sync.');
  }
  if (keyHolders) {
    lines.push(`${keyHolders} owner(s) hold an admin API key. Revoke the key before `
      + 'the role, or the credential outlives the demotion.');
  }
  if (looseProjects) {
    lines.push(`${looseProjects} project(s) also grant owner to every member, so an `
      + 'org-level demotion alone will not change what anybody can do there.');
  }
  return lines;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
                    + 'organization admin key, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function paged(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
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
                  + 'key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 180);
  const now = Math.floor(Date.now() / 1000);

  const users = await paged(admin, '/organization/users', { limit: 100 });
  const people = humans(users);
  const counts = roleCounts(people);
  const owners = people.filter((p) => roleOf(p) === OWNER);
  const scim = owners.filter((p) => p.is_scim_managed);
  const holders = adminKeyOwners(
    await paged(admin, '/organization/admin_api_keys', { limit: 100 }));

  const projects = (await paged(admin, '/organization/projects', { limit: 100 }))
    .filter((p) => String(p.status ?? '').toLowerCase() !== 'archived');
  let loose = 0;
  for (const project of projects) {
    const members = await paged(admin, `/organization/projects/${project.id}/users`,
                                { limit: 100 });
    const [, total, ratio] = projectOwnerShare(members);
    if (total && ratio >= 0.90) loose += 1;
  }

  console.log(`${people.length} member(s), ${users.length - people.length} service `
              + `account(s) excluded, ${scim.length} SCIM-managed`);

  const [state, detail] = verdict(counts);
  console.log(`${state.padEnd(18)} ${detail}`);
  if (!FINDINGS.has(state)) return;

  for (const person of [...owners].sort((a, b) =>
    Number(a.added_at ?? 0) - Number(b.added_at ?? 0))) {
    const [, note] = unusedPrivilege(person, now, days);
    const extra = holders[String(person.id)] ? ' holds an admin API key' : '';
    const added = new Date(Number(person.added_at ?? 0) * 1000)
      .toISOString().slice(0, 10);
    console.log(`  ${mask(person.email).padEnd(24)} owner   added ${added}  ${note}${extra}`);
  }
  if (loose) {
    console.log(`  project roles: ${loose} of ${projects.length} project(s) also `
                + 'grant owner to every member');
  }
  const keyHolders = owners.filter((p) => holders[String(p.id)]).length;
  for (const line of repairLines(state, scim.length, keyHolders, loose)) {
    console.log(`  repair: ${line}`);
  }
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the one that decides whether this note is worth anything: a roster of ten where three are service accounts and all three are owners, so the raw list says eighty per cent and the roster of people says seventy-one, and only one of those numbers is about access control. Under it: the member floor, because two owners in a three-person company is a company; the absolute count that flags at a low share and says out loud that the ceiling is a convention; the null <code>api_key_last_used_at</code> that must be reported as a question rather than as an unused privilege; SCIM-managed owners, whose repair points at the identity provider because an API change reverts at the next sync; the admin-key index, which reads the owner block and never a key value; and the project level, where the same over-granting hides from a roster that looks fine.",
"test_py_file": "test_openai_owner_ratio_audit.py",
"test_py": '''from openai_owner_ratio_audit import (admin_key_owners, humans, mask,
                                        owner_ratio, project_owner_share,
                                        repair_lines, role_counts, role_of,
                                        unused_privilege, verdict)

NOW = 1_780_000_000


def user(uid, email, role="reader", service=False, scim=False, last_used=NOW,
         added=1_700_000_000):
    return {"id": uid, "email": email, "role": role,
            "is_service_account": service, "is_scim_managed": scim,
            "api_key_last_used_at": last_used, "added_at": added}


ROSTER = [
    user("u_1", "ada@example.com", "owner", last_used=None),
    user("u_2", "mel@example.com", "owner", last_used=NOW - 214 * 86400),
    user("u_3", "pat@example.com", "owner"),
    user("u_4", "sam@example.com", "owner", scim=True),
    user("u_5", "kim@example.com", "owner", scim=True),
    user("u_6", "rob@example.com", "reader"),
    user("u_7", "jo@example.com", "reader"),
    user("sa_1", "ingest@svc", "owner", service=True),
    user("sa_2", "batch@svc", "owner", service=True),
    user("sa_3", "evals@svc", "owner", service=True),
]


def test_service_accounts_never_count_toward_the_owner_ratio():
    # The trap in one assertion. The raw list is 8 owners of 10; the roster of
    # people is 5 of 7. Only the second is a statement about access control,
    # and the first recommends demoting a cron job.
    assert round(owner_ratio(role_counts(ROSTER)), 2) == 0.80
    people = humans(ROSTER)
    assert len(people) == 7
    counts = role_counts(people)
    assert counts == {"owner": 5, "reader": 2, "other": 0}
    state, detail = verdict(counts)
    assert state == "owner-majority"
    assert "5 of 7" in detail


def test_a_small_organization_is_never_graded():
    two = [user("u_1", "a@x.com", "owner"), user("u_2", "b@x.com", "owner")]
    state, detail = verdict(role_counts(humans(two)))
    assert state == "too-few-members"
    assert "too few" in detail
    assert repair_lines(state) == []


def test_everyone_being_an_owner_is_its_own_state():
    roster = [user("u_%d" % i, "p%d@x.com" % i, "owner") for i in range(6)]
    state, detail = verdict(role_counts(humans(roster)))
    assert state == "everyone-is-owner"
    assert "stopped existing" in detail


def test_a_high_count_at_a_low_share_says_the_ceiling_is_a_convention():
    roster = ([user("o_%d" % i, "o%d@x.com" % i, "owner") for i in range(6)]
              + [user("r_%d" % i, "r%d@x.com" % i, "reader") for i in range(34)])
    state, detail = verdict(role_counts(humans(roster)))
    assert state == "owner-count-high"
    assert "convention rather than a platform rule" in detail


def test_no_recorded_key_use_is_a_question_and_not_a_verdict():
    quiet, note = unused_privilege(ROSTER[0], NOW)
    assert quiet is True and note == "no API key use on record"
    old, note = unused_privilege(ROSTER[1], NOW)
    assert old is True and "214 day(s) ago" in note
    fresh, note = unused_privilege(ROSTER[2], NOW)
    assert fresh is False
    assert unused_privilege({"api_key_last_used_at": "yesterday"}, NOW)[0] is True


def test_scim_managed_owners_get_a_repair_pointed_somewhere_else():
    owners = [p for p in humans(ROSTER) if role_of(p) == "owner"]
    scim = [p for p in owners if p["is_scim_managed"]]
    assert len(scim) == 2
    lines = repair_lines("owner-majority", len(scim), 1, 3)
    assert any("identity provider" in line and "reverted at the next sync" in line
               for line in lines)
    assert any("Revoke the key before" in line for line in lines)
    assert any("org-level demotion alone" in line for line in lines)


def test_the_admin_key_index_reads_the_owner_block_and_nothing_else():
    keys = [{"id": "key_admin_1", "name": "ci",
             "owner": {"id": "u_3", "name": "Pat", "type": "user"}},
            {"id": "key_admin_2", "owner": {"user": {"id": "u_9",
                                                     "email": "x@y.com"}}},
            {"id": "key_admin_3", "owner": {}}]
    index = admin_key_owners(keys)
    assert index == {"u_3": "Pat", "u_9": "x@y.com"}
    assert admin_key_owners(None) == {}


def test_project_roles_are_the_second_level():
    members = [{"id": "u_1", "role": "owner"}, {"id": "u_2", "role": "owner"},
               {"id": "u_3", "role": "owner"},
               {"id": "sa_1", "role": "owner", "is_service_account": True}]
    assert project_owner_share(members) == (3, 3, 1.0)
    mixed = [{"id": "u_1", "role": "owner"}, {"id": "u_2", "role": "member"},
             {"id": "u_3", "role": "member"}]
    owners, total, ratio = project_owner_share(mixed)
    assert (owners, total) == (1, 3) and round(ratio, 2) == 0.33
    assert project_owner_share([]) == (0, 0, 0.0)


def test_unknown_roles_are_never_counted_as_restricted():
    assert role_of({"role": "OWNER"}) == "owner"
    assert role_of({"role": "reader"}) == "reader"
    assert role_of({"role": "billing"}) == "other"
    assert role_of({}) == "other"
    assert owner_ratio({}) == 0.0


def test_emails_are_masked():
    assert mask("ada@example.com") == "a***@example.com"
    assert mask("service-account") == "service-account"
    assert mask(None) == "unknown"
''',
"test_js_file": "openai-owner-ratio-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { adminKeyOwners, humans, mask, ownerRatio, projectOwnerShare, repairLines,
         roleCounts, roleOf, unusedPrivilege, verdict }
  from './openai-owner-ratio-audit.mjs';

const NOW = 1780000000;

const user = (id, email, role = 'reader', {
  service = false, scim = false, lastUsed = NOW, added = 1700000000 } = {}) =>
  ({ id, email, role, is_service_account: service, is_scim_managed: scim,
     api_key_last_used_at: lastUsed, added_at: added });

const ROSTER = [
  user('u_1', 'ada@example.com', 'owner', { lastUsed: null }),
  user('u_2', 'mel@example.com', 'owner', { lastUsed: NOW - 214 * 86400 }),
  user('u_3', 'pat@example.com', 'owner'),
  user('u_4', 'sam@example.com', 'owner', { scim: true }),
  user('u_5', 'kim@example.com', 'owner', { scim: true }),
  user('u_6', 'rob@example.com', 'reader'),
  user('u_7', 'jo@example.com', 'reader'),
  user('sa_1', 'ingest@svc', 'owner', { service: true }),
  user('sa_2', 'batch@svc', 'owner', { service: true }),
  user('sa_3', 'evals@svc', 'owner', { service: true }),
];

test('service accounts never count toward the owner ratio', () => {
  assert.equal(Math.round(ownerRatio(roleCounts(ROSTER)) * 100) / 100, 0.8);
  const people = humans(ROSTER);
  assert.equal(people.length, 7);
  const counts = roleCounts(people);
  assert.deepEqual(counts, { owner: 5, reader: 2, other: 0 });
  const [state, detail] = verdict(counts);
  assert.equal(state, 'owner-majority');
  assert.match(detail, /5 of 7/);
});

test('a small organization is never graded', () => {
  const two = [user('u_1', 'a@x.com', 'owner'), user('u_2', 'b@x.com', 'owner')];
  const [state, detail] = verdict(roleCounts(humans(two)));
  assert.equal(state, 'too-few-members');
  assert.match(detail, /too few/);
  assert.deepEqual(repairLines(state), []);
});

test('everyone being an owner is its own state', () => {
  const roster = Array.from({ length: 6 },
    (_, i) => user(`u_${i}`, `p${i}@x.com`, 'owner'));
  const [state, detail] = verdict(roleCounts(humans(roster)));
  assert.equal(state, 'everyone-is-owner');
  assert.match(detail, /stopped existing/);
});

test('a high count at a low share says the ceiling is a convention', () => {
  const roster = [
    ...Array.from({ length: 6 }, (_, i) => user(`o_${i}`, `o${i}@x.com`, 'owner')),
    ...Array.from({ length: 34 }, (_, i) => user(`r_${i}`, `r${i}@x.com`, 'reader')),
  ];
  const [state, detail] = verdict(roleCounts(humans(roster)));
  assert.equal(state, 'owner-count-high');
  assert.match(detail, /convention rather than a platform rule/);
});

test('no recorded key use is a question and not a verdict', () => {
  assert.deepEqual(unusedPrivilege(ROSTER[0], NOW), [true, 'no API key use on record']);
  const [old, note] = unusedPrivilege(ROSTER[1], NOW);
  assert.equal(old, true);
  assert.match(note, /214 day\\(s\\) ago/);
  assert.equal(unusedPrivilege(ROSTER[2], NOW)[0], false);
  assert.equal(unusedPrivilege({ api_key_last_used_at: 'yesterday' }, NOW)[0], true);
});

test('scim-managed owners get a repair pointed somewhere else', () => {
  const owners = humans(ROSTER).filter((p) => roleOf(p) === 'owner');
  const scim = owners.filter((p) => p.is_scim_managed);
  assert.equal(scim.length, 2);
  const lines = repairLines('owner-majority', scim.length, 1, 3);
  assert.ok(lines.some((l) => l.includes('identity provider')
                              && l.includes('reverted at the next sync')));
  assert.ok(lines.some((l) => l.includes('Revoke the key before')));
  assert.ok(lines.some((l) => l.includes('org-level demotion alone')));
});

test('the admin key index reads the owner block and nothing else', () => {
  const keys = [
    { id: 'key_admin_1', name: 'ci', owner: { id: 'u_3', name: 'Pat', type: 'user' } },
    { id: 'key_admin_2', owner: { user: { id: 'u_9', email: 'x@y.com' } } },
    { id: 'key_admin_3', owner: {} },
  ];
  assert.deepEqual(adminKeyOwners(keys), { u_3: 'Pat', u_9: 'x@y.com' });
  assert.deepEqual(adminKeyOwners(null), {});
});

test('project roles are the second level', () => {
  const members = [{ id: 'u_1', role: 'owner' }, { id: 'u_2', role: 'owner' },
                   { id: 'u_3', role: 'owner' },
                   { id: 'sa_1', role: 'owner', is_service_account: true }];
  assert.deepEqual(projectOwnerShare(members), [3, 3, 1]);
  const [owners, total, ratio] = projectOwnerShare(
    [{ id: 'u_1', role: 'owner' }, { id: 'u_2', role: 'member' },
     { id: 'u_3', role: 'member' }]);
  assert.deepEqual([owners, total], [1, 3]);
  assert.equal(Math.round(ratio * 100) / 100, 0.33);
  assert.deepEqual(projectOwnerShare([]), [0, 0, 0]);
});

test('unknown roles are never counted as restricted', () => {
  assert.equal(roleOf({ role: 'OWNER' }), 'owner');
  assert.equal(roleOf({ role: 'reader' }), 'reader');
  assert.equal(roleOf({ role: 'billing' }), 'other');
  assert.equal(roleOf({}), 'other');
  assert.equal(ownerRatio({}), 0);
});

test('emails are masked', () => {
  assert.equal(mask('ada@example.com'), 'a***@example.com');
  assert.equal(mask('service-account'), 'service-account');
  assert.equal(mask(null), 'unknown');
});
''',
"faq": [
 ("Is a lot of owners really a problem, or is this just security theatre?",
  "It is an accountability problem before it is a security one. When eleven people can change a rate limit, a rate limit that changed has eleven candidate authors and no shorter list, and the same is true of an archived project, a raised spend limit and a new admin key. The sharper edge is that an owner can provision an admin API key, which reads the whole organization's usage, costs, users, projects and audit log from anywhere. So the owner count is not a count of people who can administer from a console session, it is a count of people who can mint a long-lived credential that does the same thing."),
 ("Why does the script exclude service accounts from the ratio?",
  "Because they are in the same list and they are frequently owners by construction. A service account created to run a nightly job may well have needed owner, and it is not a governance failure that it has one. Including them inflates the ratio, sometimes past the threshold on its own, and produces a report whose top recommendation is to demote a cron job. The script filters on is_service_account before it computes anything and prints how many it removed, so the number you are reading is always about people."),
 ("One of our owners shows no API key use at all. Should they be demoted?",
  "Maybe, but not on that field alone. A null api_key_last_used_at means the person has not authenticated an API request, which is exactly what an administrator who works through the console looks like — including the person who actually runs your billing. The script reports it as a question next to the name rather than as a finding, because treating silence as absence is how an audit ends up recommending the removal of the one owner you cannot do without."),
 ("We manage membership through SCIM. Does any of this apply?",
  "The reading does; the repair does not. Members with is_scim_managed set have their membership and role projected from your identity provider, so a role changed through this API is reverted at the next sync, leaving an audit-log entry saying somebody tried and a roster that has not moved. The script counts those owners separately and prints a repair aimed at the group mapping in the IdP. Everyone else is repairable here."),
 ("Does Anthropic have the same problem?",
  "It has the same shape with different names and one extra consequence. Console organizations use user, developer, billing, admin and claude_code_user rather than owner and reader, and developer is the correct default for people building against the API. The role that matters is admin, because only an admin can provision an Admin API key, and an org:admin token grants access to the whole organization regardless of which workspace the underlying profile is bound to. The equivalent reads are the org user list and, one level down, each workspace's member list."),
],
"related": [REL_OWNER_LOST, REL_ARCHIVED, REL_INVITES],
"citations": [CITE_OA_ADMIN, CITE_OA_ADMIN_GUIDE, CITE_OA_PROJECTS, CITE_OA_SDK],
},
{
"slug": "openai-invites-pending-past-expiry",
"title": "Organization invites sat pending until they expired",
"description": "An invite whose status still reads pending while its expires_at has passed is invisible to a status filter. Read the timestamp, and read the role it carried.",
"h1": "Organization invites sat pending until they expired",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai organization invites pending expired",
             "openai admin api list invites",
             "openai invite expires_at role owner",
             "openai invite never accepted",
             "openai organization onboarding api access"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because /v1/organization/invites rejects a project key.",
"lead": "The new engineer said she was set up, and she was: the laptop arrived, SSO worked, the repository cloned. Six weeks later somebody notices that the nightly job is running under a colleague's personal key because she asked to borrow it on her second day and never stopped. The invite to the API organization was sent on her first morning, went to a filtered folder, and is still sitting in the list marked <code>pending</code> with an <code>expires_at</code> that passed in April.",
"short_answer": """<p><code>GET /v1/organization/invites?limit=100</code> with an <strong>organization admin key</strong>, paginated on <code>after</code>. Each <code>organization.invite</code> carries <code>id</code>, <code>email</code>, <code>role</code> (<code>"owner"</code> or <code>"reader"</code>), <code>status</code> (<code>"pending"</code>, <code>"accepted"</code>, <code>"expired"</code>), <code>expires_at</code>, <code>accepted_at</code>, a sent timestamp, and <code>projects[]</code> with a per-project <code>role</code>.</p>
<p>The test that matters is on the timestamp, not the status. <strong>An invite can read <code>status: "pending"</code> while its <code>expires_at</code> is already in the past</strong>, so a filter that trusts the status field alone never sees the row at all. Compare <code>expires_at</code> against now and treat that as its own state, separate from the ones the API has already relabelled <code>expired</code>.</p>
<p>Then cross-check the roster. <code>GET /v1/organization/users?limit=100</code>: a pending invite for somebody who already appears there is a stale record rather than a failed onboarding, and it has a one-line repair. What is left is the real list &mdash; people who were told they had access and do not.</p>
<p>Read the <code>role</code> and the <code>projects[]</code> grants before you delete anything. An outstanding invite at <code>role: "owner"</code> is an unclaimed grant of full organization control sitting in somebody's mailbox, and a <code>projects[]</code> entry with <code>role: "owner"</code> is the same thing scoped to a project.</p>""",
"problem": """<p>An invite is fire-and-forget in both directions. Nothing chases the recipient, and nothing tells the sender that it lapsed. The sender closed the onboarding ticket the moment the invite went out, because sending it was the task, and the acceptance is a step that happens in a mailbox they cannot see.</p>
<p>What actually happens next is the operational cost. The person needs to do their job, so they borrow a credential: a colleague's key in an environment file, a service account key pasted into a chat, a project key that ends up in three places. The absence of access does not stop the work, it just routes the work through somebody else's identity, which is how a key ends up authenticating requests that its owner cannot account for.</p>
<p>And there is a second half that has nothing to do with onboarding. An outstanding invite is a standing offer. A pending or lapsed invite at <code>owner</code> for a candidate who was never hired, or an employee who has since left, is a grant of organization control that nobody is watching and that only requires access to one mailbox.</p>""",
"why": """<p><strong>The status field and the clock disagree, and the disagreement is the whole detection.</strong> Invites carry an <code>expires_at</code> and the platform relabels them <code>expired</code> on its own, but a record can sit at <code>pending</code> with an <code>expires_at</code> that has already gone by. An audit written as <code>status == "expired"</code> reports a tidy list and misses exactly the rows that are neither live nor cleaned up. The script therefore compares the timestamp itself and reports the two states separately, because a lapsed pending record and an already-relabelled one call for different sentences in the same email.</p>
<p><strong>Not every stale invite is a failed onboarding, and mixing them wastes the reviewer's attention.</strong> A pending invite for somebody who is already in <code>GET /v1/organization/users</code> means the person got in another way &mdash; a second invite, a different address, SSO provisioning &mdash; and the only thing to do is delete the record. The script resolves every invite against the roster first and files those separately, so the list a human reads is people who genuinely do not have access.</p>
<p><strong>An invite is not only a membership, and the deletion withdraws more than people expect.</strong> The <code>projects[]</code> array carries per-project roles that take effect on acceptance, so an invite can hand over organization <code>reader</code> and project <code>owner</code> in the same message. The script prints the grants alongside the role for that reason: deleting the invite is correct, and re-sending it later without the project entries silently gives the person less than the first one offered.</p>
<p><strong>The one thing the API cannot tell you is whether the email arrived.</strong> There is no delivery status on this object, and no read-only way to distinguish a filtered message from an ignored one. The script never claims to know why an invite went uncollected; it reports how long ago it was sent, when it expired, what it granted, and whether the person is in the org by some other route. The reconstruction that does exist is the audit log, where <code>invite.sent</code>, <code>invite.accepted</code> and <code>invite.deleted</code> give you the history of who offered what and when.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p><code>/v1/organization/invites</code> and <code>/v1/organization/users</code> both reject a project key. Read scopes are enough; this script sends nothing and deletes nothing.</p>"""},
 {"h": "List every invite, not just the pending ones",
  "body": """<p><code>GET /v1/organization/invites?limit=100</code>, paginated on <code>after</code>. Do not narrow by status at the API: the accepted rows cost nothing to read and the expired ones are half the cleanup.</p>"""},
 {"h": "Test expires_at against the clock, not status against a string",
  "body": """<p>A record at <code>status: "pending"</code> whose <code>expires_at</code> has passed is the row a status filter never returns. Grade it separately from the rows the platform has already relabelled <code>expired</code>, because one is a lapse and the other is a backlog.</p>"""},
 {"h": "Resolve every invitee against the current roster",
  "body": """<p><code>GET /v1/organization/users?limit=100</code>. A pending invite for an existing member is a stale record with a one-line repair, and separating those keeps the list a human reads down to people who really have no access.</p>"""},
 {"h": "Sort by what the invite granted, and print the repair",
  "body": """<p><code>role: "owner"</code> first, then anything with a project <code>owner</code> grant, then the rest. The repair per row is <code>DELETE /v1/organization/invites/{invite_id}</code>, followed for the ones that should still proceed by a fresh invite carrying the same <code>projects[]</code> entries &mdash; printed, never performed.</p>"""},
],
"verify": """<p>Delete the stale records, re-send the ones that should proceed, and re-run in a week. The lapsed rows should be gone rather than reclassified, and any invite that is pending again with a fresh <code>expires_at</code> is one to chase by hand, because the API will not tell you whether the second email arrived either.</p>
<pre><code class="language-bash">python3 openai_stale_invite_audit.py --stale-days 14
# 23 invite(s), 14 accepted, 7 finding(s)
# expired-but-still-pending  r***@example.com  role=owner   sent 137 day(s) ago,
#                            expires_at passed 107 day(s) ago
#   grants: proj_ingest=owner, proj_web=member
#   repair: this invite still offers full organization control. Delete it first.
#   repair: DELETE /v1/organization/invites/invite_01hd
# already-a-member           m***@example.com  role=reader  sent 61 day(s) ago
#   repair: this person is already in the roster. Delete the record; there is no
#           onboarding problem here.
# pending-stale              j***@example.com  role=reader  sent 29 day(s) ago
#   repair: ask whether they ever received it, then delete and re-send with the
#           same projects[] entries, or delete and stop.</code></pre>""",
"code_intro": "Two paged GETs and six pure functions. The sent-timestamp reader, which accepts either name the field goes by; the email mask; the owner-grant test, which looks at the project entries as well as the top-level role; the project-grant list; the roster index; and the classifier, which tests <code>expires_at</code> against the clock before it tests <code>status</code> against a string, because that ordering is the only reason the lapsed-but-pending rows appear at all. No token, key or secret appears anywhere in the output: the invite object carries none, and the script prints ids, masked addresses, roles and dates.",
"py_file": "openai_stale_invite_audit.py",
"py": '''"""Find OpenAI organization invites that lapsed without anybody noticing.

Read only. Two paged GETs against /v1/organization/invites and
/v1/organization/users with an organization admin key. Every request is a GET
and no request body is constructed.

The detection is a timestamp comparison rather than a status filter: an invite
can read status "pending" while its expires_at is already in the past, and a
filter on status alone never returns that row.

Nothing secret is printed. The invite object carries no token, and the output
is ids, masked email addresses, roles and dates.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_stale_invite_audit")

API = "https://api.openai.com/v1"
DAY = 86400

OWNER = "owner"

FINDINGS = ("expired-but-still-pending", "already-a-member", "pending-stale",
            "expired-uncollected")

# Findings in the order a human should read them. An unclaimed grant of
# organization control outranks a tidy-up, whatever the timestamps say.
SEVERITY = {"expired-but-still-pending": 0, "pending-stale": 1,
            "expired-uncollected": 2, "already-a-member": 3}


def sent_at(invite):
    """When the invite was sent, as unix seconds. Pure. None when unreadable.

    The field goes by two names depending on where you read the reference, so
    both are accepted rather than picking a side and reporting every invite as
    having been sent at the epoch.
    """
    row = invite or {}
    for field in ("invited_at", "created_at", "sent_at"):
        value = row.get(field)
        if value:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def mask(email):
    """Hide the local part of an email address. Pure. Non-emails pass through."""
    text = str(email or "").strip()
    if "@" not in text:
        return text or "unknown"
    local, _, domain = text.partition("@")
    if not local:
        return text
    return local[0] + "***@" + domain


def project_roles(invite):
    """[(project_id, role)] carried by one invite. Pure.

    These take effect on acceptance, so they are part of what the invite is
    offering and part of what deleting it withdraws.
    """
    out = []
    for entry in (invite or {}).get("projects") or []:
        row = entry or {}
        out.append((str(row.get("id") or "unknown"),
                    str(row.get("role") or "member").strip().lower()))
    return out


def owner_grant(invite):
    """Does this invite hand over owner anywhere? Pure.

    True for a top-level owner role and for a project entry at owner, because
    an org reader with project owner is still an unclaimed grant of control.
    """
    row = invite or {}
    if str(row.get("role") or "").strip().lower() == OWNER:
        return True
    return any(role == OWNER for _, role in project_roles(row))


def member_emails(users):
    """Lowercased email addresses on the current roster. Pure."""
    out = set()
    for user in users or []:
        email = str((user or {}).get("email") or "").strip().lower()
        if email:
            out.add(email)
    return out


def classify(invite, members, now, stale_days=14):
    """Classify one invite. Pure. Returns (state, detail).

    expires_at is tested against the clock BEFORE status is tested against a
    string. A record can sit at "pending" past its own expiry, and that is the
    row every status filter misses.
    """
    row = invite or {}
    status = str(row.get("status") or "").strip().lower()
    email = str(row.get("email") or "").strip().lower()
    sent = sent_at(row)
    age = (int(now) - sent) // DAY if sent else None

    if status == "accepted":
        return ("accepted", "accepted%s"
                % ("" if age is None else ", sent %d day(s) ago" % age))

    if email and email in (members or set()):
        return ("already-a-member",
                "this address is already on the roster%s"
                % ("" if age is None else ", invite sent %d day(s) ago" % age))

    if status == "expired":
        return ("expired-uncollected",
                "expired and never cleaned up%s"
                % ("" if age is None else ", sent %d day(s) ago" % age))

    if status != "pending":
        return ("unknown-status",
                "status %r is not one this audit recognises" % status)

    expires = row.get("expires_at")
    try:
        expires = int(expires) if expires else None
    except (TypeError, ValueError):
        expires = None
    if expires and expires < int(now):
        return ("expired-but-still-pending",
                "still reads pending%s, and expires_at passed %d day(s) ago. A "
                "filter on status alone never returns this row."
                % ("" if age is None else " %d day(s) after it was sent" % age,
                   (int(now) - expires) // DAY))

    if age is not None and age >= stale_days:
        return ("pending-stale",
                "pending for %d day(s) and not yet past its expires_at" % age)

    return ("pending", "sent recently and still live")


def repair_lines(state, invite):
    """The repair for one classified invite. Pure. Printed, never performed."""
    row = invite or {}
    invite_id = str(row.get("id") or "unknown")
    lines = []
    if state not in FINDINGS:
        return lines
    if owner_grant(row):
        lines.append("this invite still offers owner rights. Read it before you "
                     "re-send anything: an uncollected owner grant only needs "
                     "access to one mailbox.")
    if state == "already-a-member":
        lines.append("this person is already in the roster. Delete the record; "
                     "there is no onboarding problem here.")
    elif state == "expired-but-still-pending":
        lines.append("the record is dead and still listed as pending. Delete it, "
                     "then decide separately whether to re-send.")
    elif state == "pending-stale":
        lines.append("ask whether they ever received it. The API has no delivery "
                     "status and cannot tell a filtered message from an ignored "
                     "one.")
    else:
        lines.append("expired and never cleaned up. Delete unless this person is "
                     "still expected.")
    grants = project_roles(row)
    if grants and state != "already-a-member":
        lines.append("re-send with the same projects[] entries (%s) or the new "
                     "invite grants less than the first one did."
                     % ", ".join("%s=%s" % g for g in grants))
    lines.append("DELETE /v1/organization/invites/%s" % invite_id)
    return lines


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    while True:
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stale-days", type=int, default=14,
                    help="days a pending invite may sit before it is flagged")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a "
                  "project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    now = int(time.time())

    members = member_emails(paged(s, "/organization/users", limit=100))
    invites = list(paged(s, "/organization/invites", limit=100))

    graded = [(invite, classify(invite, members, now, args.stale_days))
              for invite in invites]
    bad = [(invite, state, detail) for invite, (state, detail) in graded
           if state in FINDINGS]
    accepted = sum(1 for _, (state, _) in graded if state == "accepted")

    log.info("%d invite(s), %d accepted, %d finding(s)",
             len(invites), accepted, len(bad))

    bad.sort(key=lambda row: (0 if owner_grant(row[0]) else 1,
                              SEVERITY.get(row[1], 9),
                              str(row[0].get("email") or "")))
    for invite, state, detail in bad:
        log.warning("%-26s %-22s role=%-7s %s", state,
                    mask(invite.get("email")),
                    str(invite.get("role") or "?"), detail)
        grants = project_roles(invite)
        if grants:
            log.warning("  grants: %s",
                        ", ".join("%s=%s" % g for g in grants))
        for line in repair_lines(state, invite):
            log.warning("  repair: %s", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-stale-invite-audit.mjs",
"js": '''/**
 * Find OpenAI organization invites that lapsed without anybody noticing.
 *
 * Read only. Two paged GETs against /v1/organization/invites and
 * /v1/organization/users. No request body is constructed.
 *
 * The detection is a timestamp comparison rather than a status filter: an
 * invite can read status "pending" while its expires_at is already in the
 * past. Nothing secret is printed; the invite object carries no token.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;

const OWNER = 'owner';

const FINDINGS = new Set(['expired-but-still-pending', 'already-a-member',
                          'pending-stale', 'expired-uncollected']);

const SEVERITY = { 'expired-but-still-pending': 0, 'pending-stale': 1,
                   'expired-uncollected': 2, 'already-a-member': 3 };

/** When the invite was sent, as unix seconds. Pure. Both field names accepted. */
export function sentAt(invite) {
  for (const field of ['invited_at', 'created_at', 'sent_at']) {
    const value = invite?.[field];
    if (!value) continue;
    const n = Number(value);
    if (Number.isFinite(n)) return Math.trunc(n);
  }
  return null;
}

/** Hide the local part of an email address. Pure. Non-emails pass through. */
export function mask(email) {
  const text = String(email ?? '').trim();
  if (!text.includes('@')) return text || 'unknown';
  const at = text.indexOf('@');
  const local = text.slice(0, at);
  if (!local) return text;
  return `${local[0]}***${text.slice(at)}`;
}

/** [[project_id, role]] carried by one invite. Pure. */
export function projectRoles(invite) {
  return (invite?.projects ?? []).map((entry) => [
    String(entry?.id ?? 'unknown'),
    String(entry?.role ?? 'member').trim().toLowerCase(),
  ]);
}

/** Does this invite hand over owner anywhere? Pure. Top level or per project. */
export function ownerGrant(invite) {
  if (String(invite?.role ?? '').trim().toLowerCase() === OWNER) return true;
  return projectRoles(invite).some(([, role]) => role === OWNER);
}

/** Lowercased email addresses on the current roster. Pure. */
export function memberEmails(users) {
  const out = new Set();
  for (const user of users ?? []) {
    const email = String(user?.email ?? '').trim().toLowerCase();
    if (email) out.add(email);
  }
  return out;
}

/** Classify one invite. Pure. expires_at is tested before status. */
export function classify(invite, members, now, staleDays = 14) {
  const row = invite ?? {};
  const status = String(row.status ?? '').trim().toLowerCase();
  const email = String(row.email ?? '').trim().toLowerCase();
  const sent = sentAt(row);
  const age = sent === null ? null : Math.floor((Number(now) - sent) / DAY);

  if (status === 'accepted') {
    return ['accepted', age === null ? 'accepted' : `accepted, sent ${age} day(s) ago`];
  }
  if (email && (members ?? new Set()).has(email)) {
    return ['already-a-member',
            'this address is already on the roster'
            + (age === null ? '' : `, invite sent ${age} day(s) ago`)];
  }
  if (status === 'expired') {
    return ['expired-uncollected',
            'expired and never cleaned up'
            + (age === null ? '' : `, sent ${age} day(s) ago`)];
  }
  if (status !== 'pending') {
    return ['unknown-status', `status "${status}" is not one this audit recognises`];
  }

  const expiresRaw = Number(row.expires_at ?? 0);
  const expires = Number.isFinite(expiresRaw) && expiresRaw > 0 ? expiresRaw : null;
  if (expires && expires < Number(now)) {
    return ['expired-but-still-pending',
            'still reads pending'
            + (age === null ? '' : ` ${age} day(s) after it was sent`)
            + `, and expires_at passed ${Math.floor((Number(now) - expires) / DAY)} `
            + 'day(s) ago. A filter on status alone never returns this row.'];
  }
  if (age !== null && age >= staleDays) {
    return ['pending-stale',
            `pending for ${age} day(s) and not yet past its expires_at`];
  }
  return ['pending', 'sent recently and still live'];
}

/** The repair for one classified invite. Pure. Printed, never performed. */
export function repairLines(state, invite) {
  const row = invite ?? {};
  const lines = [];
  if (!FINDINGS.has(state)) return lines;
  if (ownerGrant(row)) {
    lines.push('this invite still offers owner rights. Read it before you re-send '
      + 'anything: an uncollected owner grant only needs access to one mailbox.');
  }
  if (state === 'already-a-member') {
    lines.push('this person is already in the roster. Delete the record; there is '
      + 'no onboarding problem here.');
  } else if (state === 'expired-but-still-pending') {
    lines.push('the record is dead and still listed as pending. Delete it, then '
      + 'decide separately whether to re-send.');
  } else if (state === 'pending-stale') {
    lines.push('ask whether they ever received it. The API has no delivery status '
      + 'and cannot tell a filtered message from an ignored one.');
  } else {
    lines.push('expired and never cleaned up. Delete unless this person is still '
      + 'expected.');
  }
  const grants = projectRoles(row);
  if (grants.length && state !== 'already-a-member') {
    lines.push(`re-send with the same projects[] entries (${
      grants.map(([id, role]) => `${id}=${role}`).join(', ')}) or the new invite `
      + 'grants less than the first one did.');
  }
  lines.push(`DELETE /v1/organization/invites/${String(row.id ?? 'unknown')}`);
  return lines;
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
                    + 'organization admin key, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function paged(key, path, params) {
  const out = [];
  const q = { ...params };
  for (;;) {
    const page = await read(key, path, q);
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
                  + 'key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const staleDays = Number(process.env.STALE_DAYS ?? 14);
  const now = Math.floor(Date.now() / 1000);

  const members = memberEmails(await paged(admin, '/organization/users', { limit: 100 }));
  const invites = await paged(admin, '/organization/invites', { limit: 100 });

  const graded = invites.map((invite) => [invite, classify(invite, members, now, staleDays)]);
  const bad = graded.filter(([, [state]]) => FINDINGS.has(state));
  const accepted = graded.filter(([, [state]]) => state === 'accepted').length;

  console.log(`${invites.length} invite(s), ${accepted} accepted, ${bad.length} finding(s)`);

  bad.sort(([a, [sa]], [b, [sb]]) =>
    (ownerGrant(a) ? 0 : 1) - (ownerGrant(b) ? 0 : 1)
    || (SEVERITY[sa] ?? 9) - (SEVERITY[sb] ?? 9)
    || String(a.email ?? '').localeCompare(String(b.email ?? '')));

  for (const [invite, [state, detail]] of bad) {
    console.warn(`${state.padEnd(26)} ${mask(invite.email).padEnd(22)} `
                 + `role=${String(invite.role ?? '?').padEnd(7)} ${detail}`);
    const grants = projectRoles(invite);
    if (grants.length) {
      console.warn(`  grants: ${grants.map(([id, role]) => `${id}=${role}`).join(', ')}`);
    }
    for (const line of repairLines(state, invite)) console.warn(`  repair: ${line}`);
  }
  process.exitCode = bad.length ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The headline test is one invite read twice. The same record, the same dates, once at <code>status: pending</code> and once at <code>status: expired</code>, has to come back as two different states with two different repairs &mdash; and the first of those is the row an audit written as a status filter never returns. Around it: an invite for somebody who is already on the roster, which is a stale record rather than a failed onboarding; the owner grant that hides in <code>projects[]</code> under a top-level <code>reader</code>; the sent timestamp read under either field name; the project entries that a re-send has to carry or it grants less than the original; and a fresh invite, which is not a finding at all.",
"test_py_file": "test_openai_stale_invite_audit.py",
"test_py": '''from openai_stale_invite_audit import (classify, mask, member_emails,
                                        owner_grant, project_roles,
                                        repair_lines, sent_at)

NOW = 1_780_000_000
DAY = 86400

ROSTER = member_emails([{"email": "Mel@example.com"}, {"email": "pat@example.com"}])


def invite(iid, email, role="reader", status="pending", sent_days=137,
           expires_days=107, projects=None):
    return {"id": iid, "email": email, "role": role, "status": status,
            "invited_at": NOW - sent_days * DAY,
            "expires_at": NOW - expires_days * DAY if expires_days else None,
            "projects": projects or []}


def test_a_pending_invite_past_its_expiry_is_the_row_a_status_filter_misses():
    # The note in one assertion, and then the same record relabelled. Same
    # dates, same grants, two states, two repairs.
    row = invite("invite_01hd", "rob@example.com", role="owner")
    state, detail = classify(row, ROSTER, NOW)
    assert state == "expired-but-still-pending"
    assert "filter on status alone" in detail
    assert "107 day(s) ago" in detail

    relabelled = dict(row, status="expired")
    other, detail = classify(relabelled, ROSTER, NOW)
    assert other == "expired-uncollected"
    assert "never cleaned up" in detail
    assert repair_lines(state, row) != repair_lines(other, relabelled)


def test_an_invite_for_somebody_already_on_the_roster_is_not_an_onboarding_failure():
    row = invite("invite_01me", "mel@EXAMPLE.com", sent_days=61, expires_days=31)
    state, detail = classify(row, ROSTER, NOW)
    assert state == "already-a-member"
    assert "already on the roster" in detail
    lines = repair_lines(state, row)
    assert any("no onboarding problem here" in line for line in lines)
    assert not any("re-send" in line for line in lines)


def test_an_owner_grant_hides_inside_the_project_entries():
    plain = invite("invite_01a", "jo@example.com", role="reader",
                   projects=[{"id": "proj_web", "role": "member"}])
    hidden = invite("invite_01b", "kim@example.com", role="reader",
                    projects=[{"id": "proj_ingest", "role": "owner"},
                              {"id": "proj_web", "role": "member"}])
    assert owner_grant(plain) is False
    assert owner_grant(hidden) is True
    assert owner_grant(invite("invite_01c", "x@y.com", role="owner")) is True
    assert project_roles(hidden) == [("proj_ingest", "owner"),
                                     ("proj_web", "member")]
    assert project_roles({}) == []
    lines = repair_lines("expired-but-still-pending", hidden)
    assert any("offers owner rights" in line for line in lines)
    assert any("proj_ingest=owner" in line for line in lines)


def test_a_stale_but_live_invite_is_its_own_state():
    row = invite("invite_01j", "jay@example.com", sent_days=29,
                 expires_days=-1)
    row["expires_at"] = NOW + 3 * DAY
    state, detail = classify(row, ROSTER, NOW)
    assert state == "pending-stale"
    assert "29 day(s)" in detail
    assert any("delivery status" in line for line in repair_lines(state, row))


def test_a_fresh_invite_and_an_accepted_one_are_not_findings():
    fresh = invite("invite_01f", "new@example.com", sent_days=2)
    fresh["expires_at"] = NOW + 5 * DAY
    assert classify(fresh, ROSTER, NOW)[0] == "pending"
    assert repair_lines("pending", fresh) == []
    done = invite("invite_01g", "old@example.com", status="accepted")
    assert classify(done, ROSTER, NOW)[0] == "accepted"
    assert classify({"status": "revoked", "email": "z@x.com"},
                    ROSTER, NOW)[0] == "unknown-status"


def test_the_sent_timestamp_is_read_under_either_field_name():
    assert sent_at({"invited_at": 1_700_000_000}) == 1_700_000_000
    assert sent_at({"created_at": 1_700_000_001}) == 1_700_000_001
    assert sent_at({"invited_at": None, "created_at": 1_700_000_002}) == 1_700_000_002
    assert sent_at({"invited_at": "not a date"}) is None
    assert sent_at({}) is None
    assert sent_at(None) is None
    # A missing timestamp must not make the invite look brand new.
    row = {"id": "i", "email": "q@x.com", "role": "reader", "status": "pending",
           "expires_at": NOW - DAY}
    assert classify(row, ROSTER, NOW)[0] == "expired-but-still-pending"


def test_every_repair_ends_with_the_delete_and_masks_the_address():
    row = invite("invite_01hd", "rob@example.com", role="owner")
    assert repair_lines("expired-but-still-pending", row)[-1] == \\
        "DELETE /v1/organization/invites/invite_01hd"
    assert mask("rob@example.com") == "r***@example.com"
    assert mask(None) == "unknown"
    assert member_emails(None) == set()
''',
"test_js_file": "openai-stale-invite-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, mask, memberEmails, ownerGrant, projectRoles, repairLines,
         sentAt } from './openai-stale-invite-audit.mjs';

const NOW = 1780000000;
const DAY = 86400;

const ROSTER = memberEmails([{ email: 'Mel@example.com' }, { email: 'pat@example.com' }]);

const invite = (id, email, { role = 'reader', status = 'pending', sentDays = 137,
                             expiresDays = 107, projects = [] } = {}) =>
  ({ id, email, role, status, invited_at: NOW - sentDays * DAY,
     expires_at: expiresDays === null ? null : NOW - expiresDays * DAY, projects });

test('a pending invite past its expiry is the row a status filter misses', () => {
  const row = invite('invite_01hd', 'rob@example.com', { role: 'owner' });
  const [state, detail] = classify(row, ROSTER, NOW);
  assert.equal(state, 'expired-but-still-pending');
  assert.match(detail, /filter on status alone/);
  assert.match(detail, /107 day\\(s\\) ago/);

  const relabelled = { ...row, status: 'expired' };
  const [other, otherDetail] = classify(relabelled, ROSTER, NOW);
  assert.equal(other, 'expired-uncollected');
  assert.match(otherDetail, /never cleaned up/);
  assert.notDeepEqual(repairLines(state, row), repairLines(other, relabelled));
});

test('an invite for somebody already on the roster is not an onboarding failure', () => {
  const row = invite('invite_01me', 'mel@EXAMPLE.com', { sentDays: 61, expiresDays: 31 });
  const [state, detail] = classify(row, ROSTER, NOW);
  assert.equal(state, 'already-a-member');
  assert.match(detail, /already on the roster/);
  const lines = repairLines(state, row);
  assert.ok(lines.some((l) => l.includes('no onboarding problem here')));
  assert.ok(!lines.some((l) => l.includes('re-send')));
});

test('an owner grant hides inside the project entries', () => {
  const plain = invite('invite_01a', 'jo@example.com',
    { projects: [{ id: 'proj_web', role: 'member' }] });
  const hidden = invite('invite_01b', 'kim@example.com',
    { projects: [{ id: 'proj_ingest', role: 'owner' },
                 { id: 'proj_web', role: 'member' }] });
  assert.equal(ownerGrant(plain), false);
  assert.equal(ownerGrant(hidden), true);
  assert.equal(ownerGrant(invite('invite_01c', 'x@y.com', { role: 'owner' })), true);
  assert.deepEqual(projectRoles(hidden),
                   [['proj_ingest', 'owner'], ['proj_web', 'member']]);
  assert.deepEqual(projectRoles({}), []);
  const lines = repairLines('expired-but-still-pending', hidden);
  assert.ok(lines.some((l) => l.includes('offers owner rights')));
  assert.ok(lines.some((l) => l.includes('proj_ingest=owner')));
});

test('a stale but live invite is its own state', () => {
  const row = invite('invite_01j', 'jay@example.com', { sentDays: 29 });
  row.expires_at = NOW + 3 * DAY;
  const [state, detail] = classify(row, ROSTER, NOW);
  assert.equal(state, 'pending-stale');
  assert.match(detail, /29 day\\(s\\)/);
  assert.ok(repairLines(state, row).some((l) => l.includes('delivery status')));
});

test('a fresh invite and an accepted one are not findings', () => {
  const fresh = invite('invite_01f', 'new@example.com', { sentDays: 2 });
  fresh.expires_at = NOW + 5 * DAY;
  assert.equal(classify(fresh, ROSTER, NOW)[0], 'pending');
  assert.deepEqual(repairLines('pending', fresh), []);
  const done = invite('invite_01g', 'old@example.com', { status: 'accepted' });
  assert.equal(classify(done, ROSTER, NOW)[0], 'accepted');
  assert.equal(classify({ status: 'revoked', email: 'z@x.com' }, ROSTER, NOW)[0],
               'unknown-status');
});

test('the sent timestamp is read under either field name', () => {
  assert.equal(sentAt({ invited_at: 1700000000 }), 1700000000);
  assert.equal(sentAt({ created_at: 1700000001 }), 1700000001);
  assert.equal(sentAt({ invited_at: null, created_at: 1700000002 }), 1700000002);
  assert.equal(sentAt({ invited_at: 'not a date' }), null);
  assert.equal(sentAt({}), null);
  assert.equal(sentAt(null), null);
  const row = { id: 'i', email: 'q@x.com', role: 'reader', status: 'pending',
                expires_at: NOW - DAY };
  assert.equal(classify(row, ROSTER, NOW)[0], 'expired-but-still-pending');
});

test('every repair ends with the delete and masks the address', () => {
  const row = invite('invite_01hd', 'rob@example.com', { role: 'owner' });
  const lines = repairLines('expired-but-still-pending', row);
  assert.equal(lines[lines.length - 1],
               'DELETE /v1/organization/invites/invite_01hd');
  assert.equal(mask('rob@example.com'), 'r***@example.com');
  assert.equal(mask(null), 'unknown');
  assert.equal(memberEmails(null).size, 0);
});
''',
"faq": [
 ("Why not just filter on status == expired and be done?",
  "Because the rows that matter most are not labelled that way. An invite can sit at status pending with an expires_at that has already gone by, so a status filter returns a tidy list and silently omits exactly the records that are neither live nor cleaned up. The script compares expires_at against the clock first and only then looks at the status string, which is why it reports lapsed-but-pending and already-relabelled-expired as two separate states. They also need two different sentences in the email you send afterwards."),
 ("What is the actual harm? The person just asks again.",
  "They usually do not. They borrow a credential, because the work is due and the access is not. A colleague's key goes into an environment file, or a service account key goes into a chat message, and from then on requests are authenticating as somebody who cannot account for them. That is the operational cost, and it is quiet. The separate, sharper cost is an outstanding invite at owner for a candidate who was never hired or an employee who has left, which is a standing grant of organization control that only needs access to one mailbox."),
 ("Does this apply to Anthropic as well?",
  "Partly, which is why the slug says OpenAI. Anthropic's Admin API does list invites with a status, an invited_at and an expires_at, and the same timestamp-against-status test is worth running there. What has no equivalent is the rest of this note: an OpenAI invite carries a projects[] array of per-project role grants that take effect on acceptance, so it offers more than membership, and OpenAI's audit log reconstructs the history through invite.sent, invite.accepted and invite.deleted. Neither of those is reachable from a read-only Anthropic Admin key, so the script is written against the API that has them."),
 ("Can the script tell me whether the invitation email was delivered?",
  "No, and nothing read-only can. There is no delivery status on the invite object and no way to distinguish a message that was filtered from one that was read and ignored. The script reports what is knowable — when it was sent, when it expires or expired, what role and project grants it carries, and whether the invitee is already in the organization by some other route — and never speculates about why it went uncollected. Asking the person is still the fastest step, and the output is written to be pasted into that message."),
 ("Is it safe to just delete the whole backlog?",
  "Deleting is safe; re-sending carelessly is not. Deleting a pending invite withdraws an offer that was never accepted, which is what you want for departed people, wrong addresses and abandoned hires. The thing to read before you delete is the projects[] array, because those per-project role grants go with it: a re-issued invite that omits them gives the person less than the original did, and they will be back in a week asking why they cannot see a project. The script prints the grants next to every row for that reason."),
],
"related": [REL_OWNERS, REL_OWNER_LOST, REL_TOPOLOGY],
"citations": [CITE_OA_INVITE, CITE_OA_AUDIT, CITE_OA_ADMIN_GUIDE, CITE_OA_SDK],
},
]
