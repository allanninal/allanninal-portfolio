#!/usr/bin/env python3
"""/llm/ field notes, batch O — the writing.

The key roster, read four ways. Every note in this batch starts from the same
list of credentials and reaches a different finding, because the list carries
four independent facts about each key and no dashboard joins them: when it was
last used, who owns it, when it was minted, and what the audit trail says
happened to it.

`api-key-never-used` reads usage. It is an idleness clock, and it is the only
note here whose finding is that a credential has no traffic behind it at all.
It is deliberately not the published `key-owner-lost-project-access`: that note
reads the flag the provider raises when a key's *owner* loses access, which is
a fact about a person. This one never looks at the owner. A key belonging to a
current, happy, fully employed engineer that has authenticated nothing in two
years is exactly the finding, and the published note cannot see it. The two
audit-completeness parameters matter more than the threshold does, because
without them the sweep returns a clean answer over a partial universe.

`legacy-user-owned-keys-in-project` reads ownership type and joins it to money.
It must not drift into the published `one-model-or-project-dominates-cost`,
which owns `group_by=api_key_id` concentration: that note asks whether one key
holds most of the bill, and this one does not care. Two user-owned keys
splitting production spend evenly are two findings here and no finding at all
there. The subject is `owner.type == "user"`, and the cost join is only there
to separate a personal credential holding production from a personal
credential holding nothing.

`service-account-key-never-rotated` reads creation dates, which is the one
clock the other three ignore. Its subject is the key that is working perfectly:
used every second of every day, owned by a service account exactly as the
guidance says it should be, and minted two years ago and never replaced. The
confirmation comes from the *absence* of creation events in the audit log, and
the note is careful about what an absence can support, because the audit event
names a project and not a service account.

`unreviewed-key-lifecycle-in-audit-log` makes the trail itself the subject. It
is the only one of the four that reads events rather than objects, and the only
one whose failure mode is that the control exists, works, and has never been
looked at. Actors are resolved against the current roster, which is how an
event performed by somebody who has since left stops being a row and starts
being a finding.

Read only throughout. Every request is a GET, there is no `--apply` and no
write path in any of the four, and no script prints a key value: the providers
return a redacted hint and the hint is all that reaches the output.
"""

CITE_PROJECT_KEYS = ("Project API keys — OpenAI API reference",
                     "https://platform.openai.com/docs/api-reference/project-api-keys")
CITE_PROJECTS = ("Projects — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/projects")
CITE_ADMIN_APIS = ("Administration APIs — OpenAI developer docs",
                   "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_AUDIT_LOGS = ("Audit logs — OpenAI API reference",
                   "https://platform.openai.com/docs/api-reference/audit-logs")
CITE_AUDIT_HELP = ("Admin and audit logs API for the API platform — OpenAI help",
                   "https://help.openai.com/en/articles/9687866-admin-and-audit-logs-api-for-the-api-platform")
CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_MANAGING_PROJECTS = ("Managing projects in the API platform — OpenAI help",
                          "https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform")
CITE_ADMINISTRATION = ("Administration — OpenAI API reference",
                       "https://platform.openai.com/docs/api-reference/administration")
CITE_AN_LIST_KEYS = ("List API keys — Claude Admin API",
                     "https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys")
CITE_AN_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                        "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_AN_ADMIN = ("Admin API — Claude Docs",
                 "https://platform.claude.com/docs/en/manage-claude/admin-api")
CITE_AN_COMPLIANCE = ("Compliance API — Claude Docs",
                      "https://platform.claude.com/docs/en/manage-claude/compliance-api")
CITE_AN_ACTIVITY = ("Compliance activity feed — Claude Docs",
                    "https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed")
CITE_AN_LIST_USERS = ("List users — Claude Admin API",
                      "https://platform.claude.com/docs/en/api/admin-api/users/list-users")

REL_OWNER_GONE = ("/llm/key-owner-lost-project-access/",
                  "The key whose owner lost access, which is a fact about a person rather than about traffic")
REL_ARCHIVED = ("/llm/archived-project-still-holds-keys/",
                "The projects your key sweep never enumerated in the first place")
REL_DOMINATES = ("/llm/one-model-or-project-dominates-cost/",
                 "When one key holds most of the bill, which is a different question from who owns it")
REL_SPEND_LIMIT = ("/llm/no-organization-spend-limit/",
                   "The ceiling that decides what a forgotten credential can cost you")
REL_QUIET = ("/llm/live-project-zero-usage-buckets/",
             "Traffic that stopped, read from the usage report rather than the key list")
REL_NEVER_USED = ("/llm/api-key-never-used/",
                  "The same roster read for traffic instead of ownership")
REL_USER_OWNED = ("/llm/legacy-user-owned-keys-in-project/",
                  "The same roster read for who owns the credential")
REL_ROTATION = ("/llm/service-account-key-never-rotated/",
                "The same roster read for how long ago each key was minted")
REL_LIFECYCLE = ("/llm/unreviewed-key-lifecycle-in-audit-log/",
                 "The events behind every change to that roster, and who made them")

GUIDES = [
{
"slug": "api-key-never-used",
"title": "API keys that no request has ever used",
"description": "OpenAI puts last_used_at on the key object. Anthropic has no such field, so the same question needs a set difference against the usage report.",
"h1": "API keys that no request has ever used",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai api key last_used_at null",
             "openai owner_project_access any",
             "unused openai api key audit",
             "anthropic api key never used",
             "revoke idle llm api keys"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY (an sk-admin- key with read scopes) or ANTHROPIC_ADMIN_KEY (sk-ant-admin), or both. Project and workspace keys are rejected by every administration endpoint.",
"lead": "Nobody left. Nobody was removed from anything. The engineer who minted the key in March is sitting eight feet away, still employed, still on the project, and could tell you within a second why she made it: a vendor evaluation that went nowhere. The key has authenticated exactly zero requests in the five months since, and it has full access to everything in that project, and there is no report anywhere that will ever mention it, because a credential with no traffic produces no cost line, no log entry and no alert. Creating it took one click. Deleting it requires somebody to be confident nothing breaks.",
"short_answer": """<p>With an <strong>organization admin key</strong>, walk every project with <code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>, then read each one's keys with <code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code>. Flag every key where <code>last_used_at</code> is <code>null</code> and <code>created_at</code> is more than 30 days old, and separately every key whose <code>last_used_at</code> is real but older than 90 days. Sweep <code>GET /v1/organization/admin_api_keys</code> the same way, because that object carries <code>last_used_at</code> too.</p>
<p>The two query parameters matter more than either threshold. <strong><code>owner_project_access=any</code> and <code>include_archived=true</code> both default to the narrow answer</strong>, and neither omission produces an error or an obviously short list. Leave them off and the sweep returns a confident, clean result over a subset of your organization.</p>
<p>On Anthropic the same question cannot be asked the same way, because <strong>the Anthropic API key object has no <code>last_used_at</code> field at all</strong>. Its schema is <code>id</code>, <code>created_at</code>, <code>created_by</code>, <code>expires_at</code>, <code>name</code>, <code>partial_key_hint</code>, <code>principal</code>, <code>scope</code>, <code>status</code>, <code>type</code>. So you list the active keys, then collect every non-null <code>api_key_id</code> from <code>GET /v1/organizations/usage_report/messages?group_by[]=api_key_id</code> over the retrievable window, and take the set difference. That answers "unused in the last N days". It cannot answer "never", and the script says so rather than rounding one to the other.</p>""",
"problem": """<p>An unused credential is the only kind of problem in this section that generates no signal whatsoever. A retired model 404s. A truncated response has a field on it. A runaway key shows up in the cost report. A key that nothing uses emits nothing at all: no requests, no tokens, no dollars, no audit entries after the one that created it. The single fact that it exists lives in a list nobody opens.</p>
<p>So the population grows monotonically. Keys get minted for a spike, for onboarding, for a vendor trial, for a debugging session at 2am, for a notebook, for the CI job that was replaced six weeks later by a different CI job with a different key. Every one of them is still valid, still carries the project's full access, and still sits in whatever Slack thread, <code>.env.example</code>, laptop backup or password manager it was pasted into on the day it was created. Project API keys have no expiry, so nothing ever removes one on its own.</p>
<p>What makes the sweep itself unreliable is subtler and worse. Both of the parameters that control what you can see default to hiding things. Ask a project for its keys without <code>owner_project_access=any</code> and the endpoint applies membership-based visibility rules that can omit enabled keys. Ask the organization for its projects without <code>include_archived=true</code> and archived projects are not in the list at all, along with every key inside them. Neither of those is an error. You get back a smaller number that looks exactly like good news.</p>""",
"why": """<p><strong>This note never looks at the owner, which is what separates it from the offboarding sweep.</strong> <a href="/llm/key-owner-lost-project-access/">The published note on keys whose owner lost project access</a> reads <code>owner_project_access == "inactive"</code>, a flag the provider raises about a <em>person</em>. Its finding is that somebody left and their credential did not. This one reads traffic and nothing else, so its central case is the opposite: a key belonging to a current employee in good standing, on a project they still work on, that has never authenticated anything. The offboarding sweep is structurally incapable of seeing that key, and this one is structurally incapable of caring who owns it.</p>
<p><strong>Never-used and dormant are the same field and different conversations.</strong> A <code>last_used_at</code> of <code>null</code> on a key three months old means nothing was ever built on it, which makes it the safest object in the organization to revoke: there is no traffic to break, by definition. A <code>last_used_at</code> from fourteen months ago means something <em>was</em> built on it and has since been decommissioned, or has been quietly failing, or runs annually. The first is a cleanup. The second deserves a question asked out loud before anything is deleted, and the script grades and orders them separately for that reason.</p>
<p><strong>The absence of the key from the cost report is corroboration, not proof.</strong> <code>GET /v1/organization/costs?group_by=api_key_id</code> only covers its reporting window, and it does not emit zero rows, so a key you cannot find there is consistent with dormancy rather than demonstrating it. The key object's <code>last_used_at</code> is the only usage signal that is actually attached to the key, and neither provider exposes a per-request log that would let you do better.</p>
<p><strong>Anthropic answers a weaker question, and the script refuses to overstate it.</strong> With no <code>last_used_at</code> on the key object, "unused" has to be reconstructed by joining the active key list against <code>api_key_id</code> values in the usage report, which reaches back only as far as the report does. A key that last ran a job thirteen months ago is indistinguishable there from a key that has never run anything. The Anthropic half of the output therefore says <code>unused-in-window</code> and states the window, and it will not print the word "never".</p>
<p><strong>Admin keys are the ones with real blast radius, and they are on a separate endpoint.</strong> <code>GET /v1/organization/admin_api_keys</code> returns objects that also carry <code>last_used_at</code> as well as an optional <code>expires_at</code> that project keys do not have. An idle admin key can enumerate every credential in the organization. A sweep that walks projects and stops there has skipped the most powerful credentials you own.</p>""",
"steps": [
 {"h": "Use an admin key, provisioned read-only",
  "body": """<p>Every path under <code>/v1/organization/*</code> and <code>/v1/organizations/*</code> rejects a project or workspace key, so this cannot run on the credential your application holds. Mint an OpenAI admin key (<code>sk-admin-</code>) with read scopes, or an Anthropic Admin key (<code>sk-ant-admin</code>), which can also be provisioned read-only. Treat it as the most sensitive secret you have: it can list every key in the organization.</p>"""},
 {"h": "Ask for the whole universe before you ask for the finding",
  "body": """<p><code>include_archived=true</code> on the project listing and <code>owner_project_access=any</code> on every key listing. Run the project call once with the parameter and once without and compare the counts; the difference is the number of projects your existing audits have never seen. Doing that once teaches the lesson better than being told the parameter exists.</p>"""},
 {"h": "Grade OpenAI keys off last_used_at, in two buckets",
  "body": """<p><code>last_used_at</code> is a unix timestamp and <code>null</code> on a key that has never authenticated anything. Never-used and older than 30 days is one finding; used at least once but idle for more than 90 days is a different one. Report <code>id</code>, <code>name</code>, <code>redacted_value</code>, <code>created_at</code> and <code>owner.type</code>, and print nothing else about the key.</p>"""},
 {"h": "Reconstruct the same question on Anthropic, and name the window",
  "body": """<p><code>GET /v1/organizations/api_keys?status=active&amp;limit=1000</code> for the roster, paging on <code>has_more</code> and <code>last_id</code>. Then <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=api_key_id</code> and collect every non-null <code>api_key_id</code>. The set difference is the finding, and it is a finding about the window, not about the key's whole life.</p>"""},
 {"h": "Order by revocation safety and print, never delete",
  "body": """<p>Never-used keys first, because nothing can break; then dormant keys ordered by how long they have been idle. For each, print the revocation call as text: <code>DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}</code> on OpenAI, or on Anthropic a status change to <code>archived</code> on the key object. Run them yourself, after somebody has confirmed what each key was for.</p>"""},
],
"verify": """<p>Re-run after the cleanup. Every project should report zero never-used keys older than the threshold, and the admin key sweep should be empty too.</p>
<pre><code class="language-bash">python3 llm_idle_key_audit.py --never-after 30 --dormant-after 90
# openai: 6 project(s) read, 2 archived, 38 key(s) including 3 admin key(s)
# never-used  proj_evals    vendor-trial      sk-...4f7a  created 154 day(s) ago, never used
#   repair: nothing has ever authenticated with this key, so revoking it cannot break traffic.
# dormant     proj_prod     nightly-export    sk-...c19b  last used 412 day(s) ago
#   repair: something was built on this one. Ask before revoking, then watch last_used_at stop moving.
# anthropic: 21 active key(s), 14 seen in the usage report over 30 day(s)
# unused-in-window  ingest-worker  sk-ant-...igAA  no traffic in the last 30 day(s)
#   note: the Anthropic key object has no last_used_at, so this is unused in the window, not never used.
# 59 key(s) read, 3 finding(s)</code></pre>""",
"code_intro": "Two providers, one report, and the difference between them is the reason the pure functions are split rather than shared. <code>openai_verdict</code> reads a field. <code>anthropic_verdict</code> reads a set membership and is given the window so it can state it in the finding. Around them: <code>age_days</code>, which has to accept a unix integer from one provider and an RFC 3339 string from the other, because a reader that handles only one silently treats every key from the other as ageless; <code>audit_gaps</code>, which turns the two defaulted parameters into an assertion instead of a comment; <code>revocation_order</code>, which sorts by how safe each row is to delete rather than by age; and <code>safe_hint</code>, which is the one function here that exists purely to make a mistake impossible. It passes through a provider-redacted hint and refuses anything that does not look like one.",
"py_file": "llm_idle_key_audit.py",
"py": '''"""Find API keys that no request has ever used.

Read only. Every request is a GET against the OpenAI Administration API or the
Anthropic Admin API. Nothing is created, changed or removed, and no key value
is printed: the providers return a redacted hint and that hint is all that
reaches the output.

The two providers answer the same question with different evidence, and the
difference is the point of the script. OpenAI carries last_used_at on the key
object, so "never used" is a field you read. Anthropic has no such field, so
"unused" has to be computed as a set difference between the active key list and
the api_key_id values appearing in the usage report, which reaches back only as
far as the report does. On Anthropic this script reports "unused in the last N
days" and will not say "never".
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm_idle_key_audit")

OPENAI = "https://api.openai.com/v1"
ANTHROPIC = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

NEVER = "never-used"
DORMANT = "dormant"
UNUSED_IN_WINDOW = "unused-in-window"
IN_USE = "in-use"
SEEN = "seen-in-window"
TOO_NEW = "too-new"
UNREADABLE = "unreadable-dates"
NOT_ACTIVE = "not-active"

FINDINGS = (NEVER, DORMANT, UNUSED_IN_WINDOW)

# Sort weight for the revocation queue. Lower goes first, and the order is by
# how safe the row is to delete rather than by how old it is: a key nothing has
# ever used cannot break anything when it is revoked, and a key that ran a job
# last spring can.
SAFETY = {NEVER: 0, UNUSED_IN_WINDOW: 1, DORMANT: 2}


def safe_hint(value):
    """Return a key hint that is safe to print. Pure.

    Both providers hand back a redacted form: OpenAI's redacted_value and
    Anthropic's partial_key_hint. This passes those through and refuses
    anything else, because the one unrecoverable mistake an audit script can
    make is to print a live credential into a log that then gets shipped
    somewhere. A hint with no ellipsis or star in it is not a hint.
    """
    text = str(value or "").strip()
    if not text:
        return "(no hint)"
    if "..." not in text and "*" not in text:
        return "(hint withheld)"
    if len(text) > 40:
        return "(hint withheld)"
    return text


def age_days(stamp, now):
    """Whole days between a timestamp and now. Pure. None when unreadable.

    Accepts a unix integer (OpenAI) or an RFC 3339 string (Anthropic). A reader
    that handles only one of the two treats every key from the other provider
    as ageless, which reads as "too new to judge" and quietly drops it from the
    report.
    """
    if stamp is None or stamp == "":
        return None
    when = None
    if isinstance(stamp, bool):
        return None
    if isinstance(stamp, (int, float)):
        when = dt.datetime.fromtimestamp(float(stamp), dt.timezone.utc)
    else:
        text = str(stamp).strip()
        if text.isdigit():
            when = dt.datetime.fromtimestamp(float(text), dt.timezone.utc)
        else:
            try:
                when = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                return None
            if when.tzinfo is None:
                when = when.replace(tzinfo=dt.timezone.utc)
    return int((now - when).total_seconds() // 86400)


def openai_verdict(key, now, never_after=30, dormant_after=90):
    """Classify one OpenAI key off last_used_at. Pure. Returns (state, detail).

    last_used_at is null on a key that has never authenticated anything, and a
    unix timestamp otherwise. Zero is treated as absent: it is not a plausible
    last-use time and reading it as one would date the key to 1970 and file it
    under dormant instead of never used.
    """
    row = key or {}
    created = age_days(row.get("created_at"), now)
    last = row.get("last_used_at")
    if last in (None, "", 0):
        if created is None:
            return (UNREADABLE,
                    "never used, and created_at cannot be read, so no age can "
                    "be given for it")
        if created < never_after:
            return (TOO_NEW,
                    "never used, but only %d day(s) old" % created)
        return (NEVER,
                "never used in the %d day(s) since it was created" % created)
    idle = age_days(last, now)
    if idle is None:
        return (UNREADABLE, "last_used_at is present but cannot be read")
    if idle >= dormant_after:
        return (DORMANT, "last used %d day(s) ago" % idle)
    return (IN_USE, "last used %d day(s) ago" % idle)


def anthropic_verdict(key, seen_ids, window_days, now, never_after=30):
    """Classify one Anthropic key off usage-report membership. Pure.

    There is no last_used_at on the Anthropic key object, so the strongest
    available claim is bounded by the usage report's window. The detail string
    says so on every row, because "unused in 30 days" and "never used" are
    different facts and only one of them is in evidence here.
    """
    row = key or {}
    status = str(row.get("status") or "active").strip().lower()
    if status != "active":
        return (NOT_ACTIVE, "status is %s, so it cannot authenticate" % status)
    created = age_days(row.get("created_at"), now)
    if created is not None and created < never_after:
        return (TOO_NEW, "only %d day(s) old" % created)
    if str(row.get("id") or "") in (seen_ids or set()):
        return (SEEN, "carried traffic inside the last %d day(s)" % window_days)
    return (UNUSED_IN_WINDOW,
            "no traffic in the last %d day(s). The Anthropic key object has no "
            "last_used_at field, so this is unused within the retrievable "
            "window and not a claim that it was never used." % window_days)


def audit_gaps(project_params, key_params):
    """Warn about a sweep that will silently under-report. Pure.

    Both parameters default to the narrower answer, and neither omission
    produces an error or a visibly short list. You get a clean report over a
    partial universe, which is the most convincing kind of wrong answer, so the
    check is an assertion in the code rather than a sentence in a comment.
    """
    gaps = []
    if str((project_params or {}).get("include_archived", "")).lower() != "true":
        gaps.append("include_archived is not true: archived projects are "
                    "omitted from the project listing, and every key inside "
                    "them with it")
    if str((key_params or {}).get("owner_project_access", "")) != "any":
        gaps.append("owner_project_access is not 'any': the key listing "
                    "applies membership visibility rules and can hide enabled "
                    "keys from this audit")
    return gaps


def seen_key_ids(pages):
    """Every non-null api_key_id in an Anthropic usage report. Pure."""
    out = set()
    for page in pages or []:
        for bucket in (page or {}).get("data") or []:
            for result in (bucket or {}).get("results") or []:
                key_id = (result or {}).get("api_key_id")
                if key_id:
                    out.add(str(key_id))
    return out


def revocation_order(rows):
    """Order findings by how safe each is to revoke. Pure.

    Never-used first: nothing has authenticated with it, so revocation cannot
    break traffic. Then the window-bounded Anthropic rows, then dormant keys
    longest-idle first, because those are the ones where something was built
    and somebody has to be asked before anything is deleted.
    """
    findings = [r for r in (rows or []) if (r or {}).get("state") in SAFETY]
    return sorted(findings,
                  key=lambda r: (SAFETY[r["state"]], -int(r.get("idle") or 0),
                                 str(r.get("name") or "")))


def repair_lines(state, row):
    """The repair for one classified key. Pure. Printed, never performed."""
    data = row or {}
    if state == NEVER:
        return [
            "nothing has ever authenticated with this key, so revoking it "
            "cannot break traffic. These are the safest credentials in the "
            "organization to remove.",
            "revoke with a DELETE on /v1/organization/projects/%s/api_keys/%s "
            "once somebody confirms what it was minted for."
            % (data.get("container") or "{project_id}", data.get("id") or "{key_id}"),
        ]
    if state == DORMANT:
        return [
            "something was built on this key and has since stopped calling. "
            "Ask what it was before revoking: annual jobs and disaster-recovery "
            "paths look exactly like this.",
            "if it is genuinely dead, revoke it and confirm last_used_at stops "
            "advancing rather than assuming it will.",
        ]
    if state == UNUSED_IN_WINDOW:
        return [
            "this is unused within the report window, not proven unused. "
            "Widen the window as far as the report allows before concluding "
            "anything, then archive the key rather than deleting it.",
            "the Anthropic key object carries an optional expires_at. Set one "
            "on the replacement so the next idle key expires itself.",
        ]
    return []


def get(session, url, params, who):
    r = session.get(url, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from %s: this endpoint needs an administration "
                         "key, not a project or workspace key"
                         % (r.status_code, who))
    r.raise_for_status()
    return r.json()


def openai_paged(session, path, params):
    """Walk an OpenAI administration listing on has_more / last_id."""
    params = dict(params)
    while True:
        page = get(session, OPENAI + path, params, "OpenAI")
        yield page
        if not page.get("has_more") or not page.get("last_id"):
            return
        params["after"] = page["last_id"]


def anthropic_paged(session, path, params):
    """Walk an Anthropic Admin listing on has_more / last_id."""
    params = dict(params)
    while True:
        page = get(session, ANTHROPIC + path, params, "Anthropic")
        yield page
        if not page.get("has_more") or not page.get("last_id"):
            return
        params["after_id"] = page["last_id"]


def anthropic_report(session, path, params):
    """Walk the Anthropic usage report on has_more / next_page."""
    params = dict(params)
    while True:
        page = get(session, ANTHROPIC + path, params, "Anthropic")
        yield page
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days, now):
    """Floor to midnight UTC: starting_at must sit on a bucket boundary."""
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def sweep_openai(session, now, args):
    """Read every project, every project key and every admin key."""
    project_params = {"limit": 100, "include_archived": "true"}
    key_params = {"limit": 100, "owner_project_access": "any"}
    for gap in audit_gaps(project_params, key_params):
        log.warning("audit gap: %s", gap)

    projects = []
    for page in openai_paged(session, "/organization/projects", project_params):
        projects.extend(page.get("data") or [])
    archived = sum(1 for p in projects if p.get("status") == "archived")

    rows = []
    for project in projects:
        pid = project.get("id")
        if not pid:
            continue
        for page in openai_paged(session,
                                 "/organization/projects/%s/api_keys" % pid,
                                 key_params):
            for key in page.get("data") or []:
                state, detail = openai_verdict(key, now, args.never_after,
                                               args.dormant_after)
                rows.append({"provider": "openai", "state": state,
                             "detail": detail, "id": key.get("id"),
                             "name": key.get("name") or "(unnamed)",
                             "hint": safe_hint(key.get("redacted_value")),
                             "container": pid,
                             "label": project.get("name") or pid,
                             "idle": age_days(key.get("last_used_at"), now)
                                     or age_days(key.get("created_at"), now) or 0})

    admin_keys = []
    for page in openai_paged(session, "/organization/admin_api_keys", {"limit": 100}):
        admin_keys.extend(page.get("data") or [])
    for key in admin_keys:
        state, detail = openai_verdict(key, now, args.never_after,
                                       args.dormant_after)
        rows.append({"provider": "openai", "state": state, "detail": detail,
                     "id": key.get("id"), "name": key.get("name") or "(unnamed)",
                     "hint": safe_hint(key.get("redacted_value")),
                     "container": "organization", "label": "admin key",
                     "idle": age_days(key.get("last_used_at"), now)
                             or age_days(key.get("created_at"), now) or 0})

    log.info("openai: %d project(s) read, %d archived, %d key(s) including %d "
             "admin key(s)", len(projects), archived, len(rows), len(admin_keys))
    return rows


def sweep_anthropic(session, now, args):
    """Read the active key roster, then the usage report it must be joined to."""
    keys = []
    for page in anthropic_paged(session, "/organizations/api_keys",
                                {"status": "active", "limit": 1000}):
        keys.extend(page.get("data") or [])

    seen = seen_key_ids(anthropic_report(
        session, "/organizations/usage_report/messages",
        {"starting_at": window_start(args.days, now), "bucket_width": "1d",
         "limit": min(args.days + 1, 31), "group_by[]": ["api_key_id"]}))

    rows = []
    for key in keys:
        state, detail = anthropic_verdict(key, seen, args.days, now,
                                          args.never_after)
        rows.append({"provider": "anthropic", "state": state, "detail": detail,
                     "id": key.get("id"), "name": key.get("name") or "(unnamed)",
                     "hint": safe_hint(key.get("partial_key_hint")),
                     "container": key.get("id"), "label": "anthropic",
                     "idle": age_days(key.get("created_at"), now) or 0})

    log.info("anthropic: %d active key(s), %d seen in the usage report over "
             "%d day(s)", len(keys), len(seen), args.days)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--never-after", type=int, default=30,
                    help="days a never-used key must exist before it is a finding")
    ap.add_argument("--dormant-after", type=int, default=90,
                    help="days since last use that counts as dormant")
    ap.add_argument("--days", type=int, default=30,
                    help="Anthropic usage-report window, which bounds that half")
    args = ap.parse_args()

    openai_key = os.environ.get("OPENAI_ADMIN_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not openai_key and not anthropic_key:
        log.error("set OPENAI_ADMIN_KEY (sk-admin-, read scopes) or "
                  "ANTHROPIC_ADMIN_KEY (sk-ant-admin), or both; a project or "
                  "workspace key cannot read the administration endpoints")
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    if openai_key:
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + openai_key})
        rows.extend(sweep_openai(s, now, args))
    if anthropic_key:
        s = requests.Session()
        s.headers.update({"x-api-key": anthropic_key,
                          "anthropic-version": ANTHROPIC_VERSION})
        rows.extend(sweep_anthropic(s, now, args))

    queue = revocation_order(rows)
    for row in queue:
        log.warning("%-16s %-14s %-18s %s  %s", row["state"], row["label"],
                    row["name"], row["hint"], row["detail"])
        for repair in repair_lines(row["state"], row):
            log.warning("  repair: %s", repair)

    log.info("%d key(s) read, %d finding(s)", len(rows), len(queue))
    log.info("no key value appears above: both providers return a redacted "
             "hint and the hint is all this script will print")
    return 1 if queue else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "llm-idle-key-audit.mjs",
"js": '''/**
 * Find API keys that no request has ever used.
 *
 * Read only. Every request is a GET against the OpenAI Administration API or
 * the Anthropic Admin API. No key value is printed: the providers return a
 * redacted hint and that hint is all that reaches the output.
 *
 * OpenAI carries last_used_at on the key object, so "never used" is a field.
 * Anthropic has no such field, so "unused" is a set difference against the
 * usage report and is bounded by that report's window. The Anthropic half of
 * the output says "unused in the last N days" and never says "never".
 */
const OPENAI = 'https://api.openai.com/v1';
const ANTHROPIC = 'https://api.anthropic.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

export const NEVER = 'never-used';
export const DORMANT = 'dormant';
export const UNUSED_IN_WINDOW = 'unused-in-window';
export const IN_USE = 'in-use';
export const SEEN = 'seen-in-window';
export const TOO_NEW = 'too-new';
export const UNREADABLE = 'unreadable-dates';
export const NOT_ACTIVE = 'not-active';

// Lower sorts first, and the order is revocation safety rather than age.
const SAFETY = { [NEVER]: 0, [UNUSED_IN_WINDOW]: 1, [DORMANT]: 2 };

/** A key hint that is safe to print. Pure. Anything unredacted is withheld. */
export function safeHint(value) {
  const text = String(value ?? '').trim();
  if (!text) return '(no hint)';
  if (!text.includes('...') && !text.includes('*')) return '(hint withheld)';
  if (text.length > 40) return '(hint withheld)';
  return text;
}

/** Whole days between a timestamp and now. Pure. null when unreadable.
 *  Accepts a unix integer (OpenAI) or an RFC 3339 string (Anthropic). */
export function ageDays(stamp, now) {
  if (stamp === null || stamp === undefined || stamp === '' ||
      typeof stamp === 'boolean') return null;
  let when;
  if (typeof stamp === 'number') {
    when = new Date(stamp * 1000);
  } else if (/^\\d+$/.test(String(stamp).trim())) {
    when = new Date(Number(String(stamp).trim()) * 1000);
  } else {
    when = new Date(String(stamp).trim());
  }
  if (Number.isNaN(when.getTime())) return null;
  return Math.floor((now.getTime() - when.getTime()) / 86400000);
}

/** Classify one OpenAI key off last_used_at. Pure. Returns [state, detail]. */
export function openaiVerdict(key, now, neverAfter = 30, dormantAfter = 90) {
  const row = key ?? {};
  const created = ageDays(row.created_at, now);
  const last = row.last_used_at;
  if (last === null || last === undefined || last === '' || last === 0) {
    if (created === null) {
      return [UNREADABLE,
        'never used, and created_at cannot be read, so no age can be given for it'];
    }
    if (created < neverAfter) {
      return [TOO_NEW, `never used, but only ${created} day(s) old`];
    }
    return [NEVER, `never used in the ${created} day(s) since it was created`];
  }
  const idle = ageDays(last, now);
  if (idle === null) return [UNREADABLE, 'last_used_at is present but cannot be read'];
  if (idle >= dormantAfter) return [DORMANT, `last used ${idle} day(s) ago`];
  return [IN_USE, `last used ${idle} day(s) ago`];
}

/** Classify one Anthropic key off usage-report membership. Pure. */
export function anthropicVerdict(key, seenIds, windowDays, now, neverAfter = 30) {
  const row = key ?? {};
  const status = String(row.status ?? 'active').trim().toLowerCase();
  if (status !== 'active') {
    return [NOT_ACTIVE, `status is ${status}, so it cannot authenticate`];
  }
  const created = ageDays(row.created_at, now);
  if (created !== null && created < neverAfter) {
    return [TOO_NEW, `only ${created} day(s) old`];
  }
  if ((seenIds ?? new Set()).has(String(row.id ?? ''))) {
    return [SEEN, `carried traffic inside the last ${windowDays} day(s)`];
  }
  return [UNUSED_IN_WINDOW,
    `no traffic in the last ${windowDays} day(s). The Anthropic key object ` +
    'has no last_used_at field, so this is unused within the retrievable ' +
    'window and not a claim that it was never used.'];
}

/** Warn about a sweep that will silently under-report. Pure. */
export function auditGaps(projectParams, keyParams) {
  const gaps = [];
  if (String((projectParams ?? {}).include_archived ?? '').toLowerCase() !== 'true') {
    gaps.push('include_archived is not true: archived projects are omitted ' +
              'from the project listing, and every key inside them with it');
  }
  if (String((keyParams ?? {}).owner_project_access ?? '') !== 'any') {
    gaps.push("owner_project_access is not 'any': the key listing applies " +
              'membership visibility rules and can hide enabled keys from ' +
              'this audit');
  }
  return gaps;
}

/** Every non-null api_key_id in an Anthropic usage report. Pure. */
export function seenKeyIds(pages) {
  const out = new Set();
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      for (const result of bucket?.results ?? []) {
        if (result?.api_key_id) out.add(String(result.api_key_id));
      }
    }
  }
  return out;
}

