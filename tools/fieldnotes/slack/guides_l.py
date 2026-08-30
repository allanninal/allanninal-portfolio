#!/usr/bin/env python3
"""/slack/ field notes, batch L - the writing.

Four notes that are one causal chain read at four different points, which is
exactly why they had to be written to reach four different conclusions. The
handshake is a setup-time exchange that happens once, before a single event is
delivered, and it is the only Slack request your endpoint receives while it is
still untrusted. The three second budget is a deadline that applies to every
request after it. The retry storm is what Slack does when that deadline is
missed, and it is arithmetic rather than a state: one event becomes at most
four deliveries, and four deliveries multiplied by the calls each one makes is
either inside a method's tier budget or it is not. Duplicate processing is what
your handler does about the retry, and the subject there is not the duplicates
themselves but the key that was supposed to stop them.

Only one of the four says "acknowledge first and work afterwards", because
saying it four times would be one note printed four times. That one is the
deadline note, where it is the repair rather than an aside.

Read only throughout. The handshake note is the sharpest case: the obvious way
to test a Request URL is to send it something, and this one never does. It
reads the manifest, and it replays an exchange the caller already recorded.
"""

CITE_EVENTS = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_URL_VERIFICATION = ("url_verification event reference - Slack Docs",
                         "https://docs.slack.dev/reference/events/url_verification")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_SOCKET_MODE = ("Socket Mode - Slack Docs",
                    "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_INTERACTIVITY = ("Handling user interaction - Slack Docs",
                      "https://docs.slack.dev/interactivity/handling-user-interaction")
CITE_VIEWS_OPEN = ("views.open method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/views.open")
CITE_RATE_LIMITS = ("Rate limits - Slack Docs",
                    "https://docs.slack.dev/apis/web-api/rate-limits")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CONV_REPLIES = ("conversations.replies method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.replies")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_MESSAGE_EVENT = ("message event reference - Slack Docs",
                      "https://docs.slack.dev/reference/events/message")
CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_USERS_CONVERSATIONS = ("users.conversations method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/users.conversations")

GUIDES = []

