#!/usr/bin/env python3
"""/slack/ field notes, batch A — the writing.

Four notes that are one note seen four ways. Slack answers almost every failure
with HTTP 200 and puts the reason in the JSON body, so code that checks the
status code never sees it. The first note is that fact; the other three are the
three shapes it takes in practice — a bot outside the channel, a scope the token
never got, and a list read one page deep.

Read-only throughout: a bot token with read scopes, GET requests only, and the
repair printed for a human to run. These scripts hold a token that can post into
a workspace, so none of them writes.
"""

CITE_WEBAPI = ("Using the Slack Web API — Slack Docs",
               "https://docs.slack.dev/apis/web-api/")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_POSTMESSAGE = ("chat.postMessage method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_TOKENS = ("Token types — Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_INSTALL = ("Installing with OAuth — Slack Docs",
                "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_CONV_INFO = ("conversations.info method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CONV_JOIN = ("conversations.join method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.join")
CITE_CONV_MEMBERS = ("conversations.members method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.members")
CITE_USERS_CONV = ("users.conversations method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.conversations")
CITE_PAGINATION = ("Pagination in the Web API — Slack Docs",
                   "https://docs.slack.dev/apis/web-api/pagination")
CITE_CONV_LIST = ("conversations.list method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_USERS_LIST = ("users.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")

GUIDES = [

{
"slug": "http-200-ok-false",
"title": "Slack answers HTTP 200 and puts the failure in the body",
"description": "Every Slack Web API error arrives as 200 OK with ok: false in the JSON. Clients that check the status code read every failure as a success.",
"h1": "slack answers HTTP 200 and puts the failure in the body",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack api ok false", "slack 200 but no message",
             "slack chat.postMessage not working", "slack api error handling",
             "slack web api returns 200"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The deploy is green. The log line reads <code>POST https://slack.com/api/chat.postMessage 200</code>. Nothing has appeared in the channel for three weeks. When somebody finally logs the response body it reads <code>{\"ok\": false, \"error\": \"not_in_channel\"}</code> &mdash; and it has read that, unchanged, every single time.",
"short_answer": """<p>Slack's Web API is RPC over HTTP. It keeps non-2xx status codes for transport-level problems and returns application-level failures &mdash; bad auth, a missing scope, a channel the bot is not in, malformed Block Kit &mdash; inside a <code>200 OK</code> body as <code>{"ok": false, "error": "..."}</code>.</p>
<p>The rule for every Slack call you make: <strong><code>response.status == 200</code> proves nothing; <code>body.ok === true</code> is the only success signal.</strong> Record <code>ok</code>, <code>error</code>, <code>needed</code>, <code>provided</code>, <code>warning</code> and <code>response_metadata.warnings</code>, and raise on the first of those that is wrong.</p>""",
"problem": """<p>Every HTTP client in common use is built on the assumption that the status code carries the verdict. <code>requests</code> only raises inside <code>raise_for_status()</code>, <code>fetch</code> sets <code>res.ok</code> from the status line, <code>axios</code> rejects on 4xx and 5xx, .NET's <code>EnsureSuccessStatusCode</code> does the same. Point any of them at Slack and they will report perfect health while the integration does nothing at all.</p>
<p>What makes it last for weeks rather than minutes is that there is no error anywhere to find. The exception tracker is empty because nothing threw. The dashboard is green because every request returned 200. The retry logic never fires because nothing looked like a failure. The only artefact of the outage is an absence &mdash; messages that were never posted &mdash; and absences do not page anyone.</p>""",
"why": """<p><strong>Slack reserves HTTP status for transport, not for logic.</strong> A 200 means the request reached Slack, was parsed, and produced an answer. Whether that answer is "done" or "no" is a field in the body. This is a deliberate design decision, documented, and consistent across nearly the whole Web API.</p>
<p><strong>The official SDKs hide it, which is why hand-rolled clients suffer.</strong> <code>@slack/web-api</code> and <code>slack_sdk</code> both raise on <code>ok: false</code>, so teams using them meet the error immediately as an exception. Anyone who reached for <code>fetch</code> or <code>requests</code> because "it's just one POST" inherits the raw contract and usually does not know it exists.</p>
<p><strong>The interesting information is in fields nobody reads.</strong> <code>missing_scope</code> comes with <code>needed</code> and <code>provided</code>. Deprecations and encoding problems come back as <code>warning</code> on an otherwise successful call. All of it is discarded by code that checks a status code and moves on.</p>
<p><strong>The few exceptions make it worse, not better.</strong> Incoming webhooks <em>do</em> return real 4xx with a plain-text body, and rate limiting sometimes surfaces as a genuine <code>429</code> with <code>Retry-After</code>. So a developer who once saw Slack return a real error code reasonably concludes that Slack returns real error codes.</p>""",
"steps": [
 {"h": "Probe a handful of read methods and keep the whole response",
  "body": """<p>Call <code>auth.test</code>, <code>team.info</code>, <code>conversations.list</code>, <code>users.list</code> and <code>emoji.list</code> with <code>Authorization: Bearer &lt;token&gt;</code>. Read methods answer a <code>GET</code>, so nothing here can change your workspace. Keep both the status line and the parsed body for every one of them.</p>"""},
 {"h": "Judge on body.ok, never on the status line",
  "body": """<p><code>ok</code> is a boolean, and it is the verdict. Treat a missing <code>ok</code> exactly like <code>false</code>: an unparseable or truncated body is not a success, and defaulting it to true is how a proxy error page gets recorded as a delivered message.</p>"""},
 {"h": "Read the diagnostic fields Slack already gave you",
  "body": """<p>On <code>ok: false</code>, <code>error</code> names the failure. On <code>missing_scope</code>, <code>needed</code> and <code>provided</code> tell you exactly which scope to add and what the token holds today. Log all three or you will be back here reading the same response by hand.</p>"""},
 {"h": "Surface warnings on calls that succeeded",
  "body": """<p><code>body.warning</code> and <code>body.response_metadata.warnings[]</code> carry non-fatal notices &mdash; <code>missing_charset</code>, <code>superfluous_charset</code>, deprecation notices &mdash; on responses where <code>ok</code> is <code>true</code>. They are the only advance notice you get before a method stops working.</p>"""},
 {"h": "Move the check into the transport, once",
  "body": """<p>One wrapper that raises on <code>ok !== true</code> fixes every call site at the same time. Adopting <code>@slack/web-api</code> or <code>slack_sdk</code> does the same thing and hands you <code>e.data.error</code> as well. What does not work is remembering to check by hand at each call site.</p>"""},
],
"verify": """<p>Re-run the script. Every probed method should report <code>ok</code>, and the summary line should show nothing that returned 200 without <code>ok: true</code>.</p>
<pre><code class="language-bash">python3 slack_ok_false_audit.py
# 5 method(s) probed, 0 answered 200 without ok: true</code></pre>""",
"code_intro": "Five GET requests and no writes at all &mdash; a bot token with read scopes is enough, and is what you should give it. The classifier is a pure function taking the status code and the parsed body, because the rule this whole section rests on is exactly one branch and it deserves to be readable rather than buried in a request loop.",
"py_file": "slack_ok_false_audit.py",
"py": '''"""Find Slack calls that returned HTTP 200 and failed anyway.

Read only. GET requests and nothing else: give this a bot token with read scopes.
The repair is printed, never performed, because a Slack bot token can post into
your workspace.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_ok_false_audit")

API = "https://slack.com/api/"

# Read methods that are safe to probe and cheap to answer. Every one of them
# returns 200 whether it worked or not, which is the entire point.
PROBES = [
    ("auth.test", {}),
    ("team.info", {}),
    ("conversations.list", {"limit": "1", "types": "public_channel"}),
    ("users.list", {"limit": "1"}),
    ("emoji.list", {}),
]


def verdict(status, body):
    """Classify one Slack response. Pure, so the rule is testable offline.

    `status` is the HTTP status code, `body` the parsed JSON (or the raw text if
    it did not parse). A 200 proves the request reached Slack and nothing more.
    """
    if status != 200:
        return ("transport",
                "HTTP %s. Slack keeps non-2xx for transport level failures, so "
                "this one means what it says: a proxy, a bad host, or a real 429."
                % status)
    if not isinstance(body, dict):
        return ("unreadable",
                "200 with a body that is not JSON. Every Web API method answers "
                "JSON, so something other than Slack replied.")
    if body.get("ok") is not True:
        return ("ok-false",
                "200 OK carrying error=%s. The status line said success and the "
                "body did not." % (body.get("error") or "<no error field>"))
    warnings = [w for w in (body.get("response_metadata") or {}).get("warnings", []) or []]
    if body.get("warning"):
        warnings.insert(0, body["warning"])
    if warnings:
        return ("warned",
                "ok is true, with warning=%s. Not fatal, and invisible to code "
                "that reads only ok." % ",".join(warnings))
    return ("ok", "ok: true, no warnings")


def probe(session, method, params):
    r = session.get(API + method, params=params, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = r.text
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", action="append", default=[],
                    help="probe this read method instead of the default set; repeatable")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (a bot token with read scopes is enough)")
        return 2

    probes = [(m, {}) for m in args.method] or PROBES
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    bad = 0
    for method, params in probes:
        status, body = probe(s, method, params)
        state, detail = verdict(status, body)
        line = "%-10s %-20s %s" % (state, method, detail)
        if state == "ok":
            log.info(line)
            continue
        if state == "warned":
            log.warning(line)
            continue
        bad += 1
        log.warning(line)
        if isinstance(body, dict) and body.get("needed"):
            log.warning("  needed=%s provided=%s", body["needed"], body.get("provided"))
        log.warning("  repair: raise when body.ok is not true, at the transport "
                    "layer, for every Slack call")

    log.info("%d method(s) probed, %d answered 200 without ok: true", len(probes), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-ok-false-audit.mjs",
"js": '''/**
 * Find Slack calls that returned HTTP 200 and failed anyway.
 *
 * Read only. GET requests and nothing else: give this a bot token with read
 * scopes. The repair is printed, never performed.
 */
const API = 'https://slack.com/api/';

// Read methods that are safe to probe and cheap to answer. Every one of them
// returns 200 whether it worked or not, which is the entire point.
const PROBES = [
  ['auth.test', {}],
  ['team.info', {}],
  ['conversations.list', { limit: '1', types: 'public_channel' }],
  ['users.list', { limit: '1' }],
  ['emoji.list', {}],
];

/**
 * Classify one Slack response. Pure, so the rule is testable offline.
 * A 200 proves the request reached Slack and nothing more.
 */
export function verdict(status, body) {
  if (status !== 200) {
    return ['transport',
      `HTTP ${status}. Slack keeps non-2xx for transport level failures, so this ` +
      'one means what it says: a proxy, a bad host, or a real 429.'];
  }
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    return ['unreadable',
      '200 with a body that is not JSON. Every Web API method answers JSON, so ' +
      'something other than Slack replied.'];
  }
  if (body.ok !== true) {
    return ['ok-false',
      `200 OK carrying error=${body.error ?? '<no error field>'}. The status line ` +
      'said success and the body did not.'];
  }
  const warnings = [...(body.response_metadata?.warnings ?? [])];
  if (body.warning) warnings.unshift(body.warning);
  if (warnings.length) {
    return ['warned',
      `ok is true, with warning=${warnings.join(',')}. Not fatal, and invisible ` +
      'to code that reads only ok.'];
  }
  return ['ok', 'ok: true, no warnings'];
}

async function probe(token, method, params) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  let body;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (a bot token with read scopes is enough)');
    process.exitCode = 2;
    return;
  }

  const args = process.argv.slice(2);
  const only = args.filter((a) => !a.startsWith('-')).map((m) => [m, {}]);
  const probes = only.length ? only : PROBES;

  let bad = 0;
  for (const [method, params] of probes) {
    const { status, body } = await probe(token, method, params);
    const [state, detail] = verdict(status, body);
    const line = `${state.padEnd(10)} ${method.padEnd(20)} ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    if (state === 'warned') { console.warn(line); continue; }
    bad += 1;
    console.warn(line);
    if (body?.needed) console.warn(`  needed=${body.needed} provided=${body.provided}`);
    console.warn('  repair: raise when body.ok is not true, at the transport layer, ' +
                 'for every Slack call');
  }

  console.log(`${probes.length} method(s) probed, ${bad} answered 200 without ok: true`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning is a 200 with no <code>ok</code> field at all. It is not a success and it is not a Slack error either &mdash; it is usually a proxy or an error page that got as far as your JSON parser, and any classifier that treats a missing <code>ok</code> as true will record it as a delivered message.",
"test_py_file": "test_slack_ok_false_audit.py",
"test_py": '''from slack_ok_false_audit import verdict


def test_two_hundred_with_ok_false_is_a_failure():
    state, detail = verdict(200, {"ok": False, "error": "not_in_channel"})
    assert state == "ok-false"
    assert "not_in_channel" in detail


def test_two_hundred_with_ok_true_is_the_only_success():
    state, _ = verdict(200, {"ok": True})
    assert state == "ok"


def test_missing_ok_field_is_not_silently_a_success():
    # A proxy error page that happens to parse as JSON lands here.
    state, detail = verdict(200, {"channels": []})
    assert state == "ok-false"
    assert "no error field" in detail


def test_warning_on_a_successful_call_is_its_own_state():
    state, detail = verdict(200, {"ok": True, "warning": "missing_charset"})
    assert state == "warned"
    assert "missing_charset" in detail


def test_response_metadata_warnings_are_read_too():
    body = {"ok": True, "response_metadata": {"warnings": ["superfluous_charset"]}}
    assert verdict(200, body)[0] == "warned"


def test_non_json_body_is_not_a_slack_answer():
    assert verdict(200, "<html>proxy error</html>")[0] == "unreadable"


def test_real_status_codes_are_still_real():
    state, detail = verdict(429, {"ok": False, "error": "ratelimited"})
    assert state == "transport"
    assert "429" in detail
''',
"test_js_file": "slack-ok-false-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './slack-ok-false-audit.mjs';

test('two hundred with ok false is a failure', () => {
  const [state, detail] = verdict(200, { ok: false, error: 'not_in_channel' });
  assert.equal(state, 'ok-false');
  assert.match(detail, /not_in_channel/);
});

test('two hundred with ok true is the only success', () => {
  assert.equal(verdict(200, { ok: true })[0], 'ok');
});

test('missing ok field is not silently a success', () => {
  const [state, detail] = verdict(200, { channels: [] });
  assert.equal(state, 'ok-false');
  assert.match(detail, /no error field/);
});

test('warning on a successful call is its own state', () => {
  const [state, detail] = verdict(200, { ok: true, warning: 'missing_charset' });
  assert.equal(state, 'warned');
  assert.match(detail, /missing_charset/);
});

test('response_metadata warnings are read too', () => {
  const body = { ok: true, response_metadata: { warnings: ['superfluous_charset'] } };
  assert.equal(verdict(200, body)[0], 'warned');
});

test('non json body is not a slack answer', () => {
  assert.equal(verdict(200, '<html>proxy error</html>')[0], 'unreadable');
});

test('real status codes are still real', () => {
  const [state, detail] = verdict(429, { ok: false, error: 'ratelimited' });
  assert.equal(state, 'transport');
  assert.match(detail, /429/);
});
''',
"faq": [
 ("Why does Slack return 200 for an error?",
  "Because the Web API is RPC over HTTP: the status code reports whether the request reached Slack and was parsed, and the body reports whether the operation succeeded. Application-level failures like a missing scope or a channel the bot is not in are answers, not transport faults, so they come back as 200 with ok: false."),
 ("Does this apply to every Slack surface?",
  "Almost. Web API methods behave this way consistently. Incoming webhooks are the exception: they return real 4xx and 5xx with a plain-text body such as invalid_payload or no_service. Rate limiting can also surface as a genuine 429 with a Retry-After header, so handle both shapes."),
 ("Will the official SDKs fix this for me?",
  "Yes, for the raising part. Both @slack/web-api and slack_sdk throw when ok is false and expose the error on the exception, which is why teams on the SDKs rarely hit this and teams with a hand-rolled fetch call hit it immediately. They will not read body.warning for you, though."),
 ("What should I log on a failed call?",
  "error, plus needed and provided when they are present, plus warning and response_metadata.warnings. Those five fields turn nearly every Slack failure into a self-describing one, and all five are discarded by code that only reads the status code."),
 ("Is a missing ok field the same as ok: false?",
  "Treat it as worse. A well-formed Slack response always has ok. A body without it usually came from a proxy, a captive portal or an error page that happened to parse, so it means the request may not have reached Slack at all."),
],
"related": [
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/pagination-not-followed/", "next_cursor ignored, so one page is all you see"),
],
"citations": [CITE_WEBAPI, CITE_AUTH_TEST, CITE_POSTMESSAGE, CITE_TOKENS],
},


{
"slug": "bot-not-in-channel",
"title": "not_in_channel: the bot was never invited to the channel",
"description": "Installing a Slack app joins it to nothing. The token is valid, the channel ID is right, and every call returns 200 with ok: false and not_in_channel.",
"h1": "not_in_channel: the bot was never invited to the channel",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack not_in_channel", "slack bot not posting to channel",
             "slack conversations.join", "invite slack bot to channel",
             "slack channel_not_found private"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The app is installed. The token authenticates. The channel ID was copied out of the URL and is correct. Every call still comes back <code>{\"ok\": false, \"error\": \"not_in_channel\"}</code>, because installing an app to a workspace does not put it in a single channel &mdash; and this is, by view count, the most-asked Slack API question there is.",
"short_answer": """<p>Call <code>conversations.info?channel=&lt;C...&gt;</code> for every channel the app targets and read <code>channel.is_member</code>. That field reports membership for the calling token directly. For a full sweep, <code>users.conversations?user=&lt;bot_user_id&gt;&amp;types=public_channel,private_channel</code> returns every conversation the bot belongs to in one paginated pass.</p>
<p>The repair depends on one other field. If <code>is_private</code> is false, the bot can join itself with <code>conversations.join</code> and <code>channels:join</code>. If it is true, no API call joins it: a human member has to run <code>/invite @YourApp</code>.</p>""",
"problem": """<p>Installation and membership are separate things, and only the first one is visible in the app configuration. The OAuth screen lists scopes, the install succeeds, the token works, <code>auth.test</code> is happy &mdash; and the bot is in zero channels. Nothing in that flow suggests a step is missing.</p>
<p>It bites automated pipelines hardest. A channel created by Terraform or by a CI job exists, has the right name, appears in <code>conversations.list</code>, and has no bot in it, because channel creation and bot invitation are two separate calls and only the first one got automated. The alerting integration that posts into it looks configured and correct in every place a human would check.</p>
<p>And because the failure is a 200, the send queue records a success. The message that never arrived is not in a dead-letter queue anywhere; it was accepted, discarded, and logged as delivered.</p>""",
"why": """<p><strong>A bot is a member of a channel or it is not, independently of the install.</strong> Scopes govern what the app may do; membership governs where it may do it. <code>chat:write</code> on a token that is in no channels posts nowhere.</p>
<p><strong>Private channels cannot be self-joined, ever.</strong> <code>conversations.join</code> works on public channels only. For a private channel the sole route in is an invitation from someone already inside it, which means the fix is a message to a human rather than a code change.</p>
<p><strong><code>channel_not_found</code> is ambiguous on purpose.</strong> A token without <code>groups:read</code> cannot see private channels at all, so "this channel does not exist" and "I am not allowed to know whether it exists" come back as the same error. Do not report the first when you cannot rule out the second.</p>
<p><strong>Membership is lost as quietly as it is gained.</strong> Someone removes the app from a channel, or a public channel is converted to private and the bot loses access. Nothing notifies your code; the next post simply returns 200 with <code>not_in_channel</code> forever.</p>
<p><strong><code>chat:write.public</code> is not a general fix.</strong> It lets an app post to public channels without joining, which papers over posting. It does not grant history: <code>conversations.history</code> still returns <code>not_in_channel</code>.</p>""",
"steps": [
 {"h": "Get the bot's own user ID",
  "body": """<p><code>auth.test</code> returns <code>user_id</code> for the token in hand &mdash; for a bot token that is the bot user, the <code>U</code>/<code>W</code> id you will need in the <code>conversations.invite</code> that repairs this. It also confirms which workspace the token is actually pointed at, which is occasionally the whole answer.</p>"""},
 {"h": "Ask each target channel whether the bot is in it",
  "body": """<p><code>conversations.info?channel=&lt;C...&gt;</code> and read <code>channel.is_member</code>. This is a per-token answer, so it reports the truth about <em>this</em> credential rather than about the app in general.</p>"""},
 {"h": "Read is_archived before you read is_member",
  "body": """<p>An archived channel refuses posts from members and non-members alike. Reporting "not a member" for a channel that was archived six months ago sends someone to invite a bot into a room that no longer accepts anything.</p>"""},
 {"h": "Split the repair on is_private",
  "body": """<p>Public: <code>conversations.join</code> with <code>channels:join</code>, or an invite. Private: a human member must invite the app, and <code>groups:read</code> is needed before the script can even see the channel. These are different tickets for different people.</p>"""},
 {"h": "Sweep the whole set rather than one channel at a time",
  "body": """<p><code>users.conversations</code> for the bot user returns every conversation it belongs to, paginated. Diff that set against your configured target channels and you have the complete gap in one pass, which is the version worth putting on a schedule.</p>"""},
],
"verify": """<p>Invite the app, then re-run over the same channel list. Every channel should report <code>member</code>.</p>
<pre><code class="language-bash">python3 slack_channel_membership.py C0123ABCDEF C0456GHIJKL
# 2 channel(s) checked, 0 the bot cannot post to</code></pre>""",
"code_intro": "Two read methods, both GET: <code>auth.test</code> once for the bot user ID, then <code>conversations.info</code> per channel. The classifier is pure and takes the whole response rather than a boolean, because four of its six answers come from fields other than <code>is_member</code> &mdash; and because <code>ok: false</code> has to be handled here as carefully as everywhere else in this section.",
"py_file": "slack_channel_membership.py",
"py": '''"""Report Slack channels the bot cannot post to, and why.

Read only. GET requests and nothing else: give this a bot token with
channels:read and groups:read. The repair is printed, never performed, because
this token can post into your workspace.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_channel_membership")

API = "https://slack.com/api/"


def verdict(body):
    """Classify one conversations.info response. Pure, so it runs offline.

    Order matters: an archived channel refuses everyone, so it outranks
    membership, and ok: false outranks both because there is no channel object
    to read at all.
    """
    if body.get("ok") is not True:
        error = body.get("error") or "<no error field>"
        if error == "channel_not_found":
            return ("not-found",
                    "channel_not_found. Either the ID is wrong, or it is a private "
                    "channel this token cannot see. Those are indistinguishable "
                    "without groups:read.")
        if error == "missing_scope":
            return ("scope",
                    "missing_scope: needed=%s. Membership is unknown until the "
                    "token can read the channel." % (body.get("needed") or "?"))
        return ("error", "ok: false, error=%s" % error)

    channel = body.get("channel") or {}
    if channel.get("is_archived"):
        return ("archived",
                "archived. Membership is beside the point: an archived channel "
                "accepts nothing from anyone until it is unarchived.")
    if channel.get("is_member"):
        return ("member", "the bot is in this channel")
    if channel.get("is_private"):
        return ("not-member-private",
                "not a member, and private. No API call joins a private channel: "
                "a human member has to invite the app.")
    return ("not-member-public",
            "not a member. Public, so the app can join itself with channels:join, "
            "or somebody can invite it.")


def get(session, method, **params):
    r = session.get(API + method, params=params, timeout=30)
    body = r.json()
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+", help="channel IDs the app targets (C..., G...)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (channels:read and groups:read are enough)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    me = get(s, "auth.test")
    if me.get("ok") is not True:
        log.error("auth.test answered 200 with ok: false, error=%s", me.get("error"))
        return 2
    bot = me.get("user_id")
    log.info("token acts as %s (%s) in %s", me.get("user"), bot, me.get("team"))

    bad = 0
    for cid in args.channels:
        body = get(s, "conversations.info", channel=cid)
        state, detail = verdict(body)
        name = (body.get("channel") or {}).get("name", "?")
        line = "%-19s %-12s #%s  %s" % (state, cid, name, detail)
        if state == "member":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "not-member-public":
            log.warning("  repair: /invite @YourApp in #%s, or call conversations.join "
                        "with channels:join", name)
            log.warning("  in a pipeline: conversations.invite channel=%s users=%s",
                        cid, bot)
        elif state == "not-member-private":
            log.warning("  repair: a member of the private channel runs /invite @YourApp; "
                        "the app cannot let itself in")
        elif state == "archived":
            log.warning("  repair: unarchive the channel, or point the app at a live one")
        elif state == "not-found":
            log.warning("  repair: check the ID, then add groups:read and reinstall "
                        "if the channel is private")

    log.info("%d channel(s) checked, %d the bot cannot post to", len(args.channels), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-channel-membership.mjs",
"js": '''/**
 * Report Slack channels the bot cannot post to, and why.
 *
 * Read only. GET requests and nothing else: give this a bot token with
 * channels:read and groups:read. The repair is printed, never performed.
 */
const API = 'https://slack.com/api/';

/**
 * Classify one conversations.info response. Pure, so it runs offline.
 *
 * Order matters: an archived channel refuses everyone, so it outranks
 * membership, and ok: false outranks both because there is no channel object to
 * read at all.
 */
export function verdict(body) {
  if (body.ok !== true) {
    const error = body.error ?? '<no error field>';
    if (error === 'channel_not_found') {
      return ['not-found',
        'channel_not_found. Either the ID is wrong, or it is a private channel ' +
        'this token cannot see. Those are indistinguishable without groups:read.'];
    }
    if (error === 'missing_scope') {
      return ['scope',
        `missing_scope: needed=${body.needed ?? '?'}. Membership is unknown until ` +
        'the token can read the channel.'];
    }
    return ['error', `ok: false, error=${error}`];
  }

  const channel = body.channel ?? {};
  if (channel.is_archived) {
    return ['archived',
      'archived. Membership is beside the point: an archived channel accepts ' +
      'nothing from anyone until it is unarchived.'];
  }
  if (channel.is_member) return ['member', 'the bot is in this channel'];
  if (channel.is_private) {
    return ['not-member-private',
      'not a member, and private. No API call joins a private channel: a human ' +
      'member has to invite the app.'];
  }
  return ['not-member-public',
    'not a member. Public, so the app can join itself with channels:join, or ' +
    'somebody can invite it.'];
}

async function get(token, method, params = {}) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  return res.json();
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (channels:read and groups:read are enough)');
    process.exitCode = 2;
    return;
  }
  const channels = process.argv.slice(2).filter((a) => !a.startsWith('-'));
  if (channels.length === 0) {
    console.error('usage: node slack-channel-membership.mjs C0123ABCDEF [...]');
    process.exitCode = 2;
    return;
  }

  const me = await get(token, 'auth.test');
  if (me.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${me.error}`);
    process.exitCode = 2;
    return;
  }
  const bot = me.user_id;
  console.log(`token acts as ${me.user} (${bot}) in ${me.team}`);

  let bad = 0;
  for (const cid of channels) {
    const body = await get(token, 'conversations.info', { channel: cid });
    const [state, detail] = verdict(body);
    const name = body.channel?.name ?? '?';
    const line = `${state.padEnd(19)} ${cid.padEnd(12)} #${name}  ${detail}`;
    if (state === 'member') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'not-member-public') {
      console.warn(`  repair: /invite @YourApp in #${name}, or call conversations.join ` +
                   'with channels:join');
      console.warn(`  in a pipeline: conversations.invite channel=${cid} users=${bot}`);
    } else if (state === 'not-member-private') {
      console.warn('  repair: a member of the private channel runs /invite @YourApp; ' +
                   'the app cannot let itself in');
    } else if (state === 'archived') {
      console.warn('  repair: unarchive the channel, or point the app at a live one');
    } else if (state === 'not-found') {
      console.warn('  repair: check the ID, then add groups:read and reinstall if the ' +
                   'channel is private');
    }
  }

  console.log(`${channels.length} channel(s) checked, ${bad} the bot cannot post to`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry this one. An archived channel where the bot <em>is</em> a member still cannot be posted to, so archived has to be checked first; and <code>channel_not_found</code> has to stay ambiguous rather than being reported as &ldquo;the channel does not exist&rdquo;, because without <code>groups:read</code> a private channel returns exactly that error.",
"test_py_file": "test_slack_channel_membership.py",
"test_py": '''from slack_channel_membership import verdict


def ok(**channel):
    return {"ok": True, "channel": channel}


def test_member_of_a_live_channel_is_fine():
    state, _ = verdict(ok(name="alerts", is_member=True))
    assert state == "member"


def test_archived_outranks_membership():
    # A member of an archived channel still cannot post to it.
    state, detail = verdict(ok(name="old-alerts", is_member=True, is_archived=True))
    assert state == "archived"
    assert "unarchived" in detail


def test_public_channel_can_be_self_joined():
    state, detail = verdict(ok(name="general", is_member=False, is_private=False))
    assert state == "not-member-public"
    assert "channels:join" in detail


def test_private_channel_needs_a_human():
    state, detail = verdict(ok(name="secrets", is_member=False, is_private=True))
    assert state == "not-member-private"
    assert "invite" in detail


def test_channel_not_found_stays_ambiguous():
    state, detail = verdict({"ok": False, "error": "channel_not_found"})
    assert state == "not-found"
    assert "groups:read" in detail


def test_missing_scope_is_not_a_membership_answer():
    body = {"ok": False, "error": "missing_scope", "needed": "channels:read"}
    state, detail = verdict(body)
    assert state == "scope"
    assert "channels:read" in detail


def test_other_errors_are_not_reported_as_membership():
    assert verdict({"ok": False, "error": "invalid_auth"})[0] == "error"
''',
"test_js_file": "slack-channel-membership.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './slack-channel-membership.mjs';

const ok = (channel) => ({ ok: true, channel });

test('member of a live channel is fine', () => {
  assert.equal(verdict(ok({ name: 'alerts', is_member: true }))[0], 'member');
});

test('archived outranks membership', () => {
  const [state, detail] = verdict(ok({ name: 'old', is_member: true, is_archived: true }));
  assert.equal(state, 'archived');
  assert.match(detail, /unarchived/);
});

test('public channel can be self joined', () => {
  const [state, detail] = verdict(ok({ name: 'general', is_member: false, is_private: false }));
  assert.equal(state, 'not-member-public');
  assert.match(detail, /channels:join/);
});

test('private channel needs a human', () => {
  const [state, detail] = verdict(ok({ name: 'secrets', is_member: false, is_private: true }));
  assert.equal(state, 'not-member-private');
  assert.match(detail, /invite/);
});

test('channel_not_found stays ambiguous', () => {
  const [state, detail] = verdict({ ok: false, error: 'channel_not_found' });
  assert.equal(state, 'not-found');
  assert.match(detail, /groups:read/);
});

test('missing_scope is not a membership answer', () => {
  const [state, detail] = verdict({ ok: false, error: 'missing_scope', needed: 'channels:read' });
  assert.equal(state, 'scope');
  assert.match(detail, /channels:read/);
});

test('other errors are not reported as membership', () => {
  assert.equal(verdict({ ok: false, error: 'invalid_auth' })[0], 'error');
});
''',
"faq": [
 ("Why is my bot not in the channel when the app is installed?",
  "Because installing an app to a workspace grants it scopes, not memberships. A bot joins a channel only when somebody invites it with /invite @YourApp, or when it calls conversations.join itself, and that second option exists for public channels only."),
 ("Can the app join a private channel by itself?",
  "No. conversations.join is public-channel only, and there is no method that lets an app add itself to a private conversation. A human who is already in the channel has to invite it, which makes this the one Slack failure whose repair is a conversation rather than a deploy."),
 ("Why do I get channel_not_found for a channel I can see?",
  "Almost always because the token lacks groups:read and the channel is private. Slack does not distinguish 'no such channel' from 'not visible to you', deliberately, so a script cannot either. Add groups:read, reinstall, and re-run before concluding the ID is wrong."),
 ("Does chat:write.public solve this?",
  "Only for posting to public channels. It lets an app post without joining, but it grants nothing for reading: conversations.history on a channel the bot is not in still returns not_in_channel, so any integration that reads messages still needs a real membership."),
 ("How do I check every channel at once instead of one at a time?",
  "Call users.conversations for the bot user with types=public_channel,private_channel and paginate it fully. That returns every conversation the bot belongs to, so a diff against your configured target list gives you the whole gap in one pass."),
],
"related": [
 ("/slack/http-200-ok-false/", "Slack answers 200 and hides the failure in the body"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/pagination-not-followed/", "next_cursor ignored, so one page is all you see"),
],
"citations": [CITE_CONV_INFO, CITE_CONV_JOIN, CITE_CONV_MEMBERS, CITE_USERS_CONV],
},


{
"slug": "missing-scope-on-read",
"title": "missing_scope tells you the scope needed and the ones you have",
"description": "Slack names both needed and provided on a missing_scope error, and X-OAuth-Scopes lists the whole grant. Adding the scope is not enough: reinstall.",
"h1": "missing_scope tells you the scope needed and the ones you have",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack missing_scope", "slack needed provided scopes",
             "x-oauth-scopes header", "slack reinstall app scopes",
             "slack token scopes not updating"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>{\"ok\": false, \"error\": \"missing_scope\", \"needed\": \"channels:history\", \"provided\": \"chat:write,commands,users:read\"}</code>. The developer swears the scope is in the app configuration, and it is &mdash; but the app was never reinstalled, so the token in production still carries the grant it was issued with.",
"short_answer": """<p>Two probes, and Slack does most of the work. Read the <code>X-OAuth-Scopes</code> response header, which Slack returns on <em>every</em> Web API response with the calling token's complete current scope list. Then call each read method the app depends on and, on failure, read <code>body.needed</code> and <code>body.provided</code>.</p>
<p><code>needed</code> is an <strong>OR list</strong>, not an AND list: any one of the scopes it names satisfies the call. And the fix is never just "add the scope" &mdash; a token is a frozen snapshot of the grant at install time, so the app has to be reinstalled and the stored token replaced.</p>""",
"problem": """<p>This is the one place Slack is unusually generous. Most APIs tell you that you are not allowed to do something. Slack tells you exactly which scope would have allowed it, exactly which scopes you hold, and repeats the second list in a header on every response you have ever received. Almost nobody reads any of it, because the whole thing arrives inside a <code>200 OK</code>.</p>
<p>The half that costs real time is the install. Editing the scope list in the app configuration changes what will be <em>requested</em> at the next installation; it does not upgrade tokens that are already in circulation. So the config is right, the code is right, the error persists, and the missing step is one nobody wrote down: reinstall, then copy the new token into the deployment.</p>
<p>For a distributed app the same fact is much larger. Every existing installation keeps its old grant until each workspace re-authorizes, so a new scope means a re-consent campaign, not a deploy.</p>""",
"why": """<p><strong>A token is a snapshot, not a pointer.</strong> The scopes attached to a token are fixed at the moment it is issued. Nothing you change in the app configuration reaches backwards into tokens already issued, which is why "I added the scope" and "the token has the scope" are unrelated statements.</p>
<p><strong><code>needed</code> is an OR list.</strong> Slack often names several scopes that would each satisfy the call &mdash; <code>channels:history</code> or <code>groups:history</code>, say, depending on the conversation type. Adding all of them because they appeared in one error message is how a routine integration ends up over-scoped.</p>
<p><strong>Bot scopes and user scopes are separate lists.</strong> They are granted on the same consent screen and stored in the same OAuth response, so a scope added to User Token Scopes while the code authenticates with the <code>xoxb-</code> bot token produces <code>missing_scope</code> with the scope visibly present in the app configuration.</p>
<p><strong>Not every refusal is a scope refusal.</strong> <code>not_allowed_token_type</code> means the method wants a different class of token entirely; <code>invalid_auth</code> and <code>token_revoked</code> mean the credential is wrong or dead. Adding scopes and reinstalling changes none of those, and a scope audit that lumps them in sends people to the wrong screen.</p>
<p><strong>Removing a scope also needs a reinstall.</strong> Pruning an over-broad grant is the same operation in reverse: the live token keeps everything it was issued with until the app is installed again.</p>""",
"steps": [
 {"h": "Read X-OAuth-Scopes off any response",
  "body": """<p>Slack returns the calling token's full granted scope list in the <code>X-OAuth-Scopes</code> response header on every Web API call, successful or not. One <code>auth.test</code> gives you the complete inventory without guessing.</p>"""},
 {"h": "Probe the read methods the app actually depends on",
  "body": """<p>Call each one with harmless arguments &mdash; <code>limit=1</code> is plenty &mdash; and look at <code>body.error</code>. This is empirical rather than theoretical: it tells you what this token can do today, not what the documentation says it should be able to do.</p>"""},
 {"h": "Separate scope failures from credential failures",
  "body": """<p><code>missing_scope</code> is a permission gap. <code>invalid_auth</code>, <code>token_revoked</code>, <code>account_inactive</code> and <code>not_allowed_token_type</code> are not, and no amount of scope editing fixes them. Report them differently or the fix goes to the wrong place.</p>"""},
 {"h": "Read needed as a choice, not a shopping list",
  "body": """<p>Pick the narrowest scope in <code>needed</code> that covers the conversations you actually touch. If your app only reads public channels, <code>channels:history</code> alone is the answer even when <code>groups:history</code> and <code>im:history</code> are offered alongside it.</p>"""},
 {"h": "Add the scope, then reinstall, then replace the token",
  "body": """<p>OAuth &amp; Permissions &rarr; Bot Token Scopes, then reinstall to the workspace, then copy the new <code>xoxb-</code> token into the deployment. A manifest-managed app edits <code>oauth_config.scopes.bot</code> and deploys the manifest first. Skipping the third step leaves the old token in production and the error unchanged.</p>"""},
],
"verify": """<p>Re-run after reinstalling. Every probed method should report <code>ok</code>, and the granted list printed at the top should now contain the scope you added.</p>
<pre><code class="language-bash">python3 slack_scope_audit.py
# granted: 6 scope(s) on this token
# 6 method(s) probed, 0 blocked by a missing scope</code></pre>""",
"code_intro": "One GET per probed method, and the interesting part of each response is a header. Two pure functions: the header parser, because a scope list arrives as one comma-joined string with inconsistent spacing, and the verdict, which has to keep four kinds of refusal apart &mdash; a genuine scope gap, a credential problem wearing a scope error's clothes, a failure that has nothing to do with permissions, and a granted list that disagrees with the response it came from.",
"py_file": "slack_scope_audit.py",
"py": '''"""Audit which Slack read methods this token's scopes actually allow.

Read only. GET requests and nothing else: give this the bot token you deploy, so
the answer is about the credential in production. The repair is printed, never
performed, because this token can post into your workspace.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_scope_audit")

API = "https://slack.com/api/"

# Cheap read probes. Each one is refused by a different scope, so the set doubles
# as a map of what the token can reach.
PROBES = [
    ("auth.test", {}),
    ("conversations.list", {"limit": "1", "types": "public_channel"}),
    ("users.list", {"limit": "1"}),
    ("emoji.list", {}),
    ("usergroups.list", {}),
    ("team.info", {}),
]

# Refusals that are about the credential rather than the grant. Adding a scope
# and reinstalling does nothing for any of these.
CREDENTIAL_ERRORS = {
    "invalid_auth", "not_authed", "token_revoked", "token_expired",
    "account_inactive", "not_allowed_token_type",
}


def parse_scopes(header):
    """Split an X-OAuth-Scopes header into a sorted tuple. Pure.

    Slack sends one comma-joined string, and the header is absent from some
    proxied responses, so treat missing as "unknown" rather than "none".
    """
    if not header:
        return ()
    return tuple(sorted({s.strip() for s in header.split(",") if s.strip()}))


def verdict(granted, body):
    """Classify one probed method against a granted scope list. Pure.

    `granted` is what X-OAuth-Scopes reported; `body` is the parsed response.
    """
    if body.get("ok") is True:
        return ("ok", "allowed by the %d scope(s) this token holds" % len(granted))

    error = body.get("error") or "<no error field>"
    if error in CREDENTIAL_ERRORS:
        return ("wrong-token",
                "error=%s. This is the credential, not the grant: adding a scope "
                "and reinstalling will not change it." % error)
    if error != "missing_scope":
        return ("other",
                "error=%s, which is not a permission problem. Fix it before "
                "concluding anything about scopes." % error)

    needed = [s.strip() for s in (body.get("needed") or "").split(",") if s.strip()]
    if not needed:
        return ("missing-scope",
                "missing_scope, and the response did not name one. Read the "
                "method reference for its scope list.")
    already = [s for s in needed if s in granted]
    if already:
        return ("scope-list-mismatch",
                "missing_scope while the granted list already contains %s. The "
                "list and the token are not the same token: read X-OAuth-Scopes "
                "off this very response." % ", ".join(already))
    return ("missing-scope",
            "add any one of: %s. needed is an OR list, so one suffices, and the "
            "app must be reinstalled before the token carries it."
            % ", ".join(needed))


def probe(session, method, params):
    r = session.get(API + method, params=params, timeout=30)
    return r.headers.get("X-OAuth-Scopes"), r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", action="append", default=[],
                    help="probe this read method as well as the default set; repeatable")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (use the token the app actually deploys with)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    probes = PROBES + [(m, {}) for m in args.method]
    blocked = 0
    for method, params in probes:
        header, body = probe(s, method, params)
        granted = parse_scopes(header)
        state, detail = verdict(granted, body)
        if method == probes[0][0]:
            log.info("granted: %d scope(s) on this token: %s",
                     len(granted), ", ".join(granted) or "<header absent>")
        line = "%-19s %-20s %s" % (state, method, detail)
        if state == "ok":
            log.info(line)
            continue
        blocked += 1
        log.warning(line)
        if state == "missing-scope":
            log.warning("  provided=%s", body.get("provided") or "?")
            log.warning("  repair: OAuth & Permissions -> Bot Token Scopes, add the "
                        "scope, reinstall the app, replace the stored token")

    log.info("%d method(s) probed, %d refused", len(probes), blocked)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-scope-audit.mjs",
"js": '''/**
 * Audit which Slack read methods this token's scopes actually allow.
 *
 * Read only. GET requests and nothing else: give this the bot token you deploy,
 * so the answer is about the credential in production. The repair is printed,
 * never performed.
 */
const API = 'https://slack.com/api/';

// Cheap read probes. Each one is refused by a different scope, so the set
// doubles as a map of what the token can reach.
const PROBES = [
  ['auth.test', {}],
  ['conversations.list', { limit: '1', types: 'public_channel' }],
  ['users.list', { limit: '1' }],
  ['emoji.list', {}],
  ['usergroups.list', {}],
  ['team.info', {}],
];

// Refusals that are about the credential rather than the grant. Adding a scope
// and reinstalling does nothing for any of these.
const CREDENTIAL_ERRORS = new Set([
  'invalid_auth', 'not_authed', 'token_revoked', 'token_expired',
  'account_inactive', 'not_allowed_token_type',
]);

/**
 * Split an X-OAuth-Scopes header into a sorted array. Pure.
 * The header is absent from some proxied responses, so missing means unknown.
 */
export function parseScopes(header) {
  if (!header) return [];
  const set = new Set(header.split(',').map((s) => s.trim()).filter(Boolean));
  return [...set].sort();
}

/**
 * Classify one probed method against a granted scope list. Pure.
 */
export function verdict(granted, body) {
  if (body.ok === true) {
    return ['ok', `allowed by the ${granted.length} scope(s) this token holds`];
  }

  const error = body.error ?? '<no error field>';
  if (CREDENTIAL_ERRORS.has(error)) {
    return ['wrong-token',
      `error=${error}. This is the credential, not the grant: adding a scope and ` +
      'reinstalling will not change it.'];
  }
  if (error !== 'missing_scope') {
    return ['other',
      `error=${error}, which is not a permission problem. Fix it before ` +
      'concluding anything about scopes.'];
  }

  const needed = (body.needed ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  if (needed.length === 0) {
    return ['missing-scope',
      'missing_scope, and the response did not name one. Read the method ' +
      'reference for its scope list.'];
  }
  const already = needed.filter((s) => granted.includes(s));
  if (already.length) {
    return ['scope-list-mismatch',
      `missing_scope while the granted list already contains ${already.join(', ')}. ` +
      'The list and the token are not the same token: read X-OAuth-Scopes off ' +
      'this very response.'];
  }
  return ['missing-scope',
    `add any one of: ${needed.join(', ')}. needed is an OR list, so one suffices, ` +
    'and the app must be reinstalled before the token carries it.'];
}

async function probe(token, method, params) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  return { header: res.headers.get('x-oauth-scopes'), body: await res.json() };
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (use the token the app actually deploys with)');
    process.exitCode = 2;
    return;
  }

  const extra = process.argv.slice(2).filter((a) => !a.startsWith('-')).map((m) => [m, {}]);
  const probes = [...PROBES, ...extra];

  let blocked = 0;
  for (const [method, params] of probes) {
    const { header, body } = await probe(token, method, params);
    const granted = parseScopes(header);
    const [state, detail] = verdict(granted, body);
    if (method === probes[0][0]) {
      console.log(`granted: ${granted.length} scope(s) on this token: ` +
                  `${granted.join(', ') || '<header absent>'}`);
    }
    const line = `${state.padEnd(19)} ${method.padEnd(20)} ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    blocked += 1;
    console.warn(line);
    if (state === 'missing-scope') {
      console.warn(`  provided=${body.provided ?? '?'}`);
      console.warn('  repair: OAuth & Permissions -> Bot Token Scopes, add the scope, ' +
                   'reinstall the app, replace the stored token');
    }
  }

  console.log(`${probes.length} method(s) probed, ${blocked} refused`);
  process.exitCode = blocked ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests hold two lines that are easy to blur. <code>needed</code> is an OR list, so the advice has to be &ldquo;add one of these&rdquo; rather than &ldquo;add these&rdquo;; and a credential error is not a scope error, because sending someone to the scopes screen for an <code>invalid_auth</code> wastes an afternoon and a reinstall.",
"test_py_file": "test_slack_scope_audit.py",
"test_py": '''from slack_scope_audit import parse_scopes, verdict


def test_scope_header_is_split_and_trimmed():
    assert parse_scopes("channels:read, users:read ,chat:write") == (
        "channels:read", "chat:write", "users:read")


def test_absent_scope_header_is_empty_not_a_crash():
    assert parse_scopes(None) == ()
    assert parse_scopes("") == ()


def test_a_successful_call_needs_nothing():
    state, _ = verdict(("channels:read",), {"ok": True})
    assert state == "ok"


def test_missing_scope_names_the_alternatives_as_a_choice():
    body = {"ok": False, "error": "missing_scope",
            "needed": "channels:history,groups:history",
            "provided": "chat:write,users:read"}
    state, detail = verdict(("chat:write", "users:read"), body)
    assert state == "missing-scope"
    assert "any one of" in detail
    assert "channels:history" in detail
    assert "reinstalled" in detail


def test_credential_errors_are_not_scope_errors():
    state, detail = verdict((), {"ok": False, "error": "not_allowed_token_type"})
    assert state == "wrong-token"
    assert "will not change it" in detail


def test_unrelated_errors_do_not_become_scope_findings():
    state, _ = verdict(("channels:read",), {"ok": False, "error": "channel_not_found"})
    assert state == "other"


def test_missing_scope_without_a_needed_field_still_reports():
    state, detail = verdict((), {"ok": False, "error": "missing_scope"})
    assert state == "missing-scope"
    assert "did not name one" in detail


def test_a_granted_list_that_contradicts_the_response_is_its_own_state():
    body = {"ok": False, "error": "missing_scope", "needed": "channels:history"}
    state, detail = verdict(("channels:history",), body)
    assert state == "scope-list-mismatch"
    assert "X-OAuth-Scopes" in detail
''',
"test_js_file": "slack-scope-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseScopes, verdict } from './slack-scope-audit.mjs';

test('scope header is split and trimmed', () => {
  assert.deepEqual(parseScopes('channels:read, users:read ,chat:write'),
    ['channels:read', 'chat:write', 'users:read']);
});

test('absent scope header is empty not a crash', () => {
  assert.deepEqual(parseScopes(null), []);
  assert.deepEqual(parseScopes(''), []);
});

test('a successful call needs nothing', () => {
  assert.equal(verdict(['channels:read'], { ok: true })[0], 'ok');
});

test('missing_scope names the alternatives as a choice', () => {
  const body = {
    ok: false, error: 'missing_scope',
    needed: 'channels:history,groups:history',
    provided: 'chat:write,users:read',
  };
  const [state, detail] = verdict(['chat:write', 'users:read'], body);
  assert.equal(state, 'missing-scope');
  assert.match(detail, /any one of/);
  assert.match(detail, /channels:history/);
  assert.match(detail, /reinstalled/);
});

test('credential errors are not scope errors', () => {
  const [state, detail] = verdict([], { ok: false, error: 'not_allowed_token_type' });
  assert.equal(state, 'wrong-token');
  assert.match(detail, /will not change it/);
});

test('unrelated errors do not become scope findings', () => {
  assert.equal(verdict(['channels:read'], { ok: false, error: 'channel_not_found' })[0],
    'other');
});

test('missing_scope without a needed field still reports', () => {
  const [state, detail] = verdict([], { ok: false, error: 'missing_scope' });
  assert.equal(state, 'missing-scope');
  assert.match(detail, /did not name one/);
});

test('a granted list that contradicts the response is its own state', () => {
  const body = { ok: false, error: 'missing_scope', needed: 'channels:history' };
  const [state, detail] = verdict(['channels:history'], body);
  assert.equal(state, 'scope-list-mismatch');
  assert.match(detail, /X-OAuth-Scopes/);
});
''',
"faq": [
 ("I added the scope and still get missing_scope. Why?",
  "Because the token was issued before you added it. Scopes are frozen into a token at install time, and editing the app configuration only changes what will be requested at the next installation. Reinstall the app to the workspace and replace the stored token with the new one."),
 ("What is the difference between needed and provided?",
  "needed is the set of scopes that would have satisfied this call, as an OR list: any one of them is enough. provided is what the calling token currently holds. The same information as provided is on every response in the X-OAuth-Scopes header, including successful ones."),
 ("Should I add every scope listed in needed?",
  "No. Pick the narrowest one that covers the conversations you actually touch. needed often lists the public, private, DM and group-DM variants of the same capability, and adding all four is how an integration that reads one channel ends up with the whole workspace archive."),
 ("The scope is in the app configuration but the call still fails. What else could it be?",
  "Check which list it is in. Bot Token Scopes attach to the xoxb- token and User Token Scopes attach to the xoxp- token, and a scope granted to one does nothing for the other. Also check the error itself: not_allowed_token_type and invalid_auth are credential problems, not scope problems."),
 ("Do I have to reinstall to remove a scope too?",
  "Yes. Pruning is the same operation in reverse. The live token keeps everything it was issued with until the app is installed again, so a token that leaked before the prune still carries the old, wider grant."),
],
"related": [
 ("/slack/http-200-ok-false/", "Slack answers 200 and hides the failure in the body"),
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
 ("/slack/pagination-not-followed/", "next_cursor ignored, so one page is all you see"),
],
"citations": [CITE_SCOPES, CITE_INSTALL, CITE_TOKENS, CITE_WEBAPI],
},


{
"slug": "pagination-not-followed",
"title": "next_cursor is ignored so only the first page is ever seen",
"description": "A Slack list call returns 100 items and a cursor. Code that reads the array and stops loses the rest silently, with ok: true and no error anywhere.",
"h1": "next_cursor is ignored so only the first page is ever seen",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack next_cursor", "slack conversations.list only 100",
             "slack users.list pagination", "slack response_metadata cursor",
             "slack api missing channels"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The channel inventory has exactly 100 entries. So does the user directory. Nobody questions either number until somebody reports that a channel which plainly exists is missing from the report &mdash; and by then the sync has been dropping four fifths of the workspace every night for a year, with <code>ok: true</code> on every single response.",
"short_answer": """<p>Every Slack list method returns a <em>page</em>, defaulting to 100 items, with the continuation token in <code>response_metadata.next_cursor</code>. When that string is non-empty there is more data. Nothing else in the response says so.</p>
<p>Check for the shape: a first page of exactly your <code>limit</code> with a non-empty <code>next_cursor</code> is a truncation bug with near-certainty. Then paginate fully and compare the totals &mdash; the delta is exactly the data the application has never seen.</p>""",
"problem": """<p>This is silent data loss dressed as a healthy job. There is no error, no warning, no <code>ok: false</code>, no exception. The call succeeded; it simply answered a smaller question than the one that was asked. Everything downstream then behaves perfectly on 100 items out of 412.</p>
<p>What makes it survive review is that it looks right and, at first, is right. A workspace with 60 channels returns 60 and no cursor, so the code that reads <code>response.channels</code> and stops is correct on the day it is written and stays correct through every test. It breaks on the day the workspace crosses 100 channels, which is nobody's deploy and nobody's incident.</p>
<p>The consequences are unevenly distributed too. A user sync that misses a fifth of the directory silently fails to alert a fifth of the company; a channel audit that stops at 100 declares the rest of the workspace compliant without looking at it.</p>""",
"why": """<p><strong>The page size is a default, not a total.</strong> <code>conversations.list</code>, <code>users.list</code>, <code>conversations.members</code>, <code>conversations.history</code>, <code>files.list</code> and <code>users.conversations</code> all return 100 items unless you say otherwise, and all of them carry the continuation token in the same place.</p>
<p><strong>Only the cursor is authoritative.</strong> Slack explicitly does not guarantee a full page: a response can come back with fewer items than the limit and still have more pages behind it. Stopping when a page looks short is a heuristic that fails silently, and it fails in exactly the direction that loses data.</p>
<p><strong>Raising the limit is not a fix.</strong> <code>limit=1000</code> moves the cliff, it does not remove it &mdash; and asking for more than the documented maximum returns <code>invalid_limit</code>, which is at least loud. A workspace grows past whatever number you pick.</p>
<p><strong>Nothing about it looks like an error.</strong> <code>ok</code> is <code>true</code>, so error handling never triggers; this is the same structural fact behind every other note in this section, seen from the one angle where the body is not lying to you but merely incomplete.</p>""",
"steps": [
 {"h": "Call the list method the way your application calls it",
  "body": """<p>Same method, same <code>limit</code>, same filters. The finding you want is about the code in production, so a probe with a different page size answers a different question.</p>"""},
 {"h": "Read response_metadata.next_cursor, not the array length",
  "body": """<p>A non-empty cursor means there is more, full page or not. Treat an absent <code>response_metadata</code>, a null cursor and an empty string as the same thing: the end. Anything else is a page boundary you have not crossed yet.</p>"""},
 {"h": "Flag a full first page with a cursor as a bug, not a maybe",
  "body": """<p>Exactly <code>limit</code> items plus a cursor is the signature. It is possible for that to be a coincidence, and it almost never is: it is what every truncated read looks like from the outside.</p>"""},
 {"h": "Walk the whole thing once and measure the gap",
  "body": """<p>Paginate to the end with <code>limit=200</code> and count. The difference between that total and the first page is the number of channels, users or messages the application has never seen, and it is the only number that makes anyone fix this today rather than next quarter.</p>"""},
 {"h": "Replace the read with a loop, or with the SDK iterator",
  "body": """<p><code>while (cursor) { ... cursor = r.response_metadata?.next_cursor || null; }</code>. Both official SDKs ship this: <code>for await (const page of client.paginate('conversations.list', {...}))</code> in Node, <code>for page in client.conversations_list(limit=200)</code> in Python. Bound the loop by pages as well, so a cursor bug cannot spin forever.</p>"""},
],
"verify": """<p>Re-run after the loop is in place. The full walk and the application's own count should agree, and every probed method should report <code>complete</code>.</p>
<pre><code class="language-bash">python3 slack_pagination_audit.py --full
# 3 list method(s) probed, 0 truncated by a first-page-only read</code></pre>""",
"code_intro": "Paginated GETs and nothing else, with the page walk bounded by both a page count and a hard item cap so a large workspace cannot turn an audit into a rate-limit incident. Two pure functions: one that reads the cursor defensively, because it is absent, null and empty in three different situations that all mean the same thing, and one that separates the four shapes a first page can have.",
"py_file": "slack_pagination_audit.py",
"py": '''"""Report Slack list calls whose first page is not the whole answer.

Read only. GET requests and nothing else: give this a bot token with read
scopes. The repair is printed, never performed, because this token can post into
your workspace.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_pagination_audit")

API = "https://slack.com/api/"

# (method, params, key holding the items). Every one of these is cursor
# paginated and every one of them defaults to 100 items per page.
PAGED = [
    ("conversations.list", {"types": "public_channel,private_channel"}, "channels"),
    ("users.list", {}, "members"),
    ("users.conversations", {"types": "public_channel,private_channel"}, "channels"),
]


def cursor_of(body):
    """The continuation token, or "" when this page is the last one. Pure.

    Absent response_metadata, a null cursor and an empty string all mean the
    same thing, and only one of the three is obvious.
    """
    meta = body.get("response_metadata") or {}
    return (meta.get("next_cursor") or "").strip()


def verdict(count, limit, cursor, total=None):
    """Classify one first page. Pure, so it runs offline.

    `count` is the length of the first page, `limit` the page size the
    application asked for, `cursor` the value cursor_of() returned, and `total`
    the size of the full walk when one was performed.
    """
    delta = ""
    if total is not None:
        delta = (" Full walk: %d item(s), so a first-page-only read misses %d."
                 % (total, max(total - count, 0)))
    if cursor:
        if count >= limit:
            return ("truncated",
                    "a full page of %d with a cursor set. The application is "
                    "seeing %d of a larger number it never asked for.%s"
                    % (count, count, delta))
        return ("more-pages",
                "only %d item(s) but the cursor is set, so more pages follow. A "
                "short page is not the last page.%s" % (count, delta))
    if count >= limit:
        return ("complete-at-limit",
                "exactly %d item(s) and no cursor: complete today. Code that "
                "stops on a short page is right here by luck, and wrong on the "
                "next item added.%s" % (count, delta))
    return ("complete", "%d item(s), no cursor: this is the whole set.%s"
                        % (count, delta))


def get(session, method, params):
    r = session.get(API + method, params=params, timeout=30)
    return r.json()


def walk(session, method, params, key, max_pages, max_items):
    """Follow every cursor to the end, bounded twice."""
    total, cursor, pages = 0, "", 0
    while True:
        page = dict(params, limit="200")
        if cursor:
            page["cursor"] = cursor
        body = get(session, method, page)
        if body.get("ok") is not True:
            log.warning("  walk stopped: ok: false, error=%s", body.get("error"))
            return total
        total += len(body.get(key) or [])
        pages += 1
        cursor = cursor_of(body)
        if not cursor or pages >= max_pages or total >= max_items:
            return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=100,
                    help="the page size your application asks for (default 100)")
    ap.add_argument("--full", action="store_true",
                    help="follow every cursor and report how much is being missed")
    ap.add_argument("--max-pages", type=int, default=50, help="cap on the full walk")
    ap.add_argument("--max-items", type=int, default=10000, help="cap on the full walk")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        log.error("set SLACK_BOT_TOKEN (a bot token with read scopes is enough)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    bad = 0
    for method, params, key in PAGED:
        body = get(s, method, dict(params, limit=str(args.limit)))
        if body.get("ok") is not True:
            log.warning("%-18s %-22s ok: false, error=%s", "unreadable", method,
                        body.get("error"))
            bad += 1
            continue
        count = len(body.get(key) or [])
        cursor = cursor_of(body)
        total = walk(s, method, params, key, args.max_pages, args.max_items) \\
            if (args.full and cursor) else None
        state, detail = verdict(count, args.limit, cursor, total)
        line = "%-18s %-22s %s" % (state, method, detail)
        if state.startswith("complete"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: loop on response_metadata.next_cursor until it is "
                    "empty, or use the SDK paginator")

    log.info("%d list method(s) probed, %d truncated by a first-page-only read",
             len(PAGED), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-pagination-audit.mjs",
"js": '''/**
 * Report Slack list calls whose first page is not the whole answer.
 *
 * Read only. GET requests and nothing else: give this a bot token with read
 * scopes. The repair is printed, never performed.
 */
const API = 'https://slack.com/api/';

// [method, params, key holding the items]. Every one of these is cursor
// paginated and every one of them defaults to 100 items per page.
const PAGED = [
  ['conversations.list', { types: 'public_channel,private_channel' }, 'channels'],
  ['users.list', {}, 'members'],
  ['users.conversations', { types: 'public_channel,private_channel' }, 'channels'],
];

/**
 * The continuation token, or '' when this page is the last one. Pure.
 * Absent response_metadata, a null cursor and an empty string all mean the same
 * thing, and only one of the three is obvious.
 */
export function cursorOf(body) {
  return (body.response_metadata?.next_cursor ?? '').trim();
}

/**
 * Classify one first page. Pure, so it runs offline.
 */
export function verdict(count, limit, cursor, total = null) {
  const delta = total === null ? ''
    : ` Full walk: ${total} item(s), so a first-page-only read misses ` +
      `${Math.max(total - count, 0)}.`;
  if (cursor) {
    if (count >= limit) {
      return ['truncated',
        `a full page of ${count} with a cursor set. The application is seeing ` +
        `${count} of a larger number it never asked for.${delta}`];
    }
    return ['more-pages',
      `only ${count} item(s) but the cursor is set, so more pages follow. A short ` +
      `page is not the last page.${delta}`];
  }
  if (count >= limit) {
    return ['complete-at-limit',
      `exactly ${count} item(s) and no cursor: complete today. Code that stops on ` +
      `a short page is right here by luck, and wrong on the next item added.${delta}`];
  }
  return ['complete', `${count} item(s), no cursor: this is the whole set.${delta}`];
}

async function get(token, method, params) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  return res.json();
}

async function walk(token, method, params, key, maxPages, maxItems) {
  let total = 0; let cursor = ''; let pages = 0;
  for (;;) {
    const page = { ...params, limit: '200' };
    if (cursor) page.cursor = cursor;
    const body = await get(token, method, page);
    if (body.ok !== true) {
      console.warn(`  walk stopped: ok: false, error=${body.error}`);
      return total;
    }
    total += (body[key] ?? []).length;
    pages += 1;
    cursor = cursorOf(body);
    if (!cursor || pages >= maxPages || total >= maxItems) return total;
  }
}

async function main() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    console.error('set SLACK_BOT_TOKEN (a bot token with read scopes is enough)');
    process.exitCode = 2;
    return;
  }
  const argv = process.argv.slice(2);
  const limit = Number(argv.find((a) => a.startsWith('--limit='))?.split('=')[1] ?? 100);
  const full = argv.includes('--full');
  const maxPages = 50;
  const maxItems = 10000;

  let bad = 0;
  for (const [method, params, key] of PAGED) {
    const body = await get(token, method, { ...params, limit: String(limit) });
    if (body.ok !== true) {
      console.warn(`unreadable         ${method.padEnd(22)} ok: false, error=${body.error}`);
      bad += 1;
      continue;
    }
    const count = (body[key] ?? []).length;
    const cursor = cursorOf(body);
    const total = (full && cursor)
      ? await walk(token, method, params, key, maxPages, maxItems) : null;
    const [state, detail] = verdict(count, limit, cursor, total);
    const line = `${state.padEnd(18)} ${method.padEnd(22)} ${detail}`;
    if (state.startsWith('complete')) { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn('  repair: loop on response_metadata.next_cursor until it is empty, ' +
                 'or use the SDK paginator');
  }

  console.log(`${PAGED.length} list method(s) probed, ${bad} truncated by a ` +
              'first-page-only read');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and fail the suite on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two states worth keeping apart are the ones that look identical to a length check. A short page with a cursor still has pages behind it, and a full page with no cursor really is the end &mdash; which is why stopping on a short page is not a safe shortcut, and why being right about it once is not evidence of anything.",
"test_py_file": "test_slack_pagination_audit.py",
"test_py": '''from slack_pagination_audit import cursor_of, verdict


def test_absent_response_metadata_means_the_end():
    assert cursor_of({"ok": True, "channels": []}) == ""


def test_null_and_empty_cursors_mean_the_end_too():
    assert cursor_of({"response_metadata": {"next_cursor": None}}) == ""
    assert cursor_of({"response_metadata": {"next_cursor": "   "}}) == ""


def test_a_real_cursor_survives():
    assert cursor_of({"response_metadata": {"next_cursor": "dGVhbTpDMDYx"}}) == "dGVhbTpDMDYx"


def test_full_page_with_a_cursor_is_the_truncation_signature():
    state, detail = verdict(100, 100, "dGVhbTpD")
    assert state == "truncated"
    assert "100" in detail


def test_short_page_with_a_cursor_still_has_more():
    state, detail = verdict(37, 100, "dGVhbTpD")
    assert state == "more-pages"
    assert "not the last page" in detail


def test_full_page_without_a_cursor_is_complete_but_not_reassuring():
    state, detail = verdict(100, 100, "")
    assert state == "complete-at-limit"
    assert "luck" in detail


def test_short_page_without_a_cursor_is_the_whole_set():
    state, _ = verdict(42, 100, "")
    assert state == "complete"


def test_the_full_walk_reports_what_is_being_missed():
    _, detail = verdict(100, 100, "dGVhbTpD", total=412)
    assert "412" in detail
    assert "misses 312" in detail
''',
"test_js_file": "slack-pagination-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cursorOf, verdict } from './slack-pagination-audit.mjs';

test('absent response_metadata means the end', () => {
  assert.equal(cursorOf({ ok: true, channels: [] }), '');
});

test('null and empty cursors mean the end too', () => {
  assert.equal(cursorOf({ response_metadata: { next_cursor: null } }), '');
  assert.equal(cursorOf({ response_metadata: { next_cursor: '   ' } }), '');
});

test('a real cursor survives', () => {
  assert.equal(cursorOf({ response_metadata: { next_cursor: 'dGVhbTpDMDYx' } }),
    'dGVhbTpDMDYx');
});

test('full page with a cursor is the truncation signature', () => {
  const [state, detail] = verdict(100, 100, 'dGVhbTpD');
  assert.equal(state, 'truncated');
  assert.match(detail, /100/);
});

test('short page with a cursor still has more', () => {
  const [state, detail] = verdict(37, 100, 'dGVhbTpD');
  assert.equal(state, 'more-pages');
  assert.match(detail, /not the last page/);
});

test('full page without a cursor is complete but not reassuring', () => {
  const [state, detail] = verdict(100, 100, '');
  assert.equal(state, 'complete-at-limit');
  assert.match(detail, /luck/);
});

test('short page without a cursor is the whole set', () => {
  assert.equal(verdict(42, 100, '')[0], 'complete');
});

test('the full walk reports what is being missed', () => {
  const [, detail] = verdict(100, 100, 'dGVhbTpD', 412);
  assert.match(detail, /412/);
  assert.match(detail, /misses 312/);
});
''',
"faq": [
 ("Why does conversations.list only return 100 channels?",
  "Because 100 is the default page size, not the total. The rest is behind response_metadata.next_cursor, and Slack returns ok: true either way, so nothing about the response signals that you have seen a fraction of the workspace."),
 ("Can I just set limit=1000 and skip pagination?",
  "No. A larger limit moves the boundary rather than removing it, Slack recommends staying well below the maximum for reliability, and asking for more than the documented ceiling returns invalid_limit. The workspace will eventually be larger than whatever number you chose."),
 ("Is a page with fewer items than the limit always the last page?",
  "No, and this is the trap. Slack does not guarantee a full page, so a response can hold 37 items and still have a cursor. The cursor is the only authoritative signal; page length is a heuristic that fails quietly in the direction of losing data."),
 ("Which methods are cursor paginated?",
  "conversations.list, users.list, conversations.members, conversations.history, conversations.replies, users.conversations and files.list among others. They all carry the token in the same place, so one loop written once handles every one of them."),
 ("How do I know how much data I have been missing?",
  "Paginate to the end once and compare the total against the first page. That delta is the number of channels or users the application has never seen, and it is far more persuasive in a bug report than the observation that a cursor exists."),
],
"related": [
 ("/slack/http-200-ok-false/", "Slack answers 200 and hides the failure in the body"),
 ("/slack/missing-scope-on-read/", "missing_scope names the scope you need"),
 ("/slack/bot-not-in-channel/", "not_in_channel: the bot was never invited"),
],
"citations": [CITE_PAGINATION, CITE_CONV_LIST, CITE_USERS_LIST, CITE_WEBAPI],
},

]