/** Order findings by how safe each is to revoke. Pure. */
export function revocationOrder(rows) {
  return (rows ?? [])
    .filter((r) => r?.state in SAFETY)
    .slice()
    .sort((a, b) => (SAFETY[a.state] - SAFETY[b.state])
      || (Number(b.idle ?? 0) - Number(a.idle ?? 0))
      || String(a.name ?? '').localeCompare(String(b.name ?? '')));
}

/** The repair for one classified key. Pure. Printed, never performed. */
export function repairLines(state, row) {
  const data = row ?? {};
  if (state === NEVER) {
    return [
      'nothing has ever authenticated with this key, so revoking it cannot ' +
      'break traffic. These are the safest credentials in the organization to remove.',
      `revoke with a DELETE on /v1/organization/projects/${data.container ?? '{project_id}'}` +
      `/api_keys/${data.id ?? '{key_id}'} once somebody confirms what it was minted for.`,
    ];
  }
  if (state === DORMANT) {
    return [
      'something was built on this key and has since stopped calling. Ask ' +
      'what it was before revoking: annual jobs and disaster-recovery paths ' +
      'look exactly like this.',
      'if it is genuinely dead, revoke it and confirm last_used_at stops ' +
      'advancing rather than assuming it will.',
    ];
  }
  if (state === UNUSED_IN_WINDOW) {
    return [
      'this is unused within the report window, not proven unused. Widen the ' +
      'window as far as the report allows before concluding anything, then ' +
      'archive the key rather than deleting it.',
      'the Anthropic key object carries an optional expires_at. Set one on ' +
      'the replacement so the next idle key expires itself.',
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

async function getJson(url, headers, who) {
  const res = await fetch(url, { headers });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from ${who}: this endpoint needs an ` +
                    'administration key, not a project or workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function openaiPaged(key, path, params) {
  const headers = { Authorization: `Bearer ${key}` };
  const out = [];
  let after = null;
  for (;;) {
    const url = new URL(OPENAI + path);
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
    if (after) url.searchParams.set('after', after);
    const page = await getJson(url, headers, 'OpenAI');
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.last_id) return out;
    after = page.last_id;
  }
}

async function anthropicPaged(key, path, params) {
  const headers = { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION };
  const out = [];
  let afterId = null;
  for (;;) {
    const url = new URL(ANTHROPIC + path);
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
    if (afterId) url.searchParams.set('after_id', afterId);
    const page = await getJson(url, headers, 'Anthropic');
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.last_id) return out;
    afterId = page.last_id;
  }
}

async function anthropicReport(key, params) {
  const headers = { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION };
  const pages = [];
  let page = null;
  for (;;) {
    const url = new URL(`${ANTHROPIC}/organizations/usage_report/messages`);
    for (const [k, v] of params) url.searchParams.append(k, v);
    if (page) url.searchParams.set('page', page);
    const body = await getJson(url, headers, 'Anthropic');
    pages.push(body);
    if (!body.has_more || !body.next_page) return pages;
    page = body.next_page;
  }
}

async function main() {
  const openaiKey = process.env.OPENAI_ADMIN_KEY;
  const anthropicKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!openaiKey && !anthropicKey) {
    console.error('set OPENAI_ADMIN_KEY (sk-admin-, read scopes) or ' +
                  'ANTHROPIC_ADMIN_KEY (sk-ant-admin), or both; a project or ' +
                  'workspace key cannot read the administration endpoints');
    process.exitCode = 2;
    return;
  }
  const neverAfter = Number(process.env.NEVER_AFTER ?? 30);
  const dormantAfter = Number(process.env.DORMANT_AFTER ?? 90);
  const days = Number(process.env.DAYS ?? 30);
  const now = new Date();
  const rows = [];

  if (openaiKey) {
    const projectParams = { limit: 100, include_archived: 'true' };
    const keyParams = { limit: 100, owner_project_access: 'any' };
    for (const gap of auditGaps(projectParams, keyParams)) {
      console.warn(`audit gap: ${gap}`);
    }
    const projects = await openaiPaged(openaiKey, '/organization/projects', projectParams);
    for (const project of projects) {
      if (!project.id) continue;
      const keys = await openaiPaged(
        openaiKey, `/organization/projects/${project.id}/api_keys`, keyParams);
      for (const key of keys) {
        const [state, detail] = openaiVerdict(key, now, neverAfter, dormantAfter);
        rows.push({ state, detail, id: key.id, name: key.name ?? '(unnamed)',
                    hint: safeHint(key.redacted_value), container: project.id,
                    label: project.name ?? project.id,
                    idle: ageDays(key.last_used_at, now) ?? ageDays(key.created_at, now) ?? 0 });
      }
    }
    const adminKeys = await openaiPaged(openaiKey, '/organization/admin_api_keys', { limit: 100 });
    for (const key of adminKeys) {
      const [state, detail] = openaiVerdict(key, now, neverAfter, dormantAfter);
      rows.push({ state, detail, id: key.id, name: key.name ?? '(unnamed)',
                  hint: safeHint(key.redacted_value), container: 'organization',
                  label: 'admin key',
                  idle: ageDays(key.last_used_at, now) ?? ageDays(key.created_at, now) ?? 0 });
    }
    console.log(`openai: ${projects.length} project(s) read, ${rows.length} key(s) ` +
                `including ${adminKeys.length} admin key(s)`);
  }

  if (anthropicKey) {
    const keys = await anthropicPaged(anthropicKey, '/organizations/api_keys',
                                      { status: 'active', limit: 1000 });
    const seen = seenKeyIds(await anthropicReport(anthropicKey, [
      ['starting_at', windowStart(days, now)], ['bucket_width', '1d'],
      ['limit', String(Math.min(days + 1, 31))], ['group_by[]', 'api_key_id'],
    ]));
    for (const key of keys) {
      const [state, detail] = anthropicVerdict(key, seen, days, now, neverAfter);
      rows.push({ state, detail, id: key.id, name: key.name ?? '(unnamed)',
                  hint: safeHint(key.partial_key_hint), container: key.id,
                  label: 'anthropic', idle: ageDays(key.created_at, now) ?? 0 });
    }
    console.log(`anthropic: ${keys.length} active key(s), ${seen.size} seen in ` +
                `the usage report over ${days} day(s)`);
  }

  const queue = revocationOrder(rows);
  for (const row of queue) {
    console.warn(`${row.state.padEnd(16)} ${String(row.label).padEnd(14)} ` +
                 `${String(row.name).padEnd(18)} ${row.hint}  ${row.detail}`);
    for (const repair of repairLines(row.state, row)) {
      console.warn(`  repair: ${repair}`);
    }
  }
  console.log(`${rows.length} key(s) read, ${queue.length} finding(s)`);
  console.log('no key value appears above: both providers return a redacted ' +
              'hint and the hint is all this script will print');
  process.exitCode = queue.length ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note itself, and it is written so that it would fail if this drifted into the offboarding sweep: a key whose owner is present, active and entirely fine, that has never authenticated anything, has to come back as <code>never-used</code>. The second is the provider split, asserted as a difference in wording rather than in state alone: the Anthropic verdict must contain the window and must not contain the word <em>never</em>, because the field that would justify it does not exist. After that: <code>audit_gaps</code>, which has to complain about exactly the two parameters that default to hiding things; <code>age_days</code> against a unix integer, an RFC 3339 string and a <code>last_used_at</code> of zero, which must not date a key to 1970; the revocation queue, which must put a never-used key ahead of a longer-idle dormant one; and <code>safe_hint</code>, which has to withhold anything that does not already look redacted.",
"test_py_file": "test_llm_idle_key_audit.py",
"test_py": '''import datetime as dt

from llm_idle_key_audit import (age_days, anthropic_verdict, audit_gaps,
                                openai_verdict, repair_lines, revocation_order,
                                safe_hint, seen_key_ids)

NOW = dt.datetime(2026, 8, 31, 12, 0, 0, tzinfo=dt.timezone.utc)


def unix(days_ago):
    return int((NOW - dt.timedelta(days=days_ago)).timestamp())


def test_a_key_whose_owner_is_perfectly_fine_is_still_the_finding():
    # The note in one assertion, and the line that keeps it away from the
    # published offboarding note. This owner is present, active and employed.
    # The verdict does not read the owner at all.
    key = {"id": "key_a1", "name": "vendor-trial",
           "redacted_value": "sk-...4f7a", "created_at": unix(154),
           "last_used_at": None,
           "owner": {"type": "user", "user": {"email": "dev@example.test"}},
           "owner_project_access": "active"}
    state, detail = openai_verdict(key, NOW)
    assert state == "never-used"
    assert "154 day(s)" in detail
    assert any("cannot break traffic" in line
               for line in repair_lines(state, {"container": "proj_1",
                                                "id": "key_a1"}))


def test_the_two_providers_answer_different_strengths_of_the_question():
    # OpenAI reads a field and may say "never". Anthropic reads a set
    # difference over a window and must not.
    openai_state, openai_detail = openai_verdict(
        {"created_at": unix(200), "last_used_at": None}, NOW)
    assert openai_state == "never-used"
    assert "never used" in openai_detail

    anthropic_state, anthropic_detail = anthropic_verdict(
        {"id": "apikey_z9", "status": "active",
         "created_at": "2025-01-04T09:12:00Z"}, set(), 30, NOW)
    assert anthropic_state == "unused-in-window"
    assert "last 30 day(s)" in anthropic_detail
    assert "no last_used_at field" in anthropic_detail
    assert "never used" not in anthropic_detail.split("not a claim")[0]


def test_the_two_defaulted_parameters_are_the_audit_and_are_asserted():
    assert audit_gaps({"include_archived": "true"},
                      {"owner_project_access": "any"}) == []
    gaps = audit_gaps({"limit": 100}, {"limit": 100})
    assert len(gaps) == 2
    assert any("include_archived" in g for g in gaps)
    assert any("owner_project_access" in g for g in gaps)
    # The dangerous middle case: one parameter remembered, one forgotten.
    assert len(audit_gaps({"include_archived": "true"}, {"limit": 100})) == 1


def test_dates_arrive_in_two_shapes_and_a_zero_is_not_1970():
    assert age_days(unix(45), NOW) == 45
    assert age_days("2026-08-01T00:00:00Z", NOW) == 30
    assert age_days("2026-08-01T00:00:00+00:00", NOW) == 30
    assert age_days(str(unix(7)), NOW) == 7
    assert age_days(None, NOW) is None
    assert age_days("not a date", NOW) is None
    assert age_days(True, NOW) is None
    # last_used_at of 0 is absent, not a use in 1970.
    state, _ = openai_verdict({"created_at": unix(100), "last_used_at": 0}, NOW)
    assert state == "never-used"


def test_dormant_and_never_used_are_graded_and_ordered_apart():
    fresh = openai_verdict({"created_at": unix(120), "last_used_at": unix(3)}, NOW)
    assert fresh[0] == "in-use"
    old = openai_verdict({"created_at": unix(900), "last_used_at": unix(412)}, NOW)
    assert old[0] == "dormant"
    assert "412 day(s) ago" in old[1]
    young = openai_verdict({"created_at": unix(9), "last_used_at": None}, NOW)
    assert young[0] == "too-new"

    order = revocation_order([
        {"state": "dormant", "idle": 412, "name": "nightly"},
        {"state": "in-use", "idle": 1, "name": "prod"},
        {"state": "never-used", "idle": 154, "name": "vendor-trial"},
        {"state": "unused-in-window", "idle": 300, "name": "ingest"},
    ])
    assert [r["state"] for r in order] == ["never-used", "unused-in-window",
                                           "dormant"]


def test_an_anthropic_key_seen_in_the_report_is_not_a_finding():
    pages = [{"data": [{"results": [{"api_key_id": "apikey_a"},
                                    {"api_key_id": None},
                                    {"api_key_id": "apikey_b"}]}]}]
    seen = seen_key_ids(pages)
    assert seen == {"apikey_a", "apikey_b"}
    assert anthropic_verdict({"id": "apikey_a", "status": "active",
                              "created_at": "2024-02-02T00:00:00Z"},
                             seen, 30, NOW)[0] == "seen-in-window"
    assert anthropic_verdict({"id": "apikey_c", "status": "archived"},
                             seen, 30, NOW)[0] == "not-active"
    assert seen_key_ids([]) == set()
    assert seen_key_ids(None) == set()


def test_no_key_value_can_reach_the_output():
    assert safe_hint("sk-...4f7a") == "sk-...4f7a"
    assert safe_hint("sk-ant-...igAA") == "sk-ant-...igAA"
    assert safe_hint("sk-abcd****wxyz") == "sk-abcd****wxyz"
    # Anything that is not already redacted is refused, whatever it is.
    assert safe_hint("sk-fake-not-redacted-value") == "(hint withheld)"
    assert safe_hint("...." + "x" * 60) == "(hint withheld)"
    assert safe_hint(None) == "(no hint)"
    assert safe_hint("") == "(no hint)"


def test_the_repairs_say_different_things_for_the_two_findings():
    never = repair_lines("never-used", {"container": "proj_1", "id": "key_1"})
    dormant = repair_lines("dormant", {})
    window = repair_lines("unused-in-window", {})
    assert any("safest credentials" in line for line in never)
    assert any("Ask what it was before revoking" in line for line in dormant)
    assert any("not proven unused" in line for line in window)
    assert repair_lines("in-use", {}) == []
''',
"test_js_file": "llm-idle-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, anthropicVerdict, auditGaps, openaiVerdict, repairLines,
         revocationOrder, safeHint, seenKeyIds, windowStart }
  from './llm-idle-key-audit.mjs';

const NOW = new Date('2026-08-31T12:00:00Z');
const unix = (daysAgo) => Math.floor(NOW.getTime() / 1000) - daysAgo * 86400;

test('a key whose owner is perfectly fine is still the finding', () => {
  const key = { id: 'key_a1', name: 'vendor-trial', redacted_value: 'sk-...4f7a',
                created_at: unix(154), last_used_at: null,
                owner: { type: 'user', user: { email: 'dev@example.test' } },
                owner_project_access: 'active' };
  const [state, detail] = openaiVerdict(key, NOW);
  assert.equal(state, 'never-used');
  assert.match(detail, /154 day\\(s\\)/);
  assert.ok(repairLines(state, { container: 'proj_1', id: 'key_a1' })
    .some((line) => line.includes('cannot break traffic')));
});

test('the two providers answer different strengths of the question', () => {
  const [openaiState, openaiDetail] =
    openaiVerdict({ created_at: unix(200), last_used_at: null }, NOW);
  assert.equal(openaiState, 'never-used');
  assert.match(openaiDetail, /never used/);

  const [anthropicState, anthropicDetail] = anthropicVerdict(
    { id: 'apikey_z9', status: 'active', created_at: '2025-01-04T09:12:00Z' },
    new Set(), 30, NOW);
  assert.equal(anthropicState, 'unused-in-window');
  assert.match(anthropicDetail, /last 30 day\\(s\\)/);
  assert.match(anthropicDetail, /no last_used_at field/);
  assert.ok(!anthropicDetail.split('not a claim')[0].includes('never used'));
});

test('the two defaulted parameters are the audit and are asserted', () => {
  assert.deepEqual(auditGaps({ include_archived: 'true' },
                             { owner_project_access: 'any' }), []);
  const gaps = auditGaps({ limit: 100 }, { limit: 100 });
  assert.equal(gaps.length, 2);
  assert.ok(gaps.some((g) => g.includes('include_archived')));
  assert.ok(gaps.some((g) => g.includes('owner_project_access')));
  assert.equal(auditGaps({ include_archived: 'true' }, { limit: 100 }).length, 1);
});

test('dates arrive in two shapes and a zero is not 1970', () => {
  assert.equal(ageDays(unix(45), NOW), 45);
  assert.equal(ageDays('2026-08-01T00:00:00Z', NOW), 30);
  assert.equal(ageDays(String(unix(7)), NOW), 7);
  assert.equal(ageDays(null, NOW), null);
  assert.equal(ageDays('not a date', NOW), null);
  assert.equal(ageDays(true, NOW), null);
  assert.equal(openaiVerdict({ created_at: unix(100), last_used_at: 0 }, NOW)[0],
               'never-used');
});

test('dormant and never used are graded and ordered apart', () => {
  assert.equal(openaiVerdict({ created_at: unix(120), last_used_at: unix(3) }, NOW)[0],
               'in-use');
  const [state, detail] =
    openaiVerdict({ created_at: unix(900), last_used_at: unix(412) }, NOW);
  assert.equal(state, 'dormant');
  assert.match(detail, /412 day\\(s\\) ago/);
  assert.equal(openaiVerdict({ created_at: unix(9), last_used_at: null }, NOW)[0],
               'too-new');

  const order = revocationOrder([
    { state: 'dormant', idle: 412, name: 'nightly' },
    { state: 'in-use', idle: 1, name: 'prod' },
    { state: 'never-used', idle: 154, name: 'vendor-trial' },
    { state: 'unused-in-window', idle: 300, name: 'ingest' },
  ]);
  assert.deepEqual(order.map((r) => r.state),
                   ['never-used', 'unused-in-window', 'dormant']);
});

test('an anthropic key seen in the report is not a finding', () => {
  const seen = seenKeyIds([{ data: [{ results: [{ api_key_id: 'apikey_a' },
                                                { api_key_id: null },
                                                { api_key_id: 'apikey_b' }] }] }]);
  assert.deepEqual([...seen].sort(), ['apikey_a', 'apikey_b']);
  assert.equal(anthropicVerdict({ id: 'apikey_a', status: 'active',
                                  created_at: '2024-02-02T00:00:00Z' },
                                seen, 30, NOW)[0], 'seen-in-window');
  assert.equal(anthropicVerdict({ id: 'apikey_c', status: 'archived' },
                                seen, 30, NOW)[0], 'not-active');
  assert.equal(seenKeyIds([]).size, 0);
  assert.equal(seenKeyIds(null).size, 0);
});

test('no key value can reach the output', () => {
  assert.equal(safeHint('sk-...4f7a'), 'sk-...4f7a');
  assert.equal(safeHint('sk-ant-...igAA'), 'sk-ant-...igAA');
  assert.equal(safeHint('sk-abcd****wxyz'), 'sk-abcd****wxyz');
  assert.equal(safeHint('sk-fake-not-redacted-value'), '(hint withheld)');
  assert.equal(safeHint(`....${'x'.repeat(60)}`), '(hint withheld)');
  assert.equal(safeHint(null), '(no hint)');
  assert.equal(safeHint(''), '(no hint)');
});

test('the window start is floored to midnight utc', () => {
  assert.equal(windowStart(30, new Date('2026-08-31T17:45:12Z')),
               '2026-08-01T00:00:00Z');
});
''',
"faq": [
 ("How is this different from auditing keys whose owner has left?",
  "It never looks at the owner. The offboarding sweep reads owner_project_access, a flag the provider raises when the person behind a key loses access to the project, so its subject is a human. This one reads last_used_at, so its subject is traffic. The case that only this note can see is a key belonging to somebody who is present, employed and still on the project, minted for a reason that evaporated, that has authenticated nothing since. Nothing about that key is irregular from the offboarding sweep's point of view, and it is a live credential with full project access all the same."),
 ("Why does the Anthropic half refuse to say a key was never used?",
  "Because the field that would justify it does not exist. The Anthropic API key object carries id, created_at, created_by, expires_at, name, partial_key_hint, principal, scope, status and type, and no last-used timestamp of any kind. So the only way to ask the question is to take the active key list and subtract every api_key_id that appears in the usage report, which reaches back exactly as far as the report does. A key that last ran something thirteen months ago and a key that has never run anything are the same row in that set difference. Reporting the weaker fact accurately is better than reporting the stronger one hopefully."),
 ("What do owner_project_access=any and include_archived=true actually change?",
  "What the audit can see, and neither omission tells you it happened. Without owner_project_access=any the key listing applies membership-based visibility rules that can leave enabled keys out of the response. Without include_archived=true the project listing omits archived projects entirely, and archived projects still hold live keys. You do not get an error or an obviously truncated list; you get a smaller number that reads as good news. The script asserts both parameters rather than mentioning them in a comment."),
 ("Is a never-used key really safe to delete?",
  "It is the safest object in the organization to delete, and that is a statement about traffic rather than about process. If last_used_at is null, nothing has ever authenticated with this credential, so there is no request path that can break when it is revoked. A dormant key is the opposite: something was built on it, and annual reports, disaster-recovery paths and quarterly exports all look identical to abandonment for eleven months of the year. The script orders never-used ahead of dormant for exactly that reason, and it still only prints the revocation call."),
 ("Why sweep the admin keys separately?",
  "Because they live on their own endpoint and they are the credentials with real blast radius. GET /v1/organization/admin_api_keys returns objects that carry last_used_at just as project keys do, plus an optional expires_at that project keys do not have at all. An idle admin key can enumerate every credential in the organization and read every usage and cost report in it. A sweep that walks projects and stops has skipped the most powerful keys you own, and it will report a clean result while doing so."),
],
"related": [REL_OWNER_GONE, REL_ARCHIVED, REL_ROTATION],
"citations": [CITE_PROJECT_KEYS, CITE_PROJECTS, CITE_AN_LIST_KEYS,
              CITE_AN_USAGE_REPORT],
},
{
"slug": "legacy-user-owned-keys-in-project",
"title": "Production keys owned by people, not service accounts",
"description": "Filter the key list on owner.type == user and join it to cost by api_key_id. The finding is who owns the credential, not how much of the bill it holds.",
"h1": "Production keys owned by people, not service accounts",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai api key owner.type user",
             "openai service account vs user key",
             "openai project service_accounts audit",
             "personal api key in production openai",
             "openai costs group_by api_key_id owner"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an sk-admin- key with read scopes: /v1/organization/* rejects project keys, and the Anthropic key object has no equivalent owner type to read.",
"lead": "The service has been up for two years and it has never once paged anybody about credentials. That is because the credential is Marco's. He minted it in the first week, before the project structure existed, because a personal key works the instant you create it and a service account is a thing you have to think about first. Nothing has gone wrong. Marco is still here, still on the team, still the person who would fix it. The only fact that has changed in two years is that eleven thousand dollars a month now moves through a credential whose lifecycle is attached to one person's employment rather than to the service's.",
"short_answer": """<p>With an <strong>organization admin key</strong>: for every project, <code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code> and keep every key whose <code>owner.type</code> is <code>"user"</code>. The owner block gives you <code>owner.user.id</code>, <code>owner.user.email</code>, <code>owner.user.name</code> and <code>owner.user.role</code>.</p>
<p>Then join money to it: <code>GET /v1/organization/costs?start_time={now-30d}&amp;limit=30&amp;group_by=api_key_id</code>, and match on <code>api_key_id</code>. A user-owned key with real <code>amount.value</code> behind it is production traffic running on a personal credential. A user-owned key with nothing behind it is a cleanup task, not an incident, and the script grades them differently.</p>
<p>The third call is the one that turns a list into a verdict: <code>GET /v1/organization/projects/{project_id}/service_accounts</code>. A project with spending user-owned keys and an <strong>empty service-account list</strong> has never had the alternative at all, which is a different conversation from a project that has service accounts and one straggler.</p>
<p><strong>This is not a concentration check.</strong> Two user-owned keys splitting production spend evenly are two findings here, and the share of the bill each holds never enters the verdict.</p>""",
"problem": """<p>A personal key is the path of least resistance, and it stays the path of least resistance forever. Any project member can mint one and it authenticates immediately. A service account asks you to have an opinion about the project's structure first, at exactly the moment you are trying to get one request to return a 200. So the first credential in every project is somebody's, and the first credential in every project is usually still there years later, because nothing ever forces the question again.</p>
<p>What that binds together is two lifecycles that have nothing to do with each other. The service's lifecycle is about deployments, migrations and decommissioning. The person's lifecycle is about employment, team moves and access reviews. As long as those two never diverge, everything works perfectly, which is why this survives so long: <em>there is no failure state until there is</em>. Then somebody changes teams, or leaves, or has their access reviewed and tidied, and a production credential is inside the blast radius of an HR event.</p>
<p>It also quietly corrupts attribution. Spend on that key rolls up to a <code>user_id</code> in the Usage API, and audit-log entries for actions taken with it name a person. A year of that produces reports that confidently attribute a service's entire consumption to an engineer who has not thought about it since the week they created it.</p>""",
"why": """<p><strong>The finding is the ownership type, and it is deliberately not a share of the bill.</strong> <a href="/llm/one-model-or-project-dominates-cost/">The published concentration note</a> owns <code>group_by=api_key_id</code> ranked by share of total: its subject is one key holding most of the money, and its repair is one key per deployable unit. That note is silent when spend is spread evenly, which is precisely when this one has the most to say. The verdict function here is not given a total to divide by, so a share cannot influence it even by accident, and the tests assert that a key holding three per cent of the bill grades identically to one holding ninety-five.</p>
<p><strong>The cost join separates two very different repairs, and nothing else.</strong> A user-owned key with money behind it is production standing on a person, and the repair is a migration with a deploy in the middle of it. A user-owned key with no money behind it is somebody's leftover experiment, and the repair is a revocation. Both are <code>owner.type == "user"</code>. Grading them the same produces a list that nobody acts on because the urgent rows are buried among the trivial ones.</p>
<p><strong>An empty service-account list is the strongest form of the finding.</strong> A project with spending user keys and no service accounts at all has not made a mistake in one place; it has never had the mechanism. That is a project-level finding rather than a per-key one, and it changes what you print: not "migrate this key" but "create the first service account this project has ever had".</p>
<p><strong>This is not the offboarding sweep, and it fires long before that one can.</strong> <a href="/llm/key-owner-lost-project-access/">The published note on owners who lost project access</a> reads a flag the provider raises after the binding has already broken. Everything here is still fine: the owner is present, has access, and the flag says <code>active</code>. The whole point is to find the arrangement while it is working, because after it stops working you are doing an emergency rotation instead of a planned one.</p>
<p><strong>Anthropic cannot be asked this question in the same form.</strong> Its key object carries <code>created_by</code>, <code>principal</code> and <code>scope</code>, and there is no project service-account object to compare a key against. <code>created_by</code> records who minted the key, which is a different question and one <a href="/llm/key-owner-lost-project-access/">the departed-member note</a> already uses. So this script is OpenAI-only, and says so on startup rather than pretending the Anthropic half is merely unimplemented.</p>""",
"steps": [
 {"h": "Use an admin key with read scopes",
  "body": """<p><code>/v1/organization/*</code> rejects project keys, so this cannot run on the application's credential. An <code>sk-admin-</code> key provisioned read-only reads projects, keys, service accounts and costs, and can change none of them.</p>"""},
 {"h": "List every project's keys with owner_project_access=any",
  "body": """<p>Walk projects with <code>include_archived=true</code>, then each project's keys with <code>owner_project_access=any</code>. Both parameters default to a narrower answer. Keep every key whose <code>owner.type</code> is <code>"user"</code> and record <code>owner.user.email</code> beside it.</p>"""},
 {"h": "Read the service-account roster for the same project",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/service_accounts?limit=100</code> returns <code>id</code>, <code>name</code>, <code>role</code> and <code>created_at</code>. An empty list here, alongside user-owned keys that are spending, is the project-level finding and gets printed once for the project rather than once per key.</p>"""},
 {"h": "Join thirty days of cost by api_key_id",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-30d}&amp;limit=30&amp;group_by=api_key_id</code>. Match <code>api_key_id</code> to the key ids you collected. Keep the currency with the amount and never sum across currencies: an organization billed in two currencies produces a meaningless total if you add the numbers and drop the units.</p>"""},
 {"h": "Print the migration in order, and run none of it",
  "body": """<p>For each spending personal key: create a service account for the service, mint its key, deploy the new value, confirm traffic moved by re-reading <code>group_by=api_key_id</code>, and only then revoke the old one. The order matters because the service-account key value is returned exactly once at creation, and because revoking before the traffic moves is an outage. The script prints the sequence; you run it.</p>"""},
],
"verify": """<p>Re-run after each migration. The key you moved should show its spend fall to zero while the new service-account key picks it up, and only then should the old key be revoked.</p>
<pre><code class="language-bash">python3 openai_user_owned_key_audit.py --days 30 --min-spend 1.00
# 6 project(s), 38 key(s), 9 owned by a user
# project proj_prod   no service accounts at all, and 2 user-owned key(s) are spending
# personal-key-in-production  proj_prod  api-main    sk-...9c31  marco@example.test  11402.88 USD over 30 day(s)
#   repair: create a service account for this service, mint its key, deploy, confirm the spend moves, then revoke.
# personal-key-in-production  proj_prod  worker-2    sk-...11ab  dana@example.test    9880.10 USD over 30 day(s)
# personal-key-idle           proj_evals scratch     sk-...77de  marco@example.test   no cost rows in 30 day(s)
#   repair: no traffic behind this one, so it is a revocation rather than a migration.
# 3 finding(s), 1 project(s) with no service accounts</code></pre>""",
"code_intro": "Three GETs and a join. <code>owner_kind</code> is the whole note in six lines, and it treats a missing or unrecognised owner block as <code>unknown</code> rather than folding it into either camp, because an unattributable credential is its own finding. <code>fold_costs</code> keeps currency alongside amount and <code>spend_line</code> refuses to add across currencies. <code>verdict</code> takes one key, that key's own spend and the project's service-account count, and nothing else: there is no organization total in its signature, so a share of the bill cannot reach it. <code>project_note</code> raises the empty-roster case to the project level, and <code>migration_plan</code> prints the ordered cutover with the revocation last.",
"py_file": "openai_user_owned_key_audit.py",
"py": '''"""Find production keys whose owner is a person rather than a service account.

Read only. Three GETs against the OpenAI Administration API with an admin key:
the project list, each project's keys and service accounts, and the cost report
grouped by api_key_id. Nothing is created, changed or removed, and no key value
is printed.

The finding is the ownership type. This is not a concentration check: the
verdict function is never given an organization total, so the share of the bill
a key holds cannot influence its grade. Two personal keys splitting production
spend evenly are two findings here.

Anthropic is not covered, and not because it was skipped. Its key object has no
owner-type distinction between a person's credential and a service one, and it
has no project service-account object to compare against. created_by records
who minted a key, which is a different question.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_user_owned_key_audit")

API = "https://api.openai.com/v1"

USER = "user"
SERVICE_ACCOUNT = "service_account"
UNKNOWN = "unknown"

IN_PRODUCTION = "personal-key-in-production"
IDLE = "personal-key-idle"
UNATTRIBUTABLE = "unattributable-owner"
FINE = "service-account-key"
FINDINGS = (IN_PRODUCTION, IDLE, UNATTRIBUTABLE)


def safe_hint(value):
    """Return a key hint that is safe to print. Pure.

    The API returns redacted_value already redacted. Anything that does not
    look redacted is withheld, because an audit script printing a live
    credential into a log is the one mistake here that cannot be undone.
    """
    text = str(value or "").strip()
    if not text:
        return "(no hint)"
    if ("..." not in text and "*" not in text) or len(text) > 40:
        return "(hint withheld)"
    return text


def owner_kind(key):
    """Is this key owned by a person or by a service account? Pure.

    An absent or unrecognised owner block becomes "unknown" and is never folded
    into either camp. A credential nobody can attribute is a finding in its own
    right, and quietly counting it as a service account would hide it.
    """
    owner = (key or {}).get("owner")
    if not isinstance(owner, dict):
        return UNKNOWN
    kind = str(owner.get("type") or "").strip().lower()
    return kind if kind in (USER, SERVICE_ACCOUNT) else UNKNOWN


def owner_label(key):
    """A printable identity for the key's owner. Pure. Never a key value."""
    owner = (key or {}).get("owner")
    if not isinstance(owner, dict):
        return "(no owner block)"
    if owner_kind(key) == USER:
        user = owner.get("user") if isinstance(owner.get("user"), dict) else {}
        return str(user.get("email") or user.get("name") or user.get("id")
                   or "(user, unnamed)")
    if owner_kind(key) == SERVICE_ACCOUNT:
        account = (owner.get("service_account")
                   if isinstance(owner.get("service_account"), dict) else {})
        return str(account.get("name") or account.get("id")
                   or "(service account, unnamed)")
    return "(owner type %r)" % str(owner.get("type"))


def fold_costs(pages):
    """Sum cost by api_key_id, keeping currency. Pure.

    Returns {api_key_id: {currency: amount}}. Currency is kept rather than
    dropped because an organization billed in more than one currency produces a
    meaningless number the moment the units are discarded.
    """
    out = {}
    for page in pages or []:
        for bucket in (page or {}).get("data") or []:
            for result in (bucket or {}).get("results") or []:
                key_id = (result or {}).get("api_key_id")
                amount = (result or {}).get("amount")
                if not key_id or not isinstance(amount, dict):
                    continue
                try:
                    value = float(amount.get("value") or 0)
                except (TypeError, ValueError):
                    continue
                currency = str(amount.get("currency") or "USD").upper()
                out.setdefault(str(key_id), {})
                out[str(key_id)][currency] = \\
                    out[str(key_id)].get(currency, 0.0) + value
    return out


def spend_of(costs, key_id):
    """The largest single-currency amount recorded for one key. Pure.

    Used only to compare against a threshold. Taking the maximum rather than a
    sum keeps the comparison honest in a multi-currency organization without
    inventing an exchange rate.
    """
    by_currency = (costs or {}).get(str(key_id or ""), {})
    return max(by_currency.values()) if by_currency else 0.0


def spend_line(costs, key_id, days):
    """A printable spend summary for one key. Pure. Never adds currencies."""
    by_currency = (costs or {}).get(str(key_id or ""), {})
    if not by_currency:
        return "no cost rows in %d day(s)" % days
    parts = ["%.2f %s" % (value, currency)
             for currency, value in sorted(by_currency.items())]
    return "%s over %d day(s)" % (" + ".join(parts), days)


def verdict(key, key_spend, service_account_count, min_spend=1.0):
    """Classify one key by who owns it. Pure. Returns (state, detail).

    Deliberately not given an organization total. The share of the bill this
    key holds is not an input, cannot be an input, and is the subject of a
    different note; a personal key carrying three per cent of production spend
    grades exactly as a personal key carrying ninety-five.
    """
    kind = owner_kind(key)
    if kind == SERVICE_ACCOUNT:
        return (FINE, "owned by a service account")
    if kind == UNKNOWN:
        return (UNATTRIBUTABLE,
                "the owner block is missing or its type is unrecognised, so "
                "nobody can say whose lifecycle this credential is attached to")
    if float(key_spend or 0) >= float(min_spend):
        return (IN_PRODUCTION,
                "a person owns a credential carrying production spend%s"
                % (", in a project with no service accounts at all"
                   if not service_account_count else ""))
    return (IDLE,
            "owned by a person and carrying no measurable spend, so this is a "
            "revocation rather than a migration")


def project_note(project_name, user_owned_spending, service_account_count):
    """The project-level finding, printed once per project. Pure.

    A project with spending personal keys and an empty service-account roster
    has not made a mistake in one place. It has never had the mechanism, and
    the repair is different: create the first one rather than migrate to the
    existing ones.
    """
    if user_owned_spending and not service_account_count:
        return ("project %s: no service accounts at all, and %d user-owned "
                "key(s) are spending" % (project_name, user_owned_spending))
    return None


def migration_plan(project_id, key_id, key_name):
    """The ordered cutover, printed and never performed. Pure.

    Revocation is last because the service-account key value is returned once
    at creation and because removing the old key before traffic moves is an
    outage rather than a rotation.
    """
    return [
        "create a service account for the service: an admin POST to "
        "/v1/organization/projects/%s/service_accounts with a name that "
        "matches the deployable unit, not the person." % project_id,
        "mint its key under /v1/organization/projects/%s/service_accounts/"
        "{service_account_id}/api_keys. The value is returned exactly once, "
        "so capture it into the secret store in the same step." % project_id,
        "deploy the new value, then re-read the cost report grouped by "
        "api_key_id and confirm the spend has moved off %s (%s)."
        % (key_name, key_id),
        "only then revoke the old key with a DELETE on "
        "/v1/organization/projects/%s/api_keys/%s." % (project_id, key_id),
    ]


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an admin "
                         "key (sk-admin-), not a project key" % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, params):
    """Walk an administration listing on has_more / last_id."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("last_id"):
            return
        params["after"] = page["last_id"]


def collect(session, path, params):
    rows = []
    for page in paged(session, path, params):
        rows.extend(page.get("data") or [])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of cost to join by api_key_id (default 30)")
    ap.add_argument("--min-spend", type=float, default=1.0,
                    help="spend above which a personal key is production")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an admin key (sk-admin-) with read "
                  "scopes; a project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    start = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=args.days)).timestamp())
    costs = fold_costs(paged(s, "/organization/costs",
                             {"start_time": start, "limit": min(args.days, 180),
                              "group_by": "api_key_id"}))

    projects = collect(s, "/organization/projects",
                       {"limit": 100, "include_archived": "true"})

    total_keys = 0
    user_owned = 0
    findings = 0
    empty_rosters = 0

    for project in projects:
        pid = project.get("id")
        if not pid:
            continue
        name = project.get("name") or pid
        keys = collect(s, "/organization/projects/%s/api_keys" % pid,
                       {"limit": 100, "owner_project_access": "any"})
        accounts = collect(s, "/organization/projects/%s/service_accounts" % pid,
                           {"limit": 100})
        total_keys += len(keys)

        graded = []
        for key in keys:
            key_spend = spend_of(costs, key.get("id"))
            state, detail = verdict(key, key_spend, len(accounts), args.min_spend)
            graded.append((key, state, detail, key_spend))
            if owner_kind(key) == USER:
                user_owned += 1

        spending = sum(1 for _, state, _, _ in graded if state == IN_PRODUCTION)
        note = project_note(name, spending, len(accounts))
        if note:
            empty_rosters += 1
            log.warning(note)

        for key, state, detail, _ in sorted(
                graded, key=lambda row: -spend_of(costs, row[0].get("id"))):
            if state not in FINDINGS:
                continue
            findings += 1
            log.warning("%-27s %-12s %-12s %s  %-24s %s", state, name,
                        key.get("name") or "(unnamed)",
                        safe_hint(key.get("redacted_value")), owner_label(key),
                        spend_line(costs, key.get("id"), args.days))
            log.warning("  detail: %s", detail)
            if state == IN_PRODUCTION:
                for step in migration_plan(pid, key.get("id"),
                                           key.get("name") or "(unnamed)"):
                    log.warning("  repair: %s", step)
            elif state == IDLE:
                log.warning("  repair: no traffic behind this one, so it is a "
                            "revocation rather than a migration.")

    log.info("%d project(s), %d key(s), %d owned by a user", len(projects),
             total_keys, user_owned)
    log.info("%d finding(s), %d project(s) with no service accounts",
             findings, empty_rosters)
    log.info("share of the bill is not part of any verdict above: that is a "
             "different note and a different repair")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-user-owned-key-audit.mjs",
"js": '''/**
 * Find production keys whose owner is a person rather than a service account.
 *
 * Read only. Three GETs against the OpenAI Administration API with an admin
 * key. Nothing is created, changed or removed, and no key value is printed.
 *
 * The finding is the ownership type. The verdict function is never given an
 * organization total, so the share of the bill a key holds cannot influence
 * its grade: two personal keys splitting production spend evenly are two
 * findings here.
 *
 * Anthropic is not covered. Its key object has no owner-type distinction
 * between a person's credential and a service one, and no project
 * service-account object to compare against.
 */
const API = 'https://api.openai.com/v1';

export const USER = 'user';
export const SERVICE_ACCOUNT = 'service_account';
export const UNKNOWN = 'unknown';

export const IN_PRODUCTION = 'personal-key-in-production';
export const IDLE = 'personal-key-idle';
export const UNATTRIBUTABLE = 'unattributable-owner';
export const FINE = 'service-account-key';
const FINDINGS = new Set([IN_PRODUCTION, IDLE, UNATTRIBUTABLE]);

/** A key hint that is safe to print. Pure. Anything unredacted is withheld. */
export function safeHint(value) {
  const text = String(value ?? '').trim();
  if (!text) return '(no hint)';
  if ((!text.includes('...') && !text.includes('*')) || text.length > 40) {
    return '(hint withheld)';
  }
  return text;
}

/** Is this key owned by a person or a service account? Pure. Unknown stays unknown. */
export function ownerKind(key) {
  const owner = (key ?? {}).owner;
  if (!owner || typeof owner !== 'object') return UNKNOWN;
  const kind = String(owner.type ?? '').trim().toLowerCase();
  return (kind === USER || kind === SERVICE_ACCOUNT) ? kind : UNKNOWN;
}

/** A printable identity for the key's owner. Pure. Never a key value. */
export function ownerLabel(key) {
  const owner = (key ?? {}).owner;
  if (!owner || typeof owner !== 'object') return '(no owner block)';
  const kind = ownerKind(key);
  if (kind === USER) {
    const user = (owner.user && typeof owner.user === 'object') ? owner.user : {};
    return String(user.email ?? user.name ?? user.id ?? '(user, unnamed)');
  }
  if (kind === SERVICE_ACCOUNT) {
    const account = (owner.service_account && typeof owner.service_account === 'object')
      ? owner.service_account : {};
    return String(account.name ?? account.id ?? '(service account, unnamed)');
  }
  return `(owner type ${JSON.stringify(String(owner.type))})`;
}

/** Sum cost by api_key_id, keeping currency. Pure. */
export function foldCosts(pages) {
  const out = {};
  for (const page of pages ?? []) {
    for (const bucket of page?.data ?? []) {
      for (const result of bucket?.results ?? []) {
        const keyId = result?.api_key_id;
        const amount = result?.amount;
        if (!keyId || !amount || typeof amount !== 'object') continue;
        const value = Number(amount.value ?? 0);
        if (!Number.isFinite(value)) continue;
        const currency = String(amount.currency ?? 'USD').toUpperCase();
        out[String(keyId)] = out[String(keyId)] ?? {};
        out[String(keyId)][currency] = (out[String(keyId)][currency] ?? 0) + value;
      }
    }
  }
  return out;
}

/** The largest single-currency amount recorded for one key. Pure. */
export function spendOf(costs, keyId) {
  const byCurrency = (costs ?? {})[String(keyId ?? '')] ?? {};
  const values = Object.values(byCurrency);
  return values.length ? Math.max(...values) : 0;
}

/** A printable spend summary for one key. Pure. Never adds currencies. */
export function spendLine(costs, keyId, days) {
  const byCurrency = (costs ?? {})[String(keyId ?? '')] ?? {};
  const entries = Object.entries(byCurrency).sort(([a], [b]) => a.localeCompare(b));
  if (!entries.length) return `no cost rows in ${days} day(s)`;
  const parts = entries.map(([currency, value]) => `${value.toFixed(2)} ${currency}`);
  return `${parts.join(' + ')} over ${days} day(s)`;
}

/** Classify one key by who owns it. Pure. No organization total is an input. */
export function verdict(key, keySpend, serviceAccountCount, minSpend = 1.0) {
  const kind = ownerKind(key);
  if (kind === SERVICE_ACCOUNT) return [FINE, 'owned by a service account'];
  if (kind === UNKNOWN) {
    return [UNATTRIBUTABLE,
      'the owner block is missing or its type is unrecognised, so nobody can ' +
      'say whose lifecycle this credential is attached to'];
  }
  if (Number(keySpend ?? 0) >= Number(minSpend)) {
    return [IN_PRODUCTION,
      'a person owns a credential carrying production spend' +
      (serviceAccountCount ? '' : ', in a project with no service accounts at all')];
  }
  return [IDLE,
    'owned by a person and carrying no measurable spend, so this is a ' +
    'revocation rather than a migration'];
}

/** The project-level finding, printed once per project. Pure. */
export function projectNote(projectName, userOwnedSpending, serviceAccountCount) {
  if (userOwnedSpending && !serviceAccountCount) {
    return `project ${projectName}: no service accounts at all, and ` +
           `${userOwnedSpending} user-owned key(s) are spending`;
  }
  return null;
}

/** The ordered cutover, printed and never performed. Pure. */
export function migrationPlan(projectId, keyId, keyName) {
  return [
    'create a service account for the service: an admin POST to ' +
    `/v1/organization/projects/${projectId}/service_accounts with a name ` +
    'that matches the deployable unit, not the person.',
    `mint its key under /v1/organization/projects/${projectId}/service_accounts/` +
    '{service_account_id}/api_keys. The value is returned exactly once, so ' +
    'capture it into the secret store in the same step.',
    'deploy the new value, then re-read the cost report grouped by ' +
    `api_key_id and confirm the spend has moved off ${keyName} (${keyId}).`,
    'only then revoke the old key with a DELETE on ' +
    `/v1/organization/projects/${projectId}/api_keys/${keyId}.`,
  ];
}

async function getJson(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function collect(key, path, params) {
  const rows = [];
  const pages = [];
  let after = null;
  for (;;) {
    const page = await getJson(key, path, after ? { ...params, after } : params);
    pages.push(page);
    rows.push(...(page.data ?? []));
    if (!page.has_more || !page.last_id) return { rows, pages };
    after = page.last_id;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an admin key (sk-admin-) with read ' +
                  'scopes; a project key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const minSpend = Number(process.env.MIN_SPEND ?? 1.0);
  const start = Math.floor(Date.now() / 1000) - days * 86400;

  const costPages = await collect(admin, '/organization/costs', {
    start_time: start, limit: Math.min(days, 180), group_by: 'api_key_id' });
  const costs = foldCosts(costPages.pages);

  const projects = (await collect(admin, '/organization/projects',
                                  { limit: 100, include_archived: 'true' })).rows;

  let totalKeys = 0;
  let userOwned = 0;
  let findings = 0;
  let emptyRosters = 0;

  for (const project of projects) {
    if (!project.id) continue;
    const name = project.name ?? project.id;
    const keys = (await collect(admin, `/organization/projects/${project.id}/api_keys`,
                                { limit: 100, owner_project_access: 'any' })).rows;
    const accounts = (await collect(
      admin, `/organization/projects/${project.id}/service_accounts`, { limit: 100 })).rows;
    totalKeys += keys.length;

    const graded = keys.map((key) => {
      const keySpend = spendOf(costs, key.id);
      const [state, detail] = verdict(key, keySpend, accounts.length, minSpend);
      if (ownerKind(key) === USER) userOwned += 1;
      return { key, state, detail, keySpend };
    });

    const spending = graded.filter((row) => row.state === IN_PRODUCTION).length;
    const note = projectNote(name, spending, accounts.length);
    if (note) { emptyRosters += 1; console.warn(note); }

    for (const row of graded.sort((a, b) => b.keySpend - a.keySpend)) {
      if (!FINDINGS.has(row.state)) continue;
      findings += 1;
      console.warn(`${row.state.padEnd(27)} ${String(name).padEnd(12)} ` +
                   `${String(row.key.name ?? '(unnamed)').padEnd(12)} ` +
                   `${safeHint(row.key.redacted_value)}  ` +
                   `${ownerLabel(row.key).padEnd(24)} ` +
                   `${spendLine(costs, row.key.id, days)}`);
      console.warn(`  detail: ${row.detail}`);
      if (row.state === IN_PRODUCTION) {
        for (const step of migrationPlan(project.id, row.key.id,
                                         row.key.name ?? '(unnamed)')) {
          console.warn(`  repair: ${step}`);
        }
      } else if (row.state === IDLE) {
        console.warn('  repair: no traffic behind this one, so it is a ' +
                     'revocation rather than a migration.');
      }
    }
  }

  console.log(`${projects.length} project(s), ${totalKeys} key(s), ` +
              `${userOwned} owned by a user`);
  console.log(`${findings} finding(s), ${emptyRosters} project(s) with no service accounts`);
  console.log('share of the bill is not part of any verdict above: that is a ' +
              'different note and a different repair');
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the distinctness rule written as an assertion: the same personal key graded against three per cent of the bill and against ninety-five per cent has to produce the identical verdict, and two keys splitting production spend evenly have to produce two findings rather than none. That is the line between this note and the published concentration note, and it is checked rather than promised. The rest: an owner block that is missing or carries an unexpected type, which must land in <code>unattributable-owner</code> and never in either camp; the empty service-account roster, which is a project-level line and not a per-key one; a two-currency organization, whose amounts must be reported side by side and never added; and the migration plan, whose revocation step must come last.",
"test_py_file": "test_openai_user_owned_key_audit.py",
"test_py": '''from openai_user_owned_key_audit import (fold_costs, migration_plan,
                                          owner_kind, owner_label,
                                          project_note, safe_hint, spend_line,
                                          spend_of, verdict)


def user_key(key_id, name, email):
    return {"id": key_id, "name": name, "redacted_value": "sk-...9c31",
            "owner": {"type": "user", "user": {"id": "user_1", "email": email}},
            "owner_project_access": "active"}


def service_key(key_id, name):
    return {"id": key_id, "name": name, "redacted_value": "sk-...aa02",
            "owner": {"type": "service_account",
                      "service_account": {"id": "svc_1", "name": "ingest"}}}


def cost_page(rows):
    return {"data": [{"results": [
        {"api_key_id": key_id, "amount": {"value": value, "currency": currency}}
        for key_id, value, currency in rows]}], "has_more": False}


def test_the_share_of_the_bill_is_not_part_of_the_verdict():
    # The line between this note and the published concentration note, as an
    # assertion. One key holding 3% of production grades exactly as one
    # holding 95%, and an even split is two findings rather than none.
    key = user_key("key_1", "api-main", "marco@example.test")
    tiny = verdict(key, 340.00, service_account_count=2)
    huge = verdict(key, 11402.88, service_account_count=2)
    assert tiny[0] == huge[0] == "personal-key-in-production"
    assert tiny[1] == huge[1]

    even = fold_costs([cost_page([("key_1", 5000.0, "USD"),
                                  ("key_2", 5000.0, "USD")])])
    a = verdict(user_key("key_1", "api-main", "marco@example.test"),
                spend_of(even, "key_1"), 1)
    b = verdict(user_key("key_2", "worker-2", "dana@example.test"),
                spend_of(even, "key_2"), 1)
    assert [a[0], b[0]] == ["personal-key-in-production"] * 2


def test_a_personal_key_with_no_traffic_is_a_different_repair():
    key = user_key("key_9", "scratch", "marco@example.test")
    state, detail = verdict(key, 0.0, service_account_count=2)
    assert state == "personal-key-idle"
    assert "revocation rather than a migration" in detail
    assert verdict(service_key("key_s", "ingest"), 90000.0, 2)[0] == \\
        "service-account-key"


def test_an_unrecognised_owner_is_never_folded_into_either_camp():
    assert owner_kind({"owner": {"type": "user"}}) == "user"
    assert owner_kind({"owner": {"type": "SERVICE_ACCOUNT"}}) == "service_account"
    assert owner_kind({"owner": {"type": "robot"}}) == "unknown"
    assert owner_kind({"owner": None}) == "unknown"
    assert owner_kind({}) == "unknown"
    assert owner_kind(None) == "unknown"
    state, detail = verdict({"owner": {"type": "robot"}}, 4000.0, 3)
    assert state == "unattributable-owner"
    assert "whose lifecycle" in detail
    assert owner_label({"owner": {"type": "robot"}}) == "(owner type 'robot')"
    assert owner_label(user_key("k", "n", "d@example.test")) == "d@example.test"
    assert owner_label(service_key("k", "n")) == "ingest"
    assert owner_label({}) == "(no owner block)"


def test_an_empty_service_account_roster_is_a_project_level_finding():
    assert project_note("proj_prod", 2, 0) == \\
        "project proj_prod: no service accounts at all, and 2 user-owned key(s) are spending"
    assert project_note("proj_prod", 2, 3) is None
    assert project_note("proj_evals", 0, 0) is None
    state, detail = verdict(user_key("key_1", "api-main", "m@example.test"),
                            9000.0, service_account_count=0)
    assert state == "personal-key-in-production"
    assert "no service accounts at all" in detail


def test_two_currencies_are_reported_side_by_side_and_never_added():
    costs = fold_costs([cost_page([("key_1", 400.0, "USD"),
                                   ("key_1", 300.0, "USD"),
                                   ("key_1", 120.0, "EUR")])])
    assert costs["key_1"] == {"USD": 700.0, "EUR": 120.0}
    line = spend_line(costs, "key_1", 30)
    assert line == "120.00 EUR + 700.00 USD over 30 day(s)"
    assert "820" not in line
    # The threshold comparison uses the largest single currency, never a total.
    assert spend_of(costs, "key_1") == 700.0
    assert spend_of(costs, "key_absent") == 0.0
    assert spend_line(costs, "key_absent", 30) == "no cost rows in 30 day(s)"


def test_cost_rows_that_cannot_be_read_are_skipped_rather_than_guessed():
    costs = fold_costs([{"data": [{"results": [
        {"api_key_id": None, "amount": {"value": 5.0, "currency": "USD"}},
        {"api_key_id": "key_1", "amount": None},
        {"api_key_id": "key_1", "amount": {"value": "many", "currency": "USD"}},
        {"api_key_id": "key_1", "amount": {"value": 12.5}},
    ]}]}])
    assert costs == {"key_1": {"USD": 12.5}}
    assert fold_costs([]) == {}
    assert fold_costs(None) == {}


def test_the_migration_puts_the_revocation_last():
    steps = migration_plan("proj_prod", "key_1", "api-main")
    assert len(steps) == 4
    assert "service_accounts" in steps[0]
    assert "returned exactly once" in steps[1]
    assert "confirm the spend has moved off" in steps[2]
    assert steps[3].startswith("only then revoke")
    assert safe_hint("sk-...9c31") == "sk-...9c31"
    assert safe_hint("sk-fake-whole-value-here") == "(hint withheld)"
    assert safe_hint(None) == "(no hint)"
''',
"test_js_file": "openai-user-owned-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { foldCosts, migrationPlan, ownerKind, ownerLabel, projectNote,
         safeHint, spendLine, spendOf, verdict }
  from './openai-user-owned-key-audit.mjs';

const userKey = (id, name, email) => ({
  id, name, redacted_value: 'sk-...9c31',
  owner: { type: 'user', user: { id: 'user_1', email } },
  owner_project_access: 'active',
});

const serviceKey = (id, name) => ({
  id, name, redacted_value: 'sk-...aa02',
  owner: { type: 'service_account', service_account: { id: 'svc_1', name: 'ingest' } },
});

const costPage = (rows) => ({
  data: [{ results: rows.map(([api_key_id, value, currency]) =>
    ({ api_key_id, amount: { value, currency } })) }],
  has_more: false,
});

test('the share of the bill is not part of the verdict', () => {
  const key = userKey('key_1', 'api-main', 'marco@example.test');
  const tiny = verdict(key, 340.0, 2);
  const huge = verdict(key, 11402.88, 2);
  assert.equal(tiny[0], 'personal-key-in-production');
  assert.deepEqual(tiny, huge);

  const even = foldCosts([costPage([['key_1', 5000.0, 'USD'],
                                    ['key_2', 5000.0, 'USD']])]);
  assert.equal(verdict(userKey('key_1', 'api-main', 'm@example.test'),
                       spendOf(even, 'key_1'), 1)[0], 'personal-key-in-production');
  assert.equal(verdict(userKey('key_2', 'worker-2', 'd@example.test'),
                       spendOf(even, 'key_2'), 1)[0], 'personal-key-in-production');
});

test('a personal key with no traffic is a different repair', () => {
  const [state, detail] = verdict(userKey('key_9', 'scratch', 'm@example.test'), 0.0, 2);
  assert.equal(state, 'personal-key-idle');
  assert.match(detail, /revocation rather than a migration/);
  assert.equal(verdict(serviceKey('key_s', 'ingest'), 90000.0, 2)[0],
               'service-account-key');
});

test('an unrecognised owner is never folded into either camp', () => {
  assert.equal(ownerKind({ owner: { type: 'user' } }), 'user');
  assert.equal(ownerKind({ owner: { type: 'SERVICE_ACCOUNT' } }), 'service_account');
  assert.equal(ownerKind({ owner: { type: 'robot' } }), 'unknown');
  assert.equal(ownerKind({ owner: null }), 'unknown');
  assert.equal(ownerKind({}), 'unknown');
  assert.equal(ownerKind(null), 'unknown');
  const [state, detail] = verdict({ owner: { type: 'robot' } }, 4000.0, 3);
  assert.equal(state, 'unattributable-owner');
  assert.match(detail, /whose lifecycle/);
  assert.equal(ownerLabel(userKey('k', 'n', 'd@example.test')), 'd@example.test');
  assert.equal(ownerLabel(serviceKey('k', 'n')), 'ingest');
  assert.equal(ownerLabel({}), '(no owner block)');
});

test('an empty service account roster is a project level finding', () => {
  assert.equal(projectNote('proj_prod', 2, 0),
    'project proj_prod: no service accounts at all, and 2 user-owned key(s) are spending');
  assert.equal(projectNote('proj_prod', 2, 3), null);
  assert.equal(projectNote('proj_evals', 0, 0), null);
  const [state, detail] = verdict(userKey('key_1', 'api-main', 'm@example.test'), 9000.0, 0);
  assert.equal(state, 'personal-key-in-production');
  assert.match(detail, /no service accounts at all/);
});

test('two currencies are reported side by side and never added', () => {
  const costs = foldCosts([costPage([['key_1', 400.0, 'USD'],
                                     ['key_1', 300.0, 'USD'],
                                     ['key_1', 120.0, 'EUR']])]);
  assert.deepEqual(costs.key_1, { USD: 700.0, EUR: 120.0 });
  const line = spendLine(costs, 'key_1', 30);
  assert.equal(line, '120.00 EUR + 700.00 USD over 30 day(s)');
  assert.ok(!line.includes('820'));
  assert.equal(spendOf(costs, 'key_1'), 700.0);
  assert.equal(spendOf(costs, 'key_absent'), 0);
  assert.equal(spendLine(costs, 'key_absent', 30), 'no cost rows in 30 day(s)');
});

test('cost rows that cannot be read are skipped rather than guessed', () => {
  const costs = foldCosts([{ data: [{ results: [
    { api_key_id: null, amount: { value: 5.0, currency: 'USD' } },
    { api_key_id: 'key_1', amount: null },
    { api_key_id: 'key_1', amount: { value: 'many', currency: 'USD' } },
    { api_key_id: 'key_1', amount: { value: 12.5 } },
  ] }] }]);
  assert.deepEqual(costs, { key_1: { USD: 12.5 } });
  assert.deepEqual(foldCosts([]), {});
  assert.deepEqual(foldCosts(null), {});
});

test('the migration puts the revocation last', () => {
  const steps = migrationPlan('proj_prod', 'key_1', 'api-main');
  assert.equal(steps.length, 4);
  assert.match(steps[0], /service_accounts/);
  assert.match(steps[1], /returned exactly once/);
  assert.match(steps[2], /confirm the spend has moved off/);
  assert.ok(steps[3].startsWith('only then revoke'));
  assert.equal(safeHint('sk-...9c31'), 'sk-...9c31');
  assert.equal(safeHint('sk-fake-whole-value-here'), '(hint withheld)');
  assert.equal(safeHint(null), '(no hint)');
});
''',
"faq": [
 ("Is this not the same as finding the key that dominates the bill?",
  "No, and the difference is worth being precise about because both start from group_by=api_key_id. The concentration note asks whether one key holds most of the money, and its repair is to split traffic across several keys so that spend can be attributed and capped. This note asks who owns the credential, and its repair is to move the traffic from a person to a service account. An organization that split its traffic across six evenly-loaded keys has fixed the first problem completely; if all six belong to engineers, it has not touched this one. The verdict function here is not even given an organization total, so a share cannot influence it."),
 ("Nothing has gone wrong in two years. Why is this a finding at all?",
  "Because the failure mode is not gradual. As long as the person stays in place with their access unchanged, a personal key behaves exactly like a service credential, which is why these survive for years. The problem is that the credential's lifetime is bound to an employment record: a team move, a departure, or a routine access review can end it, and the first symptom is production failing to authenticate. Finding it while everything is fine means you do a planned rotation with a deploy in the middle. Finding it afterwards means you do the same work at 2am."),
 ("What does the service-account list add that the key list does not?",
  "It separates a straggler from a project that has never had the mechanism. A project with eight service accounts and one personal key left over has a migration to finish. A project with spending personal keys and an empty service-account roster has no alternative in place at all, so the repair is not to move this key but to create the first service account this project has ever had, and it applies to every key in there rather than to one. The script prints that once per project rather than repeating it per key."),
 ("Why not run the same check against Anthropic?",
  "Because the field does not exist. Anthropic's API key object carries id, created_at, created_by, expires_at, name, partial_key_hint, principal, scope, status and type, and there is no project service-account object anywhere in the Admin API to compare a key against. created_by tells you which member minted the key, which is a genuinely useful field and a different question, and it is the one the published note on keys whose owner has left already uses. Writing an Anthropic half here would mean presenting created_by as if it were owner.type, which is not what it means."),
 ("Can the script do the migration if I give it a write-scoped key?",
  "It has no write path to enable. There is no flag, no confirmation prompt and no code that issues anything but a GET, which is a deliberate property of every script in this section rather than a default that can be turned off. The migration is printed in order for a reason too: the service-account key value is returned exactly once at creation, and revoking the old key before the new one is deployed and verified is an outage rather than a rotation. Both of those steps want a human watching them."),
],
"related": [REL_OWNER_GONE, REL_DOMINATES, REL_ROTATION],
"citations": [CITE_PROJECT_KEYS, CITE_PROJECTS, CITE_COSTS,
              CITE_MANAGING_PROJECTS],
},
{
"slug": "service-account-key-never-rotated",
"title": "A service account key that has never been rotated",
"description": "Take the newest key age per service account. Past 180 days with only one key there is no overlap to rotate through, and the audit log confirms only per project.",
"h1": "A service account key that has never been rotated",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai service account key rotation",
             "openai api key created_at age audit",
             "zero downtime openai key rotation",
             "openai audit_logs api_key.created",
             "rotate llm api credentials policy"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an sk-admin- key with read scopes. The audit-log half degrades gracefully when the organization does not have audit logging enabled.",
"lead": "This one is the reward for having done it right. Somebody read the guidance, created service accounts, moved production onto them and deleted the personal keys, and every audit since has come back clean because every audit since has been looking for personal keys. The service account was created in February two years ago. Its key was minted the same afternoon. There has never been a second key, so there has never been a moment when two keys were valid at once, so rotation has never been a deploy with a rollback: it has always been a hard cutover with an outage on the other side of it. Which is why it keeps being scheduled for next quarter.",
"short_answer": """<p>With an <strong>organization admin key</strong>, per project: <code>GET /v1/organization/projects/{project_id}/service_accounts?limit=100</code> for the roster, then <code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code> filtered to <code>owner.type == "service_account"</code>. Group the keys by <code>owner.service_account.id</code> and take the <strong>newest</strong> <code>created_at</code> in each group. Anything past 180 days has not been rotated in six months.</p>
<p>Then read how many keys that account has, because the count changes the finding. <strong>One stale key is worse than two.</strong> With a single key there is no overlap window: swapping it means the old value stops working the instant the new one starts, which is a hard cutover with no rollback, and that is the actual reason the rotation keeps getting deferred rather than laziness.</p>
<p>Corroborate with <code>GET /v1/organization/audit_logs?event_types[]=api_key.created&amp;effective_at[gte]={now-180d}&amp;limit=100</code>. No <code>api_key.created</code> event for a project in the window means nothing has been minted there in six months. Read that carefully: the event carries <code>project.id</code> and <code>actor</code> and <strong>does not name a service account</strong>, so an absence is a fact about the project and never about one account. And if audit logging is not enabled for your organization, the endpoint's silence is not evidence of anything at all.</p>""",
"problem": """<p>Service accounts fix ownership and nothing else. They detach the credential from a person's employment, which is the whole reason to use them, and in doing so they remove the last event that ever forced anybody to think about the key again. A personal key at least has an owner who eventually changes teams. A service account has nobody, no expiry, and no prompt.</p>
<p>So the key ages, and nothing about it degrades. It authenticates as well on day 900 as on day one. There is no error, no warning, no field that turns amber, and no read-only endpoint anywhere that reports when a credential was last rotated, because no such field exists on either provider. The only evidence available is <code>created_at</code>, and <code>created_at</code> looks identical on a key minted last month as part of a disciplined quarterly rotation and on a key minted last month because the service is new.</p>
<p>The single-key case is the one that explains the whole pattern. Rotation is safe when two keys can be valid at once: mint the second, deploy it, watch the first go quiet, remove it. A service account with exactly one key has never been in that shape, so every rotation attempt is a synchronised cutover across every deployment that holds the value. That is a change with a real chance of an outage and no obvious rollback, which is why it is always the thing being planned rather than the thing being done.</p>""",
"why": """<p><strong>This clock is the one the other key notes ignore, and it points at the healthiest credential in the organization.</strong> <a href="/llm/api-key-never-used/">The idleness note</a> finds keys with no traffic. This one finds the opposite: a key used every second of every day, owned exactly as the guidance says it should be, and two years old. Nothing in a usage-based sweep can surface it, because on every usage measure it is the best-behaved key you have.</p>
<p><strong>Key count is part of the verdict, not a detail in the output.</strong> One stale key means no overlap window has ever existed and the rotation is a cutover. Two keys where both are stale means overlap is possible and simply was not used. One fresh key beside one stale one is a rotation that started and never finished, which is the state that most deserves a nudge because somebody already did the risky part and left the old credential live. Three different findings, three different sentences, one <code>created_at</code> field.</p>
<p><strong>The audit log confirms an absence at the project level and nothing finer.</strong> The <code>api_key.created</code> event carries <code>id</code>, <code>data.scopes</code>, <code>effective_at</code>, <code>project.id</code> and <code>actor</code>. It does not carry the service account the key belongs to. So "no creation events in this project for 180 days" is a sound conclusion about the project, and "therefore this particular service account was not rotated" is an inference the script declines to print as a fact. The per-account claim rests on <code>created_at</code> in the key list, which is where it belongs.</p>
<p><strong>An unreachable or empty audit log is not a clean one.</strong> Audit logging is gated to organizations that have it enabled, so an empty response can mean nothing happened or can mean nothing is being recorded. The script reports <code>audit-unavailable</code> and explicitly downgrades its own confidence rather than upgrading a silence into corroboration. It also backs off on a 429, because this is the one administration endpoint that documents its own rate limit with a <code>Retry-After</code>.</p>
<p><strong>Nothing here self-corrects, and one endpoint shows what it would look like if it did.</strong> Project API keys have no <code>expires_at</code> at all. Admin keys do, on <code>GET /v1/organization/admin_api_keys</code>, which is worth reading precisely because it demonstrates the field that would make this note unnecessary. Where you cannot set an expiry, the schedule has to live outside the platform, and a scheduled run of this script is the cheapest version of that.</p>""",
"steps": [
 {"h": "Use an admin key with read scopes",
  "body": """<p>Projects, service accounts, project keys and audit logs all live under <code>/v1/organization/*</code>, which rejects project keys. An <code>sk-admin-</code> key provisioned read-only reads all four.</p>"""},
 {"h": "Build the service-account roster per project",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/service_accounts?limit=100</code> returns <code>id</code>, <code>name</code>, <code>role</code> and <code>created_at</code>. Keep it even when a service account turns out to have no keys at all: that is its own small finding, and it usually means a half-finished migration.</p>"""},
 {"h": "Group the keys by owner.service_account.id and take the newest",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code>, filtered to <code>owner.type == "service_account"</code>. The <em>newest</em> <code>created_at</code> in each group is the rotation clock. Using the oldest instead reports a service account that rotated last week as stale, because the key it replaced is still sitting there.</p>"""},
 {"h": "Count the keys, because the count is the finding",
  "body": """<p>One key past the threshold is a cutover with no rollback. Two stale keys mean the overlap was available and unused. One fresh and one stale is a rotation that stopped halfway. Print the right sentence for each rather than one generic age warning.</p>"""},
 {"h": "Ask the audit log, and grade its answer honestly",
  "body": """<p><code>GET /v1/organization/audit_logs?event_types[]=api_key.created&amp;effective_at[gte]={now-180d}&amp;limit=100</code>, paginating on <code>after</code>. Zero events for a project corroborates at the project level. An empty log across the whole organization means audit logging may not be enabled, and the script says <code>audit-unavailable</code> rather than treating silence as agreement.</p>"""},
],
"verify": """<p>Re-run after a rotation. The account you rotated should show two keys with the newest one days old, then a single fresh key once the old one is revoked.</p>
<pre><code class="language-bash">python3 openai_key_rotation_clock.py --stale-after 180
# 6 project(s), 11 service account(s), 14 service-account key(s)
# audit log: 3 api_key.created event(s) in 180 day(s) across 2 project(s)
# single-stale-key   proj_prod   ingest-worker   newest key 731 day(s) old, and it is the only one
#   repair: mint a second key first. One key means every rotation is a hard cutover with no rollback.
# stale-key          proj_prod   billing-sync    newest key 402 day(s) old across 2 key(s)
# unfinished-rotation proj_api   search-indexer  newest key 12 day(s) old, oldest 588 day(s) and still live
#   repair: the new key is deployed. Confirm the old one has gone quiet, then revoke it.
# corroboration: proj_prod has no api_key.created events in 180 day(s) (project level, not per account)
# 3 finding(s)</code></pre>""",
"code_intro": "Four GETs and one clock. <code>newest_and_oldest</code> is where the note is won or lost: taking the newest <code>created_at</code> per account is what stops a freshly-rotated account being reported as stale because its retired key is still in the list. <code>rotation_verdict</code> takes the key count as a first-class input rather than a footnote, so a single stale key and two stale keys come back as different findings. <code>corroboration</code> is the honest one: it distinguishes a project with no creation events from an organization whose audit log is empty or unreachable, and it labels its own conclusion project-level because the <code>api_key.created</code> event does not name a service account. <code>rotation_plan</code> prints the overlap sequence with the revocation last.",
"py_file": "openai_key_rotation_clock.py",
"py": '''"""Find service account keys that have never been rotated.

Read only. Four GETs against the OpenAI Administration API with an admin key:
projects, service accounts, project keys and the audit log. Nothing is created,
changed or removed, and no key value is printed.

The clock is created_at on the newest key belonging to each service account.
There is no rotated_at field anywhere on either provider, so age since minting
is the only evidence available, and the key count decides which of three
findings it is.

The audit log corroborates an absence at the PROJECT level only: the
api_key.created event carries project.id and actor and does not name a service
account. An empty or unreachable audit log is reported as unavailable rather
than as agreement, because audit logging is gated to organizations that have it
enabled and silence from it means nothing either way.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_key_rotation_clock")

API = "https://api.openai.com/v1"

SINGLE_STALE = "single-stale-key"
STALE = "stale-key"
UNFINISHED = "unfinished-rotation"
NO_KEYS = "service-account-with-no-keys"
ROTATING = "rotating"
TOO_NEW = "too-new"
FINDINGS = (SINGLE_STALE, STALE, UNFINISHED, NO_KEYS)

AUDIT_CONFIRMED = "confirmed-at-project-level"
AUDIT_ACTIVITY = "creation-activity-in-window"
AUDIT_UNAVAILABLE = "audit-unavailable"


def age_days(stamp, now):
    """Whole days between a unix timestamp and now. Pure. None when unreadable."""
    if stamp is None or stamp == "" or isinstance(stamp, bool):
        return None
    try:
        when = dt.datetime.fromtimestamp(float(stamp), dt.timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    return int((now - when).total_seconds() // 86400)


def service_account_id(key):
    """The service account a key belongs to, or None. Pure."""
    owner = (key or {}).get("owner")
    if not isinstance(owner, dict):
        return None
    if str(owner.get("type") or "").strip().lower() != "service_account":
        return None
    account = owner.get("service_account")
    if not isinstance(account, dict):
        return None
    return str(account.get("id") or "") or None


def group_by_account(keys):
    """Group service-account keys by owner.service_account.id. Pure.

    Keys owned by a user are dropped here rather than counted as unattributed,
    because a personal key in a project is a finding for a different note and
    counting it towards a service account's key total would make a single-key
    account look like it has an overlap window it does not have.
    """
    out = {}
    for key in keys or []:
        account = service_account_id(key)
        if account:
            out.setdefault(account, []).append(key)
    return out


def newest_and_oldest(keys, now):
    """(newest_age, oldest_age) in days across a key group. Pure.

    The newest is the rotation clock. Using the oldest instead reports a
    service account that rotated last week as stale, because the key it
    replaced is still in the list until somebody revokes it.
    """
    ages = [a for a in (age_days((k or {}).get("created_at"), now) for k in keys or [])
            if a is not None]
    if not ages:
        return (None, None)
    return (min(ages), max(ages))


def rotation_verdict(account, keys, now, stale_after=180, min_age=30):
    """Classify one service account's rotation state. Pure. (state, detail).

    The key count is an input rather than a detail, because one stale key and
    two stale keys are different problems. With one key there has never been a
    moment when two credentials were valid at once, so every rotation is a
    synchronised cutover with no rollback, and that is the reason it keeps
    being deferred.
    """
    name = str((account or {}).get("name") or (account or {}).get("id") or "(unnamed)")
    rows = list(keys or [])
    if not rows:
        created = age_days((account or {}).get("created_at"), now)
        return (NO_KEYS,
                "service account %s has no keys at all%s"
                % (name, "" if created is None else
                   ", and was created %d day(s) ago" % created))

    newest, oldest = newest_and_oldest(rows, now)
    if newest is None:
        return (TOO_NEW, "no readable created_at on any of its %d key(s)" % len(rows))
    if newest < min_age and len(rows) == 1:
        return (TOO_NEW, "its only key is %d day(s) old" % newest)
    if newest < stale_after:
        if oldest >= stale_after and len(rows) > 1:
            return (UNFINISHED,
                    "newest key %d day(s) old, oldest %d day(s) and still live"
                    % (newest, oldest))
        return (ROTATING, "newest key %d day(s) old" % newest)
    if len(rows) == 1:
        return (SINGLE_STALE,
                "newest key %d day(s) old, and it is the only one" % newest)
    return (STALE,
            "newest key %d day(s) old across %d key(s)" % (newest, len(rows)))


def corroboration(events, project_id, audit_reachable=True, days=180):
    """What the audit log can and cannot confirm. Pure. (state, detail).

    Three outcomes and only one of them is corroboration. The api_key.created
    event names a project and an actor and never a service account, so the
    strongest available statement is about the project. An empty or unreachable
    log is reported as unavailable, because audit logging is gated and its
    silence is not evidence.
    """
    if not audit_reachable:
        return (AUDIT_UNAVAILABLE,
                "the audit log could not be read, so nothing here is "
                "corroborated. Audit logging is gated to organizations that "
                "have it enabled and its silence is not evidence.")
    rows = list(events or [])
    if not rows:
        return (AUDIT_UNAVAILABLE,
                "the audit log returned no events of any kind in %d day(s), "
                "which can mean nothing was minted or can mean nothing is "
                "being recorded. Treated as unavailable rather than clean."
                % days)
    here = [e for e in rows
            if str(((e or {}).get("project") or {}).get("id") or "") == str(project_id)]
    if here:
        return (AUDIT_ACTIVITY,
                "%d api_key.created event(s) in this project in %d day(s), so "
                "something was minted here. The event does not name a service "
                "account, so it neither confirms nor clears any one of them."
                % (len(here), days))
    return (AUDIT_CONFIRMED,
            "no api_key.created events in this project in %d day(s). That is a "
            "project-level fact: the event carries project.id and actor and "
            "not the service account, so the per-account age above remains the "
            "evidence for any single account." % days)


def rotation_plan(project_id, account_name, single_key):
    """The overlap rotation, printed and never performed. Pure."""
    steps = []
    if single_key:
        steps.append("mint a second key first. One key means every rotation is "
                     "a hard cutover with no rollback, which is the actual "
                     "reason this has not happened yet.")
    steps.extend([
        "mint the replacement with an admin POST to /v1/organization/projects/"
        "%s/service_accounts/{service_account_id}/api_keys for %s. The value "
        "is returned exactly once." % (project_id, account_name),
        "deploy the new value everywhere the old one is held, then watch the "
        "old key: its last_used_at should stop advancing within one traffic "
        "cycle. Do not skip this; it is the only rollback you get.",
        "revoke the old key with a DELETE on /v1/organization/projects/%s/"
        "api_keys/{api_key_id}, and diary the next rotation at 90 days. "
        "Project keys have no expires_at, so nothing will remind you."
        % project_id,
    ])
    return steps


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an admin "
                         "key (sk-admin-), not a project key" % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, params, limit_pages=20):
    """Walk an administration listing on has_more / last_id."""
    params = dict(params)
    for _ in range(limit_pages):
        page = get(session, path, params)
        yield page
        if not page.get("has_more") or not page.get("last_id"):
            return
        params["after"] = page["last_id"]


def collect(session, path, params):
    rows = []
    for page in paged(session, path, params):
        rows.extend(page.get("data") or [])
    return rows


def read_audit_log(session, days):
    """Read api_key.created events, tolerating an organization without them.

    Returns (events, reachable). A 4xx here is not fatal: audit logging is not
    enabled everywhere, and a script that dies on it would report nothing about
    the key ages it already has in hand.
    """
    since = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days)).timestamp())
    try:
        return (collect(session, "/organization/audit_logs",
                        {"limit": 100, "event_types[]": ["api_key.created"],
                         "effective_at[gte]": since}), True)
    except requests.HTTPError as err:
        status = getattr(getattr(err, "response", None), "status_code", None)
        log.warning("audit log unreadable (%s): rotation ages below stand on "
                    "created_at alone", status)
        return ([], False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stale-after", type=int, default=180,
                    help="days since the newest key was minted (default 180)")
    ap.add_argument("--min-age", type=int, default=30,
                    help="days before a new service account is graded at all")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an admin key (sk-admin-) with read "
                  "scopes; a project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    now = dt.datetime.now(dt.timezone.utc)

    events, reachable = read_audit_log(s, args.stale_after)
    if reachable:
        projects_seen = {str(((e or {}).get("project") or {}).get("id") or "")
                         for e in events}
        log.info("audit log: %d api_key.created event(s) in %d day(s) across "
                 "%d project(s)", len(events), args.stale_after,
                 len([p for p in projects_seen if p]))

    projects = collect(s, "/organization/projects",
                       {"limit": 100, "include_archived": "true"})

    accounts_seen = 0
    keys_seen = 0
    findings = 0

    for project in projects:
        pid = project.get("id")
        if not pid:
            continue
        name = project.get("name") or pid
        accounts = collect(s, "/organization/projects/%s/service_accounts" % pid,
                           {"limit": 100})
        keys = collect(s, "/organization/projects/%s/api_keys" % pid,
                       {"limit": 100, "owner_project_access": "any"})
        grouped = group_by_account(keys)
        accounts_seen += len(accounts)
        keys_seen += sum(len(v) for v in grouped.values())

        project_findings = 0
        for account in accounts:
            rows = grouped.get(str(account.get("id") or ""), [])
            state, detail = rotation_verdict(account, rows, now,
                                             args.stale_after, args.min_age)
            if state not in FINDINGS:
                continue
            findings += 1
            project_findings += 1
            log.warning("%-19s %-11s %-15s %s", state, name,
                        account.get("name") or account.get("id") or "(unnamed)",
                        detail)
            if state in (SINGLE_STALE, STALE, UNFINISHED):
                for step in rotation_plan(pid,
                                          account.get("name") or "(unnamed)",
                                          state == SINGLE_STALE):
                    log.warning("  repair: %s", step)

        if project_findings:
            audit_state, audit_detail = corroboration(events, pid, reachable,
                                                      args.stale_after)
            log.info("corroboration for %s: %s: %s", name, audit_state,
                     audit_detail)

    log.info("%d project(s), %d service account(s), %d service-account key(s)",
             len(projects), accounts_seen, keys_seen)
    log.info("%d finding(s)", findings)
    log.info("there is no rotated_at field on either provider: created_at on "
             "the newest key is the only clock available")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-key-rotation-clock.mjs",
"js": '''/**
 * Find service account keys that have never been rotated.
 *
 * Read only. Four GETs against the OpenAI Administration API with an admin
 * key. Nothing is created, changed or removed, and no key value is printed.
 *
 * The clock is created_at on the newest key belonging to each service account,
 * because no rotated_at field exists on either provider. The key count decides
 * which of three findings it is.
 *
 * The audit log corroborates an absence at the PROJECT level only: the
 * api_key.created event carries project.id and actor and does not name a
 * service account. An empty or unreachable log is reported as unavailable.
 */
const API = 'https://api.openai.com/v1';

export const SINGLE_STALE = 'single-stale-key';
export const STALE = 'stale-key';
export const UNFINISHED = 'unfinished-rotation';
export const NO_KEYS = 'service-account-with-no-keys';
export const ROTATING = 'rotating';
export const TOO_NEW = 'too-new';
const FINDINGS = new Set([SINGLE_STALE, STALE, UNFINISHED, NO_KEYS]);

export const AUDIT_CONFIRMED = 'confirmed-at-project-level';
export const AUDIT_ACTIVITY = 'creation-activity-in-window';
export const AUDIT_UNAVAILABLE = 'audit-unavailable';

/** Whole days between a unix timestamp and now. Pure. null when unreadable. */
export function ageDays(stamp, now) {
  if (stamp === null || stamp === undefined || stamp === '' ||
      typeof stamp === 'boolean') return null;
  const seconds = Number(stamp);
  if (!Number.isFinite(seconds)) return null;
  return Math.floor((now.getTime() - seconds * 1000) / 86400000);
}

/** The service account a key belongs to, or null. Pure. */
export function serviceAccountId(key) {
  const owner = (key ?? {}).owner;
  if (!owner || typeof owner !== 'object') return null;
  if (String(owner.type ?? '').trim().toLowerCase() !== 'service_account') return null;
  const account = owner.service_account;
  if (!account || typeof account !== 'object') return null;
  return String(account.id ?? '') || null;
}

/** Group service-account keys by owner.service_account.id. Pure. */
export function groupByAccount(keys) {
  const out = {};
  for (const key of keys ?? []) {
    const account = serviceAccountId(key);
    if (!account) continue;
    out[account] = out[account] ?? [];
    out[account].push(key);
  }
  return out;
}

/** [newestAge, oldestAge] in days across a key group. Pure. */
export function newestAndOldest(keys, now) {
  const ages = (keys ?? [])
    .map((k) => ageDays((k ?? {}).created_at, now))
    .filter((a) => a !== null);
  if (!ages.length) return [null, null];
  return [Math.min(...ages), Math.max(...ages)];
}

/** Classify one service account's rotation state. Pure. [state, detail]. */
export function rotationVerdict(account, keys, now, staleAfter = 180, minAge = 30) {
  const name = String((account ?? {}).name ?? (account ?? {}).id ?? '(unnamed)');
  const rows = [...(keys ?? [])];
  if (!rows.length) {
    const created = ageDays((account ?? {}).created_at, now);
    return [NO_KEYS,
      `service account ${name} has no keys at all` +
      (created === null ? '' : `, and was created ${created} day(s) ago`)];
  }
  const [newest, oldest] = newestAndOldest(rows, now);
  if (newest === null) {
    return [TOO_NEW, `no readable created_at on any of its ${rows.length} key(s)`];
  }
  if (newest < minAge && rows.length === 1) {
    return [TOO_NEW, `its only key is ${newest} day(s) old`];
  }
  if (newest < staleAfter) {
    if (oldest >= staleAfter && rows.length > 1) {
      return [UNFINISHED,
        `newest key ${newest} day(s) old, oldest ${oldest} day(s) and still live`];
    }
    return [ROTATING, `newest key ${newest} day(s) old`];
  }
  if (rows.length === 1) {
    return [SINGLE_STALE, `newest key ${newest} day(s) old, and it is the only one`];
  }
  return [STALE, `newest key ${newest} day(s) old across ${rows.length} key(s)`];
}

/** What the audit log can and cannot confirm. Pure. [state, detail]. */
export function corroboration(events, projectId, auditReachable = true, days = 180) {
  if (!auditReachable) {
    return [AUDIT_UNAVAILABLE,
      'the audit log could not be read, so nothing here is corroborated. ' +
      'Audit logging is gated to organizations that have it enabled and its ' +
      'silence is not evidence.'];
  }
  const rows = [...(events ?? [])];
  if (!rows.length) {
    return [AUDIT_UNAVAILABLE,
      `the audit log returned no events of any kind in ${days} day(s), which ` +
      'can mean nothing was minted or can mean nothing is being recorded. ' +
      'Treated as unavailable rather than clean.'];
  }
  const here = rows.filter(
    (e) => String((e?.project ?? {}).id ?? '') === String(projectId));
  if (here.length) {
    return [AUDIT_ACTIVITY,
      `${here.length} api_key.created event(s) in this project in ${days} ` +
      'day(s), so something was minted here. The event does not name a ' +
      'service account, so it neither confirms nor clears any one of them.'];
  }
  return [AUDIT_CONFIRMED,
    `no api_key.created events in this project in ${days} day(s). That is a ` +
    'project-level fact: the event carries project.id and actor and not the ' +
    'service account, so the per-account age above remains the evidence for ' +
    'any single account.'];
}

/** The overlap rotation, printed and never performed. Pure. */
export function rotationPlan(projectId, accountName, singleKey) {
  const steps = [];
  if (singleKey) {
    steps.push('mint a second key first. One key means every rotation is a ' +
               'hard cutover with no rollback, which is the actual reason ' +
               'this has not happened yet.');
  }
  steps.push(
    'mint the replacement with an admin POST to /v1/organization/projects/' +
    `${projectId}/service_accounts/{service_account_id}/api_keys for ` +
    `${accountName}. The value is returned exactly once.`,
    'deploy the new value everywhere the old one is held, then watch the old ' +
    'key: its last_used_at should stop advancing within one traffic cycle. ' +
    'Do not skip this; it is the only rollback you get.',
    `revoke the old key with a DELETE on /v1/organization/projects/${projectId}` +
    '/api_keys/{api_key_id}, and diary the next rotation at 90 days. Project ' +
    'keys have no expires_at, so nothing will remind you.');
  return steps;
}

async function getJson(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of params) url.searchParams.append(k, String(v));
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'admin key (sk-admin-), not a project key');
  }
  if (!res.ok) {
    const err = new Error(`${res.status} from ${path}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

async function collect(key, path, params) {
  const rows = [];
  let after = null;
  for (let page = 0; page < 20; page += 1) {
    const query = after ? [...params, ['after', after]] : params;
    const body = await getJson(key, path, query);
    rows.push(...(body.data ?? []));
    if (!body.has_more || !body.last_id) return rows;
    after = body.last_id;
  }
  return rows;
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an admin key (sk-admin-) with read ' +
                  'scopes; a project key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const staleAfter = Number(process.env.STALE_AFTER ?? 180);
  const minAge = Number(process.env.MIN_AGE ?? 30);
  const now = new Date();
  const since = Math.floor(now.getTime() / 1000) - staleAfter * 86400;

  let events = [];
  let reachable = true;
  try {
    events = await collect(admin, '/organization/audit_logs', [
      ['limit', 100], ['event_types[]', 'api_key.created'],
      ['effective_at[gte]', since]]);
    console.log(`audit log: ${events.length} api_key.created event(s) in ` +
                `${staleAfter} day(s)`);
  } catch (err) {
    reachable = false;
    console.warn(`audit log unreadable (${err.status ?? err.message}): ` +
                 'rotation ages below stand on created_at alone');
  }

  const projects = await collect(admin, '/organization/projects',
                                 [['limit', 100], ['include_archived', 'true']]);
  let accountsSeen = 0;
  let keysSeen = 0;
  let findings = 0;

  for (const project of projects) {
    if (!project.id) continue;
    const name = project.name ?? project.id;
    const accounts = await collect(
      admin, `/organization/projects/${project.id}/service_accounts`, [['limit', 100]]);
    const keys = await collect(
      admin, `/organization/projects/${project.id}/api_keys`,
      [['limit', 100], ['owner_project_access', 'any']]);
    const grouped = groupByAccount(keys);
    accountsSeen += accounts.length;
    keysSeen += Object.values(grouped).reduce((n, v) => n + v.length, 0);

    let projectFindings = 0;
    for (const account of accounts) {
      const rows = grouped[String(account.id ?? '')] ?? [];
      const [state, detail] = rotationVerdict(account, rows, now, staleAfter, minAge);
      if (!FINDINGS.has(state)) continue;
      findings += 1;
      projectFindings += 1;
      console.warn(`${state.padEnd(19)} ${String(name).padEnd(11)} ` +
                   `${String(account.name ?? account.id ?? '(unnamed)').padEnd(15)} ${detail}`);
      if (state === SINGLE_STALE || state === STALE || state === UNFINISHED) {
        for (const step of rotationPlan(project.id, account.name ?? '(unnamed)',
                                        state === SINGLE_STALE)) {
          console.warn(`  repair: ${step}`);
        }
      }
    }

    if (projectFindings) {
      const [auditState, auditDetail] =
        corroboration(events, project.id, reachable, staleAfter);
      console.log(`corroboration for ${name}: ${auditState}: ${auditDetail}`);
    }
  }

  console.log(`${projects.length} project(s), ${accountsSeen} service account(s), ` +
              `${keysSeen} service-account key(s)`);
  console.log(`${findings} finding(s)`);
  console.log('there is no rotated_at field on either provider: created_at on ' +
              'the newest key is the only clock available');
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the mistake that would make this note useless: an account that rotated last week still has its retired key in the list, so a reader that takes the <em>oldest</em> <code>created_at</code> reports it as two years stale. Reading the newest has to return <code>unfinished-rotation</code>, and once the retired key is revoked, nothing at all. The second is the count rule, three ways: one stale key, two stale keys and one fresh key beside one stale one are three findings with three different sentences, and only the first is told to mint a second key before touching anything. Then the honest half. <code>corroboration</code> has to return <code>audit-unavailable</code> for an empty log and for an unreachable one, and it must never claim that a project-level absence clears a specific service account. Finally: a key owned by a person must not be counted towards a service account's key total, or a single-key account looks like it has an overlap window it has never had.",
"test_py_file": "test_openai_key_rotation_clock.py",
"test_py": '''import datetime as dt

from openai_key_rotation_clock import (age_days, corroboration,
                                       group_by_account, newest_and_oldest,
                                       rotation_plan, rotation_verdict,
                                       service_account_id)

NOW = dt.datetime(2026, 8, 31, 12, 0, 0, tzinfo=dt.timezone.utc)
ACCOUNT = {"id": "svc_1", "name": "ingest-worker", "created_at": 0}


def unix(days_ago):
    return int((NOW - dt.timedelta(days=days_ago)).timestamp())


def sa_key(key_id, days_ago, account="svc_1"):
    return {"id": key_id, "created_at": unix(days_ago),
            "owner": {"type": "service_account",
                      "service_account": {"id": account, "name": "ingest-worker"}}}


def test_the_newest_key_is_the_clock_and_the_oldest_would_lie():
    # An account rotated last week still holds the retired key until somebody
    # revokes it. A reader that takes the oldest created_at calls that account
    # two years stale, which is the single mistake that would make this note
    # useless. Reading the newest calls it a rotation that has not been
    # finished, which is what it is.
    rotated = [sa_key("key_new", 45), sa_key("key_old", 731)]
    newest, oldest = newest_and_oldest(rotated, NOW)
    assert (newest, oldest) == (45, 731)
    state, detail = rotation_verdict(ACCOUNT, rotated, NOW)
    assert state != "single-stale-key" and state != "stale-key"
    assert state == "unfinished-rotation"
    assert "newest key 45 day(s) old" in detail

    # And once the retired key is revoked, there is nothing left to report.
    finished = rotation_verdict(ACCOUNT, [sa_key("key_new", 45)], NOW)
    assert finished[0] == "rotating"
    assert "45 day(s) old" in finished[1]


def test_the_key_count_produces_three_different_findings():
    single = rotation_verdict(ACCOUNT, [sa_key("key_a", 731)], NOW)
    assert single[0] == "single-stale-key"
    assert "it is the only one" in single[1]
    assert any("mint a second key first" in step
               for step in rotation_plan("proj_1", "ingest-worker", True))

    both_old = rotation_verdict(ACCOUNT, [sa_key("key_a", 402),
                                          sa_key("key_b", 500)], NOW)
    assert both_old[0] == "stale-key"
    assert "across 2 key(s)" in both_old[1]
    assert not any("mint a second key first" in step
                   for step in rotation_plan("proj_1", "ingest-worker", False))

    halfway = rotation_verdict(ACCOUNT, [sa_key("key_a", 12),
                                         sa_key("key_b", 588)], NOW)
    assert halfway[0] == "unfinished-rotation"
    assert "still live" in halfway[1]


def test_an_empty_or_unreachable_audit_log_is_never_corroboration():
    unreachable = corroboration([], "proj_1", audit_reachable=False)
    assert unreachable[0] == "audit-unavailable"
    assert "silence is not evidence" in unreachable[1]

    empty = corroboration([], "proj_1", audit_reachable=True)
    assert empty[0] == "audit-unavailable"
    assert "nothing is being recorded" in empty[1]


def test_the_audit_log_confirms_a_project_and_never_an_account():
    elsewhere = [{"type": "api_key.created", "project": {"id": "proj_other"}}]
    state, detail = corroboration(elsewhere, "proj_1", True, 180)
    assert state == "confirmed-at-project-level"
    assert "project-level fact" in detail
    assert "does not name" in detail or "not the service account" in detail

    here = [{"type": "api_key.created", "project": {"id": "proj_1"}},
            {"type": "api_key.created", "project": {"id": "proj_1"}}]
    state, detail = corroboration(here, "proj_1", True, 180)
    assert state == "creation-activity-in-window"
    assert "neither confirms nor clears" in detail


def test_a_personal_key_is_not_counted_towards_a_service_account():
    keys = [sa_key("key_a", 731),
            {"id": "key_user", "created_at": unix(2),
             "owner": {"type": "user", "user": {"email": "dev@example.test"}}},
            {"id": "key_odd", "created_at": unix(2), "owner": None}]
    grouped = group_by_account(keys)
    assert list(grouped) == ["svc_1"]
    assert len(grouped["svc_1"]) == 1
    # Counting the personal key here would turn a single-key account into a
    # two-key one and hide the fact that no overlap window has ever existed.
    assert rotation_verdict(ACCOUNT, grouped["svc_1"], NOW)[0] == "single-stale-key"
    assert service_account_id({"owner": {"type": "service_account"}}) is None
    assert service_account_id(None) is None
    assert group_by_account([]) == {}


def test_a_service_account_with_no_keys_and_one_too_new_to_judge():
    empty = rotation_verdict({"id": "svc_2", "name": "search-indexer",
                              "created_at": unix(300)}, [], NOW)
    assert empty[0] == "service-account-with-no-keys"
    assert "300 day(s) ago" in empty[1]
    fresh = rotation_verdict(ACCOUNT, [sa_key("key_a", 4)], NOW)
    assert fresh[0] == "too-new"
    unreadable = rotation_verdict(ACCOUNT, [{"id": "key_a", "created_at": None,
                                             "owner": None}], NOW)
    assert unreadable[0] == "too-new"


def test_ages_are_read_from_unix_seconds_only():
    assert age_days(unix(180), NOW) == 180
    assert age_days(None, NOW) is None
    assert age_days("", NOW) is None
    assert age_days(True, NOW) is None
    assert age_days("not a number", NOW) is None


def test_the_rotation_plan_revokes_last_and_names_the_missing_field():
    steps = rotation_plan("proj_prod", "ingest-worker", False)
    assert len(steps) == 3
    assert "returned exactly once" in steps[0]
    assert "last_used_at should stop advancing" in steps[1]
    assert steps[2].startswith("revoke the old key")
    assert "no expires_at" in steps[2]
''',
"test_js_file": "openai-key-rotation-clock.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, corroboration, groupByAccount, newestAndOldest, rotationPlan,
         rotationVerdict, serviceAccountId }
  from './openai-key-rotation-clock.mjs';

const NOW = new Date('2026-08-31T12:00:00Z');
const ACCOUNT = { id: 'svc_1', name: 'ingest-worker', created_at: 0 };
const unix = (daysAgo) => Math.floor(NOW.getTime() / 1000) - daysAgo * 86400;

const saKey = (id, daysAgo, account = 'svc_1') => ({
  id, created_at: unix(daysAgo),
  owner: { type: 'service_account',
           service_account: { id: account, name: 'ingest-worker' } },
});

test('the newest key is the clock and the oldest would lie', () => {
  const rotated = [saKey('key_new', 45), saKey('key_old', 731)];
  assert.deepEqual(newestAndOldest(rotated, NOW), [45, 731]);
  const [state, detail] = rotationVerdict(ACCOUNT, rotated, NOW);
  assert.ok(state !== 'single-stale-key' && state !== 'stale-key');
  assert.equal(state, 'unfinished-rotation');
  assert.match(detail, /newest key 45 day\\(s\\) old/);

  const finished = rotationVerdict(ACCOUNT, [saKey('key_new', 45)], NOW);
  assert.equal(finished[0], 'rotating');
});

test('the key count produces three different findings', () => {
  const single = rotationVerdict(ACCOUNT, [saKey('key_a', 731)], NOW);
  assert.equal(single[0], 'single-stale-key');
  assert.match(single[1], /it is the only one/);
  assert.ok(rotationPlan('proj_1', 'ingest-worker', true)
    .some((s) => s.includes('mint a second key first')));

  const bothOld = rotationVerdict(ACCOUNT, [saKey('key_a', 402), saKey('key_b', 500)], NOW);
  assert.equal(bothOld[0], 'stale-key');
  assert.match(bothOld[1], /across 2 key\\(s\\)/);
  assert.ok(!rotationPlan('proj_1', 'ingest-worker', false)
    .some((s) => s.includes('mint a second key first')));

  const halfway = rotationVerdict(ACCOUNT, [saKey('key_a', 12), saKey('key_b', 588)], NOW);
  assert.equal(halfway[0], 'unfinished-rotation');
  assert.match(halfway[1], /still live/);
});

test('an empty or unreachable audit log is never corroboration', () => {
  const unreachable = corroboration([], 'proj_1', false);
  assert.equal(unreachable[0], 'audit-unavailable');
  assert.match(unreachable[1], /silence is not evidence/);
  const empty = corroboration([], 'proj_1', true);
  assert.equal(empty[0], 'audit-unavailable');
  assert.match(empty[1], /nothing is being recorded/);
});

test('the audit log confirms a project and never an account', () => {
  const [state, detail] = corroboration(
    [{ type: 'api_key.created', project: { id: 'proj_other' } }], 'proj_1', true, 180);
  assert.equal(state, 'confirmed-at-project-level');
  assert.match(detail, /project-level fact/);
  assert.match(detail, /not the service account/);

  const [state2, detail2] = corroboration([
    { type: 'api_key.created', project: { id: 'proj_1' } },
    { type: 'api_key.created', project: { id: 'proj_1' } }], 'proj_1', true, 180);
  assert.equal(state2, 'creation-activity-in-window');
  assert.match(detail2, /neither confirms nor clears/);
});

test('a personal key is not counted towards a service account', () => {
  const grouped = groupByAccount([
    saKey('key_a', 731),
    { id: 'key_user', created_at: unix(2),
      owner: { type: 'user', user: { email: 'dev@example.test' } } },
    { id: 'key_odd', created_at: unix(2), owner: null },
  ]);
  assert.deepEqual(Object.keys(grouped), ['svc_1']);
  assert.equal(grouped.svc_1.length, 1);
  assert.equal(rotationVerdict(ACCOUNT, grouped.svc_1, NOW)[0], 'single-stale-key');
  assert.equal(serviceAccountId({ owner: { type: 'service_account' } }), null);
  assert.equal(serviceAccountId(null), null);
  assert.deepEqual(groupByAccount([]), {});
});

test('a service account with no keys and one too new to judge', () => {
  const empty = rotationVerdict(
    { id: 'svc_2', name: 'search-indexer', created_at: unix(300) }, [], NOW);
  assert.equal(empty[0], 'service-account-with-no-keys');
  assert.match(empty[1], /300 day\\(s\\) ago/);
  assert.equal(rotationVerdict(ACCOUNT, [saKey('key_a', 4)], NOW)[0], 'too-new');
  assert.equal(rotationVerdict(
    ACCOUNT, [{ id: 'key_a', created_at: null, owner: null }], NOW)[0], 'too-new');
});

test('ages are read from unix seconds only', () => {
  assert.equal(ageDays(unix(180), NOW), 180);
  assert.equal(ageDays(null, NOW), null);
  assert.equal(ageDays('', NOW), null);
  assert.equal(ageDays(true, NOW), null);
  assert.equal(ageDays('not a number', NOW), null);
});

test('the rotation plan revokes last and names the missing field', () => {
  const steps = rotationPlan('proj_prod', 'ingest-worker', false);
  assert.equal(steps.length, 3);
  assert.match(steps[0], /returned exactly once/);
  assert.match(steps[1], /last_used_at should stop advancing/);
  assert.ok(steps[2].startsWith('revoke the old key'));
  assert.match(steps[2], /no expires_at/);
});
''',
"faq": [
 ("How is an unrotated key different from an unused one?",
  "They are opposite readings of the same roster. The idleness note looks for credentials with no traffic behind them, and its finding is a key nothing depends on. This one looks at creation dates, and its subject is the key everything depends on: used constantly, owned by a service account exactly as the guidance says, and minted two years ago. On every usage measure it is the best-behaved credential in the organization, which is precisely why no traffic-based sweep will ever mention it."),
 ("Why does having only one key make it worse rather than simpler?",
  "Because rotation is only safe when two credentials can be valid at once. The safe sequence is mint the second, deploy it, watch the first go quiet, then revoke. A service account with exactly one key has never been in that shape, so any rotation is a synchronised cutover across every deployment holding the value, with no rollback if something is missed. That is a genuinely risky change, and it is the real reason the rotation keeps moving to next quarter. The script tells single-key accounts to mint the second key first and stop there."),
 ("Can the audit log tell me a specific service account was never rotated?",
  "No, and the script refuses to imply otherwise. The api_key.created event carries id, data.scopes, effective_at, project.id and actor. It does not carry the service account the key belongs to. So the strongest sound conclusion from an absence is that nothing was minted in that project during the window, which is reported as a project-level fact. The claim about any single account rests on created_at in the key list, which is the field that actually knows."),
 ("The audit log came back empty. Is that good news?",
  "It is no news. Audit logging is gated to organizations that have it enabled, so an empty response can mean nothing was minted or can mean nothing is being recorded, and those are not the same. The script reports audit-unavailable in both cases and explicitly says the key ages stand on created_at alone. It also treats a 4xx from that endpoint as non-fatal, because dying there would throw away the rotation ages it already has in hand."),
 ("Is there any field that would make this check unnecessary?",
  "An expiry, and one endpoint has it. Admin API keys carry an optional expires_at, so an admin key can be made to lapse on a schedule of its own. Project API keys have no such field at all, and neither provider records anything like a rotated_at. So for the credentials that actually run production, the schedule has to live outside the platform, and a scheduled run of this script is the cheapest version of that until an expiry exists to set."),
],
"related": [REL_NEVER_USED, REL_LIFECYCLE, REL_OWNER_GONE],
"citations": [CITE_PROJECTS, CITE_PROJECT_KEYS, CITE_AUDIT_LOGS,
              CITE_ADMIN_APIS],
},
{
"slug": "unreviewed-key-lifecycle-in-audit-log",
"title": "Nobody has ever read the key lifecycle audit log",
"description": "Both providers record every key and member lifecycle event and wait to be asked. Resolve each actor against the current roster and the unreviewed ones surface.",
"h1": "Nobody has ever read the key lifecycle audit log",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai audit logs api_key.created",
             "anthropic compliance activities feed",
             "openai audit log actor session ip_address",
             "review llm key lifecycle events",
             "openai login.failed audit alert"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY (sk-admin-) or ANTHROPIC_ADMIN_KEY (sk-ant-admin) with the read:compliance_activities scope, or both. Both feeds are read-only and pull-only.",
"lead": "The control exists. It has existed since the organization was created, it has recorded every key minted and every key deleted and every member added since then, and it is complete, accurate and correctly timestamped. It has also never been read by anybody, because reading it requires standing up a job, and a log that is silent when everything is healthy gives nobody a reason to build one. There is an entry in there from a Tuesday in March: a key created at 02:14 UTC by an email address that is no longer on the roster. It has been sitting there for five months.",
"short_answer": """<p>On OpenAI, with an <strong>organization admin key</strong>: <code>GET /v1/organization/audit_logs?effective_at[gte]={now-7d}&amp;limit=100</code> with <code>event_types[]</code> repeated for <code>api_key.created</code>, <code>api_key.updated</code>, <code>api_key.deleted</code>, <code>service_account.created</code>, <code>service_account.deleted</code> and <code>login.failed</code>. Each entry carries <code>id</code>, <code>type</code>, <code>effective_at</code>, <code>project</code> and <code>actor</code>.</p>
<p>On Anthropic the same events live in a different API: <code>GET /v1/compliance/activities?limit=100</code>, which needs the <code>read:compliance_activities</code> scope and returns <code>Activity</code> records with <code>type</code>, <code>created_at</code> and an <code>actor</code> block of <code>email_address</code>, <code>user_id</code>, <code>ip_address</code> and <code>user_agent</code>. Because it is documented under Compliance rather than under Admin, integrations that pull usage and keys almost never pull it.</p>
<p>The join is what turns a feed into a finding: <strong>resolve every actor against the current roster</strong> from <code>GET /v1/organization/users</code> or <code>GET /v1/organizations/users</code>. An actor who is no longer on the roster performed a credential action that nobody has looked at since. On top of that, flag creation events outside business hours, creation events from a country you do not operate in, and bursts of <code>login.failed</code>.</p>
<p>And read an empty feed correctly. <strong>Audit logging is gated to organizations that have it enabled</strong>, so nothing coming back is not the same as nothing happening, and the script says so instead of reporting a clean result.</p>""",
"problem": """<p>This is the classic control that exists on paper. Both providers capture exactly the events you would want to be woken up for: credential creation and deletion, service-account lifecycle, invite and role changes, failed logins, SSO and SCIM changes. Both store them faithfully. Neither pushes them anywhere. There is no webhook, no email, no default alert, and no banner in either console that says three keys were minted this week.</p>
<p>So the feed is pull-only, which means somebody has to build the puller, which means it needs a scheduler, a cursor, a destination and an owner. All of that is work with no visible payoff on the day it ships, because a healthy log is empty of interesting rows. The result is that the log accumulates for years and the first time anyone reads it is during an incident, when the question is not "what happened" but "what happened eight months ago and who did it".</p>
<p>The raw feed is also not readable by a person in the state the API returns it. Actors are ids and email addresses with no indication of whether those people still work here. Event payloads hang off a key named after the event type. Timestamps are epochs. Some entries are attributed to a project that had nothing to do with them. Turning that into something a human can act on is exactly the small amount of processing that never gets written.</p>""",
"why": """<p><strong>This is the only note in the batch whose subject is events rather than objects.</strong> The other three read the current state of the roster: what a key's usage looks like now, who owns it now, how old it is now. None of them can tell you that a key existed for six weeks and was deleted, or that somebody minted one at 2am from a country you do not operate in, because the object those facts describe is gone. The feed is the only surface where a credential that no longer exists left a mark.</p>
<p><strong>Resolving actors against the roster is the whole join.</strong> An email in an audit entry means very little on its own. The same email checked against <code>GET /v1/organization/users</code> means one of three things: a current member, in which case the event is reviewable; somebody no longer on the roster, which is an action taken by a person whose access has since ended and which nobody has read; or no email at all, because the actor was an API key rather than a session, which is unattributable to a human and worth separating rather than dropping.</p>
<p><strong>An empty feed is the single most misreadable result here.</strong> Audit logging is gated to organizations that have it enabled. A script that treats an empty response as "no findings" converts a missing control into a passing check, which is worse than not running the check at all. This one reports <code>feed-unavailable</code> and refuses to grade anything when the feed produces nothing.</p>
<p><strong>The two providers do not carry the same evidence, so the same rules cannot be applied to both.</strong> OpenAI's <em>session</em> actor is forensically rich: <code>actor.session.user.email</code>, <code>ip_address</code>, <code>user_agent</code>, the <code>ja3</code> and <code>ja4</code> TLS fingerprints, and <code>ip_address_details</code> with country, city, region and ASN. Anthropic's <code>Activity</code> actor carries an email address, a user id, an IP and a user agent, and no geography breakdown. The country rule therefore applies to OpenAI events only, and the script says which rules it could and could not run on which feed rather than reporting a uniform verdict it did not earn.</p>
<p><strong>Two attribution quirks will mislead you if nobody names them.</strong> Admin actions taken with an OpenAI Admin API key are attributed to the default project, so <code>project</code> on those entries tells you nothing about where the action landed. And the audit-log endpoint is the one administration path that documents its own <code>429</code> with a <code>Retry-After</code>, so a first-time backfill has to back off rather than page as fast as it can; on Anthropic every <code>/v1/compliance/*</code> endpoint shares a single 600 requests per minute budget for the whole organization.</p>""",
"steps": [
 {"h": "Get a credential that can read the feed, and check the scope",
  "body": """<p>OpenAI: an <code>sk-admin-</code> key with read scopes. Anthropic: an Admin key or a Compliance Access Key carrying <code>read:compliance_activities</code>, which is a scope you have to ask for rather than one an Admin key has by default. An Admin key reaches <code>/v1/compliance/activities</code> and no other compliance endpoint.</p>"""},
 {"h": "Pull the lifecycle events, not the whole log",
  "body": """<p>Repeat <code>event_types[]</code> for the credential and member events you actually want to be paged on. The full log is large, and a first pull that asks for everything is both slow and impossible to read. Paginate on <code>after</code> and back off on a <code>429</code>: this endpoint declares one with a <code>Retry-After</code>.</p>"""},
 {"h": "Build the roster once and resolve every actor against it",
  "body": """<p><code>GET /v1/organization/users?limit=100</code> or <code>GET /v1/organizations/users?limit=1000</code>. Lowercase the emails into a set. Then every event resolves to on-roster, off-roster or unattributable, and only the first of those is a row a reviewer can close.</p>"""},
 {"h": "Apply only the rules the feed can actually support",
  "body": """<p>Out-of-hours creation applies to both providers, because both carry a timestamp. The country rule applies to OpenAI session actors only, because <code>ip_address_details</code> has no counterpart on the Anthropic activity record. Say which rules ran on which feed in the output instead of implying a uniform sweep.</p>"""},
 {"h": "Print the watermark, because the repair is a scheduled job",
  "body": """<p>The finding is not really any single event; it is that nobody is reading. So the last thing the script prints is the newest <code>effective_at</code> it saw, ready to be stored as <code>effective_at[gte]</code> for the next run. That cursor, a schedule and an alerting destination are the actual fix, and the script is the prototype of it.</p>"""},
],
"verify": """<p>Run it once for the backlog, then daily from the stored watermark. A healthy day is a run with events, zero findings, and a watermark that advanced.</p>
<pre><code class="language-bash">python3 llm_key_lifecycle_review.py --days 7
# openai: 24 event(s), roster of 31 member(s); country and session rules available
# anthropic: 9 activity(s), roster of 12 member(s); no geography on this feed
# off-roster-actor    api_key.created   2026-03-17T02:14:08Z  ada@example.test  198.51.100.24  NL
#   reason: the actor is not on the current roster
#   reason: created outside business hours (02:00 UTC)
#   reason: ip_address_details.country NL is outside the operating geographies
# unattributable      api_key.deleted   2026-08-02T11:40:55Z  (api_key actor)   -
#   reason: an api_key actor carries no user email, so no person can be attributed
# 2 finding(s) of 33 event(s)
# watermark: store effective_at[gte]=1756636800 for the next run</code></pre>""",
"code_intro": "Two feeds normalised into one shape, then one grader. <code>normalise_openai</code> has to walk two different actor shapes, because a session actor and an api_key actor keep their email in different places and one of them has no email at all. <code>normalise_anthropic</code> is simpler and deliberately leaves <code>country</code> as <code>None</code>, which is how the grader knows not to run the geography rule on it rather than silently passing every Anthropic event. <code>resolve_actor</code> is the join. <code>grade</code> returns a state and every reason, so an event that is off-roster <em>and</em> out of hours <em>and</em> from an unexpected country prints three lines. <code>feed_state</code> is the honest one, and <code>watermark</code> is the repair.",
"py_file": "llm_key_lifecycle_review.py",
"py": '''"""Read the key and member lifecycle events nobody has ever read.

Read only. GET requests only, against the OpenAI Audit Logs API and the
Anthropic Compliance activity feed. Nothing is created, changed or removed.

Both feeds are pull-only: there is no webhook, no email and no default alert on
either provider, which is why the control exists everywhere and has fired
nowhere. The finding is not any single event; it is that nobody is reading. So
the last thing this prints is a watermark to store for the next run.

Two honest limits are enforced in the code rather than mentioned in a comment.
An empty feed is reported as unavailable and never as clean, because audit
logging is gated to organizations that have it enabled. And the geography rule
runs on OpenAI session actors only: the Anthropic activity record carries an
email, a user id, an IP and a user agent, and no country breakdown to test.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm_key_lifecycle_review")

OPENAI = "https://api.openai.com/v1"
ANTHROPIC = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

OPENAI_EVENTS = ("api_key.created", "api_key.updated", "api_key.deleted",
                 "service_account.created", "service_account.deleted",
                 "login.failed")

OFF_ROSTER = "off-roster-actor"
UNATTRIBUTABLE = "unattributable"
UNEXPECTED_COUNTRY = "unexpected-country"
OUT_OF_HOURS = "out-of-hours"
REVIEWED = "reviewed"
FINDINGS = (OFF_ROSTER, UNATTRIBUTABLE, UNEXPECTED_COUNTRY, OUT_OF_HOURS)

FEED_OK = "feed-readable"
FEED_UNAVAILABLE = "feed-unavailable"

# Highest first. An event can trip several rules at once and every reason is
# printed; the state is the one that decides how loudly it is printed.
SEVERITY = (OFF_ROSTER, UNEXPECTED_COUNTRY, UNATTRIBUTABLE, OUT_OF_HOURS)


def parse_when(value):
    """Epoch seconds from a unix integer or an RFC 3339 string. Pure.

    OpenAI dates effective_at in unix seconds; the Anthropic activity record
    uses an RFC 3339 string. Normalising here is what lets one grader read both
    feeds without either one being special-cased downstream.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    try:
        when = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    return int(when.timestamp())


def iso(epoch):
    """A readable UTC timestamp. Pure."""
    if epoch is None:
        return "(no timestamp)"
    return dt.datetime.fromtimestamp(int(epoch), dt.timezone.utc) \\
             .strftime("%Y-%m-%dT%H:%M:%SZ")


def normalise_openai(entry):
    """One audit-log entry in the common shape. Pure.

    The actor arrives in two shapes and they keep the email in different
    places. A session actor is the forensically rich one and carries the
    address, the IP and ip_address_details. An api_key actor carries a tracking
    id and either a user email or a service account id, and frequently no email
    at all, which is a distinct outcome rather than a missing value.
    """
    row = entry or {}
    actor = row.get("actor") if isinstance(row.get("actor"), dict) else {}
    kind = str(actor.get("type") or "").strip().lower()
    email, ip, country = None, None, None
    if kind == "session":
        session = actor.get("session") if isinstance(actor.get("session"), dict) else {}
        user = session.get("user") if isinstance(session.get("user"), dict) else {}
        email = user.get("email")
        ip = session.get("ip_address")
        details = (session.get("ip_address_details")
                   if isinstance(session.get("ip_address_details"), dict) else {})
        country = details.get("country")
    elif kind == "api_key":
        api_key = actor.get("api_key") if isinstance(actor.get("api_key"), dict) else {}
        user = api_key.get("user") if isinstance(api_key.get("user"), dict) else {}
        email = user.get("email")
    project = row.get("project") if isinstance(row.get("project"), dict) else {}
    return {"source": "openai", "type": str(row.get("type") or "(untyped)"),
            "when": parse_when(row.get("effective_at")),
            "actor_kind": kind or "unknown",
            "actor_email": str(email).strip().lower() if email else None,
            "actor_ip": ip, "country": country,
            "container": project.get("name") or project.get("id")}


def normalise_anthropic(activity):
    """One compliance activity in the common shape. Pure.

    country stays None on purpose. The activity record carries email_address,
    user_id, ip_address and user_agent and no geography breakdown, and leaving
    the field absent is how the grader knows to skip the country rule here
    rather than silently passing every Anthropic event.
    """
    row = activity or {}
    actor = row.get("actor") if isinstance(row.get("actor"), dict) else {}
    email = actor.get("email_address")
    return {"source": "anthropic", "type": str(row.get("type") or "(untyped)"),
            "when": parse_when(row.get("created_at")),
            "actor_kind": "user" if email else "unknown",
            "actor_email": str(email).strip().lower() if email else None,
            "actor_ip": actor.get("ip_address"), "country": None,
            "container": row.get("organization_id")}


def resolve_actor(event, roster):
    """on-roster, off-roster or unattributable. Pure.

    The join that turns a feed into a finding. An email checked against the
    current roster is the difference between an event a reviewer can close and
    an action taken by somebody whose access has since ended.
    """
    email = (event or {}).get("actor_email")
    if not email:
        return "unattributable"
    return "on-roster" if str(email).strip().lower() in (roster or set()) \\
        else "off-roster"


def hour_of(event):
    """The UTC hour of an event, or None. Pure."""
    when = (event or {}).get("when")
    if when is None:
        return None
    return dt.datetime.fromtimestamp(int(when), dt.timezone.utc).hour


def grade(event, roster, business_hours=(7, 19), operating_countries=None):
    """Classify one normalised event. Pure. Returns (state, reasons).

    Every rule that fires contributes a reason, because an event can be
    off-roster and out of hours and from an unexpected country at once and a
    reviewer wants all three. The state is the most severe reason present and
    decides how loudly the row is printed.
    """
    reasons = []
    resolution = resolve_actor(event, roster)
    if resolution == "off-roster":
        reasons.append((OFF_ROSTER, "the actor is not on the current roster"))
    elif resolution == "unattributable":
        reasons.append((UNATTRIBUTABLE,
                        "an %s actor carries no user email, so no person can "
                        "be attributed" % ((event or {}).get("actor_kind")
                                           or "unknown")))

    country = (event or {}).get("country")
    if operating_countries and country:
        if str(country).strip().upper() not in {c.upper() for c in operating_countries}:
            reasons.append((UNEXPECTED_COUNTRY,
                            "ip_address_details.country %s is outside the "
                            "operating geographies" % country))

    hour = hour_of(event)
    start, end = business_hours
    creation = str((event or {}).get("type") or "").endswith((".created", ".deleted"))
    if creation and hour is not None and not (start <= hour < end):
        reasons.append((OUT_OF_HOURS,
                        "created outside business hours (%02d:00 UTC)" % hour))

    if not reasons:
        return (REVIEWED, [])
    present = {state for state, _ in reasons}
    state = next(s for s in SEVERITY if s in present)
    return (state, [text for _, text in reasons])


def feed_state(events, reachable):
    """Whether the feed said anything at all. Pure. (state, detail).

    An empty feed is the most misreadable result on this surface. Audit logging
    is gated to organizations that have it enabled, so treating silence as "no
    findings" turns a missing control into a passing check.
    """
    if not reachable:
        return (FEED_UNAVAILABLE,
                "the feed could not be read, so nothing below is a review of "
                "anything")
    if not (events or []):
        return (FEED_UNAVAILABLE,
                "the feed returned no events at all. Audit logging is gated to "
                "organizations that have it enabled, so this is not a clean "
                "result: it is an unknown one.")
    return (FEED_OK, "%d event(s) read" % len(events))


def failed_login_bursts(events, window_seconds=600, threshold=5):
    """Clusters of login.failed inside one window. Pure.

    A single failed login is a typo. Five in ten minutes is the only pattern in
    this feed that is worth an alert on its own rather than a weekly read.
    """
    rows = sorted([e for e in (events or [])
                   if str((e or {}).get("type") or "") == "login.failed"
                   and (e or {}).get("when") is not None],
                  key=lambda e: e["when"])
    bursts = []
    for i, first in enumerate(rows):
        window = [e for e in rows[i:]
                  if e["when"] - first["when"] <= window_seconds]
        if len(window) >= threshold:
            bursts.append((first["when"], len(window),
                           first.get("actor_email") or "(no email)"))
            break
    return bursts


def watermark(events):
    """The newest timestamp seen, for the next run's cursor. Pure."""
    stamps = [e["when"] for e in (events or []) if (e or {}).get("when") is not None]
    return max(stamps) if stamps else None


def project_caveat(event):
    """Whether this entry's project field means anything. Pure.

    Admin actions taken with an Admin API key are attributed to the default
    project, so the project on those entries says nothing about where the
    action landed.
    """
    if (event or {}).get("source") != "openai":
        return None
    if (event or {}).get("actor_kind") == "api_key":
        return ("project is not meaningful here: admin actions taken with an "
                "Admin API key are attributed to the default project")
    return None


def get(session, url, params, who):
    r = session.get(url, params=params, timeout=60)
    if r.status_code == 429:
        raise SystemExit("429 from %s: this feed declares its own rate limit "
                         "with Retry-After. Back off and resume from the "
                         "stored watermark." % who)
    if r.status_code in (401, 403):
        raise SystemExit("%d from %s: the feed needs an administration "
                         "credential, and on Anthropic the "
                         "read:compliance_activities scope" % (r.status_code, who))
    r.raise_for_status()
    return r.json()


def collect(session, url, params, who, cursor="after", limit_pages=20):
    rows = []
    params = dict(params)
    for _ in range(limit_pages):
        page = get(session, url, params, who)
        rows.extend(page.get("data") or [])
        if not page.get("has_more") or not page.get("last_id"):
            return rows
        params[cursor] = page["last_id"]
    return rows


def report(name, events, roster, args, geography):
    state, detail = feed_state(events, True)
    log.info("%s: %s (%s), roster of %d member(s); %s", name, state, detail,
             len(roster), "country and session rules available" if geography
             else "no geography on this feed")
    if state == FEED_UNAVAILABLE:
        return 0

    countries = [c.strip() for c in args.countries.split(",") if c.strip()]
    findings = 0
    for event in sorted(events, key=lambda e: e.get("when") or 0):
        verdict, reasons = grade(event, roster,
                                 (args.hours_from, args.hours_to),
                                 countries if geography else None)
        if verdict == REVIEWED:
            continue
        findings += 1
        log.warning("%-19s %-22s %s  %-18s %-15s %s", verdict, event["type"],
                    iso(event.get("when")),
                    event.get("actor_email") or "(%s actor)" % event.get("actor_kind"),
                    event.get("actor_ip") or "-", event.get("country") or "")
        for reason in reasons:
            log.warning("  reason: %s", reason)
        caveat = project_caveat(event)
        if caveat:
            log.info("  note: %s", caveat)

    for when, count, who in failed_login_bursts(events):
        findings += 1
        log.warning("login-failed-burst   %d failure(s) within 10 minutes from "
                    "%s, starting %s", count, who, iso(when))

    mark = watermark(events)
    if mark is not None:
        log.info("watermark: store the cursor %d (%s) for the next %s run",
                 mark, iso(mark), name)
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="days of lifecycle events to read (default 7)")
    ap.add_argument("--hours-from", type=int, default=7,
                    help="first business hour, UTC")
    ap.add_argument("--hours-to", type=int, default=19,
                    help="first non-business hour, UTC")
    ap.add_argument("--countries", default="US,GB,DE,IE",
                    help="comma separated operating geographies for the "
                         "country rule, which runs on OpenAI events only")
    args = ap.parse_args()

    openai_key = os.environ.get("OPENAI_ADMIN_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not openai_key and not anthropic_key:
        log.error("set OPENAI_ADMIN_KEY or ANTHROPIC_ADMIN_KEY, or both; the "
                  "Anthropic credential also needs the "
                  "read:compliance_activities scope")
        return 2

    since = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=args.days)).timestamp())
    findings = 0

    if openai_key:
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + openai_key})
        roster = {str(u.get("email") or "").strip().lower()
                  for u in collect(s, OPENAI + "/organization/users",
                                   {"limit": 100}, "OpenAI")
                  if u.get("email")}
        raw = collect(s, OPENAI + "/organization/audit_logs",
                      {"limit": 100, "effective_at[gte]": since,
                       "event_types[]": list(OPENAI_EVENTS)}, "OpenAI")
        findings += report("openai", [normalise_openai(e) for e in raw],
                           roster, args, geography=True)

    if anthropic_key:
        s = requests.Session()
        s.headers.update({"x-api-key": anthropic_key,
                          "anthropic-version": ANTHROPIC_VERSION})
        roster = {str(u.get("email") or "").strip().lower()
                  for u in collect(s, ANTHROPIC + "/organizations/users",
                                   {"limit": 1000}, "Anthropic",
                                   cursor="after_id")
                  if u.get("email")}
        raw = collect(s, ANTHROPIC + "/compliance/activities", {"limit": 100},
                      "Anthropic")
        findings += report("anthropic",
                           [normalise_anthropic(a) for a in raw
                            if (parse_when((a or {}).get("created_at")) or 0) >= since],
                           roster, args, geography=False)

    log.info("%d finding(s)", findings)
    log.info("the repair is a schedule, not a run: poll from the stored "
             "watermark and route these events to somewhere a person looks")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "llm-key-lifecycle-review.mjs",
