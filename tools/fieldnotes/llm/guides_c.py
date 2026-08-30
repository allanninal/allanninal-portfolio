#!/usr/bin/env python3
"""/llm/ field notes, batch C — the writing.

Four problems that live in the organization rather than in a single request:
two about credentials that outlive the reason they existed, and two about
prompt caching, which is the rare LLM setting that can be wrong in both
directions.

The two caching notes are a deliberate pair and must not be read as one note
written twice. `prompt-caching-never-used` is caching that was never switched
on: `cache_read_input_tokens` is flat zero, nothing is being written, and the
loss is the discount you are not taking. `cache-writes-with-no-reads` is
caching that *was* switched on and never earns its keep: writes are billed at
1.25x (5m) or 2x (1h) base input while reads are 0.1x, so a workload that
writes and never reads is paying strictly more than it would with caching
switched off. One is an unclaimed discount. The other is a surcharge.

The two key notes need an organization ADMIN key, because everything under
/v1/organization/* rejects a project key outright. An admin key can be
provisioned read-only, and read-only is all these scripts want.

Read-only throughout. GET requests only, and every repair is printed for a
human to run rather than performed.
"""

CITE_PROJECT_KEYS = ("Project API keys — OpenAI API reference",
                     "https://platform.openai.com/docs/api-reference/project-api-keys")
CITE_PROJECTS = ("Projects — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/projects")
CITE_AUDIT_LOGS = ("Audit logs — OpenAI API reference",
                   "https://platform.openai.com/docs/api-reference/audit-logs")
CITE_ADMIN_APIS = ("Administration APIs — OpenAI developer docs",
                   "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_USAGE_REPORT = ("Get messages usage report — Claude Admin API",
                     "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report")
CITE_COST_REPORT = ("Get cost report — Claude Admin API",
                    "https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report")
