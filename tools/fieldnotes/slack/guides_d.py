#!/usr/bin/env python3
"""/slack/ field notes, batch D — the writing.

Four notes that all end in a token that will not work, and that reach that end
by four different roads. One compares an app's two credentials against each
other and finds the scope sitting on the wrong one. One sweeps an installation
store and sorts dead rows by what should happen to them, which is almost never
"retry". One joins the install rows against the member directory and asks which
human each token is standing on. One does arithmetic on the stored OAuth
response and finds the installs that will expire tonight, before any of them do.

The error strings differ, but so does the evidence: two X-OAuth-Scopes headers
read side by side, a triage table over auth.test error codes, a users.list
census joined on authed_user.id, and a clock compared against expires_in.

Read-only throughout. These scripts are handed credentials that can post into a
workspace, and in two of them they are handed several tenants' credentials at
once, so none of them writes: every one reports what it found and prints the
repair for a human to run.
"""

CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_TOKENS = ("Token types — Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_INSTALL = ("Installing with OAuth — Slack Docs",
                "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_OAUTH_ACCESS = ("oauth.v2.access method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/oauth.v2.access")
CITE_ROTATION = ("Using token rotation — Slack Docs",
                 "https://docs.slack.dev/authentication/using-token-rotation")
CITE_TOKENS_REVOKED = ("The tokens_revoked event — Slack Docs",
                       "https://docs.slack.dev/reference/events/tokens_revoked")
CITE_APP_UNINSTALLED = ("The app_uninstalled event — Slack Docs",
                        "https://docs.slack.dev/reference/events/app_uninstalled")
CITE_USERS_INFO = ("users.info method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_USERS_LIST = ("users.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")

GUIDES = [

{
"slug": "bot-vs-user-scope-mixup",
"title": "The scope was granted to the user token, not the bot",
"description": "Slack keeps two scope lists per app. Add the scope to one and call with the other and missing_scope survives every reinstall you throw at it.",
"h1": "the scope was granted to the user token, not the bot",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot token vs user token scopes", "missing_scope after reinstall",
             "slack user token scopes xoxp", "authed_user access_token bolt",
             "slack search:read bot token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You added the scope. The consent screen listed it, an admin approved it, you reinstalled, you replaced the stored token, and the call still returns <code>missing_scope</code> with that exact scope in <code>needed</code>. Open the app configuration and there it is, plainly granted &mdash; under <strong>User Token Scopes</strong>, while every line of your code authenticates with the <code>xoxb-</code> bot token.",
"short_answer": """<p>Call <code>auth.test</code> once with each of the app's two tokens and read <code>X-OAuth-Scopes</code> off both responses. Those two headers are the two scope lists, as granted, on the credentials you are actually deploying. The scope you need is on one of them and your code is calling with the other.</p>
<p>Then decide which identity should do the work rather than which list is easier to edit. Some scopes are only offered on one side: <code>search:read</code> and <code>users.profile:write</code> exist only as user scopes, <code>app_mentions:read</code> and <code>commands</code> only as bot scopes. Where both are possible, prefer the bot &mdash; it outlives the person who installed the app.</p>""",
"problem": """<p>Slack apps have two identities and most codebases have one environment variable. The install flow returns both credentials in one response: <code>access_token</code> is the bot token, <code>authed_user.access_token</code> is the user token, and they carry two entirely separate grants that were approved on the same consent screen in the same click. Nothing in the response labels which one your code should keep, and a great many apps keep the first one, call it <code>SLACK_TOKEN</code>, and never learn there was a second.</p>
<p>The configuration page reinforces the confusion by putting both lists on one screen under one heading. <strong>Bot Token Scopes</strong> and <strong>User Token Scopes</strong> sit a few pixels apart, they autocomplete from overlapping vocabularies, and adding <code>channels:history</code> to the wrong one looks identical to adding it to the right one. The app then requests it, the admin approves it, and the grant lands on a token your runtime never touches.</p>
<p>What makes this specifically maddening is that the standard repair for <code>missing_scope</code> &mdash; add the scope, reinstall, replace the token &mdash; is exactly what you have been doing, and it is working perfectly. Each reinstall faithfully re-grants the scope to the token that already had it. The error is unchanged because nothing about the failing call has changed, and after the third round trip through an admin approval queue it is very easy to conclude that Slack is broken.</p>""",
"why": """<p><strong>The two lists are independent grants, not a display detail.</strong> A bot token's scopes describe what the app may do as itself; a user token's scopes describe what it may do while impersonating the human who installed it. They are stored separately, revoked separately, and reported separately in <code>X-OAuth-Scopes</code>.</p>
<p><strong>Some scopes only exist on one side.</strong> Message search is user-only: there is no bot equivalent of <code>search:read</code>, so an app that wants to search must hold a user token, full stop. Equally, <code>commands</code> and <code>app_mentions:read</code> are bot-only. When the scope you need is one of these, "move it to the other list" is not available and the code has to change instead.</p>
<p><strong><code>auth.test</code> distinguishes them and the token prefix does not always.</strong> A bot token's response carries a <code>bot_id</code>; a user token's does not. Both return a <code>user_id</code> starting <code>U</code> or <code>W</code>, and on a bot token that id is the bot user, which is why comparing ids tells you nothing.</p>
<p><strong>The user token dies with the user.</strong> A scope moved to the user side to make one call work has quietly made the whole integration dependent on one employee's account remaining active. That is a different failure with its own note, and it arrives on somebody's last day.</p>
<p><strong>One environment variable cannot hold two credentials.</strong> The durable fix is not a scope edit, it is naming: <code>SLACK_BOT_TOKEN</code> and <code>SLACK_USER_TOKEN</code>, so every call site states which identity it is acting as, and a swap is visible in a diff rather than at runtime.</p>""",
"steps": [
 {"h": "Put both tokens in the environment under distinct names",
  "body": """<p>The audit needs both halves of the install: <code>SLACK_BOT_TOKEN</code> from <strong>Bot User OAuth Token</strong> and <code>SLACK_USER_TOKEN</code> from <strong>User OAuth Token</strong> on the same page. If your store only kept one, that is itself the finding &mdash; the script says so and reports what it can see from one side.</p>"""},
 {"h": "Ask each token who it is",
  "body": """<p>One <code>auth.test</code> per token. The presence of <code>bot_id</code> in the body is the only reliable discriminator, and the script checks it against the variable's name: a user token in <code>SLACK_BOT_TOKEN</code> explains a great deal on its own.</p>"""},
 {"h": "Read both scope lists off those same two responses",
  "body": """<p><code>X-OAuth-Scopes</code> is returned on every Web API response and describes the calling token. Reading it from the live response, rather than from the configuration page, is the point: the page describes the app you intend to deploy, the header describes the credential that is running.</p>"""},
 {"h": "Diff the two lists before you look for anything specific",
  "body": """<p>The scopes held by one token and not the other are where every instance of this bug lives. Printing that split first often ends the investigation before the developer has finished naming the scope they were looking for.</p>"""},
 {"h": "Name the scope you need and the token your code calls with",
  "body": """<p><code>--need channels:history --caller bot</code> asks the only question that matters: is the grant on the credential the failing code path uses? The answer separates "on the other token" from "granted nowhere", which is an ordinary missing scope and a different repair.</p>"""},
 {"h": "Move the scope, or move the call, and reinstall",
  "body": """<p>If the app should act as itself, add the scope under <strong>Bot Token Scopes</strong> and reinstall. If it must act as a human, keep it under <strong>User Token Scopes</strong> and change the code to authenticate with <code>authed_user.access_token</code>. Either way the token in the store must be replaced; a reinstall does not upgrade tokens already in circulation.</p>"""},
],
"verify": """<p>Re-run with the same arguments after the reinstall. The scope should be reported on the calling token, and the split should show it as no longer exclusive to the other side.</p>
<pre><code class="language-bash">python3 slack_token_identity_split.py --need channels:history --caller bot
# correct    channels:history  held by the bot token this code path calls with
# 1 scope(s) checked, 0 on the wrong token</code></pre>""",
"code_intro": "Two GETs, one per token, and nothing else &mdash; this script is handed both of an app's credentials at once, which is exactly why it must not be able to act with either. Four pure functions carry the logic: <code>scope_set</code> parses the header, <code>identity_kind</code> reads <code>bot_id</code>, <code>split</code> does the three-way comparison, and <code>verdict</code> answers the question for one named scope.",
"py_file": "slack_token_identity_split.py",
"py": '''"""Compare a Slack app's two tokens and find scopes granted to the wrong one.

Read only. Two GET requests and nothing else. This script holds both halves of
an app's install at once, so it must not be able to act with either; the repair
is printed for a human to run.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_token_identity_split")

API = "https://slack.com/api/"

# Scopes Slack offers on one list only. When the scope you need is one of these,
# "move it to the other list" is not an available repair and the calling code has
# to change instead. Not exhaustive; it is the set that shows up in this bug.
USER_ONLY = {
    "search:read", "search:read.files", "search:read.messages",
    "users.profile:write", "identity.basic", "identity.email",
    "identity.avatar", "identity.team", "stars:read", "dnd:write:user",
}
BOT_ONLY = {
    "app_mentions:read", "commands", "incoming-webhook", "workflow.steps:execute",
}


def scope_set(header):
    """X-OAuth-Scopes as a frozenset. Pure.

    Slack returns one comma-joined string on every response. Some proxies strip
    it, so an absent header means "unknown" and must never be read as "none" --
    that reading turns a missing header into a full sheet of false findings.
    """
    if not header:
        return frozenset()
    return frozenset(s.strip() for s in header.split(",") if s.strip())


def identity_kind(body):
    """Which of the two token classes answered auth.test. Pure.

    A bot token's response carries bot_id; a user token's does not. Both carry a
    user_id beginning U or W, and on a bot token that id is the bot user, which
    is why the id alone cannot tell them apart.
    """
    if body.get("ok") is not True:
        return "unusable"
    return "bot" if body.get("bot_id") else "user"


def split(bot_scopes, user_scopes):
    """The three-way comparison this whole audit rests on. Pure.

    Returns (both, bot_only, user_only). The last two are where every instance
    of this bug lives, and printing them usually ends the investigation.
    """
    return (tuple(sorted(bot_scopes & user_scopes)),
            tuple(sorted(bot_scopes - user_scopes)),
            tuple(sorted(user_scopes - bot_scopes)))


def side(scope):
    """Which of the two lists this scope can appear on at all. Pure."""
    if scope in USER_ONLY:
        return "user-only"
    if scope in BOT_ONLY:
        return "bot-only"
    return "either"


def verdict(scope, caller, caller_scopes, other_scopes):
    """Answer one question: is this scope on the token the failing code uses?

    `caller` is "bot" or "user" -- the identity the runtime code path
    authenticates as. Pure, so the whole truth table runs offline.
    """
    other = "user" if caller == "bot" else "bot"
    where = side(scope)
    held = scope in caller_scopes
    elsewhere = scope in other_scopes

    if held and elsewhere:
        return ("granted-twice",
                "both tokens hold %s. Nothing is broken, but the call site "
                "decides which identity acts, so make that choice explicit "
                "rather than leaving it to whichever variable was in scope."
                % scope)
    if held:
        return ("correct",
                "held by the %s token this code path calls with" % caller)
    if elsewhere:
        if where != "either":
            return ("wrong-side",
                    "%s is granted to the %s token, and it is a %s scope: it "
                    "cannot be moved. The %s code path has to authenticate "
                    "with the %s token instead." % (scope, other, where, caller, other))
        return ("wrong-side",
                "%s is granted to the %s token and this code path calls with "
                "the %s token. Reinstalling re-grants it to the same side, "
                "which is why the error never changed." % (scope, other, caller))
    if where != "either" and where != caller + "-only":
        return ("unobtainable",
                "%s is a %s scope and this code path calls with the %s token. "
                "It is not offered on the %s list, so request it on the %s "
                "side and switch the call." % (scope, where, caller, caller, other))
    return ("granted-nowhere",
            "neither token holds %s. This is an ordinary missing scope: add it "
            "to the %s list, reinstall, and replace the stored token." % (scope, caller))


def probe(session, token):
    """auth.test for one token. Returns (X-OAuth-Scopes, parsed body)."""
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.headers.get("X-OAuth-Scopes"), r.json()
    except ValueError:
        return r.headers.get("X-OAuth-Scopes"), {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--need", action="append", default=[],
                    help="a scope the failing call requires; repeatable")
    ap.add_argument("--caller", choices=("bot", "user"), default="bot",
                    help="which token the failing code path authenticates with")
    args = ap.parse_args()

    tokens = {"bot": os.environ.get("SLACK_BOT_TOKEN"),
              "user": os.environ.get("SLACK_USER_TOKEN")}
    if not tokens["bot"] and not tokens["user"]:
        log.error("set SLACK_BOT_TOKEN and SLACK_USER_TOKEN to the two halves of "
                  "one install (OAuth & Permissions shows both)")
        return 2

    s = requests.Session()
    scopes = {"bot": frozenset(), "user": frozenset()}
    bad = 0

    for role in ("bot", "user"):
        token = tokens[role]
        if not token:
            log.warning("%-16s %s", "token-absent",
                        "SLACK_%s_TOKEN is unset, so that side of the grant "
                        "cannot be read and findings about it are provisional"
                        % role.upper())
            bad += 1
            continue
        header, body = probe(s, token)
        kind = identity_kind(body)
        scopes[role] = scope_set(header)
        if kind == "unusable":
            log.warning("%-16s %s token: auth.test answered ok: false, error=%s",
                        "unusable", role, body.get("error") or "<no error field>")
            bad += 1
            continue
        if kind != role:
            bad += 1
            log.warning("%-16s SLACK_%s_TOKEN holds a %s token: auth.test %s a "
                        "bot_id. Half of this bug is a mislabelled variable.",
                        "mislabelled", role.upper(), kind,
                        "returned" if kind == "bot" else "returned no")
        log.info("%-16s %s token, team=%s, %d scope(s)%s", "identity", kind,
                 body.get("team_id"), len(scopes[role]),
                 "" if scopes[role] else " (X-OAuth-Scopes absent from the response)")

    both, bot_only, user_only = split(scopes["bot"], scopes["user"])
    log.info("%-16s %s", "on both", ", ".join(both) or "<none>")
    log.info("%-16s %s", "bot only", ", ".join(bot_only) or "<none>")
    log.info("%-16s %s", "user only", ", ".join(user_only) or "<none>")

    other = "user" if args.caller == "bot" else "bot"
    for scope in args.need:
        state, detail = verdict(scope, args.caller, scopes[args.caller], scopes[other])
        line = "%-16s %-22s %s" % (state, scope, detail)
        if state in ("correct", "granted-twice"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "wrong-side":
            log.warning("  repair: decide which identity should act, then either move "
                        "the scope between the two lists and reinstall, or call with "
                        "the token that already holds it")
        else:
            log.warning("  repair: OAuth & Permissions -> %s Token Scopes, add the "
                        "scope, reinstall, replace the stored token",
                        "Bot" if args.caller == "bot" else "User")

    log.info("%d scope(s) checked, %d on the wrong token or unreadable",
             len(args.need), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-token-identity-split.mjs",
"js": '''/**
 * Compare a Slack app's two tokens and find scopes granted to the wrong one.
 *
 * Read only. Two GET requests and nothing else. This script holds both halves
 * of an app's install at once, so it must not be able to act with either; the
 * repair is printed for a human to run.
 */
const API = 'https://slack.com/api/';

// Scopes Slack offers on one list only. When the scope you need is one of
// these, "move it to the other list" is not an available repair and the calling
// code has to change instead. Not exhaustive; it is the set that shows up here.
export const USER_ONLY = new Set([
  'search:read', 'search:read.files', 'search:read.messages',
  'users.profile:write', 'identity.basic', 'identity.email',
  'identity.avatar', 'identity.team', 'stars:read', 'dnd:write:user',
]);
export const BOT_ONLY = new Set([
  'app_mentions:read', 'commands', 'incoming-webhook', 'workflow.steps:execute',
]);

/**
 * X-OAuth-Scopes as a Set. Pure. An absent header means "unknown" and must
 * never be read as "none": that reading turns a stripped header into a full
 * sheet of false findings.
 */
export function scopeSet(header) {
  if (!header) return new Set();
  return new Set(header.split(',').map((s) => s.trim()).filter(Boolean));
}

/**
 * Which of the two token classes answered auth.test. Pure. A bot token's
 * response carries bot_id; a user token's does not. Both carry a user_id, and
 * on a bot token that id is the bot user, so the id alone proves nothing.
 */
export function identityKind(body) {
  if (body?.ok !== true) return 'unusable';
  return body.bot_id ? 'bot' : 'user';
}

/**
 * The three-way comparison this whole audit rests on. Pure.
 * Returns [both, botOnly, userOnly].
 */
export function split(botScopes, userScopes) {
  const both = [...botScopes].filter((s) => userScopes.has(s)).sort();
  const botOnly = [...botScopes].filter((s) => !userScopes.has(s)).sort();
  const userOnly = [...userScopes].filter((s) => !botScopes.has(s)).sort();
  return [both, botOnly, userOnly];
}

/** Which of the two lists this scope can appear on at all. Pure. */
export function side(scope) {
  if (USER_ONLY.has(scope)) return 'user-only';
  if (BOT_ONLY.has(scope)) return 'bot-only';
  return 'either';
}

/**
 * Answer one question: is this scope on the token the failing code uses?
 * `caller` is "bot" or "user". Pure, so the truth table runs offline.
 */
export function verdict(scope, caller, callerScopes, otherScopes) {
  const other = caller === 'bot' ? 'user' : 'bot';
  const where = side(scope);
  const held = callerScopes.has(scope);
  const elsewhere = otherScopes.has(scope);

  if (held && elsewhere) {
    return ['granted-twice',
      `both tokens hold ${scope}. Nothing is broken, but the call site decides ` +
      'which identity acts, so make that choice explicit rather than leaving it ' +
      'to whichever variable was in scope.'];
  }
  if (held) {
    return ['correct', `held by the ${caller} token this code path calls with`];
  }
  if (elsewhere) {
    if (where !== 'either') {
      return ['wrong-side',
        `${scope} is granted to the ${other} token, and it is a ${where} scope: ` +
        `it cannot be moved. The ${caller} code path has to authenticate with ` +
        `the ${other} token instead.`];
    }
    return ['wrong-side',
      `${scope} is granted to the ${other} token and this code path calls with ` +
      `the ${caller} token. Reinstalling re-grants it to the same side, which is ` +
      'why the error never changed.'];
  }
  if (where !== 'either' && where !== `${caller}-only`) {
    return ['unobtainable',
      `${scope} is a ${where} scope and this code path calls with the ${caller} ` +
      `token. It is not offered on the ${caller} list, so request it on the ` +
      `${other} side and switch the call.`];
  }
  return ['granted-nowhere',
    `neither token holds ${scope}. This is an ordinary missing scope: add it to ` +
    `the ${caller} list, reinstall, and replace the stored token.`];
}

async function probe(token) {
  const res = await fetch(API + 'auth.test', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const header = res.headers.get('x-oauth-scopes');
  try {
    return [header, await res.json()];
  } catch {
    return [header, { ok: false, error: 'unparseable_body' }];
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const need = [];
  let caller = 'bot';
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--need') need.push(argv[i + 1]);
    if (argv[i] === '--caller') caller = argv[i + 1] === 'user' ? 'user' : 'bot';
  }

  const tokens = { bot: process.env.SLACK_BOT_TOKEN, user: process.env.SLACK_USER_TOKEN };
  if (!tokens.bot && !tokens.user) {
    console.error('set SLACK_BOT_TOKEN and SLACK_USER_TOKEN to the two halves of ' +
                  'one install (OAuth & Permissions shows both)');
    process.exitCode = 2;
    return;
  }

  const scopes = { bot: new Set(), user: new Set() };
  let bad = 0;

  for (const role of ['bot', 'user']) {
    const token = tokens[role];
    if (!token) {
      console.warn(`${'token-absent'.padEnd(16)} SLACK_${role.toUpperCase()}_TOKEN is ` +
        'unset, so that side of the grant cannot be read and findings about it ' +
        'are provisional');
      bad += 1;
      continue;
    }
    const [header, body] = await probe(token);
    const kind = identityKind(body);
    scopes[role] = scopeSet(header);
    if (kind === 'unusable') {
      console.warn(`${'unusable'.padEnd(16)} ${role} token: auth.test answered ` +
        `ok: false, error=${body?.error ?? '<no error field>'}`);
      bad += 1;
      continue;
    }
    if (kind !== role) {
      bad += 1;
      console.warn(`${'mislabelled'.padEnd(16)} SLACK_${role.toUpperCase()}_TOKEN holds ` +
        `a ${kind} token: auth.test ${kind === 'bot' ? 'returned' : 'returned no'} a ` +
        'bot_id. Half of this bug is a mislabelled variable.');
    }
    console.log(`${'identity'.padEnd(16)} ${kind} token, team=${body.team_id}, ` +
      `${scopes[role].size} scope(s)` +
      (scopes[role].size ? '' : ' (X-OAuth-Scopes absent from the response)'));
  }

  const [both, botOnly, userOnly] = split(scopes.bot, scopes.user);
  console.log(`${'on both'.padEnd(16)} ${both.join(', ') || '<none>'}`);
  console.log(`${'bot only'.padEnd(16)} ${botOnly.join(', ') || '<none>'}`);
  console.log(`${'user only'.padEnd(16)} ${userOnly.join(', ') || '<none>'}`);

  const other = caller === 'bot' ? 'user' : 'bot';
  for (const scope of need) {
    const [state, detail] = verdict(scope, caller, scopes[caller], scopes[other]);
    const line = `${state.padEnd(16)} ${String(scope).padEnd(22)} ${detail}`;
    if (state === 'correct' || state === 'granted-twice') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (state === 'wrong-side') {
      console.warn('  repair: decide which identity should act, then either move the ' +
        'scope between the two lists and reinstall, or call with the token that ' +
        'already holds it');
    } else {
      console.warn('  repair: OAuth & Permissions -> ' +
        `${caller === 'bot' ? 'Bot' : 'User'} Token Scopes, add the scope, ` +
        'reinstall, replace the stored token');
    }
  }

  console.log(`${need.length} scope(s) checked, ${bad} on the wrong token or unreadable`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is the one that decides whether the advice is even possible: a user-only scope like <code>search:read</code>, wanted by a code path that calls with the bot token. Every other finding ends in \"move it and reinstall\", and this one must not &mdash; there is no bot list to move it to, and telling somebody to look for one costs them an afternoon.",
"test_py_file": "test_slack_token_identity_split.py",
"test_py": '''from slack_token_identity_split import identity_kind, scope_set, side, split, verdict


def test_scope_header_absent_is_unknown_not_empty():
    assert scope_set(None) == frozenset()
    assert scope_set("channels:read, users:read ,") == frozenset(
        {"channels:read", "users:read"})


def test_bot_id_is_the_only_discriminator():
    assert identity_kind({"ok": True, "user_id": "U1", "bot_id": "B1"}) == "bot"
    assert identity_kind({"ok": True, "user_id": "U1"}) == "user"
    assert identity_kind({"ok": False, "error": "invalid_auth"}) == "unusable"


def test_split_reports_the_exclusive_halves():
    both, bot_only, user_only = split(frozenset({"a", "b"}), frozenset({"b", "c"}))
    assert (both, bot_only, user_only) == (("b",), ("a",), ("c",))


def test_scope_on_the_other_token_is_the_finding():
    state, detail = verdict("channels:history", "bot",
                            frozenset(), frozenset({"channels:history"}))
    assert state == "wrong-side"
    assert "never changed" in detail


def test_user_only_scope_cannot_be_moved_to_the_bot_list():
    assert side("search:read") == "user-only"
    state, detail = verdict("search:read", "bot", frozenset(), frozenset())
    assert state == "unobtainable"
    assert "not offered on the bot list" in detail


def test_user_only_scope_held_by_the_user_token_says_switch_the_call():
    state, detail = verdict("search:read", "bot", frozenset(),
                            frozenset({"search:read"}))
    assert state == "wrong-side"
    assert "cannot be moved" in detail


def test_scope_on_the_calling_token_is_not_reported():
    assert verdict("users:read", "bot", frozenset({"users:read"}), frozenset())[0] == "correct"


def test_scope_on_neither_token_is_an_ordinary_missing_scope():
    state, detail = verdict("users:read", "user", frozenset(), frozenset())
    assert state == "granted-nowhere"
    assert "add it to the user list" in detail


def test_both_tokens_holding_it_is_ambiguity_rather_than_a_fault():
    assert verdict("users:read", "bot", frozenset({"users:read"}),
                   frozenset({"users:read"}))[0] == "granted-twice"
''',
"test_js_file": "slack-token-identity-split.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { identityKind, scopeSet, side, split, verdict } from './slack-token-identity-split.mjs';

test('scope header absent is unknown not empty', () => {
  assert.equal(scopeSet(null).size, 0);
  assert.deepEqual([...scopeSet('channels:read, users:read ,')].sort(),
    ['channels:read', 'users:read']);
});

test('bot_id is the only discriminator', () => {
  assert.equal(identityKind({ ok: true, user_id: 'U1', bot_id: 'B1' }), 'bot');
  assert.equal(identityKind({ ok: true, user_id: 'U1' }), 'user');
  assert.equal(identityKind({ ok: false, error: 'invalid_auth' }), 'unusable');
});

test('split reports the exclusive halves', () => {
  const [both, botOnly, userOnly] = split(new Set(['a', 'b']), new Set(['b', 'c']));
  assert.deepEqual([both, botOnly, userOnly], [['b'], ['a'], ['c']]);
});

test('scope on the other token is the finding', () => {
  const [state, detail] = verdict('channels:history', 'bot',
    new Set(), new Set(['channels:history']));
  assert.equal(state, 'wrong-side');
  assert.match(detail, /never changed/);
});

test('user only scope cannot be moved to the bot list', () => {
  assert.equal(side('search:read'), 'user-only');
  const [state, detail] = verdict('search:read', 'bot', new Set(), new Set());
  assert.equal(state, 'unobtainable');
  assert.match(detail, /not offered on the bot list/);
});

test('user only scope held by the user token says switch the call', () => {
  const [state, detail] = verdict('search:read', 'bot', new Set(), new Set(['search:read']));
  assert.equal(state, 'wrong-side');
  assert.match(detail, /cannot be moved/);
});

test('scope on the calling token is not reported', () => {
  assert.equal(verdict('users:read', 'bot', new Set(['users:read']), new Set())[0], 'correct');
});

test('scope on neither token is an ordinary missing scope', () => {
  const [state, detail] = verdict('users:read', 'user', new Set(), new Set());
  assert.equal(state, 'granted-nowhere');
  assert.match(detail, /add it to the user list/);
});

test('both tokens holding it is ambiguity rather than a fault', () => {
  assert.equal(verdict('users:read', 'bot', new Set(['users:read']),
    new Set(['users:read']))[0], 'granted-twice');
});
''',
"faq": [
 ("How do I tell a bot token from a user token if the prefix is missing?",
  "Call auth.test and look for bot_id in the body. A bot token returns it, a user token does not. The xoxb- and xoxp- prefixes are reliable for classic tokens, but a rotated token arrives as xoxe.xoxb- or xoxe.xoxp- and a token pasted into the wrong variable keeps its own prefix regardless of what the variable is called, so the body is the honest answer."),
 ("Can I just add the scope to both lists?",
  "You can, and for scopes offered on both sides it works. It also doubles the consent screen and leaves the choice of identity implicit at every call site, which is the condition that produced the bug. Decide whether the app is acting as itself or as a person, grant the scope on that side only, and let the second token fail loudly if something calls it."),
 ("Why does search have no bot scope?",
  "Slack scopes search to a human's view of the workspace. search:read returns what that person can see, including their DMs and private channels, so there is no coherent bot equivalent and none is offered. An app that must search has to hold a user token, which also means inheriting that user's account lifecycle."),
 ("Does reinstalling ever move a scope from one list to the other?",
  "No. A reinstall re-grants whatever the app configuration currently requests, on the side it requests it. If the scope is on the user list, every reinstall grants it to the user token, which is exactly why repeating the standard missing_scope repair changes nothing here."),
 ("What should I store after an install that grants both?",
  "Both tokens, under distinct keys, alongside the team and enterprise ids. access_token is the bot credential and authed_user.access_token is the user one. A single SLACK_TOKEN variable cannot represent two identities, and the day someone needs the other one they will overwrite the first."),
],
"related": [
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/token-revoked/", "token_revoked means the app is gone"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_TOKENS, CITE_SCOPES, CITE_AUTH_TEST, CITE_INSTALL],
},

{
"slug": "token-revoked",
"title": "token_revoked: the app is gone and retrying will not help",
"description": "token_revoked is permanent. Sweep auth.test across the installation store, sort the dead rows by what should happen to them, and stop scheduling work.",
"h1": "token_revoked: the app is gone and retrying will not help",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack token_revoked", "app_uninstalled event handler",
             "tokens_revoked slack event", "slack installation store cleanup",
             "slack multi workspace app uninstall"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One tenant of your multi-workspace app has received nothing for six weeks. No alert fired. The installation row is still there, still marked active, still being handed to the scheduler every fifteen minutes, and every call it makes returns <code>{\"ok\": false, \"error\": \"token_revoked\"}</code>. Somebody removed the app from <strong>Manage apps</strong> in January and your store has been retrying ever since.",
"short_answer": """<p>Iterate the installation store, call <code>auth.test</code> once per stored token, and sort the failures by what should actually be done about them. <code>token_revoked</code> is the one that never recovers: the grant is gone, the string in your database is dead, and no retry schedule will bring it back. Tombstone the row and stop scheduling work for that workspace.</p>
<p>The other failures in the same sweep look identical in a log line and need opposite treatment &mdash; <code>token_expired</code> wants a refresh, <code>account_inactive</code> wants a different kind of token, <code>ratelimited</code> wants a wait. The finding worth reporting is not "this token failed"; it is the number of rows your store still believes are healthy, and the number of live installs it has quietly stopped serving.</p>""",
"problem": """<p>An uninstall is a silent event on the app's side. An admin opens <strong>Manage apps</strong>, removes your app, and Slack invalidates every token issued for that workspace immediately. Slack does emit <code>app_uninstalled</code> and <code>tokens_revoked</code>, but only to apps that subscribed to them, and only over an event delivery path that the uninstall itself has just severed for that workspace. An app that never subscribed &mdash; or that dropped the event during a deploy &mdash; is never told.</p>
<p>So the installation store keeps a row that describes an app that is no longer installed. Every scheduled job for that tenant runs, calls the API, gets <code>200 OK</code> with <code>ok: false</code>, and either logs nothing or logs a line indistinguishable from a transient failure. Retry logic makes it worse: a generic backoff treats a permanently dead credential as a temporary outage and spends months rediscovering that it is still dead.</p>
<p>The mirror image is rarer and more expensive. A row disabled during an incident, or tombstoned by an over-eager cleanup that keyed on the wrong error, describes a workspace that is still installed and still paying. Nobody notices that one either, because a disabled row generates no errors at all. Both directions are the same defect: the store's opinion of an install and the API's are never compared.</p>""",
"why": """<p><strong><code>token_revoked</code> is terminal.</strong> The token is not expired, throttled, or misconfigured; the authorisation behind it no longer exists. Only a fresh OAuth install produces a working credential for that workspace, and that is a customer action, not something a retry can trigger.</p>
<p><strong>Slack's error codes are a disposition table, not a severity scale.</strong> <code>token_revoked</code> means delete the row, <code>token_expired</code> means refresh it, <code>account_inactive</code> means the human behind a user token was deactivated, <code>invalid_auth</code> means the string is wrong, and <code>ratelimited</code> means wait. Treating them as one bucket called "auth error" is what produces both a retry storm and a tombstoned paying customer.</p>
<p><strong>Whether the bot or the user token died tells you what happened.</strong> If the bot token is revoked and the user token with it, the app was removed from the workspace. If only the user token is revoked while the bot token still authenticates, one person revoked their own authorisation and the app is still installed. Those are different conversations with the customer.</p>
<p><strong>The events exist and are worth subscribing to.</strong> <code>tokens_revoked</code> names the revoked bot and user ids; <code>app_uninstalled</code> arrives once per workspace removal. Handling them in the same function this audit's repair describes means the store self-heals and the audit stops finding anything.</p>
<p><strong>Do not delete on a single failed call.</strong> A network blip and a revocation both produce an exception in a naive client. The disposition should come from the error code in the body, which is why the sweep reads <code>body.error</code> rather than catching whatever the HTTP layer threw.</p>""",
"steps": [
 {"h": "Export the store with its own opinion attached",
  "body": """<p>Each row needs the key, the environment variable holding its token, and the fields your store uses to decide whether to schedule work: a <code>status</code>, and a <code>last_ok</code> timestamp if you keep one. The audit is a comparison between that opinion and the API's, so an export that omits the status has nothing to compare.</p>"""},
 {"h": "Ask every token whether it still authenticates",
  "body": """<p>One <code>auth.test</code> per row. It needs no scopes, so it works for any token in any state, and its error field is the whole diagnosis. A healthy row answers <code>ok: true</code> with the team id, which is also a cheap check that the row is filed under the workspace it thinks it is.</p>"""},
 {"h": "Map each error to a disposition rather than a severity",
  "body": """<p><code>token_revoked</code> gets tombstoned. <code>token_expired</code> gets a refresh. <code>account_inactive</code> gets migrated to a bot token. <code>invalid_auth</code> gets its credential checked. <code>ratelimited</code> gets retried. Sorting the sweep this way turns a page of identical warnings into a short list of different jobs.</p>"""},
 {"h": "Compare the disposition against what your store believes",
  "body": """<p>A dead token in a row marked active is work going nowhere. A live token in a row marked disabled is a customer you stopped serving. The script counts both, because a cleanup that only looks for the first will eventually create the second.</p>"""},
 {"h": "Read the shape of the revocation per workspace",
  "body": """<p>Where you store both a bot and a user token for the same workspace, the pattern of which one died says what happened: both dead is an app removal, the user token alone is one person revoking their own authorisation, and the bot token alone is odd enough to look at by hand.</p>"""},
 {"h": "Tombstone, and subscribe to the events so it stops happening",
  "body": """<p>The repair is printed: mark the revoked rows dead, stop scheduling them, and handle <code>app_uninstalled</code> and <code>tokens_revoked</code> in the same code path the audit describes. Keep the row as a tombstone rather than deleting it, so a reinstall is an update and your churn numbers survive.</p>"""},
],
"verify": """<p>Re-run after the cleanup. Every remaining active row should authenticate, and no row should be disabled while its token still works.</p>
<pre><code class="language-bash">python3 slack_dead_install_sweep.py --store installs.json
# 24 row(s) swept, 0 dead but active, 0 live but disabled</code></pre>""",
"code_intro": "One GET per stored token and nothing else &mdash; this script is handed every tenant's credential at once, so it reports and never acts, and the cleanup it describes is a migration a human runs deliberately. Four pure functions: <code>disposition</code> maps an error code to a job, <code>is_retryable</code> answers the question retry logic keeps getting wrong, <code>reconcile</code> compares the store's opinion against the API's, and <code>revocation_shape</code> reads the pattern across a workspace's tokens.",
"py_file": "slack_dead_install_sweep.py",
"py": '''"""Sweep a Slack installation store for dead tokens and sort them by disposition.

Read only. One GET per stored token and nothing else: this script is handed
every tenant's credential at once, so it reports what it found and prints the
cleanup for a human to run.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_dead_install_sweep")

API = "https://slack.com/api/"

# What should happen to a row, keyed by the error auth.test returned. This is a
# disposition table, not a severity scale: the codes below are all "auth failed"
# and no two of them want the same treatment.
DISPOSITIONS = {
    "token_revoked": ("tombstone",
                      "the authorisation no longer exists. Only a fresh OAuth "
                      "install produces a working token for this workspace, and "
                      "that is a customer action"),
    "account_inactive": ("migrate",
                         "a user token whose human was deactivated. The app is "
                         "still installed; the person is gone"),
    "token_expired": ("refresh",
                      "a rotated token past its 12 hour life. The refresh token "
                      "you stored alongside it is the repair"),
    "invalid_refresh_token": ("reinstall",
                              "the refresh token was replayed or expired. The "
                              "rotation pair is unrecoverable"),
    "invalid_auth": ("credential",
                     "the string does not authenticate at all. Check what was "
                     "stored before concluding anything about the install"),
    "not_authed": ("credential", "no token was sent on the request"),
    "not_allowed_token_type": ("credential",
                               "this token class cannot call this method. An "
                               "app-level xapp- token in a bot token's variable "
                               "looks exactly like this"),
    "ratelimited": ("wait", "throttled, not broken. Retry after the window"),
}

# The only errors where retrying the same call unchanged is the right move.
# token_expired is deliberately absent: it is retryable, but only after a
# refresh, and a bare retry burns the window without fixing anything.
RETRYABLE = {"ratelimited", "internal_error", "service_unavailable",
             "fatal_error", "request_timeout"}


def disposition(error):
    """Map an auth.test error to the job it implies. Pure."""
    if not error:
        return ("none", "the token authenticates")
    if error in DISPOSITIONS:
        return DISPOSITIONS[error]
    return ("investigate",
            "error=%s is not in the disposition table. Read it before deciding "
            "whether the row is dead" % error)


def is_retryable(error):
    """Whether retrying this exact call unchanged can ever succeed. Pure."""
    return error in RETRYABLE


def parse_ts(text):
    """Accept the two timestamp shapes an installation store actually holds."""
    if not text:
        return None
    try:
        return datetime.strptime(str(text)[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(str(text)[:10], "%Y-%m-%d")
    except ValueError:
        return None


def reconcile(row, body, now):
    """Compare what the store believes about a row against what Slack says. Pure.

    `row` is the installation record including its own status; `body` is the
    parsed auth.test response for that row's token. The two findings are
    symmetric and a cleanup that only looks for the first eventually creates
    the second.
    """
    active = str(row.get("status", "active")).lower() not in ("disabled", "revoked",
                                                              "dead", "tombstoned")
    ok = body.get("ok") is True
    error = body.get("error")

    if ok and active:
        return ("serving", "team %s authenticates and the row is active"
                % (body.get("team_id") or "?"))
    if ok and not active:
        return ("live-but-disabled",
                "the token still authenticates for team %s and the row is marked "
                "%r. This workspace is installed and you stopped serving it."
                % (body.get("team_id") or "?", row.get("status")))
    if not ok and not active:
        return ("already-tombstoned",
                "error=%s and the row is marked %r. Dead, and your store knows."
                % (error, row.get("status")))

    action, why = disposition(error)
    last = parse_ts(row.get("last_ok"))
    idle = ""
    if last:
        idle = " Nothing has succeeded on this row for %d day(s)." % (now - last).days
    return ("dead-but-active",
            "error=%s -> %s: %s.%s" % (error, action, why, idle))


def revocation_shape(entries):
    """Read the pattern of dead tokens across each workspace. Pure.

    `entries` is a list of {"team", "role", "dead"}. Which token died says what
    happened: both is an app removal, the user token alone is one person
    revoking their own authorisation, and the bot token alone is strange.
    """
    by_team = {}
    for e in entries:
        by_team.setdefault(e.get("team"), []).append(e)
    out = []
    for team in sorted(by_team, key=lambda t: str(t)):
        rows = by_team[team]
        dead = {r.get("role") for r in rows if r.get("dead")}
        alive = {r.get("role") for r in rows if not r.get("dead")}
        if not dead:
            out.append((team, "healthy", "every stored token authenticates"))
        elif not alive:
            out.append((team, "app-removed",
                        "every token for this workspace is dead, which is what an "
                        "uninstall looks like from here"))
        elif dead == {"user"}:
            out.append((team, "user-grant-revoked",
                        "the user token is dead and the bot token is not. One "
                        "person revoked their own authorisation; the app is still "
                        "installed"))
        elif dead == {"bot"}:
            out.append((team, "bot-token-only-dead",
                        "the bot token is dead while a user token still works. "
                        "Unusual enough to look at by hand before deleting"))
        else:
            out.append((team, "mixed", "dead: %s, alive: %s"
                        % (", ".join(sorted(dead)), ", ".join(sorted(alive)))))
    return out


def auth_test(session, token):
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def load_rows(path):
    if path:
        return json.loads(open(path, encoding="utf-8").read())
    return [{"key": "<the only row>", "token_env": "SLACK_BOT_TOKEN", "role": "bot"}]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", help="JSON array of installation rows; each row needs "
                                    "key and token_env, plus status, role and last_ok "
                                    "if you keep them")
    args = ap.parse_args()

    if not args.store and not os.environ.get("SLACK_BOT_TOKEN"):
        log.error("set SLACK_BOT_TOKEN, or pass --store with one token_env per row")
        return 2

    rows = load_rows(args.store)
    s = requests.Session()
    now = datetime.utcnow()

    entries = []
    dead_active = 0
    live_disabled = 0
    for row in rows:
        token = os.environ.get(row.get("token_env") or "SLACK_BOT_TOKEN")
        if not token:
            log.warning("%-19s %-16s row names %s and it is unset", "no-token",
                        row.get("key"), row.get("token_env"))
            continue
        body = auth_test(s, token)
        state, detail = reconcile(row, body, now)
        line = "%-19s %-16s %s" % (state, row.get("key"), detail)
        if state in ("serving", "already-tombstoned"):
            log.info(line)
        else:
            log.warning(line)
            if state == "dead-but-active":
                dead_active += 1
                if not is_retryable(body.get("error")):
                    log.warning("  repair: stop scheduling this row. Retrying this "
                                "error unchanged can never succeed")
            else:
                live_disabled += 1
                log.warning("  repair: this row was disabled by something that did "
                            "not read the error code. Re-enable it")
        entries.append({"team": body.get("team_id") or row.get("key"),
                        "role": row.get("role") or "bot",
                        "dead": body.get("ok") is not True})

    for team, shape, why in revocation_shape(entries):
        log.info("%-19s %-16s %s", shape, team, why)

    if dead_active:
        log.warning("  repair: tombstone the revoked rows rather than deleting them, "
                    "and handle app_uninstalled and tokens_revoked in the same code "
                    "path so the store self-heals")

    log.info("%d row(s) swept, %d dead but active, %d live but disabled",
             len(rows), dead_active, live_disabled)
    return 1 if (dead_active or live_disabled) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-dead-install-sweep.mjs",
"js": '''/**
 * Sweep a Slack installation store for dead tokens and sort them by disposition.
 *
 * Read only. One GET per stored token and nothing else: this script is handed
 * every tenant's credential at once, so it reports what it found and prints the
 * cleanup for a human to run.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// What should happen to a row, keyed by the error auth.test returned. A
// disposition table, not a severity scale: these codes are all "auth failed"
// and no two of them want the same treatment.
export const DISPOSITIONS = {
  token_revoked: ['tombstone',
    'the authorisation no longer exists. Only a fresh OAuth install produces a ' +
    'working token for this workspace, and that is a customer action'],
  account_inactive: ['migrate',
    'a user token whose human was deactivated. The app is still installed; the ' +
    'person is gone'],
  token_expired: ['refresh',
    'a rotated token past its 12 hour life. The refresh token you stored ' +
    'alongside it is the repair'],
  invalid_refresh_token: ['reinstall',
    'the refresh token was replayed or expired. The rotation pair is unrecoverable'],
  invalid_auth: ['credential',
    'the string does not authenticate at all. Check what was stored before ' +
    'concluding anything about the install'],
  not_authed: ['credential', 'no token was sent on the request'],
  not_allowed_token_type: ['credential',
    'this token class cannot call this method. An app-level xapp- token in a bot ' +
    "token's variable looks exactly like this"],
  ratelimited: ['wait', 'throttled, not broken. Retry after the window'],
};

// The only errors where retrying the same call unchanged is the right move.
// token_expired is deliberately absent: it is retryable, but only after a
// refresh, and a bare retry burns the window without fixing anything.
export const RETRYABLE = new Set(['ratelimited', 'internal_error',
  'service_unavailable', 'fatal_error', 'request_timeout']);

/** Map an auth.test error to the job it implies. Pure. */
export function disposition(error) {
  if (!error) return ['none', 'the token authenticates'];
  if (Object.prototype.hasOwnProperty.call(DISPOSITIONS, error)) return DISPOSITIONS[error];
  return ['investigate',
    `error=${error} is not in the disposition table. Read it before deciding ` +
    'whether the row is dead'];
}

/** Whether retrying this exact call unchanged can ever succeed. Pure. */
export function isRetryable(error) {
  return RETRYABLE.has(error);
}

/** Accept the two timestamp shapes an installation store actually holds. */
export function parseTs(text) {
  if (!text) return null;
  const d = new Date(text);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Compare what the store believes about a row against what Slack says. Pure.
 * The two findings are symmetric, and a cleanup that only looks for the first
 * eventually creates the second.
 */
export function reconcile(row, body, now) {
  const status = String(row.status ?? 'active').toLowerCase();
  const active = !['disabled', 'revoked', 'dead', 'tombstoned'].includes(status);
  const ok = body?.ok === true;
  const error = body?.error;

  if (ok && active) {
    return ['serving', `team ${body.team_id ?? '?'} authenticates and the row is active`];
  }
  if (ok && !active) {
    return ['live-but-disabled',
      `the token still authenticates for team ${body.team_id ?? '?'} and the row ` +
      `is marked ${JSON.stringify(row.status)}. This workspace is installed and ` +
      'you stopped serving it.'];
  }
  if (!ok && !active) {
    return ['already-tombstoned',
      `error=${error} and the row is marked ${JSON.stringify(row.status)}. Dead, ` +
      'and your store knows.'];
  }

  const [action, why] = disposition(error);
  const last = parseTs(row.last_ok);
  let idle = '';
  if (last) {
    const days = Math.floor((now.getTime() - last.getTime()) / 86400000);
    idle = ` Nothing has succeeded on this row for ${days} day(s).`;
  }
  return ['dead-but-active', `error=${error} -> ${action}: ${why}.${idle}`];
}

/**
 * Read the pattern of dead tokens across each workspace. Pure.
 * `entries` is a list of { team, role, dead }.
 */
export function revocationShape(entries) {
  const byTeam = new Map();
  for (const e of entries) {
    const key = e.team;
    if (!byTeam.has(key)) byTeam.set(key, []);
    byTeam.get(key).push(e);
  }
  const out = [];
  for (const team of [...byTeam.keys()].sort((a, b) => String(a).localeCompare(String(b)))) {
    const rows = byTeam.get(team);
    const dead = [...new Set(rows.filter((r) => r.dead).map((r) => r.role))].sort();
    const alive = [...new Set(rows.filter((r) => !r.dead).map((r) => r.role))].sort();
    if (dead.length === 0) {
      out.push([team, 'healthy', 'every stored token authenticates']);
    } else if (alive.length === 0) {
      out.push([team, 'app-removed',
        'every token for this workspace is dead, which is what an uninstall looks ' +
        'like from here']);
    } else if (dead.length === 1 && dead[0] === 'user') {
      out.push([team, 'user-grant-revoked',
        'the user token is dead and the bot token is not. One person revoked their ' +
        'own authorisation; the app is still installed']);
    } else if (dead.length === 1 && dead[0] === 'bot') {
      out.push([team, 'bot-token-only-dead',
        'the bot token is dead while a user token still works. Unusual enough to ' +
        'look at by hand before deleting']);
    } else {
      out.push([team, 'mixed', `dead: ${dead.join(', ')}, alive: ${alive.join(', ')}`]);
    }
  }
  return out;
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
  return [{ key: '<the only row>', token_env: 'SLACK_BOT_TOKEN', role: 'bot' }];
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
  const now = new Date();
  const entries = [];
  let deadActive = 0;
  let liveDisabled = 0;

  for (const row of rows) {
    const token = process.env[row.token_env ?? 'SLACK_BOT_TOKEN'];
    if (!token) {
      console.warn(`${'no-token'.padEnd(19)} ${String(row.key).padEnd(16)} row names ` +
        `${row.token_env} and it is unset`);
      continue;
    }
    const body = await authTest(token);
    const [state, detail] = reconcile(row, body, now);
    const line = `${state.padEnd(19)} ${String(row.key).padEnd(16)} ${detail}`;
    if (state === 'serving' || state === 'already-tombstoned') {
      console.log(line);
    } else {
      console.warn(line);
      if (state === 'dead-but-active') {
        deadActive += 1;
        if (!isRetryable(body?.error)) {
          console.warn('  repair: stop scheduling this row. Retrying this error ' +
            'unchanged can never succeed');
        }
      } else {
        liveDisabled += 1;
        console.warn('  repair: this row was disabled by something that did not read ' +
          'the error code. Re-enable it');
      }
    }
    entries.push({
      team: body?.team_id ?? row.key,
      role: row.role ?? 'bot',
      dead: body?.ok !== true,
    });
  }

  for (const [team, shape, why] of revocationShape(entries)) {
    console.log(`${shape.padEnd(19)} ${String(team).padEnd(16)} ${why}`);
  }

  if (deadActive) {
    console.warn('  repair: tombstone the revoked rows rather than deleting them, and ' +
      'handle app_uninstalled and tokens_revoked in the same code path so the store ' +
      'self-heals');
  }

  console.log(`${rows.length} row(s) swept, ${deadActive} dead but active, ` +
    `${liveDisabled} live but disabled`);
  process.exitCode = deadActive || liveDisabled ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. A revoked token must never be classed as retryable, or the scheduler spends a quarter rediscovering that an uninstalled app is still uninstalled. And a live token in a row somebody disabled must be reported as loudly as a dead one, because that finding is a paying customer nobody is serving and it produces no errors at all.",
"test_py_file": "test_slack_dead_install_sweep.py",
"test_py": '''from datetime import datetime

from slack_dead_install_sweep import (disposition, is_retryable, reconcile,
                                      revocation_shape)

NOW = datetime(2026, 8, 30)


def test_revoked_is_a_tombstone_and_never_retryable():
    action, why = disposition("token_revoked")
    assert action == "tombstone"
    assert "fresh OAuth install" in why
    assert is_retryable("token_revoked") is False


def test_expired_wants_a_refresh_not_a_bare_retry():
    assert disposition("token_expired")[0] == "refresh"
    assert is_retryable("token_expired") is False


def test_ratelimited_is_the_one_that_should_be_retried():
    assert disposition("ratelimited")[0] == "wait"
    assert is_retryable("ratelimited") is True


def test_unknown_error_is_investigated_rather_than_deleted():
    action, why = disposition("something_new")
    assert action == "investigate"
    assert "something_new" in why


def test_dead_token_in_an_active_row_is_the_finding():
    row = {"key": "T1", "status": "active", "last_ok": "2026-06-01T00:00:00Z"}
    state, detail = reconcile(row, {"ok": False, "error": "token_revoked"}, NOW)
    assert state == "dead-but-active"
    assert "90 day(s)" in detail


def test_live_token_in_a_disabled_row_is_the_mirror_finding():
    row = {"key": "T1", "status": "disabled"}
    state, detail = reconcile(row, {"ok": True, "team_id": "T1"}, NOW)
    assert state == "live-but-disabled"
    assert "stopped serving it" in detail


def test_dead_token_already_tombstoned_is_not_a_finding():
    row = {"key": "T1", "status": "tombstoned"}
    assert reconcile(row, {"ok": False, "error": "token_revoked"}, NOW)[0] == "already-tombstoned"


def test_healthy_row_is_quiet():
    assert reconcile({"key": "T1"}, {"ok": True, "team_id": "T1"}, NOW)[0] == "serving"


def test_both_tokens_dead_reads_as_an_app_removal():
    shapes = revocation_shape([{"team": "T1", "role": "bot", "dead": True},
                               {"team": "T1", "role": "user", "dead": True}])
    assert shapes[0][1] == "app-removed"


def test_only_the_user_token_dead_is_one_person_revoking():
    shapes = revocation_shape([{"team": "T1", "role": "bot", "dead": False},
                               {"team": "T1", "role": "user", "dead": True}])
    assert shapes[0][1] == "user-grant-revoked"
    assert "still installed" in shapes[0][2]
''',
"test_js_file": "slack-dead-install-sweep.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { disposition, isRetryable, reconcile, revocationShape } from './slack-dead-install-sweep.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');

test('revoked is a tombstone and never retryable', () => {
  const [action, why] = disposition('token_revoked');
  assert.equal(action, 'tombstone');
  assert.match(why, /fresh OAuth install/);
  assert.equal(isRetryable('token_revoked'), false);
});

test('expired wants a refresh not a bare retry', () => {
  assert.equal(disposition('token_expired')[0], 'refresh');
  assert.equal(isRetryable('token_expired'), false);
});

test('ratelimited is the one that should be retried', () => {
  assert.equal(disposition('ratelimited')[0], 'wait');
  assert.equal(isRetryable('ratelimited'), true);
});

test('unknown error is investigated rather than deleted', () => {
  const [action, why] = disposition('something_new');
  assert.equal(action, 'investigate');
  assert.match(why, /something_new/);
});

test('dead token in an active row is the finding', () => {
  const [state, detail] = reconcile(
    { key: 'T1', status: 'active', last_ok: '2026-06-01T00:00:00Z' },
    { ok: false, error: 'token_revoked' }, NOW,
  );
  assert.equal(state, 'dead-but-active');
  assert.match(detail, /90 day\\(s\\)/);
});

test('live token in a disabled row is the mirror finding', () => {
  const [state, detail] = reconcile(
    { key: 'T1', status: 'disabled' }, { ok: true, team_id: 'T1' }, NOW,
  );
  assert.equal(state, 'live-but-disabled');
  assert.match(detail, /stopped serving it/);
});

test('dead token already tombstoned is not a finding', () => {
  assert.equal(reconcile({ key: 'T1', status: 'tombstoned' },
    { ok: false, error: 'token_revoked' }, NOW)[0], 'already-tombstoned');
});

test('healthy row is quiet', () => {
  assert.equal(reconcile({ key: 'T1' }, { ok: true, team_id: 'T1' }, NOW)[0], 'serving');
});

test('both tokens dead reads as an app removal', () => {
  const shapes = revocationShape([
    { team: 'T1', role: 'bot', dead: true },
    { team: 'T1', role: 'user', dead: true },
  ]);
  assert.equal(shapes[0][1], 'app-removed');
});

test('only the user token dead is one person revoking', () => {
  const shapes = revocationShape([
    { team: 'T1', role: 'bot', dead: false },
    { team: 'T1', role: 'user', dead: true },
  ]);
  assert.equal(shapes[0][1], 'user-grant-revoked');
  assert.match(shapes[0][2], /still installed/);
});
''',
"faq": [
 ("Can a revoked token ever start working again?",
  "No. Revocation destroys the authorisation, not just the string, so there is nothing for a retry to recover. A workspace comes back only by installing the app again, which mints an entirely new token. Any backoff schedule pointed at a token_revoked row is spending requests to re-learn a permanent fact."),
 ("Should I delete the installation row or keep it?",
  "Keep it as a tombstone. A deleted row loses the history that says this workspace was once a customer, and a reinstall then arrives as a brand new install with no continuity. Mark it dead, stop scheduling work against it, and let a fresh OAuth callback flip it back to active."),
 ("Why did I not receive app_uninstalled?",
  "Either the app never subscribed to it, or the event was delivered while the handler was down and Slack's retries were exhausted. It is also worth checking whether event delivery for the app was disabled entirely, which is a separate failure that silences every event rather than one."),
 ("How do I tell token_revoked apart from account_inactive?",
  "By the error string, and they mean different things. token_revoked means the grant is gone, usually because the app was removed. account_inactive means the app is still installed but the human that a user token belongs to was deactivated. The first needs a tombstone, the second needs a bot token."),
 ("Is one failed auth.test enough to tombstone a row?",
  "Only when the body names a terminal error. A transport failure, a timeout, or a 429 says nothing about the grant, which is why the sweep reads body.error rather than catching whatever the HTTP client threw. Anything not in the disposition table is reported for a human rather than acted on."),
],
"related": [
 ("/slack/account-inactive/", "account_inactive is the installer, not the app"),
 ("/slack/enterprise-id-not-stored/", "installs keyed on team_id alone collide"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_AUTH_TEST, CITE_TOKENS_REVOKED, CITE_APP_UNINSTALLED, CITE_INSTALL],
},

{
"slug": "account-inactive",
"title": "account_inactive: the installer left and took the token",
"description": "A user token dies with its human. Join your install rows against the member directory to find the automations that are one offboarding away from stopping.",
"h1": "account_inactive: the installer left and took the token",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack account_inactive", "slack user token deactivated user",
             "authed_user id offboarding", "slack bot token vs user token lifecycle",
             "users.info deleted true"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the directory half needs users:read",
"lead": "The nightly export ran for two years and stopped on a Tuesday. Nothing was deployed, no scope changed, the app is still listed in the workspace. The error is <code>{\"ok\": false, \"error\": \"account_inactive\"}</code>, and the explanation is in the HR system rather than yours: the engineer who installed the app in 2024 left the company on Monday, and SSO deprovisioning deactivated her account overnight.",
"short_answer": """<p>Two questions, and the second is the one worth running. First, <code>auth.test</code> per stored token: <code>account_inactive</code> means the human behind a user token was deactivated and that automation is already down. Second, and before anything breaks: take the <code>authed_user.id</code> you persisted at install, look each one up in the member directory, and find every automation that is currently standing on one employee.</p>
<p>The repair is a token class, not a token. Move the work to a bot token, which survives the installer's departure entirely. Where a user token is genuinely required &mdash; message search, acting as a person &mdash; install from a service account that offboarding does not touch, and watch its <code>deleted</code> flag.</p>""",
"problem": """<p>A user token is a credential issued to a person. It carries their identity, sees what they can see, and is cancelled when their account is. That is correct behaviour and it is precisely what makes it the wrong credential for a job that has to run every night for three years. The failure is not gradual: the account is deactivated at 02:00 and the integration is dead at 02:01, with no warning and no window in which anything could have been renewed.</p>
<p>Almost nobody chooses this on purpose. A user token gets adopted because one call needed a user scope, or because the OAuth response's first token was the one that got stored, or because the app was set up during a hackathon by whoever happened to be at the keyboard. From that moment the integration has an undocumented dependency on one employee remaining employed, recorded nowhere except in an <code>authed_user.id</code> field that most stores do not even keep.</p>
<p>And the app looks installed the whole time, because it is. Nobody removed it. The workspace admin's <strong>Manage apps</strong> page shows it present and healthy, which is why the first hour of the investigation is usually spent looking at the app configuration &mdash; the one place where nothing is wrong.</p>""",
"why": """<p><strong>Bot tokens are immune and that is the point of them.</strong> A <code>xoxb-</code> token belongs to the app, not to a person. It survives the installer leaving, changing teams, or losing their laptop. Slack's own guidance is to use it for anything that must outlive an individual, and this error is the sharpest illustration of why.</p>
<p><strong>The identity you need was in the install response and probably discarded.</strong> <code>authed_user.id</code> is the id of the human whose token you are holding. Without it you cannot ask whether they are still here; you find out when the automation stops. Persisting it costs one column and converts this failure into something a scheduled read can see coming.</p>
<p><strong>A deactivated member is visible before the token fails.</strong> <code>users.list</code> and <code>users.info</code> report <code>deleted: true</code> for deactivated accounts, so a join between your install rows and the member directory produces a risk register: which automations depend on which humans, and which of those humans have already gone.</p>
<p><strong>Guests go first.</strong> <code>is_restricted</code> and <code>is_ultra_restricted</code> mark multi-channel and single-channel guests, and guest accounts are typically deprovisioned soonest and most abruptly. An install standing on a guest account is the highest-risk row in the register.</p>
<p><strong>The id in your row and the id on the token can disagree.</strong> If a row records one installer and <code>auth.test</code> reports a different <code>user_id</code>, you are monitoring the wrong person: the token was replaced at some point and the row was not. That row is unmonitored even though it looks monitored, which is worse than not having the column.</p>""",
"steps": [
 {"h": "Persist the installer id, if you have not already",
  "body": """<p>The audit needs <code>authed_user.id</code> per row. If your store never kept it, the script recovers it from <code>auth.test</code> and tells you to write it down &mdash; recovery works only while the token still authenticates, which is exactly the window this note is about.</p>"""},
 {"h": "Ask each token whether it still works, and what it is",
  "body": """<p><code>auth.test</code> answers both at once. <code>account_inactive</code> means already broken. A successful response carrying <code>bot_id</code> means a bot token, which has no exposure here at all and should be reported as such rather than filling the output with rows that cannot fail this way.</p>"""},
 {"h": "Read the member directory once",
  "body": """<p>One paginated pass over <code>users.list?limit=200</code> with a token holding <code>users:read</code>, following <code>response_metadata.next_cursor</code> to the end. One sweep is cheaper and kinder to the rate limiter than a <code>users.info</code> per install, and it also lets you count how much of the workspace is deactivated.</p>"""},
 {"h": "Join the installers against the directory",
  "body": """<p>For each user token, look up its installer. Deleted means the automation is down or about to be. A guest account means it is fragile. An id that is not in the directory at all usually means the person has been removed entirely, or that the row belongs to a different workspace on the same Grid org.</p>"""},
 {"h": "Check that the row names the human the token actually belongs to",
  "body": """<p>Compare the recorded installer against the <code>user_id</code> in the <code>auth.test</code> response. A mismatch means the token was swapped without updating the row, so your monitoring has been watching somebody who has nothing to do with this credential.</p>"""},
 {"h": "Move the work to a bot token, or to a service account",
  "body": """<p>The printed repair is the same one Slack gives: reinstall with the equivalent bot scopes and use <code>xoxb-</code>. Where a user token is unavoidable, install from a documented service account that offboarding does not touch, and keep watching its <code>deleted</code> flag &mdash; a service account can be deactivated too, usually during a licence audit.</p>"""},
],
"verify": """<p>After migrating, re-run. Every row should report a bot token, or a user token whose installer is a live, non-guest service account.</p>
<pre><code class="language-bash">python3 slack_installer_account_watch.py --store installs.json
# bot-token          exports    bot token: no dependency on any human account
# 6 row(s) checked, 0 already broken, 0 standing on a live human</code></pre>""",
"code_intro": "Two kinds of GET: one <code>auth.test</code> per stored token, and one paginated <code>users.list</code> sweep to build the directory. Nothing is written, and nothing about a person is changed &mdash; the script only reads whether an account is still active. Two pure functions do the work: <code>directory</code> turns a <code>users.list</code> page set into a lookup, and <code>exposure</code> decides what one install row is standing on.",
"py_file": "slack_installer_account_watch.py",
"py": '''"""Find Slack installs whose token depends on one human account still existing.

Read only. GET requests and nothing else: this script reads whether people are
still active, which is about as sensitive as workspace data gets, so it reports
and prints the repair rather than performing anything.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_installer_account_watch")

API = "https://slack.com/api/"


def directory(members):
    """Turn users.list members into an id -> record lookup. Pure.

    Keeps only the four fields the audit reasons about, so the register that
    comes out of this script is not a copy of the member list.
    """
    out = {}
    for m in members or []:
        uid = m.get("id")
        if not uid:
            continue
        out[uid] = {
            "name": m.get("name") or m.get("real_name") or uid,
            "deleted": m.get("deleted") is True,
            "is_bot": m.get("is_bot") is True,
            "guest": bool(m.get("is_restricted") or m.get("is_ultra_restricted")),
        }
    return out


def exposure(row, identity, people):
    """What is this installation standing on. Pure.

    `row` is the stored installation record, `identity` the parsed auth.test
    body for its token, `people` the directory lookup. The states are ordered so
    that "already broken" is reported before "will break", and a bot token is
    dismissed before any of the human reasoning runs.
    """
    if identity.get("ok") is not True:
        error = identity.get("error")
        if error == "account_inactive":
            return ("already-broken",
                    "account_inactive: this is a user token and its human was "
                    "deactivated. The app is still installed; the person is not.")
        return ("other-failure",
                "error=%s, which is not this failure. A revoked token or an "
                "expired rotated one looks similar in a log line and wants a "
                "different repair." % (error or "<no error field>"))

    if identity.get("bot_id"):
        return ("bot-token",
                "bot token: no dependency on any human account. This row cannot "
                "fail the way the others can.")

    live_id = identity.get("user_id")
    stored_id = row.get("installer")
    if not stored_id:
        return ("installer-not-recorded",
                "a working user token and no authed_user id in the row. It "
                "belongs to %s, recoverable only while the token still works: "
                "persist it now." % live_id)
    if stored_id != live_id:
        return ("installer-id-drift",
                "the row names %s and the token belongs to %s. Whatever you are "
                "monitoring, it is not this credential." % (stored_id, live_id))

    person = people.get(live_id)
    if person is None:
        return ("installer-not-in-directory",
                "%s holds a working token and is not in this workspace's member "
                "list. Usually a removed account, or a row belonging to a "
                "different workspace in the same org." % live_id)
    if person["deleted"]:
        return ("directory-disagrees",
                "%s is marked deleted and the token still authenticates. Read "
                "this by hand before acting on it." % person["name"])
    if person["guest"]:
        return ("guest-installer",
                "%s is a guest account. Guests are deprovisioned soonest and "
                "most abruptly, which makes this the most fragile row here."
                % person["name"])
    return ("standing-on-a-human",
            "user token belonging to %s, who is active today. This automation "
            "stops on their last day." % person["name"])


def get(session, token, method, params=None):
    r = session.get(API + method, params=params or {},
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def read_directory(session, token):
    """One paginated users.list sweep. Cheaper than users.info per install."""
    members, cursor = [], ""
    while True:
        body = get(session, token, "users.list",
                   {"limit": "200", "cursor": cursor} if cursor else {"limit": "200"})
        if body.get("ok") is not True:
            return None, body.get("error")
        members.extend(body.get("members") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return members, None


def load_rows(path):
    if path:
        return json.loads(open(path, encoding="utf-8").read())
    return [{"key": "<the only row>", "token_env": "SLACK_BOT_TOKEN",
             "installer": os.environ.get("SLACK_INSTALLER_ID")}]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", help="JSON array of installation rows; each row needs "
                                    "key and token_env, and installer if you kept it")
    ap.add_argument("--directory-token-env", default="SLACK_BOT_TOKEN",
                    help="env var holding a users:read token for the member sweep")
    args = ap.parse_args()

    rows = load_rows(args.store)
    s = requests.Session()

    people = {}
    dir_token = os.environ.get(args.directory_token_env)
    if dir_token:
        members, err = read_directory(s, dir_token)
        if members is None:
            log.warning("%-26s users.list refused: %s. The directory half of this "
                        "audit is unavailable and rows will be reported on liveness "
                        "alone.", "directory-unavailable", err)
        else:
            people = directory(members)
            gone = sum(1 for p in people.values() if p["deleted"])
            log.info("%-26s %d member(s), %d deactivated", "directory", len(people), gone)
    else:
        log.warning("%-26s %s is unset, so installers cannot be looked up",
                    "directory-unavailable", args.directory_token_env)

    broken = 0
    at_risk = 0
    for row in rows:
        token = os.environ.get(row.get("token_env") or "SLACK_BOT_TOKEN")
        if not token:
            log.warning("%-26s %-12s row names %s and it is unset", "no-token",
                        row.get("key"), row.get("token_env"))
            continue
        identity = get(s, token, "auth.test")
        state, detail = exposure(row, identity, people)
        line = "%-26s %-12s %s" % (state, row.get("key"), detail)
        if state == "bot-token":
            log.info(line)
            continue
        log.warning(line)
        if state == "already-broken":
            broken += 1
        elif state in ("standing-on-a-human", "guest-installer",
                       "installer-not-in-directory"):
            at_risk += 1
        if state in ("already-broken", "standing-on-a-human", "guest-installer"):
            log.warning("  repair: reinstall with the equivalent bot scopes and use "
                        "the xoxb- token, or install from a documented service "
                        "account that offboarding does not touch")

    log.info("%d row(s) checked, %d already broken, %d standing on a live human",
             len(rows), broken, at_risk)
    return 1 if (broken or at_risk) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-installer-account-watch.mjs",
"js": '''/**
 * Find Slack installs whose token depends on one human account still existing.
 *
 * Read only. GET requests and nothing else: this script reads whether people
 * are still active, which is about as sensitive as workspace data gets, so it
 * reports and prints the repair rather than performing anything.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

/**
 * Turn users.list members into an id -> record lookup. Pure. Keeps only the
 * four fields the audit reasons about, so the register that comes out of this
 * script is not a copy of the member list.
 */
export function directory(members) {
  const out = new Map();
  for (const m of members ?? []) {
    if (!m?.id) continue;
    out.set(m.id, {
      name: m.name || m.real_name || m.id,
      deleted: m.deleted === true,
      is_bot: m.is_bot === true,
      guest: Boolean(m.is_restricted || m.is_ultra_restricted),
    });
  }
  return out;
}

/**
 * What is this installation standing on. Pure. The states are ordered so that
 * "already broken" is reported before "will break", and a bot token is
 * dismissed before any of the human reasoning runs.
 */
export function exposure(row, identity, people) {
  if (identity?.ok !== true) {
    const error = identity?.error;
    if (error === 'account_inactive') {
      return ['already-broken',
        'account_inactive: this is a user token and its human was deactivated. ' +
        'The app is still installed; the person is not.'];
    }
    return ['other-failure',
      `error=${error ?? '<no error field>'}, which is not this failure. A revoked ` +
      'token or an expired rotated one looks similar in a log line and wants a ' +
      'different repair.'];
  }

  if (identity.bot_id) {
    return ['bot-token',
      'bot token: no dependency on any human account. This row cannot fail the ' +
      'way the others can.'];
  }

  const liveId = identity.user_id;
  const storedId = row.installer;
  if (!storedId) {
    return ['installer-not-recorded',
      'a working user token and no authed_user id in the row. It belongs to ' +
      `${liveId}, recoverable only while the token still works: persist it now.`];
  }
  if (storedId !== liveId) {
    return ['installer-id-drift',
      `the row names ${storedId} and the token belongs to ${liveId}. Whatever you ` +
      'are monitoring, it is not this credential.'];
  }

  const person = people.get(liveId);
  if (person === undefined) {
    return ['installer-not-in-directory',
      `${liveId} holds a working token and is not in this workspace's member list. ` +
      'Usually a removed account, or a row belonging to a different workspace in ' +
      'the same org.'];
  }
  if (person.deleted) {
    return ['directory-disagrees',
      `${person.name} is marked deleted and the token still authenticates. Read ` +
      'this by hand before acting on it.'];
  }
  if (person.guest) {
    return ['guest-installer',
      `${person.name} is a guest account. Guests are deprovisioned soonest and most ` +
      'abruptly, which makes this the most fragile row here.'];
  }
  return ['standing-on-a-human',
    `user token belonging to ${person.name}, who is active today. This automation ` +
    'stops on their last day.'];
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

/** One paginated users.list sweep. Cheaper than users.info per install. */
async function readDirectory(token) {
  const members = [];
  let cursor = '';
  for (;;) {
    const params = cursor ? { limit: '200', cursor } : { limit: '200' };
    const body = await get(token, 'users.list', params);
    if (body?.ok !== true) return [null, body?.error];
    members.push(...(body.members ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return [members, null];
  }
}

async function loadRows(path) {
  if (path) return JSON.parse(await readFile(path, 'utf8'));
  return [{ key: '<the only row>', token_env: 'SLACK_BOT_TOKEN',
    installer: process.env.SLACK_INSTALLER_ID }];
}

async function main() {
  const args = process.argv.slice(2);
  const si = args.indexOf('--store');
  const store = si === -1 ? null : args[si + 1];
  const di = args.indexOf('--directory-token-env');
  const dirEnv = di === -1 ? 'SLACK_BOT_TOKEN' : args[di + 1];

  const rows = await loadRows(store);
  let people = new Map();

  const dirToken = process.env[dirEnv];
  if (dirToken) {
    const [members, err] = await readDirectory(dirToken);
    if (members === null) {
      console.warn(`${'directory-unavailable'.padEnd(26)} users.list refused: ${err}. ` +
        'The directory half of this audit is unavailable and rows will be reported ' +
        'on liveness alone.');
    } else {
      people = directory(members);
      const gone = [...people.values()].filter((p) => p.deleted).length;
      console.log(`${'directory'.padEnd(26)} ${people.size} member(s), ${gone} deactivated`);
    }
  } else {
    console.warn(`${'directory-unavailable'.padEnd(26)} ${dirEnv} is unset, so ` +
      'installers cannot be looked up');
  }

  let broken = 0;
  let atRisk = 0;
  for (const row of rows) {
    const token = process.env[row.token_env ?? 'SLACK_BOT_TOKEN'];
    if (!token) {
      console.warn(`${'no-token'.padEnd(26)} ${String(row.key).padEnd(12)} row names ` +
        `${row.token_env} and it is unset`);
      continue;
    }
    const identity = await get(token, 'auth.test');
    const [state, detail] = exposure(row, identity, people);
    const line = `${state.padEnd(26)} ${String(row.key).padEnd(12)} ${detail}`;
    if (state === 'bot-token') {
      console.log(line);
      continue;
    }
    console.warn(line);
    if (state === 'already-broken') broken += 1;
    else if (['standing-on-a-human', 'guest-installer',
      'installer-not-in-directory'].includes(state)) atRisk += 1;
    if (['already-broken', 'standing-on-a-human', 'guest-installer'].includes(state)) {
      console.warn('  repair: reinstall with the equivalent bot scopes and use the ' +
        'xoxb- token, or install from a documented service account that offboarding ' +
        'does not touch');
    }
  }

  console.log(`${rows.length} row(s) checked, ${broken} already broken, ` +
    `${atRisk} standing on a live human`);
  process.exitCode = broken || atRisk ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The row the tests exist for is the one that is working perfectly: a user token whose installer is present, active and employed. It must be reported, because it is the whole point of running the audit before the offboarding rather than after it &mdash; and the bot token beside it must not be, or the register fills up with rows that cannot fail this way and nobody reads it twice.",
"test_py_file": "test_slack_installer_account_watch.py",
"test_py": '''from slack_installer_account_watch import directory, exposure

PEOPLE = directory([
    {"id": "U_LIVE", "name": "dana", "deleted": False},
    {"id": "U_GONE", "name": "sam", "deleted": True},
    {"id": "U_GUEST", "name": "vendor", "deleted": False, "is_restricted": True},
])


def test_directory_keeps_only_what_the_audit_reasons_about():
    assert PEOPLE["U_GUEST"] == {"name": "vendor", "deleted": False,
                                 "is_bot": False, "guest": True}
    assert "U_MISSING" not in PEOPLE


def test_account_inactive_is_the_already_broken_state():
    state, detail = exposure({"key": "T1", "installer": "U_GONE"},
                             {"ok": False, "error": "account_inactive"}, PEOPLE)
    assert state == "already-broken"
    assert "still installed" in detail


def test_a_revoked_token_is_not_this_failure():
    state, detail = exposure({"key": "T1"}, {"ok": False, "error": "token_revoked"}, PEOPLE)
    assert state == "other-failure"
    assert "token_revoked" in detail


def test_bot_token_has_no_exposure_at_all():
    state, detail = exposure({"key": "T1"},
                             {"ok": True, "user_id": "U_BOT", "bot_id": "B1"}, PEOPLE)
    assert state == "bot-token"
    assert "no dependency on any human" in detail


def test_live_installer_is_reported_before_anything_breaks():
    state, detail = exposure({"key": "T1", "installer": "U_LIVE"},
                             {"ok": True, "user_id": "U_LIVE"}, PEOPLE)
    assert state == "standing-on-a-human"
    assert "their last day" in detail


def test_guest_installer_is_the_most_fragile_row():
    state, detail = exposure({"key": "T1", "installer": "U_GUEST"},
                             {"ok": True, "user_id": "U_GUEST"}, PEOPLE)
    assert state == "guest-installer"
    assert "deprovisioned soonest" in detail


def test_row_naming_the_wrong_human_is_unmonitored():
    state, detail = exposure({"key": "T1", "installer": "U_GONE"},
                             {"ok": True, "user_id": "U_LIVE"}, PEOPLE)
    assert state == "installer-id-drift"
    assert "not this credential" in detail


def test_missing_installer_id_is_recovered_while_it_still_can_be():
    state, detail = exposure({"key": "T1"}, {"ok": True, "user_id": "U_LIVE"}, PEOPLE)
    assert state == "installer-not-recorded"
    assert "U_LIVE" in detail


def test_installer_absent_from_the_directory():
    state, _ = exposure({"key": "T1", "installer": "U_OTHER"},
                        {"ok": True, "user_id": "U_OTHER"}, PEOPLE)
    assert state == "installer-not-in-directory"
''',
"test_js_file": "slack-installer-account-watch.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { directory, exposure } from './slack-installer-account-watch.mjs';

const PEOPLE = directory([
  { id: 'U_LIVE', name: 'dana', deleted: false },
  { id: 'U_GONE', name: 'sam', deleted: true },
  { id: 'U_GUEST', name: 'vendor', deleted: false, is_restricted: true },
]);

test('directory keeps only what the audit reasons about', () => {
  assert.deepEqual(PEOPLE.get('U_GUEST'),
    { name: 'vendor', deleted: false, is_bot: false, guest: true });
  assert.equal(PEOPLE.has('U_MISSING'), false);
});

test('account_inactive is the already broken state', () => {
  const [state, detail] = exposure({ key: 'T1', installer: 'U_GONE' },
    { ok: false, error: 'account_inactive' }, PEOPLE);
  assert.equal(state, 'already-broken');
  assert.match(detail, /still installed/);
});

test('a revoked token is not this failure', () => {
  const [state, detail] = exposure({ key: 'T1' },
    { ok: false, error: 'token_revoked' }, PEOPLE);
  assert.equal(state, 'other-failure');
  assert.match(detail, /token_revoked/);
});

test('bot token has no exposure at all', () => {
  const [state, detail] = exposure({ key: 'T1' },
    { ok: true, user_id: 'U_BOT', bot_id: 'B1' }, PEOPLE);
  assert.equal(state, 'bot-token');
  assert.match(detail, /no dependency on any human/);
});

test('live installer is reported before anything breaks', () => {
  const [state, detail] = exposure({ key: 'T1', installer: 'U_LIVE' },
    { ok: true, user_id: 'U_LIVE' }, PEOPLE);
  assert.equal(state, 'standing-on-a-human');
  assert.match(detail, /their last day/);
});

test('guest installer is the most fragile row', () => {
  const [state, detail] = exposure({ key: 'T1', installer: 'U_GUEST' },
    { ok: true, user_id: 'U_GUEST' }, PEOPLE);
  assert.equal(state, 'guest-installer');
  assert.match(detail, /deprovisioned soonest/);
});

test('row naming the wrong human is unmonitored', () => {
  const [state, detail] = exposure({ key: 'T1', installer: 'U_GONE' },
    { ok: true, user_id: 'U_LIVE' }, PEOPLE);
  assert.equal(state, 'installer-id-drift');
  assert.match(detail, /not this credential/);
});

test('missing installer id is recovered while it still can be', () => {
  const [state, detail] = exposure({ key: 'T1' }, { ok: true, user_id: 'U_LIVE' }, PEOPLE);
  assert.equal(state, 'installer-not-recorded');
  assert.match(detail, /U_LIVE/);
});

test('installer absent from the directory', () => {
  const [state] = exposure({ key: 'T1', installer: 'U_OTHER' },
    { ok: true, user_id: 'U_OTHER' }, PEOPLE);
  assert.equal(state, 'installer-not-in-directory');
});
''',
"faq": [
 ("Does the app get uninstalled when the installer is deactivated?",
  "No, and that is what makes this confusing. The installation survives, the app still appears in Manage apps, and bot tokens issued by that install keep working. Only the user token dies, because it is a credential belonging to a person rather than to the app."),
 ("Can I just reactivate the account to bring the token back?",
  "Sometimes, and it is the wrong instinct. Reactivating a departed employee's account to keep a cron job alive is a licence cost and an access-control problem, and it leaves the same failure scheduled for the next person who leaves. Move the work to a bot token instead."),
 ("What if the job genuinely needs a user token?",
  "Message search and acting-as-a-person posts have no bot equivalent, so some jobs really do need one. Install from a service account that is documented, exempt from offboarding, and owned by a team rather than a person, and monitor its deleted flag on a schedule. A service account can still be deactivated during a licence audit."),
 ("Why look at users.list rather than users.info per install?",
  "Because one paginated sweep is a handful of calls regardless of how many installs you have, while users.info per row scales with the store and runs into the rate limiter. The sweep also gives you the deactivated count for the workspace, which is useful context for how aggressive the offboarding process is."),
 ("The token works but the directory says the user is deleted. What now?",
  "Read it by hand rather than acting on it. The usual causes are a recently deactivated account whose token has not been swept yet, a Grid workspace where the person exists in a different member list, or a row whose recorded installer is not who the token belongs to. The script reports the disagreement instead of picking a side."),
],
"related": [
 ("/slack/token-revoked/", "token_revoked means the app is gone"),
 ("/slack/bot-vs-user-scope-mixup/", "the scope is on the other token"),
 ("/slack/users-read-email-missing/", "every profile has a null email"),
],
"citations": [CITE_USERS_INFO, CITE_AUTH_TEST, CITE_TOKENS, CITE_USERS_LIST],
},

{
"slug": "token-expired-rotation",
"title": "token_expired every 12 hours because rotation is on",
"description": "Rotated Slack tokens live 43200 seconds. Read the xoxe. prefix and the stored expires_in to find installs with no refresh loop, before tonight breaks them.",
"h1": "token_expired every 12 hours because rotation is on",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack token_expired rotation", "xoxe token prefix slack",
             "slack expires_in 43200", "oauth.v2.access grant_type refresh_token",
             "slack token rotation cannot be disabled"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The app is perfect for half a day after every deploy and then every call returns <code>{\"ok\": false, \"error\": \"token_expired\"}</code>. A nightly redeploy hid it for four months, because each deploy ran the install flow again and each install handed back a fresh token. Then the redeploy was removed as an optimisation, and the app started dying every lunchtime.",
"short_answer": """<p>Look at the token string before you call anything. A leading <code>xoxe.</code> means rotation is enabled: that access token expires <code>43200</code> seconds &mdash; twelve hours &mdash; after it was issued, and the install response also returned an <code>xoxe-1-</code> refresh token you were expected to keep. If you did not keep it, this install is permanently broken on a twelve-hour cycle, because rotation cannot be switched off once it is on.</p>
<p>The finding is arithmetic, not an error: <code>obtained_at + expires_in</code> against the clock tells you which installs expire tonight, hours before any of them fail. <code>auth.test</code> then confirms, and the interesting result is when the two disagree.</p>""",
"problem": """<p>Token rotation is a good idea that is easy to turn on by accident. It is a switch in the app configuration, and it is also a line in an app manifest &mdash; <code>token_rotation_enabled: true</code> &mdash; so adopting a manifest that somebody else wrote, or copying one from a template, enables it for an app whose code has never heard of refresh tokens. The install flow still succeeds. Every call still works. For twelve hours.</p>
<p>What makes it hard to see is the shape of the symptom. It is not a failure that happens under load, or on one endpoint, or for one workspace: it is a failure that happens at a fixed offset from the last deploy, which means anything that redeploys regularly looks completely healthy. Nightly CI, a platform that recycles containers, an autoscaler that replaces instances &mdash; each of these silently re-runs whatever obtains the token and resets the clock. The bug surfaces the day the deploy cadence slows down.</p>
<p>And rotation is one-way. Slack does not offer a switch to turn it back off, so "just disable it" is not among the options no matter how attractive it sounds at 3am. The only way out is forward: store both halves of the pair, refresh before expiry, and persist the new pair atomically.</p>""",
"why": """<p><strong>The prefix is the tell, and it is on the token itself.</strong> Rotated access tokens arrive as <code>xoxe.xoxb-</code> or <code>xoxe.xoxp-</code>; the companion refresh token starts <code>xoxe-1-</code>. A classic <code>xoxb-</code> token does not expire. One string comparison, no network call, tells you which regime an install is in.</p>
<p><strong><code>expires_in</code> is 43200 and it is a lifetime, not a deadline.</strong> It counts from issue, so a stored token is only meaningful next to the timestamp at which you received it. A store that persisted the token and dropped <code>obtained_at</code> cannot compute an expiry at all, which is a finding in its own right: you cannot schedule a refresh you cannot date.</p>
<p><strong>Refresh at half life, not at expiry.</strong> A job scheduled for the moment of expiry has no room for a failed request, a slow deploy, or a clock skew. <code>expires_in / 2</code> gives six hours of slack and costs one extra call a day.</p>
<p><strong>Both halves change on every refresh.</strong> <code>oauth.v2.access</code> with <code>grant_type=refresh_token</code> returns a new access token <em>and</em> a new refresh token, and the old refresh token is single use. Persist the pair in one transaction; writing the access token and losing the refresh token converts a twelve-hour problem into a reinstall.</p>
<p><strong>Rotation cannot be disabled.</strong> Once enabled on an app it stays enabled, for every installation, forever. That is why an app that opted in without building the refresh loop is not intermittently broken but permanently broken on a schedule.</p>""",
"steps": [
 {"h": "Export what you persisted from the OAuth response",
  "body": """<p>Per row: the token, the refresh token if you kept one, <code>expires_in</code>, and the timestamp at which the pair was obtained or last refreshed. This audit is arithmetic over those four fields, so an export that only has the token can tell you the regime and nothing about the schedule.</p>"""},
 {"h": "Read the prefix of every token",
  "body": """<p><code>xoxe.</code> means a rotated access token, <code>xoxe-1-</code> a refresh token, <code>xoxb-</code> or <code>xoxp-</code> a classic one that does not expire. A refresh token sitting in the variable your Web API client reads is its own bug, and this check catches it without a network call.</p>"""},
 {"h": "Compute the expiry from what you stored",
  "body": """<p><code>obtained_at + expires_in</code> against now, sorted into fresh, past the halfway mark, and already expired. This is the part that runs before anything breaks: an install past its half life with no scheduled refresh will fail tonight, and it says so this afternoon.</p>"""},
 {"h": "Report the install with no refresh token loudly",
  "body": """<p>Rotation on and no <code>xoxe-1-</code> stored is the terminal case. There is nothing to refresh with, rotation cannot be turned off, and the only repair is a fresh OAuth install that keeps both halves. Everything else in this audit is a schedule; this one is an outage on a timer.</p>"""},
 {"h": "Confirm with auth.test, and read the disagreements",
  "body": """<p>A live rotated token answers <code>ok: true</code>; an expired one answers <code>token_expired</code>. The valuable result is when the clock and the API disagree: a token your store thinks is fresh but Slack has expired means the stored timestamp is wrong, and one your store thinks is dead but Slack accepts means another replica refreshed and you are holding a stale row.</p>"""},
 {"h": "Build the refresh loop, or adopt the SDK that has one",
  "body": """<p>The printed repair is a form-encoded call to <code>oauth.v2.access</code> with <code>client_id</code>, <code>client_secret</code>, <code>grant_type=refresh_token</code> and the stored refresh token, persisting both returned values atomically and scheduling the next refresh at half life. Bolt's installation store does this for you when rotation is enabled, which is the shorter route.</p>"""},
],
"verify": """<p>Re-run a few hours after the refresh job has run once. Every rotated install should be fresh, and the clock and the API should agree on every row.</p>
<pre><code class="language-bash">python3 slack_rotation_clock.py --store installs.json
# fresh        acme   5.2 hour(s) of life left of 43200s; refresh due at 6.0h
# 4 row(s) checked, 0 expiring unrefreshed, 0 disagreeing with the API</code></pre>""",
"code_intro": "The detection happens before the network call: <code>token_shape</code> reads the prefix and <code>clock</code> does arithmetic over the record you persisted, so the finding exists hours before any request fails. One <code>auth.test</code> per row then confirms it, <code>confirm</code> reads that answer, and <code>agreement</code> compares the two &mdash; because a store that disagrees with Slack about when a token dies is its own bug.",
"py_file": "slack_rotation_clock.py",
"py": '''"""Find Slack installs where token rotation is on and nothing refreshes them.

Read only. The detection is arithmetic over what you persisted; one GET per row
confirms it. Nothing is refreshed here: minting a token is a write, and the
refresh call is printed for a human to run.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_rotation_clock")

API = "https://slack.com/api/"

# Every rotated access token Slack issues carries this lifetime. It is a
# constant, not a per-app setting, which is why a stored expires_in that is not
# 43200 usually means the field was copied from somewhere else.
ROTATED_LIFETIME = 43200


def token_shape(token):
    """Which regime a token string belongs to. Pure, and needs no network call.

    The xoxe. check comes first: a rotated access token is xoxe.xoxb-, and a
    refresh token is xoxe-1-, so a prefix test that starts with "xoxe-" would
    swallow both and report the wrong one.
    """
    if not token:
        return "absent"
    if token.startswith("xoxe.xoxb-") or token.startswith("xoxe.xoxp-"):
        return "rotating"
    if token.startswith("xoxe-"):
        return "refresh"
    if token.startswith("xoxb-") or token.startswith("xoxp-"):
        return "classic"
    if token.startswith("xapp-"):
        return "app-level"
    return "unrecognised"


def parse_ts(text):
    """The timestamp shapes an installation store actually holds."""
    if not text:
        return None
    try:
        return datetime.strptime(str(text)[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(str(text)[:10], "%Y-%m-%d")
    except ValueError:
        return None


def clock(row, now):
    """Where this install is in its twelve hour cycle. Pure.

    `row` carries expires_in, has_refresh_token, and the moment the pair was
    obtained or last refreshed. This runs before any request fails, which is the
    only reason the audit is worth running at all.
    """
    expires_in = row.get("expires_in")
    if not expires_in:
        return ("not-rotating",
                "no expires_in persisted. A classic xoxb- token does not expire; "
                "if the token string starts xoxe. then the expiry is real and you "
                "did not record it.")
    if not row.get("has_refresh_token"):
        return ("no-refresh-token",
                "rotation is on and no refresh token is stored. Rotation cannot "
                "be switched off, so this install breaks every %d hour(s) until a "
                "fresh OAuth install keeps both halves." % (expires_in // 3600))

    started = parse_ts(row.get("refreshed_at") or row.get("obtained_at"))
    if started is None:
        return ("clock-unknown",
                "expires_in is %ds and nothing records when the pair was issued. "
                "You cannot schedule a refresh you cannot date." % expires_in)

    age = (now - started).total_seconds()
    half = expires_in / 2.0
    if age >= expires_in:
        return ("expired",
                "issued %.1f hour(s) ago against a %ds life. Every call is "
                "answering token_expired." % (age / 3600.0, expires_in))
    if age >= half:
        return ("overdue",
                "%.1f hour(s) old, past the %.1f hour halfway mark. Refresh at "
                "expires_in/2, not at expiry: a job scheduled for the deadline "
                "has no room for a failed request."
                % (age / 3600.0, half / 3600.0))
    return ("fresh",
            "%.1f hour(s) of life left of %ds; refresh due at %.1fh"
            % ((expires_in - age) / 3600.0, expires_in, half / 3600.0))


def confirm(body):
    """What Slack says about the same token, right now. Pure."""
    if body.get("ok") is True:
        return ("live", "auth.test succeeded for team %s" % (body.get("team_id") or "?"))
    error = body.get("error")
    if error == "token_expired":
        return ("expired", "auth.test answered token_expired")
    if error == "token_revoked":
        return ("revoked", "token_revoked, which is an uninstall rather than an "
                           "expiry and wants a different repair")
    if error == "invalid_auth":
        return ("invalid", "invalid_auth: the string does not authenticate at all")
    return ("unusable", "error=%s" % (error or "<no error field>"))


def agreement(clock_state, live_state):
    """Compare the store's arithmetic against the API's answer. Pure.

    A store that disagrees with Slack about when a token dies is its own bug,
    and it is the finding that a purely live check can never produce.
    """
    if live_state in ("revoked", "invalid", "unusable"):
        return ("unrelated",
                "the token failed for a reason that has nothing to do with "
                "rotation, so the clock says nothing useful here")
    if clock_state in ("expired", "overdue") and live_state == "live":
        return ("store-behind",
                "your record says this token is spent and Slack still accepts it. "
                "Something else refreshed it and did not write back, so the row "
                "you are holding is stale")
    if clock_state == "fresh" and live_state == "expired":
        return ("store-ahead",
                "your record says hours of life remain and Slack has already "
                "expired it. The stored timestamp or expires_in is wrong, or "
                "another refresh replaced this token")
    if clock_state in ("no-refresh-token", "clock-unknown"):
        return ("unknowable",
                "the record cannot be reconciled with anything: fix what is "
                "persisted before trusting either side")
    return ("agree", "the clock and the API agree")


def auth_test(session, token):
    r = session.get(API + "auth.test", headers={"Authorization": "Bearer " + token},
                    timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def load_rows(path):
    if path:
        return json.loads(open(path, encoding="utf-8").read())
    return [{"key": "<the only row>", "token_env": "SLACK_BOT_TOKEN",
             "refresh_token_env": "SLACK_REFRESH_TOKEN",
             "expires_in": ROTATED_LIFETIME,
             "obtained_at": os.environ.get("SLACK_TOKEN_OBTAINED_AT")}]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", help="JSON array of installation rows: token_env, "
                                    "refresh_token_env, expires_in, obtained_at")
    args = ap.parse_args()

    rows = load_rows(args.store)
    s = requests.Session()
    now = datetime.utcnow()

    expiring = 0
    disagreeing = 0
    for row in rows:
        token = os.environ.get(row.get("token_env") or "SLACK_BOT_TOKEN")
        if not token:
            log.warning("%-17s %-10s row names %s and it is unset", "no-token",
                        row.get("key"), row.get("token_env"))
            continue

        shape = token_shape(token)
        if shape == "refresh":
            log.warning("%-17s %-10s the Web API variable holds an xoxe-1- refresh "
                        "token. That is the other half of the pair.",
                        "wrong-half", row.get("key"))
            expiring += 1
            continue
        if shape in ("classic", "app-level", "unrecognised"):
            log.info("%-17s %-10s %s token: rotation is not enabled for this "
                     "install", shape, row.get("key"), shape)
            continue

        has_refresh = bool(os.environ.get(row.get("refresh_token_env") or ""))
        state, detail = clock(dict(row, has_refresh_token=has_refresh), now)
        body = auth_test(s, token)
        live_state, live_detail = confirm(body)
        verdict, why = agreement(state, live_state)

        line = "%-17s %-10s %s" % (state, row.get("key"), detail)
        if state == "fresh":
            log.info(line)
        else:
            expiring += 1
            log.warning(line)
        log.info("%-17s %-10s %s", "api-says", row.get("key"), live_detail)
        if verdict != "agree":
            disagreeing += 1
            log.warning("%-17s %-10s %s", verdict, row.get("key"), why)
        if state in ("no-refresh-token", "expired", "overdue", "clock-unknown"):
            log.warning("  repair: form-encoded call to %soauth.v2.access with "
                        "client_id, client_secret, grant_type=refresh_token and the "
                        "stored xoxe-1- token; persist both returned values in one "
                        "transaction and schedule the next run at expires_in/2", API)

    log.info("%d row(s) checked, %d expiring unrefreshed, %d disagreeing with the API",
             len(rows), expiring, disagreeing)
    return 1 if (expiring or disagreeing) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-rotation-clock.mjs",
"js": '''/**
 * Find Slack installs where token rotation is on and nothing refreshes them.
 *
 * Read only. The detection is arithmetic over what you persisted; one GET per
 * row confirms it. Nothing is refreshed here: minting a token is a write, and
 * the refresh call is printed for a human to run.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Every rotated access token Slack issues carries this lifetime. It is a
// constant, not a per-app setting, which is why a stored expires_in that is not
// 43200 usually means the field was copied from somewhere else.
export const ROTATED_LIFETIME = 43200;

/**
 * Which regime a token string belongs to. Pure, and needs no network call.
 * The xoxe. check comes first: a rotated access token is xoxe.xoxb- and a
 * refresh token is xoxe-1-, so a test on "xoxe-" alone reports the wrong one.
 */
export function tokenShape(token) {
  if (!token) return 'absent';
  if (token.startsWith('xoxe.xoxb-') || token.startsWith('xoxe.xoxp-')) return 'rotating';
  if (token.startsWith('xoxe-')) return 'refresh';
  if (token.startsWith('xoxb-') || token.startsWith('xoxp-')) return 'classic';
  if (token.startsWith('xapp-')) return 'app-level';
  return 'unrecognised';
}

/** The timestamp shapes an installation store actually holds. */
export function parseTs(text) {
  if (!text) return null;
  const d = new Date(text);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Where this install is in its twelve hour cycle. Pure. This runs before any
 * request fails, which is the only reason the audit is worth running at all.
 */
export function clock(row, now) {
  const expiresIn = row.expires_in;
  if (!expiresIn) {
    return ['not-rotating',
      'no expires_in persisted. A classic xoxb- token does not expire; if the ' +
      'token string starts xoxe. then the expiry is real and you did not record it.'];
  }
  if (!row.has_refresh_token) {
    return ['no-refresh-token',
      'rotation is on and no refresh token is stored. Rotation cannot be switched ' +
      `off, so this install breaks every ${Math.floor(expiresIn / 3600)} hour(s) ` +
      'until a fresh OAuth install keeps both halves.'];
  }

  const started = parseTs(row.refreshed_at || row.obtained_at);
  if (started === null) {
    return ['clock-unknown',
      `expires_in is ${expiresIn}s and nothing records when the pair was issued. ` +
      'You cannot schedule a refresh you cannot date.'];
  }

  const age = (now.getTime() - started.getTime()) / 1000;
  const half = expiresIn / 2;
  if (age >= expiresIn) {
    return ['expired',
      `issued ${(age / 3600).toFixed(1)} hour(s) ago against a ${expiresIn}s life. ` +
      'Every call is answering token_expired.'];
  }
  if (age >= half) {
    return ['overdue',
      `${(age / 3600).toFixed(1)} hour(s) old, past the ${(half / 3600).toFixed(1)} ` +
      'hour halfway mark. Refresh at expires_in/2, not at expiry: a job scheduled ' +
      'for the deadline has no room for a failed request.'];
  }
  return ['fresh',
    `${((expiresIn - age) / 3600).toFixed(1)} hour(s) of life left of ${expiresIn}s; ` +
    `refresh due at ${(half / 3600).toFixed(1)}h`];
}

/** What Slack says about the same token, right now. Pure. */
export function confirm(body) {
  if (body?.ok === true) {
    return ['live', `auth.test succeeded for team ${body.team_id ?? '?'}`];
  }
  const error = body?.error;
  if (error === 'token_expired') return ['expired', 'auth.test answered token_expired'];
  if (error === 'token_revoked') {
    return ['revoked',
      'token_revoked, which is an uninstall rather than an expiry and wants a ' +
      'different repair'];
  }
  if (error === 'invalid_auth') {
    return ['invalid', 'invalid_auth: the string does not authenticate at all'];
  }
  return ['unusable', `error=${error ?? '<no error field>'}`];
}

/**
 * Compare the store's arithmetic against the API's answer. Pure. A store that
 * disagrees with Slack about when a token dies is its own bug, and it is the
 * finding a purely live check can never produce.
 */
export function agreement(clockState, liveState) {
  if (['revoked', 'invalid', 'unusable'].includes(liveState)) {
    return ['unrelated',
      'the token failed for a reason that has nothing to do with rotation, so the ' +
      'clock says nothing useful here'];
  }
  if (['expired', 'overdue'].includes(clockState) && liveState === 'live') {
    return ['store-behind',
      'your record says this token is spent and Slack still accepts it. Something ' +
      'else refreshed it and did not write back, so the row you are holding is stale'];
  }
  if (clockState === 'fresh' && liveState === 'expired') {
    return ['store-ahead',
      'your record says hours of life remain and Slack has already expired it. The ' +
      'stored timestamp or expires_in is wrong, or another refresh replaced this token'];
  }
  if (['no-refresh-token', 'clock-unknown'].includes(clockState)) {
    return ['unknowable',
      'the record cannot be reconciled with anything: fix what is persisted before ' +
      'trusting either side'];
  }
  return ['agree', 'the clock and the API agree'];
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
  return [{
    key: '<the only row>',
    token_env: 'SLACK_BOT_TOKEN',
    refresh_token_env: 'SLACK_REFRESH_TOKEN',
    expires_in: ROTATED_LIFETIME,
    obtained_at: process.env.SLACK_TOKEN_OBTAINED_AT,
  }];
}

async function main() {
  const args = process.argv.slice(2);
  const i = args.indexOf('--store');
  const store = i === -1 ? null : args[i + 1];

  const rows = await loadRows(store);
  const now = new Date();
  let expiring = 0;
  let disagreeing = 0;

  for (const row of rows) {
    const token = process.env[row.token_env ?? 'SLACK_BOT_TOKEN'];
    if (!token) {
      console.warn(`${'no-token'.padEnd(17)} ${String(row.key).padEnd(10)} row names ` +
        `${row.token_env} and it is unset`);
      continue;
    }

    const shape = tokenShape(token);
    if (shape === 'refresh') {
      console.warn(`${'wrong-half'.padEnd(17)} ${String(row.key).padEnd(10)} the Web ` +
        'API variable holds an xoxe-1- refresh token. That is the other half of the pair.');
      expiring += 1;
      continue;
    }
    if (['classic', 'app-level', 'unrecognised'].includes(shape)) {
      console.log(`${shape.padEnd(17)} ${String(row.key).padEnd(10)} ${shape} token: ` +
        'rotation is not enabled for this install');
      continue;
    }

    const hasRefresh = Boolean(process.env[row.refresh_token_env ?? '']);
    const [state, detail] = clock({ ...row, has_refresh_token: hasRefresh }, now);
    const body = await authTest(token);
    const [liveState, liveDetail] = confirm(body);
    const [verdict, why] = agreement(state, liveState);

    const line = `${state.padEnd(17)} ${String(row.key).padEnd(10)} ${detail}`;
    if (state === 'fresh') {
      console.log(line);
    } else {
      expiring += 1;
      console.warn(line);
    }
    console.log(`${'api-says'.padEnd(17)} ${String(row.key).padEnd(10)} ${liveDetail}`);
    if (verdict !== 'agree') {
      disagreeing += 1;
      console.warn(`${verdict.padEnd(17)} ${String(row.key).padEnd(10)} ${why}`);
    }
    if (['no-refresh-token', 'expired', 'overdue', 'clock-unknown'].includes(state)) {
      console.warn(`  repair: form-encoded call to ${API}oauth.v2.access with ` +
        'client_id, client_secret, grant_type=refresh_token and the stored xoxe-1- ' +
        'token; persist both returned values in one transaction and schedule the ' +
        'next run at expires_in/2');
    }
  }

  console.log(`${rows.length} row(s) checked, ${expiring} expiring unrefreshed, ` +
    `${disagreeing} disagreeing with the API`);
  process.exitCode = expiring || disagreeing ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things have to be pinned. The prefix test must return <code>rotating</code> for <code>xoxe.xoxb-</code> and <code>refresh</code> for <code>xoxe-1-</code>, because a check written as \"starts with xoxe\" swallows both and cheerfully reports a refresh token as a healthy access token. And the halfway mark must be a finding while the token still works &mdash; a script that only reports expired tokens has waited until the outage to speak.",
"test_py_file": "test_slack_rotation_clock.py",
"test_py": '''from datetime import datetime

from slack_rotation_clock import agreement, clock, confirm, token_shape

NOW = datetime(2026, 8, 30, 12, 0, 0)
ROTATED = {"expires_in": 43200, "has_refresh_token": True}


def test_the_two_xoxe_prefixes_are_not_the_same_thing():
    assert token_shape("xoxe.xoxb-1-abc") == "rotating"
    assert token_shape("xoxe-1-abc") == "refresh"
    assert token_shape("xoxb-1-abc") == "classic"
    assert token_shape("xapp-1-abc") == "app-level"
    assert token_shape(None) == "absent"


def test_rotation_on_with_nothing_to_refresh_with_is_terminal():
    state, detail = clock({"expires_in": 43200, "has_refresh_token": False}, NOW)
    assert state == "no-refresh-token"
    assert "cannot be switched off" in detail


def test_a_classic_token_is_not_rotating():
    assert clock({"has_refresh_token": False}, NOW)[0] == "not-rotating"


def test_past_the_halfway_mark_is_a_finding_while_it_still_works():
    row = dict(ROTATED, obtained_at="2026-08-30T04:00:00Z")
    state, detail = clock(row, NOW)
    assert state == "overdue"
    assert "expires_in/2" in detail


def test_still_inside_the_first_half_is_quiet():
    assert clock(dict(ROTATED, obtained_at="2026-08-30T11:00:00Z"), NOW)[0] == "fresh"


def test_past_the_lifetime_is_expired():
    assert clock(dict(ROTATED, obtained_at="2026-08-29T20:00:00Z"), NOW)[0] == "expired"


def test_a_pair_with_no_timestamp_cannot_be_scheduled():
    state, detail = clock(ROTATED, NOW)
    assert state == "clock-unknown"
    assert "cannot date" in detail


def test_the_last_refresh_wins_over_the_original_issue():
    row = dict(ROTATED, obtained_at="2026-08-01T00:00:00Z",
               refreshed_at="2026-08-30T11:00:00Z")
    assert clock(row, NOW)[0] == "fresh"


def test_confirm_separates_expiry_from_uninstall():
    assert confirm({"ok": True, "team_id": "T1"})[0] == "live"
    assert confirm({"ok": False, "error": "token_expired"})[0] == "expired"
    assert confirm({"ok": False, "error": "token_revoked"})[0] == "revoked"


def test_store_and_api_disagreeing_is_its_own_finding():
    assert agreement("expired", "live")[0] == "store-behind"
    assert agreement("fresh", "expired")[0] == "store-ahead"
    assert agreement("fresh", "live")[0] == "agree"
    assert agreement("expired", "revoked")[0] == "unrelated"
''',
"test_js_file": "slack-rotation-clock.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { agreement, clock, confirm, tokenShape } from './slack-rotation-clock.mjs';

const NOW = new Date('2026-08-30T12:00:00Z');
const ROTATED = { expires_in: 43200, has_refresh_token: true };

test('the two xoxe prefixes are not the same thing', () => {
  assert.equal(tokenShape('xoxe.xoxb-1-abc'), 'rotating');
  assert.equal(tokenShape('xoxe-1-abc'), 'refresh');
  assert.equal(tokenShape('xoxb-1-abc'), 'classic');
  assert.equal(tokenShape('xapp-1-abc'), 'app-level');
  assert.equal(tokenShape(null), 'absent');
});

test('rotation on with nothing to refresh with is terminal', () => {
  const [state, detail] = clock({ expires_in: 43200, has_refresh_token: false }, NOW);
  assert.equal(state, 'no-refresh-token');
  assert.match(detail, /cannot be switched off/);
});

test('a classic token is not rotating', () => {
  assert.equal(clock({ has_refresh_token: false }, NOW)[0], 'not-rotating');
});

test('past the halfway mark is a finding while it still works', () => {
  const [state, detail] = clock({ ...ROTATED, obtained_at: '2026-08-30T04:00:00Z' }, NOW);
  assert.equal(state, 'overdue');
  assert.match(detail, /expires_in\\/2/);
});

test('still inside the first half is quiet', () => {
  assert.equal(clock({ ...ROTATED, obtained_at: '2026-08-30T11:00:00Z' }, NOW)[0], 'fresh');
});

test('past the lifetime is expired', () => {
  assert.equal(clock({ ...ROTATED, obtained_at: '2026-08-29T20:00:00Z' }, NOW)[0], 'expired');
});

test('a pair with no timestamp cannot be scheduled', () => {
  const [state, detail] = clock(ROTATED, NOW);
  assert.equal(state, 'clock-unknown');
  assert.match(detail, /cannot date/);
});

test('the last refresh wins over the original issue', () => {
  const row = { ...ROTATED, obtained_at: '2026-08-01T00:00:00Z',
    refreshed_at: '2026-08-30T11:00:00Z' };
  assert.equal(clock(row, NOW)[0], 'fresh');
});

test('confirm separates expiry from uninstall', () => {
  assert.equal(confirm({ ok: true, team_id: 'T1' })[0], 'live');
  assert.equal(confirm({ ok: false, error: 'token_expired' })[0], 'expired');
  assert.equal(confirm({ ok: false, error: 'token_revoked' })[0], 'revoked');
});

test('store and api disagreeing is its own finding', () => {
  assert.equal(agreement('expired', 'live')[0], 'store-behind');
  assert.equal(agreement('fresh', 'expired')[0], 'store-ahead');
  assert.equal(agreement('fresh', 'live')[0], 'agree');
  assert.equal(agreement('expired', 'revoked')[0], 'unrelated');
});
''',
"faq": [
 ("How do I know rotation is enabled without asking anyone?",
  "Look at the token. A rotated access token starts xoxe.xoxb- or xoxe.xoxp- and a classic one starts xoxb- or xoxp-. If you kept the OAuth response, a non-null expires_in and a refresh_token field say the same thing. With an app configuration token, apps.manifest.export reports settings.token_rotation_enabled directly, but that is a different credential class from the bot token your app runs on."),
 ("Can I turn rotation off again?",
  "No. Slack does not offer a way back once rotation is enabled on an app, which is why enabling it by adopting somebody else's manifest is such an expensive accident. The only route is to build the refresh loop, or to use an SDK installation store that already has one."),
 ("Why refresh at half life rather than just before expiry?",
  "Because a refresh scheduled at the deadline has no margin. Six hours of slack absorbs a failed request, a deploy that overruns, a paused worker and a clock that drifts, and it costs one extra call per day. Refreshing on every request is the other extreme and burns the two-active-token limit."),
 ("My token expired and the refresh token no longer works either. Now what?",
  "A fresh OAuth install, and then a look at how many workers refresh concurrently. Slack refresh tokens are single use: two replicas refreshing at once, or a retry after a response that was lost in transit, both burn the token twice and revoke the pair. Serialise refreshes behind a per-installation lock."),
 ("Does the nightly redeploy that hid this count as a fix?",
  "No, it is a coincidence with a deployment schedule attached. Anything that re-runs the install flow resets the twelve-hour clock, which is why the bug appears the week somebody removes a redundant deploy or lengthens the release cadence. The refresh loop is the fix; the redeploy just moved the failure into the future."),
],
"related": [
 ("/slack/token-revoked/", "token_revoked means the app is gone"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_ROTATION, CITE_OAUTH_ACCESS, CITE_AUTH_TEST, CITE_TOKENS],
},

]