"js": '''/**
 * Read the key and member lifecycle events nobody has ever read.
 *
 * Read only. GET requests only, against the OpenAI Audit Logs API and the
 * Anthropic Compliance activity feed.
 *
 * Both feeds are pull-only, which is why the control exists everywhere and has
 * fired nowhere. The finding is not any single event; it is that nobody is
 * reading, so the last thing printed is a watermark for the next run.
 *
 * An empty feed is reported as unavailable and never as clean, and the
 * geography rule runs on OpenAI session actors only: the Anthropic activity
 * record has no country breakdown to test.
 */
const OPENAI = 'https://api.openai.com/v1';
const ANTHROPIC = 'https://api.anthropic.com/v1';
const ANTHROPIC_VERSION = '2023-06-01';

const OPENAI_EVENTS = ['api_key.created', 'api_key.updated', 'api_key.deleted',
                       'service_account.created', 'service_account.deleted',
                       'login.failed'];

export const OFF_ROSTER = 'off-roster-actor';
export const UNATTRIBUTABLE = 'unattributable';
export const UNEXPECTED_COUNTRY = 'unexpected-country';
export const OUT_OF_HOURS = 'out-of-hours';
export const REVIEWED = 'reviewed';

export const FEED_OK = 'feed-readable';
export const FEED_UNAVAILABLE = 'feed-unavailable';

const SEVERITY = [OFF_ROSTER, UNEXPECTED_COUNTRY, UNATTRIBUTABLE, OUT_OF_HOURS];

/** Epoch seconds from a unix integer or an RFC 3339 string. Pure. */
export function parseWhen(value) {
  if (value === null || value === undefined || value === '' ||
      typeof value === 'boolean') return null;
  if (typeof value === 'number') return Math.trunc(value);
  const text = String(value).trim();
  if (/^\\d+$/.test(text)) return Number(text);
  const when = new Date(text);
  if (Number.isNaN(when.getTime())) return null;
  return Math.floor(when.getTime() / 1000);
}

/** A readable UTC timestamp. Pure. */
export function iso(epoch) {
  if (epoch === null || epoch === undefined) return '(no timestamp)';
  return `${new Date(Number(epoch) * 1000).toISOString().slice(0, 19)}Z`;
}

/** One audit-log entry in the common shape. Pure. Two actor shapes. */
export function normaliseOpenai(entry) {
  const row = entry ?? {};
  const actor = (row.actor && typeof row.actor === 'object') ? row.actor : {};
  const kind = String(actor.type ?? '').trim().toLowerCase();
  let email = null;
  let ip = null;
  let country = null;
  if (kind === 'session') {
    const session = (actor.session && typeof actor.session === 'object') ? actor.session : {};
    const user = (session.user && typeof session.user === 'object') ? session.user : {};
    email = user.email ?? null;
    ip = session.ip_address ?? null;
    const details = (session.ip_address_details &&
                     typeof session.ip_address_details === 'object')
      ? session.ip_address_details : {};
    country = details.country ?? null;
  } else if (kind === 'api_key') {
    const apiKey = (actor.api_key && typeof actor.api_key === 'object') ? actor.api_key : {};
    const user = (apiKey.user && typeof apiKey.user === 'object') ? apiKey.user : {};
    email = user.email ?? null;
  }
  const project = (row.project && typeof row.project === 'object') ? row.project : {};
  return { source: 'openai', type: String(row.type ?? '(untyped)'),
           when: parseWhen(row.effective_at), actorKind: kind || 'unknown',
           actorEmail: email ? String(email).trim().toLowerCase() : null,
           actorIp: ip, country,
           container: project.name ?? project.id ?? null };
}

/** One compliance activity in the common shape. Pure. country stays null. */
export function normaliseAnthropic(activity) {
  const row = activity ?? {};
  const actor = (row.actor && typeof row.actor === 'object') ? row.actor : {};
  const email = actor.email_address ?? null;
  return { source: 'anthropic', type: String(row.type ?? '(untyped)'),
           when: parseWhen(row.created_at),
           actorKind: email ? 'user' : 'unknown',
           actorEmail: email ? String(email).trim().toLowerCase() : null,
           actorIp: actor.ip_address ?? null, country: null,
           container: row.organization_id ?? null };
}

/** on-roster, off-roster or unattributable. Pure. */
export function resolveActor(event, roster) {
  const email = (event ?? {}).actorEmail;
  if (!email) return 'unattributable';
  return (roster ?? new Set()).has(String(email).trim().toLowerCase())
    ? 'on-roster' : 'off-roster';
}

/** The UTC hour of an event, or null. Pure. */
export function hourOf(event) {
  const when = (event ?? {}).when;
  if (when === null || when === undefined) return null;
  return new Date(Number(when) * 1000).getUTCHours();
}

/** Classify one normalised event. Pure. Returns [state, reasons]. */
export function grade(event, roster, businessHours = [7, 19], operatingCountries = null) {
  const reasons = [];
  const resolution = resolveActor(event, roster);
  if (resolution === 'off-roster') {
    reasons.push([OFF_ROSTER, 'the actor is not on the current roster']);
  } else if (resolution === 'unattributable') {
    reasons.push([UNATTRIBUTABLE,
      `an ${(event ?? {}).actorKind ?? 'unknown'} actor carries no user ` +
      'email, so no person can be attributed']);
  }

  const country = (event ?? {}).country;
  if (operatingCountries && operatingCountries.length && country) {
    const allowed = new Set(operatingCountries.map((c) => String(c).toUpperCase()));
    if (!allowed.has(String(country).trim().toUpperCase())) {
      reasons.push([UNEXPECTED_COUNTRY,
        `ip_address_details.country ${country} is outside the operating geographies`]);
    }
  }

  const hour = hourOf(event);
  const [start, end] = businessHours;
  const type = String((event ?? {}).type ?? '');
  const creation = type.endsWith('.created') || type.endsWith('.deleted');
  if (creation && hour !== null && !(hour >= start && hour < end)) {
    reasons.push([OUT_OF_HOURS,
      `created outside business hours (${String(hour).padStart(2, '0')}:00 UTC)`]);
  }

  if (!reasons.length) return [REVIEWED, []];
  const present = new Set(reasons.map(([state]) => state));
  const state = SEVERITY.find((s) => present.has(s));
  return [state, reasons.map(([, text]) => text)];
}

/** Whether the feed said anything at all. Pure. [state, detail]. */
export function feedState(events, reachable) {
  if (!reachable) {
    return [FEED_UNAVAILABLE,
      'the feed could not be read, so nothing below is a review of anything'];
  }
  if (!(events ?? []).length) {
    return [FEED_UNAVAILABLE,
      'the feed returned no events at all. Audit logging is gated to ' +
      'organizations that have it enabled, so this is not a clean result: ' +
      'it is an unknown one.'];
  }
  return [FEED_OK, `${events.length} event(s) read`];
}

/** Clusters of login.failed inside one window. Pure. */
export function failedLoginBursts(events, windowSeconds = 600, threshold = 5) {
  const rows = (events ?? [])
    .filter((e) => String(e?.type ?? '') === 'login.failed' && e?.when !== null &&
                   e?.when !== undefined)
    .sort((a, b) => a.when - b.when);
  for (let i = 0; i < rows.length; i += 1) {
    const window = rows.slice(i).filter((e) => e.when - rows[i].when <= windowSeconds);
    if (window.length >= threshold) {
      return [[rows[i].when, window.length, rows[i].actorEmail ?? '(no email)']];
    }
  }
  return [];
}

/** The newest timestamp seen, for the next run's cursor. Pure. */
export function watermark(events) {
  const stamps = (events ?? [])
    .map((e) => e?.when)
    .filter((w) => w !== null && w !== undefined);
  return stamps.length ? Math.max(...stamps) : null;
}

/** Whether this entry's project field means anything. Pure. */
export function projectCaveat(event) {
  if ((event ?? {}).source !== 'openai') return null;
  if ((event ?? {}).actorKind === 'api_key') {
    return 'project is not meaningful here: admin actions taken with an ' +
           'Admin API key are attributed to the default project';
  }
  return null;
}

async function getJson(headers, url, who) {
  const res = await fetch(url, { headers });
  if (res.status === 429) {
    throw new Error(`429 from ${who}: this feed declares its own rate limit ` +
                    'with Retry-After. Back off and resume from the stored watermark.');
  }
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from ${who}: the feed needs an ` +
                    'administration credential, and on Anthropic the ' +
                    'read:compliance_activities scope');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function collect(headers, base, path, params, who, cursor = 'after') {
  const rows = [];
  let after = null;
  for (let page = 0; page < 20; page += 1) {
    const url = new URL(base + path);
    for (const [k, v] of params) url.searchParams.append(k, String(v));
    if (after) url.searchParams.set(cursor, after);
    const body = await getJson(headers, url, who);
    rows.push(...(body.data ?? []));
    if (!body.has_more || !body.last_id) return rows;
    after = body.last_id;
  }
  return rows;
}

function report(name, events, roster, options, geography) {
  const [state, detail] = feedState(events, true);
  console.log(`${name}: ${state} (${detail}), roster of ${roster.size} member(s); ` +
              `${geography ? 'country and session rules available'
                           : 'no geography on this feed'}`);
  if (state === FEED_UNAVAILABLE) return 0;

  let findings = 0;
  for (const event of [...events].sort((a, b) => (a.when ?? 0) - (b.when ?? 0))) {
    const [verdict, reasons] = grade(event, roster, options.businessHours,
                                     geography ? options.countries : null);
    if (verdict === REVIEWED) continue;
    findings += 1;
    console.warn(`${verdict.padEnd(19)} ${event.type.padEnd(22)} ` +
                 `${iso(event.when)}  ` +
                 `${(event.actorEmail ?? `(${event.actorKind} actor)`).padEnd(18)} ` +
                 `${(event.actorIp ?? '-').padEnd(15)} ${event.country ?? ''}`);
    for (const reason of reasons) console.warn(`  reason: ${reason}`);
    const caveat = projectCaveat(event);
    if (caveat) console.log(`  note: ${caveat}`);
  }

  for (const [when, count, who] of failedLoginBursts(events)) {
    findings += 1;
    console.warn(`login-failed-burst   ${count} failure(s) within 10 minutes ` +
                 `from ${who}, starting ${iso(when)}`);
  }

  const mark = watermark(events);
  if (mark !== null) {
    console.log(`watermark: store the cursor ${mark} (${iso(mark)}) for the ` +
                `next ${name} run`);
  }
  return findings;
}

async function main() {
  const openaiKey = process.env.OPENAI_ADMIN_KEY;
  const anthropicKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!openaiKey && !anthropicKey) {
    console.error('set OPENAI_ADMIN_KEY or ANTHROPIC_ADMIN_KEY, or both; the ' +
                  'Anthropic credential also needs the ' +
                  'read:compliance_activities scope');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 7);
  const options = {
    businessHours: [Number(process.env.HOURS_FROM ?? 7),
                    Number(process.env.HOURS_TO ?? 19)],
    countries: String(process.env.COUNTRIES ?? 'US,GB,DE,IE')
      .split(',').map((c) => c.trim()).filter(Boolean),
  };
  const since = Math.floor(Date.now() / 1000) - days * 86400;
  let findings = 0;

  if (openaiKey) {
    const headers = { Authorization: `Bearer ${openaiKey}` };
    const users = await collect(headers, OPENAI, '/organization/users',
                                [['limit', 100]], 'OpenAI');
    const roster = new Set(users.filter((u) => u.email)
      .map((u) => String(u.email).trim().toLowerCase()));
    const raw = await collect(headers, OPENAI, '/organization/audit_logs',
      [['limit', 100], ['effective_at[gte]', since],
       ...OPENAI_EVENTS.map((t) => ['event_types[]', t])], 'OpenAI');
    findings += report('openai', raw.map(normaliseOpenai), roster, options, true);
  }

  if (anthropicKey) {
    const headers = { 'x-api-key': anthropicKey, 'anthropic-version': ANTHROPIC_VERSION };
    const users = await collect(headers, ANTHROPIC, '/organizations/users',
                                [['limit', 1000]], 'Anthropic', 'after_id');
    const roster = new Set(users.filter((u) => u.email)
      .map((u) => String(u.email).trim().toLowerCase()));
    const raw = await collect(headers, ANTHROPIC, '/compliance/activities',
                              [['limit', 100]], 'Anthropic');
    const events = raw.map(normaliseAnthropic).filter((e) => (e.when ?? 0) >= since);
    findings += report('anthropic', events, roster, options, false);
  }

  console.log(`${findings} finding(s)`);
  console.log('the repair is a schedule, not a run: poll from the stored ' +
              'watermark and route these events to somewhere a person looks');
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the note: an <code>api_key.created</code> at 02:14 UTC by an address that is not on the roster has to come back with three reasons, not one, and with <code>off-roster-actor</code> as the state, because that is the reason that decides how loudly it prints. The second is the one that keeps the script honest, and it is asserted twice: an empty feed and an unreachable feed both have to return <code>feed-unavailable</code>, never a clean pass. Then the shape work: the two OpenAI actor types, which keep their email in different places and one of which has none at all; an Anthropic activity, whose <code>country</code> must stay absent so the geography rule is skipped rather than silently passed; the <code>login.failed</code> burst; the watermark, which is the actual repair; and the project caveat, which fires on api_key actors and nowhere else.",
"test_py_file": "test_llm_key_lifecycle_review.py",
"test_py": '''import datetime as dt

