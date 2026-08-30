#!/usr/bin/env python3
"""/slack/ field notes, batch E — the writing.

Four notes that all live near the word "token" and deliberately do not share a
detection. One reads timestamps out of your own refresh ledger and never asks
Slack why. One reads the first eight characters of every credential in the
environment and reaches its finding before a packet leaves the machine. One
accepts that the credential is fine and asks which methods refuse its class,
reading an argument error as proof the class was right. And one starts from a
workspace where nothing is failing at all and has to prove a negative: that a
scope on the token has no call site behind it.

Read-only throughout. GET requests only, and for Slack that means Web API
methods that read: nothing here posts, invites, deletes or edits. Every script
reports what it found and prints the repair for a human to run.
"""

CITE_TOKENS = ("Token types — Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_ROTATION = ("Using token rotation — Slack Docs",
                 "https://docs.slack.dev/authentication/using-token-rotation")
CITE_OAUTH_ACCESS = ("oauth.v2.access method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/oauth.v2.access")
CITE_OAUTH_EXCHANGE = ("oauth.v2.exchange method reference — Slack Docs",
                       "https://docs.slack.dev/reference/methods/oauth.v2.exchange")
CITE_INSTALL = ("Installing with OAuth — Slack Docs",
                "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_SOCKET = ("Socket Mode — Slack Docs",
               "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_CONNECTIONS_OPEN = ("apps.connections.open method reference — Slack Docs",
                         "https://docs.slack.dev/reference/methods/apps.connections.open")
CITE_EVENT_AUTHZ = ("apps.event.authorizations.list method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/apps.event.authorizations.list")
CITE_ADMIN_TEAMS = ("admin.teams.list method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/admin.teams.list")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_SECURITY = ("Best practices for security — Slack Docs",
                 "https://docs.slack.dev/authentication/best-practices-for-security")
CITE_USERS_INFO = ("users.info method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")

