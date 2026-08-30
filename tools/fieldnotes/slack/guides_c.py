#!/usr/bin/env python3
"""/slack/ field notes, batch C — the writing.

Four notes about things Slack will not tell you unless you ask a very specific
question. An installation row that cannot represent the org it was installed
into; a method that has been dead since November 2025 and answers every call the
same way; a field that is absent rather than wrong; and an app that has gone
quiet in a workspace that is still talking to it.

Each one uses a different read: a sweep of auth.test across every stored token,
a single probe read for its error code, a census of a field across users.list,
and the distance between two timestamps in conversations.history.

Read-only throughout. These scripts hold tokens that can post into a workspace,
so none of them writes: every one reports what it found and prints the repair
for a human to run. Where the evidence is genuinely not in the Web API, the note
says so instead of inventing a detection.
"""

CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_INSTALL = ("Installing with OAuth — Slack Docs",
                "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_GRID = ("Enterprise Grid and org-wide apps — Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")
CITE_ADMIN_TEAMS = ("admin.teams.list method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/admin.teams.list")
CITE_TOKENS = ("Token types — Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_FILES_UPLOAD = ("files.upload method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/files.upload")
CITE_GET_UPLOAD_URL = ("files.getUploadURLExternal method reference — Slack Docs",
                       "https://docs.slack.dev/reference/methods/files.getUploadURLExternal")
CITE_COMPLETE_UPLOAD = ("files.completeUploadExternal method reference — Slack Docs",
                        "https://docs.slack.dev/reference/methods/files.completeUploadExternal")
CITE_UPLOAD_CHANGELOG = ("A better way to upload files is here to stay — Slack changelog",
                         "https://docs.slack.dev/changelog/2024-04-a-better-way-to-upload-files-is-here-to-stay/")
CITE_FILES_LIST = ("files.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.list")
CITE_USERS_LIST = ("users.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")
CITE_USERS_LOOKUP = ("users.lookupByEmail method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/users.lookupByEmail")
CITE_EVENTS = ("The Events API — Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_HISTORY = ("conversations.history method reference — Slack Docs",
                "https://docs.slack.dev/reference/methods/conversations.history")
CITE_APP_MENTION = ("The app_mention event — Slack Docs",
                    "https://docs.slack.dev/reference/events/app_mention")
CITE_MANIFEST = ("apps.manifest.export method reference — Slack Docs",
                 "https://docs.slack.dev/reference/methods/apps.manifest.export")

GUIDES = [

{
"slug": "enterprise-id-not-stored",
"title": "Installs keyed on team_id alone collide on Enterprise Grid",
"description": "On Grid an install is identified by enterprise_id, team_id and is_enterprise_install. A store keyed on team_id alone hands one tenant another's token.",
"h1": "installs keyed on team_id alone collide on Enterprise Grid",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack enterprise_id installation store", "bolt installationstore grid",
             "is_enterprise_install team_id null", "slack org wide app install key",
             "slack multi tenant token leak"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Two customers file the same ticket in the same week: messages from their Slack app are arriving in a channel that belongs to somebody else. Both are on the same Enterprise Grid organisation. Your installation store has one row per <code>team_id</code>, it has always had one row per <code>team_id</code>, and on a single-workspace customer that was correct. On Grid it is a cross-tenant data leak with a green dashboard.",
"short_answer": """<p>Take every row in your installation store, call <code>auth.test</code> with that row's token, and compare what comes back &mdash; <code>enterprise_id</code>, <code>team_id</code>, <code>is_enterprise_install</code> &mdash; against the key you filed it under. A row that does not round-trip is a live risk, not a tidiness problem.</p>
<p>Three findings, in order of seriousness: two rows with the same <code>team_id</code> under different <code>enterprise_id</code> values, a row where <code>is_enterprise_install</code> is <code>true</code> but the key is a workspace id, and a row where <code>enterprise_id</code> was never persisted at all. The repair is to re-key on the triple <code>(enterprise_id, team_id, is_enterprise_install)</code> and to re-run <code>auth.test</code> per token to backfill.</p>""",
"problem": """<p>An installation store written for a single workspace has an obvious key: the workspace. <code>team_id</code> is unique, it is in every event payload, and it is the value Slack hands you in the OAuth response. Nothing in the API pushes back, nothing in the SDK complains, and for every non-Grid customer the design is correct for as long as they stay non-Grid.</p>
<p>Enterprise Grid changes the identity without changing the shape of the payload. An org contains many workspaces. An app can be installed into one workspace, into several, or org-wide across all of them &mdash; and an org-wide installation's <code>team_id</code> may be <code>null</code>, because it is not scoped to a workspace at all. The install is identified by <code>enterprise_id</code> together with <code>team_id</code> and the <code>is_enterprise_install</code> flag; any one of the three on its own is ambiguous.</p>
<p>What makes this different from every other note in this section is the failure mode. Most Slack bugs end in an absence: a message that was never posted, a page that was never read. This one ends in a presence. A lookup keyed on <code>team_id</code> finds <em>a</em> row, that row holds <em>a</em> valid token, the call succeeds with <code>ok: true</code>, and one customer's data is written into another customer's workspace. There is no error to catch, and the tenant on the receiving end is the one who reports it.</p>""",
"why": """<p><strong>The install identity is a triple, not a scalar.</strong> <code>(enterprise_id, team_id, is_enterprise_install)</code> is what Bolt's <code>InstallationQuery</code> passes to <code>fetchInstallation</code>, in both the JS and Python SDKs, and it is passed as three fields precisely because no subset of it is sufficient.</p>
<p><strong>An org-wide install cannot be filed under a workspace.</strong> When <code>is_enterprise_install</code> is <code>true</code> the grant covers every workspace in the org, present and future. Storing it under one <code>team_id</code> means the other workspaces either find nothing or, worse, find a row written by a different install and use its token.</p>
<p><strong>Lookup needs a fallback, not just a key.</strong> An event arriving from workspace <code>T2</code> inside org <code>E1</code> should prefer an exact <code>(E1, T2)</code> row and fall back to the org-wide <code>(E1, null, true)</code> row. A store that only does exact matching will silently drop events for workspaces that are covered by an org-wide grant.</p>
<p><strong>A non-Grid customer can become a Grid customer overnight.</strong> Workspace-to-org migration is an admin action you never see. The API's warning shot is <code>team_added_to_org</code> on calls made mid-migration; your store finds out when the ids it has stop meaning what they meant.</p>
<p><strong>Deleting is as dangerous as reading.</strong> A <code>deleteInstallation</code> implemented on <code>team_id</code> alone will, on an uninstall from one workspace, remove the row another tenant is using. The audit below is read-only for exactly this reason: the repair is a migration a human should run deliberately.</p>""",
"steps": [
 {"h": "Export the store as rows, keys included",
  "body": """<p>The script takes a JSON array of the rows as you actually hold them: the key you filed each install under, whatever you persisted about it, and the environment variable holding that row's token. Do not normalise the export &mdash; the whole audit is a comparison between what you stored and what Slack says, so a helpfully cleaned-up export destroys the finding.</p>"""},
 {"h": "Ask each token who it is",
  "body": """<p><code>auth.test</code> is the only method that answers this. For a Grid install it returns <code>enterprise_id</code> and <code>enterprise_name</code> alongside <code>team_id</code>, plus <code>is_enterprise_install</code>. It needs no scopes, it is a GET, and it is the ground truth for the row that supplied the token.</p>"""},
 {"h": "Check that every row round-trips",
  "body": """<p>A row round-trips when the key you would compute from the live <code>auth.test</code> answer is the key the row is filed under. Anything else &mdash; a dropped <code>enterprise_id</code>, an org-wide install under a workspace key, a key that names a different team than the token does &mdash; means a lookup can return the wrong token.</p>"""},
 {"h": "Look across rows for the collision itself",
  "body": """<p>Per-row checks miss the finding that matters most: two rows carrying the same <code>team_id</code> under different <code>enterprise_id</code> values, or one key that two distinct identities both map to. That is not a risk of leakage, it is leakage already happening on whichever row was written second.</p>"""},
 {"h": "Size the org before you estimate the blast radius",
  "body": """<p><code>admin.teams.list</code> reports how many workspaces the org contains, which converts "one collision" into "one collision across forty workspaces". It needs <code>admin.teams:read</code> on a user token from an org admin, so treat it as optional context rather than part of the detection.</p>"""},
 {"h": "Re-key, then backfill by re-running auth.test",
  "body": """<p>The migration is mechanical: widen the key to the triple with <code>enterprise_id</code> nullable, implement lookup as exact-match-then-org-wide-fallback, and populate the new column by calling <code>auth.test</code> once per stored token. The script prints this and performs none of it.</p>"""},
],
"verify": """<p>After the migration, re-run over the same export. Every row should round-trip and no <code>team_id</code> should appear under two organisations.</p>
<pre><code class="language-bash">python3 slack_install_key_audit.py --store installs.json
# 12 install(s) checked, 0 keyed in a way that can collide</code></pre>""",
"code_intro": "One GET per stored token, and no writes anywhere &mdash; this script reads credentials belonging to several tenants at once, which is precisely why it must never be able to change one. Both classifiers are pure: <code>verdict</code> compares a single row against its live identity, and <code>collisions</code> looks across rows for the two shapes that a per-row check cannot see.",
"py_file": "slack_install_key_audit.py",
"py": '''"""Audit a Slack installation store for keys that collide on Enterprise Grid.

Read only. GET requests and nothing else, because this script is handed one
token per tenant and a mistake here is a cross-tenant one. The repair is a store
migration; it is printed for a human to run.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_install_key_audit")

API = "https://slack.com/api/"


def verdict(stored, identity):
    """Compare one stored installation row against what its token says it is.

    `stored` is the row as your store holds it: a `key`, and whatever else was
    persisted (`enterprise_id`, `is_enterprise_install`). `identity` is the
    parsed auth.test body for that row's token. Pure, so the whole truth table
    runs offline.
    """
    if identity.get("ok") is not True:
        return ("unusable",
                "auth.test answered ok: false, error=%s. The row cannot be "
                "checked, and a token that no longer authenticates is its own "
                "finding." % (identity.get("error") or "<no error field>"))

    live_team = identity.get("team_id")
    live_ent = identity.get("enterprise_id")
    org_install = identity.get("is_enterprise_install") is True
    key = str(stored.get("key", ""))
    stored_ent = stored.get("enterprise_id")
    stored_org = stored.get("is_enterprise_install") is True

    if live_ent and not stored_ent:
        return ("enterprise-id-dropped",
                "live install is in org %s and the row kept no enterprise_id. "
                "Two workspaces in different orgs can now be filed under one "
                "key, and the second write wins." % live_ent)
    if live_ent and stored_ent != live_ent:
        return ("enterprise-id-wrong",
                "row says org %s, the token says %s. A lookup on this row hands "
                "out a credential belonging to another organisation."
                % (stored_ent, live_ent))
    if org_install and not stored_org:
        return ("org-install-under-team-key",
                "is_enterprise_install is true but the row is filed as a "
                "workspace install under %r. The grant covers every workspace "
                "in the org, including ones with no row at all." % key)
    if stored_org and not org_install:
        return ("workspace-install-flagged-org",
                "the row claims an org-wide install and the token is scoped to "
                "workspace %s. Lookups for sibling workspaces will match this "
                "row and use a token that cannot serve them." % live_team)
    if live_team and key not in (live_team, "%s.%s" % (live_ent, live_team)):
        return ("key-drift",
                "row is filed under %r and the token reports team %s. The key "
                "does not round-trip, so whatever wrote it is not what reads it."
                % (key, live_team))
    if live_ent:
        return ("grid-keyed",
                "org %s, team %s, org-wide=%s, all three persisted"
                % (live_ent, live_team, org_install))
    return ("single-workspace",
            "team %s, not on Grid. team_id alone is adequate today and stops "
            "being adequate the day this customer migrates to an org."
            % live_team)


def collisions(seen):
    """Find cross-row collisions. Pure.

    `seen` is a list of dicts with `key`, `team_id` and `enterprise_id`. Returns
    (team_collisions, key_collisions): team ids that appear under more than one
    organisation, and store keys that resolve to more than one live identity.
    Neither is visible from a single row, and both are leakage in progress.
    """
    by_team = {}
    by_key = {}
    for row in seen:
        team = row.get("team_id")
        if team:
            by_team.setdefault(team, set()).add(row.get("enterprise_id") or "")
        by_key.setdefault(str(row.get("key", "")), set()).add(
            (row.get("enterprise_id") or "", team or ""))
    team_collisions = sorted(t for t, orgs in by_team.items() if len(orgs) > 1)
    key_collisions = sorted(k for k, ids in by_key.items() if len(ids) > 1)
    return team_collisions, key_collisions


def auth_test(session, token):
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def load_rows(path):
    """Rows as the store holds them, not as it wishes it held them."""
    if path:
        return json.loads(open(path, encoding="utf-8").read())
    return [{"key": os.environ.get("SLACK_TEAM_ID", "<the only row>"),
             "token_env": "SLACK_BOT_TOKEN"}]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", help="JSON array of installation rows; each row needs "
                                    "key and token_env, plus whatever else you persist")
    args = ap.parse_args()

    if not args.store and not os.environ.get("SLACK_BOT_TOKEN"):
        log.error("set SLACK_BOT_TOKEN, or pass --store with one token_env per row")
        return 2

    rows = load_rows(args.store)
    s = requests.Session()

    seen = []
    bad = 0
    for row in rows:
        token = os.environ.get(row.get("token_env") or "SLACK_BOT_TOKEN")
        if not token:
            log.warning("%-28s %s", "no-token", "row %r names %s and it is unset"
                        % (row.get("key"), row.get("token_env")))
            bad += 1
            continue
        identity = auth_test(s, token)
        state, detail = verdict(row, identity)
        line = "%-28s %-18s %s" % (state, row.get("key"), detail)
        if state in ("grid-keyed", "single-workspace"):
            log.info(line)
        else:
            bad += 1
            log.warning(line)
            log.warning("  repair: key this store on (enterprise_id, team_id, "
                        "is_enterprise_install), enterprise_id nullable")
        if identity.get("ok") is True:
            seen.append({"key": row.get("key"),
                         "team_id": identity.get("team_id"),
                         "enterprise_id": identity.get("enterprise_id")})

    team_collisions, key_collisions = collisions(seen)
    for team in team_collisions:
        bad += 1
        log.warning("%-28s %s", "team-id-in-two-orgs",
                    "team %s is filed under more than one enterprise_id" % team)
    for key in key_collisions:
        bad += 1
        log.warning("%-28s %s", "key-serves-two-installs",
                    "store key %r resolves to more than one live identity" % key)
    if team_collisions or key_collisions:
        log.warning("  repair: migrate before the next uninstall. A delete keyed on "
                    "team_id alone removes another tenant's row")

    log.info("%d install(s) checked, %d keyed in a way that can collide",
             len(rows), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-install-key-audit.mjs",
"js": '''/**
 * Audit a Slack installation store for keys that collide on Enterprise Grid.
 *
 * Read only. GET requests and nothing else, because this script is handed one
 * token per tenant and a mistake here is a cross-tenant one. The repair is a
 * store migration; it is printed for a human to run.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

/**
 * Compare one stored installation row against what its token says it is.
 * Pure, so the whole truth table runs offline.
 */
export function verdict(stored, identity) {
  if (identity?.ok !== true) {
    return ['unusable',
      `auth.test answered ok: false, error=${identity?.error ?? '<no error field>'}. ` +
      'The row cannot be checked, and a token that no longer authenticates is its ' +
      'own finding.'];
  }

  const liveTeam = identity.team_id;
  const liveEnt = identity.enterprise_id;
  const orgInstall = identity.is_enterprise_install === true;
  const key = String(stored.key ?? '');
  const storedEnt = stored.enterprise_id;
  const storedOrg = stored.is_enterprise_install === true;

  if (liveEnt && !storedEnt) {
    return ['enterprise-id-dropped',
      `live install is in org ${liveEnt} and the row kept no enterprise_id. Two ` +
      'workspaces in different orgs can now be filed under one key, and the ' +
      'second write wins.'];
  }
  if (liveEnt && storedEnt !== liveEnt) {
    return ['enterprise-id-wrong',
      `row says org ${storedEnt}, the token says ${liveEnt}. A lookup on this row ` +
      'hands out a credential belonging to another organisation.'];
  }
  if (orgInstall && !storedOrg) {
    return ['org-install-under-team-key',
      `is_enterprise_install is true but the row is filed as a workspace install ` +
      `under ${JSON.stringify(key)}. The grant covers every workspace in the org, ` +
      'including ones with no row at all.'];
  }
  if (storedOrg && !orgInstall) {
    return ['workspace-install-flagged-org',
      `the row claims an org-wide install and the token is scoped to workspace ` +
      `${liveTeam}. Lookups for sibling workspaces will match this row and use a ` +
      'token that cannot serve them.'];
  }
  if (liveTeam && key !== liveTeam && key !== `${liveEnt}.${liveTeam}`) {
    return ['key-drift',
      `row is filed under ${JSON.stringify(key)} and the token reports team ` +
      `${liveTeam}. The key does not round-trip, so whatever wrote it is not what ` +
      'reads it.'];
  }
  if (liveEnt) {
    return ['grid-keyed',
      `org ${liveEnt}, team ${liveTeam}, org-wide=${orgInstall}, all three persisted`];
  }
  return ['single-workspace',
    `team ${liveTeam}, not on Grid. team_id alone is adequate today and stops being ` +
    'adequate the day this customer migrates to an org.'];
}

/**
 * Find cross-row collisions. Pure. Returns [teamCollisions, keyCollisions]:
 * team ids filed under more than one organisation, and store keys that resolve
 * to more than one live identity.
 */
export function collisions(seen) {
  const byTeam = new Map();
  const byKey = new Map();
  for (const row of seen) {
    const team = row.team_id;
    if (team) {
      if (!byTeam.has(team)) byTeam.set(team, new Set());
      byTeam.get(team).add(row.enterprise_id ?? '');
    }
    const key = String(row.key ?? '');
    if (!byKey.has(key)) byKey.set(key, new Set());
    byKey.get(key).add(`${row.enterprise_id ?? ''}|${team ?? ''}`);
  }
  const teamCollisions = [...byTeam.entries()]
    .filter(([, orgs]) => orgs.size > 1).map(([t]) => t).sort();
  const keyCollisions = [...byKey.entries()]
    .filter(([, ids]) => ids.size > 1).map(([k]) => k).sort();
  return [teamCollisions, keyCollisions];
}

async function authTest(token) {
  const res = await fetch(API + 'auth.test', {
    headers: { Authorization: `Bearer ${token}` },
  });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function loadRows(path) {
  if (path) return JSON.parse(await readFile(path, 'utf8'));
  return [{ key: process.env.SLACK_TEAM_ID ?? '<the only row>', token_env: 'SLACK_BOT_TOKEN' }];
}

async function main() {
  const args = process.argv.slice(2);
  const i = args.indexOf('--store');
  const store = i === -1 ? null : args[i + 1];

  if (!store && !process.env.SLACK_BOT_TOKEN) {
    console.error('set SLACK_BOT_TOKEN, or pass --store with one token_env per row');
    process.exitCode = 2;
    return;
  }

  const rows = await loadRows(store);
  const seen = [];
  let bad = 0;

  for (const row of rows) {
    const token = process.env[row.token_env ?? 'SLACK_BOT_TOKEN'];
    if (!token) {
      console.warn(`${'no-token'.padEnd(28)} row ${JSON.stringify(row.key)} names ` +
                   `${row.token_env} and it is unset`);
      bad += 1;
      continue;
    }
    const identity = await authTest(token);
    const [state, detail] = verdict(row, identity);
    const line = `${state.padEnd(28)} ${String(row.key).padEnd(18)} ${detail}`;
    if (state === 'grid-keyed' || state === 'single-workspace') {
      console.log(line);
    } else {
      bad += 1;
      console.warn(line);
      console.warn('  repair: key this store on (enterprise_id, team_id, ' +
                   'is_enterprise_install), enterprise_id nullable');
    }
    if (identity?.ok === true) {
      seen.push({ key: row.key, team_id: identity.team_id, enterprise_id: identity.enterprise_id });
    }
  }

  const [teamCollisions, keyCollisions] = collisions(seen);
  for (const team of teamCollisions) {
    bad += 1;
    console.warn(`${'team-id-in-two-orgs'.padEnd(28)} team ${team} is filed under ` +
                 'more than one enterprise_id');
  }
  for (const key of keyCollisions) {
    bad += 1;
    console.warn(`${'key-serves-two-installs'.padEnd(28)} store key ` +
                 `${JSON.stringify(key)} resolves to more than one live identity`);
  }
  if (teamCollisions.length || keyCollisions.length) {
    console.warn('  repair: migrate before the next uninstall. A delete keyed on ' +
                 'team_id alone removes another tenant\\'s row');
  }

  console.log(`${rows.length} install(s) checked, ${bad} keyed in a way that can collide`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The row worth pinning is the one that looks healthiest: a workspace install on a non-Grid customer, filed under <code>team_id</code>, with no <code>enterprise_id</code> to store. It must not be reported as a finding, or the audit cries wolf on every ordinary customer &mdash; and it must not be reported as safe forever either, because the day that workspace joins an org the same row becomes the leak.",
"test_py_file": "test_slack_install_key_audit.py",
"test_py": '''from slack_install_key_audit import collisions, verdict


def test_grid_install_with_no_stored_enterprise_id_is_the_finding():
    stored = {"key": "T111"}
    live = {"ok": True, "team_id": "T111", "enterprise_id": "E999",
            "is_enterprise_install": False}
    state, detail = verdict(stored, live)
    assert state == "enterprise-id-dropped"
    assert "E999" in detail


def test_org_wide_install_filed_under_a_workspace_key():
    stored = {"key": "T111", "enterprise_id": "E999"}
    live = {"ok": True, "team_id": None, "enterprise_id": "E999",
            "is_enterprise_install": True}
    assert verdict(stored, live)[0] == "org-install-under-team-key"


def test_row_pointing_at_another_org_is_a_credential_handout():
    stored = {"key": "E1.T111", "enterprise_id": "E1"}
    live = {"ok": True, "team_id": "T111", "enterprise_id": "E2",
            "is_enterprise_install": False}
    state, detail = verdict(stored, live)
    assert state == "enterprise-id-wrong"
    assert "another organisation" in detail


def test_plain_workspace_install_is_not_reported():
    stored = {"key": "T111"}
    live = {"ok": True, "team_id": "T111", "enterprise_id": None,
            "is_enterprise_install": False}
    state, detail = verdict(stored, live)
    assert state == "single-workspace"
    assert "migrates to an org" in detail


def test_key_that_does_not_round_trip():
    stored = {"key": "T222"}
    live = {"ok": True, "team_id": "T111", "enterprise_id": None,
            "is_enterprise_install": False}
    assert verdict(stored, live)[0] == "key-drift"


def test_dead_token_is_reported_rather_than_guessed_at():
    assert verdict({"key": "T111"}, {"ok": False, "error": "token_revoked"})[0] == "unusable"


def test_same_team_under_two_orgs_is_a_cross_row_finding():
    seen = [{"key": "T111", "team_id": "T111", "enterprise_id": "E1"},
            {"key": "T111", "team_id": "T111", "enterprise_id": "E2"}]
    teams, keys = collisions(seen)
    assert teams == ["T111"]
    assert keys == ["T111"]


def test_distinct_installs_do_not_collide():
    seen = [{"key": "E1.T111", "team_id": "T111", "enterprise_id": "E1"},
            {"key": "E2.T222", "team_id": "T222", "enterprise_id": "E2"}]
    assert collisions(seen) == ([], [])
''',
"test_js_file": "slack-install-key-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { collisions, verdict } from './slack-install-key-audit.mjs';

test('grid install with no stored enterprise_id is the finding', () => {
  const [state, detail] = verdict(
    { key: 'T111' },
    { ok: true, team_id: 'T111', enterprise_id: 'E999', is_enterprise_install: false },
  );
  assert.equal(state, 'enterprise-id-dropped');
  assert.match(detail, /E999/);
});

test('org wide install filed under a workspace key', () => {
  const [state] = verdict(
    { key: 'T111', enterprise_id: 'E999' },
    { ok: true, team_id: null, enterprise_id: 'E999', is_enterprise_install: true },
  );
  assert.equal(state, 'org-install-under-team-key');
});

test('row pointing at another org is a credential handout', () => {
  const [state, detail] = verdict(
    { key: 'E1.T111', enterprise_id: 'E1' },
    { ok: true, team_id: 'T111', enterprise_id: 'E2', is_enterprise_install: false },
  );
  assert.equal(state, 'enterprise-id-wrong');
  assert.match(detail, /another organisation/);
});

test('plain workspace install is not reported', () => {
  const [state, detail] = verdict(
    { key: 'T111' },
    { ok: true, team_id: 'T111', enterprise_id: null, is_enterprise_install: false },
  );
  assert.equal(state, 'single-workspace');
  assert.match(detail, /migrates to an org/);
});

test('key that does not round trip', () => {
  const [state] = verdict(
    { key: 'T222' },
    { ok: true, team_id: 'T111', enterprise_id: null, is_enterprise_install: false },
  );
  assert.equal(state, 'key-drift');
});

test('dead token is reported rather than guessed at', () => {
  assert.equal(verdict({ key: 'T111' }, { ok: false, error: 'token_revoked' })[0], 'unusable');
});

test('same team under two orgs is a cross row finding', () => {
  const [teams, keys] = collisions([
    { key: 'T111', team_id: 'T111', enterprise_id: 'E1' },
    { key: 'T111', team_id: 'T111', enterprise_id: 'E2' },
  ]);
  assert.deepEqual(teams, ['T111']);
  assert.deepEqual(keys, ['T111']);
});

test('distinct installs do not collide', () => {
  const [teams, keys] = collisions([
    { key: 'E1.T111', team_id: 'T111', enterprise_id: 'E1' },
    { key: 'E2.T222', team_id: 'T222', enterprise_id: 'E2' },
  ]);
  assert.deepEqual(teams, []);
  assert.deepEqual(keys, []);
});
''',
"faq": [
 ("Is this really a security issue rather than a bug?",
  "Yes. The outcome is one tenant's token being used to act in another tenant's workspace, inside the same Enterprise Grid organisation. Treat it the way you would treat any cross-tenant key collision: the audit is read-only, the migration is deliberate, and the customers whose rows collided are the ones who can tell you what was written where."),
 ("Why can an org-wide install have a null team_id?",
  "Because it is not scoped to a workspace. When is_enterprise_install is true the grant applies across the organisation, so there is no single team to name. Any store whose primary key is team_id has nowhere to put that row, which is why it ends up filed under whichever workspace happened to be in the payload."),
 ("Do I need admin scopes to run the audit?",
  "No. The detection is auth.test per stored token, which needs no scopes at all. admin.teams.list is optional and only sizes the org, and it needs admin.teams:read on a user token belonging to an org admin, which is a different credential class from the bot token the audit otherwise uses."),
 ("What should lookup do once the key is a triple?",
  "Prefer the exact workspace row for (enterprise_id, team_id), and fall back to the org-wide row for (enterprise_id, null, true) when there is no exact match. Without that fallback, an app installed org-wide stops serving every workspace that never had its own row written."),
 ("Can I detect this without an export of my store?",
  "Only partially. With a single token the script can tell you whether that install is on Grid and whether you kept its enterprise_id, which is the per-row half of the finding. The collision half is a comparison between rows, so it needs the rows."),
],
"related": [
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/event-subscriptions-auto-disabled/", "Slack turned event delivery off"),
],
"citations": [CITE_AUTH_TEST, CITE_INSTALL, CITE_GRID, CITE_ADMIN_TEAMS],
},

{
"slug": "files-upload-retired",
"title": "files.upload is retired: one probe returns method_deprecated",
"description": "files.upload was sunset for every app on 12 November 2025. One argument-free read of the method answers method_deprecated and settles it in a second.",
"h1": "files.upload is retired: one probe returns method_deprecated",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack files.upload deprecated", "method_deprecated slack",
             "files.getUploadURLExternal", "files.completeUploadExternal",
             "slack filesUploadV2 migration"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every internal tool that posts a screenshot into Slack stopped posting screenshots, all of them on the same day, none of them deployed that week. The logs say <code>200</code>. The bodies say <code>{\"ok\": false, \"error\": \"method_deprecated\"}</code>. Nothing broke: <code>files.upload</code> reached the end of a sunset that was announced eighteen months earlier and moved once.",
"short_answer": """<p>Call <code>files.upload</code> once with no arguments and read the error. <code>method_deprecated</code> or <code>deprecated_endpoint</code> means the method is dead for this app and no amount of retrying will change it. A call with no file cannot create anything, so the probe is a read.</p>
<p>The replacement is three calls: <code>files.getUploadURLExternal</code> for a one-time URL and a <code>file_id</code>, an upload of the raw bytes to that URL, then <code>files.completeUploadExternal</code> to register the file and share it. The SDK helpers <code>filesUploadV2</code> and <code>files_upload_v2</code> wrap all three, and are where the migration should start.</p>""",
"problem": """<p>This is the rarest kind of Slack failure: one with a date on it. Slack deprecated <code>files.upload</code> on 16 May 2024, blocked it immediately for apps created after 8 May 2024, and sunset it for every remaining app on 12 November 2025 &mdash; a date that had already been moved once from 11 March 2025. Nothing about your code changed. The method simply stopped existing.</p>
<p>What makes the fleet fail at once is that this method was easy to hand-roll. It took a multipart form and a channel name, it worked in three lines of <code>curl</code>, and so it ended up copied into report scripts, CI notifiers, alerting cron jobs and one-off dashboards that nobody thinks of as Slack integrations. They share a cutover date rather than a codebase, which is why the outage looks like an infrastructure event and is not one.</p>
<p>And, as everywhere else in this section, the refusal arrives as <code>200 OK</code>. A script that checked the status code has been reporting successful uploads since the sunset. The screenshots are not in a retry queue; they were never anywhere.</p>""",
"why": """<p><strong>The replacement is a sequence, not a rename.</strong> <code>files.getUploadURLExternal?filename=&amp;length=</code> returns <code>upload_url</code> and <code>file_id</code>; the bytes go to that URL directly; <code>files.completeUploadExternal</code> then registers the file and shares it into a channel. Three round trips, each of which can fail on its own, replacing one call that could not.</p>
<p><strong><code>length</code> must be the exact byte count.</strong> The upload URL is issued for a specific size. A length computed from a string's character count rather than its encoded bytes is the single most common migration failure, and it fails at the upload step rather than at the call that got the URL wrong.</p>
<p><strong><code>channel_id</code> takes an ID and only an ID.</strong> The old method tolerated <code>#general</code>. <code>files.completeUploadExternal</code> does not: channel names and user IDs are rejected. Every hand-rolled caller that stored a channel name now needs a lookup it never had.</p>
<p><strong>A file uploaded and never completed is invisible, not absent.</strong> If the third call never happens the file exists in Slack's storage and appears in no channel. Half-migrated tools produce a stream of orphans rather than an error.</p>
<p><strong>The warning field carried the notice, and nobody read it.</strong> Before the sunset, successful <code>files.upload</code> calls came back <code>ok: true</code> with a deprecation notice in <code>warning</code>. That was the advance notice, on the response, for a year and a half.</p>""",
"steps": [
 {"h": "Probe the method with no arguments",
  "body": """<p>A GET to <code>files.upload</code> carrying no file, no content and no channel cannot upload anything; it exists only to be refused, and the refusal is the answer. <code>method_deprecated</code> or <code>deprecated_endpoint</code> is conclusive.</p>"""},
 {"h": "Read the other errors as the answers they are",
  "body": """<p><code>no_file_data</code> would mean the method is still answering for this app &mdash; surprising after the sunset, and still not a reason to stay. <code>missing_scope</code> means the probe could not reach the method at all, so it tells you nothing about the method and you should migrate anyway. <code>invalid_auth</code> is a token problem wearing a deprecation problem's clothes.</p>"""},
 {"h": "Corroborate with the app's own upload history",
  "body": """<p><code>auth.test</code> gives the bot's user ID; <code>files.list?user=&lt;that ID&gt;&amp;count=100</code> gives the files this app uploaded. Restricting by user matters &mdash; unrestricted, the list is every file the token can see, and other apps' successful uploads will make yours look healthy.</p>"""},
 {"h": "Compare the newest upload against the cutover",
  "body": """<p>If the newest file this app uploaded predates 12 November 2025, the fleet has been failing since the sunset and nobody noticed. If there are files after it, something in the fleet already speaks the new flow, and the job becomes finding which callers do not.</p>"""},
 {"h": "Migrate to the three-call flow, or to the SDK helper",
  "body": """<p><code>client.filesUploadV2({ channel_id, file, filename, initial_comment })</code> in Node, <code>client.files_upload_v2(...)</code> in Python. Hand-rolled callers need the exact byte length and a channel ID. Either way, keep the sequence in one function so a caller cannot perform two thirds of it.</p>"""},
],
"verify": """<p>After the migration, upload once from the real code path and re-run. The probe still reports the method as retired &mdash; that is permanent &mdash; but the newest file should now be dated after the cutover.</p>
<pre><code class="language-bash">python3 slack_files_upload_probe.py
# retired    files.upload answered method_deprecated
# uploading  newest app upload is after the 2025-11-12 cutover</code></pre>""",
"code_intro": "Two GETs: one deliberately argument-free probe of <code>files.upload</code>, and one <code>files.list</code> restricted to the bot's own uploads. Nothing is uploaded, and nothing could be &mdash; the probe carries no bytes. Both classifiers are pure: <code>verdict</code> reads the probe's error, and <code>upload_activity</code> compares the newest upload against the sunset date.",
"py_file": "slack_files_upload_probe.py",
"py": '''"""Confirm whether files.upload is dead for this app, and whether it was noticed.

Read only. The probe calls files.upload with no arguments, which cannot create
anything: it exists to be refused, and the refusal is the finding. The migration
is printed, never performed.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_files_upload_probe")

API = "https://slack.com/api/"

# 12 November 2025, 00:00 UTC: the day files.upload was sunset for all apps.
# The date was announced for 11 March 2025 and moved once.
SUNSET = 1762905600

DEAD = {"method_deprecated", "deprecated_endpoint"}
# Errors that mean the method answered rather than refused to exist.
ALIVE = {"no_file_data", "no_file_or_content", "invalid_arguments", "posting_to_general_channel_denied"}


def verdict(body):
    """Classify the argument-free files.upload probe. Pure, so it runs offline.

    The probe's whole job is to distinguish "this method no longer exists" from
    "this method exists and you called it wrong", and both arrive as HTTP 200.
    """
    if not isinstance(body, dict):
        return ("unreadable",
                "the probe got a body that is not JSON, so something other than "
                "Slack answered. Nothing can be concluded about the method.")
    error = body.get("error")
    if body.get("ok") is True:
        return ("unexpected",
                "ok: true from a call with no file. Read the response by hand "
                "before trusting anything else here.")
    if error in DEAD:
        return ("retired",
                "files.upload answered %s. The method was sunset for all apps on "
                "2025-11-12 and will not come back." % error)
    if error == "missing_scope":
        return ("unknown",
                "missing_scope: needed=%s. The probe never reached the method, so "
                "this says nothing about whether it is alive. Migrate anyway."
                % (body.get("needed") or "?"))
    if error in ("invalid_auth", "not_authed", "token_revoked", "account_inactive"):
        return ("auth",
                "error=%s. That is the token, not the method. Fix the credential "
                "and re-run before concluding anything." % error)
    if error in ALIVE:
        return ("still-answering",
                "error=%s, which means the method parsed the call rather than "
                "refusing to exist. Unexpected after the sunset, and still not a "
                "reason to stay on it." % error)
    return ("other",
            "error=%s. Not a deprecation answer; read it before acting."
            % (error or "<no error field>"))


def upload_activity(files, now=None, sunset=SUNSET):
    """Classify this app's own upload history against the cutover. Pure.

    `files` is the files.list array, restricted to files this bot uploaded.
    A fleet that has been failing since the sunset has no files after it.
    """
    stamps = sorted(int(f.get("created") or 0) for f in files)
    if not stamps:
        return ("no-uploads",
                "this app has uploaded no files the token can see, so there is "
                "no history to date the breakage from.")
    newest = stamps[-1]
    after = [s for s in stamps if s >= sunset]
    if after:
        return ("uploading",
                "%d file(s) uploaded after the 2025-11-12 cutover, so some caller "
                "already speaks the replacement flow." % len(after))
    days = int(((now or time.time()) - newest) / 86400)
    return ("silent-since-sunset",
            "newest upload is %d day(s) old and predates the cutover. Every "
            "caller has been failing since, quietly, at HTTP 200." % days)


def get(session, method, **params):
    r = session.get(API + method, params=params, timeout=30)
    try:
        return r.json()
    except ValueError:
        return r.text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=100,
                    help="how many of the app's own files to read (default 100)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (files:read is enough for the corroboration)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    state, detail = verdict(get(s, "files.upload"))
    bad = 0
    if state == "retired":
        bad += 1
        log.warning("%-19s %s", state, detail)
        log.warning("  repair: files.getUploadURLExternal(filename, length) -> upload the "
                    "raw bytes to upload_url -> files.completeUploadExternal(files, channel_id)")
        log.warning("  or use the SDK helper: client.files_upload_v2(...) / "
                    "client.filesUploadV2({...})")
    elif state in ("still-answering", "unknown", "auth", "unreadable", "unexpected", "other"):
        log.warning("%-19s %s", state, detail)
    else:
        log.info("%-19s %s", state, detail)

    me = get(s, "auth.test")
    if isinstance(me, dict) and me.get("ok") is True:
        listing = get(s, "files.list", user=me.get("user_id"), count=str(args.count))
        if isinstance(listing, dict) and listing.get("ok") is True:
            hstate, hdetail = upload_activity(listing.get("files") or [])
            if hstate == "silent-since-sunset":
                bad += 1
                log.warning("%-19s %s", hstate, hdetail)
            else:
                log.info("%-19s %s", hstate, hdetail)
        else:
            log.info("%-19s files.list did not answer ok: true (%s); the probe "
                     "above stands on its own", "no-history",
                     isinstance(listing, dict) and listing.get("error") or "?")
    else:
        log.info("%-19s auth.test did not answer ok: true, so the history check "
                 "was skipped", "no-history")

    log.info("1 method probed, %d finding(s)", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-files-upload-probe.mjs",
"js": '''/**
 * Confirm whether files.upload is dead for this app, and whether it was noticed.
 *
 * Read only. The probe calls files.upload with no arguments, which cannot create
 * anything: it exists to be refused, and the refusal is the finding. The
 * migration is printed, never performed.
 */
const API = 'https://slack.com/api/';

// 12 November 2025, 00:00 UTC: the day files.upload was sunset for all apps.
// The date was announced for 11 March 2025 and moved once.
export const SUNSET = 1762905600;

const DEAD = new Set(['method_deprecated', 'deprecated_endpoint']);
// Errors that mean the method answered rather than refused to exist.
const ALIVE = new Set([
  'no_file_data', 'no_file_or_content', 'invalid_arguments',
  'posting_to_general_channel_denied',
]);

/**
 * Classify the argument-free files.upload probe. Pure, so it runs offline.
 * Its job is to separate "this method no longer exists" from "this method
 * exists and you called it wrong", both of which arrive as HTTP 200.
 */
export function verdict(body) {
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    return ['unreadable',
      'the probe got a body that is not JSON, so something other than Slack ' +
      'answered. Nothing can be concluded about the method.'];
  }
  const error = body.error;
  if (body.ok === true) {
    return ['unexpected',
      'ok: true from a call with no file. Read the response by hand before ' +
      'trusting anything else here.'];
  }
  if (DEAD.has(error)) {
    return ['retired',
      `files.upload answered ${error}. The method was sunset for all apps on ` +
      '2025-11-12 and will not come back.'];
  }
  if (error === 'missing_scope') {
    return ['unknown',
      `missing_scope: needed=${body.needed ?? '?'}. The probe never reached the ` +
      'method, so this says nothing about whether it is alive. Migrate anyway.'];
  }
  if (['invalid_auth', 'not_authed', 'token_revoked', 'account_inactive'].includes(error)) {
    return ['auth',
      `error=${error}. That is the token, not the method. Fix the credential and ` +
      're-run before concluding anything.'];
  }
  if (ALIVE.has(error)) {
    return ['still-answering',
      `error=${error}, which means the method parsed the call rather than ` +
      'refusing to exist. Unexpected after the sunset, and still not a reason ' +
      'to stay on it.'];
  }
  return ['other',
    `error=${error ?? '<no error field>'}. Not a deprecation answer; read it ` +
    'before acting.'];
}

/**
 * Classify this app's own upload history against the cutover. Pure.
 * `files` is the files.list array restricted to files this bot uploaded.
 */
export function uploadActivity(files, now = null, sunset = SUNSET) {
  const stamps = files.map((f) => Number(f.created ?? 0)).sort((a, b) => a - b);
  if (!stamps.length) {
    return ['no-uploads',
      'this app has uploaded no files the token can see, so there is no history ' +
      'to date the breakage from.'];
  }
  const newest = stamps[stamps.length - 1];
  const after = stamps.filter((s) => s >= sunset);
  if (after.length) {
    return ['uploading',
      `${after.length} file(s) uploaded after the 2025-11-12 cutover, so some ` +
      'caller already speaks the replacement flow.'];
  }
  const days = Math.floor((((now ?? Date.now() / 1000)) - newest) / 86400);
  return ['silent-since-sunset',
    `newest upload is ${days} day(s) old and predates the cutover. Every caller ` +
    'has been failing since, quietly, at HTTP 200.'];
}

async function get(token, method, params = {}) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await res.json();
  } catch {
    return null;
  }
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (files:read is enough for the corroboration)');
    process.exitCode = 2;
    return;
  }

  const args = process.argv.slice(2);
  const i = args.indexOf('--count');
  const count = i === -1 ? '100' : args[i + 1];

  const [state, detail] = verdict(await get(token, 'files.upload'));
  let bad = 0;
  if (state === 'retired') {
    bad += 1;
    console.warn(`${state.padEnd(19)} ${detail}`);
    console.warn('  repair: files.getUploadURLExternal(filename, length) -> upload the ' +
                 'raw bytes to upload_url -> files.completeUploadExternal(files, channel_id)');
    console.warn('  or use the SDK helper: client.filesUploadV2({...}) / ' +
                 'client.files_upload_v2(...)');
  } else {
    console.warn(`${state.padEnd(19)} ${detail}`);
  }

  const me = await get(token, 'auth.test');
  if (me?.ok === true) {
    const listing = await get(token, 'files.list', { user: me.user_id, count });
    if (listing?.ok === true) {
      const [hstate, hdetail] = uploadActivity(listing.files ?? []);
      if (hstate === 'silent-since-sunset') {
        bad += 1;
        console.warn(`${hstate.padEnd(19)} ${hdetail}`);
      } else {
        console.log(`${hstate.padEnd(19)} ${hdetail}`);
      }
    } else {
      console.log(`${'no-history'.padEnd(19)} files.list did not answer ok: true ` +
                  `(${listing?.error ?? '?'}); the probe above stands on its own`);
    }
  } else {
    console.log(`${'no-history'.padEnd(19)} auth.test did not answer ok: true, so ` +
                'the history check was skipped');
  }

  console.log(`1 method probed, ${bad} finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two answers that must not be confused are <code>method_deprecated</code> and <code>missing_scope</code>. The first is the finding; the second means the probe never reached the method, and a classifier that folds it into &quot;the method is fine&quot; will tell a team on the dead path that they have nothing to do.",
"test_py_file": "test_slack_files_upload_probe.py",
"test_py": '''from slack_files_upload_probe import SUNSET, upload_activity, verdict


def test_method_deprecated_is_the_finding():
    state, detail = verdict({"ok": False, "error": "method_deprecated"})
    assert state == "retired"
    assert "2025-11-12" in detail


def test_deprecated_endpoint_is_the_same_finding():
    assert verdict({"ok": False, "error": "deprecated_endpoint"})[0] == "retired"


def test_missing_scope_proves_nothing_about_the_method():
    state, detail = verdict({"ok": False, "error": "missing_scope", "needed": "files:write"})
    assert state == "unknown"
    assert "files:write" in detail


def test_a_parsed_call_means_the_method_still_answers():
    assert verdict({"ok": False, "error": "no_file_data"})[0] == "still-answering"


def test_a_credential_error_is_not_a_deprecation():
    assert verdict({"ok": False, "error": "invalid_auth"})[0] == "auth"


def test_non_json_body_is_not_an_answer():
    assert verdict("<html>proxy</html>")[0] == "unreadable"


def test_history_ending_before_the_cutover_is_a_silent_outage():
    files = [{"created": SUNSET - 86400 * 30}, {"created": SUNSET - 86400 * 400}]
    state, detail = upload_activity(files, now=SUNSET + 86400 * 10)
    assert state == "silent-since-sunset"
    assert "40 day(s)" in detail


def test_an_upload_after_the_cutover_clears_the_history_check():
    files = [{"created": SUNSET - 10}, {"created": SUNSET + 10}]
    assert upload_activity(files, now=SUNSET + 86400)[0] == "uploading"


def test_no_files_is_not_evidence_either_way():
    assert upload_activity([], now=SUNSET)[0] == "no-uploads"
''',
"test_js_file": "slack-files-upload-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SUNSET, uploadActivity, verdict } from './slack-files-upload-probe.mjs';

test('method_deprecated is the finding', () => {
  const [state, detail] = verdict({ ok: false, error: 'method_deprecated' });
  assert.equal(state, 'retired');
  assert.match(detail, /2025-11-12/);
});

test('deprecated_endpoint is the same finding', () => {
  assert.equal(verdict({ ok: false, error: 'deprecated_endpoint' })[0], 'retired');
});

test('missing_scope proves nothing about the method', () => {
  const [state, detail] = verdict({ ok: false, error: 'missing_scope', needed: 'files:write' });
  assert.equal(state, 'unknown');
  assert.match(detail, /files:write/);
});

test('a parsed call means the method still answers', () => {
  assert.equal(verdict({ ok: false, error: 'no_file_data' })[0], 'still-answering');
});

test('a credential error is not a deprecation', () => {
  assert.equal(verdict({ ok: false, error: 'invalid_auth' })[0], 'auth');
});

test('non json body is not an answer', () => {
  assert.equal(verdict('<html>proxy</html>')[0], 'unreadable');
});

test('history ending before the cutover is a silent outage', () => {
  const files = [{ created: SUNSET - 86400 * 30 }, { created: SUNSET - 86400 * 400 }];
  const [state, detail] = uploadActivity(files, SUNSET + 86400 * 10);
  assert.equal(state, 'silent-since-sunset');
  assert.match(detail, /40 day\\(s\\)/);
});

test('an upload after the cutover clears the history check', () => {
  const files = [{ created: SUNSET - 10 }, { created: SUNSET + 10 }];
  assert.equal(uploadActivity(files, SUNSET + 86400)[0], 'uploading');
});

test('no files is not evidence either way', () => {
  assert.equal(uploadActivity([], SUNSET)[0], 'no-uploads');
});
''',
"faq": [
 ("Is calling files.upload with no arguments really read-only?",
  "Yes. There is no file, no content and no channel in the request, so there is nothing for Slack to create or share. The call exists to be refused, and after the sunset it is refused before any argument is examined at all."),
 ("Can I get an extension, or does an old app still work?",
  "No. The 16 May 2024 deprecation blocked apps created after 8 May 2024 immediately, and the 12 November 2025 sunset applied to every remaining app regardless of age. The date moved once, from 11 March 2025, and then did not move again."),
 ("What is the smallest possible migration?",
  "Three calls: files.getUploadURLExternal with filename and the exact byte length, an upload of the raw bytes to the returned upload_url, then files.completeUploadExternal with the file id and a channel ID. Prefer filesUploadV2 or files_upload_v2, which sequence all three and retry sensibly."),
 ("Why did my migration upload files that appear nowhere?",
  "The third call did not happen, or it happened without a channel_id. A file registered by files.completeUploadExternal but never shared exists in Slack and appears in no conversation, so a half-migrated caller produces orphans rather than errors."),
 ("Why does the script restrict files.list by user?",
  "Because unrestricted it returns every file the token can see, including files uploaded by humans and by other apps. Those would date the history to yesterday and hide the fact that your app has uploaded nothing since the cutover. auth.test supplies the bot user ID to filter on."),
],
"related": [
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
 ("/slack/public-file-links-exposed/", "files readable without Slack at all"),
 ("/slack/users-read-email-missing/", "a field that is absent rather than wrong"),
],
"citations": [CITE_FILES_UPLOAD, CITE_GET_UPLOAD_URL, CITE_COMPLETE_UPLOAD, CITE_UPLOAD_CHANGELOG],
},

{
"slug": "users-read-email-missing",
"title": "Every Slack profile has a null email and nothing errored",
"description": "users:read returns profiles with no email at all. The address needs users:read.email, a separate scope, and its absence is a missing key rather than an error.",
"h1": "every Slack profile has a null email and nothing errored",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack users.list email null", "users:read.email scope",
             "slack profile email missing", "users.lookupByEmail users_not_found",
             "slack user sync no email"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The nightly user sync has been green for four months. It reads every member out of Slack, writes them to the warehouse, and joins them against the HR system on email. The join has matched nothing since the day it shipped, because every row it wrote has <code>email = null</code> &mdash; and <code>users.list</code> returned <code>ok: true</code>, with complete-looking profiles, every single night.",
"short_answer": """<p>Page <code>users.list</code>, count the members who are neither deleted nor bots, and count how many of those have a truthy <code>profile.email</code>. Zero out of several hundred is not a data problem: it is <code>users:read.email</code> missing from the token.</p>
<p>Confirm it on the same response by reading the <code>X-OAuth-Scopes</code> header, which lists what this token actually holds. The repair is to add <code>users:read.email</code> to Bot Token Scopes, reinstall the app, and replace the deployed token &mdash; adding a scope in the app config changes nothing about the token already in production.</p>""",
"problem": """<p>Every other scope failure in Slack announces itself. Ask for something the token cannot do and you get <code>ok: false</code> with <code>error: missing_scope</code>, plus <code>needed</code> and <code>provided</code> naming the exact fix. This one does not. <code>users:read</code> grants profiles; the email address is withheld from those profiles by a second scope, and the way it is withheld is by leaving the key out.</p>
<p>A missing key is not an error in any language your sync is written in. <code>profile.get("email")</code> is <code>None</code>. <code>profile.email</code> is <code>undefined</code>. Both flow straight into the row, the insert succeeds, the job exits zero, and the dashboard is green. The only visible symptom is downstream and much later: a join that returns no rows, an onboarding email that never sends, a mapping table that stays empty.</p>
<p>It survives review, too. The profile object that comes back is genuinely rich &mdash; display name, real name, title, avatars in six sizes, timezone &mdash; so a developer inspecting one member sees a full record and concludes the API is working. It is working. It is answering the question the token was allowed to ask.</p>""",
"why": """<p><strong>Email is deliberately a separate grant.</strong> <code>users:read</code> is the profile scope; <code>users:read.email</code> is the address. Slack split them because an app that needs to render a member list does not need everyone's email, and admins approving an install can see the difference.</p>
<p><strong>Nothing errors, because nothing was refused.</strong> The response is a valid, complete answer to a request from a token without that grant. There is no <code>needed</code> field to read and no exception to catch, which is what makes this the quietest scope failure in the API.</p>
<p><strong>The lookup direction fails just as quietly.</strong> <code>users.lookupByEmail</code> without the scope returns <code>users_not_found</code> for an address you know exists &mdash; an answer that reads like "no such person" rather than "you may not ask". Code that treats that as a soft miss will create duplicate accounts rather than raise.</p>
<p><strong>The scope alone does not guarantee a value.</strong> Some workspaces and many Grid orgs hide email by admin policy, and guest accounts may have none to show. So assert per member, not once per run: the correct post-fix state is "almost every human has an email", not "the scope is present".</p>
<p><strong>Adding the scope requires a reinstall.</strong> The token in production was minted with the grant it had at install time. Editing Bot Token Scopes changes what the <em>next</em> install requests. Until someone reinstalls and swaps the deployed token, the census will read exactly the same.</p>""",
"steps": [
 {"h": "Page users.list rather than reading the first hundred",
  "body": """<p><code>users.list?limit=200</code> and follow <code>response_metadata.next_cursor</code> until it is empty. A single page in a large workspace can be all bots and deactivated accounts, which produces a census of zero humans and no conclusion at all.</p>"""},
 {"h": "Count humans, not members",
  "body": """<p>Exclude <code>deleted</code>, <code>is_bot</code>, and <code>USLACKBOT</code>. Bots have no email by definition and deactivated accounts often lose theirs, so leaving them in the denominator turns a clean finding into a plausible-looking ratio.</p>"""},
 {"h": "Read X-OAuth-Scopes off the same response",
  "body": """<p>The header lists the scopes this token actually holds. Reading it from the response you are judging &mdash; rather than from the app configuration page, or from a list someone pasted into a ticket &mdash; is the difference between diagnosing the deployed token and diagnosing the intended one.</p>"""},
 {"h": "Separate none from some",
  "body": """<p>Zero emails with the scope absent is the finding. A handful missing out of hundreds is not: those are guests, unconfirmed accounts or admin-hidden addresses, and adding a scope will not change them. Reporting the second as the first sends a team through a reinstall that fixes nothing.</p>"""},
 {"h": "Confirm from the other direction",
  "body": """<p><code>users.lookupByEmail?email=</code> with an address you know is in the workspace. <code>missing_scope</code>, or a persistent <code>users_not_found</code> for a member you can see in the census, corroborates the finding without needing any write anywhere.</p>"""},
 {"h": "Add the scope, reinstall, replace the token",
  "body": """<p>All three, in that order. Marketplace submissions need a written justification for this scope, so budget for that if the app is distributed. Then re-run the census and assert per member rather than trusting the grant.</p>"""},
],
"verify": """<p>After the reinstall and the token swap, re-run. The census should flip from none to nearly all, and the header should list the scope.</p>
<pre><code class="language-bash">python3 slack_email_scope_audit.py
# complete   412 of 418 humans have an email; users:read.email is granted</code></pre>""",
"code_intro": "One paginated read of <code>users.list</code>, plus the <code>X-OAuth-Scopes</code> header off the same response. Both classifiers are pure: <code>parse_scopes</code> turns the header into a set, and <code>verdict</code> does the census and decides whether the emails are missing because of the grant or in spite of it.",
"py_file": "slack_email_scope_audit.py",
"py": '''"""Decide whether Slack profiles have no email, or the token may not see it.

Read only. GET requests and nothing else: users:read is enough to run this, and
whether users:read.email is present is the thing being measured. The repair is a
scope change and a reinstall, and is printed rather than performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_email_scope_audit")

API = "https://slack.com/api/"
EMAIL_SCOPE = "users:read.email"


def parse_scopes(header):
    """Turn an X-OAuth-Scopes header into a set. Pure.

    Slack sends a comma separated list, occasionally with spaces after the
    commas and occasionally absent altogether on a cached or proxied response.
    """
    if not header:
        return set()
    return {s.strip() for s in header.split(",") if s.strip()}


def verdict(members, scopes):
    """Census the members and decide what the missing emails mean. Pure.

    `members` is the users.list array, `scopes` the set from X-OAuth-Scopes.
    Bots and deactivated accounts are excluded from the denominator: they have
    no email to show, and counting them turns a clean finding into a ratio.
    """
    humans = [m for m in members
              if not m.get("deleted") and not m.get("is_bot")
              and m.get("id") != "USLACKBOT"]
    total = len(humans)
    if not total:
        return ("no-humans",
                "no active human members in the page(s) read, so there is nothing "
                "to census. Page further before concluding anything.")

    with_email = sum(1 for m in humans if (m.get("profile") or {}).get("email"))
    granted = EMAIL_SCOPE in scopes

    if with_email == 0 and not granted:
        return ("scope-missing",
                "0 of %d humans have an email and %s is not on this token. The "
                "field is withheld, not absent: nothing errored because nothing "
                "was refused." % (total, EMAIL_SCOPE))
    if with_email == 0:
        return ("scope-granted-none-visible",
                "0 of %d humans have an email even though %s is granted. That is "
                "admin policy or Grid restriction, not the scope, and no reinstall "
                "will change it." % (total, EMAIL_SCOPE))
    if with_email < total:
        return ("partial",
                "%d of %d humans have an email%s. Guests, unconfirmed accounts and "
                "admin-hidden addresses look exactly like this, so assert per "
                "member rather than per run."
                % (with_email, total,
                   "" if granted else "; note %s is absent, so something other "
                   "than this token supplied them" % EMAIL_SCOPE))
    return ("complete",
            "%d of %d humans have an email; %s is granted"
            % (with_email, total, EMAIL_SCOPE))


def page_users(session, limit, max_pages):
    """Walk users.list, keeping the scope header from the last response."""
    members, cursor, scopes, pages = [], "", set(), 0
    while pages < max_pages:
        params = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        r = session.get(API + "users.list", params=params, timeout=60)
        scopes = parse_scopes(r.headers.get("X-OAuth-Scopes"))
        body = r.json()
        if body.get("ok") is not True:
            return members, scopes, body
        members.extend(body.get("members") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "").strip()
        pages += 1
        if not cursor:
            break
    return members, scopes, {"ok": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=200, help="page size (default 200)")
    ap.add_argument("--max-pages", type=int, default=20,
                    help="stop after this many pages (default 20)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (users:read is enough to run the census)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    members, scopes, last = page_users(s, args.limit, args.max_pages)
    if last.get("ok") is not True:
        log.error("users.list answered 200 with ok: false, error=%s", last.get("error"))
        return 2

    state, detail = verdict(members, scopes)
    if state in ("complete", "no-humans"):
        log.info("%-26s %s", state, detail)
    else:
        log.warning("%-26s %s", state, detail)

    if state == "scope-missing":
        log.warning("  granted: %s", ", ".join(sorted(scopes)) or "<no header on the response>")
        log.warning("  repair: add %s to Bot Token Scopes, reinstall the app, and "
                    "replace the deployed token", EMAIL_SCOPE)
        log.warning("  the token in production keeps the grant it was minted with; "
                    "editing the app config alone changes nothing")
    elif state == "scope-granted-none-visible":
        log.warning("  repair: ask a workspace admin whether email visibility is "
                    "restricted; the scope is already there")
    elif state == "partial":
        log.warning("  repair: none at the scope level. Handle a missing email "
                    "per member rather than failing the run")

    log.info("%d member(s) read, verdict %s", len(members), state)
    return 1 if state in ("scope-missing", "scope-granted-none-visible") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-email-scope-audit.mjs",
"js": '''/**
 * Decide whether Slack profiles have no email, or the token may not see it.
 *
 * Read only. GET requests and nothing else: users:read is enough to run this,
 * and whether users:read.email is present is the thing being measured. The
 * repair is a scope change and a reinstall, and is printed rather than done.
 */
const API = 'https://slack.com/api/';
export const EMAIL_SCOPE = 'users:read.email';

/**
 * Turn an X-OAuth-Scopes header into a Set. Pure. Slack sends a comma separated
 * list, sometimes with spaces, and sometimes not at all on a proxied response.
 */
export function parseScopes(header) {
  if (!header) return new Set();
  return new Set(header.split(',').map((s) => s.trim()).filter(Boolean));
}

/**
 * Census the members and decide what the missing emails mean. Pure.
 * Bots and deactivated accounts are excluded from the denominator: they have no
 * email to show, and counting them turns a clean finding into a ratio.
 */
export function verdict(members, scopes) {
  const humans = members.filter(
    (m) => !m.deleted && !m.is_bot && m.id !== 'USLACKBOT');
  const total = humans.length;
  if (!total) {
    return ['no-humans',
      'no active human members in the page(s) read, so there is nothing to ' +
      'census. Page further before concluding anything.'];
  }

  const withEmail = humans.filter((m) => m.profile?.email).length;
  const granted = scopes.has(EMAIL_SCOPE);

  if (withEmail === 0 && !granted) {
    return ['scope-missing',
      `0 of ${total} humans have an email and ${EMAIL_SCOPE} is not on this ` +
      'token. The field is withheld, not absent: nothing errored because ' +
      'nothing was refused.'];
  }
  if (withEmail === 0) {
    return ['scope-granted-none-visible',
      `0 of ${total} humans have an email even though ${EMAIL_SCOPE} is granted. ` +
      'That is admin policy or Grid restriction, not the scope, and no reinstall ' +
      'will change it.'];
  }
  if (withEmail < total) {
    const note = granted ? ''
      : `; note ${EMAIL_SCOPE} is absent, so something other than this token supplied them`;
    return ['partial',
      `${withEmail} of ${total} humans have an email${note}. Guests, unconfirmed ` +
      'accounts and admin-hidden addresses look exactly like this, so assert per ' +
      'member rather than per run.'];
  }
  return ['complete',
    `${withEmail} of ${total} humans have an email; ${EMAIL_SCOPE} is granted`];
}

async function pageUsers(token, limit, maxPages) {
  const members = [];
  let cursor = '';
  let scopes = new Set();
  let pages = 0;
  while (pages < maxPages) {
    const url = new URL(API + 'users.list');
    url.searchParams.set('limit', String(limit));
    if (cursor) url.searchParams.set('cursor', cursor);
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    scopes = parseScopes(res.headers.get('x-oauth-scopes'));
    const body = await res.json();
    if (body.ok !== true) return { members, scopes, last: body };
    members.push(...(body.members ?? []));
    cursor = (body.response_metadata?.next_cursor ?? '').trim();
    pages += 1;
    if (!cursor) break;
  }
  return { members, scopes, last: { ok: true } };
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (users:read is enough to run the census)');
    process.exitCode = 2;
    return;
  }

  const args = process.argv.slice(2);
  const li = args.indexOf('--limit');
  const pi = args.indexOf('--max-pages');
  const limit = li === -1 ? 200 : Number(args[li + 1]);
  const maxPages = pi === -1 ? 20 : Number(args[pi + 1]);

  const { members, scopes, last } = await pageUsers(token, limit, maxPages);
  if (last.ok !== true) {
    console.error(`users.list answered 200 with ok: false, error=${last.error}`);
    process.exitCode = 2;
    return;
  }

  const [state, detail] = verdict(members, scopes);
  if (state === 'complete' || state === 'no-humans') {
    console.log(`${state.padEnd(26)} ${detail}`);
  } else {
    console.warn(`${state.padEnd(26)} ${detail}`);
  }

  if (state === 'scope-missing') {
    console.warn(`  granted: ${[...scopes].sort().join(', ') || '<no header on the response>'}`);
    console.warn(`  repair: add ${EMAIL_SCOPE} to Bot Token Scopes, reinstall the app, ` +
                 'and replace the deployed token');
    console.warn('  the token in production keeps the grant it was minted with; ' +
                 'editing the app config alone changes nothing');
  } else if (state === 'scope-granted-none-visible') {
    console.warn('  repair: ask a workspace admin whether email visibility is ' +
                 'restricted; the scope is already there');
  } else if (state === 'partial') {
    console.warn('  repair: none at the scope level. Handle a missing email per ' +
                 'member rather than failing the run');
  }

  console.log(`${members.length} member(s) read, verdict ${state}`);
  process.exitCode = ['scope-missing', 'scope-granted-none-visible'].includes(state) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases decide whether this audit is useful or merely noisy. All emails missing with the scope absent is the finding. A few missing out of hundreds, scope present, is ordinary workspace life &mdash; guests and hidden addresses &mdash; and must come back as its own state, because the repair for it is not a reinstall.",
"test_py_file": "test_slack_email_scope_audit.py",
"test_py": '''from slack_email_scope_audit import parse_scopes, verdict


def human(uid, email=None):
    profile = {"real_name": "A Person"}
    if email:
        profile["email"] = email
    return {"id": uid, "deleted": False, "is_bot": False, "profile": profile}


def test_no_emails_and_no_scope_is_the_finding():
    members = [human("U1"), human("U2")]
    state, detail = verdict(members, {"users:read"})
    assert state == "scope-missing"
    assert "0 of 2" in detail


def test_no_emails_with_the_scope_is_not_a_scope_problem():
    members = [human("U1"), human("U2")]
    state, detail = verdict(members, {"users:read", "users:read.email"})
    assert state == "scope-granted-none-visible"
    assert "admin policy" in detail


def test_a_few_missing_is_ordinary_and_says_so():
    members = [human("U1", "a@example.com"), human("U2")]
    state, detail = verdict(members, {"users:read", "users:read.email"})
    assert state == "partial"
    assert "per member" in detail


def test_every_human_with_an_email_is_complete():
    members = [human("U1", "a@example.com"), human("U2", "b@example.com")]
    assert verdict(members, {"users:read.email"})[0] == "complete"


def test_bots_and_deactivated_accounts_are_not_in_the_denominator():
    members = [
        human("U1", "a@example.com"),
        {"id": "U2", "deleted": True, "is_bot": False, "profile": {}},
        {"id": "B1", "deleted": False, "is_bot": True, "profile": {}},
        {"id": "USLACKBOT", "deleted": False, "is_bot": False, "profile": {}},
    ]
    state, detail = verdict(members, {"users:read.email"})
    assert state == "complete"
    assert "1 of 1" in detail


def test_a_page_of_only_bots_yields_no_verdict():
    members = [{"id": "B1", "deleted": False, "is_bot": True, "profile": {}}]
    assert verdict(members, set())[0] == "no-humans"


def test_scope_header_parsing_survives_spaces_and_absence():
    assert parse_scopes("users:read, users:read.email ,team:read") == {
        "users:read", "users:read.email", "team:read"}
    assert parse_scopes(None) == set()
    assert parse_scopes("") == set()
''',
"test_js_file": "slack-email-scope-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseScopes, verdict } from './slack-email-scope-audit.mjs';

function human(id, email) {
  const profile = { real_name: 'A Person' };
  if (email) profile.email = email;
  return { id, deleted: false, is_bot: false, profile };
}

test('no emails and no scope is the finding', () => {
  const [state, detail] = verdict([human('U1'), human('U2')], new Set(['users:read']));
  assert.equal(state, 'scope-missing');
  assert.match(detail, /0 of 2/);
});

test('no emails with the scope is not a scope problem', () => {
  const [state, detail] = verdict(
    [human('U1'), human('U2')], new Set(['users:read', 'users:read.email']));
  assert.equal(state, 'scope-granted-none-visible');
  assert.match(detail, /admin policy/);
});

test('a few missing is ordinary and says so', () => {
  const [state, detail] = verdict(
    [human('U1', 'a@example.com'), human('U2')],
    new Set(['users:read', 'users:read.email']));
  assert.equal(state, 'partial');
  assert.match(detail, /per member/);
});

test('every human with an email is complete', () => {
  const members = [human('U1', 'a@example.com'), human('U2', 'b@example.com')];
  assert.equal(verdict(members, new Set(['users:read.email']))[0], 'complete');
});

test('bots and deactivated accounts are not in the denominator', () => {
  const members = [
    human('U1', 'a@example.com'),
    { id: 'U2', deleted: true, is_bot: false, profile: {} },
    { id: 'B1', deleted: false, is_bot: true, profile: {} },
    { id: 'USLACKBOT', deleted: false, is_bot: false, profile: {} },
  ];
  const [state, detail] = verdict(members, new Set(['users:read.email']));
  assert.equal(state, 'complete');
  assert.match(detail, /1 of 1/);
});

test('a page of only bots yields no verdict', () => {
  const members = [{ id: 'B1', deleted: false, is_bot: true, profile: {} }];
  assert.equal(verdict(members, new Set())[0], 'no-humans');
});

test('scope header parsing survives spaces and absence', () => {
  assert.deepEqual(
    [...parseScopes('users:read, users:read.email ,team:read')].sort(),
    ['team:read', 'users:read', 'users:read.email']);
  assert.equal(parseScopes(null).size, 0);
  assert.equal(parseScopes('').size, 0);
});
''',
"faq": [
 ("Why is there no missing_scope error for this?",
  "Because nothing was refused. users:read entitles the token to profiles, and the response is a complete, valid profile for that grant with the email key simply not included. missing_scope is returned when a method is refused; here the method succeeded and answered a narrower question than you thought you asked."),
 ("Does users:read.email work on its own?",
  "No. It extends the profile read rather than replacing it, so the token needs users:read as well. Add both, and remember that the email scope needs a written justification if the app is submitted to the Marketplace."),
 ("I added the scope and nothing changed. Why?",
  "The deployed token still holds the grant it was minted with at install time. Editing Bot Token Scopes only affects what the next install requests, so the sequence is: add the scope, reinstall the app, then replace the token in your configuration. Skipping the third step is the usual reason a fix appears not to work."),
 ("Why does users.lookupByEmail say users_not_found?",
  "Because without the scope the lookup cannot see email addresses to match against, and Slack answers as though no such user exists rather than as though you may not ask. Treat a users_not_found for an address you can verify by hand as evidence of the scope gap, not of a missing member."),
 ("Some members still have no email after the fix. Is that a bug?",
  "Usually not. Guest accounts may have no address, and some workspaces and Grid orgs hide email by admin policy even when the scope is granted. That is why the script reports a partial census as its own state: the repair for it is to handle a missing email per member, not to reinstall again."),
],
"related": [
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/pagination-not-followed/", "next_cursor ignored, so one page is all you see"),
 ("/slack/files-upload-retired/", "a method that has been dead since November 2025"),
],
"citations": [CITE_USERS_LIST, CITE_SCOPES, CITE_USERS_LOOKUP, CITE_TOKENS],
},

{
"slug": "event-subscriptions-auto-disabled",
"title": "Slack disabled event delivery and will not turn it back on",
"description": "Fail more than 95% of deliveries in an hour and Slack switches your event subscriptions off. Recovery is manual, and the Web API never reports the flag.",
"h1": "Slack disabled event delivery and will not turn it back on",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack event subscriptions disabled", "slack stopped sending events",
             "slack bot not responding to mentions", "slack request url 5xx disabled",
             "slack events api retries"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the manifest cross-check needs an app configuration token",
"lead": "There was a two-hour outage on Tuesday. The service came back, the health checks went green, the on-call went to bed. On Thursday somebody asks why the bot has not answered anyone since Tuesday. Slack turned event delivery off during the outage, emailed the app owner about it, and does not turn it back on when you recover &mdash; a human has to click a button that nobody knows exists.",
"short_answer": """<p>Slack watches delivery success. If your app fails more than <strong>95% of delivery attempts in a 60-minute window</strong> it disables the app's event subscriptions and notifies the owner. Slow counts as failed: anything over three seconds, plus SSL errors, redirect loops and every non-2xx.</p>
<p>The Web API does not expose that flag, so the detection is behavioural: read <code>conversations.history</code> in channels the app serves, find the messages that mention it, find the app's own replies, and measure the gap. A run of mentions with no reply after them is the symptom. Then check the app config page, because that is the only place the truth lives.</p>""",
"problem": """<p>The disable is a protection mechanism working exactly as designed, and it is invisible from every angle a developer normally looks. The app is installed. The token authenticates. The bot is still in the channel. Scopes are unchanged. The Request URL, if you curl it, answers instantly. Nothing in the Web API differs by a single field from a healthy app, because the Web API is your app calling Slack and this failure is Slack not calling your app.</p>
<p>The email went to the app owner &mdash; frequently a person who left, or a shared address nobody reads &mdash; and the state itself lives on a configuration page that is visited during setup and essentially never again. So the app sits there, permanently deaf, looking perfectly healthy, until a human notices that the mentions are going unanswered.</p>
<p>Recovery not being automatic is the part that costs the days. Teams assume that fixing the endpoint restores delivery, because that is how every other outage they have ever had behaved. It does not. The subscriptions stay off until someone re-enables them.</p>""",
"why": """<p><strong>Failure is measured by delivery, not by your definition of an error.</strong> A response slower than three seconds is a failed delivery even if the work completed. So is an expired certificate, a redirect chain, and a 502 from a load balancer sitting in front of a healthy app. A deploy that takes an hour can trip the threshold on its own.</p>
<p><strong>The threshold is a rate, so a quiet app trips faster.</strong> 95% of attempts within an hour is easy to reach when the hour contains twenty events. A busy app has more headroom than a quiet one, which is why this bites internal tools hardest.</p>
<p><strong>Retries make it worse before it makes it stop.</strong> Each failed delivery is retried up to three times, so a struggling endpoint receives multiples of its normal traffic during exactly the window in which its success rate is being judged.</p>
<p><strong>The symptom has three causes and they look identical from outside.</strong> Delivery disabled, the handler down, and events never subscribed to in the first place all produce "mentions, no replies". The script reports the shape and refuses to name the cause, because from the workspace side they are genuinely indistinguishable.</p>
<p><strong>This is the boundary of what a token can see, and it is worth being precise about it.</strong> No read method reports whether subscriptions are enabled. <code>apps.manifest.export</code> returns the configuration &mdash; and needs an <em>app configuration token</em>, a different credential class from your bot token &mdash; but it reports what was configured, not whether Slack is currently delivering. Whether your handler verifies <code>X-Slack-Signature</code> or enforces the five-minute timestamp window is entirely inside your process and Slack never reports it at all.</p>""",
"steps": [
 {"h": "Identify the app from the token, not from a config file",
  "body": """<p><code>auth.test</code> returns <code>bot_id</code> and <code>user_id</code>. The first identifies the app's own messages in history; the second is the id that appears inside a mention as <code>&lt;@U...&gt;</code>. Both come from the token in hand, so the audit describes the app that is actually deployed.</p>"""},
 {"h": "Read history in the channels the app is supposed to serve",
  "body": """<p><code>conversations.history?channel=&lt;C...&gt;&amp;limit=200</code> needs <code>channels:history</code> and membership. If it comes back <code>not_in_channel</code> you have a different problem and a different note; membership is a prerequisite for this one, not a finding of it.</p>"""},
 {"h": "Separate triggers from replies",
  "body": """<p>A trigger is a message that mentions the bot and was not written by it. A reply is a message whose <code>bot_id</code> matches <code>auth.test</code>. Everything else in the channel is noise for this purpose, including other apps' messages and threads the bot was never addressed in.</p>"""},
 {"h": "Count the mentions that arrived after the last reply",
  "body": """<p>One unanswered mention is a person typing the bot's name in passing. Three or more, spread over hours, with a reply before them and none after, is the fingerprint. The count matters more than the elapsed time, because a quiet channel can be quiet for ordinary reasons.</p>"""},
 {"h": "Distinguish gone quiet from never spoke",
  "body": """<p>If the app has never posted in a channel where it is repeatedly addressed, the likelier cause is that no events were ever subscribed to, or the Request URL never passed verification. Auto-disable produces a run of replies that stops; never-configured produces silence from the beginning.</p>"""},
 {"h": "Go and look at the app configuration page",
  "body": """<p>This is the step the script cannot do for you. Event Subscriptions is where the disabled state is visible and where it is re-enabled. Fix the endpoint first, then re-enable, then add an uptime check that alerts you long before 95% of an hour's deliveries have failed.</p>"""},
],
"verify": """<p>Re-enable delivery, then mention the app and re-run over the same channels. Every channel should report a reply after its most recent trigger.</p>
<pre><code class="language-bash">python3 slack_event_silence_audit.py C0123ABCDEF C0456GHIJKL
# 2 channel(s) checked, 0 where the app has gone quiet</code></pre>""",
"code_intro": "Two read methods: <code>auth.test</code> once, then <code>conversations.history</code> per channel. Both pure functions do the part that matters &mdash; <code>scan</code> reduces a page of history to four numbers, and <code>verdict</code> decides whether those numbers are evidence of anything. The second one exists mostly to refuse: most channels are quiet for reasons that are nobody's bug.",
"py_file": "slack_event_silence_audit.py",
"py": '''"""Find channels where a Slack app is addressed and has stopped answering.

Read only. GET requests and nothing else: channels:history and membership are
enough. This detects the symptom of disabled event delivery, not the flag: no
read method reports whether Slack is delivering, so the repair ends at the app
configuration page and is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_silence_audit")

API = "https://slack.com/api/"


def scan(messages, bot_id, bot_user_id):
    """Reduce one page of history to the four numbers that matter. Pure.

    A trigger is a message mentioning the bot that the bot did not write. A
    reply is any message carrying the app's own bot_id. `unanswered` counts the
    triggers that arrived after the app last said anything.
    """
    mention = "<@%s>" % bot_user_id
    replies, triggers = [], []
    for m in messages:
        ts = float(m.get("ts") or 0)
        if m.get("bot_id") == bot_id:
            replies.append(ts)
        elif mention in (m.get("text") or ""):
            triggers.append(ts)
    last_reply = max(replies) if replies else None
    last_trigger = max(triggers) if triggers else None
    unanswered = len([t for t in triggers if last_reply is None or t > last_reply])
    return {"replies": len(replies), "triggers": len(triggers),
            "last_reply": last_reply, "last_trigger": last_trigger,
            "unanswered": unanswered}


def verdict(stats, min_triggers=3):
    """Decide whether the silence is evidence. Pure, and mostly a refusal.

    Three different causes produce this shape - delivery disabled by Slack, the
    handler down, and events never subscribed to - and none of them can be told
    apart from inside the workspace. The states name the shape, not the cause.
    """
    if not stats["triggers"]:
        return ("no-triggers",
                "nothing addressed the app in this window, so there is no "
                "evidence either way. Silence is not a finding on its own.")
    if not stats["unanswered"]:
        return ("answering",
                "%d mention(s), and the app replied after the most recent one"
                % stats["triggers"])
    if not stats["replies"]:
        return ("never-answered",
                "%d mention(s) and the app has never posted here. That points at "
                "subscriptions never configured or a Request URL that never "
                "verified, rather than at delivery being switched off."
                % stats["triggers"])
    if stats["unanswered"] >= min_triggers:
        hours = (stats["last_trigger"] - stats["last_reply"]) / 3600.0
        return ("silent",
                "%d mention(s) since the app last replied, spanning %.1f hour(s). "
                "It was answering and then stopped: check whether Slack disabled "
                "event delivery." % (stats["unanswered"], hours))
    return ("too-little-evidence",
            "%d unanswered mention(s), below the %d needed to call it. People "
            "type a bot's name without expecting an answer."
            % (stats["unanswered"], min_triggers))


def get(session, method, **params):
    r = session.get(API + method, params=params, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+", help="channel IDs the app serves (C...)")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages of history per channel (default 200)")
    ap.add_argument("--min-triggers", type=int, default=3,
                    help="unanswered mentions before it counts (default 3)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (channels:history and membership are enough)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    me = get(s, "auth.test")
    if me.get("ok") is not True:
        log.error("auth.test answered 200 with ok: false, error=%s", me.get("error"))
        return 2
    bot_id, bot_user = me.get("bot_id"), me.get("user_id")
    log.info("app is %s (bot_id=%s, mentioned as <@%s>)", me.get("user"), bot_id, bot_user)

    bad = 0
    for cid in args.channels:
        body = get(s, "conversations.history", channel=cid, limit=str(args.limit))
        if body.get("ok") is not True:
            bad += 1
            log.warning("%-20s %-12s history refused: error=%s. Membership and "
                        "channels:history come first; this audit assumes both",
                        "unreadable", cid, body.get("error"))
            continue
        stats = scan(body.get("messages") or [], bot_id, bot_user)
        state, detail = verdict(stats, args.min_triggers)
        line = "%-20s %-12s %s" % (state, cid, detail)
        if state in ("silent", "never-answered"):
            bad += 1
            log.warning(line)
            log.warning("  the Web API cannot tell you whether Slack disabled "
                        "delivery: open Event Subscriptions in the app config")
            log.warning("  repair: fix the endpoint, re-enable delivery by hand, then "
                        "alert on the Request URL before 95%% of an hour fails")
        else:
            log.info(line)

    log.info("%d channel(s) checked, %d where the app has gone quiet",
             len(args.channels), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-silence-audit.mjs",
"js": '''/**
 * Find channels where a Slack app is addressed and has stopped answering.
 *
 * Read only. GET requests and nothing else: channels:history and membership are
 * enough. This detects the symptom of disabled event delivery, not the flag: no
 * read method reports whether Slack is delivering, so the repair ends at the app
 * configuration page and is printed, never performed.
 */
const API = 'https://slack.com/api/';

/**
 * Reduce one page of history to the four numbers that matter. Pure.
 * A trigger is a message mentioning the bot that the bot did not write; a reply
 * is any message carrying the app's own bot_id.
 */
export function scan(messages, botId, botUserId) {
  const mention = `<@${botUserId}>`;
  const replies = [];
  const triggers = [];
  for (const m of messages) {
    const ts = Number(m.ts ?? 0);
    if (m.bot_id === botId) replies.push(ts);
    else if ((m.text ?? '').includes(mention)) triggers.push(ts);
  }
  const lastReply = replies.length ? Math.max(...replies) : null;
  const lastTrigger = triggers.length ? Math.max(...triggers) : null;
  const unanswered = triggers.filter((t) => lastReply === null || t > lastReply).length;
  return {
    replies: replies.length, triggers: triggers.length,
    lastReply, lastTrigger, unanswered,
  };
}

/**
 * Decide whether the silence is evidence. Pure, and mostly a refusal.
 * Delivery disabled, the handler down and events never subscribed to all produce
 * this shape, so the states name the shape and not the cause.
 */
export function verdict(stats, minTriggers = 3) {
  if (!stats.triggers) {
    return ['no-triggers',
      'nothing addressed the app in this window, so there is no evidence either ' +
      'way. Silence is not a finding on its own.'];
  }
  if (!stats.unanswered) {
    return ['answering',
      `${stats.triggers} mention(s), and the app replied after the most recent one`];
  }
  if (!stats.replies) {
    return ['never-answered',
      `${stats.triggers} mention(s) and the app has never posted here. That points ` +
      'at subscriptions never configured or a Request URL that never verified, ' +
      'rather than at delivery being switched off.'];
  }
  if (stats.unanswered >= minTriggers) {
    const hours = (stats.lastTrigger - stats.lastReply) / 3600;
    return ['silent',
      `${stats.unanswered} mention(s) since the app last replied, spanning ` +
      `${hours.toFixed(1)} hour(s). It was answering and then stopped: check ` +
      'whether Slack disabled event delivery.'];
  }
  return ['too-little-evidence',
    `${stats.unanswered} unanswered mention(s), below the ${minTriggers} needed to ` +
    "call it. People type a bot's name without expecting an answer."];
}

async function get(token, method, params = {}) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (channels:history and membership are enough)');
    process.exitCode = 2;
    return;
  }

  const argv = process.argv.slice(2);
  const li = argv.indexOf('--limit');
  const mi = argv.indexOf('--min-triggers');
  const limit = li === -1 ? '200' : argv[li + 1];
  const minTriggers = mi === -1 ? 3 : Number(argv[mi + 1]);
  const channels = argv.filter((a, n) => !a.startsWith('--')
    && argv[n - 1] !== '--limit' && argv[n - 1] !== '--min-triggers');

  if (!channels.length) {
    console.error('usage: node slack-event-silence-audit.mjs C0123ABCDEF [C...]');
    process.exitCode = 2;
    return;
  }

  const me = await get(token, 'auth.test');
  if (me.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${me.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = me.bot_id;
  const botUser = me.user_id;
  console.log(`app is ${me.user} (bot_id=${botId}, mentioned as <@${botUser}>)`);

  let bad = 0;
  for (const cid of channels) {
    const body = await get(token, 'conversations.history', { channel: cid, limit });
    if (body.ok !== true) {
      bad += 1;
      console.warn(`${'unreadable'.padEnd(20)} ${cid.padEnd(12)} history refused: ` +
                   `error=${body.error}. Membership and channels:history come ` +
                   'first; this audit assumes both');
      continue;
    }
    const stats = scan(body.messages ?? [], botId, botUser);
    const [state, detail] = verdict(stats, minTriggers);
    const line = `${state.padEnd(20)} ${cid.padEnd(12)} ${detail}`;
    if (state === 'silent' || state === 'never-answered') {
      bad += 1;
      console.warn(line);
      console.warn('  the Web API cannot tell you whether Slack disabled delivery: ' +
                   'open Event Subscriptions in the app config');
      console.warn('  repair: fix the endpoint, re-enable delivery by hand, then ' +
                   'alert on the Request URL before 95% of an hour fails');
    } else {
      console.log(line);
    }
  }

  console.log(`${channels.length} channel(s) checked, ${bad} where the app has gone quiet`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The state that keeps this audit honest is <code>never-answered</code>. An app that has been addressed forty times and has never once replied is almost certainly not an app whose delivery was disabled &mdash; it is one that was never subscribed to anything. Collapsing the two sends a team to re-enable a switch that was never off.",
"test_py_file": "test_slack_event_silence_audit.py",
"test_py": '''from slack_event_silence_audit import scan, verdict

BOT = "B123"
BOT_USER = "U999"


def msg(ts, text="hello", bot=False):
    m = {"ts": "%d.000100" % ts, "text": text}
    if bot:
        m["bot_id"] = BOT
    return m


def mention(ts):
    return msg(ts, "<@%s> please deploy" % BOT_USER)


def test_scan_separates_triggers_from_replies():
    messages = [mention(100), msg(110, "unrelated chatter"), msg(120, "done", bot=True)]
    stats = scan(messages, BOT, BOT_USER)
    assert stats["triggers"] == 1
    assert stats["replies"] == 1
    assert stats["unanswered"] == 0


def test_the_bots_own_mention_of_itself_is_not_a_trigger():
    messages = [msg(100, "<@%s> was asked" % BOT_USER, bot=True)]
    assert scan(messages, BOT, BOT_USER)["triggers"] == 0


def test_a_run_of_mentions_after_the_last_reply_is_the_finding():
    messages = [msg(1000, "on it", bot=True), mention(5000), mention(9000), mention(13000)]
    state, detail = verdict(scan(messages, BOT, BOT_USER))
    assert state == "silent"
    assert "3 mention(s)" in detail


def test_an_app_that_never_replied_is_a_different_diagnosis():
    messages = [mention(1000), mention(2000), mention(3000), mention(4000)]
    state, detail = verdict(scan(messages, BOT, BOT_USER))
    assert state == "never-answered"
    assert "never configured" in detail


def test_a_reply_after_the_last_mention_is_healthy():
    messages = [mention(1000), msg(1100, "done", bot=True)]
    assert verdict(scan(messages, BOT, BOT_USER))[0] == "answering"


def test_one_unanswered_mention_is_not_enough():
    messages = [msg(1000, "done", bot=True), mention(2000)]
    assert verdict(scan(messages, BOT, BOT_USER))[0] == "too-little-evidence"


def test_a_quiet_channel_is_not_evidence():
    messages = [msg(1000, "morning"), msg(2000, "morning")]
    assert verdict(scan(messages, BOT, BOT_USER))[0] == "no-triggers"


def test_the_threshold_is_adjustable():
    messages = [msg(1000, "done", bot=True), mention(2000), mention(3000)]
    assert verdict(scan(messages, BOT, BOT_USER), min_triggers=2)[0] == "silent"
''',
"test_js_file": "slack-event-silence-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scan, verdict } from './slack-event-silence-audit.mjs';

const BOT = 'B123';
const BOT_USER = 'U999';

function msg(ts, text = 'hello', bot = false) {
  const m = { ts: `${ts}.000100`, text };
  if (bot) m.bot_id = BOT;
  return m;
}

const mention = (ts) => msg(ts, `<@${BOT_USER}> please deploy`);

test('scan separates triggers from replies', () => {
  const stats = scan([mention(100), msg(110, 'unrelated chatter'), msg(120, 'done', true)],
    BOT, BOT_USER);
  assert.equal(stats.triggers, 1);
  assert.equal(stats.replies, 1);
  assert.equal(stats.unanswered, 0);
});

test('the bots own mention of itself is not a trigger', () => {
  const messages = [msg(100, `<@${BOT_USER}> was asked`, true)];
  assert.equal(scan(messages, BOT, BOT_USER).triggers, 0);
});

test('a run of mentions after the last reply is the finding', () => {
  const messages = [msg(1000, 'on it', true), mention(5000), mention(9000), mention(13000)];
  const [state, detail] = verdict(scan(messages, BOT, BOT_USER));
  assert.equal(state, 'silent');
  assert.match(detail, /3 mention\\(s\\)/);
});

test('an app that never replied is a different diagnosis', () => {
  const messages = [mention(1000), mention(2000), mention(3000), mention(4000)];
  const [state, detail] = verdict(scan(messages, BOT, BOT_USER));
  assert.equal(state, 'never-answered');
  assert.match(detail, /never configured/);
});

test('a reply after the last mention is healthy', () => {
  const messages = [mention(1000), msg(1100, 'done', true)];
  assert.equal(verdict(scan(messages, BOT, BOT_USER))[0], 'answering');
});

test('one unanswered mention is not enough', () => {
  const messages = [msg(1000, 'done', true), mention(2000)];
  assert.equal(verdict(scan(messages, BOT, BOT_USER))[0], 'too-little-evidence');
});

test('a quiet channel is not evidence', () => {
  const messages = [msg(1000, 'morning'), msg(2000, 'morning')];
  assert.equal(verdict(scan(messages, BOT, BOT_USER))[0], 'no-triggers');
});

test('the threshold is adjustable', () => {
  const messages = [msg(1000, 'done', true), mention(2000), mention(3000)];
  assert.equal(verdict(scan(messages, BOT, BOT_USER), 2)[0], 'silent');
});
''',
"faq": [
 ("What exactly trips the disable?",
  "Failing more than 95% of delivery attempts inside a 60-minute window. Counted failures include any non-2xx, responses slower than three seconds, SSL validation errors and too many redirects. A quiet app trips more easily than a busy one, because the percentage is over attempts rather than over time."),
 ("Does delivery resume when my service recovers?",
  "No, and that is the part that costs days. Slack disables the subscriptions and notifies the app owner by email; re-enabling is a manual action on the Event Subscriptions page in the app configuration. Fixing the endpoint alone changes nothing."),
 ("Can a script read whether delivery is disabled?",
  "Not with a bot token. No Web API read method exposes the flag. apps.manifest.export can show what is configured, but it needs an app configuration token, which is a different credential class, and it still reports configuration rather than live delivery state. That is why this note detects the symptom in the workspace instead."),
 ("Could the silence mean something else?",
  "Yes, and the script says so rather than guessing. Delivery disabled, a handler that is down, and events that were never subscribed to all look identical from inside the workspace. The one distinction it can draw is between an app that was answering and stopped, and one that never answered at all."),
 ("How do I stop this happening again?",
  "Ack within milliseconds and do the work asynchronously, so a slow dependency cannot turn into a failed delivery. Then put an external uptime check on the Request URL that alerts on the first sustained failures, long before 95% of an hour has failed, and make sure the app owner address on the configuration is a mailbox somebody reads."),
],
"related": [
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
 ("/slack/duplicate-messages-no-dedupe/", "the same message posted three times"),
 ("/slack/enterprise-id-not-stored/", "installs keyed on team_id alone collide"),
],
"citations": [CITE_EVENTS, CITE_HISTORY, CITE_APP_MENTION, CITE_MANIFEST],
},

]