from llm_key_lifecycle_review import (failed_login_bursts, feed_state, grade,
                                      hour_of, iso, normalise_anthropic,
                                      normalise_openai, parse_when,
                                      project_caveat, resolve_actor, watermark)

ROSTER = {"dana@example.test", "marco@example.test"}
COUNTRIES = ["US", "GB"]


def at(text):
    return int(dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())


def session_entry(event_type, when, email, ip="198.51.100.24", country="US"):
    return {"id": "audit_1", "type": event_type, "effective_at": when,
            "project": {"id": "proj_1", "name": "prod"},
            "actor": {"type": "session",
                      "session": {"user": {"email": email}, "ip_address": ip,
                                  "ip_address_details": {"country": country}}}}


def test_a_key_minted_at_2am_by_somebody_who_has_left_trips_three_rules():
    # The note in one assertion. Every reason is reported, and the state is the
    # most severe of them, because a reviewer wants all three and triage wants
    # one.
    event = normalise_openai(session_entry(
        "api_key.created", at("2026-03-17T02:14:08Z"), "ada@example.test",
        country="NL"))
    state, reasons = grade(event, ROSTER, (7, 19), COUNTRIES)
    assert state == "off-roster-actor"
    assert len(reasons) == 3
    assert any("not on the current roster" in r for r in reasons)
    assert any("outside the operating geographies" in r for r in reasons)
    assert any("02:00 UTC" in r for r in reasons)
    assert iso(event["when"]) == "2026-03-17T02:14:08Z"