GUIDES = [

{
"slug": "refresh-token-reused",
"title": "Slack refresh tokens are single use: a replay kills the pair",
"description": "Two replicas refreshing a rotating Slack token at once burn a single-use refresh token. The evidence is in your refresh ledger, not in the API.",
"h1": "Slack refresh tokens are single use: a replay kills the pair",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack invalid_refresh_token", "slack token rotation single use",
             "slack refresh token concurrency", "slack 2 active token limit",
             "xoxe refresh token revoked"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Rotation was working. Then one afternoon every call returns <code>token_expired</code>, the refresh call answers <code>invalid_refresh_token</code>, and the only recovery is to send a customer through the install flow again. Nothing was deployed. What changed is that the service went from one replica to two, and both of them woke up on the same cron minute.",
"short_answer": """<p>A Slack refresh token is <strong>single use</strong>. Redeeming it returns a <em>new</em> refresh token and begins retiring the old one, and Slack keeps at most <strong>two active tokens</strong> per installation. Two workers refreshing at the same moment, or one worker retrying after a request that actually succeeded but whose response was lost, both spend the same token twice.</p>
<p>The Web API cannot tell you this happened. All it will say is <code>token_expired</code>, which is what an un-refreshed token says too. The evidence lives in the refresh attempts <em>your own app</em> recorded: two attempts seconds apart from different workers, or more than two successful refreshes inside one twelve-hour window. The script below reads that ledger, calls <code>auth.test</code> once per installation to prove the app is still installed, and names the refresh that burned the pair.</p>""",
"problem": """<p>Token rotation is opt-in and cannot be switched back off. Once it is on, an installation carries two secrets rather than one: an access token prefixed <code>xoxe.xoxb-</code> that expires after exactly 43200 seconds, and a refresh token prefixed <code>xoxe-1-</code> that exists to mint the next pair. The app is expected to redeem the second before the first expires.</p>
<p>The trap is that redeeming is not idempotent. Each redemption issues a fresh pair and starts revoking the one it replaced, so the operation is only safe if exactly one actor performs it at a time. Nothing in the deployment enforces that. A refresh scheduled on a fixed cron runs on every replica. A refresh triggered lazily by "the token expires in under an hour" fires on whichever requests arrive first, which on a busy service is several at once. And an HTTP client that retries on timeout will happily redeem a token whose response was lost in transit rather than never sent.</p>
<p>What makes it hard to see is that the failure is <em>delayed and total</em>. The first replay usually succeeds; both workers get a valid pair and both write one, and whichever wrote last wins. The loser's pair is still live, because Slack allows two. The breakage arrives on the third redemption inside the window, when the two-token limit retires something still in use, or on the next cycle when the stored refresh token turns out to be the one that was superseded. By then the logs that would explain it have rolled.</p>""",
"why": """<p><strong>Single use is the whole mechanism.</strong> Rotation exists so that a leaked token has a short life. That guarantee is only worth anything if redeeming a refresh token invalidates it, so Slack does exactly that. A design that treats the refresh token as a long-lived credential to be reused is not slightly wrong; it is using the feature backwards.</p>
<p><strong>Two active tokens, not unlimited.</strong> Slack keeps a small number of tokens live per installation so that a redemption whose response was lost does not immediately lock you out. Refresh more than that inside one window and the oldest is retired &mdash; which, if the oldest is the one a still-running worker holds, looks exactly like a random logout.</p>
<p><strong>The store write has to be atomic with the read.</strong> Reading the refresh token, calling out, and writing the result back is a read-modify-write across a network call. Without a per-installation lock held for the whole sequence, two workers interleave and the later write can be the older pair.</p>
<p><strong>A retry is a second redemption.</strong> A gateway timeout does not mean the request failed; it means you do not know. Retrying it spends the token a second time. Refresh calls should not be inside a generic retrying HTTP client, or the client should retry only on a connection error that provably never reached Slack.</p>
<p><strong>Nothing distinguishes this from plain expiry at the API.</strong> <code>auth.test</code> answers <code>token_expired</code> either way. The only thing that separates "we never built the refresh loop" from "we built it and two copies of it fought" is the record of attempts, which is why this note's detection is a ledger read and not a probe.</p>""",
"steps": [
 {"h": "Write down the refresh attempts, if you are not already",
  "body": """<p>The script consumes a JSON array of what your app recorded: for each attempt, the installation it was for, an ISO-8601 timestamp, the worker or pod that made it, and whether it came back <code>ok</code>, timed out, or errored. If you have never logged this, that is the first repair &mdash; four fields at the point of redemption, and the next incident explains itself.</p>"""},
 {"h": "Look for two attempts inside the lock window",
  "body": """<p>Two redemptions for one installation seconds apart from <em>different</em> workers is a concurrency bug and needs a lock. Two seconds apart from the <em>same</em> worker, where the first did not return cleanly, is a retry spending the token twice and needs the retry removed. They have the same symptom and opposite fixes, so the script keeps them apart.</p>"""},
 {"h": "Count successful refreshes per twelve-hour window",
  "body": """<p>A rotated access token lives 43200 seconds, so a healthy app refreshes once or twice per window. More than two successes inside one sliding window means older tokens are being retired by the active-token limit while something may still be holding them.</p>"""},
 {"h": "Ask the live token what state it is actually in",
  "body": """<p>One <code>auth.test</code> per installation, which needs no scopes. <code>token_revoked</code> means the app was uninstalled and the ledger is a red herring. <code>token_expired</code> alongside a ledger finding is the replay. <code>ok: true</code> alongside a ledger finding is the worst of the three: the bug is live and simply has not landed yet.</p>"""},
 {"h": "Serialise the refresh and write both halves together",
  "body": """<p>Take a per-installation lock &mdash; a row lock in the database that holds the installation is enough &mdash; re-read the stored pair inside it, skip the redemption if another worker already wrote something fresher, and persist the new access token and the new refresh token in one transaction. Schedule at roughly half the lifetime rather than at expiry.</p>"""},
 {"h": "Accept that a dead refresh token is dead",
  "body": """<p>There is no recovery call. If both halves of the pair are gone, the installation has to go back through OAuth. Say so in the report rather than scheduling retries against a credential that will never answer again.</p>"""},
],
"verify": """<p>After the lock is in place, re-run over a fresh ledger. Every installation should refresh once or twice per window, always from a worker that held the lock, and no two attempts should sit inside the lock window.</p>
<pre><code class="language-bash">python3 slack_refresh_ledger_audit.py --ledger refreshes.json
# 6 installation(s) checked, 0 with a refresh that can burn the pair</code></pre>""",
"code_intro": "One GET per installation, and it is the smaller half of the job &mdash; the finding is computed from timestamps before Slack is contacted at all. Two pure functions: <code>ledger_verdict</code> reads one installation's attempt history and names the shape of the misuse, and <code>install_state</code> combines that with the live <code>auth.test</code> answer, because a burned pair and an uninstalled app produce the same silence.",
"py_file": "slack_refresh_ledger_audit.py",
"py": '''"""Find the refresh that burned a Slack rotating token, and the worker that did it.

Read only. One GET per installation and nothing else; the finding itself is
computed from timestamps the app already wrote down. The repair is a lock and a
transaction, and it is printed for a human to implement.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_refresh_ledger_audit")

API = "https://slack.com/api/"

WINDOW_HOURS = 12    # a rotated access token lives 43200 seconds
ACTIVE_LIMIT = 2     # Slack keeps at most this many live tokens per installation
LOCK_SECONDS = 60    # two redemptions closer than this were not serialised

BURNED = ("concurrent-refresh", "retry-after-timeout", "over-active-limit")


def _at(value):
    """ISO-8601 to an aware datetime. Pure, and tolerant of a trailing Z."""
    text = str(value).replace("Z", "+00:00")
    stamp = datetime.fromisoformat(text)
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def ledger_verdict(events, window_hours=WINDOW_HOURS, lock_seconds=LOCK_SECONDS):
    """Classify one installation's recorded refresh attempts. Pure.

    `events` is what the app logged at the point of redemption:
    [{"at": "2026-08-30T09:00:00Z", "worker": "web-2", "outcome": "ok"}, ...]
    in any order. Returns (state, detail).
    """
    rows = sorted(({"at": _at(e.get("at")),
                    "worker": str(e.get("worker") or "?"),
                    "outcome": str(e.get("outcome") or "ok")} for e in events),
                  key=lambda r: r["at"])
    if not rows:
        return ("no-refresh-recorded",
                "no redemption was ever logged for this installation. Either "
                "rotation is off, or the refresh loop does not exist yet, which "
                "is a different problem from spending the token twice.")

    for older, newer in zip(rows, rows[1:]):
        gap = (newer["at"] - older["at"]).total_seconds()
        if gap > lock_seconds:
            continue
        if newer["worker"] != older["worker"]:
            return ("concurrent-refresh",
                    "%s and %s both redeemed within %.0fs at %s. The token is "
                    "single use, so one of those two pairs was already dying "
                    "when it was written."
                    % (older["worker"], newer["worker"], gap,
                       newer["at"].isoformat()))
        if older["outcome"] != "ok":
            return ("retry-after-timeout",
                    "%s redeemed, saw outcome=%s, and redeemed again %.0fs "
                    "later. A timeout is not a failure: the first call may have "
                    "spent the token and lost the answer."
                    % (older["worker"], older["outcome"], gap))

    ok_rows = [r for r in rows if r["outcome"] == "ok"]
    span = timedelta(hours=window_hours)
    for i, first in enumerate(ok_rows):
        inside = [r for r in ok_rows[i:] if r["at"] - first["at"] < span]
        if len(inside) > ACTIVE_LIMIT:
            return ("over-active-limit",
                    "%d successful redemptions in the %dh window starting %s. "
                    "Slack keeps %d tokens live, so the oldest were retired "
                    "while something may still have been holding them."
                    % (len(inside), window_hours, first["at"].isoformat(),
                       ACTIVE_LIMIT))

    return ("serialised",
            "%d redemption(s), none inside the %ds lock window and at most %d "
            "per %dh window" % (len(rows), lock_seconds, ACTIVE_LIMIT, window_hours))


def install_state(identity, ledger_state):
    """Combine the live auth.test answer with the ledger classification. Pure.

    The Web API cannot distinguish a replayed refresh token from one that was
    never refreshed, so neither half is conclusive alone.
    """
    burned = ledger_state in BURNED
    if identity.get("ok") is True:
        if burned:
            return ("at-risk",
                    "the token works right now and the ledger shows a redemption "
                    "that can spend the pair twice. This is the cheap moment to "
                    "fix it: after the next collision the only repair is OAuth.")
        return ("healthy", "auth.test answers ok and the refresh history is clean")

    error = identity.get("error") or "<no error field>"
    if error == "token_revoked":
        return ("uninstalled",
                "token_revoked. The app was removed from the workspace, which is "
                "not a rotation problem at all; tombstone the row instead.")
    if error in ("token_expired", "invalid_auth"):
        if burned:
            return ("refresh-token-burned",
                    "error=%s with a redemption that spent the pair twice. The "
                    "stored refresh token is the superseded one and will not be "
                    "redeemable. Only a fresh install recovers this." % error)
        return ("expired-not-refreshed",
                "error=%s and the ledger shows no misuse. This looks like a "
                "refresh that never ran rather than one that ran twice." % error)
    return ("inconclusive",
            "error=%s, which is neither expiry nor revocation. Resolve that "
            "before reading anything into the ledger." % error)


def auth_test(session, token):
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def load_ledger(path):
    """Group the recorded attempts by installation."""
    rows = json.loads(open(path, encoding="utf-8").read())
    grouped = {}
    for row in rows:
        grouped.setdefault(str(row.get("install") or "<unkeyed>"), []).append(row)
    return grouped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True,
                    help="JSON array of refresh attempts: install, at, worker, outcome")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token for the single-install case")
    ap.add_argument("--tokens",
                    help="JSON object mapping install id to the env var holding its token")
    args = ap.parse_args()

    grouped = load_ledger(args.ledger)
    token_envs = json.loads(open(args.tokens, encoding="utf-8").read()) if args.tokens else {}
    s = requests.Session()

    bad = 0
    for install, events in sorted(grouped.items()):
        state, detail = ledger_verdict(events)
        env_name = token_envs.get(install, args.token_env)
        token = os.environ.get(env_name)
        if not token:
            log.warning("%-24s %-14s ledger says %s; %s is unset so the live "
                        "state is unknown", "no-token", install, state, env_name)
            bad += 1
            continue

        combined, live_detail = install_state(auth_test(s, token), state)
        line = "%-24s %-14s %s" % (combined, install, live_detail)
        if combined == "healthy":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  ledger: %s -- %s", state, detail)
        if state in BURNED:
            log.warning("  repair: hold a per-installation lock across read, redeem "
                        "and write; persist both new values in one transaction")
            log.warning("  repair: do not retry a redemption on timeout, and do not "
                        "schedule one on a fixed cron across replicas")

    log.info("%d installation(s) checked, %d with a refresh that can burn the pair",
             len(grouped), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-refresh-ledger-audit.mjs",
"js": '''/**
 * Find the refresh that burned a Slack rotating token, and the worker that did it.
 *
 * Read only. One GET per installation and nothing else; the finding itself is
 * computed from timestamps the app already wrote down. The repair is a lock and
 * a transaction, and it is printed for a human to implement.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

const WINDOW_HOURS = 12;   // a rotated access token lives 43200 seconds
const ACTIVE_LIMIT = 2;    // Slack keeps at most this many live tokens per install
const LOCK_SECONDS = 60;   // two redemptions closer than this were not serialised

const BURNED = new Set(['concurrent-refresh', 'retry-after-timeout', 'over-active-limit']);

/**
 * Classify one installation's recorded refresh attempts. Pure.
 * `events` is [{ at, worker, outcome }, ...] in any order.
 */
export function ledgerVerdict(events, windowHours = WINDOW_HOURS, lockSeconds = LOCK_SECONDS) {
  const rows = events
    .map((e) => ({
      at: new Date(e.at),
      worker: String(e.worker ?? '?'),
      outcome: String(e.outcome ?? 'ok'),
    }))
    .sort((a, b) => a.at - b.at);

  if (rows.length === 0) {
    return ['no-refresh-recorded',
      'no redemption was ever logged for this installation. Either rotation is ' +
      'off, or the refresh loop does not exist yet, which is a different problem ' +
      'from spending the token twice.'];
  }

  for (let i = 1; i < rows.length; i += 1) {
    const older = rows[i - 1];
    const newer = rows[i];
    const gap = (newer.at - older.at) / 1000;
    if (gap > lockSeconds) continue;
    if (newer.worker !== older.worker) {
      return ['concurrent-refresh',
        `${older.worker} and ${newer.worker} both redeemed within ${gap.toFixed(0)}s ` +
        `at ${newer.at.toISOString()}. The token is single use, so one of those two ` +
        'pairs was already dying when it was written.'];
    }
    if (older.outcome !== 'ok') {
      return ['retry-after-timeout',
        `${older.worker} redeemed, saw outcome=${older.outcome}, and redeemed again ` +
        `${gap.toFixed(0)}s later. A timeout is not a failure: the first call may ` +
        'have spent the token and lost the answer.'];
    }
  }

  const okRows = rows.filter((r) => r.outcome === 'ok');
  const span = windowHours * 3600 * 1000;
  for (let i = 0; i < okRows.length; i += 1) {
    const inside = okRows.slice(i).filter((r) => r.at - okRows[i].at < span);
    if (inside.length > ACTIVE_LIMIT) {
      return ['over-active-limit',
        `${inside.length} successful redemptions in the ${windowHours}h window ` +
        `starting ${okRows[i].at.toISOString()}. Slack keeps ${ACTIVE_LIMIT} tokens ` +
        'live, so the oldest were retired while something may still have been ' +
        'holding them.'];
    }
  }

  return ['serialised',
    `${rows.length} redemption(s), none inside the ${lockSeconds}s lock window and ` +
    `at most ${ACTIVE_LIMIT} per ${windowHours}h window`];
}

/**
 * Combine the live auth.test answer with the ledger classification. Pure.
 * The Web API cannot distinguish a replayed refresh token from one that was
 * never refreshed, so neither half is conclusive alone.
 */
export function installState(identity, ledgerState) {
  const burned = BURNED.has(ledgerState);
  if (identity?.ok === true) {
    if (burned) {
      return ['at-risk',
        'the token works right now and the ledger shows a redemption that can ' +
        'spend the pair twice. This is the cheap moment to fix it: after the next ' +
        'collision the only repair is OAuth.'];
    }
    return ['healthy', 'auth.test answers ok and the refresh history is clean'];
  }

  const error = identity?.error ?? '<no error field>';
  if (error === 'token_revoked') {
    return ['uninstalled',
      'token_revoked. The app was removed from the workspace, which is not a ' +
      'rotation problem at all; tombstone the row instead.'];
  }
  if (error === 'token_expired' || error === 'invalid_auth') {
    if (burned) {
      return ['refresh-token-burned',
        `error=${error} with a redemption that spent the pair twice. The stored ` +
        'refresh token is the superseded one and will not be redeemable. Only a ' +
        'fresh install recovers this.'];
    }
    return ['expired-not-refreshed',
      `error=${error} and the ledger shows no misuse. This looks like a refresh ` +
      'that never ran rather than one that ran twice.'];
  }
  return ['inconclusive',
    `error=${error}, which is neither expiry nor revocation. Resolve that before ` +
    'reading anything into the ledger.'];
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

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const ledgerPath = arg(args, '--ledger');
  if (!ledgerPath) {
    console.error('usage: --ledger refreshes.json [--tokens tokens.json] ' +
                  '[--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const tokensPath = arg(args, '--tokens');
  const tokenEnvs = tokensPath ? JSON.parse(await readFile(tokensPath, 'utf8')) : {};

  const grouped = new Map();
  for (const row of JSON.parse(await readFile(ledgerPath, 'utf8'))) {
    const key = String(row.install ?? '<unkeyed>');
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(row);
  }

  let bad = 0;
  for (const [install, events] of [...grouped.entries()].sort()) {
    const [state, detail] = ledgerVerdict(events);
    const envName = tokenEnvs[install] ?? tokenEnv;
    const token = process.env[envName];
    if (!token) {
      console.warn(`${'no-token'.padEnd(24)} ${install.padEnd(14)} ledger says ` +
                   `${state}; ${envName} is unset so the live state is unknown`);
      bad += 1;
      continue;
    }

    const [combined, liveDetail] = installState(await authTest(token), state);
    const line = `${combined.padEnd(24)} ${install.padEnd(14)} ${liveDetail}`;
    if (combined === 'healthy') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    console.warn(`  ledger: ${state} -- ${detail}`);
    if (BURNED.has(state)) {
      console.warn('  repair: hold a per-installation lock across read, redeem and ' +
                   'write; persist both new values in one transaction');
      console.warn('  repair: do not retry a redemption on timeout, and do not ' +
                   'schedule one on a fixed cron across replicas');
    }
  }

  console.log(`${grouped.size} installation(s) checked, ${bad} with a refresh that ` +
              'can burn the pair');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing ledger.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The pair worth pinning is the two redemptions sixty seconds apart. From different workers it is a missing lock; from the same worker after a timeout it is a retry that spent the token twice. Identical timestamps, identical symptom at the API, opposite repairs &mdash; so the tests assert on which one the classifier picked, not merely that it complained.",
"test_py_file": "test_slack_refresh_ledger_audit.py",
"test_py": '''from slack_refresh_ledger_audit import install_state, ledger_verdict


def test_two_workers_inside_the_lock_window_is_a_concurrency_finding():
    state, detail = ledger_verdict([
        {"at": "2026-08-30T09:00:00Z", "worker": "web-1", "outcome": "ok"},
        {"at": "2026-08-30T09:00:12Z", "worker": "web-2", "outcome": "ok"},
    ])
    assert state == "concurrent-refresh"
    assert "web-1" in detail and "web-2" in detail


def test_same_worker_retrying_a_timeout_is_a_different_finding():
    state, detail = ledger_verdict([
        {"at": "2026-08-30T09:00:00Z", "worker": "web-1", "outcome": "timeout"},
        {"at": "2026-08-30T09:00:20Z", "worker": "web-1", "outcome": "ok"},
    ])
    assert state == "retry-after-timeout"
    assert "timeout is not a failure" in detail


def test_three_successes_in_one_window_exceed_the_active_token_limit():
    state, _ = ledger_verdict([
        {"at": "2026-08-30T00:00:00Z", "worker": "w", "outcome": "ok"},
        {"at": "2026-08-30T04:00:00Z", "worker": "w", "outcome": "ok"},
        {"at": "2026-08-30T08:00:00Z", "worker": "w", "outcome": "ok"},
    ])
    assert state == "over-active-limit"


def test_two_refreshes_a_window_apart_are_normal():
    state, _ = ledger_verdict([
        {"at": "2026-08-30T00:00:00Z", "worker": "w", "outcome": "ok"},
        {"at": "2026-08-30T06:00:00Z", "worker": "w", "outcome": "ok"},
        {"at": "2026-08-30T18:00:00Z", "worker": "w", "outcome": "ok"},
    ])
    assert state == "serialised"


def test_an_empty_ledger_is_not_reported_as_misuse():
    assert ledger_verdict([])[0] == "no-refresh-recorded"


def test_expired_token_plus_a_burned_ledger_names_the_replay():
    state, detail = install_state({"ok": False, "error": "token_expired"},
                                  "concurrent-refresh")
    assert state == "refresh-token-burned"
    assert "fresh install" in detail


def test_expired_token_with_a_clean_ledger_is_a_missing_loop_not_a_replay():
    state, _ = install_state({"ok": False, "error": "token_expired"}, "serialised")
    assert state == "expired-not-refreshed"


def test_uninstall_is_not_read_as_a_rotation_problem():
    state, _ = install_state({"ok": False, "error": "token_revoked"},
                             "concurrent-refresh")
    assert state == "uninstalled"


def test_a_working_token_with_a_burned_ledger_is_still_a_finding():
    state, detail = install_state({"ok": True, "team_id": "T1"}, "over-active-limit")
    assert state == "at-risk"
    assert "cheap moment" in detail


def test_a_working_token_with_a_clean_ledger_is_reported_as_healthy():
    assert install_state({"ok": True, "team_id": "T1"}, "serialised")[0] == "healthy"
''',
"test_js_file": "slack-refresh-ledger-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { installState, ledgerVerdict } from './slack-refresh-ledger-audit.mjs';

test('two workers inside the lock window is a concurrency finding', () => {
  const [state, detail] = ledgerVerdict([
    { at: '2026-08-30T09:00:00Z', worker: 'web-1', outcome: 'ok' },
    { at: '2026-08-30T09:00:12Z', worker: 'web-2', outcome: 'ok' },
  ]);
  assert.equal(state, 'concurrent-refresh');
  assert.match(detail, /web-1/);
  assert.match(detail, /web-2/);
});

test('same worker retrying a timeout is a different finding', () => {
  const [state, detail] = ledgerVerdict([
    { at: '2026-08-30T09:00:00Z', worker: 'web-1', outcome: 'timeout' },
    { at: '2026-08-30T09:00:20Z', worker: 'web-1', outcome: 'ok' },
  ]);
  assert.equal(state, 'retry-after-timeout');
  assert.match(detail, /timeout is not a failure/);
});

test('three successes in one window exceed the active token limit', () => {
  const [state] = ledgerVerdict([
    { at: '2026-08-30T00:00:00Z', worker: 'w', outcome: 'ok' },
    { at: '2026-08-30T04:00:00Z', worker: 'w', outcome: 'ok' },
    { at: '2026-08-30T08:00:00Z', worker: 'w', outcome: 'ok' },
  ]);
  assert.equal(state, 'over-active-limit');
});

test('two refreshes a window apart are normal', () => {
  const [state] = ledgerVerdict([
    { at: '2026-08-30T00:00:00Z', worker: 'w', outcome: 'ok' },
    { at: '2026-08-30T06:00:00Z', worker: 'w', outcome: 'ok' },
    { at: '2026-08-30T18:00:00Z', worker: 'w', outcome: 'ok' },
  ]);
  assert.equal(state, 'serialised');
});

test('an empty ledger is not reported as misuse', () => {
  assert.equal(ledgerVerdict([])[0], 'no-refresh-recorded');
});

test('expired token plus a burned ledger names the replay', () => {
  const [state, detail] = installState(
    { ok: false, error: 'token_expired' }, 'concurrent-refresh');
  assert.equal(state, 'refresh-token-burned');
  assert.match(detail, /fresh install/);
});

test('expired token with a clean ledger is a missing loop not a replay', () => {
  const [state] = installState({ ok: false, error: 'token_expired' }, 'serialised');
  assert.equal(state, 'expired-not-refreshed');
});

test('uninstall is not read as a rotation problem', () => {
  const [state] = installState({ ok: false, error: 'token_revoked' }, 'concurrent-refresh');
  assert.equal(state, 'uninstalled');
});

test('a working token with a burned ledger is still a finding', () => {
  const [state, detail] = installState({ ok: true, team_id: 'T1' }, 'over-active-limit');
  assert.equal(state, 'at-risk');
  assert.match(detail, /cheap moment/);
});

test('a working token with a clean ledger is reported as healthy', () => {
  assert.equal(installState({ ok: true, team_id: 'T1' }, 'serialised')[0], 'healthy');
});
''',
"faq": [
 ("Can I detect the replay from the Slack API alone?",
  "No, and that is the honest answer rather than a limitation of this script. auth.test returns token_expired for a token that was never refreshed and for one whose pair was spent twice, and there is no read method that reports how many times a refresh token has been redeemed. The distinguishing evidence is the record of your own redemption attempts, which is why the script asks for it."),
 ("Is a timeout on the refresh call safe to retry?",
  "Not blindly. A timeout means the answer was lost, not that the request never arrived, so the token may already have been spent. Retry only on an error that provably never reached Slack, such as a DNS failure or a refused connection, and on anything else re-read the store first to see whether a new pair was written."),
 ("Why does Slack allow two active tokens instead of one?",
  "So that a redemption whose response was lost does not lock the installation out immediately: the previous token stays usable for a short grace period. It is a safety margin for a single well-behaved refresher, not a budget for several. Three redemptions inside one window will retire something that is still in use."),
 ("Can I turn rotation off once I discover the refresh loop is broken?",
  "No. Rotation is a one-way switch on the app configuration, so the only path forward is to implement the refresh loop correctly. If an app adopted a copied manifest with rotation enabled and never noticed, that is worth knowing before the twelve hours are up rather than after."),
 ("What recovers an installation whose refresh token is already dead?",
  "Only a fresh OAuth install. There is no method that reissues a pair from a revoked refresh token, and retrying the dead one produces the same error indefinitely. Report it as needing re-authorisation and stop scheduling work against it, rather than burning rate limit on a credential that cannot come back."),
],
"related": [
 ("/slack/invalid-auth-wrong-token-type/", "the token in the slot is the wrong class"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
],
"citations": [CITE_ROTATION, CITE_OAUTH_ACCESS, CITE_OAUTH_EXCHANGE, CITE_AUTH_TEST],
},

{
"slug": "invalid-auth-wrong-token-type",
"title": "invalid_auth: the xapp- token is in the Web API slot",
"description": "Slack issues six token classes with different prefixes. A prefix check across your environment finds the swap before a single request is sent.",
"h1": "invalid_auth: the xapp- token is in the Web API slot",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack invalid_auth", "xapp token web api", "slack token prefix xoxb xoxp",
             "slack app level token socket mode", "xoxc token unsupported"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>{\"ok\": false, \"error\": \"invalid_auth\"}</code> on a call that plainly should work, with a token copied out of the app configuration ten minutes ago. The token is not expired, not revoked, and not missing a scope. It starts with <code>xapp-</code>, and the Web API has never accepted one of those.",
"short_answer": """<p>Slack issues at least six classes of credential and tells them apart by prefix: <code>xoxb-</code> bot, <code>xoxp-</code> user, <code>xapp-</code> app-level, <code>xoxe.</code> rotating, <code>xoxe-</code> refresh, <code>xwfp-</code> workflow, plus <code>xoxc-</code> browser session tokens that are not a supported credential at all. Each is accepted by a different surface, and using one on the wrong surface produces <code>invalid_auth</code> rather than anything that names the mistake.</p>
<p>So check the prefix, not the call. The script below reads every Slack credential in the environment, decides what class each one is, and compares that against what the variable it lives in is <em>for</em>. That finding needs no network at all. It then calls <code>auth.test</code> on the credentials that should be Web API tokens, which separates "wrong class" from "right class, mangled value" &mdash; a trailing newline from <code>$(cat secret)</code> gives the identical error.</p>""",
"problem": """<p>The app configuration page shows several tokens. Basic Information has App-Level Tokens; OAuth &amp; Permissions has the Bot User OAuth Token and, if user scopes were requested, a user token. They are all long opaque strings that begin with <code>xox</code>-something, they all look like the thing you were told to copy, and the pages do not sit next to each other. Copying the wrong one is not carelessness; it is the default outcome of a page layout.</p>
<p>What turns a thirty-second mistake into an afternoon is the error. <code>invalid_auth</code> is what Slack says for a revoked token, a truncated token, a token from a different workspace, and a token of a class this endpoint has never accepted. All four send you looking in different places, and the message distinguishes none of them. Developers reasonably assume the credential is stale, reinstall the app, get a new token, put it in the same wrong variable, and get the same error.</p>
<p>The related trap is the browser session token. Search results and older tooling suggest lifting an <code>xoxc-</code> value out of the Slack web client's local storage, and it works &mdash; for a while, from the right IP, alongside a <code>d</code> cookie. It is not a supported credential, it dies without notice, and it authenticates as a human being with all of that human's access.</p>""",
"why": """<p><strong>The prefix is the class, and it is public.</strong> There is no ambiguity to resolve: <code>xoxb-</code> is a bot token, <code>xapp-</code> is an app-level token, <code>xoxe-</code> is a refresh token and not an access token. A check that reads the first eight characters catches the whole family of swaps without a request, which means it can run at process startup rather than at 3am.</p>
<p><strong>App-level tokens serve a different API surface.</strong> An <code>xapp-</code> token opens a Socket Mode connection and reads app event authorizations. It is not a workspace credential, holds no workspace scopes, and cannot call <code>chat.postMessage</code> or <code>conversations.list</code> no matter what it is granted. It is not a weaker bot token; it is a different thing.</p>
<p><strong>A refresh token is not an access token.</strong> With rotation on, the install flow hands back two secrets and only one of them is a bearer credential. Storing <code>xoxe-1-...</code> in the variable the Web API client reads produces <code>invalid_auth</code> forever, and it looks like a rotation bug because rotation is the reason there are two strings.</p>
<p><strong>Whitespace produces the same error as the wrong token.</strong> A secret read with <code>$(cat /run/secrets/slack)</code> keeps its trailing newline, a value pasted into a YAML file keeps its quotes, and Slack rejects both as <code>invalid_auth</code>. Checking the prefix without checking hygiene finds three of the four cases and leaves the most annoying one.</p>
<p><strong>Name the variable for the role.</strong> <code>SLACK_TOKEN</code> is the root cause of this note. Two variables named <code>SLACK_BOT_TOKEN</code> and <code>SLACK_APP_TOKEN</code>, validated by prefix at startup, make the swap impossible to deploy rather than merely possible to find.</p>""",
"steps": [
 {"h": "List the slots, not the tokens",
  "body": """<p>Write down the environment variables the app reads and what each is <em>for</em>: a Web API credential, a Socket Mode credential, a manifest credential. The audit is a comparison between the role of the slot and the class of the value in it, so the roles have to be stated before anything can be checked.</p>"""},
 {"h": "Classify each value by prefix",
  "body": """<p>Longest prefix first, because <code>xoxe.xoxb-</code> and <code>xoxe-</code> both begin the same way and mean different things &mdash; the first is a rotating bot access token, the second is the refresh token that mints it. Getting that order wrong reports a healthy rotating app as broken.</p>"""},
 {"h": "Check hygiene before class",
  "body": """<p>A value with leading or trailing whitespace, or wrapped in quotes that were meant to be shell syntax, will fail with the same <code>invalid_auth</code> as a wrong class. Report it first and separately, because the repair is a deployment fix rather than a credential fix.</p>"""},
 {"h": "Confirm the Web API slots with auth.test",
  "body": """<p>For the values whose class fits their slot, one <code>auth.test</code> each. It needs no scopes, and it separates the two remaining cases: a right-class credential that authenticates, and a right-class credential that does not &mdash; which is a revoked, rotated or copied-from-another-workspace token, not a swap.</p>"""},
 {"h": "Do not call auth.test with the app-level token expecting an identity",
  "body": """<p>It will fail, and that failure is not evidence of anything wrong. An <code>xapp-</code> token has no workspace identity to report. The script says so explicitly rather than counting it as a finding, because an audit that flags a correctly configured Socket Mode credential will be turned off within a week.</p>"""},
 {"h": "Validate the prefix at startup and keep the names honest",
  "body": """<p>Assert the prefix of each credential when the process boots and exit loudly if it does not match. Take the bot token from OAuth &amp; Permissions and the app-level token from Basic Information, and never collapse them into one variable because "the app only needs one token today".</p>"""},
],
"verify": """<p>Re-run after fixing the slots. Every configured credential should report as fitting its role, and the Web API ones should authenticate.</p>
<pre><code class="language-bash">python3 slack_token_class_check.py
# fits         SLACK_BOT_TOKEN   bot token in a Web API slot, authenticates as B0123
# fits         SLACK_APP_TOKEN   app-level token in the Socket Mode slot
# 2 slot(s) checked, 0 holding the wrong class of credential</code></pre>""",
"code_intro": "The interesting half of this script does no I/O. <code>classify</code> maps a prefix to a token class and <code>slot_verdict</code> decides whether that class belongs in the slot it was found in &mdash; both pure, both able to answer before a request is sent. The single GET is <code>auth.test</code>, and it exists only to separate a wrong class from a right class with a mangled value.",
"py_file": "slack_token_class_check.py",
"py": '''"""Check that every Slack credential in the environment is in the right slot.

Read only, and mostly offline: the class of a token is in its prefix, so the
finding is available before any request. One auth.test per Web API credential
confirms it. Nothing is written, and no secret value is ever printed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_token_class_check")

API = "https://slack.com/api/"

# Longest first: xoxe.xoxb- is a rotating access token and xoxe- is the refresh
# token that mints one. Matching the short prefix first calls a healthy rotating
# app broken.
PREFIXES = (
    ("xoxe.xoxb-", "rotating-bot",
     "a rotating bot token; a Web API credential with a 12 hour life"),
    ("xoxe.xoxp-", "rotating-user",
     "a rotating user token, or an app configuration token; the prefix is shared"),
    ("xoxe-", "refresh",
     "a refresh token. It is redeemed for an access token and is not one"),
    ("xoxb-", "bot", "a bot token; the Web API credential for an app acting as itself"),
    ("xoxp-", "user", "a user token; the Web API credential for an app acting as a person"),
    ("xapp-", "app-level",
     "an app-level token; Socket Mode and app event methods, no workspace identity"),
    ("xoxc-", "browser-session",
     "a session token from the Slack web client. Not a supported credential"),
    ("xwfp-", "workflow", "a workflow token, minted per step and alive for 15 minutes"),
    ("xoxa-", "legacy-workspace", "a legacy workspace token, long retired"),
)

WEB_API_CLASSES = {"bot", "user", "rotating-bot", "rotating-user"}

# What each role will accept. A slot is a promise about what belongs in it.
ROLE_ACCEPTS = {
    "web-api": WEB_API_CLASSES,
    "socket-mode": {"app-level"},
    "manifest": {"rotating-user"},
}

DEFAULT_SLOTS = (
    ("SLACK_BOT_TOKEN", "web-api"),
    ("SLACK_USER_TOKEN", "web-api"),
    ("SLACK_APP_TOKEN", "socket-mode"),
    ("SLACK_CONFIG_TOKEN", "manifest"),
)


def classify(token):
    """Prefix to token class. Pure, and never returns the token itself."""
    text = str(token or "")
    for prefix, name, note in PREFIXES:
        if text.startswith(prefix):
            return (name, note)
    if text.startswith("xox"):
        return ("unknown-slack", "an unrecognised xox prefix; Slack adds classes over time")
    return ("not-a-slack-token", "no Slack token prefix at all")


def slot_verdict(name, role, raw):
    """Does the value in this environment variable belong in this slot? Pure.

    `raw` is the value exactly as the environment holds it, whitespace included,
    because whitespace is one of the findings. Returns (state, detail).
    """
    if raw is None:
        return ("unset", "not set. If the app needs a %s credential it will fail "
                         "at first use." % role)
    if raw == "":
        return ("empty", "set to the empty string, which is worse than unset: the "
                         "usual `if not token` guard never fires.")
    if raw != raw.strip():
        return ("whitespace-in-value",
                "the value has leading or trailing whitespace. A secret read with "
                "$(cat ...) keeps its newline and Slack answers invalid_auth, "
                "which reads exactly like the wrong token.")
    if raw[0] in "'\\"" or raw[-1] in "'\\"":
        return ("quoted-value",
                "the value is wrapped in quote characters. Those are shell or YAML "
                "syntax that was stored literally, and Slack sees a token that "
                "starts with a quote.")

    cls, note = classify(raw)
    accepts = ROLE_ACCEPTS.get(role, set())
    if cls in accepts:
        return ("fits", "%s in a %s slot: %s" % (cls, role, note))

    if cls == "browser-session":
        return ("browser-session-token",
                "%s holds %s. It authenticates as the human whose browser it came "
                "from, expires without warning, and is not supported." % (name, note))
    if cls == "refresh":
        return ("refresh-token-in-access-slot",
                "%s holds %s. Rotation hands back two strings and only the other "
                "one is a bearer credential." % (name, note))
    if cls == "app-level" and role == "web-api":
        return ("app-level-in-web-slot",
                "%s is a Web API slot and holds an app-level token. The Web API "
                "has never accepted one; every call will answer invalid_auth." % name)
    if cls in WEB_API_CLASSES and role == "socket-mode":
        return ("web-token-in-socket-slot",
                "%s is the Socket Mode slot and holds %s. Socket Mode needs an "
                "app-level token from Basic Information." % (name, note))
    if cls == "not-a-slack-token":
        return ("not-a-slack-token",
                "%s does not look like a Slack credential at all. Check what the "
                "deployment actually injected here." % name)
    return ("wrong-class",
            "%s expects a %s credential and holds %s" % (name, role, note))


def auth_test(session, token):
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slot", action="append", default=[], metavar="NAME=ROLE",
                    help="check this variable as well, e.g. SLACK_TOKEN=web-api; repeatable")
    args = ap.parse_args()

    slots = list(DEFAULT_SLOTS)
    for spec in args.slot:
        name, _, role = spec.partition("=")
        slots.append((name, role or "web-api"))

    s = requests.Session()
    bad = 0
    for name, role in slots:
        raw = os.environ.get(name)
        state, detail = slot_verdict(name, role, raw)

        if state == "unset":
            log.info("%-28s %-20s %s", state, name, detail)
            continue
        if state != "fits":
            bad += 1
            log.warning("%-28s %-20s %s", state, name, detail)
            log.warning("  repair: bot token from OAuth & Permissions, app-level "
                        "token from Basic Information, one variable each")
            continue

        cls, _ = classify(raw)
        if cls not in WEB_API_CLASSES:
            # An app-level token has no workspace identity to report, so calling
            # auth.test with it proves nothing and flagging it would be noise.
            log.info("%-28s %-20s %s", state, name, detail)
            continue

        body = auth_test(s, raw)
        if body.get("ok") is True:
            log.info("%-28s %-20s %s, authenticates as %s in %s", state, name, detail,
                     body.get("bot_id") or body.get("user_id"), body.get("team_id"))
            continue
        bad += 1
        log.warning("%-28s %-20s the class is right and the value is not: error=%s",
                    "class-right-value-wrong", name, body.get("error") or "?")
        log.warning("  repair: this is a revoked, rotated or foreign-workspace "
                    "token, not a swapped one. Reissue it rather than moving it")

    log.info("%d slot(s) checked, %d holding the wrong class of credential",
             len(slots), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-token-class-check.mjs",
"js": '''/**
 * Check that every Slack credential in the environment is in the right slot.
 *
 * Read only, and mostly offline: the class of a token is in its prefix, so the
 * finding is available before any request. One auth.test per Web API credential
 * confirms it. Nothing is written, and no secret value is ever printed.
 */
const API = 'https://slack.com/api/';

// Longest first: xoxe.xoxb- is a rotating access token and xoxe- is the refresh
// token that mints one. Matching the short prefix first calls a healthy rotating
// app broken.
const PREFIXES = [
  ['xoxe.xoxb-', 'rotating-bot',
    'a rotating bot token; a Web API credential with a 12 hour life'],
  ['xoxe.xoxp-', 'rotating-user',
    'a rotating user token, or an app configuration token; the prefix is shared'],
  ['xoxe-', 'refresh',
    'a refresh token. It is redeemed for an access token and is not one'],
  ['xoxb-', 'bot', 'a bot token; the Web API credential for an app acting as itself'],
  ['xoxp-', 'user', 'a user token; the Web API credential for an app acting as a person'],
  ['xapp-', 'app-level',
    'an app-level token; Socket Mode and app event methods, no workspace identity'],
  ['xoxc-', 'browser-session',
    'a session token from the Slack web client. Not a supported credential'],
  ['xwfp-', 'workflow', 'a workflow token, minted per step and alive for 15 minutes'],
  ['xoxa-', 'legacy-workspace', 'a legacy workspace token, long retired'],
];

const WEB_API_CLASSES = new Set(['bot', 'user', 'rotating-bot', 'rotating-user']);

// What each role will accept. A slot is a promise about what belongs in it.
const ROLE_ACCEPTS = {
  'web-api': WEB_API_CLASSES,
  'socket-mode': new Set(['app-level']),
  manifest: new Set(['rotating-user']),
};

const DEFAULT_SLOTS = [
  ['SLACK_BOT_TOKEN', 'web-api'],
  ['SLACK_USER_TOKEN', 'web-api'],
  ['SLACK_APP_TOKEN', 'socket-mode'],
  ['SLACK_CONFIG_TOKEN', 'manifest'],
];

/** Prefix to token class. Pure, and never returns the token itself. */
export function classify(token) {
  const text = String(token ?? '');
  for (const [prefix, name, note] of PREFIXES) {
    if (text.startsWith(prefix)) return [name, note];
  }
  if (text.startsWith('xox')) {
    return ['unknown-slack', 'an unrecognised xox prefix; Slack adds classes over time'];
  }
  return ['not-a-slack-token', 'no Slack token prefix at all'];
}

/**
 * Does the value in this environment variable belong in this slot? Pure.
 * `raw` is the value exactly as the environment holds it, whitespace included,
 * because whitespace is one of the findings.
 */
export function slotVerdict(name, role, raw) {
  if (raw === undefined || raw === null) {
    return ['unset',
      `not set. If the app needs a ${role} credential it will fail at first use.`];
  }
  if (raw === '') {
    return ['empty',
      'set to the empty string, which is worse than unset: the usual falsy guard ' +
      'never fires.'];
  }
  if (raw !== raw.trim()) {
    return ['whitespace-in-value',
      'the value has leading or trailing whitespace. A secret read with $(cat ...) ' +
      'keeps its newline and Slack answers invalid_auth, which reads exactly like ' +
      'the wrong token.'];
  }
  if ('\\'"'.includes(raw[0]) || '\\'"'.includes(raw[raw.length - 1])) {
    return ['quoted-value',
      'the value is wrapped in quote characters. Those are shell or YAML syntax ' +
      'that was stored literally, and Slack sees a token that starts with a quote.'];
  }

  const [cls, note] = classify(raw);
  const accepts = ROLE_ACCEPTS[role] ?? new Set();
  if (accepts.has(cls)) return ['fits', `${cls} in a ${role} slot: ${note}`];

  if (cls === 'browser-session') {
    return ['browser-session-token',
      `${name} holds ${note}. It authenticates as the human whose browser it came ` +
      'from, expires without warning, and is not supported.'];
  }
  if (cls === 'refresh') {
    return ['refresh-token-in-access-slot',
      `${name} holds ${note}. Rotation hands back two strings and only the other ` +
      'one is a bearer credential.'];
  }
  if (cls === 'app-level' && role === 'web-api') {
    return ['app-level-in-web-slot',
      `${name} is a Web API slot and holds an app-level token. The Web API has ` +
      'never accepted one; every call will answer invalid_auth.'];
  }
  if (WEB_API_CLASSES.has(cls) && role === 'socket-mode') {
    return ['web-token-in-socket-slot',
      `${name} is the Socket Mode slot and holds ${note}. Socket Mode needs an ` +
      'app-level token from Basic Information.'];
  }
  if (cls === 'not-a-slack-token') {
    return ['not-a-slack-token',
      `${name} does not look like a Slack credential at all. Check what the ` +
      'deployment actually injected here.'];
  }
  return ['wrong-class', `${name} expects a ${role} credential and holds ${note}`];
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

async function main() {
  const slots = [...DEFAULT_SLOTS];
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] !== '--slot') continue;
    const [name, role] = String(args[i + 1] ?? '').split('=');
    if (name) slots.push([name, role || 'web-api']);
  }

  let bad = 0;
  for (const [name, role] of slots) {
    const raw = process.env[name];
    const [state, detail] = slotVerdict(name, role, raw);

    if (state === 'unset') {
      console.log(`${state.padEnd(28)} ${name.padEnd(20)} ${detail}`);
      continue;
    }
    if (state !== 'fits') {
      bad += 1;
      console.warn(`${state.padEnd(28)} ${name.padEnd(20)} ${detail}`);
      console.warn('  repair: bot token from OAuth & Permissions, app-level token ' +
                   'from Basic Information, one variable each');
      continue;
    }

    const [cls] = classify(raw);
    if (!WEB_API_CLASSES.has(cls)) {
      // An app-level token has no workspace identity to report, so calling
      // auth.test with it proves nothing and flagging it would be noise.
      console.log(`${state.padEnd(28)} ${name.padEnd(20)} ${detail}`);
      continue;
    }

    const body = await authTest(raw);
    if (body?.ok === true) {
      console.log(`${state.padEnd(28)} ${name.padEnd(20)} ${detail}, authenticates ` +
                  `as ${body.bot_id ?? body.user_id} in ${body.team_id}`);
      continue;
    }
    bad += 1;
    console.warn(`${'class-right-value-wrong'.padEnd(28)} ${name.padEnd(20)} the ` +
                 `class is right and the value is not: error=${body?.error ?? '?'}`);
    console.warn('  repair: this is a revoked, rotated or foreign-workspace token, ' +
                 'not a swapped one. Reissue it rather than moving it');
  }

  console.log(`${slots.length} slot(s) checked, ${bad} holding the wrong class of ` +
              'credential');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and start reading the environment.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things have to be pinned. The prefix table must be ordered so <code>xoxe.xoxb-</code> is matched before <code>xoxe-</code>, or every rotating app is reported as storing a refresh token in the access slot. And the correctly configured Socket Mode credential must come back clean, because an audit that flags a working <code>xapp-</code> token is an audit nobody runs twice.",
"test_py_file": "test_slack_token_class_check.py",
"test_py": '''from slack_token_class_check import classify, slot_verdict


def test_app_level_token_in_a_web_api_slot_is_the_headline_finding():
    state, detail = slot_verdict("SLACK_BOT_TOKEN", "web-api", "xapp-1-A01-99-abc")
    assert state == "app-level-in-web-slot"
    assert "invalid_auth" in detail


def test_app_level_token_in_its_own_slot_is_not_a_finding():
    state, _ = slot_verdict("SLACK_APP_TOKEN", "socket-mode", "xapp-1-A01-99-abc")
    assert state == "fits"


def test_bot_token_in_the_socket_slot_is_the_swap_the_other_way():
    state, _ = slot_verdict("SLACK_APP_TOKEN", "socket-mode", "xoxb-1-abc")
    assert state == "web-token-in-socket-slot"


def test_rotating_access_token_is_not_mistaken_for_a_refresh_token():
    assert classify("xoxe.xoxb-1-abc")[0] == "rotating-bot"
    assert slot_verdict("SLACK_BOT_TOKEN", "web-api", "xoxe.xoxb-1-abc")[0] == "fits"


def test_refresh_token_in_the_access_slot_is_named_as_such():
    state, detail = slot_verdict("SLACK_BOT_TOKEN", "web-api", "xoxe-1-abc")
    assert state == "refresh-token-in-access-slot"
    assert "bearer credential" in detail


def test_browser_session_token_is_reported_even_though_it_might_work():
    state, detail = slot_verdict("SLACK_BOT_TOKEN", "web-api", "xoxc-1-abc")
    assert state == "browser-session-token"
    assert "not supported" in detail


def test_trailing_newline_is_caught_before_the_class_check():
    state, _ = slot_verdict("SLACK_BOT_TOKEN", "web-api", "xoxb-1-abc\\n")
    assert state == "whitespace-in-value"


def test_a_quoted_value_is_its_own_finding():
    assert slot_verdict("SLACK_BOT_TOKEN", "web-api", '"xoxb-1-abc"')[0] == "quoted-value"


def test_empty_string_is_distinguished_from_unset():
    assert slot_verdict("SLACK_BOT_TOKEN", "web-api", None)[0] == "unset"
    assert slot_verdict("SLACK_BOT_TOKEN", "web-api", "")[0] == "empty"


def test_a_value_that_is_not_a_slack_token_at_all():
    assert classify("ghp_abc")[0] == "not-a-slack-token"
    assert slot_verdict("SLACK_BOT_TOKEN", "web-api", "ghp_abc")[0] == "not-a-slack-token"
''',
"test_js_file": "slack-token-class-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, slotVerdict } from './slack-token-class-check.mjs';

test('app level token in a web api slot is the headline finding', () => {
  const [state, detail] = slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'xapp-1-A01-99-abc');
  assert.equal(state, 'app-level-in-web-slot');
  assert.match(detail, /invalid_auth/);
});

test('app level token in its own slot is not a finding', () => {
  const [state] = slotVerdict('SLACK_APP_TOKEN', 'socket-mode', 'xapp-1-A01-99-abc');
  assert.equal(state, 'fits');
});

test('bot token in the socket slot is the swap the other way', () => {
  const [state] = slotVerdict('SLACK_APP_TOKEN', 'socket-mode', 'xoxb-1-abc');
  assert.equal(state, 'web-token-in-socket-slot');
});

test('rotating access token is not mistaken for a refresh token', () => {
  assert.equal(classify('xoxe.xoxb-1-abc')[0], 'rotating-bot');
  assert.equal(slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'xoxe.xoxb-1-abc')[0], 'fits');
});

test('refresh token in the access slot is named as such', () => {
  const [state, detail] = slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'xoxe-1-abc');
  assert.equal(state, 'refresh-token-in-access-slot');
  assert.match(detail, /bearer credential/);
});

test('browser session token is reported even though it might work', () => {
  const [state, detail] = slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'xoxc-1-abc');
  assert.equal(state, 'browser-session-token');
  assert.match(detail, /not supported/);
});

test('trailing newline is caught before the class check', () => {
  const [state] = slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'xoxb-1-abc\\n');
  assert.equal(state, 'whitespace-in-value');
});

test('a quoted value is its own finding', () => {
  const [state] = slotVerdict('SLACK_BOT_TOKEN', 'web-api', '"xoxb-1-abc"');
  assert.equal(state, 'quoted-value');
});

test('empty string is distinguished from unset', () => {
  assert.equal(slotVerdict('SLACK_BOT_TOKEN', 'web-api', undefined)[0], 'unset');
  assert.equal(slotVerdict('SLACK_BOT_TOKEN', 'web-api', '')[0], 'empty');
});

test('a value that is not a slack token at all', () => {
  assert.equal(classify('ghp_abc')[0], 'not-a-slack-token');
  assert.equal(slotVerdict('SLACK_BOT_TOKEN', 'web-api', 'ghp_abc')[0], 'not-a-slack-token');
});
''',
"faq": [
 ("Why does an app-level token not work on the Web API?",
  "Because it is not a workspace credential. An xapp- token is issued against the app itself and carries connections:write or authorizations:read, not channels:read or chat:write. It exists to open a Socket Mode connection and to read app event authorizations. There is no workspace identity behind it for auth.test to return, so the Web API rejects it rather than returning a diminished answer."),
 ("Is an xoxc- token from the browser ever acceptable?",
  "No. It is the session credential of a signed-in human, it is bound to a cookie, it expires without warning, and using it means your automation acts as that person with all of their access. Slack does not support it and there is no version of the workaround that becomes supported later. Register an app and take an xoxb- token instead."),
 ("The prefix is right and I still get invalid_auth. What now?",
  "Then the class is not the problem and the value is. In order of likelihood: the token was revoked by an uninstall, it belongs to a different workspace than the ids in your request, rotation replaced it and the stored copy is the old one, or the string was truncated or padded on its way into the environment. The script separates that case out as class-right-value-wrong for exactly this reason."),
 ("Can I just check the prefix at startup and skip the audit?",
  "That is the recommended end state, and it is the last step in this note. The audit is what you run once to find out which of your deployed environments already has the swap, and to catch the values that pass a prefix check but carry a newline. Once the startup assertion is in place the swap cannot be deployed again."),
 ("Why not name the variable SLACK_TOKEN and work out the class at runtime?",
  "Because the class determines what the credential can be used for, and deciding that at runtime means every call site has to handle both cases. Two variables named for their roles turn a runtime branch into a deployment fact, and make the startup assertion possible at all."),
],
"related": [
 ("/slack/not-allowed-token-type/", "the method refuses this class of token"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_TOKENS, CITE_AUTH_TEST, CITE_SOCKET, CITE_CONNECTIONS_OPEN],
},

{
"slug": "not-allowed-token-type",
"title": "not_allowed_token_type: right secret, wrong token class",
"description": "The token authenticates everywhere else and one method still refuses it. Probe each method and read an argument error as proof the class was accepted.",
"h1": "not_allowed_token_type: right secret, wrong token class",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack not_allowed_token_type", "slack admin methods user token",
             "apps.event.authorizations.list app level token",
             "slack admin.teams.list xoxb", "slack method token type"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>{\"ok\": false, \"error\": \"not_allowed_token_type\"}</code>. The token works. It authenticates, it has scopes, it calls a dozen other methods happily. This one method, and only this one, will not take it &mdash; and the error names the problem without naming the solution, because it says what is wrong with the class you brought and nothing about which class it wanted.",
"short_answer": """<p>Some Slack methods accept exactly one class of credential. <code>admin.*</code> wants a user token held by an org owner or admin and rejects a bot token outright. <code>apps.connections.open</code> and <code>apps.event.authorizations.list</code> want an app-level <code>xapp-</code> token, sent in the <code>Authorization</code> header rather than as a form field. Everything else wants <code>xoxb-</code> or <code>xoxp-</code>.</p>
<p>So the diagnosis is per method, not per token. Establish what class you hold with <code>auth.test</code> &mdash; a <code>bot_id</code> in the response means a bot token, its absence means a user token &mdash; then probe each method you depend on and read the error. <code>not_allowed_token_type</code> is the finding. <code>missing_scope</code> is emphatically <em>not</em>: it means the class was accepted and the grant was short. And an error about the <em>arguments</em> is the best news of all, because a method only gets as far as validating arguments once it has accepted the credential.</p>""",
"problem": """<p>This is the error that arrives after you have already fixed the obvious things. The token is not expired. It is not the wrong prefix &mdash; a bot token is a perfectly good Slack credential and it is in the variable it belongs in. Twelve methods accept it. The thirteenth does not, and the message is a bare statement that this class of token is not allowed here.</p>
<p>What it will not tell you is which class <em>is</em> allowed. That fact lives on the method's reference page, in a line most people scroll past, and it varies in ways that do not follow an obvious rule. <code>admin.teams.list</code> reads a list of workspaces and needs a human org admin's token, because Grid administration is modelled as something a person does. <code>apps.event.authorizations.list</code> reads which installations an event was delivered for, and needs the app's own token, because it is a fact about the app rather than about a workspace.</p>
<p>The second half of the trap is transport. The app-level methods want the token in the <code>Authorization</code> header. Send the same correct <code>xapp-</code> token as a form parameter, the way older Slack examples pass <code>token=</code>, and you get the identical <code>not_allowed_token_type</code> &mdash; with the right credential, in the right variable, for the right method. Nothing about the error hints that the problem is where you put it.</p>""",
"why": """<p><strong>Class is a property of the method, not of the app.</strong> One app routinely holds three credentials: a bot token for the Web API, an app-level token for Socket Mode, and possibly a user token for anything that must act as a person. Which one to send is decided per call site, and a client that has a single configured token cannot express that.</p>
<p><strong><code>admin.*</code> is a person's authority, not an app's.</strong> These methods reject bot tokens categorically. The user token has to belong to an org owner or admin on Enterprise Grid, and it needs the matching <code>admin.*:read</code> scope on top. A bot cannot be granted the authority because the authority is modelled as belonging to a human.</p>
<p><strong>An argument error means the class was accepted.</strong> If a method answers <code>invalid_arguments</code> or names a missing parameter, it has already checked and approved the credential. That is the cleanest possible confirmation that the class is right, and it is the one signal in this audit that is good news wearing an error's clothing.</p>
<p><strong><code>missing_scope</code> belongs to a different note.</strong> It means the class was fine and the grant was short, and the repair is a scope plus a reinstall rather than a different credential. An audit that lumps the two together sends people to the wrong configuration page, which is the specific failure this script exists to prevent.</p>
<p><strong>The header is part of the contract.</strong> For the app-level methods, <code>Authorization: Bearer xapp-...</code> is the supported placement. A token passed as a parameter is treated as the wrong class, so "it worked in curl once" and "it fails in the client" can both be true of the same secret.</p>""",
"steps": [
 {"h": "Establish the class you are holding",
  "body": """<p>One <code>auth.test</code>. A <code>bot_id</code> in the response means a bot token; its absence with a <code>user_id</code> means a user token. Do this first, because every subsequent verdict is a comparison against it and an unauthenticated token makes the whole probe meaningless.</p>"""},
 {"h": "Find out whether that user is an admin",
  "body": """<p>For a user token, <code>users.info?user=&lt;the user_id from auth.test&gt;</code> reports <code>is_admin</code> and <code>is_owner</code>. That is what separates a user token that will satisfy <code>admin.*</code> from one that will be refused for a reason no error message will spell out. It needs <code>users:read</code>, so treat it as optional enrichment.</p>"""},
 {"h": "Derive the class each method wants from its name",
  "body": """<p>The families are regular enough to encode: <code>admin.</code> wants an org admin's user token, <code>apps.connections.</code> and <code>apps.event.</code> want an app-level token, <code>apps.manifest.</code> wants an app configuration token, and everything else takes a bot or user token. Deriving it means the audit covers methods you have not thought about yet.</p>"""},
 {"h": "Probe with the credential the method should get",
  "body": """<p>Where the app holds several tokens, send each method the one its family calls for &mdash; the app-level token to the <code>apps.event.</code> probe, the user token to the <code>admin.</code> probes. A script that sends the bot token to everything reproduces the bug rather than diagnosing it.</p>"""},
 {"h": "Read the errors as statements about class",
  "body": """<p><code>not_allowed_token_type</code>: wrong class, and the table says which is right. <code>missing_scope</code>: right class, missing grant, different repair. <code>invalid_auth</code>: the credential itself is wrong and nothing about class can be concluded. An argument error: the class was accepted, which is the answer you wanted.</p>"""},
 {"h": "Route the credential at the call site, not in the client",
  "body": """<p>Keep a per-family mapping from method to credential and pass the right one explicitly. In the SDKs that means a second client instance rather than swapping a token on a shared one, and for the app-level methods it means the <code>Authorization</code> header rather than a form field.</p>"""},
],
"verify": """<p>Re-run once each method is being called with the credential its family requires. Every probe should report either <code>allowed</code> or <code>class-accepted</code>, and no probe should report a class mismatch.</p>
<pre><code class="language-bash">python3 slack_method_token_class.py
# holding    bot token B0123 in T0123
# allowed          team.info
# wrong-class      admin.teams.list      wants org-admin-user, holding bot
# 4 method(s) probed, 1 refusing this class of token</code></pre>""",
"code_intro": "Three pure functions carry the diagnosis and one GET per method feeds them. <code>required_class</code> derives what a method wants from its name, <code>token_class</code> reads <code>auth.test</code> and the optional profile to say what you hold, and <code>verdict</code> reads one probe's error &mdash; including the argument errors it deliberately treats as confirmation rather than failure.",
"py_file": "slack_method_token_class.py",
"py": '''"""Work out which Slack methods refuse the class of token this app deploys.

Read only. Every probe is a GET against a read method, and the arguments are
chosen so that a method which accepts the credential still cannot do anything
with the call. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_method_token_class")

API = "https://slack.com/api/"

# Method families and the class of credential each one accepts. Derived from the
# name rather than listed per method, so a method nobody thought about is still
# classified correctly.
FAMILIES = (
    ("admin.", "org-admin-user"),
    ("apps.connections.", "app-level"),
    ("apps.event.", "app-level"),
    ("apps.manifest.", "app-config"),
)

# Which environment variable holds the credential for each class.
ENV_FOR_CLASS = {
    "bot-or-user": "SLACK_BOT_TOKEN",
    "org-admin-user": "SLACK_USER_TOKEN",
    "app-level": "SLACK_APP_TOKEN",
    "app-config": "SLACK_CONFIG_TOKEN",
}

# The credential was accepted and the call was refused on its arguments. That is
# the confirmation this audit is looking for, not a failure.
ARGUMENT_ERRORS = {
    "invalid_arguments", "invalid_arg_name", "invalid_array_arg", "invalid_limit",
    "event_context_not_found", "channel_not_found", "user_not_found",
    "team_not_found", "not_found", "missing_argument",
}

CREDENTIAL_ERRORS = {
    "invalid_auth", "not_authed", "token_revoked", "token_expired", "account_inactive",
}

PROBES = (
    ("team.info", {}),
    ("conversations.list", {"limit": "1", "types": "public_channel"}),
    ("admin.teams.list", {"limit": "1"}),
    ("apps.event.authorizations.list", {"event_context": "audit-probe"}),
)


def required_class(method):
    """Which class of credential a method will accept, from its name. Pure."""
    for prefix, cls in FAMILIES:
        if method.startswith(prefix):
            return cls
    return "bot-or-user"


def token_class(identity, profile=None):
    """What class the credential in hand is. Pure.

    `identity` is a parsed auth.test body. `profile` is an optional users.info
    body, which is the only way to learn whether a user token belongs to an
    admin -- auth.test does not say.
    """
    if identity.get("ok") is not True:
        return ("unusable",
                "auth.test answered error=%s, so nothing can be concluded about "
                "class until the credential itself works."
                % (identity.get("error") or "<no error field>"))
    if identity.get("bot_id"):
        return ("bot", "bot token %s in %s"
                % (identity.get("bot_id"), identity.get("team_id")))
    user = (profile or {}).get("user") or {}
    if user.get("is_admin") or user.get("is_owner"):
        return ("org-admin-user", "user token for %s, who is an admin or owner"
                % identity.get("user_id"))
    if profile:
        return ("user", "user token for %s, who is neither admin nor owner. The "
                        "admin family will refuse it." % identity.get("user_id"))
    return ("user", "user token for %s; admin status unknown without users:read"
            % identity.get("user_id"))


def verdict(method, have, body):
    """Read one probe's answer as a statement about token class. Pure."""
    want = required_class(method)
    if body.get("ok") is True:
        return ("allowed", "answered ok with a %s credential" % have)

    error = body.get("error") or "<no error field>"
    if error == "not_allowed_token_type":
        return ("wrong-class",
                "wants %s, holding %s. Send this method the credential its family "
                "requires rather than the app's default token." % (want, have))
    if error == "missing_scope":
        return ("scope-not-class",
                "the %s class was accepted and the grant was short: needed=%s. "
                "That is a scope problem, not a token-class one."
                % (have, body.get("needed") or "?"))
    if error in CREDENTIAL_ERRORS:
        return ("credential",
                "error=%s. The credential itself is wrong or dead, so this probe "
                "says nothing about class." % error)
    if error in ARGUMENT_ERRORS:
        return ("class-accepted",
                "error=%s, which is a complaint about the arguments. A method only "
                "validates arguments after it has accepted the credential, so the "
                "%s class is right for it." % (error, have))
    return ("inconclusive",
            "error=%s, which is neither a class refusal nor an argument complaint. "
            "Read the method reference before concluding anything." % error)


def probe(session, method, params, token):
    r = session.get(API + method, params=params,
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def users_info(session, token, user_id):
    if not user_id:
        return None
    body = probe(session, "users.info", {"user": user_id}, token)
    return body if body.get("ok") is True else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", action="append", default=[],
                    help="probe this read method as well as the default set; repeatable")
    args = ap.parse_args()

    bot = os.environ.get("SLACK_BOT_TOKEN")
    if not bot:
        log.error("set SLACK_BOT_TOKEN (the token the app actually deploys with)")
        return 2

    s = requests.Session()
    identity = probe(s, "auth.test", {}, bot)
    profile = users_info(s, bot, identity.get("user_id")) if identity.get("ok") else None
    have, note = token_class(identity, profile)
    log.info("%-16s %s", "holding", note)
    if have == "unusable":
        return 2

    probes = list(PROBES) + [(m, {}) for m in args.method]
    bad = 0
    for method, params in probes:
        want = required_class(method)
        env_name = ENV_FOR_CLASS.get(want, "SLACK_BOT_TOKEN")
        token = os.environ.get(env_name)
        if not token:
            log.info("%-16s %-32s wants %s from %s, which is unset. Skipped rather "
                     "than probed with the wrong credential.",
                     "no-credential", method, want, env_name)
            continue

        # When a family has its own credential, report the class of that one.
        holding = have if env_name == "SLACK_BOT_TOKEN" else want
        state, detail = verdict(method, holding, probe(s, method, params, token))
        line = "%-16s %-32s %s" % (state, method, detail)
        if state in ("allowed", "class-accepted"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "wrong-class":
            log.warning("  repair: %s wants a %s credential; put it in %s and route "
                        "this call to it", method, want, env_name)
            if want == "app-level":
                log.warning("  repair: send it as an Authorization header, not as a "
                            "form field, or the class is rejected anyway")

    log.info("%d method(s) probed, %d refusing this class of token", len(probes), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-method-token-class.mjs",
"js": '''/**
 * Work out which Slack methods refuse the class of token this app deploys.
 *
 * Read only. Every probe is a GET against a read method, and the arguments are
 * chosen so that a method which accepts the credential still cannot do anything
 * with the call. The repair is printed, never performed.
 */
const API = 'https://slack.com/api/';

// Method families and the class of credential each one accepts. Derived from the
// name rather than listed per method, so a method nobody thought about is still
// classified correctly.
const FAMILIES = [
  ['admin.', 'org-admin-user'],
  ['apps.connections.', 'app-level'],
  ['apps.event.', 'app-level'],
  ['apps.manifest.', 'app-config'],
];

// Which environment variable holds the credential for each class.
const ENV_FOR_CLASS = {
  'bot-or-user': 'SLACK_BOT_TOKEN',
  'org-admin-user': 'SLACK_USER_TOKEN',
  'app-level': 'SLACK_APP_TOKEN',
  'app-config': 'SLACK_CONFIG_TOKEN',
};

// The credential was accepted and the call was refused on its arguments. That is
// the confirmation this audit is looking for, not a failure.
const ARGUMENT_ERRORS = new Set([
  'invalid_arguments', 'invalid_arg_name', 'invalid_array_arg', 'invalid_limit',
  'event_context_not_found', 'channel_not_found', 'user_not_found',
  'team_not_found', 'not_found', 'missing_argument',
]);

const CREDENTIAL_ERRORS = new Set([
  'invalid_auth', 'not_authed', 'token_revoked', 'token_expired', 'account_inactive',
]);

const PROBES = [
  ['team.info', {}],
  ['conversations.list', { limit: '1', types: 'public_channel' }],
  ['admin.teams.list', { limit: '1' }],
  ['apps.event.authorizations.list', { event_context: 'audit-probe' }],
];

/** Which class of credential a method will accept, from its name. Pure. */
export function requiredClass(method) {
  for (const [prefix, cls] of FAMILIES) {
    if (method.startsWith(prefix)) return cls;
  }
  return 'bot-or-user';
}

/**
 * What class the credential in hand is. Pure.
 * `profile` is an optional users.info body, the only way to learn whether a user
 * token belongs to an admin -- auth.test does not say.
 */
export function tokenClass(identity, profile = null) {
  if (identity?.ok !== true) {
    return ['unusable',
      `auth.test answered error=${identity?.error ?? '<no error field>'}, so ` +
      'nothing can be concluded about class until the credential itself works.'];
  }
  if (identity.bot_id) {
    return ['bot', `bot token ${identity.bot_id} in ${identity.team_id}`];
  }
  const user = profile?.user ?? {};
  if (user.is_admin || user.is_owner) {
    return ['org-admin-user',
      `user token for ${identity.user_id}, who is an admin or owner`];
  }
  if (profile) {
    return ['user',
      `user token for ${identity.user_id}, who is neither admin nor owner. The ` +
      'admin family will refuse it.'];
  }
  return ['user',
    `user token for ${identity.user_id}; admin status unknown without users:read`];
}

/** Read one probe's answer as a statement about token class. Pure. */
export function verdict(method, have, body) {
  const want = requiredClass(method);
  if (body?.ok === true) return ['allowed', `answered ok with a ${have} credential`];

  const error = body?.error ?? '<no error field>';
  if (error === 'not_allowed_token_type') {
    return ['wrong-class',
      `wants ${want}, holding ${have}. Send this method the credential its family ` +
      'requires rather than the app\\'s default token.'];
  }
  if (error === 'missing_scope') {
    return ['scope-not-class',
      `the ${have} class was accepted and the grant was short: needed=` +
      `${body.needed ?? '?'}. That is a scope problem, not a token-class one.`];
  }
  if (CREDENTIAL_ERRORS.has(error)) {
    return ['credential',
      `error=${error}. The credential itself is wrong or dead, so this probe says ` +
      'nothing about class.'];
  }
  if (ARGUMENT_ERRORS.has(error)) {
    return ['class-accepted',
      `error=${error}, which is a complaint about the arguments. A method only ` +
      `validates arguments after it has accepted the credential, so the ${have} ` +
      'class is right for it.'];
  }
  return ['inconclusive',
    `error=${error}, which is neither a class refusal nor an argument complaint. ` +
    'Read the method reference before concluding anything.'];
}

async function probe(method, params, token) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await res.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function usersInfo(token, userId) {
  if (!userId) return null;
  const body = await probe('users.info', { user: userId }, token);
  return body?.ok === true ? body : null;
}

async function main() {
  const bot = process.env.SLACK_BOT_TOKEN;
  if (!bot) {
    console.error('set SLACK_BOT_TOKEN (the token the app actually deploys with)');
    process.exitCode = 2;
    return;
  }

  const args = process.argv.slice(2);
  const extra = args.map((a, i) => (args[i - 1] === '--method' ? a : null)).filter(Boolean);

  const identity = await probe('auth.test', {}, bot);
  const profile = identity?.ok ? await usersInfo(bot, identity.user_id) : null;
  const [have, note] = tokenClass(identity, profile);
  console.log(`${'holding'.padEnd(16)} ${note}`);
  if (have === 'unusable') {
    process.exitCode = 2;
    return;
  }

  const probes = [...PROBES, ...extra.map((m) => [m, {}])];
  let bad = 0;
  for (const [method, params] of probes) {
    const want = requiredClass(method);
    const envName = ENV_FOR_CLASS[want] ?? 'SLACK_BOT_TOKEN';
    const token = process.env[envName];
    if (!token) {
      console.log(`${'no-credential'.padEnd(16)} ${method.padEnd(32)} wants ${want} ` +
                  `from ${envName}, which is unset. Skipped rather than probed with ` +
                  'the wrong credential.');
      continue;
    }

    // When a family has its own credential, report the class of that one.
    const holding = envName === 'SLACK_BOT_TOKEN' ? have : want;
    const [state, detail] = verdict(method, holding, await probe(method, params, token));
    const line = `${state.padEnd(16)} ${method.padEnd(32)} ${detail}`;
    if (state === 'allowed' || state === 'class-accepted') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (state === 'wrong-class') {
      console.warn(`  repair: ${method} wants a ${want} credential; put it in ` +
                   `${envName} and route this call to it`);
      if (want === 'app-level') {
        console.warn('  repair: send it as an Authorization header, not as a form ' +
                     'field, or the class is rejected anyway');
      }
    }
  }

  console.log(`${probes.length} method(s) probed, ${bad} refusing this class of token`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that carries this note is the argument error. <code>event_context_not_found</code> from <code>apps.event.authorizations.list</code> looks like a failure and is in fact the proof that the app-level token was accepted, so the tests pin it as <code>class-accepted</code> rather than as any flavour of problem. Alongside it, <code>missing_scope</code> has to stay firmly out of this note's territory.",
"test_py_file": "test_slack_method_token_class.py",
"test_py": '''from slack_method_token_class import required_class, token_class, verdict


def test_method_families_map_to_the_class_they_want():
    assert required_class("admin.teams.list") == "org-admin-user"
    assert required_class("apps.connections.open") == "app-level"
    assert required_class("apps.event.authorizations.list") == "app-level"
    assert required_class("apps.manifest.export") == "app-config"
    assert required_class("conversations.history") == "bot-or-user"


def test_bot_token_refused_by_an_admin_method_is_the_finding():
    state, detail = verdict("admin.teams.list", "bot",
                            {"ok": False, "error": "not_allowed_token_type"})
    assert state == "wrong-class"
    assert "org-admin-user" in detail


def test_an_argument_error_proves_the_class_was_accepted():
    state, detail = verdict("apps.event.authorizations.list", "app-level",
                            {"ok": False, "error": "event_context_not_found"})
    assert state == "class-accepted"
    assert "after it has accepted the credential" in detail


def test_missing_scope_is_explicitly_not_this_notes_finding():
    state, detail = verdict("conversations.history", "bot",
                            {"ok": False, "error": "missing_scope",
                             "needed": "channels:history"})
    assert state == "scope-not-class"
    assert "not a token-class one" in detail


def test_a_dead_credential_says_nothing_about_class():
    state, _ = verdict("team.info", "bot", {"ok": False, "error": "token_revoked"})
    assert state == "credential"


def test_success_is_reported_plainly():
    assert verdict("team.info", "bot", {"ok": True})[0] == "allowed"


def test_an_unfamiliar_error_is_not_guessed_at():
    assert verdict("team.info", "bot", {"ok": False, "error": "ratelimited"})[0] == "inconclusive"


def test_bot_id_in_auth_test_identifies_a_bot_token():
    state, detail = token_class({"ok": True, "bot_id": "B1", "team_id": "T1"})
    assert state == "bot"
    assert "B1" in detail


def test_a_user_token_needs_users_info_to_be_called_an_admin():
    plain = token_class({"ok": True, "user_id": "U1", "team_id": "T1"})
    assert plain[0] == "user"
    assert "admin status unknown" in plain[1]
    admin = token_class({"ok": True, "user_id": "U1", "team_id": "T1"},
                        {"user": {"is_owner": True}})
    assert admin[0] == "org-admin-user"


def test_a_non_admin_user_token_is_named_as_one_admin_will_refuse():
    state, detail = token_class({"ok": True, "user_id": "U1"},
                                {"user": {"is_admin": False, "is_owner": False}})
    assert state == "user"
    assert "will refuse it" in detail
''',
"test_js_file": "slack-method-token-class.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { requiredClass, tokenClass, verdict } from './slack-method-token-class.mjs';

test('method families map to the class they want', () => {
  assert.equal(requiredClass('admin.teams.list'), 'org-admin-user');
  assert.equal(requiredClass('apps.connections.open'), 'app-level');
  assert.equal(requiredClass('apps.event.authorizations.list'), 'app-level');
  assert.equal(requiredClass('apps.manifest.export'), 'app-config');
  assert.equal(requiredClass('conversations.history'), 'bot-or-user');
});

test('bot token refused by an admin method is the finding', () => {
  const [state, detail] = verdict('admin.teams.list', 'bot',
    { ok: false, error: 'not_allowed_token_type' });
  assert.equal(state, 'wrong-class');
  assert.match(detail, /org-admin-user/);
});

test('an argument error proves the class was accepted', () => {
  const [state, detail] = verdict('apps.event.authorizations.list', 'app-level',
    { ok: false, error: 'event_context_not_found' });
  assert.equal(state, 'class-accepted');
  assert.match(detail, /after it has accepted the credential/);
});

test('missing scope is explicitly not this notes finding', () => {
  const [state, detail] = verdict('conversations.history', 'bot',
    { ok: false, error: 'missing_scope', needed: 'channels:history' });
  assert.equal(state, 'scope-not-class');
  assert.match(detail, /not a token-class one/);
});

test('a dead credential says nothing about class', () => {
  const [state] = verdict('team.info', 'bot', { ok: false, error: 'token_revoked' });
  assert.equal(state, 'credential');
});

test('success is reported plainly', () => {
  assert.equal(verdict('team.info', 'bot', { ok: true })[0], 'allowed');
});

test('an unfamiliar error is not guessed at', () => {
  assert.equal(verdict('team.info', 'bot', { ok: false, error: 'ratelimited' })[0],
    'inconclusive');
});

test('bot_id in auth.test identifies a bot token', () => {
  const [state, detail] = tokenClass({ ok: true, bot_id: 'B1', team_id: 'T1' });
  assert.equal(state, 'bot');
  assert.match(detail, /B1/);
});

test('a user token needs users.info to be called an admin', () => {
  const plain = tokenClass({ ok: true, user_id: 'U1', team_id: 'T1' });
  assert.equal(plain[0], 'user');
  assert.match(plain[1], /admin status unknown/);
  const admin = tokenClass({ ok: true, user_id: 'U1', team_id: 'T1' },
    { user: { is_owner: true } });
  assert.equal(admin[0], 'org-admin-user');
});

test('a non admin user token is named as one admin will refuse', () => {
  const [state, detail] = tokenClass({ ok: true, user_id: 'U1' },
    { user: { is_admin: false, is_owner: false } });
  assert.equal(state, 'user');
  assert.match(detail, /will refuse it/);
});
''',
"faq": [
 ("How is this different from invalid_auth?",
  "invalid_auth means the credential itself was not accepted anywhere: wrong class for the whole API, revoked, mangled or foreign. not_allowed_token_type means the credential is genuinely valid and this particular method will not take that class. The first is a problem with the token, the second is a problem with the routing, and they are fixed on different screens."),
 ("Why can a bot token never call admin methods?",
  "Because Grid administration is modelled as authority a person holds. The admin.* family requires a user token belonging to an org owner or admin, with the matching admin.*:read scope on top of that. There is no bot scope that confers it, so the answer is never to add a scope to the bot; it is to use an admin's user token for those calls."),
 ("Is an argument error really good news?",
  "For this audit, yes. A method validates the credential before it validates arguments, so an error naming a missing or invalid parameter is proof the class was accepted. The script reports it as class-accepted rather than as a failure, because a probe deliberately called with useless arguments is meant to get exactly that answer."),
 ("Why does the app-level token have to go in the header?",
  "apps.connections.open and apps.event.authorizations.list accept the app-level token as Authorization: Bearer and reject it when it arrives as a form parameter, which surfaces as the same not_allowed_token_type. If a call fails with the right token in the right variable, check where in the request it is being placed before anything else."),
 ("Should I just hold every class of token so nothing is refused?",
  "No. Each credential you hold is a credential that can leak, and an org admin's user token is the most dangerous one in the set. Hold only the classes the app actually needs, route each call to the right one explicitly, and if a single admin.* call is the only thing forcing you to keep a user token, ask whether that call is worth the blast radius."),
],
"related": [
 ("/slack/invalid-auth-wrong-token-type/", "the token in the slot is the wrong class"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/over-broad-scopes/", "scopes the app has never called"),
],
"citations": [CITE_TOKENS, CITE_EVENT_AUTHZ, CITE_ADMIN_TEAMS, CITE_USERS_INFO],
},

{
"slug": "over-broad-scopes",
"title": "The token holds admin scopes the app has never called",
"description": "Nothing is failing, which is the problem. Compare X-OAuth-Scopes against the methods your code actually calls and prune what has no call site.",
"h1": "the token holds admin scopes the app has never called",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack over-scoped token", "x-oauth-scopes audit", "slack least privilege scopes",
             "remove slack scope reinstall", "chat:write.public risk"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The security review asks a reasonable question: why does the nightly digest bot hold <code>admin.users:write</code>, <code>files:write</code>, <code>chat:write.public</code> and <code>users:read.email</code>? Nobody knows. Nothing is broken, no error has ever been logged, and every scope on that list was added by somebody who needed it for ten minutes in 2023.",
"short_answer": """<p>This is the one note in the section where nothing is failing, so there is no error to read. The script has to prove a negative instead: that a scope on the token has no call site behind it.</p>
<p>It does that by comparing two lists. The first is the complete grant, which Slack returns in the <code>X-OAuth-Scopes</code> header on every Web API response &mdash; one <code>auth.test</code> and you have it. The second is the set of methods your code actually calls, which you produce by grepping the repository. Any granted scope that satisfies none of those methods is surplus, ranked by what it would cost if the token leaked: <code>admin.*</code> first, then anything with <code>:write</code>, then email and full message history.</p>
<p>Pruning is not free. Removing a scope, like adding one, only takes effect after a reinstall.</p>""",
"problem": """<p>Scopes accrete in one direction. A developer hits <code>missing_scope</code>, reads the <code>needed</code> list, adds every scope it names because the error is an OR list and that is not obvious, reinstalls, and moves on. A manifest gets copied from a more ambitious app. A feature is prototyped, abandoned, and its scopes stay. Nothing ever removes one, because removing one requires a reinstall and a reinstall is a change that could break something, and the scope is not breaking anything today.</p>
<p>The result is a bearer credential with far more authority than the code exercises. Slack tokens have no per-call attenuation: there is no way to make a particular request weaker than the token that carries it. So the blast radius of a leak &mdash; into a log line, a CI variable, an image layer, a laptop backup &mdash; is the full grant, not the part you use. With <code>channels:history</code> the finder can read the workspace's public archive. With <code>users:read.email</code> they can enumerate staff. With an <code>admin.*</code> scope on Grid they can act across the organisation.</p>
<p>What makes this hard to audit honestly is that absence of evidence really is the evidence here. Every other note in this section reads an error. This one reads a silence, and a silence can be produced by a scope that is genuinely unused or by a call site the audit could not see. The script is built to say which of those it is looking at rather than to assert the stronger claim.</p>""",
"why": """<p><strong><code>X-OAuth-Scopes</code> is the grant, and the config page is not.</strong> The header comes back on every response and describes the token in your hand. The scope list on the app configuration page describes what the <em>next</em> install will request. On an app that has not been reinstalled since the last edit, those two are different documents.</p>
<p><strong><code>needed</code> is an OR list, and that is where over-scoping starts.</strong> When Slack says a call needs <code>channels:history</code> or <code>groups:history</code> or <code>im:history</code>, any one of them will do. Adding all three, which is the natural reading of a comma-separated error field, triples the archive a leaked token opens.</p>
<p><strong><code>chat:write.public</code> is much larger than it sounds.</strong> It removes the requirement to be invited: the app can post into any public channel in the workspace. <code>chat:write</code> plus a deliberate invitation gives you a bot that can only speak where somebody asked it to.</p>
<p><strong>Removing a scope needs a reinstall too.</strong> The token is a snapshot of the grant at install time in both directions. Pruning the list and redeploying changes nothing until the app is installed again and the new token replaces the old one everywhere it is stored.</p>
<p><strong>Two apps beat one over-scoped app.</strong> If some job genuinely needs to read every message and another only posts a digest, those are two installs with two tokens and two rotation schedules. One token that can do both is one leak away from doing both for somebody else.</p>""",
"steps": [
 {"h": "Read the whole grant off one response",
  "body": """<p>One <code>auth.test</code>, and the answer is in the <code>X-OAuth-Scopes</code> response header rather than the body. That is the complete current scope list for the credential that is actually deployed, which is the only list worth auditing.</p>"""},
 {"h": "Produce the call inventory from the code, not from memory",
  "body": """<p>Grep the repository for Slack method names and keep the distinct ones. The script prints the command if you have not run it. This list is the entire basis for the conclusion, so an incomplete grep produces a confidently wrong report &mdash; which is why the next step exists.</p>"""},
 {"h": "Map each called method to the scopes that would satisfy it",
  "body": """<p>Per method the requirement is an OR list, so a granted scope is <em>justified</em> if it appears in the option set of any method the app calls. Methods the table does not recognise are counted separately and reported, because each one makes the justified set a lower bound.</p>"""},
 {"h": "Rank what is left by what it would cost",
  "body": """<p>Surplus is not uniform. An unused <code>admin.*</code> scope on a routine integration is a different finding from an unused <code>emoji:read</code>. The ranking is <code>admin.*</code>, then any <code>:write</code>, then email and profile access, then full history, then ordinary reads &mdash; and only the first four change the exit code.</p>"""},
 {"h": "Report the gaps as well, and send them elsewhere",
  "body": """<p>A method the app calls with none of its scopes granted is the opposite finding, and it belongs in the note about <code>missing_scope</code> rather than this one. Printing it here is still worth doing: it is a fast check that the inventory and the grant describe the same app.</p>"""},
 {"h": "Prune, reinstall, replace the token",
  "body": """<p>Cut the scope list in OAuth &amp; Permissions to what the inventory justifies, reinstall the app, and replace the stored token everywhere. For a distributed app, every workspace re-authorises on its own schedule, so plan the prune as a migration rather than a deploy.</p>"""},
],
"verify": """<p>After the prune and the reinstall, re-run against the new token. The granted list should be shorter, and nothing above the ordinary-read tier should remain unjustified.</p>
<pre><code class="language-bash">python3 slack_scope_surplus.py --calls calls.txt
# granted 7, justified 7, surplus 0, gaps 0
# 0 surplus scope(s) above the ordinary-read tier</code></pre>""",
"code_intro": "One GET, and the interesting value is a response header rather than the body. Two pure functions do the reasoning: <code>justify</code> splits the granted list against the methods the app calls and hands back the unrecognised methods separately, because those are what make the answer a lower bound; and <code>rank</code> orders whatever is left by how much it would cost if the token were found in a log.",
"py_file": "slack_scope_surplus.py",
"py": '''"""Find Slack scopes on the deployed token that no call site justifies.

Read only, and unusually, nothing here is failing: the script proves a negative
rather than reading an error. One GET, and the answer is in a response header.
The prune and the reinstall are printed for a human to run.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_scope_surplus")

API = "https://slack.com/api/"

# Per method, the scopes that would each satisfy it: an OR list, not an AND list.
# Deliberately incomplete -- Slack has hundreds of methods, and a method missing
# from this table is reported rather than assumed harmless.
SCOPES_FOR_METHOD = {
    "auth.test": (),
    "team.info": ("team:read",),
    "conversations.list": ("channels:read", "groups:read", "im:read", "mpim:read"),
    "conversations.info": ("channels:read", "groups:read", "im:read", "mpim:read"),
    "conversations.members": ("channels:read", "groups:read"),
    "conversations.history": ("channels:history", "groups:history",
                              "im:history", "mpim:history"),
    "conversations.replies": ("channels:history", "groups:history",
                              "im:history", "mpim:history"),
    "users.list": ("users:read",),
    "users.info": ("users:read",),
    "users.lookupByEmail": ("users:read.email",),
    "users.conversations": ("channels:read", "groups:read", "im:read", "mpim:read"),
    "chat.postMessage": ("chat:write", "chat:write.public"),
    "chat.update": ("chat:write",),
    "files.list": ("files:read",),
    "files.info": ("files:read",),
    "emoji.list": ("emoji:read",),
    "usergroups.list": ("usergroups:read",),
    "reactions.get": ("reactions:read",),
    "pins.list": ("pins:read",),
    "bookmarks.list": ("bookmarks:read",),
    "search.messages": ("search:read",),
    "admin.teams.list": ("admin.teams:read",),
    "admin.users.list": ("admin.users:read",),
    "admin.conversations.search": ("admin.conversations:read",),
}

# Tier, and why it matters if the token is ever found somewhere it should not be.
TIERS = (
    ("admin", "acts across the organisation, not just this workspace"),
    ("write", "changes the workspace; a read-only integration should hold none"),
    ("pii", "enumerates staff identities and addresses"),
    ("archive", "opens the full message archive of every conversation it covers"),
    ("read", "ordinary read access; surplus is untidy rather than dangerous"),
)
SERIOUS = ("admin", "write", "pii", "archive")


def _tier(scope):
    if scope.startswith("admin."):
        return "admin"
    if ":write" in scope:
        return "write"
    if scope in ("users:read.email", "users.profile:read"):
        return "pii"
    if scope.endswith(":history"):
        return "archive"
    return "read"


def justify(granted, methods):
    """Split a granted scope list against the methods the app actually calls. Pure.

    Returns (justified, surplus, gaps, unknown). `justified` is every granted
    scope that satisfies at least one called method; `surplus` is the rest;
    `gaps` are called methods with none of their scopes granted; `unknown` are
    methods absent from the table, which make `surplus` a candidate list rather
    than a verdict.
    """
    granted = sorted(set(granted))
    justified, gaps, unknown = set(), [], []
    for method in sorted(set(methods)):
        options = SCOPES_FOR_METHOD.get(method)
        if options is None:
            unknown.append(method)
            continue
        if not options:
            continue
        hit = [s for s in options if s in granted]
        if hit:
            justified.update(hit)
        else:
            gaps.append((method, list(options)))
    surplus = [s for s in granted if s not in justified]
    return (sorted(justified), surplus, gaps, unknown)


def rank(scopes):
    """Order surplus scopes by what they would cost if the token leaked. Pure."""
    order = {name: i for i, (name, _why) in enumerate(TIERS)}
    why = dict(TIERS)
    out = [(s, _tier(s), why[_tier(s)]) for s in scopes]
    return sorted(out, key=lambda row: (order[row[1]], row[0]))


def granted_scopes(session, token):
    """The complete grant, from the header Slack puts on every response."""
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    header = r.headers.get("X-OAuth-Scopes")
    try:
        body = r.json()
    except ValueError:
        body = {"ok": False, "error": "unparseable_body"}
    scopes = [s.strip() for s in (header or "").split(",") if s.strip()]
    return (scopes, header is not None, body)


def load_calls(path):
    """One Slack method name per line; comments and blanks ignored."""
    lines = open(path, encoding="utf-8").read().splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calls", help="file of Slack method names this app actually calls")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (the token the app actually deploys with)")
        return 2
    if not args.calls:
        log.error("pass --calls with the methods this app calls. Build it with:")
        log.error("  grep -rhoE 'slack[./][a-z]+\\\\.[a-zA-Z]+' . | sort -u")
        log.error("A surplus scope is only surplus relative to a call inventory, so "
                  "this script will not guess one.")
        return 2

    s = requests.Session()
    scopes, had_header, body = granted_scopes(s, token)
    if body.get("ok") is not True:
        log.error("auth.test answered error=%s; fix the credential first",
                  body.get("error") or "?")
        return 2
    if not had_header:
        log.error("no X-OAuth-Scopes header on the response. Something between this "
                  "script and Slack is stripping it, and the audit cannot proceed")
        return 2

    methods = load_calls(args.calls)
    justified, surplus, gaps, unknown = justify(scopes, methods)

    log.info("granted %d, justified %d, surplus %d, gaps %d",
             len(scopes), len(justified), len(surplus), len(gaps))

    serious = 0
    for scope, tier, why in rank(surplus):
        line = "%-9s %-26s %s" % (tier, scope, why)
        if tier in SERIOUS:
            serious += 1
            log.warning(line)
        else:
            log.info(line)

    for method, options in gaps:
        log.warning("%-9s %-26s none of %s is granted; that is a missing scope, "
                    "not a surplus one", "gap", method, ", ".join(options))

    if unknown:
        log.warning("%-9s %d method(s) are not in this script's table: %s",
                    "unmapped", len(unknown), ", ".join(unknown))
        log.warning("  each one may justify a scope listed above, so treat the "
                    "surplus list as candidates until they are mapped")

    if serious:
        log.warning("repair: prune OAuth & Permissions to the justified set, then "
                    "reinstall -- removing a scope needs a reinstall too")
        log.warning("repair: where broad read access is genuinely needed, split it "
                    "into a second app so the wide token has its own blast radius")

    log.info("%d surplus scope(s) above the ordinary-read tier", serious)
    return 1 if serious else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-scope-surplus.mjs",
"js": '''/**
 * Find Slack scopes on the deployed token that no call site justifies.
 *
 * Read only, and unusually, nothing here is failing: the script proves a
 * negative rather than reading an error. One GET, and the answer is in a
 * response header. The prune and the reinstall are printed for a human to run.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Per method, the scopes that would each satisfy it: an OR list, not an AND
// list. Deliberately incomplete -- Slack has hundreds of methods, and a method
// missing from this table is reported rather than assumed harmless.
const SCOPES_FOR_METHOD = {
  'auth.test': [],
  'team.info': ['team:read'],
  'conversations.list': ['channels:read', 'groups:read', 'im:read', 'mpim:read'],
  'conversations.info': ['channels:read', 'groups:read', 'im:read', 'mpim:read'],
  'conversations.members': ['channels:read', 'groups:read'],
  'conversations.history': ['channels:history', 'groups:history', 'im:history', 'mpim:history'],
  'conversations.replies': ['channels:history', 'groups:history', 'im:history', 'mpim:history'],
  'users.list': ['users:read'],
  'users.info': ['users:read'],
  'users.lookupByEmail': ['users:read.email'],
  'users.conversations': ['channels:read', 'groups:read', 'im:read', 'mpim:read'],
  'chat.postMessage': ['chat:write', 'chat:write.public'],
  'chat.update': ['chat:write'],
  'files.list': ['files:read'],
  'files.info': ['files:read'],
  'emoji.list': ['emoji:read'],
  'usergroups.list': ['usergroups:read'],
  'reactions.get': ['reactions:read'],
  'pins.list': ['pins:read'],
  'bookmarks.list': ['bookmarks:read'],
  'search.messages': ['search:read'],
  'admin.teams.list': ['admin.teams:read'],
  'admin.users.list': ['admin.users:read'],
  'admin.conversations.search': ['admin.conversations:read'],
};

// Tier, and why it matters if the token is ever found somewhere it should not be.
const TIERS = [
  ['admin', 'acts across the organisation, not just this workspace'],
  ['write', 'changes the workspace; a read-only integration should hold none'],
  ['pii', 'enumerates staff identities and addresses'],
  ['archive', 'opens the full message archive of every conversation it covers'],
  ['read', 'ordinary read access; surplus is untidy rather than dangerous'],
];
const SERIOUS = new Set(['admin', 'write', 'pii', 'archive']);

function tierOf(scope) {
  if (scope.startsWith('admin.')) return 'admin';
  if (scope.includes(':write')) return 'write';
  if (scope === 'users:read.email' || scope === 'users.profile:read') return 'pii';
  if (scope.endsWith(':history')) return 'archive';
  return 'read';
}

/**
 * Split a granted scope list against the methods the app actually calls. Pure.
 * Returns [justified, surplus, gaps, unknown]. `unknown` are methods absent from
 * the table, which make `surplus` a candidate list rather than a verdict.
 */
export function justify(granted, methods) {
  const grantedSet = new Set(granted);
  const sortedGranted = [...grantedSet].sort();
  const justified = new Set();
  const gaps = [];
  const unknown = [];

  for (const method of [...new Set(methods)].sort()) {
    const options = SCOPES_FOR_METHOD[method];
    if (options === undefined) {
      unknown.push(method);
      continue;
    }
    if (options.length === 0) continue;
    const hit = options.filter((s) => grantedSet.has(s));
    if (hit.length) hit.forEach((s) => justified.add(s));
    else gaps.push([method, options]);
  }

  const surplus = sortedGranted.filter((s) => !justified.has(s));
  return [[...justified].sort(), surplus, gaps, unknown];
}

/** Order surplus scopes by what they would cost if the token leaked. Pure. */
export function rank(scopes) {
  const order = new Map(TIERS.map(([name], i) => [name, i]));
  const why = new Map(TIERS);
  return scopes
    .map((s) => [s, tierOf(s), why.get(tierOf(s))])
    .sort((a, b) => (order.get(a[1]) - order.get(b[1])) || a[0].localeCompare(b[0]));
}

async function grantedScopes(token) {
  const res = await fetch(API + 'auth.test', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const header = res.headers.get('x-oauth-scopes');
  let body;
  try {
    body = await res.json();
  } catch {
    body = { ok: false, error: 'unparseable_body' };
  }
  const scopes = (header ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  return [scopes, header !== null, body];
}

async function main() {
  const args = process.argv.slice(2);
  const i = args.indexOf('--calls');
  const callsPath = i === -1 ? null : args[i + 1];

  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (the token the app actually deploys with)');
    process.exitCode = 2;
    return;
  }
  if (!callsPath) {
    console.error('pass --calls with the methods this app calls. Build it with:');
    console.error("  grep -rhoE 'slack[./][a-z]+\\\\.[a-zA-Z]+' . | sort -u");
    console.error('A surplus scope is only surplus relative to a call inventory, ' +
                  'so this script will not guess one.');
    process.exitCode = 2;
    return;
  }

  const [scopes, hadHeader, body] = await grantedScopes(token);
  if (body?.ok !== true) {
    console.error(`auth.test answered error=${body?.error ?? '?'}; fix the credential first`);
    process.exitCode = 2;
    return;
  }
  if (!hadHeader) {
    console.error('no X-OAuth-Scopes header on the response. Something between this ' +
                  'script and Slack is stripping it, and the audit cannot proceed');
    process.exitCode = 2;
    return;
  }

  const methods = (await readFile(callsPath, 'utf8'))
    .split('\\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
  const [justified, surplus, gaps, unknown] = justify(scopes, methods);

  console.log(`granted ${scopes.length}, justified ${justified.length}, surplus ` +
              `${surplus.length}, gaps ${gaps.length}`);

  let serious = 0;
  for (const [scope, tier, why] of rank(surplus)) {
    const line = `${tier.padEnd(9)} ${scope.padEnd(26)} ${why}`;
    if (SERIOUS.has(tier)) {
      serious += 1;
      console.warn(line);
    } else {
      console.log(line);
    }
  }

  for (const [method, options] of gaps) {
    console.warn(`${'gap'.padEnd(9)} ${method.padEnd(26)} none of ${options.join(', ')} ` +
                 'is granted; that is a missing scope, not a surplus one');
  }

  if (unknown.length) {
    console.warn(`${'unmapped'.padEnd(9)} ${unknown.length} method(s) are not in this ` +
                 `script's table: ${unknown.join(', ')}`);
    console.warn('  each one may justify a scope listed above, so treat the surplus ' +
                 'list as candidates until they are mapped');
  }

  if (serious) {
    console.warn('repair: prune OAuth & Permissions to the justified set, then ' +
                 'reinstall -- removing a scope needs a reinstall too');
    console.warn('repair: where broad read access is genuinely needed, split it into ' +
                 'a second app so the wide token has its own blast radius');
  }

  console.log(`${serious} surplus scope(s) above the ordinary-read tier`);
  process.exitCode = serious ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The trap in an audit that proves a negative is the method it has never heard of: silently ignoring it turns &ldquo;we could not check&rdquo; into &ldquo;it is surplus&rdquo;, and the report becomes a confident instruction to remove a scope something depends on. So the tests pin that an unmapped method is returned separately, and that a scope satisfied by an OR list is counted as justified by whichever option was actually granted.",
"test_py_file": "test_slack_scope_surplus.py",
"test_py": '''from slack_scope_surplus import justify, rank


def test_a_scope_with_no_call_site_is_surplus():
    justified, surplus, gaps, unknown = justify(
        ["chat:write", "admin.users:read"], ["chat.postMessage"])
    assert justified == ["chat:write"]
    assert surplus == ["admin.users:read"]
    assert gaps == [] and unknown == []


def test_an_or_list_is_justified_by_whichever_option_was_granted():
    justified, surplus, _, _ = justify(["groups:history"], ["conversations.history"])
    assert justified == ["groups:history"]
    assert surplus == []


def test_a_method_the_table_does_not_know_is_reported_not_ignored():
    justified, surplus, gaps, unknown = justify(["pins:read"], ["pins.add"])
    assert unknown == ["pins.add"]
    assert surplus == ["pins:read"]
    assert gaps == []


def test_a_called_method_with_no_granted_scope_is_a_gap_not_a_surplus():
    _, surplus, gaps, _ = justify(["chat:write"], ["chat.postMessage", "users.list"])
    assert surplus == []
    assert gaps == [("users.list", ["users:read"])]


def test_a_method_that_needs_no_scope_justifies_nothing():
    justified, surplus, _, _ = justify(["team:read"], ["auth.test"])
    assert justified == []
    assert surplus == ["team:read"]


def test_ranking_puts_admin_scopes_first_and_plain_reads_last():
    ordered = [row[0] for row in rank(
        ["emoji:read", "channels:history", "admin.users:write", "files:write",
         "users:read.email"])]
    assert ordered == ["admin.users:write", "files:write", "users:read.email",
                       "channels:history", "emoji:read"]


def test_write_scopes_are_flagged_even_when_they_look_narrow():
    assert dict((s, t) for s, t, _ in rank(["chat:write.public"]))["chat:write.public"] == "write"


def test_history_is_ranked_as_an_archive_scope():
    assert rank(["im:history"])[0][1] == "archive"


def test_ordinary_reads_carry_a_gentler_explanation():
    _, _, why = rank(["emoji:read"])[0]
    assert "untidy" in why
''',
"test_js_file": "slack-scope-surplus.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { justify, rank } from './slack-scope-surplus.mjs';

test('a scope with no call site is surplus', () => {
  const [justified, surplus, gaps, unknown] = justify(
    ['chat:write', 'admin.users:read'], ['chat.postMessage']);
  assert.deepEqual(justified, ['chat:write']);
  assert.deepEqual(surplus, ['admin.users:read']);
  assert.deepEqual(gaps, []);
  assert.deepEqual(unknown, []);
});

test('an or list is justified by whichever option was granted', () => {
  const [justified, surplus] = justify(['groups:history'], ['conversations.history']);
  assert.deepEqual(justified, ['groups:history']);
  assert.deepEqual(surplus, []);
});

test('a method the table does not know is reported not ignored', () => {
  const [, surplus, gaps, unknown] = justify(['pins:read'], ['pins.add']);
  assert.deepEqual(unknown, ['pins.add']);
  assert.deepEqual(surplus, ['pins:read']);
  assert.deepEqual(gaps, []);
});

test('a called method with no granted scope is a gap not a surplus', () => {
  const [, surplus, gaps] = justify(['chat:write'], ['chat.postMessage', 'users.list']);
  assert.deepEqual(surplus, []);
  assert.deepEqual(gaps, [['users.list', ['users:read']]]);
});

test('a method that needs no scope justifies nothing', () => {
  const [justified, surplus] = justify(['team:read'], ['auth.test']);
  assert.deepEqual(justified, []);
  assert.deepEqual(surplus, ['team:read']);
});

test('ranking puts admin scopes first and plain reads last', () => {
  const ordered = rank(['emoji:read', 'channels:history', 'admin.users:write',
    'files:write', 'users:read.email']).map((row) => row[0]);
  assert.deepEqual(ordered, ['admin.users:write', 'files:write', 'users:read.email',
    'channels:history', 'emoji:read']);
});

test('write scopes are flagged even when they look narrow', () => {
  assert.equal(rank(['chat:write.public'])[0][1], 'write');
});

test('history is ranked as an archive scope', () => {
  assert.equal(rank(['im:history'])[0][1], 'archive');
});

test('ordinary reads carry a gentler explanation', () => {
  assert.match(rank(['emoji:read'])[0][2], /untidy/);
});
''',
"faq": [
 ("How can a script prove a scope is unused?",
  "It cannot, on its own, and it should not claim to. What it can do is compare the grant against a stated inventory of the methods your code calls, and report any scope that inventory does not justify. That is why the script refuses to run without a call list and why it reports methods it could not map: the conclusion is only as good as the inventory, and saying so is part of the output."),
 ("Does removing a scope really need a reinstall?",
  "Yes, in both directions. A token is a snapshot of the grant at the moment it was issued, so pruning the scope list changes what the next installation will request and leaves the deployed token exactly as it was. The scope is only gone once the app has been installed again and the new token has replaced the old one everywhere it is stored."),
 ("Which surplus scopes are actually worth acting on?",
  "Anything under admin.*, because it acts across a Grid organisation; anything containing :write on an integration that only reads; users:read.email, because it turns a leak into a staff directory; and the :history family, because it opens the full message archive of every conversation it covers. An unused emoji:read is worth tidying and is not worth an incident."),
 ("Is chat:write.public really that different from chat:write?",
  "Yes. chat:write lets the app post in conversations it has been added to, so somebody made a decision for each one. chat:write.public removes that step entirely and lets the app post in any public channel in the workspace without being invited. If the app posts to a fixed set of channels, the invitation is the cheaper and much narrower answer."),
 ("What if two teams share one app to avoid a second install?",
  "Then one token carries the union of both teams' needs, and a leak carries both. Splitting them into two apps costs a second installation and buys two smaller blast radiuses, two independent rotation schedules, and the ability to revoke one without breaking the other. That is usually the right trade the moment either half needs a history or admin scope."),
],
"related": [
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/public-file-links-exposed/", "file links that need no login"),
 ("/slack/users-read-email-missing/", "every profile has a null email"),
],
"citations": [CITE_SCOPES, CITE_SECURITY, CITE_INSTALL, CITE_AUTH_TEST],
},

]