CITE_CACHING = ("Prompt caching — Claude Docs",
                "https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
CITE_PRICING = ("Pricing — Claude Docs",
                "https://platform.claude.com/docs/en/about-claude/pricing")

GUIDES = [

{
"slug": "key-owner-lost-project-access",
"title": "Keys still work after their owner loses project access",
"description": "Removing someone from a project revokes their console access, not their API key. One admin call lists the keys that are still live and still billing.",
"h1": "keys still work after their owner loses project access",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai owner_project_access inactive", "openai offboarding api key",
             "openai admin api keys audit", "revoke openai key former employee",
             "openai project api keys last_used_at"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "She left in March. The laptop came back, SSO was switched off the same afternoon, and the offboarding ticket was closed with every box ticked. The API key she minted in her second week is still in the environment of a nightly job, still authenticating, still billing. Nothing revoked it, because nothing was ever asked to: the key is a separate object from her membership, and removing the membership left the key exactly as it was.",
"short_answer": """<p>With an <strong>organization admin key</strong>, read <code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=inactive</code> for every project. Every object that comes back is a live, usable key whose owner no longer has effective access to that project.</p>
<p>The field is the whole finding. Each <code>organization.project.api_key</code> carries <code>owner_project_access</code>, which flips to <code>"inactive"</code> when the owning principal loses access &mdash; and the key itself stays enabled. Sort what you get by <code>last_used_at</code>, most recent first: those are the ones with production traffic behind them, and therefore the ones that break something when you revoke them.</p>
<p>An admin key provisioned read-only is enough for this. It has to be an admin key regardless: a project key gets a 401 from every <code>/v1/organization/*</code> endpoint.</p>""",
"problem": """<p>Offboarding has a mental model that does not match the API. The model is that a person has access, and removing the person removes the access. What actually exists is a person, and separately a set of credentials that person created, and the two are joined only by an ownership record. Deleting the membership deletes the join. It does not delete the credential, and the credential never needed the membership to work in the first place.</p>
<p>So the key keeps going, and it keeps going invisibly. It does not error, so nothing in your logs mentions it. It bills to the project, so the money looks normal. It appears in the audit log under a name nobody recognises any more, if anyone is reading the audit log. The only place the truth is written down is a single field on the key object, and until somebody asks for that field nothing surfaces it.</p>
<p>The security shape of this is worse than the accounting shape. A live key held by someone who no longer works here is a credential outside your control that can spend money on inference and, on most projects, read whatever the project's stored files and vector stores contain. It sits in a laptop backup, a personal password manager, a shell history, an old <code>.env</code> in a fork. None of those are places you can reach.</p>""",
"why": """<p><strong>A key's lifecycle is not attached to a person's.</strong> Creating a key is an action a member takes; the object it creates outlives the membership that permitted it. There is no cascade, no expiry, and no notification to anyone when the two fall out of step.</p>
<p><strong>Personal keys are the path of least resistance.</strong> Any project member can mint one in two clicks and it works immediately. A service account requires thinking about structure first. The result is that production ends up standing on credentials whose lifecycle is tied to somebody's employment rather than to the service's.</p>
<p><strong>The console does not show you this list.</strong> <code>owner_project_access</code> is a filter on an API call, not a red banner on a page. Nothing walks the projects for you, and nothing tells you the count went up.</p>
<p><strong>The default listing quietly changes what you see.</strong> Ask for keys without saying which owners you mean and you are relying on a default, which is exactly the position that produced the problem. Say <code>owner_project_access=any</code> when you want the inventory and <code>inactive</code> when you want the finding, and never read a short list as good news.</p>
<p><strong>Archived projects hide their share of it.</strong> A project you archived last year still holds keys, and it is not in the default project listing at all. A sweep that iterates projects without <code>include_archived=true</code> under-reports the org's live key surface by however many projects have been tidied away.</p>""",
"steps": [
 {"h": "Get an admin key, and make it read-only",
  "body": """<p><code>/v1/organization/*</code> rejects project keys, so this check cannot be done with the credential your application uses. Mint an organization admin key (<code>sk-admin-</code>), give it read scopes only, and treat it as the most sensitive thing in your secret store &mdash; it can enumerate every key in the org.</p>"""},
 {"h": "List every project, archived ones included",
  "body": """<p><code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>, following <code>has_more</code> and <code>last_id</code>. Archived projects are excluded by default and are the least-watched place a live key can sit.</p>"""},
 {"h": "Ask each project for the inactive-owner keys",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=inactive</code>. Read <code>id</code>, <code>name</code>, <code>redacted_value</code>, <code>owner.type</code>, <code>owner.user.email</code> and <code>last_used_at</code>. There is no interpretation to do here: every row is a live key whose owner is gone.</p>"""},
 {"h": "Sort by last use, not by age",
  "body": """<p><code>last_used_at</code> is a unix timestamp, and null on a key that has never authenticated anything. A never-used key is the safe one to revoke today. A key used this morning is production traffic on a departed person's credential, which is both the most urgent row and the one that breaks something if you revoke it without warning.</p>"""},
 {"h": "Re-issue first, revoke second, then schedule the sweep",
  "body": """<p>For anything with recent use, mint a replacement under a service account, deploy it, confirm the old key's <code>last_used_at</code> stops advancing, and only then remove the old key with <code>DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}</code>. Corroborate the timeline in <code>GET /v1/organization/audit_logs</code> if you need to know when the person actually left. Then put this sweep on a schedule, because doing it once fixes today and doing it weekly fixes offboarding.</p>"""},
],
"verify": """<p>Re-run the script. Every project should report zero keys with an inactive owner.</p>
<pre><code class="language-bash">python3 openai_orphaned_key_audit.py
# 34 key(s) read across 6 project(s), 0 whose owner no longer has project access</code></pre>""",
"code_intro": "Two paginated GETs and no writes at all. It wants an <strong>organization admin key</strong> because a project key cannot read <code>/v1/organization/*</code>; an admin key provisioned read-only satisfies both that requirement and this section's rule, and is what you should give it. The classification is a pure function so that the one case that matters &mdash; a missing <code>owner_project_access</code>, which must never be read as “fine” &mdash; is visible and tested rather than buried in the request loop.",
"py_file": "openai_orphaned_key_audit.py",
"py": '''"""Report OpenAI API keys whose owner no longer has access to the project.

Read only. GET requests and nothing else. This one needs an ORGANIZATION ADMIN
key (sk-admin-...), because every /v1/organization/* endpoint rejects a project
key outright; an admin key provisioned read-only is enough and is what you
should give it. The repair is printed, never performed: a key on this list may
still be carrying production traffic, and revoking it before you know that is
how a cleanup becomes an outage.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_orphaned_key_audit")

API = "https://api.openai.com/v1"
DAY = 86400

# Worst first, so the report leads with the key that is still serving traffic
# rather than with the harmless one that has never been used.
SEVERITY = {"serving": 4, "orphaned": 3, "unknown": 2, "dormant": 1, "in-force": 0}


def owner_label(key):
    """Best identity available for whoever owns a key. Pure.

    owner.type is "user" or "service_account"; only the user branch carries an
    email, and a service account carries a name instead. Falling back to the
    type rather than to "?" keeps the row readable when neither is populated.
    """
    owner = key.get("owner") or {}
    user = owner.get("user") or {}
    account = owner.get("service_account") or {}
    return (user.get("email") or user.get("name") or account.get("name")
            or owner.get("type") or "unknown owner")


def verdict(key, now, hot_days=7):
    """Classify one organization.project.api_key object.

    Pure, so the rules can be read and tested without an admin credential and
    without a network. `now` is a unix timestamp, and so are `last_used_at` and
    `created_at` on this object; `last_used_at` is null on a key that has never
    authenticated a request.

    Returns (state, detail).
    """
    raw = key.get("owner_project_access")
    if raw is None:
        return ("unknown",
                "no owner_project_access on this object: ask for it explicitly "
                "with owner_project_access=any and re-read, rather than taking "
                "the absence for active")
    access = str(raw).strip().lower()
    if access == "active":
        return ("in-force", "owner still has access to this project")
    if access != "inactive":
        return ("unknown", "unrecognised owner_project_access %r" % (raw,))

    last = key.get("last_used_at")
    if last is None:
        return ("dormant",
                "owner has lost project access and this key has never "
                "authenticated a request. Nothing depends on it, so it is the "
                "safe one to revoke first.")
    age = (int(now) - int(last)) // DAY
    if age <= hot_days:
        return ("serving",
                "owner has lost project access and the key authenticated a "
                "request %d day(s) ago. Something in production is still "
                "holding it: re-issue before you revoke." % age)
    return ("orphaned",
            "owner has lost project access; last used %d day(s) ago" % age)


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-...), not a project key")
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    """Walk a cursor-paginated admin listing."""
    params.setdefault("limit", 100)
    while True:
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or data[-1].get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hot-days", type=int, default=7,
                    help="a key used inside this many days counts as live traffic")
    ap.add_argument("--all-keys", action="store_true",
                    help="read every key (owner_project_access=any), not only the "
                         "inactive-owner ones, for a full inventory")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key (sk-admin-...); "
                  "a project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    now = int(time.time())
    scope = "any" if args.all_keys else "inactive"

    rows = []
    projects = 0
    # include_archived=true, because an archived project still holds live keys
    # and is absent from the default listing.
    for project in paged(s, "/organization/projects", include_archived="true"):
        projects += 1
        path = "/organization/projects/%s/api_keys" % project["id"]
        for key in paged(s, path, owner_project_access=scope):
            state, detail = verdict(key, now, args.hot_days)
            rows.append((state, detail, project, key))

    rows.sort(key=lambda r: (-SEVERITY.get(r[0], 2), -(r[3].get("last_used_at") or 0)))

    bad = 0
    for state, detail, project, key in rows:
        line = "%-9s %s / %s  %s  %s" % (
            state, project.get("name") or project["id"], owner_label(key),
            key.get("redacted_value") or "?", detail)
        if state == "in-force":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: mint a replacement under a service account, deploy "
                    "it, confirm last_used_at stops moving, then remove this one: "
                    "DELETE %s/organization/projects/%s/api_keys/%s",
                    API, project["id"], key.get("id"))

    log.info("%d key(s) read across %d project(s), %d whose owner no longer has "
             "project access", len(rows), projects, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-orphaned-key-audit.mjs",
"js": '''/**
 * Report OpenAI API keys whose owner no longer has access to the project.
 *
 * Read only. GET requests and nothing else, and it needs an ORGANIZATION ADMIN
 * key (sk-admin-...) because /v1/organization/* rejects project keys. An admin
 * key provisioned read-only is enough. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;

// Worst first, so the report leads with the key still serving traffic.
const SEVERITY = { serving: 4, orphaned: 3, unknown: 2, dormant: 1, 'in-force': 0 };

/** Best identity available for whoever owns a key. Pure. */
export function ownerLabel(key) {
  const owner = key.owner ?? {};
  const user = owner.user ?? {};
  const account = owner.service_account ?? {};
  return user.email || user.name || account.name || owner.type || 'unknown owner';
}

/**
 * Classify one organization.project.api_key object. Pure, so the rules can be
 * tested without an admin credential and without a network.
 */
export function verdict(key, now, hotDays = 7) {
  const raw = key.owner_project_access;
  if (raw === undefined || raw === null) {
    return ['unknown',
      'no owner_project_access on this object: ask for it explicitly with ' +
      'owner_project_access=any and re-read, rather than taking the absence ' +
      'for active'];
  }
  const access = String(raw).trim().toLowerCase();
  if (access === 'active') return ['in-force', 'owner still has access to this project'];
  if (access !== 'inactive') {
    return ['unknown', `unrecognised owner_project_access ${JSON.stringify(raw)}`];
  }

  const last = key.last_used_at;
  if (last === undefined || last === null) {
    return ['dormant',
      'owner has lost project access and this key has never authenticated a ' +
      'request. Nothing depends on it, so it is the safe one to revoke first.'];
  }
  const age = Math.floor((Number(now) - Number(last)) / DAY);
  if (age <= hotDays) {
    return ['serving',
      `owner has lost project access and the key authenticated a request ${age} ` +
      'day(s) ago. Something in production is still holding it: re-issue before ' +
      'you revoke.'];
  }
  return ['orphaned', `owner has lost project access; last used ${age} day(s) ago`];
}

async function get(adminKey, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${adminKey}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: /v1/organization/* needs an organization ' +
                    'admin key (sk-admin-...), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paged(adminKey, path, params = {}) {
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1].id;
  }
}

async function main() {
  const adminKey = process.env.OPENAI_ADMIN_KEY;
  if (!adminKey) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key (sk-admin-...); ' +
                  'a project key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }

  const hotDays = Number(process.env.HOT_DAYS ?? 7);
  const scope = process.env.ALL_KEYS ? 'any' : 'inactive';
  const now = Math.floor(Date.now() / 1000);

  const rows = [];
  let projects = 0;
  // include_archived=true: an archived project still holds live keys and is
  // absent from the default listing.
  for await (const project of paged(adminKey, '/organization/projects',
                                    { include_archived: 'true' })) {
    projects += 1;
    const path = `/organization/projects/${project.id}/api_keys`;
    for await (const key of paged(adminKey, path, { owner_project_access: scope })) {
      const [state, detail] = verdict(key, now, hotDays);
      rows.push({ state, detail, project, key });
    }
  }

  rows.sort((a, b) =>
    (SEVERITY[b.state] ?? 2) - (SEVERITY[a.state] ?? 2) ||
    (b.key.last_used_at ?? 0) - (a.key.last_used_at ?? 0));

  let bad = 0;
  for (const { state, detail, project, key } of rows) {
    const line = `${state.padEnd(9)} ${project.name ?? project.id} / ` +
                 `${ownerLabel(key)}  ${key.redacted_value ?? '?'}  ${detail}`;
    if (state === 'in-force') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn('  repair: mint a replacement under a service account, deploy it, ' +
                 'confirm last_used_at stops moving, then remove this one: ' +
                 `DELETE ${API}/organization/projects/${project.id}/api_keys/${key.id}`);
  }

  console.log(`${rows.length} key(s) read across ${projects} project(s), ${bad} ` +
              'whose owner no longer has project access');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main(), fail on the missing key, and set a non-zero exit code
// that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is the key with no <code>owner_project_access</code> at all. A classifier that treats a missing field as active reports a clean organization on a response that never carried the answer, which is the one failure mode nobody would notice. The other case worth its own state is the inactive-owner key that was used this morning: revoking that one without re-issuing first is an outage, so it cannot share a label with the key nobody has ever used.",
"test_py_file": "test_openai_orphaned_key_audit.py",
"test_py": '''from openai_orphaned_key_audit import owner_label, verdict

NOW = 1_756_000_000  # a fixed clock, so these never age out


def make(**over):
    key = {
        "id": "key_abc",
        "redacted_value": "sk-proj-...aB3d",
        "owner_project_access": "active",
        "last_used_at": NOW - 3600,
        "owner": {"type": "user", "user": {"email": "dev@example.com"}},
    }
    key.update(over)
    return key


def test_active_owner_is_not_a_finding():
    state, _ = verdict(make(), NOW)
    assert state == "in-force"


def test_inactive_owner_used_today_is_production_traffic():
    state, detail = verdict(make(owner_project_access="inactive"), NOW)
    assert state == "serving"
    assert "re-issue" in detail


def test_inactive_owner_long_idle_is_orphaned_not_serving():
    state, detail = verdict(
        make(owner_project_access="inactive", last_used_at=NOW - 90 * 86400), NOW)
    assert state == "orphaned"
    assert "90 day(s)" in detail


def test_inactive_owner_never_used_is_the_safe_one():
    state, detail = verdict(
        make(owner_project_access="inactive", last_used_at=None), NOW)
    assert state == "dormant"
    assert "revoke first" in detail


def test_missing_access_field_is_never_read_as_active():
    # The whole point: an absent field is an unanswered question, not a clean org.
    key = make()
    del key["owner_project_access"]
    state, detail = verdict(key, NOW)
    assert state == "unknown"
    assert "owner_project_access=any" in detail


def test_unrecognised_access_value_is_not_silently_fine():
    assert verdict(make(owner_project_access="pending"), NOW)[0] == "unknown"


def test_a_service_account_key_is_judged_on_the_same_field():
    key = make(owner_project_access="inactive",
               owner={"type": "service_account",
                      "service_account": {"name": "batch-runner"}})
    assert verdict(key, NOW)[0] == "serving"
    assert owner_label(key) == "batch-runner"


def test_owner_label_prefers_the_email():
    assert owner_label(make()) == "dev@example.com"
    assert owner_label({"owner": {"type": "user"}}) == "user"
    assert owner_label({}) == "unknown owner"


def test_the_hot_window_is_a_parameter_not_a_constant():
    key = make(owner_project_access="inactive", last_used_at=NOW - 20 * 86400)
    assert verdict(key, NOW, hot_days=7)[0] == "orphaned"
    assert verdict(key, NOW, hot_days=30)[0] == "serving"
''',
"test_js_file": "openai-orphaned-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ownerLabel, verdict } from './openai-orphaned-key-audit.mjs';

const NOW = 1_756_000_000;

const make = (over = {}) => ({
  id: 'key_abc',
  redacted_value: 'sk-proj-...aB3d',
  owner_project_access: 'active',
  last_used_at: NOW - 3600,
  owner: { type: 'user', user: { email: 'dev@example.com' } },
  ...over,
});

test('active owner is not a finding', () => {
  assert.equal(verdict(make(), NOW)[0], 'in-force');
});

test('inactive owner used today is production traffic', () => {
  const [state, detail] = verdict(make({ owner_project_access: 'inactive' }), NOW);
  assert.equal(state, 'serving');
  assert.match(detail, /re-issue/);
});

test('inactive owner long idle is orphaned not serving', () => {
  const [state, detail] = verdict(
    make({ owner_project_access: 'inactive', last_used_at: NOW - 90 * 86400 }), NOW);
  assert.equal(state, 'orphaned');
  assert.match(detail, /90 day\\(s\\)/);
});

test('inactive owner never used is the safe one', () => {
  const [state, detail] = verdict(
    make({ owner_project_access: 'inactive', last_used_at: null }), NOW);
  assert.equal(state, 'dormant');
  assert.match(detail, /revoke first/);
});

test('missing access field is never read as active', () => {
  const key = make();
  delete key.owner_project_access;
  const [state, detail] = verdict(key, NOW);
  assert.equal(state, 'unknown');
  assert.match(detail, /owner_project_access=any/);
});

test('unrecognised access value is not silently fine', () => {
  assert.equal(verdict(make({ owner_project_access: 'pending' }), NOW)[0], 'unknown');
});

test('a service account key is judged on the same field', () => {
  const key = make({
    owner_project_access: 'inactive',
    owner: { type: 'service_account', service_account: { name: 'batch-runner' } },
  });
  assert.equal(verdict(key, NOW)[0], 'serving');
  assert.equal(ownerLabel(key), 'batch-runner');
});

test('owner label prefers the email', () => {
  assert.equal(ownerLabel(make()), 'dev@example.com');
  assert.equal(ownerLabel({ owner: { type: 'user' } }), 'user');
  assert.equal(ownerLabel({}), 'unknown owner');
});

test('the hot window is a parameter not a constant', () => {
  const key = make({ owner_project_access: 'inactive', last_used_at: NOW - 20 * 86400 });
  assert.equal(verdict(key, NOW, 7)[0], 'orphaned');
  assert.equal(verdict(key, NOW, 30)[0], 'serving');
});
''',
"faq": [
 ("Why does this need an admin key when the rest of the section does not?",
  "Because the endpoint lives under /v1/organization/, and every path under it rejects project keys with a 401. There is no project-scoped way to ask which keys exist or who owns them. Mint an organization admin key (sk-admin-), give it read scopes only, and store it somewhere more carefully than the key your application runs on: an admin-read key cannot spend money, but it can enumerate every credential in the organization."),
 ("Is an admin key really read-only?",
  "It can be. Admin keys carry scopes, and an admin key with only the read scopes can list projects, keys, users, usage and costs and nothing else. That is all this script asks for, and all it should be given. The word admin describes what the key can see, not what this script does with it."),
 ("Does removing someone from the organization revoke their keys?",
  "No, and that is the entire note. Membership and credentials are separate objects. Removing the membership ends their console access and flips owner_project_access to inactive on their keys, which is how you find them, but the keys themselves stay enabled and keep authenticating until somebody deletes them."),
 ("Can I just delete every key this reports?",
  "Not blindly. A key with a recent last_used_at is carrying live traffic, and deleting it takes that traffic down with no grace period. Mint the replacement under a service account first, deploy it, watch the old key's last_used_at stop advancing, then delete. Keys with a null last_used_at have never authenticated anything and can go today."),
 ("How do I stop this from coming back?",
  "Run the owner_project_access=inactive sweep as a scheduled job rather than an offboarding checklist item, and move production onto service accounts so that a person leaving is never the same event as a credential dying. The checklist gets skipped; the cron job does not."),
],
"related": [
 ("/llm/archived-project-still-holds-keys/", "An archived project still holding live keys"),
 ("/llm/prompt-caching-never-used/", "Prompt caching that was never switched on"),
 ("/llm/cache-writes-with-no-reads/", "Cache writes that are never read back"),
],
"citations": [CITE_PROJECT_KEYS, CITE_PROJECTS, CITE_ADMIN_APIS, CITE_AUDIT_LOGS],
},

{
"slug": "archived-project-still-holds-keys",
"title": "An archived project still holds live API keys",
"description": "Archiving hides a project from the default listing without revoking anything inside it. Without include_archived=true your key audit never sees those keys.",
"h1": "an archived project still holds live API keys",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai include_archived projects", "openai archived project api keys",
             "openai project archive revoke keys", "openai admin api project audit",
             "openai archived project still billing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The prototype was shut down in the spring. The project was archived, which felt like closing it: it vanished from the console's project switcher and from every list anyone looks at. Nothing inside it was touched. Two keys are still enabled, one of them authenticated a request last Tuesday, and the quarterly key audit has never seen either of them, because the audit iterates projects and archived projects are not in the default listing.",
"short_answer": """<p>With an <strong>organization admin key</strong>, call <code>GET /v1/organization/projects?limit=100&amp;include_archived=true</code>. That parameter is the whole trick: archived projects are excluded by default, so any audit that omits it is auditing a subset of your organization by construction.</p>
<p>Filter to <code>status == "archived"</code> (equivalently <code>archived_at != null</code>) and then, for each one, <code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code>. Any key returned is live inside a project everyone considers closed. Escalate any whose <code>last_used_at</code> is later than the project's <code>archived_at</code>: the project is still serving traffic.</p>
<p>An admin key provisioned read-only is enough, and an admin key is required &mdash; a project key gets a 401 from every <code>/v1/organization/*</code> path.</p>""",
"problem": """<p>Archiving reads as a closing action. It is a visibility action. <code>POST /v1/organization/projects/{project_id}/archive</code> sets <code>archived_at</code>, flips <code>status</code> to <code>"archived"</code>, and removes the project from default listings and the console switcher. It does not enumerate the credentials inside, does not disable them, and does not warn you that any exist. Projects cannot be deleted at all, so archiving is the only closing gesture available, which is exactly why people reach for it and assume it does more than it does.</p>
<p>What is left behind is the least-monitored credential in the organization. It is live, it is attached to a project nobody opens, its spend rolls into a cost report line for a project name nobody recognises, and it is structurally absent from the sweep that was supposed to catch it. Every other key in your org is at least in a list somewhere. These are not.</p>
<p>The audit blind spot is the part worth internalising. A key audit that walks projects without <code>include_archived=true</code> does not report an error, does not report a smaller number, and does not hint that anything is missing. It returns a clean result over a partial universe, which is the most convincing kind of wrong answer.</p>""",
"why": """<p><strong>Archive is a filter, not a revocation.</strong> The operation changes two fields on the project object. Nothing cascades to the keys, the service accounts, the files or the vector stores inside it.</p>
<p><strong>The exclusion is the default, not the exception.</strong> <code>include_archived</code> defaults to false, so you have to know the parameter exists before you can ask the question. Nobody writes a script to include a category of thing they do not know is being hidden.</p>
<p><strong>Projects cannot be deleted, so archiving absorbs every kind of ending.</strong> Finished prototype, cancelled customer, migrated workload, wrong name at creation: all of them end in the same state, which means the archived list is where the organization's history accumulates, keys and all.</p>
<p><strong>An archived project can still bill.</strong> Nothing stops a key inside it from calling the API. <code>GET /v1/organization/costs?start_time={now-30d}&amp;group_by=project_id</code> returning a non-zero amount for an archived <code>project_id</code> is a project that was closed on paper and is spending money in fact.</p>
<p><strong>The keys inside outlive their owners too.</strong> Archiving a project is often part of a team winding down, so the keys in there are disproportionately likely to be owned by people who have since left &mdash; the two findings compound, and the combined case is invisible from both directions.</p>""",
"steps": [
 {"h": "List projects twice and compare the counts",
  "body": """<p>Call <code>GET /v1/organization/projects?limit=100</code> and then again with <code>include_archived=true</code>. The difference between the two counts is the number of projects your existing audits have never looked at. Doing it this way once is worth more than being told the parameter exists.</p>"""},
 {"h": "Select the archived ones properly",
  "body": """<p><code>status == "archived"</code> and <code>archived_at != null</code> should agree. If they disagree, trust <code>status</code> and report the object, because a project in an unexpected shape is a finding rather than a row to skip.</p>"""},
 {"h": "Enumerate the keys inside each",
  "body": """<p><code>GET /v1/organization/projects/{project_id}/api_keys?limit=100&amp;owner_project_access=any</code>. Use <code>any</code> here rather than accepting the default: you want the full key surface of a project nobody is watching, not a filtered view of it.</p>"""},
 {"h": "Compare last_used_at against archived_at",
  "body": """<p>Both are unix timestamps. A key used <em>after</em> the archive date means the project is still doing work, which is a live integration nobody has an owner for. A key that has not been used since before the archive is dead weight you can remove immediately. A key with a null <code>last_used_at</code> has never been used at all.</p>"""},
 {"h": "Corroborate with spend, then fix the audit itself",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-30d}&amp;group_by=project_id</code> tells you whether an archived project is still costing money. Then revoke with <code>DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}</code> per key &mdash; and change the standing audit job to pass <code>include_archived=true</code>, because that line is the durable half of the repair.</p>"""},
],
"verify": """<p>Re-run the script. Every archived project should report zero live keys, and the coverage line should confirm the listing included them.</p>
<pre><code class="language-bash">python3 openai_archived_project_keys.py
# listing covers archived projects: yes
# 9 project(s), 3 archived, 0 live key(s) inside them</code></pre>""",
"code_intro": "One paginated GET for the projects and one per archived project for its keys, with an <strong>organization admin key</strong> because <code>/v1/organization/*</code> rejects project keys; read-only admin scopes are enough and are what you should give it. Two pure functions carry the note: one asks whether a listing call would have included archived projects at all, which is the mistake this note exists for, and one classifies an archived project against the keys found inside it.",
"py_file": "openai_archived_project_keys.py",
"py": '''"""Report live API keys sitting inside archived OpenAI projects.

Read only. GET requests and nothing else, with an ORGANIZATION ADMIN key
(sk-admin-...) because /v1/organization/* rejects project keys; read-only admin
scopes are enough. The repair is printed, never performed.

Archiving a project hides it from the default listing without revoking anything
inside it, so the parameter below is the whole point of the script.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_archived_project_keys")

API = "https://api.openai.com/v1"
DAY = 86400

TRUTHY = ("true", "1", "yes", "on")


def covers_archived(params):
    """True when a projects listing will actually include archived projects.

    Pure. include_archived defaults to false, so a key audit that never passes
    it is auditing a subset of the organization and reporting a clean result
    over it. Accepts the bool and the query-string spelling, because the value
    reaches the API as a string either way.
    """
    value = params.get("include_archived")
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in TRUTHY


def verdict(project, keys, now):
    """Classify one project against the keys found inside it.

    Pure, so the comparison between a key's last_used_at and the project's
    archived_at is testable without an admin credential. All three timestamps
    are unix seconds; last_used_at is null on a key that has never been used.

    Returns (state, detail).
    """
    status = str(project.get("status") or "").strip().lower()
    archived_at = project.get("archived_at")
    if status != "archived" and archived_at is None:
        return ("active", "not archived; outside the scope of this check")

    keys = list(keys or [])
    if not keys:
        return ("clean", "archived, and holds no API keys")

    used_after = [k for k in keys
                  if k.get("last_used_at") and archived_at
                  and int(k["last_used_at"]) > int(archived_at)]
    if used_after:
        newest = max(int(k["last_used_at"]) for k in used_after)
        return ("still-serving",
                "%d of %d live key(s) authenticated a request after the project "
                "was archived, the most recent %d day(s) ago. This project is "
                "closed on paper and running in fact."
                % (len(used_after), len(keys), (int(now) - newest) // DAY))

    ever_used = [k for k in keys if k.get("last_used_at")]
    if ever_used:
        newest = max(int(k["last_used_at"]) for k in ever_used)
        return ("live-keys",
                "%d live key(s) inside an archived project, last used %d day(s) "
                "ago. Nothing has needed them since the archive."
                % (len(keys), (int(now) - newest) // DAY))
    return ("dormant-keys",
            "%d live key(s) inside an archived project, none of which has ever "
            "authenticated a request" % len(keys))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-...), not a project key")
    r.raise_for_status()
    return r.json()


def paged(session, path, **params):
    params.setdefault("limit", 100)
    while True:
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or data[-1].get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show-active", action="store_true",
                    help="also print the projects that are not archived")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key (sk-admin-...); "
                  "a project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})
    now = int(time.time())

    listing = {"limit": 100, "include_archived": "true"}
    # Stated out loud, because the silent version of this mistake is what the
    # note is about: a sweep that omits the parameter reports a clean subset.
    log.info("listing covers archived projects: %s",
             "yes" if covers_archived(listing) else "NO, this audit is partial")

    projects = list(paged(s, "/organization/projects", **listing))
    archived = 0
    exposed = 0
    for project in projects:
        keys = []
        if str(project.get("status") or "").lower() == "archived" \\
                or project.get("archived_at") is not None:
            archived += 1
            keys = list(paged(s, "/organization/projects/%s/api_keys" % project["id"],
                              owner_project_access="any"))
        state, detail = verdict(project, keys, now)
        line = "%-13s %s  %s" % (state, project.get("name") or project["id"], detail)
        if state in ("active", "clean"):
            if state == "clean" or args.show_active:
                log.info(line)
            continue
        exposed += len(keys)
        log.warning(line)
        for key in keys:
            log.warning("  repair: DELETE %s/organization/projects/%s/api_keys/%s  (%s)",
                        API, project["id"], key.get("id"),
                        key.get("redacted_value") or key.get("name") or "unnamed")
        log.warning("  and check the spend: GET %s/organization/costs"
                    "?start_time=<now-30d>&group_by=project_id", API)

    log.info("%d project(s), %d archived, %d live key(s) inside them",
             len(projects), archived, exposed)
    return 1 if exposed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-archived-project-keys.mjs",
"js": '''/**
 * Report live API keys sitting inside archived OpenAI projects.
 *
 * Read only. GET requests and nothing else, with an ORGANIZATION ADMIN key
 * (sk-admin-...) because /v1/organization/* rejects project keys; read-only
 * admin scopes are enough. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400;
const TRUTHY = ['true', '1', 'yes', 'on'];

/**
 * True when a projects listing will actually include archived projects. Pure.
 * include_archived defaults to false, so an audit that never passes it reports
 * a clean result over a subset of the organization.
 */
export function coversArchived(params = {}) {
  const value = params.include_archived;
  if (typeof value === 'boolean') return value;
  if (value === undefined || value === null) return false;
  return TRUTHY.includes(String(value).trim().toLowerCase());
}

/**
 * Classify one project against the keys found inside it. Pure. All timestamps
 * are unix seconds; last_used_at is null on a key that has never been used.
 */
export function verdict(project, keys, now) {
  const status = String(project.status ?? '').trim().toLowerCase();
  const archivedAt = project.archived_at;
  if (status !== 'archived' && (archivedAt === undefined || archivedAt === null)) {
    return ['active', 'not archived; outside the scope of this check'];
  }

  const all = [...(keys ?? [])];
  if (all.length === 0) return ['clean', 'archived, and holds no API keys'];

  const usedAfter = all.filter((k) => k.last_used_at && archivedAt &&
                                      Number(k.last_used_at) > Number(archivedAt));
  if (usedAfter.length > 0) {
    const newest = Math.max(...usedAfter.map((k) => Number(k.last_used_at)));
    const days = Math.floor((Number(now) - newest) / DAY);
    return ['still-serving',
      `${usedAfter.length} of ${all.length} live key(s) authenticated a request ` +
      `after the project was archived, the most recent ${days} day(s) ago. This ` +
      'project is closed on paper and running in fact.'];
  }

  const everUsed = all.filter((k) => k.last_used_at);
  if (everUsed.length > 0) {
    const newest = Math.max(...everUsed.map((k) => Number(k.last_used_at)));
    const days = Math.floor((Number(now) - newest) / DAY);
    return ['live-keys',
      `${all.length} live key(s) inside an archived project, last used ${days} ` +
      'day(s) ago. Nothing has needed them since the archive.'];
  }
  return ['dormant-keys',
    `${all.length} live key(s) inside an archived project, none of which has ` +
    'ever authenticated a request'];
}

async function get(adminKey, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${adminKey}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: /v1/organization/* needs an organization ' +
                    'admin key (sk-admin-...), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paged(adminKey, path, params = {}) {
  const q = { limit: 100, ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1].id;
  }
}

async function main() {
  const adminKey = process.env.OPENAI_ADMIN_KEY;
  if (!adminKey) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key (sk-admin-...); ' +
                  'a project key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const now = Math.floor(Date.now() / 1000);

  const listing = { limit: 100, include_archived: 'true' };
  console.log(`listing covers archived projects: ${
    coversArchived(listing) ? 'yes' : 'NO, this audit is partial'}`);

  const projects = [];
  for await (const p of paged(adminKey, '/organization/projects', listing)) projects.push(p);

  let archived = 0;
  let exposed = 0;
  for (const project of projects) {
    let keys = [];
    const isArchived = String(project.status ?? '').toLowerCase() === 'archived' ||
                       (project.archived_at !== undefined && project.archived_at !== null);
    if (isArchived) {
      archived += 1;
      for await (const k of paged(adminKey,
                                  `/organization/projects/${project.id}/api_keys`,
                                  { owner_project_access: 'any' })) keys.push(k);
    }
    const [state, detail] = verdict(project, keys, now);
    const line = `${state.padEnd(13)} ${project.name ?? project.id}  ${detail}`;
    if (state === 'active' || state === 'clean') {
      if (state === 'clean') console.log(line);
      continue;
    }
    exposed += keys.length;
    console.warn(line);
    for (const key of keys) {
      console.warn(`  repair: DELETE ${API}/organization/projects/${project.id}` +
                   `/api_keys/${key.id}  (${key.redacted_value ?? key.name ?? 'unnamed'})`);
    }
    console.warn(`  and check the spend: GET ${API}/organization/costs` +
                 '?start_time=<now-30d>&group_by=project_id');
  }

  console.log(`${projects.length} project(s), ${archived} archived, ${exposed} ` +
              'live key(s) inside them');
  process.exitCode = exposed ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are pinned here. The first is the coverage check, because <code>include_archived</code> arrives as the string <code>\"false\"</code> often enough that a truthiness test on it passes and the audit silently narrows to the projects it was always going to see. The second is the difference between a key last used before the archive and one used after it: the same count of live keys, and completely different urgency.",
"test_py_file": "test_openai_archived_project_keys.py",
"test_py": '''from openai_archived_project_keys import covers_archived, verdict

NOW = 1_756_000_000
ARCHIVED_AT = NOW - 120 * 86400


def project(**over):
    p = {"id": "proj_x", "name": "prototype", "status": "archived",
         "archived_at": ARCHIVED_AT}
    p.update(over)
    return p


def key(last_used_at=None, **over):
    k = {"id": "key_1", "redacted_value": "sk-proj-...9f2c",
         "last_used_at": last_used_at}
    k.update(over)
    return k


def test_a_listing_without_the_parameter_does_not_cover_archived():
    assert covers_archived({"limit": 100}) is False


def test_the_string_false_is_not_truthy_here():
    # The quiet version of this bug: a non-empty string read as "yes".
    assert covers_archived({"include_archived": "false"}) is False
    assert covers_archived({"include_archived": False}) is False


def test_the_parameter_is_recognised_in_the_spellings_that_reach_the_api():
    assert covers_archived({"include_archived": "true"}) is True
    assert covers_archived({"include_archived": "TRUE"}) is True
    assert covers_archived({"include_archived": True}) is True
    assert covers_archived({"include_archived": "1"}) is True


def test_an_active_project_is_out_of_scope():
    state, _ = verdict(project(status="active", archived_at=None), [key(NOW)], NOW)
    assert state == "active"


def test_an_archived_project_with_no_keys_is_clean():
    assert verdict(project(), [], NOW)[0] == "clean"


def test_a_key_used_after_the_archive_is_the_urgent_case():
    state, detail = verdict(project(), [key(ARCHIVED_AT + 10 * 86400)], NOW)
    assert state == "still-serving"
    assert "closed on paper" in detail


def test_a_key_last_used_before_the_archive_is_dead_weight():
    state, detail = verdict(project(), [key(ARCHIVED_AT - 5 * 86400)], NOW)
    assert state == "live-keys"
    assert "since the archive" in detail


def test_a_never_used_key_is_still_reported():
    state, detail = verdict(project(), [key(None)], NOW)
    assert state == "dormant-keys"
    assert "has ever authenticated" in detail


def test_status_archived_without_a_timestamp_is_still_archived():
    # Nothing to compare last_used_at against, so it cannot be still-serving,
    # but it must not fall through to "active" either.
    state, _ = verdict(project(archived_at=None), [key(NOW - 86400)], NOW)
    assert state == "live-keys"
''',
"test_js_file": "openai-archived-project-keys.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coversArchived, verdict } from './openai-archived-project-keys.mjs';

const NOW = 1_756_000_000;
const ARCHIVED_AT = NOW - 120 * 86400;

const project = (over = {}) => ({
  id: 'proj_x', name: 'prototype', status: 'archived', archived_at: ARCHIVED_AT, ...over,
});
const key = (lastUsedAt = null, over = {}) => ({
  id: 'key_1', redacted_value: 'sk-proj-...9f2c', last_used_at: lastUsedAt, ...over,
});

test('a listing without the parameter does not cover archived', () => {
  assert.equal(coversArchived({ limit: 100 }), false);
  assert.equal(coversArchived(), false);
});

test('the string false is not truthy here', () => {
  assert.equal(coversArchived({ include_archived: 'false' }), false);
  assert.equal(coversArchived({ include_archived: false }), false);
});

test('the parameter is recognised in the spellings that reach the API', () => {
  assert.equal(coversArchived({ include_archived: 'true' }), true);
  assert.equal(coversArchived({ include_archived: 'TRUE' }), true);
  assert.equal(coversArchived({ include_archived: true }), true);
  assert.equal(coversArchived({ include_archived: '1' }), true);
});

test('an active project is out of scope', () => {
  assert.equal(
    verdict(project({ status: 'active', archived_at: null }), [key(NOW)], NOW)[0],
    'active');
});

test('an archived project with no keys is clean', () => {
  assert.equal(verdict(project(), [], NOW)[0], 'clean');
});

test('a key used after the archive is the urgent case', () => {
  const [state, detail] = verdict(project(), [key(ARCHIVED_AT + 10 * 86400)], NOW);
  assert.equal(state, 'still-serving');
  assert.match(detail, /closed on paper/);
});

test('a key last used before the archive is dead weight', () => {
  const [state, detail] = verdict(project(), [key(ARCHIVED_AT - 5 * 86400)], NOW);
  assert.equal(state, 'live-keys');
  assert.match(detail, /since the archive/);
});

test('a never used key is still reported', () => {
  const [state, detail] = verdict(project(), [key(null)], NOW);
  assert.equal(state, 'dormant-keys');
  assert.match(detail, /has ever authenticated/);
});

test('status archived without a timestamp is still archived', () => {
  assert.equal(verdict(project({ archived_at: null }), [key(NOW - 86400)], NOW)[0],
               'live-keys');
});
''',
"faq": [
 ("Does archiving a project revoke its API keys?",
  "No. Archiving sets archived_at and flips status to archived, which removes the project from default listings and from the console's project switcher. The keys inside remain enabled and continue to authenticate requests and bill to the organization until somebody deletes them individually."),
 ("Why can't I just delete the project instead?",
  "Projects cannot be deleted, only archived. That is why archiving carries so much weight in practice: it is the only closing gesture the API offers, so every kind of ending lands in the same state, and the archived list becomes where the organization's history accumulates along with its credentials."),
 ("What does include_archived actually change?",
  "It changes which projects the listing returns. Without it the response omits archived projects entirely, and there is no field or count telling you that anything was omitted. That is why an audit missing the parameter reports a clean result rather than an incomplete one."),
 ("How do I know whether an archived project is still doing work?",
  "Compare each key's last_used_at against the project's archived_at. A key used after the archive date means something is still calling the API through that project. Confirm it in money with GET /v1/organization/costs?start_time=<now-30d>&group_by=project_id, which shows a non-zero amount for an archived project_id that is still spending."),
 ("Does this need an admin key?",
  "Yes. Both the projects listing and the project API keys listing live under /v1/organization/, which rejects project keys with a 401. Use an organization admin key with read scopes only. Admin describes what it can see; this script only reads."),
],
"related": [
 ("/llm/key-owner-lost-project-access/", "Keys whose owner has lost project access"),
 ("/llm/prompt-caching-never-used/", "Prompt caching that was never switched on"),
 ("/llm/cache-writes-with-no-reads/", "Cache writes that are never read back"),
],
"citations": [CITE_PROJECTS, CITE_PROJECT_KEYS, CITE_ADMIN_APIS, CITE_AUDIT_LOGS],
},

{
"slug": "prompt-caching-never-used",
"title": "Prompt caching was never switched on anywhere",
"description": "cache_read_input_tokens is flat zero across every bucket while uncached input climbs. Caching is opt-in, and nothing tells you it is off.",
"h1": "prompt caching was never switched on anywhere",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic prompt caching not working", "cache_read_input_tokens zero",
             "claude cache_control ephemeral", "anthropic usage report caching",
             "claude prompt caching cost"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The system prompt is four thousand tokens of instructions, a tool catalogue and two worked examples. It is identical on every call, and there are three hundred thousand calls a month. It has been reprocessed at the full input rate every single time, because prompt caching is opt-in and nobody opted in. There is no error to find, no warning header, and no line in the invoice that says what this cost. There is only a field in the usage report that has been zero since the day the integration shipped.",
"short_answer": """<p>With an <strong>Admin API key</strong>, read <code>GET /v1/organizations/usage_report/messages?starting_at={T-30d}&amp;bucket_width=1d&amp;limit=31&amp;group_by[]=model&amp;group_by[]=workspace_id</code>. Sum <code>cache_read_input_tokens</code> and both <code>cache_creation.ephemeral_5m_input_tokens</code> and <code>cache_creation.ephemeral_1h_input_tokens</code> across every result on every page.</p>
<p>If all three sums are zero while <code>uncached_input_tokens</code> is large, caching is not switched on anywhere in the organization. Confirm from the money side with <code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;group_by[]=description</code>: no result will carry a <code>token_type</code> of <code>cache_read_input_tokens</code>.</p>
<p>This is the <em>never switched on</em> half of a pair. If cache writes are non-zero and reads are still zero, caching <em>is</em> on and is costing you extra rather than saving you anything &mdash; that is <a href="/llm/cache-writes-with-no-reads/">cache writes with no reads</a>, and it is a worse position than this one.</p>""",
"problem": """<p>A cache read is billed at 0.1x the base input rate. On a workload with a stable prefix &mdash; a long system prompt, a tool catalogue, a document the user is asking questions about, a conversation history that only grows at the end &mdash; that prefix is the majority of the input on every call, and it is being paid for at full price on every call. The gap between the two numbers does not appear anywhere as a loss, because it is a discount not taken rather than a charge incurred.</p>
<p>What makes it persist is that nothing in the system has an opinion about it. Sending a request without <code>cache_control</code> is not an error, not a warning, not a header, not a deprecation notice. The response looks identical. The latency is worse, but only by an amount that reads as normal variance. The invoice is larger, but it is larger than a counterfactual nobody computed. The integration works perfectly and has always worked perfectly, which is exactly why it never gets revisited.</p>
<p>It also tends to be organization-wide rather than local. Caching is a decision someone makes once, when they are reading the docs closely, and then applies everywhere. If the first integration shipped without it, the second one was copied from the first.</p>""",
"why": """<p><strong>Caching is opt-in and the opt-in is a single field.</strong> Without a <code>cache_control: {"type": "ephemeral"}</code> breakpoint &mdash; at the top level of <code>messages.create()</code>, or on a specific content block &mdash; every request reprocesses the entire prefix from scratch. There is no account setting, no default-on, and no nudge.</p>
<p><strong>Nothing surfaces the absence.</strong> The response carries <code>usage.cache_read_input_tokens: 0</code>, which is indistinguishable from a cache miss and which almost no client logs. The API cannot tell you that a prefix <em>would have been</em> cacheable, because it never saw you ask.</p>
<p><strong>The saving is invisible by construction.</strong> Costs that were avoided do not appear on invoices. You can only see this by computing what the same tokens would have cost at the read rate, which is a calculation nobody runs unprompted.</p>
<p><strong>The usage report has no request count, so you must reason in tokens.</strong> <code>GET /v1/organizations/usage_report/messages</code> returns token sums per bucket and nothing else &mdash; there is no field giving the number of calls. Any statement about "per request" behaviour on the Anthropic side is derived from token totals, not counted, and this note is careful to claim only what the token sums support.</p>
<p><strong>The nesting hides the write fields from a careless parser.</strong> <code>cache_creation</code> is an object containing <code>ephemeral_5m_input_tokens</code> and <code>ephemeral_1h_input_tokens</code>. A script that looks for a flat <code>cache_creation_input_tokens</code> gets nothing back and reports "no caching anywhere" on an organization that caches heavily.</p>""",
"steps": [
 {"h": "Get an Admin API key",
  "body": """<p><code>/v1/organizations/*</code> needs an Admin API key (<code>sk-ant-admin...</code>); a workspace key is rejected by every path under it. Admin keys can be provisioned read-only, and read-only is all this check wants. Send it as <code>x-api-key</code> with <code>anthropic-version: 2023-06-01</code>.</p>"""},
 {"h": "Pull thirty days of daily buckets",
  "body": """<p><code>starting_at</code> has to sit on a bucket boundary, so floor it to midnight UTC. Group by <code>model</code> and <code>workspace_id</code> so the answer is per workload rather than one organization-wide number that a single cached service could mask.</p>"""},
 {"h": "Sum all four token fields, including the nested ones",
  "body": """<p><code>uncached_input_tokens</code>, <code>cache_read_input_tokens</code>, and both members of the <code>cache_creation</code> object. Follow <code>has_more</code> and <code>next_page</code> to the end; a partial page set is how a real cache read gets missed.</p>"""},
 {"h": "Read the two zeros differently",
  "body": """<p>Reads zero <em>and</em> writes zero means caching was never switched on: this note. Reads zero and writes non-zero means it is switched on and paying nothing back, which is the sibling note and is strictly worse, because a write costs 1.25x or 2x base input while an uncached call costs 1x.</p>"""},
 {"h": "Turn it on for the largest workload first, then re-read",
  "body": """<p>Add a <code>cache_control</code> breakpoint at the end of the stable prefix on the highest-volume model and workspace pair, with everything variable after it. Deploy, wait a day, and read the same window again: <code>cache_read_input_tokens</code> should be non-zero and climbing. If it is not, the breakpoint is in the wrong place and you have moved from this note to the sibling one.</p>"""},
],
"verify": """<p>Re-run the script after the change has been live for a day. The workload you changed should report <code>in-use</code>.</p>
<pre><code class="language-bash">python3 anthropic_prompt_cache_off.py --days 7
# in-use  claude-sonnet-4-5 / ws_prod  412.8M read token(s) against 9.1M written
# 1 workload(s), 0 with caching switched off</code></pre>""",
"code_intro": "One paginated GET against the Admin API and no writes. It needs an <strong>Admin API key</strong>, which can be provisioned read-only and should be. Two pure functions do the work: the accumulator, because <code>cache_creation</code> is a nested object and reading it flat is how a caching organization gets reported as an uncached one, and the classifier, which keeps “never switched on”, “switched on and never read back” and “not enough traffic to say” as three separate answers instead of one.",
"py_file": "anthropic_prompt_cache_off.py",
"py": '''"""Report an Anthropic organization that never switched prompt caching on.

Read only. GET requests and nothing else against the Admin API, which needs an
Admin API key (sk-ant-admin...); a workspace key is rejected by every
/v1/organizations/* path, and an Admin key can be provisioned read-only. The
repair is printed, never performed: switching caching on is a change to your
own messages.create() call, not something a script should do to you.

Note on what this report can and cannot say: the messages usage report returns
token sums per bucket and carries no request count at all, so nothing here is
expressed per request. Every ratio below is a ratio of tokens.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_prompt_cache_off")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Published multipliers on base input: a cache read is a tenth of the price of
# processing the same tokens uncached.
READ_MULTIPLIER = 0.10


def accumulate(results, into=None):
    """Sum the token fields that matter across usage-report results. Pure.

    cache_creation is a nested object holding ephemeral_5m_input_tokens and
    ephemeral_1h_input_tokens. A parser that looks for a flat field instead sums
    zero and reports a heavily cached organization as an uncached one, which is
    why this is a function with tests rather than four lines in a loop.
    """
    total = {"uncached": 0, "cache_read": 0, "write_5m": 0, "write_1h": 0}
    if into:
        total.update(into)
    for result in results or []:
        total["uncached"] += int(result.get("uncached_input_tokens") or 0)
        total["cache_read"] += int(result.get("cache_read_input_tokens") or 0)
        creation = result.get("cache_creation") or {}
        total["write_5m"] += int(creation.get("ephemeral_5m_input_tokens") or 0)
        total["write_1h"] += int(creation.get("ephemeral_1h_input_tokens") or 0)
    return total


def cache_saving_ceiling(uncached_tokens, reusable_fraction):
    """Base-rate tokens you could stop paying for, at best. Pure.

    Deliberately a ceiling and not an estimate: it assumes the given fraction of
    uncached input is a stable prefix that would hit the cache every time, and
    prices that fraction at the read rate instead of the base rate. Real
    integrations do worse. Nothing in the API can tell you what the fraction
    actually is, because the API never returns your prompts.
    """
    if not 0.0 <= reusable_fraction <= 1.0:
        raise ValueError("reusable_fraction must be between 0 and 1")
    return int(max(0, uncached_tokens) * reusable_fraction * (1.0 - READ_MULTIPLIER))


def verdict(total, min_input=1_000_000):
    """Classify one workload's 30 day token totals. Pure.

    Returns (state, detail). The three states that matter are kept apart on
    purpose: caching absent, caching present, and not enough traffic to make
    either claim.
    """
    reads = int(total.get("cache_read", 0))
    writes = int(total.get("write_5m", 0)) + int(total.get("write_1h", 0))
    uncached = int(total.get("uncached", 0))

    if reads > 0:
        return ("in-use",
                "%.1fM read token(s) against %.1fM written. Caching is on here; "
                "whether it earns its keep is the write to read ratio, which is "
                "a separate question." % (reads / 1e6, writes / 1e6))
    if writes > 0:
        return ("writes-only",
                "%.1fM cache write token(s) and not one read. Caching is switched "
                "on and paying nothing back, which costs more than leaving it off: "
                "a write is 1.25x (5m) or 2x (1h) base input, an uncached call is "
                "1x." % (writes / 1e6))
    if uncached < min_input:
        return ("too-little-traffic",
                "only %d uncached input token(s) in the window; too little to "
                "conclude anything" % uncached)
    return ("never-used",
            "%.1fM uncached input token(s), zero cache reads and zero cache "
            "writes. Caching has never been switched on for this workload."
            % (uncached / 1e6))


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def buckets(session, path, params):
    """Walk the paginated usage or cost report."""
    params = dict(params)
    while True:
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days):
    """Floor to midnight UTC, because starting_at must sit on a bucket boundary."""
    now = datetime.datetime.now(datetime.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="days of daily buckets to read")
    ap.add_argument("--min-input", type=int, default=1_000_000,
                    help="uncached input tokens below which no claim is made")
    ap.add_argument("--reusable", type=float, default=0.5,
                    help="fraction of input you believe is a stable prefix, used "
                         "only for the printed ceiling")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    params = {"starting_at": window_start(args.days), "bucket_width": "1d",
              "limit": min(args.days + 1, 31),
              "group_by[]": ["model", "workspace_id"]}

    workloads = {}
    for bucket in buckets(s, "/organizations/usage_report/messages", params):
        for result in bucket.get("results") or []:
            name = (result.get("model") or "all models",
                    result.get("workspace_id") or "default workspace")
            workloads[name] = accumulate([result], workloads.get(name))

    if not workloads:
        log.info("no message usage in the last %d day(s)", args.days)
        return 0

    off = 0
    for name, total in sorted(workloads.items(), key=lambda kv: -kv[1]["uncached"]):
        state, detail = verdict(total, args.min_input)
        line = "%-18s %s / %s  %s" % (state, name[0], name[1], detail)
        if state in ("in-use", "too-little-traffic"):
            log.info(line)
            continue
        off += 1
        log.warning(line)
        if state == "never-used":
            ceiling = cache_saving_ceiling(total["uncached"], args.reusable)
            log.warning("  at %.0f%% reusable prefix that is up to %.1fM base rate "
                        "input token(s) a window you would stop paying for",
                        args.reusable * 100, ceiling / 1e6)
            log.warning("  repair: add cache_control {\\"type\\": \\"ephemeral\\"} at the "
                        "end of the stable prefix, keep everything variable after "
                        "it, redeploy, then re-read this window tomorrow")
        else:
            log.warning("  repair: caching is already on here. Move the breakpoint "
                        "to the end of the stable prefix so entries get read back, "
                        "or remove it: paying to write and never read is worse "
                        "than not caching")

    log.info("%d workload(s), %d with caching switched off", len(workloads), off)
    return 1 if off else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-prompt-cache-off.mjs",
"js": '''/**
 * Report an Anthropic organization that never switched prompt caching on.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path, and an Admin key can be provisioned read-only.
 * The repair is printed, never performed.
 *
 * The messages usage report carries token sums and no request count, so every
 * ratio here is a ratio of tokens, never of calls.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';
const READ_MULTIPLIER = 0.10;

/**
 * Sum the token fields that matter across usage-report results. Pure.
 * cache_creation is a nested object; reading it flat sums zero and reports a
 * heavily cached organization as an uncached one.
 */
export function accumulate(results, into = null) {
  const total = { uncached: 0, cache_read: 0, write_5m: 0, write_1h: 0, ...(into ?? {}) };
  for (const result of results ?? []) {
    total.uncached += Number(result.uncached_input_tokens ?? 0);
    total.cache_read += Number(result.cache_read_input_tokens ?? 0);
    const creation = result.cache_creation ?? {};
    total.write_5m += Number(creation.ephemeral_5m_input_tokens ?? 0);
    total.write_1h += Number(creation.ephemeral_1h_input_tokens ?? 0);
  }
  return total;
}

/**
 * Base-rate tokens you could stop paying for, at best. Pure and deliberately a
 * ceiling: nothing in the API can tell you what fraction of your input is
 * really a stable prefix, because the API never returns your prompts.
 */
export function cacheSavingCeiling(uncachedTokens, reusableFraction) {
  if (!(reusableFraction >= 0 && reusableFraction <= 1)) {
    throw new RangeError('reusableFraction must be between 0 and 1');
  }
  return Math.floor(Math.max(0, uncachedTokens) * reusableFraction * (1 - READ_MULTIPLIER));
}

/** Classify one workload's token totals. Pure. */
export function verdict(total, minInput = 1_000_000) {
  const reads = Number(total.cache_read ?? 0);
  const writes = Number(total.write_5m ?? 0) + Number(total.write_1h ?? 0);
  const uncached = Number(total.uncached ?? 0);

  if (reads > 0) {
    return ['in-use',
      `${(reads / 1e6).toFixed(1)}M read token(s) against ${(writes / 1e6).toFixed(1)}M ` +
      'written. Caching is on here; whether it earns its keep is the write to ' +
      'read ratio, which is a separate question.'];
  }
  if (writes > 0) {
    return ['writes-only',
      `${(writes / 1e6).toFixed(1)}M cache write token(s) and not one read. Caching ` +
      'is switched on and paying nothing back, which costs more than leaving it ' +
      'off: a write is 1.25x (5m) or 2x (1h) base input, an uncached call is 1x.'];
  }
  if (uncached < minInput) {
    return ['too-little-traffic',
      `only ${uncached} uncached input token(s) in the window; too little to ` +
      'conclude anything'];
  }
  return ['never-used',
    `${(uncached / 1e6).toFixed(1)}M uncached input token(s), zero cache reads and ` +
    'zero cache writes. Caching has never been switched on for this workload.'];
}

async function get(adminKey, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, one);
  }
  const res = await fetch(url, {
    headers: { 'x-api-key': adminKey, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs an ` +
                    'Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* buckets(adminKey, path, params) {
  const q = { ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

/** Floor to midnight UTC: starting_at must sit on a bucket boundary. */
export function windowStart(days, now = new Date()) {
  const midnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return new Date(midnight - days * 86400000).toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const adminKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!adminKey) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 30);
  const minInput = Number(process.env.MIN_INPUT ?? 1_000_000);
  const reusable = Number(process.env.REUSABLE ?? 0.5);

  const params = {
    starting_at: windowStart(days),
    bucket_width: '1d',
    limit: Math.min(days + 1, 31),
    'group_by[]': ['model', 'workspace_id'],
  };

  const workloads = new Map();
  for await (const bucket of buckets(adminKey, '/organizations/usage_report/messages',
                                     params)) {
    for (const result of bucket.results ?? []) {
      const name = `${result.model ?? 'all models'} / ` +
                   `${result.workspace_id ?? 'default workspace'}`;
      workloads.set(name, accumulate([result], workloads.get(name)));
    }
  }

  if (workloads.size === 0) {
    console.log(`no message usage in the last ${days} day(s)`);
    return;
  }

  let off = 0;
  const ordered = [...workloads.entries()].sort((a, b) => b[1].uncached - a[1].uncached);
  for (const [name, total] of ordered) {
    const [state, detail] = verdict(total, minInput);
    const line = `${state.padEnd(18)} ${name}  ${detail}`;
    if (state === 'in-use' || state === 'too-little-traffic') { console.log(line); continue; }
    off += 1;
    console.warn(line);
    if (state === 'never-used') {
      const ceiling = cacheSavingCeiling(total.uncached, reusable);
      console.warn(`  at ${(reusable * 100).toFixed(0)}% reusable prefix that is up to ` +
                   `${(ceiling / 1e6).toFixed(1)}M base rate input token(s) a window ` +
                   'you would stop paying for');
      console.warn('  repair: add cache_control {"type": "ephemeral"} at the end of ' +
                   'the stable prefix, keep everything variable after it, redeploy, ' +
                   'then re-read this window tomorrow');
    } else {
      console.warn('  repair: caching is already on here. Move the breakpoint to the ' +
                   'end of the stable prefix so entries get read back, or remove it: ' +
                   'paying to write and never read is worse than not caching');
    }
  }

  console.log(`${workloads.size} workload(s), ${off} with caching switched off`);
  process.exitCode = off ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The accumulator gets its own tests because the write fields are nested one level down, and a parser that misses them turns a caching organization into a false finding of this exact note. The classifier gets tests for the boundary that separates this note from its sibling: writes present with no reads is not “caching off”, it is caching on and losing money, and collapsing the two is how a reader is told to switch on something that is already switched on.",
"test_py_file": "test_anthropic_prompt_cache_off.py",
"test_py": '''import pytest

from anthropic_prompt_cache_off import accumulate, cache_saving_ceiling, verdict


def test_accumulate_reads_the_nested_cache_creation_object():
    # The trap: these two fields live inside cache_creation, not at the top.
    total = accumulate([{
        "uncached_input_tokens": 100,
        "cache_read_input_tokens": 40,
        "cache_creation": {"ephemeral_5m_input_tokens": 7,
                           "ephemeral_1h_input_tokens": 3},
    }])
    assert total == {"uncached": 100, "cache_read": 40, "write_5m": 7, "write_1h": 3}


def test_accumulate_treats_absent_and_null_fields_as_zero():
    assert accumulate([{"uncached_input_tokens": None}])["uncached"] == 0
    assert accumulate([{}])["write_5m"] == 0
    assert accumulate(None)["cache_read"] == 0


def test_accumulate_adds_into_a_running_total():
    first = accumulate([{"uncached_input_tokens": 10}])
    second = accumulate([{"uncached_input_tokens": 5}], first)
    assert second["uncached"] == 15


def test_zero_reads_and_zero_writes_on_real_traffic_is_the_finding():
    state, detail = verdict({"uncached": 50_000_000, "cache_read": 0,
                             "write_5m": 0, "write_1h": 0})
    assert state == "never-used"
    assert "never been switched on" in detail


def test_writes_without_reads_is_the_other_note_not_this_one():
    state, detail = verdict({"uncached": 50_000_000, "cache_read": 0,
                             "write_5m": 4_000_000, "write_1h": 0})
    assert state == "writes-only"
    assert "worse" in detail or "more than leaving it off" in detail


def test_any_read_at_all_means_caching_is_on():
    assert verdict({"uncached": 5_000_000, "cache_read": 1, "write_5m": 0,
                    "write_1h": 0})[0] == "in-use"


def test_a_quiet_workload_makes_no_claim_either_way():
    state, _ = verdict({"uncached": 900, "cache_read": 0, "write_5m": 0, "write_1h": 0})
    assert state == "too-little-traffic"


def test_the_saving_ceiling_prices_the_reusable_share_at_the_read_rate():
    # 0.1x read rate, so 90% of the reusable share stops being paid for.
    assert cache_saving_ceiling(1_000_000, 1.0) == 900_000
    assert cache_saving_ceiling(1_000_000, 0.5) == 450_000
    assert cache_saving_ceiling(1_000_000, 0.0) == 0


def test_the_ceiling_refuses_a_fraction_that_is_not_a_fraction():
    with pytest.raises(ValueError):
        cache_saving_ceiling(1_000_000, 1.4)
''',
"test_js_file": "anthropic-prompt-cache-off.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accumulate, cacheSavingCeiling, verdict, windowStart,
} from './anthropic-prompt-cache-off.mjs';

test('accumulate reads the nested cache_creation object', () => {
  const total = accumulate([{
    uncached_input_tokens: 100,
    cache_read_input_tokens: 40,
    cache_creation: { ephemeral_5m_input_tokens: 7, ephemeral_1h_input_tokens: 3 },
  }]);
  assert.deepEqual(total, { uncached: 100, cache_read: 40, write_5m: 7, write_1h: 3 });
});

test('accumulate treats absent and null fields as zero', () => {
  assert.equal(accumulate([{ uncached_input_tokens: null }]).uncached, 0);
  assert.equal(accumulate([{}]).write_5m, 0);
  assert.equal(accumulate(null).cache_read, 0);
});

test('accumulate adds into a running total', () => {
  const first = accumulate([{ uncached_input_tokens: 10 }]);
  assert.equal(accumulate([{ uncached_input_tokens: 5 }], first).uncached, 15);
});

test('zero reads and zero writes on real traffic is the finding', () => {
  const [state, detail] = verdict({
    uncached: 50_000_000, cache_read: 0, write_5m: 0, write_1h: 0,
  });
  assert.equal(state, 'never-used');
  assert.match(detail, /never been switched on/);
});

test('writes without reads is the other note not this one', () => {
  const [state, detail] = verdict({
    uncached: 50_000_000, cache_read: 0, write_5m: 4_000_000, write_1h: 0,
  });
  assert.equal(state, 'writes-only');
  assert.match(detail, /more than leaving it off/);
});

test('any read at all means caching is on', () => {
  assert.equal(verdict({ uncached: 5_000_000, cache_read: 1, write_5m: 0, write_1h: 0 })[0],
               'in-use');
});

test('a quiet workload makes no claim either way', () => {
  assert.equal(verdict({ uncached: 900, cache_read: 0, write_5m: 0, write_1h: 0 })[0],
               'too-little-traffic');
});

test('the saving ceiling prices the reusable share at the read rate', () => {
  assert.equal(cacheSavingCeiling(1_000_000, 1.0), 900_000);
  assert.equal(cacheSavingCeiling(1_000_000, 0.5), 450_000);
  assert.equal(cacheSavingCeiling(1_000_000, 0.0), 0);
});

test('the ceiling refuses a fraction that is not a fraction', () => {
  assert.throws(() => cacheSavingCeiling(1_000_000, 1.4), RangeError);
});

test('the window start is floored to midnight UTC', () => {
  assert.equal(windowStart(7, new Date('2026-08-30T13:45:12Z')), '2026-08-23T00:00:00Z');
});
''',
"faq": [
 ("How much does prompt caching actually save?",
  "A cache read is billed at 0.1x the base input rate, so the cached portion of a request costs a tenth of what it costs uncached. The saving is bounded by how much of your input is genuinely a stable prefix: a four-thousand-token system prompt in front of a two-hundred-token question is nearly all of it, and a workload whose whole prompt changes every call saves nothing because nothing repeats."),
 ("Why is there no warning that caching is off?",
  "Because sending a request without a cache_control breakpoint is a completely valid request. There is no error, no header, no deprecation notice, and the response is identical. The API cannot know that a prefix would have been cacheable, because you never asked it to cache anything."),
 ("Can I tell how many requests were affected?",
  "No. The messages usage report returns token sums per bucket and carries no request-count field at all, so anything phrased per request on the Anthropic side is derived from tokens rather than counted. This script deliberately reports token totals and token ratios only."),
 ("The cache write fields come back as zero. Is my parser wrong?",
  "Possibly. cache_creation is a nested object containing ephemeral_5m_input_tokens and ephemeral_1h_input_tokens, not a flat field. A script reading a top-level cache_creation_input_tokens sums nothing and reports a heavily cached organization as one that has never cached at all, which is the false positive this note is most likely to produce."),
 ("What if reads are zero but writes are not?",
  "Then caching is switched on, entries are being written, and nothing is reading them back. That is the sibling problem and it is worse than this one: a 5m write costs 1.25x base input and a 1h write 2x, against 1x for an uncached call, so you are paying a surcharge for a feature returning nothing. See cache writes with no reads."),
],
"related": [
 ("/llm/cache-writes-with-no-reads/", "Cache writes that are never read back"),
 ("/llm/key-owner-lost-project-access/", "Keys whose owner has lost project access"),
 ("/llm/archived-project-still-holds-keys/", "An archived project still holding live keys"),
],
"citations": [CITE_CACHING, CITE_USAGE_REPORT, CITE_PRICING, CITE_COST_REPORT],
},

{
"slug": "cache-writes-with-no-reads",
"title": "Cache writes are paid for and never read back",
"description": "A cache write costs 1.25x or 2x base input and a read costs 0.1x. When the reads never come, caching costs strictly more than leaving it off.",
"h1": "cache writes are paid for and never read back",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic cache thrash", "cache_creation_input_tokens high",
             "claude prompt cache not hitting", "cache_control breakpoint position",
             "anthropic cache write cost"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Caching was switched on in June and the bill went up. Every call writes a fresh cache entry, is billed 1.25x base input for the privilege, and then nothing ever reads that entry back before it expires. The reason is one line: a request id got templated into the system prompt, ahead of the breakpoint, so no two prefixes have ever been byte-identical. The feature is working exactly as documented and it is costing you money.",
"short_answer": """<p>With an <strong>Admin API key</strong>, read <code>GET /v1/organizations/usage_report/messages?starting_at={T-7d}&amp;bucket_width=1h&amp;limit=168&amp;group_by[]=api_key_id</code>. Per key, sum <code>writes = cache_creation.ephemeral_5m_input_tokens + cache_creation.ephemeral_1h_input_tokens</code> and compare against <code>cache_read_input_tokens</code>.</p>
<p>A read-to-write ratio below 1 is the flag. The exact break-even is computable from the published multipliers: a 5m write costs 1.25x base input and a 1h write 2x, while a read costs 0.1x, so caching starts paying at about 0.28 read tokens per write token for pure 5m traffic and about 1.11 for pure 1h. Below your own mix's break-even you are paying more than you would with caching switched off.</p>
<p>This is the opposite half of a pair. <a href="/llm/prompt-caching-never-used/">Prompt caching never used</a> is caching that was never turned on, where the loss is a discount not taken. This one is caching that <em>is</em> on and is charging you a surcharge, which is the worse of the two.</p>""",
"problem": """<p>Cache thrash is uniquely annoying because every individual part of it is correct. The API caches what you asked it to cache. It bills the documented rate. The entry expires on schedule. Your code is doing what it says. The only thing wrong is that the prefix you are caching is never the same twice, so each write is a payment for a lookup nobody will ever perform.</p>
<p>And it does not look like a regression. Turning caching on is a cost optimisation, so when it lands the assumption is that the number went down; if the number went up, the first explanation reached for is volume. It takes deliberately splitting cache writes from cache reads in the usage report before the shape shows up, and both fields are easy to skim past because they are small next to <code>uncached_input_tokens</code> on a report you were reading for other reasons.</p>
<p>The specific causes are boring, which is why they survive review. A timestamp or a request id rendered into the system prompt. A conversation history assembled in a different order each time. A breakpoint placed after the user's message instead of before it. A cron job that runs every fifteen minutes against a five-minute TTL, so every entry has expired by the time the next call arrives.</p>""",
"why": """<p><strong>Writing costs more than not caching.</strong> 1.25x base input for a 5m entry, 2x for a 1h entry. Caching is a bet that the entry will be read enough times to pay back that premium at 0.1x a read. Lose the bet and you have simply paid a surcharge on every call.</p>
<p><strong>Break-even is arithmetic, not a rule of thumb.</strong> A write of <em>w</em> tokens plus reads of <em>r</em> tokens costs <code>1.25w + 0.1r</code> where the uncached equivalent costs <code>w + r</code>, so caching wins when <code>r &gt; 0.25w / 0.9</code> &mdash; about 0.28 for 5m. For a 1h entry the premium is 1.0 rather than 0.25 and break-even moves to about 1.11. Your real threshold sits between the two, weighted by how your writes split across the two TTLs.</p>
<p><strong>A cache entry needs an exact prefix match.</strong> One byte before the breakpoint that differs between calls &mdash; an id, a clock, a reordered tool list, a differently serialised JSON blob &mdash; and the lookup misses and a fresh entry is written. Nothing reports the miss. It looks like a first call, every time.</p>
<p><strong>TTL and traffic rate have to agree.</strong> A 5-minute entry against traffic that arrives every twenty minutes expires before every read. The 1h TTL fixes that at double the write price, which raises break-even to roughly two reads per write and can turn a small loss into a larger one if the arrival rate does not also improve.</p>
<p><strong>The ratio is tokens, not requests, and it has to be.</strong> The messages usage report has no request-count field &mdash; it returns token sums per bucket and nothing else. Reads per write here means read tokens per write token. It is a good proxy because a read and a write of the same prefix cover roughly the same tokens, but it is a proxy, and no call count exists on this API to check it against.</p>""",
"steps": [
 {"h": "Pull a week of hourly buckets grouped by key",
  "body": """<p><code>GET /v1/organizations/usage_report/messages?starting_at={T-7d}&amp;bucket_width=1h&amp;limit=168&amp;group_by[]=api_key_id</code>, floored to the hour so <code>starting_at</code> lands on a bucket boundary. Grouping by <code>api_key_id</code> matters: one well-tuned service will otherwise average away a thrashing one.</p>"""},
 {"h": "Split writes by TTL rather than summing them",
  "body": """<p><code>cache_creation.ephemeral_5m_input_tokens</code> and <code>cache_creation.ephemeral_1h_input_tokens</code> are priced differently, so the break-even for a key depends on the mix. Keep them apart through the accumulation and let the threshold be computed rather than assumed.</p>"""},
 {"h": "Compute the ratio and the break-even, then compare them",
  "body": """<p>Ratio is <code>cache_read_input_tokens</code> over total write tokens. Break-even is <code>(0.25 &times; write_5m + 1.0 &times; write_1h) / (0.9 &times; total writes)</code>. Below it, the traffic costs more than it would uncached; the effective multiplier tells you by how much.</p>"""},
 {"h": "Confirm it in money",
  "body": """<p><code>GET /v1/organizations/cost_report?starting_at={T-30d}&amp;group_by[]=description</code> and compare the <code>amount</code> on the <code>cache_creation.*</code> rows against the <code>cache_read_input_tokens</code> row. Write spend exceeding read spend is the same finding in currency, which is the version that survives a conversation with whoever owns the budget.</p>"""},
 {"h": "Move the breakpoint, do not remove the feature",
  "body": """<p>Put the <code>cache_control</code> breakpoint at the end of the genuinely stable prefix, and push everything volatile &mdash; timestamps, request ids, the user's question &mdash; strictly after it. Redeploy and re-measure the ratio over the next 24 hours. If the arrival rate is the real problem rather than the prefix, either batch the callers or accept that this workload should not be cached at all.</p>"""},
],
"verify": """<p>Re-run the script a day after moving the breakpoint. The key should report <code>paying-off</code>, with an effective multiplier below 1.</p>
<pre><code class="language-bash">python3 anthropic_cache_write_ratio.py --days 7
# paying-off  apikey_01ab  6.42 read tokens per write token, effective 0.26x base input
# 3 key(s), 0 losing money on caching</code></pre>""",
"code_intro": "One paginated GET against the Admin API and no writes. It needs an <strong>Admin API key</strong>, which can be provisioned read-only and should be. Three pure functions carry the arithmetic: the accumulator that keeps the two TTLs apart, the break-even ratio derived from the published multipliers rather than guessed, and the effective multiplier that says what this traffic costs relative to the same tokens uncached. At exactly break-even the multiplier is 1.0, and the tests pin that identity so the two numbers can never drift apart.",
"py_file": "anthropic_cache_write_ratio.py",
"py": '''"""Report Anthropic cache writes that are never read back.

Read only. GET requests and nothing else against the Admin API, which needs an
Admin API key (sk-ant-admin...); a workspace key is rejected by every
/v1/organizations/* path, and an Admin key can be provisioned read-only. The
repair is printed, never performed: moving a cache_control breakpoint is a
change to your own request, not something a script should do to you.

The messages usage report carries token sums per bucket and no request count at
all, so "reads per write" below means read tokens per write token. It is a
proxy for call counts, not a call count, and this API has no call count to
check it against.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_cache_write_ratio")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Published multipliers on base input.
WRITE_5M = 1.25
WRITE_1H = 2.00
READ = 0.10
BASE = 1.00


def accumulate(results, into=None):
    """Sum token fields across usage-report results, keeping the TTLs apart. Pure.

    The two cache_creation members are priced differently, so summing them here
    would throw away the information the break-even calculation needs. They live
    inside a nested cache_creation object, which is the field a flat parser
    misses entirely.
    """
    total = {"uncached": 0, "cache_read": 0, "write_5m": 0, "write_1h": 0}
    if into:
        total.update(into)
    for result in results or []:
        total["uncached"] += int(result.get("uncached_input_tokens") or 0)
        total["cache_read"] += int(result.get("cache_read_input_tokens") or 0)
        creation = result.get("cache_creation") or {}
        total["write_5m"] += int(creation.get("ephemeral_5m_input_tokens") or 0)
        total["write_1h"] += int(creation.get("ephemeral_1h_input_tokens") or 0)
    return total


def break_even_ratio(write_5m, write_1h):
    """Read tokens per write token at which caching starts to save money. Pure.

    Caching w write tokens and r read tokens costs 1.25*w5 + 2.0*w1h + 0.1*r,
    against w5 + w1h + r for the same tokens uncached. Solving for r gives
    r > ((1.25-1)*w5 + (2.0-1)*w1h) / (1 - 0.1), which is about 0.28 for pure
    5m traffic and about 1.11 for pure 1h. Returns None when nothing was
    written, because a ratio against zero is not a number.
    """
    writes = write_5m + write_1h
    if writes <= 0:
        return None
    premium = (WRITE_5M - BASE) * write_5m + (WRITE_1H - BASE) * write_1h
    return premium / ((BASE - READ) * writes)


def effective_multiplier(write_5m, write_1h, reads):
    """What this cached traffic costs per token relative to not caching. Pure.

    Above 1.0 means the caching is charging you a surcharge: the same tokens
    would have been cheaper with the feature switched off.
    """
    tokens = write_5m + write_1h + reads
    if tokens <= 0:
        return None
    cost = WRITE_5M * write_5m + WRITE_1H * write_1h + READ * reads
    return cost / tokens


def verdict(total, min_writes=100_000, margin=1.5):
    """Classify one key's cache economics over the window. Pure.

    Returns (state, detail). `margin` is how far above break-even a ratio has to
    sit before it is called safe rather than marginal, because a ratio sitting
    on the line will cross it the first week traffic dips.
    """
    reads = int(total.get("cache_read", 0))
    write_5m = int(total.get("write_5m", 0))
    write_1h = int(total.get("write_1h", 0))
    writes = write_5m + write_1h

    if writes == 0 and reads == 0:
        return ("no-caching",
                "no cache reads and no cache writes in this window: caching is "
                "not switched on for this key at all, which is a different "
                "problem from this one")
    if writes == 0:
        return ("reads-only",
                "%d read token(s) against entries written before this window "
                "opened. Widen the window before drawing a ratio from it." % reads)
    if writes < min_writes:
        return ("too-little-traffic",
                "only %d cache write token(s) in the window; too little to draw "
                "a ratio from" % writes)

    ratio = reads / writes
    threshold = break_even_ratio(write_5m, write_1h)
    multiplier = effective_multiplier(write_5m, write_1h, reads)
    shape = ("%.2f read tokens per write token against a break-even of %.2f; "
             "this traffic costs %.2fx what the same tokens would cost with "
             "caching switched off" % (ratio, threshold, multiplier))
    if ratio < threshold:
        return ("losing", shape)
    if ratio < threshold * margin:
        return ("marginal", shape + ", which is barely above the line")
    return ("paying-off", shape)


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: /v1/organizations/* needs an Admin "
                         "API key (sk-ant-admin...), not a workspace key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def buckets(session, path, params):
    params = dict(params)
    while True:
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def window_start(days):
    """Floor to the hour, because starting_at must sit on a bucket boundary."""
    now = datetime.datetime.now(datetime.timezone.utc)
    top = now.replace(minute=0, second=0, microsecond=0)
    return (top - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="days of hourly buckets to read")
    ap.add_argument("--min-writes", type=int, default=100_000,
                    help="cache write tokens below which no ratio is claimed")
    args = ap.parse_args()

    admin = os.environ.get("ANTHROPIC_ADMIN_KEY")
    if not admin:
        log.error("set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); "
                  "a workspace key cannot read /v1/organizations/*")
        return 2

    s = requests.Session()
    s.headers.update({"x-api-key": admin, "anthropic-version": VERSION})

    params = {"starting_at": window_start(args.days), "bucket_width": "1h",
              "limit": min(args.days * 24, 168), "group_by[]": ["api_key_id"]}

    by_key = {}
    for bucket in buckets(s, "/organizations/usage_report/messages", params):
        for result in bucket.get("results") or []:
            name = result.get("api_key_id") or "unattributed"
            by_key[name] = accumulate([result], by_key.get(name))

    if not by_key:
        log.info("no message usage in the last %d day(s)", args.days)
        return 0

    losing = 0
    for name, total in sorted(by_key.items(),
                              key=lambda kv: -(kv[1]["write_5m"] + kv[1]["write_1h"])):
        state, detail = verdict(total, args.min_writes)
        line = "%-18s %s  %s" % (state, name, detail)
        if state in ("paying-off", "too-little-traffic", "reads-only"):
            log.info(line)
            continue
        if state == "no-caching":
            log.info(line)
            continue
        losing += 1
        log.warning(line)
        log.warning("  repair: move the cache_control breakpoint to the end of the "
                    "stable prefix and keep timestamps, request ids and the user's "
                    "question strictly after it, then re-measure this ratio tomorrow")
        if total["write_1h"] > total["write_5m"]:
            log.warning("  note: most writes here are 1h entries at 2x base input, "
                        "so break-even needs about twice the reads a 5m entry does")
        log.warning("  confirm in money: GET %s/organizations/cost_report"
                    "?starting_at=<T-30d>&group_by[]=description", API)

    log.info("%d key(s), %d losing money on caching", len(by_key), losing)
    return 1 if losing else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-cache-write-ratio.mjs",
"js": '''/**
 * Report Anthropic cache writes that are never read back.
 *
 * Read only. GET requests and nothing else against the Admin API, which needs
 * an Admin API key (sk-ant-admin...); a workspace key is rejected by every
 * /v1/organizations/* path, and an Admin key can be provisioned read-only.
 * The repair is printed, never performed.
 *
 * The usage report has no request-count field, so "reads per write" means read
 * tokens per write token: a proxy for call counts, not a call count.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// Published multipliers on base input.
const WRITE_5M = 1.25;
const WRITE_1H = 2.00;
const READ = 0.10;
const BASE = 1.00;

/** Sum token fields across results, keeping the two TTLs apart. Pure. */
export function accumulate(results, into = null) {
  const total = { uncached: 0, cache_read: 0, write_5m: 0, write_1h: 0, ...(into ?? {}) };
  for (const result of results ?? []) {
    total.uncached += Number(result.uncached_input_tokens ?? 0);
    total.cache_read += Number(result.cache_read_input_tokens ?? 0);
    const creation = result.cache_creation ?? {};
    total.write_5m += Number(creation.ephemeral_5m_input_tokens ?? 0);
    total.write_1h += Number(creation.ephemeral_1h_input_tokens ?? 0);
  }
  return total;
}

/**
 * Read tokens per write token at which caching starts to save money. Pure.
 * About 0.28 for pure 5m traffic, about 1.11 for pure 1h. Null when nothing
 * was written, because a ratio against zero is not a number.
 */
export function breakEvenRatio(write5m, write1h) {
  const writes = write5m + write1h;
  if (writes <= 0) return null;
  const premium = (WRITE_5M - BASE) * write5m + (WRITE_1H - BASE) * write1h;
  return premium / ((BASE - READ) * writes);
}

/**
 * What this cached traffic costs per token relative to not caching. Pure.
 * Above 1.0 means caching is charging a surcharge.
 */
export function effectiveMultiplier(write5m, write1h, reads) {
  const tokens = write5m + write1h + reads;
  if (tokens <= 0) return null;
  return (WRITE_5M * write5m + WRITE_1H * write1h + READ * reads) / tokens;
}

/** Classify one key's cache economics over the window. Pure. */
export function verdict(total, minWrites = 100_000, margin = 1.5) {
  const reads = Number(total.cache_read ?? 0);
  const write5m = Number(total.write_5m ?? 0);
  const write1h = Number(total.write_1h ?? 0);
  const writes = write5m + write1h;

  if (writes === 0 && reads === 0) {
    return ['no-caching',
      'no cache reads and no cache writes in this window: caching is not ' +
      'switched on for this key at all, which is a different problem from this one'];
  }
  if (writes === 0) {
    return ['reads-only',
      `${reads} read token(s) against entries written before this window opened. ` +
      'Widen the window before drawing a ratio from it.'];
  }
  if (writes < minWrites) {
    return ['too-little-traffic',
      `only ${writes} cache write token(s) in the window; too little to draw a ratio from`];
  }

  const ratio = reads / writes;
  const threshold = breakEvenRatio(write5m, write1h);
  const multiplier = effectiveMultiplier(write5m, write1h, reads);
  const shape = `${ratio.toFixed(2)} read tokens per write token against a ` +
    `break-even of ${threshold.toFixed(2)}; this traffic costs ` +
    `${multiplier.toFixed(2)}x what the same tokens would cost with caching switched off`;
  if (ratio < threshold) return ['losing', shape];
  if (ratio < threshold * margin) return ['marginal', `${shape}, which is barely above the line`];
  return ['paying-off', shape];
}

async function get(adminKey, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, one);
  }
  const res = await fetch(url, {
    headers: { 'x-api-key': adminKey, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: /v1/organizations/* needs an ` +
                    'Admin API key (sk-ant-admin...), not a workspace key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* buckets(adminKey, path, params) {
  const q = { ...params };
  for (;;) {
    const page = await get(adminKey, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

/** Floor to the hour: starting_at must sit on a bucket boundary. */
export function windowStart(days, now = new Date()) {
  const top = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
                       now.getUTCHours());
  return new Date(top - days * 86400000).toISOString().replace(/\\.\\d{3}Z$/, 'Z');
}

async function main() {
  const adminKey = process.env.ANTHROPIC_ADMIN_KEY;
  if (!adminKey) {
    console.error('set ANTHROPIC_ADMIN_KEY to an Admin API key (sk-ant-admin...); ' +
                  'a workspace key cannot read /v1/organizations/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 7);
  const minWrites = Number(process.env.MIN_WRITES ?? 100_000);

  const params = {
    starting_at: windowStart(days),
    bucket_width: '1h',
    limit: Math.min(days * 24, 168),
    'group_by[]': ['api_key_id'],
  };

  const byKey = new Map();
  for await (const bucket of buckets(adminKey, '/organizations/usage_report/messages',
                                     params)) {
    for (const result of bucket.results ?? []) {
      const name = result.api_key_id ?? 'unattributed';
      byKey.set(name, accumulate([result], byKey.get(name)));
    }
  }

  if (byKey.size === 0) {
    console.log(`no message usage in the last ${days} day(s)`);
    return;
  }

  let losing = 0;
  const ordered = [...byKey.entries()].sort(
    (a, b) => (b[1].write_5m + b[1].write_1h) - (a[1].write_5m + a[1].write_1h));
  for (const [name, total] of ordered) {
    const [state, detail] = verdict(total, minWrites);
    const line = `${state.padEnd(18)} ${name}  ${detail}`;
    if (state !== 'losing' && state !== 'marginal') { console.log(line); continue; }
    losing += 1;
    console.warn(line);
    console.warn('  repair: move the cache_control breakpoint to the end of the stable ' +
                 "prefix and keep timestamps, request ids and the user's question " +
                 'strictly after it, then re-measure this ratio tomorrow');
    if (total.write_1h > total.write_5m) {
      console.warn('  note: most writes here are 1h entries at 2x base input, so ' +
                   'break-even needs about twice the reads a 5m entry does');
    }
    console.warn(`  confirm in money: GET ${API}/organizations/cost_report` +
                 '?starting_at=<T-30d>&group_by[]=description');
  }

  console.log(`${byKey.size} key(s), ${losing} losing money on caching`);
  process.exitCode = losing ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The identity worth pinning is that a ratio exactly at break-even produces an effective multiplier of exactly 1.0. Those two functions are derived from the same three multipliers, and a test that ties them together is what stops a later edit from moving one threshold without the other and quietly turning a losing workload into a passing one. The rest of the tests keep this note's finding distinct from its sibling's: no writes and no reads is not a bad ratio, it is caching that was never switched on.",
"test_py_file": "test_anthropic_cache_write_ratio.py",
"test_py": '''from anthropic_cache_write_ratio import (
    accumulate, break_even_ratio, effective_multiplier, verdict,
)


def test_accumulate_keeps_the_two_ttls_apart():
    # Summing them would destroy the information break-even needs.
    total = accumulate([{
        "cache_read_input_tokens": 5,
        "cache_creation": {"ephemeral_5m_input_tokens": 100,
                           "ephemeral_1h_input_tokens": 20},
    }])
    assert total["write_5m"] == 100
    assert total["write_1h"] == 20
    assert total["cache_read"] == 5


def test_break_even_for_pure_5m_writes():
    # (1.25 - 1) / (1 - 0.1)
    assert round(break_even_ratio(1000, 0), 4) == 0.2778


def test_break_even_for_pure_1h_writes_is_about_four_times_higher():
    # (2.0 - 1) / (1 - 0.1)
    assert round(break_even_ratio(0, 1000), 4) == 1.1111


def test_break_even_of_nothing_written_is_none_not_zero():
    assert break_even_ratio(0, 0) is None


def test_at_break_even_the_effective_multiplier_is_exactly_one():
    # The identity that keeps the two functions from drifting apart.
    for w5, w1h in ((1000, 0), (0, 1000), (600, 400)):
        reads = break_even_ratio(w5, w1h) * (w5 + w1h)
        assert round(effective_multiplier(w5, w1h, reads), 6) == 1.0


def test_writes_with_no_reads_cost_more_than_not_caching():
    assert effective_multiplier(1000, 0, 0) == 1.25
    assert effective_multiplier(0, 1000, 0) == 2.0


def test_a_key_that_writes_and_never_reads_is_losing():
    state, detail = verdict({"cache_read": 0, "write_5m": 5_000_000, "write_1h": 0})
    assert state == "losing"
    assert "1.25x" in detail


def test_a_key_reading_back_many_times_is_paying_off():
    state, _ = verdict({"cache_read": 50_000_000, "write_5m": 5_000_000, "write_1h": 0})
    assert state == "paying-off"


def test_just_above_break_even_is_marginal_not_safe():
    writes = 5_000_000
    reads = int(break_even_ratio(writes, 0) * writes * 1.1)
    assert verdict({"cache_read": reads, "write_5m": writes, "write_1h": 0})[0] == "marginal"


def test_no_writes_and_no_reads_is_the_other_note():
    state, detail = verdict({"cache_read": 0, "write_5m": 0, "write_1h": 0})
    assert state == "no-caching"
    assert "different problem" in detail


def test_reads_with_no_writes_in_the_window_is_not_a_ratio():
    state, detail = verdict({"cache_read": 9_000_000, "write_5m": 0, "write_1h": 0})
    assert state == "reads-only"
    assert "Widen the window" in detail


def test_a_trickle_of_writes_makes_no_claim():
    assert verdict({"cache_read": 0, "write_5m": 10, "write_1h": 0})[0] == "too-little-traffic"
''',
"test_js_file": "anthropic-cache-write-ratio.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accumulate, breakEvenRatio, effectiveMultiplier, verdict, windowStart,
} from './anthropic-cache-write-ratio.mjs';

test('accumulate keeps the two TTLs apart', () => {
  const total = accumulate([{
    cache_read_input_tokens: 5,
    cache_creation: { ephemeral_5m_input_tokens: 100, ephemeral_1h_input_tokens: 20 },
  }]);
  assert.equal(total.write_5m, 100);
  assert.equal(total.write_1h, 20);
  assert.equal(total.cache_read, 5);
});

test('break-even for pure 5m writes', () => {
  assert.equal(Number(breakEvenRatio(1000, 0).toFixed(4)), 0.2778);
});

test('break-even for pure 1h writes is about four times higher', () => {
  assert.equal(Number(breakEvenRatio(0, 1000).toFixed(4)), 1.1111);
});

test('break-even of nothing written is null not zero', () => {
  assert.equal(breakEvenRatio(0, 0), null);
});

test('at break-even the effective multiplier is exactly one', () => {
  for (const [w5, w1h] of [[1000, 0], [0, 1000], [600, 400]]) {
    const reads = breakEvenRatio(w5, w1h) * (w5 + w1h);
    assert.equal(Number(effectiveMultiplier(w5, w1h, reads).toFixed(6)), 1);
  }
});

test('writes with no reads cost more than not caching', () => {
  assert.equal(effectiveMultiplier(1000, 0, 0), 1.25);
  assert.equal(effectiveMultiplier(0, 1000, 0), 2.0);
});

test('a key that writes and never reads is losing', () => {
  const [state, detail] = verdict({ cache_read: 0, write_5m: 5_000_000, write_1h: 0 });
  assert.equal(state, 'losing');
  assert.match(detail, /1\\.25x/);
});

test('a key reading back many times is paying off', () => {
  assert.equal(
    verdict({ cache_read: 50_000_000, write_5m: 5_000_000, write_1h: 0 })[0],
    'paying-off');
});

test('just above break-even is marginal not safe', () => {
  const writes = 5_000_000;
  const reads = Math.floor(breakEvenRatio(writes, 0) * writes * 1.1);
  assert.equal(verdict({ cache_read: reads, write_5m: writes, write_1h: 0 })[0],
               'marginal');
});

test('no writes and no reads is the other note', () => {
  const [state, detail] = verdict({ cache_read: 0, write_5m: 0, write_1h: 0 });
  assert.equal(state, 'no-caching');
  assert.match(detail, /different problem/);
});

test('reads with no writes in the window is not a ratio', () => {
  const [state, detail] = verdict({ cache_read: 9_000_000, write_5m: 0, write_1h: 0 });
  assert.equal(state, 'reads-only');
  assert.match(detail, /Widen the window/);
});

test('a trickle of writes makes no claim', () => {
  assert.equal(verdict({ cache_read: 0, write_5m: 10, write_1h: 0 })[0],
               'too-little-traffic');
});

test('the window start is floored to the hour', () => {
  assert.equal(windowStart(7, new Date('2026-08-30T13:45:12Z')), '2026-08-23T13:00:00Z');
});
''',
"faq": [
 ("How is caching more expensive than not caching?",
  "Because a write is billed above the base input rate. A 5-minute cache write costs 1.25x base input and a 1-hour write costs 2x, while an uncached request pays 1x. Caching is a bet that reads at 0.1x will repay that premium. If nothing ever reads the entry, you have paid 1.25x or 2x for every call and received nothing back."),
 ("What ratio should I be aiming for?",
  "Above your own break-even, which depends on your TTL mix: about 0.28 read tokens per write token for pure 5m traffic and about 1.11 for pure 1h. A healthy cached workload is usually far above either, often several reads per write, because the whole point is a prefix reused many times before it expires."),
 ("Why do my cache reads stay at zero when caching is clearly on?",
  "A cache hit needs an exact prefix match up to the breakpoint. Anything varying before it, a timestamp, a request id, a reordered tool list, differently serialised JSON, produces a miss and a fresh write. It is also possible the traffic simply arrives slower than the TTL, so every entry has expired before the next call. Neither case produces an error or a header."),
 ("Is this the same as prompt caching never being used?",
  "No, and the difference matters. Caching never used means no writes and no reads at all: the cost is a discount you are not taking. This note is caching that is switched on and being paid for without ever paying back, which is strictly worse, because you are paying a write premium on top of the base rate rather than just the base rate."),
 ("Can the API tell me reads per request rather than per token?",
  "No. The messages usage report returns token sums per bucket and carries no request-count field, so there is no call volume on this endpoint to divide by. Read tokens per write token is the closest available measure, and it is a good proxy because a read and a write of the same prefix cover roughly the same tokens."),
],
"related": [
 ("/llm/prompt-caching-never-used/", "Prompt caching that was never switched on"),
 ("/llm/key-owner-lost-project-access/", "Keys whose owner has lost project access"),
 ("/llm/archived-project-still-holds-keys/", "An archived project still holding live keys"),
],
"citations": [CITE_CACHING, CITE_PRICING, CITE_USAGE_REPORT, CITE_COST_REPORT],
},

]