def test_an_empty_feed_is_unavailable_and_never_clean():
    # Audit logging is gated. Reading silence as "no findings" turns a missing
    # control into a passing check, which is the worst outcome available here.
    empty_state, empty_detail = feed_state([], True)
    assert empty_state == "feed-unavailable"
    assert "not a clean result" in empty_detail
    unreachable_state, unreachable_detail = feed_state([], False)
    assert unreachable_state == "feed-unavailable"
    assert "could not be read" in unreachable_detail
    ok_state, ok_detail = feed_state([{"type": "api_key.created"}], True)
    assert ok_state == "feed-readable"
    assert "1 event(s)" in ok_detail


def test_the_two_openai_actor_shapes_keep_their_email_in_different_places():
    session = normalise_openai(session_entry(
        "api_key.created", at("2026-08-11T10:02:00Z"), "Dana@Example.test"))
    assert session["actor_kind"] == "session"
    assert session["actor_email"] == "dana@example.test"
    assert session["country"] == "US"
    assert grade(session, ROSTER, (7, 19), COUNTRIES)[0] == "reviewed"

    by_key = normalise_openai({
        "type": "api_key.deleted", "effective_at": at("2026-08-02T11:40:55Z"),
        "project": {"id": "proj_default"},
        "actor": {"type": "api_key", "api_key": {"id": "key_track",
                                                 "service_account": {"id": "svc_1"}}}})
    assert by_key["actor_kind"] == "api_key"
    assert by_key["actor_email"] is None
    assert resolve_actor(by_key, ROSTER) == "unattributable"
    state, reasons = grade(by_key, ROSTER, (7, 19), COUNTRIES)
    assert state == "unattributable"
    assert any("no user email" in r for r in reasons)
    assert "default project" in project_caveat(by_key)
    assert project_caveat(session) is None


