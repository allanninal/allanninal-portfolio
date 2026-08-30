#!/usr/bin/env python3
"""/slack/ field notes, batch F — the writing.

Four notes about the *configuration* of a Slack app rather than the health of
its runtime token, and none of them reaches its answer the way the token notes
do. One decides which permission era an install belongs to by reading the
vocabulary of its grant, and concludes that no scope can be added at all. One
proves a write capability without writing, by asking the only read method that
accepts the same class of credential. One finds nothing broken anywhere and
derives the severity from how many workspaces have installed the app. And one
is about a credential whose death does not break the app at all, only the
audit, which must then say so instead of reporting clean.

Read-only throughout. GET requests only, and for Slack that means Web API
methods that read: nothing here posts, invites, deletes or edits. Every script
reports what it found and prints the repair for a human to run.
"""

CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_TOKENS = ("Token types — Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_WEB_API = ("Using the Web API — Slack Docs",
                "https://docs.slack.dev/apis/web-api/")
CITE_SOCKET = ("Socket Mode — Slack Docs",
               "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_CONNECTIONS_OPEN = ("apps.connections.open method reference — Slack Docs",
                         "https://docs.slack.dev/reference/methods/apps.connections.open")
CITE_EVENT_AUTHZ = ("apps.event.authorizations.list method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/apps.event.authorizations.list")
CITE_EVENTS_API = ("Events API — Slack Docs",
                   "https://docs.slack.dev/apis/events-api/")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference — Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_TOKENS_ROTATE = ("tooling.tokens.rotate method reference — Slack Docs",
                      "https://docs.slack.dev/reference/methods/tooling.tokens.rotate")
CITE_ROTATION = ("Using token rotation — Slack Docs",
                 "https://docs.slack.dev/authentication/using-token-rotation")
CITE_GRID = ("Enterprise Grid — Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")