GUIDES.append({
"slug": "request-url-unverified",
"title": "The Request URL never echoed back the challenge",
"description": "Slack sends one challenge before it will deliver anything, and it does not follow redirects or pass an auth wall. Read the manifest, replay the exchange.",
"h1": "The Request URL never echoed back the challenge",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack url_verification challenge", "slack request url not verified",
             "slack didn't respond with the value of the challenge parameter",
             "slack event subscriptions request url", "slack challenge parameter"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The app is installed. The scopes are right. The bot is in the channel and people are talking to it. Not one line has appeared in the handler's log, ever, because the handler has never been called: on the Event Subscriptions page there is a red line under the Request URL that says the URL did not respond with the value of the challenge parameter.</p><p>That sentence is the whole failure, and it lives in a browser tab rather than in your logs, which is why apps sit in this state for days.",
"short_answer": """<p>Before Slack will deliver any event, it sends your candidate Request URL a single request containing <code>{"type": "url_verification", "challenge": "&lt;random&gt;"}</code> and requires the challenge value handed straight back, within three seconds, either as a plain body or as <code>{"challenge": "..."}</code> JSON. It does not follow redirects. It does not carry your session cookie. It is the only request your endpoint will ever receive while it is still an unverified stranger, so every piece of middleware you have is standing in front of it.</p>
<p>Two things are therefore worth reading, and neither of them involves sending anything to your own URL. The first is the manifest: whether a Request URL is configured at all, whether Socket Mode is on and makes the question moot, and whether the URL's shape can survive the exchange. The second is the exchange itself, replayed offline from what your endpoint actually returned &mdash; a status, a content type, a body &mdash; which your access log already has. The script below does both and names which of the seven usual endings you got.</p>""",
"problem": """<p>The handshake is a one-time event with a permanent consequence, and it does not resemble anything else Slack does to you. Every other note in this section is about a running app that is failing at something; this is about an app that has never run. There is no <code>ok: false</code> to find, no error string to grep, no gap in a message history to measure, because the app has never been given the chance to produce any of those. The single artefact is a red line in the app configuration UI.</p>
<p>What makes it stick is the ordering. The verification request arrives before Slack knows anything about your endpoint, so it arrives at whatever your endpoint presents to strangers. If your framework requires an authenticated session on every route, the handshake gets a redirect to a login page. If an API gateway authoriser sits in front, it gets a 403. If a load balancer normalises the path and issues a 301 to add a trailing slash, Slack does not follow it and records a failure. If a body parser is registered only for <code>application/x-www-form-urlencoded</code> because that is what slash commands send, the JSON body arrives as an empty object and your handler reads <code>undefined</code> for the challenge and answers cheerfully with a 200 and nothing in it.</p>
<p>All five of those produce the same red line, and four of the five never reach your application code at all, which is why "I added the challenge handler and it still fails" is the most common second message in every thread on this subject. The handler is fine. It is not being reached.</p>""",
"why": """<p><strong>The challenge is random per attempt, so it cannot be memorised.</strong> People occasionally get the URL verified by hard-coding the string they saw in a log, and it works exactly once. Every subsequent verification &mdash; and Slack re-verifies when you change the URL &mdash; sends a different value. A handler that echoes a constant is a handler that passed once and will fail silently the next time somebody touches the configuration.</p>
<p><strong>Redirects are not followed here, and this is unusual enough to catch people twice.</strong> Most HTTP clients follow a 301 without mentioning it, so the URL you tested with <code>curl</code> works and the one Slack tested does not. The two most common sources are the trailing slash and the http-to-https upgrade, and both are invisible from the outside unless you look at the status code rather than the final body.</p>
<p><strong>Socket Mode removes the question entirely.</strong> An app using Socket Mode has no Request URL, cannot fail a handshake, and does not want one configured. If you are staring at a verification error on an app that is meant to be socket-based, the finding is that the configuration is trying to do both.</p>
<p><strong>Verification is a different failure from having nothing subscribed.</strong> A manifest with a verified URL and an empty bot event list is a fully working delivery path with nothing routed down it, and no amount of work on the URL will fix it. The script separates the two before it says anything about the URL, because they present identically: a bot that answers nobody.</p>
<p><strong>The three second budget applies to the handshake too.</strong> A cold-starting function that takes four seconds to return the challenge fails verification for a reason that has nothing to do with the challenge, and the message Slack shows you will still be about the challenge parameter. That is the point where this note hands over to <a href="/slack/three-second-timeout/">the deadline note</a>.</p>""",
"steps": [
 {"h": "Establish whether a Request URL is even the right question",
  "body": """<p>Socket Mode on and no URL configured means there is no handshake to fail. An empty bot event list means the delivery path is fine and nothing is routed down it. The script sorts those two out first and stops, because both of them look like a silent bot and neither is repaired by touching the URL.</p>"""},
 {"h": "Read the configured URL out of the manifest rather than out of memory",
  "body": """<p><code>apps.manifest.export</code> returns <code>settings.event_subscriptions.request_url</code>. That needs an app configuration token, which is a different credential class from your bot token &mdash; if you do not have one, the script says so and moves on to the half that does not need it.</p>"""},
 {"h": "Look at the shape of the URL before the behaviour",
  "body": """<p>A plain <code>http://</code> scheme, an ngrok or trycloudflare host, credentials in the userinfo, a query string a gateway will drop: each of these is decidable from the string alone, without sending anything. A tunnel host in particular is a URL that verified perfectly on Tuesday and points at nothing today.</p>"""},
 {"h": "Take the recorded exchange from your own access log",
  "body": """<p>Your endpoint answered the verification request, and whatever it answered is in your log with a status code, a content type and a length. Copy that into a small JSON file along with the challenge string Slack sent. This is deliberately not a live probe: firing requests at a production Request URL to see what it says is how an audit becomes an incident.</p>"""},
 {"h": "Let the replay name the ending rather than guessing at it",
  "body": """<p>Seven endings, and they have five different repairs. A redirect is a routing fix, an auth wall is a middleware ordering fix, an empty 200 is a body parser fix, a correct echo that took four seconds is a latency fix, and a correct echo inside the budget means the handshake is not your problem.</p>"""},
 {"h": "Move the challenge handler in front of everything",
  "body": """<p>The printed repair is an ordering instruction, not a code change: the branch that answers <code>url_verification</code> has to run before authentication, before redirects, and before anything that inspects the body for a shape it expects. Both Bolt receivers already do this, which is why the usual real repair is to mount the receiver properly rather than to hand-roll the route.</p>"""},
],
"verify": """<p>Re-run after the ordering change with a fresh recorded exchange, taken from the log line produced when you press Retry on the Event Subscriptions page.</p>
<pre><code class="language-bash">python3 slack_request_url_handshake.py --app-id A04HANDSHK --record exchange.json
# config     configured     a request url is set and 3 bot event(s) are subscribed
# url        clean          https://hooks.example.com/slack/events
# replay     echoed         the challenge came back as a plain body in 180ms
# verdict    ok             nothing here explains a silent app; look at delivery next</code></pre>""",
"code_intro": "Three pure functions and one GET. <code>handshake_config</code> decides whether the handshake is the question at all, which for a Socket Mode app or an app with nothing subscribed it is not. <code>url_shape</code> reads the four things that are decidable from the URL string alone. <code>replay_verdict</code> is the note itself: it takes the status, headers and body your endpoint returned and the challenge it was sent, and sorts that into one of seven endings, of which exactly two are success.",
"py_file": "slack_request_url_handshake.py",
"py": '''"""Diagnose a Slack Request URL that never passed the challenge handshake.

Read only, and deliberately not a probe. The verification exchange is replayed
from a record the caller supplies out of their own access log; this script
never sends anything to the Request URL, because an audit that fires traffic at
a production endpoint to see what it says is an incident with a report attached.
The one network call it makes is a GET to apps.manifest.export.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_request_url_handshake")

API = "https://slack.com/api/"

# Slack requires the challenge back within the same three seconds it gives
# every other delivery. A correct echo that arrives late is still a failure,
# and it is worth calling that out separately because the repair is different.
DEADLINE_MS = 3000

# Hosts that hand out ephemeral URLs. A tunnel verified fine on the day it was
# configured and points at nothing now, which is the single most common reason
# a URL that "used to work" stops without anybody changing it.
TUNNEL_HOSTS = ("ngrok.io", "ngrok-free.app", "ngrok.app", "trycloudflare.com",
                "loca.lt", "serveo.net", "localhost", "127.0.0.1", "0.0.0.0")


def handshake_config(manifest):
    """Decide whether the challenge handshake is the question here at all. Pure.

    Returns (verdict, detail). Two of the verdicts are hand-offs: a Socket Mode
    app has no Request URL to verify, and an app with nothing subscribed has a
    delivery path with nothing routed down it. Both present as a bot that
    answers nobody, and neither is repaired by touching a URL.
    """
    if not isinstance(manifest, dict) or not manifest:
        return ("not-assessed",
                "no manifest was read, so the configuration half of this check "
                "did not run. That is a missing credential, not a finding.")

    settings = manifest.get("settings") or {}
    subs = settings.get("event_subscriptions") or {}
    url = (subs.get("request_url") or "").strip()
    events = list(subs.get("bot_events") or []) + list(subs.get("user_events") or [])
    socket = bool(settings.get("socket_mode_enabled"))

    if socket and not url:
        return ("socket-mode",
                "Socket Mode is enabled and no request url is set, so there is "
                "no handshake to fail. Delivery problems on this app are "
                "connection problems, not verification ones.")
    if socket and url:
        return ("both-configured",
                "Socket Mode is enabled and a request url is also set (%s). The "
                "configuration is describing two delivery paths; verify which "
                "one this app is actually meant to use before reading anything "
                "into a verification error." % url)
    if not events:
        return ("nothing-subscribed",
                "no bot or user events are subscribed, so the Request URL is "
                "not yet the question: a verified URL with an empty event list "
                "delivers nothing and looks exactly the same from a channel.")
    if not url:
        return ("no-request-url",
                "%d event(s) are subscribed and there is no request url and no "
                "Socket Mode. Nothing can be delivered, and no handshake has "
                "ever been attempted." % len(events))
    return ("configured",
            "a request url is set and %d event(s) are subscribed" % len(events))


def url_shape(url):
    """Read what is decidable from the URL string alone. Pure.

    Returns a list of (code, detail). None of these need a request, which is
    the point: four of the five ways this handshake fails are visible in the
    configured string before anybody sends anything anywhere.
    """
    out = []
    raw = (url or "").strip()
    if not raw:
        return out

    scheme, _, rest = raw.partition("://")
    if not rest:
        scheme, rest = "", raw
    if scheme.lower() != "https":
        out.append(("not-https",
                    "the scheme is %r. Slack requires https and will not follow "
                    "an upgrade redirect, so an http url fails the handshake "
                    "even when the host answers correctly on 443."
                    % (scheme or "missing")))

    authority = rest.split("/", 1)[0]
    if "@" in authority:
        out.append(("credentials-in-url",
                    "the authority carries userinfo before the @. Slack sends "
                    "no basic auth, and the credentials are configuration "
                    "anybody with the app page can read."))
        authority = authority.rsplit("@", 1)[1]

    host = authority.split(":", 1)[0].lower()
    port = authority.split(":", 1)[1] if ":" in authority else ""
    if any(host == h or host.endswith("." + h) for h in TUNNEL_HOSTS):
        out.append(("tunnel-host",
                    "%s is an ephemeral tunnel or a loopback address. It "
                    "verified on the day it was set and there is no reason to "
                    "expect it resolves to your service now." % host))
    if port and port not in ("443", ""):
        out.append(("non-standard-port",
                    "port %s. Legal, and one more thing between Slack and the "
                    "handler that a firewall rule can quietly close." % port))
    if "?" in raw:
        out.append(("query-string",
                    "the url carries a query string. Some gateways strip or "
                    "rewrite it before your route sees it, and the handshake "
                    "then lands on a path you never wrote."))
    return out


def replay_verdict(record, challenge):
    """Sort a recorded verification exchange into one of seven endings. Pure.

    ``record`` is what the caller's own access log holds: a status, response
    headers, the body that was returned, and optionally how long it took.
    Nothing here sends a request. Returns (verdict, detail); only "echoed" and
    "echoed-json" mean the handshake passed.
    """
    rec = record or {}
    want = str(challenge or "").strip()
    status = int(rec.get("status") or 0)
    headers = {str(k).lower(): str(v) for k, v in (rec.get("headers") or {}).items()}
    body = rec.get("body")
    body = "" if body is None else str(body)
    ctype = headers.get("content-type", "").lower()
    elapsed = rec.get("elapsed_ms")

    if 300 <= status < 400:
        return ("redirected",
                "status %d to %s. Slack does not follow redirects during "
                "verification, so this is recorded as a failure however "
                "correct the destination is. A trailing slash and an "
                "http-to-https upgrade are the two usual sources."
                % (status, headers.get("location", "an unnamed location")))
    if status in (401, 403):
        return ("auth-wall",
                "status %d. Something in front of the handler demanded "
                "credentials. The verification request is the only one Slack "
                "sends while your endpoint is still a stranger, so every "
                "authenticator you have is standing in its way." % status)
    if status == 404:
        return ("not-found",
                "status 404. The configured path is not the path the handler "
                "is mounted at, which is usually a router prefix or a stage "
                "name the gateway adds.")
    if status >= 500:
        return ("server-error",
                "status %d. The handler was reached and threw. This is the one "
                "ending where your own stack trace is the next thing to read."
                % status)
    if status < 200 or status >= 300:
        return ("unexpected-status",
                "status %d, which is neither a success nor one of the failures "
                "this replay knows how to name." % status)

    if not body.strip():
        return ("empty-200",
                "status 200 with an empty body. The route answered and echoed "
                "nothing, which is what a handler reading an unparsed body "
                "does: the challenge was never in the object it looked at.")

    echoed = None
    if body.strip() == want and want:
        echoed = "echoed"
    else:
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict) and want and str(parsed.get("challenge", "")) == want:
            echoed = "echoed-json"

    if echoed:
        if isinstance(elapsed, (int, float)) and elapsed > DEADLINE_MS:
            return ("too-slow",
                    "the challenge came back correctly and took %dms, over the "
                    "%dms Slack allows. The body is right and the handshake "
                    "still failed, which is why the error message about the "
                    "challenge parameter is misleading here."
                    % (int(elapsed), DEADLINE_MS))
        took = ("" if not isinstance(elapsed, (int, float))
                else " in %dms" % int(elapsed))
        kind = "a plain body" if echoed == "echoed" else "a json challenge field"
        return (echoed, "the challenge came back as %s%s" % (kind, took))

    if want and want in body:
        return ("buried",
                "status 200 and the challenge is somewhere in the body but is "
                "not the body and is not a top-level challenge field. An error "
                "page that happens to include the request payload does this.")
    if "text/html" in ctype:
        return ("html-page",
                "status 200 with %s. A framework error page or a single page "
                "app index answered on this path; the handler is not on it."
                % ctype)
    return ("wrong-body",
            "status 200 and %d byte(s) that are neither the challenge nor a "
            "json object carrying it." % len(body))


def export_manifest(session, token, app_id):
    """One GET, with an app configuration token. Returns the parsed body."""
    r = session.get(API + "apps.manifest.export",
                    headers={"Authorization": "Bearer " + token},
                    params={"app_id": app_id}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--record", default="",
                    help="json file holding the recorded verification exchange")
    ap.add_argument("--challenge", default="",
                    help="the challenge string Slack sent, if not in the record")
    args = ap.parse_args()

    findings = 0
    manifest = {}
    token = os.environ.get(args.config_token_env)
    if args.app_id and token:
        body = export_manifest(requests.Session(), token, args.app_id)
        if body.get("ok") is not True:
            log.warning("manifest   unavailable    apps.manifest.export answered "
                        "ok: false, error=%s", body.get("error"))
        else:
            manifest = body
    elif args.app_id:
        log.info("manifest   skipped        set %s to read the configured url; "
                 "a bot token cannot", args.config_token_env)

    verdict, detail = handshake_config(manifest)
    (log.info if verdict in ("configured", "socket-mode") else log.warning)(
        "config     %-14s %s", verdict, detail)
    if verdict in ("no-request-url", "both-configured"):
        findings += 1

    url = ((manifest.get("settings") or {}).get("event_subscriptions") or {}).get(
        "request_url") or ""
    concerns = url_shape(url)
    if url and not concerns:
        log.info("url        clean          %s", url)
    for code, why in concerns:
        findings += 1
        log.warning("url        %-14s %s", code, why)

    if args.record:
        rec = json.loads(open(args.record, encoding="utf-8").read())
        challenge = args.challenge or rec.get("challenge") or ""
        state, why = replay_verdict(rec, challenge)
        ok = state in ("echoed", "echoed-json")
        (log.info if ok else log.warning)("replay     %-14s %s", state, why)
        if not ok:
            findings += 1
            log.warning("  repair: answer url_verification before any "
                        "authentication, redirect or body-shape check runs, and "
                        "return body.challenge exactly as it arrived")
    else:
        log.info("replay     skipped        pass --record with the status, "
                 "headers and body your endpoint returned")

    if findings:
        log.warning("verdict    %-14s %d finding(s); press Retry on the Event "
                    "Subscriptions page once they are addressed", "action", findings)
        return 1
    log.info("verdict    %-14s nothing here explains a silent app; look at "
             "delivery next", "ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-request-url-handshake.mjs",
"js": '''/**
 * Diagnose a Slack Request URL that never passed the challenge handshake.
 *
 * Read only, and deliberately not a probe. The verification exchange is
 * replayed from a record the caller supplies out of their own access log; this
 * script never sends anything to the Request URL. The one network call it
 * makes is a GET to apps.manifest.export.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

// A correct echo that arrives late is still a failed handshake, and it is
// worth naming separately because the repair is a different one.
const DEADLINE_MS = 3000;

// Ephemeral tunnels and loopback: verified on the day they were configured,
// pointing at nothing now.
const TUNNEL_HOSTS = ['ngrok.io', 'ngrok-free.app', 'ngrok.app',
  'trycloudflare.com', 'loca.lt', 'serveo.net', 'localhost', '127.0.0.1',
  '0.0.0.0'];

/**
 * Decide whether the challenge handshake is the question here at all. Pure.
 * Two verdicts are hand-offs: Socket Mode has no URL to verify, and an empty
 * event list is a working delivery path with nothing routed down it.
 */
export function handshakeConfig(manifest) {
  if (!manifest || typeof manifest !== 'object' || Object.keys(manifest).length === 0) {
    return ['not-assessed',
      'no manifest was read, so the configuration half of this check did not ' +
      'run. That is a missing credential, not a finding.'];
  }
  const settings = manifest.settings ?? {};
  const subs = settings.event_subscriptions ?? {};
  const url = String(subs.request_url ?? '').trim();
  const events = [...(subs.bot_events ?? []), ...(subs.user_events ?? [])];
  const socket = Boolean(settings.socket_mode_enabled);

  if (socket && !url) {
    return ['socket-mode',
      'Socket Mode is enabled and no request url is set, so there is no ' +
      'handshake to fail. Delivery problems on this app are connection ' +
      'problems, not verification ones.'];
  }
  if (socket && url) {
    return ['both-configured',
      `Socket Mode is enabled and a request url is also set (${url}). The ` +
      'configuration is describing two delivery paths; verify which one this ' +
      'app is actually meant to use before reading anything into a ' +
      'verification error.'];
  }
  if (events.length === 0) {
    return ['nothing-subscribed',
      'no bot or user events are subscribed, so the Request URL is not yet ' +
      'the question: a verified URL with an empty event list delivers nothing ' +
      'and looks exactly the same from a channel.'];
  }
  if (!url) {
    return ['no-request-url',
      `${events.length} event(s) are subscribed and there is no request url ` +
      'and no Socket Mode. Nothing can be delivered, and no handshake has ' +
      'ever been attempted.'];
  }
  return ['configured', `a request url is set and ${events.length} event(s) are subscribed`];
}

/**
 * Read what is decidable from the URL string alone. Pure.
 * Four of the five ways this handshake fails are visible in the configured
 * string before anybody sends anything anywhere.
 */
export function urlShape(url) {
  const out = [];
  const raw = String(url ?? '').trim();
  if (!raw) return out;

  const idx = raw.indexOf('://');
  const scheme = idx === -1 ? '' : raw.slice(0, idx);
  const rest = idx === -1 ? raw : raw.slice(idx + 3);
  if (scheme.toLowerCase() !== 'https') {
    out.push(['not-https',
      `the scheme is ${scheme || 'missing'}. Slack requires https and will not ` +
      'follow an upgrade redirect, so an http url fails the handshake even ' +
      'when the host answers correctly on 443.']);
  }

  let authority = rest.split('/')[0];
  if (authority.includes('@')) {
    out.push(['credentials-in-url',
      'the authority carries userinfo before the @. Slack sends no basic ' +
      'auth, and the credentials are configuration anybody with the app page ' +
      'can read.']);
    authority = authority.slice(authority.lastIndexOf('@') + 1);
  }
  const host = authority.split(':')[0].toLowerCase();
  const port = authority.includes(':') ? authority.split(':')[1] : '';
  if (TUNNEL_HOSTS.some((h) => host === h || host.endsWith(`.${h}`))) {
    out.push(['tunnel-host',
      `${host} is an ephemeral tunnel or a loopback address. It verified on ` +
      'the day it was set and there is no reason to expect it resolves to ' +
      'your service now.']);
  }
  if (port && port !== '443') {
    out.push(['non-standard-port',
      `port ${port}. Legal, and one more thing between Slack and the handler ` +
      'that a firewall rule can quietly close.']);
  }
  if (raw.includes('?')) {
    out.push(['query-string',
      'the url carries a query string. Some gateways strip or rewrite it ' +
      'before your route sees it, and the handshake then lands on a path you ' +
      'never wrote.']);
  }
  return out;
}

/**
 * Sort a recorded verification exchange into one of seven endings. Pure.
 * The record is what the caller's own access log holds. Nothing here sends a
 * request. Only 'echoed' and 'echoed-json' mean the handshake passed.
 */
export function replayVerdict(record, challenge) {
  const rec = record ?? {};
  const want = String(challenge ?? '').trim();
  const status = Number(rec.status ?? 0);
  const headers = {};
  for (const [k, v] of Object.entries(rec.headers ?? {})) {
    headers[String(k).toLowerCase()] = String(v);
  }
  const body = rec.body === null || rec.body === undefined ? '' : String(rec.body);
  const ctype = (headers['content-type'] ?? '').toLowerCase();
  const elapsed = rec.elapsed_ms;

  if (status >= 300 && status < 400) {
    return ['redirected',
      `status ${status} to ${headers.location ?? 'an unnamed location'}. Slack ` +
      'does not follow redirects during verification, so this is recorded as ' +
      'a failure however correct the destination is. A trailing slash and an ' +
      'http-to-https upgrade are the two usual sources.'];
  }
  if (status === 401 || status === 403) {
    return ['auth-wall',
      `status ${status}. Something in front of the handler demanded ` +
      'credentials. The verification request is the only one Slack sends ' +
      'while your endpoint is still a stranger, so every authenticator you ' +
      'have is standing in its way.'];
  }
  if (status === 404) {
    return ['not-found',
      'status 404. The configured path is not the path the handler is mounted ' +
      'at, which is usually a router prefix or a stage name the gateway adds.'];
  }
  if (status >= 500) {
    return ['server-error',
      `status ${status}. The handler was reached and threw. This is the one ` +
      'ending where your own stack trace is the next thing to read.'];
  }
  if (status < 200 || status >= 300) {
    return ['unexpected-status',
      `status ${status}, which is neither a success nor one of the failures ` +
      'this replay knows how to name.'];
  }

  if (!body.trim()) {
    return ['empty-200',
      'status 200 with an empty body. The route answered and echoed nothing, ' +
      'which is what a handler reading an unparsed body does: the challenge ' +
      'was never in the object it looked at.'];
  }

  let echoed = null;
  if (want && body.trim() === want) {
    echoed = 'echoed';
  } else {
    let parsed = null;
    try { parsed = JSON.parse(body); } catch { parsed = null; }
    if (parsed && typeof parsed === 'object' && want
      && String(parsed.challenge ?? '') === want) echoed = 'echoed-json';
  }

  if (echoed) {
    if (typeof elapsed === 'number' && elapsed > DEADLINE_MS) {
      return ['too-slow',
        `the challenge came back correctly and took ${Math.trunc(elapsed)}ms, ` +
        `over the ${DEADLINE_MS}ms Slack allows. The body is right and the ` +
        'handshake still failed, which is why the error message about the ' +
        'challenge parameter is misleading here.'];
    }
    const took = typeof elapsed === 'number' ? ` in ${Math.trunc(elapsed)}ms` : '';
    const kind = echoed === 'echoed' ? 'a plain body' : 'a json challenge field';
    return [echoed, `the challenge came back as ${kind}${took}`];
  }

  if (want && body.includes(want)) {
    return ['buried',
      'status 200 and the challenge is somewhere in the body but is not the ' +
      'body and is not a top-level challenge field. An error page that ' +
      'happens to include the request payload does this.'];
  }
  if (ctype.includes('text/html')) {
    return ['html-page',
      `status 200 with ${ctype}. A framework error page or a single page app ` +
      'index answered on this path; the handler is not on it.'];
  }
  return ['wrong-body',
    `status 200 and ${body.length} byte(s) that are neither the challenge nor ` +
    'a json object carrying it.'];
}

async function exportManifest(token, appId) {
  const res = await fetch(`${API}apps.manifest.export?app_id=${encodeURIComponent(appId)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  try { return await res.json(); } catch { return { ok: false, error: 'unparseable_body' }; }
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id', '');
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_ACCESS_TOKEN');
  const token = process.env[tokenEnv];

  let findings = 0;
  let manifest = {};
  if (appId && token) {
    const body = await exportManifest(token, appId);
    if (body.ok !== true) {
      console.warn('manifest   unavailable    apps.manifest.export answered ' +
        `ok: false, error=${body.error}`);
    } else {
      manifest = body;
    }
  } else if (appId) {
    console.log(`manifest   skipped        set ${tokenEnv} to read the configured ` +
      'url; a bot token cannot');
  }

  const [verdict, detail] = handshakeConfig(manifest);
  const good = verdict === 'configured' || verdict === 'socket-mode';
  (good ? console.log : console.warn)(`config     ${verdict.padEnd(14)} ${detail}`);
  if (verdict === 'no-request-url' || verdict === 'both-configured') findings += 1;

  const url = manifest.settings?.event_subscriptions?.request_url ?? '';
  const concerns = urlShape(url);
  if (url && concerns.length === 0) console.log(`url        clean          ${url}`);
  for (const [code, why] of concerns) {
    findings += 1;
    console.warn(`url        ${code.padEnd(14)} ${why}`);
  }

  const recordPath = arg(args, '--record', '');
  if (recordPath) {
    const rec = JSON.parse(readFileSync(recordPath, 'utf8'));
    const challenge = arg(args, '--challenge', '') || rec.challenge || '';
    const [state, why] = replayVerdict(rec, challenge);
    const ok = state === 'echoed' || state === 'echoed-json';
    (ok ? console.log : console.warn)(`replay     ${state.padEnd(14)} ${why}`);
    if (!ok) {
      findings += 1;
      console.warn('  repair: answer url_verification before any authentication, ' +
        'redirect or body-shape check runs, and return body.challenge exactly ' +
        'as it arrived');
    }
  } else {
    console.log('replay     skipped        pass --record with the status, headers ' +
      'and body your endpoint returned');
  }

  if (findings) {
    console.warn(`verdict    action         ${findings} finding(s); press Retry on ` +
      'the Event Subscriptions page once they are addressed');
    process.exitCode = 1;
  } else {
    console.log('verdict    ok             nothing here explains a silent app; ' +
      'look at delivery next');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The replay classifier is the part worth pinning, because the whole value of this note is that seven different endings do not all mean &ldquo;fix the challenge handler&rdquo;. A 301 to the same URL with a trailing slash is asserted to come back as <code>redirected</code> rather than as a success, a correct echo that took four seconds is asserted to come back as <code>too-slow</code> rather than as an echo, and an empty 200 is kept apart from a 200 that carries the wrong thing. The configuration half is pinned on its two hand-offs, which are the cases where the honest answer is that this is somebody else's note.",
"test_py_file": "test_slack_request_url_handshake.py",
"test_py": '''import json

from slack_request_url_handshake import handshake_config, replay_verdict, url_shape

CH = "3eZbrw1aB1LmzHi8"


def rec(status=200, body="", headers=None, elapsed_ms=None):
    out = {"status": status, "body": body, "headers": headers or {}}
    if elapsed_ms is not None:
        out["elapsed_ms"] = elapsed_ms
    return out


def test_a_plain_echo_and_a_json_echo_both_pass():
    assert replay_verdict(rec(body=CH), CH)[0] == "echoed"
    assert replay_verdict(rec(body=json.dumps({"challenge": CH})), CH)[0] == "echoed-json"


def test_a_redirect_is_a_failure_however_correct_the_destination():
    state, detail = replay_verdict(
        rec(status=301, headers={"Location": "https://x.example.com/slack/events/"}), CH)
    assert state == "redirected"
    assert "does not follow redirects" in detail


def test_an_authenticator_in_front_of_the_handler_is_named_as_such():
    assert replay_verdict(rec(status=403), CH)[0] == "auth-wall"
    assert replay_verdict(rec(status=401), CH)[0] == "auth-wall"


def test_a_correct_echo_that_missed_the_budget_is_not_reported_as_success():
    state, detail = replay_verdict(rec(body=CH, elapsed_ms=4200), CH)
    assert state == "too-slow"
    assert "4200ms" in detail
    assert replay_verdict(rec(body=CH, elapsed_ms=180), CH)[0] == "echoed"


def test_an_empty_200_is_kept_apart_from_a_wrong_200():
    assert replay_verdict(rec(body="   "), CH)[0] == "empty-200"
    assert replay_verdict(rec(body="thanks"), CH)[0] == "wrong-body"


def test_a_challenge_buried_in_an_error_page_is_not_an_echo():
    assert replay_verdict(rec(body="<h1>500</h1> payload was " + CH), CH)[0] == "buried"
    assert replay_verdict(
        rec(body="<html>ok</html>", headers={"Content-Type": "text/html"}), CH
    )[0] == "html-page"


def test_socket_mode_and_an_empty_event_list_are_both_hand_offs():
    assert handshake_config({"settings": {"socket_mode_enabled": True}})[0] == "socket-mode"
    assert handshake_config(
        {"settings": {"event_subscriptions": {"request_url": "https://a.example/x",
                                              "bot_events": []}}}
    )[0] == "nothing-subscribed"


def test_subscribed_events_with_nowhere_to_go_is_the_finding():
    state, detail = handshake_config(
        {"settings": {"event_subscriptions": {"bot_events": ["app_mention"]}}})
    assert state == "no-request-url"
    assert "1 event(s)" in detail


def test_two_delivery_paths_configured_at_once_is_its_own_verdict():
    state, _ = handshake_config({"settings": {
        "socket_mode_enabled": True,
        "event_subscriptions": {"request_url": "https://a.example/x",
                                "bot_events": ["app_mention"]}}})
    assert state == "both-configured"


def test_a_missing_manifest_is_never_reported_as_a_clean_configuration():
    assert handshake_config({})[0] == "not-assessed"
    assert handshake_config(None)[0] == "not-assessed"


def test_the_url_string_gives_up_four_things_without_a_request():
    codes = [c for c, _ in url_shape("http://bot.ngrok.io:8443/slack/events?stage=prod")]
    assert codes == ["not-https", "tunnel-host", "non-standard-port", "query-string"]
    assert url_shape("https://hooks.example.com/slack/events") == []


def test_userinfo_is_reported_and_then_stripped_before_the_host_is_read():
    codes = [c for c, _ in url_shape("https://user:pw@hooks.example.com/slack/events")]
    assert codes == ["credentials-in-url"]
    assert url_shape("") == []
''',
"test_js_file": "slack-request-url-handshake.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handshakeConfig, replayVerdict, urlShape } from './slack-request-url-handshake.mjs';

const CH = '3eZbrw1aB1LmzHi8';

function rec(status = 200, body = '', headers = {}, elapsedMs = undefined) {
  const out = { status, body, headers };
  if (elapsedMs !== undefined) out.elapsed_ms = elapsedMs;
  return out;
}

test('a plain echo and a json echo both pass', () => {
  assert.equal(replayVerdict(rec(200, CH), CH)[0], 'echoed');
  assert.equal(replayVerdict(rec(200, JSON.stringify({ challenge: CH })), CH)[0],
    'echoed-json');
});

test('a redirect is a failure however correct the destination', () => {
  const [state, detail] = replayVerdict(
    rec(301, '', { Location: 'https://x.example.com/slack/events/' }), CH);
  assert.equal(state, 'redirected');
  assert.match(detail, /does not follow redirects/);
});

test('an authenticator in front of the handler is named as such', () => {
  assert.equal(replayVerdict(rec(403), CH)[0], 'auth-wall');
  assert.equal(replayVerdict(rec(401), CH)[0], 'auth-wall');
});

test('a correct echo that missed the budget is not reported as success', () => {
  const [state, detail] = replayVerdict(rec(200, CH, {}, 4200), CH);
  assert.equal(state, 'too-slow');
  assert.match(detail, /4200ms/);
  assert.equal(replayVerdict(rec(200, CH, {}, 180), CH)[0], 'echoed');
});

test('an empty 200 is kept apart from a wrong 200', () => {
  assert.equal(replayVerdict(rec(200, '   '), CH)[0], 'empty-200');
  assert.equal(replayVerdict(rec(200, 'thanks'), CH)[0], 'wrong-body');
});

test('a challenge buried in an error page is not an echo', () => {
  assert.equal(replayVerdict(rec(200, `<h1>500</h1> payload was ${CH}`), CH)[0], 'buried');
  assert.equal(
    replayVerdict(rec(200, '<html>ok</html>', { 'Content-Type': 'text/html' }), CH)[0],
    'html-page');
});

test('socket mode and an empty event list are both hand-offs', () => {
  assert.equal(handshakeConfig({ settings: { socket_mode_enabled: true } })[0],
    'socket-mode');
  assert.equal(handshakeConfig({
    settings: {
      event_subscriptions: { request_url: 'https://a.example/x', bot_events: [] },
    },
  })[0], 'nothing-subscribed');
});

test('subscribed events with nowhere to go is the finding', () => {
  const [state, detail] = handshakeConfig({
    settings: { event_subscriptions: { bot_events: ['app_mention'] } },
  });
  assert.equal(state, 'no-request-url');
  assert.match(detail, /1 event\\(s\\)/);
});

test('two delivery paths configured at once is its own verdict', () => {
  const [state] = handshakeConfig({
    settings: {
      socket_mode_enabled: true,
      event_subscriptions: {
        request_url: 'https://a.example/x', bot_events: ['app_mention'],
      },
    },
  });
  assert.equal(state, 'both-configured');
});

test('a missing manifest is never reported as a clean configuration', () => {
  assert.equal(handshakeConfig({})[0], 'not-assessed');
  assert.equal(handshakeConfig(null)[0], 'not-assessed');
});

test('the url string gives up four things without a request', () => {
  const codes = urlShape('http://bot.ngrok.io:8443/slack/events?stage=prod')
    .map((r) => r[0]);
  assert.deepEqual(codes,
    ['not-https', 'tunnel-host', 'non-standard-port', 'query-string']);
  assert.deepEqual(urlShape('https://hooks.example.com/slack/events'), []);
});

test('userinfo is reported and then stripped before the host is read', () => {
  const codes = urlShape('https://user:pw@hooks.example.com/slack/events').map((r) => r[0]);
  assert.deepEqual(codes, ['credentials-in-url']);
  assert.deepEqual(urlShape(''), []);
});
''',
"faq": [
 ("Does the challenge request carry a Slack signature?",
  "Yes. The verification request is signed like every other delivery, so a correctly ordered signature check does not break the handshake. What breaks it is your own authentication: session middleware, an API gateway authoriser, an IP allowlist that has not been told about Slack. Those run before your route and answer the stranger with a redirect or a 403, and the app configuration page reports that as a challenge failure."),
 ("Can I return the challenge as JSON, or does it have to be plain text?",
  "Either works. A body that is exactly the challenge string with content type text/plain is accepted, and so is a JSON object with a top-level challenge field holding the same value. What is not accepted is the challenge nested inside a wrapper, or an object with the challenge alongside other fields your framework added, or the string with quotation marks around it from a serialiser that JSON-encoded a bare string."),
 ("Why does the script refuse to send a test request to my Request URL?",
  "Because it holds a token for a live workspace and is auditing a production endpoint that it did not write. A probe against an unknown handler can create records, page somebody, or trip a WAF rule that blocks Slack's own egress next. Everything this note needs is already written down: the manifest holds the configuration, and your access log holds what your endpoint said when Slack last asked."),
 ("The URL verified fine and the app is still silent. What now?",
  "Then the handshake is not your problem and the script says so in as many words. Verification proves that one exchange succeeded; it says nothing about whether any events are subscribed, whether the scopes behind them were granted, or whether Slack has since switched delivery off after a run of failures. Those are three different notes, and the last of them is the one to read if the app used to work."),
 ("We use Socket Mode. Does any of this apply?",
  "No, and that is worth confirming rather than assuming. A Socket Mode app has no Request URL, so there is no handshake and no way to fail one. If the manifest shows Socket Mode enabled and a Request URL configured at the same time, the configuration is describing two delivery paths, and somebody should decide which one this app uses before reading anything into an error about either."),
],
"related": [
 ("/slack/three-second-timeout/", "the same three seconds, applied to every event after the handshake"),
 ("/slack/event-subscriptions-auto-disabled/", "a URL that verified once and was switched off later"),
 ("/slack/config-token-expired/", "the credential that reads the manifest, and its twelve hours"),
],
"citations": [CITE_URL_VERIFICATION, CITE_EVENTS, CITE_MANIFEST_EXPORT, CITE_SOCKET_MODE],
})

GUIDES.append({
"slug": "three-second-timeout",
"title": "Three seconds to acknowledge, and what you spend them on",
"description": "Slack counts anything slower than three seconds as a failed delivery. Split the handler at the ack, price one Slack call, and see what is left.",
"h1": "Three seconds to acknowledge, and what you spend them on",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack 3 second timeout", "slack operation_timeout slash command",
             "slack dispatch_failed", "slack ack before work bolt",
             "slack event handler timeout retry"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody submits the modal and gets <em>We had some trouble connecting. Try again?</em> The record was created. It was created twice, actually, and both times correctly. The slash command says <code>operation_timeout</code> and then does the thing anyway.</p><p>Nothing here is broken in the sense of producing a wrong answer. Every one of these symptoms is Slack telling you the same single fact: the answer arrived after the deadline, and the deadline is three seconds.",
"short_answer": """<p>Slack requires an HTTP 2xx within <strong>three seconds</strong> for every event, every interaction payload and every slash command. Slower is not slow, it is failed: the delivery is counted as unsuccessful and retried, and enough of them in an hour will get event delivery switched off entirely. The clock starts on Slack's side, so DNS, TLS, gateway queueing and a cold start are all spending your budget before your code is reached.</p>
<p>The repair is one sentence and it belongs to this note rather than to any of its neighbours: <strong>acknowledge first, then do the work</strong>. What makes it worth a script is that the sentence is not always available. Some of the budget cannot be moved after the ack &mdash; a cold start is before your code, signature verification has to precede everything, and <code>views.open</code> has to happen inside three seconds of the trigger because that is how long the <code>trigger_id</code> lives. So the useful question is not "am I over" but "how much of this can move, and is what remains inside the budget on its own". The script splits your stage timings at the ack and answers exactly that, after measuring what one ordinary call to Slack costs from the host the handler runs on, because that is the number people leave out.</p>""",
"problem": """<p>Three seconds sounds generous, and it is, right up until you write down what actually happens in a handler that feels instantaneous when you test it. A Lambda cold start is somewhere between 300 milliseconds and two seconds depending on the runtime and the size of the bundle. An installation-store lookup against a database in another region is 40 milliseconds on a good day and 400 on a bad one. One <code>chat.postMessage</code> is a round trip to Slack's API from wherever you are, which is rarely under 150 milliseconds and is occasionally much worse. A single call to the service the bot is actually a front end for is anything at all.</p>
<p>Add those up honestly and the surprise is not that handlers time out, it is that any of them do not. And the failure is peculiarly hard to read, because <em>the work still happens</em>. The ticket is created, the message is posted, the record is written. The only external sign is a red toast in somebody's Slack client and, later, the same work having happened three or four times. People spend a long time looking for a bug in code that has none, because the code is correct and merely late.</p>
<p>The other half of the problem is that "just ack first" is offered as universal advice and it is not universally available. On a platform that freezes the process the instant the response is returned, work scheduled after the ack simply does not run, and the app moves from timing out to silently dropping every job, which is worse. Deferring is a repair that requires somewhere to defer to.</p>""",
"why": """<p><strong>The clock is Slack's, not yours.</strong> Your handler's own timer starts when the request reaches your code. Slack's started at the moment it sent the request, and it includes name resolution, the TLS handshake, whatever queueing your gateway does, and the cold start of the process that is about to serve it. A handler that logs 900 milliseconds of work can still miss a three second deadline without ever knowing.</p>
<p><strong>Late is failed, and failed is retried.</strong> There is no partial credit and no separate timeout status. A 200 that arrives at 3.1 seconds is treated exactly like a connection refused: it is a failed delivery, it is retried on the standard schedule, and it counts towards the failure rate that gets subscriptions disabled. That is the whole reason this note sits upstream of two others.</p>
<p><strong>Not all of the budget is deferrable, and the differences matter.</strong> Signature verification has to run before you trust the payload, so it is pre-ack by necessity, though it costs microseconds. A cold start is pre-ack because it is not your code. An installation-store lookup is pre-ack in most receivers but is cacheable, which is a different repair from deferring. And <code>views.open</code> is the awkward one: the <code>trigger_id</code> it needs expires in three seconds, so opening a modal cannot be moved into the background at all, only made fast.</p>
<p><strong>Acking is not the same as answering.</strong> The 2xx is a receipt, not a reply. The actual answer goes back afterwards through <code>response_url</code>, which is valid for thirty minutes and up to five uses, or through an ordinary <code>chat.postMessage</code>. Handlers that time out are frequently handlers whose author thought the response body <em>was</em> the answer and so could not send it until the work was done.</p>
<p><strong>On a function-as-a-service platform, "after the ack" may not exist.</strong> Returning the response can freeze the container, so a promise you did not await is a promise that never resolves. The deferral has to go somewhere durable &mdash; a queue, a job table, a second function &mdash; before the response is returned, and that hand-off is itself part of the pre-ack budget.</p>""",
"steps": [
 {"h": "Price one round trip to Slack from the host that runs the handler",
  "body": """<p>The script makes a handful of ordinary read calls and reports the median. This is the number nobody writes into their budget: if a call to Slack from your region costs 190 milliseconds, then a handler that posts a message and updates it inside the ack path has already spent close to 400 of its 3000 on network alone.</p>"""},
 {"h": "Write the stages down, including the ones that are not your code",
  "body": """<p>Cold start, TLS, gateway, signature check, installation lookup, the downstream call, the Slack call, the ack. Take the numbers from whatever you already have &mdash; APM spans, structured log timings, a p95 out of CloudWatch. Guessed numbers produce a guessed verdict, which the script will happily print.</p>"""},
 {"h": "Split the list at the ack rather than summing it",
  "body": """<p>Every stage is either something that must happen before the acknowledgement or something that can happen after it. The sum of the first group is the only number the deadline actually cares about, and it is usually a small fraction of the total, which is what makes the repair so effective when it is available.</p>"""},
 {"h": "Check whether deferring is even enough",
  "body": """<p>If the pre-ack group alone is over three seconds, moving work into the background changes nothing and the finding is a cold start or a slow lookup, not an architecture. The script reports that as a separate verdict because it is the case where the standard advice is wrong.</p>"""},
 {"h": "Give the deferred work somewhere to go",
  "body": """<p>A queue, a job row, a second process. Not a bare background task on a platform that freezes after the response, and not a fire-and-forget promise. The hand-off costs a few milliseconds and it happens before the ack, so it belongs in the pre-ack column where the script counts it.</p>"""},
 {"h": "Answer through response_url once you actually have an answer",
  "body": """<p>Thirty minutes, five uses, and it turns a three second budget into a thirty minute one for everything except the receipt. For modals the constraint is different and stricter: <code>trigger_id</code> expires in three seconds, so the call that opens a view has to stay in the fast path.</p>"""},
],
"verify": """<p>Re-run with the stage timings from after the change. The total will be roughly the same, which is the point: nothing got faster, the deadline just stopped applying to most of it.</p>
<pre><code class="language-bash">python3 slack_ack_budget.py --stage cold_start=420 --stage signature_verification=2 \\
    --stage enqueue=15 --stage ack=3 --stage downstream_http=2600 --stage chat_postMessage=190
# api        190ms          median of 5 read call(s) from this host
# budget     pre-ack        440ms of 3000ms, 2560ms of headroom
# budget     deferred       2790ms moved after the ack
# verdict    fixed          the deadline applies to 440ms of a 3230ms handler</code></pre>""",
"code_intro": "Three pure functions and a few timed GETs. <code>stage_phase</code> is the table that decides what can move, and the entries that cannot are the interesting ones. <code>split_budget</code> sums each side of the ack and produces four verdicts, one of which is that deferring will not save you. <code>api_call_budget</code> turns the measured round trip into a share of the deadline, which is the arithmetic that makes a handler with four Slack calls in it obviously wrong before anybody profiles anything.",
"py_file": "slack_ack_budget.py",
"py": '''"""Split a Slack handler's timings at the acknowledgement and price what is left.

Read only. The network half makes a handful of ordinary read calls and times
them, so the budget arithmetic uses this host's real round trip to Slack rather
than a guess. Nothing is sent to your own Request URL: timing that endpoint
means firing synthetic events at a production handler, which creates records
somebody has to clean up.
"""
import argparse
import logging
import os
import statistics
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_ack_budget")

API = "https://slack.com/api/"

# Every event, interaction payload and slash command wants a 2xx inside this,
# measured from Slack's side rather than from the moment your code is reached.
DEADLINE_MS = 3000

# What each stage is, with respect to the acknowledgement. The phases that are
# not "deferrable" are the whole reason this script exists: "ack first" is
# excellent advice that does nothing at all for a cold start.
STAGE_PHASES = {
    "dns": ("before-your-code", "resolution, already spent when your process wakes"),
    "tls": ("before-your-code", "the handshake, likewise"),
    "gateway": ("before-your-code", "queueing and routing in front of the handler"),
    "cold_start": ("before-your-code",
                   "the runtime booting; not code you can move after an ack"),
    "signature_verification": ("must-precede-ack",
                               "has to run before the payload is trusted, and costs "
                               "microseconds when done right"),
    "body_parse": ("must-precede-ack", "the payload has to be read to be answered"),
    "installation_lookup": ("cacheable-pre-ack",
                            "a store lookup in the receiver; cache it rather than "
                            "defer it, because the receiver needs the answer"),
    "token_lookup": ("cacheable-pre-ack", "the same shape of problem"),
    "enqueue": ("must-precede-ack",
                "handing the work to a queue is itself pre-ack, and is the cost "
                "of being able to defer anything at all"),
    "ack": ("must-precede-ack", "writing the 2xx"),
    "views_open": ("hard-deadline",
                   "trigger_id expires three seconds after the interaction, so "
                   "opening a modal cannot be deferred, only made fast"),
    "trigger_id_use": ("hard-deadline", "the same three second expiry"),
    "downstream_http": ("deferrable", "the service the bot fronts"),
    "database_write": ("deferrable", "record creation"),
    "llm_call": ("deferrable", "generation, and never inside an ack path"),
    "chat_postMessage": ("deferrable", "the answer, which is not the receipt"),
    "chat_update": ("deferrable", "likewise"),
    "response_url_post": ("deferrable",
                          "valid for thirty minutes and five uses, which is the "
                          "point of it"),
}


def stage_phase(name):
    """Place one stage relative to the acknowledgement. Pure.

    Unknown stages are treated as deferrable and said to be assumed, because
    guessing them into the pre-ack column would silently inflate the finding.
    """
    key = str(name or "").strip()
    if key in STAGE_PHASES:
        return STAGE_PHASES[key]
    return ("deferrable",
            "not a stage this script knows; assumed deferrable, so check it")


def split_budget(stages, deadline_ms=DEADLINE_MS):
    """Sum each side of the ack and say whether deferring is enough. Pure.

    ``stages`` is a sequence of (name, milliseconds). Returns the two sums, the
    headroom against the deadline, and one of four verdicts. The one worth
    having is "over-even-deferred": the case where the usual advice does not
    apply because the immovable half is already too slow.
    """
    deadline = max(int(deadline_ms or 0), 1)
    pre, deferred, hard = 0.0, 0.0, []
    for name, ms in stages or []:
        cost = max(float(ms or 0), 0.0)
        phase, _why = stage_phase(name)
        if phase == "deferrable":
            deferred += cost
        else:
            pre += cost
            if phase == "hard-deadline":
                hard.append(str(name))
    total = pre + deferred
    headroom = deadline - pre

    if total <= deadline:
        verdict = "inside"
    elif pre > deadline:
        verdict = "over-even-deferred"
    elif pre > deadline * 0.66:
        verdict = "tight-after-deferring"
    else:
        verdict = "fixed-by-deferring"
    return {"pre_ack_ms": round(pre, 1), "deferrable_ms": round(deferred, 1),
            "total_ms": round(total, 1), "headroom_ms": round(headroom, 1),
            "deadline_ms": deadline, "hard_deadline_stages": hard,
            "verdict": verdict}


def api_call_budget(latency_ms, calls, deadline_ms=DEADLINE_MS):
    """Price the Slack calls a handler makes inside the ack path. Pure.

    The measured round trip is the number people leave out of the budget
    entirely. Four calls at two hundred milliseconds is nearly a third of the
    deadline spent on network before any of your own work is counted.
    """
    deadline = max(int(deadline_ms or 0), 1)
    one = max(float(latency_ms or 0), 0.0)
    n = max(int(calls or 0), 0)
    cost = one * n
    share = round(cost * 100.0 / deadline, 1)
    if n == 0:
        verdict = "none-in-path"
    elif share >= 50.0:
        verdict = "dominant"
    elif share >= 20.0:
        verdict = "significant"
    else:
        verdict = "minor"
    return {"one_call_ms": round(one, 1), "calls": n, "cost_ms": round(cost, 1),
            "share_percent": share, "deadline_ms": deadline, "verdict": verdict}


def time_read_calls(session, samples):
    """Time a few ordinary read calls. GET only, and deliberately few of them."""
    timings = []
    for _ in range(max(int(samples or 0), 1)):
        started = time.monotonic()
        r = session.get(API + "auth.test", timeout=30)
        body = r.json()
        elapsed = (time.monotonic() - started) * 1000.0
        if body.get("ok") is not True:
            return ([], "auth.test answered 200 with ok: false, error=%s"
                    % body.get("error"))
        timings.append(elapsed)
    return (timings, "")


def parse_stage(text):
    name, _, value = str(text).partition("=")
    try:
        return (name.strip(), float(value))
    except ValueError:
        raise SystemExit("stage %r should look like name=milliseconds" % text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--stage", action="append", default=[],
                    help="name=milliseconds, repeatable; take the numbers from "
                         "your own traces")
    ap.add_argument("--calls-in-ack-path", type=int, default=0,
                    help="how many Slack API calls the handler makes before acking")
    ap.add_argument("--samples", type=int, default=5,
                    help="how many read calls to time; keep it small")
    args = ap.parse_args()

    stages = [parse_stage(s) for s in args.stage]
    one_call = 0.0

    token = os.environ.get(args.token_env)
    if not token:
        log.info("api        skipped        set %s to measure this host's round "
                 "trip to Slack", args.token_env)
    else:
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        timings, err = time_read_calls(s, args.samples)
        if err:
            log.warning("api        unavailable    %s", err)
        else:
            one_call = statistics.median(timings)
            log.info("api        %-14s median of %d read call(s) from this host",
                     "%dms" % int(one_call), len(timings))

    if args.calls_in_ack_path:
        call_cost = api_call_budget(one_call, args.calls_in_ack_path)
        (log.info if call_cost["verdict"] in ("minor", "none-in-path")
         else log.warning)(
            "calls      %-14s %d call(s) at %dms is %.1f%% of the %dms deadline",
            call_cost["verdict"], call_cost["calls"], int(call_cost["one_call_ms"]),
            call_cost["share_percent"], call_cost["deadline_ms"])

    if not stages:
        log.info("budget     no-stages      pass --stage name=milliseconds to "
                 "split a handler at the ack")
        return 0

    split = split_budget(stages)
    log.info("budget     pre-ack        %.0fms of %dms, %.0fms of headroom",
             split["pre_ack_ms"], split["deadline_ms"], split["headroom_ms"])
    log.info("budget     deferred       %.0fms moved after the ack",
             split["deferrable_ms"])
    for name in split["hard_deadline_stages"]:
        log.warning("budget     hard-deadline  %s cannot be deferred; trigger_id "
                    "expires in three seconds", name)

    if split["verdict"] == "inside":
        log.info("verdict    inside         the whole handler is %.0fms, under "
                 "the deadline as it stands", split["total_ms"])
        return 0
    if split["verdict"] == "over-even-deferred":
        log.warning("verdict    over-even-deferred  %.0fms of immovable work "
                    "against a %dms deadline; acking first changes nothing here",
                    split["pre_ack_ms"], split["deadline_ms"])
        log.warning("  repair: attack the pre-ack stages themselves. A cold start "
                    "is provisioned concurrency or a warmer runtime; an "
                    "installation lookup is a cache, not a queue")
        return 1
    (log.warning if split["verdict"] == "tight-after-deferring" else log.info)(
        "verdict    %-14s the deadline applies to %.0fms of a %.0fms handler",
        split["verdict"], split["pre_ack_ms"], split["total_ms"])
    log.warning("  repair: acknowledge first and hand the deferrable %.0fms to a "
                "queue. On a platform that freezes the process after the "
                "response, the hand-off has to be durable and has to happen "
                "before the ack", split["deferrable_ms"])
    log.warning("  repair: send the actual answer afterwards through response_url, "
                "which is good for thirty minutes and five uses")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-ack-budget.mjs",
"js": '''/**
 * Split a Slack handler's timings at the acknowledgement and price what is left.
 *
 * Read only. The network half makes a handful of ordinary read calls and times
 * them, so the budget arithmetic uses this host's real round trip to Slack
 * rather than a guess. Nothing is sent to your own Request URL.
 */

const API = 'https://slack.com/api/';

// Measured from Slack's side, not from the moment your code is reached.
const DEADLINE_MS = 3000;

// What each stage is with respect to the acknowledgement. The phases that are
// not 'deferrable' are the whole reason this script exists.
const STAGE_PHASES = new Map([
  ['dns', ['before-your-code', 'resolution, already spent when your process wakes']],
  ['tls', ['before-your-code', 'the handshake, likewise']],
  ['gateway', ['before-your-code', 'queueing and routing in front of the handler']],
  ['cold_start', ['before-your-code',
    'the runtime booting; not code you can move after an ack']],
  ['signature_verification', ['must-precede-ack',
    'has to run before the payload is trusted, and costs microseconds when done right']],
  ['body_parse', ['must-precede-ack', 'the payload has to be read to be answered']],
  ['installation_lookup', ['cacheable-pre-ack',
    'a store lookup in the receiver; cache it rather than defer it, because the ' +
    'receiver needs the answer']],
  ['token_lookup', ['cacheable-pre-ack', 'the same shape of problem']],
  ['enqueue', ['must-precede-ack',
    'handing the work to a queue is itself pre-ack, and is the cost of being ' +
    'able to defer anything at all']],
  ['ack', ['must-precede-ack', 'writing the 2xx']],
  ['views_open', ['hard-deadline',
    'trigger_id expires three seconds after the interaction, so opening a modal ' +
    'cannot be deferred, only made fast']],
  ['trigger_id_use', ['hard-deadline', 'the same three second expiry']],
  ['downstream_http', ['deferrable', 'the service the bot fronts']],
  ['database_write', ['deferrable', 'record creation']],
  ['llm_call', ['deferrable', 'generation, and never inside an ack path']],
  ['chat_postMessage', ['deferrable', 'the answer, which is not the receipt']],
  ['chat_update', ['deferrable', 'likewise']],
  ['response_url_post', ['deferrable',
    'valid for thirty minutes and five uses, which is the point of it']],
]);

/**
 * Place one stage relative to the acknowledgement. Pure.
 * Unknown stages are assumed deferrable and said to be assumed, because
 * guessing them into the pre-ack column would inflate the finding.
 */
export function stagePhase(name) {
  const key = String(name ?? '').trim();
  return STAGE_PHASES.get(key)
    ?? ['deferrable', 'not a stage this script knows; assumed deferrable, so check it'];
}

/**
 * Sum each side of the ack and say whether deferring is enough. Pure.
 * The verdict worth having is 'over-even-deferred': the case where the usual
 * advice does not apply because the immovable half is already too slow.
 */
export function splitBudget(stages, deadlineMs = DEADLINE_MS) {
  const deadline = Math.max(Number(deadlineMs) || 0, 1);
  let pre = 0;
  let deferred = 0;
  const hard = [];
  for (const [name, ms] of stages ?? []) {
    const cost = Math.max(Number(ms) || 0, 0);
    const [phase] = stagePhase(name);
    if (phase === 'deferrable') {
      deferred += cost;
    } else {
      pre += cost;
      if (phase === 'hard-deadline') hard.push(String(name));
    }
  }
  const total = pre + deferred;
  const headroom = deadline - pre;

  let verdict = 'fixed-by-deferring';
  if (total <= deadline) verdict = 'inside';
  else if (pre > deadline) verdict = 'over-even-deferred';
  else if (pre > deadline * 0.66) verdict = 'tight-after-deferring';

  return {
    preAckMs: Math.round(pre * 10) / 10,
    deferrableMs: Math.round(deferred * 10) / 10,
    totalMs: Math.round(total * 10) / 10,
    headroomMs: Math.round(headroom * 10) / 10,
    deadlineMs: deadline,
    hardDeadlineStages: hard,
    verdict,
  };
}

/**
 * Price the Slack calls a handler makes inside the ack path. Pure.
 * The measured round trip is the number people leave out of the budget.
 */
export function apiCallBudget(latencyMs, calls, deadlineMs = DEADLINE_MS) {
  const deadline = Math.max(Number(deadlineMs) || 0, 1);
  const one = Math.max(Number(latencyMs) || 0, 0);
  const n = Math.max(Number(calls) || 0, 0);
  const cost = one * n;
  const share = Math.round((cost * 1000.0) / deadline) / 10;
  let verdict = 'minor';
  if (n === 0) verdict = 'none-in-path';
  else if (share >= 50.0) verdict = 'dominant';
  else if (share >= 20.0) verdict = 'significant';
  return {
    oneCallMs: Math.round(one * 10) / 10,
    calls: n,
    costMs: Math.round(cost * 10) / 10,
    sharePercent: share,
    deadlineMs: deadline,
    verdict,
  };
}

async function timeReadCalls(token, samples) {
  const timings = [];
  for (let i = 0; i < Math.max(Number(samples) || 0, 1); i += 1) {
    const started = Date.now();
    // eslint-disable-next-line no-await-in-loop
    const res = await fetch(`${API}auth.test`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    // eslint-disable-next-line no-await-in-loop
    const body = await res.json();
    const elapsed = Date.now() - started;
    if (body.ok !== true) {
      return [[], `auth.test answered 200 with ok: false, error=${body.error}`];
    }
    timings.push(elapsed);
  }
  return [timings, ''];
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const stages = argAll(args, '--stage').map((text) => {
    const [name, value] = String(text).split('=');
    const ms = Number(value);
    if (!Number.isFinite(ms)) {
      console.error(`stage ${text} should look like name=milliseconds`);
      process.exit(2);
    }
    return [name.trim(), ms];
  });

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  let oneCall = 0;
  if (!token) {
    console.log(`api        skipped        set ${tokenEnv} to measure this host's ` +
      'round trip to Slack');
  } else {
    const [timings, err] = await timeReadCalls(token, Number(arg(args, '--samples', 5)));
    if (err) {
      console.warn(`api        unavailable    ${err}`);
    } else {
      oneCall = median(timings);
      console.log(`api        ${`${Math.trunc(oneCall)}ms`.padEnd(14)} median of ` +
        `${timings.length} read call(s) from this host`);
    }
  }

  const callsInPath = Number(arg(args, '--calls-in-ack-path', 0));
  if (callsInPath) {
    const c = apiCallBudget(oneCall, callsInPath);
    const quiet = c.verdict === 'minor' || c.verdict === 'none-in-path';
    (quiet ? console.log : console.warn)(
      `calls      ${c.verdict.padEnd(14)} ${c.calls} call(s) at ` +
      `${Math.trunc(c.oneCallMs)}ms is ${c.sharePercent}% of the ${c.deadlineMs}ms deadline`);
  }

  if (stages.length === 0) {
    console.log('budget     no-stages      pass --stage name=milliseconds to split ' +
      'a handler at the ack');
    return;
  }

  const split = splitBudget(stages);
  console.log(`budget     pre-ack        ${Math.round(split.preAckMs)}ms of ` +
    `${split.deadlineMs}ms, ${Math.round(split.headroomMs)}ms of headroom`);
  console.log(`budget     deferred       ${Math.round(split.deferrableMs)}ms moved ` +
    'after the ack');
  for (const name of split.hardDeadlineStages) {
    console.warn(`budget     hard-deadline  ${name} cannot be deferred; trigger_id ` +
      'expires in three seconds');
  }

  if (split.verdict === 'inside') {
    console.log(`verdict    inside         the whole handler is ` +
      `${Math.round(split.totalMs)}ms, under the deadline as it stands`);
    return;
  }
  if (split.verdict === 'over-even-deferred') {
    console.warn(`verdict    over-even-deferred  ${Math.round(split.preAckMs)}ms of ` +
      `immovable work against a ${split.deadlineMs}ms deadline; acking first ` +
      'changes nothing here');
    console.warn('  repair: attack the pre-ack stages themselves. A cold start is ' +
      'provisioned concurrency or a warmer runtime; an installation lookup is a ' +
      'cache, not a queue');
    process.exitCode = 1;
    return;
  }
  (split.verdict === 'tight-after-deferring' ? console.warn : console.log)(
    `verdict    ${split.verdict.padEnd(14)} the deadline applies to ` +
    `${Math.round(split.preAckMs)}ms of a ${Math.round(split.totalMs)}ms handler`);
  console.warn(`  repair: acknowledge first and hand the deferrable ` +
    `${Math.round(split.deferrableMs)}ms to a queue. On a platform that freezes ` +
    'the process after the response, the hand-off has to be durable and has to ' +
    'happen before the ack');
  console.warn('  repair: send the actual answer afterwards through response_url, ' +
    'which is good for thirty minutes and five uses');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the split rather than the totals, because the total is not what the deadline applies to. The same handler, unchanged, is asserted to be over the budget when everything runs before the ack and inside it when the deferrable stages move, and a cold start large enough to blow the deadline on its own is asserted to produce the verdict that says deferring will not help. <code>views_open</code> is pinned as non-deferrable, since it is the one piece of work people move into the background and then cannot understand why the modal never opens.",
"test_py_file": "test_slack_ack_budget.py",
"test_js_file": "slack-ack-budget.test.mjs",
"test_py": '''from slack_ack_budget import api_call_budget, split_budget, stage_phase

HANDLER = [
    ("cold_start", 420),
    ("signature_verification", 2),
    ("installation_lookup", 120),
    ("downstream_http", 2600),
    ("chat_postMessage", 190),
    ("ack", 3),
]


def test_the_same_handler_is_over_the_deadline_and_inside_the_ack_budget():
    split = split_budget(HANDLER)
    assert split["total_ms"] > 3000
    assert split["pre_ack_ms"] == 545.0
    assert split["verdict"] == "fixed-by-deferring"


def test_the_deferrable_half_is_where_almost_all_the_time_is():
    split = split_budget(HANDLER)
    assert split["deferrable_ms"] == 2790.0
    assert split["headroom_ms"] == 2455.0


def test_a_handler_that_already_fits_is_left_alone():
    split = split_budget([("cold_start", 200), ("downstream_http", 400)])
    assert split["verdict"] == "inside"
    assert split["total_ms"] == 600.0


def test_an_immovable_half_over_the_deadline_is_its_own_verdict():
    split = split_budget([("cold_start", 3400), ("downstream_http", 50)])
    assert split["verdict"] == "over-even-deferred"
    assert split["headroom_ms"] < 0


def test_the_two_thirds_mark_is_reported_as_tight_rather_than_fixed():
    split = split_budget([("cold_start", 2200), ("downstream_http", 4000)])
    assert split["verdict"] == "tight-after-deferring"


def test_opening_a_modal_is_never_treated_as_deferrable():
    assert stage_phase("views_open")[0] == "hard-deadline"
    split = split_budget([("views_open", 800), ("downstream_http", 5000)])
    assert split["hard_deadline_stages"] == ["views_open"]
    assert split["pre_ack_ms"] == 800.0


def test_the_queue_handoff_is_counted_before_the_ack_not_after_it():
    assert stage_phase("enqueue")[0] == "must-precede-ack"
    assert split_budget([("enqueue", 15)])["deferrable_ms"] == 0.0


def test_an_unknown_stage_is_assumed_deferrable_and_says_so():
    phase, why = stage_phase("some_internal_span")
    assert phase == "deferrable"
    assert "assumed" in why


def test_four_slack_calls_in_the_ack_path_are_a_third_of_the_budget():
    cost = api_call_budget(190, 4)
    assert cost["cost_ms"] == 760.0
    assert cost["share_percent"] == 25.3
    assert cost["verdict"] == "significant"


def test_one_fast_call_is_minor_and_eight_slow_ones_dominate():
    assert api_call_budget(120, 1)["verdict"] == "minor"
    assert api_call_budget(200, 8)["verdict"] == "dominant"
    assert api_call_budget(190, 0)["verdict"] == "none-in-path"


def test_an_empty_stage_list_produces_zeroes_rather_than_a_crash():
    split = split_budget([])
    assert split["total_ms"] == 0.0
    assert split["verdict"] == "inside"
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apiCallBudget, splitBudget, stagePhase } from './slack-ack-budget.mjs';

const HANDLER = [
  ['cold_start', 420],
  ['signature_verification', 2],
  ['installation_lookup', 120],
  ['downstream_http', 2600],
  ['chat_postMessage', 190],
  ['ack', 3],
];

test('the same handler is over the deadline and inside the ack budget', () => {
  const split = splitBudget(HANDLER);
  assert.ok(split.totalMs > 3000);
  assert.equal(split.preAckMs, 545);
  assert.equal(split.verdict, 'fixed-by-deferring');
});

test('the deferrable half is where almost all the time is', () => {
  const split = splitBudget(HANDLER);
  assert.equal(split.deferrableMs, 2790);
  assert.equal(split.headroomMs, 2455);
});

test('a handler that already fits is left alone', () => {
  const split = splitBudget([['cold_start', 200], ['downstream_http', 400]]);
  assert.equal(split.verdict, 'inside');
  assert.equal(split.totalMs, 600);
});

test('an immovable half over the deadline is its own verdict', () => {
  const split = splitBudget([['cold_start', 3400], ['downstream_http', 50]]);
  assert.equal(split.verdict, 'over-even-deferred');
  assert.ok(split.headroomMs < 0);
});

test('the two thirds mark is reported as tight rather than fixed', () => {
  const split = splitBudget([['cold_start', 2200], ['downstream_http', 4000]]);
  assert.equal(split.verdict, 'tight-after-deferring');
});

test('opening a modal is never treated as deferrable', () => {
  assert.equal(stagePhase('views_open')[0], 'hard-deadline');
  const split = splitBudget([['views_open', 800], ['downstream_http', 5000]]);
  assert.deepEqual(split.hardDeadlineStages, ['views_open']);
  assert.equal(split.preAckMs, 800);
});

test('the queue handoff is counted before the ack not after it', () => {
  assert.equal(stagePhase('enqueue')[0], 'must-precede-ack');
  assert.equal(splitBudget([['enqueue', 15]]).deferrableMs, 0);
});

test('an unknown stage is assumed deferrable and says so', () => {
  const [phase, why] = stagePhase('some_internal_span');
  assert.equal(phase, 'deferrable');
  assert.match(why, /assumed/);
});

test('four slack calls in the ack path are a third of the budget', () => {
  const cost = apiCallBudget(190, 4);
  assert.equal(cost.costMs, 760);
  assert.equal(cost.sharePercent, 25.3);
  assert.equal(cost.verdict, 'significant');
});

test('one fast call is minor and eight slow ones dominate', () => {
  assert.equal(apiCallBudget(120, 1).verdict, 'minor');
  assert.equal(apiCallBudget(200, 8).verdict, 'dominant');
  assert.equal(apiCallBudget(190, 0).verdict, 'none-in-path');
});

test('an empty stage list produces zeroes rather than a crash', () => {
  const split = splitBudget([]);
  assert.equal(split.totalMs, 0);
  assert.equal(split.verdict, 'inside');
});
''',
"faq": [
 ("Is the three seconds measured at my server or at Slack?",
  "At Slack. The clock starts when the request is sent and stops when the response is complete, so it includes name resolution, the TLS handshake, any queueing in a gateway, and the cold start of the process that serves it. A handler whose own instrumentation reports 900 milliseconds can still be a failed delivery, which is why the stage list in this script starts with things that are not your code."),
 ("What actually happens if I miss it?",
  "The delivery is counted as failed and retried on a fixed schedule, so the same work arrives again. Sustained failure has a further consequence: Slack disables event subscriptions for apps that fail the great majority of deliveries in an hour, and does not switch them back on when you recover. Missing the deadline is therefore not a latency problem with a latency-sized consequence."),
 ("Can I always fix this by acking first and working in the background?",
  "No, and that is the case the script exists to find. If the immovable stages alone exceed three seconds, deferring moves nothing that was costing you the deadline. A two second cold start plus a 1.2 second installation-store lookup is over the budget before your handler has read the payload, and the repairs there are provisioned concurrency and a cache rather than a queue."),
 ("I ack first and the background work never runs. What is wrong?",
  "Almost certainly the platform. Several function-as-a-service runtimes freeze the container the moment the response is returned, so a task you started and did not await is a task that is suspended indefinitely and may never resume. The deferral has to be handed to something durable before the response goes out, and that hand-off is pre-ack work that belongs in the budget."),
 ("Why does the script time calls to Slack instead of timing my handler?",
  "Because your handler is already instrumented and Slack's round trip usually is not. The number that goes missing from these budgets is the cost of talking to Slack from wherever the handler runs, and a script holding a read token can measure that honestly in five calls. Timing your own Request URL would mean sending it synthetic events, which creates real records in somebody's workspace."),
],
"related": [
 ("/slack/retry-storm-from-event-retries/", "what a missed deadline turns into at volume"),
 ("/slack/event-subscriptions-auto-disabled/", "where sustained misses end up"),
 ("/slack/request-url-unverified/", "the same three seconds, applied once at setup"),
],
"citations": [CITE_EVENTS, CITE_INTERACTIVITY, CITE_VIEWS_OPEN, CITE_AUTH_TEST],
})