def test_an_anthropic_activity_has_no_country_so_the_rule_is_skipped():
    event = normalise_anthropic({
        "type": "api_key.created", "created_at": "2026-08-14T09:31:00Z",
        "organization_id": "org_1",
        "actor": {"email_address": "MARCO@example.test", "user_id": "u_1",
                  "ip_address": "203.0.113.9", "user_agent": "curl/8"}})
    assert event["source"] == "anthropic"
    assert event["country"] is None
    assert event["actor_email"] == "marco@example.test"
    # The country rule cannot run, so an on-roster in-hours event is clean
    # rather than being failed for a field the feed does not have.
    assert grade(event, ROSTER, (7, 19), COUNTRIES)[0] == "reviewed"
    assert project_caveat(event) is None
    anonymous = normalise_anthropic({"type": "api_key.deleted",
                                     "created_at": "2026-08-14T09:31:00Z"})
    assert anonymous["actor_email"] is None
    assert resolve_actor(anonymous, ROSTER) == "unattributable"


def test_timestamps_arrive_in_two_shapes_and_the_hour_is_utc():
    assert parse_when(1_772_000_000) == 1_772_000_000
    assert parse_when("2026-03-17T02:14:08Z") == at("2026-03-17T02:14:08Z")
    assert parse_when("1772000000") == 1_772_000_000
    assert parse_when(None) is None
    assert parse_when(True) is None
    assert parse_when("whenever") is None
    assert hour_of({"when": at("2026-03-17T02:14:08Z")}) == 2
    assert hour_of({}) is None
    assert iso(None) == "(no timestamp)"