GUIDES = [

{
"slug": "classic-app-coarse-scopes",
"title": "Classic Slack app: the scope list says bot, client, read",
"description": "A pre-2020 Slack app holds coarse scopes no reinstall can change. Read X-OAuth-Scopes and the vocabulary alone tells you which era you are in.",
"h1": "Classic Slack app: the scope list says bot, client, read",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack classic app scopes", "slack granular permissions migration",
             "chat:write:bot deprecated", "x-oauth-scopes bot client read",
             "slack app cannot add scope"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You go to add one scope. The OAuth &amp; Permissions page does not offer the scope picker you have seen in every tutorial, the code references <code>chat:write:bot</code> which the documentation says does not exist, and the header on every API response reads <code>bot,client,identify,post,read</code>. Nothing is broken yet. What is broken is the assumption that this app can be fixed by adding something to it.",
"short_answer": """<p>Apps created before the 2020 granular-permissions migration hold <strong>coarse</strong> scopes: bare words like <code>bot</code>, <code>client</code>, <code>read</code>, <code>post</code>, <code>identify</code>, each granting a broad slice of the workspace. Granular apps hold namespaced scopes like <code>channels:read</code> and <code>chat:write</code>. The two vocabularies <strong>cannot be mixed</strong>, and Slack does not upgrade a classic app in place.</p>
<p>So the diagnosis is a vocabulary check, not an error check. The script below makes one <code>auth.test</code> call and reads the grant out of the <code>X-OAuth-Scopes</code> response header, then sorts every scope into three groups: coarse names from the old model, intermediate names the migration retired, and current granular names. A single bare word that is not <code>incoming-webhook</code> or <code>commands</code> settles it. The repair it prints is a new app and a cutover, because there is no other one.</p>""",
"problem": """<p>The confusing part is that a classic app works. It authenticates, it posts, it reads channels, and it has probably done so for years. The only symptoms are negative ones: a scope you cannot add, a picker that is not there, a documentation page that describes a scope your token does not have and cannot get.</p>
<p>The second symptom is the retired middle generation. Between the coarse model and today's model there was a set of qualified write scopes &mdash; <code>chat:write:bot</code> and <code>chat:write:user</code> most visibly &mdash; that let you say <em>who</em> a message was posted as. The migration collapsed them into <code>chat:write</code> plus <code>chat:write.customize</code> for the case where you override the display name or icon. Code that still names the old ones is not going to fail loudly; it is going to fail at install time, in a redirect, with a scope error that nobody reads.</p>
<p>And the third is that classic apps still have the RTM API. That is why they survive: RTM was retired for new apps, so any app still speaking it is by definition classic, and any team that tried to move to the Events API discovered they could not simply add the scopes. The app has to be rebuilt. That is a project, so it gets postponed, and the postponement is invisible until the day someone needs a feature that only exists on the granular side.</p>""",
"why": """<p><strong>The grant is in a header, not the body.</strong> Every authenticated Web API response carries <code>X-OAuth-Scopes</code> with the complete list of what this token holds. You do not need a failing call to see it, and you do not need admin access to the app configuration page. One <code>auth.test</code> is enough, and <code>auth.test</code> itself requires no scopes.</p>
<p><strong>A colon is the tell.</strong> Granular scopes are namespaced: <code>channels:read</code>, <code>files:write</code>, <code>users:read.email</code>. Coarse scopes are bare words. There are exactly two bare names in the granular world &mdash; <code>incoming-webhook</code> and <code>commands</code> &mdash; so a bare scope that is neither of those is a classic app with no further analysis required.</p>
<p><strong>The two models cannot coexist.</strong> This is what makes the finding terminal rather than a to-do. Slack will not let a classic app request a granular scope, so the usual repair for a permissions problem &mdash; add the scope, reinstall, replace the token &mdash; has no effect here. Reporting "add <code>channels:history</code>" to a classic app is worse than reporting nothing, because someone will spend an afternoon looking for the button.</p>
<p><strong>A retired scope name is a different, smaller finding.</strong> An app holding <code>chat:write:bot</code> is granular-era but was minted before the collapse. That one <em>is</em> fixable in place: change the requested scope to <code>chat:write</code>, reinstall, done. Lumping it in with the classic finding sends a team on a rebuild they do not need, so the script keeps the two apart.</p>
<p><strong>Migration means two apps running at once.</strong> There is no in-place upgrade, so the honest plan is: create the new app from a manifest, install it alongside the old one, move traffic, then uninstall the classic app. Both apps in the same workspace at the same time is the point &mdash; it is what makes the cutover reversible.</p>""",
"steps": [
 {"h": "Read the header rather than the settings page",
  "body": """<p>You may not have admin access to the app configuration, and the page does not show the grant as a list anyway. One <code>auth.test</code> with the deployed token returns the complete granted scope set in <code>X-OAuth-Scopes</code>, which is the ground truth: it is what the token actually holds, not what the manifest asked for.</p>"""},
 {"h": "Sort the grant into three vocabularies",
  "body": """<p>Coarse, retired, and current. The classification is mechanical and needs no network, which is why it is the part the tests cover: a bare word that is not <code>incoming-webhook</code> or <code>commands</code> goes in the coarse bucket, a name in the retired table goes in the retired bucket, and everything else is current.</p>"""},
 {"h": "Treat one coarse scope as the whole answer",
  "body": """<p>You do not need a majority. Because the models cannot be mixed, a single <code>bot</code> or <code>read</code> in the grant means the installation is classic and every granular scope in the same list is a reporting artefact rather than a real grant. Stop analysing and print the migration.</p>"""},
 {"h": "Separate the write scopes that were merely collapsed",
  "body": """<p><code>chat:write:bot</code> and <code>chat:write:user</code> became <code>chat:write</code>; <code>files:write:user</code> became <code>files:write</code>. If those are the only stale names, the app is granular and the repair is one edit to the requested scope list plus a reinstall. Add <code>chat:write.customize</code> only if the code overrides <code>username</code> or <code>icon_emoji</code>.</p>"""},
 {"h": "Plan a second app, not a reinstall",
  "body": """<p>Write the new app's manifest with the granular scopes the code actually needs, install it into the same workspace, point a copy of the service at the new token, and verify. Only then uninstall the classic app. Nothing about this is reversible if you uninstall first.</p>"""},
 {"h": "Budget for the RTM rewrite in the same change",
  "body": """<p>If the app is on RTM it has to move to the Events API or Socket Mode as part of the migration, because the new granular app will not have RTM. That is usually the largest part of the work and the reason the migration keeps slipping, so it belongs in the estimate rather than in the surprise.</p>"""},
],
"verify": """<p>After the cutover, run the same script against the new token. The grant should classify as granular with no coarse and no retired names, and the verdict line should be the only one the script prints.</p>
<pre><code class="language-bash">SLACK_BOT_TOKEN=xoxb-... python3 slack_classic_scope_audit.py
# granular  12 granular scope(s), no coarse or retired names</code></pre>""",
"code_intro": "One GET, and the answer arrives in a response header rather than in the body &mdash; which is unusual enough that the fetch returns both. Three pure functions do the actual work: <code>grant_buckets</code> sorts the raw header into the three vocabularies, <code>classify_grant</code> names the era, and <code>migration_verdict</code> crosses that with what <code>auth.test</code> said about the credential, because a scope list means nothing if the token behind it is dead.",
"py_file": "slack_classic_scope_audit.py",
"py": '''"""Decide which Slack permission era an installed app belongs to.

Read only. One GET, and the finding is in the response header rather than the
body: X-OAuth-Scopes carries the complete grant. The repair for a classic app is
a second app, so the script prints the migration rather than suggesting a
reinstall that cannot work.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_classic_scope_audit")

API = "https://slack.com/api/"

# The only two granular scopes that legitimately carry no colon. Any other bare
# word in the grant is a coarse scope from the pre-2020 model.
GRANULAR_BARE = frozenset({"incoming-webhook", "commands"})

# Intermediate scopes the granular migration retired, and what replaced them.
RETIRED = {
    "chat:write:bot": "chat:write",
    "chat:write:user": "chat:write",
    "files:write:user": "files:write",
}


def grant_buckets(header):
    """Sort a raw X-OAuth-Scopes header into three vocabularies. Pure.

    Returns {"coarse": [...], "retired": [...], "granular": [...]}.
    """
    scopes = [s.strip() for s in str(header or "").split(",") if s.strip()]
    buckets = {"coarse": [], "retired": [], "granular": []}
    for scope in scopes:
        if scope in RETIRED:
            buckets["retired"].append(scope)
        elif ":" not in scope and scope not in GRANULAR_BARE:
            buckets["coarse"].append(scope)
        else:
            buckets["granular"].append(scope)
    return buckets


def classify_grant(header):
    """Name the permission era this grant belongs to. Pure. -> (state, detail)"""
    if not str(header or "").strip():
        return ("no-scope-header",
                "the response carried no X-OAuth-Scopes header, so the grant is "
                "unknown. Slack sets it on every authenticated Web API response, "
                "so its absence usually means the call never authenticated.")

    buckets = grant_buckets(header)
    if buckets["coarse"]:
        return ("classic",
                "coarse scope(s) %s. Those belong to the pre-2020 model, which "
                "cannot be mixed with granular scopes, so nothing can be added "
                "to this app." % ", ".join(sorted(buckets["coarse"])))
    if buckets["retired"]:
        return ("retired-intermediate",
                "granular vocabulary, but %s no longer exists. The requested "
                "scope list predates the collapse of the qualified write scopes."
                % ", ".join(sorted(buckets["retired"])))
    return ("granular",
            "%d granular scope(s), no coarse or retired names"
            % len(buckets["granular"]))


def migration_verdict(identity, state):
    """Cross the era with what auth.test said about the token. Pure.

    A scope list read off a credential that does not authenticate is not
    evidence of anything, so the credential is resolved first.
    """
    if identity.get("ok") is not True:
        return ("credential-unusable",
                "auth.test answered error=%s, so nothing can be concluded from "
                "the header on that response. Resolve the credential before "
                "reading its grant." % (identity.get("error") or "<no error field>"))

    if state == "no-scope-header":
        return ("not-assessed",
                "the call authenticated but no grant came back with it. Report "
                "this as unknown rather than as granular.")

    if state == "classic":
        if identity.get("bot_id"):
            return ("classic-bot-install",
                    "a classic bot install. It still has RTM, which is usually "
                    "why it is still here, and it cannot be given a single "
                    "granular scope. Build a new app and cut over.")
        return ("classic-user-install",
                "a classic install on a user token: it acts as the person who "
                "installed it and dies with their account. Rebuild as a granular "
                "app with bot scopes rather than porting the user token across.")

    if state == "retired-intermediate":
        return ("granular-with-dead-names",
                "granular app, stale scope names. This one is fixable in place: "
                "edit the requested scopes, reinstall, replace the token. No new "
                "app is needed.")

    return ("granular", "current permission model, nothing to migrate")


def auth_test(session, token):
    """One GET. Returns (body, grant) because the finding is in the header."""
    r = session.get(API + "auth.test",
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = {"ok": False, "error": "unparseable_body"}
    return body, r.headers.get("x-oauth-scopes")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token to inspect")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("%s is not set; nothing to inspect", args.token_env)
        return 2

    body, header = auth_test(requests.Session(), token)
    state, detail = classify_grant(header)
    verdict, why = migration_verdict(body, state)
    buckets = grant_buckets(header)

    log.info("%-26s %s", verdict, why)
    log.info("  grant: %s", detail)

    if verdict == "granular":
        return 0

    if buckets["coarse"]:
        log.warning("  coarse: %s", ", ".join(sorted(buckets["coarse"])))
        log.warning("  repair: create a new app from a manifest with granular "
                    "scopes, install it alongside this one, move traffic, then "
                    "uninstall the classic app. There is no in-place upgrade.")
        log.warning("  repair: budget for the RTM rewrite; the new app will not "
                    "have RTM, so the code moves to the Events API or Socket Mode.")
    for scope in sorted(buckets["retired"]):
        log.warning("  retired: %s is now %s", scope, RETIRED[scope])
    if buckets["retired"]:
        log.warning("  repair: swap the names above in the requested scope list "
                    "and reinstall. Add chat:write.customize only if the code "
                    "overrides username or icon_emoji.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-classic-scope-audit.mjs",
"js": '''/**
 * Decide which Slack permission era an installed app belongs to.
 *
 * Read only. One GET, and the finding is in the response header rather than the
 * body: X-OAuth-Scopes carries the complete grant. The repair for a classic app
 * is a second app, so the script prints the migration rather than suggesting a
 * reinstall that cannot work.
 */
const API = 'https://slack.com/api/';

// The only two granular scopes that legitimately carry no colon. Any other bare
// word in the grant is a coarse scope from the pre-2020 model.
const GRANULAR_BARE = new Set(['incoming-webhook', 'commands']);

// Intermediate scopes the granular migration retired, and what replaced them.
export const RETIRED = {
  'chat:write:bot': 'chat:write',
  'chat:write:user': 'chat:write',
  'files:write:user': 'files:write',
};

/**
 * Sort a raw X-OAuth-Scopes header into three vocabularies. Pure.
 */
export function grantBuckets(header) {
  const scopes = String(header ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  const buckets = { coarse: [], retired: [], granular: [] };
  for (const scope of scopes) {
    if (Object.prototype.hasOwnProperty.call(RETIRED, scope)) buckets.retired.push(scope);
    else if (!scope.includes(':') && !GRANULAR_BARE.has(scope)) buckets.coarse.push(scope);
    else buckets.granular.push(scope);
  }
  return buckets;
}

/**
 * Name the permission era this grant belongs to. Pure.
 */
export function classifyGrant(header) {
  if (!String(header ?? '').trim()) {
    return ['no-scope-header',
      'the response carried no X-OAuth-Scopes header, so the grant is unknown. ' +
      'Slack sets it on every authenticated Web API response, so its absence ' +
      'usually means the call never authenticated.'];
  }

  const buckets = grantBuckets(header);
  if (buckets.coarse.length) {
    return ['classic',
      `coarse scope(s) ${[...buckets.coarse].sort().join(', ')}. Those belong to ` +
      'the pre-2020 model, which cannot be mixed with granular scopes, so nothing ' +
      'can be added to this app.'];
  }
  if (buckets.retired.length) {
    return ['retired-intermediate',
      `granular vocabulary, but ${[...buckets.retired].sort().join(', ')} no longer ` +
      'exists. The requested scope list predates the collapse of the qualified ' +
      'write scopes.'];
  }
  return ['granular',
    `${buckets.granular.length} granular scope(s), no coarse or retired names`];
}

/**
 * Cross the era with what auth.test said about the token. Pure.
 * A scope list read off a credential that does not authenticate is not evidence
 * of anything, so the credential is resolved first.
 */
export function migrationVerdict(identity, state) {
  if (identity?.ok !== true) {
    return ['credential-unusable',
      `auth.test answered error=${identity?.error ?? '<no error field>'}, so ` +
      'nothing can be concluded from the header on that response. Resolve the ' +
      'credential before reading its grant.'];
  }

  if (state === 'no-scope-header') {
    return ['not-assessed',
      'the call authenticated but no grant came back with it. Report this as ' +
      'unknown rather than as granular.'];
  }

  if (state === 'classic') {
    if (identity.bot_id) {
      return ['classic-bot-install',
        'a classic bot install. It still has RTM, which is usually why it is ' +
        'still here, and it cannot be given a single granular scope. Build a new ' +
        'app and cut over.'];
    }
    return ['classic-user-install',
      'a classic install on a user token: it acts as the person who installed it ' +
      'and dies with their account. Rebuild as a granular app with bot scopes ' +
      'rather than porting the user token across.'];
  }

  if (state === 'retired-intermediate') {
    return ['granular-with-dead-names',
      'granular app, stale scope names. This one is fixable in place: edit the ' +
      'requested scopes, reinstall, replace the token. No new app is needed.'];
  }

  return ['granular', 'current permission model, nothing to migrate'];
}

async function authTest(token) {
  const res = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  let body;
  try {
    body = await res.json();
  } catch {
    body = { ok: false, error: 'unparseable_body' };
  }
  return [body, res.headers.get('x-oauth-scopes')];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const tokenEnv = arg(process.argv.slice(2), '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`${tokenEnv} is not set; nothing to inspect`);
    process.exitCode = 2;
    return;
  }

  const [body, header] = await authTest(token);
  const [state, detail] = classifyGrant(header);
  const [verdict, why] = migrationVerdict(body, state);
  const buckets = grantBuckets(header);

  console.log(`${verdict.padEnd(26)} ${why}`);
  console.log(`  grant: ${detail}`);

  if (verdict === 'granular') {
    process.exitCode = 0;
    return;
  }

  if (buckets.coarse.length) {
    console.warn(`  coarse: ${[...buckets.coarse].sort().join(', ')}`);
    console.warn('  repair: create a new app from a manifest with granular scopes, ' +
                 'install it alongside this one, move traffic, then uninstall the ' +
                 'classic app. There is no in-place upgrade.');
    console.warn('  repair: budget for the RTM rewrite; the new app will not have ' +
                 'RTM, so the code moves to the Events API or Socket Mode.');
  }
  for (const scope of [...buckets.retired].sort()) {
    console.warn(`  retired: ${scope} is now ${RETIRED[scope]}`);
  }
  if (buckets.retired.length) {
    console.warn('  repair: swap the names above in the requested scope list and ' +
                 'reinstall. Add chat:write.customize only if the code overrides ' +
                 'username or icon_emoji.');
  }

  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does not
// reach for a token that is not there.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two cases worth pinning are the ones that look alike and lead opposite ways: a grant containing <code>bot</code> is a rebuild, and a grant containing only <code>chat:write:bot</code> is a one-line edit. Both are &ldquo;your scopes are wrong&rdquo;; only one of them is a project. The rest of the suite defends the bare-word rule against its two legitimate exceptions, because flagging <code>commands</code> as classic would condemn a healthy app.",
"test_py_file": "test_slack_classic_scope_audit.py",
"test_py": '''from slack_classic_scope_audit import classify_grant, grant_buckets, migration_verdict


def test_a_bare_coarse_scope_makes_the_install_classic():
    state, detail = classify_grant("bot,client,identify,post,read")
    assert state == "classic"
    assert "cannot be mixed" in detail


def test_incoming_webhook_and_commands_are_not_coarse():
    state, _ = classify_grant("commands,incoming-webhook,chat:write,channels:read")
    assert state == "granular"


def test_a_retired_write_scope_is_a_separate_smaller_finding():
    state, detail = classify_grant("channels:read,chat:write:bot")
    assert state == "retired-intermediate"
    assert "chat:write:bot" in detail


def test_coarse_wins_over_retired_because_it_is_terminal():
    assert classify_grant("bot,chat:write:bot")[0] == "classic"


def test_an_absent_header_is_reported_as_unknown_not_as_granular():
    assert classify_grant(None)[0] == "no-scope-header"
    assert classify_grant("  ")[0] == "no-scope-header"


def test_buckets_split_the_three_vocabularies():
    buckets = grant_buckets("read, chat:write:user , channels:read,commands")
    assert buckets["coarse"] == ["read"]
    assert buckets["retired"] == ["chat:write:user"]
    assert sorted(buckets["granular"]) == ["channels:read", "commands"]


def test_a_classic_bot_install_is_named_as_a_rebuild():
    verdict, detail = migration_verdict({"ok": True, "bot_id": "B1"}, "classic")
    assert verdict == "classic-bot-install"
    assert "new app" in detail


def test_a_classic_user_install_is_a_different_verdict():
    verdict, _ = migration_verdict({"ok": True, "user_id": "U1"}, "classic")
    assert verdict == "classic-user-install"


def test_stale_names_alone_are_fixable_in_place():
    verdict, detail = migration_verdict({"ok": True, "bot_id": "B1"},
                                        "retired-intermediate")
    assert verdict == "granular-with-dead-names"
    assert "No new app" in detail


def test_a_dead_credential_stops_the_analysis_before_the_scopes():
    verdict, detail = migration_verdict({"ok": False, "error": "invalid_auth"},
                                        "classic")
    assert verdict == "credential-unusable"
    assert "invalid_auth" in detail
''',
"test_js_file": "slack-classic-scope-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyGrant, grantBuckets, migrationVerdict } from './slack-classic-scope-audit.mjs';

test('a bare coarse scope makes the install classic', () => {
  const [state, detail] = classifyGrant('bot,client,identify,post,read');
  assert.equal(state, 'classic');
  assert.match(detail, /cannot be mixed/);
});

test('incoming-webhook and commands are not coarse', () => {
  assert.equal(classifyGrant('commands,incoming-webhook,chat:write,channels:read')[0],
    'granular');
});

test('a retired write scope is a separate smaller finding', () => {
  const [state, detail] = classifyGrant('channels:read,chat:write:bot');
  assert.equal(state, 'retired-intermediate');
  assert.match(detail, /chat:write:bot/);
});

test('coarse wins over retired because it is terminal', () => {
  assert.equal(classifyGrant('bot,chat:write:bot')[0], 'classic');
});

test('an absent header is reported as unknown not as granular', () => {
  assert.equal(classifyGrant(null)[0], 'no-scope-header');
  assert.equal(classifyGrant('  ')[0], 'no-scope-header');
});

test('buckets split the three vocabularies', () => {
  const buckets = grantBuckets('read, chat:write:user , channels:read,commands');
  assert.deepEqual(buckets.coarse, ['read']);
  assert.deepEqual(buckets.retired, ['chat:write:user']);
  assert.deepEqual([...buckets.granular].sort(), ['channels:read', 'commands']);
});

test('a classic bot install is named as a rebuild', () => {
  const [verdict, detail] = migrationVerdict({ ok: true, bot_id: 'B1' }, 'classic');
  assert.equal(verdict, 'classic-bot-install');
  assert.match(detail, /new app/);
});

test('stale names alone are fixable in place', () => {
  const [verdict, detail] = migrationVerdict({ ok: true, bot_id: 'B1' },
    'retired-intermediate');
  assert.equal(verdict, 'granular-with-dead-names');
  assert.match(detail, /No new app/);
});

test('a dead credential stops the analysis before the scopes', () => {
  const [verdict, detail] = migrationVerdict({ ok: false, error: 'invalid_auth' },
    'classic');
  assert.equal(verdict, 'credential-unusable');
  assert.match(detail, /invalid_auth/);
});
''',
"faq": [
 ("Can I convert a classic app to a granular one?",
  "No. Slack has never offered an in-place upgrade, and the two scope models cannot be held by the same app, so a classic app cannot request a granular scope even once. The supported path is a new app installed alongside the old one, a traffic cutover, and then uninstalling the classic app. Everything about the migration is a copy, not an edit."),
 ("Is a classic app going to stop working?",
  "It has not been switched off, and existing installations continue to function. What you lose is forward motion: no new scopes, no granular features, and no way to adopt anything Slack ships for granular apps. Treat it as a component that cannot receive changes rather than as an outage waiting to happen."),
 ("Why does chat:write:bot appear in tutorials that still rank well?",
  "Because it was correct for years and the pages were never updated. The qualified write scopes were collapsed in the granular migration: chat:write covers posting, and chat:write.customize covers overriding the username or icon_emoji. If your requested scope list still names the old ones the install will fail on the scope, which is a redirect error rather than a runtime one and is easy to miss."),
 ("The header lists both bare words and granular scopes. What is that?",
  "Take the bare words as authoritative and report the app as classic. The two models are not mixable, so a list containing both is a reporting artefact rather than a genuinely hybrid grant, and any advice derived from the granular half will send someone looking for a scope picker that is not there."),
 ("Does the RTM API have to go at the same time?",
  "Effectively yes, since RTM is only available to classic apps and the replacement app will not have it. Plan the move to the Events API or Socket Mode as part of the same project rather than as a follow-up, because the new app cannot receive events any other way and a half-migrated app has no working event transport at all."),
],
"related": [
 ("/slack/missing-scope-on-read/", "when adding a scope is the fix"),
 ("/slack/over-broad-scopes/", "the scopes nothing ever calls"),
 ("/slack/bot-vs-user-scope-mixup/", "the scope is on the other token"),
],
"citations": [CITE_SCOPES, CITE_TOKENS, CITE_AUTH_TEST, CITE_WEB_API],
},

{
"slug": "app-level-token-missing-connections-write",
"title": "Socket Mode never connects: the xapp- token is underscoped",
"description": "apps.connections.open is a write, so a read-only script proves Socket Mode viability through the one read method an app-level token can call.",
"h1": "Socket Mode never connects: the xapp- token is underscoped",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack connections:write missing_scope", "xapp token socket mode",
             "apps.connections.open missing_scope", "slack app-level token scopes",
             "slack socket mode not connecting"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the manifest cross-check reads a manifest you export yourself",
"lead": "The process starts, Bolt announces that it is connecting, and then it retries. Forever. No events arrive, nothing crashes, and the only line in the log that matters is <code>missing_scope</code> from <code>apps.connections.open</code> &mdash; a method your read-only audit script is not allowed to call, because opening a connection is a write.",
"short_answer": """<p>App-level tokens are minted <strong>per scope set</strong> on the Basic Information page and cannot be edited afterwards. Socket Mode needs <code>connections:write</code>; the multi-install helper <code>apps.event.authorizations.list</code> needs <code>authorizations:read</code>. A token generated for one of those does not carry the other, and there is no method that returns an app-level token's scope list.</p>
<p>So a read-only script cannot ask the question directly &mdash; but it can ask the neighbouring one. <code>apps.event.authorizations.list</code> is the only <em>read</em> method that accepts an <code>xapp-</code> credential. Call it with an <code>event_context</code> you invented, and the error is a statement about the token: <code>invalid_event_context</code> means it authenticated and holds an app-level scope, <code>missing_scope</code> means it does not, <code>auth_mismatch</code> means it belongs to a different app. Cross that with <code>settings.socket_mode_enabled</code> from a manifest you export yourself and you have the finding: Socket Mode is on and the credential the app was given cannot support it.</p>""",
"problem": """<p>Everything about this failure is quiet. Socket Mode does not fail closed with a crash; the client library treats a failed connection as transient and reconnects, so the service stays up, the health check passes, and the app simply never receives an event. On a workspace where the app mostly listens, that can go unnoticed for days.</p>
<p>The configuration mistake behind it is easy to make. The App-Level Tokens dialog asks you to name the token and tick the scopes, and it is entirely reasonable to tick the one you came for. A team that added <code>authorizations:read</code> to support a second customer, generated a fresh token, and updated <code>SLACK_APP_TOKEN</code> has just removed Socket Mode from an app that had it &mdash; and the reverse happens just as often. There is no edit button on an existing app-level token; there is only generate and revoke.</p>
<p>What makes it awkward to audit is that the diagnostic call is a write. <code>apps.connections.open</code> mints a single-use WebSocket URL: calling it changes server state, counts against the ten permitted connections, and is exactly the sort of thing a section that promises read-only scripts must not do. So the check has to be an inference, and an inference is only worth running if it is honest about its limits.</p>""",
"why": """<p><strong>An app-level token is not a workspace credential.</strong> It carries no workspace scopes, cannot call <code>chat.postMessage</code> or <code>conversations.list</code>, and <code>auth.test</code> refuses it. Two methods accept it and only one of them reads. That is the entire surface available for the inference.</p>
<p><strong>The argument error is the proof.</strong> Slack checks the credential before it checks the parameters, so a complaint about the <code>event_context</code> you deliberately made up means everything before that step passed: the token is an app-level token, it belongs to this app, and it holds the app-level scope this method needs. Reading an error as a pass feels wrong the first time and is the most reliable signal here.</p>
<p><strong>One app-level scope missing is evidence about the mint, not proof about the other.</strong> <code>missing_scope</code> from the probe says <code>authorizations:read</code> is absent. It does not say <code>connections:write</code> is absent &mdash; that scope is genuinely unobservable. What it does say is that this token was minted with a partial scope set, which is the mistake, and since the fix is to regenerate with both boxes ticked, the finding is actionable regardless.</p>
<p><strong>The manifest supplies the other half.</strong> <code>settings.socket_mode_enabled</code> tells you whether Socket Mode is the transport at all. Without it, a token that lacks an app-level scope is a curiosity; with it, the same fact is the reason no events arrive. If you cannot export the manifest, the script says so rather than assuming.</p>
<p><strong>Socket Mode off with no request URL is its own finding.</strong> An app with neither transport configured receives nothing and has no error to show for it, and that combination falls out of the same matrix for free.</p>""",
"steps": [
 {"h": "Do not call the method that opens the connection",
  "body": """<p><code>apps.connections.open</code> mints a WebSocket URL. That is a write: it consumes one of the ten permitted connections and changes state on Slack's side. An audit that opens a socket to prove a socket can be opened is not an audit, and on a busy app it can displace a live connection.</p>"""},
 {"h": "Probe the read method that takes the same credential",
  "body": """<p>One GET to <code>apps.event.authorizations.list</code> with the <code>xapp-</code> token in the <code>Authorization</code> header and an <code>event_context</code> that is obviously not real. Sending it as a query parameter matters: this method rejects the token if it arrives as a body parameter rather than a header.</p>"""},
 {"h": "Read the argument complaint as a pass",
  "body": """<p><code>invalid_event_context</code> is the healthy answer. It means the credential cleared and the method got as far as the parameters. <code>missing_scope</code> names the gap, <code>auth_mismatch</code> means the token was minted for a different app, and <code>invalid_auth</code> or <code>not_allowed_token_type</code> means the value is not an app-level token at all.</p>"""},
 {"h": "Export the manifest yourself and hand it over",
  "body": """<p>The script takes a manifest as a local JSON file rather than fetching it, so the check needs no second credential class. Export it once from the app configuration and keep it next to the audit; the two fields it reads are <code>settings.socket_mode_enabled</code> and <code>settings.event_subscriptions.request_url</code>.</p>"""},
 {"h": "Regenerate the token with both scopes ticked",
  "body": """<p>There is no way to add a scope to an existing app-level token. Generate a new one on Basic Information with <code>connections:write</code> and <code>authorizations:read</code> both selected, deploy it as <code>SLACK_APP_TOKEN</code>, restart, and only then revoke the old token from the same page.</p>"""},
 {"h": "State what the probe cannot prove",
  "body": """<p>Write the limitation into the output, not just into the README. The probe demonstrates that one app-level scope is missing and that Socket Mode is enabled; it infers rather than proves that the connection scope is also absent. A reader who understands that will trust the next finding too.</p>"""},
],
"verify": """<p>After regenerating the token, run it again with the same manifest. The probe should come back with the argument complaint and the verdict should be the plausible one, which is the strongest statement this check is allowed to make.</p>
<pre><code class="language-bash">SLACK_APP_TOKEN=xapp-... python3 slack_socket_readiness.py --manifest app-manifest.json
# socket-mode-plausible  the token authenticates and holds an app-level scope</code></pre>""",
"code_intro": "One GET, sent deliberately wrong. Three pure functions carry the reasoning: <code>probe_verdict</code> turns the API's error into a statement about the credential, <code>manifest_settings</code> pulls the two fields that matter out of an exported manifest without caring how the rest of it is shaped, and <code>socket_readiness</code> is the matrix that crosses them &mdash; nine outcomes, only three of which are findings.",
"py_file": "slack_socket_readiness.py",
"py": '''"""Ask a Slack app-level token what it can do, without minting a connection.

Read only. apps.connections.open mints a WebSocket URL, which is a write, so
this script never calls it. It exercises the one read method that accepts the
same credential class, reads the error as a statement about the token, and
crosses that with a manifest you exported yourself.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_socket_readiness")

API = "https://slack.com/api/"

# Deliberately not a real event_context. The method checks the credential before
# it checks the arguments, so a complaint about this string is the pass.
PROBE_CONTEXT = "read-only-probe-not-a-real-event-context"

FINDINGS = ("socket-mode-cannot-connect", "app-level-scopes-incomplete",
            "scope-gap-without-socket-mode", "no-event-transport",
            "credential-not-app-level", "token-belongs-elsewhere")


def probe_verdict(body):
    """Read one apps.event.authorizations.list answer as a statement about the
    credential rather than about the request. Pure. -> (state, detail)
    """
    if body.get("ok") is True:
        return ("app-level-scope-present",
                "the call answered ok, so the token authenticated and holds "
                "authorizations:read.")

    error = body.get("error") or "<no error field>"
    if error in ("invalid_event_context", "event_context_invalid"):
        return ("app-level-scope-present",
                "the method refused the event_context we invented, which means "
                "it accepted the credential and the scope first. An argument "
                "complaint here is the pass.")
    if error == "missing_scope":
        return ("missing-authorizations-read",
                "missing_scope: this app-level token was minted without "
                "authorizations:read. App-level scopes are chosen once, at mint "
                "time, and cannot be added afterwards.")
    if error == "auth_mismatch":
        return ("token-from-another-app",
                "auth_mismatch: the token is a valid app-level token belonging "
                "to a different app. Nothing about this app's configuration is "
                "wrong; the wrong secret was deployed.")
    if error == "not_allowed_token_type":
        return ("wrong-credential-class",
                "not_allowed_token_type: the value in the app-level slot is a "
                "workspace token. It will never open a socket.")
    if error == "invalid_auth":
        return ("credential-rejected",
                "invalid_auth: the credential was refused outright. Check the "
                "prefix and check for whitespace before reading anything else "
                "into this.")
    if error == "ratelimited":
        return ("not-assessed",
                "ratelimited: no conclusion is available from this run.")
    return ("not-assessed",
            "error=%s, which is not one of the answers this probe knows how to "
            "read. Resolve it before drawing a conclusion." % error)


def manifest_settings(manifest):
    """Pull the two fields this note needs out of an exported manifest. Pure.

    Returns None when no manifest was supplied, so the caller can distinguish
    "Socket Mode is off" from "nobody told us".
    """
    if not isinstance(manifest, dict):
        return None
    settings = manifest.get("settings")
    settings = settings if isinstance(settings, dict) else {}
    subs = settings.get("event_subscriptions")
    subs = subs if isinstance(subs, dict) else {}
    return {"socket_mode_enabled": bool(settings.get("socket_mode_enabled")),
            "request_url": subs.get("request_url") or None}


def socket_readiness(settings, probe_state):
    """Cross the probe with the manifest. Pure. -> (state, detail)"""
    if probe_state in ("wrong-credential-class", "credential-rejected"):
        return ("credential-not-app-level",
                "the value deployed as the app-level token is not one. Fix that "
                "before asking anything about Socket Mode.")
    if probe_state == "token-from-another-app":
        return ("token-belongs-elsewhere",
                "the token is well formed and useless here. Take the app-level "
                "token from this app's Basic Information page.")
    if probe_state == "not-assessed":
        return ("not-assessed",
                "the probe gave no usable answer, so Socket Mode readiness is "
                "unknown. Report it that way rather than as healthy.")

    gap = probe_state == "missing-authorizations-read"

    if settings is None:
        if gap:
            return ("app-level-scopes-incomplete",
                    "the token was minted with a partial app-level scope set. "
                    "Without a manifest we cannot say whether Socket Mode is the "
                    "transport, but the token should be regenerated either way.")
        return ("app-level-token-live",
                "the token authenticates and holds an app-level scope. Supply a "
                "manifest to say whether Socket Mode is actually enabled.")

    if settings["socket_mode_enabled"]:
        if gap:
            return ("socket-mode-cannot-connect",
                    "Socket Mode is enabled and the deployed app-level token was "
                    "minted without one of the two app-level scopes. That is why "
                    "the client reconnects forever and no event ever arrives.")
        return ("socket-mode-plausible",
                "Socket Mode is enabled and the token authenticates with an "
                "app-level scope. connections:write cannot be read and cannot be "
                "exercised without minting a connection, so this is the "
                "strongest read-only evidence available.")

    if gap:
        return ("scope-gap-without-socket-mode",
                "the app-level token is short a scope, but Socket Mode is off so "
                "nothing is broken today. Regenerate before turning it on.")
    if settings["request_url"]:
        return ("http-events-not-socket",
                "Socket Mode is off and a request URL is configured, so events "
                "arrive over HTTP and the app-level token is not in the path.")
    return ("no-event-transport",
            "Socket Mode is off and no request URL is configured. The app has no "
            "way to receive events at all, and there is no error anywhere that "
            "says so.")


def probe(session, token, context=PROBE_CONTEXT):
    """One GET. The event_context goes in the query string and the credential in
    the header: this method rejects an app-level token sent as a parameter."""
    r = session.get(API + "apps.event.authorizations.list",
                    headers={"Authorization": "Bearer " + token},
                    params={"event_context": context}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_APP_TOKEN",
                    help="environment variable holding the xapp- app-level token")
    ap.add_argument("--manifest",
                    help="path to a manifest you exported from the app config")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("%s is not set; there is no app-level credential to probe",
                  args.token_env)
        return 2
    if not token.startswith("xapp-"):
        log.warning("%s does not start with xapp-, so the probe below is very "
                    "likely to confirm the wrong credential class", args.token_env)

    manifest = None
    if args.manifest:
        manifest = json.loads(open(args.manifest, encoding="utf-8").read())
    settings = manifest_settings(manifest)

    state, detail = probe_verdict(probe(requests.Session(), token))
    verdict, why = socket_readiness(settings, state)

    log.info("%-30s %s", verdict, why)
    log.info("  probe: %s -- %s", state, detail)

    if verdict not in FINDINGS:
        return 0

    if state == "missing-authorizations-read":
        log.warning("  repair: Basic Information -> App-Level Tokens -> Generate. "
                    "Tick connections:write and authorizations:read together; an "
                    "existing app-level token cannot have a scope added.")
        log.warning("  repair: deploy the new value as %s, restart, and only then "
                    "revoke the old token from the same page.", args.token_env)
        log.warning("  limit: the probe proves one app-level scope is absent. "
                    "connections:write is unobservable without minting a "
                    "connection, so its absence here is inference, not proof.")
    if verdict == "no-event-transport":
        log.warning("  repair: enable Socket Mode, or set a request URL under "
                    "Event Subscriptions. With neither, no event is delivered.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-socket-readiness.mjs",
"js": '''/**
 * Ask a Slack app-level token what it can do, without minting a connection.
 *
 * Read only. apps.connections.open mints a WebSocket URL, which is a write, so
 * this script never calls it. It exercises the one read method that accepts the
 * same credential class, reads the error as a statement about the token, and
 * crosses that with a manifest you exported yourself.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Deliberately not a real event_context. The method checks the credential before
// it checks the arguments, so a complaint about this string is the pass.
const PROBE_CONTEXT = 'read-only-probe-not-a-real-event-context';

const FINDINGS = new Set([
  'socket-mode-cannot-connect', 'app-level-scopes-incomplete',
  'scope-gap-without-socket-mode', 'no-event-transport',
  'credential-not-app-level', 'token-belongs-elsewhere',
]);

/**
 * Read one apps.event.authorizations.list answer as a statement about the
 * credential rather than about the request. Pure.
 */
export function probeVerdict(body) {
  if (body?.ok === true) {
    return ['app-level-scope-present',
      'the call answered ok, so the token authenticated and holds authorizations:read.'];
  }

  const error = body?.error ?? '<no error field>';
  if (error === 'invalid_event_context' || error === 'event_context_invalid') {
    return ['app-level-scope-present',
      'the method refused the event_context we invented, which means it accepted ' +
      'the credential and the scope first. An argument complaint here is the pass.'];
  }
  if (error === 'missing_scope') {
    return ['missing-authorizations-read',
      'missing_scope: this app-level token was minted without authorizations:read. ' +
      'App-level scopes are chosen once, at mint time, and cannot be added afterwards.'];
  }
  if (error === 'auth_mismatch') {
    return ['token-from-another-app',
      'auth_mismatch: the token is a valid app-level token belonging to a different ' +
      'app. Nothing about this app is wrong; the wrong secret was deployed.'];
  }
  if (error === 'not_allowed_token_type') {
    return ['wrong-credential-class',
      'not_allowed_token_type: the value in the app-level slot is a workspace ' +
      'token. It will never open a socket.'];
  }
  if (error === 'invalid_auth') {
    return ['credential-rejected',
      'invalid_auth: the credential was refused outright. Check the prefix and ' +
      'check for whitespace before reading anything else into this.'];
  }
  if (error === 'ratelimited') {
    return ['not-assessed', 'ratelimited: no conclusion is available from this run.'];
  }
  return ['not-assessed',
    `error=${error}, which is not one of the answers this probe knows how to read. ` +
    'Resolve it before drawing a conclusion.'];
}

/**
 * Pull the two fields this note needs out of an exported manifest. Pure.
 * Returns null when no manifest was supplied, so the caller can distinguish
 * "Socket Mode is off" from "nobody told us".
 */
export function manifestSettings(manifest) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) return null;
  const settings = (manifest.settings && typeof manifest.settings === 'object')
    ? manifest.settings : {};
  const subs = (settings.event_subscriptions && typeof settings.event_subscriptions === 'object')
    ? settings.event_subscriptions : {};
  return {
    socket_mode_enabled: Boolean(settings.socket_mode_enabled),
    request_url: subs.request_url || null,
  };
}

/**
 * Cross the probe with the manifest. Pure.
 */
export function socketReadiness(settings, probeState) {
  if (probeState === 'wrong-credential-class' || probeState === 'credential-rejected') {
    return ['credential-not-app-level',
      'the value deployed as the app-level token is not one. Fix that before ' +
      'asking anything about Socket Mode.'];
  }
  if (probeState === 'token-from-another-app') {
    return ['token-belongs-elsewhere',
      'the token is well formed and useless here. Take the app-level token from ' +
      "this app's Basic Information page."];
  }
  if (probeState === 'not-assessed') {
    return ['not-assessed',
      'the probe gave no usable answer, so Socket Mode readiness is unknown. ' +
      'Report it that way rather than as healthy.'];
  }

  const gap = probeState === 'missing-authorizations-read';

  if (settings === null || settings === undefined) {
    if (gap) {
      return ['app-level-scopes-incomplete',
        'the token was minted with a partial app-level scope set. Without a ' +
        'manifest we cannot say whether Socket Mode is the transport, but the ' +
        'token should be regenerated either way.'];
    }
    return ['app-level-token-live',
      'the token authenticates and holds an app-level scope. Supply a manifest to ' +
      'say whether Socket Mode is actually enabled.'];
  }

  if (settings.socket_mode_enabled) {
    if (gap) {
      return ['socket-mode-cannot-connect',
        'Socket Mode is enabled and the deployed app-level token was minted ' +
        'without one of the two app-level scopes. That is why the client ' +
        'reconnects forever and no event ever arrives.'];
    }
    return ['socket-mode-plausible',
      'Socket Mode is enabled and the token authenticates with an app-level ' +
      'scope. connections:write cannot be read and cannot be exercised without ' +
      'minting a connection, so this is the strongest read-only evidence available.'];
  }

  if (gap) {
    return ['scope-gap-without-socket-mode',
      'the app-level token is short a scope, but Socket Mode is off so nothing is ' +
      'broken today. Regenerate before turning it on.'];
  }
  if (settings.request_url) {
    return ['http-events-not-socket',
      'Socket Mode is off and a request URL is configured, so events arrive over ' +
      'HTTP and the app-level token is not in the path.'];
  }
  return ['no-event-transport',
    'Socket Mode is off and no request URL is configured. The app has no way to ' +
    'receive events at all, and there is no error anywhere that says so.'];
}

async function probe(token, context = PROBE_CONTEXT) {
  const url = `${API}apps.event.authorizations.list?event_context=${encodeURIComponent(context)}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_APP_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`${tokenEnv} is not set; there is no app-level credential to probe`);
    process.exitCode = 2;
    return;
  }
  if (!token.startsWith('xapp-')) {
    console.warn(`${tokenEnv} does not start with xapp-, so the probe below is very ` +
                 'likely to confirm the wrong credential class');
  }

  const manifestPath = arg(args, '--manifest');
  const manifest = manifestPath
    ? JSON.parse(await readFile(manifestPath, 'utf8')) : null;
  const settings = manifestSettings(manifest);

  const [state, detail] = probeVerdict(await probe(token));
  const [verdict, why] = socketReadiness(settings, state);

  console.log(`${verdict.padEnd(30)} ${why}`);
  console.log(`  probe: ${state} -- ${detail}`);

  if (!FINDINGS.has(verdict)) {
    process.exitCode = 0;
    return;
  }

  if (state === 'missing-authorizations-read') {
    console.warn('  repair: Basic Information -> App-Level Tokens -> Generate. Tick ' +
                 'connections:write and authorizations:read together; an existing ' +
                 'app-level token cannot have a scope added.');
    console.warn(`  repair: deploy the new value as ${tokenEnv}, restart, and only ` +
                 'then revoke the old token from the same page.');
    console.warn('  limit: the probe proves one app-level scope is absent. ' +
                 'connections:write is unobservable without minting a connection, ' +
                 'so its absence here is inference, not proof.');
  }
  if (verdict === 'no-event-transport') {
    console.warn('  repair: enable Socket Mode, or set a request URL under Event ' +
                 'Subscriptions. With neither, no event is delivered.');
  }

  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does not
// reach for a token that is not there.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters most is the one asserting an <em>error</em> is a pass: <code>invalid_event_context</code> has to classify as a healthy credential, because everything else in the matrix hangs off that inversion. After that the suite walks the manifest crossing, including the row nobody thinks to configure &mdash; Socket Mode off, no request URL, no error anywhere, and no events either.",
"test_py_file": "test_slack_socket_readiness.py",
"test_py": '''from slack_socket_readiness import manifest_settings, probe_verdict, socket_readiness


def test_an_argument_complaint_proves_the_credential_and_the_scope():
    state, detail = probe_verdict({"ok": False, "error": "invalid_event_context"})
    assert state == "app-level-scope-present"
    assert "the pass" in detail


def test_missing_scope_names_the_mint_time_mistake():
    state, detail = probe_verdict({"ok": False, "error": "missing_scope"})
    assert state == "missing-authorizations-read"
    assert "mint" in detail


def test_auth_mismatch_is_the_wrong_app_not_the_wrong_scope():
    assert probe_verdict({"ok": False, "error": "auth_mismatch"})[0] == "token-from-another-app"


def test_a_workspace_token_in_the_app_level_slot_is_a_class_problem():
    assert probe_verdict({"ok": False,
                          "error": "not_allowed_token_type"})[0] == "wrong-credential-class"


def test_an_unknown_error_is_not_assessed_rather_than_healthy():
    assert probe_verdict({"ok": False, "error": "fatal_error"})[0] == "not-assessed"


def test_manifest_settings_survives_a_manifest_with_nothing_in_it():
    assert manifest_settings({}) == {"socket_mode_enabled": False, "request_url": None}
    assert manifest_settings(None) is None


def test_socket_mode_on_plus_a_scope_gap_is_the_headline_finding():
    verdict, detail = socket_readiness(
        {"socket_mode_enabled": True, "request_url": None},
        "missing-authorizations-read")
    assert verdict == "socket-mode-cannot-connect"
    assert "reconnects forever" in detail


def test_socket_mode_on_with_a_live_token_is_only_ever_plausible():
    verdict, detail = socket_readiness(
        {"socket_mode_enabled": True, "request_url": None}, "app-level-scope-present")
    assert verdict == "socket-mode-plausible"
    assert "strongest read-only evidence" in detail


def test_no_manifest_downgrades_the_conclusion_instead_of_guessing():
    assert socket_readiness(None, "app-level-scope-present")[0] == "app-level-token-live"
    assert socket_readiness(None, "missing-authorizations-read")[0] == "app-level-scopes-incomplete"


def test_socket_mode_off_with_a_request_url_is_not_a_finding():
    verdict, _ = socket_readiness(
        {"socket_mode_enabled": False, "request_url": "https://example.test/slack"},
        "app-level-scope-present")
    assert verdict == "http-events-not-socket"


def test_neither_transport_configured_is_a_finding_with_no_error_behind_it():
    verdict, detail = socket_readiness(
        {"socket_mode_enabled": False, "request_url": None}, "app-level-scope-present")
    assert verdict == "no-event-transport"
    assert "no error anywhere" in detail
''',
"test_js_file": "slack-socket-readiness.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { manifestSettings, probeVerdict, socketReadiness } from './slack-socket-readiness.mjs';

test('an argument complaint proves the credential and the scope', () => {
  const [state, detail] = probeVerdict({ ok: false, error: 'invalid_event_context' });
  assert.equal(state, 'app-level-scope-present');
  assert.match(detail, /the pass/);
});

test('missing_scope names the mint time mistake', () => {
  const [state, detail] = probeVerdict({ ok: false, error: 'missing_scope' });
  assert.equal(state, 'missing-authorizations-read');
  assert.match(detail, /mint/);
});

test('auth_mismatch is the wrong app not the wrong scope', () => {
  assert.equal(probeVerdict({ ok: false, error: 'auth_mismatch' })[0],
    'token-from-another-app');
});

test('a workspace token in the app-level slot is a class problem', () => {
  assert.equal(probeVerdict({ ok: false, error: 'not_allowed_token_type' })[0],
    'wrong-credential-class');
});

test('an unknown error is not assessed rather than healthy', () => {
  assert.equal(probeVerdict({ ok: false, error: 'fatal_error' })[0], 'not-assessed');
});

test('manifestSettings survives a manifest with nothing in it', () => {
  assert.deepEqual(manifestSettings({}),
    { socket_mode_enabled: false, request_url: null });
  assert.equal(manifestSettings(null), null);
});

test('socket mode on plus a scope gap is the headline finding', () => {
  const [verdict, detail] = socketReadiness(
    { socket_mode_enabled: true, request_url: null }, 'missing-authorizations-read');
  assert.equal(verdict, 'socket-mode-cannot-connect');
  assert.match(detail, /reconnects forever/);
});

test('socket mode on with a live token is only ever plausible', () => {
  const [verdict, detail] = socketReadiness(
    { socket_mode_enabled: true, request_url: null }, 'app-level-scope-present');
  assert.equal(verdict, 'socket-mode-plausible');
  assert.match(detail, /strongest read-only evidence/);
});

test('no manifest downgrades the conclusion instead of guessing', () => {
  assert.equal(socketReadiness(null, 'app-level-scope-present')[0], 'app-level-token-live');
  assert.equal(socketReadiness(null, 'missing-authorizations-read')[0],
    'app-level-scopes-incomplete');
});

test('neither transport configured is a finding with no error behind it', () => {
  const [verdict, detail] = socketReadiness(
    { socket_mode_enabled: false, request_url: null }, 'app-level-scope-present');
  assert.equal(verdict, 'no-event-transport');
  assert.match(detail, /no error anywhere/);
});
''',
"faq": [
 ("Why not just call apps.connections.open and see what happens?",
  "Because it mints a connection. The method returns a single-use WebSocket URL, counts against the ten connections an app may hold open, and changes state on Slack's side, so it is a write by any reasonable definition. On a running app an audit that opens sockets can also displace a live one, which is a worse outcome than not knowing."),
 ("Can I read the scopes on an app-level token?",
  "No. auth.test rejects an xapp- token, there is no method that returns its grant, and the App-Level Tokens page shows the scopes only at creation time. The probe in this note is the whole observable surface: one read method, one credential class, and an error message that tells you which stage the request reached."),
 ("Does missing_scope on the probe really mean Socket Mode is broken?",
  "It means this token was minted with a partial scope set, which is the mistake behind almost every case of this. It is not proof that connections:write is absent, because that scope cannot be observed at all without minting a connection. The script says so in its own output, and the repair is the same either way: regenerate with both boxes ticked."),
 ("Can I add connections:write to the token I already have?",
  "No. App-level tokens are immutable once generated; the page offers generate and revoke and nothing in between. Generate a replacement with both scopes, deploy it, restart the process, and revoke the old one afterwards rather than before, so a failed deploy leaves you somewhere to fall back to."),
 ("What if I cannot export the manifest?",
  "The script runs without one and downgrades its conclusion rather than assuming. You still learn whether the app-level token authenticates and whether it holds an app-level scope, which is most of the value; what you lose is the ability to say whether Socket Mode is the transport that matters here, and the output says that explicitly instead of implying a clean bill of health."),
],
"related": [
 ("/slack/invalid-auth-wrong-token-type/", "the prefix in the wrong slot"),
 ("/slack/not-allowed-token-type/", "when the method refuses the class"),
 ("/slack/authorizations-read-missing/", "the other app-level scope"),
],
"citations": [CITE_SOCKET, CITE_CONNECTIONS_OPEN, CITE_EVENT_AUTHZ, CITE_TOKENS],
},

{
"slug": "authorizations-read-missing",
"title": "One event, many installs: authorizations:read fans it out",
"description": "A distributed Slack app serves one workspace per event: the authorizations array is truncated, and only apps.event.authorizations.list expands it.",
"h1": "One event, many installs: authorizations:read fans it out",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack authorizations:read", "apps.event.authorizations.list",
             "slack event_context", "slack multi workspace event delivery",
             "slack distributed app only works for some"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the tenancy half reads your installation store",
"lead": "Support says the bot only works for some customers. Your logs disagree: every event was received, handled, and acknowledged, with no errors on any of them. Both are true. Slack delivered one event that several installations should have seen, your handler processed it for the one workspace named in the payload, and nothing anywhere recorded the ones it skipped.",
"short_answer": """<p>When an event is visible to more than one installation of your app, Slack sends <strong>one delivery</strong>. The payload carries an <code>event_context</code> and an <code>authorizations</code> array that has been <strong>truncated to a single entry</strong>. You are expected to call <code>apps.event.authorizations.list</code> with that <code>event_context</code> to enumerate every installation that should see the event, and to process it once per authorization.</p>
<p>That method needs <code>authorizations:read</code> on an app-level token. Without it, the fan-out cannot happen and the app serves exactly one tenant per event, silently. The script below establishes three things and combines them: whether the app is genuinely multi-install (from your installation store), what one captured event envelope actually looked like, and whether the capability exists at all. The severity comes from the first of those, not from the third &mdash; a single-workspace app with no <code>authorizations:read</code> is not broken, it is one customer away from being broken.</p>""",
"problem": """<p>This bug has no error. The delivery arrives, the signature verifies, the handler runs, the acknowledgement goes back inside three seconds, and Slack is satisfied. The only thing wrong is a comparison nobody performs: how many installations should have seen this event versus how many did.</p>
<p>It also hides behind a plausible-looking payload. The <code>authorizations</code> array is present and well formed and contains one entry, and a developer reading it for the first time will conclude that one installation is who this event is for. That is exactly what the field looks like when it has been truncated, because truncation here is normal &mdash; Slack documents that the array is limited and that <code>event_context</code> is the way to get the rest. Nothing in the payload announces that it was cut.</p>
<p>And it is invisible in the workspace that reported it. The customer who complains is the one who saw nothing; the customer who was served has no idea anything happened. So the bug reaches you as "it works for us but not for them", which sounds like a permissions problem in the affected workspace and sends everyone to inspect the wrong installation.</p>""",
"why": """<p><strong>One event, one delivery.</strong> The design is deliberate: Slack does not fan an event out to every installation on your behalf, because it does not know how you shard, batch or deduplicate. It hands you a handle &mdash; <code>event_context</code> &mdash; and expects you to expand it. An app that ignores the handle has not disabled a feature; it has skipped a step.</p>
<p><strong>The array length is not a count.</strong> Treating <code>authorizations.length</code> as the number of interested installations is the mistake at the centre of this note. It is a sample, and the sample size is one. Any logic that branches on it is branching on a constant.</p>
<p><strong>Tenancy determines whether this matters at all.</strong> A single-workspace app can ignore the whole mechanism forever with no consequence. The identical missing scope becomes a customer-facing correctness bug the moment a second workspace installs, which is why the script reads your installation store before it reads anything else and reports a single-workspace app as dormant rather than as failing.</p>
<p><strong>An org-wide install is the sharpest version.</strong> On Enterprise Grid, one installation can span many workspaces, and the truncated array will name one of them. An app that serves only the named workspace looks correct to the admin who installed it and broken to everyone else in the org.</p>
<p><strong>Holding the scope is not the same as using it.</strong> The API can tell you the capability exists. It cannot tell you whether your handler calls it, paginates the cursor, or processes the event once per authorization, so the script reports capability and leaves behaviour to a source review rather than pretending to have checked.</p>""",
"steps": [
 {"h": "Ask your own store whether the app is multi-install",
  "body": """<p>Count distinct <code>team_id</code> values, and look for any record with <code>is_enterprise_install</code> set. One team is dormant, several teams is live, an org-wide install is live and wider than it looks. This is the number that decides how loudly the rest of the report speaks.</p>"""},
 {"h": "Look at one real event envelope",
  "body": """<p>Take a payload the app actually received and check three fields: is <code>event_context</code> present, is <code>authorizations</code> present, and how many entries does it have. One entry is the normal, truncated shape &mdash; it is not evidence that one installation was the intended audience, and code that reads it that way is the bug.</p>"""},
 {"h": "Ask once whether the capability exists",
  "body": """<p>A single probe of <code>apps.event.authorizations.list</code> with the app-level token, answering present, absent or unknown. Nothing more granular is needed here; the fine reading of that method's errors belongs to the Socket Mode note, and this one only needs to know whether the door opens.</p>"""},
 {"h": "Rank by tenancy, not by the error",
  "body": """<p>Absent capability plus several workspaces is a correctness bug affecting paying customers. Absent capability plus one workspace is a note for the roadmap. Reporting both at the same severity trains people to ignore the report, so the script gives the second one its own verdict and does not fail the run for it.</p>"""},
 {"h": "Fan out in the handler, and follow the cursor",
  "body": """<p>Call <code>apps.event.authorizations.list</code> with the payload's <code>event_context</code>, page through <code>response_metadata.next_cursor</code>, and process the event once per returned authorization with that installation's own token. Deduplicate on the pair of event id and authorization, not on the event id alone.</p>"""},
 {"h": "Say what the probe did not check",
  "body": """<p>The capability being present says nothing about whether the handler uses it. Put that sentence in the output. A report that claims to have verified fan-out when it verified a scope is worse than one that admits the boundary, because the next person will trust it.</p>"""},
],
"verify": """<p>Re-run after generating an app-level token with <code>authorizations:read</code>. The capability line should read present, and the verdict for a multi-workspace store should stop being a finding.</p>
<pre><code class="language-bash">python3 slack_event_fanout_audit.py --installs installs.json --event sample-event.json
# capability-present  4 distinct team_id(s) and the expansion call is available</code></pre>""",
"code_intro": "The live half is two GETs and the quiet half is where the answer is. <code>tenancy</code> reads your installation store, <code>delivery_shape</code> reads one captured envelope, <code>capability</code> reduces the app-level probe to three values, and <code>fanout_risk</code> combines the first and third into a severity &mdash; which is the only part of this that a caller should act on.",
"py_file": "slack_event_fanout_audit.py",
"py": '''"""Decide whether a Slack app is silently serving one installation per event.

Read only. Two GETs: one auth.test to name the app you are standing in, and one
probe of apps.event.authorizations.list to see whether the capability that fans
an event out to every installation exists at all. Everything else is read from
your own installation store and from one captured event envelope.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_fanout_audit")

API = "https://slack.com/api/"

PROBE_CONTEXT = "read-only-probe-not-a-real-event-context"

# Severities that should fail the run. A dormant finding is real but it is not
# breaking anything today, and failing on it teaches people to ignore the report.
FAILING = ("dropping-installations", "dropping-workspaces-in-org")


def tenancy(installs):
    """Classify the installation store. Pure. -> (state, detail)"""
    rows = [r for r in installs if isinstance(r, dict)]
    if not rows:
        return ("empty-store",
                "no installation records were supplied, so there is nothing to "
                "say about how many tenants an event should reach.")

    org_wide = [r for r in rows if r.get("is_enterprise_install")]
    teams = sorted({str(r.get("team_id")) for r in rows if r.get("team_id")})
    if org_wide:
        return ("enterprise-install",
                "%d org-wide install(s) across %d recorded team_id(s). One "
                "installation can span many workspaces, so a truncated "
                "authorizations array names one of them and hides the rest."
                % (len(org_wide), len(teams)))
    if len(teams) > 1:
        return ("multi-workspace",
                "%d distinct team_id(s) in the store, so events are routinely "
                "visible to more than one installation." % len(teams))
    return ("single-workspace",
            "one workspace installed. The fan-out mechanism has nothing to fan "
            "out to yet.")


def delivery_shape(event):
    """Read one captured event envelope. Pure. -> (state, detail)"""
    if not isinstance(event, dict):
        return ("no-envelope",
                "no event payload was supplied, so the delivery shape is unknown.")
    if not event.get("event_context"):
        return ("no-event-context",
                "the envelope carries no event_context. Either it predates the "
                "field or it is a hand-written fixture; with no handle there is "
                "nothing to expand and nothing to conclude.")

    authorizations = event.get("authorizations")
    if not isinstance(authorizations, list) or not authorizations:
        return ("no-authorizations",
                "event_context is present but authorizations is missing or "
                "empty, so the handler has no installation named at all and must "
                "expand the context before it can do anything.")

    shared = " The envelope is also marked is_ext_shared." if event.get("is_ext_shared") else ""
    if len(authorizations) == 1:
        return ("single-authorization",
                "one entry in authorizations, which is the normal truncated "
                "shape rather than a count of interested installations. Code "
                "that treats this length as the audience is the bug.%s" % shared)
    return ("multiple-authorizations",
            "%d entries in authorizations. Expand event_context anyway: the "
            "array is capped, so more is not the same as all.%s"
            % (len(authorizations), shared))


def capability(body):
    """Three-way read of the app-level probe. Pure. -> (state, detail)

    Deliberately coarse. All this note needs to know is whether the expansion
    call is available; the full reading of this method's errors belongs to the
    Socket Mode readiness check.
    """
    if body.get("ok") is True:
        return ("present", "the expansion call answered ok")
    error = body.get("error") or "<no error field>"
    if error in ("invalid_event_context", "event_context_invalid"):
        return ("present",
                "the probe context was refused as an argument, which means the "
                "credential and the scope were accepted before it")
    if error == "missing_scope":
        return ("absent",
                "missing_scope: the app-level token was minted without "
                "authorizations:read, so an event cannot be expanded")
    return ("unknown",
            "error=%s, which says nothing conclusive about the scope" % error)


def fanout_risk(tenancy_state, capability_state):
    """Combine tenancy with capability into a severity. Pure. -> (state, detail)"""
    if tenancy_state == "empty-store" or capability_state == "unknown":
        return ("not-assessed",
                "one of the two inputs is missing, so no severity can be "
                "assigned. Report it as unknown rather than as clean.")

    if capability_state == "absent":
        if tenancy_state == "enterprise-install":
            return ("dropping-workspaces-in-org",
                    "an org-wide installation with no way to expand an event. "
                    "The workspace named in the truncated array is served and "
                    "every other workspace in the org is silently skipped.")
        if tenancy_state == "multi-workspace":
            return ("dropping-installations",
                    "more than one installation and no way to expand an event. "
                    "Each event is handled for exactly one tenant, which is why "
                    "the bot appears to work for some customers and not others.")
        return ("dormant",
                "one workspace, so nothing is being dropped today. The day a "
                "second installation appears this becomes a correctness bug "
                "with no error attached, so fix it before you sell it.")

    if tenancy_state == "single-workspace":
        return ("capability-unused",
                "the scope is present and there is only one installation to "
                "serve. Nothing to do, and nothing wasted.")
    return ("capability-present",
            "the expansion call is available. Whether the handler actually "
            "calls it, follows the cursor and processes the event once per "
            "authorization is not visible from the API: read the handler.")


def get(session, url, token, params=None):
    r = session.get(url, headers={"Authorization": "Bearer " + token},
                    params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--installs", required=True,
                    help="JSON array of installation records: team_id, enterprise_id, "
                         "is_enterprise_install")
    ap.add_argument("--event", help="path to one captured event envelope")
    ap.add_argument("--app-token-env", default="SLACK_APP_TOKEN")
    ap.add_argument("--bot-token-env", default="SLACK_BOT_TOKEN")
    args = ap.parse_args()

    installs = json.loads(open(args.installs, encoding="utf-8").read())
    event = json.loads(open(args.event, encoding="utf-8").read()) if args.event else None

    ten_state, ten_detail = tenancy(installs)
    shape_state, shape_detail = delivery_shape(event)

    app_token = os.environ.get(args.app_token_env)
    if not app_token:
        log.error("%s is not set; the capability cannot be probed",
                  args.app_token_env)
        return 2

    s = requests.Session()
    bot_token = os.environ.get(args.bot_token_env)
    if bot_token:
        identity = get(s, API + "auth.test", bot_token)
        log.info("app: %s in team %s", identity.get("app_id") or "<unknown app_id>",
                 identity.get("team") or identity.get("team_id") or "<unknown team>")

    cap_state, cap_detail = capability(
        get(s, API + "apps.event.authorizations.list", app_token,
            {"event_context": PROBE_CONTEXT}))
    verdict, why = fanout_risk(ten_state, cap_state)

    log.info("%-28s %s", verdict, why)
    log.info("  tenancy:    %s -- %s", ten_state, ten_detail)
    log.info("  envelope:   %s -- %s", shape_state, shape_detail)
    log.info("  capability: %s -- %s", cap_state, cap_detail)

    if cap_state == "absent":
        log.warning("  repair: generate an app-level token with authorizations:read "
                    "on Basic Information, and deploy it as %s", args.app_token_env)
        log.warning("  repair: in the handler, expand payload.event_context via "
                    "apps.event.authorizations.list, page through "
                    "response_metadata.next_cursor, and process the event once per "
                    "authorization using that installation's own token")
        log.warning("  repair: deduplicate on the pair of event id and "
                    "authorization, not on the event id alone")

    return 1 if verdict in FAILING else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-fanout-audit.mjs",
"js": '''/**
 * Decide whether a Slack app is silently serving one installation per event.
 *
 * Read only. Two GETs: one auth.test to name the app you are standing in, and
 * one probe of apps.event.authorizations.list to see whether the capability that
 * fans an event out to every installation exists at all. Everything else is read
 * from your own installation store and from one captured event envelope.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

const PROBE_CONTEXT = 'read-only-probe-not-a-real-event-context';

// Severities that should fail the run. A dormant finding is real but it is not
// breaking anything today, and failing on it teaches people to ignore the report.
const FAILING = new Set(['dropping-installations', 'dropping-workspaces-in-org']);

/**
 * Classify the installation store. Pure.
 */
export function tenancy(installs) {
  const rows = (installs ?? []).filter((r) => r && typeof r === 'object');
  if (rows.length === 0) {
    return ['empty-store',
      'no installation records were supplied, so there is nothing to say about ' +
      'how many tenants an event should reach.'];
  }

  const orgWide = rows.filter((r) => r.is_enterprise_install);
  const teams = [...new Set(rows.filter((r) => r.team_id).map((r) => String(r.team_id)))];
  if (orgWide.length) {
    return ['enterprise-install',
      `${orgWide.length} org-wide install(s) across ${teams.length} recorded ` +
      'team_id(s). One installation can span many workspaces, so a truncated ' +
      'authorizations array names one of them and hides the rest.'];
  }
  if (teams.length > 1) {
    return ['multi-workspace',
      `${teams.length} distinct team_id(s) in the store, so events are routinely ` +
      'visible to more than one installation.'];
  }
  return ['single-workspace',
    'one workspace installed. The fan-out mechanism has nothing to fan out to yet.'];
}

/**
 * Read one captured event envelope. Pure.
 */
export function deliveryShape(event) {
  if (!event || typeof event !== 'object' || Array.isArray(event)) {
    return ['no-envelope',
      'no event payload was supplied, so the delivery shape is unknown.'];
  }
  if (!event.event_context) {
    return ['no-event-context',
      'the envelope carries no event_context. Either it predates the field or it ' +
      'is a hand-written fixture; with no handle there is nothing to expand and ' +
      'nothing to conclude.'];
  }

  const authorizations = event.authorizations;
  if (!Array.isArray(authorizations) || authorizations.length === 0) {
    return ['no-authorizations',
      'event_context is present but authorizations is missing or empty, so the ' +
      'handler has no installation named at all and must expand the context ' +
      'before it can do anything.'];
  }

  const shared = event.is_ext_shared ? ' The envelope is also marked is_ext_shared.' : '';
  if (authorizations.length === 1) {
    return ['single-authorization',
      'one entry in authorizations, which is the normal truncated shape rather ' +
      'than a count of interested installations. Code that treats this length as ' +
      `the audience is the bug.${shared}`];
  }
  return ['multiple-authorizations',
    `${authorizations.length} entries in authorizations. Expand event_context ` +
    `anyway: the array is capped, so more is not the same as all.${shared}`];
}

/**
 * Three-way read of the app-level probe. Pure.
 * Deliberately coarse: all this note needs to know is whether the expansion call
 * is available.
 */
export function capability(body) {
  if (body?.ok === true) return ['present', 'the expansion call answered ok'];
  const error = body?.error ?? '<no error field>';
  if (error === 'invalid_event_context' || error === 'event_context_invalid') {
    return ['present',
      'the probe context was refused as an argument, which means the credential ' +
      'and the scope were accepted before it'];
  }
  if (error === 'missing_scope') {
    return ['absent',
      'missing_scope: the app-level token was minted without authorizations:read, ' +
      'so an event cannot be expanded'];
  }
  return ['unknown', `error=${error}, which says nothing conclusive about the scope`];
}

/**
 * Combine tenancy with capability into a severity. Pure.
 */
export function fanoutRisk(tenancyState, capabilityState) {
  if (tenancyState === 'empty-store' || capabilityState === 'unknown') {
    return ['not-assessed',
      'one of the two inputs is missing, so no severity can be assigned. Report ' +
      'it as unknown rather than as clean.'];
  }

  if (capabilityState === 'absent') {
    if (tenancyState === 'enterprise-install') {
      return ['dropping-workspaces-in-org',
        'an org-wide installation with no way to expand an event. The workspace ' +
        'named in the truncated array is served and every other workspace in the ' +
        'org is silently skipped.'];
    }
    if (tenancyState === 'multi-workspace') {
      return ['dropping-installations',
        'more than one installation and no way to expand an event. Each event is ' +
        'handled for exactly one tenant, which is why the bot appears to work for ' +
        'some customers and not others.'];
    }
    return ['dormant',
      'one workspace, so nothing is being dropped today. The day a second ' +
      'installation appears this becomes a correctness bug with no error ' +
      'attached, so fix it before you sell it.'];
  }

  if (tenancyState === 'single-workspace') {
    return ['capability-unused',
      'the scope is present and there is only one installation to serve. Nothing ' +
      'to do, and nothing wasted.'];
  }
  return ['capability-present',
    'the expansion call is available. Whether the handler actually calls it, ' +
    'follows the cursor and processes the event once per authorization is not ' +
    'visible from the API: read the handler.'];
}

async function get(url, token, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(qs ? `${url}?${qs}` : url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const installsPath = arg(args, '--installs');
  if (!installsPath) {
    console.error('usage: --installs installs.json [--event sample-event.json]');
    process.exitCode = 2;
    return;
  }
  const eventPath = arg(args, '--event');
  const appTokenEnv = arg(args, '--app-token-env', 'SLACK_APP_TOKEN');
  const botTokenEnv = arg(args, '--bot-token-env', 'SLACK_BOT_TOKEN');

  const installs = JSON.parse(await readFile(installsPath, 'utf8'));
  const event = eventPath ? JSON.parse(await readFile(eventPath, 'utf8')) : null;

  const [tenState, tenDetail] = tenancy(installs);
  const [shapeState, shapeDetail] = deliveryShape(event);

  const appToken = process.env[appTokenEnv];
  if (!appToken) {
    console.error(`${appTokenEnv} is not set; the capability cannot be probed`);
    process.exitCode = 2;
    return;
  }

  const botToken = process.env[botTokenEnv];
  if (botToken) {
    const identity = await get(`${API}auth.test`, botToken);
    console.log(`app: ${identity.app_id ?? '<unknown app_id>'} in team ` +
                `${identity.team ?? identity.team_id ?? '<unknown team>'}`);
  }

  const [capState, capDetail] = capability(
    await get(`${API}apps.event.authorizations.list`, appToken,
      { event_context: PROBE_CONTEXT }));
  const [verdict, why] = fanoutRisk(tenState, capState);

  console.log(`${verdict.padEnd(28)} ${why}`);
  console.log(`  tenancy:    ${tenState} -- ${tenDetail}`);
  console.log(`  envelope:   ${shapeState} -- ${shapeDetail}`);
  console.log(`  capability: ${capState} -- ${capDetail}`);

  if (capState === 'absent') {
    console.warn('  repair: generate an app-level token with authorizations:read on ' +
                 `Basic Information, and deploy it as ${appTokenEnv}`);
    console.warn('  repair: in the handler, expand payload.event_context via ' +
                 'apps.event.authorizations.list, page through ' +
                 'response_metadata.next_cursor, and process the event once per ' +
                 "authorization using that installation's own token");
    console.warn('  repair: deduplicate on the pair of event id and authorization, ' +
                 'not on the event id alone');
  }

  process.exitCode = FAILING.has(verdict) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// go looking for an installation store.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions carry the note. The first is that an <code>authorizations</code> array of length one is reported as a truncation rather than as an audience &mdash; get that wrong and the script confirms the bug it is meant to find. The second is that the same missing scope produces a failing verdict for a multi-tenant store and a non-failing one for a single workspace, which is the whole reason severity is computed rather than asserted.",
"test_py_file": "test_slack_event_fanout_audit.py",
"test_py": '''from slack_event_fanout_audit import (capability, delivery_shape, fanout_risk,
                                       tenancy)


def test_distinct_teams_make_the_app_multi_install():
    state, detail = tenancy([{"team_id": "T1"}, {"team_id": "T2"}, {"team_id": "T2"}])
    assert state == "multi-workspace"
    assert "2 distinct" in detail


def test_an_org_wide_install_outranks_the_team_count():
    state, _ = tenancy([{"team_id": "T1", "is_enterprise_install": True}])
    assert state == "enterprise-install"


def test_one_workspace_is_not_a_multi_install_app():
    assert tenancy([{"team_id": "T1"}])[0] == "single-workspace"
    assert tenancy([])[0] == "empty-store"


def test_a_single_authorization_is_truncation_not_an_audience():
    state, detail = delivery_shape({"event_context": "ec-1",
                                    "authorizations": [{"team_id": "T1"}]})
    assert state == "single-authorization"
    assert "truncated shape" in detail


def test_an_externally_shared_envelope_is_called_out():
    _, detail = delivery_shape({"event_context": "ec-1", "is_ext_shared": True,
                                "authorizations": [{"team_id": "T1"}]})
    assert "is_ext_shared" in detail


def test_a_missing_event_context_stops_the_envelope_read():
    assert delivery_shape({"authorizations": []})[0] == "no-event-context"
    assert delivery_shape(None)[0] == "no-envelope"


def test_the_probe_reduces_to_three_values():
    assert capability({"ok": False, "error": "invalid_event_context"})[0] == "present"
    assert capability({"ok": False, "error": "missing_scope"})[0] == "absent"
    assert capability({"ok": False, "error": "ratelimited"})[0] == "unknown"


def test_missing_scope_on_a_multi_tenant_app_is_the_failing_finding():
    state, detail = fanout_risk("multi-workspace", "absent")
    assert state == "dropping-installations"
    assert "some customers and not others" in detail


def test_the_same_gap_on_one_workspace_is_dormant_rather_than_failing():
    state, detail = fanout_risk("single-workspace", "absent")
    assert state == "dormant"
    assert "before you sell it" in detail


def test_an_org_wide_install_gets_its_own_severity():
    assert fanout_risk("enterprise-install", "absent")[0] == "dropping-workspaces-in-org"


def test_having_the_scope_is_not_a_claim_that_the_handler_uses_it():
    state, detail = fanout_risk("multi-workspace", "present")
    assert state == "capability-present"
    assert "read the handler" in detail


def test_a_missing_input_downgrades_to_not_assessed():
    assert fanout_risk("empty-store", "present")[0] == "not-assessed"
    assert fanout_risk("multi-workspace", "unknown")[0] == "not-assessed"
''',
"test_js_file": "slack-event-fanout-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { capability, deliveryShape, fanoutRisk, tenancy } from './slack-event-fanout-audit.mjs';

test('distinct teams make the app multi-install', () => {
  const [state, detail] = tenancy([{ team_id: 'T1' }, { team_id: 'T2' }, { team_id: 'T2' }]);
  assert.equal(state, 'multi-workspace');
  assert.match(detail, /2 distinct/);
});

test('an org-wide install outranks the team count', () => {
  assert.equal(tenancy([{ team_id: 'T1', is_enterprise_install: true }])[0],
    'enterprise-install');
});

test('one workspace is not a multi-install app', () => {
  assert.equal(tenancy([{ team_id: 'T1' }])[0], 'single-workspace');
  assert.equal(tenancy([])[0], 'empty-store');
});

test('a single authorization is truncation not an audience', () => {
  const [state, detail] = deliveryShape({
    event_context: 'ec-1', authorizations: [{ team_id: 'T1' }],
  });
  assert.equal(state, 'single-authorization');
  assert.match(detail, /truncated shape/);
});

test('an externally shared envelope is called out', () => {
  const [, detail] = deliveryShape({
    event_context: 'ec-1', is_ext_shared: true, authorizations: [{ team_id: 'T1' }],
  });
  assert.match(detail, /is_ext_shared/);
});

test('a missing event_context stops the envelope read', () => {
  assert.equal(deliveryShape({ authorizations: [] })[0], 'no-event-context');
  assert.equal(deliveryShape(null)[0], 'no-envelope');
});

test('the probe reduces to three values', () => {
  assert.equal(capability({ ok: false, error: 'invalid_event_context' })[0], 'present');
  assert.equal(capability({ ok: false, error: 'missing_scope' })[0], 'absent');
  assert.equal(capability({ ok: false, error: 'ratelimited' })[0], 'unknown');
});

test('missing scope on a multi-tenant app is the failing finding', () => {
  const [state, detail] = fanoutRisk('multi-workspace', 'absent');
  assert.equal(state, 'dropping-installations');
  assert.match(detail, /some customers and not others/);
});

test('the same gap on one workspace is dormant rather than failing', () => {
  const [state, detail] = fanoutRisk('single-workspace', 'absent');
  assert.equal(state, 'dormant');
  assert.match(detail, /before you sell it/);
});

test('having the scope is not a claim that the handler uses it', () => {
  const [state, detail] = fanoutRisk('multi-workspace', 'present');
  assert.equal(state, 'capability-present');
  assert.match(detail, /read the handler/);
});

test('a missing input downgrades to not assessed', () => {
  assert.equal(fanoutRisk('empty-store', 'present')[0], 'not-assessed');
  assert.equal(fanoutRisk('multi-workspace', 'unknown')[0], 'not-assessed');
});
''',
"faq": [
 ("Why does Slack send one event instead of one per installation?",
  "Because it does not know how your app is organised. Fan-out is a decision about sharding, batching and deduplication that belongs to you, so Slack sends a single delivery with a handle, event_context, and a method that expands it. The design pushes the choice to the side that can make it, at the cost of a step that is easy to skip."),
 ("Is a one-entry authorizations array ever the true audience?",
  "For a single-workspace app, yes, trivially. For anything else, treat it as a sample: the array is documented as truncated and the length is not a count. The safe rule is to never branch on that length at all, since the code that expands event_context works correctly whether there is one interested installation or forty."),
 ("Does this affect a single-workspace app at all?",
  "Not today. The script reports it as dormant and does not fail the run, because nothing is being dropped and the repair is a token regeneration nobody needs yet. It matters the moment a second workspace installs, and since that day usually arrives without a deploy, the finding is worth carrying on the roadmap rather than in an incident."),
 ("Can the script tell me whether my handler actually fans out?",
  "No, and it says so in its own output. The API can show that the capability exists; it cannot see whether your code calls apps.event.authorizations.list, follows response_metadata.next_cursor, or processes the event once per authorization. That part is a source review, and treating a present scope as proof of correct behaviour is exactly the mistake this note is about."),
 ("How should deduplication work once fan-out is in place?",
  "Key on the pair of event id and authorization rather than on the event id alone. A single event legitimately produces several units of work, one per installation, and a dedupe key built from the event id will discard all but the first of them, which reproduces the original bug through a different route."),
],
"related": [
 ("/slack/app-level-token-missing-connections-write/", "the other app-level scope"),
 ("/slack/enterprise-id-not-stored/", "installs that span an org"),
 ("/slack/event-subscriptions-auto-disabled/", "when Slack stops delivering"),
],
"citations": [CITE_EVENT_AUTHZ, CITE_EVENTS_API, CITE_GRID, CITE_TOKENS],
},

{
"slug": "config-token-expired",
"title": "The Slack app configuration token died twelve hours ago",
"description": "App configuration tokens live 12 hours and rotate through tooling.tokens.rotate. When one dies, every manifest check must read as not assessed.",
"h1": "The Slack app configuration token died twelve hours ago",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack app configuration token expired", "tooling.tokens.rotate",
             "apps.manifest.export invalid_auth", "app_configurations:read",
             "slack manifest ci token"],
"deps": "Python 3.9+ with requests, or Node.js 18+; needs an app configuration token",
"lead": "The manifest step in CI passed yesterday and fails today. Someone regenerates the token by hand, the build goes green, and the same thing happens tomorrow morning. Meanwhile the audit that runs beside it reports every manifest-derived check as clean, because a check that could not run returned nothing to complain about.",
"short_answer": """<p>App configuration tokens are a <strong>separate credential class</strong> from the tokens your app runs on. They are used only by the <code>apps.manifest.*</code> and <code>tooling.tokens.*</code> families, they are issued as an access and refresh <strong>pair</strong> from the app management page, and the access half expires after <strong>twelve hours</strong>. The refresh half is redeemed through <code>tooling.tokens.rotate</code>, not through <code>oauth.v2.access</code> &mdash; a different endpoint from the one that rotates workspace tokens.</p>
<p>Paste the access token into a CI secret and you get one working day out of it. Store the <em>refresh</em> token and rotate at the start of every run and it keeps working indefinitely, provided you write both returned values back, because the new refresh token is single use too.</p>
<p>The second half of this note is the part that matters more. When the configuration token is dead, every check in your audit that reads the manifest cannot run &mdash; and a check that cannot run must be reported as <strong>not assessed</strong>, never as clean. The script below establishes the token's state, then splits the audit's own check list into what was actually assessed and what was silently skipped.</p>""",
"problem": """<p>Nothing about this failure touches the running app. The bot keeps posting, events keep arriving, customers notice nothing. What breaks is the tooling around the app: manifest sync, drift detection, the audit that reads <code>settings.socket_mode_enabled</code> to decide whether Socket Mode is even the transport. All of it goes quiet, and quiet reads as fine.</p>
<p>The twelve-hour life is the trap because it is just long enough. A developer generates a token, wires the pipeline, watches three builds pass, and ships. The token dies overnight. The first failure looks like a flake, the second like an infrastructure problem, and the manual regeneration that fixes it also resets the clock, so the pattern takes several days to become visible as a pattern.</p>
<p>The rotation endpoint being different from the workspace one compounds it. Teams that already built a refresh loop for rotating bot tokens reach for <code>oauth.v2.access</code>, get an error that does not obviously mean "wrong endpoint", and conclude that configuration tokens cannot be refreshed programmatically. They can; the call is <code>tooling.tokens.rotate</code> and it takes the refresh token.</p>
<p>And underneath all of it sits the reporting problem. An audit that runs twenty checks, six of which need the manifest, will happily print fourteen results and a summary line saying no problems found. That summary is false, and it is false in the direction that makes people stop looking.</p>""",
"why": """<p><strong>This is not the app's token and not the app's clock.</strong> A rotating workspace token lives twelve hours too, but it is a different credential, refreshed at a different endpoint, held by a different process. Conflating them sends someone to fix the app's refresh loop when the app was never involved.</p>
<p><strong>Store the refresh half, derive the access half.</strong> The access token is a twelve-hour artefact; the refresh token is the durable secret. A pipeline that holds the access token is holding the wrong string, and no amount of care about expiry makes it the right one.</p>
<p><strong>Both halves come back, and both must be written.</strong> <code>tooling.tokens.rotate</code> returns a new access token <em>and</em> a new refresh token, and the old refresh token is spent. Persisting only the access token leaves the next run holding a refresh token that has already been redeemed, which fails identically to expiry and is usually diagnosed as expiry.</p>
<p><strong>The error tells you which of four things went wrong.</strong> <code>token_expired</code> and <code>invalid_auth</code> mean the pair needs rotating; <code>missing_scope</code> means the token was created without <code>app_configurations:read</code>; <code>app_not_found</code> or <code>invalid_app_id</code> mean the token belongs to a different app account. Those are four different repairs and it is worth naming which one applies.</p>
<p><strong>A blind check is not a passing check.</strong> This is the honest-reporting rule that the whole note is built around. When the credential that powers a branch of the audit is dead, that branch is unknown, and the summary has to say how many checks were skipped. Otherwise the audit's most useful property &mdash; that a clean run means something &mdash; is gone.</p>""",
"steps": [
 {"h": "Ask the manifest API one question",
  "body": """<p>A single read of <code>apps.manifest.export</code> for the app id you care about. You are not looking at the manifest yet; you are looking at whether the credential works, and the error name distinguishes expiry from a missing scope from a token issued against a different app account.</p>"""},
 {"h": "Check which half of the pair the environment holds",
  "body": """<p>If only the access token is present, the pipeline has a one-day credential and will fail tomorrow regardless of what today's call returned. If only the refresh token is present, that is the correct shape: the access token should be derived per run and never stored at all.</p>"""},
 {"h": "Rotate at the start of the run, not on failure",
  "body": """<p>Call <code>tooling.tokens.rotate</code> with the refresh token as the first step of the job, before anything can half-succeed. Rotating in an error handler means the first call of every run is a call you expect to fail, which makes real failures indistinguishable from routine ones.</p>"""},
 {"h": "Write both returned values back",
  "body": """<p>The rotate call returns a new access token and a new refresh token, and the refresh token you sent is spent. Persist both into the secret store in one operation. A pipeline that saves only the access token works exactly once more and then fails in a way that looks like expiry.</p>"""},
 {"h": "Mark the manifest checks not assessed",
  "body": """<p>Take the audit's own check list, tagged with which entries need the manifest, and split it. Print the deferred names individually rather than as a count, and make sure the summary line distinguishes zero problems from zero problems observed. This is the step that keeps the rest of the audit trustworthy.</p>"""},
 {"h": "Split read from write across two tokens",
  "body": """<p>Give the audit a token scoped <code>app_configurations:read</code> and give only the deployment pipeline one that can write. They rotate independently, and a leaked audit credential cannot rewrite your app's manifest.</p>"""},
],
"verify": """<p>With the refresh token in the secret store and the rotate step at the top of the job, the run should report the manifest as readable and defer nothing.</p>
<pre><code class="language-bash">python3 slack_config_token_state.py --app-id A0123456789
# readable  the configuration token works; 0 check(s) deferred</code></pre>""",
"code_intro": "One GET, and then the part that is really the point. <code>manifest_access</code> turns the answer into one of five states with a repair attached to each, <code>stored_pair</code> says which half of the credential pair the environment is holding, and <code>coverage</code> takes the audit's own list of checks and splits it into what was assessed and what has to be reported as unknown. That last function is why the script exists.",
"py_file": "slack_config_token_state.py",
"py": '''"""Report the state of a Slack app configuration token, and what its death hides.

Read only. One GET of apps.manifest.export, purely to establish whether the
credential works. The point of the script is the second half: when that call
fails, every check in the audit that depends on the manifest has to be reported
as not assessed rather than quietly as clean.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_config_token_state")

API = "https://slack.com/api/"

# The audit's own checks, tagged with whether they need the manifest. Replace
# this with your real list; the shape is what matters.
DEFAULT_CHECKS = [
    ("bot token identity", False),
    ("granted scope list", False),
    ("bot channel membership", False),
    ("request URL configured", True),
    ("socket mode setting", True),
    ("token rotation enabled", True),
    ("scopes declared in the manifest", True),
]


def manifest_access(body):
    """Name the state of the configuration token. Pure. -> (state, detail)"""
    if body.get("ok") is True:
        return ("readable",
                "the configuration token works and the manifest came back.")

    error = body.get("error") or "<no error field>"
    if error in ("token_expired", "expired_token"):
        return ("expired",
                "token_expired: configuration tokens live twelve hours. Rotate "
                "the pair with tooling.tokens.rotate rather than regenerating by "
                "hand every morning.")
    if error == "invalid_auth":
        return ("rejected",
                "invalid_auth: the stored value is not a usable configuration "
                "token. It is often the access half of a pair that has already "
                "expired, or a workspace token in the wrong slot.")
    if error == "missing_scope":
        return ("missing-app-configurations-read",
                "missing_scope: the configuration token was created without "
                "app_configurations:read, so it cannot read a manifest at all.")
    if error in ("app_not_found", "invalid_app_id"):
        return ("wrong-app-account",
                "%s: the token is valid but was issued under a different app "
                "account, or the app id does not belong to it." % error)
    if error == "ratelimited":
        return ("unknown", "ratelimited: no conclusion is available this run.")
    return ("unknown",
            "error=%s, which is not one of the answers this check knows. Treat "
            "the manifest as unavailable." % error)


def stored_pair(present):
    """Which half of the credential pair the environment holds. Pure.

    `present` is {"access": bool, "refresh": bool}. -> (state, detail)
    """
    access, refresh = bool(present.get("access")), bool(present.get("refresh"))
    if not access and not refresh:
        return ("no-credential",
                "neither half of the pair is in the environment, so no manifest "
                "check can run at all.")
    if access and not refresh:
        return ("access-only",
                "only the access token is stored. That is the half that dies in "
                "twelve hours, so this pipeline has a one-day credential no "
                "matter what today's call returned.")
    if refresh and not access:
        return ("refresh-only",
                "only the refresh token is stored, which is the right shape: "
                "rotate at the start of the run and let the access token exist "
                "for the length of the job and no longer.")
    return ("both-stored",
            "both halves are stored. Fine, as long as the rotate step writes "
            "both returned values back; writing only one breaks the next run.")


def coverage(access_state, checks):
    """Split the audit's checks into assessed and deferred. Pure.

    `checks` is [(name, needs_manifest), ...]. Returns (assessed, deferred).
    A check that could not run is not a check that passed.
    """
    blind = access_state != "readable"
    assessed, deferred = [], []
    for name, needs_manifest in checks:
        target = deferred if (blind and needs_manifest) else assessed
        target.append(name)
    return (assessed, deferred)


def export_manifest(session, token, app_id):
    """One GET. We want the error, not the manifest."""
    r = session.get(API + "apps.manifest.export",
                    headers={"Authorization": "Bearer " + token},
                    params={"app_id": app_id}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", required=True, help="the app id to export, A...")
    ap.add_argument("--access-env", default="SLACK_CONFIG_ACCESS_TOKEN")
    ap.add_argument("--refresh-env", default="SLACK_CONFIG_REFRESH_TOKEN")
    args = ap.parse_args()

    access = os.environ.get(args.access_env)
    present = {"access": bool(access),
               "refresh": bool(os.environ.get(args.refresh_env))}
    pair_state, pair_detail = stored_pair(present)

    if not access:
        state, detail = ("unknown",
                         "%s is not set, so the manifest was never asked for."
                         % args.access_env)
    else:
        state, detail = manifest_access(
            export_manifest(requests.Session(), access, args.app_id))

    assessed, deferred = coverage(state, DEFAULT_CHECKS)

    log.info("%-32s %s", state, detail)
    log.info("  credential: %s -- %s", pair_state, pair_detail)
    log.info("  %d check(s) assessed, %d deferred", len(assessed), len(deferred))
    for name in deferred:
        log.warning("  not assessed: %s", name)

    if state == "expired" or pair_state == "access-only":
        log.warning("  repair: store the refresh token in CI, not the access token, "
                    "and call tooling.tokens.rotate with it at the start of every run")
        log.warning("  repair: persist BOTH values the rotate call returns; the new "
                    "refresh token is single use too, so writing one of them breaks "
                    "the next run")
    if state == "missing-app-configurations-read":
        log.warning("  repair: reissue the configuration token with "
                    "app_configurations:read for audit use, and keep "
                    "app_configurations:write to the pipeline that deploys manifests")
    if state == "wrong-app-account":
        log.warning("  repair: configuration tokens are issued per app account. "
                    "Reissue from the account that owns %s", args.app_id)
    if deferred:
        log.warning("  note: those checks did not run. Do not read their silence as "
                    "a pass in whatever consumes this report.")

    return 0 if state == "readable" and pair_state != "access-only" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-config-token-state.mjs",
"js": '''/**
 * Report the state of a Slack app configuration token, and what its death hides.
 *
 * Read only. One GET of apps.manifest.export, purely to establish whether the
 * credential works. The point of the script is the second half: when that call
 * fails, every check in the audit that depends on the manifest has to be
 * reported as not assessed rather than quietly as clean.
 */
const API = 'https://slack.com/api/';

// The audit's own checks, tagged with whether they need the manifest. Replace
// this with your real list; the shape is what matters.
export const DEFAULT_CHECKS = [
  ['bot token identity', false],
  ['granted scope list', false],
  ['bot channel membership', false],
  ['request URL configured', true],
  ['socket mode setting', true],
  ['token rotation enabled', true],
  ['scopes declared in the manifest', true],
];

/**
 * Name the state of the configuration token. Pure.
 */
export function manifestAccess(body) {
  if (body?.ok === true) {
    return ['readable', 'the configuration token works and the manifest came back.'];
  }

  const error = body?.error ?? '<no error field>';
  if (error === 'token_expired' || error === 'expired_token') {
    return ['expired',
      'token_expired: configuration tokens live twelve hours. Rotate the pair with ' +
      'tooling.tokens.rotate rather than regenerating by hand every morning.'];
  }
  if (error === 'invalid_auth') {
    return ['rejected',
      'invalid_auth: the stored value is not a usable configuration token. It is ' +
      'often the access half of a pair that has already expired, or a workspace ' +
      'token in the wrong slot.'];
  }
  if (error === 'missing_scope') {
    return ['missing-app-configurations-read',
      'missing_scope: the configuration token was created without ' +
      'app_configurations:read, so it cannot read a manifest at all.'];
  }
  if (error === 'app_not_found' || error === 'invalid_app_id') {
    return ['wrong-app-account',
      `${error}: the token is valid but was issued under a different app account, ` +
      'or the app id does not belong to it.'];
  }
  if (error === 'ratelimited') {
    return ['unknown', 'ratelimited: no conclusion is available this run.'];
  }
  return ['unknown',
    `error=${error}, which is not one of the answers this check knows. Treat the ` +
    'manifest as unavailable.'];
}

/**
 * Which half of the credential pair the environment holds. Pure.
 * `present` is { access: bool, refresh: bool }.
 */
export function storedPair(present) {
  const access = Boolean(present?.access);
  const refresh = Boolean(present?.refresh);
  if (!access && !refresh) {
    return ['no-credential',
      'neither half of the pair is in the environment, so no manifest check can ' +
      'run at all.'];
  }
  if (access && !refresh) {
    return ['access-only',
      'only the access token is stored. That is the half that dies in twelve ' +
      'hours, so this pipeline has a one-day credential no matter what the call ' +
      'in this run returned.'];
  }
  if (refresh && !access) {
    return ['refresh-only',
      'only the refresh token is stored, which is the right shape: rotate at the ' +
      'start of the run and let the access token exist for the length of the job ' +
      'and no longer.'];
  }
  return ['both-stored',
    'both halves are stored. Fine, as long as the rotate step writes both returned ' +
    'values back; writing only one breaks the next run.'];
}

/**
 * Split the audit's checks into assessed and deferred. Pure.
 * `checks` is [[name, needsManifest], ...]. A check that could not run is not a
 * check that passed.
 */
export function coverage(accessState, checks) {
  const blind = accessState !== 'readable';
  const assessed = [];
  const deferred = [];
  for (const [name, needsManifest] of checks) {
    (blind && needsManifest ? deferred : assessed).push(name);
  }
  return [assessed, deferred];
}

async function exportManifest(token, appId) {
  const url = `${API}apps.manifest.export?app_id=${encodeURIComponent(appId)}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id');
  if (!appId) {
    console.error('usage: --app-id A0123456789 [--access-env NAME] [--refresh-env NAME]');
    process.exitCode = 2;
    return;
  }
  const accessEnv = arg(args, '--access-env', 'SLACK_CONFIG_ACCESS_TOKEN');
  const refreshEnv = arg(args, '--refresh-env', 'SLACK_CONFIG_REFRESH_TOKEN');

  const access = process.env[accessEnv];
  const [pairState, pairDetail] = storedPair({
    access: Boolean(access), refresh: Boolean(process.env[refreshEnv]),
  });

  const [state, detail] = access
    ? manifestAccess(await exportManifest(access, appId))
    : ['unknown', `${accessEnv} is not set, so the manifest was never asked for.`];

  const [assessed, deferred] = coverage(state, DEFAULT_CHECKS);

  console.log(`${state.padEnd(32)} ${detail}`);
  console.log(`  credential: ${pairState} -- ${pairDetail}`);
  console.log(`  ${assessed.length} check(s) assessed, ${deferred.length} deferred`);
  for (const name of deferred) console.warn(`  not assessed: ${name}`);

  if (state === 'expired' || pairState === 'access-only') {
    console.warn('  repair: store the refresh token in CI, not the access token, and ' +
                 'call tooling.tokens.rotate with it at the start of every run');
    console.warn('  repair: persist BOTH values the rotate call returns; the new ' +
                 'refresh token is single use too, so writing one of them breaks the ' +
                 'next run');
  }
  if (state === 'missing-app-configurations-read') {
    console.warn('  repair: reissue the configuration token with ' +
                 'app_configurations:read for audit use, and keep ' +
                 'app_configurations:write to the pipeline that deploys manifests');
  }
  if (state === 'wrong-app-account') {
    console.warn('  repair: configuration tokens are issued per app account. Reissue ' +
                 `from the account that owns ${appId}`);
  }
  if (deferred.length) {
    console.warn('  note: those checks did not run. Do not read their silence as a ' +
                 'pass in whatever consumes this report.');
  }

  process.exitCode = (state === 'readable' && pairState !== 'access-only') ? 0 : 1;
}

// Only run when invoked directly, so importing this module in the tests does not
// require an app id on the command line.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The suite spends most of its assertions on <code>coverage</code>, because that is the function whose failure mode is a false clean bill of health rather than a wrong label. The others pin the four repairs apart &mdash; expiry, missing scope, wrong app account, wrong credential entirely &mdash; and pin the credential shape that guarantees tomorrow's failure even when today's call succeeded.",
"test_py_file": "test_slack_config_token_state.py",
"test_py": '''from slack_config_token_state import coverage, manifest_access, stored_pair

CHECKS = [("bot identity", False), ("socket mode setting", True),
          ("request URL configured", True)]


def test_a_readable_manifest_assesses_everything():
    assessed, deferred = coverage("readable", CHECKS)
    assert deferred == []
    assert len(assessed) == 3


def test_a_dead_token_defers_the_manifest_checks_rather_than_passing_them():
    assessed, deferred = coverage("expired", CHECKS)
    assert assessed == ["bot identity"]
    assert deferred == ["socket mode setting", "request URL configured"]


def test_every_unreadable_state_defers_the_same_way():
    for state in ("rejected", "missing-app-configurations-read",
                  "wrong-app-account", "unknown"):
        assert coverage(state, CHECKS)[1] == ["socket mode setting",
                                              "request URL configured"]


def test_expiry_names_the_rotate_endpoint_not_the_oauth_one():
    state, detail = manifest_access({"ok": False, "error": "token_expired"})
    assert state == "expired"
    assert "tooling.tokens.rotate" in detail


def test_a_missing_scope_is_not_an_expiry():
    state, _ = manifest_access({"ok": False, "error": "missing_scope"})
    assert state == "missing-app-configurations-read"


def test_the_token_belonging_to_another_app_account_is_its_own_state():
    assert manifest_access({"ok": False,
                            "error": "app_not_found"})[0] == "wrong-app-account"
    assert manifest_access({"ok": False,
                            "error": "invalid_app_id"})[0] == "wrong-app-account"


def test_an_unrecognised_error_leaves_the_manifest_unavailable():
    assert manifest_access({"ok": False, "error": "fatal_error"})[0] == "unknown"
    assert manifest_access({"ok": True})[0] == "readable"


def test_holding_only_the_access_token_is_a_one_day_credential():
    state, detail = stored_pair({"access": True, "refresh": False})
    assert state == "access-only"
    assert "one-day credential" in detail


def test_holding_only_the_refresh_token_is_the_right_shape():
    state, detail = stored_pair({"access": False, "refresh": True})
    assert state == "refresh-only"
    assert "right shape" in detail


def test_holding_both_is_conditional_on_writing_both_back():
    state, detail = stored_pair({"access": True, "refresh": True})
    assert state == "both-stored"
    assert "writing only one" in detail


def test_holding_neither_is_reported_before_any_call_is_made():
    assert stored_pair({})[0] == "no-credential"
''',
"test_js_file": "slack-config-token-state.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage, manifestAccess, storedPair } from './slack-config-token-state.mjs';

const CHECKS = [['bot identity', false], ['socket mode setting', true],
  ['request URL configured', true]];

test('a readable manifest assesses everything', () => {
  const [assessed, deferred] = coverage('readable', CHECKS);
  assert.deepEqual(deferred, []);
  assert.equal(assessed.length, 3);
});

test('a dead token defers the manifest checks rather than passing them', () => {
  const [assessed, deferred] = coverage('expired', CHECKS);
  assert.deepEqual(assessed, ['bot identity']);
  assert.deepEqual(deferred, ['socket mode setting', 'request URL configured']);
});

test('every unreadable state defers the same way', () => {
  for (const state of ['rejected', 'missing-app-configurations-read',
    'wrong-app-account', 'unknown']) {
    assert.deepEqual(coverage(state, CHECKS)[1],
      ['socket mode setting', 'request URL configured']);
  }
});

test('expiry names the rotate endpoint not the oauth one', () => {
  const [state, detail] = manifestAccess({ ok: false, error: 'token_expired' });
  assert.equal(state, 'expired');
  assert.match(detail, /tooling\\.tokens\\.rotate/);
});

test('a missing scope is not an expiry', () => {
  assert.equal(manifestAccess({ ok: false, error: 'missing_scope' })[0],
    'missing-app-configurations-read');
});

test('the token belonging to another app account is its own state', () => {
  assert.equal(manifestAccess({ ok: false, error: 'app_not_found' })[0],
    'wrong-app-account');
  assert.equal(manifestAccess({ ok: false, error: 'invalid_app_id' })[0],
    'wrong-app-account');
});

test('an unrecognised error leaves the manifest unavailable', () => {
  assert.equal(manifestAccess({ ok: false, error: 'fatal_error' })[0], 'unknown');
  assert.equal(manifestAccess({ ok: true })[0], 'readable');
});

test('holding only the access token is a one-day credential', () => {
  const [state, detail] = storedPair({ access: true, refresh: false });
  assert.equal(state, 'access-only');
  assert.match(detail, /one-day credential/);
});

test('holding only the refresh token is the right shape', () => {
  const [state, detail] = storedPair({ access: false, refresh: true });
  assert.equal(state, 'refresh-only');
  assert.match(detail, /right shape/);
});

test('holding both is conditional on writing both back', () => {
  const [state, detail] = storedPair({ access: true, refresh: true });
  assert.equal(state, 'both-stored');
  assert.match(detail, /writing only one/);
});

test('holding neither is reported before any call is made', () => {
  assert.equal(storedPair({})[0], 'no-credential');
});
''',
"faq": [
 ("How is this different from the twelve-hour token rotation on my bot token?",
  "Different credential, different endpoint, different holder. A rotating workspace token belongs to the running app and refreshes through oauth.v2.access; a configuration token belongs to whoever manages the app and refreshes through tooling.tokens.rotate. The lifetimes happen to match, which is precisely why the two get confused and why someone ends up debugging the app's refresh loop for a failure the app was never part of."),
 ("Can I make the configuration token last longer?",
  "No. Twelve hours is fixed and there is no long-lived variant, which is deliberate: the token can rewrite your app's configuration, so it is meant to be minted per session rather than parked in a secret store. Build the rotate step instead of looking for a setting."),
 ("What exactly does tooling.tokens.rotate give back?",
  "A new access token and a new refresh token. The refresh token you sent is spent, so the next run needs the one that came back. This is the detail that breaks pipelines: a job that writes only the access token to the secret store works one more time and then fails with an error indistinguishable from ordinary expiry."),
 ("Why should the audit care that the manifest was unreadable?",
  "Because the alternative is a report that says nothing is wrong when in fact six checks never ran. Every finding that depends on the manifest, such as whether Socket Mode is enabled or whether token rotation was switched on, is unknown rather than clean, and a summary that does not distinguish those two states destroys the value of a clean run."),
 ("Do I need a write-scoped configuration token for an audit?",
  "No, and you should not have one. Issue the audit a token with app_configurations:read only, and keep app_configurations:write to the pipeline that actually deploys manifests. They rotate independently, so a leak of the read credential cannot rewrite the app, and the split costs nothing beyond one extra secret."),
],
"related": [
 ("/slack/token-expired-rotation/", "the app's own twelve-hour clock"),
 ("/slack/refresh-token-reused/", "when a refresh token is spent twice"),
 ("/slack/app-level-token-missing-connections-write/", "reading the manifest to explain a socket"),
],
"citations": [CITE_MANIFEST_EXPORT, CITE_TOKENS_ROTATE, CITE_TOKENS, CITE_ROTATION],
},

]