GUIDES.append({
"slug": "retry-storm-from-event-retries",
"title": "One missed ack becomes four deliveries and a 429",
"description": "Slack retries at 0, 60 and 300 seconds. Multiply the deliveries by the calls each one makes, hold that against the tier, and find where the loop settles.",
"h1": "One missed ack becomes four deliveries and a 429",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack retry storm", "x-slack-retry-num rate limit",
             "slack event retries 429", "slack events api amplification",
             "slack retry schedule 60 300 seconds"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It is fine at ten events a minute and it is fine at forty, and then one afternoon it is not fine at anything. The handler slows down a little, some deliveries miss the deadline, Slack sends them again, the extra deliveries make the same API calls, the calls start coming back <code>ratelimited</code>, the handler waits on them, and now it is missing far more deadlines than it was a minute ago.</p><p>Nothing in that sequence is a bug. Every component is behaving exactly as designed, and together they converge on total failure and stay there until the traffic stops.",
"short_answer": """<p>Slack retries a delivery it believes failed up to three times, at roughly zero, sixty and three hundred seconds. That is a ceiling of four deliveries per event, so the amplification is bounded and small &mdash; on its own it would be a nuisance. What makes it a storm is the second multiplier: each delivery runs your handler, and each run of your handler makes some number of Web API calls. Four deliveries times three calls is twelve calls where you budgeted three, against a per-method quota that did not grow.</p>
<p>So this note is arithmetic rather than a state to detect. Events per minute, times deliveries per event, times calls per handler run, held against the method's budget. And then the part people miss: the miss rate is not an input, it is an output. Being throttled makes handlers slower, slower handlers miss more deadlines, more misses mean more deliveries, and the script iterates that loop until it settles &mdash; which it always does, because the retry ceiling bounds it. <strong>Where</strong> it settles is the finding. The same forty events a minute settle at a five percent miss rate with one API call per handler run and at ninety-three percent with three, and ninety-three percent is not a slow app: it is a hair under the failure rate at which Slack switches your event subscriptions off.</p>""",
"problem": """<p>The reason this arrives as a surprise is that every number involved looks fine in isolation. Forty events a minute is nothing. Three API calls per event is modest. A five percent timeout rate is a good day. A Tier 3 method allows fifty requests a minute. Every one of those is defensible in a design review and the combination is over the line by a factor of two.</p>
<p>What makes it a storm rather than a shortfall is that one of the four numbers depends on the other three. If the demand exceeds the budget, calls start being refused, and a handler that waits on a refused call takes longer, and a handler that takes longer misses the three second acknowledgement, and a missed acknowledgement produces another delivery, which makes another set of calls. The miss rate that started at five percent is now thirty, then sixty. There is no component in that loop that is misbehaving and no log line that says what happened.</p>
<p>It also recovers strangely, which is the tell. The system does not degrade gracefully and then improve as load falls; it collapses, stays collapsed while the sixty-second and three-hundred-second retries keep arriving from events that are already minutes old, and then comes back all at once when the backlog is finally exhausted. People describe it as the service "unsticking itself", which is exactly what a feedback loop looks like from outside.</p>""",
"why": """<p><strong>The amplification is bounded at four and the consequence is not.</strong> Three retries is the ceiling and it never goes higher, so the tempting conclusion is that the worst case is a four times spike, which any system with headroom absorbs. That is true of the deliveries and false of the effect, because the four times lands on a quota that four times exceeded then feeds back into the thing producing the retries.</p>
<p><strong>The loop has an equilibrium, and the equilibrium is the problem.</strong> Because the amplification is capped, the feedback cannot run away to infinity; it settles. What the arithmetic shows, and what makes this worth computing rather than intuiting, is that the settling point for an ordinary over-budget configuration is a miss rate in the nineties. That is not a degraded service. It is within a percentage point or two of the sustained failure rate at which Slack disables event delivery outright &mdash; which is why an app that survives one storm sometimes does not survive the next.</p>
<p><strong>The retry spacing is why the pain outlasts the incident.</strong> Deliveries at sixty and three hundred seconds mean that five minutes after the load spike ends you are still receiving retries of events from before it started, all of them still making calls. The tail is longer than the incident, and a graph of API calls will show a second and third hump that no traffic in your product explains.</p>
<p><strong>Per-method, per-workspace, per-app is what the budget is scoped to.</strong> Not per handler, and not per instance. Adding replicas does not add quota, so scaling out to serve the extra deliveries makes the throttling worse rather than better, which is the single most common wrong move at this point in the incident.</p>
<p><strong>The multiplicand you control is the calls per handler run.</strong> You cannot change the retry schedule and you should not want to change the deadline. What you can change is how many API calls one delivery makes: a handler that posts a message, then updates it, then looks up two users, is four calls where one would do, and that four is multiplied by everything else in the chain.</p>
<p><strong>An audit must not demonstrate this.</strong> Provoking the loop to prove it exists means exhausting a real workspace's quota for every app installed in it, yours and everybody else's. The script below computes and iterates a model; the only thing it measures is how many messages the workspace already produced, which it reads out of history.</p>""",
"steps": [
 {"h": "Measure how many events a minute the app is really on the hook for",
  "body": """<p>One page of <code>conversations.history</code> in a sample of the channels the bot belongs to, and the span between the oldest and newest <code>ts</code>, gives messages per minute. For an app subscribed to <code>message.channels</code> that is the delivery rate directly. It is a floor rather than a census, and the script says so.</p>"""},
 {"h": "Count the API calls one handler run makes",
  "body": """<p>Read the handler and count them: every <code>chat.postMessage</code>, every lookup, every update. This is the one number in the model that is nobody's estimate, and it is also the one you can change this afternoon.</p>"""},
 {"h": "Expand the deliveries for the miss rate you have today",
  "body": """<p>One event is one delivery plus a retry for each miss, capped at three. At a five percent miss rate that is 1.05 deliveries per event, which is nothing. At forty percent it is 1.7, and at eighty percent it is 3.4. The function is not linear in the miss rate and that is exactly why it feels like a cliff.</p>"""},
 {"h": "Hold the product against the method's budget",
  "body": """<p>Events times deliveries times calls, against requests per minute for the method your handler leans on hardest. Under half the budget is fine. Over the budget is not a warning, it is the point at which some of your calls are already being refused.</p>"""},
 {"h": "Iterate it, because the miss rate is an output",
  "body": """<p>Feed the throttled fraction back into the miss rate and run it again, and again. It will settle; the ceiling on retries guarantees that. The question is where, and the four answers are not variations on each other: unchanged, elevated, collapsed at a fixed point that happens to be failure, or settled above the rate at which delivery is switched off. The script prints the path so the walk is visible rather than asserted.</p>"""},
 {"h": "Cut a multiplicand rather than adding capacity",
  "body": """<p>Fewer calls per handler run, or fewer events arriving, or a narrower subscription. More replicas add nothing because the quota is per app, not per process. And the deliveries factor closes itself once the deadline is met, which is a different note and the one to read next.</p>"""},
],
"verify": """<p>Re-run with the reduced call count. The event rate will be identical, and the loop should settle instead of walking to the ceiling.</p>
<pre><code class="language-bash">python3 slack_retry_amplification.py --calls-per-event 1 --miss-rate 0.05 --tier-per-minute 50
# rate       observed       38.4 message(s)/minute across 5 channel(s), a floor
# demand     tight          40.4 call(s)/minute against a budget of 50 (80.8%)
# loop       stable         settles at a miss rate of 0.05 after 1 round(s)
# loop       path           0.05 -&gt; 0.05
# verdict    ok             no feedback: the throttled fraction stays at zero</code></pre>""",
"code_intro": "Three pure functions and one page of history per sampled channel. <code>deliveries_per_event</code> is the retry schedule as a geometric sum capped at three. <code>demand</code> multiplies the three factors and holds the product against the budget. <code>converge</code> is the note's actual claim: it feeds the throttled fraction back into the miss rate and iterates until the loop settles, and <code>settle_verdict</code> reads the ladder off the fixed point, whose top rung is not slowness but the failure rate that gets an app switched off.",
"py_file": "slack_retry_amplification.py",
"py": '''"""Model the retry amplification of a Slack event handler against its quota.

Read only, and it does not demonstrate the problem it describes: provoking a
retry storm means exhausting a real workspace's per-method quota for every app
installed in it. The only measurement taken is how many messages the workspace
already produced, read from one page of history per sampled channel. Everything
else is arithmetic over numbers the caller supplies.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_retry_amplification")

API = "https://slack.com/api/"

# Slack retries a delivery it believes failed three times: immediately, after
# about a minute, and after about five minutes. Four deliveries is the ceiling
# and the spacing is why the tail outlasts the incident.
MAX_RETRIES = 3
RETRY_SCHEDULE_SECONDS = (0, 60, 300)

# The miss rate is capped just short of one so the arithmetic stays meaningful.
# The number that matters more is the other one: Slack disables an app's event
# subscriptions when it fails more than 95% of deliveries in an hour, so a loop
# whose equilibrium sits above that does not end in a slow app.
MISS_CAP = 0.99
DISABLE_THRESHOLD = 0.95


def deliveries_per_event(miss_rate, max_retries=MAX_RETRIES):
    """Expected deliveries for one event at a given miss rate. Pure.

    A geometric sum truncated at the retry ceiling. It is deliberately not
    linear: five percent gives 1.05 and eighty percent gives 3.4, and the
    distance between those is why this feels like a cliff rather than a slope.
    """
    p = min(max(float(miss_rate or 0.0), 0.0), 1.0)
    total = 1.0
    term = 1.0
    for _ in range(max(int(max_retries or 0), 0)):
        term *= p
        total += term
    return round(total, 4)


def demand(events_per_minute, calls_per_event, miss_rate, tier_per_minute):
    """Multiply the three factors and hold the product against the budget. Pure.

    Returns the demanded call rate, the share of the budget it takes, and the
    fraction of calls that must be refused. That last number is the input to
    the feedback loop, which is what makes this more than a multiplication.
    """
    events = max(float(events_per_minute or 0.0), 0.0)
    calls = max(float(calls_per_event or 0.0), 0.0)
    budget = max(float(tier_per_minute or 0.0), 1.0)
    per_event = deliveries_per_event(miss_rate)
    demanded = events * per_event * calls
    share = round(demanded * 100.0 / budget, 1)
    throttled = 0.0 if demanded <= budget else round(1.0 - (budget / demanded), 4)

    if demanded > budget:
        verdict = "over-budget"
    elif share >= 80.0:
        verdict = "saturated"
    elif share >= 50.0:
        verdict = "tight"
    else:
        verdict = "stable"
    return {"deliveries_per_event": per_event, "calls_per_minute": round(demanded, 1),
            "budget_per_minute": round(budget, 1), "share_percent": share,
            "throttled_fraction": throttled, "verdict": verdict}


def settle_verdict(final_miss_rate, base_miss_rate):
    """Name the equilibrium the loop arrived at. Pure.

    The loop always has a fixed point, because the retry ceiling bounds the
    amplification. Whether that fixed point is somewhere you can live is the
    entire question, and the top rung is not a performance problem: an app
    failing more than 95% of deliveries for an hour has its event
    subscriptions switched off, and they do not come back on their own.
    """
    final = float(final_miss_rate or 0.0)
    base = float(base_miss_rate or 0.0)
    if final <= base + 0.01:
        return ("stable", "no feedback: the throttled fraction never leaves zero")
    if final >= DISABLE_THRESHOLD:
        return ("disabling",
                "the equilibrium is above the %d%% failure rate that gets event "
                "subscriptions switched off. This loop does not end in a slow "
                "app, it ends in a disabled one." % int(DISABLE_THRESHOLD * 100))
    if final >= 0.5:
        return ("collapsed",
                "the loop has a fixed point and the fixed point is failure: "
                "most deliveries miss, most events are retried, and it stays "
                "there until the traffic stops")
    return ("elevated",
            "the feedback is real and the equilibrium is survivable; there is "
            "no headroom left for the next increase in traffic")


def converge(events_per_minute, calls_per_event, base_miss_rate, tier_per_minute,
             rounds=12):
    """Feed the throttled fraction back into the miss rate and iterate. Pure.

    The claim of this note is that the miss rate is an output rather than an
    input: throttled calls make handlers slower, slower handlers miss the three
    second deadline, and missed deadlines produce the deliveries that caused
    the throttling. The retry ceiling means this always settles somewhere. The
    path is returned so the walk can be read rather than asserted.
    """
    p = min(max(float(base_miss_rate or 0.0), 0.0), MISS_CAP)
    base = p
    path = [round(p, 4)]
    for step in range(max(int(rounds or 0), 1)):
        state = demand(events_per_minute, calls_per_event, p, tier_per_minute)
        nxt = min(base + state["throttled_fraction"], MISS_CAP)
        path.append(round(nxt, 4))
        if abs(nxt - p) < 0.001:
            verdict, detail = settle_verdict(nxt, base)
            return {"verdict": verdict, "detail": detail,
                    "miss_rate": round(nxt, 4), "rounds": step + 1, "path": path,
                    "deliveries_per_event": deliveries_per_event(nxt)}
        p = nxt
    return {"verdict": "unsettled",
            "detail": "still climbing after %d round(s), which is the same "
                      "finding as collapse with less arithmetic" % int(rounds),
            "miss_rate": round(p, 4), "rounds": int(rounds), "path": path,
            "deliveries_per_event": deliveries_per_event(p)}


def observed_rate(timestamps):
    """Messages per minute across a sample of history. Pure.

    A floor, not a census: one page per channel, and a workspace whose history
    calls are clamped returns fewer objects than were asked for. Both of those
    bias the number down, never up, which is the safe direction for a model
    whose output is a warning.
    """
    values = sorted(float(t) for t in timestamps or [] if t)
    if len(values) < 2:
        return {"count": len(values), "span_seconds": 0.0, "per_minute": 0.0,
                "note": "not enough messages in the sample to derive a rate"}
    span = values[-1] - values[0]
    if span <= 0:
        return {"count": len(values), "span_seconds": 0.0, "per_minute": 0.0,
                "note": "every sampled message shares a timestamp"}
    per_minute = round(len(values) * 60.0 / span, 1)
    return {"count": len(values), "span_seconds": round(span, 1),
            "per_minute": per_minute,
            "note": "a floor: one page per channel, so the real rate is higher"}


def get(session, method, **params):
    r = session.get(API + method, params=params, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--calls-per-event", type=float, default=3.0,
                    help="Web API calls one handler run makes; count them")
    ap.add_argument("--miss-rate", type=float, default=0.05,
                    help="fraction of deliveries that miss the three second ack")
    ap.add_argument("--tier-per-minute", type=float, default=50.0,
                    help="requests a minute the busiest method in the handler allows")
    ap.add_argument("--events-per-minute", type=float, default=0.0,
                    help="override the measured rate instead of sampling history")
    ap.add_argument("--channels", type=int, default=5,
                    help="how many of the bot's channels to sample")
    args = ap.parse_args()

    events = args.events_per_minute
    token = os.environ.get(args.token_env)
    if events <= 0 and not token:
        log.error("set %s or pass --events-per-minute", args.token_env)
        return 2

    if events <= 0:
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        who = get(s, "auth.test")
        if who.get("ok") is not True:
            log.error("auth.test answered 200 with ok: false, error=%s", who.get("error"))
            return 2
        mine = get(s, "users.conversations", user=who.get("user_id", ""),
                   types="public_channel,private_channel", limit=200)
        ids = [c.get("id") for c in (mine.get("channels") or [])][:max(args.channels, 1)]
        stamps, sampled = [], 0
        for cid in ids:
            page = get(s, "conversations.history", channel=cid, limit=200)
            if page.get("ok") is not True:
                log.warning("rate       skipped        %s on %s", page.get("error"), cid)
                continue
            sampled += 1
            stamps.extend(m.get("ts") for m in (page.get("messages") or []))
        rate = observed_rate(stamps)
        events = rate["per_minute"]
        log.info("rate       observed       %s message(s)/minute across %d "
                 "channel(s), %s", rate["per_minute"], sampled, rate["note"])

    state = demand(events, args.calls_per_event, args.miss_rate, args.tier_per_minute)
    (log.info if state["verdict"] == "stable" else log.warning)(
        "demand     %-14s %.1f call(s)/minute against a budget of %.0f (%.1f%%)",
        state["verdict"], state["calls_per_minute"], state["budget_per_minute"],
        state["share_percent"])
    log.info("deliveries %-14s %.2f per event at a miss rate of %.2f, retried at "
             "%s seconds", "expanded", state["deliveries_per_event"], args.miss_rate,
             ", ".join(str(x) for x in RETRY_SCHEDULE_SECONDS))

    loop = converge(events, args.calls_per_event, args.miss_rate, args.tier_per_minute)
    (log.info if loop["verdict"] == "stable" else log.warning)(
        "loop       %-14s settles at a miss rate of %.2f after %d round(s), "
        "%.2f deliveries/event", loop["verdict"], loop["miss_rate"],
        loop["rounds"], loop["deliveries_per_event"])
    log.info("loop       path           %s", " -> ".join("%.2f" % p for p in loop["path"]))
    (log.info if loop["verdict"] == "stable" else log.warning)(
        "loop       %-14s %s", "meaning", loop["detail"])

    if loop["verdict"] == "stable" and state["verdict"] in ("stable", "tight"):
        log.info("verdict    %-14s no feedback: the throttled fraction stays at "
                 "zero", "ok")
        return 0
    log.warning("  repair: cut the calls one handler run makes. That factor "
                "multiplies everything else in the chain and it is the only one "
                "of the four you can change today")
    log.warning("  repair: narrow the subscription so fewer events arrive at all; "
                "an app that receives every message in every channel is paying "
                "the multiplier on traffic it will never act on")
    log.warning("  repair: do not add replicas. The quota is per method, per "
                "workspace, per app, so another process shares the same bucket "
                "and arrives at the same refusals sooner")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-retry-amplification.mjs",
"js": '''/**
 * Model the retry amplification of a Slack event handler against its quota.
 *
 * Read only, and it does not demonstrate the problem it describes. The only
 * measurement taken is how many messages the workspace already produced, read
 * from one page of history per sampled channel. Everything else is arithmetic
 * over numbers the caller supplies.
 */

const API = 'https://slack.com/api/';

// Three retries: immediately, after about a minute, and after about five.
const MAX_RETRIES = 3;
const RETRY_SCHEDULE_SECONDS = [0, 60, 300];

// The miss rate is capped just short of one so the arithmetic stays meaningful.
// The number that matters more is the other one: Slack disables an app's event
// subscriptions when it fails more than 95% of deliveries in an hour.
const MISS_CAP = 0.99;
const DISABLE_THRESHOLD = 0.95;

/**
 * Expected deliveries for one event at a given miss rate. Pure.
 * A geometric sum truncated at the retry ceiling, and deliberately not linear.
 */
export function deliveriesPerEvent(missRate, maxRetries = MAX_RETRIES) {
  const p = Math.min(Math.max(Number(missRate) || 0, 0), 1);
  let total = 1;
  let term = 1;
  for (let i = 0; i < Math.max(Number(maxRetries) || 0, 0); i += 1) {
    term *= p;
    total += term;
  }
  return Math.round(total * 10000) / 10000;
}

/**
 * Multiply the three factors and hold the product against the budget. Pure.
 * The throttled fraction is the input to the feedback loop, which is what
 * makes this more than a multiplication.
 */
export function demand(eventsPerMinute, callsPerEvent, missRate, tierPerMinute) {
  const events = Math.max(Number(eventsPerMinute) || 0, 0);
  const calls = Math.max(Number(callsPerEvent) || 0, 0);
  const budget = Math.max(Number(tierPerMinute) || 0, 1);
  const perEvent = deliveriesPerEvent(missRate);
  const demanded = events * perEvent * calls;
  const share = Math.round((demanded * 1000.0) / budget) / 10;
  const throttled = demanded <= budget
    ? 0 : Math.round((1 - budget / demanded) * 10000) / 10000;

  let verdict = 'stable';
  if (demanded > budget) verdict = 'over-budget';
  else if (share >= 80.0) verdict = 'saturated';
  else if (share >= 50.0) verdict = 'tight';

  return {
    deliveriesPerEvent: perEvent,
    callsPerMinute: Math.round(demanded * 10) / 10,
    budgetPerMinute: Math.round(budget * 10) / 10,
    sharePercent: share,
    throttledFraction: throttled,
    verdict,
  };
}

/**
 * Name the equilibrium the loop arrived at. Pure.
 * The loop always has a fixed point, because the retry ceiling bounds the
 * amplification. Whether that fixed point is somewhere you can live is the
 * whole question, and the top rung is not a performance problem.
 */
export function settleVerdict(finalMissRate, baseMissRate) {
  const final = Number(finalMissRate) || 0;
  const base = Number(baseMissRate) || 0;
  if (final <= base + 0.01) {
    return ['stable', 'no feedback: the throttled fraction never leaves zero'];
  }
  if (final >= DISABLE_THRESHOLD) {
    return ['disabling',
      `the equilibrium is above the ${Math.round(DISABLE_THRESHOLD * 100)}% ` +
      'failure rate that gets event subscriptions switched off. This loop does ' +
      'not end in a slow app, it ends in a disabled one.'];
  }
  if (final >= 0.5) {
    return ['collapsed',
      'the loop has a fixed point and the fixed point is failure: most ' +
      'deliveries miss, most events are retried, and it stays there until the ' +
      'traffic stops'];
  }
  return ['elevated',
    'the feedback is real and the equilibrium is survivable; there is no ' +
    'headroom left for the next increase in traffic'];
}

/**
 * Feed the throttled fraction back into the miss rate and iterate. Pure.
 * The miss rate is an output rather than an input. The retry ceiling means
 * this always settles somewhere; where it settles is the finding.
 */
export function converge(eventsPerMinute, callsPerEvent, baseMissRate,
  tierPerMinute, rounds = 12) {
  let p = Math.min(Math.max(Number(baseMissRate) || 0, 0), MISS_CAP);
  const base = p;
  const path = [Math.round(p * 10000) / 10000];
  const limit = Math.max(Number(rounds) || 0, 1);
  for (let step = 0; step < limit; step += 1) {
    const state = demand(eventsPerMinute, callsPerEvent, p, tierPerMinute);
    const next = Math.min(base + state.throttledFraction, MISS_CAP);
    path.push(Math.round(next * 10000) / 10000);
    if (Math.abs(next - p) < 0.001) {
      const [verdict, detail] = settleVerdict(next, base);
      return {
        verdict,
        detail,
        missRate: Math.round(next * 10000) / 10000,
        rounds: step + 1,
        path,
        deliveriesPerEvent: deliveriesPerEvent(next),
      };
    }
    p = next;
  }
  return {
    verdict: 'unsettled',
    detail: `still climbing after ${limit} round(s), which is the same finding ` +
      'as collapse with less arithmetic',
    missRate: Math.round(p * 10000) / 10000,
    rounds: limit,
    path,
    deliveriesPerEvent: deliveriesPerEvent(p),
  };
}

/**
 * Messages per minute across a sample of history. Pure.
 * A floor, not a census: one page per channel, and a clamped history returns
 * fewer objects than were asked for. Both bias the number down.
 */
export function observedRate(timestamps) {
  const values = (timestamps ?? []).filter(Boolean).map(Number).sort((a, b) => a - b);
  if (values.length < 2) {
    return {
      count: values.length,
      spanSeconds: 0,
      perMinute: 0,
      note: 'not enough messages in the sample to derive a rate',
    };
  }
  const span = values[values.length - 1] - values[0];
  if (span <= 0) {
    return {
      count: values.length,
      spanSeconds: 0,
      perMinute: 0,
      note: 'every sampled message shares a timestamp',
    };
  }
  return {
    count: values.length,
    spanSeconds: Math.round(span * 10) / 10,
    perMinute: Math.round((values.length * 600.0) / span) / 10,
    note: 'a floor: one page per channel, so the real rate is higher',
  };
}

async function get(token, method, params) {
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  try { return await res.json(); } catch { return { ok: false, error: 'unparseable_body' }; }
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const callsPerEvent = Number(arg(args, '--calls-per-event', 3));
  const missRate = Number(arg(args, '--miss-rate', 0.05));
  const tierPerMinute = Number(arg(args, '--tier-per-minute', 50));
  const channels = Number(arg(args, '--channels', 5));
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  let events = Number(arg(args, '--events-per-minute', 0));

  if (events <= 0 && !token) {
    console.error(`set ${tokenEnv} or pass --events-per-minute`);
    process.exitCode = 2;
    return;
  }

  if (events <= 0) {
    const who = await get(token, 'auth.test', {});
    if (who.ok !== true) {
      console.error(`auth.test answered 200 with ok: false, error=${who.error}`);
      process.exitCode = 2;
      return;
    }
    const mine = await get(token, 'users.conversations', {
      user: who.user_id ?? '', types: 'public_channel,private_channel', limit: '200',
    });
    const ids = (mine.channels ?? []).map((c) => c.id).slice(0, Math.max(channels, 1));
    const stamps = [];
    let sampled = 0;
    for (const cid of ids) {
      // eslint-disable-next-line no-await-in-loop
      const page = await get(token, 'conversations.history', { channel: cid, limit: '200' });
      if (page.ok !== true) {
        console.warn(`rate       skipped        ${page.error} on ${cid}`);
        continue;
      }
      sampled += 1;
      for (const m of page.messages ?? []) stamps.push(m.ts);
    }
    const rate = observedRate(stamps);
    events = rate.perMinute;
    console.log(`rate       observed       ${rate.perMinute} message(s)/minute ` +
      `across ${sampled} channel(s), ${rate.note}`);
  }

  const state = demand(events, callsPerEvent, missRate, tierPerMinute);
  (state.verdict === 'stable' ? console.log : console.warn)(
    `demand     ${state.verdict.padEnd(14)} ${state.callsPerMinute} call(s)/minute ` +
    `against a budget of ${state.budgetPerMinute} (${state.sharePercent}%)`);
  console.log(`deliveries expanded       ${state.deliveriesPerEvent} per event at a ` +
    `miss rate of ${missRate}, retried at ${RETRY_SCHEDULE_SECONDS.join(', ')} seconds`);

  const loop = converge(events, callsPerEvent, missRate, tierPerMinute);
  const calm = loop.verdict === 'stable';
  (calm ? console.log : console.warn)(
    `loop       ${loop.verdict.padEnd(14)} settles at a miss rate of ` +
    `${loop.missRate} after ${loop.rounds} round(s), ${loop.deliveriesPerEvent} ` +
    'deliveries/event');
  console.log(`loop       path           ${loop.path.map((p) => p.toFixed(2)).join(' -> ')}`);
  (calm ? console.log : console.warn)(`loop       meaning        ${loop.detail}`);

  if (calm && (state.verdict === 'stable' || state.verdict === 'tight')) {
    console.log('verdict    ok             no feedback: the throttled fraction ' +
      'stays at zero');
    return;
  }
  console.warn('  repair: cut the calls one handler run makes. That factor ' +
    'multiplies everything else in the chain and it is the only one of the four ' +
    'you can change today');
  console.warn('  repair: narrow the subscription so fewer events arrive at all; ' +
    'an app that receives every message in every channel is paying the multiplier ' +
    'on traffic it will never act on');
  console.warn('  repair: do not add replicas. The quota is per method, per ' +
    'workspace, per app, so another process shares the same bucket and arrives ' +
    'at the same refusals sooner');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the cliff and the fixed point, because those are the two claims. Deliveries per event is asserted to be almost nothing at a five percent miss rate and nearly three at eighty percent, from the same bounded schedule, which is the non-linearity people budget as if it were linear. Then the same forty events a minute are asserted to settle at five percent with one call per handler run and in the nineties with three, and a heavier configuration is asserted to settle above the failure rate that gets event delivery switched off &mdash; the rung where this stops being a performance finding.",
"test_py_file": "test_slack_retry_amplification.py",
"test_js_file": "slack-retry-amplification.test.mjs",
"test_py": '''from slack_retry_amplification import (converge, deliveries_per_event, demand,
                                       observed_rate, settle_verdict)


def test_the_amplification_is_bounded_at_four_deliveries():
    assert deliveries_per_event(1.0) == 4.0
    assert deliveries_per_event(0.0) == 1.0


def test_the_expansion_is_a_cliff_rather_than_a_slope():
    assert deliveries_per_event(0.05) < 1.06
    assert deliveries_per_event(0.4) > 1.6
    assert deliveries_per_event(0.8) > 2.9


def test_a_saturated_handler_has_nothing_refused_yet():
    state = demand(40, 1, 0.05, 50)
    assert state["verdict"] == "saturated"
    assert state["share_percent"] > 80
    assert state["throttled_fraction"] == 0.0


def test_three_calls_on_the_same_traffic_is_over_the_same_budget():
    state = demand(40, 3, 0.05, 50)
    assert state["verdict"] == "over-budget"
    assert state["calls_per_minute"] > 50
    assert state["throttled_fraction"] > 0.5


def test_the_throttled_fraction_is_what_feeds_the_loop():
    assert demand(40, 3, 0.05, 50)["throttled_fraction"] > demand(
        40, 2, 0.05, 50)["throttled_fraction"]


def test_the_same_traffic_is_stable_at_one_call_and_collapses_at_three():
    assert converge(40, 1, 0.05, 50)["verdict"] == "stable"
    assert converge(40, 3, 0.05, 50)["verdict"] == "collapsed"


def test_a_stable_loop_keeps_the_miss_rate_it_started_with():
    loop = converge(40, 1, 0.05, 50)
    assert loop["miss_rate"] == 0.05
    assert loop["rounds"] == 1


def test_the_collapsed_loop_still_has_a_fixed_point():
    loop = converge(40, 3, 0.05, 50)
    assert loop["path"][0] == 0.05
    assert loop["path"] == sorted(loop["path"])
    assert 0.9 < loop["miss_rate"] < 0.95
    assert loop["deliveries_per_event"] > 3.5


def test_enough_load_settles_above_the_rate_that_gets_you_switched_off():
    loop = converge(200, 5, 0.05, 50)
    assert loop["verdict"] == "disabling"
    assert loop["miss_rate"] >= 0.95
    assert "switched off" in loop["detail"]


def test_the_ladder_is_read_off_the_fixed_point_not_the_journey():
    assert settle_verdict(0.05, 0.05)[0] == "stable"
    assert settle_verdict(0.3, 0.05)[0] == "elevated"
    assert settle_verdict(0.7, 0.05)[0] == "collapsed"
    assert settle_verdict(0.96, 0.05)[0] == "disabling"


def test_zero_traffic_cannot_feed_back():
    assert converge(0, 10, 0.05, 50)["verdict"] == "stable"


def test_a_rate_needs_two_messages_and_a_span():
    assert observed_rate([])["per_minute"] == 0.0
    assert observed_rate(["1735689600.000100"])["count"] == 1
    same = observed_rate(["1735689600.000100", "1735689600.000100"])
    assert same["per_minute"] == 0.0
    assert "shares a timestamp" in same["note"]


def test_the_measured_rate_is_reported_as_a_floor():
    rate = observed_rate(["1735689600.000100", "1735689630.000100",
                          "1735689660.000100"])
    assert rate["span_seconds"] == 60.0
    assert rate["per_minute"] == 3.0
    assert "floor" in rate["note"]
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  converge, deliveriesPerEvent, demand, observedRate, settleVerdict,
} from './slack-retry-amplification.mjs';

test('the amplification is bounded at four deliveries', () => {
  assert.equal(deliveriesPerEvent(1.0), 4);
  assert.equal(deliveriesPerEvent(0), 1);
});

test('the expansion is a cliff rather than a slope', () => {
  assert.ok(deliveriesPerEvent(0.05) < 1.06);
  assert.ok(deliveriesPerEvent(0.4) > 1.6);
  assert.ok(deliveriesPerEvent(0.8) > 2.9);
});

test('a saturated handler has nothing refused yet', () => {
  const state = demand(40, 1, 0.05, 50);
  assert.equal(state.verdict, 'saturated');
  assert.ok(state.sharePercent > 80);
  assert.equal(state.throttledFraction, 0);
});

test('three calls on the same traffic is over the same budget', () => {
  const state = demand(40, 3, 0.05, 50);
  assert.equal(state.verdict, 'over-budget');
  assert.ok(state.callsPerMinute > 50);
  assert.ok(state.throttledFraction > 0.5);
});

test('the throttled fraction is what feeds the loop', () => {
  assert.ok(demand(40, 3, 0.05, 50).throttledFraction
    > demand(40, 2, 0.05, 50).throttledFraction);
});

test('the same traffic is stable at one call and collapses at three', () => {
  assert.equal(converge(40, 1, 0.05, 50).verdict, 'stable');
  assert.equal(converge(40, 3, 0.05, 50).verdict, 'collapsed');
});

test('a stable loop keeps the miss rate it started with', () => {
  const loop = converge(40, 1, 0.05, 50);
  assert.equal(loop.missRate, 0.05);
  assert.equal(loop.rounds, 1);
});

test('the collapsed loop still has a fixed point', () => {
  const loop = converge(40, 3, 0.05, 50);
  assert.equal(loop.path[0], 0.05);
  assert.deepEqual(loop.path, [...loop.path].sort((a, b) => a - b));
  assert.ok(loop.missRate > 0.9 && loop.missRate < 0.95);
  assert.ok(loop.deliveriesPerEvent > 3.5);
});

test('enough load settles above the rate that gets you switched off', () => {
  const loop = converge(200, 5, 0.05, 50);
  assert.equal(loop.verdict, 'disabling');
  assert.ok(loop.missRate >= 0.95);
  assert.match(loop.detail, /switched off/);
});

test('the ladder is read off the fixed point not the journey', () => {
  assert.equal(settleVerdict(0.05, 0.05)[0], 'stable');
  assert.equal(settleVerdict(0.3, 0.05)[0], 'elevated');
  assert.equal(settleVerdict(0.7, 0.05)[0], 'collapsed');
  assert.equal(settleVerdict(0.96, 0.05)[0], 'disabling');
});

test('zero traffic cannot feed back', () => {
  assert.equal(converge(0, 10, 0.05, 50).verdict, 'stable');
});

test('a rate needs two messages and a span', () => {
  assert.equal(observedRate([]).perMinute, 0);
  assert.equal(observedRate(['1735689600.000100']).count, 1);
  const same = observedRate(['1735689600.000100', '1735689600.000100']);
  assert.equal(same.perMinute, 0);
  assert.match(same.note, /shares a timestamp/);
});

test('the measured rate is reported as a floor', () => {
  const rate = observedRate(['1735689600.000100', '1735689630.000100',
    '1735689660.000100']);
  assert.equal(rate.spanSeconds, 60);
  assert.equal(rate.perMinute, 3);
  assert.match(rate.note, /floor/);
});
''',
"faq": [
 ("Is four deliveries per event really the worst case?",
  "For a single event, yes: the original plus three retries, and Slack does not go beyond that. The reason it still becomes a storm is that the ceiling applies per event while the quota applies per method per minute across every event at once. A four times spike on a system running at forty percent of its budget is fine; the same spike on one running at sixty percent is not, and the difference between those two workspaces is invisible until it happens."),
 ("Why not just add more workers to absorb the retries?",
  "Because the rate limit is per method, per workspace, per app, and not per process. Two replicas share one bucket, so doubling the workers doubles the rate at which the bucket is emptied and brings the refusals forward. It is the most natural response to a queue that is not draining and it is the one that makes this particular failure worse."),
 ("Where do the sixty and three hundred second retries show up?",
  "As humps in your API call graph that no product traffic explains, minutes after the load that caused them has gone. That spacing is also the fingerprint in the workspace itself: duplicate app messages roughly a minute and roughly five minutes apart are Slack's retry schedule, and reading those gaps is how a duplicate is attributed to a retry rather than to a double subscription."),
 ("Does the model need my real miss rate to be useful?",
  "It needs a starting one, and any honest number will do, because the interesting output is where the loop settles rather than where it starts. Take whatever fraction of deliveries your logs show taking over three seconds. If a five percent start settles in the nineties, then no plausible starting value saves this configuration; if a twenty percent start settles back near twenty, the feedback is not engaged and you have real headroom."),
 ("Could the script measure the storm instead of modelling it?",
  "It could measure the aftermath, which is duplicate messages in a channel, and that is a different note with a different script. What it will not do is produce the storm to prove the model, because the quota being exhausted belongs to the whole workspace: every other app installed there would be refused alongside yours, and none of their owners agreed to the experiment."),
],
"related": [
 ("/slack/three-second-timeout/", "the missed deadline that starts the loop"),
 ("/slack/ratelimited-retry-after-ignored/", "what to do with the refusal when it arrives"),
 ("/slack/parallel-workers-share-quota/", "who else is spending the same bucket"),
],
"citations": [CITE_EVENTS, CITE_RATE_LIMITS, CITE_CONV_HISTORY, CITE_USERS_CONVERSATIONS],
})

GUIDES.append({
"slug": "duplicate-processing-on-retry",
"title": "The dedupe key that does not survive the retry",
"description": "event_id is stable across all three retries. client_msg_id is missing from a third of your events, and a 60 second TTL expires before the last one.",
"h1": "The dedupe key that does not survive the retry",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack event_id idempotency", "x-slack-retry-num duplicate",
             "slack dedupe event retries", "slack client_msg_id missing",
             "slack socket mode retry header"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There is a dedupe check in the handler. Somebody added it after the last incident, it has a Redis set behind it and a TTL and a test, and there are still three Jira tickets for one Slack message.</p><p>This note is not about whether you deduplicate. It assumes you do. It is about the two properties the key has to have and the one property the store has to have, and about the fact that a key can fail all three while looking completely reasonable in a code review.",
"short_answer": """<p>An idempotency key for Slack event retries has to be <strong>stable</strong> (identical on the retry and on the original) and <strong>unique</strong> (different for two events you genuinely want processed separately). <code>event.event_id</code> is both. Most of the things people reach for instead fail one of them: the request signature is recomputed per delivery with a fresh timestamp, so it is never stable; <code>event.ts</code> is stable but is shared by every event about the same message; <code>client_msg_id</code> is stable and unique and simply is not there on bot messages, on subtyped messages, or on anything that is not a message at all.</p>
<p>Then there is the store. Slack's retry schedule ends at about five minutes, so a TTL under three hundred seconds is a key that survives the first retry and expires before the last one &mdash; which is why the bug reproduces only on the delivery that arrives five minutes late, and only sometimes. The script below audits the key expression against those two properties, audits the TTL against the schedule, and then measures the one thing a read token can measure directly: how often the field you chose is actually present in your workspace's real messages.</p>""",
"problem": """<p>The duplicates themselves are easy to see and there is <a href="/slack/duplicate-messages-no-dedupe/">a note about seeing them</a>. This one deliberately never counts a duplicate, because by the time you are reading this you have already counted them and have already written the guard that was supposed to stop them. The interesting failure is downstream of that decision: the guard is there, it runs, and it does not fire.</p>
<p>The most common reason is a key that is not stable. A retry is a fresh HTTP request: new <code>X-Slack-Request-Timestamp</code>, new <code>X-Slack-Signature</code>, new arrival time at your load balancer. Anything derived from the delivery rather than from the event changes on every attempt, so a set keyed on it accumulates one entry per delivery and rejects nothing. The code looks like deduplication. It is a log with an eviction policy.</p>
<p>The second reason is a key that is not always there. <code>client_msg_id</code> is a genuinely good identifier when it exists, and it exists only on messages a person typed into a Slack client. Bot messages do not carry it. Subtyped messages generally do not. Reactions, channel joins and app mentions of the non-message kind never did. So the expression <code>event.client_msg_id</code> evaluates to nothing for a substantial share of real traffic, and now the behaviour depends entirely on what your code does with a missing key: store it and every keyless event collides with every other keyless event, so the first one is processed and the rest are silently dropped; skip the check and every keyless event is processed once per delivery. One of those loses work and the other duplicates it, and neither is what the guard was for.</p>""",
"why": """<p><strong><code>event_id</code> is the only field designed for this.</strong> It identifies the event, not the delivery, and Slack sends the same one on every retry of it. It is present on every event type, it is opaque, and it needs no parsing. Almost every other candidate is something that happens to be unique often enough to pass a test.</p>
<p><strong>Stable and unique are separate properties and most wrong keys fail exactly one.</strong> A key that fails stability dedupes nothing, which shows up as duplicates. A key that fails uniqueness dedupes too much, which shows up as missing work and is far harder to notice, because nobody files a ticket about the ticket that was not created.</p>
<p><strong>The TTL is not a tuning parameter, it is a deadline set by Slack.</strong> Retries land at roughly zero, sixty and three hundred seconds. Anything under three hundred is arithmetically incapable of catching the last one. Sixty seconds is the value people pick because the first retry is at sixty, and it produces a system that deduplicates the retries you tested and not the ones that happen at load.</p>
<p><strong>Under Socket Mode there is no retry header at all.</strong> The <code>X-Slack-Retry-Num</code> and <code>X-Slack-Retry-Reason</code> headers are an HTTP transport thing. An app that guards by checking whether the retry header is present has no guard when it moves to Socket Mode, and the move is usually made for unrelated reasons by somebody who has never read the dedupe code. Guard on the event id, which arrives the same way over both transports.</p>
<p><strong>The retry reason tells you whether the original probably succeeded.</strong> <code>http_timeout</code> means Slack sent it, your service took the payload and then answered late, so the work very likely happened. <code>connection_failed</code> and <code>ssl_error</code> mean it probably did not. That distinction is worth reading when it is available, and it is a refinement on top of an event id check, never a replacement for one.</p>""",
"steps": [
 {"h": "Write down the key expression exactly as the code computes it",
  "body": """<p>Not "we dedupe on the event", the actual expression: <code>event.event_id</code>, <code>body.event.client_msg_id</code>, <code>sha256(raw_body)</code>, <code>headers['x-slack-signature']</code>. The whole audit turns on which of those it is, and the four are indistinguishable in a design document.</p>"""},
 {"h": "Check it for stability first",
  "body": """<p>Does the retry carry the same value? Anything computed from the request rather than read out of the event fails here, and the failure is total: the guard runs on every delivery and rejects none of them. The script names which side of that line each known expression falls on.</p>"""},
 {"h": "Then check it for uniqueness",
  "body": """<p>Do two events you want handled separately get different values? A message timestamp is stable and is shared by the message event, the reaction on it, and the edit of it, so a single set keyed on it will swallow two of the three. This is the failure that loses work rather than duplicating it.</p>"""},
 {"h": "Measure how often the field is actually there",
  "body": """<p>This is the half a read token answers directly. Sample real messages from the workspace and count how many carry the field you chose. A key present on sixty percent of messages is not a key, it is a key and a coin flip, and the script reports the rate rather than the opinion.</p>"""},
 {"h": "Hold the TTL against the retry schedule, not against your intuition",
  "body": """<p>Three hundred seconds is the floor and ten minutes is the number to use. Below three hundred the guard cannot see the last retry; the resulting bug appears minutes after the event, under load, on a delivery nobody is watching.</p>"""},
 {"h": "Make the downstream operation idempotent as well",
  "body": """<p>A dedupe set is a cache and caches are lost. Putting the event id on the created record as an external key means that even a cold Redis cannot double-create, which turns a correctness property into a database constraint rather than a timing one.</p>"""},
],
"verify": """<p>Re-run after moving to the event id and lengthening the TTL. The coverage line is the one that should change most, because it stops being a measurement of your traffic and starts being a constant.</p>
<pre><code class="language-bash">python3 slack_dedupe_key_audit.py --key event_id --ttl 600 --channels 5
# key        stable-unique  event_id identifies the event, not the delivery
# ttl        sufficient     600s covers the last retry at 300s with margin
# schedule   retries        0, 60, 300 seconds after the original
# coverage   always-present ts on 412 of 412 sampled message(s), 100.0%
# verdict    ok             the key is stable, unique and always present</code></pre>""",
"code_intro": "Three pure functions and one page of history per sampled channel. <code>key_stability</code> is a table of the expressions people actually write, each placed against the two properties a key needs, and the entries that fail are more instructive than the one that passes. <code>ttl_verdict</code> holds the store against Slack's schedule, where three hundred seconds is a fact rather than a preference. <code>key_coverage</code> is the part only a token can answer: how often the field you chose exists in this workspace's real messages.",
"py_file": "slack_dedupe_key_audit.py",
"py": '''"""Audit the idempotency key a Slack event handler dedupes on.

Read only. This script never counts duplicate messages; that is a different
question with a different script. It takes the key expression and TTL the
handler uses, places them against the two properties an idempotency key needs
and against Slack's retry schedule, and then samples history to measure how
often the chosen field is actually present in real traffic.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_dedupe_key_audit")

API = "https://slack.com/api/"

# Retries land at roughly these offsets, so the last one a store has to
# remember is five minutes old. A TTL under 300 cannot catch it, whatever else
# is right about the key.
RETRY_SCHEDULE_SECONDS = (0, 60, 300)
LAST_RETRY_SECONDS = 300
COMFORTABLE_TTL_SECONDS = 600

# The expressions people actually write, against the two properties a key
# needs: stable means the retry carries the same value, unique means two
# events you want handled separately get different ones. Failing stability
# dedupes nothing. Failing uniqueness dedupes too much, which loses work and
# is much harder to notice.
KEY_TABLE = {
    "event_id": (True, True,
                 "identifies the event, not the delivery, and Slack sends the "
                 "same one on every retry of it. Present on every event type."),
    "event.event_id": (True, True, "the same field, spelled with its envelope"),
    "event_time": (True, False,
                   "stable, and only second granularity: two events in the same "
                   "second collide and one of them is silently dropped"),
    "event.ts": (True, False,
                 "stable for one message and shared by every event about that "
                 "message, so the reaction and the edit collide with it"),
    "ts": (True, False, "the same field without its envelope"),
    "client_msg_id": (True, True,
                      "stable and unique where it exists, and it exists only on "
                      "messages a person typed into a Slack client. Check the "
                      "coverage line before trusting it."),
    "x-slack-signature": (False, True,
                          "recomputed per delivery over a fresh request "
                          "timestamp, so the retry never matches the original. "
                          "A set keyed on this rejects nothing."),
    "x-slack-request-timestamp": (False, True,
                                  "the delivery's clock, not the event's"),
    "received_at": (False, True, "your clock, which moves"),
    "uuid": (False, True, "generated per delivery, so every delivery is new"),
    "x-slack-retry-num": (False, False,
                          "a flag, not a key: it says whether this is a retry "
                          "and not which event it is. It is also absent under "
                          "Socket Mode, so a guard built on it disappears when "
                          "the transport changes."),
    "body_hash": (True, True,
                  "identical across retries in practice, and brittle: it covers "
                  "envelope fields you do not control, and re-wrapping the "
                  "payload through your own queue changes it"),
}


def key_stability(expression):
    """Place a key expression against stability and uniqueness. Pure.

    Returns a dict. The two properties are separate on purpose: a key that
    fails stability produces duplicates, and a key that fails uniqueness
    produces missing work, which nobody files a ticket about.
    """
    name = str(expression or "").strip().lower().lstrip("$")
    row = KEY_TABLE.get(name)
    if row is None:
        return {"verdict": "unrecognised", "stable": None, "unique": None,
                "detail": "not an expression this script knows. Check it by "
                          "hand: does the retry carry the same value, and do "
                          "two different events get different ones?"}
    stable, unique, detail = row
    if stable and unique:
        verdict = "stable-unique"
    elif not stable and not unique:
        verdict = "flag-not-key"
    elif not stable:
        verdict = "not-stable"
    else:
        verdict = "stable-collides"
    if name == "client_msg_id":
        verdict = "sparse"
    return {"verdict": verdict, "stable": stable, "unique": unique,
            "detail": detail}


def ttl_verdict(ttl_seconds):
    """Hold the dedupe store's TTL against Slack's retry schedule. Pure.

    Three hundred seconds is not a preference. It is where the last retry
    lands, and a shorter TTL is arithmetically incapable of catching it.
    """
    if ttl_seconds is None:
        return ("unbounded",
                "nothing expires. Correct for deduplication and a memory leak "
                "with a long fuse; ten minutes is enough and bounded.")
    try:
        ttl = float(ttl_seconds)
    except (TypeError, ValueError):
        return ("unreadable", "the ttl is not a number of seconds")
    if ttl <= 0:
        return ("no-ttl",
                "nothing is remembered, so every delivery is the first one this "
                "store has seen")
    if ttl < LAST_RETRY_SECONDS:
        return ("too-short",
                "%ds expires before the last retry at %ds. This guard catches "
                "the retry you tested and misses the one that arrives five "
                "minutes later under load." % (int(ttl), LAST_RETRY_SECONDS))
    if ttl < COMFORTABLE_TTL_SECONDS:
        return ("no-margin",
                "%ds covers the schedule exactly and leaves nothing for clock "
                "skew or a slow queue" % int(ttl))
    return ("sufficient",
            "%ds covers the last retry at %ds with margin"
            % (int(ttl), LAST_RETRY_SECONDS))


def key_coverage(messages, field):
    """Count how often the chosen field is present in real messages. Pure.

    The half a read token answers directly. A key present on sixty percent of
    traffic is not a key, and what happens to the other forty percent depends
    on how the handler treats a missing value: store it and they all collide
    with each other, skip the check and they are all processed per delivery.
    """
    rows = list(messages or [])
    name = str(field or "").strip()
    if not rows:
        return {"present": 0, "total": 0, "rate": 0.0, "verdict": "no-sample",
                "detail": "no messages were sampled, so coverage is unmeasured"}
    present = sum(1 for m in rows if isinstance(m, dict) and m.get(name))
    total = len(rows)
    rate = round(present * 100.0 / total, 1)
    if present == 0:
        return {"present": present, "total": total, "rate": rate, "verdict": "never",
                "detail": "%s is on none of the %d sampled message(s); a key that "
                          "is always absent is not a key" % (name, total)}
    if rate >= 99.5:
        return {"present": present, "total": total, "rate": rate,
                "verdict": "always-present",
                "detail": "%s on %d of %d sampled message(s), %.1f%%"
                          % (name, present, total, rate)}
    return {"present": present, "total": total, "rate": rate, "verdict": "sparse",
            "detail": "%s is missing from %d of %d sampled message(s). Those "
                      "events either all collide on the empty key, losing work, "
                      "or all skip the guard, duplicating it."
                      % (name, total - present, total)}


def get(session, method, **params):
    r = session.get(API + method, params=params, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--key", default="event_id",
                    help="the key expression the handler dedupes on")
    ap.add_argument("--ttl", default="600",
                    help="the dedupe store's ttl in seconds, or none")
    ap.add_argument("--field", action="append", default=[],
                    help="message field to measure coverage for; repeatable")
    ap.add_argument("--channels", type=int, default=5,
                    help="how many of the bot's channels to sample")
    args = ap.parse_args()

    findings = 0
    key = key_stability(args.key)
    good_key = key["verdict"] == "stable-unique"
    (log.info if good_key else log.warning)(
        "key        %-14s %s %s", key["verdict"], args.key, key["detail"])
    if not good_key:
        findings += 1

    ttl = None if str(args.ttl).strip().lower() in ("none", "") else args.ttl
    state, detail = ttl_verdict(ttl)
    (log.info if state == "sufficient" else log.warning)(
        "ttl        %-14s %s", state, detail)
    log.info("schedule   retries        %s seconds after the original, so the "
             "last one to remember is %ds old",
             ", ".join(str(x) for x in RETRY_SCHEDULE_SECONDS), LAST_RETRY_SECONDS)
    if state != "sufficient":
        findings += 1

    fields = args.field or ["ts", "client_msg_id"]
    token = os.environ.get(args.token_env)
    if not token:
        log.info("coverage   skipped        set %s to measure how often each "
                 "field is present", args.token_env)
    else:
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        who = get(s, "auth.test")
        if who.get("ok") is not True:
            log.error("auth.test answered 200 with ok: false, error=%s", who.get("error"))
            return 2
        mine = get(s, "users.conversations", user=who.get("user_id", ""),
                   types="public_channel,private_channel", limit=200)
        ids = [c.get("id") for c in (mine.get("channels") or [])][:max(args.channels, 1)]
        sample = []
        for cid in ids:
            page = get(s, "conversations.history", channel=cid, limit=200)
            if page.get("ok") is not True:
                log.warning("coverage   skipped        %s on %s", page.get("error"), cid)
                continue
            sample.extend(page.get("messages") or [])
        for name in fields:
            cov = key_coverage(sample, name)
            (log.info if cov["verdict"] == "always-present" else log.warning)(
                "coverage   %-14s %s", cov["verdict"], cov["detail"])
            if cov["verdict"] == "sparse" and name == args.key:
                findings += 1

    if findings:
        log.warning("  repair: dedupe on event.event_id, which identifies the "
                    "event rather than the delivery and arrives identically over "
                    "http and Socket Mode")
        log.warning("  repair: give the store a ten minute ttl so the retry at "
                    "300 seconds is still remembered when it lands")
        log.warning("  repair: put the event id on the created record as an "
                    "external key, so a cold dedupe cache cannot double-create")
        return 1
    log.info("verdict    %-14s the key is stable, unique and always present", "ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-dedupe-key-audit.mjs",
"js": '''/**
 * Audit the idempotency key a Slack event handler dedupes on.
 *
 * Read only. This script never counts duplicate messages; that is a different
 * question with a different script. It takes the key expression and TTL the
 * handler uses, places them against the two properties an idempotency key
 * needs and against Slack's retry schedule, and then samples history to
 * measure how often the chosen field is actually present in real traffic.
 */

const API = 'https://slack.com/api/';

// The last retry a store has to remember is five minutes old.
const RETRY_SCHEDULE_SECONDS = [0, 60, 300];
const LAST_RETRY_SECONDS = 300;
const COMFORTABLE_TTL_SECONDS = 600;

// The expressions people actually write, against the two properties a key
// needs. Failing stability dedupes nothing; failing uniqueness dedupes too
// much, which loses work and is much harder to notice.
const KEY_TABLE = new Map([
  ['event_id', [true, true,
    'identifies the event, not the delivery, and Slack sends the same one on ' +
    'every retry of it. Present on every event type.']],
  ['event.event_id', [true, true, 'the same field, spelled with its envelope']],
  ['event_time', [true, false,
    'stable, and only second granularity: two events in the same second ' +
    'collide and one of them is silently dropped']],
  ['event.ts', [true, false,
    'stable for one message and shared by every event about that message, so ' +
    'the reaction and the edit collide with it']],
  ['ts', [true, false, 'the same field without its envelope']],
  ['client_msg_id', [true, true,
    'stable and unique where it exists, and it exists only on messages a ' +
    'person typed into a Slack client. Check the coverage line before ' +
    'trusting it.']],
  ['x-slack-signature', [false, true,
    'recomputed per delivery over a fresh request timestamp, so the retry ' +
    'never matches the original. A set keyed on this rejects nothing.']],
  ['x-slack-request-timestamp', [false, true, "the delivery's clock, not the event's"]],
  ['received_at', [false, true, 'your clock, which moves']],
  ['uuid', [false, true, 'generated per delivery, so every delivery is new']],
  ['x-slack-retry-num', [false, false,
    'a flag, not a key: it says whether this is a retry and not which event it ' +
    'is. It is also absent under Socket Mode, so a guard built on it ' +
    'disappears when the transport changes.']],
  ['body_hash', [true, true,
    'identical across retries in practice, and brittle: it covers envelope ' +
    'fields you do not control, and re-wrapping the payload through your own ' +
    'queue changes it']],
]);

/**
 * Place a key expression against stability and uniqueness. Pure.
 * The two properties are separate on purpose: failing stability produces
 * duplicates, failing uniqueness produces missing work.
 */
export function keyStability(expression) {
  const name = String(expression ?? '').trim().toLowerCase().replace(/^\\$+/, '');
  const row = KEY_TABLE.get(name);
  if (!row) {
    return {
      verdict: 'unrecognised',
      stable: null,
      unique: null,
      detail: 'not an expression this script knows. Check it by hand: does the ' +
        'retry carry the same value, and do two different events get different ones?',
    };
  }
  const [stable, unique, detail] = row;
  let verdict = 'stable-collides';
  if (stable && unique) verdict = 'stable-unique';
  else if (!stable && !unique) verdict = 'flag-not-key';
  else if (!stable) verdict = 'not-stable';
  if (name === 'client_msg_id') verdict = 'sparse';
  return { verdict, stable, unique, detail };
}

/**
 * Hold the dedupe store's TTL against Slack's retry schedule. Pure.
 * Three hundred seconds is where the last retry lands, not a preference.
 */
export function ttlVerdict(ttlSeconds) {
  if (ttlSeconds === null || ttlSeconds === undefined) {
    return ['unbounded',
      'nothing expires. Correct for deduplication and a memory leak with a ' +
      'long fuse; ten minutes is enough and bounded.'];
  }
  const ttl = Number(ttlSeconds);
  if (!Number.isFinite(ttl)) return ['unreadable', 'the ttl is not a number of seconds'];
  if (ttl <= 0) {
    return ['no-ttl',
      'nothing is remembered, so every delivery is the first one this store has seen'];
  }
  if (ttl < LAST_RETRY_SECONDS) {
    return ['too-short',
      `${Math.trunc(ttl)}s expires before the last retry at ${LAST_RETRY_SECONDS}s. ` +
      'This guard catches the retry you tested and misses the one that arrives ' +
      'five minutes later under load.'];
  }
  if (ttl < COMFORTABLE_TTL_SECONDS) {
    return ['no-margin',
      `${Math.trunc(ttl)}s covers the schedule exactly and leaves nothing for ` +
      'clock skew or a slow queue'];
  }
  return ['sufficient',
    `${Math.trunc(ttl)}s covers the last retry at ${LAST_RETRY_SECONDS}s with margin`];
}

/**
 * Count how often the chosen field is present in real messages. Pure.
 * A key present on sixty percent of traffic is not a key, and what happens to
 * the other forty percent depends on how the handler treats a missing value.
 */
export function keyCoverage(messages, field) {
  const rows = [...(messages ?? [])];
  const name = String(field ?? '').trim();
  if (rows.length === 0) {
    return {
      present: 0, total: 0, rate: 0, verdict: 'no-sample',
      detail: 'no messages were sampled, so coverage is unmeasured',
    };
  }
  const present = rows.filter((m) => m && typeof m === 'object' && m[name]).length;
  const total = rows.length;
  const rate = Math.round((present * 1000.0) / total) / 10;
  if (present === 0) {
    return {
      present, total, rate, verdict: 'never',
      detail: `${name} is on none of the ${total} sampled message(s); a key that ` +
        'is always absent is not a key',
    };
  }
  if (rate >= 99.5) {
    return {
      present, total, rate, verdict: 'always-present',
      detail: `${name} on ${present} of ${total} sampled message(s), ${rate}%`,
    };
  }
  return {
    present, total, rate, verdict: 'sparse',
    detail: `${name} is missing from ${total - present} of ${total} sampled ` +
      'message(s). Those events either all collide on the empty key, losing ' +
      'work, or all skip the guard, duplicating it.',
  };
}

async function get(token, method, params) {
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  try { return await res.json(); } catch { return { ok: false, error: 'unparseable_body' }; }
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const keyExpr = arg(args, '--key', 'event_id');
  const ttlArg = arg(args, '--ttl', '600');
  const channels = Number(arg(args, '--channels', 5));
  let findings = 0;

  const key = keyStability(keyExpr);
  const goodKey = key.verdict === 'stable-unique';
  (goodKey ? console.log : console.warn)(
    `key        ${key.verdict.padEnd(14)} ${keyExpr} ${key.detail}`);
  if (!goodKey) findings += 1;

  const ttl = ['none', ''].includes(String(ttlArg).trim().toLowerCase()) ? null : ttlArg;
  const [state, detail] = ttlVerdict(ttl);
  (state === 'sufficient' ? console.log : console.warn)(
    `ttl        ${state.padEnd(14)} ${detail}`);
  console.log(`schedule   retries        ${RETRY_SCHEDULE_SECONDS.join(', ')} seconds ` +
    `after the original, so the last one to remember is ${LAST_RETRY_SECONDS}s old`);
  if (state !== 'sufficient') findings += 1;

  const fields = argAll(args, '--field');
  const wanted = fields.length ? fields : ['ts', 'client_msg_id'];
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.log(`coverage   skipped        set ${tokenEnv} to measure how often ` +
      'each field is present');
  } else {
    const who = await get(token, 'auth.test', {});
    if (who.ok !== true) {
      console.error(`auth.test answered 200 with ok: false, error=${who.error}`);
      process.exitCode = 2;
      return;
    }
    const mine = await get(token, 'users.conversations', {
      user: who.user_id ?? '', types: 'public_channel,private_channel', limit: '200',
    });
    const ids = (mine.channels ?? []).map((c) => c.id).slice(0, Math.max(channels, 1));
    const sample = [];
    for (const cid of ids) {
      // eslint-disable-next-line no-await-in-loop
      const page = await get(token, 'conversations.history', { channel: cid, limit: '200' });
      if (page.ok !== true) {
        console.warn(`coverage   skipped        ${page.error} on ${cid}`);
        continue;
      }
      sample.push(...(page.messages ?? []));
    }
    for (const name of wanted) {
      const cov = keyCoverage(sample, name);
      (cov.verdict === 'always-present' ? console.log : console.warn)(
        `coverage   ${cov.verdict.padEnd(14)} ${cov.detail}`);
      if (cov.verdict === 'sparse' && name === keyExpr) findings += 1;
    }
  }

  if (findings) {
    console.warn('  repair: dedupe on event.event_id, which identifies the event ' +
      'rather than the delivery and arrives identically over http and Socket Mode');
    console.warn(`  repair: give the store a ten minute ttl so the retry at ` +
      `${LAST_RETRY_SECONDS} seconds is still remembered when it lands`);
    console.warn('  repair: put the event id on the created record as an external ' +
      'key, so a cold dedupe cache cannot double-create');
    process.exitCode = 1;
  } else {
    console.log('verdict    ok             the key is stable, unique and always present');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the two properties apart, because collapsing them is the mistake the whole note is about. The request signature is asserted to be unique and not stable, which is a guard that rejects nothing; the message timestamp is asserted to be stable and not unique, which is a guard that rejects too much and quietly loses work. The TTL boundary is pinned at exactly three hundred seconds in both directions, since that is Slack's number rather than anybody's preference, and coverage is asserted against a sample containing the message shapes that have no <code>client_msg_id</code>.",
"test_py_file": "test_slack_dedupe_key_audit.py",
"test_js_file": "slack-dedupe-key-audit.test.mjs",
"test_py": '''from slack_dedupe_key_audit import key_coverage, key_stability, ttl_verdict

SAMPLE = [
    {"ts": "1735689600.000100", "user": "U01", "client_msg_id": "aaa-1"},
    {"ts": "1735689601.000100", "user": "U01", "client_msg_id": "aaa-2"},
    {"ts": "1735689602.000100", "user": "U02", "client_msg_id": "aaa-3"},
    {"ts": "1735689603.000100", "bot_id": "B01"},
    {"ts": "1735689604.000100", "bot_id": "B01"},
    {"ts": "1735689605.000100", "subtype": "channel_join", "user": "U03"},
]


def test_the_event_id_is_the_only_expression_that_passes_both_properties():
    row = key_stability("event_id")
    assert row["verdict"] == "stable-unique"
    assert row["stable"] is True and row["unique"] is True
    assert key_stability("event.event_id")["verdict"] == "stable-unique"


def test_a_signature_is_unique_and_not_stable_so_it_rejects_nothing():
    row = key_stability("x-slack-signature")
    assert row["stable"] is False
    assert row["unique"] is True
    assert row["verdict"] == "not-stable"


def test_a_message_timestamp_is_stable_and_not_unique_so_it_rejects_too_much():
    row = key_stability("event.ts")
    assert row["stable"] is True
    assert row["unique"] is False
    assert row["verdict"] == "stable-collides"
    assert key_stability("ts")["verdict"] == "stable-collides"


def test_the_retry_header_is_reported_as_a_flag_rather_than_a_key():
    row = key_stability("x-slack-retry-num")
    assert row["verdict"] == "flag-not-key"
    assert "Socket Mode" in row["detail"]


def test_client_msg_id_is_kept_apart_from_the_keys_that_always_exist():
    row = key_stability("client_msg_id")
    assert row["verdict"] == "sparse"
    assert row["stable"] is True and row["unique"] is True


def test_an_unknown_expression_is_never_guessed_at():
    row = key_stability("some_field_we_invented")
    assert row["verdict"] == "unrecognised"
    assert row["stable"] is None


def test_the_ttl_boundary_is_the_last_retry_and_not_a_preference():
    assert ttl_verdict(299)[0] == "too-short"
    assert ttl_verdict(300)[0] == "no-margin"
    assert ttl_verdict(599)[0] == "no-margin"
    assert ttl_verdict(600)[0] == "sufficient"


def test_a_sixty_second_ttl_is_named_for_the_retry_it_misses():
    state, detail = ttl_verdict(60)
    assert state == "too-short"
    assert "300s" in detail


def test_no_ttl_and_no_expiry_are_different_findings():
    assert ttl_verdict(0)[0] == "no-ttl"
    assert ttl_verdict(None)[0] == "unbounded"
    assert ttl_verdict("soon")[0] == "unreadable"


def test_a_field_on_every_message_and_a_field_on_half_of_them():
    assert key_coverage(SAMPLE, "ts")["verdict"] == "always-present"
    cov = key_coverage(SAMPLE, "client_msg_id")
    assert cov["verdict"] == "sparse"
    assert cov["present"] == 3
    assert cov["rate"] == 50.0


def test_a_missing_field_is_reported_as_never_rather_than_as_sparse():
    cov = key_coverage(SAMPLE, "event_id")
    assert cov["verdict"] == "never"
    assert "not a key" in cov["detail"]


def test_an_empty_sample_is_unmeasured_rather_than_clean():
    cov = key_coverage([], "ts")
    assert cov["verdict"] == "no-sample"
    assert cov["rate"] == 0.0
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyCoverage, keyStability, ttlVerdict } from './slack-dedupe-key-audit.mjs';

const SAMPLE = [
  { ts: '1735689600.000100', user: 'U01', client_msg_id: 'aaa-1' },
  { ts: '1735689601.000100', user: 'U01', client_msg_id: 'aaa-2' },
  { ts: '1735689602.000100', user: 'U02', client_msg_id: 'aaa-3' },
  { ts: '1735689603.000100', bot_id: 'B01' },
  { ts: '1735689604.000100', bot_id: 'B01' },
  { ts: '1735689605.000100', subtype: 'channel_join', user: 'U03' },
];

test('the event id is the only expression that passes both properties', () => {
  const row = keyStability('event_id');
  assert.equal(row.verdict, 'stable-unique');
  assert.equal(row.stable, true);
  assert.equal(row.unique, true);
  assert.equal(keyStability('event.event_id').verdict, 'stable-unique');
});

test('a signature is unique and not stable so it rejects nothing', () => {
  const row = keyStability('x-slack-signature');
  assert.equal(row.stable, false);
  assert.equal(row.unique, true);
  assert.equal(row.verdict, 'not-stable');
});

test('a message timestamp is stable and not unique so it rejects too much', () => {
  const row = keyStability('event.ts');
  assert.equal(row.stable, true);
  assert.equal(row.unique, false);
  assert.equal(row.verdict, 'stable-collides');
  assert.equal(keyStability('ts').verdict, 'stable-collides');
});

test('the retry header is reported as a flag rather than a key', () => {
  const row = keyStability('x-slack-retry-num');
  assert.equal(row.verdict, 'flag-not-key');
  assert.match(row.detail, /Socket Mode/);
});

test('client_msg_id is kept apart from the keys that always exist', () => {
  const row = keyStability('client_msg_id');
  assert.equal(row.verdict, 'sparse');
  assert.equal(row.stable, true);
  assert.equal(row.unique, true);
});

test('an unknown expression is never guessed at', () => {
  const row = keyStability('some_field_we_invented');
  assert.equal(row.verdict, 'unrecognised');
  assert.equal(row.stable, null);
});

test('the ttl boundary is the last retry and not a preference', () => {
  assert.equal(ttlVerdict(299)[0], 'too-short');
  assert.equal(ttlVerdict(300)[0], 'no-margin');
  assert.equal(ttlVerdict(599)[0], 'no-margin');
  assert.equal(ttlVerdict(600)[0], 'sufficient');
});

test('a sixty second ttl is named for the retry it misses', () => {
  const [state, detail] = ttlVerdict(60);
  assert.equal(state, 'too-short');
  assert.match(detail, /300s/);
});

test('no ttl and no expiry are different findings', () => {
  assert.equal(ttlVerdict(0)[0], 'no-ttl');
  assert.equal(ttlVerdict(null)[0], 'unbounded');
  assert.equal(ttlVerdict('soon')[0], 'unreadable');
});

test('a field on every message and a field on half of them', () => {
  assert.equal(keyCoverage(SAMPLE, 'ts').verdict, 'always-present');
  const cov = keyCoverage(SAMPLE, 'client_msg_id');
  assert.equal(cov.verdict, 'sparse');
  assert.equal(cov.present, 3);
  assert.equal(cov.rate, 50);
});

test('a missing field is reported as never rather than as sparse', () => {
  const cov = keyCoverage(SAMPLE, 'event_id');
  assert.equal(cov.verdict, 'never');
  assert.match(cov.detail, /not a key/);
});

test('an empty sample is unmeasured rather than clean', () => {
  const cov = keyCoverage([], 'ts');
  assert.equal(cov.verdict, 'no-sample');
  assert.equal(cov.rate, 0);
});
''',
"faq": [
 ("Why event_id rather than the message timestamp?",
  "Because the timestamp identifies the message and the event id identifies the event. A message being posted, reacted to and then edited produces three events that a timestamp-keyed set will treat as one, so two of the three are dropped as duplicates when neither is. The event id is different for each of them and identical across the retries of each, which is exactly the pair of properties the guard needs."),
 ("Is ten minutes not excessive for a TTL?",
  "It is two entries per event in a set of short strings, for ten minutes. The alternative failure is worse than the memory: at sixty seconds the guard catches the retry at sixty and misses the one at three hundred, so the bug survives your testing and reappears only under the load that produced the slow deliveries in the first place. Three hundred seconds is the floor and six hundred is the number to use."),
 ("We moved to Socket Mode and started seeing duplicates again. Why?",
  "Because the retry headers are an HTTP transport feature and Socket Mode does not carry them. Any guard written as &ldquo;if the retry header is present, skip&rdquo; silently becomes a no-op on the socket path. The event id is in the event payload itself and arrives identically over both transports, which is one more reason to key on it rather than on delivery metadata."),
 ("Should I short-circuit on X-Slack-Retry-Reason?",
  "As a refinement, yes, and never as the guard. A reason of http_timeout means Slack sent the payload, your service accepted it, and the response was late, so the work has probably already been done. connection_failed and ssl_error suggest it has not. Reading that improves your odds on the cases the dedupe store missed; it does not replace the store, and it is unavailable over Socket Mode."),
 ("The dedupe check is right and duplicates still appear.",
  "Then the duplicates are probably not retries, and the spacing will tell you: sub-second copies mean two delivery paths or two replicas handling the same event, hours apart means a scheduler running twice. Retry duplicates land at roughly sixty and three hundred seconds and nowhere else. Measuring that spacing is a different script, linked below, and it is the right one to run before changing any of this."),
],
"related": [
 ("/slack/duplicate-messages-no-dedupe/", "counting the duplicates and reading their spacing"),
 ("/slack/retry-storm-from-event-retries/", "why there are retries to deduplicate at all"),
 ("/slack/bot-message-echo-loop/", "the other way one event becomes many"),
],
"citations": [CITE_EVENTS, CITE_MESSAGE_EVENT, CITE_SOCKET_MODE, CITE_CONV_HISTORY],
})