def test_a_burst_of_failed_logins_and_the_watermark_for_the_next_run():
    base = at("2026-08-20T09:00:00Z")
    events = [{"type": "login.failed", "when": base + i * 60,
               "actor_email": "ada@example.test"} for i in range(6)]
    events.append({"type": "api_key.created", "when": base + 4000,
                   "actor_email": "dana@example.test"})
    bursts = failed_login_bursts(events)
    assert len(bursts) == 1
    when, count, who = bursts[0]
    assert when == base and count >= 5 and who == "ada@example.test"
    # One failure is a typo, not a burst.
    assert failed_login_bursts([events[0]]) == []
    assert failed_login_bursts([]) == []
    assert watermark(events) == base + 4000
    assert watermark([]) is None
    assert watermark([{"type": "x"}]) is None


def test_an_out_of_hours_read_event_is_not_a_creation():
    # The out-of-hours rule fires on lifecycle events, not on everything that
    # happens to be timestamped at night.
    updated = {"source": "openai", "type": "api_key.updated",
               "when": at("2026-08-20T03:00:00Z"), "actor_kind": "session",
               "actor_email": "dana@example.test", "actor_ip": "203.0.113.1",
               "country": "US"}
    assert grade(updated, ROSTER, (7, 19), COUNTRIES)[0] == "reviewed"
    created = dict(updated, type="service_account.created")
    state, reasons = grade(created, ROSTER, (7, 19), COUNTRIES)
    assert state == "out-of-hours"
    assert reasons == ["created outside business hours (03:00 UTC)"]
''',
"test_js_file": "llm-key-lifecycle-review.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { failedLoginBursts, feedState, grade, hourOf, iso, normaliseAnthropic,
         normaliseOpenai, parseWhen, projectCaveat, resolveActor, watermark }
  from './llm-key-lifecycle-review.mjs';

const ROSTER = new Set(['dana@example.test', 'marco@example.test']);
const COUNTRIES = ['US', 'GB'];
const at = (text) => Math.floor(new Date(text).getTime() / 1000);

const sessionEntry = (type, when, email, ip = '198.51.100.24', country = 'US') => ({
  id: 'audit_1', type, effective_at: when,
  project: { id: 'proj_1', name: 'prod' },
  actor: { type: 'session',
           session: { user: { email }, ip_address: ip,
                      ip_address_details: { country } } },
});

test('a key minted at 2am by somebody who has left trips three rules', () => {
  const event = normaliseOpenai(sessionEntry(
    'api_key.created', at('2026-03-17T02:14:08Z'), 'ada@example.test',
    '198.51.100.24', 'NL'));
  const [state, reasons] = grade(event, ROSTER, [7, 19], COUNTRIES);
  assert.equal(state, 'off-roster-actor');
  assert.equal(reasons.length, 3);
  assert.ok(reasons.some((r) => r.includes('not on the current roster')));
  assert.ok(reasons.some((r) => r.includes('outside the operating geographies')));
  assert.ok(reasons.some((r) => r.includes('02:00 UTC')));
  assert.equal(iso(event.when), '2026-03-17T02:14:08Z');
});

test('an empty feed is unavailable and never clean', () => {
  const [emptyState, emptyDetail] = feedState([], true);
  assert.equal(emptyState, 'feed-unavailable');
  assert.match(emptyDetail, /not a clean result/);
  const [unreachableState, unreachableDetail] = feedState([], false);
  assert.equal(unreachableState, 'feed-unavailable');
  assert.match(unreachableDetail, /could not be read/);
  const [okState, okDetail] = feedState([{ type: 'api_key.created' }], true);
  assert.equal(okState, 'feed-readable');
  assert.match(okDetail, /1 event\\(s\\)/);
});

test('the two openai actor shapes keep their email in different places', () => {
  const session = normaliseOpenai(sessionEntry(
    'api_key.created', at('2026-08-11T10:02:00Z'), 'Dana@Example.test'));
  assert.equal(session.actorKind, 'session');
  assert.equal(session.actorEmail, 'dana@example.test');
  assert.equal(session.country, 'US');
  assert.equal(grade(session, ROSTER, [7, 19], COUNTRIES)[0], 'reviewed');

  const byKey = normaliseOpenai({
    type: 'api_key.deleted', effective_at: at('2026-08-02T11:40:55Z'),
    project: { id: 'proj_default' },
    actor: { type: 'api_key',
             api_key: { id: 'key_track', service_account: { id: 'svc_1' } } } });
  assert.equal(byKey.actorKind, 'api_key');
  assert.equal(byKey.actorEmail, null);
  assert.equal(resolveActor(byKey, ROSTER), 'unattributable');
  const [state, reasons] = grade(byKey, ROSTER, [7, 19], COUNTRIES);
  assert.equal(state, 'unattributable');
  assert.ok(reasons.some((r) => r.includes('no user email')));
  assert.match(projectCaveat(byKey), /default project/);
  assert.equal(projectCaveat(session), null);
});

test('an anthropic activity has no country so the rule is skipped', () => {
  const event = normaliseAnthropic({
    type: 'api_key.created', created_at: '2026-08-14T09:31:00Z',
    organization_id: 'org_1',
    actor: { email_address: 'MARCO@example.test', user_id: 'u_1',
             ip_address: '203.0.113.9', user_agent: 'curl/8' } });
  assert.equal(event.source, 'anthropic');
  assert.equal(event.country, null);
  assert.equal(event.actorEmail, 'marco@example.test');
  assert.equal(grade(event, ROSTER, [7, 19], COUNTRIES)[0], 'reviewed');
  assert.equal(projectCaveat(event), null);
  const anonymous = normaliseAnthropic({ type: 'api_key.deleted',
                                         created_at: '2026-08-14T09:31:00Z' });
  assert.equal(anonymous.actorEmail, null);
  assert.equal(resolveActor(anonymous, ROSTER), 'unattributable');
});

test('timestamps arrive in two shapes and the hour is utc', () => {
  assert.equal(parseWhen(1772000000), 1772000000);
  assert.equal(parseWhen('2026-03-17T02:14:08Z'), at('2026-03-17T02:14:08Z'));
  assert.equal(parseWhen('1772000000'), 1772000000);
  assert.equal(parseWhen(null), null);
  assert.equal(parseWhen(true), null);
  assert.equal(parseWhen('whenever'), null);
  assert.equal(hourOf({ when: at('2026-03-17T02:14:08Z') }), 2);
  assert.equal(hourOf({}), null);
  assert.equal(iso(null), '(no timestamp)');
});

test('a burst of failed logins and the watermark for the next run', () => {
  const base = at('2026-08-20T09:00:00Z');
  const events = Array.from({ length: 6 }, (_, i) => (
    { type: 'login.failed', when: base + i * 60, actorEmail: 'ada@example.test' }));
  events.push({ type: 'api_key.created', when: base + 4000,
                actorEmail: 'dana@example.test' });
  const bursts = failedLoginBursts(events);
  assert.equal(bursts.length, 1);
  assert.equal(bursts[0][0], base);
  assert.ok(bursts[0][1] >= 5);
  assert.equal(bursts[0][2], 'ada@example.test');
  assert.deepEqual(failedLoginBursts([events[0]]), []);
  assert.deepEqual(failedLoginBursts([]), []);
  assert.equal(watermark(events), base + 4000);
  assert.equal(watermark([]), null);
  assert.equal(watermark([{ type: 'x' }]), null);
});

test('an out of hours read event is not a creation', () => {
  const updated = { source: 'openai', type: 'api_key.updated',
                    when: at('2026-08-20T03:00:00Z'), actorKind: 'session',
                    actorEmail: 'dana@example.test', actorIp: '203.0.113.1',
                    country: 'US' };
  assert.equal(grade(updated, ROSTER, [7, 19], COUNTRIES)[0], 'reviewed');
  const created = { ...updated, type: 'service_account.created' };
  const [state, reasons] = grade(created, ROSTER, [7, 19], COUNTRIES);
  assert.equal(state, 'out-of-hours');
  assert.deepEqual(reasons, ['created outside business hours (03:00 UTC)']);
});
''',
"faq": [
 ("Why is an unread audit log a finding when nothing has gone wrong?",
  "Because the log is the only place where things that are already gone left a mark. The other key notes read the current roster, so they can tell you what a credential looks like today. None of them can tell you that a key existed for six weeks and was deleted, or that somebody minted one at 2am from a country you do not operate in, because the object those facts describe no longer exists. The feed is complete and correct and pull-only, so it accumulates until an incident, and by then the question is what happened eight months ago."),
 ("The feed came back empty. Does that mean the organization is clean?",
  "No, it means the answer is unknown. Audit logging is gated to organizations that have it enabled, so an empty response can mean nothing happened or can mean nothing is being recorded, and the two are indistinguishable from outside. A script that grades an empty feed as passing has converted a missing control into a green tick, which is worse than never having run it. This one returns feed-unavailable, refuses to grade anything, and says so on its first line of output."),
 ("Why does the country rule only run on OpenAI events?",
  "Because only OpenAI carries the field. An OpenAI session actor is unusually rich: email, IP, user agent, the ja3 and ja4 TLS fingerprints, and ip_address_details with country, city, region and ASN. Anthropic's Activity record carries an email address, a user id, an IP and a user agent, and no geography breakdown at all. Running the rule against a field that does not exist would pass every Anthropic event silently, so the script leaves country absent on that feed and reports which rules it was able to run on which provider."),
 ("What does resolving actors against the roster actually add?",
  "It converts a row into a decision. An email in an audit entry is just a string; the same email checked against the current member list is one of three things. On the roster, and the event is reviewable by asking that person. Not on the roster, and somebody whose access has since ended performed a credential action that nobody has read. No email at all, because the actor was an API key rather than a session, and the action cannot be attributed to a human at all. Only the first of those is a row a reviewer can close."),
 ("Is there anything about the project field I should not trust?",
  "Yes, and it catches people out. Admin actions taken with an OpenAI Admin API key are attributed to the default project, so on those entries the project tells you nothing about where the action landed. The script prints that caveat on exactly the entries it applies to rather than as a footnote. While you are there, note the rate limits: the audit-log endpoint is the one administration path that documents its own 429 with a Retry-After, and on Anthropic every /v1/compliance/* endpoint shares a single 600 requests per minute budget for the whole organization."),
],
"related": [REL_NEVER_USED, REL_ROTATION, REL_ARCHIVED],
"citations": [CITE_AUDIT_LOGS, CITE_AUDIT_HELP, CITE_AN_COMPLIANCE,
              CITE_AN_ACTIVITY],
},
]
